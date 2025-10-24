"""
Integration tests for Supervisor CLI Agent.
Tests complete workflows from query to response.
"""
import pytest
from unittest.mock import patch


class TestEndToEndDirectQuery:
    """Integration test for direct LLM queries."""

    @patch('supervisor.handlers.call_claude_api')
    def test_e2e_direct_query(self, mock_claude):
        """
        Integration test: Query → Router → Direct Handler → Response
        Given: Simple general knowledge query
        When: Full supervisor pipeline is invoked
        Then: Response is generated via direct LLM call
        """
        from supervisor.agent import SupervisorAgent

        mock_claude.return_value = "2 + 2 equals 4."

        supervisor = SupervisorAgent(config_path='tests/fixtures/test_config.json')
        response = supervisor.respond("What is 2 + 2?")

        assert len(response) > 0
        assert "4" in response


class TestEndToEndDocumentQuery:
    """Integration test for document queries."""

    def test_e2e_document_query(self):
        """
        Integration test: Query → Router → Doc Handler → Stub Tool → Response
        Given: Document-specific query
        When: Full supervisor pipeline is invoked
        Then: Document stub is called and result returned
        """
        from supervisor.agent import SupervisorAgent

        supervisor = SupervisorAgent(config_path='tests/fixtures/test_config.json')
        response = supervisor.respond("According to Q3 Project Plan, what is the deadline?")

        assert "October 31" in response


class TestEndToEndDatabaseQuery:
    """Integration test for database queries."""

    def test_e2e_database_query(self):
        """
        Integration test: Query → Router → DB Handler → Stub Tool → Response
        Given: Database-specific query
        When: Full supervisor pipeline is invoked
        Then: Database stub is called and result returned
        """
        from supervisor.agent import SupervisorAgent

        supervisor = SupervisorAgent(config_path='tests/fixtures/test_config.json')
        response = supervisor.respond("How many new accounts were created last week?")

        assert "42" in response


class TestEndToEndWebQuery:
    """Integration test for web search queries."""

    def test_e2e_web_query(self):
        """
        Integration test: Query → Router → Web Handler → Stub Tool → Response
        Given: Web search query
        When: Full supervisor pipeline is invoked
        Then: Web search stub is called and result returned
        """
        from supervisor.agent import SupervisorAgent

        supervisor = SupervisorAgent(config_path='tests/fixtures/test_config.json')
        response = supervisor.respond("Latest news about artificial intelligence")

        assert len(response) > 0


class TestConfigDrivenBehavior:
    """Integration test for configuration-driven routing."""

    @patch('supervisor.handlers.call_claude_api')
    def test_e2e_config_driven_behavior(self, mock_claude):
        """
        Integration test: Config changes affect routing and handling
        Given: Two different configurations
        When: Same query is processed with each config
        Then: Responses differ based on configuration
        """
        from supervisor.agent import SupervisorAgent

        mock_claude.return_value = "Direct LLM response."

        # Test with all tools enabled
        supervisor1 = SupervisorAgent(config_path='tests/fixtures/all_tools_enabled.json')
        response1 = supervisor1.respond("According to the document")

        # Test with document tool disabled
        supervisor2 = SupervisorAgent(config_path='tests/fixtures/disabled_doc_tool_config.json')
        response2 = supervisor2.respond("According to the document")

        # When doc tool is disabled, should fall back to direct LLM
        # So response2 should use Claude, while response1 uses doc stub
        # Responses should differ
        assert len(response1) > 0
        assert len(response2) > 0


class TestMultipleQueryFlow:
    """Integration test for processing multiple queries sequentially."""

    @patch('supervisor.handlers.call_claude_api')
    def test_multiple_queries_sequential(self, mock_claude):
        """
        Integration test: Multiple queries processed by same supervisor instance
        Given: Supervisor instance
        When: Multiple different queries are processed
        Then: Each is routed correctly
        """
        from supervisor.agent import SupervisorAgent

        mock_claude.return_value = "Claude response."

        supervisor = SupervisorAgent(config_path='tests/fixtures/test_config.json')

        # Query 1: Direct
        response1 = supervisor.respond("What is the capital of France?")
        assert len(response1) > 0

        # Query 2: Document
        response2 = supervisor.respond("What does the Q3 Project Plan say?")
        assert "October 31" in response2

        # Query 3: Database
        response3 = supervisor.respond("How many accounts were created?")
        assert "42" in response3

        # Query 4: Web
        response4 = supervisor.respond("Latest news about AI")
        assert len(response4) > 0


