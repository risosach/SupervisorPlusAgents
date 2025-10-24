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
