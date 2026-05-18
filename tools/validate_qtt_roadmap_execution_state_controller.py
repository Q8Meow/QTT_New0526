#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
import pathlib
import sys
from typing import Any, Iterable, Mapping, Sequence

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from src.qtt.core.testing import qtt_active_non_sha_day1_gate_state_registry as gate_registry
from tools.validate_master_plan_section_coverage import validate_json_schema_subset


REPO_ROOT = _REPO_ROOT
DEFAULT_CONTROLLER = pathlib.Path(
    "docs/roadmap/QTT_Roadmap_Execution_State_Controller_v1_0.json"
)
DEFAULT_SCHEMA = pathlib.Path(
    "schemas/roadmap/qtt_roadmap_execution_state_controller.schema.json"
)
DEFAULT_ROSTER = pathlib.Path("docs/roadmap/QTT_PR_Identity_Roster_v1_0.json")
DEFAULT_REPORT = pathlib.Path(
    "docs/master_plan/generated/QttRoadmapExecutionStateController.report.json"
)
RUN_VALIDATION_GATES = pathlib.Path("tools/run_validation_gates.py")

SUCCESS_MARKER = "QTT_ROADMAP_EXECUTION_STATE_CONTROLLER_OK"
FAILURE_MARKER = "QTT_ROADMAP_EXECUTION_STATE_CONTROLLER_FAILED"
REPORT_ID = "QTT_ROADMAP_EXECUTION_STATE_CONTROLLER_REPORT"
VALIDATOR_NAME = "validate_qtt_roadmap_execution_state_controller.py"
CONTROLLER_ID = "QTT_ROADMAP_EXECUTION_STATE_CONTROLLER_V1_0"
ROSTER_ID = "QTT_PR_IDENTITY_ROSTER_V1_0"

ROSTER_PATH = "docs/roadmap/QTT_PR_Identity_Roster_v1_0.json"
ACTIVE_GATE_REGISTRY_PATH = (
    "docs/master_plan/launch/QttActiveNonShaDay1GateStateRegistryContract.yaml"
)
FINAL_READINESS_POLICY_PATH = (
    "docs/master_plan/launch/QttFinalReadinessDependencyPolicyContract.yaml"
)
UPSTREAM_MARKERS = (
    "QTT_PR_IDENTITY_ROSTER_OK",
    "QTT_ACTIVE_NON_SHA_DAY1_GATE_STATE_REGISTRY_OK",
    "QTT_FINAL_READINESS_DEPENDENCY_POLICY_OK",
)
REQUIRED_UPSTREAM_PATHS = (
    ROSTER_PATH,
    ACTIVE_GATE_REGISTRY_PATH,
    FINAL_READINESS_POLICY_PATH,
)

CONTROLLED_STATES = (
    "ROADMAP_EXECUTION_STATE_CONTROLLER_ESTABLISHED",
    "STATIC_FOUNDATION_STATE_REFERENCED_BY_CONTROLLER",
    "CONTROL_PLANE_STATE_REFERENCED_BY_CONTROLLER",
    "SOURCE_EVIDENCE_STATE_CONTROLLED_BY_ACCEPTED_SOURCE_WORKFLOW",
    "CONNECTOR_SEMANTIC_STATE_CONTROLLED_BY_BINDING_LEDGER",
    "RUNTIME_CASH_STATE_CONTROLLED_BY_RUNTIME_CASH_RECEIPTS",
    "REPLAY_PAPER_STATE_CONTROLLED_BY_RESULT_LEDGER",
    "OWNER_REVIEW_STATE_CONTROLLED_BY_OWNER_RECEIPTS",
    "QUANTUM_FORWARD_OPTIMIZATION_STATE_REFERENCED_BY_CONTROLLER",
    "QUANTUM_BACKEND_STATE_CONTROLLED_BY_ACTIVE_NON_SHA_GATE",
    "FINAL_READINESS_CONTROLLED_BY_ACTIVE_NON_SHA_GATES",
    "LIVE_EXECUTION_STATE_CONTROLLED_BY_OWNER_LAUNCH_AND_EXECUTION_RECEIPTS",
)

