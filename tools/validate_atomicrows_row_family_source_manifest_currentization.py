#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
import pathlib
import sys
from typing import Any, Mapping, Sequence

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tools.build_master_plan_section_coverage_report import (  # noqa: E402
    RegistryParseError,
    load_yaml_subset,
)
from tools.validate_master_plan_section_coverage import (  # noqa: E402
    validate_json_schema_subset,
)


SUCCESS_MARKER = "QTT_ATOMICROWS_ROW_FAMILY_SOURCE_MANIFEST_CURRENTIZATION_OK"
FAILURE_MARKER = "QTT_ATOMICROWS_ROW_FAMILY_SOURCE_MANIFEST_CURRENTIZATION_FAILED"
AUTHORITY_CLASS = (
    "STATIC_ATOMICROWS_ROW_FAMILY_SOURCE_MANIFEST_CURRENTIZATION_ONLY_NOT_BUNDLE_"
    "MUTATION_NOT_SOURCE_MUTATION_NOT_FINAL_READINESS"
)
MANIFEST_ID = "ATOMICROWS_ROW_FAMILY_SOURCE_MANIFEST_CURRENTIZATION"
MANIFEST_VERSION = "v1"
REPO_CURRENT_SEQUENCE_LABEL = "PR139"
CURRENTIZATION_STATUS = "REQUIRED_STATIC_CURRENTIZATION_PENDING"
STATIC_BOUNDARY = (
    "Static AtomicRows row-family source manifest currentization only. Future "
    "enrichment requirements are explicit; no live, order, source acceptance, "
    "connector binding, replay, paper, neural, quantum backend, profit, final "
    "readiness, or trading readiness authority is created."
)

DEFAULT_SCHEMA = pathlib.Path(
    "schemas/atomicrows/atomicrows_row_family_source_manifest_currentization.schema.json"
)
DEFAULT_MANIFEST = pathlib.Path(
    "docs/master_plan/atomic_rows/AtomicRowsRowFamilySourceManifestCurrentization.yaml"
)
DEFAULT_FIXTURE = pathlib.Path(
    "tests/fixtures/atomicrows/"
    "synthetic_atomicrows_row_family_source_manifest_currentization.v1.fixture.json"
)
DEFAULT_REPORT = pathlib.Path(
    "docs/master_plan/generated/"
    "AtomicRowsRowFamilySourceManifestCurrentization.report.json"
)

ROW_FAMILY_SOURCE_DIRECTORY = pathlib.Path(
    "docs/master_plan/atomic_rows/pr98_row_family_sources"
)
ATOMICROWS_BUNDLE_PATH = pathlib.Path("docs/master_plan/atomic_rows/AtomicRows.bundle.jsonl")
MASTER_PLAN_PATH = pathlib.Path("docs/master_plan/QTT_MasterPlan_Current.md")

PR136_JSON_EVIDENCE_REFS: tuple[tuple[str, pathlib.Path], ...] = (
    ("pr136_route_triage_ref", pathlib.Path("docs/master_plan/generated/PR136RouteTriage.report.json")),
    ("pr136_read_receipt_ref", pathlib.Path("docs/master_plan/generated/PR136ReadReceipt.report.json")),
    (
        "pr136_master_plan_coverage_to_readiness_domain_map_ref",
        pathlib.Path("docs/master_plan/generated/PR136MasterPlanCoverageToReadinessDomainMap.report.json"),
    ),
    (
        "pr136_market_specific_launch_readiness_index_ref",
        pathlib.Path("docs/master_plan/generated/PR136MarketSpecificLaunchReadinessIndex.report.json"),
    ),
    (
        "pr136_command_action_matrix_ref",
        pathlib.Path("docs/master_plan/generated/PR136CommandActionMatrix.report.json"),
    ),
    (
        "pr136_agent_launch_orchestration_map_ref",
        pathlib.Path("docs/master_plan/generated/PR136AgentLaunchOrchestrationMap.report.json"),
    ),
    (
        "pr136_launch_readiness_dependency_graph_ref",
        pathlib.Path("docs/master_plan/generated/PR136LaunchReadinessDependencyGraph.report.json"),
    ),
    (
        "pr136_quantum_atomicrows_optimization_readiness_map_ref",
        pathlib.Path("docs/master_plan/generated/PR136QuantumAtomicRowsOptimizationReadinessMap.report.json"),
    ),
    (
        "pr136_post_pr135_roadmap_sequence_ref",
        pathlib.Path("docs/master_plan/generated/PR136PostPR135RoadmapSequence.report.json"),
    ),
    (
        "pr136_future_pr_card_registry_ref",
        pathlib.Path("docs/master_plan/generated/PR136FuturePRCardRegistry.report.json"),
    ),
    (
        "pr136_roadmap_replacement_and_insertion_matrix_ref",
        pathlib.Path("docs/master_plan/generated/PR136RoadmapReplacementAndInsertionMatrix.report.json"),
    ),
    (
        "pr136_day1_launch_readiness_roadmap_ref",
        pathlib.Path("docs/master_plan/generated/PR136Day1LaunchReadinessRoadmap.report.json"),
    ),
    (
        "pr136_policy_manifest_ref",
        pathlib.Path("docs/master_plan/generated/PR136PolicyManifest.report.json"),
    ),
    (
        "pr136_policy_literal_drift_ref",
        pathlib.Path("docs/master_plan/generated/PR136PolicyLiteralDrift.report.json"),
    ),
    (
        "pr136_validation_gate_integration_ref",
        pathlib.Path("docs/master_plan/generated/PR136ValidationGateIntegration.report.json"),
    ),
)
ATOMICROWS_JSON_EVIDENCE_REFS: tuple[tuple[str, pathlib.Path], ...] = (
    (
        "pr137r_report_ref",
        pathlib.Path("docs/master_plan/generated/PR137R_AtomicRowsBundleReconciliation.report.json"),
    ),
    (
        "pr137r_index_ref",
        pathlib.Path("docs/master_plan/generated/PR137R_AtomicRowsBundleReconciliation.index.json"),
    ),
    (
        "pr137l_report_ref",
        pathlib.Path("docs/master_plan/generated/PR137L_LatencyHotPathSnapshotBoundary.report.json"),
    ),
    (
        "pr137l_index_ref",
        pathlib.Path("docs/master_plan/generated/PR137L_LatencyHotPathSnapshotBoundary.index.json"),
    ),
    (
        "pr138_semantic_contract_report_ref",
        pathlib.Path("docs/master_plan/generated/PR138_AtomicRowsSemanticRowContract.report.json"),
    ),
    (
        "pr138_field_inventory_ref",
        pathlib.Path("docs/master_plan/generated/PR138_AtomicRowsSemanticFieldInventory.json"),
    ),
)
NON_JSON_EVIDENCE_REFS: tuple[tuple[str, pathlib.Path], ...] = (
    ("row_family_source_directory_ref", ROW_FAMILY_SOURCE_DIRECTORY),
    ("optional_existing_bundle_read_only_ref", ATOMICROWS_BUNDLE_PATH),
)
EVIDENCE_REF_FIELDS: tuple[tuple[str, pathlib.Path], ...] = (
    *PR136_JSON_EVIDENCE_REFS,
    *ATOMICROWS_JSON_EVIDENCE_REFS,
    *NON_JSON_EVIDENCE_REFS,
)
EVIDENCE_REF_FIELD_NAMES = tuple(field for field, _path in EVIDENCE_REF_FIELDS)

CANONICAL_STAGE1_VENUE_IDS = (
    "PREDICTION_MARKETS_GENERAL",
    "KALSHI",
    "POLYMARKET",
    "FORECASTEX_IBKR",
)
FORBIDDEN_VENUE_ALIASES = (
    "FORECASTEX",
    "FORECASTX",
    "IBKR_FORECASTX",
    "forecastx",
)

