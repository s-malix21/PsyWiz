"""
Global dependencies for dependency injection.
"""

from typing import Annotated
from fastapi import Depends

from app.config import settings


def get_settings():
    """Get application settings."""
    return settings


def get_embedding_manager():
    """Get embedding manager singleton."""
    # Lazy import to avoid startup issues
    from app.core.embeddings import EmbeddingManager
    return EmbeddingManager.get_instance()


def get_vector_db():
    """Get vector database instance."""
    # Lazy import to avoid startup issues
    from app.core.vector_db import VectorDatabase
    return VectorDatabase(
        db_path=settings.vector_db_path,
        collection_name=settings.collection_name
    )


def get_rag_engine():
    """Get RAG engine instance."""
    # Lazy import to avoid startup issues
    from app.core.rag_engine import RAGEngine
    
    embedding_manager = get_embedding_manager()
    vector_db = get_vector_db()
    
    return RAGEngine(
        embedding_manager=embedding_manager,
        vector_db=vector_db,
        settings=settings
    )


# Type annotations for dependency injection (simplified)
SettingsDep = Annotated[type(settings), Depends(get_settings)]

# FIXED: Use proper forward references to avoid import issues
try:
    from app.core.embeddings import EmbeddingManager
    from app.core.vector_db import VectorDatabase  
    from app.core.rag_engine import RAGEngine
    
    EmbeddingManagerDep = Annotated[EmbeddingManager, Depends(get_embedding_manager)]
    VectorDBDep = Annotated[VectorDatabase, Depends(get_vector_db)]
    RAGEngineDep = Annotated[RAGEngine, Depends(get_rag_engine)]
    
except ImportError:
    # Fallback if imports fail during startup
    EmbeddingManagerDep = Annotated[object, Depends(get_embedding_manager)]
    VectorDBDep = Annotated[object, Depends(get_vector_db)]
    RAGEngineDep = Annotated[object, Depends(get_rag_engine)]