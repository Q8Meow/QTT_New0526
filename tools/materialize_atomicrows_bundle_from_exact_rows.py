#!/usr/bin/env python3
"""Materialize the canonical AtomicRows bundle from exact-row sources.

This tool assembles a deterministic JSONL control-plane bundle only. It does
not compute SHA/freeze authority, execute scoring/ranking/selection, retrieve
or accept source facts, bind connector semantics, execute replay/paper lanes,
run optimizers, call quantum backends/simulators/providers, or create live/order
authority.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
import pathlib
import sys
from typing import Any, Sequence

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from src.qtt.core.testing.atomicrows_bundle_state import (
    CANONICAL_ATOMICROWS_BUNDLE,
    CANONICAL_ATOMICROWS_BUNDLE_SHA,
)
from tools import generate_atomicrows_exact_row_agent_family_eligibility_matrix as matrix_generator
from tools import generate_atomicrows_exact_row_source_files as source_generator
from tools import validate_atomicrows_exact_row_agent_family_eligibility_matrix as matrix_gate
from tools import validate_atomicrows_exact_row_source_materialization_manifest as source_gate


REPO_ROOT = _REPO_ROOT
BUNDLE_PATH = pathlib.Path(CANONICAL_ATOMICROWS_BUNDLE.as_posix())
BUNDLE_SHA_PATH = pathlib.Path(CANONICAL_ATOMICROWS_BUNDLE_SHA.as_posix())
MATRIX_PATH = matrix_generator.DEFAULT_MANIFEST
SUCCESS_MARKER = "QTT_ATOMICROWS_BUNDLE_MATERIALIZATION_GENERATED"
FAILURE_MARKER = "QTT_ATOMICROWS_BUNDLE_MATERIALIZATION_FAILED"

BUNDLE_ROW_VERSION = "v1"
AUTHORITY_CLASS = (
    "STATIC_ATOMICROWS_BUNDLE_FILE_MATERIALIZATION_ONLY_NOT_SHA_NOT_FREEZE_"
    "NOT_FINAL_READINESS_NOT_RUNTIME_NOT_LIVE_NOT_SCORING_EXECUTION_NOT_SELECTION"
)
MATERIALIZATION_STATE = "POST_MATERIALIZATION_PRE_SHA"
TRANSITION_FROM_STATE = "PRE_MATERIALIZATION"
TRANSITION_TO_STATE = "POST_MATERIALIZATION_PRE_SHA"

FUTURE_ONLY_HANDOFF_STATE = "REQUIRED_FUTURE_ONLY_NOT_EXECUTED"
QUANTUM_FORWARD_FAMILIES = set(source_generator.QUANTUM_FORWARD_FAMILY_IDS)


@dataclass(frozen=True)
class SourceRowLine:
    row: dict[str, Any]
    raw_line: str
    digest: str
    stable_identity: str


def _resolve(repo_root: pathlib.Path, path: pathlib.Path | pathlib.PurePosixPath) -> pathlib.Path:
    concrete = pathlib.Path(*path.parts) if isinstance(path, pathlib.PurePosixPath) else path
    return concrete if concrete.is_absolute() else repo_root / concrete


def _stable_source_identity(row: dict[str, Any]) -> str:
    return (
        f"{row['row_id']}::{row['row_index']}::{row['family_id']}::"
        f"{row['source_file_path']}"
    )


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _json_loads_object(line: str, *, location: str) -> dict[str, Any]:
    value = json.loads(line)
    if not isinstance(value, dict):
        raise ValueError(f"{location} must be a JSON object")
    return value


def load_exact_source_rows(repo_root: pathlib.Path = REPO_ROOT) -> list[SourceRowLine]:
    repo_root = repo_root.resolve()
    rows: list[SourceRowLine] = []
    seen_ids: set[str] = set()
    seen_indexes: set[int] = set()
    for plan in source_generator.build_family_plans():
        path = _resolve(repo_root, pathlib.Path(plan.exact_rows_file_path))
        if not path.exists():
            raise ValueError(f"missing exact-row source file: {plan.exact_rows_file_path}")
        raw = path.read_bytes()
        if not raw.endswith(b"\n"):
            raise ValueError(f"{plan.exact_rows_file_path} must end with LF")
        text = raw.decode("utf-8")
        lines = text.splitlines()
        if len(lines) != plan.row_count:
            raise ValueError(f"{plan.exact_rows_file_path} line count must be {plan.row_count}")
        for family_row_index, line in enumerate(lines, start=1):
            if not line.strip():
                raise ValueError(f"{plan.exact_rows_file_path}:{family_row_index} is blank")
            row = _json_loads_object(
                line,
                location=f"{plan.exact_rows_file_path}:{family_row_index}",
            )
            row_id = row.get("row_id")
            row_index = row.get("row_index")
            if not isinstance(row_id, str):
                raise ValueError(f"{plan.exact_rows_file_path}:{family_row_index} row_id must be string")
            if not isinstance(row_index, int) or isinstance(row_index, bool):
                raise ValueError(f"{row_id}.row_index must be integer")
            if row_id in seen_ids:
                raise ValueError(f"duplicate exact source row_id: {row_id}")
            if row_index in seen_indexes:
                raise ValueError(f"duplicate exact source row_index: {row_index}")
            seen_ids.add(row_id)
            seen_indexes.add(row_index)
            expected = {
                "family_id": plan.family_id,
                "family_label": plan.family_label,
                "family_row_ordinal": family_row_index,
                "family_start_row_index": plan.start_row_index,
                "family_end_row_index": plan.end_row_index,
                "source_file_path": plan.exact_rows_file_path,
            }
            for field, expected_value in expected.items():
                if row.get(field) != expected_value:
                    raise ValueError(f"{row_id}.{field} must be {expected_value!r}")
            rows.append(
                SourceRowLine(
                    row=row,
                    raw_line=line,
                    digest=_sha256_text(line),
                    stable_identity=_stable_source_identity(row),
                )
            )
    rows.sort(key=lambda item: item.row["row_index"])
    expected_indexes = list(range(1, source_generator.EXPECTED_TOTAL_ROWS + 1))
    observed_indexes = [item.row["row_index"] for item in rows]
    if observed_indexes != expected_indexes:
        raise ValueError("exact source rows must cover row_index 1..4183 in order")
    return rows


def load_d2_e0_records(repo_root: pathlib.Path = REPO_ROOT) -> dict[str, dict[str, Any]]:
    repo_root = repo_root.resolve()
    manifest = matrix_gate.load_manifest(_resolve(repo_root, MATRIX_PATH))
    records = manifest.get("row_coverage_records")
    if not isinstance(records, list):
        raise ValueError("D2/E0 row_coverage_records must be an array")
    by_id: dict[str, dict[str, Any]] = {}
    for record in records:
        if not isinstance(record, dict):
            raise ValueError("D2/E0 row_coverage_records entries must be objects")
        row_id = record.get("exact_row_id")
        if not isinstance(row_id, str):
            raise ValueError("D2/E0 exact_row_id must be string")
        if row_id in by_id:
            raise ValueError(f"duplicate D2/E0 exact_row_id: {row_id}")
        by_id[row_id] = record
    if len(by_id) != source_generator.EXPECTED_TOTAL_ROWS:
        raise ValueError("D2/E0 coverage must contain exactly 4183 records")
    return by_id


def _blocked_score_components(record: dict[str, Any]) -> list[str]:
    blocked = record.get("blocked_future_score_components")
    if not isinstance(blocked, list):
        return []
    return [item for item in blocked if isinstance(item, str)]


def _eligible_score_components(record: dict[str, Any]) -> list[str]:
    eligible = record.get("eligible_future_score_components")
    if not isinstance(eligible, list):
        return []
    return [item for item in eligible if isinstance(item, str)]


def _eligible_stack_roles(record: dict[str, Any]) -> list[str]:
    eligible = record.get("eligible_future_stack_roles")
    if not isinstance(eligible, list):
        return []
    return [item for item in eligible if isinstance(item, str)]


def _blocked_stack_roles(record: dict[str, Any]) -> list[dict[str, Any]]:
    blocked = record.get("blocked_future_stack_roles")
    if not isinstance(blocked, list):
        return []
    return [item for item in blocked if isinstance(item, dict)]


def _authority_boundary(record: dict[str, Any]) -> dict[str, bool]:
    fields = (
        "live_order_authority_allowed",
        "final_order_submission_authority_allowed",
        "live_trade_intent_authority_allowed",
        "scoring_execution_allowed",
        "ranking_execution_allowed",
        "selection_execution_allowed",
        "candidate_stack_generation_allowed",
        "optimizer_execution_allowed",
        "replay_execution_allowed",
        "paper_execution_allowed",
        "source_fact_authority_allowed",
        "connector_authority_allowed",
        "runtime_cash_authority_allowed",
        "quantum_backend_authority_allowed",
        "quantum_simulator_authority_allowed",
        "quantum_provider_authority_allowed",
        "profit_evidence_allowed",
        "expected_profit_proof_allowed",
        "latency_superiority_evidence_allowed",
        "execution_superiority_evidence_allowed",
        "quantum_advantage_evidence_allowed",
        "bundle_authority_allowed",
        "sha_freeze_authority_allowed",
        "final_readiness_authority_allowed",
    )
    return {field: record.get(field) is True for field in fields}


def _validate_join(source: SourceRowLine, d2_e0: dict[str, Any]) -> None:
    row = source.row
    row_id = row["row_id"]
    expected = {
        "exact_row_id": row_id,
        "row_index": row["row_index"],
        "family_id": row["family_id"],
        "family_name": row["family_label"],
        "source_file": row["source_file_path"],
        "source_record_stable_identity": source.stable_identity,
        "source_record_digest": source.digest,
        "source_row_class": row["row_class"],
        "source_subfamily_id": row["subfamily_id"],
        "source_quantum_metadata_class": row["quantum_metadata"]["quantum_metadata_class"],
    }
    for field, expected_value in expected.items():
        if d2_e0.get(field) != expected_value:
            raise ValueError(f"{row_id} D2/E0 join mismatch for {field}")
    if not _eligible_score_components(d2_e0) and not _blocked_score_components(d2_e0):
        raise ValueError(f"{row_id} must have future score-component eligibility or blocks")
    if not _eligible_stack_roles(d2_e0) and not _blocked_stack_roles(d2_e0):
        raise ValueError(f"{row_id} must have future stack-role eligibility or blocks")
    if not isinstance(d2_e0.get("trade_context_applicability_metadata"), dict):
        raise ValueError(f"{row_id} must have trade-context metadata")


def _family_boundary_reason_codes(family_id: str) -> list[str]:
    reasons = ["PR113_STATIC_BUNDLE_ROW_MATERIALIZED"]
    if family_id == "002_scoring_ranking":
        reasons.append("PR113_BLOCK_SCORING_RANKING_EXECUTION")
    if family_id == "006_capital_sizing_cash":
        reasons.append("PR113_BLOCK_RUNTIME_CASH_RECEIPTS")
    if family_id == "007_latency_routing":
        reasons.append("PR113_BLOCK_LATENCY_SUPERIORITY_EVIDENCE")
    if family_id == "009_lifecycle_agent_binding":
        reasons.append("PR113_AGENT_GOVERNANCE_NON_LIVE")
    if family_id == "010_source_evidence_connector_semantic":
        reasons.append("PR113_BLOCK_SOURCE_FACT_AND_CONNECTOR_SEMANTIC_AUTHORITY")
    if family_id == "011_replay_paper_validation":
        reasons.append("PR113_BLOCK_REPLAY_PAPER_EXECUTION_AND_RESULTS")
    if family_id in QUANTUM_FORWARD_FAMILIES:
        reasons.append("PR113_QUANTUM_METADATA_ONLY_NO_BACKEND_SIMULATOR_PROVIDER")
        reasons.append("PR113_BLOCK_QUANTUM_ADVANTAGE_CLAIM")
    return reasons


def build_bundle_row(source: SourceRowLine, d2_e0: dict[str, Any]) -> dict[str, Any]:
    _validate_join(source, d2_e0)
    row = source.row
    family_id = row["family_id"]
    authority_boundary = _authority_boundary(d2_e0)
    return {
        "bundle_row_id": f"AR_BUNDLE_ROW_{row['row_index']:04d}",
        "bundle_row_version": BUNDLE_ROW_VERSION,
        "bundle_materialized": True,
        "bundle_materialization_authority_class": AUTHORITY_CLASS,
        "current_expected_boundary_state": MATERIALIZATION_STATE,
        "transition_from_state": TRANSITION_FROM_STATE,
        "transition_to_state": TRANSITION_TO_STATE,
        "exact_row_id": row["row_id"],
        "row_index": row["row_index"],
        "family_id": family_id,
        "family_name": row["family_label"],
        "family_row_index": row["family_row_ordinal"],
        "source_file": row["source_file_path"],
        "source_record_digest": source.digest,
        "source_record_stable_identity": source.stable_identity,
        "source_record": row,
        "source_row_class": row["row_class"],
        "source_subfamily_id": row["subfamily_id"],
        "source_quantum_metadata_class": row["quantum_metadata"]["quantum_metadata_class"],
        "d2_e0_agent_family_eligibility": {
            "agent_family_eligibility_decision": d2_e0["agent_family_eligibility_decision"],
            "agent_family_eligibility_reason_codes": d2_e0["agent_family_eligibility_reason_codes"],
            "allowed_agent_family_classes": d2_e0["allowed_agent_family_classes"],
            "blocked_agent_family_classes": d2_e0["blocked_agent_family_classes"],
            "allowed_static_actions": d2_e0["allowed_static_actions"],
            "blocked_authority_classes": d2_e0["blocked_authority_classes"],
        },
        "d2_e0_scoring_ranking_readiness": {
            "scoring_readiness_decision": d2_e0["scoring_readiness_decision"],
            "scoring_readiness_reason_codes": d2_e0["scoring_readiness_reason_codes"],
            "eligible_future_score_components": d2_e0["eligible_future_score_components"],
            "blocked_future_score_components": d2_e0["blocked_future_score_components"],
            "eligible_future_stack_roles": d2_e0["eligible_future_stack_roles"],
            "blocked_future_stack_roles": d2_e0["blocked_future_stack_roles"],
            "candidate_stack_generation_eligible_future_only": d2_e0[
                "candidate_stack_generation_eligible_future_only"
            ],
            "ranking_contract_input_eligible_future_only": d2_e0[
                "ranking_contract_input_eligible_future_only"
            ],
            "selection_contract_input_eligible_future_only": d2_e0[
                "selection_contract_input_eligible_future_only"
            ],
            "optimizer_arbitration_input_eligible_future_only": d2_e0[
                "optimizer_arbitration_input_eligible_future_only"
            ],
            "replay_paper_competition_input_eligible_future_only": d2_e0[
                "replay_paper_competition_input_eligible_future_only"
            ],
        },
        "eligible_future_score_components": d2_e0["eligible_future_score_components"],
        "blocked_future_score_components": d2_e0["blocked_future_score_components"],
        "eligible_future_stack_roles": d2_e0["eligible_future_stack_roles"],
        "blocked_future_stack_roles": d2_e0["blocked_future_stack_roles"],
        "trade_context_applicability_metadata": d2_e0[
            "trade_context_applicability_metadata"
        ],
        "platform_applicability_metadata_only": d2_e0[
            "platform_applicability_metadata_only"
        ],
        "market_type_applicability_metadata_only": d2_e0[
            "market_type_applicability_metadata_only"
        ],
        "strategy_fit_metadata_only": d2_e0["strategy_fit_metadata_only"],
        "latency_fit_metadata_only": d2_e0["latency_fit_metadata_only"],
        "risk_fit_metadata_only": d2_e0["risk_fit_metadata_only"],
        "capital_fit_metadata_only": d2_e0["capital_fit_metadata_only"],
        "source_currentness_dependency_class": d2_e0[
            "source_currentness_dependency_class"
        ],
        "runtime_readiness_dependency_class": d2_e0[
            "runtime_readiness_dependency_class"
        ],
        "replay_paper_dependency_class": d2_e0["replay_paper_dependency_class"],
        "quantum_applicability_metadata_class": d2_e0[
            "quantum_applicability_metadata_class"
        ],
        "owner_priority_applicability_metadata_only": d2_e0[
            "owner_priority_applicability_metadata_only"
        ],
        "candidate_stack_generation_eligible_future_only": d2_e0[
            "candidate_stack_generation_eligible_future_only"
        ],
        "ranking_contract_input_eligible_future_only": d2_e0[
            "ranking_contract_input_eligible_future_only"
        ],
        "selection_contract_input_eligible_future_only": d2_e0[
            "selection_contract_input_eligible_future_only"
        ],
        "optimizer_arbitration_input_eligible_future_only": d2_e0[
            "optimizer_arbitration_input_eligible_future_only"
        ],
        "replay_paper_competition_input_eligible_future_only": d2_e0[
            "replay_paper_competition_input_eligible_future_only"
        ],
        "quantum_metadata_policy": {
            "family_id": family_id,
            "quantum_forward_family": family_id in QUANTUM_FORWARD_FAMILIES,
            "source_quantum_metadata": row["quantum_metadata"],
            "quantum_metadata_only": row["quantum_metadata"].get(
                "quantum_forward_family_flag"
            )
            is True,
            "quantum_backend_authority_allowed": False,
            "quantum_simulator_authority_allowed": False,
            "quantum_provider_authority_allowed": False,
            "quantum_advantage_claim_allowed": False,
            "quantum_live_order_authority_allowed": False,
        },
        "owner_override_policy": {
            "owner_override_applicability": d2_e0["owner_override_applicability"],
            "owner_override_limits": d2_e0["owner_override_limits"],
        },
        "runtime_live_authority_boundary": {
            "live_order_authority_allowed": authority_boundary["live_order_authority_allowed"],
            "final_order_submission_authority_allowed": authority_boundary[
                "final_order_submission_authority_allowed"
            ],
            "live_trade_intent_authority_allowed": authority_boundary[
                "live_trade_intent_authority_allowed"
            ],
            "runtime_cash_authority_allowed": authority_boundary[
                "runtime_cash_authority_allowed"
            ],
            "runtime_live_authority_allowed": False,
            "backend_authority_allowed": False,
            "profit_evidence_allowed": authority_boundary["profit_evidence_allowed"],
        },
        "source_connector_authority_boundary": {
            "source_fact_authority_allowed": authority_boundary[
                "source_fact_authority_allowed"
            ],
            "connector_authority_allowed": authority_boundary["connector_authority_allowed"],
            "source_retrieval_execution_allowed": False,
            "source_acceptance_execution_allowed": False,
            "connector_semantic_binding_execution_allowed": False,
        },
        "execution_authority_boundary": {
            "scoring_execution_allowed": authority_boundary["scoring_execution_allowed"],
            "ranking_execution_allowed": authority_boundary["ranking_execution_allowed"],
            "selection_execution_allowed": authority_boundary["selection_execution_allowed"],
            "candidate_stack_generation_allowed": authority_boundary[
                "candidate_stack_generation_allowed"
            ],
            "optimizer_execution_allowed": authority_boundary["optimizer_execution_allowed"],
            "replay_execution_allowed": authority_boundary["replay_execution_allowed"],
            "paper_execution_allowed": authority_boundary["paper_execution_allowed"],
            "quantum_backend_authority_allowed": authority_boundary[
                "quantum_backend_authority_allowed"
            ],
            "quantum_simulator_authority_allowed": authority_boundary[
                "quantum_simulator_authority_allowed"
            ],
            "quantum_provider_authority_allowed": authority_boundary[
                "quantum_provider_authority_allowed"
            ],
        },
        "evidence_authority_boundary": {
            "profit_evidence_allowed": authority_boundary["profit_evidence_allowed"],
            "expected_profit_proof_allowed": authority_boundary[
                "expected_profit_proof_allowed"
            ],
            "latency_superiority_evidence_allowed": authority_boundary[
                "latency_superiority_evidence_allowed"
            ],
            "execution_superiority_evidence_allowed": authority_boundary[
                "execution_superiority_evidence_allowed"
            ],
            "quantum_advantage_evidence_allowed": authority_boundary[
                "quantum_advantage_evidence_allowed"
            ],
        },
        "future_handoff_metadata": {
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
        },
        "d2_e0_authority_boundaries": authority_boundary,
        "validation_reason_codes": (
            list(d2_e0["agent_family_eligibility_reason_codes"])
            + list(d2_e0["scoring_readiness_reason_codes"])
            + _family_boundary_reason_codes(family_id)
        ),
    }


def assemble_bundle_rows(repo_root: pathlib.Path = REPO_ROOT) -> list[dict[str, Any]]:
    source_rows = load_exact_source_rows(repo_root)
    d2_e0_by_id = load_d2_e0_records(repo_root)
    bundle_rows: list[dict[str, Any]] = []
    for source in source_rows:
        row_id = source.row["row_id"]
        d2_e0 = d2_e0_by_id.get(row_id)
        if d2_e0 is None:
            raise ValueError(f"missing D2/E0 coverage for {row_id}")
        bundle_rows.append(build_bundle_row(source, d2_e0))
    if len(bundle_rows) != source_generator.EXPECTED_TOTAL_ROWS:
        raise ValueError("bundle must contain exactly 4183 rows")
    return bundle_rows


def render_bundle_bytes(bundle_rows: Sequence[dict[str, Any]]) -> bytes:
    lines = [
        json.dumps(row, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        for row in bundle_rows
    ]
    return ("\n".join(lines) + "\n").encode("utf-8")


def validate_upstream_inputs(repo_root: pathlib.Path) -> None:
    source_result = source_gate.validate(repo_root=repo_root)
    if not source_result.ok:
        raise ValueError(
            "exact-row source materialization validation failed: "
            + "; ".join(source_result.failures)
        )
    matrix_result = matrix_gate.validate(repo_root=repo_root)
    if not matrix_result.ok:
        raise ValueError(
            "D2/E0 exact-row agent-family eligibility validation failed: "
            + "; ".join(matrix_result.failures)
        )


def materialize_bundle(repo_root: pathlib.Path = REPO_ROOT) -> tuple[pathlib.Path, bool]:
    repo_root = repo_root.resolve()
    validate_upstream_inputs(repo_root)
    sha_path = _resolve(repo_root, BUNDLE_SHA_PATH)
    if sha_path.exists():
        raise ValueError(f"forbidden SHA/freeze artifact exists: {BUNDLE_SHA_PATH.as_posix()}")
    bundle_rows = assemble_bundle_rows(repo_root)
    desired = render_bundle_bytes(bundle_rows)
    bundle_path = _resolve(repo_root, BUNDLE_PATH)
    if bundle_path.exists() and bundle_path.read_bytes() == desired:
        return bundle_path, False
    bundle_path.parent.mkdir(parents=True, exist_ok=True)
    bundle_path.write_bytes(desired)
    return bundle_path, True


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=pathlib.Path, default=REPO_ROOT)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        materialize_bundle(args.repo_root)
    except Exception as exc:
        print(f"{FAILURE_MARKER}: {exc}", file=sys.stderr)
        return 1
    print(SUCCESS_MARKER)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