NON_MATERIALIZED_CAPABILITIES = (
    "FINAL_READINESS",
    "DAY1_LAUNCH",
    "SOURCE_ACCEPTANCE",
    "CONNECTOR_SEMANTIC_BINDING",
    "RUNTIME_CASH_RECEIPT",
    "REPLAY_EXECUTION",
    "PAPER_EXECUTION",
    "OPTIMIZER_EXECUTION",
    "NEURAL_EXECUTION",
    "QUANTUM_BACKEND_EXECUTION",
    "LIVE_EXECUTION",
    "ORDER_EXECUTION",
    "PROFIT_EVIDENCE",
    "LATENCY_SUPERIORITY_EVIDENCE",
    "EXECUTION_SUPERIORITY_EVIDENCE",
    "QUANTUM_ADVANTAGE_EVIDENCE",
    "ATOMICROWS_BUNDLE_MUTATION",
    "ATOMICROWS_SHA_CREATION",
)

ROADMAP_DOCS = (
    pathlib.Path("docs/roadmap/README.md"),
    pathlib.Path(
        "docs/roadmap/QTT_PRs_Roadmap_Consolidated_Static_Runtime_Live_Stage1_to_Stage5_v1_0.md"
    ),
    pathlib.Path("docs/roadmap/QTT_PRs_Roadmap_Index_v1_0.json"),
    pathlib.Path(
        "docs/roadmap/QTT_PR_Blueprints_Stage1_to_Stage5_PR83_to_PR224_v1_0.md"
    ),
    pathlib.Path("docs/roadmap/QTT_PR_Blueprints_Index_PR83_to_PR224_v1_0.json"),
)

EXPECTED_MAPPING_STATES = {
    "PR #101": "FINAL_READINESS_CONTROLLED_BY_ACTIVE_NON_SHA_GATES",
    "PR #105": "SOURCE_EVIDENCE_STATE_CONTROLLED_BY_ACCEPTED_SOURCE_WORKFLOW",
    "PR #106": "SOURCE_EVIDENCE_STATE_CONTROLLED_BY_ACCEPTED_SOURCE_WORKFLOW",
    "PR #107": "SOURCE_EVIDENCE_STATE_CONTROLLED_BY_ACCEPTED_SOURCE_WORKFLOW",
    "PR #108": "CONNECTOR_SEMANTIC_STATE_CONTROLLED_BY_BINDING_LEDGER",
    "PR #111": "RUNTIME_CASH_STATE_CONTROLLED_BY_RUNTIME_CASH_RECEIPTS",
    "PR #112": "RUNTIME_CASH_STATE_CONTROLLED_BY_RUNTIME_CASH_RECEIPTS",
    "PR #118": "REPLAY_PAPER_STATE_CONTROLLED_BY_RESULT_LEDGER",
    "PR #119": "REPLAY_PAPER_STATE_CONTROLLED_BY_RESULT_LEDGER",
    "PR #120": "REPLAY_PAPER_STATE_CONTROLLED_BY_RESULT_LEDGER",
    "PR #121": "REPLAY_PAPER_STATE_CONTROLLED_BY_RESULT_LEDGER",
    "PR #122": "OWNER_REVIEW_STATE_CONTROLLED_BY_OWNER_RECEIPTS",
    "PR #125": "QUANTUM_BACKEND_STATE_CONTROLLED_BY_ACTIVE_NON_SHA_GATE",
    "PR #126": "QUANTUM_FORWARD_OPTIMIZATION_STATE_REFERENCED_BY_CONTROLLER",
}


@dataclass(frozen=True)
class ValidationResult:
    ok: bool
    failures: tuple[str, ...]
    report: dict[str, Any] | None


def _resolve(repo_root: pathlib.Path, path: pathlib.Path | str) -> pathlib.Path:
    concrete = pathlib.Path(path)
    return concrete if concrete.is_absolute() else repo_root / concrete


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


def _mapping_by_label(controller: Mapping[str, Any], label: str) -> dict[str, Any] | None:
    for entry in controller.get("roadmap_range_currentization", []):
        if isinstance(entry, dict) and entry.get("roadmap_pr_label") == label:
            return entry
    return None


