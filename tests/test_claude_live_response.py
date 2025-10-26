"""
Tests for live Claude API integration.

This module tests that the Supervisor properly integrates with the real
Anthropic Claude API when ANTHROPIC_API_KEY is available, and gracefully
falls back to stub responses when it's not.
"""

import pytest
import os
from unittest.mock import patch, MagicMock
from supervisor.handlers import call_claude_api, handle_direct
from supervisor.config import load_config


class TestClaudeLiveAPIIntegration:
    """Test live Claude API integration with real API calls."""

    @pytest.mark.skipif(
        not os.getenv("ANTHROPIC_API_KEY"),
        reason="ANTHROPIC_API_KEY not set - skipping live API test"
    )
    def test_live_claude_api_call(self):
        """
        Given: ANTHROPIC_API_KEY is set in environment
        When: Calling call_claude_api with a simple query
        Then: Returns real Claude response (not stub)
        """
        system_prompt = "You are a helpful assistant. Answer concisely."
        user_message = "What is the capital of the UK?"

        response = call_claude_api(system_prompt, user_message)

        # Should NOT be a stub response
        assert "[Stub Claude API Response]" not in response

        # Should contain relevant information about London
        assert "London" in response or "london" in response.lower()

        # Should be a reasonable length
        assert len(response) > 0
        assert len(response) < 1000  # Claude should be concise

    @pytest.mark.skipif(
        not os.getenv("ANTHROPIC_API_KEY"),
        reason="ANTHROPIC_API_KEY not set - skipping live API test"
    )
    def test_live_claude_math_query(self):
        """
        Given: ANTHROPIC_API_KEY is set
        When: Asking a math question
        Then: Returns correct answer from Claude
        """
        system_prompt = "You are a helpful assistant. Answer concisely."
        user_message = "What is 15 + 27? Just give the number."

        response = call_claude_api(system_prompt, user_message)

        # Should NOT be a stub response
        assert "[Stub Claude API Response]" not in response

        # Should contain the correct answer
        assert "42" in response

    @pytest.mark.skipif(
        not os.getenv("ANTHROPIC_API_KEY"),
        reason="ANTHROPIC_API_KEY not set - skipping live API test"
    )
    def test_live_direct_handler(self):
        """
        Given: ANTHROPIC_API_KEY is set
        When: Using handle_direct for general query
        Then: Returns real Claude response through handler
        """
        config = load_config('tests/fixtures/test_config.json')
        query = "What is the capital of France?"

        response = handle_direct(query, config)

        # Should NOT be a stub response
        assert "[Stub Claude API Response]" not in response

        # Should mention Paris
        assert "Paris" in response or "paris" in response.lower()


class TestClaudeAPIFallback:
    """Test graceful fallback when API is unavailable."""

    def test_fallback_when_no_api_key(self):
        """
        Given: ANTHROPIC_API_KEY is not set
        When: Calling call_claude_api
        Then: Falls back to stub response
        """
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": ""}, clear=False):
            system_prompt = "You are helpful."
            user_message = "What is 2+2?"

            response = call_claude_api(system_prompt, user_message)

            # Should be a stub response
            assert "[Stub Claude API Response]" in response
            assert "What is 2+2?" in response

    @patch('supervisor.handlers.ANTHROPIC_AVAILABLE', False)
    def test_fallback_when_sdk_unavailable(self):
        """
        Given: Anthropic SDK is not installed
        When: Calling call_claude_api
        Then: Falls back to stub response
        """
        system_prompt = "You are helpful."
        user_message = "Hello world"

        response = call_claude_api(system_prompt, user_message)

        # Should be a stub response
        assert "[Stub Claude API Response]" in response
        assert "Hello world" in response

    @patch('supervisor.handlers.Anthropic')
    def test_fallback_on_api_error(self, mock_anthropic):
        """
        Given: Claude API call raises an error
        When: Calling call_claude_api
        Then: Catches error and falls back to stub
        """
        # Mock the Anthropic client to raise an error
        mock_client = MagicMock()
        mock_client.messages.create.side_effect = Exception("API Error")
        mock_anthropic.return_value = mock_client

        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}, clear=False):
            with patch('supervisor.handlers.ANTHROPIC_AVAILABLE', True):
                system_prompt = "You are helpful."
                user_message = "Test query"

                response = call_claude_api(system_prompt, user_message)

                # Should fall back to stub response
                assert "[Stub Claude API Response]" in response
                assert "Test query" in response


class TestClaudeAPIValidation:
    """Test input validation for Claude API calls."""

    def test_empty_system_prompt(self):
        """
        Given: Empty system prompt
        When: Calling call_claude_api
        Then: Raises ValueError
        """
        with pytest.raises(ValueError, match="System prompt must be a non-empty string"):
            call_claude_api("", "Hello")

    def test_empty_user_message(self):
        """
        Given: Empty user message
        When: Calling call_claude_api
        Then: Raises ValueError
        """
        with pytest.raises(ValueError, match="User message must be a non-empty string"):
            call_claude_api("You are helpful", "")

    def test_whitespace_only_inputs(self):
        """
        Given: Whitespace-only inputs
        When: Calling call_claude_api
        Then: Raises ValueError
        """
        with pytest.raises(ValueError, match="cannot be empty or whitespace only"):
            call_claude_api("   ", "test")

        with pytest.raises(ValueError, match="cannot be empty or whitespace only"):
            call_claude_api("test", "   ")

    def test_non_string_inputs(self):
        """
        Given: Non-string inputs
        When: Calling call_claude_api
        Then: Raises ValueError
        """
        with pytest.raises(ValueError, match="must be a non-empty string"):
            call_claude_api(None, "test")

        with pytest.raises(ValueError, match="must be a non-empty string"):
            call_claude_api("test", None)


class TestClaudeModelConfiguration:
    """Test Claude model configuration from environment."""

    @patch('supervisor.handlers.Anthropic')
    def test_uses_model_from_env(self, mock_anthropic):
        """
        Given: CLAUDE_RUNTIME_MODEL is set in environment
        When: Calling call_claude_api
        Then: Uses the specified model
        """
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Test response")]
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_client

        custom_model = "claude-3-5-sonnet-20241022"

        with patch.dict(os.environ, {
            "ANTHROPIC_API_KEY": "test-key",
            "CLAUDE_RUNTIME_MODEL": custom_model
        }, clear=False):
            with patch('supervisor.handlers.ANTHROPIC_AVAILABLE', True):
                response = call_claude_api("You are helpful", "Test")

                # Verify the model was used
                mock_client.messages.create.assert_called_once()
                call_kwargs = mock_client.messages.create.call_args[1]
                assert call_kwargs['model'] == custom_model

    @patch('supervisor.handlers.Anthropic')
    def test_uses_default_model_when_not_set(self, mock_anthropic):
        """
        Given: CLAUDE_RUNTIME_MODEL is not set
        When: Calling call_claude_api
        Then: Uses default claude-3-5-haiku-20241022
        """
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Test response")]
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_client

        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}, clear=True):
            with patch('supervisor.handlers.ANTHROPIC_AVAILABLE', True):
                response = call_claude_api("You are helpful", "Test")

                # Verify default model was used
                mock_client.messages.create.assert_called_once()
                call_kwargs = mock_client.messages.create.call_args[1]
                assert call_kwargs['model'] == "claude-3-5-haiku-20241022"
