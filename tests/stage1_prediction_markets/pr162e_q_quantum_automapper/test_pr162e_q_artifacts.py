from __future__ import annotations

from collections import Counter

from src.qtt.stage1_prediction_markets.pr162e_q_quantum_automapper import constants as c
from src.qtt.stage1_prediction_markets.pr162e_q_quantum_automapper.validator import (
    validate_artifacts,
)

from .helpers import REPO_ROOT, assert_report_contract, payload, records, summary


def test_pr162e_q_validator_accepts_generated_artifacts():
    result = validate_artifacts(REPO_ROOT)
    assert result.ok, result.failures


def test_pr162e_q_input_counts_and_final_summary():
    final = summary()
    assert final["consumed_pr162e_q_handoff_rows"] == 559
    assert final["input_record_counts"]["PR166_QC_To_PR162E_Q.report.json"] == 559
    assert final["input_record_counts"]["PR166_QC_AutomapperNeeds.report.json"] == 559
    assert final["input_record_counts"]["PR166_QC_ReplayPaperRepairLab.report.json"] == 559
    assert final["input_record_counts"]["PR166_QC_StillNegativeAfterCosts.report.json"] == 559
    assert final["deep_mapping_subset_count"] == c.MAP_CAPS["max_deep_mapping_rows_default_ci"]
    assert final["forbidden_authority_counts_all_zero_flag"] is True
    assert final["dashboard_ui_implemented_flag"] is False


def test_pr162e_q_required_reports_have_contracts_and_rows():
    for filename in c.REPORT_FILENAMES:
        expected = 559 if filename in c.ROW_REPORTS else None
        assert_report_contract(filename, expected)

    manifest = assert_report_contract("PR162E_Q_ReportManifest.report.json")
    assert len(manifest) == len(c.REPORT_FILENAMES)
    assert {row["report_path"].split("/")[-1] for row in manifest} == set(c.REPORT_FILENAMES)


def test_pr162e_q_source_and_upstream_consumption_ledgers():
    sources = assert_report_contract("PR162E_Q_SourceMapParams.report.json")
    assert len(sources) >= 8
    assert any(row["official_flag"] is True for row in sources)
    assert any(row["non_official_flag"] is True for row in sources)
    assert any(row["source_type"].startswith("official_") for row in sources)
    assert any(row["source_type"].startswith("research_") for row in sources)
    assert all(row["no_backend_execution_flag"] is True for row in sources)
    assert all(row["no_source_truth_acceptance_flag"] is True for row in sources)

    upstream = assert_report_contract("PR162E_Q_UpstreamReportUse.report.json")
    assert len(upstream) == len(c.STRICT_INPUT_REPORTS)
    assert all(row["consumed_by_pr162e_q_flag"] is True for row in upstream)
    assert all(row["terminal_flag"] is False for row in upstream)
    assert {row["source_pr"] for row in upstream} >= {"PR166-QC", "PR166-QB", "PR166-Q", "PR165-D2"}


def test_pr162e_q_budget_subset_and_dispositions_are_bounded():
    budget = records("PR162E_Q_MapBudget.report.json")[0]
    assert budget["max_deep_mapping_rows_default_ci"] == 64
    assert budget["max_penalty_variants_per_row_default_ci"] == 8
    assert budget["no_unbounded_mapping_execution_flag"] is True

    rows = assert_report_contract("PR162E_Q_MapEligibility.report.json", 559)
    deep = [row for row in rows if row["actual_deep_mapping_subset_flag"]]
    assert len(deep) == 64
    assert max(Counter(row["model_family_selected"] for row in deep).values()) <= 16
    assert all(row["automapper_disposition"] in c.AUTOMAPPER_DISPOSITIONS for row in rows)
    assert not (set(row["automapper_disposition"] for row in rows) & set(c.FORBIDDEN_AUTOMAPPER_DISPOSITIONS))
    assert all(row["mapping_quality_grade"] in c.MAPPING_QUALITY_GRADES for row in rows)
    assert all(row["classical_fallback_available"] is True for row in rows)
    assert all(row["hot_path_allowed_flag"] is False for row in rows)


