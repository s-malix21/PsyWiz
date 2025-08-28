"""
Main FastAPI application setup and configuration.
"""

import time
from contextlib import asynccontextmanager
from typing import Dict, Any
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from loguru import logger
import sys

from app.config import settings
from app.api.endpoints import rag, documents, health
from app.core.embeddings import EmbeddingManager
from app.models.responses import ErrorResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Handles startup and shutdown events.
    """
    # Startup
    logger.info("Starting PsyWiz Backend...")
    startup_start = time.time()
    
    try:
        # Configure logging
        logger.remove()  # Remove default handler
        logger.add(
            sys.stdout,
            level=settings.log_level,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
        )
        
        if settings.log_file:
            logger.add(
                settings.log_file,
                level=settings.log_level,
                rotation="10 MB",
                retention="1 week"
            )
        
        logger.info("Logging configured")
        
        # Validate configuration
        settings.validate_required_keys()
        logger.info("Configuration validated")
        
        # Initialize and load embedding model (critical for performance)
        logger.info("Loading embedding model...")
        embedding_manager = EmbeddingManager.get_instance()
        embedding_manager.load_model(settings.embedding_model)
        
        # Warm up the model
        embedding_manager.warm_up()
        
        model_info = embedding_manager.get_model_info()
        logger.info(f"Embedding model loaded: {model_info['model_name']} on {model_info['device']}")
        
        startup_time = time.time() - startup_start
        logger.success(f"PsyWiz Backend started successfully in {startup_time:.2f}s")
        
        yield
        
    except Exception as e:
        logger.error(f"Startup failed: {str(e)}")
        raise
    
    # Shutdown
    logger.info("Shutting down PsyWiz Backend...")
    logger.info("Shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="PsyWiz Backend",
    description="""
    **PsyWiz** - A production-ready RAG (Retrieval-Augmented Generation) system for medical research papers.
    
    ## Features
    
    * **Intelligent Q&A**: Ask questions about medical research and get AI-powered answers
    * **Document Management**: Upload, process, and manage research papers
    * **Semantic Search**: Find relevant papers using advanced embedding techniques
    * **Health Monitoring**: Comprehensive system health and status monitoring
    
    ## Main Endpoints
    
    * **`/rag/ask`** - Ask questions about research papers
    * **`/documents/upload`** - Upload and process documents
    * **`/health/`** - System health monitoring
    
    ## Technology Stack
    
    * **FastAPI** - High-performance API framework
    * **ChromaDB** - Vector database for embeddings
    * **sentence-transformers** - Local embedding model
    * **Google Gemini** - Large Language Model
    """,
    version=settings.app_version,
    contact={
        "name": "PsyWiz Team",
        "email": "contact@psywiz.com",
    },
    license_info={
        "name": "MIT",
    },
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Add trusted host middleware for security
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]  # Configure appropriately for production
)


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests."""
    start_time = time.time()
    
    # Log request
    logger.info(f"Request: {request.method} {request.url}")
    
    # Process request
    response = await call_next(request)
    
    # Log response
    process_time = time.time() - start_time
    logger.info(
        f"Response: {response.status_code} in {process_time:.3f}s"
    )
    
    # Add performance header
    response.headers["X-Process-Time"] = str(process_time)
    
    return response


# Global exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with standardized format."""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            message=exc.detail,
            error_type="HTTPException",
            details={
                "status_code": exc.status_code,
                "url": str(request.url),
                "method": request.method
            }
        ).dict()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions."""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            message="An unexpected error occurred",
            error_type=type(exc).__name__,
            details={
                "url": str(request.url),
                "method": request.method
            }
        ).dict()
    )


# Include routers
app.include_router(
    health.router,
    tags=["Health"]
)

app.include_router(
    rag.router,
    tags=["RAG"]
)

app.include_router(
    documents.router,
    tags=["Documents"]
)


# Root endpoint
@app.get(
    "/",
    summary="API Root",
    description="Get basic API information",
    response_model=Dict[str, Any]
)
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Welcome to PsyWiz Backend API",
        "version": settings.app_version,
        "description": "RAG system for medical research papers",
        "docs": "/docs",
        "health": "/health",
        "status": "running"
    }


# API information endpoint
@app.get(
    "/info",
    summary="API Information",
    description="Get detailed API information and configuration",
    response_model=Dict[str, Any]
)
async def api_info():
    """Get API information and configuration."""
    embedding_manager = EmbeddingManager.get_instance()
    model_info = embedding_manager.get_model_info()
    
    return {
        "api": {
            "name": settings.app_name,
            "version": settings.app_version,
            "debug": settings.debug,
        },
        "configuration": {
            "embedding_model": settings.embedding_model,
            "chunk_size": settings.chunk_size,
            "chunk_overlap": settings.chunk_overlap,
            "top_k_retrieval": settings.top_k_retrieval,
            "similarity_threshold": settings.similarity_threshold,
        },
        "model_status": model_info,
        "endpoints": {
            "health": "/health",
            "rag_ask": "/rag/ask",
            "rag_status": "/rag/status",
            "document_upload": "/documents/upload",
            "document_search": "/documents/search",
            "documentation": "/docs"
        }
    }


if __name__ == "__main__":
    import uvicorn
    
    logger.info("Starting development server...")
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )