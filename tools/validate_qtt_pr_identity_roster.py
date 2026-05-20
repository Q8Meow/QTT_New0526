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
REQUIRED_GITHUB_AUDIT_NUMBERS = tuple(range(97, 127))
REQUIRED_ROADMAP_LABELS = tuple(f"PR #{number}" for number in range(97, 127))
REQUIRED_SAME_NUMBER_MISMATCHES = tuple(range(107, 127))
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
    "GitHub #118 is the audit number assigned",
    "repo-canonical PR118",
    "does not imply Roadmap PR #118",
    "Blueprint PR #118",
    "implementation-truth label",
)
REQUIRED_PR119_NOTE_PARTS = (
    "GitHub #119 is the audit number assigned",
    "repo-canonical PR119",
    "does not imply Roadmap PR #119",
    "Blueprint PR #119",
    "implementation-truth label",
)
REQUIRED_PR120_NOTE_PARTS = (
    "GitHub #120 is the audit number assigned",
    "repo-canonical PR120",
    "does not imply Roadmap PR #120",
    "Blueprint PR #120",
    "implementation-truth label",
)
REQUIRED_PR121_NOTE_PARTS = (
    "GitHub #121 is the audit number assigned",
    "repo-canonical PR121",
    "does not imply Roadmap PR #121",
    "Blueprint PR #121",
    "implementation-truth label",
)
REQUIRED_PR122_NOTE_PARTS = (
    "GitHub #122 is the audit number assigned",
    "repo-canonical PR122",
    "does not imply Roadmap PR #122",
    "Blueprint PR #122",
    "Repo PR123 does not imply Roadmap PR #123",
    "owner explicitly authorized Roadmap PR106 for Repo PR123",
    "state evidence records, not veto authority",
)
REQUIRED_PR123_NOTE_PARTS = (
    "GitHub #123 is the audit number assigned",
    "repo-canonical PR123",
    "does not imply Roadmap PR #123",
    "Blueprint PR #123",
    "Repo PR124 does not imply Roadmap PR #124",
    "owner explicitly authorized ACCEPTED_SOURCE_TO_CONNECTOR_SEMANTIC_BINDING_CONSUMER_GATE",
    "state evidence records, not veto authority",
)
REQUIRED_PR124_NOTE_PARTS = (
    "GitHub #124 is the audit number assigned",
    "repo-canonical PR124",
    "does not imply Roadmap PR #124",
    "Blueprint PR #124",
    "Repo PR125 does not imply Roadmap PR #125",
    "owner explicitly authorized Roadmap PR107 for Repo PR125",
    "state evidence records, not veto authority",
)
REQUIRED_PR125_NOTE_PARTS = (
    "Repo-canonical PR125",
    "source revalidation, supersession, and materiality scheduler",
    "Repo PR125 does not imply Roadmap PR #125",
    "owner explicitly authorized Roadmap PR107 for Repo PR125",
    "state evidence records, not veto authority",
)
REQUIRED_PR126_NOTE_PARTS = (
    "repo-canonical PR126",
    "connector semantic binding implementation gate",
    "Repo PR126 does not imply Roadmap PR #126",
    "owner explicitly authorized Roadmap PR108 for Repo PR126",
    "state evidence records, not veto authority",
)
REQUIRED_PR127_NOTE_PARTS = (
    "repo-canonical PR127",
    "per-venue execution lifecycle model builder",
    "Repo PR127 does not imply Roadmap PR #127",
    "owner explicitly authorized Roadmap PR109 for Repo PR127",
    "state evidence records, not veto authority",
    "Repo PR128 does not imply Roadmap PR #128",
    "owner explicitly authorized Roadmap PR110 for Repo PR128",
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
        failures.append("seed_scope.github_pr_numbers_included must be GitHub PR #97 through #126")
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
            "github_pr_number": 118,
        "repo_title": "Roadmap execution-state controller and audit currentization",
        "roadmap_title": None,
        "blueprint_title": None,
            "github_title": "PR118 add roadmap execution-state controller",
        "branch_name": "pr118-roadmap-execution-state-controller-audit-currentization",
        "semantic_role": "CONTROL_PLANE_RECONCILIATION",
        "authority_scope": "CONTROL_PLANE_ONLY",
            "current_status": "MERGED",
            "github_audit_url": "https://github.com/Q8Meow/QTT_New0526/pull/118",
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


def _validate_pr119_self_entry(entries: Sequence[dict[str, Any]]) -> list[str]:
    failures: list[str] = []
    pr119 = _entry_by_id(entries, "PR119_REPO_CANONICAL_SELF_ENTRY")
    if pr119 is None:
        return ["missing PR119 repo-canonical self-entry"]
    expected = {
        "repo_canonical_pr_label": "PR119",
        "roadmap_pr_label": None,
        "blueprint_pr_label": None,
        "github_pr_number": 119,
        "repo_title": "Currentize identity roster and add controller-approved coverage triage routes",
        "roadmap_title": None,
        "blueprint_title": None,
        "github_title": "PR119 currentize identity roster and add controller-approved coverage triage routes",
        "branch_name": "pr119-identity-roster-currentization-and-coverage-triage-routes",
        "semantic_role": "CONTROL_PLANE_RECONCILIATION",
        "authority_scope": "CONTROL_PLANE_ONLY",
        "current_status": "MERGED",
        "github_audit_url": "https://github.com/Q8Meow/QTT_New0526/pull/119",
        "identity_relation_class": "REPO_CANONICAL_ONLY",
        "same_number_mismatch_recorded": True,
    }
    for field, expected_value in expected.items():
        if pr119.get(field) != expected_value:
            failures.append(f"PR119 self-entry {field} must be {expected_value!r}")
    if "PR118_REPO_CANONICAL_SELF_ENTRY" not in pr119.get(
        "depends_on_roster_entries", []
    ):
        failures.append("PR119 self-entry must depend on PR118_REPO_CANONICAL_SELF_ENTRY")
    for marker in (
        "QTT_PR_IDENTITY_ROSTER_OK",
        "QTT_MASTER_PLAN_SECTION_COVERAGE_TRIAGE_ROUTES_OK",
    ):
        if marker not in pr119.get("validator_markers", []):
            failures.append(f"PR119 self-entry must reference {marker}")
    if "GITHUB_AUDIT_NUMBER" not in pr119.get("reference_types", []):
        failures.append("PR119 self-entry reference_types must include GITHUB_AUDIT_NUMBER")
    missing_notes = _notes_contain(pr119, REQUIRED_PR119_NOTE_PARTS)
    if missing_notes:
        failures.append(f"PR119 self-entry notes missing: {', '.join(missing_notes)}")
    return failures


def _validate_pr120_self_entry(entries: Sequence[dict[str, Any]]) -> list[str]:
    failures: list[str] = []
    pr120 = _entry_by_id(entries, "PR120_REPO_CANONICAL_SELF_ENTRY")
    if pr120 is None:
        return ["missing PR120 repo-canonical self-entry"]
    expected = {
        "repo_canonical_pr_label": "PR120",
        "roadmap_pr_label": None,
        "blueprint_pr_label": None,
        "github_pr_number": 120,
        "repo_title": "Add master-plan roadmap crosswalk and market section indexes",
        "roadmap_title": None,
        "blueprint_title": None,
        "github_title": "PR120 add master-plan roadmap crosswalk and market section indexes",
        "branch_name": "pr120-master-plan-roadmap-crosswalk-market-indexes",
        "semantic_role": "CONTROL_PLANE_RECONCILIATION",
        "authority_scope": "CONTROL_PLANE_ONLY",
        "current_status": "MERGED",
        "github_audit_url": "https://github.com/Q8Meow/QTT_New0526/pull/120",
        "identity_relation_class": "REPO_CANONICAL_ONLY",
        "same_number_mismatch_recorded": True,
    }
    for field, expected_value in expected.items():
        if pr120.get(field) != expected_value:
            failures.append(f"PR120 self-entry {field} must be {expected_value!r}")
    if "PR119_REPO_CANONICAL_SELF_ENTRY" not in pr120.get(
        "depends_on_roster_entries", []
    ):
        failures.append("PR120 self-entry must depend on PR119_REPO_CANONICAL_SELF_ENTRY")
    for marker in (
        "QTT_PR_IDENTITY_ROSTER_OK",
        "MASTER_PLAN_SECTION_COVERAGE_VALIDATION_OK",
        "QTT_MASTER_PLAN_SECTION_ROADMAP_CROSSWALK_OK",
    ):
        if marker not in pr120.get("validator_markers", []):
            failures.append(f"PR120 self-entry must reference {marker}")
    if "GITHUB_AUDIT_NUMBER" not in pr120.get("reference_types", []):
        failures.append("PR120 self-entry reference_types must include GITHUB_AUDIT_NUMBER")
    missing_notes = _notes_contain(pr120, REQUIRED_PR120_NOTE_PARTS)
    if missing_notes:
        failures.append(f"PR120 self-entry notes missing: {', '.join(missing_notes)}")
    return failures


def _validate_pr121_self_entry(entries: Sequence[dict[str, Any]]) -> list[str]:
    failures: list[str] = []
    pr121 = _entry_by_id(entries, "PR121_REPO_CANONICAL_SELF_ENTRY")
    if pr121 is None:
        return ["missing PR121 repo-canonical self-entry"]
    expected = {
        "repo_canonical_pr_label": "PR121",
        "roadmap_pr_label": None,
        "blueprint_pr_label": None,
        "github_pr_number": 121,
        "repo_title": "Add master-plan section coverage command matrix",
        "roadmap_title": None,
        "blueprint_title": None,
        "github_title": "PR121 add master-plan section coverage command matrix",
        "branch_name": "pr121-master-plan-section-coverage-command-matrix",
        "semantic_role": "CONTROL_PLANE_RECONCILIATION",
        "authority_scope": "CONTROL_PLANE_ONLY",
        "current_status": "MERGED",
        "github_audit_url": "https://github.com/Q8Meow/QTT_New0526/pull/121",
        "identity_relation_class": "REPO_CANONICAL_ONLY",
        "same_number_mismatch_recorded": True,
    }
    for field, expected_value in expected.items():
        if pr121.get(field) != expected_value:
            failures.append(f"PR121 self-entry {field} must be {expected_value!r}")
    if "PR120_REPO_CANONICAL_SELF_ENTRY" not in pr121.get(
        "depends_on_roster_entries", []
    ):
        failures.append("PR121 self-entry must depend on PR120_REPO_CANONICAL_SELF_ENTRY")
    for marker in (
        "QTT_PR_IDENTITY_ROSTER_OK",
        "MASTER_PLAN_SECTION_COVERAGE_VALIDATION_OK",
        "QTT_MASTER_PLAN_SECTION_COVERAGE_COMMAND_MATRIX_OK",
    ):
        if marker not in pr121.get("validator_markers", []):
            failures.append(f"PR121 self-entry must reference {marker}")
    if "GITHUB_AUDIT_NUMBER" not in pr121.get("reference_types", []):
        failures.append("PR121 self-entry reference_types must include GITHUB_AUDIT_NUMBER")
    missing_notes = _notes_contain(pr121, REQUIRED_PR121_NOTE_PARTS)
    if missing_notes:
        failures.append(f"PR121 self-entry notes missing: {', '.join(missing_notes)}")
    return failures


def _validate_pr122_self_entry(entries: Sequence[dict[str, Any]]) -> list[str]:
    failures: list[str] = []
    pr122 = _entry_by_id(entries, "PR122_REPO_CANONICAL_SELF_ENTRY")
    if pr122 is None:
        return ["missing PR122 repo-canonical self-entry"]
    expected = {
        "repo_canonical_pr_label": "PR122",
        "roadmap_pr_label": None,
        "blueprint_pr_label": None,
        "github_pr_number": 122,
        "repo_title": "Source-evidence retrieval controller gate",
        "roadmap_title": None,
        "blueprint_title": None,
        "github_title": "PR122 add source-evidence retrieval controller gate",
        "branch_name": "pr122-source-evidence-retrieval-controller-gated",
        "semantic_role": "CONTROL_PLANE_RECONCILIATION",
        "authority_scope": "CONTROL_PLANE_ONLY",
        "current_status": "MERGED",
        "github_audit_url": "https://github.com/Q8Meow/QTT_New0526/pull/122",
        "identity_relation_class": "REPO_CANONICAL_ONLY",
        "same_number_mismatch_recorded": True,
    }
    for field, expected_value in expected.items():
        if pr122.get(field) != expected_value:
            failures.append(f"PR122 self-entry {field} must be {expected_value!r}")
    if "PR121_REPO_CANONICAL_SELF_ENTRY" not in pr122.get(
        "depends_on_roster_entries", []
    ):
        failures.append("PR122 self-entry must depend on PR121_REPO_CANONICAL_SELF_ENTRY")
    for marker in (
        "QTT_PR_IDENTITY_ROSTER_OK",
        "QTT_SOURCE_EVIDENCE_RETRIEVAL_CONTROLLER_GATE_OK",
    ):
        if marker not in pr122.get("validator_markers", []):
            failures.append(f"PR122 self-entry must reference {marker}")
    if "GITHUB_AUDIT_NUMBER" not in pr122.get("reference_types", []):
        failures.append("PR122 self-entry reference_types must include GITHUB_AUDIT_NUMBER")
    missing_notes = _notes_contain(pr122, REQUIRED_PR122_NOTE_PARTS)
    if missing_notes:
        failures.append(f"PR122 self-entry notes missing: {', '.join(missing_notes)}")
    return failures


def _validate_pr123_self_entry(entries: Sequence[dict[str, Any]]) -> list[str]:
    failures: list[str] = []
    pr123 = _entry_by_id(entries, "PR123_REPO_CANONICAL_SELF_ENTRY")
    if pr123 is None:
        return ["missing PR123 repo-canonical self-entry"]
    expected = {
        "repo_canonical_pr_label": "PR123",
        "roadmap_pr_label": None,
        "blueprint_pr_label": None,
        "github_pr_number": 123,
        "repo_title": "Accepted source-evidence acceptance executor ledger",
        "roadmap_title": None,
        "blueprint_title": None,
        "github_title": "PR123 implement accepted source-evidence acceptance executor ledger",
        "branch_name": "pr123-accepted-source-evidence-acceptance-executor-ledger",
        "semantic_role": "CONTROL_PLANE_RECONCILIATION",
        "authority_scope": "CONTROL_PLANE_ONLY",
        "current_status": "MERGED",
        "github_audit_url": "https://github.com/Q8Meow/QTT_New0526/pull/123",
        "identity_relation_class": "REPO_CANONICAL_ONLY",
        "same_number_mismatch_recorded": True,
    }
    for field, expected_value in expected.items():
        if pr123.get(field) != expected_value:
            failures.append(f"PR123 self-entry {field} must be {expected_value!r}")
    if "PR122_REPO_CANONICAL_SELF_ENTRY" not in pr123.get(
        "depends_on_roster_entries", []
    ):
        failures.append("PR123 self-entry must depend on PR122_REPO_CANONICAL_SELF_ENTRY")
    for marker in (
        "QTT_PR_IDENTITY_ROSTER_OK",
        "QTT_SOURCE_EVIDENCE_ACCEPTANCE_EXECUTOR_OK",
        "QTT_ACCEPTED_SOURCE_EVIDENCE_ACCEPTANCE_EXECUTOR_AND_LEDGER_OK",
    ):
        if marker not in pr123.get("validator_markers", []):
            failures.append(f"PR123 self-entry must reference {marker}")
    if "GITHUB_AUDIT_NUMBER" not in pr123.get("reference_types", []):
        failures.append("PR123 self-entry reference_types must include GITHUB_AUDIT_NUMBER")
    missing_notes = _notes_contain(pr123, REQUIRED_PR123_NOTE_PARTS)
    if missing_notes:
        failures.append(f"PR123 self-entry notes missing: {', '.join(missing_notes)}")
    return failures


def _validate_pr124_self_entry(entries: Sequence[dict[str, Any]]) -> list[str]:
    failures: list[str] = []
    pr124 = _entry_by_id(entries, "PR124_REPO_CANONICAL_SELF_ENTRY")
    if pr124 is None:
        return ["missing PR124 repo-canonical self-entry"]
    expected = {
        "repo_canonical_pr_label": "PR124",
        "roadmap_pr_label": None,
        "blueprint_pr_label": None,
        "github_pr_number": 124,
        "repo_title": "Accepted-source connector semantic binding consumer gate",
        "roadmap_title": None,
        "blueprint_title": None,
        "github_title": "PR124 implement accepted-source connector semantic binding consumer gate",
        "branch_name": "pr124-accepted-source-to-connector-semantic-binding-consumer-gate",
        "semantic_role": "CONTROL_PLANE_RECONCILIATION",
        "authority_scope": "CONTROL_PLANE_ONLY",
        "current_status": "MERGED",
        "github_audit_url": "https://github.com/Q8Meow/QTT_New0526/pull/124",
        "identity_relation_class": "REPO_CANONICAL_ONLY",
        "same_number_mismatch_recorded": True,
        "github_pr_state": "MERGED",
        "github_pr_mergedAt": "2026-05-19T09:57:48Z",
        "github_pr_mergeCommit_oid": "bc77112be515414837a46fba81abded63c956373",
        "github_headRefName": "pr124-accepted-source-to-connector-semantic-binding-consumer-gate",
        "github_baseRefName": "main",
        "owner_authorized_next_capability": "ACCEPTED_SOURCE_TO_CONNECTOR_SEMANTIC_BINDING_CONSUMER_GATE",
    }
    for field, expected_value in expected.items():
        if pr124.get(field) != expected_value:
            failures.append(f"PR124 self-entry {field} must be {expected_value!r}")
    if "PR123_REPO_CANONICAL_SELF_ENTRY" not in pr124.get(
        "depends_on_roster_entries", []
    ):
        failures.append("PR124 self-entry must depend on PR123_REPO_CANONICAL_SELF_ENTRY")
    for marker in (
        "QTT_PR_IDENTITY_ROSTER_OK",
        "QTT_ACCEPTED_SOURCE_TO_CONNECTOR_SEMANTIC_BINDING_CONSUMER_GATE_OK",
    ):
        if marker not in pr124.get("validator_markers", []):
            failures.append(f"PR124 self-entry must reference {marker}")
    if "GITHUB_AUDIT_NUMBER" not in pr124.get("reference_types", []):
        failures.append("PR124 self-entry reference_types must include GITHUB_AUDIT_NUMBER")
    missing_notes = _notes_contain(pr124, REQUIRED_PR124_NOTE_PARTS)
    if missing_notes:
        failures.append(f"PR124 self-entry notes missing: {', '.join(missing_notes)}")
    return failures


def _validate_pr125_self_entry(entries: Sequence[dict[str, Any]]) -> list[str]:
    failures: list[str] = []
    pr125 = _entry_by_id(entries, "PR125_REPO_CANONICAL_SELF_ENTRY")
    if pr125 is None:
        return ["missing PR125 repo-canonical self-entry"]
    expected = {
        "repo_canonical_pr_label": "PR125",
        "roadmap_pr_label": None,
        "blueprint_pr_label": None,
        "github_pr_number": 125,
        "repo_title": "Source revalidation, supersession, and materiality scheduler",
        "roadmap_title": None,
        "blueprint_title": None,
        "github_title": "PR125 implement source revalidation supersession materiality scheduler",
        "branch_name": "pr125-source-revalidation-supersession-materiality-scheduler",
        "semantic_role": "CONTROL_PLANE_RECONCILIATION",
        "authority_scope": "CONTROL_PLANE_ONLY",
        "current_status": "MERGED",
        "github_audit_url": "https://github.com/Q8Meow/QTT_New0526/pull/125",
        "identity_relation_class": "REPO_CANONICAL_ONLY",
        "same_number_mismatch_recorded": True,
        "github_pr_state": "MERGED",
        "github_pr_mergedAt": "2026-05-19T20:03:45Z",
        "github_pr_mergeCommit_oid": "c7bbb8769cea72efe74db9f7f3be4439493dd4bc",
        "github_headRefName": "pr125-source-revalidation-supersession-materiality-scheduler",
        "github_baseRefName": "main",
        "owner_authorized_roadmap_pr": "PR107",
        "owner_authorized_next_capability": "SOURCE_REVALIDATION_SUPERSESSION_AND_MATERIALITY_SCHEDULER",
        "controller_used_as_record_not_veto": True,
    }
    for field, expected_value in expected.items():
        if pr125.get(field) != expected_value:
            failures.append(f"PR125 self-entry {field} must be {expected_value!r}")
    if "PR124_REPO_CANONICAL_SELF_ENTRY" not in pr125.get(
        "depends_on_roster_entries", []
    ):
        failures.append("PR125 self-entry must depend on PR124_REPO_CANONICAL_SELF_ENTRY")
    for marker in (
        "QTT_PR_IDENTITY_ROSTER_OK",
        "QTT_SOURCE_REVALIDATION_SUPERSESSION_AND_MATERIALITY_SCHEDULER_OK",
    ):
        if marker not in pr125.get("validator_markers", []):
            failures.append(f"PR125 self-entry must reference {marker}")
    if "GITHUB_AUDIT_NUMBER" not in pr125.get("reference_types", []):
        failures.append("PR125 self-entry reference_types must include GITHUB_AUDIT_NUMBER")
    missing_notes = _notes_contain(pr125, REQUIRED_PR125_NOTE_PARTS)
    if missing_notes:
        failures.append(f"PR125 self-entry notes missing: {', '.join(missing_notes)}")
    return failures


def _validate_pr126_self_entry(entries: Sequence[dict[str, Any]]) -> list[str]:
    failures: list[str] = []
    pr126 = _entry_by_id(entries, "PR126_REPO_CANONICAL_SELF_ENTRY")
    if pr126 is None:
        return ["missing PR126 repo-canonical self-entry"]
    expected = {
        "repo_canonical_pr_label": "PR126",
        "roadmap_pr_label": None,
        "blueprint_pr_label": None,
        "github_pr_number": 126,
        "repo_title": "Connector semantic binding implementation gate",
        "roadmap_title": None,
        "blueprint_title": None,
        "github_title": "PR126 implement connector semantic binding implementation gate",
        "branch_name": "pr126-connector-semantic-binding-implementation-gate",
        "semantic_role": "CONTROL_PLANE_RECONCILIATION",
        "authority_scope": "CONTROL_PLANE_ONLY",
        "current_status": "MERGED",
        "github_audit_url": "https://github.com/Q8Meow/QTT_New0526/pull/126",
        "identity_relation_class": "REPO_CANONICAL_ONLY",
        "same_number_mismatch_recorded": True,
        "github_pr_state": "MERGED",
        "github_pr_mergedAt": "2026-05-19T21:39:57Z",
        "github_pr_mergeCommit_oid": "bbbf11f59da644b7519354802695b7cab050b6af",
        "github_headRefName": "pr126-connector-semantic-binding-implementation-gate",
        "github_baseRefName": "main",
        "owner_authorized_roadmap_pr": "PR108",
        "owner_authorized_next_capability": "CONNECTOR_SEMANTIC_BINDING_IMPLEMENTATION_GATE",
        "controller_used_as_record_not_veto": True,
    }
    for field, expected_value in expected.items():
        if pr126.get(field) != expected_value:
            failures.append(f"PR126 self-entry {field} must be {expected_value!r}")
    if "PR125_REPO_CANONICAL_SELF_ENTRY" not in pr126.get(
        "depends_on_roster_entries", []
    ):
        failures.append("PR126 self-entry must depend on PR125_REPO_CANONICAL_SELF_ENTRY")
    for marker in (
        "QTT_PR_IDENTITY_ROSTER_OK",
        "QTT_CONNECTOR_SEMANTIC_BINDING_IMPLEMENTATION_GATE_OK",
    ):
        if marker not in pr126.get("validator_markers", []):
            failures.append(f"PR126 self-entry must reference {marker}")
    if "GITHUB_AUDIT_NUMBER" not in pr126.get("reference_types", []):
        failures.append("PR126 self-entry reference_types must include GITHUB_AUDIT_NUMBER")
    missing_notes = _notes_contain(pr126, REQUIRED_PR126_NOTE_PARTS)
    if missing_notes:
        failures.append(f"PR126 self-entry notes missing: {', '.join(missing_notes)}")
    return failures


def _validate_pr127_self_entry(entries: Sequence[dict[str, Any]]) -> list[str]:
    failures: list[str] = []
    pr127 = _entry_by_id(entries, "PR127_REPO_CANONICAL_SELF_ENTRY")
    if pr127 is None:
        return ["missing PR127 repo-canonical self-entry"]
    expected = {
        "repo_canonical_pr_label": "PR127",
        "roadmap_pr_label": None,
        "blueprint_pr_label": None,
        "github_pr_number": 127,
        "repo_title": "Per-venue execution lifecycle model builder",
        "roadmap_title": None,
        "blueprint_title": None,
        "github_title": "PR127 implement per-venue execution lifecycle model builder",
        "branch_name": "pr127-per-venue-execution-lifecycle-model-builder",
        "semantic_role": "CONTROL_PLANE_RECONCILIATION",
        "authority_scope": "CONTROL_PLANE_ONLY",
        "current_status": "MERGED",
        "github_audit_url": "https://github.com/Q8Meow/QTT_New0526/pull/127",
        "identity_relation_class": "REPO_CANONICAL_ONLY",
        "same_number_mismatch_recorded": True,
        "github_pr_state": "MERGED",
        "github_pr_mergedAt": "2026-05-19T23:11:19Z",
        "github_pr_mergeCommit_oid": "84848c0bbe2fb17ca02b76acd6cca45150ac59f9",
        "github_headRefName": "pr127-per-venue-execution-lifecycle-model-builder",
        "github_baseRefName": "main",
        "owner_authorized_roadmap_pr": "PR109",
        "owner_authorized_next_capability": "PER_VENUE_EXECUTION_LIFECYCLE_MODEL_BUILDER",
        "controller_used_as_record_not_veto": True,
    }
    for field, expected_value in expected.items():
        if pr127.get(field) != expected_value:
            failures.append(f"PR127 self-entry {field} must be {expected_value!r}")
    if "PR126_REPO_CANONICAL_SELF_ENTRY" not in pr127.get(
        "depends_on_roster_entries", []
    ):
        failures.append("PR127 self-entry must depend on PR126_REPO_CANONICAL_SELF_ENTRY")
    for marker in (
        "QTT_PR_IDENTITY_ROSTER_OK",
        "QTT_PER_VENUE_EXECUTION_LIFECYCLE_MODEL_BUILDER_OK",
    ):
        if marker not in pr127.get("validator_markers", []):
            failures.append(f"PR127 self-entry must reference {marker}")
    if "GITHUB_AUDIT_NUMBER" not in pr127.get("reference_types", []):
        failures.append("PR127 self-entry reference_types must include GITHUB_AUDIT_NUMBER")
    missing_notes = _notes_contain(pr127, REQUIRED_PR127_NOTE_PARTS)
    if missing_notes:
        failures.append(f"PR127 self-entry notes missing: {', '.join(missing_notes)}")
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
        if number <= 116:
            matching_entries = [
                entry
                for entry in entries
                if entry.get("github_pr_number") == number
                and entry.get("roadmap_pr_label") == f"PR #{number}"
                and entry.get("same_number_mismatch_recorded") is True
            ]
            if not matching_entries:
                failures.append(f"entry-level same-number mismatch missing for GitHub #{number}")
    pr117_self = _entry_by_id(entries, "PR117_REPO_CANONICAL_SELF_ENTRY")
    if pr117_self is not None:
        if pr117_self.get("roadmap_pr_label") is not None:
            failures.append("repo-canonical PR117 must not take roadmap PR #117 label")
        if pr117_self.get("blueprint_pr_label") is not None:
            failures.append("repo-canonical PR117 must not take blueprint PR #117 label")
        if pr117_self.get("identity_relation_class") == "EXACT_SAME_SYSTEM_REFERENCE":
            failures.append("repo-canonical PR117 must not be treated as roadmap PR #117")

    for number in range(117, 128):
        self_entry = _entry_by_id(entries, f"PR{number}_REPO_CANONICAL_SELF_ENTRY")
        if self_entry is None:
            continue
        if self_entry.get("roadmap_pr_label") is not None:
            failures.append(f"repo-canonical PR{number} must not take roadmap PR #{number} label")
        if self_entry.get("blueprint_pr_label") is not None:
            failures.append(f"repo-canonical PR{number} must not take blueprint PR #{number} label")
        if self_entry.get("identity_relation_class") == "EXACT_SAME_SYSTEM_REFERENCE":
            failures.append(f"repo-canonical PR{number} must not be treated as roadmap PR #{number}")

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
    if summary.get("pr124_self_entry_does_not_assume_same_number_identity") is not True:
        failures.append("PR124 self-entry same-number mismatch summary must be confirmed")
    if summary.get("pr125_owner_authorized_roadmap_pr107_not_roadmap_pr125") is not True:
        failures.append("Repo PR125 owner authorization for Roadmap PR107 must be recorded")
    if summary.get("pr126_owner_authorized_roadmap_pr108_not_roadmap_pr126") is not True:
        failures.append("Repo PR126 owner authorization for Roadmap PR108 must be recorded")
    if summary.get("pr127_owner_authorized_roadmap_pr109_not_roadmap_pr127") is not True:
        failures.append("Repo PR127 owner authorization for Roadmap PR109 must be recorded")
    if summary.get("roadmap_controller_files_used_as_state_evidence_not_veto") is not True:
        failures.append("roadmap/controller files must be recorded as state evidence, not veto authority")
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
        "pr118_github_audit_number": (
            _entry_by_id(entries, "PR118_REPO_CANONICAL_SELF_ENTRY") or {}
        ).get("github_pr_number"),
        "pr118_github_audit_url": (
            _entry_by_id(entries, "PR118_REPO_CANONICAL_SELF_ENTRY") or {}
        ).get("github_audit_url"),
        "pr119_self_entry_present": _entry_by_id(
            entries, "PR119_REPO_CANONICAL_SELF_ENTRY"
        )
        is not None,
        "pr119_assumed_github_119": False,
        "pr119_assumed_roadmap_pr_119": False,
        "pr119_assumed_blueprint_pr_119": False,
        "pr119_github_audit_number": (
            _entry_by_id(entries, "PR119_REPO_CANONICAL_SELF_ENTRY") or {}
        ).get("github_pr_number"),
        "pr119_github_audit_url": (
            _entry_by_id(entries, "PR119_REPO_CANONICAL_SELF_ENTRY") or {}
        ).get("github_audit_url"),
        "pr120_self_entry_present": _entry_by_id(
            entries, "PR120_REPO_CANONICAL_SELF_ENTRY"
        )
        is not None,
        "pr120_assumed_github_120": False,
        "pr120_assumed_roadmap_pr_120": False,
        "pr120_assumed_blueprint_pr_120": False,
        "pr120_github_audit_number": (
            _entry_by_id(entries, "PR120_REPO_CANONICAL_SELF_ENTRY") or {}
        ).get("github_pr_number"),
        "pr120_github_audit_url": (
            _entry_by_id(entries, "PR120_REPO_CANONICAL_SELF_ENTRY") or {}
        ).get("github_audit_url"),
        "pr121_self_entry_present": _entry_by_id(
            entries, "PR121_REPO_CANONICAL_SELF_ENTRY"
        )
        is not None,
        "pr121_assumed_github_121": False,
        "pr121_assumed_roadmap_pr_121": False,
        "pr121_assumed_blueprint_pr_121": False,
        "pr121_github_audit_number": (
            _entry_by_id(entries, "PR121_REPO_CANONICAL_SELF_ENTRY") or {}
        ).get("github_pr_number"),
        "pr121_github_audit_url": (
            _entry_by_id(entries, "PR121_REPO_CANONICAL_SELF_ENTRY") or {}
        ).get("github_audit_url"),
        "pr122_self_entry_present": _entry_by_id(
            entries, "PR122_REPO_CANONICAL_SELF_ENTRY"
        )
        is not None,
        "pr122_assumed_github_122": False,
        "pr122_assumed_roadmap_pr_122": False,
        "pr122_assumed_blueprint_pr_122": False,
        "pr122_github_audit_number": (
            _entry_by_id(entries, "PR122_REPO_CANONICAL_SELF_ENTRY") or {}
        ).get("github_pr_number"),
        "pr122_github_audit_url": (
            _entry_by_id(entries, "PR122_REPO_CANONICAL_SELF_ENTRY") or {}
        ).get("github_audit_url"),
        "pr123_self_entry_present": _entry_by_id(
            entries, "PR123_REPO_CANONICAL_SELF_ENTRY"
        )
        is not None,
        "pr123_assumed_github_123": False,
        "pr123_assumed_roadmap_pr_123": False,
        "pr123_assumed_blueprint_pr_123": False,
        "pr123_github_audit_number": (
            _entry_by_id(entries, "PR123_REPO_CANONICAL_SELF_ENTRY") or {}
        ).get("github_pr_number"),
        "pr123_github_audit_url": (
            _entry_by_id(entries, "PR123_REPO_CANONICAL_SELF_ENTRY") or {}
        ).get("github_audit_url"),
        "pr124_self_entry_present": _entry_by_id(
            entries, "PR124_REPO_CANONICAL_SELF_ENTRY"
        )
        is not None,
        "pr124_assumed_github_124": False,
        "pr124_assumed_roadmap_pr_124": False,
        "pr124_assumed_blueprint_pr_124": False,
        "pr124_github_audit_number": (
            _entry_by_id(entries, "PR124_REPO_CANONICAL_SELF_ENTRY") or {}
        ).get("github_pr_number"),
        "pr124_github_audit_url": (
            _entry_by_id(entries, "PR124_REPO_CANONICAL_SELF_ENTRY") or {}
        ).get("github_audit_url"),
        "pr124_github_pr_state": (
            _entry_by_id(entries, "PR124_REPO_CANONICAL_SELF_ENTRY") or {}
        ).get("github_pr_state"),
        "pr124_github_pr_mergedAt": (
            _entry_by_id(entries, "PR124_REPO_CANONICAL_SELF_ENTRY") or {}
        ).get("github_pr_mergedAt"),
        "pr124_github_pr_mergeCommit_oid": (
            _entry_by_id(entries, "PR124_REPO_CANONICAL_SELF_ENTRY") or {}
        ).get("github_pr_mergeCommit_oid"),
        "pr125_self_entry_present": _entry_by_id(
            entries, "PR125_REPO_CANONICAL_SELF_ENTRY"
        )
        is not None,
        "pr125_assumed_github_125": False,
        "pr125_assumed_roadmap_pr_125": False,
        "pr125_assumed_blueprint_pr_125": False,
        "repo_pr125_owner_authorized_roadmap_pr107": True,
        "controller_used_as_record_not_veto_for_pr125": True,
        "pr126_self_entry_present": _entry_by_id(
            entries, "PR126_REPO_CANONICAL_SELF_ENTRY"
        )
        is not None,
        "pr126_assumed_github_126": False,
        "pr126_assumed_roadmap_pr_126": False,
        "pr126_assumed_blueprint_pr_126": False,
        "pr126_github_audit_number": (
            _entry_by_id(entries, "PR126_REPO_CANONICAL_SELF_ENTRY") or {}
        ).get("github_pr_number"),
        "pr126_github_audit_url": (
            _entry_by_id(entries, "PR126_REPO_CANONICAL_SELF_ENTRY") or {}
        ).get("github_audit_url"),
        "pr126_github_pr_state": (
            _entry_by_id(entries, "PR126_REPO_CANONICAL_SELF_ENTRY") or {}
        ).get("github_pr_state"),
        "pr126_github_pr_mergedAt": (
            _entry_by_id(entries, "PR126_REPO_CANONICAL_SELF_ENTRY") or {}
        ).get("github_pr_mergedAt"),
        "pr126_github_pr_mergeCommit_oid": (
            _entry_by_id(entries, "PR126_REPO_CANONICAL_SELF_ENTRY") or {}
        ).get("github_pr_mergeCommit_oid"),
        "repo_pr126_owner_authorized_roadmap_pr108": True,
        "controller_used_as_record_not_veto_for_pr126": True,
        "repo_pr127_assumed_roadmap_pr127": False,
        "pr127_self_entry_present": _entry_by_id(
            entries, "PR127_REPO_CANONICAL_SELF_ENTRY"
        )
        is not None,
        "pr127_github_audit_number": (
            _entry_by_id(entries, "PR127_REPO_CANONICAL_SELF_ENTRY") or {}
        ).get("github_pr_number"),
        "pr127_github_audit_url": (
            _entry_by_id(entries, "PR127_REPO_CANONICAL_SELF_ENTRY") or {}
        ).get("github_audit_url"),
        "pr127_github_pr_state": (
            _entry_by_id(entries, "PR127_REPO_CANONICAL_SELF_ENTRY") or {}
        ).get("github_pr_state"),
        "pr127_github_pr_mergedAt": (
            _entry_by_id(entries, "PR127_REPO_CANONICAL_SELF_ENTRY") or {}
        ).get("github_pr_mergedAt"),
        "pr127_github_pr_mergeCommit_oid": (
            _entry_by_id(entries, "PR127_REPO_CANONICAL_SELF_ENTRY") or {}
        ).get("github_pr_mergeCommit_oid"),
        "repo_pr127_owner_authorized_roadmap_pr109": True,
        "controller_used_as_record_not_veto_for_pr127": True,
        "repo_pr128_assumed_roadmap_pr128": False,
        "repo_pr128_owner_authorized_roadmap_pr110": True,
        "controller_used_as_record_not_veto_for_pr128": True,
        "repo_pr123_assumed_roadmap_pr123": False,
        "repo_pr123_owner_authorized_roadmap_pr106": True,
        "controller_used_as_record_not_veto_for_pr123": True,
        "repo_pr124_assumed_roadmap_pr124": False,
        "repo_pr124_owner_authorized_accepted_source_to_connector_semantic_binding_consumer_gate": True,
        "controller_used_as_record_not_veto_for_pr124": True,
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
    failures.extend(_validate_pr119_self_entry(entries))
    failures.extend(_validate_pr120_self_entry(entries))
    failures.extend(_validate_pr121_self_entry(entries))
    failures.extend(_validate_pr122_self_entry(entries))
    failures.extend(_validate_pr123_self_entry(entries))
    failures.extend(_validate_pr124_self_entry(entries))
    failures.extend(_validate_pr125_self_entry(entries))
    failures.extend(_validate_pr126_self_entry(entries))
    failures.extend(_validate_pr127_self_entry(entries))
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
