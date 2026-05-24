from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

import pytest

from src.qtt.stage1_prediction_markets.atomicrows_semantic_contract import constants as c
from src.qtt.stage1_prediction_markets.atomicrows_semantic_contract.fixtures import (
    build_fixture_collection,
)
from src.qtt.stage1_prediction_markets.atomicrows_semantic_contract.report import (
    build_index,
    build_report,
    evidence_snapshot,
)
from src.qtt.stage1_prediction_markets.atomicrows_semantic_contract.schema import (
    build_contract,
    build_json_schema,
)
from src.qtt.stage1_prediction_markets.atomicrows_semantic_contract import validator
from src.qtt.stage1_prediction_markets.atomicrows_semantic_contract.validator import (
    validate_contract_payload,
    validate_fixture_collection,
    validate_report_payload,
)
from tools import ci_branch_context


REPO_ROOT = Path(__file__).resolve().parents[2]
_CACHE: dict | None = None


def _outputs() -> dict:
    global _CACHE
    if _CACHE is None:
        evidence = evidence_snapshot(REPO_ROOT)
        contract = build_contract(evidence)
        report = build_report(REPO_ROOT)
        _CACHE = {
            "contract": contract,
            "index": build_index(report),
            "report": report,
            "schema": build_json_schema(),
            "fixture": build_fixture_collection(),
        }
    return _CACHE


def _contract() -> dict:
    return deepcopy(_outputs()["contract"])


def _report() -> dict:
    return deepcopy(_outputs()["report"])


def _contract_failures(mutator) -> set[str]:
    contract = _contract()
    mutator(contract)
    return set(validate_contract_payload(contract))


def _report_failures(mutator) -> set[str]:
    report = _report()
    mutator(report)
    return set(validate_report_payload(report).failures)


def _field(contract: dict, field_id: str) -> dict:
    for field in contract["fields"]:
        if field["field_id"] == field_id:
            return field
    raise AssertionError(field_id)


def _clear_ci_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for env_name in ("GITHUB_ACTIONS", "GITHUB_EVENT_NAME", "GITHUB_REF", "GITHUB_REF_NAME"):
        monkeypatch.delenv(env_name, raising=False)


def _mock_git_stdout(
    monkeypatch: pytest.MonkeyPatch,
    responses: dict[tuple[str, ...], tuple[int, str, str]],
) -> None:
    def fake_git_stdout(repo_root: Path, args: list[str]) -> tuple[int, str, str]:
        key = tuple(args)
        if key not in responses:
            raise AssertionError(f"unexpected git command: {args}")
        return responses[key]

    monkeypatch.setattr(validator, "_git_stdout", fake_git_stdout)


def _git_responses(
    *,
    branch: str = c.BRANCH,
    branch_rc: int = 0,
    base_rc: int = 0,
    ancestor_rc: int = 0,
) -> dict[tuple[str, ...], tuple[int, str, str]]:
    return {
        ("branch", "--show-current"): (branch_rc, branch, ""),
        ("cat-file", "-e", f"{c.BASELINE_CHECKPOINT}^{{commit}}"): (base_rc, "", ""),
        ("merge-base", "--is-ancestor", c.BASELINE_CHECKPOINT, "HEAD"): (
            ancestor_rc,
            "",
            "",
        ),
    }


def test_pr138_semantic_contract_contains_exactly_eight_required_field_groups() -> None:
    contract = _contract()
    assert contract["required_field_group_count"] == 8
    assert len(contract["field_groups"]) == 8
    assert validate_contract_payload(contract) == []


def test_pr138_semantic_contract_contains_exactly_fifty_nine_required_fields() -> None:
    contract = _contract()
    assert contract["required_field_count"] == 59
    assert len(contract["fields"]) == 59
    assert validate_contract_payload(contract) == []


def test_pr138_semantic_contract_contains_all_required_field_groups() -> None:
    group_ids = {group["field_group_id"] for group in _contract()["field_groups"]}
    assert group_ids == set(c.REQUIRED_FIELD_GROUP_IDS)


def test_pr138_semantic_contract_contains_all_required_fields() -> None:
    field_ids = {field["field_id"] for field in _contract()["fields"]}
    assert field_ids == set(c.REQUIRED_FIELD_IDS)


