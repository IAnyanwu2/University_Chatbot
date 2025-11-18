"""
ChromaDB Vector Store for Persistent, Scalable Vector Search
Replaces lightweight vector store with production-ready solution
"""

import os
import logging
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings
import json
from pathlib import Path
from sentence_transformers import SentenceTransformer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RetrievalResult:
    """Result from vector database retrieval - keeping same interface"""
    def __init__(self, content: str, metadata: Dict[str, Any], similarity_score: float):
        self.content = content
        self.metadata = metadata
        self.similarity_score = similarity_score

class ChromaVectorStore:
    """Production-ready vector store using ChromaDB with persistence"""
    
    def __init__(self, 
                 collection_name: str = "gsu_cs_knowledge",
                 persist_directory: str = "./chroma_db",
                 embedding_model: str = "all-mpnet-base-v2"):
        
        self.collection_name = collection_name
        self.persist_directory = Path(persist_directory)
        self.embedding_model_name = embedding_model
        
        # Ensure persist directory exists
        self.persist_directory.mkdir(exist_ok=True)
        
        # Initialize ChromaDB client
        self._initialize_client()
        
        # Initialize embedding model
        self._initialize_embedding_model()
        
        # Get or create collection
        self._initialize_collection()
        
        logger.info(f"ChromaDB vector store initialized: {collection_name}")
    
    def _initialize_client(self):
        """Initialize ChromaDB client with persistence"""
        try:
            self.client = chromadb.PersistentClient(
                path=str(self.persist_directory),
                settings=Settings(
                    anonymized_telemetry=False,  # Disable telemetry for privacy
                    is_persistent=True
                )
            )
            logger.info(f"ChromaDB client initialized with persistence at: {self.persist_directory}")
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB client: {e}")
            raise
    
    def _initialize_embedding_model(self):
        """Initialize embedding model for query encoding"""
        try:
            logger.info(f"Loading embedding model: {self.embedding_model_name}")
            self.embedding_model = SentenceTransformer(self.embedding_model_name)
            logger.info("Embedding model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise
    
    def _initialize_collection(self):
        """Get or create the document collection"""
        try:
            # Try to get existing collection
            self.collection = self.client.get_collection(
                name=self.collection_name,
                embedding_function=None  # We'll handle embeddings ourselves
            )
            logger.info(f"Retrieved existing collection: {self.collection_name}")
            
            # Get collection stats
            count = self.collection.count()
            logger.info(f"Collection contains {count} documents")
            
        except Exception:
            # Create new collection if it doesn't exist
            logger.info(f"Creating new collection: {self.collection_name}")
            self.collection = self.client.create_collection(
                name=self.collection_name,
                embedding_function=None,  # We'll handle embeddings ourselves
                metadata={"description": "GSU CS Graduate Program Knowledge Base"}
            )
            logger.info(f"Created new collection: {self.collection_name}")
    
    def add_documents(self, enhanced_chunks: List[Dict[str, Any]]) -> None:
        """Add enhanced document chunks to ChromaDB"""
        
        if not enhanced_chunks:
            logger.warning("No chunks to add to ChromaDB")
            return
        
        logger.info(f"Adding {len(enhanced_chunks)} chunks to ChromaDB...")
        
        # Prepare data for ChromaDB
        ids = []
        embeddings = []
        documents = []
        metadatas = []
        
        for chunk in enhanced_chunks:
            ids.append(chunk['id'])
            embeddings.append(chunk['embedding'])
            documents.append(chunk['content'])
            
            # ChromaDB metadata cannot contain nested objects
            metadata = {
                'source': chunk['metadata'].get('source', 'unknown'),
                'file_type': chunk['metadata'].get('file_type', 'unknown'),
                'chunk_index': chunk['metadata'].get('chunk_index', 0),
                'document_index': chunk['metadata'].get('document_index', 0),
                'content_hash': chunk['metadata'].get('content_hash', ''),
                'chunk_length': chunk['metadata'].get('chunk_length', 0),
                'scraped_at': chunk['metadata'].get('scraped_at', '')
            }
            metadatas.append(metadata)
        
        try:
            # Add to ChromaDB in batches for efficiency
            batch_size = 100
            for i in range(0, len(ids), batch_size):
                batch_ids = ids[i:i + batch_size]
                batch_embeddings = embeddings[i:i + batch_size]
                batch_documents = documents[i:i + batch_size]
                batch_metadatas = metadatas[i:i + batch_size]
                
                self.collection.add(
                    ids=batch_ids,
                    embeddings=batch_embeddings,
                    documents=batch_documents,
                    metadatas=batch_metadatas
                )
                
                logger.info(f"Added batch {i//batch_size + 1}/{(len(ids)-1)//batch_size + 1}")
            
            logger.info(f"Successfully added all {len(enhanced_chunks)} chunks to ChromaDB")
            
        except Exception as e:
            logger.error(f"Failed to add documents to ChromaDB: {e}")
            raise
    
    def similarity_search(self, query: str, k: int = 5) -> List[RetrievalResult]:
        """Search for similar documents using semantic embeddings"""
        
        try:
            # Generate query embedding
            query_embedding = self.embedding_model.encode(query).tolist()
            
            # Search ChromaDB
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=k,
                include=['documents', 'metadatas', 'distances']
            )
            
            # Process results
            retrieval_results = []
            
            if results['documents'] and results['documents'][0]:  # ChromaDB returns nested lists
                documents = results['documents'][0]
                metadatas = results['metadatas'][0] if results['metadatas'] else [{}] * len(documents)
                distances = results['distances'][0] if results['distances'] else [1.0] * len(documents)
                
                for doc, metadata, distance in zip(documents, metadatas, distances):
                    # Convert distance to similarity score (ChromaDB uses cosine distance)
                    similarity_score = 1.0 - distance  # Convert distance to similarity
                    
                    retrieval_results.append(RetrievalResult(
                        content=doc,
                        metadata=metadata,
                        similarity_score=similarity_score
                    ))
            
            logger.info(f"Found {len(retrieval_results)} results for query: '{query[:50]}...'")
            
            # Log top results for debugging
            for i, result in enumerate(retrieval_results[:3]):
                logger.info(f"Result {i+1}: Score={result.similarity_score:.3f}, Content='{result.content[:100]}...'")
            
            return retrieval_results
            
        except Exception as e:
            logger.error(f"Error during similarity search: {e}")
            return []
    
    def delete_collection(self):
        """Delete the entire collection (for rebuilding)"""
        try:
            self.client.delete_collection(name=self.collection_name)
            logger.info(f"Deleted collection: {self.collection_name}")
        except Exception as e:
            logger.warning(f"Failed to delete collection: {e}")
    
    def rebuild_from_documents(self, documents) -> None:
        """Rebuild the entire vector store from scratch"""
        logger.info("Rebuilding vector store from documents...")
        
        # Delete existing collection
        self.delete_collection()
        
        # Recreate collection
        self._initialize_collection()
        
        # Process documents with enhanced processor
        from enhanced_document_processor import EnhancedDocumentProcessor
        processor = EnhancedDocumentProcessor(embedding_model=self.embedding_model_name)
        enhanced_chunks = processor.process_documents_with_embeddings(documents)
        
        # Add to vector store
        self.add_documents(enhanced_chunks)
        
        logger.info("Vector store rebuild completed")
    
    def get_collection_info(self) -> Dict[str, Any]:
        """Get information about the collection"""
        try:
            count = self.collection.count()
            return {
                "collection_name": self.collection_name,
                "document_count": count,
                "embedding_model": self.embedding_model_name,
                "persist_directory": str(self.persist_directory),
                "status": "healthy"
            }
        except Exception as e:
            return {
                "collection_name": self.collection_name,
                "error": str(e),
                "status": "error"
            }
    
    def get_sample_documents(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get sample documents for inspection"""
        try:
            results = self.collection.get(
                limit=limit,
                include=['documents', 'metadatas']
            )
            
            samples = []
            if results['documents']:
                for doc, metadata in zip(results['documents'], results['metadatas'] or [{}] * len(results['documents'])):
                    samples.append({
                        'content_preview': doc[:200] + "..." if len(doc) > 200 else doc,
                        'metadata': metadata
                    })
            
            return samples
        
        except Exception as e:
            logger.error(f"Error getting sample documents: {e}")
            return []