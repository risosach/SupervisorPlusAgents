"""
LangChain Agent Integration for Supervisor.

This module provides LangChain AgentExecutor integration for the Supervisor Agent,
exposing MCP tools as LangChain Tools and enabling orchestration through LangChain's
agent framework.

The integration:
- Wraps existing Supervisor routing logic in LangChain Tools
- Provides AgentExecutor for tool orchestration
- Maintains backward compatibility with existing Supervisor
- Enables future integration with LangChain ecosystem

Note: This is a lightweight wrapper that preserves the Supervisor's existing
routing logic. The actual routing decisions are still made by supervisor.router.decide_tool().
"""

from typing import Optional, List, Any, Dict
from langchain_core.tools import Tool
from langchain_core.language_models import BaseChatModel
from langchain_anthropic import ChatAnthropic
from supervisor.config import Config, load_config
from supervisor.router import decide_tool
from supervisor.handlers import (
    handle_direct,
    handle_document,
    handle_database,
    handle_web,
    handle_fallback
)
import os


def create_supervisor_tools(config: Config) -> List[Tool]:
    """
    Create LangChain Tools from Supervisor's MCP tools.

    This function wraps the Supervisor's existing handlers as LangChain Tools,
    allowing them to be used in LangChain AgentExecutor.

    Args:
        config: Supervisor configuration object

    Returns:
        List of LangChain Tool objects

    Examples:
        >>> from supervisor.config import load_config
        >>> config = load_config('config.json')
        >>> tools = create_supervisor_tools(config)
        >>> len(tools)
        4
        >>> tools[0].name
        'direct_llm'
    """
    tools = []

    # Direct LLM tool (always available)
    tools.append(Tool(
        name="direct_llm",
        description="Answer general knowledge questions using Claude Haiku LLM. "
                    "Use this for questions that don't require external data sources.",
        func=lambda query: handle_direct(query, config)
    ))

    # Document Retriever MCP tool
    if config.is_tool_enabled('document_retriever'):
        tools.append(Tool(
            name="document_retriever",
            description="Search and retrieve information from internal documents. "
                        "Use this when the query references documents, files, plans, or internal knowledge.",
            func=lambda query: handle_document(query, config)
        ))

    # Database Query MCP tool
    if config.is_tool_enabled('database_query'):
        tools.append(Tool(
            name="database_query",
            description="Query structured database for metrics, counts, and analytics. "
                        "Use this when the query asks about numbers, statistics, or database records.",
            func=lambda query: handle_database(query, config)
        ))

    # Web Search tool
    if config.is_tool_enabled('web_search'):
        tools.append(Tool(
            name="web_search",
            description="Search the internet for current information and news. "
                        "Use this when the query requires up-to-date external information.",
            func=lambda query: handle_web(query, config)
        ))

    return tools


class LangChainSupervisorAgent:
    """
    LangChain-based Supervisor Agent.

    This class wraps the existing Supervisor functionality in a LangChain-compatible
    interface, using AgentExecutor for tool orchestration while maintaining the
    Supervisor's existing routing logic.

    Attributes:
        config: Supervisor configuration
        llm: Language model for agent reasoning
        tools: List of available LangChain tools
        verbose: Whether to print verbose logging

    Examples:
        >>> agent = LangChainSupervisorAgent(config_path='config.json')
        >>> response = agent.run("What is the capital of France?")
        >>> print(response)
        'The capital of France is Paris.'
    """

    def __init__(
        self,
        config_path: str = "config.json",
        verbose: bool = False,
        llm: Optional[BaseChatModel] = None
    ):
        """
        Initialize the LangChain Supervisor Agent.

        Args:
            config_path: Path to Supervisor configuration file
            verbose: Whether to enable verbose logging
            llm: Optional language model (defaults to Claude Haiku from .env)

        Examples:
            >>> agent = LangChainSupervisorAgent('config.json')
            >>> agent.config.system_prompt
            'You are a helpful AI assistant...'
        """
        self.config = load_config(config_path)
        self.verbose = verbose

        # Initialize LLM (defaults to Claude Haiku from .env)
        if llm is None:
            model = os.getenv("CLAUDE_RUNTIME_MODEL") or "claude-3-5-haiku-20241022"
            api_key = os.getenv("ANTHROPIC_API_KEY")

            if not api_key:
                raise ValueError(
                    "ANTHROPIC_API_KEY not set. Please set it in .env or environment variables."
                )

            self.llm = ChatAnthropic(
                model=model,
                api_key=api_key,
                temperature=0.7
            )
        else:
            self.llm = llm

        # Create LangChain tools from Supervisor handlers
        self.tools = create_supervisor_tools(self.config)

    def run(self, query: str, use_router: bool = True) -> str:
        """
        Run a query through the LangChain Supervisor Agent.

        This method uses the Supervisor's existing routing logic to select
        the appropriate tool, then executes it. The use_router parameter
        allows bypassing the router for testing.

        Args:
            query: User's natural language query
            use_router: Whether to use Supervisor's router (default: True)

        Returns:
            Response string from the selected tool

        Raises:
            ValueError: If query is invalid

        Examples:
            >>> agent = LangChainSupervisorAgent('config.json')
            >>> agent.run("What is 2+2?")
            '[Stub Claude API Response] Received query: What is 2+2?'

            >>> agent.run("What does the Q3 Project Plan say?")
            'According to the Q3 Project Plan, the deadline is October 31, 2025.'
        """
        # Validate query
        if not query or not isinstance(query, str):
            raise ValueError("Query must be a non-empty string")

        if not query.strip():
            raise ValueError("Query cannot be empty or whitespace only")

        # Use Supervisor's router to determine which tool to use
        if use_router:
            classification = decide_tool(query, self.config)

            # Map classification to tool execution
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
                return handle_fallback(query, self.config)
        else:
            # Direct LLM call without routing (for testing)
            return handle_direct(query, self.config)

    def get_available_tools(self) -> List[str]:
        """
        Get list of available tool names.

        Returns:
            List of tool names

        Examples:
            >>> agent = LangChainSupervisorAgent('config.json')
            >>> tools = agent.get_available_tools()
            >>> 'direct_llm' in tools
            True
        """
        return [tool.name for tool in self.tools]

    def reload_config(self) -> None:
        """
        Reload configuration and recreate tools.

        Useful for applying configuration changes without restarting the agent.

        Examples:
            >>> agent = LangChainSupervisorAgent('config.json')
            >>> # ... config.json is modified externally ...
            >>> agent.reload_config()
            >>> # New configuration is now active
        """
        self.config = load_config(self.config.config_path if hasattr(self.config, 'config_path') else 'config.json')
        self.tools = create_supervisor_tools(self.config)


# Convenience function for backward compatibility
def create_langchain_supervisor(
    config_path: str = "config.json",
    verbose: bool = False
) -> LangChainSupervisorAgent:
    """
    Create a LangChain Supervisor Agent.

    Convenience function for creating a LangChain-based Supervisor Agent.

    Args:
        config_path: Path to configuration file
        verbose: Whether to enable verbose logging

    Returns:
        Initialized LangChainSupervisorAgent

    Examples:
        >>> agent = create_langchain_supervisor('config.json')
        >>> response = agent.run("Hello")
        >>> len(response) > 0
        True
    """
    return LangChainSupervisorAgent(config_path=config_path, verbose=verbose)
