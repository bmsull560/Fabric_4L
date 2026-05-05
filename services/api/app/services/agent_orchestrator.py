import json
import os
from datetime import UTC, datetime
from typing import Any, Protocol

from app.core.config import get_settings
from app.core.database import db
from app.models.schemas import AgentRun, ToolResult


class LLMProvider(Protocol):
    def generate_structured(self, prompt: str, schema: dict[str, Any]) -> dict[str, Any]: ...
    def summarize(self, text: str) -> str: ...
    def extract(self, text: str, fields: list[str]) -> dict[str, Any]: ...
    def classify(self, text: str, labels: list[str]) -> str: ...
    def reason(self, premise: str, question: str) -> str: ...


class ProductionLLMNotConfigured(RuntimeError):
    """Raised when production requests would otherwise use a mock LLM provider."""


class MockLLMProvider:
    """Development/test-only LLM provider used by local demos and fixtures."""

    provider_name = "mock"

    def generate_structured(self, prompt: str, schema: dict[str, Any]) -> dict[str, Any]:
        return {"result": "mock structured output", "prompt_length": len(prompt)}

    def summarize(self, text: str) -> str:
        return f"Summary: {text[:100]}..."

    def extract(self, text: str, fields: list[str]) -> dict[str, Any]:
        return {field: f"extracted_{field}" for field in fields}

    def classify(self, text: str, labels: list[str]) -> str:
        return labels[0] if labels else "unknown"

    def reason(self, premise: str, question: str) -> str:
        return f"Reasoned answer to '{question}' based on premise."


class OpenAILLMProvider:
    """OpenAI-compatible production provider for standalone API orchestration.

    The adapter is intentionally contained inside ``services/api`` so the unified
    API does not bypass Layer 2 extraction or Layer 4 orchestration contracts.
    Network calls are made only when a workflow method is invoked; construction
    fails closed if the package or API key is unavailable.
    """

    provider_name = "openai"

    def __init__(self, model: str | None = None, api_key: str | None = None, timeout: float = 60.0):
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise ProductionLLMNotConfigured(
                "openai package is required when llm_provider=openai."
            ) from exc

        resolved_api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not resolved_api_key:
            raise ProductionLLMNotConfigured(
                "OPENAI_API_KEY must be configured when llm_provider=openai."
            )

        self.model = model or os.getenv("OPENAI_MODEL") or "gpt-4.1-mini"
        self._client = OpenAI(api_key=resolved_api_key, timeout=timeout)

    def _complete(self, system_prompt: str, user_prompt: str) -> str:
        response = self._client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0,
        )
        content = response.choices[0].message.content
        return content or ""

    def generate_structured(self, prompt: str, schema: dict[str, Any]) -> dict[str, Any]:
        content = self._complete(
            "Return only a valid JSON object that conforms to the requested schema.",
            f"Prompt:\n{prompt}\n\nJSON schema or field description:\n{json.dumps(schema, sort_keys=True)}",
        )
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError:
            return {"result": content}
        if not isinstance(parsed, dict):
            return {"result": parsed}
        return parsed

    def summarize(self, text: str) -> str:
        return self._complete("Summarize the supplied business context concisely.", text)

    def extract(self, text: str, fields: list[str]) -> dict[str, Any]:
        return self.generate_structured(
            f"Extract these fields from the text: {', '.join(fields)}\n\n{text}",
            {"type": "object", "properties": {field: {"type": "string"} for field in fields}},
        )

    def classify(self, text: str, labels: list[str]) -> str:
        if not labels:
            return "unknown"
        content = self._complete(
            "Classify the text using exactly one of the supplied labels. Return only the label.",
            f"Labels: {', '.join(labels)}\n\nText:\n{text}",
        ).strip()
        return content if content in labels else labels[0]

    def reason(self, premise: str, question: str) -> str:
        return self._complete(
            "Answer the question using only the supplied premise. Be concise and explicit about uncertainty.",
            f"Premise:\n{premise}\n\nQuestion:\n{question}",
        )


def create_llm_provider() -> LLMProvider:
    settings = get_settings()
    provider = settings.llm_provider.lower()

    if provider == "mock":
        if settings.is_production_like:
            raise ProductionLLMNotConfigured(
                "Mock LLM provider is disabled in production-like environments."
            )
        return MockLLMProvider()

    if provider == "openai":
        return OpenAILLMProvider(model=settings.llm_model)

    raise ProductionLLMNotConfigured(
        f"LLM provider '{settings.llm_provider}' is not supported by services/api. "
        "Supported production providers: openai."
    )


class AgentOrchestrator:
    def __init__(self, llm: LLMProvider | None = None):
        self.llm = llm or create_llm_provider()

    def create_run(
        self,
        tenant_id: str,
        workflow_type: str,
        account_id: str | None = None,
        input_data: dict[str, Any] | None = None,
    ) -> AgentRun:
        run_id = f"run-{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}-{tenant_id[:4]}"
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

    def execute_step(self, run_id: str, step_name: str, tool_name: str | None = None) -> AgentRun:
        run = db.agent_runs.get(run_id)
        if not run:
            raise ValueError(f"Run {run_id} not found")

        run.status = "running"
        run.current_step = step_name
        run.updated_at = datetime.now(UTC).isoformat()

        if tool_name:
            tool_result = ToolResult(
                id=f"tr-{run_id}-{step_name}",
                agent_run_id=run_id,
                tool_name=tool_name,
                status="success",
                output={
                    "provider": getattr(self.llm, "provider_name", "configured"),
                    "step": step_name,
                },
                completed_at=datetime.now(UTC).isoformat(),
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
            run.updated_at = datetime.now(UTC).isoformat()
            db.agent_runs.update(run_id, status=run.status)
        return run

    def cancel_run(self, run_id: str) -> AgentRun:
        run = db.agent_runs.get(run_id)
        if not run:
            raise ValueError(f"Run {run_id} not found")
        run.status = "cancelled"
        run.updated_at = datetime.now(UTC).isoformat()
        db.agent_runs.update(run_id, status=run.status)
        return run


_orchestrator: AgentOrchestrator | None = None


def get_orchestrator() -> AgentOrchestrator:
    """Return the global orchestrator, creating it lazily on first use."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = AgentOrchestrator()
    return _orchestrator


# Lazy proxy for backward-compatible direct imports.
class _LazyOrchestrator:
    """Lazy proxy that instantiates AgentOrchestrator on first use."""

    _instance: AgentOrchestrator | None = None

    @classmethod
    def _get(cls) -> AgentOrchestrator:
        if cls._instance is None:
            cls._instance = AgentOrchestrator()
        return cls._instance

    def __getattr__(self, name: str):
        return getattr(self._get(), name)

    def __setattr__(self, name: str, value):
        if name == "_instance":
            super().__setattr__(name, value)
        else:
            setattr(self._get(), name, value)

    def __call__(self, *args, **kwargs):
        return self._get()(*args, **kwargs)


orchestrator: AgentOrchestrator = _LazyOrchestrator()  # type: ignore[assignment]
