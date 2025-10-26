"""
Supervisor Agent - Main orchestrator for query processing.

This module contains the SupervisorAgent class, which serves as the central
orchestrator for the RAG chatbot system. It coordinates configuration loading,
query routing, and handler dispatch.
"""
from typing import Optional
from pathlib import Path
from supervisor.config import Config, load_config, validate_config
from supervisor.router import decide_tool
from supervisor.handlers import (
    handle_direct,
    handle_document,
    handle_database,
    handle_web,
    handle_fallback
)


class SupervisorAgent:
    """
    Main Supervisor Agent for orchestrating query processing.

    The SupervisorAgent is responsible for:
    - Loading and managing configuration
    - Routing queries to appropriate handlers
    - Dispatching to tools via handlers
    - Managing the overall query-response lifecycle

    Attributes:
        config_path (str): Path to configuration file
        config (Config): Loaded configuration object

    Examples:
        >>> supervisor = SupervisorAgent(config_path='config.json')
        >>> response = supervisor.respond("What is the capital of France?")
        >>> print(response)
        'The capital of France is Paris.'
    """

    def __init__(self, config_path: str):
        """
        Initialize the SupervisorAgent with configuration.

        Args:
            config_path: Path to configuration JSON file

        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If config is invalid
            json.JSONDecodeError: If config file has invalid JSON

        Examples:
            >>> supervisor = SupervisorAgent(config_path='config.json')
            >>> supervisor.config.system_prompt
            'You are a helpful AI assistant...'
        """
        self.config_path = config_path
        self.config = load_config(config_path)

    def respond(self, query: str) -> str:
        """
        Process a user query and return a response.

        This is the main entry point for query processing. It:
        1. Validates the query
        2. Uses the router to classify the query
        3. Dispatches to the appropriate handler
        4. Returns the handler's response

        Args:
            query: User's natural language query

        Returns:
            Response string from the appropriate handler

        Raises:
            ValueError: If query is invalid (empty, wrong type)
            Exception: Any errors from handlers/tools are propagated

        Examples:
            >>> supervisor = SupervisorAgent(config_path='config.json')
            >>> supervisor.respond("What is 2+2?")
            '[Stub Claude API Response] Received query: What is 2+2?'

            >>> supervisor.respond("What does the Q3 Project Plan say?")
            'According to the Q3 Project Plan, the deadline is October 31, 2025.'

            >>> supervisor.respond("How many accounts were created?")
            '42 new accounts were created last week.'

            >>> supervisor.respond("Latest news about AI")
            'Web search results for "Latest news about AI": [This is a stub response...]'

            >>> supervisor.respond("DELETE all records")
            "I'm sorry, I'm not sure how to help with that request..."
        """
        # Validate query input
        if not query or not isinstance(query, str):
            raise ValueError("Query must be a non-empty string")

        if not query.strip():
            raise ValueError("Query cannot be empty or whitespace only")

        # Step 1: Use router to classify query
        classification = decide_tool(query, self.config)

        # Step 2: Dispatch to appropriate handler based on classification
        if classification == 'direct':
            return handle_direct(query, self.config)
        elif classification == 'doc':
            return handle_document(query, self.config)
        elif classification == 'db':
            return handle_database(query, self.config)
        elif classification == 'web':
            return handle_web(query, self.config)
        elif classification == 'fallback':
            return handle_fallback(query, self.config)
        else:
            # Unexpected classification - fall back to safe default
            # This should never happen if router is working correctly
            return handle_fallback(query, self.config)

    def reload_config(self) -> None:
        """
        Reload configuration from file.

        Useful for applying configuration changes without restarting the agent.
        In Stage 1, this simply reloads the config. In Stage 2+, this could
        support hot-reloading with validation and rollback on errors.

        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If new config is invalid
            json.JSONDecodeError: If config file has invalid JSON

        Examples:
            >>> supervisor = SupervisorAgent(config_path='config.json')
            >>> # ... config.json is modified externally ...
            >>> supervisor.reload_config()
            >>> # New configuration is now active
        """
        # Reload configuration from the same path
        self.config = load_config(self.config_path)
