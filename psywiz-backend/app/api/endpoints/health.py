"""
Health check endpoints for system monitoring.
"""

import time
import os
import psutil
from datetime import datetime
from typing import Dict, Any
from fastapi import APIRouter, Depends
from loguru import logger

from app.dependencies import get_settings, get_embedding_manager, get_vector_db, get_rag_engine
from app.models.responses import (
    HealthCheckResponse,
    # EmbeddingModelInfo,  # REMOVED - These models now exist in responses.py
    # VectorDatabaseInfo   # REMOVED - These models now exist in responses.py
)

router = APIRouter(prefix="/health", tags=["Health"])

# Track startup time for uptime calculation
startup_time = time.time()


@router.get(
    "/",
    response_model=HealthCheckResponse,
    summary="Basic health check",
    description="Basic health check to verify API is responsive"
)
async def health_check() -> HealthCheckResponse:
    """
    Basic health check endpoint.
    
    Returns minimal health information to verify the API is responsive.
    """
    try:
        uptime = time.time() - startup_time
        
        return HealthCheckResponse(
            status="healthy",
            components={
                "api": "healthy",
                "uptime_seconds": round(uptime, 2)
            },
            version="1.0.0",
            uptime=uptime
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return HealthCheckResponse(
            status="unhealthy",
            components={
                "api": "unhealthy",
                "error": str(e)
            },
            version="1.0.0"
        )


@router.get(
    "/detailed",
    response_model=Dict[str, Any],
    summary="Detailed health check",
    description="Comprehensive health check including all system components"
)
async def detailed_health_check(
    settings = Depends(get_settings),
    embedding_manager = Depends(get_embedding_manager),
    vector_db = Depends(get_vector_db),
    rag_engine = Depends(get_rag_engine)
) -> Dict[str, Any]:
    """
    Detailed health check with component-specific information.
    
    Checks:
    - API status
    - Embedding model status
    - Vector database status
    - RAG engine status
    - System resources
    """
    health_info = {
        "timestamp": datetime.utcnow().isoformat(),
        "status": "unknown",
        "version": "1.0.0",
        "uptime_seconds": round(time.time() - startup_time, 2),
        "components": {}
    }
    
    try:
        # Check API status
        health_info["components"]["api"] = {
            "status": "healthy",
            "description": "FastAPI server is running"
        }
        
        # Check embedding model
        try:
            model_info = embedding_manager.get_model_info()
            health_info["components"]["embedding_model"] = {
                "status": "healthy" if model_info.get("is_loaded", False) else "degraded",
                "info": model_info
            }
        except Exception as e:
            health_info["components"]["embedding_model"] = {
                "status": "unhealthy",
                "error": str(e)
            }
        
        # Check vector database
        try:
            db_health = vector_db.health_check() if hasattr(vector_db, 'health_check') else {"status": "unknown"}
            health_info["components"]["vector_database"] = {
                "status": db_health.get("status", "unknown"),
                "info": db_health
            }
        except Exception as e:
            health_info["components"]["vector_database"] = {
                "status": "unhealthy",
                "error": str(e)
            }
        
        # Check RAG engine
        try:
            rag_health = rag_engine.health_check() if hasattr(rag_engine, 'health_check') else {"status": "unknown"}
            health_info["components"]["rag_engine"] = {
                "status": rag_health.get("status", "unknown"),
                "info": rag_health
            }
        except Exception as e:
            health_info["components"]["rag_engine"] = {
                "status": "unhealthy",
                "error": str(e)
            }
        
        # Check system resources
        try:
            health_info["components"]["system"] = _get_system_info()
        except Exception as e:
            health_info["components"]["system"] = {
                "status": "error",
                "error": str(e)
            }
        
        # Determine overall status
        component_statuses = [
            comp.get("status", "unknown") 
            for comp in health_info["components"].values()
        ]
        
        if all(status == "healthy" for status in component_statuses):
            health_info["status"] = "healthy"
        elif any(status == "unhealthy" for status in component_statuses):
            health_info["status"] = "unhealthy"
        else:
            health_info["status"] = "degraded"
        
        return health_info
        
    except Exception as e:
        logger.error(f"Detailed health check failed: {str(e)}")
        health_info["status"] = "unhealthy"
        health_info["error"] = str(e)
        return health_info


@router.get(
    "/embedding",
    response_model=Dict[str, Any],
    summary="Embedding model health",
    description="Check the status of the embedding model"
)
async def embedding_health(
    embedding_manager = Depends(get_embedding_manager)
) -> Dict[str, Any]:
    """Check embedding model health and perform a test inference."""
    try:
        # Get model info
        model_info = embedding_manager.get_model_info()
        
        # Perform test inference if model is loaded
        test_result = None
        if model_info.get("is_loaded", False):
            try:
                start_time = time.time()
                test_embeddings = embedding_manager.encode(["Health check test text"])
                inference_time = time.time() - start_time
                
                test_result = {
                    "test_passed": True,
                    "inference_time_ms": round(inference_time * 1000, 2),
                    "embedding_dimension": len(test_embeddings[0]) if test_embeddings else None
                }
            except Exception as e:
                test_result = {
                    "test_passed": False,
                    "error": str(e)
                }
        
        return {
            "status": "healthy" if model_info.get("is_loaded", False) else "not_loaded",
            "model_info": model_info,
            "test_result": test_result,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Embedding health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


@router.get(
    "/database",
    response_model=Dict[str, Any],
    summary="Vector database health",
    description="Check the status of the vector database"
)
async def database_health(
    vector_db = Depends(get_vector_db)
) -> Dict[str, Any]:
    """Check vector database health and perform test operations."""
    try:
        # Get database stats
        db_stats = vector_db.get_collection_stats() if hasattr(vector_db, 'get_collection_stats') else {}
        
        # Perform health check
        health_result = vector_db.health_check() if hasattr(vector_db, 'health_check') else {"status": "unknown"}
        
        return {
            "status": health_result.get("status", "unknown"),
            "database_stats": db_stats,
            "health_check": health_result,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


def _get_system_info() -> Dict[str, Any]:
    """Get system resource information."""
    try:
        # Get CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # Get memory usage
        memory = psutil.virtual_memory()
        
        # Get disk usage
        disk = psutil.disk_usage('/')
        
        # Get process info
        process = psutil.Process()
        process_memory = process.memory_info()
        
        return {
            "status": "healthy",
            "cpu": {
                "usage_percent": cpu_percent,
                "count": psutil.cpu_count()
            },
            "memory": {
                "total_gb": round(memory.total / (1024**3), 2),
                "available_gb": round(memory.available / (1024**3), 2),
                "usage_percent": memory.percent
            },
            "disk": {
                "total_gb": round(disk.total / (1024**3), 2),
                "free_gb": round(disk.free / (1024**3), 2),
                "usage_percent": round((disk.used / disk.total) * 100, 2)
            },
            "process": {
                "memory_mb": round(process_memory.rss / (1024**2), 2),
                "cpu_percent": process.cpu_percent()
            }
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


@router.get(
    "/ready",
    response_model=Dict[str, Any],
    summary="Readiness check",
    description="Check if the system is ready to serve requests"
)
async def readiness_check(
    rag_engine = Depends(get_rag_engine)
) -> Dict[str, Any]:
    """
    Readiness check for container orchestration.
    
    Returns whether the system is ready to handle RAG queries.
    """
    try:
        # Perform a quick RAG system check
        health_info = await rag_engine.get_status() if hasattr(rag_engine, 'get_status') else {"status": "unknown"}
        
        is_ready = (
            health_info.get("status") in ["healthy", "degraded"] and
            health_info.get("embedding_model", {}).get("is_loaded", False)
        )
        
        return {
            "ready": is_ready,
            "status": "ready" if is_ready else "not_ready",
            "checks": {
                "rag_system": health_info.get("status"),
                "embedding_model": health_info.get("embedding_model", {}).get("is_loaded", False)
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Readiness check failed: {str(e)}")
        return {
            "ready": False,
            "status": "not_ready",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }