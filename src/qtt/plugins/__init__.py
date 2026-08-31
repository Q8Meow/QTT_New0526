"""Deterministic nonlive plugin ABI for PR162E."""

from .contracts import (
    PluginAdapterBase,
    PluginAuthorityEnvelope,
    PluginContext,
    PluginDiagnostic,
    PluginLineageRef,
    PluginRepairPlan,
    PluginRequest,
    PluginResponse,
    PluginRetestPlan,
    PluginRuntimeBudget,
    ValidationReceipt,
)

__all__ = [
    "PluginAdapterBase",
    "PluginAuthorityEnvelope",
    "PluginContext",
    "PluginDiagnostic",
    "PluginLineageRef",
    "PluginRepairPlan",
    "PluginRequest",
    "PluginResponse",
    "PluginRetestPlan",
    "PluginRuntimeBudget",
    "ValidationReceipt",
]

from .contracts import (
    CompatibilityAndDependencyReceiptV1,
    PackageAdmissionStateV1,
    PackageCompatibilityStateV1,
    PackageOperationEligibilityStateV1,
    PackageOperationEligibilityV1,
    PackageReproducibilityReceiptV1,
    PackageRollbackTargetKindV1,
    PackageSupersessionStateV1,
    PackageValidationTerminalStateV1,
    PackageVersionV1,
    PluginPackageContractError,
    PluginPackageReasonCodeV1,
    RollbackAndSupersessionReceiptV1,
    SelectedComponentPackageEntryV1,
    SelectedComponentPackageManifestV1,
)
from .dag import compile_selected_package_dependency_order_v1
from .registry import (
    build_selected_component_package_manifest_v1,
    derive_rollback_and_supersession_receipt_v1,
    rebuild_selected_component_package_v1,
    selected_component_package_projection_v1,
    validate_package_supersession_v1,
    validate_selected_component_package_v1,
)

__all__ += [
    "PluginPackageReasonCodeV1",
    "PluginPackageContractError",
    "PackageVersionV1",
    "PackageAdmissionStateV1",
    "PackageCompatibilityStateV1",
    "PackageRollbackTargetKindV1",
    "PackageOperationEligibilityStateV1",
    "PackageValidationTerminalStateV1",
    "PackageSupersessionStateV1",
    "PackageOperationEligibilityV1",
    "SelectedComponentPackageEntryV1",
    "SelectedComponentPackageManifestV1",
    "CompatibilityAndDependencyReceiptV1",
    "RollbackAndSupersessionReceiptV1",
    "PackageReproducibilityReceiptV1",
    "compile_selected_package_dependency_order_v1",
    "build_selected_component_package_manifest_v1",
    "validate_selected_component_package_v1",
    "derive_rollback_and_supersession_receipt_v1",
    "validate_package_supersession_v1",
    "rebuild_selected_component_package_v1",
    "selected_component_package_projection_v1",
]
