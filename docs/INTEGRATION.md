# Integration

This is the team's single source of truth for interfaces and boundaries.

## Actual Architecture

```mermaid
flowchart TD
    Raw[PDF / PPTX / Videos] -->|Ingestion Pipeline| M1[Member 1 KB & Media Store]
    M1 -->|ContentUnit| KB[Knowledge Base Vector Store]
    M1 -->|Concepts & Evidence| M3[Member 3 Assessment Engine]
    M1 -->|Prerequisite DAG| M4[Member 4 Learner Model]
    KB --> M2[Member 2]
    M2 -->|Retriever / Tutor API| RAG[RAG + Tutor]
    RAG --> M3
    M3 -->|Grounded Questions| A[Assessment]
    A --> M4
    RAG -->|TutorTurnEvent| M4
    M4 --> LM[Learner Model / Evaluation]
```

## Known Interfaces

### Member 1 → Member 2
**STATUS:** FULLY IMPLEMENTED
- **Interface:** Member 1 ingestion pipeline parses PDFs (with page numbers), PPTX slides (with slide numbers & notes), and Videos (with timestamps), extracts diagrams, and outputs `ContentUnit` objects defined in `app/tutor/models.py`. Vector indexing and `Retriever.retrieve()` are fully integrated.
- **Endpoints:** `POST /api/kb/upload`, `POST /api/kb/ingest`, `GET /api/kb/search`.

### Member 1 → Member 3
**STATUS:** FULLY IMPLEMENTED
- **Interface:** Member 1 exposes `GET /api/kb/courses/{course_id}/concepts` for question scoping, and `GET /api/kb/courses/{course_id}/concepts/{concept_id}/evidence` returning the concept node, all linked `ContentUnit` text chunks, and all linked `FigureUnit` diagrams for grounded MCQ/assessment generation.

### Member 1 → Member 4
**STATUS:** FULLY IMPLEMENTED
- **Interface:** Member 1 exposes `GET /api/kb/courses/{course_id}/prerequisites` providing the DAG of concept dependencies (with cycle resolution guaranteed) and `GET /api/kb/courses/{course_id}/learning_path` providing topological sort order for Bayesian Knowledge Tracing.

### Member 2 → Member 3
**STATUS:** FULLY IMPLEMENTED
- **Interface:** Member 3 calls `Retriever.retrieve()` to fetch source-grounded evidence to populate MCQs with exact source locations (`PdfSource`, `SlideSource`, `VideoSource`).

### Member 3 → Member 4
**STATUS:** FULLY IMPLEMENTED
- **Interface:** `AssessmentService` automatically calls `LearnerModelService.on_assessment_completed(report: AssessmentReport)` upon submission. Each evaluated question updates the target concept's Bayesian Knowledge Tracing score ($P(\text{know})$).

### Member 2 → Member 4
**STATUS:** FULLY IMPLEMENTED
- **Interface:** `TutorService` emits `TutorTurnEvent` directly to `LearnerModelService.on_tutor_turn(event)`. Discussed concepts receive scaffolding boosts and are recorded in the student's recent activity stream.