def test_pr162e_q_unit_objective_variable_interpret_and_proof_contracts():
    unit_rows = assert_report_contract("PR162E_Q_UnitNorm.report.json", 559)
    assert all(row["YES_NO_side"] in {"YES", "NO"} for row in unit_rows)
    assert all(row["probability_unit"] == "PROBABILITY_0_TO_1" for row in unit_rows)
    assert all(
        row["expected_value_unit"]
        == "NORMALIZED_EXPECTED_NET_PROFIT_PER_ORDER_CANDIDATE_NOT_EVIDENCE"
        for row in unit_rows
    )

    objective_rows = assert_report_contract("PR162E_Q_ObjectiveMap.report.json", 559)
    assert all(row["objective_terms"] for row in objective_rows)
    assert all(row["objective_linear_terms"] for row in objective_rows)
    assert all("MAXIMIZE" in row["objective_direction"] for row in objective_rows)

    encoding_rows = assert_report_contract("PR162E_Q_VariableEncoding.report.json", 559)
    assert all(row["decision_variables"] for row in encoding_rows)
    assert any("bounded_integer_to_binary" in row["integer_encoding"] for row in encoding_rows)
    assert any(row["spin_encoding"].get("binary_to_spin") == "x=(s+1)/2" for row in encoding_rows)
    assert any("route_case" in row["one_hot_encoding"] for row in encoding_rows)

    interpret_rows = assert_report_contract("PR162E_Q_SolutionInterpretBack.report.json", 559)
    assert all(row["interpret_back_entries"] for row in interpret_rows)
    assert all(row["reverse_transform_rule"] for row in interpret_rows)
    assert all(row["lost_information_flag"] is False for row in interpret_rows)

    proof_rows = assert_report_contract("PR162E_Q_MapProof.report.json", 559)
    assert all(
        row["proof_status"]
        in {
            "PROOF_VECTOR_COMPUTED_DETERMINISTIC_NO_SOLVER",
            "STRUCTURAL_PROOF_VECTOR_COMPUTED_NO_SOLVER",
        }
        for row in proof_rows
    )
    assert all(abs(row["objective_delta"]) <= 1e-9 for row in proof_rows)
    assert all(row["interpret_back_match_flag"] is True for row in proof_rows)

    # A complete synthetic model supplies the predicate fixture. Retained
    # reports above are tested as stored; this fixture neither currentizes them
    # nor treats a generated witness as independently accepted evidence.
    from copy import deepcopy
    import json
    from src.qtt.stage1_prediction_markets.pr162e_q_quantum_automapper.report_writer import (
        _constraints, _decision_variables, _variable_domains, _qubo_matrix,
        _ising_from_qubo, _recipe_payload, _proof_fields,
    )
    fixture_linear = dict.fromkeys(("x_select", "x_precompute", "x_retest", "x_owner_review"), 0.0)
    fixture_constraints = [
        {"name": "select_requires_one_route", "linear": {"x_select": 1, "x_precompute": -1}, "sense": "GE", "rhs": 0},
        {"name": "owner_review_for_negative_or_repair", "linear": {"x_owner_review": 1, "x_retest": 1}, "sense": "GE", "rhs": 0},
        {"name": "bounded_candidate_size", "linear": {"x_size_0": 1, "x_size_1": 2, "x_size_2": 4}, "sense": "LE", "rhs": 7},
    ]
    assert _constraints(1, "QUBO", False, False) == fixture_constraints
    fixture_q = _qubo_matrix(fixture_linear, {}, 0.0)
    fixture_recipe = _recipe_payload(
        "QUBO", fixture_linear, {}, fixture_q, _ising_from_qubo(fixture_q, 0.0),
        fixture_constraints, 1.0, {"hybrid": "fixture-hybrid", "to_pr166_qc": "fixture-retest"}, False,
    )
    # Independently known loss for this zero-utility fixture is precompute*(1-select).
    assert {key: value for key, value in fixture_recipe["qubo"]["Q"].items() if value} == {
        "x_precompute,x_precompute": 1.0, "x_precompute,x_select": -1.0,
    }
    assert fixture_recipe["qubo"]["offset"] == 0.0
    model_fixture = deepcopy(proof_rows[0])
    model_fixture.update(
        candidate_packet_id="fixture-packet-A",
        model_family_selected="QUBO", still_negative_after_costs_flag=False,
        paper_retest_flag=False, owner_dashboard_review_flag=False,
        objective_linear_terms=fixture_linear, objective_quadratic_terms={},
        objective_terms={"linear": fixture_linear, "quadratic": {}, "offset": 0.0},
        constraints=fixture_constraints, recipe_payload=fixture_recipe,
        decision_variables=_decision_variables(1), variable_domains=_variable_domains("QUBO"),
        canonical_variable_signature=",".join(item["name"] for item in _decision_variables(1)),
        canonical_constraint_signature=json.dumps(fixture_constraints, sort_keys=True, separators=(",", ":")),
        constraint_native_flag=False,
        slack_variable_plan="NO_ADDITIONAL_SLACK_FOR_SELECTED_SOURCE_BOUND_BINARY_CONSTRAINTS",
        coefficient_scaling_status="UNSCALED_MODEL_COEFFICIENTS_WITH_SOURCE_MAXIMUM_MAGNITUDE_PROXY",
        discrete_case_handling="TWO_CASE_PER_ORIGINAL_BINARY_VARIABLE;ONE_HOT_ONLY_WHEN_ORIGINAL_CONSTRAINT_REQUIRES",
    )
    model_fixture.update(_proof_fields(model_fixture, 1, fixture_linear, {}, fixture_constraints, 1.0))
    assert model_fixture["encoded_variable_assignment"] == {
        "x_select": 1, "x_precompute": 1, "x_retest": 0, "x_owner_review": 0,
        "x_size_0": 0, "x_size_1": 0, "x_size_2": 0,
        "case_skip": 0, "case_precompute": 0, "case_retest": 1, "case_owner_review": 0,
    }
    for field in ("original_objective_value", "encoded_objective_value", "objective_delta",
                  "encoded_energy_value", "bqm_energy_value", "ising_energy_value", "penalty_value"):
        assert model_fixture[field] == 0.0

    # Exercise finite objective proof values without claiming a solver run.
    from copy import deepcopy
    import math
    from src.qtt.stage1_prediction_markets.pr162e_q_quantum_automapper.validator import _validate_interpret_back_and_proofs
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import NumericDomainError, ReasonCode
    key = "PR162E_Q_MapProof.report.json"
    baseline = {
        "PR162E_Q_SolutionInterpretBack.report.json": [],
        key: [deepcopy(model_fixture)],
        "PR162E_Q_TestVectors.report.json": [],
    }
    for value in (0, 0.0, -0.0, 1e-9, -1e-9, "0", "0.000000001", "-0.000000001"):
        case = deepcopy(baseline)
        case[key][0]["objective_delta"] = value
        failures = []
        _validate_interpret_back_and_proofs(case, failures)
        assert failures == []
    for value in (math.nextafter(1e-9, math.inf), math.nextafter(-1e-9, -math.inf), 1.0, -1.0):
        case = deepcopy(baseline)
        case[key][0]["objective_delta"] = value
        failures = []
        _validate_interpret_back_and_proofs(case, failures)
        assert failures == [f"PROOF_OBJECTIVE_DELTA_NONZERO::{case[key][0].get('row_id')}"]
    for value in (float("nan"), float("inf"), float("-inf"), "NaN", "Infinity", "1e999", True, False, None, [], {}):
        case = deepcopy(baseline)
        case[key][0]["objective_delta"] = value
        try:
            _validate_interpret_back_and_proofs(case, [])
        except NumericDomainError as exc:
            assert exc.reason_code in {ReasonCode.INVALID_NUMERIC_INPUT, ReasonCode.NONFINITE_NUMERIC_INPUT}
        else:
            raise AssertionError("invalid mapping objective proof accepted")
    case = deepcopy(baseline)
    del case[key][0]["objective_delta"]
    try:
        _validate_interpret_back_and_proofs(case, [])
    except NumericDomainError as exc:
        assert exc.reason_code == ReasonCode.INVALID_NUMERIC_INPUT
    else:
        raise AssertionError("missing mapping objective proof accepted")
    for field, value, prefix in (
        ("proof_status", "UNPROVEN", "PROOF_STATUS_BAD"),
        ("interpret_back_match_flag", False, "PROOF_INTERPRET_BACK_FAIL"),
    ):
        case = deepcopy(baseline)
        case[key][0]["objective_delta"] = 0.0
        case[key][0][field] = value
        failures = []
        _validate_interpret_back_and_proofs(case, failures)
        expected = f"{prefix}::{case[key][0].get('row_id')}"
        if field == "proof_status":
            expected += "::UNPROVEN"
        assert failures == [expected]

    from src.qtt.stage1_prediction_markets.pr162e_q_quantum_automapper.validator import _validate_payload_contracts
    count_name = "PR162E_Q_InputConsumption.report.json"
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

    from src.qtt.stage1_prediction_markets.pr162e_q_quantum_automapper.validator import _validate_risk_execution_and_units
    map_reports = ('PR162E_Q_UnitNorm.report.json', 'PR162E_Q_TCAMapImpact.report.json', 'PR162E_Q_OverfitFDRMapRisk.report.json', 'PR162E_Q_MapSensitivityStress.report.json', 'PR162E_Q_EdgeAttribution.report.json')
    cost_fields = ('explicit_fee_component', 'bid_ask_spread_component', 'slippage_component', 'impact_component', 'latency_component', 'no_fill_opportunity_cost_component', 'settlement_finality_component', 'market_state_mismatch_component', 'model_vs_execution_gap_component', 'mapping_to_replay_translation_penalty', 'mapping_to_paper_translation_penalty', 'mapping_to_simulator_translation_penalty', 'total_tca_estimate')
    delta_fields = ('baseline_expected_net_profit_per_order_candidate', 'mapped_expected_net_profit_per_order_candidate', 'expected_value_delta_candidate', 'TCA_delta_candidate', 'latency_delta_candidate', 'fill_probability_delta_candidate', 'queue_risk_delta_candidate', 'capacity_delta_candidate', 'crowding_delta_candidate', 'overfit_delta_candidate', 'marginal_utility_delta_candidate', 'quantum_precompute_delta_candidate', 'classical_fallback_delta_candidate')
    tca_name = "PR162E_Q_TCAMapImpact.report.json"
    edge_name = "PR162E_Q_EdgeAttribution.report.json"
    packets = {name: [] for name in map_reports}
    packets[tca_name] = [{"row_id": "synthetic", "tca_reason_codes": ["SYNTHETIC"], **dict.fromkeys(cost_fields, 0.5)}]
    packets[edge_name] = [{"row_id": "synthetic", "not_profit_evidence_flag": True, **dict.fromkeys(delta_fields, 0.5)}]
    for name, fields, prefix in ((tca_name, cost_fields, "TCA_FIELD_MISSING"), (edge_name, delta_fields, "EDGE_FIELD_MISSING")):
        for field in fields:
            for value in (True, False, float("nan"), float("inf"), float("-inf"), "0.5", None):
                case = deepcopy(packets)
                case[name][0][field] = value
                failures = []
                _validate_risk_execution_and_units(case, failures)
                assert failures == [f"{prefix}::synthetic::{field}"]
            case = deepcopy(packets)
            case[name][0][field] = -1.0
            failures = []
            _validate_risk_execution_and_units(case, failures)
            assert failures == []

    # Companion association is checked on existing semantic fields, not row order.
    from copy import deepcopy
    from types import SimpleNamespace
    import pytest
    from src.qtt.stage1_prediction_markets.pr162e_q_quantum_automapper.report_writer import build_candidate_contexts
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import SerializationSafetyError

    companion_names = (
        'PR166_QC_AutomapperNeeds.report.json',
        'PR166_QC_ReplayPaperRepairLab.report.json',
        'PR166_QC_StillNegativeAfterCosts.report.json',
        'PR166_QC_PaperPromotionCandidate.report.json',
        'PR166_QC_ChampChallengerPaper.report.json',
        'PR166_QC_OpenTradeSimHandoff.report.json',
        'PR166_QC_BenchmarkOnlyResidual.report.json',
        'PR166_QC_OwnerDashboardReview.report.json',
        'PR166_QC_ConnectorRouteReadiness.report.json',
        'PR166_QC_OverfitFDRRetest.report.json',
        'PR166_QC_PortfolioUtility.report.json',
        'PR166_QC_RegimeEvidence.report.json',
        'PR166_QB_QUBOReceipt.report.json',
        'PR166_QB_BQMReceipt.report.json',
        'PR166_QB_IsingReceipt.report.json',
        'PR166_QB_CQMReceipt.report.json',
        'PR166_QB_DQMReceipt.report.json',
        'PR166_QB_QuadProgramReceipt.report.json',
        'PR166_QB_ClassicalReceipt.report.json',
        'PR166_QB_RaceArb.report.json',
        'PR166_Q_QuantumStructuralReadiness.report.json',
        'PR166_Q_ObjectiveVariableConstraintPenaltyMap.report.json',
        'PR166_Q_QuantumClassicalHybridRaceLedger.report.json',
    )
    primary_name = 'PR166_QC_To_PR162E_Q.report.json'
    base = {"row_id": "fixture-A", "qku_id": "fixture-QKU", "formula_id": "fixture-formula",
            "algorithm_id": "fixture-algorithm", "parameter_stack_id": "fixture-parameters-A",
            "execution_route_id": "fixture-route", "market_scope": "fixture-market",
            "qku_family": "fixture-family", "model_family": "QUBO", "deterministic_sort_key": "A"}
    other = {**base, "row_id": "fixture-B", "parameter_stack_id": "fixture-parameters-B", "deterministic_sort_key": "B"}
    base["candidate_packet_id"] = "fixture-packet-A"
    other["candidate_packet_id"] = "fixture-packet-B"
    source_rows = {primary_name: [base, other]}
    for name in companion_names:
        source_rows[name] = [{**base, "row_id": name + "::A", "association_value": -7},
                             {**other, "row_id": name + "::B", "association_value": 11}]
    source = SimpleNamespace(records=source_rows)
    clean = build_candidate_contexts(source)
    assert len(clean) == 2
    expected = [-7, 11]
    for name in companion_names:
        assert [item["companions"][name]["association_value"] for item in clean] == expected
    name = companion_names[0]
    source_rows[name][0]["deterministic_sort_key"] = "Z"
    source_rows[name][1]["deterministic_sort_key"] = "0"
    source_rows[name].reverse()
    snapshot = deepcopy(source_rows)
    aligned = build_candidate_contexts(source)
    assert [item["companions"][name]["association_value"] for item in aligned] == expected
    assert source_rows == snapshot
    for mutation in ("missing", "extra", "duplicate-key", "wrong-key", "duplicate-row-id", "null-key"):
        changed = deepcopy(source_rows)
        if mutation == "missing":
            changed[name].pop()
        elif mutation == "extra":
            changed[name].append({**changed[name][0], "row_id": "fixture-extra", "parameter_stack_id": "fixture-extra"})
        elif mutation == "duplicate-key":
            changed[name].append({**changed[name][0], "row_id": "fixture-duplicate"})
        elif mutation == "wrong-key":
            changed[name][0]["execution_route_id"] = "fixture-unmatched-route"
        elif mutation == "duplicate-row-id":
            changed[name][1]["row_id"] = changed[name][0]["row_id"]
        else:
            changed[name][0]["qku_id"] = None
        with pytest.raises(SerializationSafetyError):
            build_candidate_contexts(SimpleNamespace(records=changed))

    # Existing packet identity must agree even when all context fields agree.
    for invalid_packet in (None, True, 0, 1.0, "", " ", "foreign-packet"):
        changed = deepcopy(source_rows)
        changed[name][0]["candidate_packet_id"] = invalid_packet
        with pytest.raises(SerializationSafetyError):
            build_candidate_contexts(SimpleNamespace(records=changed))
    changed = deepcopy(source_rows)
    del changed[name][0]["candidate_packet_id"]
    with pytest.raises(SerializationSafetyError):
        build_candidate_contexts(SimpleNamespace(records=changed))
    # Distinct packet identities resolve a legitimately shared six-field context.
    changed = deepcopy(source_rows)
    for values in changed.values():
        for value in values:
            value["parameter_stack_id"] = "shared-fixture-parameters"
    aligned = build_candidate_contexts(SimpleNamespace(records=changed))
    assert [item["companions"][name]["candidate_packet_id"] for item in aligned] == ["fixture-packet-A", "fixture-packet-B"]

    # Independent bounded energy oracle and original-constraint witness checks.
    from fractions import Fraction
    from itertools import product
    from src.qtt.stage1_prediction_markets.pr162e_q_quantum_automapper.report_writer import (
        _qubo_matrix, _ising_from_qubo, _constraints_satisfied,
        _proof_fields, _recipe_payload,
    )
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import ContractValidationError
    linear = {"x_1": 22, "x_2": 6, "x_3": 14}
    quadratic = {"x_1*x_2": -20, "x_1*x_3": -28}
    q = _qubo_matrix(linear, quadratic, 9)
    ising = _ising_from_qubo(q, 9)
    assert q == {"x_1,x_1": -22, "x_2,x_2": -6, "x_3,x_3": -14, "x_1,x_2": 20, "x_1,x_3": 28}
    assert ising["h"] == {"s_1": 1, "s_2": 2, "s_3": 0} and ising["J"] == {"s_1,s_2": 5, "s_1,s_3": 7} and ising["offset"] == 0
    for x1, x2, x3 in product((0, 1), repeat=3):
        expected = -22*x1 - 6*x2 - 14*x3 + 20*x1*x2 + 28*x1*x3 + 9
        s1, s2, s3 = 2*x1-1, 2*x2-1, 2*x3-1
        observed = ising["h"]["s_1"]*s1 + ising["h"]["s_2"]*s2 + ising["h"]["s_3"]*s3 + ising["J"]["s_1,s_2"]*s1*s2 + ising["J"]["s_1,s_3"]*s1*s3 + ising["offset"]
        assert observed == expected
    tiny = _ising_from_qubo({"x_1,x_1": 0.000001}, 0)
    assert abs(tiny["h"]["s_1"] + tiny["offset"] - 0.000001) <= 1e-9
    assert _qubo_matrix({"x_select": 0.005}, {}, 1) == _qubo_matrix({"x_select": 0.005}, {}, 0)
    constraint = {"name": "bound", "linear": {"x": 1}, "sense": "LE", "rhs": 0}
    assert _constraints_satisfied({"x": 0}, [constraint]) is True
    assert _constraints_satisfied({"x": 1}, [constraint]) is False
    for bad in ({**constraint, "sense": "UNKNOWN"}, {**constraint, "rhs": float("nan")}, {**constraint, "linear": {"missing": 1}}, {**constraint, "quadratic": {"x*x": 1}}):
        with pytest.raises((ContractValidationError, NumericDomainError)):
            _constraints_satisfied({"x": 0}, [bad])
    for value in (True, False, 0.0, "0", None, -1, 2):
        with pytest.raises(ContractValidationError):
            _constraints_satisfied({"x": value}, [constraint])
    with pytest.raises(ContractValidationError):
        _constraints_satisfied({"x": 1}, [constraint, {**constraint, "name": "bad", "sense": "UNKNOWN"}])
    assert _constraints_satisfied({"x": 1, "y": 1}, [{"name": "cancellation", "linear": {"x": 2**53+1, "y": -(2**53)}, "sense": "EQ", "rhs": 0}]) is False

    # Reuse the complete synthetic model; report admission remains separate.
    witness = deepcopy(model_fixture)
    failures = []
    _validate_interpret_back_and_proofs({"PR162E_Q_SolutionInterpretBack.report.json": [], "PR162E_Q_MapProof.report.json": [witness], "PR162E_Q_TestVectors.report.json": []}, failures)
    assert failures == []
    for path, bad_value in (
        (("encoded_variable_assignment", "x_size_0"), None),
        (("constraints", 0, "sense"), "UNKNOWN"),
        (("recipe_payload", "bqm", "offset"), 42),
        (("recipe_payload", "ising", "offset"), 42),
        (("recipe_payload", "qubo", "Q", "x_retest,x_retest"), 42),
        (("original_variable_assignment", "candidate_size"), 7),
        (("feasibility_match_flag",), False),
        (("encoded_energy_value",), 42),
    ):
        changed = deepcopy(witness)
        cursor = changed
        for part in path[:-1]:
            cursor = cursor[part]
        cursor[path[-1]] = bad_value
        failures = []
        _validate_interpret_back_and_proofs({"PR162E_Q_SolutionInterpretBack.report.json": [], "PR162E_Q_MapProof.report.json": [changed], "PR162E_Q_TestVectors.report.json": []}, failures)
        assert failures == [f"PROOF_MODEL_WITNESS_INVALID::{changed.get('row_id')}"]
    changed = deepcopy(witness)
    changed["recipe_payload"]["qubo"]["Q"]["x_select,x_select"] += 1
    with pytest.raises(ContractValidationError):
        _proof_fields(changed, 1, changed["objective_linear_terms"], changed["objective_quadratic_terms"], changed["constraints"], 3.0)

    # Original-model constraint compilation; no slack variables or guessed penalty.
    from src.qtt.stage1_prediction_markets.pr162e_q_quantum_automapper.report_writer import (
        _constraints, _decision_variables, _mapping_penalty_polynomial_v1, _mapping_solution_v1,
    )
    names = [item["name"] for item in _decision_variables(1)]
    assert len(names) == len(set(names)) == 11
    for family in ("QUBO", "BQM", "Ising", "CQM", "DQM", "QuadraticProgram"):
        constraint_rows = _constraints(13, family, True, True)
        penalty_terms, penalty_constant = _mapping_penalty_polynomial_v1(constraint_rows)
        for values in product((0, 1), repeat=len(names)):
            assignment = dict(zip(names, values))
            loss = 0
            for item in constraint_rows:
                residual = sum(value*assignment[name] for name, value in item["linear"].items()) - item["rhs"]
                violation = max(0, -residual) if item["sense"] == "GE" else max(0, residual) if item["sense"] == "LE" else abs(residual)
                loss += violation*violation
            encoded_loss = penalty_constant + sum(value*assignment[pair.split(",")[0]]*assignment[pair.split(",")[1]] for pair, value in penalty_terms.items())
            assert encoded_loss == loss
    # Decode preserves the original domain and never invents missing size bits.
    witness = deepcopy(model_fixture)
    bits = witness["encoded_variable_assignment"]
    decoded = _mapping_solution_v1(witness, bits)
    assert decoded["original_variable_assignment"] == witness["original_variable_assignment"]
    spin = {name.replace("x_", "s_"): 2*value-1 for name, value in bits.items()}
    assert _mapping_solution_v1(witness, spin, sample_kind="SPIN") == decoded
    assert _mapping_solution_v1(witness, bits, sample_kind="DQM") == decoded
    for invalid in (None, True, 0.0, "0", -1, 2):
        changed = dict(bits, x_size_0=invalid)
        with pytest.raises(ContractValidationError):
            _mapping_solution_v1(witness, changed)
    changed = dict(bits)
    del changed["case_skip"]
    with pytest.raises(ContractValidationError):
        _mapping_solution_v1(witness, changed)
    with pytest.raises(ContractValidationError):
        _mapping_solution_v1(witness, dict(bits, x_select=0, x_precompute=1))
    # A penalty below the original utility variation cannot certify feasibility.
    lin, quad = witness["objective_linear_terms"], witness["objective_quadratic_terms"]
    offset = witness["objective_terms"]["offset"]
    q = _qubo_matrix(lin, quad, offset)
    s = _ising_from_qubo(q, offset)
    with pytest.raises(NumericDomainError):
        _recipe_payload(witness["recipe_payload"]["selected_family"], lin, quad, q, s, witness["constraints"], 0, {"hybrid":"fixture-hybrid", "to_pr166_qc":"fixture-retest"}, witness["recipe_payload"]["hybrid"]["structural_only_flag"])
    for path, invalid in (
        (("recipe_payload", "cqm", "objective", "sense"), "maximize"),
        (("recipe_payload", "quadratic_program", "objective", "sense"), "minimize"),
        (("recipe_payload", "dqm", "offset"), 42),
        (("recipe_payload", "dqm", "linear_biases", "x_retest"), [1, 0]),
        (("recipe_payload", "constraint_encoding", "additional_binary_variables"), True),
        (("recipe_payload", "constraint_encoding", "uniform_export_error_bound"), -1),
    ):
        changed = deepcopy(witness)
        cursor = changed
        for key in path[:-1]: cursor = cursor[key]
        cursor[path[-1]] = invalid
        failures = []
        _validate_interpret_back_and_proofs({"PR162E_Q_SolutionInterpretBack.report.json": [], "PR162E_Q_MapProof.report.json": [changed], "PR162E_Q_TestVectors.report.json": []}, failures)
        assert failures == [f"PROOF_MODEL_WITNESS_INVALID::{changed.get('row_id')}"]

    # The selected compiler never accepts a missing native constraint roster.
    for family in ("QUBO", "BQM", "Ising", "CQM", "DQM", "QuadraticProgram"):
        with pytest.raises(ContractValidationError):
            _recipe_payload(family, lin, quad, q, s, [], 3.0, {"hybrid":"fixture-hybrid", "to_pr166_qc":"fixture-retest"}, False)

    # A model's native case constraint, not the chosen sample container, governs
    # one-hot feasibility. Non-DQM branches preserve zero/multiple case bits.
    from src.qtt.stage1_prediction_markets.pr162e_q_quantum_automapper.report_writer import _variable_domains
    for family in ("QUBO", "BQM", "Ising", "CQM", "DQM", "QuadraticProgram"):
        lin = {name: 0.0 for name in ("x_select", "x_precompute", "x_retest", "x_owner_review")}
        quad = {}
        q = _qubo_matrix(lin, quad, 0.0)
        s = _ising_from_qubo(q, 0.0)
        constraint_rows = _constraints(1, family, False, False)
        recipe = _recipe_payload(family, lin, quad, q, s, constraint_rows, 1.0, {"hybrid":"fixture-hybrid", "to_pr166_qc":"fixture-retest"}, False)
        seed = {"row_id":"domain-fixture", "proof_status":"PROOF_VECTOR_COMPUTED_DETERMINISTIC_NO_SOLVER",
                "still_negative_after_costs_flag":False, "paper_retest_flag":False, "owner_dashboard_review_flag":False,
                "objective_linear_terms":lin, "objective_quadratic_terms":quad,
                "objective_terms":{"linear":lin,"quadratic":quad,"offset":0.0},
                "constraints":constraint_rows, "recipe_payload":recipe, "model_family_selected":family,
                "decision_variables":_decision_variables(1), "variable_domains":_variable_domains(family)}
        seed.update(_proof_fields(seed, 1, lin, quad, constraint_rows, 1.0))
        for cases in product((0, 1), repeat=4):
            sample = dict(seed["encoded_variable_assignment"])
            sample.update(dict(zip(("case_skip", "case_precompute", "case_retest", "case_owner_review"), cases)))
            if family == "DQM" and sum(cases) != 1:
                with pytest.raises(ContractValidationError):
                    _mapping_solution_v1(seed, sample)
                continue
            for sample_kind in ("BINARY", "SPIN", "DQM"):
                native_sample = {name.replace("x_", "s_"):2*value-1 for name,value in sample.items()} if sample_kind=="SPIN" else sample
                updated = deepcopy(seed)
                updated.update(_mapping_solution_v1(seed, native_sample, sample_kind=sample_kind))
                failures = []
                _validate_interpret_back_and_proofs({"PR162E_Q_SolutionInterpretBack.report.json":[], "PR162E_Q_MapProof.report.json":[updated], "PR162E_Q_TestVectors.report.json":[]}, failures)
                assert failures == []
                if sum(cases) != 1:
                    assert updated["original_variable_assignment"]["route_case"] is None
            for field in ("model_family_selected", "decision_variables", "variable_domains"):
                changed = deepcopy(updated)
                del changed[field]
                failures = []
                _validate_interpret_back_and_proofs({"PR162E_Q_SolutionInterpretBack.report.json":[], "PR162E_Q_MapProof.report.json":[changed], "PR162E_Q_TestVectors.report.json":[]}, failures)
                assert failures == ["PROOF_MODEL_WITNESS_INVALID::domain-fixture"]

    # Bind all current row-report projections to the independently checked proof.
    # Original report/schema/current-generation admission remains independent.
    from src.qtt.stage1_prediction_markets.pr162e_q_quantum_automapper.report_writer import row_for_report
    from src.qtt.stage1_prediction_markets.pr162e_q_quantum_automapper.validator import _validate_mapping_projection_consistency_v1
    projection_names = ("PR162E_Q_MapProof.report.json", "PR162E_Q_SolutionInterpretBack.report.json", "PR162E_Q_TestVectors.report.json")
    projection_report_names = tuple(c.ROW_REPORTS)
    projection_seed = deepcopy(model_fixture)
    projection_seed_before = deepcopy(projection_seed)
    projections = {name: [row_for_report(name, projection_seed, 1)] for name in projection_report_names}
    projection_failures = []
    _validate_interpret_back_and_proofs(projections, projection_failures)
    _validate_mapping_projection_consistency_v1(projections, projection_failures)
    assert projection_failures == []
    assert projection_seed == projection_seed_before
    for name, field, value in (
        (projection_names[2], "expected_original_objective_value", None),
        (projection_names[2], "expected_encoded_objective_value", 123.0),
        (projection_names[1], "original_variable_assignment", {}),
        (projection_names[1], "proof_vector_ref", "foreign-proof"),
        (projection_names[2], "candidate_packet_id", "foreign-packet"),
        (projection_names[1], "reverse_transform_rule", "choose argmax and overwrite execution_route_id"),
    ):
        changed = deepcopy(projections)
        changed[name][0][field] = value
        projection_failures = []
        _validate_mapping_projection_consistency_v1(changed, projection_failures)
        assert projection_failures == ["MAPPING_PROJECTION_MISMATCH"]
    for name in projection_report_names:
        changed = deepcopy(projections)
        changed[name] = []
        projection_failures = []
        _validate_mapping_projection_consistency_v1(changed, projection_failures)
        assert projection_failures == ["MAPPING_PROJECTION_MISMATCH"]
    # A valid current inverse may retain several case bits without one-hot.
    # Its serialized interpretation must not invent a unique route.
    projection_report_names = tuple(c.ROW_REPORTS)
    projection_seed = deepcopy(model_fixture)
    if projection_seed["model_family_selected"] != "DQM":
        sample = dict(projection_seed["encoded_variable_assignment"])
        sample.update(case_skip=1, case_precompute=0, case_retest=1, case_owner_review=0)
        projection_seed.update(_mapping_solution_v1(projection_seed, sample))
        projections = {name: [row_for_report(name, projection_seed, 1)] for name in projection_report_names}
        projection_failures = []
        _validate_interpret_back_and_proofs(projections, projection_failures)
        _validate_mapping_projection_consistency_v1(projections, projection_failures)
        assert projection_failures == []
        assert projections[projection_names[1]][0]["original_variable_assignment"]["route_case"] is None

    # Distinct packets must not share a business-reference identity.
    for key, related in (("proof_vector_id", "proof_vector_ref"), ("mapping_row_ref", "source_mapping_row_ref"), ("test_vector_ref", "test_vector_id")):
        changed = deepcopy(projections)
        for name in projection_report_names:
            other = deepcopy(changed[name][0])
            other["candidate_packet_id"] += "-distinct-packet"
            other["row_id"] += "-distinct-row"
            for distinct_key, distinct_ref in (("proof_vector_id", "proof_vector_ref"), ("mapping_row_ref", "source_mapping_row_ref"), ("test_vector_ref", "test_vector_id")):
                other[distinct_key] += "-distinct-reference"
                if distinct_ref in other:
                    other[distinct_ref] = other[distinct_key]
            other[key] = changed[name][0][key]
            if related in other:
                other[related] = other[key]
            changed[name].append(other)
        projection_failures = []
        _validate_mapping_projection_consistency_v1(changed, projection_failures)
        assert projection_failures == ["MAPPING_PROJECTION_MISMATCH"]

    # Crosswalk projection counts must reflect the final inline reports and
    # actual acquisition-ledger counts, never the pre-convergence empty state.
    from copy import deepcopy as publication_copy
    from types import SimpleNamespace as PublicationSource
    from unittest.mock import patch as publication_patch
    from pathlib import Path as PublicationPath
    from src.qtt.stage1_prediction_markets.pr162e_q_quantum_automapper import report_writer as publication_writer
    from src.qtt.stage1_prediction_markets.pr162e_q_quantum_automapper.validator import _validate_crosswalk_and_artifacts as publication_validate

    publication_rows = {name: [] for name in publication_writer.c.REPORT_FILENAMES}
    for name in publication_writer.c.ROW_REPORTS:
        publication_rows[name] = [{
            "row_id": name + "::fixture", "no_orphan_status": "NO_ORPHAN",
            "artifact_refs_checked": ["synthetic-count-test"],
        }]
    publication_rows["PR162E_Q_InputConsumption.report.json"] = [
        {"source_report_ref": name, "expanded_record_count": 3}
        for name in publication_writer.c.STRICT_INPUT_REPORTS
    ]
    publication_rows["PR162E_Q_FinalSummary.report.json"] = [{"synthetic": True}]
    with publication_patch.object(publication_writer, "load_sources", return_value=PublicationSource()), \
         publication_patch.object(publication_writer, "build_candidate_contexts", return_value=[]), \
         publication_patch.object(publication_writer, "select_deep_mapping_subset", return_value=set()), \
         publication_patch.object(publication_writer, "build_row_payloads", side_effect=lambda *_: publication_copy(publication_rows)):
        publication_payloads, publication_shards = publication_writer.build_payloads_with_shards(PublicationPath("."))
    publication_records = {
        name: (
            [row for path in payload.get("shard_files", []) for row in publication_shards[path]["records"]]
            if payload.get("sharded_flag") else payload["records"]
        ) for name, payload in publication_payloads.items()
    }
    publication_crosswalk = publication_records["PR162E_Q_ReportConsumerCrosswalk.report.json"]
    assert all(
        row["record_count"] == (
            publication_payloads[row["report_path"].rsplit("/", 1)[-1]]["record_count"]
            if row["report_path"].rsplit("/", 1)[-1] in publication_payloads else 3
        ) for row in publication_crosswalk
    )
    publication_failures = []
    publication_validate(publication_records, publication_failures)
    assert publication_failures == []
    for invalid in (0, True, 3.0, "3", None):
        publication_bad = publication_copy(publication_records)
        publication_bad["PR162E_Q_ReportConsumerCrosswalk.report.json"][0]["record_count"] = invalid
        publication_failures = []
        publication_validate(publication_bad, publication_failures)
        assert "CROSSWALK_COUNT_OR_COVERAGE_MISMATCH" in publication_failures

    # A second fill pass must charge only newly selected references. The eight
    # champion rows consume eight slots, not sixteen, under the original cap.
    from src.qtt.stage1_prediction_markets.pr162e_q_quantum_automapper.report_writer import select_deep_mapping_subset
    family_cap = c.MAP_CAPS["max_rows_per_model_family_default_ci"]
    selector_rows = [
        {"upstream_pr166_qc_row_ref": f"selection::{i:05d}", "model_family": "QUBO",
         "handoff": {"paper_champion_flag": i < family_cap // 2}}
        for i in range(family_cap + 4)
    ]
    selected_refs = select_deep_mapping_subset(selector_rows)
    assert len(selected_refs) == family_cap
    assert selected_refs == {row["upstream_pr166_qc_row_ref"] for row in selector_rows[:family_cap]}

    # Independent decoded files do not share nested object aliases. A changed
    # recipe on any row report must not hide behind an unchanged proof copy.
    all_projections = {name: [row_for_report(name, deepcopy(model_fixture), 1)] for name in c.ROW_REPORTS}
    projection_failures = []
    _validate_mapping_projection_consistency_v1(all_projections, projection_failures)
    assert projection_failures == []
    for name in c.ROW_REPORTS:
        if name == "PR162E_Q_MapProof.report.json":
            continue
        changed = deepcopy(all_projections)
        changed[name][0]["recipe_payload"]["qubo"]["Q"]["x_select,x_select"] += 0.5
        projection_failures = []
        _validate_mapping_projection_consistency_v1(changed, projection_failures)
        assert projection_failures == ["MAPPING_PROJECTION_MISMATCH"]
    for field, wrong in (
        ("constraint_native_flag", not model_fixture["constraint_native_flag"]),
        ("coefficient_scaling_status", "SCALED_TO_UNIT_INTERVAL_WITH_DYNAMIC_RANGE_RECORDED"),
        ("canonical_variable_signature", "x_select,x_size_bits,x_side_case"),
        ("canonical_constraint_signature", "budget<=1"),
        ("slack_variable_plan", "BINARY_SLACK_INSERTED"),
        ("discrete_case_handling", "ONE_FOUR_CASE_VARIABLE"),
    ):
        changed = deepcopy(all_projections)
        for rows in changed.values():
            rows[0][field] = wrong
        projection_failures = []
        _validate_mapping_projection_consistency_v1(changed, projection_failures)
        assert projection_failures == ["MAPPING_PROJECTION_MISMATCH"]


def test_pr162e_q_recipe_reports_are_computable_not_label_only():
    for filename in (
        "PR162E_Q_QUBORecipe.report.json",
        "PR162E_Q_BQMRecipe.report.json",
        "PR162E_Q_IsingRecipe.report.json",
        "PR162E_Q_CQMRecipe.report.json",
        "PR162E_Q_DQMRecipe.report.json",
        "PR162E_Q_QuadProgramRecipe.report.json",
        "PR162E_Q_HybridRecipe.report.json",
    ):
        rows = assert_report_contract(filename, 559)
        assert all(row["recipe_payload"] for row in rows)
        assert all(row["objective_terms"] for row in rows)
        assert all(row["decision_variables"] for row in rows)
        assert all(row["solution_interpret_back_ref"] for row in rows)
        assert all(row["proof_vector_ref"] for row in rows)


def test_pr162e_q_tca_overfit_portfolio_regime_and_edge_are_materialized():
    for filename in (
        "PR162E_Q_TCAMapImpact.report.json",
        "PR162E_Q_OverfitFDRMapRisk.report.json",
        "PR162E_Q_PortfolioUtilityMap.report.json",
        "PR162E_Q_RegimeMapMemory.report.json",
        "PR162E_Q_EdgeAttribution.report.json",
        "PR162E_Q_MapSensitivityStress.report.json",
        "PR162E_Q_ExecutionAdjustedMapRank.report.json",
    ):
        rows = assert_report_contract(filename, 559)
        assert all(row["total_tca_estimate"] >= 0 for row in rows)
        assert all(row["tca_reason_codes"] for row in rows)
        assert all("FEE" in row["tca_reason_codes"][0] for row in rows)
        assert all(row["false_discovery_penalty"] >= 0 for row in rows)
        assert all(row["final_marginal_utility_mapping_score"] >= 0 for row in rows)
        assert all(row["scenario_similarity_key"] for row in rows)
        assert all(row["not_profit_evidence_flag"] is True for row in rows)


def test_pr162e_q_repairs_handoffs_dashboard_connector_and_portability():
    repairs = assert_report_contract("PR162E_Q_StillNegativeMapRepair.report.json", 559)
    still_negative = [row for row in repairs if row["still_negative_after_costs_flag"]]
    assert len(still_negative) == summary()["still_negative_map_repair_count"] == 385
    assert all(row["repair_mapping_flag"] is True for row in still_negative)
    assert all(row["not_profit_evidence_flag"] is True for row in repairs)

    assert len([row for row in records("PR162E_Q_OpenTradeSimMap.report.json") if row["open_trade_sim_route_flag"]]) == 61
    assert len([row for row in records("PR162E_Q_OwnerDashboardMapReview.report.json") if row["owner_dashboard_review_flag"]]) == 438

    for filename in (
        "PR162E_Q_To_PR166_QC_Retest.report.json",
        "PR162E_Q_To_PR167.report.json",
        "PR162E_Q_To_PR162E.report.json",
        "PR162E_Q_To_PR162F.report.json",
        "PR162E_Q_To_OwnerDashboard.report.json",
        "PR162E_Q_To_CloudSwitchboard.report.json",
        "PR162E_Q_To_FutureConnectors.report.json",
        "PR162E_Q_ConnectorRouteReady.report.json",
        "PR162E_Q_MarketPortability.report.json",
    ):
        rows = assert_report_contract(filename, 559)
        assert all(row["no_live_authority_flag"] is True for row in rows)
        assert all(row["connector_semantic_binding_flag"] is False for row in rows)
        assert all(row["source_truth_acceptance_flag"] is False for row in rows)

    portability = records("PR162E_Q_MarketPortability.report.json")
    assert all(row["stage1_prediction_market_flag"] is True for row in portability)
    assert all(row["future_market_portability_flag"] is True for row in portability)
    assert all(row["no_current_connector_binding_flag"] is True for row in portability)


def test_pr162e_q_crosswalk_artifact_agent_and_no_orphan_maps():
    crosswalk = assert_report_contract("PR162E_Q_ReportConsumerCrosswalk.report.json")
    assert len(crosswalk) >= len(c.REPORT_FILENAMES) + len(c.STRICT_INPUT_REPORTS)
    assert all(
        row["consuming_agent_ids"] or row["consuming_downstream_reports"] or row["terminal_flag"]
        for row in crosswalk
    )

    artifact_rows = assert_report_contract("PR162E_Q_ArtifactMap.report.json")
    assert all(
        row["consumed_by_agent"] or row["consumed_by_report"] or row["terminal_flag"]
        for row in artifact_rows
    )
    assert any(row["artifact_type"] == "generated_schema" for row in artifact_rows)
    assert any(row["artifact_type"] == "generated_shard_report" for row in artifact_rows)

    assert_report_contract("PR162E_Q_AgentWorkOrders.report.json", 559)
    dag = assert_report_contract("PR162E_Q_AgentDAG.report.json", 559)
    assert all(row["downstream_agent_refs"] for row in dag)
    no_orphan = assert_report_contract("PR162E_Q_NoOrphanProof.report.json", 559)
    assert all(row["no_orphan_status"] == "NO_ORPHAN" for row in no_orphan)
    assert all(row["orphan_count"] == 0 for row in no_orphan)


def test_pr162e_q_summary_counts_match_ledgers():
    final = summary()
    eligibility = records("PR162E_Q_MapEligibility.report.json")
    assert final["automapper_disposition_counts"] == dict(
        sorted(Counter(row["automapper_disposition"] for row in eligibility).items())
    )
    assert final["mapping_quality_grade_counts"] == dict(
        sorted(Counter(row["mapping_quality_grade"] for row in eligibility).items())
    )
    assert final["model_family_selected_counts"] == dict(
        sorted(Counter(row["model_family_selected"] for row in eligibility).items())
    )
    assert payload("PR162E_Q_FinalSummary.report.json")["record_count"] == 1
