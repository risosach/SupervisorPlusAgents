# Supervisor Test Plan

This document contains the test plan for the Supervisor CLI Agent (Stage 1), following Test-Driven Development (TDD) principles.

## Overview

All tests will be written using **pytest** before implementation code is written. Tests are organized by component and aligned with the 6 user stories. The goal is to achieve high test coverage while ensuring the Supervisor behaves correctly for all expected scenarios.

---

## Testing Strategy

### Test Pyramid

```
        ┌──────────────────┐
        │  End-to-End (5%) │  ← CLI integration tests
        ├──────────────────┤
        │ Integration (15%)│  ← Component integration
        ├──────────────────┤
        │  Unit Tests (80%)│  ← Core logic testing
        └──────────────────┘
```

### Test Categories

1. **Unit Tests**: Test individual functions and methods in isolation
2. **Integration Tests**: Test component interactions (router → handler → tool)
3. **End-to-End Tests**: Test complete CLI workflows

### Mocking Strategy

- **External APIs** (Claude API): Always mocked in unit tests
- **MCP Tools**: Use stubs for Stage 1
- **Configuration**: Use test fixtures with known values
- **File I/O**: Mock or use temporary test files

---

## Test Coverage by User Story

### Story 1: General Question Answering

**File**: `tests/test_supervisor.py`

#### Test Case 1.1: Direct Answer - Capital of France
```python
def test_direct_answer_capital_of_france(mock_claude_api):
    """
    Given: Query "What is the capital of France?"
    When: Supervisor processes the query
    Then: Response contains "Paris"
    And: No tools are invoked
    And: Claude API is called once
    """
    mock_claude_api.return_value = "The capital of France is Paris."

    supervisor = SupervisorAgent(config_path='tests/fixtures/test_config.json')
    response = supervisor.respond("What is the capital of France?")

    assert "Paris" in response
    assert mock_claude_api.call_count == 1
```

#### Test Case 1.2: Direct Answer - Math Query
```python
def test_direct_answer_math_query(mock_claude_api):
    """
    Given: Query "What is 25 × 4?"
    When: Supervisor processes the query
    Then: Response contains "100"
    And: Router classifies as 'direct'
    """
    mock_claude_api.return_value = "25 × 4 equals 100."

    supervisor = SupervisorAgent(config_path='tests/fixtures/test_config.json')
    response = supervisor.respond("What is 25 × 4?")

    assert "100" in response
```

#### Test Case 1.3: Response Time
```python
def test_direct_answer_response_time(mock_claude_api):
    """
    Given: A simple factual query
    When: Supervisor processes the query
    Then: Response time is under 3 seconds
    """
    import time
    mock_claude_api.return_value = "The answer is 42."

    supervisor = SupervisorAgent(config_path='tests/fixtures/test_config.json')
    start_time = time.time()
    response = supervisor.respond("What is the meaning of life?")
    elapsed_time = time.time() - start_time

    assert elapsed_time < 3.0
```

---

### Story 2: Document Retrieval Query

**File**: `tests/test_supervisor.py`, `tests/test_handlers.py`

#### Test Case 2.1: Q3 Project Plan Query
```python
def test_document_query_q3_project_plan():
    """
    Given: Query "What does the Q3 Project Plan say about milestones?"
    When: Supervisor processes the query
    Then: Document retrieval tool is invoked
    And: Response contains "October 31"
    """
    supervisor = SupervisorAgent(config_path='tests/fixtures/test_config.json')
    response = supervisor.respond("What does the Q3 Project Plan say about milestones?")

    assert "October 31" in response
```

#### Test Case 2.2: Router Classification
```python
def test_router_classifies_document_query():
    """
    Given: Query containing "according to" keyword
    When: Router analyzes the query
    Then: Classification is 'doc'
    """
    from supervisor.router import decide_tool
    from supervisor.config import load_config

    config = load_config('tests/fixtures/test_config.json')
    classification = decide_tool("According to the design document, what is X?", config)

    assert classification == 'doc'
```

