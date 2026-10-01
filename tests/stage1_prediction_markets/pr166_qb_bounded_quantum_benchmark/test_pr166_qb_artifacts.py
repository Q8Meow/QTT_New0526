from __future__ import annotations

from copy import deepcopy

from src.qtt.stage1_prediction_markets.pr166_qb_bounded_quantum_benchmark import constants as c
from src.qtt.stage1_prediction_markets.pr166_qb_bounded_quantum_benchmark.validator import validate_artifacts

from .helpers import REPO_ROOT, assert_report_contract, records, summary


def test_pr166_qb_validator_passes_generated_artifacts():
    result = validate_artifacts(REPO_ROOT)
    assert result.ok, result.failures


def test_pr166_qb_consumes_expected_upstream_handoffs_and_counts():
    final = summary()
    assert final["consumed_pr166_qb_handoff_rows"] == 559
    assert final["input_record_counts"]["PR166_Q_PR166_QB_BoundedNonLiveQuantumBenchmarkHandoff.report.json"] == 559
    assert final["input_record_counts"]["PR166_Q_UniversalArtifactConsumerMap.report.json"] == 685
    assert_report_contract("PR166_QB_Eligibility.report.json", 559)
    assert_report_contract("PR166_QB_RaceArb.report.json", 559)


def test_pr166_qb_budget_subset_is_capped_and_deterministic():
    final = summary()
    subset = [row for row in records("PR166_QB_SubsetSelection.report.json") if row["benchmark_subset_flag"]]
    assert len(subset) == 64
    assert final["benchmark_subset_count"] == 64
    assert all(row["iterations_used"] <= c.BENCHMARK_CAPS["max_optimizer_iterations_default_ci"] for row in subset)
    assert all(row["samples_or_reads_used"] <= c.BENCHMARK_CAPS["max_samples_or_reads_default_ci"] for row in subset)
    assert all(row["seed_count"] <= c.BENCHMARK_CAPS["max_random_seeds_default_ci"] for row in subset)
    by_family = {}
    for row in subset:
        by_family[row["model_family"]] = by_family.get(row["model_family"], 0) + 1
    assert all(count <= c.BENCHMARK_CAPS["max_rows_per_family_default_ci"] for count in by_family.values())
    assert [row["deterministic_sort_key"] for row in subset] == sorted(row["deterministic_sort_key"] for row in subset)

    # Exercise the native budget predicate inside this existing grouped test.
    from copy import deepcopy
    from src.qtt.stage1_prediction_markets.pr166_qb_bounded_quantum_benchmark.validator import _validate_budget
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import (
        ContractValidationError, NumericDomainError, ReasonCode,
    )
    budget_key = "PR166_QB_BudgetPolicy.report.json"
    rows_key = "PR166_QB_SubsetSelection.report.json"
    baseline = {budget_key: [{"actual_benchmark_subset_size": len(subset)}], rows_key: deepcopy(subset)}
    failures = []
    _validate_budget(baseline, failures)
    assert failures == []
    fields = (
        ("iterations_used", "max_optimizer_iterations_default_ci", "ITERATION_CAP_EXCEEDED"),
        ("samples_or_reads_used", "max_samples_or_reads_default_ci", "SAMPLE_CAP_EXCEEDED"),
        ("seed_count", "max_random_seeds_default_ci", "SEED_CAP_EXCEEDED"),
        ("problem_variable_count", "max_problem_variables_default_ci", "VARIABLE_CAP_EXCEEDED"),
    )
    for field, cap_field, prefix in fields:
        for value in (-1, True, False, 1.0, "1", None, float("nan"), float("inf")):
            case = deepcopy(baseline)
            case[rows_key][0][field] = value
            try:
                _validate_budget(case, [])
            except NumericDomainError as exc:
                assert exc.reason_code in {ReasonCode.INVALID_NUMERIC_INPUT, ReasonCode.OUT_OF_DOMAIN}
            else:
                raise AssertionError(f"invalid resource count accepted: {field}")
        case = deepcopy(baseline)
        del case[rows_key][0][field]
        try:
            _validate_budget(case, [])
        except NumericDomainError as exc:
            assert exc.reason_code == ReasonCode.INVALID_NUMERIC_INPUT
        else:
            raise AssertionError(f"missing resource count accepted: {field}")
        for value in (0, c.BENCHMARK_CAPS[cap_field]):
            case = deepcopy(baseline)
            case[rows_key][0][field] = value
            failures = []
            _validate_budget(case, failures)
            assert failures == []
        case = deepcopy(baseline)
        case[rows_key][0][field] = c.BENCHMARK_CAPS[cap_field] + 1
        failures = []
        _validate_budget(case, failures)
        assert failures == [f"{prefix}::{case[rows_key][0].get('row_id')}"]
    for value in (-1, True, False, 64.0, "64", None, float("nan"), float("inf")):
        case = deepcopy(baseline)
        case[budget_key][0]["actual_benchmark_subset_size"] = value
        try:
            _validate_budget(case, [])
        except NumericDomainError as exc:
            assert exc.reason_code in {ReasonCode.INVALID_NUMERIC_INPUT, ReasonCode.OUT_OF_DOMAIN}
        else:
            raise AssertionError("invalid observed subset size accepted")
    case = deepcopy(baseline)
    del case[budget_key][0]["actual_benchmark_subset_size"]
    try:
        _validate_budget(case, [])
    except NumericDomainError as exc:
        assert exc.reason_code == ReasonCode.INVALID_NUMERIC_INPUT
    else:
        raise AssertionError("missing observed subset size accepted")
    for value in (0, 1, "true", "false", None, [], {}):
        case = deepcopy(baseline)
        case[rows_key][0]["benchmark_subset_flag"] = value
        try:
            _validate_budget(case, [])
        except ContractValidationError as exc:
            assert exc.reason_code == ReasonCode.INVALID_CONTRACT
        else:
            raise AssertionError("non-Boolean subset selector accepted")
    case = deepcopy(baseline)
    del case[rows_key][0]["benchmark_subset_flag"]
    try:
        _validate_budget(case, [])
    except ContractValidationError as exc:
        assert exc.reason_code == ReasonCode.INVALID_CONTRACT
    else:
        raise AssertionError("missing subset selector accepted")
    failures = []
    _validate_budget({budget_key: [{"actual_benchmark_subset_size": 0}], rows_key: []}, failures)
    assert failures == []

    # Keep JSON scalar typing distinct from the proof parser's coercion policy.
    from decimal import Decimal
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.context import (
        is_finite_json_number_v1, is_nonnegative_json_integer_v1,
    )
    from src.qtt.stage1_prediction_markets.pr166_qb_bounded_quantum_benchmark.validator import (
        _validate_race, _validate_payload_contracts,
    )
    for value in (0, -1, 0.0, -0.0, 1.5, 10 ** 400):
        assert is_finite_json_number_v1(value) is True
    for value in (True, False, float("nan"), float("inf"), float("-inf"), "1", Decimal("1"), None, [], {}):
        assert is_finite_json_number_v1(value) is False
    for value in (0, 1, 10 ** 400):
        assert is_nonnegative_json_integer_v1(value) is True
    for value in (-1, True, False, 1.0, "1", None):
        assert is_nonnegative_json_integer_v1(value) is False
    race_name = "PR166_QB_RaceArb.report.json"
    score_fields = (
        "classical_route_score", "quantum_inspired_route_score",
        "true_quantum_structural_route_score", "hybrid_route_score", "final_arbitration_score",
    )
    race = {race_name: [{
        "row_id": "synthetic", **dict.fromkeys(score_fields, 0.5),
        "classical_fallback_required_flag": True, "hot_path_allowed_flag": False,
        "no_live_authority_flag": True, "winning_nonlive_route": "CLASSICAL",
    }]}
    failures = []
    _validate_race(race, failures)
    assert failures == []
    for field in score_fields:
        for value in (True, False, float("nan"), float("inf"), float("-inf"), "0.5", None):
            case = deepcopy(race)
            case[race_name][0][field] = value
            failures = []
            _validate_race(case, failures)
            assert failures == [f"RACE_SCORE_MISSING::synthetic::{field}"]
        case = deepcopy(race)
        case[race_name][0][field] = -1
        failures = []
        _validate_race(case, failures)
        assert failures == []

    from src.qtt.stage1_prediction_markets.pr166_qb_bounded_quantum_benchmark.validator import _validate_payload_contracts
    count_name = "PR166_QB_InputConsumption.report.json"
    count_payload = {count_name: {"roadmap_pr_id": c.PR_ID, "created_by_pr": c.PR_ID, "record_count": 1}}
    count_rows = {count_name: [{}]}
    failures = []
    _validate_payload_contracts(count_payload, count_rows, failures)
    assert failures == []
    for value in (True, False, 1.0, 1.9, "1", None, -1, float("nan"), float("inf")):
        candidate_count = dict(count_payload[count_name])
        candidate_count["record_count"] = value
        failures = []
        _validate_payload_contracts({count_name: candidate_count}, count_rows, failures)
        assert failures == [f"BAD_RECORD_COUNT::{count_name}"]

    # Candidate lineage is data from an upstream producer, never a default.
    from pathlib import Path
    from unittest.mock import patch
    import pytest
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.serialization import _report_carry_candidate_lineage_v1
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import SerializationSafetyError
    from src.qtt.stage1_prediction_markets.pr166_qb_bounded_quantum_benchmark import validator as lineage_qb
    from src.qtt.stage1_prediction_markets.pr166_qc_quantum_selected_replay_paper_retest import validator as lineage_qc
    from src.qtt.stage1_prediction_markets.pr162e_q_quantum_automapper import validator as lineage_mapper
    from src.qtt.stage1_prediction_markets.pr167_open_trade_simulator_integration import validator as lineage_sim

    nested = ["fixture-value"]
    source_row = {"candidate_packet_id": "fixture-packet"}
    produced = {"row_id": "owned-output", "signed_value": -7.25, "nested": nested}
    carried = _report_carry_candidate_lineage_v1(source_row, produced)
    assert carried["candidate_packet_id"] == source_row["candidate_packet_id"]
    assert carried is not produced and carried["nested"] is nested
    assert produced == {"row_id": "owned-output", "signed_value": -7.25, "nested": nested}
    for invalid_source in ({}, {"candidate_packet_id": None}, {"candidate_packet_id": True}, {"candidate_packet_id": 0}, {"candidate_packet_id": " "}):
        with pytest.raises(SerializationSafetyError):
            _report_carry_candidate_lineage_v1(invalid_source, produced)
    for conflicting in (None, True, 0, "foreign-packet"):
        with pytest.raises(SerializationSafetyError):
            _report_carry_candidate_lineage_v1(source_row, {**produced, "candidate_packet_id": conflicting})

    cohort = [{"row_id": f"source-{i}", "candidate_packet_id": f"packet-{i}",
               "qku_id": "Q", "formula_id": "F", "algorithm_id": "A",
               "parameter_stack_id": "P", "execution_route_id": "R", "market_scope": "M"}
              for i in range(559)]
    for validator, prefix, collection_name in (
        (lineage_qb, "PR166_QB", "BENCHMARK_ROW_REPORTS"),
        (lineage_qc, "PR166_QC", "ROW_REPORTS"),
        (lineage_mapper, "PR162E_Q", "ROW_REPORTS"),
        (lineage_sim, "PR167", "ROW_REPORTS"),
    ):
        output_names = sorted(getattr(validator.c, collection_name))
        packets = {name: [dict(row, row_id=f"{name}::{i}") for i, row in enumerate(cohort)] for name in output_names}
        packets[prefix + "_InputConsumption.report.json"] = [
            {"row_id": name, "source_report_ref": name, "record_count_matches_expected_flag": True,
             "no_source_truth_acceptance_flag": True, "no_connector_binding_flag": True,
             "no_profit_evidence_flag": True, "no_backend_execution_flag": True,
             "no_live_order_execution_flag": True} for name in validator.c.STRICT_INPUT_REPORTS]
        if prefix == "PR162E_Q":
            # The mocked decoder returns this same 559-row cohort for every input.
            for input_row in packets[prefix + "_InputConsumption.report.json"]:
                input_row["expanded_record_count"] = len(cohort)
                input_row["expected_record_count"] = len(cohort)
        if prefix == "PR167":
            packets["PR167_UpstreamReportUse.report.json"] = [
                {"row_id": name, "consumed_by_pr167_flag": True, "fields_used": ["candidate_packet_id"]}
                for name in validator.c.STRICT_INPUT_REPORTS]
        # Only filesystem/decoder inputs are substituted. The actual current
        # _validate_inputs function and lineage checker remain active.
        with patch.object(Path, "exists", return_value=True), \
             patch.object(validator, "read_json", return_value={"records": cohort}), \
             patch.object(validator, "records_from_report_payload", side_effect=lambda root, payload: payload["records"]):
            failures = []
            validator._validate_inputs(Path("lineage-fixture-root"), packets, failures)
            assert failures == []
            chosen = output_names[0]
            packets[chosen][0]["candidate_packet_id"] = "foreign-packet"
            failures = []
            validator._validate_inputs(Path("lineage-fixture-root"), packets, failures)
            assert failures == ["INPUT_CANDIDATE_LINEAGE_MISMATCH"]


