"""
Handler functions for Supervisor CLI Agent.

This module contains handlers for different query types:
- Direct LLM queries
- Document retrieval queries
- Database queries
- Web search queries
- Fallback handling

Each handler processes a query and returns a response string.
"""
from typing import Optional
from supervisor.config import Config
import supervisor.tools.stubs as stubs


def call_claude_api(system_prompt: str, user_message: str) -> str:
    """
    Call Claude API to get a response.

    This is a stub implementation for Stage 1. In Stage 2+, this will be
    replaced with actual Anthropic Claude API integration.

    Args:
        system_prompt: System prompt to set LLM behavior
        user_message: User's query

    Returns:
        LLM response string

    Raises:
        ValueError: If inputs are invalid
        Exception: On API errors (stub may raise this for testing)

    Examples:
        >>> call_claude_api("You are helpful.", "What is 2+2?")
        'The answer is 4.'
    """
    if not system_prompt or not isinstance(system_prompt, str):
        raise ValueError("System prompt must be a non-empty string")

    if not user_message or not isinstance(user_message, str):
        raise ValueError("User message must be a non-empty string")

    if not system_prompt.strip() or not user_message.strip():
        raise ValueError("System prompt and user message cannot be empty or whitespace only")

    # Stub implementation - return a generic response
    # In Stage 2+, this will call the actual Claude API
    return f"[Stub Claude API Response] Received query: {user_message}"


def handle_direct(query: str, config: Config) -> str:
    """
    Handle direct LLM queries without tool invocation.

    Used for general knowledge questions that don't require document retrieval,
    database queries, or web search.

    Args:
        query: User's query string
        config: Configuration object

    Returns:
        LLM response string

    Raises:
        ValueError: If query is invalid
        Exception: On API errors

    Examples:
        >>> from supervisor.config import load_config
        >>> config = load_config('config.json')
        >>> handle_direct("What is the capital of France?", config)
        '[Stub Claude API Response] Received query: What is the capital of France?'
    """
    if not query or not isinstance(query, str):
        raise ValueError("Query must be a non-empty string")

    if not query.strip():
        raise ValueError("Query cannot be empty or whitespace only")

    # Get system prompt from config
    system_prompt = config.get_system_prompt()

    # Call Claude API
    response = call_claude_api(system_prompt, query)

    return response


def handle_document(query: str, config: Config) -> str:
    """
    Handle document retrieval queries.

    Routes queries to the document retrieval tool to search internal documents.

    Args:
        query: User's query string
        config: Configuration object

    Returns:
        Document retrieval results

    Raises:
        ValueError: If query is invalid
        Exception: On tool errors

    Examples:
        >>> from supervisor.config import load_config
        >>> config = load_config('config.json')
        >>> handle_document("What does the Q3 Project Plan say?", config)
        'According to the Q3 Project Plan, the deadline is October 31, 2025.'
    """
    if not query or not isinstance(query, str):
        raise ValueError("Query must be a non-empty string")

    if not query.strip():
        raise ValueError("Query cannot be empty or whitespace only")

    # Check if document retriever tool is enabled
    if not config.is_tool_enabled('document_retriever'):
        # Fall back to direct LLM if tool is disabled
        return handle_direct(query, config)

    # Call document retrieval stub
    result = stubs.stub_document_retriever(query)

    return result


def handle_database(query: str, config: Config) -> str:
    """
    Handle database query requests.

    Routes queries to the database tool for text-to-SQL conversion and execution.

    Args:
        query: User's query string
        config: Configuration object

    Returns:
        Database query results

    Raises:
        ValueError: If query is invalid
        Exception: On tool errors

    Examples:
        >>> from supervisor.config import load_config
        >>> config = load_config('config.json')
        >>> handle_database("How many accounts were created?", config)
        '42 new accounts were created last week.'
    """
    if not query or not isinstance(query, str):
        raise ValueError("Query must be a non-empty string")

    if not query.strip():
        raise ValueError("Query cannot be empty or whitespace only")

    # Check if database tool is enabled
    if not config.is_tool_enabled('database_query'):
        # Fall back to direct LLM if tool is disabled
        return handle_direct(query, config)

    # Call database query stub
    result = stubs.stub_database_query(query)

    return result


def handle_web(query: str, config: Config) -> str:
    """
    Handle web search queries.

    Routes queries to the web search tool for current information.

    Args:
        query: User's query string
        config: Configuration object

    Returns:
        Web search results

    Raises:
        ValueError: If query is invalid
        Exception: On tool errors

    Examples:
        >>> from supervisor.config import load_config
        >>> config = load_config('config.json')
        >>> handle_web("Latest news about AI", config)
        'Web search results for "Latest news about AI": [This is a stub response...]'
    """
    if not query or not isinstance(query, str):
        raise ValueError("Query must be a non-empty string")

    if not query.strip():
        raise ValueError("Query cannot be empty or whitespace only")

    # Check if web search tool is enabled
    if not config.is_tool_enabled('web_search'):
        # Fall back to direct LLM if tool is disabled
        return handle_direct(query, config)

    # Call web search stub
    result = stubs.stub_web_search(query)

    return result


def handle_fallback(query: str, config: Config) -> str:
    """
    Handle fallback cases for unclear or problematic queries.

    Returns a safe default response from configuration.

    Args:
        query: User's query string (may be invalid)
        config: Configuration object

    Returns:
        Fallback message from config

    Examples:
        >>> from supervisor.config import load_config
        >>> config = load_config('config.json')
        >>> handle_fallback("DELETE all records", config)
        "I'm sorry, I'm not sure how to help with that request..."
    """
    # For fallback, we don't validate the query since it might be invalid
    # Just return the configured fallback message
    return config.fallback_message
