# Member 1 — Multimodal Knowledge Base Handoff

## 1. Role in System

Member 1 owns the Multimodal Knowledge Base layer: the authoritative ingestion, extraction, chunking, and semantic indexing of all raw course assets.

```
RAW ASSETS (PDF / PPTX / MP4)
        ↓
Multimodal Extractors & Parsers (PyMuPDF, python-pptx, Whisper/ffmpeg)
        ↓
Figure & Diagram Understanding (Captions, Explanations, Coordinates)
        ↓
Semantic Chunker (Preserving exact Page / Slide / Timestamps)
        ↓
Taxonomy & Prerequisite DAG Engine (Topics, Subtopics, Concepts, Dependencies)
        ↓
Knowledge Base & Media Store
        ↓
API Contracts for Members 2, 3, & 4
```

---

## 2. Provenance Guarantees

Every piece of retrieved text and every visual figure maintains an unbreakable source link:

| Modality | Provenance Fields | Exact Location Format |
| :--- | :--- | :--- |
| **PDF Textbooks / Notes** | `file_name`, `page` | `Page 42` (1-indexed) |
| **Slide Decks (PPTX)** | `file_name`, `slide` | `Slide 5` (1-indexed, including notes) |
| **Lecture Videos / Audio** | `file_name`, `timestamp_start`, `timestamp_end` | `00:05:30 - 00:07:00` (`HH:MM:SS`) |
| **Diagrams & Figures** | `source` (`PdfSource` / `SlideSource`), `bounding_box` | Exact page/slide coordinates & crop |

---

## 3. Data Contracts & Models

All models reside in `app/kb/models.py` and strictly maintain 100% interoperability with `app/tutor/models.py`.

### 3.1 ContentUnit (For Member 2 Retriever)
```python
class ContentUnit(BaseModel):
    id: str                                  # e.g. "unit_bio101_p42_01"
    course_id: str                           # Boundary: e.g. "biology_101"
    text: str                                # 1 - 20,000 chars
    topic: str | None                        # e.g. "Photosynthesis"
    subtopic: str | None                     # e.g. "Light-Dependent Reactions"
    concept: str | None                      # e.g. "Thylakoid Membrane"
    source: PdfSource | SlideSource | VideoSource
    metadata: dict[str, Any]                 # { "figure_ids": [...], "page": 42 }
```

### 3.2 FigureUnit (For Diagram Understanding & Member 3 Assessment Questions)
```python
class FigureUnit(BaseModel):
    id: str                                  # e.g. "fig_bio101_p42_1"
    course_id: str
    source: PdfSource | SlideSource | VideoSource
    image_rel_path: str                      # Local asset path
    caption: str                             # Extracted or generated title
    explanation: str                         # Deep multimodal explanation of diagram
    associated_concepts: list[str]           # Linked concepts
    bounding_box: BoundingBox | None         # {x0, y0, x1, y1}
```

### 3.3 ConceptNode & CourseKnowledgeGraph (For Member 3 Scoping & Member 4 Mastery)
```python
class ConceptNode(BaseModel):
    id: str                                  # e.g. "concept_calvin_cycle"
    course_id: str
    name: str                                # "Calvin Cycle"
    topic: str                               # "Cellular Energetics"
    subtopic: str | None                     # "Photosynthesis"
    summary: str                             # 1-2 sentence core definition
    content_unit_ids: list[str]              # Units covering this concept
    figure_ids: list[str]                    # Diagrams illustrating this concept

class PrerequisiteEdge(BaseModel):
    source_concept_id: str                   # Prerequisite (must learn first)
    target_concept_id: str                   # Dependent concept
    rationale: str                           # Pedagogical reasoning
    strength: float                          # 0.0 - 1.0 confidence

class CourseKnowledgeGraph(BaseModel):
    course_id: str
    nodes: dict[str, ConceptNode]
    edges: list[PrerequisiteEdge]
    topics_hierarchy: dict[str, dict[str, list[str]]]
```

---

## 4. API Endpoints

### Ingestion & Search
- `POST /api/kb/upload` (Multipart: `file`, `course_id`): Ingests PDF, PPTX, or Video end-to-end and updates vector index + prerequisite DAG.
- `POST /api/kb/ingest` (JSON: `{ "units": [ContentUnit, ...] }`): Direct batch ingestion.
- `GET /api/kb/search?course_id=...&query=...&top_k=6`: Semantic vector retrieval with optional `topic` and `concept` filters.
- `GET /api/kb/courses`: Lists courses and chunk counts.
- `GET /api/kb/courses/{course_id}/units`: Lists all chunks in a course.

### Figures & Visual Assets
- `GET /api/kb/courses/{course_id}/figures`: Lists all diagrams and figures with metadata.
- `GET /api/kb/figures/{course_id}/{figure_id}`: Metadata and multimodal explanation for a figure.
- `GET /api/kb/figures/{course_id}/{figure_id}/image`: Streams the raw image file for frontend display.

### For Member 3 (Assessment Grounding)
- `GET /api/kb/courses/{course_id}/concepts`: List all concepts for question scoping.
- `GET /api/kb/courses/{course_id}/concepts/{concept_id}/evidence`: Returns concept definition, all linked `ContentUnit` chunks, and all linked `FigureUnit`s. Member 3 uses this to generate strictly-grounded MCQs and figure-based questions with validated citations.

### For Member 4 (Learner Model Mastery)
- `GET /api/kb/courses/{course_id}/prerequisites`: Full DAG of prerequisite relationships with cycle detection guaranteed.
- `GET /api/kb/courses/{course_id}/learning_path`: Topological sort ordering of concepts (prerequisites first) for student learning progressions.
- `GET /api/kb/courses/{course_id}/hierarchy`: Nested `Topic -> Subtopic -> Concepts` hierarchy for student mastery dashboards.

---

## 5. Verification Commands

Run Member 1 test suite:
```powershell
cd backend
pytest tests/test_member1_pipeline.py -v
```
