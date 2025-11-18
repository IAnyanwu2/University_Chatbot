from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import logging
import json
from datetime import datetime

# Import lightweight components to avoid transformers import hang
from lightweight_vector_store import LightweightVectorStore
from cloud_llm import CloudLLM
from document_processor import DocumentProcessor

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Global chatbot components
vector_store = None
llm = None

def init_chatbot():
    """Initialize the lightweight chatbot"""
    global vector_store, llm
    try:
        logger.info("Initializing RAG chatbot...")
        
        # Initialize components
        doc_processor = DocumentProcessor()
        vector_store = LightweightVectorStore()
        llm = CloudLLM()
        
        # Load sample documents
        documents = doc_processor.load_sample_gsu_data()
        vector_store.add_documents(documents)
        
        logger.info("Chatbot initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize chatbot: {e}")
        return False

@app.route('/')
def index():
    """Main chat interface"""
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    """API endpoint for chat"""
    global vector_store, llm
    
    if not vector_store or not llm:
        return jsonify({
            'error': 'Chatbot not initialized. Please check server logs.',
            'answer': 'System is currently unavailable. Please try again later.'
        }), 500
    
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        
        if not query:
            return jsonify({
                'error': 'Empty query',
                'answer': 'Please enter a question about the GSU CS Graduate Program.'
            }), 400
        
        logger.info(f"Processing query: {query}")
        
        # Retrieve relevant context
        results = vector_store.similarity_search(query, k=5)
        context_chunks = [result.content for result in results]
        similarity_scores = [result.similarity_score for result in results]
        
        # Generate response
        response = llm.generate_response(query, context_chunks, similarity_scores)
        
        # Prepare response data
        response_data = {
            'answer': response.content,
            'confidence': response.confidence,
            'sources': [r.metadata.get('source', 'unknown') for r in results[:3]],
            'query': query,
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"Response generated with confidence: {response.confidence:.2f}")
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Error processing chat request: {e}")
        return jsonify({
            'error': str(e),
            'answer': 'I encountered an error processing your request. Please try again or contact the CS department directly.'
        }), 500

@app.route('/api/system_info')
def system_info():
    """API endpoint for system information"""
    global vector_store, llm
    
    info = {
        'status': 'running',
        'chatbot_initialized': vector_store is not None and llm is not None,
        'timestamp': datetime.now().isoformat(),
        'endpoints': {
            'chat': '/api/chat',
            'system_info': '/api/system_info'
        }
    }
    
    if vector_store:
        info['vector_store'] = vector_store.get_collection_info()
    
    return jsonify(info)

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    # Initialize chatbot
    print("🚀 Starting GSU CS Graduate Program Chatbot Server...")
    print("📝 Access the chat interface at: http://localhost:5000")
    print("🔧 API endpoint available at: http://localhost:5000/api/chat")
    print("📊 System info at: http://localhost:5000/api/system_info")
    print()
    
    if init_chatbot():
        print("✅ Chatbot initialized successfully!")
    else:
        print("❌ Chatbot initialization failed. Check logs for details.")
    
    print()
    print("🌐 Starting web server...")
    
    # Run the Flask app
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True,
        use_reloader=False  # Disable reloader to avoid import issues
    )