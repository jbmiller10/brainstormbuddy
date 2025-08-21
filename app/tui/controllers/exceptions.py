"""Custom exceptions for onboarding controller."""


class OnboardingError(Exception):
    """Base exception for all onboarding-related errors."""

    pass


class ValidationError(OnboardingError):
    """Raised when input validation fails.

    This includes empty strings, excessive length, invalid format, etc.
    """

    pass


class LLMGenerationError(OnboardingError):
    """Raised when LLM generation fails.

    This includes timeouts, API errors, network issues, etc.
    """

    pass


class TranscriptError(OnboardingError):
    """Raised when transcript operations fail.

    This includes serialization errors, invalid transcript state, etc.
    """

    pass


class KernelValidationError(OnboardingError):
    """Raised when kernel structure validation fails.

    This is more specific than general ValidationError and indicates
    the generated kernel doesn't meet structural requirements.
    """

    pass


class ThreadSafetyError(OnboardingError):
    """Raised when thread safety issues are detected.

    This includes problems with event loop management in sync wrappers.
    """

    pass
