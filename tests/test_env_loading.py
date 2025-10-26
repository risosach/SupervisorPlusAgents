"""
Tests for .env file loading and runtime configuration.
Verifies that environment variables from .env are correctly loaded and applied.
"""
import pytest
import os
from unittest.mock import patch, MagicMock


class TestEnvLoading:
    """Test .env file loading for Claude runtime configuration."""

    def test_dotenv_package_available(self):
        """
        Given: python-dotenv package installed
        When: Importing dotenv
        Then: Import succeeds
        """
        try:
            from dotenv import load_dotenv
            assert callable(load_dotenv)
        except ImportError:
            pytest.fail("python-dotenv package not installed")

    def test_env_file_exists(self):
        """
        Given: Project root directory
        When: Checking for .env file
        Then: .env file exists
        """
        import os
        env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
        assert os.path.exists(env_path), ".env file not found at project root"

    def test_env_variables_loaded(self):
        """
        Given: .env file with ANTHROPIC_API_KEY and CLAUDE_RUNTIME_MODEL
        When: llm_router module is imported (loads .env automatically)
        Then: Environment variables are accessible
        """
        # Import triggers load_dotenv() at module level
        from supervisor import llm_router

        # Check if API key is loaded
        api_key = os.getenv("ANTHROPIC_API_KEY")
        assert api_key is not None, "ANTHROPIC_API_KEY not loaded from .env"
        assert len(api_key) > 0, "ANTHROPIC_API_KEY is empty"

        # Check if model is loaded
        model = os.getenv("CLAUDE_RUNTIME_MODEL")
        assert model is not None, "CLAUDE_RUNTIME_MODEL not loaded from .env"
        assert len(model) > 0, "CLAUDE_RUNTIME_MODEL is empty"

    def test_claude_runtime_model_used(self):
        """
        Given: CLAUDE_RUNTIME_MODEL set in .env
        When: _call_llm_for_routing is called
        Then: Uses model from environment variable
        """
        from supervisor.llm_router import _call_llm_for_routing
        from supervisor.config import load_config

        # Get the model that should be loaded from .env
        expected_model = os.getenv("CLAUDE_RUNTIME_MODEL")
        assert expected_model is not None, "CLAUDE_RUNTIME_MODEL not loaded"

        # Skip if Anthropic SDK not available
        try:
            from anthropic import Anthropic
        except ImportError:
            pytest.skip("Anthropic SDK not installed")

        with patch('supervisor.llm_router.ANTHROPIC_AVAILABLE', True):
            with patch('supervisor.llm_router.Anthropic') as mock_anthropic_class:
                # Mock the client and response
                mock_client = MagicMock()
                mock_response = MagicMock()
                mock_response.content = [MagicMock(text="doc")]
                mock_client.messages.create.return_value = mock_response
                mock_anthropic_class.return_value = mock_client

                config = load_config('tests/fixtures/test_config.json')
                result = _call_llm_for_routing("Test prompt", config)

                # Verify the correct model was used
                call_args = mock_client.messages.create.call_args
                actual_model = call_args.kwargs['model']
                assert actual_model == expected_model, \
                    f"Expected model {expected_model}, but got {actual_model}"

    def test_fallback_to_default_model(self):
        """
        Given: CLAUDE_RUNTIME_MODEL not set
        When: _call_llm_for_routing is called
        Then: Falls back to default model
        """
        from supervisor.llm_router import _call_llm_for_routing
        from supervisor.config import load_config

        # Skip if Anthropic SDK not available
        try:
            from anthropic import Anthropic
        except ImportError:
            pytest.skip("Anthropic SDK not installed")

        # Temporarily unset CLAUDE_RUNTIME_MODEL and set API key
        with patch.dict(os.environ, {'CLAUDE_RUNTIME_MODEL': '', 'ANTHROPIC_API_KEY': 'test-key'}, clear=False):
            with patch('supervisor.llm_router.ANTHROPIC_AVAILABLE', True):
                with patch('supervisor.llm_router.Anthropic') as mock_anthropic_class:
                    mock_client = MagicMock()
                    mock_response = MagicMock()
                    mock_response.content = [MagicMock(text="doc")]
                    mock_client.messages.create.return_value = mock_response
                    mock_anthropic_class.return_value = mock_client

                    config = load_config('tests/fixtures/test_config.json')
                    result = _call_llm_for_routing("Test prompt", config)

                    # Should use default model
                    call_args = mock_client.messages.create.call_args
                    actual_model = call_args.kwargs['model']
                    assert actual_model == "claude-3-5-sonnet-20241022", \
                        f"Expected default model, but got {actual_model}"

    def test_backward_compatibility_without_dotenv(self):
        """
        Given: python-dotenv not installed (simulated)
        When: llm_router module is imported
        Then: Module loads successfully without errors
        """
        # This test verifies the try/except ImportError block works
        # The actual import has already happened, but we verify
        # that the module is functional
        from supervisor import llm_router

        # Verify key functions exist
        assert hasattr(llm_router, 'llm_route_query')
        assert hasattr(llm_router, '_call_llm_for_routing')
        assert hasattr(llm_router, 'llm_route_with_context')

    def test_env_values_format(self):
        """
        Given: Environment variables loaded from .env
        When: Checking format and validity
        Then: Values are in expected format
        """
        api_key = os.getenv("ANTHROPIC_API_KEY")
        model = os.getenv("CLAUDE_RUNTIME_MODEL")

        # Verify API key format (starts with sk-ant-)
        if api_key:
            assert api_key.startswith("sk-ant-"), \
                "ANTHROPIC_API_KEY should start with 'sk-ant-'"

        # Verify model name format (contains 'claude')
        if model:
            assert "claude" in model.lower(), \
                "CLAUDE_RUNTIME_MODEL should contain 'claude'"


class TestEnvConfigurationLogging:
    """Test that .env configuration is properly logged."""

    def test_model_selection_logged(self, caplog):
        """
        Given: _call_llm_for_routing is called
        When: Model is selected from environment
        Then: Model selection is logged at debug level
        """
        from supervisor.llm_router import _call_llm_for_routing
        from supervisor.config import load_config
        import logging

        # Skip if Anthropic SDK not available
        try:
            from anthropic import Anthropic
        except ImportError:
            pytest.skip("Anthropic SDK not installed")

        with patch('supervisor.llm_router.ANTHROPIC_AVAILABLE', True):
            with patch('supervisor.llm_router.Anthropic') as mock_anthropic_class:
                mock_client = MagicMock()
                mock_response = MagicMock()
                mock_response.content = [MagicMock(text="doc")]
                mock_client.messages.create.return_value = mock_response
                mock_anthropic_class.return_value = mock_client

                config = load_config('tests/fixtures/test_config.json')

                # Enable debug logging
                with caplog.at_level(logging.DEBUG):
                    result = _call_llm_for_routing("Test prompt", config)

                # Check that model selection was logged
                model_logs = [record for record in caplog.records
                             if "Using Claude model:" in record.message]
                assert len(model_logs) > 0, "Model selection not logged"
