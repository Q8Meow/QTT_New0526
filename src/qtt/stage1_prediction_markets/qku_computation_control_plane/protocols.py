"""Data-only Protocol surfaces for later authorized runtime owners."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from .errors import ContractValidationError, OwnerAdapterError, ReasonCode
from .models import (
    ConfigurationEnvelopeV1,
    FallbackEnvelopeV1,
    HealthEnvelopeV1,
    OperationContractV1,
    ModeSnapshotDecisionV1,
    ModeSnapshotOwnerProjectionV1,
    OwnerActionConfirmationReceiptV1,
    ReadOnlyKillSubmitStateV1,
    ST12FEvidenceReferenceV1,
    SupervisionEnvelopeV1,
    validate_reference_identity_classes,
)

if TYPE_CHECKING:
    from .agent_policy import AgentCapabilityDecisionV1
    from .cohort_compiler import ReplayPaperCohortCompilationRecordV1
    from .evidence import (
        ComputationEvidenceBundleV1,
        PaperResultContractV1,
        ReplayResultContractV1,
    )
    from .mode_snapshot_policy import (
        ModeSnapshotCandidateInputsV1,
        ModeSnapshotPreconstructionGateV1,
    )
    from .models import (
        BuildEvidenceBundleRequestV1,
        CompileReplayPaperCohortRequestV1,
        ComputationExecutionContextV1,
        RegisterReplayPaperResultRequestV1,
    )


@runtime_checkable
class ServiceBoundaryProtocolV1(Protocol):
    """Describes a service contract; it does not start or operate a service."""

    def describe_operation(self, operation_id: str) -> OperationContractV1: ...


@runtime_checkable
class ConfigurationBoundaryProtocolV1(Protocol):
    def describe_configuration(self) -> ConfigurationEnvelopeV1: ...


@runtime_checkable
class HealthBoundaryProtocolV1(Protocol):
    def describe_health(self) -> HealthEnvelopeV1: ...


@runtime_checkable
class SupervisionBoundaryProtocolV1(Protocol):
    def describe_supervision(self) -> SupervisionEnvelopeV1: ...


@runtime_checkable
class FallbackBoundaryProtocolV1(Protocol):
    def describe_fallback(self, reason_code: str) -> FallbackEnvelopeV1: ...


@runtime_checkable
class ReadinessProjectionProtocolV1(Protocol):
    def describe_readiness_route(self, qku_id: str) -> OperationContractV1: ...


@runtime_checkable
class PretradeProjectionProtocolV1(Protocol):
    def describe_pretrade_route(self, qku_id: str) -> OperationContractV1: ...


@runtime_checkable
class OwnerReadModelProjectionProtocolV1(Protocol):
    def describe_read_model_route(self, qku_id: str) -> OperationContractV1: ...


@runtime_checkable
class AgentDagProjectionProtocolV1(Protocol):
    def describe_agent_dag_route(self, qku_id: str) -> OperationContractV1: ...


@runtime_checkable
class AgentCapabilityAdmissionProtocolV1(Protocol):
    """Typed no-effect admission hook; it does not grant runtime authority."""

    def admit_operation(
        self, request: object
    ) -> "AgentCapabilityDecisionV1": ...


@runtime_checkable
class ReplayPaperCohortCompilerProtocolV1(Protocol):
    """Injected OP13 delegate; it exposes no execution or runner method."""

    def compile(
        self, request: "CompileReplayPaperCohortRequestV1"
    ) -> "ReplayPaperCohortCompilationRecordV1": ...


@runtime_checkable
class ComputationEvidenceServiceProtocolV1(Protocol):
    """Injected OP14/OP15 and read-only F-reference behavior."""

    def register_result(
        self, request: "RegisterReplayPaperResultRequestV1"
    ) -> "ReplayResultContractV1 | PaperResultContractV1": ...

    def build_bundle(
        self,
        request: "BuildEvidenceBundleRequestV1",
    ) -> "ComputationEvidenceBundleV1": ...

    def read_evidence_reference(
        self,
        context: "ComputationExecutionContextV1",
        *,
        causation_id: str,
        correlation_id: str,
        query: object | None = None,
    ) -> ST12FEvidenceReferenceV1: ...


@runtime_checkable
class SafetyStateProjectionProtocolV1(Protocol):
    """Read-only safety-state view owned outside ST12-E."""

    def describe_safety_state(self, context_ref: str) -> object: ...


@runtime_checkable
class ReadOnlyKillSubmitStateProtocolV1(Protocol):
    """Read exact current safety state; no set, clear, or override method exists."""

    def read_kill_submit_state(
        self, context: "ComputationExecutionContextV1"
    ) -> ReadOnlyKillSubmitStateV1: ...


@runtime_checkable
class ST12FEvidenceReferenceProtocolV1(Protocol):
    """Read only a future-F reference state; D cannot produce evidence."""

    def read_evidence_reference(
        self,
        context: "ComputationExecutionContextV1",
        *,
        causation_id: str,
        correlation_id: str,
        query: object | None = None,
    ) -> ST12FEvidenceReferenceV1: ...


@runtime_checkable
class OwnerActionConfirmationProtocolV1(Protocol):
    """Read one exact current owner-action receipt; no action method exists."""

    def read_owner_action_confirmation(
        self, context: "ComputationExecutionContextV1"
    ) -> OwnerActionConfirmationReceiptV1: ...


@runtime_checkable
class ModeSnapshotCandidateInputProtocolV1(Protocol):
    """Resolve the early gate first, then enrich only a nonterminal gate."""

    def resolve_mode_snapshot_preconstruction_gate(
        self,
        request: object,
        capability_decision: "AgentCapabilityDecisionV1",
    ) -> "ModeSnapshotPreconstructionGateV1": ...

    def enrich_mode_snapshot_candidate(
        self,
        request: object,
        capability_decision: "AgentCapabilityDecisionV1",
        preconstruction_gate: "ModeSnapshotPreconstructionGateV1",
        owner_projections: "PreloadedOwnerProjectionBundleV1",
    ) -> "ModeSnapshotCandidateInputsV1": ...


@runtime_checkable
class ModeSnapshotCandidateValidationProtocolV1(Protocol):
    """Optional independent candidate validator with no mutation method."""

    def validate_snapshot_candidate(
        self, candidate: object
    ) -> tuple[ReasonCode, ...]: ...


@runtime_checkable
class ModeSnapshotOwnerProjectionProtocolV1(Protocol):
    """One-way D state projection into the existing owner semantic fabric."""

    def project_mode_snapshot(
        self,
        decision: ModeSnapshotDecisionV1,
        evidence: ST12FEvidenceReferenceV1,
        safety: ReadOnlyKillSubmitStateV1,
        *,
        snapshot_version: str,
        svc_view: "OwnerProjectionViewV1",
    ) -> ModeSnapshotOwnerProjectionV1: ...


@runtime_checkable
class MemoryPriorProjectionProtocolV1(Protocol):
    """MEM1 condition-scoped prior view requiring current revalidation."""

    def describe_memory_prior(self, context_ref: str) -> object: ...


@runtime_checkable
class OwnerActionSemanticProtocolV1(Protocol):
    """Read-only central owner action grammar shared by every surface."""

    def describe_owner_action(self, action_id: str) -> object: ...


@dataclass(frozen=True, slots=True)
class OwnerProjectionViewV1:
    owner_id: str
    authority_domain: str
    source_path: str
    source_version: str
    source_snapshot_ref: str
    consume_interfaces: tuple[str, ...]
    row_count: int
    identity_refs: tuple[str, ...]
    receipt_refs: tuple[str, ...] = ()
    source_epoch_refs: tuple[str, ...] = ()
    projection_mutation_allowed: bool = False
    runtime_effect_allowed: bool = False

    def __post_init__(self) -> None:
        for name in (
            "owner_id",
            "authority_domain",
            "source_path",
            "source_version",
            "source_snapshot_ref",
        ):
            value = getattr(self, name)
            if not isinstance(value, str) or not value:
                raise OwnerAdapterError(
                    ReasonCode.OWNER_DATA_MALFORMED,
                    f"{name} is required for an owner projection view",
                )
        for name in ("consume_interfaces", "identity_refs"):
            values = getattr(self, name)
            if (
                not isinstance(values, tuple)
                or not values
                or any(not isinstance(value, str) or not value for value in values)
                or len(set(values)) != len(values)
            ):
                raise OwnerAdapterError(
                    ReasonCode.OWNER_DATA_MALFORMED,
                    f"{name} must contain unique nonempty owner lineage strings",
                )
        for name in ("receipt_refs", "source_epoch_refs"):
            values = getattr(self, name)
            if (
                not isinstance(values, tuple)
                or any(not isinstance(value, str) or not value for value in values)
                or len(set(values)) != len(values)
            ):
                raise OwnerAdapterError(
                    ReasonCode.OWNER_DATA_MALFORMED,
                    f"{name} must contain only actual unique owner identities",
                )
        if self.source_snapshot_ref != self.source_path:
            raise OwnerAdapterError(
                ReasonCode.OWNER_DATA_MALFORMED,
                "owner projection source snapshot must be the exact consumed source path",
            )
        try:
            validate_reference_identity_classes(
                source_snapshot_refs=(
                    self.source_snapshot_ref,
                    self.source_version,
                    *self.identity_refs,
                ),
                source_epoch_refs=self.source_epoch_refs,
                receipt_refs=self.receipt_refs,
            )
        except ContractValidationError as exc:
            raise OwnerAdapterError(
                ReasonCode.OWNER_DATA_MALFORMED,
                "owner projection reference classes overlap or contain synthetic lineage",
            ) from exc
        if (
            isinstance(self.row_count, bool)
            or not isinstance(self.row_count, int)
            or self.row_count <= 0
        ):
            raise OwnerAdapterError(
                ReasonCode.OWNER_DATA_MALFORMED,
                "owner projection row_count must be positive",
            )
        if (
            type(self.projection_mutation_allowed) is not bool
            or type(self.runtime_effect_allowed) is not bool
        ):
            raise OwnerAdapterError(
                ReasonCode.OWNER_DATA_MALFORMED,
                "owner projection authority flags must be booleans",
            )
        if self.projection_mutation_allowed or self.runtime_effect_allowed:
            raise OwnerAdapterError(
                ReasonCode.CAPABILITY_DENIED,
                "Tranche A owner views cannot mutate projections or exercise effects",
            )
        from .serialization import validate_relative_path

        validate_relative_path(self.source_path)


@dataclass(frozen=True, slots=True)
class PreloadedOwnerProjectionBundleV1:
    """Immutable four-owner projection bundle loaded outside the D request path."""

    readiness: OwnerProjectionViewV1
    pretrade: OwnerProjectionViewV1
    svc: OwnerProjectionViewV1
    agent_orch: OwnerProjectionViewV1

    def __post_init__(self) -> None:
        rows = (self.readiness, self.pretrade, self.svc, self.agent_orch)
        if any(type(row) is not OwnerProjectionViewV1 for row in rows) or tuple(
            row.owner_id for row in rows
        ) != ("READINESS1", "PRETRADE1", "SVC1", "AGENT_ORCH1"):
            raise OwnerAdapterError(
                ReasonCode.OWNER_DATA_MALFORMED,
                "preloaded D projections require the exact four current owner views",
            )
        if any(
            row.projection_mutation_allowed or row.runtime_effect_allowed
            for row in rows
        ):
            raise OwnerAdapterError(
                ReasonCode.CAPABILITY_DENIED,
                "preloaded owner projections must remain immutable and no-effect",
            )

    @property
    def receipt_refs(self) -> tuple[str, ...]:
        return tuple(
            ref
            for row in (self.readiness, self.pretrade, self.svc, self.agent_orch)
            for ref in row.receipt_refs
        )

    @property
    def source_epoch_refs(self) -> tuple[str, ...]:
        return tuple(
            ref
            for row in (self.readiness, self.pretrade, self.svc, self.agent_orch)
            for ref in row.source_epoch_refs
        )

    @property
    def source_snapshot_refs(self) -> tuple[str, ...]:
        return tuple(
            row.source_snapshot_ref
            for row in (self.readiness, self.pretrade, self.svc, self.agent_orch)
        )


def _validated_rows(
    rows: object,
    *,
    owner_id: str,
) -> tuple[dict[str, object], ...]:
    if not isinstance(rows, tuple) or not rows:
        raise OwnerAdapterError(
            ReasonCode.OWNER_DATA_MISSING,
            f"{owner_id} returned no typed projection rows",
        )
    if any(not isinstance(row, dict) for row in rows):
        raise OwnerAdapterError(
            ReasonCode.OWNER_DATA_MALFORMED,
            f"{owner_id} returned a non-object projection row",
        )
    typed_rows = rows
    forbidden = sorted(
        {
            key
            for row in typed_rows
            for key, value in row.items()
            if isinstance(key, str) and key.endswith("_created") and value is True
        }
    )
    if forbidden:
        raise OwnerAdapterError(
            ReasonCode.OWNER_DATA_CONTRADICTORY,
            f"{owner_id} reports exercised effects: {forbidden}",
        )
    return typed_rows


def _single_projection_version(
    rows: tuple[dict[str, object], ...],
    *,
    owner_id: str,
) -> str:
    versions = {
        value
        for row in rows
        for key in ("projection_version", "version")
        if isinstance((value := row.get(key)), str) and value
    }
    if len(versions) != 1:
        raise OwnerAdapterError(
            ReasonCode.OWNER_DATA_CONTRADICTORY,
            f"{owner_id} must expose exactly one projection version",
        )
    return versions.pop()


class ExistingOwnerProjectionAdapterV1:
    """Explicit read-only consumption of the four current projection owners."""

    def __init__(self, repo_root: str | Path) -> None:
        self._repo_root = Path(repo_root).resolve()

    def load_readiness(self) -> OwnerProjectionViewV1:
        from src.qtt.readiness.pr169_readiness1_resolvers import (
            load_agent_universe,
            load_formula_resolver,
            load_qku_resolver,
            load_registry,
        )

        try:
            registry = _validated_rows(
                load_registry(repo_root=self._repo_root).rows,
                owner_id="READINESS1",
            )
            agents = _validated_rows(
                load_agent_universe(repo_root=self._repo_root).rows,
                owner_id="READINESS1",
            )
            qku_rows = _validated_rows(
                load_qku_resolver(repo_root=self._repo_root).rows,
                owner_id="READINESS1",
            )
            formula_rows = _validated_rows(
                load_formula_resolver(repo_root=self._repo_root).rows,
                owner_id="READINESS1",
            )
        except (OSError, KeyError, TypeError, ValueError) as exc:
            if isinstance(exc, OwnerAdapterError):
                raise
            raise OwnerAdapterError(
                ReasonCode.OWNER_DATA_MISSING,
                "READINESS1 projection interfaces could not be consumed",
            ) from exc
        if registry != qku_rows or registry != formula_rows:
            raise OwnerAdapterError(
                ReasonCode.OWNER_DATA_CONTRADICTORY,
                "READINESS1 identity resolvers do not share canonical rows",
            )
        version = _single_projection_version(
            registry + agents, owner_id="READINESS1"
        )
        return OwnerProjectionViewV1(
            owner_id="READINESS1",
            authority_domain="READINESS_PROJECTION",
            source_path="src/qtt/readiness/pr169_readiness1_resolvers.py",
            source_version=version,
            source_snapshot_ref="src/qtt/readiness/pr169_readiness1_resolvers.py",
            consume_interfaces=(
                "load_registry",
                "load_agent_universe",
                "load_qku_resolver",
                "load_formula_resolver",
            ),
            row_count=len(registry) + len(agents),
            identity_refs=(
                "CandidateReadinessResolverV1",
                "Stage1AgentComputationUniverseV1",
                "QKUAccessResolverV1",
                "FormulaAccessResolverV1",
            ),
        )

    def load_pretrade(self) -> OwnerProjectionViewV1:
        from src.qtt.pretrade.pr169_pretrade1_resolvers import load_registry

        try:
            rows = _validated_rows(
                load_registry(repo_root=self._repo_root).rows,
                owner_id="PRETRADE1",
            )
        except (OSError, KeyError, TypeError, ValueError) as exc:
            if isinstance(exc, OwnerAdapterError):
                raise
            raise OwnerAdapterError(
                ReasonCode.OWNER_DATA_MISSING,
                "PRETRADE1 registry could not be consumed",
            ) from exc
        return OwnerProjectionViewV1(
            owner_id="PRETRADE1",
            authority_domain="PRETRADE_REALITY_AND_DECISION_PROJECTION",
            source_path="src/qtt/pretrade/pr169_pretrade1_resolvers.py",
            source_version=_single_projection_version(
                rows, owner_id="PRETRADE1"
            ),
            source_snapshot_ref="src/qtt/pretrade/pr169_pretrade1_resolvers.py",
            consume_interfaces=("load_registry",),
            row_count=len(rows),
            identity_refs=("PreTradeRegistryView",),
        )

    def load_svc(self) -> OwnerProjectionViewV1:
        from src.qtt.service.pr169_svc1_resolvers import DashboardReadModelService

        base_dir = self._repo_root / "docs/master_plan/generated/pr169_svc1"
        try:
            service = DashboardReadModelService(base_dir)
            manifest = service.load_service_manifest()
            rows = _validated_rows(
                service.list_read_model_snapshots(), owner_id="SVC1"
            )
        except (OSError, KeyError, TypeError, ValueError) as exc:
            if isinstance(exc, OwnerAdapterError):
                raise
            raise OwnerAdapterError(
                ReasonCode.OWNER_DATA_MISSING,
                "SVC1 read-model service could not be consumed",
            ) from exc
        if not isinstance(manifest, dict):
            raise OwnerAdapterError(
                ReasonCode.OWNER_DATA_MALFORMED,
                "SVC1 manifest must be an object",
            )
        version = manifest.get("projection_version")
        if (
            manifest.get("acceptance_state") != "PASS"
            or not isinstance(version, str)
            or not version
            or manifest.get("manual_edit_allowed") is not False
        ):
            raise OwnerAdapterError(
                ReasonCode.OWNER_DATA_STALE,
                "SVC1 manifest lineage or acceptance state is invalid",
            )
        return OwnerProjectionViewV1(
            owner_id="SVC1",
            authority_domain="OWNER_READ_MODEL_AND_ACTION_PROJECTION",
            source_path="src/qtt/service/pr169_svc1_resolvers.py",
            source_version=version,
            source_snapshot_ref="src/qtt/service/pr169_svc1_resolvers.py",
            consume_interfaces=("DashboardReadModelService",),
            row_count=len(rows),
            identity_refs=("read_model_snapshots.generated.jsonl",),
        )

    def load_agent_orch(self) -> OwnerProjectionViewV1:
        from src.qtt.agents.pr169_agent_orch1_resolvers import AgentOrchService

        try:
            service = AgentOrchService(repo_root=self._repo_root)
            manifest = service.load_manifest()
            rows = _validated_rows(service.list_dags(), owner_id="AGENT_ORCH1")
        except (OSError, KeyError, TypeError, ValueError) as exc:
            if isinstance(exc, OwnerAdapterError):
                raise
            raise OwnerAdapterError(
                ReasonCode.OWNER_DATA_MISSING,
                "AGENT_ORCH1 task/DAG projection could not be consumed",
            ) from exc
        if not isinstance(manifest, dict):
            raise OwnerAdapterError(
                ReasonCode.OWNER_DATA_MALFORMED,
                "AGENT_ORCH1 manifest must be an object",
            )
        version = manifest.get("manifest_version")
        if not isinstance(version, str) or not version:
            raise OwnerAdapterError(
                ReasonCode.OWNER_DATA_STALE,
                "AGENT_ORCH1 manifest version is missing",
            )
        return OwnerProjectionViewV1(
            owner_id="AGENT_ORCH1",
            authority_domain="AGENT_TASK_AND_DAG_PROJECTION",
            source_path="src/qtt/agents/pr169_agent_orch1_resolvers.py",
            source_version=version,
            source_snapshot_ref="src/qtt/agents/pr169_agent_orch1_resolvers.py",
            consume_interfaces=("AgentOrchService",),
            row_count=len(rows),
            identity_refs=("dag.jsonl",),
        )

    def load_bundle(self) -> PreloadedOwnerProjectionBundleV1:
        """Load once before request handling; request code consumes only this value."""

        return PreloadedOwnerProjectionBundleV1(
            readiness=self.load_readiness(),
            pretrade=self.load_pretrade(),
            svc=self.load_svc(),
            agent_orch=self.load_agent_orch(),
        )

    def project_mode_snapshot(
        self,
        decision: ModeSnapshotDecisionV1,
        evidence: ST12FEvidenceReferenceV1,
        safety: ReadOnlyKillSubmitStateV1,
        *,
        snapshot_version: str,
        svc_view: OwnerProjectionViewV1,
    ) -> ModeSnapshotOwnerProjectionV1:
        """Project exact D semantics through an already loaded immutable SVC view."""

        if (
            type(svc_view) is not OwnerProjectionViewV1
            or svc_view.owner_id != "SVC1"
            or svc_view.projection_mutation_allowed
            or svc_view.runtime_effect_allowed
        ):
            raise OwnerAdapterError(
                ReasonCode.OWNER_DATA_MALFORMED,
                "D owner projection requires a current no-effect SVC1 view",
            )
        from .mode_snapshot_policy import owner_projection

        return owner_projection(
            decision,
            evidence,
            safety,
            snapshot_version=snapshot_version,
        )
