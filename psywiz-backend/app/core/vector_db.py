"""
Vector database operations using ChromaDB.
"""

import os
import uuid
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import chromadb
from chromadb.config import Settings as ChromaSettings
from loguru import logger
import numpy as np

from app.config import settings


class VectorDatabase:
    """Vector database interface using ChromaDB."""
    
    def __init__(self, db_path: str = None, collection_name: str = None):
        """Initialize vector database."""
        self.db_path = db_path or settings.vector_db_path
        self.collection_name = collection_name or settings.collection_name
        
        # Ensure database directory exists
        Path(self.db_path).mkdir(parents=True, exist_ok=True)
        
        self.client = None
        self.collection = None
        
        # Initialize ChromaDB client
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize ChromaDB client and collection."""
        try:
            # ChromaDB settings for persistent storage - FIXED telemetry issue
            chroma_settings = ChromaSettings(
                persist_directory=self.db_path,
                anonymized_telemetry=False,  # Disable telemetry to avoid errors
                allow_reset=True,
                is_persistent=True  # Ensure persistence
            )
            
            # Create persistent client
            self.client = chromadb.PersistentClient(
                path=self.db_path,
                settings=chroma_settings
            )
            
            # Get or create collection
            try:
                self.collection = self.client.get_collection(name=self.collection_name)
                document_count = self.collection.count()
                logger.info(f"Loaded existing collection: {self.collection_name} with {document_count} documents")
                
            except Exception:
                # Collection doesn't exist, create it
                self.collection = self.client.create_collection(
                    name=self.collection_name,
                    metadata={"description": "PsyWiz research papers collection"}
                )
                logger.info(f"Created new collection: {self.collection_name}")
                
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {str(e)}")
            raise RuntimeError(f"Database initialization failed: {str(e)}")
    
    def _normalize_embedding(self, embedding) -> List[float]:
        """Normalize embedding to list of floats."""
        if hasattr(embedding, 'tolist'):  # NumPy array
            return embedding.tolist()
        elif hasattr(embedding, 'cpu'):  # PyTorch tensor
            return embedding.cpu().numpy().tolist()
        elif isinstance(embedding, np.ndarray):
            return embedding.tolist()
        elif isinstance(embedding, list):
            return [float(x) for x in embedding]  # Ensure all elements are floats
        else:
            return list(float(x) for x in embedding)
    
    def add_documents(
        self,
        documents: List[str],
        embeddings: List[List[float]],
        metadatas: List[Dict[str, Any]],
        ids: Optional[List[str]] = None
    ) -> bool:
        """Add documents to the vector database."""
        try:
            if not documents or not embeddings or not metadatas:
                raise ValueError("Documents, embeddings, and metadatas cannot be empty")
            
            if len(documents) != len(embeddings) != len(metadatas):
                raise ValueError("Documents, embeddings, and metadatas must have the same length")
            
            # Generate IDs if not provided
            if ids is None:
                ids = [str(uuid.uuid4()) for _ in documents]
            
            # Normalize embeddings
            processed_embeddings = [self._normalize_embedding(emb) for emb in embeddings]
            
            # Add to collection
            self.collection.add(
                documents=documents,
                embeddings=processed_embeddings,
                metadatas=metadatas,
                ids=ids
            )
            
            logger.info(f"Added {len(documents)} documents to collection")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add documents: {str(e)}")
            raise
    
    def similarity_search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        similarity_threshold: float = 0.7,
        metadata_filter: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[str], List[Dict[str, Any]], List[float]]:
        """Search for similar documents."""
        try:
            if not self.collection:
                raise RuntimeError("Collection not initialized")
            
            # Check if collection has any documents
            document_count = self.collection.count()
            if document_count == 0:
                logger.warning("Collection is empty - no documents to search")
                return [], [], []
            
            # Normalize query embedding
            query_embedding = self._normalize_embedding(query_embedding)
            
            logger.debug(f"Searching collection with {document_count} documents")
            logger.debug(f"Query embedding shape: {len(query_embedding)}")
            
            # FIXED: Proper ChromaDB query format
            search_kwargs = {
                "query_embeddings": [query_embedding],  # Must be list of embeddings
                "n_results": min(top_k, document_count),  # Don't request more than available
            }
            
            # Add metadata filter if provided
            if metadata_filter:
                search_kwargs["where"] = metadata_filter
            
            # Perform similarity search
            results = self.collection.query(**search_kwargs)
            
            # FIXED: Better result handling
            if not results or not results.get('documents') or not results['documents'][0]:
                logger.info("No documents found matching the query")
                return [], [], []
            
            # Extract results (ChromaDB returns nested lists)
            documents = results['documents'][0]
            metadatas = results['metadatas'][0] if results.get('metadatas') else [{}] * len(documents)
            distances = results['distances'][0] if results.get('distances') else [0.0] * len(documents)
            
            # Convert distances to similarities (ChromaDB uses cosine distance)
            # For cosine distance: similarity = 1 - distance
            similarities = [max(0.0, 1.0 - distance) for distance in distances]
            
            # Filter by similarity threshold
            filtered_results = []
            for doc, meta, sim in zip(documents, metadatas, similarities):
                if sim >= similarity_threshold:
                    filtered_results.append((doc, meta, sim))
            
            if filtered_results:
                documents, metadatas, similarities = zip(*filtered_results)
                documents = list(documents)
                metadatas = list(metadatas)
                similarities = list(similarities)
                
                logger.info(f"Found {len(documents)} documents above similarity threshold {similarity_threshold}")
            else:
                logger.info(f"No documents found above similarity threshold {similarity_threshold}")
                documents, metadatas, similarities = [], [], []
            
            return documents, metadatas, similarities
            
        except Exception as e:
            logger.error(f"Similarity search failed: {str(e)}")
            logger.error(f"Collection count: {self.collection.count() if self.collection else 'N/A'}")
            raise RuntimeError(f"Search failed: {str(e)}")
    
    def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Get a document by ID."""
        try:
            results = self.collection.get(ids=[document_id])
            
            if results['documents'] and results['documents'][0]:
                return {
                    'id': document_id,
                    'document': results['documents'][0],
                    'metadata': results['metadatas'][0] if results['metadatas'] else {}
                }
            return None
            
        except Exception as e:
            logger.error(f"Failed to get document {document_id}: {str(e)}")
            return None
    
    def delete_document(self, document_id: str) -> bool:
        """Delete a document by ID."""
        try:
            self.collection.delete(ids=[document_id])
            logger.info(f"Deleted document: {document_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete document {document_id}: {str(e)}")
            return False
    
    def update_document(
        self,
        document_id: str,
        document: str = None,
        embedding: List[float] = None,
        metadata: Dict[str, Any] = None
    ) -> bool:
        """Update a document."""
        try:
            update_data = {"ids": [document_id]}
            
            if document is not None:
                update_data["documents"] = [document]
            
            if embedding is not None:
                update_data["embeddings"] = [self._normalize_embedding(embedding)]
            
            if metadata is not None:
                update_data["metadatas"] = [metadata]
            
            self.collection.update(**update_data)
            logger.info(f"Updated document: {document_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update document {document_id}: {str(e)}")
            return False
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get collection statistics."""
        try:
            if not self.collection:
                return {"error": "Collection not initialized"}
            
            count = self.collection.count()
            
            # FIXED: Add more detailed stats
            stats = {
                "collection_name": self.collection_name,
                "document_count": count,
                "database_path": self.db_path,
                "status": "healthy" if count > 0 else "empty"
            }
            
            # Try to get a sample document for additional info
            if count > 0:
                try:
                    sample = self.collection.get(limit=1)
                    if sample and sample.get('metadatas') and sample['metadatas'][0]:
                        stats["sample_metadata_keys"] = list(sample['metadatas'][0].keys())
                except Exception:
                    pass
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get collection stats: {str(e)}")
            return {
                "collection_name": self.collection_name,
                "error": str(e),
                "status": "unhealthy"
            }
    
    def clear_collection(self) -> bool:
        """Clear all documents from the collection."""
        try:
            if self.collection:
                # Get all document IDs
                results = self.collection.get()
                if results['ids']:
                    self.collection.delete(ids=results['ids'])
                logger.info(f"Cleared collection: {self.collection_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to clear collection: {str(e)}")
            return False
    
    def reset_database(self) -> bool:
        """Reset the entire database."""
        try:
            if self.client:
                self.client.reset()
                logger.info("Database reset successfully")
            
            # Reinitialize
            self._initialize_client()
            return True
            
        except Exception as e:
            logger.error(f"Failed to reset database: {str(e)}")
            return False
    
    def __repr__(self):
        return f"VectorDatabase(path='{self.db_path}', collection='{self.collection_name}')"