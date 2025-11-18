"""
Alternative LLM interface using cloud APIs when local Ollama isn't available
"""

import os
import logging
from typing import List, Optional
from dataclasses import dataclass
import requests
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class LLMResponse:
    content: str
    confidence: float
    sources_used: List[str]

class CloudLLMInterface:
    """Interface for cloud-based LLMs as Ollama alternative"""
    
    def __init__(self):
        # Ollama configuration
        self.ollama_url = "http://localhost:11434/api/generate"
        self.ollama_model = "gpt-oss:120b-cloud"  # Your current model
        self.use_ollama = True  # Try Ollama first
        
        self.system_prompt = """You are the Georgia State University Computer Science Graduate Program Assistant chatbot. Your role is to provide accurate, helpful information about the CS graduate program based ONLY on the provided context.

IMPORTANT GUIDELINES:
1. Answer ONLY based on the provided context documents
2. If the answer isn't in the context, say "I don't have that specific information in my knowledge base. Please contact the CS department directly."
3. Be conversational but professional
4. If asked about personal information (applications, grades, etc.), redirect to appropriate contacts
5. Always cite your sources when possible
6. If the question is unrelated to the CS graduate program, politely redirect"""
    
    def generate_response(self, query: str, context_chunks: List[str], 
                         similarity_scores: Optional[List[float]] = None) -> LLMResponse:
        """Generate response using Ollama first, fallback to mock if needed"""
        
        # Try Ollama first
        if self.use_ollama:
            try:
                response = self._generate_ollama_response(query, context_chunks, similarity_scores)
                if response:
                    return response
                logger.warning("Ollama response was empty, falling back to mock")
            except Exception as e:
                logger.warning(f"Ollama failed: {e}. Falling back to mock response.")
        
        # Fallback to mock response
        return self.generate_response_mock(query, context_chunks, similarity_scores)
    
    def _generate_ollama_response(self, query: str, context_chunks: List[str], 
                                 similarity_scores: Optional[List[float]] = None) -> Optional[LLMResponse]:
        """Generate response using local Ollama model"""
        
        # Determine confidence based on similarity scores
        confidence = 0.7
        if similarity_scores:
            avg_similarity = sum(similarity_scores) / len(similarity_scores)
            confidence = min(avg_similarity * 1.5, 1.0)
        
        # Prepare context for Ollama
        context_text = "\n\n".join(context_chunks) if context_chunks else ""
        
        # Create enhanced prompt for Ollama
        prompt = f"""{self.system_prompt}

CONTEXT FROM GSU CS GRADUATE PROGRAM DOCUMENTS:
{context_text}

USER QUESTION: {query}

Please provide a helpful and accurate answer based strictly on the context above:"""

        try:
            response = requests.post(
                self.ollama_url,
                json={
                    "model": self.ollama_model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "top_p": 0.9,
                        "max_tokens": 500
                    }
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result.get('response', '').strip()
                
                if content:
                    # Clean up response
                    content = self._clean_ollama_response(content)
                    
                    return LLMResponse(
                        content=content,
                        confidence=confidence,
                        sources_used=["Ollama Local Model"]
                    )
            else:
                logger.error(f"Ollama API error: {response.status_code}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Ollama connection failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Ollama request failed: {e}")
            return None
    
    def _clean_ollama_response(self, response: str) -> str:
        """Clean and format Ollama response"""
        # Remove any markdown artifacts
        response = response.replace('**', '')
        response = response.replace('*', '')
        
        # Ensure proper spacing
        response = ' '.join(response.split())
        
        return response.strip()

    def generate_response_mock(self, query: str, context_chunks: List[str], 
                              similarity_scores: Optional[List[float]] = None) -> LLMResponse:
        """
        Enhanced mock LLM response generator that uses retrieved context
        In production, this would call OpenAI, Anthropic, or Google APIs
        """
        
        # Determine confidence based on similarity scores
        confidence = 0.7  # default
        if similarity_scores:
            avg_similarity = sum(similarity_scores) / len(similarity_scores)
            confidence = min(avg_similarity * 1.5, 1.0)  # Increased multiplier for better confidence
            
            # Log similarity scores for debugging
            logger.info(f"Similarity scores: {similarity_scores}, Average: {avg_similarity:.3f}, Confidence: {confidence:.3f}")
        
        # Enhanced threshold - accept lower similarity if we have good context
        if confidence < 0.25 or not context_chunks:
            return LLMResponse(
                content="I don't have enough relevant information to answer your question confidently. Please contact the CS department at cs@gsu.edu or visit the program website for more details.",
                confidence=confidence,
                sources_used=[]
            )
        
        # Use actual context chunks for more relevant responses
        context_text = "\n".join(context_chunks) if context_chunks else ""
        query_lower = query.lower()
        
        # Enhanced context analysis for better responses
        if any(keyword in query_lower for keyword in ["gpa", "grade", "requirement", "prerequisite"]):
            # Look for GPA/grade info in context
            gpa_info = self._extract_gpa_info(context_text, query_lower)
            if gpa_info:
                response = f"Based on the program requirements, {gpa_info}"
            else:
                response = "For specific GPA requirements and prerequisites, please contact the CS admissions office at cs@gsu.edu or check the official graduate program website."
                
        elif any(keyword in query_lower for keyword in ["gre", "test", "score", "international"]):
            # Look for test score info in context
            test_info = self._extract_test_info(context_text)
            response = test_info if test_info else "For current test score requirements, please contact CS admissions at cs@gsu.edu."
            
        elif any(keyword in query_lower for keyword in ["cost", "tuition", "fee", "money", "price"]):
            # Look for cost info in context
            cost_info = self._extract_cost_info(context_text)
            response = cost_info if cost_info else "For current tuition and fee information, please visit the GSU Bursar's Office website or contact the CS department."
            
        elif any(keyword in query_lower for keyword in ["research", "faculty", "area", "lab", "professor"]):
            # Look for research info in context
            research_info = self._extract_research_info(context_text)
            response = research_info if research_info else "For information about research opportunities and faculty, please visit the CS department website or contact individual faculty members."
            
        elif any(keyword in query_lower for keyword in ["time", "long", "duration", "complete", "credit"]):
            # Look for program duration info in context
            duration_info = self._extract_duration_info(context_text)
            response = duration_info if duration_info else "For program duration and credit requirements, please contact the CS graduate program coordinator."
            
        elif any(keyword in query_lower for keyword in ["financial", "aid", "scholarship", "assistant", "funding"]):
            # Look for financial aid info in context
            financial_info = self._extract_financial_info(context_text)
            response = financial_info if financial_info else "For financial aid opportunities, please contact the CS department or GSU Financial Aid office."
            
        else:
            # Generic response using available context
            if context_text:
                response = f"Based on the available information: {context_text[:300]}{'...' if len(context_text) > 300 else ''}"
            else:
                response = "I can help you with information about admissions requirements, program costs, research areas, program duration, and financial aid opportunities. Could you please be more specific about what aspect of the CS graduate program you'd like to know about?"
        
        return LLMResponse(
            content=response,
            confidence=confidence,
            sources_used=[f"Context chunk {i+1}" for i in range(len(context_chunks))]
        )

    def _extract_gpa_info(self, context: str, query: str) -> Optional[str]:
        """Extract GPA/grade requirement information from context"""
        context_lower = context.lower()
        
        # Look for GPA mentions
        if any(term in context_lower for term in ["gpa", "grade point", "undergraduate", "minimum"]):
            # Find sentences containing GPA info
            sentences = context.split('.')
            gpa_sentences = [s.strip() for s in sentences if any(term in s.lower() for term in ["gpa", "grade", "3.0", "3.5", "minimum", "requirement"])]
            
            if gpa_sentences:
                return ". ".join(gpa_sentences[:2]) + "."  # Return up to 2 relevant sentences
        
        return None
    
    def _extract_test_info(self, context: str) -> Optional[str]:
        """Extract test score information from context"""
        context_lower = context.lower()
        
        if any(term in context_lower for term in ["gre", "toefl", "ielts", "test", "score"]):
            sentences = context.split('.')
            test_sentences = [s.strip() for s in sentences if any(term in s.lower() for term in ["gre", "toefl", "ielts", "test", "score", "waived"])]
            
            if test_sentences:
                return ". ".join(test_sentences[:2]) + "."
        
        return None
    
    def _extract_cost_info(self, context: str) -> Optional[str]:
        """Extract cost/tuition information from context"""
        context_lower = context.lower()
        
        if any(term in context_lower for term in ["tuition", "cost", "fee", "$", "dollar", "credit hour"]):
            sentences = context.split('.')
            cost_sentences = [s.strip() for s in sentences if any(term in s.lower() for term in ["tuition", "cost", "fee", "$", "dollar", "credit"])]
            
            if cost_sentences:
                return ". ".join(cost_sentences[:2]) + "."
        
        return None
    
    def _extract_research_info(self, context: str) -> Optional[str]:
        """Extract research information from context"""
        context_lower = context.lower()
        
        if any(term in context_lower for term in ["research", "faculty", "professor", "lab", "area", "artificial intelligence", "machine learning"]):
            sentences = context.split('.')
            research_sentences = [s.strip() for s in sentences if any(term in s.lower() for term in ["research", "faculty", "professor", "lab", "area"])]
            
            if research_sentences:
                return ". ".join(research_sentences[:3]) + "."
        
        return None
    
    def _extract_duration_info(self, context: str) -> Optional[str]:
        """Extract program duration information from context"""
        context_lower = context.lower()
        
        if any(term in context_lower for term in ["year", "semester", "credit", "hour", "time", "complete", "duration"]):
            sentences = context.split('.')
            duration_sentences = [s.strip() for s in sentences if any(term in s.lower() for term in ["year", "semester", "credit", "time", "complete"])]
            
            if duration_sentences:
                return ". ".join(duration_sentences[:2]) + "."
        
        return None
    
    def _extract_financial_info(self, context: str) -> Optional[str]:
        """Extract financial aid information from context"""
        context_lower = context.lower()
        
        if any(term in context_lower for term in ["financial", "aid", "scholarship", "assistant", "stipend", "funding", "grant"]):
            sentences = context.split('.')
            financial_sentences = [s.strip() for s in sentences if any(term in s.lower() for term in ["financial", "aid", "scholarship", "assistant", "stipend", "funding"])]
            
            if financial_sentences:
                return ". ".join(financial_sentences[:2]) + "."
        
        return None

# Configuration for different cloud APIs
CLOUD_LLM_CONFIGS = {
    "openai": {
        "api_key_env": "OPENAI_API_KEY",
        "model": "gpt-3.5-turbo",
        "endpoint": "https://api.openai.com/v1/chat/completions"
    },
    "anthropic": {
        "api_key_env": "ANTHROPIC_API_KEY", 
        "model": "claude-3-haiku-20240307",
        "endpoint": "https://api.anthropic.com/v1/messages"
    },
    "google": {
        "api_key_env": "GOOGLE_API_KEY",
        "model": "gemini-1.5-flash",
        "endpoint": "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
    }
}