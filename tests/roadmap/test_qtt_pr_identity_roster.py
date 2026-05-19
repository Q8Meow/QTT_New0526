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
PR122_AUDIT_RECEIPT_PATH = Path(
    "docs/roadmap/generated/CODEX_REPO_PR122_GITHUB_AUDIT_CURRENTIZATION_RECEIPT.json"
)
PR123_AUDIT_RECEIPT_PATH = Path(
    "docs/roadmap/generated/CODEX_REPO_PR123_GITHUB_AUDIT_CURRENTIZATION_RECEIPT.json"
)
PR123_OWNER_AUTH_RECEIPT_PATH = Path(
    "docs/roadmap/generated/CODEX_PR123_OWNER_AUTHORIZED_PR106_IMPLEMENTATION_RECEIPT.json"
)


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


def test_same_number_mismatches_for_github_107_through_123_are_recorded():
    records = _roster()["mismatch_summary"][
        "github_107_through_116_same_number_mismatches"
    ]
    numbers = {record["github_pr_number"] for record in records}

    assert numbers == set(range(107, 124))
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


def test_pr120_self_entry_is_currentized_but_not_roadmap_or_blueprint_120():
    pr120 = _entry("PR120_REPO_CANONICAL_SELF_ENTRY")

    assert pr120["repo_canonical_pr_label"] == "PR120"
    assert pr120["github_pr_number"] == 120
    assert (
        pr120["github_audit_url"]
        == "https://github.com/Q8Meow/QTT_New0526/pull/120"
    )
    assert (
        pr120["github_title"]
        == "PR120 add master-plan roadmap crosswalk and market section indexes"
    )
    assert pr120["roadmap_pr_label"] is None
    assert pr120["blueprint_pr_label"] is None
    assert pr120["identity_relation_class"] == "REPO_CANONICAL_ONLY"
    assert pr120["same_number_mismatch_recorded"] is True
    assert pr120["depends_on_roster_entries"] == [
        "PR119_REPO_CANONICAL_SELF_ENTRY"
    ]


def test_pr121_self_entry_is_currentized_but_not_roadmap_or_blueprint_121():
    pr121 = _entry("PR121_REPO_CANONICAL_SELF_ENTRY")

    assert pr121["repo_canonical_pr_label"] == "PR121"
    assert pr121["github_pr_number"] == 121
    assert (
        pr121["github_audit_url"]
        == "https://github.com/Q8Meow/QTT_New0526/pull/121"
    )
    assert pr121["github_title"] == "PR121 add master-plan section coverage command matrix"
    assert pr121["branch_name"] == "pr121-master-plan-section-coverage-command-matrix"
    assert pr121["roadmap_pr_label"] is None
    assert pr121["blueprint_pr_label"] is None
    assert pr121["identity_relation_class"] == "REPO_CANONICAL_ONLY"
    assert pr121["same_number_mismatch_recorded"] is True
    assert pr121["depends_on_roster_entries"] == [
        "PR120_REPO_CANONICAL_SELF_ENTRY"
    ]


def test_pr122_self_entry_is_currentized_but_not_roadmap_or_blueprint_122():
    pr122 = _entry("PR122_REPO_CANONICAL_SELF_ENTRY")
    receipt = json.loads(PR122_AUDIT_RECEIPT_PATH.read_text(encoding="utf-8"))

    assert pr122["repo_canonical_pr_label"] == "PR122"
    assert pr122["github_pr_number"] == 122
    assert pr122["github_audit_url"] == "https://github.com/Q8Meow/QTT_New0526/pull/122"
    assert pr122["github_title"] == "PR122 add source-evidence retrieval controller gate"
    assert pr122["branch_name"] == "pr122-source-evidence-retrieval-controller-gated"
    assert pr122["roadmap_pr_label"] is None
    assert pr122["blueprint_pr_label"] is None
    assert pr122["identity_relation_class"] == "REPO_CANONICAL_ONLY"
    assert pr122["same_number_mismatch_recorded"] is True
    assert pr122["depends_on_roster_entries"] == [
        "PR121_REPO_CANONICAL_SELF_ENTRY"
    ]
    assert receipt["github_pr_number"] == 122
    assert receipt["github_pr_title"] == pr122["github_title"]
    assert receipt["github_pr_state"] == "MERGED"
    assert receipt["github_pr_mergedAt"] == "2026-05-19T05:38:14Z"
    assert (
        receipt["github_pr_mergeCommit_oid"]
        == "1ca3f621349598ac73be1f1392600a862d25bb34"
    )
    assert receipt["same_number_inference_used"] is False


