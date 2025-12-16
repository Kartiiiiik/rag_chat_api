from fastapi import APIRouter, Request, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db.dependencies import get_db
from app.core.config import GEMINI_API_KEY
from app.core.limiter import limiter

router = APIRouter(tags=["misc"])


@router.get("/")
@limiter.limit("100/minute")
async def root(request: Request):
    return {
        "message": "RAG Chat API is running",
        "version": "1.0.0",
    }


@router.get("/health")
@limiter.limit("100/minute")
async def health(request: Request, db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False

    return {
        "status": "healthy" if db_ok else "unhealthy",
        "database": "ok" if db_ok else "down",
        "gemini": "configured" if GEMINI_API_KEY else "missing key",
    }


@router.get("/rate-limit-info")
@limiter.limit("10/minute")
async def rate_info(request: Request):
    return {
        "rate_limits": {
            "upload": "10/minute",
            "list": "30/minute",
            "delete": "20/minute",
            "chat": "20/minute",
            "health": "100/minute",
        }
    }
