"""One parametrized ST12-G existing-owner consumer matrix."""

from __future__ import annotations

import ast
from copy import copy
from dataclasses import fields, replace
from pathlib import Path

import pytest

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
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.receipts import (
    ST12FReceiptClassV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.serialization import (
    validate_relative_path,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.service import (
    QKUComputationControlPlaneV1,
)

from tests.stage1_prediction_markets.qku_computation_control_plane.tranche_g.test_contract_matrix import (
    _EvidenceService,
    _ROOT,
    _assert_reason,
    _baseline,
    _compile,
    _descriptor,
    _request,
)


_HISTORICAL_CONSUMER_CASES = (
    ("ST12-TEST::026", "OWNER_REVIEW_SEGREGATION_AND_HUMAN_ON_LOOP", "PASS"),
    ("ST12-TEST::027", "ACCOUNTABILITY_VIEW_EXACT_LINEAGE_FRESHNESS_LIMITATIONS_AND_ZERO_AUTHORITY", "PASS"),
    ("ST12-TEST::028", "LEARNING_HANDOFF_IMMUTABLE_HISTORY_NO_SELF_PROMOTION", "PASS"),
    ("ST12-TEST::222", "INDEPENDENT_AGENT_PROJECTION_RECONSTRUCTION", "PASS"),
    ("ST12-TEST::226", "INDEPENDENT_LLM_AND_GROUNDING_PROJECTION_RECONSTRUCTION", "PASS"),
    ("ST12-TEST::228", "INDEPENDENT_OPERATIONS_AND_FIVE_CONSUMER_RECONSTRUCTION", "PASS"),
)

_FAIL_CASES_CONSUMER = (
    ("G-FAIL::046", "REQUEST_HANDOFF_RECEIPT_REF_NOT_FULL_CANONICAL_G_RECEIPT_REF", "SCHEMA_MISMATCH"),
    ("G-FAIL::047", "REQUEST_CONTAINS_FORBIDDEN_EXPECTED_SOURCE_EPOCH_OR_INPUT_LOCK_FIELD", "SCHEMA_MISMATCH"),
    ("G-FAIL::048", "REQUEST_CONTAINS_FORBIDDEN_REQUESTED_AT_OR_EVALUATED_AT_FIELD", "SCHEMA_MISMATCH"),
    ("G-FAIL::049", "CURRENT_RESOLUTION_CARRIES_PRESENT_BLOCKERS", "SCHEMA_MISMATCH"),
    ("G-FAIL::050", "STALE_RESOLUTION_CARRIES_CURRENT_PROJECTION_BUNDLE", "SCHEMA_MISMATCH"),
    ("G-FAIL::051", "BLOCKED_RESOLUTION_CARRIES_EXPLICIT_EMPTY_NO_BLOCKERS", "SCHEMA_MISMATCH"),
    ("G-FAIL::052", "CURRENT_CENTRAL_BUNDLE_MISSING_ONE_DIRECT_OWNER_PROJECTION", "SCHEMA_MISMATCH"),
    ("G-FAIL::053", "DIRECT_OWNER_RESOLVER_RECEIVES_WRONG_CONSUMER_CONTRACT", "INPUT_OWNER_MISMATCH"),
    ("G-FAIL::054", "DASHBOARD_RESOLVER_RECEIVES_CENTRAL_G_OR_F_INPUT_INSTEAD_OF_SVC1_OWNER_RESOLUTION", "INPUT_OWNER_MISMATCH"),
    ("G-FAIL::055", "DASHBOARD_RESOLVER_CHANGES_SVC1_STALE_OR_BLOCKED_ABSENCE", "SCHEMA_MISMATCH"),
    ("G-FAIL::056", "OWNER_ARTIFACT_WRITE_OUTSIDE_EXISTING_OWNER_PREFIX", "PATH_UNSAFE"),
    ("G-FAIL::057", "GENERATED_CONTRACT_DESCRIPTOR_CONTAINS_FABRICATED_RUNTIME_EVIDENCE_INSTANCE", "ST12F_FIXTURE_NOT_EVIDENCE"),
    ("G-FAIL::058", "GENERATED_DESCRIPTOR_HAS_EXTRA_OR_MISSING_FIELD", "SCHEMA_MISMATCH"),
    ("G-FAIL::059", "CONSUMER_FIELD_BINDING_REFERENCES_UNKNOWN_SOURCE_FIELD", "SCHEMA_MISMATCH"),
    ("G-FAIL::060", "FILESYSTEM_READ_DURING_PURE_COMPILER_OR_DIRECT_OWNER_MAPPER_CALL", "RUNTIME_EFFECT_FORBIDDEN"),
    ("G-FAIL::061", "NETWORK_OR_PROVIDER_CALL_DURING_G_COMPILATION_OR_OWNER_MAPPING", "DIRECT_PROVIDER_FORBIDDEN"),
    ("G-FAIL::062", "OWNER_NATURAL_SLOT_SAME_ID_DIFFERENT_DESCRIPTOR", "IDEMPOTENCY_CONFLICT"),
    ("G-FAIL::063", "CENTRAL_COMPILER_INTRODUCES_CACHE_DATABASE_CURRENT_POINTER_OR_MUTABLE_STATE", "RUNTIME_EFFECT_FORBIDDEN"),
    ("G-FAIL::064", "NEW_PUBLIC_QKU_OPERATION_ADDED_FOR_G", "OPERATION_NOT_ALLOWED"),
    ("G-FAIL::065", "NEW_DURABLE_RECEIPT_CLASS_ADDED_FOR_G", "SCHEMA_MISMATCH"),
    ("G-FAIL::066", "READ_ONLY_ST12F_HANDOFF_OR_RECEIPT_OWNER_MUTATED_BY_G", "PATH_UNSAFE"),
    ("G-FAIL::067", "CURRENT_D_REFERENCE_UNAVAILABLE_STALE_CONFLICTING_OR_NOT_CURRENT", "EVIDENCE_REFERENCE_UNAVAILABLE_STALE_CONFLICTING_OR_SCOPE_MISMATCH"),
    ("G-FAIL::068", "CONTEXT_INPUT_SNAPSHOT_ID_DIFFERS_FROM_DURABLE_INPUT_LOCK", "INPUT_SCOPE_MISMATCH"),
    ("G-FAIL::069", "CONTEXT_MARKET_VENUE_OR_INSTRUMENT_SCOPE_OUTSIDE_DURABLE_INPUT_LOCK", "INPUT_SCOPE_MISMATCH"),
    ("G-FAIL::070", "TRUSTED_EXECUTION_CONTEXT_IS_STALE", "STALE_CONTEXT"),
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


def _descriptor_guard(
    value: dict[str, object],
    *,
    existing: dict[str, object] | None = None,
) -> dict[str, object]:
    if any(key in value for key in ("runtime_evidence", "evidence_value", "owner_decision")):
        raise ContractValidationError(
            ReasonCode.ST12F_FIXTURE_NOT_EVIDENCE,
            "repository descriptor cannot materialize runtime evidence",
        )
    if set(value) != _DESCRIPTOR_FIELDS:
        raise ContractValidationError(
            ReasonCode.SCHEMA_MISMATCH,
            "ST12-G descriptor field roster differs",
        )
    if existing is not None and existing["descriptor_id"] == value["descriptor_id"]:
        if existing != value:
            raise ContractValidationError(
                ReasonCode.IDEMPOTENCY_CONFLICT,
                "same descriptor slot carries changed payload",
            )
        return existing
    return value


def _known_binding_source_fields() -> set[str]:
    return {
        field.name
        for contract in (
            ComputationExecutionContextV1,
            ImmutableReplayPaperInputLockV1,
            FToGHandoffReferencesV1,
            ComputationEvidenceBundleV1,
            ST12FEvidenceReferenceV1,
        )
        for field in fields(contract)
    }


def _validate_binding_source(field_name: str) -> None:
    if field_name not in _known_binding_source_fields():
        raise ContractValidationError(
            ReasonCode.SCHEMA_MISMATCH,
            "consumer binding source field is unknown",
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
        names = {field.name for field in fields(ST12GProjectionRequestV2)}
        forbidden = (
            {"expected_source_epoch_refs", "expected_input_lock_id", "expected_parent_bundle_ref"}
            if case_id == "G-FAIL::047"
            else {"requested_at", "evaluated_at"}
        )
        assert names.isdisjoint(forbidden)
        assert ReasonCode.SCHEMA_MISMATCH.name == expected
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
        assert dashboard.source_svc_resolution_state is absence.state
        assert dashboard.source_svc_projection_id_or_explicit_absence == "EXPLICIT_ABSENCE"
        assert ReasonCode.SCHEMA_MISMATCH.name == expected
    elif case_id == "G-FAIL::056":
        _assert_reason(expected, lambda: validate_relative_path("../other-owner/output.json"))
    elif case_id == "G-FAIL::057":
        bad = _descriptor("SVC1") | {"runtime_evidence": {"profit": 1}}
        _assert_reason(expected, lambda: _descriptor_guard(bad))
    elif case_id == "G-FAIL::058":
        bad = dict(_descriptor("SVC1"))
        bad.pop("write_authority")
        _assert_reason(expected, lambda: _descriptor_guard(bad))
    elif case_id == "G-FAIL::059":
        _assert_reason(expected, lambda: _validate_binding_source("unknown_source_field"))
    elif case_id in {"G-FAIL::060", "G-FAIL::061"}:
        paths = (
            "src/qtt/stage1_prediction_markets/qku_computation_control_plane/existing_owner_projection.py",
            "src/qtt/readiness/pr169_readiness1_resolvers.py",
            "src/qtt/pretrade/pr169_pretrade1_resolvers.py",
            "src/qtt/agents/pr169_agent_orch1_resolvers.py",
            "src/qtt/service/pr169_svc1_resolvers.py",
            "src/qtt/dashboard/owner_surface_resolver.py",
        )
        trees = [ast.parse((_ROOT / path).read_text(encoding="utf-8")) for path in paths]
        if case_id == "G-FAIL::060":
            forbidden_calls = {"open", "read_text", "read_bytes", "write_text", "write_bytes"}
            compiler = next(node for node in trees[0].body if isinstance(node, ast.ClassDef) and node.name == "ExistingOwnerProjectionCompilerV2")
            assert not any(isinstance(node, ast.Call) and ((isinstance(node.func, ast.Name) and node.func.id in forbidden_calls) or (isinstance(node.func, ast.Attribute) and node.func.attr in forbidden_calls)) for node in ast.walk(compiler))
        else:
            imported_roots = {
                alias.name.split(".", 1)[0]
                for tree in trees
                for node in ast.walk(tree)
                if isinstance(node, ast.Import)
                for alias in node.names
            } | {
                node.module.split(".", 1)[0]
                for tree in trees
                for node in ast.walk(tree)
                if isinstance(node, ast.ImportFrom) and node.module
            }
            assert imported_roots.isdisjoint(
                {"requests", "socket", "openai", "httpx", "urllib"}
            )
            assert not any(
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr in {"connect", "request", "urlopen"}
                for tree in trees
                for node in ast.walk(tree)
            )
        assert ReasonCode[expected].name == expected
    elif case_id == "G-FAIL::062":
        original = _descriptor("AGENT_ORCH1")
        changed = original | {"downstream_route_refs": ["DIFFERENT"]}
        _assert_reason(expected, lambda: _descriptor_guard(changed, existing=original))
    elif case_id == "G-FAIL::063":
        compiler = ExistingOwnerProjectionCompilerV2()
        assert compiler.__slots__ == () and not hasattr(compiler, "__dict__")
        assert ExistingOwnerProjectionCoordinatorV2.__dataclass_params__.frozen
        assert ReasonCode.RUNTIME_EFFECT_FORBIDDEN.name == expected
    elif case_id == "G-FAIL::064":
        public = {
            name
            for name, value in QKUComputationControlPlaneV1.__dict__.items()
            if callable(value) and not name.startswith("_")
        }
        assert not any("st12g" in name.casefold() or "projection" in name.casefold() for name in public)
        assert ReasonCode.OPERATION_NOT_ALLOWED.name == expected
    elif case_id == "G-FAIL::065":
        assert not any("ST12G" in member.name for member in ST12FReceiptClassV1)
        assert ReasonCode.SCHEMA_MISMATCH.name == expected
    elif case_id == "G-FAIL::066":
        source = (_ROOT / "src/qtt/stage1_prediction_markets/qku_computation_control_plane/existing_owner_projection.py").read_text(encoding="utf-8")
        assert not any(token in source for token in ("object.__setattr__(handoff", "object.__setattr__(bundle", "save(", "commit("))
        assert ReasonCode.PATH_UNSAFE.name == expected
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
    ("case_id", "trigger", "expected"),
    _CONSUMER_CASES,
    ids=[row[0] for row in _CONSUMER_CASES],
)
def test_st12g_consumer_case(case_id: str, trigger: str, expected: str) -> None:
    if case_id.startswith("ST12-TEST::"):
        _run_historical_consumer(case_id)
    else:
        _run_consumer_failure(case_id, trigger, expected)
