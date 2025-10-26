"""
Tests for stub MCP tool implementations.
These stubs simulate real tool behavior for Stage 1.
"""
import pytest


class TestDocumentRetrieverStub:
    """Test stub document retriever functionality."""

    def test_stub_document_retriever_q3_plan(self):
        """
        Given: Query mentioning "Q3 Project Plan"
        When: Stub document retriever is called
        Then: Returns mock data about October 31 deadline
        """
        from supervisor.tools.stubs import stub_document_retriever

        result = stub_document_retriever("What does the Q3 Project Plan say about milestones?")

        assert "October 31" in result

    def test_stub_document_retriever_not_found(self):
        """
        Given: Query for non-existent document
        When: Stub document retriever is called
        Then: Returns "not found" message
        """
        from supervisor.tools.stubs import stub_document_retriever

        result = stub_document_retriever("What does the NonExistent Plan say?")

        assert "not found" in result.lower()


class TestDatabaseQueryStub:
    """Test stub database query functionality."""

    def test_stub_database_query_accounts(self):
        """
        Given: Query about accounts created
        When: Stub database query is called
        Then: Returns "42 new accounts"
        """
        from supervisor.tools.stubs import stub_database_query

        result = stub_database_query("How many new accounts were created last week?")

        assert "42" in result

    def test_stub_database_query_no_data(self):
        """
        Given: Query with no matching stub data
        When: Stub database query is called
        Then: Returns "no data available" message
        """
        from supervisor.tools.stubs import stub_database_query

        result = stub_database_query("What is the average temperature?")

        assert "no data" in result.lower() or "not available" in result.lower()


class TestWebSearchStub:
    """Test stub web search functionality."""

    def test_stub_web_search_returns_result(self):
        """
        Given: Any web search query
        When: Stub web search is called
        Then: Returns stub search results message
        """
        from supervisor.tools.stubs import stub_web_search

        result = stub_web_search("Latest news about AI")

        assert len(result) > 0
        # Stub should indicate it's mock data
        assert "stub" in result.lower() or "search" in result.lower()
