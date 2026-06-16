"""
Configuration module

Provides configuration loading and validation for the event log generator.
"""

from .loader import ConfigDict, ConfigurationError, load_config, parse_yaml
from .validator import ValidationResult, validate_config

__all__ = [
    "ConfigDict",
    "ConfigurationError",
    "ValidationResult",
    "load_config",
    "parse_yaml",
    "validate_config",
]
