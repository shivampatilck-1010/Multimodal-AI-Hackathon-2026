"""Evidence gate: decides whether retrieved evidence is strong enough to answer.

Runs BEFORE generation. If it fails, the LLM is never asked for a course answer,
which removes the opportunity to hallucinate one.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.tutor.models import RetrievedChunk
from app.tutor.text import term_coverage


@dataclass(frozen=True)
class GroundingDecision:
    sufficient: bool
    reason: str
    threshold: float
    evidence: list[RetrievedChunk] = field(default_factory=list)
    top_score: float = 0.0
    term_coverage: float | None = None


class EvidenceGate:
    def __init__(
        self,
        min_score: float,
        min_chunks: int = 1,
        min_term_coverage: float = 0.0,
        max_evidence: int = 6,
    ) -> None:
        self.min_score = min_score
        self.min_chunks = min_chunks
        self.min_term_coverage = min_term_coverage
        self.max_evidence = max_evidence

    def evaluate(self, query: str, chunks: list[RetrievedChunk]) -> GroundingDecision:
        if not chunks:
            return GroundingDecision(False, "No course material was retrieved for this question.", self.min_score)

        top = max(c.score for c in chunks)
        evidence = [c for c in chunks if c.score >= self.min_score][: self.max_evidence]
        if len(evidence) < self.min_chunks:
            return GroundingDecision(
                False,
                f"No retrieved evidence met the relevance threshold "
                f"(best score {top:.3f} < {self.min_score:.3f}).",
                self.min_score,
                top_score=top,
            )

        coverage = None
        if self.min_term_coverage > 0:
            coverage = term_coverage(query, [c.text + " " + (c.topic or "") + " " + (c.concept or "") for c in evidence])
            if coverage < self.min_term_coverage:
                return GroundingDecision(
                    False,
                    f"Retrieved evidence covers too little of the question "
                    f"(term coverage {coverage:.2f} < {self.min_term_coverage:.2f}).",
                    self.min_score,
                    top_score=top,
                    term_coverage=coverage,
                )

        return GroundingDecision(
            True,
            f"{len(evidence)} evidence chunk(s) at or above threshold {self.min_score:.3f}.",
            self.min_score,
            evidence=evidence,
            top_score=top,
            term_coverage=coverage,
        )
