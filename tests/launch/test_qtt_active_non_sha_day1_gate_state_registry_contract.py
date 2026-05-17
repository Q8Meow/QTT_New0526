from __future__ import annotations

import ast
import copy
import json
from pathlib import Path

from src.qtt.core.testing import atomicrows_sha_system_dormancy_state as sha_state
from src.qtt.core.testing import qtt_active_non_sha_day1_gate_state_registry as registry
from src.qtt.core.testing import qtt_final_readiness_dependency_policy as policy
from tools import validate_qtt_active_non_sha_day1_gate_state_registry_contract as validator
from tools import validate_qtt_final_readiness_dependency_policy_contract as policy_validator


REPO_ROOT = Path(__file__).resolve().parents[2]
_REPORT_CACHE: dict | None = None


def _contract() -> dict:
    return validator.load_yaml(REPO_ROOT / validator.DEFAULT_CONTRACT)


def _schema() -> dict:
    return validator.load_json(REPO_ROOT / validator.DEFAULT_SCHEMA)


def _report() -> dict:
    global _REPORT_CACHE
    if _REPORT_CACHE is None:
        result = validator.validate(repo_root=REPO_ROOT)
        assert result.ok is True, result.failures
        assert result.report is not None
        _REPORT_CACHE = result.report
    return _REPORT_CACHE


def _assert_failure_contains(failures: list[str], fragment: str) -> None:
    assert any(fragment in failure for failure in failures), failures


def test_registry_module_exists_and_current_state_is_established():
    contract = _contract()

    assert validator.validate_contract_payload(contract, _schema()) == []
    assert (
        registry.get_qtt_active_non_sha_day1_gate_registry_state()
        == "ACTIVE_NON_SHA_DAY1_GATE_STATE_REGISTRY_ESTABLISHED_ALL_POSITIVE_EVIDENCE_GATES_BLOCKED_GUARDS_ACTIVE"
    )
    assert (
        registry.CURRENT_QTT_ACTIVE_NON_SHA_DAY1_GATE_REGISTRY_STATE
        == registry.EXPECTED_CURRENT_QTT_ACTIVE_NON_SHA_DAY1_GATE_REGISTRY_STATE
    )
    assert len(registry.get_active_non_sha_day1_gate_ids()) == 18
    assert len(registry.get_active_non_sha_day1_gate_records()) == 18


def test_active_gate_ids_match_final_readiness_dependency_policy_and_exclude_sha():
    assert (
        registry.get_active_non_sha_day1_gate_ids()
        == policy.get_active_non_sha_final_readiness_dependencies()
    )
    assert (
        policy.ACTIVE_NON_SHA_FINAL_READINESS_DEPENDENCIES
        is registry.QTT_ACTIVE_NON_SHA_DAY1_GATE_IDS
    )
    assert registry.is_sha_dormancy_system_excluded() is True
    assert "SHA_DORMANCY_SYSTEM" not in registry.get_active_non_sha_day1_gate_ids()
    assert registry.get_excluded_non_participating_subsystems() == (
        "SHA_DORMANCY_SYSTEM",
    )
    registry.assert_gate_ids_match_expected_active_non_sha_dependencies(
        policy.get_active_non_sha_final_readiness_dependencies()
    )
    policy.assert_active_dependencies_consume_gate_registry()


def test_sha_dormancy_is_non_participating_and_not_day1_evidence_or_blocker():
    assert (
        sha_state.get_atomicrows_sha_system_dormancy_state()
        == "SHA_SYSTEM_DORMANT_NON_PARTICIPATING_OWNER_CONTROLLED"
    )
    assert sha_state.is_sha_system_non_participating_for_final_readiness() is True
    assert policy.is_sha_required_for_final_readiness() is False
    assert policy.is_sha_dormancy_a_final_readiness_blocker() is False
    assert policy.is_sha_absence_a_final_readiness_blocker() is False
    assert policy.is_sha_presence_final_readiness_evidence() is False
    policy.assert_day1_final_readiness_must_ignore_sha_dormancy_when_non_sha_gates_pass()


