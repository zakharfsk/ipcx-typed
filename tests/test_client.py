import pytest
from pydantic import BaseModel

from ipcx_typed.client import Client
from ipcx_typed.server import Server


class EchoRequest(BaseModel):
    message: str


class EchoResponse(BaseModel):
    message: str


@pytest.fixture
async def server():
    """Fixture that creates and starts a test server."""
    server = Server(host="localhost", port=8082)

    @server.route(param_model=EchoRequest, return_model=EchoResponse)
    async def echo(data: EchoRequest) -> EchoResponse:
        return EchoResponse(message=data.message)

    await server.start()
    yield server
    await server.stop()


async def test_client_connection(server):
    """Test client connection to server."""
    async with Client(host="localhost", port=8082) as client:
        assert client.session is not None


async def test_client_request(server):
    """Test client request to server."""
    async with Client(host="localhost", port=8082) as client:
        request_data = EchoRequest(message="Hello, World!")
        response = await client.request("echo", request_data, EchoResponse)
        assert isinstance(response, EchoResponse)
        assert response.message == "Hello, World!"


async def test_client_invalid_endpoint(server):
    """Test client request to invalid endpoint."""
    async with Client(host="localhost", port=8082) as client:
        request_data = EchoRequest(message="Hello")
        with pytest.raises(ValueError):
            await client.request("invalid_endpoint", request_data, EchoResponse)


async def test_client_connection_retry():
    """Test client connection retry mechanism."""
    client = Client(host="localhost", port=8082, max_retries=2, retry_delay=0.1)

    with pytest.raises(ConnectionError):
        await client.request("echo", EchoRequest(message="Hello"), EchoResponse)


async def test_client_context_manager():
    """Test client context manager."""
    client = Client(host="localhost", port=8082)
    assert client.session is None

    async with client:
        assert client.session is not None

    assert client.session is None


async def test_client_timeout():
    """Test client timeout configuration."""
    client = Client(host="localhost", port=8082, timeout=1.0)
    assert client.timeout is not None
    assert client.timeout.total == 1.0
