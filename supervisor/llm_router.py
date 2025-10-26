"""
LLM-based routing fallback for Supervisor CLI Agent.

This module provides intelligent routing when keyword-based classification
is ambiguous or uncertain. It uses an LLM to analyze the query and suggest
the most appropriate tool.
"""

import os
import logging
from typing import Optional
from supervisor.config import Config

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()  # Load .env from project root
except ImportError:
    pass  # dotenv not installed, rely on system environment variables

# Set up logging
logger = logging.getLogger(__name__)

# Try to import Anthropic SDK (optional dependency)
try:
    from anthropic import Anthropic, APIError, APIConnectionError, APITimeoutError
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    logger.warning("Anthropic SDK not installed. LLM routing will be disabled.")

# Try to import OpenAI SDK for future hybrid routing (optional)
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


def llm_route_query(query: str, config: Config) -> Optional[str]:
    """
    Use LLM to determine the best tool/handler for an ambiguous query.

    This function is called when keyword-based routing is inconclusive.
    It prompts an LLM (Claude) to analyze the query intent and recommend a tool.

    Args:
        query: User's natural language query
        config: Configuration object

    Returns:
        One of: "direct", "doc", "db", "web", or None if uncertain/error

    Raises:
        ValueError: If query is empty or invalid

    Examples:
        >>> config = load_config('config.json')
        >>> llm_route_query("Tell me about the project timeline", config)
        'doc'  # Claude recognizes this should check documents
    """
    # Input validation
    if not query or not isinstance(query, str):
        raise ValueError("Query must be a non-empty string")

    if not query.strip():
        raise ValueError("Query cannot be empty or whitespace only")

    # Check if LLM routing is enabled in config
    if not config.routing_rules.get('enable_llm_fallback', False):
        return None

    # Check if Anthropic SDK is available
    if not ANTHROPIC_AVAILABLE:
        logger.debug("Anthropic SDK not available, skipping LLM routing")
        return None

    # Get available tools from config
    available_tools = []
    if config.is_tool_enabled('document_retriever'):
        available_tools.append('doc')
    if config.is_tool_enabled('database_query'):
        available_tools.append('db')
    if config.is_tool_enabled('web_search'):
        available_tools.append('web')
    available_tools.append('direct')  # Always available

    # Build routing prompt
    prompt = _build_routing_prompt(query, available_tools)

    # Call Claude API
    try:
        suggestion = _call_llm_for_routing(prompt, config)
        if suggestion and suggestion in ['direct', 'doc', 'db', 'web']:
            logger.info(f"LLM routing suggested: {suggestion} for query: {query[:50]}...")
            return suggestion
        else:
            logger.debug(f"LLM routing returned invalid suggestion: {suggestion}")
            return None
    except Exception as e:
        logger.error(f"LLM routing failed: {e}")
        return None


def llm_route_with_context(
    query: str,
    config: Config,
    available_tools: list[str],
    previous_context: Optional[str] = None
) -> Optional[str]:
    """
    Advanced LLM routing with context awareness.

    This function provides more sophisticated routing by:
    - Considering which tools are actually enabled
    - Taking into account previous conversation context
    - Using a more detailed prompt for better accuracy

    Args:
        query: User's natural language query
        config: Configuration object
        available_tools: List of enabled tool names (e.g., ["doc", "db", "web"])
        previous_context: Optional conversation history for context

    Returns:
        One of the available tool names, "direct", or None if uncertain

    Raises:
        ValueError: If query is empty or invalid

    Examples:
        >>> config = load_config('config.json')
        >>> available_tools = ["doc", "db", "web"]
        >>> llm_route_with_context("project timeline", config, available_tools)
        'doc'  # Claude recognizes document-related query
    """
    # Input validation
    if not query or not isinstance(query, str):
        raise ValueError("Query must be a non-empty string")

    if not query.strip():
        raise ValueError("Query cannot be empty or whitespace only")

    if not available_tools:
        return None

    # Check if LLM routing is enabled
    if not config.routing_rules.get('enable_llm_fallback', False):
        return None

    # Check if Anthropic SDK is available
    if not ANTHROPIC_AVAILABLE:
        logger.debug("Anthropic SDK not available, skipping context-aware LLM routing")
        return None

    # Build detailed routing prompt with context
    prompt = _build_routing_prompt(query, available_tools, previous_context)

    # Call Claude API
    try:
        suggestion = _call_llm_for_routing(prompt, config)
        if suggestion and suggestion in available_tools + ['direct']:
            logger.info(f"Context-aware LLM routing suggested: {suggestion}")
            return suggestion
        else:
            logger.debug(f"Context-aware LLM routing returned invalid suggestion: {suggestion}")
            return None
    except Exception as e:
        logger.error(f"Context-aware LLM routing failed: {e}")
        return None


