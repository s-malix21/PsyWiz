"""
RAG endpoint for question answering functionality.
"""

import time
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, status, Depends
from loguru import logger

# FIXED: Import the dependency types properly
from app.dependencies import get_rag_engine, get_settings
from app.models.requests import RAGQueryRequest, ConfigUpdateRequest
from app.models.responses import (
    RAGQueryResponse, 
    SourceInfo, 
    SystemStatusResponse,
    ConfigUpdateResponse,
    ErrorResponse
)

router = APIRouter(prefix="/rag", tags=["RAG"])


@router.post(
    "/ask",
    response_model=RAGQueryResponse,
    summary="Ask a question about research papers",
    description="Submit a question and get an AI-generated answer based on the research paper database"
)
async def ask_question(
    request: RAGQueryRequest,
    rag_engine = Depends(get_rag_engine)
) -> RAGQueryResponse:
    """
    Process a question using the RAG system.
    
    This endpoint:
    1. Encodes the question into embeddings
    2. Retrieves relevant document chunks from the vector database
    3. Generates an answer using the LLM with retrieved context
    4. Returns the answer with source citations
    """
    start_time = time.time()
    
    try:
        logger.info(f"Processing RAG query: {request.question[:50]}...")
        
        # FIXED: Add await keyword since query() is async
        result = await rag_engine.query(
            question=request.question,
            include_sources=request.include_sources,
            top_k=getattr(request, 'top_k', None),
            similarity_threshold=getattr(request, 'similarity_threshold', 0.3),
            max_context_length=getattr(request, 'max_context_length', None),
            temperature=getattr(request, 'temperature', 0.3),
            custom_context=getattr(request, 'custom_context', None)
        )
        
        # Check if query processing failed
        if "error" in result:
            logger.error(f"RAG query failed: {result['error']}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Query processing failed: {result['error']}"
            )
        
        # Convert sources to response format
        sources = []
        if request.include_sources and result.get("sources"):
            sources = [
                SourceInfo(
                    id=source["id"],
                    title=source.get("title", "Unknown"),
                    source=source["source"],
                    similarity=source["similarity"],
                    content=source.get("content", ""),
                    metadata=source.get("metadata", {})
                )
                for source in result["sources"]
            ]
        
        processing_time = time.time() - start_time
        
        response = RAGQueryResponse(
            answer=result["answer"],
            sources=sources,
            confidence=result.get("confidence", 0.0),
            query=request.question,
            processing_time=round(processing_time, 3)
        )
        
        logger.info(f"RAG query completed in {processing_time:.3f}s")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in RAG query: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while processing your question"
        )


@router.get(
    "/status",
    response_model=SystemStatusResponse,
    summary="Get RAG system status",
    description="Get detailed status information about all RAG system components"
)
async def get_rag_status(
    rag_engine = Depends(get_rag_engine)
) -> SystemStatusResponse:
    """
    Get comprehensive status of the RAG system.
    
    Returns information about:
    - Embedding model status
    - Vector database status  
    - LLM availability
    - Current configuration
    """
    try:
        # FIXED: Add await if health_check is async, or use sync call
        health_info = await rag_engine.get_status()
        
        response = SystemStatusResponse(
            status=health_info.get("status", "unknown"),
            components=health_info.get("components", {}),
            performance=health_info.get("performance", {}),
            timestamp=health_info.get("timestamp", "")
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Status check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve system status"
        )


@router.post(
    "/config",
    response_model=ConfigUpdateResponse,
    summary="Update RAG configuration",
    description="Update RAG system parameters like top_k, similarity threshold, etc."
)
async def update_rag_config(
    request: ConfigUpdateRequest,
    rag_engine = Depends(get_rag_engine)
) -> ConfigUpdateResponse:
    """
    Update RAG system configuration.
    
    Allows updating:
    - top_k: Number of documents to retrieve
    - similarity_threshold: Minimum similarity for retrieval
    - max_context_length: Maximum context length for LLM
    """
    try:
        # Get current configuration
        current_health = await rag_engine.get_status()
        old_config = current_health.get("configuration", {})
        
        # Update configuration (if this method exists)
        success = rag_engine.update_config(
            top_k=getattr(request, 'top_k', None),
            similarity_threshold=getattr(request, 'similarity_threshold', None),
            max_context_length=getattr(request, 'max_context_length', None)
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to update configuration"
            )
        
        # Get new configuration
        new_health = await rag_engine.get_status()
        new_config = new_health.get("configuration", {})
        
        response = ConfigUpdateResponse(
            success=True,
            message="Configuration updated successfully",
            updated_config=new_config
        )
        
        logger.info("RAG configuration updated successfully")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Configuration update failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update configuration"
        )


@router.get(
    "/config",
    response_model=Dict[str, Any],
    summary="Get current RAG configuration",
    description="Retrieve the current RAG system configuration parameters"
)
async def get_rag_config(
    rag_engine = Depends(get_rag_engine)
) -> Dict[str, Any]:
    """Get current RAG configuration."""
    try:
        health_info = await rag_engine.get_status()
        config = health_info.get("configuration", {})
        
        return {
            "success": True,
            "configuration": config
        }
        
    except Exception as e:
        logger.error(f"Failed to get configuration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve configuration"
        )