import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from loguru import logger

from app.config import settings


@dataclass
class DocumentChunk:
    """Represents a chunk of text with metadata."""
    text: str
    metadata: Dict[str, Any]
    chunk_id: str
    start_idx: int
    end_idx: int


class TextChunker:
    """
    Advanced text chunking engine for optimal RAG performance.
    Based on no3_chunking_engine.ipynb implementation.
    """
    
    def __init__(
        self,
        chunk_size: int = None,
        chunk_overlap: int = None,
        min_chunk_size: int = 50
    ):
        """
        Initialize the text chunker.
        
        Args:
            chunk_size: Maximum chunk size in characters
            chunk_overlap: Overlap between consecutive chunks
            min_chunk_size: Minimum chunk size to avoid tiny chunks
        """
        self.chunk_size = chunk_size or settings.chunk_size
        self.chunk_overlap = chunk_overlap or settings.chunk_overlap
        self.min_chunk_size = min_chunk_size
        
        # Sentence boundary patterns
        self.sentence_endings = re.compile(r'[.!?]+\s+')
        self.paragraph_breaks = re.compile(r'\n\s*\n')
        
        logger.info(f"TextChunker initialized: size={self.chunk_size}, overlap={self.chunk_overlap}")
    
    def chunk_text(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
        preserve_structure: bool = True
    ) -> List[DocumentChunk]:
        """
        Chunk text into optimal segments for RAG.
        
        Args:
            text: Input text to chunk
            metadata: Base metadata to attach to all chunks
            preserve_structure: Whether to preserve paragraph boundaries
            
        Returns:
            List of DocumentChunk objects
        """
        if not text or len(text.strip()) < self.min_chunk_size:
            logger.warning("Text too short for chunking")
            return []
        
        metadata = metadata or {}
        chunks = []
        
        if preserve_structure:
            chunks = self._chunk_with_structure(text, metadata)
        else:
            chunks = self._chunk_simple(text, metadata)
        
        # Filter out chunks that are too small
        chunks = [chunk for chunk in chunks if len(chunk.text.strip()) >= self.min_chunk_size]
        
        logger.info(f"Created {len(chunks)} chunks from text of length {len(text)}")
        return chunks
    
    def _chunk_with_structure(
        self,
        text: str,
        base_metadata: Dict[str, Any]
    ) -> List[DocumentChunk]:
        """Chunk text while preserving paragraph and sentence boundaries."""
        chunks = []
        
        # Split into paragraphs first
        paragraphs = self.paragraph_breaks.split(text)
        current_chunk = ""
        current_start = 0
        chunk_counter = 0
        
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
            
            # If adding this paragraph would exceed chunk size
            if len(current_chunk) + len(paragraph) > self.chunk_size and current_chunk:
                # Save current chunk
                chunk = self._create_chunk(
                    text=current_chunk.strip(),
                    metadata=base_metadata,
                    chunk_id=f"chunk_{chunk_counter}",
                    start_idx=current_start,
                    end_idx=current_start + len(current_chunk)
                )
                chunks.append(chunk)
                
                # Start new chunk with overlap
                overlap_text = self._get_overlap_text(current_chunk)
                current_chunk = overlap_text + paragraph
                current_start = current_start + len(current_chunk) - len(overlap_text)
                chunk_counter += 1
            else:
                # Add paragraph to current chunk
                if current_chunk:
                    current_chunk += "\n\n" + paragraph
                else:
                    current_chunk = paragraph
                    current_start = text.find(paragraph, current_start)
        
        # Add final chunk if it exists
        if current_chunk.strip():
            chunk = self._create_chunk(
                text=current_chunk.strip(),
                metadata=base_metadata,
                chunk_id=f"chunk_{chunk_counter}",
                start_idx=current_start,
                end_idx=current_start + len(current_chunk)
            )
            chunks.append(chunk)
        
        return chunks
    
    def _chunk_simple(
        self,
        text: str,
        base_metadata: Dict[str, Any]
    ) -> List[DocumentChunk]:
        """Simple sliding window chunking."""
        chunks = []
        start = 0
        chunk_counter = 0
        
        while start < len(text):
            end = min(start + self.chunk_size, len(text))
            
            # Try to end at sentence boundary if within reasonable distance
            if end < len(text):
                # Look for sentence ending within last 100 characters
                search_start = max(end - 100, start)
                search_text = text[search_start:end + 50]
                
                match = None
                for match in self.sentence_endings.finditer(search_text):
                    pass  # Get the last match
                
                if match:
                    end = search_start + match.end()
            
            chunk_text = text[start:end].strip()
            
            if chunk_text:
                chunk = self._create_chunk(
                    text=chunk_text,
                    metadata=base_metadata,
                    chunk_id=f"chunk_{chunk_counter}",
                    start_idx=start,
                    end_idx=end
                )
                chunks.append(chunk)
                chunk_counter += 1
            
            # Move start position with overlap
            start = max(start + self.chunk_size - self.chunk_overlap, end)
            
            # Prevent infinite loop
            if start >= len(text):
                break
        
        return chunks
    
    def _get_overlap_text(self, text: str) -> str:
        """Get overlap text from the end of current chunk."""
        if len(text) <= self.chunk_overlap:
            return text
        
        # Try to get overlap at sentence boundary
        overlap_start = len(text) - self.chunk_overlap
        search_text = text[overlap_start:]
        
        # Find first sentence boundary in overlap region
        match = self.sentence_endings.search(search_text)
        if match:
            return search_text[match.end():]
        
        # If no sentence boundary, use character-based overlap
        return text[-self.chunk_overlap:]
    
    def _create_chunk(
        self,
        text: str,
        metadata: Dict[str, Any],
        chunk_id: str,
        start_idx: int,
        end_idx: int
    ) -> DocumentChunk:
        """Create a DocumentChunk with enhanced metadata."""
        chunk_metadata = metadata.copy()
        chunk_metadata.update({
            "chunk_id": chunk_id,
            "chunk_size": len(text),
            "start_index": start_idx,
            "end_index": end_idx,
            "word_count": len(text.split()),
            "sentence_count": len(self.sentence_endings.findall(text))
        })
        
        return DocumentChunk(
            text=text,
            metadata=chunk_metadata,
            chunk_id=chunk_id,
            start_idx=start_idx,
            end_idx=end_idx
        )
    
    def chunk_documents(
        self,
        documents: List[Dict[str, Any]],
        text_field: str = "content",
        metadata_fields: Optional[List[str]] = None
    ) -> List[DocumentChunk]:
        """
        Chunk multiple documents.
        
        Args:
            documents: List of document dictionaries
            text_field: Field name containing the text content
            metadata_fields: Fields to preserve as metadata
            
        Returns:
            List of all chunks from all documents
        """
        metadata_fields = metadata_fields or []
        all_chunks = []
        
        for doc_idx, doc in enumerate(documents):
            if text_field not in doc:
                logger.warning(f"Document {doc_idx} missing text field '{text_field}'")
                continue
            
            # Extract metadata
            doc_metadata = {"document_index": doc_idx}
            for field in metadata_fields:
                if field in doc:
                    doc_metadata[field] = doc[field]
            
            # Chunk document
            chunks = self.chunk_text(
                text=doc[text_field],
                metadata=doc_metadata
            )
            
            all_chunks.extend(chunks)
        
        logger.info(f"Chunked {len(documents)} documents into {len(all_chunks)} total chunks")
        return all_chunks