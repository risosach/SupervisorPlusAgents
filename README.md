# Supervisor Agent & MCP Tools – RAG System Backend

This repository contains the evolving backend for an enterprise-grade **Retrieval-Augmented Generation (RAG)** chatbot.  
It uses a **Supervisor Agent** to route user queries to modular **MCP-based tools**, and is developed using a **test-driven, tool-oriented agent architecture**.

---

## 🗺️ Project Overview

The system is implemented in phases as outlined in the planning documents.  
Key goals include:

- Modular orchestration of AI tools (retrievers, DB, web) via MCP
- LLM-agent routing logic with clear decision control
- Secure tool access (e.g., via On-Behalf-Of token flow)
- Full test coverage using TDD and clear stage separation

---

## 📁 Reference Documents

| File | Description | When to Use |
|------|-------------|-------------|
| [`docs/project_background.md`](docs/project_background.md) | High-level vision, RAG architecture, staged roadmap | 📌 Use to understand the mission |
| [`docs/supervisor_design.md`](docs/supervisor_design.md) | Supervisor class architecture, config handling, CLI goals | 📌 Use during Stage 1 or agent implementation |
| [`docs/supervisor_test_plan.md`](docs/supervisor_test_plan.md) | Full test cases per user story | 📌 Use during test writing or debugging |
| [`docs/user_stories.md`](docs/user_stories.md) | 6 core user stories with acceptance criteria | 📌 Use when validating behavior coverage |
| [`docs/openai_mcp_protocol.md`](docs/openai_mcp_protocol.md) | In-depth guide to MCP, OpenAI function calling, security model | 📌 Use when designing real tools (Stage 2) or Supervisor-tool interfaces |
| [`docs/Plan_for_Re-Authoring_GenAI_Components.md`](docs/Plan_for_Re-Authoring_GenAI_Components.md) | LangChain + Claude Code integration plan | 📌 Use when restructuring agents, tools, or orchestrators |
| `logs/phase*_*.md` | Claude Code outputs + test summaries | 📌 Use for traceability and phase review |

---

## 🧪 Development Flow

1. Each stage is implemented using **test-driven development**.
2. Stub tools are used early for fast testing; real MCP tools come later.
3. Each phase’s results are logged in `logs/`.

---

## 📌 Status (As of October 24, 2025)

| Phase     | Status | Description |
|-----------|--------|-------------|
| Phase 1   | ✅ Complete | Configuration module (`config.py`) – 10 tests passing |
| Phase 2   | ✅ Complete | Stub tool module (`stubs.py`) – 5 tests passing |
| Phase 3   | ✅ Complete | Router logic (`router.py`) – 8 tests passing |
| Phase 4   | 🟡 Next | Tool handlers (dispatch logic to stub tools) – 9 tests target |
| Phase 5   | ⏳ Pending | Supervisor agent (end-to-end query response logic) |
| Phase 6   | ⏳ Pending | Integration tests for full workflows |
| Phase 7   | ⏳ Pending | CLI interface (query entrypoint, config flags)

**Current Progress**: 23/65 tests passing (35.4%)

---

## 🧠 Restarting Claude Code

If restarting the Claude Code terminal, use:

> “Use the following reference files for this phase:  
> - `project_background.md`,  
> - `openai_mcp_protocol.md`,  
> - `supervisor_design.md`,  
> - `supervisor_test_plan.md`.”

---

## 🔐 Secure Tool Usage