def test_no_active_gate_was_flipped_or_satisfied_by_this_pr():
    registry.assert_no_gate_flipped_by_this_pr()
    registry.assert_no_gate_satisfied_by_this_pr()
    assert registry.CURRENT_PR_FLIPS_ANY_GATE is False
    assert registry.CURRENT_PR_MARKS_ANY_GATE_SATISFIED is False
    assert not any(
        record["current_state"] == "SATISFIED_BY_CANONICAL_RECEIPT"
        for record in registry.get_active_non_sha_day1_gate_records()
    )
    assert not any(
        record["current_pr_may_flip"]
        for record in registry.get_active_non_sha_day1_gate_records()
    )


def test_positive_blocker_gates_remain_blocked_and_guard_gates_unviolated():
    registry.assert_all_positive_evidence_gates_remain_blocked()
    registry.assert_guard_gates_active_and_unviolated()
    assert set(registry.get_currently_blocking_positive_gate_ids()) == {
        "OWNER_DAY1_LAUNCH_APPROVAL",
        "ACCEPTED_SOURCE_EVIDENCE_FOR_TARGET_FIELDS",
        "CONNECTOR_SEMANTIC_BINDINGS_FOR_TARGET_FIELDS",
        "FRESH_SOURCE_REVALIDATION_STATE",
        "RUNTIME_CASH_COMPONENT_FIELD_MAP",
        "RUNTIME_CASH_RECEIPTS_WHEN_REQUIRED",
        "REPLAY_AND_PAPER_RESULTS_WHEN_REQUIRED",
        "DUAL_RESULT_REVIEW_WHEN_REQUIRED",
        "OWNER_LIVE_PROMOTION_REVIEW_WHEN_REQUIRED",
        "RISK_LIMIT_AND_EXPOSURE_GATES",
        "LIVE_PREFLIGHT_MATRIX",
        "ORDER_ROUTER_SAFETY_GATES",
        "KILL_SWITCH_AND_ROLLBACK_GATES",
    }
    assert set(registry.get_no_claim_guard_gate_ids()) == {
        "QUANTUM_ADVANTAGE_NO_CLAIM_GATE",
        "PROFIT_NO_CLAIM_GATE",
        "LATENCY_AND_EXECUTION_EVIDENCE_NO_FABRICATION_GATE",
    }


def test_no_claim_gates_do_not_create_profit_latency_execution_or_quantum_evidence():
    profit = registry.get_gate_record("PROFIT_NO_CLAIM_GATE")
    quantum = registry.get_gate_record("QUANTUM_ADVANTAGE_NO_CLAIM_GATE")
    latency = registry.get_gate_record(
        "LATENCY_AND_EXECUTION_EVIDENCE_NO_FABRICATION_GATE"
    )

    for record in (profit, quantum, latency):
        assert record["evaluation_mode"] == "ACTIVE_GUARD_UNVIOLATED"
        assert record["guard_active_and_unviolated"] is True
        assert record["currently_blocks_final_readiness"] is False
        assert record["creates_evidence_in_this_pr"] is False
        assert record["creates_authority_in_this_pr"] is False
        assert record["executes_runtime_in_this_pr"] is False
    registry.assert_current_pr_creates_no_profit_latency_execution_quantum_advantage_evidence()


def test_quantum_backend_authority_gate_is_conditional_and_blocks_unauthorized_backend_execution():
    record = registry.get_gate_record("QUANTUM_BACKEND_AUTHORITY_GATE")

    assert registry.is_quantum_backend_gate_conditional() is True
    assert (
        record["evaluation_mode"]
        == "CONDITIONAL_AUTHORITY_GUARD_NONBLOCKING_UNLESS_SCOPE_REQUIRES"
    )
    assert record["currently_blocks_final_readiness"] is False
    assert (
        record[
            "conditional_blocks_final_readiness_if_selected_stack_requires_true_quantum_backend"
        ]
        is True
    )
    assert record["true_quantum_backend_required_for_non_backend_day1_launch_scope"] is False
    assert record["blocks_unauthorized_backend_simulator_provider_execution"] is True
    assert record["blocks_static_quantum_metadata_or_planning"] is False
    registry.assert_quantum_backend_gate_does_not_require_backend_for_non_backend_day1()


