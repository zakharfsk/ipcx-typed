"""
This is a Python library for implementing Inter-Process Communication (IPC) using WebSocket connections,
featuring type-safe request/response handling with Pydantic models and async support.
"""

from .client import Client
from .server import Server, route

__all__ = ["Client", "Server", "route"]

__title__ = "ipcx_typed"
__author__ = "zakharfsk"
__license__ = "Apache-2.0"
__copyright__ = "(c) 2024-present zakharfsk"
__version__ = "0.1.0"