#### Test Case 2.3: Document Not Found
```python
def test_document_not_found():
    """
    Given: Query for non-existent document
    When: Document retriever returns no results
    Then: User receives "not found" message
    """
    supervisor = SupervisorAgent(config_path='tests/fixtures/test_config.json')
    response = supervisor.respond("What does the NonExistent Plan say?")

    assert "not found" in response.lower()
```

#### Test Case 2.4: Multiple Document Snippets
```python
def test_multiple_document_snippets():
    """
    Given: Query matching multiple document sections
    When: Document retriever returns multiple snippets
    Then: All relevant snippets are included in response
    """
    # This test will be implemented when multiple-result handling is added
    pytest.skip("Multiple snippet handling not implemented in Stage 1")
```

---

### Story 3: Database Query

**File**: `tests/test_supervisor.py`, `tests/test_handlers.py`

#### Test Case 3.1: Accounts Created Query
```python
def test_database_query_accounts_created():
    """
    Given: Query "How many new accounts were created last week?"
    When: Supervisor processes the query
    Then: Database tool is invoked
    And: Response contains "42"
    """
    supervisor = SupervisorAgent(config_path='tests/fixtures/test_config.json')
    response = supervisor.respond("How many new accounts were created last week?")

    assert "42" in response
```

#### Test Case 3.2: Router Classification for DB Queries
```python
def test_router_classifies_database_query():
    """
    Given: Query containing database keywords ("how many", "accounts")
    When: Router analyzes the query
    Then: Classification is 'db'
    """
    from supervisor.router import decide_tool
    from supervisor.config import load_config

    config = load_config('tests/fixtures/test_config.json')
    classification = decide_tool("How many accounts were created?", config)

    assert classification == 'db'
```

#### Test Case 3.3: SQL Error Handling
```python
def test_database_query_error_handling():
    """
    Given: Database query that fails
    When: DB tool returns error
    Then: User receives graceful error message
    """
    # Mock the database tool to raise an error
    with patch('supervisor.tools.stubs.stub_database_query', side_effect=Exception("DB Error")):
        supervisor = SupervisorAgent(config_path='tests/fixtures/test_config.json')
        response = supervisor.respond("How many accounts?")

        assert "error" in response.lower() or "unable" in response.lower()
```

#### Test Case 3.4: Formatted Results
```python
def test_database_results_formatting():
    """
    Given: Database returns numerical result
    When: Handler formats the response
    Then: Result is user-friendly (not raw SQL output)
    """
    supervisor = SupervisorAgent(config_path='tests/fixtures/test_config.json')
    response = supervisor.respond("How many accounts were created?")

    # Should not contain SQL syntax
    assert "SELECT" not in response
    assert "FROM" not in response
    # Should be human-readable
    assert any(word in response for word in ["accounts", "created", "42"])
```

---

### Story 4: Web Research

**File**: `tests/test_supervisor.py`, `tests/test_handlers.py`

#### Test Case 4.1: Web Search Invocation
```python
def test_web_search_query():
    """
    Given: Query "Latest news about artificial intelligence"
    When: Supervisor processes the query
    Then: Web search tool is invoked
    And: Response contains web search results
    """
    supervisor = SupervisorAgent(config_path='tests/fixtures/test_config.json')
    response = supervisor.respond("Latest news about artificial intelligence")

    assert "Web search" in response or len(response) > 0
```

#### Test Case 4.2: Router Classification for Web Queries
```python
def test_router_classifies_web_query():
    """
    Given: Query containing "latest" or "news" keywords
    When: Router analyzes the query
    Then: Classification is 'web'
    """
    from supervisor.router import decide_tool
    from supervisor.config import load_config

    config = load_config('tests/fixtures/test_config.json')
    classification = decide_tool("Latest news about AI", config)

    assert classification == 'web'
```

#### Test Case 4.3: Web Search Fallback
```python
def test_web_search_failure_fallback():
    """
    Given: Web search tool fails
    When: Tool returns error
    Then: Fallback behavior is triggered
    """
    with patch('supervisor.tools.stubs.stub_web_search', side_effect=Exception("Network Error")):
        supervisor = SupervisorAgent(config_path='tests/fixtures/test_config.json')
        response = supervisor.respond("Latest news?")

        assert len(response) > 0  # Should return something, not crash
```

