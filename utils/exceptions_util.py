class ValidationError(Exception):
    """
    Raised when validation of input data fails.
    """

    def __init__(self, message: str, field: str = None):
        self.message = message
        self.field = field
        super().__init__(self.message)

    def to_dict(self):
        """
        Return dictionary for JSON response.
        """
        error = {"error": self.message}
        if self.field:
            error["field"] = self.field
        return error


class AuthenticationError(Exception):
    """
    Raised when authentication fails.
    """
    def __init__(self, message: str = "Invalid credentials"):
        super().__init__(message)


class AuthorizationError(Exception):
    """
    Raised when a user tries to access a resource without permission.
    """
    def __init__(self, message: str = "Unauthorized access"):
        super().__init__(message)


class NotFoundError(Exception):
    """
    Raised when a resource is not found.
    """
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message)
