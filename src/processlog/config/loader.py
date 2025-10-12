"""
Configuration loader module

Loads and parses YAML configuration files for the event log generator.
"""

from pathlib import Path
from typing import Any, Dict

import yaml


# Type alias for configuration dictionary
ConfigDict = Dict[str, Any]


class ConfigurationError(Exception):
    """Raised when configuration loading fails"""
    pass


def load_config(file_path: str | Path) -> ConfigDict:
    """
    Load YAML configuration from file

    Args:
        file_path: Path to YAML configuration file

    Returns:
        ConfigDict: Parsed configuration dictionary

    Raises:
        ConfigurationError: If file cannot be read or parsed

    Example:
        >>> config = load_config('configs/process_config.yaml')
        >>> print(config['process_name'])
        'Restaurant Permit Application'
    """
    file_path = Path(file_path)

    # Check file exists
    if not file_path.exists():
        raise ConfigurationError(f"Configuration file not found: {file_path}")

    # Check file is readable
    if not file_path.is_file():
        raise ConfigurationError(f"Path is not a file: {file_path}")

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ConfigurationError(f"Failed to parse YAML file: {e}") from e
    except Exception as e:
        raise ConfigurationError(f"Failed to read file {file_path}: {e}") from e

    # Check that config is not None (empty file)
    if config is None:
        raise ConfigurationError(f"Configuration file is empty: {file_path}")

    # Check that config is a dictionary
    if not isinstance(config, dict):
        raise ConfigurationError(
            f"Configuration must be a YAML dictionary, got {type(config).__name__}"
        )

    return config


def parse_yaml(yaml_string: str) -> ConfigDict:
    """
    Parse YAML string into configuration dictionary

    Useful for testing without creating temporary files.

    Args:
        yaml_string: YAML content as string

    Returns:
        ConfigDict: Parsed configuration dictionary

    Raises:
        ConfigurationError: If YAML cannot be parsed

    Example:
        >>> config = parse_yaml('''
        ... process_name: Test Process
        ... num_cases: 10
        ... ''')
        >>> print(config['process_name'])
        'Test Process'
    """
    try:
        config = yaml.safe_load(yaml_string)
    except yaml.YAMLError as e:
        raise ConfigurationError(f"Failed to parse YAML string: {e}") from e

    # Check that config is not None (empty string)
    if config is None:
        raise ConfigurationError("YAML string is empty")

    # Check that config is a dictionary
    if not isinstance(config, dict):
        raise ConfigurationError(
            f"Configuration must be a YAML dictionary, got {type(config).__name__}"
        )

    return config
