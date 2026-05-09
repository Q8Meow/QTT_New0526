#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import pathlib
import re
import subprocess
from typing import Any, Sequence

SUCCESS_MARKER = "MASTER_PLAN_IMPLEMENTATION_COVERAGE_LEDGER_BUILT"

LEDGER_TYPE = "MASTER_PLAN_IMPLEMENTATION_COVERAGE_LEDGER"
LEDGER_SCHEMA_VERSION = "PR47_MASTER_PLAN_IMPLEMENTATION_COVERAGE_LEDGER_V1"
GENERATED_AT_POLICY = "DETERMINISTIC_NO_WALLCLOCK_TIMESTAMP"
GENERATED_BY_TOOL = "tools/build_master_plan_implementation_coverage_ledger.py"
SOURCE_MASTER_PLAN_PATH = "docs/master_plan/QTT_MasterPlan_Current.md"
CANONICAL_LEDGER_PATH = (
    "docs/master_plan/generated/MasterPlanImplementationCoverageLedger.json"
)
CANONICAL_ATOMICROWS_BUNDLE = "docs/master_plan/atomic_rows/AtomicRows.bundle.jsonl"
CANONICAL_ATOMICROWS_SHA = "docs/master_plan/atomic_rows/AtomicRows.bundle.sha256"

MERGE_SUBJECT_RE = re.compile(
    r"^Merge pull request #(?P<pr_number>\d+) from (?P<branch_name>\S+)$"
)
SUCCESS_MARKER_RE = re.compile(r'SUCCESS_MARKER\s*=\s*"([^"]+)"')
PRINTED_OK_RE = re.compile(r'print\(\s*"([A-Z0-9_]+_OK)"')
HEADING_RE = re.compile(r"^#{1,6}\s+(?P<section_id>0X\.[0-9A-Z]+(?:\.[0-9A-Z]+)*)\s+(?P<title>.+)$")

PR_RECORD_FALSE_FLAGS: tuple[str, ...] = (
    "runtime_authority_created_flag",
    "order_authority_created_flag",
    "profit_claim_created_flag",
    "atomicrows_bundle_created_flag",
    "atomicrows_sha_created_flag",
    "source_fact_acceptance_created_flag",
    "connector_semantics_populated_flag",
    "live_reachability_created_flag",
    "runtime_resolver_snapshot_created_flag",
    "replay_or_paper_execution_created_flag",
    "replay_paper_result_packets_created_flag",
    "result_merge_created_flag",
    "dual_result_review_decision_created_flag",
    "owner_live_promotion_approval_created_flag",
    "live_eligibility_created_flag",
    "canary_eligibility_created_flag",
    "canary_execution_created_flag",
    "runtime_cash_receipt_created_flag",
    "blocker_reduction_created_flag",
    "network_io_created_flag",
    "source_retrieval_created_flag",
)

AUTHORITY = {
    "authority_class": "NON_AUTHORITATIVE_IMPLEMENTATION_COVERAGE_LEDGER",
    "derived_from": "local_git_history_and_repo_files",
    "ledger_is_master_plan_authority": False,
    "ledger_is_source_fact_authority": False,
    "ledger_is_connector_semantic_authority": False,
    "ledger_is_runtime_authority": False,
    "ledger_is_order_authority": False,
    "ledger_is_atomicrows_authority": False,
    "ledger_is_profit_evidence": False,
    "ledger_may_select_next_pr_without_master_plan_crosscheck": False,
    "owner_review_required_for_uncertain_mapping": True,
}

AUTHORITY_BOUNDARY = {
    "boundary_class": "STATIC_LEDGER_RECORD_ONLY_NO_AUTHORITY",
    "retrieves_source_evidence": False,
    "creates_source_fact_acceptance": False,
    "creates_real_accepted_source_evidence_packets": False,
    "populates_production_connector_semantics": False,
    "creates_runtime_resolver_snapshot": False,
    "executes_replay_or_paper": False,
    "creates_replay_or_paper_result_packets": False,
    "merges_replay_paper_results": False,
    "creates_dual_result_review_decision": False,
    "creates_owner_live_promotion_approval": False,
    "creates_live_eligibility": False,
    "creates_canary_eligibility": False,
    "executes_canary": False,
    "creates_live_reachability": False,
    "creates_order_authority": False,
    "creates_runtime_cash_receipt": False,
    "creates_atomicrows_bundle": False,
    "creates_atomicrows_hash": False,
    "reduces_blockers": False,
    "creates_profit_evidence": False,
    "creates_network_io": False,
}

