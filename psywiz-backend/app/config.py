"""
Configuration settings for PsyWiz Backend.
"""

import os
from pathlib import Path
from typing import List, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # API Configuration
    app_name: str = Field(default="PsyWiz Backend", description="Application name")
    app_version: str = Field(default="1.0.0", description="Application version")
    debug: bool = Field(default=False, description="Debug mode")
    host: str = Field(default="127.0.0.1", description="Host to bind to")
    port: int = Field(default=8000, ge=1, le=65535, description="Port to bind to")
    log_level: str = Field(default="INFO", description="Logging level")
    log_file: Optional[str] = Field(default=None, description="Log file path")
    
    # API Keys
    gemini_api_key: Optional[str] = Field(default=None, description="Google Gemini API key")
    openrouter_api_key: Optional[str] = Field(default=None, description="OpenRouter API key")
    
    # Model Configuration
    embedding_model: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2", 
        description="Embedding model name"
    )
    cache_path: str = Field(
        default="./model_cache", 
        description="Model cache directory"
    )
    device: str = Field(default="auto", description="Device for model inference")
    
    # Vector Database Configuration
    vector_db_path: str = Field(default="./vector_db", description="Vector database path")
    collection_name: str = Field(default="psywiz_papers", description="ChromaDB collection name")
    
    # RAG Configuration
    chunk_size: int = Field(default=512, ge=100, le=2000, description="Text chunk size")
    chunk_overlap: int = Field(default=50, ge=0, le=500, description="Chunk overlap size")
    top_k_retrieval: int = Field(default=5, ge=1, le=20, description="Number of chunks to retrieve")
    similarity_threshold: float = Field(default=0.7, ge=0.0, le=1.0, description="Similarity threshold")
    max_context_length: int = Field(default=8000, ge=1000, le=16000, description="Maximum context length")
    
    # CORS Configuration
    allowed_origins: List[str] = Field(
        default=[
            "http://localhost:3000",
            "http://localhost:5173", 
            "http://localhost:8080",
            "http://127.0.0.1:3000"
        ],
        description="Allowed CORS origins"
    )
    
    # Pydantic v2 configuration
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore",
        "protected_namespaces": (),
    }
    
    def __init__(self, **kwargs):
        """Initialize settings with path validation."""
        super().__init__(**kwargs)
        
        # Create directories if they don't exist
        Path(self.cache_path).mkdir(parents=True, exist_ok=True)
        Path(self.vector_db_path).mkdir(parents=True, exist_ok=True)
        
        # Create logs directory
        if self.log_file:
            Path(self.log_file).parent.mkdir(parents=True, exist_ok=True)
        else:
            Path("./logs").mkdir(parents=True, exist_ok=True)
    
    @field_validator('allowed_origins', mode='before')
    @classmethod
    def parse_origins(cls, v):
        """Parse CORS origins from string or list."""
        if isinstance(v, str):
            # Handle JSON string format
            if v.startswith('[') and v.endswith(']'):
                import json
                try:
                    return json.loads(v)
                except json.JSONDecodeError:
                    pass
            # Handle comma-separated string
            return [origin.strip() for origin in v.split(',')]
        return v
    
    @field_validator('log_level')
    @classmethod
    def validate_log_level(cls, v):
        """Validate log level."""
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f'Log level must be one of: {valid_levels}')
        return v.upper()
    
    @field_validator('device')
    @classmethod
    def validate_device(cls, v):
        """Validate device setting."""
        valid_devices = ['auto', 'cpu', 'cuda', 'mps']
        if v.lower() not in valid_devices:
            raise ValueError(f'Device must be one of: {valid_devices}')
        return v.lower()
    
    def validate_required_keys(self):
        """Validate that required API keys are present."""
        if not self.gemini_api_key:
            raise ValueError(
                "GEMINI_API_KEY is required. Get one from: https://makersuite.google.com/app/apikey"
            )
    
    @property
    def model_cache_path(self) -> str:
        """Get model cache path (backward compatibility)."""
        return self.cache_path


# Create global settings instance
settings = Settings()