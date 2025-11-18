"""
Enhanced Document Processor with Embedding Support
Replaces TF-IDF with proper semantic embeddings for department-scale accuracy
"""

import os
import logging
from typing import List, Dict, Any
from pathlib import Path
import re
from sentence_transformers import SentenceTransformer
import hashlib

# Import existing document processor components
from document_processor import DocumentProcessor
from simple_langchain import Document

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedDocumentProcessor(DocumentProcessor):
    """Enhanced document processor with embedding support and better chunking"""
    
    def __init__(self, data_dir: str = "./data", embedding_model: str = "all-mpnet-base-v2"):
        super().__init__(data_dir)
        self.embedding_model_name = embedding_model
        self.embedding_model = None
        self.chunk_size = 512  # Optimal for academic content
        self.chunk_overlap = 50  # 50 token overlap for context preservation
        
        # Initialize embedding model
        self._initialize_embedding_model()
    
    def _initialize_embedding_model(self):
        """Initialize the sentence transformer model"""
        try:
            logger.info(f"Loading embedding model: {self.embedding_model_name}")
            self.embedding_model = SentenceTransformer(self.embedding_model_name)
            logger.info("Embedding model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise
    
    def process_documents_with_embeddings(self, documents: List[Document]) -> List[Dict[str, Any]]:
        """Process documents with enhanced chunking and embeddings"""
        
        logger.info(f"Processing {len(documents)} documents with embeddings...")
        enhanced_chunks = []
        
        for doc_idx, document in enumerate(documents):
            # Clean the document content
            cleaned_content = self._deep_clean_content(document.page_content)
            
            if len(cleaned_content.strip()) < 100:  # Skip very short documents
                logger.warning(f"Skipping short document {doc_idx}: {len(cleaned_content)} chars")
                continue
            
            # Create semantic chunks
            chunks = self._create_semantic_chunks(cleaned_content)
            
            for chunk_idx, chunk in enumerate(chunks):
                if len(chunk.strip()) < 50:  # Skip very short chunks
                    continue
                
                # Generate embedding
                try:
                    embedding = self.embedding_model.encode(chunk)
                    
                    enhanced_chunks.append({
                        'id': f"doc_{doc_idx}_chunk_{chunk_idx}",
                        'content': chunk,
                        'embedding': embedding.tolist(),  # Convert to list for JSON serialization
                        'metadata': {
                            **document.metadata,
                            'chunk_index': chunk_idx,
                            'document_index': doc_idx,
                            'content_hash': hashlib.md5(chunk.encode()).hexdigest()[:8],
                            'chunk_length': len(chunk)
                        }
                    })
                    
                except Exception as e:
                    logger.warning(f"Failed to generate embedding for chunk {chunk_idx} in doc {doc_idx}: {e}")
                    continue
            
            if (doc_idx + 1) % 10 == 0:
                logger.info(f"Processed {doc_idx + 1}/{len(documents)} documents...")
        
        logger.info(f"Created {len(enhanced_chunks)} enhanced chunks with embeddings")
        return enhanced_chunks
    
    def _deep_clean_content(self, content: str) -> str:
        """Enhanced content cleaning for academic content"""
        
        # Remove excessive navigation elements
        navigation_patterns = [
            r'Alumni Faculty & Staff Students',
            r'Undergraduate Students Two-Year Course Schedule',
            r'Graduate Students.*?Registration Assistance',
            r'Computer Science Club.*?Student Chapter of the ACM',
            r'Georgia State Menu.*?College to Career',
            r'Useful Links Directory.*?Ethics Hotline',
        ]
        
        for pattern in navigation_patterns:
            content = re.sub(pattern, '', content, flags=re.DOTALL | re.IGNORECASE)
        
        # Normalize whitespace
        content = re.sub(r'\s+', ' ', content)
        content = re.sub(r'\n\s*\n\s*\n+', '\n\n', content)
        
        # Remove duplicate phrases (common in scraped content)
        sentences = content.split('.')
        seen_sentences = set()
        unique_sentences = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence and len(sentence) > 10:
                # Use a simplified version for deduplication
                simplified = re.sub(r'\s+', ' ', sentence.lower())
                if simplified not in seen_sentences:
                    seen_sentences.add(simplified)
                    unique_sentences.append(sentence)
        
        return '. '.join(unique_sentences)
    
    def _create_semantic_chunks(self, content: str) -> List[str]:
        """Create semantically meaningful chunks with overlap"""
        
        # Split by meaningful boundaries (paragraphs, sections)
        paragraphs = self._split_by_semantic_boundaries(content)
        
        chunks = []
        current_chunk = ""
        
        for paragraph in paragraphs:
            # If adding this paragraph would exceed chunk size
            if len(current_chunk) + len(paragraph) > self.chunk_size:
                if current_chunk:  # Save current chunk if not empty
                    chunks.append(current_chunk.strip())
                    
                    # Start new chunk with overlap
                    current_chunk = self._create_overlap(current_chunk) + paragraph
                else:
                    # Single paragraph is too long, split it
                    sub_chunks = self._split_long_paragraph(paragraph)
                    chunks.extend(sub_chunks[:-1])  # Add all but last
                    current_chunk = sub_chunks[-1] if sub_chunks else ""
            else:
                current_chunk += " " + paragraph if current_chunk else paragraph
        
        # Add final chunk
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        # Filter out very short chunks
        chunks = [chunk for chunk in chunks if len(chunk.split()) >= 10]
        
        return chunks
    
    def _split_by_semantic_boundaries(self, content: str) -> List[str]:
        """Split content at semantic boundaries"""
        
        # Split by multiple sentence endings or section markers
        patterns = [
            r'(?<=\.)\s*(?=[A-Z][a-z])',  # Sentence boundaries
            r'(?<=:)\s*(?=[A-Z])',        # After colons
            r'(?<=\?)\s*(?=[A-Z])',       # After questions
            r'(?<=!)\s*(?=[A-Z])',        # After exclamations
        ]
        
        paragraphs = [content]
        
        for pattern in patterns:
            new_paragraphs = []
            for para in paragraphs:
                splits = re.split(pattern, para)
                new_paragraphs.extend([s.strip() for s in splits if s.strip()])
            paragraphs = new_paragraphs
        
        return paragraphs
    
    def _create_overlap(self, chunk: str) -> str:
        """Create overlap text from the end of a chunk"""
        words = chunk.split()
        if len(words) > self.chunk_overlap:
            return ' '.join(words[-self.chunk_overlap:]) + " "
        return chunk + " "
    
    def _split_long_paragraph(self, paragraph: str) -> List[str]:
        """Split a long paragraph into smaller chunks"""
        words = paragraph.split()
        chunks = []
        
        for i in range(0, len(words), self.chunk_size):
            chunk_words = words[i:i + self.chunk_size]
            chunks.append(' '.join(chunk_words))
        
        return chunks
    
    def extract_key_sections(self, content: str) -> Dict[str, str]:
        """Extract key sections for better organization"""
        
        sections = {
            'admission_requirements': '',
            'program_information': '',
            'research_areas': '',
            'faculty_information': '',
            'contact_information': '',
            'financial_information': ''
        }
        
        # Patterns to identify different sections
        section_patterns = {
            'admission_requirements': [
                r'admission.*?requirement', r'application.*?process', r'gpa.*?requirement',
                r'prerequisite', r'eligibility', r'apply.*?program'
            ],
            'program_information': [
                r'program.*?structure', r'curriculum', r'degree.*?requirement',
                r'course.*?work', r'credit.*?hour', r'graduation'
            ],
            'research_areas': [
                r'research.*?area', r'research.*?interest', r'faculty.*?research',
                r'artificial intelligence', r'machine learning', r'data science'
            ],
            'faculty_information': [
                r'faculty', r'professor', r'instructor', r'dr\.', r'ph\.d\.'
            ],
            'contact_information': [
                r'contact', r'email', r'phone', r'address', r'office'
            ],
            'financial_information': [
                r'tuition', r'cost', r'financial.*?aid', r'scholarship', r'funding'
            ]
        }
        
        sentences = content.split('.')
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 20:
                continue
                
            for section_name, patterns in section_patterns.items():
                for pattern in patterns:
                    if re.search(pattern, sentence, re.IGNORECASE):
                        sections[section_name] += sentence + '. '
                        break
        
        return sections