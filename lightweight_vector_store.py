"""
Lightweight vector store without sentence-transformers to avoid import hang
Uses simple TF-IDF for demonstration
"""

import os
import logging
from typing import List, Dict, Any
from dataclasses import dataclass
from pathlib import Path
import json
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class RetrievalResult:
    """Result from vector database retrieval"""
    content: str
    metadata: Dict[str, Any]
    similarity_score: float

class LightweightVectorStore:
    """Simple vector store using TF-IDF instead of sentence transformers"""
    
    def __init__(self, collection_name: str = "gsu_cs_knowledge"):
        self.collection_name = collection_name
        self.documents = []
        self.document_texts = []
        self.vectorizer = TfidfVectorizer(
            max_features=5000,  # Increased vocabulary size for better matching
            stop_words='english',
            ngram_range=(1, 3),  # Include trigrams for better phrase matching
            min_df=1,  # Include terms that appear in at least 1 document
            max_df=0.95,  # Ignore terms that appear in more than 95% of documents
            lowercase=True,
            token_pattern=r'\b[a-zA-Z][a-zA-Z0-9]*\b'  # Include alphanumeric tokens
        )
        self.document_vectors = None
        logger.info(f"Initialized lightweight vector store: {collection_name}")
    
    def add_documents(self, documents) -> None:
        """Add documents to the vector store"""
        logger.info(f"Adding {len(documents)} documents to vector store")
        
        # Improved chunking strategy
        chunks = []
        for doc in documents:
            content = doc.page_content
            source = doc.metadata.get('source', 'unknown')
            
            # Split by multiple separators for better chunking
            paragraphs = []
            
            # First try double newlines (paragraphs)
            if '\n\n' in content:
                paragraphs.extend([p.strip() for p in content.split('\n\n') if p.strip()])
            else:
                # Fall back to single newlines
                paragraphs.extend([p.strip() for p in content.split('\n') if p.strip() and len(p.strip()) > 50])
            
            # If still no good chunks, split by sentences
            if not paragraphs:
                sentences = content.split('. ')
                current_chunk = ""
                for sentence in sentences:
                    if len(current_chunk + sentence) < 500:
                        current_chunk += sentence + ". "
                    else:
                        if current_chunk.strip():
                            paragraphs.append(current_chunk.strip())
                        current_chunk = sentence + ". "
                if current_chunk.strip():
                    paragraphs.append(current_chunk.strip())
            
            # Create chunks with metadata
            for i, paragraph in enumerate(paragraphs):
                if len(paragraph) > 20:  # Only include substantial chunks
                    chunk_metadata = doc.metadata.copy()
                    chunk_metadata['chunk_id'] = f"{source}_{i}"
                    chunk_metadata['chunk_size'] = len(paragraph)
                    chunks.append({
                        'content': paragraph,
                        'metadata': chunk_metadata
                    })
        
        self.documents = chunks
        self.document_texts = [chunk['content'] for chunk in chunks]
        
        # Debug: show chunk statistics
        if chunks:
            avg_chunk_size = sum(len(chunk['content']) for chunk in chunks) / len(chunks)
            logger.info(f"Created {len(chunks)} chunks, average size: {avg_chunk_size:.0f} characters")
            
            # Show sample chunks for debugging
            for i, chunk in enumerate(chunks[:3]):
                logger.info(f"Sample chunk {i+1}: {chunk['content'][:150]}...")
        
        # Create TF-IDF vectors
        if self.document_texts:
            self.document_vectors = self.vectorizer.fit_transform(self.document_texts)
            logger.info(f"Successfully added {len(chunks)} chunks to vector store")
            logger.info(f"TF-IDF vocabulary size: {len(self.vectorizer.vocabulary_)}")
        else:
            logger.warning("No valid chunks to add")
    
    def similarity_search(self, query: str, k: int = 5) -> List[RetrievalResult]:
        """Search for similar documents"""
        if self.document_vectors is None or self.document_vectors.shape[0] == 0:
            logger.warning("No documents in vector store")
            return []
        
        logger.info(f"Searching for: {query}")
        
        # Vectorize query
        query_vector = self.vectorizer.transform([query])
        
        # Calculate similarities
        similarities = cosine_similarity(query_vector, self.document_vectors).flatten()
        
        # Debug: show similarity statistics
        max_sim = float(np.max(similarities))
        min_sim = float(np.min(similarities))
        mean_sim = float(np.mean(similarities))
        logger.info(f"Similarity stats - Max: {max_sim:.4f}, Min: {min_sim:.4f}, Mean: {mean_sim:.4f}")
        
        # Get top k results with lower threshold
        top_indices = np.argsort(similarities)[::-1][:k]
        
        results = []
        for idx in top_indices:
            # Convert numpy types to Python native types to avoid array comparison issues
            idx = int(idx)
            similarity_score = float(similarities[idx])
            # Lower threshold - include any positive similarity
            if similarity_score > 0.01:  # Lower threshold for TF-IDF
                results.append(RetrievalResult(
                    content=self.documents[idx]['content'],
                    metadata=self.documents[idx]['metadata'],
                    similarity_score=similarity_score
                ))
                logger.info(f"Match {len(results)}: Score={similarity_score:.4f}, Content preview: {self.documents[idx]['content'][:100]}...")
        
        logger.info(f"Found {len(results)} relevant documents with scores above threshold")
        
        # If no matches found, return top matches regardless of score for debugging
        if not results:
            logger.warning("No matches above threshold, returning top matches for debugging")
            for idx in top_indices[:3]:  # Return top 3 for debugging
                idx = int(idx)
                similarity_score = float(similarities[idx])
                results.append(RetrievalResult(
                    content=self.documents[idx]['content'],
                    metadata=self.documents[idx]['metadata'],
                    similarity_score=similarity_score
                ))
                logger.info(f"Debug match: Score={similarity_score:.4f}, Content preview: {self.documents[idx]['content'][:100]}...")
        
        return results
    
    def get_collection_info(self) -> Dict[str, Any]:
        """Get information about the collection"""
        return {
            "collection_name": self.collection_name,
            "document_count": len(self.documents),
            "model_name": "TF-IDF"
        }