import json
import subprocess
import sys
from pathlib import Path

from src.qtt.core.testing import qtt_active_non_sha_day1_gate_state_registry as gate_registry
from src.qtt.core.testing import qtt_final_readiness_dependency_policy as readiness_policy
from tools import run_validation_gates
from tools import validate_qtt_pr_identity_roster as roster_gate


ROSTER_PATH = Path("docs/roadmap/QTT_PR_Identity_Roster_v1_0.json")
SCHEMA_PATH = Path("schemas/roadmap/qtt_pr_identity_roster.schema.json")
ATOMICROWS_BUNDLE = Path("docs/master_plan/atomic_rows/AtomicRows.bundle.jsonl")
ATOMICROWS_BUNDLE_SHA = Path("docs/master_plan/atomic_rows/AtomicRows.bundle.sha256")


def _roster() -> dict:
    return json.loads(ROSTER_PATH.read_text(encoding="utf-8"))


def _entries() -> list[dict]:
    return _roster()["entries"]


def _entry(entry_id: str) -> dict:
    return next(entry for entry in _entries() if entry["roster_entry_id"] == entry_id)


def _git_status_for(path: Path) -> list[str]:
    completed = subprocess.run(
        ["git", "status", "--short", "--", path.as_posix()],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    return completed.stdout.splitlines()


def test_roster_json_and_schema_validate():
    assert ROSTER_PATH.exists()
    assert SCHEMA_PATH.exists()

    result = roster_gate.validate()

    assert result.ok, result.failures
    assert _roster()["roster_id"] == "QTT_PR_IDENTITY_ROSTER_V1_0"
    assert json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))["title"] == (
        "QTT PR Identity Roster v1.0"
    )


def test_four_systems_and_canonical_priority_are_enforced():
    roster = _roster()

    assert roster["systems_declared"] == ["repo", "roadmap", "blueprint", "github"]
    assert roster["canonical_priority_order"] == [
        "REPO_CANONICAL_LABEL",
        "BLUEPRINT_DELIVERY_LABEL",
        "ROADMAP_DELIVERY_LABEL",
        "GITHUB_AUDIT_NUMBER",
    ]


def test_identity_system_invariants_are_explicit():
    invariants = _roster()["global_invariants"]

    assert invariants["github_numbers_are_audit_only"] is True
    assert invariants["repo_canonical_references_are_implementation_truth"] is True
    assert invariants["blueprint_labels_are_implementation_scope_labels"] is True
    assert invariants["roadmap_labels_are_planning_orchestration_labels"] is True
    assert invariants["same_number_identity_inference_forbidden"] is True


def test_pr115a_and_pr116a_corrective_overlays_map_to_github_audit_numbers():
    pr115a = _entry("PR115A_CORRECTIVE_OVERLAY_GITHUB_115")
    pr116a = _entry("PR116A_CORRECTIVE_OVERLAY_GITHUB_116")

    assert pr115a["repo_canonical_pr_label"] == "PR115A"
    assert pr115a["github_pr_number"] == 115
    assert pr115a["corrective_overlay"] is True
    assert pr115a["semantic_role"] == "CORRECTIVE_OVERLAY"
    assert pr115a["authority_scope"] == "CONTROL_PLANE_ONLY"

    assert pr116a["repo_canonical_pr_label"] == "PR116A"
    assert pr116a["github_pr_number"] == 116
    assert pr116a["corrective_overlay"] is True
    assert pr116a["semantic_role"] == "CORRECTIVE_OVERLAY"
    assert pr116a["authority_scope"] == "CONTROL_PLANE_ONLY"


def test_github_116_does_not_overwrite_roadmap_116():
    pr116a = _entry("PR116A_CORRECTIVE_OVERLAY_GITHUB_116")
    roadmap_pr116 = _entry("ROADMAP_PR_116_PLANNED")

    assert pr116a["github_title"] == "Add active non-SHA Day-1 gate registry"
    assert pr116a["roadmap_title"] == "Runtime resolver snapshot executor"
    assert pr116a["same_number_mismatch_recorded"] is True
    assert pr116a["identity_relation_class"] != "EXACT_SAME_SYSTEM_REFERENCE"

    assert roadmap_pr116["github_pr_number"] is None
    assert roadmap_pr116["roadmap_title"] == "Runtime resolver snapshot executor"
    assert roadmap_pr116["current_status"] == "PLANNED"


def test_same_number_mismatches_for_github_107_through_119_are_recorded():
    records = _roster()["mismatch_summary"][
        "github_107_through_116_same_number_mismatches"
    ]
    numbers = {record["github_pr_number"] for record in records}

    assert numbers == set(range(107, 120))
    assert any(
        record["github_pr_number"] == 107
        and record["github_title"] == "Add AtomicRows repair-chain grand debug logic audit"
        and record["roadmap_title"]
        == "Source revalidation, supersession, and materiality scheduler"
        for record in records
    )


