"""
L5 Validation Hook — abstraction for claim validation with graceful fallback.

Rules:
  - Do not hard-depend on live L5 if current test setup lacks it.
  - Do not silently approve when L5 is unavailable.
  - Use needs_review or insufficient_evidence fallback.
  - Preserve room for real L5 integration.
"""

from __future__ import annotations

import abc
import random
from datetime import datetime, timezone
from typing import List, Optional

from harness.models import (
    ClaimValidationResult,
    HarnessTraceEvent,
    HarnessWorkflowType,
    ValidationState,
)


class ValidationUnavailableError(RuntimeError):
    """Raised when the validator is unavailable and fallback is not configured."""

    pass


class ClaimValidationRequest:
    """Request to validate a claim."""

    def __init__(
        self,
        tenant_id: str,
        claim_id: str,
        claim_text: str,
        evidence_refs: List[str],
        value_pack_id: Optional[str] = None,
        account_id: Optional[str] = None,
    ) -> None:
        self.tenant_id = tenant_id
        self.claim_id = claim_id
        self.claim_text = claim_text
        self.evidence_refs = evidence_refs
        self.value_pack_id = value_pack_id
        self.account_id = account_id


class ClaimValidator(abc.ABC):
    """
    Protocol for L5 claim validators.

    Implementations:
      - UnavailableValidator: fallback when L5 is unreachable.
      - LiveL5Validator: future integration with Layer 5 Ground Truth.
      - MockValidator: testing.
    """

    @abc.abstractmethod
    def validate(
        self,
        request: ClaimValidationRequest,
    ) -> ClaimValidationResult:
        """
        Validate a claim.

        Must NOT silently approve. On unavailable, return needs_review or
        insufficient_evidence.
        """
        ...

    @abc.abstractmethod
    def health(self) -> bool:
        """Return True if validator is healthy and available."""
        ...


class UnavailableValidator(ClaimValidator):
    """
    Fallback validator when L5 is unavailable.

    NEVER approves. Always returns insufficient_evidence.
    This ensures claims cannot slip through without real validation.
    """

    def validate(
        self,
        request: ClaimValidationRequest,
    ) -> ClaimValidationResult:
        return ClaimValidationResult(
            tenant_id=request.tenant_id,
            claim_id=request.claim_id,
            validation_state=ValidationState.INSUFFICIENT_EVIDENCE,
            evidence_refs=list(request.evidence_refs),
            confidence=0.0,
            trust_score=0.0,
            validator="unavailable",
            reason="L5 validation service unavailable — claim requires review",
        )

    def health(self) -> bool:
        return False


class MockValidator(ClaimValidator):
    """
    Test validator that returns deterministic results based on claim_id.
    """

    def __init__(
        self,
        default_state: ValidationState = ValidationState.PASSED,
    ) -> None:
        self.default_state = default_state
        self._results: dict[str, ValidationState] = {}

    def set_result(self, claim_id: str, state: ValidationState) -> None:
        """Pre-configure a result for a specific claim."""
        self._results[claim_id] = state

    def validate(
        self,
        request: ClaimValidationRequest,
    ) -> ClaimValidationResult:
        state = self._results.get(request.claim_id, self.default_state)
        confidence = 1.0 if state == ValidationState.PASSED else 0.0
        trust_score = confidence

        return ClaimValidationResult(
            tenant_id=request.tenant_id,
            claim_id=request.claim_id,
            validation_state=state,
            evidence_refs=list(request.evidence_refs),
            confidence=confidence,
            trust_score=trust_score,
            validator="policy" if state == ValidationState.PASSED else "human",
            reason=f"Mock validation result: {state.value}",
        )

    def health(self) -> bool:
        return True


class ValidationHook:
    """
    Orchestrates claim validation with fallback behavior.

    Invariant: unavailable validation never equals approved.
    """

    def __init__(
        self,
        primary_validator: Optional[ClaimValidator] = None,
        fallback_validator: Optional[ClaimValidator] = None,
    ) -> None:
        self._primary = primary_validator
        self._fallback = fallback_validator or UnavailableValidator()

    def validate_claims(
        self,
        requests: List[ClaimValidationRequest],
    ) -> List[ClaimValidationResult]:
        """
        Validate multiple claims.

        Strategy:
          1. If primary validator is healthy, use it.
          2. If primary is unhealthy, use fallback (which never approves).
          3. Return results for all claims.
        """
        validator = self._primary if (self._primary and self._primary.health()) else self._fallback
        return [validator.validate(req) for req in requests]

    def validate_single(
        self,
        request: ClaimValidationRequest,
    ) -> ClaimValidationResult:
        """Validate a single claim."""
        validator = self._primary if (self._primary and self._primary.health()) else self._fallback
        return validator.validate(request)

    @property
    def is_available(self) -> bool:
        """True if the primary validator is healthy."""
        return self._primary is not None and self._primary.health()
