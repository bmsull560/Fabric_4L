"""
Unit tests for Layer 5 Ground Truth service.

Tests the evidence-backed, CFO-defensible facts management.
"""

import pytest
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import Mock, AsyncMock, patch

from layer5_ground_truth.models.evidence import (
    Evidence,
    EvidenceType,
    EvidenceStatus,
    SourceCredibility,
    ConfidenceLevel,
)
from layer5_ground_truth.services.evidence_service import EvidenceService


class TestEvidenceModel:
    """Test Evidence data model validation and behavior."""

    @pytest.mark.unit
    def test_evidence_creation(self):
        """Evidence can be created with required fields."""
        evidence = Evidence(
            evidence_id="ev-001",
            entity_id="entity-123",
            evidence_type=EvidenceType.FINANCIAL_STATEMENT,
            source_url="https://sec.gov/10k/abc-2024.pdf",
            source_credibility=SourceCredibility.REGULATORY_FILING,
            confidence=ConfidenceLevel.HIGH,
            raw_data={"revenue": 1000000, "net_income": 150000},
        )
        
        assert evidence.evidence_id == "ev-001"
        assert evidence.entity_id == "entity-123"
        assert evidence.status == EvidenceStatus.PENDING  # Default
        assert evidence.verified_at is None

    @pytest.mark.unit
    def test_evidence_confidence_validation(self):
        """Confidence must be within valid range."""
        with pytest.raises(ValueError):
            Evidence(
                evidence_id="ev-002",
                entity_id="entity-123",
                evidence_type=EvidenceType.ANALYST_REPORT,
                source_url="https://example.com/report.pdf",
                source_credibility=SourceCredibility.INDUSTRY_ANALYST,
                confidence="invalid",  # Should be ConfidenceLevel enum
            )

    @pytest.mark.unit
    def test_evidence_verification_flow(self):
        """Evidence can be verified with timestamp."""
        evidence = Evidence(
            evidence_id="ev-003",
            entity_id="entity-123",
            evidence_type=EvidenceType.BENCHMARK_DATA,
            source_url="https://benchmarks.org/data.json",
            source_credibility=SourceCredibility.PEER_BENCHMARK,
            confidence=ConfidenceLevel.MEDIUM,
        )
        
        # Initially pending
        assert evidence.status == EvidenceStatus.PENDING
        assert evidence.verified_at is None
        
        # After verification
        evidence.status = EvidenceStatus.VERIFIED
        evidence.verified_at = datetime.now(timezone.utc)
        evidence.verified_by = "auditor-001"
        
        assert evidence.status == EvidenceStatus.VERIFIED
        assert evidence.verified_at is not None
        assert evidence.verified_by == "auditor-001"

    @pytest.mark.unit
    def test_evidence_rejection_flow(self):
        """Evidence can be rejected with reason."""
        evidence = Evidence(
            evidence_id="ev-004",
            entity_id="entity-123",
            evidence_type=EvidenceType.USER_SUBMITTED,
            source_url="https://user.example.com/claim.pdf",
            source_credibility=SourceCredibility.USER_SUBMITTED,
            confidence=ConfidenceLevel.LOW,
        )
        
        evidence.status = EvidenceStatus.REJECTED
        evidence.rejection_reason = "Insufficient documentation"
        evidence.verified_at = datetime.now(timezone.utc)
        evidence.verified_by = "auditor-002"
        
        assert evidence.status == EvidenceStatus.REJECTED
        assert evidence.rejection_reason == "Insufficient documentation"

    @pytest.mark.unit
    def test_evidence_raw_data_storage(self):
        """Evidence can store arbitrary raw data."""
        raw_data = {
            "financials": {
                "revenue": 1000000,
                "costs": 750000,
                "margin": 0.25,
            },
            "metadata": {
                "fiscal_year": 2024,
                "currency": "USD",
            },
        }
        
        evidence = Evidence(
            evidence_id="ev-005",
            entity_id="entity-456",
            evidence_type=EvidenceType.FINANCIAL_STATEMENT,
            source_url="https://sec.gov/filing.pdf",
            source_credibility=SourceCredibility.REGULATORY_FILING,
            confidence=ConfidenceLevel.HIGH,
            raw_data=raw_data,
        )
        
        assert evidence.raw_data["financials"]["revenue"] == 1000000
        assert evidence.raw_data["metadata"]["currency"] == "USD"


