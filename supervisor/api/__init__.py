"""
Supervisor API Module - OpenAI-compatible interfaces.

This module provides OpenAI Chat Completions-compatible interfaces
for the Supervisor Agent, enabling integration with tools that expect
OpenAI's API format.
"""

from supervisor.api.openai_adapter import (
    ChatMessage,
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatCompletionChoice,
    ChatCompletionUsage,
    create_chat_completion,
    create_chat_completion_from_dict
)

__all__ = [
    'ChatMessage',
    'ChatCompletionRequest',
    'ChatCompletionResponse',
    'ChatCompletionChoice',
    'ChatCompletionUsage',
    'create_chat_completion',
    'create_chat_completion_from_dict'
]
