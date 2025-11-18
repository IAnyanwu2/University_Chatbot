import os
import logging
from typing import List, Dict, Any
from dataclasses import dataclass
from pathlib import Path

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from simple_langchain import Document, SimpleTextSplitter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class RetrievalResult:
    """Result from vector database retrieval"""
    content: str
    metadata: Dict[str, Any]
    similarity_score: float

class VectorStore:
    """Handles document embedding, storage, and retrieval using ChromaDB"""
    
    def __init__(self, 
                 collection_name: str = "gsu_cs_knowledge",
                 model_name: str = "all-MiniLM-L6-v2",
                 persist_directory: str = "./chroma_db"):
        
        self.collection_name = collection_name
        self.persist_directory = persist_directory
        
        # Initialize embedding model
        logger.info(f"Loading embedding model: {model_name}")
        self.embedding_model = SentenceTransformer(model_name)
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        
        # Text splitter for chunking documents
        self.text_splitter = SimpleTextSplitter(
            chunk_size=500,
            chunk_overlap=50
        )
        
    def add_documents(self, documents: List[Document]) -> None:
        """Add documents to the vector store"""
        logger.info(f"Adding {len(documents)} documents to vector store")
        
        # Split documents into chunks
        chunks = []
        for doc in documents:
            doc_chunks = self.text_splitter.split_text(doc.page_content)
            for i, chunk in enumerate(doc_chunks):
                chunk_metadata = doc.metadata.copy()
                chunk_metadata['chunk_id'] = f"{doc.metadata.get('source', 'unknown')}_{i}"
                chunks.append(Document(page_content=chunk, metadata=chunk_metadata))
        
        if not chunks:
            logger.warning("No chunks to add")
            return
            
        # Generate embeddings
        texts = [chunk.page_content for chunk in chunks]
        embeddings = self.embedding_model.encode(texts).tolist()
        
        # Prepare data for ChromaDB
        ids = [chunk.metadata['chunk_id'] for chunk in chunks]
        metadatas = [chunk.metadata for chunk in chunks]
        
        # Add to collection
        self.collection.add(
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas,
            ids=ids
        )
        
        logger.info(f"Successfully added {len(chunks)} chunks to vector store")
    
    def similarity_search(self, query: str, k: int = 5) -> List[RetrievalResult]:
        """Search for similar documents"""
        logger.info(f"Searching for: {query}")
        
        # Generate query embedding
        query_embedding = self.embedding_model.encode([query]).tolist()[0]
        
        # Search in ChromaDB
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=k,
            include=['documents', 'metadatas', 'distances']
        )
        
        # Convert to RetrievalResult objects
        retrieval_results = []
        if results['documents'][0]:  # Check if we have results
            for i, (doc, metadata, distance) in enumerate(zip(
                results['documents'][0],
                results['metadatas'][0],
                results['distances'][0]
            )):
                # Convert distance to similarity score (cosine similarity)
                similarity_score = 1 - distance
                retrieval_results.append(RetrievalResult(
                    content=doc,
                    metadata=metadata,
                    similarity_score=similarity_score
                ))
        
        logger.info(f"Found {len(retrieval_results)} relevant documents")
        return retrieval_results
    
    def get_collection_info(self) -> Dict[str, Any]:
        """Get information about the collection"""
        count = self.collection.count()
        return {
            "collection_name": self.collection_name,
            "document_count": count,
            "model_name": self.embedding_model.model_name if hasattr(self.embedding_model, 'model_name') else "all-MiniLM-L6-v2"
        }