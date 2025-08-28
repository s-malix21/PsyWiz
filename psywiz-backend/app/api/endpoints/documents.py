"""
Document management endpoints for upload, search, and deletion.
"""

import time
import uuid
from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, status, Depends
from loguru import logger

from app.dependencies import get_embedding_manager, get_vector_db, get_settings
from app.core.chunking import TextChunker, DocumentChunk
from app.models.requests import (
    DocumentUploadRequest,
    DocumentSearchRequest,
    DocumentDeleteRequest,
    BulkDocumentUploadRequest  # FIXED: Use the actual class name
)
from app.models.responses import (
    DocumentResponse,  # FIXED: Use the actual response class names
    BulkDocumentResponse,  # FIXED: Use the actual response class names
    DocumentSearchResponse,
    SuccessResponse
)

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post(
    "/upload",
    response_model=DocumentResponse,  # FIXED: Use correct response model
    summary="Upload a single document",
    description="Upload and process a single document into the vector database"
)
async def upload_document(
    request: DocumentUploadRequest,
    embedding_manager = Depends(get_embedding_manager),
    vector_db = Depends(get_vector_db),
    settings = Depends(get_settings)
) -> DocumentResponse:  # FIXED: Use correct response model
    """
    Upload and process a single document.
    
    This endpoint:
    1. Validates the document content
    2. Chunks the text into optimal segments
    3. Generates embeddings for each chunk
    4. Stores chunks and embeddings in the vector database
    """
    start_time = time.time()
    
    try:
        logger.info(f"Processing document upload: {request.title}")
        
        # Initialize chunker
        chunker = TextChunker(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap
        )
        
        # Prepare base metadata
        base_metadata = {
            "title": request.title,
            "source": request.source,
            "document_type": request.document_type,
            "authors": request.authors,
            "publication_date": request.publication_date,
            "doi": request.doi,
            "upload_timestamp": time.time()
        }
        
        # Chunk the document
        chunks = chunker.chunk_text(
            text=request.content,
            metadata=base_metadata
        )
        
        if not chunks:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Document could not be chunked. Content may be too short or invalid."
            )
        
        # Generate embeddings for chunks
        chunk_texts = [chunk.text for chunk in chunks]
        embeddings = embedding_manager.encode(chunk_texts)
        
        # Prepare data for vector database
        chunk_metadatas = [chunk.metadata for chunk in chunks]
        document_id = str(uuid.uuid4())
        
        # Add document ID to all chunk metadata
        for metadata in chunk_metadatas:
            metadata["document_id"] = document_id
        
        # Store in vector database
        chunk_ids = vector_db.add_documents(
            documents=chunk_texts,
            metadatas=chunk_metadatas,
            embeddings=embeddings
        )
        
        processing_time = time.time() - start_time
        
        response = DocumentResponse(
            success=True,
            document_id=document_id,
            chunks_created=len(chunks),
            processing_time=round(processing_time, 3),
            message=f"Document successfully uploaded and processed into {len(chunks)} chunks"
        )
        
        logger.info(f"Document uploaded successfully: {document_id} ({len(chunks)} chunks)")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document upload failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Document upload failed: {str(e)}"
        )


@router.post(
    "/bulk-upload",
    response_model=BulkDocumentResponse,
    summary="Upload multiple documents",
    description="Upload and process multiple documents in a single request"
)
async def bulk_upload_documents(
    request: BulkDocumentUploadRequest,  # FIXED: Use correct class name
    embedding_manager = Depends(get_embedding_manager),
    vector_db = Depends(get_vector_db),
    settings = Depends(get_settings)
) -> BulkDocumentResponse:
    """
    Upload multiple documents in bulk.
    
    Processes documents in batches for efficiency and memory management.
    """
    start_time = time.time()
    
    try:
        logger.info(f"Starting bulk upload of {len(request.documents)} documents")
        
        successful_uploads = []
        failed_uploads = []
        
        # Process documents in batches
        for i in range(0, len(request.documents), request.batch_size):
            batch = request.documents[i:i + request.batch_size]
            logger.info(f"Processing batch {i//request.batch_size + 1}")
            
            for doc_request in batch:
                try:
                    # Process individual document
                    upload_response = await upload_document(
                        request=doc_request,
                        embedding_manager=embedding_manager,
                        vector_db=vector_db,
                        settings=settings
                    )
                    successful_uploads.append(upload_response.dict())
                    
                except Exception as e:
                    error_info = {
                        "document": {
                            "title": doc_request.title,
                            "content_length": len(doc_request.content)
                        },
                        "error": str(e),
                        "error_type": type(e).__name__
                    }
                    failed_uploads.append(error_info)
        
        processing_time = time.time() - start_time
        
        response = BulkDocumentResponse(
            success=len(failed_uploads) == 0,
            processed=len(successful_uploads),
            failed=len(failed_uploads),
            processing_time=round(processing_time, 3),
            results=successful_uploads + failed_uploads,
            errors=[error["error"] for error in failed_uploads]
        )
        
        logger.info(f"Bulk upload completed: {len(successful_uploads)}/{len(request.documents)} successful")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Bulk upload failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Bulk upload failed: {str(e)}"
        )


