"""Bayesian Knowledge Tracing and Prerequisite Remediation Engine.

Implements standard educational data mining algorithms:
1. Corbett & Anderson standard Bayesian Knowledge Tracing (BKT)
2. DAG Prerequisite gap diagnosis (recommending root-cause blockers)
3. Zone of Proximal Development (ZPD) adaptive sequencing
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from app.kb.graph_store import GraphStore
from app.kb.models import CourseKnowledgeGraph
from app.learner.models import (
    AdaptiveRecommendation,
    BKTParameters,
    ConceptMastery,
    LearnerProfile,
    TopicMastery,
)

logger = logging.getLogger(__name__)


class LearnerModelEngine:
    """Computes Bayesian student knowledge updates and prerequisite remediation."""

    def __init__(self, bkt_params: BKTParameters | None = None) -> None:
        self.params = bkt_params or BKTParameters()

    def update_bkt_on_answer(
        self,
        mastery: ConceptMastery,
        is_correct: bool,
    ) -> None:
        """Standard Corbett & Anderson Bayesian Knowledge Tracing update."""
        p_l = mastery.p_know
        p_g = self.params.p_guess
        p_s = self.params.p_slip
        p_t = self.params.p_transit

        # 1. Posterior calculation
        if is_correct:
            numerator = p_l * (1.0 - p_s)
            denominator = numerator + ((1.0 - p_l) * p_g)
        else:
            numerator = p_l * p_s
            denominator = numerator + ((1.0 - p_l) * (1.0 - p_g))

        # Guard against zero division
        posterior = numerator / denominator if denominator > 0 else p_l

        # 2. Knowledge transit step
        p_l_next = posterior + ((1.0 - posterior) * p_t)
        mastery.p_know = round(max(0.01, min(0.99, p_l_next)), 4)
        mastery.attempts += 1
        if is_correct:
            mastery.correct_count += 1
        mastery.last_interaction = datetime.now(UTC)
        mastery.recalculate_status()

    def update_on_tutor_turn(
        self,
        mastery: ConceptMastery,
    ) -> None:
        """Reinforce concept exposure when a student engages with the AI Tutor."""
        # Tutor explanation provides scaffolding, slight boost in transit
        p_l = mastery.p_know
        boost = 0.08 * (1.0 - p_l)
        mastery.p_know = round(min(0.95, p_l + boost), 4)
        mastery.tutor_queries_count += 1
        mastery.last_interaction = datetime.now(UTC)
        mastery.recalculate_status()

    def recompute_profile(
        self,
        profile: LearnerProfile,
        graph: CourseKnowledgeGraph | None = None,
    ) -> None:
        """Recompute aggregated topic masteries, weak/strong concepts, and adaptive recommendations."""
        if not profile.concepts:
            return

        # 1. Group concepts by topic
        topics_map: dict[str, list[ConceptMastery]] = {}
        for c in profile.concepts.values():
            topics_map.setdefault(c.topic, []).append(c)

        topics_result: dict[str, TopicMastery] = {}
        total_mastery_sum = 0.0

        for topic_name, concepts in topics_map.items():
            avg_p = sum(c.p_know for c in concepts) / len(concepts)
            mastered_count = sum(1 for c in concepts if c.status == "mastered")
            total_mastery_sum += avg_p

            t_status = "needs_help"
            if avg_p >= 0.75:
                t_status = "mastered"
            elif avg_p >= 0.45:
                t_status = "developing"

            topics_result[topic_name] = TopicMastery(
                topic_name=topic_name,
                mastery_percentage=round(avg_p * 100, 1),
                total_concepts=len(concepts),
                mastered_concepts=mastered_count,
                status=t_status,
            )

        profile.topics = topics_result
        if topics_result:
            profile.overall_mastery = round((total_mastery_sum / len(topics_result)) * 100, 1)

        # 2. Identify weak and strong concepts
        profile.weak_concepts = [
            c.concept_name for c in profile.concepts.values() if c.status == "needs_help"
        ]
        profile.strong_concepts = [
            c.concept_name for c in profile.concepts.values() if c.status == "mastered"
        ]

        # 3. Generate adaptive recommendations with Prerequisite Graph gap diagnosis
        profile.recommendations = self.generate_adaptive_recommendations(profile, graph)
        profile.updated_at = datetime.now(UTC)

    def generate_adaptive_recommendations(
        self,
        profile: LearnerProfile,
        graph: CourseKnowledgeGraph | None,
    ) -> list[AdaptiveRecommendation]:
        """Examine prerequisite DAG to find root causes and optimal next steps."""
        recs: list[AdaptiveRecommendation] = []

        # Find concepts needing help
        weak_c_list = [c for c in profile.concepts.values() if c.status == "needs_help"]

        for weak in weak_c_list:
            blocker_id = None
            blocker_name = None

            if graph:
                # Check prerequisites of this weak concept
                prereqs = graph.get_prerequisites(weak.concept_id)
                for pid in prereqs:
                    prereq_mastery = profile.concepts.get(pid)
                    # If prerequisite is also weak or never studied, it is the root blocker!
                    if not prereq_mastery or prereq_mastery.p_know < 0.50:
                        blocker_id = pid
                        blocker_name = (
                            graph.nodes[pid].name if pid in graph.nodes else pid
                        )
                        break

            if blocker_id and blocker_name:
                recs.append(
                    AdaptiveRecommendation(
                        concept_id=weak.concept_id,
                        concept_name=weak.concept_name,
                        topic=weak.topic,
                        priority="high",
                        reason=f"Struggling with '{weak.concept_name}', but the foundational gap is prerequisite '{blocker_name}'.",
                        action="review_prerequisite",
                        prerequisite_blocker_id=blocker_id,
                        prerequisite_blocker_name=blocker_name,
                    )
                )
            else:
                recs.append(
                    AdaptiveRecommendation(
                        concept_id=weak.concept_id,
                        concept_name=weak.concept_name,
                        topic=weak.topic,
                        priority="medium",
                        reason=f"Current mastery is {int(weak.p_know * 100)}%. Target practice recommended.",
                        action="practice_quiz",
                    )
                )

        # If everything mastered or developing, suggest ZPD next step
        if not recs:
            developing = [c for c in profile.concepts.values() if c.status == "developing"]
            if developing:
                target = developing[0]
                recs.append(
                    AdaptiveRecommendation(
                        concept_id=target.concept_id,
                        concept_name=target.concept_name,
                        topic=target.topic,
                        priority="low",
                        reason=f"Almost mastered! Take a short quiz to solidify '{target.concept_name}'.",
                        action="practice_quiz",
                    )
                )
            else:
                recs.append(
                    AdaptiveRecommendation(
                        concept_id="comprehensive",
                        concept_name="Course Mastery Review",
                        topic="All Topics",
                        priority="low",
                        reason="All foundational concepts mastered. Take a comprehensive mock exam!",
                        action="practice_quiz",
                    )
                )

        # Sort recommendations by priority (high > medium > low)
        priority_order = {"high": 0, "medium": 1, "low": 2}
        recs.sort(key=lambda r: priority_order.get(r.priority, 3))

        return recs[:5]
