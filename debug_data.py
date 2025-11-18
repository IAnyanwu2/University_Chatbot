from document_processor import DocumentProcessor
import json

dp = DocumentProcessor()
# Force refresh cache to see current data
print("Forcing cache refresh...")
docs = dp.force_refresh_cache()

print(f'\nRefreshed cache with {len(docs)} documents')

for i, doc in enumerate(docs):
    print(f'\n=== Document {i+1} ===')
    print(f'Source: {doc.metadata.get("source", "unknown")}')
    print(f'Length: {len(doc.page_content)} characters')
    print(f'First 300 chars: {doc.page_content[:300]}...')
    
    # Check for faculty/contact info
    content_lower = doc.page_content.lower()
    if any(term in content_lower for term in ['email', '@', 'contact', 'phone', 'dr.', 'professor']):
        print("*** Contains potential contact/faculty info ***")