"""
Pydantic Models Package
======================

Contains all Pydantic models for request validation and response formatting.
"""

# Request models
from app.models.requests import (
    DocumentUploadRequest,
    BulkDocumentUploadRequest,
    DocumentSearchRequest,
    RAGQueryRequest,
    ConfigUpdateRequest,
    ChatMessage,
    ChatRequest,
    URLProcessRequest,
    FileProcessRequest,
    DocumentDeleteRequest,
    DocumentUpdateRequest,
    DocumentFilterRequest,
    DocumentExportRequest,
)

# Response models
from app.models.responses import (
    DocumentResponse,
    BulkDocumentResponse,
    DocumentSearchResponse,
    DocumentSearchResult,
    RAGResponse,
    RAGSource,
    SourceInfo,
    ChatResponse,
    ErrorResponse,
    SuccessResponse,
    HealthResponse,
    DetailedHealthResponse,
    StatusResponse,
    ComponentHealth,
    DocumentStatsResponse,
    ConfigResponse,
    SystemStatusResponse,
    RAGQueryResponse,
    ConfigUpdateResponse,
    EmbeddingModelInfo,
    VectorDatabaseInfo,
    HealthCheckResponse,
    DocumentUploadResponse,
)

# Create backward compatibility aliases
BulkDocumentRequest = BulkDocumentUploadRequest

# Export all models
__all__ = [
    # Request models
    "DocumentUploadRequest",
    "BulkDocumentUploadRequest",
    "BulkDocumentRequest",
    "DocumentSearchRequest", 
    "RAGQueryRequest",
    "ConfigUpdateRequest",
    "ChatMessage",
    "ChatRequest",
    "URLProcessRequest",
    "FileProcessRequest",
    "DocumentDeleteRequest",
    "DocumentUpdateRequest", 
    "DocumentFilterRequest",
    "DocumentExportRequest",
    
    # Response models
    "DocumentResponse",
    "BulkDocumentResponse",
    "DocumentSearchResponse",
    "DocumentSearchResult",
    "RAGResponse",
    "RAGSource",
    "SourceInfo",
    "ChatResponse",
    "ErrorResponse",
    "SuccessResponse",
    "HealthResponse",
    "DetailedHealthResponse",
    "ComponentHealth",
    "StatusResponse",
    "DocumentStatsResponse",
    "ConfigResponse",
    "SystemStatusResponse",
    "RAGQueryResponse",
    "ConfigUpdateResponse",
    "EmbeddingModelInfo",
    "VectorDatabaseInfo",
    "HealthCheckResponse", 
    "DocumentUploadResponse",
]