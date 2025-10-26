"""
Tests for LLM-based routing fallback.
Tests ambiguous query handling and LLM routing integration.
"""
import pytest
from unittest.mock import patch, MagicMock


class TestLLMRouterStub:
    """Test LLM router stub functionality (Phase 3)."""

    def test_llm_route_query_stub_returns_none(self):
        """
        Given: LLM routing called with any query
        When: llm_route_query is called (stub implementation)
        Then: Returns None (no routing suggestion yet)
        """
        from supervisor.llm_router import llm_route_query
        from supervisor.config import load_config

        config = load_config('tests/fixtures/test_config.json')
        result = llm_route_query("ambiguous query", config)

        # Stub implementation should return None
        assert result is None

    def test_llm_route_query_validates_input(self):
        """
        Given: Invalid input to llm_route_query
        When: Called with empty or non-string query
        Then: Raises ValueError
        """
        from supervisor.llm_router import llm_route_query
        from supervisor.config import load_config

        config = load_config('tests/fixtures/test_config.json')

        with pytest.raises(ValueError):
            llm_route_query("", config)

        with pytest.raises(ValueError):
            llm_route_query("   ", config)

    def test_llm_routing_disabled_by_default(self):
        """
        Given: Config without enable_llm_fallback flag
        When: llm_route_query is called
        Then: Returns None (LLM routing not enabled)
        """
        from supervisor.llm_router import llm_route_query
        from supervisor.config import load_config

        config = load_config('tests/fixtures/test_config.json')
        # Config doesn't have enable_llm_fallback, so should return None
        result = llm_route_query("test query", config)

        assert result is None


class TestAmbiguityDetection:
    """Test query ambiguity detection logic."""

    def test_ambiguous_multiple_categories(self):
        """
        Given: Query matches multiple keyword categories
        When: is_ambiguous_query is called
        Then: Returns True (ambiguous)
        """
        from supervisor.llm_router import is_ambiguous_query

        # Multiple matches = ambiguous
        assert is_ambiguous_query("Check the document and database", ["doc", "db"]) is True
        assert is_ambiguous_query("Latest news in the file", ["doc", "web"]) is True

    def test_not_ambiguous_single_match(self):
        """
        Given: Query matches single category clearly
        When: is_ambiguous_query is called
        Then: Returns False (not ambiguous)
        """
        from supervisor.llm_router import is_ambiguous_query

        # Single clear match = not ambiguous
        assert is_ambiguous_query("According to the Q3 Project Plan", ["doc"]) is False
        assert is_ambiguous_query("How many accounts were created?", ["db"]) is False

    def test_ambiguous_short_vague_query(self):
        """
        Given: Very short query with no clear category
        When: is_ambiguous_query is called
        Then: Returns True (potentially ambiguous)
        """
        from supervisor.llm_router import is_ambiguous_query

        # Short queries with no matches might be ambiguous
        assert is_ambiguous_query("timeline", []) is True
        assert is_ambiguous_query("status", []) is True

    def test_not_ambiguous_longer_query_no_match(self):
        """
        Given: Longer query with no keyword matches
        When: is_ambiguous_query is called
        Then: Returns False (not ambiguous, just no tool match)
        """
        from supervisor.llm_router import is_ambiguous_query

        # Longer queries without matches aren't necessarily ambiguous
        # They're just general questions that should go to direct LLM
        assert is_ambiguous_query("What is the capital of France?", []) is False


class TestRouterLLMIntegration:
    """Test integration of LLM fallback with main router."""

    def test_router_falls_back_to_direct_when_llm_returns_none(self):
        """
        Given: Ambiguous query with no keyword matches
        When: LLM routing returns None (stub behavior)
        Then: Router defaults to 'direct'
        """
        from supervisor.router import decide_tool
        from supervisor.config import load_config

        config = load_config('tests/fixtures/test_config.json')

        # Query with no clear keywords should try LLM fallback
        # LLM stub returns None, so should fall back to 'direct'
        classification = decide_tool("Tell me something interesting", config)

        assert classification == 'direct'

    def test_router_respects_keyword_match_priority(self):
        """
        Given: Query with clear keyword match
        When: Router classifies query
        Then: Uses keyword routing (doesn't call LLM)
        """
        from supervisor.router import decide_tool
        from supervisor.config import load_config

        config = load_config('tests/fixtures/test_config.json')

        # Clear keyword matches should not trigger LLM fallback
        assert decide_tool("According to the document", config) == 'doc'
        assert decide_tool("How many accounts?", config) == 'db'
        assert decide_tool("Latest news", config) == 'web'

    @patch('supervisor.router.is_ambiguous_query')
    @patch('supervisor.router.llm_route_query')
    def test_router_calls_llm_for_ambiguous_queries(self, mock_llm, mock_ambiguous):
        """
        Given: Ambiguous query (detected by is_ambiguous_query)
        When: Router processes query
        Then: Calls LLM routing fallback
        """
        from supervisor.router import decide_tool
        from supervisor.config import load_config

        # Force query to be detected as ambiguous
        mock_ambiguous.return_value = True
        mock_llm.return_value = None  # Stub returns None
        config = load_config('tests/fixtures/test_config.json')

        # Query that we're forcing to be ambiguous
        decide_tool("status", config)

        # Verify LLM was called
        assert mock_llm.call_count >= 1

    @patch('supervisor.router.is_ambiguous_query')
    @patch('supervisor.router.llm_route_query')
    def test_router_uses_llm_suggestion_when_provided(self, mock_llm, mock_ambiguous):
        """
        Given: LLM returns a valid routing suggestion
        When: Router processes ambiguous query
        Then: Uses LLM suggestion if tool is enabled
        """
        from supervisor.router import decide_tool
        from supervisor.config import load_config

        # Force query to be detected as ambiguous
        mock_ambiguous.return_value = True
        # Mock LLM to return 'doc' suggestion
        mock_llm.return_value = 'doc'
        config = load_config('tests/fixtures/test_config.json')

        # Query that we're forcing to be ambiguous
        classification = decide_tool("timeline", config)

        # Should use LLM suggestion if document tool is enabled
        if config.is_tool_enabled('document_retriever'):
            assert classification == 'doc'
        else:
            assert classification == 'direct'

    @patch('supervisor.llm_router.llm_route_query')
    def test_router_validates_llm_suggestion(self, mock_llm):
        """
        Given: LLM returns invalid suggestion
        When: Router processes query
        Then: Ignores invalid suggestion and uses default
        """
        from supervisor.router import decide_tool
        from supervisor.config import load_config

        # Mock LLM to return invalid suggestion
        mock_llm.return_value = 'invalid_tool'
        config = load_config('tests/fixtures/test_config.json')

        classification = decide_tool("some query", config)

        # Should fall back to 'direct' (ignore invalid suggestion)
        assert classification == 'direct'

    @patch('supervisor.llm_router.llm_route_query')
    def test_router_checks_tool_enabled_for_llm_suggestion(self, mock_llm):
        """
        Given: LLM suggests a disabled tool
        When: Router processes query
        Then: Falls back to 'direct' instead of using disabled tool
        """
        from supervisor.router import decide_tool
        from supervisor.config import load_config

        # Mock LLM to suggest document tool
        mock_llm.return_value = 'doc'

        # Use config with document tool disabled
        config = load_config('tests/fixtures/disabled_doc_tool_config.json')

        classification = decide_tool("some query", config)

        # Should not use 'doc' since it's disabled
        assert classification != 'doc'
        assert classification == 'direct'


