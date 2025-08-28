"""
RAG Engine - RUNTIME COMPONENT
This is the core RAG system that runs during FastAPI runtime.
Enhanced to work with rich metadata from improved chunking.
"""

import re
import time
from typing import List, Dict, Any, Optional, Tuple
import google.generativeai as genai
from loguru import logger

from app.core.embeddings import EmbeddingManager
from app.core.vector_db import VectorDatabase


class RAGEngine:
    """
    Retrieval-Augmented Generation engine for question answering.
    Enhanced to work with rich metadata.
    """
    
    def __init__(
        self,
        embedding_manager: EmbeddingManager,
        vector_db: VectorDatabase,
        settings,  # FIXED: Accept settings instead of individual parameters
        api_key: Optional[str] = None
    ):
        """
        Initialize RAG engine.
        
        Args:
            embedding_manager: Singleton embedding manager
            vector_db: Vector database instance
            settings: Application settings
            api_key: Gemini API key (optional, uses settings if not provided)
        """
        self.embedding_manager = embedding_manager
        self.vector_db = vector_db
        self.settings = settings
        
        # Use configuration from settings
        self.top_k = settings.top_k_retrieval
        self.similarity_threshold = settings.similarity_threshold
        self.max_context_length = settings.max_context_length
        
        # Initialize Gemini
        api_key = api_key or settings.gemini_api_key
        if not api_key:
            raise ValueError("Gemini API key is required. Set GEMINI_API_KEY in .env file")
        
        self._initialize_llm(api_key)
        
        # Ensure embedding model is loaded
        if not self.embedding_manager.is_loaded():
            self.embedding_manager.load_model()
        
        logger.info("RAGEngine initialized and ready for queries")
    
    def _initialize_llm(self, api_key: str) -> None:
        """Initialize Google Gemini LLM."""
        try:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-2.0-flash')
            
            # Test the model with a simple query
            test_response = self.model.generate_content("Hello")
            logger.info("Gemini model initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Gemini: {str(e)}")
            raise RuntimeError(f"LLM initialization failed: {str(e)}")
    
    async def query(
        self,
        question: str,
        include_sources: bool = True,
        top_k: Optional[int] = None,
        similarity_threshold: Optional[float] = None,
        max_context_length: Optional[int] = None,
        temperature: float = 0.7,
        custom_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a question using RAG pipeline.
        
        Args:
            question: User question
            include_sources: Whether to include source citations
            top_k: Override default top_k
            similarity_threshold: Override default threshold
            max_context_length: Override default max context
            temperature: LLM temperature
            custom_context: Optional custom context to include
            
        Returns:
            Dictionary with answer, sources, and metadata
        """
        try:
            start_time = time.time()
            
            logger.info(f"Processing query: {question[:50]}...")
            
            # Use provided parameters or defaults
            _top_k = top_k or self.top_k
            _threshold = similarity_threshold or self.similarity_threshold
            _max_context = max_context_length or self.max_context_length
            
            # Step 1: Encode query
            query_embedding = self.embedding_manager.encode_query(question)
            
            # Step 2: Retrieve relevant documents
            retrieved_docs, metadatas, similarities = self.vector_db.similarity_search(
                query_embedding=query_embedding,
                top_k=_top_k,
                similarity_threshold= 0.3  #_threshold SIMILARITY THRESHOLD SET HERE
            )
            
            if not retrieved_docs:
                return {
                    "answer": "I couldn't find relevant information to answer your question. Please try rephrasing or asking about a different topic.",
                    "sources": [],
                    "confidence": 0.0,
                    "retrieved_chunks": 0,
                    "query": question,
                    "processing_time": time.time() - start_time
                }
            
            # Step 3: Build enhanced context with rich metadata
            context = self._build_enhanced_context(retrieved_docs, metadatas, custom_context, _max_context)
            
            # Step 4: Generate answer
            answer = self._generate_answer(question, context, temperature)
            
            # Step 5: Extract enhanced sources if requested
            sources = []
            if include_sources:
                sources = self._extract_enhanced_sources(retrieved_docs, metadatas, similarities)
            
            # Calculate confidence based on similarity scores
            confidence = sum(similarities) / len(similarities) if similarities else 0.0
            
            processing_time = time.time() - start_time
            
            result = {
                "answer": answer,
                "sources": sources,
                "confidence": round(confidence, 3),
                "retrieved_chunks": len(retrieved_docs),
                "query": question,
                "processing_time": round(processing_time, 2)
            }
            
            logger.info(f"Query processed successfully in {processing_time:.2f}s. Retrieved {len(retrieved_docs)} chunks")
            return result
            
        except Exception as e:
            logger.error(f"Query processing failed: {str(e)}")
            return {
                "answer": "I encountered an error while processing your question. Please try again.",
                "sources": [],
                "confidence": 0.0,
                "retrieved_chunks": 0,
                "query": question,
                "processing_time": 0.0,
                "error": str(e)
            }
    
    def _build_enhanced_context(
        self,
        documents: List[str],
        metadatas: List[Dict[str, Any]],
        custom_context: Optional[str] = None,
        max_length: int = 8000
    ) -> str:
        """Build enhanced context string with rich metadata from retrieved documents."""
        context_parts = []
        current_length = 0
        
        # Add custom context if provided
        if custom_context:
            context_parts.append(f"Additional Context:\n{custom_context}\n\n")
            current_length += len(custom_context)
        
        context_parts.append("Relevant Research Information:\n\n")
        
        for i, (doc, metadata) in enumerate(zip(documents, metadatas)):
            # ENHANCED: Create detailed source identifier with rich metadata
            source_id = f"[Source {i+1}]"
            
            # Extract enhanced metadata
            paper_title = metadata.get('paper_title', 'Unknown Title')
            authors = metadata.get('authors', 'Unknown Authors')
            journal = metadata.get('journal', 'Unknown Journal')
            publication_date = metadata.get('publication_date', '')
            doi = metadata.get('doi', '')
            section = metadata.get('section', 'Unknown Section')
            
            # Build rich source header
            source_header = f"{source_id} "
            if paper_title != 'Unknown Title':
                source_header += f'"{paper_title}"'
            if authors != 'Unknown Authors' and authors:
                source_header += f" by {authors}"
            if journal and journal != 'Unknown Journal':
                source_header += f" ({journal}"
                if publication_date:
                    source_header += f", {publication_date}"
                source_header += ")"
            if section != 'Unknown Section':
                source_header += f" - {section} section"
            if doi:
                source_header += f" [DOI: {doi}]"
            
            source_header += ":\n"
            
            # Add document content with enhanced header
            doc_context = f"{source_header}{doc}\n\n"
            
            # Check if adding this document would exceed max length
            if current_length + len(doc_context) > max_length:
                logger.warning(f"Context truncated at {current_length} characters")
                break
            
            context_parts.append(doc_context)
            current_length += len(doc_context)
        
        return "".join(context_parts)
    
    def _generate_answer(self, question: str, context: str, temperature: float = 0.7) -> str:
        """Generate answer using Gemini with enhanced context."""
        prompt = f"""You are an expert research assistant specializing in medical and psychological research. Based on the provided research context with detailed source information, answer the user's question accurately and comprehensively.

Context (with source details):
{context}

Question: {question}

Instructions:
1. Provide a clear, accurate answer based on the research context
2. Reference specific sources by their [Source X] numbers when citing findings
3. Include author names, journal information, and publication details when relevant
4. If the context doesn't contain enough information, clearly state what information is missing
5. Include specific details and findings from the research when relevant
6. Maintain scientific accuracy and avoid speculation
7. If multiple studies are mentioned, synthesize their findings appropriately
8. Use professional, academic language appropriate for research contexts
9. When citing findings, mention the study authors and publication details

Answer:"""

        try:
            # Configure generation parameters
            generation_config = genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=1000,
                top_p=0.8,
                top_k=40
            )
            
            response = self.model.generate_content(
                prompt,
                generation_config=generation_config
            )
            
            if response and response.text:
                return response.text.strip()
            else:
                logger.warning("Empty response from Gemini")
                return "I apologize, but I couldn't generate a proper response. Please try rephrasing your question."
                
        except Exception as e:
            logger.error(f"Answer generation failed: {str(e)}")
            return "I encountered an error while generating the answer. Please try again."
    
    def _extract_enhanced_sources(
        self,
        documents: List[str],
        metadatas: List[Dict[str, Any]],
        similarities: List[float]
    ) -> List[Dict[str, Any]]:
        """Extract and format enhanced source information with all metadata."""
        sources = []
        
        for i, (doc, metadata, similarity) in enumerate(zip(documents, metadatas, similarities)):
            # ENHANCED: Use actual document ID from metadata or generate proper string ID
            doc_id = metadata.get('document_id') or metadata.get('chunk_id') or f"doc_{i+1}"
            
            # Extract all available metadata
            paper_title = metadata.get('paper_title', 'Unknown Title')
            authors = metadata.get('authors', '')
            doi = metadata.get('doi', '')
            journal = metadata.get('journal', '')
            publication_date = metadata.get('publication_date', '')
            source_url = metadata.get('source_url', '')
            section = metadata.get('section', 'Unknown Section')
            
            # Create content preview
            content_preview = doc[:300] + "..." if len(doc) > 300 else doc
            
            source = {
                "id": str(doc_id),  # FIXED: Ensure it's always a string
                "title": paper_title,
                "source": metadata.get('source_file', 'Unknown Source'),
                "similarity": round(similarity, 3),
                "content": content_preview,
                "metadata": {
                    # Core identifiers
                    "document_id": metadata.get('document_id', ''),
                    "chunk_id": metadata.get('chunk_id', ''),
                    "source_file": metadata.get('source_file', ''),
                    
                    # Paper metadata
                    "paper_title": paper_title,
                    "authors": authors,
                    "doi": doi,
                    "publication_date": publication_date,
                    "journal": journal,
                    "source_url": source_url,
                    
                    # Section information
                    "section": section,
                    "section_index": metadata.get('section_index', 0),
                    "chunk_index": metadata.get('chunk_index', 0),
                    
                    # Content metadata
                    "token_count": metadata.get('token_count', 0),
                    "content_preview": metadata.get('content_preview', content_preview),
                    
                    # Additional metadata
                    "total_chunks": metadata.get('total_chunks', 0),
                    "priority_score": metadata.get('priority_score', 0.7),
                    "abstract": metadata.get('abstract', ''),
                    "keywords": metadata.get('keywords', '')
                }
            }
            
            sources.append(source)
        
        return sources
    
    async def get_status(self) -> Dict[str, Any]:
        """Get RAG system status with enhanced metadata information."""
        try:
            # Check embedding manager
            embedding_status = self.embedding_manager.is_loaded()
            embedding_info = self.embedding_manager.get_model_info()
            
            # Check vector database with enhanced stats
            db_stats = self.vector_db.get_collection_stats()
            
            # Test LLM
            try:
                test_response = self.model.generate_content("Test")
                llm_status = True
            except Exception:
                llm_status = False
            
            return {
                "timestamp": time.time(),
                "status": "healthy" if all([embedding_status, llm_status]) else "degraded",
                "components": {
                    "embedding_model": {
                        "status": "loaded" if embedding_status else "not_loaded",
                        "details": embedding_info
                    },
                    "vector_database": {
                        "status": db_stats.get("status", "unknown"),
                        "document_count": db_stats.get("document_count", 0),
                        "collection_name": db_stats.get("collection_name", "unknown")
                    },
                    "llm": {
                        "status": "healthy" if llm_status else "unhealthy",
                        "model": "gemini-2.0-flash"
                    }
                },
                "performance": {
                    "top_k": self.top_k,
                    "similarity_threshold": self.similarity_threshold,
                    "max_context_length": self.max_context_length
                },
                "configuration": {
                    "top_k": self.top_k,
                    "similarity_threshold": self.similarity_threshold,
                    "max_context_length": self.max_context_length
                }
            }
            
        except Exception as e:
            logger.error(f"Status check failed: {str(e)}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": time.time()
            }
    
    def update_config(
        self,
        top_k: Optional[int] = None,
        similarity_threshold: Optional[float] = None,
        max_context_length: Optional[int] = None
    ) -> bool:
        """Update RAG configuration parameters."""
        try:
            if top_k is not None:
                self.top_k = top_k
            if similarity_threshold is not None:
                self.similarity_threshold = similarity_threshold
            if max_context_length is not None:
                self.max_context_length = max_context_length
            
            logger.info(f"Configuration updated: top_k={self.top_k}, threshold={self.similarity_threshold}, max_context={self.max_context_length}")
            return True
            
        except Exception as e:
            logger.error(f"Configuration update failed: {str(e)}")
            return False
    
    async def chat(self, messages: List[Dict], include_context: bool = True, max_tokens: int = 1000) -> Dict[str, Any]:
        """Handle chat conversations with enhanced context."""
        # Simple implementation - can be enhanced
        last_message = messages[-1]
        if last_message['role'] == 'user':
            result = await self.query(last_message['content'], include_sources=include_context)
            return {
                "response": result['answer'],
                "sources": result.get('sources', []),
                "processing_time": result.get('processing_time', 0)
            }
        return {"response": "Invalid message format", "sources": [], "processing_time": 0}
    
    async def reset(self) -> Dict[str, Any]:
        """Reset the RAG system."""
        try:
            # Clear vector database
            success = self.vector_db.clear_collection()
            return {
                "message": "RAG system reset successfully",
                "success": success
            }
        except Exception as e:
            logger.error(f"Reset failed: {str(e)}")
            raise
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Get enhanced performance metrics."""
        return {
            "timestamp": time.time(),
            "embedding_model": self.embedding_manager.get_model_info(),
            "database_stats": self.vector_db.get_collection_stats(),
            "configuration": {
                "top_k": self.top_k,
                "similarity_threshold": self.similarity_threshold,
                "max_context_length": self.max_context_length
            }
        }