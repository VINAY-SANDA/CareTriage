"""
ICMR Document Indexer
Processes PDFs and creates FAISS index with rate limiting for free API tier.
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, '.')

from app.utils.pdf_processor import PDFProcessor
from app.config import settings

def index_documents():
    """Index ICMR documents with simple text storage (no embeddings for now)."""
    import pickle
    
    processor = PDFProcessor()
    
    print(f"ICMR Documents Directory: {settings.ICMR_DOCS_DIR}")
    print(f"Directory exists: {settings.ICMR_DOCS_DIR.exists()}")
    
    # Get all PDFs
    pdf_files = list(settings.ICMR_DOCS_DIR.glob("*.pdf"))
    print(f"Found {len(pdf_files)} PDF files: {[f.name for f in pdf_files]}")
    
    if not pdf_files:
        print("No PDF files found!")
        return
    
    # Process all documents
    print("\nExtracting text from PDFs...")
    all_chunks = processor.process_directory(settings.ICMR_DOCS_DIR)
    print(f"Created {len(all_chunks)} text chunks from documents")
    
    # Save chunks to disk (without embeddings for now)
    chunks_path = settings.VECTOR_STORE_DIR / "chunks.pkl"
    chunks_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(chunks_path, 'wb') as f:
        pickle.dump(all_chunks, f)
    
    print(f"\nSaved {len(all_chunks)} chunks to {chunks_path}")
    print("\nDocument text is now indexed and ready for keyword search.")
    print("For full semantic search, embeddings will be generated when you have more API quota.")
    
    return all_chunks

if __name__ == "__main__":
    chunks = index_documents()
    if chunks:
        print(f"\n✅ Successfully indexed {len(chunks)} document chunks!")
        print("\nSample chunk:")
        print("-" * 50)
        print(f"Source: {chunks[0].source}, Page: {chunks[0].page_number}")
        print(chunks[0].text[:300] + "...")
