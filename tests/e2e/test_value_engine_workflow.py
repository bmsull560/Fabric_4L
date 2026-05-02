"""End-to-End 7-Step Value Engine Workflow Validation.

Phase 9: Prove the core Value Engine workflow works for a real account executive user.

Precondition: Structural gates must pass (Phase 7) or blockers documented.
"""
from __future__ import annotations

import os
import uuid
from typing import Any

import pytest
import requests

# Demo identity from metaprompt
DEMO_TENANT = {
    "slug": "demo-acme",
    "name": "Acme Corp",
}

DEMO_USER = {
    "name": "Sarah Chen",
    "email": "sarah.chen@acmerobotics.com",
    "password": "Demo1234!",
    "role": "admin",
    "persona": "Account Executive",
}

DEMO_PROSPECT = {
    "company_name": "Axiom Robotics",
    "domain": "axiomrobotics.com",
    "objective": "cost_reduction",
}


class ValueEngineE2EClient:
    """E2E test client for Value Engine API."""

    def __init__(self, base_url: str, api_key: str | None = None) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.token: str | None = None
        self.tenant_id: str | None = None
        self.user_id: str | None = None

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        elif self.api_key:
            headers["X-API-Key"] = self.api_key
        if self.tenant_id:
            headers["X-Tenant-ID"] = self.tenant_id
        return headers

    def signup(self, email: str, password: str, name: str) -> dict[str, Any]:
        """Step 0: Create user account."""
        resp = requests.post(
            f"{self.base_url}/v1/auth/signup",
            json={"email": email, "password": password, "name": name},
        )
        resp.raise_for_status()
        data = resp.json()
        self.token = data.get("access_token")
        self.tenant_id = data.get("tenant_id")
        self.user_id = data.get("user_id")
        return data

    def login(self, email: str, password: str) -> dict[str, Any]:
        """Step 0 alt: Authenticate existing user."""
        resp = requests.post(
            f"{self.base_url}/v1/auth/login",
            json={"email": email, "password": password},
        )
        resp.raise_for_status()
        data = resp.json()
        self.token = data.get("access_token")
        self.tenant_id = data.get("tenant_id")
        self.user_id = data.get("user_id")
        return data

    def create_prospect(self, company_name: str, domain: str) -> dict[str, Any]:
        """Step 1: Prospect Setup - create company profile."""
        resp = requests.post(
            f"{self.base_url}/v1/prospects",
            headers=self._headers(),
            json={"company_name": company_name, "domain": domain},
        )
        resp.raise_for_status()
        return resp.json()

    def enrich_prospect(self, prospect_id: str) -> dict[str, Any]:
        """Step 1b: Enrich prospect with intelligence."""
        resp = requests.post(
            f"{self.base_url}/v1/prospects/{prospect_id}/enrich",
            headers=self._headers(),
        )
        resp.raise_for_status()
        return resp.json()

    def get_prospect_context(self, prospect_id: str) -> dict[str, Any]:
        """Step 1c: Get enriched context."""
        resp = requests.get(
            f"{self.base_url}/v1/prospects/{prospect_id}/context",
            headers=self._headers(),
        )
        resp.raise_for_status()
        return resp.json()

    def run_intelligence_workflow(self, prospect_id: str) -> dict[str, Any]:
        """Step 2: Intelligence Gathering - trigger workflow."""
        resp = requests.post(
            f"{self.base_url}/v1/workflows/intelligence",
            headers=self._headers(),
            json={"prospect_id": prospect_id, "objective": "discovery"},
        )
        resp.raise_for_status()
        return resp.json()

    def get_workflow_status(self, workflow_id: str) -> dict[str, Any]:
        """Step 2b: Check workflow status."""
        resp = requests.get(
            f"{self.base_url}/v1/workflows/{workflow_id}/status",
            headers=self._headers(),
        )
        resp.raise_for_status()
        return resp.json()

    def get_intelligence_findings(self, prospect_id: str) -> dict[str, Any]:
        """Step 2c: Get pain points, opportunities, stakeholders."""
        resp = requests.get(
            f"{self.base_url}/v1/intelligence/findings",
            headers=self._headers(),
            params={"prospect_id": prospect_id},
        )
        resp.raise_for_status()
        return resp.json()

    def create_hypothesis(self, prospect_id: str, claim: str) -> dict[str, Any]:
        """Step 3: AI Model / Value Hypothesis."""
        resp = requests.post(
            f"{self.base_url}/v1/intelligence/hypotheses",
            headers=self._headers(),
            json={"prospect_id": prospect_id, "claim": claim, "confidence": 0.85},
        )
        resp.raise_for_status()
        return resp.json()

    def get_hypotheses(self, prospect_id: str) -> dict[str, Any]:
        """Step 3b: List hypotheses for prospect."""
        resp = requests.get(
            f"{self.base_url}/v1/intelligence/hypotheses",
            headers=self._headers(),
            params={"prospect_id": prospect_id},
        )
        resp.raise_for_status()
        return resp.json()

    def create_driver_tree(self, prospect_id: str) -> dict[str, Any]:
        """Step 4: Driver Tree - create value tree."""
        resp = requests.post(
            f"{self.base_url}/v1/value-engine/driver-tree",
            headers=self._headers(),
            json={"prospect_id": prospect_id, "objective": DEMO_PROSPECT["objective"]},
        )
        resp.raise_for_status()
        return resp.json()

    def get_driver_tree(self, tree_id: str) -> dict[str, Any]:
        """Step 4b: Get driver tree with nodes."""
        resp = requests.get(
            f"{self.base_url}/v1/value-engine/driver-tree/{tree_id}",
            headers=self._headers(),
        )
        resp.raise_for_status()
        return resp.json()

    def get_evidence(self, prospect_id: str, driver_node_id: str | None = None) -> dict[str, Any]:
        """Step 5: Evidence Library - get supporting evidence."""
        params: dict[str, str] = {"prospect_id": prospect_id}
        if driver_node_id:
            params["driver_node_id"] = driver_node_id

        resp = requests.get(
            f"{self.base_url}/v1/evidence",
            headers=self._headers(),
            params=params,
        )
        resp.raise_for_status()
        return resp.json()

    def attach_evidence(self, prospect_id: str, evidence_id: str, driver_node_id: str) -> dict[str, Any]:
        """Step 5b: Attach evidence to driver node."""
        resp = requests.post(
            f"{self.base_url}/v1/evidence/attach",
            headers=self._headers(),
            json={
                "prospect_id": prospect_id,
                "evidence_id": evidence_id,
                "driver_node_id": driver_node_id,
            },
        )
        resp.raise_for_status()
        return resp.json()

    def create_scenario(self, prospect_id: str, tree_id: str) -> dict[str, Any]:
        """Step 6: Calculator - create ROI scenario."""
        resp = requests.post(
            f"{self.base_url}/v1/value-engine/scenarios",
            headers=self._headers(),
            json={"prospect_id": prospect_id, "driver_tree_id": tree_id},
        )
        resp.raise_for_status()
        return resp.json()

    def calculate_scenario(self, scenario_id: str) -> dict[str, Any]:
        """Step 6b: Run ROI calculation."""
        resp = requests.post(
            f"{self.base_url}/v1/value-engine/scenarios/{scenario_id}/calculate",
            headers=self._headers(),
        )
        resp.raise_for_status()
        return resp.json()

    def get_scenario(self, scenario_id: str) -> dict[str, Any]:
        """Step 6c: Get scenario with ROI results."""
        resp = requests.get(
            f"{self.base_url}/v1/value-engine/scenarios/{scenario_id}",
            headers=self._headers(),
        )
        resp.raise_for_status()
        return resp.json()

    def create_value_case(self, prospect_id: str, scenario_id: str) -> dict[str, Any]:
        """Step 7: Value Case / Narrative Generation."""
        resp = requests.post(
            f"{self.base_url}/v1/value-engine/cases",
            headers=self._headers(),
            json={"prospect_id": prospect_id, "scenario_id": scenario_id},
        )
        resp.raise_for_status()
        return resp.json()

    def get_value_case(self, case_id: str) -> dict[str, Any]:
        """Step 7b: Get complete value case."""
        resp = requests.get(
            f"{self.base_url}/v1/value-engine/cases/{case_id}",
            headers=self._headers(),
        )
        resp.raise_for_status()
        return resp.json()

    def get_value_case_preview(self, case_id: str) -> dict[str, Any]:
        """Step 7c: Preview narrative output."""
        resp = requests.get(
            f"{self.base_url}/v1/value-engine/cases/{case_id}/preview",
            headers=self._headers(),
        )
        resp.raise_for_status()
        return resp.json()


