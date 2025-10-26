# Supervisor Design

This document contains the design specifications for the Supervisor CLI Agent (Stage 1).

## Overview

The Supervisor CLI Agent is the central orchestrator of the RAG chatbot system. In Stage 1, it acts as a command-line tool that accepts user queries and routes them to appropriate handlers using rule-based decision logic. The Supervisor coordinates stub MCP (Model Context Protocol) tools and integrates with Claude 4.5 for LLM capabilities.

---

## Architecture

### High-Level Design

```
┌─────────────┐
│   User CLI  │
└──────┬──────┘
       │
       v
┌──────────────────────────────────────┐
│      Supervisor Agent                │
│                                      │
│  ┌────────────────────────────────┐ │
│  │  Configuration Manager         │ │
│  │  - Loads config.json           │ │
│  │  - System prompts              │ │
│  │  - Tool definitions            │ │
│  └────────────────────────────────┘ │
│                                      │
│  ┌────────────────────────────────┐ │
│  │  Decision Router               │ │
│  │  - Rule-based classifier       │ │
│  │  - Keyword matching            │ │
│  │  - Intent detection            │ │
│  └────────────────────────────────┘ │
│                                      │
│  ┌────────────────────────────────┐ │
│  │  Handler Dispatcher            │ │
│  │  - Direct LLM handler          │ │
│  │  - Document tool handler       │ │
│  │  - Database tool handler       │ │
│  │  - Web search handler          │ │
│  │  - Fallback handler            │ │
│  └────────────────────────────────┘ │
└──────────────────────────────────────┘
       │
       v
┌──────────────────────────────────────┐
│  MCP Tool Interfaces (Stubs)        │
│                                      │
│  ┌────────────┐  ┌──────────────┐  │
│  │ Document   │  │ Database     │  │
│  │ Retriever  │  │ Query Tool   │  │
│  │ (stub)     │  │ (stub)       │  │
│  └────────────┘  └──────────────┘  │
│                                      │
│  ┌────────────┐  ┌──────────────┐  │
│  │ Web Search │  │ Claude LLM   │  │
│  │ Tool       │  │ Direct API   │  │
│  │ (stub)     │  │              │  │
│  └────────────┘  └──────────────┘  │
└──────────────────────────────────────┘
```

### Stage 1 Characteristics

- **Command-Line Interface**: Simple CLI for accepting queries and printing responses
- **Rule-Based Routing**: Uses keyword matching and heuristics (not LLM-based routing yet)
- **Stub MCP Tools**: Tool interfaces return mock data for testing
- **File-Based Configuration**: Reads from `config.json` for system prompts and tool settings
- **Synchronous Processing**: Single-threaded request/response (no async or streaming)
- **No State Persistence**: Each query is stateless (no conversation history)

---

## Components

### 1. Configuration Manager

**Responsibilities:**
- Load configuration from `config.json` at startup
- Validate configuration structure
- Provide access to system prompts, tool endpoints, and routing rules

**Configuration Schema:**

```json
{
  "system_prompt": "You are a helpful AI assistant...",
  "tools": {
    "document_retriever": {
      "enabled": true,
      "type": "http",
      "url": "http://localhost:5001/mcp",
      "description": "Retrieves information from internal documents"
    },
    "database_query": {
      "enabled": true,
      "type": "http",
      "url": "http://localhost:5002/mcp",
      "description": "Queries structured databases using text-to-SQL"
    },
    "web_search": {
      "enabled": true,
      "type": "http",
      "url": "http://localhost:5003/mcp",
      "description": "Searches the web for current information"
    }
  },
  "routing_rules": {
    "document_keywords": ["document", "file", "according to", "Q3 Project Plan"],
    "database_keywords": ["database", "accounts", "sales", "how many", "revenue"],
    "web_keywords": ["news", "latest", "current", "website", "http"]
  },
  "fallback_message": "I'm sorry, I'm not sure how to help with that request."
}
```

**Key Methods:**
- `load_config()`: Read and parse config.json
- `validate_config()`: Check for required fields and valid values
- `get_system_prompt()`: Return the system prompt string
- `get_tool_config(tool_name)`: Return configuration for a specific tool
- `is_tool_enabled(tool_name)`: Check if a tool is enabled

### 2. Decision Router

**Responsibilities:**
- Analyze incoming query
- Determine which handler/tool should process it
- Return routing decision (direct, doc, db, web, or fallback)

**Routing Logic (Rule-Based):**