def test_pr138_field_group_membership_is_deterministic_and_unique() -> None:
    contract = _contract()
    expected = dict(c.REQUIRED_FIELDS_BY_GROUP)
    for group in contract["field_groups"]:
        assert tuple(group["fields"]) == expected[group["field_group_id"]]
    assert [field["field_ordinal"] for field in contract["fields"]] == list(range(1, 60))


def test_pr138_rejects_missing_required_field() -> None:
    failures = _contract_failures(
        lambda contract: contract.update(
            fields=[field for field in contract["fields"] if field["field_id"] != "row_id"]
        )
    )
    assert c.PR138_REASON_REQUIRED_FIELD_MISSING in failures


def test_pr138_rejects_missing_required_field_group() -> None:
    failures = _contract_failures(
        lambda contract: contract.update(
            field_groups=[
                group for group in contract["field_groups"] if group["field_group_id"] != "IDENTITY"
            ]
        )
    )
    assert c.PR138_REASON_REQUIRED_FIELD_GROUP_MISSING in failures


def test_pr138_rejects_duplicate_required_field() -> None:
    failures = _contract_failures(
        lambda contract: contract["fields"].append(deepcopy(_field(contract, "row_id")))
    )
    assert c.PR138_REASON_FIELD_DUPLICATE in failures


def test_pr138_rejects_duplicate_field_group() -> None:
    failures = _contract_failures(
        lambda contract: contract["field_groups"].append(deepcopy(contract["field_groups"][0]))
    )
    assert c.PR138_REASON_FIELD_GROUP_DUPLICATE in failures


def test_pr138_rejects_forbidden_venue_aliases_as_valid_values() -> None:
    failures = _contract_failures(
        lambda contract: _field(contract, "venue_scope")["allowed_market_scopes"].append(
            "FORECASTX"
        )
    )
    assert c.PR138_REASON_FORBIDDEN_VENUE_ALIAS in failures


def test_pr138_allows_forbidden_aliases_only_in_central_forbidden_alias_constants_and_negative_fixtures() -> None:
    assert set(c.FORBIDDEN_ALIASES) == {"FORECASTEX", "FORECASTX", "IBKR_FORECASTX", "forecastx"}
    valid_values = validator._string_values(
        {
            "contract": _contract(),
            "report": _report(),
            "schema": _outputs()["schema"],
        }
    )
    for alias in c.FORBIDDEN_ALIASES:
        assert alias not in valid_values
    fixture = build_fixture_collection()
    assert "FORECASTX" in json.dumps(fixture, sort_keys=True)


def test_pr138_preserves_forecastex_ibkr_canonical_identity() -> None:
    contract = _contract()
    assert c.CANONICAL_THIRD_VENUE == "FORECASTEX_IBKR"
    assert "FORECASTEX_IBKR" in contract["canonical_stage1_market_scopes"]
    assert "FORECASTEX_IBKR" in _report()["semantic_contract"]["canonical_stage1_market_scopes"]


def test_pr138_quantum_fields_are_static_metadata_only() -> None:
    contract = _contract()
    for field_id in (
        "quantum_applicability_class",
        "qubo_compatible_flag",
        "ising_compatible_flag",
        "qaoa_compatible_flag",
        "vqe_compatible_flag",
        "annealing_compatible_flag",
        "quantum_kernel_feature_map_compatible_flag",
        "quantum_backend_execution_allowed_flag",
    ):
        field = _field(contract, field_id)
        assert field["quantum_execution_created_by_field"] is False
        assert field["precomputed_snapshot_compatibility_class"] == (
            c.PRECOMPUTED_SNAPSHOT_COMPATIBILITY_CLASS
        )


def test_pr138_rejects_quantum_backend_execution_allowed_true() -> None:
    failures = _report_failures(
        lambda report: report["contract_level_default_flag_values"].update(
            quantum_backend_execution_allowed_flag=True
        )
    )
    assert c.PR138_REASON_QUANTUM_BACKEND_EXECUTION_FLAG_TRUE_FORBIDDEN in failures