class TestEvidenceService:
    """Test EvidenceService business logic."""

    @pytest.fixture
    def mock_repository(self):
        """Create a mock evidence repository."""
        return Mock()

    @pytest.fixture
    def evidence_service(self, mock_repository):
        """Create evidence service with mock repository."""
        return EvidenceService(repository=mock_repository)

    @pytest.mark.unit
    async def test_create_evidence(self, evidence_service, mock_repository):
        """Service can create new evidence."""
        mock_repository.create = AsyncMock(return_value="ev-006")
        
        evidence_data = {
            "entity_id": "entity-789",
            "evidence_type": EvidenceType.BENCHMARK_DATA,
            "source_url": "https://source.com/data",
            "source_credibility": SourceCredibility.PEER_BENCHMARK,
            "confidence": ConfidenceLevel.MEDIUM,
            "raw_data": {"metric": 42},
        }
        
        evidence_id = await evidence_service.create_evidence(evidence_data)
        
        assert evidence_id == "ev-006"
        mock_repository.create.assert_called_once()

    @pytest.mark.unit
    async def test_verify_evidence(self, evidence_service, mock_repository):
        """Service can verify evidence with auditor ID."""
        mock_evidence = Evidence(
            evidence_id="ev-007",
            entity_id="entity-123",
            evidence_type=EvidenceType.FINANCIAL_STATEMENT,
            source_url="https://sec.gov/filing.pdf",
            source_credibility=SourceCredibility.REGULATORY_FILING,
            confidence=ConfidenceLevel.HIGH,
            status=EvidenceStatus.PENDING,
        )
        mock_repository.get_by_id = AsyncMock(return_value=mock_evidence)
        mock_repository.update = AsyncMock(return_value=True)
        
        result = await evidence_service.verify_evidence(
            evidence_id="ev-007",
            auditor_id="auditor-003",
        )
        
        assert result is True
        assert mock_evidence.status == EvidenceStatus.VERIFIED
        assert mock_evidence.verified_by == "auditor-003"
        assert mock_evidence.verified_at is not None

    @pytest.mark.unit
    async def test_verify_already_verified_evidence_fails(self, evidence_service, mock_repository):
        """Cannot verify already verified evidence."""
        mock_evidence = Evidence(
            evidence_id="ev-008",
            entity_id="entity-123",
            evidence_type=EvidenceType.FINANCIAL_STATEMENT,
            source_url="https://sec.gov/filing.pdf",
            source_credibility=SourceCredibility.REGULATORY_FILING,
            confidence=ConfidenceLevel.HIGH,
            status=EvidenceStatus.VERIFIED,
            verified_at=datetime.now(timezone.utc),
            verified_by="auditor-001",
        )
        mock_repository.get_by_id = AsyncMock(return_value=mock_evidence)
        
        with pytest.raises(ValueError, match="already verified"):
            await evidence_service.verify_evidence(
                evidence_id="ev-008",
                auditor_id="auditor-004",
            )

    @pytest.mark.unit
    async def test_reject_evidence(self, evidence_service, mock_repository):
        """Service can reject evidence with reason."""
        mock_evidence = Evidence(
            evidence_id="ev-009",
            entity_id="entity-123",
            evidence_type=EvidenceType.USER_SUBMITTED,
            source_url="https://user.com/claim.pdf",
            source_credibility=SourceCredibility.USER_SUBMITTED,
            confidence=ConfidenceLevel.LOW,
            status=EvidenceStatus.PENDING,
        )
        mock_repository.get_by_id = AsyncMock(return_value=mock_evidence)
        mock_repository.update = AsyncMock(return_value=True)
        
        result = await evidence_service.reject_evidence(
            evidence_id="ev-009",
            reason="Insufficient supporting documentation",
            auditor_id="auditor-005",
        )
        
        assert result is True
        assert mock_evidence.status == EvidenceStatus.REJECTED
        assert mock_evidence.rejection_reason == "Insufficient supporting documentation"

    @pytest.mark.unit
    async def test_get_evidence_by_entity(self, evidence_service, mock_repository):
        """Service can retrieve all evidence for an entity."""
        mock_repository.get_by_entity = AsyncMock(return_value=[
            Evidence(
                evidence_id="ev-010",
                entity_id="entity-abc",
                evidence_type=EvidenceType.FINANCIAL_STATEMENT,
                source_url="https://sec.gov/10k.pdf",
                source_credibility=SourceCredibility.REGULATORY_FILING,
                confidence=ConfidenceLevel.HIGH,
            ),
            Evidence(
                evidence_id="ev-011",
                entity_id="entity-abc",
                evidence_type=EvidenceType.ANALYST_REPORT,
                source_url="https://analyst.com/report.pdf",
                source_credibility=SourceCredibility.INDUSTRY_ANALYST,
                confidence=ConfidenceLevel.MEDIUM,
            ),
        ])
        
        evidence_list = await evidence_service.get_evidence_by_entity("entity-abc")
        
        assert len(evidence_list) == 2
        assert all(e.entity_id == "entity-abc" for e in evidence_list)

    @pytest.mark.unit
    async def test_calculate_aggregate_confidence(self, evidence_service, mock_repository):
        """Service can calculate aggregate confidence from multiple evidence."""
        mock_repository.get_by_entity = AsyncMock(return_value=[
            Evidence(
                evidence_id="ev-012",
                entity_id="entity-def",
                evidence_type=EvidenceType.FINANCIAL_STATEMENT,
                source_url="https://sec.gov/10k.pdf",
                source_credibility=SourceCredibility.REGULATORY_FILING,
                confidence=ConfidenceLevel.HIGH,
                status=EvidenceStatus.VERIFIED,
            ),
            Evidence(
                evidence_id="ev-013",
                entity_id="entity-def",
                evidence_type=EvidenceType.BENCHMARK_DATA,
                source_url="https://benchmark.org/data",
                source_credibility=SourceCredibility.PEER_BENCHMARK,
                confidence=ConfidenceLevel.MEDIUM,
                status=EvidenceStatus.VERIFIED,
            ),
        ])
        
        aggregate = await evidence_service.calculate_aggregate_confidence("entity-def")
        
        # Should weight by credibility
        assert aggregate["score"] > 0
        assert aggregate["method"] == "weighted_by_credibility"
        assert aggregate["evidence_count"] == 2

    @pytest.mark.unit
    async def test_filter_evidence_by_status(self, evidence_service, mock_repository):
        """Service can filter evidence by status."""
        all_evidence = [
            Evidence(
                evidence_id="ev-014",
                entity_id="entity-ghi",
                evidence_type=EvidenceType.FINANCIAL_STATEMENT,
                source_url="https://1.pdf",
                source_credibility=SourceCredibility.REGULATORY_FILING,
                confidence=ConfidenceLevel.HIGH,
                status=EvidenceStatus.VERIFIED,
            ),
            Evidence(
                evidence_id="ev-015",
                entity_id="entity-ghi",
                evidence_type=EvidenceType.ANALYST_REPORT,
                source_url="https://2.pdf",
                source_credibility=SourceCredibility.INDUSTRY_ANALYST,
                confidence=ConfidenceLevel.MEDIUM,
                status=EvidenceStatus.PENDING,
            ),
            Evidence(
                evidence_id="ev-016",
                entity_id="entity-ghi",
                evidence_type=EvidenceType.USER_SUBMITTED,
                source_url="https://3.pdf",
                source_credibility=SourceCredibility.USER_SUBMITTED,
                confidence=ConfidenceLevel.LOW,
                status=EvidenceStatus.REJECTED,
            ),
        ]
        mock_repository.get_by_entity = AsyncMock(return_value=all_evidence)
        
        verified = await evidence_service.get_evidence_by_entity(
            "entity-ghi", status=EvidenceStatus.VERIFIED
        )
        
        assert len(verified) == 1
        assert verified[0].status == EvidenceStatus.VERIFIED


