# This file initializes the app package.

"""
PsyWiz Backend Application Package
==================================

A production-ready RAG (Retrieval-Augmented Generation) system for medical research papers.

This package provides:
- FastAPI-based REST API for question answering
- Semantic search through research papers using embeddings
- Integration with Google Gemini for intelligent response generation
- Document upload, processing, and management capabilities
- Health monitoring and system status endpoints

Main Components:
- api/: REST API endpoints and routing
- core/: Business logic (RAG engine, embeddings, vector database)
- models/: Pydantic models for request/response validation
- utils/: Utility functions and helpers

Usage:
    from app.main import app
    # or
    from app.core.rag_engine import RAGEngine
"""

__version__ = "1.0.0"
__author__ = "PsyWiz Team"
__description__ = "RAG system for medical research papers"

# Import key components for easier access
from app.config import settings
from app.main import app

__all__ = [
    "app",
    "settings",
    "__version__",
    "__author__",
    "__description__"
]