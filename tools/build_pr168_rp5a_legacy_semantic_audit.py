#!/usr/bin/env python3
"""Build PR168-RP5A legacy semantic audit artifacts."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import subprocess
import sys
import time
import types
from typing import Any, Mapping, Sequence
import uuid

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.pr168_rp5a_agent_touchpoints import build_agent_touchpoint_rows, pr165_d2_crosswalk_status
from tools.pr168_rp5a_blast_radius import build_blast_radius_rows
from tools.pr168_rp5a_config import (
    BRANCH_NAME,
    CHECKPOINT_PATH,
    CREATED_AT_UTC,
    FILE_KIND_CURRENTIZATION,
    FILE_KIND_DOC,
    FILE_KIND_GENERATED_REPORT,
    FILE_KIND_GENERATED_SHARD,
    FILE_KIND_MANIFEST,
    FILE_KIND_TEST_SOURCE,
    FILE_KIND_TOOL_SOURCE,
    FILE_KIND_VALIDATOR,
    FORBIDDEN_OPERATION_COUNTERS,
    HARD_FAIL_PHYSICAL_PATH_LENGTH,
    MAX_CONSUMER_REFS_PER_FILE,
    MAX_FILES_SCANNED,
    MAX_IDENTITY_REFS_PER_FILE,
    MAX_LINE_HITS_PER_FILE,
    MAX_MATCHED_FILES,
    MAX_STRUCTURED_JSON_BYTES,
    MAX_TOTAL_LINE_HITS,
    MAX_TOTAL_ROWS_PER_SHARD,
    MAX_WALL_SECONDS,
    PR_TITLE,
    PR240_HEAD_REF,
    PROGRESS_INTERVAL_SECONDS,
    REPORT_NAMES,
    REPORT_VERSION,
    ROW_SHARDS,
    SHARD_ROOT,
    WARNING_THRESHOLD_PHYSICAL_PATH_LENGTH,
    classify_file_kind,
    generated_ref,
    is_owned_rp5a_path,
    manifest_path_for_shard,
    normalize_repo_path,
    report_path,
    semantic_risk_level,
    severity_rank,
    shard_path,
)
from tools.pr168_rp5a_consumer_graph import build_consumer_graph
from tools.pr168_rp5a_cross_graph_consistency import build_consistency_report_rows
from tools.pr168_rp5a_delete_eligibility import build_delete_eligibility_rows
from tools.pr168_rp5a_git_grep_scanner import file_inventory_rows, scan_files_for_terms, scannable_files
from tools.pr168_rp5a_identity_custody import build_identity_custody_rows
from tools.pr168_rp5a_identity_dependency import build_identity_dependency_rows, scan_identity_occurrences
from tools.pr168_rp5a_pr_metadata_scanner import fetch_pr_metadata_rows
from tools.pr168_rp5a_report_writer import (
    read_json,
    read_jsonl,
    report_payload,
    write_json,
    write_report,
    write_shard,
)
from tools.pr168_rp5a_row_field_hit_index import LAST_ROW_FIELD_STATS, build_row_field_hits
from tools.pr168_rp5a_term_taxonomy import TERM_BY_ID, severities_from_ids, taxonomy_rows
from tools.pr168_rp5a_validation_dependency_graph import build_validation_dependency_rows, build_validation_time_risk_rows
from tools.ci_branch_context import current_branch_context
from tools import run_validation_gates as current_validation_runner
from tools.validation_scope_registry import ST12A_BRANCH
from tools.validation_inventory import (
    canonical_command,
    validate_inventory,
    validator_id_for_command,
)


VALIDATION_SCOPE_EVIDENCE_SCHEMA_VERSION = 2
VALIDATION_SCOPE_SNAPSHOT_CONTEXT = "ST12A_BRANCH_MERGE_BASE_DELTA"
VALIDATION_SCOPE_MAIN_COMPARISON_MODE = (
    "FIRST_PARENT_TO_EFFECTIVE_WORKTREE_PHASE_COMMAND_INVENTORY"
)
VALIDATION_SCOPE_MERGE_BASE_COMPARISON_MODE = (
    "MERGE_BASE_TO_EFFECTIVE_WORKTREE_PHASE_COMMAND_INVENTORY"
)
VALIDATION_SCOPE_MAIN_BASELINE_LABEL = "first-parent(HEAD)"
VALIDATION_SCOPE_MERGE_BASELINE_LABEL = "merge-base(HEAD,origin/main)"
VALIDATION_SCOPE_RUNNER_PATH = "tools/run_validation_gates.py"
VALIDATION_SCOPE_VALIDATION_DIR = Path(
    ".tmp/st12a-rp5a-semantic-currentization/validation-inventory"
)
VALIDATION_SCOPE_PYTEST_BASETEMP = (
    VALIDATION_SCOPE_VALIDATION_DIR / "pytest"
)
VALIDATION_SCOPE_EVIDENCE_FIELDS = (
    "validation_scope_evidence_schema_version",
    "validation_scope_snapshot_context",
    "validation_scope_comparison_mode",
    "validation_scope_baseline_ref",
    "validation_scope_baseline_command_count",
    "validation_scope_current_command_count",
    "validation_scope_added_count",
    "validation_scope_removed_count",
    "validation_scope_removed_refs",
    "current_validation_inventory_failure_count",
    "current_validation_inventory_failures",
    "validation_scope_changed_flag",
    "no_legacy_scope_removal_flag",
    "validation_scope_change_type",
)
ValidationScopeSignature = tuple[str, str, tuple[str, ...]]


def _run_text(args: list[str]) -> str:
    completed = subprocess.run(
        args,
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return completed.stdout.strip() if completed.returncode == 0 else ""


def _run_json(args: list[str]) -> object | None:
    text = _run_text(args)
    if not text:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


class PhaseTimer:
    def __init__(self) -> None:
        self.started_at = time.perf_counter()
        self.elapsed: dict[str, float] = {}

    def mark(self, phase: str, phase_started: float) -> None:
        self.elapsed[phase] = round(time.perf_counter() - phase_started, 6)

    def start_phase(self) -> float:
        return time.perf_counter()

    def total(self) -> float:
        return round(time.perf_counter() - self.started_at, 6)


def _write_checkpoint(phase: str, **payload: object) -> None:
    CHECKPOINT_PATH.parent.mkdir(parents=True, exist_ok=True)
    checkpoint = {
        "phase": phase,
        "updated_at_utc": CREATED_AT_UTC,
        "checkpoint_path": ".tmp/rp5a_scan_checkpoint.json",
        **payload,
    }
    CHECKPOINT_PATH.write_text(
        json.dumps(checkpoint, indent=2, sort_keys=True, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )


def _log_phase(phase: str, *, files_processed: int = 0, matched_files: int = 0, started_at: float | None = None) -> None:
    started_at = time.perf_counter() if started_at is None else started_at
    print(
        json.dumps(
            {
                "phase": phase,
                "files_processed": files_processed,
                "matched_files": matched_files,
                "elapsed_seconds": round(time.perf_counter() - started_at, 3),
            },
            sort_keys=True,
        ),
        flush=True,
    )


def _collect_preflight(existing_path: Path) -> dict[str, Any]:
    current_branch = _run_text(["git", "branch", "--show-current"])
    origin_main_head = _run_text(["git", "rev-parse", "origin/main"])
    status_short = _run_text(["git", "status", "--short", "--untracked-files=all"])
    pr240 = _run_json(["gh", "pr", "view", "240", "--json", "number,state,mergedAt,headRefName,headRefOid,baseRefName,mergeable"])
    open_prs = _run_json(["gh", "pr", "list", "--state", "open", "--limit", "50", "--json", "number,title,headRefName"])
    latest_main = _run_json(["gh", "run", "list", "--branch", "main", "--limit", "1", "--json", "status,conclusion,databaseId,headSha,displayTitle"])
    if pr240 is None and existing_path.is_file():
        existing = read_json(existing_path)
        return dict(existing.get("records") or existing)
    open_prs_filtered = []
    if isinstance(open_prs, list):
        open_prs_filtered = [row for row in open_prs if isinstance(row, dict) and row.get("headRefName") != BRANCH_NAME]
    latest_main_record = latest_main[0] if isinstance(latest_main, list) and latest_main else None
    pr240_ok = bool(
        isinstance(pr240, dict)
        and pr240.get("state") == "CLOSED"
        and pr240.get("mergedAt") is None
        and pr240.get("headRefName") == PR240_HEAD_REF
    )
    return {
        "current_branch": current_branch,
        "intended_branch": BRANCH_NAME,
        "origin_main_head": origin_main_head,
        "git_status_short_after_rp5a_edits": status_short or "<clean>",
        "latest_main_run_state": latest_main_record,
        "latest_main_run_green_or_exact_gapped": bool(isinstance(latest_main_record, dict) and latest_main_record.get("conclusion") == "success"),
        "open_prs_excluding_rp5a_branch": open_prs_filtered,
        "no_open_pr_conflict_detected": len(open_prs_filtered) == 0,
        "pr240_state": pr240,
        "pr240_closed_not_merged_preflight_passed": pr240_ok,
        "recovery1_branch_not_active": current_branch != PR240_HEAD_REF,
        "main_current_with_origin_at_branch_time": bool(origin_main_head),
        "preflight_note": "Runtime status is after RP5A edits; guard output recorded clean pre-edit state before file modifications.",
    }


def _input_rows(files_scanned: list[str], preflight: dict[str, Any], crosswalk_status: dict[str, object]) -> list[dict[str, object]]:
    required_sources = [
        ("git_status", "git status/log/fetch/preflight branch state", "READ"),
        ("github_pr_metadata", "gh pr list/view PR metadata", "READ"),
        ("github_main_runs", "gh run list --branch main", "READ"),
        ("master_plan", "QTT_MasterPlan_Current.md and docs/master_plan markdown", "READ"),
        ("roadmap", "docs/roadmap artifacts", "READ"),
        ("pr165_d2_crosswalk", "AgentRosterDiscoveryAudit and AgentDutySourceCrosswalk", "READ" if crosswalk_status["documented_equivalent_crosswalk_present"] else "EXACT_GAP"),
        ("generated_artifacts", "docs/master_plan/generated reports/shards/manifests", "READ"),
        ("tools", "tools/**/*.py", "READ"),
        ("tests", "tests/**/*.py", "READ"),
        ("validators_currentization", "run_validation_gates, validation registry/inventory/currentization tests", "READ"),
    ]
    rows = [
        {
            "row_id": f"RP5A_INPUT_{index:04d}",
            "input_source_id": source_id,
            "input_description": description,
            "read_status": status,
            "audit_only_flag": True,
        }
        for index, (source_id, description, status) in enumerate(required_sources, start=1)
    ]
    rows.append(
        {
            "row_id": f"RP5A_INPUT_{len(rows) + 1:04d}",
            "input_source_id": "scan_inventory",
            "input_description": "tracked text files scanned for stale semantics",
            "read_status": "READ",
            "files_scanned_count": len(files_scanned),
            "audit_only_flag": True,
        }
    )
    rows.append(
        {
            "row_id": f"RP5A_INPUT_{len(rows) + 1:04d}",
            "input_source_id": "preflight_pr240",
            "input_description": "PR #240 must be closed and not merged",
            "read_status": "PASS" if preflight.get("pr240_closed_not_merged_preflight_passed") else "FAIL",
            "audit_only_flag": True,
        }
    )
    return rows


def _group_hits_by_file(hit_rows: list[dict[str, object]]) -> dict[str, dict[str, object]]:
    grouped: dict[str, dict[str, object]] = {}
    for row in hit_rows:
        file_path = str(row["file_path"])
        bucket = grouped.setdefault(
            file_path,
            {
                "file_path": file_path,
                "file_kind": row["file_kind"],
                "matched_term_ids": set(),
                "matched_terms": set(),
                "term_families": set(),
                "severities": [],
                "refs": [],
                "match_count": 0,
                "critical_term_count": 0,
                "high_term_count": 0,
                "medium_term_count": 0,
                "low_term_count": 0,
                "line_hits_capped_flag": False,
                "structured_scan_statuses": set(),
            },
        )
        term_id = str(row["matched_term_id"])
        spec = TERM_BY_ID.get(term_id)
        bucket["matched_term_ids"].add(term_id)
        if spec is not None:
            bucket["matched_terms"].add(spec.report_safe_text_or_regex)
        bucket["term_families"].add(str(row["term_family"]))
        severity = str(row["semantic_risk_level"])
        bucket["severities"].append(severity)
        bucket["match_count"] = int(bucket["match_count"]) + 1
        if len(bucket["refs"]) < 250:
            bucket["refs"].append(str(row["json_pointer_or_line_ref"]))
        if row.get("line_hits_capped_flag"):
            bucket["line_hits_capped_flag"] = True
        bucket["structured_scan_statuses"].add(str(row.get("structured_scan_status", "UNKNOWN")))
        if severity == "CRITICAL":
            bucket["critical_term_count"] = int(bucket["critical_term_count"]) + 1
        elif severity == "HIGH":
            bucket["high_term_count"] = int(bucket["high_term_count"]) + 1
        elif severity == "MEDIUM":
            bucket["medium_term_count"] = int(bucket["medium_term_count"]) + 1
        else:
            bucket["low_term_count"] = int(bucket["low_term_count"]) + 1
    for bucket in grouped.values():
        bucket["matched_term_ids"] = sorted(bucket["matched_term_ids"])
        bucket["matched_terms"] = sorted(bucket["matched_terms"])
        bucket["term_families"] = sorted(bucket["term_families"])
        bucket["structured_scan_statuses"] = sorted(bucket["structured_scan_statuses"])
        bucket["matched_line_numbers_or_json_paths"] = list(bucket.pop("refs"))
        bucket["semantic_risk_level"] = semantic_risk_level(list(bucket["severities"]))
    return grouped


def _originating_pr(path: str, pr_rows: list[dict[str, object]]) -> str | None:
    upper_path = path.upper().replace("-", "_")
    for row in pr_rows:
        for prefix in row.get("known_artifact_prefixes_if_inferred", []) or []:
            if str(prefix) in upper_path:
                return f"PR#{row.get('pr_number')}:{row.get('pr_title')}"
    return None


def _contains_runtime_code(path: str) -> bool:
    if classify_file_kind(path) not in {FILE_KIND_TOOL_SOURCE, FILE_KIND_VALIDATOR}:
        return False
    try:
        text = (REPO_ROOT / path).read_text(encoding="utf-8", errors="replace").lower()
    except OSError:
        return False
    return any(token in text for token in ("runtime", "live_order", "connector", "private_state", "cash"))


def _file_semantic_rows(
    matched_files: list[str],
    file_term_map: dict[str, dict[str, object]],
    pr_rows: list[dict[str, object]],
    consumer_rows: list[dict[str, object]],
    validation_rows: list[dict[str, object]],
    identity_rows: list[dict[str, object]],
    agent_rows: list[dict[str, object]],
    delete_rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    active_consumer = {str(row["file_path"]) for row in consumer_rows if row.get("active_consumer_flag")}
    validation_dep = {str(row["file_path_or_prefix"]) for row in validation_rows if row.get("validation_dependency_type") != "NONE"}
    identity_by_file = {str(row["file_path"]): row for row in identity_rows}
    agent_active = {str(row["file_path"]) for row in agent_rows if row.get("active_agent_touchpoint_flag")}
    classification = {str(row["file_path"]): row["classification"] for row in delete_rows}
    rows: list[dict[str, object]] = []
    for index, file_path in enumerate(matched_files, start=1):
        term_info = file_term_map[file_path]
        identity = identity_by_file.get(file_path, {})
        sample_refs = identity.get("sample_identity_refs_limited", []) or []
        text_sample = " ".join(str(value) for value in sample_refs)
        rows.append(
            {
                "row_id": f"RP5A_FILE_{index:07d}",
                "file_path": file_path,
                "file_kind": classify_file_kind(file_path),
                "matched_terms": term_info["matched_terms"],
                "matched_term_ids": term_info["matched_term_ids"],
                "matched_line_numbers_or_json_paths": term_info["matched_line_numbers_or_json_paths"],
                "term_families": term_info["term_families"],
                "match_count": term_info["match_count"],
                "semantic_risk_level": term_info["semantic_risk_level"],
                "contains_formula_id_flag": "FORMULA" in text_sample.upper() or "FORMULA_ID" in str(identity.get("identity_type")),
                "contains_qku_id_flag": "QKU" in text_sample.upper() or str(identity.get("identity_type")) == "QKU_ID",
                "contains_formula_expression_flag": "FORMULA_EXPRESSION" in str(identity.get("identity_type")) or "expression" in text_sample.lower(),
                "contains_formula_to_pnl_map_flag": "FORMULA_TO_PNL" in str(identity.get("identity_type")) or "FormulaToPnL" in text_sample,
                "contains_plugin_contract_flag": "PLUGIN_CONTRACT" in str(identity.get("identity_type")) or "plugin" in text_sample.lower(),
                "contains_agent_crosswalk_flag": file_path in agent_active,
                "contains_validation_expectation_flag": file_path in validation_dep,
                "contains_runtime_code_flag": _contains_runtime_code(file_path),
                "contains_unique_identity_possible_flag": bool(identity.get("unique_identity_possible_flag")),
                "active_consumer_status_ref": f"consumer_graph:{file_path}",
                "validation_dependency_status_ref": f"validation_dependency:{file_path}",
                "identity_dependency_status_ref": f"identity_dependency:{file_path}",
                "agent_touchpoint_ref": f"agent_touchpoint:{file_path}",
                "originating_pr_if_known": _originating_pr(file_path, pr_rows),
                "recommended_classification_draft": classification[file_path],
                "delete_safe_now_flag": False,
                "unclear_dependency_flag": classification[file_path] == "UNCLEAR_DO_NOT_DELETE",
                "line_hits_capped_flag": bool(term_info.get("line_hits_capped_flag")),
                "structured_scan_statuses": term_info.get("structured_scan_statuses", []),
                "active_consumer_detected_flag": file_path in active_consumer,
                "validation_dependency_detected_flag": file_path in validation_dep,
                "active_agent_touchpoint_detected_flag": file_path in agent_active,
            }
        )
    return rows


def _wrong_concept_rows(hit_rows: list[dict[str, object]], pr_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    files_by_term: dict[str, set[str]] = defaultdict(set)
    high_by_term: Counter[str] = Counter()
    critical_by_term: Counter[str] = Counter()
    examples: dict[str, list[str]] = defaultdict(list)
    for row in hit_rows:
        term_id = str(row["matched_term_id"])
        files_by_term[term_id].add(str(row["file_path"]))
        if row["semantic_risk_level"] == "HIGH":
            high_by_term[term_id] += 1
        if row["semantic_risk_level"] == "CRITICAL":
            critical_by_term[term_id] += 1
        if len(examples[term_id]) < 5:
            examples[term_id].append(f"{row['file_path']}:{row['json_pointer_or_line_ref']}")
    pr_by_term: Counter[str] = Counter()
    for row in pr_rows:
        for term_id in row.get("matched_terms", []) or []:
            pr_by_term[str(term_id)] += 1
    rows: list[dict[str, object]] = []
    for spec in TERM_BY_ID.values():
        rows.append(
            {
                "term_id": spec.term_id,
                "term_text_or_regex": spec.report_safe_text_or_regex,
                "raw_regex_redacted_for_path_safety_flag": spec.is_regex,
                "term_family": spec.term_family,
                "canonical_future_interpretation": spec.canonical_future_interpretation,
                "matched_file_count": len(files_by_term.get(spec.term_id, set())),
                "matched_pr_count": pr_by_term.get(spec.term_id, 0),
                "high_risk_match_count": high_by_term.get(spec.term_id, 0),
                "critical_match_count": critical_by_term.get(spec.term_id, 0),
                "example_file_refs": examples.get(spec.term_id, []),
                "future_validator_rule_suggestion": "RP5B semantic-normalization validator should flag raw active consumption of this term family.",
            }
        )
    return rows


def _future_plan_rows(delete_rows: list[dict[str, object]], validation_rows: list[dict[str, object]], identity_rows: list[dict[str, object]], consumer_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    validation_dep = {str(row["file_path_or_prefix"]) for row in validation_rows if row.get("validation_dependency_type") != "NONE"}
    identity_dep = {str(row["file_path"]) for row in identity_rows if row.get("delete_requires_reclaim_flag")}
    consumer_dep = {str(row["file_path"]) for row in consumer_rows if row.get("active_consumer_flag")}
    rows: list[dict[str, object]] = []
    for index, row in enumerate(delete_rows, start=1):
        file_path = str(row["file_path"])
        classification = str(row["classification"])
        rows.append(
            {
                "future_action_id": f"RP5A_TO_RP5B_{index:07d}",
                "file_path_or_prefix": file_path,
                "current_classification": classification,
                "required_precondition": row["delete_in_future_allowed_after_conditions"],
                "required_replacement_or_summary": "canonical active layer or compact legacy summary" if classification != "DELETE_FROM_ACTIVE_TREE_SAFE" else "operator confirmation only",
                "validation_update_needed_flag": file_path in validation_dep,
                "currentization_update_needed_flag": file_path in validation_dep and file_path.endswith(".report.json"),
                "identity_reclaim_needed_flag": file_path in identity_dep,
                "consumer_rewrite_needed_flag": file_path in consumer_dep,
                "estimated_validation_time_benefit_category": "HIGH" if file_path.startswith("docs/master_plan/generated/") else "LOW",
                "risk_if_done_wrong": "identity loss, broken validators, or future-agent stale semantic consumption",
                "recommended_order": index,
            }
        )
    return rows


def _status_rows() -> list[str]:
    text = _run_text(["git", "status", "--porcelain=v1", "--untracked-files=all"])
    return [line for line in text.splitlines() if line.strip()]


def _validation_scope_counter(
    manifest: Sequence[dict[str, object]],
) -> Counter[ValidationScopeSignature]:
    counter: Counter[ValidationScopeSignature] = Counter()
    for phase_record in manifest:
        phase = str(phase_record["phase"])
        commands = phase_record["commands"]
        if not isinstance(commands, list):
            raise RuntimeError(
                "RP5A_VALIDATION_SCOPE_MANIFEST_COMMANDS_NOT_A_LIST:"
                f"{phase}"
            )
        for command in commands:
            if not isinstance(command, list):
                raise RuntimeError(
                    "RP5A_VALIDATION_SCOPE_COMMAND_NOT_A_LIST:"
                    f"{phase}"
                )
            signature = (
                phase,
                validator_id_for_command(command, phase),
                canonical_command(command),
            )
            counter[signature] += 1
    return counter


def _validation_scope_counter_delta(
    baseline: Counter[ValidationScopeSignature],
    current: Counter[ValidationScopeSignature],
) -> tuple[
    Counter[ValidationScopeSignature],
    Counter[ValidationScopeSignature],
]:
    return baseline - current, current - baseline


def _validation_scope_refs(
    counter: Counter[ValidationScopeSignature],
) -> list[dict[str, object]]:
    return [
        {
            "phase": phase,
            "validator_id": validator_id,
            "canonical_command": list(command),
            "multiplicity": multiplicity,
        }
        for (phase, validator_id, command), multiplicity in sorted(
            counter.items()
        )
    ]


def _validation_scope_baseline() -> tuple[str, str, str]:
    branch = current_branch_context(REPO_ROOT).branch
    if branch == "main":
        git_args = ["git", "rev-parse", "HEAD^1"]
        semantic_label = VALIDATION_SCOPE_MAIN_BASELINE_LABEL
        comparison_mode = VALIDATION_SCOPE_MAIN_COMPARISON_MODE
    else:
        git_args = ["git", "merge-base", "HEAD", "origin/main"]
        semantic_label = VALIDATION_SCOPE_MERGE_BASELINE_LABEL
        comparison_mode = VALIDATION_SCOPE_MERGE_BASE_COMPARISON_MODE
    internal_ref = _run_text(git_args)
    if not internal_ref:
        raise RuntimeError(
            "RP5A_VALIDATION_SCOPE_BASELINE_RESOLVE_FAILED:"
            f"{semantic_label}"
        )
    return internal_ref, semantic_label, comparison_mode


def _baseline_phase_manifest(
    internal_ref: str,
    semantic_label: str,
) -> list[dict[str, object]]:
    completed = subprocess.run(
        [
            "git",
            "show",
            f"{internal_ref}:{VALIDATION_SCOPE_RUNNER_PATH}",
        ],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if completed.returncode != 0 or not completed.stdout:
        detail = completed.stderr.strip() or "baseline runner source is empty"
        raise RuntimeError(
            "RP5A_VALIDATION_SCOPE_BASELINE_READ_FAILED:"
            f"{semantic_label}:{VALIDATION_SCOPE_RUNNER_PATH}:"
            f"{detail}"
        )

    module_name = f"_qtt_rp5a_baseline_runner_{uuid.uuid4().hex}"
    baseline_module = types.ModuleType(module_name)
    baseline_module.__file__ = str(REPO_ROOT / VALIDATION_SCOPE_RUNNER_PATH)
    sys.modules[module_name] = baseline_module
    try:
        exec(
            compile(
                completed.stdout,
                baseline_module.__file__,
                "exec",
            ),
            baseline_module.__dict__,
        )
        build_manifest = getattr(
            baseline_module,
            "build_phase_manifest",
            None,
        )
        if not callable(build_manifest):
            raise RuntimeError(
                "RP5A_VALIDATION_SCOPE_BASELINE_MANIFEST_BUILDER_MISSING:"
                f"{semantic_label}:{VALIDATION_SCOPE_RUNNER_PATH}"
            )
        return build_manifest(
            VALIDATION_SCOPE_VALIDATION_DIR,
            VALIDATION_SCOPE_PYTEST_BASETEMP,
        )
    except Exception as exc:
        if isinstance(exc, RuntimeError) and str(exc).startswith(
            "RP5A_VALIDATION_SCOPE_"
        ):
            raise
        raise RuntimeError(
            "RP5A_VALIDATION_SCOPE_BASELINE_LOAD_FAILED:"
            f"{semantic_label}:{VALIDATION_SCOPE_RUNNER_PATH}"
        ) from exc
    finally:
        sys.modules.pop(module_name, None)


def _validation_scope_delta() -> dict[str, object]:
    (
        internal_ref,
        semantic_label,
        comparison_mode,
    ) = _validation_scope_baseline()
    baseline_counter = _validation_scope_counter(
        _baseline_phase_manifest(internal_ref, semantic_label)
    )
    current_counter = _validation_scope_counter(
        current_validation_runner.build_phase_manifest(
            VALIDATION_SCOPE_VALIDATION_DIR,
            VALIDATION_SCOPE_PYTEST_BASETEMP,
        )
    )
    removed, added = _validation_scope_counter_delta(
        baseline_counter,
        current_counter,
    )
    current_inventory_failures = list(validate_inventory())
    removed_count = sum(removed.values())
    added_count = sum(added.values())
    return {
        "validation_scope_evidence_schema_version": (
            VALIDATION_SCOPE_EVIDENCE_SCHEMA_VERSION
        ),
        "validation_scope_snapshot_context": (
            VALIDATION_SCOPE_SNAPSHOT_CONTEXT
        ),
        "validation_scope_comparison_mode": comparison_mode,
        "validation_scope_baseline_ref": semantic_label,
        "validation_scope_baseline_command_count": sum(
            baseline_counter.values()
        ),
        "validation_scope_current_command_count": sum(
            current_counter.values()
        ),
        "validation_scope_added_count": added_count,
        "validation_scope_removed_count": removed_count,
        "validation_scope_removed_refs": _validation_scope_refs(removed),
        "current_validation_inventory_failure_count": len(
            current_inventory_failures
        ),
        "current_validation_inventory_failures": (
            current_inventory_failures
        ),
        "validation_scope_changed_flag": bool(added or removed),
        "validation_scope_change_type": (
            "SEMANTIC_COMMAND_REMOVAL_DETECTED"
            if removed
            else (
                "SEMANTIC_COMMAND_ADDITION_ONLY"
                if added
                else "NONE"
            )
        ),
        "no_legacy_scope_removal_flag": (
            removed_count == 0 and not current_inventory_failures
        ),
    }


_ALLOWED_CURRENTIZATION_ARTIFACT_PATHS = frozenset(
    {
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
    }
)


def _status_path(line: str) -> str:
    return normalize_repo_path(line[3:] if len(line) > 3 else line)


def _status_code(line: str) -> str:
    return line[:2].strip()


def _is_legacy_generated_artifact_path(path: str) -> bool:
    return (
        path.startswith("docs/master_plan/generated/")
        and not is_owned_rp5a_path(path)
        and path not in _ALLOWED_CURRENTIZATION_ARTIFACT_PATHS
    )


def _no_deletion_proof(baseline_status_rows: list[str] | None = None) -> dict[str, object]:
    baseline_status_rows = baseline_status_rows or []
    baseline_legacy_modified = {
        _status_path(line)
        for line in baseline_status_rows
        if _status_code(line) in {"M", "A"}
        and _is_legacy_generated_artifact_path(_status_path(line))
    }
    rows = _status_rows()
    deleted = [line for line in rows if _status_code(line) == "D" or "D" in line[:2]]
    moved = [line for line in rows if "R" in line[:2]]
    legacy_modified = []
    for line in rows:
        path = _status_path(line)
        if (
            _is_legacy_generated_artifact_path(path)
            and _status_code(line) in {"M", "A"}
            and path not in baseline_legacy_modified
        ):
            legacy_modified.append(path)
    validation_scope_delta = _validation_scope_delta()
    return {
        **FORBIDDEN_OPERATION_COUNTERS,
        "deleted_file_count": len(deleted),
        "moved_file_count": len(moved),
        "archived_file_count": 0,
        "legacy_artifact_content_modified_count": len(legacy_modified),
        **validation_scope_delta,
        "runtime_stack_generation_count": 0,
        "trade_simulation_count": 0,
        "formula_reclaim_count": 0,
        "active_registry_authority_created_count": 0,
        "runtime_stack_generation_refs": [],
        "trade_simulation_refs": [],
        "formula_reclaim_refs": [],
        "legacy_modified_refs": legacy_modified[:50],
        "preexisting_legacy_artifact_modified_count": len(baseline_legacy_modified),
        "preexisting_legacy_artifact_modified_refs": sorted(baseline_legacy_modified)[:50],
        "deleted_refs": deleted,
        "moved_refs": moved,
    }


def _path_audit_rows(extra_owned_paths: list[str]) -> list[dict[str, object]]:
    paths = [f"docs/master_plan/generated/{name}" for name in REPORT_NAMES]
    for key in ROW_SHARDS:
        shard = shard_path(key)
        paths.append(generated_ref(shard))
        paths.append(generated_ref(manifest_path_for_shard(shard)))
    paths.extend(extra_owned_paths)
    rows: list[dict[str, object]] = []
    for index, path in enumerate(sorted(set(paths)), start=1):
        length = len(path)
        rows.append(
            {
                "row_id": f"RP5A_PATH_{index:04d}",
                "file_path": path,
                "physical_path_length": length,
                "preferred_max_physical_path_length": 180,
                "warning_threshold_physical_path_length": WARNING_THRESHOLD_PHYSICAL_PATH_LENGTH,
                "hard_fail_physical_path_length": HARD_FAIL_PHYSICAL_PATH_LENGTH,
                "path_status": "FAIL" if length >= HARD_FAIL_PHYSICAL_PATH_LENGTH else "WARN" if length >= WARNING_THRESHOLD_PHYSICAL_PATH_LENGTH else "PASS",
            }
        )
    return rows


_FILE_KIND_SUMMARY_FIELDS = {
    FILE_KIND_GENERATED_REPORT: "generated_reports_with_stale_terms_count",
    FILE_KIND_GENERATED_SHARD: "generated_shards_with_stale_terms_count",
    FILE_KIND_TOOL_SOURCE: "tools_with_stale_terms_count",
    FILE_KIND_TEST_SOURCE: "tests_with_stale_terms_count",
    FILE_KIND_VALIDATOR: "validators_with_stale_terms_count",
    FILE_KIND_DOC: "docs_with_stale_terms_count",
    FILE_KIND_CURRENTIZATION: "currentization_with_stale_terms_count",
    FILE_KIND_MANIFEST: "manifests_with_stale_terms_count",
}
_DELETE_CLASSIFICATION_SUMMARY_FIELDS = {
    "DELETE_FROM_ACTIVE_TREE_SAFE": (
        "delete_from_active_tree_safe_draft_count"
    ),
    "DELETE_AFTER_QKU_FORMULA_IDENTITY_RECLAIM": (
        "delete_after_qku_formula_identity_reclaim_count"
    ),
    "KEEP_ACTIVE_CONSUMER": "keep_active_consumer_count",
    "KEEP_UNIQUE_QKU_FORMULA_SOURCE": (
        "keep_unique_qku_formula_source_count"
    ),
    "KEEP_TEST_FIXTURE": "keep_test_fixture_count",
    "KEEP_VALIDATION_DEPENDENCY": "keep_validation_dependency_count",
    "KEEP_LEGACY_SUMMARY_ONLY": "keep_legacy_summary_only_count",
    "ARCHIVE_NO_VALIDATION_SCAN": "archive_no_validation_scan_count",
    "REWRITE_CONSUMER_FIRST": "rewrite_consumer_first_count",
    "UNCLEAR_DO_NOT_DELETE": "unclear_do_not_delete_count",
}


def _required_summary_count(
    owner: Mapping[str, object],
    field: str,
    owner_name: str,
) -> int:
    value = owner.get(field)
    if (
        not isinstance(value, int)
        or isinstance(value, bool)
        or value < 0
    ):
        raise RuntimeError(
            f"RP5A_SUMMARY_OWNER_COUNT_INVALID:{owner_name}:{field}"
        )
    return value


def _report_summary_counts(
    *,
    input_summary: Mapping[str, object],
    performance_summary: Mapping[str, object],
    legacy_pr_summary: Mapping[str, object],
    term_rows: Sequence[Mapping[str, object]],
    file_rows: Sequence[Mapping[str, object]],
    hit_rows: Sequence[Mapping[str, object]],
    consumer_rows: Sequence[Mapping[str, object]],
    validation_rows: Sequence[Mapping[str, object]],
    identity_rows: Sequence[Mapping[str, object]],
    custody_rows: Sequence[Mapping[str, object]],
    agent_rows: Sequence[Mapping[str, object]],
    blast_rows: Sequence[Mapping[str, object]],
    validation_time_rows: Sequence[Mapping[str, object]],
    delete_rows: Sequence[Mapping[str, object]],
    delete_manifest: Mapping[str, object],
    no_delete: Mapping[str, object],
) -> dict[str, object]:
    input_files_scanned = _required_summary_count(
        input_summary,
        "files_scanned_count",
        "Input",
    )
    performance_files_scanned = _required_summary_count(
        performance_summary,
        "files_scanned_count",
        "ScanPerformance",
    )
    if input_files_scanned != performance_files_scanned:
        raise RuntimeError(
            "RP5A_SUMMARY_FILES_SCANNED_OWNER_MISMATCH:"
            f"{input_files_scanned}:{performance_files_scanned}"
        )
    github_prs_scanned = _required_summary_count(
        legacy_pr_summary,
        "github_prs_scanned_count",
        "LegacyPRSemanticAudit",
    )
    github_prs_with_stale_terms = _required_summary_count(
        legacy_pr_summary,
        "github_prs_with_stale_terms_count",
        "LegacyPRSemanticAudit",
    )
    kind_counts = Counter(str(row["file_kind"]) for row in file_rows)
    class_counts = Counter(str(row["classification"]) for row in delete_rows)
    unexpected_classes = sorted(
        set(class_counts) - set(_DELETE_CLASSIFICATION_SUMMARY_FIELDS)
    )
    if unexpected_classes:
        raise RuntimeError(
            "RP5A_SUMMARY_DELETE_CLASSIFICATION_UNKNOWN:"
            f"{unexpected_classes}"
        )
    delete_manifest_count = _required_summary_count(
        delete_manifest,
        "row_count",
        "delete_eligibility_rows.manifest",
    )
    if delete_manifest_count != len(delete_rows):
        raise RuntimeError(
            "RP5A_SUMMARY_DELETE_MANIFEST_ROW_COUNT_MISMATCH:"
            f"{delete_manifest_count}:{len(delete_rows)}"
        )
    classification_counts = {
        summary_field: class_counts[classification]
        for classification, summary_field
        in _DELETE_CLASSIFICATION_SUMMARY_FIELDS.items()
    }
    if sum(classification_counts.values()) != delete_manifest_count:
        raise RuntimeError(
            "RP5A_SUMMARY_DELETE_CLASSIFICATION_TOTAL_MISMATCH:"
            f"{sum(classification_counts.values())}:{delete_manifest_count}"
        )
    return {
        "pr240_closed_not_merged_preflight_passed": True,
        "stale_term_taxonomy_count": len(term_rows),
        "github_prs_scanned_count": github_prs_scanned,
        "github_prs_with_stale_terms_count": (
            github_prs_with_stale_terms
        ),
        "files_scanned_count": input_files_scanned,
        "files_with_stale_terms_count": len(file_rows),
        **{
            summary_field: kind_counts[file_kind]
            for file_kind, summary_field in _FILE_KIND_SUMMARY_FIELDS.items()
        },
        "row_field_semantic_hit_count": len(hit_rows),
        "consumer_graph_row_count": len(consumer_rows),
        "active_consumer_file_count": len(
            {
                row["file_path"]
                for row in consumer_rows
                if row.get("active_consumer_flag")
            }
        ),
        "validation_dependency_row_count": len(validation_rows),
        "validation_dependent_file_count": len(
            {
                row["file_path_or_prefix"]
                for row in validation_rows
                if row.get("validation_dependency_type") != "NONE"
            }
        ),
        "qku_formula_identity_dependency_file_count": len(
            [row for row in identity_rows if row.get("identity_count")]
        ),
        "identity_custody_row_count": len(custody_rows),
        "agent_touchpoint_file_count": len(
            {
                row["file_path"]
                for row in agent_rows
                if row.get("active_agent_touchpoint_flag")
            }
        ),
        "blast_radius_row_count": len(blast_rows),
        "validation_time_risk_row_count": len(validation_time_rows),
        **classification_counts,
        **{
            key: _required_summary_count(
                no_delete,
                key,
                "NoDeletionProof",
            )
            for key in FORBIDDEN_OPERATION_COUNTERS
        },
        **{
            field: no_delete[field]
            for field in VALIDATION_SCOPE_EVIDENCE_FIELDS
        },
    }


_REPORT_PAYLOAD_METADATA_FIELDS = frozenset(
    {
        "logical_report_id",
        "physical_filename",
        "report_version",
        "created_at_utc",
        "audit_only_flag",
        "records",
        "rows_ref",
        "manifest_ref",
    }
)
_VALIDATION_SCOPE_EVIDENCE_ONLY_REPORTS = (
    "PR168_RP5A_NoDeletionProof.report.json",
    "PR168_RP5A_FinalSummary.report.json",
)
_PR_METADATA_COMMITTED_FALLBACK_SOURCE = (
    "existing_committed_rows_fallback"
)
_PR_METADATA_REQUIRED_SUMMARY_FIELDS = (
    "github_prs_scanned_count",
    "github_prs_with_stale_terms_count",
    "pr240_closed_not_merged_preflight_passed",
)


def _validated_pr_metadata_owner(
    rows: object,
    summary: object,
    *,
    owner: str,
) -> tuple[list[dict[str, object]], dict[str, object]]:
    if (
        not isinstance(rows, list)
        or any(not isinstance(row, dict) for row in rows)
    ):
        raise RuntimeError(
            f"RP5A_PR_METADATA_{owner}_ROWS_INVALID"
        )
    if not isinstance(summary, Mapping):
        raise RuntimeError(
            f"RP5A_PR_METADATA_{owner}_SUMMARY_INVALID"
        )

    counts: dict[str, int] = {}
    for field, label in (
        ("github_prs_scanned_count", "SCANNED_COUNT"),
        ("github_prs_with_stale_terms_count", "STALE_COUNT"),
    ):
        value = summary.get(field)
        if (
            not isinstance(value, int)
            or isinstance(value, bool)
            or value < 0
        ):
            raise RuntimeError(
                f"RP5A_PR_METADATA_{owner}_{label}_INVALID"
            )
        counts[field] = value

    scanned_count = counts["github_prs_scanned_count"]
    stale_count = counts["github_prs_with_stale_terms_count"]
    if scanned_count < stale_count:
        raise RuntimeError(
            f"RP5A_PR_METADATA_{owner}_SCANNED_BELOW_STALE"
        )
    matched_row_count = sum(
        bool(row.get("matched_terms")) for row in rows
    )
    if stale_count != matched_row_count:
        raise RuntimeError(
            f"RP5A_PR_METADATA_{owner}_STALE_ROW_COUNT_MISMATCH"
        )
    if (
        summary.get("pr240_closed_not_merged_preflight_passed")
        is not True
    ):
        raise RuntimeError(
            f"RP5A_PR_METADATA_{owner}_PR240_CLOSURE_INVALID"
        )
    return rows, dict(summary)


def _load_committed_pr_metadata_owner(
    existing_rows_path: Path,
    existing_report_path: Path,
) -> tuple[list[dict[str, object]], dict[str, object]]:
    try:
        rows = read_jsonl(existing_rows_path)
    except Exception as exc:
        raise RuntimeError(
            "RP5A_PR_METADATA_COMMITTED_ROWS_LOAD_FAILED"
        ) from exc
    try:
        manifest = read_json(
            manifest_path_for_shard(existing_rows_path)
        )
    except Exception as exc:
        raise RuntimeError(
            "RP5A_PR_METADATA_COMMITTED_MANIFEST_LOAD_FAILED"
        ) from exc
    try:
        report = read_json(existing_report_path)
    except Exception as exc:
        raise RuntimeError(
            "RP5A_PR_METADATA_COMMITTED_REPORT_LOAD_FAILED"
        ) from exc

    if not isinstance(manifest, Mapping):
        raise RuntimeError(
            "RP5A_PR_METADATA_COMMITTED_MANIFEST_INVALID"
        )
    manifest_count = manifest.get("row_count")
    if (
        not isinstance(manifest_count, int)
        or isinstance(manifest_count, bool)
        or manifest_count < 0
    ):
        raise RuntimeError(
            "RP5A_PR_METADATA_COMMITTED_MANIFEST_ROW_COUNT_INVALID"
        )
    if not isinstance(rows, list) or manifest_count != len(rows):
        raise RuntimeError(
            "RP5A_PR_METADATA_COMMITTED_MANIFEST_ROW_COUNT_MISMATCH"
        )
    if not isinstance(report, Mapping):
        raise RuntimeError(
            "RP5A_PR_METADATA_COMMITTED_REPORT_INVALID"
        )
    summary = {
        key: value
        for key, value in report.items()
        if key not in _REPORT_PAYLOAD_METADATA_FIELDS
    }
    return _validated_pr_metadata_owner(
        rows,
        summary,
        owner="COMMITTED",
    )


def _resolve_pr_metadata(
    *,
    offline: bool,
    existing_rows_path: Path,
    existing_report_path: Path,
) -> tuple[list[dict[str, object]], dict[str, object]]:
    if offline:
        return _load_committed_pr_metadata_owner(
            existing_rows_path,
            existing_report_path,
        )

    live_rows, live_summary = fetch_pr_metadata_rows(
        existing_rows_path
    )
    if not isinstance(live_summary, Mapping):
        raise RuntimeError(
            "RP5A_PR_METADATA_LIVE_SUMMARY_INVALID"
        )
    if (
        live_summary.get("github_metadata_source")
        == _PR_METADATA_COMMITTED_FALLBACK_SOURCE
    ):
        return _load_committed_pr_metadata_owner(
            existing_rows_path,
            existing_report_path,
        )
    missing_fields = [
        field
        for field in _PR_METADATA_REQUIRED_SUMMARY_FIELDS
        if field not in live_summary
    ]
    if missing_fields:
        raise RuntimeError(
            "RP5A_PR_METADATA_LIVE_SUMMARY_INCOMPLETE:"
            + ",".join(missing_fields)
        )
    return _validated_pr_metadata_owner(
        live_rows,
        live_summary,
        owner="LIVE",
    )


def _persisted_report_summary_counts(
    no_delete: Mapping[str, object],
) -> dict[str, object]:
    delete_shard = shard_path("delete_eligibility_rows")
    return _report_summary_counts(
        input_summary=read_json(
            report_path("PR168_RP5A_Input.report.json")
        ),
        performance_summary=read_json(
            report_path("PR168_RP5A_ScanPerformance.report.json")
        ),
        legacy_pr_summary=read_json(
            report_path("PR168_RP5A_LegacyPRSemanticAudit.report.json")
        ),
        term_rows=read_jsonl(shard_path("term_taxonomy_rows")),
        file_rows=read_jsonl(shard_path("legacy_file_semantic_rows")),
        hit_rows=read_jsonl(shard_path("row_field_semantic_hit_rows")),
        consumer_rows=read_jsonl(shard_path("consumer_graph_rows")),
        validation_rows=read_jsonl(
            shard_path("validation_dependency_rows")
        ),
        identity_rows=read_jsonl(
            shard_path("qku_formula_identity_dependency_rows")
        ),
        custody_rows=read_jsonl(shard_path("identity_custody_rows")),
        agent_rows=read_jsonl(shard_path("agent_touchpoint_rows")),
        blast_rows=read_jsonl(shard_path("blast_radius_rows")),
        validation_time_rows=read_jsonl(
            shard_path("validation_time_risk_rows")
        ),
        delete_rows=read_jsonl(delete_shard),
        delete_manifest=read_json(
            manifest_path_for_shard(delete_shard)
        ),
        no_delete=no_delete,
    )


def _validation_scope_evidence_only_payloads(
) -> dict[str, dict[str, Any]]:
    no_delete_report = read_json(
        report_path("PR168_RP5A_NoDeletionProof.report.json")
    )
    no_delete_summary = {
        key: value
        for key, value in no_delete_report.items()
        if key not in _REPORT_PAYLOAD_METADATA_FIELDS
    }
    no_delete_summary.update(_validation_scope_delta())
    summary_counts = _persisted_report_summary_counts(no_delete_summary)
    return {
        "PR168_RP5A_NoDeletionProof.report.json": report_payload(
            "PR168_RP5A_NoDeletionProof.report.json",
            summary=no_delete_summary,
            records=no_delete_summary,
        ),
        "PR168_RP5A_FinalSummary.report.json": report_payload(
            "PR168_RP5A_FinalSummary.report.json",
            summary=summary_counts,
            records=summary_counts,
        ),
    }


def currentize_validation_scope_evidence_only(
) -> dict[str, dict[str, Any]]:
    branch = current_branch_context(REPO_ROOT).branch
    if branch != ST12A_BRANCH:
        raise RuntimeError(
            "RP5A_VALIDATION_SCOPE_EVIDENCE_ONLY_BRANCH_INVALID:"
            f"{branch}"
        )
    payloads = _validation_scope_evidence_only_payloads()
    if tuple(payloads) != _VALIDATION_SCOPE_EVIDENCE_ONLY_REPORTS:
        raise RuntimeError(
            "RP5A_VALIDATION_SCOPE_EVIDENCE_ONLY_PATH_SET_INVALID"
        )
    for report_name, payload in payloads.items():
        write_json(report_path(report_name), payload)
    print("PR168_RP5A_VALIDATION_SCOPE_EVIDENCE_CURRENTIZED")
    return payloads


def _quick_selftest_files(files: list[str]) -> list[str]:
    preferred_tokens = (
        "QTT_MasterPlan_Current.md",
        "docs/master_plan/",
        "docs/roadmap/",
        "docs/master_plan/generated/",
        "tools/",
        "tests/",
    )
    preferred = [path for path in files if any(token in path for token in preferred_tokens)]
    remainder = [path for path in files if path not in set(preferred)]
    return [*preferred[:900], *remainder[:100]][:1000]


def build_all(*, offline: bool = True, quick_selftest: bool = False) -> dict[str, object]:
    timer = PhaseTimer()
    baseline_status_rows = _status_rows()
    _write_checkpoint("start", offline=offline, quick_selftest=quick_selftest)
    _log_phase("start", started_at=timer.started_at)
    phase = timer.start_phase()
    existing_preflight = report_path("PR168_RP5A_Preflight.report.json")
    preflight = _collect_preflight(existing_preflight)
    crosswalk_status = pr165_d2_crosswalk_status(REPO_ROOT)
    timer.mark("preflight_and_crosswalk", phase)
    _write_checkpoint("preflight_and_crosswalk", pr240_ok=preflight.get("pr240_closed_not_merged_preflight_passed"))
    _log_phase("preflight_and_crosswalk", started_at=timer.started_at)

    phase = timer.start_phase()
    all_files = scannable_files(REPO_ROOT)
    files = _quick_selftest_files(all_files) if quick_selftest else all_files[:MAX_FILES_SCANNED]
    max_wall_seconds = 180 if quick_selftest else MAX_WALL_SECONDS
    max_files_scanned = len(files) if quick_selftest else MAX_FILES_SCANNED
    max_matched_files = 1_000 if quick_selftest else MAX_MATCHED_FILES
    max_total_line_hits = 10_000 if quick_selftest else MAX_TOTAL_LINE_HITS
    line_rows, _file_index, scan_stats = scan_files_for_terms(
        files,
        REPO_ROOT,
        max_wall_seconds=max_wall_seconds,
        max_files_scanned=max_files_scanned,
        max_matched_files=max_matched_files,
        max_total_line_hits=max_total_line_hits,
        progress_interval_seconds=PROGRESS_INTERVAL_SECONDS,
    )
    timer.mark("rg_two_pass_line_scan", phase)
    checkpoint_scan_stats = {key: value for key, value in scan_stats.items() if key != "files_scanned_count"}
    _write_checkpoint("rg_two_pass_line_scan", files_scanned_count=len(files), line_hit_count=len(line_rows), **checkpoint_scan_stats)
    _log_phase("rg_two_pass_line_scan", files_processed=len(files), matched_files=int(scan_stats.get("matched_files_count", 0)), started_at=timer.started_at)

    phase = timer.start_phase()
    hit_rows = build_row_field_hits(line_rows, REPO_ROOT)
    file_term_map = _group_hits_by_file(hit_rows)
    matched_files = sorted(file_term_map)
    timer.mark("bounded_row_field_hit_index", phase)
    _write_checkpoint("bounded_row_field_hit_index", matched_files_count=len(matched_files), row_field_semantic_hit_count=len(hit_rows), **LAST_ROW_FIELD_STATS)
    _log_phase("bounded_row_field_hit_index", files_processed=len(files), matched_files=len(matched_files), started_at=timer.started_at)

    phase = timer.start_phase()
    pr_existing_rows = SHARD_ROOT / ROW_SHARDS["legacy_pr_semantic_rows"]
    pr_rows, pr_summary = _resolve_pr_metadata(
        offline=offline,
        existing_rows_path=pr_existing_rows,
        existing_report_path=report_path(
            "PR168_RP5A_LegacyPRSemanticAudit.report.json"
        ),
    )
    timer.mark("github_pr_metadata", phase)
    _write_checkpoint("github_pr_metadata", pr_rows_count=len(pr_rows))
    _log_phase("github_pr_metadata", files_processed=len(files), matched_files=len(matched_files), started_at=timer.started_at)

    phase = timer.start_phase()
    validation_rows = build_validation_dependency_rows(matched_files)
    consumer_rows = build_consumer_graph(matched_files, REPO_ROOT, validation_rows=validation_rows)
    timer.mark("bounded_dependency_graphs", phase)
    _write_checkpoint("bounded_dependency_graphs", consumer_rows_count=len(consumer_rows), validation_dependency_rows_count=len(validation_rows))
    _log_phase("bounded_dependency_graphs", files_processed=len(files), matched_files=len(matched_files), started_at=timer.started_at)

    phase = timer.start_phase()
    identity_occurrences = scan_identity_occurrences(REPO_ROOT, matched_files)
    identity_rows = build_identity_dependency_rows(matched_files, identity_occurrences)
    custody_rows = build_identity_custody_rows(matched_files, identity_occurrences)
    agent_rows = build_agent_touchpoint_rows(matched_files, REPO_ROOT)
    timer.mark("identity_and_agent_touchpoints", phase)
    _write_checkpoint("identity_and_agent_touchpoints", identity_rows_count=len(identity_rows), custody_rows_count=len(custody_rows), agent_rows_count=len(agent_rows))
    _log_phase("identity_and_agent_touchpoints", files_processed=len(files), matched_files=len(matched_files), started_at=timer.started_at)

    phase = timer.start_phase()
    blast_rows = build_blast_radius_rows(matched_files, file_term_map, consumer_rows, validation_rows, identity_rows, agent_rows)
    delete_rows = build_delete_eligibility_rows(matched_files, file_term_map, consumer_rows, validation_rows, identity_rows, agent_rows, blast_rows)
    if scan_stats.get("budget_exhausted_flag"):
        for row in delete_rows:
            if row.get("classification") == "DELETE_FROM_ACTIVE_TREE_SAFE":
                row["classification"] = "UNCLEAR_DO_NOT_DELETE"
                row["classification_reason"] = (
                    "Scan budget exhausted before exhaustive audit; future cleanup requires a complete replacement or operator review."
                )
                row["future_cleanup_pr"] = "UNKNOWN"
                row["operator_review_required_flag"] = True
                row["delete_in_future_allowed_after_conditions"] = "Resolve SCAN_BUDGET_EXHAUSTED and rerun RP5A/RP5B dependency proof."
        existing_delete_paths = {str(row["file_path"]) for row in delete_rows}
        for skipped_path in scan_stats.get("skipped_large_line_scan_files_all", []) or []:
            if skipped_path in existing_delete_paths:
                continue
            delete_rows.append(
                {
                    "row_id": f"RP5A_DELETE_BUDGET_{len(delete_rows) + 1:07d}",
                    "file_path": skipped_path,
                    "classification": "UNCLEAR_DO_NOT_DELETE",
                    "classification_reason": (
                        "Candidate file matched bounded rg Pass A, but Pass B line-hit extraction was skipped by size/runtime budget."
                    ),
                    "stale_term_refs": [],
                    "consumer_graph_refs": [],
                    "validation_dependency_refs": [],
                    "identity_dependency_refs": [],
                    "agent_touchpoint_refs": [],
                    "blast_radius_refs": [],
                    "future_cleanup_pr": "UNKNOWN",
                    "delete_now_flag": False,
                    "delete_in_future_allowed_after_conditions": "Resolve SCAN_BUDGET_EXHAUSTED and rerun bounded line-hit proof.",
                    "operator_review_required_flag": True,
                    "scan_budget_status": "SCAN_BUDGET_EXHAUSTED",
                }
            )
            existing_delete_paths.add(str(skipped_path))
    consistency_rows = build_consistency_report_rows(delete_rows, consumer_rows, validation_rows, identity_rows, agent_rows)
    validation_time_rows = build_validation_time_risk_rows(matched_files, REPO_ROOT)
    file_rows = _file_semantic_rows(matched_files, file_term_map, pr_rows, consumer_rows, validation_rows, identity_rows, agent_rows, delete_rows)
    wrong_term_rows = _wrong_concept_rows(hit_rows, pr_rows)
    future_rows = _future_plan_rows(delete_rows, validation_rows, identity_rows, consumer_rows)
    no_delete = _no_deletion_proof(baseline_status_rows)
    input_rows = _input_rows(files, preflight, crosswalk_status)
    timer.mark("classification_and_reports_in_memory", phase)
    _write_checkpoint("classification_and_reports_in_memory", delete_rows_count=len(delete_rows), consistency_failures=len([row for row in consistency_rows if not row["consistent_flag"]]))
    _log_phase("classification_and_reports_in_memory", files_processed=len(files), matched_files=len(matched_files), started_at=timer.started_at)

    phase = timer.start_phase()
    path_rows = _path_audit_rows(
        [
            "tools/build_pr168_rp5a_legacy_semantic_audit.py",
            "tools/validate_pr168_rp5a_legacy_semantic_audit.py",
            "tools/pr168_rp5a_config.py",
            "tests/pr168_rp5a/_helpers.py",
        ]
    )
    performance_report = {
        "files_scanned_count": len(files),
        "files_available_count": len(all_files),
        "matched_files_count": len(matched_files),
        "candidate_files_count": int(scan_stats.get("candidate_files_count", 0)),
        "matched_files_processed_count": int(scan_stats.get("matched_files_processed_count", 0)),
        "elapsed_seconds_by_phase": dict(timer.elapsed),
        "total_elapsed_seconds": timer.total(),
        "peak_memory_strategy": (
            "RG_TEMP_FILE_TWO_PASS_BOUNDED_HITS"
            if bool(scan_stats.get("rg_used_flag"))
            else (
                "GIT_GREP_TEMP_FILE_TWO_PASS_BOUNDED_HITS"
                if bool(scan_stats.get("git_grep_used_flag"))
                else "PYTHON_FALLBACK_STREAMING_BOUNDED_LINE_SCAN"
            )
        ),
        "scan_budget_status": scan_stats.get("scan_budget_status", "SCAN_BUDGET_OK"),
        "budget_exhausted_flag": bool(scan_stats.get("budget_exhausted_flag")),
        "budget_exhaustion_reasons": scan_stats.get("budget_exhaustion_reasons", []),
        "scan_budget_exhausted_handling": "unfinished_or_unclear_files_classified_UNCLEAR_DO_NOT_DELETE",
        "capped_file_count": int(scan_stats.get("capped_file_count", 0)),
        "capped_match_count": int(scan_stats.get("capped_match_count", 0)),
        "skipped_large_structured_file_count": int(LAST_ROW_FIELD_STATS.get("skipped_large_structured_file_count", 0)),
        "skipped_large_structured_files_limited": LAST_ROW_FIELD_STATS.get("skipped_large_structured_files_limited", []),
        "skipped_large_line_scan_file_count": int(scan_stats.get("skipped_large_line_scan_file_count", 0)),
        "skipped_large_line_scan_files_limited": scan_stats.get("skipped_large_line_scan_files_limited", []),
        "row_field_budget_exhausted_flag": bool(LAST_ROW_FIELD_STATS.get("row_field_budget_exhausted_flag")),
        "rg_used_flag": bool(scan_stats.get("rg_used_flag")),
        "git_grep_used_flag": bool(scan_stats.get("git_grep_used_flag")),
        "python_fallback_used_flag": bool(scan_stats.get("python_fallback_used_flag")),
        "quick_selftest_flag": quick_selftest,
        "max_wall_seconds": max_wall_seconds,
        "max_files_scanned": max_files_scanned,
        "max_matched_files": max_matched_files,
        "max_line_hits_per_file": MAX_LINE_HITS_PER_FILE,
        "max_total_line_hits": max_total_line_hits,
        "max_consumer_refs_per_file": MAX_CONSUMER_REFS_PER_FILE,
        "max_identity_refs_per_file": MAX_IDENTITY_REFS_PER_FILE,
        "max_structured_json_bytes": MAX_STRUCTURED_JSON_BYTES,
        "max_total_rows_per_shard": MAX_TOTAL_ROWS_PER_SHARD,
        "consumer_graph_scan_mode": "BOUNDED_STATUS_ONLY_NO_ALL_PAIRS",
        "checkpoint_path": ".tmp/rp5a_scan_checkpoint.json",
        "checkpoint_committed_flag": False,
    }

    shard_material: dict[str, tuple[list[dict[str, Any]], dict[str, Any]]] = {}
    shard_material["input_rows"] = write_shard("input_rows", input_rows, logical_family_id="PR168_RP5A_INPUT_ROWS")
    shard_material["term_taxonomy_rows"] = write_shard("term_taxonomy_rows", taxonomy_rows(), logical_family_id="PR168_RP5A_TERM_TAXONOMY_ROWS")
    shard_material["legacy_pr_semantic_rows"] = write_shard("legacy_pr_semantic_rows", pr_rows, logical_family_id="PR168_RP5A_LEGACY_PR_SEMANTIC_ROWS")
    shard_material["legacy_file_semantic_rows"] = write_shard("legacy_file_semantic_rows", file_rows, logical_family_id="PR168_RP5A_LEGACY_FILE_SEMANTIC_ROWS")
    shard_material["row_field_semantic_hit_rows"] = write_shard("row_field_semantic_hit_rows", hit_rows, logical_family_id="PR168_RP5A_ROW_FIELD_HIT_ROWS")
    shard_material["wrong_concept_term_rows"] = write_shard("wrong_concept_term_rows", wrong_term_rows, logical_family_id="PR168_RP5A_WRONG_CONCEPT_TERM_ROWS")
    shard_material["consumer_graph_rows"] = write_shard("consumer_graph_rows", consumer_rows, logical_family_id="PR168_RP5A_CONSUMER_GRAPH_ROWS")
    shard_material["validation_dependency_rows"] = write_shard("validation_dependency_rows", validation_rows, logical_family_id="PR168_RP5A_VALIDATION_DEPENDENCY_ROWS")
    shard_material["qku_formula_identity_dependency_rows"] = write_shard("qku_formula_identity_dependency_rows", identity_rows, logical_family_id="PR168_RP5A_IDENTITY_DEPENDENCY_ROWS")
    shard_material["identity_custody_rows"] = write_shard("identity_custody_rows", custody_rows, logical_family_id="PR168_RP5A_IDENTITY_CUSTODY_ROWS")
    shard_material["agent_touchpoint_rows"] = write_shard("agent_touchpoint_rows", agent_rows, logical_family_id="PR168_RP5A_AGENT_TOUCHPOINT_ROWS")
    shard_material["blast_radius_rows"] = write_shard("blast_radius_rows", blast_rows, logical_family_id="PR168_RP5A_BLAST_RADIUS_ROWS")
    shard_material["validation_time_risk_rows"] = write_shard("validation_time_risk_rows", validation_time_rows, logical_family_id="PR168_RP5A_VALIDATION_TIME_RISK_ROWS")
    shard_material["delete_eligibility_rows"] = write_shard("delete_eligibility_rows", delete_rows, logical_family_id="PR168_RP5A_DELETE_ELIGIBILITY_ROWS")
    shard_material["future_rp5b_plan_rows"] = write_shard("future_rp5b_plan_rows", future_rows, logical_family_id="PR168_RP5A_FUTURE_RP5B_PLAN_ROWS")

    def refs(key: str) -> tuple[str, str]:
        shard = shard_path(key)
        return generated_ref(shard), generated_ref(manifest_path_for_shard(shard))

    persisted_summary_rows = {
        key: read_jsonl(shard_path(key))
        for key in (
            "term_taxonomy_rows",
            "legacy_file_semantic_rows",
            "row_field_semantic_hit_rows",
            "consumer_graph_rows",
            "validation_dependency_rows",
            "qku_formula_identity_dependency_rows",
            "identity_custody_rows",
            "agent_touchpoint_rows",
            "blast_radius_rows",
            "validation_time_risk_rows",
            "delete_eligibility_rows",
        )
    }
    summary_counts = _report_summary_counts(
        input_summary={"files_scanned_count": len(files)},
        performance_summary=performance_report,
        legacy_pr_summary=pr_summary,
        term_rows=persisted_summary_rows["term_taxonomy_rows"],
        file_rows=persisted_summary_rows["legacy_file_semantic_rows"],
        hit_rows=persisted_summary_rows["row_field_semantic_hit_rows"],
        consumer_rows=persisted_summary_rows["consumer_graph_rows"],
        validation_rows=persisted_summary_rows[
            "validation_dependency_rows"
        ],
        identity_rows=persisted_summary_rows[
            "qku_formula_identity_dependency_rows"
        ],
        custody_rows=persisted_summary_rows["identity_custody_rows"],
        agent_rows=persisted_summary_rows["agent_touchpoint_rows"],
        blast_rows=persisted_summary_rows["blast_radius_rows"],
        validation_time_rows=persisted_summary_rows[
            "validation_time_risk_rows"
        ],
        delete_rows=persisted_summary_rows["delete_eligibility_rows"],
        delete_manifest=shard_material["delete_eligibility_rows"][1],
        no_delete=no_delete,
    )
    summary_counts["pr240_closed_not_merged_preflight_passed"] = bool(pr_summary.get("pr240_closed_not_merged_preflight_passed") and preflight.get("pr240_closed_not_merged_preflight_passed"))

    write_report("PR168_RP5A_Input.report.json", summary={"files_scanned_count": len(files), "scan_excludes_rp5a_outputs_flag": True}, rows_ref=refs("input_rows")[0], manifest_ref=refs("input_rows")[1], records=input_rows)
    write_report("PR168_RP5A_Preflight.report.json", summary=preflight, records=preflight)
    write_report("PR168_RP5A_TermTaxonomy.report.json", summary={"stale_term_taxonomy_count": len(TERM_BY_ID)}, rows_ref=refs("term_taxonomy_rows")[0], manifest_ref=refs("term_taxonomy_rows")[1], records=taxonomy_rows()[:25])
    write_report("PR168_RP5A_LegacyPRSemanticAudit.report.json", summary=pr_summary, rows_ref=refs("legacy_pr_semantic_rows")[0], manifest_ref=refs("legacy_pr_semantic_rows")[1], records=pr_rows[:25])
    write_report("PR168_RP5A_LegacyFileSemanticAudit.report.json", summary={"files_with_stale_terms_count": len(file_rows)}, rows_ref=refs("legacy_file_semantic_rows")[0], manifest_ref=refs("legacy_file_semantic_rows")[1], records=file_rows[:25])
    write_report("PR168_RP5A_RowFieldSemanticHitIndex.report.json", summary={"row_field_semantic_hit_count": len(hit_rows)}, rows_ref=refs("row_field_semantic_hit_rows")[0], manifest_ref=refs("row_field_semantic_hit_rows")[1], records=hit_rows[:25])
    write_report("PR168_RP5A_WrongConceptTermIndex.report.json", summary={"wrong_concept_term_count": len(wrong_term_rows)}, rows_ref=refs("wrong_concept_term_rows")[0], manifest_ref=refs("wrong_concept_term_rows")[1], records=wrong_term_rows[:25])
    write_report("PR168_RP5A_ConsumerGraph.report.json", summary={"consumer_graph_row_count": len(consumer_rows), "active_consumer_file_count": summary_counts["active_consumer_file_count"]}, rows_ref=refs("consumer_graph_rows")[0], manifest_ref=refs("consumer_graph_rows")[1], records=consumer_rows[:25])
    write_report("PR168_RP5A_ValidationDependencyGraph.report.json", summary={"validation_dependency_row_count": len(validation_rows), "validation_dependent_file_count": summary_counts["validation_dependent_file_count"]}, rows_ref=refs("validation_dependency_rows")[0], manifest_ref=refs("validation_dependency_rows")[1], records=validation_rows[:25])
    write_report("PR168_RP5A_QKUFormulaIdentityDependency.report.json", summary={"qku_formula_identity_dependency_file_count": summary_counts["qku_formula_identity_dependency_file_count"]}, rows_ref=refs("qku_formula_identity_dependency_rows")[0], manifest_ref=refs("qku_formula_identity_dependency_rows")[1], records=identity_rows[:25])
    write_report("PR168_RP5A_IdentityCustodyGraph.report.json", summary={"identity_custody_row_count": len(custody_rows)}, rows_ref=refs("identity_custody_rows")[0], manifest_ref=refs("identity_custody_rows")[1], records=custody_rows[:25])
    write_report("PR168_RP5A_AgentCrosswalkTouchpoints.report.json", summary={**crosswalk_status, "agent_touchpoint_file_count": summary_counts["agent_touchpoint_file_count"]}, rows_ref=refs("agent_touchpoint_rows")[0], manifest_ref=refs("agent_touchpoint_rows")[1], records=agent_rows[:25])
    write_report("PR168_RP5A_NoOrphanAuditTouchpoints.report.json", summary={**crosswalk_status, "no_orphan_touchpoint_rows": len(agent_rows)}, rows_ref=refs("agent_touchpoint_rows")[0], manifest_ref=refs("agent_touchpoint_rows")[1], records=agent_rows[:25])
    write_report("PR168_RP5A_StaleSemanticBlastRadius.report.json", summary={"blast_radius_row_count": len(blast_rows)}, rows_ref=refs("blast_radius_rows")[0], manifest_ref=refs("blast_radius_rows")[1], records=blast_rows[:25])
    write_report("PR168_RP5A_ValidationTimeRisk.report.json", summary={"validation_time_risk_row_count": len(validation_time_rows)}, rows_ref=refs("validation_time_risk_rows")[0], manifest_ref=refs("validation_time_risk_rows")[1], records=validation_time_rows[:25])
    write_report("PR168_RP5A_DeleteEligibilityDraft.report.json", summary={key: summary_counts[key] for key in summary_counts if key.endswith("_count") and "delete" in key.lower() or key in {"rewrite_consumer_first_count", "unclear_do_not_delete_count"}}, rows_ref=refs("delete_eligibility_rows")[0], manifest_ref=refs("delete_eligibility_rows")[1], records=delete_rows[:25])
    write_report("PR168_RP5A_CrossGraphConsistency.report.json", summary={"consistency_failure_count": len([row for row in consistency_rows if not row["consistent_flag"]]), "consistent_flag": all(row["consistent_flag"] for row in consistency_rows)}, records=consistency_rows)
    write_report("PR168_RP5A_NoDeletionProof.report.json", summary=no_delete, records=no_delete)
    write_report("PR168_RP5A_FutureRP5BPlan.report.json", summary={"future_rp5b_plan_row_count": len(future_rows)}, rows_ref=refs("future_rp5b_plan_rows")[0], manifest_ref=refs("future_rp5b_plan_rows")[1], records=future_rows[:25])
    write_report("PR168_RP5A_PathAudit.report.json", summary={"path_audit_row_count": len(path_rows), "path_hard_fail_count": len([row for row in path_rows if row["path_status"] == "FAIL"]), "path_warning_count": len([row for row in path_rows if row["path_status"] == "WARN"])}, records=path_rows)
    write_report("PR168_RP5A_ScanPerformance.report.json", summary=performance_report, records=performance_report)
    write_report("PR168_RP5A_FinalSummary.report.json", summary=summary_counts, records=summary_counts)
    timer.mark("write_reports_and_shards", phase)
    _write_checkpoint("complete", files_scanned_count=len(files), matched_files_count=len(matched_files), total_elapsed_seconds=timer.total())
    _log_phase("write_reports_and_shards", files_processed=len(files), matched_files=len(matched_files), started_at=timer.started_at)

    print(
        json.dumps(
            {
                "built": True,
                "mode": "offline" if offline else "default",
                "report_version": REPORT_VERSION,
                "created_at_utc": CREATED_AT_UTC,
                "files_scanned_count": len(files),
                "files_with_stale_terms_count": len(file_rows),
                "row_field_semantic_hit_count": len(hit_rows),
                "delete_now_count": len([row for row in delete_rows if row.get("delete_now_flag")]),
                "reports_written": len(REPORT_NAMES),
            },
            sort_keys=True,
        )
    )
    return summary_counts


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--offline", action="store_true", help="Do not use public web or online docs; GitHub PR metadata may fall back to committed rows if unavailable.")
    parser.add_argument("--quick-selftest", action="store_true", help="Run a small bounded scan to prove report generation without exhaustive coverage.")
    parser.add_argument(
        "--validation-scope-evidence-only",
        action="store_true",
        help=(
            "Currentize only persisted RP5A validation-scope and "
            "FinalSummary evidence from committed detailed owners."
        ),
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    if args.validation_scope_evidence_only:
        currentize_validation_scope_evidence_only()
        return 0
    build_all(offline=bool(args.offline), quick_selftest=bool(args.quick_selftest))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
