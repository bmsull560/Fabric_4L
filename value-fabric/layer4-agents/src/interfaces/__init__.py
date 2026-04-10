"""Service interfaces for Phase 2 Architecture Extensions.

Provides clean extension points for:
- Layer 6 Benchmark Service integration
- Value Pack Domain composition
- Formula Governance lifecycle
- Variable Registry resolution
"""

from .benchmark_client import (
    IBenchmarkClient,
    HTTPBenchmarkClient,
    BenchmarkDataset,
    ComparisonRequest,
    ComparisonResult,
    RangeValidationRequest,
    RangeValidationResult,
)

from .value_pack_service import (
    IValuePackService,
    ValuePack,
    ValueDriverRef,
    FormulaRef,
    BenchmarkRef,
    PackExecutionRequest,
    PackExecutionResult,
    PackStatus,
)

from .formula_governance import (
    IFormulaGovernanceService,
    IFormulaApprovalWorkflow,
    FormulaGovernance,
    FormulaVersion,
    FormulaDependency,
    FormulaStatus,
    ActivationRequest,
    DeprecationRequest,
    GovernanceTransitionResult,
)

from .variable_registry import (
    IVariableRegistry,
    IGroundTruthVariableBridge,
    Variable,
    VariableValue,
    VariableSourceBinding,
    VariableValidationRule,
    VariableSearchCriteria,
    ResolutionContext,
    VariableSourceType,
    VariableDataType,
)

__all__ = [
    # Benchmark Client
    "IBenchmarkClient",
    "HTTPBenchmarkClient",
    "BenchmarkDataset",
    "ComparisonRequest",
    "ComparisonResult",
    "RangeValidationRequest",
    "RangeValidationResult",
    # Value Pack Service
    "IValuePackService",
    "ValuePack",
    "ValueDriverRef",
    "FormulaRef",
    "BenchmarkRef",
    "PackExecutionRequest",
    "PackExecutionResult",
    "PackStatus",
    # Formula Governance
    "IFormulaGovernanceService",
    "IFormulaApprovalWorkflow",
    "FormulaGovernance",
    "FormulaVersion",
    "FormulaDependency",
    "FormulaStatus",
    "ActivationRequest",
    "DeprecationRequest",
    "GovernanceTransitionResult",
    # Variable Registry
    "IVariableRegistry",
    "IGroundTruthVariableBridge",
    "Variable",
    "VariableValue",
    "VariableSourceBinding",
    "VariableValidationRule",
    "VariableSearchCriteria",
    "ResolutionContext",
    "VariableSourceType",
    "VariableDataType",
]
