# This file is intentionally left blank.

"""
API Endpoints Package
====================

Contains all FastAPI router endpoints.

Available routers:
- rag: RAG question answering and configuration
- documents: Document management (upload, search, delete)
- health: System health monitoring and status checks

Each module contains a router that can be included in the main FastAPI app.
"""

from app.api.endpoints import rag, documents, health

# Export routers for easy import
routers = {
    "rag": rag.router,
    "documents": documents.router,
    "health": health.router
}

__all__ = [
    "rag",
    "documents",
    "health",
    "routers"
]