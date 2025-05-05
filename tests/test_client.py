# ruff: noqa: S106
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
    server = Server(host="localhost", port=8082, secret_key="test_secret")

    @server.route(param_model=EchoRequest, return_model=EchoResponse)
    async def echo(data: EchoRequest) -> EchoResponse:
        return EchoResponse(message=data.message)

    await server.start()
    yield server
    await server.stop()


@pytest.fixture
async def auth_server():
    """Fixture that creates and starts a test server with authorization."""
    server = Server(host="localhost", port=8082, secret_key="test_secret")

    @server.route(param_model=EchoRequest, return_model=EchoResponse)
    async def echo(data: EchoRequest) -> EchoResponse:
        return EchoResponse(message=data.message)

    await server.start()
    yield server
    await server.stop()


async def test_client_connection(server):
    """Test client connection to server."""
    async with Client(host="localhost", port=8082, secret_key="test_secret") as client:
        assert client.session is not None


async def test_client_request(server):
    """Test client request to server."""
    async with Client(host="localhost", port=8082, secret_key="test_secret") as client:
        request_data = EchoRequest(message="Hello, World!")
        response = await client.request("echo", request_data, EchoResponse)
        assert response.success is True
        assert isinstance(response.data, EchoResponse)
        assert response.data.message == "Hello, World!"
        assert response.error_message is None


async def test_client_invalid_endpoint(server):
    """Test client request to invalid endpoint."""
    async with Client(host="localhost", port=8082, secret_key="test_secret") as client:
        request_data = EchoRequest(message="Hello")
        response = await client.request("invalid_endpoint", request_data, EchoResponse)
        assert response.success is False
        assert response.data is None
        assert response.error_message is not None
        assert "endpoint" in response.error_message.lower()


async def test_client_connection_retry():
    """Test client connection retry mechanism."""
    client = Client(host="localhost", port=8082, max_retries=2, retry_delay=0.1, secret_key="test_secret")

    with pytest.raises(ConnectionError):
        await client.request("echo", EchoRequest(message="Hello"), EchoResponse)


async def test_client_context_manager():
    """Test client context manager."""
    client = Client(host="localhost", port=8082, secret_key="test_secret")
    assert client.session is None

    async with client:
        assert client.session is not None

    assert client.session is None


async def test_client_timeout():
    """Test client timeout configuration."""
    client = Client(host="localhost", port=8082, timeout=1.0, secret_key="test_secret")
    assert client.timeout is not None
    assert client.timeout.total == 1.0


async def test_client_authorization(auth_server):
    """Test client authorization with valid and invalid secret keys."""
    # Test with valid secret key
    async with Client(host="localhost", port=8082, secret_key="test_secret") as client:
        request_data = EchoRequest(message="Hello, World!")
        response = await client.request("echo", request_data, EchoResponse)
        assert response.success is True
        assert isinstance(response.data, EchoResponse)
        assert response.data.message == "Hello, World!"
        assert response.error_message is None

    # Test with invalid secret key
    async with Client(host="localhost", port=8082, secret_key="wrong_secret") as client:
        request_data = EchoRequest(message="Hello, World!")
        response = await client.request("echo", request_data, EchoResponse)
        assert response.success is False
        assert response.data is None
        assert response.error_message is not None
        assert "Invalid authorization header" in response.error_message

    # Test with missing secret key
    async with Client(host="localhost", port=8082) as client:
        request_data = EchoRequest(message="Hello, World!")
        response = await client.request("echo", request_data, EchoResponse)
        assert response.success is False
        assert response.data is None
        assert response.error_message is not None
        assert "Invalid authorization header" in response.error_message


async def test_client_error_response(server):
    """Test client handling of error responses."""
    async with Client(host="localhost", port=8082, secret_key="test_secret") as client:
        # Test with invalid endpoint
        response = await client.request("nonexistent", EchoRequest(message="test"), EchoResponse)
        assert response.success is False
        assert response.data is None
        assert response.error_message is not None
        assert "endpoint" in response.error_message.lower()

        # Test with invalid request data
        class InvalidRequest(BaseModel):
            invalid_field: str

        response = await client.request("echo", InvalidRequest(invalid_field="test"), EchoResponse)
        assert response.success is False
        assert response.data is None
        assert response.error_message is not None
        assert "validation" in response.error_message.lower()
