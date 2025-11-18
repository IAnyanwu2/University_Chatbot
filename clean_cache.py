#!/usr/bin/env python3
"""
Clean corrupted cache data
"""

import pickle
import re
from simple_langchain import Document

def clean_cache():
    """Clean corrupted text data in cache"""
    
    # Load corrupted documents
    try:
        with open('data/scraped_documents.pkl', 'rb') as f:
            docs = pickle.load(f)
        print(f"Loaded {len(docs)} documents from cache")
        
        # Show before cleaning
        print("Before cleaning:")
        print(repr(docs[0].page_content[:100]))
        
        # Clean each document
        cleaned_docs = []
        for doc in docs:
            try:
                text = doc.page_content
                
                # Remove binary/non-ASCII characters
                text = re.sub(r'[^\x00-\x7F]+', ' ', text)  # Remove non-ASCII
                text = re.sub(r'[\x00-\x1F\x7F-\x9F]', ' ', text)  # Remove control characters
                text = re.sub(r'\s+', ' ', text)  # Normalize whitespace
                text = text.strip()
                
                # Only keep if we have substantial content
                if len(text) > 100:
                    new_doc = Document(
                        page_content=text,
                        metadata=doc.metadata
                    )
                    cleaned_docs.append(new_doc)
                    
            except Exception as e:
                print(f"Error cleaning document: {e}")
                continue
        
        print(f"Cleaned {len(cleaned_docs)} documents")
        
        if cleaned_docs:
            print("After cleaning:")
            print(cleaned_docs[0].page_content[:200])
            
            # Save cleaned documents
            with open('data/scraped_documents.pkl', 'wb') as f:
                pickle.dump(cleaned_docs, f)
            print("Cache updated with cleaned data")
        else:
            print("No valid documents after cleaning")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    clean_cache()