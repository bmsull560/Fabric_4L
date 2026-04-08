"""Multi-agent messaging system for Layer 4.

Provides pub/sub messaging, message routing, and inter-agent communication.
"""

from .types import MessageType, AgentMessage, MessagePriority
from .bus import MessageBus, InMemoryMessageBus, RedisMessageBus
from .router import MessageRouter

__all__ = [
    "MessageType",
    "AgentMessage",
    "MessagePriority",
    "MessageBus",
    "InMemoryMessageBus",
    "RedisMessageBus",
    "MessageRouter",
]
