"""
PDF Document Processor
Handles extraction, chunking, and preparation of ICMR documents for RAG.
"""
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging
from PyPDF2 import PdfReader

from ..config import settings

logger = logging.getLogger(__name__)


class DocumentChunk:
    """Represents a chunk of document text with metadata."""
    
    def __init__(
        self,
        text: str,
        source: str,
        page_number: int,
        chunk_index: int,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.text = text
        self.source = source
        self.page_number = page_number
        self.chunk_index = chunk_index
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "source": self.source,
            "page_number": self.page_number,
            "chunk_index": self.chunk_index,
            "metadata": self.metadata
        }


class PDFProcessor:
    """Processes PDF documents for the RAG system."""
    
    def __init__(
        self,
        chunk_size: int = None,
        chunk_overlap: int = None
    ):
        self.chunk_size = chunk_size or settings.CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or settings.CHUNK_OVERLAP
    
    def extract_text_from_pdf(self, pdf_path: Path) -> List[Dict[str, Any]]:
        """
        Extract text from a PDF file, page by page.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            List of dicts with page number and text
        """
        pages = []
        
        try:
            reader = PdfReader(str(pdf_path))
            
            for page_num, page in enumerate(reader.pages, start=1):
                text = page.extract_text()
                if text and text.strip():
                    pages.append({
                        "page_number": page_num,
                        "text": text.strip(),
                        "source": pdf_path.name
                    })
            
            logger.info(f"Extracted {len(pages)} pages from {pdf_path.name}")
            
        except Exception as e:
            logger.error(f"Error extracting PDF {pdf_path}: {str(e)}")
            raise
        
        return pages
    
    def chunk_text(self, text: str, source: str, page_number: int) -> List[DocumentChunk]:
        """
        Split text into overlapping chunks.
        
        Args:
            text: Text to chunk
            source: Source document name
            page_number: Page number in source
            
        Returns:
            List of DocumentChunk objects
        """
        chunks = []
        
        # Split by sentences first for cleaner chunks
        sentences = text.replace('\n', ' ').split('. ')
        
        current_chunk = ""
        chunk_index = 0
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            # Add period back if it was removed
            if not sentence.endswith('.'):
                sentence += '.'
            
            # Check if adding this sentence exceeds chunk size
            if len(current_chunk) + len(sentence) > self.chunk_size:
                if current_chunk:
                    chunks.append(DocumentChunk(
                        text=current_chunk.strip(),
                        source=source,
                        page_number=page_number,
                        chunk_index=chunk_index
                    ))
                    chunk_index += 1
                    
                    # Keep overlap from end of current chunk
                    overlap_text = current_chunk[-self.chunk_overlap:] if len(current_chunk) > self.chunk_overlap else ""
                    current_chunk = overlap_text + " " + sentence
                else:
                    current_chunk = sentence
            else:
                current_chunk = current_chunk + " " + sentence if current_chunk else sentence
        
        # Add remaining text
        if current_chunk.strip():
            chunks.append(DocumentChunk(
                text=current_chunk.strip(),
                source=source,
                page_number=page_number,
                chunk_index=chunk_index
            ))
        
        return chunks
    
    def process_directory(self, directory: Path = None) -> List[DocumentChunk]:
        """
        Process all PDFs in a directory.
        
        Args:
            directory: Directory containing PDFs (defaults to ICMR docs dir)
            
        Returns:
            List of all document chunks
        """
        directory = directory or settings.ICMR_DOCS_DIR
        all_chunks = []
        
        pdf_files = list(directory.glob("*.pdf"))
        logger.info(f"Found {len(pdf_files)} PDF files in {directory}")
        
        for pdf_path in pdf_files:
            try:
                pages = self.extract_text_from_pdf(pdf_path)
                
                for page_data in pages:
                    chunks = self.chunk_text(
                        text=page_data["text"],
                        source=page_data["source"],
                        page_number=page_data["page_number"]
                    )
                    all_chunks.extend(chunks)
                
            except Exception as e:
                logger.error(f"Failed to process {pdf_path}: {str(e)}")
                continue
        
        logger.info(f"Created {len(all_chunks)} total chunks from {len(pdf_files)} documents")
        return all_chunks
    
    def get_document_stats(self, directory: Path = None) -> Dict[str, Any]:
        """Get statistics about documents in directory."""
        directory = directory or settings.ICMR_DOCS_DIR
        
        pdf_files = list(directory.glob("*.pdf"))
        
        return {
            "total_documents": len(pdf_files),
            "document_names": [f.name for f in pdf_files],
            "directory": str(directory)
        }


# Singleton instance
pdf_processor = PDFProcessor()
