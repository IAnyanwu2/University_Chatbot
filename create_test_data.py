#!/usr/bin/env python3
"""
Create clean test data for the cache
"""

import pickle
import json
from datetime import datetime
from simple_langchain import Document

def create_test_data():
    """Create clean test data"""
    
    # Create a simple test document with GSU CS info
    test_content = """
Georgia State University Computer Science Graduate Programs

ADMISSIONS REQUIREMENTS

Master's in Computer Science:
- Bachelor's degree in Computer Science or related field
- Minimum GPA of 3.0
- GRE scores recommended
- Three letters of recommendation
- Statement of purpose
- TOEFL/IELTS for international students

PhD in Computer Science:
- Master's degree preferred
- Minimum GPA of 3.5
- GRE scores required
- Three letters of recommendation
- Research statement

FACULTY

Dr. Saeid Belkasim - Computer Vision, Image Processing
Dr. Raj Sunderraman - Database Systems, Data Mining
Dr. Ying Zhu - Computer Graphics, Virtual Reality
Dr. Ashwin Ashok - Networks, Mobile Computing
Dr. Mukesh Singhal - Distributed Systems, Cloud Computing

RESEARCH AREAS

- Artificial Intelligence and Machine Learning
- Computer Vision and Image Processing
- Data Science and Big Data Analytics
- Cybersecurity and Information Assurance
- Human-Computer Interaction
- Software Engineering
- Database Systems and Data Mining
- Computer Networks and Distributed Systems

CONTACT

Computer Science Department
Georgia State University
Email: cs-grad@gsu.edu
Phone: (404) 413-5820
    """.strip()
    
    # Create document
    doc = Document(
        page_content=test_content,
        metadata={
            "source": "test_data",
            "file_type": "text",
            "scraped_at": "2025-11-05"
        }
    )
    
    # Save to cache
    with open('data/scraped_documents.pkl', 'wb') as f:
        pickle.dump([doc], f)
    
    # Update metadata
    metadata = {
        'cached_at': datetime.now().isoformat(),
        'document_count': 1,
        'cache_hours': 24
    }
    with open('data/cache_metadata.json', 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print("Created clean test data")
    print(f"Content preview: {test_content[:200]}...")

if __name__ == "__main__":
    create_test_data()