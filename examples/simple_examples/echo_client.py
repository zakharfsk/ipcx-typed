import asyncio
import logging

from pydantic import BaseModel

from ipcx_typed import Client

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Define request/response models
class EchoRequest(BaseModel):
    message: str


class EchoResponse(BaseModel):
    echo: str


async def main():
    # Create client instance
    client = Client(host="localhost", port=8080)

    # Send echo request
    request = EchoRequest(message="Hello, World!")
    logger.info(f"Sending message: {request.message}")

    try:
        response = await client.request("echo", request, EchoResponse)
        logger.info(f"Received echo: {response.echo}")
    except Exception as e:
        logger.error(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