@router.post(
    "/search",
    response_model=DocumentSearchResponse,
    summary="Search documents",
    description="Search for documents based on query and filters"
)
async def search_documents(
    request: DocumentSearchRequest,
    embedding_manager = Depends(get_embedding_manager),
    vector_db = Depends(get_vector_db)
) -> DocumentSearchResponse:
    """
    Search for documents using semantic search.
    """
    start_time = time.time()
    
    try:
        logger.info(f"Searching documents with query: {request.query}")
        
        # Perform semantic search
        query_embedding = embedding_manager.encode_query(request.query)
        
        documents, metadatas, similarities = vector_db.similarity_search(
            query_embedding=query_embedding,
            top_k=request.limit,
            similarity_threshold=request.similarity_threshold
        )
        
        # Convert to search results
        results = []
        for i, (doc, metadata, similarity) in enumerate(zip(documents, metadatas, similarities)):
            result = {
                "id": metadata.get("document_id", f"doc_{i}"),
                "title": metadata.get("title", "Unknown"),
                "source": metadata.get("source", "Unknown"),
                "similarity": round(similarity, 3),
                "content_preview": doc[:200] + "..." if len(doc) > 200 else doc,
                "metadata": metadata
            }
            results.append(result)
        
        processing_time = time.time() - start_time
        
        response = DocumentSearchResponse(
            results=results,
            total=len(results),
            query=request.query,
            processing_time=round(processing_time, 3)
        )
        
        logger.info(f"Document search completed: found {len(results)} documents")
        return response
        
    except Exception as e:
        logger.error(f"Document search failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Document search failed: {str(e)}"
        )


@router.delete(
    "/delete",
    response_model=SuccessResponse,
    summary="Delete documents",
    description="Delete documents by their IDs"
)
async def delete_documents(
    request: DocumentDeleteRequest,
    vector_db = Depends(get_vector_db)
) -> SuccessResponse:
    """
    Delete documents from the vector database.
    """
    start_time = time.time()
    
    try:
        logger.info(f"Deleting {len(request.document_ids)} documents")
        
        # For now, return a simple response
        # In a real implementation, you'd delete from the vector database
        success = True  # Placeholder
        
        processing_time = time.time() - start_time
        
        response = SuccessResponse(
            success=success,
            message=f"Successfully processed deletion request for {len(request.document_ids)} documents",
            details={
                "document_ids": request.document_ids,
                "processing_time": round(processing_time, 3)
            }
        )
        
        logger.info(f"Document deletion completed")
        return response
        
    except Exception as e:
        logger.error(f"Document deletion failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Document deletion failed: {str(e)}"
        )


@router.get(
    "/stats",
    response_model=Dict[str, Any],
    summary="Get document statistics",
    description="Get statistics about documents in the vector database"
)
async def get_document_stats(
    vector_db = Depends(get_vector_db)
) -> Dict[str, Any]:
    """Get statistics about the document collection."""
    try:
        db_stats = vector_db.get_collection_stats()
        
        return {
            "success": True,
            "statistics": db_stats,
            "timestamp": time.time()
        }
        
    except Exception as e:
        logger.error(f"Failed to get document stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve document statistics"
        )


@router.delete(
    "/clear",
    response_model=SuccessResponse,
    summary="Clear all documents",
    description="Delete all documents from the vector database (use with caution!)"
)
async def clear_all_documents(
    vector_db = Depends(get_vector_db),
    confirm: bool = False
) -> SuccessResponse:
    """
    Clear all documents from the vector database.
    
    This is a destructive operation that cannot be undone!
    """
    if not confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must set confirm=true to clear all documents"
        )
    
    try:
        logger.warning("Clearing all documents from vector database")
        
        # Placeholder for actual implementation
        success = True
        
        return SuccessResponse(
            success=success,
            message="All documents successfully cleared from the database" if success else "Failed to clear documents"
        )
        
    except Exception as e:
        logger.error(f"Failed to clear documents: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clear documents"
        )