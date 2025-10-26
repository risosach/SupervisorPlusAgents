"""
Tests for Claude API integration in LLM router.
Tests real API calls with mocking to avoid actual API usage.
"""
import pytest
from unittest.mock import patch, MagicMock, Mock
import os

# Check if Anthropic SDK is available for testing
try:
    from anthropic import Anthropic, APIError, APIConnectionError, APITimeoutError
    ANTHROPIC_SDK_AVAILABLE = True
except ImportError:
    ANTHROPIC_SDK_AVAILABLE = False

# Skip tests requiring Anthropic SDK if not installed
requires_anthropic = pytest.mark.skipif(
    not ANTHROPIC_SDK_AVAILABLE,
    reason="Anthropic SDK not installed"
)


class TestClaudeAPIIntegration:
    """Test Claude API integration for LLM routing."""

    @requires_anthropic
    @patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'test-key-123'})
    @patch('supervisor.llm_router.ANTHROPIC_AVAILABLE', True)
    def test_call_llm_for_routing_success(self):
        """
        Given: Valid API key and Anthropic SDK available
        When: _call_llm_for_routing is called
        Then: Returns tool suggestion from Claude API
        """
        from supervisor.llm_router import _call_llm_for_routing
        from supervisor.config import load_config

        # Mock the Anthropic class in the llm_router module
        with patch('supervisor.llm_router.Anthropic') as mock_anthropic_class:
            # Mock Claude API response
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.content = [MagicMock(text="doc")]
            mock_client.messages.create.return_value = mock_response
            mock_anthropic_class.return_value = mock_client

            config = load_config('tests/fixtures/test_config.json')
            result = _call_llm_for_routing("Test prompt", config)

            assert result == "doc"
            mock_anthropic_class.assert_called_once_with(api_key='test-key-123')
            mock_client.messages.create.assert_called_once()

    @patch('supervisor.llm_router.ANTHROPIC_AVAILABLE', True)
    @patch.dict(os.environ, {}, clear=True)  # No API key
    def test_call_llm_for_routing_no_api_key(self):
        """
        Given: No ANTHROPIC_API_KEY environment variable
        When: _call_llm_for_routing is called
        Then: Returns None (API key not configured)
        """
        from supervisor.llm_router import _call_llm_for_routing
        from supervisor.config import load_config

        config = load_config('tests/fixtures/test_config.json')
        result = _call_llm_for_routing("Test prompt", config)

        assert result is None

    @patch('supervisor.llm_router.ANTHROPIC_AVAILABLE', False)
    def test_call_llm_for_routing_sdk_not_available(self):
        """
        Given: Anthropic SDK not installed
        When: _call_llm_for_routing is called
        Then: Returns None (SDK not available)
        """
        from supervisor.llm_router import _call_llm_for_routing
        from supervisor.config import load_config

        config = load_config('tests/fixtures/test_config.json')
        result = _call_llm_for_routing("Test prompt", config)

        assert result is None

    @requires_anthropic
    @patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'test-key-123'})
    @patch('supervisor.llm_router.ANTHROPIC_AVAILABLE', True)
    def test_call_llm_for_routing_api_timeout(self):
        """
        Given: Claude API times out
        When: _call_llm_for_routing is called
        Then: Returns None (graceful fallback)
        """
        from supervisor.llm_router import _call_llm_for_routing
        from supervisor.config import load_config

        with patch('supervisor.llm_router.Anthropic') as mock_anthropic_class:
            with patch('supervisor.llm_router.APITimeoutError', Exception):
                # Mock timeout error
                mock_client = MagicMock()
                mock_client.messages.create.side_effect = Exception("Timeout")
                mock_anthropic_class.return_value = mock_client

                config = load_config('tests/fixtures/test_config.json')
                result = _call_llm_for_routing("Test prompt", config)

                assert result is None

    @requires_anthropic
    @patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'test-key-123'})
    @patch('supervisor.llm_router.ANTHROPIC_AVAILABLE', True)
    def test_call_llm_for_routing_api_error(self):
        """
        Given: Claude API returns an error
        When: _call_llm_for_routing is called
        Then: Returns None (graceful fallback)
        """
        from supervisor.llm_router import _call_llm_for_routing
        from supervisor.config import load_config

        with patch('supervisor.llm_router.Anthropic') as mock_anthropic_class:
            # Mock API error
            mock_client = MagicMock()
            if ANTHROPIC_SDK_AVAILABLE:
                # Create a mock request for APIError
                mock_request = MagicMock()
                mock_request.method = "POST"
                mock_request.url = "https://api.anthropic.com/v1/messages"

                from anthropic import APIError
                mock_client.messages.create.side_effect = APIError(
                    "API Error",
                    request=mock_request,
                    body=None
                )
            else:
                mock_client.messages.create.side_effect = Exception("API Error")
            mock_anthropic_class.return_value = mock_client

            config = load_config('tests/fixtures/test_config.json')
            result = _call_llm_for_routing("Test prompt", config)

            assert result is None

    @requires_anthropic
    @patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'test-key-123'})
    @patch('supervisor.llm_router.ANTHROPIC_AVAILABLE', True)
    def test_call_llm_for_routing_empty_response(self):
        """
        Given: Claude API returns empty content
        When: _call_llm_for_routing is called
        Then: Returns None (invalid response)
        """
        from supervisor.llm_router import _call_llm_for_routing
        from supervisor.config import load_config

        with patch('supervisor.llm_router.Anthropic') as mock_anthropic_class:
            # Mock empty response
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.content = []
            mock_client.messages.create.return_value = mock_response
            mock_anthropic_class.return_value = mock_client

            config = load_config('tests/fixtures/test_config.json')
            result = _call_llm_for_routing("Test prompt", config)

            assert result is None


