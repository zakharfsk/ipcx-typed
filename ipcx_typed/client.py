import asyncio
import json
import logging
from typing import Optional, Type

import aiohttp
from pydantic import BaseModel, ValidationError

from ipcx_typed._types import T
from ipcx_typed.models import Headers, Request, Response

logger = logging.getLogger(__name__)


class Client:
    """A WebSocket client for IPC communication with the server."""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 8080,
        secret_key: Optional[str] = None,
        max_retries: int = 3,
        retry_delay: float = 5.0,
        timeout: Optional[float] = 30.0,
    ) -> None:
        """
        Initialize a Client instance.

        Args:
            host: The server host address to connect to
            port: The server port number to connect to
            max_retries: Maximum number of connection retry attempts
            retry_delay: Delay in seconds between retry attempts
            timeout: Connection timeout in seconds
        """
        self.host = host
        self.port = port
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.timeout = aiohttp.ClientTimeout(total=timeout) if timeout else None
        self.session: Optional[aiohttp.ClientSession] = None
        self.secret_key = secret_key

    async def __aenter__(self) -> "Client":
        """Context manager entry point. Establishes the WebSocket session."""
        await self._get_session()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        """Context manager exit point. Closes the WebSocket session."""
        await self.close()

    @property
    def url(self) -> str:
        """Get the WebSocket URL for the server."""
        return f"ws://{self.host}:{self.port}"

    async def _get_session(self) -> aiohttp.ClientSession:
        """
        Get or create a new WebSocket session.

        Returns:
            An active aiohttp ClientSession
        """
        if not self.session:
            self.session = aiohttp.ClientSession()
        return self.session

    async def close(self) -> None:
        """Close the WebSocket session and clean up resources."""
        if self.session:
            await self.session.close()
            self.session = None

    async def request(
        self,
        endpoint: str,
        request_model: BaseModel,
        response_model: Type[T],
        retry_count: int = 0,
    ) -> Response[T]:
        """
        Send a request to the server and wait for a response.

        Args:
            endpoint: The server endpoint to call
            request_model: The Pydantic model containing request data
            response_model: The Pydantic model for validating response data
            retry_count: Current retry attempt number

        Returns:
            The validated response data

        Raises:
            ConnectionError: If max retries are exceeded
            ValueError: If server returns an error or invalid response format
        """
        if retry_count >= self.max_retries:
            raise ConnectionError(f"Max retries ({self.max_retries}) exceeded")

        session = await self._get_session()

        try:
            async with session.ws_connect(
                self.url,
                autoclose=False,
                autoping=False,
                heartbeat=30.0,
            ) as websocket:
                payload = Request(
                    endpoint=endpoint,
                    data=request_model.model_dump(),
                    headers=Headers(authorization=self.secret_key),
                )

                logger.debug(f"Sending payload: {payload}")
                await websocket.send_json(payload.model_dump())

                while True:
                    try:
                        recv = await websocket.receive()
                        logger.info(f"Received response: {recv}")

                        if recv.type == aiohttp.WSMsgType.PING:
                            await websocket.ping()
                            continue

                        if recv.type == aiohttp.WSMsgType.PONG:
                            continue

                        if recv.type == aiohttp.WSMsgType.CLOSED:
                            raise ConnectionError("WebSocket connection closed")

                        if recv.type == aiohttp.WSMsgType.ERROR:
                            raise ConnectionError(f"WebSocket error: {recv.data}")

                        response_data = recv.json()
                        logger.debug(f"Response data: {response_data}")

                        if not response_data.get("success", False):
                            error_data = response_data.get("data", {})
                            return Response.create_error(error=error_data)

                        return Response.create_success(response_model.model_validate(response_data.get("data", {})))

                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to decode JSON response: {e}")
                        return Response.create_error(error=str(e))

        except (aiohttp.ClientError, ConnectionError) as e:
            logger.warning(f"Connection error (attempt {retry_count + 1}/{self.max_retries}): {e}")
            await asyncio.sleep(self.retry_delay)
            return await self.request(endpoint, request_model, response_model, retry_count + 1)

        except ValidationError as e:
            logger.error(f"Validation error: {e}")
            return Response.create_error(error=str(e))

        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return Response.create_error(error=str(e))
