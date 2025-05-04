import json
import logging
from collections.abc import Awaitable, Callable
from typing import Any, Dict, Optional, Type, TypeVar

import aiohttp.web
from pydantic import BaseModel, ValidationError

from .models import Request, Response

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)
R = TypeVar("R", bound=BaseModel)


class Endpoint:
    """A class representing an API endpoint with its associated function and models."""

    def __init__(
        self,
        func: Callable[[T], Awaitable[Any]],
        param_model: Type[T],
        return_model: Type[R],
    ) -> None:
        """
        Initialize an Endpoint instance.

        Args:
            func: The async function to be called when the endpoint is hit
            param_model: The Pydantic model for validating input parameters
            return_model: The Pydantic model for validating return values
        """
        self.func = func
        self.param_model = param_model
        self.return_model = return_model


def route(
    param_model: Type[T],
    return_model: Type[R],
    name: Optional[str] = None,
) -> Callable[[Callable[[T], Awaitable[Any]]], Callable[[T], Awaitable[Any]]]:
    """
    Decorator for registering a route with the server.

    Args:
        param_model: The Pydantic model for validating input parameters
        return_model: The Pydantic model for validating return values
        name: Optional custom name for the endpoint. If not provided, uses function name

    Returns:
        A decorator function that registers the route
    """

    def decorator(func: Callable[[T], Awaitable[Any]]) -> Callable[[T], Awaitable[Any]]:
        if not issubclass(param_model, BaseModel):
            raise ValueError(f"Model must inherit from {BaseModel.__name__} class")

        print(dir(func))

        endpoint = Endpoint(func, param_model, return_model)
        if not name:
            Server.ROUTES[func.__name__] = endpoint
        else:
            Server.ROUTES[name] = endpoint

        return func

    return decorator


class Server:
    """A WebSocket server for handling IPC communication."""

    ROUTES: Dict[str, Endpoint] = {}

    def __init__(
        self,
        host: str = "localhost",
        port: int = 8080,
        on_startup: Optional[Callable[..., Awaitable[None]]] = None,
        on_error: Optional[Callable[..., Awaitable[None]]] = None,
    ) -> None:
        """
        Initialize a Server instance.

        Args:
            host: The host address to bind to
            port: The port number to listen on
            on_startup: Optional callback function to run when server starts
            on_error: Optional callback function to run when an error occurs
        """
        self.host = host
        self.port = port
        self._server: Optional[aiohttp.web.Application] = None
        self._runner: Optional[aiohttp.web.AppRunner] = None
        self.on_error = on_error
        self.on_startup = on_startup
        self.endpoints: Dict[str, Endpoint] = {}

    def route(
        self,
        param_model: Type[T],
        return_model: Type[R],
        name: Optional[str] = None,
    ) -> Callable[[Callable[[T], Awaitable[Any]]], Callable[[T], Awaitable[Any]]]:
        """
        Decorator for registering a route with this server instance.

        Args:
            param_model: The Pydantic model for validating input parameters
            return_model: The Pydantic model for validating return values
            name: Optional custom name for the endpoint. If not provided, uses function name

        Returns:
            A decorator function that registers the route
        """

        def decorator(func: Callable[[T], Awaitable[Any]]) -> Callable[[T], Awaitable[Any]]:
            if not issubclass(param_model, BaseModel):
                raise ValueError(f"Model must inherit from {BaseModel.__name__} class")

            endpoint = Endpoint(func, param_model, return_model)
            if not name:
                self.endpoints[func.__name__] = endpoint
            else:
                self.endpoints[name] = endpoint

            return func

        return decorator

    def update_endpoints(self) -> None:
        """Update the server's endpoints by merging global ROUTES with instance endpoints."""
        self.endpoints = {**self.ROUTES, **self.endpoints}
        self.ROUTES = {}

    async def _handle_request(self, http_request: aiohttp.web.Request) -> aiohttp.web.WebSocketResponse:
        """
        Handle incoming WebSocket requests.

        Args:
            http_request: The incoming HTTP request

        Returns:
            A WebSocket response object
        """
        self.update_endpoints()
        websocket = aiohttp.web.WebSocketResponse()
        await websocket.prepare(http_request)

        try:
            async for message in websocket:
                if message.type != aiohttp.WSMsgType.TEXT:
                    logger.warning(f"Received non-text message: {message.type}")
                    continue

                try:
                    request = Request.model_validate_json(message.data)
                    if request.endpoint not in self.endpoints:
                        raise ValueError(f"Endpoint {request.endpoint} not found")

                    endpoint = self.endpoints[request.endpoint]
                    validated_data = endpoint.param_model.model_validate(request.data)
                    func_response = await endpoint.func(validated_data)
                    func_response_model = endpoint.return_model.model_validate(func_response)

                    await websocket.send_json(
                        Response(success=True, data=func_response_model.model_dump(), error_message=None).model_dump()
                    )

                except ValidationError as e:
                    logger.error(f"Validation error: {e}")
                    await websocket.send_json(
                        Response(success=False, data=json.loads(e.json()), error_message=str(e)).model_dump()
                    )
                    if self.on_error:
                        await self.on_error()

                except Exception as e:
                    logger.error(f"Error processing request: {e}")
                    await websocket.send_json(Response(success=False, data=str(e), error_message=str(e)).model_dump())
                    if self.on_error:
                        await self.on_error()
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
            if self.on_error:
                await self.on_error()

        return websocket

    async def _start(self, application: aiohttp.web.Application) -> None:
        """
        Start the server with the given application.

        Args:
            application: The aiohttp web application to run
        """
        self._runner = aiohttp.web.AppRunner(application)
        await self._runner.setup()

        site = aiohttp.web.TCPSite(self._runner, self.host, self.port)
        await site.start()

    async def stop(self) -> None:
        """Stop the server and clean up resources."""
        if self._runner:
            await self._runner.cleanup()
            self._runner = None
        self._server = None

    async def start(self) -> None:
        """Start the server and run the startup callback if provided."""
        if self.on_startup:
            await self.on_startup()

        self._server = aiohttp.web.Application()
        self._server.router.add_route("GET", "/", self._handle_request)

        await self._start(self._server)
