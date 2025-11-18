# GSU CS Graduate Program RAG Chatbot - System Architecture

## Overview
A production-ready Retrieval-Augmented Generation (RAG) chatbot system built with Flask, using local Ollama models and real-time web scraping of GSU Computer Science department data.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                               USER INTERFACE LAYER                              │
├─────────────────────────────────────────────────────────────────────────────────┤
│  Web Browser (localhost:5000)                                                  │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐            │
│  │   Chat UI       │    │   Health Check  │    │  System Info    │            │
│  │   (index.html)  │    │   (/health)     │    │  (/api/system)  │            │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘            │
└─────────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              FLASK WEB SERVER                                  │
├─────────────────────────────────────────────────────────────────────────────────┤
│  Flask Application (app.py)                                                    │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐            │
│  │   Route: /      │    │  Route: /health │    │ Route: /api/chat│            │
│  │   (UI Handler)  │    │  (Status Check) │    │ (Main Endpoint) │            │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘            │
│                                    │                      │                     │
│  Global Components:                │                      │                     │
│  • vector_store (LightweightVectorStore)                 │                     │
│  • llm (CloudLLM)                                        │                     │
│  • init_chatbot() initialization                         │                     │
└─────────────────────────────────────────────────────────┼─────────────────────┘
                                    │                      │
                                    ▼                      ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              RAG PIPELINE LAYER                                │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────────┐│
│  │                        DOCUMENT PROCESSING                                  ││
│  │  DocumentProcessor (document_processor.py)                                 ││
│  │  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐        ││
│  │  │ Web Scraping    │    │ Cache Manager   │    │ File Processors │        ││
│  │  │ • GSU URLs (5)  │    │ • 24hr TTL      │    │ • PDF Support   │        ││
│  │  │ • BeautifulSoup │    │ • Pickle Cache  │    │ • DOCX Support  │        ││
│  │  │ • Error Handling│    │ • Smart Refresh │    │ • Text Files    │        ││
│  │  └─────────────────┘    └─────────────────┘    └─────────────────┘        ││
│  └─────────────────────────────────────────────────────────────────────────────┘│
│                                    │                                            │
│                                    ▼                                            │
│  ┌─────────────────────────────────────────────────────────────────────────────┐│
│  │                         VECTOR STORAGE                                      ││
│  │  LightweightVectorStore (lightweight_vector_store.py)                      ││
│  │  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐        ││
│  │  │ TF-IDF Vectors  │    │ Similarity      │    │ Document Store  │        ││
│  │  │ • Scikit-learn  │    │ • Cosine Sim    │    │ • In-Memory     │        ││
│  │  │ • No GPU needed │    │ • Confidence    │    │ • Fast Access   │        ││
│  │  │ • Lightweight   │    │ • Score Ranking │    │ • Chunked Data  │        ││
│  │  └─────────────────┘    └─────────────────┘    └─────────────────┘        ││
│  └─────────────────────────────────────────────────────────────────────────────┘│
│                                    │                                            │
│                                    ▼                                            │
│  ┌─────────────────────────────────────────────────────────────────────────────┐│
│  │                          LLM INTEGRATION                                    ││
│  │  CloudLLM (cloud_llm.py)                                                   ││
│  │  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐        ││
│  │  │ Ollama Client   │    │ Response Clean  │    │ Context Process │        ││
│  │  │ • Local Model   │    │ • Markdown Fix  │    │ • Smart Extract │        ││
│  │  │ • HTTP API      │    │ • Format Clean  │    │ • Content Filter│        ││
│  │  │ • 30s Timeout   │    │ • Spacing Fix   │    │ • Faculty Info  │        ││
│  │  └─────────────────┘    └─────────────────┘    └─────────────────┘        ││
│  └─────────────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                            EXTERNAL DEPENDENCIES                               │
├─────────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐            │
│  │ Ollama Server   │    │ GSU Websites    │    │ Local Storage   │            │
│  │ • localhost:11434│    │ • 5 Verified   │    │ • Cache Files   │            │
│  │ • gpt-oss:120b  │    │ • Real-time     │    │ • Data Dir      │            │
│  │ • Local Model   │    │ • Updated Info  │    │ • Metadata      │            │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘            │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## Data Flow

### 1. **Initialization Flow**
```
Start → DocumentProcessor → Check Cache → [Valid?] 
                                         ├─ Yes → Load Cache
                                         └─ No  → Scrape GSU → Save Cache
                          → VectorStore → Add Documents → TF-IDF Index
                          → CloudLLM → Test Ollama Connection → Ready
```

### 2. **Query Processing Flow**
```
User Query → Flask Route → VectorStore.similarity_search() 
                        → Get Top Relevant Chunks + Confidence Scores
                        → CloudLLM.generate_response()
                        → Context + Query → Ollama Model
                        → Raw Response → Clean Formatting
                        → Return JSON → Display in UI
```

### 3. **Caching Strategy**
```
First Run:    Scrape → Process → Cache (24h TTL) → Store
Subsequent:   Check Cache → [Expired?] → Load Cache OR Re-scrape
Manual:       force_refresh_cache() → Always Scrape → Update Cache
```

## Component Details

### Core Files
- **app.py**: Flask web server, routing, global state management
- **document_processor.py**: Web scraping, caching, document loading
- **lightweight_vector_store.py**: TF-IDF vectorization, similarity search
- **cloud_llm.py**: Ollama integration, response generation, formatting
- **simple_langchain.py**: Document abstraction layer

### Data Sources
- **GSU Websites**: 5 verified URLs for CS graduate program info
- **Local Files**: PDF/DOCX support in ./data directory
- **Cache**: Pickle files with 24-hour TTL

### Configuration
- **Model**: gpt-oss:120b-cloud (116.8B params, MXFP4 quantized)
- **Cache TTL**: 24 hours
- **Timeout**: 30 seconds for Ollama requests
- **Port**: 5000 (Flask server)

## Key Features

### ✅ **Production Ready**
- Error handling and fallbacks
- Health monitoring endpoints
- Caching for performance
- Clean, professional UI

### ✅ **Privacy Focused**
- Local Ollama model (no cloud APIs)
- No external API keys required
- Data stays on local machine

### ✅ **Scalable Architecture**
- Modular component design
- Easy to add new data sources
- Configurable caching strategy
- RESTful API design

### ✅ **Real Data Integration**
- Live GSU website scraping
- Verified URL endpoints
- Smart content extraction
- Automatic updates

## Performance Characteristics

### Startup Time
- **First Run**: 5-10 seconds (scraping + processing)
- **Cached Run**: 1-2 seconds (load from cache)
- **Model Loading**: Handled by Ollama (pre-loaded) -

### Query Response
- **Vector Search**: <100ms (TF-IDF is fast)
- **LLM Generation**: 2-5 seconds (depends on model)
- **Total Response**: 2-6 seconds end-to-end

### Memory Usage
- **Vector Store**: ~10-50MB (depends on document size)
- **Cache Files**: ~1-5MB (compressed)
- **Model**: Handled by Ollama (external process)