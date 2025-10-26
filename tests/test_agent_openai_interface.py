"""
Tests for OpenAI Chat Completions API compatibility.

This module tests the Supervisor's OpenAI-compatible interface,
ensuring it properly accepts Chat Completions requests and returns
properly formatted responses.
"""

import pytest
from supervisor.api import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatMessage,
    create_chat_completion,
    create_chat_completion_from_dict
)


class TestChatCompletionSchema:
    """Test Chat Completions API schema compliance."""

    def test_chat_message_creation(self):
        """
        Given: Valid role and content
        When: Creating a ChatMessage
        Then: Message is created with correct attributes
        """
        message = ChatMessage(role="user", content="Hello")

        assert message.role == "user"
        assert message.content == "Hello"

    def test_chat_message_validation(self):
        """
        Given: Invalid role
        When: Creating a ChatMessage
        Then: Validation error is raised
        """
        with pytest.raises(Exception):  # Pydantic validation error
            ChatMessage(role="invalid", content="Hello")

    def test_chat_completion_request_creation(self):
        """
        Given: Valid messages and model
        When: Creating a ChatCompletionRequest
        Then: Request is created with correct attributes
        """
        messages = [ChatMessage(role="user", content="Hello")]
        request = ChatCompletionRequest(
            messages=messages,
            model="claude-3-5-haiku-20241022"
        )

        assert len(request.messages) == 1
        assert request.model == "claude-3-5-haiku-20241022"
        assert request.temperature == 1.0  # default
        assert request.stream is False  # default

    def test_chat_completion_request_with_options(self):
        """
        Given: Messages with additional options
        When: Creating a ChatCompletionRequest
        Then: All options are set correctly
        """
        messages = [ChatMessage(role="user", content="Hello")]
        request = ChatCompletionRequest(
            messages=messages,
            model="claude-3-5-sonnet-20241022",
            temperature=0.5,
            max_tokens=100
        )

        assert request.temperature == 0.5
        assert request.max_tokens == 100


class TestDirectQuery:
    """Test direct LLM queries through OpenAI interface."""

    def test_direct_query_routing(self):
        """
        Given: General knowledge query
        When: Sending via Chat Completions API
        Then: Routes to direct LLM handler
        """
        request = ChatCompletionRequest(
            messages=[ChatMessage(role="user", content="What is the capital of France?")],
            model="claude-3-5-haiku-20241022"
        )

        response = create_chat_completion(request, config_path='tests/fixtures/test_config.json')

        assert isinstance(response, ChatCompletionResponse)
        assert response.object == "chat.completion"
        assert len(response.choices) == 1
        assert response.choices[0].message.role == "assistant"
        assert len(response.choices[0].message.content) > 0
        # Should contain stub response indicator
        assert "Stub Claude API Response" in response.choices[0].message.content or "France" in response.choices[0].message.content

    def test_math_query(self):
        """
        Given: Math query
        When: Sending via Chat Completions API
        Then: Returns answer from direct LLM
        """
        request = ChatCompletionRequest(
            messages=[ChatMessage(role="user", content="What is 2+2?")],
            model="claude-3-5-haiku-20241022"
        )

        response = create_chat_completion(request, config_path='tests/fixtures/test_config.json')

        assert response.choices[0].message.role == "assistant"
        assert len(response.choices[0].message.content) > 0