GENERIC_REMAINING_BLOCKERS = [
    "official source facts remain unaccepted",
    "production connector semantic values remain unpopulated",
    "runtime resolver snapshots remain uncreated",
    "replay/paper execution and result packets remain uncreated",
    "dual-result review decisions and result merges remain uncreated",
    "owner live-promotion approval remains uncreated",
    "live eligibility, canary eligibility, canary execution, and live reachability remain uncreated",
    "order authority and runtime cash receipts remain uncreated",
    "AtomicRows bundle/hash remain absent and unauthoritative",
    "blockers remain unreduced and no profit evidence exists",
]

STRONG_PR_RECORDS: dict[int, dict[str, Any]] = {
    38: {
        "implemented_subject": "source-fact binding connector semantic readiness static gate",
        "implementation_status": "STATIC_GATE_IMPLEMENTED",
        "master_plan_section_ids": ["0X.4P"],
        "master_plan_anchor_terms": [
            "0X.4P",
            "Source-fact binding, connector semantic implementation readiness",
            "source-to-connector field binding manifest contract",
        ],
        "validator_tools": [
            "tools/validate_source_fact_binding_connector_semantic_readiness_static.py",
        ],
        "generated_report_paths": [
            "docs/master_plan/generated/QTTTestGate.report.json",
        ],
        "validation_markers": [
            "SOURCE_FACT_BINDING_CONNECTOR_SEMANTIC_READINESS_STATIC_VALIDATION_OK",
        ],
        "next_allowed_consumer_if_known": "0X.4Q/0X.4R static gates after master-plan crosscheck and accepted source-evidence prerequisites",
    },
    39: {
        "implemented_subject": "accepted source-evidence consumer contract",
        "implementation_status": "STATIC_CONTRACT_IMPLEMENTED",
        "master_plan_section_ids": ["0X.4Q"],
        "master_plan_anchor_terms": [
            "0X.4Q",
            "accepted source-evidence export ledger",
            "target-field acceptance ledger",
        ],
        "validator_tools": [
            "tools/source_evidence_acceptance_consumer_contract_check.py",
        ],
        "generated_report_paths": [
            "docs/master_plan/generated/QTTTestGate.report.json",
        ],
        "validation_markers": [
            "SOURCE_EVIDENCE_ACCEPTANCE_CONSUMER_CONTRACT_STATIC_VALIDATION_OK",
        ],
        "next_allowed_consumer_if_known": "0X.4R connector semantic binding contract gate only",
    },
    40: {
        "implemented_subject": "connector semantic binding contract",
        "implementation_status": "STATIC_CONTRACT_IMPLEMENTED",
        "master_plan_section_ids": ["0X.4R"],
        "master_plan_anchor_terms": [
            "0X.4R",
            "Connector semantic binding after accepted source-evidence packets",
            "semantic value packet discipline",
        ],
        "validator_tools": [
            "tools/stage1_connector_semantic_binding_ledger_check.py",
        ],
        "generated_report_paths": [
            "docs/master_plan/generated/Stage1ConnectorSemanticBindingLedgerCheck.report.json",
            "docs/master_plan/generated/QTTTestGate.report.json",
        ],
        "validation_markers": [
            "STAGE1_CONNECTOR_SEMANTIC_BINDING_LEDGER_CHECK_OK",
        ],
        "next_allowed_consumer_if_known": "0X.4S runtime resolver snapshot contract gate only",
    },
    41: {
        "implemented_subject": "runtime resolver snapshot contract",
        "implementation_status": "STATIC_CONTRACT_IMPLEMENTED",
        "master_plan_section_ids": [
            "0X.4S.3",
            "0X.4S.4",
            "0X.4S.5",
            "0X.4S.6",
            "0X.4S.7",
        ],
        "master_plan_anchor_terms": [
            "0X.4S.3",
            "runtime resolver snapshot manifest and input-lock contract",
            "runtime resolver implementation contract",
        ],
        "validator_tools": [
            "tools/stage1_runtime_resolver_snapshot_contract_check.py",
        ],
        "generated_report_paths": [
            "docs/master_plan/generated/Stage1RuntimeResolverSnapshotContractCheck.report.json",
            "docs/master_plan/generated/QTTTestGate.report.json",
        ],
        "validation_markers": [
            "STAGE1_RUNTIME_RESOLVER_SNAPSHOT_CONTRACT_CHECK_OK",
        ],
        "next_allowed_consumer_if_known": "0X.4S.8 handoff contract only; no snapshot creation authority",
    },
    42: {
        "implemented_subject": "runtime resolver to replay/paper handoff contract",
        "implementation_status": "STATIC_CONTRACT_IMPLEMENTED",
        "master_plan_section_ids": ["0X.4S.8", "0X.4S.9"],
        "master_plan_anchor_terms": [
            "0X.4S.8",
            "runtime-resolver-to-concurrent-replay/paper handoff contract",
            "runtime resolver snapshot consumer-boundary",
        ],
        "validator_tools": [
            "tools/stage1_runtime_resolver_to_replay_paper_handoff_check.py",
        ],
        "generated_report_paths": [
            "docs/master_plan/generated/Stage1RuntimeResolverToReplayPaperHandoff.report.json",
            "docs/master_plan/generated/QTTTestGate.report.json",
        ],
        "validation_markers": [
            "STAGE1_RUNTIME_RESOLVER_TO_REPLAY_PAPER_HANDOFF_CHECK_OK",
        ],
        "next_allowed_consumer_if_known": "0X.4T concurrent replay/paper contract gate only",
    },
    43: {
        "implemented_subject": "concurrent replay/paper contract",
        "implementation_status": "STATIC_CONTRACT_IMPLEMENTED",
        "master_plan_section_ids": ["0X.4T"],
        "master_plan_anchor_terms": [
            "0X.4T",
            "Concurrent replay/paper execution after runtime resolver snapshot",
            "same runtime resolver snapshot, same input lock",
        ],
        "validator_tools": [
            "tools/stage1_concurrent_replay_paper_contract_check.py",
        ],
        "generated_report_paths": [
            "docs/master_plan/generated/Stage1ConcurrentReplayPaperContractCheck.report.json",
            "docs/master_plan/generated/QTTTestGate.report.json",
        ],
        "validation_markers": [
            "STAGE1_CONCURRENT_REPLAY_PAPER_CONTRACT_CHECK_OK",
        ],
        "next_allowed_consumer_if_known": "0X.4U dual-result review contract gate only",
    },
    44: {
        "implemented_subject": "dual-result review contract",
        "implementation_status": "STATIC_CONTRACT_IMPLEMENTED",
        "master_plan_section_ids": ["0X.4U"],
        "master_plan_anchor_terms": [
            "0X.4U",
            "Dual-result review after separate replay and paper result packets",
            "no-auto-promotion",
        ],
        "validator_tools": [
            "tools/stage1_dual_result_review_contract_check.py",
        ],
        "generated_report_paths": [
            "docs/master_plan/generated/Stage1DualResultReviewContractCheck.report.json",
            "docs/master_plan/generated/QTTTestGate.report.json",
        ],
        "validation_markers": [
            "STAGE1_DUAL_RESULT_REVIEW_CONTRACT_CHECK_OK",
        ],
        "next_allowed_consumer_if_known": "0X.4V owner live-promotion review contract gate only",
    },
    45: {
        "implemented_subject": "owner live-promotion review contract",
        "implementation_status": "STATIC_CONTRACT_IMPLEMENTED",
        "master_plan_section_ids": ["0X.4V"],
        "master_plan_anchor_terms": [
            "0X.4V",
            "Owner live-promotion review and three-venue live-canary eligibility",
            "owner approval receipt boundary",
        ],
        "validator_tools": [
            "tools/stage1_owner_live_promotion_review_contract_check.py",
        ],
        "generated_report_paths": [
            "docs/master_plan/generated/Stage1OwnerLivePromotionReviewContractCheck.report.json",
            "docs/master_plan/generated/QTTTestGate.report.json",
        ],
        "validation_markers": [
            "STAGE1_OWNER_LIVE_PROMOTION_REVIEW_CONTRACT_CHECK_OK",
        ],
        "next_allowed_consumer_if_known": "0X.4V.9/0X.4W.9 canary eligibility handoff contract only",
    },
    46: {
        "implemented_subject": "three-venue canary eligibility contract",
        "implementation_status": "STATIC_CONTRACT_IMPLEMENTED",
        "master_plan_section_ids": [
            "0X.4V.9",
            "0X.4V.11",
            "0X.4B.5",
            "0X.4B.9",
            "0X.4W.9",
        ],
        "master_plan_anchor_terms": [
            "0X.4V.9",
            "three-venue live-canary eligibility consumer contract",
            "limited-live canary execution precondition lock",
        ],
        "validator_tools": [
            "tools/stage1_three_venue_canary_eligibility_contract_check.py",
        ],
        "generated_report_paths": [
            "docs/master_plan/generated/Stage1ThreeVenueCanaryEligibilityContractCheck.report.json",
            "docs/master_plan/generated/QTTTestGate.report.json",
        ],
        "validation_markers": [
            "STAGE1_THREE_VENUE_CANARY_ELIGIBILITY_CONTRACT_CHECK_OK",
        ],
        "next_allowed_consumer_if_known": "0X.4W limited-live canary execution boundary remains blocked until future owner-authorized receipts",
    },
}


