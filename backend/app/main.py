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

from app.kb.media_store import MediaStore
from app.kb.graph_store import GraphStore
from app.ingestion.pipeline import IngestionPipeline

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global instances
kb: KnowledgeBase = None
tutor_service: TutorService = None
media_store: MediaStore = None
graph_store: GraphStore = None
ingestion_pipeline: IngestionPipeline = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global kb, tutor_service, media_store, graph_store, ingestion_pipeline
    settings = get_settings()
    
    # Initialize providers
    llm = build_llm_provider(settings)
    embedder = build_embedding_provider(settings)
    
    # Initialize KB & Stores
    vector_store = InMemoryVectorStore()
    persist_dir = settings.data_dir if settings.persist else None
    
    kb = KnowledgeBase(store=vector_store, embedder=embedder, persist_dir=persist_dir)
    logger.info(f"Loaded Knowledge Base with {sum(kb.courses().values())} chunks.")
    
    media_dir = settings.data_dir / "figures"
    graph_dir = settings.data_dir / "graphs" if settings.persist else None
    media_store = MediaStore(base_dir=media_dir)
    graph_store = GraphStore(persist_dir=graph_dir)
    
    api_key = settings.gemini_api_key.get_secret_value() if settings.gemini_api_key else None
    ingestion_pipeline = IngestionPipeline(
        kb=kb,
        media_store=media_store,
        graph_store=graph_store,
        api_key=api_key,
    )
    
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