def test_repo_pr123_does_not_imply_roadmap_pr123_and_owner_authorized_pr106():
    receipt = json.loads(PR123_OWNER_AUTH_RECEIPT_PATH.read_text(encoding="utf-8"))
    roadmap_123 = _entry("ROADMAP_PR_123_PLANNED")

    assert roadmap_123["roadmap_title"] == (
        "Prediction-market microstructure feature calibration runtime"
    )
    assert not any(
        entry["repo_canonical_pr_label"] == "PR123"
        and entry["roadmap_pr_label"] == "PR #123"
        for entry in _entries()
    )
    assert receipt["repo_pr_label"] == "PR123"
    assert receipt["roadmap_pr_implemented"] == "PR106"
    assert receipt["blueprint_pr_implemented"] == "PR106"
    assert receipt["owner_explicitly_authorized_roadmap_blueprint_pr106"] is True
    assert receipt["roadmap_controller_files_used_as_state_evidence_records_only"] is True
    assert receipt["same_number_identity_inference_used"] is False


def test_pr123_github_audit_currentization_is_recorded_and_audit_only():
    pr123 = _entry("PR123_REPO_CANONICAL_SELF_ENTRY")
    receipt = json.loads(PR123_AUDIT_RECEIPT_PATH.read_text(encoding="utf-8"))

    assert pr123["repo_canonical_pr_label"] == "PR123"
    assert pr123["github_pr_number"] == 123
    assert pr123["github_audit_url"] == "https://github.com/Q8Meow/QTT_New0526/pull/123"
    assert pr123["github_title"] == "PR123 implement accepted source-evidence acceptance executor ledger"
    assert pr123["branch_name"] == "pr123-accepted-source-evidence-acceptance-executor-ledger"
    assert pr123["roadmap_pr_label"] is None
    assert pr123["blueprint_pr_label"] is None
    assert pr123["identity_relation_class"] == "REPO_CANONICAL_ONLY"
    assert pr123["same_number_mismatch_recorded"] is True
    assert pr123["depends_on_roster_entries"] == [
        "PR122_REPO_CANONICAL_SELF_ENTRY"
    ]
    assert receipt["currentized_prior_repo_pr_label"] == "PR123"
    assert receipt["github_pr_number"] == 123
    assert receipt["github_pr_title"] == pr123["github_title"]
    assert receipt["github_pr_state"] == "MERGED"
    assert receipt["github_pr_mergedAt"] == "2026-05-19T08:05:14Z"
    assert (
        receipt["github_pr_mergeCommit_oid"]
        == "f80819434da508c8c214168d62ff0b5d83df2e37"
    )
    assert receipt["same_number_inference_used"] is False


def test_repo_pr124_does_not_imply_roadmap_pr124_and_owner_authorized_connector_gate():
    receipt = json.loads(PR123_AUDIT_RECEIPT_PATH.read_text(encoding="utf-8"))
    roadmap_124 = _entry("ROADMAP_PR_124_PLANNED")

    assert roadmap_124["roadmap_title"] == (
        "Neural signal walk-forward, calibration, and drift runtime"
    )
    assert not any(
        entry["repo_canonical_pr_label"] == "PR124"
        and entry["roadmap_pr_label"] == "PR #124"
        for entry in _entries()
    )
    assert receipt["repo_pr_label"] == "PR124"
    assert (
        receipt["owner_authorized_next_capability"]
        == "ACCEPTED_SOURCE_TO_CONNECTOR_SEMANTIC_BINDING_CONSUMER_GATE"
    )
    assert receipt["implementation_scope"] == (
        "ACCEPTED_SOURCE_TO_CONNECTOR_SEMANTIC_BINDING_CONSUMER_GATE"
    )
    assert receipt["controller_used_as_record_not_veto"] is True
    assert receipt["same_number_inference_used"] is False


def test_pr105_is_not_inferred_from_github_105_or_repo_pr122():
    github_105 = _entry("GITHUB_PR_105_IDENTITY_MISMATCH")
    roadmap_105 = _entry("ROADMAP_PR_105_PLANNED")

    assert github_105["github_pr_number"] == 105
    assert github_105["repo_canonical_pr_label"] == "REPAIR_PR_C0"
    assert github_105["current_status"] == "MERGED"
    assert github_105["identity_relation_class"] == "SAME_NUMBER_MISMATCH"
    assert github_105["same_number_mismatch_recorded"] is True

    assert roadmap_105["github_pr_number"] is None
    assert roadmap_105["repo_canonical_pr_label"] is None
    assert roadmap_105["current_status"] == "PLANNED"
    assert roadmap_105["identity_relation_class"] == "ROADMAP_ONLY_PLANNED"
    assert roadmap_105["roadmap_title"] == "Source-evidence retrieval executor"
    assert not any(
        entry["repo_canonical_pr_label"] == "PR122"
        and entry["roadmap_pr_label"] == "PR #105"
        for entry in _entries()
    )


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