def _as_repo_path(path: str | pathlib.Path) -> str:
    return pathlib.Path(path).as_posix()


def _run_git(repo_root: pathlib.Path, args: Sequence[str]) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout


def _git_file_text(repo_root: pathlib.Path, commit: str, rel_path: str) -> str:
    completed = subprocess.run(
        ["git", "show", f"{commit}:{rel_path}"],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )
    return completed.stdout if completed.returncode == 0 else ""


def _git_body_first_line(repo_root: pathlib.Path, commit: str) -> str | None:
    body = _run_git(repo_root, ["show", "--no-patch", "--pretty=format:%b", commit])
    for line in body.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped
    return None


def _changed_paths(repo_root: pathlib.Path, first_parent: str, merge_commit: str) -> list[str]:
    output = _run_git(repo_root, ["diff", "--name-only", first_parent, merge_commit])
    return sorted(path for path in output.splitlines() if path)


def _merge_records_from_git(repo_root: pathlib.Path) -> list[dict[str, Any]]:
    output = _run_git(
        repo_root,
        ["log", "--format=%H%x09%P%x09%s", "--merges", "--first-parent", "--reverse", "HEAD"],
    )
    records: list[dict[str, Any]] = []
    for line in output.splitlines():
        commit, parents_text, subject = line.split("\t", 2)
        match = MERGE_SUBJECT_RE.match(subject)
        if not match:
            continue
        pr_number = int(match.group("pr_number"))
        if pr_number < 1 or pr_number > 46:
            continue
        parents = parents_text.split()
        first_parent = parents[0] if parents else ""
        branch_tip = parents[1] if len(parents) > 1 else None
        paths = _changed_paths(repo_root, first_parent, commit) if first_parent else []
        body_title = _git_body_first_line(repo_root, commit)
        records.append(
            {
                "pr_number": pr_number,
                "branch_name_if_known": match.group("branch_name"),
                "local_commit_if_known": branch_tip,
                "merge_commit_if_known": commit,
                "merge_subject": subject,
                "pr_title_or_subject": body_title or subject,
                "created_or_changed_paths": paths,
            }
        )
    return sorted(records, key=lambda record: record["pr_number"])