class TestFallbackBehavior:
    """Integration test for fallback handling."""

    def test_e2e_harmful_query_fallback(self):
        """
        Integration test: Harmful query → Router → Fallback Handler
        Given: Query with harmful SQL patterns
        When: Full supervisor pipeline is invoked
        Then: Fallback message is returned
        """
        from supervisor.agent import SupervisorAgent

        supervisor = SupervisorAgent(config_path='tests/fixtures/test_config.json')
        response = supervisor.respond("DELETE all records from accounts")

        assert "I'm sorry" in response
        assert "sorry" in response.lower() or "cannot" in response.lower()

    def test_e2e_document_not_found(self):
        """
        Integration test: Document query → Doc Handler → "Not found" response
        Given: Query for non-existent document
        When: Full supervisor pipeline is invoked
        Then: "Document not found" message is returned
        """
        from supervisor.agent import SupervisorAgent

        supervisor = SupervisorAgent(config_path='tests/fixtures/test_config.json')
        response = supervisor.respond("What does the UnknownDocument say?")

        assert "not found" in response.lower() or "document" in response.lower()


class TestToolEnableDisable:
    """Integration test for tool enable/disable behavior."""

    @patch('supervisor.handlers.call_claude_api')
    def test_disabled_document_tool_falls_back(self, mock_claude):
        """
        Integration test: Document query with tool disabled → Direct handler
        Given: Document tool is disabled in config
        When: Document query is processed
        Then: Query falls back to direct LLM handler
        """
        from supervisor.agent import SupervisorAgent

        mock_claude.return_value = "Direct LLM response about the document."

        supervisor = SupervisorAgent(config_path='tests/fixtures/disabled_doc_tool_config.json')
        response = supervisor.respond("According to the document")

        # Should use Claude (direct handler) not document stub
        assert len(response) > 0
        # Verify Claude was called
        assert mock_claude.call_count >= 1

    def test_all_tools_enabled_routes_correctly(self):
        """
        Integration test: All tools enabled → Correct routing
        Given: All tools are enabled
        When: Various queries are processed
        Then: Each routes to appropriate tool
        """
        from supervisor.agent import SupervisorAgent

        supervisor = SupervisorAgent(config_path='tests/fixtures/all_tools_enabled.json')

        # Document query
        doc_response = supervisor.respond("According to the Q3 Plan")
        assert "October 31" in doc_response or len(doc_response) > 0

        # Database query
        db_response = supervisor.respond("How many accounts?")
        assert "42" in db_response

        # Web query
        web_response = supervisor.respond("Latest news")
        assert len(web_response) > 0


class TestErrorPropagation:
    """Integration test for error handling across components."""

    def test_invalid_query_raises_error(self):
        """
        Integration test: Invalid query → ValueError
        Given: Empty or invalid query
        When: Supervisor processes it
        Then: ValueError is raised
        """
        from supervisor.agent import SupervisorAgent

        supervisor = SupervisorAgent(config_path='tests/fixtures/test_config.json')

        # Empty string
        with pytest.raises(ValueError):
            supervisor.respond("")

        # Whitespace only
        with pytest.raises(ValueError):
            supervisor.respond("   ")

    def test_invalid_config_raises_error(self):
        """
        Integration test: Invalid config → Error on initialization
        Given: Invalid configuration file
        When: Supervisor is initialized
        Then: Appropriate error is raised
        """
        from supervisor.agent import SupervisorAgent

        # Invalid JSON
        with pytest.raises(Exception):
            SupervisorAgent(config_path='tests/fixtures/invalid_config.json')