REQUIRED_TRUE_FLAGS = (
    "static_only_flag",
    "read_only_evidence_only_flag",
    "deterministic_output_flag",
)
REQUIRED_FALSE_FLAGS = (
    "roadmap_identity_inference_used",
    "source_file_mutation_allowed_flag",
    "bundle_mutation_allowed_flag",
    "semantic_value_materialization_allowed_flag",
    "final_readiness_created_flag",
    "runtime_live_order_authority_created_flag",
    "source_acceptance_created_flag",
    "connector_semantic_binding_created_flag",
    "replay_paper_execution_created_flag",
    "neural_training_or_inference_created_flag",
    "quantum_backend_execution_created_flag",
    "profit_latency_execution_superiority_claim_created_flag",
    "cryptographic_sidecar_authority_created_flag",
    "freeze_authority_created_flag",
)
PR136_ALIGNMENT_TRUE_FLAGS = (
    "pr136_control_plane_consumed_read_only",
    "pr136_same_number_inference_preserved_false",
    "pr136_no_authority_flags_preserved",
    "pr136_canonical_venue_ids_consumed",
    "pr136_master_plan_coverage_to_readiness_domain_map_consumed",
    "pr136_agent_launch_orchestration_map_consumed",
    "pr136_launch_readiness_dependency_graph_consumed",
    "pr136_quantum_atomicrows_optimization_readiness_map_consumed",
    "pr136_future_sequence_context_consumed",
    "pr136_did_not_override_repo_current_atomicrows_scope",
)
ENTRY_FALSE_FLAGS = (
    "semantic_value_materialization_allowed_flag",
    "source_file_mutation_allowed_flag",
    "bundle_mutation_allowed_flag",
)
FORBIDDEN_AUTHORITY_CLAIM_FIELDS = {
    "roadmap_identity_inference_used": "PR139_REASON_SAME_NUMBER_INFERENCE_FORBIDDEN",
    "source_file_mutation_allowed_flag": "PR139_REASON_SOURCE_MUTATION_FLAG_TRUE_FORBIDDEN",
    "bundle_mutation_allowed_flag": "PR139_REASON_BUNDLE_MUTATION_FLAG_TRUE_FORBIDDEN",
    "semantic_value_materialization_allowed_flag": (
        "PR139_REASON_SEMANTIC_VALUE_MATERIALIZATION_FLAG_TRUE_FORBIDDEN"
    ),
    "final_readiness_created_flag": "PR139_REASON_FINAL_READINESS_CLAIM_FORBIDDEN",
    "runtime_live_order_authority_created_flag": (
        "PR139_REASON_RUNTIME_LIVE_ORDER_AUTHORITY_CLAIM_FORBIDDEN"
    ),
    "source_acceptance_created_flag": "PR139_REASON_SOURCE_ACCEPTANCE_CLAIM_FORBIDDEN",
    "connector_semantic_binding_created_flag": (
        "PR139_REASON_CONNECTOR_SEMANTIC_BINDING_CLAIM_FORBIDDEN"
    ),
    "replay_paper_execution_created_flag": "PR139_REASON_REPLAY_PAPER_EXECUTION_CLAIM_FORBIDDEN",
    "neural_training_or_inference_created_flag": (
        "PR139_REASON_NEURAL_TRAINING_OR_INFERENCE_CLAIM_FORBIDDEN"
    ),
    "quantum_backend_execution_created_flag": (
        "PR139_REASON_QUANTUM_BACKEND_EXECUTION_CLAIM_FORBIDDEN"
    ),
    "profit_latency_execution_superiority_claim_created_flag": (
        "PR139_REASON_PROFIT_LATENCY_EXECUTION_SUPERIORITY_CLAIM_FORBIDDEN"
    ),
    "cryptographic_sidecar_authority_created_flag": (
        "PR139_REASON_CRYPTOGRAPHIC_FREEZE_SIDECAR_AUTHORITY_CLAIM_FORBIDDEN"
    ),
    "freeze_authority_created_flag": (
        "PR139_REASON_CRYPTOGRAPHIC_FREEZE_SIDECAR_AUTHORITY_CLAIM_FORBIDDEN"
    ),
    "live_use_allowed_flag": "PR139_REASON_RUNTIME_LIVE_ORDER_AUTHORITY_CLAIM_FORBIDDEN",
    "order_authority_created_flag": "PR139_REASON_RUNTIME_LIVE_ORDER_AUTHORITY_CLAIM_FORBIDDEN",
    "profit_evidence_created_flag": (
        "PR139_REASON_PROFIT_LATENCY_EXECUTION_SUPERIORITY_CLAIM_FORBIDDEN"
    ),
    "quantum_backend_execution_allowed_flag": (
        "PR139_REASON_QUANTUM_BACKEND_EXECUTION_CLAIM_FORBIDDEN"
    ),
    "external_fact_authority_flag": "PR139_REASON_SOURCE_ACCEPTANCE_CLAIM_FORBIDDEN",
}
FORBIDDEN_FIELD_NAME_FRAGMENTS = ("sha", "digest", "hash", "checksum")

EXPECTED_ROW_FAMILY_SOURCE_FILE_COUNT = 15
EXPECTED_BUNDLE_ROW_COUNT = 4183
EXPECTED_REQUIRED_FIELD_COUNT = 59
EXPECTED_REQUIRED_FIELD_GROUP_COUNT = 8

SEMANTIC_REQUIREMENT_FIELD_GROUPS = {
    "prediction_market_compatibility_requirements": "MARKET_VENUE_SCOPE",
    "quantum_metadata_currentization_requirements": "QUANTUM_COMPATIBILITY",
    "profit_risk_latency_objective_metadata_requirements": "TRADING_OBJECTIVE_SUPPORT",
    "agent_selection_replay_paper_requirements": "AGENT_CONSUMER_BINDING",
    "source_provenance_requirements": "SOURCE_PROVENANCE_BOUNDARY",
}
REPLAY_PAPER_GROUP_ID = "REPLAY_PAPER_LIVE_BOUNDARY"
REQUIREMENT_PLACEHOLDER = "REQUIRED_PENDING_FUTURE_STATIC_ENRICHMENT"
VENUE_COMPATIBILITY_PLACEHOLDER = "REQUIRES_STATIC_COMPATIBILITY_METADATA"

REASON_SCHEMA_FAILED = "PR139_REASON_SCHEMA_VALIDATION_FAILED"
REASON_IDENTITY_OR_AUTHORITY = "PR139_REASON_IDENTITY_OR_AUTHORITY_MISMATCH"
REASON_VALIDATOR_MARKER = "PR139_REASON_VALIDATOR_MARKER_MISMATCH"
REASON_EVIDENCE_MISSING_OR_MALFORMED = "PR139_REASON_EVIDENCE_MISSING_OR_MALFORMED"
REASON_PR136_ROUTE_TRIAGE_MISSING = "PR139_REASON_PR136_ROUTE_TRIAGE_EVIDENCE_MISSING"
REASON_PR136_COMMAND_MATRIX_MISSING = "PR139_REASON_PR136_COMMAND_ACTION_MATRIX_EVIDENCE_MISSING"
REASON_PR136_MARKET_INDEX_MISSING = "PR139_REASON_PR136_MARKET_INDEX_EVIDENCE_MISSING"
REASON_PR136_COVERAGE_MAP_MISSING = "PR139_REASON_PR136_COVERAGE_DOMAIN_MAP_EVIDENCE_MISSING"
REASON_PR136_AGENT_MAP_MISSING = "PR139_REASON_PR136_AGENT_ORCHESTRATION_EVIDENCE_MISSING"
REASON_PR136_DEPENDENCY_GRAPH_MISSING = "PR139_REASON_PR136_DEPENDENCY_GRAPH_EVIDENCE_MISSING"
REASON_PR136_QUANTUM_MAP_MISSING = "PR139_REASON_PR136_QUANTUM_ATOMICROWS_EVIDENCE_MISSING"
REASON_PR136_FUTURE_SEQUENCE_MISSING = "PR139_REASON_PR136_FUTURE_SEQUENCE_EVIDENCE_MISSING"
REASON_PR136_SAME_NUMBER = "PR139_REASON_SAME_NUMBER_INFERENCE_FORBIDDEN"
REASON_PR136_NO_AUTHORITY_DRIFT = "PR139_REASON_PR136_NO_AUTHORITY_FLAG_DRIFT"
REASON_CANONICAL_VENUE = "PR139_REASON_CANONICAL_VENUE_IDS_NOT_CONSUMED"
REASON_FORBIDDEN_VENUE_ALIAS = "PR139_REASON_FORBIDDEN_VENUE_ALIAS_USED"
REASON_PR137R_MISSING = "PR139_REASON_PR137R_EVIDENCE_MISSING"
REASON_PR137L_MISSING = "PR139_REASON_PR137L_EVIDENCE_MISSING"
REASON_PR138_MISSING = "PR139_REASON_PR138_EVIDENCE_MISSING"
REASON_ROW_FAMILY_COUNT = "PR139_REASON_ROW_FAMILY_SOURCE_FILE_COUNT_NOT_15"
REASON_ROW_COUNT = "PR139_REASON_EXISTING_BUNDLE_ROW_COUNT_NOT_4183"
REASON_REQUIRED_FIELD_COUNT = "PR139_REASON_PR138_REQUIRED_FIELD_COUNT_NOT_59"
REASON_REQUIRED_FIELD_GROUP_COUNT = "PR139_REASON_PR138_REQUIRED_FIELD_GROUP_COUNT_NOT_8"
REASON_MANIFEST_ENTRY_COUNT = "PR139_REASON_MANIFEST_ENTRY_COUNT_NOT_15"
REASON_SOURCE_FILE_MISSING = "PR139_REASON_SOURCE_FILE_MISSING"
REASON_DUPLICATE_FAMILY_ID = "PR139_REASON_DUPLICATE_FAMILY_ID"
REASON_DUPLICATE_SOURCE_PATH = "PR139_REASON_DUPLICATE_SOURCE_FILE_PATH"
REASON_REQUIRED_FIELD_MISSING = "PR139_REASON_REQUIRED_FIELD_ID_MISSING"
REASON_UNKNOWN_FIELD_ID = "PR139_REASON_UNKNOWN_FIELD_ID"
REASON_REQUIRED_FIELD_GROUP_MISSING = "PR139_REASON_REQUIRED_FIELD_GROUP_ID_MISSING"
REASON_UNKNOWN_FIELD_GROUP_ID = "PR139_REASON_UNKNOWN_FIELD_GROUP_ID"
REASON_MISSING_FIELD_NOT_TRACEABLE = "PR139_REASON_MISSING_FIELD_ID_NOT_TRACEABLE"
REASON_FALSE_FLAG = "PR139_REASON_REQUIRED_FALSE_AUTHORITY_FLAG_TRUE"
REASON_TRUE_FLAG = "PR139_REASON_REQUIRED_TRUE_STATIC_FLAG_FALSE"
REASON_CRYPTO_FIELD_NAME = "PR139_REASON_FORBIDDEN_FIELD_NAME_FRAGMENT"
REASON_OUTPUT_NOT_DETERMINISTIC = "PR139_REASON_OUTPUT_REPORT_NOT_DETERMINISTIC"
REASON_PROTECTED_MUTATION = "PR139_REASON_PROTECTED_ARTIFACT_MUTATION_DETECTED"
REASON_FIXTURE_INVALID = "PR139_REASON_FIXTURE_INVALID"

