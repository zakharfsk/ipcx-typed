class AuthorizationError(Exception):
    """Exception raised when the authorization header is invalid."""

    def __init__(self, message: str = "Invalid authorization header"):
        self.message = message
        super().__init__(self.message)


class EndpointNotFoundError(Exception):
    """Exception raised when the endpoint is not found."""

    def __init__(self, message: str = "Endpoint not found"):
        self.message = message
        super().__init__(self.message)
