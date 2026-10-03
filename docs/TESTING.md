# Testing

This document contains testing guidelines and commands for the project.

## Running Tests

For Member 2 (RAG + AI Tutor), the following commands run the deterministic tests locally without requiring an API key.

1. Ensure the virtual environment is activated and the python path is set:
```powershell
cd backend
.venv\Scripts\Activate.ps1
$env:PYTHONPATH="."
```

2. Run unit and integration tests using pytest:
```powershell
pytest -q
```

3. Run end-to-end query verifications:
```powershell
python scripts/test_query.py
```

## Member 1 Testing (Multimodal Knowledge Base)

Run the full Member 1 suite (models, graph DAG acyclicity, topological sort, video timestamps, PDF/PPTX chunking):
```powershell
cd backend
$env:PYTHONPATH="."
pytest tests/test_member1_pipeline.py -v
```

Test multimodal database seeding (injects textbook excerpts, slides with notes, and timestamped lecture video chunks):
```powershell
cd backend
$env:PYTHONPATH="."
python scripts/seed_multimodal.py
```

*Note: Member 3 and 4 testing commands are awaiting their respective implementations.*