def _paths_with_prefix(paths: Sequence[str], prefix: str) -> list[str]:
    return sorted(path for path in paths if path.startswith(prefix))


def _validator_tools(paths: Sequence[str]) -> list[str]:
    tool_paths = _paths_with_prefix(paths, "tools/")
    return sorted(
        path
        for path in tool_paths
        if (
            "validate" in pathlib.PurePosixPath(path).name
            or pathlib.PurePosixPath(path).name.endswith("_check.py")
            or pathlib.PurePosixPath(path).name in {"qtt_test_gate.py", "local_gate_command_matrix.py", "pr_handoff_check.py"}
        )
    )


def _generated_report_paths(paths: Sequence[str]) -> list[str]:
    return sorted(path for path in paths if path.startswith("docs/master_plan/generated/"))


def _test_paths(paths: Sequence[str]) -> list[str]:
    return sorted(path for path in paths if path.startswith("tests/"))


def _validation_markers_from_tools(
    repo_root: pathlib.Path,
    commit: str,
    tool_paths: Sequence[str],
) -> list[str]:
    markers: set[str] = set()
    for path in tool_paths:
        text = _git_file_text(repo_root, commit, path)
        markers.update(SUCCESS_MARKER_RE.findall(text))
        markers.update(PRINTED_OK_RE.findall(text))
    return sorted(markers)


