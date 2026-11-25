from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, Iterable, Mapping

if TYPE_CHECKING:
    from ..stage1_prediction_markets.qku_computation_control_plane.existing_owner_projection import (
        ST12GOwnerProjectionResolutionV2,
        ST12GProjectionResolutionV2,
    )


GENERATED_PREFIX = Path("docs/master_plan/generated/pr169_agent_orch1")

JSONL_FILES = frozenset(
    {
        "registry.jsonl",
        "dag.jsonl",
        "dag_nodes.jsonl",
        "dag_edges.jsonl",
        "task_registry.jsonl",
        "task_queue.jsonl",
        "task_env.jsonl",
        "directives.jsonl",
        "workflows.jsonl",
        "handoffs.jsonl",
        "role_map.jsonl",
        "duty_map.jsonl",
        "perm_scope.jsonl",
        "retry_policy.jsonl",
        "priority_policy.jsonl",
        "quarantine.jsonl",
        "agent_ops.jsonl",
        "team_queue.jsonl",
        "intel_lanes.jsonl",
        "tournament_tasks.jsonl",
        "task_receipts.jsonl",
        "decision_receipts.jsonl",
        "dispute_receipts.jsonl",
        "escalation_receipts.jsonl",
        "handoff_receipts.jsonl",
        "audit_trail.jsonl",
        "svc1_bindings.jsonl",
        "readiness_bindings.jsonl",
        "pretrade_bindings.jsonl",
        "mem1_bindings.jsonl",
        "owner_cmd_tasks.jsonl",
        "chat_tasks.jsonl",
        "qku_tasks.jsonl",
        "formula_tasks.jsonl",
        "access_proof.jsonl",
        "library_receipts.jsonl",
        "graph_routes.jsonl",
        "graph_tasks.jsonl",
        "graph_quality.jsonl",
        "tradeplan_tasks.jsonl",
        "pretrade_tasks.jsonl",
        "mode_tasks.jsonl",
        "order_policy_tasks.jsonl",
        "paper_prep.jsonl",
        "hotpath_prep.jsonl",
        "shadow_prep.jsonl",
        "live_prep.jsonl",
        "rank_tasks.jsonl",
        "tca_tasks.jsonl",
        "fdr_tasks.jsonl",
        "portfolio_tasks.jsonl",
        "capacity_tasks.jsonl",
        "champion_tasks.jsonl",
        "mem_prior_tasks.jsonl",
        "utility_tasks.jsonl",
        "scenario_tasks.jsonl",
        "calibration_tasks.jsonl",
        "notrade_tasks.jsonl",
        "var_tune_tasks.jsonl",
        "stack_tasks.jsonl",
        "venue_side_tasks.jsonl",
        "source_refresh_tasks.jsonl",
        "retest_tasks.jsonl",
        "reality_tasks.jsonl",
        "metric_tasks.jsonl",
        "plugin_prep.jsonl",
        "qmap_prep.jsonl",
        "allow_prep.jsonl",
        "formula_intake.jsonl",
        "latency_tiers.jsonl",
        "clean_room.jsonl",
        "quantum_tasks.jsonl",
        "fallback_tasks.jsonl",
        "downstream.jsonl",
        "value_routes.jsonl",
        "capability_routes.jsonl",
        "learning_routes.jsonl",
    }
)

POLICY_JSONL_FILES = (
    "role_map.jsonl",
    "duty_map.jsonl",
    "perm_scope.jsonl",
    "task_env.jsonl",
    "capability_routes.jsonl",
    "decision_receipts.jsonl",
)

