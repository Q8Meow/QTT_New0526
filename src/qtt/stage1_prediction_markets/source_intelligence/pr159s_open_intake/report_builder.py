"""Deterministic PR159S artifact construction."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
import subprocess
from typing import Any, Mapping

from . import constants as c
from .algorithm_formula_extractor import build_algorithm_formula_candidate_records
from .artifact_discovery import (
    fallback_crosswalk_path_used,
    input_consumption_receipts,
    selected_artifact_paths,
)
from .atomicrows_candidate_mapper import build_atomicrows_candidate_records
from .atomicrows_source_profit_readiness import build_atomicrows_source_profit_readiness_records
from .io import as_list, as_mapping, read_json, record_count, stable_counter, write_json
from .models import BuildArtifacts
from .official_confirmed_backfill import build_backfill_records
from .official_fact_extractor import build_official_fact_delta_records
from .open_source_intake import build_open_research_source_records
from .profit_validation_state import build_profit_validation_records
from .quantum_candidate_classifier import build_quantum_candidate_records
from .replay_paper_candidate_router import build_replay_paper_candidate_routes
from .research_candidate_extractor import build_research_candidate_records
from .source_profit_provenance import (
    classify_target,
    is_testable_target,
    profit_validation_bucket,
    source_provenance_bucket,
)
from .source_taxonomy import build_source_taxonomy_records, taxonomy_counts
from .target_loader import inventory_counts, load_input_targets
from .terminal_completion import terminal_partition_template


def _load(root: Path, rel_path: Path) -> Mapping[str, Any]:
    path = root / rel_path
    if not path.exists():
        return {}
    return as_mapping(read_json(path))


def _records(payload: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    return [as_mapping(record) for record in as_list(payload.get("records"))]


def _git_stdout(root: Path, args: list[str]) -> tuple[int, str, str]:
    completed = subprocess.run(
        ["git", *args],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    return completed.returncode, completed.stdout.strip(), completed.stderr.strip()


def repo_preflight_receipt(root: Path) -> dict[str, Any]:
    branch_rc, branch, _branch_err = _git_stdout(root, ["branch", "--show-current"])
    head_rc, head, _head_err = _git_stdout(root, ["rev-parse", "HEAD"])
    status_rc, status, _status_err = _git_stdout(root, ["status", "--short"])
    return {
        "receipt_id": "PR159S_REPO_PREFLIGHT_RECEIPT",
        "repo_root": root.as_posix(),
        "branch": branch if branch_rc == 0 else "DETACHED_HEAD",
        "head_commit": head if head_rc == 0 else None,
        "expected_branch": c.EXPECTED_BRANCH,
        "preferred_branch_active_flag": branch == c.EXPECTED_BRANCH,
        "worktree_clean_at_build_start_flag": status_rc == 0 and status == "",
        "commit_push_pr_merge_performed_by_pr159s_flag": False,
        "no_authority_confirmation": dict(c.NO_AUTHORITY_CONFIRMATION),
    }


def _prior_counts(root: Path) -> dict[str, Any]:
    return {
        "pr154_universe": c.EXPECTED_PR154_UNIVERSE,
        "atomicrows_overlay_universe": c.EXPECTED_ATOMICROWS_UNIVERSE,
        "pr159_accepted_packets": record_count(_load(root, c.PR159_ACCEPTED_PACKET_REGISTRY)),
        "pr159r_accepted_packets_after_second_pass": record_count(
            _load(root, c.PR159R_ACCEPTED_PACKET_REGISTRY)
        ),
        "pr159r_unresolved_after_repair": record_count(_load(root, c.PR159R_UNRESOLVED_FILL_PATH)),
        "pr160_route_partition_processed": record_count(_load(root, c.PR160_ROUTE_CLOSURE_REPORT)),
        "pr160_pr159r_requeue_processed": record_count(_load(root, c.PR160_REQUEUE_REPORT)),
        "pr152_deterministic_audit_present": (root / c.PR152_AUDIT_REPORT).exists(),
    }


def _classify_targets(targets: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    testable_sequence = 0
    classified: list[dict[str, Any]] = []
    for target in targets:
        sequence_for_target: int | None = None
        if is_testable_target(target):
            testable_sequence += 1
            sequence_for_target = testable_sequence
        classification = classify_target(target, sequence_for_target)
        classified.append(
            {
                "completion_record_id": f"PR159S_COMPLETION__{len(classified)+1:04d}",
                "target_id_or_row_id": target.get("target_id_or_row_id"),
                "target_population": target.get("target_population"),
                "target_field_id": target.get("target_field_id"),
                "source_family": target.get("source_family"),
                "atomicrows_linked_flag": target.get("atomicrows_linked_flag"),
                "family_id": target.get("family_id"),
                "parameter_id": target.get("parameter_id"),
                "platform_scope": target.get("platform_scope") or _platform_from_target(str(target.get("target_id_or_row_id"))),
                "market_scope": target.get("market_scope") or _market_scope_from_target(str(target.get("target_id_or_row_id"))),
                "prior_pr159r_state": target.get("final_PR159R_target_state"),
                "prior_pr159r_future_route": target.get("future_PR_route"),
                "input_inventory_source": target.get("input_inventory_source"),
                "open_intake_lanes_attempted": [
                    "target_identity_lock",
                    "existing_accepted_reuse_scan",
                    "official_confirmed_backfill_scan",
                    "official_source_route_classification",
                    "open_research_source_intake",
                    "algorithm_formula_parameter_extraction",
                    "atomicrows_compatibility_mapping",
                    "replay_paper_candidate_routing",
                    "quantum_forward_classification",
                    "source_profit_provenance_classification",
                    "terminal_completion",
                ],
                **classification,
                "no_authority_confirmation": dict(c.NO_AUTHORITY_CONFIRMATION),
            }
        )
    return classified


def _platform_from_target(target_id: str) -> str:
    for platform in ("KALSHI", "POLYMARKET", "FORECASTEX_IBKR"):
        if platform in target_id:
            return platform
    return "PREDICTION_MARKETS_GENERAL"


def _market_scope_from_target(target_id: str) -> str:
    if "PREDICTION_MARKETS_GENERAL" in target_id:
        return "PREDICTION_MARKETS_GENERAL"
    return "PREDICTION_MARKET_SOURCE_TARGET"


def _terminal_partition(records: list[Mapping[str, Any]]) -> dict[str, int]:
    partition = terminal_partition_template()
    for record in records:
        partition[str(record.get("terminal_completion_state"))] += 1
    return partition


def _source_provenance_partition(records: list[Mapping[str, Any]]) -> dict[str, int]:
    keys = (
        "official_confirmed_total",
        "official_candidate_pending_exact_field_total",
        "open_research_untested_total",
        "open_research_testable_total",
        "non_official_profit_proven_total",
        "non_official_non_profitable_total",
        "mixed_official_and_research_total",
        "owner_policy_input_total",
        "quarantined_or_rejected_total",
    )
    partition = {key: 0 for key in keys}
    for record in records:
        partition[source_provenance_bucket(record)] += 1
    return partition


def _profit_partition(records: list[Mapping[str, Any]]) -> dict[str, int]:
    keys = (
        "profit_not_tested_total",
        "replay_profitable_total",
        "paper_profitable_total",
        "replay_and_paper_profitable_total",
        "replay_non_profitable_total",
        "paper_non_profitable_total",
        "replay_and_paper_non_profitable_total",
        "replay_paper_conflicting_total",
        "replay_paper_inconclusive_total",
        "promotion_evidence_not_in_scope_total",
    )
    partition = {key: 0 for key in keys}
    for record in records:
        partition[profit_validation_bucket(record)] += 1
    return partition


def _atomicrows_counts(records: list[Mapping[str, Any]]) -> dict[str, int]:
    atomic = [record for record in records if record.get("atomicrows_linked_flag")]
    return {
        "atomicrows_candidate_ready_count": len(atomic),
        "atomicrows_official_source_ready_count": 0,
        "atomicrows_all_official_confirmed_count": 0,
        "atomicrows_partial_official_confirmed_count": 0,
        "atomicrows_research_candidate_only_count": sum(
            1
            for record in atomic
            if record.get("row_level_aggregate_provenance_tag")
            == c.RowLevelAggregateProvenanceTag.ROW_RESEARCH_CANDIDATE_ONLY.value
        ),
        "atomicrows_mixed_official_and_research_count": 0,
        "atomicrows_replay_paper_profit_proven_count": 0,
        "atomicrows_non_profitable_retired_count": 0,
        "atomicrows_replay_paper_candidate_ready_count": sum(
            1 for record in atomic if record.get("replay_paper_candidate_flag") is True
        ),
    }


def count_invariant_receipt(records: list[Mapping[str, Any]], backfill_records: list[Mapping[str, Any]]) -> dict[str, Any]:
    inventory = {
        "processed_total": len(records),
        "processed_atomicrows": sum(1 for record in records if record.get("source_family") == "ATOMICROWS"),
        "processed_pr154": sum(1 for record in records if record.get("source_family") == "PR154"),
    }
    terminal_partition = _terminal_partition(records)
    provenance_partition = _source_provenance_partition(records)
    profit_partition = _profit_partition(records)
    ids = [str(record.get("target_id_or_row_id")) for record in records]
    terminal_total = sum(terminal_partition.values())
    provenance_total = sum(provenance_partition.values())
    profit_total = sum(profit_partition.values())
    receipt: dict[str, Any] = {
        **inventory,
        "input_total": c.EXPECTED_INPUT_TOTAL,
        "atomicrows_input": c.EXPECTED_ATOMICROWS_INPUT,
        "pr154_input": c.EXPECTED_PR154_INPUT,
        "terminal_completion_total": terminal_total,
        "source_profit_classified_total": provenance_total,
        "profit_validation_classified_total": profit_total,
        "orphan_target_count": len(ids) - len(set(ids)),
        "generic_blocker_count": 0,
        "terminal_completion_partition": terminal_partition,
        "source_provenance_partition": provenance_partition,
        "profit_validation_partition": profit_partition,
        "official_external_fact_completions": terminal_partition[
            c.TerminalCompletionState.COMPLETED_AS_OFFICIAL_EXTERNAL_FACT.value
        ],
        "official_confirmed_total": provenance_partition["official_confirmed_total"],
        "official_confirmed_reused_from_previous_pr_total": len(backfill_records),
        "official_candidate_pending_exact_field_total": provenance_partition[
            "official_candidate_pending_exact_field_total"
        ],
        "open_research_input_completions": terminal_partition[
            c.TerminalCompletionState.COMPLETED_AS_OPEN_RESEARCH_INPUT.value
        ],
        "open_research_untested_total": provenance_partition["open_research_untested_total"],
        "open_research_testable_total": provenance_partition["open_research_testable_total"],
        "algorithm_candidate_completions": terminal_partition[
            c.TerminalCompletionState.COMPLETED_AS_ALGORITHM_CANDIDATE.value
        ],
        "formula_candidate_completions": terminal_partition[
            c.TerminalCompletionState.COMPLETED_AS_FORMULA_CANDIDATE.value
        ],
        "parameter_candidate_completions": terminal_partition[
            c.TerminalCompletionState.COMPLETED_AS_PARAMETER_CANDIDATE.value
        ],
        "edge_hypothesis_candidate_completions": terminal_partition[
            c.TerminalCompletionState.COMPLETED_AS_EDGE_HYPOTHESIS_CANDIDATE.value
        ],
        "microstructure_candidate_completions": terminal_partition[
            c.TerminalCompletionState.COMPLETED_AS_MICROSTRUCTURE_CANDIDATE.value
        ],
        "replay_paper_candidate_completions": terminal_partition[
            c.TerminalCompletionState.COMPLETED_AS_REPLAY_PAPER_TEST_CANDIDATE.value
        ],
        "replay_paper_candidate_route_count": sum(
            1 for record in records if record.get("replay_paper_candidate_flag") is True
        ),
        "quantum_candidate_completions": terminal_partition[
            c.TerminalCompletionState.COMPLETED_AS_QUANTUM_CANDIDATE.value
        ],
        "classical_candidate_completions": terminal_partition[
            c.TerminalCompletionState.COMPLETED_AS_CLASSICAL_CANDIDATE.value
        ],
        "hybrid_candidate_completions": terminal_partition[
            c.TerminalCompletionState.COMPLETED_AS_HYBRID_CANDIDATE.value
        ],
        "connector_future_route_completions": terminal_partition[
            c.TerminalCompletionState.COMPLETED_AS_CONNECTOR_FUTURE_ROUTE.value
        ],
        "non_official_profit_proven_total": provenance_partition["non_official_profit_proven_total"],
        "non_official_non_profitable_total": provenance_partition["non_official_non_profitable_total"],
        "mixed_official_and_research_total": provenance_partition["mixed_official_and_research_total"],
        **profit_partition,
        **_atomicrows_counts(records),
        "pr154_terminal_completion_count": sum(1 for record in records if record.get("source_family") == "PR154"),
        "count_invariants_passed_flag": (
            len(records) == c.EXPECTED_INPUT_TOTAL
            and inventory["processed_atomicrows"] == c.EXPECTED_ATOMICROWS_INPUT
            and inventory["processed_pr154"] == c.EXPECTED_PR154_INPUT
            and terminal_total == c.EXPECTED_INPUT_TOTAL
            and provenance_total == c.EXPECTED_INPUT_TOTAL
            and profit_total == c.EXPECTED_INPUT_TOTAL
            and len(ids) == len(set(ids))
        ),
    }
    return receipt


def _common_payload(
    report_type: str,
    records: list[Mapping[str, Any]],
    count_receipt: Mapping[str, Any],
    receipts: list[Mapping[str, Any]],
    **extra: Any,
) -> dict[str, Any]:
    return {
        "pr_id": c.PR_ID,
        "semantic_task_id": c.SEMANTIC_TASK_ID,
        "implementation_class": c.IMPLEMENTATION_CLASS,
        "authority_class": c.AUTHORITY_CLASS,
        "report_type": report_type,
        "record_count": len(records),
        "records": records,
        "central_enum_value_sets": c.CENTRAL_ENUM_VALUE_SETS,
        "count_invariant_receipt": count_receipt,
        "input_consumption_receipt": receipts,
        "no_authority_confirmation": dict(c.NO_AUTHORITY_CONFIRMATION),
        "validation_result": "PASS_PENDING_VALIDATOR",
        **c.ZERO_AUTHORITY_COUNTS,
        **extra,
    }


def _inventory_records(targets: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "inventory_record_id": f"PR159S_INPUT_TARGET__{index:04d}",
            "target_id_or_row_id": target.get("target_id_or_row_id"),
            "target_population": target.get("target_population"),
            "target_field_id": target.get("target_field_id"),
            "source_family": target.get("source_family"),
            "atomicrows_linked_flag": target.get("atomicrows_linked_flag"),
            "input_inventory_source": target.get("input_inventory_source"),
            "prior_pr159r_state": target.get("final_PR159R_target_state"),
            "prior_pr159r_future_route": target.get("future_PR_route"),
        }
        for index, target in enumerate(targets, start=1)
    ]


def build_artifacts(root: Path) -> BuildArtifacts:
    receipts = input_consumption_receipts(root)
    targets = load_input_targets(root)
    classified_targets = _classify_targets(targets)
    backfill_records = build_backfill_records(root)
    count_receipt = count_invariant_receipt(classified_targets, backfill_records)

    source_taxonomy_records = build_source_taxonomy_records()
    open_research_records = build_open_research_source_records(classified_targets)
    official_delta_records = build_official_fact_delta_records(classified_targets)
    algorithm_formula_records = build_algorithm_formula_candidate_records(classified_targets)
    atomicrows_candidate_records = build_atomicrows_candidate_records(classified_targets)
    replay_paper_records = build_replay_paper_candidate_routes(classified_targets)
    quantum_records = build_quantum_candidate_records(classified_targets)
    profit_records = build_profit_validation_records(classified_targets)
    atomicrows_source_profit_records = build_atomicrows_source_profit_readiness_records(
        atomicrows_candidate_records
    )

    payloads: dict[str, dict[str, Any]] = {}
    payloads[c.ORCHESTRATION_PREFLIGHT_PATH.as_posix()] = _common_payload(
        "PR159S_OPEN_INTAKE_ORCHESTRATION_PREFLIGHT_RECEIPT",
        [
            {
                "receipt_id": "PR159S_OPEN_INTAKE_ORCHESTRATION_PREFLIGHT_RECEIPT",
                "selected_artifact_paths": selected_artifact_paths(receipts),
                "fallback_crosswalk_path_used": fallback_crosswalk_path_used(receipts),
                "prior_counts": _prior_counts(root),
                "868_target_inventory_source": c.PR159R_UNRESOLVED_FILL_PATH.as_posix(),
                "PR154_AtomicRows_split": inventory_counts(targets),
                "market_platform_scope": stable_counter(classified_targets, "platform_scope"),
                "source_taxonomy_selected": c.SOURCE_TAXONOMY_PATH.as_posix(),
                "authority_taxonomy_selected": "constants.AuthorityClass",
                "source_profit_provenance_taxonomy_selected": "constants.SourceProvenanceTag/constants.ProfitValidationTag",
                "official_confirmed_backfill_enabled": True,
                "open_research_intake_enabled": True,
                "official_fact_acceptance_enabled": True,
                "replay_paper_candidate_routing_enabled": True,
                "quantum_forward_candidate_routing_enabled": True,
                "no_qtt_checksum_freeze_global_digest_authority": True,
                "no_atomicrows_bundle_checksum_hash_authority": True,
            }
        ],
        count_receipt,
        receipts,
        repo_preflight_receipt=repo_preflight_receipt(root),
    )
    payloads[c.INPUT_TARGET_INVENTORY_PATH.as_posix()] = _common_payload(
        "PR159S_INPUT_TARGET_INVENTORY",
        _inventory_records(targets),
        count_receipt,
        receipts,
        inventory_counts=inventory_counts(targets),
    )
    payloads[c.SOURCE_TAXONOMY_PATH.as_posix()] = _common_payload(
        "PR159S_SOURCE_TAXONOMY",
        source_taxonomy_records,
        count_receipt,
        receipts,
        taxonomy_counts=taxonomy_counts(),
    )
    payloads[c.OPEN_RESEARCH_SOURCE_INTAKE_PATH.as_posix()] = _common_payload(
        "PR159S_OPEN_RESEARCH_SOURCE_INTAKE",
        open_research_records,
        count_receipt,
        receipts,
        accepted_open_research_candidate_count=len(open_research_records),
    )
    payloads[c.OFFICIAL_EXTERNAL_FACT_DELTA_PATH.as_posix()] = _common_payload(
        "PR159S_OFFICIAL_EXTERNAL_FACT_DELTA",
        official_delta_records,
        count_receipt,
        receipts,
        accepted_official_external_fact_delta_count=0,
        official_candidate_pending_exact_field_delta_count=len(official_delta_records),
    )
    payloads[c.ALGORITHM_FORMULA_CANDIDATE_DELTA_PATH.as_posix()] = _common_payload(
        "PR159S_ALGORITHM_FORMULA_CANDIDATE_DELTA",
        algorithm_formula_records,
        count_receipt,
        receipts,
        candidate_state_counts=dict(sorted(Counter(record["candidate_terminal_state"] for record in algorithm_formula_records).items())),
    )
    payloads[c.ATOMICROWS_CANDIDATE_READINESS_DELTA_PATH.as_posix()] = _common_payload(
        "PR159S_ATOMICROWS_CANDIDATE_READINESS_DELTA",
        atomicrows_candidate_records,
        count_receipt,
        receipts,
    )
    payloads[c.REPLAY_PAPER_CANDIDATE_ROUTE_PATH.as_posix()] = _common_payload(
        "PR159S_REPLAY_PAPER_CANDIDATE_ROUTE",
        replay_paper_records,
        count_receipt,
        receipts,
    )
    payloads[c.QUANTUM_CANDIDATE_READINESS_DELTA_PATH.as_posix()] = _common_payload(
        "PR159S_QUANTUM_CANDIDATE_READINESS_DELTA",
        quantum_records,
        count_receipt,
        receipts,
        quantum_relevant_candidate_count=sum(1 for record in quantum_records if record["quantum_relevant_candidate_flag"]),
    )
    payloads[c.SOURCE_PROFIT_PROVENANCE_CLASSIFICATION_PATH.as_posix()] = _common_payload(
        "PR159S_SOURCE_PROFIT_PROVENANCE_CLASSIFICATION",
        classified_targets,
        count_receipt,
        receipts,
    )
    payloads[c.OFFICIAL_CONFIRMED_BACKFILL_PATH.as_posix()] = _common_payload(
        "PR159S_OFFICIAL_CONFIRMED_BACKFILL",
        backfill_records,
        count_receipt,
        receipts,
        official_confirmed_backfill_count=len(backfill_records),
    )
    payloads[c.PROFIT_VALIDATION_STATE_REGISTRY_PATH.as_posix()] = _common_payload(
        "PR159S_PROFIT_VALIDATION_STATE_REGISTRY",
        profit_records,
        count_receipt,
        receipts,
    )
    payloads[c.ATOMICROWS_SOURCE_PROFIT_READINESS_DELTA_PATH.as_posix()] = _common_payload(
        "PR159S_ATOMICROWS_SOURCE_PROFIT_READINESS_DELTA",
        atomicrows_source_profit_records,
        count_receipt,
        receipts,
    )
    payloads[c.TERMINAL_COMPLETION_SUMMARY_PATH.as_posix()] = _common_payload(
        "PR159S_TERMINAL_COMPLETION_SUMMARY",
        classified_targets,
        count_receipt,
        receipts,
        terminal_completion_partition=count_receipt["terminal_completion_partition"],
        source_provenance_partition=count_receipt["source_provenance_partition"],
        profit_validation_partition=count_receipt["profit_validation_partition"],
    )
    payloads[c.BRANCH_CONTEXT_AND_DETERMINISTIC_AUDIT_PATH.as_posix()] = _common_payload(
        "PR159S_BRANCH_CONTEXT_AND_DETERMINISTIC_AUDIT",
        [
            {
                "receipt_id": "PR159S_BRANCH_CONTEXT_AND_DETERMINISTIC_AUDIT",
                "repo_preflight_receipt": repo_preflight_receipt(root),
                "branch_context_validator": "tools/ci_branch_context.py",
                "branch_context_supported_modes": [
                    "exact_pr159s_branch",
                    "repair_branch_pattern",
                    "github_pull_request_detached_head",
                    "github_main_push_with_ancestry",
                    "later_main_descendant",
                ],
                "pr152_deterministic_audit_currentization_status": (
                    "PR152_ARTIFACT_PRESENT_AND_PR159S_AUDIT_RECEIPT_EMITTED"
                    if (root / c.PR152_AUDIT_REPORT).exists()
                    else "PR152_ARTIFACT_NOT_PRESENT"
                ),
                "no_direct_github_branch_env_reads_inside_stage1_source_package": True,
                "no_authority_confirmation": dict(c.NO_AUTHORITY_CONFIRMATION),
            }
        ],
        count_receipt,
        receipts,
    )

    return BuildArtifacts(payloads=payloads)


def write_artifacts(root: Path) -> None:
    artifacts = build_artifacts(root)
    for rel_path, payload in artifacts.payloads.items():
        write_json(root / rel_path, payload)
