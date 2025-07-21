"""
API package for FastAPI application.
Contains REST API routes and WebSocket handlers.
"""

from .routes import router
from .websocket import websocket_manager

__all__ = ["router", "websocket_manager"]