EVIDENCE_REASON_BY_FIELD = {
    "pr136_route_triage_ref": REASON_PR136_ROUTE_TRIAGE_MISSING,
    "pr136_command_action_matrix_ref": REASON_PR136_COMMAND_MATRIX_MISSING,
    "pr136_market_specific_launch_readiness_index_ref": REASON_PR136_MARKET_INDEX_MISSING,
    "pr136_master_plan_coverage_to_readiness_domain_map_ref": REASON_PR136_COVERAGE_MAP_MISSING,
    "pr136_agent_launch_orchestration_map_ref": REASON_PR136_AGENT_MAP_MISSING,
    "pr136_launch_readiness_dependency_graph_ref": REASON_PR136_DEPENDENCY_GRAPH_MISSING,
    "pr136_quantum_atomicrows_optimization_readiness_map_ref": REASON_PR136_QUANTUM_MAP_MISSING,
    "pr136_post_pr135_roadmap_sequence_ref": REASON_PR136_FUTURE_SEQUENCE_MISSING,
    "pr136_future_pr_card_registry_ref": REASON_PR136_FUTURE_SEQUENCE_MISSING,
    "pr136_roadmap_replacement_and_insertion_matrix_ref": REASON_PR136_FUTURE_SEQUENCE_MISSING,
    "pr137r_report_ref": REASON_PR137R_MISSING,
    "pr137r_index_ref": REASON_PR137R_MISSING,
    "pr137l_report_ref": REASON_PR137L_MISSING,
    "pr137l_index_ref": REASON_PR137L_MISSING,
    "pr138_semantic_contract_report_ref": REASON_PR138_MISSING,
    "pr138_field_inventory_ref": REASON_PR138_MISSING,
}

NEGATIVE_FIXTURE_EXPECTATIONS: tuple[tuple[str, str], ...] = (
    ("MISSING_PR136_ROUTE_TRIAGE_EVIDENCE", REASON_PR136_ROUTE_TRIAGE_MISSING),
    ("MISSING_PR136_COVERAGE_DOMAIN_MAP_EVIDENCE", REASON_PR136_COVERAGE_MAP_MISSING),
    ("MISSING_PR136_QUANTUM_ATOMICROWS_EVIDENCE", REASON_PR136_QUANTUM_MAP_MISSING),
    ("PR136_SAME_NUMBER_INFERENCE_TRUE", REASON_PR136_SAME_NUMBER),
    ("PR136_AUTHORITY_FLAG_DRIFT", REASON_PR136_NO_AUTHORITY_DRIFT),
    ("MISSING_PR137R_EVIDENCE", REASON_PR137R_MISSING),
    ("MISSING_PR138_EVIDENCE", REASON_PR138_MISSING),
    ("MISSING_SOURCE_FILE", REASON_SOURCE_FILE_MISSING),
    ("DUPLICATE_FAMILY_ID", REASON_DUPLICATE_FAMILY_ID),
    ("DUPLICATE_SOURCE_FILE_PATH", REASON_DUPLICATE_SOURCE_PATH),
    ("MISSING_REQUIRED_FIELD_ID", REASON_REQUIRED_FIELD_MISSING),
    ("UNKNOWN_FIELD_ID", REASON_UNKNOWN_FIELD_ID),
    ("MISSING_REQUIRED_FIELD_GROUP_ID", REASON_REQUIRED_FIELD_GROUP_MISSING),
    ("UNKNOWN_FIELD_GROUP_ID", REASON_UNKNOWN_FIELD_GROUP_ID),
    ("SOURCE_MUTATION_FLAG_TRUE", FORBIDDEN_AUTHORITY_CLAIM_FIELDS["source_file_mutation_allowed_flag"]),
    ("BUNDLE_MUTATION_FLAG_TRUE", FORBIDDEN_AUTHORITY_CLAIM_FIELDS["bundle_mutation_allowed_flag"]),
    (
        "SEMANTIC_VALUE_MATERIALIZATION_FLAG_TRUE",
        FORBIDDEN_AUTHORITY_CLAIM_FIELDS["semantic_value_materialization_allowed_flag"],
    ),
    ("FINAL_READINESS_CLAIM", FORBIDDEN_AUTHORITY_CLAIM_FIELDS["final_readiness_created_flag"]),
    (
        "RUNTIME_LIVE_ORDER_AUTHORITY_CLAIM",
        FORBIDDEN_AUTHORITY_CLAIM_FIELDS["runtime_live_order_authority_created_flag"],
    ),
    ("SOURCE_ACCEPTANCE_CLAIM", FORBIDDEN_AUTHORITY_CLAIM_FIELDS["source_acceptance_created_flag"]),
    (
        "CONNECTOR_SEMANTIC_BINDING_CLAIM",
        FORBIDDEN_AUTHORITY_CLAIM_FIELDS["connector_semantic_binding_created_flag"],
    ),
    (
        "REPLAY_PAPER_EXECUTION_CLAIM",
        FORBIDDEN_AUTHORITY_CLAIM_FIELDS["replay_paper_execution_created_flag"],
    ),
    (
        "NEURAL_TRAINING_OR_INFERENCE_CLAIM",
        FORBIDDEN_AUTHORITY_CLAIM_FIELDS["neural_training_or_inference_created_flag"],
    ),
    (
        "QUANTUM_BACKEND_EXECUTION_CLAIM",
        FORBIDDEN_AUTHORITY_CLAIM_FIELDS["quantum_backend_execution_created_flag"],
    ),
    (
        "PROFIT_LATENCY_EXECUTION_SUPERIORITY_CLAIM",
        FORBIDDEN_AUTHORITY_CLAIM_FIELDS["profit_latency_execution_superiority_claim_created_flag"],
    ),
    (
        "CRYPTOGRAPHIC_FREEZE_SIDECAR_AUTHORITY_CLAIM",
        FORBIDDEN_AUTHORITY_CLAIM_FIELDS["cryptographic_sidecar_authority_created_flag"],
    ),
    ("FORBIDDEN_FIELD_NAME_FRAGMENT", REASON_CRYPTO_FIELD_NAME),
)


@dataclass(frozen=True)
class ValidationResult:
    failures: tuple[str, ...]
    report: dict[str, Any]


def _json_dump(value: Any) -> str:
    return json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True) + "\n"


def _read_json(path: pathlib.Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_json(path: pathlib.Path) -> dict[str, Any]:
    value = _read_json(path)
    if not isinstance(value, dict):
        raise ValueError(f"{path.as_posix()} must contain a JSON object")
    return value


def load_yaml(path: pathlib.Path) -> dict[str, Any]:
    return load_yaml_subset(path)


def _as_posix(path: pathlib.Path | str) -> str:
    return pathlib.Path(path).as_posix()


def _list_of_mappings(value: Any) -> list[Mapping[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, Mapping)]


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str)]


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _walk(value: Any, path: str = "$"):
    if isinstance(value, Mapping):
        for key, item in value.items():
            current = f"{path}.{key}"
            yield current, str(key), item
            yield from _walk(item, current)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            current = f"{path}[{index}]"
            yield current, f"[{index}]", item
            yield from _walk(item, current)


def _unique(values: Sequence[str]) -> bool:
    return len(values) == len(set(values))


def _load_json_evidence(repo_root: pathlib.Path) -> tuple[dict[str, dict[str, Any]], list[str]]:
    payloads: dict[str, dict[str, Any]] = {}
    failures: list[str] = []
    for field, rel_path in (*PR136_JSON_EVIDENCE_REFS, *ATOMICROWS_JSON_EVIDENCE_REFS):
        path = repo_root / rel_path
        reason = EVIDENCE_REASON_BY_FIELD.get(field, REASON_EVIDENCE_MISSING_OR_MALFORMED)
        if not path.exists():
            failures.append(f"{reason}: missing {rel_path.as_posix()}")
            continue
        try:
            payload = load_json(path)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            failures.append(f"{reason}: malformed {rel_path.as_posix()}: {exc}")
            continue
        payloads[field] = payload
    return payloads, failures


def _source_paths_from_pr137r(pr137r: Mapping[str, Any]) -> list[str]:
    inventory = _mapping(pr137r.get("atomicrows_artifact_inventory"))
    return _string_list(inventory.get("row_family_source_file_paths"))


def _field_ids_from_inventory(inventory: Mapping[str, Any]) -> list[str]:
    fields = _list_of_mappings(inventory.get("fields"))
    return [str(field.get("field_id")) for field in fields if isinstance(field.get("field_id"), str)]


def _group_ids_from_inventory(inventory: Mapping[str, Any]) -> list[str]:
    groups = _list_of_mappings(inventory.get("field_groups"))
    return [
        str(group.get("field_group_id"))
        for group in groups
        if isinstance(group.get("field_group_id"), str)
    ]


def _fields_by_group_from_inventory(inventory: Mapping[str, Any]) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    for group in _list_of_mappings(inventory.get("field_groups")):
        group_id = group.get("field_group_id")
        fields = group.get("fields")
        if isinstance(group_id, str) and isinstance(fields, list):
            result[group_id] = [field for field in fields if isinstance(field, str)]
    return result


def _supported_fields_from_pr137r(pr137r: Mapping[str, Any]) -> list[str]:
    state = _mapping(pr137r.get("atomicrows_validation_state"))
    audit = _mapping(state.get("row_contract_field_audit"))
    return _string_list(audit.get("supported_fields"))


def _missing_fields_from_pr137r(pr137r: Mapping[str, Any]) -> list[str]:
    state = _mapping(pr137r.get("atomicrows_validation_state"))
    audit = _mapping(state.get("row_contract_field_audit"))
    return _string_list(audit.get("missing_fields"))