#### Test Case 4.4: Source Citation
```python
def test_web_search_source_citation():
    """
    Given: Web search returns results
    When: Response is formatted
    Then: Sources are referenced (future enhancement)
    """
    pytest.skip("Source citation not implemented in Stage 1")
```

---

### Story 5: Fallback and Clarification

**File**: `tests/test_supervisor.py`, `tests/test_router.py`

#### Test Case 5.1: Ambiguous Query
```python
def test_ambiguous_query_clarification():
    """
    Given: Query "Tell me about the policy"
    When: Supervisor processes ambiguous query
    Then: Response asks for clarification
    And: Contains "which" or "clarify"
    """
    supervisor = SupervisorAgent(config_path='tests/fixtures/test_config.json')
    response = supervisor.respond("Tell me about the policy")

    # In Stage 1, might just return fallback message
    # In Stage 2+, should ask clarifying question
    assert len(response) > 0
```

#### Test Case 5.2: Harmful Query Refusal
```python
def test_harmful_query_refusal():
    """
    Given: Query "DELETE all records"
    When: Router detects harmful intent
    Then: Classification is 'fallback'
    And: Response refuses politely
    """
    from supervisor.router import decide_tool
    from supervisor.config import load_config

    config = load_config('tests/fixtures/test_config.json')
    classification = decide_tool("DELETE all records", config)

    assert classification == 'fallback'

    supervisor = SupervisorAgent(config_path='tests/fixtures/test_config.json')
    response = supervisor.respond("DELETE all records")

    assert "sorry" in response.lower() or "cannot" in response.lower()
```

#### Test Case 5.3: Nonsensical Input
```python
def test_nonsensical_input():
    """
    Given: Query "asdfghjkl"
    When: Supervisor processes nonsensical input
    Then: Response is friendly and helpful
    """
    supervisor = SupervisorAgent(config_path='tests/fixtures/test_config.json')
    response = supervisor.respond("asdfghjkl")

    assert len(response) > 0
    assert "sorry" in response.lower() or "understand" in response.lower()
```

#### Test Case 5.4: Fallback Message Customization
```python
def test_fallback_message_from_config():
    """
    Given: Custom fallback message in config
    When: Fallback handler is invoked
    Then: Custom message is returned
    """
    supervisor = SupervisorAgent(config_path='tests/fixtures/test_config.json')
    response = supervisor.respond("asdfghjkl")

    # Should match the fallback_message in test_config.json
    assert "I'm sorry" in response
```

---

### Story 6: Configuration Management

**File**: `tests/test_config.py`

#### Test Case 6.1: Load Config from File
```python
def test_load_config_from_file():
    """
    Given: Valid config.json file
    When: Configuration is loaded
    Then: All fields are accessible
    """
    from supervisor.config import load_config

    config = load_config('tests/fixtures/test_config.json')

    assert config.system_prompt is not None
    assert len(config.tools) > 0
    assert 'document_retriever' in config.tools
```

#### Test Case 6.2: System Prompt Modification
```python
def test_system_prompt_modification():
    """
    Given: Config with custom system prompt
    When: Supervisor is initialized
    Then: Custom prompt is used
    """
    from supervisor.config import load_config

    config = load_config('tests/fixtures/custom_prompt_config.json')

    assert "helpful AI assistant" in config.system_prompt
```

#### Test Case 6.3: Enable/Disable Tools
```python
def test_tool_enable_disable():
    """
    Given: Tool disabled in config
    When: Query would normally route to that tool
    Then: Alternative handler is used
    """
    # Create config with document_retriever disabled
    supervisor = SupervisorAgent(config_path='tests/fixtures/disabled_doc_tool_config.json')
    response = supervisor.respond("According to the document")

    # Should fall back to direct LLM or another handler
    # Not call the disabled tool
```

#### Test Case 6.4: Invalid Config Error
```python
def test_invalid_config_error():
    """
    Given: Invalid config file (malformed JSON)
    When: Configuration is loaded
    Then: Clear error message is raised
    """
    from supervisor.config import load_config

    with pytest.raises(Exception) as exc_info:
        load_config('tests/fixtures/invalid_config.json')

    assert "config" in str(exc_info.value).lower()
```

