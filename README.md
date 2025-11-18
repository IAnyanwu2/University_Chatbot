# GSU CS Graduate Program RAG Chatbot

A Retrieval-Augmented Generation (RAG) chatbot designed to answer questions about the Georgia State University Computer Science Graduate Program.

## 🚀 Quick Start (Local Development)

### Prerequisites

1. **Python 3.8+** installed on your system
2. **Ollama** installed and running locally

### Step 1: Install Ollama

**Windows:**
```bash
# Download and install from: https://ollama.ai
# Or using winget:
winget install Ollama.Ollama
```

**After installation, pull a model:**
```bash
ollama pull mistral:7b
# or
ollama pull llama3.1:8b
```

### Step 2: Setup Python Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 3: Run the Chatbot

```bash
# Start the web server
python app.py
```

Visit `http://localhost:5000` in your browser to use the chatbot!

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   User Query    │───▶│   Vector Store  │───▶│      LLM        │
│                 │    │   (ChromaDB)    │    │   (Ollama)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                       │
                                ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Document      │───▶│   Embeddings    │    │   Generated     │
│   Processing    │    │  (SentenceT5)   │    │   Response      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 📁 Project Structure

```
Chatbot/
├── app.py                 # Flask web server
├── rag_chatbot.py        # Main RAG logic
├── vector_store.py       # Vector database handling
├── llm_interface.py      # Ollama LLM interface
├── document_processor.py # Document ingestion
├── requirements.txt      # Python dependencies
├── templates/
│   └── index.html        # Web chat interface
└── README.md            # This file
```

## 🔧 Components

### 1. Vector Store (`vector_store.py`)
- **ChromaDB** for local vector storage
- **SentenceTransformers** for embeddings (all-MiniLM-L6-v2)
- Document chunking and similarity search

### 2. LLM Interface (`llm_interface.py`)
- **Ollama** integration for local LLM inference
- Supports Mistral 7B, Llama 3.1, and other models
- Confidence scoring and hallucination detection

### 3. Document Processing (`document_processor.py`)
- Sample GSU CS program data included
- Support for PDF, DOCX, and text files
- Web scraping capabilities (BeautifulSoup)

### 4. RAG Orchestration (`rag_chatbot.py`)
- Query classification (personal/off-topic filtering)
- Context retrieval and response generation
- Confidence thresholding and fallback handling

### 5. Web Interface (`app.py` + `templates/`)
- **Flask** backend with REST API
- Interactive chat interface
- Real-time system status monitoring

## 🛡️ Built-in Safeguards

1. **Personal Query Detection**: Redirects personal questions to appropriate contacts
2. **Off-topic Filtering**: Keeps conversations focused on CS graduate program
3. **Confidence Thresholding**: Provides fallback responses for low-confidence answers
4. **Source Attribution**: Shows which documents informed each answer

## 🧪 Testing the System

The system includes sample data covering:
- ✅ Admission requirements and deadlines
- ✅ Course curriculum and requirements
- ✅ Research areas and faculty
- ✅ Financial aid and assistantships
- ✅ Student services and resources
- ✅ Frequently asked questions

**Try these sample queries:**
- "What are the GRE requirements for international students?"
- "Tell me about the research areas in AI and machine learning"
- "How can I get a teaching assistantship?"
- "What courses are required for the MS program?"

## 📈 Next Steps for Production

### Phase 1: Enhanced Data Collection
- [ ] Web scraping of official GSU CS website
- [ ] PDF processing of official program documents
- [ ] Email archive integration (with PII redaction)
- [ ] Regular data updates via cron jobs

### Phase 2: Model Optimization
- [ ] Fine-tuning on domain-specific data
- [ ] Implement active learning feedback loop
- [ ] A/B testing different embedding models
- [ ] Response quality metrics

### Phase 3: Production Deployment
- [ ] Docker containerization
- [ ] GPU server deployment (vector.cs.gsu.edu)
- [ ] Authentication and authorization
- [ ] Monitoring and logging
- [ ] User feedback collection

### Phase 4: Advanced Features
- [ ] Knowledge graph integration (Neo4j)
- [ ] Multi-modal support (images, videos)
- [ ] Real-time chat with human handoff
- [ ] Analytics dashboard

## 🔧 Configuration Options

Edit `rag_chatbot.py` to customize:

```python
# Vector store settings
VectorStore(
    collection_name="gsu_cs_knowledge",
    model_name="all-MiniLM-L6-v2",  # Embedding model
    persist_directory="./chroma_db"
)

# LLM settings
OllamaLLM(
    model_name="mistral:7b",        # Ollama model
    temperature=0.1,               # Creativity (0.0-1.0)
    max_tokens=512                # Response length
)

# Chatbot settings
RAGChatbot(
    min_confidence_threshold=0.3,  # Minimum confidence
    max_retrieved_chunks=5         # Context window size
)
```

## 🐛 Troubleshooting

**Ollama not connecting?**
- Ensure Ollama is running: `ollama serve`
- Check available models: `ollama list`
- Pull required model: `ollama pull mistral:7b`

**Dependencies not installing?**
- Upgrade pip: `python -m pip install --upgrade pip`
- Use virtual environment
- Check Python version (3.8+ required)

**Web interface not loading?**
- Check Flask is running on port 5000
- Verify templates directory exists
- Check browser console for JavaScript errors

## 📊 Performance Notes

**Local Development:**
- First query may be slow (model loading)
- Embedding generation: ~100ms per query
- LLM inference: 1-5 seconds (depending on model/hardware)

**Recommended Hardware:**
- 8GB+ RAM for embedding models
- 16GB+ RAM for larger LLMs (Llama 13B+)
- GPU optional but significantly improves performance

## 📞 Support

For questions about this implementation:
- Check the troubleshooting section above
- Review Ollama documentation: https://ollama.ai/docs
- Check ChromaDB documentation: https://docs.trychroma.com/