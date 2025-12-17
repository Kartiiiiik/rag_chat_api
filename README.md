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

## Why Switch to Local Model (Sentence-Transformers) Instead of Gemini?

In our project, we switched from using the **Gemini API** for generating embeddings to a **local model (Sentence-Transformers)** for the following reasons:

1. **Cost Savings**: The Gemini API comes with usage costs that can quickly add up, especially with high traffic. By using **Sentence-Transformers locally**, we avoid paying for each embedding request.

2. **No Rate Limits**: With Gemini, we were limited by **API rate limits** and **daily quotas**. A local model means we can generate embeddings without worrying about limits, ensuring smooth operation at scale.

3. **Improved Speed**: Generating embeddings with a local model is faster since it eliminates the need for external API calls. This improves the overall **performance** of the application.

4. **Better Control and Reliability**: By running **Sentence-Transformers locally**, we reduce our dependency on **external services** (Gemini), making the system more **reliable** and stable.

5. **Scalability**: The local model can be easily scaled to handle larger amounts of data without worrying about **service interruptions** or **API restrictions**.

Overall, switching to a local model helps us maintain better **performance**, **cost efficiency**, and **control** in the long run.
