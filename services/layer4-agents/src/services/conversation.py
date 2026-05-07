"""ConversationService — ValuePilot backend orchestration.

Bridges the ConversationAgent (GATE-governed intent classification and
context gathering) with the Thesys C1 proxy (LLM response generation)
and the OrchestrationController (spine workflow delegation).

Architecture:
    Frontend (RightRail)
        → POST /agent-stream/chat
            → ConversationService.handle_message()
                1. ConversationAgent.classify_intent()   [GATE-governed]
                2. ConversationAgent.gather_context()     [GATE-governed]
                3. Route by intent:
                   a. Workflow intents → OrchestrationController.schedule_workflow()
                   b. All intents → C1 proxy for LLM generation (with enriched context)
                4. Emit audit event + return response
"""

from __future__ import annotations

import json
import logging
import os
import uuid
from datetime import UTC, datetime
from typing import Any

from value_fabric.shared.audit import AuditAction, AuditOutcome
from value_fabric.shared.audit.emitter import emit_audit_event
from value_fabric.shared.models.typed_dict import TypedDictModel


class ConversationService_handle_messageResult(TypedDictModel):
    content: Any
    metadata: dict[str, Any]

class ConversationService__gather_contextResult(TypedDictModel):
    entities: Any
    entity_context: Any = None
    intent: Any

class ConversationService__heuristic_classifyResult(TypedDictModel):
    confidence: float
    entities: dict[str, Any]
    intent: str

class ConversationService__guardrailResult(TypedDictModel):
    reason: str
    message: str

logger = logging.getLogger(__name__)

# Tab-specific system prompts that provide workspace context to the LLM
TAB_SYSTEM_PROMPTS: dict[str, str] = {
    "signals": (
        "You are ValuePilot, an AI co-pilot in the Intelligence → Signals workspace. "
        "Help sales engineers analyze AI-surfaced pain signals for a prospect account. "
        "Summarize signals, compare them, explain confidence scores, suggest priorities, "
        "and recommend next steps. Keep responses concise (2-3 sentences) and actionable."
    ),
    "drivers": (
        "You are ValuePilot, an AI co-pilot in the Intelligence → Drivers workspace. "
        "Help sales engineers understand root cause analysis connecting pain signals "
        "to underlying business drivers. Explain hierarchies, suggest missing drivers, "
        "and map drivers to product capabilities. Keep responses concise and actionable."
    ),
    "evidence": (
        "You are ValuePilot, an AI co-pilot in the Intelligence → Evidence workspace. "
        "Help sales engineers validate claims with source documents, benchmarks, and "
        "case studies. Explain match scores, suggest sources, flag weak claims. "
        "Keep responses concise and actionable."
    ),
    "stakeholders": (
        "You are ValuePilot, an AI co-pilot in the Intelligence → Stakeholders workspace. "
        "Help sales engineers map buyer personas and stakeholder priorities. "
        "Suggest messaging angles, identify missing stakeholders, recommend engagement "
        "strategies. Keep responses concise and actionable."
    ),
    "action-plan": (
        "You are ValuePilot, an AI co-pilot in the Value Studio → Action Plan workspace. "
        "Help sales engineers build product-anchored recommendations mapping validated "
        "pain to product capabilities. Refine recommendations, adjust priorities, "
        "strengthen the 'why us' argument. Keep responses concise and actionable."
    ),
    "value-model": (
        "You are ValuePilot, an AI co-pilot in the Value Studio → Value Model workspace. "
        "Help sales engineers build and refine quantified business cases. Explain "
        "financial projections, adjust assumptions, compare scenarios, validate "
        "calculations. Keep responses concise and actionable."
    ),
    "narrative": (
        "You are ValuePilot, an AI co-pilot in the Value Studio → Narrative workspace. "
        "Help sales engineers package the value case for stakeholder presentations. "
        "Refine messaging, adjust tone for audiences, suggest narrative structures. "
        "Keep responses concise and actionable."
    ),
    "competitive": (
        "You are ValuePilot, an AI co-pilot in the Intelligence → Competitive workspace. "
        "Help sales engineers analyze competitive positioning, build battlecards, "
        "and identify differentiation opportunities. Keep responses concise and actionable."
    ),
    "enrichment": (
        "You are ValuePilot, an AI co-pilot in the Intelligence → Enrichment workspace. "
        "Help sales engineers review and validate enriched account data, identify gaps, "
        "and trigger re-enrichment. Keep responses concise and actionable."
    ),
    "hypotheses": (
        "You are ValuePilot, an AI co-pilot in the Intelligence → Hypotheses workspace. "
        "Help sales engineers evaluate and refine value hypotheses, test assumptions, "
        "and prioritize the strongest value angles. Keep responses concise and actionable."
    ),
    "roi": (
        "You are ValuePilot, an AI co-pilot in the Intelligence → ROI workspace. "
        "Help sales engineers build ROI models, validate assumptions, run sensitivity "
        "analysis, and compare scenarios. Keep responses concise and actionable."
    ),
}

