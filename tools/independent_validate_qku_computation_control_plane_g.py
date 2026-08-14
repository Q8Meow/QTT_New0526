#!/usr/bin/env python3
"""Independent structural reconstruction of the ST12-G owner projection contract."""

from __future__ import annotations

import ast
from collections import Counter
from dataclasses import fields
import inspect
import json
from pathlib import Path
import re
import sys
from typing import Mapping, Sequence


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.qtt.stage1_prediction_markets.qku_computation_control_plane import (  # noqa: E402
    existing_owner_projection as projection,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import (  # noqa: E402
    ContractValidationError,
    ReasonCode,
)
from tools import changed_area_validation_router as router  # noqa: E402
from tools import ci_branch_context  # noqa: E402
from tools import validation_inventory as inventory  # noqa: E402
from tools import validation_scope_registry as scope  # noqa: E402


SUCCESS_MARKER = "QKU_COMPUTATION_CONTROL_PLANE_INDEPENDENT_G_VALIDATED"
EXPECTED_BRANCH = "agent/st12g-existing-owner-projections-v2"
EXPECTED_PUBLIC_NAMES = frozenset(
    {
        "ST12GProjectionRequestV2",
        "ST12GProjectionResolutionStateV2",
        "ST12GReferenceCollectionStateV2",
        "ST12GReferenceCollectionV2",
        "ST12GVersionMappingStateV2",
        "ST12GVersionMappingV2",
        "ST12GBlockerSetStateV2",
        "ST12GBlockerStateV2",
        "ST12GProjectionCoreV2",
        "ST12GReadinessEvidenceProjectionV2",
        "ST12GPretradeEvidenceProjectionV2",
        "ST12GAgentEvidenceHandoffV2",
        "ST12GServiceEvidenceViewV2",
        "ST12GProjectionBundleV2",
        "ST12GProjectionAbsenceV2",
        "ST12GProjectionResolutionV2",
        "ST12GOwnerProjectionResolutionV2",
        "ST12GOwnerDashboardEvidenceViewV2",
        "ExistingOwnerProjectionCompilerV2",
        "ExistingOwnerProjectionCoordinatorV2",
    }
)
EXPECTED_CORE_FIELDS = (
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
EXPECTED_TYPE_FIELDS = {
    "ST12GProjectionRequestV2": (
        "request_id",
        "context",
        "source_handoff_receipt_ref",
        "causation_id",
        "correlation_id",
    ),
    "ST12GReadinessEvidenceProjectionV2": (
        "projection_id",
        "projection_contract_version",
        "consumer_id",
        "core",
        "evidence_readiness_state",
        "runtime_instance_state",
        "activation_authority",
        "runtime_effect_allowed",
        "write_authority",
    ),
    "ST12GPretradeEvidenceProjectionV2": (
        "projection_id",
        "projection_contract_version",
        "consumer_id",
        "core",
        "pretrade_evidence_state",
        "no_trade_route_state",
        "submit_authority_created",
        "order_authority_created",
        "profit_claim_created",
        "runtime_effect_allowed",
        "write_authority",
    ),
    "ST12GAgentEvidenceHandoffV2": (
        "projection_id",
        "projection_contract_version",
        "consumer_id",
        "core",
        "task_class",
        "allowed_operation",
        "self_promotion_allowed",
        "historical_rewrite_allowed",
        "owner_review_route",
        "runtime_effect_allowed",
        "write_authority",
    ),
    "ST12GServiceEvidenceViewV2": (
        "projection_id",
        "projection_contract_version",
        "consumer_id",
        "core",
        "read_model_class",
        "stale_state",
        "action_eligibility_state",
        "fake_receipt_allowed",
        "runtime_execution_allowed",
        "runtime_effect_allowed",
        "write_authority",
    ),
    "ST12GOwnerDashboardEvidenceViewV2": (
        "projection_id",
        "contract_version",
        "consumer_id",
        "source_svc_resolution_state",
        "source_svc_projection_id_or_explicit_absence",
        "panel_id",
        "availability_badge",
        "stale_banner_state",
        "owner_safe_next_action",
        "direct_f_binding_allowed",
        "live_control_authority",
        "source_lineage_state",
        "no_effect_flags",
        "runtime_effect_allowed",
        "write_authority",
    ),
}
EXPECTED_DESCRIPTOR_FIELDS = frozenset(
    {
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
)
CENTRAL_MANIFEST = (
    "docs/master_plan/generated/qku_control_plane/existing_owner_projection/"
    "st12g_projection_contract_manifest.json"
)
DESCRIPTORS = {
    "READINESS1": (
        "docs/master_plan/generated/pr169_readiness1/"
        "st12g_evidence_projection_contract.generated.jsonl",
        "ST12GReadinessEvidenceProjectionV2",
        ("READINESS1",),
    ),
    "PRETRADE1": (
        "docs/master_plan/generated/pr169_pretrade1/"
        "st12g_evidence_projection_contract.generated.jsonl",
        "ST12GPretradeEvidenceProjectionV2",
        ("PRETRADE1",),
    ),
    "AGENT_ORCH1": (
        "docs/master_plan/generated/pr169_agent_orch1/"
        "st12g_evidence_handoff_contract.generated.jsonl",
        "ST12GAgentEvidenceHandoffV2",
        ("AGENT_ORCH1",),
    ),
    "SVC1": (
        "docs/master_plan/generated/pr169_svc1/"
        "st12g_evidence_view_contract.generated.jsonl",
        "ST12GServiceEvidenceViewV2",
        ("SVC1", "DASH1_UI1"),
    ),
    "DASH1_UI1": (
        "docs/master_plan/generated/pr169_dash1/"
        "st12g_evidence_owner_view_contract.generated.jsonl",
        "ST12GOwnerDashboardEvidenceViewV2",
        ("DASH1_UI1",),
    ),
}
EXPECTED_HISTORICAL_IDS = frozenset(
    {
        "ST12-TEST::026",
        "ST12-TEST::027",
        "ST12-TEST::028",
        "ST12-TEST::103",
        "ST12-TEST::109",
        "ST12-TEST::117",
        "ST12-TEST::118",
        "ST12-TEST::141",
        "ST12-TEST::144",
        "ST12-TEST::145",
        "ST12-TEST::155",
        "ST12-TEST::160",
        "ST12-TEST::222",
        "ST12-TEST::226",
        "ST12-TEST::228",
    }
)
ALLOWED_VERIFICATION_MODES = frozenset(
    {
        "PRODUCTION_MUTATION_REJECTION",
        "EXISTING_OWNER_REJECTION_PROPAGATION",
        "STATIC_ARCHITECTURE_MUTATION_DETECTION",
        "DETERMINISTIC_PRESERVATION_PROOF",
    }
)
EXPECTED_FAIL_CLOSED_ROWS = (
    ("G-FAIL::001", "HANDOFF_RECEIPT_MISSING", "REJECT_NO_PROJECTION", "OWNER_DATA_MISSING"),
    ("G-FAIL::002", "WRONG_HANDOFF_CONTRACT_VERSION", "REJECT_SCHEMA_MISMATCH", "SCHEMA_MISMATCH"),
    ("G-FAIL::003", "INPUT_LOCK_MISMATCH", "REJECT_INPUT_LOCK_MISMATCH", "ST12F_INPUT_LOCK_MISMATCH"),
    ("G-FAIL::004", "SOURCE_EPOCH_MISSING", "REJECT_SOURCE_EPOCH_MISSING", "SOURCE_EPOCH_MISSING"),
    ("G-FAIL::005", "SOURCE_EPOCH_MISMATCH", "REJECT_SOURCE_EPOCH_CONFLICT", "SOURCE_CONFLICT"),
    ("G-FAIL::006", "EVIDENCE_BUNDLE_NOT_CLOSED", "REJECT_INDEPENDENT_REVIEW_REQUIRED", "ST12F_INDEPENDENT_REVIEW_REQUIRED"),
    ("G-FAIL::007", "INDEPENDENT_REVIEW_ABSENT_OR_NOT_VALIDATED", "REJECT_INDEPENDENT_REVIEW_REQUIRED", "ST12F_INDEPENDENT_REVIEW_REQUIRED"),
    ("G-FAIL::008", "VALIDITY_EXPIRED", "RETURN_STALE_NO_AUTHORITY", "ST12F_BUNDLE_STALE"),
    ("G-FAIL::009", "OBSERVATION_AFTER_VALID_UNTIL", "REJECT_INVALID_TIME_SEQUENCE", "POINT_IN_TIME_FRESHNESS_OR_SEQUENCE_INVALID"),
    ("G-FAIL::010", "PARENT_EVIDENCE_REFERENCE_MISMATCH", "REJECT_PARENT_LINEAGE_MISMATCH", "SCHEMA_MISMATCH"),
    ("G-FAIL::011", "SOURCE_RECORD_REFERENCES_INCOMPLETE", "REJECT_SOURCE_CUSTODY_INCOMPLETE", "ST12F_EVIDENCE_INCOMPLETE"),
    ("G-FAIL::012", "SOURCE_RECORD_REFERENCES_OUT_OF_ORDER", "REJECT_SOURCE_CUSTODY_ORDER_MISMATCH", "SCHEMA_MISMATCH"),
    ("G-FAIL::013", "UNKNOWN_CONSUMER_OWNER", "REJECT_OWNER_TOPOLOGY_MISMATCH", "OWNER_DATA_MISSING"),
    ("G-FAIL::014", "UNKNOWN_CONSUMER_FIELD", "REJECT_SCHEMA_MISMATCH", "SCHEMA_MISMATCH"),
    ("G-FAIL::015", "OWNER_DESCRIPTOR_NATURAL_SLOT_SAME_ID_SAME_PAYLOAD", "RETURN_BYTE_EQUIVALENT_EXISTING_DESCRIPTOR", "IDEMPOTENT_RETURN_EXISTING"),
    ("G-FAIL::016", "OWNER_DESCRIPTOR_NATURAL_SLOT_SAME_ID_DIFFERENT_PAYLOAD", "REJECT_IDEMPOTENCY_CONFLICT", "IDEMPOTENCY_CONFLICT"),
    ("G-FAIL::017", "ATTEMPTED_RUNTIME_AUTHORITY", "REJECT_RUNTIME_EFFECT_FORBIDDEN", "RUNTIME_EFFECT_FORBIDDEN"),
    ("G-FAIL::018", "ATTEMPTED_SECOND_STATE_STORE", "REJECT_DUPLICATE_AUTHORITY", "INPUT_OWNER_MISMATCH"),
    ("G-FAIL::019", "ATTEMPTED_ECONOMIC_OR_STATISTICAL_RECOMPUTATION", "REJECT_DUPLICATE_MATH_AUTHORITY", "FORMULA_EXECUTION_REJECTED"),
    ("G-FAIL::020", "ATTEMPTED_PARAMETER_VALUE_MUTATION", "REJECT_PARAMETER_OWNER_MISMATCH", "PARAMETER_NOT_EDITABLE"),
    ("G-FAIL::021", "REQUEST_CONTAINS_CALLER_SUPPLIED_FRESHNESS_EPOCH_INPUT_LOCK_OR_PARENT_ASSERTION", "REJECT_CALLER_AUTHORITY_FIELD", "INPUT_OWNER_MISMATCH"),
    ("G-FAIL::022", "DASHBOARD_DIRECTLY_BOUND_TO_F_HANDOFF", "REJECT_OWNER_CHAIN_BYPASS", "INPUT_OWNER_MISMATCH"),
    ("G-FAIL::023", "UNEXPLAINED_EMPTY_STRING_OR_UNTYPED_ABSENCE", "REJECT_INCOMPLETE_CONTRACT", "INCOMPLETE_CONTRACT"),
    ("G-FAIL::024", "FIXTURE_OR_CONTRACT_ROW_PRESENTED_AS_EMPIRICAL_EVIDENCE", "REJECT_EVIDENCE_FABRICATION", "ST12F_FIXTURE_NOT_EVIDENCE"),
    ("G-FAIL::025", "ATTEMPTED_MODE_ACTIVATION", "REJECT_MODE_ACTIVATION", "MODE_ACTIVATION_FORBIDDEN"),
    ("G-FAIL::026", "ATTEMPTED_ALLOW_ACTIVATION", "REJECT_ALLOW_ACTIVATION", "MODE_ACTIVATION_FORBIDDEN"),
    ("G-FAIL::027", "ATTEMPTED_ORDER_RELEASE", "REJECT_ORDER_RELEASE", "ORDER_RELEASE_FORBIDDEN"),
    ("G-FAIL::028", "ATTEMPTED_CAPITAL_EFFECT", "REJECT_CAPITAL_EFFECT", "CAPITAL_EFFECT_FORBIDDEN"),
    ("G-FAIL::029", "ATTEMPTED_PROVIDER_ACCESS", "REJECT_PROVIDER_ACCESS", "DIRECT_PROVIDER_FORBIDDEN"),
    ("G-FAIL::030", "ATTEMPTED_PRIVATE_STATE_ACCESS", "REJECT_PRIVATE_STATE_ACCESS", "PRIVATE_STATE_FORBIDDEN"),
    ("G-FAIL::031", "ATTEMPTED_REPLAY_OR_PAPER_EXECUTION", "REJECT_REPLAY_PAPER_EFFECT", "REPLAY_PAPER_EFFECT_FORBIDDEN"),
    ("G-FAIL::032", "ATTEMPTED_LLM_INFERENCE", "REJECT_LLM_INFERENCE", "LLM_INFERENCE_FORBIDDEN"),
    ("G-FAIL::033", "ATTEMPTED_QPU_OR_SIMULATOR_EXECUTION", "REJECT_QPU_EFFECT", "QPU_EFFECT_FORBIDDEN"),
    ("G-FAIL::034", "UNLISTED_OR_WILDCARD_REPOSITORY_PATH", "REJECT_PATH_SCOPE", "PATH_UNSAFE"),
    ("G-FAIL::035", "WRONG_DURABLE_RECEIPT_CLASS", "REJECT_SCHEMA_MISMATCH", "SCHEMA_MISMATCH"),
    ("G-FAIL::036", "G_HANDOFF_RECEIPT_MARKED_FIXTURE_ONLY_NOT_EVIDENCE", "REJECT_EVIDENCE_FABRICATION", "ST12F_FIXTURE_NOT_EVIDENCE"),
    ("G-FAIL::037", "RECEIPT_PARENT_METADATA_MISMATCH", "REJECT_PARENT_LINEAGE_MISMATCH", "SCHEMA_MISMATCH"),
    ("G-FAIL::038", "RECEIPT_INPUT_LOCK_METADATA_MISMATCH", "REJECT_INPUT_LOCK_MISMATCH", "ST12F_INPUT_LOCK_MISMATCH"),
    ("G-FAIL::039", "RECEIPT_SOURCE_EPOCH_METADATA_MISMATCH", "REJECT_SOURCE_EPOCH_CONFLICT", "SOURCE_CONFLICT"),
    ("G-FAIL::040", "RECEIPT_STABLE_FIRST_OCCURRENCE_SOURCE_RECORD_METADATA_MISMATCH", "REJECT_SOURCE_CUSTODY_ORDER_MISMATCH", "SCHEMA_MISMATCH"),
    ("G-FAIL::041", "PARENT_EMBEDDED_G_HANDOFF_DIFFERS_FROM_DURABLE_HANDOFF", "REJECT_PARENT_HANDOFF_CONTRADICTION", "SCHEMA_MISMATCH"),
    ("G-FAIL::042", "CURRENT_PARENT_COMPONENT_VERSION_MAPPING_EMPTY", "REJECT_EVIDENCE_INCOMPLETE", "ST12F_EVIDENCE_INCOMPLETE"),
    ("G-FAIL::043", "STACK_VERSION_EMPTY_WITHOUT_TYPED_EXPLICIT_ABSENCE", "REJECT_SCHEMA_MISMATCH", "SCHEMA_MISMATCH"),
    ("G-FAIL::044", "DUPLICATE_REFERENCE_INSIDE_HANDOFF_COLLECTION", "REJECT_SCHEMA_MISMATCH", "SCHEMA_MISMATCH"),
    ("G-FAIL::045", "G_SORTS_OR_DEDUPLICATES_A_PROJECTED_REFERENCE_COLLECTION", "REJECT_LINEAGE_REWRITE", "SCHEMA_MISMATCH"),
    ("G-FAIL::046", "REQUEST_HANDOFF_RECEIPT_REF_NOT_FULL_CANONICAL_G_RECEIPT_REF", "REJECT_SCHEMA_MISMATCH", "SCHEMA_MISMATCH"),
    ("G-FAIL::047", "REQUEST_CONTAINS_FORBIDDEN_EXPECTED_SOURCE_EPOCH_OR_INPUT_LOCK_FIELD", "REJECT_SCHEMA_MISMATCH", "SCHEMA_MISMATCH"),
    ("G-FAIL::048", "REQUEST_CONTAINS_FORBIDDEN_REQUESTED_AT_OR_EVALUATED_AT_FIELD", "REJECT_SCHEMA_MISMATCH", "SCHEMA_MISMATCH"),
    ("G-FAIL::049", "CURRENT_RESOLUTION_CARRIES_PRESENT_BLOCKERS", "REJECT_SCHEMA_MISMATCH", "SCHEMA_MISMATCH"),
    ("G-FAIL::050", "STALE_RESOLUTION_CARRIES_CURRENT_PROJECTION_BUNDLE", "REJECT_SCHEMA_MISMATCH", "SCHEMA_MISMATCH"),
    ("G-FAIL::051", "BLOCKED_RESOLUTION_CARRIES_EXPLICIT_EMPTY_NO_BLOCKERS", "REJECT_SCHEMA_MISMATCH", "SCHEMA_MISMATCH"),
    ("G-FAIL::052", "CURRENT_CENTRAL_BUNDLE_MISSING_ONE_DIRECT_OWNER_PROJECTION", "REJECT_PARTIAL_OWNER_BUNDLE", "SCHEMA_MISMATCH"),
    ("G-FAIL::053", "DIRECT_OWNER_RESOLVER_RECEIVES_WRONG_CONSUMER_CONTRACT", "REJECT_OWNER_TOPOLOGY_MISMATCH", "INPUT_OWNER_MISMATCH"),
    ("G-FAIL::054", "DASHBOARD_RESOLVER_RECEIVES_CENTRAL_G_OR_F_INPUT_INSTEAD_OF_SVC1_OWNER_RESOLUTION", "REJECT_OWNER_CHAIN_BYPASS", "INPUT_OWNER_MISMATCH"),
    ("G-FAIL::055", "DASHBOARD_RESOLVER_CHANGES_SVC1_STALE_OR_BLOCKED_ABSENCE", "REJECT_LINEAGE_REWRITE", "SCHEMA_MISMATCH"),
    ("G-FAIL::056", "OWNER_ARTIFACT_WRITE_OUTSIDE_EXISTING_OWNER_PREFIX", "REJECT_PATH_SCOPE", "PATH_UNSAFE"),
    ("G-FAIL::057", "GENERATED_CONTRACT_DESCRIPTOR_CONTAINS_FABRICATED_RUNTIME_EVIDENCE_INSTANCE", "REJECT_EVIDENCE_FABRICATION", "ST12F_FIXTURE_NOT_EVIDENCE"),
    ("G-FAIL::058", "GENERATED_DESCRIPTOR_HAS_EXTRA_OR_MISSING_FIELD", "REJECT_SCHEMA_MISMATCH", "SCHEMA_MISMATCH"),
    ("G-FAIL::059", "CONSUMER_FIELD_BINDING_REFERENCES_UNKNOWN_SOURCE_FIELD", "REJECT_SCHEMA_MISMATCH", "SCHEMA_MISMATCH"),
    ("G-FAIL::060", "FILESYSTEM_READ_DURING_PURE_COMPILER_OR_DIRECT_OWNER_MAPPER_CALL", "REJECT_RUNTIME_EFFECT_FORBIDDEN", "RUNTIME_EFFECT_FORBIDDEN"),
    ("G-FAIL::061", "NETWORK_OR_PROVIDER_CALL_DURING_G_COMPILATION_OR_OWNER_MAPPING", "REJECT_PROVIDER_ACCESS", "DIRECT_PROVIDER_FORBIDDEN"),
    ("G-FAIL::062", "OWNER_NATURAL_SLOT_SAME_ID_DIFFERENT_DESCRIPTOR", "REJECT_IDEMPOTENCY_CONFLICT", "IDEMPOTENCY_CONFLICT"),
    ("G-FAIL::063", "CENTRAL_COMPILER_INTRODUCES_CACHE_DATABASE_CURRENT_POINTER_OR_MUTABLE_STATE", "REJECT_DUPLICATE_AUTHORITY", "RUNTIME_EFFECT_FORBIDDEN"),
    ("G-FAIL::064", "NEW_PUBLIC_QKU_OPERATION_ADDED_FOR_G", "REJECT_OPERATION_AUTHORITY_EXPANSION", "OPERATION_NOT_ALLOWED"),
    ("G-FAIL::065", "NEW_DURABLE_RECEIPT_CLASS_ADDED_FOR_G", "REJECT_RECEIPT_AUTHORITY_EXPANSION", "SCHEMA_MISMATCH"),
    ("G-FAIL::066", "READ_ONLY_ST12F_HANDOFF_OR_RECEIPT_OWNER_MUTATED_BY_G", "REJECT_PREDECESSOR_MUTATION", "PATH_UNSAFE"),
    ("G-FAIL::067", "CURRENT_D_REFERENCE_UNAVAILABLE_STALE_CONFLICTING_OR_NOT_CURRENT", "RETURN_BLOCKED_NO_AUTHORITY", "EVIDENCE_REFERENCE_UNAVAILABLE_STALE_CONFLICTING_OR_SCOPE_MISMATCH"),
    ("G-FAIL::068", "CONTEXT_INPUT_SNAPSHOT_ID_DIFFERS_FROM_DURABLE_INPUT_LOCK", "REJECT_CONTEXT_SCOPE_MISMATCH", "INPUT_SCOPE_MISMATCH"),
    ("G-FAIL::069", "CONTEXT_MARKET_VENUE_OR_INSTRUMENT_SCOPE_OUTSIDE_DURABLE_INPUT_LOCK", "REJECT_CONTEXT_SCOPE_MISMATCH", "INPUT_SCOPE_MISMATCH"),
    ("G-FAIL::070", "TRUSTED_EXECUTION_CONTEXT_IS_STALE", "RETURN_STALE_NO_AUTHORITY", "STALE_CONTEXT"),
)


def _read_json(path: str) -> object:
    def reject_duplicates(pairs: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate JSON key: {key}")
            result[key] = value
        return result

    return json.loads(
        (REPO_ROOT / path).read_text(encoding="utf-8"),
        object_pairs_hook=reject_duplicates,
        parse_constant=lambda value: (_ for _ in ()).throw(
            ValueError(f"non-finite JSON constant: {value}")
        ),
    )


def _read_one_jsonl(path: str) -> dict[str, object]:
    lines = [
        line
        for line in (REPO_ROOT / path).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if len(lines) != 1:
        raise ValueError(f"{path} must contain exactly one row")
    value = json.loads(lines[0])
    if type(value) is not dict:
        raise ValueError(f"{path} row must be an object")
    return value


def _field_names(contract: type[object]) -> tuple[str, ...]:
    return tuple(field.name for field in fields(contract))


def validate_projection_field_binding_candidate(
    candidate: object,
) -> None:
    """Independently validate one mutated frozen binding against real types."""

    expected_keys = {
        "absence_rule",
        "binding_id",
        "binding_scope",
        "consumer_field",
        "consumer_ids",
        "freshness_rule",
        "independent_oracle",
        "runtime_effect_authority",
        "source_contract",
        "source_field_or_rule",
        "stale_rule",
        "transformation",
        "units_and_basis",
    }
    if type(candidate) is not dict or set(candidate) != expected_keys:
        raise ContractValidationError(
            ReasonCode.SCHEMA_MISMATCH,
            "projection binding row schema differs",
        )
    allowed_consumer_fields = set(EXPECTED_CORE_FIELDS)
    for roster in EXPECTED_TYPE_FIELDS.values():
        allowed_consumer_fields.update(roster)
    if candidate["consumer_field"] not in allowed_consumer_fields:
        raise ContractValidationError(
            ReasonCode.SCHEMA_MISMATCH,
            "projection binding references an unknown consumer field",
        )
    if candidate["transformation"] != "IDENTITY":
        return
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.evidence import (  # noqa: PLC0415
        ComputationEvidenceBundleV1,
        FToGHandoffReferencesV1,
    )
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.input_lock import (  # noqa: PLC0415
        ImmutableReplayPaperInputLockV1,
    )
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.models import (  # noqa: PLC0415
        ComputationExecutionContextV1,
        ST12FEvidenceReferenceV1,
    )

    source_types = {
        contract.__name__: contract
        for contract in (
            ComputationExecutionContextV1,
            ImmutableReplayPaperInputLockV1,
            FToGHandoffReferencesV1,
            ComputationEvidenceBundleV1,
            ST12FEvidenceReferenceV1,
        )
    }
    source_type = source_types.get(str(candidate["source_contract"]))
    if source_type is not None and candidate["source_field_or_rule"] not in {
        field.name for field in fields(source_type)
    }:
        raise ContractValidationError(
            ReasonCode.SCHEMA_MISMATCH,
            "projection binding references an unknown source field",
        )


def validate_static_architecture_candidate(candidate_source: object) -> None:
    """Reject one declared mutation of the real compiler source contract."""

    if type(candidate_source) is not str or not candidate_source.strip():
        raise ContractValidationError(
            ReasonCode.SCHEMA_MISMATCH,
            "compiler source candidate must be nonempty text",
        )
    try:
        tree = ast.parse(candidate_source)
    except SyntaxError as exc:
        raise ContractValidationError(
            ReasonCode.SCHEMA_MISMATCH,
            "compiler source candidate is not valid Python",
        ) from exc
    compiler = next(
        (
            node
            for node in tree.body
            if isinstance(node, ast.ClassDef)
            and node.name == "ExistingOwnerProjectionCompilerV2"
        ),
        None,
    )
    if compiler is None:
        raise ContractValidationError(
            ReasonCode.SCHEMA_MISMATCH,
            "compiler source candidate omits the canonical compiler",
        )
    state_store_names = {
        "state_store",
        "database",
        "current_pointer",
        "projection_store",
    }
    assigned_names = {
        target.id
        for node in ast.walk(compiler)
        if isinstance(node, (ast.Assign, ast.AnnAssign))
        for target in (
            node.targets if isinstance(node, ast.Assign) else (node.target,)
        )
        if isinstance(target, ast.Name)
    }
    if assigned_names & state_store_names:
        raise ContractValidationError(
            ReasonCode.INPUT_OWNER_MISMATCH,
            "compiler candidate introduces a second state owner",
        )
    if assigned_names & {"cache", "mutable_state", "current_projection"}:
        raise ContractValidationError(
            ReasonCode.RUNTIME_EFFECT_FORBIDDEN,
            "compiler candidate introduces cached or mutable runtime state",
        )
    slots = next(
        (
            node.value
            for node in compiler.body
            if isinstance(node, ast.Assign)
            and any(
                isinstance(target, ast.Name) and target.id == "__slots__"
                for target in node.targets
            )
        ),
        None,
    )
    if not isinstance(slots, ast.Tuple) or slots.elts:
        raise ContractValidationError(
            ReasonCode.RUNTIME_EFFECT_FORBIDDEN,
            "compiler candidate introduces mutable or cached instance state",
        )
    call_names = {
        node.func.id
        if isinstance(node.func, ast.Name)
        else node.func.attr
        for node in ast.walk(compiler)
        if isinstance(node, ast.Call)
        and isinstance(node.func, (ast.Name, ast.Attribute))
    }
    if call_names & {
        "recompute_economic_or_statistical_value",
        "compute_math",
        "get_math_callable",
        "mean",
        "median",
    }:
        raise ContractValidationError(
            ReasonCode.FORMULA_EXECUTION_REJECTED,
            "compiler candidate introduces economic or statistical recomputation",
        )
    if call_names & {"sorted", "sort", "deduplicate", "unique"}:
        raise ContractValidationError(
            ReasonCode.SCHEMA_MISMATCH,
            "compiler candidate rewrites projected reference order",
        )
    if call_names & {"open", "read_text", "read_bytes", "write_text", "write_bytes"}:
        raise ContractValidationError(
            ReasonCode.RUNTIME_EFFECT_FORBIDDEN,
            "compiler candidate introduces filesystem I/O",
        )
    imported_roots = {
        alias.name.split(".", 1)[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    } | {
        node.module.split(".", 1)[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    }
    if imported_roots & {"requests", "socket", "httpx", "urllib", "openai"} or call_names & {
        "connect",
        "request",
        "urlopen",
    }:
        raise ContractValidationError(
            ReasonCode.DIRECT_PROVIDER_FORBIDDEN,
            "compiler candidate introduces a provider or network call",
        )


def validate_public_operation_roster_candidate(
    candidate_names: object,
) -> None:
    """Reject additions to the existing public QKU operation owner."""

    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.service import (  # noqa: PLC0415
        QKUComputationControlPlaneV1,
    )

    actual = {
        name
        for name, value in QKUComputationControlPlaneV1.__dict__.items()
        if callable(value) and not name.startswith("_")
    }
    if not isinstance(candidate_names, (tuple, frozenset, set)) or any(
        type(name) is not str for name in candidate_names
    ):
        raise ContractValidationError(
            ReasonCode.SCHEMA_MISMATCH,
            "public operation roster candidate must be exact text",
        )
    additions = set(candidate_names) - actual
    if additions:
        raise ContractValidationError(
            ReasonCode.OPERATION_NOT_ALLOWED,
            f"public QKU operation additions are forbidden: {sorted(additions)}",
        )


def validate_receipt_class_roster_candidate(candidate_names: object) -> None:
    """Reject a G receipt-class addition to the existing ST12-F owner."""

    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.receipts import (  # noqa: PLC0415
        ST12FReceiptClassV1,
    )

    actual = {member.name for member in ST12FReceiptClassV1}
    if not isinstance(candidate_names, (tuple, frozenset, set)) or any(
        type(name) is not str for name in candidate_names
    ):
        raise ContractValidationError(
            ReasonCode.SCHEMA_MISMATCH,
            "receipt class roster candidate must be exact text",
        )
    if set(candidate_names) - actual:
        raise ContractValidationError(
            ReasonCode.SCHEMA_MISMATCH,
            "ST12-G cannot add a durable receipt class",
        )


def validate_st12g_changed_path_candidate(candidate_path: object) -> None:
    """Apply the canonical exact-path owner to one proposed G write."""

    if type(candidate_path) is not str or not scope.is_pr_scoped_changed_path_allowed(
        EXPECTED_BRANCH, candidate_path
    ):
        raise ContractValidationError(
            ReasonCode.PATH_UNSAFE,
            "candidate path is outside the exact ST12-G write scope",
        )


def _function(tree: ast.Module, class_name: str, function_name: str) -> ast.FunctionDef:
    owner = next(
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == class_name
    )
    return next(
        node
        for node in owner.body
        if isinstance(node, ast.FunctionDef) and node.name == function_name
    )


def _test_contract_failures() -> list[str]:
    failures: list[str] = []
    if frozenset(projection.__all__) != EXPECTED_PUBLIC_NAMES:
        failures.append("public ST12-G type roster differs")
    if _field_names(projection.ST12GProjectionCoreV2) != EXPECTED_CORE_FIELDS:
        failures.append("shared core is not the exact ordered 33-field contract")
    for type_name, expected_fields in EXPECTED_TYPE_FIELDS.items():
        if _field_names(getattr(projection, type_name)) != expected_fields:
            failures.append(f"field roster differs: {type_name}")
    for type_name in EXPECTED_PUBLIC_NAMES:
        value = getattr(projection, type_name)
        if hasattr(value, "__dataclass_fields__"):
            params = value.__dataclass_params__
            if not params.frozen or not hasattr(value, "__slots__"):
                failures.append(f"contract is not frozen and slotted: {type_name}")
    if projection.ExistingOwnerProjectionCompilerV2.__slots__ != ():
        failures.append("compiler owns state")
    signature = tuple(
        inspect.signature(
            projection.ExistingOwnerProjectionCompilerV2.compile_current
        ).parameters
    )
    if signature != (
        "self",
        "context",
        "input_lock",
        "handoff",
        "bundle",
        "current_d_reference",
        "owner_views",
    ):
        failures.append("compiler input roster differs")

    source_path = (
        REPO_ROOT
        / "src/qtt/stage1_prediction_markets/qku_computation_control_plane/"
        "existing_owner_projection.py"
    )
    tree = ast.parse(source_path.read_text(encoding="utf-8"))
    compiler = _function(tree, "ExistingOwnerProjectionCompilerV2", "compile_current")
    forbidden_calls = {
        "open",
        "read_text",
        "read_bytes",
        "write_text",
        "write_bytes",
        "connect",
        "request",
        "urlopen",
    }
    if any(
        isinstance(node, ast.Call)
        and (
            isinstance(node.func, ast.Name) and node.func.id in forbidden_calls
            or isinstance(node.func, ast.Attribute) and node.func.attr in forbidden_calls
        )
        for node in ast.walk(compiler)
    ):
        failures.append("compiler contains I/O or provider call")
    coordinator = _function(
        tree,
        "ExistingOwnerProjectionCoordinatorV2",
        "resolve",
    )
    call_counts = {
        method: sum(
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == method
            for node in ast.walk(coordinator)
        )
        for method in (
            "resolve_g_handoff",
            "resolve_control_receipt",
            "resolve_bundle",
            "read_evidence_reference",
        )
    }
    if set(call_counts.values()) != {1}:
        failures.append(f"coordinator durable-read budget differs: {call_counts}")
    return failures


def _materialization_failures() -> list[str]:
    failures: list[str] = []
    manifest = _read_json(CENTRAL_MANIFEST)
    if type(manifest) is not dict:
        return ["central manifest is not an object"]
    if (
        manifest.get("contract_version") != "2.0"
        or manifest.get("shared_core_field_count") != 33
        or manifest.get("source_binding_row_count") != 71
        or manifest.get("direct_consumer_ids")
        != ["READINESS1", "PRETRADE1", "AGENT_ORCH1", "SVC1"]
        or manifest.get("derived_consumer_id") != "DASH1_UI1"
        or manifest.get("runtime_instance_state")
        != "NOT_MATERIALIZED_BY_REPOSITORY_BUILD"
        or manifest.get("runtime_effect_allowed") is not False
        or manifest.get("write_authority") != "NONE"
    ):
        failures.append("central materialization manifest differs")
    if manifest.get("owner_descriptor_refs") != [
        details[0] for details in DESCRIPTORS.values()
    ]:
        failures.append("central owner descriptor roster differs")
    no_effects = manifest.get("no_effect_flags")
    if type(no_effects) is not dict or len(no_effects) != 8 or any(no_effects.values()):
        failures.append("central no-effect roster differs")

    for consumer_id, (path, contract_type, downstream) in DESCRIPTORS.items():
        row = _read_one_jsonl(path)
        if frozenset(row) != EXPECTED_DESCRIPTOR_FIELDS:
            failures.append(f"descriptor field roster differs: {consumer_id}")
            continue
        if (
            row["descriptor_id"] != f"ST12G-DESCRIPTOR::{consumer_id}"
            or row["contract_version"] != "2.0"
            or row["consumer_id"] != consumer_id
            or row["contract_type"] != contract_type
            or row["source_contract_manifest_ref"] != CENTRAL_MANIFEST
            or row["runtime_instance_state"]
            != "NOT_MATERIALIZED_BY_REPOSITORY_BUILD"
            or row["manual_edit_allowed"] is not False
            or row["runtime_effect_allowed"] is not False
            or row["write_authority"] != "NONE"
            or row["downstream_route_refs"] != list(downstream)
        ):
            failures.append(f"descriptor value contract differs: {consumer_id}")
        if any(
            forbidden in row
            for forbidden in ("runtime_evidence", "evidence_value", "owner_decision")
        ):
            failures.append(f"descriptor fabricates runtime evidence: {consumer_id}")
    return failures


def _extract_behavior_definitions(
    tree: ast.Module,
    table_name: str,
) -> list[dict[str, str]]:
    module_strings = {
        target.id: str(node.value.value)
        for node in tree.body
        if isinstance(node, ast.Assign)
        and isinstance(node.value, ast.Constant)
        and type(node.value.value) is str
        for target in node.targets
        if isinstance(target, ast.Name)
    }

    def string_value(node: ast.expr) -> str | None:
        if isinstance(node, ast.Constant) and type(node.value) is str:
            return str(node.value)
        if isinstance(node, ast.Name):
            return module_strings.get(node.id)
        return None

    assignment = next(
        (
            node
            for node in tree.body
            if isinstance(node, ast.Assign)
            and any(
                isinstance(target, ast.Name) and target.id == table_name
                for target in node.targets
            )
        ),
        None,
    )
    if assignment is None or not isinstance(assignment.value, (ast.Tuple, ast.List)):
        return []
    field_names = (
        "case_id",
        "verification_mode",
        "valid_baseline_factory",
        "declared_mutation_action",
        "production_entrypoint",
        "expected_terminal_outcome",
        "expected_reason_code",
        "predecessor_proof_reference",
    )
    definitions: list[dict[str, str]] = []
    for value in assignment.value.elts:
        if (
            not isinstance(value, ast.Call)
            or not isinstance(value.func, ast.Name)
            or value.func.id != "_BehaviorCase"
            or value.keywords
            or len(value.args) != len(field_names)
            or any(string_value(argument) is None for argument in value.args)
        ):
            definitions.append({"case_id": "INVALID_CASE_DEFINITION"})
            continue
        definitions.append(
            dict(
                zip(
                    field_names,
                    (string_value(argument) or "" for argument in value.args),
                    strict=True,
                )
            )
        )
    return definitions


def _reference_binding_failure(reference: str, *, allow_tests: bool) -> str | None:
    if "::" not in reference:
        return "reference lacks exact path and symbol binding"
    path_text, symbol = reference.split("::", 1)
    if not path_text or not symbol or Path(path_text).is_absolute():
        return "reference path or symbol is invalid"
    if not allow_tests and path_text.startswith("tests/"):
        return "test helper is not a production/current-owner entrypoint"
    path = REPO_ROOT / path_text
    if not path.is_file() or path.suffix != ".py":
        return "reference path is not an existing Python owner"
    final_symbol = symbol.rsplit(".", 1)[-1]
    if final_symbol not in path.read_text(encoding="utf-8"):
        return "reference symbol is absent from the named owner"
    return None


def _behavior_case_definition_failures(
    definition: Mapping[str, str],
    frozen: tuple[str, str, str, str],
) -> list[str]:
    failures: list[str] = []
    case_id, trigger, outcome, reason = frozen
    if definition.get("case_id") != case_id:
        failures.append("case identity differs")
    mode = definition.get("verification_mode", "")
    if mode not in ALLOWED_VERIFICATION_MODES:
        failures.append("verification mode is not allowed")
    baseline = definition.get("valid_baseline_factory", "")
    if not baseline or baseline in {"NONE", "N/A"}:
        failures.append("valid baseline factory is absent")
    mutation = definition.get("declared_mutation_action", "")
    if mutation != trigger or len(mutation.split("_")) < 2:
        failures.append("declared mutation is empty, nonspecific, or differs")
    entrypoint = definition.get("production_entrypoint", "")
    lowered_entrypoint = entrypoint.casefold()
    if (
        not entrypoint
        or "reasoncode" in lowered_entrypoint
        or "enum" in lowered_entrypoint
        or "_descriptor_guard" in lowered_entrypoint
        or "_validate_binding_source" in lowered_entrypoint
    ):
        failures.append("enum-only, tautological, or test-helper-only entrypoint")
    else:
        binding_failure = _reference_binding_failure(
            entrypoint,
            allow_tests=False,
        )
        if binding_failure:
            failures.append(f"entrypoint {binding_failure}")
    if definition.get("expected_terminal_outcome") != outcome:
        failures.append("terminal outcome differs from frozen matrix")
    if definition.get("expected_reason_code") != reason:
        failures.append("reason differs from frozen matrix")
    proof = definition.get("predecessor_proof_reference", "")
    if mode == "EXISTING_OWNER_REJECTION_PROPAGATION":
        if not proof or proof == "NONE":
            failures.append("propagation row lacks predecessor proof binding")
        else:
            binding_failure = _reference_binding_failure(
                proof,
                allow_tests=True,
            )
            if binding_failure:
                failures.append(f"predecessor proof {binding_failure}")
    elif proof != "NONE":
        failures.append("non-propagation row declares a predecessor proof")
    if mode == "STATIC_ARCHITECTURE_MUTATION_DETECTION" and not entrypoint.startswith(
        "tools/independent_validate_qku_computation_control_plane_g.py::validate_"
    ):
        failures.append("static mutation row is not bound to the independent validator")
    return failures


def _behavior_definition_failures(
    trees: Sequence[ast.Module],
) -> list[str]:
    failures: list[str] = []
    definitions = [
        *_extract_behavior_definitions(trees[0], "_FAIL_CASES_CONTRACT"),
        *_extract_behavior_definitions(trees[1], "_FAIL_CASES_CONSUMER"),
    ]
    frozen_by_id = {row[0]: row for row in EXPECTED_FAIL_CLOSED_ROWS}
    counts = Counter(row.get("case_id", "") for row in definitions)
    if len(definitions) != 70:
        failures.append(f"behavior case definition count differs: {len(definitions)}")
    for case_id in sorted(frozen_by_id):
        if counts[case_id] != 1:
            failures.append(
                f"behavior case definition cardinality differs: {case_id}:{counts[case_id]}"
            )
            continue
        definition = next(row for row in definitions if row.get("case_id") == case_id)
        failures.extend(
            f"{case_id}: {failure}"
            for failure in _behavior_case_definition_failures(
                definition,
                frozen_by_id[case_id],
            )
        )
    extras = sorted(set(counts) - set(frozen_by_id))
    if extras:
        failures.append(f"unexpected behavior case definitions: {extras}")
    modes = Counter(row.get("verification_mode", "") for row in definitions)
    if set(modes) != set(ALLOWED_VERIFICATION_MODES):
        failures.append(f"verification-mode closure differs: {dict(modes)}")
    fabricated = {
        "case_id": "G-FAIL::001",
        "verification_mode": "PRODUCTION_MUTATION_REJECTION",
        "valid_baseline_factory": "VALID_BASELINE",
        "declared_mutation_action": "HANDOFF_RECEIPT_MISSING",
        "production_entrypoint": "ReasonCode.OWNER_DATA_MISSING",
        "expected_terminal_outcome": "REJECT_NO_PROJECTION",
        "expected_reason_code": "OWNER_DATA_MISSING",
        "predecessor_proof_reference": "NONE",
    }
    negative_failures = _behavior_case_definition_failures(
        fabricated,
        frozen_by_id["G-FAIL::001"],
    )
    if not any("enum-only" in failure for failure in negative_failures):
        failures.append("enum-only negative validator self-test did not fail closed")
    return failures


def _test_partition_failures() -> list[str]:
    failures: list[str] = []
    test_paths = (
        "tests/stage1_prediction_markets/qku_computation_control_plane/"
        "tranche_g/test_contract_matrix.py",
        "tests/stage1_prediction_markets/qku_computation_control_plane/"
        "tranche_g/test_consumer_integration_matrix.py",
    )
    trees = [
        ast.parse((REPO_ROOT / path).read_text(encoding="utf-8"))
        for path in test_paths
    ]
    test_functions = {
        node.name
        for tree in trees
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name.startswith("test_")
    }
    if test_functions != {"test_st12g_contract_case", "test_st12g_consumer_case"}:
        failures.append("created test function roster differs")
    strings = {
        node.value
        for tree in trees
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and type(node.value) is str
    }
    historical = {
        value for value in strings if re.fullmatch(r"ST12-TEST::\d{3}", value)
    }
    fail_closed = {
        value for value in strings if re.fullmatch(r"G-FAIL::\d{3}", value)
    }
    if historical != EXPECTED_HISTORICAL_IDS:
        failures.append("historical semantic identity roster differs")
    if fail_closed != {f"G-FAIL::{index:03d}" for index in range(1, 71)}:
        failures.append("70-case fail-closed roster differs")
    failures.extend(_behavior_definition_failures(trees))
    return failures


def _validation_wiring_failures() -> list[str]:
    failures: list[str] = []
    if scope.ST12G_BRANCH != EXPECTED_BRANCH:
        failures.append("authorized branch differs")
    if len(scope.ST12G_ALLOWED_EXACT_PATHS) != 65:
        failures.append("authorized path denominator differs")
    if len(scope.ST12G_FORBIDDEN_EXACT_PATHS) != 7:
        failures.append("forbidden path denominator differs")
    if any("*" in path for path in scope.ST12G_ALLOWED_EXACT_PATHS):
        failures.append("authorized path registry contains wildcard")
    if ci_branch_context.is_owner_authorized_validation_branch(
        f"{EXPECTED_BRANCH}-near"
    ):
        failures.append("near-name branch accepted")
    if not ci_branch_context.is_owner_authorized_validation_branch(EXPECTED_BRANCH):
        failures.append("exact authorized branch rejected")
    expected_commands = (
        "python tools/validate_qku_computation_control_plane.py --domain g",
        "python tools/independent_validate_qku_computation_control_plane_g.py",
        "python tools/validate_validation_inventory.py",
        "python -m pytest tests/stage1_prediction_markets/qku_computation_control_plane/tranche_g/test_contract_matrix.py -q",
        "python -m pytest tests/stage1_prediction_markets/qku_computation_control_plane/tranche_g/test_consumer_integration_matrix.py -q",
        "python tools/run_validation_gates.py --phase all --validation-mode full",
    )
    if inventory.ST12G_EXACT_VALIDATION_COMMANDS != expected_commands:
        failures.append("six-command validation roster differs")
    known = inventory.inventory_by_id()
    missing = inventory.ST12G_REQUIRED_VALIDATOR_IDS - known.keys()
    if missing:
        failures.append(f"registered ST12-G validators missing: {sorted(missing)}")
    classified = router._classify_changed_files(
        tuple(sorted(scope.ST12G_ALLOWED_EXACT_PATHS))
    )[0]
    for path in scope.ST12G_ALLOWED_EXACT_PATHS:
        routed = set(classified.get(path, ()))
        if not inventory.ST12G_REQUIRED_VALIDATOR_IDS <= routed:
            failures.append(f"incomplete ST12-G route: {path}")
            break
    return failures


def main() -> int:
    failures: list[str] = []
    for validator in (
        _test_contract_failures,
        _materialization_failures,
        _test_partition_failures,
        _validation_wiring_failures,
    ):
        try:
            failures.extend(validator())
        except Exception as exc:
            failures.append(f"{validator.__name__}: {type(exc).__name__}: {exc}")
    if failures:
        print("QKU_COMPUTATION_CONTROL_PLANE_INDEPENDENT_G_VALIDATION_FAILED")
        for failure in failures:
            print(failure)
        return 1
    print(
        f"{SUCCESS_MARKER} public_types=20 core_fields=33 owners=5 "
        "field_bindings=71 historical_cases=15 fail_closed_cases=70 "
        "authorized_paths=65 validation_commands=6"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
