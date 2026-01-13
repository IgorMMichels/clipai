"""
ClipAI Backend - FastAPI Application
AI-powered video clipping tool
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import logging

from config import settings
from api.routes import upload_router, clips_router


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    logger.info("Starting ClipAI Backend...")
    logger.info(f"Upload directory: {settings.UPLOAD_DIR}")
    logger.info(f"Output directory: {settings.OUTPUT_DIR}")
    yield
    logger.info("Shutting down ClipAI Backend...")


# Create FastAPI app
app = FastAPI(
    title="ClipAI",
    description="AI-powered video clipping tool. Transform long videos into viral clips.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files for outputs
app.mount("/outputs", StaticFiles(directory=str(settings.OUTPUT_DIR)), name="outputs")

# Include routers
app.include_router(upload_router, prefix="/api")
app.include_router(clips_router, prefix="/api")


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "name": "ClipAI",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
    }


@app.get("/api/health")
async def health():
    """Health check for API"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
    )