def test_registry_creates_no_readiness_authority_receipts_runtime_or_evidence():
    report = _report()

    registry.assert_current_pr_creates_no_final_readiness()
    registry.assert_current_pr_creates_no_runtime_live_profit_or_backend_authority()
    registry.assert_current_pr_creates_no_replay_paper_optimizer_neural_quantum_execution()
    registry.assert_current_pr_creates_no_profit_latency_execution_quantum_advantage_evidence()
    assert report["final_readiness_created"] is False
    assert report["day1_launch_authority_created"] is False
    assert (
        report[
            "runtime_live_order_source_connector_runtime_cash_backend_profit_authority_created"
        ]
        is False
    )
    assert report["replay_paper_optimizer_neural_quantum_backend_execution_created"] is False
    assert report["source_facts_accepted_by_this_pr"] is False
    assert report["connector_semantics_bound_by_this_pr"] is False
    assert report["runtime_cash_receipts_created_by_this_pr"] is False
    assert report["order_fill_account_receipts_created_by_this_pr"] is False
    assert (
        report[
            "qubo_qaoa_vqe_ising_annealing_backend_simulator_execution_created_by_this_pr"
        ]
        is False
    )
    assert report["profit_latency_execution_quantum_advantage_evidence_claimed"] is False


def test_atomicrows_bundle_remains_present_unchanged_and_sha_absent(tmp_path):
    bundle_path = REPO_ROOT / validator.CANONICAL_ATOMICROWS_BUNDLE
    sha_path = REPO_ROOT / validator.CANONICAL_ATOMICROWS_BUNDLE_SHA
    before = bundle_path.read_bytes()

    result = validator.validate(
        repo_root=REPO_ROOT,
        report_out=tmp_path / "active_gate_registry.report.json",
    )

    assert result.ok is True, result.failures
    assert bundle_path.read_bytes() == before
    assert bundle_path.exists()
    assert len(before.decode("utf-8").splitlines()) == 4183
    assert not sha_path.exists()
    assert result.report is not None
    assert result.report["atomicrows_bundle_exists"] is True
    assert result.report["atomicrows_bundle_line_count"] == 4183
    assert result.report["atomicrows_bundle_sha256_exists"] is False
    assert result.report["sha_absence_is_day1_gate_blocker"] is False
    assert result.report["sha_presence_is_final_readiness_evidence"] is False


def test_validator_rejects_unknown_gate_satisfied_gate_and_authority_creation():
    schema = _schema()
    contract = copy.deepcopy(_contract())
    contract["active_non_sha_gate_ids"] = [
        *contract["active_non_sha_gate_ids"],
        "UNKNOWN_GATE",
    ]
    _assert_failure_contains(
        validator.validate_contract_payload(contract, schema),
        "active_non_sha_gate_ids",
    )

    contract = copy.deepcopy(_contract())
    contract["gate_records"][0]["current_state"] = "SATISFIED_BY_CANONICAL_RECEIPT"
    _assert_failure_contains(
        validator.validate_contract_payload(contract, schema),
        "must not be marked satisfied",
    )

    contract = copy.deepcopy(_contract())
    contract["current_pr_creates_final_readiness"] = True
    _assert_failure_contains(
        validator.validate_contract_payload(contract, schema),
        "current_pr_creates_final_readiness",
    )


def test_policy_validator_checks_registry_alignment():
    schema = policy_validator.load_json(REPO_ROOT / policy_validator.DEFAULT_SCHEMA)
    contract = policy_validator.load_yaml(REPO_ROOT / policy_validator.DEFAULT_CONTRACT)
    tampered = copy.deepcopy(contract)
    tampered["active_non_sha_final_readiness_dependencies"] = [
        *tampered["active_non_sha_final_readiness_dependencies"],
        "UNREGISTERED_DAY1_GATE",
    ]

    _assert_failure_contains(
        policy_validator.validate_contract_payload(tampered, schema),
        "active_non_sha_final_readiness_dependencies",
    )


