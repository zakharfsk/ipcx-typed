import asyncio
import logging

from pydantic import BaseModel

from ipcx_typed import Server

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Define request/response models
class EchoRequest(BaseModel):
    message: str


class EchoResponse(BaseModel):
    echo: str


async def main():
    # Create server instance
    server = Server(host="localhost", port=8080)

    # Define echo endpoint
    @server.route(param_model=EchoRequest, return_model=EchoResponse)
    async def echo(request: EchoRequest) -> EchoResponse:
        logger.info(f"Received message: {request.message}")
        return EchoResponse(echo=request.message)

    # Start server
    await server.start()
    logger.info("Server started on ws://localhost:8080")

    try:
        # Keep server running
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutting down server...")
        await server.stop()


if __name__ == "__main__":
    asyncio.run(main())