def _build_routing_prompt(query: str, available_tools: list[str], context: Optional[str] = None) -> str:
    """
    Build a prompt for LLM-based routing.

    This helper function constructs a clear, structured prompt that asks
    the LLM to classify the query intent and suggest the best tool.

    Args:
        query: User's query to classify
        available_tools: List of enabled tool names
        context: Optional conversation context

    Returns:
        Formatted prompt string for LLM

    Examples:
        >>> prompt = _build_routing_prompt("project deadline", ["doc", "db"])
        >>> "document" in prompt
        True
    """
    prompt = f"""You are a query routing assistant. Your job is to analyze user queries and recommend the best tool to handle them.

Available tools:
"""

    # Add tool descriptions
    tool_descriptions = {
        "doc": "document_retriever - Search internal documents, files, and knowledge base",
        "db": "database_query - Query structured databases for metrics, counts, and analytics",
        "web": "web_search - Search the internet for current information and news",
        "direct": "direct_llm - General knowledge questions that don't require tools"
    }

    for tool in available_tools:
        if tool in tool_descriptions:
            prompt += f"- {tool_descriptions[tool]}\n"

    # Add context if available
    if context:
        prompt += f"\nPrevious conversation context:\n{context}\n"

    # Add the query to classify
    prompt += f"""
User query: "{query}"

Based on the query, which tool should handle this? Respond with ONLY the tool name: {', '.join(available_tools)}, or 'direct'.
"""

    return prompt


def is_ambiguous_query(query: str, keyword_matches: list[str]) -> bool:
    """
    Determine if a query is ambiguous and needs LLM routing.

    A query is considered ambiguous if:
    - It matches keywords from multiple categories
    - It's very short (< 5 words) and vague
    - It contains negations or conditionals
    - It has unclear intent

    Args:
        query: User's query
        keyword_matches: List of categories that matched (e.g., ["doc", "web"])

    Returns:
        True if query needs LLM routing, False if keyword routing is sufficient

    Examples:
        >>> is_ambiguous_query("project timeline", ["doc", "db"])
        True  # Matches multiple categories

        >>> is_ambiguous_query("According to the Q3 Project Plan", ["doc"])
        False  # Clear single match

        >>> is_ambiguous_query("timeline", [])
        True  # Too vague, no clear category
    """
    # Multiple category matches = ambiguous
    if len(keyword_matches) > 1:
        return True

    # Very short queries with no matches might be ambiguous
    word_count = len(query.split())
    if word_count < 3 and not keyword_matches:
        return True

    # Single clear match = not ambiguous
    if len(keyword_matches) == 1:
        return False

    # No matches and very short = potentially ambiguous
    if word_count < 5 and not keyword_matches:
        return True

    # Default: not ambiguous
    return False


def _call_llm_for_routing(prompt: str, config: Config) -> Optional[str]:
    """
    Call Claude API to get routing decision.

    Args:
        prompt: Routing prompt to send to LLM
        config: Configuration object with API credentials

    Returns:
        Tool name suggestion or None if API fails

    Raises:
        APIError: On Claude API errors
        APIConnectionError: On network errors
        APITimeoutError: On timeout
    """
    if not ANTHROPIC_AVAILABLE:
        return None

    # Get API key from environment variable
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        logger.warning("ANTHROPIC_API_KEY not set, LLM routing disabled")
        return None

    try:
        # Initialize Anthropic client
        client = Anthropic(api_key=api_key)

        # Get model from environment variable or use default
        model = os.getenv("CLAUDE_RUNTIME_MODEL") or "claude-3-5-sonnet-20241022"
        logger.debug(f"Using Claude model: {model}")

        # Call Claude API with short timeout for routing
        response = client.messages.create(
            model=model,
            max_tokens=10,  # We only need a single word response
            timeout=5.0,    # Short timeout for fast routing
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        # Extract and parse response
        if response.content and len(response.content) > 0:
            tool_suggestion = response.content[0].text.strip().lower()
            logger.debug(f"Claude API returned: {tool_suggestion}")
            return tool_suggestion
        else:
            logger.warning("Claude API returned empty response")
            return None

    except APITimeoutError as e:
        logger.error(f"Claude API timeout: {e}")
        return None
    except APIConnectionError as e:
        logger.error(f"Claude API connection error: {e}")
        return None
    except APIError as e:
        logger.error(f"Claude API error: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error calling Claude API: {e}")
        return None
