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
from supervisor.tools.mcp_doc_tool import create_document_tool
from supervisor.tools.mcp_db_tool import create_database_tool
import os
import logging

# Set up logging
logger = logging.getLogger(__name__)

# Try to import Anthropic SDK (optional dependency)
try:
    from anthropic import Anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    logger.debug("Anthropic SDK not installed. Using stub responses for direct queries.")


def call_claude_api(system_prompt: str, user_message: str) -> str:
    """
    Call Claude API to get a response.

    If ANTHROPIC_API_KEY and CLAUDE_RUNTIME_MODEL are set in environment,
    calls the real Claude API. Otherwise, falls back to stub response.

    Args:
        system_prompt: System prompt to set LLM behavior
        user_message: User's query

    Returns:
        LLM response string (from Claude API or stub)

    Raises:
        ValueError: If inputs are invalid
        Exception: On API errors

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

    # Check if Anthropic SDK is available and API key is set
    api_key = os.getenv("ANTHROPIC_API_KEY")
    model = os.getenv("CLAUDE_RUNTIME_MODEL", "claude-3-5-haiku-20241022")

    if ANTHROPIC_AVAILABLE and api_key:
        try:
            # Call real Claude API
            client = Anthropic(api_key=api_key)

            response = client.messages.create(
                model=model,
                max_tokens=1024,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_message}
                ]
            )

            # Extract text from response
            return response.content[0].text

        except Exception as e:
            # Log error and fall back to stub
            logger.warning(f"Claude API call failed: {e}. Falling back to stub response.")
            return f"[Stub Claude API Response] Received query: {user_message}"
    else:
        # Fall back to stub if API key missing or SDK unavailable
        if not ANTHROPIC_AVAILABLE:
            logger.debug("Anthropic SDK not available. Using stub response.")
        elif not api_key:
            logger.debug("ANTHROPIC_API_KEY not set. Using stub response.")

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

    # Call document retrieval MCP tool
    doc_tool = create_document_tool()
    result = doc_tool(query)

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

    # Call database query MCP tool
    db_tool = create_database_tool()
    result = db_tool(query)

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
