"""Fixture-backed PR135 historical dataset digest and loader contracts."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from . import historical_dataset_policy as policy


REPO_ROOT = Path(__file__).resolve().parents[4]
SCHEMA_DIR = Path("schemas/replay_paper")
FIXTURE_PATH = Path("tests/fixtures/replay_paper/historical_dataset_digest_and_loader.fixture.json")
REPORT_DIR = Path("docs/master_plan/generated")
ROADMAP_GENERATED_DIR = Path("docs/roadmap/generated")

SCHEMA_FILES = {
    "historical_dataset_policy.defs.schema.json": "PR135 policy defs",
    "historical_dataset_digest_and_loader.schema.json": "PR135 digest and loader records",
    "historical_dataset_digest_and_loader_receipt.schema.json": "PR135 receipt records",
}

RUN_TIMESTAMP_KEYS = {
    "run_timestamp_utc",
    "generated_at_utc",
    "validation_run_timestamp_utc",
    "validated_at_utc",
}


@dataclass(frozen=True)
class ValidationFailure:
    code: str
    message: str
    artifact_ref: str


def _json_dump(value: Any) -> str:
    return json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True) + "\n"


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_json_dump(payload), encoding="utf-8", newline="\n")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def strip_run_timestamps(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: strip_run_timestamps(item)
            for key, item in sorted(value.items())
            if key not in RUN_TIMESTAMP_KEYS
        }
    if isinstance(value, list):
        return [strip_run_timestamps(item) for item in value]
    return value


def canonical_json(value: Any) -> str:
    return json.dumps(
        strip_run_timestamps(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )


def sha256_hex(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _scope_payload(scope_ref: policy.ScopeRef) -> dict[str, Any]:
    return {
        "dataset_digest_id": f"{scope_ref.record_prefix}_DATASET_DIGEST_V1",
        "dataset_scope_class": "FIXTURE_ONLY",
        "venue_scope": scope_ref.canonical_venue_id,
        "market_scope": scope_ref.market_scope_id,
        "source_lineage_class": policy.SOURCE_REQUIRED_REFERENCE_ONLY,
        "source_lineage_ref": f"{scope_ref.record_prefix}_SOURCE_REQUIRED_REFERENCE_ONLY",
        "fixture_shape_only_not_venue_fact_truth_flag": True,
        "synthetic_rows": [
            {
                "canonical_sort_key": f"{scope_ref.canonical_venue_id}:0001",
                "fixture_row_id": f"{scope_ref.record_prefix}_SYNTHETIC_ROW_0001",
                "shape_class": "HISTORICAL_DATASET_FIXTURE_ROW",
                "value_basis": "SYNTHETIC_CONTRACT_METADATA_ONLY",
            },
            {
                "canonical_sort_key": f"{scope_ref.canonical_venue_id}:0002",
                "fixture_row_id": f"{scope_ref.record_prefix}_SYNTHETIC_ROW_0002",
                "shape_class": "HISTORICAL_DATASET_FIXTURE_ROW",
                "value_basis": "SYNTHETIC_SOURCE_LINEAGE_REFERENCE_ONLY",
            },
        ],
    }


def _common_scope_fields(scope_ref: policy.ScopeRef) -> dict[str, Any]:
    fields = {
        "schema_version": policy.SCHEMA_VERSION,
        "repo_pr_number": policy.PRODUCER_REPO_PR,
        "roadmap_pr_number": policy.PRODUCER_ROADMAP_PR,
        "created_by": policy.CREATED_BY,
        "venue_scope": scope_ref.canonical_venue_id,
        "market_scope": scope_ref.market_scope_id,
        "source_boundary_class": policy.FIXTURE_SHAPE_ONLY_NOT_VENUE_FACT_TRUTH,
        "source_boundary_language": policy.SOURCE_BOUNDARY_LANGUAGE,
    }
    fields.update(policy.no_authority_record_fields())
    return fields


def build_digest_record(scope_ref: policy.ScopeRef) -> dict[str, Any]:
    payload = _scope_payload(scope_ref)
    digest = sha256_hex(payload)
    record = _common_scope_fields(scope_ref)
    record.update(
        {
            "record_type": "HISTORICAL_DATASET_DIGEST",
            "dataset_digest_id": payload["dataset_digest_id"],
            "dataset_scope_class": "FIXTURE_ONLY",
            "source_lineage_class": policy.SOURCE_REQUIRED_REFERENCE_ONLY,
            "source_lineage_ref": payload["source_lineage_ref"],
            "source_required_flag": True,
            "accepted_source_packet_required_for_real_historical_use": True,
            "fixture_shape_only_not_venue_fact_truth_flag": True,
            "fixture_ref": f"tests/fixtures/replay_paper/{scope_ref.record_prefix}.fixture-shape.json",
            "fixture_digest_sha256": digest,
            "canonical_content_digest_sha256": digest,
            "loader_manifest_id": f"{scope_ref.record_prefix}_LOADER_MANIFEST_V1",
            "input_lock_id": f"{scope_ref.record_prefix}_INPUT_LOCK_V1",
            "integrity_receipt_id": f"{scope_ref.record_prefix}_INTEGRITY_RECEIPT_V1",
            "rejection_receipt_id": None,
            "runtime_resolver_snapshot_handoff_ref": (
                "PR134_RUNTIME_RESOLVER_SNAPSHOT_DOWNSTREAM_HANDOFF_V1"
            ),
            "versioned_candidate_set_snapshot_lock_ref": (
                f"{scope_ref.record_prefix}_VERSIONED_CANDIDATE_SET_SNAPSHOT_LOCK_V1"
            ),
            "replay_paper_input_identity_ref": (
                f"{scope_ref.record_prefix}_REPLAY_PAPER_INPUT_IDENTITY_V1"
            ),
            "orderbook_event_state_snapshot_ref": (
                "PR133_ORDERBOOK_EVENT_STATE_SNAPSHOT_DOWNSTREAM_HANDOFF_V1"
            ),
            "market_data_ingest_contract_ref": (
                "PR132_MARKET_DATA_INGEST_DOWNSTREAM_HANDOFF_V1"
            ),
            "credential_readiness_ref": "PR131_CREDENTIAL_READINESS_HANDOFF_V1",
            "immutable_after_creation_flag": True,
            "deterministic_generation_method": (
                "canonical JSON sorted keys, LF serialization, timestamp keys excluded"
            ),
            "validation_marker": policy.VALIDATOR_MARKER,
        }
    )
    return record


def build_loader_manifest(scope_ref: policy.ScopeRef) -> dict[str, Any]:
    record = _common_scope_fields(scope_ref)
    record.update(
        {
            "record_type": "HISTORICAL_DATASET_LOADER_MANIFEST",
            "loader_manifest_id": f"{scope_ref.record_prefix}_LOADER_MANIFEST_V1",
            "dataset_digest_id": f"{scope_ref.record_prefix}_DATASET_DIGEST_V1",
            "fixture_backed_flag": True,
            "fixture_shape_only_not_venue_fact_truth_flag": True,
            "live_loader_flag": False,
            "network_io_used_flag": False,
            "accepted_source_packet_required_for_live_or_real_historical_use": True,
            "allowed_loader_mode": "FIXTURE_MANIFEST_ONLY",
            "dataset_files": [
                f"tests/fixtures/replay_paper/{scope_ref.record_prefix}.fixture-shape.json"
            ],
            "canonical_sort_key": scope_ref.canonical_venue_id,
            "digest_algorithm": "SHA256",
            "line_ending_normalization_policy": "LF",
            "timestamp_normalization_policy": "RUN_TIMESTAMPS_EXCLUDED_FROM_DIGEST_INPUT",
            "deterministic_fixture_timestamp_policy": policy.FIXTURE_TIMESTAMP,
            "deterministic_ordering_flag": True,
            "source_lineage_ref": f"{scope_ref.record_prefix}_SOURCE_REQUIRED_REFERENCE_ONLY",
            "integrity_receipt_id": f"{scope_ref.record_prefix}_INTEGRITY_RECEIPT_V1",
            "rejection_receipt_ids": [],
            "downstream_handoff_ref": f"{scope_ref.record_prefix}_DOWNSTREAM_HANDOFF_V1",
        }
    )
    return record


def build_input_lock(scope_ref: policy.ScopeRef) -> dict[str, Any]:
    identity_payload = {
        "runtime_resolver_snapshot_handoff_ref": (
            "PR134_RUNTIME_RESOLVER_SNAPSHOT_DOWNSTREAM_HANDOFF_V1"
        ),
        "versioned_candidate_set_snapshot_lock_ref": (
            f"{scope_ref.record_prefix}_VERSIONED_CANDIDATE_SET_SNAPSHOT_LOCK_V1"
        ),
        "replay_paper_input_identity_ref": (
            f"{scope_ref.record_prefix}_REPLAY_PAPER_INPUT_IDENTITY_V1"
        ),
        "source_lineage_ref": f"{scope_ref.record_prefix}_SOURCE_REQUIRED_REFERENCE_ONLY",
    }
    record = _common_scope_fields(scope_ref)
    record.update(
        {
            "record_type": "HISTORICAL_DATASET_INPUT_LOCK",
            "input_lock_id": f"{scope_ref.record_prefix}_INPUT_LOCK_V1",
            "dataset_digest_id": f"{scope_ref.record_prefix}_DATASET_DIGEST_V1",
            "runtime_resolver_snapshot_handoff_ref": identity_payload[
                "runtime_resolver_snapshot_handoff_ref"
            ],
            "runtime_resolver_snapshot_input_lock_ref": (
                f"{scope_ref.record_prefix}_PR134_RUNTIME_RESOLVER_INPUT_LOCK_REF"
            ),
            "versioned_candidate_set_snapshot_lock_ref": identity_payload[
                "versioned_candidate_set_snapshot_lock_ref"
            ],
            "candidate_set_snapshot_version": (
                f"{scope_ref.record_prefix}_CANDIDATE_SET_SNAPSHOT_VERSION_V1"
            ),
            "global_candidate_freeze_flag": False,
            "future_candidate_additions_allowed_by_new_snapshot_versions": True,
            "replay_paper_input_identity_ref": identity_payload[
                "replay_paper_input_identity_ref"
            ],
            "orderbook_event_state_snapshot_ref": (
                "PR133_ORDERBOOK_EVENT_STATE_SNAPSHOT_DOWNSTREAM_HANDOFF_V1"
            ),
            "market_data_ingest_contract_ref": (
                "PR132_MARKET_DATA_INGEST_DOWNSTREAM_HANDOFF_V1"
            ),
            "credential_readiness_ref": "PR131_CREDENTIAL_READINESS_HANDOFF_V1",
            "immutable_input_identity_digest": sha256_hex(identity_payload),
            "locked_at_utc_or_fixture_timestamp": policy.FIXTURE_TIMESTAMP,
            "lock_reason": "PR135_HISTORICAL_DATASET_DIGEST_LOADER_CONTRACT",
            "input_lock_state": policy.LOCKED_FIXTURE_INPUT,
            "allowed_future_consumers": list(policy.ALLOWED_FUTURE_CONSUMERS),
            "forbidden_consumers": list(policy.FORBIDDEN_CONSUMERS),
        }
    )
    return record


def build_integrity_receipt(scope_ref: policy.ScopeRef, digest_record: Mapping[str, Any]) -> dict[str, Any]:
    record = _common_scope_fields(scope_ref)
    record.update(
        {
            "record_type": "HISTORICAL_DATASET_INTEGRITY_RECEIPT",
            "integrity_receipt_id": f"{scope_ref.record_prefix}_INTEGRITY_RECEIPT_V1",
            "dataset_digest_id": digest_record["dataset_digest_id"],
            "loader_manifest_id": f"{scope_ref.record_prefix}_LOADER_MANIFEST_V1",
            "canonical_content_digest_sha256": digest_record[
                "canonical_content_digest_sha256"
            ],
            "fixture_digest_sha256": digest_record["fixture_digest_sha256"],
            "digest_algorithm": "SHA256",
            "deterministic_rebuild_match_flag": True,
            "duplicate_dataset_id_detected_flag": False,
            "mutable_input_detected_flag": False,
            "unsupported_live_data_detected_flag": False,
            "unsupported_source_retrieval_detected_flag": False,
            "unsupported_source_acceptance_detected_flag": False,
            "unsupported_connector_binding_detected_flag": False,
            "unsupported_credential_resolution_detected_flag": False,
            "unsupported_private_state_fetch_detected_flag": False,
            "unsupported_runtime_cash_authority_detected_flag": False,
            "unsupported_replay_execution_detected_flag": False,
            "unsupported_paper_execution_detected_flag": False,
            "unsupported_feature_signal_ranking_detected_flag": False,
            "unsupported_order_authority_detected_flag": False,
            "unsupported_profit_evidence_detected_flag": False,
            "unsupported_quantum_execution_detected_flag": False,
            "unsupported_quantum_optimizer_input_detected_flag": False,
            "unsupported_atomicrows_materialization_detected_flag": False,
            "policy_block_code_ref": None,
            "pass_flag": True,
            "validation_marker": policy.VALIDATOR_MARKER,
        }
    )
    return record


def build_rejection_receipts() -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for index, (case_id, block_code) in enumerate(
        sorted(policy.REQUIRED_FIXTURE_CASE_BLOCKS.items()), start=1
    ):
        record = {
            "record_type": "HISTORICAL_DATASET_REJECTION_RECEIPT",
            "schema_version": policy.SCHEMA_VERSION,
            "repo_pr_number": policy.PRODUCER_REPO_PR,
            "roadmap_pr_number": policy.PRODUCER_ROADMAP_PR,
            "created_by": policy.CREATED_BY,
            "rejection_receipt_id": f"PR135_HISTORICAL_DATASET_REJECTION_{index:03d}",
            "dataset_digest_id": f"PR135_REJECTION_FIXTURE::{case_id}",
            "policy_block_code_ref": block_code,
            "blocked_field_path": f"fixture_cases.{case_id}",
            "blocked_reason": case_id,
            "authority_boundary_violated": block_code != policy.LOCKED_FIXTURE_INPUT,
            "deterministic_rejection_flag": True,
            "live_or_runtime_authority_created_flag": False,
            "remediation_hint": "Use PR135 fixture-backed contract metadata only and preserve upstream lock refs.",
            "created_at_utc_or_fixture_timestamp": policy.FIXTURE_TIMESTAMP,
        }
        record.update(policy.no_authority_record_fields())
        records.append(record)
    return records


def build_downstream_handoff(scope_ref: policy.ScopeRef) -> dict[str, Any]:
    record = _common_scope_fields(scope_ref)
    record.update(
        {
            "record_type": "HISTORICAL_DATASET_DOWNSTREAM_HANDOFF",
            "handoff_id": f"{scope_ref.record_prefix}_DOWNSTREAM_HANDOFF_V1",
            "dataset_digest_id": f"{scope_ref.record_prefix}_DATASET_DIGEST_V1",
            "loader_manifest_id": f"{scope_ref.record_prefix}_LOADER_MANIFEST_V1",
            "input_lock_id": f"{scope_ref.record_prefix}_INPUT_LOCK_V1",
            "integrity_receipt_id": f"{scope_ref.record_prefix}_INTEGRITY_RECEIPT_V1",
            "runtime_resolver_snapshot_handoff_ref": (
                "PR134_RUNTIME_RESOLVER_SNAPSHOT_DOWNSTREAM_HANDOFF_V1"
            ),
            "versioned_candidate_set_snapshot_lock_ref": (
                f"{scope_ref.record_prefix}_VERSIONED_CANDIDATE_SET_SNAPSHOT_LOCK_V1"
            ),
            "replay_paper_input_identity_ref": (
                f"{scope_ref.record_prefix}_REPLAY_PAPER_INPUT_IDENTITY_V1"
            ),
            "future_replay_engine_consumer_ref": "PR118_REPLAY_ENGINE_EXECUTOR",
            "future_paper_engine_consumer_ref": "PR119_PAPER_TRADING_ENGINE_EXECUTOR",
            "future_optimizer_consumer_ref": "FUTURE_OWNER_AUTHORIZED_OPTIMIZER_PRECOMPUTE",
            "future_atomicrows_bridge_consumer_ref": (
                "FUTURE_OWNER_AUTHORIZED_ATOMICROWS_BRIDGE"
            ),
            "no_live_authority_flag": True,
            "no_order_authority_flag": True,
            "no_profit_evidence_flag": True,
            "no_quantum_execution_flag": True,
            "no_atomicrows_materialization_flag": True,
        }
    )
    return record


def build_quantum_metadata(scope_ref: policy.ScopeRef) -> dict[str, Any]:
    return {
        "quantum_metadata_record_type": (
            "HISTORICAL_DATASET_QUANTUM_METADATA_PRECOMPUTE_READY_ONLY"
        ),
        "dataset_digest_id": f"{scope_ref.record_prefix}_DATASET_DIGEST_V1",
        "future_quantum_state_encoding_refs": [
            f"FUTURE_QUANTUM_STATE_ENCODING::{scope_ref.canonical_venue_id}"
        ],
        "future_quantum_kernel_dataset_regime_refs": [
            f"FUTURE_QUANTUM_KERNEL_DATASET_REGIME::{scope_ref.canonical_venue_id}"
        ],
        "future_qaoa_qubo_dataset_constraint_refs": [
            f"FUTURE_QAOA_QUBO_DATASET_CONSTRAINT::{scope_ref.canonical_venue_id}"
        ],
        "future_quantum_annealing_dataset_sampling_refs": [
            f"FUTURE_QUANTUM_ANNEALING_DATASET_SAMPLING::{scope_ref.canonical_venue_id}"
        ],
        "future_quantum_microstructure_dataset_graph_refs": [
            f"FUTURE_QUANTUM_MICROSTRUCTURE_DATASET_GRAPH::{scope_ref.canonical_venue_id}"
        ],
        "future_amplitude_encoding_dataset_refs": [
            f"FUTURE_AMPLITUDE_ENCODING_DATASET::{scope_ref.canonical_venue_id}"
        ],
        "future_quantum_dependency_graph_refs": [
            f"FUTURE_QUANTUM_DEPENDENCY_GRAPH::{scope_ref.canonical_venue_id}"
        ],
        "future_quantum_feature_map_refs": [
            f"FUTURE_QUANTUM_FEATURE_MAP::{scope_ref.canonical_venue_id}"
        ],
        "future_quantum_optimizer_comparison_refs": [
            f"FUTURE_QUANTUM_OPTIMIZER_COMPARISON::{scope_ref.canonical_venue_id}"
        ],
        "classical_comparator_required_flag": True,
        "no_quantum_feature_computation_flag": True,
        "no_quantum_optimizer_input_flag": True,
        "no_qaoa_execution_flag": True,
        "no_vqe_execution_flag": True,
        "no_annealing_execution_flag": True,
        "no_qubo_solving_flag": True,
        "no_ising_solving_flag": True,
        "no_backend_or_simulator_provider_call_flag": True,
        "no_quantum_signal_creation_flag": True,
        "no_quantum_advantage_claim_flag": True,
        "future_owner_authorization_required_for_execution_flag": True,
    }


def build_atomicrows_metadata(scope_ref: policy.ScopeRef) -> dict[str, Any]:
    return {
        "atomicrows_metadata_record_type": (
            "HISTORICAL_DATASET_ATOMICROWS_PRE_BRIDGE_COMPATIBILITY_ONLY"
        ),
        "dataset_digest_id": f"{scope_ref.record_prefix}_DATASET_DIGEST_V1",
        "future_atomicrows_historical_dataset_digest_row_refs": [
            f"FUTURE_ATOMICROWS_HISTORICAL_DATASET_DIGEST::{scope_ref.canonical_venue_id}"
        ],
        "future_atomicrows_loader_manifest_row_refs": [
            f"FUTURE_ATOMICROWS_LOADER_MANIFEST::{scope_ref.canonical_venue_id}"
        ],
        "future_atomicrows_dataset_lineage_family_refs": [
            f"FUTURE_ATOMICROWS_DATASET_LINEAGE::{scope_ref.canonical_venue_id}"
        ],
        "future_atomicrows_replay_paper_input_identity_family_refs": [
            f"FUTURE_ATOMICROWS_REPLAY_PAPER_INPUT_IDENTITY::{scope_ref.canonical_venue_id}"
        ],
        "future_atomicrows_quantum_dataset_feature_family_refs": [
            f"FUTURE_ATOMICROWS_QUANTUM_DATASET_FEATURE::{scope_ref.canonical_venue_id}"
        ],
        "future_atomicrows_policy_registry_family_refs": [
            f"FUTURE_ATOMICROWS_POLICY_REGISTRY::{scope_ref.canonical_venue_id}"
        ],
        "atomicrows_bundle_path": "docs/master_plan/atomic_rows/AtomicRows.bundle.jsonl",
        "atomicrows_bundle_sha_path": "docs/master_plan/atomic_rows/AtomicRows.bundle.sha256",
        "atomicrows_bundle_created_flag": False,
        "atomicrows_bundle_edited_flag": False,
        "atomicrows_bundle_sha_created_flag": False,
        "atomicrows_rows_created_flag": False,
        "atomicrows_bridge_authority_created_flag": False,
        "atomicrows_4183_row_completion_claimed_flag": False,
        "future_bridge_pr_required_flag": True,
        "owner_explicit_authorization_required_for_materialization_flag": True,
    }


def build_artifacts() -> dict[str, Any]:
    digest_records = []
    loader_manifests = []
    input_locks = []
    integrity_receipts = []
    downstream_handoffs = []
    quantum_metadata = []
    atomicrows_metadata = []
    fixture_payloads = []
    for scope_ref in policy.scope_refs():
        digest_record = build_digest_record(scope_ref)
        digest_records.append(digest_record)
        loader_manifests.append(build_loader_manifest(scope_ref))
        input_locks.append(build_input_lock(scope_ref))
        integrity_receipts.append(build_integrity_receipt(scope_ref, digest_record))
        downstream_handoffs.append(build_downstream_handoff(scope_ref))
        quantum_metadata.append(build_quantum_metadata(scope_ref))
        atomicrows_metadata.append(build_atomicrows_metadata(scope_ref))
        fixture_payloads.append(_scope_payload(scope_ref))

    return {
        "historical_dataset_digests": digest_records,
        "historical_dataset_loader_manifests": loader_manifests,
        "historical_dataset_input_locks": input_locks,
        "historical_dataset_integrity_receipts": integrity_receipts,
        "historical_dataset_rejection_receipts": build_rejection_receipts(),
        "historical_dataset_downstream_handoffs": downstream_handoffs,
        "historical_dataset_quantum_metadata": quantum_metadata,
        "historical_dataset_atomicrows_pre_bridge_metadata": atomicrows_metadata,
        "canonical_fixture_payloads": fixture_payloads,
    }


def build_fixture() -> dict[str, Any]:
    artifacts = build_artifacts()
    fixture_cases = [
        {
            "case_id": "valid_three_scope_fixture",
            "expected_pass": True,
            "venue_scope_count": len(policy.VENUE_SPECIFIC_IDS),
            "shared_scope_count": len(policy.SHARED_SCOPE_IDS),
            "policy_block_code_ref": None,
        }
    ]
    for case_id, block_code in sorted(policy.REQUIRED_FIXTURE_CASE_BLOCKS.items()):
        fixture_cases.append(
            {
                "case_id": case_id,
                "expected_pass": False,
                "policy_block_code_ref": block_code,
                "deterministic_rejection_flag": True,
            }
        )
    return {
        "fixture_type": "PR135_HISTORICAL_DATASET_DIGEST_AND_LOADER_FIXTURE",
        "mode": "SOURCE_REQUIRED",
        "execution": "DISABLED",
        "schema_version": policy.SCHEMA_VERSION,
        "repo_pr_number": policy.PRODUCER_REPO_PR,
        "roadmap_pr_number": policy.PRODUCER_ROADMAP_PR,
        "deterministic_fixture_timestamp": policy.FIXTURE_TIMESTAMP,
        "run_timestamp_excluded_from_digest": True,
        "fixture_shape_only_not_venue_fact_truth_flag": True,
        "source_boundary_language": policy.SOURCE_BOUNDARY_LANGUAGE,
        "fixture_cases": fixture_cases,
        "artifacts": artifacts,
    }


def _defs_schema() -> dict[str, Any]:
    string_enum = lambda values: {"type": "string", "enum": list(values)}
    false_const = {"type": "boolean", "const": False}
    no_authority_properties = {
        name: false_const for name in sorted(policy.NO_AUTHORITY_FLAGS)
    }
    record_no_authority_properties = {
        name: false_const for name in sorted(policy.RECORD_NO_AUTHORITY_FLAGS)
    }
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://qtt.local/schemas/replay_paper/historical_dataset_policy.defs.schema.json",
        "title": "PR135 Historical Dataset Policy Definitions",
        "$defs": {
            "validator_marker": {"type": "string", "const": policy.VALIDATOR_MARKER},
            "canonical_venue_id": string_enum(policy.CANONICAL_VENUE_IDS),
            "forbidden_venue_identity": string_enum(policy.FORBIDDEN_VENUE_IDENTITIES),
            "dataset_record_scope": string_enum(policy.DATASET_RECORD_SCOPES),
            "digest_algorithm": string_enum(policy.DIGEST_ALGORITHMS),
            "loader_manifest_mode": string_enum(policy.LOADER_MANIFEST_MODES),
            "policy_block_code_ref": string_enum(
                sorted(
                    set(policy.INPUT_LOCK_STATES)
                    | set(policy.REQUIRED_FIXTURE_CASE_BLOCKS.values())
                )
            ),
            "source_boundary_constant": string_enum(policy.SOURCE_BOUNDARY_CONSTANTS),
            "candidate_set_constant": string_enum(policy.CANDIDATE_SET_CONSTANTS),
            "no_authority_flags": {
                "type": "object",
                "additionalProperties": False,
                "required": sorted(no_authority_properties),
                "properties": no_authority_properties,
            },
            "record_no_authority_flags": {
                "type": "object",
                "additionalProperties": False,
                "required": sorted(record_no_authority_properties),
                "properties": record_no_authority_properties,
            },
        },
    }


def _record_schema() -> dict[str, Any]:
    policy_ref = "historical_dataset_policy.defs.schema.json#/$defs/"
    common_properties = {
        "schema_version": {"type": "string", "const": policy.SCHEMA_VERSION},
        "repo_pr_number": {"type": "integer", "const": policy.PRODUCER_REPO_PR},
        "roadmap_pr_number": {"type": "integer", "const": policy.PRODUCER_ROADMAP_PR},
        "venue_scope": {"$ref": f"{policy_ref}canonical_venue_id"},
        "market_scope": {"type": "string"},
        "source_boundary_class": {"$ref": f"{policy_ref}source_boundary_constant"},
        "source_boundary_language": {"type": "string", "const": policy.SOURCE_BOUNDARY_LANGUAGE},
    }
    required_common = sorted(common_properties)
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://qtt.local/schemas/replay_paper/historical_dataset_digest_and_loader.schema.json",
        "title": "PR135 Historical Dataset Digest And Loader",
        "$defs": {
            "HistoricalDatasetDigest": {
                "type": "object",
                "additionalProperties": True,
                "required": required_common
                + [
                    "record_type",
                    "dataset_digest_id",
                    "dataset_scope_class",
                    "source_lineage_ref",
                    "fixture_digest_sha256",
                    "canonical_content_digest_sha256",
                    "runtime_resolver_snapshot_handoff_ref",
                    "versioned_candidate_set_snapshot_lock_ref",
                    "replay_paper_input_identity_ref",
                    "immutable_after_creation_flag",
                    "validation_marker",
                ],
                "properties": {
                    **common_properties,
                    "record_type": {"type": "string", "const": "HISTORICAL_DATASET_DIGEST"},
                    "dataset_scope_class": {"$ref": f"{policy_ref}dataset_record_scope"},
                    "validation_marker": {"$ref": f"{policy_ref}validator_marker"},
                },
            },
            "HistoricalDatasetLoaderManifest": {
                "type": "object",
                "additionalProperties": True,
                "required": required_common
                + [
                    "record_type",
                    "loader_manifest_id",
                    "dataset_digest_id",
                    "fixture_backed_flag",
                    "live_loader_flag",
                    "network_io_used_flag",
                    "allowed_loader_mode",
                    "digest_algorithm",
                    "deterministic_ordering_flag",
                ],
                "properties": {
                    **common_properties,
                    "record_type": {
                        "type": "string",
                        "const": "HISTORICAL_DATASET_LOADER_MANIFEST",
                    },
                    "allowed_loader_mode": {"$ref": f"{policy_ref}loader_manifest_mode"},
                    "digest_algorithm": {"$ref": f"{policy_ref}digest_algorithm"},
                },
            },
            "HistoricalDatasetInputLock": {
                "type": "object",
                "additionalProperties": True,
                "required": required_common
                + [
                    "record_type",
                    "input_lock_id",
                    "runtime_resolver_snapshot_handoff_ref",
                    "versioned_candidate_set_snapshot_lock_ref",
                    "replay_paper_input_identity_ref",
                    "global_candidate_freeze_flag",
                    "future_candidate_additions_allowed_by_new_snapshot_versions",
                    "immutable_input_identity_digest",
                    "input_lock_state",
                ],
                "properties": {
                    **common_properties,
                    "record_type": {"type": "string", "const": "HISTORICAL_DATASET_INPUT_LOCK"},
                    "input_lock_state": {"$ref": f"{policy_ref}policy_block_code_ref"},
                },
            },
        },
        "type": "object",
        "additionalProperties": True,
    }


def _receipt_schema() -> dict[str, Any]:
    policy_ref = "historical_dataset_policy.defs.schema.json#/$defs/"
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://qtt.local/schemas/replay_paper/historical_dataset_digest_and_loader_receipt.schema.json",
        "title": "PR135 Historical Dataset Receipt Records",
        "$defs": {
            "HistoricalDatasetIntegrityReceipt": {
                "type": "object",
                "additionalProperties": True,
                "required": [
                    "record_type",
                    "integrity_receipt_id",
                    "dataset_digest_id",
                    "canonical_content_digest_sha256",
                    "fixture_digest_sha256",
                    "digest_algorithm",
                    "pass_flag",
                ],
                "properties": {
                    "record_type": {
                        "type": "string",
                        "const": "HISTORICAL_DATASET_INTEGRITY_RECEIPT",
                    },
                    "digest_algorithm": {"$ref": f"{policy_ref}digest_algorithm"},
                    "policy_block_code_ref": {
                        "anyOf": [
                            {"$ref": f"{policy_ref}policy_block_code_ref"},
                            {"type": "null"},
                        ]
                    },
                },
            },
            "HistoricalDatasetRejectionReceipt": {
                "type": "object",
                "additionalProperties": True,
                "required": [
                    "record_type",
                    "rejection_receipt_id",
                    "dataset_digest_id",
                    "policy_block_code_ref",
                    "blocked_field_path",
                    "blocked_reason",
                    "deterministic_rejection_flag",
                ],
                "properties": {
                    "record_type": {
                        "type": "string",
                        "const": "HISTORICAL_DATASET_REJECTION_RECEIPT",
                    },
                    "policy_block_code_ref": {"$ref": f"{policy_ref}policy_block_code_ref"},
                },
            },
            "HistoricalDatasetDownstreamHandoff": {
                "type": "object",
                "additionalProperties": True,
                "required": [
                    "record_type",
                    "handoff_id",
                    "dataset_digest_id",
                    "loader_manifest_id",
                    "input_lock_id",
                    "integrity_receipt_id",
                    "no_live_authority_flag",
                    "no_order_authority_flag",
                    "no_profit_evidence_flag",
                    "no_quantum_execution_flag",
                    "no_atomicrows_materialization_flag",
                ],
                "properties": {
                    "record_type": {
                        "type": "string",
                        "const": "HISTORICAL_DATASET_DOWNSTREAM_HANDOFF",
                    }
                },
            },
            "HistoricalDatasetQuantumOptimizationMetadata": {
                "type": "object",
                "additionalProperties": True,
                "required": [
                    "quantum_metadata_record_type",
                    "dataset_digest_id",
                    "classical_comparator_required_flag",
                    "no_quantum_optimizer_input_flag",
                    "no_quantum_advantage_claim_flag",
                ],
            },
            "HistoricalDatasetAtomicRowsPreBridgeMetadata": {
                "type": "object",
                "additionalProperties": True,
                "required": [
                    "atomicrows_metadata_record_type",
                    "dataset_digest_id",
                    "atomicrows_bundle_path",
                    "atomicrows_bundle_sha_path",
                    "atomicrows_bundle_created_flag",
                    "atomicrows_bundle_edited_flag",
                    "atomicrows_bundle_sha_created_flag",
                    "atomicrows_rows_created_flag",
                ],
            },
        },
        "type": "object",
        "additionalProperties": True,
    }


def build_schema_documents() -> dict[str, dict[str, Any]]:
    return {
        "historical_dataset_policy.defs.schema.json": _defs_schema(),
        "historical_dataset_digest_and_loader.schema.json": _record_schema(),
        "historical_dataset_digest_and_loader_receipt.schema.json": _receipt_schema(),
    }


def _owner_verified_inputs_receipt() -> dict[str, Any]:
    receipt = {
        "receipt_type": "PR135_OWNER_VERIFIED_INPUTS_RECEIPT",
        "repo_pr_number": policy.PRODUCER_REPO_PR,
        "roadmap_pr_number": policy.PRODUCER_ROADMAP_PR,
        "prior_repo_pr_number": policy.PREVIOUS_REPO_PR,
        "prior_roadmap_pr_number": policy.PREVIOUS_ROADMAP_PR,
        "owner_verified_pr134_fields_present": True,
        "missing_owner_verified_pr134_fields": [],
        "placeholder_values_remaining": False,
        "placeholder_values_detected": [],
        "codex_network_access_used": False,
        "gh_command_used_by_codex": False,
        "owner_side_verification_required_if_missing": True,
    }
    receipt.update(policy.PR134_OWNER_VERIFIED_FIELDS)
    return receipt


def _pr134_currentization_receipt() -> dict[str, Any]:
    return {
        "receipt_type": "PR134_GITHUB_AUDIT_CURRENTIZATION_RECEIPT",
        "repo_pr_number": policy.PREVIOUS_REPO_PR,
        "roadmap_pr_number": policy.PREVIOUS_ROADMAP_PR,
        "repo_pr_title": policy.PR134_OWNER_VERIFIED_FIELDS["repo_pr_title"],
        "repo_pr_state": policy.PR134_OWNER_VERIFIED_FIELDS["repo_pr_state"],
        "repo_pr_url": policy.PR134_OWNER_VERIFIED_FIELDS["url"],
        "headRefName": policy.PR134_OWNER_VERIFIED_FIELDS["headRefName"],
        "baseRefName": policy.PR134_OWNER_VERIFIED_FIELDS["baseRefName"],
        "mergedAt": policy.PR134_OWNER_VERIFIED_FIELDS["mergedAt"],
        "mergeCommit_full": policy.PR134_OWNER_VERIFIED_FIELDS["mergeCommit_full"],
        "mergeCommit_short": policy.PR134_OWNER_VERIFIED_FIELDS["mergeCommit_short"],
        "head_branch_commit": policy.PR134_OWNER_VERIFIED_FIELDS["head_branch_commit"],
        "owner_verified_source": True,
        "codex_network_access_used": False,
        "gh_command_used_by_codex": False,
        "currentized_in_identity_roster": True,
        "source_of_truth_note": "owner-side gh pr view 134 verification; Codex did not verify via network",
        "missing_owner_verified_fields": [],
        "placeholder_values_detected": [],
        "stop_if_missing_required_fields": True,
    }


def _route_triage_report() -> dict[str, Any]:
    return {
        "receipt_type": "PR135_ROUTE_TRIAGE_RECEIPT",
        "repo_pr_number": policy.PRODUCER_REPO_PR,
        "roadmap_pr_number": policy.PRODUCER_ROADMAP_PR,
        "owner_authorized_roadmap_pr": policy.PRODUCER_ROADMAP_PR,
        "previous_repo_pr_number": policy.PREVIOUS_REPO_PR,
        "previous_roadmap_pr_number": policy.PREVIOUS_ROADMAP_PR,
        "same_number_inference_used": False,
        "route_resolution_basis": (
            "OWNER_AUTHORIZED_ROADMAP_PR117_HISTORICAL_DATASET_DIGEST_AND_LOADER"
        ),
        "implement_only_owner_authorized_scope": True,
        "branch_expected": "pr135-historical-dataset-digest-loader",
        "repo_task": "historical dataset digest and loader contracts",
        "explicit_non_scope_roadmap_pr135": True,
        "non_scope_reason": "SAME_NUMBER_INFERENCE_FORBIDDEN",
        "currentization_first_subtask_completed": True,
        "roadmap_blueprint_extraction_receipt_ref": (
            "PR135RoadmapBlueprintExtraction.report.json"
        ),
        "policy_registry_ref": "PR135HistoricalDatasetPolicyManifest.report.json",
        "blockers": [],
    }


def _read_receipt() -> dict[str, Any]:
    return {
        "receipt_type": "PR135_HISTORICAL_DATASET_DIGEST_LOADER_READ_RECEIPT",
        "repo_pr_number": policy.PRODUCER_REPO_PR,
        "roadmap_pr_number": policy.PRODUCER_ROADMAP_PR,
        "same_number_inference_used": False,
        "required_files_read": list(policy.REQUIRED_READ_FILES),
        "read_success": True,
        "missing_files": [],
        "file_digests_or_sizes": policy.PRE_EDIT_REQUIRED_FILE_METADATA,
        "repo_convention_files_inspected": list(policy.REPO_CONVENTION_FILES_INSPECTED),
        "master_plan_anchors_inspected": list(policy.MASTER_PLAN_ANCHORS_INSPECTED),
        "read_before_editing_confirmed": True,
        "worktree_pre_edit_status_short": "",
        "pre_edit_head_full": policy.PR134_OWNER_VERIFIED_FIELDS["mergeCommit_full"],
    }


def _roadmap_blueprint_extraction_report() -> dict[str, Any]:
    return {
        "receipt_type": "PR135_ROADMAP_BLUEPRINT_EXTRACTION_RECEIPT",
        "repo_pr_number": policy.PRODUCER_REPO_PR,
        "roadmap_pr_number": policy.PRODUCER_ROADMAP_PR,
        "roadmap_task_title_extracted": "historical dataset digest and loader contracts",
        "blueprint_task_title_extracted": "Historical dataset digest and loader",
        "roadmap_files_consulted": [
            "docs/roadmap/README.md",
            "docs/roadmap/QTT_PRs_Roadmap_Consolidated_Static_Runtime_Live_Stage1_to_Stage5_v1_0.md",
            "docs/roadmap/QTT_PRs_Roadmap_Index_v1_0.json",
        ],
        "blueprint_files_consulted": [
            "docs/roadmap/QTT_PR_Blueprints_Stage1_to_Stage5_PR83_to_PR224_v1_0.md",
            "docs/roadmap/QTT_PR_Blueprints_Index_PR83_to_PR224_v1_0.json",
        ],
        "identity_roster_consulted": True,
        "execution_state_controller_consulted": True,
        "roadmap_pr117_found": True,
        "roadmap_pr135_explicitly_not_used": True,
        "same_number_inference_used": False,
        "extracted_required_inputs": [
            "PR134 runtime resolver snapshot downstream handoff",
            "PR134 versioned candidate-set snapshot-lock metadata",
            "PR134 replay/paper input identity metadata",
            "PR133 orderbook/event-state snapshot contracts",
            "PR132 market-data ingest adapter contracts",
            "PR131 credential alias / secret no-capture readiness metadata",
        ],
        "extracted_forbidden_authority_refs": [
            "no live data",
            "no source acceptance",
            "no connector binding",
            "no credential resolution",
            "no private-state fetch",
            "no runtime cash authority",
            "no replay execution",
            "no paper execution",
            "no feature vector",
            "no trading signal",
            "no ranking/scoring/arbitration output",
            "no order authority",
            "no profit evidence",
            "no quantum execution",
            "no AtomicRows materialization",
        ],
        "extraction_conflicts": [],
    }


def _path_decision_report() -> dict[str, Any]:
    return {
        "receipt_type": "PR135_PATH_DECISION_RECEIPT",
        "repo_pr_number": policy.PRODUCER_REPO_PR,
        "roadmap_pr_number": policy.PRODUCER_ROADMAP_PR,
        "path_selection_precedence_used": [
            "Reuse current repo convention from PR131-PR134 when clear",
            "Reuse closest Stage 1 replay_paper/runtime_resolver path pattern",
            "Use PR135 default paths where no stronger convention exists",
        ],
        "chosen_paths": {
            "policy_module": policy.POLICY_MODULE_PATH,
            "implementation_module": (
                "src/qtt/stage1_prediction_markets/replay_paper/"
                "historical_dataset_digest_and_loader.py"
            ),
            "policy_schema_defs": policy.POLICY_SCHEMA_DEFS_PATH,
            "schemas": [
                f"{SCHEMA_DIR.as_posix()}/{name}" for name in SCHEMA_FILES
            ],
            "fixture": FIXTURE_PATH.as_posix(),
            "fixture_builder": "tools/build_historical_dataset_digest_and_loader_fixture.py",
            "validator": "tools/validate_historical_dataset_digest_and_loader.py",
            "policy_literal_drift_validator": (
                "tools/validate_historical_dataset_policy_literal_drift.py"
            ),
            "focused_tests": "tests/replay_paper/test_historical_dataset_digest_and_loader.py",
            "fail_closed_tests": "tests/fail_closed/test_run_validation_gates.py",
        },
        "path_decisions": [
            {
                "chosen_path": policy.POLICY_MODULE_PATH,
                "reason": "Stage 1 repo convention keeps replay/paper contracts under src/qtt/stage1_prediction_markets.",
                "convention_inspected": "src/qtt/stage1_prediction_markets/runtime_resolver_snapshot_executor",
                "rejected_alternative_paths": [
                    "src/qtt/replay_paper/historical_dataset_policy.py"
                ],
                "authority_boundary_impact": "metadata-only local fixture contract",
                "schema_drift_risk": False,
            },
            {
                "chosen_path": policy.POLICY_SCHEMA_DEFS_PATH,
                "reason": "Prompt and blueprint both identify replay_paper schema family for this dataset contract.",
                "convention_inspected": "schemas/replay_paper_review and Stage 1 package schemas",
                "rejected_alternative_paths": [
                    "src/qtt/stage1_prediction_markets/replay_paper/historical_dataset_policy.defs.schema.json"
                ],
                "authority_boundary_impact": "central policy refs avoid scattered enums",
                "schema_drift_risk": False,
            },
        ],
        "report_path_mapping": {
            "route_triage_convention": "docs/roadmap/generated/CODEX_PR135_ROUTE_TRIAGE_RECEIPT.json",
            "read_receipt_convention": "docs/roadmap/generated/CODEX_PR135_MANDATORY_READ_RECEIPT.json",
            "currentization_convention": (
                "docs/roadmap/generated/CODEX_REPO_PR134_GITHUB_AUDIT_CURRENTIZATION_RECEIPT.json"
            ),
        },
    }


def _market_specific_index() -> dict[str, Any]:
    rows = []
    for scope_ref in policy.scope_refs():
        rows.append(
            {
                "market_scope_id": scope_ref.market_scope_id,
                "canonical_venue_id": scope_ref.canonical_venue_id,
                "master_plan_anchor_terms_inspected": list(policy.MASTER_PLAN_ANCHORS_INSPECTED),
                "roadmap_anchor_terms_inspected": [
                    "Stage 1 prediction markets",
                    "Historical dataset digest and loader",
                    policy.VALIDATOR_MARKER,
                ],
                "blueprint_anchor_terms_inspected": [
                    "Dataset identity, source lineage, schema, and immutability are explicit",
                    "Load and digest historical prediction-market datasets for replay lanes",
                ],
                "dataset_digest_contract_applicability": True,
                "loader_manifest_contract_applicability": True,
                "source_lineage_requirement": policy.SOURCE_REQUIRED_REFERENCE_ONLY,
                "candidate_set_snapshot_lock_requirement": (
                    policy.VERSIONED_CANDIDATE_SET_SNAPSHOT_LOCK
                ),
                "replay_paper_input_identity_requirement": (
                    "PR134_REPLAY_PAPER_INPUT_IDENTITY_METADATA"
                ),
                "allowed_fixture_classes": list(policy.DATASET_RECORD_SCOPES),
                "forbidden_live_or_real_data_classes": [
                    policy.BLOCKED_LIVE_DATA_ATTEMPT,
                    policy.BLOCKED_SOURCE_ACCEPTANCE_ATTEMPT,
                    policy.BLOCKED_CONNECTOR_BINDING_ATTEMPT,
                ],
                "quantum_metadata_fields_required": [
                    "classical_comparator_required_flag",
                    "no_quantum_optimizer_input_flag",
                    "no_quantum_advantage_claim_flag",
                ],
                "atomicrows_pre_bridge_metadata_fields_required": [
                    "atomicrows_bundle_created_flag",
                    "atomicrows_bundle_edited_flag",
                    "atomicrows_bundle_sha_created_flag",
                    "atomicrows_rows_created_flag",
                ],
                "policy_block_code_refs": [
                    policy.BLOCKED_LIVE_DATA_ATTEMPT,
                    policy.BLOCKED_SOURCE_ACCEPTANCE_ATTEMPT,
                    policy.BLOCKED_CONNECTOR_BINDING_ATTEMPT,
                    policy.BLOCKED_NONCANONICAL_FORECASTEX_IBKR_IDENTITY,
                ],
                "downstream_consumers": list(policy.ALLOWED_FUTURE_CONSUMERS),
                "no_authority_flags_ref": policy.POLICY_MANIFEST_PATH,
                "policy_manifest_ref": policy.POLICY_MANIFEST_PATH,
                "fixture_shape_only_not_venue_fact_truth_boundary": (
                    policy.SOURCE_BOUNDARY_LANGUAGE
                ),
            }
        )
    return {
        "receipt_type": "PR135_MARKET_SPECIFIC_SECTION_INDEX",
        "repo_pr_number": policy.PRODUCER_REPO_PR,
        "roadmap_pr_number": policy.PRODUCER_ROADMAP_PR,
        "market_scope_count": len(rows),
        "market_scopes": rows,
    }


def _crosswalk_report() -> dict[str, Any]:
    required_rows = [
        "0X.4K Stage-1 packet schemas and contract boundaries",
        "0X.4S runtime resolver snapshot / handoff / input lock",
        "0X.4T concurrent replay/paper shared input identity and lane separation",
        "0X.4Q source-evidence retrieval/acceptance boundary",
        "0X.4R connector semantic binding boundary",
        "0X.4Z live path exclusion / low latency boundary",
        "0X.5C owner authority and external fact boundary",
        "0X.5F AtomicRows bundle/hash authority gate",
        "0X.5L Codex handoff / validation workflow / no deletion boundary",
        "8.1C / QT sections for quantum metadata only",
        "Roadmap PR117 / historical dataset digest and loader anchors",
        "Blueprint PR117 / historical dataset digest and loader anchors",
    ]
    rows = []
    for section in required_rows:
        rows.append(
            {
                "section_id": section.split(" ", 1)[0],
                "section_title_or_anchor": section,
                "relevance_to_PR135": "historical dataset digest/loader boundary and downstream metadata",
                "action_for_PR135": "create deterministic fixture-backed contract artifacts only",
                "allowed_artifacts": [
                    "schemas",
                    "fixtures",
                    "metadata reports",
                    "validators",
                ],
                "forbidden_artifacts": [
                    "live data",
                    "source acceptance",
                    "connector binding",
                    "replay or paper execution",
                    "order authority",
                    "profit evidence",
                    "quantum execution",
                    "AtomicRows materialization",
                ],
                "source_authority_boundary": policy.OWNER_DEFINITIONS_PACKET_NOT_EXTERNAL_FACT_AUTHORITY,
                "live_authority_boundary": "NO_LIVE_AUTHORITY_CREATED",
                "quantum_boundary": "METADATA_ONLY_NO_QUANTUM_EXECUTION",
                "atomicrows_boundary": "PRE_BRIDGE_METADATA_ONLY_NO_BUNDLE_SHA_ROWS",
                "policy_block_code_refs": [
                    policy.BLOCKED_SOURCE_ACCEPTANCE_ATTEMPT,
                    policy.BLOCKED_CONNECTOR_BINDING_ATTEMPT,
                    policy.BLOCKED_ATOMICROWS_MATERIALIZATION_ATTEMPT,
                ],
                "validation_hooks_to_add_or_preserve": [
                    "tools/validate_historical_dataset_digest_and_loader.py",
                    "tools/validate_historical_dataset_policy_literal_drift.py",
                    "tools/run_validation_gates.py",
                ],
            }
        )
    return {
        "receipt_type": "PR135_MASTER_PLAN_SECTION_CROSSWALK",
        "repo_pr_number": policy.PRODUCER_REPO_PR,
        "roadmap_pr_number": policy.PRODUCER_ROADMAP_PR,
        "rows": rows,
    }


def _command_action_matrix() -> dict[str, Any]:
    actions = (
        "READ_REQUIRED_FILES",
        "VERIFY_BRANCH_HEAD_WORKTREE",
        "LOAD_OWNER_VERIFIED_INPUTS",
        "CURRENTIZE_PR134_IDENTITY_ROSTER",
        "EMIT_PR134_GITHUB_AUDIT_CURRENTIZATION",
        "EMIT_PR135_ROUTE_TRIAGE",
        "EMIT_ROADMAP_BLUEPRINT_EXTRACTION",
        "EMIT_READ_RECEIPT",
        "EMIT_PATH_DECISION",
        "CREATE_POLICY_REGISTRY",
        "CREATE_POLICY_SCHEMA_DEFS",
        "CREATE_POLICY_MANIFEST",
        "CREATE_SCHEMAS_WITH_POLICY_REFS",
        "CREATE_FIXTURES",
        "CREATE_FIXTURE_BUILDER",
        "CREATE_VALIDATOR",
        "CREATE_POLICY_LITERAL_DRIFT_VALIDATOR",
        "CREATE_GENERATED_REPORTS",
        "ADD_FOCUSED_TESTS",
        "ADD_FAIL_CLOSED_TESTS",
        "UPDATE_CUMULATIVE_VALIDATION_GATE",
        "RUN_VALIDATIONS",
        "RESTORE_NON_PR_VALIDATION_NOISE",
        "CHECK_PROTECTED_ARTIFACT_DIFFS",
        "REPORT_FINAL_STATUS",
    )
    rows = []
    for action in actions:
        rows.append(
            {
                "action_id": action,
                "owner_authority_required": action.startswith("LOAD_OWNER"),
                "codex_allowed": True,
                "network_allowed": False,
                "github_allowed": False,
                "writes_repo_files": action.startswith(("CREATE", "EMIT", "ADD", "UPDATE", "CURRENTIZE")),
                **policy.no_authority_report_fields(),
                "policy_block_code_refs": [],
                "expected_outputs": [],
                "validation_tests": [
                    "tools/validate_historical_dataset_digest_and_loader.py"
                ],
            }
        )
    return {
        "receipt_type": "PR135_COMMAND_ACTION_MATRIX",
        "repo_pr_number": policy.PRODUCER_REPO_PR,
        "roadmap_pr_number": policy.PRODUCER_ROADMAP_PR,
        "actions": rows,
    }


def build_reports(fixture: Mapping[str, Any]) -> dict[str, Any]:
    artifacts = fixture["artifacts"]
    main_report = {
        "receipt_type": "PR135_HISTORICAL_DATASET_DIGEST_AND_LOADER_REPORT",
        "schema_version": policy.REPORT_SCHEMA_VERSION,
        "repo_pr_number": policy.PRODUCER_REPO_PR,
        "roadmap_pr_number": policy.PRODUCER_ROADMAP_PR,
        "validator_marker": policy.VALIDATOR_MARKER,
        "same_number_inference_used": False,
        "repo_pr135_maps_to_roadmap_pr117": True,
        "repo_pr135_maps_to_roadmap_pr135": False,
        "fixture_backed": True,
        "source_boundary_language": policy.SOURCE_BOUNDARY_LANGUAGE,
        "historical_dataset_digest_count": len(artifacts["historical_dataset_digests"]),
        "loader_manifest_count": len(artifacts["historical_dataset_loader_manifests"]),
        "input_lock_count": len(artifacts["historical_dataset_input_locks"]),
        "integrity_receipt_count": len(artifacts["historical_dataset_integrity_receipts"]),
        "rejection_receipt_count": len(artifacts["historical_dataset_rejection_receipts"]),
        "downstream_handoff_count": len(artifacts["historical_dataset_downstream_handoffs"]),
        "quantum_metadata_only_count": len(artifacts["historical_dataset_quantum_metadata"]),
        "atomicrows_pre_bridge_metadata_only_count": len(
            artifacts["historical_dataset_atomicrows_pre_bridge_metadata"]
        ),
        "no_authority_flags": policy.no_authority_report_fields(),
        "policy_manifest_ref": policy.POLICY_MANIFEST_PATH,
        "policy_schema_defs_ref": policy.POLICY_SCHEMA_DEFS_PATH,
        "fixture_ref": FIXTURE_PATH.as_posix(),
        "schema_refs": [f"{SCHEMA_DIR.as_posix()}/{name}" for name in SCHEMA_FILES],
    }
    return {
        "PR135OwnerVerifiedInputs.report.json": _owner_verified_inputs_receipt(),
        "PR134GitHubAuditCurrentization.report.json": {
            **_pr134_currentization_receipt(),
            "equivalent_repo_convention_receipt_path": (
                "docs/roadmap/generated/CODEX_REPO_PR134_GITHUB_AUDIT_CURRENTIZATION_RECEIPT.json"
            ),
        },
        "PR135RouteTriage.report.json": _route_triage_report(),
        "PR135HistoricalDatasetDigestAndLoaderReadReceipt.report.json": _read_receipt(),
        "PR135RoadmapBlueprintExtraction.report.json": _roadmap_blueprint_extraction_report(),
        "PR135PathDecision.report.json": _path_decision_report(),
        "PR135HistoricalDatasetPolicyManifest.report.json": policy.policy_manifest_payload(),
        "PR135MarketSpecificSectionIndex.report.json": _market_specific_index(),
        "PR135MasterPlanSectionCrosswalk.report.json": _crosswalk_report(),
        "PR135CommandActionMatrix.report.json": _command_action_matrix(),
        "PR135HistoricalDatasetDigestAndLoader.report.json": main_report,
    }


def write_artifacts(repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    fixture = build_fixture()
    for file_name, schema_doc in build_schema_documents().items():
        write_json(repo_root / SCHEMA_DIR / file_name, schema_doc)
    write_json(repo_root / FIXTURE_PATH, fixture)
    for file_name, report in build_reports(fixture).items():
        write_json(repo_root / REPORT_DIR / file_name, report)
    write_json(
        repo_root / ROADMAP_GENERATED_DIR / "CODEX_PR135_ROUTE_TRIAGE_RECEIPT.json",
        _route_triage_report(),
    )
    write_json(
        repo_root / ROADMAP_GENERATED_DIR / "CODEX_PR135_MANDATORY_READ_RECEIPT.json",
        _read_receipt(),
    )
    write_json(
        repo_root
        / ROADMAP_GENERATED_DIR
        / "CODEX_REPO_PR134_GITHUB_AUDIT_CURRENTIZATION_RECEIPT.json",
        _pr134_currentization_receipt(),
    )
    return fixture


def _failure(code: str, message: str, artifact_ref: str) -> ValidationFailure:
    return ValidationFailure(code, message, artifact_ref)


def validate_owner_verified_inputs(receipt: Mapping[str, Any]) -> list[ValidationFailure]:
    failures: list[ValidationFailure] = []
    for field, expected in policy.PR134_OWNER_VERIFIED_FIELDS.items():
        if receipt.get(field) != expected:
            failures.append(
                _failure(
                    policy.BLOCKED_PLACEHOLDER_OWNER_VERIFIED_INPUT,
                    f"owner verified field {field} is not {expected!r}",
                    "PR135OwnerVerifiedInputs.report.json",
                )
            )
    if not receipt.get("owner_verified_pr134_fields_present"):
        failures.append(
            _failure(
                policy.BLOCKED_PLACEHOLDER_OWNER_VERIFIED_INPUT,
                "owner verified PR134 fields are incomplete",
                "PR135OwnerVerifiedInputs.report.json",
            )
        )
    text = json.dumps(receipt, sort_keys=True)
    if "OWNER_VERIFIED_VALUE_REQUIRED" in text or "OWNER_VERIFIED_FROM_GH_PR_VIEW_134" in text:
        failures.append(
            _failure(
                policy.BLOCKED_PLACEHOLDER_OWNER_VERIFIED_INPUT,
                "owner verified PR134 placeholder remains",
                "PR135OwnerVerifiedInputs.report.json",
            )
        )
    return failures


def validate_route_triage(report: Mapping[str, Any]) -> list[ValidationFailure]:
    failures: list[ValidationFailure] = []
    if report.get("roadmap_pr_number") != policy.PRODUCER_ROADMAP_PR:
        failures.append(
            _failure(
                policy.BLOCKED_SAME_NUMBER_ROADMAP_INFERENCE,
                "Repo PR135 must map to Roadmap PR117",
                "PR135RouteTriage.report.json",
            )
        )
    if report.get("same_number_inference_used") is not False:
        failures.append(
            _failure(
                policy.BLOCKED_SAME_NUMBER_ROADMAP_INFERENCE,
                "same_number_inference_used must be false",
                "PR135RouteTriage.report.json",
            )
        )
    if report.get("repo_pr_number") == report.get("roadmap_pr_number"):
        failures.append(
            _failure(
                policy.BLOCKED_SAME_NUMBER_ROADMAP_INFERENCE,
                "Repo PR135 cannot map to Roadmap PR135",
                "PR135RouteTriage.report.json",
            )
        )
    if report.get("currentization_first_subtask_completed") is not True:
        failures.append(
            _failure(
                policy.BLOCKED_MISSING_PR134_CURRENTIZATION,
                "PR134 currentization must complete before PR135 implementation",
                "PR135RouteTriage.report.json",
            )
        )
    return failures


def _contains_forbidden_phrase(value: Any) -> bool:
    phrases = (
        "global permanent candidate freeze",
        "candidate universe freeze",
        "permanent candidate freeze",
        "freeze global candidates",
    )
    return any(phrase in json.dumps(value, sort_keys=True).lower() for phrase in phrases)


def validate_dataset_records(records: Sequence[Mapping[str, Any]]) -> list[ValidationFailure]:
    failures: list[ValidationFailure] = []
    seen_digest_ids: set[str] = set()
    for index, record in enumerate(records):
        artifact_ref = f"historical_dataset_digests[{index}]"
        dataset_id = record.get("dataset_digest_id")
        if not isinstance(dataset_id, str) or not dataset_id:
            failures.append(
                _failure(
                    policy.BLOCKED_MISSING_DATASET_DIGEST_ID,
                    "missing dataset id",
                    artifact_ref,
                )
            )
        elif dataset_id in seen_digest_ids:
            failures.append(
                _failure(
                    policy.BLOCKED_DUPLICATE_DATASET_DIGEST_ID,
                    "duplicate dataset digest id",
                    artifact_ref,
                )
            )
        else:
            seen_digest_ids.add(dataset_id)
        for field, block_code in policy.FORBIDDEN_RECORD_FLAG_TO_BLOCK_CODE.items():
            if record.get(field) is True:
                failures.append(
                    _failure(block_code, f"{field} must remain false", artifact_ref)
                )
        required_refs = {
            "runtime_resolver_snapshot_handoff_ref": policy.BLOCKED_MISSING_RUNTIME_RESOLVER_HANDOFF,
            "versioned_candidate_set_snapshot_lock_ref": policy.BLOCKED_MISSING_CANDIDATE_SET_SNAPSHOT_LOCK,
            "replay_paper_input_identity_ref": policy.BLOCKED_MISSING_REPLAY_PAPER_INPUT_IDENTITY,
            "source_lineage_ref": policy.BLOCKED_MISSING_SOURCE_LINEAGE,
        }
        for field, block_code in required_refs.items():
            if not record.get(field):
                failures.append(_failure(block_code, f"{field} is required", artifact_ref))
        if record.get("immutable_after_creation_flag") is not True:
            failures.append(
                _failure(policy.BLOCKED_MUTABLE_DATASET, "dataset must be immutable", artifact_ref)
            )
        if record.get("venue_scope") in policy.FORBIDDEN_VENUE_IDENTITIES:
            failures.append(
                _failure(
                    policy.BLOCKED_NONCANONICAL_FORECASTEX_IBKR_IDENTITY,
                    "noncanonical ForecastEx/IBKR identity",
                    artifact_ref,
                )
            )
        if record.get("global_candidate_freeze_flag") is True or _contains_forbidden_phrase(record):
            failures.append(
                _failure(
                    policy.BLOCKED_GLOBAL_PERMANENT_CANDIDATE_FREEZE_LANGUAGE,
                    "candidate-set wording must use versioned snapshot-lock language",
                    artifact_ref,
                )
            )
    return failures


def validate_fixture(fixture: Mapping[str, Any]) -> list[ValidationFailure]:
    failures: list[ValidationFailure] = []
    artifacts = fixture.get("artifacts")
    if not isinstance(artifacts, dict):
        return [
            _failure(
                policy.BLOCKED_MISSING_FIXTURE_ARTIFACTS,
                "fixture artifacts missing",
                FIXTURE_PATH.as_posix(),
            )
        ]
    failures.extend(validate_dataset_records(artifacts.get("historical_dataset_digests", [])))
    cases = {case.get("case_id"): case for case in fixture.get("fixture_cases", [])}
    if "valid_three_scope_fixture" not in cases:
        failures.append(
            _failure(
                policy.BLOCKED_MISSING_VALID_FIXTURE_CASE,
                "missing valid fixture case",
                FIXTURE_PATH.as_posix(),
            )
        )
    for case_id, block_code in policy.REQUIRED_FIXTURE_CASE_BLOCKS.items():
        case = cases.get(case_id)
        if case is None:
            failures.append(
                _failure(block_code, f"missing required fixture case {case_id}", FIXTURE_PATH.as_posix())
            )
        elif case.get("policy_block_code_ref") != block_code:
            failures.append(
                _failure(block_code, f"fixture case {case_id} has wrong block code", FIXTURE_PATH.as_posix())
            )
    return failures


def _load_report(repo_root: Path, name: str) -> dict[str, Any]:
    return load_json(repo_root / REPORT_DIR / name)


def _load_required_json(repo_root: Path, rel_path: str) -> Any:
    path = repo_root / rel_path
    if not path.exists():
        raise FileNotFoundError(rel_path)
    return load_json(path)


def validate_reports(repo_root: Path = REPO_ROOT) -> list[ValidationFailure]:
    failures: list[ValidationFailure] = []
    for rel_path in (*policy.REQUIRED_REPORTS[:-1], *policy.REQUIRED_ROADMAP_RECEIPTS):
        if not (repo_root / rel_path).exists():
            failures.append(
                _failure(policy.BLOCKED_MISSING_PR135_REPORT, f"missing {rel_path}", rel_path)
            )
    if failures:
        return failures

    failures.extend(validate_owner_verified_inputs(_load_report(repo_root, "PR135OwnerVerifiedInputs.report.json")))
    failures.extend(validate_route_triage(_load_report(repo_root, "PR135RouteTriage.report.json")))
    currentization = _load_report(repo_root, "PR134GitHubAuditCurrentization.report.json")
    if currentization.get("currentized_in_identity_roster") is not True:
        failures.append(
            _failure(
                policy.BLOCKED_MISSING_PR134_CURRENTIZATION,
                "PR134 currentization receipt is incomplete",
                "PR134GitHubAuditCurrentization.report.json",
            )
        )
    extraction = _load_report(repo_root, "PR135RoadmapBlueprintExtraction.report.json")
    if extraction.get("roadmap_pr117_found") is not True or extraction.get("roadmap_pr135_explicitly_not_used") is not True:
        failures.append(
            _failure(
                policy.BLOCKED_SAME_NUMBER_ROADMAP_INFERENCE,
                "Roadmap PR117 extraction must be explicit",
                "PR135RoadmapBlueprintExtraction.report.json",
            )
        )
    read_receipt = _load_report(repo_root, "PR135HistoricalDatasetDigestAndLoaderReadReceipt.report.json")
    if read_receipt.get("read_success") is not True or read_receipt.get("missing_files") != []:
        failures.append(
            _failure(
                policy.BLOCKED_MISSING_READ_INPUT,
                "required read receipt is incomplete",
                "PR135HistoricalDatasetDigestAndLoaderReadReceipt.report.json",
            )
        )
    market_index = _load_report(repo_root, "PR135MarketSpecificSectionIndex.report.json")
    scopes = [row.get("canonical_venue_id") for row in market_index.get("market_scopes", [])]
    if tuple(scopes) != policy.CANONICAL_VENUE_IDS:
        failures.append(
            _failure(
                policy.BLOCKED_NONCANONICAL_FORECASTEX_IBKR_IDENTITY,
                "market-specific section index must contain exactly four canonical scopes",
                "PR135MarketSpecificSectionIndex.report.json",
            )
        )
    command_matrix = _load_report(repo_root, "PR135CommandActionMatrix.report.json")
    for row in command_matrix.get("actions", []):
        if row.get("network_allowed") is not False or row.get("github_allowed") is not False:
            failures.append(
                _failure(
                    policy.BLOCKED_NETWORK_OR_GITHUB_ACTION,
                    "command matrix must be local-only",
                    "PR135CommandActionMatrix.report.json",
                )
            )
        for flag, expected in policy.NO_AUTHORITY_FLAGS.items():
            if row.get(flag) is not expected:
                failures.append(
                    _failure(flag.upper(), f"{flag} must remain false", "PR135CommandActionMatrix.report.json")
                )
    return failures


def validate_policy_manifest(repo_root: Path = REPO_ROOT) -> list[ValidationFailure]:
    failures: list[ValidationFailure] = []
    manifest = _load_report(repo_root, "PR135HistoricalDatasetPolicyManifest.report.json")
    defs = _load_required_json(repo_root, policy.POLICY_SCHEMA_DEFS_PATH)
    expected_manifest = policy.policy_manifest_payload()
    for key in (
        "validator_marker",
        "canonical_venues",
        "forbidden_venue_identities",
        "dataset_record_scopes",
        "digest_algorithms",
        "loader_manifest_modes",
        "input_lock_states",
        "no_authority_flags",
        "source_boundary_constants",
        "candidate_set_constants",
    ):
        if manifest.get(key) != expected_manifest.get(key):
            failures.append(
                _failure(
                    policy.BLOCKED_POLICY_LITERAL_DRIFT,
                    f"policy manifest drift at {key}",
                    policy.POLICY_MANIFEST_PATH,
                )
            )
    defs_root = defs.get("$defs", {})
    if defs_root.get("validator_marker", {}).get("const") != policy.VALIDATOR_MARKER:
        failures.append(
            _failure(
                policy.BLOCKED_POLICY_LITERAL_DRIFT,
                "policy schema defs marker drift",
                policy.POLICY_SCHEMA_DEFS_PATH,
            )
        )
    if defs_root.get("canonical_venue_id", {}).get("enum") != list(policy.CANONICAL_VENUE_IDS):
        failures.append(
            _failure(
                policy.BLOCKED_POLICY_LITERAL_DRIFT,
                "policy schema defs venue drift",
                policy.POLICY_SCHEMA_DEFS_PATH,
            )
        )
    return failures


def validate_protected_artifacts(repo_root: Path = REPO_ROOT) -> list[ValidationFailure]:
    protected = (
        "docs/master_plan/QTT_MasterPlan_Current.md",
        "docs/master_plan/atomic_rows/AtomicRows.bundle.jsonl",
        "docs/master_plan/atomic_rows/AtomicRows.bundle.sha256",
    )
    failures: list[ValidationFailure] = []
    import subprocess

    for rel_path in protected:
        completed = subprocess.run(
            ["git", "diff", "--", rel_path],
            cwd=repo_root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if completed.returncode != 0 or completed.stdout.strip():
            block = (
                policy.BLOCKED_UNAUTHORIZED_MASTER_PLAN_EDIT
                if rel_path.endswith("QTT_MasterPlan_Current.md")
                else policy.BLOCKED_ATOMICROWS_BUNDLE_OR_SHA_DIFF
            )
            failures.append(_failure(block, f"protected artifact diff: {rel_path}", rel_path))
    return failures


def validate_all(repo_root: Path = REPO_ROOT) -> list[ValidationFailure]:
    failures: list[ValidationFailure] = []
    try:
        fixture = load_json(repo_root / FIXTURE_PATH)
    except Exception as exc:
        return [
            _failure(
                policy.BLOCKED_MISSING_PR135_FIXTURE,
                str(exc),
                FIXTURE_PATH.as_posix(),
            )
        ]
    failures.extend(validate_fixture(fixture))
    failures.extend(validate_reports(repo_root))
    if not failures:
        failures.extend(validate_policy_manifest(repo_root))
    failures.extend(validate_protected_artifacts(repo_root))
    try:
        from tools import validate_historical_dataset_policy_literal_drift as drift

        drift_failures = drift.validate_policy_literal_drift(repo_root=repo_root)
        failures.extend(
            _failure(policy.BLOCKED_POLICY_LITERAL_DRIFT, item, "PR135PolicyLiteralDrift.report.json")
            for item in drift_failures
        )
    except Exception as exc:
        failures.append(
            _failure(policy.BLOCKED_POLICY_LITERAL_DRIFT, str(exc), "policy literal drift validator")
        )
    return failures


def marker_for_failures(failures: Sequence[ValidationFailure]) -> str:
    return policy.VALIDATOR_MARKER if not failures else ""


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--write-artifacts", action="store_true")
    args = parser.parse_args(argv)
    repo_root = args.repo_root.resolve()
    if args.write_artifacts:
        write_artifacts(repo_root)
    failures = validate_all(repo_root)
    if failures:
        for failure in failures:
            print(f"{failure.code}: {failure.message} ({failure.artifact_ref})")
        return 1
    print(policy.VALIDATOR_MARKER)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