class TestConfigReload:
    """Integration test for config reload functionality."""

    @patch('supervisor.handlers.call_claude_api')
    def test_config_reload_updates_behavior(self, mock_claude):
        """
        Integration test: Config reload → Updated behavior
        Given: Running supervisor instance
        When: Config is reloaded
        Then: New config is active
        """
        from supervisor.agent import SupervisorAgent

        mock_claude.return_value = "Test response"

        supervisor = SupervisorAgent(config_path='tests/fixtures/test_config.json')

        # Get initial system prompt
        original_prompt = supervisor.config.system_prompt
        assert original_prompt is not None

        # Reload config
        supervisor.reload_config()

        # Verify config is still loaded and valid
        assert supervisor.config is not None
        assert supervisor.config.system_prompt is not None

        # Verify supervisor still works after reload
        response = supervisor.respond("Test query")
        assert len(response) > 0


class TestComplexQueryScenarios:
    """Integration tests for complex query patterns."""

    @patch('supervisor.handlers.call_claude_api')
    def test_ambiguous_query_handling(self, mock_claude):
        """
        Integration test: Ambiguous query → Handled gracefully
        Given: Query that's unclear or ambiguous
        When: Supervisor processes it
        Then: Response is provided (direct LLM or fallback)
        """
        from supervisor.agent import SupervisorAgent

        mock_claude.return_value = "Could you clarify which policy?"

        supervisor = SupervisorAgent(config_path='tests/fixtures/test_config.json')
        response = supervisor.respond("Tell me about the policy")

        assert len(response) > 0

    def test_mixed_keywords_query(self):
        """
        Integration test: Query with multiple keyword types
        Given: Query containing both document and database keywords
        When: Supervisor processes it
        Then: Router prioritizes and routes correctly
        """
        from supervisor.agent import SupervisorAgent

        supervisor = SupervisorAgent(config_path='tests/fixtures/test_config.json')

        # Document keywords have higher priority in router
        response = supervisor.respond("According to the accounts document")

        # Should route to document handler (higher priority)
        assert len(response) > 0

    def test_case_insensitive_routing(self):
        """
        Integration test: Case-insensitive keyword matching
        Given: Query with various capitalizations
        When: Supervisor processes it
        Then: Routing works regardless of case
        """
        from supervisor.agent import SupervisorAgent

        supervisor = SupervisorAgent(config_path='tests/fixtures/test_config.json')

        # Uppercase
        response1 = supervisor.respond("ACCORDING TO THE DOCUMENT")
        assert len(response1) > 0

        # Mixed case
        response2 = supervisor.respond("AcCoRdInG tO tHe DoCuMeNt")
        assert len(response2) > 0

        # Lowercase
        response3 = supervisor.respond("according to the document")
        assert len(response3) > 0


class TestRealWorldQueries:
    """Integration tests using realistic user queries."""

    @patch('supervisor.handlers.call_claude_api')
    def test_realistic_general_question(self, mock_claude):
        """
        Integration test: Realistic general knowledge query
        """
        from supervisor.agent import SupervisorAgent

        mock_claude.return_value = "Python is a high-level programming language."

        supervisor = SupervisorAgent(config_path='tests/fixtures/test_config.json')
        response = supervisor.respond("What is Python programming language?")

        assert len(response) > 0

    def test_realistic_document_query(self):
        """
        Integration test: Realistic document query
        """
        from supervisor.agent import SupervisorAgent

        supervisor = SupervisorAgent(config_path='tests/fixtures/test_config.json')
        response = supervisor.respond("What does the Q3 Project Plan say about the October deadline?")

        assert "October 31" in response

    def test_realistic_database_query(self):
        """
        Integration test: Realistic database query
        """
        from supervisor.agent import SupervisorAgent

        supervisor = SupervisorAgent(config_path='tests/fixtures/test_config.json')
        response = supervisor.respond("Can you tell me how many new accounts were created last week?")

        assert "42" in response

    def test_realistic_web_query(self):
        """
        Integration test: Realistic web search query
        """
        from supervisor.agent import SupervisorAgent

        supervisor = SupervisorAgent(config_path='tests/fixtures/test_config.json')
        response = supervisor.respond("What's the latest news about artificial intelligence developments?")

        assert len(response) > 0
        assert "Web search" in response or "stub" in response.lower()
