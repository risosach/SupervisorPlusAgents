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
