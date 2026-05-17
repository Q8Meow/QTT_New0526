from __future__ import annotations

import copy
import json
from pathlib import Path

from src.qtt.core.testing import atomicrows_sha_system_dormancy_state as sha_state
from src.qtt.core.testing import qtt_final_readiness_dependency_policy as readiness_policy
from tools import validate_atomicrows_bundle_sha_freeze_authority_gate as sha_freeze_gate
from tools import validate_atomicrows_sha_system_dormancy_state_contract as validator


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


def test_sha_dormancy_contract_schema_and_central_state_are_current():
    contract = _contract()

    assert validator.validate_contract_payload(contract, _schema()) == []
    assert contract["contract_id"] == validator.CONTRACT_ID
    assert (
        sha_state.get_atomicrows_sha_system_dormancy_state()
        == "SHA_SYSTEM_DORMANT_NON_PARTICIPATING_OWNER_CONTROLLED"
    )
    assert (
        sha_state.CURRENT_ATOMICROWS_SHA_SYSTEM_DORMANCY_STATE
        == sha_state.EXPECTED_CURRENT_ATOMICROWS_SHA_SYSTEM_DORMANCY_STATE
    )
    assert set(sha_state.ATOMICROWS_SHA_SYSTEM_DORMANCY_STATES) == {
        "SHA_SYSTEM_DORMANT_NON_PARTICIPATING_OWNER_CONTROLLED",
        "SHA_SYSTEM_REACTIVATION_OWNER_REQUESTED",
        "SHA_SYSTEM_ACTIVE_OWNER_APPROVED",
    }


def test_sha_generation_freeze_authority_and_reactivation_remain_disabled():
    contract = _contract()

    assert sha_state.is_sha_system_dormant() is True
    assert sha_state.is_sha_system_non_participating_for_final_readiness() is True
    assert sha_state.is_sha_generation_allowed() is False
    assert sha_state.is_sha_freeze_authority_allowed() is False
    assert contract["sha_reactivation_performed_in_this_pr"] is False
    assert contract["sha_reactivation_requires_future_owner_approved_pr"] is True
    assert contract["sha_reactivation_is_not_required_for_day1_final_readiness"] is True
    sha_state.assert_sha_system_dormant_non_participating()
    sha_state.assert_sha_generation_disabled()
    sha_state.assert_sha_freeze_authority_disabled()
    sha_state.assert_sha_reactivation_not_performed()
    sha_state.assert_sha_reactivation_requires_future_owner_approved_pr()


def test_sha_dormancy_is_neither_final_readiness_nor_final_readiness_blocker():
    contract = _contract()
    report = _report()

    assert contract["sha_dormancy_is_not_final_readiness"] is True
    assert contract["sha_dormancy_is_not_final_readiness_blocker"] is True
    assert report["sha_dormancy_is_not_final_readiness"] is True
    assert report["sha_dormancy_is_not_final_readiness_blocker"] is True
    assert readiness_policy.is_sha_required_for_final_readiness() is False
    assert readiness_policy.is_sha_dormancy_a_final_readiness_blocker() is False
    sha_state.assert_sha_dormancy_does_not_create_final_readiness()
    sha_state.assert_sha_dormancy_does_not_block_final_readiness()


def test_atomicrows_bundle_remains_present_and_sha_absence_is_non_authoritative():
    report = _report()
    bundle_path = REPO_ROOT / validator.CANONICAL_ATOMICROWS_BUNDLE
    sha_path = REPO_ROOT / validator.CANONICAL_ATOMICROWS_BUNDLE_SHA

    assert bundle_path.exists()
    assert sum(1 for _ in bundle_path.open(encoding="utf-8")) == 4183
    assert not sha_path.exists()
    assert report["atomicrows_bundle_exists"] is True
    assert report["atomicrows_bundle_line_count"] == 4183
    assert report["atomicrows_bundle_sha256_exists"] is False
    assert _contract()["atomicrows_bundle_sha256_created_by_this_pr"] is False
    assert _contract()["atomicrows_bundle_sha256_absence_is_not_final_readiness_blocker"] is True
    assert _contract()["atomicrows_bundle_sha256_presence_is_not_final_readiness_evidence"] is True


