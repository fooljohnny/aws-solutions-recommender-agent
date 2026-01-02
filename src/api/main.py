"""FastAPI main application with automatic OpenAPI schema generation."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import conversations, messages, health
from .middleware.error_handler import error_handler
from .middleware.rate_limiter import RateLimitMiddleware

app = FastAPI(
    title="AWS Solution Architecture Recommendation Agent API",
    version="1.0.0",
    description="REST API for AWS Solution Architecture Recommendation Agent",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting middleware
app.add_middleware(RateLimitMiddleware)

# Error handling middleware
app.middleware("http")(error_handler)

# Include routers
app.include_router(health.router)
app.include_router(conversations.router, prefix="/v1")
app.include_router(messages.router, prefix="/v1")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "AWS Solution Architecture Recommendation Agent API",
        "version": "1.0.0",
    }

