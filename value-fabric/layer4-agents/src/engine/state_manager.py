"""State manager for workflow state persistence using Redis."""

import json
from typing import Any, Dict, Optional
from datetime import datetime

from ..models.agent_state import AgentState, WorkflowStatus


class StateManager:
    """Manages workflow state persistence using Redis.
    
    Provides:
    - State storage and retrieval
    - Workflow status tracking
    - History recording
    
    Example:
        manager = StateManager(redis_client)
        await manager.save_state(workflow_id, state)
        state = await manager.load_state(workflow_id)
    """
    
    def __init__(self, redis_client=None):
        """Initialize state manager.
        
        Args:
            redis_client: Redis client instance (optional)
        """
        self.redis = redis_client
        self._memory_store: Dict[str, Dict] = {}  # Fallback if no Redis
    
    def _get_key(self, workflow_id: str) -> str:
        """Generate Redis key for workflow state."""
        return f"layer4:workflow:{workflow_id}"
    
    def _get_history_key(self, workflow_id: str) -> str:
        """Generate Redis key for workflow history."""
        return f"layer4:workflow:{workflow_id}:history"
    
    async def save_state(
        self,
        workflow_id: str,
        state: AgentState,
        ttl_seconds: int = 86400  # 24 hours default
    ) -> None:
        """Save workflow state.
        
        Args:
            workflow_id: Workflow identifier
            state: Current workflow state
            ttl_seconds: Time to live for Redis key
        """
        key = self._get_key(workflow_id)
        
        # Serialize state
        state_dict = state.model_dump()
        state_json = json.dumps(state_dict, default=str)
        
        if self.redis:
            await self.redis.setex(key, ttl_seconds, state_json)
        else:
            self._memory_store[key] = {
                "data": state_dict,
                "expires": datetime.utcnow().timestamp() + ttl_seconds
            }
    
    async def load_state(self, workflow_id: str) -> Optional[AgentState]:
        """Load workflow state.
        
        Args:
            workflow_id: Workflow identifier
            
        Returns:
            Workflow state or None if not found
        """
        key = self._get_key(workflow_id)
        
        if self.redis:
            data = await self.redis.get(key)
            if data:
                state_dict = json.loads(data)
                return self._deserialize_state(state_dict)
        else:
            stored = self._memory_store.get(key)
            if stored and stored["expires"] > datetime.utcnow().timestamp():
                return self._deserialize_state(stored["data"])
        
        return None
    
    def _deserialize_state(self, state_dict: Dict[str, Any]) -> AgentState:
        """Deserialize state dict to appropriate state type."""
        from ..models.agent_state import (
            ROIAgentState,
            WhitespaceAgentState,
            BusinessCaseAgentState,
        )
        
        workflow_type = state_dict.get("workflow_type")
        
        # Map to correct state type
        type_map = {
            "roi_calculator": ROIAgentState,
            "whitespace_analysis": WhitespaceAgentState,
            "business_case": BusinessCaseAgentState,
        }
        
        state_class = type_map.get(workflow_type, AgentState)
        
        # Parse datetime fields
        for field in ["started_at", "completed_at", "extracted_at"]:
            if state_dict.get(field) and isinstance(state_dict[field], str):
                try:
                    state_dict[field] = datetime.fromisoformat(state_dict[field].replace("Z", "+00:00"))
                except ValueError:
                    pass
        
        return state_class(**state_dict)
    
    async def delete_state(self, workflow_id: str) -> None:
        """Delete workflow state."""
        key = self._get_key(workflow_id)
        
        if self.redis:
            await self.redis.delete(key)
        else:
            self._memory_store.pop(key, None)
    
    async def record_history(
        self,
        workflow_id: str,
        node_id: str,
        input_data: Dict,
        output_data: Dict,
        duration_ms: int
    ) -> None:
        """Record node execution history.
        
        Args:
            workflow_id: Workflow identifier
            node_id: Node that executed
            input_data: Node input
            output_data: Node output
            duration_ms: Execution duration
        """
        key = self._get_history_key(workflow_id)
        
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "node_id": node_id,
            "input_summary": self._summarize(input_data),
            "output_summary": self._summarize(output_data),
            "duration_ms": duration_ms
        }
        
        if self.redis:
            await self.redis.lpush(key, json.dumps(entry))
            await self.redis.ltrim(key, 0, 99)  # Keep last 100
        else:
            history_key = f"{workflow_id}:history"
            if history_key not in self._memory_store:
                self._memory_store[history_key] = []
            self._memory_store[history_key].insert(0, entry)
            self._memory_store[history_key] = self._memory_store[history_key][:100]
    
    def _summarize(self, data: Dict, max_length: int = 200) -> str:
        """Create summary of data for history."""
        text = json.dumps(data, default=str)
        if len(text) > max_length:
            return text[:max_length] + "..."
        return text
    
    async def get_history(self, workflow_id: str, limit: int = 50) -> list:
        """Get execution history for workflow."""
        key = self._get_history_key(workflow_id)
        
        if self.redis:
            data = await self.redis.lrange(key, 0, limit - 1)
            return [json.loads(d) for d in data]
        else:
            history_key = f"{workflow_id}:history"
            history = self._memory_store.get(history_key, [])
            return history[:limit]
