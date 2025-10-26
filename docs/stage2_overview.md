# Implementing the MCP-Compliant Document Tool

In this phase, we replace the stub Document Tool with a real MCP server using the FastMCP framework. The new Document Tool will be registered as an MCP tool and handle queries about internal documents. Below we outline the design and integration steps, ensuring the solution is comprehensive and aligns with MCP standards.

## 1. Creating the MCP Document Tool Server

We will create a new Python module under `supervisor/tools/mcp_doc_tool/` to define the Document Tool server. Using FastMCP, we set up a server instance and register a tool function for document retrieval:

### Initialize FastMCP
Create a FastMCP server (e.g. named "DocumentRetrieverServer"). This server will host our tool function(s).

### Define the Tool with @mcp.tool
Use the `@mcp.tool` decorator to expose a Python function as the document retrieval tool. For example:

```python
from fastmcp import FastMCP

mcp = FastMCP(name="DocumentRetrieverServer")

@mcp.tool(name="document_retriever",
          description="Retrieve info from internal documents by keyword")
def get_document_answer(query: str) -> str:
    """Looks up query in sample documents and returns a relevant snippet."""
    # ... logic described below ...
    return snippet_or_message
```

This registers the function as an MCP tool named "document_retriever", with an input schema (a single string parameter) and a return type of string. FastMCP will automatically handle schema generation and MCP compliance (e.g. wrapping primitive outputs in a JSON result) under the hood.

### Load a Mock Document Corpus
For this initial version, we use an in-memory dictionary of sample documents. Each entry maps a document title or key to a snippet of content. For example:

```python
documents = {
    "q3 project plan": "The Q3 Project Plan says the milestone deadline is October 31.",
    # ... other sample docs ...
}
```

We include the "Q3 Project Plan" in this corpus with a line about its milestone deadline being October 31. This ensures queries referencing the Q3 plan and milestones can be answered.

### Retrieval Logic
The `get_document_answer(query: str)` implementation performs a simple keyword match over the mock corpus:

- It normalizes the query (e.g. to lowercase) and checks for known document names or keywords.
- If the query mentions "Q3 Project Plan" (or similar keywords) and something about "milestones" or "deadline", the tool finds the relevant snippet. In our example, it would detect the Q3 Project Plan entry and return: "The Q3 Project Plan says the deadline is October 31."
- If no known document or keyword is found, it returns a "not found" message. For instance, the tool might respond with "Sorry, I couldn't find information on that." when the query doesn't match any document in our sample set.

This simple approach satisfies our current tests: one test expects an answer containing "October 31" for a milestones query, and another expects a "no info found" message for an irrelevant query.

### Structured Response
The tool returns a Python string for the snippet. FastMCP will package this into a JSON result object for the LLM. By default, a primitive return like `str` is wrapped under a "result" field in the MCP response. For example, a query JSON of:

```json
{"query": "What does the Q3 Project Plan say about milestones?"}
```

would yield a response like:

```json
{"result": "The Q3 Project Plan says the deadline is October 31."}
```

This aligns with the MCP spec and OpenAI function-calling format, where the function's output is provided as structured data.

### Docstring & Metadata
We will add a clear docstring at the top of the tool module or class to indicate its purpose and MCP compliance. For example:

```python
"""Document Retriever Tool – MCP Server.

Exposes a tool 'document_retriever' that returns snippets from internal documents.
Implements Model-Context-Protocol (MCP) compliance via FastMCP.
"""
```

This makes the tool's role and compliance explicit in the code documentation.

## 2. Making the Tool Callable via MCP (No HTTP Needed)

Instead of calling an HTTP endpoint, we leverage FastMCP's in-process capabilities to query the tool directly. FastMCP supports an in-memory transport for testing and local integration:

- We can create a FastMCP Client linked to our server instance: e.g. `client = Client(mcp_server_instance)`. Passing a FastMCP instance to the client tells FastMCP to use an in-memory connection (no network or subprocess). This means the Supervisor can call the tool as a normal function call, avoiding any HTTP overhead.

- The client provides an async method `call_tool("document_retriever", {"query": ...})` to invoke the tool. In our case, we will wrap this in a synchronous interface for the handler. For example, we might use `asyncio.run()` to execute the coroutine internally, or simply call the tool function directly since it's a local Python function.

