"""
Response models for API endpoints.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class DocumentResponse(BaseModel):
    """Response model for document upload."""
    
    success: bool = Field(..., description="Whether the operation was successful")
    document_id: str = Field(..., description="Unique document identifier")
    chunks_created: int = Field(..., description="Number of text chunks created")
    processing_time: float = Field(..., description="Processing time in seconds")
    message: str = Field(..., description="Success message")
    
    model_config = {"protected_namespaces": ()}


class BulkDocumentResponse(BaseModel):
    """Response model for bulk document upload."""
    
    success: bool = Field(..., description="Whether the operation was successful")
    processed: int = Field(..., description="Number of documents processed")
    failed: int = Field(..., description="Number of documents that failed")
    processing_time: float = Field(..., description="Total processing time in seconds")
    results: List[Dict[str, Any]] = Field(..., description="Detailed results for each document")
    errors: List[str] = Field(default_factory=list, description="Error messages")
    
    model_config = {"protected_namespaces": ()}


class DocumentSearchResult(BaseModel):
    """Individual document search result."""
    
    id: str = Field(..., description="Document ID")
    title: str = Field(..., description="Document title")
    source: str = Field(..., description="Document source")
    similarity: float = Field(..., description="Similarity score")
    content_preview: str = Field(..., description="Content preview")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Document metadata")
    
    model_config = {"protected_namespaces": ()}


class DocumentSearchResponse(BaseModel):
    """Response model for document search."""
    
    results: List[DocumentSearchResult] = Field(..., description="Search results")
    total: int = Field(..., description="Total number of results")
    query: str = Field(..., description="Original search query")
    processing_time: float = Field(..., description="Search processing time")
    
    model_config = {"protected_namespaces": ()}


class SourceInfo(BaseModel):
    """Source information for RAG responses."""
    
    id: str = Field(..., description="Source document ID")
    title: str = Field(..., description="Source document title")
    source: str = Field(..., description="Source document filename")
    similarity: float = Field(..., description="Similarity score")
    content: str = Field(..., description="Relevant content snippet")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    model_config = {"protected_namespaces": ()}


class RAGSource(BaseModel):
    """Source citation for RAG response."""
    
    id: str = Field(..., description="Source document ID")
    title: str = Field(..., description="Source document title")
    source: str = Field(..., description="Source document filename")
    similarity: float = Field(..., description="Similarity score")
    content: str = Field(..., description="Relevant content snippet")
    
    model_config = {"protected_namespaces": ()}


class RAGResponse(BaseModel):
    """Response model for RAG question answering."""
    
    answer: str = Field(..., description="Generated answer")
    sources: List[RAGSource] = Field(..., description="Source citations")
    confidence: float = Field(..., description="Answer confidence score")
    query: str = Field(..., description="Original question")
    retrieved_chunks: int = Field(..., description="Number of chunks retrieved")
    processing_time: float = Field(..., description="Processing time in seconds")
    
    model_config = {"protected_namespaces": ()}


class ChatResponse(BaseModel):
    """Response model for chat conversations."""
    
    response: str = Field(..., description="AI response")
    sources: List[RAGSource] = Field(default_factory=list, description="Source citations")
    conversation_id: str = Field(..., description="Conversation identifier")
    message_id: str = Field(..., description="Message identifier")
    processing_time: float = Field(..., description="Processing time in seconds")
    
    model_config = {"protected_namespaces": ()}


class ErrorResponse(BaseModel):
    """Error response model."""
    
    error: str = Field(default="UnknownError", description="Error type")  # FIXED: Added default value
    message: str = Field(..., description="Error message")
    status_code: int = Field(default=500, description="HTTP status code")  # ADDED
    details: Optional[Dict[str, Any]] = Field(default=None, description="Additional error details")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat(), description="Error timestamp")
    path: Optional[str] = Field(default=None, description="Request path")  # ADDED
    method: Optional[str] = Field(default=None, description="HTTP method")  # ADDED
    
    model_config = {"protected_namespaces": ()}


class SuccessResponse(BaseModel):
    """Generic success response model."""
    
    success: bool = Field(default=True, description="Operation success status")
    message: str = Field(..., description="Success message")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Additional details")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat(), description="Response timestamp")
    
    model_config = {"protected_namespaces": ()}


class HealthResponse(BaseModel):
    """Basic health check response."""
    
    status: str = Field(..., description="Health status")
    timestamp: str = Field(..., description="Check timestamp")
    version: str = Field(..., description="Application version")
    
    model_config = {"protected_namespaces": ()}


class ComponentHealth(BaseModel):
    """Individual component health status."""
    
    status: str = Field(..., description="Component status")
    details: Dict[str, Any] = Field(default_factory=dict, description="Component details")
    last_check: str = Field(..., description="Last health check time")
    
    model_config = {"protected_namespaces": ()}


class DetailedHealthResponse(BaseModel):
    """Detailed health check response."""
    
    status: str = Field(..., description="Overall health status")
    timestamp: str = Field(..., description="Check timestamp")
    version: str = Field(..., description="Application version")
    uptime: float = Field(..., description="Application uptime in seconds")
    components: Dict[str, ComponentHealth] = Field(..., description="Component health statuses")
    system_info: Dict[str, Any] = Field(default_factory=dict, description="System information")
    
    model_config = {"protected_namespaces": ()}


class StatusResponse(BaseModel):
    """Generic status response."""
    
    status: str = Field(..., description="Status")
    details: Dict[str, Any] = Field(default_factory=dict, description="Status details")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat(), description="Status timestamp")
    
    model_config = {"protected_namespaces": ()}


class DocumentStatsResponse(BaseModel):
    """Document collection statistics."""
    
    total_documents: int = Field(..., description="Total number of documents")
    total_chunks: int = Field(..., description="Total number of text chunks")
    storage_size: int = Field(..., description="Storage size in bytes")
    last_updated: str = Field(..., description="Last update timestamp")
    document_types: Dict[str, int] = Field(default_factory=dict, description="Document type counts")
    
    model_config = {"protected_namespaces": ()}


class ConfigResponse(BaseModel):
    """Configuration response."""
    
    current_config: Dict[str, Any] = Field(..., description="Current configuration")
    updated_fields: List[str] = Field(default_factory=list, description="Fields that were updated")
    message: str = Field(..., description="Response message")
    
    model_config = {"protected_namespaces": ()}


class SystemStatusResponse(BaseModel):
    """System status response model."""
    
    status: str = Field(..., description="System status")
    components: Dict[str, Any] = Field(..., description="Component statuses")
    performance: Dict[str, Any] = Field(..., description="Performance metrics")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    
    model_config = {"protected_namespaces": ()}


class RAGQueryResponse(BaseModel):
    """RAG query response model."""
    
    answer: str = Field(..., description="Generated answer")
    sources: List[SourceInfo] = Field(..., description="Source information")
    query: str = Field(..., description="Original query")
    confidence: float = Field(..., description="Confidence score")
    processing_time: float = Field(..., description="Processing time")
    
    model_config = {"protected_namespaces": ()}


class ConfigUpdateResponse(BaseModel):
    """Configuration update response."""
    
    success: bool = Field(..., description="Update success")
    message: str = Field(..., description="Update message")
    updated_config: Dict[str, Any] = Field(..., description="Updated configuration")
    
    model_config = {"protected_namespaces": ()}


# MISSING MODELS THAT HEALTH.PY IS TRYING TO IMPORT
class EmbeddingModelInfo(BaseModel):
    """Information about the embedding model."""
    
    model_name: str = Field(..., description="Name of the embedding model")
    is_loaded: bool = Field(..., description="Whether the model is loaded")
    device: str = Field(..., description="Device the model is running on")
    model_size: Optional[str] = Field(default=None, description="Model size information")
    embedding_dimension: Optional[int] = Field(default=None, description="Embedding vector dimension")
    
    model_config = {"protected_namespaces": ()}


class VectorDatabaseInfo(BaseModel):
    """Information about the vector database."""
    
    database_type: str = Field(..., description="Type of vector database")
    collection_name: str = Field(..., description="Collection name")
    document_count: int = Field(..., description="Number of documents in the collection")
    vector_count: int = Field(..., description="Number of vectors in the collection")
    status: str = Field(..., description="Database status")
    
    model_config = {"protected_namespaces": ()}


class HealthCheckResponse(BaseModel):
    """Health check response model."""
    
    status: str = Field(..., description="Overall health status")
    components: Dict[str, Any] = Field(..., description="Component statuses")
    version: str = Field(..., description="Application version")
    uptime: Optional[float] = Field(default=None, description="Application uptime in seconds")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    
    model_config = {"protected_namespaces": ()}


# BACKWARD COMPATIBILITY ALIASES
DocumentUploadResponse = DocumentResponse