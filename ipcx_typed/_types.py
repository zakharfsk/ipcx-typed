from collections.abc import Awaitable
from typing import Any, Callable, Type, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)
R = TypeVar("R", bound=BaseModel)
G = TypeVar("G")


class Endpoint:
    """A class representing an API endpoint with its associated function and models."""

    def __init__(
        self,
        func: Callable[[T], Awaitable[Any]],
        param_model: Type[T],
        return_model: Type[R],
    ) -> None:
        """
        Initialize an Endpoint instance.

        Args:
            func: The async function to be called when the endpoint is hit
            param_model: The Pydantic model for validating input parameters
            return_model: The Pydantic model for validating return values
        """
        self.func = func
        self.param_model = param_model
        self.return_model = return_model
