# PsyWiz Backend Documentation

## Overview

**PsyWiz** is a production-ready Retrieval-Augmented Generation (RAG) system designed for medical research papers. The backend leverages FastAPI to provide a high-performance REST API that processes research documents, creates semantic embeddings, and generates intelligent responses to user queries using advanced Large Language Models (LLMs).

## Features

- **Semantic Search**: Efficiently retrieves relevant research papers based on user queries.
- **Document Processing**: Supports uploading, listing, and deleting research documents.
- **Health Monitoring**: Provides endpoints for system health checks and model status.
- **Caching Mechanism**: Utilizes local model caching for improved performance and offline capabilities.

## Technology Stack

- **API Framework**: FastAPI
- **Embeddings**: Sentence-transformers
- **Vector Database**: ChromaDB
- **LLM**: Google Gemini API
- **Containerization**: Docker

## Directory Structure

The project is organized as follows:

```
psywiz-backend/
├── app/                     # Main application code
│   ├── __init__.py
│   ├── main.py              # FastAPI app entry point
│   ├── config.py           # Configuration management
│   ├── dependencies.py      # Shared dependencies
│   ├── api/                 # API layer
│   │   ├── __init__.py
│   │   ├── endpoints/       # API endpoints
│   │   │   ├── __init__.py
│   │   │   ├── rag.py
│   │   │   ├── documents.py
│   │   │   └── health.py
│   │   └── deps.py
│   ├── core/                # Business logic
│   │   ├── __init__.py
│   │   ├── rag_engine.py
│   │   ├── vector_db.py
│   │   ├── chunking.py
│   │   ├── pdf_processor.py
│   │   ├── scraper.py
│   │   └── embeddings.py
│   ├── models/              # Data schemas
│   │   ├── __init__.py
│   │   ├── requests.py
│   │   └── responses.py
│   └── utils/               # Utility functions
│       ├── __init__.py
│       └── helpers.py
├── model_cache/             # Local model storage
│   └── embeddings/
├── requirements.txt         # Project dependencies
├── requirements-dev.txt     # Development dependencies
├── Dockerfile               # Production container setup
├── docker-compose.yml       # Local development configuration
├── .env.example             # Environment variable template
├── run.py                   # Application runner
└── README.md                # Project documentation
```

## Getting Started

### Prerequisites

- Python 3.11 or higher
- Docker (for containerized deployment)

### Installation

1. Clone the repository:
   ```
   git clone <repository-url>
   cd psywiz-backend
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

### Running the Application

- **Development Mode**:
  ```
  python -m uvicorn app.main:app --reload
  ```

- **Production Mode**:
  ```
  docker-compose up --build
  ```

## Contributing

Contributions are welcome! Please submit a pull request or open an issue for any enhancements or bug fixes.

## License

This project is licensed under the MIT License. See the LICENSE file for details.