```python
def decide_tool(query: str) -> str:
    """
    Classify query using keyword matching.
    Returns: 'direct', 'doc', 'db', 'web', or 'fallback'
    """
    query_lower = query.lower()

    # Check for document-related queries
    if any(keyword in query_lower for keyword in config.document_keywords):
        if config.is_tool_enabled('document_retriever'):
            return 'doc'

    # Check for database queries
    if any(keyword in query_lower for keyword in config.database_keywords):
        if config.is_tool_enabled('database_query'):
            return 'db'

    # Check for web search queries
    if any(keyword in query_lower for keyword in config.web_keywords):
        if config.is_tool_enabled('web_search'):
            return 'web'

    # Check for harmful/invalid patterns
    if is_harmful_query(query):
        return 'fallback'

    # Default to direct LLM response
    return 'direct'
```

**Key Methods:**
- `decide_tool(query: str) -> str`: Main routing function
- `is_harmful_query(query: str) -> bool`: Detect potentially harmful commands
- `extract_keywords(query: str) -> List[str]`: Parse query for classification

### 3. Handler Dispatcher

**Responsibilities:**
- Execute the appropriate handler based on routing decision
- Manage tool invocations
- Format responses for user output

**Handler Types:**

#### Direct LLM Handler
```python
def handle_direct(query: str) -> str:
    """
    Send query directly to Claude LLM with system prompt.
    """
    system_prompt = config.get_system_prompt()
    response = call_claude_api(
        system_prompt=system_prompt,
        user_message=query
    )
    return response
```

#### Document Tool Handler
```python
def handle_document(query: str) -> str:
    """
    Route query to Document Retriever MCP tool.
    """
    tool_url = config.get_tool_config('document_retriever')['url']
    result = invoke_mcp_tool(tool_url, query)

    # In Stage 1, this is a stub returning mock data
    # In Stage 2+, this will call real vector DB retrieval
    return result
```

#### Database Tool Handler
```python
def handle_database(query: str) -> str:
    """
    Route query to Database Query MCP tool (text-to-SQL).
    """
    tool_url = config.get_tool_config('database_query')['url']
    result = invoke_mcp_tool(tool_url, query)
    return result
```

#### Web Search Handler
```python
def handle_web(query: str) -> str:
    """
    Route query to Web Search MCP tool.
    """
    tool_url = config.get_tool_config('web_search')['url']
    result = invoke_mcp_tool(tool_url, query)
    return result
```

#### Fallback Handler
```python
def handle_fallback(query: str) -> str:
    """
    Return safe default response for unclear/harmful queries.
    """
    return config.fallback_message
```

### 4. MCP Tool Interface (Stub Implementation)

**Responsibilities:**
- Provide consistent interface for tool invocation
- In Stage 1: Return mock data for testing
- In Stage 2+: Implement real HTTP/MCP protocol calls

**Stub Implementations:**

```python
def stub_document_retriever(query: str) -> str:
    """Mock document retrieval for testing."""
    if "Q3 Project Plan" in query:
        return "According to the Q3 Project Plan, the deadline is October 31, 2025."
    return "No relevant documents found."

def stub_database_query(query: str) -> str:
    """Mock database query for testing."""
    if "accounts" in query:
        return "42 new accounts were created last week."
    return "No data available."

def stub_web_search(query: str) -> str:
    """Mock web search for testing."""
    return "Web search results would appear here. (This is a stub response.)"
```

### 5. CLI Interface

**Responsibilities:**
- Accept user input from command line
- Display formatted responses
- Handle CLI arguments and options

**Basic CLI Flow:**

```python
def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description='Supervisor CLI Agent')
    parser.add_argument('query', nargs='?', help='Query to process')
    parser.add_argument('--config', default='config.json', help='Config file path')
    parser.add_argument('--interactive', action='store_true', help='Interactive mode')

    args = parser.parse_args()

    # Load configuration
    supervisor = SupervisorAgent(config_path=args.config)

    if args.interactive:
        # Interactive REPL mode
        while True:
            query = input("You: ")
            if query.lower() in ['exit', 'quit']:
                break
            response = supervisor.respond(query)
            print(f"Assistant: {response}\n")
    else:
        # Single query mode
        if args.query:
            response = supervisor.respond(args.query)
            print(response)
```

---

## Data Flow

### Document Source and Ingestion
Documents are not uploaded directly by users through the chat or UI.  
All enterprise documents reside in SharePoint and are automatically ingested by the Document Retriever MCP Tool.  
Ingestion is triggered either by a scheduled polling process (e.g., hourly) or by file-system events on the SharePoint sync directory.  
This ensures consistent document availability without requiring manual uploads.