def _section_headings(master_plan_text: str) -> dict[str, str]:
    headings: dict[str, str] = {}
    for line in master_plan_text.splitlines():
        match = HEADING_RE.match(line)
        if match:
            headings[match.group("section_id")] = match.group("title").strip()
    return headings


def _section_sort_key(section_id: str) -> tuple[Any, ...]:
    pieces: list[Any] = []
    for part in re.split(r"([0-9]+)", section_id):
        if part.isdigit():
            pieces.append(int(part))
        elif part:
            pieces.append(part)
    return tuple(pieces)


def _record_for_merge(
    repo_root: pathlib.Path,
    merge_record: dict[str, Any],
) -> dict[str, Any]:
    paths = merge_record["created_or_changed_paths"]
    validator_tools = _validator_tools(paths)
    markers = _validation_markers_from_tools(
        repo_root,
        merge_record["merge_commit_if_known"],
        validator_tools,
    )
    record: dict[str, Any] = {
        "pr_number": merge_record["pr_number"],
        "pr_title_or_subject": merge_record["pr_title_or_subject"],
        "branch_name_if_known": merge_record["branch_name_if_known"],
        "local_commit_if_known": merge_record["local_commit_if_known"],
        "merge_commit_if_known": merge_record["merge_commit_if_known"],
        "implementation_status": "TRACKING_ONLY",
        "master_plan_section_ids": [],
        "master_plan_anchor_terms": [],
        "implemented_subject": merge_record["pr_title_or_subject"],
        "created_or_changed_paths": paths,
        "generated_report_paths": _generated_report_paths(paths),
        "validator_tools": validator_tools,
        "test_paths": _test_paths(paths),
        "validation_markers": markers,
        "authority_boundary": dict(AUTHORITY_BOUNDARY),
        "review_status": "SECTION_MAPPING_REQUIRES_OWNER_REVIEW",
    }
    for flag in PR_RECORD_FALSE_FLAGS:
        record[flag] = False

    strong = STRONG_PR_RECORDS.get(record["pr_number"])
    if strong is not None:
        record["implementation_status"] = strong["implementation_status"]
        record["master_plan_section_ids"] = list(strong["master_plan_section_ids"])
        record["master_plan_anchor_terms"] = list(strong["master_plan_anchor_terms"])
        record["implemented_subject"] = strong["implemented_subject"]
        record["generated_report_paths"] = sorted(
            set(record["generated_report_paths"]) | set(strong["generated_report_paths"])
        )
        record["validator_tools"] = sorted(
            set(record["validator_tools"]) | set(strong["validator_tools"])
        )
        record["validation_markers"] = sorted(
            set(record["validation_markers"]) | set(strong["validation_markers"])
        )
        record["review_status"] = "VERIFIED"

    return record


