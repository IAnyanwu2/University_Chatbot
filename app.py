from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import logging
import json
import os
import subprocess
import sys
from datetime import datetime
import os
import subprocess
import os
import re

# Import lightweight components to avoid transformers import hang
from lightweight_vector_store import LightweightVectorStore
from cloud_llm_interface import CloudLLMInterface
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
        llm = CloudLLMInterface()
        
        # Load real GSU documents from web scraping
        documents = doc_processor.load_real_gsu_data()
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
    """API endpoint for chat with history and contact lookup"""
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

        # Load known faculty emails to use for sanitization
        faculty_emails = {}
        verified_map = {}
        try:
            with open('data/faculty_emails.json', 'r', encoding='utf-8') as f:
                faculty_emails = json.load(f)
        except Exception:
            faculty_emails = {}
        try:
            with open('data/faculty_emails_verified.json', 'r', encoding='utf-8') as vf:
                verified_map = json.load(vf)
        except Exception:
            # fallback: mark any present entries as unverified unless explicitly true
            verified_map = {k: False for k in faculty_emails.keys()}

        # Prepare approved email sets
        approved_emails = set()
        for name, email in faculty_emails.items():
            if verified_map.get(name, False):
                approved_emails.add(email.lower())

        # Helper sanitizers
        email_regex = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
        phone_regex = re.compile(r"\+?\d[\d\s\-()]{7,}\d")

        def sanitize_text(text: str):
            """Redact any email or phone occurrences that are not in approved_emails."""
            if not text:
                return text, False
            redacted = False

            # redact emails not in approved list
            def _email_repl(m):
                nonlocal redacted
                email = m.group(0)
                if email.lower() in approved_emails:
                    return email
                redacted = True
                return "[contact redacted]"

            text = email_regex.sub(_email_repl, text)

            # redact phone-like strings
            def _phone_repl(m):
                nonlocal redacted
                val = m.group(0)
                # very small heuristic: if contains letters it's not a phone
                if any(c.isalpha() for c in val):
                    return val
                redacted = True
                return "[contact redacted]"

            text = phone_regex.sub(_phone_repl, text)

            return text, redacted

        # Default contacts empty
        contacts = []

        # If the LLM returned structured JSON, prefer that and filter contacts
        structured = getattr(response, 'structured', None)
        redaction_note = ""
        if structured and isinstance(structured, dict):
            answer_text = structured.get('answer', response.content)
            # sanitize free-text answer
            sanitized_answer, redacted = sanitize_text(answer_text)
            if redacted:
                redaction_note = "\n\n[Note: One or more contact items were redacted because they could not be verified.]"

            # process contacts array if present
            raw_contacts = structured.get('contacts', []) if isinstance(structured.get('contacts', []), list) else []
            for c in raw_contacts:
                name = c.get('name') if isinstance(c, dict) else None
                email = (c.get('email') if isinstance(c, dict) else None) or ''
                if email and email.lower() in approved_emails:
                    # keep only approved verified contacts
                    contacts.append({'name': name, 'email': email, 'verified': True})
                else:
                    # skip unverified contacts
                    continue

            final_answer = sanitized_answer + redaction_note
        else:
            # No structured response: sanitize raw text
            final_answer, redacted = sanitize_text(response.content)
            if redacted:
                redaction_note = "\n\n[Note: One or more contact items were redacted because they could not be verified.]"
                final_answer = final_answer + redaction_note

        # Prepare response data
        response_data = {
            'answer': final_answer,
            'confidence': response.confidence,
            'sources': [r.metadata.get('source', 'unknown') for r in results[:3]],
            'contacts': contacts,
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
        global enhanced_chatbot
        if not enhanced_chatbot:
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
            response = enhanced_chatbot.chat(query)
            response_data = {
                'answer': response['response'],
                'confidence': response['confidence'],
                'sources': response['sources'][:3],
                'query': query,
                'timestamp': datetime.now().isoformat()
            }
            logger.info(f"Response generated with confidence: {response['confidence']:.2f}")
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
    global llm
    
    if not llm:
        return jsonify({'error': 'Chatbot not initialized'}), 500
    
    try:
        session_id = request.args.get('session_id', 'default')
        history = llm.get_history(session_id)
        return jsonify({
            'session_id': session_id,
            'history': history,
            'count': len(history),
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error getting history: {e}")
        return jsonify({'error': 'Failed to get chat history'}), 500

@app.route('/api/history', methods=['DELETE'])
def clear_history():
    """Clear chat history for a session"""
    global llm

    if not llm:
        return jsonify({'error': 'Chatbot not initialized'}), 500

    try:
        data = request.get_json()
        session_id = data.get('session_id', 'default') if data else 'default'

        llm.clear_history(session_id)
        return jsonify({
            'message': f'Chat history cleared for session: {session_id}',
            'session_id': session_id,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error clearing history: {e}")
        return jsonify({'error': 'Failed to clear chat history'}), 500

@app.route('/api/system_info')
def system_info():
    """Get system information"""
    global vector_store, llm
    
    if not vector_store or not llm:
        return jsonify({'error': 'Chatbot not initialized'}), 500
    
    try:
        # Get basic system info
        info = {
            'status': 'operational',
            'components': {
                'vector_store': 'initialized' if vector_store else 'not_initialized',
                'llm': 'initialized' if llm else 'not_initialized'
            },
            'timestamp': datetime.now().isoformat()
        }
        return jsonify(info)
    except Exception as e:
        logger.error(f"Error getting system info: {e}")
        return jsonify({'error': 'Failed to get system info'}), 500


@app.route('/api/faculty_emails', methods=['GET'])
def faculty_emails():
    """Serve a simple mapping of known faculty names to email addresses to avoid hallucinated contact info."""
    try:
        # Return mapping and verified flags if available
        with open('data/faculty_emails.json', 'r', encoding='utf-8') as f:
            data = json.load(f)

        verified = {}
        try:
            with open('data/faculty_emails_verified.json', 'r', encoding='utf-8') as vf:
                verified = json.load(vf)
        except Exception:
            # If verified file missing or invalid, assume entries are unverified
            verified = {k: False for k in data.keys()}

        # Build response as array of entries for easier consumption by frontend
        entries = []
        for name, email in data.items():
            entries.append({
                'name': name,
                'email': email,
                'verified': bool(verified.get(name, False))
            })
        return jsonify({'entries': entries})
    except Exception as e:
        logger.error(f"Failed to load faculty emails: {e}")
        return jsonify({'entries': []}), 500

@app.route('/health')
def health_check():
    """Health check endpoint"""
    global vector_store, llm
    
    status = 'healthy' if (vector_store is not None and llm is not None) else 'unhealthy'
    return jsonify({
        'status': status,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/georgia_state_panthers_logo.png')
def serve_logo():
    """Serve the GSU logo from the root directory"""
    from flask import send_from_directory
    import os
    return send_from_directory(os.getcwd(), 'georgia_state_panthers_logo.png')

@app.route('/favicon.ico')
def favicon():
    """Serve the favicon"""
    from flask import send_from_directory
    import os
    return send_from_directory(os.getcwd(), 'GSU.png')

@app.route('/favicon-32x32.png')
def favicon_32():
    """Serve 32x32 favicon"""
    from flask import send_from_directory
    import os
    return send_from_directory(os.getcwd(), 'GSU.png')

@app.route('/favicon-16x16.png')
def favicon_16():
    """Serve 16x16 favicon"""
    from flask import send_from_directory
    import os
    return send_from_directory(os.getcwd(), 'GSU.png')

@app.route('/apple-touch-icon.png')
def apple_icon():
    """Serve Apple touch icon"""
    from flask import send_from_directory
    import os
    return send_from_directory(os.getcwd(), 'GSU.png')


# Note: admin scrape endpoint intentionally not exposed. Use the
# `scripts/scrape_directory.py` script manually or schedule it.

if __name__ == '__main__':
    # Initialize chatbot before starting server
    if init_chatbot():
        print("🚀 Starting GSU CS Graduate Program Chatbot Server...")
        print("📝 Access the chat interface at: http://localhost:5000")
        print("🔧 API endpoint available at: http://localhost:5000/api/chat")
        print("📊 System info at: http://localhost:5000/api/system_info")
        print("\n⚠️  Make sure Ollama is running with a model (e.g., 'ollama run mistral:7b')")
        
        app.run(debug=True, host='0.0.0.0', port=5000)
    else:
        print("❌ Failed to initialize chatbot. Please check the logs and try again.")
        print("\n🔧 Troubleshooting:")
        print("1. Make sure Ollama is installed and running")
        print("2. Pull a model: ollama pull mistral:7b")
        print("3. Check if all Python dependencies are installed")