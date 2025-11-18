"""
Demo script to show the RAG retrieval system working without LLM
This demonstrates the core functionality of our chatbot
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from vector_store import VectorStore
from document_processor import DocumentProcessor

def demo_retrieval():
    print("🚀 GSU CS RAG Chatbot - Retrieval Demo")
    print("=" * 60)
    
    # Initialize components
    print("📚 Loading sample GSU CS documents...")
    doc_processor = DocumentProcessor()
    documents = doc_processor.load_sample_gsu_data()
    
    print(f"   ✓ Loaded {len(documents)} documents")
    for i, doc in enumerate(documents[:3], 1):
        print(f"   {i}. {doc.metadata['source']} ({doc.metadata['category']})")
    print("   ...")
    
    # Set up vector store
    print("\n🧠 Setting up vector database...")
    vector_store = VectorStore(collection_name="gsu_demo")
    vector_store.add_documents(documents)
    
    info = vector_store.get_collection_info()
    print(f"   ✓ Vector store ready: {info['document_count']} chunks indexed")
    
    # Test queries
    test_queries = [
        "What are the GRE requirements for international students?",
        "How much does the program cost?", 
        "What research areas are available?",
        "How long does it take to complete the program?",
        "What financial aid is available?"
    ]
    
    print("\n🔍 Testing retrieval with sample queries...")
    print("-" * 60)
    
    for query in test_queries:
        print(f"\n❓ Query: {query}")
        
        # Retrieve relevant documents
        results = vector_store.similarity_search(query, k=3)
        
        print(f"📊 Found {len(results)} relevant documents:")
        
        for i, result in enumerate(results, 1):
            similarity_pct = result.similarity_score * 100
            source = result.metadata.get('source', 'unknown')
            category = result.metadata.get('category', 'general')
            
            print(f"   {i}. [{similarity_pct:.1f}% match] {source} ({category})")
            
            # Show snippet of retrieved content
            content_snippet = result.content[:150].replace('\n', ' ')
            if len(result.content) > 150:
                content_snippet += "..."
            print(f"      💡 Context: {content_snippet}")
        
        print()
    
    print("=" * 60)
    print("🎯 Retrieval Demo Complete!")
    print("\nThis demonstrates that our RAG system can:")
    print("✅ Process and chunk documents")
    print("✅ Create semantic embeddings") 
    print("✅ Retrieve relevant context for queries")
    print("✅ Rank results by relevance")
    print("\nNext step: Add LLM (Ollama) for natural language generation")

if __name__ == "__main__":
    demo_retrieval()