For tools requiring authenticated API calls (e.g., SharePoint, Azure DevOps), follow the **OBO (On-Behalf-Of) pattern** as defined in  
[`docs/openai_mcp_protocol.md`](docs/openai_mcp_protocol.md#secure-tool-access-and-the-on-behalf-of-obo-pattern).

---

## 📦 Structure (Stage 1)

```
supervisor/
  ├─ config.py
  ├─ router.py
  ├─ handlers.py         # Next
  ├─ agent.py
  └─ tools/
       ├─ stubs.py
tests/
  ├─ test_config.py
  ├─ test_router.py
  ├─ ...
docs/
  ├─ *.md
logs/
  ├─ phase*_*.md
```


---

# LangChain + Supervisor Agent Integration

This supplemental README provides LangChain-specific guidance for integrating our Supervisor Agent and MCP tool system into a LangChain or LangGraph-based orchestration pipeline.

---

## 🧩 Integration Architecture

LangChain will serve as the **orchestration layer**, allowing our Supervisor Agent to be embedded as an agent, chain component, or tool-invoking controller.

At a high level:

```
User Query
   ↓
LangChain Agent (Supervisor)
   ↓
Supervisor decides: direct | doc | db | web
   ↓
Tool call (via MCP microservice) → response
   ↓
LangChain handles final answer formatting / context passing
```

---

## 🛠️ LangChain Agent Design

| Component | Purpose | Implementation |
|----------|---------|----------------|
| `SupervisorAgent` | LangChain-compatible agent class | Wraps supervisor decision + tool calls |
| `ToolExecutor` | Wraps MCP server calls | Uses `requests.post()` or subprocess to call MCP tool |
| `LLM` | Claude or OpenAI | Handled via LangChain’s `ChatOpenAI` or custom Claude wrapper |
| `Memory` | Conversation state | Can be ephemeral or persistent |
| `Chain` | Full interaction logic | `ConversationalRetrievalChain` (if needed) or `AgentExecutor` |

---

## 🧪 Example LangChain Setup

```python
from langchain.agents import Tool, AgentExecutor
from supervisor.agent import SupervisorAgent
from supervisor.tools.dispatch import execute_tool

# Define LangChain-style tools (wrapping MCP calls)
tools = [
    Tool(name="document_query", func=lambda q: execute_tool("doc", q)),
    Tool(name="database_query", func=lambda q: execute_tool("db", q)),
    Tool(name="web_search", func=lambda q: execute_tool("web", q)),
]

# SupervisorAgent wraps routing logic
agent = SupervisorAgent(config_path="config.json")

agent_executor = AgentExecutor.from_agent_and_tools(agent=agent, tools=tools)
response = agent_executor.run("What’s the Q3 project deadline?")
```

---

## 📦 Tool Dispatch Notes

- **Tool names must match config.json** (`tools` key)  
- Tool execution is delegated to MCP servers via HTTP or subprocess  
- Claude 4.5 can autonomously call tools via MCP if enabled in prompt

---

## 🔐 Authentication + Security

If using **On-Behalf-Of (OBO)** for secure tools:
- Ensure LangChain frontend supplies JWT per user
- Supervisor or tool layer should forward this token to MCP server
- MCP server performs OBO token exchange (see `openai_mcp_protocol.md`)

---

## 📚 References

- [`docs/openai_mcp_protocol.md`](../docs/openai_mcp_protocol.md)
- LangChain docs: https://docs.langchain.com
- LangGraph (for advanced control flows): https://langchain-ai.github.io/langgraph/

---

## 🔄 Coming Soon

- LangGraph Supervisor flow (branching logic)
- Async MCP invocation
- Streaming support from Claude + MCP


---

# LangGraph + Supervisor Agent: Structured RAG Flow

This guide describes how to use **LangGraph** to orchestrate the Supervisor Agent and MCP tools in a node-based, branching execution graph.

LangGraph allows fine-grained control over agent execution flows, tool calls, memory updates, and retry logic — ideal for our structured Supervisor-driven architecture.

---

## 🔄 Supervisor Node in LangGraph

LangGraph treats each agent/tool as a node. The Supervisor Agent becomes a **router node** that determines the flow:

```
User Input → [Supervisor] → [Tool_X] → [ResponseComposer]
```

---

## 🧠 Node Definitions

| Node Name         | Purpose                                |
|-------------------|----------------------------------------|
| `supervisor_router` | Classifies query: direct/doc/db/web   |
| `tool_document`     | Calls MCP document tool stub/server   |
| `tool_database`     | Calls MCP database query tool         |
| `tool_web`          | Calls MCP web search tool             |
| `tool_fallback`     | Handles ambiguous or harmful queries  |
| `response_node`     | Assembles final output string         |

---

## 🧪 Example LangGraph Implementation

```python
from langgraph.graph import StateGraph
from langgraph.graph.graph import END
from supervisor.agent import SupervisorAgent
from supervisor.tools.dispatch import execute_tool

# Define graph
graph = StateGraph(input_type=str)

# Add router node
supervisor = SupervisorAgent(config_path="config.json")
graph.add_node("supervisor_router", supervisor.decide_tool)

# Add tool nodes
graph.add_node("tool_document", lambda q: execute_tool("doc", q))
graph.add_node("tool_database", lambda q: execute_tool("db", q))
graph.add_node("tool_web", lambda q: execute_tool("web", q))
graph.add_node("tool_fallback", lambda q: "Sorry, I can't help with that.")

# Add response composer (optional)
graph.add_node("response_node", lambda x: f"Answer: {x}")

# Routing edges
graph.set_entry_point("supervisor_router")
graph.add_conditional_edges(
    "supervisor_router",
    {
        "doc": "tool_document",
        "db": "tool_database",
        "web": "tool_web",
        "direct": "response_node",
        "fallback": "tool_fallback"
    }
)
# Chain tool outputs to final response node
graph.add_edge("tool_document", "response_node")
graph.add_edge("tool_database", "response_node")
graph.add_edge("tool_web", "response_node")
graph.add_edge("tool_fallback", "response_node")

# Final output
graph.add_edge("response_node", END)
runnable = graph.compile()
result = runnable.invoke("How many accounts were created?")
print(result)
```

---

## 🧩 Advantages of LangGraph

- Branching logic based on query type
- Retry nodes for error handling
- Easy expansion: summariser, planner, etc.
- Visualisable + testable control flow

---

## 🛡️ Secure Tool Access

Use JWT + OBO pattern as described in `openai_mcp_protocol.md` for secure tool calls. Tokens can be passed via graph state.

---

## 🔗 References

- LangGraph Agents: https://langchain-ai.github.io/langgraph/agents/agents/
- LangGraph Guide: https://docs.langchain.com/langgraph/
- [`openai_mcp_protocol.md`](../docs/openai_mcp_protocol.md)

---

## 📈 Roadmap

- Retry loop node for tool failure recovery
- Streaming node integration for Claude outputs
- LangGraph integration with event logs (MLflow / LangSmith)
