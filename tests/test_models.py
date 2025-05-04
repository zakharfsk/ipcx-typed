import pytest
from pydantic import ValidationError

from ipcx_typed.models import Request, Response


def test_request_model_valid():
    """Test creating a valid Request model."""
    request = Request(endpoint="test_endpoint", data={"message": "Hello"})
    assert request.endpoint == "test_endpoint"
    assert request.data == {"message": "Hello"}


def test_request_model_invalid_endpoint():
    """Test Request model with invalid endpoint (empty string)."""
    with pytest.raises(ValidationError):
        Request(endpoint="", data={"message": "Hello"})


def test_request_model_missing_data():
    """Test Request model with missing required fields."""
    with pytest.raises(ValidationError):
        Request(endpoint="test_endpoint")  # type: ignore


def test_response_model_success():
    """Test creating a successful Response model."""
    response = Response.create_success(data={"result": "Success"})
    assert response.success is True
    assert response.data == {"result": "Success"}
    assert response.error_message is None


def test_response_model_error():
    """Test creating an error Response model."""
    response = Response.create_error(error="Test error")
    assert response.success is False
    assert response.data is None
    assert response.error_message == "Test error"


def test_response_model_direct_creation():
    """Test direct creation of Response model."""
    response = Response(success=True, data={"result": "Direct"}, error_message=None)
    assert response.success is True
    assert response.data == {"result": "Direct"}
    assert response.error_message is None


def test_response_model_validation():
    """Test Response model validation."""
    with pytest.raises(ValidationError):
        # success must be bool, not str
        Response(success="invalid", data={}, error_message=None)  # type: ignore
