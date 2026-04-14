"""Real LangGraph workflow execution tests with InMemory checkpointing.

Tier A: Fast tests using InMemorySaver (no Redis required).
Validates actual LangGraph execution, not mocks.

Key scenarios:
- Workflow executes and terminates deterministically
- Recursion limit enforced
- Checkpoint saved at each node
- State accumulates output across nodes
- Thread-based checkpoint isolation
"""

import pytest
from typing import Annotated, Any, TypedDict

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import InMemorySaver

from src.workflows.base import DEFAULT_RECURSION_LIMIT


def _last(left: Any, right: Any) -> Any:
    """Reducer: keep the most recent value."""
    return right


def _merge(left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
    """Reducer: shallow-merge dicts, right wins on conflict."""
    return {**left, **right}


class TestState(TypedDict, total=False):
    """Lightweight LangGraph state schema for orchestration tests."""

    workflow_id: str
    status: Annotated[str, _last]
    current_node: Annotated[str, _last]
    output_data: Annotated[dict[str, Any], _merge]
    errors: list[str]


def _make_initial_state(
    workflow_id: str = "wf-test",
    pre_existing_output: dict[str, Any] | None = None,
) -> TestState:
    """Build a fresh initial state dict for test invocation."""
    return {
        "workflow_id": workflow_id,
        "status": "pending",
        "output_data": pre_existing_output or {},
        "errors": [],
    }


def _build_simple_graph(checkpointer=None) -> Any:
    """Build a simple START → PROCESS → END graph."""
    async def start_node(state: TestState) -> dict:
        return {"current_node": "start", "status": "running"}

    async def process_node(state: TestState) -> dict:
        output = state.get("output_data", {})
        return {"current_node": "process", "output_data": {**output, "process": "done"}, "status": "running"}

    async def end_node(state: TestState) -> dict:
        output = state.get("output_data", {})
        return {"current_node": "end", "output_data": {**output, "end": "done"}, "status": "completed"}

    graph = StateGraph(TestState)
    graph.add_node("start", start_node)
    graph.add_node("process", process_node)
    graph.add_node("end_node", end_node)
    graph.add_edge("start", "process")
    graph.add_edge("process", "end_node")
    graph.add_edge("end_node", END)
    graph.set_entry_point("start")
    return graph.compile(checkpointer=checkpointer)


def _build_looping_graph(checkpointer=None) -> Any:
    """Build A → B → A loop graph to test recursion limits."""
    call_count = [0]

    def node_a(state: TestState) -> dict:
        call_count[0] += 1
        output = state.get("output_data", {})
        return {"current_node": "node_a", "output_data": {**output, "a_calls": call_count[0]}, "status": "running"}

    def node_b(state: TestState) -> dict:
        output = state.get("output_data", {})
        return {"current_node": "node_b", "output_data": {**output, "b": "executed"}, "status": "running"}

    graph = StateGraph(TestState)
    graph.add_node("node_a", node_a)
    graph.add_node("node_b", node_b)
    graph.add_edge("node_a", "node_b")
    graph.add_edge("node_b", "node_a")
    graph.set_entry_point("node_a")
    return graph.compile(checkpointer=checkpointer)


class TestRealWorkflowExecution:
    """Test workflow execution with real LangGraph (not mocked)."""

    @pytest.mark.asyncio
    async def test_workflow_executes_and_terminates(self):
        """Workflow runs through all nodes and terminates deterministically."""
        saver = InMemorySaver()
        compiled = _build_simple_graph(checkpointer=saver)

        initial = _make_initial_state("wf-1")
        config = {"configurable": {"thread_id": "t1"}, "recursion_limit": 25}

        result = await compiled.ainvoke(initial, config=config)

        assert result["status"] == "completed"
        assert result["current_node"] == "end"
        assert "process" in result["output_data"]
        assert "end" in result["output_data"]

    @pytest.mark.asyncio
    async def test_recursion_limit_enforced(self):
        """Infinite-loop workflow hits recursion limit and raises error."""
        saver = InMemorySaver()
        compiled = _build_looping_graph(checkpointer=saver)

        initial = _make_initial_state("wf-loop")
        config = {"configurable": {"thread_id": "t-loop"}, "recursion_limit": 10}

        with pytest.raises(Exception) as exc_info:
            await compiled.ainvoke(initial, config=config)

        error_msg = str(exc_info.value).lower()
        assert "recursion" in error_msg or "limit" in error_msg

    def test_default_recursion_limit_is_bounded(self):
        """DEFAULT_RECURSION_LIMIT is a sane positive integer (not unbounded)."""
        assert isinstance(DEFAULT_RECURSION_LIMIT, int)
        assert 1 <= DEFAULT_RECURSION_LIMIT <= 500

    @pytest.mark.asyncio
    async def test_state_accumulates_output(self):
        """Output data merges across nodes (not overwritten)."""
        compiled = _build_simple_graph()

        initial = _make_initial_state("wf-acc", pre_existing_output={"pre": "existing"})
        result = await compiled.ainvoke(initial)

        assert result["output_data"]["pre"] == "existing"
        assert result["output_data"]["process"] == "done"
        assert result["output_data"]["end"] == "done"


class TestCheckpointPersistence:
    """Test checkpoint save/resume with real LangGraph checkpointing."""

    @pytest.mark.asyncio
    async def test_checkpoint_saved_during_execution(self):
        """Checkpoints are persisted; thread state can be inspected."""
        saver = InMemorySaver()
        compiled = _build_simple_graph(checkpointer=saver)

        initial = _make_initial_state("wf-ckpt")
        config = {"configurable": {"thread_id": "ckpt-1"}, "recursion_limit": 25}

        result = await compiled.ainvoke(initial, config=config)
        assert result["status"] == "completed"

        # Verify checkpoint exists for this thread
        state = await compiled.aget_state(config)
        assert state is not None
        assert state.values.get("status") == "completed"

    @pytest.mark.asyncio
    async def test_thread_id_isolation(self):
        """Different thread IDs maintain independent state."""
        saver = InMemorySaver()
        compiled = _build_simple_graph(checkpointer=saver)

        state_a = _make_initial_state("wf-a")
        state_b = _make_initial_state("wf-b")

        config_a = {"configurable": {"thread_id": "thread-a"}, "recursion_limit": 25}
        config_b = {"configurable": {"thread_id": "thread-b"}, "recursion_limit": 25}

        result_a = await compiled.ainvoke(state_a, config=config_a)
        result_b = await compiled.ainvoke(state_b, config=config_b)

        assert result_a["workflow_id"] == "wf-a"
        assert result_b["workflow_id"] == "wf-b"
        assert result_a["status"] == "completed"
        assert result_b["status"] == "completed"

        # Verify checkpoints are isolated
        ckpt_a = await compiled.aget_state(config_a)
        ckpt_b = await compiled.aget_state(config_b)
        assert ckpt_a.values["workflow_id"] == "wf-a"
        assert ckpt_b.values["workflow_id"] == "wf-b"
