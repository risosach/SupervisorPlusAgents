"""
Tests for Configuration Manager module.
Story 6: Configuration Management
"""
import pytest
from pathlib import Path


class TestConfigLoad:
    """Test configuration loading functionality."""

    def test_load_config_from_file(self):
        """
        Given: Valid config.json file
        When: Configuration is loaded
        Then: All fields are accessible
        """
        from supervisor.config import load_config

        config = load_config('tests/fixtures/test_config.json')

        assert config.system_prompt is not None
        assert len(config.tools) > 0
        assert 'document_retriever' in config.tools

    def test_config_load_missing_file(self):
        """
        Given: Non-existent config file path
        When: Configuration is loaded
        Then: FileNotFoundError is raised
        """
        from supervisor.config import load_config

        with pytest.raises(FileNotFoundError):
            load_config('tests/fixtures/nonexistent_config.json')

    def test_config_load_invalid_json(self):
        """
        Given: Invalid config file (malformed JSON)
        When: Configuration is loaded
        Then: Exception is raised with clear error message
        """
        from supervisor.config import load_config

        with pytest.raises(Exception) as exc_info:
            load_config('tests/fixtures/invalid_config.json')

        assert "config" in str(exc_info.value).lower() or "json" in str(exc_info.value).lower()


class TestConfigValidation:
    """Test configuration validation functionality."""

    def test_config_validate_required_fields(self):
        """
        Given: Valid config with all required fields
        When: Configuration is validated
        Then: No exception is raised
        """
        from supervisor.config import load_config, validate_config

        config = load_config('tests/fixtures/test_config.json')
        # Should not raise
        validate_config(config)

    def test_config_validation_missing_fields(self):
        """
        Given: Config with missing required fields
        When: Configuration is validated
        Then: Validation error is raised
        """
        from supervisor.config import load_config, validate_config

        with pytest.raises(ValueError):
            config = load_config('tests/fixtures/missing_fields_config.json')
            validate_config(config)


class TestConfigAccess:
    """Test configuration access methods."""

    def test_config_get_system_prompt(self):
        """
        Given: Valid config
        When: get_system_prompt() is called
        Then: System prompt string is returned
        """
        from supervisor.config import load_config

        config = load_config('tests/fixtures/test_config.json')
        prompt = config.get_system_prompt()

        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert "helpful AI assistant" in prompt

    def test_config_get_tool_config(self):
        """
        Given: Valid config with tools
        When: get_tool_config(tool_name) is called
        Then: Tool configuration dict is returned
        """
        from supervisor.config import load_config

        config = load_config('tests/fixtures/test_config.json')
        tool_config = config.get_tool_config('document_retriever')

        assert isinstance(tool_config, dict)
        assert 'enabled' in tool_config
        assert 'url' in tool_config

    def test_config_is_tool_enabled(self):
        """
        Given: Config with enabled and disabled tools
        When: is_tool_enabled(tool_name) is called
        Then: Correct boolean is returned
        """
        from supervisor.config import load_config

        # Test with all tools enabled
        config_enabled = load_config('tests/fixtures/test_config.json')
        assert config_enabled.is_tool_enabled('document_retriever') is True

        # Test with document tool disabled
        config_disabled = load_config('tests/fixtures/disabled_doc_tool_config.json')
        assert config_disabled.is_tool_enabled('document_retriever') is False


class TestConfigModification:
    """Test configuration modification and reloading."""

    def test_system_prompt_modification(self):
        """
        Given: Config with custom system prompt
        When: Supervisor is initialized
        Then: Custom prompt is used
        """
        from supervisor.config import load_config

        config = load_config('tests/fixtures/custom_prompt_config.json')

        assert "helpful AI assistant" in config.system_prompt
        assert "custom personality" in config.system_prompt

    def test_fallback_message_from_config(self):
        """
        Given: Config with custom fallback message
        When: Fallback message is accessed
        Then: Custom message is returned
        """
        from supervisor.config import load_config

        config = load_config('tests/fixtures/test_config.json')
        fallback = config.fallback_message

        assert "I'm sorry" in fallback
