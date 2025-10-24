# Supervisor System – Full Development Plan

This document outlines the complete development roadmap for the Supervisor Agent system, broken down by **Stages** and **Phases**. It includes key outcomes for each phase, and identifies which components are implemented in Stage 1 (stubs and CLI) versus later stages (production MCP tools, LangChain orchestration, and deployment).

---

## 📍 Stage 1 – Supervisor CLI Agent (Local, TDD-Driven)

| Phase | Description | Status | Outputs |
|-------|-------------|--------|---------|
| 1. Config Module       | Load/validate `config.json` | ✅ Complete | `config.py`, config validation, accessors |
| 2. Stub Tools          | Stubs for doc, db, web tools | ✅ Complete | `stubs.py`, config-driven interfaces |
| 3. Router              | Keyword-based routing logic | ✅ Complete | `router.py`, `decide_tool()` |
| 4. Handlers            | Route to stub tools | ✅ Complete | `handlers.py`, tool invocation + formatting |
| 5. Supervisor Agent    | Full end-to-end query dispatch | ✅ Complete | `agent.py`, combines router + handler |
| 6. Integration Tests   | Verify cross-module behavior | ✅ Complete | `test_integration.py` |
| 7. CLI Interface       | Single-query + interactive CLI | ✅ Complete | `cli.py`, command parsing, tool invocation |

🧪 Total Tests: 76 (100% passing)  
📦 All tests structured under `tests/` with fixture configs and markdown logs.

---

## 🧭 Stage 2 – MCP Tool Integration & LangChain Orchestration

| Component | Upgrade Path | Notes |
|-----------|---------------|-------|
| Stub Tools → MCP Servers | ✅ Stubs match MCP interface | Real HTTP or STDIO MCP servers replace stub functions |
| Router → LLM Routing (optional) | Adds Claude-assisted fallback | Current router uses keyword matching; fallback to Claude/LLM for ambiguous queries |
| Claude Stub → Claude API | Replace `call_claude_api()` | Integrate OpenAI or Claude API with streaming |
| Supervisor Agent → LangChain Agent | Plug into LangChain `AgentExecutor` | Enables tool use via LangChain-style agents |
| CLI → LangGraph Graph | Replace CLI loop with `StateGraph` | Node-based routing, tool nodes, retry handling |
| Auth → OBO Token Flow | Secure tool access | Use Azure AD tokens and On-Behalf-Of pattern |

---

## 🚢 Stage 3 – Deployment & Frontend

| Target | Description |
|--------|-------------|
| MCP Microservices | Deploy tool servers independently |
| Supervisor API | Flask/FastAPI server for chat interface |
| Frontend Integration | React or other client connects to API |
| Docker/Infra | Containerized deployment with environment switching |
| Audit Logging | Track tool usage, auth flows, and model responses |
| Rate Limiting & Content Filtering | Guardrails for safe, secure production use |

---

## 📈 Summary Roadmap View

```
Stage 1 (TDD):
  - ✅ Config, Stubs, Router
  - ✅ Handlers, Agent, Integration, CLI
  - All logic fully test-driven
  - CLI-based query execution
  - 100% test coverage (76/76 tests passing)

Stage 2 (Tooling):
  - 🧠 Replace stubs with real MCP tools
  - 🔁 Claude + LangChain integration
  - 🔐 Secure tool calls via OBO
  - 🧭 LangGraph replaces CLI routing

Stage 3 (Deployment):
  - 🖥️ Frontend integration
  - ☁️ Microservice deployment
  - 🚪 Secure API and monitoring
```

---

## 🔁 Status Recap

| Stage | Completion | Notes |
|-------|------------|-------|
| Stage 1 | ✅ Complete | All 7 phases complete (76/76 tests passing, 100% coverage) |
| Stage 2 | 🧭 Ready to Start | Real tools, LangChain orchestration |
| Stage 3 | 🛠️ Planning | Production deployment and user interface

---

*This plan is updated at each phase. See `logs/` for progress logs and `README.md` for current status.*
