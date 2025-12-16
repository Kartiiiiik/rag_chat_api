from fastapi import FastAPI
from app.core.middleware import add_cors_middleware
from app.core.limiter import limiter
from app.api.v1.router_documents import router as documents_router
from app.api.v1.router_chat import router as chat_router
from app.api.v1.router_misc import router as misc_router
from slowapi.errors import RateLimitExceeded
from fastapi.responses import JSONResponse

app = FastAPI(title="RAG Chat API", version="1.0.0")

# Middleware
add_cors_middleware(app)

# Rate limiter exception handler
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, lambda req, exc: JSONResponse(status_code=429, content={"detail": "Rate limit exceeded"}))

# Routers
app.include_router(misc_router)
app.include_router(documents_router)
app.include_router(chat_router)
