"""FastAPI application entrypoint."""

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.api.kb_routes import router as kb_router
from app.api.tutor_routes import router as tutor_router
from app.tutor.knowledge_base import KnowledgeBase
from app.tutor.vector_store import InMemoryVectorStore
from app.tutor.providers import build_llm_provider, build_embedding_provider
from app.tutor.service import TutorService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global instances
kb: KnowledgeBase = None
tutor_service: TutorService = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global kb, tutor_service
    settings = get_settings()
    
    # Initialize providers
    llm = build_llm_provider(settings)
    embedder = build_embedding_provider(settings)
    
    # Initialize KB
    vector_store = InMemoryVectorStore()
    persist_dir = settings.data_dir if settings.persist else None
    
    kb = KnowledgeBase(store=vector_store, embedder=embedder, persist_dir=persist_dir)
    logger.info(f"Loaded Knowledge Base with {sum(kb.courses().values())} chunks.")
    
    # Initialize Service
    tutor_service = TutorService(llm, kb)
    
    yield
    
    # Teardown
    # KB auto-saves on ingest

app = FastAPI(title="AI Study Companion API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(kb_router, prefix="/api/kb", tags=["Knowledge Base"])
app.include_router(tutor_router, prefix="/api/tutor", tags=["Tutor"])

@app.get("/health")
def health_check():
    return {"status": "ok", "kb_size": sum(kb.courses().values()) if kb else 0}
