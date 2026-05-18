#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
import pathlib
import subprocess
import sys
from typing import Any, Iterable, Mapping, Sequence

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from src.qtt.core.testing import qtt_active_non_sha_day1_gate_state_registry as gate_registry
from src.qtt.core.testing import qtt_final_readiness_dependency_policy as readiness_policy
from tools.validate_master_plan_section_coverage import validate_json_schema_subset


REPO_ROOT = _REPO_ROOT
DEFAULT_ROSTER = pathlib.Path("docs/roadmap/QTT_PR_Identity_Roster_v1_0.json")
DEFAULT_SCHEMA = pathlib.Path("schemas/roadmap/qtt_pr_identity_roster.schema.json")
DEFAULT_REPORT = pathlib.Path("docs/master_plan/generated/QttPrIdentityRoster.report.json")
ATOMICROWS_BUNDLE = pathlib.Path("docs/master_plan/atomic_rows/AtomicRows.bundle.jsonl")
ATOMICROWS_BUNDLE_SHA = pathlib.Path("docs/master_plan/atomic_rows/AtomicRows.bundle.sha256")
RUN_VALIDATION_GATES = pathlib.Path("tools/run_validation_gates.py")

SUCCESS_MARKER = "QTT_PR_IDENTITY_ROSTER_OK"
FAILURE_MARKER = "QTT_PR_IDENTITY_ROSTER_FAILED"
REPORT_ID = "QTT_PR_IDENTITY_ROSTER_REPORT"
VALIDATOR_NAME = "validate_qtt_pr_identity_roster.py"
ROSTER_ID = "QTT_PR_IDENTITY_ROSTER_V1_0"
ROSTER_SCHEMA_VERSION = "v1.0"
ROSTER_TITLE = "QTT PR Identity Roster v1.0"
ROSTER_AUTHORITY_CLASS = (
    "CONTROL_PLANE_IDENTITY_TRANSLATOR_NOT_PR_NUMBER_AUTHORITY_NOT_RUNTIME_AUTHORITY"
)
CREATED_BY_REPO_DELIVERY_LABEL = (
    "PR117 — Canonical PR identity roster and reconciliation framework"
)
SYSTEMS_DECLARED = ("repo", "roadmap", "blueprint", "github")
CANONICAL_PRIORITY_ORDER = (
    "REPO_CANONICAL_LABEL",
    "BLUEPRINT_DELIVERY_LABEL",
    "ROADMAP_DELIVERY_LABEL",
    "GITHUB_AUDIT_NUMBER",
)
REQUIRED_ENTRY_FIELDS = {
    "roster_entry_id",
    "repo_canonical_pr_label",
    "roadmap_pr_label",
    "blueprint_pr_label",
    "github_pr_number",
    "repo_title",
    "roadmap_title",
    "blueprint_title",
    "github_title",
    "branch_name",
    "validator_markers",
    "reference_types",
    "corrective_overlay",
    "repair_chain",
    "current_status",
    "semantic_role",
    "authority_scope",
    "superseded_by",
    "depends_on_roster_entries",
    "github_audit_url",
    "identity_relation_class",
    "same_number_mismatch_recorded",
    "notes",
}
REQUIRED_GLOBAL_INVARIANTS = {
    "repo_canonical_references_are_implementation_truth": True,
    "github_numbers_are_audit_only": True,
    "roadmap_labels_are_planning_orchestration_labels": True,
    "blueprint_labels_are_implementation_scope_labels": True,
    "same_number_identity_inference_forbidden": True,
    "history_rewrite_forbidden": True,
    "merged_branch_renaming_forbidden": True,
    "master_plan_edit_forbidden_this_pr": True,
    "active_non_sha_day1_gate_flip_forbidden": True,
    "final_readiness_creation_forbidden": True,
    "day1_launch_authority_creation_forbidden": True,
    "runtime_live_order_source_connector_runtime_cash_backend_profit_authority_creation_forbidden": True,
    "source_acceptance_forbidden": True,
    "connector_semantic_binding_forbidden": True,
    "replay_paper_optimizer_neural_quantum_backend_execution_forbidden": True,
    "qaoa_vqe_qubo_ising_annealing_execution_forbidden": True,
    "profit_latency_execution_quantum_advantage_claim_forbidden": True,
    "atomicrows_bundle_mutation_forbidden": True,
    "atomicrows_bundle_sha_creation_forbidden": True,
    "sha_dormancy_weakening_forbidden": True,
    "pr116a_gate_registry_weakening_forbidden": True,
}
REQUIRED_NO_CLAIM_BOUNDARY = {
    "no_active_non_sha_day1_gate_flipped": True,
    "final_readiness_created": False,
    "day1_launch_authority_created": False,
    "runtime_live_order_source_connector_runtime_cash_backend_profit_authority_created": False,
    "source_facts_accepted": False,
    "connector_semantics_bound": False,
    "runtime_cash_receipts_created": False,
    "replay_paper_optimizer_neural_quantum_backend_execution_created": False,
    "qubo_qaoa_vqe_ising_annealing_execution_created": False,
    "profit_latency_execution_quantum_advantage_evidence_created": False,
    "bug_free_status_claimed": False,
}
REQUIRED_GITHUB_AUDIT_NUMBERS = tuple(range(97, 118))
REQUIRED_ROADMAP_LABELS = tuple(f"PR #{number}" for number in range(97, 127))
REQUIRED_SAME_NUMBER_MISMATCHES = tuple(range(107, 117))
ROADMAP_RUNTIME_BLOCK_LABELS = tuple(f"PR #{number}" for number in range(105, 127))
REQUIRED_PR115A_NOTE_PARTS = (
    "SHA dormant/non-participating",
    "SHA is not Day-1 final readiness",
    "SHA dormancy is not a final-readiness blocker",
    "SHA absence is not a final-readiness blocker",
    "SHA presence is not final-readiness evidence",
    "No final readiness, no Day-1 launch authority",
    "no runtime/live/order/source/connector/runtime-cash/backend/profit authority created",
)
REQUIRED_PR116A_NOTE_PARTS = (
    "Active non-SHA Day-1 gate registry established",
    "Positive evidence gates remain blocked",
    "Guard/no-claim gates remain active and unviolated",
    "SHA_DORMANCY_SYSTEM excluded from active gate IDs",
    "QUANTUM_BACKEND_AUTHORITY_GATE is conditional",
    "No active non-SHA Day-1 gate was flipped",
    "No final readiness",
    "No Day-1 launch authority",
    "No runtime/live/order/profit authority",
)
REQUIRED_PR117_NOTE_PARTS = (
    "GitHub #117 is the audit number assigned",
    "repo-canonical PR117",
    "does not imply Roadmap PR #117",
    "Blueprint PR #117",
    "implementation-truth label",
)
REQUIRED_PR118_NOTE_PARTS = (
    "Repo PR118 is a repo-canonical control-plane state-controller PR",
    "does not imply Roadmap PR #118",
    "Blueprint PR #118",
    "GitHub PR #118",
    "github_pr_number remains null",
)


