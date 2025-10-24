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
| [`docs/Plan.md`](docs/Plan.md) | Overall development integration plan | 📌 Use to understand overall development steps and context of current tasks |
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
| Phase 7   | ⏳ Pending | CLI interface (query entrypoint, config flags) |

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
  ├─ handlers.py
  ├─ agent.py
  └─ tools/
       ├─ stubs.py
tests/
  ├─ test_config.py
  ├─ test_router.py
docs/
  ├─ *.md
logs/
  ├─ phase*_*.md
examples/
  ├─ mcp_server_example/
  ├─ langgraph_agent_example/
  ├─ openai_chat_example/
  └─ mlflow_agent_model_example/
```

---

# 🧰 Real-World Examples Directory

A curated `/examples` directory provides **working Python references** that Claude Code and developers can use to understand real-world implementations of key technologies used in this project.

| Example | Source | Focus | Why It Matters |
|----------|---------|--------|----------------|
| **MCP Server Example** | [FastMCP](https://github.com/jlowin/fastmcp) | `server.py` shows `@mcp.tool` decorator and `mcp.run()` | Demonstrates how to build an MCP-compliant microservice for tools (e.g., Document Retriever) |
| **LangGraph Agent Example** | [LangGraph Example](https://github.com/langchain-ai/langgraph-example) | `graph_app.py` defines and wires nodes | Shows how to orchestrate multi-agent logic (used for Supervisor flow control) |
| **OpenAI Chat Example** | [OpenAI Quickstart Python](https://github.com/openai/openai-quickstart-python) | `app.py` uses `openai.ChatCompletion.create()` | Demonstrates ChatCompletion schema compatible with Supervisor’s chat layer |
| **MLflow Agent Model Example** | [MLflow Official Examples](https://github.com/mlflow/mlflow/tree/master/examples/python_function) | `python_function.py` wraps a Python class as a model | Mirrors how we’ll expose agents as MLflow models in Databricks |

### 🔍 Usage Guidelines
- Use these examples as **learning and grounding references** for Claude when generating code.  
- Each folder contains a `README.md` summarizing key files and patterns to focus on.  
- These are not imported by the Supervisor — they exist to **guide development** and ensure architectural alignment.

---

# LangChain + Supervisor Agent Integration

*(Existing LangChain, LangGraph, and Supervisor content continues unchanged below…)*
