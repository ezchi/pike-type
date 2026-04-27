"""Project-specific exception types."""


class TypistError(Exception):
    """Base exception for typist."""


class DiscoveryError(TypistError):
    """Raised when repo/module discovery fails."""


class ValidationError(TypistError):
    """Raised when frozen IR validation fails."""


class EmissionError(TypistError):
    """Raised when code generation fails."""
