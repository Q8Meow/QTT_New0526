from __future__ import annotations

import copy
import json
from pathlib import Path

from src.qtt.core.testing import atomicrows_sha_system_dormancy_state as sha_state
from src.qtt.core.testing import qtt_active_non_sha_day1_gate_state_registry as gate_registry
from src.qtt.core.testing import qtt_final_readiness_dependency_policy as policy
from tools import validate_atomicrows_bundle_sha_freeze_authority_gate as sha_freeze_gate
from tools import validate_qtt_final_readiness_dependency_policy_contract as validator


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


def test_dependency_policy_contract_schema_and_central_state_are_current():
    contract = _contract()

    assert validator.validate_contract_payload(contract, _schema()) == []
    assert contract["contract_id"] == validator.CONTRACT_ID
    assert (
        policy.get_qtt_final_readiness_dependency_policy_state()
        == "FINAL_READINESS_DEPENDENCY_POLICY_ACTIVE_NON_SHA_GATES_ONLY"
    )
    assert (
        policy.CURRENT_QTT_FINAL_READINESS_DEPENDENCY_POLICY_STATE
        == policy.EXPECTED_CURRENT_QTT_FINAL_READINESS_DEPENDENCY_POLICY_STATE
    )
    assert set(policy.QTT_FINAL_READINESS_DEPENDENCY_POLICY_STATES) == {
        "FINAL_READINESS_DEPENDENCY_POLICY_ACTIVE_NON_SHA_GATES_ONLY",
        "FINAL_READINESS_DEPENDENCY_POLICY_OWNER_SHA_RECONSIDERATION_REQUESTED",
        "FINAL_READINESS_DEPENDENCY_POLICY_SHA_REACTIVATED_AFTER_OWNER_APPROVAL",
    }


def test_sha_is_not_required_not_blocking_and_not_readiness_evidence():
    contract = _contract()
    report = _report()

    assert sha_state.is_sha_system_non_participating_for_final_readiness() is True
    assert policy.is_sha_required_for_final_readiness() is False
    assert policy.is_sha_dormancy_a_final_readiness_blocker() is False
    assert contract["sha_required_for_final_readiness"] is False
    assert contract["sha_dormancy_is_final_readiness_blocker"] is False
    assert contract["sha_absence_is_final_readiness_blocker"] is False
    assert contract["sha_presence_is_final_readiness_evidence"] is False
    assert contract["sha_reactivation_required_for_day1_launch"] is False
    assert report["sha_required_for_final_readiness"] is False
    assert report["sha_dormancy_is_final_readiness_blocker"] is False
    assert report["sha_absence_is_final_readiness_blocker"] is False
    assert report["sha_presence_is_final_readiness_evidence"] is False
    assert report["sha_reactivation_required_for_day1_launch"] is False


def test_active_dependencies_are_declared_exactly_and_exclude_sha_terms():
    contract = _contract()
    dependencies = policy.get_active_non_sha_final_readiness_dependencies()

    assert list(dependencies) == contract["active_non_sha_final_readiness_dependencies"]
    assert dependencies == gate_registry.get_active_non_sha_day1_gate_ids()
    assert (
        policy.ACTIVE_NON_SHA_FINAL_READINESS_DEPENDENCIES
        is gate_registry.QTT_ACTIVE_NON_SHA_DAY1_GATE_IDS
    )
    assert set(dependencies) >= {
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
        "EXECUTION_RECEIPT_BOUNDARY",
        "QUANTUM_BACKEND_AUTHORITY_GATE",
        "QUANTUM_ADVANTAGE_NO_CLAIM_GATE",
        "PROFIT_NO_CLAIM_GATE",
        "LATENCY_AND_EXECUTION_EVIDENCE_NO_FABRICATION_GATE",
    }
    assert not any(validator._contains_sha_dependency(item) for item in dependencies)
    assert _report()["active_non_sha_final_readiness_dependencies_include_sha"] is False
    assert _report()["active_gate_ids_match_gate_state_registry"] is True
    policy.assert_active_dependencies_consume_gate_registry()


