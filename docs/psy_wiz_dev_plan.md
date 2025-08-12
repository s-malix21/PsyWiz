# PsyWiz — Development Roadmap and Tech Plan

**Short description**

PsyWiz is a full-stack AI assistant for exploring and querying medical research papers using a Retrieval-Augmented Generation (RAG) architecture. The system ingests research documents, preprocesses and indexes them, provides semantic search via a vector database, and generates natural language answers with citations. The objective is a top-tier quality product built with zero monetary cost at the start (self-hosted/local-first), suitable for a technical ML engineer to implement and extend.

---

## Goals

- Deliver accurate, reference-backed answers to medical research queries.
- Support document browsing and source transparency.
- Start with zero-dollar infrastructure (local dev / free tiers) and maintain a clear upgrade path to production-grade components.

---

## Repository layout

```
psywiz/
├── backend/        # FastAPI app, RAG pipeline endpoints
├── ingest/         # Scrapers, parsers, ingestion pipelines
├── vector/         # Indexing scripts and vector DB adapters
├── models/         # LLM server glue, quantization scripts
├── frontend/       # Next.js app: chat UI, doc browser, uploader
├── infra/          # docker-compose, deployment configs
└── docs/           # design notes, data schema, policies
```

---

## Phase 0 — Principles & Initial Setup (1 day)

- Initialize the repo and project structure as above.
- Choose the orchestration library: pick **LangChain** or **LlamaIndex** and standardize on it.
- Establish coding standards, CI basics, and a reproducible local environment (Docker Compose + Python virtualenv).

---

## Phase 1 — MVP (local, $0) — 1–2 weeks

### 1) Document ingestion & processing

- Tools: `requests` / `scrapy` for crawling; `PyMuPDF` or `pdfminer.six` for text extraction. Use **Grobid** or **Unstructured/Docling** for richer structure (title, abstract, sections, references) when PDFs are complex.
- Produce: cleaned text + metadata JSON per paper (title, authors, year, DOI, source link).
- Normalization: strip headers/footers, normalize whitespace, retain section boundaries. Tag each chunk with source metadata.

### 2) Chunking & embeddings

- Chunk strategy: ~500 tokens per chunk with 50–100 token overlap.
- Embedding model: `sentence-transformers/all-MiniLM-L6-v2` for CPU-friendly, high-throughput local inference.
- Pipeline: batch-encode chunks and persist (text, metadata, embedding).

### 3) Vector DB (local)

- Use **Chroma** in local mode for development (file-based persistence). Store entries as (chunk_id, text, metadata, embedding).

### 4) Retrieval & generation (RAG)

- Orchestrator: LangChain or LlamaIndex chains.
- Retrieval: embed query with same embedder → nearest-neighbor search in Chroma → retrieve top-k chunks (k=4–8).
- Prompt assembly: contextual prompt composed of retrieved chunks + user question, with explicit instructions to cite sources by metadata.
- LLM: self-host a quantized open model (Mistral 7B or LLama 7B/13B depending on hardware) using `llama.cpp`/`ggml` or `text-generation-inference`.
- Response: return generated text plus a structured list of source snippets and metadata.

### 5) Backend & frontend

- Backend: **FastAPI** exposing `/api/ask`, `/api/docs`, `/api/upload`, and job endpoints for ingestion.
- Frontend: **Next.js** chat UI, documents list, PDF preview, and link to source metadata.
- Auth & storage (dev): optional use of Supabase free tier for file hosting and metadata (1 GB free). Otherwise use local FS and Postgres for metadata.

---

## Phase 2 — Hardening & Features (2–4 weeks)

- Add citation formatting and an interface to view source context for each answer.
- Maintain conversational context: store prior turns with retrieval-augmented history.
- Safety and compliance: add a medical disclaimer, query filters, and logging for audit.
- Re-ranking: apply a cross-encoder re-ranker or short LLM re-score on top-k retrieval results to improve precision.
- Monitoring and tests: unit tests for ingestion, integration tests for RAG responses, and evaluation scripts for recall/precision of retrieval.

---

## Phase 3 — Scale & Production (when required)

- Vector DB upgrade: move from Chroma to **Milvus** (or Weaviate) for large-scale vector storage, sharding, and higher QPS.
- LLM hosting: evaluate hosting options or leased GPU VMs; consider hybrid inference (small local LLM for most queries and a higher-quality remote model for complex requests).
- Orchestration: transition from Docker Compose to Kubernetes for reliability and autoscaling.
- CI/CD: GitHub Actions to run tests and build containers; deployment pipelines for backend and model services.
- Observability: add metrics for latency, error rates, retrieval hit-rate, and auditing logs (Sentry + Prometheus/Grafana).

---

## Concrete tech stack (MVP → Scale)

- RAG orchestration: **LangChain** or **LlamaIndex**
- Document parsing: **Grobid**, **Unstructured**, **PyMuPDF** / **pdfminer.six**
- Embeddings: **sentence-transformers/all-MiniLM-L6-v2**
- Vector DB (dev): **Chroma**; (scale): **Milvus**
- LLM: open-source models (Mistral 7B, Llama family); quantize with `ggml`/`gguf` and serve via `llama.cpp` or `text-generation-inference`
- Backend: **FastAPI** (Python)
- Frontend: **Next.js** (React)
- File hosting & metadata: **Supabase** (free tier) or local Postgres
- Orchestration: Docker Compose for dev, Kubernetes for production
- Caching: Redis for query/embedding cache

---

## Minimal runnable checklist

1. `git init psywiz && cd psywiz`
2. Create a Python virtualenv and install core packages:
   - `pip install fastapi uvicorn langchain sentence-transformers chromadb pymupdf`
3. Implement `ingest.py` to extract text from PDFs, chunk, embed, and upsert into Chroma.
4. Implement `api.py` (FastAPI): `/ask` endpoint that embeds query, queries Chroma, assembles prompt, calls local LLM server, and returns `{ answer, sources }`.
5. Create a minimal Next.js frontend to POST queries to `/ask` and render responses and sources.
6. Populate a demo corpus of ~10–50 sample papers and validate retrieval+generation quality.

---

## Cost-saving & operational tips

- Keep everything local until usage or corpus size dictates otherwise.
- Use CPU-friendly embedding models and small/quantized LLMs to avoid cloud GPU costs.
- Store raw files in Supabase free tier (1 GB) during prototyping to avoid managing S3.
- Cache embeddings and avoid re-embedding unchanged documents.
- Use scheduled ingestion (cron/Celery beat) and incremental updates to reduce compute load.

---

## Evaluation and quality control

- Track retrieval recall: verify that ground-truth passages are present in top-k retrieval (top-5 recommended).
- Measure answer faithfulness: add a script that validates whether generated claims are linked to retrieved sources.
- Collect user feedback and build a triage pipeline to flag hallucinations and adjust chunking/reranking strategies.

---

## References & further reading

- LangChain and LlamaIndex documentation for RAG patterns and chains.
- Grobid and Unstructured for scientific PDF processing.
- Chroma quickstart for local vector DB usage and Milvus for production-scale vector storage.

---

## Notes

- The architecture is designed for rapid iteration and high-quality results with zero initial spend by relying on open-source tooling and local infrastructure. The stack and components are selected to mirror patterns used in widely adopted RAG projects and production deployments.