def test_research_candidate_velocity_and_quantum_metadata_additions_are_unblocked():
    contract = _contract()
    report = _report()

    assert contract["sha_dormancy_does_not_block_research_candidate_intake"] is True
    assert contract["sha_dormancy_does_not_block_future_parameter_additions"] is True
    assert contract["sha_dormancy_does_not_block_future_algorithm_additions"] is True
    assert contract["sha_dormancy_does_not_block_future_quantum_metadata_additions"] is True
    assert (
        contract[
            "sha_dormancy_does_not_block_qubo_qaoa_vqe_ising_annealing_metadata_additions"
        ]
        is True
    )
    assert report["research_candidate_intake_blocked_by_sha_dormancy"] is False
    assert report["future_parameter_additions_blocked_by_sha_dormancy"] is False
    assert report["future_algorithm_additions_blocked_by_sha_dormancy"] is False
    assert report["future_quantum_metadata_additions_blocked_by_sha_dormancy"] is False


def test_authority_execution_evidence_and_bug_free_claims_remain_false():
    contract = _contract()
    report = _report()

    for field in validator.FORBIDDEN_FALSE_FIELDS:
        assert contract[field] is False
    assert (
        report[
            "runtime_live_order_source_connector_runtime_cash_backend_profit_authority_created"
        ]
        is False
    )
    assert report["replay_paper_optimizer_neural_quantum_backend_execution_created"] is False
    assert report["profit_latency_execution_quantum_advantage_evidence_claimed"] is False
    assert contract["source_facts_accepted_by_this_pr"] is False
    assert contract["connector_semantics_bound_by_this_pr"] is False
    assert contract["runtime_cash_receipts_created_by_this_pr"] is False
    assert contract["live_trading_authority_created_by_this_pr"] is False
    assert contract["bug_free_status_claimed_by_this_pr"] is False


def test_schema_and_custom_validation_reject_sha_authority_and_claim_creation():
    schema = _schema()
    contract = copy.deepcopy(_contract())
    contract["sha_generation_allowed"] = True
    _assert_failure_contains(
        validator.validate_contract_payload(contract, schema),
        "sha_generation_allowed",
    )

    contract = copy.deepcopy(_contract())
    contract[
        "current_pr_creates_runtime_live_order_source_connector_runtime_cash_backend_profit_authority"
    ] = True
    _assert_failure_contains(
        validator.validate_contract_payload(contract, schema),
        "current_pr_creates_runtime_live_order_source_connector_runtime_cash_backend_profit_authority",
    )

    contract = copy.deepcopy(_contract())
    contract["bug_free_status_claimed_by_this_pr"] = True
    _assert_failure_contains(
        validator.validate_contract_payload(contract, schema),
        "bug_free_status_claimed_by_this_pr",
    )


def test_validator_emits_success_marker_and_does_not_create_sha(tmp_path, capsys):
    sha_path = REPO_ROOT / validator.CANONICAL_ATOMICROWS_BUNDLE_SHA

    assert not sha_path.exists()
    assert (
        validator.main(
            [
                "--repo-root",
                str(REPO_ROOT),
                "--report-out",
                str(tmp_path / "sha_dormancy.report.json"),
            ]
        )
        == 0
    )
    output = [line.strip() for line in capsys.readouterr().out.splitlines() if line.strip()]
    assert output == [validator.SUCCESS_MARKER]
    assert not sha_path.exists()
    report = json.loads((tmp_path / "sha_dormancy.report.json").read_text(encoding="utf-8"))
    assert report["result_marker"] == validator.SUCCESS_MARKER


def test_existing_sha_freeze_gate_consumes_central_dormancy_policy(tmp_path):
    result = sha_freeze_gate.validate(
        repo_root=REPO_ROOT,
        output_path=tmp_path / "sha_freeze_gate.report.json",
    )

    assert result.ok is True, result.failures
    assert result.report is not None
    report = result.report
    assert (
        report["sha_system_dormancy_state"]
        == sha_state.CURRENT_ATOMICROWS_SHA_SYSTEM_DORMANCY_STATE
    )
    assert report["sha_generation_allowed"] is sha_state.is_sha_generation_allowed()
    assert (
        report["sha_freeze_authority_allowed"]
        is sha_state.is_sha_freeze_authority_allowed()
    )
    assert report["sha_required_for_final_readiness"] is False
    assert report["sha_absence_is_final_readiness_blocker"] is False
    assert report["sha_presence_is_final_readiness_evidence"] is False
    assert report["final_readiness_created"] is False
    assert "ATOMICROWS_SHA_FREEZE_BLOCKED_SHA_FILE_MUST_NOT_BE_CREATED" not in set(
        report["blocked_reason_codes"]
    )
