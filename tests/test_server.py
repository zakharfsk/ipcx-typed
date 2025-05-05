# ruff: noqa: S106
import aiohttp
import pytest
from pydantic import BaseModel

from ipcx_typed.server import Server


class EchoRequest(BaseModel):
    message: str


class EchoResponse(BaseModel):
    message: str


@pytest.fixture
async def server():
    """Fixture that creates and starts a test server."""
    server = Server(host="localhost", port=8081)

    @server.route(param_model=EchoRequest, return_model=EchoResponse)
    async def echo(data: EchoRequest) -> EchoResponse:
        return EchoResponse(message=data.message)

    await server.start()
    yield server
    await server.stop()


@pytest.fixture
async def auth_server():
    """Fixture that creates and starts a test server with authorization."""
    server = Server(host="localhost", port=8081, secret_key="test_secret")

    @server.route(param_model=EchoRequest, return_model=EchoResponse)
    async def echo(data: EchoRequest) -> EchoResponse:
        return EchoResponse(message=data.message)

    await server.start()
    yield server
    await server.stop()


async def test_server_startup():
    """Test server startup and shutdown."""
    server = Server(host="localhost", port=8081)
    await server.start()
    assert server._server is not None
    assert server._runner is not None
    await server.stop()
    assert server._runner is None


async def test_server_route_decorator():
    """Test route decorator registration."""
    server = Server()

    @server.route(param_model=EchoRequest, return_model=EchoResponse)
    async def test_endpoint(data: EchoRequest) -> EchoResponse:
        return EchoResponse(message=data.message)

    server.update_endpoints()
    assert "test_endpoint" in server.endpoints
    endpoint = server.endpoints["test_endpoint"]
    assert endpoint.param_model == EchoRequest
    assert endpoint.return_model == EchoResponse


async def test_server_custom_route_name():
    """Test route decorator with custom endpoint name."""
    server = Server()

    @server.route(param_model=EchoRequest, return_model=EchoResponse, name="custom_echo")
    async def test_endpoint(data: EchoRequest) -> EchoResponse:
        return EchoResponse(message=data.message)

    server.update_endpoints()
    assert "custom_echo" in server.endpoints
    assert "test_endpoint" not in server.endpoints


async def test_server_startup_callback():
    """Test server startup callback."""
    startup_called = False

    async def on_startup():
        nonlocal startup_called
        startup_called = True

    server = Server(on_startup=on_startup)
    await server.start()
    assert startup_called
    await server.stop()


async def test_server_error_callback():
    """Test server error callback."""
    error_called = False

    async def on_error():
        nonlocal error_called
        error_called = True

    server = Server(on_error=on_error, secret_key="test_secret")
    await server.start()

    # Create a test endpoint that will raise an error
    @server.route(param_model=EchoRequest, return_model=EchoResponse)
    async def error_endpoint(data: EchoRequest) -> EchoResponse:
        raise Exception("Test error")

    # Create a WebSocket client to trigger the error
    async with aiohttp.ClientSession() as session:
        async with session.ws_connect(f"ws://{server.host}:{server.port}") as ws:
            await ws.send_json(
                {"endpoint": "error_endpoint", "data": {"message": "test"}, "headers": {"authorization": "test_secret"}}
            )
            response = await ws.receive_json()
            assert not response["success"]
            assert "Test error" in response["error_message"]

    assert error_called
    await server.stop()


async def test_server_authorization(auth_server):
    """Test server authorization with valid and invalid secret keys."""
    # Test with valid secret key
    async with aiohttp.ClientSession() as session:
        async with session.ws_connect(f"ws://{auth_server.host}:{auth_server.port}") as ws:
            await ws.send_json(
                {"endpoint": "echo", "data": {"message": "test"}, "headers": {"authorization": "test_secret"}}
            )
            response = await ws.receive_json()
            assert response["success"]
            assert response["data"]["message"] == "test"

    # Test with invalid secret key
    async with aiohttp.ClientSession() as session:
        async with session.ws_connect(f"ws://{auth_server.host}:{auth_server.port}") as ws:
            await ws.send_json(
                {"endpoint": "echo", "data": {"message": "test"}, "headers": {"authorization": "wrong_secret"}}
            )
            response = await ws.receive_json()
            assert not response["success"]
            assert "Invalid authorization header" in response["error_message"]

    # Test with missing authorization header
    async with aiohttp.ClientSession() as session:
        async with session.ws_connect(f"ws://{auth_server.host}:{auth_server.port}") as ws:
            await ws.send_json({"endpoint": "echo", "data": {"message": "test"}, "headers": {}})
            response = await ws.receive_json()
            assert not response["success"]
            assert "Invalid authorization header" in response["error_message"]
