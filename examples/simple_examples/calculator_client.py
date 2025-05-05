# ruff: noqa: S106
import asyncio
import logging
from typing import List

from pydantic import BaseModel

from ipcx_typed import Client

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
    # Create client instance
    client = Client(host="localhost", port=8080, secret_key="secret")

    # Test numbers
    numbers = [1.5, 2.5, 3.5, 4.5]

    try:
        # Test addition
        add_request = AddRequest(numbers=numbers)
        add_response = await client.request("add", add_request, AddResponse)
        logger.info(f"Addition result: {add_response.sum}")

        # Test multiplication
        multiply_request = MultiplyRequest(numbers=numbers)
        multiply_response = await client.request("multiply", multiply_request, MultiplyResponse)
        logger.info(f"Multiplication result: {multiply_response.product}")

        # Test statistics
        stats_request = StatsRequest(numbers=numbers)
        stats_response = await client.request("stats", stats_request, StatsResponse)
        logger.info(f"Statistics: min={stats_response.min}, max={stats_response.max}, average={stats_response.average}")

        # Test error handling with empty list
        empty_request = StatsRequest(numbers=[])
        try:
            await client.request("stats", empty_request, StatsResponse)
        except Exception as e:
            logger.error(f"Expected error: {e}")

    except Exception as e:
        logger.error(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