def test_pr138_rejects_quantum_simulator_execution_claim() -> None:
    failures = _report_failures(
        lambda report: report.update(quantum_simulator_execution_created_by_pr138=True)
    )
    assert c.PR138_REASON_QUANTUM_SIMULATOR_EXECUTION_FORBIDDEN in failures


def test_pr138_rejects_quantum_optimizer_input_or_output_claim() -> None:
    input_failures = _report_failures(
        lambda report: report.update(quantum_optimizer_input_created_by_pr138=True)
    )
    output_failures = _report_failures(
        lambda report: report.update(quantum_optimizer_output_created_by_pr138=True)
    )
    assert c.PR138_REASON_QUANTUM_OPTIMIZER_INPUT_FORBIDDEN in input_failures
    assert c.PR138_REASON_QUANTUM_OPTIMIZER_INPUT_FORBIDDEN in output_failures


def test_pr138_rejects_live_use_allowed_true() -> None:
    failures = _report_failures(
        lambda report: report["contract_level_default_flag_values"].update(live_use_allowed_flag=True)
    )
    assert c.PR138_REASON_LIVE_USE_FLAG_TRUE_FORBIDDEN in failures


def test_pr138_rejects_order_authority_created_true() -> None:
    failures = _report_failures(
        lambda report: report["contract_level_default_flag_values"].update(
            order_authority_created_flag=True
        )
    )
    assert c.PR138_REASON_ORDER_AUTHORITY_FLAG_TRUE_FORBIDDEN in failures


def test_pr138_rejects_profit_evidence_created_true() -> None:
    failures = _report_failures(
        lambda report: report["contract_level_default_flag_values"].update(
            profit_evidence_created_flag=True
        )
    )
    assert c.PR138_REASON_PROFIT_EVIDENCE_FLAG_TRUE_FORBIDDEN in failures


def test_pr138_rejects_external_fact_authority_true_without_accepted_source_packet() -> None:
    failures = _report_failures(
        lambda report: report["contract_level_default_flag_values"].update(
            external_fact_authority_flag=True
        )
    )
    assert (
        c.PR138_REASON_EXTERNAL_FACT_AUTHORITY_TRUE_FORBIDDEN_WITHOUT_ACCEPTED_SOURCE_PACKET
        in failures
    )


def test_pr138_inventory_records_include_authority_boundary_metadata() -> None:
    for field in _contract()["fields"]:
        assert field["authority_boundary"] == c.AUTHORITY_BOUNDARY


def test_pr138_inventory_records_include_future_pr_phase_metadata() -> None:
    for field in _contract()["fields"]:
        assert field["future_enrichment_phase"] in c.FUTURE_PR_PHASE_VALUES


def test_pr138_inventory_records_include_crosswalk_market_index_and_command_matrix_trace_or_blocker() -> None:
    for field in _contract()["fields"]:
        assert field["route_triage_trace"]["trace_state"] == "TRACE_CONSUMED_READ_ONLY"
        assert field["full_master_plan_section_crosswalk_trace"]["trace_state"] == (
            "TRACE_CONSUMED_READ_ONLY"
        )
        assert field["market_specific_section_index_trace"]["trace_state"] == (
            "TRACE_CONSUMED_READ_ONLY"
        )
        assert field["command_action_matrix_trace"]["trace_state"] == "TRACE_CONSUMED_READ_ONLY"


def test_pr138_report_declares_bundle_not_mutated() -> None:
    assert _report()["atomicrows_bundle_mutated_by_pr138"] is False


def test_pr138_report_declares_row_family_sources_not_mutated() -> None:
    assert _report()["row_family_sources_mutated_by_pr138"] is False


def test_pr138_report_declares_bundle_builder_not_mutated() -> None:
    assert _report()["bundle_builder_mutated_by_pr138"] is False


def test_pr138_report_declares_final_readiness_not_created() -> None:
    report = _report()
    assert report["final_readiness_gate_created_by_pr138"] is False
    assert report["final_readiness_claimed_by_pr138"] is False


def test_pr138_report_declares_day1_live_readiness_not_created() -> None:
    assert _report()["day1_live_readiness_claimed_by_pr138"] is False


