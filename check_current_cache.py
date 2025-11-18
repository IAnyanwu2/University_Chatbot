import pickle
docs = pickle.load(open('data/scraped_documents.pkl', 'rb'))
print(f'Current cache has {len(docs)} documents')
for i, doc in enumerate(docs):
    print(f'Doc {i+1}: Source = {doc.metadata.get("source", "unknown")}')
    print(f'Content preview: {doc.page_content[:200]}...')
    print()