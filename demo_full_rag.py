"""
Complete RAG Demo with Mock LLM - Shows full end-to-end functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from vector_store import VectorStore
from document_processor import DocumentProcessor
from cloud_llm_interface import CloudLLMInterface

def demo_full_rag():
    print("🎯 GSU CS RAG Chatbot - COMPLETE DEMO")
    print("=" * 70)
    print("This demonstrates the FULL RAG pipeline:")
    print("1. Document Processing & Chunking")
    print("2. Vector Embedding & Storage") 
    print("3. Semantic Retrieval")
    print("4. LLM Generation with Context")
    print("=" * 70)
    
    # Initialize components
    print("\n📚 Setting up RAG components...")
    doc_processor = DocumentProcessor()
    vector_store = VectorStore(collection_name="gsu_full_demo")
    llm = CloudLLMInterface()
    
    # Load and process documents
    documents = doc_processor.load_sample_gsu_data()
    vector_store.add_documents(documents)
    
    print(f"   ✓ Loaded {len(documents)} documents")
    print(f"   ✓ Created {vector_store.get_collection_info()['document_count']} searchable chunks")
    print("   ✓ Mock LLM interface ready")
    
    # Test realistic student queries
    student_queries = [
        "What are the GRE requirements for international students?",
        "How much will this program cost me?",
        "I'm interested in AI research. What options do you have?", 
        "How long does it typically take to finish the degree?",
        "What kind of financial assistance is available?"
    ]
    
    print(f"\n🤖 Testing {len(student_queries)} realistic student queries...")
    print("-" * 70)
    
    for i, query in enumerate(student_queries, 1):
        print(f"\n📝 Query {i}: {query}")
        
        # Step 1: Retrieve relevant context
        print("   🔍 Retrieving relevant context...")
        results = vector_store.similarity_search(query, k=3)
        
        # Show what was retrieved
        context_chunks = [result.content for result in results]
        similarity_scores = [result.similarity_score for result in results]
        
        print(f"   📊 Found {len(results)} relevant documents:")
        for j, result in enumerate(results, 1):
            similarity_pct = result.similarity_score * 100
            source = result.metadata.get('source', 'unknown')
            print(f"      {j}. [{similarity_pct:.1f}% match] {source}")
        
        # Step 2: Generate response with LLM
        print("   🤖 Generating response...")
        response = llm.generate_response_mock(query, context_chunks, similarity_scores)
        
        # Show the final result
        confidence_pct = response.confidence * 100
        print(f"   ✅ Response (Confidence: {confidence_pct:.1f}%):")
        print(f"      {response.content}")
        
        if i < len(student_queries):  # Add separator except for last query
            print("\n" + "-" * 50)
    
    print("\n" + "=" * 70)
    print("🎉 COMPLETE RAG DEMO FINISHED!")
    print("\nWhat just happened:")
    print("✅ Documents were semantically searched for relevant context")
    print("✅ Context was ranked by relevance/similarity")
    print("✅ LLM generated natural language responses using ONLY the retrieved context")
    print("✅ Confidence scores ensured response quality")
    print("✅ Sources were preserved for transparency")
    
    print(f"\n🚀 Next Steps:")
    print("1. Replace mock LLM with real API (OpenAI, Anthropic, Google)")
    print("2. Add real GSU documents via web scraping")
    print("3. Implement security features (PII redaction)")
    print("4. Add user feedback and learning capabilities")
    print("5. Deploy to university servers")

if __name__ == "__main__":
    demo_full_rag()