"""
PDF Processing Module - INGESTION UTILITY
This is a standalone utility for data preparation, NOT loaded during FastAPI runtime.
Based on no2_pdf_processor.ipynb implementation.
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import PyPDF2
from loguru import logger


@dataclass
class ProcessedDocument:
    """Represents a processed PDF document."""
    content: str
    metadata: Dict[str, Any]
    page_count: int
    file_path: str
    processing_errors: List[str]


class PDFProcessor:
    """
    PDF processing utility for research paper ingestion.
    Based on no2_pdf_processor.ipynb - STANDALONE INGESTION TOOL.
    """
    
    def __init__(self):
        """Initialize PDF processor with cleaning patterns."""
        # Text cleaning patterns
        self.header_footer_pattern = re.compile(
            r'^\s*(page\s+\d+|copyright|©|\d+\s*$|www\..*|https?://.*)\s*$',
            re.IGNORECASE | re.MULTILINE
        )
        
        self.reference_pattern = re.compile(
            r'^\s*references?\s*$|^\s*bibliography\s*$',
            re.IGNORECASE | re.MULTILINE
        )
        
        self.excessive_whitespace = re.compile(r'\s{3,}')
        self.line_breaks = re.compile(r'\n{3,}')
        
        logger.info("PDFProcessor initialized for ingestion pipeline")
    
    def process_pdf(self, file_path: str) -> Optional[ProcessedDocument]:
        """
        Process a single PDF file into clean text.
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            ProcessedDocument or None if processing failed
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            logger.error(f"PDF file not found: {file_path}")
            return None
        
        if not file_path.suffix.lower() == '.pdf':
            logger.error(f"File is not a PDF: {file_path}")
            return None
        
        try:
            logger.info(f"Processing PDF: {file_path.name}")
            
            # Extract text from PDF
            raw_text, page_count, errors = self._extract_text_from_pdf(file_path)
            
            if not raw_text:
                logger.error(f"No text extracted from {file_path}")
                return None
            
            # Clean and normalize text
            cleaned_text = self._clean_text(raw_text)
            
            # Extract metadata
            metadata = self._extract_metadata(file_path, cleaned_text)
            
            processed_doc = ProcessedDocument(
                content=cleaned_text,
                metadata=metadata,
                page_count=page_count,
                file_path=str(file_path),
                processing_errors=errors
            )
            
            logger.info(f"Successfully processed {file_path.name}: {len(cleaned_text)} characters")
            return processed_doc
            
        except Exception as e:
            logger.error(f"Failed to process PDF {file_path}: {str(e)}")
            return None
    
    def _extract_text_from_pdf(self, file_path: Path) -> tuple[str, int, List[str]]:
        """Extract raw text from PDF file."""
        text = ""
        page_count = 0
        errors = []
        
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                page_count = len(pdf_reader.pages)
                
                for page_num, page in enumerate(pdf_reader.pages):
                    try:
                        page_text = page.extract_text()
                        if page_text:
                            text += f"\n--- PAGE {page_num + 1} ---\n{page_text}\n"
                    except Exception as e:
                        error_msg = f"Error extracting page {page_num + 1}: {str(e)}"
                        errors.append(error_msg)
                        logger.warning(error_msg)
                        
        except Exception as e:
            error_msg = f"Error reading PDF file: {str(e)}"
            errors.append(error_msg)
            logger.error(error_msg)
        
        return text, page_count, errors
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize extracted text."""
        if not text:
            return ""
        
        # Remove page markers we added
        text = re.sub(r'\n--- PAGE \d+ ---\n', '\n', text)
        
        # Remove headers and footers
        text = self.header_footer_pattern.sub('', text)
        
        # Remove excessive whitespace
        text = self.excessive_whitespace.sub(' ', text)
        text = self.line_breaks.sub('\n\n', text)
        
        # Normalize line endings
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        
        # Remove lines with only special characters
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            # Skip lines that are mostly special characters or numbers
            if len(line) < 3:
                continue
            if re.match(r'^[^\w\s]*$', line):
                continue
            cleaned_lines.append(line)
        
        # Rejoin text
        cleaned_text = '\n'.join(cleaned_lines)
        
        # Final cleanup
        cleaned_text = re.sub(r'\n\s*\n\s*\n', '\n\n', cleaned_text)
        cleaned_text = cleaned_text.strip()
        
        return cleaned_text
    
    def _extract_metadata(self, file_path: Path, content: str) -> Dict[str, Any]:
        """Extract metadata from PDF and content."""
        metadata = {
            "source": str(file_path),
            "filename": file_path.name,
            "file_size": file_path.stat().st_size,
            "processing_date": str(file_path.stat().st_mtime),
            "content_length": len(content),
            "word_count": len(content.split()),
            "document_type": "research_paper"
        }
        
        # Try to extract title (first meaningful line)
        lines = content.split('\n')
        for line in lines[:10]:  # Check first 10 lines
            line = line.strip()
            if len(line) > 10 and not line.isupper():
                metadata["title"] = line[:200]  # Limit title length
                break
        
        # Try to extract abstract
        abstract_match = re.search(
            r'abstract[:\s]+(.*?)(?=\n\s*(?:keywords|introduction|1\.|method))',
            content,
            re.IGNORECASE | re.DOTALL
        )
        if abstract_match:
            metadata["abstract"] = abstract_match.group(1).strip()[:500]
        
        return metadata
    
    def process_directory(
        self,
        directory_path: str,
        recursive: bool = True,
        file_pattern: str = "*.pdf"
    ) -> List[ProcessedDocument]:
        """
        Process all PDF files in a directory.
        
        Args:
            directory_path: Path to directory containing PDFs
            recursive: Whether to search subdirectories
            file_pattern: File pattern to match
            
        Returns:
            List of processed documents
        """
        directory = Path(directory_path)
        
        if not directory.exists():
            logger.error(f"Directory not found: {directory}")
            return []
        
        # Find PDF files
        if recursive:
            pdf_files = list(directory.rglob(file_pattern))
        else:
            pdf_files = list(directory.glob(file_pattern))
        
        logger.info(f"Found {len(pdf_files)} PDF files in {directory}")
        
        processed_docs = []
        for pdf_file in pdf_files:
            doc = self.process_pdf(pdf_file)
            if doc:
                processed_docs.append(doc)
        
        logger.info(f"Successfully processed {len(processed_docs)}/{len(pdf_files)} PDF files")
        return processed_docs


# CLI utility function for standalone usage
def main():
    """CLI entry point for PDF processing."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Process PDF files for PsyWiz ingestion")
    parser.add_argument("input_path", help="PDF file or directory path")
    parser.add_argument("--output", "-o", help="Output JSON file path")
    parser.add_argument("--recursive", "-r", action="store_true", help="Process subdirectories")
    
    args = parser.parse_args()
    
    processor = PDFProcessor()
    
    input_path = Path(args.input_path)
    if input_path.is_file():
        # Process single file
        doc = processor.process_pdf(input_path)
        if doc:
            processed_docs = [doc]
        else:
            processed_docs = []
    else:
        # Process directory
        processed_docs = processor.process_directory(
            input_path,
            recursive=args.recursive
        )
    
    if args.output:
        # Save results to JSON
        import json
        output_data = [
            {
                "content": doc.content,
                "metadata": doc.metadata,
                "page_count": doc.page_count,
                "file_path": doc.file_path,
                "processing_errors": doc.processing_errors
            }
            for doc in processed_docs
        ]
        
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Results saved to {args.output}")
    
    logger.info(f"Processing complete: {len(processed_docs)} documents processed")


if __name__ == "__main__":
    main()