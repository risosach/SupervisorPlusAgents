"""
Decision router for Supervisor CLI Agent.

This module implements query classification logic to route user queries
to the appropriate handler (direct LLM, document retrieval, database query,
web search, or fallback).
"""
from typing import List
from supervisor.config import Config


def decide_tool(query: str, config: Config) -> str:
    """
    Classify a query and decide which tool/handler should process it.

    Uses keyword-based classification with the following priority:
    1. Harmful patterns → "fallback" (security)
    2. Document keywords → "doc" (if enabled)
    3. Database keywords → "db" (if enabled)
    4. Web keywords → "web" (if enabled)
    5. Default → "direct" (general LLM)

    Args:
        query: User's natural language query
        config: Configuration object containing routing rules

    Returns:
        One of: "direct", "doc", "db", "web", or "fallback"

    Raises:
        ValueError: If query is empty or not a string
        TypeError: If config is not a Config object

    Examples:
        >>> config = load_config('config.json')
        >>> decide_tool("What is the capital of France?", config)
        'direct'
        >>> decide_tool("According to the Q3 Project Plan", config)
        'doc'
        >>> decide_tool("How many accounts were created?", config)
        'db'
        >>> decide_tool("Latest news about AI", config)
        'web'
        >>> decide_tool("DELETE all records", config)
        'fallback'
    """
    # Input validation
    if not isinstance(query, str):
        raise TypeError(f"Query must be a string, got {type(query).__name__}")

    if not query or not query.strip():
        raise ValueError("Query cannot be empty or whitespace only")

    if not isinstance(config, Config):
        raise TypeError(f"Config must be a Config object, got {type(config).__name__}")

    # Normalize query for case-insensitive matching
    query_lower = query.lower()

    # Priority 1: Check for harmful patterns (security first!)
    harmful_patterns = config.routing_rules.get('harmful_patterns', [])
    if _contains_harmful_pattern(query_lower, harmful_patterns):
        return 'fallback'

    # Priority 2: Check for document-related queries
    document_keywords = config.routing_rules.get('document_keywords', [])
    if _matches_keywords(query_lower, document_keywords):
        if config.is_tool_enabled('document_retriever'):
            return 'doc'
        # If tool disabled, continue to next category

    # Priority 3: Check for database queries
    database_keywords = config.routing_rules.get('database_keywords', [])
    if _matches_keywords(query_lower, database_keywords):
        if config.is_tool_enabled('database_query'):
            return 'db'
        # If tool disabled, continue to next category

    # Priority 4: Check for web search queries
    web_keywords = config.routing_rules.get('web_keywords', [])
    if _matches_keywords(query_lower, web_keywords):
        if config.is_tool_enabled('web_search'):
            return 'web'
        # If tool disabled, continue to next category

    # Default: Direct LLM handling
    return 'direct'


def _matches_keywords(query_lower: str, keywords: List[str]) -> bool:
    """
    Check if query contains any of the specified keywords.

    Args:
        query_lower: Query in lowercase
        keywords: List of keywords to check (will be lowercased)

    Returns:
        True if any keyword is found in the query
    """
    if not keywords:
        return False

    for keyword in keywords:
        if keyword.lower() in query_lower:
            return True

    return False


def _contains_harmful_pattern(query_lower: str, harmful_patterns: List[str]) -> bool:
    """
    Check if query contains harmful SQL or command patterns.

    Args:
        query_lower: Query in lowercase
        harmful_patterns: List of harmful patterns to detect

    Returns:
        True if any harmful pattern is detected
    """
    if not harmful_patterns:
        return False

    for pattern in harmful_patterns:
        # Check for pattern as a separate word (not part of another word)
        pattern_lower = pattern.lower()

        # Simple word boundary check
        # Look for pattern surrounded by spaces or at start/end
        if f' {pattern_lower} ' in f' {query_lower} ':
            return True

    return False