class TestSourceCredibilityWeighting:
    """Test source credibility weighting calculations."""

    @pytest.mark.unit
    def test_regulatory_filing_highest_weight(self):
        """Regulatory filings have highest credibility weight."""
        assert SourceCredibility.REGULATORY_FILING.weight == 1.0

    @pytest.mark.unit
    def test_user_submitted_lowest_weight(self):
        """User submitted evidence has lowest credibility weight."""
        assert SourceCredibility.USER_SUBMITTED.weight == 0.3

    @pytest.mark.unit
    def test_credibility_weight_ordering(self):
        """Credibility weights follow expected order."""
        weights = [
            SourceCredibility.REGULATORY_FILING.weight,
            SourceCredibility.INDUSTRY_ANALYST.weight,
            SourceCredibility.PEER_BENCHMARK.weight,
            SourceCredibility.ACADEMIC_RESEARCH.weight,
            SourceCredibility.USER_SUBMITTED.weight,
        ]
        
        assert weights == sorted(weights, reverse=True)


class TestConfidenceLevelScoring:
    """Test confidence level scoring."""

    @pytest.mark.unit
    def test_high_confidence_score(self):
        """HIGH confidence has score of 0.9."""
        assert ConfidenceLevel.HIGH.score == 0.9

    @pytest.mark.unit
    def test_medium_confidence_score(self):
        """MEDIUM confidence has score of 0.6."""
        assert ConfidenceLevel.MEDIUM.score == 0.6

    @pytest.mark.unit
    def test_low_confidence_score(self):
        """LOW confidence has score of 0.3."""
        assert ConfidenceLevel.LOW.score == 0.3

    @pytest.mark.unit
    def test_uncertain_confidence_score(self):
        """UNCERTAIN confidence has score of 0.0."""
        assert ConfidenceLevel.UNCERTAIN.score == 0.0
