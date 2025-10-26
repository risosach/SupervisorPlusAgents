# Model Context Protocol (MCP) and OpenAI Chat Completions API

## Introduction

In our system, we leverage both the OpenAI Chat Completions API format for structuring conversations and the Anthropic Model Context Protocol (MCP) for integrating external tools. This document provides a comprehensive reference to these standards, along with related concepts (like secure tool access, text-to-SQL patterns, and ML lifecycle tools) to ensure our AI agents (e.g. Claude Code 2.0) have the context needed for success. By adhering to open standards, we make our solution modular and future-proof, allowing easy swapping of models or adding of tools without custom integration work.

## OpenAI Chat Completions API Format

OpenAI's Chat Completions API (the basis for GPT-4/GPT-3.5 chat models) uses a structured message format with roles to delineate the conversation. Each message in the API has a `role` and `content` field. The primary roles are:

- **System**: Provides initial instructions or context that define the assistant's behavior (e.g. "You are a helpful assistant."). This message sets the tone, boundaries, and persona for the AI. Only one system message is typically at the start of the conversation.

- **User**: Represents the user's input or question. The user message is the prompt or query the assistant should respond to. In a chat API call, the latest user message often carries the actual question/task.

- **Assistant**: The assistant's response message. This is produced by the model. When sending a new request, you may include prior assistant messages to continue a conversation thread. The API will populate the assistant's content in the response.

For example, a simple conversation payload looks like:

```json
[
  {"role": "system", "content": "You are a helpful assistant."},
  {"role": "user", "content": "What is the capital of France?"},
  {"role": "assistant", "content": "The capital of France is Paris."}
]
```

The use of roles enforces a clear separation between instructions, user queries, and model outputs, which helps maintain context and control the model's behavior. Our supervisor agent will structure prompts and responses in this OpenAI-compatible schema for internal messaging. By using the same format (JSON with role/content), we ensure that swapping in an OpenAI model later would be straightforward, and it aligns with LangChain/LangGraph conventions for chat messages as well. (LangGraph's `agent.invoke()` also expects a messages list with this structure.)

## Function Calling in Chat API

One powerful feature of the OpenAI Chat Completions API is the ability to define functions (tools) that the model can call. Developers can supply a list of function specifications (name, parameters schema, etc.) in the API request. The model can then decide to output a function call instead of a normal message if it determines a tool is needed. In such a case, the assistant's response will contain a `function_call` field (with the function name and arguments) and typically an empty content. The client (our system) is expected to execute that function and then provide the result back to the model as a new message with role "function" (and the name of the function). The model can then use that function result to generate a final answer.

This function-calling mechanism is how OpenAI enables tool use (e.g. querying databases, calculators, web lookup) in a safe, structured way. For example, if a user asks for weather, the model might return a function call `get_current_weather` with arguments, instead of answering directly. Our system's design keeps this in mind. While Claude+MCP uses a different approach for tools, the concept is analogous – structured tool invocations rather than free-form text. We maintain the OpenAI chat schema for compatibility; for internal processing we may intercept a tool request either from Claude (via MCP) or via an OpenAI model's function call, using a unified approach to execute the tool and return results.

**Note**: In the Chat Completions API, additional fields like `model`, `temperature`, `max_tokens`, etc., control generation parameters, but those do not affect the message format. We will ensure our Supervisor agent populates and handles these fields as needed if we ever expose an API compatible with OpenAI's. The key takeaway is that all conversational state is passed as an array of role-based messages, which our system and agents will rigorously follow.

## Model Context Protocol (MCP) for Tool Integration

The Model Context Protocol (MCP) is an open standard (open-sourced by Anthropic in late 2024) that defines how AI assistants can connect to external tools, data sources, and services in a uniform, structured way. Think of MCP as a "universal adapter" for tools – it allows an AI (like Claude or ChatGPT) to discover available tools and invoke them via a standardized interface, instead of having custom prompts or APIs for each tool. Anthropic describes MCP as providing "a secure, two-way connection between AI-powered applications and the systems where data lives".

