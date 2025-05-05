import json
import logging
from collections.abc import Awaitable, Callable
from typing import Any, Dict, Optional, Type

import aiohttp.web
from pydantic import ValidationError

from ipcx_typed._types import Endpoint, R, T
from ipcx_typed.errors import AuthorizationError, EndpointNotFoundError

from .models import Request, Response

logger = logging.getLogger(__name__)


def route(
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
        endpoint = Endpoint(func, param_model, return_model)
        fn_name = name or func.__name__
        Server.ROUTES[fn_name] = endpoint
        return func

    return decorator


class Server:
    """A WebSocket server for handling IPC communication."""

    ROUTES: Dict[str, Endpoint] = {}

    def __init__(
        self,
        host: str = "localhost",
        port: int = 8080,
        secret_key: Optional[str] = None,
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
        self.secret_key = secret_key

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
            endpoint = Endpoint(func, param_model, return_model)
            fn_name = name or func.__name__
            self.endpoints[fn_name] = endpoint
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

                    if request.headers.authorization != self.secret_key:
                        raise AuthorizationError()

                    if request.endpoint not in self.endpoints:
                        raise EndpointNotFoundError()

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
