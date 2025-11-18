import os
import logging
from typing import List, Optional, Dict, Any
import json
import requests
from dataclasses import dataclass
from collections import deque

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ChatMessage:
    """Single chat message"""
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: str

@dataclass
class LLMResponse:
    """Response from LLM generation"""
    content: str
    confidence: float
    sources_used: List[str]

class OllamaLLM:
    """Interface to Ollama for local LLM inference with chat history"""
    
    def __init__(self, 
                 model_name: str = "gpt-oss:120b-cloud",
                 base_url: str = "http://localhost:11434",
                 temperature: float = 0.1,
                 max_tokens: int = 512,
                 history_window: int = 6):  # Keep last 6 messages (3 exchanges)
        
        self.model_name = model_name
        self.base_url = base_url
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.history_window = history_window
        
        # Chat history with sliding window
        self.chat_history = deque(maxlen=history_window)
        
        # System prompt for GSU CS chatbot
        self.system_prompt = """You are the Georgia State University Computer Science Graduate Program Assistant chatbot. Your role is to provide accurate, helpful information about the CS graduate program based ONLY on the provided context.

IMPORTANT GUIDELINES:
1. Answer ONLY based on the provided context documents
2. If the answer isn't in the context, say "I don't have that specific information in my knowledge base. Please contact the CS department directly."
3. Be conversational but professional
4. If asked about personal information (applications, grades, etc.), redirect to appropriate contacts
5. Always cite your sources when possible
6. If the question is unrelated to the CS graduate program, politely redirect

Your responses should be:
- Accurate and grounded in the provided context
- Helpful and student-friendly
- Concise but complete
- Professional yet conversational"""

    def _check_ollama_connection(self) -> bool:
        """Check if Ollama server is running and model is available"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                model_names = [model['name'] for model in models]
                if self.model_name in model_names:
                    return True
                else:
                    logger.warning(f"Model {self.model_name} not found. Available models: {model_names}")
                    return False
            return False
        except Exception as e:
            logger.error(f"Cannot connect to Ollama: {e}")
            return False

    def generate_response(self, 
                         query: str, 
                         context_chunks: List[str],
                         similarity_scores: Optional[List[float]] = None,
                         session_id: str = "default") -> LLMResponse:
        """Generate response using retrieved context"""
        
        if not self._check_ollama_connection():
            return LLMResponse(
                content="Sorry, I'm currently unavailable. Please try again later or contact the CS department directly.",
                confidence=0.0,
                sources_used=[]
            )
        
        # Build context from retrieved chunks
        context_text = "\\n\\n".join([f"[Source {i+1}]: {chunk}" for i, chunk in enumerate(context_chunks)])
        
        # Determine confidence based on similarity scores
        confidence = 0.5  # default
        if similarity_scores:
            avg_similarity = sum(similarity_scores) / len(similarity_scores)
            # More generous confidence scaling for TF-IDF
            # TF-IDF scores above 0.05 are quite good, above 0.1 are excellent
            if avg_similarity > 0.08:  # Excellent match
                confidence = 0.9
            elif avg_similarity > 0.05:  # Good match
                confidence = 0.7
            elif avg_similarity > 0.02:  # Decent match
                confidence = 0.5
            else:  # Weak match
                confidence = 0.3
        
        # Lower confidence threshold since TF-IDF scores are naturally lower
        if confidence < 0.2:
            return LLMResponse(
                content="I don't have enough relevant information to answer your question confidently. Please contact the CS department at cs@gsu.edu or visit the program website for more details.",
                confidence=confidence,
                sources_used=[]
            )
        
        # Build conversation history for context
        conversation_context = ""
        if self.chat_history:
            conversation_context = "\n\nRecent Conversation History:\n"
            for msg in list(self.chat_history):
                role_label = "Student" if msg.role == "user" else "Assistant"
                conversation_context += f"{role_label}: {msg.content}\n"
            conversation_context += "\n"

        # Create the full prompt with history
        full_prompt = f"""Context Information:
{context_text}
{conversation_context}
Current Student Question: {query}

Based on the context information provided above and the conversation history, please answer the current student's question about the GSU Computer Science Graduate Program. If the information isn't available in the context, say so and direct them to contact the department. Maintain conversational flow by referencing previous questions when relevant."""

        # Make request to Ollama
        try:
            payload = {
                "model": self.model_name,
                "prompt": full_prompt,
                "system": self.system_prompt,
                "stream": False,
                "options": {
                    "temperature": self.temperature,
                    "num_predict": self.max_tokens,
                    "top_k": 10,
                    "top_p": 0.9
                }
            }
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                generated_text = result.get('response', '').strip()
                
                # Add to chat history (sliding window)
                from datetime import datetime
                timestamp = datetime.now().isoformat()
                
                # Add user message and assistant response to history
                self.chat_history.append(ChatMessage("user", query, timestamp))
                self.chat_history.append(ChatMessage("assistant", generated_text, timestamp))
                
                # Extract sources mentioned
                sources_used = [f"Source {i+1}" for i in range(len(context_chunks))]
                
                return LLMResponse(
                    content=generated_text,
                    confidence=confidence,
                    sources_used=sources_used
                )
            else:
                logger.error(f"Ollama API error: {response.status_code}")
                return LLMResponse(
                    content="I'm experiencing technical difficulties. Please contact the CS department directly.",
                    confidence=0.0,
                    sources_used=[]
                )
                
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return LLMResponse(
                content="I'm experiencing technical difficulties. Please contact the CS department directly.",
                confidence=0.0,
                sources_used=[]
            )
    
    def clear_history(self, session_id: str = "default"):
        """Clear chat history for a session"""
        self.chat_history.clear()
        logger.info("Chat history cleared")
    
    def get_history(self, session_id: str = "default") -> List[ChatMessage]:
        """Get current chat history"""
        return list(self.chat_history)
    
    def list_available_models(self) -> List[str]:
        """List available models in Ollama"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                return [model['name'] for model in models]
            return []
        except Exception as e:
            logger.error(f"Error listing models: {e}")
            return []