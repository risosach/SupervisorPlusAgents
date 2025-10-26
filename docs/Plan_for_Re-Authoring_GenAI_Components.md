# Plan for Re-Authoring the GenAI Components with Claude Code 2.0 and LangChain

## 1. Setting Up Claude Code 2.0 with Cursor and Git

### Install/Update Cursor and Claude Code

First, ensure you have the latest version of Cursor (the AI-augmented IDE) installed on your Windows machine. If your Cursor is outdated, download and install the newest version from the official site (or use any built-in updater). 

Next, install Claude Code 2.0 – Anthropic's agentic coding assistant – via Node.js. Make sure Node.js 18+ is installed. Then open a terminal (on Windows, you can use Command Prompt, PowerShell, or the terminal inside Cursor) and run:

```bash
npm install -g @anthropic-ai/claude-code
```

This globally installs the Claude Code CLI. After installation, navigate to a project folder (or your desired workspace directory) and launch the Claude CLI by simply typing `claude`. The first time you run it, you'll be prompted to log in to your Anthropic account via a browser (if you don't have one, sign up at claude.ai). Once logged in, Claude Code will be ready in your terminal.

### Integrate Claude with Cursor

There are two ways to leverage Claude in Cursor:

- **Via Cursor Settings**: If you have a Cursor Pro subscription (required for external LLMs), you can add your Anthropic API key in Cursor's settings. In Cursor's settings menu (likely under Models or API Keys), paste your Anthropic API key. Once added, Claude Sonnet 4 (Anthropic's latest model) will appear as an available model in Cursor's dropdown. Using your own key ensures you're billed directly by Anthropic and avoids Cursor's markup on API calls.

- **Via Claude CLI inside Cursor**: Alternatively, even without configuring the API key in Cursor, you can use the Claude Code CLI within Cursor's integrated terminal. Open a terminal panel in Cursor, run the `claude` command, and it will interface with Cursor. In fact, users report that launching `claude` inside Cursor automatically installs a plugin into Cursor. This allows Claude to make inline code edits and suggestions through the Cursor interface. (Ensure you've logged in via the CLI as described above.)

Using either method, you'll have Claude Code 2.0 (powered by the Sonnet 4.5 model) assisting your coding. Claude Sonnet 4.5 is Anthropic's newest and best coding model, capable of handling very long, complex tasks and agentic workflows. Once configured, you can use Cursor's AI chat or suggestions powered by Claude. For example, you can highlight code or errors and ask Claude for fixes or explanations. Claude Code can even execute certain actions (like running tests or Git commands) on your behalf.

### Connect to the DigitalOcean Droplet

You mentioned having a DigitalOcean droplet (Linux server) from a previous project. To use it as a development or deployment environment, you have a couple of options:

- **SSH in Cursor's Terminal**: You can simply SSH into the droplet from Cursor's terminal. For example, in Cursor's terminal: `ssh username@your-server-ip`. This gives you a remote shell where you can run commands on the droplet. If you installed Claude Code on the droplet as well, you could even run `claude` there. However, editing files directly via SSH would require using console editors (vim, nano, etc.) unless you mount the file system.