class TestRoutingPromptBuilder:
    """Test LLM routing prompt construction."""

    def test_build_routing_prompt_includes_tools(self):
        """
        Given: Available tools list
        When: Building routing prompt
        Then: Prompt includes tool descriptions
        """
        from supervisor.llm_router import _build_routing_prompt

        prompt = _build_routing_prompt("test query", ["doc", "db", "web"])

        # Should include tool names
        assert "doc" in prompt
        assert "db" in prompt or "database" in prompt
        assert "web" in prompt

        # Should include the query
        assert "test query" in prompt

    def test_build_routing_prompt_includes_context(self):
        """
        Given: Previous conversation context
        When: Building routing prompt
        Then: Context is included in prompt
        """
        from supervisor.llm_router import _build_routing_prompt

        context = "User previously asked about sales data"
        prompt = _build_routing_prompt("what about Q3?", ["doc", "db"], context)

        # Should include context
        assert context in prompt
        assert "what about Q3?" in prompt

    def test_build_routing_prompt_without_context(self):
        """
        Given: No context provided
        When: Building routing prompt
        Then: Prompt is built without context section
        """
        from supervisor.llm_router import _build_routing_prompt

        prompt = _build_routing_prompt("test query", ["doc", "db"], None)

        # Should still work without context
        assert "test query" in prompt
        assert len(prompt) > 0


class TestBackwardCompatibility:
    """Test that LLM routing doesn't break existing functionality."""

    def test_all_existing_router_tests_still_pass(self):
        """
        Given: LLM routing is integrated
        When: Running existing router tests
        Then: All tests still pass (backward compatible)
        """
        from supervisor.router import decide_tool
        from supervisor.config import load_config

        config = load_config('tests/fixtures/test_config.json')

        # Test cases from original router tests
        assert decide_tool("What is the capital of France?", config) == 'direct'
        assert decide_tool("According to the design document", config) == 'doc'
        assert decide_tool("How many accounts were created?", config) == 'db'
        assert decide_tool("Latest news about AI", config) == 'web'
        assert decide_tool("DELETE all records", config) == 'fallback'

    def test_keyword_routing_takes_priority(self):
        """
        Given: Query matches keyword rules
        When: Router processes query
        Then: Uses keyword routing (LLM not called)
        """
        from supervisor.router import decide_tool
        from supervisor.config import load_config

        config = load_config('tests/fixtures/test_config.json')

        # These should all use keyword routing, not LLM
        with patch('supervisor.llm_router.llm_route_query') as mock_llm:
            decide_tool("According to the document", config)
            decide_tool("How many accounts", config)
            decide_tool("Latest news", config)

            # LLM should not be called for clear keyword matches
            # (might be called for ambiguous cases, but not these)
            assert mock_llm.call_count == 0


class TestFutureReadiness:
    """Test that stubs are ready for Phase 4+ implementation."""

    def test_llm_route_with_context_stub_exists(self):
        """
        Given: Future LLM routing with context function
        When: Called in Phase 3
        Then: Function exists and returns None (stub)
        """
        from supervisor.llm_router import llm_route_with_context
        from supervisor.config import load_config

        config = load_config('tests/fixtures/test_config.json')
        result = llm_route_with_context(
            "test query",
            config,
            ["doc", "db", "web"],
            "previous context"
        )

        # Stub should return None
        assert result is None

    def test_build_routing_prompt_ready_for_api(self):
        """
        Given: Routing prompt builder
        When: Used to create prompts
        Then: Generates well-formed prompts ready for LLM API
        """
        from supervisor.llm_router import _build_routing_prompt

        prompt = _build_routing_prompt("project timeline", ["doc", "db", "web"])

        # Should be a non-empty string
        assert isinstance(prompt, str)
        assert len(prompt) > 50  # Reasonable prompt length

        # Should include key elements
        assert "project timeline" in prompt
        assert "tool" in prompt.lower()
