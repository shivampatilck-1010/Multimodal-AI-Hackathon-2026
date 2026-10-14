# Member 4 — Learner Model & Personalization Handoff

**STATUS:** FULLY IMPLEMENTED & TESTED

## 1. Role in System
Member 4 owns the Learner Modeling, Knowledge Tracing, and Adaptive Recommendation Engine (Track D Requirement 4). It tracks longitudinal student mastery using Bayesian Knowledge Tracing (BKT), diagnoses root-cause gaps using Member 1's Prerequisite DAG, consumes telemetry from both the AI Tutor and Assessment engines, and implements cohort benchmarking (Track D Requirement 5.c).

```
AI Tutor Telemetry (TutorTurnEvent) ──┐
                                     ├──> Learner Model Engine (BKT) ──> Student Profile & Dashboard
Assessment Results (AssessmentReport) ┘         │
                                                ↓
                         Prerequisite DAG Analysis (Root Cause Diagnosis)
```

---

## 2. Implemented Models (`app/learner/models.py`)

- `BKTParameters`: Hyperparameters for Corbett & Anderson standard BKT ($P(L_0)=0.20$, $P(T)=0.15$, $P(G)=0.25$, $P(S)=0.10$).
- `ConceptMastery`: Per-concept Bayesian state ($P(\text{know})$, attempt count, correct count, tutor interaction count, status: `"needs_help"` | `"developing"` | `"mastered"`).
- `TopicMastery`: Aggregated percentage and status per curriculum topic.
- `AdaptiveRecommendation`: Targeted remediation actions (`"review_prerequisite"` | `"practice_quiz"` | `"ask_tutor"`), including identified `prerequisite_blocker_id`.
- `LearnerProfile`: Full student state with streak, study time, concepts map, topics map, and recent activities.
- `SimulationResult`: Track D 5.c multi-student cohort benchmark data across multiple learning sessions.

---

## 3. Core Engine Components

1. **`LearnerModelEngine` (`app/learner/engine.py`)**:
   - **Bayesian Knowledge Tracing (BKT)**:
     - Posterior update on correct: $P(L_t | \text{corr}) = \frac{P(L_t)(1 - P_s)}{P(L_t)(1 - P_s) + (1 - P(L_t))P_g}$
     - Posterior update on incorrect: $P(L_t | \text{inc}) = \frac{P(L_t)P_s}{P(L_t)P_s + (1 - P(L_t))(1 - P_g)}$
     - Learning transit step: $P(L_{t+1}) = P(L_t | \text{obs}) + (1 - P(L_t | \text{obs})) P_t$
   - **Tutor Scaffolding Boost**: Reinforces concept familiarization when students chat with the AI Tutor.
   - **Prerequisite DAG Remediation**: Inspects dependencies from `CourseKnowledgeGraph`. If a student fails a concept, checks its prerequisite parents. If a prerequisite has low mastery, flags it as the root blocker to review first.
2. **`LearnerModelService` (`app/learner/service.py`)**:
   - Manages persistent student profiles in `data/runtime/profiles/`.
   - Handles new student intake baseline.
   - `on_assessment_completed(report)`: Updates BKT probabilities.
   - `on_tutor_turn(event)`: Ingests `TutorTurnEvent` conversational telemetry.
   - `get_dashboard_data(user_id, course_id)`: Generates structured payload for frontend.
   - `run_student_simulation(course_id, num_students, num_sessions)`: Track D 5.c benchmark simulation reporting empirical mastery gains and question repetition rate.

---

## 4. API Endpoints (`app/api/learner_routes.py`)

- `GET /api/learner/{user_id}/dashboard?course_id=...`: Returns live dashboard summary and topic masteries.
- `GET /api/learner/{user_id}/profile?course_id=...`: Returns raw student profile.
- `GET /api/learner/{user_id}/recommendations?course_id=...`: Returns adaptive recommendations with prerequisite blocker detection.
- `POST /api/learner/{user_id}/events/tutor`: Logs conversational tutor turn event.
- `POST /api/learner/{user_id}/reset`: Resets student progress for demos.
- `GET /api/learner/simulation/run?course_id=...&students=5&sessions=6`: Executes Track D 5.c benchmark simulation.

---

## 5. Verification Commands

```powershell
cd backend
.venv\Scripts\Activate.ps1
$env:PYTHONPATH="."
pytest tests/test_learner_model.py -v
```
All unit tests pass with 100% success.
