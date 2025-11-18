# 🚀 GSU CS RAG Chatbot - Setup Instructions

## Current Status ✅
- ✅ Virtual environment configured
- ✅ All Python dependencies installed
- ✅ Vector database working
- ✅ Document processing working
- ✅ RAG pipeline functional
- ⚠️ Need to install Ollama for LLM

## 🔧 Setting Up Ollama (Local LLM)

### Option 1: Automatic Installation (Recommended)
1. **Run the downloaded installer:**
   ```powershell
   .\ollama-windows-amd64.exe
   ```
   - Follow the installation wizard
   - This will install Ollama and start the service

### Option 2: Manual Installation
1. **Download from website:** Visit https://ollama.com/download
2. **Install the Windows version**
3. **Ollama will automatically start as a service**

### 🤖 Downloading a Model
After Ollama is installed, download a model:
```powershell
# Option A: Mistral 7B (Recommended - good balance of quality/speed)
ollama pull mistral:7b

# Option B: Llama 3.1 8B (Alternative)  
ollama pull llama3.1:8b

# Option C: Gemma 7B (Google's model)
ollama pull gemma:7b
```

### 🧪 Testing the Setup
Once Ollama is installed and a model is downloaded:
```powershell
# Activate virtual environment
.\venv\Scripts\activate

# Test the complete system
python test_system.py

# Start the web interface
python app.py
```

## 🌐 Using the Chatbot

### Web Interface
After running `python app.py`, open your browser to:
- **Local:** http://localhost:5000
- Test queries like:
  - "What are the GRE requirements for international students?"
  - "How much does the program cost?"
  - "What research areas are available?"

### Command Line
You can also test directly in Python:
```python
from rag_chatbot import RAGChatbot

chatbot = RAGChatbot()
response = chatbot.chat("What are the admission requirements?")
print(response.content)
```

## 📊 Current Test Results
```
============================================================
📊 Test Results: 3/4 tests passed
⚠️  Only missing: Ollama LLM connection
============================================================
```

## 🔧 Troubleshooting

### If Ollama won't start:
```powershell
# Check if Ollama service is running
ollama list

# Start Ollama manually if needed  
ollama serve
```

### If models are slow:
- Mistral 7B: ~4GB RAM, good for most queries
- For faster responses: `ollama pull phi3:mini` (smaller model)
- For better quality: `ollama pull llama3.1:8b` (needs more RAM)

### If getting errors:
```powershell
# Reinstall packages in virtual environment
.\venv\Scripts\pip install -r requirements.txt

# Check Python environment
python --version
```

## 🎯 Next Development Steps

1. **✅ Local Proof of Concept** ← We are here!
2. **🔄 Add more GSU-specific documents**
3. **🔍 Implement web scraping for live GSU data** 
4. **🛡️ Add security features (PII redaction)**
5. **📈 Add user feedback and learning**
6. **🌐 Deploy to university servers**

## 📁 Project Structure
```
Chatbot/
├── 📄 app.py              # Flask web server
├── 🧠 rag_chatbot.py      # Main RAG orchestration  
├── 💾 vector_store.py     # ChromaDB vector database
├── 🤖 llm_interface.py    # Ollama LLM interface
├── 📚 document_processor.py # Document loading & processing
├── 🧪 test_system.py      # System testing
├── 🌐 templates/index.html # Web UI
├── 📋 requirements.txt    # Python dependencies
└── 🚀 setup_instructions.md # This file
```

**Ready to test once Ollama is installed! 🎉**