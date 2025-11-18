from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import logging
import json
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Global chatbot components - import lazily to avoid transformers hang
chatbot_initialized = False
rag_chatbot = None

def init_chatbot():
    """Initialize the RAG chatbot with lazy imports"""
    global chatbot_initialized, rag_chatbot
    
    if chatbot_initialized:
        return True
        
    try:
        logger.info("Initializing RAG chatbot with chat history...")
        
        # Import here to avoid initial transformers hang
        from vector_store import VectorStore
        from llm_interface import OllamaLLM
        from document_processor import DocumentProcessor
        
        # Initialize components
        doc_processor = DocumentProcessor()
        vector_store = VectorStore()
        llm = OllamaLLM()  # Now with chat history support
        
        # Load sample documents
        documents = doc_processor.load_sample_gsu_data()
        vector_store.add_documents(documents)
        
        # Create simple chatbot wrapper
        class SimpleChatbot:
            def __init__(self, vector_store, llm):
                self.vector_store = vector_store
                self.llm = llm
            
            def chat(self, query, session_id="default"):
                # Retrieve relevant context
                results = self.vector_store.similarity_search(query, k=5)
                context_chunks = [result.content for result in results]
                similarity_scores = [result.similarity_score for result in results]
                
                # Generate response with history
                response = self.llm.generate_response(query, context_chunks, similarity_scores, session_id)
                
                # Return in expected format
                class ChatResponse:
                    def __init__(self, answer, confidence, sources):
                        self.answer = answer
                        self.confidence = confidence
                        self.sources = sources
                
                sources = [r.metadata.get('source', 'unknown') for r in results[:3]]
                return ChatResponse(response.content, response.confidence, sources)
            
            def clear_history(self, session_id="default"):
                self.llm.clear_history(session_id)
            
            def get_history(self, session_id="default"):
                return self.llm.get_history(session_id)
        
        rag_chatbot = SimpleChatbot(vector_store, llm)
        chatbot_initialized = True
        
        logger.info("Chatbot initialized successfully with chat history!")
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
    """API endpoint for chat with history"""
    global rag_chatbot
    
    if not chatbot_initialized or not rag_chatbot:
        # Try to initialize on first request
        if not init_chatbot():
            return jsonify({
                'error': 'Chatbot not initialized. Please check server logs.',
                'answer': 'System is currently initializing. Please try again in a moment.'
            }), 500
    
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        session_id = data.get('session_id', 'default')
        
        if not query:
            return jsonify({
                'error': 'Empty query',
                'answer': 'Please enter a question about the GSU CS Graduate Program.'
            }), 400
        
        logger.info(f"Processing query: {query} (session: {session_id})")
        
        # Get response from chatbot with history
        response = rag_chatbot.chat(query, session_id)
        
        # Prepare response data
        response_data = {
            'answer': response.answer,
            'confidence': response.confidence,
            'sources': response.sources,
            'query': query,
            'session_id': session_id,
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

@app.route('/api/history', methods=['GET'])
def get_history():
    """Get chat history for a session"""
    global rag_chatbot
    
    if not chatbot_initialized or not rag_chatbot:
        return jsonify({'error': 'Chatbot not initialized'}), 500
    
    try:
        session_id = request.args.get('session_id', 'default')
        history = rag_chatbot.get_history(session_id)
        
        history_data = []
        for msg in history:
            history_data.append({
                'role': msg.role,
                'content': msg.content,
                'timestamp': msg.timestamp
            })
        
        return jsonify({
            'history': history_data,
            'session_id': session_id
        })
        
    except Exception as e:
        logger.error(f"Error getting history: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/history', methods=['DELETE'])
def clear_history():
    """Clear chat history for a session"""
    global rag_chatbot
    
    if not chatbot_initialized or not rag_chatbot:
        return jsonify({'error': 'Chatbot not initialized'}), 500
    
    try:
        session_id = request.args.get('session_id', 'default')
        rag_chatbot.clear_history(session_id)
        
        return jsonify({
            'message': 'Chat history cleared',
            'session_id': session_id
        })
        
    except Exception as e:
        logger.error(f"Error clearing history: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/system_info')
def system_info():
    """API endpoint for system information"""
    global rag_chatbot, chatbot_initialized
    
    info = {
        'status': 'running',
        'chatbot_initialized': chatbot_initialized,
        'timestamp': datetime.now().isoformat(),
        'features': {
            'chat_history': True,
            'sliding_window': True,
            'session_support': True
        },
        'endpoints': {
            'chat': '/api/chat',
            'history_get': '/api/history',
            'history_clear': '/api/history (DELETE)',
            'system_info': '/api/system_info'
        }
    }
    
    return jsonify(info)

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    print("🚀 Starting GSU CS Graduate Program Chatbot Server...")
    print("💬 Features: Chat History with Sliding Window")
    print("📝 Access the chat interface at: http://localhost:5001")
    print("🔧 API endpoints:")
    print("   - Chat: POST /api/chat")
    print("   - History: GET /api/history")
    print("   - Clear: DELETE /api/history")
    print("📊 System info: /api/system_info")
    print()
    print("🔄 Chatbot will initialize on first request...")
    print("🌐 Starting web server...")
    
    # Run the Flask app on port 5001 to avoid conflicts
    app.run(
        host='0.0.0.0',
        port=5001,
        debug=True,
        use_reloader=False  # Disable reloader to avoid import issues
    )