def test_pr138_report_declares_no_runtime_live_order_profit_quantum_authority() -> None:
    report = _report()
    for field in (
        "live_order_authority_created_by_pr138",
        "order_execution_created_by_pr138",
        "profit_evidence_created_by_pr138",
        "quantum_execution_created_by_pr138",
        "quantum_simulator_execution_created_by_pr138",
        "quantum_optimizer_input_created_by_pr138",
        "quantum_optimizer_output_created_by_pr138",
        "quantum_advantage_claimed_by_pr138",
        "runtime_cash_authority_created_by_pr138",
    ):
        assert report[field] is False


def test_pr138_report_declares_no_scoring_ranking_arbitration_output() -> None:
    assert _report()["scoring_ranking_arbitration_output_created_by_pr138"] is False


def test_pr138_report_declares_no_trading_signal() -> None:
    assert _report()["trading_signal_created_by_pr138"] is False


def test_pr138_reason_codes_are_centralized() -> None:
    assert len(c.REASON_CODES) == len(set(c.REASON_CODES))
    contract = _contract()
    fixture = build_fixture_collection()
    failures = validate_fixture_collection(
        fixture,
        valid_contract=contract,
        valid_report=_report(),
    )
    assert failures == []


def test_pr138_gate_ci_detached_head_relaxes_branch_only(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_ci_env(monkeypatch)
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setenv("GITHUB_EVENT_NAME", "pull_request")
    monkeypatch.setenv("GITHUB_REF", "refs/pull/138/merge")
    monkeypatch.setenv("GITHUB_REF_NAME", "138/merge")
    _mock_git_stdout(
        monkeypatch,
        _git_responses(branch="", branch_rc=0, base_rc=0, ancestor_rc=0),
    )
    outcome = validate_report_payload(_report(), repo_root=REPO_ROOT, enforce_environment=True)
    assert outcome.ok, outcome.failures
    assert c.PR138_REASON_CI_DETACHED_HEAD_RELAXATION_BRANCH_ONLY in outcome.receipts


def test_pr138_gate_ci_detached_head_skips_shallow_fetch_baseline_object_absence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _clear_ci_env(monkeypatch)
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setenv("GITHUB_EVENT_NAME", "pull_request")
    monkeypatch.setenv("GITHUB_REF", "refs/pull/140/merge")
    monkeypatch.setenv("GITHUB_REF_NAME", "140/merge")
    _mock_git_stdout(
        monkeypatch,
        _git_responses(branch="", branch_rc=0, base_rc=128, ancestor_rc=128),
    )
    outcome = validate_report_payload(_report(), repo_root=REPO_ROOT, enforce_environment=True)
    assert outcome.ok, outcome.failures
    assert c.PR138_REASON_CI_DETACHED_HEAD_RELAXATION_BRANCH_ONLY in outcome.receipts


def test_pr138_gate_ci_main_push_skips_pr_branch_and_shallow_ancestry_requirements(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _clear_ci_env(monkeypatch)
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setenv("GITHUB_EVENT_NAME", "push")
    monkeypatch.setenv("GITHUB_REF", "refs/heads/main")
    monkeypatch.setenv("GITHUB_REF_NAME", "main")
    _mock_git_stdout(
        monkeypatch,
        _git_responses(branch="main", branch_rc=0, base_rc=128, ancestor_rc=128),
    )
    outcome = validate_report_payload(_report(), repo_root=REPO_ROOT, enforce_environment=True)
    assert outcome.ok, outcome.failures
    assert c.PR138_REASON_CI_MAIN_PUSH_RELAXATION_BRANCH_AND_ANCESTRY in outcome.receipts


def test_pr138_gate_local_mainline_continuation_preserves_baseline_check(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _clear_ci_env(monkeypatch)
    _mock_git_stdout(
        monkeypatch,
        _git_responses(branch="main", branch_rc=0, base_rc=0, ancestor_rc=0),
    )

    outcome = validate_report_payload(
        _report(),
        repo_root=REPO_ROOT,
        enforce_environment=True,
    )

    assert outcome.ok, outcome.failures
    assert c.PR138_REASON_BRANCH_MISMATCH not in outcome.failures
    assert (
        ci_branch_context.DOWNSTREAM_ROADMAP_BRANCH_VALIDATION_MODE_MARKER
        not in outcome.receipts
    )

    _mock_git_stdout(
        monkeypatch,
        _git_responses(branch="main", branch_rc=0, base_rc=0, ancestor_rc=1),
    )
    stale_outcome = validate_report_payload(
        _report(),
        repo_root=REPO_ROOT,
        enforce_environment=True,
    )

    assert not stale_outcome.ok
    assert c.PR138_REASON_BRANCH_MISMATCH not in stale_outcome.failures
    assert c.PR138_REASON_LOCAL_BASELINE_NOT_DESCENDANT in stale_outcome.failures


def test_pr138_gate_same_pr_repair_branch_preserves_baseline_check(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _clear_ci_env(monkeypatch)
    _mock_git_stdout(
        monkeypatch,
        _git_responses(
            branch="repair/pr138-branch-context-mainline-normalization",
            branch_rc=0,
            base_rc=0,
            ancestor_rc=0,
        ),
    )

    outcome = validate_report_payload(
        _report(),
        repo_root=REPO_ROOT,
        enforce_environment=True,
    )

    assert outcome.ok, outcome.failures
    assert c.PR138_REASON_BRANCH_MISMATCH not in outcome.failures
    assert (
        ci_branch_context.DOWNSTREAM_ROADMAP_BRANCH_VALIDATION_MODE_MARKER
        not in outcome.receipts
    )


def test_pr138_gate_local_wrong_branch_fails_closed_with_branch_mismatch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _clear_ci_env(monkeypatch)
    _mock_git_stdout(
        monkeypatch,
        _git_responses(branch="wrong-pr138-branch", base_rc=0, ancestor_rc=0),
    )

    outcome = validate_report_payload(
        _report(),
        repo_root=REPO_ROOT,
        enforce_environment=True,
    )

    assert not outcome.ok
    assert c.PR138_REASON_BRANCH_MISMATCH in outcome.failures
    assert c.PR138_REASON_LOCAL_BASELINE_NOT_DESCENDANT not in outcome.failures
    assert outcome.receipts == ()


def test_pr138_gate_local_downstream_pr140_branch_context_passes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _clear_ci_env(monkeypatch)
    _mock_git_stdout(
        monkeypatch,
        _git_responses(
            branch="pr140-atomicrows-semantic-field-coverage-enrichment-plan",
            base_rc=0,
            ancestor_rc=0,
        ),
    )

    outcome = validate_report_payload(
        _report(),
        repo_root=REPO_ROOT,
        enforce_environment=True,
    )

    assert outcome.ok, outcome.failures
    assert (
        ci_branch_context.DOWNSTREAM_ROADMAP_BRANCH_VALIDATION_MODE_MARKER
        in outcome.receipts
    )


def test_pr138_gate_local_repair_branch_is_not_downstream_pr140_context(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _clear_ci_env(monkeypatch)
    _mock_git_stdout(
        monkeypatch,
        _git_responses(
            branch="repair/pr140-atomicrows-semantic-field-coverage-enrichment-plan",
            base_rc=0,
            ancestor_rc=0,
        ),
    )

    outcome = validate_report_payload(
        _report(),
        repo_root=REPO_ROOT,
        enforce_environment=True,
    )

    assert not outcome.ok
    assert c.PR138_REASON_BRANCH_MISMATCH in outcome.failures
    assert (
        ci_branch_context.DOWNSTREAM_ROADMAP_BRANCH_VALIDATION_MODE_MARKER
        not in outcome.receipts
    )


def test_pr138_gate_local_requires_descendant_of_d1bce40_or_owner_verified_sandbox_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _clear_ci_env(monkeypatch)
    _mock_git_stdout(monkeypatch, _git_responses(base_rc=0, ancestor_rc=1))
    outcome = validate_report_payload(_report(), repo_root=REPO_ROOT, enforce_environment=True)
    assert not outcome.ok
    assert c.PR138_REASON_LOCAL_BASELINE_NOT_DESCENDANT in outcome.failures

    fallback_report = _report()
    fallback_report["owner_verified_baseline_receipt_consumed"] = True
    fallback_report["sandbox_bootstrap_fallback_used"] = True
    fallback_outcome = validate_report_payload(
        fallback_report,
        repo_root=REPO_ROOT,
        enforce_environment=True,
    )
    assert fallback_outcome.ok, fallback_outcome.failures


def test_pr138_does_not_edit_master_plan() -> None:
    failures = validator._protected_diff_failures_for_paths(
        ["docs/master_plan/QTT_MasterPlan_Current.md"]
    )
    assert c.PR138_REASON_MASTER_PLAN_EDIT_FORBIDDEN in failures


def test_pr138_does_not_mutate_atomicrows_bundle() -> None:
    failures = validator._protected_diff_failures_for_paths(
        [c.ATOMICROWS_BUNDLE_PATH.as_posix()]
    )
    assert c.PR138_REASON_BUNDLE_MUTATION_FORBIDDEN in failures


def test_pr138_does_not_mutate_row_family_sources() -> None:
    failures = validator._protected_diff_failures_for_paths(
        ["docs/master_plan/atomic_rows/pr98_row_family_sources/001_signal_features.source.jsonl"]
    )
    assert c.PR138_REASON_ROW_FAMILY_SOURCE_MUTATION_FORBIDDEN in failures


def test_pr138_does_not_mutate_bundle_builder() -> None:
    failures = validator._protected_diff_failures_for_paths(["tools/build_atomicrows_bundle.py"])
    assert c.PR138_REASON_BUILDER_MUTATION_FORBIDDEN in failures


def test_pr138_does_not_introduce_atomicrows_bundle_sha_sidecar_reference_in_pr138_diff_scope() -> None:
    assert _report()["new_atomicrows_bundle_sidecar_reference_created_by_pr138"] is False
    fixture = build_fixture_collection()
    sidecar_fixture = [
        item
        for item in fixture["fixtures"]
        if item["fixture_id"]
        == "invalid_new_atomicrows_bundle_sidecar_reference_in_pr138_artifact_or_diff_scope"
    ][0]
    failures = validate_fixture_collection(
        {"fixtures": [sidecar_fixture]},
        valid_contract=_contract(),
        valid_report=_report(),
    )
    assert failures == []


def test_pr138_does_not_create_qtt_generated_cryptographic_authority() -> None:
    assert _report()["qtt_cryptographic_authority_created_by_pr138"] is False
    failures = _report_failures(
        lambda report: report.update(qtt_generated_cryptographic_authority_field=True)
    )
    assert c.PR138_REASON_QTT_GENERATED_CRYPTOGRAPHIC_AUTHORITY_FORBIDDEN in failures


def test_pr138_hot_path_boundary_excludes_forbidden_runtime_dependencies() -> None:
    assert tuple(_report()["hot_path_forbidden_dependencies"]) == c.HOT_PATH_FORBIDDEN_DEPENDENCIES


def test_pr138_handoff_lists_pr139_pr140_pr141_pr142_as_next_required_prs() -> None:
    assert _report()["next_required_prs"] == ["PR139", "PR140", "PR141", "PR142"]


def test_pr138_uses_d1bce40_as_only_baseline_checkpoint() -> None:
    assert _contract()["baseline_checkpoint"] == "d1bce40"
    assert _report()["baseline_checkpoint"] == "d1bce40"
    failures = _report_failures(
        lambda report: report.update(baseline_checkpoint="STALE_NON_D1BCE40_BASELINE_PLACEHOLDER")
    )
    assert c.PR138_REASON_OLDER_BASELINE_CHECKPOINT_REFERENCE_FORBIDDEN in failures


def test_pr138_generated_report_consumes_required_static_evidence() -> None:
    report = _report()
    evidence = evidence_snapshot(REPO_ROOT)
    assert report["pr137r_evidence_consumed_read_only"] is True
    assert report["pr137l_evidence_consumed_read_only"] is True
    assert report["route_triage_evidence_consumed_read_only"] is True
    assert report["full_master_plan_section_crosswalk_consumed_read_only"] is True
    assert report["market_specific_section_indexes_consumed_read_only"] is True
    assert report["command_action_matrix_consumed_read_only"] is True
    assert evidence["pr137r_state"]["row_count_value"] == 4183
    assert evidence["pr137r_semantic_missing_field_count"] > 0
