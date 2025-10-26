"""
Document Retriever MCP Server.

This module implements an MCP-compliant document retrieval tool using FastMCP.
The tool searches an in-memory document store and returns relevant snippets.
"""

try:
    from fastmcp import FastMCP
except ImportError:
    # Fallback if fastmcp not installed - use mock implementation
    FastMCP = None


# In-memory document store
# In Stage 2+, this will be replaced with vector database or SharePoint integration
DOCUMENTS = {
    "q3 project plan": {
        "title": "Q3 Project Plan",
        "content": "According to the Q3 Project Plan, the deadline is October 31, 2025. "
                  "The project includes milestone reviews in September and October. "
                  "Key deliverables must be completed by the end of Q3."
    },
    "design document": {
        "title": "Design Document",
        "content": "The design document specifies the authentication flow requirements. "
                  "Users must authenticate using OAuth 2.0 with Azure AD integration. "
                  "MFA is required for all administrative access."
    },
    "security policy": {
        "title": "Security Policy",
        "content": "The security policy mandates encryption at rest and in transit. "
                  "All data must be classified according to sensitivity levels. "
                  "Access controls follow the principle of least privilege."
    }
}


def search_documents(query: str) -> str:
    """
    Search the in-memory document store for relevant information.

    Args:
        query: Natural language query string

    Returns:
        Relevant document snippet or "not found" message

    Examples:
        >>> search_documents("Q3 Project Plan deadline")
        'According to the Q3 Project Plan, the deadline is October 31, 2025...'

        >>> search_documents("NonExistent document")
        'Document not found.'
    """
    if not query or not isinstance(query, str):
        return "Invalid query. Please provide a valid question."

    query_lower = query.lower()

    # Search for document matches
    for doc_key, doc_info in DOCUMENTS.items():
        if doc_key in query_lower:
            return doc_info["content"]

    # Check for partial keyword matches
    if "q3" in query_lower and ("plan" in query_lower or "project" in query_lower):
        return DOCUMENTS["q3 project plan"]["content"]

    if "design" in query_lower and ("doc" in query_lower or "document" in query_lower):
        return DOCUMENTS["design document"]["content"]

    if "security" in query_lower and "policy" in query_lower:
        return DOCUMENTS["security policy"]["content"]

    # No match found
    return "Document not found."


# Create FastMCP server if available
if FastMCP is not None:
    mcp = FastMCP("DocumentRetrieverServer")

    @mcp.tool(
        name="document_retriever",
        description="Retrieve information from internal documents by keyword search"
    )
    def get_document_answer(query: str) -> str:
        """
        Retrieve relevant information from internal documents.

        This tool searches an in-memory document store for information
        related to the user's query. It performs keyword matching to
        find relevant documents.

        Args:
            query: Natural language question about documents

        Returns:
            Relevant document snippet or "not found" message
        """
        return search_documents(query)
else:
    # Fallback if FastMCP not available
    mcp = None


class DocumentTool:
    """
    Document retrieval tool with callable interface.

    Implements __call__ to match OpenAI tool-calling semantics.
    Provides synchronous access to the MCP document retriever.
    """

    def __init__(self):
        """Initialize the document tool."""
        self.mcp_server = mcp
        # For Stage 2, we could initialize a FastMCP Client here
        # For now, we directly call the search function

    def __call__(self, query: str) -> str:
        """
        Retrieve document information.

        Args:
            query: Natural language query string

        Returns:
            Relevant document snippet or "not found" message

        Examples:
            >>> tool = DocumentTool()
            >>> tool("What does the Q3 Project Plan say?")
            'According to the Q3 Project Plan, the deadline is October 31, 2025...'
        """
        return search_documents(query)


def create_document_tool() -> DocumentTool:
    """
    Factory function to create a DocumentTool instance.

    Returns:
        Configured DocumentTool instance

    Examples:
        >>> tool = create_document_tool()
        >>> result = tool("Q3 deadline")
        >>> "October 31" in result
        True
    """
    return DocumentTool()
