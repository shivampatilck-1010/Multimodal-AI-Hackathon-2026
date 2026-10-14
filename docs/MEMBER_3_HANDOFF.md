# Member 3 — Adaptive Assessment Engine Handoff

**STATUS:** FULLY IMPLEMENTED & TESTED

## 1. Role in System
Member 3 owns the Adaptive Assessment and Evaluation layer (Track D Requirement 3). It generates source-grounded quizzes, verifies answers, produces cited feedback pointing to exact pages/slides, identifies student misconceptions, and dispatches performance telemetry to the Member 4 Learner Model.

```
COURSE MATERIAL & CONCEPTS (Member 1 KB)
         ↓
Source-Grounded Retrieval (Member 2 Retriever)
         ↓
Assessment Generator (MCQ, Short Answer, Numerical)
         ↓
Student Taking Quiz (React Frontend / API)
         ↓
Assessment Evaluator (Scoring, Misconceptions, Exact Citations)
         ↓
Telemetry Dispatched to Learner Model (Member 4 BKT Updates)
```

---

## 2. Implemented Models (`app/assessment/models.py`)

- `AssessmentQuestion`:
  - `id`: Unique identifier
  - `course_id`: Boundary isolation identifier
  - `concept_id` & `concept_name`: Target concept
  - `topic`: Major subject topic
  - `question_type`: `"mcq"` | `"short_answer"` | `"numerical"`
  - `difficulty`: `"easy"` | `"medium"` | `"hard"`
  - `question_text`: Grounded prompt
  - `options`: List of `{ key, text }` choices (A, B, C, D)
  - `correct_answer`: Correct key or value
  - `explanation`: Pedagogical explanation
  - `misconception_distractors`: Map of option keys to specific misconception tags
  - `source`: Complete `SourceReference` provenance (`file_name`, `page`, `slide`, `timestamp_start`)
  - `chunk_id`: Knowledge base chunk origin
- `AssessmentQuiz`: Complete quiz session holding an array of questions.
- `QuestionEvaluation`: Individual grading result with score, feedback, cited source, and detected misconception.
- `AssessmentReport`: Post-assessment diagnostic report with score percentage, weak/strong topics, misconceptions, and recommendations.

---

## 3. Core Engine Components

1. **`AssessmentGenerator` (`app/assessment/generator.py`)**:
   - Queries `KnowledgeBase` and `Retriever` to select course chunks covering target concepts.
   - Prompts LLM using structured JSON schema to generate conceptual questions.
   - Seamlessly falls back to deterministic grounded question extraction when running offline without an API key.
   - Prevents question repetition via cryptographic question hashing.
2. **`AssessmentEvaluator` (`app/assessment/evaluator.py`)**:
   - Grades submitted student answers.
   - Pinpoints specific misconceptions when students select distractors.
   - Synthesizes exact source citations into explanatory feedback.
   - Generates post-assessment diagnosis and recommendations.
3. **`AssessmentService` (`app/assessment/service.py`)**:
   - Coordinates active quiz sessions.
   - Automatically notifies `LearnerModelService.on_assessment_completed(report)` to trigger real-time Bayesian Knowledge Tracing updates.

---

## 4. API Endpoints (`app/api/assessment_routes.py`)

- `POST /api/assessments/generate`:
  - Body: `{ course_id, topic, concept_id, num_questions, difficulty }`
  - Returns: `AssessmentQuiz`
- `GET /api/assessments/{quiz_id}`:
  - Returns: `AssessmentQuiz`
- `POST /api/assessments/submit`:
  - Body: `{ assessment_id, user_id, course_id, answers: [{ question_id, selected_answer }] }`
  - Returns: `AssessmentReport`
- `GET /api/assessments/history/{user_id}`:
  - Returns historical assessment reports for a student.

---

## 5. Verification Commands

```powershell
cd backend
.venv\Scripts\Activate.ps1
$env:PYTHONPATH="."
pytest tests/test_assessment.py -v
```
All unit tests pass with 100% success.
