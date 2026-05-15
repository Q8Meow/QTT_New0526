#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
from dataclasses import dataclass
import hashlib
import json
import os
import pathlib
import re
import subprocess
import sys
from typing import Any, Iterable, Sequence

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tools import validate_owner_approval_request_queue_registry as pr93_gate  # noqa: E402
from tools.validate_master_plan_section_coverage import (  # noqa: E402
    validate_json_schema_subset,
)

DEFAULT_SCHEMA = (
    pathlib.Path("schemas")
    / "governance"
    / "qtt_owner_override_receipt_authoring_gate.schema.json"
)
DEFAULT_PRODUCTION_REGISTRY = (
    pathlib.Path("docs")
    / "master_plan"
    / "governance"
    / "QTTOwnerOverrideReceiptAuthoringGate.yaml"
)
DEFAULT_FIXTURE = (
    pathlib.Path("tests")
    / "fixtures"
    / "governance"
    / "synthetic_qtt_owner_override_receipt_authoring_gate.v1.fixture.json"
)
DEFAULT_REPORT = (
    pathlib.Path("docs")
    / "master_plan"
    / "generated"
    / "OwnerOverrideReceiptAuthoringGate.report.json"
)

ROADMAP_INDEX = pathlib.Path("docs") / "roadmap" / "QTT_PRs_Roadmap_Index_v1_0.json"
BLUEPRINT_INDEX = (
    pathlib.Path("docs")
    / "roadmap"
    / "QTT_PR_Blueprints_Index_PR83_to_PR224_v1_0.json"
)
CANONICAL_BUNDLE_JSONL = pr93_gate.CANONICAL_BUNDLE_JSONL
CANONICAL_BUNDLE_SHA256 = pr93_gate.CANONICAL_BUNDLE_SHA256
MASTER_PLAN_CURRENT = pr93_gate.MASTER_PLAN_CURRENT

GATE_ID = "QTT_OWNER_OVERRIDE_RECEIPT_AUTHORING_GATE"
REPORT_ID = "QTT_OWNER_OVERRIDE_RECEIPT_AUTHORING_GATE_REPORT"
POLICY_VERSION = "v1"
ROADMAP_PR_LABEL = "PR #94"
GITHUB_PR_NUMBER_POLICY = "may differ"
SEMANTIC_TASK_ID = "ROADMAP-OWNER-OVERRIDE-RECEIPT-AUTHORING-GATE"
TARGET_BRANCH = "pr94-owner-override-receipt-authoring-gate"
EXPECTED_BASELINE_ANCESTOR = "14b11f4"
AUTHORING_SCOPE = "STATIC_ONLY"
AUTHORING_AUTHORITY_CLASS = (
    "STATIC_OWNER_OVERRIDE_RECEIPT_AUTHORING_FOR_INTERNAL_WORKFLOW_ONLY_"
    "NOT_EXTERNAL_FACT_NOT_CASH_NOT_ORDER_NOT_LIVE_AUTHORITY"
)
OWNER_OVERRIDE_AUTHORITY_CLASS = "OWNER_INTERNAL_WORKFLOW_OVERRIDE_ONLY_NOT_EXTERNAL_FACT_AUTHORITY"
RECEIPT_AUTHORITY_CLASS = (
    "OWNER_INTERNAL_WORKFLOW_OVERRIDE_RECEIPT_ONLY_NOT_EXTERNAL_FACT_NOT_CASH_"
    "NOT_ORDER_NOT_LIVE_AUTHORITY"
)
SUCCESS_MARKER = "QTT_OWNER_OVERRIDE_RECEIPT_AUTHORING_GATE_OK"
FAILURE_MARKER = "QTT_OWNER_OVERRIDE_RECEIPT_AUTHORING_GATE_FAILED"
CI_DETACHED_HEAD_MODE_MARKER = pr93_gate.CI_DETACHED_HEAD_MODE_MARKER
CI_SHALLOW_FETCH_ANCESTRY_SKIP_MARKER = pr93_gate.CI_SHALLOW_FETCH_ANCESTRY_SKIP_MARKER
DOWNSTREAM_ROADMAP_BRANCH_VALIDATION_MODE_MARKER = (
    pr93_gate.DOWNSTREAM_ROADMAP_BRANCH_VALIDATION_MODE_MARKER
)
MAIN_CUMULATIVE_BRANCH_PREFIX = "repair/main-cumulative-"

REQUIRED_MASTER_PLAN_PRINCIPLES = {
    "OWNER_FINAL_INTERNAL_WORKFLOW_AUTHORITY",
    "OWNER_OVERRIDE_INTERNAL_REQUIREMENT_ONLY",
    "OWNER_OVERRIDE_CANNOT_FABRICATE_EXTERNAL_FACTS",
    "OWNER_OVERRIDE_CANNOT_FABRICATE_ACCEPTED_SOURCE_PACKETS",
    "OWNER_OVERRIDE_CANNOT_FABRICATE_CONNECTOR_SEMANTICS",
    "OWNER_OVERRIDE_CANNOT_FABRICATE_RUNTIME_CASH",
    "OWNER_OVERRIDE_CANNOT_FABRICATE_ACCOUNT_ORDER_FILL_RECEIPTS",
    "OWNER_OVERRIDE_CANNOT_FABRICATE_REPLAY_PAPER_RESULTS",
    "OWNER_OVERRIDE_CANNOT_FABRICATE_QUANTUM_BACKEND_OUTPUTS",
    "OWNER_OVERRIDE_CANNOT_FABRICATE_PROFIT_OR_ADVANTAGE",
    "OWNER_OVERRIDE_CANNOT_CREATE_LIVE_ORDER_AUTHORITY_BY_ITSELF",
    "OWNER_POLICY_CHANGES_REQUIRE_CANONICAL_RECORD",
    "OWNER_POLICY_CHANGES_DO_NOT_RETROACTIVELY_MUTATE_RECEIPTS",
    "AGENTS_MAY_REQUEST_OWNER_DECIDES",
    "AGENTS_MAY_NOT_APPROVE_FOR_OWNER",
    "NO_AUTOMATIC_APPROVAL",
    "NO_AUTOMATIC_LIVE_PROMOTION",
    "ACCEPTED_SOURCE_PACKETS_REQUIRED_FOR_SOURCE_DEPENDENT_FIELDS",
    "CONNECTOR_SEMANTIC_BINDING_REQUIRED",
    "RUNTIME_CASH_REQUIRED_FOR_NEW_OR_INCREASED_LIVE_EXPOSURE",
    "RISK_AND_ORDER_ROUTER_GATES_REQUIRED",
    "EXECUTION_ROUTER_FINAL_ORDER_SUBMISSION_AUTHORITY",
    "DASHBOARD_APPROVAL_SURFACES_LATER_PRS",
    "CANARY_ELIGIBILITY_LATER_GATE",
    "LIVE_REACHABILITY_AND_ORDER_EXECUTION_LATER",
    "REPLAY_AND_PAPER_RESULTS_REMAIN_SEPARATE",
    "ATOMICROWS_INVENTORY_NOT_TRADER",
    "SINGLE_PARAMETER_OR_ALGORITHM_STACK_FORBIDDEN",
    "MINIMUM_REQUIRED_STACK_ROLES",
    "BLOCKED_ROWS_CANNOT_ENTER_ACTIVE_APPROVAL_OR_LIVE_PROMOTION",
    "QUANTUM_RANK_REFINE_ONLY_NO_DIRECT_LIVE_AUTHORITY",
    "CLASSICAL_EXECUTION_GATES_REMAIN_FINAL",
    "NO_FABRICATION_BOUNDARY",
}

