"""
Stub implementations of MCP tools for Stage 1 development.

These stubs simulate real tool behavior with mock data to enable TDD development
without requiring actual MCP tool implementations. They will be replaced with
real tool implementations in Stage 2.
"""
from typing import Optional


def stub_document_retriever(query: str) -> str:
    """
    Mock document retrieval tool.

    Simulates retrieving information from internal documents. In Stage 1,
    this returns hardcoded responses based on query keywords. In Stage 2+,
    this will be replaced with real vector DB retrieval.

    Args:
        query: Natural language query about documents

    Returns:
        Mock document content or "not found" message

    Raises:
        ValueError: If query is empty or invalid
        Exception: On stub errors

    Examples:
        >>> stub_document_retriever("What does the Q3 Project Plan say?")
        'According to the Q3 Project Plan, the deadline is October 31, 2025.'

        >>> stub_document_retriever("What does the NonExistent Plan say?")
        'No relevant documents found.'
    """
    if not query or not isinstance(query, str):
        raise ValueError("Query must be a non-empty string")

    if not query.strip():
        raise ValueError("Query cannot be empty or whitespace only")

    query_lower = query.lower()

    # Check for Q3 Project Plan queries
    if "q3 project plan" in query_lower:
        return "According to the Q3 Project Plan, the deadline is October 31, 2025."

    # Check for other known documents (can be extended)
    if "design document" in query_lower or "design doc" in query_lower:
        return "The design document specifies the authentication flow requirements."

    # Default: document not found
    return "Document not found."


def stub_database_query(query: str) -> str:
    """
    Mock database query tool (text-to-SQL).

    Simulates querying structured databases using natural language. In Stage 1,
    returns hardcoded responses. In Stage 2+, will implement real text-to-SQL
    and database execution.

    Args:
        query: Natural language query about data

    Returns:
        Mock query results or "no data" message

    Raises:
        ValueError: If query is empty or invalid
        Exception: On stub errors

    Examples:
        >>> stub_database_query("How many accounts were created?")
        '42 new accounts were created last week.'

        >>> stub_database_query("What is the temperature?")
        'No data available for this query.'
    """
    if not query or not isinstance(query, str):
        raise ValueError("Query must be a non-empty string")

    if not query.strip():
        raise ValueError("Query cannot be empty or whitespace only")

    query_lower = query.lower()

    # Check for accounts/sales queries
    if "account" in query_lower:
        return "42 new accounts were created last week."

    if "sales" in query_lower or "revenue" in query_lower:
        return "Total sales revenue for Q3 is $1.2M."

    # Default: no data found
    return "No data available for this query."


def stub_web_search(query: str) -> str:
    """
    Mock web search tool.

    Simulates searching the web for current information. In Stage 1, returns
    a mock search response. In Stage 2+, will implement real web search API
    integration (Bing, Google, etc.).

    Args:
        query: Natural language search query

    Returns:
        Mock web search results

    Raises:
        ValueError: If query is empty or invalid
        Exception: On stub errors

    Examples:
        >>> stub_web_search("Latest news about AI")
        'Web search results for "Latest news about AI": [This is a stub response]...'
    """
    if not query or not isinstance(query, str):
        raise ValueError("Query must be a non-empty string")

    if not query.strip():
        raise ValueError("Query cannot be empty or whitespace only")

    # Return mock web search results
    return (
        f'Web search results for "{query}": '
        f'[This is a stub response. In Stage 2, this will connect to real web search APIs.]'
    )
