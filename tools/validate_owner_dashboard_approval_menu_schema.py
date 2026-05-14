#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
from dataclasses import dataclass
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

from tools import validate_owner_override_receipt_authoring_gate as pr94_gate  # noqa: E402
from tools.validate_master_plan_section_coverage import (  # noqa: E402
    validate_json_schema_subset,
)

DEFAULT_SCHEMA = (
    pathlib.Path("schemas")
    / "governance"
    / "qtt_owner_dashboard_approval_menu_schema.schema.json"
)
DEFAULT_PRODUCTION_REGISTRY = (
    pathlib.Path("docs")
    / "master_plan"
    / "governance"
    / "QTTOwnerDashboardApprovalMenuSchema.yaml"
)
DEFAULT_FIXTURE = (
    pathlib.Path("tests")
    / "fixtures"
    / "governance"
    / "synthetic_qtt_owner_dashboard_approval_menu_schema.v1.fixture.json"
)
DEFAULT_REPORT = (
    pathlib.Path("docs")
    / "master_plan"
    / "generated"
    / "OwnerDashboardApprovalMenuSchema.report.json"
)

ROADMAP_INDEX = pathlib.Path("docs") / "roadmap" / "QTT_PRs_Roadmap_Index_v1_0.json"
BLUEPRINT_INDEX = (
    pathlib.Path("docs")
    / "roadmap"
    / "QTT_PR_Blueprints_Index_PR83_to_PR224_v1_0.json"
)
CANONICAL_BUNDLE_JSONL = pr94_gate.CANONICAL_BUNDLE_JSONL
CANONICAL_BUNDLE_SHA256 = pr94_gate.CANONICAL_BUNDLE_SHA256
MASTER_PLAN_CURRENT = pr94_gate.MASTER_PLAN_CURRENT

MENU_SCHEMA_ID = "QTT_OWNER_DASHBOARD_APPROVAL_MENU_SCHEMA"
MENU_CONTRACT_ID = "QTT_OWNER_DASHBOARD_APPROVAL_MENU_SCHEMA_V1"
REPORT_ID = "QTT_OWNER_DASHBOARD_APPROVAL_MENU_SCHEMA_REPORT"
POLICY_VERSION = "v1"
ROADMAP_PR_LABEL = "PR #95"
GITHUB_PR_NUMBER_POLICY = "may differ"
SEMANTIC_TASK_ID = "ROADMAP-OWNER-DASHBOARD-MENU-SCHEMA"
BLUEPRINT_SEMANTIC_TASK_ID = "ROADMAP-OWNER-DASHBOARD-APPROVAL-MENU-SCHEMA"
TARGET_BRANCH = "pr95-owner-dashboard-approval-menu-schema"
EXPECTED_BASELINE_ANCESTOR = "65eb507"
MENU_SCOPE = "STATIC_OWNER_DASHBOARD_APPROVAL_MENU_SCHEMA_ONLY"
MENU_AUTHORITY_CLASS = (
    "STATIC_OWNER_DASHBOARD_APPROVAL_MENU_METADATA_ONLY_NOT_OWNER_DECISION_"
    "NOT_RECEIPT_NOT_RUNTIME_AUTHORITY"
)
SUCCESS_MARKER = "QTT_OWNER_DASHBOARD_APPROVAL_MENU_SCHEMA_OK"
FAILURE_MARKER = "QTT_OWNER_DASHBOARD_APPROVAL_MENU_SCHEMA_FAILED"
CI_DETACHED_HEAD_MODE_MARKER = pr94_gate.CI_DETACHED_HEAD_MODE_MARKER
CI_SHALLOW_FETCH_ANCESTRY_SKIP_MARKER = pr94_gate.CI_SHALLOW_FETCH_ANCESTRY_SKIP_MARKER
DOWNSTREAM_ROADMAP_BRANCH_VALIDATION_MODE_MARKER = (
    pr94_gate.DOWNSTREAM_ROADMAP_BRANCH_VALIDATION_MODE_MARKER
)

