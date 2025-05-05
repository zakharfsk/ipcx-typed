# ruff: noqa: S106
import asyncio
import logging
from typing import List

from pydantic import BaseModel

from ipcx_typed import Server

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Define request/response models
class AddRequest(BaseModel):
    numbers: List[float]


class AddResponse(BaseModel):
    sum: float


class MultiplyRequest(BaseModel):
    numbers: List[float]


class MultiplyResponse(BaseModel):
    product: float


class StatsRequest(BaseModel):
    numbers: List[float]


class StatsResponse(BaseModel):
    min: float
    max: float
    average: float


async def main():
    # Create server instance
    server = Server(host="localhost", port=8080, secret_key="secret")

    # Define calculator endpoints
    @server.route(param_model=AddRequest, return_model=AddResponse)
    async def add(request: AddRequest) -> AddResponse:
        result = sum(request.numbers)
        logger.info(f"Adding numbers: {request.numbers} = {result}")
        return AddResponse(sum=result)

    @server.route(param_model=MultiplyRequest, return_model=MultiplyResponse)
    async def multiply(request: MultiplyRequest) -> MultiplyResponse:
        result = 1
        for num in request.numbers:
            result *= num
        logger.info(f"Multiplying numbers: {request.numbers} = {result}")
        return MultiplyResponse(product=result)

    @server.route(param_model=StatsRequest, return_model=StatsResponse)
    async def stats(request: StatsRequest) -> StatsResponse:
        if not request.numbers:
            raise ValueError("Empty list provided")

        min_val = min(request.numbers)
        max_val = max(request.numbers)
        avg_val = sum(request.numbers) / len(request.numbers)

        logger.info(f"Calculating stats for: {request.numbers}")
        return StatsResponse(min=min_val, max=max_val, average=avg_val)

    # Start server
    await server.start()
    logger.info("Calculator server started on ws://localhost:8080")

    try:
        # Keep server running
        while True:  # noqa: ASYNC110
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutting down server...")
        await server.stop()


if __name__ == "__main__":
    asyncio.run(main())
