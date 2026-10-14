"""Tests for Member 4 Learner Model & Personalization Engine."""

import pytest
from app.assessment.models import (
    AssessmentReport,
    QuestionEvaluation,
)
from app.kb.graph_store import GraphStore
from app.kb.models import ConceptNode, CourseKnowledgeGraph, PrerequisiteEdge
from app.learner.engine import LearnerModelEngine
from app.learner.models import ConceptMastery
from app.learner.service import LearnerModelService
from app.tutor.knowledge_base import KnowledgeBase
from app.tutor.models import ContentUnit, PdfSource, TutorTurnEvent
from app.tutor.providers.embeddings import HashingEmbeddingProvider
from app.tutor.vector_store import InMemoryVectorStore


@pytest.fixture
def learner_setup():
    graph_store = GraphStore()
    kb = KnowledgeBase(store=InMemoryVectorStore(), embedder=HashingEmbeddingProvider())

    # Build graph with prerequisite dependency: Chain Rule -> Backprop
    graph = CourseKnowledgeGraph(
        course_id="test_course",
        nodes={
            "c_chain_rule": ConceptNode(
                id="c_chain_rule",
                course_id="test_course",
                name="Chain Rule",
                topic="Calculus",
            ),
            "c_backprop": ConceptNode(
                id="c_backprop",
                course_id="test_course",
                name="Backpropagation",
                topic="Neural Networks",
            ),
        },
        edges=[
            PrerequisiteEdge(
                source_concept_id="c_chain_rule",
                target_concept_id="c_backprop",
                rationale="Chain rule is the mathematical foundation of backprop",
            )
        ],
    )
    graph_store.save_graph(graph)

    service = LearnerModelService(graph_store=graph_store, kb=kb)
    return service, graph_store, kb


def test_bkt_updates_on_answers():
    engine = LearnerModelEngine()
    concept = ConceptMastery(
        concept_id="c_test",
        concept_name="Test Concept",
        topic="Math",
        p_know=0.20,
    )

    # Correct answer should increase p_know
    engine.update_bkt_on_answer(concept, is_correct=True)
    assert concept.p_know > 0.20
    assert concept.attempts == 1
    assert concept.correct_count == 1

    first_val = concept.p_know

    # Incorrect answer should reduce probability
    engine.update_bkt_on_answer(concept, is_correct=False)
    assert concept.p_know < first_val
    assert concept.attempts == 2


def test_prerequisite_gap_diagnosis(learner_setup):
    service, _, _ = learner_setup
    profile = service.get_or_create_profile("user_123", "test_course")

    # Simulate student failing backprop while chain rule is unmastered
    profile.concepts["c_backprop"].p_know = 0.25
    profile.concepts["c_backprop"].recalculate_status()
    profile.concepts["c_chain_rule"].p_know = 0.20
    profile.concepts["c_chain_rule"].recalculate_status()

    graph = service.graph_store.get_graph("test_course")
    service.engine.recompute_profile(profile, graph)

    # System should diagnose Chain Rule as the root cause blocker!
    recs = profile.recommendations
    assert len(recs) > 0
    top_rec = recs[0]
    assert top_rec.prerequisite_blocker_id == "c_chain_rule"
    assert top_rec.action == "review_prerequisite"
    assert "foundational gap" in top_rec.reason


def test_tutor_telemetry_integration(learner_setup):
    service, _, _ = learner_setup
    event = TutorTurnEvent(
        user_id="user_123",
        course_id="test_course",
        conversation_id="conv_1",
        message_id="msg_1",
        question="How does the chain rule work in calculus?",
        rewritten_query="How does the chain rule work in calculus?",
        grounded=True,
        topics=["Calculus"],
        concepts=["Chain Rule"],
        cited_chunk_ids=["chunk_1"],
        level="intermediate",
    )

    profile_before = service.get_or_create_profile("user_123", "test_course")
    init_p = profile_before.concepts["c_chain_rule"].p_know

    service.on_tutor_turn(event)

    profile_after = service.get_or_create_profile("user_123", "test_course")
    assert profile_after.tutor_turns == 1
    assert profile_after.concepts["c_chain_rule"].p_know > init_p
    assert len(profile_after.recent_activity) == 1


def test_learner_simulation(learner_setup):
    service, _, _ = learner_setup
    sim_result = service.run_student_simulation(
        course_id="test_course",
        num_students=3,
        num_sessions=4,
    )

    assert sim_result.num_students == 3
    assert sim_result.num_sessions == 4
    assert sim_result.average_final_mastery >= sim_result.average_initial_mastery
    assert sim_result.mastery_gain_percentage >= 0
    assert sim_result.question_repetition_rate < 0.10
