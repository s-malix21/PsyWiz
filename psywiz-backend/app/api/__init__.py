# This file initializes the api package.
"""
API Package
===========

Contains all FastAPI endpoints and API-related functionality.

Modules:
- endpoints/: Individual endpoint modules (rag, documents, health)
- deps.py: API-specific dependencies

The API provides:
- /rag/ask: Question answering endpoint
- /rag/status: RAG system status
- /rag/config: Configuration management
- /documents/upload: Document upload and processing
- /documents/search: Document search functionality
- /health/: System health monitoring endpoints
"""

from app.api.endpoints import rag, documents, health

__all__ = [
    "rag",
    "documents", 
    "health"
]