def _section_records(
    pr_records: Sequence[dict[str, Any]],
    section_titles: dict[str, str],
) -> list[dict[str, Any]]:
    section_to_prs: dict[str, list[dict[str, Any]]] = {}
    for record in pr_records:
        for section_id in record["master_plan_section_ids"]:
            section_to_prs.setdefault(section_id, []).append(record)

    records: list[dict[str, Any]] = []
    for section_id in sorted(section_to_prs, key=_section_sort_key):
        prs = sorted(section_to_prs[section_id], key=lambda item: item["pr_number"])
        markers = sorted({marker for pr in prs for marker in pr["validation_markers"]})
        reports = sorted({path for pr in prs for path in pr["generated_report_paths"]})
        statuses = {pr["implementation_status"] for pr in prs}
        status = (
            "STATIC_GATE_IMPLEMENTED"
            if "STATIC_GATE_IMPLEMENTED" in statuses
            else "STATIC_CONTRACT_IMPLEMENTED"
        )
        next_consumers = sorted(
            {
                STRONG_PR_RECORDS[pr["pr_number"]]["next_allowed_consumer_if_known"]
                for pr in prs
                if pr["pr_number"] in STRONG_PR_RECORDS
            }
        )
        records.append(
            {
                "section_id": section_id,
                "section_title_or_anchor": section_titles.get(
                    section_id,
                    f"{section_id} section anchor requires owner-title review",
                ),
                "implementing_pr_numbers": [pr["pr_number"] for pr in prs],
                "implementation_status": status,
                "current_authority_state": (
                    "STATIC_ONLY_NON_AUTHORITATIVE_NO_RUNTIME_LIVE_ORDER_ATOMICROWS_OR_PROFIT_AUTHORITY"
                ),
                "validator_marker_if_any": markers,
                "generated_report_if_any": reports,
                "next_allowed_consumer_if_known": next_consumers,
                "remaining_blockers": list(GENERIC_REMAINING_BLOCKERS),
                "review_required_flag": False,
            }
        )
    return records