def test_pr117_self_entry_is_currentized_but_not_roadmap_or_blueprint_117():
    pr117 = _entry("PR117_REPO_CANONICAL_SELF_ENTRY")

    assert pr117["repo_canonical_pr_label"] == "PR117"
    assert pr117["github_pr_number"] == 117
    assert (
        pr117["github_audit_url"]
        == "https://github.com/Q8Meow/QTT_New0526/pull/117"
    )
    assert pr117["github_title"] == "PR117 add canonical PR identity roster"
    assert pr117["roadmap_pr_label"] is None
    assert pr117["blueprint_pr_label"] is None
    assert pr117["identity_relation_class"] == "REPO_CANONICAL_ONLY"
    assert pr117["same_number_mismatch_recorded"] is True


def test_pr118_self_entry_is_currentized_but_not_roadmap_or_blueprint_118():
    pr118 = _entry("PR118_REPO_CANONICAL_SELF_ENTRY")

    assert pr118["repo_canonical_pr_label"] == "PR118"
    assert pr118["github_pr_number"] == 118
    assert (
        pr118["github_audit_url"]
        == "https://github.com/Q8Meow/QTT_New0526/pull/118"
    )
    assert pr118["github_title"] == "PR118 add roadmap execution-state controller"
    assert pr118["roadmap_pr_label"] is None
    assert pr118["blueprint_pr_label"] is None
    assert pr118["identity_relation_class"] == "REPO_CANONICAL_ONLY"
    assert pr118["same_number_mismatch_recorded"] is True
    assert pr118["depends_on_roster_entries"] == [
        "PR117_REPO_CANONICAL_SELF_ENTRY"
    ]


def test_pr119_self_entry_is_currentized_but_not_roadmap_or_blueprint_119():
    pr119 = _entry("PR119_REPO_CANONICAL_SELF_ENTRY")

    assert pr119["repo_canonical_pr_label"] == "PR119"
    assert pr119["github_pr_number"] == 119
    assert (
        pr119["github_audit_url"]
        == "https://github.com/Q8Meow/QTT_New0526/pull/119"
    )
    assert (
        pr119["github_title"]
        == "PR119 currentize identity roster and add controller-approved coverage triage routes"
    )
    assert pr119["roadmap_pr_label"] is None
    assert pr119["blueprint_pr_label"] is None
    assert pr119["identity_relation_class"] == "REPO_CANONICAL_ONLY"
    assert pr119["same_number_mismatch_recorded"] is True
    assert pr119["depends_on_roster_entries"] == [
        "PR118_REPO_CANONICAL_SELF_ENTRY"
    ]


def test_atomicrows_bundle_is_not_mutated_and_sha_is_not_created():
    expectations = _roster()["validation_expectations"]

    assert expectations["atomicrows_bundle_jsonl_required_status"] == (
        "UNCHANGED_FROM_BASELINE_STATE"
    )
    assert expectations["atomicrows_bundle_sha256_required_absent"] is True
    assert ATOMICROWS_BUNDLE.exists()
    assert _git_status_for(ATOMICROWS_BUNDLE) == []
    assert not ATOMICROWS_BUNDLE_SHA.exists()
    assert _git_status_for(ATOMICROWS_BUNDLE_SHA) == []


def test_roster_preserves_active_gate_registry_and_final_readiness_blockers():
    boundary = _roster()["no_claim_boundary"]

    assert boundary["no_active_non_sha_day1_gate_flipped"] is True
    assert boundary["final_readiness_created"] is False
    assert boundary["day1_launch_authority_created"] is False
    assert (
        boundary[
            "runtime_live_order_source_connector_runtime_cash_backend_profit_authority_created"
        ]
        is False
    )
    gate_registry.assert_no_gate_flipped_by_this_pr()
    gate_registry.assert_all_positive_evidence_gates_remain_blocked()
    readiness_policy.assert_current_pr_does_not_create_final_readiness()


def test_roster_preserves_source_connector_runtime_profit_and_execution_blocks():
    boundary = _roster()["no_claim_boundary"]

    assert boundary["source_facts_accepted"] is False
    assert boundary["connector_semantics_bound"] is False
    assert boundary["runtime_cash_receipts_created"] is False
    assert (
        boundary["replay_paper_optimizer_neural_quantum_backend_execution_created"]
        is False
    )
    assert boundary["qubo_qaoa_vqe_ising_annealing_execution_created"] is False
    assert boundary["profit_latency_execution_quantum_advantage_evidence_created"] is False
    assert boundary["bug_free_status_claimed"] is False


def test_roster_validator_is_in_cumulative_validation_gates():
    commands = run_validation_gates.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands]

    roster_index = command_names.index("validate_qtt_pr_identity_roster.py")
    active_registry_index = command_names.index(
        "validate_qtt_active_non_sha_day1_gate_state_registry_contract.py"
    )
    pr100_index = command_names.index(
        "validate_atomicrows_bundle_sha_freeze_authority_gate.py"
    )

    assert active_registry_index < roster_index < pr100_index


def test_roster_validator_prints_success_marker():
    completed = subprocess.run(
        [sys.executable, "tools/validate_qtt_pr_identity_roster.py"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.strip() == "QTT_PR_IDENTITY_ROSTER_OK"