### Query Processing Flow

1. **User Input**: User submits query via CLI
2. **Configuration Load**: Supervisor loads config (if not already loaded)
3. **Query Analysis**: Decision Router analyzes query using keyword matching
4. **Routing Decision**: Router returns handler type (direct/doc/db/web/fallback)
5. **Handler Invocation**: Dispatcher calls appropriate handler
6. **Tool Call** (if applicable): Handler invokes MCP tool (or stub)
7. **Response Formatting**: Handler formats tool result for user
8. **Output**: Response printed to CLI

### Example Flow: Document Query

```
User Query: "What does the Q3 Project Plan say about milestones?"
    ↓
[Decision Router]
    - Detect keywords: "Q3 Project Plan", "say about"
    - Classification: 'doc'
    ↓
[Document Handler]
    - Check if tool enabled: Yes
    - Invoke: stub_document_retriever()
    - Stub returns: "According to the Q3 Project Plan, the deadline is October 31, 2025."
    ↓
[Output]
    - Print to CLI: "According to the Q3 Project Plan, the deadline is October 31, 2025."
```

### Example Flow: Direct LLM Query

```
User Query: "What is the capital of France?"
    ↓
[Decision Router]
    - No special keywords detected
    - Classification: 'direct'
    ↓
[Direct Handler]
    - Load system prompt from config
    - Call Claude API with prompt + query
    - Claude returns: "The capital of France is Paris."
    ↓
[Output]
    - Print to CLI: "The capital of France is Paris."
```

---

## Technology Stack

### Core Dependencies

- **Python 3.10+**: Core language
- **anthropic**: Official Claude API client
- **pytest**: Testing framework
- **pydantic**: Configuration validation (optional but recommended)
- **requests**: HTTP client for future MCP tool calls
- **argparse**: CLI argument parsing (standard library)
- **json**: Configuration parsing (standard library)

### Project Structure

```
SupervisorPlusAgents/
├── config.json              # Configuration file
├── supervisor/
│   ├── __init__.py
│   ├── agent.py            # Main SupervisorAgent class
│   ├── config.py           # Configuration manager
│   ├── router.py           # Decision router
│   ├── handlers.py         # Handler implementations
│   └── tools/
│       ├── __init__.py
│       ├── stubs.py        # Stub MCP tools for Stage 1
│       └── mcp_client.py   # MCP protocol client (for Stage 2)
├── tests/
│   ├── test_supervisor.py  # Main supervisor tests
│   ├── test_router.py      # Router tests
│   ├── test_handlers.py    # Handler tests
│   └── fixtures/
│       └── test_config.json
└── cli.py                  # CLI entry point
```

---

## Design Principles

### 1. Testability
- All components are independently testable
- Stub implementations allow testing without external dependencies
- Clear interfaces between components

### 2. Configurability
- Behavior controlled via config.json
- No hardcoded prompts or URLs in code
- Easy to enable/disable tools

### 3. Extensibility
- New handlers can be added without modifying core logic
- Plugin-style tool architecture
- Clear separation of concerns

### 4. Simplicity (Stage 1)
- Rule-based routing (avoid over-engineering)
- Synchronous processing (no async complexity yet)
- File-based config (no database dependency)

### 5. Future-Ready
- Interface design accommodates Stage 2/3 enhancements
- Stub implementations mirror real tool interfaces
- Architecture supports transition to microservices

---

## Known Limitations (Stage 1)

1. **No Conversation History**: Each query is independent (no context retention)
2. **Rule-Based Only**: Routing decisions use simple keywords, not intelligent classification
3. **Stub Tools**: MCP tools return mock data, not real results
4. **No Streaming**: Responses are synchronous and blocking
5. **No Authentication**: No user authentication or authorization
6. **No Logging**: Minimal logging infrastructure
7. **Single Model**: Only supports Claude (no model switching)
8. **No Error Recovery**: Limited error handling and retry logic

These limitations are intentional for Stage 1 and will be addressed in subsequent stages.

---

## Migration Path to Stage 2

Stage 2 will introduce:
- Real MCP tool implementations (document ingest, vector DB, web search)
- LLM-based routing (replace rule-based classifier)
- Conversation state management
- Asynchronous tool execution
- Enhanced error handling and logging
- LangGraph integration for orchestration

The Stage 1 architecture is designed to make this migration straightforward by maintaining clean interfaces and modular design.
