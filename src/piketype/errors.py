"""Project-specific exception types."""


class PikeTypeError(Exception):
    """Base exception for piketype."""


class DiscoveryError(PikeTypeError):
    """Raised when repo/module discovery fails."""


class ValidationError(PikeTypeError):
    """Raised when frozen IR validation fails."""


class EmissionError(PikeTypeError):
    """Raised when code generation fails."""
