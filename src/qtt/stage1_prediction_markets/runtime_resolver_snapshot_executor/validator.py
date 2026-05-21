"""Validator and deterministic artifact writer for PR134 contracts."""

from __future__ import annotations

import argparse
import ast
import copy
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from . import policy
from .executor import build_runtime_resolver_snapshot_artifacts
from .integrity import compute_integrity_summary


PACKAGE_DIR = "src/qtt/stage1_prediction_markets/runtime_resolver_snapshot_executor"
FIXTURE_DIR = "tests/fixtures/source_evidence/pr134_runtime_resolver_snapshot_executor"

SCHEMA_FILES = {
    "runtime_resolver_input_lock.schema.json": "RUNTIME_RESOLVER_INPUT_LOCK",
    "runtime_resolver_snapshot.schema.json": "RUNTIME_RESOLVER_SNAPSHOT_RECORD",
    "runtime_resolver_binding.schema.json": "RUNTIME_RESOLVER_SNAPSHOT_BINDING",
    "runtime_resolver_integrity_receipt.schema.json": (
        "RUNTIME_RESOLVER_SNAPSHOT_INTEGRITY_RECEIPT"
    ),
    "runtime_resolver_rejection_receipt.schema.json": "RUNTIME_RESOLVER_SNAPSHOT_REJECTION",
    "runtime_resolver_downstream_handoff.schema.json": (
        "RUNTIME_RESOLVER_SNAPSHOT_DOWNSTREAM_HANDOFF"
    ),
    "atomicrows_pre_bridge_compatibility.schema.json": (
        "RUNTIME_RESOLVER_ATOMICROWS_PRE_BRIDGE_COMPATIBILITY_RECORD"
    ),
}

REPORT_FILES = {
    "CODEX_PR134_RUNTIME_RESOLVER_SNAPSHOT_EXECUTOR_REPORT.json": (
        "main_report"
    ),
    "RuntimeResolverSnapshotExecutor.report.json": "executor_report",
    "RuntimeResolverSnapshotIntegrity.report.json": "integrity_report",
    "RuntimeResolverSnapshotDownstreamHandoff.report.json": "handoff_report",
    "RuntimeResolverAtomicRowsPreBridgeCompatibility.report.json": (
        "atomicrows_report"
    ),
}

ROADMAP_RECEIPT_FILES = {
    "CODEX_PR134_MANDATORY_READ_RECEIPT.json": "mandatory_read_receipt",
    "CODEX_PR134_ROUTE_TRIAGE_RECEIPT.json": "route_triage_receipt",
    "CODEX_REPO_PR133_GITHUB_AUDIT_CURRENTIZATION_RECEIPT.json": (
        "pr133_audit_currentization_receipt"
    ),
}

NORMAL_FIXTURE_FILES = {
    "orderbook_event_state_snapshot_downstream_handoff.v1.fixture.json": (
        "orderbook_event_state_snapshot_downstream_handoff"
    ),
    "runtime_resolver_input_locks.v1.fixture.json": "runtime_resolver_input_locks",
    "runtime_resolver_snapshots.v1.fixture.json": "runtime_resolver_snapshots",
    "runtime_resolver_bindings.v1.fixture.json": "runtime_resolver_bindings",
    "runtime_resolver_integrity_receipts.v1.fixture.json": (
        "runtime_resolver_integrity_receipts"
    ),
    "runtime_resolver_rejections.v1.fixture.json": "runtime_resolver_rejections",
    "atomicrows_pre_bridge_compatibility.v1.fixture.json": (
        "atomicrows_pre_bridge_compatibility"
    ),
    "expected_runtime_resolver_downstream_handoff.v1.fixture.json": (
        "runtime_resolver_downstream_handoff"
    ),
}


@dataclass(frozen=True)
class ValidationFailure:
    code: str
    message: str
    artifact_ref: str


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _json_type(value: Any) -> dict[str, Any]:
    if isinstance(value, bool):
        return {"type": "boolean"}
    if isinstance(value, int):
        return {"type": "integer"}
    if isinstance(value, list):
        return {"type": "array"}
    if isinstance(value, dict):
        return {"type": "object"}
    if value is None:
        return {"type": ["string", "null"]}
    return {"type": "string"}


def _schema_for_sample(record_type: str, sample: dict[str, Any], required: list[str]) -> dict[str, Any]:
    properties = {field_name: _json_type(value) for field_name, value in sorted(sample.items())}
    required_fields = set(required)
    required_fields.update(
        field_name
        for field_name in (
            "record_type",
            "schema_version",
            "created_by",
            "authority_class",
            *policy.AUTHORITY_ZERO_FLAGS.keys(),
            *policy.QUANTUM_FORWARD_RUNTIME_RESOLVER_METADATA_FIELDS,
            *policy.QUANTUM_ZERO_AUTHORITY_FLAGS,
            *policy.ATOMICROWS_PRE_BRIDGE_METADATA_FIELDS,
            *policy.ATOMICROWS_ZERO_AUTHORITY_FLAGS,
        )
        if field_name in properties
    )
    properties.setdefault("venue_id", {"type": "string", "enum": list(policy.STAGE1_VENUE_IDS)})
    properties.setdefault("scope_id", {"type": "string", "enum": list(policy.SHARED_SCOPE_IDS)})
    properties["record_type"] = {"type": "string", "const": record_type}
    properties["schema_version"] = {"type": "string", "const": policy.SCHEMA_VERSION}
    properties["created_by"] = {"type": "string", "const": policy.CREATED_BY}
    properties["authority_class"] = {
        "type": "string",
        "const": policy.PACKAGE_AUTHORITY_CLASS,
    }
    if "producer_pr" in properties:
        properties["producer_pr"] = {"type": "string", "const": policy.PRODUCER_REPO_PR}
    if "producer_roadmap_pr" in properties:
        properties["producer_roadmap_pr"] = {
            "type": "string",
            "const": policy.PRODUCER_ROADMAP_PR,
        }
    if "runtime_resolver_input_class" in properties:
        properties["runtime_resolver_input_class"] = {
            "type": "string",
            "enum": list(policy.ALLOWED_RUNTIME_RESOLVER_INPUT_CLASSES),
        }
    if "runtime_resolver_snapshot_class" in properties:
        properties["runtime_resolver_snapshot_class"] = {
            "type": "string",
            "enum": list(policy.ALLOWED_RUNTIME_RESOLVER_SNAPSHOT_CLASSES),
        }
    if "runtime_resolver_readiness_state" in properties:
        properties["runtime_resolver_readiness_state"] = {
            "type": "string",
            "enum": list(policy.ALLOWED_RUNTIME_RESOLVER_READINESS_STATES),
        }
    if "rejected_reason_code" in properties:
        properties["rejected_reason_code"] = {
            "type": "string",
            "enum": list(policy.REJECTION_REASON_CODES),
        }
    if "rejected_action_or_payload_class" in properties:
        properties["rejected_action_or_payload_class"] = {
            "type": "string",
            "enum": list(policy.REJECTION_REASON_CODES),
        }
    if "future_atomicrows_bridge_recommended_after_repo_pr" in properties:
        properties["future_atomicrows_bridge_recommended_after_repo_pr"] = {
            "type": "string",
            "const": policy.RECOMMENDED_ATOMICROWS_BRIDGE_AFTER_REPO_PR,
        }
    if "future_atomicrows_bridge_candidate_repo_pr" in properties:
        properties["future_atomicrows_bridge_candidate_repo_pr"] = {
            "type": "string",
            "const": policy.RECOMMENDED_ATOMICROWS_BRIDGE_CANDIDATE_REPO_PR,
        }
    if "canonical_dependency_state_set" in properties:
        properties["canonical_dependency_state_set"] = {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "dependency_family",
                    "dependency_id",
                    "dependency_state",
                ],
                "properties": {
                    "dependency_family": {"type": "string"},
                    "dependency_id": {"type": "string"},
                    "dependency_state": {
                        "type": "string",
                        "enum": list(policy.ALLOWED_SOURCE_DEPENDENCY_STATES),
                    },
                },
            },
        }
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": f"https://qtt.local/schemas/pr134/{record_type}.schema.json",
        "title": record_type,
        "type": "object",
        "additionalProperties": False,
        "required": sorted(required_fields),
        "properties": properties,
    }


