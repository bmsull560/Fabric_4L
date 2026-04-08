"""Agent taxonomy and implementations for Layer 4.

Provides 8 agent types as defined in the specification:
- DocumentIngestionAgent
- FinancialExtractionAgent
- ValueTreeProjectionAgent
- WhitespaceAnalysisAgent
- ROICalculationAgent
- NarrativeSynthesisAgent
- ProvenanceTrackingAgent
- OrchestrationController
"""

from .base import BaseAgent, AgentState, AgentCapability
from .taxonomy import (
    AgentType,
    DocumentIngestionAgent,
    FinancialExtractionAgent,
    ValueTreeProjectionAgent,
    WhitespaceAnalysisAgent,
    ROICalculationAgent,
    NarrativeSynthesisAgent,
    ProvenanceTrackingAgent,
    OrchestrationController,
)

__all__ = [
    # Base
    "BaseAgent",
    "AgentState",
    "AgentCapability",
    # Taxonomy & Types
    "AgentType",
    # Agents
    "DocumentIngestionAgent",
    "FinancialExtractionAgent",
    "ValueTreeProjectionAgent",
    "WhitespaceAnalysisAgent",
    "ROICalculationAgent",
    "NarrativeSynthesisAgent",
    "ProvenanceTrackingAgent",
    "OrchestrationController",
]