def test_pr166_qb_rejects_forbidden_benchmark_dispositions_and_modes():
    rows = deepcopy(records("PR166_QB_Eligibility.report.json"))
    rows[0]["benchmark_disposition"] = "METADATA_ONLY_BENCHMARKED"
    assert rows[0]["benchmark_disposition"] in c.FORBIDDEN_BENCHMARK_DISPOSITIONS
    rows[1]["benchmark_execution_mode"] = "CLOUD_BACKEND_EXECUTION"
    assert rows[1]["benchmark_execution_mode"] in c.FORBIDDEN_EXECUTION_MODES


def test_pr166_qb_fairness_normalizes_objective_direction_and_budget():
    rows = assert_report_contract("PR166_QB_FairnessNorm.report.json", 559)
    assert all(row["objective_direction_normalized"] == "MAXIMIZE_EXECUTION_ADJUSTED_EDGE" for row in rows)
    assert all(row["minmax_sign"] == 1 for row in rows)
    assert all(row["same_budget_comparison_flag"] is True for row in rows)
    assert all(row["energy_to_edge_translation"] for row in rows)
    assert all(row["paired_comparison_group_id"] for row in rows)


def test_pr166_qb_race_arbitration_keeps_classical_fallback_nonlive():
    rows = assert_report_contract("PR166_QB_RaceArb.report.json", 559)
    assert all(row["classical_fallback_required_flag"] is True for row in rows)
    assert all(row["hot_path_allowed_flag"] is False for row in rows)
    assert all(row["future_live_route_candidate_flag"] is False for row in rows)
    assert all(row["no_live_authority_flag"] is True for row in rows)
    assert all(row["winning_nonlive_route"] != "TRUE_QUANTUM_STRUCTURAL_PAPER_ONLY" for row in rows)


