"""
ICMR STW Retrieval Agent
RAG system using FAISS Vector Database for retrieving Indian Council of Medical Research
Standard Treatment Workflows.
"""
import os
import pickle
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging
import numpy as np

from ..config import settings
from ..utils.gemini_client import gemini_client
from ..utils.pdf_processor import pdf_processor, DocumentChunk

logger = logging.getLogger(__name__)

# Try to import FAISS
try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    logger.warning("FAISS not available. RAG functionality will be limited.")


class ICMRRetrievalAgent:
    """
    Retrieval-Augmented Generation agent for ICMR Standard Treatment Workflows.
    Uses FAISS for vector similarity search.
    """
    
    def __init__(self):
        self.gemini = gemini_client
        self.processor = pdf_processor
        self.index: Optional[Any] = None
        self.chunks: List[DocumentChunk] = []
        self.index_path = settings.VECTOR_STORE_DIR / "faiss_index.bin"
        self.chunks_path = settings.VECTOR_STORE_DIR / "chunks.pkl"
        
        # Try to load existing index
        self._load_index()
    
    def _load_index(self) -> bool:
        """Load existing FAISS index if available."""
        if not FAISS_AVAILABLE:
            return False
            
        try:
            if self.index_path.exists() and self.chunks_path.exists():
                self.index = faiss.read_index(str(self.index_path))
                with open(self.chunks_path, 'rb') as f:
                    self.chunks = pickle.load(f)
                logger.info(f"Loaded existing index with {len(self.chunks)} chunks")
                return True
        except Exception as e:
            logger.error(f"Failed to load index: {e}")
        
        return False
    
    def _save_index(self):
        """Save FAISS index and chunks to disk."""
        if not FAISS_AVAILABLE or self.index is None:
            return
        
        # Ensure directory exists
        settings.VECTOR_STORE_DIR.mkdir(parents=True, exist_ok=True)
        
        faiss.write_index(self.index, str(self.index_path))
        with open(self.chunks_path, 'wb') as f:
            pickle.dump(self.chunks, f)
        
        logger.info(f"Saved index with {len(self.chunks)} chunks")
    
    def ingest_documents(self, directory: Path = None) -> Dict[str, Any]:
        """
        Process and index all PDF documents in directory.
        
        Args:
            directory: Directory containing ICMR PDFs
            
        Returns:
            Statistics about ingestion
        """
        directory = directory or settings.ICMR_DOCS_DIR
        
        # Process PDFs
        self.chunks = self.processor.process_directory(directory)
        
        if not self.chunks:
            return {
                "success": False,
                "documents_processed": 0,
                "chunks_created": 0,
                "message": "No documents found or failed to process"
            }
        
        # Create embeddings
        if FAISS_AVAILABLE:
            self._create_faiss_index()
        
        stats = self.processor.get_document_stats(directory)
        
        return {
            "success": True,
            "documents_processed": stats["total_documents"],
            "chunks_created": len(self.chunks),
            "message": f"Successfully indexed {len(self.chunks)} chunks from {stats['total_documents']} documents"
        }
    
    def _create_faiss_index(self):
        """Create FAISS index from document chunks."""
        if not self.chunks:
            logger.warning("No chunks to index")
            return
        
        logger.info(f"Creating embeddings for {len(self.chunks)} chunks...")
        
        # Get embeddings for all chunks
        texts = [chunk.text for chunk in self.chunks]
        
        # Batch embeddings (Gemini has limits)
        all_embeddings = []
        batch_size = 10
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            embeddings = self.gemini.get_embeddings(batch)
            all_embeddings.extend(embeddings)
            logger.info(f"Embedded {min(i + batch_size, len(texts))}/{len(texts)} chunks")
        
        # Convert to numpy array
        embeddings_array = np.array(all_embeddings).astype('float32')
        
        # Create FAISS index
        dimension = embeddings_array.shape[1]
        self.index = faiss.IndexFlatIP(dimension)  # Inner product for cosine similarity
        
        # Normalize embeddings for cosine similarity
        faiss.normalize_L2(embeddings_array)
        
        # Add to index
        self.index.add(embeddings_array)
        
        # Save index
        self._save_index()
        
        logger.info(f"Created FAISS index with {self.index.ntotal} vectors")
    
    def retrieve(
        self,
        query: str,
        top_k: int = None,
        filter_source: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant documents for a query.
        
        Args:
            query: Search query
            top_k: Number of results to return
            filter_source: Optional source document to filter by
            
        Returns:
            List of relevant document chunks with scores
        """
        top_k = top_k or settings.TOP_K_RESULTS
        
        if not FAISS_AVAILABLE or self.index is None or len(self.chunks) == 0:
            logger.warning("No index available for retrieval")
            return self._get_fallback_results(query)
        
        # Get query embedding
        query_embedding = self.gemini.get_query_embedding(query)
        query_vector = np.array([query_embedding]).astype('float32')
        faiss.normalize_L2(query_vector)
        
        # Search
        scores, indices = self.index.search(query_vector, min(top_k * 2, len(self.chunks)))
        
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0 or idx >= len(self.chunks):
                continue
            
            chunk = self.chunks[idx]
            
            # Apply source filter if specified
            if filter_source and chunk.source != filter_source:
                continue
            
            results.append({
                "text": chunk.text,
                "source": chunk.source,
                "page_number": chunk.page_number,
                "score": float(score),
                "metadata": chunk.metadata
            })
            
            if len(results) >= top_k:
                break
        
        return results
    
    def _get_fallback_results(self, query: str) -> List[Dict[str, Any]]:
        """Provide fallback results when FAISS is not available."""
        # Return general medical guidance
        return [{
            "text": "Please upload ICMR Standard Treatment Workflow documents to enable specific guideline retrieval. In the meantime, general medical best practices apply.",
            "source": "system",
            "page_number": 0,
            "score": 0.5,
            "metadata": {"fallback": True}
        }]
    
    def get_treatment_workflow(self, condition: str) -> Dict[str, Any]:
        """
        Get specific treatment workflow for a condition.
        
        Args:
            condition: Medical condition to look up
            
        Returns:
            Treatment workflow information
        """
        query = f"Standard treatment workflow protocol for {condition}"
        results = self.retrieve(query, top_k=3)
        
        if not results or results[0].get("metadata", {}).get("fallback"):
            return {
                "found": False,
                "condition": condition,
                "workflow": None,
                "references": [],
                "message": "No specific ICMR guidelines found. Please consult standard medical references."
            }
        
        # Compile workflow from retrieved results
        workflow_text = "\n\n".join([r["text"] for r in results])
        references = list(set([r["source"] for r in results]))
        
        return {
            "found": True,
            "condition": condition,
            "workflow": workflow_text,
            "references": references,
            "confidence": results[0]["score"]
        }
    
    def search_guidelines(self, symptoms: List[str]) -> List[Dict[str, Any]]:
        """
        Search for guidelines relevant to a set of symptoms.
        
        Args:
            symptoms: List of symptom terms
            
        Returns:
            List of relevant guideline excerpts
        """
        combined_query = f"Treatment guidelines for patient presenting with: {', '.join(symptoms)}"
        return self.retrieve(combined_query, top_k=settings.TOP_K_RESULTS)
    
    def get_index_stats(self) -> Dict[str, Any]:
        """Get statistics about the current index."""
        return {
            "faiss_available": FAISS_AVAILABLE,
            "index_loaded": self.index is not None,
            "total_chunks": len(self.chunks),
            "total_vectors": self.index.ntotal if self.index else 0,
            "unique_sources": list(set([c.source for c in self.chunks])) if self.chunks else [],
            "index_path": str(self.index_path)
        }


# Singleton instance
retrieval_agent = ICMRRetrievalAgent()