def _row_count_from_pr137r(pr137r: Mapping[str, Any]) -> Any:
    state = _mapping(pr137r.get("atomicrows_validation_state"))
    return state.get("row_count_value")


def _canonical_venue_ids_from_evidence(payloads: Mapping[str, Mapping[str, Any]]) -> list[str]:
    policy_manifest = _mapping(payloads.get("pr136_policy_manifest_ref"))
    policy_venues = _string_list(policy_manifest.get("canonical_venues"))
    if policy_venues:
        return policy_venues
    market_index = _mapping(payloads.get("pr136_market_specific_launch_readiness_index_ref"))
    venues: list[str] = []
    for row in _list_of_mappings(market_index.get("market_scopes")):
        venue = row.get("canonical_venue_id")
        if isinstance(venue, str) and venue not in venues:
            venues.append(venue)
    return venues


def _load_source_file_record(repo_root: pathlib.Path, source_path: str) -> tuple[dict[str, Any] | None, str | None]:
    path = repo_root / source_path
    if not path.exists():
        return None, f"{REASON_SOURCE_FILE_MISSING}: {source_path}"
    try:
        first_line = next(
            line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()
        )
        payload = json.loads(first_line)
    except (OSError, StopIteration, json.JSONDecodeError) as exc:
        return None, f"{REASON_SOURCE_FILE_MISSING}: unreadable {source_path}: {exc}"
    if not isinstance(payload, dict):
        return None, f"{REASON_SOURCE_FILE_MISSING}: non-object source record {source_path}"
    return payload, None


def _semantic_group_fields(
    fields_by_group: Mapping[str, list[str]],
    *group_ids: str,
) -> list[str]:
    values: list[str] = []
    for group_id in group_ids:
        values.extend(fields_by_group.get(group_id, []))
    return values


def _field_requirements(field_ids: Sequence[str], *, false_fields: Sequence[str] = ()) -> dict[str, Any]:
    false_set = set(false_fields)
    return {
        field_id: False if field_id in false_set else REQUIREMENT_PLACEHOLDER
        for field_id in field_ids
    }


def _build_entry(
    *,
    repo_root: pathlib.Path,
    source_path: str,
    required_field_group_ids: Sequence[str],
    required_field_ids: Sequence[str],
    supported_field_ids: Sequence[str],
    missing_field_ids: Sequence[str],
    fields_by_group: Mapping[str, list[str]],
    canonical_venue_ids: Sequence[str],
) -> tuple[dict[str, Any] | None, list[str]]:
    source_record, failure = _load_source_file_record(repo_root, source_path)
    if failure is not None:
        return None, [failure]
    assert source_record is not None
    family_id = str(source_record.get("row_family_id") or "")
    canonical_order = source_record.get("canonical_order")
    if not isinstance(canonical_order, int):
        canonical_order = int(source_path.split("/")[-1].split("_", 1)[0])

    market_fields = _semantic_group_fields(
        fields_by_group,
        SEMANTIC_REQUIREMENT_FIELD_GROUPS["prediction_market_compatibility_requirements"],
    )
    quantum_fields = _semantic_group_fields(
        fields_by_group,
        SEMANTIC_REQUIREMENT_FIELD_GROUPS["quantum_metadata_currentization_requirements"],
    )
    objective_fields = _semantic_group_fields(
        fields_by_group,
        SEMANTIC_REQUIREMENT_FIELD_GROUPS["profit_risk_latency_objective_metadata_requirements"],
    )
    agent_fields = _semantic_group_fields(
        fields_by_group,
        SEMANTIC_REQUIREMENT_FIELD_GROUPS["agent_selection_replay_paper_requirements"],
        REPLAY_PAPER_GROUP_ID,
    )
    source_fields = _semantic_group_fields(
        fields_by_group,
        SEMANTIC_REQUIREMENT_FIELD_GROUPS["source_provenance_requirements"],
    )

    return {
        "family_id": family_id,
        "canonical_family_order": canonical_order,
        "source_file_path": source_path,
        "source_file_exists_flag": True,
        "currentization_status": CURRENTIZATION_STATUS,
        "semantic_contract_ref": DEFAULT_REPORT_PR138().as_posix(),
        "required_field_group_ids": list(required_field_group_ids),
        "required_field_ids": list(required_field_ids),
        "missing_field_ids_requiring_future_enrichment": list(missing_field_ids),
        "supported_field_ids_currently_present_if_known": list(supported_field_ids),
        "semantic_value_materialization_allowed_flag": False,
        "source_file_mutation_allowed_flag": False,
        "bundle_mutation_allowed_flag": False,
        "prediction_market_compatibility_requirements": {
            "canonical_stage1_venue_ids": list(canonical_venue_ids),
            "forbidden_venue_aliases": list(FORBIDDEN_VENUE_ALIASES),
            "required_field_ids": market_fields,
            **{
                venue_id: VENUE_COMPATIBILITY_PLACEHOLDER
                for venue_id in CANONICAL_STAGE1_VENUE_IDS
            },
        },
        "quantum_metadata_currentization_requirements": {
            "metadata_only_flag": True,
            "execution_allowed_by_pr139_flag": False,
            "required_field_ids": quantum_fields,
            **_field_requirements(
                quantum_fields,
                false_fields=("quantum_backend_execution_allowed_flag",),
            ),
        },
        "profit_risk_latency_objective_metadata_requirements": {
            "metadata_only_flag": True,
            "profit_latency_execution_superiority_claim_created_flag": False,
            "required_field_ids": objective_fields,
            **_field_requirements(objective_fields),
        },
        "agent_selection_replay_paper_requirements": {
            "metadata_only_flag": True,
            "execution_allowed_by_pr139_flag": False,
            "required_field_ids": agent_fields,
            **_field_requirements(
                agent_fields,
                false_fields=(
                    "live_use_allowed_flag",
                    "order_authority_created_flag",
                    "profit_evidence_created_flag",
                ),
            ),
        },
        "source_provenance_requirements": {
            "metadata_only_flag": True,
            "source_acceptance_created_flag": False,
            "required_field_ids": source_fields,
            **{
                "source_evidence_required_flag": True,
                "accepted_source_packet_required_flag": True,
                "research_input_only_flag": True,
                "external_fact_authority_flag": False,
            },
        },
    }, []


def DEFAULT_REPORT_PR138() -> pathlib.Path:
    return dict(ATOMICROWS_JSON_EVIDENCE_REFS)["pr138_semantic_contract_report_ref"]


def build_manifest(repo_root: pathlib.Path | str = _REPO_ROOT) -> dict[str, Any]:
    root = pathlib.Path(repo_root)
    payloads, failures = _load_json_evidence(root)
    if failures:
        raise ValueError("; ".join(failures))
    pr137r = payloads["pr137r_report_ref"]
    pr138_report = payloads["pr138_semantic_contract_report_ref"]
    inventory = payloads["pr138_field_inventory_ref"]

    required_field_ids = _field_ids_from_inventory(inventory)
    required_field_group_ids = _group_ids_from_inventory(inventory)
    fields_by_group = _fields_by_group_from_inventory(inventory)
    supported_field_ids = _supported_fields_from_pr137r(pr137r)
    missing_field_ids = [
        field_id for field_id in required_field_ids if field_id not in set(supported_field_ids)
    ]
    source_paths = _source_paths_from_pr137r(pr137r)
    canonical_venue_ids = _canonical_venue_ids_from_evidence(payloads)

    entry_failures: list[str] = []
    entries: list[dict[str, Any]] = []
    for source_path in source_paths:
        entry, failures_for_entry = _build_entry(
            repo_root=root,
            source_path=source_path,
            required_field_group_ids=required_field_group_ids,
            required_field_ids=required_field_ids,
            supported_field_ids=supported_field_ids,
            missing_field_ids=missing_field_ids,
            fields_by_group=fields_by_group,
            canonical_venue_ids=canonical_venue_ids,
        )
        entry_failures.extend(failures_for_entry)
        if entry is not None:
            entries.append(entry)
    if entry_failures:
        raise ValueError("; ".join(entry_failures))

    evidence_refs = {field: path.as_posix() for field, path in EVIDENCE_REF_FIELDS}
    semantic_contract = _mapping(pr138_report.get("semantic_contract"))
    return {
        "manifest_id": MANIFEST_ID,
        "manifest_version": MANIFEST_VERSION,
        "repo_current_sequence_label": REPO_CURRENT_SEQUENCE_LABEL,
        "roadmap_identity_inference_used": False,
        "authority_class": AUTHORITY_CLASS,
        "validator_marker": SUCCESS_MARKER,
        "static_only_flag": True,
        "read_only_evidence_only_flag": True,
        "deterministic_output_flag": True,
        "source_file_mutation_allowed_flag": False,
        "bundle_mutation_allowed_flag": False,
        "semantic_value_materialization_allowed_flag": False,
        "final_readiness_created_flag": False,
        "runtime_live_order_authority_created_flag": False,
        "source_acceptance_created_flag": False,
        "connector_semantic_binding_created_flag": False,
        "replay_paper_execution_created_flag": False,
        "neural_training_or_inference_created_flag": False,
        "quantum_backend_execution_created_flag": False,
        "profit_latency_execution_superiority_claim_created_flag": False,
        "cryptographic_sidecar_authority_created_flag": False,
        "freeze_authority_created_flag": False,
        "evidence_references": evidence_refs,
        "pr136_alignment": {
            "pr136_control_plane_consumed_read_only": True,
            "pr136_same_number_inference_preserved_false": True,
            "pr136_no_authority_flags_preserved": True,
            "pr136_canonical_venue_ids_consumed": True,
            "pr136_master_plan_coverage_to_readiness_domain_map_consumed": True,
            "pr136_agent_launch_orchestration_map_consumed": True,
            "pr136_launch_readiness_dependency_graph_consumed": True,
            "pr136_quantum_atomicrows_optimization_readiness_map_consumed": True,
            "pr136_future_sequence_context_consumed": True,
            "pr136_did_not_override_repo_current_atomicrows_scope": True,
        },
        "row_family_source_manifest": {
            "manifest_entry_count": len(entries),
            "row_family_source_file_count": len(source_paths),
            "existing_bundle_row_count": _row_count_from_pr137r(pr137r),
            "required_field_count": semantic_contract.get("required_field_count"),
            "required_field_group_count": semantic_contract.get("required_field_group_count"),
            "missing_field_count": len(missing_field_ids),
            "stable_ordering_policy": "CANONICAL_FAMILY_ORDER_ASCENDING_FROM_PR137R",
            "row_family_entries": entries,
        },
    }


