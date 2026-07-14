class ReinspectionAgentError(Exception):
    """Base exception for the Re-inspection Decision Agent."""


class InvalidZoneDataError(ReinspectionAgentError):
    """Raised when zone result data is invalid or incomplete."""


class MaxPassesExceededError(ReinspectionAgentError):
    """Raised when inspection passes exceed the allowed maximum."""
