# RAG Chat API

A full-stack RAG (Retrieval Augmented Generation) application featuring:
- **Frontend**: React + Vite + Shadcn/UI (Dockerized with Nginx)
- **Backend**: FastAPI + Python (Dockerized)
- **Database**: PostgreSQL with `pgvector` for vector embeddings

## Prerequisites
- Docker & Docker Compose
- Node.js 18+ (for local development)
- Python 3.11+ (for local development)

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
2. Create virtual environment and install dependencies.
3. Run with `uvicorn app.main:app --reload`.

### Frontend
1. Navigate to `frontend/`.
2. `npm install`.
3. `npm run dev`.
   - Accessible at `http://localhost:8080`.
   - API requests are proxied to `http://localhost:8000`.

## Architecture
- **Nginx** serves the statically built React app and proxies `/api` requests to the FastAPI backend.
- **FastAPI** handles document upload, chunking (with `pgvector`), and chat generation.
- **PostgreSQL** stores document metadata and vector embeddings.