def _strings(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from _strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from _strings(item)


def _validate_top_level(controller: Mapping[str, Any]) -> list[str]:
    failures: list[str] = []
    expected = {
        "controller_schema_version": "v1.0",
        "controller_id": CONTROLLER_ID,
        "controller_title": "QTT Roadmap Execution-State Controller v1.0",
        "controller_authority_class": (
            "CONTROL_PLANE_EXECUTION_STATE_CONTROLLER_NOT_RUNTIME_NOT_FINAL_READINESS_AUTHORITY"
        ),
        "created_by_repo_delivery_label": (
            "PR118 — Roadmap execution-state controller and audit currentization"
        ),
        "controller_established_state": "ROADMAP_EXECUTION_STATE_CONTROLLER_ESTABLISHED",
        "generated_report_path": DEFAULT_REPORT.as_posix(),
    }
    for field, expected_value in expected.items():
        if controller.get(field) != expected_value:
            failures.append(f"controller.{field} must be {expected_value!r}")
    return failures


def _validate_upstream_authorities(
    repo_root: pathlib.Path, controller: Mapping[str, Any]
) -> list[str]:
    failures: list[str] = []
    authorities = [
        item for item in controller.get("upstream_authorities", []) if isinstance(item, dict)
    ]
    paths = {item.get("authority_path") for item in authorities}
    markers = {item.get("authority_validation_marker") for item in authorities}
    for path in REQUIRED_UPSTREAM_PATHS:
        if path not in paths:
            failures.append(f"upstream_authorities must reference {path}")
        if not _resolve(repo_root, path).exists():
            failures.append(f"upstream authority path must exist: {path}")
    for marker in UPSTREAM_MARKERS:
        if marker not in markers:
            failures.append(f"upstream_authorities must include marker {marker}")
    return failures


def _validate_identity_translation(controller: Mapping[str, Any]) -> list[str]:
    failures: list[str] = []
    identity = controller.get("identity_translation_authority")
    if not isinstance(identity, dict):
        return ["identity_translation_authority must be an object"]
    expected = {
        "translator_path": ROSTER_PATH,
        "translator_created_by_repo_pr": "PR117",
        "translator_success_marker": "QTT_PR_IDENTITY_ROSTER_OK",
        "repo_canonical_labels_are_implementation_truth": True,
        "blueprint_labels_are_implementation_scope_metadata": True,
        "roadmap_labels_are_orchestration_metadata": True,
        "github_numbers_are_audit_only": True,
        "same_number_identity_inference_forbidden": True,
        "roster_wins_on_identity_conflict": True,
    }
    for field, expected_value in expected.items():
        if identity.get(field) != expected_value:
            failures.append(
                f"identity_translation_authority.{field} must be {expected_value!r}"
            )
    return failures


def _validate_taxonomy(controller: Mapping[str, Any]) -> list[str]:
    failures: list[str] = []
    taxonomy = controller.get("controlled_state_taxonomy")
    if taxonomy != list(CONTROLLED_STATES):
        failures.append("controlled_state_taxonomy must match the required controller states")
    if isinstance(taxonomy, list):
        if taxonomy.count("FINAL_READINESS_CONTROLLED_BY_ACTIVE_NON_SHA_GATES") != 1:
            failures.append("FINAL_READINESS_CONTROLLED_BY_ACTIVE_NON_SHA_GATES must appear exactly once")
        for state in (
            "QUANTUM_FORWARD_OPTIMIZATION_STATE_REFERENCED_BY_CONTROLLER",
            "QUANTUM_BACKEND_STATE_CONTROLLED_BY_ACTIVE_NON_SHA_GATE",
        ):
            if state not in taxonomy:
                failures.append(f"controlled_state_taxonomy missing {state}")
        if len(taxonomy) != len(set(taxonomy)):
            failures.append("controlled_state_taxonomy must not contain duplicates")
    return failures


def _validate_active_bindings(controller: Mapping[str, Any]) -> list[str]:
    failures: list[str] = []
    bindings = controller.get("active_state_bindings")
    if not isinstance(bindings, dict):
        return ["active_state_bindings must be an object"]
    expected = {
        "final_readiness_state": "FINAL_READINESS_CONTROLLED_BY_ACTIVE_NON_SHA_GATES",
        "final_readiness_upstream_registry_path": ACTIVE_GATE_REGISTRY_PATH,
        "final_readiness_dependency_policy_path": FINAL_READINESS_POLICY_PATH,
        "quantum_forward_optimization_state": (
            "QUANTUM_FORWARD_OPTIMIZATION_STATE_REFERENCED_BY_CONTROLLER"
        ),
        "quantum_backend_state": "QUANTUM_BACKEND_STATE_CONTROLLED_BY_ACTIVE_NON_SHA_GATE",
        "quantum_backend_upstream_gate_reference": "QUANTUM_BACKEND_AUTHORITY_GATE",
        "controller_established_state": "ROADMAP_EXECUTION_STATE_CONTROLLER_ESTABLISHED",
        "active_gate_registry_remains_source_of_truth": True,
        "full_active_non_sha_gate_list_duplicated_here": False,
    }
    for field, expected_value in expected.items():
        if bindings.get(field) != expected_value:
            failures.append(f"active_state_bindings.{field} must be {expected_value!r}")
    return failures


def _validate_roster_currentization(roster: Mapping[str, Any]) -> list[str]:
    failures: list[str] = []
    entries = _entries(roster)
    pr117 = _entry_by_id(entries, "PR117_REPO_CANONICAL_SELF_ENTRY")
    pr118 = _entry_by_id(entries, "PR118_REPO_CANONICAL_SELF_ENTRY")
    pr119 = _entry_by_id(entries, "PR119_REPO_CANONICAL_SELF_ENTRY")
    if pr117 is None:
        failures.append("PR117_REPO_CANONICAL_SELF_ENTRY must exist")
    else:
        if pr117.get("github_pr_number") != 117:
            failures.append("PR117_REPO_CANONICAL_SELF_ENTRY github_pr_number must be 117")
        if pr117.get("github_audit_url") != "https://github.com/Q8Meow/QTT_New0526/pull/117":
            failures.append("PR117_REPO_CANONICAL_SELF_ENTRY github_audit_url is not current")
        if pr117.get("roadmap_pr_label") is not None:
            failures.append("PR117_REPO_CANONICAL_SELF_ENTRY roadmap_pr_label must remain null")
        if pr117.get("blueprint_pr_label") is not None:
            failures.append("PR117_REPO_CANONICAL_SELF_ENTRY blueprint_pr_label must remain null")
    if pr118 is None:
        failures.append("PR118_REPO_CANONICAL_SELF_ENTRY must exist")
    else:
        expected = {
            "repo_canonical_pr_label": "PR118",
            "roadmap_pr_label": None,
            "blueprint_pr_label": None,
            "github_pr_number": 118,
            "github_title": "PR118 add roadmap execution-state controller",
            "current_status": "MERGED",
            "github_audit_url": "https://github.com/Q8Meow/QTT_New0526/pull/118",
        }
        for field, expected_value in expected.items():
            if pr118.get(field) != expected_value:
                failures.append(f"PR118_REPO_CANONICAL_SELF_ENTRY {field} must be {expected_value!r}")
    if pr119 is None:
        failures.append("PR119_REPO_CANONICAL_SELF_ENTRY must exist")
    else:
        expected = {
            "repo_canonical_pr_label": "PR119",
            "roadmap_pr_label": None,
            "blueprint_pr_label": None,
            "github_pr_number": 119,
            "github_title": "PR119 currentize identity roster and add controller-approved coverage triage routes",
            "current_status": "MERGED",
            "github_audit_url": "https://github.com/Q8Meow/QTT_New0526/pull/119",
        }
        for field, expected_value in expected.items():
            if pr119.get(field) != expected_value:
                failures.append(f"PR119_REPO_CANONICAL_SELF_ENTRY {field} must be {expected_value!r}")
    return failures


def _validate_roadmap_currentization(controller: Mapping[str, Any]) -> list[str]:
    failures: list[str] = []
    entries = [
        item
        for item in controller.get("roadmap_range_currentization", [])
        if isinstance(item, dict)
    ]
    labels = [entry.get("roadmap_pr_label") for entry in entries]
    expected_labels = [f"PR #{number}" for number in range(101, 127)]
    if labels != expected_labels:
        failures.append("roadmap_range_currentization must contain PR #101 through PR #126 in order")
    if len(labels) != len(set(labels)):
        failures.append("roadmap_range_currentization roadmap_pr_label values must be unique")
    for entry in entries:
        label = entry.get("roadmap_pr_label")
        if entry.get("blueprint_pr_label") != label:
            failures.append(f"{label} blueprint_pr_label must match metadata label")
        if entry.get("state_source") != CONTROLLER_ID:
            failures.append(f"{label} state_source must be {CONTROLLER_ID}")
        if entry.get("identity_source") != ROSTER_ID:
            failures.append(f"{label} identity_source must be {ROSTER_ID}")
        if not entry.get("controller_state"):
            failures.append(f"{label} must include controller_state")
        if not entry.get("next_allowed_action_class"):
            failures.append(f"{label} must include next_allowed_action_class")
        if entry.get("repo_delivery_status") != "ROADMAP_BLUEPRINT_PLANNED_METADATA_ONLY":
            failures.append(f"{label} must remain roadmap/blueprint metadata only")
    for label, expected_state in EXPECTED_MAPPING_STATES.items():
        entry = _mapping_by_label(controller, label)
        if entry is None:
            failures.append(f"missing controller mapping for {label}")
        elif entry.get("controller_state") != expected_state:
            failures.append(f"{label} controller_state must be {expected_state}")
    for number in range(105, 127):
        entry = _mapping_by_label(controller, f"PR #{number}")
        if entry is None:
            failures.append(f"missing controller mapping for PR #{number}")
            continue
        for field in (
            "controller_state",
            "state_source",
            "identity_source",
            "next_allowed_action_class",
        ):
            if not entry.get(field):
                failures.append(f"PR #{number} missing {field}")
    pr118_mapping = _mapping_by_label(controller, "PR #118")
    if pr118_mapping:
        if pr118_mapping.get("roster_entry_id") == "PR118_REPO_CANONICAL_SELF_ENTRY":
            failures.append("controller mapping must not treat repo PR118 as Roadmap PR #118")
        if pr118_mapping.get("title") != "Replay engine executor":
            failures.append("Roadmap/Blueprint PR #118 must remain Replay engine executor")
    if any(entry.get("roster_entry_id") == "PR118_REPO_CANONICAL_SELF_ENTRY" for entry in entries):
        failures.append("roadmap_range_currentization must not use the PR118 repo self-entry")
    return failures


def _validate_capability_and_discipline(controller: Mapping[str, Any]) -> list[str]:
    failures: list[str] = []
    envelope = controller.get("capability_envelope")
    if not isinstance(envelope, dict):
        failures.append("capability_envelope must be an object")
    else:
        expected = {
            "materialized_capability_this_pr": CONTROLLER_ID,
            "state_transition_this_pr": "ROADMAP_EXECUTION_STATE_CONTROLLER_ESTABLISHED",
            "metadata_currentization_allowed": True,
            "roadmap_blueprint_reference_note_allowed": True,
            "downstream_functional_implementation_allowed_this_pr": False,
        }
        for field, expected_value in expected.items():
            if envelope.get(field) != expected_value:
                failures.append(f"capability_envelope.{field} must be {expected_value!r}")
    if controller.get("non_materialized_capability_vector") != list(NON_MATERIALIZED_CAPABILITIES):
        failures.append("non_materialized_capability_vector must match the required centralized vector")

    discipline = controller.get("state_transition_discipline")
    if not isinstance(discipline, dict):
        failures.append("state_transition_discipline must be an object")
    else:
        required_true = (
            "one_state_flip_per_repo_pr",
            "one_artifact_or_capability_per_repo_pr",
            "repo_pr_title_uses_repo_label_only",
            "roadmap_blueprint_labels_are_metadata_only",
            "github_numbers_are_audit_only",
            "same_number_identity_inference_forbidden",
        )
        for field in required_true:
            if discipline.get(field) is not True:
                failures.append(f"state_transition_discipline.{field} must be true")
        if discipline.get("current_pr_state_flip") != "ROADMAP_EXECUTION_STATE_CONTROLLER_ESTABLISHED":
            failures.append("current_pr_state_flip must be ROADMAP_EXECUTION_STATE_CONTROLLER_ESTABLISHED")
        if discipline.get("current_pr_materialized_capability") != CONTROLLER_ID:
            failures.append(f"current_pr_materialized_capability must be {CONTROLLER_ID}")
    return failures


def _validate_invariants(controller: Mapping[str, Any]) -> list[str]:
    failures: list[str] = []
    invariants = controller.get("controller_invariants")
    if not isinstance(invariants, dict):
        return ["controller_invariants must be an object"]
    required_true = (
        "quantum_forward_state_is_preserved",
        "future_quantum_optimization_support_must_route_through_controller",
        "future_qaoa_vqe_qubo_ising_annealing_support_is_controller_referenced",
        "deterministic_selection_ranking_arbitration_future_compatibility_required",
        "active_non_sha_gate_list_source_of_truth_is_pr116a_registry",
        "final_readiness_derives_from_active_non_sha_gate_registry",
        "controller_does_not_redefine_active_non_sha_gates",
        "controller_does_not_duplicate_gate_list_across_downstream_files",
        "roadmap_blueprint_files_reference_controller_instead_of_scattering_state_text",
    )
    for field in required_true:
        if invariants.get(field) is not True:
            failures.append(f"controller_invariants.{field} must be true")
    return failures


def _validate_no_gate_list_duplication(controller: Mapping[str, Any]) -> list[str]:
    failures: list[str] = []
    active_gate_ids = set(gate_registry.get_active_non_sha_day1_gate_ids())
    for value in _iter_lists(controller):
        string_items = {item for item in value if isinstance(item, str)}
        if active_gate_ids.issubset(string_items):
            failures.append("controller must not duplicate the full active non-SHA gate list")
    return failures


def _iter_lists(value: Any) -> Iterable[list[Any]]:
    if isinstance(value, list):
        yield value
        for item in value:
            yield from _iter_lists(item)
    elif isinstance(value, dict):
        for item in value.values():
            yield from _iter_lists(item)


def _validate_downstream_references(repo_root: pathlib.Path) -> list[str]:
    failures: list[str] = []
    controller_path = DEFAULT_CONTROLLER.as_posix()
    roster_path = DEFAULT_ROSTER.as_posix()
    taxonomy = set(CONTROLLED_STATES)
    vector = set(NON_MATERIALIZED_CAPABILITIES)
    for path in ROADMAP_DOCS:
        full_path = _resolve(repo_root, path)
        if not full_path.exists():
            failures.append(f"roadmap/blueprint currentization surface missing: {path.as_posix()}")
            continue
        text = full_path.read_text(encoding="utf-8")
        if controller_path not in text:
            failures.append(f"{path.as_posix()} must reference {controller_path}")
        if roster_path not in text:
            failures.append(f"{path.as_posix()} must reference {roster_path}")
        if taxonomy.issubset(set(_strings(text))):
            failures.append(f"{path.as_posix()} must not copy the full controller taxonomy")
        if vector.issubset(set(_strings(text))):
            failures.append(f"{path.as_posix()} must not copy the non-materialized capability vector")
        if all(state in text for state in CONTROLLED_STATES):
            failures.append(f"{path.as_posix()} must not copy the full controller taxonomy")
        if all(capability in text for capability in NON_MATERIALIZED_CAPABILITIES):
            failures.append(f"{path.as_posix()} must not copy the non-materialized capability vector")
    return failures


def _validate_gate_sequence(repo_root: pathlib.Path) -> list[str]:
    gate_text = _resolve(repo_root, RUN_VALIDATION_GATES).read_text(encoding="utf-8")
    roster_name = "validate_qtt_pr_identity_roster.py"
    controller_name = VALIDATOR_NAME
    if controller_name not in gate_text:
        return [f"tools/run_validation_gates.py must include {controller_name}"]
    if gate_text.find(roster_name) > gate_text.find(controller_name):
        return [f"{controller_name} must run after {roster_name}"]
    return []


def _build_report(
    controller: Mapping[str, Any],
    roster: Mapping[str, Any],
    failures: Sequence[str],
) -> dict[str, Any]:
    entries = _entries(roster)
    pr117 = _entry_by_id(entries, "PR117_REPO_CANONICAL_SELF_ENTRY") or {}
    pr118 = _entry_by_id(entries, "PR118_REPO_CANONICAL_SELF_ENTRY") or {}
    result_ok = not failures
    return {
        "report_id": REPORT_ID,
        "controller_id": controller.get("controller_id"),
        "validator_name": VALIDATOR_NAME,
        "validation_status": "PASS" if result_ok else "FAIL",
        "controller_established_state": controller.get("controller_established_state"),
        "materialized_capability_this_pr": controller.get(
            "capability_envelope", {}
        ).get("materialized_capability_this_pr"),
        "state_transition_this_pr": controller.get("capability_envelope", {}).get(
            "state_transition_this_pr"
        ),
        "roadmap_range_mapping_count": len(
            controller.get("roadmap_range_currentization", [])
        ),
        "identity_translation_authority": ROSTER_PATH,
        "pr117_github_pr_number": pr117.get("github_pr_number"),
        "pr117_github_audit_url": pr117.get("github_audit_url"),
        "pr117_roadmap_pr_label": pr117.get("roadmap_pr_label"),
        "pr117_blueprint_pr_label": pr117.get("blueprint_pr_label"),
        "pr118_repo_canonical_pr_label": pr118.get("repo_canonical_pr_label"),
        "pr118_github_pr_number": pr118.get("github_pr_number"),
        "pr118_roadmap_pr_label": pr118.get("roadmap_pr_label"),
        "pr118_blueprint_pr_label": pr118.get("blueprint_pr_label"),
        "final_readiness_state": controller.get("active_state_bindings", {}).get(
            "final_readiness_state"
        ),
        "final_readiness_derives_from_pr116a_active_non_sha_registry": True,
        "active_non_sha_gate_list_duplicated_in_controller": False,
        "quantum_backend_state": controller.get("active_state_bindings", {}).get(
            "quantum_backend_state"
        ),
        "quantum_forward_optimization_state": controller.get(
            "active_state_bindings", {}
        ).get("quantum_forward_optimization_state"),
        "result_marker": SUCCESS_MARKER if result_ok else FAILURE_MARKER,
        "validation_errors": list(failures),
    }


def validate(
    *,
    repo_root: pathlib.Path = REPO_ROOT,
    controller_path: pathlib.Path = DEFAULT_CONTROLLER,
    schema_path: pathlib.Path = DEFAULT_SCHEMA,
    roster_path: pathlib.Path = DEFAULT_ROSTER,
    report_out: pathlib.Path = DEFAULT_REPORT,
) -> ValidationResult:
    repo_root = repo_root.resolve()
    failures: list[str] = []
    try:
        controller = _load_json(_resolve(repo_root, controller_path))
        schema = _load_json(_resolve(repo_root, schema_path))
        roster = _load_json(_resolve(repo_root, roster_path))
    except Exception as exc:
        return ValidationResult(False, (f"could not load controller inputs: {exc}",), None)

    failures.extend(
        f"CONTROLLER_SCHEMA {failure}"
        for failure in validate_json_schema_subset(controller, schema)
    )
    failures.extend(_validate_top_level(controller))
    failures.extend(_validate_upstream_authorities(repo_root, controller))
    failures.extend(_validate_identity_translation(controller))
    failures.extend(_validate_taxonomy(controller))
    failures.extend(_validate_active_bindings(controller))
    failures.extend(_validate_roster_currentization(roster))
    failures.extend(_validate_roadmap_currentization(controller))
    failures.extend(_validate_capability_and_discipline(controller))
    failures.extend(_validate_invariants(controller))
    failures.extend(_validate_no_gate_list_duplication(controller))
    failures.extend(_validate_downstream_references(repo_root))
    failures.extend(_validate_gate_sequence(repo_root))

    report = _build_report(controller, roster, failures)
    if failures:
        return ValidationResult(False, tuple(failures), report)
    if report != json.loads(json.dumps(report, sort_keys=True)):
        return ValidationResult(False, ("report serialization must be deterministic",), report)
    _write_json_report(report, _resolve(repo_root, report_out))
    return ValidationResult(True, tuple(), report)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=pathlib.Path, default=REPO_ROOT)
    parser.add_argument("--controller", type=pathlib.Path, default=DEFAULT_CONTROLLER)
    parser.add_argument("--schema", type=pathlib.Path, default=DEFAULT_SCHEMA)
    parser.add_argument("--roster", type=pathlib.Path, default=DEFAULT_ROSTER)
    parser.add_argument("--report-out", type=pathlib.Path, default=DEFAULT_REPORT)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    result = validate(
        repo_root=args.repo_root,
        controller_path=args.controller,
        schema_path=args.schema,
        roster_path=args.roster,
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