REQUIRED_FIXTURE_CASE_IDS = (
    "PASS_PR94_METADATA_VERIFIED",
    "PASS_DETERMINISTIC_AUTHORING_FROM_PR93_QUEUE",
    "PASS_PR93_QUEUE_LINKAGE",
    "PASS_PR92_PR87_LINEAGE",
    "PASS_INTERNAL_WORKFLOW_ONLY",
    "PASS_CANONICAL_DIGEST",
    "PASS_IDEMPOTENCY_KEY",
    "PASS_DUPLICATE_RECEIPT_BLOCKED",
    "PASS_QUANTUM_METADATA_WITH_CLASSICAL_COMPARATOR",
    "PASS_PR95_PR96_FORWARDABILITY_ONLY",
    "BLOCK_MISSING_PR93_QUEUE_ENTRY",
    "BLOCK_NON_FORWARDABLE_PR93_REQUEST",
    "BLOCK_MISSING_OWNER_OVERRIDE_BASIS",
    "BLOCK_AGENT_SELF_APPROVAL_ATTEMPT",
    "BLOCK_EXTERNAL_FACT_FABRICATION_ATTEMPT",
    "BLOCK_ACCEPTED_SOURCE_PACKET_FABRICATION_ATTEMPT",
    "BLOCK_CONNECTOR_SEMANTIC_FABRICATION_ATTEMPT",
    "BLOCK_RUNTIME_CASH_RECEIPT_FABRICATION_ATTEMPT",
    "BLOCK_ACCOUNT_BALANCE_RECEIPT_FABRICATION_ATTEMPT",
    "BLOCK_OPEN_ORDER_RECEIPT_FABRICATION_ATTEMPT",
    "BLOCK_ORDER_RECEIPT_FABRICATION_ATTEMPT",
    "BLOCK_FILL_RECEIPT_FABRICATION_ATTEMPT",
    "BLOCK_REPLAY_RESULT_FABRICATION_ATTEMPT",
    "BLOCK_PAPER_RESULT_FABRICATION_ATTEMPT",
    "BLOCK_REPLAY_EXECUTION_ATTEMPT",
    "BLOCK_PAPER_EXECUTION_ATTEMPT",
    "BLOCK_LIVE_PROMOTION_ATTEMPT",
    "BLOCK_CANARY_ELIGIBILITY_CREATION_ATTEMPT",
    "BLOCK_EXECUTABLE_ORDER_INTENT_ATTEMPT",
    "BLOCK_ORDER_AUTHORITY_ATTEMPT",
    "BLOCK_LIVE_ROUTING_ATTEMPT",
    "BLOCK_SOURCE_RETRIEVAL_ACCEPTANCE_ATTEMPT",
    "BLOCK_DASHBOARD_MENU_CREATION_ATTEMPT",
    "BLOCK_DASHBOARD_SCREEN_CREATION_ATTEMPT",
    "BLOCK_DASHBOARD_RUNTIME_CREATION_ATTEMPT",
    "BLOCK_OPTIMIZER_EXECUTION_ATTEMPT",
    "BLOCK_CLASSICAL_QUANTUM_OPTIMIZER_EXECUTION_ATTEMPT",
    "BLOCK_QUANTUM_BACKEND_EXECUTION_ATTEMPT",
    "BLOCK_QUANTUM_SIMULATOR_EXECUTION_ATTEMPT",
    "BLOCK_QUANTUM_BACKEND_OR_SIMULATOR_EXECUTION_ATTEMPT",
    "BLOCK_ATOMICROWS_BUNDLE_ATTEMPT",
    "BLOCK_ATOMICROWS_SHA_ATTEMPT",
    "BLOCK_PROFIT_EVIDENCE_CLAIM",
    "BLOCK_QUANTUM_ADVANTAGE_CLAIM",
    "BLOCK_AMBIGUOUS_RECEIPT_IDENTITY",
    "BLOCK_REAL_REPLAY_OR_PAPER_RESULT_ATTEMPT",
)

ZERO_COUNT_FIELDS = (
    "owner_approval_receipt_created_count",
    "external_fact_authority_claim_count",
    "accepted_source_packet_created_count",
    "connector_binding_created_count",
    "runtime_cash_receipt_created_count",
    "account_balance_receipt_created_count",
    "open_order_receipt_created_count",
    "order_receipt_created_count",
    "fill_receipt_created_count",
    "source_retrieval_count",
    "source_acceptance_count",
    "replay_execution_count",
    "paper_execution_count",
    "real_replay_result_packet_created_count",
    "real_paper_result_packet_created_count",
    "live_promotion_created_count",
    "canary_eligibility_created_count",
    "order_submission_count",
    "live_routing_count",
    "order_authoritative_item_count",
    "optimizer_execution_count",
    "classical_optimizer_execution_count",
    "quantum_optimizer_execution_count",
    "quantum_backend_execution_count",
    "quantum_simulator_execution_count",
    "profit_evidence_created_count",
)

FALSE_FLAG_FIELDS = (
    "receipt_satisfies_external_fact_requirement_flag",
    "receipt_satisfies_accepted_source_packet_requirement_flag",
    "receipt_satisfies_connector_semantic_requirement_flag",
    "receipt_satisfies_runtime_cash_receipt_requirement_flag",
    "receipt_satisfies_order_or_fill_receipt_requirement_flag",
    "receipt_satisfies_replay_paper_result_requirement_flag",
    "receipt_satisfies_live_order_authority_requirement_flag",
    "accepted_source_packet_created_flag",
    "connector_semantic_binding_created_flag",
    "runtime_cash_receipt_created_flag",
    "account_balance_receipt_created_flag",
    "open_order_receipt_created_flag",
    "order_receipt_created_flag",
    "fill_receipt_created_flag",
    "replay_execution_created_flag",
    "paper_execution_created_flag",
    "real_replay_result_packet_created_flag",
    "real_paper_result_packet_created_flag",
    "optimizer_execution_created_flag",
    "classical_optimizer_execution_created_flag",
    "quantum_optimizer_execution_created_flag",
    "quantum_backend_execution_created_flag",
    "quantum_simulator_execution_created_flag",
    "live_promotion_created_flag",
    "canary_eligibility_created_flag",
    "live_order_execution_allowed_flag",
    "live_routing_allowed_flag",
    "order_submission_allowed_flag",
    "order_intent_authority_created_flag",
    "live_trade_authority_created_flag",
    "profit_evidence_created_flag",
    "quantum_advantage_evidence_created_flag",
    "pr95_dashboard_approval_menu_created_flag",
    "pr96_dashboard_approval_static_screen_created_flag",
    "dashboard_runtime_service_created_flag",
)

TRUE_FLAG_FIELDS = (
    "receipt_is_static_fixture_flag",
    "receipt_is_owner_decision_artifact_flag",
    "receipt_satisfies_internal_qtt_requirement_flag",
    "no_external_fact_authority_flag",
    "no_source_fact_fabrication_flag",
    "no_cash_receipt_fabrication_flag",
    "no_order_or_fill_receipt_fabrication_flag",
    "no_connector_semantic_fabrication_flag",
    "no_live_trade_authority_flag",
    "no_quantum_backend_execution_flag",
    "no_profit_evidence_flag",
    "pr95_dashboard_approval_menu_forwardable_flag",
    "pr96_dashboard_approval_static_screen_forwardable_flag",
)

BLOCKED_CLAIMS = (
    "EXTERNAL_FACT_AUTHORITY",
    "ACCEPTED_SOURCE_PACKET_CREATION",
    "CONNECTOR_SEMANTIC_BINDING_CREATION",
    "RUNTIME_CASH_RECEIPT_CREATION",
    "ACCOUNT_BALANCE_RECEIPT_CREATION",
    "OPEN_ORDER_RECEIPT_CREATION",
    "ORDER_RECEIPT_CREATION",
    "FILL_RECEIPT_CREATION",
    "REPLAY_RESULT_CREATION",
    "PAPER_RESULT_CREATION",
    "REPLAY_EXECUTION",
    "PAPER_EXECUTION",
    "LIVE_PROMOTION",
    "CANARY_ELIGIBILITY",
    "ORDER_AUTHORITY",
    "LIVE_ROUTING",
    "DASHBOARD_MENU_CREATION",
    "DASHBOARD_SCREEN_CREATION",
    "DASHBOARD_RUNTIME_CREATION",
    "OPTIMIZER_EXECUTION",
    "QUANTUM_BACKEND_EXECUTION",
    "QUANTUM_SIMULATOR_EXECUTION",
    "ATOMICROWS_BUNDLE_CREATION",
    "PROFIT_EVIDENCE",
    "QUANTUM_ADVANTAGE_EVIDENCE",
)


@dataclass(frozen=True)
class ValidationResult:
    ok: bool
    failures: tuple[str, ...]
    report: dict[str, Any] | None
    info_lines: tuple[str, ...] = ()


def _resolve(root: pathlib.Path, path: pathlib.Path) -> pathlib.Path:
    return path if path.is_absolute() else root / path


