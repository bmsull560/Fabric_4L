"""State manager for workflow state persistence using Redis."""

import json
import logging
from typing import Any, Dict, Optional, TYPE_CHECKING
from datetime import datetime, timezone

from ..models.agent_state import AgentState, WorkflowStatus

if TYPE_CHECKING:
    from ..api.websocket.manager import WorkflowWebSocketManager

logger = logging.getLogger(__name__)


class StateManager:
    """Manages workflow state persistence using Redis.
    
    Provides:
    - State storage and retrieval
    - Workflow status tracking
    - History recording
    - Real-time WebSocket broadcasting
    
    Example:
        manager = StateManager(redis_client)
        await manager.save_state(workflow_id, state)
        state = await manager.load_state(workflow_id)
    """
    
    def __init__(self, redis_client=None, ws_manager: Optional['WorkflowWebSocketManager'] = None):
        """Initialize state manager.
        
        Args:
            redis_client: Redis client instance (optional)
            ws_manager: WebSocket manager for real-time streaming (optional)
        """
        self.redis = redis_client
        self._memory_store: Dict[str, Dict] = {}  # Fallback if no Redis
        self._ws_manager: Optional['WorkflowWebSocketManager'] = ws_manager
    
    def _get_key(self, workflow_id: str) -> str:
        """Generate Redis key for workflow state."""
        return f"layer4:workflow:{workflow_id}"
    
    def _get_history_key(self, workflow_id: str) -> str:
        """Generate Redis key for workflow history."""
        return f"layer4:workflow:{workflow_id}:history"
    
    def set_ws_manager(self, ws_manager: 'WorkflowWebSocketManager') -> None:
        """Set WebSocket manager for real-time broadcasting."""
        self._ws_manager = ws_manager
    
    async def save_state(
        self,
        workflow_id: str,
        state: AgentState,
        ttl_seconds: int = 86400  # 24 hours default
    ) -> None:
        """Save workflow state and broadcast update.
        
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
                "expires": datetime.now(timezone.utc).timestamp() + ttl_seconds
            }
        
        # Broadcast state update via WebSocket
        if self._ws_manager:
            try:
                await self._ws_manager.broadcast_state_update(
                    workflow_id=workflow_id,
                    status=state.status.value if hasattr(state.status, 'value') else str(state.status),
                    current_node=state.current_node,
                    progress_percentage=self._calculate_progress(state),
                    output_data=state_dict.get("output_data"),
                    pause_point=state_dict.get("pause_point")
                )
            except Exception as e:
                logger.warning(f"Failed to broadcast state update: {e}")
    
    def _calculate_progress(self, state: AgentState) -> float:
        """Calculate workflow progress percentage."""
        # Simple heuristic: if completed, 100%; if failed, 0%;
        # otherwise estimate based on status
        status = state.status
        if status == WorkflowStatus.COMPLETED:
            return 100.0
        elif status == WorkflowStatus.FAILED:
            return 0.0
        elif status == WorkflowStatus.PAUSED:
            # Estimate based on whether we have output
            return 50.0 if state.output_data else 25.0
        elif status == WorkflowStatus.RUNNING:
            return 10.0
        else:
            return 0.0
    
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
                try:
                    state_dict = json.loads(data)
                    return self._deserialize_state(state_dict)
                except json.JSONDecodeError:
                    logger.error(f"Failed to parse state JSON for workflow {workflow_id}")
                    return None
        else:
            stored = self._memory_store.get(key)
            if stored and stored["expires"] > datetime.now(timezone.utc).timestamp():
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
            "timestamp": datetime.now(timezone.utc).isoformat(),
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
            history = []
            for d in data:
                try:
                    history.append(json.loads(d))
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse history entry for workflow {workflow_id}")
                    continue
            return history
        else:
            history_key = f"{workflow_id}:history"
            history = self._memory_store.get(history_key, [])
            return history[:limit]
