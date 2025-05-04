from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class Request(BaseModel):
    """WebSocket request model.

    Attributes:
        endpoint: The name of the endpoint to call
        data: The request data to be validated against the endpoint's parameter model
    """

    endpoint: str = Field(..., min_length=1, description="The name of the endpoint to call")
    data: Any = Field(..., description="The request data to be validated against the endpoint's parameter model")

    model_config = ConfigDict(json_schema_extra={"example": {"endpoint": "echo", "data": {"message": "Hello, World!"}}})


class Response(BaseModel, Generic[T]):
    """WebSocket response model.

    Attributes:
        success: Whether the request was successful
        data: The response data, type depends on the endpoint's return model
        error_message: Optional error message if success is False
    """

    success: bool = Field(..., description="Whether the request was successful")
    data: T = Field(..., description="The response data, type depends on the endpoint's return model")
    error_message: Optional[str] = Field(None, description="Optional error message if success is False")

    model_config = ConfigDict(
        json_schema_extra={"example": {"success": True, "data": {"message": "Hello, World!"}, "error_message": None}}
    )

    @classmethod
    def create_success(cls, data: T) -> "Response[T]":
        """Create a successful response.

        Args:
            data: The response data

        Returns:
            Response with success=True and the provided data
        """
        return cls(success=True, data=data, error_message=None)

    @classmethod
    def create_error(cls, error: str) -> "Response[T]":
        """Create an error response.

        Args:
            error: The error message

        Returns:
            Response with success=False and the error message
        """
        return cls(success=False, data=None, error_message=error)  # type: ignore