class TestLLMRouteQueryWithAPI:
    """Test llm_route_query with real API integration."""

    @patch('supervisor.llm_router.ANTHROPIC_AVAILABLE', True)
    @patch('supervisor.llm_router._call_llm_for_routing')
    def test_llm_route_query_with_enabled_flag(self, mock_call_llm):
        """
        Given: enable_llm_fallback is True in config
        When: llm_route_query is called
        Then: Calls Claude API and returns suggestion
        """
        from supervisor.llm_router import llm_route_query
        from supervisor.config import load_config

        mock_call_llm.return_value = "doc"
        config = load_config('tests/fixtures/test_config.json')

        # Enable LLM fallback
        config.routing_rules['enable_llm_fallback'] = True

        result = llm_route_query("project timeline", config)

        assert result == "doc"
        assert mock_call_llm.call_count >= 1

    @patch('supervisor.llm_router.ANTHROPIC_AVAILABLE', True)
    @patch('supervisor.llm_router._call_llm_for_routing')
    def test_llm_route_query_validates_suggestion(self, mock_call_llm):
        """
        Given: Claude returns invalid tool name
        When: llm_route_query is called
        Then: Returns None (invalid suggestion rejected)
        """
        from supervisor.llm_router import llm_route_query
        from supervisor.config import load_config

        mock_call_llm.return_value = "invalid_tool"
        config = load_config('tests/fixtures/test_config.json')
        config.routing_rules['enable_llm_fallback'] = True

        result = llm_route_query("test query", config)

        assert result is None

    @patch('supervisor.llm_router.ANTHROPIC_AVAILABLE', True)
    @patch('supervisor.llm_router._call_llm_for_routing')
    def test_llm_route_query_handles_exception(self, mock_call_llm):
        """
        Given: Claude API raises exception
        When: llm_route_query is called
        Then: Returns None (graceful fallback)
        """
        from supervisor.llm_router import llm_route_query
        from supervisor.config import load_config

        mock_call_llm.side_effect = Exception("API Error")
        config = load_config('tests/fixtures/test_config.json')
        config.routing_rules['enable_llm_fallback'] = True

        result = llm_route_query("test query", config)

        assert result is None


class TestPromptFormatting:
    """Test that prompts are correctly formatted for Claude API."""

    def test_build_routing_prompt_format(self):
        """
        Given: Query and available tools
        When: _build_routing_prompt is called
        Then: Returns well-formed prompt for Claude
        """
        from supervisor.llm_router import _build_routing_prompt

        prompt = _build_routing_prompt(
            "What is the project status?",
            ["doc", "db", "web"]
        )

        # Verify prompt includes key elements
        assert "project status" in prompt.lower()
        assert "doc" in prompt or "document" in prompt.lower()
        assert "db" in prompt or "database" in prompt.lower()
        assert "web" in prompt.lower()
        assert "tool" in prompt.lower()

    def test_build_routing_prompt_with_context(self):
        """
        Given: Query, tools, and conversation context
        When: _build_routing_prompt is called
        Then: Context is included in prompt
        """
        from supervisor.llm_router import _build_routing_prompt

        context = "User previously asked about Q3 sales"
        prompt = _build_routing_prompt(
            "How about the target?",
            ["doc", "db"],
            context
        )

        # Verify context is in prompt
        assert context in prompt
        assert "target" in prompt.lower()