def test_dependency_policy_records_central_registry_as_gate_state_source():
    contract = _contract()
    report = _report()

    assert (
        contract["active_gate_state_registry_contract_path"]
        == "docs/master_plan/launch/QttActiveNonShaDay1GateStateRegistryContract.yaml"
    )
    assert contract["active_gate_state_registry_required"] is True
    assert contract["active_gate_state_registry_is_source_of_day1_gate_state"] is True
    assert (
        contract[
            "final_readiness_dependency_policy_does_not_hardcode_gate_states_independently"
        ]
        is True
    )
    assert (
        contract[
            "final_readiness_dependency_policy_consumes_or_validates_registry_gate_ids"
        ]
        is True
    )
    for field in validator.REQUIRED_TRUE_FIELDS:
        assert contract[field] is True
        assert report[field] is True


def test_excluded_subsystems_include_sha_dormancy_and_readiness_can_ignore_sha():
    contract = _contract()
    report = _report()

    assert policy.get_excluded_non_participating_final_readiness_subsystems() == (
        "SHA_DORMANCY_SYSTEM",
    )
    assert contract["excluded_non_participating_subsystems"] == ["SHA_DORMANCY_SYSTEM"]
    assert report["excluded_non_participating_subsystems"] == ["SHA_DORMANCY_SYSTEM"]
    assert (
        contract[
            "final_readiness_may_be_authorized_without_sha_if_all_active_non_sha_gates_pass_and_owner_approves"
        ]
        is True
    )
    assert (
        report[
            "final_readiness_may_be_authorized_without_sha_if_all_active_non_sha_gates_pass_and_owner_approves"
        ]
        is True
    )
    policy.assert_day1_final_readiness_must_ignore_sha_dormancy_when_non_sha_gates_pass()


def test_current_pr_creates_no_final_readiness_launch_or_runtime_authority():
    contract = _contract()
    report = _report()

    for field in validator.FORBIDDEN_FALSE_FIELDS:
        assert contract[field] is False
    assert report["current_pr_creates_final_readiness"] is False
    assert report["current_pr_creates_day1_launch_authority"] is False
    assert (
        report[
            "runtime_live_order_source_connector_runtime_cash_backend_profit_authority_created"
        ]
        is False
    )
    assert report["replay_paper_optimizer_neural_quantum_backend_execution_created"] is False
    assert report["profit_latency_execution_quantum_advantage_evidence_claimed"] is False
    policy.assert_current_pr_does_not_create_final_readiness()


def test_schema_and_custom_validation_reject_sha_dependencies_and_authority():
    schema = _schema()
    contract = copy.deepcopy(_contract())
    contract["sha_required_for_final_readiness"] = True
    _assert_failure_contains(
        validator.validate_contract_payload(contract, schema),
        "sha_required_for_final_readiness",
    )

    contract = copy.deepcopy(_contract())
    contract["active_non_sha_final_readiness_dependencies"] = [
        *contract["active_non_sha_final_readiness_dependencies"],
        "SHA_FREEZE_AUTHORITY_GATE",
    ]
    _assert_failure_contains(
        validator.validate_contract_payload(contract, schema),
        "active dependency must be non-SHA only",
    )

    contract = copy.deepcopy(_contract())
    contract["current_pr_creates_day1_launch_authority"] = True
    _assert_failure_contains(
        validator.validate_contract_payload(contract, schema),
        "current_pr_creates_day1_launch_authority",
    )


def test_validator_emits_success_marker_and_report(tmp_path, capsys):
    report_path = tmp_path / "final_readiness_dependency_policy.report.json"

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


def test_existing_sha_freeze_gate_consumes_central_final_readiness_policy(tmp_path):
    result = sha_freeze_gate.validate(
        repo_root=REPO_ROOT,
        output_path=tmp_path / "sha_freeze_gate.report.json",
    )

    assert result.ok is True, result.failures
    assert result.report is not None
    report = result.report
    assert (
        report["final_readiness_dependency_policy_state"]
        == policy.CURRENT_QTT_FINAL_READINESS_DEPENDENCY_POLICY_STATE
    )
    assert report["sha_required_for_final_readiness"] is False
    assert report["sha_dormancy_is_final_readiness_blocker"] is False
    assert report["sha_absence_is_final_readiness_blocker"] is False
    assert report["sha_presence_is_final_readiness_evidence"] is False
    assert report["final_readiness_created"] is False
    assert report["downstream_status"]["roadmap_pr101_final_readiness_gate"] == (
        "NOT_CREATED_BY_THIS_PR_ACTIVE_NON_SHA_GATES_CONTROL_DAY1_FINAL_READINESS"
    )