REQUIRED_FIELDS = {
    "RUNTIME_RESOLVER_INPUT_LOCK": [
        "record_type",
        "schema_version",
        "input_lock_id",
        "runtime_resolver_input_lock_id",
        "orderbook_event_state_snapshot_handoff_ref",
        "orderbook_snapshot_refs",
        "event_state_snapshot_refs",
        "market_data_ingest_dependency_refs",
        "credential_readiness_dependency_refs",
        "accepted_source_dependency_refs",
        "connector_semantic_dependency_refs",
        "contract_normalization_dependency_ref",
        "comparability_scope_dependency_ref",
        "liquidity_scope_dependency_ref",
        "canonical_input_identity_ref",
        "candidate_set_snapshot_version_id",
        "candidate_set_snapshot_parent_version_id",
        "synthetic_candidate_set_ref",
        "candidate_scope_lock_ref",
        "future_replay_paper_input_identity_ref",
        "deterministic_sequence_id",
        "input_payload_is_synthetic",
        "fixture_runtime_resolver_snapshot_allowed",
        "live_runtime_execution_allowed",
    ],
    "RUNTIME_RESOLVER_SNAPSHOT_RECORD": [
        "record_type",
        "schema_version",
        "runtime_resolver_snapshot_id",
        "runtime_resolver_input_lock_ref",
        "runtime_resolver_snapshot_class",
        "runtime_resolver_readiness_state",
        "canonical_dependency_state_set",
        "canonical_input_identity_ref",
        "candidate_set_snapshot_lock_metadata_created",
        "candidate_set_snapshot_version_id",
        "candidate_set_snapshot_parent_version_id",
        "synthetic_candidate_set_ref",
        "candidate_scope_lock_ref",
        "future_replay_paper_input_identity_ref",
        "canonical_sort_key",
        "deterministic_sequence_id",
        "fixture_runtime_resolver_snapshot_created",
    ],
    "RUNTIME_RESOLVER_SNAPSHOT_BINDING": [
        "record_type",
        "schema_version",
        "binding_id",
        "executor_name",
        "executor_version",
        "executor_scope",
        "input_lock_refs",
        "runtime_resolver_snapshot_refs",
        "orderbook_event_state_snapshot_handoff_ref",
        "market_data_ingest_handoff_ref",
        "credential_readiness_handoff_ref",
        "source_dependency_refs",
        "connector_semantic_dependency_refs",
        "runtime_resolver_readiness_policy_ref",
        "candidate_set_snapshot_lock_policy_ref",
        "future_replay_paper_input_identity_ref",
        "allowed_use",
        "disallowed_use",
    ],
    "RUNTIME_RESOLVER_SNAPSHOT_INTEGRITY_RECEIPT": [
        "record_type",
        "schema_version",
        "integrity_receipt_id",
        "runtime_resolver_binding_ref",
        "runtime_resolver_snapshot_refs",
        "deterministic_sorting_verified",
        "canonical_sequence_verified",
        "dependency_state_policy_verified",
        "versioned_candidate_set_snapshot_lock_metadata_verified",
        "future_candidate_additions_allowed_by_new_versions",
        "replay_paper_input_identity_metadata_verified",
        *policy.ZERO_COUNT_INVARIANTS,
    ],
    "RUNTIME_RESOLVER_SNAPSHOT_REJECTION": [
        "record_type",
        "schema_version",
        "rejection_id",
        "rejected_action_or_payload_class",
        "rejected_reason_code",
        "rejected_artifact_ref",
        "raw_live_payload_stored",
        "live_fetch_performed",
        "validator_fail_closed",
    ],
    "RUNTIME_RESOLVER_SNAPSHOT_DOWNSTREAM_HANDOFF": [
        "record_type",
        "schema_version",
        "handoff_id",
        "producer_pr",
        "producer_roadmap_pr",
        "upstream_prs",
        "downstream_prs",
        "venue_specific_scope",
        "shared_scope",
        "contains_fixture_runtime_resolver_snapshot",
        "contains_versioned_candidate_set_snapshot_lock_metadata",
        "contains_future_replay_paper_input_identity_metadata",
        "contains_global_candidate_universe_freeze",
        "contains_live_candidate_discovery",
        "contains_live_candidate_import",
        "contains_live_contract_selection",
        "contains_live_runtime_resolver_authority",
        "contains_historical_dataset_digest",
        "contains_feature_vector",
        "contains_trading_signal",
        "contains_replay_execution",
        "contains_paper_execution",
        "contains_order_authority",
        "contains_profit_evidence",
        "downstream_pr117_contract_prepared",
    ],
    "RUNTIME_RESOLVER_ATOMICROWS_PRE_BRIDGE_COMPATIBILITY_RECORD": [
        "record_type",
        "schema_version",
        "compatibility_id",
        "producer_pr",
        "producer_roadmap_pr",
        "runtime_resolver_binding_ref",
        "runtime_resolver_snapshot_refs",
        *policy.ATOMICROWS_PRE_BRIDGE_METADATA_FIELDS,
        *policy.ATOMICROWS_ZERO_AUTHORITY_FLAGS,
    ],
}


def build_schema_documents(artifacts: dict[str, Any] | None = None) -> dict[str, dict[str, Any]]:
    artifacts = artifacts or build_runtime_resolver_snapshot_artifacts()
    samples = {
        "RUNTIME_RESOLVER_INPUT_LOCK": artifacts["runtime_resolver_input_locks"][0],
        "RUNTIME_RESOLVER_SNAPSHOT_RECORD": artifacts["runtime_resolver_snapshots"][0],
        "RUNTIME_RESOLVER_SNAPSHOT_BINDING": artifacts["runtime_resolver_bindings"][0],
        "RUNTIME_RESOLVER_SNAPSHOT_INTEGRITY_RECEIPT": (
            artifacts["runtime_resolver_integrity_receipts"][0]
        ),
        "RUNTIME_RESOLVER_SNAPSHOT_REJECTION": artifacts["runtime_resolver_rejections"][0],
        "RUNTIME_RESOLVER_SNAPSHOT_DOWNSTREAM_HANDOFF": (
            artifacts["runtime_resolver_downstream_handoff"]
        ),
        "RUNTIME_RESOLVER_ATOMICROWS_PRE_BRIDGE_COMPATIBILITY_RECORD": (
            artifacts["atomicrows_pre_bridge_compatibility"][0]
        ),
    }
    return {
        file_name: _schema_for_sample(
            record_type,
            samples[record_type],
            REQUIRED_FIELDS[record_type],
        )
        for file_name, record_type in SCHEMA_FILES.items()
    }


def _scope_value(record: dict[str, Any]) -> str | None:
    value = record.get("venue_id") or record.get("scope_id")
    return value if isinstance(value, str) else None


