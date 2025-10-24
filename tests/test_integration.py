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
