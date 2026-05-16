#!/usr/bin/env python3
"""Validate PR113 AtomicRows bundle materialization."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
import pathlib
import subprocess
import sys
from typing import Any, Iterable, Sequence

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from src.qtt.core.testing.atomicrows_bundle_state import (
    AtomicRowsBundleState,
    canonical_atomicrows_bundle_presence,
    expected_atomicrows_bundle_state_from_contract,
    validate_current_atomicrows_bundle_state,
)
from tools import generate_atomicrows_exact_row_source_files as source_generator
from tools import materialize_atomicrows_bundle_from_exact_rows as materializer
from tools import validate_atomicrows_exact_row_agent_family_eligibility_matrix as matrix_gate


REPO_ROOT = _REPO_ROOT
DEFAULT_MANIFEST = pathlib.Path(
    "docs/master_plan/atomicrows/AtomicRowsBundleMaterializationManifest.yaml"
)
DEFAULT_SCHEMA = pathlib.Path(
    "schemas/atomicrows/atomicrows_bundle_materialization_manifest.schema.json"
)
DEFAULT_ROW_SCHEMA = pathlib.Path(
    "schemas/atomicrows/atomicrows_materialized_bundle_row.schema.json"
)
DEFAULT_REPORT = pathlib.Path(
    "docs/master_plan/generated/AtomicRowsBundleMaterialization.report.json"
)
SUCCESS_MARKER = "QTT_ATOMICROWS_BUNDLE_MATERIALIZATION_OK"
FAILURE_MARKER = "QTT_ATOMICROWS_BUNDLE_MATERIALIZATION_FAILED"

REPORT_ID = "ATOMICROWS_BUNDLE_MATERIALIZATION_REPORT"
VALIDATOR_NAME = "validate_atomicrows_bundle_materialization_manifest.py"
VALIDATION_STATUS = "PASS"
MANIFEST_ID = "ATOMICROWS_BUNDLE_MATERIALIZATION_MANIFEST"
MANIFEST_VERSION = "v1"
AUTHORITY_CLASS = materializer.AUTHORITY_CLASS
CURRENT_EXPECTED_STATE = materializer.MATERIALIZATION_STATE
TRANSITION_FROM_STATE = materializer.TRANSITION_FROM_STATE
TRANSITION_TO_STATE = materializer.TRANSITION_TO_STATE
BYTE_STABLE_MATCH = "MATCH_EXISTING_BYTES"
LINE_ENDING_OK = "LF_ONLY_FINAL_NEWLINE"
FUTURE_ONLY_HANDOFF_STATE = materializer.FUTURE_ONLY_HANDOFF_STATE

FORBIDDEN_COMPUTED_FIELDS = {
    "agent_binding_score",
    "lifecycle_status_score",
    "owner_override_score",
    "platform_applicability_score",
    "market_type_applicability_score",
    "strategy_fit_score",
    "latency_fit_score",
    "risk_fit_score",
    "replay_paper_score",
    "optimizer_score",
    "runtime_readiness_score",
    "quantum_applicability_score",
    "expected_net_profit_score",
    "drawdown_penalty",
    "complexity_penalty",
    "source_currentness_penalty",
    "execution_cost_penalty",
    "owner_priority_boost",
    "quantum_boost",
    "final_selection_score",
    "score_breakdown",
    "rank",
    "rank_order",
    "selected_stack_id",
    "selected_parameter_families",
    "selected_algorithm_families",
    "selected_trade_context_id",
    "selected_order_intent_id",
    "optimizer_output",
    "replay_result",
    "paper_result",
    "profit_result",
    "latency_superiority_result",
    "execution_superiority_result",
    "quantum_advantage_result",
}

AUTHORITY_TRUE_FIELDS = {
    "live_order_authority_allowed",
    "final_order_submission_authority_allowed",
    "live_trade_intent_authority_allowed",
    "runtime_live_authority_allowed",
    "backend_authority_allowed",
    "source_fact_authority_allowed",
    "connector_authority_allowed",
    "runtime_cash_authority_allowed",
    "source_retrieval_execution_allowed",
    "source_acceptance_execution_allowed",
    "connector_semantic_binding_execution_allowed",
    "scoring_execution_allowed",
    "ranking_execution_allowed",
    "selection_execution_allowed",
    "candidate_stack_generation_allowed",
    "optimizer_execution_allowed",
    "replay_execution_allowed",
    "paper_execution_allowed",
    "quantum_backend_authority_allowed",
    "quantum_simulator_authority_allowed",
    "quantum_provider_authority_allowed",
    "profit_evidence_allowed",
    "expected_profit_proof_allowed",
    "latency_superiority_evidence_allowed",
    "execution_superiority_evidence_allowed",
    "quantum_advantage_evidence_allowed",
    "sha_freeze_authority_allowed",
    "final_readiness_authority_allowed",
}


@dataclass
class ValidationResult:
    ok: bool
    failures: list[str]
    report: dict[str, Any] | None = None


@dataclass(frozen=True)
class BundleRows:
    rows: list[dict[str, Any]]
    raw_lines: list[str]
    raw_bytes: bytes


def _resolve(repo_root: pathlib.Path, path: pathlib.Path) -> pathlib.Path:
    return path if path.is_absolute() else repo_root / path


def _mapping(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _list_of_mappings(value: Any) -> list[dict[str, Any]]:
    return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []


def _load_json(path: pathlib.Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON root must be an object: {path}")
    return value


def load_manifest(path: pathlib.Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    try:
        value = json.loads(text)
    except json.JSONDecodeError:
        value = source_generator.load_yaml(path)
    if not isinstance(value, dict):
        raise ValueError(f"manifest root must be an object: {path}")
    return value


def serialize_report(report: dict[str, Any]) -> str:
    return json.dumps(report, indent=2, sort_keys=True) + "\n"


def schema_subset_failures(payload: dict[str, Any], schema: dict[str, Any], label: str) -> list[str]:
    failures: list[str] = []
    if schema.get("type") == "object" and not isinstance(payload, dict):
        return [f"{label} must be an object"]
    for field in schema.get("required", []):
        if field not in payload:
            failures.append(f"{label}.{field} is required")
    if schema.get("additionalProperties") is False:
        allowed = set(_mapping(schema.get("properties")))
        for field in payload:
            if field not in allowed:
                failures.append(f"{label}.{field} is not allowed by schema")
    for field, rules in _mapping(schema.get("properties")).items():
        if field not in payload or not isinstance(rules, dict):
            continue
        value = payload[field]
        if "const" in rules and value != rules["const"]:
            failures.append(f"{label}.{field} must be {rules['const']!r}")
        expected_type = rules.get("type")
        if expected_type == "object" and not isinstance(value, dict):
            failures.append(f"{label}.{field} must be an object")
        if expected_type == "array" and not isinstance(value, list):
            failures.append(f"{label}.{field} must be an array")
        if expected_type == "string" and not isinstance(value, str):
            failures.append(f"{label}.{field} must be a string")
        if expected_type == "integer" and (
            not isinstance(value, int) or isinstance(value, bool)
        ):
            failures.append(f"{label}.{field} must be an integer")
        if expected_type == "boolean" and not isinstance(value, bool):
            failures.append(f"{label}.{field} must be a boolean")
    return failures


def expected_family_distribution() -> dict[str, int]:
    return {
        plan.family_id: plan.row_count
        for plan in source_generator.build_family_plans()
    }


def expected_row_ranges() -> dict[str, tuple[int, int]]:
    return {
        plan.family_id: (plan.start_row_index, plan.end_row_index)
        for plan in source_generator.build_family_plans()
    }


def validate_manifest_payload(manifest: dict[str, Any], schema: dict[str, Any]) -> list[str]:
    failures = schema_subset_failures(manifest, schema, "manifest")
    expected = {
        "manifest_id": MANIFEST_ID,
        "manifest_version": MANIFEST_VERSION,
        "authority_class": AUTHORITY_CLASS,
        "created_for": "PR113_ATOMICROWS_BUNDLE_MATERIALIZATION",
        "current_expected_boundary_state": CURRENT_EXPECTED_STATE,
        "transition_from_state": TRANSITION_FROM_STATE,
        "transition_to_state": TRANSITION_TO_STATE,
        "bundle_path": materializer.BUNDLE_PATH.as_posix(),
        "bundle_sha_path_expected_absent": materializer.BUNDLE_SHA_PATH.as_posix(),
        "source_exact_row_directory": source_generator.EXACT_ROW_SOURCES_DIR.as_posix() + "/",
        "source_materialization_manifest_ref": source_generator.EXACT_ROW_MATERIALIZATION_MANIFEST_PATH.as_posix()
        if hasattr(source_generator, "EXACT_ROW_MATERIALIZATION_MANIFEST_PATH")
        else "docs/master_plan/atomicrows/AtomicRowsExactRowSourceMaterializationManifest.yaml",
        "d2_e0_eligibility_matrix_ref": matrix_gate.DEFAULT_MANIFEST.as_posix(),
        "bundle_boundary_state_contract_ref": (
            "docs/master_plan/atomicrows/AtomicRowsBundleBoundaryStateContract.yaml"
        ),
        "expected_source_family_file_count": source_generator.EXPECTED_FAMILY_COUNT,
        "expected_exact_row_record_count": source_generator.EXPECTED_TOTAL_ROWS,
        "expected_bundle_row_count": source_generator.EXPECTED_TOTAL_ROWS,
        "generated_report_path": DEFAULT_REPORT.as_posix(),
    }
    for field, expected_value in expected.items():
        if manifest.get(field) != expected_value:
            failures.append(f"manifest.{field} must be {expected_value!r}")

    observed_distribution = {
        item.get("family_id"): item.get("expected_row_count")
        for item in _list_of_mappings(manifest.get("expected_family_distribution"))
    }
    if observed_distribution != expected_family_distribution():
        failures.append("manifest.expected_family_distribution must match canonical distribution")

    observed_ranges = {
        item.get("family_id"): (item.get("row_range_start"), item.get("row_range_end"))
        for item in _list_of_mappings(manifest.get("expected_row_ranges"))
    }
    if observed_ranges != expected_row_ranges():
        failures.append("manifest.expected_row_ranges must match canonical ranges")

    for field in (
        "bundle_format_contract",
        "deterministic_assembly_contract",
        "source_join_contract",
        "d2_e0_join_contract",
        "scoring_ranking_readiness_preservation_contract",
        "trade_context_readiness_preservation_contract",
        "role_complete_stack_future_contract",
        "quantum_metadata_preservation_contract",
        "low_latency_future_lookup_contract",
        "owner_research_extension_contract",
        "forbidden_authority_contract",
        "future_centralized_blocker_handoff_contract",
        "no_claim_boundary",
        "validation_contract",
        "future_handoff",
    ):
        if not isinstance(manifest.get(field), dict):
            failures.append(f"manifest.{field} must be an object")
    return failures


def load_bundle_rows(repo_root: pathlib.Path) -> tuple[list[str], BundleRows]:
    path = _resolve(repo_root, materializer.BUNDLE_PATH)
    if not path.exists():
        return ["bundle file missing"], BundleRows([], [], b"")
    raw = path.read_bytes()
    failures: list[str] = []
    if raw.startswith(b"\xef\xbb\xbf"):
        failures.append("bundle must not include UTF-8 BOM")
    if b"\r\n" in raw or b"\r" in raw:
        failures.append("bundle must use LF-only line endings")
    if not raw.endswith(b"\n"):
        failures.append("bundle must end with LF")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        return [f"bundle must be UTF-8: {exc}"], BundleRows([], [], raw)
    lines = text.splitlines()
    if any(not line.strip() for line in lines):
        failures.append("bundle must not contain blank lines")
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(lines, start=1):
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            failures.append(f"bundle line {line_number} invalid JSON: {exc}")
            continue
        if not isinstance(value, dict):
            failures.append(f"bundle line {line_number} must be a JSON object")
            continue
        rows.append(value)
    return failures, BundleRows(rows, lines, raw)


def _iter_key_values(value: Any) -> Iterable[tuple[str, Any]]:
    if isinstance(value, dict):
        for key, child in value.items():
            yield key, child
            yield from _iter_key_values(child)
    elif isinstance(value, list):
        for child in value:
            yield from _iter_key_values(child)


def _count_forbidden_key_presence(rows: Sequence[dict[str, Any]], keys: set[str]) -> int:
    count = 0
    for row in rows:
        count += sum(1 for key, _value in _iter_key_values(row) if key in keys)
    return count


def _count_true_fields(rows: Sequence[dict[str, Any]], keys: set[str]) -> dict[str, int]:
    counts = {key: 0 for key in keys}
    for row in rows:
        for key, value in _iter_key_values(row):
            if key in counts and value is True:
                counts[key] += 1
    return counts


def _field_true_count(rows: Sequence[dict[str, Any]], field: str) -> int:
    return sum(1 for row in rows for key, value in _iter_key_values(row) if key == field and value is True)


def _git_diff_check(repo_root: pathlib.Path, pathspec: str) -> dict[str, Any]:
    completed = subprocess.run(
        ["git", "diff", "--name-only", "--", pathspec],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )
    changed = [line.strip() for line in completed.stdout.splitlines() if line.strip()]
    return {
        "pathspec": pathspec,
        "unchanged": completed.returncode == 0 and not changed,
        "changed_paths": changed,
        "git_returncode": completed.returncode,
    }


def validate_bundle_rows(
    rows: BundleRows,
    row_schema: dict[str, Any],
    repo_root: pathlib.Path,
) -> tuple[list[str], dict[str, Any]]:
    failures: list[str] = []
    expected_source_rows = materializer.load_exact_source_rows(repo_root)
    source_dir = repo_root / pathlib.Path(*source_generator.EXACT_ROW_SOURCES_DIR.parts)
    actual_source_family_file_count = len(
        sorted(source_dir.glob("*.exact_rows.jsonl"))
    )
    expected_source_by_id = {item.row["row_id"]: item for item in expected_source_rows}
    d2_e0_by_id = materializer.load_d2_e0_records(repo_root)
    expected_bytes = materializer.render_bundle_bytes(
        materializer.assemble_bundle_rows(repo_root)
    )
    row_ids = [row.get("exact_row_id") for row in rows.rows]
    bundle_ids = [row.get("bundle_row_id") for row in rows.rows]
    duplicate_bundle_ids = sorted(
        str(row_id) for row_id in set(bundle_ids) if bundle_ids.count(row_id) > 1
    )
    source_id_set = set(expected_source_by_id)
    bundle_source_ids = {row_id for row_id in row_ids if isinstance(row_id, str)}
    missing_source_ids = sorted(source_id_set - bundle_source_ids)
    unexpected_source_ids = sorted(bundle_source_ids - source_id_set)
    source_record_digest_mismatch_count = 0
    d2_e0_join_mismatch_count = 0
    scoring_readiness_join_mismatch_count = 0
    future_score_component_input_coverage_count = 0
    future_stack_role_input_coverage_count = 0
    trade_context_metadata_or_blocker_coverage_count = 0

    observed_order = [row.get("row_index") for row in rows.rows]
    expected_order = list(range(1, source_generator.EXPECTED_TOTAL_ROWS + 1))
    row_order_valid = observed_order == expected_order
    if not row_order_valid:
        failures.append("bundle row order must be row_index 1..4183")

    for index, row in enumerate(rows.rows, start=1):
        failures.extend(schema_subset_failures(row, row_schema, f"bundle_rows[{index}]"))
        row_id = row.get("exact_row_id")
        if not isinstance(row_id, str):
            failures.append(f"bundle_rows[{index}].exact_row_id must be string")
            continue
        source = expected_source_by_id.get(row_id)
        d2_e0 = d2_e0_by_id.get(row_id)
        if source is None:
            continue
        if d2_e0 is None:
            d2_e0_join_mismatch_count += 1
            continue
        if row.get("source_record_digest") != source.digest:
            source_record_digest_mismatch_count += 1
        if row.get("source_record_stable_identity") != source.stable_identity:
            source_record_digest_mismatch_count += 1
        expected_join = {
            "row_index": source.row["row_index"],
            "family_id": source.row["family_id"],
            "family_name": source.row["family_label"],
            "source_file": source.row["source_file_path"],
            "source_row_class": source.row["row_class"],
            "source_subfamily_id": source.row["subfamily_id"],
            "source_quantum_metadata_class": source.row["quantum_metadata"][
                "quantum_metadata_class"
            ],
        }
        for field, expected_value in expected_join.items():
            if row.get(field) != expected_value or d2_e0.get(field) != expected_value:
                d2_e0_join_mismatch_count += 1
                break
        if row.get("d2_e0_scoring_ranking_readiness", {}).get(
            "scoring_readiness_decision"
        ) != d2_e0.get("scoring_readiness_decision"):
            scoring_readiness_join_mismatch_count += 1
        if row.get("eligible_future_score_components") or row.get(
            "blocked_future_score_components"
        ):
            future_score_component_input_coverage_count += 1
        if row.get("eligible_future_stack_roles") or row.get("blocked_future_stack_roles"):
            future_stack_role_input_coverage_count += 1
        if row.get("trade_context_applicability_metadata") or row.get(
            "trade_context_applicability_blocker"
        ):
            trade_context_metadata_or_blocker_coverage_count += 1
        if row.get("source_record") != source.row:
            failures.append(f"{row_id}.source_record must preserve the exact source payload")
        if row.get("bundle_materialization_authority_class") != AUTHORITY_CLASS:
            failures.append(f"{row_id}.bundle_materialization_authority_class mismatch")
        if row.get("bundle_materialized") is not True:
            failures.append(f"{row_id}.bundle_materialized must be true")

    distribution = {
        family_id: sum(1 for row in rows.rows if row.get("family_id") == family_id)
        for family_id in expected_family_distribution()
    }
    row_ranges_observed: dict[str, tuple[int, int]] = {}
    for family_id in expected_family_distribution():
        indexes = [
            row["row_index"]
            for row in rows.rows
            if row.get("family_id") == family_id and isinstance(row.get("row_index"), int)
        ]
        if indexes:
            row_ranges_observed[family_id] = (min(indexes), max(indexes))

    forbidden_key_count = _count_forbidden_key_presence(rows.rows, FORBIDDEN_COMPUTED_FIELDS)
    true_counts = _count_true_fields(rows.rows, AUTHORITY_TRUE_FIELDS)
    computed_counts = {
        "computed_score_field_count": forbidden_key_count,
        "numeric_ranking_output_count": _count_forbidden_key_presence(
            rows.rows, {"rank", "rank_order"}
        ),
        "selected_stack_output_count": _count_forbidden_key_presence(
            rows.rows,
            {
                "selected_stack_id",
                "selected_parameter_families",
                "selected_algorithm_families",
            },
        ),
        "selected_order_intent_output_count": _count_forbidden_key_presence(
            rows.rows, {"selected_order_intent_id"}
        ),
        "optimizer_output_count": _count_forbidden_key_presence(rows.rows, {"optimizer_output"}),
        "replay_paper_result_count": _count_forbidden_key_presence(
            rows.rows, {"replay_result", "paper_result", "replay_paper_result"}
        ),
        "profit_evidence_count": _field_true_count(rows.rows, "profit_evidence_allowed"),
        "expected_profit_proof_count": _field_true_count(rows.rows, "expected_profit_proof_allowed"),
        "latency_superiority_evidence_count": _field_true_count(
            rows.rows, "latency_superiority_evidence_allowed"
        ),
        "execution_superiority_evidence_count": _field_true_count(
            rows.rows, "execution_superiority_evidence_allowed"
        ),
        "quantum_advantage_evidence_count": _field_true_count(
            rows.rows, "quantum_advantage_evidence_allowed"
        ),
    }

    counts = {
        "bundle_row_count": len(rows.rows),
        "source_family_file_count": actual_source_family_file_count,
        "source_exact_row_record_count": len(expected_source_rows),
        "eligibility_matrix_coverage_count": len(d2_e0_by_id),
        "scoring_readiness_coverage_count": sum(
            1 for record in d2_e0_by_id.values() if record.get("scoring_readiness_decision")
        ),
        "future_score_component_input_coverage_count": future_score_component_input_coverage_count,
        "future_stack_role_input_coverage_count": future_stack_role_input_coverage_count,
        "trade_context_metadata_or_blocker_coverage_count": trade_context_metadata_or_blocker_coverage_count,
        "family_distribution_observed": distribution,
        "family_distribution_expected": expected_family_distribution(),
        "family_distribution_match": distribution == expected_family_distribution(),
        "row_range_match": row_ranges_observed == expected_row_ranges(),
        "row_order_valid": row_order_valid,
        "all_source_rows_bundled": not missing_source_ids and len(bundle_source_ids) == len(source_id_set),
        "all_bundle_rows_have_source": not unexpected_source_ids,
        "all_bundle_rows_have_d2_e0_eligibility": len(bundle_source_ids & set(d2_e0_by_id)) == len(rows.rows),
        "all_bundle_rows_have_scoring_readiness": scoring_readiness_join_mismatch_count == 0
        and len(rows.rows) == source_generator.EXPECTED_TOTAL_ROWS,
        "all_bundle_rows_have_future_score_component_contract": future_score_component_input_coverage_count
        == source_generator.EXPECTED_TOTAL_ROWS,
        "all_bundle_rows_have_future_stack_role_contract": future_stack_role_input_coverage_count
        == source_generator.EXPECTED_TOTAL_ROWS,
        "all_bundle_rows_have_trade_context_metadata_or_blocker": trade_context_metadata_or_blocker_coverage_count
        == source_generator.EXPECTED_TOTAL_ROWS,
        "missing_source_row_count": len(missing_source_ids),
        "duplicate_bundle_row_count": len(duplicate_bundle_ids),
        "unexpected_bundle_row_count": len(unexpected_source_ids),
        "source_record_digest_mismatch_count": source_record_digest_mismatch_count,
        "d2_e0_join_mismatch_count": d2_e0_join_mismatch_count,
        "scoring_readiness_join_mismatch_count": scoring_readiness_join_mismatch_count,
        "byte_stable_generation_result": BYTE_STABLE_MATCH
        if rows.raw_bytes == expected_bytes
        else "MISMATCH_EXPECTED_GENERATED_BYTES",
        "line_ending_result": LINE_ENDING_OK
        if rows.raw_bytes.endswith(b"\n") and b"\r" not in rows.raw_bytes
        else "LINE_ENDING_INVALID",
        "live_order_authority_count": true_counts["live_order_authority_allowed"],
        "final_order_submission_authority_count": true_counts[
            "final_order_submission_authority_allowed"
        ],
        "live_trade_intent_authority_count": true_counts["live_trade_intent_authority_allowed"],
        "runtime_live_authority_count": true_counts["runtime_live_authority_allowed"],
        "backend_authority_count": true_counts["backend_authority_allowed"],
        "scoring_execution_allowed_count": true_counts["scoring_execution_allowed"],
        "ranking_execution_allowed_count": true_counts["ranking_execution_allowed"],
        "selection_execution_allowed_count": true_counts["selection_execution_allowed"],
        "candidate_stack_generation_allowed_count": true_counts[
            "candidate_stack_generation_allowed"
        ],
        "optimizer_execution_allowed_count": true_counts["optimizer_execution_allowed"],
        "replay_execution_allowed_count": true_counts["replay_execution_allowed"],
        "paper_execution_allowed_count": true_counts["paper_execution_allowed"],
        "source_retrieval_execution_allowed_count": true_counts[
            "source_retrieval_execution_allowed"
        ],
        "source_fact_authority_count": true_counts["source_fact_authority_allowed"],
        "connector_authority_count": true_counts["connector_authority_allowed"],
        "runtime_cash_authority_count": true_counts["runtime_cash_authority_allowed"],
        "quantum_backend_authority_count": true_counts["quantum_backend_authority_allowed"],
        "quantum_simulator_authority_count": true_counts["quantum_simulator_authority_allowed"],
        "quantum_provider_authority_count": true_counts["quantum_provider_authority_allowed"],
        **computed_counts,
    }
    return failures, counts


def _family_rows(rows: Sequence[dict[str, Any]], family_id: str) -> list[dict[str, Any]]:
    return [row for row in rows if row.get("family_id") == family_id]


def build_family_results(rows: Sequence[dict[str, Any]]) -> dict[str, Any]:
    quantum_rows = [
        row for row in rows if row.get("family_id") in source_generator.QUANTUM_FORWARD_FAMILY_IDS
    ]
    family_009 = _family_rows(rows, source_generator.AGENT_GOVERNANCE_FAMILY_ID)
    family_010 = _family_rows(rows, "010_source_evidence_connector_semantic")
    family_006 = _family_rows(rows, "006_capital_sizing_cash")
    family_007 = _family_rows(rows, "007_latency_routing")
    family_011 = _family_rows(rows, "011_replay_paper_validation")
    family_002 = _family_rows(rows, "002_scoring_ranking")
    return {
        "quantum_family_metadata_only_result": {
            "families": sorted(source_generator.QUANTUM_FORWARD_FAMILY_IDS),
            "row_count": len(quantum_rows),
            "metadata_only": all(
                row.get("quantum_metadata_policy", {}).get("quantum_forward_family") is True
                and row.get("quantum_metadata_policy", {}).get(
                    "quantum_backend_authority_allowed"
                )
                is False
                and row.get("quantum_metadata_policy", {}).get(
                    "quantum_simulator_authority_allowed"
                )
                is False
                and row.get("quantum_metadata_policy", {}).get(
                    "quantum_provider_authority_allowed"
                )
                is False
                and row.get("quantum_metadata_policy", {}).get(
                    "quantum_advantage_claim_allowed"
                )
                is False
                for row in quantum_rows
            ),
        },
        "agent_governance_family_non_live_result": {
            "family_id": source_generator.AGENT_GOVERNANCE_FAMILY_ID,
            "row_count": len(family_009),
            "non_live": all(
                row.get("runtime_live_authority_boundary", {}).get(
                    "live_order_authority_allowed"
                )
                is False
                for row in family_009
            ),
        },
        "source_connector_family_block_result": {
            "family_id": "010_source_evidence_connector_semantic",
            "source_fact_authority_count": sum(
                row.get("source_connector_authority_boundary", {}).get(
                    "source_fact_authority_allowed"
                )
                is True
                for row in family_010
            ),
            "connector_authority_count": sum(
                row.get("source_connector_authority_boundary", {}).get(
                    "connector_authority_allowed"
                )
                is True
                for row in family_010
            ),
        },
        "capital_cash_family_runtime_cash_block_result": {
            "family_id": "006_capital_sizing_cash",
            "runtime_cash_authority_count": sum(
                row.get("runtime_live_authority_boundary", {}).get(
                    "runtime_cash_authority_allowed"
                )
                is True
                for row in family_006
            ),
        },
        "latency_family_superiority_claim_block_result": {
            "family_id": "007_latency_routing",
            "latency_superiority_evidence_count": sum(
                row.get("evidence_authority_boundary", {}).get(
                    "latency_superiority_evidence_allowed"
                )
                is True
                for row in family_007
            ),
        },
        "replay_paper_family_execution_result_block_result": {
            "family_id": "011_replay_paper_validation",
            "replay_execution_allowed_count": sum(
                row.get("execution_authority_boundary", {}).get("replay_execution_allowed")
                is True
                for row in family_011
            ),
            "paper_execution_allowed_count": sum(
                row.get("execution_authority_boundary", {}).get("paper_execution_allowed")
                is True
                for row in family_011
            ),
            "replay_paper_result_count": _count_forbidden_key_presence(
                family_011, {"replay_result", "paper_result", "replay_paper_result"}
            ),
        },
        "scoring_ranking_family_execution_block_result": {
            "family_id": "002_scoring_ranking",
            "scoring_execution_allowed_count": sum(
                row.get("execution_authority_boundary", {}).get("scoring_execution_allowed")
                is True
                for row in family_002
            ),
            "ranking_execution_allowed_count": sum(
                row.get("execution_authority_boundary", {}).get("ranking_execution_allowed")
                is True
                for row in family_002
            ),
        },
    }


def build_report(
    *,
    repo_root: pathlib.Path,
    counts: dict[str, Any],
    rows: Sequence[dict[str, Any]],
    validation_errors: list[str],
) -> dict[str, Any]:
    presence = canonical_atomicrows_bundle_presence(repo_root)
    family_results = build_family_results(rows)
    result_ok = not validation_errors
    report: dict[str, Any] = {
        "report_id": REPORT_ID,
        "manifest_id": MANIFEST_ID,
        "validator_name": VALIDATOR_NAME,
        "validation_status": VALIDATION_STATUS if result_ok else "FAIL",
        "current_expected_boundary_state": CURRENT_EXPECTED_STATE,
        "transition_from_state": TRANSITION_FROM_STATE,
        "transition_to_state": TRANSITION_TO_STATE,
        "bundle_path": materializer.BUNDLE_PATH.as_posix(),
        "bundle_file_exists": presence.bundle_jsonl_exists,
        "bundle_row_count": counts.get("bundle_row_count", 0),
        "expected_bundle_row_count": source_generator.EXPECTED_TOTAL_ROWS,
        "source_family_file_count": counts.get("source_family_file_count", 0),
        "source_exact_row_record_count": counts.get("source_exact_row_record_count", 0),
        "expected_source_family_file_count": source_generator.EXPECTED_FAMILY_COUNT,
        "expected_exact_row_record_count": source_generator.EXPECTED_TOTAL_ROWS,
        "eligibility_matrix_coverage_count": counts.get("eligibility_matrix_coverage_count", 0),
        "scoring_readiness_coverage_count": counts.get("scoring_readiness_coverage_count", 0),
        "future_score_component_input_coverage_count": counts.get(
            "future_score_component_input_coverage_count", 0
        ),
        "future_stack_role_input_coverage_count": counts.get(
            "future_stack_role_input_coverage_count", 0
        ),
        "trade_context_metadata_or_blocker_coverage_count": counts.get(
            "trade_context_metadata_or_blocker_coverage_count", 0
        ),
        "family_distribution_observed": counts.get("family_distribution_observed", {}),
        "family_distribution_expected": counts.get("family_distribution_expected", {}),
        "family_distribution_match": counts.get("family_distribution_match", False),
        "row_range_match": counts.get("row_range_match", False),
        "row_order_valid": counts.get("row_order_valid", False),
        "all_source_rows_bundled": counts.get("all_source_rows_bundled", False),
        "all_bundle_rows_have_source": counts.get("all_bundle_rows_have_source", False),
        "all_bundle_rows_have_d2_e0_eligibility": counts.get(
            "all_bundle_rows_have_d2_e0_eligibility", False
        ),
        "all_bundle_rows_have_scoring_readiness": counts.get(
            "all_bundle_rows_have_scoring_readiness", False
        ),
        "all_bundle_rows_have_future_score_component_contract": counts.get(
            "all_bundle_rows_have_future_score_component_contract", False
        ),
        "all_bundle_rows_have_future_stack_role_contract": counts.get(
            "all_bundle_rows_have_future_stack_role_contract", False
        ),
        "all_bundle_rows_have_trade_context_metadata_or_blocker": counts.get(
            "all_bundle_rows_have_trade_context_metadata_or_blocker", False
        ),
        "missing_source_row_count": counts.get("missing_source_row_count", 0),
        "duplicate_bundle_row_count": counts.get("duplicate_bundle_row_count", 0),
        "unexpected_bundle_row_count": counts.get("unexpected_bundle_row_count", 0),
        "source_record_digest_mismatch_count": counts.get(
            "source_record_digest_mismatch_count", 0
        ),
        "d2_e0_join_mismatch_count": counts.get("d2_e0_join_mismatch_count", 0),
        "scoring_readiness_join_mismatch_count": counts.get(
            "scoring_readiness_join_mismatch_count", 0
        ),
        "byte_stable_generation_result": counts.get("byte_stable_generation_result"),
        "line_ending_result": counts.get("line_ending_result"),
        "bundle_sha_file_exists": presence.bundle_sha256_exists,
        "bundle_sha_file_forbidden_absent": not presence.bundle_sha256_exists,
        "sha_freeze_authority_created": False,
        "final_readiness_authority_created": False,
        "live_order_authority_count": counts.get("live_order_authority_count", 0),
        "final_order_submission_authority_count": counts.get(
            "final_order_submission_authority_count", 0
        ),
        "live_trade_intent_authority_count": counts.get("live_trade_intent_authority_count", 0),
        "runtime_live_authority_count": counts.get("runtime_live_authority_count", 0),
        "backend_authority_count": counts.get("backend_authority_count", 0),
        "scoring_execution_allowed_count": counts.get("scoring_execution_allowed_count", 0),
        "ranking_execution_allowed_count": counts.get("ranking_execution_allowed_count", 0),
        "selection_execution_allowed_count": counts.get("selection_execution_allowed_count", 0),
        "candidate_stack_generation_allowed_count": counts.get(
            "candidate_stack_generation_allowed_count", 0
        ),
        "optimizer_execution_allowed_count": counts.get("optimizer_execution_allowed_count", 0),
        "replay_execution_allowed_count": counts.get("replay_execution_allowed_count", 0),
        "paper_execution_allowed_count": counts.get("paper_execution_allowed_count", 0),
        "source_retrieval_execution_allowed_count": counts.get(
            "source_retrieval_execution_allowed_count", 0
        ),
        "source_fact_authority_count": counts.get("source_fact_authority_count", 0),
        "connector_authority_count": counts.get("connector_authority_count", 0),
        "runtime_cash_authority_count": counts.get("runtime_cash_authority_count", 0),
        "quantum_backend_authority_count": counts.get("quantum_backend_authority_count", 0),
        "quantum_simulator_authority_count": counts.get("quantum_simulator_authority_count", 0),
        "quantum_provider_authority_count": counts.get("quantum_provider_authority_count", 0),
        "computed_score_field_count": counts.get("computed_score_field_count", 0),
        "numeric_ranking_output_count": counts.get("numeric_ranking_output_count", 0),
        "selected_stack_output_count": counts.get("selected_stack_output_count", 0),
        "selected_order_intent_output_count": counts.get("selected_order_intent_output_count", 0),
        "optimizer_output_count": counts.get("optimizer_output_count", 0),
        "replay_paper_result_count": counts.get("replay_paper_result_count", 0),
        "profit_evidence_count": counts.get("profit_evidence_count", 0),
        "expected_profit_proof_count": counts.get("expected_profit_proof_count", 0),
        "latency_superiority_evidence_count": counts.get("latency_superiority_evidence_count", 0),
        "execution_superiority_evidence_count": counts.get(
            "execution_superiority_evidence_count", 0
        ),
        "quantum_advantage_evidence_count": counts.get("quantum_advantage_evidence_count", 0),
        **family_results,
        "future_sha_freeze_state_centralization_required": FUTURE_ONLY_HANDOFF_STATE,
        "future_final_readiness_state_centralization_required": FUTURE_ONLY_HANDOFF_STATE,
        "future_runtime_live_state_centralization_required": FUTURE_ONLY_HANDOFF_STATE,
        "future_profit_evidence_state_centralization_required": FUTURE_ONLY_HANDOFF_STATE,
        "future_quantum_execution_state_centralization_required": FUTURE_ONLY_HANDOFF_STATE,
        "future_pr84_scoring_policy_handoff_ready": True,
        "future_pr85_stack_scoring_ranking_handoff_ready": True,
        "future_pr86_quantum_classical_arbitration_handoff_ready": True,
        "future_pr87_candidate_stack_generation_handoff_ready": True,
        "future_pr88_trade_context_selection_handoff_ready": True,
        "future_pr89_selected_stack_handoff_ready": True,
        "future_pr90_replay_paper_competition_handoff_ready": True,
        "forbidden_artifact_checks": {
            materializer.BUNDLE_SHA_PATH.as_posix(): {
                "exists": presence.bundle_sha256_exists,
                "expected_exists": False,
                "valid": not presence.bundle_sha256_exists,
            }
        },
        "master_plan_diff_check": _git_diff_check(
            repo_root, "docs/master_plan/QTT_MasterPlan_Current.md"
        ),
        "exact_row_source_diff_check": _git_diff_check(
            repo_root, "docs/master_plan/atomic_rows/exact_row_sources"
        ),
        "future_sha_freeze_handoff_state": FUTURE_ONLY_HANDOFF_STATE,
        "future_final_readiness_handoff_state": FUTURE_ONLY_HANDOFF_STATE,
        "validation_errors": validation_errors,
        "validation_warnings": [],
        "result_marker": SUCCESS_MARKER if result_ok else FAILURE_MARKER,
    }
    return report


def validate_report(report: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    expected_true_fields = (
        "bundle_file_exists",
        "family_distribution_match",
        "row_range_match",
        "row_order_valid",
        "all_source_rows_bundled",
        "all_bundle_rows_have_source",
        "all_bundle_rows_have_d2_e0_eligibility",
        "all_bundle_rows_have_scoring_readiness",
        "all_bundle_rows_have_future_score_component_contract",
        "all_bundle_rows_have_future_stack_role_contract",
        "all_bundle_rows_have_trade_context_metadata_or_blocker",
        "bundle_sha_file_forbidden_absent",
        "future_pr84_scoring_policy_handoff_ready",
        "future_pr85_stack_scoring_ranking_handoff_ready",
        "future_pr86_quantum_classical_arbitration_handoff_ready",
        "future_pr87_candidate_stack_generation_handoff_ready",
        "future_pr88_trade_context_selection_handoff_ready",
        "future_pr89_selected_stack_handoff_ready",
        "future_pr90_replay_paper_competition_handoff_ready",
    )
    for field in expected_true_fields:
        if report.get(field) is not True:
            failures.append(f"report.{field} must be true")
    expected_counts = {
        "bundle_row_count": source_generator.EXPECTED_TOTAL_ROWS,
        "expected_bundle_row_count": source_generator.EXPECTED_TOTAL_ROWS,
        "source_family_file_count": source_generator.EXPECTED_FAMILY_COUNT,
        "source_exact_row_record_count": source_generator.EXPECTED_TOTAL_ROWS,
        "expected_source_family_file_count": source_generator.EXPECTED_FAMILY_COUNT,
        "expected_exact_row_record_count": source_generator.EXPECTED_TOTAL_ROWS,
        "eligibility_matrix_coverage_count": source_generator.EXPECTED_TOTAL_ROWS,
        "scoring_readiness_coverage_count": source_generator.EXPECTED_TOTAL_ROWS,
        "future_score_component_input_coverage_count": source_generator.EXPECTED_TOTAL_ROWS,
        "future_stack_role_input_coverage_count": source_generator.EXPECTED_TOTAL_ROWS,
        "trade_context_metadata_or_blocker_coverage_count": source_generator.EXPECTED_TOTAL_ROWS,
    }
    for field, expected in expected_counts.items():
        if report.get(field) != expected:
            failures.append(f"report.{field} must be {expected}")
    zero_fields = (
        "missing_source_row_count",
        "duplicate_bundle_row_count",
        "unexpected_bundle_row_count",
        "source_record_digest_mismatch_count",
        "d2_e0_join_mismatch_count",
        "scoring_readiness_join_mismatch_count",
        "live_order_authority_count",
        "final_order_submission_authority_count",
        "live_trade_intent_authority_count",
        "runtime_live_authority_count",
        "backend_authority_count",
        "scoring_execution_allowed_count",
        "ranking_execution_allowed_count",
        "selection_execution_allowed_count",
        "candidate_stack_generation_allowed_count",
        "optimizer_execution_allowed_count",
        "replay_execution_allowed_count",
        "paper_execution_allowed_count",
        "source_retrieval_execution_allowed_count",
        "source_fact_authority_count",
        "connector_authority_count",
        "runtime_cash_authority_count",
        "quantum_backend_authority_count",
        "quantum_simulator_authority_count",
        "quantum_provider_authority_count",
        "computed_score_field_count",
        "numeric_ranking_output_count",
        "selected_stack_output_count",
        "selected_order_intent_output_count",
        "optimizer_output_count",
        "replay_paper_result_count",
        "profit_evidence_count",
        "expected_profit_proof_count",
        "latency_superiority_evidence_count",
        "execution_superiority_evidence_count",
        "quantum_advantage_evidence_count",
    )
    for field in zero_fields:
        if report.get(field) != 0:
            failures.append(f"report.{field} must be 0")
    expected_literals = {
        "validation_status": VALIDATION_STATUS,
        "current_expected_boundary_state": CURRENT_EXPECTED_STATE,
        "transition_from_state": TRANSITION_FROM_STATE,
        "transition_to_state": TRANSITION_TO_STATE,
        "byte_stable_generation_result": BYTE_STABLE_MATCH,
        "line_ending_result": LINE_ENDING_OK,
        "result_marker": SUCCESS_MARKER,
    }
    for field, expected in expected_literals.items():
        if report.get(field) != expected:
            failures.append(f"report.{field} must be {expected!r}")
    if report.get("bundle_sha_file_exists") is not False:
        failures.append("report.bundle_sha_file_exists must be false")
    for field in (
        "sha_freeze_authority_created",
        "final_readiness_authority_created",
    ):
        if report.get(field) is not False:
            failures.append(f"report.{field} must be false")
    for field in (
        "future_sha_freeze_state_centralization_required",
        "future_final_readiness_state_centralization_required",
        "future_runtime_live_state_centralization_required",
        "future_profit_evidence_state_centralization_required",
        "future_quantum_execution_state_centralization_required",
        "future_sha_freeze_handoff_state",
        "future_final_readiness_handoff_state",
    ):
        if report.get(field) != FUTURE_ONLY_HANDOFF_STATE:
            failures.append(f"report.{field} must be {FUTURE_ONLY_HANDOFF_STATE!r}")
    if _mapping(report.get("master_plan_diff_check")).get("unchanged") is not True:
        failures.append("docs/master_plan/QTT_MasterPlan_Current.md must remain unchanged")
    if _mapping(report.get("exact_row_source_diff_check")).get("unchanged") is not True:
        failures.append("exact-row source files must remain unchanged")
    quantum = _mapping(report.get("quantum_family_metadata_only_result"))
    if quantum.get("metadata_only") is not True or quantum.get("row_count") != 1103:
        failures.append("report.quantum_family_metadata_only_result must preserve 1103 metadata-only rows")
    for field in (
        "agent_governance_family_non_live_result",
        "source_connector_family_block_result",
        "capital_cash_family_runtime_cash_block_result",
        "latency_family_superiority_claim_block_result",
        "replay_paper_family_execution_result_block_result",
        "scoring_ranking_family_execution_block_result",
    ):
        value = _mapping(report.get(field))
        for key, item in value.items():
            if key.endswith("_count") and key != "row_count" and item != 0:
                failures.append(f"report.{field}.{key} must be 0")
        if field == "agent_governance_family_non_live_result" and value.get("non_live") is not True:
            failures.append("report.agent_governance_family_non_live_result.non_live must be true")
    if report.get("validation_errors") != []:
        failures.append("report.validation_errors must be empty")
    if report != json.loads(serialize_report(report)):
        failures.append("report serialization must be deterministic")
    return failures


def validate(
    *,
    repo_root: pathlib.Path = REPO_ROOT,
    manifest_path: pathlib.Path = DEFAULT_MANIFEST,
    schema_path: pathlib.Path = DEFAULT_SCHEMA,
    row_schema_path: pathlib.Path = DEFAULT_ROW_SCHEMA,
    report_out: pathlib.Path = DEFAULT_REPORT,
) -> ValidationResult:
    repo_root = repo_root.resolve()
    failures: list[str] = []
    try:
        manifest = load_manifest(_resolve(repo_root, manifest_path))
        schema = _load_json(_resolve(repo_root, schema_path))
        row_schema = _load_json(_resolve(repo_root, row_schema_path))
    except Exception as exc:
        return ValidationResult(False, [f"could not load PR113 validation input: {exc}"])

    failures.extend(validate_manifest_payload(manifest, schema))
    state = expected_atomicrows_bundle_state_from_contract(repo_root)
    if state is not AtomicRowsBundleState.POST_MATERIALIZATION_PRE_SHA:
        failures.append("central bundle boundary state must be POST_MATERIALIZATION_PRE_SHA")
    failures.extend(
        validate_current_atomicrows_bundle_state(
            repo_root,
            label="AtomicRows bundle materialization",
        )
    )
    bundle_failures, bundle_rows = load_bundle_rows(repo_root)
    failures.extend(bundle_failures)
    if not bundle_failures:
        row_failures, counts = validate_bundle_rows(bundle_rows, row_schema, repo_root)
        failures.extend(row_failures)
    else:
        counts = {}
    if (repo_root / materializer.BUNDLE_SHA_PATH).exists():
        failures.append("AtomicRows.bundle.sha256 must remain absent")

    report = build_report(
        repo_root=repo_root,
        counts=counts,
        rows=bundle_rows.rows,
        validation_errors=[] if not failures else failures,
    )
    if failures:
        return ValidationResult(False, failures, report)

    report_failures = validate_report(report)
    if report_failures:
        return ValidationResult(False, report_failures, report)

    report_path = _resolve(repo_root, report_out)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(serialize_report(report), encoding="utf-8", newline="\n")
    return ValidationResult(True, [], report)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=pathlib.Path, default=REPO_ROOT)
    parser.add_argument("--manifest", type=pathlib.Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--schema", type=pathlib.Path, default=DEFAULT_SCHEMA)
    parser.add_argument("--row-schema", type=pathlib.Path, default=DEFAULT_ROW_SCHEMA)
    parser.add_argument("--report-out", type=pathlib.Path, default=DEFAULT_REPORT)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    result = validate(
        repo_root=args.repo_root,
        manifest_path=args.manifest,
        schema_path=args.schema,
        row_schema_path=args.row_schema,
        report_out=args.report_out,
    )
    if not result.ok:
        for failure in result.failures:
            print(f"{FAILURE_MARKER}: {failure}", file=sys.stderr)
        return 1
    print(SUCCESS_MARKER)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
