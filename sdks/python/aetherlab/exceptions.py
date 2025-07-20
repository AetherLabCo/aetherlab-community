"""
AetherLab SDK Exceptions

Custom exceptions for the AetherLab SDK.
"""


class AetherLabError(Exception):
    """Base exception for all AetherLab SDK errors."""
    pass


class APIError(AetherLabError):
    """Raised when an API request fails."""
    pass


class ValidationError(AetherLabError):
    """Raised when input validation fails."""
    pass


class AuthenticationError(AetherLabError):
    """Raised when authentication fails."""
    pass


class RateLimitError(AetherLabError):
    """Raised when rate limit is exceeded."""
    pass


class ConfigurationError(AetherLabError):
    """Raised when there's a configuration issue."""
    pass 