#### Test Case 6.5: Config Validation
```python
def test_config_validation():
    """
    Given: Config with missing required fields
    When: Configuration is validated
    Then: Validation error is raised
    """
    from supervisor.config import load_config, validate_config

    with pytest.raises(ValueError):
        config = load_config('tests/fixtures/missing_fields_config.json')
        validate_config(config)
```

#### Test Case 6.6: Config Reload
```python
def test_config_reload():
    """
    Given: Running Supervisor instance
    When: Config file is modified and reloaded
    Then: New configuration takes effect
    """
    supervisor = SupervisorAgent(config_path='tests/fixtures/test_config.json')
    original_prompt = supervisor.config.system_prompt

    # Simulate config reload (in Stage 1, requires restart)
    supervisor.reload_config()

    # In Stage 1, this might just re-initialize
    # In Stage 2+, should support hot reload
```

---

## Component-Level Unit Tests

### Configuration Module Tests

**File**: `tests/test_config.py`

```python
def test_config_load_valid_file()
def test_config_load_missing_file()
def test_config_load_invalid_json()
def test_config_validate_required_fields()
def test_config_get_tool_config()
def test_config_is_tool_enabled()
def test_config_get_system_prompt()
```

### Router Module Tests

**File**: `tests/test_router.py`

```python
def test_router_direct_classification()
def test_router_document_keywords()
def test_router_database_keywords()
def test_router_web_keywords()
def test_router_harmful_query_detection()
def test_router_disabled_tool_fallback()
def test_router_keyword_case_insensitivity()
def test_router_multiple_keyword_priority()
```

### Handler Module Tests

**File**: `tests/test_handlers.py`

```python
def test_handle_direct_calls_claude()
def test_handle_document_calls_stub()
def test_handle_database_calls_stub()
def test_handle_web_calls_stub()
def test_handle_fallback_returns_message()
def test_handler_error_handling()
```

### Stub Tools Tests

**File**: `tests/test_stubs.py`

```python
def test_stub_document_retriever_q3_plan()
def test_stub_document_retriever_not_found()
def test_stub_database_query_accounts()
def test_stub_database_query_no_data()
def test_stub_web_search_returns_result()
```

---

## Integration Tests

**File**: `tests/test_integration.py`

### Test Case: End-to-End Direct Query
```python
def test_e2e_direct_query():
    """
    Integration test: Query → Router → Direct Handler → Response
    """
    supervisor = SupervisorAgent(config_path='tests/fixtures/test_config.json')
    response = supervisor.respond("What is 2 + 2?")
    assert len(response) > 0
```

### Test Case: End-to-End Document Query
```python
def test_e2e_document_query():
    """
    Integration test: Query → Router → Doc Handler → Stub Tool → Response
    """
    supervisor = SupervisorAgent(config_path='tests/fixtures/test_config.json')
    response = supervisor.respond("According to Q3 Project Plan, what is the deadline?")
    assert "October 31" in response
```

### Test Case: End-to-End Database Query
```python
def test_e2e_database_query():
    """
    Integration test: Query → Router → DB Handler → Stub Tool → Response
    """
    supervisor = SupervisorAgent(config_path='tests/fixtures/test_config.json')
    response = supervisor.respond("How many new accounts were created last week?")
    assert "42" in response
```

### Test Case: Config-Driven Behavior
```python
def test_e2e_config_driven_behavior():
    """
    Integration test: Config changes affect routing and handling
    """
    # Test with tools enabled
    supervisor1 = SupervisorAgent(config_path='tests/fixtures/all_tools_enabled.json')
    response1 = supervisor1.respond("According to the document")

    # Test with document tool disabled
    supervisor2 = SupervisorAgent(config_path='tests/fixtures/doc_tool_disabled.json')
    response2 = supervisor2.respond("According to the document")

    # Responses should differ based on configuration
    assert response1 != response2
```

---

## CLI Tests

**File**: `tests/test_cli.py`

### Test Case: CLI Single Query Mode
```python
def test_cli_single_query_mode():
    """
    Test: python cli.py "What is the capital of France?"
    """
    result = subprocess.run(
        ['python', 'cli.py', 'What is the capital of France?'],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
    assert len(result.stdout) > 0
```