def test_run_validator_emits_exact_success_marker_and_report_has_no_forbidden_claims(
    tmp_path,
    capsys,
):
    report_path = tmp_path / "active_gate_registry.report.json"

    assert (
        validator.main(
            [
                "--repo-root",
                str(REPO_ROOT),
                "--report-out",
                str(report_path),
            ]
        )
        == 0
    )
    output = [line.strip() for line in capsys.readouterr().out.splitlines() if line.strip()]
    assert output == [validator.SUCCESS_MARKER]
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["result_marker"] == validator.SUCCESS_MARKER
    serialized = json.dumps(report, sort_keys=True).lower()
    assert "bug-free" not in serialized
    assert "bug_free" not in serialized
    assert "production-ready" not in serialized
    assert "launch readiness" not in serialized
    assert "profit readiness" not in serialized
    assert "quantum advantage" not in serialized


def test_roadmap_blueprint_pr116a_notes_preserve_blocked_authority_boundaries():
    roadmap_readme = (REPO_ROOT / "docs/roadmap/README.md").read_text(
        encoding="utf-8"
    )
    roadmap_md = (
        REPO_ROOT
        / "docs/roadmap/QTT_PRs_Roadmap_Consolidated_Static_Runtime_Live_Stage1_to_Stage5_v1_0.md"
    ).read_text(encoding="utf-8")
    blueprint_md = (
        REPO_ROOT
        / "docs/roadmap/QTT_PR_Blueprints_Stage1_to_Stage5_PR83_to_PR224_v1_0.md"
    ).read_text(encoding="utf-8")
    roadmap_index = json.loads(
        (
            REPO_ROOT / "docs/roadmap/QTT_PRs_Roadmap_Index_v1_0.json"
        ).read_text(encoding="utf-8")
    )
    blueprint_index = json.loads(
        (
            REPO_ROOT / "docs/roadmap/QTT_PR_Blueprints_Index_PR83_to_PR224_v1_0.json"
        ).read_text(encoding="utf-8")
    )

    for text in (roadmap_readme, roadmap_md, blueprint_md):
        assert "PR116A" in text
        assert "does not unblock" in text or "does not unblock a gate" in text
        assert "does not create final readiness" in text
        assert "does not create runtime/live/order/profit/quantum-backend authority" in text
        assert "Future PRs must flip only one centralized gate state at a time" in text
        assert "PR numbers remain delivery labels only" in text

    for index in (roadmap_index, blueprint_index):
        overlays = index["corrective_control_plane_overlays"]
        pr116a = next(item for item in overlays if item["delivery_label"] == "PR116A")
        assert "does not unblock any gate" in pr116a["summary"]
        assert "create final readiness" in pr116a["summary"]
        assert "runtime/live/order/profit/quantum-backend authority" in pr116a["summary"]
        assert "one centralized gate state at a time" in pr116a["future_transition_rule"]


def test_registry_module_does_not_import_policy_and_has_no_runtime_side_effect_calls():
    registry_path = REPO_ROOT / "src/qtt/core/testing/qtt_active_non_sha_day1_gate_state_registry.py"
    source = registry_path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported_modules = {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    }
    imported_names = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }

    assert "qtt_final_readiness_dependency_policy" not in source
    assert "src.qtt.core.testing.qtt_final_readiness_dependency_policy" not in imported_names
    assert "qtt_final_readiness_dependency_policy" not in imported_modules
    forbidden_runtime_tokens = (
        "requests.",
        "urllib.",
        "subprocess.",
        "socket.",
        "open(",
        "Path(",
        "time.",
        "datetime.",
    )
    assert not any(token in source for token in forbidden_runtime_tokens)