def _schema_string_array() -> dict[str, Any]:
    return {"type": "array", "items": {"type": "string"}, "minItems": 1}


def _requirement_section_schema(
    field_names: Sequence[str],
    *,
    extra_properties: Mapping[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    properties: dict[str, Any] = {
        "metadata_only_flag": {"type": "boolean"},
        "required_field_ids": {"$ref": "#/$defs/string_array"},
    }
    properties.update(extra_properties or {})
    for field_name in field_names:
        properties[field_name] = {"type": ["string", "boolean"]}
    return {
        "type": "object",
        "additionalProperties": False,
        "required": sorted(properties),
        "properties": properties,
    }


def build_json_schema() -> dict[str, Any]:
    top_properties: dict[str, Any] = {
        "manifest_id": {"const": MANIFEST_ID},
        "manifest_version": {"const": MANIFEST_VERSION},
        "repo_current_sequence_label": {"const": REPO_CURRENT_SEQUENCE_LABEL},
        "roadmap_identity_inference_used": {"const": False},
        "authority_class": {"const": AUTHORITY_CLASS},
        "validator_marker": {"const": SUCCESS_MARKER},
        "evidence_references": {
            "type": "object",
            "additionalProperties": False,
            "required": list(EVIDENCE_REF_FIELD_NAMES),
            "properties": {
                field: {"type": "string"} for field in EVIDENCE_REF_FIELD_NAMES
            },
        },
        "pr136_alignment": {
            "type": "object",
            "additionalProperties": False,
            "required": list(PR136_ALIGNMENT_TRUE_FLAGS),
            "properties": {
                field: {"const": True} for field in PR136_ALIGNMENT_TRUE_FLAGS
            },
        },
        "row_family_source_manifest": {"$ref": "#/$defs/row_family_source_manifest"},
    }
    for field in REQUIRED_TRUE_FLAGS:
        top_properties[field] = {"const": True}
    for field in REQUIRED_FALSE_FLAGS:
        top_properties[field] = {"const": False}

    entry_properties: dict[str, Any] = {
        "family_id": {"type": "string"},
        "canonical_family_order": {"type": "integer"},
        "source_file_path": {"type": "string"},
        "source_file_exists_flag": {"const": True},
        "currentization_status": {"const": CURRENTIZATION_STATUS},
        "semantic_contract_ref": {"type": "string"},
        "required_field_group_ids": {"$ref": "#/$defs/string_array"},
        "required_field_ids": {"$ref": "#/$defs/string_array"},
        "missing_field_ids_requiring_future_enrichment": {"$ref": "#/$defs/string_array"},
        "supported_field_ids_currently_present_if_known": {"$ref": "#/$defs/string_array"},
        "semantic_value_materialization_allowed_flag": {"const": False},
        "source_file_mutation_allowed_flag": {"const": False},
        "bundle_mutation_allowed_flag": {"const": False},
        "prediction_market_compatibility_requirements": {
            "type": "object",
            "additionalProperties": False,
            "required": [
                "canonical_stage1_venue_ids",
                "forbidden_venue_aliases",
                "required_field_ids",
                *CANONICAL_STAGE1_VENUE_IDS,
            ],
            "properties": {
                "canonical_stage1_venue_ids": {"$ref": "#/$defs/string_array"},
                "forbidden_venue_aliases": {"$ref": "#/$defs/string_array"},
                "required_field_ids": {"$ref": "#/$defs/string_array"},
                **{
                    venue_id: {"type": "string"}
                    for venue_id in CANONICAL_STAGE1_VENUE_IDS
                },
            },
        },
        "quantum_metadata_currentization_requirements": {"$ref": "#/$defs/quantum_requirements"},
        "profit_risk_latency_objective_metadata_requirements": {
            "$ref": "#/$defs/objective_requirements"
        },
        "agent_selection_replay_paper_requirements": {"$ref": "#/$defs/agent_requirements"},
        "source_provenance_requirements": {"$ref": "#/$defs/source_requirements"},
    }
    return {
        "$schema": "json-schema-draft-2020-12",
        "$id": "qtt-local-schemas-atomicrows-row-family-source-manifest-currentization",
        "title": "AtomicRows Row-Family Source Manifest Currentization",
        "description": (
            "Static deterministic PR139 AtomicRows row-family source manifest "
            "currentization. This schema validates shape only; policy validation "
            "is enforced by the PR139 validator."
        ),
        "type": "object",
        "additionalProperties": False,
        "required": [
            "manifest_id",
            "manifest_version",
            "repo_current_sequence_label",
            "roadmap_identity_inference_used",
            "authority_class",
            "validator_marker",
            *REQUIRED_TRUE_FLAGS,
            *[
                field for field in REQUIRED_FALSE_FLAGS if field != "roadmap_identity_inference_used"
            ],
            "evidence_references",
            "pr136_alignment",
            "row_family_source_manifest",
        ],
        "properties": top_properties,
        "$defs": {
            "string_array": _schema_string_array(),
            "row_family_source_manifest": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "manifest_entry_count",
                    "row_family_source_file_count",
                    "existing_bundle_row_count",
                    "required_field_count",
                    "required_field_group_count",
                    "missing_field_count",
                    "stable_ordering_policy",
                    "row_family_entries",
                ],
                "properties": {
                    "manifest_entry_count": {"type": "integer"},
                    "row_family_source_file_count": {"type": "integer"},
                    "existing_bundle_row_count": {"type": "integer"},
                    "required_field_count": {"type": "integer"},
                    "required_field_group_count": {"type": "integer"},
                    "missing_field_count": {"type": "integer"},
                    "stable_ordering_policy": {"type": "string"},
                    "row_family_entries": {
                        "type": "array",
                        "items": {"$ref": "#/$defs/row_family_entry"},
                        "minItems": EXPECTED_ROW_FAMILY_SOURCE_FILE_COUNT,
                    },
                },
            },
            "row_family_entry": {
                "type": "object",
                "additionalProperties": False,
                "required": list(entry_properties),
                "properties": entry_properties,
            },
            "quantum_requirements": _requirement_section_schema(
                (
                    "quantum_applicability_class",
                    "classical_only_flag",
                    "quantum_inspired_flag",
                    "true_quantum_compatible_flag",
                    "qubo_compatible_flag",
                    "ising_compatible_flag",
                    "qaoa_compatible_flag",
                    "vqe_compatible_flag",
                    "annealing_compatible_flag",
                    "quantum_kernel_feature_map_compatible_flag",
                    "quantum_backend_execution_allowed_flag",
                ),
                extra_properties={"execution_allowed_by_pr139_flag": {"type": "boolean"}},
            ),
            "objective_requirements": _requirement_section_schema(
                (
                    "expected_net_profit_objective_family",
                    "execution_cost_model_family",
                    "latency_sensitivity_class",
                    "capital_intensity_class",
                    "risk_mode",
                    "drawdown_control_family",
                    "exposure_limit_family",
                    "liquidity_context_family",
                ),
                extra_properties={
                    "profit_latency_execution_superiority_claim_created_flag": {
                        "type": "boolean"
                    }
                },
            ),
            "agent_requirements": _requirement_section_schema(
                (
                    "agent_role",
                    "consumer_class",
                    "allowed_consumers",
                    "blocked_consumers",
                    "command_matrix_binding",
                    "replay_required_flag",
                    "paper_required_flag",
                    "owner_review_required_flag",
                    "live_use_allowed_flag",
                    "order_authority_created_flag",
                    "profit_evidence_created_flag",
                ),
                extra_properties={"execution_allowed_by_pr139_flag": {"type": "boolean"}},
            ),
            "source_requirements": _requirement_section_schema(
                (
                    "source_evidence_required_flag",
                    "accepted_source_packet_required_flag",
                    "research_input_only_flag",
                    "external_fact_authority_flag",
                ),
                extra_properties={"source_acceptance_created_flag": {"type": "boolean"}},
            ),
        },
    }


def _yaml_scalar(value: Any) -> str:
    if value is True:
        return "true"
    if value is False:
        return "false"
    if value is None:
        return "null"
    if isinstance(value, int):
        return str(value)
    text = str(value)
    if text == "":
        return '""'
    return text