class TestDocumentRetriever:
    """Test document retrieval through OpenAI interface."""

    def test_document_query_routing(self):
        """
        Given: Query about internal documents
        When: Sending via Chat Completions API
        Then: Routes to document retriever MCP tool
        """
        request = ChatCompletionRequest(
            messages=[ChatMessage(role="user", content="What does the Q3 Project Plan say about milestones?")],
            model="claude-3-5-haiku-20241022"
        )

        response = create_chat_completion(request, config_path='tests/fixtures/test_config.json')

        assert isinstance(response, ChatCompletionResponse)
        assert response.choices[0].message.role == "assistant"
        content = response.choices[0].message.content

        # Should contain information from Q3 Project Plan
        assert "October 31" in content or "Q3" in content

    def test_document_not_found(self):
        """
        Given: Query for non-existent document
        When: Sending via Chat Completions API
        Then: Returns appropriate not found message
        """
        request = ChatCompletionRequest(
            messages=[ChatMessage(role="user", content="According to the Nonexistent Document...")],
            model="claude-3-5-haiku-20241022"
        )

        response = create_chat_completion(request, config_path='tests/fixtures/test_config.json')

        content = response.choices[0].message.content
        # Should indicate document not found
        assert "not found" in content.lower() or "couldn't find" in content.lower()


class TestDatabaseQuery:
    """Test database queries through OpenAI interface."""

    def test_database_query_routing(self):
        """
        Given: Query for database metrics
        When: Sending via Chat Completions API
        Then: Routes to database query MCP tool
        """
        request = ChatCompletionRequest(
            messages=[ChatMessage(role="user", content="How many accounts were created last week?")],
            model="claude-3-5-haiku-20241022"
        )

        response = create_chat_completion(request, config_path='tests/fixtures/test_config.json')

        assert isinstance(response, ChatCompletionResponse)
        content = response.choices[0].message.content

        # Should contain database result
        assert "account" in content.lower() or "42" in content

    def test_database_count_query(self):
        """
        Given: Count query
        When: Sending via Chat Completions API
        Then: Returns response from database
        """
        request = ChatCompletionRequest(
            messages=[ChatMessage(role="user", content="How many users do we have?")],
            model="claude-3-5-haiku-20241022"
        )

        response = create_chat_completion(request, config_path='tests/fixtures/test_config.json')

        content = response.choices[0].message.content
        # Should have a response (content not empty)
        assert len(content) > 0


class TestResponseFormat:
    """Test Chat Completions response format compliance."""

    def test_response_has_required_fields(self):
        """
        Given: Any query
        When: Processing via Chat Completions API
        Then: Response has all required fields
        """
        request = ChatCompletionRequest(
            messages=[ChatMessage(role="user", content="Hello")],
            model="claude-3-5-haiku-20241022"
        )

        response = create_chat_completion(request, config_path='tests/fixtures/test_config.json')

        # Check required fields
        assert response.id.startswith("chatcmpl-")
        assert response.object == "chat.completion"
        assert response.created > 0
        assert response.model == "claude-3-5-haiku-20241022"
        assert len(response.choices) > 0
        assert response.usage is not None

    def test_response_usage_information(self):
        """
        Given: Any query
        When: Processing via Chat Completions API
        Then: Usage information is provided
        """
        request = ChatCompletionRequest(
            messages=[ChatMessage(role="user", content="What is AI?")],
            model="claude-3-5-haiku-20241022"
        )

        response = create_chat_completion(request, config_path='tests/fixtures/test_config.json')

        # Check usage information
        assert response.usage.prompt_tokens > 0
        assert response.usage.completion_tokens > 0
        assert response.usage.total_tokens == response.usage.prompt_tokens + response.usage.completion_tokens

    def test_response_finish_reason(self):
        """
        Given: Any query
        When: Processing via Chat Completions API
        Then: Finish reason is set correctly
        """
        request = ChatCompletionRequest(
            messages=[ChatMessage(role="user", content="Hello")],
            model="claude-3-5-haiku-20241022"
        )

        response = create_chat_completion(request, config_path='tests/fixtures/test_config.json')

        assert response.choices[0].finish_reason == "stop"