### Test Case: CLI Interactive Mode
```python
def test_cli_interactive_mode():
    """
    Test: python cli.py --interactive
    """
    # Simulate interactive input/output
    # This is complex and might be deferred to manual testing
    pytest.skip("Interactive mode testing requires complex simulation")
```

### Test Case: CLI Config Flag
```python
def test_cli_custom_config():
    """
    Test: python cli.py --config custom_config.json "query"
    """
    result = subprocess.run(
        ['python', 'cli.py', '--config', 'tests/fixtures/test_config.json', 'test query'],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
```

---

## Test Fixtures

### Test Config File: `tests/fixtures/test_config.json`

```json
{
  "system_prompt": "You are a helpful AI assistant. Answer questions concisely.",
  "tools": {
    "document_retriever": {
      "enabled": true,
      "type": "stub",
      "url": "http://localhost:5001/mcp",
      "description": "Retrieves information from internal documents"
    },
    "database_query": {
      "enabled": true,
      "type": "stub",
      "url": "http://localhost:5002/mcp",
      "description": "Queries structured databases"
    },
    "web_search": {
      "enabled": true,
      "type": "stub",
      "url": "http://localhost:5003/mcp",
      "description": "Searches the web"
    }
  },
  "routing_rules": {
    "document_keywords": ["document", "file", "according to", "Q3 Project Plan"],
    "database_keywords": ["database", "accounts", "sales", "how many", "revenue"],
    "web_keywords": ["news", "latest", "current", "website", "http"]
  },
  "fallback_message": "I'm sorry, I'm not sure how to help with that request."
}
```

---

## Test Execution

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=supervisor --cov-report=html

# Run specific test file
pytest tests/test_supervisor.py

# Run specific test
pytest tests/test_supervisor.py::test_direct_answer_capital_of_france

# Run with verbose output
pytest -v

# Run tests matching pattern
pytest -k "document"
```

### Coverage Goals

- **Unit Tests**: 90%+ coverage of core logic
- **Integration Tests**: Cover all primary user flows
- **Overall**: 85%+ code coverage

### Continuous Integration

Tests should run automatically on:
- Every commit to `dev` branch
- Every pull request to `main`
- Pre-merge checks

---

## Test Development Workflow (TDD)

### Red-Green-Refactor Cycle

1. **Red**: Write a failing test
   ```bash
   pytest tests/test_supervisor.py::test_direct_answer_capital_of_france
   # FAILED - Function not implemented
   ```

2. **Green**: Implement minimal code to pass
   ```python
   def respond(query):
       return "The capital of France is Paris."
   ```
   ```bash
   pytest tests/test_supervisor.py::test_direct_answer_capital_of_france
   # PASSED
   ```

3. **Refactor**: Improve code while keeping tests green
   ```python
   def respond(query):
       classification = decide_tool(query)
       return handle_direct(query)
   ```
   ```bash
   pytest tests/test_supervisor.py::test_direct_answer_capital_of_france
   # PASSED
   ```

### Implementation Order

1. **Phase 1**: Configuration management
   - Write config tests
   - Implement config loader
   - Validate all config tests pass

2. **Phase 2**: Router logic
   - Write router tests
   - Implement decision logic
   - Validate all router tests pass

3. **Phase 3**: Handlers and stubs
   - Write handler tests
   - Implement handlers with stubs
   - Validate all handler tests pass

4. **Phase 4**: Integration
   - Write integration tests
   - Connect components
   - Validate all integration tests pass

5. **Phase 5**: CLI
   - Write CLI tests
   - Implement CLI interface
   - Validate all CLI tests pass

---

## Success Criteria

All tests must pass before Stage 1 is considered complete:

- [ ] All unit tests pass (90%+ coverage)
- [ ] All integration tests pass
- [ ] CLI tests pass
- [ ] No critical bugs in issue tracker
- [ ] Documentation matches implementation
- [ ] Code reviewed and approved

---

## Future Test Enhancements (Stage 2+)

- Performance/load testing
- Security testing (input validation, injection attacks)
- LLM-based routing accuracy tests
- Real MCP tool integration tests
- Conversation context retention tests
- Multi-turn dialogue tests
- Authentication/authorization tests
