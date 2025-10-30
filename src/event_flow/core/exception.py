"""Custom exceptions for the event flow framework.

This module defines exception classes for various error conditions
in the event flow system.
"""


class EngineNotSetError(Exception):
    """Raised when attempting to use an Application without setting its engine."""
    ...


class SettingNotFound(Exception):
    """Raised when a required configuration setting is not found."""
    ...


class SettingError(Exception):
    """Raised when there is an error with configuration settings."""
    ...


class PublisherNotSetError(Exception):
    """Raised when attempting to publish an event without a configured publisher."""
    ...
