import pickle
import os

print("Checking for existing cached data...")
cache_file = "data/scraped_documents.pkl"

if os.path.exists(cache_file):
    try:
        with open(cache_file, 'rb') as f:
            docs = pickle.load(f)
        print(f"Found {len(docs)} cached documents")
        
        for i, doc in enumerate(docs):
            print(f"\n=== Document {i+1} ===")
            print(f"Source: {doc.metadata.get('source', 'unknown')}")
            print(f"Length: {len(doc.page_content)} characters")
            content = doc.page_content
            print(f"First 500 chars: {content[:500]}...")
            
            # Check for faculty names and contact info
            content_lower = content.lower()
            if 'professor' in content_lower or 'dr.' in content_lower or 'faculty' in content_lower:
                print("*** Contains faculty information ***")
            if '@' in content or 'email' in content_lower or 'contact' in content_lower:
                print("*** Contains contact information ***")
                
    except Exception as e:
        print(f"Error loading cache: {e}")
else:
    print("No cached data file found")

# Also check metadata
metadata_file = "data/cache_metadata.json"
if os.path.exists(metadata_file):
    import json
    with open(metadata_file, 'r') as f:
        metadata = json.load(f)
    print(f"\nCache metadata: {metadata}")
else:
    print("\nNo cache metadata found")