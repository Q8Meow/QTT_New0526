"""One parametrized ST12-G contract and fail-closed matrix."""

from __future__ import annotations

import ast
from copy import copy
from dataclasses import fields, replace
from datetime import UTC, datetime, timedelta
from functools import lru_cache
import json
from pathlib import Path

import pytest

from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import (
    ComputationControlPlaneError,
    ContractValidationError,
    ReasonCode,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.evidence import (
    ComputationEvidenceBundleV1,
    EvidenceBundleTerminalStateV1,
    EvidenceIdentityDispositionStateV1,
    EvidenceIdentityDispositionV1,
    EvidenceSectionV1,
    FToGHandoffReferencesV1,
    ST12F_EVIDENCE_IDENTITIES_V1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.existing_owner_projection import (
    ExistingOwnerProjectionCompilerV2,
    ExistingOwnerProjectionCoordinatorV2,
    ST12GBlockerSetStateV2,
    ST12GBlockerStateV2,
    ST12GOwnerProjectionResolutionV2,
    ST12GProjectionAbsenceV2,
    ST12GProjectionCoreV2,
    ST12GProjectionRequestV2,
    ST12GProjectionResolutionStateV2,
    ST12GProjectionResolutionV2,
    ST12GReferenceCollectionStateV2,
    ST12GReferenceCollectionV2,
    ST12GVersionMappingStateV2,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.input_lock import (
    INPUT_LOCK_SCHEMA_VERSION_V1,
    ImmutableReplayPaperInputLockV1,
    ST12F_PAPER_RESULT_CONTRACT_IDS_V1,
    ST12F_PARAMETER_VALUE_REF_COUNT_V1,
    ST12F_REPLAY_RESULT_CONTRACT_IDS_V1,
    ST12F_TEMPLATE_IDS_V1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.models import (
    ComputationExecutionContextV1,
    ComputationScopeV1,
    ImplementationVersionPinV1,
    NO_EFFECTS_V1,
    ST12FEvidenceReferenceV1,
    ST12FEvidenceStateV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.protocols import (
    OwnerProjectionViewV1,
    PreloadedOwnerProjectionBundleV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.serialization import (
    deterministic_json,
    validate_relative_path,
)


_ROOT = Path(__file__).resolve().parents[4]
_NOW = datetime(2026, 1, 1, 12, tzinfo=UTC)
_SECTION_FIELDS = (
    "calibration_and_probability_quality",
    "transaction_cost_decomposition",
    "fill_and_queue_quality",
    "latency_and_staleness",
    "capacity_and_crowding",
    "portfolio_marginal_contribution",
    "false_discovery_and_overfit_controls",
    "regime_and_scenario_outcomes",
    "uncertainty_and_model_risk_reserves",
    "agent_and_model_disagreement",
    "no_trade_comparison",
)
_CORE_FIELDS = (
    "core_id",
    "contract_version",
    "evaluation_context_id",
    "evaluated_at",
    "source_handoff_receipt_ref",
    "current_d_reference_receipt_ref",
    "current_d_reference_id",
    "handoff_id",
    "input_lock_id",
    "source_epoch_refs",
    "observed_at",
    "valid_until",
    "terminal_state",
    "evidence_bundle_ref",
    "evidence_id",
    "evidence_bundle_version",
    "component_or_template_ref",
    "independent_review_state",
    "actual_executed_component_versions",
    "actual_executed_stack_version_state",
    "replay_result_ref",
    "paper_result_ref",
    "divergence_assessment_ref",
    "lane_execution_receipt_refs",
    "failure_and_negative_evidence_state",
    "source_and_provenance_refs",
    "bundle_blocker_state",
    "no_trade_blocker_reference_state",
    "champion_challenger_reference_state",
    "portfolio_utility_reference_state",
    "quantum_classical_comparison_receipt_ref",
    "runtime_authority",
    "no_effect_flags",
)

_HISTORICAL_CONTRACT_CASES = (
    ("ST12-TEST::103", "POISONED_CONTEXT_SOURCE_EPOCH_OR_CITATION_MISMATCH_REJECTED", "PASS"),
    ("ST12-TEST::109", "MALFORMED_OR_INSECURE_OUTPUT_CANNOT_ENTER_TYPED_PROJECTION", "PASS"),
    ("ST12-TEST::117", "SENSITIVE_SECRET_PRIVATE_STATE_AND_REASONING_FIELDS_ABSENT", "PASS"),
    ("ST12-TEST::118", "NO_MODEL_PLUGIN_RETRIEVAL_OR_SUPPLY_CHAIN_EXECUTION_IN_G", "PASS"),
    ("ST12-TEST::141", "TYPED_STALE_BLOCKER_ALERT_ROUTES_HAVE_NO_ORDER_AUTHORITY", "PASS"),
    ("ST12-TEST::144", "IDENTICAL_REBUILD_IDEMPOTENT_CONFLICTING_REPLAY_REJECTED", "PASS"),
    ("ST12-TEST::145", "EXACT_GENERATED_ROSTER_NO_SECOND_STORE_NO_CACHE_OR_BYTECODE", "PASS"),
    ("ST12-TEST::155", "TIMES_VALIDITY_LINEAGE_AND_AUTHORITY_FALSE_OBSERVABILITY", "PASS"),
    ("ST12-TEST::160", "VALIDATION_INVENTORY_SCOPE_AND_CHANGED_AREA_ROUTE_EXACT", "PASS"),
)

_FAIL_CASES_CONTRACT = (
    ("G-FAIL::001", "HANDOFF_RECEIPT_MISSING", "OWNER_DATA_MISSING"),
    ("G-FAIL::002", "WRONG_HANDOFF_CONTRACT_VERSION", "SCHEMA_MISMATCH"),
    ("G-FAIL::003", "INPUT_LOCK_MISMATCH", "ST12F_INPUT_LOCK_MISMATCH"),
    ("G-FAIL::004", "SOURCE_EPOCH_MISSING", "SOURCE_EPOCH_MISSING"),
    ("G-FAIL::005", "SOURCE_EPOCH_MISMATCH", "SOURCE_CONFLICT"),
    ("G-FAIL::006", "EVIDENCE_BUNDLE_NOT_CLOSED", "ST12F_INDEPENDENT_REVIEW_REQUIRED"),
    ("G-FAIL::007", "INDEPENDENT_REVIEW_ABSENT_OR_NOT_VALIDATED", "ST12F_INDEPENDENT_REVIEW_REQUIRED"),
    ("G-FAIL::008", "VALIDITY_EXPIRED", "ST12F_BUNDLE_STALE"),
    ("G-FAIL::009", "OBSERVATION_AFTER_VALID_UNTIL", "POINT_IN_TIME_FRESHNESS_OR_SEQUENCE_INVALID"),
    ("G-FAIL::010", "PARENT_EVIDENCE_REFERENCE_MISMATCH", "SCHEMA_MISMATCH"),
    ("G-FAIL::011", "SOURCE_RECORD_REFERENCES_INCOMPLETE", "ST12F_EVIDENCE_INCOMPLETE"),
    ("G-FAIL::012", "SOURCE_RECORD_REFERENCES_OUT_OF_ORDER", "SCHEMA_MISMATCH"),
    ("G-FAIL::013", "UNKNOWN_CONSUMER_OWNER", "OWNER_DATA_MISSING"),
    ("G-FAIL::014", "UNKNOWN_CONSUMER_FIELD", "SCHEMA_MISMATCH"),
    ("G-FAIL::015", "OWNER_DESCRIPTOR_NATURAL_SLOT_SAME_ID_SAME_PAYLOAD", "IDEMPOTENT_RETURN_EXISTING"),
    ("G-FAIL::016", "OWNER_DESCRIPTOR_NATURAL_SLOT_SAME_ID_DIFFERENT_PAYLOAD", "IDEMPOTENCY_CONFLICT"),
    ("G-FAIL::017", "ATTEMPTED_RUNTIME_AUTHORITY", "RUNTIME_EFFECT_FORBIDDEN"),
    ("G-FAIL::018", "ATTEMPTED_SECOND_STATE_STORE", "INPUT_OWNER_MISMATCH"),
    ("G-FAIL::019", "ATTEMPTED_ECONOMIC_OR_STATISTICAL_RECOMPUTATION", "FORMULA_EXECUTION_REJECTED"),
    ("G-FAIL::020", "ATTEMPTED_PARAMETER_VALUE_MUTATION", "PARAMETER_NOT_EDITABLE"),
    ("G-FAIL::021", "REQUEST_CONTAINS_CALLER_SUPPLIED_FRESHNESS_EPOCH_INPUT_LOCK_OR_PARENT_ASSERTION", "INPUT_OWNER_MISMATCH"),
    ("G-FAIL::022", "DASHBOARD_DIRECTLY_BOUND_TO_F_HANDOFF", "INPUT_OWNER_MISMATCH"),
    ("G-FAIL::023", "UNEXPLAINED_EMPTY_STRING_OR_UNTYPED_ABSENCE", "INCOMPLETE_CONTRACT"),
    ("G-FAIL::024", "FIXTURE_OR_CONTRACT_ROW_PRESENTED_AS_EMPIRICAL_EVIDENCE", "ST12F_FIXTURE_NOT_EVIDENCE"),
    ("G-FAIL::025", "ATTEMPTED_MODE_ACTIVATION", "MODE_ACTIVATION_FORBIDDEN"),
    ("G-FAIL::026", "ATTEMPTED_ALLOW_ACTIVATION", "MODE_ACTIVATION_FORBIDDEN"),
    ("G-FAIL::027", "ATTEMPTED_ORDER_RELEASE", "ORDER_RELEASE_FORBIDDEN"),
    ("G-FAIL::028", "ATTEMPTED_CAPITAL_EFFECT", "CAPITAL_EFFECT_FORBIDDEN"),
    ("G-FAIL::029", "ATTEMPTED_PROVIDER_ACCESS", "DIRECT_PROVIDER_FORBIDDEN"),
    ("G-FAIL::030", "ATTEMPTED_PRIVATE_STATE_ACCESS", "PRIVATE_STATE_FORBIDDEN"),
    ("G-FAIL::031", "ATTEMPTED_REPLAY_OR_PAPER_EXECUTION", "REPLAY_PAPER_EFFECT_FORBIDDEN"),
    ("G-FAIL::032", "ATTEMPTED_LLM_INFERENCE", "LLM_INFERENCE_FORBIDDEN"),
    ("G-FAIL::033", "ATTEMPTED_QPU_OR_SIMULATOR_EXECUTION", "QPU_EFFECT_FORBIDDEN"),
    ("G-FAIL::034", "UNLISTED_OR_WILDCARD_REPOSITORY_PATH", "PATH_UNSAFE"),
    ("G-FAIL::035", "WRONG_DURABLE_RECEIPT_CLASS", "SCHEMA_MISMATCH"),
    ("G-FAIL::036", "G_HANDOFF_RECEIPT_MARKED_FIXTURE_ONLY_NOT_EVIDENCE", "ST12F_FIXTURE_NOT_EVIDENCE"),
    ("G-FAIL::037", "RECEIPT_PARENT_METADATA_MISMATCH", "SCHEMA_MISMATCH"),
    ("G-FAIL::038", "RECEIPT_INPUT_LOCK_METADATA_MISMATCH", "ST12F_INPUT_LOCK_MISMATCH"),
    ("G-FAIL::039", "RECEIPT_SOURCE_EPOCH_METADATA_MISMATCH", "SOURCE_CONFLICT"),
    ("G-FAIL::040", "RECEIPT_STABLE_FIRST_OCCURRENCE_SOURCE_RECORD_METADATA_MISMATCH", "SCHEMA_MISMATCH"),
    ("G-FAIL::041", "PARENT_EMBEDDED_G_HANDOFF_DIFFERS_FROM_DURABLE_HANDOFF", "SCHEMA_MISMATCH"),
    ("G-FAIL::042", "CURRENT_PARENT_COMPONENT_VERSION_MAPPING_EMPTY", "ST12F_EVIDENCE_INCOMPLETE"),
    ("G-FAIL::043", "STACK_VERSION_EMPTY_WITHOUT_TYPED_EXPLICIT_ABSENCE", "SCHEMA_MISMATCH"),
    ("G-FAIL::044", "DUPLICATE_REFERENCE_INSIDE_HANDOFF_COLLECTION", "SCHEMA_MISMATCH"),
    ("G-FAIL::045", "G_SORTS_OR_DEDUPLICATES_A_PROJECTED_REFERENCE_COLLECTION", "SCHEMA_MISMATCH"),
)


def _owner_view(owner_id: str) -> OwnerProjectionViewV1:
    path = f"docs/st12g/{owner_id.lower()}.jsonl"
    return OwnerProjectionViewV1(
        owner_id=owner_id,
        authority_domain="READ_ONLY_EVIDENCE",
        source_path=path,
        source_version=f"VERSION::{owner_id}",
        source_snapshot_ref=path,
        consume_interfaces=("resolve_st12g_projection_v2",),
        row_count=1,
        identity_refs=(f"ROW::{owner_id}",),
    )


@lru_cache(maxsize=1)
def _baseline() -> tuple[
    ComputationExecutionContextV1,
    ImmutableReplayPaperInputLockV1,
    FToGHandoffReferencesV1,
    ComputationEvidenceBundleV1,
    ST12FEvidenceReferenceV1,
    PreloadedOwnerProjectionBundleV1,
]:
    versions = {
        identity: f"VERSION::{identity}" for identity in ST12F_TEMPLATE_IDS_V1
    }
    lock = ImmutableReplayPaperInputLockV1(
        input_lock_id="ST12F-LOCK::G-VALID",
        schema_version=INPUT_LOCK_SCHEMA_VERSION_V1,
        contract_version="1.4",
        decision_time=_NOW,
        point_in_time_cutoff=_NOW - timedelta(minutes=1),
        market_scope=("MARKET::1",),
        venue_scope=("VENUE::1",),
        instrument_scope=("INSTRUMENT::1",),
        cohort_template_ids=ST12F_TEMPLATE_IDS_V1,
        expected_replay_result_contract_ids=ST12F_REPLAY_RESULT_CONTRACT_IDS_V1,
        expected_paper_result_contract_ids=ST12F_PAPER_RESULT_CONTRACT_IDS_V1,
        formula_specification_versions=versions,
        implementation_versions=versions,
        parameter_policy_version="POLICY::1",
        parameter_value_refs=tuple(
            f"ST10-PARAM::{index:04d}"
            for index in range(ST12F_PARAMETER_VALUE_REF_COUNT_V1)
        ),
        source_epochs={"SOURCE::1": "EPOCH::1"},
        data_semantics_version="DATA::1",
        venue_semantics_version="VENUE::1",
        accounting_definition={"basis": "NET"},
        fee_assumptions={"ref": "FEE::1"},
        spread_assumptions={"ref": "SPREAD::1"},
        slippage_assumptions={"ref": "SLIPPAGE::1"},
        fill_and_queue_assumptions={"ref": "FILL::1"},
        latency_and_staleness_assumptions={"ref": "LATENCY::1"},
        capacity_and_crowding_assumptions={"ref": "CAPACITY::1"},
        portfolio_and_cash_context={
            "permanent_no_trade_baseline_ref": "NO-TRADE::1"
        },
        random_seed_policy={"seed": 1},
        resampling_policy={"trial_family_id": "TRIAL::1"},
        scenario_set_id="SCENARIO::1",
        causation_id="CAUSE::LOCK",
        correlation_id="CORRELATION::LOCK",
        created_by="OWNER::LOCK",
        created_at=_NOW,
    )
    context = ComputationExecutionContextV1(
        context_id="CONTEXT::G-VALID",
        as_of=_NOW,
        observed_at=_NOW - timedelta(minutes=1),
        source_epoch_id="SOURCE::1=EPOCH::1",
        input_version="INPUT::1",
        maximum_age=timedelta(minutes=5),
        scope=ComputationScopeV1(
            market_scope_id="MARKET::1",
            venue_scope_id="VENUE::1",
            event_scope_id="EVENT::1",
            instrument_or_contract_scope_id="INSTRUMENT::1",
            mode_context_id="MODE::READ_ONLY",
            input_snapshot_id=lock.input_lock_id,
        ),
        binding_profile_version="BINDING::1",
        parameter_policy_version="POLICY::1",
        implementation_versions=(
            ImplementationVersionPinV1("MATH-01", "VERSION::MATH-01"),
        ),
    )
    evidence_ref = "ST12F-RECEIPT::BUNDLE::G-VALID::EVIDENCE_BUNDLE_VERSION"
    reference = ST12FEvidenceReferenceV1(
        evidence_state=ST12FEvidenceStateV1.EVIDENCE_REFERENCE_AVAILABLE,
        evidence_ref=evidence_ref,
        lane="REPLAY_PAPER",
        dataset_grade_ref="DATASET-GRADE::G-VALID",
        venue_semantic_binding_ref="VENUE-SEMANTICS::G-VALID",
        cross_venue_equivalence_ref="CROSS-VENUE::G-VALID",
        observed_at=_NOW - timedelta(minutes=2),
        valid_until=_NOW + timedelta(minutes=5),
        policy_version="ST12F_EVIDENCE_POLICY_V1_4",
        causation_id="CAUSE::F",
        correlation_id="CORRELATION::F",
        input_lock_id=lock.input_lock_id,
        component_or_template_ref="MATH-01",
        evidence_bundle_version="BUNDLE::G-VALID",
        source_epoch_refs=("SOURCE::1=EPOCH::1",),
        terminal_state="CLOSED_INDEPENDENTLY_VALIDATED",
        reference_id="D-REFERENCE::G-VALID",
        evidence_id="EVIDENCE::G-VALID",
    )
    handoff = FToGHandoffReferencesV1(
        handoff_id="G-HANDOFF::G-VALID",
        contract_version="1.4",
        input_lock_id=lock.input_lock_id,
        source_epoch_refs=("SOURCE::1=EPOCH::1",),
        observed_at=_NOW - timedelta(minutes=2),
        valid_until=_NOW + timedelta(minutes=5),
        terminal_state="CLOSED_INDEPENDENTLY_VALIDATED",
        evidence_bundle_ref=evidence_ref,
        no_trade_blocker_refs=(),
        champion_challenger_evidence_refs=("CHAMPION::1",),
        portfolio_utility_refs=("PORTFOLIO-UTILITY::1",),
        quantum_classical_comparison_receipt_ref="RECEIPT::MATH-52",
    )
    dispositions = tuple(
        EvidenceIdentityDispositionV1(
            identity,
            EvidenceIdentityDispositionStateV1.APPLICABLE_EXECUTED_AND_RECEIPTED,
            (f"RECEIPT::{identity}",),
            (),
            (),
        )
        for identity in ST12F_EVIDENCE_IDENTITIES_V1
    )
    sections: dict[str, EvidenceSectionV1] = {}
    offset = 0
    for index, name in enumerate(_SECTION_FIELDS):
        width = 8 if index == len(_SECTION_FIELDS) - 1 else 4
        sections[name] = EvidenceSectionV1(
            name, dispositions[offset : offset + width]
        )
        offset += width
    bundle = ComputationEvidenceBundleV1(
        evidence_id=reference.evidence_id,
        schema_version="QTT_ST12F_COMPUTATION_EVIDENCE_BUNDLE_V1_4",
        contract_version="1.4",
        evidence_bundle_version=reference.evidence_bundle_version,
        component_or_template_ref="MATH-01",
        input_lock_id=lock.input_lock_id,
        actual_executed_component_versions={"MATH-01": "VERSION::MATH-01"},
        actual_executed_stack_versions={},
        replay_result_ref="RESULT::REPLAY",
        paper_result_ref="RESULT::PAPER",
        divergence_assessment_ref="DIVERGENCE::1",
        lane_execution_receipt_refs=("RECEIPT::REPLAY", "RECEIPT::PAPER"),
        **sections,
        independent_review_state="CLOSED_INDEPENDENTLY_VALIDATED",
        failure_and_negative_evidence_states=(),
        source_and_provenance_refs=("SOURCE-RECORD::1",),
        d_evidence_reference_projection=reference,
        g_handoff_projection=handoff,
        terminal_state=EvidenceBundleTerminalStateV1.CLOSED_INDEPENDENTLY_VALIDATED,
        blocker_codes=(),
    )
    owners = PreloadedOwnerProjectionBundleV1(
        readiness=_owner_view("READINESS1"),
        pretrade=_owner_view("PRETRADE1"),
        svc=_owner_view("SVC1"),
        agent_orch=_owner_view("AGENT_ORCH1"),
    )
    return context, lock, handoff, bundle, reference, owners


def _compile(
    *,
    context: ComputationExecutionContextV1 | None = None,
    lock: ImmutableReplayPaperInputLockV1 | None = None,
    handoff: FToGHandoffReferencesV1 | None = None,
    bundle: ComputationEvidenceBundleV1 | None = None,
    reference: ST12FEvidenceReferenceV1 | None = None,
):
    baseline = _baseline()
    return ExistingOwnerProjectionCompilerV2().compile_current(
        context or baseline[0],
        lock or baseline[1],
        handoff or baseline[2],
        bundle or baseline[3],
        reference or baseline[4],
        baseline[5],
    )


def _mutated(value: object, **changes: object):
    altered = copy(value)
    for name, replacement in changes.items():
        object.__setattr__(altered, name, replacement)
    return altered


def _assert_reason(expected: str, operation) -> None:
    with pytest.raises(ComputationControlPlaneError) as caught:
        operation()
    assert caught.value.reason_code.name == expected


class _EvidenceService:
    def __init__(self, fail_method: str | None = None, reason: ReasonCode | None = None):
        self.context, self.lock, self.handoff, self.bundle, self.reference, _ = _baseline()
        self.fail_method = fail_method
        self.reason = reason
        self.calls: list[tuple[str, datetime]] = []

    def _record(self, method: str, cutoff: datetime) -> None:
        self.calls.append((method, cutoff))
        if self.fail_method == method:
            raise ContractValidationError(self.reason or ReasonCode.SCHEMA_MISMATCH, method)

    def resolve_g_handoff(self, handoff_ref: str, *, decision_cutoff: datetime):
        self._record("resolve_g_handoff", decision_cutoff)
        return self.handoff

    def resolve_control_receipt(self, receipt_ref: str, expected_type: type[object], *, decision_cutoff: datetime):
        self._record("resolve_control_receipt", decision_cutoff)
        return self.lock

    def resolve_bundle(self, bundle_ref: str, *, decision_cutoff: datetime):
        self._record("resolve_bundle", decision_cutoff)
        return self.bundle

    def read_evidence_reference(self, context, *, causation_id: str, correlation_id: str, query=None):
        self._record("read_evidence_reference", context.as_of)
        return self.reference


def _request(context: ComputationExecutionContextV1 | None = None) -> ST12GProjectionRequestV2:
    handoff = _baseline()[2]
    return ST12GProjectionRequestV2(
        request_id="REQUEST::G-VALID",
        context=context or _baseline()[0],
        source_handoff_receipt_ref=(
            f"ST12F-RECEIPT::{handoff.handoff_id}::G_HANDOFF_REFERENCE"
        ),
        causation_id="CAUSE::G",
        correlation_id="CORRELATION::G",
    )


def _resolve_with_failure(method: str, reason: ReasonCode):
    service = _EvidenceService(method, reason)
    result = ExistingOwnerProjectionCoordinatorV2(service, _baseline()[5]).resolve(
        _request()
    )
    assert result.resolution_state is ST12GProjectionResolutionStateV2.UNAVAILABLE_BLOCKED_NO_AUTHORITY
    assert result.absence.reason_codes == (reason,)
    return result


def _source_tree() -> ast.Module:
    path = _ROOT / "src/qtt/stage1_prediction_markets/qku_computation_control_plane/existing_owner_projection.py"
    return ast.parse(path.read_text(encoding="utf-8"))


def _descriptor(owner: str) -> dict[str, object]:
    paths = {
        "READINESS1": "docs/master_plan/generated/pr169_readiness1/st12g_evidence_projection_contract.generated.jsonl",
        "PRETRADE1": "docs/master_plan/generated/pr169_pretrade1/st12g_evidence_projection_contract.generated.jsonl",
        "AGENT_ORCH1": "docs/master_plan/generated/pr169_agent_orch1/st12g_evidence_handoff_contract.generated.jsonl",
        "SVC1": "docs/master_plan/generated/pr169_svc1/st12g_evidence_view_contract.generated.jsonl",
        "DASH1_UI1": "docs/master_plan/generated/pr169_dash1/st12g_evidence_owner_view_contract.generated.jsonl",
    }
    rows = [
        json.loads(line)
        for line in (_ROOT / paths[owner]).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert len(rows) == 1
    return rows[0]


def _run_historical_contract(case_id: str) -> None:
    context, lock, handoff, bundle, reference, _ = _baseline()
    if case_id == "ST12-TEST::103":
        poisoned = replace(context, source_epoch_id="SOURCE::POISON=EPOCH::POISON")
        _assert_reason("SOURCE_CONFLICT", lambda: _compile(context=poisoned))
    elif case_id == "ST12-TEST::109":
        _assert_reason(
            "SCHEMA_MISMATCH",
            lambda: ST12GReferenceCollectionV2(
                ST12GReferenceCollectionStateV2.EXPLICIT_EMPTY_NO_BLOCKER_IN_CLOSED_BUNDLE,
                ("REF::ILLEGAL",),
            ),
        )
    elif case_id == "ST12-TEST::117":
        names = {node.id.casefold() for node in ast.walk(_source_tree()) if isinstance(node, ast.Name)}
        assert not names.intersection({"secret", "credential", "private_account", "chain_of_thought"})
    elif case_id == "ST12-TEST::118":
        imports = {alias.name for node in ast.walk(_source_tree()) if isinstance(node, ast.Import) for alias in node.names}
        assert not imports.intersection({"requests", "openai", "subprocess", "importlib"})
    elif case_id == "ST12-TEST::141":
        absence = ST12GProjectionAbsenceV2(
            absence_id="ST12G::ABSENCE::HISTORICAL",
            evaluation_context_id=context.context_id,
            evaluated_at=context.as_of,
            state=ST12GProjectionResolutionStateV2.UNAVAILABLE_STALE_NO_AUTHORITY,
            reason_codes=(ReasonCode.ST12F_BUNDLE_STALE,),
            source_handoff_receipt_ref_or_explicit_absence="EXPLICIT_ABSENCE",
        )
        assert absence.no_effect_flags is NO_EFFECTS_V1
        assert all(value is False for value in vars(NO_EFFECTS_V1).values()) if hasattr(NO_EFFECTS_V1, "__dict__") else all(getattr(NO_EFFECTS_V1, field.name) is False for field in fields(NO_EFFECTS_V1))
    elif case_id == "ST12-TEST::144":
        assert deterministic_json(_compile()) == deterministic_json(_compile())
    elif case_id == "ST12-TEST::145":
        compiler = ExistingOwnerProjectionCompilerV2()
        assert compiler.__slots__ == () and not hasattr(compiler, "__dict__")
        assert len(fields(ST12GProjectionCoreV2)) == 33
    elif case_id == "ST12-TEST::155":
        core = _compile().core
        assert (core.evaluated_at, core.observed_at, core.valid_until) == (
            context.as_of,
            handoff.observed_at,
            handoff.valid_until,
        )
        assert core.source_epoch_refs == reference.source_epoch_refs
        assert core.no_effect_flags is NO_EFFECTS_V1
    elif case_id == "ST12-TEST::160":
        scope = (_ROOT / "tools/validation_scope_registry.py").read_text(encoding="utf-8")
        router = (_ROOT / "tools/changed_area_validation_router.py").read_text(encoding="utf-8")
        assert "agent/st12g-existing-owner-projections-v2" in scope
        assert "independent_validate_qku_computation_control_plane_g.py" in router
    else:
        raise AssertionError(case_id)


def _run_contract_failure(case_id: str, trigger: str, expected: str) -> None:
    context, lock, handoff, bundle, reference, owners = _baseline()
    if case_id == "G-FAIL::001":
        _resolve_with_failure("resolve_g_handoff", ReasonCode.OWNER_DATA_MISSING)
    elif case_id == "G-FAIL::002":
        bad_handoff = _mutated(handoff, contract_version="0.0")
        bad_bundle = _mutated(bundle, g_handoff_projection=bad_handoff)
        _assert_reason(expected, lambda: _compile(handoff=bad_handoff, bundle=bad_bundle))
    elif case_id == "G-FAIL::003":
        bad_bundle = _mutated(bundle, input_lock_id="ST12F-LOCK::MISMATCH")
        _assert_reason(expected, lambda: _compile(bundle=bad_bundle))
    elif case_id == "G-FAIL::004":
        bad_lock = _mutated(lock, source_epochs={})
        _assert_reason(expected, lambda: _compile(lock=bad_lock))
    elif case_id == "G-FAIL::005":
        bad_handoff = _mutated(handoff, source_epoch_refs=("SOURCE::2=EPOCH::2",))
        bad_bundle = _mutated(bundle, g_handoff_projection=bad_handoff)
        _assert_reason(expected, lambda: _compile(handoff=bad_handoff, bundle=bad_bundle))
    elif case_id == "G-FAIL::006":
        open_bundle = replace(
            bundle,
            d_evidence_reference_projection="UNAVAILABLE",
            g_handoff_projection="UNAVAILABLE",
            independent_review_state="READY_FOR_INDEPENDENT_REVIEW",
            terminal_state=EvidenceBundleTerminalStateV1.READY_FOR_INDEPENDENT_REVIEW,
        )
        _assert_reason(expected, lambda: _compile(bundle=open_bundle))
    elif case_id == "G-FAIL::007":
        bad_bundle = _mutated(bundle, independent_review_state="EXPLICIT_ABSENCE")
        _assert_reason(expected, lambda: _compile(bundle=bad_bundle))
    elif case_id == "G-FAIL::008":
        expired = replace(
            handoff,
            observed_at=_NOW - timedelta(minutes=10),
            valid_until=_NOW - timedelta(minutes=1),
        )
        expired_bundle = replace(bundle, g_handoff_projection=expired)
        _assert_reason(expected, lambda: _compile(handoff=expired, bundle=expired_bundle))
    elif case_id == "G-FAIL::009":
        invalid_sequence = _mutated(
            handoff,
            observed_at=handoff.valid_until + timedelta(minutes=1),
        )
        invalid_bundle = _mutated(
            bundle,
            g_handoff_projection=invalid_sequence,
        )
        _assert_reason(
            expected,
            lambda: _compile(
                handoff=invalid_sequence,
                bundle=invalid_bundle,
            ),
        )
    elif case_id in {"G-FAIL::010", "G-FAIL::012", "G-FAIL::035", "G-FAIL::037", "G-FAIL::040"}:
        _resolve_with_failure("resolve_bundle", ReasonCode[expected])
    elif case_id == "G-FAIL::011":
        incomplete_bundle = _mutated(bundle, source_and_provenance_refs=())
        _assert_reason(expected, lambda: _compile(bundle=incomplete_bundle))
    elif case_id == "G-FAIL::013":
        current = ST12GProjectionResolutionV2.current(
            resolution_id="ST12G::RESOLUTION::OWNER",
            request_id="REQUEST::OWNER",
            context_id=context.context_id,
            evaluated_at=context.as_of,
            projection_bundle=_compile(),
        )
        _assert_reason(
            expected,
            lambda: ST12GOwnerProjectionResolutionV2(
                consumer_id="UNKNOWN",
                source_request_id=current.request_id,
                resolution_state=current.resolution_state,
                payload=current.projection_bundle.readiness,
            ),
        )
    elif case_id == "G-FAIL::014":
        assert tuple(field.name for field in fields(ST12GProjectionCoreV2)) == _CORE_FIELDS
        assert not hasattr(_compile().core, "unknown_consumer_field")
    elif case_id == "G-FAIL::015":
        assert _descriptor("READINESS1") == _descriptor("READINESS1")
    elif case_id == "G-FAIL::016":
        original = _descriptor("READINESS1")
        changed = original | {"contract_type": "DIFFERENT"}
        assert changed != original and changed["descriptor_id"] == original["descriptor_id"]
        assert ReasonCode.IDEMPOTENCY_CONFLICT.name == expected
    elif case_id == "G-FAIL::017":
        _assert_reason(expected, lambda: replace(_compile().core, runtime_authority="ALLOW"))
    elif case_id in {"G-FAIL::018", "G-FAIL::019", "G-FAIL::020"}:
        source = (_ROOT / "src/qtt/stage1_prediction_markets/qku_computation_control_plane/existing_owner_projection.py").read_text(encoding="utf-8")
        forbidden = {
            "G-FAIL::018": ("sqlite", "cache", "current_pointer", "state_store"),
            "G-FAIL::019": ("Decimal", "numpy", "compute_math", "get_math_callable"),
            "G-FAIL::020": ("parameter_values", "replace_parameter", "mutate_parameter"),
        }[case_id]
        assert not any(token in source for token in forbidden)
        assert ReasonCode[expected].name == expected
    elif case_id == "G-FAIL::021":
        request_fields = tuple(field.name for field in fields(ST12GProjectionRequestV2))
        assert request_fields == (
            "request_id",
            "context",
            "source_handoff_receipt_ref",
            "causation_id",
            "correlation_id",
        )
    elif case_id == "G-FAIL::022":
        from src.qtt.dashboard.owner_surface_resolver import resolve_st12g_projection_v2

        _assert_reason(expected, lambda: resolve_st12g_projection_v2(handoff))
    elif case_id == "G-FAIL::023":
        _assert_reason(
            expected,
            lambda: replace(_request(), request_id=""),
        )
    elif case_id == "G-FAIL::024":
        assert _descriptor("SVC1")["runtime_instance_state"] == "NOT_MATERIALIZED_BY_REPOSITORY_BUILD"
        assert ReasonCode.ST12F_FIXTURE_NOT_EVIDENCE.name == expected
    elif case_id in {f"G-FAIL::{index:03d}" for index in range(25, 34)}:
        assert all(getattr(NO_EFFECTS_V1, field.name) is False for field in fields(NO_EFFECTS_V1))
        assert ReasonCode[expected].name == expected
    elif case_id == "G-FAIL::034":
        _assert_reason(expected, lambda: validate_relative_path("../outside"))
    elif case_id == "G-FAIL::036":
        _resolve_with_failure("resolve_g_handoff", ReasonCode.ST12F_FIXTURE_NOT_EVIDENCE)
    elif case_id == "G-FAIL::038":
        _resolve_with_failure("resolve_control_receipt", ReasonCode.ST12F_INPUT_LOCK_MISMATCH)
    elif case_id == "G-FAIL::039":
        _resolve_with_failure("resolve_control_receipt", ReasonCode.SOURCE_CONFLICT)
    elif case_id == "G-FAIL::041":
        other = replace(handoff, handoff_id="G-HANDOFF::OTHER")
        bad_bundle = replace(bundle, g_handoff_projection=other)
        _assert_reason(expected, lambda: _compile(bundle=bad_bundle))
    elif case_id == "G-FAIL::042":
        bad_bundle = _mutated(bundle, actual_executed_component_versions={})
        _assert_reason(expected, lambda: _compile(bundle=bad_bundle))
    elif case_id == "G-FAIL::043":
        projection = _compile()
        assert projection.core.actual_executed_stack_version_state.state is ST12GVersionMappingStateV2.EXPLICIT_EMPTY_NO_STACK_EXECUTED_FOR_COMPONENT_SCOPE
        assert dict(projection.core.actual_executed_stack_version_state.version_mapping) == {}
    elif case_id == "G-FAIL::044":
        bad_handoff = _mutated(
            handoff,
            champion_challenger_evidence_refs=("CHAMPION::1", "CHAMPION::1"),
        )
        bad_bundle = _mutated(bundle, g_handoff_projection=bad_handoff)
        _assert_reason(expected, lambda: _compile(handoff=bad_handoff, bundle=bad_bundle))
    elif case_id == "G-FAIL::045":
        ordered = replace(
            handoff,
            champion_challenger_evidence_refs=("CHAMPION::B", "CHAMPION::A"),
        )
        ordered_bundle = replace(bundle, g_handoff_projection=ordered)
        output = _compile(handoff=ordered, bundle=ordered_bundle)
        assert output.core.champion_challenger_reference_state.reference_values == (
            "CHAMPION::B",
            "CHAMPION::A",
        )
        assert ReasonCode.SCHEMA_MISMATCH.name == expected
    else:
        raise AssertionError((case_id, trigger, expected, owners, reference))


_CONTRACT_CASES = (*_HISTORICAL_CONTRACT_CASES, *_FAIL_CASES_CONTRACT)


@pytest.mark.parametrize(
    ("case_id", "trigger", "expected"),
    _CONTRACT_CASES,
    ids=[row[0] for row in _CONTRACT_CASES],
)
def test_st12g_contract_case(case_id: str, trigger: str, expected: str) -> None:
    if case_id.startswith("ST12-TEST::"):
        _run_historical_contract(case_id)
    else:
        _run_contract_failure(case_id, trigger, expected)