def _validation_marker_records(pr_records: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    marker_to_records: dict[str, list[dict[str, Any]]] = {}
    for record in pr_records:
        for marker in record["validation_markers"]:
            marker_to_records.setdefault(marker, []).append(record)

    records: list[dict[str, Any]] = []
    for marker in sorted(marker_to_records):
        prs = sorted(marker_to_records[marker], key=lambda item: item["pr_number"])
        records.append(
            {
                "validation_marker": marker,
                "producing_pr_numbers": [record["pr_number"] for record in prs],
                "validator_tools": sorted(
                    {tool for record in prs for tool in record["validator_tools"]}
                ),
                "generated_report_paths": sorted(
                    {path for record in prs for path in record["generated_report_paths"]}
                ),
                "authority_state": "STATIC_VALIDATION_MARKER_ONLY_NOT_AUTHORITY",
                "creates_authority_flag": False,
                "review_required_flag": any(
                    record["review_status"] != "VERIFIED" for record in prs
                ),
            }
        )
    return records


def _review_required_records(pr_records: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for record in pr_records:
        if record["review_status"] not in {
            "SECTION_MAPPING_REQUIRES_OWNER_REVIEW",
            "UNKNOWN_REQUIRES_OWNER_REVIEW",
        }:
            continue
        records.append(
            {
                "review_record_id": f"PR_{record['pr_number']:03d}_SECTION_MAPPING_REVIEW_REQUIRED",
                "record_type": "PR_SECTION_MAPPING_REVIEW",
                "pr_number": record["pr_number"],
                "reason": (
                    "Local merge commit, changed paths, validators, tests, and generated reports "
                    "prove implementation activity, but no exact master-plan section mapping was "
                    "proven by PR47 without owner crosscheck."
                ),
                "owner_review_required": True,
                "local_evidence_paths": record["created_or_changed_paths"],
            }
        )
    return records


def _future_pr_tracking_policy() -> dict[str, Any]:
    return {
        "policy_id": "PR47_FUTURE_IMPLEMENTATION_PR_LEDGER_TRACKING_POLICY",
        "applies_to": "EVERY_FUTURE_IMPLEMENTATION_PR",
        "future_pr_must_add_or_regenerate_ledger_coverage": True,
        "required_future_pr_fields": [
            "PR number",
            "section IDs",
            "validator marker",
            "generated report",
            "authority boundary",
            "next allowed consumer",
            "review required flag",
        ],
        "ledger_does_not_replace_master_plan_crosscheck": True,
        "ledger_may_not_select_next_pr_without_master_plan_crosscheck": True,
        "missing_or_uncertain_mapping_must_be_review_required": True,
    }


def build_ledger(repo_root: pathlib.Path) -> dict[str, Any]:
    root = repo_root.resolve()
    master_plan_path = root / pathlib.Path(SOURCE_MASTER_PLAN_PATH)
    master_plan_text = master_plan_path.read_text(encoding="utf-8")
    section_titles = _section_headings(master_plan_text)

    pr_records = [
        _record_for_merge(root, merge_record)
        for merge_record in _merge_records_from_git(root)
    ]
    section_records = _section_records(pr_records, section_titles)
    marker_records = _validation_marker_records(pr_records)
    review_required_records = _review_required_records(pr_records)

    pr_1_37_review_required_count = sum(
        1
        for record in pr_records
        if 1 <= record["pr_number"] <= 37
        and record["review_status"] == "SECTION_MAPPING_REQUIRES_OWNER_REVIEW"
    )
    strong_count = sum(
        1
        for record in pr_records
        if 38 <= record["pr_number"] <= 46 and record["review_status"] == "VERIFIED"
    )

    return {
        "ledger_type": LEDGER_TYPE,
        "ledger_schema_version": LEDGER_SCHEMA_VERSION,
        "generated_at_policy": GENERATED_AT_POLICY,
        "generated_by_tool": GENERATED_BY_TOOL,
        "source_repository_path": ".",
        "source_master_plan_path": SOURCE_MASTER_PLAN_PATH,
        "authority": dict(AUTHORITY),
        "coverage_summary": {
            "total_pr_records": len(pr_records),
            "strong_pr_38_through_46_record_count": strong_count,
            "pr_1_through_37_review_required_count": pr_1_37_review_required_count,
            "master_plan_section_record_count": len(section_records),
            "validation_marker_record_count": len(marker_records),
            "review_required_record_count": len(review_required_records),
            "unknown_unmapped_pr_record_count": sum(
                1
                for record in pr_records
                if record["implementation_status"] == "UNKNOWN_UNMAPPED"
            ),
            "atomicrows_bundle_present": (root / pathlib.Path(CANONICAL_ATOMICROWS_BUNDLE)).exists(),
            "atomicrows_sha_present": (root / pathlib.Path(CANONICAL_ATOMICROWS_SHA)).exists(),
            "deterministic_local_git_history_only": True,
            "no_authority_claims_preserved": True,
        },
        "pr_records": pr_records,
        "master_plan_section_records": section_records,
        "validation_marker_records": marker_records,
        "review_required_records": review_required_records,
        "future_pr_tracking_policy": _future_pr_tracking_policy(),
    }


def write_ledger(ledger: dict[str, Any], output_path: pathlib.Path) -> None:
    out_posix = output_path.as_posix()
    if out_posix in {SOURCE_MASTER_PLAN_PATH, CANONICAL_ATOMICROWS_BUNDLE, CANONICAL_ATOMICROWS_SHA}:
        raise ValueError(f"refusing to write protected path: {out_posix}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(ledger, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--out", default=CANONICAL_LEDGER_PATH)
    args = parser.parse_args(argv)

    repo_root = pathlib.Path(args.repo_root)
    output = repo_root / pathlib.Path(args.out)
    ledger = build_ledger(repo_root)
    write_ledger(ledger, output)
    print(SUCCESS_MARKER)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