@dataclass(frozen=True)
class ValidationResult:
    ok: bool
    failures: tuple[str, ...]
    report: dict[str, Any] | None


def _resolve(repo_root: pathlib.Path, path: pathlib.Path) -> pathlib.Path:
    return path if path.is_absolute() else repo_root / path


def _load_json(path: pathlib.Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON root must be an object: {path}")
    return value


def _write_json_report(report: dict[str, Any], output: pathlib.Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _entries(roster: Mapping[str, Any]) -> list[dict[str, Any]]:
    return [entry for entry in roster.get("entries", []) if isinstance(entry, dict)]


def _entry_by_id(entries: Iterable[dict[str, Any]], entry_id: str) -> dict[str, Any] | None:
    for entry in entries:
        if entry.get("roster_entry_id") == entry_id:
            return entry
    return None


def _entries_with(entries: Iterable[dict[str, Any]], **criteria: Any) -> list[dict[str, Any]]:
    return [
        entry
        for entry in entries
        if all(entry.get(field) == expected for field, expected in criteria.items())
    ]


def _notes_contain(entry: Mapping[str, Any], required_parts: Sequence[str]) -> list[str]:
    notes = str(entry.get("notes", ""))
    return [part for part in required_parts if part not in notes]


def _git_path_status(repo_root: pathlib.Path, path: pathlib.Path) -> list[str]:
    commands = (
        ["git", "status", "--short", "--", path.as_posix()],
        ["git", "diff", "--name-only", "--", path.as_posix()],
        ["git", "diff", "--cached", "--name-only", "--", path.as_posix()],
    )
    output: list[str] = []
    for command in commands:
        completed = subprocess.run(
            command,
            cwd=repo_root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if completed.returncode != 0:
            output.append(f"{' '.join(command)} failed: {completed.stderr.strip()}")
        elif completed.stdout.strip():
            output.extend(completed.stdout.splitlines())
    return output


def _validate_top_level(roster: Mapping[str, Any]) -> list[str]:
    failures: list[str] = []
    expected = {
        "roster_schema_version": ROSTER_SCHEMA_VERSION,
        "roster_id": ROSTER_ID,
        "roster_title": ROSTER_TITLE,
        "roster_authority_class": ROSTER_AUTHORITY_CLASS,
        "created_by_repo_delivery_label": CREATED_BY_REPO_DELIVERY_LABEL,
        "generated_report_path": DEFAULT_REPORT.as_posix(),
    }
    for field, expected_value in expected.items():
        if roster.get(field) != expected_value:
            failures.append(f"roster.{field} must be {expected_value!r}")
    if tuple(roster.get("systems_declared", [])) != SYSTEMS_DECLARED:
        failures.append("systems_declared must be repo, roadmap, blueprint, github")
    if tuple(roster.get("canonical_priority_order", [])) != CANONICAL_PRIORITY_ORDER:
        failures.append("canonical_priority_order is not repo/blueprint/roadmap/github")

    invariants = roster.get("global_invariants")
    if not isinstance(invariants, dict):
        failures.append("global_invariants must be an object")
    else:
        for field, expected_value in REQUIRED_GLOBAL_INVARIANTS.items():
            if invariants.get(field) is not expected_value:
                failures.append(f"global_invariants.{field} must be {expected_value}")

    boundary = roster.get("no_claim_boundary")
    if not isinstance(boundary, dict):
        failures.append("no_claim_boundary must be an object")
    else:
        for field, expected_value in REQUIRED_NO_CLAIM_BOUNDARY.items():
            if boundary.get(field) is not expected_value:
                failures.append(f"no_claim_boundary.{field} must be {expected_value}")

    expectations = roster.get("validation_expectations")
    if not isinstance(expectations, dict):
        failures.append("validation_expectations must be an object")
    else:
        expected_expectations = {
            "validator_name": VALIDATOR_NAME,
            "success_marker": SUCCESS_MARKER,
            "validation_gate_sequence_inclusion_required": True,
            "atomicrows_bundle_jsonl_required_status": "UNCHANGED_FROM_BASELINE_STATE",
            "atomicrows_bundle_sha256_required_absent": True,
            "generated_report_path": DEFAULT_REPORT.as_posix(),
        }
        for field, expected_value in expected_expectations.items():
            if expectations.get(field) != expected_value:
                failures.append(f"validation_expectations.{field} must be {expected_value!r}")
    return failures


def _validate_entry_shape(entries: Sequence[dict[str, Any]]) -> list[str]:
    failures: list[str] = []
    seen: set[str] = set()
    for index, entry in enumerate(entries, start=1):
        label = f"entries[{index}]"
        missing = sorted(REQUIRED_ENTRY_FIELDS - set(entry))
        if missing:
            failures.append(f"{label} missing required fields: {', '.join(missing)}")
        entry_id = entry.get("roster_entry_id")
        if not isinstance(entry_id, str) or not entry_id:
            failures.append(f"{label}.roster_entry_id must be a non-empty string")
        elif entry_id in seen:
            failures.append(f"duplicate roster_entry_id: {entry_id}")
        else:
            seen.add(entry_id)
        if not isinstance(entry.get("validator_markers"), list):
            failures.append(f"{label}.validator_markers must be an array")
        if not isinstance(entry.get("reference_types"), list) or not entry.get("reference_types"):
            failures.append(f"{label}.reference_types must be a non-empty array")
        if not isinstance(entry.get("repair_chain"), list):
            failures.append(f"{label}.repair_chain must be an array")
        if not isinstance(entry.get("depends_on_roster_entries"), list):
            failures.append(f"{label}.depends_on_roster_entries must be an array")
    return failures


def _validate_seed_scope(roster: Mapping[str, Any], entries: Sequence[dict[str, Any]]) -> list[str]:
    failures: list[str] = []
    scope = roster.get("seed_scope")
    if not isinstance(scope, dict):
        return ["seed_scope must be an object"]
    if tuple(scope.get("github_pr_numbers_included", [])) != REQUIRED_GITHUB_AUDIT_NUMBERS:
        failures.append("seed_scope.github_pr_numbers_included must be GitHub PR #97 through #117")
    if tuple(scope.get("roadmap_pr_labels_included", [])) != REQUIRED_ROADMAP_LABELS:
        failures.append("seed_scope.roadmap_pr_labels_included must be roadmap PR #97 through #126")
    if tuple(scope.get("corrective_overlays_included", [])) != ("PR115A", "PR116A"):
        failures.append("seed_scope.corrective_overlays_included must contain PR115A and PR116A")
    if scope.get("self_entry_required") != "PR117":
        failures.append("seed_scope.self_entry_required must be PR117")

    github_numbers = {entry.get("github_pr_number") for entry in entries}
    for number in REQUIRED_GITHUB_AUDIT_NUMBERS:
        if number not in github_numbers:
            failures.append(f"missing GitHub PR #{number} roster entry")
    roadmap_labels = {entry.get("roadmap_pr_label") for entry in entries}
    for label in REQUIRED_ROADMAP_LABELS:
        if label not in roadmap_labels:
            failures.append(f"missing roadmap {label} roster entry")
    return failures


def _validate_corrective_overlays(entries: Sequence[dict[str, Any]]) -> list[str]:
    failures: list[str] = []
    pr115a = _entry_by_id(entries, "PR115A_CORRECTIVE_OVERLAY_GITHUB_115")
    pr116a = _entry_by_id(entries, "PR116A_CORRECTIVE_OVERLAY_GITHUB_116")
    if pr115a is None:
        failures.append("missing PR115A corrective overlay entry")
    else:
        expected = {
            "repo_canonical_pr_label": "PR115A",
            "github_pr_number": 115,
            "semantic_role": "CORRECTIVE_OVERLAY",
            "authority_scope": "CONTROL_PLANE_ONLY",
            "corrective_overlay": True,
        }
        for field, expected_value in expected.items():
            if pr115a.get(field) != expected_value:
                failures.append(f"PR115A.{field} must be {expected_value!r}")
        for reference in (
            "REPO_CANONICAL_LABEL",
            "GITHUB_AUDIT_NUMBER",
            "CORRECTIVE_CONTROL_PLANE_OVERLAY",
        ):
            if reference not in pr115a.get("reference_types", []):
                failures.append(f"PR115A reference_types must include {reference}")
        missing_notes = _notes_contain(pr115a, REQUIRED_PR115A_NOTE_PARTS)
        if missing_notes:
            failures.append(f"PR115A notes missing: {', '.join(missing_notes)}")

    if pr116a is None:
        failures.append("missing PR116A corrective overlay entry")
    else:
        expected = {
            "repo_canonical_pr_label": "PR116A",
            "github_pr_number": 116,
            "semantic_role": "CORRECTIVE_OVERLAY",
            "authority_scope": "CONTROL_PLANE_ONLY",
            "corrective_overlay": True,
        }
        for field, expected_value in expected.items():
            if pr116a.get(field) != expected_value:
                failures.append(f"PR116A.{field} must be {expected_value!r}")
        for reference in (
            "REPO_CANONICAL_LABEL",
            "GITHUB_AUDIT_NUMBER",
            "CORRECTIVE_CONTROL_PLANE_OVERLAY",
        ):
            if reference not in pr116a.get("reference_types", []):
                failures.append(f"PR116A reference_types must include {reference}")
        missing_notes = _notes_contain(pr116a, REQUIRED_PR116A_NOTE_PARTS)
        if missing_notes:
            failures.append(f"PR116A notes missing: {', '.join(missing_notes)}")

    if not _entries_with(entries, repo_canonical_pr_label="PR115A", github_pr_number=115):
        failures.append("GitHub PR #115 must map to PR115A overlay")
    if not _entries_with(entries, repo_canonical_pr_label="PR116A", github_pr_number=116):
        failures.append("GitHub PR #116 must map to PR116A overlay")
    return failures


def _validate_pr117_self_entry(entries: Sequence[dict[str, Any]]) -> list[str]:
    failures: list[str] = []
    pr117 = _entry_by_id(entries, "PR117_REPO_CANONICAL_SELF_ENTRY")
    if pr117 is None:
        return ["missing PR117 repo-canonical self-entry"]
    expected = {
        "repo_canonical_pr_label": "PR117",
        "roadmap_pr_label": None,
        "blueprint_pr_label": None,
        "github_pr_number": 117,
        "repo_title": "Canonical PR identity roster and reconciliation framework",
        "github_title": "PR117 add canonical PR identity roster",
        "semantic_role": "CONTROL_PLANE_RECONCILIATION",
        "authority_scope": "CONTROL_PLANE_ONLY",
        "current_status": "MERGED",
        "github_audit_url": "https://github.com/Q8Meow/QTT_New0526/pull/117",
        "same_number_mismatch_recorded": True,
    }
    for field, expected_value in expected.items():
        if pr117.get(field) != expected_value:
            failures.append(f"PR117 self-entry {field} must be {expected_value!r}")
    if pr117.get("identity_relation_class") not in {
        "REPO_CANONICAL_ONLY",
        "PENDING_OWNER_DECISION",
    }:
        failures.append("PR117 self-entry identity_relation_class must be repo-only or pending")
    missing_notes = _notes_contain(pr117, REQUIRED_PR117_NOTE_PARTS)
    if missing_notes:
        failures.append(f"PR117 self-entry notes missing: {', '.join(missing_notes)}")
    if "GITHUB_AUDIT_NUMBER" not in pr117.get("reference_types", []):
        failures.append("PR117 self-entry reference_types must include GITHUB_AUDIT_NUMBER")
    return failures


def _validate_pr118_self_entry(entries: Sequence[dict[str, Any]]) -> list[str]:
    failures: list[str] = []
    pr118 = _entry_by_id(entries, "PR118_REPO_CANONICAL_SELF_ENTRY")
    if pr118 is None:
        return ["missing PR118 repo-canonical self-entry"]
    expected = {
        "repo_canonical_pr_label": "PR118",
        "roadmap_pr_label": None,
        "blueprint_pr_label": None,
        "github_pr_number": None,
        "repo_title": "Roadmap execution-state controller and audit currentization",
        "roadmap_title": None,
        "blueprint_title": None,
        "github_title": None,
        "branch_name": "pr118-roadmap-execution-state-controller-audit-currentization",
        "semantic_role": "CONTROL_PLANE_RECONCILIATION",
        "authority_scope": "CONTROL_PLANE_ONLY",
        "current_status": "PLANNED",
        "github_audit_url": None,
        "identity_relation_class": "REPO_CANONICAL_ONLY",
        "same_number_mismatch_recorded": True,
    }
    for field, expected_value in expected.items():
        if pr118.get(field) != expected_value:
            failures.append(f"PR118 self-entry {field} must be {expected_value!r}")
    if "PR117_REPO_CANONICAL_SELF_ENTRY" not in pr118.get(
        "depends_on_roster_entries", []
    ):
        failures.append("PR118 self-entry must depend on PR117_REPO_CANONICAL_SELF_ENTRY")
    if "QTT_ROADMAP_EXECUTION_STATE_CONTROLLER_OK" not in pr118.get(
        "validator_markers", []
    ):
        failures.append("PR118 self-entry must reference QTT_ROADMAP_EXECUTION_STATE_CONTROLLER_OK")
    missing_notes = _notes_contain(pr118, REQUIRED_PR118_NOTE_PARTS)
    if missing_notes:
        failures.append(f"PR118 self-entry notes missing: {', '.join(missing_notes)}")
    return failures


def _validate_mismatches(roster: Mapping[str, Any], entries: Sequence[dict[str, Any]]) -> list[str]:
    failures: list[str] = []
    summary = roster.get("mismatch_summary")
    if not isinstance(summary, dict):
        return ["mismatch_summary must be an object"]
    mismatch_records = summary.get("github_107_through_116_same_number_mismatches")
    if not isinstance(mismatch_records, list):
        return ["mismatch_summary.github_107_through_116_same_number_mismatches must be an array"]
    mismatch_numbers = {
        record.get("github_pr_number")
        for record in mismatch_records
        if isinstance(record, dict)
    }
    for number in REQUIRED_SAME_NUMBER_MISMATCHES:
        if number not in mismatch_numbers:
            failures.append(f"missing same-number mismatch record for GitHub #{number}")
        matching_entries = [
            entry
            for entry in entries
            if entry.get("github_pr_number") == number
            and entry.get("roadmap_pr_label") == f"PR #{number}"
            and entry.get("same_number_mismatch_recorded") is True
        ]
        if not matching_entries:
            failures.append(f"entry-level same-number mismatch missing for GitHub #{number}")

    if 117 not in mismatch_numbers:
        failures.append("missing same-number mismatch record for GitHub #117")
    pr117_self = _entry_by_id(entries, "PR117_REPO_CANONICAL_SELF_ENTRY")
    if pr117_self is not None:
        if pr117_self.get("roadmap_pr_label") is not None:
            failures.append("repo-canonical PR117 must not take roadmap PR #117 label")
        if pr117_self.get("blueprint_pr_label") is not None:
            failures.append("repo-canonical PR117 must not take blueprint PR #117 label")
        if pr117_self.get("identity_relation_class") == "EXACT_SAME_SYSTEM_REFERENCE":
            failures.append("repo-canonical PR117 must not be treated as roadmap PR #117")

    pr116_entries = _entries_with(entries, github_pr_number=116, roadmap_pr_label="PR #116")
    if not pr116_entries:
        failures.append("GitHub #116 vs roadmap PR #116 mismatch must be recorded")
    for entry in pr116_entries:
        if entry.get("roadmap_title") == entry.get("github_title"):
            failures.append("GitHub #116 must not have the roadmap PR #116 title")
        if entry.get("same_number_mismatch_recorded") is not True:
            failures.append("GitHub #116 same-number mismatch flag must be true")
        if entry.get("identity_relation_class") == "EXACT_SAME_SYSTEM_REFERENCE":
            failures.append("GitHub #116 must not be treated as roadmap PR #116")

    pr100 = _entry_by_id(entries, "ROADMAP_PR_100_GITHUB_102_SHA_FREEZE_MISMATCH")
    if pr100 is None:
        failures.append("missing roadmap PR #100 / GitHub #102 SHA/freeze mismatch entry")
    else:
        if pr100.get("roadmap_pr_label") != "PR #100" or pr100.get("github_pr_number") != 102:
            failures.append("roadmap PR #100 must record GitHub #102 as audit-only")
        if "GitHub #102 is not roadmap PR #102" not in str(pr100.get("notes", "")):
            failures.append("roadmap PR #100 / GitHub #102 mismatch notes must forbid PR #102 inference")
    if summary.get("roadmap_pr100_github102_sha_freeze_mismatch_confirmed") is not True:
        failures.append("roadmap PR #100 / GitHub #102 mismatch summary must be confirmed")

    if summary.get("roadmap_pr105_to_pr126_runtime_live_block_confirmed") is not True:
        failures.append("roadmap PR #105-#126 runtime/live block summary must be confirmed")
    for label in ROADMAP_RUNTIME_BLOCK_LABELS:
        number = int(label.split("#", 1)[1])
        planned_entry = _entry_by_id(entries, f"ROADMAP_PR_{number:03d}_PLANNED")
        if planned_entry is None:
            failures.append(f"missing planned roadmap runtime/live block entry for {label}")
            continue
        if planned_entry.get("github_pr_number") is not None:
            failures.append(f"{label} planned entry must not assume a GitHub audit number")
        if planned_entry.get("current_status") != "PLANNED":
            failures.append(f"{label} planned entry must remain PLANNED")
    return failures


def _validate_gate_and_authority_boundaries(repo_root: pathlib.Path, roster: Mapping[str, Any]) -> list[str]:
    failures: list[str] = []
    for assertion in (
        gate_registry.assert_registry_current,
        gate_registry.assert_no_gate_flipped_by_this_pr,
        gate_registry.assert_no_gate_satisfied_by_this_pr,
        gate_registry.assert_all_positive_evidence_gates_remain_blocked,
        gate_registry.assert_guard_gates_active_and_unviolated,
        gate_registry.assert_sha_dormancy_system_excluded,
        gate_registry.assert_quantum_backend_gate_does_not_require_backend_for_non_backend_day1,
        gate_registry.assert_current_pr_creates_no_final_readiness,
        gate_registry.assert_current_pr_creates_no_runtime_live_profit_or_backend_authority,
        gate_registry.assert_current_pr_creates_no_replay_paper_optimizer_neural_quantum_execution,
        gate_registry.assert_current_pr_creates_no_profit_latency_execution_quantum_advantage_evidence,
        readiness_policy.assert_current_pr_does_not_create_final_readiness,
        readiness_policy.assert_day1_final_readiness_must_ignore_sha_dormancy_when_non_sha_gates_pass,
    ):
        try:
            assertion()
        except AssertionError as exc:
            failures.append(str(exc))

    bundle_path = _resolve(repo_root, ATOMICROWS_BUNDLE)
    sha_path = _resolve(repo_root, ATOMICROWS_BUNDLE_SHA)
    if not bundle_path.exists():
        failures.append("AtomicRows.bundle.jsonl baseline path must exist for unchanged-state verification")
    if sha_path.exists():
        failures.append("AtomicRows.bundle.sha256 must remain absent")
    for path in (ATOMICROWS_BUNDLE, ATOMICROWS_BUNDLE_SHA):
        status_lines = _git_path_status(repo_root, path)
        if status_lines:
            failures.append(f"{path.as_posix()} must not be added or modified: {status_lines}")

    gate_text = _resolve(repo_root, RUN_VALIDATION_GATES).read_text(encoding="utf-8")
    if VALIDATOR_NAME not in gate_text:
        failures.append("tools/run_validation_gates.py must include validate_qtt_pr_identity_roster.py")

    boundary = roster.get("no_claim_boundary", {})
    if isinstance(boundary, dict):
        if boundary.get("runtime_live_order_source_connector_runtime_cash_backend_profit_authority_created") is not False:
            failures.append("runtime/live/order/source/connector/runtime-cash/backend/profit authority must remain blocked")
        if boundary.get("replay_paper_optimizer_neural_quantum_backend_execution_created") is not False:
            failures.append("replay/paper/optimizer/neural/quantum backend execution must remain blocked")
        if boundary.get("qubo_qaoa_vqe_ising_annealing_execution_created") is not False:
            failures.append("QUBO/QAOA/VQE/Ising/annealing execution must remain blocked")
        if boundary.get("profit_latency_execution_quantum_advantage_evidence_created") is not False:
            failures.append("profit/latency/execution/quantum-advantage evidence must remain absent")
    return failures


def _build_report(roster: Mapping[str, Any], entries: Sequence[dict[str, Any]], failures: Sequence[str]) -> dict[str, Any]:
    result_ok = not failures
    return {
        "report_id": REPORT_ID,
        "roster_id": roster.get("roster_id"),
        "validator_name": VALIDATOR_NAME,
        "validation_status": "PASS" if result_ok else "FAIL",
        "entry_count": len(entries),
        "systems_declared": list(roster.get("systems_declared", [])),
        "canonical_priority_order": list(roster.get("canonical_priority_order", [])),
        "github_audit_numbers_are_audit_only": bool(
            roster.get("global_invariants", {}).get("github_numbers_are_audit_only")
        ),
        "repo_canonical_labels_are_implementation_truth": bool(
            roster.get("global_invariants", {}).get(
                "repo_canonical_references_are_implementation_truth"
            )
        ),
        "roadmap_labels_are_planning_orchestration_labels": bool(
            roster.get("global_invariants", {}).get(
                "roadmap_labels_are_planning_orchestration_labels"
            )
        ),
        "blueprint_labels_are_implementation_scope_labels": bool(
            roster.get("global_invariants", {}).get(
                "blueprint_labels_are_implementation_scope_labels"
            )
        ),
        "same_number_identity_inference_forbidden": bool(
            roster.get("global_invariants", {}).get(
                "same_number_identity_inference_forbidden"
            )
        ),
        "pr115a_overlay_present": _entry_by_id(
            entries, "PR115A_CORRECTIVE_OVERLAY_GITHUB_115"
        )
        is not None,
        "pr116a_overlay_present": _entry_by_id(
            entries, "PR116A_CORRECTIVE_OVERLAY_GITHUB_116"
        )
        is not None,
        "pr117_self_entry_present": _entry_by_id(
            entries, "PR117_REPO_CANONICAL_SELF_ENTRY"
        )
        is not None,
        "pr117_github_audit_number": (
            _entry_by_id(entries, "PR117_REPO_CANONICAL_SELF_ENTRY") or {}
        ).get("github_pr_number"),
        "pr117_github_audit_url": (
            _entry_by_id(entries, "PR117_REPO_CANONICAL_SELF_ENTRY") or {}
        ).get("github_audit_url"),
        "github_116_is_not_roadmap_pr_116": True,
        "pr117_assumed_github_117": False,
        "pr117_assumed_roadmap_pr_117": False,
        "pr117_assumed_blueprint_pr_117": False,
        "pr118_self_entry_present": _entry_by_id(
            entries, "PR118_REPO_CANONICAL_SELF_ENTRY"
        )
        is not None,
        "pr118_assumed_github_118": False,
        "pr118_assumed_roadmap_pr_118": False,
        "pr118_assumed_blueprint_pr_118": False,
        "no_active_non_sha_day1_gate_flipped": not gate_registry.CURRENT_PR_FLIPS_ANY_GATE,
        "final_readiness_created": gate_registry.CURRENT_PR_CREATES_FINAL_READINESS,
        "day1_launch_authority_created": gate_registry.CURRENT_PR_CREATES_DAY1_LAUNCH_AUTHORITY,
        "atomicrows_bundle_path": ATOMICROWS_BUNDLE.as_posix(),
        "atomicrows_bundle_required_status": "UNCHANGED_FROM_BASELINE_STATE",
        "atomicrows_bundle_sha256_path": ATOMICROWS_BUNDLE_SHA.as_posix(),
        "atomicrows_bundle_sha256_exists": _resolve(REPO_ROOT, ATOMICROWS_BUNDLE_SHA).exists(),
        "runtime_live_order_source_connector_runtime_cash_backend_profit_authority_created": gate_registry.CURRENT_PR_CREATES_RUNTIME_LIVE_ORDER_SOURCE_CONNECTOR_RUNTIME_CASH_BACKEND_PROFIT_AUTHORITY,
        "replay_paper_optimizer_neural_quantum_backend_execution_created": gate_registry.CURRENT_PR_CREATES_REPLAY_PAPER_OPTIMIZER_NEURAL_QUANTUM_BACKEND_EXECUTION,
        "qubo_qaoa_vqe_ising_annealing_backend_simulator_execution_created_by_this_pr": gate_registry.CURRENT_PR_EXECUTES_QUBO_QAOA_VQE_ISING_ANNEALING_BACKEND_SIMULATOR,
        "profit_latency_execution_quantum_advantage_evidence_claimed": gate_registry.CURRENT_PR_CLAIMS_PROFIT_LATENCY_EXECUTION_QUANTUM_ADVANTAGE_EVIDENCE,
        "bug_free_status_claimed": False,
        "validation_errors": list(failures),
        "result_marker": SUCCESS_MARKER if result_ok else FAILURE_MARKER,
    }


def validate(
    *,
    repo_root: pathlib.Path = REPO_ROOT,
    roster_path: pathlib.Path = DEFAULT_ROSTER,
    schema_path: pathlib.Path = DEFAULT_SCHEMA,
    report_out: pathlib.Path = DEFAULT_REPORT,
) -> ValidationResult:
    repo_root = repo_root.resolve()
    failures: list[str] = []
    try:
        roster = _load_json(_resolve(repo_root, roster_path))
        schema = _load_json(_resolve(repo_root, schema_path))
    except Exception as exc:
        return ValidationResult(False, (f"could not load PR identity roster inputs: {exc}",), None)

    failures.extend(
        f"ROSTER_SCHEMA {failure}"
        for failure in validate_json_schema_subset(roster, schema)
    )
    entries = _entries(roster)
    failures.extend(_validate_top_level(roster))
    failures.extend(_validate_entry_shape(entries))
    failures.extend(_validate_seed_scope(roster, entries))
    failures.extend(_validate_corrective_overlays(entries))
    failures.extend(_validate_pr117_self_entry(entries))
    failures.extend(_validate_pr118_self_entry(entries))
    failures.extend(_validate_mismatches(roster, entries))
    failures.extend(_validate_gate_and_authority_boundaries(repo_root, roster))

    report = _build_report(roster, entries, failures)
    if failures:
        return ValidationResult(False, tuple(failures), report)
    if report != json.loads(json.dumps(report, sort_keys=True)):
        return ValidationResult(False, ("report serialization must be deterministic",), report)
    _write_json_report(report, _resolve(repo_root, report_out))
    return ValidationResult(True, tuple(), report)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=pathlib.Path, default=REPO_ROOT)
    parser.add_argument("--roster", type=pathlib.Path, default=DEFAULT_ROSTER)
    parser.add_argument("--schema", type=pathlib.Path, default=DEFAULT_SCHEMA)
    parser.add_argument("--report-out", type=pathlib.Path, default=DEFAULT_REPORT)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    result = validate(
        repo_root=args.repo_root,
        roster_path=args.roster,
        schema_path=args.schema,
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
