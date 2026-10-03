# Multimodal AI Hackathon 2026

## Track D — Personalized Tutoring & Adaptive Learning

## Overview
Build an AI study companion that unifies lecture videos, textbooks, and slides into a source-cited knowledge base, and uses it to run adaptive assessments and personalized tutoring.

## Core Features
- **Unified Multimodal Knowledge Base (Member 1):** Ingests textbook PDFs, PowerPoint slide decks (PPT/PPTX), and lecture videos without manual preprocessing, preserving exact provenance (page, slide, timestamp ranges).
- **Diagram & Figure Understanding (Member 1):** Extracts figures and visual diagrams with coordinate bounding boxes, generating semantic explanations and concept associations.
- **Taxonomy & Prerequisite DAGs (Member 1):** Hierarchically organizes material into Topics, Subtopics, and Concepts; discovers prerequisite dependencies and computes pedagogical learning paths with cycle detection.
- **Generative RAG Tutor Layer (Member 2):** Built with strict evidence-gating to prevent hallucination, enforcing source citations.
- **Adaptive Assessments (Member 3):** Grounded questions backed directly by course material and concept evidence.
- **Learner Model (Member 4):** Maintains long-term student mastery tracking and weakness topic modeling.

## System Architecture

```mermaid
flowchart LR
    Ingest[PDFs / Slides / Videos] -->|Parsers + Vision| M1[Member 1 KB & Media Store]
    M1 -->|ContentUnit| KB[Vector Store Index]
    M1 -->|Concepts & Evidence| M3[Assessments]
    M1 -->|Prerequisite DAG| M4[Learner Model]
    KB --> M2[RAG Tutor]
    M2 --> M3
    M3 --> M4
    M2 --> M4
```

## Project Structure
- `backend/app/ingestion/` - Multimodal parsers (PDF, PPTX, Video/Whisper), vision analysis, semantic chunking, and taxonomy extraction.
- `backend/app/kb/` - Knowledge base models, graph store (prerequisite DAGs), and media asset store.
- `backend/app/tutor/` - RAG tutor logic, evidence gating, and citation validation.
- `backend/app/api/` - REST API routes for ingestion, search, concepts, prerequisites, and tutor interaction.
- `docs/` - Central project integration and architecture documentation.
- `scripts/` - Ingestion, seeding, and automated evaluation scripts.

## Prerequisites
- Python 3.10+
- (Optional) `google-genai` capable API Key for live testing (deterministic offline hashing embedder & mock LLM available for offline dev).

## Environment Variables
The application uses the `GEMINI_API_KEY` for generative capabilities. 

Example only (place in `backend/.env`):
```env
GEMINI_API_KEY=your_gemini_api_key_here
```
*(Never include the real key in source code).*

## Local Setup

### Running the Backend

1. Navigate to the backend directory:
   ```powershell
   cd backend
   ```
2. Set the Python path:
   ```powershell
   $env:PYTHONPATH="."
   ```
3. Start the application:
   ```powershell
   uvicorn app.main:app --port 8000
   ```
   The API will be available at `http://localhost:8000` (docs at `http://localhost:8000/docs`).

### Seeding Multimodal Course Materials

The server automatically auto-seeds `backend/data/sample_course.json` on startup when the Knowledge Base is empty. You can also re-seed or seed custom multimodal datasets anytime:
```powershell
cd backend
$env:PYTHONPATH="."
python scripts/seed_multimodal.py
```

### Running the Frontend

1. Navigate to the frontend directory:
   ```powershell
   cd frontend
   ```
2. Install dependencies:
   ```powershell
   npm install
   ```
3. Start the Vite dev server:
   ```powershell
   npm run dev
   ```
   Open `http://localhost:5173` in your browser.

For full frontend architecture, component layout, and mock data documentation, see [docs/dashboard.md](docs/dashboard.md).

## Key API Endpoints

Interactive Swagger documentation is available at `http://localhost:8000/docs`.

| Endpoint | Method | Consumer | Description |
| :--- | :--- | :--- | :--- |
| `/api/kb/upload` | `POST` | Member 1/All | Ingest raw PDF, PPTX, or Video/Audio with diagram understanding and DAG generation. |
| `/api/kb/search` | `GET` | Member 2 | Vector search with optional `topic` and `concept` filters. |
| `/api/kb/courses/{course_id}/concepts` | `GET` | Member 3 | List all identified concepts for question scoping. |
| `/api/kb/courses/{course_id}/concepts/{concept_id}/evidence` | `GET` | Member 3 | Fetch concept definition, text chunks, and diagrams for grounded question generation. |
| `/api/kb/figures/{course_id}/{figure_id}` | `GET` | Member 3 | Figure metadata, coordinate bounding boxes, and multimodal explanation. |
| `/api/kb/figures/{course_id}/{figure_id}/image` | `GET` | UI / Member 3 | Stream raw diagram image crop for assessment questions. |
| `/api/kb/courses/{course_id}/prerequisites` | `GET` | Member 4 | Full concept prerequisite DAG (verified acyclic) for student mastery tracking. |
| `/api/kb/courses/{course_id}/learning_path` | `GET` | Member 4 | Topological sort ordering of concepts (prerequisites first). |
| `/api/kb/courses/{course_id}/flowchart` | `GET` | UI / All | Visual course flow map in Mermaid syntax (Track D 6.a). |
| `/api/tutor/ask` | `POST` | Member 2 / UI | Ask tutor questions with strict evidence-gating and verified citations. |

## Testing

Run unit and integration test suites:
```powershell
cd backend
$env:PYTHONPATH="."
pytest tests/ -v
```

Run specific test modules:
```powershell
# Member 1 tests (parsers, provenance, chunking, prerequisite DAGs)
pytest tests/test_member1_pipeline.py -v

# Member 1 end-to-end integration test (multimodal files -> vector search)
pytest tests/test_end_to_end_ingestion.py -v

# Member 2 grounding tests
pytest tests/test_grounding.py -v

# End-to-end query verification script
python scripts/test_query.py
```
For more details, see [docs/TESTING.md](docs/TESTING.md).

## Team Architecture

- **Member 1 (Data Engineer):** [DONE] Multimodal ingestion (PDF, PPTX, Video), diagram understanding, provenance tracking, prerequisite DAGs, and KB API contracts.
- **Member 2 (RAG + AI Tutor Engineer):** [DONE] Generative tutoring, query rewriting, citation validation, and retrieval interfaces.
- **Member 3 (Assessment Engineer):** Grounded MCQ generation and assessment evaluation.
- **Member 4 (Learner Model Engineer):** Student mastery tracking and topic personalization.

## Integration Documentation

- [Member 1 Handoff](docs/MEMBER_1_HANDOFF.md)
- [Member 2 Handoff](docs/MEMBER_2_HANDOFF.md)
- [Member 3 Handoff](docs/MEMBER_3_HANDOFF.md)
- [Member 4 Handoff](docs/MEMBER_4_HANDOFF.md)
- [Central Integration](docs/INTEGRATION.md)
- [Testing Guidelines](docs/TESTING.md)

## Security
- **.env is local:** API keys are never committed.
- **Server-side Gemini configuration:** The backend safely isolates the Gemini API configuration.
- **Students do not provide Gemini credentials:** The UI lacks any API-key inputs.

## Known Limitations
- The Gemini Interactions API endpoint can intermittently return HTTP 503 (Service Unavailable) under rapid burst requests. Exponential backoff has been added to mitigate this.
- Cross-course referencing is intentionally disabled via strict `course_id` isolation.

## Demo
*No demo URL is currently available. Please run the backend locally.*
