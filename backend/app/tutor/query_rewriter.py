"""Query rewriting module."""

import json
import logging
from collections.abc import Sequence

from app.tutor.providers.llm import LLMProvider, LLMMessage

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an AI study companion's query rewriter.
Your task is to take a student's follow-up question and rewrite it into a fully
standalone search query that can be used to retrieve course materials.

Rules:
1. Resolve any pronouns or implicit references using the conversation history.
2. If the user's query is already standalone, return it as-is or slightly clarified.
3. If the user is just saying "thanks" or "hello", return an empty string.
"""

REWRITE_SCHEMA = {
    "type": "object",
    "properties": {
        "standalone_query": {
            "type": "string",
            "description": "The rewritten, standalone search query resolving any references."
        }
    },
    "required": ["standalone_query"]
}

def rewrite_query(
    llm: LLMProvider, 
    query: str, 
    history: Sequence[LLMMessage]
) -> str:
    """Rewrite the query to be standalone. If history is empty, return original."""
    if not history:
        return query
        
    try:
        response_text = llm.generate(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=f"Please rewrite this query to be standalone: {query}",
            conversation_history=history[-4:], # Only last 4 messages needed
            response_schema=REWRITE_SCHEMA,
            temperature=0.0
        )
        data = json.loads(response_text)
        rewritten = data.get("standalone_query", "")
        
        # ExtractiveMockLLM returns empty string to signal heuristic fallback.
        if not rewritten:
            # Fallback heuristic: just prepend the main terms of the previous question
            for msg in reversed(history):
                if msg.role == "user":
                    return f"{msg.content} {query}"
            return query
            
        return rewritten
        
    except Exception as e:
        logger.warning(f"Query rewrite failed: {e}. Falling back to original query.")
        return query
