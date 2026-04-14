"""CRM tools for Salesforce/HubSpot integration."""

import logging
from typing import Any

import httpx

from ..models.tool_schemas import (
    FetchInteractionHistoryInput,
    FetchInteractionHistoryOutput,
    GetProspectDataInput,
    GetProspectDataOutput,
    ScoreLeadInput,
    ScoreLeadOutput,
    ToolCategory,
    UpdateOpportunityInput,
    UpdateOpportunityOutput,
)
from .registry import BaseTool

logger = logging.getLogger(__name__)


class GetProspectDataTool(BaseTool):
    """Retrieve prospect data from CRM (Salesforce/HubSpot)."""

    name = "get_prospect_data"
    category = ToolCategory.CRM
    description = "Retrieves prospect profile, interactions, and opportunities from CRM"
    input_schema = GetProspectDataInput
    output_schema = GetProspectDataOutput
    timeout_seconds = 15
    requires_auth = True

    def __init__(self, config: dict[str, Any] | None = None):
        super().__init__(config)
        self.crm_type = config.get("crm_type", "salesforce") if config else "salesforce"
        self.api_key = config.get("crm_api_key") if config else None
        self.api_secret = config.get("crm_api_secret") if config else None
        self.instance_url = config.get("crm_instance_url") if config else None
        self._client = None

    def _get_client(self):
        """Get HTTP client with auth headers."""
        if self._client is None:
            headers = {}
            if self.crm_type == "salesforce" or self.crm_type == "hubspot":
                headers["Authorization"] = f"Bearer {self.api_key}"
            self._client = httpx.AsyncClient(headers=headers, timeout=30.0)
        return self._client

    async def execute(self, input_data: GetProspectDataInput) -> GetProspectDataOutput:
        """Get prospect data from CRM."""
        client = self._get_client()

        try:
            if self.crm_type == "salesforce":
                return await self._get_salesforce_data(client, input_data)
            elif self.crm_type == "hubspot":
                return await self._get_hubspot_data(client, input_data)
            else:
                raise ValueError(f"Unsupported CRM type: {self.crm_type}")
        except Exception as e:
            logger.error(f"CRM data fetch failed: {e}")
            return GetProspectDataOutput(
                profile={}, interactions=[], opportunities=[], custom_fields={}
            )

    async def _get_salesforce_data(
        self, client: httpx.AsyncClient, input_data: GetProspectDataInput
    ) -> GetProspectDataOutput:
        """Fetch data from Salesforce API."""
        prospect_id = input_data.prospect_id

        result = GetProspectDataOutput()

        # Fetch account/profile
        if "profile" in input_data.data_types:
            account_url = f"{self.instance_url}/services/data/v58.0/sobjects/Account/{prospect_id}"
            response = await client.get(account_url)
            if response.status_code == 200:
                data = response.json()
                result.profile = {
                    "id": prospect_id,
                    "name": data.get("Name"),
                    "industry": data.get("Industry"),
                    "company_size": data.get("NumberOfEmployees"),
                    "annual_revenue": data.get("AnnualRevenue"),
                    "website": data.get("Website"),
                    "headquarters": f"{data.get('BillingCity', '')}, {data.get('BillingState', '')}",
                    "employees": data.get("NumberOfEmployees"),
                }

        # Fetch opportunities
        if "opportunities" in input_data.data_types:
            opp_query = f"SELECT Id, Name, StageName, Amount, Probability, CloseDate FROM Opportunity WHERE AccountId = '{prospect_id}'"
            query_url = f"{self.instance_url}/services/data/v58.0/query?q={opp_query}"
            response = await client.get(query_url)
            if response.status_code == 200:
                data = response.json()
                result.opportunities = [
                    {
                        "id": rec.get("Id"),
                        "name": rec.get("Name"),
                        "stage": rec.get("StageName"),
                        "value": rec.get("Amount"),
                        "probability": rec.get("Probability") / 100
                        if rec.get("Probability")
                        else 0,
                        "close_date": rec.get("CloseDate"),
                    }
                    for rec in data.get("records", [])
                ]

        # Fetch interactions (activities)
        if "interactions" in input_data.data_types:
            task_query = f"SELECT Id, Subject, ActivityDate, Status, Description FROM Task WHERE WhatId = '{prospect_id}' ORDER BY ActivityDate DESC"
            query_url = f"{self.instance_url}/services/data/v58.0/query?q={task_query}"
            response = await client.get(query_url)
            if response.status_code == 200:
                data = response.json()
                result.interactions = [
                    {
                        "id": rec.get("Id"),
                        "type": "task",
                        "date": rec.get("ActivityDate"),
                        "subject": rec.get("Subject"),
                        "outcome": rec.get("Status"),
                    }
                    for rec in data.get("records", [])
                ]

        return result

    async def _get_hubspot_data(
        self, client: httpx.AsyncClient, input_data: GetProspectDataInput
    ) -> GetProspectDataOutput:
        """Fetch data from HubSpot API."""
        prospect_id = input_data.prospect_id

        result = GetProspectDataOutput()

        # HubSpot company endpoint
        if "profile" in input_data.data_types:
            url = f"https://api.hubapi.com/crm/v3/objects/companies/{prospect_id}"
            response = await client.get(url)
            if response.status_code == 200:
                data = response.json()
                props = data.get("properties", {})
                result.profile = {
                    "id": prospect_id,
                    "name": props.get("name"),
                    "industry": props.get("industry"),
                    "company_size": props.get("numberofemployees"),
                    "annual_revenue": props.get("annualrevenue"),
                    "website": props.get("website"),
                    "headquarters": props.get("address"),
                    "employees": props.get("numberofemployees"),
                    "domain": props.get("domain"),
                }

        # Fetch opportunities (deals) associated with company
        if "opportunities" in input_data.data_types:
            # HubSpot CRM API v3 - get deals associated with company
            associations_url = (
                f"https://api.hubapi.com/crm/v3/objects/companies/{prospect_id}/associations/deals"
            )
            assoc_response = await client.get(associations_url)

            if assoc_response.status_code == 200:
                assoc_data = assoc_response.json()
                deal_ids = [r.get("toObjectId") for r in assoc_data.get("results", [])]

                # Fetch each deal's details
                opportunities = []
                for deal_id in deal_ids[:50]:  # Limit to 50 deals
                    deal_url = f"https://api.hubapi.com/crm/v3/objects/deals/{deal_id}"
                    deal_response = await client.get(deal_url)
                    if deal_response.status_code == 200:
                        deal_data = deal_response.json()
                        props = deal_data.get("properties", {})
                        opportunities.append(
                            {
                                "id": str(deal_id),
                                "name": props.get("dealname", "Untitled Deal"),
                                "stage": props.get("dealstage", "unknown"),
                                "value": float(props.get("amount", 0))
                                if props.get("amount")
                                else 0,
                                "probability": float(props.get("probability", 0)) / 100
                                if props.get("probability")
                                else 0,
                                "close_date": props.get("closedate"),
                                "pipeline": props.get("pipeline"),
                            }
                        )

                result.opportunities = opportunities

        # Fetch interactions (engagements) via v1 API
        if "interactions" in input_data.data_types:
            engagements_url = f"https://api.hubapi.com/engagements/v1/engagements/associated/COMPANY/{prospect_id}/paged"
            engagements_response = await client.get(engagements_url)

            if engagements_response.status_code == 200:
                engagements_data = engagements_response.json()
                interactions = []

                for eng in engagements_data.get("results", [])[:100]:  # Limit to 100
                    metadata = eng.get("engagement", {})
                    eng.get("associations", {})

                    # Determine interaction type and extract relevant data
                    eng_type = metadata.get("type", "unknown").lower()

                    interaction = {
                        "id": str(metadata.get("id", "")),
                        "type": eng_type,
                        "date": metadata.get("createdAt"),
                        "subject": metadata.get("subject", ""),
                        "outcome": "completed" if metadata.get("active") else "pending",
                    }

                    # Add type-specific details
                    if eng_type == "email":
                        email_meta = eng.get("metadata", {})
                        interaction["subject"] = email_meta.get("subject", "Email")
                        interaction["sender"] = (
                            email_meta.get("from", {}).get("rawEmail")
                            if isinstance(email_meta.get("from"), dict)
                            else None
                        )
                    elif eng_type == "call":
                        call_meta = eng.get("metadata", {})
                        interaction["duration_minutes"] = (
                            call_meta.get("durationMilliseconds", 0) // 60000
                            if call_meta.get("durationMilliseconds")
                            else None
                        )
                        interaction["notes"] = call_meta.get("body", "")
                    elif eng_type == "meeting":
                        meeting_meta = eng.get("metadata", {})
                        interaction["subject"] = meeting_meta.get("title", "Meeting")
                        interaction["duration_minutes"] = (
                            meeting_meta.get("durationMillis", 0) // 60000
                            if meeting_meta.get("durationMillis")
                            else None
                        )
                    elif eng_type == "task":
                        task_meta = eng.get("metadata", {})
                        interaction["subject"] = task_meta.get("subject", "Task")
                        interaction["notes"] = task_meta.get("body", "")

                    interactions.append(interaction)

                result.interactions = interactions

        return result


