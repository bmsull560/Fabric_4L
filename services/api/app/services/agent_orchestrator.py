from datetime import datetime, timezone
from typing import Any, Dict, Optional, Protocol

from app.core.config import get_settings
from app.core.database import db
from app.models.schemas import AgentRun, ToolResult


class LLMProvider(Protocol):
    def generate_structured(self, prompt: str, schema: Dict[str, Any]) -> Dict[str, Any]: ...
    def summarize(self, text: str) -> str: ...
    def extract(self, text: str, fields: list[str]) -> Dict[str, Any]: ...
    def classify(self, text: str, labels: list[str]) -> str: ...
    def reason(self, premise: str, question: str) -> str: ...


class ProductionLLMNotConfigured(RuntimeError):
    """Raised when production requests would otherwise use a mock LLM provider."""


class MockLLMProvider:
    """Development/test-only LLM provider used by local demos and fixtures."""

    provider_name = "mock"

    def generate_structured(self, prompt: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        return {"result": "mock structured output", "prompt_length": len(prompt)}

    def summarize(self, text: str) -> str:
        return f"Summary: {text[:100]}..."

    def extract(self, text: str, fields: list[str]) -> Dict[str, Any]:
        return {field: f"extracted_{field}" for field in fields}

    def classify(self, text: str, labels: list[str]) -> str:
        return labels[0] if labels else "unknown"

    def reason(self, premise: str, question: str) -> str:
        return f"Reasoned answer to '{question}' based on premise."


def create_llm_provider() -> LLMProvider:
    settings = get_settings()
    provider = settings.llm_provider.lower()

    if provider == "mock":
        if settings.is_production_like and not settings.allow_mock_llm:
            raise ProductionLLMNotConfigured(
                "Mock LLM provider is disabled in production-like environments."
            )
        return MockLLMProvider()

    raise ProductionLLMNotConfigured(
        f"LLM provider '{settings.llm_provider}' is selected, but no production "
        "provider adapter is wired for services/api yet."
    )


class AgentOrchestrator:
    def __init__(self, llm: Optional[LLMProvider] = None):
        self.llm = llm or create_llm_provider()

    def create_run(
        self,
        tenant_id: str,
        workflow_type: str,
        account_id: Optional[str] = None,
        input_data: Optional[Dict[str, Any]] = None,
    ) -> AgentRun:
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
                output={"provider": getattr(self.llm, "provider_name", "configured"), "step": step_name},
                completed_at=datetime.now(timezone.utc).isoformat(),
            )
            db.tool_results.insert(tool_result.id, tool_result)
            run.tool_results.append(tool_result)

        # This MVP orchestrator only marks a single local/demo step complete. It is guarded
        # by create_llm_provider() and app.core.config so production-like environments cannot
        # accidentally run mock AI workflows.
        run.status = "completed"
        run.output = {
            "completed_step": step_name,
            "provider": getattr(self.llm, "provider_name", "configured"),
        }
        db.agent_runs.update(
            run_id,
            status=run.status,
            current_step=run.current_step,
            output=run.output,
            tool_results=run.tool_results,
        )
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
