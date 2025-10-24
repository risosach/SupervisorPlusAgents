# Project Background – Supervisor Agent and RAG Chatbot System

## Mission
This project’s long-term goal is to build an **enterprise-grade Retrieval-Augmented Generation (RAG) chatbot system** capable of providing accurate, context-rich answers sourced from internal and external data.

The architecture will centre on a **Supervisor Agent**, which coordinates a set of specialised **MCP (Model Context Protocol) tools** to perform retrieval, summarisation, and reasoning tasks.  
The Supervisor acts as the intelligent orchestrator — deciding which tools to invoke, handling context management, and ensuring that responses are explainable, safe, and grounded in data.

## Vision
The final system should function as a modular, extensible backend for enterprise chat interfaces or APIs.  
Key properties:
- **Tool-Oriented Reasoning:** Supervisor delegates to MCP tools (document retriever, database query, web research, summariser, planner).
- **Flexible LLM Integration:** The system should work with multiple model providers (OpenAI, Anthropic, etc.) through an abstraction layer.
- **RAG-Centric Pipeline:** Retrieval and grounding are first-class; generation must always reference factual sources.
- **Enterprise Features:** Configurable access control, logging, model selection, and potential microservice deployment.

## Development Strategy
The project will evolve through clear stages:

1. **Stage 1 – Supervisor CLI Agent (TDD Development):**  
   - Build the Supervisor as a local Python CLI tool with stub MCP tools.  
   - Define user stories, design spec, and test plan (TDD).  
   - Implement decision routing logic (rules-based at first).

2. **Stage 2 – MCP Tool Development:**  
   - Expand stubs into real tools: Document Retriever, Web Researcher, and Summariser.  
   - Introduce OpenAI/Claude API integration via an abstracted LLM service.  
   - Support conversation state and chain-of-thought orchestration.

3. **Stage 3 – Microservice Deployment:**  
   - Containerise Supervisor and MCP tools.  
   - Expose APIs for chat frontend integration (LangChain or custom orchestrator).  
   - Add persistence, logging, and configuration management.

## Current Focus
You are currently implementing **Stage 1**, where the goal is to:
- Scaffold the Supervisor CLI agent.
- Write documentation (user stories, design, test plan).
- Develop tests first (TDD), then implement minimal working Supervisor logic.

This foundation ensures that all later stages — including full RAG pipeline integration — are built on a robust, test-driven, modular core.