def test_pr166_qb_qaoa_and_sampling_vqe_are_dependency_unavailable_noexec():
    for filename in ("PR166_QB_QAOAReceipt.report.json", "PR166_QB_SamplingVQEReceipt.report.json"):
        rows = assert_report_contract(filename, 559)
        assert all(row["benchmark_disposition"] == "BENCHMARK_STRUCTURAL_ONLY_DEPENDENCY_UNAVAILABLE" for row in rows)
        assert all(row["benchmark_executed_flag"] is False for row in rows)
        assert all(row["credential_access_flag"] is False for row in rows)
        assert all(row["cloud_backend_execution_flag"] is False for row in rows)
        assert all(row["quantum_backend_execution_flag"] is False for row in rows)


def test_pr166_qb_repair_lab_routes_negative_candidates_without_profit_evidence():
    rows = assert_report_contract("PR166_QB_QuantumRepairLab.report.json", 559)
    assert all(row["repair_row_id"] for row in rows)
    assert all(row["not_profit_evidence_flag"] is True for row in rows)
    assert all(row["no_live_authority_flag"] is True for row in rows)
    assert all(row["downstream_pr166_qc_route_ref"] or row["downstream_pr162e_q_route_ref"] for row in rows)


def test_pr166_qb_cloud_switchboard_and_owner_controls_default_off():
    for filename in ("PR166_QB_CloudSwitchReady.report.json", "PR166_QB_OwnerQuantumControlReady.report.json"):
        rows = assert_report_contract(filename, 5)
        assert all(row["default_mode"] == "OFF" for row in rows)
        assert all(row["credential_access_allowed_flag"] is False for row in rows)
        assert all(row["backend_execution_allowed_flag"] is False for row in rows)
        assert all(row["live_order_authority_flag"] is False for row in rows)
        assert all(row["no_backend_execution_flag"] is True for row in rows)
    owner_rows = records("PR166_QB_OwnerQuantumControlReady.report.json")
    assert all(row["dashboard_implementation_required_flag"] is True for row in owner_rows)
    assert all(row["dashboard_ui_implemented_flag"] is False for row in owner_rows)


def test_pr166_qb_market_portability_is_route_only():
    rows = assert_report_contract("PR166_QB_MarketPortability.report.json", 559)
    assert all(row["stage1_prediction_market_flag"] is True for row in rows)
    assert all(row["future_market_portability_flag"] is True for row in rows)
    assert all(row["no_current_connector_binding_flag"] is True for row in rows)
    assert all(row["no_live_authority_flag"] is True for row in rows)


def test_pr166_qb_agent_dag_and_artifact_map_have_no_orphans():
    assert_report_contract("PR166_QB_AgentWorkOrders.report.json", 559)
    assert_report_contract("PR166_QB_AgentDAG.report.json", 559)
    proof_rows = assert_report_contract("PR166_QB_NoOrphanProof.report.json", 559)
    assert all(row["no_orphan_status"] == "NO_ORPHAN" for row in proof_rows)
    artifact_rows = assert_report_contract("PR166_QB_ArtifactMap.report.json")
    assert artifact_rows
    assert all(row["artifact_path"] for row in artifact_rows)
    assert all(row["consumed_by_module"] for row in artifact_rows)
