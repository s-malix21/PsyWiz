# This file initializes the core package.

"""
Core Business Logic Package
===========================

Contains the core functionality for the RAG system.

Runtime Components (loaded during FastAPI startup):
- embeddings: Singleton embedding model manager
- vector_db: ChromaDB vector database interface
- rag_engine: Main RAG query processing engine

Ingestion Tools (standalone utilities):
- pdf_processor: PDF document processing
- scraper: Web scraping for research papers
- chunking: Text chunking and segmentation

Key Classes:
- EmbeddingManager: Singleton embedding model management
- VectorDatabase: ChromaDB interface for vector storage/retrieval
- RAGEngine: Main RAG pipeline orchestrator
- TextChunker: Intelligent text segmentation
- PDFProcessor: PDF processing utility
- ResearchScraper: Web scraping utility
"""

# Import key classes for easier access
from app.core.embeddings import EmbeddingManager
from app.core.vector_db import VectorDatabase
from app.core.rag_engine import RAGEngine
from app.core.chunking import TextChunker, DocumentChunk
from app.core.pdf_processor import PDFProcessor, ProcessedDocument
from app.core.scraper import ResearchScraper, ScrapedDocument

__all__ = [
    # Runtime components
    "EmbeddingManager",
    "VectorDatabase", 
    "RAGEngine",
    
    # Ingestion tools
    "TextChunker",
    "DocumentChunk",
    "PDFProcessor",
    "ProcessedDocument",
    "ResearchScraper",
    "ScrapedDocument"
]