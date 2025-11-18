"""
Enhanced RAG Chatbot using ChromaDB Vector Store and Semantic Search
Replaces TF-IDF with proper embedding-based retrieval
"""

import os
import logging
import re
from typing import List, Dict, Any, Optional
from pathlib import Path

# Import our enhanced components
from enhanced_document_processor import EnhancedDocumentProcessor
from chroma_vector_store import ChromaVectorStore
from cloud_llm_interface import CloudLLMInterface, LLMResponse

# Import original components we still need
from document_processor import DocumentProcessor
import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedRAGChatbot:
    def get_all_faculty_names(self) -> List[str]:
        """Extract all faculty names from the vector store metadata and content."""
        names = set()
        info = self.vector_store.get_collection_info()
        sample_docs = self.vector_store.get_sample_documents(limit=100)
        for doc in sample_docs:
            # Look for patterns like 'Dr. Name', 'Professor Name', etc.
            matches = re.findall(r'(Dr\.?|Professor|Prof\.?)[ ]+[A-Z][a-z]+[ ]+[A-Z][a-z]+', doc.get('content', ''))
            for m in matches:
                names.add(m.strip())
            # Also check metadata for names
            if 'faculty_name' in doc:
                names.add(doc['faculty_name'])
        return list(names)

    def fuzzy_match_names(self, query: str, names: List[str], threshold: float = 0.6) -> List[str]:
        from difflib import SequenceMatcher
        query_lower = query.lower()
        matches = []
        for name in names:
            name_lower = name.lower()
            ratio = SequenceMatcher(None, query_lower, name_lower).ratio()
            if ratio >= threshold or any(token in name_lower for token in query_lower.split() if len(token) > 2):
                matches.append(name)
        return matches
    """Enhanced RAG chatbot with semantic search and proper embeddings"""
    
    def __init__(self, 
                 data_directory: str = "./data",
                 vector_db_path: str = "./chroma_db",
                 embedding_model: str = "all-mpnet-base-v2",
                 rebuild_vector_store: bool = False):
        
        self.data_directory = Path(data_directory)
        self.vector_db_path = vector_db_path
        self.embedding_model = embedding_model
        
        # Initialize components
        logger.info("Initializing Enhanced RAG Chatbot...")
        
        # Document processor for initial data loading
        self.doc_processor = EnhancedDocumentProcessor(data_directory)
        
        # Enhanced document processor for embeddings
        self.enhanced_processor = EnhancedDocumentProcessor(embedding_model=embedding_model)
        
        # Vector store with ChromaDB
        self.vector_store = ChromaVectorStore(
            collection_name="gsu_cs_knowledge",
            persist_directory=vector_db_path,
            embedding_model=embedding_model
        )
        
        # LLM interface
        self.llm = CloudLLMInterface()
        
        # Initialize or rebuild vector store
        if rebuild_vector_store:
            self._rebuild_vector_store()
        else:
            self._ensure_vector_store_populated()
        
        logger.info("Enhanced RAG Chatbot initialized successfully!")
    
    def _rebuild_vector_store(self):
        """Rebuild vector store from scratch"""
        logger.info("Rebuilding vector store...")
        
        # Load documents using enhanced processor (inherits from base DocumentProcessor)
        documents = self.doc_processor.load_real_gsu_data()
        logger.info(f"Loaded {len(documents)} documents")
        
        if documents:
            # Process with embeddings and add to vector store
            enhanced_docs = self.doc_processor.process_documents_with_embeddings(documents)
            self.vector_store.add_documents(enhanced_docs)
        else:
            logger.warning("No documents found to process")
    
    def _ensure_vector_store_populated(self):
        """Ensure vector store has data, populate if empty"""
        info = self.vector_store.get_collection_info()
        
        if info.get("document_count", 0) == 0:
            logger.info("Vector store is empty, populating...")
            self._rebuild_vector_store()
        else:
            logger.info(f"Vector store contains {info['document_count']} documents")
    
    async def chat(self, user_query: str, max_context_chunks: int = 5) -> Dict[str, Any]:
        """
        Enhanced chat with semantic search and context-aware responses
        Args:
            user_query: User's question
            max_context_chunks: Maximum number of context chunks to retrieve
        Returns:
            Dict with response, confidence, sources, and debug info
        """
        # Fuzzy faculty name matching
        faculty_names = self.get_all_faculty_names()
        matched_names = self.fuzzy_match_names(user_query, faculty_names)
        if matched_names:
            if len(matched_names) == 1:
                return {
                    "response": f"Are you asking about {matched_names[0]}? Please confirm so I can provide more information.",
                    "confidence": 0.0,
                    "sources": [],
                    "debug_info": {"query": user_query, "matched_names": matched_names}
                }
            else:
                name_list = ', '.join(matched_names)
                return {
                    "response": f"Your query matches multiple faculty: {name_list}. Please specify which professor you want to know about.",
                    "confidence": 0.0,
                    "sources": [],
                    "debug_info": {"query": user_query, "matched_names": matched_names}
                }
        logger.info(f"Processing query: '{user_query}'")
        try:
            # Semantic search for relevant context
            search_results = self.vector_store.similarity_search(
                query=user_query, 
                k=max_context_chunks
            )
            # Filter out undergraduate sources
            search_results = [r for r in search_results if 'undergraduate' not in r.metadata.get('source','').lower()]
            # Fix contact info in context chunks
            for result in search_results:
                result.content = result.content.replace('cs@gsu.edu', 'cscgrad@gsu.edu')
                result.content = result.content.replace('ashwin.ashok@gsu.edu', 'aashok@gsu.edu')
                # Add more replacements for other professors as needed
            if not search_results:
                return {
                    "response": "I apologize, but I couldn't find any relevant information in my graduate knowledge base. Please contact the CS department at cscgrad@gsu.edu for assistance.",
                    "confidence": 0.0,
                    "sources": [],
                    "debug_info": {
                        "query": user_query,
                        "chunks_found": 0,
                        "search_successful": False
                    }
                }
            context_chunks = [result.content for result in search_results]
            similarity_scores = [result.similarity_score for result in search_results]
            sources = [result.metadata.get('source', 'Unknown') for result in search_results]
            logger.info(f"Found {len(search_results)} relevant chunks")
            for i, result in enumerate(search_results[:3]):
                logger.info(f"Chunk {i+1}: Score={result.similarity_score:.3f}, Source={result.metadata.get('source', 'Unknown')}")
            llm_response = self.llm.generate_response_mock(
                query=user_query,
                context_chunks=context_chunks,
                similarity_scores=similarity_scores
            )
            # Ensure conversational, context-driven response
            if not llm_response.content or 'I don' in llm_response.content:
                llm_response.content = f"Here's what I found about the graduate CS program at GSU:\n\n" + '\n\n'.join(context_chunks[:2]) + f"\n\nFor more details, contact cscgrad@gsu.edu."
            return {
                "response": llm_response.content,
                "confidence": llm_response.confidence,
                "sources": sources,
                "debug_info": {
                    "query": user_query,
                    "chunks_found": len(search_results),
                    "similarity_scores": similarity_scores,
                    "avg_similarity": sum(similarity_scores) / len(similarity_scores),
                    "search_successful": True,
                    "context_preview": [chunk[:100] + "..." for chunk in context_chunks[:2]]
                }
            }
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return {
                "response": "I encountered an error while processing your question. Please try again or contact support.",
                "confidence": 0.0,
                "sources": [],
                "debug_info": {
                    "query": user_query,
                    "error": str(e),
                    "search_successful": False
                }
            }
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        try:
            vector_info = self.vector_store.get_collection_info()
            sample_docs = self.vector_store.get_sample_documents(limit=3)
            
            return {
                "status": "healthy",
                "vector_store": vector_info,
                "sample_documents": sample_docs,
                "embedding_model": self.embedding_model,
                "data_directory": str(self.data_directory)
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    def add_documents(self, new_documents: List[str]) -> bool:
        """Add new documents to the knowledge base"""
        try:
            # Process with enhanced processor
            enhanced_chunks = self.enhanced_processor.process_documents_with_embeddings(new_documents)
            
            # Add to vector store
            self.vector_store.add_documents(enhanced_chunks)
            
            logger.info(f"Successfully added {len(new_documents)} new documents")
            return True
            
        except Exception as e:
            logger.error(f"Error adding documents: {e}")
            return False
    
    def search_knowledge_base(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search knowledge base and return raw results for inspection"""
        try:
            results = self.vector_store.similarity_search(query, k=limit)
            
            return [
                {
                    "content": result.content,
                    "metadata": result.metadata,
                    "similarity_score": result.similarity_score
                }
                for result in results
            ]
        except Exception as e:
            logger.error(f"Error searching knowledge base: {e}")
            return []

# Test function for command line usage
def test_enhanced_chatbot():
    """Test the enhanced chatbot with common queries"""
    
    print("Initializing Enhanced RAG Chatbot...")
    chatbot = EnhancedRAGChatbot(rebuild_vector_store=False)  # Set to True to rebuild
    
    # Get system status
    status = chatbot.get_system_status()
    print(f"\nSystem Status: {status['status']}")
    if status['status'] == 'healthy':
        print(f"Vector Store: {status['vector_store']['document_count']} documents")
        print(f"Embedding Model: {status['embedding_model']}")
    
    # Test queries
    test_queries = [
        "What are the GPA requirements?",
        "What is the cost of tuition?", 
        "What research areas are available?",
        "How long does the program take?",
        "What financial aid is available?"
    ]
    
    print("\n" + "="*50)
    print("TESTING ENHANCED RAG CHATBOT")
    print("="*50)
    
    for query in test_queries:
        print(f"\nQ: {query}")
        print("-" * 30)
        
        result = chatbot.chat(query)
        
        print(f"Response: {result['response']}")
        print(f"Confidence: {result['confidence']:.3f}")
        print(f"Sources: {result['sources']}")
        
        debug = result['debug_info']
        if debug['search_successful']:
            print(f"Debug: Found {debug['chunks_found']} chunks, avg similarity: {debug['avg_similarity']:.3f}")
        else:
            print(f"Debug: Search failed - {debug.get('error', 'Unknown error')}")

if __name__ == "__main__":
    test_enhanced_chatbot()