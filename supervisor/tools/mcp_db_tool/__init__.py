"""Database Query Tool – MCP Server.

Exposes a tool 'database_query' that executes natural language queries against
a SQLite database. Implements Model-Context-Protocol (MCP) compliance via FastMCP.
"""

from supervisor.tools.mcp_db_tool.server import create_database_tool

__all__ = ['create_database_tool']
