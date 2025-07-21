"""
Main FastAPI application for Triple Network AI Comparison System.
Entry point for the backend service.
"""
import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from .api.routes import router
from .api.websocket import websocket_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('simulation.log')
    ]
)

logger = logging.getLogger("main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("Starting Triple Network AI Comparison System...")
    
    # Initialize any startup tasks here
    try:
        # Could initialize database connections, load models, etc.
        logger.info("Backend services initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize services: {str(e)}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Triple Network AI Comparison System...")
    
    # Cleanup tasks
    try:
        # Close any open connections, save state, etc.
        logger.info("Cleanup completed successfully")
    except Exception as e:
        logger.error(f"Error during cleanup: {str(e)}")

# Create FastAPI application
app = FastAPI(
    title="Triple Network AI Comparison System",
    description="Real-time comparison of AI approaches to network self-healing",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router, prefix="/api/v1")

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors."""
    logger.error(f"Unhandled exception in {request.url}: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred",
            "path": str(request.url)
        }
    )

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with system information."""
    return {
        "service": "Triple Network AI Comparison System",
        "version": "1.0.0",
        "description": "Real-time comparison of AI approaches to network self-healing",
        "endpoints": {
            "api": "/api/v1",
            "docs": "/docs",
            "websocket": "/api/v1/ws"
        },
        "features": [
            "Rule-based Expert System",
            "Machine Learning Regression Model", 
            "Reinforcement Learning Agent",
            "Real-time Fault Injection",
            "Performance Monitoring",
            "Comparative Analysis"
        ]
    }

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "Triple Network AI Comparison System",
        "websocket_connections": websocket_manager.get_connection_count()
    }

# Metrics endpoint for monitoring
@app.get("/metrics")
async def get_metrics():
    """Get basic system metrics."""
    return {
        "websocket_connections": websocket_manager.get_connection_count(),
        "uptime": "N/A",  # Could track application uptime
        "memory_usage": "N/A",  # Could add memory monitoring
        "active_simulations": "N/A"  # Could track active simulations
    }

if __name__ == "__main__":
    # Development server
    port = int(os.getenv("API_PORT", 8000))
    host = os.getenv("API_HOST", "0.0.0.0")
    
    logger.info(f"Starting development server on {host}:{port}")
    
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )