"""LLM providers.

``LLMProvider.generate`` is the only generation entry point used by the tutor.
Provider-specific code (Gemini SDK) is confined to ``GeminiLLMProvider``.
``ExtractiveMockLLM`` is a deterministic offline stand-in used for tests and for
running the full pipeline locally without an API key.
"""

from __future__ import annotations

import json
import logging
import re
import time
from collections.abc import Sequence
from typing import Any, Literal, Protocol, runtime_checkable

from pydantic import BaseModel

from app.tutor.text import content_terms, sentences

logger = logging.getLogger(__name__)


class LLMMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class LLMError(RuntimeError):
    """Raised when the LLM provider fails. Message is safe to surface (no secrets)."""


@runtime_checkable
class LLMProvider(Protocol):
    name: str

    def generate(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        context: str = "",
        conversation_history: Sequence[LLMMessage] = (),
        response_schema: dict[str, Any] | None = None,
        temperature: float = 0.0,
    ) -> str:
        """Return the model's text output (a JSON string when ``response_schema`` is set)."""
        ...


def compose_input(user_prompt: str, context: str, history: Sequence[LLMMessage]) -> str:
    """Assemble the single user turn sent to the model.

    History is rendered *outside* the evidence block and explicitly labelled as
    non-evidence, so prior tutor statements can never masquerade as course data.
    """
    parts: list[str] = []
    if history:
        lines = [f"{m.role.upper()}: {m.content}" for m in history]
        parts.append(
            "<conversation_history>\n"
            "(For resolving references like 'it' or 'that' ONLY. This is NOT course evidence; "
            "earlier tutor replies may be incomplete or wrong and must not be cited.)\n"
            + "\n".join(lines)
            + "\n</conversation_history>"
        )
    if context:
        parts.append(context)
    parts.append(user_prompt)
    return "\n\n".join(parts)


class GeminiLLMProvider:
    """Gemini via the Interactions API of the official ``google-genai`` SDK."""

    name = "gemini"

    def __init__(self, api_key: str, model: str, timeout_seconds: float = 60.0) -> None:
        from google import genai

        self._client = genai.Client(api_key=api_key)
        self._model = model
        self._timeout = timeout_seconds

    def generate(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        context: str = "",
        conversation_history: Sequence[LLMMessage] = (),
        response_schema: dict[str, Any] | None = None,
        temperature: float = 0.0,
    ) -> str:
        kwargs: dict[str, Any] = {
            "model": self._model,
            "system_instruction": system_prompt,
            "input": compose_input(user_prompt, context, conversation_history),
            "generation_config": {"temperature": temperature},
            # Student questions + course content should not be retained server-side.
            "store": False,
            "timeout": self._timeout,
        }
        if response_schema is not None:
            kwargs["response_format"] = {
                "type": "text",
                "mime_type": "application/json",
                "schema": response_schema,
            }
        
        interaction = None
        last_exc = None
        for attempt in range(3):
            try:
                interaction = self._client.interactions.create(**kwargs)
                break
            except Exception as exc:  # noqa: BLE001 - never leak SDK internals / keys
                last_exc = exc
                logger.warning(f"gemini_generate_failed attempt {attempt+1}", extra={"error_type": type(exc).__name__})
                time.sleep(2 ** attempt) # Exponential backoff
        
        if interaction is None:
            raise LLMError("The language model request failed after retries") from last_exc

        text = getattr(interaction, "output_text", None)
        if not text:
            raise LLMError("The language model returned an empty response")
        return text


# ---------------------------------------------------------------------------
# Deterministic offline provider
# ---------------------------------------------------------------------------

_SOURCE_BLOCK_RE = re.compile(
    r'<source label="(S\d+)">.*?Content:\n"""\n(.*?)\n"""\n</source>', re.DOTALL
)
_FIELD_RE = re.compile(r"^STANDALONE QUESTION:\s*(.+)$", re.MULTILINE)
_LEVEL_RE = re.compile(r"^EXPLANATION LEVEL:\s*(\w+)", re.MULTILINE)


class ExtractiveMockLLM:
    """Deterministic extractive 'LLM' that only quotes the evidence it is given.

    It behaves like a well-aligned model: it answers from the labelled evidence,
    cites the labels it used, and reports ``grounded=false`` when nothing in the
    evidence overlaps with the question. It never follows instructions found in
    evidence because it does not interpret evidence as instructions at all.
    """

    name = "mock"

    def generate(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        context: str = "",
        conversation_history: Sequence[LLMMessage] = (),
        response_schema: dict[str, Any] | None = None,
        temperature: float = 0.0,
    ) -> str:
        props = (response_schema or {}).get("properties", {})
        if "standalone_query" in props:
            # Deterministic rewrite for offline tests
            q = user_prompt.replace("Please rewrite this query to be standalone: ", "").strip()
            if "it" in q.lower() and conversation_history:
                last_user = next((m.content for m in reversed(conversation_history) if m.role == "user"), "")
                words = [w for w in last_user.split() if len(w) > 4]
                noun = words[-1] if words else "the concept"
                q = q.replace("it", noun).replace("It", noun.capitalize())
            return json.dumps({"standalone_query": q})
            
        if "cited_sources" not in props:
            return json.dumps(
                {"outside_knowledge": "Outside knowledge is unavailable in offline mock mode."}
            )

        q_match = _FIELD_RE.search(user_prompt)
        question = q_match.group(1) if q_match else user_prompt
        level_match = _LEVEL_RE.search(user_prompt)
        level = level_match.group(1).lower() if level_match else "intermediate"
        q_terms = set(content_terms(question))

        scored: list[tuple[int, int, str, str]] = []
        for order, (label, body) in enumerate(_SOURCE_BLOCK_RE.findall(context)):
            overlap = len(q_terms & set(content_terms(body)))
            if overlap:
                scored.append((-overlap, order, label, body))
        scored.sort()

        if not scored:
            return json.dumps({"grounded": False, "answer": "", "cited_sources": []})

        n_sentences = 1 if level == "beginner" else (3 if level == "advanced" else 2)
        pieces: list[str] = []
        cited: list[str] = []
        for _, _, label, body in scored[:2]:
            relevant = [s for s in sentences(body) if q_terms & set(content_terms(s))] or sentences(body)
            snippet = " ".join(relevant[:n_sentences]).strip()
            if snippet:
                pieces.append(f"{snippet} [{label}]")
                cited.append(label)
        prefix = "In simple terms: " if level == "beginner" else "According to the course material: "
        return json.dumps({"grounded": True, "answer": prefix + " ".join(pieces), "cited_sources": cited})
