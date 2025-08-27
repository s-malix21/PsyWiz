# PsyWiz Backend

A production-ready **RAG (Retrieval-Augmented Generation)** system for medical research papers, built with FastAPI, ChromaDB, and Google Gemini.

## 🚀 Features

- **🧠 Intelligent Q&A**: Ask questions about medical research and get AI-powered answers
- **📄 Document Management**: Upload, process, and manage research papers  
- **🔍 Semantic Search**: Find relevant papers using advanced embedding techniques
- **⚡ High Performance**: FastAPI with async support and optimized embeddings
- **🐳 Docker Ready**: Complete containerization with docker-compose
- **📊 Health Monitoring**: Comprehensive system health and status monitoring
- **🔒 Production Ready**: Proper error handling, logging, and security

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   FastAPI       │    │   ChromaDB      │
│   (React/Vue)   │◄──►│   Backend       │◄──►│   Vector DB     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │  Google Gemini  │
                       │      LLM        │
                       └─────────────────┘
```

### Core Components

- **FastAPI**: High-performance async API framework
- **ChromaDB**: Vector database for semantic search
- **sentence-transformers**: Local embedding model (`all-MiniLM-L6-v2`)
- **Google Gemini**: Large Language Model for answer generation
- **Docker**: Containerization and deployment

## 📋 Prerequisites

- **Python 3.11+**
- **Docker & Docker Compose** (recommended)
- **Google AI Studio API Key** ([Get one here](https://makersuite.google.com/app/apikey))

## 🛠️ Installation

### Option 1: Docker (Recommended)

1. **Clone and setup**:
   ```bash
   cd psywiz-backend
   cp .env.example .env
   ```

2. **Configure environment** (edit `.env`):
   ```bash
   GEMINI_API_KEY=your_google_ai_studio_api_key_here
   ```

3. **Start the application**:
   ```bash
   docker-compose up -d
   ```

4. **Access the API**:
   - API: http://localhost:8000
   - Documentation: http://localhost:8000/docs
   - Health: http://localhost:8000/health

### Option 2: Local Development

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

3. **Run the server**:
   ```bash
   python run.py
   # or for development:
   python run.py --reload
   ```

## 🧪 Quick Start

### 1. Upload a Document

```bash
curl -X POST "http://localhost:8000/documents/upload" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Sample Research Paper",
    "content": "This is the content of a medical research paper...",
    "source": "journal_name.pdf",
    "authors": ["Dr. Smith", "Dr. Johnson"]
  }'
```

### 2. Ask a Question

```bash
curl -X POST "http://localhost:8000/rag/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What are the main findings about treatment effectiveness?",
    "include_sources": true
  }'
```

### 3. Check System Health

```bash
curl http://localhost:8000/health/detailed
```

## 📚 API Documentation

### Main Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/rag/ask` | POST | Ask questions about research papers |
| `/rag/status` | GET | Get RAG system status |
| `/documents/upload` | POST | Upload and process documents |
| `/documents/search` | POST | Search documents semantically |
| `/health/` | GET | Basic health check |
| `/health/detailed` | GET | Comprehensive system status |

### Interactive Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🔧 Configuration

Key configuration options in `.env`:

```bash
# API Keys
GEMINI_API_KEY=your_key_here

# Model Configuration
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
MODEL_CACHE_PATH=./model_cache

# RAG Parameters
CHUNK_SIZE=512
CHUNK_OVERLAP=50
TOP_K_RETRIEVAL=5
SIMILARITY_THRESHOLD=0.7

# Server Configuration
HOST=0.0.0.0
PORT=8000
DEBUG=false
LOG_LEVEL=INFO
```

## 📊 Monitoring

### Health Endpoints

- `/health/` - Basic health check
- `/health/detailed` - Comprehensive status
- `/health/embedding` - Embedding model status
- `/health/database` - Vector database status
- `/health/ready` - Container readiness check

### Logging

Structured logging with different levels:
- **INFO**: General operations
- **WARNING**: Non-critical issues  
- **ERROR**: Error conditions
- **DEBUG**: Detailed debugging info

## 🐳 Docker Configuration

### Services

- **psywiz-backend**: Main FastAPI application
- **nginx**: Reverse proxy (optional, with `--profile with-nginx`)
- **prometheus**: Monitoring (optional, with `--profile with-monitoring`)

### Volumes

- `model_cache`: Persistent embedding model storage
- `vector_db`: Persistent vector database
- `logs`: Application logs

### Resource Limits

- **Memory**: 4GB limit, 2GB reservation
- **CPU**: 2.0 cores limit, 1.0 core reservation

## 🔒 Security

- **CORS**: Configurable origins
- **Rate Limiting**: Built-in request throttling
- **Input Validation**: Pydantic model validation
- **Error Handling**: Sanitized error responses
- **Container Security**: Non-root user execution

## 🚀 Production Deployment

### 1. Environment Setup

```bash
# Production environment variables
DEBUG=false
LOG_LEVEL=INFO
ALLOWED_ORIGINS=["https://yourdomain.com"]
```

### 2. Docker Production Build

```bash
docker-compose -f docker-compose.yml --profile production up -d
```

### 3. Reverse Proxy (Nginx)

```bash
docker-compose --profile with-nginx up -d
```

### 4. Monitoring

```bash
docker-compose --profile with-monitoring up -d
```

## 📈 Performance

### Optimization Features

- **Model Caching**: Embedding models cached locally
- **Singleton Pattern**: Single model instance across requests
- **Async Processing**: FastAPI async support
- **Batch Processing**: Efficient batch embedding generation
- **Connection Pooling**: Optimized database connections

### Benchmarks

- **Cold Start**: ~30-60 seconds (model loading)
- **Query Response**: ~1-3 seconds (typical)
- **Document Upload**: ~2-5 seconds per document
- **Memory Usage**: ~2-4GB (including models)

## 🛠️ Development

### Setup Development Environment

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run with auto-reload
python run.py --reload

# Run tests
pytest

# Code formatting
black app/
isort app/

# Type checking
mypy app/
```

### Project Structure

```
psywiz-backend/
├── app/
│   ├── api/endpoints/     # API route handlers
│   ├── core/             # Business logic
│   ├── models/           # Pydantic models
│   └── utils/            # Utility functions
├── model_cache/          # Cached models
├── vector_db/           # Vector database storage
├── requirements.txt      # Dependencies
├── Dockerfile           # Container configuration
└── docker-compose.yml   # Multi-service setup
```

## 🐛 Troubleshooting

### Common Issues

1. **Model Download Fails**
   ```bash
   # Check internet connection and retry
   docker-compose restart psywiz-backend
   ```

2. **API Key Errors**
   ```bash
   # Verify API key in .env
   echo $GEMINI_API_KEY
   ```

3. **Memory Issues**
   ```bash
   # Increase Docker memory limit to 4GB+
   # Check Docker Desktop settings
   ```

4. **Port Conflicts**
   ```bash
   # Change port in docker-compose.yml
   ports:
     - "8001:8000"  # Use different host port
   ```

### Logs

```bash
# View application logs
docker-compose logs -f psywiz-backend

# View specific service logs
docker-compose logs nginx
docker-compose logs prometheus
```

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📞 Support

- **Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

---

**Built with ❤️ for medical research and AI-powered knowledge discovery.**