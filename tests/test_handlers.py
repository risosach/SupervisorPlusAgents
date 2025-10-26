"""
Tests for handler functions.
Tests each handler type: direct, document, database, web, fallback.
"""
import pytest
from unittest.mock import patch, MagicMock


class TestDirectHandler:
    """Test direct LLM handler."""

    @patch('supervisor.handlers.call_claude_api')
    def test_handle_direct_calls_claude(self, mock_claude):
        """
        Given: A query for direct LLM handling
        When: handle_direct is called
        Then: Claude API is invoked with system prompt and query
        """
        from supervisor.handlers import handle_direct
        from supervisor.config import load_config

        mock_claude.return_value = "The capital of France is Paris."
        config = load_config('tests/fixtures/test_config.json')

        result = handle_direct("What is the capital of France?", config)

        assert mock_claude.call_count == 1
        assert "Paris" in result

    @patch('supervisor.handlers.call_claude_api')
    def test_handle_direct_error_handling(self, mock_claude):
        """
        Given: Claude API raises an error
        When: handle_direct is called
        Then: Error is handled gracefully
        """
        from supervisor.handlers import handle_direct
        from supervisor.config import load_config

        mock_claude.side_effect = Exception("API Error")
        config = load_config('tests/fixtures/test_config.json')

        # Should either raise or return error message
        with pytest.raises(Exception):
            handle_direct("test query", config)


class TestDocumentHandler:
    """Test document retrieval handler."""

    def test_handle_document_calls_stub(self):
        """
        Given: A document query
        When: handle_document is called
        Then: Document stub is invoked and result returned
        """
        from supervisor.handlers import handle_document
        from supervisor.config import load_config

        config = load_config('tests/fixtures/test_config.json')
        result = handle_document("What does the Q3 Project Plan say?", config)

        assert "October 31" in result

    def test_handle_document_not_found(self):
        """
        Given: Query for non-existent document
        When: handle_document is called
        Then: "not found" message is returned
        """
        from supervisor.handlers import handle_document
        from supervisor.config import load_config

        config = load_config('tests/fixtures/test_config.json')
        result = handle_document("What does the NonExistent Plan say?", config)

        assert "not found" in result.lower()


class TestDatabaseHandler:
    """Test database query handler."""

    def test_handle_database_calls_stub(self):
        """
        Given: A database query
        When: handle_database is called
        Then: Database stub is invoked and result returned
        """
        from supervisor.handlers import handle_database
        from supervisor.config import load_config

        config = load_config('tests/fixtures/test_config.json')
        result = handle_database("How many accounts were created?", config)

        assert "42" in result

    @patch('supervisor.tools.mcp_db_tool.server.query_database')
    def test_handle_database_error_handling(self, mock_db):
        """
        Given: Database query that fails
        When: handle_database is called
        Then: Error is handled gracefully with error message
        """
        from supervisor.handlers import handle_database
        from supervisor.config import load_config

        mock_db.return_value = "Database error: Connection failed"
        config = load_config('tests/fixtures/test_config.json')

        # Should handle error gracefully by returning error message
        result = handle_database("test query", config)
        assert "error" in result.lower() or "database" in result.lower()


class TestWebHandler:
    """Test web search handler."""

    def test_handle_web_calls_stub(self):
        """
        Given: A web search query
        When: handle_web is called
        Then: Web search stub is invoked and result returned
        """
        from supervisor.handlers import handle_web
        from supervisor.config import load_config

        config = load_config('tests/fixtures/test_config.json')
        result = handle_web("Latest news about AI", config)

        assert len(result) > 0

    @patch('supervisor.tools.stubs.stub_web_search')
    def test_handle_web_error_handling(self, mock_web):
        """
        Given: Web search that fails
        When: handle_web is called
        Then: Error is handled gracefully
        """
        from supervisor.handlers import handle_web
        from supervisor.config import load_config

        mock_web.side_effect = Exception("Network Error")
        config = load_config('tests/fixtures/test_config.json')

        # Should handle error gracefully
        with pytest.raises(Exception):
            handle_web("test query", config)


class TestFallbackHandler:
    """Test fallback handler."""

    def test_handle_fallback_returns_message(self):
        """
        Given: Any query requiring fallback
        When: handle_fallback is called
        Then: Fallback message from config is returned
        """
        from supervisor.handlers import handle_fallback
        from supervisor.config import load_config

        config = load_config('tests/fixtures/test_config.json')
        result = handle_fallback("invalid query", config)

        assert "I'm sorry" in result
        assert result == config.fallback_message