def _dump_yaml_lines(value: Any, indent: int = 0) -> list[str]:
    prefix = " " * indent
    if isinstance(value, Mapping):
        lines: list[str] = []
        for key, item in value.items():
            if isinstance(item, (Mapping, list)) and item not in ({}, []):
                lines.append(f"{prefix}{key}:")
                lines.extend(_dump_yaml_lines(item, indent + 2))
            else:
                lines.append(f"{prefix}{key}: {_yaml_scalar(item)}")
        return lines
    if isinstance(value, list):
        if not value:
            return [f"{prefix}[]"]
        lines = []
        for item in value:
            if isinstance(item, Mapping):
                items = list(item.items())
                first_key, first_value = items[0]
                if isinstance(first_value, (Mapping, list)) and first_value not in ({}, []):
                    lines.append(f"{prefix}- {first_key}:")
                    lines.extend(_dump_yaml_lines(first_value, indent + 4))
                else:
                    lines.append(f"{prefix}- {first_key}: {_yaml_scalar(first_value)}")
                for key, child in items[1:]:
                    if isinstance(child, (Mapping, list)) and child not in ({}, []):
                        lines.append(f"{prefix}  {key}:")
                        lines.extend(_dump_yaml_lines(child, indent + 4))
                    else:
                        lines.append(f"{prefix}  {key}: {_yaml_scalar(child)}")
            else:
                lines.append(f"{prefix}- {_yaml_scalar(item)}")
        return lines
    return [f"{prefix}{_yaml_scalar(value)}"]


def yaml_dump(value: Mapping[str, Any]) -> str:
    return "\n".join(_dump_yaml_lines(value)) + "\n"


