"""
Configuration management for Supervisor CLI Agent.

This module handles loading, validation, and access to configuration files.
"""
import json
from pathlib import Path
from typing import Dict, Any, Optional


class Config:
    """
    Configuration object for Supervisor Agent.

    Attributes:
        system_prompt (str): System prompt for LLM
        tools (Dict): Tool configurations
        routing_rules (Dict): Routing keyword rules
        fallback_message (str): Default fallback message
    """

    def __init__(self, config_dict: Dict[str, Any]):
        """
        Initialize Config from dictionary.

        Args:
            config_dict: Configuration dictionary loaded from JSON
        """
        self.system_prompt = config_dict.get('system_prompt', '')
        self.tools = config_dict.get('tools', {})
        self.routing_rules = config_dict.get('routing_rules', {})
        self.fallback_message = config_dict.get('fallback_message', '')

        # Store raw config for future use
        self._raw_config = config_dict

    def get_system_prompt(self) -> str:
        """
        Get the system prompt.

        Returns:
            System prompt string
        """
        return self.system_prompt

    def get_tool_config(self, tool_name: str) -> Dict[str, Any]:
        """
        Get configuration for a specific tool.

        Args:
            tool_name: Name of the tool

        Returns:
            Tool configuration dictionary

        Raises:
            KeyError: If tool not found in configuration
        """
        if tool_name not in self.tools:
            raise KeyError(f"Tool '{tool_name}' not found in configuration")
        return self.tools[tool_name]

    def is_tool_enabled(self, tool_name: str) -> bool:
        """
        Check if a tool is enabled.

        Args:
            tool_name: Name of the tool

        Returns:
            True if tool is enabled, False otherwise
        """
        if tool_name not in self.tools:
            return False
        return self.tools[tool_name].get('enabled', False)


def load_config(path: str) -> Config:
    """
    Load configuration from JSON file.

    Args:
        path: Path to configuration JSON file

    Returns:
        Config object

    Raises:
        FileNotFoundError: If config file doesn't exist
        json.JSONDecodeError: If config file is invalid JSON
        ValueError: If config fails validation
    """
    config_path = Path(path)

    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {path}")

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config_dict = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in config file: {e}")

    # Create Config object
    config = Config(config_dict)

    # Validate the configuration
    validate_config(config)

    return config


def validate_config(config: Config) -> None:
    """
    Validate configuration has all required fields.

    Args:
        config: Config object to validate

    Raises:
        ValueError: If required fields are missing or invalid
    """
    # Check for required fields
    if not config.system_prompt:
        raise ValueError("Configuration missing required field: 'system_prompt'")

    if not isinstance(config.tools, dict):
        raise ValueError("Configuration field 'tools' must be a dictionary")

    if not isinstance(config.routing_rules, dict):
        raise ValueError("Configuration missing required field: 'routing_rules'")

    # Validate tools structure
    for tool_name, tool_config in config.tools.items():
        if not isinstance(tool_config, dict):
            raise ValueError(f"Tool '{tool_name}' configuration must be a dictionary")

        if 'enabled' not in tool_config:
            raise ValueError(f"Tool '{tool_name}' missing 'enabled' field")
