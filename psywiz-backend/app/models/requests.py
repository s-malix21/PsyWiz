"""
Request models for API endpoints.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator


class DocumentUploadRequest(BaseModel):
    """Request model for document upload."""
    
    title: str = Field(..., description="Document title", min_length=1, max_length=500)
    content: str = Field(..., description="Document content", min_length=10)
    source: str = Field(..., description="Document source/filename", min_length=1, max_length=255)
    document_type: str = Field(default="research_paper", description="Type of document")
    authors: Optional[List[str]] = Field(default=None, description="List of authors")
    publication_date: Optional[str] = Field(default=None, description="Publication date")
    keywords: Optional[List[str]] = Field(default=None, description="Document keywords")
    abstract: Optional[str] = Field(default=None, description="Document abstract")
    doi: Optional[str] = Field(default=None, description="DOI identifier")
    
    model_config = {
        "protected_namespaces": (),
        "json_schema_extra": {
            "example": {
                "title": "Deep Learning in Medical Diagnosis",
                "content": "This paper explores the application of deep learning...",
                "source": "medical_journal_2024.pdf",
                "document_type": "research_paper",
                "authors": ["Dr. Jane Smith", "Dr. John Doe"],
                "publication_date": "2024-01-15",
                "keywords": ["deep learning", "medical diagnosis", "AI"],
                "abstract": "Abstract of the research paper...",
                "doi": "10.1000/xyz123"
            }
        }
    }


class BulkDocumentUploadRequest(BaseModel):
    """Request model for bulk document upload."""
    
    documents: List[DocumentUploadRequest] = Field(..., description="List of documents to upload")
    batch_size: int = Field(default=5, ge=1, le=20, description="Batch processing size")
    
    model_config = {"protected_namespaces": ()}


class DocumentSearchRequest(BaseModel):
    """Request model for document search."""
    
    query: str = Field(..., description="Search query", min_length=1, max_length=500)
    limit: int = Field(default=10, ge=1, le=50, description="Maximum number of results")
    similarity_threshold: float = Field(default=0.7, ge=0.0, le=1.0, description="Minimum similarity score")
    document_type: Optional[str] = Field(default=None, description="Filter by document type")
    
    model_config = {"protected_namespaces": ()}


class RAGQueryRequest(BaseModel):
    """Request model for RAG question answering."""
    
    question: str = Field(..., description="Question to ask", min_length=1, max_length=1000)
    include_sources: bool = Field(default=True, description="Include source citations")
    top_k: int = Field(default=5, ge=1, le=20, description="Number of relevant chunks to retrieve")
    similarity_threshold: float = Field(default=0.7, ge=0.0, le=1.0, description="Minimum similarity for retrieval")
    max_context_length: int = Field(default=8000, ge=1000, le=16000, description="Maximum context length for LLM")
    llm_model: str = Field(default="gemini", description="LLM model to use for generation")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Generation temperature")
    
    model_config = {
        "protected_namespaces": (),
        "json_schema_extra": {
            "example": {
                "question": "What are the main findings about diabetes treatment?",
                "include_sources": True,
                "top_k": 5,
                "similarity_threshold": 0.3,
                "llm_model": "gemini",
                "temperature": 0.3
            }
        }
    }


class ChatMessage(BaseModel):
    """Chat message model."""
    
    role: str = Field(..., description="Message role: user, assistant, system")
    content: str = Field(..., description="Message content")
    timestamp: Optional[str] = Field(default=None, description="Message timestamp")
    
    model_config = {"protected_namespaces": ()}


class ChatRequest(BaseModel):
    """Request model for chat conversations."""
    
    messages: List[ChatMessage] = Field(..., description="Chat conversation history")
    include_context: bool = Field(default=True, description="Include document context")
    max_tokens: int = Field(default=1000, ge=100, le=4000, description="Maximum response tokens")
    
    model_config = {"protected_namespaces": ()}


class ConfigUpdateRequest(BaseModel):
    """Request model for updating system configuration."""
    
    embedding_model: Optional[str] = Field(default=None, description="Embedding model name")
    chunk_size: Optional[int] = Field(default=None, ge=100, le=2000, description="Text chunk size")
    chunk_overlap: Optional[int] = Field(default=None, ge=0, le=500, description="Chunk overlap size")
    top_k_retrieval: Optional[int] = Field(default=None, ge=1, le=20, description="Number of chunks to retrieve")
    similarity_threshold: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Similarity threshold")
    temperature: Optional[float] = Field(default=None, ge=0.0, le=2.0, description="LLM temperature")
    max_context_length: Optional[int] = Field(default=None, ge=1000, le=16000, description="Maximum context length")
    
    model_config = {
        "protected_namespaces": (),
        "json_schema_extra": {
            "example": {
                "chunk_size": 512,
                "chunk_overlap": 50,
                "top_k_retrieval": 5,
                "similarity_threshold": 0.3,
                "temperature": 0.3
            }
        }
    }


class URLProcessRequest(BaseModel):
    """Request model for processing URLs."""
    
    url: str = Field(..., description="URL to process")
    title: Optional[str] = Field(default=None, description="Document title (auto-extracted if not provided)")
    document_type: str = Field(default="web_page", description="Type of document")
    extract_links: bool = Field(default=False, description="Extract and process internal links")
    max_depth: int = Field(default=1, ge=1, le=3, description="Maximum crawling depth")
    
    model_config = {"protected_namespaces": ()}


class FileProcessRequest(BaseModel):
    """Request model for processing uploaded files."""
    
    filename: str = Field(..., description="Name of the uploaded file")
    content_type: str = Field(..., description="MIME type of the file")
    title: Optional[str] = Field(default=None, description="Document title")
    authors: Optional[List[str]] = Field(default=None, description="Document authors")
    
    model_config = {"protected_namespaces": ()}


# MISSING MODELS - Adding them now
class DocumentDeleteRequest(BaseModel):
    """Request model for document deletion."""
    
    document_ids: List[str] = Field(..., description="List of document IDs to delete")
    confirm_deletion: bool = Field(default=False, description="Confirmation flag for deletion")
    
    model_config = {
        "protected_namespaces": (),
        "json_schema_extra": {
            "example": {
                "document_ids": ["doc_123", "doc_456"],
                "confirm_deletion": True
            }
        }
    }


class DocumentUpdateRequest(BaseModel):
    """Request model for document updates."""
    
    document_id: str = Field(..., description="Document ID to update")
    title: Optional[str] = Field(default=None, description="New document title")
    authors: Optional[List[str]] = Field(default=None, description="Updated authors list")
    keywords: Optional[List[str]] = Field(default=None, description="Updated keywords")
    abstract: Optional[str] = Field(default=None, description="Updated abstract")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata to update")
    
    model_config = {"protected_namespaces": ()}


class DocumentFilterRequest(BaseModel):
    """Request model for filtering documents."""
    
    document_type: Optional[str] = Field(default=None, description="Filter by document type")
    authors: Optional[List[str]] = Field(default=None, description="Filter by authors")
    date_from: Optional[str] = Field(default=None, description="Filter from date (YYYY-MM-DD)")
    date_to: Optional[str] = Field(default=None, description="Filter to date (YYYY-MM-DD)")
    keywords: Optional[List[str]] = Field(default=None, description="Filter by keywords")
    limit: int = Field(default=50, ge=1, le=100, description="Maximum results")
    offset: int = Field(default=0, ge=0, description="Pagination offset")
    
    model_config = {"protected_namespaces": ()}


class DocumentExportRequest(BaseModel):
    """Request model for document export."""
    
    document_ids: Optional[List[str]] = Field(default=None, description="Specific document IDs to export")
    export_format: str = Field(default="json", description="Export format: json, csv, txt")
    include_content: bool = Field(default=True, description="Include full document content")
    include_metadata: bool = Field(default=True, description="Include document metadata")
    
    model_config = {
        "protected_namespaces": (),
        "json_schema_extra": {
            "example": {
                "document_ids": ["doc_123", "doc_456"],
                "export_format": "json",
                "include_content": True,
                "include_metadata": True
            }
        }
    }

    @field_validator('export_format')
    @classmethod
    def validate_export_format(cls, v):
        """Validate export format."""
        valid_formats = ['json', 'csv', 'txt', 'pdf']
        if v.lower() not in valid_formats:
            raise ValueError(f'Export format must be one of: {valid_formats}')
        return v.lower()