class UpdateOpportunityTool(BaseTool):
    """Update opportunity fields in CRM."""

    name = "update_opportunity"
    category = ToolCategory.CRM
    description = "Updates opportunity fields and optionally notifies owner"
    input_schema = UpdateOpportunityInput
    output_schema = UpdateOpportunityOutput
    timeout_seconds = 10
    requires_auth = True

    def __init__(self, config: dict[str, Any] | None = None):
        super().__init__(config)
        self.crm_type = config.get("crm_type", "salesforce") if config else "salesforce"
        self.api_key = config.get("crm_api_key") if config else None
        self.instance_url = config.get("crm_instance_url") if config else None
        self._client = None

    def _get_client(self):
        """Get HTTP client with auth headers."""
        if self._client is None:
            headers = {}
            if self.crm_type == "salesforce" or self.crm_type == "hubspot":
                headers["Authorization"] = f"Bearer {self.api_key}"
            self._client = httpx.AsyncClient(headers=headers, timeout=30.0)
        return self._client

    async def execute(self, input_data: UpdateOpportunityInput) -> UpdateOpportunityOutput:
        """Update opportunity in CRM."""
        client = self._get_client()

        try:
            if self.crm_type == "salesforce":
                # Salesforce REST API PATCH
                url = f"{self.instance_url}/services/data/v58.0/sobjects/Opportunity/{input_data.opportunity_id}"
                response = await client.patch(url, json=input_data.updates)
                success = response.status_code in [200, 204]

            elif self.crm_type == "hubspot":
                # HubSpot API
                url = f"https://api.hubapi.com/crm/v3/objects/deals/{input_data.opportunity_id}"
                properties = {k: str(v) for k, v in input_data.updates.items()}
                response = await client.patch(url, json={"properties": properties})
                success = response.status_code == 200
            else:
                raise ValueError(f"Unsupported CRM type: {self.crm_type}")

            return UpdateOpportunityOutput(
                success=success,
                opportunity_id=input_data.opportunity_id,
                updated_fields=list(input_data.updates.keys()),
                error=None if success else response.text,
            )

        except Exception as e:
            logger.error(f"Opportunity update failed: {e}")
            return UpdateOpportunityOutput(
                success=False,
                opportunity_id=input_data.opportunity_id,
                updated_fields=[],
                error=str(e),
            )