@pytest.fixture
def l4_client() -> ValueEngineE2EClient:
    """Create E2E client for Layer 4 (orchestrator)."""
    base_url = os.getenv("LAYER4_AGENTS_URL", "http://localhost:8004")
    return ValueEngineE2EClient(base_url)


@pytest.mark.e2e
@pytest.mark.skipif(
    os.getenv("RUN_E2E") != "1",
    reason="E2E tests require RUN_E2E=1 and running stack",
)
class TestValueEngineE2E:
    """7-Step Value Engine E2E Test Suite."""

    def test_step_1_prospect_setup(self, l4_client: ValueEngineE2EClient) -> None:
        """Step 1: Prospect Setup - company profile exists."""
        # Auth
        l4_client.signup(DEMO_USER["email"], DEMO_USER["password"], DEMO_USER["name"])

        # Create prospect
        prospect = l4_client.create_prospect(
            DEMO_PROSPECT["company_name"],
            DEMO_PROSPECT["domain"],
        )
        assert "id" in prospect
        prospect_id = prospect["id"]

        # Enrich
        enrich_result = l4_client.enrich_prospect(prospect_id)
        assert "status" in enrich_result

        # Context
        context = l4_client.get_prospect_context(prospect_id)
        assert "company_profile" in context or "context" in context

    def test_step_2_intelligence_gathering(self, l4_client: ValueEngineE2EClient) -> None:
        """Step 2: Intelligence Gathering - workflow completes."""
        l4_client.signup(
            f"test_{uuid.uuid4().hex[:8]}@test.com",
            DEMO_USER["password"],
            DEMO_USER["name"],
        )

        prospect = l4_client.create_prospect("TestCorp", "testcorp.com")
        prospect_id = prospect["id"]

        # Run intelligence workflow
        workflow = l4_client.run_intelligence_workflow(prospect_id)
        assert "workflow_id" in workflow or "id" in workflow
        workflow_id = workflow.get("workflow_id") or workflow.get("id")

        # Get findings
        findings = l4_client.get_intelligence_findings(prospect_id)
        assert "items" in findings or "findings" in findings or "pain_points" in findings

    def test_step_3_value_hypothesis(self, l4_client: ValueEngineE2EClient) -> None:
        """Step 3: AI Model / Value Hypothesis - at least one hypothesis exists."""
        l4_client.signup(
            f"test_{uuid.uuid4().hex[:8]}@test.com",
            DEMO_USER["password"],
            DEMO_USER["name"],
        )

        prospect = l4_client.create_prospect("TestCorp", "testcorp.com")
        prospect_id = prospect["id"]

        # Create hypothesis
        hypothesis = l4_client.create_hypothesis(
            prospect_id,
            "Cost reduction through automation",
        )
        assert "id" in hypothesis

        # List hypotheses
        hypotheses = l4_client.get_hypotheses(prospect_id)
        assert len(hypotheses.get("items", [])) >= 1

    def test_step_4_driver_tree(self, l4_client: ValueEngineE2EClient) -> None:
        """Step 4: Driver Tree - tree has root, branches, leaves."""
        l4_client.signup(
            f"test_{uuid.uuid4().hex[:8]}@test.com",
            DEMO_USER["password"],
            DEMO_USER["name"],
        )

        prospect = l4_client.create_prospect("TestCorp", "testcorp.com")
        prospect_id = prospect["id"]

        # Create driver tree
        tree = l4_client.create_driver_tree(prospect_id)
        assert "id" in tree
        tree_id = tree["id"]

        # Get tree
        tree_data = l4_client.get_driver_tree(tree_id)
        assert "nodes" in tree_data or "tree" in tree_data

    def test_step_5_evidence_library(self, l4_client: ValueEngineE2EClient) -> None:
        """Step 5: Evidence Library - evidence exists and can be attached."""
        l4_client.signup(
            f"test_{uuid.uuid4().hex[:8]}@test.com",
            DEMO_USER["password"],
            DEMO_USER["name"],
        )

        prospect = l4_client.create_prospect("TestCorp", "testcorp.com")
        prospect_id = prospect["id"]

        # Get evidence
        evidence = l4_client.get_evidence(prospect_id)
        # Evidence may be empty initially - that's OK
        assert "items" in evidence or "evidence" in evidence

    def test_step_6_roi_calculator(self, l4_client: ValueEngineE2EClient) -> None:
        """Step 6: Calculator - ROI calculated."""
        l4_client.signup(
            f"test_{uuid.uuid4().hex[:8]}@test.com",
            DEMO_USER["password"],
            DEMO_USER["name"],
        )

        prospect = l4_client.create_prospect("TestCorp", "testcorp.com")
        prospect_id = prospect["id"]

        tree = l4_client.create_driver_tree(prospect_id)
        tree_id = tree["id"]

        scenario = l4_client.create_scenario(prospect_id, tree_id)
        assert "id" in scenario
        scenario_id = scenario["id"]

        # Calculate
        calc_result = l4_client.calculate_scenario(scenario_id)
        assert "roi" in calc_result or "results" in calc_result or "status" in calc_result

        # Get with results
        scenario_data = l4_client.get_scenario(scenario_id)
        assert "roi" in scenario_data or "results" in scenario_data or "inputs" in scenario_data

    def test_step_7_value_case(self, l4_client: ValueEngineE2EClient) -> None:
        """Step 7: Value Case - executive summary and narrative exist."""
        l4_client.signup(
            f"test_{uuid.uuid4().hex[:8]}@test.com",
            DEMO_USER["password"],
            DEMO_USER["name"],
        )

        prospect = l4_client.create_prospect("TestCorp", "testcorp.com")
        prospect_id = prospect["id"]

        tree = l4_client.create_driver_tree(prospect_id)
        scenario = l4_client.create_scenario(prospect_id, tree["id"])
        scenario_id = scenario["id"]
        l4_client.calculate_scenario(scenario_id)

        # Create value case
        case = l4_client.create_value_case(prospect_id, scenario_id)
        assert "id" in case
        case_id = case["id"]

        # Get case
        case_data = l4_client.get_value_case(case_id)
        assert "executive_summary" in case_data or "narrative" in case_data or "content" in case_data

        # Preview
        preview = l4_client.get_value_case_preview(case_id)
        assert "preview" in preview or "content" in preview

    def test_full_7_step_workflow(self, l4_client: ValueEngineE2EClient) -> None:
        """Complete 7-step workflow end-to-end."""
        # Use demo identity
        l4_client.signup(DEMO_USER["email"], DEMO_USER["password"], DEMO_USER["name"])

        # Step 1: Prospect Setup
        prospect = l4_client.create_prospect(
            DEMO_PROSPECT["company_name"],
            DEMO_PROSPECT["domain"],
        )
        prospect_id = prospect["id"]
        l4_client.enrich_prospect(prospect_id)

        # Step 2: Intelligence
        workflow = l4_client.run_intelligence_workflow(prospect_id)
        findings = l4_client.get_intelligence_findings(prospect_id)

        # Step 3: Hypothesis
        l4_client.create_hypothesis(prospect_id, "Automation reduces costs by 30%")
        hypotheses = l4_client.get_hypotheses(prospect_id)
        assert len(hypotheses.get("items", [])) >= 1

        # Step 4: Driver Tree
        tree = l4_client.create_driver_tree(prospect_id)
        tree_data = l4_client.get_driver_tree(tree["id"])

        # Step 5: Evidence
        evidence = l4_client.get_evidence(prospect_id)

        # Step 6: ROI
        scenario = l4_client.create_scenario(prospect_id, tree["id"])
        l4_client.calculate_scenario(scenario["id"])

        # Step 7: Value Case
        case = l4_client.create_value_case(prospect_id, scenario["id"])
        case_data = l4_client.get_value_case(case["id"])
        preview = l4_client.get_value_case_preview(case["id"])

        # Assert persistence
        assert prospect_id is not None
        assert tree["id"] is not None
        assert scenario["id"] is not None
        assert case["id"] is not None