class TestAPIParameters:
    """Test that API calls use correct parameters."""

    @requires_anthropic
    @patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'test-key-123', 'CLAUDE_RUNTIME_MODEL': ''})
    @patch('supervisor.llm_router.ANTHROPIC_AVAILABLE', True)
    def test_api_call_uses_correct_model(self):
        """
        Given: API call is made without CLAUDE_RUNTIME_MODEL set
        When: Claude API is invoked
        Then: Uses default model (claude-3-5-sonnet-20241022)
        """
        from supervisor.llm_router import _call_llm_for_routing
        from supervisor.config import load_config

        with patch('supervisor.llm_router.Anthropic') as mock_anthropic_class:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.content = [MagicMock(text="doc")]
            mock_client.messages.create.return_value = mock_response
            mock_anthropic_class.return_value = mock_client

            config = load_config('tests/fixtures/test_config.json')
            _call_llm_for_routing("Test prompt", config)

            # Verify default model is used
            call_args = mock_client.messages.create.call_args
            assert call_args.kwargs['model'] == "claude-3-5-sonnet-20241022"

    @requires_anthropic
    @patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'test-key-123'})
    @patch('supervisor.llm_router.ANTHROPIC_AVAILABLE', True)
    def test_api_call_uses_short_timeout(self):
        """
        Given: API call is made for routing
        When: Claude API is invoked
        Then: Uses short timeout (5 seconds)
        """
        from supervisor.llm_router import _call_llm_for_routing
        from supervisor.config import load_config

        with patch('supervisor.llm_router.Anthropic') as mock_anthropic_class:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.content = [MagicMock(text="doc")]
            mock_client.messages.create.return_value = mock_response
            mock_anthropic_class.return_value = mock_client

            config = load_config('tests/fixtures/test_config.json')
            _call_llm_for_routing("Test prompt", config)

            # Verify short timeout
            call_args = mock_client.messages.create.call_args
            assert call_args.kwargs['timeout'] == 5.0

    @requires_anthropic
    @patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'test-key-123'})
    @patch('supervisor.llm_router.ANTHROPIC_AVAILABLE', True)
    def test_api_call_uses_minimal_tokens(self):
        """
        Given: API call is made for routing
        When: Claude API is invoked
        Then: Uses minimal max_tokens (10)
        """
        from supervisor.llm_router import _call_llm_for_routing
        from supervisor.config import load_config

        with patch('supervisor.llm_router.Anthropic') as mock_anthropic_class:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.content = [MagicMock(text="doc")]
            mock_client.messages.create.return_value = mock_response
            mock_anthropic_class.return_value = mock_client

            config = load_config('tests/fixtures/test_config.json')
            _call_llm_for_routing("Test prompt", config)

            # Verify minimal tokens
            call_args = mock_client.messages.create.call_args
            assert call_args.kwargs['max_tokens'] == 10


class TestBackwardCompatibility:
    """Test that Phase 3 tests still pass with Phase 4 changes."""

    def test_routing_without_api_key_still_works(self):
        """
        Given: No API key configured
        When: Router is used
        Then: Falls back to keyword routing (no errors)
        """
        from supervisor.router import decide_tool
        from supervisor.config import load_config

        config = load_config('tests/fixtures/test_config.json')

        # Should still work with keyword routing
        assert decide_tool("According to the document", config) == 'doc'
        assert decide_tool("How many accounts", config) == 'db'
        assert decide_tool("Latest news", config) == 'web'

    @patch('supervisor.llm_router.ANTHROPIC_AVAILABLE', False)
    def test_routing_without_sdk_still_works(self):
        """
        Given: Anthropic SDK not installed
        When: Router is used
        Then: Falls back to keyword routing (no errors)
        """
        from supervisor.router import decide_tool
        from supervisor.config import load_config

        config = load_config('tests/fixtures/test_config.json')

        # Should still work with keyword routing
        assert decide_tool("What is the capital of France?", config) == 'direct'
        assert decide_tool("According to the document", config) == 'doc'


class TestContextAwareRouting:
    """Test context-aware LLM routing."""

    @patch('supervisor.llm_router.ANTHROPIC_AVAILABLE', True)
    @patch('supervisor.llm_router._call_llm_for_routing')
    def test_llm_route_with_context_includes_context(self, mock_call_llm):
        """
        Given: Previous conversation context
        When: llm_route_with_context is called
        Then: Context is passed to API
        """
        from supervisor.llm_router import llm_route_with_context
        from supervisor.config import load_config

        mock_call_llm.return_value = "doc"
        config = load_config('tests/fixtures/test_config.json')
        config.routing_rules['enable_llm_fallback'] = True

        result = llm_route_with_context(
            "What about the target?",
            config,
            ["doc", "db", "web"],
            "User previously asked about Q3 sales"
        )

        # Should call API with context
        assert mock_call_llm.call_count >= 1
        # Verify context was in prompt
        call_args = mock_call_llm.call_args
        prompt = call_args[0][0]
        assert "Q3 sales" in prompt
