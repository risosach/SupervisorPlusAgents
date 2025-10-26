"""Document Retriever Tool – MCP Server.

Exposes a tool 'document_retriever' that returns snippets from internal documents.
Implements Model-Context-Protocol (MCP) compliance via FastMCP.
"""

from supervisor.tools.mcp_doc_tool.server import create_document_tool

__all__ = ['create_document_tool']
