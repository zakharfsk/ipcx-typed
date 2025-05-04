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
    server = Server(host="localhost", port=8083)

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
    async with Client(host="localhost", port=8083) as client:
        # Test addition
        add_request = MathRequest(a=5.0, b=3.0)
        add_response = await client.request("add", add_request, MathResponse)
        assert add_response.result == 8.0

        # Test multiplication
        mult_request = MathRequest(a=5.0, b=3.0)
        mult_response = await client.request("multiply", mult_request, MathResponse)
        assert mult_response.result == 15.0


async def test_concurrent_requests(math_server):
    """Test handling multiple concurrent requests."""
    async with Client(host="localhost", port=8083) as client:
        requests = []
        for i in range(5):
            request = MathRequest(a=float(i), b=2.0)
            requests.append(client.request("add", request, MathResponse))

        responses = await asyncio.gather(*requests)

        for i, response in enumerate(responses):
            assert response.result == float(i) + 2.0


async def test_error_handling(math_server):
    """Test error handling in integration scenario."""
    async with Client(host="localhost", port=8083) as client:
        # Test invalid endpoint
        with pytest.raises(ValueError):
            await client.request("invalid_op", MathRequest(a=1.0, b=2.0), MathResponse)

        # Test invalid model type
        class InvalidModel(BaseModel):
            invalid: str

        with pytest.raises(ValueError):
            await client.request("add", InvalidModel(invalid="data"), MathResponse)


async def test_server_client_reconnection(math_server):
    """Test client reconnection after server restart."""
    client = Client(host="localhost", port=8083, max_retries=3, retry_delay=0.1)

    # First request should work
    async with client:
        response = await client.request("add", MathRequest(a=1.0, b=2.0), MathResponse)
        assert response.result == 3.0

    # Stop and restart server
    await math_server.stop()
    await math_server.start()

    # Second request should work after reconnection
    async with client:
        response = await client.request("add", MathRequest(a=2.0, b=3.0), MathResponse)
        assert response.result == 5.0
