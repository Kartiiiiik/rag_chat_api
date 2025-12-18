# RAG Chat API

A production-grade RAG (Retrieval Augmented Generation) application featuring:
- **Frontend**: React + Vite + Shadcn/UI (Dockerized with Nginx)
- **Backend**: FastAPI + Python (Dockerized)
- **Database**: PostgreSQL with `pgvector` for vector embeddings
- **Authentication**: Secure JWT-based login and signup system

## Features
- **Document Management**: Upload and index PDF/Word/Text documents.
- **RAG Chat**: Intelligent chat interface using indexed documents for context.
- **Secure Auth**: Production-grade authentication with password hashing and JWT.
- **Local Embeddings**: High-performance local embedding generation using `sentence-transformers`.

## Prerequisites
- Docker & Docker Compose
- Node.js 18+ (for local development)
- [uv](https://docs.astral.sh/uv/) (recommended for backend development)

## Quick Start (Docker)

1. **Build and Run**:
   ```bash
   make build
   make up
   ```
   Or using docker-compose directly:
   ```bash
   docker-compose up --build -d
   ```

2. **Access the Application**:
   - Frontend: [http://localhost](http://localhost)
   - API Docs: [http://localhost:8000/docs](http://localhost:8000/docs)

3. **Stop**:
   ```bash
   make down
   ```

## Development

### Backend
1. Navigate to `backend/`.
2. Configure environment:
   ```bash
   cp .env.example .env
   # Add your GEMINI_API_KEY and SECRET_KEY
   ```
3. Sync dependencies and run:
   ```bash
   uv sync
   uv run run.py
   ```

### Frontend
1. Navigate to `frontend/`.
2. `npm install`.
3. `npm run dev`.
   - Accessible at `http://localhost:8080`.
   - API requests are directed to `http://localhost:8000` (or as configured in `api.ts`).

## Environment Variables

### Backend (`backend/.env`)
- `DATABASE_URL`: PostgreSQL connection string.
- `GEMINI_API_KEY`: API key for chat completion.
- `SECRET_KEY`: Long random string for JWT signing.

## Architecture
- **Nginx**: Serves the React app and proxies requests.
- **FastAPI**: Handles document processing, vector search, and authentication.
- **PostgreSQL**: Stores users, document metadata, and `pgvector` embeddings.
- **Sentence-Transformers**: Local model (`all-MiniLM-L6-v2`) used for generating embeddings.

## Why Switch to Local Model (Sentence-Transformers)?

We switched from using the **Gemini API** for embeddings to a **local model** for:
1. **Cost Savings**: $0 per embedding.
2. **No Rate Limits**: No daily quotas or API restrictions.
3. **Speed**: Eliminates network latency for embedding generation.
4. **Reliability**: No dependency on external API availability.
5. **Scalability**: Easily scale processing without service interruptions.
