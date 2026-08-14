"""One parametrized ST12-G existing-owner consumer matrix."""

from __future__ import annotations

from copy import copy
from dataclasses import replace
from pathlib import Path

import pytest

from src.qtt.dashboard.owner_dashboard_validator import (
    validate_st12g_descriptor_candidate,
)
from src.qtt.agents.pr169_agent_orch1_resolvers import (
    resolve_st12g_projection_v2 as resolve_agent,
)
from src.qtt.dashboard.owner_surface_resolver import (
    resolve_st12g_projection_v2 as resolve_dashboard,
)
from src.qtt.pretrade.pr169_pretrade1_resolvers import (
    resolve_st12g_projection_v2 as resolve_pretrade,
)
from src.qtt.readiness.pr169_readiness1_resolvers import (
    resolve_st12g_projection_v2 as resolve_readiness,
)
from src.qtt.service.pr169_svc1_resolvers import (
    resolve_st12g_projection_v2 as resolve_svc,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import (
    ContractValidationError,
    ReasonCode,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.evidence import (
    ComputationEvidenceBundleV1,
    FToGHandoffReferencesV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.existing_owner_projection import (
    ExistingOwnerProjectionCompilerV2,
    ExistingOwnerProjectionCoordinatorV2,
    ST12GBlockerSetStateV2,
    ST12GBlockerStateV2,
    ST12GOwnerProjectionResolutionV2,
    ST12GProjectionAbsenceV2,
    ST12GProjectionBundleV2,
    ST12GProjectionRequestV2,
    ST12GProjectionResolutionStateV2,
    ST12GProjectionResolutionV2,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.input_lock import (
    ImmutableReplayPaperInputLockV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.models import (
    ComputationExecutionContextV1,
    ComputationScopeV1,
    NO_EFFECTS_V1,
    ST12FEvidenceReferenceV1,
    ST12FEvidenceStateV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.serialization import (
    validate_relative_path,
)
from tests.stage1_prediction_markets.qku_computation_control_plane.tranche_g.test_contract_matrix import (
    _BehaviorCase,
    _EvidenceService,
    _ROOT,
    _assert_reason,
    _baseline,
    _binding_baseline,
    _compile,
    _compiler_candidate,
    _descriptor,
    _request,
)
from tools.independent_validate_qku_computation_control_plane_g import (
    validate_projection_field_binding_candidate,
    validate_public_operation_roster_candidate,
    validate_receipt_class_roster_candidate,
    validate_static_architecture_candidate,
    validate_st12g_changed_path_candidate,
)


_HISTORICAL_CONSUMER_CASES = (
    ("ST12-TEST::026", "OWNER_REVIEW_SEGREGATION_AND_HUMAN_ON_LOOP", "PASS"),
    ("ST12-TEST::027", "ACCOUNTABILITY_VIEW_EXACT_LINEAGE_FRESHNESS_LIMITATIONS_AND_ZERO_AUTHORITY", "PASS"),
    ("ST12-TEST::028", "LEARNING_HANDOFF_IMMUTABLE_HISTORY_NO_SELF_PROMOTION", "PASS"),
    ("ST12-TEST::222", "INDEPENDENT_AGENT_PROJECTION_RECONSTRUCTION", "PASS"),
    ("ST12-TEST::226", "INDEPENDENT_LLM_AND_GROUNDING_PROJECTION_RECONSTRUCTION", "PASS"),
    ("ST12-TEST::228", "INDEPENDENT_OPERATIONS_AND_FIVE_CONSUMER_RECONSTRUCTION", "PASS"),
)

_COMPILER_ENTRYPOINT = "src/qtt/stage1_prediction_markets/qku_computation_control_plane/existing_owner_projection.py::ExistingOwnerProjectionCompilerV2.compile_current"
_COORDINATOR_ENTRYPOINT = "src/qtt/stage1_prediction_markets/qku_computation_control_plane/existing_owner_projection.py::ExistingOwnerProjectionCoordinatorV2.resolve"
_DESCRIPTOR_ENTRYPOINT = "src/qtt/dashboard/owner_dashboard_validator.py::validate_st12g_descriptor_candidate"
_STATIC_ENTRYPOINT = "tools/independent_validate_qku_computation_control_plane_g.py::validate_static_architecture_candidate"
_BINDING_ENTRYPOINT = "tools/independent_validate_qku_computation_control_plane_g.py::validate_projection_field_binding_candidate"

_FAIL_CASES_CONSUMER = (
    _BehaviorCase("G-FAIL::046", "PRODUCTION_MUTATION_REJECTION", "_request", "REQUEST_HANDOFF_RECEIPT_REF_NOT_FULL_CANONICAL_G_RECEIPT_REF", "src/qtt/stage1_prediction_markets/qku_computation_control_plane/existing_owner_projection.py::ST12GProjectionRequestV2.__post_init__", "REJECT_SCHEMA_MISMATCH", "SCHEMA_MISMATCH", "NONE"),
    _BehaviorCase("G-FAIL::047", "PRODUCTION_MUTATION_REJECTION", "_request mapping", "REQUEST_CONTAINS_FORBIDDEN_EXPECTED_SOURCE_EPOCH_OR_INPUT_LOCK_FIELD", _COORDINATOR_ENTRYPOINT, "REJECT_SCHEMA_MISMATCH", "SCHEMA_MISMATCH", "NONE"),
    _BehaviorCase("G-FAIL::048", "PRODUCTION_MUTATION_REJECTION", "_request mapping", "REQUEST_CONTAINS_FORBIDDEN_REQUESTED_AT_OR_EVALUATED_AT_FIELD", _COORDINATOR_ENTRYPOINT, "REJECT_SCHEMA_MISMATCH", "SCHEMA_MISMATCH", "NONE"),
    _BehaviorCase("G-FAIL::049", "PRODUCTION_MUTATION_REJECTION", "_current_resolution", "CURRENT_RESOLUTION_CARRIES_PRESENT_BLOCKERS", "src/qtt/stage1_prediction_markets/qku_computation_control_plane/existing_owner_projection.py::ST12GProjectionCoreV2.__post_init__", "REJECT_SCHEMA_MISMATCH", "SCHEMA_MISMATCH", "NONE"),
    _BehaviorCase("G-FAIL::050", "PRODUCTION_MUTATION_REJECTION", "_current_resolution", "STALE_RESOLUTION_CARRIES_CURRENT_PROJECTION_BUNDLE", "src/qtt/stage1_prediction_markets/qku_computation_control_plane/existing_owner_projection.py::ST12GProjectionResolutionV2.__init__", "REJECT_SCHEMA_MISMATCH", "SCHEMA_MISMATCH", "NONE"),
    _BehaviorCase("G-FAIL::051", "PRODUCTION_MUTATION_REJECTION", "_absence", "BLOCKED_RESOLUTION_CARRIES_EXPLICIT_EMPTY_NO_BLOCKERS", "src/qtt/stage1_prediction_markets/qku_computation_control_plane/existing_owner_projection.py::ST12GProjectionAbsenceV2.__post_init__", "REJECT_SCHEMA_MISMATCH", "SCHEMA_MISMATCH", "NONE"),
    _BehaviorCase("G-FAIL::052", "PRODUCTION_MUTATION_REJECTION", "_current_resolution", "CURRENT_CENTRAL_BUNDLE_MISSING_ONE_DIRECT_OWNER_PROJECTION", "src/qtt/stage1_prediction_markets/qku_computation_control_plane/existing_owner_projection.py::ST12GProjectionBundleV2.__post_init__", "REJECT_PARTIAL_OWNER_BUNDLE", "SCHEMA_MISMATCH", "NONE"),
    _BehaviorCase("G-FAIL::053", "PRODUCTION_MUTATION_REJECTION", "_current_resolution", "DIRECT_OWNER_RESOLVER_RECEIVES_WRONG_CONSUMER_CONTRACT", "src/qtt/stage1_prediction_markets/qku_computation_control_plane/existing_owner_projection.py::ST12GOwnerProjectionResolutionV2.__init__", "REJECT_OWNER_TOPOLOGY_MISMATCH", "INPUT_OWNER_MISMATCH", "NONE"),
    _BehaviorCase("G-FAIL::054", "PRODUCTION_MUTATION_REJECTION", "_current_resolution", "DASHBOARD_RESOLVER_RECEIVES_CENTRAL_G_OR_F_INPUT_INSTEAD_OF_SVC1_OWNER_RESOLUTION", "src/qtt/dashboard/owner_surface_resolver.py::resolve_st12g_projection_v2", "REJECT_OWNER_CHAIN_BYPASS", "INPUT_OWNER_MISMATCH", "NONE"),
    _BehaviorCase("G-FAIL::055", "PRODUCTION_MUTATION_REJECTION", "SVC1 stale absence", "DASHBOARD_RESOLVER_CHANGES_SVC1_STALE_OR_BLOCKED_ABSENCE", "src/qtt/stage1_prediction_markets/qku_computation_control_plane/existing_owner_projection.py::ST12GOwnerDashboardEvidenceViewV2.__post_init__", "REJECT_LINEAGE_REWRITE", "SCHEMA_MISMATCH", "NONE"),
    _BehaviorCase("G-FAIL::056", "PRODUCTION_MUTATION_REJECTION", "existing owner path", "OWNER_ARTIFACT_WRITE_OUTSIDE_EXISTING_OWNER_PREFIX", "src/qtt/stage1_prediction_markets/qku_computation_control_plane/serialization.py::validate_relative_path", "REJECT_PATH_SCOPE", "PATH_UNSAFE", "NONE"),
    _BehaviorCase("G-FAIL::057", "PRODUCTION_MUTATION_REJECTION", "generated DASH1 descriptor", "GENERATED_CONTRACT_DESCRIPTOR_CONTAINS_FABRICATED_RUNTIME_EVIDENCE_INSTANCE", _DESCRIPTOR_ENTRYPOINT, "REJECT_EVIDENCE_FABRICATION", "ST12F_FIXTURE_NOT_EVIDENCE", "NONE"),
    _BehaviorCase("G-FAIL::058", "PRODUCTION_MUTATION_REJECTION", "generated DASH1 descriptor", "GENERATED_DESCRIPTOR_HAS_EXTRA_OR_MISSING_FIELD", _DESCRIPTOR_ENTRYPOINT, "REJECT_SCHEMA_MISMATCH", "SCHEMA_MISMATCH", "NONE"),
    _BehaviorCase("G-FAIL::059", "STATIC_ARCHITECTURE_MUTATION_DETECTION", "projection_field_bindings.jsonl", "CONSUMER_FIELD_BINDING_REFERENCES_UNKNOWN_SOURCE_FIELD", _BINDING_ENTRYPOINT, "REJECT_SCHEMA_MISMATCH", "SCHEMA_MISMATCH", "NONE"),
    _BehaviorCase("G-FAIL::060", "STATIC_ARCHITECTURE_MUTATION_DETECTION", "existing_owner_projection.py", "FILESYSTEM_READ_DURING_PURE_COMPILER_OR_DIRECT_OWNER_MAPPER_CALL", _STATIC_ENTRYPOINT, "REJECT_RUNTIME_EFFECT_FORBIDDEN", "RUNTIME_EFFECT_FORBIDDEN", "NONE"),
    _BehaviorCase("G-FAIL::061", "STATIC_ARCHITECTURE_MUTATION_DETECTION", "existing_owner_projection.py", "NETWORK_OR_PROVIDER_CALL_DURING_G_COMPILATION_OR_OWNER_MAPPING", _STATIC_ENTRYPOINT, "REJECT_PROVIDER_ACCESS", "DIRECT_PROVIDER_FORBIDDEN", "NONE"),
    _BehaviorCase("G-FAIL::062", "PRODUCTION_MUTATION_REJECTION", "generated DASH1 descriptor", "OWNER_NATURAL_SLOT_SAME_ID_DIFFERENT_DESCRIPTOR", _DESCRIPTOR_ENTRYPOINT, "REJECT_IDEMPOTENCY_CONFLICT", "IDEMPOTENCY_CONFLICT", "NONE"),
    _BehaviorCase("G-FAIL::063", "STATIC_ARCHITECTURE_MUTATION_DETECTION", "existing_owner_projection.py", "CENTRAL_COMPILER_INTRODUCES_CACHE_DATABASE_CURRENT_POINTER_OR_MUTABLE_STATE", _STATIC_ENTRYPOINT, "REJECT_DUPLICATE_AUTHORITY", "RUNTIME_EFFECT_FORBIDDEN", "NONE"),
    _BehaviorCase("G-FAIL::064", "STATIC_ARCHITECTURE_MUTATION_DETECTION", "QKUComputationControlPlaneV1 public roster", "NEW_PUBLIC_QKU_OPERATION_ADDED_FOR_G", "tools/independent_validate_qku_computation_control_plane_g.py::validate_public_operation_roster_candidate", "REJECT_OPERATION_AUTHORITY_EXPANSION", "OPERATION_NOT_ALLOWED", "NONE"),
    _BehaviorCase("G-FAIL::065", "STATIC_ARCHITECTURE_MUTATION_DETECTION", "ST12FReceiptClassV1 roster", "NEW_DURABLE_RECEIPT_CLASS_ADDED_FOR_G", "tools/independent_validate_qku_computation_control_plane_g.py::validate_receipt_class_roster_candidate", "REJECT_RECEIPT_AUTHORITY_EXPANSION", "SCHEMA_MISMATCH", "NONE"),
    _BehaviorCase("G-FAIL::066", "STATIC_ARCHITECTURE_MUTATION_DETECTION", "ST12-G exact write scope", "READ_ONLY_ST12F_HANDOFF_OR_RECEIPT_OWNER_MUTATED_BY_G", "tools/independent_validate_qku_computation_control_plane_g.py::validate_st12g_changed_path_candidate", "REJECT_PREDECESSOR_MUTATION", "PATH_UNSAFE", "NONE"),
    _BehaviorCase("G-FAIL::067", "PRODUCTION_MUTATION_REJECTION", "_baseline", "CURRENT_D_REFERENCE_UNAVAILABLE_STALE_CONFLICTING_OR_NOT_CURRENT", _COMPILER_ENTRYPOINT, "RETURN_BLOCKED_NO_AUTHORITY", "EVIDENCE_REFERENCE_UNAVAILABLE_STALE_CONFLICTING_OR_SCOPE_MISMATCH", "NONE"),
    _BehaviorCase("G-FAIL::068", "PRODUCTION_MUTATION_REJECTION", "_baseline", "CONTEXT_INPUT_SNAPSHOT_ID_DIFFERS_FROM_DURABLE_INPUT_LOCK", _COMPILER_ENTRYPOINT, "REJECT_CONTEXT_SCOPE_MISMATCH", "INPUT_SCOPE_MISMATCH", "NONE"),
    _BehaviorCase("G-FAIL::069", "PRODUCTION_MUTATION_REJECTION", "_baseline", "CONTEXT_MARKET_VENUE_OR_INSTRUMENT_SCOPE_OUTSIDE_DURABLE_INPUT_LOCK", _COMPILER_ENTRYPOINT, "REJECT_CONTEXT_SCOPE_MISMATCH", "INPUT_SCOPE_MISMATCH", "NONE"),
    _BehaviorCase("G-FAIL::070", "PRODUCTION_MUTATION_REJECTION", "_baseline", "TRUSTED_EXECUTION_CONTEXT_IS_STALE", _COORDINATOR_ENTRYPOINT, "RETURN_STALE_NO_AUTHORITY", "STALE_CONTEXT", "NONE"),
)

_DESCRIPTOR_FIELDS = {
    "descriptor_id",
    "contract_version",
    "consumer_id",
    "contract_type",
    "source_contract_manifest_ref",
    "canonical_owner_ref",
    "runtime_instance_state",
    "manual_edit_allowed",
    "runtime_effect_allowed",
    "write_authority",
    "downstream_route_refs",
}


def _current_resolution() -> ST12GProjectionResolutionV2:
    context = _baseline()[0]
    return ST12GProjectionResolutionV2.current(
        resolution_id="ST12G::RESOLUTION::CONSUMER",
        request_id="REQUEST::CONSUMER",
        context_id=context.context_id,
        evaluated_at=context.as_of,
        projection_bundle=_compile(),
    )


def _all_owner_resolutions(
    current: ST12GProjectionResolutionV2 | None = None,
):
    current = current or _current_resolution()
    return (
        resolve_readiness(current),
        resolve_pretrade(current),
        resolve_agent(current),
        resolve_svc(current),
    )


def _absence(
    state: ST12GProjectionResolutionStateV2,
    reason: ReasonCode,
) -> ST12GProjectionAbsenceV2:
    context = _baseline()[0]
    return ST12GProjectionAbsenceV2(
        absence_id=f"ST12G::ABSENCE::{state.value}",
        evaluation_context_id=context.context_id,
        evaluated_at=context.as_of,
        state=state,
        reason_codes=(reason,),
        source_handoff_receipt_ref_or_explicit_absence=(
            _request().source_handoff_receipt_ref
        ),
    )


def _run_historical_consumer(case_id: str) -> None:
    current = _current_resolution()
    owner_resolutions = _all_owner_resolutions(current)
    readiness, pretrade, agent, svc = owner_resolutions
    if case_id == "ST12-TEST::026":
        assert agent.projection.owner_review_route == "OWNER_REVIEW_REQUIRED_FOR_ANY_LATER_AUTHORITY"
        assert agent.projection.allowed_operation == "REVIEW_PROJECTED_EVIDENCE_AND_ROUTE_TYPED_RESPONSE"
    elif case_id == "ST12-TEST::027":
        cores = tuple(owner.projection.core for owner in owner_resolutions)
        assert all(core is cores[0] for core in cores)
        assert cores[0].source_and_provenance_refs == _baseline()[3].source_and_provenance_refs
        assert cores[0].valid_until == _baseline()[2].valid_until
        assert cores[0].no_effect_flags is NO_EFFECTS_V1
    elif case_id == "ST12-TEST::028":
        assert agent.projection.self_promotion_allowed is False
        assert agent.projection.historical_rewrite_allowed is False
    elif case_id == "ST12-TEST::222":
        assert agent.projection is current.projection_bundle.agent_orch
        assert agent.projection.core is readiness.projection.core
    elif case_id == "ST12-TEST::226":
        assert svc.projection.fake_receipt_allowed is False
        assert svc.projection.runtime_execution_allowed is False
        assert agent.projection.task_class == "READ_ONLY_EVIDENCE_REVIEW_HANDOFF"
    elif case_id == "ST12-TEST::228":
        dashboard = resolve_dashboard(svc)
        assert tuple(owner.consumer_id for owner in owner_resolutions) == (
            "READINESS1",
            "PRETRADE1",
            "AGENT_ORCH1",
            "SVC1",
        )
        assert dashboard.consumer_id == "DASH1_UI1"
        assert dashboard.source_svc_projection_id_or_explicit_absence == svc.projection.projection_id
        assert dashboard.direct_f_binding_allowed is False
    else:
        raise AssertionError(case_id)


def _run_consumer_failure(case_id: str, trigger: str, expected: str) -> None:
    context, lock, handoff, bundle, reference, owners = _baseline()
    current = _current_resolution()
    if case_id == "G-FAIL::046":
        _assert_reason(expected, lambda: replace(_request(), source_handoff_receipt_ref="G-HANDOFF::SHORT"))
    elif case_id in {"G-FAIL::047", "G-FAIL::048"}:
        request = _request()
        candidate = {
            "request_id": request.request_id,
            "context": request.context,
            "source_handoff_receipt_ref": request.source_handoff_receipt_ref,
            "causation_id": request.causation_id,
            "correlation_id": request.correlation_id,
        }
        if case_id == "G-FAIL::047":
            candidate["expected_source_epoch_refs"] = handoff.source_epoch_refs
            candidate["expected_input_lock_id"] = lock.input_lock_id
        else:
            candidate["requested_at"] = context.as_of
            candidate["evaluated_at"] = context.as_of
        _assert_reason(
            expected,
            lambda: ExistingOwnerProjectionCoordinatorV2(
                _EvidenceService(),
                owners,
            ).resolve(candidate),
        )
    elif case_id == "G-FAIL::049":
        blockers = ST12GBlockerStateV2(
            ST12GBlockerSetStateV2.PRESENT_TYPED_BLOCKERS,
            (ReasonCode.SCHEMA_MISMATCH,),
        )
        _assert_reason(expected, lambda: replace(current.projection_bundle.core, bundle_blocker_state=blockers))
    elif case_id == "G-FAIL::050":
        _assert_reason(
            expected,
            lambda: ST12GProjectionResolutionV2(
                resolution_id="ST12G::RESOLUTION::BAD",
                request_id="REQUEST::BAD",
                context_id=context.context_id,
                evaluated_at=context.as_of,
                resolution_state=ST12GProjectionResolutionStateV2.UNAVAILABLE_STALE_NO_AUTHORITY,
                payload=current.projection_bundle,
            ),
        )
    elif case_id == "G-FAIL::051":
        _assert_reason(
            expected,
            lambda: ST12GProjectionAbsenceV2(
                absence_id="ST12G::ABSENCE::BAD",
                evaluation_context_id=context.context_id,
                evaluated_at=context.as_of,
                state=ST12GProjectionResolutionStateV2.UNAVAILABLE_BLOCKED_NO_AUTHORITY,
                reason_codes=(),
                source_handoff_receipt_ref_or_explicit_absence="EXPLICIT_ABSENCE",
            ),
        )
    elif case_id == "G-FAIL::052":
        _assert_reason(expected, lambda: replace(current.projection_bundle, svc=None))
    elif case_id == "G-FAIL::053":
        _assert_reason(
            expected,
            lambda: ST12GOwnerProjectionResolutionV2(
                consumer_id="READINESS1",
                source_request_id=current.request_id,
                resolution_state=current.resolution_state,
                payload=current.projection_bundle.svc,
            ),
        )
    elif case_id == "G-FAIL::054":
        _assert_reason(expected, lambda: resolve_dashboard(current))
        _assert_reason(expected, lambda: resolve_dashboard(handoff))
    elif case_id == "G-FAIL::055":
        absence = _absence(
            ST12GProjectionResolutionStateV2.UNAVAILABLE_STALE_NO_AUTHORITY,
            ReasonCode.ST12F_BUNDLE_STALE,
        )
        svc_resolution = ST12GOwnerProjectionResolutionV2(
            consumer_id="SVC1",
            source_request_id="REQUEST::ABSENCE",
            resolution_state=absence.state,
            payload=absence,
        )
        dashboard = resolve_dashboard(svc_resolution)
        assert svc_resolution.absence is absence
        _assert_reason(
            expected,
            lambda: replace(
                dashboard,
                source_svc_projection_id_or_explicit_absence=(
                    _current_resolution().projection_bundle.svc.projection_id
                ),
            ),
        )
    elif case_id == "G-FAIL::056":
        _assert_reason(expected, lambda: validate_relative_path("../other-owner/output.json"))
    elif case_id == "G-FAIL::057":
        bad = _descriptor("DASH1_UI1") | {"runtime_evidence": {"profit": 1}}
        _assert_reason(
            expected,
            lambda: validate_st12g_descriptor_candidate(bad),
        )
    elif case_id == "G-FAIL::058":
        bad = dict(_descriptor("DASH1_UI1"))
        bad.pop("write_authority")
        _assert_reason(
            expected,
            lambda: validate_st12g_descriptor_candidate(bad),
        )
    elif case_id == "G-FAIL::059":
        bad_binding = _binding_baseline() | {
            "source_field_or_rule": "unknown_source_field"
        }
        _assert_reason(
            expected,
            lambda: validate_projection_field_binding_candidate(bad_binding),
        )
    elif case_id == "G-FAIL::060":
        candidate = _compiler_candidate(
            "    filesystem_probe = Path(\"candidate\").read_text()"
        )
        _assert_reason(
            expected,
            lambda: validate_static_architecture_candidate(candidate),
        )
    elif case_id == "G-FAIL::061":
        candidate = _compiler_candidate(
            "    provider_probe = requests.request(\"GET\", \"https://provider.invalid\")"
        ).replace(
            "from __future__ import annotations",
            "from __future__ import annotations\nimport requests",
            1,
        )
        _assert_reason(
            expected,
            lambda: validate_static_architecture_candidate(candidate),
        )
    elif case_id == "G-FAIL::062":
        original = _descriptor("DASH1_UI1")
        changed = original | {"downstream_route_refs": ["DIFFERENT"]}
        _assert_reason(
            expected,
            lambda: validate_st12g_descriptor_candidate(
                changed,
                existing=original,
            ),
        )
    elif case_id == "G-FAIL::063":
        candidate = _compiler_candidate("    cache = {}")
        _assert_reason(
            expected,
            lambda: validate_static_architecture_candidate(candidate),
        )
    elif case_id == "G-FAIL::064":
        from src.qtt.stage1_prediction_markets.qku_computation_control_plane.service import QKUComputationControlPlaneV1

        public = {
            name
            for name, value in QKUComputationControlPlaneV1.__dict__.items()
            if callable(value) and not name.startswith("_")
        }
        _assert_reason(
            expected,
            lambda: validate_public_operation_roster_candidate(
                (*sorted(public), "resolve_st12g_projection_v2")
            ),
        )
    elif case_id == "G-FAIL::065":
        from src.qtt.stage1_prediction_markets.qku_computation_control_plane.receipts import ST12FReceiptClassV1

        _assert_reason(
            expected,
            lambda: validate_receipt_class_roster_candidate(
                (*(member.name for member in ST12FReceiptClassV1), "ST12G_PROJECTION")
            ),
        )
    elif case_id == "G-FAIL::066":
        _assert_reason(
            expected,
            lambda: validate_st12g_changed_path_candidate(
                "src/qtt/stage1_prediction_markets/qku_computation_control_plane/evidence.py"
            ),
        )
    elif case_id == "G-FAIL::067":
        unavailable = copy(reference)
        object.__setattr__(
            unavailable,
            "evidence_state",
            ST12FEvidenceStateV1.EVIDENCE_REFERENCE_STALE,
        )
        _assert_reason(expected, lambda: _compile(reference=unavailable))
    elif case_id == "G-FAIL::068":
        bad_scope = replace(context.scope, input_snapshot_id="ST12F-LOCK::OTHER")
        bad_context = replace(context, scope=bad_scope)
        _assert_reason(expected, lambda: _compile(context=bad_context))
    elif case_id == "G-FAIL::069":
        bad_scope = replace(context.scope, market_scope_id="MARKET::OUTSIDE")
        bad_context = replace(context, scope=bad_scope)
        _assert_reason(expected, lambda: _compile(context=bad_context))
    elif case_id == "G-FAIL::070":
        stale_context = replace(
            context,
            observed_at=context.as_of - context.maximum_age - context.maximum_age,
        )
        service = _EvidenceService()
        result = ExistingOwnerProjectionCoordinatorV2(service, owners).resolve(
            _request(stale_context)
        )
        assert result.resolution_state is ST12GProjectionResolutionStateV2.UNAVAILABLE_STALE_NO_AUTHORITY
        assert result.absence.reason_codes == (ReasonCode.STALE_CONTEXT,)
    else:
        raise AssertionError((case_id, trigger, expected, lock, bundle))


_CONSUMER_CASES = (*_HISTORICAL_CONSUMER_CASES, *_FAIL_CASES_CONSUMER)


@pytest.mark.parametrize(
    "case",
    _CONSUMER_CASES,
    ids=[row[0] for row in _CONSUMER_CASES],
)
def test_st12g_consumer_case(case: tuple[str, ...] | _BehaviorCase) -> None:
    if not isinstance(case, _BehaviorCase):
        _run_historical_consumer(case[0])
    else:
        assert case.verification_mode in {
            "PRODUCTION_MUTATION_REJECTION",
            "EXISTING_OWNER_REJECTION_PROPAGATION",
            "STATIC_ARCHITECTURE_MUTATION_DETECTION",
            "DETERMINISTIC_PRESERVATION_PROOF",
        }
        assert case.valid_baseline_factory
        assert case.production_entrypoint
        assert case.expected_terminal_outcome
        _run_consumer_failure(
            case.case_id,
            case.declared_mutation_action,
            case.expected_reason_code,
        )
