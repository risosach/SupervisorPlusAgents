# User Stories

This document contains user stories for the Supervisor CLI Agent (Stage 1).

## Overview

The Supervisor CLI Agent is the central orchestrator that interprets user queries and routes them to appropriate handlers or tools. These user stories define the core functionality for Stage 1, where the Supervisor uses rule-based decision logic and stub MCP tools.

---

## Story 1: General Question Answering

**As an** end-user
**I want** the assistant to answer general knowledge questions directly
**So that** I get quick answers without unnecessary tool invocations

### Example Queries
- "What is the capital of France?"
- "Who invented the telephone?"
- "What is 25 × 4?"

### Expected Behavior
The Supervisor detects this is a general knowledge query and uses the LLM (Claude) directly to provide an answer, without invoking document retrieval, database, or web search tools.

### Acceptance Criteria
- [ ] Query "What is the capital of France?" returns answer containing "Paris"
- [ ] No document retrieval tool is invoked for general queries
- [ ] Response time is under 3 seconds for simple factual questions
- [ ] Answer is concise and directly addresses the question

---

## Story 2: Document Retrieval Query

**As an** end-user
**I want** the assistant to search my uploaded documents when I ask about internal content
**So that** I get accurate, relevant information from our files

### Example Queries
- "What does the Q3 Project Plan say about milestones?"
- "According to the design document, what is the deadline?"
- "Find information about the authentication flow in our documentation"

### Expected Behavior
The Supervisor recognizes document-related queries through keywords like "document," "according to," "file," or specific document names, and routes to the Document Retriever tool.

### Acceptance Criteria
- [ ] Query about Q3 Project Plan routes to document retrieval tool
- [ ] Response includes information retrieved from the document (e.g., "October 31")
- [ ] If document not found, system provides clear "not found" message
- [ ] Retrieved content is properly attributed to source document
- [ ] Multiple relevant snippets are combined when appropriate

---

## Story 3: Database Query

**As an** analyst user
**I want** the assistant to retrieve data from our database using natural language
**So that** I can get up-to-date numbers or records without writing SQL

### Example Queries
- "How many new accounts were created last week?"
- "What is the total revenue for Q3?"
- "Show me the top 5 customers by purchase volume"

### Expected Behavior
The Supervisor identifies data-oriented queries through keywords like "how many," "accounts," "database," "sales," etc., and routes to the Database Retriever (text-to-SQL) tool.

### Acceptance Criteria
- [ ] Query about accounts created routes to database tool
- [ ] Response includes the numerical result (e.g., "42 new accounts")
- [ ] Result is formatted in a user-friendly way (not raw SQL output)
- [ ] If query cannot be translated to SQL, user receives explanation
- [ ] Database errors are caught and reported gracefully

---

## Story 4: Web Research

**As an** end-user
**I want** the assistant to search the web for current information
**So that** I can access latest news and external knowledge not in our system

### Example Queries
- "What are people saying about our competitor's new product?"
- "Latest news about artificial intelligence"
- "Current price of Bitcoin"

### Expected Behavior
The Supervisor detects queries requiring external/current information through keywords like "news," "latest," "current," "website," or when the topic is clearly outside internal scope, and routes to Web Search tool.

### Acceptance Criteria
- [ ] Query about external/current events routes to web search tool
- [ ] Response includes information from web sources
- [ ] Web sources are cited or referenced in the response
- [ ] If web search fails, fallback behavior is triggered
- [ ] Results are summarized rather than raw search results

---

## Story 5: Fallback and Clarification

**As an** end-user
**I want** the assistant to gracefully handle unclear or problematic queries
**So that** I'm not left frustrated and can get help refining my request

### Example Queries
- "Tell me about the policy" (ambiguous)
- "DELETE all records" (potentially harmful)
- "asdfghjkl" (nonsensical)

### Expected Behavior
The Supervisor identifies ambiguous, potentially harmful, or incomprehensible queries and responds appropriately:
- For ambiguous queries: asks clarifying questions
- For harmful queries: refuses politely
- For nonsensical input: provides helpful guidance

### Acceptance Criteria
- [ ] Ambiguous query prompts for clarification (e.g., "Which policy are you referring to?")
- [ ] Potentially harmful commands are refused with explanation
- [ ] Nonsensical input receives friendly "I don't understand" response
- [ ] Fallback responses are polite and helpful
- [ ] User is guided toward valid query patterns

---

## Story 6: Configuration Management

**As a** system administrator
**I want** to update the Supervisor's behavior via configuration
**So that** I can tune the system without modifying code

### Configuration Elements
- System prompt (defines agent behavior and tone)
- Available tools and their endpoints
- Decision routing rules
- Fallback messages
- Logging preferences

### Expected Behavior
The Supervisor loads configuration from `config.json` (or equivalent) at startup. Changes to configuration take effect on next startup or reload.

### Acceptance Criteria
- [ ] Supervisor reads configuration from `config.json` on startup
- [ ] System prompt can be modified via config
- [ ] Tools can be enabled/disabled via config
- [ ] Invalid configuration triggers clear error message
- [ ] Configuration reload works without code changes
- [ ] Config validation catches common errors (missing fields, invalid URLs)

---

## Future Enhancements (Post-Stage 1)

These stories are deferred to later stages:

- **Document Summarization**: "Summarize this 50-page report"
- **Document Comparison**: "What changed between version 1 and 2?"
- **Multi-turn Conversations**: Context retention across multiple exchanges
- **User Authentication**: Per-user permissions and document access
- **Visualization**: "Create a chart showing Q3 revenue trends"
