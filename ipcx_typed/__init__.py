"""
This is a Python library for implementing Inter-Process Communication (IPC) using WebSocket connections,
featuring type-safe request/response handling with Pydantic models and async support.
"""

from .client import Client
from .server import Server, route

__all__ = ["Client", "Server", "route"]