class FetchInteractionHistoryTool(BaseTool):
    """Fetch interaction history for a prospect from CRM."""

    name = "fetch_interaction_history"
    category = ToolCategory.CRM
    description = "Retrieves interaction history including emails, calls, meetings"
    input_schema = FetchInteractionHistoryInput
    output_schema = FetchInteractionHistoryOutput
    timeout_seconds = 15
    requires_auth = True

    def __init__(self, config: dict[str, Any] | None = None):
        super().__init__(config)
        self.crm_type = config.get("crm_type", "salesforce") if config else "salesforce"
        self.api_key = config.get("crm_api_key") if config else None
        self.instance_url = config.get("crm_instance_url") if config else None
        self._client = None

    def _get_client(self):
        """Get HTTP client with auth headers."""
        if self._client is None:
            headers = {}
            if self.crm_type == "salesforce" or self.crm_type == "hubspot":
                headers["Authorization"] = f"Bearer {self.api_key}"
            self._client = httpx.AsyncClient(headers=headers, timeout=30.0)
        return self._client

    async def execute(
        self, input_data: FetchInteractionHistoryInput
    ) -> FetchInteractionHistoryOutput:
        """Fetch interaction history from CRM."""
        client = self._get_client()

        try:
            if self.crm_type == "salesforce":
                return await self._get_salesforce_interactions(client, input_data)
            elif self.crm_type == "hubspot":
                return await self._get_hubspot_interactions(client, input_data)
            else:
                raise ValueError(f"Unsupported CRM type: {self.crm_type}")
        except Exception as e:
            logger.error(f"Interaction history fetch failed: {e}")
            return FetchInteractionHistoryOutput(
                interactions=[], total_count=0, summary="No interactions available"
            )

    async def _get_salesforce_interactions(
        self, client: httpx.AsyncClient, input_data: FetchInteractionHistoryInput
    ) -> FetchInteractionHistoryOutput:
        """Fetch interactions from Salesforce."""
        prospect_id = input_data.prospect_id

        # Build SOQL query
        since_clause = ""
        if input_data.since_date:
            since_clause = f" AND ActivityDate >= {input_data.since_date}"

        type_filter = ""
        if input_data.interaction_types:
            types_str = ",".join([f"'{t}'" for t in input_data.interaction_types])
            type_filter = f" AND Type IN ({types_str})"

        query = f"""
            SELECT Id, Subject, ActivityDate, Type, Status, Description, DurationInMinutes
            FROM Task
            WHERE WhatId = '{prospect_id}'{since_clause}{type_filter}
            ORDER BY ActivityDate DESC
            LIMIT {input_data.limit}
        """

        url = f"{self.instance_url}/services/data/v58.0/query?q={query}"
        response = await client.get(url)

        interactions = []
        if response.status_code == 200:
            data = response.json()
            for rec in data.get("records", []):
                interactions.append(
                    {
                        "id": rec.get("Id"),
                        "type": rec.get("Type", "task").lower(),
                        "date": rec.get("ActivityDate"),
                        "subject": rec.get("Subject"),
                        "duration_minutes": rec.get("DurationInMinutes"),
                        "notes": rec.get("Description"),
                        "outcome": rec.get("Status"),
                    }
                )

        # Generate summary
        summary = self._generate_summary(interactions)

        return FetchInteractionHistoryOutput(
            interactions=interactions, total_count=len(interactions), summary=summary
        )

    async def _get_hubspot_interactions(
        self, client: httpx.AsyncClient, input_data: FetchInteractionHistoryInput
    ) -> FetchInteractionHistoryOutput:
        """Fetch interactions from HubSpot."""
        # HubSpot engagements API
        url = f"https://api.hubapi.com/engagements/v1/engagements/associated/COMPANY/{input_data.prospect_id}/paged"

        response = await client.get(url)
        interactions = []

        if response.status_code == 200:
            data = response.json()
            for eng in data.get("results", [])[: input_data.limit]:
                metadata = eng.get("engagement", {})
                interactions.append(
                    {
                        "id": metadata.get("id"),
                        "type": metadata.get("type", "unknown").lower(),
                        "date": metadata.get("createdAt"),
                        "subject": metadata.get("subject", ""),
                        "outcome": "completed" if metadata.get("active") else "pending",
                    }
                )

        summary = self._generate_summary(interactions)

        return FetchInteractionHistoryOutput(
            interactions=interactions, total_count=len(interactions), summary=summary
        )

    def _generate_summary(self, interactions: list[dict]) -> str:
        """Generate summary of interactions."""
        if not interactions:
            return "No recent interactions recorded"

        meeting_count = sum(1 for i in interactions if i.get("type") == "meeting")
        email_count = sum(1 for i in interactions if i.get("type") == "email")
        call_count = sum(1 for i in interactions if i.get("type") == "call")

        parts = [
            f"Recent activity: {meeting_count} meetings, {email_count} emails, {call_count} calls"
        ]

        positive_count = sum(1 for i in interactions if i.get("outcome") == "positive")
        if positive_count >= 2:
            parts.append("Multiple positive interactions indicate strong interest")

        return ". ".join(parts)


