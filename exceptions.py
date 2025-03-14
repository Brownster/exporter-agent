"""Custom exceptions for the exporter-agent."""

class ExporterAgentError(Exception):
    """Base exception class for all exporter-agent errors."""
    pass


class LLMProviderError(ExporterAgentError):
    """Exception for LLM provider errors."""
    pass


class APIKeyError(LLMProviderError):
    """Exception for missing or invalid API keys."""
    pass


class ConfigError(ExporterAgentError):
    """Exception for configuration errors."""
    pass


class ResearchError(ExporterAgentError):
    """Exception for errors during research phase."""
    pass


class CodeGenerationError(ExporterAgentError):
    """Exception for errors during code generation."""
    pass


class ValidationError(ExporterAgentError):
    """Exception for code validation errors."""
    pass


class TestingError(ExporterAgentError):
    """Exception for testing errors."""
    pass


class DashboardGenerationError(ExporterAgentError):
    """Exception for errors during dashboard generation."""
    pass


class AlertGenerationError(ExporterAgentError):
    """Exception for errors during alert generation."""
    pass