CANONICAL_OPTION_ORDER = (
    "APPROVE",
    "APPROVE_WITH_OVERRIDE",
    "REJECT",
    "REQUEST_MORE_INFO",
    "WAIVE_REQUIREMENT",
    "SET_OWNER_APPROVED_VALUE",
    "APPROVE_RESEARCH_ONLY",
    "APPROVE_REPLAY_PAPER",
    "APPROVE_OPTIMIZER",
    "APPROVE_RUNTIME",
    "APPROVE_LIVE_USE",
    "APPROVE_QUANTUM_BACKEND",
    "APPLY_TO_ONE_ROW",
    "APPLY_TO_PARAMETER_FAMILY",
    "APPLY_TO_AGENT",
    "APPLY_GLOBALLY",
)
REQUIRED_PROMPT_CONCEPT_ORDER = (
    "APPROVE",
    "APPROVE_WITH_OVERRIDE",
    "REJECT",
    "REQUEST_MORE_INFO",
    "WAIVE_REQUIREMENT",
    "SET_OWNER_APPROVED_VALUE",
    "APPROVE_RESEARCH_ONLY",
    "APPROVE_REPLAY_PAPER",
    "APPROVE_OPTIMIZER",
    "APPROVE_RUNTIME",
    "APPROVE_LIVE_USE",
    "APPROVE_QUANTUM_BACKEND",
    "APPLY_TO_ROW",
    "APPLY_TO_FAMILY",
    "APPLY_TO_AGENT",
    "APPLY_GLOBALLY",
)
OPTION_CLASS_ORDER = (
    "DECISION_OPTIONS",
    "REQUIREMENT_AND_VALUE_OPTIONS",
    "MODE_OR_SCOPE_APPROVAL_OPTIONS",
    "TARGET_SCOPE_OPTIONS",
)
OPTION_CLASS_BY_ID = {
    "APPROVE": "DECISION_OPTIONS",
    "APPROVE_WITH_OVERRIDE": "DECISION_OPTIONS",
    "REJECT": "DECISION_OPTIONS",
    "REQUEST_MORE_INFO": "DECISION_OPTIONS",
    "WAIVE_REQUIREMENT": "REQUIREMENT_AND_VALUE_OPTIONS",
    "SET_OWNER_APPROVED_VALUE": "REQUIREMENT_AND_VALUE_OPTIONS",
    "APPROVE_RESEARCH_ONLY": "MODE_OR_SCOPE_APPROVAL_OPTIONS",
    "APPROVE_REPLAY_PAPER": "MODE_OR_SCOPE_APPROVAL_OPTIONS",
    "APPROVE_OPTIMIZER": "MODE_OR_SCOPE_APPROVAL_OPTIONS",
    "APPROVE_RUNTIME": "MODE_OR_SCOPE_APPROVAL_OPTIONS",
    "APPROVE_LIVE_USE": "MODE_OR_SCOPE_APPROVAL_OPTIONS",
    "APPROVE_QUANTUM_BACKEND": "MODE_OR_SCOPE_APPROVAL_OPTIONS",
    "APPLY_TO_ONE_ROW": "TARGET_SCOPE_OPTIONS",
    "APPLY_TO_PARAMETER_FAMILY": "TARGET_SCOPE_OPTIONS",
    "APPLY_TO_AGENT": "TARGET_SCOPE_OPTIONS",
    "APPLY_GLOBALLY": "TARGET_SCOPE_OPTIONS",
}
PROMPT_CONCEPT_TO_OPTION_ID = {
    "APPROVE": "APPROVE",
    "APPROVE_WITH_OVERRIDE": "APPROVE_WITH_OVERRIDE",
    "REJECT": "REJECT",
    "REQUEST_MORE_INFO": "REQUEST_MORE_INFO",
    "WAIVE_REQUIREMENT": "WAIVE_REQUIREMENT",
    "SET_OWNER_APPROVED_VALUE": "SET_OWNER_APPROVED_VALUE",
    "APPROVE_RESEARCH_ONLY": "APPROVE_RESEARCH_ONLY",
    "APPROVE_REPLAY_PAPER": "APPROVE_REPLAY_PAPER",
    "APPROVE_OPTIMIZER": "APPROVE_OPTIMIZER",
    "APPROVE_RUNTIME": "APPROVE_RUNTIME",
    "APPROVE_LIVE_USE": "APPROVE_LIVE_USE",
    "APPROVE_QUANTUM_BACKEND": "APPROVE_QUANTUM_BACKEND",
    "APPLY_TO_ROW": "APPLY_TO_ONE_ROW",
    "APPLY_TO_FAMILY": "APPLY_TO_PARAMETER_FAMILY",
    "APPLY_TO_AGENT": "APPLY_TO_AGENT",
    "APPLY_GLOBALLY": "APPLY_GLOBALLY",
}
CANONICAL_SCOPE_SUBSTITUTIONS = {
    "APPLY_TO_ROW": "APPLY_TO_ONE_ROW",
    "APPLY_TO_FAMILY": "APPLY_TO_PARAMETER_FAMILY",
}
EXPECTED_SCOPE_CLASSES = {
    "APPLY_TO_ONE_ROW": ("ROW",),
    "APPLY_TO_PARAMETER_FAMILY": ("PARAMETER_FAMILY",),
    "APPLY_TO_AGENT": ("AGENT",),
    "APPLY_GLOBALLY": ("GLOBAL",),
}
BROADER_SCOPE_CLASSES = ("ROW", "PARAMETER_FAMILY", "AGENT", "GLOBAL")
BLOCKED_EFFECTS = (
    "RUNTIME_EFFECT_CREATION",
    "OWNER_DECISION_EXECUTION",
    "OWNER_APPROVAL_RECEIPT_CREATION",
    "OWNER_OVERRIDE_RECEIPT_CREATION",
    "PR96_STATIC_SCREEN_CONTRACT_CREATION",
    "DASHBOARD_RUNTIME_UI_CREATION",
    "TELEGRAM_RUNTIME_CREATION",
    "LIVE_PROMOTION_CREATION",
    "CANARY_ELIGIBILITY_CREATION",
    "LIVE_AUTHORITY_CREATION",
    "ORDER_AUTHORITY_CREATION",
    "ORDER_SUBMISSION",
    "ORDER_CANCELLATION",
    "ORDER_REDUCTION",
    "ORDER_CLOSE",
    "LIVE_ROUTING",
    "SOURCE_RETRIEVAL",
    "SOURCE_ACCEPTANCE",
    "ACCEPTED_SOURCE_PACKET_CREATION",
    "SOURCE_FACT_CREATION",
    "CONNECTOR_SEMANTIC_BINDING",
    "PRIVATE_STATE_FETCH",
    "RUNTIME_CASH_RECEIPT_CREATION",
    "REPLAY_EXECUTION",
    "PAPER_EXECUTION",
    "REPLAY_PAPER_RESULT_CREATION",
    "OPTIMIZER_EXECUTION",
    "CLASSICAL_OPTIMIZER_EXECUTION",
    "QUANTUM_OPTIMIZER_EXECUTION",
    "QUANTUM_BACKEND_EXECUTION",
    "QUANTUM_SIMULATOR_EXECUTION",
    "QUANTUM_PROVIDER_CALL",
    "PROFIT_EVIDENCE_CREATION",
    "QUANTUM_ADVANTAGE_EVIDENCE_CREATION",
    "LATENCY_SUPERIORITY_CLAIM",
    "EXECUTION_SUPERIORITY_CLAIM",
    "ATOMICROWS_BUNDLE_CREATION",
    "ATOMICROWS_BUNDLE_SHA_CREATION",
    "GLOBAL_MUTATION",
)
FALSE_OPTION_FIELDS = (
    "creates_runtime_effect_flag",
    "creates_receipt_flag",
    "creates_live_authority_flag",
    "creates_order_authority_flag",
    "creates_source_fact_flag",
    "creates_connector_semantic_flag",
    "creates_runtime_cash_flag",
    "creates_replay_paper_result_flag",
    "creates_optimizer_execution_flag",
    "creates_quantum_backend_execution_flag",
    "creates_profit_evidence_flag",
    "creates_quantum_advantage_evidence_flag",
    "creates_global_mutation_flag",
)
NO_AUTHORITY_FLAG_FIELDS = (
    "creates_runtime_dashboard_service",
    "creates_dashboard_runtime_ui",
    "creates_telegram_runtime",
    "creates_pr96_static_screen_contract",
    "executes_owner_decision",
    "creates_owner_approval_receipt",
    "creates_owner_override_receipt",
    "creates_live_promotion",
    "creates_canary_eligibility",
    "creates_live_authority",
    "creates_order_authority",
    "submits_order",
    "cancels_order",
    "reduces_order",
    "closes_order",
    "creates_live_routing",
    "retrieves_source",
    "accepts_source",
    "creates_accepted_source_packet",
    "creates_source_fact",
    "creates_connector_semantic_binding",
    "fetches_private_state",
    "creates_runtime_cash_receipt",
    "executes_replay",
    "executes_paper",
    "creates_replay_paper_result",
    "executes_optimizer",
    "executes_classical_optimizer",
    "executes_quantum_optimizer",
    "executes_quantum_backend",
    "executes_quantum_simulator",
    "calls_quantum_provider",
    "creates_profit_evidence",
    "creates_quantum_advantage_evidence",
    "claims_latency_superiority",
    "claims_execution_superiority",
    "creates_atomicrows_bundle",
    "creates_atomicrows_bundle_sha256",
    "creates_global_mutation",
)
ZERO_COUNT_FIELDS = (
    "owner_decision_execution_count",
    "owner_approval_receipt_created_count",
    "owner_override_receipt_created_count",
    "dashboard_runtime_service_created_count",
    "dashboard_runtime_ui_created_count",
    "telegram_runtime_created_count",
    "pr96_static_screen_contract_created_count",
    "live_promotion_created_count",
    "canary_eligibility_created_count",
    "source_retrieval_count",
    "source_acceptance_count",
    "accepted_source_packet_created_count",
    "connector_binding_created_count",
    "private_state_fetch_count",
    "runtime_cash_receipt_created_count",
    "replay_execution_count",
    "paper_execution_count",
    "replay_paper_result_created_count",
    "optimizer_execution_count",
    "classical_optimizer_execution_count",
    "quantum_optimizer_execution_count",
    "quantum_backend_execution_count",
    "quantum_simulator_execution_count",
    "quantum_provider_call_count",
    "order_submission_count",
    "order_cancellation_count",
    "order_reduction_count",
    "order_close_count",
    "live_routing_count",
    "order_authority_created_count",
    "profit_evidence_created_count",
    "quantum_advantage_evidence_created_count",
    "atomicrows_bundle_jsonl_created_count",
    "atomicrows_bundle_sha256_created_count",
)
REQUIRED_FIXTURE_CASE_IDS = (
    "PASS_PR95_METADATA_VERIFIED",
    "PASS_ALL_REQUIRED_OPTIONS_PRESENT",
    "PASS_CANONICAL_SCOPE_TOKEN_MAPPING_EXPLICIT",
    "PASS_STATIC_NO_EFFECT_FLAGS",
    "PASS_QUANTUM_BACKEND_STATIC_METADATA_ONLY",
    "PASS_LIVE_RUNTIME_ORDER_STATIC_METADATA_ONLY",
    "PASS_PR96_SCREEN_CONTRACT_ABSENT",
    "BLOCK_MISSING_REQUIRED_OPTION",
    "BLOCK_DUPLICATE_OPTION_ID",
    "BLOCK_UNKNOWN_OPTION_ID",
    "BLOCK_EXECUTABLE_RUNTIME_EFFECT",
    "BLOCK_RECEIPT_CREATION_CLAIM",
    "BLOCK_SOURCE_CONNECTOR_RUNTIME_CASH_CLAIM",
    "BLOCK_LIVE_ORDER_AUTHORITY_CLAIM",
    "BLOCK_QUANTUM_BACKEND_EXECUTION_CLAIM",
    "BLOCK_APPLY_GLOBALLY_MUTATION_CLAIM",
    "BLOCK_ATOMICROWS_BUNDLE_HASH_CLAIM",
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
    text = path.read_text(encoding="utf-8")
    try:
        value = json.loads(text)
    except json.JSONDecodeError:
        value = pr94_gate.load_yaml(path)
    if not isinstance(value, dict):
        raise ValueError(f"registry root must be an object: {path}")
    return value


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
    except (json.JSONDecodeError, ValueError) as exc:
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


def _downstream_validation_branch_allowed(branch: str) -> bool:
    match = re.match(r"pr(?P<number>[0-9]+)-", branch)
    if not match:
        return False
    return int(match.group("number")) > 95


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


def validate_pr95_roadmap_metadata(repo_root: pathlib.Path) -> tuple[list[str], dict[str, Any]]:
    failures: list[str] = []
    info_lines: list[str] = []
    github_actions = _github_actions_active()
    roadmap = load_json(_resolve(repo_root, ROADMAP_INDEX))
    blueprint = load_json(_resolve(repo_root, BLUEPRINT_INDEX))
    roadmap_entries = _list_of_mappings(roadmap.get("pr_entries"))
    blueprint_entries = _list_of_mappings(blueprint.get("entries"))
    roadmap_entry = next((item for item in roadmap_entries if item.get("number") == 95), None)
    blueprint_entry = next((item for item in blueprint_entries if item.get("number") == 95), None)
    if roadmap_entry is None:
        failures.append("PR95 roadmap index entry missing")
        roadmap_entry = {}
    if blueprint_entry is None:
        failures.append("PR95 blueprint index entry missing")
        blueprint_entry = {}

    checks = (
        ("roadmap.delivery_label", roadmap_entry.get("delivery_label"), ROADMAP_PR_LABEL),
        ("roadmap.title", roadmap_entry.get("title"), "Owner dashboard approval menu schema"),
        ("roadmap.branch", roadmap_entry.get("branch"), TARGET_BRANCH),
        ("roadmap.marker", roadmap_entry.get("marker"), SUCCESS_MARKER),
        ("blueprint.delivery_label", blueprint_entry.get("delivery_label"), ROADMAP_PR_LABEL),
        ("blueprint.title", blueprint_entry.get("title"), "Owner dashboard approval menu schema"),
        ("blueprint.branch", blueprint_entry.get("branch"), TARGET_BRANCH),
        ("blueprint.validator_marker", blueprint_entry.get("validator_marker"), SUCCESS_MARKER),
        ("blueprint.category", blueprint_entry.get("category"), "STATIC"),
        ("blueprint.stage", blueprint_entry.get("stage"), "Owner approval foundation"),
        ("blueprint.priority", blueprint_entry.get("priority"), "S1 launch-essential static"),
    )
    for label, actual, expected in checks:
        if actual != expected:
            failures.append(f"{label} must be {expected}, got {actual}")

    branch_rc, branch, branch_err = _git_stdout(repo_root, ["branch", "--show-current"])
    if branch_rc != 0:
        if github_actions:
            info_lines.append(CI_DETACHED_HEAD_MODE_MARKER)
        else:
            failures.append(f"git branch check failed: {branch_err}")
    elif branch != TARGET_BRANCH:
        if github_actions:
            info_lines.append(CI_DETACHED_HEAD_MODE_MARKER)
        elif _downstream_validation_branch_allowed(branch):
            info_lines.append(DOWNSTREAM_ROADMAP_BRANCH_VALIDATION_MODE_MARKER)
        else:
            failures.append(f"current branch must be {TARGET_BRANCH}, got {branch}")

    head_rc, head, head_err = _git_stdout(repo_root, ["rev-parse", "--short", "HEAD"])
    if head_rc != 0:
        failures.append(f"git HEAD check failed: {head_err}")
    baseline_rc, _, baseline_err = _git_stdout(
        repo_root, ["cat-file", "-e", f"{EXPECTED_BASELINE_ANCESTOR}^{{commit}}"]
    )
    if github_actions and baseline_rc != 0:
        info_lines.append(CI_SHALLOW_FETCH_ANCESTRY_SKIP_MARKER)
    elif baseline_rc != 0:
        failures.append(f"baseline commit missing: {EXPECTED_BASELINE_ANCESTOR}: {baseline_err}")
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
        "semantic_task_id_source": "owner prompt semantic task controls",
        "blueprint_semantic_task_id": blueprint_entry.get("semantic_task_id"),
        "blueprint_semantic_task_id_source": BLUEPRINT_INDEX.as_posix(),
        "blueprint_semantic_task_id_expected_by_blueprint": BLUEPRINT_SEMANTIC_TASK_ID,
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


def _duplicate_values(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for value in values:
        if value in seen:
            duplicates.add(value)
        seen.add(value)
    return sorted(duplicates)


def _option_by_id(registry: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(option.get("option_id")): option
        for option in _list_of_mappings(registry.get("menu_options"))
    }


def validate_mapping_payload(registry: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    mappings = _list_of_mappings(registry.get("prompt_concept_to_option_id_map"))
    prompt_ids = [str(item.get("prompt_concept_id")) for item in mappings]
    option_ids = [str(item.get("option_id")) for item in mappings]
    if prompt_ids != list(REQUIRED_PROMPT_CONCEPT_ORDER):
        failures.append("prompt_concept_to_option_id_map order must match required prompt concepts")
    if option_ids != list(CANONICAL_OPTION_ORDER):
        failures.append("prompt_concept_to_option_id_map option order must match canonical options")
    if _duplicate_values(prompt_ids):
        failures.append("duplicate prompt concept mapping found")
    if _duplicate_values(option_ids):
        failures.append("duplicate option mapping found")
    for item in mappings:
        prompt_id = str(item.get("prompt_concept_id"))
        option_id = str(item.get("option_id"))
        expected_option_id = PROMPT_CONCEPT_TO_OPTION_ID.get(prompt_id)
        if expected_option_id != option_id:
            failures.append(f"mapping for {prompt_id} must target {expected_option_id}, got {option_id}")
        expected_policy = (
            "EXPLICIT_EXISTING_CANONICAL_ENUM_STRONGER_NAME"
            if prompt_id in CANONICAL_SCOPE_SUBSTITUTIONS
            else "EXACT_PROMPT_TOKEN"
        )
        if item.get("mapping_policy") != expected_policy:
            failures.append(f"mapping policy for {prompt_id} must be {expected_policy}")
        if prompt_id != option_id and item.get("mapping_policy") != (
            "EXPLICIT_EXISTING_CANONICAL_ENUM_STRONGER_NAME"
        ):
            failures.append(f"non-identical mapping for {prompt_id} is a silent alias")
    return failures


def validate_registry_payload(
    registry: dict[str, Any],
    *,
    repo_root: pathlib.Path,
) -> list[str]:
    failures: list[str] = []
    if registry.get("owner_dashboard_approval_menu_schema_id") != MENU_SCHEMA_ID:
        failures.append("registry menu schema id mismatch")
    if registry.get("owner_dashboard_approval_menu_contract_id") != MENU_CONTRACT_ID:
        failures.append("registry menu contract id mismatch")
    if registry.get("semantic_task_id") != SEMANTIC_TASK_ID:
        failures.append(f"registry semantic_task_id must be {SEMANTIC_TASK_ID}")
    if registry.get("menu_scope") != MENU_SCOPE:
        failures.append("registry menu_scope mismatch")
    if registry.get("menu_authority_class") != MENU_AUTHORITY_CLASS:
        failures.append("registry menu_authority_class mismatch")
    for flag in ("static_only_flag", "metadata_only_flag", "synthetic_fixture_only_flag"):
        if registry.get(flag) is not True:
            failures.append(f"registry {flag} must be true")
    if registry.get("final_ready") is not False:
        failures.append("registry final_ready must be false")
    if registry.get("canonical_option_order") != list(CANONICAL_OPTION_ORDER):
        failures.append("canonical_option_order must match PR95 deterministic order")
    if registry.get("required_prompt_concept_order") != list(REQUIRED_PROMPT_CONCEPT_ORDER):
        failures.append("required_prompt_concept_order must match owner prompt concepts")
    if registry.get("option_class_order") != list(OPTION_CLASS_ORDER):
        failures.append("option_class_order must match deterministic class order")
    failures.extend(validate_mapping_payload(registry))

    no_authority_flags = registry.get("no_authority_flags", {})
    if not isinstance(no_authority_flags, dict):
        failures.append("no_authority_flags must be an object")
    else:
        for field in NO_AUTHORITY_FLAG_FIELDS:
            if no_authority_flags.get(field) is not False:
                failures.append(f"no_authority_flags.{field} must be false")
    if registry.get("blocked_effects_catalog") != list(BLOCKED_EFFECTS):
        failures.append("blocked_effects_catalog must match canonical blocked effects")

    options = _list_of_mappings(registry.get("menu_options"))
    option_ids = [str(option.get("option_id")) for option in options]
    if option_ids != list(CANONICAL_OPTION_ORDER):
        failures.append("menu_options option_id order must match canonical_option_order")
    duplicates = _duplicate_values(option_ids)
    if duplicates:
        failures.append(f"duplicate option_id values: {', '.join(duplicates)}")
    unknown = sorted(set(option_ids) - set(CANONICAL_OPTION_ORDER))
    if unknown:
        failures.append(f"unknown option_id values: {', '.join(unknown)}")
    missing = [option_id for option_id in CANONICAL_OPTION_ORDER if option_id not in option_ids]
    if missing:
        failures.append(f"missing required option_id values: {', '.join(missing)}")

    for index, option in enumerate(options, start=1):
        option_id = str(option.get("option_id"))
        expected_index = index * 10
        if option.get("canonical_sort_index") != expected_index:
            failures.append(f"{option_id} canonical_sort_index must be {expected_index}")
        expected_class = OPTION_CLASS_BY_ID.get(option_id)
        if option.get("option_class") != expected_class:
            failures.append(f"{option_id} option_class must be {expected_class}")
        expected_prompt = next(
            (
                prompt_id
                for prompt_id, mapped_id in PROMPT_CONCEPT_TO_OPTION_ID.items()
                if mapped_id == option_id
            ),
            None,
        )
        if option.get("prompt_concept_id") != expected_prompt:
            failures.append(f"{option_id} prompt_concept_id must be {expected_prompt}")
        for field in FALSE_OPTION_FIELDS:
            if option.get(field) is not False:
                failures.append(f"{option_id} {field} must be false")
        if option.get("handoff_only_flag") is not True:
            failures.append(f"{option_id} handoff_only_flag must be true")
        if option.get("requires_owner_identity_flag") is not True:
            failures.append(f"{option_id} requires owner identity")
        if option.get("blocked_effects") != list(BLOCKED_EFFECTS):
            failures.append(f"{option_id} blocked_effects must match canonical blocked effects")
        expected_scopes = EXPECTED_SCOPE_CLASSES.get(option_id, BROADER_SCOPE_CLASSES)
        if tuple(option.get("allowed_target_scope_classes", [])) != expected_scopes:
            failures.append(f"{option_id} allowed target scopes must be {expected_scopes}")

    by_id = _option_by_id(registry)
    quantum = by_id.get("APPROVE_QUANTUM_BACKEND", {})
    for effect in ("QUANTUM_BACKEND_EXECUTION", "QUANTUM_SIMULATOR_EXECUTION", "QUANTUM_PROVIDER_CALL"):
        if effect not in quantum.get("blocked_effects", []):
            failures.append(f"APPROVE_QUANTUM_BACKEND must block {effect}")
    live = by_id.get("APPROVE_LIVE_USE", {})
    for effect in ("LIVE_AUTHORITY_CREATION", "CANARY_ELIGIBILITY_CREATION", "ORDER_SUBMISSION", "LIVE_ROUTING"):
        if effect not in live.get("blocked_effects", []):
            failures.append(f"APPROVE_LIVE_USE must block {effect}")
    apply_globally = by_id.get("APPLY_GLOBALLY", {})
    if apply_globally.get("creates_global_mutation_flag") is not False:
        failures.append("APPLY_GLOBALLY creates_global_mutation_flag must be false")
    if "GLOBAL_MUTATION" not in apply_globally.get("blocked_effects", []):
        failures.append("APPLY_GLOBALLY must block GLOBAL_MUTATION")
    if by_id.get("SET_OWNER_APPROVED_VALUE", {}).get("requires_owner_approved_value_flag") is not True:
        failures.append("SET_OWNER_APPROVED_VALUE must require owner approved value")
    if by_id.get("APPROVE_WITH_OVERRIDE", {}).get("authority_class") != (
        "OWNER_MENU_OVERRIDE_METADATA_ONLY_INTERNAL_QTT_WORKFLOW_NOT_EXTERNAL_FACT"
    ):
        failures.append("APPROVE_WITH_OVERRIDE authority class must be internal workflow only")
    for option_id in ("WAIVE_REQUIREMENT", "SET_OWNER_APPROVED_VALUE"):
        if by_id.get(option_id, {}).get("authority_class") != (
            "OWNER_MENU_REQUIREMENT_VALUE_METADATA_ONLY_INTERNAL_POLICY_NOT_RECEIPT"
        ):
            failures.append(f"{option_id} must be internal-policy metadata only")

    future_consumers = _list_of_mappings(registry.get("future_consumers"))
    if not any(item.get("consumer_id") == "PR96_OWNER_DASHBOARD_APPROVAL_STATIC_SCREEN_CONTRACT" for item in future_consumers):
        failures.append("future_consumers must include PR96 static screen contract")
    for consumer in future_consumers:
        if consumer.get("pr95_creates_consumer_execution") is not False:
            failures.append(f"{consumer.get('consumer_id')} pr95_creates_consumer_execution must be false")

    failures.extend(validate_filesystem_boundaries(repo_root))
    return failures


def validate_fixture_payload(fixture: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    expected = {
        "fixture_id": "SYNTHETIC_PR95_QTT_OWNER_DASHBOARD_APPROVAL_MENU_SCHEMA_FIXTURE",
        "fixture_version": "PR95_QTT_OWNER_DASHBOARD_APPROVAL_MENU_SCHEMA_FIXTURE_V1",
        "mode": "SOURCE_REQUIRED",
        "execution": "DISABLED",
        "registry_ref": DEFAULT_PRODUCTION_REGISTRY.as_posix(),
        "schema_ref": DEFAULT_SCHEMA.as_posix(),
    }
    for field, expected_value in expected.items():
        if fixture.get(field) != expected_value:
            failures.append(f"fixture {field} must be {expected_value}")
    if fixture.get("deterministic_output") is not True:
        failures.append("fixture deterministic_output must be true")
    if fixture.get("required_prompt_concept_ids") != list(REQUIRED_PROMPT_CONCEPT_ORDER):
        failures.append("fixture required_prompt_concept_ids mismatch")
    if fixture.get("canonical_option_ids") != list(CANONICAL_OPTION_ORDER):
        failures.append("fixture canonical_option_ids mismatch")
    mappings = _list_of_mappings(fixture.get("canonical_scope_token_mapping"))
    expected_scope_mappings = [
        {
            "prompt_concept_id": prompt_id,
            "option_id": option_id,
            "mapping_policy": "EXPLICIT_EXISTING_CANONICAL_ENUM_STRONGER_NAME",
        }
        for prompt_id, option_id in CANONICAL_SCOPE_SUBSTITUTIONS.items()
    ]
    if mappings != expected_scope_mappings:
        failures.append("fixture canonical scope token mapping mismatch")
    cases = _list_of_mappings(fixture.get("fixture_cases"))
    case_ids = [str(case.get("case_id")) for case in cases]
    missing_cases = [case_id for case_id in REQUIRED_FIXTURE_CASE_IDS if case_id not in case_ids]
    if missing_cases:
        failures.append(f"fixture missing required cases: {', '.join(missing_cases)}")
    if _duplicate_values(case_ids):
        failures.append("fixture case ids must not contain duplicates")
    no_claim_flags = fixture.get("no_claim_flags", {})
    if not isinstance(no_claim_flags, dict):
        failures.append("fixture no_claim_flags must be an object")
    else:
        for field in NO_AUTHORITY_FLAG_FIELDS:
            if no_claim_flags.get(field) is not False:
                failures.append(f"fixture no_claim_flags.{field} must be false")
    return failures


def build_case_packet(case: dict[str, Any], registry: dict[str, Any]) -> dict[str, Any]:
    case_id = str(case.get("case_id"))
    expected_valid = int(case.get("expected_valid_menu_option_count", 0))
    expected_reason = str(case.get("expected_reason_code"))
    blocked = case_id.startswith("BLOCK_")
    return {
        "fixture_case_id": case_id,
        "case_authority_class": "STATIC_FIXTURE_CASE_ONLY_NO_RUNTIME_EFFECT",
        "valid_menu_option_count": 0 if blocked else len(_list_of_mappings(registry.get("menu_options"))),
        "blocked_menu_option_count": 1 if blocked else 0,
        "expected_valid_menu_option_count": expected_valid,
        "menu_reason_codes": [] if blocked else [expected_reason],
        "blocked_reason_codes": [expected_reason] if blocked else [],
        "owner_decision_execution_count": 0,
        "owner_approval_receipt_created_count": 0,
        "owner_override_receipt_created_count": 0,
        "dashboard_runtime_service_created_count": 0,
        "pr96_static_screen_contract_created_count": 0,
        "source_retrieval_count": 0,
        "connector_binding_created_count": 0,
        "runtime_cash_receipt_created_count": 0,
        "order_submission_count": 0,
        "quantum_backend_execution_count": 0,
        "quantum_simulator_execution_count": 0,
        "profit_evidence_created_count": 0,
        "atomicrows_bundle_jsonl_created_count": 0,
        "atomicrows_bundle_sha256_created_count": 0,
    }


def validate_case_packets(case_packets: list[dict[str, Any]], fixture: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    packets = {packet.get("fixture_case_id"): packet for packet in case_packets}
    for case in _list_of_mappings(fixture.get("fixture_cases")):
        case_id = str(case.get("case_id"))
        packet = packets.get(case_id)
        if packet is None:
            failures.append(f"case packet missing: {case_id}")
            continue
        if packet.get("valid_menu_option_count") != case.get("expected_valid_menu_option_count"):
            failures.append(f"case {case_id} valid_menu_option_count mismatch")
        expected_reason = str(case.get("expected_reason_code"))
        all_reasons = set(packet.get("menu_reason_codes", [])) | set(packet.get("blocked_reason_codes", []))
        if expected_reason not in all_reasons:
            failures.append(f"case {case_id} missing expected reason {expected_reason}")
        for field in ZERO_COUNT_FIELDS:
            if packet.get(field, 0) != 0:
                failures.append(f"case {case_id} {field} must be 0")
    return failures


def validate_upstream_reports(repo_root: pathlib.Path) -> tuple[list[str], dict[str, Any]]:
    failures: list[str] = []
    upstream: dict[str, Any] = {}
    pr94_report_path = _resolve(repo_root, pr94_gate.DEFAULT_REPORT)
    try:
        pr94_report = load_json(pr94_report_path)
    except FileNotFoundError:
        failures.append(f"PR94 report missing: {pr94_gate.DEFAULT_REPORT.as_posix()}")
        pr94_report = {}
    except (json.JSONDecodeError, ValueError) as exc:
        failures.append(f"PR94 report invalid: {pr94_gate.DEFAULT_REPORT.as_posix()}: {exc}")
        pr94_report = {}
    if pr94_report and pr94_report.get("validation_marker") != pr94_gate.SUCCESS_MARKER:
        failures.append("PR94 report validation marker mismatch")
    upstream["pr94_report"] = pr94_report
    return failures, upstream


def validate_filesystem_boundaries(repo_root: pathlib.Path) -> list[str]:
    failures: list[str] = []
    if _resolve(repo_root, CANONICAL_BUNDLE_JSONL).exists():
        failures.append(
            "OWNER_DASHBOARD_APPROVAL_MENU_BLOCKED_ATOMICROWS_BUNDLE: "
            f"{CANONICAL_BUNDLE_JSONL.as_posix()} must be absent"
        )
    if _resolve(repo_root, CANONICAL_BUNDLE_SHA256).exists():
        failures.append(
            "OWNER_DASHBOARD_APPROVAL_MENU_BLOCKED_ATOMICROWS_SHA: "
            f"{CANONICAL_BUNDLE_SHA256.as_posix()} must be absent"
        )
    forbidden_paths = (
        pathlib.Path("schemas/governance/qtt_owner_dashboard_approval_static_screen_contract.schema.json"),
        pathlib.Path("schemas/owner/owner_dashboard_approval_static_screen_contract.schema.json"),
        pathlib.Path("docs/master_plan/governance/QTTOwnerDashboardApprovalStaticScreenContract.yaml"),
        pathlib.Path("docs/master_plan/owner/OwnerDashboardApprovalStaticScreenContract.yaml"),
        pathlib.Path("docs/master_plan/generated/OwnerDashboardApprovalStaticScreenContract.report.json"),
        pathlib.Path("tools/validate_owner_dashboard_approval_static_screen_contract.py"),
        pathlib.Path("tests/governance/test_owner_dashboard_approval_static_screen_contract.py"),
        pathlib.Path("tests/owner/test_owner_dashboard_approval_static_screen_contract.py"),
        pathlib.Path("src/qtt/dashboard_runtime"),
        pathlib.Path("src/qtt/telegram_runtime"),
        pathlib.Path("src/qtt/owner_dashboard_runtime"),
    )
    for path in forbidden_paths:
        if _resolve(repo_root, path).exists():
            failures.append(f"PR95 must not create forbidden later/runtime artifact: {path.as_posix()}")
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
            "OWNER_DASHBOARD_APPROVAL_MENU_BLOCKED_MASTER_PLAN_EDIT: "
            f"{MASTER_PLAN_CURRENT.as_posix()} has local diff"
        ]
    return [f"git diff check failed for {MASTER_PLAN_CURRENT.as_posix()}: {completed.stderr.strip()}"]


def validate_validator_static_surface(validator_path: pathlib.Path) -> list[str]:
    return pr94_gate.validate_validator_static_surface(validator_path)


def build_menu_packet(registry: dict[str, Any]) -> dict[str, Any]:
    options = _list_of_mappings(registry.get("menu_options"))
    option_class_mapping = {
        str(option.get("option_id")): option.get("option_class")
        for option in options
    }
    scope_mapping = {
        str(option.get("option_id")): option.get("allowed_target_scope_classes")
        for option in options
    }
    packet: dict[str, Any] = {
        "owner_dashboard_approval_menu_schema_id": registry.get(
            "owner_dashboard_approval_menu_schema_id"
        ),
        "owner_dashboard_approval_menu_contract_id": registry.get(
            "owner_dashboard_approval_menu_contract_id"
        ),
        "menu_scope": registry.get("menu_scope"),
        "menu_authority_class": registry.get("menu_authority_class"),
        "menu_option_count": len(options),
        "canonical_option_order": [option.get("option_id") for option in options],
        "required_prompt_concept_order": list(REQUIRED_PROMPT_CONCEPT_ORDER),
        "option_class_mapping": option_class_mapping,
        "scope_class_mapping": scope_mapping,
        "prompt_concept_to_option_id_map": copy.deepcopy(
            registry.get("prompt_concept_to_option_id_map")
        ),
        "canonical_scope_substitution_policy": {
            prompt_id: {
                "option_id": option_id,
                "mapping_policy": "EXPLICIT_EXISTING_CANONICAL_ENUM_STRONGER_NAME",
                "silent_aliasing": False,
            }
            for prompt_id, option_id in CANONICAL_SCOPE_SUBSTITUTIONS.items()
        },
        "static_only_flag": True,
        "metadata_only_flag": True,
        "synthetic_fixture_only_flag": True,
        "handoff_only_flag": True,
        "unknown_option_id_count": 0,
        "duplicate_option_id_count": 0,
        "silent_alias_count": 0,
        "allowed_target_scope_classes_by_option": scope_mapping,
        "blocked_effects": list(BLOCKED_EFFECTS),
        "menu_options": copy.deepcopy(options),
    }
    for field in NO_AUTHORITY_FLAG_FIELDS:
        packet[field] = False
    for field in ZERO_COUNT_FIELDS:
        packet[field] = 0
    return packet


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
        "blueprint_semantic_task_id": metadata.get("blueprint_semantic_task_id"),
        "blueprint_semantic_task_id_source": metadata.get("blueprint_semantic_task_id_source"),
        "validator_marker_source": metadata.get("validator_marker_source"),
        "owner_dashboard_approval_menu_schema_packet": copy.deepcopy(packet),
        "fixture_case_packets": copy.deepcopy(case_packets),
        "upstream_pr94_report_marker": upstream.get("pr94_report", {}).get("validation_marker"),
        "upstream_owner_override_receipt_authoring_gate_ref": copy.deepcopy(
            registry.get("upstream_owner_override_receipt_authoring_gate_ref")
        ),
        "upstream_owner_approval_request_queue_registry_ref": copy.deepcopy(
            registry.get("upstream_owner_approval_request_queue_registry_ref")
        ),
        "master_plan_principles_consumed": copy.deepcopy(
            registry.get("master_plan_principles_consumed")
        ),
        "menu_option_count": packet.get("menu_option_count"),
        "required_prompt_concept_count": len(REQUIRED_PROMPT_CONCEPT_ORDER),
        "canonical_option_count": len(CANONICAL_OPTION_ORDER),
        "canonical_scope_substitution_count": len(CANONICAL_SCOPE_SUBSTITUTIONS),
        "static_only_flag": True,
        "metadata_only_flag": True,
        "deterministic_output": True,
        "schema_validated": True,
        "registry_validated": True,
        "fixture_validated": True,
        "atomicrows_bundle_jsonl_exists": False,
        "atomicrows_bundle_sha256_exists": False,
        "master_plan_diff_empty": True,
        "final_ready": False,
        "remaining_boundary": (
            "PR95 creates no runtime, live, trading, profit, latency, backend, "
            "quantum-advantage, dashboard-runtime, receipt, source, connector, "
            "runtime-cash, replay/paper, optimizer, order, or AtomicRows authority."
        ),
    }
    for field in NO_AUTHORITY_FLAG_FIELDS:
        report[field] = False
    for field in ZERO_COUNT_FIELDS:
        report[field] = 0
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

    metadata_failures, metadata = validate_pr95_roadmap_metadata(repo_root)
    info_lines = tuple(metadata.get("ci_info_lines", ()))
    failures.extend(metadata_failures)
    upstream_failures, upstream = validate_upstream_reports(repo_root)
    failures.extend(upstream_failures)
    failures.extend(schema_subset_failures(registry, schema, "REGISTRY"))
    failures.extend(validate_registry_payload(registry, repo_root=repo_root))
    failures.extend(validate_fixture_payload(fixture))
    packet = build_menu_packet(registry)
    case_packets = [
        build_case_packet(case, registry)
        for case in _list_of_mappings(fixture.get("fixture_cases"))
    ]
    failures.extend(validate_case_packets(case_packets, fixture))
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