def _write_text(path: pathlib.Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def write_schema_file(repo_root: pathlib.Path | str = _REPO_ROOT) -> dict[str, Any]:
    schema = build_json_schema()
    _write_text(pathlib.Path(repo_root) / DEFAULT_SCHEMA, _json_dump(schema))
    return schema


def write_manifest_file(repo_root: pathlib.Path | str = _REPO_ROOT) -> dict[str, Any]:
    manifest = build_manifest(repo_root)
    _write_text(pathlib.Path(repo_root) / DEFAULT_MANIFEST, yaml_dump(manifest))
    return manifest


def build_fixture(manifest: Mapping[str, Any] | None = None) -> dict[str, Any]:
    return {
        "fixture_id": "SYNTHETIC_ATOMICROWS_ROW_FAMILY_SOURCE_MANIFEST_CURRENTIZATION_V1",
        "fixture_version": "v1",
        "validator_marker": SUCCESS_MARKER,
        "authority_class": AUTHORITY_CLASS,
        "static_only_flag": True,
        "manifest_id": MANIFEST_ID,
        "repo_current_sequence_label": REPO_CURRENT_SEQUENCE_LABEL,
        "positive_expected_entry_count": EXPECTED_ROW_FAMILY_SOURCE_FILE_COUNT,
        "canonical_stage1_venue_ids": list(CANONICAL_STAGE1_VENUE_IDS),
        "forbidden_venue_aliases": list(FORBIDDEN_VENUE_ALIASES),
        "forbidden_field_name_fragments": list(FORBIDDEN_FIELD_NAME_FRAGMENTS),
        "negative_case_expectations": [
            {"case_id": case_id, "expected_reason": reason}
            for case_id, reason in NEGATIVE_FIXTURE_EXPECTATIONS
        ],
        "manifest_entry_count": (
            _mapping(manifest.get("row_family_source_manifest")).get("manifest_entry_count")
            if isinstance(manifest, Mapping)
            else EXPECTED_ROW_FAMILY_SOURCE_FILE_COUNT
        ),
    }


def write_fixture_file(repo_root: pathlib.Path | str = _REPO_ROOT) -> dict[str, Any]:
    root = pathlib.Path(repo_root)
    manifest = load_yaml(root / DEFAULT_MANIFEST) if (root / DEFAULT_MANIFEST).exists() else None
    fixture = build_fixture(manifest)
    _write_text(root / DEFAULT_FIXTURE, _json_dump(fixture))
    return fixture


def _expected_evidence_refs() -> dict[str, str]:
    return {field: path.as_posix() for field, path in EVIDENCE_REF_FIELDS}


def _protected_bytes(repo_root: pathlib.Path) -> dict[str, bytes | None]:
    paths = [
        MASTER_PLAN_PATH,
        ATOMICROWS_BUNDLE_PATH,
        *[
            path.relative_to(repo_root)
            for path in sorted((repo_root / ROW_FAMILY_SOURCE_DIRECTORY).glob("*.source.jsonl"))
        ],
    ]
    result: dict[str, bytes | None] = {}
    for rel_path in paths:
        path = repo_root / rel_path
        result[rel_path.as_posix()] = path.read_bytes() if path.exists() else None
    return result


def _validate_fixture_payload(fixture: Mapping[str, Any]) -> list[str]:
    failures: list[str] = []
    if fixture.get("validator_marker") != SUCCESS_MARKER:
        failures.append(REASON_FIXTURE_INVALID)
    if fixture.get("authority_class") != AUTHORITY_CLASS:
        failures.append(REASON_FIXTURE_INVALID)
    case_ids = [
        item.get("case_id")
        for item in _list_of_mappings(fixture.get("negative_case_expectations"))
    ]
    expected_case_ids = [case_id for case_id, _reason in NEGATIVE_FIXTURE_EXPECTATIONS]
    if case_ids != expected_case_ids:
        failures.append(REASON_FIXTURE_INVALID)
    return failures


def _validate_evidence_payloads(payloads: Mapping[str, Mapping[str, Any]]) -> list[str]:
    failures: list[str] = []

    route = _mapping(payloads.get("pr136_route_triage_ref"))
    if route.get("same_number_inference_used") is not False:
        failures.append(REASON_PR136_SAME_NUMBER)
    for field in (
        "future_pr_sequence_auto_authorizes_implementation",
        "future_pr_sequence_auto_authorizes_live_trading",
        "future_pr_sequence_auto_authorizes_atomicrows_materialization",
        "future_pr_sequence_auto_authorizes_quantum_execution",
    ):
        if route.get(field) is not False:
            failures.append(REASON_PR136_NO_AUTHORITY_DRIFT)

    day1 = _mapping(payloads.get("pr136_day1_launch_readiness_roadmap_ref"))
    policy = _mapping(payloads.get("pr136_policy_manifest_ref"))
    for evidence in (day1, policy):
        no_authority = _mapping(evidence.get("no_authority_flags"))
        if no_authority and any(value is not False for value in no_authority.values()):
            failures.append(REASON_PR136_NO_AUTHORITY_DRIFT)

    quantum = _mapping(payloads.get("pr136_quantum_atomicrows_optimization_readiness_map_ref"))
    for field in (
        "atomicrows_bundle_created_flag",
        "atomicrows_bundle_edited_flag",
        "atomicrows_materialization_authority_created_flag",
        "atomicrows_rows_created_flag",
    ):
        if quantum.get(field) is not False:
            failures.append(REASON_PR136_NO_AUTHORITY_DRIFT)
    for field in (
        "no_quantum_advantage_claim_flag",
        "no_quantum_execution_flag",
        "no_quantum_optimizer_input_flag",
        "no_quantum_signal_creation_flag",
    ):
        if quantum.get(field) is not True:
            failures.append(REASON_PR136_NO_AUTHORITY_DRIFT)

    canonical_venues = _canonical_venue_ids_from_evidence(payloads)
    if canonical_venues != list(CANONICAL_STAGE1_VENUE_IDS):
        failures.append(REASON_CANONICAL_VENUE)
    market = _mapping(payloads.get("pr136_market_specific_launch_readiness_index_ref"))
    if _string_list(market.get("forbidden_forecastex_aliases")) != list(FORBIDDEN_VENUE_ALIASES):
        failures.append(REASON_FORBIDDEN_VENUE_ALIAS)

    pr137r = _mapping(payloads.get("pr137r_report_ref"))
    inventory = _mapping(pr137r.get("atomicrows_artifact_inventory"))
    state = _mapping(pr137r.get("atomicrows_validation_state"))
    if inventory.get("row_family_source_file_count") != EXPECTED_ROW_FAMILY_SOURCE_FILE_COUNT:
        failures.append(REASON_ROW_FAMILY_COUNT)
    if len(_source_paths_from_pr137r(pr137r)) != EXPECTED_ROW_FAMILY_SOURCE_FILE_COUNT:
        failures.append(REASON_ROW_FAMILY_COUNT)
    if state.get("row_count_value") != EXPECTED_BUNDLE_ROW_COUNT:
        failures.append(REASON_ROW_COUNT)

    pr138 = _mapping(payloads.get("pr138_semantic_contract_report_ref"))
    field_inventory = _mapping(payloads.get("pr138_field_inventory_ref"))
    if pr138.get("required_field_count") != EXPECTED_REQUIRED_FIELD_COUNT:
        failures.append(REASON_REQUIRED_FIELD_COUNT)
    if field_inventory.get("required_field_count") != EXPECTED_REQUIRED_FIELD_COUNT:
        failures.append(REASON_REQUIRED_FIELD_COUNT)
    if pr138.get("required_field_group_count") != EXPECTED_REQUIRED_FIELD_GROUP_COUNT:
        failures.append(REASON_REQUIRED_FIELD_GROUP_COUNT)
    if field_inventory.get("required_field_group_count") != EXPECTED_REQUIRED_FIELD_GROUP_COUNT:
        failures.append(REASON_REQUIRED_FIELD_GROUP_COUNT)
    contract = _mapping(pr138.get("semantic_contract"))
    if _string_list(contract.get("field_ids")) != _field_ids_from_inventory(field_inventory):
        failures.append(REASON_REQUIRED_FIELD_MISSING)
    if _string_list(contract.get("field_group_ids")) != _group_ids_from_inventory(field_inventory):
        failures.append(REASON_REQUIRED_FIELD_GROUP_MISSING)
    return failures


def _validate_no_forbidden_field_names(payload: Mapping[str, Any]) -> list[str]:
    failures: list[str] = []
    for path, key, _item in _walk(payload):
        if key.startswith("["):
            continue
        lowered = key.lower()
        if any(fragment in lowered for fragment in FORBIDDEN_FIELD_NAME_FRAGMENTS):
            failures.append(f"{REASON_CRYPTO_FIELD_NAME}: {path}")
    return failures


def _validate_no_forbidden_alias_use(payload: Mapping[str, Any]) -> list[str]:
    failures: list[str] = []
    for path, _key, item in _walk(payload):
        if not isinstance(item, str) or item not in FORBIDDEN_VENUE_ALIASES:
            continue
        if ".forbidden_venue_aliases" not in path:
            failures.append(f"{REASON_FORBIDDEN_VENUE_ALIAS}: {path}")
    return failures


def _false_flag_reason(field_name: str) -> str:
    return FORBIDDEN_AUTHORITY_CLAIM_FIELDS.get(field_name, REASON_FALSE_FLAG)


def _validate_flags(payload: Mapping[str, Any]) -> list[str]:
    failures: list[str] = []
    for field in REQUIRED_TRUE_FLAGS:
        if payload.get(field) is not True:
            failures.append(f"{REASON_TRUE_FLAG}: {field}")
    for field in REQUIRED_FALSE_FLAGS:
        if payload.get(field) is not False:
            failures.append(f"{_false_flag_reason(field)}: {field}")

    alignment = _mapping(payload.get("pr136_alignment"))
    for field in PR136_ALIGNMENT_TRUE_FLAGS:
        if alignment.get(field) is not True:
            reason = (
                REASON_PR136_SAME_NUMBER
                if field == "pr136_same_number_inference_preserved_false"
                else REASON_PR136_NO_AUTHORITY_DRIFT
            )
            failures.append(f"{reason}: {field}")

    for path, key, item in _walk(payload):
        if key not in FORBIDDEN_AUTHORITY_CLAIM_FIELDS or item is not True:
            continue
        failures.append(f"{_false_flag_reason(key)}: {path}")
    return failures


def validate_manifest_payload(
    manifest: Mapping[str, Any],
    schema: Mapping[str, Any],
    payloads: Mapping[str, Mapping[str, Any]],
    repo_root: pathlib.Path | str,
) -> list[str]:
    root = pathlib.Path(repo_root)
    failures: list[str] = []
    schema_failures = validate_json_schema_subset(manifest, dict(schema))
    if schema_failures:
        failures.extend(f"{REASON_SCHEMA_FAILED}: {failure}" for failure in schema_failures)

    if manifest.get("manifest_id") != MANIFEST_ID:
        failures.append(REASON_IDENTITY_OR_AUTHORITY)
    if manifest.get("manifest_version") != MANIFEST_VERSION:
        failures.append(REASON_IDENTITY_OR_AUTHORITY)
    if manifest.get("repo_current_sequence_label") != REPO_CURRENT_SEQUENCE_LABEL:
        failures.append(REASON_IDENTITY_OR_AUTHORITY)
    if manifest.get("authority_class") != AUTHORITY_CLASS:
        failures.append(REASON_IDENTITY_OR_AUTHORITY)
    if manifest.get("validator_marker") != SUCCESS_MARKER:
        failures.append(REASON_VALIDATOR_MARKER)
    failures.extend(_validate_flags(manifest))
    failures.extend(_validate_no_forbidden_field_names(manifest))
    failures.extend(_validate_no_forbidden_alias_use(manifest))

    evidence_refs = _mapping(manifest.get("evidence_references"))
    expected_refs = _expected_evidence_refs()
    for field, expected_path in expected_refs.items():
        if evidence_refs.get(field) != expected_path:
            failures.append(f"{REASON_EVIDENCE_MISSING_OR_MALFORMED}: {field}")

    pr137r = _mapping(payloads.get("pr137r_report_ref"))
    field_inventory = _mapping(payloads.get("pr138_field_inventory_ref"))
    required_field_ids = _field_ids_from_inventory(field_inventory)
    required_group_ids = _group_ids_from_inventory(field_inventory)
    fields_by_group = _fields_by_group_from_inventory(field_inventory)
    supported_fields = _supported_fields_from_pr137r(pr137r)
    expected_missing_fields = [
        field_id for field_id in required_field_ids if field_id not in set(supported_fields)
    ]
    traceable_missing_fields = set(_missing_fields_from_pr137r(pr137r)) | set(
        expected_missing_fields
    )
    source_paths = _source_paths_from_pr137r(pr137r)

    source_manifest = _mapping(manifest.get("row_family_source_manifest"))
    entries = _list_of_mappings(source_manifest.get("row_family_entries"))
    if source_manifest.get("manifest_entry_count") != EXPECTED_ROW_FAMILY_SOURCE_FILE_COUNT:
        failures.append(REASON_MANIFEST_ENTRY_COUNT)
    if len(entries) != EXPECTED_ROW_FAMILY_SOURCE_FILE_COUNT:
        failures.append(REASON_MANIFEST_ENTRY_COUNT)
    if source_manifest.get("row_family_source_file_count") != EXPECTED_ROW_FAMILY_SOURCE_FILE_COUNT:
        failures.append(REASON_ROW_FAMILY_COUNT)
    if source_manifest.get("existing_bundle_row_count") != EXPECTED_BUNDLE_ROW_COUNT:
        failures.append(REASON_ROW_COUNT)
    if source_manifest.get("required_field_count") != EXPECTED_REQUIRED_FIELD_COUNT:
        failures.append(REASON_REQUIRED_FIELD_COUNT)
    if source_manifest.get("required_field_group_count") != EXPECTED_REQUIRED_FIELD_GROUP_COUNT:
        failures.append(REASON_REQUIRED_FIELD_GROUP_COUNT)
    if source_manifest.get("missing_field_count") != len(expected_missing_fields):
        failures.append(REASON_MISSING_FIELD_NOT_TRACEABLE)

    family_ids = [str(entry.get("family_id")) for entry in entries]
    source_entry_paths = [str(entry.get("source_file_path")) for entry in entries]
    if not _unique(family_ids):
        failures.append(REASON_DUPLICATE_FAMILY_ID)
    if not _unique(source_entry_paths):
        failures.append(REASON_DUPLICATE_SOURCE_PATH)
    if source_entry_paths != source_paths:
        failures.append(REASON_SOURCE_FILE_MISSING)

    canonical_venues = _canonical_venue_ids_from_evidence(payloads)
    for index, entry in enumerate(entries, start=1):
        source_path = str(entry.get("source_file_path") or "")
        source_record, source_failure = _load_source_file_record(root, source_path)
        if source_failure is not None:
            failures.append(source_failure)
        elif source_record is not None and source_record.get("row_family_id") != entry.get("family_id"):
            failures.append(REASON_DUPLICATE_FAMILY_ID)
        if entry.get("canonical_family_order") != index:
            failures.append(REASON_MANIFEST_ENTRY_COUNT)
        if entry.get("source_file_exists_flag") is not True:
            failures.append(f"{REASON_SOURCE_FILE_MISSING}: {source_path}")
        if entry.get("currentization_status") != CURRENTIZATION_STATUS:
            failures.append(REASON_IDENTITY_OR_AUTHORITY)
        if entry.get("semantic_contract_ref") != DEFAULT_REPORT_PR138().as_posix():
            failures.append(REASON_PR138_MISSING)
        for field in ENTRY_FALSE_FLAGS:
            if entry.get(field) is not False:
                failures.append(f"{_false_flag_reason(field)}: {source_path}.{field}")

        entry_groups = _string_list(entry.get("required_field_group_ids"))
        entry_fields = _string_list(entry.get("required_field_ids"))
        if entry_groups != required_group_ids:
            missing_groups = set(required_group_ids) - set(entry_groups)
            unknown_groups = set(entry_groups) - set(required_group_ids)
            if missing_groups:
                failures.append(REASON_REQUIRED_FIELD_GROUP_MISSING)
            if unknown_groups:
                failures.append(REASON_UNKNOWN_FIELD_GROUP_ID)
            if not missing_groups and not unknown_groups:
                failures.append(REASON_REQUIRED_FIELD_GROUP_MISSING)
        if entry_fields != required_field_ids:
            missing_fields = set(required_field_ids) - set(entry_fields)
            unknown_fields = set(entry_fields) - set(required_field_ids)
            if missing_fields:
                failures.append(REASON_REQUIRED_FIELD_MISSING)
            if unknown_fields:
                failures.append(REASON_UNKNOWN_FIELD_ID)
            if not missing_fields and not unknown_fields:
                failures.append(REASON_REQUIRED_FIELD_MISSING)
        entry_missing = _string_list(entry.get("missing_field_ids_requiring_future_enrichment"))
        if entry_missing != expected_missing_fields:
            if set(entry_missing) - traceable_missing_fields:
                failures.append(REASON_MISSING_FIELD_NOT_TRACEABLE)
            else:
                failures.append(REASON_REQUIRED_FIELD_MISSING)
        if _string_list(entry.get("supported_field_ids_currently_present_if_known")) != supported_fields:
            failures.append(REASON_UNKNOWN_FIELD_ID)

        prediction = _mapping(entry.get("prediction_market_compatibility_requirements"))
        if _string_list(prediction.get("canonical_stage1_venue_ids")) != canonical_venues:
            failures.append(REASON_CANONICAL_VENUE)
        if _string_list(prediction.get("forbidden_venue_aliases")) != list(FORBIDDEN_VENUE_ALIASES):
            failures.append(REASON_FORBIDDEN_VENUE_ALIAS)
        if _string_list(prediction.get("required_field_ids")) != fields_by_group.get(
            SEMANTIC_REQUIREMENT_FIELD_GROUPS["prediction_market_compatibility_requirements"],
            [],
        ):
            failures.append(REASON_REQUIRED_FIELD_MISSING)

        quantum = _mapping(entry.get("quantum_metadata_currentization_requirements"))
        if quantum.get("metadata_only_flag") is not True:
            failures.append(REASON_TRUE_FLAG)
        if quantum.get("execution_allowed_by_pr139_flag") is not False:
            failures.append(FORBIDDEN_AUTHORITY_CLAIM_FIELDS["quantum_backend_execution_allowed_flag"])
        if quantum.get("quantum_backend_execution_allowed_flag") is not False:
            failures.append(FORBIDDEN_AUTHORITY_CLAIM_FIELDS["quantum_backend_execution_allowed_flag"])

        objective = _mapping(entry.get("profit_risk_latency_objective_metadata_requirements"))
        if objective.get("profit_latency_execution_superiority_claim_created_flag") is not False:
            failures.append(
                FORBIDDEN_AUTHORITY_CLAIM_FIELDS[
                    "profit_latency_execution_superiority_claim_created_flag"
                ]
            )

        agent = _mapping(entry.get("agent_selection_replay_paper_requirements"))
        for field in ("live_use_allowed_flag", "order_authority_created_flag", "profit_evidence_created_flag"):
            if agent.get(field) is not False:
                failures.append(FORBIDDEN_AUTHORITY_CLAIM_FIELDS[field])

        source = _mapping(entry.get("source_provenance_requirements"))
        if source.get("source_acceptance_created_flag") is not False:
            failures.append(FORBIDDEN_AUTHORITY_CLAIM_FIELDS["source_acceptance_created_flag"])
        if source.get("external_fact_authority_flag") is not False:
            failures.append(FORBIDDEN_AUTHORITY_CLAIM_FIELDS["external_fact_authority_flag"])
        for field in (
            "source_evidence_required_flag",
            "accepted_source_packet_required_flag",
            "research_input_only_flag",
        ):
            if source.get(field) is not True:
                failures.append(REASON_TRUE_FLAG)
    return sorted(set(failures))


def build_report(
    *,
    manifest: Mapping[str, Any],
    payloads: Mapping[str, Mapping[str, Any]],
    failures: Sequence[str],
    no_mutation_confirmations: Mapping[str, bool] | None = None,
) -> dict[str, Any]:
    source_manifest = _mapping(manifest.get("row_family_source_manifest"))
    pr137r = _mapping(payloads.get("pr137r_report_ref"))
    inventory = _mapping(payloads.get("pr138_field_inventory_ref"))
    required_field_ids = _field_ids_from_inventory(inventory)
    supported_field_ids = _supported_fields_from_pr137r(pr137r)
    missing_fields = [
        field_id for field_id in required_field_ids if field_id not in set(supported_field_ids)
    ]
    return {
        "validation_marker": SUCCESS_MARKER if not failures else FAILURE_MARKER,
        "authority_class": AUTHORITY_CLASS,
        "manifest_path": DEFAULT_MANIFEST.as_posix(),
        "schema_path": DEFAULT_SCHEMA.as_posix(),
        "fixture_path": DEFAULT_FIXTURE.as_posix(),
        "pr136_evidence_consumed": [
            path.as_posix() for _field, path in PR136_JSON_EVIDENCE_REFS
        ],
        "pr137r_evidence_consumed": [
            dict(ATOMICROWS_JSON_EVIDENCE_REFS)["pr137r_report_ref"].as_posix(),
            dict(ATOMICROWS_JSON_EVIDENCE_REFS)["pr137r_index_ref"].as_posix(),
        ],
        "pr137l_evidence_consumed": [
            dict(ATOMICROWS_JSON_EVIDENCE_REFS)["pr137l_report_ref"].as_posix(),
            dict(ATOMICROWS_JSON_EVIDENCE_REFS)["pr137l_index_ref"].as_posix(),
        ],
        "pr138_evidence_consumed": [
            dict(ATOMICROWS_JSON_EVIDENCE_REFS)["pr138_semantic_contract_report_ref"].as_posix(),
            dict(ATOMICROWS_JSON_EVIDENCE_REFS)["pr138_field_inventory_ref"].as_posix(),
        ],
        "source_manifest_entry_count": source_manifest.get("manifest_entry_count"),
        "row_family_source_file_count": source_manifest.get("row_family_source_file_count"),
        "existing_bundle_row_count": source_manifest.get("existing_bundle_row_count"),
        "required_field_count": source_manifest.get("required_field_count"),
        "required_field_group_count": source_manifest.get("required_field_group_count"),
        "missing_field_count": len(missing_fields),
        "canonical_venue_ids": list(CANONICAL_STAGE1_VENUE_IDS),
        "false_authority_flags": list(REQUIRED_FALSE_FLAGS),
        "no_mutation_confirmations": dict(no_mutation_confirmations or {}),
        "final_ready": False,
        "remaining_boundary": STATIC_BOUNDARY,
        "deterministic_output": True,
        "failure_count": len(set(failures)),
        "failures": sorted(set(failures)),
    }


def _deterministic_report_check(report: Mapping[str, Any]) -> bool:
    return json.loads(_json_dump(report)) == report


def validate(
    *,
    repo_root: pathlib.Path | str = _REPO_ROOT,
    schema_path: pathlib.Path = DEFAULT_SCHEMA,
    manifest_path: pathlib.Path = DEFAULT_MANIFEST,
    fixture_path: pathlib.Path = DEFAULT_FIXTURE,
    output_path: pathlib.Path | None = DEFAULT_REPORT,
) -> ValidationResult:
    root = pathlib.Path(repo_root).resolve()
    protected_before = _protected_bytes(root)
    failures: list[str] = []

    try:
        schema = load_json(root / schema_path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        schema = {}
        failures.append(f"{REASON_SCHEMA_FAILED}: {schema_path.as_posix()}: {exc}")
    expected_schema = build_json_schema()
    if schema and schema != expected_schema:
        failures.append(f"{REASON_SCHEMA_FAILED}: schema is not generated from canonical policy")

    try:
        manifest = load_yaml(root / manifest_path)
    except (OSError, RegistryParseError) as exc:
        manifest = {}
        failures.append(f"{REASON_SCHEMA_FAILED}: {manifest_path.as_posix()}: {exc}")

    try:
        fixture = load_json(root / fixture_path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        fixture = {}
        failures.append(f"{REASON_FIXTURE_INVALID}: {fixture_path.as_posix()}: {exc}")

    payloads, evidence_failures = _load_json_evidence(root)
    failures.extend(evidence_failures)
    failures.extend(_validate_evidence_payloads(payloads))
    failures.extend(_validate_fixture_payload(fixture))
    failures.extend(validate_manifest_payload(manifest, schema or expected_schema, payloads, root))

    no_mutation_confirmations = {
        "master_plan_not_edited": True,
        "existing_bundle_not_edited": True,
        "row_family_source_files_not_edited": True,
    }
    report = build_report(
        manifest=manifest,
        payloads=payloads,
        failures=failures,
        no_mutation_confirmations=no_mutation_confirmations,
    )
    if not _deterministic_report_check(report):
        failures.append(REASON_OUTPUT_NOT_DETERMINISTIC)
        report = build_report(
            manifest=manifest,
            payloads=payloads,
            failures=failures,
            no_mutation_confirmations=no_mutation_confirmations,
        )

    if output_path is not None:
        _write_text(root / output_path, _json_dump(report))

    protected_after = _protected_bytes(root)
    if protected_before != protected_after:
        failures.append(REASON_PROTECTED_MUTATION)
        no_mutation_confirmations = {
            "master_plan_not_edited": protected_before.get(MASTER_PLAN_PATH.as_posix())
            == protected_after.get(MASTER_PLAN_PATH.as_posix()),
            "existing_bundle_not_edited": protected_before.get(ATOMICROWS_BUNDLE_PATH.as_posix())
            == protected_after.get(ATOMICROWS_BUNDLE_PATH.as_posix()),
            "row_family_source_files_not_edited": all(
                before == protected_after.get(path)
                for path, before in protected_before.items()
                if path.startswith(ROW_FAMILY_SOURCE_DIRECTORY.as_posix())
            ),
        }
        report = build_report(
            manifest=manifest,
            payloads=payloads,
            failures=failures,
            no_mutation_confirmations=no_mutation_confirmations,
        )
        if output_path is not None:
            _write_text(root / output_path, _json_dump(report))

    return ValidationResult(failures=tuple(sorted(set(failures))), report=report)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=pathlib.Path, default=_REPO_ROOT)
    parser.add_argument("--write-schema", action="store_true")
    parser.add_argument("--write-manifest", action="store_true")
    parser.add_argument("--write-fixture", action="store_true")
    parser.add_argument("--schema", type=pathlib.Path, default=DEFAULT_SCHEMA)
    parser.add_argument("--manifest", type=pathlib.Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--fixture", type=pathlib.Path, default=DEFAULT_FIXTURE)
    parser.add_argument("--out", type=pathlib.Path, default=DEFAULT_REPORT)
    args = parser.parse_args(argv)

    root = args.repo_root.resolve()
    if args.write_schema:
        write_schema_file(root)
    if args.write_manifest:
        write_manifest_file(root)
    if args.write_fixture:
        write_fixture_file(root)

    result = validate(
        repo_root=root,
        schema_path=args.schema,
        manifest_path=args.manifest,
        fixture_path=args.fixture,
        output_path=args.out,
    )
    if result.failures:
        for failure in result.failures:
            print(failure)
        return 1
    print(SUCCESS_MARKER)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