- **Structured result handling:** The FastMCP client returns a structured `ToolResult` object. We will extract the actual string from it. (For a simple string result, FastMCP usually wraps it in a content object with the JSON already prepared; we can safely pull out the text or JSON field). In practice, because our tool returns a plain string, calling it directly in Python gives that string. We will use this direct call approach for simplicity.

### DocumentTool Class and __call__
To mirror an OpenAI function-call style interface, we implement a class (e.g. `DocumentTool`) with a `__call__(query: str) -> str` method. This makes the tool behave like a callable object. Internally, `DocumentTool.__call__` will invoke the MCP tool and return the resulting string. For example:

```python
class DocumentTool:
    def __init__(self):
        # Initialize FastMCP server and client once
        self.server = create_mcp_server()  # sets up mcp and tool as above
        self.client = Client(self.server)
    
    def __call__(self, query: str) -> str:
        # If needed, run async call_tool to get result
        result = asyncio.run(self.client.call_tool("document_retriever",
                                                     {"query": query}))
        return extract_text(result)  # unwrap the content to plain string
```

This design ensures the tool can be discovered via the MCP registry (the server's tool list) and called programmatically. By using an in-memory client, we adhere to the MCP interface without needing a live HTTP endpoint. The `DocumentTool` instance essentially acts as a lightweight wrapper around the MCP server's functionality, providing a convenient synchronous call.

## 3. Integrating with the Supervisor (doc_tool.py)

We will update `supervisor/tools/doc_tool.py` to utilize the new MCP-based tool instead of the stub:

### Tool Discovery
On module import, we can instantiate the Document Tool (creating the FastMCP server and registering the tool). For example, `doc_tool_instance = DocumentTool()`. This ensures the tool is ready to use and registered in the MCP server's registry when the Supervisor runs.

### Invocation Function
Replace the stub usage with a function or method that calls our `doc_tool_instance`. For instance, define `query_document(query: str, config: Config) -> str` that will route the call:

- **Check Tool Enabled:** If the document tool is disabled in config, we fall back to the direct LLM handler. In practice, we can mirror what the handlers did: `if not config.is_tool_enabled('document_retriever'): return handle_direct(query, config)`. This respects the config setting for disabling the doc tool.

- **Call DocumentTool:** If enabled, use the `doc_tool_instance` to get the answer. E.g. `answer = doc_tool_instance(query)`. This triggers the MCP tool logic we implemented. We may wrap this in a try/except if we expect any exceptions (though our simple lookup likely won't throw).

- **Return Result:** Pass the resulting snippet string back to the caller. (If using the async client internally, the `__call__` already handles extracting the string.)

### Update Handlers
In `handle_document()` (in `supervisor/handlers.py`), replace the stub call with the new interface. Previously it did: `result = stubs.stub_document_retriever(query)`. Now it will do something like:

```python
import supervisor.tools.doc_tool as doc_tool

# ...
def handle_document(query, config):
    if not config.is_tool_enabled('document_retriever'):
        return handle_direct(query, config)
    return doc_tool.query_document(query, config)
```

This way, the Supervisor's logic remains the same, but it now invokes the real tool. We keep the fallback to direct answer if the tool is disabled (as above) or if the tool returns a "not found" indication, ensuring robust behavior.

### Config Endpoints
In this in-process approach, we don't need an actual URL for the document service. However, for future-proofing, we might still include a placeholder in `config.json` (e.g. an entry for `document_retriever.endpoint`). For now, the code doesn't use an HTTP endpoint – the communication is internal via FastMCP – so this can be optional. The important config flag is the enabled status, which we honor as described.

By integrating at the `doc_tool.py` level, we encapsulate the MCP client usage inside the tool module. The rest of the system (router, handlers, supervisor agent) doesn't need to know the details – it simply calls our Document Tool and gets an answer. This matches the design goal that in Stage 2 we swap out stub implementations for real tools without changing the higher-level logic.

## 4. Testing and Verification

With the above implementation, we expect all relevant tests to pass:

### Document Query Handling
The user story test for document retrieval (e.g. `TestStory2DocumentRetrievalQuery`) should now get a real snippet. For the query "What does the Q3 Project Plan say about milestones?", the Document Tool will find the Q3 Project Plan entry and return "The Q3 Project Plan says the deadline is October 31." – satisfying the expected answer containing "October 31." The Supervisor's response should include that snippet.

### "Not Found" Scenario
If a query references a document or info not in our corpus, the tool returns a polite not found message. The handler will relay that as the answer. The test (e.g. `test_handle_document_not_found`) expecting an indication of no info will pass, since our output explicitly says nothing was found.

### Tool Disabled Case
If the config disables the document tool (as in `disabled_doc_tool_config.json`), `handle_document` will route to `handle_direct` instead. Our `doc_tool.query_document` double-checks the flag as well, so no attempt is made to call the MCP tool. The Supervisor will then answer via the LLM direct path, and tests confirming fallback behavior will pass.

### Integration Tests
Running the full test suite (`pytest -v`) after these changes should show all document-related tests passing. This includes unit tests in `tests/test_supervisor.py` and `tests/test_handlers.py` for the document story, and any integration tests in `tests/test_integration.py` that involve document queries. The output for the document query scenario should match the expected format (likely just the snippet string, as our handler returns it directly).

Finally, we will document the results and mark this phase complete:
- Write a log in `logs/stage2_doc_tool_results.md` summarizing the implementation and test outcomes.
- Update `docs/plan.md` to mark Stage 2, Phase 1 (Document Tool) as complete.
- Proceed to the next phase (the Database tool) once all tests (now including ~65+ tests) are green.

---

## 5. Environment Variable Configuration (.env Loading)

As of **Stage 2 - Phase 4 (Modifier)**, the Supervisor now automatically loads environment variables from a `.env` file at the project root. This provides a clean, standardized way to configure Claude API credentials and runtime settings without hardcoding values or manually exporting environment variables.

### Automatic .env Loading

The `supervisor/llm_router.py` module now loads the `.env` file automatically at import time:

```python
# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()  # Load .env from project root
except ImportError:
    pass  # dotenv not installed, rely on system environment variables
```

This happens once when the module is first imported, making configuration transparent throughout the application.

### Supported Environment Variables

The following variables can be configured in `.env`:

1. **ANTHROPIC_API_KEY** - Your Anthropic API key for Claude access
   - Format: `sk-ant-api03-...`
   - Required for LLM routing functionality

2. **CLAUDE_RUNTIME_MODEL** - The Claude model to use for routing decisions
   - Format: `claude-3-5-haiku-20241022` or `claude-3-5-sonnet-20241022`
   - Optional: Defaults to `claude-3-5-sonnet-20241022` if not set

### Example .env File

```
ANTHROPIC_API_KEY=sk-ant-api03-your-key-here
CLAUDE_RUNTIME_MODEL=claude-3-5-haiku-20241022
```

### Benefits

- **No Code Changes**: Switch models by editing `.env`, no code modification needed
- **Secure**: API keys stored in `.env` (should be in `.gitignore`), not in code
- **Environment-Specific**: Use different `.env` files for dev/staging/prod
- **Backward Compatible**: Works with or without python-dotenv installed
- **Standard Practice**: Follows 12-factor app configuration principles

### Model Selection

The runtime model is now configurable via the `CLAUDE_RUNTIME_MODEL` environment variable:

```python
# Get model from environment variable or use default
model = os.getenv("CLAUDE_RUNTIME_MODEL", "claude-3-5-sonnet-20241022")
logger.debug(f"Using Claude model: {model}")
```

This allows easy switching between models for different use cases:
- **claude-3-5-haiku-20241022**: Faster, more cost-effective for simple routing
- **claude-3-5-sonnet-20241022**: More capable for complex routing decisions

### Usage

1. Install python-dotenv (if not already installed):
   ```bash
   pip install python-dotenv
   ```

2. Create `.env` file at project root with your configuration

3. Run the Supervisor - `.env` loads automatically:
   ```bash
   python -m supervisor.cli "your query"
   ```

No additional configuration or code changes needed!

---

## 6. Live Claude API Integration (Phase 5 Modifier)

As of **Stage 2 - Phase 5 (Modifier)**, the Supervisor now makes real Claude API calls instead of returning stub responses, providing genuine AI-powered answers to user queries.

### Implementation Overview

The `call_claude_api()` function in `supervisor/handlers.py` was updated to:
1. Check for `ANTHROPIC_API_KEY` and `CLAUDE_RUNTIME_MODEL` in environment
2. Make real API calls to Claude when configured
3. Gracefully fall back to stub responses when unavailable
4. Handle API errors with proper logging

### Code Changes

**Modified:** `supervisor/handlers.py` (Lines 18-96)

```python
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
    """Call Claude API to get a response."""
    # Validation (unchanged)...

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
                messages=[{"role": "user", "content": user_message}]
            )
            return response.content[0].text
        except Exception as e:
            logger.warning(f"Claude API call failed: {e}. Falling back to stub response.")
            return f"[Stub Claude API Response] Received query: {user_message}"
    else:
        # Fall back to stub if API key missing or SDK unavailable
        return f"[Stub Claude API Response] Received query: {user_message}"
```

### Configuration Requirements

**Environment Variables:**
- `ANTHROPIC_API_KEY` - Your Anthropic API key (required for live responses)
- `CLAUDE_RUNTIME_MODEL` - Claude model to use (defaults to `claude-3-5-haiku-20241022`)

**Example .env:**
```env
ANTHROPIC_API_KEY=sk-ant-api03-your-key-here
CLAUDE_RUNTIME_MODEL=claude-3-5-haiku-20241022
```

### Behavior

| Configuration | Behavior |
|---------------|----------|
| API key set + SDK installed | Real Claude API calls |
| API key missing | Stub responses (logged) |
| SDK not installed | Stub responses (logged) |
| API error occurs | Stub responses (logged with warning) |

### Testing

**New Test Suite:** `tests/test_claude_live_response.py` (12 tests)

- **Live API Tests** (3 tests) - Skip automatically if no API key
  - `test_live_claude_api_call` - "What is the capital of the UK?" → "London"
  - `test_live_claude_math_query` - "What is 15 + 27?" → "42"
  - `test_live_direct_handler` - Full handler integration test

- **Fallback Tests** (3 tests)
  - `test_fallback_when_no_api_key` - Verifies stub when API key missing
  - `test_fallback_when_sdk_unavailable` - Verifies stub when SDK not installed
  - `test_fallback_on_api_error` - Verifies stub on API errors

- **Validation Tests** (4 tests) - Input validation unchanged
- **Model Configuration Tests** (2 tests) - Environment variable handling

**Test Results:** 153/156 tests passing (12 new tests, 3 skipped)

### CLI Validation

```bash
# Live Claude response
$ python -m supervisor.cli "What is the capital of the UK?"
London is the capital of the United Kingdom. Located in southeastern England,
London is not only the capital but also the largest city in the UK, serving as
a major global financial, cultural, and political center.

# Math query
$ python -m supervisor.cli "What is 25 + 17?"
25 + 17 = 42

# Document query (routes to MCP tool)
$ python -m supervisor.cli "What does the Q3 Project Plan say?"
According to the Q3 Project Plan, the deadline is October 31, 2025...

# Database query (routes to MCP tool)
$ python -m supervisor.cli "How many accounts were created last week?"
42 new accounts were created last week.
```

### Benefits

- **Real AI Responses**: Genuine Claude-powered answers for user queries
- **Graceful Degradation**: Works without API key (uses stubs)
- **Error Handling**: Automatically falls back on API failures
- **Configurable**: Easy model switching via environment variables
- **Production Ready**: Comprehensive error handling and logging
- **100% Backward Compatible**: All existing tests pass

### Documentation

See `logs/stage2_phase5_modifier_live_claude_results.md` for complete implementation details, test results, and validation.

---

## Sources

1. FastMCP tool definition and usage
2. Planning docs for Document Retriever design
3. Handler logic from Phase 1/Stage 1 (for config checks and stubs)

### References:
- [Tools - FastMCP](https://gofastmcp.com/servers/tools)
- Development Stages and Documentation Plan for Supervisor Agent and MCP Tools.pdf
- [The FastMCP Client - FastMCP](https://gofastmcp.com/clients/client)
- [Building an MCP Server and Client with FastMCP 2.0 | DataCamp](https://www.datacamp.com/tutorial/building-mcp-server-client-fastmcp)
- phase4_handlers_results.md
