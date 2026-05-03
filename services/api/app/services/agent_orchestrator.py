from typing import Dict, Any, Optional
from datetime import datetime, timezone
from app.models.schemas import AgentRun, ToolResult
from app.core.database import db


class MockLLMProvider:
    """Mockable LLM provider for MVP. Replace with Together.ai or OpenAI later."""

    def generate_structured(self, prompt: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        return {"result": "mock structured output", "prompt_length": len(prompt)}

    def summarize(self, text: str) -> str:
        return f"Summary: {text[:100]}..."

    def extract(self, text: str, fields: list) -> Dict[str, Any]:
        return {f: f"extracted_{f}" for f in fields}

    def classify(self, text: str, labels: list) -> str:
        return labels[0] if labels else "unknown"

    def reason(self, premise: str, question: str) -> str:
        return f"Reasoned answer to '{question}' based on premise."


class AgentOrchestrator:
    def __init__(self, llm: Optional[MockLLMProvider] = None):
        self.llm = llm or MockLLMProvider()

    def create_run(self, tenant_id: str, workflow_type: str, account_id: Optional[str] = None, input_data: Optional[Dict[str, Any]] = None) -> AgentRun:
        run_id = f"run-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{tenant_id[:4]}"
        run = AgentRun(
            id=run_id,
            tenant_id=tenant_id,
            account_id=account_id,
            workflow_type=workflow_type,
            status="pending",
            input=input_data or {},
        )
        db.agent_runs.insert(run_id, run)
        return run

    def execute_step(self, run_id: str, step_name: str, tool_name: Optional[str] = None) -> AgentRun:
        run = db.agent_runs.get(run_id)
        if not run:
            raise ValueError(f"Run {run_id} not found")

        run.status = "running"
        run.current_step = step_name
        run.updated_at = datetime.now(timezone.utc).isoformat()

        if tool_name:
            tool_result = ToolResult(
                id=f"tr-{run_id}-{step_name}",
                agent_run_id=run_id,
                tool_name=tool_name,
                status="success",
                output={"mock": True, "step": step_name},
                completed_at=datetime.now(timezone.utc).isoformat(),
            )
            db.tool_results.insert(tool_result.id, tool_result)
            run.tool_results.append(tool_result)

        # Auto-complete for mock
        run.status = "completed"
        run.output = {"completed_step": step_name, "mock": True}
        db.agent_runs.update(run_id, status=run.status, current_step=run.current_step, output=run.output, tool_results=run.tool_results)
        return run

    def resume_run(self, run_id: str) -> AgentRun:
        run = db.agent_runs.get(run_id)
        if not run:
            raise ValueError(f"Run {run_id} not found")
        if run.status == "paused":
            run.status = "running"
            run.updated_at = datetime.now(timezone.utc).isoformat()
            db.agent_runs.update(run_id, status=run.status)
        return run

    def cancel_run(self, run_id: str) -> AgentRun:
        run = db.agent_runs.get(run_id)
        if not run:
            raise ValueError(f"Run {run_id} not found")
        run.status = "cancelled"
        run.updated_at = datetime.now(timezone.utc).isoformat()
        db.agent_runs.update(run_id, status=run.status)
        return run


orchestrator = AgentOrchestrator()