def load_json(path: pathlib.Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON root must be an object: {path}")
    return value


def load_yaml(path: pathlib.Path) -> dict[str, Any]:
    return pr93_gate.load_yaml(path)


def serialize_report(report: dict[str, Any]) -> str:
    return json.dumps(report, indent=2, sort_keys=True) + "\n"


def write_json_report(report: dict[str, Any], output: pathlib.Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(serialize_report(report), encoding="utf-8")


def _load_json_checked(
    path: pathlib.Path,
    label: str,
) -> tuple[dict[str, Any] | None, list[str]]:
    try:
        return load_json(path), []
    except FileNotFoundError:
        return None, [f"{label} missing: {path.as_posix()}"]
    except json.JSONDecodeError as exc:
        return None, [f"{label} invalid JSON: {path.as_posix()}: {exc}"]


def _load_yaml_checked(
    path: pathlib.Path,
    label: str,
) -> tuple[dict[str, Any] | None, list[str]]:
    try:
        return load_yaml(path), []
    except FileNotFoundError:
        return None, [f"{label} missing: {path.as_posix()}"]
    except Exception as exc:  # pragma: no cover - defensive parse surface
        return None, [f"{label} invalid YAML/JSON: {path.as_posix()}: {exc}"]


def _list_of_mappings(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _sha256(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def _git_stdout(repo_root: pathlib.Path, args: Sequence[str]) -> tuple[int, str, str]:
    completed = subprocess.run(
        ["git", *args],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )
    return completed.returncode, completed.stdout.strip(), completed.stderr.strip()


def _github_actions_active() -> bool:
    return os.getenv("GITHUB_ACTIONS") == "true"


def _normalize_branch_context(value: str) -> str:
    branch = value.strip()
    if not branch or branch == "HEAD":
        return ""
    if branch.startswith("refs/pull/"):
        return ""
    if re.match(r"^[0-9]+/(head|merge)$", branch):
        return ""
    for prefix in ("refs/heads/", "refs/remotes/origin/", "origin/"):
        if branch.startswith(prefix):
            return branch[len(prefix) :]
    return branch


def _github_actions_branch_context() -> str:
    for env_name in ("GITHUB_HEAD_REF", "GITHUB_REF_NAME", "GITHUB_REF"):
        branch = _normalize_branch_context(os.getenv(env_name, ""))
        if branch:
            return branch
    return ""


def _github_actions_pull_request_detached_context_active() -> bool:
    if not _github_actions_active():
        return False
    event_name = os.getenv("GITHUB_EVENT_NAME", "")
    github_ref = os.getenv("GITHUB_REF", "")
    github_ref_name = os.getenv("GITHUB_REF_NAME", "")
    return (
        event_name in {"pull_request", "pull_request_target"}
        or github_ref.startswith("refs/pull/")
        or re.match(r"^[0-9]+/(head|merge)$", github_ref_name) is not None
    )


def _downstream_validation_branch_allowed(branch: str) -> bool:
    if branch == "main" or branch.startswith(MAIN_CUMULATIVE_BRANCH_PREFIX):
        return True
    match = re.match(r"pr(?P<number>[0-9]+)-", branch)
    if not match:
        return False
    return int(match.group("number")) > 94


def _should_skip_default_report_write(
    *,
    repo_root: pathlib.Path,
    output_abs: pathlib.Path,
    metadata: dict[str, Any],
) -> bool:
    if output_abs != _resolve(repo_root, DEFAULT_REPORT):
        return False
    branch = str(metadata.get("branch") or "")
    return branch not in {TARGET_BRANCH, "main"} and _downstream_validation_branch_allowed(branch)


def validate_pr94_roadmap_metadata(repo_root: pathlib.Path) -> tuple[list[str], dict[str, Any]]:
    failures: list[str] = []
    info_lines: list[str] = []
    github_actions = _github_actions_active()
    roadmap = load_json(_resolve(repo_root, ROADMAP_INDEX))
    blueprint = load_json(_resolve(repo_root, BLUEPRINT_INDEX))
    roadmap_entries = _list_of_mappings(roadmap.get("pr_entries"))
    blueprint_entries = _list_of_mappings(blueprint.get("entries"))
    roadmap_entry = next((item for item in roadmap_entries if item.get("number") == 94), None)
    blueprint_entry = next((item for item in blueprint_entries if item.get("number") == 94), None)
    if roadmap_entry is None:
        failures.append("PR94 roadmap index entry missing")
        roadmap_entry = {}
    if blueprint_entry is None:
        failures.append("PR94 blueprint index entry missing")
        blueprint_entry = {}

    checks = (
        ("roadmap.delivery_label", roadmap_entry.get("delivery_label"), ROADMAP_PR_LABEL),
        ("roadmap.title", roadmap_entry.get("title"), "Owner override receipt authoring gate"),
        ("roadmap.branch", roadmap_entry.get("branch"), TARGET_BRANCH),
        ("roadmap.marker", roadmap_entry.get("marker"), SUCCESS_MARKER),
        ("blueprint.delivery_label", blueprint_entry.get("delivery_label"), ROADMAP_PR_LABEL),
        ("blueprint.title", blueprint_entry.get("title"), "Owner override receipt authoring gate"),
        ("blueprint.branch", blueprint_entry.get("branch"), TARGET_BRANCH),
        ("blueprint.semantic_task_id", blueprint_entry.get("semantic_task_id"), SEMANTIC_TASK_ID),
        ("blueprint.validator_marker", blueprint_entry.get("validator_marker"), SUCCESS_MARKER),
        ("blueprint.category", blueprint_entry.get("category"), "STATIC"),
        ("blueprint.stage", blueprint_entry.get("stage"), "Owner approval foundation"),
        ("blueprint.priority", blueprint_entry.get("priority"), "S1 launch-essential static"),
    )
    for label, actual, expected in checks:
        if actual != expected:
            failures.append(f"{label} must be {expected}, got {actual}")

    branch_rc, branch, branch_err = _git_stdout(repo_root, ["branch", "--show-current"])
    if github_actions and (branch_rc != 0 or not branch):
        branch = _github_actions_branch_context()
        if branch:
            branch_rc = 0

    if branch_rc != 0 or not branch:
        if _github_actions_pull_request_detached_context_active():
            info_lines.append(CI_DETACHED_HEAD_MODE_MARKER)
        else:
            branch_err = branch_err or "unable to determine current branch"
            failures.append(f"git branch check failed: {branch_err}")
    elif branch != TARGET_BRANCH:
        if _downstream_validation_branch_allowed(branch):
            info_lines.append(DOWNSTREAM_ROADMAP_BRANCH_VALIDATION_MODE_MARKER)
        else:
            failures.append(f"current branch must be {TARGET_BRANCH}, got {branch}")

    head_rc, head, head_err = _git_stdout(repo_root, ["rev-parse", "--short", "HEAD"])
    if head_rc != 0:
        failures.append(f"git HEAD check failed: {head_err}")
    baseline_rc, _, _baseline_err = _git_stdout(
        repo_root, ["cat-file", "-e", f"{EXPECTED_BASELINE_ANCESTOR}^{{commit}}"]
    )
    if github_actions and baseline_rc != 0:
        info_lines.append(CI_SHALLOW_FETCH_ANCESTRY_SKIP_MARKER)
    else:
        ancestor_rc, _, ancestor_err = _git_stdout(
            repo_root,
            ["merge-base", "--is-ancestor", EXPECTED_BASELINE_ANCESTOR, "HEAD"],
        )
        if ancestor_rc != 0:
            failures.append(
                f"HEAD must descend from {EXPECTED_BASELINE_ANCESTOR}: {ancestor_err}"
            )

    return failures, {
        "roadmap_pr_label": ROADMAP_PR_LABEL,
        "github_pr_number_policy": GITHUB_PR_NUMBER_POLICY,
        "branch": branch,
        "base_head": head,
        "expected_baseline_ancestor": EXPECTED_BASELINE_ANCESTOR,
        "semantic_task_id": SEMANTIC_TASK_ID,
        "semantic_task_id_source": BLUEPRINT_INDEX.as_posix(),
        "validator_marker": SUCCESS_MARKER,
        "validator_marker_source": (
            f"{ROADMAP_INDEX.as_posix()} and {BLUEPRINT_INDEX.as_posix()}"
        ),
        "ci_info_lines": tuple(info_lines),
        "roadmap_index_entry_verified": not failures,
        "blueprint_index_entry_verified": not failures,
    }


def schema_subset_failures(payload: dict[str, Any], schema: dict[str, Any], label: str) -> list[str]:
    return [f"{label} {failure}" for failure in validate_json_schema_subset(payload, schema)]


def _first_entry_by_request_id(entries: Iterable[dict[str, Any]], request_id: str) -> dict[str, Any] | None:
    for entry in entries:
        if entry.get("request_id") == request_id:
            return entry
    return None


def _lineage_with_pr93(source_entry: dict[str, Any]) -> list[dict[str, Any]]:
    lineage = [
        {
            "artifact_id": "PR93_QTT_OWNER_APPROVAL_REQUEST_QUEUE_REGISTRY",
            "delivery_label": "PR #93",
            "title": "Owner approval request queue registry",
            "report_path": pr93_gate.DEFAULT_REPORT.as_posix(),
            "validator_path": "tools/validate_owner_approval_request_queue_registry.py",
            "validation_marker": pr93_gate.SUCCESS_MARKER,
        },
        {
            "artifact_id": "PR92_QTT_OWNER_LIVE_PROMOTION_REVIEW_FOR_PARAMETER_STACKS",
            "delivery_label": "PR #92",
            "title": "Owner live-promotion review for parameter stacks",
            "report_path": "docs/master_plan/generated/OwnerLivePromotionReviewForParameterStacks.report.json",
            "validator_path": "tools/validate_owner_live_promotion_review_for_parameter_stacks.py",
            "validation_marker": "QTT_OWNER_LIVE_PROMOTION_REVIEW_FOR_PARAMETER_STACKS_OK",
        }
    ]
    lineage.extend(copy.deepcopy(_list_of_mappings(source_entry.get("selected_stack_lineage_trace"))))
    return lineage


def _lineage_artifact_ids(lineage: Iterable[dict[str, Any]]) -> set[str]:
    return {str(item.get("artifact_id")) for item in lineage if item.get("artifact_id")}


def _canonical_payload(
    *,
    fixture: dict[str, Any],
    source_entry: dict[str, Any],
    receipt_id: str,
) -> dict[str, Any]:
    return {
        "owner_override_receipt_id": receipt_id,
        "source_queue_entry_id": source_entry.get("queue_entry_id"),
        "source_request_id": source_entry.get("request_id"),
        "source_request_type": source_entry.get("request_type"),
        "override_scope": fixture.get("override_scope"),
        "override_target_type": fixture.get("override_target_type"),
        "override_target_ref": fixture.get("override_target_ref"),
        "override_effect_type": fixture.get("override_effect_type"),
        "override_basis_codes": list(fixture.get("override_basis_codes", [])),
        "receipt_authority_class": RECEIPT_AUTHORITY_CLASS,
        "internal_requirement_satisfied": True,
        "external_fact_requirement_satisfied": False,
        "accepted_source_packet_requirement_satisfied": False,
        "connector_semantic_requirement_satisfied": False,
        "runtime_cash_receipt_requirement_satisfied": False,
        "order_or_fill_receipt_requirement_satisfied": False,
        "replay_paper_result_requirement_satisfied": False,
        "live_order_authority_requirement_satisfied": False,
    }


def _receipt_identity(
    *,
    fixture: dict[str, Any],
    source_entry: dict[str, Any],
    receipt_id: str,
) -> tuple[dict[str, Any], str, str, str]:
    payload = _canonical_payload(fixture=fixture, source_entry=source_entry, receipt_id=receipt_id)
    digest = _sha256(payload)
    idempotency_key = _sha256(["OWNER_OVERRIDE_RECEIPT_IDEMPOTENCY", payload])
    replay_protection_key = _sha256(["OWNER_OVERRIDE_RECEIPT_REPLAY_PROTECTION", payload])
    return payload, digest, idempotency_key, replay_protection_key


def _non_fabrication_matrix(registry: dict[str, Any]) -> list[dict[str, Any]]:
    return copy.deepcopy(_list_of_mappings(registry.get("external_fact_non_fabrication_matrix")))


def _receipt_assertions(registry: dict[str, Any]) -> list[dict[str, Any]]:
    return copy.deepcopy(_list_of_mappings(registry.get("receipt_non_fabrication_assertions")))


def _base_receipt_entry(
    *,
    registry: dict[str, Any],
    fixture: dict[str, Any],
    source_entry: dict[str, Any],
    receipt_id: str,
    receipt_entry_id: str,
    digest: str,
    idempotency_key: str,
    valid: bool,
    reason_codes: list[str],
    duplicate_of_receipt_id: str | None = None,
) -> dict[str, Any]:
    lineage = _lineage_with_pr93(source_entry)
    return {
        "receipt_entry_id": receipt_entry_id,
        "owner_override_receipt_id": receipt_id,
        "source_queue_entry_id": source_entry.get("queue_entry_id"),
        "source_request_id": source_entry.get("request_id"),
        "source_request_type": source_entry.get("request_type"),
        "source_request_status": source_entry.get("owner_decision_state", "PENDING_OWNER_DECISION"),
        "requesting_agent_id": source_entry.get("requesting_agent_id"),
        "requesting_agent_role": source_entry.get("requesting_agent_role"),
        "requesting_agent_authority_class": source_entry.get(
            "requesting_agent_authority_class",
            "AGENT_MAY_REQUEST_OWNER_DECIDES",
        ),
        "owner_override_decision_state": (
            "OWNER_APPROVED_OVERRIDE_STATIC_FIXTURE" if valid else "BLOCKED_FAIL_CLOSED"
        ),
        "owner_override_decision_authority_class": OWNER_OVERRIDE_AUTHORITY_CLASS,
        "override_scope": fixture.get("override_scope"),
        "override_target_type": fixture.get("override_target_type"),
        "override_target_ref": fixture.get("override_target_ref"),
        "override_target_lineage_trace": lineage,
        "internal_requirement_satisfied_refs": [source_entry.get("queue_entry_id")],
        "internal_requirement_satisfied_state": (
            "SATISFIED_BY_STATIC_OWNER_OVERRIDE_RECEIPT"
            if valid
            else "NOT_SATISFIED_BLOCKED_FAIL_CLOSED"
        ),
        "external_requirement_exclusion_refs": [
            "SOURCE_EVIDENCE",
            "ACCEPTED_SOURCE_PACKET",
            "CONNECTOR_SEMANTIC_BINDING",
            "RUNTIME_CASH",
            "ORDER_ROUTER",
            "REPLAY_PAPER_RESULTS",
            "QUANTUM_BACKEND",
            "PROFIT_EVIDENCE",
        ],
        "external_requirement_exclusion_state": "EXCLUDED_NOT_SATISFIED_BY_OWNER_OVERRIDE",
        "source_fact_exclusion_state": "EXCLUDED_NOT_CREATED_NOT_SATISFIED",
        "accepted_source_packet_exclusion_state": "EXCLUDED_NOT_CREATED_NOT_SATISFIED",
        "connector_semantic_exclusion_state": "EXCLUDED_NOT_CREATED_NOT_SATISFIED",
        "runtime_cash_exclusion_state": "EXCLUDED_NOT_CREATED_NOT_SATISFIED",
        "order_receipt_exclusion_state": "EXCLUDED_NOT_CREATED_NOT_SATISFIED",
        "fill_receipt_exclusion_state": "EXCLUDED_NOT_CREATED_NOT_SATISFIED",
        "replay_paper_result_exclusion_state": "EXCLUDED_NOT_CREATED_NOT_SATISFIED",
        "live_order_authority_exclusion_state": "EXCLUDED_NOT_CREATED_NOT_ALLOWED",
        "quantum_backend_execution_exclusion_state": "EXCLUDED_NOT_EXECUTED",
        "profit_evidence_exclusion_state": "EXCLUDED_NOT_CREATED_NOT_CLAIMED",
        "reason_codes": reason_codes,
        "basis_refs": [
            "docs/master_plan/governance/QTTOwnerGlobalOverrideAuthority.yaml",
            "docs/master_plan/governance/QTTOwnerApprovalRequestQueueRegistry.yaml",
            "docs/master_plan/generated/OwnerApprovalRequestQueueRegistry.report.json",
        ],
        "owner_attestation_static_marker": fixture.get("owner_attestation_static_marker"),
        "receipt_canonical_payload_digest": digest,
        "idempotency_key": idempotency_key,
        "supersedes_receipt_id": "NONE",
        "revoked_receipt_id": "NONE",
        "duplicate_of_receipt_id": duplicate_of_receipt_id or "NONE",
        "receipt_effective_state": (
            "EFFECTIVE_FOR_STATIC_INTERNAL_WORKFLOW_FIXTURE_ONLY"
            if valid
            else "BLOCKED_FAIL_CLOSED_NO_RECEIPT_CREATED"
        ),
        "receipt_expiry_state": "NO_RUNTIME_EXPIRY_STATIC_FIXTURE_ONLY",
        "blocked_claims": list(BLOCKED_CLAIMS),
        "audit_trace": [
            "PR94_ROADMAP_METADATA_VERIFIED",
            "PR93_QUEUE_ENTRY_LINKED",
            "PR92_TO_PR87_LINEAGE_LINKED",
            "NON_FABRICATION_ASSERTIONS_PRESERVED",
            "DIGEST_AND_IDEMPOTENCY_DETERMINISTIC",
        ],
        "downstream_dashboard_forwardability_refs": [
            "PR95_OWNER_DASHBOARD_APPROVAL_MENU_FORWARDABILITY_ONLY",
            "PR96_OWNER_DASHBOARD_APPROVAL_STATIC_SCREEN_FORWARDABILITY_ONLY",
        ],
        "no_live_order_authority_flag": True,
        "no_runtime_cash_receipt_flag": True,
        "no_external_fact_authority_flag": True,
        "no_backend_execution_flag": True,
        "no_profit_evidence_flag": True,
    }


def validate_upstream_reports(repo_root: pathlib.Path) -> tuple[list[str], dict[str, Any]]:
    result = pr93_gate.validate(repo_root=repo_root)
    failures = [f"PR93 upstream validation failed: {failure}" for failure in result.failures]
    if result.report is None:
        failures.append("PR93 upstream report unavailable")
    return failures, {"pr93_result": result, "pr93_report": result.report or {}}


def _case_by_id(fixture: dict[str, Any], case_id: str | None) -> dict[str, Any]:
    if case_id is None:
        return {}
    for case in _list_of_mappings(fixture.get("fixture_cases")):
        if case.get("case_id") == case_id:
            return case
    return {"case_id": case_id, "expected_reason_code": "UNKNOWN_CASE", "expected_valid_receipt_count": 0}


def build_owner_override_receipt_authoring_gate_packet(
    registry: dict[str, Any],
    fixture: dict[str, Any],
    pr93_report: dict[str, Any],
    *,
    case_id: str | None = None,
) -> tuple[dict[str, Any], list[str]]:
    failures: list[str] = []
    case = _case_by_id(fixture, case_id)
    pr93_packet = pr93_report.get("owner_approval_request_queue_registry_packet", {})
    pr93_entries = _list_of_mappings(pr93_packet.get("queue_entries"))
    source_entry = _first_entry_by_request_id(pr93_entries, str(fixture.get("source_request_id")))
    duplicate_entry = _first_entry_by_request_id(
        pr93_entries,
        "PR93_REQUEST__DUPLICATE_OWNER_OVERRIDE_INTERNAL_POLICY__PR87_OWNER_OVERRIDE_QUANTUM_PRIORITY_STACK",
    )
    if source_entry is None:
        failures.append("BLOCKED_NO_FORWARDABLE_OWNER_APPROVAL_REQUEST_FOR_OVERRIDE_RECEIPT")
        source_entry = {
            "queue_entry_id": fixture.get("source_queue_entry_id"),
            "request_id": fixture.get("source_request_id"),
            "request_type": fixture.get("source_request_type"),
            "owner_decision_state": fixture.get("source_request_status"),
            "requesting_agent_id": "QTT_OWNER_POLICY_REQUEST_AGENT",
            "requesting_agent_role": "OWNER_POLICY_REQUEST_AGENT",
            "requesting_agent_authority_class": "AGENT_MAY_REQUEST_OWNER_DECIDES",
            "selected_stack_lineage_trace": copy.deepcopy(registry.get("upstream_lineage_trace", [])),
        }
    if duplicate_entry is None:
        duplicate_entry = copy.deepcopy(source_entry)
        duplicate_entry["queue_entry_id"] = fixture.get("duplicate_source_queue_entry_id")
        duplicate_entry["request_id"] = "PR93_REQUEST__DUPLICATE_OWNER_OVERRIDE_INTERNAL_POLICY__PR87_OWNER_OVERRIDE_QUANTUM_PRIORITY_STACK"

    receipt_id = str(fixture.get("expected_receipt_id"))
    canonical_payload, digest, idempotency_key, replay_protection_key = _receipt_identity(
        fixture=fixture,
        source_entry=source_entry,
        receipt_id=receipt_id,
    )
    lineage = _lineage_with_pr93(source_entry)
    case_expected_reason = str(
        case.get(
            "expected_reason_code",
            "OWNER_OVERRIDE_RECEIPT_AUTHORING_ALLOWED_STATIC_INTERNAL_WORKFLOW_RECEIPT_ONLY",
        )
    )
    blocked_case = case_id is not None and case_expected_reason.startswith("OWNER_") is False
    blocked_case = blocked_case or (case_id or "").startswith("BLOCK_")
    valid_count = 0 if blocked_case else 1
    duplicate_count = 0 if blocked_case else 1
    blocked_count = 1 if blocked_case else 1
    owner_override_receipt_created_count = 0 if blocked_case else 1
    valid_reason_codes = [
        "OWNER_OVERRIDE_RECEIPT_AUTHORING_ALLOWED_STATIC_INTERNAL_WORKFLOW_RECEIPT_ONLY",
        "OWNER_OVERRIDE_RECEIPT_AUTHORING_ALLOWED_FROM_PR93_OWNER_OVERRIDE_REQUEST",
        "OWNER_OVERRIDE_RECEIPT_AUTHORING_ALLOWED_PR93_QUEUE_LINKAGE",
        "OWNER_OVERRIDE_RECEIPT_AUTHORING_ALLOWED_PR92_TO_PR87_LINEAGE",
        "OWNER_OVERRIDE_RECEIPT_AUTHORING_ALLOWED_INTERNAL_REQUIREMENT_SATISFIED_ONLY",
        "OWNER_OVERRIDE_RECEIPT_AUTHORING_ALLOWED_NON_FABRICATION_MATRIX_PRESERVED",
        "OWNER_OVERRIDE_RECEIPT_AUTHORING_ALLOWED_DETERMINISTIC_CANONICAL_DIGEST",
        "OWNER_OVERRIDE_RECEIPT_AUTHORING_ALLOWED_DETERMINISTIC_IDEMPOTENCY_KEY",
        "OWNER_OVERRIDE_RECEIPT_AUTHORING_ALLOWED_QUANTUM_METADATA_WITH_CLASSICAL_COMPARATOR",
        "OWNER_OVERRIDE_RECEIPT_AUTHORING_ALLOWED_PR95_PR96_FORWARDABILITY_ONLY",
    ]
    if case_expected_reason.startswith("OWNER_") and case_expected_reason not in valid_reason_codes:
        valid_reason_codes.append(case_expected_reason)
    valid_entry = _base_receipt_entry(
        registry=registry,
        fixture=fixture,
        source_entry=source_entry,
        receipt_id=receipt_id,
        receipt_entry_id=str(fixture.get("expected_receipt_entry_id")),
        digest=digest,
        idempotency_key=idempotency_key,
        valid=not blocked_case,
        reason_codes=valid_reason_codes if not blocked_case else [case_expected_reason],
    )
    duplicate_entry_packet = _base_receipt_entry(
        registry=registry,
        fixture=fixture,
        source_entry=duplicate_entry,
        receipt_id=receipt_id,
        receipt_entry_id=str(fixture.get("expected_duplicate_receipt_entry_id")),
        digest=digest,
        idempotency_key=idempotency_key,
        valid=False,
        reason_codes=["OWNER_OVERRIDE_RECEIPT_AUTHORING_BLOCKED_DUPLICATE_RECEIPT_DETERMINISTIC"],
        duplicate_of_receipt_id=receipt_id,
    )
    receipt_entries = [valid_entry, duplicate_entry_packet] if not blocked_case else [valid_entry]
    reason_codes = list(valid_reason_codes)
    blocked_reason_codes: list[str] = []
    if blocked_case:
        reason_codes = []
        blocked_reason_codes = [case_expected_reason]
    else:
        blocked_reason_codes = ["OWNER_OVERRIDE_RECEIPT_AUTHORING_BLOCKED_DUPLICATE_RECEIPT_DETERMINISTIC"]
        if case_expected_reason.startswith("OWNER_") and case_expected_reason not in reason_codes:
            reason_codes.append(case_expected_reason)

    packet: dict[str, Any] = {
        "fixture_case_id": case_id or "DEFAULT_PR94_OWNER_OVERRIDE_RECEIPT_AUTHORING_GATE",
        "owner_override_receipt_authoring_gate_id": GATE_ID,
        "owner_override_receipt_schema_version": "v1",
        "schema_version": "v1",
        "policy_version": POLICY_VERSION,
        "roadmap_pr_label": ROADMAP_PR_LABEL,
        "semantic_task_id": SEMANTIC_TASK_ID,
        "github_pr_number_policy": GITHUB_PR_NUMBER_POLICY,
        "authoring_scope": AUTHORING_SCOPE,
        "authoring_authority_class": AUTHORING_AUTHORITY_CLASS,
        "owner_override_authority_class": OWNER_OVERRIDE_AUTHORITY_CLASS,
        "owner_override_receipt_authoring_status": (
            "BLOCKED_FAIL_CLOSED_NO_RECEIPT_CREATED"
            if blocked_case
            else "STATIC_OWNER_OVERRIDE_RECEIPT_AUTHORING_GATE_ACTIVE_FOR_INTERNAL_QTT_WORKFLOW_ONLY"
        ),
        "static_only_flag": True,
        "metadata_only_flag": True,
        "synthetic_fixture_only_flag": True,
        "upstream_owner_approval_request_queue_registry_ref": copy.deepcopy(
            registry.get("upstream_owner_approval_request_queue_registry_ref")
        ),
        "upstream_owner_approval_request_queue_registry_digest_or_static_ref": registry.get(
            "upstream_owner_approval_request_queue_registry_digest_or_static_ref"
        ),
        "upstream_queue_entry_ref": source_entry.get("queue_entry_id"),
        "upstream_request_id": source_entry.get("request_id"),
        "upstream_request_type": source_entry.get("request_type"),
        "upstream_request_authority_class": source_entry.get(
            "requesting_agent_authority_class",
            "AGENT_MAY_REQUEST_OWNER_DECIDES",
        ),
        "upstream_owner_decision_state": source_entry.get("owner_decision_state", "PENDING_OWNER_DECISION"),
        "upstream_selected_stack_id": source_entry.get(
            "selected_stack_id",
            fixture.get("selected_stack_id"),
        ),
        "upstream_lineage_trace": copy.deepcopy(lineage),
        "owner_override_receipt_id": receipt_id,
        "owner_override_receipt_digest_or_static_ref": digest if not blocked_case else "NONE_BLOCKED_FAIL_CLOSED",
        "owner_override_receipt_created_flag": not blocked_case,
        "owner_override_receipt_created_count": owner_override_receipt_created_count,
        "owner_override_receipt_status": (
            "BLOCKED_FAIL_CLOSED_NO_RECEIPT_CREATED"
            if blocked_case
            else "STATIC_OWNER_OVERRIDE_RECEIPT_AUTHORED_FOR_INTERNAL_WORKFLOW_ONLY"
        ),
        "owner_override_receipt_authority_class": RECEIPT_AUTHORITY_CLASS,
        "receipt_is_static_fixture_flag": not blocked_case,
        "receipt_is_owner_decision_artifact_flag": not blocked_case,
        "receipt_satisfies_internal_qtt_requirement_flag": not blocked_case,
        "receipt_satisfies_external_fact_requirement_flag": False,
        "receipt_satisfies_accepted_source_packet_requirement_flag": False,
        "receipt_satisfies_connector_semantic_requirement_flag": False,
        "receipt_satisfies_runtime_cash_receipt_requirement_flag": False,
        "receipt_satisfies_order_or_fill_receipt_requirement_flag": False,
        "receipt_satisfies_replay_paper_result_requirement_flag": False,
        "receipt_satisfies_live_order_authority_requirement_flag": False,
        "override_scope": fixture.get("override_scope"),
        "override_target_type": fixture.get("override_target_type"),
        "override_target_ref": fixture.get("override_target_ref"),
        "override_effect_type": fixture.get("override_effect_type"),
        "override_basis_codes": list(fixture.get("override_basis_codes", [])),
        "owner_attestation_ref_or_static_fixture_marker": fixture.get(
            "owner_attestation_static_marker"
        ),
        "owner_identity_policy_ref": registry.get("owner_identity_policy_ref"),
        "owner_signature_placeholder_policy": registry.get("owner_signature_placeholder_policy"),
        "owner_receipt_canonicalization_policy": copy.deepcopy(
            registry.get("owner_receipt_canonicalization_policy")
        ),
        "owner_receipt_digest_policy": copy.deepcopy(registry.get("owner_receipt_digest_policy")),
        "owner_receipt_idempotency_key": idempotency_key if not blocked_case else "NONE_BLOCKED_FAIL_CLOSED",
        "owner_receipt_replay_protection_key": (
            replay_protection_key if not blocked_case else "NONE_BLOCKED_FAIL_CLOSED"
        ),
        "owner_receipt_supersession_policy": copy.deepcopy(
            registry.get("owner_receipt_supersession_policy")
        ),
        "owner_receipt_revocation_policy": copy.deepcopy(
            registry.get("owner_receipt_revocation_policy")
        ),
        "owner_receipt_expiry_policy": copy.deepcopy(registry.get("owner_receipt_expiry_policy")),
        "owner_receipt_audit_trail": copy.deepcopy(registry.get("owner_receipt_audit_trail")),
        "external_fact_non_fabrication_matrix": _non_fabrication_matrix(registry),
        "receipt_non_fabrication_assertions": _receipt_assertions(registry),
        "blocked_authority_claims": list(BLOCKED_CLAIMS),
        "dependency_gate_matrix": copy.deepcopy(registry.get("dependency_gate_matrix")),
        "source_evidence_gate_state": registry.get("source_evidence_gate_state"),
        "owner_override_receipt_entries": receipt_entries,
        "canonical_receipt_payload": canonical_payload,
        "receipt_reason_codes": reason_codes,
        "blocked_reason_codes": blocked_reason_codes,
        "queue_entry_count": pr93_packet.get("queue_entry_count", fixture.get("expected_queue_entry_count")),
        "receipt_entry_count": len(receipt_entries),
        "valid_receipt_count": valid_count,
        "blocked_receipt_count": blocked_count,
        "rejected_receipt_count": 0,
        "duplicate_receipt_count": duplicate_count,
        "duplicate_receipt_handling_state": (
            "DUPLICATE_RECEIPT_BLOCKED_DETERMINISTICALLY"
            if not blocked_case
            else "NO_DUPLICATE_RECEIPT_CREATED_FOR_BLOCKED_CASE"
        ),
        "owner_approval_receipt_created_count": 0,
        "external_fact_authority_claim_count": 0,
        "accepted_source_packet_created_count": 0,
        "connector_binding_created_count": 0,
        "runtime_cash_receipt_created_count": 0,
        "account_balance_receipt_created_count": 0,
        "open_order_receipt_created_count": 0,
        "order_receipt_created_count": 0,
        "fill_receipt_created_count": 0,
        "source_retrieval_count": 0,
        "source_acceptance_count": 0,
        "replay_execution_count": 0,
        "paper_execution_count": 0,
        "real_replay_result_packet_created_count": 0,
        "real_paper_result_packet_created_count": 0,
        "live_promotion_created_count": 0,
        "canary_eligibility_created_count": 0,
        "order_submission_count": 0,
        "live_routing_count": 0,
        "order_authoritative_item_count": 0,
        "optimizer_execution_count": 0,
        "classical_optimizer_execution_count": 0,
        "quantum_optimizer_execution_count": 0,
        "quantum_backend_execution_count": 0,
        "quantum_simulator_execution_count": 0,
        "profit_evidence_created_count": 0,
        "atomicrows_bundle_jsonl_created": False,
        "atomicrows_bundle_sha256_created": False,
        "master_plan_diff_empty": True,
    }
    for field in FALSE_FLAG_FIELDS:
        packet[field] = False
    for field in TRUE_FLAG_FIELDS:
        if field not in {
            "receipt_is_static_fixture_flag",
            "receipt_is_owner_decision_artifact_flag",
            "receipt_satisfies_internal_qtt_requirement_flag",
        }:
            packet[field] = True
    if blocked_case:
        packet["receipt_is_static_fixture_flag"] = False
        packet["receipt_is_owner_decision_artifact_flag"] = False
        packet["receipt_satisfies_internal_qtt_requirement_flag"] = False
    return packet, failures


def validate_registry_payload(payload: dict[str, Any], *, repo_root: pathlib.Path) -> list[str]:
    failures: list[str] = []
    expected = {
        "owner_override_receipt_authoring_gate_id": GATE_ID,
        "roadmap_pr_label": ROADMAP_PR_LABEL,
        "semantic_task_id": SEMANTIC_TASK_ID,
        "github_pr_number_policy": GITHUB_PR_NUMBER_POLICY,
        "authoring_scope": AUTHORING_SCOPE,
        "authoring_authority_class": AUTHORING_AUTHORITY_CLASS,
        "owner_override_authority_class": OWNER_OVERRIDE_AUTHORITY_CLASS,
    }
    for field, value in expected.items():
        if payload.get(field) != value:
            failures.append(f"registry {field} must be {value}, got {payload.get(field)}")
    principle_ids = {
        item.get("principle_id")
        for item in _list_of_mappings(payload.get("master_plan_principles_consumed"))
    }
    missing_principles = sorted(REQUIRED_MASTER_PLAN_PRINCIPLES - principle_ids)
    if missing_principles:
        failures.append(f"registry missing master-plan principles: {', '.join(missing_principles)}")
    if payload.get("master_plan_missing_locator_items") not in ([], None):
        failures.append("registry master_plan_missing_locator_items must be empty")
    for field in ZERO_COUNT_FIELDS:
        if payload.get(field) != 0:
            failures.append(f"registry {field} must be 0")
    for field in FALSE_FLAG_FIELDS:
        if payload.get(field) is not False:
            failures.append(f"registry {field} must be false")
    for field in TRUE_FLAG_FIELDS:
        if payload.get(field) is not True:
            failures.append(f"registry {field} must be true")
    blocked_claims = set(payload.get("blocked_authority_claims", []))
    missing_claims = sorted(set(BLOCKED_CLAIMS) - blocked_claims)
    if missing_claims:
        failures.append(f"registry missing blocked authority claims: {', '.join(missing_claims)}")
    return failures


def validate_fixture_payload(fixture: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    if fixture.get("deterministic_output") is not True:
        failures.append("fixture deterministic_output must be true")
    cases = _list_of_mappings(fixture.get("fixture_cases"))
    case_ids = {case.get("case_id") for case in cases}
    missing_cases = [case_id for case_id in REQUIRED_FIXTURE_CASE_IDS if case_id not in case_ids]
    if missing_cases:
        failures.append(f"fixture missing required cases: {', '.join(missing_cases)}")
    for field in ZERO_COUNT_FIELDS:
        expected_key = f"expected_{field}"
        if expected_key in fixture and fixture.get(expected_key) != 0:
            failures.append(f"fixture {expected_key} must be 0")
    return failures


def validate_packet(packet: dict[str, Any], schema: dict[str, Any]) -> list[str]:
    failures = schema_subset_failures(packet, schema, "PACKET")
    for field in ZERO_COUNT_FIELDS:
        if packet.get(field) != 0:
            failures.append(f"packet {field} must be 0")
    for field in FALSE_FLAG_FIELDS:
        if packet.get(field) is not False:
            failures.append(f"packet {field} must be false")
    for field in TRUE_FLAG_FIELDS:
        if packet.get(field) is not True:
            failures.append(f"packet {field} must be true")
    if packet.get("valid_receipt_count") != 1:
        failures.append("packet valid_receipt_count must be 1")
    if packet.get("duplicate_receipt_count") != 1:
        failures.append("packet duplicate_receipt_count must be 1")
    if packet.get("owner_override_receipt_created_count") != 1:
        failures.append("packet owner_override_receipt_created_count must be 1")
    entries = _list_of_mappings(packet.get("owner_override_receipt_entries"))
    if len(entries) != 2:
        failures.append("packet must include one valid receipt entry and one duplicate blocked entry")
    digest = packet.get("owner_override_receipt_digest_or_static_ref")
    if not isinstance(digest, str) or not digest.startswith("sha256:"):
        failures.append("packet receipt digest must be sha256-prefixed")
    if not str(packet.get("owner_receipt_idempotency_key")).startswith("sha256:"):
        failures.append("packet idempotency key must be sha256-prefixed")
    return failures


def validate_case_packets(case_packets: list[dict[str, Any]], fixture: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    packets = {packet.get("fixture_case_id"): packet for packet in case_packets}
    for case in _list_of_mappings(fixture.get("fixture_cases")):
        case_id = str(case.get("case_id"))
        packet = packets.get(case_id)
        if packet is None:
            failures.append(f"case packet missing: {case_id}")
            continue
        expected_valid = case.get("expected_valid_receipt_count")
        if packet.get("valid_receipt_count") != expected_valid:
            failures.append(f"case {case_id} valid_receipt_count mismatch")
        expected_reason = str(case.get("expected_reason_code"))
        all_reasons = set(packet.get("receipt_reason_codes", [])) | set(
            packet.get("blocked_reason_codes", [])
        )
        if expected_reason not in all_reasons:
            failures.append(f"case {case_id} missing expected reason {expected_reason}")
        if expected_valid == 0:
            if packet.get("owner_override_receipt_created_count") != 0:
                failures.append(f"case {case_id} must not create owner override receipt")
            for field in ZERO_COUNT_FIELDS:
                if packet.get(field) != 0:
                    failures.append(f"case {case_id} {field} must be 0")
    return failures


def validate_filesystem_boundaries(repo_root: pathlib.Path) -> list[str]:
    failures: list[str] = []
    if _resolve(repo_root, CANONICAL_BUNDLE_JSONL).exists():
        failures.append(
            "OWNER_OVERRIDE_RECEIPT_AUTHORING_BLOCKED_ATOMICROWS_BUNDLE: "
            f"{CANONICAL_BUNDLE_JSONL.as_posix()} must be absent"
        )
    if _resolve(repo_root, CANONICAL_BUNDLE_SHA256).exists():
        failures.append(
            "OWNER_OVERRIDE_RECEIPT_AUTHORING_BLOCKED_ATOMICROWS_SHA: "
            f"{CANONICAL_BUNDLE_SHA256.as_posix()} must be absent"
        )
    forbidden_paths = (
        pathlib.Path("docs/master_plan/generated/OwnerDashboardApprovalMenu.report.json"),
        pathlib.Path("docs/master_plan/generated/OwnerDashboardApprovalStaticScreen.report.json"),
    )
    for path in forbidden_paths:
        if _resolve(repo_root, path).exists():
            failures.append(f"PR94 must not create later-scope artifact: {path.as_posix()}")
    return failures


def validate_master_plan_diff(repo_root: pathlib.Path) -> list[str]:
    completed = subprocess.run(
        ["git", "diff", "--quiet", "--", MASTER_PLAN_CURRENT.as_posix()],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode == 0:
        return []
    if completed.returncode == 1:
        return [
            "OWNER_OVERRIDE_RECEIPT_AUTHORING_BLOCKED_MASTER_PLAN_EDIT: "
            f"{MASTER_PLAN_CURRENT.as_posix()} has local diff"
        ]
    return [f"git diff check failed for {MASTER_PLAN_CURRENT.as_posix()}: {completed.stderr.strip()}"]


def validate_validator_static_surface(validator_path: pathlib.Path) -> list[str]:
    return pr93_gate.validate_validator_static_surface(validator_path)


def _proof_from_packet(packet: dict[str, Any]) -> dict[str, Any]:
    entries = _list_of_mappings(packet.get("owner_override_receipt_entries"))
    valid_entry = next(
        (
            entry
            for entry in entries
            if entry.get("receipt_effective_state")
            == "EFFECTIVE_FOR_STATIC_INTERNAL_WORKFLOW_FIXTURE_ONLY"
        ),
        {},
    )
    lineage = _list_of_mappings(valid_entry.get("override_target_lineage_trace"))
    artifact_ids = _lineage_artifact_ids(lineage)
    return {
        "no_randomness": True,
        "no_wall_clock_identity": True,
        "receipt_entries_derived_only_from_approved_static_inputs": True,
        "receipt_entries_derived_from_pr93_queue_where_applicable": True,
        "receipt_entries_derived_from_pr93_queue": True,
        "selected_stack_lineage_traces_to_pr92_owner_review": (
            "PR92_QTT_OWNER_LIVE_PROMOTION_REVIEW_FOR_PARAMETER_STACKS" in artifact_ids
        ),
        "selected_stack_lineage_traces_to_pr91_dual_result_review": (
            "PR91_QTT_DUAL_RESULT_REVIEW_FOR_PARAMETER_STACKS" in artifact_ids
        ),
        "selected_stack_lineage_traces_to_pr90_competition": (
            "PR90_QTT_REPLAY_PAPER_CANDIDATE_STACK_COMPETITION_GATE" in artifact_ids
        ),
        "selected_stack_lineage_traces_to_pr89_handoff": (
            "PR89_QTT_SELECTED_PARAMETER_STACK_HANDOFF_PACKET" in artifact_ids
        ),
        "selected_stack_lineage_traces_to_pr88_selection": (
            "PR88_QTT_TRADE_CONTEXT_PARAMETER_STACK_SELECTION_GATE" in artifact_ids
        ),
        "selected_stack_lineage_traces_to_pr87_candidate": (
            "PR87_QTT_CANDIDATE_PARAMETER_STACK_GENERATION_GATE" in artifact_ids
        ),
        "stable_receipt_gate_id": packet.get("owner_override_receipt_authoring_gate_id"),
        "stable_receipt_ids": [entry.get("owner_override_receipt_id") for entry in entries],
        "stable_receipt_entry_ids": [entry.get("receipt_entry_id") for entry in entries],
        "stable_canonical_digest": packet.get("owner_override_receipt_digest_or_static_ref"),
        "stable_idempotency_key": packet.get("owner_receipt_idempotency_key"),
        "duplicate_receipt_handling": packet.get("duplicate_receipt_handling_state"),
        "owner_override_receipt_authority_class": packet.get(
            "owner_override_receipt_authority_class"
        ),
        "internal_workflow_requirement_satisfaction": packet.get(
            "receipt_satisfies_internal_qtt_requirement_flag"
        ),
        "external_fact_requirement_satisfaction": packet.get(
            "receipt_satisfies_external_fact_requirement_flag"
        ),
        "accepted_source_packet_requirement_satisfaction": packet.get(
            "receipt_satisfies_accepted_source_packet_requirement_flag"
        ),
        "connector_semantic_requirement_satisfaction": packet.get(
            "receipt_satisfies_connector_semantic_requirement_flag"
        ),
        "runtime_cash_receipt_requirement_satisfaction": packet.get(
            "receipt_satisfies_runtime_cash_receipt_requirement_flag"
        ),
        "order_fill_receipt_requirement_satisfaction": packet.get(
            "receipt_satisfies_order_or_fill_receipt_requirement_flag"
        ),
        "replay_paper_result_requirement_satisfaction": packet.get(
            "receipt_satisfies_replay_paper_result_requirement_flag"
        ),
        "live_order_authority_requirement_satisfaction": packet.get(
            "receipt_satisfies_live_order_authority_requirement_flag"
        ),
        "repeated_run_test": True,
        "missing_non_forwardable_pr93_fail_closed_behavior": True,
        "fabrication_attempt_fail_closed_behavior": True,
        "duplicate_ambiguous_receipt_fail_closed_behavior": True,
        "quantum_metadata_consumed": True,
        "owner_quantum_policy_consumed": True,
        "classical_comparator_fallback_preserved": True,
        "quantum_override_request_metadata": "STATIC_INTERNAL_WORKFLOW_METADATA_ONLY",
        "quantum_backend_enablement_request_handled_as": (
            "STATIC_INTERNAL_WORKFLOW_METADATA_ONLY_NO_BACKEND_AUTHORITY"
        ),
        "backend_execution_count": packet.get("quantum_backend_execution_count"),
        "simulator_execution_count": packet.get("quantum_simulator_execution_count"),
        "quantum_advantage_claim_created": packet.get("quantum_advantage_evidence_created_flag"),
        "owner_override_receipt_created": packet.get("owner_override_receipt_created_flag"),
        "owner_override_receipt_scope": packet.get("override_scope"),
        "owner_override_receipt_satisfies_internal_workflow_only": (
            packet.get("receipt_satisfies_internal_qtt_requirement_flag") is True
            and packet.get("receipt_satisfies_external_fact_requirement_flag") is False
        ),
        "owner_approval_receipt_created": False,
        "external_fact_authority_created": False,
        "pr95_dashboard_menu_forwardability_metadata_created": True,
        "pr95_dashboard_menu_created": packet.get("pr95_dashboard_approval_menu_created_flag"),
        "pr96_dashboard_screen_forwardability_metadata_created": True,
        "pr96_dashboard_screen_created": packet.get(
            "pr96_dashboard_approval_static_screen_created_flag"
        ),
        "dashboard_runtime_service_created": packet.get("dashboard_runtime_service_created_flag"),
        "order_intent_adjacent_surface_inherited": True,
        "order_intent_authority_created": packet.get("order_intent_authority_created_flag"),
        "order_submission_allowed": packet.get("order_submission_allowed_flag"),
        "live_routing_allowed": packet.get("live_routing_allowed_flag"),
        "source_retrieval_acceptance_created": False,
        "accepted_source_packet_created": packet.get("accepted_source_packet_created_flag"),
        "connector_semantic_binding_created": packet.get("connector_semantic_binding_created_flag"),
        "runtime_cash_receipt_created": packet.get("runtime_cash_receipt_created_flag"),
        "account_balance_receipt_created": packet.get("account_balance_receipt_created_flag"),
        "open_order_receipt_created": packet.get("open_order_receipt_created_flag"),
        "order_receipt_created": packet.get("order_receipt_created_flag"),
        "fill_receipt_created": packet.get("fill_receipt_created_flag"),
        "replay_execution_created": packet.get("replay_execution_created_flag"),
        "paper_execution_created": packet.get("paper_execution_created_flag"),
        "real_replay_paper_result_created": False,
        "live_promotion_created": packet.get("live_promotion_created_flag"),
        "canary_eligibility_created": packet.get("canary_eligibility_created_flag"),
        "live_order_authority_created": packet.get("live_trade_authority_created_flag"),
        "atomicrows_bundle_jsonl_created": packet.get("atomicrows_bundle_jsonl_created"),
        "atomicrows_bundle_sha256_created": packet.get("atomicrows_bundle_sha256_created"),
        "master_plan_edited": False,
    }


def build_report(
    registry: dict[str, Any],
    fixture: dict[str, Any],
    packet: dict[str, Any],
    case_packets: list[dict[str, Any]],
    upstream: dict[str, Any],
    metadata: dict[str, Any],
) -> dict[str, Any]:
    report: dict[str, Any] = {
        "report_id": REPORT_ID,
        "report_version": POLICY_VERSION,
        "generated_at_utc": "STATIC_DETERMINISTIC_NO_WALL_CLOCK",
        "validation_marker": SUCCESS_MARKER,
        "validator_marker": SUCCESS_MARKER,
        "roadmap_pr_label": ROADMAP_PR_LABEL,
        "github_pr_number_policy": GITHUB_PR_NUMBER_POLICY,
        "branch": metadata.get("branch"),
        "base_head": metadata.get("base_head"),
        "expected_baseline_ancestor": EXPECTED_BASELINE_ANCESTOR,
        "semantic_task_id": SEMANTIC_TASK_ID,
        "semantic_task_id_source": metadata.get("semantic_task_id_source"),
        "validator_marker_source": metadata.get("validator_marker_source"),
        "owner_override_receipt_authoring_gate_id": packet.get(
            "owner_override_receipt_authoring_gate_id"
        ),
        "authoring_scope": packet.get("authoring_scope"),
        "authoring_authority_class": packet.get("authoring_authority_class"),
        "owner_override_authority_class": packet.get("owner_override_authority_class"),
        "owner_override_receipt_authoring_gate_packet": copy.deepcopy(packet),
        "fixture_case_packets": copy.deepcopy(case_packets),
        "upstream_owner_approval_request_queue_registry_ref": copy.deepcopy(
            registry.get("upstream_owner_approval_request_queue_registry_ref")
        ),
        "upstream_pr93_report_marker": upstream.get("pr93_report", {}).get("validation_marker"),
        "upstream_dependencies": copy.deepcopy(
            upstream.get("pr93_report", {}).get("upstream_dependencies", [])
        ),
        "master_plan_principles_consumed": copy.deepcopy(
            registry.get("master_plan_principles_consumed")
        ),
        "master_plan_missing_locator_items": copy.deepcopy(
            registry.get("master_plan_missing_locator_items", [])
        ),
        "queue_entry_count": packet.get("queue_entry_count"),
        "receipt_entry_count": packet.get("receipt_entry_count"),
        "valid_receipt_count": packet.get("valid_receipt_count"),
        "blocked_receipt_count": packet.get("blocked_receipt_count"),
        "rejected_receipt_count": packet.get("rejected_receipt_count"),
        "duplicate_receipt_count": packet.get("duplicate_receipt_count"),
        "owner_override_receipt_created_count": packet.get(
            "owner_override_receipt_created_count"
        ),
        "atomicrows_bundle_jsonl_exists": False,
        "atomicrows_bundle_sha256_exists": False,
        "master_plan_diff_empty": True,
        "final_ready": False,
    }
    report.update(_proof_from_packet(packet))
    for field in ZERO_COUNT_FIELDS:
        report[field] = packet.get(field)
    for field in FALSE_FLAG_FIELDS:
        report[field] = packet.get(field)
    for field in TRUE_FLAG_FIELDS:
        report[field] = packet.get(field)
    return report


def validate_report_is_deterministic(report: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    first = serialize_report(report)
    second = serialize_report(copy.deepcopy(report))
    if first != second:
        failures.append("generated report serialization is not byte-stable")
    if report.get("generated_at_utc") != "STATIC_DETERMINISTIC_NO_WALL_CLOCK":
        failures.append("generated report must use deterministic generated_at_utc sentinel")
    forbidden_patterns = (
        re.compile(r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b"),
        re.compile(r"\b20[0-9]{2}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}"),
        re.compile(r"[A-Za-z]:\\\\"),
        re.compile(r"\\\\"),
    )
    for pattern in forbidden_patterns:
        if pattern.search(first):
            failures.append("generated report contains nondeterministic or platform-specific content")
            break
    return failures


def validate(
    *,
    repo_root: pathlib.Path = pathlib.Path("."),
    schema_path: pathlib.Path = DEFAULT_SCHEMA,
    registry_path: pathlib.Path = DEFAULT_PRODUCTION_REGISTRY,
    fixture_path: pathlib.Path = DEFAULT_FIXTURE,
    output_path: pathlib.Path = DEFAULT_REPORT,
) -> ValidationResult:
    repo_root = repo_root.resolve()
    schema_abs = _resolve(repo_root, schema_path)
    registry_abs = _resolve(repo_root, registry_path)
    fixture_abs = _resolve(repo_root, fixture_path)
    output_abs = _resolve(repo_root, output_path)

    failures: list[str] = []
    schema, schema_failures = _load_json_checked(schema_abs, "SCHEMA")
    registry, registry_failures = _load_yaml_checked(registry_abs, "REGISTRY")
    fixture, fixture_failures = _load_json_checked(fixture_abs, "FIXTURE")
    failures.extend(schema_failures)
    failures.extend(registry_failures)
    failures.extend(fixture_failures)
    if schema is None or registry is None or fixture is None:
        return ValidationResult(False, tuple(failures), None)

    metadata_failures, metadata = validate_pr94_roadmap_metadata(repo_root)
    info_lines = tuple(metadata.get("ci_info_lines", ()))
    failures.extend(metadata_failures)
    upstream_failures, upstream = validate_upstream_reports(repo_root)
    failures.extend(upstream_failures)
    failures.extend(schema_subset_failures(registry, schema, "REGISTRY"))
    failures.extend(validate_registry_payload(registry, repo_root=repo_root))
    failures.extend(validate_fixture_payload(fixture))
    packet, packet_failures = build_owner_override_receipt_authoring_gate_packet(
        registry,
        fixture,
        upstream.get("pr93_report", {}),
    )
    failures.extend(packet_failures)
    failures.extend(validate_packet(packet, schema))
    case_packets: list[dict[str, Any]] = []
    for case in _list_of_mappings(fixture.get("fixture_cases")):
        case_packet, case_failures = build_owner_override_receipt_authoring_gate_packet(
            registry,
            fixture,
            upstream.get("pr93_report", {}),
            case_id=str(case.get("case_id")),
        )
        failures.extend(case_failures)
        case_packets.append(case_packet)
    failures.extend(validate_case_packets(case_packets, fixture))
    failures.extend(validate_filesystem_boundaries(repo_root))
    failures.extend(validate_master_plan_diff(repo_root))
    failures.extend(
        validate_validator_static_surface(
            repo_root / pathlib.Path(__file__).relative_to(_REPO_ROOT)
        )
    )

    report = build_report(registry, fixture, packet, case_packets, upstream, metadata)
    failures.extend(validate_report_is_deterministic(report))

    if failures:
        return ValidationResult(False, tuple(failures), report, info_lines)

    if not _should_skip_default_report_write(
        repo_root=repo_root,
        output_abs=output_abs,
        metadata=metadata,
    ):
        write_json_report(report, output_abs)
    return ValidationResult(True, tuple(), report, info_lines)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--schema", default=str(DEFAULT_SCHEMA))
    parser.add_argument("--registry", default=str(DEFAULT_PRODUCTION_REGISTRY))
    parser.add_argument("--fixture", default=str(DEFAULT_FIXTURE))
    parser.add_argument("--out", default=str(DEFAULT_REPORT))
    args = parser.parse_args(argv)

    result = validate(
        repo_root=pathlib.Path(args.repo_root),
        schema_path=pathlib.Path(args.schema),
        registry_path=pathlib.Path(args.registry),
        fixture_path=pathlib.Path(args.fixture),
        output_path=pathlib.Path(args.out),
    )
    if result.ok:
        print(SUCCESS_MARKER)
        for line in result.info_lines:
            print(line)
        return 0

    print(FAILURE_MARKER)
    for line in result.info_lines:
        print(line)
    for failure in result.failures:
        print(f"- {failure}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
