# ruff: noqa: S106
import asyncio

import pytest
from pydantic import BaseModel

from ipcx_typed.client import Client
from ipcx_typed.server import Server


class MathRequest(BaseModel):
    a: float
    b: float


class MathResponse(BaseModel):
    result: float


@pytest.fixture
async def math_server():
    """Fixture that creates and starts a test server with math operations."""
    server = Server(host="localhost", port=8083, secret_key="math_secret")

    @server.route(param_model=MathRequest, return_model=MathResponse)
    async def add(data: MathRequest) -> MathResponse:
        return MathResponse(result=data.a + data.b)

    @server.route(param_model=MathRequest, return_model=MathResponse)
    async def multiply(data: MathRequest) -> MathResponse:
        return MathResponse(result=data.a * data.b)

    await server.start()
    yield server
    await server.stop()


@pytest.fixture
async def auth_math_server():
    """Fixture that creates and starts a test server with math operations and authorization."""
    server = Server(host="localhost", port=8083, secret_key="math_secret")

    @server.route(param_model=MathRequest, return_model=MathResponse)
    async def add(data: MathRequest) -> MathResponse:
        return MathResponse(result=data.a + data.b)

    @server.route(param_model=MathRequest, return_model=MathResponse)
    async def multiply(data: MathRequest) -> MathResponse:
        return MathResponse(result=data.a * data.b)

    await server.start()
    yield server
    await server.stop()


async def test_multiple_endpoints(math_server):
    """Test multiple endpoint operations on the same server."""
    async with Client(host="localhost", port=8083, secret_key="math_secret") as client:
        # Test addition
        add_request = MathRequest(a=5.0, b=3.0)
        add_response = await client.request("add", add_request, MathResponse)
        assert add_response.success is True
        assert isinstance(add_response.data, MathResponse)
        assert add_response.data.result == 8.0
        assert add_response.error_message is None

        # Test multiplication
        mult_request = MathRequest(a=5.0, b=3.0)
        mult_response = await client.request("multiply", mult_request, MathResponse)
        assert mult_response.success is True
        assert isinstance(mult_response.data, MathResponse)
        assert mult_response.data.result == 15.0
        assert mult_response.error_message is None


async def test_concurrent_requests(math_server):
    """Test handling multiple concurrent requests."""
    async with Client(host="localhost", port=8083, secret_key="math_secret") as client:
        requests = []
        for i in range(5):
            request = MathRequest(a=float(i), b=2.0)
            requests.append(client.request("add", request, MathResponse))

        responses = await asyncio.gather(*requests)

        for i, response in enumerate(responses):
            assert response.success is True
            assert isinstance(response.data, MathResponse)
            assert response.data.result == float(i) + 2.0
            assert response.error_message is None


async def test_authorized_concurrent_requests(auth_math_server):
    """Test handling multiple concurrent requests with authorization."""
    async with Client(host="localhost", port=8083, secret_key="math_secret") as client:
        requests = []
        for i in range(5):
            request = MathRequest(a=float(i), b=2.0)
            requests.append(client.request("add", request, MathResponse))

        responses = await asyncio.gather(*requests)

        for i, response in enumerate(responses):
            assert response.success is True
            assert isinstance(response.data, MathResponse)
            assert response.data.result == float(i) + 2.0
            assert response.error_message is None


async def test_error_handling(math_server):
    """Test error handling in integration scenario."""
    async with Client(host="localhost", port=8083, secret_key="math_secret") as client:
        # Test invalid endpoint
        response = await client.request("invalid_op", MathRequest(a=1.0, b=2.0), MathResponse)
        assert response.success is False
        assert response.data is None
        assert response.error_message is not None

        # Test invalid model type
        class InvalidModel(BaseModel):
            invalid: str

        response = await client.request("add", InvalidModel(invalid="data"), MathResponse)
        assert response.success is False
        assert response.data is None
        assert response.error_message is not None


async def test_authorization_error_handling(auth_math_server):
    """Test authorization error handling in integration scenario."""
    # Test with wrong secret key
    async with Client(host="localhost", port=8083, secret_key="wrong_secret") as client:
        response = await client.request("add", MathRequest(a=1.0, b=2.0), MathResponse)
        assert response.success is False
        assert response.data is None
        assert response.error_message is not None
        assert "Invalid authorization header" in response.error_message

    # Test with missing secret key
    async with Client(host="localhost", port=8083) as client:
        response = await client.request("add", MathRequest(a=1.0, b=2.0), MathResponse)
        assert response.success is False
        assert response.data is None
        assert response.error_message is not None
        assert "Invalid authorization header" in response.error_message


async def test_server_client_reconnection(math_server):
    """Test client reconnection after server restart."""
    client = Client(host="localhost", port=8083, max_retries=3, retry_delay=0.1, secret_key="math_secret")

    # First request should work
    async with client:
        response = await client.request("add", MathRequest(a=1.0, b=2.0), MathResponse)
        assert response.success is True
        assert isinstance(response.data, MathResponse)
        assert response.data.result == 3.0
        assert response.error_message is None

    # Stop and restart server
    await math_server.stop()
    await math_server.start()

    # Second request should work after reconnection
    async with client:
        response = await client.request("add", MathRequest(a=2.0, b=3.0), MathResponse)
        assert response.success is True
        assert isinstance(response.data, MathResponse)
        assert response.data.result == 5.0
        assert response.error_message is None


async def test_auth_server_client_reconnection(auth_math_server):
    """Test client reconnection after server restart with authorization."""
    client = Client(host="localhost", port=8083, max_retries=3, retry_delay=0.1, secret_key="math_secret")

    # First request should work
    async with client:
        response = await client.request("add", MathRequest(a=1.0, b=2.0), MathResponse)
        assert response.success is True
        assert isinstance(response.data, MathResponse)
        assert response.data.result == 3.0
        assert response.error_message is None

    # Stop and restart server
    await auth_math_server.stop()
    await auth_math_server.start()

    # Second request should work after reconnection
    async with client:
        response = await client.request("add", MathRequest(a=2.0, b=3.0), MathResponse)
        assert response.success is True
        assert isinstance(response.data, MathResponse)
        assert response.data.result == 5.0
        assert response.error_message is None