class TestConversationHistory:
    """Test multi-turn conversation handling."""

    def test_multi_turn_conversation(self):
        """
        Given: Multiple messages in conversation history
        When: Processing via Chat Completions API
        Then: Uses latest user message for routing
        """
        request = ChatCompletionRequest(
            messages=[
                ChatMessage(role="system", content="You are a helpful assistant."),
                ChatMessage(role="user", content="Hello"),
                ChatMessage(role="assistant", content="Hi! How can I help?"),
                ChatMessage(role="user", content="What is the capital of France?")
            ],
            model="claude-3-5-haiku-20241022"
        )

        response = create_chat_completion(request, config_path='tests/fixtures/test_config.json')

        # Should respond to the latest user message
        assert len(response.choices[0].message.content) > 0

    def test_system_message_handling(self):
        """
        Given: System message in conversation
        When: Processing via Chat Completions API
        Then: System message is accepted but routing based on user message
        """
        request = ChatCompletionRequest(
            messages=[
                ChatMessage(role="system", content="You are an expert assistant."),
                ChatMessage(role="user", content="What is 2+2?")
            ],
            model="claude-3-5-haiku-20241022"
        )

        response = create_chat_completion(request, config_path='tests/fixtures/test_config.json')

        # Should respond successfully
        assert len(response.choices[0].message.content) > 0


class TestErrorHandling:
    """Test error handling in OpenAI interface."""

    def test_empty_messages_list(self):
        """
        Given: Empty messages list
        When: Creating chat completion
        Then: Raises ValueError
        """
        request = ChatCompletionRequest(
            messages=[],
            model="claude-3-5-haiku-20241022"
        )

        with pytest.raises(ValueError, match="Messages list cannot be empty"):
            create_chat_completion(request, config_path='tests/fixtures/test_config.json')

    def test_no_user_messages(self):
        """
        Given: Messages without user role
        When: Creating chat completion
        Then: Raises ValueError
        """
        request = ChatCompletionRequest(
            messages=[ChatMessage(role="system", content="You are helpful")],
            model="claude-3-5-haiku-20241022"
        )

        with pytest.raises(ValueError, match="No user messages found"):
            create_chat_completion(request, config_path='tests/fixtures/test_config.json')

    def test_streaming_not_supported(self):
        """
        Given: Request with streaming enabled
        When: Creating chat completion
        Then: Raises NotImplementedError
        """
        request = ChatCompletionRequest(
            messages=[ChatMessage(role="user", content="Hello")],
            model="claude-3-5-haiku-20241022",
            stream=True
        )

        with pytest.raises(NotImplementedError, match="Streaming is not yet supported"):
            create_chat_completion(request, config_path='tests/fixtures/test_config.json')


class TestDictionaryInterface:
    """Test dictionary-based interface for Chat Completions."""

    def test_create_from_dict(self):
        """
        Given: Dictionary request
        When: Using create_chat_completion_from_dict
        Then: Returns dictionary response
        """
        request_dict = {
            "messages": [{"role": "user", "content": "Hello"}],
            "model": "claude-3-5-haiku-20241022"
        }

        response_dict = create_chat_completion_from_dict(
            request_dict,
            config_path='tests/fixtures/test_config.json'
        )

        assert isinstance(response_dict, dict)
        assert "id" in response_dict
        assert "choices" in response_dict
        assert len(response_dict["choices"]) > 0
        assert "message" in response_dict["choices"][0]
        assert response_dict["choices"][0]["message"]["role"] == "assistant"

    def test_dict_response_format(self):
        """
        Given: Dictionary request
        When: Processing
        Then: Response matches OpenAI schema
        """
        request_dict = {
            "messages": [{"role": "user", "content": "What is AI?"}],
            "model": "claude-3-5-haiku-20241022",
            "temperature": 0.7
        }

        response_dict = create_chat_completion_from_dict(
            request_dict,
            config_path='tests/fixtures/test_config.json'
        )

        # Check schema compliance
        assert response_dict["object"] == "chat.completion"
        assert "created" in response_dict
        assert "usage" in response_dict
        assert "prompt_tokens" in response_dict["usage"]
        assert "completion_tokens" in response_dict["usage"]
        assert "total_tokens" in response_dict["usage"]