def _record_list(artifacts: dict[str, Any]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for key in (
        "runtime_resolver_input_locks",
        "runtime_resolver_snapshots",
        "runtime_resolver_bindings",
        "runtime_resolver_integrity_receipts",
        "runtime_resolver_rejections",
        "atomicrows_pre_bridge_compatibility",
    ):
        records.extend(artifacts.get(key, []))
    records.append(artifacts.get("runtime_resolver_downstream_handoff", {}))
    return [record for record in records if isinstance(record, dict)]


SUMMARY_FAILURE_CODES = {
    "duplicate_runtime_resolver_snapshot_id_count": "DUPLICATE_RUNTIME_RESOLVER_SNAPSHOT_ID",
    "missing_input_lock_count": "MISSING_RUNTIME_RESOLVER_INPUT_LOCK",
    "missing_candidate_scope_lock_count": "MISSING_CANDIDATE_SCOPE_LOCK",
    "missing_contract_normalization_dependency_count": (
        "MISSING_CONTRACT_NORMALIZATION_DEPENDENCY"
    ),
    "missing_comparability_scope_dependency_count": (
        "MISSING_COMPARABILITY_SCOPE_DEPENDENCY"
    ),
    "missing_liquidity_scope_dependency_count": "MISSING_LIQUIDITY_SCOPE_DEPENDENCY",
    "cross_venue_scope_mismatch_count": "VENUE_SCOPE_MISMATCH",
    "invalid_readiness_state_count": "BLOCKED_SCHEMA_MISMATCH",
    "unresolved_dependency_ready_claim_count": "READY_WITH_UNRESOLVED_DEPENDENCY",
    "stale_dependency_ready_claim_count": "STALE_DEPENDENCY_READY_CLAIM",
    "conflict_dependency_ready_claim_count": "CONFLICT_DEPENDENCY_READY_CLAIM",
    "exact_live_contract_id_created_count": "EXACT_LIVE_CONTRACT_ID_CREATED",
    "global_candidate_universe_freeze_claim_count": (
        "GLOBAL_CANDIDATE_UNIVERSE_FREEZE_CLAIM"
    ),
    "future_candidate_addition_blocked_count": "FUTURE_CANDIDATE_ADDITION_BLOCKED",
    "live_candidate_discovery_created_count": "LIVE_CANDIDATE_DISCOVERY_CREATED",
    "live_candidate_import_created_count": "LIVE_CANDIDATE_IMPORT_CREATED",
    "live_contract_selection_created_count": "LIVE_CONTRACT_SELECTION_CREATED",
    "live_runtime_authority_created_count": "LIVE_RUNTIME_AUTHORITY_CREATED",
    "historical_dataset_digest_created_count": "HISTORICAL_DATASET_DIGEST_CREATED",
    "feature_vector_created_count": "FEATURE_VECTOR_CREATED",
    "trading_signal_created_count": "TRADING_SIGNAL_CREATED",
    "ranking_output_created_count": "RANKING_OUTPUT_CREATED",
    "scoring_ranking_arbitration_output_created_count": (
        "SCORING_RANKING_ARBITRATION_OUTPUT_CREATED"
    ),
    "replay_execution_created_count": "REPLAY_EXECUTION_CREATED",
    "paper_execution_created_count": "PAPER_EXECUTION_CREATED",
    "replay_result_created_count": "REPLAY_RESULT_CREATED",
    "paper_result_created_count": "PAPER_RESULT_CREATED",
    "live_trading_created_count": "LIVE_TRADING_CREATED",
    "order_authority_count": "ORDER_AUTHORITY_CREATED",
    "order_execution_count": "ORDER_EXECUTION_CREATED",
    "profit_evidence_count": "PROFIT_EVIDENCE_CREATED",
    "live_market_data_fetch_count": "LIVE_MARKET_DATA_FETCH_CREATED",
    "rest_client_created_count": "REST_CLIENT_CREATED",
    "websocket_client_created_count": "WEBSOCKET_CLIENT_CREATED",
    "venue_api_call_count": "VENUE_API_CALL_CREATED",
    "network_io_count": "NETWORK_IO_CREATED",
    "credential_provider_call_count": "CREDENTIAL_PROVIDER_CALLED",
    "live_credential_resolution_count": "LIVE_CREDENTIAL_RESOLUTION_PERFORMED",
    "private_state_fetch_count": "PRIVATE_STATE_FETCH_CREATED",
    "runtime_cash_authority_count": "RUNTIME_CASH_AUTHORITY_CREATED",
    "quantum_runtime_feature_computation_created_count": (
        "QUANTUM_RUNTIME_FEATURE_COMPUTATION_CREATED"
    ),
    "quantum_optimizer_input_created_count": "QUANTUM_OPTIMIZER_INPUT_CREATED",
    "quantum_trading_signal_created_count": "QUANTUM_TRADING_SIGNAL_CREATED",
    "quantum_backend_simulator_optimizer_execution_count": "QUANTUM_EXECUTION_CREATED",
    "quantum_advantage_claim_created_count": "QUANTUM_ADVANTAGE_CLAIM_CREATED",
    "atomicrows_bridge_authority_created_count": "ATOMICROWS_BRIDGE_AUTHORITY_CREATED",
    "atomicrows_bundle_created_count": "ATOMICROWS_BUNDLE_CREATED",
    "atomicrows_sha_created_count": "ATOMICROWS_SHA_CREATED",
    "atomicrows_row_records_created_count": "ATOMICROWS_ROW_RECORDS_CREATED",
    "atomicrows_4183_completion_claim_created_count": (
        "ATOMICROWS_4183_COMPLETION_CLAIM_CREATED"
    ),
}


def _is_valid_pr133_handoff(handoff: dict[str, Any] | None) -> bool:
    if not handoff:
        return False
    return (
        handoff.get("handoff_id") == policy.PR133_HANDOFF_ID
        and handoff.get("producer_pr") == "PR133"
        and handoff.get("producer_roadmap_pr") == "PR115"
        and "PR116" in handoff.get("downstream_prs", [])
    )


def _validate_import_guards(repo_root: Path | None) -> list[ValidationFailure]:
    if repo_root is None:
        return []
    candidates: list[Path] = []
    package_path = repo_root / PACKAGE_DIR
    if package_path.exists():
        candidates.extend(sorted(package_path.glob("*.py")))
    for tool_name in (
        "runtime_resolver_snapshot_executor_validate.py",
        "runtime_resolver_snapshot_fixture_build.py",
    ):
        tool_path = repo_root / "tools" / tool_name
        if tool_path.exists():
            candidates.append(tool_path)
    test_path = repo_root / "tests" / "source_evidence"
    if test_path.exists():
        candidates.extend(sorted(test_path.glob("test_pr134_*.py")))
        support_path = test_path / "pr134_runtime_resolver_snapshot_support.py"
        if support_path.exists():
            candidates.append(support_path)

    failures: list[ValidationFailure] = []
    banned = set(policy.BANNED_IMPORT_MODULES)
    for path in candidates:
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        for node in ast.walk(tree):
            import_name: str | None = None
            if (
                isinstance(node, ast.Attribute)
                and node.attr == "environ"
                and isinstance(node.value, ast.Name)
                and node.value.id == "os"
            ):
                failures.append(
                    ValidationFailure(
                        "CREDENTIAL_ENVIRONMENT_LOOKUP_FORBIDDEN",
                        "PR134 files must not use environment credential lookup",
                        str(path.relative_to(repo_root)).replace("\\", "/"),
                    )
                )
            if isinstance(node, ast.Import):
                for alias in node.names:
                    import_name = alias.name
                    if import_name in banned or any(
                        import_name.startswith(f"{name}.") for name in banned
                    ):
                        failures.append(
                            ValidationFailure(
                                "BANNED_IMPORT_USED",
                                f"Forbidden import {import_name}",
                                str(path.relative_to(repo_root)).replace("\\", "/"),
                            )
                        )
            elif isinstance(node, ast.ImportFrom):
                import_name = node.module
                if import_name and (
                    import_name in banned
                    or any(import_name.startswith(f"{name}.") for name in banned)
                ):
                    failures.append(
                        ValidationFailure(
                            "BANNED_IMPORT_USED",
                            f"Forbidden import {import_name}",
                            str(path.relative_to(repo_root)).replace("\\", "/"),
                        )
                    )
    return failures


def validate_artifacts(
    artifacts: dict[str, Any] | None = None,
    *,
    repo_root: Path | None = None,
) -> list[ValidationFailure]:
    artifacts = copy.deepcopy(artifacts or build_runtime_resolver_snapshot_artifacts())
    input_locks = artifacts.get("runtime_resolver_input_locks", [])
    snapshots = artifacts.get("runtime_resolver_snapshots", [])
    bindings = artifacts.get("runtime_resolver_bindings", [])
    atomicrows_compatibility = artifacts.get("atomicrows_pre_bridge_compatibility", [])
    pr133_handoff = artifacts.get("orderbook_event_state_snapshot_downstream_handoff")

    failures: list[ValidationFailure] = []
    if not pr133_handoff:
        failures.append(
            ValidationFailure(
                "MISSING_PR133_HANDOFF",
                "PR134 requires PR133 orderbook/event-state snapshot handoff metadata",
                "orderbook_event_state_snapshot_downstream_handoff",
            )
        )
    elif not _is_valid_pr133_handoff(pr133_handoff):
        failures.append(
            ValidationFailure(
                "MALFORMED_PR133_HANDOFF",
                "PR133 handoff metadata is malformed or does not route to PR116",
                "orderbook_event_state_snapshot_downstream_handoff",
            )
        )

    venue_bindings = [binding for binding in bindings if binding.get("venue_id")]
    shared_bindings = [binding for binding in bindings if binding.get("scope_id")]
    if sorted(binding["venue_id"] for binding in venue_bindings) != sorted(policy.STAGE1_VENUE_IDS):
        failures.append(
            ValidationFailure(
                "STAGE1_VENUE_BINDINGS_MISMATCH",
                "Exactly three venue-specific bindings are required",
                "runtime_resolver_bindings",
            )
        )
    if [binding.get("scope_id") for binding in shared_bindings] != list(policy.SHARED_SCOPE_IDS):
        failures.append(
            ValidationFailure(
                "SHARED_SCOPE_BINDING_MISMATCH",
                "PREDICTION_MARKETS_GENERAL must be shared metadata, not a venue",
                "runtime_resolver_bindings",
            )
        )

    sorted_snapshots = sorted(
        snapshots,
        key=lambda record: (
            str(record.get("venue_id") or record.get("scope_id")),
            int(record.get("deterministic_sequence_id", 0)),
        ),
    )
    if snapshots != sorted_snapshots:
        failures.append(
            ValidationFailure(
                "CANONICAL_SORT_ORDER_VIOLATION",
                "Runtime resolver snapshots are not canonical ordered",
                "runtime_resolver_snapshots",
            )
        )

    sorted_versions = sorted(
        input_locks,
        key=lambda record: (
            str(record.get("candidate_set_snapshot_version_id")),
            str(record.get("candidate_set_snapshot_parent_version_id")),
            int(record.get("deterministic_sequence_id", 0)),
        ),
    )
    if input_locks != sorted_versions:
        failures.append(
            ValidationFailure(
                "CANDIDATE_SET_VERSION_ORDER_VIOLATION",
                "Candidate-set snapshot versions are not canonical ordered",
                "runtime_resolver_input_locks",
            )
        )

    fixture_runtime_resolver_snapshot_count = sum(
        1 for snapshot in snapshots if snapshot.get("fixture_runtime_resolver_snapshot_created") is True
    )
    if fixture_runtime_resolver_snapshot_count < 3:
        failures.append(
            ValidationFailure(
                "FIXTURE_RUNTIME_RESOLVER_SNAPSHOT_COUNT_TOO_LOW",
                "At least three fixture runtime resolver snapshots are required",
                "runtime_resolver_snapshots",
            )
        )

    versioned_candidate_set_snapshot_lock_count = sum(
        1
        for record in input_locks + snapshots
        if record.get("candidate_set_snapshot_lock_metadata_created") is True
        or record.get("candidate_set_snapshot_created_from_fixture") is True
    )
    if versioned_candidate_set_snapshot_lock_count < 3:
        failures.append(
            ValidationFailure(
                "VERSIONED_CANDIDATE_SET_SNAPSHOT_LOCK_COUNT_TOO_LOW",
                "At least three versioned candidate-set snapshot-lock records are required",
                "runtime_resolver_input_locks",
            )
        )

    quantum_ready_count = sum(
        1
        for record in _record_list(artifacts)
        if record.get("quantum_ready_runtime_resolver_snapshot_contract") is True
    )
    if quantum_ready_count < 4:
        failures.append(
            ValidationFailure(
                "QUANTUM_READY_METADATA_COUNT_TOO_LOW",
                "Four quantum-ready metadata records are required",
                "runtime_resolver_snapshots",
            )
        )

    atomicrows_pre_bridge_count = sum(
        1
        for record in _record_list(artifacts)
        if record.get("atomicrows_pre_bridge_compatibility_metadata_created") is True
    )
    if atomicrows_pre_bridge_count < 4:
        failures.append(
            ValidationFailure(
                "ATOMICROWS_PRE_BRIDGE_METADATA_COUNT_TOO_LOW",
                "Four AtomicRows pre-bridge metadata records are required",
                "atomicrows_pre_bridge_compatibility",
            )
        )

    summary = compute_integrity_summary(
        input_locks,
        snapshots,
        bindings,
        pr133_handoff if _is_valid_pr133_handoff(pr133_handoff) else None,
        atomicrows_compatibility,
    )
    for summary_key, reason_code in SUMMARY_FAILURE_CODES.items():
        if int(summary.get(summary_key, 0)) != 0:
            failures.append(
                ValidationFailure(
                    reason_code,
                    f"{summary_key} must be zero",
                    "runtime_resolver_integrity_summary",
                )
            )

    for record in _record_list(artifacts):
        for field_name, expected_value in policy.AUTHORITY_ZERO_FLAGS.items():
            if record.get(field_name, expected_value) != expected_value:
                failures.append(
                    ValidationFailure(
                        "AUTHORITY_ZERO_FLAG_VIOLATION",
                        f"{field_name} must remain {expected_value!r}",
                        str(record.get("record_type", "UNKNOWN_RECORD")),
                    )
                )
        if record.get("candidate_set_snapshot_is_global_permanent_freeze") is True:
            failures.append(
                ValidationFailure(
                    "GLOBAL_CANDIDATE_UNIVERSE_FREEZE_CLAIM",
                    "PR134 must not permanently freeze the global candidate universe",
                    str(record.get("record_type", "UNKNOWN_RECORD")),
                )
            )
        if record.get("candidate_set_snapshot_allows_future_candidate_additions") is False:
            failures.append(
                ValidationFailure(
                    "FUTURE_CANDIDATE_ADDITION_BLOCKED",
                    "Future candidates must be allowed through new snapshot versions",
                    str(record.get("record_type", "UNKNOWN_RECORD")),
                )
            )

    failures.extend(_validate_import_guards(repo_root))
    return failures


def _fixture_wrapper(fixture_id: str, payload: Any) -> dict[str, Any]:
    return {
        "fixture_id": fixture_id,
        "fixture_payload_is_synthetic": True,
        "producer_pr": policy.PRODUCER_REPO_PR,
        "producer_roadmap_pr": policy.PRODUCER_ROADMAP_PR,
        "schema_version": policy.REPORT_SCHEMA_VERSION,
        "mode": "SOURCE_REQUIRED",
        "execution": "DISABLED",
        "raw_live_payload_stored": False,
        "live_fetch_performed": False,
        "network_io_created": False,
        "records": payload,
    }


Mutation = Callable[[dict[str, Any]], None]


def _mutate_handoff_missing(artifacts: dict[str, Any]) -> None:
    artifacts["orderbook_event_state_snapshot_downstream_handoff"] = None


def _mutate_handoff_malformed(artifacts: dict[str, Any]) -> None:
    artifacts["orderbook_event_state_snapshot_downstream_handoff"]["handoff_id"] = "MALFORMED"


def _mutate_snapshot_field(artifacts: dict[str, Any], field_name: str, value: Any) -> None:
    artifacts["runtime_resolver_snapshots"][0][field_name] = value


def _mutate_input_lock_field(artifacts: dict[str, Any], field_name: str, value: Any) -> None:
    artifacts["runtime_resolver_input_locks"][0][field_name] = value


def _mutate_scope_mismatch(artifacts: dict[str, Any]) -> None:
    artifacts["runtime_resolver_snapshots"][0]["venue_id"] = "POLYMARKET"
    artifacts["runtime_resolver_snapshots"][0].pop("scope_id", None)


def _mutate_ready_dependency(artifacts: dict[str, Any], dependency_state: str) -> None:
    snapshot = artifacts["runtime_resolver_snapshots"][0]
    snapshot["runtime_resolver_readiness_state"] = "READY_METADATA_ONLY"
    snapshot["canonical_dependency_state_set"][0]["dependency_state"] = dependency_state


def _mutate_duplicate_snapshot_id(artifacts: dict[str, Any]) -> None:
    artifacts["runtime_resolver_snapshots"][1]["runtime_resolver_snapshot_id"] = (
        artifacts["runtime_resolver_snapshots"][0]["runtime_resolver_snapshot_id"]
    )


def _mutate_missing_input_lock(artifacts: dict[str, Any]) -> None:
    artifacts["runtime_resolver_snapshots"][0]["runtime_resolver_input_lock_ref"] = (
        "PR134_MISSING_RUNTIME_RESOLVER_INPUT_LOCK"
    )


def _mutate_atomicrows_row_records(artifacts: dict[str, Any]) -> None:
    artifacts["atomicrows_pre_bridge_compatibility"][0]["atomicrows_row_records_created_count"] = 1


def _mutate_atomicrows_4183_claim(artifacts: dict[str, Any]) -> None:
    artifacts["atomicrows_pre_bridge_compatibility"][0]["atomicrows_4183_completion_claim_created"] = True


MALFORMED_FIXTURE_SPECS: tuple[tuple[str, str, Mutation], ...] = (
    ("malformed_missing_pr133_handoff.v1.fixture.json", "MISSING_PR133_HANDOFF", _mutate_handoff_missing),
    ("malformed_scope_mismatch.v1.fixture.json", "VENUE_SCOPE_MISMATCH", _mutate_scope_mismatch),
    ("malformed_live_runtime_authority_created.v1.fixture.json", "LIVE_RUNTIME_AUTHORITY_CREATED", lambda artifacts: _mutate_snapshot_field(artifacts, "live_runtime_resolver_authority_created", True)),
    ("malformed_live_market_data_fetch.v1.fixture.json", "LIVE_MARKET_DATA_FETCH_CREATED", lambda artifacts: _mutate_input_lock_field(artifacts, "live_market_data_fetch_created", True)),
    ("malformed_private_state_fetch.v1.fixture.json", "PRIVATE_STATE_FETCH_CREATED", lambda artifacts: _mutate_input_lock_field(artifacts, "private_state_fetch_created", True)),
    ("malformed_historical_dataset_digest_created.v1.fixture.json", "HISTORICAL_DATASET_DIGEST_CREATED", lambda artifacts: _mutate_snapshot_field(artifacts, "historical_dataset_digest_created", True)),
    ("malformed_feature_vector_created.v1.fixture.json", "FEATURE_VECTOR_CREATED", lambda artifacts: _mutate_snapshot_field(artifacts, "runtime_feature_vector_created", True)),
    ("malformed_trading_signal_created.v1.fixture.json", "TRADING_SIGNAL_CREATED", lambda artifacts: _mutate_snapshot_field(artifacts, "trading_signal_created", True)),
    ("malformed_replay_execution_created.v1.fixture.json", "REPLAY_EXECUTION_CREATED", lambda artifacts: _mutate_snapshot_field(artifacts, "replay_execution_created", True)),
    ("malformed_paper_execution_created.v1.fixture.json", "PAPER_EXECUTION_CREATED", lambda artifacts: _mutate_snapshot_field(artifacts, "paper_execution_created", True)),
    ("malformed_replay_result_created.v1.fixture.json", "REPLAY_RESULT_CREATED", lambda artifacts: _mutate_snapshot_field(artifacts, "replay_result_created", True)),
    ("malformed_paper_result_created.v1.fixture.json", "PAPER_RESULT_CREATED", lambda artifacts: _mutate_snapshot_field(artifacts, "paper_result_created", True)),
    ("malformed_order_authority_created.v1.fixture.json", "ORDER_AUTHORITY_CREATED", lambda artifacts: _mutate_snapshot_field(artifacts, "order_authority_created", True)),
    ("malformed_quantum_runtime_feature_computation_created.v1.fixture.json", "QUANTUM_RUNTIME_FEATURE_COMPUTATION_CREATED", lambda artifacts: _mutate_snapshot_field(artifacts, "quantum_runtime_feature_computation_created", True)),
    ("malformed_quantum_optimizer_input_created.v1.fixture.json", "QUANTUM_OPTIMIZER_INPUT_CREATED", lambda artifacts: _mutate_snapshot_field(artifacts, "quantum_optimizer_input_created", True)),
    ("malformed_quantum_trading_signal_created.v1.fixture.json", "QUANTUM_TRADING_SIGNAL_CREATED", lambda artifacts: _mutate_snapshot_field(artifacts, "quantum_trading_signal_created", True)),
    ("malformed_atomicrows_bundle_created.v1.fixture.json", "ATOMICROWS_BUNDLE_CREATED", lambda artifacts: _mutate_snapshot_field(artifacts, "atomicrows_bundle_created", True)),
    ("malformed_atomicrows_row_records_created.v1.fixture.json", "ATOMICROWS_ROW_RECORDS_CREATED", _mutate_atomicrows_row_records),
    ("malformed_atomicrows_4183_completion_claim.v1.fixture.json", "ATOMICROWS_4183_COMPLETION_CLAIM_CREATED", _mutate_atomicrows_4183_claim),
    ("malformed_ready_with_unresolved_dependency.v1.fixture.json", "READY_WITH_UNRESOLVED_DEPENDENCY", lambda artifacts: _mutate_ready_dependency(artifacts, "SOURCE_REQUIRED")),
    ("malformed_duplicate_runtime_resolver_snapshot_id.v1.fixture.json", "DUPLICATE_RUNTIME_RESOLVER_SNAPSHOT_ID", _mutate_duplicate_snapshot_id),
    ("malformed_missing_runtime_resolver_input_lock.v1.fixture.json", "MISSING_RUNTIME_RESOLVER_INPUT_LOCK", _mutate_missing_input_lock),
    ("malformed_missing_candidate_scope_lock.v1.fixture.json", "MISSING_CANDIDATE_SCOPE_LOCK", lambda artifacts: _mutate_snapshot_field(artifacts, "candidate_scope_lock_ref", "")),
    ("malformed_missing_contract_normalization_dependency.v1.fixture.json", "MISSING_CONTRACT_NORMALIZATION_DEPENDENCY", lambda artifacts: _mutate_input_lock_field(artifacts, "contract_normalization_dependency_ref", "")),
    ("malformed_missing_comparability_scope_dependency.v1.fixture.json", "MISSING_COMPARABILITY_SCOPE_DEPENDENCY", lambda artifacts: _mutate_input_lock_field(artifacts, "comparability_scope_dependency_ref", "")),
    ("malformed_missing_liquidity_scope_dependency.v1.fixture.json", "MISSING_LIQUIDITY_SCOPE_DEPENDENCY", lambda artifacts: _mutate_input_lock_field(artifacts, "liquidity_scope_dependency_ref", "")),
    ("malformed_stale_dependency_ready_claim.v1.fixture.json", "STALE_DEPENDENCY_READY_CLAIM", lambda artifacts: _mutate_ready_dependency(artifacts, "SOURCE_REVALIDATION_REQUIRED")),
    ("malformed_conflict_dependency_ready_claim.v1.fixture.json", "CONFLICT_DEPENDENCY_READY_CLAIM", lambda artifacts: _mutate_ready_dependency(artifacts, "BLOCKED_CONFLICT")),
    ("malformed_exact_live_contract_id_created.v1.fixture.json", "EXACT_LIVE_CONTRACT_ID_CREATED", lambda artifacts: _mutate_snapshot_field(artifacts, "exact_live_contract_id_created", True)),
    ("malformed_global_candidate_universe_freeze_claim.v1.fixture.json", "GLOBAL_CANDIDATE_UNIVERSE_FREEZE_CLAIM", lambda artifacts: _mutate_snapshot_field(artifacts, "candidate_set_snapshot_is_global_permanent_freeze", True)),
    ("malformed_future_candidate_addition_blocked.v1.fixture.json", "FUTURE_CANDIDATE_ADDITION_BLOCKED", lambda artifacts: _mutate_snapshot_field(artifacts, "candidate_set_snapshot_allows_future_candidate_additions", False)),
    ("malformed_live_candidate_discovery_created.v1.fixture.json", "LIVE_CANDIDATE_DISCOVERY_CREATED", lambda artifacts: _mutate_snapshot_field(artifacts, "live_candidate_discovery_created", True)),
    ("malformed_live_candidate_import_created.v1.fixture.json", "LIVE_CANDIDATE_IMPORT_CREATED", lambda artifacts: _mutate_snapshot_field(artifacts, "live_candidate_import_created", True)),
    ("malformed_live_contract_selection_created.v1.fixture.json", "LIVE_CONTRACT_SELECTION_CREATED", lambda artifacts: _mutate_snapshot_field(artifacts, "live_contract_selection_created", True)),
    ("malformed_malformed_pr133_handoff.v1.fixture.json", "MALFORMED_PR133_HANDOFF", _mutate_handoff_malformed),
)


def build_malformed_fixture_payloads() -> dict[str, dict[str, Any]]:
    payloads: dict[str, dict[str, Any]] = {}
    for file_name, expected_code, mutator in MALFORMED_FIXTURE_SPECS:
        artifacts = copy.deepcopy(build_runtime_resolver_snapshot_artifacts())
        mutator(artifacts)
        payloads[file_name] = {
            "fixture_id": file_name.replace(".json", "").upper(),
            "expected_rejection_reason_code": expected_code,
            "fixture_payload_is_synthetic": True,
            "mode": "SOURCE_REQUIRED",
            "execution": "DISABLED",
            "raw_live_payload_stored": False,
            "live_fetch_performed": False,
            "network_io_created": False,
            "artifacts": artifacts,
        }
    return payloads


def validate_malformed_fixture_payload(payload: dict[str, Any]) -> list[ValidationFailure]:
    expected_code = payload["expected_rejection_reason_code"]
    failures = validate_artifacts(payload["artifacts"])
    if expected_code not in {failure.code for failure in failures}:
        failures.append(
            ValidationFailure(
                "EXPECTED_REJECTION_CODE_NOT_OBSERVED",
                f"Expected malformed fixture to fail with {expected_code}",
                str(payload.get("fixture_id", "malformed_fixture")),
            )
        )
    return failures


MANDATORY_FILES_READ = [
    "docs/roadmap/README.md",
    "docs/roadmap/QTT_PRs_Roadmap_Consolidated_Static_Runtime_Live_Stage1_to_Stage5_v1_0.md",
    "docs/roadmap/QTT_PRs_Roadmap_Index_v1_0.json",
    "docs/roadmap/QTT_PR_Blueprints_Stage1_to_Stage5_PR83_to_PR224_v1_0.md",
    "docs/roadmap/QTT_PR_Blueprints_Index_PR83_to_PR224_v1_0.json",
    "docs/roadmap/QTT_PR_Identity_Roster_v1_0.json",
    "docs/roadmap/QTT_Roadmap_Execution_State_Controller_v1_0.json",
    "docs/master_plan/QTT_MasterPlan_Current.md",
    "docs/master_plan/source_evidence/QTT_OWNER_SOURCE_EVIDENCE_DEFINITIONS_PACKET.md",
]

PR105_TO_PR133_ARTIFACTS_INSPECTED = [
    "source-evidence retrieval executor artifacts",
    "accepted source-evidence acceptance executor and ledger artifacts",
    "accepted-source to connector semantic binding consumer-gate artifacts",
    "source revalidation supersession materiality scheduler artifacts",
    "connector semantic binding implementation gate artifacts",
    "per-venue execution lifecycle model builder artifacts",
    "cross-venue execution normalization binding artifacts",
    "src/qtt/stage1_prediction_markets/capital_risk",
    "src/qtt/stage1_prediction_markets/private_state_receipts",
    "src/qtt/stage1_prediction_markets/credential_readiness",
    "src/qtt/stage1_prediction_markets/market_data_ingest",
    "src/qtt/stage1_prediction_markets/orderbook_event_state_snapshot",
    "src/qtt/stage1_prediction_markets/runtime_resolver",
    "src/qtt/stage1_prediction_markets/runtime_resolver_snapshot",
    "docs/master_plan/source_evidence/generated/CODEX_PR132_VENUE_MARKET_DATA_INGEST_ADAPTERS_REPORT.json",
    "docs/master_plan/source_evidence/generated/MarketDataIngestDownstreamHandoff.report.json",
    "docs/master_plan/source_evidence/generated/CODEX_PR133_ORDERBOOK_EVENT_STATE_SNAPSHOT_BUILDER_REPORT.json",
    "docs/master_plan/source_evidence/generated/OrderbookEventStateSnapshotDownstreamHandoff.report.json",
    "docs/master_plan/source_evidence/generated/OrderbookEventStateSnapshotBuilder.report.json",
    "docs/master_plan/source_evidence/generated/OrderbookSnapshotIntegrity.report.json",
    "docs/master_plan/source_evidence/generated/EventStateSnapshotIntegrity.report.json",
    "docs/master_plan/source_evidence/generated/AtomicRowsPreBridgeCompatibility.report.json",
    "tools/credential_alias_secret_no_capture_readiness_validate.py",
    "tools/venue_market_data_ingest_adapters_validate.py",
    "tools/orderbook_event_state_snapshot_builder_validate.py",
    "tools/run_validation_gates.py",
    "tests/fail_closed/test_run_validation_gates.py",
]

ATOMICROWS_AUTHORITY_ARTIFACTS_INSPECTED = [
    "docs/master_plan/atomic_rows/AtomicRows.bundle.jsonl",
    "docs/master_plan/atomic_rows/AtomicRows.bundle.sha256",
    "docs/master_plan/generated/AtomicRowsBundleBoundaryStateContract.report.json",
    "docs/master_plan/generated/AtomicRowsBundleMaterialization.report.json",
    "docs/master_plan/generated/AtomicRowsBundleShaFreezeAuthorityGate.report.json",
    "docs/master_plan/generated/AtomicRowsShaFreezeFinalReadinessStateContract.report.json",
    "docs/master_plan/generated/AtomicRowsExactRowAgentFamilyEligibilityMatrix.report.json",
    "docs/master_plan/generated/AtomicRowsExactRowSourceMaterialization.report.json",
]


def build_mandatory_read_receipt() -> dict[str, Any]:
    return {
        "repo_pr_label": "PR134",
        "roadmap_pr": "PR116",
        "branch_verified": "pr134-runtime-resolver-snapshot-executor",
        "head_verified": "78542c7",
        "worktree_clean_before_edits": True,
        "mandatory_files_read": MANDATORY_FILES_READ,
        "pr105_to_pr133_artifacts_inspected": PR105_TO_PR133_ARTIFACTS_INSPECTED,
        "existing_runtime_resolver_surfaces_inspected": True,
        "pr133_snapshot_downstream_handoff_observed": True,
        "pr132_market_data_ingest_handoff_observed": True,
        "pr131_credential_readiness_handoff_observed": True,
        "owner_source_packet_observed": True,
        "roadmap_blueprint_chain_observed": True,
        "atomicrows_authority_artifacts_inspected_without_mutation": True,
        "atomicrows_authority_artifacts_inspected": ATOMICROWS_AUTHORITY_ARTIFACTS_INSPECTED,
        "no_network_commands_run_by_codex": True,
        "no_github_cli_commands_run_by_codex": True,
        "no_live_market_data_fetch_run_by_codex": True,
        "no_venue_api_call_run_by_codex": True,
        "no_credential_resolution_run_by_codex": True,
        "no_live_runtime_execution_run_by_codex": True,
        "no_live_candidate_discovery_run_by_codex": True,
        "no_live_contract_selection_run_by_codex": True,
        "no_replay_paper_live_execution_run_by_codex": True,
        "no_historical_dataset_digest_run_by_codex": True,
        "no_quantum_execution_run_by_codex": True,
        "no_quantum_feature_computation_run_by_codex": True,
        "no_atomicrows_bundle_or_sha_mutation_run_by_codex": True,
        "no_atomicrows_row_materialization_run_by_codex": True,
    }


def build_route_triage_receipt() -> dict[str, Any]:
    return {
        "repo_pr_label": "PR134",
        "authorized_roadmap_pr": "PR116",
        "unauthorized_roadmap_pr_same_number": "PR134",
        "same_number_inference_used": False,
        "implementation_scope": "ROADMAP_PR116_RUNTIME_RESOLVER_SNAPSHOT_EXECUTOR_CONTRACTS",
        "runtime_resolver_snapshot_executor_is_fixture_backed_contract_only": True,
        "fixture_runtime_resolver_snapshot_records_created": True,
        "versioned_candidate_set_snapshot_lock_metadata_created": True,
        "global_candidate_universe_freeze_forbidden": True,
        "future_candidate_additions_allowed_by_new_snapshot_versions": True,
        "replay_paper_input_identity_metadata_created": True,
        "live_candidate_discovery_forbidden": True,
        "live_candidate_import_forbidden": True,
        "live_contract_selection_forbidden": True,
        "live_runtime_resolver_authority_forbidden": True,
        "replay_execution_forbidden": True,
        "paper_execution_forbidden": True,
        "replay_result_forbidden": True,
        "paper_result_forbidden": True,
        "live_trading_forbidden": True,
        "order_authority_forbidden": True,
        "order_execution_forbidden": True,
        "historical_dataset_digest_creation_forbidden": True,
        "feature_vector_creation_forbidden": True,
        "trading_signal_generation_forbidden": True,
        "scoring_ranking_arbitration_output_forbidden": True,
        "live_market_data_fetch_forbidden": True,
        "live_rest_client_forbidden": True,
        "live_websocket_client_forbidden": True,
        "venue_api_calls_forbidden": True,
        "network_io_forbidden": True,
        "credential_provider_calls_forbidden": True,
        "live_credential_resolution_forbidden": True,
        "source_retrieval_forbidden": True,
        "new_source_acceptance_forbidden": True,
        "connector_semantic_binding_creation_forbidden": True,
        "private_state_fetch_forbidden": True,
        "runtime_cash_authority_forbidden": True,
        "quantum_ready_runtime_resolver_snapshot_contract_prepared": True,
        "quantum_execution_forbidden": True,
        "quantum_runtime_feature_computation_forbidden": True,
        "quantum_optimizer_input_creation_forbidden": True,
        "quantum_trading_signal_creation_forbidden": True,
        "quantum_advantage_claim_forbidden": True,
        "atomicrows_pre_bridge_compatibility_metadata_created": True,
        "atomicrows_bridge_recommended_after_pr135": True,
        "atomicrows_bundle_sha_mutation_forbidden": True,
        "atomicrows_row_materialization_forbidden": True,
        "atomicrows_4183_completion_claim_forbidden": True,
        "downstream_prs_preserved": ["PR117"],
    }


def build_pr133_audit_currentization_receipt() -> dict[str, Any]:
    return {
        "repo_pr_label": "PR134",
        "currentized_prior_repo_pr_label": "PR133",
        "github_pr_number": 133,
        "github_pr_title": "PR133 implement orderbook event-state snapshot builder contracts",
        "github_pr_state": "MERGED",
        "github_pr_mergedAt": "2026-05-20T23:36:50Z",
        "github_pr_mergeCommit_oid": "78542c7be9dd8598a9142407cca66d0098d4a32f",
        "github_headRefName": "pr133-orderbook-event-state-snapshot-builder",
        "github_baseRefName": "main",
        "github_url": "https://github.com/Q8Meow/QTT_New0526/pull/133",
        "owner_authorized_roadmap_pr": "PR115",
        "owner_authorized_next_capability": "ORDERBOOK_AND_EVENT_STATE_SNAPSHOT_BUILDER_CONTRACTS",
        "same_number_inference_used": False,
        "identity_doctrine_preserved": True,
        "controller_used_as_record_not_veto": True,
        "next_repo_pr_label": "PR134",
        "next_owner_authorized_roadmap_pr": "PR116",
        "next_implementation_scope": "ROADMAP_PR116_RUNTIME_RESOLVER_SNAPSHOT_EXECUTOR_CONTRACTS",
    }


def _market_specific_section_index(artifacts: dict[str, Any]) -> dict[str, Any]:
    input_locks = artifacts["runtime_resolver_input_locks"]
    snapshots = artifacts["runtime_resolver_snapshots"]
    bindings = artifacts["runtime_resolver_bindings"]
    receipts = artifacts["runtime_resolver_integrity_receipts"]
    compatibility = artifacts["atomicrows_pre_bridge_compatibility"]
    by_scope = {
        "input_locks": {_scope_value(record): record for record in input_locks},
        "snapshots": {_scope_value(record): record for record in snapshots},
        "bindings": {_scope_value(record): record for record in bindings},
        "receipts": {_scope_value(record): record for record in receipts},
        "compatibility": {_scope_value(record): record for record in compatibility},
    }
    venue_entries = []
    for venue_id in policy.STAGE1_VENUE_IDS:
        input_lock = by_scope["input_locks"][venue_id]
        snapshot = by_scope["snapshots"][venue_id]
        binding = by_scope["bindings"][venue_id]
        receipt = by_scope["receipts"][venue_id]
        atomicrows = by_scope["compatibility"][venue_id]
        venue_entries.append(
            {
                "venue_id": venue_id,
                "runtime_resolver_input_lock_ids": [input_lock["input_lock_id"]],
                "runtime_resolver_snapshot_ids": [
                    snapshot["runtime_resolver_snapshot_id"]
                ],
                "runtime_resolver_binding_ids": [binding["binding_id"]],
                "runtime_resolver_integrity_receipt_ids": [
                    receipt["integrity_receipt_id"]
                ],
                "atomicrows_pre_bridge_compatibility_ids": [
                    atomicrows["compatibility_id"]
                ],
                "candidate_set_snapshot_version_ids": [
                    input_lock["candidate_set_snapshot_version_id"]
                ],
                "candidate_set_snapshot_parent_version_ids": [
                    input_lock["candidate_set_snapshot_parent_version_id"]
                ],
                "candidate_scope_lock_refs": [input_lock["candidate_scope_lock_ref"]],
                "future_replay_paper_input_identity_refs": [
                    input_lock["future_replay_paper_input_identity_ref"]
                ],
                "pr133_snapshot_dependency_ids": [
                    input_lock["orderbook_event_state_snapshot_handoff_ref"]
                ],
                "pr132_market_data_ingest_dependency_ids": (
                    input_lock["market_data_ingest_dependency_refs"]
                ),
                "pr131_credential_readiness_dependency_ids": (
                    input_lock["credential_readiness_dependency_refs"]
                ),
                "allowed_runtime_resolver_input_classes": list(
                    policy.ALLOWED_RUNTIME_RESOLVER_INPUT_CLASSES
                ),
                "allowed_runtime_resolver_snapshot_classes": list(
                    policy.ALLOWED_RUNTIME_RESOLVER_SNAPSHOT_CLASSES
                ),
                "allowed_runtime_resolver_readiness_states": list(
                    policy.ALLOWED_RUNTIME_RESOLVER_READINESS_STATES
                ),
                "quantum_ready_runtime_resolver_snapshot_contract": True,
                "atomicrows_pre_bridge_compatibility_metadata_created": True,
                "downstream_pr117_contract_ref": (
                    f"PR117_HISTORICAL_DATASET_DIGEST_CONTRACT_REF::{venue_id}"
                ),
                "no_global_candidate_universe_freeze": True,
                "future_candidate_additions_allowed_by_new_snapshot_versions": True,
                "no_live_candidate_discovery": True,
                "no_live_candidate_import": True,
                "no_live_contract_selection": True,
                "no_exact_live_contract_id_created": True,
                "no_live_market_data_fetch": True,
                "no_rest_client": True,
                "no_websocket_client": True,
                "no_venue_api_call": True,
                "no_network_io": True,
                "no_live_credential_resolution": True,
                "no_private_state_fetch": True,
                "no_live_runtime_resolver_authority": True,
                "no_historical_dataset_digest_created": True,
                "no_feature_vector_created": True,
                "no_trading_signal_created": True,
                "no_ranking_output_created": True,
                "no_replay_execution_created": True,
                "no_paper_execution_created": True,
                "no_replay_result_created": True,
                "no_paper_result_created": True,
                "no_order_authority_created": True,
                "no_quantum_feature_computation_created": True,
                "no_quantum_optimizer_input_created": True,
                "no_quantum_trading_signal_created": True,
                "no_quantum_advantage_claim_created": True,
                "no_atomicrows_bundle_created": True,
                "no_atomicrows_sha_created": True,
                "no_atomicrows_row_records_created": True,
                "no_atomicrows_4183_completion_claim_created": True,
            }
        )
    return {
        "venue_specific_entries": venue_entries,
        "shared_scope_entry": {
            "scope_id": "PREDICTION_MARKETS_GENERAL",
            "scope_type": "SHARED_TAXONOMY_NOT_VENUE",
            "not_counted_as_venue": True,
            "no_venue_api_authority": True,
            "no_live_runtime_resolver_authority": True,
            "no_global_candidate_universe_freeze": True,
            "future_candidate_additions_allowed_by_new_snapshot_versions": True,
            "quantum_ready_runtime_resolver_snapshot_contract": True,
            "atomicrows_pre_bridge_compatibility_metadata_created": True,
            "no_atomicrows_materialization_authority": True,
        },
    }


def _command_action_matrix() -> list[dict[str, Any]]:
    def entry(action_id: str, allowed: bool) -> dict[str, Any]:
        return {
            "action_id": action_id,
            "actor": "CODEX",
            "authority_class": policy.PACKAGE_AUTHORITY_CLASS,
            "input_artifacts": MANDATORY_FILES_READ if action_id.startswith("READ_") else [],
            "output_artifacts": [],
            "allowed": allowed,
            "blocked_reason": None if allowed else "FORBIDDEN_BY_PR134_NO_AUTHORITY_SCOPE",
            "creates_runtime_authority": False,
            "creates_live_authority": False,
            "creates_fixture_runtime_resolver_snapshot": (
                allowed and "RUNTIME_RESOLVER_SNAPSHOT" in action_id
            ),
            "creates_versioned_candidate_set_snapshot_lock_metadata": (
                allowed and "CANDIDATE_SET_SNAPSHOT_LOCK" in action_id
            ),
            "creates_global_candidate_universe_freeze": False,
            "blocks_future_candidate_additions": False,
            "creates_future_replay_paper_input_identity_metadata": (
                allowed and "REPLAY_PAPER_INPUT_IDENTITY" in action_id
            ),
            "creates_live_candidate_discovery": False,
            "creates_live_candidate_import": False,
            "creates_live_contract_selection": False,
            "creates_live_runtime_resolver_authority": False,
            "creates_replay_execution": False,
            "creates_paper_execution": False,
            "creates_replay_result": False,
            "creates_paper_result": False,
            "creates_historical_dataset_digest": False,
            "creates_feature_vector": False,
            "creates_trading_signal": False,
            "creates_ranking_output": False,
            "creates_order_authority": False,
            "creates_profit_evidence": False,
            "creates_quantum_ready_contract_metadata": (
                allowed and "QUANTUM_READY" in action_id
            ),
            "creates_quantum_feature_computation": False,
            "creates_quantum_optimizer_input": False,
            "creates_quantum_trading_signal": False,
            "creates_atomicrows_pre_bridge_metadata": (
                allowed and "ATOMICROWS_PRE_BRIDGE" in action_id
            ),
            "creates_atomicrows_bridge_authority": False,
            "creates_atomicrows_bundle": False,
            "creates_atomicrows_sha": False,
            "creates_atomicrows_row_records": False,
            "creates_atomicrows_4183_completion_claim": False,
            "creates_quantum_execution": False,
        }

    return [entry(action_id, True) for action_id in policy.ALLOWED_ACTION_IDS] + [
        entry(action_id, False) for action_id in policy.BLOCKED_ACTION_IDS
    ]


def build_reports(artifacts: dict[str, Any]) -> dict[str, dict[str, Any]]:
    summary = compute_integrity_summary(
        artifacts["runtime_resolver_input_locks"],
        artifacts["runtime_resolver_snapshots"],
        artifacts["runtime_resolver_bindings"],
        artifacts["orderbook_event_state_snapshot_downstream_handoff"],
        artifacts["atomicrows_pre_bridge_compatibility"],
    )
    base = {
        "schema_version": policy.REPORT_SCHEMA_VERSION,
        "producer_pr": policy.PRODUCER_REPO_PR,
        "producer_roadmap_pr": policy.PRODUCER_ROADMAP_PR,
        "authority_class": policy.PACKAGE_AUTHORITY_CLASS,
    }
    main_report = {
        **base,
        "report_id": "CODEX_PR134_RUNTIME_RESOLVER_SNAPSHOT_EXECUTOR_REPORT",
        "PR134_ROUTE_TRIAGE": build_route_triage_receipt(),
        "PR134_MASTER_PLAN_SECTION_CROSSWALK": {
            "authority_families": [
                "owner source-evidence definitions and non-authority policy",
                "accepted source-evidence and target-field ledger boundary",
                "source revalidation/freshness boundary",
                "connector semantic non-authority boundary",
                "runtime cash/account/private-state non-production boundary",
                "PR131 credential-readiness metadata-only handoff",
                "PR132 market-data ingest adapter contract-only handoff",
                "PR133 orderbook/event-state fixture snapshot contract handoff",
                "PR134 fixture runtime resolver snapshot contract boundary",
                "versioned candidate-set snapshot-lock metadata boundary",
                "future candidate-addition compatibility boundary",
                "replay/paper input identity metadata boundary",
                "historical dataset digest downstream PR117 boundary",
                "replay/paper/live non-execution boundary",
                "post-PR135 AtomicRows bridge-readiness boundary",
                "AtomicRows metadata-only / no-bundle / no-SHA / no-row-materialization boundary",
                "quantum-ready runtime resolver snapshot contract boundary",
                "quantum metadata-only / no-execution boundary",
                "low-latency hot-path exclusion boundary",
            ]
        },
        "PR134_MARKET_SPECIFIC_SECTION_INDEX": _market_specific_section_index(artifacts),
        "PR134_COMMAND_ACTION_MATRIX": _command_action_matrix(),
        "PR134_PR133_SNAPSHOT_DEPENDENCY_EVIDENCE": {
            "handoff_id": policy.PR133_HANDOFF_ID,
            "consumed_as_metadata_only": True,
        },
        "PR134_PR132_MARKET_DATA_INGEST_DEPENDENCY_EVIDENCE": {
            "handoff_id": policy.PR132_MARKET_DATA_HANDOFF_ID,
            "consumed_as_metadata_only": True,
        },
        "PR134_PR131_CREDENTIAL_READINESS_DEPENDENCY_EVIDENCE": {
            "handoff_id": policy.PR131_CREDENTIAL_READINESS_HANDOFF_ID,
            "consumed_as_metadata_only": True,
        },
        "PR134_RUNTIME_RESOLVER_INTEGRITY_EVIDENCE": summary,
        "PR134_RUNTIME_RESOLVER_READINESS_STATE_EVIDENCE": {
            "allowed_runtime_resolver_readiness_states": list(
                policy.ALLOWED_RUNTIME_RESOLVER_READINESS_STATES
            ),
            "ready_metadata_only_not_inferred_with_unresolved_dependencies": True,
            "unresolved_dependency_ready_claim_count": summary[
                "unresolved_dependency_ready_claim_count"
            ],
            "stale_dependency_ready_claim_count": summary[
                "stale_dependency_ready_claim_count"
            ],
            "conflict_dependency_ready_claim_count": summary[
                "conflict_dependency_ready_claim_count"
            ],
            "invalid_readiness_state_count": summary["invalid_readiness_state_count"],
        },
        "PR134_VERSIONED_CANDIDATE_SET_SNAPSHOT_LOCK_EVIDENCE": {
            "candidate_set_snapshot_lock_metadata_created_count": len(
                artifacts["runtime_resolver_snapshots"]
            ),
            "candidate_set_snapshot_is_global_permanent_freeze": False,
            "candidate_set_snapshot_allows_future_versions": True,
            "candidate_set_snapshot_allows_future_candidate_additions": True,
            "candidate_set_snapshot_immutable_for_replay_audit_only": True,
            "global_candidate_universe_freeze_claim_count": summary[
                "global_candidate_universe_freeze_claim_count"
            ],
            "future_candidate_addition_blocked_count": summary[
                "future_candidate_addition_blocked_count"
            ],
        },
        "PR134_FUTURE_CANDIDATE_ADDITION_COMPATIBILITY_EVIDENCE": {
            "future_candidate_additions_allowed_by_new_snapshot_versions": True
        },
        "PR134_REPLAY_PAPER_INPUT_IDENTITY_METADATA_EVIDENCE": {
            "future_replay_paper_input_identity_refs": [
                record["future_replay_paper_input_identity_ref"]
                for record in artifacts["runtime_resolver_input_locks"]
            ],
            "replay_execution_created_count": summary["replay_execution_created_count"],
            "paper_execution_created_count": summary["paper_execution_created_count"],
            "replay_result_created_count": summary["replay_result_created_count"],
            "paper_result_created_count": summary["paper_result_created_count"],
        },
        "PR134_FIXTURE_SYNTHETIC_PAYLOAD_EVIDENCE": {
            "fixture_payload_is_synthetic_count": len(
                artifacts["runtime_resolver_input_locks"]
            )
        },
        "PR134_DOWNSTREAM_PR117_HANDOFF_EVIDENCE": {
            "downstream_prs": list(policy.DOWNSTREAM_PR_IDS),
            "downstream_execution_authorization": False,
        },
        "PR134_LOW_LATENCY_BOUNDARY_EVIDENCE": {
            "precomputed_runtime_resolver_snapshot_contracts_only": True,
            "excluded_from_live_hot_path": True,
            "future_hot_path_consumption_requires_later_authorization": True,
        },
        "PR134_QUANTUM_READY_RUNTIME_RESOLVER_CONTRACT_EVIDENCE": {
            "quantum_ready_runtime_resolver_snapshot_contract_count": len(
                artifacts["runtime_resolver_snapshots"]
            ),
            "metadata_fields": list(policy.QUANTUM_FORWARD_RUNTIME_RESOLVER_METADATA_FIELDS),
        },
        "PR134_QUANTUM_METADATA_ONLY_EVIDENCE": {
            "zero_authority_flags": list(policy.QUANTUM_ZERO_AUTHORITY_FLAGS),
            "quantum_backend_simulator_optimizer_execution_count": summary[
                "quantum_backend_simulator_optimizer_execution_count"
            ],
            "quantum_runtime_feature_computation_count": summary[
                "quantum_runtime_feature_computation_created_count"
            ],
            "quantum_optimizer_input_count": summary[
                "quantum_optimizer_input_created_count"
            ],
            "quantum_trading_signal_count": summary[
                "quantum_trading_signal_created_count"
            ],
            "quantum_advantage_claim_count": summary[
                "quantum_advantage_claim_created_count"
            ],
        },
        "PR134_ATOMICROWS_PRE_BRIDGE_COMPATIBILITY_EVIDENCE": {
            "atomicrows_pre_bridge_compatibility_metadata_created_count": len(
                artifacts["atomicrows_pre_bridge_compatibility"]
            ),
            "metadata_fields": list(policy.ATOMICROWS_PRE_BRIDGE_METADATA_FIELDS),
        },
        "PR134_POST_PR135_ATOMICROWS_BRIDGE_READINESS_HANDOFF": {
            "future_atomicrows_bridge_recommended_after_repo_pr": "PR135",
            "future_atomicrows_bridge_candidate_repo_pr": "PR136",
            "bridge_authority_created": False,
        },
        "PR134_ATOMICROWS_METADATA_ONLY_EVIDENCE": {
            "atomicrows_bundle_consumed_count": summary["atomicrows_bundle_consumed_count"],
            "atomicrows_bundle_created_count": summary["atomicrows_bundle_created_count"],
            "atomicrows_bundle_edited_count": summary["atomicrows_bundle_edited_count"],
            "atomicrows_sha_created_count": summary["atomicrows_sha_created_count"],
            "atomicrows_row_records_created_count": summary[
                "atomicrows_row_records_created_count"
            ],
            "atomicrows_4183_completion_claim_created_count": summary[
                "atomicrows_4183_completion_claim_created_count"
            ],
        },
        "PR134_VALIDATION_EVIDENCE": {
            "validation_passed": not validate_artifacts(artifacts),
            "schema_files": [f"{PACKAGE_DIR}/{file_name}" for file_name in SCHEMA_FILES],
            "fixture_files": [f"{FIXTURE_DIR}/{file_name}" for file_name in NORMAL_FIXTURE_FILES],
        },
    }
    return {
        "main_report": main_report,
        "executor_report": {
            **base,
            "report_id": "RuntimeResolverSnapshotExecutor",
            "runtime_resolver_input_lock_count": len(artifacts["runtime_resolver_input_locks"]),
            "runtime_resolver_snapshot_count": len(artifacts["runtime_resolver_snapshots"]),
            "runtime_resolver_binding_count": len(artifacts["runtime_resolver_bindings"]),
            "fixture_runtime_resolver_snapshot_count": len(
                artifacts["runtime_resolver_snapshots"]
            ),
            "live_runtime_resolver_authority_created_count": summary[
                "live_runtime_authority_created_count"
            ],
        },
        "integrity_report": {
            **base,
            "report_id": "RuntimeResolverSnapshotIntegrity",
            "integrity_summary": summary,
            "runtime_resolver_integrity_receipts": artifacts[
                "runtime_resolver_integrity_receipts"
            ],
        },
        "handoff_report": {
            **base,
            "report_id": "RuntimeResolverSnapshotDownstreamHandoff",
            "runtime_resolver_snapshot_downstream_handoff": artifacts[
                "runtime_resolver_downstream_handoff"
            ],
        },
        "atomicrows_report": {
            **base,
            "report_id": "RuntimeResolverAtomicRowsPreBridgeCompatibility",
            "atomicrows_pre_bridge_compatibility": artifacts[
                "atomicrows_pre_bridge_compatibility"
            ],
            "atomicrows_bundle_created_count": summary["atomicrows_bundle_created_count"],
            "atomicrows_sha_created_count": summary["atomicrows_sha_created_count"],
            "atomicrows_row_records_created_count": summary[
                "atomicrows_row_records_created_count"
            ],
        },
    }


def write_artifacts(
    *,
    repo_root: Path,
    output_root: Path | None = None,
) -> dict[str, Any]:
    target_root = output_root or repo_root
    artifacts = build_runtime_resolver_snapshot_artifacts()
    schema_docs = build_schema_documents(artifacts)
    for file_name, schema_doc in schema_docs.items():
        _write_json(target_root / PACKAGE_DIR / file_name, schema_doc)

    for file_name, artifact_key in NORMAL_FIXTURE_FILES.items():
        _write_json(
            target_root / FIXTURE_DIR / file_name,
            _fixture_wrapper(file_name.replace(".json", "").upper(), artifacts[artifact_key]),
        )
    for file_name, malformed_payload in build_malformed_fixture_payloads().items():
        _write_json(target_root / FIXTURE_DIR / file_name, malformed_payload)

    reports = build_reports(artifacts)
    for file_name, report_key in REPORT_FILES.items():
        _write_json(
            target_root / "docs" / "master_plan" / "source_evidence" / "generated" / file_name,
            reports[report_key],
        )

    receipt_builders = {
        "mandatory_read_receipt": build_mandatory_read_receipt,
        "route_triage_receipt": build_route_triage_receipt,
        "pr133_audit_currentization_receipt": build_pr133_audit_currentization_receipt,
    }
    for file_name, builder_name in ROADMAP_RECEIPT_FILES.items():
        _write_json(
            target_root / "docs" / "roadmap" / "generated" / file_name,
            receipt_builders[builder_name](),
        )
    return artifacts


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=".", type=Path)
    parser.add_argument("--output-root", default=None, type=Path)
    parser.add_argument("--check-only", action="store_true")
    args = parser.parse_args(argv)

    artifacts = (
        build_runtime_resolver_snapshot_artifacts()
        if args.check_only
        else write_artifacts(repo_root=args.repo_root, output_root=args.output_root)
    )
    failures = validate_artifacts(artifacts, repo_root=args.repo_root)
    if failures:
        for failure in failures:
            print(f"{failure.code}: {failure.message} ({failure.artifact_ref})")
        return 1
    print("QTT_RUNTIME_RESOLVER_SNAPSHOT_EXECUTOR_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
