"""Conversation memory module."""

from collections import deque
from collections.abc import Sequence

from app.tutor.providers.llm import LLMMessage

class ConversationMemory:
    """Stores a sliding window of recent conversation history."""
    
    def __init__(self, max_turns: int = 4) -> None:
        self.max_turns = max_turns
        self.messages: deque[LLMMessage] = deque(maxlen=max_turns * 2)
        
    def add_user_message(self, content: str) -> None:
        self.messages.append(LLMMessage(role="user", content=content))
        
    def add_assistant_message(self, content: str) -> None:
        self.messages.append(LLMMessage(role="assistant", content=content))
        
    def get_history(self) -> Sequence[LLMMessage]:
        return list(self.messages)
