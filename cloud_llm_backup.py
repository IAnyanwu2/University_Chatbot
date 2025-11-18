"""
Ollama LLM interface for local model integration with intent classification and persistent history
"""

import os
import logging
import requests
import json
import re
from typing import List, Optional
from dataclasses import dataclass

# Import new components
try:
    from intent_classifier import IntentClassifier, Intent
    from persistent_conversation_history import PersistentConversationHistory
    HAS_ENHANCEMENTS = True
except ImportError as e:
    HAS_ENHANCEMENTS = False
    logging.warning(f"Enhanced features not available: {e}")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class LLMResponse:
    """Response from LLM generation"""
    content: str
    confidence: float
    sources_used: List[str]

class CloudLLM:
    """Ollama LLM interface with intelligent content processing and conversation history"""
    
    def __init__(self, model_name: str = "gpt-oss:120b-cloud"):
        self.model_name = model_name
        self.ollama_url = "http://localhost:11434/api/generate"
        self.use_ollama = True  # Try Ollama first, fallback to smart processing if needed
        self.conversation_history = {}  # Store conversation history by session_id
        self.max_history_length = 10  # Keep last 10 exchanges per session
        
    def generate_response(self, 
                         query: str, 
                         context_chunks: List[str],
                         similarity_scores: Optional[List[float]] = None,
                         session_id: str = "default") -> LLMResponse:
        """Generate response using enhanced features or fallback to basic processing"""
        
        # DEBUG: Log what context we're actually getting
        logger.info(f"RAG Debug - Query: {query}")
        logger.info(f"RAG Debug - Context chunks: {len(context_chunks)}")
        for i, chunk in enumerate(context_chunks[:2]):  # Log first 2 chunks
            logger.info(f"RAG Debug - Chunk {i+1}: {chunk[:200]}...")
        
        # Use enhanced processing if available
        if self.use_enhancements:
            return self._generate_enhanced_response(query, context_chunks, similarity_scores, session_id)
        else:
            return self._generate_basic_response(query, context_chunks, similarity_scores, session_id)
    
    def _generate_enhanced_response(self, query: str, context_chunks: List[str], 
                                  similarity_scores: Optional[List[float]], session_id: str) -> LLMResponse:
        """Generate response using intent classification and enhanced context"""
        
        # Classify intent
        intent = self.intent_classifier.classify_intent(query)
        logger.info(f"Classified intent: {intent.name} (confidence: {intent.confidence:.2f}, topic: {intent.specific_topic})")
        
        # Determine confidence based on similarity scores
        similarity_confidence = 0.5  # default
        if similarity_scores:
            avg_similarity = sum(similarity_scores) / len(similarity_scores)
            similarity_confidence = min(avg_similarity * 10.0, 1.0)
            logger.info(f"RAG Debug - Similarity scores: {similarity_scores}")
            logger.info(f"RAG Debug - Similarity confidence: {similarity_confidence}")
        
        # Combine intent confidence with similarity confidence
        combined_confidence = (intent.confidence + similarity_confidence) / 2.0
        
        # Enhanced low confidence handling based on intent
        if similarity_confidence < 0.05:  # Very low similarity
            response_text = self._generate_intent_specific_guidance(query, intent)
            
            # Add to conversation history
            self.add_to_history(session_id, query, response_text, combined_confidence, intent.name)
            
            return LLMResponse(
                content=response_text,
                confidence=combined_confidence,
                sources_used=[]
            )
        
        # Clean and process the context first
        processed_context = self._clean_and_process_context(context_chunks)
        
        # Add conversation context from history
        conversation_context = self.get_conversation_context(session_id)
        if conversation_context:
            processed_context = conversation_context + "\n\nCurrent context:\n" + processed_context
        
        # Try Ollama first
        if self.use_ollama:
            try:
                response_text = self._generate_ollama_response(query, processed_context, intent)
                if response_text:
                    # Add to conversation history
                    self.add_to_history(session_id, query, response_text, combined_confidence, intent.name)
                    
                    return LLMResponse(
                        content=response_text,
                        confidence=combined_confidence,
                        sources_used=[f"Source {i+1}" for i in range(len(context_chunks))]
                    )
            except Exception as e:
                logger.warning(f"Ollama failed: {e}. Falling back to intelligent processing.")
        
        # Fallback to intelligent content processing with intent awareness
        response_text = self._generate_intelligent_response(query, processed_context, intent)
        
        # Add to conversation history
        self.add_to_history(session_id, query, response_text, combined_confidence, intent.name)
        
        return LLMResponse(
            content=response_text,
            confidence=combined_confidence,
            sources_used=[f"Source {i+1}" for i in range(len(context_chunks))]
        )
    
    def _generate_basic_response(self, query: str, context_chunks: List[str], 
                               similarity_scores: Optional[List[float]], session_id: str) -> LLMResponse:
        """Fallback to basic response generation without enhanced features"""
        
        # Determine confidence based on similarity scores
        confidence = 0.5  # default
        if similarity_scores:
            avg_similarity = sum(similarity_scores) / len(similarity_scores)
            confidence = min(avg_similarity * 10.0, 1.0)
            logger.info(f"RAG Debug - Similarity scores: {similarity_scores}")
            logger.info(f"RAG Debug - Confidence: {confidence}")
        
        # Low confidence threshold
        if confidence < 0.05:
            return LLMResponse(
                content="I don't have enough relevant information to answer your question confidently. Please contact the CS department at cs-grad@gsu.edu or visit the program website for more details.",
                confidence=confidence,
                sources_used=[]
            )
        
        # Clean and process the context first
        processed_context = self._clean_and_process_context(context_chunks)
        
        # Try Ollama first
        if self.use_ollama:
            try:
                response = self._generate_ollama_response(query, processed_context)
                if response:
                    return LLMResponse(
                        content=response,
                        confidence=confidence,
                        sources_used=[f"Source {i+1}" for i in range(len(context_chunks))]
                    )
            except Exception as e:
                logger.warning(f"Ollama failed: {e}. Falling back to intelligent processing.")
        
        # Fallback to intelligent content processing
        response = self._generate_intelligent_response(query, processed_context)
        
        return LLMResponse(
            content=response,
            confidence=confidence,
            sources_used=[f"Source {i+1}" for i in range(len(context_chunks))]
        )
    
    def _generate_intent_specific_guidance(self, query: str, intent: Intent) -> str:
        """Generate helpful guidance based on intent when specific information isn't available"""
        
        if intent.name == "admission_requirements":
            if intent.specific_topic == "gpa":
                return """**GPA Requirements for Graduate Admission:**

While I don't have the specific GPA requirements for GSU's CS program in my current knowledge base, most Computer Science graduate programs typically require:

• **Minimum GPA:** Usually around 3.0 for the last 60 credit hours of coursework
• **Strong Performance:** Particularly important in mathematics and computer science courses
• **Holistic Review:** GPA is considered alongside other factors like:
  - Research experience
  - Letters of recommendation
  - Statement of purpose
  - Professional experience

**Next Steps:**
• Contact the CS graduate office at 404-413-5700 for exact GPA requirements
• Review the official admissions website
• Speak with a graduate advisor about your specific situation
• Consider highlighting strong performance in relevant coursework in your application

For the most current and accurate GPA requirements, I recommend contacting the department directly."""

            else:
                return """**Admission Requirements Information:**

For specific admission requirements including GPA, GRE scores, prerequisites, and application materials, I recommend:

• **Contact the Graduate Office:** 404-413-5700
• **Visit the Program Website:** Check the official CS graduate program pages
• **Speak with an Advisor:** Schedule a consultation to discuss your specific situation
• **Review Application Materials:** Look at the detailed admission criteria

The admissions team can provide the most current and accurate requirements for the specific program you're interested in."""

        elif intent.name == "program_information":
            return """**Program Information:**

GSU offers several Computer Science graduate programs. For detailed information about:

• **Degree Options:** M.S. in Computer Science, M.S. in Data Science, Ph.D. in Computer Science
• **Curriculum Details:** Course requirements, credit hours, specializations
• **Program Duration:** Timeline and scheduling options
• **Degree Requirements:** Thesis vs. non-thesis options

**I recommend:**
• Visiting the official program website for detailed curriculum information
• Contacting the graduate office at 404-413-5700
• Speaking with current students or faculty about the program experience
• Attending information sessions or virtual tours if available"""

        elif intent.name == "research_areas":
            return """**Research Areas at GSU Computer Science:**

The CS department at GSU is active in several research areas including artificial intelligence, data science, cybersecurity, and bioinformatics. For specific information about:

• **Faculty Research Interests:** Individual faculty specializations and current projects
• **Research Opportunities:** Available positions and funding
• **Research Groups:** Active labs and their focus areas
• **Publications:** Recent research output and collaborations

**I recommend:**
• Browsing faculty profiles on the department website
• Contacting faculty members directly about their research
• Speaking with the graduate coordinator about research opportunities
• Attending department seminars or research presentations"""

        elif intent.name == "contact_information":
            return """**Contact Information:**

For current and accurate contact information, please:

• **Visit the Official Website:** Check the CS department directory
• **Main Department Number:** 404-413-5700
• **Graduate Program Office:** Contact for graduate-specific questions
• **Faculty Contacts:** Available on individual faculty pages

**Office Hours:**
• Monday - Friday: 8:30 a.m. - 5:15 p.m.
• In-person meetings by appointment

The department website will have the most up-to-date contact information for specific faculty members and staff."""

        elif intent.name == "financial_information":
            return """**Financial Information:**

For information about tuition, fees, and financial assistance:

• **Tuition and Fees:** Check the university's official tuition rates
• **Graduate Assistantships:** Research and teaching assistant positions may be available
• **Scholarships and Fellowships:** Various funding opportunities for qualified students
• **Financial Aid:** Standard financial aid options through the university

**Contact:**
• Graduate office for program-specific funding opportunities
• University financial aid office for general assistance
• Department at 404-413-5700 for assistantship information"""

        else:
            return f"""**GSU Computer Science Graduate Program:**

I'd be happy to help you learn more about the GSU Computer Science Graduate Program. For the most accurate and detailed information about your specific question, I recommend:

• **Contacting the Graduate Office:** 404-413-5700
• **Visiting the Program Website:** Official CS department pages
• **Speaking with an Advisor:** Schedule a consultation for personalized guidance
• **Attending Information Sessions:** Check for upcoming virtual or in-person events

The department staff can provide the most current information about admissions, programs, research opportunities, and other aspects of the graduate program."""

    def _generate_ollama_response(self, query: str, context: str, intent: Intent = None) -> Optional[str]:
        """Generate response using local Ollama model with intent awareness"""
        
        # Enhance prompt with intent information
        intent_guidance = ""
        if intent and intent.name != "general":
            intent_guidance = f"\nThis query is about {intent.name.replace('_', ' ')}."
            if intent.specific_topic:
                intent_guidance += f" Specifically about {intent.specific_topic}."

        prompt = f"""You are a GSU Computer Science Graduate Program assistant. You must answer STRICTLY based on the provided context documents from the official GSU website.

CRITICAL RULES:
1. Use ONLY information explicitly stated in the context below
2. If information is NOT in the context, say "This information is not available in my current knowledge base. Please contact the CS department directly."
3. DO NOT create, guess, or infer email addresses, phone numbers, or contact details
4. DO NOT use any knowledge from your training data about faculty or programs  
5. Stick strictly to what is written in the context documents{intent_guidance}

CONTEXT FROM GSU OFFICIAL WEBSITE:
{context}

USER QUESTION: {query}

ANSWER STRICTLY FROM THE CONTEXT ABOVE:"""

        try:
            response = requests.post(
                self.ollama_url,
                json={
                    "model": self.model_name,
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
                raw_response = result.get('response', '').strip()
                # Clean up any remaining markdown artifacts
                cleaned_response = self._clean_markdown_artifacts(raw_response)
                return cleaned_response
            else:
                logger.error(f"Ollama error: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Ollama request failed: {e}")
            return None
    
    def _clean_and_process_context(self, context_chunks: List[str]) -> str:
        """Clean and format the scraped content properly"""
        processed_text = ""
        
        for chunk in context_chunks:
            # Remove excessive whitespace and newlines
            cleaned = re.sub(r'\s+', ' ', chunk.strip())
            
            # Remove navigation/menu text patterns but preserve contact info
            cleaned = re.sub(r'Alumni\s+Faculty & Staff\s+Students', '', cleaned)
            cleaned = re.sub(r'Undergraduate Students\s+Two-Year Course Schedule', '', cleaned)
            
            # Preserve email patterns and phone numbers
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            phone_pattern = r'\b\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})\b'
            
            # Extract and preserve important contact/faculty information
            emails = re.findall(email_pattern, cleaned)
            phones = re.findall(phone_pattern, cleaned)
            
            # Keep faculty names and research areas
            faculty_pattern = r'(Dr\.|Professor|Prof\.)\s+[A-Z][a-z]+\s+[A-Z][a-z]+'
            faculty_names = re.findall(faculty_pattern, cleaned)
            
            # Split into sentences and filter
            sentences = cleaned.split('.')
            meaningful_sentences = []
            
            for sentence in sentences:
                sentence = sentence.strip()
                # Keep sentences with sufficient content OR important keywords
                if (len(sentence.split()) > 8 or 
                    any(keyword in sentence.lower() for keyword in 
                        ['contact', 'email', 'phone', 'dr.', 'professor', 'research', 'admission', 'requirement'])):
                    meaningful_sentences.append(sentence)
            
            if meaningful_sentences:
                processed_text += '. '.join(meaningful_sentences) + '. '
        
        return processed_text.strip()
    
    def _generate_ollama_response(self, query: str, context: str) -> Optional[str]:
        """Generate response using local Ollama model"""
        
        prompt = f"""You are a GSU Computer Science Graduate Program assistant. You must answer STRICTLY based on the provided context documents from the official GSU website.

CRITICAL RULES:
1. Use ONLY information explicitly stated in the context below
2. If information is NOT in the context, say "This information is not available in my current knowledge base. Please contact the CS department directly."
3. DO NOT create, guess, or infer email addresses, phone numbers, or contact details
4. DO NOT use any knowledge from your training data about faculty or programs
5. Stick strictly to what is written in the context documents

CONTEXT FROM GSU OFFICIAL WEBSITE:
{context}

USER QUESTION: {query}

ANSWER STRICTLY FROM THE CONTEXT ABOVE:"""

        try:
            response = requests.post(
                self.ollama_url,
                json={
                    "model": self.model_name,
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
                raw_response = result.get('response', '').strip()
                # Clean up any remaining markdown artifacts
                cleaned_response = self._clean_markdown_artifacts(raw_response)
                return cleaned_response
            else:
                logger.error(f"Ollama error: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Ollama request failed: {e}")
            return None
    
    def _clean_markdown_artifacts(self, text: str) -> str:
        """Remove markdown formatting artifacts and improve readability"""
        # Remove bold markdown
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
        text = re.sub(r'\*(.*?)\*', r'\1', text)
        
        # Remove header markdown
        text = re.sub(r'#{1,6}\s*(.*?)(?:\n|$)', r'\1\n', text)
        
        # Remove placeholder email patterns
        text = re.sub(r'\[email protected\]', 'the department email', text)
        text = re.sub(r'\[.*?\]', '', text)
        
        # CRITICAL: Remove likely hallucinated emails
        # Remove any @gatech.edu emails (wrong university)
        text = re.sub(r'\b[a-zA-Z0-9._%+-]+@gatech\.edu\b', '[contact department for email]', text)
        
        # Remove any faculty-name-based email patterns that look fabricated
        text = re.sub(r'\b[a-zA-Z]+@[a-zA-Z]+\.edu\b', '[contact department for specific email]', text)
        
        # Force proper spacing for numbered lists
        text = re.sub(r'(\d+\.\s)', r'\n\n\1', text)
        
        # Add spacing before specific information patterns
        text = re.sub(r'(\w)\s*(Core coursework|foundation courses|Breadth coursework|Elective coursework)', r'\1\n\n\2', text)
        text = re.sub(r'(\w)\s*(Research training|qualifying exam|dissertation)', r'\1\n\n\2', text)
        
        # Improve spacing for contact information and addresses  
        text = re.sub(r'(\w)\s*(at\s*)?(\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})', r'\1\n\nPhone: \3', text)
        text = re.sub(r'(\w)\s*(at:\s*)?([A-Z][^.]*University[^.]*\d+[^.]*\w+,\s*[A-Z]{2}\s*\d{5})', r'\1\n\nAddress: \3', text)
        text = re.sub(r'(\w)\s*(by email)', r'\1\n\nYou can also contact them \2', text)
        
        # Add spacing before key transition phrases
        text = re.sub(r'(\w)\s*(If you have|The best|You can also|For more|The department)', r'\1\n\n\2', text)
        
        # Force spacing for course requirements (Ph.D. specific formatting)
        text = re.sub(r'(\w)\s*(you need:|requirements:|following:|include:)', r'\1\n\n\2', text)
        
        # Clean up multiple consecutive spaces and normalize paragraph breaks
        text = re.sub(r' +', ' ', text)  # Multiple spaces to single space
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)  # Multiple line breaks to double
        
        # Remove leading/trailing whitespace on each line
        lines = [line.strip() for line in text.split('\n')]
        text = '\n'.join(lines)
        
        return text.strip()
    
    def _generate_intelligent_response(self, query: str, context: str) -> str:
        """Generate intelligent response by extracting relevant content from context"""
        
        query_lower = query.lower()
        context_lower = context.lower()
        
        # Extract relevant sentences based on question type
        relevant_sentences = []
        
        # Find sentences that contain query keywords
        sentences = context.split('.')
        query_words = set(query_lower.split())
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 20:  # Skip very short sentences
                continue
                
            sentence_words = set(sentence.lower().split())
            # If sentence contains multiple query words, it's likely relevant
            if len(query_words.intersection(sentence_words)) >= 2:
                relevant_sentences.append(sentence)
        
        # If we found relevant sentences, format them nicely
        if relevant_sentences:
            # Take the most relevant ones (max 3)
            top_sentences = relevant_sentences[:3]
            
            response = "Based on the GSU Computer Science program information:\n\n"
            
            for i, sentence in enumerate(top_sentences, 1):
                # Clean up the sentence
                cleaned = sentence.strip()
                if not cleaned.endswith('.'):
                    cleaned += '.'
                response += f"• {cleaned}\n"
            
            response += f"\nFor more specific details, you can contact the CS department at cs-grad@gsu.edu or visit the program website."
            return response
        
        # If no specific content found, try category-based extraction
        if any(word in query_lower for word in ["admission", "requirement", "apply"]):
            return self._extract_admission_info(context)
        elif any(word in query_lower for word in ["course", "curriculum", "class"]):
            return self._extract_curriculum_info(context)
        elif any(word in query_lower for word in ["research", "faculty", "professor"]):
            return self._extract_research_info(context)
        elif any(word in query_lower for word in ["cost", "tuition", "financial"]):
            return self._extract_financial_info(context)
        else:
            # Generic extraction - just return the most relevant chunk
            if context and len(context) > 100:
                snippet = context[:400] + "..." if len(context) > 400 else context
                return f"Based on the available information:\n\n{snippet}\n\nFor more detailed information, please contact the CS department at cs-grad@gsu.edu."
            
            return "I'd be happy to help you with information about the GSU Computer Science Graduate Program. Could you please ask a more specific question about admissions, curriculum, research areas, or other aspects of the program?"
    
    def _extract_admission_info(self, context: str) -> str:
        """Extract admission-related information from context"""
        admission_keywords = ["admission", "requirement", "gpa", "gre", "toefl", "transcript", "application", "bachelor", "degree"]
        relevant_info = []
        
        sentences = context.split('.')
        for sentence in sentences:
            if any(keyword in sentence.lower() for keyword in admission_keywords) and len(sentence.strip()) > 20:
                relevant_info.append(sentence.strip())
        
        if relevant_info:
            response = "**Admission Requirements for GSU CS Graduate Program:**\n\n"
            for info in relevant_info[:4]:  # Limit to 4 most relevant
                if not info.endswith('.'):
                    info += '.'
                response += f"• {info}\n"
            response += f"\nFor complete admission requirements and application procedures, contact cs-grad@gsu.edu."
            return response
        
        return "I don't have specific admission requirement details in the current context. Please contact the CS department at cs-grad@gsu.edu for detailed admission requirements."
    
    def _extract_curriculum_info(self, context: str) -> str:
        """Extract curriculum-related information from context"""
        curriculum_keywords = ["course", "credit", "curriculum", "degree", "program", "semester", "thesis", "project"]
        relevant_info = []
        
        sentences = context.split('.')
        for sentence in sentences:
            if any(keyword in sentence.lower() for keyword in curriculum_keywords) and len(sentence.strip()) > 20:
                relevant_info.append(sentence.strip())
        
        if relevant_info:
            response = "**GSU CS Graduate Program Curriculum:**\n\n"
            for info in relevant_info[:4]:
                if not info.endswith('.'):
                    info += '.'
                response += f"• {info}\n"
            response += f"\nFor detailed course listings and requirements, visit the program website or contact cs-grad@gsu.edu."
            return response
        
        return "I don't have specific curriculum details in the current context. Please contact the CS department for detailed course information."
    
    def _extract_research_info(self, context: str) -> str:
        """Extract research-related information from context"""
        research_keywords = ["research", "faculty", "professor", "ai", "machine learning", "data science", "cybersecurity", "software"]
        relevant_info = []
        
        sentences = context.split('.')
        for sentence in sentences:
            if any(keyword in sentence.lower() for keyword in research_keywords) and len(sentence.strip()) > 20:
                relevant_info.append(sentence.strip())
        
        if relevant_info:
            response = "**Research Opportunities at GSU CS Department:**\n\n"
            for info in relevant_info[:4]:
                if not info.endswith('.'):
                    info += '.'
                response += f"• {info}\n"
            response += f"\nFor more information about specific research opportunities, contact faculty directly or reach out to cs-grad@gsu.edu."
            return response
        
        return "I don't have specific research information in the current context. Please contact the CS department for details about research opportunities."
    
    def _extract_financial_info(self, context: str) -> str:
        """Extract financial/cost information from context"""
        financial_keywords = ["tuition", "cost", "fee", "financial", "aid", "scholarship", "assistantship", "funding"]
        relevant_info = []
        
        sentences = context.split('.')
        for sentence in sentences:
            if any(keyword in sentence.lower() for keyword in financial_keywords) and len(sentence.strip()) > 20:
                relevant_info.append(sentence.strip())
        
        if relevant_info:
            response = "**Financial Information for GSU CS Graduate Program:**\n\n"
            for info in relevant_info[:4]:
                if not info.endswith('.'):
                    info += '.'
                response += f"• {info}\n"
            response += f"\nFor current tuition rates and financial aid opportunities, contact the financial aid office or cs-grad@gsu.edu."
            return response
        
        return "I don't have specific financial information in the current context. Please contact the CS department or financial aid office for details about costs and financial assistance."