PR165_POLICY_REPORTS = (
    Path("docs/master_plan/generated/PR165_D2_AgentRosterDiscoveryAudit.report.json"),
    Path("docs/master_plan/generated/PR165_D2_AgentDutySourceCrosswalk.report.json"),
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _read_jsonl(path: Path) -> tuple[dict[str, Any], ...]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                value = json.loads(line)
                if isinstance(value, dict):
                    rows.append(value)
    return tuple(rows)


def _freeze(value: Any) -> Any:
    if isinstance(value, dict):
        return MappingProxyType(
            {str(key): _freeze(item) for key, item in sorted(value.items())}
        )
    if isinstance(value, list | tuple):
        return tuple(_freeze(item) for item in value)
    return value


def _first(rows: Iterable[dict[str, Any]], key: str, value: str) -> dict[str, Any]:
    for row in rows:
        if str(row.get(key)) == value:
            return dict(row)
    raise KeyError(value)


def _candidate_match(row: dict[str, Any], candidate_id: str) -> bool:
    return candidate_id in {
        str(row.get("candidate_id") or ""),
        str(row.get("candidate_id_or_gap") or ""),
        str(row.get("current_trade_candidate_id_or_gap") or ""),
        str(row.get("candidate_ref") or ""),
    }


@dataclass(frozen=True)
class AgentOrchRows:
    rows: tuple[dict[str, Any], ...]


class AgentOrchRegistry(AgentOrchRows):
    pass


class AgentDAGRegistryV1(AgentOrchRows):
    pass


@dataclass(frozen=True)
class AgentDAGNodeV1:
    row: dict[str, Any]


@dataclass(frozen=True)
class AgentDAGEdgeV1:
    row: dict[str, Any]


class AgentTaskRegistryV1(AgentOrchRows):
    pass


class AgentTaskQueueV1(AgentOrchRows):
    pass


@dataclass(frozen=True)
class AgentTaskEnvelopeV1:
    row: dict[str, Any]


@dataclass(frozen=True)
class AgentDirectiveEnvelopeV1:
    row: dict[str, Any]


class AgentWorkflowRunV1(AgentOrchRows):
    pass


@dataclass(frozen=True)
class AgentHandoffPacketV1:
    row: dict[str, Any]


@dataclass(frozen=True)
class RuntimeTaskReceiptV1:
    row: dict[str, Any]


@dataclass(frozen=True)
class AgentDecisionReceiptV1:
    row: dict[str, Any]


@dataclass(frozen=True)
class AgentDisagreementReceiptV1:
    row: dict[str, Any]


@dataclass(frozen=True)
class AgentEscalationReceiptV1:
    row: dict[str, Any]


@dataclass(frozen=True)
class AgentNoTradeTaskV1:
    row: dict[str, Any]


@dataclass(frozen=True)
class AgentQKUFormulaTaskV1:
    row: dict[str, Any]


@dataclass(frozen=True)
class AgentLLMTaskContractV1:
    row: dict[str, Any]


@dataclass(frozen=True)
class AgentPaperPrepTaskV1:
    row: dict[str, Any]


@dataclass(frozen=True)
class AgentHotpathPrepTaskV1:
    row: dict[str, Any]


@dataclass(frozen=True)
class AgentOrchPolicySnapshotV1:
    """Frozen selected AGENT-ORCH1 policy views loaded once per service."""

    manifest: Mapping[str, Any]
    role_rows: tuple[Mapping[str, Any], ...]
    duty_rows: tuple[Mapping[str, Any], ...]
    permission_rows: tuple[Mapping[str, Any], ...]
    task_envelope_rows: tuple[Mapping[str, Any], ...]
    capability_route_rows: tuple[Mapping[str, Any], ...]
    decision_receipt_rows: tuple[Mapping[str, Any], ...]
    pr165_roster_rows: tuple[Mapping[str, Any], ...]
    pr165_duty_source_rows: tuple[Mapping[str, Any], ...]

    @property
    def manifest_version(self) -> str:
        return str(self.manifest.get("manifest_version") or "")


class AgentOrchService:
    """Thin read API over AGENT-ORCH1 generated contract artifacts."""

    def __init__(self, artifact_dir: str | Path | None = None, repo_root: str | Path | None = None) -> None:
        root = Path(repo_root) if repo_root is not None else _repo_root()
        self.repo_root = root.resolve()
        self.artifact_dir = Path(artifact_dir) if artifact_dir is not None else root / GENERATED_PREFIX
        if not self.artifact_dir.is_absolute():
            self.artifact_dir = root / self.artifact_dir
        self._jsonl_cache: dict[str, tuple[dict[str, Any], ...]] = {}
        self._manifest_cache: dict[str, Any] | None = None
        self._report_cache: dict[Path, tuple[dict[str, Any], ...]] = {}
        self._policy_snapshot_cache: AgentOrchPolicySnapshotV1 | None = None

    def bind_evidence_authority_v1(self, host_binding: "EvidenceHostBindingV1", *,
                                   control_store=None, original_owner_envelopes=(), original_source_registries=(),
                                   original_historical_owner_envelopes=(), original_cold_role_stores=(),
                                   original_callback_registry=None, original_callback_package=None):
        """Explicit private setup; generated artifacts cannot provide this binding."""
        from ..stage1_prediction_markets.qku_computation_control_plane.context import _native_require
        from ..stage1_prediction_markets.qku_computation_control_plane.models import EvidenceKeyPurposeV1

        from ..stage1_prediction_markets.qku_computation_control_plane.errors import ContractValidationError, ReasonCode
        if type(host_binding) is not EvidenceHostBindingV1:
            raise ContractValidationError(ReasonCode.EVIDENCE_AUTHORITY_UNAVAILABLE, "EVIDENCE_AUTHORITY_UNAVAILABLE")
        EvidenceHostBindingV1._assert_local_binding_v1(host_binding)
        configuration = host_binding.public_configuration
        _native_require(configuration.service_owner == "AGENT_ORCH1"
                        and host_binding.signing_purpose is EvidenceKeyPurposeV1.EVIDENCE_ISSUER,
                        "LP03_ISSUER_HOST_ROLE")
        _native_require(getattr(self, "_evidence_authority_binding_v1", None) is None,
                        "LP03_ISSUER_ALREADY_BOUND")
        _native_require(type(original_owner_envelopes) is tuple and type(original_source_registries) is tuple
                        and type(original_historical_owner_envelopes) is tuple and type(original_cold_role_stores) is tuple
                        and (not original_cold_role_stores or original_historical_owner_envelopes)
                        and ((control_store is None and not original_owner_envelopes and not original_source_registries
                              and not original_historical_owner_envelopes and original_callback_registry is None
                              and original_callback_package is None)
                             or (control_store is not None and bool(original_owner_envelopes))),
                        "LP03_ISSUER_SETUP_INCOMPLETE")
        state = (None if control_store is None else _EvidenceIssuerStateV1(
            service=self, host_binding=host_binding, control_store=control_store,
            original_owner_envelopes=original_owner_envelopes, original_source_registries=original_source_registries,
            original_historical_owner_envelopes=original_historical_owner_envelopes,
            original_cold_role_stores=original_cold_role_stores, original_callback_registry=original_callback_registry,
            original_callback_package=original_callback_package))
        self._evidence_authority_binding_v1 = host_binding
        self._evidence_issuer_state_v1 = state
        return None if state is None else state.context

    def recover_cold_evidence_control_v1(self, owner_envelope_ref, *, historical_owner_envelope_ref, issuer_context):
        """Resolve selected original CONTROL evidence without restoring an earlier grant."""
        from ..stage1_prediction_markets.qku_computation_control_plane.context import _native_ident, _native_require
        from ..stage1_prediction_markets.qku_computation_control_plane.persistence import _EvidenceColdControlReadV1

        _native_ident(owner_envelope_ref)
        _native_ident(historical_owner_envelope_ref)
        _native_require(type(issuer_context) is EvidenceIssuerContextV1, "LP03_ISSUER_CONTEXT_REQUIRED")
        state = EvidenceIssuerContextV1._identity_for_owner_v1(issuer_context, self)
        with state.lock:
            _native_require(EvidenceIssuerContextV1._state_for_owner_v1(issuer_context, self) is state,
                "LP03_COLD_ARCHIVE_ORIGINAL_ISSUER_REQUIRED")
            current = tuple(row for row in state.owner_envelopes if row[0] == owner_envelope_ref)
            historical = tuple(row for row in state.historical_owner_envelopes
                if row[2].envelope_ref == historical_owner_envelope_ref)
            _native_require(len(current) == len(historical) == 1, "LP03_COLD_ARCHIVE_ENROLLED_OWNER_REQUIRED")
            operation = _EvidenceColdControlReadV1(issuer=state, current_owner=current[0], historical_owner=historical[0])
            return _EvidenceColdControlReadV1._run_v1(operation)

    def issue_evidence_assembly_grant_v1(self, owner_envelope_ref, *, assembly_request, issuer_context):
        """Private pre-lock admission; a committed readback precedes its handle."""
        from ..stage1_prediction_markets.qku_computation_control_plane.context import _native_require
        _native_require(type(issuer_context) is EvidenceIssuerContextV1, "LP03_ISSUER_CONTEXT_REQUIRED")
        state = EvidenceIssuerContextV1._identity_for_owner_v1(issuer_context, self)
        with state.lock:
            identity = state.lifecycle_identity
            _native_require(EvidenceIssuerContextV1._state_for_owner_v1(issuer_context, self) is state
                            and state.lifecycle_identity is identity, "LP03_CONTROL_LIFECYCLE_IDENTITY_CHANGED")
            return _EvidenceIssuerStateV1._issue_assembly_v1(state, owner_envelope_ref, assembly_request,
                                                            lifecycle_identity=identity)

    def resolve_evidence_assembly_grant_v1(self, grant_ref, *, purpose, requester_context):
        from contextlib import ExitStack
        from ..stage1_prediction_markets.qku_computation_control_plane.context import _native_ident, _native_require
        from ..stage1_prediction_markets.qku_computation_control_plane.input_lock import EvidenceAssemblerContextV1
        from ..stage1_prediction_markets.qku_computation_control_plane.models import EvidenceAssemblyStateV1
        from ..stage1_prediction_markets.qku_computation_control_plane.persistence import _EvidenceControlBootstrapV1
        from ..stage1_prediction_markets.qku_computation_control_plane.sqlite_reference import SQLiteReferenceAdapterV1

        _native_ident(grant_ref)
        _native_require(type(purpose) is str and purpose == "EVIDENCE_INPUT_ASSEMBLY_V1"
                        and type(requester_context) is EvidenceAssemblerContextV1,
                        "LP03_ASSEMBLY_REQUESTER_PURPOSE_REQUIRED")
        state = EvidenceAssemblerContextV1._require_original_v1(requester_context)
        _native_require(state.service is self, "LP03_ASSEMBLY_ISSUER_NOT_ORIGINAL")
        with state.lock, ExitStack() as locks:
            _native_require(state.operation is None, "LP03_CONTROL_OPERATION_REENTRY")
            original = state.preparations.get(grant_ref)
            _native_require(original is not None, "LP03_ORIGINAL_ASSEMBLY_GRANT_UNAVAILABLE")
            operation, handle, _source_original = original
            _native_require(type(handle) is EvidenceAssemblyGrantV1 and handle._owner is state
                            and handle._grant_ref == operation.grant_record.record_id == grant_ref
                            and operation.commit_state == "COMMITTED_AND_READBACK"
                            and operation.current_state.state in (EvidenceAssemblyStateV1.ADMITTED, EvidenceAssemblyStateV1.READING)
                            and requester_context._host.public_configuration.service_principal
                            == operation.grant_record.assembler_principal,
                            "LP03_ORIGINAL_ASSEMBLY_GRANT_UNAVAILABLE")
            state.operation = operation
            try:
                state._lock_original_source_custodies_v1(locks)
                _EvidenceIssuerStateV1._load_bootstrap_metadata_v1(state, operation)
                SQLiteReferenceAdapterV1._evidence_bootstrap_readback_v1(state.control_store, operation)
                _EvidenceControlBootstrapV1._check_current_v1(operation)
                return handle
            finally:
                state.operation = None

    def close_evidence_assembly_v1(self, grant_ref, *, assembly_outcome, issuer_context):
        from contextlib import ExitStack
        from ..stage1_prediction_markets.qku_computation_control_plane.context import _native_ident, _native_require
        from ..stage1_prediction_markets.qku_computation_control_plane.input_lock import (
            EvidenceAssemblerContextV1, EvidenceInputAssemblyOutcomeV1, _require_original_input_assembly_outcome_v1,
        )
        from ..stage1_prediction_markets.qku_computation_control_plane.models import EvidenceAssemblyStateV1, EvidenceRecordRefV1
        from ..stage1_prediction_markets.qku_computation_control_plane.persistence import _EvidenceControlBootstrapV1
        from ..stage1_prediction_markets.qku_computation_control_plane.sqlite_reference import SQLiteReferenceAdapterV1

        _native_ident(grant_ref)
        _native_require(type(issuer_context) is EvidenceIssuerContextV1
                        and type(assembly_outcome) is EvidenceInputAssemblyOutcomeV1, "LP03_ORIGINAL_ASSEMBLY_OUTCOME_REQUIRED")
        state = EvidenceIssuerContextV1._state_for_owner_v1(issuer_context, self)
        with state.lock, ExitStack() as locks:
            _native_require(state.operation is None, "LP03_CONTROL_OPERATION_REENTRY")
            retained = state.preparations.get(grant_ref)
            _native_require(retained is not None and type(retained[1]) is EvidenceAssemblyGrantV1,
                            "LP03_ORIGINAL_ASSEMBLY_GRANT_UNAVAILABLE")
            operation = retained[0]
            _native_require(operation.input_assembly_outcome is assembly_outcome and assembly_outcome._operation is operation
                            and assembly_outcome._assembler is state.assembler_context
                            and operation.commit_state == "COMMITTED_AND_READBACK", "LP03_ORIGINAL_ASSEMBLY_OUTCOME_REQUIRED")
            _require_original_input_assembly_outcome_v1(operation, assembly_outcome)
            EvidenceAssemblerContextV1._require_original_v1(state.assembler_context)
            state.operation = operation
            try:
                state._lock_original_source_custodies_v1(locks)
                _EvidenceIssuerStateV1._load_bootstrap_metadata_v1(state, operation)
                SQLiteReferenceAdapterV1._evidence_bootstrap_readback_v1(state.control_store, operation)
                if operation.current_state.state is not EvidenceAssemblyStateV1.SEALED:
                    SQLiteReferenceAdapterV1._evidence_seal_assembly_v1(state.control_store, operation, assembly_outcome)
                _native_require(operation.current_state.input_assembly_ref_or_absence == assembly_outcome._record.record_id,
                                "LP03_SEALED_ASSEMBLY_STATE_JOIN")
                result = EvidenceRecordRefV1(operation.envelope_entry[3].assembly_scope.control_store_id,
                                             assembly_outcome._record.record_id)
                _EvidenceControlBootstrapV1._check_current_v1(operation)
                return result
            except BaseException:
                if operation.commit_state == "COMMITTED_AND_READBACK":
                    operation.commit_state = "ASSEMBLY_SEAL_FAILED_REQUIRES_AUDIT"
                raise
            finally:
                state.operation = None

    def register_evidence_experiment_v1(self, request, *, issuer_context):
        """Commit original preregistration; the returned reference cannot run a lane."""
        from contextlib import ExitStack
        from ..stage1_prediction_markets.qku_computation_control_plane.context import _native_require
        from ..stage1_prediction_markets.qku_computation_control_plane.models import EvidenceRegistrationRequestV1, EvidenceRecordRefV1
        from ..stage1_prediction_markets.qku_computation_control_plane.persistence import _EvidenceRegistrationOperationV1
        from ..stage1_prediction_markets.qku_computation_control_plane.parameter_policy import _resolve_evidence_registration_policies_v1
        from ..stage1_prediction_markets.qku_computation_control_plane.sqlite_reference import SQLiteReferenceAdapterV1
        from ..stage1_prediction_markets.qku_computation_control_plane.latency_policy import _EvidenceLocalClockV1

        _native_require(type(request) is EvidenceRegistrationRequestV1 and type(issuer_context) is EvidenceIssuerContextV1,
                        "LP03_REGISTRATION_ORIGINAL_CONTEXT")
        state = EvidenceIssuerContextV1._identity_for_owner_v1(issuer_context, self)
        ref = request.input_assembly_ref.record_id
        _native_require(ref.endswith("::INPUT_ASSEMBLY"), "LP03_REGISTRATION_ORIGINAL_ASSEMBLY_JOIN")
        preparation_ref = ref.removesuffix("::INPUT_ASSEMBLY")
        retained = state.preparations.get(preparation_ref)
        _native_require(retained is not None, "LP03_REGISTRATION_ORIGINAL_ASSEMBLY_JOIN")
        operation = state.registrations.get(preparation_ref)
        replay = operation is not None
        if not replay:
            # The constructor samples the original clock before acquiring the
            # issuer lock. Waiting for that lock remains admitted elapsed work.
            operation = _EvidenceRegistrationOperationV1(issuer=state, preparation=retained[0], request=request)
        with state.lock, ExitStack() as locks:
            _native_require(state.operation is None and state.registrations.get(preparation_ref) is operation,
                            "LP03_CONTROL_OPERATION_REENTRY")
            if replay:
                _native_require(type(operation) is _EvidenceRegistrationOperationV1 and operation.request == request
                                and operation.commit_state == "COMMITTED_AND_READBACK" and operation.handle is not None,
                                "LP03_REGISTRATION_ALREADY_RESERVED_OR_UNRESOLVED")
            state.operation = operation
            try:
                state._lock_original_source_custodies_v1(locks)
                _EvidenceRegistrationOperationV1._check_current_v1(operation)
                if replay:
                    SQLiteReferenceAdapterV1._evidence_registration_readback_v1(state.control_store, operation)
                else:
                    SQLiteReferenceAdapterV1._evidence_registration_readback_v1(state.control_store, operation, parent_assembly=True)
                    _resolve_evidence_registration_policies_v1(state.assembler_context._parameter_resolver, operation=operation)
                    SQLiteReferenceAdapterV1._evidence_register_experiment_v1(state.control_store, operation)
                _native_require(operation.commit_observation is not None and operation.readback_observation is not None,
                                "LP03_REGISTRATION_COMMIT_READBACK_UNRESOLVED")
                result = operation.handle if operation.handle is not None else EvidenceRecordRefV1(
                    request.input_assembly_ref.store_id, operation.records[0].record_id)
                wall, _mono, _cpu = _EvidenceRegistrationOperationV1._check_current_v1(operation)
                _native_require(operation.protocol.valid_from_wall_ns <= wall < operation.records[0].expiry_wall_ns,
                                "LP03_PARAMETER_PROTOCOL_EXPIRED")
                operation.handle = result
                return operation.handle
            except BaseException:
                # Failure remains on the original natural key, including actual
                # failed-read/decoder work. Never erase or renew that deadline.
                if operation.commit_state not in ("ROLLED_BACK", "ROLLBACK_UNPROVEN", "COMMIT_OR_OBSERVATION_UNRESOLVED"):
                    operation.commit_state = "REGISTRATION_FAILED_REQUIRES_AUDIT"
                try:
                    _native_require(_EvidenceRegistrationOperationV1._observe_accounting_v1(operation),
                                    "LP03_EXECUTION_ACCOUNTING_UNPROVEN")
                except BaseException:
                    operation.commit_state = "REGISTRATION_CLOCK_CUSTODY_UNAVAILABLE"
                    raise
                raise
            finally:
                state.operation = None

    def issue_evidence_attempt_v1(self, request, *, issuer_context):
        """Post-lock original admission; no grant is returned before native readback."""
        from contextlib import ExitStack
        from ..stage1_prediction_markets.qku_computation_control_plane.context import _native_require
        from ..stage1_prediction_markets.qku_computation_control_plane.models import EvidenceAttemptRequestV1, EvidenceMessageKindV1
        from ..stage1_prediction_markets.qku_computation_control_plane.persistence import _EvidenceAttemptOperationV1, _EvidenceRegistrationOperationV1
        from ..stage1_prediction_markets.qku_computation_control_plane.sqlite_reference import SQLiteReferenceAdapterV1
        from ..stage1_prediction_markets.qku_computation_control_plane.latency_policy import _EvidenceLocalClockV1
        _native_require(type(request) is EvidenceAttemptRequestV1 and type(issuer_context) is EvidenceIssuerContextV1,
                        "LP03_ATTEMPT_ORIGINAL_CONTEXT")
        state = EvidenceIssuerContextV1._identity_for_owner_v1(issuer_context, self)
        matches = tuple(operation for operation in state.registrations.values() if operation.binding_record is not None
                        and operation.binding_record.record_id == request.registration_binding_ref.record_id)
        _native_require(len(matches) == 1, "LP03_ATTEMPT_ORIGINAL_BINDING_JOIN")
        operation = matches[0]
        key = (request.lane, request.attempt_ordinal)
        attempt = operation.attempts.get(key)
        replay = attempt is not None
        if not replay:
            attempt = _EvidenceAttemptOperationV1(operation, request)
        with state.lock, ExitStack() as locks:
            _native_require(state.operation is None and operation.active_attempt is None, "LP03_CONTROL_OPERATION_REENTRY")
            _native_require(operation.attempts.get(key) is attempt and attempt.request == request
                            and (not replay or (attempt.phase == "COMMITTED_AND_READBACK" and attempt.handle is not None)),
                            "LP03_ATTEMPT_ALREADY_RESERVED_OR_UNRESOLVED")
            state.operation, operation.active_attempt = operation, attempt
            try:
                state._lock_original_source_custodies_v1(locks)
                _EvidenceRegistrationOperationV1._check_current_v1(operation)
                if replay:
                    SQLiteReferenceAdapterV1._evidence_read_attempt_members_v1(state.control_store, attempt)
                else:
                    SQLiteReferenceAdapterV1._evidence_issue_attempt_v1(state.control_store, attempt)
                _native_require(attempt.commit_observation is not None and attempt.readback_observation is not None,
                                "LP03_ATTEMPT_COMMIT_READBACK_UNRESOLVED")
                _message, payload = EvidenceHostBindingV1._verify_message_v1(state.host, attempt.grant_record.signed_grant,
                    expected_kind=EvidenceMessageKindV1.ATTEMPT_GRANT,
                    expected_issuer=state.host.public_configuration.service_principal,
                    expected_subject=attempt.grant_record.record_id, expected_audience=attempt.payload.service_principal,
                    expected_generation=state.generation)
                _native_require(payload == attempt.payload, "LP03_ATTEMPT_ORIGINAL_SIGNED_PAYLOAD_CHANGED")
                handle = attempt.handle
                if handle is None:
                    handle = object.__new__(EvidenceAttemptGrantV1)
                    handle._owner, handle._attempt, handle._grant_ref = state, attempt, attempt.grant_record.record_id
                _EvidenceRegistrationOperationV1._check_current_v1(operation)
                attempt.handle = handle
                return handle
            except BaseException:
                if attempt.phase not in ("ROLLED_BACK", "ROLLBACK_UNPROVEN", "COMMIT_OR_OBSERVATION_UNRESOLVED"):
                    attempt.phase = "ATTEMPT_FAILED_REQUIRES_AUDIT"
                try:
                    _native_require(_EvidenceRegistrationOperationV1._observe_accounting_v1(operation),
                                    "LP03_EXECUTION_ACCOUNTING_UNPROVEN")
                except BaseException:
                    attempt.phase = "ATTEMPT_CLOCK_CUSTODY_UNAVAILABLE"
                    raise
                raise
            finally:
                operation.active_attempt, state.operation = None, None

    def resolve_evidence_attempt_v1(self, grant, *, purpose, requester_context):
        from ..service.pr169_svc1_resolvers import EvidenceProcessSupervisorV1
        from ..stage1_prediction_markets.qku_computation_control_plane.context import _native_require
        _native_require(type(grant) is EvidenceAttemptGrantV1 and type(requester_context) is EvidenceProcessSupervisorV1
                        and purpose == "EVIDENCE_LANE_EXECUTION_V1", "LP03_ATTEMPT_REQUESTER_PURPOSE_REQUIRED")
        EvidenceProcessSupervisorV1._assert_original_v1(requester_context)
        state, attempt = grant._owner, grant._attempt
        _native_require(state.service is self and requester_context is state.supervisor and attempt.supervisor is requester_context
                        and attempt.handle is grant and grant._grant_ref == attempt.grant_record.record_id,
                        "LP03_ORIGINAL_ATTEMPT_GRANT_UNAVAILABLE")
        return AgentOrchService.issue_evidence_attempt_v1(self, attempt.request, issuer_context=state.context)

    def _append_evidence_process_observation_v1(self, grant, *, requester_context, native, stage):
        """Original SVC observations enter CONTROL only through its issuer."""
        from ..service.pr169_svc1_resolvers import EvidenceProcessSupervisorV1
        from ..stage1_prediction_markets.qku_computation_control_plane.context import _native_require
        from ..stage1_prediction_markets.qku_computation_control_plane.persistence import (
            _EvidenceAttemptObservationAppendV1, _EvidenceRegistrationOperationV1)
        from ..stage1_prediction_markets.qku_computation_control_plane.sqlite_reference import SQLiteReferenceAdapterV1
        from ..stage1_prediction_markets.qku_computation_control_plane.serialization import deterministic_json
        _native_require(type(grant) is EvidenceAttemptGrantV1 and type(requester_context) is EvidenceProcessSupervisorV1,
                        "LP03_PROCESS_APPEND_ORIGINAL_REQUESTER")
        state, attempt = grant._owner, grant._attempt
        _native_require(state.service is self and requester_context is state.supervisor and attempt.handle is grant
                        and native.original[1] is attempt and native.original[5] is grant,
                        "LP03_PROCESS_APPEND_ORIGINAL_ATTEMPT")
        with EvidenceProcessSupervisorV1._operation_v1(requester_context, attempt):
            existing = tuple(entry for entry in attempt.observation_appends if entry.stage == stage)
            if existing:
                append = existing[0]
                _native_require(append.phase == "COMMITTED_AND_READBACK" and append.native is native,
                                "LP03_PROCESS_APPEND_UNRESOLVED")
                SQLiteReferenceAdapterV1._evidence_read_process_append_v1(state.control_store, append)
            else:
                append = _EvidenceAttemptObservationAppendV1(attempt, native, stage)
                SQLiteReferenceAdapterV1._evidence_append_process_observation_v1(state.control_store, append)
            _EvidenceAttemptObservationAppendV1._assert_original_v1(append)
            proposed_original = (append.record, deterministic_json(append.record)) if append.record is not None else None
            _EvidenceRegistrationOperationV1._check_current_v1(attempt.registration)
            _EvidenceAttemptObservationAppendV1._assert_original_v1(append, canonical=False)
            _native_require(append.phase == "COMMITTED_AND_READBACK" and append.commit_observation is not None
                            and append.readback_observation is not None, "LP03_PROCESS_APPEND_COMMIT_READBACK_UNRESOLVED")
            if proposed_original is not None:
                _native_require(attempt.current_state is append.predecessor or attempt.current_state is append.record,
                                "LP03_PROCESS_APPEND_PREDECESSOR_CHANGED")
                attempt.current_state, attempt.current_state_original = append.record, proposed_original
            if stage == "TERMINAL":
                # Physical completion alone cannot finish collection or release
                # the original reservation before the atomic lane result.
                attempt.phase = "NATIVE_TERMINAL_PENDING_LANE_FINALIZATION"
            return append

    def _audit_evidence_attempt_failure_v1(self, grant, *, requester_context, native, reason, original_error,
            trigger_original, trigger_roster):
        """Original attempt integrity only; no source read or grant renewal."""
        from ..service.pr169_svc1_resolvers import EvidenceProcessSupervisorV1, _WindowsEvidenceProcessV1
        from ..stage1_prediction_markets.qku_computation_control_plane.context import _native_require
        from ..stage1_prediction_markets.qku_computation_control_plane.persistence import (
            _EvidenceAttemptFailureAuditV1, _EvidenceRegistrationOperationV1, _EvidenceAttemptOperationV1)
        from ..stage1_prediction_markets.qku_computation_control_plane.latency_policy import _EvidenceLocalClockV1
        from ..stage1_prediction_markets.qku_computation_control_plane.sqlite_reference import SQLiteReferenceAdapterV1
        _native_require(type(grant) is EvidenceAttemptGrantV1 and type(requester_context) is EvidenceProcessSupervisorV1
                        and type(native) is _WindowsEvidenceProcessV1, "LP03_FAILURE_AUDIT_ORIGINAL_REQUESTER")
        issuer, attempt = grant._owner, grant._attempt
        _native_require(issuer.service is self and issuer.supervisor is requester_context and attempt.handle is grant
                        and native.original[1] is attempt and native.original[5] is grant,
                        "LP03_FAILURE_AUDIT_ORIGINAL_ATTEMPT")
        if attempt.failure_audit is not None:
            return attempt.failure_audit
        audit = _EvidenceAttemptFailureAuditV1(attempt, native, failure_reason=reason, original_error=original_error,
            trigger_original=trigger_original, trigger_roster=trigger_roster)
        locked = False
        try:
            now = _EvidenceLocalClockV1.observe_v1(issuer.clock)
            remaining = min(attempt.failure_bounds[2], audit.started[1] + attempt.limits.reserved_failure_wall_ns) - now[1]
            locked = remaining > 0 and issuer.lock.acquire(timeout=remaining / 1_000_000_000)
            _native_require(locked, "LP03_FAILURE_AUDIT_ENTRY_LOCK_UNAVAILABLE")
            _native_require(issuer.operation is None and attempt.registration.active_attempt is None
                            and attempt.registration.active_lane_operation is None, "LP03_FAILURE_AUDIT_POSITIVE_SCOPE_ACTIVE")
            issuer.operation = audit
            _EvidenceAttemptFailureAuditV1._check_current_v1(audit)
            _EvidenceAttemptOperationV1._assert_original_members_v1(attempt, canonical=True)
            _EvidenceAttemptFailureAuditV1._prepare_v1(audit)
            SQLiteReferenceAdapterV1._evidence_commit_failure_audit_v1(issuer.control_store, audit)
            return _EvidenceAttemptFailureAuditV1._finish_v1(audit)
        except BaseException:
            try:
                audit.entry_failure_observation = _EvidenceLocalClockV1.observe_v1(issuer.clock)
            except BaseException:
                pass  # The already-retained entry remains unobserved and unusable.
            raise
        finally:
            if locked:
                try:
                    if audit.phase not in ("COMPLETED_RESERVED", "COMMITTED_QUARANTINED"):
                        _EvidenceRegistrationOperationV1._observe_accounting_v1(attempt.registration)
                finally:
                    if issuer.operation is audit:
                        issuer.operation = None
                    issuer.lock.release()

    def _build_evidence_ready_conformance_v1(self, *, service, experiment_ref, issuer_context):
        from contextlib import ExitStack
        from ..stage1_prediction_markets.qku_computation_control_plane.context import _native_require
        from ..stage1_prediction_markets.qku_computation_control_plane.models import EvidenceRecordRefV1
        from ..stage1_prediction_markets.qku_computation_control_plane.evidence import ComputationEvidenceServiceV1
        from ..stage1_prediction_markets.qku_computation_control_plane.persistence import _EvidenceConformanceOperationV1, _EvidenceRegistrationOperationV1
        from ..stage1_prediction_markets.qku_computation_control_plane.sqlite_reference import SQLiteReferenceAdapterV1
        state = EvidenceIssuerContextV1._identity_for_owner_v1(issuer_context, self)
        ComputationEvidenceServiceV1._assert_measured_binding_v1(service)
        _native_require(type(experiment_ref) is EvidenceRecordRefV1 and service._measured_original[0] is state
                        and experiment_ref.store_id == state.control_store._evidence_store_binding_v1.binding.store_id,
                        "LP03_CONFORMANCE_ORIGINAL_EXPERIMENT_REQUIRED")
        selected = tuple(registration for registration in state.registrations.values()
                         if registration.binding_record is not None and registration.binding_record.record_id == experiment_ref.record_id)
        _native_require(len(selected) == 1, "LP03_CONFORMANCE_ORIGINAL_EXPERIMENT_REQUIRED")
        registration = selected[0]
        operation = registration.conformance_operation
        replay = operation is not None
        if not replay:
            operation = _EvidenceConformanceOperationV1(service=service, registration=registration)
        with state.lock, ExitStack() as locks:
            _native_require(state.operation is None and operation.service is service
                            and (not replay or operation.phase == "COMMITTED_AND_READBACK"),
                            "LP03_CONFORMANCE_ALREADY_RESERVED_OR_UNRESOLVED")
            state.operation = registration
            try:
                state._lock_original_source_custodies_v1(locks)
                _EvidenceConformanceOperationV1._check_current_v1(operation)
                if replay:
                    SQLiteReferenceAdapterV1._evidence_read_conformance_v1(state.control_store, operation, parents=False)
                else:
                    SQLiteReferenceAdapterV1._evidence_read_conformance_v1(state.control_store, operation, parents=True)
                    SQLiteReferenceAdapterV1._evidence_commit_conformance_v1(state.control_store, operation)
                _EvidenceConformanceOperationV1._check_current_v1(operation)
                return operation.record
            except BaseException:
                _EvidenceRegistrationOperationV1._observe_accounting_v1(registration)
                raise
            finally:
                state.operation = None

    def bind_evidence_receiver_v1(self, *, parent_resolver, host_binding, persistence_adapter):
        from ..stage1_prediction_markets.qku_computation_control_plane.persistence import _EvidenceReceiverContextV1
        return _EvidenceReceiverContextV1._bind_v1(owner_service=self, receiving_owner="AGENT_ORCH1",
            parent_resolver=parent_resolver, host_binding=host_binding, persistence_adapter=persistence_adapter)

    def receive_evidence_delivery_v1(self, delivery_ref, *, receiver_context):
        from ..stage1_prediction_markets.qku_computation_control_plane.persistence import _EvidenceReceiverContextV1
        return _EvidenceReceiverContextV1._receive_v1(receiver_context, delivery_ref, owner_service=self)

    def _build_reviewed_evidence_conformance_v1(self, *, service, candidate_ref, review_ref, issuer_context):
        from contextlib import ExitStack
        from ..stage1_prediction_markets.qku_computation_control_plane.context import _native_require
        from ..stage1_prediction_markets.qku_computation_control_plane.models import EvidenceRecordRefV1
        from ..stage1_prediction_markets.qku_computation_control_plane.evidence import ComputationEvidenceServiceV1
        from ..stage1_prediction_markets.qku_computation_control_plane.persistence import (
            _EvidenceReviewedConformanceOperationV1, _EvidenceRegistrationOperationV1)
        from ..stage1_prediction_markets.qku_computation_control_plane.sqlite_reference import SQLiteReferenceAdapterV1
        state = EvidenceIssuerContextV1._identity_for_owner_v1(issuer_context, self)
        ComputationEvidenceServiceV1._assert_measured_binding_v1(service)
        _native_require(service._measured_original[0] is state and type(candidate_ref) is type(review_ref) is EvidenceRecordRefV1
                        and candidate_ref.store_id == state.control_store._evidence_store_binding_v1.binding.store_id,
                        "LP03_REVIEWED_CONFORMANCE_ORIGINAL_REFERENCES_REQUIRED")
        parents = tuple(registration.conformance_operation for registration in state.registrations.values()
            if registration.conformance_operation is not None and registration.conformance_operation.record is not None
            and registration.conformance_operation.record.record_id == candidate_ref.record_id)
        _native_require(len(parents) == 1, "LP03_REVIEWED_CONFORMANCE_ORIGINAL_CANDIDATE_REQUIRED")
        parent, review = parents[0], parents[0].registration.review_operation
        _native_require(review is not None and review.record is not None and review.record.record_id == review_ref.record_id
                        and review_ref.store_id == review.store._evidence_store_binding_v1.binding.store_id,
                        "LP03_REVIEWED_CONFORMANCE_ORIGINAL_REVIEW_REQUIRED")
        registration = parent.registration
        operation = registration.reviewed_conformance_operation
        replay = operation is not None
        if not replay:
            operation = _EvidenceReviewedConformanceOperationV1(service=service, parent=parent, review=review)
        with state.lock, ExitStack() as locks:
            _native_require(state.operation is None and operation.service is service
                            and (not replay or operation.phase == "COMMITTED_AND_READBACK"),
                            "LP03_REVIEWED_CONFORMANCE_ALREADY_RESERVED_OR_UNRESOLVED")
            state.operation = registration
            try:
                state._lock_original_source_custodies_v1(locks)
                _EvidenceReviewedConformanceOperationV1._check_current_v1(operation)
                if replay:
                    SQLiteReferenceAdapterV1._evidence_read_measured_rows_v1(state.control_store, operation, stage="SUCCESSOR")
                else:
                    SQLiteReferenceAdapterV1._evidence_read_measured_rows_v1(state.control_store, operation, stage="PARENTS")
                    SQLiteReferenceAdapterV1._evidence_commit_measured_rows_v1(state.control_store, operation, stage="SUCCESSOR")
                _EvidenceReviewedConformanceOperationV1._check_current_v1(operation)
                return operation.record
            except BaseException:
                _EvidenceRegistrationOperationV1._observe_accounting_v1(registration)
                raise
            finally:
                state.operation = None

    def _issue_evidence_delivery_v1(self, *, service, candidate_ref, receiver_context, issuer_context):
        from ..stage1_prediction_markets.qku_computation_control_plane.context import _native_require
        from ..stage1_prediction_markets.qku_computation_control_plane.models import EvidenceRecordRefV1
        from ..stage1_prediction_markets.qku_computation_control_plane.evidence import ComputationEvidenceServiceV1
        from ..stage1_prediction_markets.qku_computation_control_plane.persistence import (
            _EvidenceReceiverContextV1, _EvidenceReceiverOperationV1, _EvidenceRegistrationOperationV1)
        from ..stage1_prediction_markets.qku_computation_control_plane.sqlite_reference import SQLiteReferenceAdapterV1
        state = EvidenceIssuerContextV1._identity_for_owner_v1(issuer_context, self)
        ComputationEvidenceServiceV1._assert_measured_binding_v1(service)
        _EvidenceReceiverContextV1._assert_original_v1(receiver_context)
        _native_require(service._measured_original[0] is state and receiver_context._original[0] is state
                        and receiver_context._original[2] is service and type(candidate_ref) is EvidenceRecordRefV1
                        and candidate_ref.store_id == state.control_store._evidence_store_binding_v1.binding.store_id,
                        "LP03_DELIVERY_ORIGINAL_BUILDER_AND_RECEIVER_REQUIRED")
        parents = tuple(registration.reviewed_conformance_operation for registration in state.registrations.values()
            if registration.reviewed_conformance_operation is not None and registration.reviewed_conformance_operation.record is not None
            and registration.reviewed_conformance_operation.record.record_id == candidate_ref.record_id)
        _native_require(len(parents) == 1, "LP03_DELIVERY_ORIGINAL_R1_REQUIRED")
        parent = parents[0]
        _EvidenceRegistrationOperationV1._retained_capacity_v1(parent.registration)
        operation = parent.registration.receiver_operations.get(receiver_context._original[5])
        if operation is None:
            operation = _EvidenceReceiverOperationV1(context=receiver_context, parent=parent)
        else:
            _native_require(type(operation) is _EvidenceReceiverOperationV1 and operation.context is receiver_context
                            and operation.parent is parent and operation.phase in ("ADMITTED_AND_READBACK", "COMMITTED_AND_READBACK"),
                            "LP03_RECEIVER_ALREADY_RESERVED_OR_UNRESOLVED")
        with _EvidenceReceiverOperationV1._scope_v1(operation):
            if operation.phase == "ADMISSION_PENDING":
                SQLiteReferenceAdapterV1._evidence_commit_measured_rows_v1(state.control_store, operation, stage="ADMISSION")
            _EvidenceReceiverOperationV1._check_current_v1(operation)
            return EvidenceRecordRefV1(state.control_store._evidence_store_binding_v1.binding.store_id, operation.delivery_id)

    def _close_evidence_conformance_v1(self, *, service, candidate_ref, receiver_ack_refs, issuer_context):
        from contextlib import ExitStack
        from ..stage1_prediction_markets.qku_computation_control_plane.context import _native_require
        from ..stage1_prediction_markets.qku_computation_control_plane.models import EvidenceRecordRefV1
        from ..stage1_prediction_markets.qku_computation_control_plane.evidence import ComputationEvidenceServiceV1
        from ..stage1_prediction_markets.qku_computation_control_plane.persistence import (
            _EvidenceClosedConformanceOperationV1, _EvidenceRegistrationOperationV1)
        from ..stage1_prediction_markets.qku_computation_control_plane.sqlite_reference import SQLiteReferenceAdapterV1
        state = EvidenceIssuerContextV1._identity_for_owner_v1(issuer_context, self)
        ComputationEvidenceServiceV1._assert_measured_binding_v1(service)
        _native_require(service._measured_original[0] is state and type(candidate_ref) is EvidenceRecordRefV1
                        and candidate_ref.store_id == state.control_store._evidence_store_binding_v1.binding.store_id
                        and type(receiver_ack_refs) is tuple and len(receiver_ack_refs) == 4
                        and all(type(ref) is EvidenceRecordRefV1 for ref in receiver_ack_refs)
                        and len(set(receiver_ack_refs)) == 4, "LP03_CLOSEOUT_EXACT_ACK_REFERENCES_REQUIRED")
        parents = tuple(registration.reviewed_conformance_operation for registration in state.registrations.values()
            if registration.reviewed_conformance_operation is not None and registration.reviewed_conformance_operation.record is not None
            and registration.reviewed_conformance_operation.record.record_id == candidate_ref.record_id)
        _native_require(len(parents) == 1, "LP03_CLOSEOUT_ORIGINAL_R1_REQUIRED")
        parent, registration = parents[0], parents[0].registration
        _EvidenceRegistrationOperationV1._retained_capacity_v1(registration)
        required = registration.protocol.review_ack_policy["required_receiver_ids"]
        _native_require(set(registration.receiver_operations) == set(required), "LP03_CLOSEOUT_ALL_RECEIVERS_REQUIRED")
        receivers = tuple(registration.receiver_operations[name] for name in required)
        _native_require(all(receiver.phase == "COMMITTED_AND_READBACK" and receiver.record is not None
            and ref.store_id == receiver.store._evidence_store_binding_v1.binding.store_id
            and ref.record_id == receiver.record.record_id and receiver.record.state == "ACCEPTED"
            for ref, receiver in zip(receiver_ack_refs, receivers)), "LP03_CLOSEOUT_EXACT_ORIGINAL_ACCEPTED_ACKS_REQUIRED")
        operation = registration.closed_conformance_operation
        replay = operation is not None
        if not replay:
            operation = _EvidenceClosedConformanceOperationV1(service=service, parent=parent, receivers=receivers)
        with state.lock, ExitStack() as locks:
            _native_require(state.operation is None and operation.service is service and operation.parent is parent
                            and (not replay or operation.phase == "COMMITTED_AND_READBACK"),
                            "LP03_CLOSEOUT_ALREADY_RESERVED_OR_UNRESOLVED")
            state.operation = registration
            try:
                state._lock_original_source_custodies_v1(locks)
                _EvidenceClosedConformanceOperationV1._check_current_v1(operation)
                if replay:
                    SQLiteReferenceAdapterV1._evidence_read_measured_rows_v1(state.control_store, operation, stage="CLOSEOUT")
                else:
                    SQLiteReferenceAdapterV1._evidence_read_measured_rows_v1(state.control_store, operation, stage="PARENTS")
                    SQLiteReferenceAdapterV1._evidence_commit_measured_rows_v1(state.control_store, operation, stage="CLOSEOUT")
                _EvidenceClosedConformanceOperationV1._check_current_v1(operation)
                return operation.record
            except BaseException:
                _EvidenceRegistrationOperationV1._observe_accounting_v1(registration)
                raise
            finally:
                state.operation = None

    def _admit_evidence_review_v1(self, *, reviewer, candidate_ref):
        from ..stage1_prediction_markets.qku_computation_control_plane.context import _native_require
        from ..stage1_prediction_markets.qku_computation_control_plane.models import EvidenceRecordRefV1
        from ..stage1_prediction_markets.qku_computation_control_plane.evidence import IndependentEvidenceReviewV1
        from ..stage1_prediction_markets.qku_computation_control_plane.persistence import _EvidenceReviewOperationV1
        from ..stage1_prediction_markets.qku_computation_control_plane.sqlite_reference import SQLiteReferenceAdapterV1
        IndependentEvidenceReviewV1._assert_measured_binding_v1(reviewer)
        state = reviewer._measured_original[0]
        _native_require(state.service is self and getattr(self, "_evidence_issuer_state_v1", None) is state
                        and type(candidate_ref) is EvidenceRecordRefV1
                        and candidate_ref.store_id == state.control_store._evidence_store_binding_v1.binding.store_id,
                        "LP03_REVIEW_ORIGINAL_ISSUER_AND_CANDIDATE_REQUIRED")
        parents = tuple(registration.conformance_operation for registration in state.registrations.values()
            if registration.conformance_operation is not None and registration.conformance_operation.record is not None
            and registration.conformance_operation.record.record_id == candidate_ref.record_id)
        _native_require(len(parents) == 1, "LP03_REVIEW_ORIGINAL_CANDIDATE_REQUIRED")
        parent = parents[0]
        operation = parent.registration.review_operation
        if operation is None:
            operation = _EvidenceReviewOperationV1(reviewer=reviewer, parent=parent)
        else:
            _native_require(type(operation) is _EvidenceReviewOperationV1 and operation.parent is parent
                            and operation.reviewer is reviewer and operation.phase in (
                                "ADMITTED_AND_READBACK", "COMMITTED_AND_READBACK"),
                            "LP03_REVIEW_ALREADY_RESERVED_OR_UNRESOLVED")
        with _EvidenceReviewOperationV1._scope_v1(operation):
            if operation.phase == "ADMISSION_PENDING":
                SQLiteReferenceAdapterV1._evidence_commit_review_v1(state.control_store, operation, stage="ADMISSION")
            _EvidenceReviewOperationV1._check_current_v1(operation)
            return operation

    def _finalize_evidence_lane_v1(self, operation):
        """Only the original CONTROL issuer settles the selected published lane."""
        from ..stage1_prediction_markets.qku_computation_control_plane.context import _native_require
        from ..stage1_prediction_markets.qku_computation_control_plane.persistence import (
            _EvidenceLaneOperationV1, _EvidenceAttemptOperationV1, _EvidenceRegistrationOperationV1, EvidenceAvailabilityHandleV1)
        from ..stage1_prediction_markets.qku_computation_control_plane.sqlite_reference import SQLiteReferenceAdapterV1
        _native_require(type(operation) is _EvidenceLaneOperationV1 and operation.issuer.service is self
                        and getattr(self, "_evidence_issuer_state_v1", None) is operation.issuer
                        and operation.issuer.operation is operation.attempt.registration
                        and operation.attempt.registration.active_lane_operation is operation,
                        "LP03_FINALIZATION_ORIGINAL_ISSUER_SCOPE")
        _EvidenceLaneOperationV1._assert_original_v1(operation)
        SQLiteReferenceAdapterV1._evidence_finalize_lane_v1(operation.issuer.control_store, operation)
        _native_require(operation.finalization_phase == "COMMITTED_AND_READBACK"
                        and operation.final_commit_original is not None and operation.final_readback_original is not None,
                        "LP03_FINALIZATION_CUSTODY_UNRESOLVED")
        attempt = operation.attempt
        produced = attempt.published_kelly27
        if produced is not None:
            from ..stage1_prediction_markets.qku_computation_control_plane.input_resolver import _EvidencePublishedKelly27V1
            _EvidencePublishedKelly27V1._prepare_v1(produced, operation)
            produced_preparation = produced.prepared
        observed = EvidenceAvailabilityHandleV1._require_current_v1(operation.availability, operation=operation,
            purpose="EVIDENCE_LANE_REGISTRATION_V1", current_grant=attempt.handle, clock=operation.issuer.clock)
        _EvidenceRegistrationOperationV1._room_v1(attempt.registration, retained_attempt=attempt)
        actual = _EvidenceAttemptOperationV1._consumption_v1(attempt)
        _native_require(attempt.supervisor._active is operation.native, "LP03_LANE_ORIGINAL_ACTIVE_SLOT_CHANGED")
        if produced is not None:
            _native_require(attempt.published_kelly27 is produced and produced.prepared is produced_preparation,
                            "LP03_KELLY27_SOURCE_ORIGINAL_ROSTER_CHANGED")
            _EvidencePublishedKelly27V1._assert_original_v1(produced)
        proof = (operation, operation.final_state, operation.native, operation.native._terminal_original,
                 operation.final_readback_original, observed, actual)
        # No blocking work follows this final observed tail. The full original
        # reservation remains encumbered; only native active custody is released.
        attempt.current_state, attempt.current_state_original = operation.final_state, operation.final_state_original
        attempt.terminal_original = attempt.terminal_proof = proof
        if produced is not None:
            produced.completion = proof
        operation.finalization_phase = "COMPLETED_RESERVED"
        attempt.phase = "COLLECTION_COMPLETE_RESERVED"
        attempt.registration.retained_reservations = (*attempt.registration.retained_reservations,
            (attempt, attempt.limits, attempt.roster_original, proof))
        attempt.supervisor._active = None
        return operation.lane_registration

    def _jsonl(self, file_name: str) -> tuple[dict[str, Any], ...]:
        if file_name not in JSONL_FILES:
            raise KeyError(file_name)
        if file_name not in self._jsonl_cache:
            self._jsonl_cache[file_name] = _read_jsonl(
                self.artifact_dir / file_name
            )
        return tuple(dict(row) for row in self._jsonl_cache[file_name])

    def load_manifest(self) -> dict[str, Any]:
        if self._manifest_cache is None:
            value = json.loads(
                (self.artifact_dir / "manifest.json").read_text(
                    encoding="utf-8"
                )
            )
            if not isinstance(value, dict):
                raise TypeError("AGENT-ORCH1 manifest must be an object")
            self._manifest_cache = value
        return dict(self._manifest_cache)

    def _report_rows(self, relative_path: Path) -> tuple[dict[str, Any], ...]:
        if relative_path not in PR165_POLICY_REPORTS:
            raise KeyError(str(relative_path))
        if relative_path not in self._report_cache:
            value = json.loads(
                (self.repo_root / relative_path).read_text(encoding="utf-8")
            )
            if not isinstance(value, dict) or not isinstance(
                value.get("records"), list
            ):
                raise TypeError(f"{relative_path} must own a records array")
            rows = tuple(
                row for row in value["records"] if isinstance(row, dict)
            )
            if len(rows) != len(value["records"]):
                raise TypeError(f"{relative_path} contains a non-object row")
            self._report_cache[relative_path] = rows
        return tuple(dict(row) for row in self._report_cache[relative_path])

    def load_policy_snapshot(self) -> AgentOrchPolicySnapshotV1:
        """Load and freeze only the exact E admission views once."""

        if self._policy_snapshot_cache is None:
            selected = {
                file_name: tuple(
                    _freeze(row) for row in self._jsonl(file_name)
                )
                for file_name in POLICY_JSONL_FILES
            }
            self._policy_snapshot_cache = AgentOrchPolicySnapshotV1(
                manifest=_freeze(self.load_manifest()),
                role_rows=selected["role_map.jsonl"],
                duty_rows=selected["duty_map.jsonl"],
                permission_rows=selected["perm_scope.jsonl"],
                task_envelope_rows=selected["task_env.jsonl"],
                capability_route_rows=selected["capability_routes.jsonl"],
                decision_receipt_rows=selected["decision_receipts.jsonl"],
                pr165_roster_rows=tuple(
                    _freeze(row)
                    for row in self._report_rows(PR165_POLICY_REPORTS[0])
                ),
                pr165_duty_source_rows=tuple(
                    _freeze(row)
                    for row in self._report_rows(PR165_POLICY_REPORTS[1])
                ),
            )
        return self._policy_snapshot_cache

    def list_dags(self) -> tuple[dict[str, Any], ...]:
        return self._jsonl("dag.jsonl")

    def get_dag(self, dag_id: str) -> dict[str, Any]:
        return _first(self.list_dags(), "dag_id", dag_id)

    def list_nodes(self, dag_id: str | None = None) -> tuple[dict[str, Any], ...]:
        rows = self._jsonl("dag_nodes.jsonl")
        if dag_id is None:
            return rows
        return tuple(row for row in rows if row.get("dag_id") == dag_id)

    def list_edges(self, dag_id: str | None = None) -> tuple[dict[str, Any], ...]:
        rows = self._jsonl("dag_edges.jsonl")
        if dag_id is None:
            return rows
        return tuple(row for row in rows if row.get("dag_id") == dag_id)

    def list_tasks(self, queue_id: str | None = None, task_class: str | None = None) -> tuple[dict[str, Any], ...]:
        rows = self._jsonl("task_queue.jsonl")
        if queue_id is not None:
            rows = tuple(row for row in rows if row.get("queue_id") == queue_id)
        if task_class is not None:
            rows = tuple(row for row in rows if row.get("task_class") == task_class)
        return rows

    def get_task(self, task_id: str) -> dict[str, Any]:
        for file_name in ("task_queue.jsonl", "task_registry.jsonl"):
            for row in self._jsonl(file_name):
                if row.get("task_id") == task_id or row.get("task_ref") == task_id:
                    return dict(row)
        raise KeyError(task_id)

    def list_task_envelopes(self) -> tuple[dict[str, Any], ...]:
        return self._jsonl("task_env.jsonl")

    def get_task_envelope(self, task_id: str) -> dict[str, Any]:
        for row in self.list_task_envelopes():
            if row.get("task_id") == task_id or row.get("task_ref") == task_id:
                return dict(row)
        raise KeyError(task_id)

    def list_workflows(self) -> tuple[dict[str, Any], ...]:
        return self._jsonl("workflows.jsonl")

    def get_workflow(self, workflow_id: str) -> dict[str, Any]:
        return _first(self.list_workflows(), "workflow_id", workflow_id)

    def list_task_receipts(self) -> tuple[dict[str, Any], ...]:
        return self._jsonl("task_receipts.jsonl")

    def get_task_receipt(self, receipt_id: str) -> dict[str, Any]:
        for row in self.list_task_receipts():
            if row.get("receipt_ref_or_gap") == receipt_id or row.get("task_id") == receipt_id:
                return dict(row)
        raise KeyError(receipt_id)

    def list_decision_receipts(self) -> tuple[dict[str, Any], ...]:
        return self._jsonl("decision_receipts.jsonl")

    def list_dispute_receipts(self) -> tuple[dict[str, Any], ...]:
        return self._jsonl("dispute_receipts.jsonl")

    def list_escalation_receipts(self) -> tuple[dict[str, Any], ...]:
        return self._jsonl("escalation_receipts.jsonl")

    def get_owner_request_tasks(self, owner_action_ref: str) -> tuple[dict[str, Any], ...]:
        return tuple(
            row
            for row in self._jsonl("owner_cmd_tasks.jsonl")
            if row.get("owner_action_ref_or_gap") == owner_action_ref
        )

    def get_qku_tasks(self, candidate_id: str) -> tuple[dict[str, Any], ...]:
        return self._candidate_rows("qku_tasks.jsonl", candidate_id)

    def get_formula_tasks(self, candidate_id: str) -> tuple[dict[str, Any], ...]:
        return self._candidate_rows("formula_tasks.jsonl", candidate_id)

    def get_no_trade_tasks(self, candidate_id: str) -> tuple[dict[str, Any], ...]:
        rows: list[dict[str, Any]] = []
        for file_name in (
            "notrade_tasks.jsonl",
            "var_tune_tasks.jsonl",
            "stack_tasks.jsonl",
            "venue_side_tasks.jsonl",
            "source_refresh_tasks.jsonl",
            "retest_tasks.jsonl",
        ):
            rows.extend(self._candidate_rows(file_name, candidate_id))
        return tuple(rows)

    def get_paper_prep(self, candidate_id: str) -> tuple[dict[str, Any], ...]:
        return self._candidate_rows("paper_prep.jsonl", candidate_id)

    def get_hotpath_prep(self, candidate_id: str) -> tuple[dict[str, Any], ...]:
        return self._candidate_rows("hotpath_prep.jsonl", candidate_id)

    def get_llm_tasks(self, candidate_id: str) -> tuple[dict[str, Any], ...]:
        rows = [
            row
            for row in self._jsonl("chat_tasks.jsonl") + self._jsonl("task_registry.jsonl")
            if _candidate_match(row, candidate_id) and row.get("llm_task_ref_or_gap")
        ]
        return tuple(rows)

    def get_quantum_tasks(self, candidate_id: str) -> tuple[dict[str, Any], ...]:
        return self._candidate_rows("quantum_tasks.jsonl", candidate_id)

    def get_downstream_routes(self, task_id: str) -> tuple[dict[str, Any], ...]:
        rows: list[dict[str, Any]] = []
        for file_name in ("downstream.jsonl", "value_routes.jsonl", "capability_routes.jsonl", "learning_routes.jsonl"):
            rows.extend(
                row
                for row in self._jsonl(file_name)
                if row.get("task_id") == task_id or row.get("task_ref") == task_id
            )
        if rows:
            return tuple(rows)
        task = self.get_task(task_id)
        return (
            {
                "task_id": task_id,
                "downstream_route_refs": tuple(task.get("downstream_route_refs") or ()),
                "authority_state": task.get("authority_state"),
                "runtime_side_effect_allowed": task.get("runtime_side_effect_allowed"),
            },
        )

    def _candidate_rows(self, file_name: str, candidate_id: str) -> tuple[dict[str, Any], ...]:
        return tuple(row for row in self._jsonl(file_name) if _candidate_match(row, candidate_id))


class AgentOrchAPI(AgentOrchService):
    pass


def resolve_st12g_projection_v2(
    resolution: "ST12GProjectionResolutionV2",
) -> "ST12GOwnerProjectionResolutionV2":
    """Select AGENT-ORCH1 without I/O, core copying, or recomputation."""

    from ..stage1_prediction_markets.qku_computation_control_plane import (
        existing_owner_projection as st12g,
    )
    from ..stage1_prediction_markets.qku_computation_control_plane.errors import (
        ContractValidationError,
        ReasonCode,
    )

    if type(resolution) is not st12g.ST12GProjectionResolutionV2:
        raise ContractValidationError(
            ReasonCode.INPUT_OWNER_MISMATCH,
            "AGENT-ORCH1 requires the exact central ST12-G resolution",
        )
    if (
        resolution.resolution_state
        is st12g.ST12GProjectionResolutionStateV2.CURRENT_READ_ONLY
    ):
        bundle = resolution.projection_bundle
        if type(bundle) is not st12g.ST12GProjectionBundleV2 or type(
            bundle.agent_orch
        ) is not st12g.ST12GAgentEvidenceHandoffV2:
            raise ContractValidationError(
                ReasonCode.SCHEMA_MISMATCH,
                "AGENT-ORCH1 projection is missing from the central bundle",
            )
        payload = bundle.agent_orch
    else:
        payload = resolution.absence
        if type(payload) is not st12g.ST12GProjectionAbsenceV2:
            raise ContractValidationError(
                ReasonCode.SCHEMA_MISMATCH,
                "AGENT-ORCH1 noncurrent resolution must preserve central absence",
            )
    return st12g.ST12GOwnerProjectionResolutionV2(
        consumer_id="AGENT_ORCH1",
        source_request_id=resolution.request_id,
        resolution_state=resolution.resolution_state,
        payload=payload,
    )


class _EvidenceRoleSigningCapabilityV1:
    """One role's native key, never a serializable or general signing interface."""

    __slots__ = ("__key", "__key_record", "__host", "__native_sign")

    def __init__(self, *, key, key_record, host) -> None:
        from ..stage1_prediction_markets.qku_computation_control_plane.context import _native_require
        from ..stage1_prediction_markets.qku_computation_control_plane.models import (
            EvidenceKeyPurposeV1, EvidenceOriginV1, EvidenceVerificationKeyV1,
        )

        _native_require(type(key_record) is EvidenceVerificationKeyV1
                        and key_record.origin is EvidenceOriginV1.SOFTWARE_CONFORMANCE
                        and key_record.purpose is not EvidenceKeyPurposeV1.OWNER_APPROVAL,
                        "LP03_ROLE_SIGNING_CUSTODY")
        try:
            # Pin the installed native implementation, not an arbitrary subclass
            # of the public abstract API with overridable sign/public_key methods.
            from cryptography.hazmat.bindings import _rust
            from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
            native_type = _rust.openssl.ed25519.Ed25519PrivateKey
            _native_require(type(key) is native_type, "LP03_NATIVE_ED25519_KEY_REQUIRED")
            public = native_type.public_key(key)
            raw = type(public).public_bytes(public, Encoding.Raw, PublicFormat.Raw)
        except (ImportError, AttributeError, ValueError, TypeError) as exc:
            from ..stage1_prediction_markets.qku_computation_control_plane.errors import ContractValidationError, ReasonCode
            raise ContractValidationError(ReasonCode.EVIDENCE_AUTHORITY_UNAVAILABLE, "EVIDENCE_AUTHORITY_UNAVAILABLE") from exc
        _native_require(raw.hex() == key_record.public_key_hex, "LP03_SIGNING_PUBLIC_KEY_MISMATCH")
        self.__key = key
        self.__key_record = key_record
        self.__host = host
        self.__native_sign = native_type.sign

    def __repr__(self) -> str:
        return "<LP03 role signing capability: nonexportable>"

    def __copy__(self):
        raise TypeError("LP03 signing capability cannot be copied")

    def __deepcopy__(self, memo):
        raise TypeError("LP03 signing capability cannot be copied")

    def __reduce_ex__(self, protocol):
        raise TypeError("LP03 signing capability cannot be serialized")

    def _sign_typed_v1(self, host, message):
        from ..stage1_prediction_markets.qku_computation_control_plane.context import _native_require
        from ..stage1_prediction_markets.qku_computation_control_plane.models import (
            EvidenceAuthorizationMessageV1, EvidenceSignedMessageV1,
        )
        from ..stage1_prediction_markets.qku_computation_control_plane.serialization import deterministic_json

        _native_require(type(host) is EvidenceHostBindingV1 and host is self.__host
                        and type(message) is EvidenceAuthorizationMessageV1, "LP03_SIGNING_OWNER")
        EvidenceHostBindingV1._assert_local_binding_v1(host)
        key = self.__key_record
        _native_require((message.key_id, message.key_purpose, message.issuer, message.origin, message.deployment_id)
                        == (key.key_id, key.purpose, key.principal, key.origin, key.deployment_id), "LP03_SIGNING_SCOPE")
        raw = deterministic_json(message).encode("utf-8")
        domain_message = b"QTT-LP03-EVIDENCE-AUTH-V1\0" + raw
        _native_require(len(domain_message) <= 65536, "LP03_SIGNING_BYTE_BOUND")
        signature = self.__native_sign(self.__key, domain_message)
        return EvidenceSignedMessageV1(raw.decode("utf-8"), signature.hex())


class EvidenceHostBindingV1:
    """Explicit private host binding; local composition is conformance-only.

    This authenticates selected message bytes, not original ledger/source
    currentness. Grant issuance/use must still acquire those original owners.
    No protected configuration or native role segregation is inferred here.
    """

    __slots__ = ("__configuration", "__signing", "__process_id", "__getpid", "__wall_ns",
                 "__nonce_bytes", "__lock", "__selected_key")

    def __init__(self):
        raise TypeError("use the explicit protected loader or software-conformance composition")

    @classmethod
    def load_protected_configuration_v1(cls, configuration):
        """Loader contract and dormant denial; enrollment is a later operation."""
        from ..stage1_prediction_markets.qku_computation_control_plane.context import _native_require
        from ..stage1_prediction_markets.qku_computation_control_plane.models import EvidenceHostPublicConfigurationV1
        from ..stage1_prediction_markets.qku_computation_control_plane.errors import AuthorityDeniedError, ReasonCode

        _native_require(configuration is None or type(configuration) is EvidenceHostPublicConfigurationV1,
                        "LP03_PROTECTED_HOST_CONFIGURATION_TYPE")
        if configuration is not None:
            EvidenceHostPublicConfigurationV1.__post_init__(configuration)
        # A configuration reference alone cannot demonstrate the separately
        # required protected key loader/native qualification. No effects occur.
        raise AuthorityDeniedError(ReasonCode.EVIDENCE_AUTHORITY_UNAVAILABLE, "EVIDENCE_AUTHORITY_UNAVAILABLE")

    @classmethod
    def for_software_conformance_v1(cls, configuration, *, role_signing_key):
        from os import getpid, urandom
        from time import time_ns
        from _thread import RLock
        from types import BuiltinFunctionType
        from ..stage1_prediction_markets.qku_computation_control_plane.context import _native_require
        from ..stage1_prediction_markets.qku_computation_control_plane.models import (
            EvidenceHostPublicConfigurationV1, EvidenceOriginV1,
        )

        _native_require(cls is EvidenceHostBindingV1 and type(configuration) is EvidenceHostPublicConfigurationV1,
                        "LP03_HOST_BINDING_TYPE")
        EvidenceHostPublicConfigurationV1.__post_init__(configuration)
        _native_require(configuration.origin is EvidenceOriginV1.SOFTWARE_CONFORMANCE,
                        "LP03_SYNTHETIC_KEYS_NOT_OBSERVED_AUTHORITY")
        _native_require(all(type(fn) is BuiltinFunctionType for fn in (getpid, urandom, time_ns)),
                        "LP03_NATIVE_HOST_OBSERVATIONS_REQUIRED")
        selected = next(item for item in configuration.verification_keys if item.key_id == configuration.signing_key_id)
        result = object.__new__(cls)
        result.__configuration = configuration
        result.__process_id = getpid()
        result.__getpid = getpid
        result.__wall_ns = time_ns
        result.__nonce_bytes = urandom
        result.__lock = RLock()
        result.__selected_key = selected
        result.__signing = _EvidenceRoleSigningCapabilityV1(key=role_signing_key, key_record=selected, host=result)
        return result

    @property
    def public_configuration(self):
        return self.__configuration

    @property
    def signing_purpose(self):
        return self.__selected_key.purpose

    @property
    def native_segregation_qualified(self) -> bool:
        return False

    def __repr__(self) -> str:
        return "<LP03 software-conformance host binding: native segregation unqualified>"

    def __copy__(self):
        raise TypeError("LP03 host binding cannot be copied")

    def __deepcopy__(self, memo):
        raise TypeError("LP03 host binding cannot be copied")

    def __reduce_ex__(self, protocol):
        raise TypeError("LP03 host binding cannot be serialized")

    def _assert_local_binding_v1(self) -> None:
        from ..stage1_prediction_markets.qku_computation_control_plane.context import _native_require

        _native_require(type(self) is EvidenceHostBindingV1 and self.__getpid() == self.__process_id
                        and type(self.__signing) is _EvidenceRoleSigningCapabilityV1,
                        "LP03_HOST_PROCESS_CUSTODY")

    def _nonce_ref_v1(self, prefix):
        from ..stage1_prediction_markets.qku_computation_control_plane.context import _native_ident
        EvidenceHostBindingV1._assert_local_binding_v1(self)
        _native_ident(prefix)
        result = prefix + "::" + self.__nonce_bytes(16).hex()
        _native_ident(result)
        return result

    def _sign_message_v1(self, *, kind, subject, audience, generation, valid_from_wall_ns,
                         exclusive_expiry_wall_ns, payload):
        from ..stage1_prediction_markets.qku_computation_control_plane.context import _native_require
        from ..stage1_prediction_markets.qku_computation_control_plane.models import (
            EvidenceAbsenceV1, EvidenceAuthorizationMessageV1, EvidenceMessageKindV1,
            _EVIDENCE_MESSAGE_PURPOSE_V1,
        )

        EvidenceHostBindingV1._assert_local_binding_v1(self)
        key = self.__selected_key
        cfg = self.__configuration
        _native_require(type(kind) is EvidenceMessageKindV1 and _EVIDENCE_MESSAGE_PURPOSE_V1[kind] is key.purpose,
                        "LP03_SIGNING_KIND_PURPOSE")
        _native_require(type(generation) is int and generation == cfg.generation, "LP03_SIGNING_GENERATION")
        message = EvidenceAuthorizationMessageV1(
            kind=kind, schema_version="1.0", key_purpose=key.purpose, key_id=key.key_id,
            issuer=cfg.service_principal, subject=subject, audience=audience,
            deployment_id=cfg.deployment_id, origin=cfg.origin, generation=generation,
            nonce=self.__nonce_bytes(32).hex(), valid_from_wall_ns=valid_from_wall_ns,
            exclusive_expiry_wall_ns=exclusive_expiry_wall_ns, payload=payload,
        )
        with self.__lock:
            EvidenceHostBindingV1._assert_local_binding_v1(self)
            now = self.__wall_ns()
            _native_require(type(key.revocation_record_ref_or_absence) is EvidenceAbsenceV1
                            and key.valid_from_wall_ns <= message.valid_from_wall_ns <= now
                            < message.exclusive_expiry_wall_ns <= key.exclusive_expiry_wall_ns,
                            "LP03_SIGNING_VALIDITY")
            return _EvidenceRoleSigningCapabilityV1._sign_typed_v1(self.__signing, self, message)

    def _verify_cold_historical_message_v1(
        self, signed, *, archive, kind, issuer, subject, audience, generation, original_wall_ns,
    ):
        """Verify original signed bytes for old CONTROL evidence without granting current use."""
        from ..stage1_prediction_markets.qku_computation_control_plane.context import (
            _native_ident, _native_require, _public_counter_v1,
        )
        from ..stage1_prediction_markets.qku_computation_control_plane.errors import AuthorityDeniedError, ReasonCode
        from ..stage1_prediction_markets.qku_computation_control_plane.models import (
            EvidenceAbsenceV1, EvidenceAuthorizationMessageV1, EvidenceMessageKindV1, EvidenceSignedMessageV1,
            _EVIDENCE_MESSAGE_PURPOSE_V1, _evidence_decode_authorization_payload_v1,
        )
        from ..stage1_prediction_markets.qku_computation_control_plane.persistence import _EvidenceColdControlReadV1
        from ..stage1_prediction_markets.qku_computation_control_plane.serialization import _evidence_canonical_object_v1

        EvidenceHostBindingV1._assert_local_binding_v1(self)
        _native_require(type(archive) is _EvidenceColdControlReadV1 and archive.issuer.host is self
            and archive.issuer.operation is archive and archive.issuer.lock._is_owned()
            and type(signed) is EvidenceSignedMessageV1 and type(kind) is EvidenceMessageKindV1
            and kind in (EvidenceMessageKindV1.OWNER_ENVELOPE, EvidenceMessageKindV1.ASSEMBLY_GRANT,
                EvidenceMessageKindV1.ATTEMPT_GRANT, EvidenceMessageKindV1.REVIEW_DECISION),
            "LP03_COLD_ARCHIVE_HISTORICAL_SIGNATURE_SCOPE")
        for value in (issuer, subject, audience):
            _native_ident(value)
        _public_counter_v1(generation, allow_zero=True)
        _public_counter_v1(original_wall_ns)
        _EvidenceColdControlReadV1._check_current_v1(archive)
        config = self.__configuration
        _native_require(generation == archive.recovery_authorization.target_generation
            and config.generation == archive.recovery_authorization.new_generation
            and original_wall_ns < archive.recovery_authorization.observed_at_ns,
            "LP03_COLD_ARCHIVE_GENERATION_AND_TIME")
        raw = signed.canonical_message.encode("utf-8", "strict")
        prefix = b"QTT-LP03-EVIDENCE-AUTH-V1\0"
        _native_require(len(prefix) + len(raw) <= 65536, "LP03_COLD_ARCHIVE_ORIGINAL_SIGNATURE_BOUND")
        message = EvidenceAuthorizationMessageV1.from_canonical_mapping(_evidence_canonical_object_v1(raw))
        _native_require((message.kind, message.key_purpose, message.issuer, message.subject, message.audience,
            message.deployment_id, message.origin, message.generation) ==
            (kind, _EVIDENCE_MESSAGE_PURPOSE_V1[kind], issuer, subject, audience,
                config.deployment_id, config.origin, generation),
            "LP03_COLD_ARCHIVE_ORIGINAL_SIGNATURE_IDENTITIES")
        keys = tuple(key for key in config.verification_keys
            if (key.purpose, key.principal, key.key_id) == (message.key_purpose, issuer, message.key_id))
        _native_require(len(keys) == 1, "LP03_COLD_ARCHIVE_ORIGINAL_KEY_UNAVAILABLE")
        key, = keys
        _native_require(type(key.revocation_record_ref_or_absence) is EvidenceAbsenceV1
            and key.valid_from_wall_ns <= message.valid_from_wall_ns <= original_wall_ns
            < message.exclusive_expiry_wall_ns <= key.exclusive_expiry_wall_ns,
            "LP03_COLD_ARCHIVE_ORIGINAL_KEY_AND_TIME")
        try:
            from cryptography.exceptions import InvalidSignature
            from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
            from cryptography.hazmat.bindings import _rust
            public = Ed25519PublicKey.from_public_bytes(bytes.fromhex(key.public_key_hex))
            _native_require(type(public) is _rust.openssl.ed25519.Ed25519PublicKey,
                "LP03_NATIVE_ED25519_KEY_REQUIRED")
        except (ImportError, AttributeError, ValueError, TypeError) as exc:
            raise AuthorityDeniedError(ReasonCode.EVIDENCE_AUTHORITY_UNAVAILABLE, "EVIDENCE_AUTHORITY_UNAVAILABLE") from exc
        try:
            type(public).verify(public, bytes.fromhex(signed.signature_hex), prefix + raw)
        except (InvalidSignature, ValueError) as exc:
            raise AuthorityDeniedError(ReasonCode.EVIDENCE_GRANT_INVALID, "LP03_COLD_ARCHIVE_ORIGINAL_SIGNATURE_INVALID") from exc
        payload = _evidence_decode_authorization_payload_v1(message)
        _EvidenceColdControlReadV1._check_current_v1(archive)
        return message, payload

    def _verify_message_v1(self, signed_message, *, expected_kind, expected_issuer,
                           expected_subject, expected_audience, expected_generation):
        from ..stage1_prediction_markets.qku_computation_control_plane.context import (
            _native_ident, _native_require, _public_counter_v1,
        )
        from ..stage1_prediction_markets.qku_computation_control_plane.models import (
            EvidenceAbsenceV1, EvidenceAuthorizationMessageV1, EvidenceMessageKindV1,
            EvidenceSignedMessageV1, _EVIDENCE_MESSAGE_PURPOSE_V1, _evidence_decode_authorization_payload_v1,
        )
        from ..stage1_prediction_markets.qku_computation_control_plane.serialization import _evidence_canonical_object_v1
        from ..stage1_prediction_markets.qku_computation_control_plane.errors import AuthorityDeniedError, ReasonCode

        EvidenceHostBindingV1._assert_local_binding_v1(self)
        _native_require(type(signed_message) is EvidenceSignedMessageV1
                        and type(expected_kind) is EvidenceMessageKindV1, "LP03_MESSAGE_VERIFICATION_TYPE")
        for value in (expected_issuer, expected_subject, expected_audience):
            _native_ident(value)
        _public_counter_v1(expected_generation, allow_zero=True)
        raw = signed_message.canonical_message.encode("utf-8", "strict")
        message = EvidenceAuthorizationMessageV1.from_canonical_mapping(_evidence_canonical_object_v1(raw))
        cfg = self.__configuration
        _native_require((message.kind, message.issuer, message.subject, message.audience, message.deployment_id, message.key_purpose)
                        == (expected_kind, expected_issuer, expected_subject, expected_audience,
                            cfg.deployment_id, _EVIDENCE_MESSAGE_PURPOSE_V1[expected_kind]),
                        "LP03_VERIFICATION_MESSAGE_SCOPE")
        issuer_keys = tuple(item for item in cfg.verification_keys
                            if item.purpose is message.key_purpose and item.principal == expected_issuer)
        if not issuer_keys:
            raise AuthorityDeniedError(ReasonCode.EVIDENCE_AUTHORITY_UNAVAILABLE, "LP03_VERIFICATION_KEY_UNAVAILABLE")
        candidates = tuple(item for item in issuer_keys if item.key_id == message.key_id)
        grant_kinds = (EvidenceMessageKindV1.ASSEMBLY_GRANT, EvidenceMessageKindV1.ATTEMPT_GRANT,
                       EvidenceMessageKindV1.REVIEW_ADMISSION, EvidenceMessageKindV1.RECEIVER_ADMISSION)
        if len(candidates) != 1 and expected_kind in grant_kinds:
            raise AuthorityDeniedError(ReasonCode.EVIDENCE_GRANT_INVALID, "LP03_VERIFICATION_KEY_UNAVAILABLE")
        _native_require(len(candidates) == 1, "LP03_VERIFICATION_KEY_UNAVAILABLE")
        key = candidates[0]
        payload = _evidence_decode_authorization_payload_v1(message)
        domain_message = b"QTT-LP03-EVIDENCE-AUTH-V1\0" + raw
        _native_require(len(domain_message) <= 65536, "LP03_VERIFICATION_BYTE_BOUND")
        try:
            from cryptography.exceptions import InvalidSignature
            from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
            from cryptography.hazmat.bindings import _rust
            public = Ed25519PublicKey.from_public_bytes(bytes.fromhex(key.public_key_hex))
            _native_require(type(public) is _rust.openssl.ed25519.Ed25519PublicKey, "LP03_NATIVE_ED25519_KEY_REQUIRED")
        except (ImportError, AttributeError, ValueError, TypeError) as exc:
            raise AuthorityDeniedError(ReasonCode.EVIDENCE_AUTHORITY_UNAVAILABLE, "EVIDENCE_AUTHORITY_UNAVAILABLE") from exc
        with self.__lock:
            EvidenceHostBindingV1._assert_local_binding_v1(self)
            now = self.__wall_ns()
            _native_require(type(key.revocation_record_ref_or_absence) is EvidenceAbsenceV1
                            and key.valid_from_wall_ns <= message.valid_from_wall_ns <= now
                            < message.exclusive_expiry_wall_ns <= key.exclusive_expiry_wall_ns,
                            "LP03_VERIFICATION_VALIDITY")
            try:
                type(public).verify(public, bytes.fromhex(signed_message.signature_hex), domain_message)
            except (InvalidSignature, ValueError) as exc:
                reason = (ReasonCode.EVIDENCE_GRANT_INVALID if expected_kind in grant_kinds
                          else ReasonCode.CAPABILITY_DENIED)
                raise AuthorityDeniedError(reason, "LP03_SIGNATURE_INVALID") from exc
            if message.generation != expected_generation:
                raise AuthorityDeniedError(ReasonCode.EVIDENCE_GENERATION_STALE, "LP03_VERIFICATION_MESSAGE_SCOPE")
            if message.origin is not cfg.origin:
                raise AuthorityDeniedError(ReasonCode.EVIDENCE_ORIGIN_MISMATCH, "LP03_VERIFICATION_MESSAGE_SCOPE")
        # This remains data. No grant handle or persistence permission is minted.
        return message, payload


class EvidenceIssuerContextV1:
    """Original issuing-service context; not serializable request authority."""

    __slots__ = ("__owner",)

    def __init__(self, owner) -> None:
        from ..stage1_prediction_markets.qku_computation_control_plane.context import _native_require

        _native_require(type(owner) is _EvidenceIssuerStateV1, "LP03_ISSUER_CONTEXT_OWNER")
        self.__owner = owner

    def __repr__(self) -> str:
        return "<LP03 original issuer context>"

    def __copy__(self):
        raise TypeError("LP03 issuer context cannot be copied")

    def __deepcopy__(self, memo):
        raise TypeError("LP03 issuer context cannot be copied")

    def __reduce_ex__(self, protocol):
        raise TypeError("LP03 issuer context cannot be serialized")

    def _identity_for_owner_v1(self, service):
        from ..stage1_prediction_markets.qku_computation_control_plane.context import _native_require

        state = self.__owner
        _native_require(type(self) is EvidenceIssuerContextV1 and type(service) is AgentOrchService
                        and type(state) is _EvidenceIssuerStateV1 and state.service is service and state.context is self
                        and getattr(service, "_evidence_issuer_state_v1", None) is state,
                        "LP03_ISSUER_CONTEXT_NOT_ORIGINAL")
        return state

    def _state_for_owner_v1(self, service):
        from ..stage1_prediction_markets.qku_computation_control_plane.context import _native_require
        from ..stage1_prediction_markets.qku_computation_control_plane.persistence import _EvidenceBoundStoreV1

        state = EvidenceIssuerContextV1._identity_for_owner_v1(self, service)
        with state.lock:
            EvidenceHostBindingV1._assert_local_binding_v1(state.host)
            retained = getattr(state.control_store, "_evidence_store_binding_v1", None)
            _native_require(type(retained) is _EvidenceBoundStoreV1, "LP03_ISSUER_CONTROL_STORE_REQUIRED")
            _EvidenceBoundStoreV1._require_original_objects_v1(retained, state.host, state.control_store)
        return state


@dataclass(frozen=True, slots=True)
class _BoundEvidenceCallbackV1:
    host_binding: EvidenceHostBindingV1
    plugin_registration: object

    @property
    def pin(self):
        return self.plugin_registration.pin

    def require_current_v1(self):
        from ..plugins.registry import _ResolvedEvidenceCallbackV1
        from ..stage1_prediction_markets.qku_computation_control_plane.context import _native_require
        from ..stage1_prediction_markets.qku_computation_control_plane.models import EvidenceCallbackPinV1

        registration = self.plugin_registration
        _native_require(type(self) is _BoundEvidenceCallbackV1
            and type(registration) is _ResolvedEvidenceCallbackV1
            and _ResolvedEvidenceCallbackV1.is_current_v1(registration)
            and type(registration.pin) is EvidenceCallbackPinV1,
            "LP03_CALLBACK_ORIGINAL_REGISTRATION_CHANGED")
        EvidenceHostBindingV1._assert_local_binding_v1(self.host_binding)
        config = self.host_binding.public_configuration
        _native_require(self.pin.package_identity_ref == config.package_identity_ref and self.pin.origin is config.origin,
                        "LP03_CALLBACK_CURRENT_PACKAGE_SCOPE")

    def on_event_v1(self, event, immutable_inputs, lane_state, scenario_values):
        from ..stage1_prediction_markets.qku_computation_control_plane.context import _native_require
        from ..stage1_prediction_markets.qku_computation_control_plane.models import (
            EvidenceStepOutcomeV1, EvidenceTimelineEventV1,
        )

        _BoundEvidenceCallbackV1.require_current_v1(self)
        _native_require(type(event) is EvidenceTimelineEventV1 and event.origin is self.pin.origin
                        and type(immutable_inputs) is MappingProxyType and type(lane_state) is MappingProxyType
                        and type(scenario_values) is tuple, "LP03_CALLBACK_TYPED_INPUTS")
        registration = self.plugin_registration
        outcome = registration.implementation(registration.adapter, event, immutable_inputs, lane_state, scenario_values)
        _BoundEvidenceCallbackV1.require_current_v1(self)
        _native_require(type(outcome) is EvidenceStepOutcomeV1, "LP03_CALLBACK_OUTCOME_TYPE")
        EvidenceStepOutcomeV1.__post_init__(outcome)
        return outcome


class _EvidenceIssuerStateV1:
    """Private AGENT_ORCH1 composition over original configured metadata/store.

    The retained owner envelopes enter only through explicit protected setup,
    never through an issue/resolve request. They remain signed data; source
    rights, generation, reservation and committed readback precede admission.
    """

    __slots__ = ("service", "host", "control_store", "owner_envelopes", "historical_owner_envelopes", "source_custodies", "lock", "context", "cold_role_stores",
                 "clock", "operation", "preparations", "generation", "cancelled_envelopes", "assembler_context", "registrations",
                 "supervisor", "supervisor_original", "measured_evidence_binding", "measured_review_binding", "measured_receiver_bindings",
                 "lifecycle_identity", "lifecycle_first_operation", "lifecycle_original", "lifecycle_unresolved",
                 "callback_registrations", "callback_registrations_original")

    def __init__(self, *, service, host_binding, control_store, original_owner_envelopes,
                 original_source_registries, original_historical_owner_envelopes=(), original_cold_role_stores=(),
                 original_callback_registry=None, original_callback_package=None) -> None:
        from _thread import RLock
        from ..stage1_prediction_markets.qku_computation_control_plane.context import _native_require
        from ..stage1_prediction_markets.qku_computation_control_plane.models import (
            EvidenceAuthorizationMessageV1, EvidenceKeyPurposeV1, EvidenceMessageKindV1,
            EvidenceSignedMessageV1, EvidenceStoreRoleV1,
        )
        from ..stage1_prediction_markets.qku_computation_control_plane.persistence import _EvidenceBoundStoreV1
        from ..stage1_prediction_markets.qku_computation_control_plane.serialization import _evidence_canonical_object_v1
        from ..stage1_prediction_markets.qku_computation_control_plane.sqlite_reference import SQLiteReferenceAdapterV1
        from ..stage1_prediction_markets.qku_computation_control_plane.input_resolver import (
            _require_evidence_packet_custody_v1, _EvidenceOwnerPacketCustodyV1,
        )

        _native_require(type(service) is AgentOrchService and type(host_binding) is EvidenceHostBindingV1
                        and type(control_store) is SQLiteReferenceAdapterV1, "LP03_ISSUER_COMPOSITION_TYPE")
        retained = getattr(control_store, "_evidence_store_binding_v1", None)
        _native_require(type(retained) is _EvidenceBoundStoreV1
                        and retained.binding.role is EvidenceStoreRoleV1.CONTROL,
                        "LP03_ISSUER_CONTROL_STORE_REQUIRED")
        _EvidenceBoundStoreV1._require_original_host_v1(retained, host_binding, control_store)
        _native_require(type(original_owner_envelopes) is tuple and 0 < len(original_owner_envelopes) <= 64
                        and all(type(item) is EvidenceSignedMessageV1 for item in original_owner_envelopes),
                        "LP03_ORIGINAL_OWNER_ENVELOPE_ROSTER")
        config = host_binding.public_configuration
        retained_envelopes = []
        for signed in original_owner_envelopes:
            body = EvidenceAuthorizationMessageV1.from_canonical_mapping(
                _evidence_canonical_object_v1(signed.canonical_message.encode("utf-8")))
            enrolled = tuple(item for item in config.verification_keys
                             if item.key_id == body.key_id and item.purpose is EvidenceKeyPurposeV1.OWNER_APPROVAL)
            _native_require(len(enrolled) == 1, "LP03_OWNER_VERIFICATION_KEY_REQUIRED")
            message, envelope = EvidenceHostBindingV1._verify_message_v1(host_binding, signed,
                expected_kind=EvidenceMessageKindV1.OWNER_ENVELOPE, expected_issuer=enrolled[0].principal,
                expected_subject=body.subject, expected_audience=config.service_principal,
                expected_generation=config.generation)
            _native_require(envelope.deployment_id == config.deployment_id
                            and envelope.package_identity_ref == config.package_identity_ref
                            and envelope.environment_identity == config.environment_identity
                            and set(envelope.store_bindings) == set(config.store_bindings)
                            and envelope.assembly_scope.control_store_id == retained.binding.store_id,
                            "LP03_OWNER_ENVELOPE_HOST_CONFIGURATION_JOIN")
            retained_envelopes.append((envelope.envelope_ref, signed, message, envelope))
        _native_require(len({item[0] for item in retained_envelopes}) == len(retained_envelopes),
                        "LP03_OWNER_ENVELOPE_IDENTITY_CONFLICT")
        _native_require(type(original_source_registries) is tuple and len(original_source_registries) <= 256
                        and len({id(item) for item in original_source_registries}) == len(original_source_registries),
                        "LP03_ORIGINAL_SOURCE_ROSTER")
        custodies = tuple(_require_evidence_packet_custody_v1(item) for item in original_source_registries)
        rights_ids = []
        for custody in custodies:
            with custody.lock:
                _EvidenceOwnerPacketCustodyV1._assert_original_v1(custody)
                source_config = custody.host.public_configuration
                _native_require((source_config.deployment_id, source_config.origin, source_config.host_identity,
                                 source_config.package_identity_ref, source_config.environment_identity)
                                == (config.deployment_id, config.origin, config.host_identity,
                                    config.package_identity_ref, config.environment_identity),
                                "LP03_ORIGINAL_SOURCE_HOST_JOIN")
                rights_ids.extend(custody.rights_by_id)
        _native_require(len(set(rights_ids)) == len(rights_ids), "LP03_ORIGINAL_SOURCE_RIGHTS_AMBIGUOUS")
        self.service = service
        self.host = host_binding
        self.control_store = control_store
        self.owner_envelopes = tuple(retained_envelopes)
        self.callback_registrations = _EvidenceIssuerStateV1._bind_original_callbacks_v1(
            self, original_callback_registry, original_callback_package)
        self.callback_registrations_original = (self, host_binding, self.owner_envelopes, self.callback_registrations)
        self.historical_owner_envelopes = _EvidenceIssuerStateV1._parse_historical_enrollments_v1(
            host_binding, retained, original_historical_owner_envelopes, self.owner_envelopes)
        self.cold_role_stores = _EvidenceIssuerStateV1._require_cold_role_stores_v1(
            host_binding, original_cold_role_stores)
        self.source_custodies = custodies
        self.lock = RLock()
        self.context = EvidenceIssuerContextV1(self)
        self.clock, self.operation = None, None
        self.preparations = {}
        self.generation = config.generation
        self.cancelled_envelopes = set()
        self.assembler_context = None
        self.registrations = {}
        self.supervisor = None
        self.supervisor_original = None
        self.measured_evidence_binding = None
        self.measured_review_binding = None
        self.measured_receiver_bindings = ()
        # These identities are inert until the first original CONTROL grant
        # transaction and its independent readback establish their custody.
        self.lifecycle_identity = (self, host_binding, control_store,
            EvidenceHostBindingV1._nonce_ref_v1(host_binding, "LP03-ISSUER-INSTANCE"),
            EvidenceHostBindingV1._nonce_ref_v1(host_binding, "LP03-SUPERVISOR-INSTANCE"), config.generation)
        self.lifecycle_first_operation = self.lifecycle_original = None
        self.lifecycle_unresolved = False

    def _bind_original_callbacks_v1(self, registry, package):
        from inspect import getattr_static
        from ..plugins.registry import PluginRegistry
        from ..stage1_prediction_markets.qku_computation_control_plane.context import _native_require
        from ..stage1_prediction_markets.qku_computation_control_plane.errors import ContractValidationError, ReasonCode
        from ..stage1_prediction_markets.qku_computation_control_plane.models import EvidenceCallbackPinV1, EvidenceOriginV1

        pairs = tuple(dict.fromkeys(pin for row in self.owner_envelopes for pin in row[3].callback_pins))
        _native_require((not pairs and registry is None and package is None)
                        or (bool(pairs) and type(registry) is PluginRegistry and
                            (package is None or type(package) is tuple and len(package) == 2)),
                        "LP03_CALLBACK_ORIGINAL_HOST_COMPOSITION")
        if not pairs:
            return ()
        EvidenceHostBindingV1._assert_local_binding_v1(self.host)
        config = self.host.public_configuration
        manifest, projection = (None, None) if package is None else package
        _native_require(config.origin is EvidenceOriginV1.SOFTWARE_CONFORMANCE
                        or (manifest is not None and projection is not None), "LP03_CALLBACK_ORIGINAL_PACKAGE_REQUIRED")
        resolved = []
        for callback_id, version in pairs:
            adapter = registry.adapters.get(callback_id)
            pin = getattr_static(type(adapter), "evidence_callback_pin_v1", None)
            _native_require(type(pin) is EvidenceCallbackPinV1 and (pin.callback_id, pin.version) == (callback_id, version),
                            "LP03_CALLBACK_ORIGINAL_HOST_REGISTRATION")
            _native_require(pin.package_identity_ref == config.package_identity_ref and pin.origin is config.origin,
                            "LP03_CALLBACK_CURRENT_PACKAGE_SCOPE")
            try:
                original = PluginRegistry.resolve_evidence_callback_v1(registry, pin, callback_id=callback_id,
                    implementation_ref=pin.implementation_ref, package_id=pin.package_identity_ref,
                    package_manifest=manifest, launch_projection=projection)
            except ValueError as exc:
                raise ContractValidationError(ReasonCode.EVIDENCE_INPUT_UNAVAILABLE, str(exc)) from exc
            bound = _BoundEvidenceCallbackV1(self.host, original)
            _BoundEvidenceCallbackV1.require_current_v1(bound)
            resolved.append(bound)
        return tuple(resolved)

    def _require_original_callbacks_v1(self, envelope_entry, pins):
        from ..stage1_prediction_markets.qku_computation_control_plane.context import _native_require

        original = self.callback_registrations_original
        _native_require(original[0] is self and original[1] is self.host and original[2] is self.owner_envelopes
                        and original[3] is self.callback_registrations
                        and any(row is envelope_entry for row in self.owner_envelopes)
                        and tuple(sorted((row.callback_id, row.version) for row in pins)) == envelope_entry[3].callback_pins,
                        "LP03_CALLBACK_ORIGINAL_ENVELOPE")
        resolved = tuple(row for pin in pins for row in original[3] if row.pin == pin)
        _native_require(tuple(row.pin for row in resolved) == pins, "LP03_CALLBACK_ORIGINAL_ROSTER")
        for row in resolved:
            _native_require(row.host_binding is self.host, "LP03_CALLBACK_ORIGINAL_HOST_REGISTRATION")
            _BoundEvidenceCallbackV1.require_current_v1(row)
        return resolved

    @staticmethod
    def _require_cold_role_stores_v1(issuer_host, stores):
        from ..stage1_prediction_markets.qku_computation_control_plane.context import _native_require
        from ..stage1_prediction_markets.qku_computation_control_plane.models import EvidenceStoreRoleV1
        from ..stage1_prediction_markets.qku_computation_control_plane.persistence import _EvidenceBoundStoreV1
        from ..stage1_prediction_markets.qku_computation_control_plane.sqlite_reference import SQLiteReferenceAdapterV1

        _native_require(type(stores) is tuple and len(stores) <= 3, "LP03_COLD_ARCHIVE_ROLE_ROSTER")
        config = issuer_host.public_configuration
        roles = set()
        for entry in stores:
            _native_require(type(entry) is tuple and len(entry) == 2 and type(entry[0]) is SQLiteReferenceAdapterV1
                and type(entry[1]) is EvidenceHostBindingV1, "LP03_COLD_ARCHIVE_ROLE_ENTRY")
            adapter, host = entry
            EvidenceHostBindingV1._assert_local_binding_v1(host)
            retained = adapter._evidence_store_binding_v1
            _native_require(type(retained) is _EvidenceBoundStoreV1
                and retained.binding.role in (EvidenceStoreRoleV1.REPLAY,EvidenceStoreRoleV1.PAPER,EvidenceStoreRoleV1.REVIEW)
                and retained.binding.role not in roles and retained.binding in config.store_bindings
                and "EVIDENCE_COLD_CONTROL_RECONSTRUCTION_V1" in retained.binding.allowed_reader_purposes
                and (host.public_configuration.host_identity,host.public_configuration.generation) == (config.host_identity,config.generation),
                "LP03_COLD_ARCHIVE_ORIGINAL_ROLE_BINDING")
            _EvidenceBoundStoreV1._require_original_host_v1(retained,host,adapter)
            roles.add(retained.binding.role)
        return stores

    @staticmethod
    def _parse_historical_enrollments_v1(host, retained_store, signed_envelopes, current_enrollments):
        """Parse exact configured candidate bytes; historical authentication follows under the archive owner."""
        from ..stage1_prediction_markets.qku_computation_control_plane.context import _native_require
        from ..stage1_prediction_markets.qku_computation_control_plane.models import (
            EvidenceAuthorizationMessageV1, EvidenceKeyPurposeV1, EvidenceMessageKindV1, EvidenceSignedMessageV1,
            _evidence_decode_authorization_payload_v1,
        )
        from ..stage1_prediction_markets.qku_computation_control_plane.serialization import _evidence_canonical_object_v1

        _native_require(type(signed_envelopes) is tuple and len(signed_envelopes) <= 64,
            "LP03_COLD_ARCHIVE_OLD_ENROLLMENT_ROSTER")
        config = host.public_configuration
        selected = []
        for signed in signed_envelopes:
            _native_require(type(signed) is EvidenceSignedMessageV1, "LP03_COLD_ARCHIVE_OLD_ENROLLMENT_TYPE")
            message = EvidenceAuthorizationMessageV1.from_canonical_mapping(
                _evidence_canonical_object_v1(signed.canonical_message.encode("utf-8")))
            _native_require(message.kind is EvidenceMessageKindV1.OWNER_ENVELOPE
                and message.key_purpose is EvidenceKeyPurposeV1.OWNER_APPROVAL
                and message.generation+1 == config.generation and message.origin is config.origin
                and message.deployment_id == config.deployment_id and message.audience == config.service_principal,
                "LP03_COLD_ARCHIVE_OLD_ENROLLMENT_SCOPE")
            envelope = _evidence_decode_authorization_payload_v1(message)
            _native_require(envelope.issuer_principal == config.service_principal
                and envelope.package_identity_ref == config.package_identity_ref
                and envelope.environment_identity == config.environment_identity
                and set(envelope.store_bindings) == set(config.store_bindings)
                and envelope.assembly_scope.control_store_id == retained_store.binding.store_id
                and envelope.envelope_ref not in {row[0] for row in current_enrollments}
                and envelope.envelope_ref not in {row[2].envelope_ref for row in selected},
                "LP03_COLD_ARCHIVE_OLD_ENROLLMENT_CONFIGURATION")
            selected.append((signed,message,envelope))
        return tuple(selected)

    def _require_lifecycle_original_v1(self, proposed=None, *, publishing=False):
        """Original first observations confer custody; stored strings do not."""
        from ..stage1_prediction_markets.qku_computation_control_plane.context import _native_require
        from ..stage1_prediction_markets.qku_computation_control_plane.errors import ContractValidationError, ReasonCode
        from ..stage1_prediction_markets.qku_computation_control_plane.persistence import _EvidenceControlBootstrapV1
        original = self.lifecycle_original if proposed is None else proposed
        if self.lifecycle_unresolved or original is None:
            raise ContractValidationError(ReasonCode.EVIDENCE_RUN_UNRESOLVED, "LP03_CONTROL_LIFECYCLE_RECOVERY_REQUIRED")
        _native_require(type(original) is tuple and len(original) == 6 and original[0] is self.lifecycle_identity
                        and type(original[0]) is tuple and len(original[0]) == 6
                        and original[0][0] is self and original[0][1] is self.host and original[0][2] is self.control_store
                        and original[0][5] == self.generation == self.host.public_configuration.generation,
                        "LP03_CONTROL_LIFECYCLE_ORIGINAL_CHANGED")
        first, roster, committed, readback, handle = original[1:]
        _native_require(type(first) is _EvidenceControlBootstrapV1, "LP03_CONTROL_LIFECYCLE_FIRST_OPERATION_REQUIRED")
        _EvidenceControlBootstrapV1._assert_lifecycle_witnesses_v1(first)
        _native_require(type(first) is _EvidenceControlBootstrapV1 and first is self.lifecycle_first_operation
                        and first.issuer is self and first.bootstrap_original is roster
                        and type(roster) is tuple and len(roster) == 4 and len(roster[0]) == len(roster[1]) == len(roster[2]) == 11
                        and type(first.lifecycle_rows) is tuple and len(first.lifecycle_rows) == 2
                        and all(row is original_row for row, original_row in zip(first.lifecycle_rows, roster[1][9:11]))
                        and committed is first.bootstrap_commit_observation and type(committed) is tuple and len(committed) == 3
                        and readback is first.bootstrap_readback_observation and type(readback) is tuple and len(readback) == 4
                        and committed[1] <= readback[1]
                        and type(handle) is EvidenceAssemblyGrantV1 and handle._owner is self
                        and handle._grant_ref == first.grant_record.record_id,
                        "LP03_CONTROL_LIFECYCLE_FIRST_OBSERVATIONS_CHANGED")
        held = self.preparations.get(first.grant_record.record_id)
        _native_require(held is not None and held[0] is first
                        and ((publishing and self.lifecycle_original is None and held[1] is None
                              and first.commit_state == "COMMITTED_AND_READBACK")
                             or (not publishing and self.lifecycle_original is original and held[1] is handle)),
                        "LP03_CONTROL_LIFECYCLE_CAPABILITY_CHANGED")
        return original

    def _registration_current_v1(self, operation):
        from ..stage1_prediction_markets.qku_computation_control_plane.context import _native_require
        from ..stage1_prediction_markets.qku_computation_control_plane.latency_policy import _EvidenceLocalClockV1
        from ..stage1_prediction_markets.qku_computation_control_plane.input_resolver import _EvidenceOwnerPacketCustodyV1
        from ..stage1_prediction_markets.qku_computation_control_plane.persistence import (
            _EvidenceBoundStoreV1, _EvidenceRegistrationOperationV1,
        )
        from ..stage1_prediction_markets.qku_computation_control_plane.models import EvidenceAbsenceV1
        lifecycle = _EvidenceIssuerStateV1._require_lifecycle_original_v1(self)
        _native_require(type(operation) is _EvidenceRegistrationOperationV1 and operation.issuer is self
                        and self.operation is operation and self.lock._is_owned()
                        and self.registrations.get(operation.preparation.grant_record.record_id) is operation
                        and getattr(self.service, "_evidence_issuer_state_v1", None) is self,
                        "LP03_REGISTRATION_OPERATION_NOT_ORIGINAL")
        EvidenceHostBindingV1._assert_local_binding_v1(self.host)
        ref, _signed, message, envelope = operation.envelope_entry
        _native_require(any(entry is operation.envelope_entry for entry in self.owner_envelopes),
                        "LP03_REGISTRATION_ENVELOPE_NOT_ORIGINAL")
        keys = tuple(k for k in self.host.public_configuration.verification_keys
                     if k.key_id in (message.key_id, self.host.public_configuration.signing_key_id))
        _native_require(len(keys) == 2 and all(type(key.revocation_record_ref_or_absence) is EvidenceAbsenceV1 for key in keys),
                        "LP03_REGISTRATION_KEY_NOT_CURRENT")
        for custody, policies in operation.policies:
            _native_require(custody.lock._is_owned(), "LP03_ORIGINAL_SOURCE_LOCK_REQUIRED")
            _EvidenceOwnerPacketCustodyV1._assert_original_v1(custody)
            for policy in policies:
                _native_require(custody.rights_by_id.get(policy.rights_ref) is policy
                                and "EVIDENCE_EXPERIMENT_REGISTRATION_V1" in policy.source_purposes
                                and self.host.public_configuration.service_principal in policy.consumer_principals,
                                "LP03_REGISTRATION_ORIGINAL_SOURCE_USE_DENIED")
        _EvidenceBoundStoreV1._require_original_objects_v1(self.control_store._evidence_store_binding_v1, self.host, self.control_store)
        from ..service.pr169_svc1_resolvers import EvidenceProcessSupervisorV1
        execution = (EvidenceProcessSupervisorV1._execution_usage_v1(self.supervisor, operation, refresh=True)
                     if self.supervisor is not None else None)
        wall, mono, cpu = _EvidenceLocalClockV1.observe_v1(self.clock)
        deadline = operation.deadline
        operation.consumed["wall_ns"] = mono - deadline.admitted_monotonic_ns
        operation.consumed["cpu_ns"] = cpu - operation.started_cpu_ns + (execution["cpu_ns"] if execution else 0)
        _native_require(self.operation is operation and ref not in self.cancelled_envelopes
                        and self.generation == message.generation == envelope.assembly_scope.generation
                        == self.host.public_configuration.generation, "LP03_ENVELOPE_WITHDRAWN_OR_STALE")
        _native_require((deadline.clock_domain_id, deadline.process_identity_ref, deadline.boot_identity_ref)
                        == (self.clock.clock_domain_id, self.clock.process_identity_ref, self.clock.boot_identity_ref)
                        and deadline.admitted_monotonic_ns <= mono and message.valid_from_wall_ns <= wall,
                        "LP03_REGISTRATION_CLOCK_CHANGED_OR_REGRESSED")
        _native_require(mono < deadline.exclusive_deadline_monotonic_ns and wall < message.exclusive_expiry_wall_ns
                        and wall < envelope.exclusive_expiry_wall_ns, "LP03_REGISTRATION_EXPIRED")
        _native_require(all(key.valid_from_wall_ns <= wall < key.exclusive_expiry_wall_ns for key in keys),
                        "LP03_REGISTRATION_KEY_NOT_CURRENT")
        _native_require(all(custody.rights_by_id.get(policy.rights_ref) is policy
                            and policy.rights_ref not in custody.withdrawn and policy.generation == custody.generation
                            and policy.valid_from_wall_ns <= wall < policy.exclusive_expiry_wall_ns
                            and wall < policy.exclusive_retention_wall_ns for custody, policies in operation.policies for policy in policies),
                        "LP03_ORIGINAL_RIGHTS_WITHDRAWN_OR_STALE")
        from ..stage1_prediction_markets.qku_computation_control_plane.input_resolver import _EvidenceOwnerPacketCustodyV1
        for custody, _policies in operation.policies:
            published = _EvidenceOwnerPacketCustodyV1._published_source_v1(custody)
            if published is not None:
                type(published)._assert_scope_v1(published, envelope.assembly_scope,
                    observed_wall_ns=wall, purpose="EVIDENCE_EXPERIMENT_REGISTRATION_V1",
                    principals=(self.host.public_configuration.service_principal,))
        if operation.protocol is not None:
            original = operation.resolved_policy_original
            _native_require(original is not None and operation.protocol is original[0]
                            and operation.registration_policy is original[1] and operation.policy_source_originals is original[4],
                            "LP03_REGISTRATION_ORIGINAL_POLICY_CHANGED")
            _native_require(operation.protocol.valid_from_wall_ns <= wall < operation.protocol.exclusive_expiry_wall_ns,
                            "LP03_PARAMETER_PROTOCOL_EXPIRED")
        _native_require(_EvidenceIssuerStateV1._require_lifecycle_original_v1(self) is lifecycle,
                        "LP03_CONTROL_LIFECYCLE_CURRENTNESS_CHANGED")
        return wall, mono, cpu

    def _bootstrap_current_v1(self, operation):
        from ..stage1_prediction_markets.qku_computation_control_plane.context import _native_require
        from ..stage1_prediction_markets.qku_computation_control_plane.latency_policy import _EvidenceLocalClockV1
        from ..stage1_prediction_markets.qku_computation_control_plane.input_resolver import _EvidenceOwnerPacketCustodyV1
        from ..stage1_prediction_markets.qku_computation_control_plane.persistence import _EvidenceBoundStoreV1
        from ..stage1_prediction_markets.qku_computation_control_plane.models import EvidenceAbsenceV1

        lifecycle = self.lifecycle_original
        if lifecycle is not None:
            _EvidenceIssuerStateV1._require_lifecycle_original_v1(self)
        else:
            _native_require(not self.lifecycle_unresolved and self.lifecycle_first_operation is operation,
                            "LP03_CONTROL_LIFECYCLE_BOOTSTRAP_UNRESOLVED")

        _native_require(self.operation is operation and self.lock._is_owned()
                        and getattr(self.service, "_evidence_issuer_state_v1", None) is self,
                        "LP03_CONTROL_OPERATION_NOT_ORIGINAL")
        EvidenceHostBindingV1._assert_local_binding_v1(self.host)
        ref, _signed, message, envelope = operation.envelope_entry
        _native_require(any(entry is operation.envelope_entry for entry in self.owner_envelopes)
                        and ref not in self.cancelled_envelopes and self.generation == message.generation
                        == envelope.assembly_scope.generation == self.host.public_configuration.generation,
                        "LP03_ENVELOPE_WITHDRAWN_OR_STALE")
        deadline = operation.grant_record.deadline_clock_and_process
        keys = tuple(k for k in self.host.public_configuration.verification_keys
                     if k.key_id in (message.key_id, self.host.public_configuration.signing_key_id))
        _native_require(len(keys) == 2 and all(type(k.revocation_record_ref_or_absence) is EvidenceAbsenceV1 for k in keys),
                        "LP03_ASSEMBLY_KEY_NOT_CURRENT")
        for custody, policies in operation.policies:
            _native_require(custody.lock._is_owned(), "LP03_ORIGINAL_SOURCE_LOCK_REQUIRED")
            _EvidenceOwnerPacketCustodyV1._assert_original_v1(custody)
            for policy in policies:
                _native_require(custody.rights_by_id.get(policy.rights_ref) is policy
                                and policy.rights_ref not in custody.withdrawn and policy.generation == custody.generation,
                                "LP03_ORIGINAL_RIGHTS_WITHDRAWN_OR_STALE")
        retained = self.control_store._evidence_store_binding_v1
        _EvidenceBoundStoreV1._require_original_objects_v1(retained, self.host, self.control_store)
        # Native/file observations may block. Time is observed after those
        # checks; only bounded original data predicates follow before effects.
        wall, mono, cpu = _EvidenceLocalClockV1.observe_v1(self.clock)
        operation.consumed["wall_ns"] = mono - deadline.admitted_monotonic_ns
        operation.consumed["cpu_ns"] = cpu - operation.started_cpu_ns
        _native_require(self.operation is operation and ref not in self.cancelled_envelopes
                        and self.generation == message.generation == envelope.assembly_scope.generation,
                        "LP03_ENVELOPE_WITHDRAWN_OR_STALE")
        _native_require((deadline.clock_domain_id, deadline.process_identity_ref, deadline.boot_identity_ref)
                        == (self.clock.clock_domain_id, self.clock.process_identity_ref, self.clock.boot_identity_ref)
                        and deadline.admitted_monotonic_ns <= mono < deadline.exclusive_deadline_monotonic_ns
                        and message.valid_from_wall_ns <= wall < message.exclusive_expiry_wall_ns
                        and wall < envelope.exclusive_expiry_wall_ns
                        and wall < envelope.assembly_scope.exclusive_expiry_wall_ns,
                        "LP03_ASSEMBLY_EXPIRED")
        _native_require(all(k.valid_from_wall_ns <= wall < k.exclusive_expiry_wall_ns for k in keys),
                        "LP03_ASSEMBLY_KEY_NOT_CURRENT")
        _native_require(all(custody.rights_by_id.get(policy.rights_ref) is policy
                            and policy.rights_ref not in custody.withdrawn and policy.generation == custody.generation
                            and policy.valid_from_wall_ns <= wall < policy.exclusive_expiry_wall_ns
                            and wall < policy.exclusive_retention_wall_ns for custody, rows in operation.policies for policy in rows),
                        "LP03_ORIGINAL_RIGHTS_WITHDRAWN_OR_STALE")
        from ..stage1_prediction_markets.qku_computation_control_plane.input_resolver import _EvidenceOwnerPacketCustodyV1
        for custody, _policies in operation.policies:
            published = _EvidenceOwnerPacketCustodyV1._published_source_v1(custody)
            if published is not None:
                type(published)._assert_scope_v1(published, envelope.assembly_scope, observed_wall_ns=wall)
        if lifecycle is not None:
            _native_require(_EvidenceIssuerStateV1._require_lifecycle_original_v1(self) is lifecycle,
                            "LP03_CONTROL_LIFECYCLE_CURRENTNESS_CHANGED")
        else:
            _native_require(self.lifecycle_original is None and not self.lifecycle_unresolved
                            and self.lifecycle_first_operation is operation, "LP03_CONTROL_LIFECYCLE_BOOTSTRAP_CHANGED")
        return wall, mono, cpu

    def _lock_original_source_custodies_v1(self, stack):
        from ..stage1_prediction_markets.qku_computation_control_plane.input_resolver import _EvidenceOwnerPacketCustodyV1

        for lock in _EvidenceOwnerPacketCustodyV1._original_operation_locks_v1(self.source_custodies):
            stack.enter_context(lock)

    def _read_source_slice_v1(self, read_grant):
        from contextlib import ExitStack
        from ..stage1_prediction_markets.qku_computation_control_plane.context import _native_require
        from ..stage1_prediction_markets.qku_computation_control_plane.input_lock import EvidenceAssemblerContextV1
        from ..stage1_prediction_markets.qku_computation_control_plane.input_resolver import (
            _require_evidence_packet_custody_v1, _EvidenceOwnerPacketCustodyV1,
        )
        from ..stage1_prediction_markets.qku_computation_control_plane.latency_policy import _EvidenceLocalClockV1
        from ..stage1_prediction_markets.qku_computation_control_plane.models import EvidenceAssemblyStateV1
        from ..stage1_prediction_markets.qku_computation_control_plane.persistence import _EvidenceControlBootstrapV1
        from ..stage1_prediction_markets.qku_computation_control_plane.source_policy import _EvidenceHistoricalReadV1
        from ..stage1_prediction_markets.qku_computation_control_plane.sqlite_reference import SQLiteReferenceAdapterV1

        _native_require(type(read_grant) is _EvidenceHistoricalReadV1 and read_grant.issuer is self,
                        "LP03_ORIGINAL_SOURCE_READ_CAPABILITY_REQUIRED")
        _native_require(EvidenceAssemblerContextV1._require_original_v1(read_grant.requester) is self,
                        "LP03_ORIGINAL_SOURCE_READ_REQUESTER")
        with self.lock, ExitStack() as locks:
            _native_require(self.operation is None, "LP03_CONTROL_OPERATION_REENTRY")
            if self.lifecycle_first_operation is not None:
                _EvidenceIssuerStateV1._require_lifecycle_original_v1(self)
            original = self.preparations.get(read_grant.assembly_grant.grant_ref)
            _native_require(original is not None and original[1] is read_grant.assembly_grant,
                            "LP03_ORIGINAL_ASSEMBLY_GRANT_UNAVAILABLE")
            operation = original[0]
            _native_require(any(read_grant is item for item in operation.source_read_capabilities)
                            and operation.commit_state == "COMMITTED_AND_READBACK"
                            and operation.current_state.state in (EvidenceAssemblyStateV1.ADMITTED, EvidenceAssemblyStateV1.READING),
                            "LP03_PREPARATION_NOT_READABLE")
            custody = _require_evidence_packet_custody_v1(read_grant.registry)
            _native_require(any(custody is item for item in self.source_custodies), "LP03_ORIGINAL_SOURCE_UNAVAILABLE")
            self.operation = operation
            try:
                self._lock_original_source_custodies_v1(locks)
                _EvidenceIssuerStateV1._load_bootstrap_metadata_v1(self, operation)
                SQLiteReferenceAdapterV1._evidence_bootstrap_readback_v1(self.control_store, operation)
                result = _EvidenceOwnerPacketCustodyV1._read_assembly_slice_v1(custody, operation, read_grant.selection)
                from ..stage1_prediction_markets.qku_computation_control_plane.input_resolver import _require_evidence_source_slice_roster_v1
                source_originals = _require_evidence_source_slice_roster_v1(operation, (result,))
                SQLiteReferenceAdapterV1._evidence_append_reading_state_v1(self.control_store, operation)
                _require_evidence_source_slice_roster_v1(operation, (result,), originals=source_originals)
                operation.acquired_slices = (*operation.acquired_slices, result)
                _EvidenceControlBootstrapV1._check_current_v1(operation)
                _require_evidence_source_slice_roster_v1(operation, (result,), originals=source_originals)
                return result
            except BaseException:
                if operation.commit_state == "COMMITTED_AND_READBACK":
                    operation.commit_state = "SOURCE_READ_FAILED_REQUIRES_AUDIT"
                _wall, mono, cpu = _EvidenceLocalClockV1.observe_v1(self.clock)
                operation.consumed["wall_ns"] = mono - operation.grant_record.deadline_clock_and_process.admitted_monotonic_ns
                operation.consumed["cpu_ns"] = cpu - operation.started_cpu_ns
                raise
            finally:
                # The positive return has no later native observation or data
                # callback between its final currentness check and lock release.
                self.operation = None

    def _load_bootstrap_metadata_v1(self, operation):
        from ..stage1_prediction_markets.qku_computation_control_plane.context import _native_require
        from ..stage1_prediction_markets.qku_computation_control_plane.input_resolver import _EvidenceOwnerPacketCustodyV1
        from ..stage1_prediction_markets.qku_computation_control_plane.persistence import _EvidenceControlBootstrapV1
        scope = operation.envelope_entry[3].assembly_scope
        required = {ref for selection in scope.source_selections for ref in selection.required_original_rights_refs}
        policies = []
        for custody in self.source_custodies:
            refs = tuple(ref for selection in scope.source_selections for ref in selection.required_original_rights_refs
                         if ref in custody.rights_by_id)
            count, byte_bound = len(refs), sum(custody.metadata_byte_sizes[ref] for ref in refs)
            _EvidenceControlBootstrapV1._check_current_v1(operation)
            _EvidenceControlBootstrapV1._room_v1(operation, owner_queries=1, record_reads=count,
                                                query_result_records=count, read_bytes=byte_bound)
            _EvidenceControlBootstrapV1._charge_v1(operation, owner_queries=1)
            try:
                selected = _EvidenceOwnerPacketCustodyV1._assembly_metadata_v1(custody, scope, operation=operation)
            finally:
                # Preserve the actual work even when the owner rejects after
                # inspecting an original policy. Native time is never invented.
                from ..stage1_prediction_markets.qku_computation_control_plane.latency_policy import _EvidenceLocalClockV1
                _wall, mono, cpu = _EvidenceLocalClockV1.observe_v1(self.clock)
                operation.consumed["wall_ns"] = mono - operation.grant_record.deadline_clock_and_process.admitted_monotonic_ns
                operation.consumed["cpu_ns"] = cpu - operation.started_cpu_ns
            if selected:
                policies.append((custody, selected))
        covered = {policy.rights_ref for _, rows in policies for policy in rows}
        envelope = operation.envelope_entry[3]
        _native_require(covered == required and required <= set(envelope.source_rights_refs),
                        "LP03_ORIGINAL_SOURCE_RIGHTS_INCOMPLETE")
        _native_require(all((policy.source_selection.original_store_id, policy.source_version)
                            in envelope.source_version_pins for _, rows in policies for policy in rows),
                        "LP03_ORIGINAL_SOURCE_VERSION_JOIN")
        _native_require(not operation.policies or operation.policies == tuple(policies), "LP03_ORIGINAL_SOURCE_METADATA_CHANGED")
        operation.policies = tuple(policies)
        _EvidenceControlBootstrapV1._check_current_v1(operation)

    def _issue_assembly_v1(self, owner_envelope_ref, request, *, lifecycle_identity):
        from contextlib import ExitStack
        from ..stage1_prediction_markets.qku_computation_control_plane.context import _native_ident, _native_require
        from ..stage1_prediction_markets.qku_computation_control_plane import models as m
        from ..stage1_prediction_markets.qku_computation_control_plane.input_resolver import _EvidenceOwnerPacketCustodyV1
        from ..stage1_prediction_markets.qku_computation_control_plane.latency_policy import _EvidenceLocalClockV1
        from ..stage1_prediction_markets.qku_computation_control_plane.persistence import _EvidenceControlBootstrapV1
        from ..stage1_prediction_markets.qku_computation_control_plane.serialization import deterministic_json, _evidence_canonical_object_v1
        from ..stage1_prediction_markets.qku_computation_control_plane.sqlite_reference import SQLiteReferenceAdapterV1

        _native_ident(owner_envelope_ref)
        _native_require(type(request) is m.EvidenceAssemblyRequestV1, "LP03_ASSEMBLY_REQUEST_TYPE")
        with self.lock, ExitStack() as locks:
            _native_require(self.operation is None, "LP03_CONTROL_OPERATION_REENTRY")
            _native_require(lifecycle_identity is self.lifecycle_identity, "LP03_CONTROL_LIFECYCLE_IDENTITY_CHANGED")
            if self.lifecycle_first_operation is not None:
                _EvidenceIssuerStateV1._require_lifecycle_original_v1(self)
            entries = tuple(row for row in self.owner_envelopes if row[0] == owner_envelope_ref)
            _native_require(len(entries) == 1, "LP03_ORIGINAL_OWNER_ENVELOPE_UNAVAILABLE")
            entry = entries[0]
            scope = entry[3].assembly_scope
            _native_require(request.assembly_scope_ref == scope.scope_ref, "LP03_ASSEMBLY_REQUEST_SCOPE")
            required = {ref for selection in scope.source_selections for ref in selection.required_original_rights_refs}
            natural = (self.host.public_configuration.deployment_id, scope.origin.value,
                       scope.intended_experiment_id, scope.intended_experiment_revision)
            for prior, handle, _source_original in self.preparations.values():
                if prior.envelope_entry[0] == owner_envelope_ref and prior.request.idempotency_key == request.idempotency_key:
                    _native_require(prior.request == request, "LP03_ASSEMBLY_IDEMPOTENCY_CONFLICT")
                    _native_require(handle is not None and prior.commit_state == "COMMITTED_AND_READBACK",
                                    "LP03_PREPARATION_UNRESOLVED")
                    self.operation = prior
                    try:
                        self._lock_original_source_custodies_v1(locks)
                        _EvidenceIssuerStateV1._load_bootstrap_metadata_v1(self, prior)
                        _EvidenceControlBootstrapV1._check_current_v1(prior)
                        SQLiteReferenceAdapterV1._evidence_bootstrap_readback_v1(self.control_store, prior)
                        _EvidenceControlBootstrapV1._check_current_v1(prior)
                        return handle
                    finally:
                        self.operation = None
                _native_require(prior.grant_record.preparation_natural_key != natural
                                and prior.grant_record.aggregate_budget_ref != scope.preparation_limits.aggregate_budget_ref,
                                "LP03_PREPARATION_ALREADY_RESERVED_OR_UNRESOLVED")
            _native_require(type(scope.scenario_plan_body_or_existing_ref) is m.EvidenceInlinePlanV1,
                            "LP03_EXISTING_PLAN_RESOLUTION_UNAVAILABLE")
            plan = scope.scenario_plan_body_or_existing_ref.plan
            if self.clock is None:
                self.clock = _EvidenceLocalClockV1()
            now, mono, cpu = _EvidenceLocalClockV1.observe_v1(self.clock)
            deadline = m.EvidenceProcessDeadlineV1(clock_domain_id=self.clock.clock_domain_id,
                process_identity_ref=self.clock.process_identity_ref, boot_identity_ref=self.clock.boot_identity_ref,
                admitted_monotonic_ns=mono, exclusive_deadline_monotonic_ns=mono + scope.preparation_limits.max_wall_ns)
            grant_id = EvidenceHostBindingV1._nonce_ref_v1(self.host, "LP03-ASSEMBLY")
            fence = EvidenceHostBindingV1._nonce_ref_v1(self.host, "LP03-PREPARATION-FENCE")
            payload = m.EvidenceAssemblyGrantPayloadV1(grant_ref=grant_id, owner_envelope_ref=owner_envelope_ref,
                assembly_scope=scope, preparation_ordinal=1, preparation_natural_key=natural,
                exact_frozen_plan_ref=m.EvidenceRecordRefV1(scope.control_store_id, plan.record_id),
                deadline=deadline, preparation_fence_ref=fence)
            signed = EvidenceHostBindingV1._sign_message_v1(self.host, kind=m.EvidenceMessageKindV1.ASSEMBLY_GRANT,
                subject=grant_id, audience=scope.assembler_audience, generation=self.generation,
                valid_from_wall_ns=now, exclusive_expiry_wall_ns=scope.exclusive_expiry_wall_ns,
                payload=_evidence_canonical_object_v1(deterministic_json(payload).encode("utf-8")))
            record = m.EvidenceAssemblyGrantRecordV1(
                record_id=grant_id, schema_version="1.0", origin=scope.origin,
                experiment_id=scope.intended_experiment_id, experiment_revision=scope.intended_experiment_revision,
                protocol_ref=scope.protocol_ref, input_lock_ref=m.EvidenceAbsenceV1("NOT_YET_BOUND_BEFORE_EXECUTION"),
                scenario_plan_ref=plan.record_id, causation_ref=owner_envelope_ref, correlation_ref=scope.scope_ref,
                producing_owner="AGENT_ORCH1", producing_principal=self.host.public_configuration.service_principal,
                source_lineage_refs=tuple(sorted(required)), created_wall_ns=now,
                clock_domain_id=self.clock.clock_domain_id, generation=self.generation,
                no_order_authority=True, no_provider_effect=True, no_model_fit=True, no_llm_execution=True, no_qpu_execution=True,
                owner_envelope_ref=owner_envelope_ref, assembly_scope_ref=scope.scope_ref, signed_grant=signed,
                preparation_ordinal=1, preparation_natural_key=natural, exact_frozen_plan_ref=payload.exact_frozen_plan_ref,
                assembler_principal=scope.assembler_principal, assembler_audience=scope.assembler_audience,
                allowed_source_selections=scope.source_selections, allowed_control_store_id=scope.control_store_id,
                allowed_control_kinds=scope.allowed_control_kinds, reserved_preparation_limits=scope.preparation_limits,
                aggregate_budget_ref=scope.preparation_limits.aggregate_budget_ref, deadline_clock_and_process=deadline,
                exclusive_expiry=scope.exclusive_expiry_wall_ns, preparation_fence_ref=fence)
            operation = _EvidenceControlBootstrapV1(issuer=self, envelope_entry=entry, request=request, plan=plan,
                grant_record=record, trace_ref=EvidenceHostBindingV1._nonce_ref_v1(self.host, "LP03-TRACE"),
                policies=(), started_cpu_ns=cpu, lifecycle_identity=lifecycle_identity)
            self.operation = operation
            source_original = (operation.source_slice_minted, operation.source_slice_guard)
            self.preparations[record.record_id] = (operation, None, source_original)
            first_lifecycle = self.lifecycle_first_operation is None
            if first_lifecycle:
                self.lifecycle_first_operation = operation
            try:
                self._lock_original_source_custodies_v1(locks)
                _EvidenceIssuerStateV1._load_bootstrap_metadata_v1(self, operation)
                _EvidenceControlBootstrapV1._check_current_v1(operation)
                committed_ref = SQLiteReferenceAdapterV1._evidence_bootstrap_assembly_v1(self.control_store, operation)
                _native_require(operation.commit_state == "COMMITTED_AND_READBACK", "LP03_ASSEMBLY_COMMIT_UNPROVEN")
                _native_require(committed_ref == record.record_id, "LP03_ASSEMBLY_REPLAY_RESOLUTION_UNAVAILABLE")
                handle = object.__new__(EvidenceAssemblyGrantV1)
                handle._owner, handle._grant_ref = self, committed_ref
                lifecycle = ((lifecycle_identity, operation, operation.bootstrap_original,
                              operation.bootstrap_commit_observation, operation.bootstrap_readback_observation, handle)
                             if first_lifecycle else self.lifecycle_original)
                _EvidenceIssuerStateV1._require_lifecycle_original_v1(self, lifecycle, publishing=first_lifecycle)
                _EvidenceControlBootstrapV1._check_current_v1(operation)
                _EvidenceIssuerStateV1._require_lifecycle_original_v1(self, lifecycle, publishing=first_lifecycle)
                self.preparations[committed_ref] = (operation, handle, source_original)
                if first_lifecycle:
                    self.lifecycle_original = lifecycle
                return handle
            except BaseException as error:
                if first_lifecycle:
                    self.lifecycle_unresolved = True
                if operation.failure_root is None:
                    operation.failure_root = error
                try:
                    _EvidenceControlBootstrapV1._observe_failure_accounting_v1(operation)
                except BaseException as accounting_error:
                    operation.failure_accounting_state = "OBSERVATION_UNRESOLVED"
                    operation.failure_unretained = accounting_error
                    operation.failure_capture_failed = True
                raise
            finally:
                self.operation = None

    def __copy__(self):
        raise TypeError("LP03 issuer state cannot be copied")

    def __deepcopy__(self, memo):
        raise TypeError("LP03 issuer state cannot be copied")

    def __reduce_ex__(self, protocol):
        raise TypeError("LP03 issuer state cannot be serialized")


class EvidenceAttemptGrantV1:
    """Original post-lock capability; serialized signatures alone are not this handle."""

    __slots__ = ("_owner", "_attempt", "_grant_ref")

    def __init__(self):
        raise TypeError("attempt grants are issued by the original AGENT_ORCH1")

    @property
    def grant_ref(self):
        return self._grant_ref

    def __copy__(self):
        raise TypeError("LP03 attempt grant cannot be copied")

    def __deepcopy__(self, memo):
        raise TypeError("LP03 attempt grant cannot be copied")

    def __reduce_ex__(self, protocol):
        raise TypeError("LP03 attempt grant cannot be serialized")


class EvidenceAssemblyGrantV1:
    """Original live preparation capability, bound only after durable readback."""

    __slots__ = ("_owner", "_grant_ref")

    def __init__(self):
        raise TypeError("assembly grants are issued by the original AGENT_ORCH1")

    @property
    def grant_ref(self):
        return self._grant_ref

    def __copy__(self):
        raise TypeError("LP03 assembly grant cannot be copied")

    def __deepcopy__(self, memo):
        raise TypeError("LP03 assembly grant cannot be copied")

    def __reduce_ex__(self, protocol):
        raise TypeError("LP03 assembly grant cannot be serialized")