### How MCP Works

MCP follows a client-server architecture:

- The AI application (or the environment hosting the AI, e.g. Claude's runtime or our LangGraph agent) acts as an MCP client (also called MCP host). It connects to one or more MCP servers – each MCP server represents an external tool or data source.

- An MCP server is typically a small web service or local process that exposes certain functionality (e.g. a database query endpoint, a document search, a CRM API) following the MCP specification. It registers a set of tools or resources that it can provide. For example, an MCP server might offer a tool named "database_query" with a specified input schema for queries.

- Communication between client and server is done via a JSON-RPC 2.0 based protocol over either a local STDIO channel or a network (HTTP + optional SSE for streaming). This means requests and responses are JSON objects with methods like `tools/list`, `tools/call`, etc., following the MCP spec.

When the AI session starts, the MCP client (Claude) will perform a tool discovery: it sends a `tools/list` request to each connected MCP server to retrieve what tools are available and their schemas. The server responds with a list of tool names, descriptions, and input/output schemas. Once tools are known, the AI can invoke them by name. Invoking a tool is done via a `tools/call` request, specifying the tool name and arguments (as JSON). The MCP server executes the requested action and returns a response which includes a result (potentially structured, e.g. text, or even binary data encoded in JSON). The response content is often an array of outputs (MCP supports multiple content types, but plain text results are common). The AI can then incorporate that result into its chat response to the user.

### Key Features of MCP

- **Standardized Tool Interface**: Instead of writing custom integration code or prompt formats for each tool, we implement the MCP spec once. The AI's requests to tools are structured (method names, params) and tool responses are structured with content types, which reduces ambiguity.

- **Tool Discovery**: The AI can dynamically discover which tools are available at runtime (via `tools/list`), and even get notified if tools are added/removed on the fly (MCP supports notifications like `tools/list_changed` for real-time updates). This dynamic capability means the assistant can adapt to new tools without code changes, making the system modular.

- **Multi-modal and Rich Responses**: MCP allows tool responses to contain not just text but images, files, or structured data (via content types). For example, a tool could return a plot image or a PDF, and the AI client would know how to handle it.

- **Security and Isolation**: Tools run as separate services (often microservices), and the MCP client controls what tools to expose to the AI. This provides a layer of isolation – the AI can only use tools through the MCP interface, and we can enforce authentication or permissions at the MCP server level (addressed more in the security section below).

- **Pre-built Ecosystem**: Since MCP is an open standard, there are already many pre-built connectors and servers for popular systems. Anthropic provided example MCP servers for Google Drive, Slack, GitHub, Git, PostgreSQL, web browsers, etc. Rather than building from scratch, we can use or adapt these. For instance, Anthropic's Claude Desktop app can install these servers with a CLI command. Early adopters have used MCP to link AI agents to internal tools (Block, Replit, etc., have case studies using MCP).

In our architecture, all auxiliary modules (document retrieval, database querying, etc.) will be implemented as MCP servers. Each module runs as a microservice exposing a standardized `/mcp` endpoint (if HTTP) or handling STDIO, so that Claude (or any MCP-compatible agent) can call it by name. For example, we might run a PostgreSQL query tool MCP server. Once connected, Claude can be asked: "Find all records in the database for XYZ", and behind the scenes it will issue a `tools/call` to the Postgres MCP server (e.g. tool name "query" with the SQL or query parameters). The result comes back and Claude presents it to the user.

By sticking to MCP, we avoid writing custom tool invocation logic or prompt strings; the protocol formalizes how the AI's requests to tools are structured, essentially standardizing what could otherwise be ad-hoc JSON or text exchanges. This makes our system more maintainable and safer. We simply register each tool with the AI (Claude) by establishing the MCP connection and then inform the AI (via the system prompt or API) that it has access to tools X, Y, Z. Claude's tool-use logic (which is part of Claude 2.0's capabilities) will handle routing requests to the right MCP call when needed.

Our Supervisor agent will only call tools via MCP, which means to add or remove a tool, we just start/stop an MCP server or adjust config – no need to alter the agent's code. This aligns well with LangChain/LangGraph: while LangChain agents traditionally could use tools via Python functions or API wrappers, using MCP provides a unified and possibly safer interface. In fact, Claude 4.5 (Claude Code) was built with tool use in mind and natively supports MCP integration, giving us confidence in its reliability for this use case.

### Implementation Note

We plan to write custom MCP servers for certain needs (likely using Python FastAPI for HTTP, or simple CLI programs for STDIO). We'll use Anthropic's MCP SDK where possible. Each server will define one or more tools with clearly defined schemas. For example, a DocumentRetriever MCP server might have a tool "doc_search" that takes a query and returns a list of relevant document snippets. Or a Database MCP server might have "sql_query" that takes a SQL string and returns query results. By using MCP, Claude can chain these in reasoning – e.g., it might call the doc search tool then use that info to answer the user, all within one conversation. Claude Code's autonomous tool use (via MCP) is a big advantage: "Claude (or any MCP-compatible agent) can use these tools autonomously" once they're connected.

## Secure Tool Access and the On-Behalf-Of (OBO) Pattern

When integrating tools, especially in an enterprise context, security and permission control are paramount. Two levels of security apply for our tools: which tools are exposed to a given user, and what each tool can do on the user's behalf. In earlier planning, we considered using Azure AD for authentication and role-based access to filter tool availability (e.g., only certain users see a "DatabaseAdmin" tool). Beyond that, we must ensure that when a tool calls an external API or database, it does so with the appropriate user permissions.

On-Behalf-Of (OBO) is a security pattern and OAuth2.0 flow that addresses this scenario. As defined by Microsoft, the OBO flow "allows a service (middle-tier) to call downstream APIs using a user's identity". In practice, it works like this:

1. **User Authentication**: The user logs in and obtains an access token (for example, a JWT from Azure AD) for our application or MCP server. This token represents the user's identity and includes scopes/permissions granted to our app.

2. **Token Exchange**: When the user invokes a tool that needs to call an external API, the MCP server for that tool takes the user's token and performs an OBO exchange – it presents the user's token to the identity provider (Azure AD) along with its own credentials, asking for a new access token for the downstream service on behalf of that user. For instance, if the tool needs to call Microsoft Graph, it will request a Graph API token for user X.

3. **Downstream API Call**: The tool then uses this new token (which carries the user's identity and permissions for the target API) to call the external service (e.g., Graph, DevOps, etc.) and fetch results. It then returns the result back to Claude via MCP. The external API sees a normal user-context call (as if user X themselves called it), not an all-powerful service account.

The advantage of OBO is **principle of least privilege** and **correct audit trails**. Without OBO, one might be tempted to give the MCP tool a blanket API key or a service account token. That could let the tool do anything (potentially beyond an individual user's rights) and any action would appear as done by the service, not the user. With OBO, "each API call happens in the true context of the user", and the external system can enforce its own RBAC or ACL checks based on the actual user's privileges. For example, if Alice doesn't have access to delete a record, even if she triggers a tool, the tool's attempted call to delete via an external API will be denied when using Alice's token. Meanwhile, the audit logs of the external system will show that Alice (via our app) made the call, which is important for compliance.

In our design, we will incorporate OBO for sensitive tools. Concretely, this means:

- Our MCP servers that call protected APIs (SharePoint, DevOps, databases, etc.) will require a user token when invoked. We'll ensure the front-end or client provides the current user's JWT to the MCP server (likely passed through the Authorization header or as part of the MCP connection setup).

- The MCP server (which is a confidential client registered in Azure AD) will be configured with the credentials (client ID/secret) and the required API permissions. When the tool is invoked, it will perform the OBO token exchange: using a library like MSAL's `AcquireTokenOnBehalfOf` to trade the incoming token for a new one scoped to the target resource.

- The new token is then used to call the external API, and only data that user is allowed to see or modify will be affected.

For example, suppose we have a "List SharePoint Sites" tool. If Bob (who has access to only Site A) asks Claude to list sites, the tool's MCP server will take Bob's token, get a Graph API token for Bob, call the Graph `/sites` API, and return only Site A in the results. If Alice (with access to Site A and B) uses the same tool, she'd get both sites. If we had instead used a single service account, both Bob and Alice might see A and B – a security hole. OBO prevents that by "securely delegating access to a downstream API using an upstream token".

Implementing OBO does add complexity (we need two Azure AD app registrations: one for the client and one for the MCP server, properly configured with trust for OBO, and token caching strategies). However, it significantly enhances security: "Without OBO, even users with minimal roles might invoke tools that call protected APIs with a privileged token, potentially doing things they shouldn't". With OBO, that risk is mitigated because the tool cannot do more than the user themselves could.

In summary, for MCP tools that interface with enterprise systems, we will:

- Require user authentication and pass the user identity to the MCP servers.
- Use OBO flow in MCP servers to obtain user-scoped tokens for downstream calls.
- Ensure auditing: the system can log not only that "Tool X was invoked" but also "on behalf of which user" for traceability (MCP itself can carry metadata, or we include it in logging).

This approach keeps our tool usage secure by design. It complements higher-level role filtering (which tools a user sees at all) with low-level permission enforcement on each tool action.

## Architectural Pattern: Text-to-SQL with LLMs

One of our planned capabilities is a natural language to SQL query function, allowing users to ask data questions that the AI will answer by querying a database. This is a complex task combining NL understanding with database schema knowledge and correct SQL generation. We have researched standard patterns for implementing text-to-SQL with LLMs, and will employ a robust approach using the AI agent plus tools.

A proven design is to use an LLM-powered SQL Agent (as described in LangChain and recent literature). Instead of a single pass conversion of text to SQL, the agent can interact with the database iteratively: examining schema, attempting a query, and refining it if needed. Key steps in this pattern:

### 1. Schema Retrieval

The agent first obtains the database schema or the relevant portion of it. This can be done by calling a schema listing tool. For instance, an MCP tool could expose a method to list tables or describe a table. In a LangChain SQL agent example, the agent might automatically run actions like `sql_db_list_tables` and `sql_db_schema` to fetch table structures. Providing the model with the schema helps it form correct queries.

### 2. Query Generation (Natural Language to SQL)

The LLM, informed by the user's question and schema, generates a SQL query. This could be direct, or in prompt form we guide it (e.g., few-shot examples of NL -> SQL). In our case, Claude 4.5 is strong in both coding and reasoning, so it should be capable of writing SQL given proper instructions. We will likely have a System prompt like "You can query the database using the database_query tool. Write a valid SQL for the user's request, considering the schema provided."

### 3. Execution and Refinement

The generated SQL is then executed against the database via the MCP database tool. The result might be data or an error. If an error occurs (syntax error, or a mistaken table/column), the agent can catch that and self-correct. This is where an agentic approach shines: the error message (e.g., "Column not found") can be fed back to the LLM, which then adjusts the query and tries again. This loop continues until a correct query is achieved or a limit is reached. The Medium article on text-to-SQL patterns notes this self-correction as an important capability in advanced patterns (Pattern IV and V in the article involve the LLM refining queries based on feedback). Our system, using Claude, will leverage its few-shot reasoning or chain-of-thought to do similar iterative refinement.

### 4. Result Composition

Once the query executes successfully, the raw result (rows from the database) may need to be formatted. We might not want to dump a large SQL table to the user. The agent can summarize or highlight the answer. For example, if the question was "How many customers signed up in 2023?", the SQL result might be a single number which can be directly answered. If it's a more complex result, the agent could say "I found the data, here's a summary…" and present it in a user-friendly way. This aligns with the Human-Friendly Output step described in the literature, where the LLM can convert query output into a helpful answer.

By implementing the database interaction as an MCP tool (`sql_query` for example), we keep the process modular. The agent's thought process might look like:

- User asks: "Show me the top 5 products by sales last month."
- Claude (agent) thinks and decides: This requires a database query.
- It calls `tools/list` on the DB MCP server (if not already done) to see available actions (maybe it finds `run_query`).
- Claude formulates a SQL: `"SELECT product_name, SUM(sales) AS total_sales FROM sales_table WHERE sale_date >= '2025-09-01' AND sale_date < '2025-10-01' GROUP BY product_name ORDER BY total_sales DESC LIMIT 5;"` (just an example).
- Claude issues a `tools/call` to the DB tool with that SQL.
- Suppose the tool returns an error: "Error: column product_name not found." Claude then realizes perhaps the table uses `name` instead. It revises the query and calls again (this loop is akin to what the LangChain SQL agent does, using the traceback for self-correction).
- The tool returns results: a table of 5 products and sales numbers. Claude then responds to the user in natural language: "The top 5 products last month were ProductA ($5000), ProductB ($4500), …" possibly formatting it nicely.

We will need to give Claude sufficient context to do this, possibly by including in the system prompt instructions on how to use the database tool, or even by providing an example. This is in line with Pattern III: Using SQL Agents, where an agent is equipped with tools (like a calculator, or in this case a DB API) and instructions on how to utilize them. LangChain's documentation confirms that their SQL agent for BigQuery works similarly, and we can mirror that logic.

Additionally, for large or complex schemas, we might incorporate a retrieval-augmented approach: e.g., use a vector store of schema or a semantic search to find which tables/columns are relevant (Pattern II from the Medium article). This could prevent the agent from hallucinating column names by ensuring it only sees real schema info. Our Document Ingestion module (with vector DB) could even be used to store database schema text and let Claude query it. But these are optimizations; initially we can start with direct schema inspection via the tool.

In summary, our approach to text-to-SQL will be agent-driven and interactive: the AI will use the MCP database tool to execute SQL and refine queries as needed, rather than one-shot prompting. This should result in more accurate and reliable database query answers, leveraging Claude's strength in code and iterative reasoning.

## Experiment Tracking and Model Management (MLflow)

While not directly related to the chat or tool protocols, it's worth noting how we plan to manage the development and tuning of our AI components. We intend to use MLflow for tracking experiments, prompt versions, and possibly model fine-tuning results.

MLflow is an open-source platform for the machine learning lifecycle, covering experiment tracking, reproducibility, model registry, and deployment. In our context, we will use it to:

### Track Prompt/Chain Experiments

As we try different prompt formulations or agent chain configurations, we can log these runs in MLflow. For instance, each change in the system prompt or each variation of a LangGraph workflow can be an MLflow run with parameters (prompt version, tools enabled, etc.) and metrics (accuracy on test queries, user feedback rating, etc.). MLflow's Tracking API will let us record these and compare results to decide which approach works best.

### Version Control AI Models

If we use or fine-tune models, MLflow's Model Registry provides a central store for models, with versioning and stage labels (e.g., "Staging", "Production"). Even though we primarily rely on external APIs (Claude, GPT-4), if we develop any custom models (say a re-ranker or classifier for filtering), we can register them in MLflow. The registry ensures we know which model version is deployed at any time and allows easy rollback if needed.

### Logging Outputs for Debugging

We can log artifacts like conversation transcripts or tool call logs for each session. This is useful for debugging the agent's behavior. For example, we could save a JSON of the conversation and tool calls when an error occurs, and MLflow will keep it under that run. LangChain's LangSmith is another tool for tracing, but MLflow can complement by keeping records tied to experimental conditions.

Using MLflow in our pipeline will make the development data-driven and reproducible. If Claude's behavior changes (due to a model update or prompt tweak), we'll have logs and metrics to quantify that. MLflow's UI or even just the logs will help the team collaboratively tune the system. It's essentially adding scientific rigor to our prompt engineering and tool integration efforts.

**Note**: We will integrate MLflow such that it does not interfere with the real-time performance. Possibly logging asynchronously or sampling some sessions for tracking. Given that MLflow is language-agnostic and supports logging from any Python code, we can instrument our LangGraph agents or FastAPI tool servers with MLflow client calls.

## Conclusion

By documenting and adhering to the OpenAI Chat Completions format and Model Context Protocol, we ensure our AI system speaks a common language with both the user and the myriad of tools it can utilize. The chat schema (system/user/assistant messages) will keep interactions consistent and easily portable to other models, while MCP provides a powerful, standardized way for Claude to safely extend its capabilities. We've also covered important complementary topics: using the OBO pattern for secure tool authentication (so the AI only does what each user is allowed to do), proven patterns for letting an AI agent write and execute SQL queries, and tools like MLflow to track our progress. With this groundwork, Claude (and any future model we use) has the best chance of success in our implementation: it will have the necessary context, the right tools, and a safety-conscious framework to operate effectively.

## Sources

The information above was compiled from official documentation and recent references, including Anthropic's announcement of MCP, the Model Context Protocol docs, OpenAI API documentation and community guides, and architectural insights from Medium articles on Text-to-SQL and Azure AD OBO flows. These sources are cited inline to provide more details on each topic.

### Referenced Documents and URLs

- Plan for Re-Authoring the GenAI Components with Claude Code 2.0 and LangChain.pdf
- Mastering Prompt Engineering: A Guide to System, User, and Assistant Roles in OpenAI API | by Mudassar Hakim | Medium: https://medium.com/@mudassar.hakim/mastering-prompt-engineering-a-guide-to-system-user-and-assistant-roles-in-openai-api-28fe5fbf1d81
- Start with a prebuilt agent: https://langchain-ai.github.io/langgraph/agents/agents/
- How to call functions with chat models: https://cookbook.openai.com/examples/how_to_call_functions_with_chat_models
- Chat Completions API Schema - Deep Java Library: https://docs.djl.ai/master/docs/serving/serving/docs/lmi/user_guides/chat_input_output_schema.html
- Introducing the Model Context Protocol \ Anthropic: https://www.anthropic.com/news/model-context-protocol
- What is the Model Context Protocol (MCP)? - Model Context Protocol: https://modelcontextprotocol.io/docs/getting-started/intro
- Architecture overview - Model Context Protocol: https://modelcontextprotocol.io/docs/learn/architecture
- Securing MCP Tools with Azure AD On-Behalf-Of (OBO) | by Saima Khan | Sep, 2025 | Medium: https://medium.com/@khansaima/securing-mcp-tools-with-azure-ad-on-behalf-of-obo-29b1ada1e505
- Security Models: On Behalf Of - Ayende @ Rahien: https://ayende.com/blog/4618/security-models-on-behalf-of
- Implement On-Behalf-Of Flow using C# Azure Function · Aakash Bhardwaj: https://aakashbhardwaj619.github.io/2021/07/27/Azure-Function-CSharp-OBO.html
- Architectural Patterns for Text-to-SQL: Leveraging LLMs for Enhanced BigQuery Interactions | by Arun Shankar | Google Cloud - Community | Medium: https://medium.com/google-cloud/architectural-patterns-for-text-to-sql-leveraging-llms-for-enhanced-bigquery-interactions-59756a749e15
- Demystifying MLflow: A Hands-on Guide to Experiment Tracking and ...: https://dspatil.medium.com/demystifying-mlflow-a-hands-on-guide-to-experiment-tracking-and-model-registry-d99b6bfd1bda
- mlflow/mlflow: The open source developer platform to build AI/LLM ...: https://github.com/mlflow/mlflow
- MLflow Tracking: https://mlflow.org/docs/latest/ml/tracking/
- MLflow Model Registry | MLflow: https://mlflow.org/docs/latest/ml/model-registry/