class ScoreLeadTool(BaseTool):
    """Score a lead based on profile and engagement data."""

    name = "score_lead"
    category = ToolCategory.CRM
    description = "Calculates lead score based on profile fit and engagement"
    input_schema = ScoreLeadInput
    output_schema = ScoreLeadOutput
    timeout_seconds = 10

    async def execute(self, input_data: ScoreLeadInput) -> ScoreLeadOutput:
        """Calculate lead score."""
        # Get prospect data
        prospect_tool = GetProspectDataTool()
        prospect_data = await prospect_tool.execute(
            GetProspectDataInput(prospect_id=input_data.prospect_id)
        )

        profile = prospect_data.profile
        interactions = prospect_data.interactions
        opportunities = prospect_data.opportunities

        # Calculate component scores
        factors = {}

        # Company size score
        employees = profile.get("employees", 0)
        if employees >= 1000:
            factors["company_size"] = 20
        elif employees >= 500:
            factors["company_size"] = 15
        elif employees >= 100:
            factors["company_size"] = 10
        else:
            factors["company_size"] = 5

        # Industry fit score
        industry = profile.get("industry", "").lower()
        high_fit_industries = ["manufacturing", "financial_services", "healthcare"]
        medium_fit_industries = ["technology", "retail"]

        if any(i in industry for i in high_fit_industries):
            factors["industry_fit"] = 15
        elif any(i in industry for i in medium_fit_industries):
            factors["industry_fit"] = 10
        else:
            factors["industry_fit"] = 5

        # Engagement score
        interaction_count = len(interactions)
        positive_signals = sum(1 for i in interactions if i.get("outcome") == "positive")

        factors["engagement"] = min(20, interaction_count * 5 + positive_signals * 5)

        # Opportunity value score
        if opportunities:
            max_value = max(opp.get("value", 0) for opp in opportunities)
            if max_value >= 500000:
                factors["opportunity_value"] = 20
            elif max_value >= 100000:
                factors["opportunity_value"] = 15
            elif max_value >= 50000:
                factors["opportunity_value"] = 10
            else:
                factors["opportunity_value"] = 5
        else:
            factors["opportunity_value"] = 0

        # Budget indicator
        custom_fields = prospect_data.custom_fields
        if custom_fields.get("budget_approved"):
            factors["budget_confirmed"] = 15
        else:
            factors["budget_confirmed"] = 0

        # Calculate total score
        total_score = sum(factors.values())

        # Determine grade
        if total_score >= 80:
            grade = "A"
        elif total_score >= 60:
            grade = "B"
        elif total_score >= 40:
            grade = "C"
        elif total_score >= 20:
            grade = "D"
        else:
            grade = "F"

        # Generate recommendations
        recommendations = []
        if factors["engagement"] < 10:
            recommendations.append("Increase engagement with targeted content")
        if factors["budget_confirmed"] == 0:
            recommendations.append("Confirm budget authority in next conversation")
        if factors["opportunity_value"] < 10:
            recommendations.append("Explore expansion opportunities")
        if grade in ["A", "B"]:
            recommendations.append("Prioritize for immediate follow-up")

        return ScoreLeadOutput(
            score=total_score,
            grade=grade,
            factors=factors,
            recommendations=recommendations if recommendations else ["Continue nurturing"],
        )
