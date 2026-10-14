"""End-to-end integration tests for FastAPI assessment and learner endpoints."""

import os
import pytest
from fastapi.testclient import TestClient

# Ensure deterministic offline providers for fast unit testing
os.environ["LLM_PROVIDER"] = "mock"
os.environ["EMBEDDING_PROVIDER"] = "hashing"

from app.main import app


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def test_api_health_check(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_api_assessment_and_learner_loop(client):
    # 1. Generate an assessment
    gen_res = client.post(
        "/api/assessments/generate",
        json={
            "course_id": "hackathon_course",
            "num_questions": 2,
            "difficulty": "medium",
        },
    )
    assert gen_res.status_code == 200
    quiz_data = gen_res.json()
    assert "id" in quiz_data
    assert len(quiz_data["questions"]) >= 1

    # 2. Submit answers
    answers = []
    for q in quiz_data["questions"]:
        answers.append(
            {
                "question_id": q["id"],
                "selected_answer": q["correct_answer"],
            }
        )

    sub_res = client.post(
        "/api/assessments/submit",
        json={
            "assessment_id": quiz_data["id"],
            "user_id": "integration_tester",
            "course_id": "hackathon_course",
            "answers": answers,
        },
    )
    assert sub_res.status_code == 200
    report = sub_res.json()
    assert report["score_percentage"] == 100.0
    assert report["correct_count"] == len(answers)

    # 3. Check student dashboard
    dash_res = client.get("/api/learner/integration_tester/dashboard?course_id=hackathon_course")
    assert dash_res.status_code == 200
    dashboard = dash_res.json()
    assert "summary" in dashboard
    assert "overallMastery" in dashboard["summary"]
    assert "topics" in dashboard
    assert len(dashboard["recentActivity"]) >= 1

    # 4. Check adaptive recommendations
    rec_res = client.get("/api/learner/integration_tester/recommendations?course_id=hackathon_course")
    assert rec_res.status_code == 200
    recs = rec_res.json()
    assert isinstance(recs, list)


def test_api_simulation_run(client):
    sim_res = client.get("/api/learner/simulation/run?course_id=hackathon_course&students=2&sessions=2")
    assert sim_res.status_code == 200
    sim_data = sim_res.json()
    assert sim_data["num_students"] == 2
    assert sim_data["num_sessions"] == 2
    assert sim_data["mastery_gain_percentage"] >= 0
    assert sim_data["question_repetition_rate"] <= 0.05
