"""
Embedding model management with singleton pattern and lazy loading.
"""

import time
from pathlib import Path
from typing import List, Optional, Dict, Any
import torch
from sentence_transformers import SentenceTransformer
from loguru import logger

from app.config import settings


class EmbeddingManager:
    """Singleton embedding manager for sentence transformers."""
    
    _instance = None
    _model = None
    _model_name = None
    _device = None
    _is_loaded = False
    
    def __init__(self):
        """Initialize the embedding manager."""
        if EmbeddingManager._instance is not None:
            raise RuntimeError("EmbeddingManager is a singleton. Use get_instance().")
        
        # Determine device
        if torch.cuda.is_available():
            self._device = "cuda"
        elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            self._device = "mps"  # Apple Silicon
        else:
            self._device = "cpu"
        
        logger.info(f"EmbeddingManager initialized on device: {self._device}")
    
    @classmethod
    def get_instance(cls):
        """Get the singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def is_loaded(self) -> bool:
        """Check if the model is loaded."""
        return self._is_loaded
    
    def load_model(self, model_name: str, device: Optional[str] = None):
        """
        Load the sentence transformer model.
        
        Args:
            model_name: Name/path of the model to load
            device: Device to load model on (optional)
        """
        if self._is_loaded and self._model_name == model_name:
            logger.info(f"Model {model_name} already loaded")
            return
        
        try:
            logger.info(f"Loading embedding model: {model_name}")
            start_time = time.time()
            
            # Use device parameter or fall back to instance device
            device_to_use = device or self._device
            
            # FIXED: Use correct attribute name from settings
            cache_dir = Path(settings.cache_path) / "embeddings"
            cache_dir.mkdir(parents=True, exist_ok=True)
            
            # Load the model
            self._model = SentenceTransformer(
                model_name,
                device=device_to_use,
                cache_folder=str(cache_dir)
            )
            
            self._model_name = model_name
            self._device = device_to_use
            self._is_loaded = True
            
            load_time = time.time() - start_time
            logger.success(f"Embedding model loaded: {model_name} on {self._device} in {load_time:.2f}s")
            
        except Exception as e:
            logger.error(f"Failed to load embedding model {model_name}: {str(e)}")
            raise RuntimeError(f"Could not load embedding model: {str(e)}")
    
    def encode(self, texts: List[str], batch_size: int = 32, show_progress: bool = False) -> List[List[float]]:
        """
        Encode texts into embeddings.
        
        Args:
            texts: List of texts to encode
            batch_size: Batch size for encoding
            show_progress: Whether to show progress bar
            
        Returns:
            List of embeddings
        """
        if not self._is_loaded:
            raise RuntimeError("Model not loaded. Call load_model() first.")
        
        if not texts:
            return []
        
        try:
            start_time = time.time()
            
            embeddings = self._model.encode(
                texts,
                batch_size=batch_size,
                show_progress_bar=show_progress and len(texts) > 5,
                convert_to_numpy=True,
                normalize_embeddings=True  # Normalize for better similarity scores
            )
            
            encode_time = time.time() - start_time
            logger.debug(f"Encoded {len(texts)} texts in {encode_time:.3f}s")
            
            return embeddings.tolist()
            
        except Exception as e:
            logger.error(f"Encoding failed: {str(e)}")
            raise
    
    # In the encode_query method, ensure it returns a list:

    def encode_query(self, query: str) -> List[float]:
        """
        Encode a single query text.
        
        Args:
            query: Query text to encode
            
        Returns:
            Query embedding as a list of floats
        """
        if not query.strip():
            raise ValueError("Query cannot be empty")
        
        # FIXED: Ensure we return a list, not a tensor
        embedding = self.encode([query])[0]
        
        # Convert to list if it's not already
        if hasattr(embedding, 'tolist'):
            return embedding.tolist()
        elif isinstance(embedding, list):
            return embedding
        else:
            return list(embedding)
    
    def encode_documents(self, documents: List[str], batch_size: int = 32) -> List[List[float]]:
        """
        Encode multiple documents with progress tracking.
        
        Args:
            documents: List of document texts
            batch_size: Batch size for processing
            
        Returns:
            List of document embeddings
        """
        return self.encode(
            documents, 
            batch_size=batch_size, 
            show_progress=len(documents) > 10
        )
    
    def warm_up(self):
        """Warm up the model with a test query."""
        if not self._is_loaded:
            logger.warning("Cannot warm up: model not loaded")
            return
        
        try:
            logger.info("Warming up embedding model...")
            test_text = "This is a test sentence for model warm-up."
            self.encode([test_text])
            logger.info("Model warm-up completed")
        except Exception as e:
            logger.warning(f"Model warm-up failed: {str(e)}")
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the loaded model.
        
        Returns:
            Dictionary with model information
        """
        info = {
            "model_name": self._model_name,
            "device": self._device,
            "is_loaded": self._is_loaded,
            "model_max_seq_length": None,
            "embedding_dimension": None
        }
        
        if self._is_loaded and self._model:
            try:
                info["model_max_seq_length"] = self._model.max_seq_length
                info["embedding_dimension"] = self._model.get_sentence_embedding_dimension()
            except Exception as e:
                logger.warning(f"Could not get model info: {str(e)}")
        
        return info
    
    def similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """
        Calculate cosine similarity between two embeddings.
        
        Args:
            embedding1: First embedding
            embedding2: Second embedding
            
        Returns:
            Cosine similarity score
        """
        try:
            import numpy as np
            
            # Convert to numpy arrays
            emb1 = np.array(embedding1)
            emb2 = np.array(embedding2)
            
            # Calculate cosine similarity
            dot_product = np.dot(emb1, emb2)
            norm1 = np.linalg.norm(emb1)
            norm2 = np.linalg.norm(emb2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            return float(dot_product / (norm1 * norm2))
            
        except Exception as e:
            logger.error(f"Similarity calculation failed: {str(e)}")
            return 0.0
    
    def unload_model(self):
        """Unload the model to free memory."""
        if self._is_loaded:
            logger.info("Unloading embedding model")
            self._model = None
            self._is_loaded = False
            self._model_name = None
            
            # Force garbage collection
            import gc
            gc.collect()
            
            # Clear CUDA cache if using GPU
            if self._device == "cuda" and torch.cuda.is_available():
                torch.cuda.empty_cache()
                logger.info("CUDA cache cleared")
    
    def __repr__(self):
        return f"EmbeddingManager(model='{self._model_name}', device='{self._device}', loaded={self._is_loaded})"