- **Remote Development Setup**: A more convenient approach is to use Git for syncing code to the server. Develop and test your code locally in Cursor, push it to GitHub, and pull it on the droplet. This way, the droplet can run the latest code (for integration tests or deployment) without you needing a full remote IDE. If desired, you could also set up an SSH remote workspace (similar to VS Code's Remote SSH extension) if Cursor supports it. Some Cursor community members use dev container or remote setups; for instance, Anthropic provides a devcontainer reference implementation for Claude Code on GitHub, which might allow connecting an editor to a container or VM. But to keep things simple, we'll use Git for now.

### Set Up Git and GitHub Repository

Since you have a GitHub account (even if you're a bit rusty with it), let's create a new repository for this project. Follow these steps:

1. **Create a New Repo on GitHub**: Log in to GitHub in your web browser. In the top-right corner, click the + menu and select "New repository." Enter a repository name (e.g., `genai-rewrite`) and an optional description. Choose the visibility (public or private as you prefer). It's helpful to initialize with a README (GitHub provides a checkbox for "Add README") so that the repo isn't empty. Then click Create repository. GitHub will set up the repo and redirect you to the repository page.

2. **Clone the Repo Locally**: On the new repository's GitHub page, find the Clone button (often a green "Code" button). Copy the repository URL (HTTPS is simplest to start). In your local environment (e.g., open a terminal in Windows or in Cursor), navigate to a folder where you want the project code to live. Run `git clone https://github.com/<YourUsername>/<RepoName>.git` with your actual repo URL. This will create a local directory for the repository and pull down the README.

3. **Set Up Branches – Dev and Prod**: By default, the new GitHub repo's main branch is usually named `main` (this will be our "prod" branch). We'll create a separate development branch for active work. Navigate into the repository folder (`cd <RepoName>`). Then create and switch to a new branch named `dev` by running:

   ```bash
   git checkout -b dev
   ```

   This Git command creates a new branch and checks it out in one step. Initially, it will be identical to `main` (just the README). Now, any changes you make will be on the `dev` branch, keeping `main` clean. Let's push this branch to GitHub:

   ```bash
   git push -u origin dev
   ```

   The `-u origin dev` sets the upstream so that subsequent pushes from `dev` go to the remote `dev` branch. After this, on GitHub you should see two branches: `main` (prod) and `dev`. Our workflow will be: develop on `dev`, run tests, then merge into `main` when ready for "production" release.

4. **Git Basics Refresher**: Remember the typical Git cycle: after editing files, do `git add .` to stage changes, then `git commit -m "Message"` to commit locally. Push with `git push`. To bring updates from GitHub (if you make changes on another machine or the server), use `git pull`. We'll keep commits frequent and messages descriptive. Since you're using Cursor, you can also use its GUI for Git if it has one, but the command-line is reliable. If you need a refresher on Git commands or branching, Atlassian's Git tutorials are helpful. For example, creating a new branch with `git checkout -b <name>` and pushing it is a standard practice for feature development.

5. **Connecting the Droplet via Git**: On the droplet, you should also clone the GitHub repo (so it can receive the code). SSH into the droplet and install Git (if not already: e.g., `sudo apt update && sudo apt install git` for Ubuntu). Then run the same `git clone` command on the droplet. You might use SSH keys or personal access tokens for auth on the droplet if prompted (that's one-time setup). Once cloned, you can `git pull origin dev` on the droplet to fetch the latest development code, or pull `main` to get stable code. This approach lets you test or run the app in an environment closer to production.

Now your environment is set: Cursor with Claude 2.0 is ready to help write code, and GitHub is ready with dev/prod branches to manage versions.

## 2. Overview of Key Technologies and Architecture Choices

Before diving into implementation, it's important to solidify the architecture and understand the tools we plan to use. Your plan involves multiple agents and modules that will interact. Here's a high-level outline of the system we aim to build, and the key technologies for each part:

### LangChain LangGraph

We intend to structure our AI agents using LangChain's LangGraph framework. LangGraph is a newer orchestration framework for building complex, multi-step or multi-agent workflows. Instead of a linear chain, it represents the agent system as a graph of nodes (each node can be an LLM step, a tool call, a data action, etc.) with shared state. This makes it easy to add new nodes (agents) or change the flow by reconfiguring the graph.

LangGraph excels at creating stateful, multi-agent systems with explicit control flow and memory, allowing for complex task automation. We'll design each functional module (document retriever, DB retriever, etc.) as a node or subgraph in LangGraph. LangGraph also integrates with standard LangChain, so we can use LangChain's tools and memory within this graph architecture. By using LangGraph, we ensure our agent orchestration is flexible and transparent, and we can easily inspect or modify how tasks are broken down. It also supports human-in-the-loop control and robust error handling, which is useful for enterprise use cases.

### Claude 4.5 (Claude Code 2.0)

The core "brain" of our system will often be an LLM. We're using Anthropic's Claude, specifically the Claude Code 2.0 setup with the Sonnet 4.5 model (the latest as of late 2025). Claude 4.5 is highly capable in coding and reasoning; Anthropic calls it "the best coding model in the world" and notes it's especially strong at building complex agents and using tools (it "shows substantial gains in reasoning and math" as well).

We will use Claude in two ways:
- (a) directly answering user queries when appropriate, and
- (b) as the reasoning engine that decides which tools to use and how.

The Claude Code environment gives us advanced features like checkpoints (to roll back code changes) and subagents/hooks for autonomous task execution. We can harness these in development: for example, Claude Code can automatically run tests after making changes (via hooks), which aligns perfectly with our test-driven approach. The fact that Claude Code can operate in a "headless" or CLI mode means we can script interactions (perhaps for CI pipelines or automated runs) if needed.

Also, because we plan to support the OpenAI Chat Completions API format for our supervisor (so it's easily replaceable or tunable), we'll structure prompts and responses in the chat format: i.e., with a system message for instructions, then user message, then assistant answer, etc. Typically, a conversation starts with a system message defining the role/behavior, followed by user and assistant messages alternating. We'll keep this in mind when building our prompt templates so that swapping in an OpenAI model (or any chat-completion API) later would be straightforward.

Essentially, the Supervisor agent will receive a conversation (history + new query) in this format and produce an assistant response – potentially consulting tools in between. We'll adhere to the OpenAI-compatible schema (role and content fields in JSON) for any internal APIs.

### Model Context Protocol (MCP)

We want all auxiliary tools (document search, web search, database query, etc.) to be accessed via the Model Context Protocol. MCP is an open standard that defines how LLMs can interface with external tools and data sources in a uniform way. In practice, an MCP "server" is typically a small web service (HTTP or SSE streaming, or even a local process) that exposes some functionality to the LLM agent.

Claude Code natively supports connecting to MCP servers and then allows the model to call those tools by name during a session. For example, one could add an MCP server for a Postgres database, and then ask Claude, "Query the database for XYZ," and Claude will know to route that request to the tool.

We will implement each of our backend modules (document retriever, DB retriever, etc.) as an MCP server. This means each module will run as a microservice providing a standardized `/mcp` endpoint (or using stdio) that Claude can call. Some MCP servers already exist (Anthropic lists many integrations like Sentry, Jira, PostgreSQL, etc.) which you can add with a CLI command.

In our case, we'll likely write custom MCP servers (probably in Python using FastAPI or similar for HTTP, or even just a CLI tool for stdio) for specific needs. The benefit is that Claude (or any MCP-compatible agent) can use these tools autonomously. By sticking to MCP, we make our system modular and easier to maintain. We can register our tools with Claude Code by name, and then in prompts, simply instruct the agent that those tools are available. (The Model Context Protocol essentially formalizes how the AI's context and requests to tools are structured – so we don't have to invent a custom JSON RPC or so; we just implement the MCP spec).

We will also design the Supervisor agent such that it only calls tools via MCP – making it easy to add/remove tools by editing config. In fact, LangChain's agents can be extended to call APIs, but using MCP with Claude might give additional safety and reliability since it was built for that integration.

### Docling for Document Ingestion

For document processing, we'll use Docling, as you suggested. Docling is an open-source library by IBM that "simplifies document processing, parsing diverse formats — including advanced PDF understanding — and provides seamless integrations with the gen AI ecosystem." This is ideal for our Document Ingest Module.

Docling can handle PDFs, Office docs (Word, PowerPoint, Excel), HTML, images (PNG, JPEG, etc.), even audio transcripts. It performs layout analysis to preserve structure (headings, tables, lists) and even extracts images and tables in a structured way. We'll use Docling to convert each new or updated document into a DoclingDocument (a unified, rich representation of the doc) and then into text and embeddings.

Importantly, Docling also supports Visual Language Models (like an IBM model called Granite Docling) for understanding diagrams/images in documents – meaning we can vectorize not just text but perhaps some visual content.

Our plan:

- Set up a watch on a cloud storage (OneDrive or Google Drive, whichever is easiest) or a designated file system directory. When a file is added or changed, our ingest service will pick it up.

- Use Docling's pipeline (likely the `DocumentConverter.convert()` API in Python) to parse the file. We might use the standard pipeline for now, which extracts text content, or if we enable `pipeline='vlm'`, Docling will use a multimodal model to get image content too.

- Once we have the content, we chunk it (Docling can output Markdown or plain text with structural markers, which we then split into chunks suitable for embeddings).

- Generate vector embeddings for each chunk. We can use a well-supported embedding model (for instance OpenAI text-embedding-ada, or open-source alternatives). Docling integrates with LangChain and vector DBs as well, but we can also do this manually with our chosen vector DB.

- Upsert the vectors into our Vector Database (initially ChromaDB). We chose ChromaDB for simplicity – it's an open-source, easy-to-use vector store that can run in-memory or persist to disk. It supports similarity search out-of-the-box. We can later swap it with another (Milvus, Pinecone, Weaviate, etc.) since we will abstract the interface, but starting with Chroma keeps things simple and local. (Note: Docling's docs even have examples using Milvus and Chroma for RAG.)

- Maintain metadata about documents (like which user uploaded it, timestamps, etc.) if needed in the vector store or a separate index, so we can do filtered searches per user permissions later on.

We'll run the Docling ingestion as a background microservice (could be a continually running Python script or a scheduled job) – essentially Module 2 in your list. For now, we might trigger it manually or on a schedule, and later integrate with OneDrive/Google Drive webhooks or APIs for real-time updates.

### Document Retrieval (QA) Module

Once documents are ingested and in the vector DB, the Document Retriever (Module 3) will be responsible for query-time retrieval. We'll implement this as another service or class that, given a user's query, does a vector similarity search in the DB and returns relevant snippets. This can be exposed to the Supervisor agent via MCP (e.g., an HTTP MCP server where Claude can send the query and get back a text answer or reference).

Initially, to keep it simple, our Supervisor might call the retriever internally (as a Python function) rather than full MCP, but making it MCP-compliant from the start is ideal. The retriever might use LangChain's retrieval QA chain under the hood: i.e., do similarity search for top k chunks, then optionally have an LLM summarize or directly answer using those chunks as context.

We can use docling here as well: Docling provides rich structured data (like knowing sections, table contents, etc.), which we might exploit in answers (perhaps for a later feature like "compare two docs" or retrieving specific figures). For now, the retriever will likely just return the text of the top chunks to the Supervisor, and then Claude will incorporate those into its final answer (i.e., a classic Retrieval-Augmented Generation pattern).

We will ensure that the retriever can handle queries for multiple documents and multiple formats. E.g., if the query is, "What does our design doc say about X?" it should pull that info; if the query is, "Show me the latest sales figures," and those are in an Excel, we might have ingested an XLSX via Docling which extracted tables, so we could retrieve data from those tables (Docling preserves table structure in DataFrames). These are advanced capabilities we can enable step by step.

### Database (SQL) Retriever Module

For structured data queries, we'll implement a Text-to-SQL tool (Module 4). The idea is to let users ask natural language questions and have the agent query enterprise databases (like a SQL database) to get answers. A typical approach is:

- Use an LLM to translate the user's question into a SQL query (possibly with schema guidance).
- Execute that SQL on the database.
- Return the results (maybe formatted nicely or summarized).

We can leverage known patterns here – for example, the architectural pattern for text-to-SQL BigQuery that you linked suggests using few-shot examples or a predefined agent that knows the schema. LangChain has a SQLDatabaseToolkit we can draw inspiration from. But we'll wrap this as an MCP tool, likely.

For instance, we could make a small Flask/FastAPI server that exposes an `/mcp` endpoint: when it receives a query (with some JSON including the user's NL question), it connects to the database, runs the LLM->SQL step, executes the SQL, and returns the result. We'll have to be careful with SQL injection and permissions – another reason to integrate with Azure AD perhaps (so that the DB is accessed with user credentials if possible). Initially though, we might just use a read-only service account for prototyping. The output could be a text answer or a table. Possibly we will incorporate this tool such that Claude can ask for clarification if needed ("which database?" or "which table?") – but that might come later.

### Web Search / Deep Research Module

This tool (Module 5) allows the agent to search the web or external knowledge sources when an answer isn't found internally. We might use an API like Bing Web Search or Google (SerpAPI or similar) to implement this. A quick way is to use something like SerpAPI or Google's PaLM/Bison via Vertex if available. But to avoid external dependencies, we might start with a simpler approach: perhaps use the Bing Web Search API (which Microsoft offers with a key) or even a headless browser for scraping.

LangChain provides a wrapper for Bing Search API and an HTTP request tool which could be useful. For now, let's plan on using an MCP server for web search – possibly by leveraging an existing MCP tool. (Anthropic's list of popular MCP servers includes some like a "searchAPI" or we could use the HuggingFace MCP which might allow using a wiki browser.) If nothing fits, we'll create a small tool: given a query, it returns top results (titles + snippets + maybe direct answer if one is found). We'll have Claude use this when the question is general knowledge or asks for information not in our documents. The Supervisor's logic (or Claude's reasoning) will decide when to invoke it.

### Document Summarizer Module

Module 6 is a tool for summarizing documents. This could actually reuse our Document Retriever + LLM, but as a distinct service: e.g., the user could say "Summarize the attached PDF" or the system might need to summarize long docs for reports. We can implement an MCP tool that takes a document (or content) and returns a summary.

Perhaps we'll use Docling here again: Docling can produce a structured representation, and then we feed that to an LLM summarizer (Claude itself is great at summarization given its long context). This is relatively straightforward with LangChain's summarize chain or a prompt template. We just have to expose it via an API so that the Supervisor can call, or maybe have the Supervisor ask Claude to summarize when needed.

### Document Comparator Module

Module 7 would compare two documents (or two versions of one document) and highlight differences or summarize changes. This is very useful in enterprise (e.g., "what changed between version 1 and 2 of a spec?"). Implementation-wise, we can use an approach like:

- If text-based, use a diff library to get changes, and then have an LLM explain those differences.
- If more semantic (e.g., two different docs on same topic), have an LLM read both (with their embeddings or content) and produce a comparative analysis (where they agree, differ, etc.).

This can be an MCP tool where the input is two doc IDs or contents and output is a comparison report. We might integrate with difflib for raw diff and then LLM for explanation. We won't tackle this until later, but it's on the roadmap. Good news: Claude's large context (100K tokens in Claude 2, possibly more in future) means it can directly ingest two pretty large docs to compare, which is promising.

### Visualizer Module

Module 8 is a bit open-ended. By "visualizer," perhaps you mean the ability to generate visual representations (charts, graphs) or UI elements from data. It could also be about visualizing the agent's reasoning or the document knowledge graph. For example, after retrieving data, maybe present it as a graph or create a diagram comparing options.

LangChain doesn't directly do that, but we might use libraries like Matplotlib or GraphViz behind the scenes and perhaps return an image. Or if this refers to creating visual output (like mermaid diagrams or flowcharts from text), we could integrate a tool for that. Given our focus, we'll defer this until core functions are done. But do note: Claude Code is capable of creating and modifying files, including image files or HTML – for instance, it can be instructed to generate a HTML report. So one idea: the Visualizer agent could instruct Claude to produce an HTML/Markdown visualization (maybe using a JS library) and then present that to the user.

### Front-End (React) and Microservices

All the above modules will live server-side, accessible through microservice APIs. The front-end will be a React app that interacts with a Chat Service (a back-end endpoint) which in turn calls the Supervisor agent. So we should plan a Chat microservice that the React app uses (likely via WebSocket or HTTP). This service will handle user messages: store them (for history), forward them to the Supervisor (and get the answer), then stream or return the answer to the UI.

Additionally, we'll have a microservice for managing chat history and user data (this could simply be part of the chat service or separate for scalability). Using a database (maybe PostgreSQL or even simpler at first, a SQLite or a vector store for chat embeddings) to save conversation context per user is a good idea.

Also, a microservice (or just an API route) for configuration – e.g., to fetch the Supervisor agent's system prompt and tool settings from a database. This aligns with your idea: "the supervisor should get its configuration from a microservice… so behavior can be tuned without code changes." We can implement that as a simple config table and an endpoint the Supervisor calls at startup or per request to get its directives (system prompts, which tools are enabled, etc.).

### Security (OBO and Permissions)

We are mindful of security from the start, although we might layer it in once basic functionality works. The goal is to use On-Behalf-Of (OBO) authentication so that each tool executes with the user's own permissions. In an enterprise environment with Azure AD (Entra ID), this is achievable by registering our app and using Azure AD tokens. The OBO flow means:

- The user logs in via Azure AD and gets a token for our front-end or API.
- Our backend (confidential client) receives that token and exchanges it for a new token to call a downstream API (like Graph or a protected resource) on behalf of the user.
- That token is passed to the tool, which uses it to access the actual service (e.g., the SharePoint or database), ensuring the action is done with the user's identity and permissions.

This prevents our tools from acting with unlimited privilege; instead, each action is limited by what that user is allowed to do in the enterprise. We will implement this by integrating with Azure AD: we'll likely use the Microsoft Authentication Library (MSAL) in Python for the token exchange. Each MCP tool that needs to call an Azure API will accept a user JWT, validate it (ensuring it's from our IdP and intended for us), then perform the OBO exchange to get a new token for the target resource. Microsoft's documentation on OBO (OAuth2) will be our guide. In practice, we will need to register two Azure AD applications (one for the client and one for the API, configured to allow OBO flow).

For now, while developing outside the enterprise environment, we might stub this or use simpler auth (or no auth) just to get things working. But we are designing the architecture such that inserting OBO later is straightforward. For example, our chat service can require an Authorization header (JWT from Azure AD) on each request. The Supervisor can then pass that token to tools (possibly via the MCP call headers).

We saw in the MCP docs that you can add headers for auth in the `.mcp.json` config – that could be one way to funnel the token. Alternatively, the Supervisor could inject the token into the tool's prompt or payload. We'll formalize this once basic calls work. The Medium article by Saima Khan on "Securing MCP Tools with Azure AD OBO" describes precisely this setup (it's the third part of her series), confirming it's a known approach. The key point is each API call happens in the true context of the user, and any downstream service enforces its own ACLs/RBAC based on that user's identity. This way, even if a tool is available to the user, it cannot perform actions the user isn't allowed to (for instance, a user without access to a certain SharePoint file couldn't retrieve it via our DocumentRetriever, because the token exchange for Graph would fail or the Graph API would deny access).

### Tracing and Model Management

For development and monitoring, we are considering tools like LangSmith or MLflow. These serve different purposes:

**LangSmith (by LangChain)**: is an observability and debugging platform specifically for LLM applications. It gives you trace logs of the agent's thought process, tool usage, intermediate prompts, and so on. With LangSmith, we can see each step the Supervisor agent takes (each node in the LangGraph) and where things might be going wrong. It's great for non-deterministic behavior debugging. We may integrate LangSmith's SDK to log each session, especially as we get to complex multi-agent flows. This will help when evaluating if the agent made the right decision calling a tool, or if a prompt needs adjustment. LangSmith also supports evaluations and feedback logging.

**MLflow**: is an open-source platform for the ML lifecycle – experiment tracking, model registry, deployment, etc. While traditionally used for training models, it's increasingly used for LLMOps as well. MLflow would allow us to log different prompt variants, track the performance of our system on test queries, and even version the prompts or chain configurations. It also could serve as a model registry if we later integrate any fine-tuned models. For example, we might log metrics like "accuracy of answers" or "latency of each tool call" for different versions of our Supervisor prompt. MLflow focuses on making ML projects "manageable, traceable, and reproducible" across their lifecycle. Given our system is more about orchestration than training, MLflow is optional, but we might use it to track improvements (say we run a suite of test questions and measure if answers are correct before and after a change – MLflow can record those results systematically).

Initially, we can proceed without these, but it's wise to keep the option. LangGraph actually encourages using LangSmith for monitoring (since they're from the same team) – it has built-in integration to send traces to LangSmith's dashboard. We will likely enable that once our agent is up and running. This way, as we develop, we have a safety net to see what's happening under the hood.

To summarize the planned architecture: we have a Supervisor Agent (Module 1) which is the central orchestrator. It takes user input and either answers directly (using Claude's capabilities) or delegates to tools (Modules 2–8) via MCP. Each tool is a microservice (or at least a logical module) that can run independently and be updated/tested in isolation. The Supervisor itself will be configurable via external prompts/config, and it will be implemented using LangGraph for flexibility and clarity. The front-end communicates with the Supervisor through a thin API layer, and user auth (eventually via Azure AD) is passed through to every tool invocation (ensuring security). We will use popular, well-supported libraries at every layer (FastAPI or Flask for APIs, LangChain/LangGraph for agent logic, Docling for docs, MSAL for auth, etc.) to avoid reinventing the wheel. This modular, token-based, cloud-agnostic design should make it easy to port back into your enterprise environment (e.g., deploying on Databricks, or on Azure with managed services) – since we're abstracting the underlying implementations. We keep infrastructure abstract: for instance, by coding to interfaces (a VectorStore interface, an Auth interface), we can later swap ChromaDB with Azure Cognitive Search or replace OpenAI API with an on-prem LLM, without breaking the Supervisor's logic.

With the architecture in mind, let's move step-by-step into building the first component: the Supervisor agent, using best practices like user stories and TDD.

## 3. Building the Supervisor Agent (Module 1) with TDD

We'll start small by implementing the Supervisor – the central agent that interprets user queries and routes them either to an LLM or to the appropriate tool. To ensure we do this robustly and in a maintainable way, we'll use Test-Driven Development (TDD) and write user stories to capture requirements. Acting as your tutor, I'll guide you through this process.

### 3.1 Define User Stories for the Supervisor

User stories will help clarify what the Supervisor should do from an end-user perspective. They are usually written in the format: "As a [user role], I want [some goal] so that [reason]." This keeps us focused on user needs. A classic example (for illustration) from Adobe is: "As a user, I want to find products quickly and easily so that I can save time and complete my shopping efficiently." For our Supervisor, our users are typically end-users (employees) interacting with a chat interface, and maybe also system administrators configuring it. Let's come up with a few key user stories:

- **Story 1: General Question Answering** – "As an end-user, I want the assistant to answer general knowledge questions directly, so that I get a quick answer without unnecessary steps."
  
  Example: If the user asks "What is the capital of France?", the Supervisor should detect this is a general fact and answer from the LLM (or perhaps an internal knowledge base) without invoking company document search or other tools. This implies the Supervisor needs a way to identify queries that don't require tools.

- **Story 2: Document Retrieval Query** – "As an end-user, I want the assistant to use my uploaded documents to answer my question when it's about internal content, so that I get accurate, relevant information from our files."
  
  Example: User asks, "What does the Q3 Project Plan say about milestones?" The Supervisor should recognize this as an internal document query and call the Document Retriever tool. It should then incorporate the retrieved info into the answer.

- **Story 3: Database Query** – "As an analyst user, I want the assistant to retrieve data from our database when I ask a data question, so that I can get up-to-date numbers or records through natural language."
  
  Example: User asks, "How many new accounts were created last week?" The Supervisor should route this to the Database Retriever (text-to-SQL) tool, rather than trying to answer from the LLM's general knowledge. It might involve the LLM to generate the SQL, but it's a tool-using scenario.

- **Story 4: Web Research** – "As an end-user, I want the assistant to perform web research when asked about an unknown topic or very recent information, so that I can get the latest information even if it's not in our system."
  
  Example: "What are people saying about our competitor's new product?" -> Supervisor uses the Web Search tool to fetch info, because this likely isn't answerable from memory or documents.

- **Story 5: Fall-back and Clarity** – "As an end-user, I want the assistant to gracefully handle queries that it cannot answer, possibly by asking clarifying questions or explaining the limitation, so that I'm not left frustrated."
  
  Example: If the query is vague or missing info (e.g., "Tell me about the policy." with no context), the Supervisor might ask "Which policy are you referring to?" or if something truly cannot be answered (maybe it's a disallowed request), it should respond politely that it cannot comply. This story ensures the Supervisor has a strategy for unknown or disallowed queries (perhaps utilizing an AI moderation or simply a default response).

- **Story 6: Configuration and Override** – "As a system administrator, I want to be able to update the Supervisor's behavior (prompts, tool availability) via configuration, so that I can tweak the system without modifying code."
  
  Example: Admin decides that the Supervisor should no longer use the web search tool (maybe due to firewall issues), and wants to disable it. Or they want to adjust the tone/style of responses by editing the system prompt. This implies the Supervisor will load its initial instructions and tool config from an external source (file, database, or service). In our design, a microservice could provide this (or we could read from a JSON config in early development).

You might come up with additional stories, but these cover primary flows. Document these in a Markdown file in your repo (perhaps `docs/user_stories.md`) or even in the README. This documentation will guide development and also serve as reference for future contributors.

### 3.2 Plan Supervisor Behavior and Interfaces

From the user stories, we can derive what the Supervisor needs to do:
- Accept a query (plus perhaps conversation history for context).
- Classify or decide how to handle it:
  - If general Q (Story 1): answer via LLM (Claude) alone.
  - If internal doc Q (Story 2): use Doc Retriever.
  - If data Q (Story 3): use DB tool.
  - If web Q (Story 4): use web search tool.
  - If unclear or restricted: handle accordingly (Story 5).
- Integrate any results from tools and compose a final answer to the user.
- Log the interaction and support using configurable system instructions (Story 6).

We should think about how to implement the classification logic. Initially, we can do something simple like keyword matching or rules (e.g., if query contains certain trigger words like "document" or matches the name of a known document or contains a question mark that looks factual). But a more robust way is to use an LLM classifier prompt: e.g., feed the query into a small prompt that asks "Should I answer directly or use a tool? If a tool, which one?" The Claude model itself can be prompted to decide – we could set up a system prompt that lists tool options and have it output a decision. LangChain's multi-tool agents often take this approach (with the ReAct framework or a structured output). For example, we could give Claude a list like: "If question is about company documents, output `use_doc_tool`; if about database, output `use_db_tool`; if general, output `answer_directly`; if about current events, output `use_web`." This is something we can refine later; to start, it might be okay to implement a stub function with if/else statements for known cases and a default to direct answer.

Additionally, we plan for the Supervisor to use the OpenAI ChatCompletions API schema for input/output. So we might define a function `supervisor_respond(user_messages: List[Message]) -> Message` where Message has `role` and `content`. The front-end will send the conversation as an array of messages (with roles system/user/assistant) and the Supervisor returns the assistant's next message. Internally, the Supervisor could build a prompt for Claude. If using LangChain, we might not need to manually concatenate messages – LangChain's Agent or ConversationChain can manage that with a system prompt plus context memory. But given our goal of configurability, we may manually craft the final prompt each time.

Libraries to use in Supervisor: We'll certainly use the anthropic Python SDK (or LangChain's Anthropic integration) to call the Claude model via API for direct answers and possibly for reasoning steps. We'll also use the LangChain (LangGraph) framework for orchestrating calls to tools if we go that route. However, to keep initial implementation straightforward, we could implement the Supervisor's logic imperatively (i.e., Python if/else and calling functions for tools or Claude) and integrate LangGraph later once the flow is clearer. An alternative quick approach is using LangChain's AgentExecutor with tools: LangChain can wrap an LLM and a set of tools so that the LLM decides which tool to use. There are standard agent types (like ReactMRKL or ZeroShotAgent). But those agents often formulate their own chain-of-thought prompts, which can be a bit unpredictable. Given we want a very controlled supervisor (with enterprise concerns), we might prefer writing a custom decision logic. LangGraph would allow that decision logic to be declarative.

For now, we can proceed with a simple approach:
- Write a function `decide_tool(query: str) -> str` that returns one of: `"direct"`, `"doc"`, `"db"`, `"web"`, or `"unknown"`. We can stub it with simple logic (and later replace with an LLM-based classifier).
- For each option, write a function to handle it. e.g., `handle_direct(query)` would call Claude to get an answer; `handle_doc(query)` calls the doc retriever service; `handle_db(query)` calls the db tool; `handle_web(query)` calls the web search.
- Then `supervisor_respond()` uses `decide_tool` and dispatches accordingly, then returns the final answer string (or Message).

This design allows easy unit testing by mocking those handler functions.

### 3.3 Set Up the Project Structure

Let's create a basic Python package structure in the repo for our backend. For example:

```
genai_supervisor/ <- main package folder (name it as you like)
  __init__.py
  supervisor.py <- contains Supervisor class or functions
  tools/
    __init__.py
    doc_tool.py
    db_tool.py
    web_tool.py
    ... <- stubs for now
  util/ <- maybe for utility functions (e.g., for auth, formatting, etc.)
tests/
  test_supervisor.py
  test_tools.py <- optional, maybe later
```

We'll implement the Supervisor in `supervisor.py`. Perhaps as a class `SupervisorAgent` that holds config (like system prompt, tool endpoints, etc.), or even just a set of functions if we want stateless simplicity. A class might be cleaner for maintaining state (like conversation history or config).

We also consider how to incorporate configuration (Story 6). A simple method now is to have a `config.yaml` or `config.json` that lists available tools and the system prompt. The Supervisor can load that on startup. Later, we can swap that with a call to a config microservice or a database lookup.

For the moment, maybe create a `config.json` with something like:

```json
{
  "system_prompt": "You are an AI assistant ... (some instructions)",
  "tools": {
    "doc_retriever": {"type": "http", "url": "http://localhost:5001/mcp"},
    "db_retriever": {"type": "http", "url": "http://localhost:5002/mcp"},
    "web_search": {"type": "http", "url": "http://localhost:5003/mcp"}
  }
}
```

(This is illustrative; the actual content will change when we implement those services.) Claude Code's docs showed `.mcp.json` formats for tool config, but we can maintain our own config and use requests directly.

### 3.4 Write Unit Tests for the Supervisor

We will now write unit tests before implementing the Supervisor logic fully. This ensures we clarify expected behavior and can later verify that the implementation meets it. Using pytest (since you're familiar with Python, pytest is a common and simple framework), we create `tests/test_supervisor.py`.

We'll cover at least the scenarios from our user stories:

- **Test direct answer (general query)**: Simulate a question like `"What is the capital of France?"` and assert that the Supervisor chooses direct answer (does not call any tool) and returns a string containing "Paris" (the expected answer). Since calling the real Claude API in a unit test is not ideal (and might produce varying text), we would mock the LLM call. For example, we can monkeypatch our `handle_direct` or the Anthropc API call to return a fixed answer. Alternatively, for initial testing, we can implement `handle_direct` as a stub that returns "Paris" for that specific question. The test can then check the output. Later, we'll rely on integration tests with the real model for correctness, but unit tests will focus on the decision logic.

- **Test document query routing**: Give a query that clearly needs the document tool, e.g., `"According to the Q3 Project Plan, when is the deadline?"`. In our test, we can pretend that our `decide_tool` should return `"doc"` for this. We then need to ensure that the Supervisor calls the doc tool and includes its result in the answer. We can simulate the doc retriever's response: for instance, monkeypatch `tools.doc_tool.query_document(query)` to return a snippet like `"The Q3 Project Plan says the deadline is October 31."`. Then the Supervisor should incorporate that. We might design `handle_doc(query)` to return a string answer directly (maybe even the final answer like "According to the Q3 Plan, the deadline is Oct 31."). Or it could return the retrieved content and the Supervisor then formats it. Either way, test that calling Supervisor yields an answer containing `"October 31"`.

- **Test DB query routing**: Input `"How many new accounts were created last week?"`. Expect `decide_tool` -> `"db"`. We can stub `tools.db_tool.query_database(query)` to return a result (e.g., "42" or a small table). The Supervisor might either output just the number or a sentence. For test, we can assert that "42" (if that's the stubbed result) is in the answer. The structure might be: Supervisor calls DB tool and then says something like `"There were 42 new accounts created last week."`.

- **Test web query routing**: Input something like `"Latest news on <some topic>"` or your example about competitor. Expect route to `"web"`. Stub `tools.web_tool.search_web(query)` to return a snippet or URL. The Supervisor might then summarize it. This one might be tricky to test deterministically, but we can at least test that the web tool was invoked. We could have the stub set a global flag or attach to the Supervisor to note it was called. For example, in the test, replace `handle_web` with a function that sets `was_called=True` and returns a dummy answer. Assert that after Supervisor, `was_called` is True and answer contains some expected phrase.

- **Test fallback for unknown query**: If input is something gibberish or prohibited, ensure Supervisor either calls no tool and returns a safe message. For instance, query=`"DELETE all records"` (some malicious instruction) – we might want Supervisor to refuse because that's dangerous. We haven't fully defined moderation policy yet (that might come from Anthropic's built-in safe completions or a custom rule), but we could simulate that `decide_tool` returns `"unknown"` or some flag, and then Supervisor returns a default `"I'm sorry, I cannot help with that request."`. Test that. Or if query is very ambiguous, maybe Supervisor asks clarifying question. We can test a scenario: query=`"Tell me about the policy."` and see if the answer contains "Which policy" (if we implement that clarification logic). However, such nuance might be left to Claude's own response rather than explicit coding, depending on approach.

We should also test that the Supervisor properly formats the conversation with the system prompt. Perhaps we include a test that checks the system prompt is being applied. For example, if we set system prompt to enforce a certain style ("answer in a brief manner"), we could test that an answer is under a certain length or contains a certain style marker. This might be too granular for now, and it might rely on LLM output, so we can skip it in unit tests (cover in integration tests).

Example Test (Pseudo-code):

```python
# In test_supervisor.py
def test_direct_answer(monkeypatch):
    query = "What is the capital of France?"
    # Monkeypatch handle_direct to avoid real API call
    from genai_supervisor import supervisor
    called = {"used": False}
    
    def fake_handle_direct(q):
        called["used"] = True
        assert q == query
        return "Paris" # the answer we expect from LLM
    
    monkeypatch.setattr(supervisor, "handle_direct", fake_handle_direct)
    monkeypatch.setattr(supervisor, "handle_doc", lambda q: "DOC")
    # ensure others not called
    monkeypatch.setattr(supervisor, "handle_db", lambda q: "DB")
    monkeypatch.setattr(supervisor, "handle_web", lambda q: "WEB")
    
    result = supervisor.respond(query)
    assert called["used"] is True
    assert isinstance(result, str)
    assert "Paris" in result

def test_doc_tool_route(monkeypatch):
    query = "According to the Q3 Project Plan, what is the deadline?"
    # Simulate doc tool return
    from genai_supervisor import supervisor, tools
    
    monkeypatch.setattr(supervisor, "decide_tool", lambda q: "doc")
    monkeypatch.setattr(tools.doc_tool, "query_document", 
                       lambda q: "The deadline is October 31.")
    # Ensure direct LLM isn't called
    monkeypatch.setattr(supervisor, "handle_direct", lambda q: "LLM ANSWER")
    
    answer = supervisor.respond(query)
    # The answer might just be the doc snippet or some formatted version
    assert "October 31" in answer

# ... similarly for DB and web ...
```

This outlines the intent. We might have to adapt based on implementation details (e.g., if Supervisor is a class, we instantiate it first, etc.). The monkeypatching is using pytest's monkeypatch fixture to replace parts of the code for test isolation. This way we can intercept calls to external systems.

One thing to note: since we haven't written the actual code yet, writing tests now means we'll initially see them fail (which is expected in TDD – red, then green). Then we implement until tests pass.

### 3.5 Implement the Supervisor to Pass the Tests

Now with tests specifying desired behavior, we proceed to implement the Supervisor module. Here's one way to implement a minimal working Supervisor that should make the tests pass:

In `supervisor.py`, have a function like:

```python
def respond(query: str) -> str:
    tool = decide_tool(query)
    if tool == "direct":
        return handle_direct(query)
    elif tool == "doc":
        doc_answer = tools.doc_tool.query_document(query)
        # Possibly post-process or ask LLM to format it, but for now just return
        return doc_answer
    elif tool == "db":
        return tools.db_tool.query_database(query)
    elif tool == "web":
        return tools.web_tool.search_web(query)
    else:
        # unknown or unclear
        return "I'm sorry, I'm not sure how to help with that."
```

And `decide_tool` can be something simple, like:

```python
def decide_tool(query: str) -> str:
    q = query.lower()
    if "according to" in q or "document" in q or "file" in q:
        return "doc"
    if "database" in q or "accounts" in q or "sales" in q:
        return "db"
    if "http" in q or "website" in q or "news" in q:
        return "web"
    # default:
    return "direct"
```

This is a naive heuristic but can work for tests. We can improve it later (maybe using a small LLM prompt or LangChain's `AgentType.ZERO_SHOT_REACT_DESCRIPTION` with tool descriptions, which would let the LLM choose automatically).

The `handle_direct(query)` can call Claude. For now, to keep it simple and not require an API key in development, you might use OpenAI's text-davinci-003 or some local model just for initial coding – but since you do want Claude 4.5 specifically, you'd use the Anthropic API. We should integrate that properly with API keys stored in environment variables for safety. Perhaps use the anthropic Python SDK:

```python
import anthropic
client = anthropic.Client(api_key=os.environ["ANTHROPIC_API_KEY"])

resp = client.chat_completion(
    model="claude-2", # or "claude-2.0", depending on what they call it
    messages=[
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": query}
    ]
)
answer = resp['completion']
```

We'll set `SYSTEM_PROMPT` from config (like "You are a helpful assistant…" plus maybe tool-use instructions in the future). For now, `SYSTEM_PROMPT` can be a generic placeholder or even empty if we just want Claude's raw answer. This call will yield the model's answer. But in unit tests, we aren't actually calling it (we monkeypatch or simulate), so it's okay.

The `tools.doc_tool.query_document` might for now just search in a dummy in-memory dict, or always return a fixed string (since we haven't built Module 2 yet). We will stub it in tests anyway. We can leave its implementation as a simple placeholder (or raise NotImplemented if called outside tests).

Similarly for `tools.db_tool.query_database` and `tools.web_tool.search_web`. Possibly we implement minimal dummy functions that return a message like "DB_RESULT" or "WEB_RESULT", just so if they accidentally get called, we see a result.

We should also implement the ability to incorporate the document retrieval into the LLM answer eventually. A refined approach (later) might be: when tool returns info, the Supervisor doesn't just forward that raw text to user, but instead prompts Claude to integrate it. For example, if the doc tool returns some paragraphs, we might call Claude with a prompt: "Using the following excerpt, answer the question: [excerpt] \n Question: [user query]". But at first, to reduce complexity, we might simply return the excerpt or a concatenation of it with a phrase. This will be obviously improvable, but it's fine for initial testing.

Given the user said "cursor+claude will do the coding", you, as the tutor, might not have to write all that code by hand, but rather guide them to it. However, since we're providing detailed guidance, writing out a code structure is okay. They can then use Claude in Cursor to refine it.

While implementing, run the tests frequently. In Cursor, you can likely run pytest in the terminal or use an integrated test runner. Claude Code might even suggest fixes when tests fail. Use that to your advantage. For example, if a test fails, you can ask Claude "Why did this test fail? How to fix?" and since Claude can see the codebase (if run in the Claude Code environment), it can suggest the code changes – this is where its "autonomous coding" features shine (especially with the new checkpoint system to roll back if needed).

Ensure each test passes one by one (it's okay to temporarily xfail or comment out later tests while focusing on one). This iterative approach will build confidence.

One by one:
- Implement minimal `decide_tool` and stub handlers to get direct answer test passing (just return "Paris" if query contains "capital of France", etc., or monkeypatch as we planned).
- Then implement doc handling to get that test passing (maybe just return the stub string from doc_tool).
- And so on.

Eventually, all Supervisor unit tests should pass. At that point, you have a basic working Supervisor agent!

### 3.6 Try Out the Supervisor (Manual Integration Test)

With tests green, do a quick manual run of the Supervisor in an interactive way (even before hooking up front-end or Claude for real). You can write a short script or use a REPL to call `supervisor.respond("Your question")` and print the output. For example, run:

```python
from genai_supervisor import supervisor
print(supervisor.respond("What is the capital of France?"))
print(supervisor.respond("According to the Q3 Project Plan, what is the deadline?"))
```

and see if you get "Paris" and "October 31..." as expected. This ensures the logic works outside of pytest context too.

At this stage, our Supervisor is very simplistic (lots of stubs and shortcuts), but it's a foundation. The next steps after this would be:
- Integrating the real Claude API in `handle_direct` (and possibly using it in other handlers to compose answers).
- Building out the actual tool modules (document ingest/retrieval, etc.) and then connecting them. We might first make the Document Retriever just read from a local folder or a dummy vector store (for test data).
- Enhancing decision logic, possibly by asking Claude to decide. Anthropic's Claude is pretty adept at following tool-use instructions, especially if we format a system prompt listing available tools and their purpose. We could experiment with a prompt like: System: "You are Supervisor. Tools available: (1) DocRetriever – for document questions, (2) DBRetriever – for data questions, (3) WebSearch – for internet queries. If the query is general knowledge or conversational, answer directly. You will be given user input and should either respond directly or call a tool by outputting an JSON with format: {...}. Only call one tool at a time." etc. Then we feed user input and see if Claude outputs a formatted action. This is analogous to LangChain's ReAct agents. We might implement this later for flexibility, but it requires careful prompt engineering and parsing of Claude's response.
- For now, keeping the Supervisor logic explicit and deterministic is okay since you can control it.

Finally, remember to commit your changes to git regularly. You have two branches: work on `dev` branch. Once the Supervisor is functionally ready and tested, you can merge to `main` (or create a PR and merge, if you want to simulate team workflow). For merging, you could simply do `git checkout main`, `git merge dev` (since it's just you, a fast-forward merge is fine), then push. That `main` branch version could be considered "prod ready" for Module 1. In the future, we might tag releases or use GitHub Releases for versioning, especially when integrating with enterprise deployment processes.

At this point, you have a solid starting point:
- Claude Code 2.0 set up in Cursor with the ability to assist coding and even run tests automatically.
- A new Git repo with structured branches.
- A clear architecture documented and the first module (Supervisor) implemented with tests.

Next, you would proceed to flesh out each tool module similarly (write user stories -> tests -> code, one by one), using Claude's help to generate code for connecting to vector DB, parsing docs with Docling, etc. Take advantage of Claude Code's checkpoints feature when doing larger refactors – you can double-tap Esc to rollback if it introduces errors. Also, as you integrate more, consider using LangSmith to monitor the agent's performance on some sample questions – it can greatly help in understanding why Claude chose a certain action.

This is a lot of information, so don't hesitate to ask me to clarify any step. We covered environment setup, tech stack choices, and a step-by-step path to start building with confidence. Now, with this plan, you can start coding in Cursor with Claude's assistance – happy coding, and good luck with your ambitious project!

## Sources

1. Installing and starting Claude Code (Anthropic CLI)
2. Cursor integration with Claude (using API key or CLI)
3. Claude Sonnet 4.5 capabilities
4. LangGraph for multi-agent orchestration
5. Model Context Protocol (MCP) concept
6. Example: using MCP for PostgreSQL (tool invocation)
7. Docling features for document parsing
8. Azure AD On-Behalf-Of flow explained
9. LangSmith for agent observability
10. MLflow for lifecycle management
11. OpenAI chat format guideline
12. Example user story format
13. Claude Code hooks for running tests automatically

### Referenced URLs

- Claude Code overview - Claude Docs: https://docs.claude.com/en/docs/claude-code/overview
- Claude 4 - Sonnet / Pricing & Configuration - Discussions - Cursor - Community Forum: https://forum.cursor.com/t/claude-4-sonnet-pricing-configuration/99361
- Introducing Claude Sonnet 4.5 \ Anthropic: https://www.anthropic.com/news/claude-sonnet-4-5
- Quickstart for repositories - GitHub Docs: https://docs.github.com/en/repositories/creating-and-managing-repositories/quickstart-for-repositories
- Git Branching, Revert, Reset, Merge, and More | Medium: https://medium.com/@saurabhdahibhate50/devops-day-10-task-681e02cde1db
- Thinking in LangGraph - Docs by LangChain: https://docs.langchain.com/oss/python/langgraph/thinking-in-langgraph
- Foundation: Introduction to LangGraph - LangChain Academy: https://academy.langchain.com/courses/intro-to-langgraph
- LangChain vs. LangGraph: A Developer's Guide to Choosing Your ...: https://duplocloud.com/blog/langchain-vs-langgraph/
- LangGraph - GitHub Pages: https://langchain-ai.github.io/langgraph/
- LangGraph: https://www.langchain.com/langgraph
- Enabling Claude Code to work more autonomously \ Anthropic: https://www.anthropic.com/news/enabling-claude-code-to-work-more-autonomously
- Multiple system messages? - API - OpenAI Developer Community: https://community.openai.com/t/multiple-system-messages/295258
- Connect Claude Code to tools via MCP - Claude Docs: https://docs.claude.com/en/docs/claude-code/mcp
- GitHub - docling-project/docling: Get your documents ready for gen AI: https://github.com/docling-project/docling
- Docling | Langflow Documentation: https://docs.langflow.org/bundles-docling
- RAG with Milvus - Docling - GitHub Pages: https://docling-project.github.io/docling/examples/rag_milvus/
- Docling: A Guide to Building a Document Intelligence App | DataCamp: https://www.datacamp.com/tutorial/docling
- Securing MCP Tools with Azure AD On-Behalf-Of (OBO) | by Saima Khan | Sep, 2025 | Medium: https://medium.com/@khansaima/securing-mcp-tools-with-azure-ad-on-behalf-of-obo-29b1ada1e505
- LangSmith - Observability - LangChain: https://www.langchain.com/langsmith/observability
- MLflow: A Tool for Managing the Machine Learning Lifecycle | MLflow: https://mlflow.org/docs/3.1.3/ml/
- User stories – How to write them and examples - Adobe for Business: https://business.adobe.com/blog/basics/user-stories-overview