# Intents that should trigger spine workflow delegation
WORKFLOW_INTENTS: dict[str, str] = {
    "value_analysis": "full_value_spine",
    "document_export": "narrative_export",
    "competitive_intel": "competitive_analysis",
}


class ConversationService:
    """Orchestrates the ValuePilot conversation pipeline.

    This service is stateless per-request — all state lives in the
    frontend message history and the GATE audit trail.
    """

    def __init__(
        self,
        conversation_agent: Any | None = None,
        orchestration_controller: Any | None = None,
        c1_enabled: bool = False,
    ) -> None:
        self.conversation_agent = conversation_agent
        self.orchestration_controller = orchestration_controller
        self.c1_enabled = c1_enabled

    async def handle_message(
        self,
        *,
        user_message: str,
        messages: list[dict[str, str]],
        active_tab: str,
        account_id: str | None = None,
        account_name: str = "this account",
        account_tier: str | None = None,
        entity_context: dict[str, Any] | None = None,
        tenant_id: str = "unknown",
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """Process a user message through the full ValuePilot pipeline.

        Returns:
            Dict with 'content' and 'metadata' matching the AgentStreamResponse contract.
        """
        trace_id = trace_id or str(uuid.uuid4())
        workflow_id = str(uuid.uuid4())
        audit_event_id = f"audit_{uuid.uuid4().hex[:12]}"

        guardrail = self._detect_guardrail_violation(user_message, messages)
        if guardrail:
            await self._emit_security_audit(
                trace_id=trace_id,
                workflow_id=workflow_id,
                audit_event_id=audit_event_id,
                tenant_id=tenant_id,
                active_tab=active_tab,
                account_id=account_id,
                reason=guardrail["reason"],
            )
            return ConversationService_handle_messageResult.model_validate({
                "content": guardrail["message"],
                "metadata": {
                    "trace_id": trace_id,
                    "workflow_id": workflow_id,
                    "tenant_id": tenant_id,
                    "tool_name": "valuepilot_conversation",
                    "audit_event_id": audit_event_id,
                    "emitted_at": datetime.now(UTC).isoformat(),
                    "intent": "refusal",
                    "confidence": 1.0,
                    "workflow_triggered": False,
                    "refusal_reason": guardrail["reason"],
                },
            })

        # Build the GATE execution context
        gate_context = self._build_gate_context()

        # Step 1: Classify intent (GATE-governed)
        intent_result = await self._classify_intent(
            user_message, gate_context
        )
        intent = intent_result.get("intent", "general_question")
        confidence = intent_result.get("confidence", 0.0)
        entities = intent_result.get("entities", {})

        logger.info(
            "Intent classified: %s (confidence=%.2f) for tab=%s",
            intent, confidence, active_tab,
        )

        # Step 2: Gather context (GATE-governed)
        context_data = await self._gather_context(
            intent=intent,
            entities=entities,
            account_id=account_id,
            entity_context=entity_context or {},
            gate_context=gate_context,
        )

        # Step 3: Check if this intent should trigger a workflow
        workflow_result = None
        if intent in WORKFLOW_INTENTS and confidence >= 0.7:
            workflow_result = await self._delegate_to_orchestrator(
                intent=intent,
                entities=entities,
                account_id=account_id,
                gate_context=gate_context,
            )

        # Step 4: Generate response
        response_content = await self._generate_response(
            user_message=user_message,
            messages=messages,
            active_tab=active_tab,
            intent=intent,
            context_data=context_data,
            workflow_result=workflow_result,
            account_name=account_name,
            gate_context=gate_context,
        )

        # Step 5: Emit audit event
        await self._emit_audit(
            trace_id=trace_id,
            workflow_id=workflow_id,
            audit_event_id=audit_event_id,
            tenant_id=tenant_id,
            intent=intent,
            confidence=confidence,
            active_tab=active_tab,
            account_id=account_id,
            has_workflow=workflow_result is not None,
        )

        return ConversationService_handle_messageResult.model_validate({
            "content": response_content,
            "metadata": {
                "trace_id": trace_id,
                "workflow_id": workflow_id,
                "tenant_id": tenant_id,
                "tool_name": "valuepilot_conversation",
                "audit_event_id": audit_event_id,
                "emitted_at": datetime.now(UTC).isoformat(),
                "intent": intent,
                "confidence": confidence,
                "workflow_triggered": workflow_result is not None,
                "entity_context": entity_context or {},
            },
        })


    def _build_gate_context(self) -> dict[str, Any]:
        """Build the GATE execution context for ConversationAgent."""
        ctx: dict[str, Any] = {}

        # If ConversationAgent is available, its run() method will have
        # injected tool_gateway and replay_recorder. For direct service
        # usage, we provide a minimal context.
        if self.conversation_agent:
            # The agent's run() method populates ctx with tool_gateway
            # For service-level calls, we pass through to the agent's execute()
            pass

        return ctx

    async def _classify_intent(
        self,
        message: str,
        gate_context: dict[str, Any],
    ) -> dict[str, Any]:
        """Classify user intent using ConversationAgent or fallback heuristics."""
        if self.conversation_agent:
            try:
                return await self.conversation_agent.execute(
                    {"capability": "classify_intent", "parameters": {"message": message}},
                    gate_context,
                )
            except Exception:
                logger.warning("ConversationAgent intent classification failed, using heuristic")

        # Heuristic fallback when agent is not available
        return self._heuristic_classify(message)

    async def _gather_context(
        self,
        *,
        intent: str,
        entities: dict[str, Any],
        account_id: str | None,
        entity_context: dict[str, Any],
        gate_context: dict[str, Any],
    ) -> dict[str, Any]:
        """Gather relevant context using ConversationAgent or return minimal context."""
        if self.conversation_agent and account_id:
            try:
                result = await self.conversation_agent.execute(
                    {
                        "capability": "gather_context",
                        "parameters": {
                            "intent": intent,
                            "entities": entities,
                            "account_id": account_id,
                            "entity_context": entity_context,
                        },
                    },
                    gate_context,
                )
                context_data = result.get("context_data", {})
                if isinstance(context_data, dict):
                    context_data.setdefault("entity_context", entity_context)
                return context_data
            except Exception:
                logger.warning("ConversationAgent context gathering failed")

        return ConversationService__gather_contextResult.model_validate({
            "intent": intent,
            "entities": entities,
            "entity_context": entity_context,
        })

    async def _delegate_to_orchestrator(
        self,
        *,
        intent: str,
        entities: dict[str, Any],
        account_id: str | None,
        gate_context: dict[str, Any],
    ) -> dict[str, Any] | None:
        """Delegate workflow-triggering intents to OrchestrationController."""
        if not self.orchestration_controller:
            logger.info("No OrchestrationController available — skipping workflow delegation")
            return None

        workflow_type = WORKFLOW_INTENTS.get(intent)
        if not workflow_type:
            return None

        try:
            result = await self.orchestration_controller.execute(
                {
                    "capability": "schedule_workflow",
                    "parameters": {
                        "workflow_type": workflow_type,
                        "inputs": {
                            "account_id": account_id,
                            "entities": entities,
                            "triggered_by": "valuepilot_conversation",
                        },
                        "priority": "high",
                    },
                },
                gate_context,
            )
            logger.info(
                "Workflow %s scheduled: %s",
                workflow_type, result.get("schedule_id"),
            )
            return result
        except Exception:
            logger.warning("Workflow delegation failed for intent=%s", intent)
            return None

    async def _generate_response(
        self,
        *,
        user_message: str,
        messages: list[dict[str, str]],
        active_tab: str,
        intent: str,
        context_data: dict[str, Any],
        workflow_result: dict[str, Any] | None,
        account_name: str,
        gate_context: dict[str, Any],
    ) -> str:
        """Generate the response content.

        Priority:
        1. ConversationAgent.execute(chat) if agent + tool_gateway available
        2. C1 proxy with enriched system prompt if C1 enabled
        3. Context-aware heuristic response (no LLM)
        """
        # Strategy 1: Full agent pipeline (uses generate_section tool via GATE)
        if self.conversation_agent and gate_context.get("tool_gateway"):
            try:
                result = await self.conversation_agent.execute(
                    {
                        "capability": "chat",
                        "parameters": {
                            "message": user_message,
                            "session_id": str(uuid.uuid4()),
                            "account_id": context_data.get("account", {}).get("entity_id"),
                        },
                    },
                    gate_context,
                )
                content = result.get("response", "")
                if content:
                    return self._append_workflow_notice(content, workflow_result)
            except Exception:
                logger.warning("Full agent pipeline failed, falling back")

        # Strategy 2: C1 proxy with enriched context
        if self.c1_enabled:
            try:
                content = await self._generate_via_c1(
                    user_message=user_message,
                    messages=messages,
                    active_tab=active_tab,
                    context_data=context_data,
                    account_name=account_name,
                )
                if content:
                    return self._append_workflow_notice(content, workflow_result)
            except Exception:
                logger.warning("C1 generation failed, falling back to heuristic")

        # Strategy 3: Context-aware heuristic (always works)
        content = self._heuristic_response(
            user_message=user_message,
            active_tab=active_tab,
            intent=intent,
            context_data=context_data,
            account_name=account_name,
        )
        return self._append_workflow_notice(content, workflow_result)

    async def _generate_via_c1(
        self,
        *,
        user_message: str,
        messages: list[dict[str, str]],
        active_tab: str,
        context_data: dict[str, Any],
        account_name: str,
    ) -> str:
        """Generate response via the Thesys C1 API.

        Enriches the system prompt with gathered context data so the LLM
        has account-specific information to work with.
        """
        import httpx

        thesys_api_key = os.getenv("THESYS_API_KEY", "")
        thesys_base_url = os.getenv(
            "THESYS_BASE_URL", "https://api.thesys.dev/v1/embed"
        )

        if not thesys_api_key:
            logger.info("THESYS_API_KEY not set — C1 generation unavailable")
            return ""

        # Build enriched system prompt
        base_prompt = TAB_SYSTEM_PROMPTS.get(
            active_tab,
            "You are ValuePilot, an AI co-pilot for value selling. "
            "Keep responses concise and actionable.",
        )

        context_section = ""
        if context_data:
            context_section = (
                f"\n\nCurrent account context for {account_name}:\n"
                f"{json.dumps(context_data, indent=2, default=str)[:2000]}"
            )

        enriched_prompt = base_prompt + context_section

        # Build message list with enriched system prompt
        c1_messages = [{"role": "system", "content": enriched_prompt}]
        # Include recent conversation history (last 10 messages)
        for msg in messages[-10:]:
            role = msg.get("role", "user")
            if role == "system":
                continue  # Skip — we already have our enriched system prompt
            c1_messages.append({"role": role, "content": msg.get("content", "")})

        payload = {
            "messages": c1_messages,
            "stream": False,
            "metadata": {
                "business_case_id": f"valuepilot_{active_tab}",
                "account_name": account_name,
            },
        }

        async with httpx.AsyncClient(
            timeout=httpx.Timeout(30.0, connect=10.0)
        ) as client:
            response = await client.post(
                thesys_base_url,
                json=payload,
                headers={
                    "Authorization": f"Bearer {thesys_api_key}",
                    "Content-Type": "application/json",
                },
            )
            response.raise_for_status()
            data = response.json()

            # C1 API returns content in various formats
            if isinstance(data, dict):
                return (
                    data.get("content", "")
                    or data.get("choices", [{}])[0].get("message", {}).get("content", "")
                    or data.get("text", "")
                )
            return str(data)

    def _heuristic_classify(self, message: str) -> dict[str, Any]:
        """Rule-based intent classification fallback."""
        lower = message.lower()

        if any(w in lower for w in ("roi", "return", "payback", "cost", "savings", "value model")):
            return ConversationService__heuristic_classifyResult.model_validate({"intent": "value_analysis", "confidence": 0.75, "entities": {}})
        if any(w in lower for w in ("competitor", "competitive", "versus", "vs", "battlecard")):
            return ConversationService__heuristic_classifyResult.model_validate({"intent": "competitive_intel", "confidence": 0.75, "entities": {}})
        if any(w in lower for w in ("export", "document", "pdf", "slide", "deck", "proposal")):
            return ConversationService__heuristic_classifyResult.model_validate({"intent": "document_export", "confidence": 0.75, "entities": {}})
        if any(w in lower for w in ("status", "workflow", "progress", "running")):
            return ConversationService__heuristic_classifyResult.model_validate({"intent": "workflow_status", "confidence": 0.70, "entities": {}})
        if any(w in lower for w in ("account", "company", "prospect", "customer", "who")):
            return ConversationService__heuristic_classifyResult.model_validate({"intent": "account_inquiry", "confidence": 0.65, "entities": {}})

        return ConversationService__heuristic_classifyResult.model_validate({"intent": "general_question", "confidence": 0.50, "entities": {}})

    def _detect_guardrail_violation(
        self,
        user_message: str,
        messages: list[dict[str, str]],
    ) -> dict[str, str] | None:
        """Deterministically refuse unsafe agent requests before tools/LLMs run."""
        combined = "\n".join(
            [user_message]
            + [
                str(msg.get("content", ""))
                for msg in messages[-5:]
                if msg.get("role", "user").lower() in {"user", "document", "system"}
            ]
        ).lower()

        refusal = (
            "I can't help with that request because it would bypass Fabric's "
            "tenant, evidence, approval, or secret-handling controls. I can help "
            "with a grounded, tenant-scoped draft using approved evidence."
        )
        rules: list[tuple[str, tuple[str, ...]]] = [
            ("prompt_injection", ("ignore previous instructions", "system override", "delete approval gates")),
            ("cross_tenant_access", ("every tenant", "all tenants", "cross-tenant", "other tenant")),
            ("secret_exfiltration", ("reveal internal secret", "reveal secrets", "api key", "token", "password")),
            ("approval_bypass", ("bypass approval", "mark them approved", "export immediately", "approval gates")),
            ("unsupported_roi", ("guarantee", "without evidence", "unsupported roi", "900% roi")),
            ("fabricated_benchmark", ("fabricate benchmark", "invent benchmark", "fake benchmark")),
            ("fabricated_citation", ("source that does not exist", "citation that does not exist", "fake citation")),
        ]
        for reason, tokens in rules:
            if any(token in combined for token in tokens):
                return ConversationService__guardrailResult.model_validate({
                    "reason": reason,
                    "message": refusal,
                })
        return None

    def _heuristic_response(
        self,
        *,
        user_message: str,
        active_tab: str,
        intent: str,
        context_data: dict[str, Any],
        account_name: str,
    ) -> str:
        """Generate a context-aware response without LLM."""
        lower = user_message.lower()
        evidence_records = (
            context_data.get("evidence_records")
            or context_data.get("evidence")
            or context_data.get("truth_references")
            or []
        )

        if any(token in lower for token in ("cite", "evidence", "claim", "roi", "business case")):
            if evidence_records:
                citations = []
                for item in evidence_records:
                    if isinstance(item, dict):
                        citation_id = item.get("id") or item.get("evidence_id") or item.get("truth_object_id")
                        tenant = item.get("tenant_id")
                        if citation_id and (tenant in {None, context_data.get("tenant_id")}):
                            citations.append(str(citation_id))
                if citations:
                    return (
                        f"For {account_name} in {active_tab}: Fact: the value claim is supported "
                        f"by persisted evidence {', '.join(citations[:3])}. Inference: prioritize "
                        "the recommendation only after reviewer validation. Assumption: missing "
                        "inputs remain unverified. Benchmark: use benchmark figures only when a "
                        "persisted benchmark source is attached."
                    )
            return (
                f"For {account_name} in {active_tab}: I do not have persisted evidence for that "
                "factual value claim, so I cannot present it as verified. Assumption: it can be "
                "kept as a draft hypothesis until supporting evidence is attached."
            )

        # Account context enrichment
        account_info = context_data.get("account", {})
        account_detail = ""
        if account_info:
            name = account_info.get("name", account_name)
            industry = account_info.get("industry", "")
            if industry:
                account_detail = f" ({industry})"
            account_name = name

        if intent == "value_analysis":
            return (
                f"For {account_name}{account_detail} in the {active_tab} view: "
                "I recommend starting with the highest-confidence value drivers, "
                "validating the ROI assumptions with the prospect, and building "
                "the business case around measurable outcomes. "
                "I can help you run sensitivity analysis or compare scenarios."
            )

        if intent == "competitive_intel":
            return (
                f"For {account_name}{account_detail}: I can pull competitive "
                "positioning data, generate battlecard talking points, and "
                "identify differentiation opportunities. Which competitor "
                "would you like to focus on?"
            )

        if intent == "document_export":
            return (
                f"I can help export the {active_tab} analysis for {account_name} "
                "as a stakeholder-ready document. Options include executive summary, "
                "detailed business case, or slide deck format. Which would you prefer?"
            )

        if intent == "workflow_status":
            return (
                "I can check the status of running workflows. Currently monitoring "
                "active analysis pipelines. What specific workflow are you asking about?"
            )

        if intent == "account_inquiry":
            if account_info:
                return (
                    f"Here's what I know about {account_name}{account_detail}: "
                    f"I have context data available including relationships and "
                    f"intelligence signals. What specific aspect would you like to explore?"
                )
            return (
                f"I can help you explore {account_name}. Select an account in the "
                "workspace to see enriched intelligence data, or ask me about "
                "specific signals, drivers, or value opportunities."
            )

        # General / summarize / compare / recommend
        if "summar" in lower:
            return (
                f"Here's a summary for {account_name} in {active_tab}: "
                "focus on the top signals by confidence, tie each to measurable "
                "impact, and capture validation questions for the next touchpoint."
            )

        if "compare" in lower:
            return (
                f"Comparing items in the {active_tab} view for {account_name}: "
                "the top-ranked items show significantly higher confidence and "
                "impact scores. I can break down the comparison in more detail."
            )

        if any(w in lower for w in ("recommend", "suggest", "next")):
            return (
                f"For {account_name} in {active_tab}: (1) Validate the top signals "
                "with the prospect, (2) Map strongest drivers to product capabilities, "
                "(3) Build the action plan around highest-confidence items."
            )

        return (
            f"Got it — for {account_name} in {active_tab}, I can help analyze "
            "findings, prioritize actions, run calculations, or draft "
            "stakeholder-ready messaging. What direction would you like to go?"
        )

    def _append_workflow_notice(
        self,
        content: str,
        workflow_result: dict[str, Any] | None,
    ) -> str:
        """Append workflow scheduling notice if a workflow was triggered."""
        if not workflow_result:
            return content

        schedule_id = workflow_result.get("schedule_id", "unknown")
        return (
            f"{content}\n\n"
            f"📋 I've also kicked off a background analysis workflow "
            f"(ID: {schedule_id}). I'll surface the results when it completes."
        )

    async def _emit_audit(
        self,
        *,
        trace_id: str,
        workflow_id: str,
        audit_event_id: str,
        tenant_id: str,
        intent: str,
        confidence: float,
        active_tab: str,
        account_id: str | None,
        has_workflow: bool,
    ) -> None:
        """Emit a GATE audit event for the conversation interaction."""
        try:
            await emit_audit_event(
                AuditAction.AGENT_EXECUTION,
                outcome=AuditOutcome.SUCCESS,
                resource_type="agent",
                resource_id="conversation-agent",
                details={
                    "trace_id": trace_id,
                    "workflow_id": workflow_id,
                    "audit_event_id": audit_event_id,
                    "tenant_id": tenant_id,
                    "intent": intent,
                    "confidence": confidence,
                    "active_tab": active_tab,
                    "account_id": account_id,
                    "workflow_triggered": has_workflow,
                },
                chain_id=f"conversation:{tenant_id}",
            )
        except Exception:
            logger.warning("Failed to emit conversation audit event", exc_info=True)

    async def _emit_security_audit(
        self,
        *,
        trace_id: str,
        workflow_id: str,
        audit_event_id: str,
        tenant_id: str,
        active_tab: str,
        account_id: str | None,
        reason: str,
    ) -> None:
        """Emit an audit event for refused unsafe agent requests."""
        try:
            await emit_audit_event(
                AuditAction.POLICY_DECISION,
                outcome=AuditOutcome.FAILURE,
                resource_type="agent",
                resource_id="conversation-agent",
                details={
                    "trace_id": trace_id,
                    "workflow_id": workflow_id,
                    "audit_event_id": audit_event_id,
                    "tenant_id": tenant_id,
                    "active_tab": active_tab,
                    "account_id": account_id,
                    "reason": reason,
                },
                chain_id=f"conversation-security:{tenant_id}",
            )
        except Exception:
            logger.warning("Failed to emit conversation security audit event", exc_info=True)
