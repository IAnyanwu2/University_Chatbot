import os
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import json

from vector_store import VectorStore, RetrievalResult
from llm_interface import OllamaLLM, LLMResponse
from document_processor import DocumentProcessor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ChatResponse:
    """Complete response from the RAG system"""
    answer: str
    confidence: float
    sources: List[str]
    retrieved_chunks: List[str]
    query: str

class RAGChatbot:
    """Main RAG-based chatbot for GSU CS Graduate Program"""
    
    def __init__(self, 
                 vector_store: VectorStore,
                 llm: OllamaLLM,
                 min_confidence_threshold: float = 0.3,
                 max_retrieved_chunks: int = 5):
        
        self.vector_store = vector_store
        self.llm = llm
        self.min_confidence_threshold = min_confidence_threshold
        self.max_retrieved_chunks = max_retrieved_chunks
        
        # Keywords that indicate personal/private queries
        self.personal_keywords = [
            'my application', 'my status', 'my grades', 'my transcript',
            'personal information', 'application status', 'admission decision'
        ]
        
        # Keywords that indicate off-topic queries
        self.off_topic_indicators = [
            'weather', 'sports', 'politics', 'cooking', 'travel',
            'entertainment', 'movies', 'music', 'restaurant'
        ]
    
    def _is_personal_query(self, query: str) -> bool:
        """Check if query is asking for personal/private information"""
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in self.personal_keywords)
    
    def _is_off_topic(self, query: str) -> bool:
        """Check if query is unrelated to CS graduate program"""
        query_lower = query.lower()
        return any(indicator in query_lower for indicator in self.off_topic_indicators)
    
    def _handle_personal_query(self, query: str) -> ChatResponse:
        """Handle queries about personal/private information"""
        response_text = """I can't access personal information like application status or grades. For questions about your specific situation, please contact:

📧 **CS Graduate Program Coordinator**: cs-grad@gsu.edu
📞 **Department Phone**: (404) 413-5820
🏢 **Office**: 25 Park Place, Suite 1400

You can also check your application status through the GSU Graduate Admissions portal."""
        
        return ChatResponse(
            answer=response_text,
            confidence=1.0,
            sources=["Contact Information"],
            retrieved_chunks=[],
            query=query
        )
    
    def _handle_off_topic_query(self, query: str) -> ChatResponse:
        """Handle queries unrelated to CS graduate program"""
        response_text = """I'm specifically designed to help with questions about the GSU Computer Science Graduate Program. I can assist with:

• Admission requirements and deadlines
• Course curriculum and requirements  
• Research areas and faculty
• Financial aid and assistantships
• Student services and resources
• General program information

For other topics, please visit the main GSU website at gsu.edu or contact the appropriate department."""
        
        return ChatResponse(
            answer=response_text,
            confidence=1.0,
            sources=["Program Scope"],
            retrieved_chunks=[],
            query=query
        )
    
    def chat(self, query: str) -> ChatResponse:
        """Process a user query and return a response"""
        logger.info(f"Processing query: {query}")
        
        # Handle special cases first
        if self._is_personal_query(query):
            return self._handle_personal_query(query)
        
        if self._is_off_topic(query):
            return self._handle_off_topic_query(query)
        
        # Retrieve relevant documents
        try:
            retrieval_results = self.vector_store.similarity_search(
                query, k=self.max_retrieved_chunks
            )
            
            if not retrieval_results:
                return ChatResponse(
                    answer="I don't have information about that topic in my knowledge base. Please contact the CS department directly at cs-grad@gsu.edu for assistance.",
                    confidence=0.0,
                    sources=[],
                    retrieved_chunks=[],
                    query=query
                )
            
            # Extract chunks and scores
            chunks = [result.content for result in retrieval_results]
            scores = [result.similarity_score for result in retrieval_results]
            sources = [result.metadata.get('source', 'Unknown') for result in retrieval_results]
            
            # Generate response using LLM
            llm_response = self.llm.generate_response(query, chunks, scores)
            
            return ChatResponse(
                answer=llm_response.content,
                confidence=llm_response.confidence,
                sources=list(set(sources)),  # Remove duplicates
                retrieved_chunks=chunks[:3],  # Show top 3 for transparency
                query=query
            )
            
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return ChatResponse(
                answer="I'm experiencing technical difficulties. Please try again later or contact the CS department directly.",
                confidence=0.0,
                sources=[],
                retrieved_chunks=[],
                query=query
            )
    
    def get_system_info(self) -> Dict[str, Any]:
        """Get information about the RAG system"""
        vector_info = self.vector_store.get_collection_info()
        available_models = self.llm.list_available_models()
        
        return {
            "vector_store": vector_info,
            "available_models": available_models,
            "current_model": self.llm.model_name,
            "confidence_threshold": self.min_confidence_threshold
        }

def setup_chatbot(use_sample_data: bool = True) -> RAGChatbot:
    """Initialize and setup the RAG chatbot"""
    logger.info("Setting up RAG chatbot...")
    
    # Initialize components
    vector_store = VectorStore()
    llm = OllamaLLM()
    
    # Load documents if collection is empty
    collection_info = vector_store.get_collection_info()
    if collection_info["document_count"] == 0 and use_sample_data:
        logger.info("Loading sample documents...")
        doc_processor = DocumentProcessor()
        documents = doc_processor.load_sample_gsu_data()
        vector_store.add_documents(documents)
        logger.info("Sample documents loaded successfully")
    
    # Create chatbot
    chatbot = RAGChatbot(vector_store, llm)
    
    logger.info("RAG chatbot setup complete")
    return chatbot

if __name__ == "__main__":
    # Test the chatbot
    chatbot = setup_chatbot()
    
    # Test queries
    test_queries = [
        "What are the admission requirements?",
        "Tell me about research areas",
        "What is the GRE requirement for international students?",
        "How can I get financial aid?",
        "What is my application status?"  # Personal query test
    ]
    
    print("=== GSU CS Graduate Program Chatbot Test ===\n")
    
    for query in test_queries:
        print(f"Q: {query}")
        response = chatbot.chat(query)
        print(f"A: {response.answer}")
        print(f"Confidence: {response.confidence:.2f}")
        print(f"Sources: {response.sources}")
        print("-" * 50)