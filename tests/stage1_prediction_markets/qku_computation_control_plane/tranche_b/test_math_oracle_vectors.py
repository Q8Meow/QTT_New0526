import json
from decimal import Decimal

import pytest

from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import (
    NumericDomainError,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.implementation_registry import (
    IMPLEMENTATION_REGISTRY,
    invoke_formula_v34,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.oracle_contracts import (
    GOLDEN_VECTOR_BY_MATH_ID,
    ORACLE_BY_MATH_ID,
    ST12B_PROPERTY_TESTS,
    ST12B_VECTOR_PACK,
    ST12B_VECTORS_BY_MATH_ID,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.serialization import (
    deterministic_json,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.specification import (
    FROZEN_FORMULA_INPUT_CONTRACTS,
    FROZEN_FORMULA_REQUIREMENTS,
    FROZEN_NAMED_OUTPUT_CONTRACTS,
    validate_formula_output_v34,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.validation import (
    validate_all_st12b_vectors,
    validate_st12b_property_mutations,
)


def test_all_real_callables_and_exact_io_contracts_are_closed() -> None:
    math_ids = tuple(FROZEN_FORMULA_REQUIREMENTS)

    assert len(math_ids) == 30
    assert tuple(IMPLEMENTATION_REGISTRY) == math_ids
    assert tuple(FROZEN_FORMULA_INPUT_CONTRACTS) == math_ids
    assert tuple(FROZEN_NAMED_OUTPUT_CONTRACTS) == math_ids
    assert all(callable(row.callable) for row in IMPLEMENTATION_REGISTRY.values())
    assert sum(
        len(contract.members)
        for contract in FROZEN_NAMED_OUTPUT_CONTRACTS.values()
    ) == 130

    for math_id in math_ids:
        inputs = json.loads(GOLDEN_VECTOR_BY_MATH_ID[math_id].inputs_json)
        assert tuple(inputs) != ()
        assert set(inputs) == set(
            FROZEN_FORMULA_INPUT_CONTRACTS[math_id].declared_input_keys
        )
        validate_formula_output_v34(math_id, invoke_formula_v34(math_id, inputs))
    _assert_lp03_existing_public_invocation_profiles()
    _assert_lp03_private_input_contracts()
    _assert_lp03_private_raw_decoding()
    _assert_lp03_private_wire_invocations()
    _assert_lp03_public_recursive_raw_decoding()
    _assert_lp03_bounded_projection_encoding()
    _assert_lp03_projection_contracts_and_bounds()


def _assert_lp03_projection_case(math_id, raw, independent_expected):
    """Projection expectations use separately owned vectors/literal fixtures."""
    from fractions import Fraction
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.evidence import (
        EVIDENCE_PROJECTION_CONTRACTS_V1, project_evidence_raw_data_v1,
    )
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import ComputationControlPlaneError
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.validation import _canonical_vector_equal
    number = int(math_id[-2:])
    contract = EVIDENCE_PROJECTION_CONTRACTS_V1[math_id]
    numerical = number in (29, 30, 31, 37)
    work = _lp03_numeric_work(dict(max_input_bits=4096, max_work_bits=16384, max_serialized_bytes=65536)) if numerical else None
    kwargs = dict(maximum_raw_bytes=1048576, maximum_raw_nodes=4096,
                  maximum_projection_bytes=1048576, maximum_projection_nodes=4096,
                  output_unit="squared probability error" if math_id == "MATH-08" else "SYNTHETIC::EXPLICIT_UNIT",
                  output_basis=contract.basis_requirement, numerical_work=work)
    if number in (20, 21, 22, 50, 51, 52):
        reason = ("MISSING_PREDICTION_PRODUCER" if number in (20, 21) else
                  "UNCERTAINTY_UNAVAILABLE" if number == 22 else "LP03_ORIGINAL_QUANTUM_CONSTRUCTOR_REQUIRED")
        with pytest.raises(ComputationControlPlaneError, match=reason):
            project_evidence_raw_data_v1(math_id, raw, **kwargs)
        return
    result = project_evidence_raw_data_v1(math_id, raw, **kwargs)
    assert result.original_raw_json is raw and result.contract is contract
    actual = json.loads(result.projection_data_json)
    assert set(actual) == {"projected_value", "numerical_conversion", "output_unit", "output_basis"}
    assert actual["output_unit"] == kwargs["output_unit"] and actual["output_basis"] == kwargs["output_basis"]
    # Selection ownership here is independent of the production selector table.
    fields = {5: "relative_spread_ratio", 6: "expected_net_cash", 7: "expected_net_cash", 8: "mean_brier_score",
        9: "mean_log_loss", 10: "expected_calibration_error", 17: "probabilistic_sharpe_ratio", 18: "deflated_sharpe_ratio",
        23: "inverse_propensity_score_estimate", 24: "self_normalized_ips_estimate", 27: "raw_fraction",
        30: "conditional_value_at_risk", 34: "amount_after_rounding", 35: "amount_after_rounding"}
    expected = independent_expected
    if number in fields:
        expected = expected[fields[number]]
    if number == 11:
        expected = [expected["lower"], expected["upper"]]
    elif number in (12, 13):
        expected = dict(rows=[dict(original_index=i, adjusted_p=p, rejected=i in expected["rejected_original_indices"])
                              for i, p in enumerate(expected["adjusted_p_values"])],
                        largest_rank=expected["largest_rank"], correction=expected["correction"])
    elif number == 45:
        expected = dict(decision="POSITIVE_NET_LCB" if expected["trade_gate"] else "NONPOSITIVE_NET_LCB",
                        lcb_net=expected["lcb_net"], raw_gate=expected["trade_gate"], no_order_authority=True)
    if numerical:
        exact = Fraction(Decimal(expected))
        certificate = actual["numerical_conversion"]
        def rational(name):
            return Fraction(int(certificate[name]["numerator"]), int(certificate[name]["denominator"]))
        assert rational("exact_source") == exact
        assert certificate["analytic_value"] == float(exact)
        assert rational("signed_error") == Fraction.from_float(certificate["analytic_value"]) - exact
        assert rational("enclosing_lower") <= exact <= rational("enclosing_upper")
        assert certificate["math_id"] == math_id and certificate["unit"] == kwargs["output_unit"]
        assert certificate["basis"] == kwargs["output_basis"] and certificate["profile"] == "EXACT_TO_BINARY64_CELL_V1"
        assert work.consumed["retained_decimal_inputs"] == work.consumed["decimal_constructions"] == 1
        assert work.state == "OPEN" and work.consumed["serialized_bytes"] > len(result.projection_data_json)
        expected = float(exact)
    else:
        assert actual["numerical_conversion"] is None
    assert set(actual["projected_value"]) == {contract.output_name}
    projected = actual["projected_value"][contract.output_name]
    def financial_values(item):
        if type(item) is str:
            try:
                return Decimal(item)
            except ArithmeticError:
                return item
        if isinstance(item, dict) or hasattr(item, "keys"):
            return {key: financial_values(child) for key, child in item.items()}
        if isinstance(item, (tuple, list)):
            return [financial_values(child) for child in item]
        return item
    assert _canonical_vector_equal(financial_values(projected), financial_values(expected)), math_id
    if not numerical:
        original_wire = json.loads(raw)
        if number not in (11, 12, 13, 45):
            # Independently expected numbers above; exact raw representation
            # and companions remain unchanged through this selection below.
            assert projected == (original_wire[fields[number]] if number in fields else original_wire)
        elif number == 45:
            assert projected["lcb_net"] == original_wire["lcb_net"]
    return result


def _assert_lp03_projection_contracts_and_bounds():
    from unittest.mock import patch
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane import evidence
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import ComputationControlPlaneError
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane import serialization
    project = evidence.project_evidence_raw_data_v1
    names = ("p_market", "edge_probability", "mid", "spread", "relative_spread", "expected_net_cash", "expected_net_cash",
        "brier_score", "log_loss", "ece", "interval", "rejections_and_adjusted_p", "rejections_and_adjusted_p",
        "bootstrap_distribution_and_interval", "reality_check_receipt", "spa_receipt", "psr", "dsr", "pbo_receipt",
        "split_indices", "cpcv_paths", "dr_value_and_uncertainty", "ips_value", "snips_value", "switch_value_and_selected_tau",
        "evi", "full_kelly_fraction", "bounded_fraction", "utility", "cvar", "expected_shortfall", "implementation_shortfall",
        "spread_cost", "fee", "signed_fee_or_rebate", "derived_yes_and_no_touches", "fill_probability", "expected_fill_quantity",
        "queue_ahead_estimate", "signed_post_fill_markout", "decayed_edge", "impact_fraction", "capacity_penalty", "shrunk_covariance",
        "gate_decision", "recomputed_objective", "recomputed_objective", "benchmark_delta_packet")
    ids = tuple(f"MATH-{n:02d}" for n in (*range(1, 46), 50, 51, 52))
    contracts = evidence.EVIDENCE_PROJECTION_CONTRACTS_V1
    assert tuple(contracts) == ids and tuple(row.output_name for row in contracts.values()) == names
    for math_id in ids:
        assert contracts[math_id].schema_id == f"LP03::{math_id}::PROJECTION_V1"
        assert contracts[math_id].unit_requirement.startswith("original ")
    assert contracts["MATH-33"].basis_requirement == "SIGNED_EXECUTION_MINUS_DECISION_MIDPOINT_TIMES_QUANTITY"
    assert contracts["MATH-38"].basis_requirement == "EXPECTED_FILLED_QUANTITY_IN_DECLARED_UNITS"
    assert contracts["MATH-40"].basis_requirement == "SIGNED_QUANTITY_TIMES_POST_FILL_MIDPOINT_MINUS_FILL_PRICE"
    assert contracts["MATH-40"].direction_rule == "HIGHER_IS_BETTER"
    assert contracts["MATH-41"].basis_requirement == "REMAINING_EDGE_AMOUNT_AT_MEASURED_LATENCY"
    assert contracts["MATH-42"].basis_requirement == "SQUARE_ROOT_FRACTIONAL_PRICE_IMPACT"
    assert contracts["MATH-45"].direction_rule == "PRESENTATION_ONLY_NO_ORDER_AUTHORITY"
    # Legacy1.4 semantics remain byte-for-byte source-owned and separately read.
    legacy40 = next(row for row in evidence.ST12F_EVIDENCE_OUTPUT_BINDINGS_V1 if row.math_spec_id == "MATH-40")
    assert legacy40.output_name == "adverse_selection_cost"
    assert evidence.ST12F_METRIC_OUTPUT_BASIS_BY_MATH_ID_V1["MATH-38"] == "filled_fraction_of_requested_quantity"
    assert next(row for row in evidence.ST12F_EVIDENCE_METRIC_DEFINITIONS_V1 if row.math_spec_ref == "MATH-40").direction == "LOWER_IS_BETTER"

    def wire(value):
        return json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False, separators=(",", ":")).encode("utf-8")
    def args(number, **changes):
        values = dict(maximum_raw_bytes=65536, maximum_raw_nodes=4096, maximum_projection_bytes=65536,
                      maximum_projection_nodes=4096, output_unit="EXPLICIT::UNIT", output_basis=contracts[f"MATH-{number:02d}"].basis_requirement)
        return dict(values, **changes)
    def nodes(item):
        if type(item) is dict:
            return 1 + sum(1 + nodes(child) for child in item.values())
        if type(item) is list:
            return 1 + sum(map(nodes, item))
        return 1
    for number, raw_value in ((12, dict(adjusted_p_values=[0.01, 0.2, 0.7], rejected_original_indices=[0], largest_rank=1, correction=1.0)),
                              (13, dict(adjusted_p_values=[0.02, 0.4], rejected_original_indices=[0], largest_rank=1, correction=1.5)),
                              (40, "2.00"), (38, "7.50"), (45, dict(lcb_net="-0.00", trade_gate=False))):
        raw = wire(raw_value)
        result = _assert_lp03_projection_case(f"MATH-{number:02d}", raw, raw_value)
        baseline = project(f"MATH-{number:02d}", raw, **args(number))
        length, node_count = len(baseline.projection_data_json), nodes(json.loads(baseline.projection_data_json))
        assert project(f"MATH-{number:02d}", raw, **args(number, maximum_projection_bytes=length,
                       maximum_projection_nodes=node_count)).projection_data_json == baseline.projection_data_json
        for change in (dict(maximum_projection_bytes=length - 1), dict(maximum_projection_nodes=node_count - 1)):
            with pytest.raises(ComputationControlPlaneError):
                project(f"MATH-{number:02d}", raw, **args(number, **change))
    for raw_value in (dict(adjusted_p_values=[0.1], rejected_original_indices=[1], largest_rank=1, correction=1.0),
                      dict(adjusted_p_values=[0.1], rejected_original_indices=[0, 0], largest_rank=2, correction=1.0)):
        with pytest.raises(ComputationControlPlaneError):
            project("MATH-12", wire(raw_value), **args(12))
    for number, raw_value in ((11, dict(lower=0.8, upper=0.2)), (45, dict(lcb_net="0.1", trade_gate=False))):
        with pytest.raises(ComputationControlPlaneError):
            project(f"MATH-{number:02d}", wire(raw_value), **args(number))
    for number in (29, 30, 31, 37):
        raw = wire(dict(value_at_risk="1", conditional_value_at_risk="2", confidence="0.5") if number == 30 else "0.125")
        work = _lp03_numeric_work(dict(max_input_bits=4096, max_work_bits=16384, max_serialized_bytes=65536))
        with pytest.raises(ComputationControlPlaneError, match="LP03_PROJECTION_JSON_BYTES"):
            project(f"MATH-{number:02d}", raw, **args(number, maximum_projection_bytes=1), numerical_work=work)
        assert work.state == "FAILED" and work.consumed["decimal_constructions"] == 1 and work.consumed["serialized_bytes"] > 0
        with pytest.raises(ComputationControlPlaneError, match="LP03_NUMERICAL_WORK_NOT_OPEN"):
            project(f"MATH-{number:02d}", raw, **args(number), numerical_work=work)
    for text in ("-0", "1E-10000"):
        work = _lp03_numeric_work(dict(max_input_bits=65536, max_work_bits=131072, max_serialized_bytes=65536))
        with pytest.raises(ComputationControlPlaneError):
            project("MATH-29", wire(text), **args(29), numerical_work=work)
        assert work.state == "FAILED"
    # Numerical failure latching cannot erase an already typed outer failure.
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import ContractValidationError, ReasonCode
    original_failure = ContractValidationError(ReasonCode.INVALID_CONTRACT, "ORIGINAL_PROJECTION_FAILURE")
    for failure in (original_failure, ValueError("untyped arithmetic boundary")):
        work = _lp03_numeric_work(dict(max_input_bits=4096, max_work_bits=16384, max_serialized_bytes=65536))
        with pytest.raises(ComputationControlPlaneError) as observed:
            with work:
                raise failure
        assert work.state == "FAILED" and work.failure == "LP03_NUMERICAL_OPERATION_FAILED"
        if failure is original_failure:
            assert observed.value is original_failure
        else:
            assert observed.value is not failure and "LP03_NUMERICAL_OPERATION_FAILED" in str(observed.value)
    for change in (dict(output_basis="OLD_OR_WRONG_BASIS"), dict(output_unit="X" * 257), dict(maximum_projection_nodes=False)):
        with pytest.raises(ComputationControlPlaneError):
            project("MATH-03", b'"0.50"', **args(3, **change))
    brier_raw = b'{"mean_brier_score":0.125,"per_observation":[0.125]}'
    brier = project("MATH-08", brier_raw, **args(8, output_unit="squared probability error"))
    assert brier.original_raw_json is brier_raw and json.loads(brier.projection_data_json)["projected_value"] == {"brier_score": 0.125}
    for unit in ("SQUARED_PROBABILITY_ERROR", "USD/CONTRACT", "squared probability", "squared probability error "):
        with pytest.raises(ComputationControlPlaneError, match="LP03_PROJECTION_UNIT_MISMATCH"):
            project("MATH-08", brier_raw, **args(8, output_unit=unit))
    # Expanded rows cannot reach the final encoder when first-pass budgets fail.
    many = wire(dict(adjusted_p_values=[0.1] * 250, rejected_original_indices=[], largest_rank=0, correction=1.0))
    original_encode = serialization._encode_evidence_projection_json_v1
    def forbid_expansion(value, **kwargs):
        assert value["projected_value"]["rejections_and_adjusted_p"]["rows"] == []
        return original_encode(value, **kwargs)
    with patch.object(serialization, "_encode_evidence_projection_json_v1", side_effect=forbid_expansion):
        for change in (dict(maximum_projection_nodes=100), dict(maximum_projection_bytes=500)):
            with pytest.raises(ComputationControlPlaneError):
                project("MATH-12", many, **args(12, **change))
    for number in (46, 47, 48, 49, 53):
        with pytest.raises(ComputationControlPlaneError, match="LP03_PROJECTION_SCHEMA_UNAVAILABLE"):
            project(f"MATH-{number}", b'"0"', **args(3))


def _assert_lp03_bounded_projection_encoding() -> None:
    from collections.abc import Mapping
    from types import MappingProxyType
    from unittest.mock import patch
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane import serialization
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import ComputationControlPlaneError
    encode = serialization._encode_evidence_projection_json_v1
    cases = (None, True, False, 0, -(10 ** 100), 0.1, -0.0, 5e-324,
             "", "a\"\\\b\f\n\r\t\x00\x1f/\u00e9\u20ac\U0001f408\u2028",
             {"z": ["0.10", 0.1, False, None], "a": ((1, 2), (3, 4))})
    for value in cases:
        expected = json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        assert encode(value, maximum_bytes=len(expected), maximum_nodes=128) == expected
        if len(expected) > 1:
            with pytest.raises(ComputationControlPlaneError, match="LP03_PROJECTION_JSON_BYTES"):
                encode(value, maximum_bytes=len(expected) - 1, maximum_nodes=128)

    class HostileMapping(Mapping):
        def __iter__(self):
            raise AssertionError("foreign iteration reached")
        def __getitem__(self, key):
            raise AssertionError("foreign lookup reached")
        def __len__(self):
            raise AssertionError("foreign length reached")

    for value in (Decimal("1"), MappingProxyType({"value": 1}), MappingProxyType(HostileMapping()), HostileMapping(), object()):
        with pytest.raises(ComputationControlPlaneError, match="LP03_PROJECTION_JSON_NATIVE_DATA_REQUIRED"):
            encode(value, maximum_bytes=128, maximum_nodes=32)
    cyclic = []
    cyclic.append(cyclic)
    for value in (cyclic, [[[[[[[[[[[[[[[[[0]]]]]]]]]]]]]]]]], {1: "value"}, float("inf"), "\ud800"):
        with pytest.raises(ComputationControlPlaneError):
            encode(value, maximum_bytes=128, maximum_nodes=128)
    for value in ({"access_token": "blocked"}, {"output_path": "../escape"}):
        with pytest.raises(ComputationControlPlaneError):
            encode(value, maximum_bytes=128, maximum_nodes=128)
    with pytest.raises(ComputationControlPlaneError, match="LP03_PROJECTION_JSON_NODES_OR_DEPTH"):
        encode({"value": 1}, maximum_bytes=128, maximum_nodes=2)
    assert encode({"value": 1}, maximum_bytes=128, maximum_nodes=3) == b'{"value":1}'
    # Oversized strings (including keys), integers and zero budgets are denied
    # before any JSON token formatting. No proxy backing object is consulted.
    with patch.object(serialization.json, "dumps", side_effect=AssertionError("token allocation reached")):
        for value, byte_limit in (("x" * 100001, 128), ({"x" * 100001: 1}, 128),
                                 ({"x" * 100 + "a": 1, "x" * 100 + "b": 1}, 128),
                                 (1 << 100001, 128), ("ok", 0)):
            with pytest.raises(ComputationControlPlaneError):
                encode(value, maximum_bytes=byte_limit, maximum_nodes=128)
    with patch.object(serialization, "_check_path_value", side_effect=AssertionError("path traversal reached")), \
         patch.object(serialization, "validate_relative_path", side_effect=AssertionError("path allocation reached")):
        for value in ({"output_path": "x" * 100001}, {"output_paths": ["x"] * 100001}):
            with pytest.raises(ComputationControlPlaneError):
                encode(value, maximum_bytes=128, maximum_nodes=128)


def _assert_lp03_public_recursive_raw_decoding() -> None:
    from types import MappingProxyType
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.specification import decode_evidence_raw_output_v1
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.validation import _canonical_vector_equal
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import ComputationControlPlaneError

    def decode(math_id, raw):
        return decode_evidence_raw_output_v1(math_id, raw, maximum_bytes=1048576, maximum_nodes=4096)

    def assert_native_order(actual, decoded):
        if type(actual) is dict:
            assert type(decoded) is MappingProxyType and tuple(decoded) == tuple(actual)
            for name in actual:
                assert_native_order(actual[name], decoded[name])
        elif type(actual) is tuple:
            assert type(decoded) is tuple and len(decoded) == len(actual)
            for first, second in zip(actual, decoded, strict=True):
                assert_native_order(first, second)
        else:
            assert type(actual) is type(decoded) and actual == decoded

    original_wires = {}
    for number in (*range(1, 26), 36):
        math_id = f"MATH-{number:02d}"
        for vector in ST12B_VECTORS_BY_MATH_ID[math_id]:
            if vector.case_type == "NEGATIVE":
                continue
            actual = invoke_formula_v34(math_id, vector.inputs)
            raw = deterministic_json(actual).encode("utf-8")
            decoded = decode(math_id, raw)
            # Numerical expectations remain owned by the original independent
            # vectors; production output is used only to exercise its codec.
            assert _canonical_vector_equal(decoded, vector.expected), vector.vector_id
            assert_native_order(actual, decoded)
            assert deterministic_json(decoded).encode("utf-8") == raw
            _assert_lp03_projection_case(math_id, raw, vector.expected)
            original_wires.setdefault(math_id, raw)
    assert decode("MATH-39", b'"3"') == Decimal("3")
    _assert_lp03_projection_case("MATH-39", b'"3"', "3")
    with pytest.raises(ComputationControlPlaneError):
        decode("MATH-39", b'"-1"')

    def mutated(number, path, field, replacement):
        math_id = f"MATH-{number:02d}"
        body = json.loads(original_wires[math_id])
        target = body
        for name in path:
            target = target[name]
        target[field] = replacement
        raw = json.dumps(body, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
        with pytest.raises(ComputationControlPlaneError):
            decode(math_id, raw)

    # Every formerly opaque nested-record family rejects unknown members.
    for number, path in ((10, ("bins", 0)), (19, ("splits", 0)), (20, ("folds", 0)),
                         (21, ("splits", 0)), (21, ("paths", 0)), (25, ("outer_fold_results", 0)),
                         (25, ("outer_fold_results", 0, "criteria", 0))):
        mutated(number, path, "unknown_member", "1")
    mutated(10, ("bins", 0), "count", False)
    mutated(19, ("splits", 0), "train_groups", [False])
    mutated(19, ("splits", 0), "is_winner_strategy_id", 1)
    mutated(20, ("folds", 0), "merged_test_intervals", [[0.0, 1.0, 2.0]])
    mutated(20, ("folds", 0), "merged_test_intervals", [[0, 1.0]])
    mutated(20, ("folds", 0), "merged_test_intervals", [[1.0, 0.0]])
    mutated(21, ("paths", 0), "split_ids", [False])
    mutated(21, ("paths", 0), "test_group_partition", [[False]])
    mutated(25, ("outer_fold_results", 0), "selected_tau", "Infinity")
    mutated(25, ("outer_fold_results", 0, "criteria", 0), "tau", 1)
    mutated(25, ("outer_fold_results", 0), "held_out_row_values", ["0.1"])
    mutated(7, (), "normalized_probabilities", [0.5, 0.5])
    mutated(12, (), "rejected_original_indices", [False])
    mutated(16, (), "consistent_valid_columns", [1])

    bins = json.loads(original_wires["MATH-10"])
    first = bins["bins"][0]
    first.update(count=0, mean_confidence=None, empirical_frequency=None, absolute_gap=None)
    raw = json.dumps(bins, sort_keys=True, separators=(",", ":")).encode("utf-8")
    assert decode("MATH-10", raw)["bins"][0]["mean_confidence"] is None
    for change in (dict(count=1), dict(mean_confidence=0.0)):
        body = json.loads(raw)
        body["bins"][0].update(change)
        with pytest.raises(ComputationControlPlaneError, match="LP03_RAW_EMPTY_BIN_NULLABILITY"):
            decode("MATH-10", json.dumps(body, sort_keys=True, separators=(",", ":")).encode("utf-8"))
    for number in (46, 47, 48, 49, 53):
        with pytest.raises(ComputationControlPlaneError, match="LP03_RAW_SCHEMA_UNAVAILABLE"):
            decode(f"MATH-{number}", b'"0"')


def _assert_lp03_private_wire_invocations() -> None:
    import sys
    from dataclasses import replace
    from datetime import timedelta
    from decimal import Inexact, ROUND_DOWN, localcontext
    from types import MappingProxyType
    from unittest.mock import patch
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane import implementation_registry as owner, serialization
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.implementation_registry import (
        _evidence_snapshot_version_pins_v1, resolve_evidence_invocation_v1, invoke_evidence_private_wire_v1,
        invoke_evidence_formula_v1, CURRENT_IMPLEMENTATION_REGISTRY,
    )
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.input_resolver import decode_evidence_private_inputs_v1
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.specification import decode_evidence_private_raw_output_v1
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.models import EvidenceOriginV1
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import ComputationControlPlaneError
    specifications, implementations = _evidence_snapshot_version_pins_v1()

    def contract(number):
        math_id = f"MATH-{number:02d}"
        return resolve_evidence_invocation_v1(math_id, implementation_pin=implementations[math_id],
            specification_pin=specifications[math_id], resource_policy_ref="LP03-TEST::WIRE-RESOURCES",
            origin=EvidenceOriginV1.SOFTWARE_CONFORMANCE)

    def wire(value):
        return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode("utf-8")

    selected = (*range(1, 46), 50, 51, 52)
    assert len(selected) == 48 and len(CURRENT_IMPLEMENTATION_REGISTRY) == 31
    for number in selected:
        row = contract(number)
        assert row.math_id == f"MATH-{number:02d}" and row.evidence_projection_version == "1.5"
        # Preserve the actual frozen B oracle identity; C/D/F use their own
        # original unsuffixed identities rather than an invented normalization.
        suffix = "::V3_4" if number in (*range(1, 26), 36) else ""
        assert row.oracle_ref == f"ORACLE::MATH-{number:02d}" + suffix
        if number in (*range(26, 36), 37, 38, *range(40, 46), 50, 51, 52):
            assert row.input_schema_ref == f"LP03::MATH-{number:02d}::INPUT_V1"
            assert row.raw_output_schema_ref == f"LP03::MATH-{number:02d}::RAW_V1"
            assert row.raw_contract_version == ("ST12C-CURRENTIZED-1.0" if number < 40 else "1.4")
            with pytest.raises(ComputationControlPlaneError, match="LP03_PRIVATE_WIRE_INPUT_REQUIRED"):
                invoke_evidence_formula_v1(row, {})

    # Exact independently selected tiny examples; these are mathematical data,
    # not accepted fee/model records, current owner policies or lane grants.
    schedule = dict(binding_ref="WIRE::schedule", venue_ref="WIRE::synthetic", market_or_category_ref="WIRE::market",
        schedule_version="1", source_epoch_ref="WIRE::epoch", valid_from="2026-01-01T00:00:00+00:00",
        valid_until="2026-01-02T00:00:00+00:00", evaluated_at="2026-01-01T00:00:01+00:00",
        component_classes=["PLATFORM_FEE"], component_rate_bindings=[["PLATFORM_FEE", "0.05"]])
    rounding = dict(policy_id="WIRE::policy", field_id="fee", increment="0.00001", rounding="ROUND_HALF_EVEN",
        unit="USD", currency_or_asset="USD", basis="CONTRACT", scale=5, source_binding_ref="WIRE::schedule")
    artifact = dict(artifact_id="WIRE::artifact", artifact_version="1", feature_schema_ref="WIRE::features",
        calibration_receipt_ref="WIRE::calibration", scope_ref="WIRE::scope", horizon_seconds=5, probability="0.60",
        feature_snapshot_ref="WIRE::snapshot", feature_observed_at="2026-01-01T00:00:00+00:00",
        evaluated_at="2026-01-01T00:00:00.000001+00:00", artifact_valid_until="2026-01-01T00:00:01+00:00",
        maximum_feature_age=dict(days=0, seconds=0, microseconds=1), calibration_state="VALIDATED")
    distribution = dict(artifact_id="WIRE::distribution", artifact_version="1", source_binding_ref="WIRE::source",
        scope_ref="WIRE::scope", horizon_seconds=5, evaluated_at="2026-01-01T00:00:00+00:00",
        artifact_valid_until="2026-01-01T00:00:01+00:00", order_quantity="10", normalization_tolerance="0",
        fill_quantity_distribution=[["0", "0.25"], ["10", "0.75"]])
    examples = {
        26: (dict(current_action_values=["1", "2"], new_information_scenarios=[["0.5", ["3", "1"]], ["0.5", ["1", "5"]]], acquisition_cost="0.5"), Decimal("1.5")),
        27: (dict(win_probability="0.6", net_odds="2"), dict(raw_fraction="0.4", sizing_candidate="0.4")),
        28: (dict(full_kelly_fraction="0.4", fraction_multiplier="0.5", risk_caps=["0.3", "0.15"]), Decimal("0.15")),
        29: (dict(weights=["0.5", "0.5"], expected_returns=["0.1", "0.2"], covariance=[["0.04", "0"], ["0", "0.04"]], risk_aversion="2", transaction_cost="0.01"), Decimal("0.12")),
        30: (dict(losses=["1", "2", "3", "4"], alpha="0.5"), dict(value_at_risk="3", conditional_value_at_risk="3.5", confidence="0.5")),
        31: (dict(losses=["1", "2", "3", "4"], alpha="0.5"), Decimal("3.5")),
        32: (dict(side="BUY", quantity="2", execution_price="0.6", decision_price="0.5", explicit_fees="0.02", opportunity_cost_unfilled="0.03", other_declared_costs="0.01"), Decimal("0.26")),
        33: (dict(side="SELL", quantity="2", execution_price="0.4", midpoint_at_decision="0.5"), Decimal("0.2")),
        34: (dict(contracts="10", fee_rate="0.05", price="0.5", schedule_binding=schedule, quantization_policy=rounding, receipt_id="WIRE::fee"), Decimal("0.12500")),
        35: (dict(contracts="10", theta="-0.02", price="0.5", liquidity_role="MAKER", schedule_binding=dict(schedule, component_classes=["MAKER_REBATE"], component_rate_bindings=[["MAKER_REBATE", "-0.02"]]), quantization_policy=dict(rounding, increment="0.01", scale=2), receipt_id="WIRE::rebate"), Decimal("-0.05")),
        37: (dict(artifact=artifact, feature_schema_ref="WIRE::features", scope_ref="WIRE::scope", horizon_seconds=5), Decimal("0.60")),
        38: (dict(artifact=distribution), Decimal("7.50")),
        40: (dict(signed_fill_quantity="100", midpoint_after_fill="0.43", fill_price="0.45"), Decimal("-2.00")),
        41: (dict(edge_now=0.08, latency=0.0, tau=2.0), 0.08),
        42: (dict(Y=1.0, sigma=0.2, Q="25", ADV="100"), 0.1),
        43: (dict(participation=0.2, approved_participation_cap=0.1, penalty_scale=2.0), 2.0),
        44: (dict(sample_covariance=[[4.0, 0.0], [0.0, 2.0]], target=[[2.0, 0.0], [0.0, 2.0]], delta=0.5), ((3.0, 0.0), (0.0, 2.0))),
        45: (dict(estimated_net_edge="0.10", uncertainty="0.02", z_or_quantile="2", model_risk_haircut="0.01"), dict(lcb_net=Decimal("0.05"), trade_gate=True)),
    }
    for number, (values, expected) in examples.items():
        raw_inputs, row = wire(values), contract(number)
        result = invoke_evidence_private_wire_v1(row, raw_inputs, maximum_input_bytes=8192, maximum_nodes=1024,
                                                maximum_output_bytes=8192, maximum_output_nodes=1024)
        assert result.input_json is raw_inputs and result.contract is row and result.constructor_receipt_or_none is None
        assert type(result.decoded_inputs) is MappingProxyType
        if number in (27, 30):
            assert json.loads(deterministic_json(result.raw_result)) == expected
        elif number in (34, 35):
            assert result.raw_result.amount_after_rounding == expected
            assert result.raw_result.quantization_receipt.receipt_id == values["receipt_id"]
        else:
            assert result.raw_result == expected, number
        raw = result.output_json
        assert type(raw) is bytes and raw == deterministic_json(result.raw_result).encode("utf-8")
        assert result.decoded_output == result.raw_result
        assert result.actual_adapter is result.actual_callable
        assert result.actual_callable is (owner.TRANCHE_C_IMPLEMENTATION_REGISTRY[row.math_id].callable
            if number < 40 else owner._ST12F_NEW_EVIDENCE_CALLABLES_V1[row.math_id])
        assert decode_evidence_private_raw_output_v1(row.math_id, raw, maximum_bytes=8192, maximum_nodes=1024) == result.raw_result
        with localcontext() as hostile:
            hostile.prec, hostile.rounding = 2, ROUND_DOWN
            hostile.traps[Inexact] = True
            hostile.capitals = 0
            repeated = invoke_evidence_private_wire_v1(row, raw_inputs, maximum_input_bytes=8192, maximum_nodes=1024,
                maximum_output_bytes=8192, maximum_output_nodes=1024)
            assert repeated.raw_result == result.raw_result and repeated.output_json == raw
        with pytest.raises(ComputationControlPlaneError, match="LP03_PRIVATE_INVOCATION_CONTRACT_CHANGED"):
            invoke_evidence_private_wire_v1(replace(row, input_schema_ref="WRONG"), raw_inputs, maximum_input_bytes=8192, maximum_nodes=1024,
                maximum_output_bytes=8192, maximum_output_nodes=1024)
        with pytest.raises(ComputationControlPlaneError, match="LP03_PRIVATE_INPUT_FIELDS"):
            invoke_evidence_private_wire_v1(row, wire(dict(values, injected="1")), maximum_input_bytes=8192, maximum_nodes=1024,
                maximum_output_bytes=8192, maximum_output_nodes=1024)

    # Observe the retained callable without replacing it with a wrapper. The
    # original object returned by that one call must survive serialization.
    from types import CodeType
    calls, normalizations = [], []
    target = owner.TRANCHE_C_IMPLEMENTATION_REGISTRY["MATH-27"].callable
    code = target.__code__
    normalize_code = next(item for item in invoke_evidence_private_wire_v1.__code__.co_consts
                          if type(item) is CodeType and item.co_name == "normalize")
    previous_profile = sys.getprofile()
    def observe(frame, event, arg):
        if event == "return" and frame.f_code is code:
            calls.append(arg)
        if event == "call" and frame.f_code is normalize_code and frame.f_globals is owner.__dict__:
            normalizations.append(frame.f_code)
    def selected(output_bytes=8192, output_nodes=1024):
        return invoke_evidence_private_wire_v1(contract(27), wire(examples[27][0]),
            maximum_input_bytes=8192, maximum_nodes=1024,
            maximum_output_bytes=output_bytes, maximum_output_nodes=output_nodes)
    try:
        sys.setprofile(observe)
        result = selected()
        assert len(calls) == 1 and result.raw_result is calls[0]
        assert normalizations
        normalizations.clear()
        for byte_limit, node_limit in ((True, 10), (0, 10), (1048577, 10), (8192, True), (8192, 0), (8192, 4097)):
            with pytest.raises(ComputationControlPlaneError, match="LP03_PRIVATE_OUTPUT_BUDGET"):
                selected(byte_limit, node_limit)
        assert len(calls) == 1 and normalizations == []  # No invocation or normalization.
        # Both failures happen after exactly one original invocation and before
        # Decimal formatting/normalized graph construction in the final codec.
        with patch.object(serialization, "_encode_evidence_projection_json_v1", side_effect=AssertionError("premature formatting")):
            with pytest.raises(ComputationControlPlaneError, match="LP03_PRIVATE_OUTPUT_BYTES"):
                selected(500)
            with pytest.raises(ComputationControlPlaneError, match="LP03_PRIVATE_OUTPUT_NODES"):
                selected(output_nodes=4)
        assert len(calls) == 3 and normalizations == []
        assert selected(output_nodes=5).output_json == b'{"raw_fraction":"0.4","sizing_candidate":"0.4"}'
        assert len(calls) == 4 and normalizations
        with patch.object(owner, "TRANCHE_C_IMPLEMENTATION_REGISTRY", MappingProxyType(dict(owner.TRANCHE_C_IMPLEMENTATION_REGISTRY))):
            with pytest.raises(ComputationControlPlaneError, match="LP03_PRIVATE_ORIGINAL_CALLABLE_CHANGED"):
                selected()
        def replacement(**values):
            raise AssertionError("substituted original executed")
        try:
            target.__code__ = replacement.__code__
            with pytest.raises(ComputationControlPlaneError, match="LP03_PRIVATE_ORIGINAL_CALLABLE_CHANGED"):
                selected()
        finally:
            target.__code__ = code
        assert len(calls) == 4
    finally:
        sys.setprofile(previous_profile)
    float_row, float_inputs = contract(41), wire(examples[41][0])
    assert invoke_evidence_private_wire_v1(float_row, float_inputs, maximum_input_bytes=8192, maximum_nodes=1024,
        maximum_output_bytes=4, maximum_output_nodes=1).output_json == b'0.08'
    with pytest.raises(ComputationControlPlaneError, match="LP03_PRIVATE_OUTPUT_BYTES"):
        invoke_evidence_private_wire_v1(float_row, float_inputs, maximum_input_bytes=8192, maximum_nodes=1024,
            maximum_output_bytes=3, maximum_output_nodes=1)
    decoded = decode_evidence_private_inputs_v1("MATH-37", wire(examples[37][0]), maximum_bytes=8192, maximum_nodes=1024)
    assert decoded["artifact"].maximum_feature_age == timedelta(microseconds=1)
    for duration in (dict(days=False, seconds=0, microseconds=1), dict(days=0, seconds=86400, microseconds=0),
                     dict(days=0, seconds=0, microseconds=1000000), dict(days=0, seconds=0, microseconds=0), 0.000001):
        with pytest.raises(ComputationControlPlaneError):
            decode_evidence_private_inputs_v1("MATH-37", wire(dict(examples[37][0], artifact=dict(artifact, maximum_feature_age=duration))), maximum_bytes=8192, maximum_nodes=1024)
    for number, values in ((27, dict(win_probability=0.6, net_odds="2")),
                           (41, dict(edge_now="0.08", latency=0.0, tau=2.0)),
                           (38, dict(artifact=dict(distribution, extra="ignored"))),
                           (37, dict(examples[37][0], artifact=dict(artifact, calibration_state="UNVALIDATED")))):
        with pytest.raises(ComputationControlPlaneError):
            invoke_evidence_private_wire_v1(contract(number), wire(values), maximum_input_bytes=8192, maximum_nodes=1024,
                maximum_output_bytes=8192, maximum_output_nodes=1024)


def _assert_lp03_private_raw_decoding() -> None:
    from decimal import Inexact, ROUND_DOWN, localcontext
    from math import copysign
    from types import MappingProxyType
    from unittest.mock import patch
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane import serialization, specification
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.economic_math import (
        KellyFractionV1, TailRiskV1, QuantizedEconomicAmountV1,
    )
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import ComputationControlPlaneError

    decode = specification.decode_evidence_private_raw_output_v1
    # Literal schema fixtures, not formula outputs or production-built oracles.
    receipt = dict(receipt_id="RAW::rounding", policy_ref="RAW::policy", field_id="fee",
        pre_value="0.012345", post_value="0.01234", residual="0.000005", unit="USD",
        currency_or_asset="USD", basis="CONTRACT", scale=5, rounding="ROUND_HALF_EVEN")
    fee = dict(amount_before_rounding="0.012345", amount_after_rounding="0.01234",
        quantization_receipt=receipt, component_class="EXPLICIT_VENUE_FEE", source_binding_ref="RAW::schedule", embedded_in_price=False)
    rebate = dict(fee, amount_before_rounding="-0.015", amount_after_rounding="-0.02", component_class="EXPLICIT_MAKER_REBATE",
        quantization_receipt=dict(receipt, pre_value="-0.015", post_value="-0.02", residual="0.005", scale=2))
    fixtures = {
        26: "1.50", 27: dict(raw_fraction="0.25", sizing_candidate="0.25"), 28: "0.125",
        29: "0.100", 30: dict(value_at_risk="3", conditional_value_at_risk="4.0", confidence="0.90"),
        31: "4.0", 32: "0.20", 33: "-0.20", 34: fee, 35: rebate, 37: "0.60", 38: "7.50",
        40: "-2.00", 41: 0.1, 42: 0.25, 43: 0.5, 44: [[1.0, 0.2], [0.2, 2.0]],
        45: dict(lcb_net="0.10", trade_gate=True),
        50: dict(trace_expected_locked_cost="1.25", original_economic_objective="0.7",
                 selected_candidate_id="CANDIDATE::B", selected_original_model_feasible=True, effect_call_count=0),
        51: dict(trace_expectation="0.2", variance="0.01", original_economic_objective="0.55",
                 selected_candidate_id="POINT::B", selected_original_model_feasible=True, effect_call_count=0),
        52: dict(delta_quantum_vs_classical="0.05", delta_quantum_vs_no_trade="0.7", winner="VALIDATED_QUANTUM",
                 quantum_advantage_claim_allowed=False),
    }

    def wire(value):
        return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode("utf-8")

    assert set(specification.EVIDENCE_PRIVATE_RAW_OUTPUT_CONTRACTS_V1) == {f"MATH-{number:02d}" for number in fixtures}
    results = {}
    for number, value in fixtures.items():
        raw = wire(value)
        # Explicit finite conformance budgets; actual grants are tested elsewhere.
        result = decode(f"MATH-{number:02d}", raw, maximum_bytes=len(raw), maximum_nodes=128)
        results[number] = result
        assert deterministic_json(result).encode("utf-8") == raw
        _assert_lp03_projection_case(f"MATH-{number:02d}", raw, value)
        with localcontext() as hostile:
            hostile.prec, hostile.rounding = 2, ROUND_DOWN
            hostile.traps[Inexact] = True
            assert decode(f"MATH-{number:02d}", raw, maximum_bytes=len(raw), maximum_nodes=128) == result
    for number in (26, 28, 29, 31, 32, 33, 37, 38, 40):
        assert type(results[number]) is Decimal and str(results[number]) == fixtures[number]
    assert type(results[27]) is KellyFractionV1 and results[27].raw_fraction == Decimal("0.25")
    assert type(results[30]) is TailRiskV1 and results[30].conditional_value_at_risk == Decimal("4.0")
    for number, scale in ((34, 5), (35, 2)):
        assert type(results[number]) is QuantizedEconomicAmountV1 and results[number].quantization_receipt.scale == scale
    assert results[34].quantization_receipt.residual == Decimal("0.000005")
    assert results[35].amount_after_rounding == Decimal("-0.02")
    assert all(type(results[number]) is float for number in (41, 42, 43))
    assert results[44] == ((1.0, 0.2), (0.2, 2.0)) and all(type(row) is tuple for row in results[44])
    for number in (45, 50, 51, 52):
        assert type(results[number]) is MappingProxyType
        assert tuple(results[number]) == tuple(fixtures[number])
        with pytest.raises(TypeError):
            results[number][next(iter(results[number]))] = None

    # Full finite binary64 range, including signed zero, is confined to declared
    # float positions. The ordinary evidence JSON codec retains its denial.
    for value in (5e-324, -5e-324, float.fromhex("0x1.fffffffffffffp+1023"), -0.0):
        raw = wire(value)
        result = decode("MATH-41", raw, maximum_bytes=128, maximum_nodes=1)
        assert type(result) is float and result.hex() == value.hex()
        assert copysign(1, result) == copysign(1, value)
    for text in ("-0.00", "1.2300E+12", "0E-20"):
        result = decode("MATH-26", wire(text), maximum_bytes=64, maximum_nodes=1)
        assert str(result) == text
    with pytest.raises(ComputationControlPlaneError, match="LP03_EXACT_JSON_SCALAR"):
        serialization._evidence_canonical_object_v1(b'{"value":0.25}')

    negative = (
        (26, b'0.1'), (26, b'1'), (26, wire("NaN")), (26, wire("+1.0")),
        (41, b'1'), (41, b'1e999'), (41, b'1e-999'), (41, b'NaN'), (41, wire("0.1")),
        (44, wire([[1.0, 0.0], [0.0]])), (44, wire([[1]])),
        (45, wire(dict(fixtures[45], trade_gate=1))), (45, wire(dict(fixtures[45], unexpected=1))),
        (50, wire(dict(fixtures[50], effect_call_count=False))), (50, wire(dict(fixtures[50], selected_original_model_feasible=1))),
        (51, wire(dict(fixtures[51], effect_call_count=0.0))),
        (52, wire(dict(fixtures[52], quantum_advantage_claim_allowed=True))),
        (34, wire(dict(fee, amount_before_rounding="0.02"))),
        (34, wire(dict(fee, amount_after_rounding="0.01"))),
        (34, wire(dict(fee, quantization_receipt=dict(receipt, residual="0.1")))),
        (34, wire(dict(fee, quantization_receipt=dict(receipt, scale=True)))),
        (34, wire(dict(fee, quantization_receipt=dict(receipt, rounding="ROUND_DOWN")))),
        (34, wire(rebate)), (35, wire(fee)),
        (34, wire(dict(fee, quantization_receipt=dict(receipt, unknown=True)))),
        (45, b'{"lcb_net":"1","lcb_net":"2","trade_gate":true}'),
        (45, b'{ "lcb_net":"1","trade_gate":true}'),
    )
    for number, raw in negative:
        with pytest.raises(ComputationControlPlaneError):
            decode(f"MATH-{number:02d}", raw, maximum_bytes=2048, maximum_nodes=128)

    # Oversize/wrong-native input and excessive depth reject before JSON loads.
    with patch.object(serialization.json, "loads", side_effect=AssertionError("JSON decoding reached")):
        for raw, byte_limit, node_limit in ((b'"1234"', 5, 8), (Decimal("1" * 100001), 64, 8),
                                           (b'"1"', 64, 0), (b'[' * 17 + b'0' + b']' * 17, 64, 128)):
            with pytest.raises(ComputationControlPlaneError):
                decode("MATH-26", raw, maximum_bytes=byte_limit, maximum_nodes=node_limit)
    # JSON node admission precedes all typed financial reconstruction.
    with patch.object(specification, "Decimal", side_effect=AssertionError("Decimal reconstruction reached")):
        with pytest.raises(ComputationControlPlaneError, match="JSON_NODES"):
            decode("MATH-27", wire(fixtures[27]), maximum_bytes=128, maximum_nodes=2)
    with pytest.raises(ComputationControlPlaneError, match="LP03_PRIVATE_RAW_SCHEMA_UNAVAILABLE"):
        decode("MATH-46", b'"1"', maximum_bytes=64, maximum_nodes=8)


def _assert_lp03_private_input_contracts() -> None:
    from dataclasses import FrozenInstanceError
    from inspect import signature
    from types import MappingProxyType
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.bindings import (
        EVIDENCE_PRIVATE_INPUT_CONTRACTS_V1, CURRENT_FORMULA_INPUT_AUTHORITY_BY_MATH_ID,
    )
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.implementation_registry import (
        TRANCHE_C_IMPLEMENTATION_REGISTRY, get_st12f_evidence_math_callable_v1,
    )
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.quantum_benchmark import QuantumBenchmarkServiceV1

    # Independently enumerated from the frozen source-input table. This tests
    # contract metadata; matching metadata does not establish producer custody.
    expected = {
        26: ("current_action_values", "new_information_scenarios", "acquisition_cost"),
        27: ("win_probability", "net_odds"),
        28: ("full_kelly_fraction", "fraction_multiplier", "risk_caps"),
        29: ("weights", "expected_returns", "covariance", "risk_aversion", "transaction_cost"),
        30: ("losses", "alpha"), 31: ("losses", "alpha"),
        32: ("side", "quantity", "execution_price", "decision_price", "explicit_fees", "opportunity_cost_unfilled", "other_declared_costs"),
        33: ("side", "quantity", "execution_price", "midpoint_at_decision"),
        34: ("contracts", "fee_rate", "price", "schedule_binding", "quantization_policy", "receipt_id"),
        35: ("contracts", "theta", "price", "liquidity_role", "schedule_binding", "quantization_policy", "receipt_id"),
        37: ("artifact", "feature_schema_ref", "scope_ref", "horizon_seconds"), 38: ("artifact",),
        40: ("signed_fill_quantity", "midpoint_after_fill", "fill_price"),
        41: ("edge_now", "latency", "tau"), 42: ("Y", "sigma", "Q", "ADV"),
        43: ("participation", "approved_participation_cap", "penalty_scale"),
        44: ("sample_covariance", "target", "delta"),
        45: ("estimated_net_edge", "uncertainty", "z_or_quantile", "model_risk_haircut"),
        50: ("trace",), 51: ("trace",),
        52: ("comparison_id", "quantum_receipt", "strongest_classical_receipt", "no_trade_receipt"),
    }
    contracts = EVIDENCE_PRIVATE_INPUT_CONTRACTS_V1
    assert type(contracts) is MappingProxyType and len(contracts) == 21
    assert tuple(contracts) == tuple(f"MATH-{number:02d}" for number in expected)
    public_bindings = {binding.binding_id for rows in CURRENT_FORMULA_INPUT_AUTHORITY_BY_MATH_ID.values() for binding in rows}
    seen = set()
    for number, names in expected.items():
        math_id = f"MATH-{number:02d}"
        contract = contracts[math_id]
        assert contract.math_id == math_id and contract.schema_id == f"LP03::{math_id}::INPUT_V1"
        assert tuple(binding.input_name for binding in contract.bindings) == names
        if number < 40:
            function = TRANCHE_C_IMPLEMENTATION_REGISTRY[math_id].callable
            assert contract.callable_ref == "economic_math.py::" + function.__name__
        elif number < 50:
            function = get_st12f_evidence_math_callable_v1(math_id)
            assert contract.callable_ref == "implementation_registry.py::" + function.__name__
        else:
            method = {50: "_validate_qaoa_trace_with_raw_v1", 51: "_validate_vqe_trace_with_raw_v1", 52: "_compare_same_lock_with_raw_v1"}[number]
            function = getattr(QuantumBenchmarkServiceV1, method)
            assert contract.callable_ref == "quantum_benchmark.py::QuantumBenchmarkServiceV1::" + method
        assert tuple(name for name in signature(function).parameters if name != "self") == names
        assert contract.required_original_producer_joins
        for binding in contract.bindings:
            assert binding.binding_id == f"LP03_FIVAB::{binding.input_name}::{math_id}"
            assert binding.exact_field_path == f"values['{binding.input_name}']"
            assert binding.native_input_type and binding.producer_role and binding.unit_or_basis_requirement
            assert binding.binding_id not in public_bindings | seen
            seen.add(binding.binding_id)
            with pytest.raises(FrozenInstanceError):
                binding.producer_role = "CALLER_ASSERTED_OWNER"
    assert contracts["MATH-28"].required_original_producer_joins[0] == "ORIGINAL_MATH27_RAW_RESULT_AND_INPUT_PROVENANCE"
    assert contracts["MATH-32"].required_original_producer_joins[1] == "ORIGINAL_TCA_NO_DOUBLE_COUNT_ATTRIBUTION"
    assert contracts["MATH-34"].required_original_producer_joins[-1] == "EXCLUDED_GLOBAL_VENUE_REMAINS_BLOCKED"
    for math_id in ("MATH-34", "MATH-35"):
        fields = {binding.input_name: binding for binding in contracts[math_id].bindings}
        assert fields["price"].unit_or_basis_requirement == "SOURCE_SUPPORTED_UNIT_PAYOUT_PRICE_IN_ZERO_ONE"
        assert fields["receipt_id"].unit_or_basis_requirement == "PREALLOCATED_ORIGINAL_INVOCATION_RECEIPT_ID"
        assert "ORIGINAL_PAYOUT_SCHEDULE_ASSOCIATION_NO_IMPLICIT_NORMALIZATION" in contracts[math_id].required_original_producer_joins
    assert contracts["MATH-52"].bindings[0].unit_or_basis_requirement == "PREALLOCATED_ORIGINAL_INVOCATION_COMPARISON_ID"
    assert contracts["MATH-37"].bindings[0].native_input_type == "FillProbabilityModelArtifactV1"
    assert contracts["MATH-38"].bindings[0].native_input_type == "FillQuantityDistributionArtifactV1"
    assert contracts["MATH-41"].bindings[1].unit_or_basis_requirement == "SAME_DURATION_UNIT_AS_FITTED_TAU"
    assert contracts["MATH-52"].required_original_producer_joins[-1] == "EXACT_ELEVEN_DIMENSION_COMPARISON_BASIS"
    with pytest.raises(TypeError):
        contracts["MATH-46"] = contracts["MATH-50"]


def _assert_lp03_existing_public_invocation_profiles() -> None:
    import sys
    from types import CodeType, MappingProxyType
    from unittest.mock import patch
    from dataclasses import replace
    from decimal import Inexact, ROUND_DOWN, localcontext
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import ContractValidationError
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.implementation_registry import (
        CURRENT_IMPLEMENTATION_REGISTRY, resolve_evidence_invocation_v1, invoke_evidence_formula_v1, invoke_evidence_public_wire_v1,
    )
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane import implementation_registry as owner
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.input_resolver import decode_evidence_public_invocation_inputs_v1
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import ComputationControlPlaneError
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.models import EvidenceOriginV1
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.validation import _canonical_vector_equal

    # Original independently owned vectors remain the expected-result source.
    # This is pure adapter coverage, not source/grant/attempt admission.
    selected = (*tuple(f"MATH-{number:02d}" for number in range(1, 26)), "MATH-36", "MATH-39")
    assert len(selected) == 27 and len(CURRENT_IMPLEMENTATION_REGISTRY) == 31
    observed, normalizations = [], []
    dispatch_code = owner.invoke_current_formula.__code__
    normalize_code = next(item for item in invoke_evidence_public_wire_v1.__code__.co_consts
                          if type(item) is CodeType and item.co_name == "normalize")
    def observe(frame, event, arg):
        if event == "return" and frame.f_code is dispatch_code:
            observed.append(arg)
        if event == "call" and frame.f_code is normalize_code and frame.f_globals is owner.__dict__:
            normalizations.append(frame.f_code)
    def wire_call(contract, data, *, input_bytes=32768, input_nodes=4096, output_bytes=32768, output_nodes=4096):
        previous_profile = sys.getprofile()
        try:
            sys.setprofile(observe)
            return invoke_evidence_public_wire_v1(contract, data, maximum_input_bytes=input_bytes, maximum_nodes=input_nodes,
                maximum_output_bytes=output_bytes, maximum_output_nodes=output_nodes)
        finally:
            sys.setprofile(previous_profile)
    for math_id in selected:
        original = CURRENT_IMPLEMENTATION_REGISTRY[math_id]
        contract = resolve_evidence_invocation_v1(math_id, implementation_pin=original.contract.implementation_id,
            specification_pin=original.contract.specification_version, resource_policy_ref="LP03-TEST::ADAPTER-RESOURCES",
            origin=EvidenceOriginV1.SOFTWARE_CONFORMANCE)
        assert contract.math_id == math_id and contract.raw_implementation_id == original.contract.implementation_id
        assert contract.evidence_projection_version == "1.5"
        if math_id != "MATH-39":
            assert contract.actual_adapter_ref == "implementation_registry.py::invoke_formula_v34"
            assert contract.raw_contract_version == "3.4" and contract.raw_output_schema_ref == f"{math_id}::OUTPUT"
            assert contract.owner_bindings
            for vector in ST12B_VECTORS_BY_MATH_ID[math_id]:
                if vector.case_type == "NEGATIVE":
                    with pytest.raises(ValueError):
                        invoke_evidence_formula_v1(contract, vector.inputs)
                else:
                    actual = invoke_evidence_formula_v1(contract, vector.inputs)
                    assert _canonical_vector_equal(actual, vector.expected), (math_id, vector.vector_id)
                    original_wire = deterministic_json(vector.inputs).encode("utf-8")
                    before = len(observed)
                    result = wire_call(contract, original_wire)
                    assert len(observed) == before + 1 and result.raw_result is observed[-1]
                    assert result.input_json is original_wire and type(result.decoded_inputs) is MappingProxyType
                    assert result.actual_callable is owner._V34_INVOCATION_ADAPTERS[math_id]
                    assert result.actual_adapter is owner.invoke_current_formula and result.constructor_receipt_or_none is None
                    assert result.invocation_input_schema_ref == contract.input_schema_ref
                    assert _canonical_vector_equal(result.raw_result, vector.expected), (math_id, vector.vector_id)
                    assert _canonical_vector_equal(result.decoded_output, vector.expected), (math_id, vector.vector_id)
                    assert result.output_json == deterministic_json(result.raw_result).encode("utf-8")
                    with localcontext() as hostile:
                        hostile.prec = 2
                        hostile.rounding = ROUND_DOWN
                        hostile.traps[Inexact] = True
                        assert _canonical_vector_equal(invoke_evidence_formula_v1(contract, vector.inputs), vector.expected)
                        hostile.capitals = 0
                        assert wire_call(contract, original_wire).output_json == result.output_json
            if math_id == "MATH-36":
                assert contract.raw_implementation_id == "MATH-36::2.0.0"
                assert contract.callable_ref == "implementation_registry.py::compute_math_36_kalshi_binary_book_transform"
        else:
            assert contract.actual_adapter_ref == "implementation_registry.py::invoke_current_formula"
            assert contract.input_schema_ref == "ST12D_MATH39_INPUT_V1" and contract.raw_contract_version == "ST12D_OUTPUT_V1"
            assert contract.owner_bindings == ("FIVAB::sequenced_book_events::MATH-39", "FIVAB::order_ack::MATH-39")
            values = dict(displayed_quantity_before_order="5", net_prior_additions="2",
                          observed_prior_cancellations="1", observed_trades_ahead="3")
            assert invoke_evidence_formula_v1(contract, values) == Decimal("3")
            result = wire_call(contract, deterministic_json(values).encode("utf-8"))
            assert result.raw_result is observed[-1] and result.output_json == b'"3"' and result.decoded_output == Decimal("3")
            assert result.invocation_input_schema_ref == "LP03::MATH-39::DERIVED_INVOCATION_INPUT_V1"
            assert tuple(result.decoded_inputs) == tuple(values) and result.actual_callable is original.callable
            precise = dict(displayed_quantity_before_order="10000000000000000000000000000000010",
                net_prior_additions="0", observed_prior_cancellations="10000000000000000000000000000000006",
                observed_trades_ahead="0")
            precise_result = wire_call(contract, deterministic_json(precise).encode("utf-8"))
            assert precise_result.decoded_inputs["observed_prior_cancellations"] == Decimal(precise["observed_prior_cancellations"])
            assert precise_result.raw_result is observed[-1] and precise_result.output_json == b'"4"'
            with pytest.raises(ComputationControlPlaneError, match="LP03_PUBLIC_INVOCATION_INPUT_FIELDS"):
                wire_call(contract, b'{"order_ack":{},"sequenced_book_events":[]}')
            with pytest.raises(ContractValidationError):
                invoke_evidence_formula_v1(contract, dict(reversed(tuple(values.items()))))
        with pytest.raises(ContractValidationError, match="PRIVATE_INVOCATION_CONTRACT_CHANGED"):
            invoke_evidence_formula_v1(replace(contract, raw_output_schema_ref="LP03-TEST::WRONG-SCHEMA"), {})
    for excluded in ("MATH-46", "MATH-47", "MATH-48", "MATH-49", "MATH-53"):
        with pytest.raises(ContractValidationError, match="PRIVATE_INVOCATION_NOT_IMPLEMENTED"):
            resolve_evidence_invocation_v1(excluded, implementation_pin="NOT-ADMITTED", specification_pin="NOT-ADMITTED",
                resource_policy_ref="LP03-TEST::ADAPTER-RESOURCES", origin=EvidenceOriginV1.SOFTWARE_CONFORMANCE)

    original = CURRENT_IMPLEMENTATION_REGISTRY["MATH-03"]
    contract = resolve_evidence_invocation_v1("MATH-03", implementation_pin=original.contract.implementation_id,
        specification_pin=original.contract.specification_version, resource_policy_ref="LP03-TEST::WIRE-RESOURCES",
        origin=EvidenceOriginV1.SOFTWARE_CONFORMANCE)
    payload = dict(best_bid="0.40", best_ask="0.60", payout="1", same_instrument_snapshot=True, snapshot_state="CURRENT_CONTIGUOUS_BOOK")
    data = deterministic_json(payload).encode("utf-8")
    count = len(observed)
    for invalid in (data + b' ', b'{"best_bid":"0.4","best_bid":"0.4"}', data.replace(b'"1"', b'NaN'),
                    deterministic_json(dict(payload, extra=True)).encode("utf-8"), data.replace(b'"0.40"', b'"\xff"')):
        with pytest.raises(ComputationControlPlaneError):
            wire_call(contract, invalid)
    for limits in (dict(input_bytes=len(data)-1), dict(input_nodes=10), dict(output_bytes=0), dict(output_nodes=True)):
        with pytest.raises(ComputationControlPlaneError):
            wire_call(contract, data, **limits)
    assert len(observed) == count
    normalizations.clear()
    with pytest.raises(ComputationControlPlaneError, match="LP03_NATIVE_DECIMAL_ALLOCATION_BOUND"):
        wire_call(contract, data, output_bytes=200)
    assert len(observed) == count + 1 and normalizations == []
    assert wire_call(contract, data, input_bytes=len(data), input_nodes=11, output_nodes=1).output_json == b'"0.50"'
    assert normalizations and len(observed) == count + 2
    def replacement(*args, **kwargs):
        raise AssertionError("replaced public callable executed")
    for name in ("invoke_current_formula", "invoke_formula_v34", "_v34_mutable_call_value",
                 "compute_math_03_v34", "compute_math_03_orderbook_midpoint"):
        with patch.object(owner, name, replacement):
            with pytest.raises(ComputationControlPlaneError, match="LP03_PUBLIC_ORIGINAL_CALLABLE_CHANGED"):
                wire_call(contract, data)
    with patch.object(owner, "_V34_INVOCATION_ADAPTERS", MappingProxyType(dict(owner._V34_INVOCATION_ADAPTERS))):
        with pytest.raises(ComputationControlPlaneError, match="LP03_PUBLIC_ORIGINAL_CALLABLE_CHANGED"):
            wire_call(contract, data)
    assert len(observed) == count + 2
    # The decoder preserves wire scalar distinctions; the original mathematical
    # adapter, not a new coercion policy here, decides the permitted domains.
    for value in (False, 0, 0.0, "0.00", None):
        decoded = decode_evidence_public_invocation_inputs_v1("MATH-03", deterministic_json(dict(payload, best_bid=value)).encode("utf-8"),
            maximum_bytes=32768, maximum_nodes=4096)
        assert type(decoded["best_bid"]) is type(value) and decoded["best_bid"] == value
    with pytest.raises(ComputationControlPlaneError, match="LP03_PUBLIC_INVOCATION_INPUT_SCHEMA_UNAVAILABLE"):
        decode_evidence_public_invocation_inputs_v1("MATH-50", b'{}', maximum_bytes=32, maximum_nodes=8)


def test_thirty_oracles_ninety_vectors_and_properties_execute() -> None:
    vector_report = validate_all_st12b_vectors()
    property_report = validate_st12b_property_mutations()

    assert len(ORACLE_BY_MATH_ID) == 30
    assert len(GOLDEN_VECTOR_BY_MATH_ID) == 30
    assert len(ST12B_VECTOR_PACK) == 90
    assert len(ST12B_VECTORS_BY_MATH_ID) == 30
    assert all(len(rows) == 3 for rows in ST12B_VECTORS_BY_MATH_ID.values())
    assert len(ST12B_PROPERTY_TESTS) == 30
    assert vector_report.passed and len(vector_report.checks) == 90
    assert property_report.passed and len(property_report.checks) == 30


def test_nonstack_components_remain_individually_callable() -> None:
    nonstack_ids = tuple(
        math_id
        for math_id in IMPLEMENTATION_REGISTRY
        if math_id not in {"MATH-01", "MATH-02"}
    )

    assert len(nonstack_ids) == 28
    for math_id in nonstack_ids:
        inputs = json.loads(GOLDEN_VECTOR_BY_MATH_ID[math_id].inputs_json)
        assert invoke_formula_v34(math_id, inputs) is not None


def test_decimal_arithmetic_stays_exact_until_json_boundary() -> None:
    result = invoke_formula_v34(
        "MATH-01",
        {
            "contract_price": "0.47",
            "payout_per_winning_contract": "1.00",
        },
    )

    assert result == Decimal("0.47")
    assert isinstance(result, Decimal)
    assert deterministic_json({"implied_probability": result}) == (
        '{"implied_probability":"0.47"}'
    )
    with pytest.raises(NumericDomainError):
        invoke_formula_v34(
            "MATH-01",
            {
                "contract_price": 0.47,
                "payout_per_winning_contract": "1.00",
            },
        )
    _assert_lp03_certified_numerical_boundaries()
    _assert_lp03_math26_decimal_admission()
    _assert_lp03_math26_ordered_context_proof()
    _assert_lp03_math26_declared_bounds()
    _assert_lp03_market_ordered_context_proof()
    _assert_lp03_binary_cashflow_ordered_proof()
    _assert_lp03_multi_outcome_cashflow_ordered_proof()
    _assert_lp03_cashflow_preregistered_enclosure()
    _assert_lp03_cashflow_source_frame_data()
    _assert_lp03_kelly_ordered_context_proof()
    _assert_lp03_log_loss_enclosure_proof()
    _assert_lp03_calibration_ordered_proof()
    _assert_lp03_multiple_testing_ordered_proof()
    _assert_lp03_wilson_ordered_model_proof()
    _assert_lp03_probabilistic_sharpe_ordered_model_proof()
    _assert_lp03_deflated_sharpe_ordered_model_proof()
    _assert_lp03_sharpe_projection_bounds()
    _assert_lp03_fold_topology_original_rosters()
    _assert_lp03_pbo_ordered_model_proof()
    _assert_lp03_bootstrap_ordered_model_proof()
    _assert_lp03_bootstrap_signed_mt_data()
    _assert_lp03_reality_check_ordered_model_proof()
    _assert_lp03_spa_ordered_model_proof()
    _assert_lp03_probability_edge_model_proof()
    _assert_lp03_original_probability_edge_chain()
    _assert_lp03_measured_probability_edge_chain()
    _assert_lp03_uniform_coordinate_recipe()
    _assert_lp03_recorded_dr_uncertainty()


def _assert_lp03_original_probability_edge_chain():
    """Pure original-call joins, not source/calibration/native authority."""
    import copy
    import json
    import pickle
    import struct
    import sys
    from dataclasses import replace
    from datetime import UTC, datetime, timedelta
    from decimal import Inexact, ROUND_DOWN, localcontext
    from unittest.mock import patch
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane import implementation_registry as owner
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane import unit_conversion as conversion_owner
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.models import (
        ComputationExecutionContextV1, ComputationScopeV1, ImplementationVersionPinV1, EvidenceOriginV1)
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import ComputationControlPlaneError
    chain_type = owner._EvidenceProbabilityEdgeChainV1
    contracts = tuple(owner.resolve_evidence_invocation_v1(math_id,
        implementation_pin=owner.CURRENT_IMPLEMENTATION_REGISTRY[math_id].contract.implementation_id,
        specification_pin=owner.CURRENT_IMPLEMENTATION_REGISTRY[math_id].contract.specification_version,
        resource_policy_ref="CHAIN-P", origin=EvidenceOriginV1.SOFTWARE_CONFORMANCE) for math_id in ("MATH-01", "MATH-02"))
    moment = datetime(2026, 1, 1, tzinfo=UTC)
    context = ComputationExecutionContextV1(context_id="CHAIN-C", as_of=moment, observed_at=moment,
        source_epoch_id="CHAIN-E", input_version="1", maximum_age=timedelta(seconds=60),
        scope=ComputationScopeV1("CHAIN-M", "CHAIN-V", "CHAIN-EV", "CHAIN-I", "CHAIN-MODE", "CHAIN-S"),
        binding_profile_version="3.4", parameter_policy_version="CHAIN-P",
        dependency_graph_id="STACK::MATH-01::MATH-02::V3_4", dependency_graph_version="3.4",
        implementation_versions=tuple(ImplementationVersionPinV1(row.math_id, row.raw_implementation_id) for row in contracts))
    def wire(value):
        return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode("utf-8")
    def bits(value):
        return struct.pack(">d", value).hex()
    def arguments(price="0.25", payout="1", model=.75, **changes):
        base = dict(contracts=contracts, market_input_json=wire(dict(contract_price=price, payout_per_winning_contract=payout)),
            model_input_json=wire(dict(calibrated_model_probability=model, calibration_state="CALIBRATED_FOR_DECLARED_CONTEXT")),
            context=context, conversion_receipt_id="CHAIN-CONVERSION", maximum_input_bytes=65536,
            maximum_nodes=4096, maximum_output_bytes=65536)
        return dict(base, **changes)
    calls, returns = [], []
    observed_codes = {owner.compute_math_01_v34.__code__: "MATH-01", owner.compute_math_02_v34.__code__: "MATH-02",
                      conversion_owner.UnitConversionOwnerV1.convert.__code__: "CONVERSION"}
    def observe(frame, event, arg):
        label = observed_codes.get(frame.f_code)
        if label is not None:
            if event == "call":
                calls.append(label)
            elif event == "return":
                returns.append((label, arg))
    def run(operation, profiler=observe):
        previous = sys.getprofile()
        try:
            sys.setprofile(profiler)
            return chain_type.run_v1(operation)
        finally:
            sys.setprofile(previous)
    def construct(**kwargs):
        previous = sys.getprofile()
        try:
            sys.setprofile(observe)
            return chain_type(**kwargs)
        finally:
            sys.setprofile(previous)
    cases = (
        ("positive", "0.25", "1", .75, "0.25", "3fd0000000000000", "3fe0000000000000"),
        ("negative", "0.75", "1", .25, "0.75", "3fe8000000000000", "bfe0000000000000"),
        ("nonunit_payout", "0.50", "2", .75, "0.25", "3fd0000000000000", "3fe0000000000000"),
        ("decimal_rounded_then_binary64", "1", "3", .5, "0.3333333333333333333333333333333333", "3fd5555555555555", "3fc5555555555556"),
        ("negative_model_zero", "0", "1", -0.0, "0", "0000000000000000", "8000000000000000"),
        ("negative_market_zero", "-0", "1", 0.0, "-0", "8000000000000000", "0000000000000000"),
        ("both_negative_zero", "-0", "1", -0.0, "-0", "8000000000000000", "0000000000000000"),
        ("subnormal_conversion", "5E-324", "1", 0.0, "5E-324", "0000000000000001", "8000000000000001"),
    )
    positives = []
    for name, price, payout, model, expected_decimal, converted_bits, edge_bits in cases:
        operation = construct(**arguments(price, payout, model))
        start_calls, start_returns = len(calls), len(returns)
        with localcontext() as hostile:
            hostile.prec, hostile.rounding, hostile.traps[Inexact] = 2, ROUND_DOWN, True
            assert run(operation) is operation
        state = operation.inspect_v1()
        assert state["phase"] == "COMPLETED" and state["failure_phase"] is None
        assert calls[start_calls:] == ["MATH-01", "CONVERSION", "MATH-02"]
        original_returns = returns[start_returns:]
        assert [label for label, _value in original_returns] == ["MATH-01", "CONVERSION", "MATH-02"]
        producer, conversion, consumer = state["producer"], state["conversion"], state["consumer"]
        assert producer.raw_result is original_returns[0][1] and conversion is original_returns[1][1]
        assert consumer.raw_result is original_returns[2][1]
        assert conversion[1].source_value is producer.raw_result and conversion[1].converted_value is conversion[0]
        assert conversion[1].execution_context is context and conversion[1].no_authority_flag is True
        assert state["derived_inputs"]["market_implied_probability"] is conversion[0]
        assert str(producer.raw_result) == expected_decimal and bits(conversion[0]) == converted_bits
        assert bits(consumer.decoded_inputs["market_implied_probability"]) == converted_bits
        assert bits(consumer.raw_result) == bits(consumer.decoded_output) == edge_bits
        assert state["consumer_input"] is consumer.input_json and producer.input_json is operation.original[1]
        assert state["conversion_json"] == deterministic_json(conversion[1]).encode("utf-8")
        assert producer.actual_adapter is consumer.actual_adapter is owner.invoke_current_formula
        assert producer.actual_callable is owner._V34_INVOCATION_ADAPTERS["MATH-01"]
        assert consumer.actual_callable is owner._V34_INVOCATION_ADAPTERS["MATH-02"]
        fragment_bytes = (len(producer.output_json), len(state["conversion_json"]), len(state["consumer_input"]),
                          len(consumer.output_json), len(state["artifact_json"]))
        assert state["serialized_bytes"] == sum(fragment_bytes) <= 65536
        before = len(calls)
        with pytest.raises(ComputationControlPlaneError, match="LP03_EDGE_CHAIN_ALREADY_STARTED_OR_UNRESOLVED"):
            run(operation)
        assert len(calls) == before and operation.inspect_v1()["artifact_json"] is state["artifact_json"]
        positives.append(dict(case=name, producer_input_json=producer.input_json.decode(), producer_output_json=producer.output_json.decode(),
            model_input_json=operation.original[2].decode(), converted_bits=converted_bits, edge_bits=edge_bits,
            consumer_input_json=consumer.input_json.decode(), consumer_output_json=consumer.output_json.decode(),
            conversion_receipt_json=state["conversion_json"].decode(), artifact_json=state["artifact_json"].decode(),
            fragment_bytes=fragment_bytes, serialized_bytes=state["serialized_bytes"], calls=calls[start_calls:]))
    original_operation = operation
    denials = []
    constructor_cases = (
        ("reversed_contracts", dict(contracts=tuple(reversed(contracts)))),
        ("wrong_contract", dict(contracts=(replace(contracts[0], raw_output_schema_ref="WRONG"), contracts[1]))),
        ("different_policy", dict(contracts=(contracts[0], replace(contracts[1], resource_policy_ref="OTHER")))),
        ("context_missing_component", dict(context=replace(context, implementation_versions=context.implementation_versions[:1]))),
        ("absent_stack_graph", dict(context=replace(context, dependency_graph_id=None, dependency_graph_version=None))),
        ("wrong_stack_graph", dict(context=replace(context, dependency_graph_id="OTHER-STACK"))),
        ("wrong_stack_version", dict(context=replace(context, dependency_graph_version="OTHER-VERSION"))),
        ("model_bool", dict(model_input_json=wire(dict(calibrated_model_probability=True, calibration_state="CALIBRATED_FOR_DECLARED_CONTEXT")))) ,
        ("model_text", dict(model_input_json=wire(dict(calibrated_model_probability="0.75", calibration_state="CALIBRATED_FOR_DECLARED_CONTEXT")))) ,
        ("model_outside", dict(model_input_json=wire(dict(calibrated_model_probability=1.1, calibration_state="CALIBRATED_FOR_DECLARED_CONTEXT")))) ,
        ("uncalibrated_data", dict(model_input_json=wire(dict(calibrated_model_probability=.75, calibration_state="UNCALIBRATED")))) ,
        ("invented_market_input", dict(model_input_json=wire(dict(calibrated_model_probability=.75, calibration_state="CALIBRATED_FOR_DECLARED_CONTEXT", market_implied_probability=.25)))) ,
        ("model_noncanonical", dict(model_input_json=arguments()["model_input_json"] + b" ")),
        ("market_noncanonical", dict(market_input_json=arguments()["market_input_json"] + b" ")),
        ("zero_output_allowance", dict(maximum_output_bytes=0)),
        ("boolean_node_allowance", dict(maximum_nodes=True)),
        ("zero_input_allowance", dict(maximum_input_bytes=0)),
        ("tiny_input_allowance", dict(maximum_input_bytes=100)),
        ("tiny_context_node_allowance", dict(maximum_nodes=12)),
        ("oversized_receipt_id", dict(conversion_receipt_id="X" * 257)),
    )
    for name, changes in constructor_cases:
        before = len(calls)
        with pytest.raises(ComputationControlPlaneError):
            construct(**arguments(**changes))
        assert len(calls) == before
        denials.append(dict(case=name, stage="CONSTRUCTOR", original_calls=0))
    for name, kwargs, expected_calls, expected_stage, statuses in (
        ("invalid_original_payout", arguments(payout="0"), ["MATH-01"], "MATH01_RUNNING", ("NOT_RETURNED", "NOT_RETURNED", "NOT_RETURNED")),
        ("producer_wire_output_exhaustion", arguments(maximum_output_bytes=16), ["MATH-01"], "MATH01_RUNNING", ("NOT_RETURNED", "NOT_RETURNED", "NOT_RETURNED")),
        ("conversion_receipt_exhaustion", arguments(maximum_output_bytes=512), ["MATH-01", "CONVERSION"], "CONVERSION_RETURNED", ("WITNESSED", "WITNESSED", "NOT_RETURNED")),
        ("complete_artifact_exhaustion", arguments(maximum_output_bytes=2048), ["MATH-01", "CONVERSION", "MATH-02"], "MATH02_RETURNED", ("WITNESSED", "WITNESSED", "WITNESSED")),
    ):
        operation = construct(**kwargs)
        before = len(calls)
        with pytest.raises(ComputationControlPlaneError):
            run(operation)
        state = operation.inspect_v1()
        assert calls[before:] == expected_calls and state["phase"] == "FAILED" and state["failure_phase"] == expected_stage
        assert tuple(state[name + "_status"] for name in ("producer", "conversion", "consumer")) == statuses
        count = len(calls)
        with pytest.raises(ComputationControlPlaneError, match="LP03_EDGE_CHAIN_ALREADY_STARTED_OR_UNRESOLVED"):
            run(operation)
        assert len(calls) == count and operation.inspect_v1()["serialized_bytes"] == state["serialized_bytes"]
        denials.append(dict(case=name, stage=state["failure_phase"], statuses=statuses, original_calls=calls[before:],
            serialized_bytes=state["serialized_bytes"], retained_producer=state["producer"] is not None,
            retained_conversion=state["conversion"] is not None, retained_consumer=state["consumer"] is not None))
    for failed_name in ("producer", "consumer"):
        operation = construct(**arguments())
        def allocation_failure(frame, event, arg):
            observe(frame, event, arg)
            if event == "call" and frame.f_code.co_name == "witness_result" and frame.f_locals.get("name") == failed_name:
                raise MemoryError("synthetic witness allocation failure")
        with pytest.raises(MemoryError, match="synthetic witness allocation failure"):
            run(operation, allocation_failure)
        state = operation.inspect_v1()
        assert state["phase"] == "FAILED" and state[failed_name] is not None
        assert state[failed_name + "_status"] == "RETURNED_UNWITNESSED"
        with pytest.raises(ComputationControlPlaneError, match="LP03_EDGE_CHAIN_ALREADY_STARTED_OR_UNRESOLVED"):
            run(operation)
        denials.append(dict(case=failed_name + "_witness_allocation", stage=state["failure_phase"], retained_return=True,
                            status=state[failed_name + "_status"], serialized_bytes=state["serialized_bytes"]))
    def forbidden(*args, **kwargs):
        raise AssertionError("substituted original owner must not run")
    for label, module, name in (("wire_owner", owner, "invoke_evidence_public_wire_v1"),
                              ("converter_function", conversion_owner, "_decimal_probability_to_float64"),
                              ("converter_method", conversion_owner.UnitConversionOwnerV1, "convert")):
        operation = construct(**arguments())
        with patch.object(module, name, forbidden):
            with pytest.raises(ComputationControlPlaneError, match="LP03_EDGE_CHAIN_ORIGINAL_OWNER_CHANGED"):
                run(operation)
        assert operation.phase == "PREPARED"
        denials.append(dict(case=label, stage="PRE_ENTRY", original_calls=0))
    for method in (copy.copy, copy.deepcopy, pickle.dumps):
        with pytest.raises(TypeError):
            method(original_operation)
        denials.append(dict(case=method.__name__, stage="COPY", original_calls=0))
    for field, value in (("phase", "PREPARED"), ("guard", forbidden), ("producer", None)):
        with pytest.raises(AttributeError):
            setattr(original_operation, field, value)
        denials.append(dict(case="replace_" + field, stage="READ_ONLY_STATE", original_calls=0))
    with pytest.raises(ComputationControlPlaneError, match="LP03_EDGE_CHAIN_ALREADY_INITIALIZED"):
        chain_type.__init__(original_operation, **arguments())
    with pytest.raises(ComputationControlPlaneError, match="LP03_EDGE_CHAIN_ORIGINAL_OPERATION_REQUIRED"):
        run(object.__new__(chain_type))
    denials.extend((dict(case="reinitialize", stage="CONSTRUCTOR", original_calls=0),
                   dict(case="unissued_object", stage="PRE_ENTRY", original_calls=0)))
    descriptor = original_operation.conversion[1].target
    original_basis = descriptor.basis
    try:
        object.__setattr__(descriptor, "basis", "UNRELATED_BASIS")
        with pytest.raises(ComputationControlPlaneError, match="LP03_EDGE_CHAIN_ORIGINAL_DESCRIPTOR_CHANGED"):
            original_operation.inspect_v1()
    finally:
        object.__setattr__(descriptor, "basis", original_basis)
    denials.append(dict(case="descriptor_basis_mutation", stage="RETAINED_INSPECTION", original_calls=0))
    print("LP03_EDGE_CHAIN_QUALIFICATION=" + json.dumps(dict(profile="PURE_REGISTERED_STACK_NO_SOURCE_AUTHORITY",
        positives=positives, denials=denials, total_positive_cases=len(positives), total_denials=len(denials),
        source_calibration_and_native_runtime="UNQUALIFIED"), sort_keys=True, separators=(",", ":")))
    _assert_lp03_probability_conversion_review(positives)


def _assert_lp03_probability_conversion_review(original_rows):
    """Bound the missing conversion proof; retain original and data-only cases."""
    import copy
    import json
    from contextlib import ExitStack
    from unittest.mock import patch
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane import parameter_policy as policy
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane import implementation_registry as formulas
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane import unit_conversion as converter
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane import serialization
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.evidence import IndependentEvidenceReviewV1
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import ComputationControlPlaneError
    limits = dict(max_input_bits=4096, max_work_bits=65536, max_serialized_bytes=65536)
    wire = lambda value: json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()
    base = original_rows[0]
    def fresh(**changes):
        return policy._EvidenceNumericalWorkV1(dict(limits, **changes), retained_input_capacity=64)
    def market(row, work, *, math_id="MATH-01"):
        source = json.loads(row["producer_input_json"])
        raw_text = json.loads(row["producer_output_json"])
        return policy._bounded_evidence_market_review_v1(math_id,
            tuple((name, source[name]) for name in ("contract_price", "payout_per_winning_contract")),
            lower_text="0", upper_text="1", raw_texts=(raw_text,), expected_texts=(raw_text,), projected_text=raw_text, work=work)
    def convert(row, proof, work, **changes):
        args = dict(producer_input_json=row["producer_input_json"].encode(), producer_raw_json=row["producer_output_json"].encode(),
            conversion_receipt_json=row["conversion_receipt_json"].encode(), consumer_input_json=row["consumer_input_json"].encode())
        return policy._bounded_evidence_probability_conversion_review_v1(proof, **dict(args, **changes), work=work)
    def edge(row, work):
        raw = row["consumer_output_json"].encode()
        return IndependentEvidenceReviewV1._bounded_review_probability_edge_v1(row["consumer_input_json"].encode(),
            raw, raw, json.loads(raw), work=work)
    def changed_receipt(row, **changes):
        return wire(dict(json.loads(row["conversion_receipt_json"]), **changes))
    def changed_consumer(row, **changes):
        return wire(dict(json.loads(row["consumer_input_json"]), **changes))
    def forbidden(*args, **kwargs):
        raise AssertionError("independent conversion review invoked a production formula or converter")
    positives, denials = [], []
    with ExitStack() as blocked:
        for name in ("compute_math_01_v34", "compute_math_02_v34"):
            blocked.enter_context(patch.object(formulas, name, forbidden))
        blocked.enter_context(patch.object(converter.UnitConversionOwnerV1, "convert", forbidden))
        for row in original_rows:
            if row["case"] == "decimal_rounded_then_binary64":
                continue
            work = fresh(); original_proof = market(row, work); before = dict(work.consumed)
            retained_decimal = work._decimal_admissions[-1][0]
            proof = convert(row, original_proof, work)
            after = dict(work.consumed)
            assert proof["summary"]["converted_bits"] == row["converted_bits"]
            assert work._decimal_admissions[-1][0] is retained_decimal
            assert all(after[name] == before[name] for name in
                ("decimal_constructions", "decimal_parse_attempts", "retained_decimal_inputs", "integer_powers", "random_draws", "log_series_terms", "square_roots"))
            assert after["serialized_bytes"] - before["serialized_bytes"] == len(wire(proof["summary"])) + len(wire(proof))
            edge_proof = edge(row, work)
            positives.append(dict(case=row["case"], source="ORIGINAL_B166_STYLE_STACK_OBSERVATIONS",
                market_proof=original_proof, conversion_proof=proof, edge_proof=edge_proof,
                before_conversion=before, after_conversion=after, after_edge=dict(work.consumed)))
        # These two independent fixed data vectors exercise a nonexact float
        # conversion and underflow-to-positive-zero. They confer no execution.
        for name, price, observed, output in (("data_decimal_tenth", "0.1", 0.1, 0.65),
                                               ("data_positive_underflow", "1E-324", 0.0, 0.75)):
            receipt = json.loads(base["conversion_receipt_json"])
            receipt.update(source_value=price, converted_value=observed)
            row = dict(base, case=name, producer_input_json=wire(dict(contract_price=price, payout_per_winning_contract="1")).decode(),
                producer_output_json=wire(price).decode(), conversion_receipt_json=wire(receipt).decode(),
                consumer_input_json=changed_consumer(base, market_implied_probability=observed).decode(), consumer_output_json=wire(output).decode())
            work = fresh(); original_proof = market(row, work); before = dict(work.consumed)
            proof = convert(row, original_proof, work); after = dict(work.consumed); edge_proof = edge(row, work)
            assert after["decimal_constructions"] == before["decimal_constructions"] == 5
            assert after["serialized_bytes"] - before["serialized_bytes"] == len(wire(proof["summary"])) + len(wire(proof))
            positives.append(dict(case=name, source="INDEPENDENT_FIXED_DATA_ONLY_NO_NATIVE_CONVERTER_OBSERVATION",
                market_proof=original_proof, conversion_proof=proof, edge_proof=edge_proof,
                before_conversion=before, after_conversion=after, after_edge=dict(work.consumed)))

        negative_zero = next(row for row in original_rows if row["case"] == "negative_market_zero")
        cases = (
            ("wrong_source_pair", base, dict(producer_input_json=wire(dict(contract_price="0.5", payout_per_winning_contract="2")))),
            ("wrong_raw_scale", base, dict(producer_raw_json=wire("0.250"))),
            ("noncanonical_source", base, dict(producer_input_json=base["producer_input_json"].encode()+b" ")),
            ("receipt_wrong_source", base, dict(conversion_receipt_json=changed_receipt(base, source_value="0.250"))),
            ("receipt_wrong_conversion", base, dict(conversion_receipt_json=changed_receipt(base, conversion_id="OTHER"))),
            ("receipt_wrong_version", base, dict(conversion_receipt_json=changed_receipt(base, conversion_version="2"))),
            ("receipt_wrong_basis", base, dict(conversion_receipt_json=changed_receipt(base,
                target=dict(type_name="float64", shape="scalar", unit="probability points", basis="OTHER")))),
            ("receipt_authority_flag", base, dict(conversion_receipt_json=changed_receipt(base, no_authority_flag=False))),
            ("receipt_extra_field", base, dict(conversion_receipt_json=changed_receipt(base, invented=True))),
            ("receipt_bool_float", base, dict(conversion_receipt_json=changed_receipt(base, converted_value=True))),
            ("receipt_integer_float", base, dict(conversion_receipt_json=changed_receipt(base, converted_value=0))),
            ("receipt_noncanonical", base, dict(conversion_receipt_json=base["conversion_receipt_json"].encode()+b" ")),
            ("receipt_wrong_stack", base, dict(conversion_receipt_json=changed_receipt(base,
                execution_context=dict(json.loads(base["conversion_receipt_json"])["execution_context"], dependency_graph_id="OTHER")))),
            ("wrong_consumer_bits", base, dict(consumer_input_json=changed_consumer(base, market_implied_probability=.5))),
            ("wrong_rounding_cell", base, dict(conversion_receipt_json=changed_receipt(base, converted_value=.5),
                consumer_input_json=changed_consumer(base, market_implied_probability=.5))),
            ("wrong_negative_zero", negative_zero, dict(conversion_receipt_json=changed_receipt(negative_zero, converted_value=0.0),
                consumer_input_json=changed_consumer(negative_zero, market_implied_probability=0.0))),
            ("uncalibrated_data", base, dict(consumer_input_json=changed_consumer(base, calibration_state="UNCALIBRATED"))),
        )
        def retain_denial(name, work, caught, **extra):
            consumed = dict(work.consumed)
            assert work.state == "FAILED"
            with pytest.raises(ComputationControlPlaneError):
                convert(base, {}, work)
            assert dict(work.consumed) == consumed
            denials.append(dict(case=name, diagnostic=str(caught), failure=work.failure, consumed=consumed, retry_denied=True, **extra))
        for name, row, changes in cases:
            work = fresh(); proof = market(row, work)
            with pytest.raises(ComputationControlPlaneError) as caught:
                convert(row, proof, work, **changes)
            retain_denial(name, work, caught.value)
        for name in ("copied_completion", "changed_completion", "foreign_work_completion", "no_completion", "stale_accounting",
                     "replaced_prefix", "replaced_admissions", "reused_completion", "completed_m04"):
            work = fresh(); proof = market(base, work)
            if name == "copied_completion": proof = copy.deepcopy(proof)
            elif name == "changed_completion": proof["projected_text"] = "0.5"
            elif name == "foreign_work_completion": proof = market(base, fresh())
            elif name == "no_completion": work = fresh()
            elif name == "stale_accounting":
                with work: work._emit(dict(unrelated=1))
            elif name == "replaced_prefix": work._math26_context_prefix = tuple(list(work._math26_context_prefix))
            elif name == "replaced_admissions": work._decimal_admissions = tuple(list(work._decimal_admissions))
            elif name == "reused_completion": convert(base, proof, work)
            elif name == "completed_m04":
                proof = policy._bounded_evidence_market_review_v1("MATH-04", (("best_bid", "0.25"), ("best_ask", "0.50"), ("payout", "1")),
                    lower_text="0", upper_text="1", raw_texts=("0.25",), expected_texts=("0.25",), projected_text="0.25", work=work)
            with pytest.raises(ComputationControlPlaneError) as caught:
                convert(base, proof, work)
            retain_denial(name, work, caught.value)

        row = next(row for row in original_rows if row["case"] == "decimal_rounded_then_binary64")
        work = fresh()
        with pytest.raises(ComputationControlPlaneError, match="LP03_MARKET_REVIEW_NONEXACT_CONTEXT_STEP") as caught:
            market(row, work)
        retain_denial("inexact_decimal34_remains_unqualified", work, caught.value,
            attempted_steps=len(work._math26_context_steps), completed_steps=len(work._math26_context_prefix))

        work = fresh(); original_encoder = serialization._encode_evidence_projection_json_v1
        def fail_complete(value, **kwargs):
            if type(value) is dict and value.get("profile") == "EXACT_DECIMAL_ORDERED_MARKET_INTERMEDIATES_V1":
                raise MemoryError("fixture complete proof encoding unavailable")
            return original_encoder(value, **kwargs)
        with patch.object(serialization, "_encode_evidence_projection_json_v1", fail_complete):
            with pytest.raises(ComputationControlPlaneError) as caught:
                market(base, work)
        assert len(work._math26_context_prefix) == 1 and len(work._decimal_admissions) == 5
        retain_denial("completed_step_without_completed_proof", work, caught.value,
            completed_steps=1, retained_decimal_inputs=5)

        work = fresh(max_serialized_bytes=20000); proof = market(base, work); before = dict(work.consumed)
        with pytest.raises(ComputationControlPlaneError, match="LP03_EDGE_CONVERSION_COMPLETE_BYTES_EXHAUSTED") as caught:
            convert(base, proof, work)
        assert dict(work.consumed) == before
        retain_denial("conversion_preflight_preserves_prefix", work, caught.value)

        # Same original work throughout two complete independent lane reviews.
        work = fresh(); lanes = []
        for ordinal in range(2):
            proof = market(base, work); conversion_proof = convert(base, proof, work); edge_proof = edge(base, work)
            assert conversion_proof["summary"]["original_context_step_ordinal"] == ordinal
            lanes.append(dict(market_proof=proof, conversion_proof=conversion_proof, edge_proof=edge_proof,
                consumed=dict(work.consumed)))
        assert work.consumed["decimal_constructions"] == work.consumed["retained_decimal_inputs"] == 10
        assert work.consumed["serialized_bytes"] == 2 * lanes[0]["consumed"]["serialized_bytes"] <= 65536
        before = dict(work.consumed)
        try:
            for ordinal in range(2, 64):
                proof = market(base, work); convert(base, proof, work); edge(base, work)
        except ComputationControlPlaneError as caught:
            retain_denial("cumulative_original_allowance", work, caught, successful_two_lane_prefix=before)
        else: raise AssertionError("original conversion review allowance did not exhaust")
    print("LP03_EDGE_CONVERSION_QUALIFICATION=" + deterministic_json(dict(
        scope="COMPLETED_SAME_WORK_M01_CONVERSION_M02_ARITHMETIC_ONLY_NO_NATIVE_OR_SOURCE_AUTHORITY",
        positives=positives, denials=denials, two_lane_prefix=lanes)))


def _assert_lp03_measured_probability_edge_chain():
    """Original local clock intervals; no grant, source or worker authority."""
    import json
    import sys
    from datetime import UTC, datetime, timedelta
    from unittest.mock import patch
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane import implementation_registry as owner
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane import unit_conversion as conversion_owner
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane import latency_policy as timing
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane import serialization
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.models import (
        ComputationExecutionContextV1, ComputationScopeV1, ImplementationVersionPinV1, EvidenceOriginV1)
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import ComputationControlPlaneError
    clock_type = timing._EvidenceLocalClockV1
    chain_type = owner._EvidenceProbabilityEdgeChainV1
    contracts = tuple(owner.resolve_evidence_invocation_v1(math_id,
        implementation_pin=owner.CURRENT_IMPLEMENTATION_REGISTRY[math_id].contract.implementation_id,
        specification_pin=owner.CURRENT_IMPLEMENTATION_REGISTRY[math_id].contract.specification_version,
        resource_policy_ref="MEASURE-P", origin=EvidenceOriginV1.SOFTWARE_CONFORMANCE) for math_id in ("MATH-01", "MATH-02"))
    moment = datetime(2026, 1, 1, tzinfo=UTC)
    context = ComputationExecutionContextV1(context_id="MEASURE-C", as_of=moment, observed_at=moment,
        source_epoch_id="MEASURE-E", input_version="1", maximum_age=timedelta(seconds=60),
        scope=ComputationScopeV1("MEASURE-M", "MEASURE-V", "MEASURE-EV", "MEASURE-I", "MEASURE-MODE", "MEASURE-S"),
        binding_profile_version="3.4", parameter_policy_version="MEASURE-P",
        dependency_graph_id="STACK::MATH-01::MATH-02::V3_4", dependency_graph_version="3.4",
        implementation_versions=tuple(ImplementationVersionPinV1(row.math_id, row.raw_implementation_id) for row in contracts))
    wire = lambda value: json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()
    def arguments(clock, *, payout="1", **changes):
        return dict(dict(contracts=contracts,
            market_input_json=wire(dict(contract_price="0.25", payout_per_winning_contract=payout)),
            model_input_json=wire(dict(calibrated_model_probability=.75, calibration_state="CALIBRATED_FOR_DECLARED_CONTEXT")),
            context=context, conversion_receipt_id="MEASURE-CONVERSION", maximum_input_bytes=65536,
            maximum_nodes=4096, maximum_output_bytes=65536, measurement_clock=clock), **changes)
    codes = {owner.compute_math_01_v34.__code__: "MATH-01", owner.compute_math_02_v34.__code__: "MATH-02",
             conversion_owner.UnitConversionOwnerV1.convert.__code__: "CONVERSION"}
    expected_calls = ["MATH-01", "CONVERSION", "MATH-02"]
    def execute(operation, hook=None):
        calls = []; previous = sys.getprofile()
        def profile(frame, event, arg):
            if event == "call" and frame.f_code in codes: calls.append(codes[frame.f_code])
            if hook is not None: hook(frame, event, arg)
        try:
            sys.setprofile(profile)
            chain_type.run_v1(operation)
        finally:
            sys.setprofile(previous)
        return calls
    def snapshot(operation):
        state = operation.inspect_v1(); stages = []
        for row in state["stage_records"]:
            value = dict(row)
            value["measurement_json"] = None if value["measurement_json"] is None else value["measurement_json"].decode()
            stages.append(json.loads(deterministic_json(value)))
        return dict(phase=state["phase"], failure_phase=state["failure_phase"], stages=stages,
            statuses={name:state[name+"_status"] for name in ("producer","conversion","consumer")},
            retained={name:state[name] is not None for name in ("producer","conversion","consumer")},
            serialized_bytes=state["serialized_bytes"],
            producer_output_json=None if state["producer"] is None else state["producer"].output_json.decode(),
            consumer_output_json=None if state["consumer"] is None else state["consumer"].output_json.decode(),
            conversion_receipt_json=None if state["conversion"] is None else deterministic_json(state["conversion"][1]),
            artifact_json=None if state["artifact_json"] is None else state["artifact_json"].decode())
    def retained_denial(name, operation, error, **extra):
        before = snapshot(operation)
        with pytest.raises(ComputationControlPlaneError, match="LP03_EDGE_CHAIN_ALREADY_STARTED_OR_UNRESOLVED"):
            execute(operation)
        assert snapshot(operation) == before
        denials.append(dict(case=name, error_class=type(error).__module__+"."+type(error).__qualname__,
            diagnostic=str(error), state=before, retry_denied=True, **extra))

    clock = clock_type(); operation = chain_type(**arguments(clock))
    aggregate_start = clock_type.observe_v1(clock)
    calls = execute(operation)
    aggregate_end = clock_type.observe_v1(clock)
    assert calls == expected_calls
    original = operation.inspect_v1(); positive = snapshot(operation)
    assert positive["phase"] == "COMPLETED"
    assert all(row["status"] == "VALIDATED" and row["call_outcome"] == "SUCCESS" for row in positive["stages"])
    stage_bytes = 0; previous = aggregate_start
    for row in positive["stages"]:
        measurement = row["measurement"]; assert measurement is not None and row["measurement_json"] is not None
        assert json.loads(row["measurement_json"])["measurement"] == measurement
        assert measurement["clock_domain_id"] == clock.clock_domain_id
        assert measurement["boot_identity_ref"] == clock.boot_identity_ref
        assert measurement["process_identity_ref"] == clock.process_identity_ref
        assert measurement["duration_ns"] == row["completed"][1] - row["started"][1] >= 0
        assert measurement["cpu_ns"] == row["completed"][2] - row["started"][2] >= 0
        assert all(a <= b <= c <= d for a,b,c,d in zip(previous,row["started"],row["completed"],aggregate_end))
        previous = row["completed"]; stage_bytes += len(row["measurement_json"].encode())
    artifact = json.loads(positive["artifact_json"])
    assert artifact["measured_original_stages"] == [json.loads(row["measurement_json"]) for row in positive["stages"]]
    fragment_bytes = (len(original["producer"].output_json), len(original["conversion_json"]), len(original["consumer_input"]),
                      len(original["consumer"].output_json), len(original["artifact_json"]))
    assert positive["serialized_bytes"] == sum(fragment_bytes) + stage_bytes <= 65536
    positive.update(aggregate_start=aggregate_start, aggregate_end=aggregate_end,
        aggregate_duration_ns=aggregate_end[1]-aggregate_start[1], aggregate_cpu_ns=aggregate_end[2]-aggregate_start[2],
        fragment_bytes=fragment_bytes, measurement_fragment_bytes=stage_bytes, calls=calls)
    denials = []

    # Original clock failures at each real stage boundary retain entered calls
    # and earlier observations. No clock value is invented or replayed.
    for position in range(1, 7):
        clock = clock_type(); operation = chain_type(**arguments(clock)); observed_calls = []; observations = [0]
        def fail_clock(frame, event, arg):
            if event == "call" and frame.f_code in codes: observed_calls.append(codes[frame.f_code])
            if event == "call" and frame.f_code is clock_type.observe_v1.__code__:
                observations[0] += 1
                if observations[0] == position: raise MemoryError("fixture native observation unavailable")
        with pytest.raises(MemoryError, match="fixture native observation unavailable") as caught:
            execute(operation, fail_clock)
        state = snapshot(operation); active = (position-1)//2
        assert observed_calls == expected_calls[:position//2]
        assert all(row["status"] == "VALIDATED" for row in state["stages"][:active])
        assert all(row["status"] == "NOT_ENTERED" for row in state["stages"][active+1:])
        row = state["stages"][active]
        assert row["measurement"] is None and row["measurement_json"] is None
        assert row["call_outcome"] == ("NOT_ENTERED" if position % 2 else "SUCCESS")
        assert row["completed"] is None
        if position % 2: assert row["started"] is None
        else: assert row["started"] is not None
        retained_denial("clock_boundary_"+str(position), operation, caught.value, original_calls=observed_calls)

    clock = clock_type(); operation = chain_type(**arguments(clock, payout="0")); observations=[0]
    def fail_secondary_end(frame,event,arg):
        if event == "call" and frame.f_code is clock_type.observe_v1.__code__:
            observations[0] += 1
            if observations[0] == 2: raise MemoryError("fixture secondary clock failure")
    with pytest.raises(ComputationControlPlaneError) as caught:
        execute(operation, fail_secondary_end)
    state=snapshot(operation)
    assert state["stages"][0]["call_outcome"] == "FAILED" and state["stages"][0]["measurement_failure_class"] == "builtins.MemoryError"
    assert state["stages"][0]["call_failure_class"] == type(caught.value).__module__+"."+type(caught.value).__qualname__
    assert state["retained"] == dict(producer=False,conversion=False,consumer=False)
    retained_denial("primary_call_error_survives_end_clock_error", operation, caught.value)

    for target, index in (("producer",0),("consumer",2)):
        clock=clock_type();operation=chain_type(**arguments(clock))
        def fail_witness(frame,event,arg):
            if event == "call" and frame.f_code.co_name == "witness_result" and frame.f_locals.get("name") == target:
                raise MemoryError("fixture return witness unavailable")
        with pytest.raises(MemoryError,match="fixture return witness unavailable") as caught:execute(operation,fail_witness)
        state=snapshot(operation);row=state["stages"][index]
        assert row["call_outcome"] == "SUCCESS" and row["measurement"] is not None
        assert row["status"] == "RETURNED_UNWITNESSED" and state["statuses"][target] == "RETURNED_UNWITNESSED"
        retained_denial(target+"_witness_after_measured_return",operation,caught.value)

    # Failure at the capture-call entry still records a successful original
    # return and attempts one end observation without encoding a measurement.
    clock=clock_type();operation=chain_type(**arguments(clock))
    def fail_capture(frame,event,arg):
        if event == "call" and frame.f_code.co_name == "latch_return_members" and frame.f_locals.get("name") == "producer":
            raise MemoryError("fixture capture call allocation unavailable")
    with pytest.raises(MemoryError,match="fixture capture call allocation unavailable") as caught:execute(operation,fail_capture)
    state=snapshot(operation);row=state["stages"][0]
    assert state["retained"]["producer"] and row["call_outcome"] == "SUCCESS" and row["completed"] is not None
    assert row["measurement"] is None and row["measurement_json"] is None
    retained_denial("capture_call_entry_allocation",operation,caught.value)

    for target, boundary in (("producer",2),("conversion_descriptor",4),("consumer",6)):
        clock=clock_type();operation=chain_type(**arguments(clock));observations=[0];changed=[]
        def mutate_at_end(frame,event,arg):
            if event == "call" and frame.f_code is clock_type.observe_v1.__code__:
                observations[0] += 1
                if observations[0] == boundary:
                    if target == "conversion_descriptor":obj=operation.conversion[1].target;field="basis";value="OTHER"
                    else:obj=getattr(operation,target);field="output_json";value=b'"substituted"'
                    changed.append((obj,field,object.__getattribute__(obj,field)))
                    object.__setattr__(obj,field,value)
        try:
            with pytest.raises(ComputationControlPlaneError,match="CHANGED_DURING_OBSERVATION") as caught:execute(operation,mutate_at_end)
        finally:
            for obj,field,value in changed:object.__setattr__(obj,field,value)
        state=snapshot(operation);row=state["stages"][(boundary-1)//2]
        assert row["completed"] is not None and row["call_outcome"] == "SUCCESS" and row["measurement"] is None
        retained_denial(target+"_substitution_during_end_observation",operation,caught.value)

    clock=clock_type();operation=chain_type(**arguments(clock))
    def descriptor_failure(frame,event,arg):
        if event == "call" and frame.f_code is conversion_owner.UnitBasisDescriptorV1.__post_init__.__code__:
            if frame.f_locals["self"].basis == "unit interval":raise MemoryError("fixture descriptor construction unavailable")
    with pytest.raises(MemoryError,match="fixture descriptor construction unavailable") as caught:execute(operation,descriptor_failure)
    assert snapshot(operation)["stages"][1]["status"] == snapshot(operation)["stages"][1]["call_outcome"] == "NOT_ENTERED"
    retained_denial("descriptor_construction_is_not_converter_entry",operation,caught.value)

    for point in ("wire_owner", "clock_owner", "input_descriptor"):
        clock=clock_type();operation=chain_type(**arguments(clock));observations=[0];changed=[];original_calls=[]
        original_observe=clock_type.observe_v1;original_wire=owner.invoke_evidence_public_wire_v1
        def forbidden(*args,**kwargs):raise AssertionError("substituted owner must not run")
        def substitute_after_start(frame,event,arg):
            if event == "call" and frame.f_code in codes:original_calls.append(codes[frame.f_code])
            if event == "call" and frame.f_code is original_observe.__code__:
                observations[0] += 1
                wanted=3 if point == "input_descriptor" else 1
                if observations[0] == wanted:
                    if point == "wire_owner":owner.invoke_evidence_public_wire_v1=forbidden
                    elif point == "clock_owner":clock_type.observe_v1=forbidden
                    else:
                        run_frame=frame.f_back.f_back
                        obj=run_frame.f_locals["source_descriptor"]
                        changed.append((obj,obj.basis));object.__setattr__(obj,"basis","OTHER")
        try:
            with pytest.raises(ComputationControlPlaneError) as caught:execute(operation,substitute_after_start)
        finally:
            owner.invoke_evidence_public_wire_v1=original_wire;clock_type.observe_v1=original_observe
            for obj,basis in changed:object.__setattr__(obj,"basis",basis)
        assert original_calls == (["MATH-01"] if point == "input_descriptor" else [])
        state=snapshot(operation);active=1 if point == "input_descriptor" else 0
        assert state["stages"][active]["started"] is not None
        assert state["stages"][active]["call_outcome"] == "NOT_ENTERED"
        retained_denial(point+"_substitution_during_start_observation",operation,caught.value,original_calls=original_calls)

    for point in ("encoding", "validation"):
        clock=clock_type();operation=chain_type(**arguments(clock));original_encoder=serialization._encode_evidence_projection_json_v1
        def fail_encoding(value,**kwargs):
            if type(value) is dict and value.get("stage") == "MATH-01" and "measurement" in value:
                raise MemoryError("fixture measurement encoding unavailable")
            return original_encoder(value,**kwargs)
        def fail_validation(frame,event,arg):
            if event == "call" and frame.f_code is timing._evidence_invocation_measurement_v1.__code__:
                raise MemoryError("fixture measurement freezing unavailable")
        if point == "encoding":
            with patch.object(serialization,"_encode_evidence_projection_json_v1",fail_encoding):
                with pytest.raises(MemoryError) as caught:execute(operation)
        else:
            with pytest.raises(MemoryError) as caught:execute(operation,fail_validation)
        state=snapshot(operation);row=state["stages"][0]
        assert row["call_outcome"] == "SUCCESS" and row["completed"] is not None and row["measurement"] is None
        expected_bytes=len(state["producer_output_json"].encode())
        if point == "validation":expected_bytes+=len(row["measurement_json"].encode())
        else:assert row["measurement_json"] is None
        assert state["serialized_bytes"] == expected_bytes
        retained_denial("measurement_"+point+"_failure",operation,caught.value)

    # Known metadata must fit prospectively; no producer is entered here.
    for label,changes in (("too_small_clock_scope",dict(maximum_output_bytes=512)),("wrong_clock_type",dict(measurement_clock=object()))):
        clock=clock_type();constructor_calls=[];previous_profile=sys.getprofile()
        def observe_constructor(frame,event,arg):
            if event == "call" and frame.f_code in codes:constructor_calls.append(codes[frame.f_code])
        try:
            sys.setprofile(observe_constructor)
            with pytest.raises(ComputationControlPlaneError) as caught:chain_type(**arguments(clock,**changes))
        finally:
            sys.setprofile(previous_profile)
        assert constructor_calls == []
        denials.append(dict(case=label,stage="CONSTRUCTOR",diagnostic=str(caught.value),
            original_calls=constructor_calls,original_calls_observed=True))
    print("LP03_EDGE_LOCAL_MEASUREMENT_QUALIFICATION=" + deterministic_json(dict(
        scope="ORIGINAL_LOCAL_CALL_INTERVALS_NO_SOURCE_CALIBRATION_GRANT_WORKER_OR_PUBLICATION_AUTHORITY",
        interval_scope="INCLUDES_FIXED_CUSTODY_CHECKS_RETURN_CAPTURE_AND_ACCOUNTING; EXCLUDES_INTERSTAGE_WORK",
        positive=positive,denials=denials)))
    _assert_lp03_probability_edge_worker_outputs(arguments, execute, contracts)
    _assert_lp03_probability_edge_clock_limits(arguments, execute, contracts)


def _assert_lp03_probability_edge_worker_outputs(arguments, execute, contracts):
    """Original local returns through closed codecs; no worker/source grant."""
    import json
    import sys
    from dataclasses import replace
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane import implementation_registry as owner
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane import latency_policy as timing
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane import evidence_execution as worker
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import ComputationControlPlaneError
    clock_type=timing._EvidenceLocalClockV1;chain_type=owner._EvidenceProbabilityEdgeChainV1
    wire=lambda value:json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=False,allow_nan=False).encode()
    native=lambda value:json.loads(deterministic_json(value))
    attempt_ref="MEASURE";fence_ref="MEASURE-FENCE"
    def make(clock):
        values=arguments(clock)
        values["context"]=replace(values["context"],parameter_policy_version="ST12F_PARAMETER_RESOURCE_ROW_V1")
        values["conversion_receipt_id"]=attempt_ref+"::CONVERSION"
        return chain_type(**values)
    def framed(kind,payload):
        frame=dict(protocol=worker.WORKER_PROTOCOL_V1,kind=kind,attempt_ref=attempt_ref,fence_ref=fence_ref,ordinal=2,payload=payload)
        raw=worker.encode_evidence_worker_frame_v1(frame,direction="WORKER_TO_PARENT",attempt_ref=attempt_ref,
            fence_ref=fence_ref,ordinal=2,frame_byte_limit=65536)
        decoded=worker.decode_evidence_worker_frame_v1(raw,direction="WORKER_TO_PARENT",attempt_ref=attempt_ref,
            fence_ref=fence_ref,ordinal=2,frame_byte_limit=65536)
        assert deterministic_json(decoded).encode()==raw[4:]
        return raw
    def failed_payload(prefix):
        return dict(reason_code="WORKER_PROTOCOL_OR_COMPUTATION_FAILED",exception_class="builtins.MemoryError",event_ordinal=0,
            measurement_or_absence=dict(state="ABSENT_WITH_REASON",reason="INVOCATION_CLOCK_UNAVAILABLE"),
            invocation_contract=native(contracts[1]),producer_invocation_contract=native(contracts[0]),
            chain_prefix_or_absence=dict(state="CAPTURED_ORIGINAL_PREFIX_DIAGNOSTIC",prefix_json=prefix.decode()))
    denials=[]
    def denied(name,kind,payload):
        with pytest.raises(ComputationControlPlaneError) as caught:framed(kind,payload)
        denials.append(dict(case=name,diagnostic=str(caught.value)))
    clock=clock_type();operation=make(clock);began=clock_type.observe_v1(clock)
    calls=execute(operation);ended=clock_type.observe_v1(clock);state=operation.inspect_v1()
    measurement=native(timing._evidence_invocation_measurement_v1(dict(clock_domain_id=clock.clock_domain_id,
        boot_identity_ref=clock.boot_identity_ref,process_identity_ref=clock.process_identity_ref,
        clock_declarations=clock_type.declaration_v1(clock),started=began,completed=ended,
        duration_ns=ended[1]-began[1],cpu_ns=ended[2]-began[2],outcome="SUCCESS")))
    result=dict(event_ordinal=0,invocation_contract=native(contracts[1]),producer_invocation_contract=native(contracts[0]),
        numeric_context_policy_ref=owner.LP03_DECIMAL_CONTEXT_POLICY_REF_V1,raw_output_json=state["consumer"].output_json.decode(),
        original_record_refs=[dict(store_id="DATA",record_id="LOCAL-DATA-ONLY")],invocation_measurement=measurement,
        chain_artifact_json=state["artifact_json"].decode())
    result_frame=framed("COMPUTATION_RESULT",result)
    prefix=chain_type.failure_prefix_v1(operation,maximum_bytes=65536,maximum_embedded_bytes=65536)
    completed_frame=framed("FAILED",failed_payload(prefix))
    completed=json.loads(prefix)
    assert completed["phase"]=="COMPLETED" and calls==["MATH-01","CONVERSION","MATH-02"]
    assert completed["returns"][0]["output_json_or_absence"]["value"]=='"0.25"'
    assert completed["returns"][1]["output_json_or_absence"]["value"]=='0.5'
    assert completed["clock_declarations"]==measurement["clock_declarations"]
    actual_embedded=len(wire(prefix.decode()))
    assert chain_type.failure_prefix_v1(operation,maximum_bytes=len(prefix),maximum_embedded_bytes=actual_embedded)==prefix
    for name,changes in (("prefix_one_byte_too_small",dict(maximum_bytes=len(prefix)-1,maximum_embedded_bytes=actual_embedded)),
                         ("embedded_one_byte_too_small",dict(maximum_bytes=len(prefix),maximum_embedded_bytes=actual_embedded-1))):
        with pytest.raises(ComputationControlPlaneError) as caught:chain_type.failure_prefix_v1(operation,**changes)
        denials.append(dict(case=name,diagnostic=str(caught.value)))
    for name in ("wrong_conversion_bits", "reordered_stages", "different_stage_clock", "wrong_context_pin", "wrong_main_raw"):
        payload=json.loads(wire(result));artifact=json.loads(payload["chain_artifact_json"])
        if name=="wrong_conversion_bits":
            data=json.loads(artifact["consumer_input_json"]);data["market_implied_probability"]=.5;artifact["consumer_input_json"]=wire(data).decode()
        elif name=="reordered_stages":artifact["measured_original_stages"].reverse()
        elif name=="different_stage_clock":artifact["measured_original_stages"][1]["measurement"]["process_identity_ref"]="OTHER"
        elif name=="wrong_context_pin":
            data=json.loads(artifact["conversion_receipt_json"]);data["execution_context"]["implementation_versions"].reverse()
            artifact["conversion_receipt_json"]=wire(data).decode()
        else:payload["raw_output_json"]="0.25"
        payload["chain_artifact_json"]=wire(artifact).decode();denied(name,"COMPUTATION_RESULT",payload)
    failure_cases=[]
    for target,boundary in (("producer",2),("conversion_descriptor",4),("consumer",6),("wire_owner",1),("clock_owner",1),("capture_entry",0)):
        clock=clock_type();operation=make(clock);observations=[0];changed=[]
        original_observe=clock_type.observe_v1;original_wire=owner.invoke_evidence_public_wire_v1
        def forbidden(*args,**kwargs):raise AssertionError("substituted owner must not execute")
        def inject(frame,event,arg):
            if target=="capture_entry" and event=="call" and frame.f_code.co_name=="latch_return_members" and frame.f_locals.get("name")=="producer":
                raise MemoryError("fixture capture frame allocation unavailable")
            if event=="call" and frame.f_code is original_observe.__code__:
                observations[0]+=1
                if observations[0]==boundary:
                    if target=="wire_owner":owner.invoke_evidence_public_wire_v1=forbidden
                    elif target=="clock_owner":clock_type.observe_v1=forbidden
                    else:
                        obj=operation.conversion[1].target if target=="conversion_descriptor" else getattr(operation,target)
                        field="basis" if target=="conversion_descriptor" else "output_json"
                        changed.append((obj,field,object.__getattribute__(obj,field)))
                        object.__setattr__(obj,field,"OTHER" if field=="basis" else b'not canonical JSON')
        try:
            with pytest.raises((ComputationControlPlaneError,MemoryError)) as caught:execute(operation,inject)
            if target!="capture_entry":
                with pytest.raises(ComputationControlPlaneError):operation.inspect_v1()
            # Export while the damaged object/owner is still damaged. Neither
            # restoration nor ordinary inspect supplies the captured bytes.
            raw=chain_type.failure_prefix_v1(operation,maximum_bytes=65536,maximum_embedded_bytes=65536)
            prefix_data=json.loads(raw);payload=failed_payload(raw)
            payload["exception_class"]=type(caught.value).__module__+"."+type(caught.value).__qualname__
            encoded=framed("FAILED",payload)
            assert prefix_data["phase"]=="FAILED"
            if target in ("producer","consumer"):
                index=0 if target=="producer" else 1
                assert prefix_data["returns"][index]["output_json_or_absence"]["value"]==('"0.25"' if index==0 else '0.5')
            if target=="conversion_descriptor":
                assert prefix_data["conversion"]["input_descriptor_captures"][1]["fields"]["basis"]=="unit interval"
                assert prefix_data["conversion"]["converted_binary64_or_absence"]["big_endian_hex"]=="3fd0000000000000"
            if target=="capture_entry":
                assert prefix_data["returns"][0]["captured_member_count"]==0
                assert prefix_data["returns"][0]["return_status"]=="RETURNED_UNWITNESSED"
            failure_cases.append(dict(case=target,prefix=prefix_data,frame_bytes=len(encoded),captured_before_restoration=True,
                primary_exception_class=payload["exception_class"]))
        finally:
            owner.invoke_evidence_public_wire_v1=original_wire;clock_type.observe_v1=original_observe
            for obj,field,value in changed:object.__setattr__(obj,field,value)
    # Opaque unwitnessed diagnostic bytes may explain the failure. They cannot
    # be interpreted as completed result JSON or promoted to result authority.
    opaque=json.loads(wire(failure_cases[0]["prefix"]))
    opaque["returns"][0]["output_json_or_absence"]["value"]='not canonical JSON\n"é\\'
    opaque_frame=framed("FAILED",failed_payload(wire(opaque)))
    opaque["returns"][0]["output_json_or_absence"]["value"]=""
    empty_opaque_frame=framed("FAILED",failed_payload(wire(opaque)))
    for name in ("false_completed_phase", "reached_later_stage", "false_validated_measurement", "false_return_capture"):
        data=json.loads(wire(failure_cases[0]["prefix"]))
        if name=="false_completed_phase":data["phase"]="COMPLETED";data["failure_phase"]=None
        elif name=="reached_later_stage":data["stages"][2]=json.loads(wire(completed["stages"][2]));data["returns"][1]=json.loads(wire(completed["returns"][1]))
        elif name=="false_validated_measurement":data["stages"][0]["measurement_validation"]="VALIDATED"
        else:data["returns"][0]["return_status"]="NOT_RETURNED"
        denied(name,"FAILED",failed_payload(wire(data)))
    for name in ("witnessed_producer_missing_bytes", "witnessed_conversion_missing_bits", "witnessed_conversion_missing_descriptors"):
        data=json.loads(wire(completed))
        if name=="witnessed_producer_missing_bytes":
            data["phase"]="FAILED";data["failure_phase"]="MATH02_RETURNED"
            data["returns"][0]["output_json_or_absence"]=dict(state="ABSENT_WITH_REASON",reason="CAPTURED_OUTPUT_MEMBER_NOT_BYTES")
        elif name=="witnessed_conversion_missing_bits":
            data["conversion"]["converted_binary64_or_absence"]=dict(state="ABSENT_WITH_REASON",reason="CAPTURED_CONVERTED_MEMBER_NOT_BINARY64")
        else:data["conversion"]["input_descriptor_captures"]=[dict(captured_member_count=0,fields={})]*2
        denied(name,"FAILED",failed_payload(wire(data)))
    print("LP03_EDGE_OUTPUT_CODEC_QUALIFICATION="+deterministic_json(dict(
        scope="LOCAL_ORIGINAL_RETURN_CAPTURE_AND_CLOSED_CODEC_ONLY_NO_SOURCE_WORKER_GRANT_OR_PUBLICATION_AUTHORITY",
        positive_result=result,result_frame_bytes=len(result_frame),completed_prefix=completed,
        completed_failure_frame_bytes=len(completed_frame),prefix_bytes=len(prefix),embedded_prefix_bytes=actual_embedded,
        failure_cases=failure_cases,opaque_unwitnessed_diagnostic_frame_bytes=len(opaque_frame),
        empty_unwitnessed_diagnostic_frame_bytes=len(empty_opaque_frame),denials=denials)))


def _assert_lp03_probability_edge_clock_limits(arguments, execute, contracts):
    """Actual local observations and prospective bounds; no execution grant."""
    import json
    import sys
    import time
    from dataclasses import replace
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane import implementation_registry as owner
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane import unit_conversion as conversion_owner
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane import latency_policy as timing
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane import evidence_execution as worker
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import ComputationControlPlaneError
    clock_type=timing._EvidenceLocalClockV1;chain_type=owner._EvidenceProbabilityEdgeChainV1
    native=lambda value:json.loads(deterministic_json(value))
    wire=lambda value:json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=False,allow_nan=False).encode()
    names=("valid_from_wall_ns","exclusive_expiry_wall_ns","admitted_monotonic_ns","exclusive_deadline_monotonic_ns")
    refs=[dict(store_id="DATA",record_id="LOCAL-DATA-ONLY")];attempt_ref="MEASURE";fence_ref="MEASURE-FENCE"
    denials=[];failures=[]
    def args(clock,limits,*,maximum_output_bytes=65536,payout="1",**changes):
        values=arguments(clock,payout=payout)
        values.update(context=replace(values["context"],parameter_policy_version="ST12F_PARAMETER_RESOURCE_ROW_V1"),
            conversion_receipt_id=attempt_ref+"::CONVERSION",maximum_output_bytes=maximum_output_bytes,execution_clock_limits=limits)
        values.update(changes);return values
    def framed(kind,payload):
        raw=worker.encode_evidence_worker_frame_v1(dict(protocol=worker.WORKER_PROTOCOL_V1,kind=kind,
            attempt_ref=attempt_ref,fence_ref=fence_ref,ordinal=2,payload=payload),direction="WORKER_TO_PARENT",
            attempt_ref=attempt_ref,fence_ref=fence_ref,ordinal=2,frame_byte_limit=65536)
        decoded=worker.decode_evidence_worker_frame_v1(raw,direction="WORKER_TO_PARENT",attempt_ref=attempt_ref,
            fence_ref=fence_ref,ordinal=2,frame_byte_limit=65536)
        assert deterministic_json(decoded).encode()==raw[4:]
        return raw
    def prefix(operation):
        return json.loads(chain_type.failure_prefix_v1(operation,maximum_bytes=65536,maximum_embedded_bytes=65536))
    def fail_payload(data,clock,*,aggregate_prefix,measurement):
        return dict(reason_code="WORKER_PROTOCOL_OR_COMPUTATION_FAILED",exception_class="builtins.MemoryError",event_ordinal=0,
            measurement_or_absence=measurement,invocation_contract=native(contracts[1]),producer_invocation_contract=native(contracts[0]),
            aggregate_observation_prefix=aggregate_prefix,
            chain_prefix_or_absence=dict(state="CAPTURED_ORIGINAL_PREFIX_DIAGNOSTIC",prefix_json=wire(data).decode()))
    def failed_interval(clock,began,ended):
        identity=dict(clock_domain_id=clock.clock_domain_id,boot_identity_ref=clock.boot_identity_ref,process_identity_ref=clock.process_identity_ref)
        declarations=native(clock_type.declaration_v1(clock))
        measurement=native(timing._evidence_invocation_measurement_v1(dict(identity,clock_declarations=declarations,
            started=began,completed=ended,duration_ns=ended[1]-began[1],cpu_ns=ended[2]-began[2],outcome="FAILED")))
        outer=dict(clock_identity=identity,clock_declarations=declarations,started=began,completed=ended,
            call_outcome="FAILED",measurement_failure_class_or_none=None)
        return dict(aggregate_prefix=outer,measurement=measurement)
    codes={owner.compute_math_01_v34.__code__:"MATH-01",owner.compute_math_02_v34.__code__:"MATH-02",
           conversion_owner.UnitConversionOwnerV1.convert.__code__:"CONVERSION"}
    def no_call_denial(name, action):
        observed=[];prior=sys.getprofile()
        def profile(frame,event,arg):
            if event=="call" and frame.f_code in codes:observed.append(codes[frame.f_code])
        try:
            sys.setprofile(profile)
            with pytest.raises(ComputationControlPlaneError) as caught:action()
        finally:sys.setprofile(prior)
        assert observed==[]
        denials.append(dict(case=name,original_calls_observed=observed,diagnostic=str(caught.value),
            exception_class=type(caught.value).__module__+"."+type(caught.value).__qualname__))
        return caught.value
    clock=clock_type();observed=clock_type.observe_v1(clock)
    limits=(0,observed[0]+60_000_000_000,0,observed[1]+60_000_000_000)
    base=args(clock,limits)
    cap_args=dict(clock=clock,contracts=contracts,attempt_ref=attempt_ref,fence_ref=fence_ref,original_record_refs=refs,
        market_input_json=base["market_input_json"],frame_byte_limit=65536,remaining_output_bytes=1_000_000)
    capacity=worker._worker_probability_edge_capacity_v1(**cap_args)
    operation=chain_type(**args(clock,limits,maximum_output_bytes=capacity["chain_output_limit"]))
    assert operation.execution_clock_limits is limits
    began=clock_type.observe_v1(clock);calls=execute(operation);ended=clock_type.observe_v1(clock)
    state=operation.inspect_v1();artifact=json.loads(state["artifact_json"])
    assert calls==["MATH-01","CONVERSION","MATH-02"] and artifact["execution_clock_limits"]==dict(zip(names,limits))
    aggregate=native(timing._evidence_invocation_measurement_v1(dict(clock_domain_id=clock.clock_domain_id,
        boot_identity_ref=clock.boot_identity_ref,process_identity_ref=clock.process_identity_ref,
        clock_declarations=clock_type.declaration_v1(clock),started=began,completed=ended,
        duration_ns=ended[1]-began[1],cpu_ns=ended[2]-began[2],outcome="SUCCESS")))
    result=dict(event_ordinal=0,invocation_contract=native(contracts[1]),producer_invocation_contract=native(contracts[0]),
        numeric_context_policy_ref=owner.LP03_DECIMAL_CONTEXT_POLICY_REF_V1,raw_output_json=state["consumer"].output_json.decode(),
        original_record_refs=refs,invocation_measurement=aggregate,chain_artifact_json=state["artifact_json"].decode())
    result_raw=framed("COMPUTATION_RESULT",result)
    positive_prefix=prefix(operation)
    outer=dict(clock_identity={name:aggregate[name] for name in ("clock_domain_id","boot_identity_ref","process_identity_ref")},
        clock_declarations=aggregate["clock_declarations"],started=began,completed=ended,call_outcome="SUCCESS",measurement_failure_class_or_none=None)
    failed=fail_payload(positive_prefix,clock,aggregate_prefix=outer,measurement=aggregate)
    failure_raw=framed("FAILED",failed)
    assert len(result_raw)<=capacity["success_frame_bound"] and len(failure_raw)<=capacity["failure_frame_bound"]
    assert state["serialized_bytes"]<=capacity["chain_output_limit"]
    positive=dict(result=result,aggregate_prefix=native(outer),prefix=positive_prefix,serialized_bytes=state["serialized_bytes"],
        capacity=dict(capacity),result_frame_bytes=len(result_raw),completed_failure_frame_bytes=len(failure_raw),original_calls=calls)
    no_call_denial("insufficient_remaining_output",lambda:worker._worker_probability_edge_capacity_v1(**dict(cap_args,remaining_output_bytes=1)))
    no_call_denial("insufficient_frame_capacity",lambda:worker._worker_probability_edge_capacity_v1(**dict(cap_args,frame_byte_limit=4096)))
    for name,changes in (("no_original_clock",dict(measurement_clock=None)),("mutable_limit_list",dict(execution_clock_limits=list(limits))),
        ("bool_limit",dict(execution_clock_limits=(False,limits[1],0,limits[3]))),
        ("empty_wall_interval",dict(execution_clock_limits=(limits[1],limits[1],0,limits[3]))),
        ("empty_monotonic_interval",dict(execution_clock_limits=(0,limits[1],limits[3],limits[3]))),
        ("overflow_limit",dict(execution_clock_limits=(0,2**63,0,limits[3])))):
        no_call_denial(name,lambda changes=changes:chain_type(**args(clock,limits,**changes)))
    for name in ("expired_wall_entry","expired_monotonic_entry","future_wall_lower","future_monotonic_lower"):
        clock=clock_type();seen=clock_type.observe_v1(clock)
        bounds=[0,seen[0]+60_000_000_000,0,seen[1]+60_000_000_000]
        if name=="expired_wall_entry":bounds[1]=seen[0]
        elif name=="expired_monotonic_entry":bounds[3]=seen[1]
        elif name=="future_wall_lower":bounds[0]=seen[0]+30_000_000_000
        else:bounds[2]=seen[1]+30_000_000_000
        operation=chain_type(**args(clock,tuple(bounds)))
        interval=[None,None]
        def try_entry():
            interval[0]=clock_type.observe_v1(clock)
            try:chain_type.run_v1(operation)
            finally:interval[1]=clock_type.observe_v1(clock)
        entry_error=no_call_denial(name,try_entry)
        data=prefix(operation);assert data["stages"][0]["started"] is not None
        assert data["stages"][0]["call_outcome"]=="NOT_ENTERED"
        observed_interval=failed_interval(clock,*interval)
        failed_frame=fail_payload(data,clock,**observed_interval)
        failed_frame["exception_class"]=type(entry_error).__module__+"."+type(entry_error).__qualname__
        framed("FAILED",failed_frame)
        failures.append(dict(case=name,prefix=data,original_calls=[],primary_exception_class=failed_frame["exception_class"],**observed_interval))
    # Wait on real monotonic time inside the fixture's original return hook.
    # No clock sample is invented, replaced, or returned from a fake clock.
    for target,payout in (("MATH-01","1"),("CONVERSION","1"),("MATH-01","0")):
        clock=clock_type();seen=clock_type.observe_v1(clock);bounds=(0,seen[0]+2_000_000_000,0,seen[1]+2_000_000_000)
        operation=chain_type(**args(clock,bounds,payout=payout));calls=[];waited=[False]
        def delay_return(frame,event,arg):
            if event=="call" and frame.f_code in codes:calls.append(codes[frame.f_code])
            if event=="return" and codes.get(frame.f_code)==target and not waited[0]:
                waited[0]=True
                while clock_type.observe_v1(clock)[1]<bounds[3]:time.sleep(.01)
        began=clock_type.observe_v1(clock)
        with pytest.raises(ComputationControlPlaneError) as caught:execute(operation,delay_return)
        ended=clock_type.observe_v1(clock)
        data=prefix(operation);index=0 if target=="MATH-01" else 1;active=data["stages"][index]
        assert waited[0] and active["completed"][1]>=bounds[3] and active["measurement_validation"]=="NOT_VALIDATED"
        assert calls==(["MATH-01"] if index==0 else ["MATH-01","CONVERSION"])
        assert all(row["status"]=="NOT_ENTERED" for row in data["stages"][index+1:])
        if payout=="0":
            assert active["call_outcome"]=="FAILED" and "EXECUTION_CLOCK_EXPIRED" not in str(caught.value)
        else:
            assert active["call_outcome"]=="SUCCESS" and "EXECUTION_CLOCK_EXPIRED" in str(caught.value)
        observed_interval=failed_interval(clock,began,ended)
        failed_frame=fail_payload(data,clock,**observed_interval)
        failed_frame["exception_class"]=type(caught.value).__module__+"."+type(caught.value).__qualname__
        framed("FAILED",failed_frame)
        failures.append(dict(case="late_"+target if payout=="1" else "primary_call_error_before_expiry_error",
            prefix=data,original_calls=calls,diagnostic=str(caught.value),**observed_interval))
    # Closed data denials use retained real samples, never invented timings.
    for name in ("result_exclusive_end","validated_failure_outside_limit","outer_identity_mismatch","absent_chain_bad_aggregate", "inactive_stage_error_label"):
        payload=json.loads(wire(failed))
        if name=="result_exclusive_end":
            payload=json.loads(wire(result));data=json.loads(payload["chain_artifact_json"])
            data["execution_clock_limits"]["exclusive_deadline_monotonic_ns"]=aggregate["completed"][1]
            payload["chain_artifact_json"]=wire(data).decode();kind="COMPUTATION_RESULT"
        else:
            kind="FAILED"
            if name=="validated_failure_outside_limit":
                payload["measurement_or_absence"]["outcome"]="FAILED"
                payload["aggregate_observation_prefix"]["call_outcome"]="FAILED"
                data=json.loads(payload["chain_prefix_or_absence"]["prefix_json"])
                data["phase"]="FAILED";data["failure_phase"]="MATH02_RETURNED"
                data["stages"][2]["status"]="RETURNED_UNWITNESSED"
                data["stages"][2]["return_processing_failure_class"]="builtins.MemoryError"
                data["execution_clock_limits"]["exclusive_deadline_monotonic_ns"]=data["stages"][2]["completed"][1]
                payload["chain_prefix_or_absence"]["prefix_json"]=wire(data).decode()
            elif name=="outer_identity_mismatch":payload["aggregate_observation_prefix"]["clock_identity"]["process_identity_ref"]="OTHER"
            elif name=="absent_chain_bad_aggregate":
                payload["chain_prefix_or_absence"]=dict(state="ABSENT_WITH_REASON",reason="CHAIN_NOT_CREATED",capture_exception_class_or_none=None)
                payload["aggregate_observation_prefix"]["completed"]=None
            else:
                payload["measurement_or_absence"]["outcome"]="FAILED"
                payload["aggregate_observation_prefix"]["call_outcome"]="FAILED"
                data=json.loads(payload["chain_prefix_or_absence"]["prefix_json"])
                data["phase"]="FAILED";data["failure_phase"]="MATH02_RETURNED"
                data["stages"][0]["return_processing_failure_class"]="builtins.MemoryError"
                payload["chain_prefix_or_absence"]["prefix_json"]=wire(data).decode()
        with pytest.raises(ComputationControlPlaneError) as caught:framed(kind,payload)
        if name=="validated_failure_outside_limit":assert "VALIDATED_CLOCK_LIMIT" in str(caught.value)
        if name=="inactive_stage_error_label":assert "INACTIVE_STAGE_LABELS" in str(caught.value)
        denials.append(dict(case=name,diagnostic=str(caught.value)))
    print("LP03_EDGE_CLOCK_RESTRICTION_QUALIFICATION="+deterministic_json(dict(
        scope="LOCAL_CLOCK_RESTRICTIONS_AND_CAPACITY_DATA_ONLY_NO_GRANT_OR_NATIVE_WORKER_AUTHORITY",
        positive=positive,failures=failures,denials=denials)))


def _assert_lp03_probability_edge_model_proof():
    import json
    import struct
    from contextlib import ExitStack
    from unittest.mock import patch
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane import implementation_registry as formulas
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.evidence import IndependentEvidenceReviewV1
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.parameter_policy import _EvidenceNumericalWorkV1
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import ComputationControlPlaneError
    limits = dict(max_input_bits=4096, max_work_bits=65536, max_serialized_bytes=65536)
    # Independently fixed Fraction/midpoint literals; these are not captured
    # formula outputs, source receipts or calibration certificates.
    cases = json.loads('[{"case":"positive","inputs":{"calibrated_model_probability":0.75,"calibration_state":"CALIBRATED_FOR_DECLARED_CONTEXT","market_implied_probability":0.25},"proof":{"candidate_bits":"3fe0000000000000","exact_difference":{"denominator":"2","numerator":"1"},"market_bits":"3fd0000000000000","model_bits":"3fe8000000000000","profile":"REPRESENTED_BINARY64_MODEL_MINUS_MARKET_NEAREST_EVEN","raw_json":"0.5","rounding_midpoints":[{"denominator":"36028797018963968","numerator":"18014398509481983"},{"denominator":"18014398509481984","numerator":"9007199254740993"}],"scope":"SOFTWARE_ARITHMETIC_MODEL_ONLY_NO_CALIBRATION_MARKET_SOURCE_OR_TRADING_AUTHORITY","tie":false}},{"case":"negative","inputs":{"calibrated_model_probability":0.25,"calibration_state":"CALIBRATED_FOR_DECLARED_CONTEXT","market_implied_probability":0.75},"proof":{"candidate_bits":"bfe0000000000000","exact_difference":{"denominator":"2","numerator":"-1"},"market_bits":"3fe8000000000000","model_bits":"3fd0000000000000","profile":"REPRESENTED_BINARY64_MODEL_MINUS_MARKET_NEAREST_EVEN","raw_json":"-0.5","rounding_midpoints":[{"denominator":"18014398509481984","numerator":"-9007199254740993"},{"denominator":"36028797018963968","numerator":"-18014398509481983"}],"scope":"SOFTWARE_ARITHMETIC_MODEL_ONLY_NO_CALIBRATION_MARKET_SOURCE_OR_TRADING_AUTHORITY","tie":false}},{"case":"equal","inputs":{"calibrated_model_probability":0.4,"calibration_state":"CALIBRATED_FOR_DECLARED_CONTEXT","market_implied_probability":0.4},"proof":{"candidate_bits":"0000000000000000","exact_difference":{"denominator":"1","numerator":"0"},"market_bits":"3fd999999999999a","model_bits":"3fd999999999999a","profile":"REPRESENTED_BINARY64_MODEL_MINUS_MARKET_NEAREST_EVEN","raw_json":"0.0","rounding_midpoints":[{"denominator":"404804506614621236704990693437834614099113299528284236713802716054860679135990693783920767402874248990374155728633623822779617474771586953734026799881477019843034848553132722728933815484186432682479535356945490137124014966849385397236206711298319112681620113024717539104666829230461005064372655017292012526615415482186989568","numerator":"-1"},{"denominator":"404804506614621236704990693437834614099113299528284236713802716054860679135990693783920767402874248990374155728633623822779617474771586953734026799881477019843034848553132722728933815484186432682479535356945490137124014966849385397236206711298319112681620113024717539104666829230461005064372655017292012526615415482186989568","numerator":"1"}],"scope":"SOFTWARE_ARITHMETIC_MODEL_ONLY_NO_CALIBRATION_MARKET_SOURCE_OR_TRADING_AUTHORITY","tie":false}},{"case":"negative_zero","inputs":{"calibrated_model_probability":-0.0,"calibration_state":"CALIBRATED_FOR_DECLARED_CONTEXT","market_implied_probability":0.0},"proof":{"candidate_bits":"8000000000000000","exact_difference":{"denominator":"1","numerator":"0"},"market_bits":"0000000000000000","model_bits":"8000000000000000","profile":"REPRESENTED_BINARY64_MODEL_MINUS_MARKET_NEAREST_EVEN","raw_json":"-0.0","rounding_midpoints":[{"denominator":"404804506614621236704990693437834614099113299528284236713802716054860679135990693783920767402874248990374155728633623822779617474771586953734026799881477019843034848553132722728933815484186432682479535356945490137124014966849385397236206711298319112681620113024717539104666829230461005064372655017292012526615415482186989568","numerator":"-1"},{"denominator":"404804506614621236704990693437834614099113299528284236713802716054860679135990693783920767402874248990374155728633623822779617474771586953734026799881477019843034848553132722728933815484186432682479535356945490137124014966849385397236206711298319112681620113024717539104666829230461005064372655017292012526615415482186989568","numerator":"1"}],"scope":"SOFTWARE_ARITHMETIC_MODEL_ONLY_NO_CALIBRATION_MARKET_SOURCE_OR_TRADING_AUTHORITY","tie":false}},{"case":"positive_minus_negative_zero","inputs":{"calibrated_model_probability":0.0,"calibration_state":"CALIBRATED_FOR_DECLARED_CONTEXT","market_implied_probability":-0.0},"proof":{"candidate_bits":"0000000000000000","exact_difference":{"denominator":"1","numerator":"0"},"market_bits":"8000000000000000","model_bits":"0000000000000000","profile":"REPRESENTED_BINARY64_MODEL_MINUS_MARKET_NEAREST_EVEN","raw_json":"0.0","rounding_midpoints":[{"denominator":"404804506614621236704990693437834614099113299528284236713802716054860679135990693783920767402874248990374155728633623822779617474771586953734026799881477019843034848553132722728933815484186432682479535356945490137124014966849385397236206711298319112681620113024717539104666829230461005064372655017292012526615415482186989568","numerator":"-1"},{"denominator":"404804506614621236704990693437834614099113299528284236713802716054860679135990693783920767402874248990374155728633623822779617474771586953734026799881477019843034848553132722728933815484186432682479535356945490137124014966849385397236206711298319112681620113024717539104666829230461005064372655017292012526615415482186989568","numerator":"1"}],"scope":"SOFTWARE_ARITHMETIC_MODEL_ONLY_NO_CALIBRATION_MARKET_SOURCE_OR_TRADING_AUTHORITY","tie":false}},{"case":"two_negative_zeros","inputs":{"calibrated_model_probability":-0.0,"calibration_state":"CALIBRATED_FOR_DECLARED_CONTEXT","market_implied_probability":-0.0},"proof":{"candidate_bits":"0000000000000000","exact_difference":{"denominator":"1","numerator":"0"},"market_bits":"8000000000000000","model_bits":"8000000000000000","profile":"REPRESENTED_BINARY64_MODEL_MINUS_MARKET_NEAREST_EVEN","raw_json":"0.0","rounding_midpoints":[{"denominator":"404804506614621236704990693437834614099113299528284236713802716054860679135990693783920767402874248990374155728633623822779617474771586953734026799881477019843034848553132722728933815484186432682479535356945490137124014966849385397236206711298319112681620113024717539104666829230461005064372655017292012526615415482186989568","numerator":"-1"},{"denominator":"404804506614621236704990693437834614099113299528284236713802716054860679135990693783920767402874248990374155728633623822779617474771586953734026799881477019843034848553132722728933815484186432682479535356945490137124014966849385397236206711298319112681620113024717539104666829230461005064372655017292012526615415482186989568","numerator":"1"}],"scope":"SOFTWARE_ARITHMETIC_MODEL_ONLY_NO_CALIBRATION_MARKET_SOURCE_OR_TRADING_AUTHORITY","tie":false}},{"case":"positive_subnormal","inputs":{"calibrated_model_probability":5e-324,"calibration_state":"CALIBRATED_FOR_DECLARED_CONTEXT","market_implied_probability":0.0},"proof":{"candidate_bits":"0000000000000001","exact_difference":{"denominator":"202402253307310618352495346718917307049556649764142118356901358027430339567995346891960383701437124495187077864316811911389808737385793476867013399940738509921517424276566361364466907742093216341239767678472745068562007483424692698618103355649159556340810056512358769552333414615230502532186327508646006263307707741093494784","numerator":"1"},"market_bits":"0000000000000000","model_bits":"0000000000000001","profile":"REPRESENTED_BINARY64_MODEL_MINUS_MARKET_NEAREST_EVEN","raw_json":"5e-324","rounding_midpoints":[{"denominator":"404804506614621236704990693437834614099113299528284236713802716054860679135990693783920767402874248990374155728633623822779617474771586953734026799881477019843034848553132722728933815484186432682479535356945490137124014966849385397236206711298319112681620113024717539104666829230461005064372655017292012526615415482186989568","numerator":"1"},{"denominator":"404804506614621236704990693437834614099113299528284236713802716054860679135990693783920767402874248990374155728633623822779617474771586953734026799881477019843034848553132722728933815484186432682479535356945490137124014966849385397236206711298319112681620113024717539104666829230461005064372655017292012526615415482186989568","numerator":"3"}],"scope":"SOFTWARE_ARITHMETIC_MODEL_ONLY_NO_CALIBRATION_MARKET_SOURCE_OR_TRADING_AUTHORITY","tie":false}},{"case":"negative_subnormal","inputs":{"calibrated_model_probability":0.0,"calibration_state":"CALIBRATED_FOR_DECLARED_CONTEXT","market_implied_probability":5e-324},"proof":{"candidate_bits":"8000000000000001","exact_difference":{"denominator":"202402253307310618352495346718917307049556649764142118356901358027430339567995346891960383701437124495187077864316811911389808737385793476867013399940738509921517424276566361364466907742093216341239767678472745068562007483424692698618103355649159556340810056512358769552333414615230502532186327508646006263307707741093494784","numerator":"-1"},"market_bits":"0000000000000001","model_bits":"0000000000000000","profile":"REPRESENTED_BINARY64_MODEL_MINUS_MARKET_NEAREST_EVEN","raw_json":"-5e-324","rounding_midpoints":[{"denominator":"404804506614621236704990693437834614099113299528284236713802716054860679135990693783920767402874248990374155728633623822779617474771586953734026799881477019843034848553132722728933815484186432682479535356945490137124014966849385397236206711298319112681620113024717539104666829230461005064372655017292012526615415482186989568","numerator":"-3"},{"denominator":"404804506614621236704990693437834614099113299528284236713802716054860679135990693783920767402874248990374155728633623822779617474771586953734026799881477019843034848553132722728933815484186432682479535356945490137124014966849385397236206711298319112681620113024717539104666829230461005064372655017292012526615415482186989568","numerator":"-1"}],"scope":"SOFTWARE_ARITHMETIC_MODEL_ONLY_NO_CALIBRATION_MARKET_SOURCE_OR_TRADING_AUTHORITY","tie":false}},{"case":"tie_to_even","inputs":{"calibrated_model_probability":1.0,"calibration_state":"CALIBRATED_FOR_DECLARED_CONTEXT","market_implied_probability":0.2},"proof":{"candidate_bits":"3fe999999999999a","exact_difference":{"denominator":"18014398509481984","numerator":"14411518807585587"},"market_bits":"3fc999999999999a","model_bits":"3ff0000000000000","profile":"REPRESENTED_BINARY64_MODEL_MINUS_MARKET_NEAREST_EVEN","raw_json":"0.8","rounding_midpoints":[{"denominator":"18014398509481984","numerator":"14411518807585587"},{"denominator":"18014398509481984","numerator":"14411518807585589"}],"scope":"SOFTWARE_ARITHMETIC_MODEL_ONLY_NO_CALIBRATION_MARKET_SOURCE_OR_TRADING_AUTHORITY","tie":true}},{"case":"opposite_tie","inputs":{"calibrated_model_probability":0.2,"calibration_state":"CALIBRATED_FOR_DECLARED_CONTEXT","market_implied_probability":1.0},"proof":{"candidate_bits":"bfe999999999999a","exact_difference":{"denominator":"18014398509481984","numerator":"-14411518807585587"},"market_bits":"3ff0000000000000","model_bits":"3fc999999999999a","profile":"REPRESENTED_BINARY64_MODEL_MINUS_MARKET_NEAREST_EVEN","raw_json":"-0.8","rounding_midpoints":[{"denominator":"18014398509481984","numerator":"-14411518807585589"},{"denominator":"18014398509481984","numerator":"-14411518807585587"}],"scope":"SOFTWARE_ARITHMETIC_MODEL_ONLY_NO_CALIBRATION_MARKET_SOURCE_OR_TRADING_AUTHORITY","tie":true}},{"case":"tiny_subtraction_rounds_to_half","inputs":{"calibrated_model_probability":0.5,"calibration_state":"CALIBRATED_FOR_DECLARED_CONTEXT","market_implied_probability":5e-324},"proof":{"candidate_bits":"3fe0000000000000","exact_difference":{"denominator":"202402253307310618352495346718917307049556649764142118356901358027430339567995346891960383701437124495187077864316811911389808737385793476867013399940738509921517424276566361364466907742093216341239767678472745068562007483424692698618103355649159556340810056512358769552333414615230502532186327508646006263307707741093494784","numerator":"101201126653655309176247673359458653524778324882071059178450679013715169783997673445980191850718562247593538932158405955694904368692896738433506699970369254960758712138283180682233453871046608170619883839236372534281003741712346349309051677824579778170405028256179384776166707307615251266093163754323003131653853870546747391"},"market_bits":"0000000000000001","model_bits":"3fe0000000000000","profile":"REPRESENTED_BINARY64_MODEL_MINUS_MARKET_NEAREST_EVEN","raw_json":"0.5","rounding_midpoints":[{"denominator":"36028797018963968","numerator":"18014398509481983"},{"denominator":"18014398509481984","numerator":"9007199254740993"}],"scope":"SOFTWARE_ARITHMETIC_MODEL_ONLY_NO_CALIBRATION_MARKET_SOURCE_OR_TRADING_AUTHORITY","tie":false}},{"case":"upper_bound","inputs":{"calibrated_model_probability":1.0,"calibration_state":"CALIBRATED_FOR_DECLARED_CONTEXT","market_implied_probability":0.0},"proof":{"candidate_bits":"3ff0000000000000","exact_difference":{"denominator":"1","numerator":"1"},"market_bits":"0000000000000000","model_bits":"3ff0000000000000","profile":"REPRESENTED_BINARY64_MODEL_MINUS_MARKET_NEAREST_EVEN","raw_json":"1.0","rounding_midpoints":[{"denominator":"18014398509481984","numerator":"18014398509481983"},{"denominator":"9007199254740992","numerator":"9007199254740993"}],"scope":"SOFTWARE_ARITHMETIC_MODEL_ONLY_NO_CALIBRATION_MARKET_SOURCE_OR_TRADING_AUTHORITY","tie":false}},{"case":"lower_bound","inputs":{"calibrated_model_probability":0.0,"calibration_state":"CALIBRATED_FOR_DECLARED_CONTEXT","market_implied_probability":1.0},"proof":{"candidate_bits":"bff0000000000000","exact_difference":{"denominator":"1","numerator":"-1"},"market_bits":"3ff0000000000000","model_bits":"0000000000000000","profile":"REPRESENTED_BINARY64_MODEL_MINUS_MARKET_NEAREST_EVEN","raw_json":"-1.0","rounding_midpoints":[{"denominator":"9007199254740992","numerator":"-9007199254740993"},{"denominator":"18014398509481984","numerator":"-18014398509481983"}],"scope":"SOFTWARE_ARITHMETIC_MODEL_ONLY_NO_CALIBRATION_MARKET_SOURCE_OR_TRADING_AUTHORITY","tie":false}}]')
    bits = lambda value:struct.pack(">d",value).hex()
    def run(case, work, *, inputs=None, raw=None, expected=None, projected=None):
        original = case["proof"]["raw_json"].encode("utf-8")
        return IndependentEvidenceReviewV1._bounded_review_probability_edge_v1(
            deterministic_json(case["inputs"] if inputs is None else inputs).encode("utf-8"),
            original if raw is None else deterministic_json(raw).encode("utf-8"),
            original if expected is None else deterministic_json(expected).encode("utf-8"),
            json.loads(original) if projected is None else projected, work=work)
    def forbidden(*args, **kwargs):raise AssertionError("edge review called the original formula")
    positives=[]
    with ExitStack() as stack:
        for name in ("compute_math_02_v34","compute_math_02_probability_edge"):
            stack.enter_context(patch.object(formulas,name,forbidden))
        for case in cases:
            work=_EvidenceNumericalWorkV1(limits,retained_input_capacity=0)
            proof=run(case,work);summary=proof["summary"];reference=case["proof"]
            for name in ("model_bits","market_bits","candidate_bits","exact_difference"):
                assert summary[name]==reference[name]
            assert summary["lower_midpoint"]==reference["rounding_midpoints"][0]
            assert summary["upper_midpoint"]==reference["rounding_midpoints"][1]
            assert summary["tie_flag"]==int(reference["tie"])
            assert summary["original_raw_json"]==summary["preregistered_raw_json"]==reference["raw_json"]
            assert summary["typed_input_json"]==deterministic_json(case["inputs"])
            assert work.state=="OPEN" and work._bootstrap_invocations==[]
            consumed=dict(work.consumed)
            assert all(consumed[name]==0 for name in ("decimal_constructions","retained_decimal_inputs","random_draws","log_series_terms","square_roots"))
            assert consumed["serialized_bytes"]==len(deterministic_json(summary).encode())+len(deterministic_json(proof).encode())
            positives.append(dict(case=case["case"],proof=proof,consumed=consumed))
    base=cases[0];negative_zero=next(case for case in cases if case["case"]=="negative_zero")
    denials=[]
    for name,case,arguments,overrides in (
        ("uncalibrated",base,dict(inputs=dict(base["inputs"],calibration_state="UNCALIBRATED")),{}),
        ("boolean_model",base,dict(inputs=dict(base["inputs"],calibrated_model_probability=True)),{}),
        ("integer_model",base,dict(inputs=dict(base["inputs"],calibrated_model_probability=1)),{}),
        ("model_above_one",base,dict(inputs=dict(base["inputs"],calibrated_model_probability=1.5)),{}),
        ("negative_market",base,dict(inputs=dict(base["inputs"],market_implied_probability=-0.25)),{}),
        ("foreign_input",base,dict(inputs=dict(base["inputs"],calibration_valid=True)),{}),
        ("wrong_raw",base,dict(raw=-0.5),{}),
        ("wrong_expectation",base,dict(expected=-0.5),{}),
        ("wrong_projection",base,dict(projected=-0.5),{}),
        ("integer_projection",base,dict(projected=0),{}),
        ("signed_zero_raw",negative_zero,dict(raw=0.0),{}),
        ("signed_zero_expected",negative_zero,dict(expected=0.0),{}),
        ("signed_zero_projected",negative_zero,dict(projected=0.0),{}),
        ("zero_input_budget",base,{},dict(max_input_bits=0)),
        ("small_input_budget",base,{},dict(max_input_bits=1)),
        ("small_work_budget",base,{},dict(max_work_bits=100)),
        ("input_byte_budget",base,{},dict(max_serialized_bytes=16)),
        ("complete_byte_preflight",base,{},dict(max_serialized_bytes=16000)),
    ):
        work=_EvidenceNumericalWorkV1(dict(limits,**overrides),retained_input_capacity=0)
        with pytest.raises(ComputationControlPlaneError) as caught:run(case,work,**arguments)
        before=dict(work.consumed)
        assert work.state=="FAILED" and work._bootstrap_invocations==[]
        assert all(before[key]==0 for key in ("decimal_constructions","retained_decimal_inputs","random_draws","log_series_terms","square_roots"))
        with pytest.raises(ComputationControlPlaneError):run(base,work)
        assert dict(work.consumed)==before
        denials.append(dict(case=name,diagnostic=str(caught.value),failure=work.failure,consumed=before,retry_denied=True))
    work=_EvidenceNumericalWorkV1(limits,retained_input_capacity=0);completed=[]
    for ordinal in range(64):
        before=dict(work.consumed)
        try:proof=run(base,work)
        except ComputationControlPlaneError as error:
            assert work.failure=="LP03_EDGE_REVIEW_COMPLETE_BYTES_EXHAUSTED" and dict(work.consumed)==before
            denials.append(dict(case="cumulative_original_allowance",diagnostic=str(error),failure=work.failure,
                consumed=before,completed=len(completed),retained_first_proof=completed[0]))
            break
        completed.append(proof)
    else:raise AssertionError("finite original edge allowance did not exhaust")
    assert len(completed)>1 and work._bootstrap_invocations==[]
    assert work.consumed["serialized_bytes"]==len(completed)*positives[0]["consumed"]["serialized_bytes"]
    print("LP03_EDGE_PURE_QUALIFICATION="+deterministic_json(dict(
        scope="BOUNDED_BINARY64_EDGE_MODEL_ONLY_NO_CALIBRATION_MARKET_SOURCE_OR_NATIVE_AUTHORITY",positives=positives,denials=denials)))


def _assert_lp03_spa_ordered_model_proof():
    import json
    import math
    import random
    from contextlib import ExitStack
    from dataclasses import replace
    from types import MappingProxyType
    from unittest.mock import patch
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane import implementation_registry as formulas
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.evidence import IndependentEvidenceReviewV1
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.evidence_execution import _worker_environment_v1
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.parameter_policy import _EvidenceNumericalWorkV1
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import ComputationControlPlaneError
    limits = dict(max_input_bits=4096, max_work_bits=65536, max_serialized_bytes=65536)
    environment = _worker_environment_v1()
    # Independent rational/MT model literals, fixed before QTT execution.
    cases = json.loads('[{"case":"positive_variance_n4","cell_candidates":["3ff0000000000000","3fd0000000000000","3ff0000000000000","3fd0000000000000","0000000000000000","3fe0000000000000","0000000000000000","bfe0000000000000","3fe0000000000000","0000000000000000","3fd0000000000000","0000000000000000","3fd0000000000000","3fe0000000000000","3fc0000000000000","3fd0000000000000","3fe8000000000000","3fe0000000000000","3fe0000000000000","3fd8000000000000","3fd0000000000000","3fe0000000000000","3fc0000000000000","3fa0000000000000","3fda000000000000","0000000000000000","0000000000000000","8000000000000000","0000000000000000","0000000000000000","3fea000000000000","0000000000000000","3fc0000000000000","3fe0000000000000","3fe0000000000000","3fe0000000000000","3fd0000000000000","3fc0000000000000","3fe0000000000000","3fe0000000000000","3fd0000000000000","3fc0000000000000","3fd0000000000000","0000000000000000","bfd0000000000000","bfd0000000000000","bfb0000000000000","3fe0000000000000","bfa0000000000000","3fb8000000000000","3fe8000000000000","3fd0000000000000","3fe0000000000000","3fc0000000000000","3fa0000000000000","3fe8000000000000","3fe0000000000000","3fe0000000000000","3fd8000000000000","3fda000000000000","8000000000000000","0000000000000000","0000000000000000","3fea000000000000","0000000000000000","3fb8000000000000","3f98000000000000","3fa8000000000000","3ff62e42fefa39ef","3fd4e7936217083f","3f8f5b5d13228c5e","3fbfad43949347c4","4000000000000000","3fe0000000000000","3fd3988e1409212e","3ffa20bd700c2c3f","3fe0000000000000","4000000000000000","0000000000000000","0000000000000000","bfd0000000000000","bfe0000000000000","3fd3988e1409212e","bffa20bd700c2c3f","3fe0000000000000"],"consistency_threshold_bits":["bfbfad43949347c4"],"draws":[{"comparison":"4","disposition":"REJECTED","method":"GETRANDBITS","ordinal":0,"position":0,"replicate":0,"value":6,"width":3},{"comparison":"4","disposition":"SELECTED","method":"GETRANDBITS","ordinal":1,"position":0,"replicate":0,"value":3,"width":3},{"comparison":"3fe0000000000000","disposition":"CONTINUE","method":"RANDOM_U53","ordinal":2,"position":1,"replicate":0,"value":6827046333291546,"width":53},{"comparison":"3fe0000000000000","disposition":"RESTART","method":"RANDOM_U53","ordinal":3,"position":2,"replicate":0,"value":3788172029424828,"width":53},{"comparison":"4","disposition":"SELECTED","method":"GETRANDBITS","ordinal":4,"position":2,"replicate":0,"value":2,"width":3},{"comparison":"3fe0000000000000","disposition":"CONTINUE","method":"RANDOM_U53","ordinal":5,"position":3,"replicate":0,"value":8696134604917657,"width":53}],"indices":[[3,0,2,3]],"inputs":{"alpha":0.5,"expected_block_length":2.0,"loss_differentials":[[0.25],[0.75],[0.25],[-0.25]],"recenter_variant":"HANSEN_CONSISTENT_LOG_LOG_THRESHOLD","replicates":1,"seed":0,"sign_convention":"BENCHMARK_LOSS_MINUS_CANDIDATE_LOSS_POSITIVE_IS_BETTER"},"log_certificates":[{"candidate":"3ff62e42fefa39ef","input_bits":"4010000000000000","position":68,"terms":64},{"candidate":"3fd4e7936217083f","input_bits":"3ff62e42fefa39ef","position":69,"terms":16}],"oriented_matrix_bits":[["3fd0000000000000"],["3fe8000000000000"],["3fd0000000000000"],["bfd0000000000000"]],"raw":{"candidate_means":[0.25],"consistent_valid_columns":[true],"long_run_variances":[0.09375],"p_value":0.5,"recenter_variant":"HANSEN_CONSISTENT_LOG_LOG_THRESHOLD","reject":true,"simulated_statistics":[0.0],"statistic":1.6329931618554523},"raw_json":"{\\"candidate_means\\":[0.25],\\"consistent_valid_columns\\":[true],\\"long_run_variances\\":[0.09375],\\"p_value\\":0.5,\\"recenter_variant\\":\\"HANSEN_CONSISTENT_LOG_LOG_THRESHOLD\\",\\"reject\\":true,\\"simulated_statistics\\":[0.0],\\"statistic\\":1.6329931618554523}","sqrt_cells":5},{"case":"positive_variance_n3","cell_candidates":["3fe8000000000000","3fd0000000000000","3fe8000000000000","3fd0000000000000","0000000000000000","3fe0000000000000","bfe0000000000000","3fe0000000000000","0000000000000000","3fd0000000000000","3fd0000000000000","3fe0000000000000","3fc5555555555555","3fd5555555555555","3fe5555555555556","3fe0000000000000","3fe0000000000000","3fd5555555555556","3fd5555555555555","3fe0000000000000","3fd0000000000000","3fb5555555555555","3fdaaaaaaaaaaaab","0000000000000000","bfd0000000000000","bfd0000000000000","bfb5555555555555","3feaaaaaaaaaaaab","bfb1c71c71c71c72","3fb8e38e38e38e38","3fe5555555555555","3fd5555555555556","3fe0000000000000","3fd0000000000000","3fb5555555555556","3fe5555555555555","3fe0000000000000","3fe0000000000000","3fd5555555555555","3fdaaaaaaaaaaaaa","8000000000000000","0000000000000000","0000000000000000","3feaaaaaaaaaaaaa","0000000000000000","3fb8e38e38e38e38","3fa097b425ed097b","3fb097b425ed097b","3ff193ea7aad030b","3fb81384b7dfa22b","3f78f7cc010dd794","3fb3fcb7bb78b12c","3ffbb67ae8584caa","3fdbb67ae8584caa","3fd3f49c0b9ad4db","3ff6383d1afc0fc3","3fe0000000000000","3ffbb67ae8584caa","3ff4000000000000","3fdaaaaaaaaaaaab","3fc5555555555556","3fd279a74590331d","3fd3f49c0b9ad4db","3feda05179501506","3fe0000000000000"],"consistency_threshold_bits":["bfb3fcb7bb78b12c"],"draws":[{"comparison":"3","disposition":"REJECTED","method":"GETRANDBITS","ordinal":0,"position":0,"replicate":0,"value":3,"width":2},{"comparison":"3","disposition":"SELECTED","method":"GETRANDBITS","ordinal":1,"position":0,"replicate":0,"value":1,"width":2},{"comparison":"3fe0000000000000","disposition":"CONTINUE","method":"RANDOM_U53","ordinal":2,"position":1,"replicate":0,"value":6827046333291546,"width":53},{"comparison":"3fe0000000000000","disposition":"RESTART","method":"RANDOM_U53","ordinal":3,"position":2,"replicate":0,"value":3788172029424828,"width":53},{"comparison":"3","disposition":"SELECTED","method":"GETRANDBITS","ordinal":4,"position":2,"replicate":0,"value":1,"width":2}],"indices":[[1,2,1]],"inputs":{"alpha":0.5,"expected_block_length":2.0,"loss_differentials":[[0.25],[0.75],[-0.25]],"recenter_variant":"HANSEN_CONSISTENT_LOG_LOG_THRESHOLD","replicates":1,"seed":0,"sign_convention":"BENCHMARK_LOSS_MINUS_CANDIDATE_LOSS_POSITIVE_IS_BETTER"},"log_certificates":[{"candidate":"3ff193ea7aad030b","input_bits":"4008000000000000","position":48,"terms":64},{"candidate":"3fb81384b7dfa22b","input_bits":"3ff193ea7aad030b","position":49,"terms":16}],"oriented_matrix_bits":[["3fd0000000000000"],["3fe8000000000000"],["bfd0000000000000"]],"raw":{"candidate_means":[0.25],"consistent_valid_columns":[true],"long_run_variances":[0.09722222222222221],"p_value":0.5,"recenter_variant":"HANSEN_CONSISTENT_LOG_LOG_THRESHOLD","reject":true,"simulated_statistics":[0.9258200997725516],"statistic":1.3887301496588271},"raw_json":"{\\"candidate_means\\":[0.25],\\"consistent_valid_columns\\":[true],\\"long_run_variances\\":[0.09722222222222221],\\"p_value\\":0.5,\\"recenter_variant\\":\\"HANSEN_CONSISTENT_LOG_LOG_THRESHOLD\\",\\"reject\\":true,\\"simulated_statistics\\":[0.9258200997725516],\\"statistic\\":1.3887301496588271}","sqrt_cells":5},{"case":"all_zero","cell_candidates":["0000000000000000","0000000000000000","0000000000000000","0000000000000000","0000000000000000","8000000000000000","0000000000000000","3ff0000000000000","0000000000000000","0000000000000000","0000000000000000","0000000000000000","0000000000000000","3fd5555555555555","3fe5555555555556","0000000000000000","0000000000000000","0000000000000000","3fd5555555555555","0000000000000000","0000000000000000","0000000000000000","0000000000000000","8000000000000000","8000000000000000","0000000000000000","0000000000000000","0000000000000000","0000000000000000","0000000000000000","3fe5555555555555","3fd5555555555556","0000000000000000","0000000000000000","0000000000000000","3fe5555555555555","0000000000000000","0000000000000000","0000000000000000","0000000000000000","0000000000000000","0000000000000000","0000000000000000","0000000000000000","0000000000000000","0000000000000000","3ff0000000000000","3ff0000000000000"],"consistency_threshold_bits":[null],"draws":[{"comparison":"3","disposition":"REJECTED","method":"GETRANDBITS","ordinal":0,"position":0,"replicate":0,"value":3,"width":2},{"comparison":"3","disposition":"SELECTED","method":"GETRANDBITS","ordinal":1,"position":0,"replicate":0,"value":1,"width":2},{"comparison":"3ff0000000000000","disposition":"RESTART","method":"RANDOM_U53","ordinal":2,"position":1,"replicate":0,"value":6827046333291546,"width":53},{"comparison":"3","disposition":"SELECTED","method":"GETRANDBITS","ordinal":3,"position":1,"replicate":0,"value":1,"width":2},{"comparison":"3ff0000000000000","disposition":"RESTART","method":"RANDOM_U53","ordinal":4,"position":2,"replicate":0,"value":364650860978552,"width":53},{"comparison":"3","disposition":"REJECTED","method":"GETRANDBITS","ordinal":5,"position":2,"replicate":0,"value":3,"width":2},{"comparison":"3","disposition":"SELECTED","method":"GETRANDBITS","ordinal":6,"position":2,"replicate":0,"value":2,"width":2}],"indices":[[1,1,2]],"inputs":{"alpha":0.5,"expected_block_length":1.0,"loss_differentials":[[0.0],[-0.0],[0.0]],"recenter_variant":"HANSEN_CONSISTENT_LOG_LOG_THRESHOLD","replicates":1,"seed":0,"sign_convention":"BENCHMARK_LOSS_MINUS_CANDIDATE_LOSS_POSITIVE_IS_BETTER"},"log_certificates":[],"oriented_matrix_bits":[["0000000000000000"],["8000000000000000"],["0000000000000000"]],"raw":{"candidate_means":[0.0],"consistent_valid_columns":[false],"long_run_variances":[0.0],"p_value":1.0,"recenter_variant":"HANSEN_CONSISTENT_LOG_LOG_THRESHOLD","reject":false,"simulated_statistics":[0.0],"statistic":0.0},"raw_json":"{\\"candidate_means\\":[0.0],\\"consistent_valid_columns\\":[false],\\"long_run_variances\\":[0.0],\\"p_value\\":1.0,\\"recenter_variant\\":\\"HANSEN_CONSISTENT_LOG_LOG_THRESHOLD\\",\\"reject\\":false,\\"simulated_statistics\\":[0.0],\\"statistic\\":0.0}","sqrt_cells":0},{"case":"constant_negative","cell_candidates":["bfe8000000000000","bfd0000000000000","bfe8000000000000","bfd0000000000000","0000000000000000","0000000000000000","0000000000000000","3fe0000000000000","0000000000000000","0000000000000000","0000000000000000","0000000000000000","0000000000000000","3fd5555555555555","3fe5555555555556","3fe0000000000000","3fe0000000000000","3fd5555555555556","3fd5555555555555","3fe0000000000000","3fd0000000000000","3fb5555555555555","3fdaaaaaaaaaaaab","0000000000000000","0000000000000000","0000000000000000","0000000000000000","3feaaaaaaaaaaaab","0000000000000000","0000000000000000","3fe5555555555555","3fd5555555555556","3fe0000000000000","3fd0000000000000","3fb5555555555556","3fe5555555555555","3fe0000000000000","3fe0000000000000","3fd5555555555555","3fdaaaaaaaaaaaaa","0000000000000000","0000000000000000","0000000000000000","3feaaaaaaaaaaaaa","0000000000000000","0000000000000000","3fe0000000000000","3fe0000000000000","3ff0000000000000"],"consistency_threshold_bits":[null],"draws":[{"comparison":"3","disposition":"SELECTED","method":"GETRANDBITS","ordinal":0,"position":0,"replicate":0,"value":0,"width":2},{"comparison":"3fe0000000000000","disposition":"CONTINUE","method":"RANDOM_U53","ordinal":1,"position":1,"replicate":0,"value":5126932717094315,"width":53},{"comparison":"3fe0000000000000","disposition":"CONTINUE","method":"RANDOM_U53","ordinal":2,"position":2,"replicate":0,"value":7226161261058799,"width":53},{"comparison":"3","disposition":"SELECTED","method":"GETRANDBITS","ordinal":3,"position":0,"replicate":1,"value":0,"width":2},{"comparison":"3fe0000000000000","disposition":"RESTART","method":"RANDOM_U53","ordinal":4,"position":1,"replicate":1,"value":2297457538547630,"width":53},{"comparison":"3","disposition":"SELECTED","method":"GETRANDBITS","ordinal":5,"position":1,"replicate":1,"value":1,"width":2},{"comparison":"3fe0000000000000","disposition":"CONTINUE","method":"RANDOM_U53","ordinal":6,"position":2,"replicate":1,"value":6854140366702434,"width":53}],"indices":[[0,1,2],[0,1,2]],"inputs":{"alpha":0.5,"expected_block_length":2.0,"loss_differentials":[[-0.25],[-0.25],[-0.25]],"recenter_variant":"HANSEN_CONSISTENT_LOG_LOG_THRESHOLD","replicates":2,"seed":1,"sign_convention":"BENCHMARK_LOSS_MINUS_CANDIDATE_LOSS_POSITIVE_IS_BETTER"},"log_certificates":[],"oriented_matrix_bits":[["bfd0000000000000"],["bfd0000000000000"],["bfd0000000000000"]],"raw":{"candidate_means":[-0.25],"consistent_valid_columns":[false],"long_run_variances":[0.0],"p_value":1.0,"recenter_variant":"HANSEN_CONSISTENT_LOG_LOG_THRESHOLD","reject":false,"simulated_statistics":[0.0,0.0],"statistic":0.0},"raw_json":"{\\"candidate_means\\":[-0.25],\\"consistent_valid_columns\\":[false],\\"long_run_variances\\":[0.0],\\"p_value\\":1.0,\\"recenter_variant\\":\\"HANSEN_CONSISTENT_LOG_LOG_THRESHOLD\\",\\"reject\\":false,\\"simulated_statistics\\":[0.0,0.0],\\"statistic\\":0.0}","sqrt_cells":0},{"case":"complete_two_candidates","cell_candidates":["3fe8000000000000","3fd0000000000000","bfe8000000000000","bfd0000000000000","3fe8000000000000","3fd0000000000000","0000000000000000","3fe0000000000000","bfe0000000000000","3fe0000000000000","0000000000000000","3fd0000000000000","3fd0000000000000","3fe0000000000000","3fc5555555555555","3fd5555555555555","3fe5555555555556","3fe0000000000000","3fe0000000000000","3fd5555555555556","3fd5555555555555","3fe0000000000000","3fd0000000000000","3fb5555555555555","3fdaaaaaaaaaaaab","0000000000000000","bfd0000000000000","bfd0000000000000","bfb5555555555555","3feaaaaaaaaaaaab","bfb1c71c71c71c72","3fb8e38e38e38e38","3fe5555555555555","3fd5555555555556","3fe0000000000000","3fd0000000000000","3fb5555555555556","3fe5555555555555","3fe0000000000000","3fe0000000000000","3fd5555555555555","3fdaaaaaaaaaaaaa","8000000000000000","0000000000000000","0000000000000000","3feaaaaaaaaaaaaa","0000000000000000","3fb8e38e38e38e38","bfe8000000000000","bfd0000000000000","0000000000000000","3fe0000000000000","bfe0000000000000","3fe0000000000000","0000000000000000","3fd0000000000000","3fd0000000000000","3fe0000000000000","3fc5555555555555","3fd5555555555555","3fe5555555555556","3fe0000000000000","3fe0000000000000","3fd5555555555556","3fd5555555555555","3fe0000000000000","3fd0000000000000","3fb5555555555555","3fdaaaaaaaaaaaab","0000000000000000","bfd0000000000000","bfd0000000000000","bfb5555555555555","3feaaaaaaaaaaaab","bfb1c71c71c71c72","3fb8e38e38e38e38","3fe5555555555555","3fd5555555555556","3fe0000000000000","3fd0000000000000","3fb5555555555556","3fe5555555555555","3fe0000000000000","3fe0000000000000","3fd5555555555555","3fdaaaaaaaaaaaaa","8000000000000000","0000000000000000","0000000000000000","3feaaaaaaaaaaaaa","0000000000000000","3fb8e38e38e38e38","3fa097b425ed097b","3fb097b425ed097b","3ff193ea7aad030b","3fb81384b7dfa22b","3f78f7cc010dd794","3fb3fcb7bb78b12c","3ffbb67ae8584caa","3fdbb67ae8584caa","3fd3f49c0b9ad4db","3ff6383d1afc0fc3","3fa097b425ed097b","3fb097b425ed097b","3ff193ea7aad030b","3fb81384b7dfa22b","3f78f7cc010dd794","3fb3fcb7bb78b12c","3ffbb67ae8584caa","bfdbb67ae8584caa","3fd3f49c0b9ad4db","bff6383d1afc0fc3","3fe0000000000000","3ffbb67ae8584caa","3fe8000000000000","3fd0000000000000","0000000000000000","0000000000000000","3fd3f49c0b9ad4db","0000000000000000","3ffbb67ae8584caa","bfe8000000000000","bfd0000000000000","bfd0000000000000","bfdbb67ae8584caa","3fd3f49c0b9ad4db","bff6383d1afc0fc3","3fe0000000000000"],"consistency_threshold_bits":["bfb3fcb7bb78b12c","bfb3fcb7bb78b12c"],"draws":[{"comparison":"3","disposition":"SELECTED","method":"GETRANDBITS","ordinal":0,"position":0,"replicate":0,"value":1,"width":2},{"comparison":"3fe0000000000000","disposition":"CONTINUE","method":"RANDOM_U53","ordinal":1,"position":1,"replicate":0,"value":8537612169672756,"width":53},{"comparison":"3fe0000000000000","disposition":"RESTART","method":"RANDOM_U53","ordinal":2,"position":2,"replicate":0,"value":3556253902737041,"width":53},{"comparison":"3","disposition":"SELECTED","method":"GETRANDBITS","ordinal":3,"position":2,"replicate":0,"value":0,"width":2}],"indices":[[1,2,0]],"inputs":{"alpha":0.5,"expected_block_length":2.0,"loss_differentials":[[0.25,-0.25],[0.75,0.25],[-0.25,-0.75]],"recenter_variant":"HANSEN_CONSISTENT_LOG_LOG_THRESHOLD","replicates":1,"seed":7,"sign_convention":"BENCHMARK_LOSS_MINUS_CANDIDATE_LOSS_POSITIVE_IS_BETTER"},"log_certificates":[{"candidate":"3ff193ea7aad030b","input_bits":"4008000000000000","position":94,"terms":64},{"candidate":"3fb81384b7dfa22b","input_bits":"3ff193ea7aad030b","position":95,"terms":16},{"candidate":"3ff193ea7aad030b","input_bits":"4008000000000000","position":104,"terms":64},{"candidate":"3fb81384b7dfa22b","input_bits":"3ff193ea7aad030b","position":105,"terms":16}],"oriented_matrix_bits":[["3fd0000000000000","bfd0000000000000"],["3fe8000000000000","3fd0000000000000"],["bfd0000000000000","bfe8000000000000"]],"raw":{"candidate_means":[0.25,-0.25],"consistent_valid_columns":[true,false],"long_run_variances":[0.09722222222222221,0.09722222222222221],"p_value":0.5,"recenter_variant":"HANSEN_CONSISTENT_LOG_LOG_THRESHOLD","reject":true,"simulated_statistics":[0.0],"statistic":1.3887301496588271},"raw_json":"{\\"candidate_means\\":[0.25,-0.25],\\"consistent_valid_columns\\":[true,false],\\"long_run_variances\\":[0.09722222222222221,0.09722222222222221],\\"p_value\\":0.5,\\"recenter_variant\\":\\"HANSEN_CONSISTENT_LOG_LOG_THRESHOLD\\",\\"reject\\":true,\\"simulated_statistics\\":[0.0],\\"statistic\\":1.3887301496588271}","sqrt_cells":10},{"case":"opposite_sign","cell_candidates":["3fe8000000000000","3fd0000000000000","3fe8000000000000","3fd0000000000000","0000000000000000","3fe0000000000000","bfe0000000000000","3fe0000000000000","0000000000000000","3fd0000000000000","3fd0000000000000","3fe0000000000000","3fc5555555555555","3fd5555555555555","3fe5555555555556","3fe0000000000000","3fe0000000000000","3fd5555555555556","3fd5555555555555","3fe0000000000000","3fd0000000000000","3fb5555555555555","3fdaaaaaaaaaaaab","0000000000000000","bfd0000000000000","bfd0000000000000","bfb5555555555555","3feaaaaaaaaaaaab","bfb1c71c71c71c72","3fb8e38e38e38e38","3fe5555555555555","3fd5555555555556","3fe0000000000000","3fd0000000000000","3fb5555555555556","3fe5555555555555","3fe0000000000000","3fe0000000000000","3fd5555555555555","3fdaaaaaaaaaaaaa","8000000000000000","0000000000000000","0000000000000000","3feaaaaaaaaaaaaa","0000000000000000","3fb8e38e38e38e38","3fa097b425ed097b","3fb097b425ed097b","3ff193ea7aad030b","3fb81384b7dfa22b","3f78f7cc010dd794","3fb3fcb7bb78b12c","3ffbb67ae8584caa","3fdbb67ae8584caa","3fd3f49c0b9ad4db","3ff6383d1afc0fc3","3fe0000000000000","3ffbb67ae8584caa","3ff4000000000000","3fdaaaaaaaaaaaab","3fc5555555555556","3fd279a74590331d","3fd3f49c0b9ad4db","3feda05179501506","3fe0000000000000"],"consistency_threshold_bits":["bfb3fcb7bb78b12c"],"draws":[{"comparison":"3","disposition":"REJECTED","method":"GETRANDBITS","ordinal":0,"position":0,"replicate":0,"value":3,"width":2},{"comparison":"3","disposition":"SELECTED","method":"GETRANDBITS","ordinal":1,"position":0,"replicate":0,"value":1,"width":2},{"comparison":"3fe0000000000000","disposition":"CONTINUE","method":"RANDOM_U53","ordinal":2,"position":1,"replicate":0,"value":6827046333291546,"width":53},{"comparison":"3fe0000000000000","disposition":"RESTART","method":"RANDOM_U53","ordinal":3,"position":2,"replicate":0,"value":3788172029424828,"width":53},{"comparison":"3","disposition":"SELECTED","method":"GETRANDBITS","ordinal":4,"position":2,"replicate":0,"value":1,"width":2}],"indices":[[1,2,1]],"inputs":{"alpha":0.5,"expected_block_length":2.0,"loss_differentials":[[-0.25],[-0.75],[0.25]],"recenter_variant":"HANSEN_CONSISTENT_LOG_LOG_THRESHOLD","replicates":1,"seed":0,"sign_convention":"CANDIDATE_LOSS_MINUS_BENCHMARK_LOSS_NEGATED_TO_POSITIVE_IS_BETTER"},"log_certificates":[{"candidate":"3ff193ea7aad030b","input_bits":"4008000000000000","position":48,"terms":64},{"candidate":"3fb81384b7dfa22b","input_bits":"3ff193ea7aad030b","position":49,"terms":16}],"oriented_matrix_bits":[["3fd0000000000000"],["3fe8000000000000"],["bfd0000000000000"]],"raw":{"candidate_means":[0.25],"consistent_valid_columns":[true],"long_run_variances":[0.09722222222222221],"p_value":0.5,"recenter_variant":"HANSEN_CONSISTENT_LOG_LOG_THRESHOLD","reject":true,"simulated_statistics":[0.9258200997725516],"statistic":1.3887301496588271},"raw_json":"{\\"candidate_means\\":[0.25],\\"consistent_valid_columns\\":[true],\\"long_run_variances\\":[0.09722222222222221],\\"p_value\\":0.5,\\"recenter_variant\\":\\"HANSEN_CONSISTENT_LOG_LOG_THRESHOLD\\",\\"reject\\":true,\\"simulated_statistics\\":[0.9258200997725516],\\"statistic\\":1.3887301496588271}","sqrt_cells":5},{"case":"subnormal_variance","cell_candidates":["0000000000000000","0000000000000000","0000000000000000","0000000000000000","9e70000000000000","0000000000000000","1e70000000000000","3fe0000000000000","0000000000000004","0000000000000000","0000000000000004","0000000000000008","0000000000000003","3fd5555555555555","3fe5555555555556","3fe0000000000000","3fe0000000000000","3fd5555555555556","3fd5555555555555","3fe0000000000000","3fd0000000000000","3fb5555555555555","3fdaaaaaaaaaaaab","8000000000000000","0000000000000000","0000000000000000","0000000000000000","3feaaaaaaaaaaaab","0000000000000000","0000000000000003","3fe5555555555555","3fd5555555555556","3fe0000000000000","3fd0000000000000","3fb5555555555556","3fe5555555555555","3fe0000000000000","3fe0000000000000","3fd5555555555555","3fdaaaaaaaaaaaaa","8000000000000004","8000000000000004","8000000000000001","3feaaaaaaaaaaaaa","8000000000000001","0000000000000002","0000000000000001","0000000000000002","3ff193ea7aad030b","3fb81384b7dfa22b","0000000000000000","0000000000000000","3ffbb67ae8584caa","0000000000000000","1e66a09e667f3bcd","0000000000000000","3fe0000000000000","3ffbb67ae8584caa","1e70000000000000","1e55555555555555","1e55555555555555","1e6279a74590331c","1e66a09e667f3bcd","3fea20bd700c2c3d","3ff0000000000000"],"consistency_threshold_bits":["8000000000000000"],"draws":[{"comparison":"3","disposition":"REJECTED","method":"GETRANDBITS","ordinal":0,"position":0,"replicate":0,"value":3,"width":2},{"comparison":"3","disposition":"SELECTED","method":"GETRANDBITS","ordinal":1,"position":0,"replicate":0,"value":1,"width":2},{"comparison":"3fe0000000000000","disposition":"CONTINUE","method":"RANDOM_U53","ordinal":2,"position":1,"replicate":0,"value":6827046333291546,"width":53},{"comparison":"3fe0000000000000","disposition":"RESTART","method":"RANDOM_U53","ordinal":3,"position":2,"replicate":0,"value":3788172029424828,"width":53},{"comparison":"3","disposition":"SELECTED","method":"GETRANDBITS","ordinal":4,"position":2,"replicate":0,"value":1,"width":2}],"indices":[[1,2,1]],"inputs":{"alpha":0.5,"expected_block_length":2.0,"loss_differentials":[[-4.445517498970155e-162],[0.0],[4.445517498970155e-162]],"recenter_variant":"HANSEN_CONSISTENT_LOG_LOG_THRESHOLD","replicates":1,"seed":0,"sign_convention":"BENCHMARK_LOSS_MINUS_CANDIDATE_LOSS_POSITIVE_IS_BETTER"},"log_certificates":[{"candidate":"3ff193ea7aad030b","input_bits":"4008000000000000","position":48,"terms":64},{"candidate":"3fb81384b7dfa22b","input_bits":"3ff193ea7aad030b","position":49,"terms":16}],"oriented_matrix_bits":[["9e70000000000000"],["0000000000000000"],["1e70000000000000"]],"raw":{"candidate_means":[0.0],"consistent_valid_columns":[true],"long_run_variances":[1e-323],"p_value":1.0,"recenter_variant":"HANSEN_CONSISTENT_LOG_LOG_THRESHOLD","reject":false,"simulated_statistics":[0.8164965809277259],"statistic":0.0},"raw_json":"{\\"candidate_means\\":[0.0],\\"consistent_valid_columns\\":[true],\\"long_run_variances\\":[1e-323],\\"p_value\\":1.0,\\"recenter_variant\\":\\"HANSEN_CONSISTENT_LOG_LOG_THRESHOLD\\",\\"reject\\":false,\\"simulated_statistics\\":[0.8164965809277259],\\"statistic\\":0.0}","sqrt_cells":5},{"case":"complete_two_candidate_tie","cell_candidates":["3fe8000000000000","3fd0000000000000","3fe8000000000000","3fd0000000000000","3fe8000000000000","3fd0000000000000","0000000000000000","3fe0000000000000","bfe0000000000000","3fe0000000000000","0000000000000000","3fd0000000000000","3fd0000000000000","3fe0000000000000","3fc5555555555555","3fd5555555555555","3fe5555555555556","3fe0000000000000","3fe0000000000000","3fd5555555555556","3fd5555555555555","3fe0000000000000","3fd0000000000000","3fb5555555555555","3fdaaaaaaaaaaaab","0000000000000000","bfd0000000000000","bfd0000000000000","bfb5555555555555","3feaaaaaaaaaaaab","bfb1c71c71c71c72","3fb8e38e38e38e38","3fe5555555555555","3fd5555555555556","3fe0000000000000","3fd0000000000000","3fb5555555555556","3fe5555555555555","3fe0000000000000","3fe0000000000000","3fd5555555555555","3fdaaaaaaaaaaaaa","8000000000000000","0000000000000000","0000000000000000","3feaaaaaaaaaaaaa","0000000000000000","3fb8e38e38e38e38","3fe8000000000000","3fd0000000000000","0000000000000000","3fe0000000000000","bfe0000000000000","3fe0000000000000","0000000000000000","3fd0000000000000","3fd0000000000000","3fe0000000000000","3fc5555555555555","3fd5555555555555","3fe5555555555556","3fe0000000000000","3fe0000000000000","3fd5555555555556","3fd5555555555555","3fe0000000000000","3fd0000000000000","3fb5555555555555","3fdaaaaaaaaaaaab","0000000000000000","bfd0000000000000","bfd0000000000000","bfb5555555555555","3feaaaaaaaaaaaab","bfb1c71c71c71c72","3fb8e38e38e38e38","3fe5555555555555","3fd5555555555556","3fe0000000000000","3fd0000000000000","3fb5555555555556","3fe5555555555555","3fe0000000000000","3fe0000000000000","3fd5555555555555","3fdaaaaaaaaaaaaa","8000000000000000","0000000000000000","0000000000000000","3feaaaaaaaaaaaaa","0000000000000000","3fb8e38e38e38e38","3fa097b425ed097b","3fb097b425ed097b","3ff193ea7aad030b","3fb81384b7dfa22b","3f78f7cc010dd794","3fb3fcb7bb78b12c","3ffbb67ae8584caa","3fdbb67ae8584caa","3fd3f49c0b9ad4db","3ff6383d1afc0fc3","3fa097b425ed097b","3fb097b425ed097b","3ff193ea7aad030b","3fb81384b7dfa22b","3f78f7cc010dd794","3fb3fcb7bb78b12c","3ffbb67ae8584caa","3fdbb67ae8584caa","3fd3f49c0b9ad4db","3ff6383d1afc0fc3","3fe0000000000000","3ffbb67ae8584caa","3fe8000000000000","3fd0000000000000","0000000000000000","0000000000000000","3fd3f49c0b9ad4db","0000000000000000","3ffbb67ae8584caa","3fe8000000000000","3fd0000000000000","0000000000000000","0000000000000000","3fd3f49c0b9ad4db","0000000000000000","3fe0000000000000"],"consistency_threshold_bits":["bfb3fcb7bb78b12c","bfb3fcb7bb78b12c"],"draws":[{"comparison":"3","disposition":"SELECTED","method":"GETRANDBITS","ordinal":0,"position":0,"replicate":0,"value":1,"width":2},{"comparison":"3fe0000000000000","disposition":"CONTINUE","method":"RANDOM_U53","ordinal":1,"position":1,"replicate":0,"value":8537612169672756,"width":53},{"comparison":"3fe0000000000000","disposition":"RESTART","method":"RANDOM_U53","ordinal":2,"position":2,"replicate":0,"value":3556253902737041,"width":53},{"comparison":"3","disposition":"SELECTED","method":"GETRANDBITS","ordinal":3,"position":2,"replicate":0,"value":0,"width":2}],"indices":[[1,2,0]],"inputs":{"alpha":0.5,"expected_block_length":2.0,"loss_differentials":[[0.25,0.25],[0.75,0.75],[-0.25,-0.25]],"recenter_variant":"HANSEN_CONSISTENT_LOG_LOG_THRESHOLD","replicates":1,"seed":7,"sign_convention":"BENCHMARK_LOSS_MINUS_CANDIDATE_LOSS_POSITIVE_IS_BETTER"},"log_certificates":[{"candidate":"3ff193ea7aad030b","input_bits":"4008000000000000","position":94,"terms":64},{"candidate":"3fb81384b7dfa22b","input_bits":"3ff193ea7aad030b","position":95,"terms":16},{"candidate":"3ff193ea7aad030b","input_bits":"4008000000000000","position":104,"terms":64},{"candidate":"3fb81384b7dfa22b","input_bits":"3ff193ea7aad030b","position":105,"terms":16}],"oriented_matrix_bits":[["3fd0000000000000","3fd0000000000000"],["3fe8000000000000","3fe8000000000000"],["bfd0000000000000","bfd0000000000000"]],"raw":{"candidate_means":[0.25,0.25],"consistent_valid_columns":[true,true],"long_run_variances":[0.09722222222222221,0.09722222222222221],"p_value":0.5,"recenter_variant":"HANSEN_CONSISTENT_LOG_LOG_THRESHOLD","reject":true,"simulated_statistics":[0.0],"statistic":1.3887301496588271},"raw_json":"{\\"candidate_means\\":[0.25,0.25],\\"consistent_valid_columns\\":[true,true],\\"long_run_variances\\":[0.09722222222222221,0.09722222222222221],\\"p_value\\":0.5,\\"recenter_variant\\":\\"HANSEN_CONSISTENT_LOG_LOG_THRESHOLD\\",\\"reject\\":true,\\"simulated_statistics\\":[0.0],\\"statistic\\":1.3887301496588271}","sqrt_cells":10},{"case":"maximum_complete_layout","cell_candidates":["3ff0000000000000","3fd0000000000000","bff0000000000000","bfd0000000000000","3ff0000000000000","3fd0000000000000","0000000000000000","3fe0000000000000","0000000000000000","bfe0000000000000","3fe0000000000000","0000000000000000","3fd0000000000000","0000000000000000","3fd0000000000000","3fe0000000000000","3fc0000000000000","3fd0000000000000","3fe8000000000000","3fe0000000000000","3fe0000000000000","3fd8000000000000","3fd0000000000000","3fe0000000000000","3fc0000000000000","3fa0000000000000","3fda000000000000","0000000000000000","0000000000000000","8000000000000000","0000000000000000","0000000000000000","3fea000000000000","0000000000000000","3fc0000000000000","3fe0000000000000","3fe0000000000000","3fe0000000000000","3fd0000000000000","3fc0000000000000","3fe0000000000000","3fe0000000000000","3fd0000000000000","3fc0000000000000","3fd0000000000000","0000000000000000","bfd0000000000000","bfd0000000000000","bfb0000000000000","3fe0000000000000","bfa0000000000000","3fb8000000000000","3fe8000000000000","3fd0000000000000","3fe0000000000000","3fc0000000000000","3fa0000000000000","3fe8000000000000","3fe0000000000000","3fe0000000000000","3fd8000000000000","3fda000000000000","8000000000000000","0000000000000000","0000000000000000","3fea000000000000","0000000000000000","3fb8000000000000","bff0000000000000","bfd0000000000000","0000000000000000","3fe0000000000000","0000000000000000","bfe0000000000000","3fe0000000000000","0000000000000000","3fd0000000000000","0000000000000000","3fd0000000000000","3fe0000000000000","3fc0000000000000","3fd0000000000000","3fe8000000000000","3fe0000000000000","3fe0000000000000","3fd8000000000000","3fd0000000000000","3fe0000000000000","3fc0000000000000","3fa0000000000000","3fda000000000000","0000000000000000","0000000000000000","8000000000000000","0000000000000000","0000000000000000","3fea000000000000","0000000000000000","3fc0000000000000","3fe0000000000000","3fe0000000000000","3fe0000000000000","3fd0000000000000","3fc0000000000000","3fe0000000000000","3fe0000000000000","3fd0000000000000","3fc0000000000000","3fd0000000000000","0000000000000000","bfd0000000000000","bfd0000000000000","bfb0000000000000","3fe0000000000000","bfa0000000000000","3fb8000000000000","3fe8000000000000","3fd0000000000000","3fe0000000000000","3fc0000000000000","3fa0000000000000","3fe8000000000000","3fe0000000000000","3fe0000000000000","3fd8000000000000","3fda000000000000","8000000000000000","0000000000000000","0000000000000000","3fea000000000000","0000000000000000","3fb8000000000000","3f98000000000000","3fa8000000000000","3ff62e42fefa39ef","3fd4e7936217083f","3f8f5b5d13228c5e","3fbfad43949347c4","4000000000000000","3fe0000000000000","3fd3988e1409212e","3ffa20bd700c2c3f","3f98000000000000","3fa8000000000000","3ff62e42fefa39ef","3fd4e7936217083f","3f8f5b5d13228c5e","3fbfad43949347c4","4000000000000000","bfe0000000000000","3fd3988e1409212e","bffa20bd700c2c3f","3fe0000000000000","4000000000000000","0000000000000000","0000000000000000","bfd0000000000000","bfe0000000000000","3fd3988e1409212e","bffa20bd700c2c3f","4000000000000000","c000000000000000","bfe0000000000000","bfe0000000000000","bff0000000000000","3fd3988e1409212e","c00a20bd700c2c3f","3fe0000000000000","4000000000000000","3fe0000000000000","3fc0000000000000","bfc0000000000000","bfd0000000000000","3fd3988e1409212e","bfea20bd700c2c3f","4000000000000000","bff8000000000000","bfd8000000000000","bfd8000000000000","bfe8000000000000","3fd3988e1409212e","c003988e1409212f","3fe0000000000000","4000000000000000","4004000000000000","3fe4000000000000","3fd8000000000000","3fe8000000000000","3fd3988e1409212e","4003988e1409212f","4000000000000000","3fe0000000000000","3fc0000000000000","3fc0000000000000","3fd0000000000000","3fd3988e1409212e","3fea20bd700c2c3f","3fe0000000000000","4000000000000000","3ff8000000000000","3fd8000000000000","3fc0000000000000","3fd0000000000000","3fd3988e1409212e","3fea20bd700c2c3f","4000000000000000","bfe0000000000000","bfc0000000000000","bfc0000000000000","bfd0000000000000","3fd3988e1409212e","bfea20bd700c2c3f","3fd999999999999a"],"consistency_threshold_bits":["bfbfad43949347c4","bfbfad43949347c4"],"draws":[{"comparison":"4","disposition":"REJECTED","method":"GETRANDBITS","ordinal":0,"position":0,"replicate":0,"value":6,"width":3},{"comparison":"4","disposition":"SELECTED","method":"GETRANDBITS","ordinal":1,"position":0,"replicate":0,"value":3,"width":3},{"comparison":"3fe0000000000000","disposition":"CONTINUE","method":"RANDOM_U53","ordinal":2,"position":1,"replicate":0,"value":6827046333291546,"width":53},{"comparison":"3fe0000000000000","disposition":"RESTART","method":"RANDOM_U53","ordinal":3,"position":2,"replicate":0,"value":3788172029424828,"width":53},{"comparison":"4","disposition":"SELECTED","method":"GETRANDBITS","ordinal":4,"position":2,"replicate":0,"value":2,"width":3},{"comparison":"3fe0000000000000","disposition":"CONTINUE","method":"RANDOM_U53","ordinal":5,"position":3,"replicate":0,"value":8696134604917657,"width":53},{"comparison":"4","disposition":"SELECTED","method":"GETRANDBITS","ordinal":6,"position":0,"replicate":1,"value":3,"width":3},{"comparison":"3fe0000000000000","disposition":"RESTART","method":"RANDOM_U53","ordinal":7,"position":1,"replicate":1,"value":3647322461062558,"width":53},{"comparison":"4","disposition":"REJECTED","method":"GETRANDBITS","ordinal":8,"position":1,"replicate":1,"value":6,"width":3},{"comparison":"4","disposition":"REJECTED","method":"GETRANDBITS","ordinal":9,"position":1,"replicate":1,"value":6,"width":3},{"comparison":"4","disposition":"SELECTED","method":"GETRANDBITS","ordinal":10,"position":1,"replicate":1,"value":2,"width":3},{"comparison":"3fe0000000000000","disposition":"CONTINUE","method":"RANDOM_U53","ordinal":11,"position":2,"replicate":1,"value":8717167392983304,"width":53},{"comparison":"3fe0000000000000","disposition":"RESTART","method":"RANDOM_U53","ordinal":12,"position":3,"replicate":1,"value":3225022060913177,"width":53},{"comparison":"4","disposition":"REJECTED","method":"GETRANDBITS","ordinal":13,"position":3,"replicate":1,"value":7,"width":3},{"comparison":"4","disposition":"REJECTED","method":"GETRANDBITS","ordinal":14,"position":3,"replicate":1,"value":7,"width":3},{"comparison":"4","disposition":"SELECTED","method":"GETRANDBITS","ordinal":15,"position":3,"replicate":1,"value":1,"width":3},{"comparison":"4","disposition":"REJECTED","method":"GETRANDBITS","ordinal":16,"position":0,"replicate":2,"value":4,"width":3},{"comparison":"4","disposition":"SELECTED","method":"GETRANDBITS","ordinal":17,"position":0,"replicate":2,"value":1,"width":3},{"comparison":"3fe0000000000000","disposition":"RESTART","method":"RANDOM_U53","ordinal":18,"position":1,"replicate":2,"value":2538569622034820,"width":53},{"comparison":"4","disposition":"REJECTED","method":"GETRANDBITS","ordinal":19,"position":1,"replicate":2,"value":6,"width":3},{"comparison":"4","disposition":"SELECTED","method":"GETRANDBITS","ordinal":20,"position":1,"replicate":2,"value":0,"width":3},{"comparison":"3fe0000000000000","disposition":"CONTINUE","method":"RANDOM_U53","ordinal":21,"position":2,"replicate":2,"value":5569772766008982,"width":53},{"comparison":"3fe0000000000000","disposition":"RESTART","method":"RANDOM_U53","ordinal":22,"position":3,"replicate":2,"value":2256360531227667,"width":53},{"comparison":"4","disposition":"REJECTED","method":"GETRANDBITS","ordinal":23,"position":3,"replicate":2,"value":7,"width":3},{"comparison":"4","disposition":"REJECTED","method":"GETRANDBITS","ordinal":24,"position":3,"replicate":2,"value":4,"width":3},{"comparison":"4","disposition":"REJECTED","method":"GETRANDBITS","ordinal":25,"position":3,"replicate":2,"value":7,"width":3},{"comparison":"4","disposition":"REJECTED","method":"GETRANDBITS","ordinal":26,"position":3,"replicate":2,"value":5,"width":3},{"comparison":"4","disposition":"REJECTED","method":"GETRANDBITS","ordinal":27,"position":3,"replicate":2,"value":6,"width":3},{"comparison":"4","disposition":"REJECTED","method":"GETRANDBITS","ordinal":28,"position":3,"replicate":2,"value":4,"width":3},{"comparison":"4","disposition":"REJECTED","method":"GETRANDBITS","ordinal":29,"position":3,"replicate":2,"value":7,"width":3},{"comparison":"4","disposition":"SELECTED","method":"GETRANDBITS","ordinal":30,"position":3,"replicate":2,"value":1,"width":3},{"comparison":"4","disposition":"SELECTED","method":"GETRANDBITS","ordinal":31,"position":0,"replicate":3,"value":2,"width":3},{"comparison":"3fe0000000000000","disposition":"RESTART","method":"RANDOM_U53","ordinal":32,"position":1,"replicate":3,"value":889581124409603,"width":53},{"comparison":"4","disposition":"SELECTED","method":"GETRANDBITS","ordinal":33,"position":1,"replicate":3,"value":0,"width":3},{"comparison":"3fe0000000000000","disposition":"CONTINUE","method":"RANDOM_U53","ordinal":34,"position":2,"replicate":3,"value":8096015557517980,"width":53},{"comparison":"3fe0000000000000","disposition":"CONTINUE","method":"RANDOM_U53","ordinal":35,"position":3,"replicate":3,"value":6160779561803576,"width":53}],"indices":[[3,0,2,3],[3,2,3,1],[1,0,1,1],[2,0,1,2]],"inputs":{"alpha":0.5,"expected_block_length":2.0,"loss_differentials":[[0.25,-0.25],[0.75,0.25],[0.25,-0.25],[-0.25,-0.75]],"recenter_variant":"HANSEN_CONSISTENT_LOG_LOG_THRESHOLD","replicates":4,"seed":0,"sign_convention":"BENCHMARK_LOSS_MINUS_CANDIDATE_LOSS_POSITIVE_IS_BETTER"},"log_certificates":[{"candidate":"3ff62e42fefa39ef","input_bits":"4010000000000000","position":134,"terms":64},{"candidate":"3fd4e7936217083f","input_bits":"3ff62e42fefa39ef","position":135,"terms":16},{"candidate":"3ff62e42fefa39ef","input_bits":"4010000000000000","position":144,"terms":64},{"candidate":"3fd4e7936217083f","input_bits":"3ff62e42fefa39ef","position":145,"terms":16}],"oriented_matrix_bits":[["3fd0000000000000","bfd0000000000000"],["3fe8000000000000","3fd0000000000000"],["3fd0000000000000","bfd0000000000000"],["bfd0000000000000","bfe8000000000000"]],"raw":{"candidate_means":[0.25,-0.25],"consistent_valid_columns":[true,false],"long_run_variances":[0.09375,0.09375],"p_value":0.4,"recenter_variant":"HANSEN_CONSISTENT_LOG_LOG_THRESHOLD","reject":true,"simulated_statistics":[0.0,0.0,2.4494897427831783,0.8164965809277261],"statistic":1.6329931618554523},"raw_json":"{\\"candidate_means\\":[0.25,-0.25],\\"consistent_valid_columns\\":[true,false],\\"long_run_variances\\":[0.09375,0.09375],\\"p_value\\":0.4,\\"recenter_variant\\":\\"HANSEN_CONSISTENT_LOG_LOG_THRESHOLD\\",\\"reject\\":true,\\"simulated_statistics\\":[0.0,0.0,2.4494897427831783,0.8164965809277261],\\"statistic\\":1.6329931618554523}","sqrt_cells":22}]')
    cap = json.loads('{"case":"all_zero_draw_cap","cell_candidates":["0000000000000000","0000000000000000","0000000000000000","0000000000000000","0000000000000000","0000000000000000","0000000000000000","0000000000000000","3ff0000000000000","0000000000000000","0000000000000000","0000000000000000","0000000000000000","0000000000000000","0000000000000000","3fd0000000000000","3fe8000000000000","0000000000000000","0000000000000000","0000000000000000","3fd0000000000000","0000000000000000","0000000000000000","0000000000000000","0000000000000000","0000000000000000","0000000000000000","0000000000000000","0000000000000000","0000000000000000","0000000000000000","0000000000000000","0000000000000000","3fe0000000000000","3fe0000000000000","0000000000000000","0000000000000000","0000000000000000","3fe0000000000000","0000000000000000","0000000000000000","0000000000000000","0000000000000000","0000000000000000","0000000000000000","0000000000000000","0000000000000000","0000000000000000","0000000000000000","0000000000000000","3fe8000000000000","3fd0000000000000","0000000000000000","0000000000000000","0000000000000000","3fe8000000000000","0000000000000000","0000000000000000","0000000000000000","0000000000000000","0000000000000000","0000000000000000","0000000000000000","0000000000000000","0000000000000000","0000000000000000","3ff0000000000000","3ff0000000000000","3ff0000000000000","3ff0000000000000","3ff0000000000000"],"consistency_threshold_bits":[null],"draws":[{"comparison":"4","disposition":"REJECTED","method":"GETRANDBITS","ordinal":0,"position":0,"replicate":0,"value":4,"width":3},{"comparison":"4","disposition":"SELECTED","method":"GETRANDBITS","ordinal":1,"position":0,"replicate":0,"value":2,"width":3},{"comparison":"3ff0000000000000","disposition":"RESTART","method":"RANDOM_U53","ordinal":2,"position":1,"replicate":0,"value":6672353513170771,"width":53},{"comparison":"4","disposition":"SELECTED","method":"GETRANDBITS","ordinal":3,"position":1,"replicate":0,"value":0,"width":3},{"comparison":"3ff0000000000000","disposition":"RESTART","method":"RANDOM_U53","ordinal":4,"position":2,"replicate":0,"value":2824969097079463,"width":53},{"comparison":"4","disposition":"REJECTED","method":"GETRANDBITS","ordinal":5,"position":2,"replicate":0,"value":7,"width":3},{"comparison":"4","disposition":"REJECTED","method":"GETRANDBITS","ordinal":6,"position":2,"replicate":0,"value":5,"width":3},{"comparison":"4","disposition":"REJECTED","method":"GETRANDBITS","ordinal":7,"position":2,"replicate":0,"value":4,"width":3},{"comparison":"4","disposition":"REJECTED","method":"GETRANDBITS","ordinal":8,"position":2,"replicate":0,"value":5,"width":3},{"comparison":"4","disposition":"REJECTED","method":"GETRANDBITS","ordinal":9,"position":2,"replicate":0,"value":7,"width":3},{"comparison":"4","disposition":"REJECTED","method":"GETRANDBITS","ordinal":10,"position":2,"replicate":0,"value":6,"width":3},{"comparison":"4","disposition":"REJECTED","method":"GETRANDBITS","ordinal":11,"position":2,"replicate":0,"value":4,"width":3},{"comparison":"4","disposition":"SELECTED","method":"GETRANDBITS","ordinal":12,"position":2,"replicate":0,"value":2,"width":3},{"comparison":"3ff0000000000000","disposition":"RESTART","method":"RANDOM_U53","ordinal":13,"position":3,"replicate":0,"value":5125821927941671,"width":53},{"comparison":"4","disposition":"REJECTED","method":"GETRANDBITS","ordinal":14,"position":3,"replicate":0,"value":4,"width":3},{"comparison":"4","disposition":"REJECTED","method":"GETRANDBITS","ordinal":15,"position":3,"replicate":0,"value":5,"width":3},{"comparison":"4","disposition":"REJECTED","method":"GETRANDBITS","ordinal":16,"position":3,"replicate":0,"value":5,"width":3},{"comparison":"4","disposition":"SELECTED","method":"GETRANDBITS","ordinal":17,"position":3,"replicate":0,"value":1,"width":3},{"comparison":"4","disposition":"SELECTED","method":"GETRANDBITS","ordinal":18,"position":0,"replicate":1,"value":3,"width":3},{"comparison":"3ff0000000000000","disposition":"RESTART","method":"RANDOM_U53","ordinal":19,"position":1,"replicate":1,"value":6374739605173293,"width":53},{"comparison":"4","disposition":"REJECTED","method":"GETRANDBITS","ordinal":20,"position":1,"replicate":1,"value":4,"width":3},{"comparison":"4","disposition":"REJECTED","method":"GETRANDBITS","ordinal":21,"position":1,"replicate":1,"value":7,"width":3},{"comparison":"4","disposition":"REJECTED","method":"GETRANDBITS","ordinal":22,"position":1,"replicate":1,"value":6,"width":3},{"comparison":"4","disposition":"REJECTED","method":"GETRANDBITS","ordinal":23,"position":1,"replicate":1,"value":7,"width":3},{"comparison":"4","disposition":"REJECTED","method":"GETRANDBITS","ordinal":24,"position":1,"replicate":1,"value":6,"width":3},{"comparison":"4","disposition":"REJECTED","method":"GETRANDBITS","ordinal":25,"position":1,"replicate":1,"value":6,"width":3},{"comparison":"4","disposition":"REJECTED","method":"GETRANDBITS","ordinal":26,"position":1,"replicate":1,"value":5,"width":3},{"comparison":"4","disposition":"REJECTED","method":"GETRANDBITS","ordinal":27,"position":1,"replicate":1,"value":7,"width":3},{"comparison":"4","disposition":"REJECTED","method":"GETRANDBITS","ordinal":28,"position":1,"replicate":1,"value":4,"width":3},{"comparison":"4","disposition":"REJECTED","method":"GETRANDBITS","ordinal":29,"position":1,"replicate":1,"value":5,"width":3},{"comparison":"4","disposition":"REJECTED","method":"GETRANDBITS","ordinal":30,"position":1,"replicate":1,"value":7,"width":3},{"comparison":"4","disposition":"REJECTED","method":"GETRANDBITS","ordinal":31,"position":1,"replicate":1,"value":6,"width":3},{"comparison":"4","disposition":"SELECTED","method":"GETRANDBITS","ordinal":32,"position":1,"replicate":1,"value":1,"width":3},{"comparison":"3ff0000000000000","disposition":"RESTART","method":"RANDOM_U53","ordinal":33,"position":2,"replicate":1,"value":3319397094041662,"width":53},{"comparison":"4","disposition":"REJECTED","method":"GETRANDBITS","ordinal":34,"position":2,"replicate":1,"value":5,"width":3},{"comparison":"4","disposition":"REJECTED","method":"GETRANDBITS","ordinal":35,"position":2,"replicate":1,"value":5,"width":3},{"comparison":"4","disposition":"REJECTED","method":"GETRANDBITS","ordinal":36,"position":2,"replicate":1,"value":4,"width":3},{"comparison":"4","disposition":"REJECTED","method":"GETRANDBITS","ordinal":37,"position":2,"replicate":1,"value":5,"width":3},{"comparison":"4","disposition":"SELECTED","method":"GETRANDBITS","ordinal":38,"position":2,"replicate":1,"value":1,"width":3},{"comparison":"3ff0000000000000","disposition":"RESTART","method":"RANDOM_U53","ordinal":39,"position":3,"replicate":1,"value":8685348348650618,"width":53},{"comparison":"4","disposition":"REJECTED","method":"GETRANDBITS","ordinal":40,"position":3,"replicate":1,"value":5,"width":3},{"comparison":"4","disposition":"SELECTED","method":"GETRANDBITS","ordinal":41,"position":3,"replicate":1,"value":2,"width":3},{"comparison":"4","disposition":"REJECTED","method":"GETRANDBITS","ordinal":42,"position":0,"replicate":2,"value":4,"width":3},{"comparison":"4","disposition":"SELECTED","method":"GETRANDBITS","ordinal":43,"position":0,"replicate":2,"value":1,"width":3},{"comparison":"3ff0000000000000","disposition":"RESTART","method":"RANDOM_U53","ordinal":44,"position":1,"replicate":2,"value":8122790624983867,"width":53},{"comparison":"4","disposition":"SELECTED","method":"GETRANDBITS","ordinal":45,"position":1,"replicate":2,"value":1,"width":3},{"comparison":"3ff0000000000000","disposition":"RESTART","method":"RANDOM_U53","ordinal":46,"position":2,"replicate":2,"value":5456080112443078,"width":53},{"comparison":"4","disposition":"REJECTED","method":"GETRANDBITS","ordinal":47,"position":2,"replicate":2,"value":7,"width":3},{"comparison":"4","disposition":"REJECTED","method":"GETRANDBITS","ordinal":48,"position":2,"replicate":2,"value":7,"width":3},{"comparison":"4","disposition":"SELECTED","method":"GETRANDBITS","ordinal":49,"position":2,"replicate":2,"value":1,"width":3},{"comparison":"3ff0000000000000","disposition":"RESTART","method":"RANDOM_U53","ordinal":50,"position":3,"replicate":2,"value":6429367834191314,"width":53},{"comparison":"4","disposition":"REJECTED","method":"GETRANDBITS","ordinal":51,"position":3,"replicate":2,"value":5,"width":3},{"comparison":"4","disposition":"REJECTED","method":"GETRANDBITS","ordinal":52,"position":3,"replicate":2,"value":7,"width":3},{"comparison":"4","disposition":"REJECTED","method":"GETRANDBITS","ordinal":53,"position":3,"replicate":2,"value":4,"width":3},{"comparison":"4","disposition":"REJECTED","method":"GETRANDBITS","ordinal":54,"position":3,"replicate":2,"value":4,"width":3},{"comparison":"4","disposition":"SELECTED","method":"GETRANDBITS","ordinal":55,"position":3,"replicate":2,"value":0,"width":3},{"comparison":"4","disposition":"REJECTED","method":"GETRANDBITS","ordinal":56,"position":0,"replicate":3,"value":5,"width":3},{"comparison":"4","disposition":"SELECTED","method":"GETRANDBITS","ordinal":57,"position":0,"replicate":3,"value":3,"width":3},{"comparison":"3ff0000000000000","disposition":"RESTART","method":"RANDOM_U53","ordinal":58,"position":1,"replicate":3,"value":3005305065223835,"width":53},{"comparison":"4","disposition":"SELECTED","method":"GETRANDBITS","ordinal":59,"position":1,"replicate":3,"value":0,"width":3},{"comparison":"3ff0000000000000","disposition":"RESTART","method":"RANDOM_U53","ordinal":60,"position":2,"replicate":3,"value":2251644347957803,"width":53},{"comparison":"4","disposition":"SELECTED","method":"GETRANDBITS","ordinal":61,"position":2,"replicate":3,"value":3,"width":3},{"comparison":"3ff0000000000000","disposition":"RESTART","method":"RANDOM_U53","ordinal":62,"position":3,"replicate":3,"value":3715359117590394,"width":53},{"comparison":"4","disposition":"REJECTED","method":"GETRANDBITS","ordinal":63,"position":3,"replicate":3,"value":5,"width":3},{"comparison":"4","disposition":"REJECTED","method":"GETRANDBITS","ordinal":64,"position":3,"replicate":3,"value":6,"width":3},{"comparison":"4","disposition":"SELECTED","method":"GETRANDBITS","ordinal":65,"position":3,"replicate":3,"value":2,"width":3}],"indices":[[2,0,2,1],[3,1,1,2],[1,1,1,0],[3,0,3,2]],"inputs":{"alpha":0.5,"expected_block_length":1.0,"loss_differentials":[[0.0],[0.0],[0.0],[0.0]],"recenter_variant":"HANSEN_CONSISTENT_LOG_LOG_THRESHOLD","replicates":4,"seed":211,"sign_convention":"BENCHMARK_LOSS_MINUS_CANDIDATE_LOSS_POSITIVE_IS_BETTER"},"log_certificates":[],"oriented_matrix_bits":[["0000000000000000"],["0000000000000000"],["0000000000000000"],["0000000000000000"]],"raw":{"candidate_means":[0.0],"consistent_valid_columns":[false],"long_run_variances":[0.0],"p_value":1.0,"recenter_variant":"HANSEN_CONSISTENT_LOG_LOG_THRESHOLD","reject":false,"simulated_statistics":[0.0,0.0,0.0,0.0],"statistic":0.0},"raw_json":"{\\"candidate_means\\":[0.0],\\"consistent_valid_columns\\":[false],\\"long_run_variances\\":[0.0],\\"p_value\\":1.0,\\"recenter_variant\\":\\"HANSEN_CONSISTENT_LOG_LOG_THRESHOLD\\",\\"reject\\":false,\\"simulated_statistics\\":[0.0,0.0,0.0,0.0],\\"statistic\\":0.0}","sqrt_cells":0}')
    def projection(value):
        return MappingProxyType({name:tuple(item) if type(item) is list else item for name,item in value.items()})
    def run(selected, work, *, inputs=None, raw=None, expected=None, projected=None, expected_environment=None):
        return IndependentEvidenceReviewV1._bounded_review_spa_v1(
            deterministic_json(selected["inputs"] if inputs is None else inputs).encode("utf-8"),
            deterministic_json(selected["raw"] if raw is None else raw).encode("utf-8"),
            deterministic_json(selected["raw"] if expected is None else expected).encode("utf-8"),
            projection(selected["raw"]) if projected is None else projected,
            expected_environment=environment if expected_environment is None else expected_environment, work=work)
    def forbidden(*args, **kwargs):
        raise AssertionError("independent SPA proof invoked formula, resampler, fsum, log or sqrt")
    positives = []
    global_rng = random.getstate()
    with ExitStack() as stack:
        for name in ("compute_math_16_hansen_spa", "_stationary_indices", "_v34_mean", "_v34_spa_long_run_variance"):
            stack.enter_context(patch.object(formulas, name, forbidden))
        for name in ("fsum", "log", "sqrt"):
            stack.enter_context(patch.object(math, name, forbidden))
        for selected in cases:
            work = _EvidenceNumericalWorkV1(limits, retained_input_capacity=0)
            proof = run(selected, work)
            first = dict(work.consumed)
            assert work.state == "OPEN" and tuple(proof["cell_candidates"]) == tuple(selected["cell_candidates"])
            assert list(proof["log_certificates"]) == selected["log_certificates"]
            assert list(proof["draws"]) == selected["draws"]
            for name in ("indices", "oriented_matrix_bits", "consistency_threshold_bits"):
                assert deterministic_json(proof[name]) == deterministic_json(selected[name])
            assert proof["summary"]["original_raw_json"] == selected["raw_json"]
            assert first["random_draws"] == len(selected["draws"])
            assert first["square_roots"] == selected["sqrt_cells"]
            assert first["log_series_terms"] == sum(row["terms"] for row in selected["log_certificates"])
            fragments = [dict(position=i,candidate=value) for i,value in enumerate(proof["cell_candidates"])]
            assert first["serialized_bytes"] == sum(len(deterministic_json(value).encode("utf-8")) for value in
                [*fragments, *proof["log_certificates"], *proof["draws"], proof["summary"], proof])
            work._assert_bootstrap_custody_v1()
            assert len(work._bootstrap_invocations) == 1
            assert work._bootstrap_invocations[0][0].completed[2] == deterministic_json(proof)
            assert all(first[key] == 0 for key in ("decimal_constructions", "retained_decimal_inputs"))
            positives.append(dict(case=selected["case"],proof=proof,first_consumption=first))
    assert random.getstate() == global_rng
    base = next(row for row in cases if row["case"] == "positive_variance_n3")
    zero_case = next(row for row in cases if row["case"] == "all_zero")
    family = next(row for row in cases if row["case"] == "complete_two_candidates")
    mutations = (
        ("boolean_seed", "inputs", dict(seed=True)),
        ("seed_bits", "inputs", dict(seed=2**256)),
        ("zero_replicates", "inputs", dict(replicates=0)),
        ("boolean_replicates", "inputs", dict(replicates=True)),
        ("replicate_bound", "inputs", dict(replicates=5)),
        ("two_times", "inputs", dict(loss_differentials=[[.25],[.75]])),
        ("too_many_times", "inputs", dict(loss_differentials=[[.25]]*5)),
        ("too_many_candidates", "inputs", dict(loss_differentials=[[.25]*3]*3)),
        ("ragged_matrix", "inputs", dict(loss_differentials=[[.25],[.75],[]])),
        ("boolean_matrix", "inputs", dict(loss_differentials=[[True],[.75],[-.25]])),
        ("integer_matrix", "inputs", dict(loss_differentials=[[0],[.75],[-.25]])),
        ("matrix_domain", "inputs", dict(loss_differentials=[[1.0000000000000002],[.75],[-.25]])),
        ("sign_convention", "inputs", dict(sign_convention="POSITIVE")),
        ("block_low", "inputs", dict(expected_block_length=.5)),
        ("block_high", "inputs", dict(expected_block_length=4.0)),
        ("block_integer", "inputs", dict(expected_block_length=2)),
        ("alpha_zero", "inputs", dict(alpha=0.0)),
        ("alpha_one", "inputs", dict(alpha=1.0)),
        ("variant", "inputs", dict(recenter_variant="UNCENTERED")),
        ("positive_mean_zero_variance", "inputs", dict(loss_differentials=[[.25]]*3)),
        ("statistic_ulp", "raw", dict(statistic=math.nextafter(base["raw"]["statistic"], 2.0))),
        ("p_value_without_plus_one", "raw", dict(p_value=0.0)),
        ("wrong_reject", "raw", dict(reject=False)),
        ("integer_reject", "raw", dict(reject=1)),
        ("omitted_family_column", "raw", dict(candidate_means=[])),
        ("variance_ulp", "raw", dict(long_run_variances=[math.nextafter(base["raw"]["long_run_variances"][0],1.0)])),
        ("valid_column", "raw", dict(consistent_valid_columns=[False])),
        ("integer_valid_flag", "raw", dict(consistent_valid_columns=[1])),
        ("simulation", "raw", dict(simulated_statistics=[0.0])),
        ("raw_variant", "raw", dict(recenter_variant="UNCENTERED")),
        ("expected_p_value", "expected", dict(p_value=1.0)),
    )
    denials = []
    for name, field, changes in mutations:
        value = dict(base["inputs"] if field == "inputs" else base["raw"], **changes)
        work = _EvidenceNumericalWorkV1(limits, retained_input_capacity=0)
        with pytest.raises(ComputationControlPlaneError):run(base, work, **{field:value})
        assert work.state == "FAILED"
        if work._bootstrap_invocations:work._assert_bootstrap_custody_v1(failed=True)
        before = dict(work.consumed)
        with pytest.raises(ComputationControlPlaneError,match="LP03_NUMERICAL_WORK_NOT_OPEN"):run(base, work)
        assert dict(work.consumed) == before
        denials.append(dict(case=name,failure=work.failure,consumed=before))
    extras = (
        ("environment",base,{},dict(expected_environment=replace(environment,build="different"))),
        ("mutable_projection",base,{},dict(projected=dict(base["raw"]))),
        ("projection_valid_flags",base,{},dict(projected=projection(dict(base["raw"],consistent_valid_columns=[False])))),
        ("zero_budget",base,dict(max_serialized_bytes=0),{}),
        ("complete_bytes",base,dict(max_serialized_bytes=10000),{}),
        ("work_bits",base,dict(max_work_bits=1074),{}),
        ("input_bits",base,dict(max_input_bits=1),{}),
        ("all_zero_bad_seed",zero_case,{},dict(inputs=dict(zero_case["inputs"],seed=True))),
        ("all_zero_clamp_sign",zero_case,{},dict(raw=dict(zero_case["raw"],statistic=-0.0))),
        ("family_reordered_means",family,{},dict(raw=dict(family["raw"],candidate_means=[-.25,.25]))),
        ("ineligible_positive_variance_omitted",family,{},dict(raw=dict(family["raw"],long_run_variances=[family["raw"]["long_run_variances"][0]]))),
    )
    for name, selected, changes, arguments in extras:
        work = _EvidenceNumericalWorkV1(dict(limits,**changes),retained_input_capacity=0)
        with pytest.raises(ComputationControlPlaneError):run(selected,work,**arguments)
        assert work.state == "FAILED"
        if work._bootstrap_invocations:work._assert_bootstrap_custody_v1(failed=True)
        denials.append(dict(case=name,failure=work.failure,consumed=dict(work.consumed)))
    # SPA's all-zero path still adds a new original replay and actual returns.
    work = _EvidenceNumericalWorkV1(limits,retained_input_capacity=0)
    run(base,work);original=tuple(work._bootstrap_invocations);before=dict(work.consumed)
    zero_proof=run(zero_case,work)
    assert len(work._bootstrap_invocations)==2 and work._bootstrap_invocations[0] is original[0]
    assert work.consumed["random_draws"]==before["random_draws"]+len(zero_case["draws"])
    work._assert_bootstrap_custody_v1()
    original_work_zero=dict(before=before,after=dict(work.consumed),retained_invocations=2,proof=zero_proof)
    def failed_constructor(*args,**kwargs):raise RuntimeError("SPA original constructor failure")
    work = _EvidenceNumericalWorkV1(limits,retained_input_capacity=0)
    with patch.object(random,"Random",failed_constructor):
        with pytest.raises(RuntimeError,match="SPA original constructor failure"):run(zero_case,work)
    work._assert_bootstrap_custody_v1(failed=True)
    assert work.state=="FAILED" and work.consumed["random_draws"]==0 and len(work._bootstrap_invocations)==1
    denials.append(dict(case="all_zero_original_constructor_failure",failure=work.failure,consumed=dict(work.consumed)))
    work = _EvidenceNumericalWorkV1(limits,retained_input_capacity=0)
    completed=0
    for _ in range(8):
        before=dict(work.consumed);original=tuple(work._bootstrap_invocations)
        try:run(base,work)
        except ComputationControlPlaneError:
            assert completed>=2 and work.failure=="LP03_SPA_REVIEW_COMPLETE_BYTES_EXHAUSTED"
            assert dict(work.consumed)==before and len(work._bootstrap_invocations)==completed
            assert all(work._bootstrap_invocations[i] is row for i,row in enumerate(original))
            break
        completed+=1
    else:raise AssertionError("original SPA allowance did not stop cumulative replay")
    work._assert_bootstrap_custody_v1(failed=True)
    denials.append(dict(case="original_cumulative_allowance",completed=completed,failure=work.failure,consumed=dict(work.consumed)))
    work = _EvidenceNumericalWorkV1(limits,retained_input_capacity=0)
    with pytest.raises(ComputationControlPlaneError,match="LP03_BOOTSTRAP_REPLAY_DRAW_LIMIT_EXHAUSTED"):run(cap,work)
    assert work.state=="FAILED" and work.consumed["random_draws"]==64
    entry=work._bootstrap_invocations[0][0]
    assert len(entry.prefix)==64 and entry.pending_request==("GETRANDBITS",3,3,3,4,None,"4")
    assert [row[3] for row in entry.prefix]==[row["value"] for row in cap["draws"][:64]]
    work._assert_bootstrap_custody_v1(failed=True)
    denials.append(dict(case="all_zero_retained_64_draws_unentered_65",failure=work.failure,consumed=dict(work.consumed),
        prefix=tuple(dict(ordinal=row[0],request=row[1],value=row[3],state=row[5]) for row in entry.prefix),pending_request=entry.pending_request))
    print("LP03_SPA_PURE_QUALIFICATION="+deterministic_json(dict(
        scope="BOUNDED_SPA_MODEL_ONLY_NO_FAMILY_SOURCE_NATIVE_OR_SIGNIFICANCE_AUTHORITY",
        positives=positives,denials=denials,original_work_all_zero=original_work_zero)))


def _assert_lp03_reality_check_ordered_model_proof():
    import json
    import math
    import random
    from contextlib import ExitStack
    from dataclasses import replace
    from types import MappingProxyType
    from unittest.mock import patch
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane import implementation_registry as formulas
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.evidence import IndependentEvidenceReviewV1
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.evidence_execution import _worker_environment_v1
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.parameter_policy import _EvidenceNumericalWorkV1
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import ComputationControlPlaneError
    limits = dict(max_input_bits=4096, max_work_bits=65536, max_serialized_bytes=65536)
    environment = _worker_environment_v1()
    # Independent integer MT and exact rational/Decimal160 model literals;
    # no QTT formula or candidate helper supplied these expected values.
    cases = json.loads('[{"branch":"COMPLETE_FAMILY_CENTERED_STATIONARY_REPLAY","case":"two_candidates","cells":[{"candidate":"3ff0000000000000","kind":"FSUM","operands_json":"[\\"3fd0000000000000\\",\\"3fe8000000000000\\"]","operation":"SUM_0"},{"candidate":"3fe0000000000000","kind":"DIV","operands_json":"[\\"3ff0000000000000\\",\\"4000000000000000\\"]","operation":"MEAN_0"},{"candidate":"0000000000000000","kind":"FSUM","operands_json":"[\\"bfd0000000000000\\",\\"3fd0000000000000\\"]","operation":"SUM_1"},{"candidate":"0000000000000000","kind":"DIV","operands_json":"[\\"0000000000000000\\",\\"4000000000000000\\"]","operation":"MEAN_1"},{"candidate":"3ff6a09e667f3bcd","kind":"SQRT","operands_json":"[\\"4000000000000000\\"]","operation":"SQRT_N"},{"candidate":"3fe6a09e667f3bcd","kind":"MUL","operands_json":"[\\"3ff6a09e667f3bcd\\",\\"3fe0000000000000\\"]","operation":"OBSERVED_0"},{"candidate":"0000000000000000","kind":"MUL","operands_json":"[\\"3ff6a09e667f3bcd\\",\\"0000000000000000\\"]","operation":"OBSERVED_1"},{"candidate":"3fe0000000000000","kind":"DIV","operands_json":"[\\"3ff0000000000000\\",\\"4000000000000000\\"]","operation":"RESTART_THRESHOLD"},{"candidate":"3ff0000000000000","kind":"FSUM","operands_json":"[\\"3fe8000000000000\\",\\"3fd0000000000000\\"]","operation":"REPLICATE_0_SUM_0"},{"candidate":"3fe0000000000000","kind":"DIV","operands_json":"[\\"3ff0000000000000\\",\\"4000000000000000\\"]","operation":"REPLICATE_0_MEAN_0"},{"candidate":"0000000000000000","kind":"SUB","operands_json":"[\\"3fe0000000000000\\",\\"3fe0000000000000\\"]","operation":"REPLICATE_0_CENTER_0"},{"candidate":"0000000000000000","kind":"MUL","operands_json":"[\\"3ff6a09e667f3bcd\\",\\"0000000000000000\\"]","operation":"REPLICATE_0_STATISTIC_0"},{"candidate":"0000000000000000","kind":"FSUM","operands_json":"[\\"3fd0000000000000\\",\\"bfd0000000000000\\"]","operation":"REPLICATE_0_SUM_1"},{"candidate":"0000000000000000","kind":"DIV","operands_json":"[\\"0000000000000000\\",\\"4000000000000000\\"]","operation":"REPLICATE_0_MEAN_1"},{"candidate":"0000000000000000","kind":"SUB","operands_json":"[\\"0000000000000000\\",\\"0000000000000000\\"]","operation":"REPLICATE_0_CENTER_1"},{"candidate":"0000000000000000","kind":"MUL","operands_json":"[\\"3ff6a09e667f3bcd\\",\\"0000000000000000\\"]","operation":"REPLICATE_0_STATISTIC_1"},{"candidate":"3ff8000000000000","kind":"FSUM","operands_json":"[\\"3fe8000000000000\\",\\"3fe8000000000000\\"]","operation":"REPLICATE_1_SUM_0"},{"candidate":"3fe8000000000000","kind":"DIV","operands_json":"[\\"3ff8000000000000\\",\\"4000000000000000\\"]","operation":"REPLICATE_1_MEAN_0"},{"candidate":"3fd0000000000000","kind":"SUB","operands_json":"[\\"3fe8000000000000\\",\\"3fe0000000000000\\"]","operation":"REPLICATE_1_CENTER_0"},{"candidate":"3fd6a09e667f3bcd","kind":"MUL","operands_json":"[\\"3ff6a09e667f3bcd\\",\\"3fd0000000000000\\"]","operation":"REPLICATE_1_STATISTIC_0"},{"candidate":"3fe0000000000000","kind":"FSUM","operands_json":"[\\"3fd0000000000000\\",\\"3fd0000000000000\\"]","operation":"REPLICATE_1_SUM_1"},{"candidate":"3fd0000000000000","kind":"DIV","operands_json":"[\\"3fe0000000000000\\",\\"4000000000000000\\"]","operation":"REPLICATE_1_MEAN_1"},{"candidate":"3fd0000000000000","kind":"SUB","operands_json":"[\\"3fd0000000000000\\",\\"0000000000000000\\"]","operation":"REPLICATE_1_CENTER_1"},{"candidate":"3fd6a09e667f3bcd","kind":"MUL","operands_json":"[\\"3ff6a09e667f3bcd\\",\\"3fd0000000000000\\"]","operation":"REPLICATE_1_STATISTIC_1"},{"candidate":"3fd5555555555555","kind":"DIV","operands_json":"[\\"3ff0000000000000\\",\\"4008000000000000\\"]","operation":"PLUS_ONE_P_VALUE"}],"derived_indices":[[1,0],[1,1]],"draws":[{"comparison":"2","disposition":"REJECTED","method":"GETRANDBITS","ordinal":0,"position":0,"replicate":0,"value":3,"width":2},{"comparison":"2","disposition":"SELECTED","method":"GETRANDBITS","ordinal":1,"position":0,"replicate":0,"value":1,"width":2},{"comparison":"3fe0000000000000","disposition":"CONTINUE","method":"RANDOM_U53","ordinal":2,"position":1,"replicate":0,"value":6827046333291546,"width":53},{"comparison":"2","disposition":"SELECTED","method":"GETRANDBITS","ordinal":3,"position":0,"replicate":1,"value":1,"width":2},{"comparison":"3fe0000000000000","disposition":"RESTART","method":"RANDOM_U53","ordinal":4,"position":1,"replicate":1,"value":364650860978552,"width":53},{"comparison":"2","disposition":"REJECTED","method":"GETRANDBITS","ordinal":5,"position":1,"replicate":1,"value":3,"width":2},{"comparison":"2","disposition":"REJECTED","method":"GETRANDBITS","ordinal":6,"position":1,"replicate":1,"value":2,"width":2},{"comparison":"2","disposition":"SELECTED","method":"GETRANDBITS","ordinal":7,"position":1,"replicate":1,"value":1,"width":2}],"exceedances":0,"inputs":{"alpha":0.5,"expected_block_length":2.0,"loss_differentials":[[0.25,-0.25],[0.75,0.25]],"replicates":2,"seed":0,"sign_convention":"BENCHMARK_LOSS_MINUS_CANDIDATE_LOSS_POSITIVE_IS_BETTER"},"mt_words":[3626764237,1654615998,3255389356,3823568514,1806341205,173879092,1112038970,4146640122,2195908194,2087043557],"observation_scope":"ALL_FORMULA_INTERMEDIATES_DERIVED_NOT_OBSERVED","observed_selected_column":0,"oriented_matrix_bits":[["3fd0000000000000","bfd0000000000000"],["3fe8000000000000","3fd0000000000000"]],"raw":{"candidate_means":[0.5,0.0],"p_value":0.3333333333333333,"recenter_policy":"CENTER_EACH_COMPLETE_MATERIAL_CANDIDATE_AT_ITS_SAMPLE_MEAN","reject":true,"simulated_statistics":[0.0,0.3535533905932738],"statistic":0.7071067811865476},"raw_json":"{\\"candidate_means\\":[0.5,0.0],\\"p_value\\":0.3333333333333333,\\"recenter_policy\\":\\"CENTER_EACH_COMPLETE_MATERIAL_CANDIDATE_AT_ITS_SAMPLE_MEAN\\",\\"reject\\":true,\\"simulated_statistics\\":[0.0,0.3535533905932738],\\"statistic\\":0.7071067811865476}","replicate_selected_columns":[-1,0],"statistical_authority":"NO_EMPIRICAL_FAMILY_OR_SIGNIFICANCE_CERTIFICATION"},{"branch":"COMPLETE_FAMILY_CENTERED_STATIONARY_REPLAY","case":"opposite_sign","cells":[{"candidate":"3ff0000000000000","kind":"FSUM","operands_json":"[\\"3fd0000000000000\\",\\"3fe8000000000000\\"]","operation":"SUM_0"},{"candidate":"3fe0000000000000","kind":"DIV","operands_json":"[\\"3ff0000000000000\\",\\"4000000000000000\\"]","operation":"MEAN_0"},{"candidate":"0000000000000000","kind":"FSUM","operands_json":"[\\"bfd0000000000000\\",\\"3fd0000000000000\\"]","operation":"SUM_1"},{"candidate":"0000000000000000","kind":"DIV","operands_json":"[\\"0000000000000000\\",\\"4000000000000000\\"]","operation":"MEAN_1"},{"candidate":"3ff6a09e667f3bcd","kind":"SQRT","operands_json":"[\\"4000000000000000\\"]","operation":"SQRT_N"},{"candidate":"3fe6a09e667f3bcd","kind":"MUL","operands_json":"[\\"3ff6a09e667f3bcd\\",\\"3fe0000000000000\\"]","operation":"OBSERVED_0"},{"candidate":"0000000000000000","kind":"MUL","operands_json":"[\\"3ff6a09e667f3bcd\\",\\"0000000000000000\\"]","operation":"OBSERVED_1"},{"candidate":"3fe0000000000000","kind":"DIV","operands_json":"[\\"3ff0000000000000\\",\\"4000000000000000\\"]","operation":"RESTART_THRESHOLD"},{"candidate":"3ff0000000000000","kind":"FSUM","operands_json":"[\\"3fe8000000000000\\",\\"3fd0000000000000\\"]","operation":"REPLICATE_0_SUM_0"},{"candidate":"3fe0000000000000","kind":"DIV","operands_json":"[\\"3ff0000000000000\\",\\"4000000000000000\\"]","operation":"REPLICATE_0_MEAN_0"},{"candidate":"0000000000000000","kind":"SUB","operands_json":"[\\"3fe0000000000000\\",\\"3fe0000000000000\\"]","operation":"REPLICATE_0_CENTER_0"},{"candidate":"0000000000000000","kind":"MUL","operands_json":"[\\"3ff6a09e667f3bcd\\",\\"0000000000000000\\"]","operation":"REPLICATE_0_STATISTIC_0"},{"candidate":"0000000000000000","kind":"FSUM","operands_json":"[\\"3fd0000000000000\\",\\"bfd0000000000000\\"]","operation":"REPLICATE_0_SUM_1"},{"candidate":"0000000000000000","kind":"DIV","operands_json":"[\\"0000000000000000\\",\\"4000000000000000\\"]","operation":"REPLICATE_0_MEAN_1"},{"candidate":"0000000000000000","kind":"SUB","operands_json":"[\\"0000000000000000\\",\\"0000000000000000\\"]","operation":"REPLICATE_0_CENTER_1"},{"candidate":"0000000000000000","kind":"MUL","operands_json":"[\\"3ff6a09e667f3bcd\\",\\"0000000000000000\\"]","operation":"REPLICATE_0_STATISTIC_1"},{"candidate":"3ff8000000000000","kind":"FSUM","operands_json":"[\\"3fe8000000000000\\",\\"3fe8000000000000\\"]","operation":"REPLICATE_1_SUM_0"},{"candidate":"3fe8000000000000","kind":"DIV","operands_json":"[\\"3ff8000000000000\\",\\"4000000000000000\\"]","operation":"REPLICATE_1_MEAN_0"},{"candidate":"3fd0000000000000","kind":"SUB","operands_json":"[\\"3fe8000000000000\\",\\"3fe0000000000000\\"]","operation":"REPLICATE_1_CENTER_0"},{"candidate":"3fd6a09e667f3bcd","kind":"MUL","operands_json":"[\\"3ff6a09e667f3bcd\\",\\"3fd0000000000000\\"]","operation":"REPLICATE_1_STATISTIC_0"},{"candidate":"3fe0000000000000","kind":"FSUM","operands_json":"[\\"3fd0000000000000\\",\\"3fd0000000000000\\"]","operation":"REPLICATE_1_SUM_1"},{"candidate":"3fd0000000000000","kind":"DIV","operands_json":"[\\"3fe0000000000000\\",\\"4000000000000000\\"]","operation":"REPLICATE_1_MEAN_1"},{"candidate":"3fd0000000000000","kind":"SUB","operands_json":"[\\"3fd0000000000000\\",\\"0000000000000000\\"]","operation":"REPLICATE_1_CENTER_1"},{"candidate":"3fd6a09e667f3bcd","kind":"MUL","operands_json":"[\\"3ff6a09e667f3bcd\\",\\"3fd0000000000000\\"]","operation":"REPLICATE_1_STATISTIC_1"},{"candidate":"3fd5555555555555","kind":"DIV","operands_json":"[\\"3ff0000000000000\\",\\"4008000000000000\\"]","operation":"PLUS_ONE_P_VALUE"}],"derived_indices":[[1,0],[1,1]],"draws":[{"comparison":"2","disposition":"REJECTED","method":"GETRANDBITS","ordinal":0,"position":0,"replicate":0,"value":3,"width":2},{"comparison":"2","disposition":"SELECTED","method":"GETRANDBITS","ordinal":1,"position":0,"replicate":0,"value":1,"width":2},{"comparison":"3fe0000000000000","disposition":"CONTINUE","method":"RANDOM_U53","ordinal":2,"position":1,"replicate":0,"value":6827046333291546,"width":53},{"comparison":"2","disposition":"SELECTED","method":"GETRANDBITS","ordinal":3,"position":0,"replicate":1,"value":1,"width":2},{"comparison":"3fe0000000000000","disposition":"RESTART","method":"RANDOM_U53","ordinal":4,"position":1,"replicate":1,"value":364650860978552,"width":53},{"comparison":"2","disposition":"REJECTED","method":"GETRANDBITS","ordinal":5,"position":1,"replicate":1,"value":3,"width":2},{"comparison":"2","disposition":"REJECTED","method":"GETRANDBITS","ordinal":6,"position":1,"replicate":1,"value":2,"width":2},{"comparison":"2","disposition":"SELECTED","method":"GETRANDBITS","ordinal":7,"position":1,"replicate":1,"value":1,"width":2}],"exceedances":0,"inputs":{"alpha":0.5,"expected_block_length":2.0,"loss_differentials":[[-0.25,0.25],[-0.75,-0.25]],"replicates":2,"seed":0,"sign_convention":"CANDIDATE_LOSS_MINUS_BENCHMARK_LOSS_NEGATED_TO_POSITIVE_IS_BETTER"},"mt_words":[3626764237,1654615998,3255389356,3823568514,1806341205,173879092,1112038970,4146640122,2195908194,2087043557],"observation_scope":"ALL_FORMULA_INTERMEDIATES_DERIVED_NOT_OBSERVED","observed_selected_column":0,"oriented_matrix_bits":[["3fd0000000000000","bfd0000000000000"],["3fe8000000000000","3fd0000000000000"]],"raw":{"candidate_means":[0.5,0.0],"p_value":0.3333333333333333,"recenter_policy":"CENTER_EACH_COMPLETE_MATERIAL_CANDIDATE_AT_ITS_SAMPLE_MEAN","reject":true,"simulated_statistics":[0.0,0.3535533905932738],"statistic":0.7071067811865476},"raw_json":"{\\"candidate_means\\":[0.5,0.0],\\"p_value\\":0.3333333333333333,\\"recenter_policy\\":\\"CENTER_EACH_COMPLETE_MATERIAL_CANDIDATE_AT_ITS_SAMPLE_MEAN\\",\\"reject\\":true,\\"simulated_statistics\\":[0.0,0.3535533905932738],\\"statistic\\":0.7071067811865476}","replicate_selected_columns":[-1,0],"statistical_authority":"NO_EMPIRICAL_FAMILY_OR_SIGNIFICANCE_CERTIFICATION"},{"branch":"ALL_ZERO_NO_RNG_CONSTRUCTION","case":"all_zero","cells":[{"candidate":"0000000000000000","kind":"FSUM","operands_json":"[\\"8000000000000000\\",\\"0000000000000000\\"]","operation":"SUM_0"},{"candidate":"0000000000000000","kind":"DIV","operands_json":"[\\"0000000000000000\\",\\"4000000000000000\\"]","operation":"MEAN_0"},{"candidate":"0000000000000000","kind":"FSUM","operands_json":"[\\"0000000000000000\\",\\"8000000000000000\\"]","operation":"SUM_1"},{"candidate":"0000000000000000","kind":"DIV","operands_json":"[\\"0000000000000000\\",\\"4000000000000000\\"]","operation":"MEAN_1"},{"candidate":"3ff6a09e667f3bcd","kind":"SQRT","operands_json":"[\\"4000000000000000\\"]","operation":"SQRT_N"},{"candidate":"0000000000000000","kind":"MUL","operands_json":"[\\"3ff6a09e667f3bcd\\",\\"0000000000000000\\"]","operation":"OBSERVED_0"},{"candidate":"0000000000000000","kind":"MUL","operands_json":"[\\"3ff6a09e667f3bcd\\",\\"0000000000000000\\"]","operation":"OBSERVED_1"}],"derived_indices":[],"draws":[],"exceedances":null,"inputs":{"alpha":0.5,"expected_block_length":1.0,"loss_differentials":[[-0.0,0.0],[0.0,-0.0]],"replicates":4,"seed":17,"sign_convention":"BENCHMARK_LOSS_MINUS_CANDIDATE_LOSS_POSITIVE_IS_BETTER"},"mt_words":[],"observation_scope":"ALL_FORMULA_INTERMEDIATES_DERIVED_NOT_OBSERVED","observed_selected_column":-1,"oriented_matrix_bits":[["8000000000000000","0000000000000000"],["0000000000000000","8000000000000000"]],"raw":{"candidate_means":[0.0,0.0],"p_value":1.0,"recenter_policy":"CENTER_EACH_COMPLETE_MATERIAL_CANDIDATE_AT_ITS_SAMPLE_MEAN","reject":false,"simulated_statistics":[0.0,0.0,0.0,0.0],"statistic":0.0},"raw_json":"{\\"candidate_means\\":[0.0,0.0],\\"p_value\\":1.0,\\"recenter_policy\\":\\"CENTER_EACH_COMPLETE_MATERIAL_CANDIDATE_AT_ITS_SAMPLE_MEAN\\",\\"reject\\":false,\\"simulated_statistics\\":[0.0,0.0,0.0,0.0],\\"statistic\\":0.0}","replicate_selected_columns":[],"statistical_authority":"NO_EMPIRICAL_FAMILY_OR_SIGNIFICANCE_CERTIFICATION"},{"branch":"COMPLETE_FAMILY_CENTERED_STATIONARY_REPLAY","case":"negative_family","cells":[{"candidate":"bff0000000000000","kind":"FSUM","operands_json":"[\\"bfe8000000000000\\",\\"bfd0000000000000\\"]","operation":"SUM_0"},{"candidate":"bfe0000000000000","kind":"DIV","operands_json":"[\\"bff0000000000000\\",\\"4000000000000000\\"]","operation":"MEAN_0"},{"candidate":"bff0000000000000","kind":"FSUM","operands_json":"[\\"bfd0000000000000\\",\\"bfe8000000000000\\"]","operation":"SUM_1"},{"candidate":"bfe0000000000000","kind":"DIV","operands_json":"[\\"bff0000000000000\\",\\"4000000000000000\\"]","operation":"MEAN_1"},{"candidate":"3ff6a09e667f3bcd","kind":"SQRT","operands_json":"[\\"4000000000000000\\"]","operation":"SQRT_N"},{"candidate":"bfe6a09e667f3bcd","kind":"MUL","operands_json":"[\\"3ff6a09e667f3bcd\\",\\"bfe0000000000000\\"]","operation":"OBSERVED_0"},{"candidate":"bfe6a09e667f3bcd","kind":"MUL","operands_json":"[\\"3ff6a09e667f3bcd\\",\\"bfe0000000000000\\"]","operation":"OBSERVED_1"},{"candidate":"3fe0000000000000","kind":"DIV","operands_json":"[\\"3ff0000000000000\\",\\"4000000000000000\\"]","operation":"RESTART_THRESHOLD"},{"candidate":"bff0000000000000","kind":"FSUM","operands_json":"[\\"bfe8000000000000\\",\\"bfd0000000000000\\"]","operation":"REPLICATE_0_SUM_0"},{"candidate":"bfe0000000000000","kind":"DIV","operands_json":"[\\"bff0000000000000\\",\\"4000000000000000\\"]","operation":"REPLICATE_0_MEAN_0"},{"candidate":"0000000000000000","kind":"SUB","operands_json":"[\\"bfe0000000000000\\",\\"bfe0000000000000\\"]","operation":"REPLICATE_0_CENTER_0"},{"candidate":"0000000000000000","kind":"MUL","operands_json":"[\\"3ff6a09e667f3bcd\\",\\"0000000000000000\\"]","operation":"REPLICATE_0_STATISTIC_0"},{"candidate":"bff0000000000000","kind":"FSUM","operands_json":"[\\"bfd0000000000000\\",\\"bfe8000000000000\\"]","operation":"REPLICATE_0_SUM_1"},{"candidate":"bfe0000000000000","kind":"DIV","operands_json":"[\\"bff0000000000000\\",\\"4000000000000000\\"]","operation":"REPLICATE_0_MEAN_1"},{"candidate":"0000000000000000","kind":"SUB","operands_json":"[\\"bfe0000000000000\\",\\"bfe0000000000000\\"]","operation":"REPLICATE_0_CENTER_1"},{"candidate":"0000000000000000","kind":"MUL","operands_json":"[\\"3ff6a09e667f3bcd\\",\\"0000000000000000\\"]","operation":"REPLICATE_0_STATISTIC_1"},{"candidate":"bff0000000000000","kind":"FSUM","operands_json":"[\\"bfe8000000000000\\",\\"bfd0000000000000\\"]","operation":"REPLICATE_1_SUM_0"},{"candidate":"bfe0000000000000","kind":"DIV","operands_json":"[\\"bff0000000000000\\",\\"4000000000000000\\"]","operation":"REPLICATE_1_MEAN_0"},{"candidate":"0000000000000000","kind":"SUB","operands_json":"[\\"bfe0000000000000\\",\\"bfe0000000000000\\"]","operation":"REPLICATE_1_CENTER_0"},{"candidate":"0000000000000000","kind":"MUL","operands_json":"[\\"3ff6a09e667f3bcd\\",\\"0000000000000000\\"]","operation":"REPLICATE_1_STATISTIC_0"},{"candidate":"bff0000000000000","kind":"FSUM","operands_json":"[\\"bfd0000000000000\\",\\"bfe8000000000000\\"]","operation":"REPLICATE_1_SUM_1"},{"candidate":"bfe0000000000000","kind":"DIV","operands_json":"[\\"bff0000000000000\\",\\"4000000000000000\\"]","operation":"REPLICATE_1_MEAN_1"},{"candidate":"0000000000000000","kind":"SUB","operands_json":"[\\"bfe0000000000000\\",\\"bfe0000000000000\\"]","operation":"REPLICATE_1_CENTER_1"},{"candidate":"0000000000000000","kind":"MUL","operands_json":"[\\"3ff6a09e667f3bcd\\",\\"0000000000000000\\"]","operation":"REPLICATE_1_STATISTIC_1"},{"candidate":"bfe0000000000000","kind":"FSUM","operands_json":"[\\"bfd0000000000000\\",\\"bfd0000000000000\\"]","operation":"REPLICATE_2_SUM_0"},{"candidate":"bfd0000000000000","kind":"DIV","operands_json":"[\\"bfe0000000000000\\",\\"4000000000000000\\"]","operation":"REPLICATE_2_MEAN_0"},{"candidate":"3fd0000000000000","kind":"SUB","operands_json":"[\\"bfd0000000000000\\",\\"bfe0000000000000\\"]","operation":"REPLICATE_2_CENTER_0"},{"candidate":"3fd6a09e667f3bcd","kind":"MUL","operands_json":"[\\"3ff6a09e667f3bcd\\",\\"3fd0000000000000\\"]","operation":"REPLICATE_2_STATISTIC_0"},{"candidate":"bff8000000000000","kind":"FSUM","operands_json":"[\\"bfe8000000000000\\",\\"bfe8000000000000\\"]","operation":"REPLICATE_2_SUM_1"},{"candidate":"bfe8000000000000","kind":"DIV","operands_json":"[\\"bff8000000000000\\",\\"4000000000000000\\"]","operation":"REPLICATE_2_MEAN_1"},{"candidate":"bfd0000000000000","kind":"SUB","operands_json":"[\\"bfe8000000000000\\",\\"bfe0000000000000\\"]","operation":"REPLICATE_2_CENTER_1"},{"candidate":"bfd6a09e667f3bcd","kind":"MUL","operands_json":"[\\"3ff6a09e667f3bcd\\",\\"bfd0000000000000\\"]","operation":"REPLICATE_2_STATISTIC_1"},{"candidate":"bff8000000000000","kind":"FSUM","operands_json":"[\\"bfe8000000000000\\",\\"bfe8000000000000\\"]","operation":"REPLICATE_3_SUM_0"},{"candidate":"bfe8000000000000","kind":"DIV","operands_json":"[\\"bff8000000000000\\",\\"4000000000000000\\"]","operation":"REPLICATE_3_MEAN_0"},{"candidate":"bfd0000000000000","kind":"SUB","operands_json":"[\\"bfe8000000000000\\",\\"bfe0000000000000\\"]","operation":"REPLICATE_3_CENTER_0"},{"candidate":"bfd6a09e667f3bcd","kind":"MUL","operands_json":"[\\"3ff6a09e667f3bcd\\",\\"bfd0000000000000\\"]","operation":"REPLICATE_3_STATISTIC_0"},{"candidate":"bfe0000000000000","kind":"FSUM","operands_json":"[\\"bfd0000000000000\\",\\"bfd0000000000000\\"]","operation":"REPLICATE_3_SUM_1"},{"candidate":"bfd0000000000000","kind":"DIV","operands_json":"[\\"bfe0000000000000\\",\\"4000000000000000\\"]","operation":"REPLICATE_3_MEAN_1"},{"candidate":"3fd0000000000000","kind":"SUB","operands_json":"[\\"bfd0000000000000\\",\\"bfe0000000000000\\"]","operation":"REPLICATE_3_CENTER_1"},{"candidate":"3fd6a09e667f3bcd","kind":"MUL","operands_json":"[\\"3ff6a09e667f3bcd\\",\\"3fd0000000000000\\"]","operation":"REPLICATE_3_STATISTIC_1"},{"candidate":"3ff0000000000000","kind":"DIV","operands_json":"[\\"4014000000000000\\",\\"4014000000000000\\"]","operation":"PLUS_ONE_P_VALUE"}],"derived_indices":[[0,1],[0,1],[1,1],[0,0]],"draws":[{"comparison":"2","disposition":"SELECTED","method":"GETRANDBITS","ordinal":0,"position":0,"replicate":0,"value":0,"width":2},{"comparison":"3fe0000000000000","disposition":"CONTINUE","method":"RANDOM_U53","ordinal":1,"position":1,"replicate":0,"value":5126932717094315,"width":53},{"comparison":"2","disposition":"REJECTED","method":"GETRANDBITS","ordinal":2,"position":0,"replicate":1,"value":3,"width":2},{"comparison":"2","disposition":"REJECTED","method":"GETRANDBITS","ordinal":3,"position":0,"replicate":1,"value":3,"width":2},{"comparison":"2","disposition":"SELECTED","method":"GETRANDBITS","ordinal":4,"position":0,"replicate":1,"value":0,"width":2},{"comparison":"3fe0000000000000","disposition":"RESTART","method":"RANDOM_U53","ordinal":5,"position":1,"replicate":1,"value":2297457538547630,"width":53},{"comparison":"2","disposition":"SELECTED","method":"GETRANDBITS","ordinal":6,"position":1,"replicate":1,"value":1,"width":2},{"comparison":"2","disposition":"REJECTED","method":"GETRANDBITS","ordinal":7,"position":0,"replicate":2,"value":3,"width":2},{"comparison":"2","disposition":"SELECTED","method":"GETRANDBITS","ordinal":8,"position":0,"replicate":2,"value":1,"width":2},{"comparison":"3fe0000000000000","disposition":"RESTART","method":"RANDOM_U53","ordinal":9,"position":1,"replicate":2,"value":4253607005993776,"width":53},{"comparison":"2","disposition":"SELECTED","method":"GETRANDBITS","ordinal":10,"position":1,"replicate":2,"value":1,"width":2},{"comparison":"2","disposition":"REJECTED","method":"GETRANDBITS","ordinal":11,"position":0,"replicate":3,"value":3,"width":2},{"comparison":"2","disposition":"SELECTED","method":"GETRANDBITS","ordinal":12,"position":0,"replicate":3,"value":0,"width":2},{"comparison":"3fe0000000000000","disposition":"RESTART","method":"RANDOM_U53","ordinal":13,"position":1,"replicate":3,"value":845412000043186,"width":53},{"comparison":"2","disposition":"SELECTED","method":"GETRANDBITS","ordinal":14,"position":1,"replicate":3,"value":0,"width":2}],"exceedances":4,"inputs":{"alpha":0.5,"expected_block_length":2.0,"loss_differentials":[[-0.75,-0.25],[-0.25,-0.75]],"replicates":4,"seed":-1,"sign_convention":"BENCHMARK_LOSS_MINUS_CANDIDATE_LOSS_POSITIVE_IS_BETTER"},"mt_words":[577090037,2444712010,3639700191,3445702192,3280387012,271041745,1095513148,506456969,2127877499,3268308804,1930549411,2028277857,2798570523,1630434966,3387541014,901749037,403123852,2095328386,121751464],"observation_scope":"ALL_FORMULA_INTERMEDIATES_DERIVED_NOT_OBSERVED","observed_selected_column":-1,"oriented_matrix_bits":[["bfe8000000000000","bfd0000000000000"],["bfd0000000000000","bfe8000000000000"]],"raw":{"candidate_means":[-0.5,-0.5],"p_value":1.0,"recenter_policy":"CENTER_EACH_COMPLETE_MATERIAL_CANDIDATE_AT_ITS_SAMPLE_MEAN","reject":false,"simulated_statistics":[0.0,0.0,0.3535533905932738,0.3535533905932738],"statistic":0.0},"raw_json":"{\\"candidate_means\\":[-0.5,-0.5],\\"p_value\\":1.0,\\"recenter_policy\\":\\"CENTER_EACH_COMPLETE_MATERIAL_CANDIDATE_AT_ITS_SAMPLE_MEAN\\",\\"reject\\":false,\\"simulated_statistics\\":[0.0,0.0,0.3535533905932738,0.3535533905932738],\\"statistic\\":0.0}","replicate_selected_columns":[-1,-1,0,1],"statistical_authority":"NO_EMPIRICAL_FAMILY_OR_SIGNIFICANCE_CERTIFICATION"},{"branch":"COMPLETE_FAMILY_CENTERED_STATIONARY_REPLAY","case":"four_rows","cells":[{"candidate":"3fe8000000000000","kind":"FSUM","operands_json":"[\\"3fd0000000000000\\",\\"bfd0000000000000\\",\\"3fe8000000000000\\",\\"0000000000000000\\"]","operation":"SUM_0"},{"candidate":"3fc8000000000000","kind":"DIV","operands_json":"[\\"3fe8000000000000\\",\\"4010000000000000\\"]","operation":"MEAN_0"},{"candidate":"0000000000000000","kind":"FSUM","operands_json":"[\\"bfe0000000000000\\",\\"3fd0000000000000\\",\\"3fe0000000000000\\",\\"bfd0000000000000\\"]","operation":"SUM_1"},{"candidate":"0000000000000000","kind":"DIV","operands_json":"[\\"0000000000000000\\",\\"4010000000000000\\"]","operation":"MEAN_1"},{"candidate":"4000000000000000","kind":"SQRT","operands_json":"[\\"4010000000000000\\"]","operation":"SQRT_N"},{"candidate":"3fd8000000000000","kind":"MUL","operands_json":"[\\"4000000000000000\\",\\"3fc8000000000000\\"]","operation":"OBSERVED_0"},{"candidate":"0000000000000000","kind":"MUL","operands_json":"[\\"4000000000000000\\",\\"0000000000000000\\"]","operation":"OBSERVED_1"},{"candidate":"3fe0000000000000","kind":"DIV","operands_json":"[\\"3ff0000000000000\\",\\"4000000000000000\\"]","operation":"RESTART_THRESHOLD"},{"candidate":"3fe8000000000000","kind":"FSUM","operands_json":"[\\"bfd0000000000000\\",\\"3fe8000000000000\\",\\"0000000000000000\\",\\"3fd0000000000000\\"]","operation":"REPLICATE_0_SUM_0"},{"candidate":"3fc8000000000000","kind":"DIV","operands_json":"[\\"3fe8000000000000\\",\\"4010000000000000\\"]","operation":"REPLICATE_0_MEAN_0"},{"candidate":"0000000000000000","kind":"SUB","operands_json":"[\\"3fc8000000000000\\",\\"3fc8000000000000\\"]","operation":"REPLICATE_0_CENTER_0"},{"candidate":"0000000000000000","kind":"MUL","operands_json":"[\\"4000000000000000\\",\\"0000000000000000\\"]","operation":"REPLICATE_0_STATISTIC_0"},{"candidate":"0000000000000000","kind":"FSUM","operands_json":"[\\"3fd0000000000000\\",\\"3fe0000000000000\\",\\"bfd0000000000000\\",\\"bfe0000000000000\\"]","operation":"REPLICATE_0_SUM_1"},{"candidate":"0000000000000000","kind":"DIV","operands_json":"[\\"0000000000000000\\",\\"4010000000000000\\"]","operation":"REPLICATE_0_MEAN_1"},{"candidate":"0000000000000000","kind":"SUB","operands_json":"[\\"0000000000000000\\",\\"0000000000000000\\"]","operation":"REPLICATE_0_CENTER_1"},{"candidate":"0000000000000000","kind":"MUL","operands_json":"[\\"4000000000000000\\",\\"0000000000000000\\"]","operation":"REPLICATE_0_STATISTIC_1"},{"candidate":"3fe0000000000000","kind":"FSUM","operands_json":"[\\"3fd0000000000000\\",\\"bfd0000000000000\\",\\"3fe8000000000000\\",\\"bfd0000000000000\\"]","operation":"REPLICATE_1_SUM_0"},{"candidate":"3fc0000000000000","kind":"DIV","operands_json":"[\\"3fe0000000000000\\",\\"4010000000000000\\"]","operation":"REPLICATE_1_MEAN_0"},{"candidate":"bfb0000000000000","kind":"SUB","operands_json":"[\\"3fc0000000000000\\",\\"3fc8000000000000\\"]","operation":"REPLICATE_1_CENTER_0"},{"candidate":"bfc0000000000000","kind":"MUL","operands_json":"[\\"4000000000000000\\",\\"bfb0000000000000\\"]","operation":"REPLICATE_1_STATISTIC_0"},{"candidate":"3fe0000000000000","kind":"FSUM","operands_json":"[\\"bfe0000000000000\\",\\"3fd0000000000000\\",\\"3fe0000000000000\\",\\"3fd0000000000000\\"]","operation":"REPLICATE_1_SUM_1"},{"candidate":"3fc0000000000000","kind":"DIV","operands_json":"[\\"3fe0000000000000\\",\\"4010000000000000\\"]","operation":"REPLICATE_1_MEAN_1"},{"candidate":"3fc0000000000000","kind":"SUB","operands_json":"[\\"3fc0000000000000\\",\\"0000000000000000\\"]","operation":"REPLICATE_1_CENTER_1"},{"candidate":"3fd0000000000000","kind":"MUL","operands_json":"[\\"4000000000000000\\",\\"3fc0000000000000\\"]","operation":"REPLICATE_1_STATISTIC_1"},{"candidate":"3fd5555555555555","kind":"DIV","operands_json":"[\\"3ff0000000000000\\",\\"4008000000000000\\"]","operation":"PLUS_ONE_P_VALUE"}],"derived_indices":[[1,2,3,0],[0,1,2,1]],"draws":[{"comparison":"4","disposition":"SELECTED","method":"GETRANDBITS","ordinal":0,"position":0,"replicate":0,"value":1,"width":3},{"comparison":"3fe0000000000000","disposition":"CONTINUE","method":"RANDOM_U53","ordinal":1,"position":1,"replicate":0,"value":5338034768530029,"width":53},{"comparison":"3fe0000000000000","disposition":"RESTART","method":"RANDOM_U53","ordinal":2,"position":2,"replicate":0,"value":1174744111699334,"width":53},{"comparison":"4","disposition":"REJECTED","method":"GETRANDBITS","ordinal":3,"position":2,"replicate":0,"value":7,"width":3},{"comparison":"4","disposition":"REJECTED","method":"GETRANDBITS","ordinal":4,"position":2,"replicate":0,"value":4,"width":3},{"comparison":"4","disposition":"SELECTED","method":"GETRANDBITS","ordinal":5,"position":2,"replicate":0,"value":3,"width":3},{"comparison":"3fe0000000000000","disposition":"CONTINUE","method":"RANDOM_U53","ordinal":6,"position":3,"replicate":0,"value":5635987456838371,"width":53},{"comparison":"4","disposition":"SELECTED","method":"GETRANDBITS","ordinal":7,"position":0,"replicate":1,"value":0,"width":3},{"comparison":"3fe0000000000000","disposition":"CONTINUE","method":"RANDOM_U53","ordinal":8,"position":1,"replicate":1,"value":5454755636542440,"width":53},{"comparison":"3fe0000000000000","disposition":"CONTINUE","method":"RANDOM_U53","ordinal":9,"position":2,"replicate":1,"value":8185908416844158,"width":53},{"comparison":"3fe0000000000000","disposition":"RESTART","method":"RANDOM_U53","ordinal":10,"position":3,"replicate":1,"value":4226469161702425,"width":53},{"comparison":"4","disposition":"REJECTED","method":"GETRANDBITS","ordinal":11,"position":3,"replicate":1,"value":4,"width":3},{"comparison":"4","disposition":"SELECTED","method":"GETRANDBITS","ordinal":12,"position":3,"replicate":1,"value":1,"width":3}],"exceedances":0,"inputs":{"alpha":0.5,"expected_block_length":2.0,"loss_differentials":[[0.25,-0.5],[-0.25,0.25],[0.75,0.5],[0.0,-0.25]],"replicates":2,"seed":3,"sign_convention":"BENCHMARK_LOSS_MINUS_CANDIDATE_LOSS_POSITIVE_IS_BETTER"},"mt_words":[1022050301,2545373330,2337446730,560161641,1588945316,3933953013,2593816829,2036044446,2687448230,2494740733,281444313,2601030205,56556069,3903345311,3596902313,2015337560,1113916996,2365602028,1006443827],"observation_scope":"ALL_FORMULA_INTERMEDIATES_DERIVED_NOT_OBSERVED","observed_selected_column":0,"oriented_matrix_bits":[["3fd0000000000000","bfe0000000000000"],["bfd0000000000000","3fd0000000000000"],["3fe8000000000000","3fe0000000000000"],["0000000000000000","bfd0000000000000"]],"raw":{"candidate_means":[0.1875,0.0],"p_value":0.3333333333333333,"recenter_policy":"CENTER_EACH_COMPLETE_MATERIAL_CANDIDATE_AT_ITS_SAMPLE_MEAN","reject":true,"simulated_statistics":[0.0,0.25],"statistic":0.375},"raw_json":"{\\"candidate_means\\":[0.1875,0.0],\\"p_value\\":0.3333333333333333,\\"recenter_policy\\":\\"CENTER_EACH_COMPLETE_MATERIAL_CANDIDATE_AT_ITS_SAMPLE_MEAN\\",\\"reject\\":true,\\"simulated_statistics\\":[0.0,0.25],\\"statistic\\":0.375}","replicate_selected_columns":[-1,1],"statistical_authority":"NO_EMPIRICAL_FAMILY_OR_SIGNIFICANCE_CERTIFICATION"},{"branch":"COMPLETE_FAMILY_CENTERED_STATIONARY_REPLAY","case":"three_rows","cells":[{"candidate":"3fe0000000000000","kind":"FSUM","operands_json":"[\\"3fd0000000000000\\",\\"3fe8000000000000\\",\\"bfe0000000000000\\"]","operation":"SUM_0"},{"candidate":"3fc5555555555555","kind":"DIV","operands_json":"[\\"3fe0000000000000\\",\\"4008000000000000\\"]","operation":"MEAN_0"},{"candidate":"3fe0000000000000","kind":"FSUM","operands_json":"[\\"bfd0000000000000\\",\\"3fd0000000000000\\",\\"3fe0000000000000\\"]","operation":"SUM_1"},{"candidate":"3fc5555555555555","kind":"DIV","operands_json":"[\\"3fe0000000000000\\",\\"4008000000000000\\"]","operation":"MEAN_1"},{"candidate":"3ffbb67ae8584caa","kind":"SQRT","operands_json":"[\\"4008000000000000\\"]","operation":"SQRT_N"},{"candidate":"3fd279a74590331c","kind":"MUL","operands_json":"[\\"3ffbb67ae8584caa\\",\\"3fc5555555555555\\"]","operation":"OBSERVED_0"},{"candidate":"3fd279a74590331c","kind":"MUL","operands_json":"[\\"3ffbb67ae8584caa\\",\\"3fc5555555555555\\"]","operation":"OBSERVED_1"},{"candidate":"3fd5555555555555","kind":"DIV","operands_json":"[\\"3ff0000000000000\\",\\"4008000000000000\\"]","operation":"RESTART_THRESHOLD"},{"candidate":"3fe0000000000000","kind":"FSUM","operands_json":"[\\"3fe8000000000000\\",\\"bfe0000000000000\\",\\"3fd0000000000000\\"]","operation":"REPLICATE_0_SUM_0"},{"candidate":"3fc5555555555555","kind":"DIV","operands_json":"[\\"3fe0000000000000\\",\\"4008000000000000\\"]","operation":"REPLICATE_0_MEAN_0"},{"candidate":"0000000000000000","kind":"SUB","operands_json":"[\\"3fc5555555555555\\",\\"3fc5555555555555\\"]","operation":"REPLICATE_0_CENTER_0"},{"candidate":"0000000000000000","kind":"MUL","operands_json":"[\\"3ffbb67ae8584caa\\",\\"0000000000000000\\"]","operation":"REPLICATE_0_STATISTIC_0"},{"candidate":"3fe0000000000000","kind":"FSUM","operands_json":"[\\"3fd0000000000000\\",\\"3fe0000000000000\\",\\"bfd0000000000000\\"]","operation":"REPLICATE_0_SUM_1"},{"candidate":"3fc5555555555555","kind":"DIV","operands_json":"[\\"3fe0000000000000\\",\\"4008000000000000\\"]","operation":"REPLICATE_0_MEAN_1"},{"candidate":"0000000000000000","kind":"SUB","operands_json":"[\\"3fc5555555555555\\",\\"3fc5555555555555\\"]","operation":"REPLICATE_0_CENTER_1"},{"candidate":"0000000000000000","kind":"MUL","operands_json":"[\\"3ffbb67ae8584caa\\",\\"0000000000000000\\"]","operation":"REPLICATE_0_STATISTIC_1"},{"candidate":"3fe0000000000000","kind":"FSUM","operands_json":"[\\"3fd0000000000000\\",\\"3fe8000000000000\\",\\"bfe0000000000000\\"]","operation":"REPLICATE_1_SUM_0"},{"candidate":"3fc5555555555555","kind":"DIV","operands_json":"[\\"3fe0000000000000\\",\\"4008000000000000\\"]","operation":"REPLICATE_1_MEAN_0"},{"candidate":"0000000000000000","kind":"SUB","operands_json":"[\\"3fc5555555555555\\",\\"3fc5555555555555\\"]","operation":"REPLICATE_1_CENTER_0"},{"candidate":"0000000000000000","kind":"MUL","operands_json":"[\\"3ffbb67ae8584caa\\",\\"0000000000000000\\"]","operation":"REPLICATE_1_STATISTIC_0"},{"candidate":"3fe0000000000000","kind":"FSUM","operands_json":"[\\"bfd0000000000000\\",\\"3fd0000000000000\\",\\"3fe0000000000000\\"]","operation":"REPLICATE_1_SUM_1"},{"candidate":"3fc5555555555555","kind":"DIV","operands_json":"[\\"3fe0000000000000\\",\\"4008000000000000\\"]","operation":"REPLICATE_1_MEAN_1"},{"candidate":"0000000000000000","kind":"SUB","operands_json":"[\\"3fc5555555555555\\",\\"3fc5555555555555\\"]","operation":"REPLICATE_1_CENTER_1"},{"candidate":"0000000000000000","kind":"MUL","operands_json":"[\\"3ffbb67ae8584caa\\",\\"0000000000000000\\"]","operation":"REPLICATE_1_STATISTIC_1"},{"candidate":"3fd5555555555555","kind":"DIV","operands_json":"[\\"3ff0000000000000\\",\\"4008000000000000\\"]","operation":"PLUS_ONE_P_VALUE"}],"derived_indices":[[1,2,0],[0,1,2]],"draws":[{"comparison":"3","disposition":"SELECTED","method":"GETRANDBITS","ordinal":0,"position":0,"replicate":0,"value":1,"width":2},{"comparison":"3fd5555555555555","disposition":"RESTART","method":"RANDOM_U53","ordinal":1,"position":1,"replicate":0,"value":2618912457733189,"width":53},{"comparison":"3","disposition":"REJECTED","method":"GETRANDBITS","ordinal":2,"position":1,"replicate":0,"value":3,"width":2},{"comparison":"3","disposition":"SELECTED","method":"GETRANDBITS","ordinal":3,"position":1,"replicate":0,"value":2,"width":2},{"comparison":"3fd5555555555555","disposition":"CONTINUE","method":"RANDOM_U53","ordinal":4,"position":2,"replicate":0,"value":7223815744895072,"width":53},{"comparison":"3","disposition":"REJECTED","method":"GETRANDBITS","ordinal":5,"position":0,"replicate":1,"value":3,"width":2},{"comparison":"3","disposition":"SELECTED","method":"GETRANDBITS","ordinal":6,"position":0,"replicate":1,"value":0,"width":2},{"comparison":"3fd5555555555555","disposition":"CONTINUE","method":"RANDOM_U53","ordinal":7,"position":1,"replicate":1,"value":5872781529716622,"width":53},{"comparison":"3fd5555555555555","disposition":"CONTINUE","method":"RANDOM_U53","ordinal":8,"position":2,"replicate":1,"value":6000466069991702,"width":53}],"exceedances":0,"inputs":{"alpha":0.5,"expected_block_length":3.0,"loss_differentials":[[0.25,-0.25],[0.75,0.25],[-0.5,0.5]],"replicates":2,"seed":13,"sign_convention":"BENCHMARK_LOSS_MINUS_CANDIDATE_LOSS_POSITIVE_IS_BETTER"},"mt_words":[1112433019,1248794762,2943160652,3906445129,2938109453,3444583746,3647871021,3822511289,797679261,2800360461,990241682,2861245199,632047008],"observation_scope":"ALL_FORMULA_INTERMEDIATES_DERIVED_NOT_OBSERVED","observed_selected_column":0,"oriented_matrix_bits":[["3fd0000000000000","bfd0000000000000"],["3fe8000000000000","3fd0000000000000"],["bfe0000000000000","3fe0000000000000"]],"raw":{"candidate_means":[0.16666666666666666,0.16666666666666666],"p_value":0.3333333333333333,"recenter_policy":"CENTER_EACH_COMPLETE_MATERIAL_CANDIDATE_AT_ITS_SAMPLE_MEAN","reject":true,"simulated_statistics":[0.0,0.0],"statistic":0.28867513459481287},"raw_json":"{\\"candidate_means\\":[0.16666666666666666,0.16666666666666666],\\"p_value\\":0.3333333333333333,\\"recenter_policy\\":\\"CENTER_EACH_COMPLETE_MATERIAL_CANDIDATE_AT_ITS_SAMPLE_MEAN\\",\\"reject\\":true,\\"simulated_statistics\\":[0.0,0.0],\\"statistic\\":0.28867513459481287}","replicate_selected_columns":[-1,-1],"statistical_authority":"NO_EMPIRICAL_FAMILY_OR_SIGNIFICANCE_CERTIFICATION"},{"branch":"COMPLETE_FAMILY_CENTERED_STATIONARY_REPLAY","case":"minimum_subnormal","cells":[{"candidate":"8000000000000001","kind":"FSUM","operands_json":"[\\"8000000000000001\\",\\"0000000000000000\\"]","operation":"SUM_0"},{"candidate":"8000000000000000","kind":"DIV","operands_json":"[\\"8000000000000001\\",\\"4000000000000000\\"]","operation":"MEAN_0"},{"candidate":"3ff6a09e667f3bcd","kind":"SQRT","operands_json":"[\\"4000000000000000\\"]","operation":"SQRT_N"},{"candidate":"8000000000000000","kind":"MUL","operands_json":"[\\"3ff6a09e667f3bcd\\",\\"8000000000000000\\"]","operation":"OBSERVED_0"},{"candidate":"3fe0000000000000","kind":"DIV","operands_json":"[\\"3ff0000000000000\\",\\"4000000000000000\\"]","operation":"RESTART_THRESHOLD"},{"candidate":"8000000000000001","kind":"FSUM","operands_json":"[\\"0000000000000000\\",\\"8000000000000001\\"]","operation":"REPLICATE_0_SUM_0"},{"candidate":"8000000000000000","kind":"DIV","operands_json":"[\\"8000000000000001\\",\\"4000000000000000\\"]","operation":"REPLICATE_0_MEAN_0"},{"candidate":"0000000000000000","kind":"SUB","operands_json":"[\\"8000000000000000\\",\\"8000000000000000\\"]","operation":"REPLICATE_0_CENTER_0"},{"candidate":"0000000000000000","kind":"MUL","operands_json":"[\\"3ff6a09e667f3bcd\\",\\"0000000000000000\\"]","operation":"REPLICATE_0_STATISTIC_0"},{"candidate":"8000000000000001","kind":"FSUM","operands_json":"[\\"0000000000000000\\",\\"8000000000000001\\"]","operation":"REPLICATE_1_SUM_0"},{"candidate":"8000000000000000","kind":"DIV","operands_json":"[\\"8000000000000001\\",\\"4000000000000000\\"]","operation":"REPLICATE_1_MEAN_0"},{"candidate":"0000000000000000","kind":"SUB","operands_json":"[\\"8000000000000000\\",\\"8000000000000000\\"]","operation":"REPLICATE_1_CENTER_0"},{"candidate":"0000000000000000","kind":"MUL","operands_json":"[\\"3ff6a09e667f3bcd\\",\\"0000000000000000\\"]","operation":"REPLICATE_1_STATISTIC_0"},{"candidate":"3ff0000000000000","kind":"DIV","operands_json":"[\\"4008000000000000\\",\\"4008000000000000\\"]","operation":"PLUS_ONE_P_VALUE"}],"derived_indices":[[1,0],[1,0]],"draws":[{"comparison":"2","disposition":"SELECTED","method":"GETRANDBITS","ordinal":0,"position":0,"replicate":0,"value":1,"width":2},{"comparison":"3fe0000000000000","disposition":"CONTINUE","method":"RANDOM_U53","ordinal":1,"position":1,"replicate":0,"value":8537612169672756,"width":53},{"comparison":"2","disposition":"SELECTED","method":"GETRANDBITS","ordinal":2,"position":0,"replicate":1,"value":1,"width":2},{"comparison":"3fe0000000000000","disposition":"CONTINUE","method":"RANDOM_U53","ordinal":3,"position":1,"replicate":1,"value":5863096500449791,"width":53}],"exceedances":2,"inputs":{"alpha":0.5,"expected_block_length":2.0,"loss_differentials":[[-5e-324],[0.0]],"replicates":2,"seed":7,"sign_convention":"BENCHMARK_LOSS_MINUS_CANDIDATE_LOSS_POSITIVE_IS_BETTER"},"mt_words":[1390851128,4071050724,647892279,1695753998,2795742288,207388624],"observation_scope":"ALL_FORMULA_INTERMEDIATES_DERIVED_NOT_OBSERVED","observed_selected_column":-1,"oriented_matrix_bits":[["8000000000000001"],["0000000000000000"]],"raw":{"candidate_means":[-0.0],"p_value":1.0,"recenter_policy":"CENTER_EACH_COMPLETE_MATERIAL_CANDIDATE_AT_ITS_SAMPLE_MEAN","reject":false,"simulated_statistics":[0.0,0.0],"statistic":0.0},"raw_json":"{\\"candidate_means\\":[-0.0],\\"p_value\\":1.0,\\"recenter_policy\\":\\"CENTER_EACH_COMPLETE_MATERIAL_CANDIDATE_AT_ITS_SAMPLE_MEAN\\",\\"reject\\":false,\\"simulated_statistics\\":[0.0,0.0],\\"statistic\\":0.0}","replicate_selected_columns":[-1,-1],"statistical_authority":"NO_EMPIRICAL_FAMILY_OR_SIGNIFICANCE_CERTIFICATION"},{"branch":"COMPLETE_FAMILY_CENTERED_STATIONARY_REPLAY","case":"plus_one_boundary","cells":[{"candidate":"3ff0000000000000","kind":"FSUM","operands_json":"[\\"3fd0000000000000\\",\\"3fe8000000000000\\"]","operation":"SUM_0"},{"candidate":"3fe0000000000000","kind":"DIV","operands_json":"[\\"3ff0000000000000\\",\\"4000000000000000\\"]","operation":"MEAN_0"},{"candidate":"3ff6a09e667f3bcd","kind":"SQRT","operands_json":"[\\"4000000000000000\\"]","operation":"SQRT_N"},{"candidate":"3fe6a09e667f3bcd","kind":"MUL","operands_json":"[\\"3ff6a09e667f3bcd\\",\\"3fe0000000000000\\"]","operation":"OBSERVED_0"},{"candidate":"3fe0000000000000","kind":"DIV","operands_json":"[\\"3ff0000000000000\\",\\"4000000000000000\\"]","operation":"RESTART_THRESHOLD"},{"candidate":"3ff0000000000000","kind":"FSUM","operands_json":"[\\"3fe8000000000000\\",\\"3fd0000000000000\\"]","operation":"REPLICATE_0_SUM_0"},{"candidate":"3fe0000000000000","kind":"DIV","operands_json":"[\\"3ff0000000000000\\",\\"4000000000000000\\"]","operation":"REPLICATE_0_MEAN_0"},{"candidate":"0000000000000000","kind":"SUB","operands_json":"[\\"3fe0000000000000\\",\\"3fe0000000000000\\"]","operation":"REPLICATE_0_CENTER_0"},{"candidate":"0000000000000000","kind":"MUL","operands_json":"[\\"3ff6a09e667f3bcd\\",\\"0000000000000000\\"]","operation":"REPLICATE_0_STATISTIC_0"},{"candidate":"3ff8000000000000","kind":"FSUM","operands_json":"[\\"3fe8000000000000\\",\\"3fe8000000000000\\"]","operation":"REPLICATE_1_SUM_0"},{"candidate":"3fe8000000000000","kind":"DIV","operands_json":"[\\"3ff8000000000000\\",\\"4000000000000000\\"]","operation":"REPLICATE_1_MEAN_0"},{"candidate":"3fd0000000000000","kind":"SUB","operands_json":"[\\"3fe8000000000000\\",\\"3fe0000000000000\\"]","operation":"REPLICATE_1_CENTER_0"},{"candidate":"3fd6a09e667f3bcd","kind":"MUL","operands_json":"[\\"3ff6a09e667f3bcd\\",\\"3fd0000000000000\\"]","operation":"REPLICATE_1_STATISTIC_0"},{"candidate":"3fd5555555555555","kind":"DIV","operands_json":"[\\"3ff0000000000000\\",\\"4008000000000000\\"]","operation":"PLUS_ONE_P_VALUE"}],"derived_indices":[[1,0],[1,1]],"draws":[{"comparison":"2","disposition":"REJECTED","method":"GETRANDBITS","ordinal":0,"position":0,"replicate":0,"value":3,"width":2},{"comparison":"2","disposition":"SELECTED","method":"GETRANDBITS","ordinal":1,"position":0,"replicate":0,"value":1,"width":2},{"comparison":"3fe0000000000000","disposition":"CONTINUE","method":"RANDOM_U53","ordinal":2,"position":1,"replicate":0,"value":6827046333291546,"width":53},{"comparison":"2","disposition":"SELECTED","method":"GETRANDBITS","ordinal":3,"position":0,"replicate":1,"value":1,"width":2},{"comparison":"3fe0000000000000","disposition":"RESTART","method":"RANDOM_U53","ordinal":4,"position":1,"replicate":1,"value":364650860978552,"width":53},{"comparison":"2","disposition":"REJECTED","method":"GETRANDBITS","ordinal":5,"position":1,"replicate":1,"value":3,"width":2},{"comparison":"2","disposition":"REJECTED","method":"GETRANDBITS","ordinal":6,"position":1,"replicate":1,"value":2,"width":2},{"comparison":"2","disposition":"SELECTED","method":"GETRANDBITS","ordinal":7,"position":1,"replicate":1,"value":1,"width":2}],"exceedances":0,"inputs":{"alpha":0.3333333333333333,"expected_block_length":2.0,"loss_differentials":[[0.25],[0.75]],"replicates":2,"seed":0,"sign_convention":"BENCHMARK_LOSS_MINUS_CANDIDATE_LOSS_POSITIVE_IS_BETTER"},"mt_words":[3626764237,1654615998,3255389356,3823568514,1806341205,173879092,1112038970,4146640122,2195908194,2087043557],"observation_scope":"ALL_FORMULA_INTERMEDIATES_DERIVED_NOT_OBSERVED","observed_selected_column":0,"oriented_matrix_bits":[["3fd0000000000000"],["3fe8000000000000"]],"raw":{"candidate_means":[0.5],"p_value":0.3333333333333333,"recenter_policy":"CENTER_EACH_COMPLETE_MATERIAL_CANDIDATE_AT_ITS_SAMPLE_MEAN","reject":true,"simulated_statistics":[0.0,0.3535533905932738],"statistic":0.7071067811865476},"raw_json":"{\\"candidate_means\\":[0.5],\\"p_value\\":0.3333333333333333,\\"recenter_policy\\":\\"CENTER_EACH_COMPLETE_MATERIAL_CANDIDATE_AT_ITS_SAMPLE_MEAN\\",\\"reject\\":true,\\"simulated_statistics\\":[0.0,0.3535533905932738],\\"statistic\\":0.7071067811865476}","replicate_selected_columns":[-1,0],"statistical_authority":"NO_EMPIRICAL_FAMILY_OR_SIGNIFICANCE_CERTIFICATION"}]')
    def projection(value):
        return MappingProxyType(dict(value, candidate_means=tuple(value["candidate_means"]), simulated_statistics=tuple(value["simulated_statistics"])))
    def run(selected, work, *, inputs=None, raw=None, expected=None, projected=None, expected_environment=None):
        return IndependentEvidenceReviewV1._bounded_review_reality_check_v1(
            deterministic_json(selected["inputs"] if inputs is None else inputs).encode("utf-8"),
            deterministic_json(selected["raw"] if raw is None else raw).encode("utf-8"),
            deterministic_json(selected["raw"] if expected is None else expected).encode("utf-8"),
            projection(selected["raw"]) if projected is None else projected,
            expected_environment=environment if expected_environment is None else expected_environment, work=work)
    def forbidden(*args, **kwargs):
        raise AssertionError("independent reality-check model invoked formula, resampler, fsum or sqrt")
    positives = []
    with ExitStack() as stack:
        for name in ("compute_math_15_white_reality_check", "compute_math_15_white_reality_check_v2", "_stationary_indices", "_v34_mean"):
            stack.enter_context(patch.object(formulas, name, forbidden))
        for name in ("fsum", "sqrt"):
            stack.enter_context(patch.object(math, name, forbidden))
        for selected in cases:
            work = _EvidenceNumericalWorkV1(limits, retained_input_capacity=0)
            if selected["case"] == "all_zero":
                with patch.object(random, "Random", forbidden):proof = run(selected, work)
            else:proof = run(selected, work)
            first = dict(work.consumed)
            assert work.state == "OPEN" and len(proof["cells"]) <= 41
            assert list(proof["cells"]) == selected["cells"] and list(proof["draws"]) == selected["draws"]
            for name, key in (("indices", "derived_indices"), ("oriented_matrix_bits", "oriented_matrix_bits"),
                    ("observed_selected_column", "observed_selected_column"), ("replicate_selected_columns", "replicate_selected_columns")):
                assert deterministic_json(proof[name]) == deterministic_json(selected[key])
            assert proof["branch"] == selected["branch"] and proof["summary"]["original_raw_json"] == selected["raw_json"]
            assert first["random_draws"] == len(selected["draws"])
            assert first["serialized_bytes"] == sum(len(deterministic_json(value).encode("utf-8")) for value in
                [*proof["cells"], *proof["draws"], proof["summary"], proof])
            repetitions = 2 if selected["case"] in ("two_candidates", "all_zero", "minimum_subnormal") else 1
            if repetitions == 2:
                if selected["case"] == "all_zero":
                    with patch.object(random, "Random", forbidden):assert run(selected, work) == proof
                else:assert run(selected, work) == proof
                assert work.consumed["serialized_bytes"] == 2 * first["serialized_bytes"]
                assert work.consumed["random_draws"] == 2 * first["random_draws"]
            work._assert_bootstrap_custody_v1()
            assert len(work._bootstrap_invocations) == (0 if selected["case"] == "all_zero" else repetitions)
            assert first["square_roots"] == 1
            assert all(first[key] == 0 for key in ("log_series_terms", "decimal_constructions", "retained_decimal_inputs"))
            positives.append(dict(case=selected["case"], proof=proof, repetitions=repetitions,
                first_consumption=first, cumulative_consumption=dict(work.consumed)))
    base, zero_case = cases[0], cases[2]
    mutations = (
        ("boolean_seed", "inputs", dict(seed=True)),
        ("seed_bits", "inputs", dict(seed=2**256)),
        ("zero_replicates", "inputs", dict(replicates=0)),
        ("boolean_replicates", "inputs", dict(replicates=True)),
        ("replicate_bound", "inputs", dict(replicates=5)),
        ("one_time", "inputs", dict(loss_differentials=[[.25, -.25]])),
        ("too_many_times", "inputs", dict(loss_differentials=[[.25, -.25]] * 5)),
        ("too_many_candidates", "inputs", dict(loss_differentials=[[.25, -.25, .5], [.75, .25, .5]])),
        ("ragged_matrix", "inputs", dict(loss_differentials=[[.25, -.25], [.75]])),
        ("boolean_matrix", "inputs", dict(loss_differentials=[[True, -.25], [.75, .25]])),
        ("integer_matrix", "inputs", dict(loss_differentials=[[0, -.25], [.75, .25]])),
        ("matrix_domain", "inputs", dict(loss_differentials=[[1.0000000000000002, -.25], [.75, .25]])),
        ("sign_convention", "inputs", dict(sign_convention="POSITIVE")),
        ("block_low", "inputs", dict(expected_block_length=.5)),
        ("block_high", "inputs", dict(expected_block_length=3.0)),
        ("block_integer", "inputs", dict(expected_block_length=2)),
        ("alpha_zero", "inputs", dict(alpha=0.0)),
        ("alpha_one", "inputs", dict(alpha=1.0)),
        ("statistic_ulp", "raw", dict(statistic=math.nextafter(base["raw"]["statistic"], 1.0))),
        ("p_value_without_plus_one", "raw", dict(p_value=0.0)),
        ("wrong_reject", "raw", dict(reject=False)),
        ("integer_reject", "raw", dict(reject=1)),
        ("omitted_family_column", "raw", dict(candidate_means=[.5])),
        ("reordered_candidate_means", "raw", dict(candidate_means=[0.0,.5])),
        ("simulated_order", "raw", dict(simulated_statistics=list(reversed(base["raw"]["simulated_statistics"])))),
        ("recenter_policy", "raw", dict(recenter_policy="UNCENTERED")),
        ("expected_p_value", "expected", dict(p_value=.5)),
    )
    denials = []
    for name, field, changes in mutations:
        value = dict(base["inputs"] if field == "inputs" else base["raw"], **changes)
        work = _EvidenceNumericalWorkV1(limits, retained_input_capacity=0)
        with pytest.raises(ComputationControlPlaneError):run(base, work, **{field: value})
        assert work.state == "FAILED"
        if work._bootstrap_invocations:work._assert_bootstrap_custody_v1(failed=True)
        consumed = dict(work.consumed)
        with pytest.raises(ComputationControlPlaneError, match="LP03_NUMERICAL_WORK_NOT_OPEN"):run(base, work)
        assert dict(work.consumed) == consumed
        denials.append(dict(case=name, failure=work.failure, consumed=consumed))
    extras = (
        ("environment", base, {}, dict(expected_environment=replace(environment, build="different"))),
        ("projection_mutable", base, {}, dict(projected=dict(base["raw"]))),
        ("projection_reject", base, {}, dict(projected=projection(dict(base["raw"], reject=False)))),
        ("zero_budget", base, dict(max_serialized_bytes=0), {}),
        ("complete_bytes", base, dict(max_serialized_bytes=10000), {}),
        ("work_bits", base, dict(max_work_bits=1074), {}),
        ("input_bits", base, dict(max_input_bits=1), {}),
        ("all_zero_bad_seed", zero_case, {}, dict(inputs=dict(zero_case["inputs"], seed=True))),
        ("all_zero_clamp_sign", zero_case, {}, dict(raw=dict(zero_case["raw"], statistic=-0.0))),
        ("underflow_mean_sign", cases[6], {}, dict(raw=dict(cases[6]["raw"], candidate_means=[0.0]))),
    )
    for name, selected, changes, arguments in extras:
        work = _EvidenceNumericalWorkV1(dict(limits, **changes), retained_input_capacity=0)
        with pytest.raises(ComputationControlPlaneError):run(selected, work, **arguments)
        assert work.state == "FAILED"
        if work._bootstrap_invocations:work._assert_bootstrap_custody_v1(failed=True)
        denials.append(dict(case=name, failure=work.failure, consumed=dict(work.consumed)))
    # All-zero execution must preserve an existing original replay and its
    # counters. No constructor is needed, even after prior completed work.
    work = _EvidenceNumericalWorkV1(limits, retained_input_capacity=0)
    run(base, work);original = tuple(work._bootstrap_invocations);before = dict(work.consumed)
    with patch.object(random, "Random", forbidden):zero_proof = run(zero_case, work)
    assert len(original) == len(work._bootstrap_invocations) == 1 and work._bootstrap_invocations[0] is original[0]
    assert work.consumed["random_draws"] == before["random_draws"] and zero_proof["draws"] == ()
    original_work_zero = dict(before=before, after=dict(work.consumed), retained_invocations=1, proof=zero_proof)
    # The complete reserve for this call may fail first; use the prior valid
    # state in a fresh original work to expose the roster identity denial.
    custody = _EvidenceNumericalWorkV1(limits, retained_input_capacity=0)
    run(base, custody);record = custody._bootstrap_invocations[0]
    custody._bootstrap_invocations[0] = tuple(list(record))
    with pytest.raises(ComputationControlPlaneError, match="LP03_BOOTSTRAP_ORIGINAL_INVOCATION_ROSTER_REQUIRED"):
        run(zero_case, custody)
    assert custody.state == "FAILED" and custody.consumed["random_draws"] == 8
    custody._bootstrap_invocations[0] = record
    custody._assert_bootstrap_custody_v1(failed=True)
    denials.append(dict(case="all_zero_original_roster_substitution", failure=custody.failure, consumed=dict(custody.consumed)))
    work = _EvidenceNumericalWorkV1(limits, retained_input_capacity=0)
    run(base, work);run(base, work);before = dict(work.consumed);original = tuple(work._bootstrap_invocations)
    with pytest.raises(ComputationControlPlaneError, match="LP03_REALITY_CHECK_REVIEW_COMPLETE_BYTES_EXHAUSTED"):run(base, work)
    assert work.state == "FAILED" and dict(work.consumed) == before and len(work._bootstrap_invocations) == 2
    assert all(work._bootstrap_invocations[index] is row for index,row in enumerate(original))
    work._assert_bootstrap_custody_v1(failed=True)
    denials.append(dict(case="original_cumulative_allowance", failure=work.failure, consumed=dict(work.consumed), completed=2))
    cap = json.loads('{"branch":"COMPLETE_FAMILY_CENTERED_STATIONARY_REPLAY","case":"cap64","cells":[{"candidate":"3ff8000000000000","kind":"FSUM","operands_json":"[\\"0000000000000000\\",\\"3fd0000000000000\\",\\"3fe0000000000000\\",\\"3fe8000000000000\\"]","operation":"SUM_0"},{"candidate":"3fd8000000000000","kind":"DIV","operands_json":"[\\"3ff8000000000000\\",\\"4010000000000000\\"]","operation":"MEAN_0"},{"candidate":"4000000000000000","kind":"SQRT","operands_json":"[\\"4010000000000000\\"]","operation":"SQRT_N"},{"candidate":"3fe8000000000000","kind":"MUL","operands_json":"[\\"4000000000000000\\",\\"3fd8000000000000\\"]","operation":"OBSERVED_0"},{"candidate":"3ff0000000000000","kind":"DIV","operands_json":"[\\"3ff0000000000000\\",\\"3ff0000000000000\\"]","operation":"RESTART_THRESHOLD"},{"candidate":"3ff4000000000000","kind":"FSUM","operands_json":"[\\"3fe0000000000000\\",\\"0000000000000000\\",\\"3fe0000000000000\\",\\"3fd0000000000000\\"]","operation":"REPLICATE_0_SUM_0"},{"candidate":"3fd4000000000000","kind":"DIV","operands_json":"[\\"3ff4000000000000\\",\\"4010000000000000\\"]","operation":"REPLICATE_0_MEAN_0"},{"candidate":"bfb0000000000000","kind":"SUB","operands_json":"[\\"3fd4000000000000\\",\\"3fd8000000000000\\"]","operation":"REPLICATE_0_CENTER_0"},{"candidate":"bfc0000000000000","kind":"MUL","operands_json":"[\\"4000000000000000\\",\\"bfb0000000000000\\"]","operation":"REPLICATE_0_STATISTIC_0"},{"candidate":"3ffc000000000000","kind":"FSUM","operands_json":"[\\"3fe8000000000000\\",\\"3fd0000000000000\\",\\"3fd0000000000000\\",\\"3fe0000000000000\\"]","operation":"REPLICATE_1_SUM_0"},{"candidate":"3fdc000000000000","kind":"DIV","operands_json":"[\\"3ffc000000000000\\",\\"4010000000000000\\"]","operation":"REPLICATE_1_MEAN_0"},{"candidate":"3fb0000000000000","kind":"SUB","operands_json":"[\\"3fdc000000000000\\",\\"3fd8000000000000\\"]","operation":"REPLICATE_1_CENTER_0"},{"candidate":"3fc0000000000000","kind":"MUL","operands_json":"[\\"4000000000000000\\",\\"3fb0000000000000\\"]","operation":"REPLICATE_1_STATISTIC_0"},{"candidate":"3fe8000000000000","kind":"FSUM","operands_json":"[\\"3fd0000000000000\\",\\"3fd0000000000000\\",\\"3fd0000000000000\\",\\"0000000000000000\\"]","operation":"REPLICATE_2_SUM_0"},{"candidate":"3fc8000000000000","kind":"DIV","operands_json":"[\\"3fe8000000000000\\",\\"4010000000000000\\"]","operation":"REPLICATE_2_MEAN_0"},{"candidate":"bfc8000000000000","kind":"SUB","operands_json":"[\\"3fc8000000000000\\",\\"3fd8000000000000\\"]","operation":"REPLICATE_2_CENTER_0"},{"candidate":"bfd8000000000000","kind":"MUL","operands_json":"[\\"4000000000000000\\",\\"bfc8000000000000\\"]","operation":"REPLICATE_2_STATISTIC_0"},{"candidate":"4000000000000000","kind":"FSUM","operands_json":"[\\"3fe8000000000000\\",\\"0000000000000000\\",\\"3fe8000000000000\\",\\"3fe0000000000000\\"]","operation":"REPLICATE_3_SUM_0"},{"candidate":"3fe0000000000000","kind":"DIV","operands_json":"[\\"4000000000000000\\",\\"4010000000000000\\"]","operation":"REPLICATE_3_MEAN_0"},{"candidate":"3fc0000000000000","kind":"SUB","operands_json":"[\\"3fe0000000000000\\",\\"3fd8000000000000\\"]","operation":"REPLICATE_3_CENTER_0"},{"candidate":"3fd0000000000000","kind":"MUL","operands_json":"[\\"4000000000000000\\",\\"3fc0000000000000\\"]","operation":"REPLICATE_3_STATISTIC_0"},{"candidate":"3fc999999999999a","kind":"DIV","operands_json":"[\\"3ff0000000000000\\",\\"4014000000000000\\"]","operation":"PLUS_ONE_P_VALUE"}],"derived_indices":[[2,0,2,1],[3,1,1,2],[1,1,1,0],[3,0,3,2]],"draws":[{"comparison":"4","disposition":"REJECTED","method":"GETRANDBITS","ordinal":0,"position":0,"replicate":0,"value":4,"width":3},{"comparison":"4","disposition":"SELECTED","method":"GETRANDBITS","ordinal":1,"position":0,"replicate":0,"value":2,"width":3},{"comparison":"3ff0000000000000","disposition":"RESTART","method":"RANDOM_U53","ordinal":2,"position":1,"replicate":0,"value":6672353513170771,"width":53},{"comparison":"4","disposition":"SELECTED","method":"GETRANDBITS","ordinal":3,"position":1,"replicate":0,"value":0,"width":3},{"comparison":"3ff0000000000000","disposition":"RESTART","method":"RANDOM_U53","ordinal":4,"position":2,"replicate":0,"value":2824969097079463,"width":53},{"comparison":"4","disposition":"REJECTED","method":"GETRANDBITS","ordinal":5,"position":2,"replicate":0,"value":7,"width":3},{"comparison":"4","disposition":"REJECTED","method":"GETRANDBITS","ordinal":6,"position":2,"replicate":0,"value":5,"width":3},{"comparison":"4","disposition":"REJECTED","method":"GETRANDBITS","ordinal":7,"position":2,"replicate":0,"value":4,"width":3},{"comparison":"4","disposition":"REJECTED","method":"GETRANDBITS","ordinal":8,"position":2,"replicate":0,"value":5,"width":3},{"comparison":"4","disposition":"REJECTED","method":"GETRANDBITS","ordinal":9,"position":2,"replicate":0,"value":7,"width":3},{"comparison":"4","disposition":"REJECTED","method":"GETRANDBITS","ordinal":10,"position":2,"replicate":0,"value":6,"width":3},{"comparison":"4","disposition":"REJECTED","method":"GETRANDBITS","ordinal":11,"position":2,"replicate":0,"value":4,"width":3},{"comparison":"4","disposition":"SELECTED","method":"GETRANDBITS","ordinal":12,"position":2,"replicate":0,"value":2,"width":3},{"comparison":"3ff0000000000000","disposition":"RESTART","method":"RANDOM_U53","ordinal":13,"position":3,"replicate":0,"value":5125821927941671,"width":53},{"comparison":"4","disposition":"REJECTED","method":"GETRANDBITS","ordinal":14,"position":3,"replicate":0,"value":4,"width":3},{"comparison":"4","disposition":"REJECTED","method":"GETRANDBITS","ordinal":15,"position":3,"replicate":0,"value":5,"width":3},{"comparison":"4","disposition":"REJECTED","method":"GETRANDBITS","ordinal":16,"position":3,"replicate":0,"value":5,"width":3},{"comparison":"4","disposition":"SELECTED","method":"GETRANDBITS","ordinal":17,"position":3,"replicate":0,"value":1,"width":3},{"comparison":"4","disposition":"SELECTED","method":"GETRANDBITS","ordinal":18,"position":0,"replicate":1,"value":3,"width":3},{"comparison":"3ff0000000000000","disposition":"RESTART","method":"RANDOM_U53","ordinal":19,"position":1,"replicate":1,"value":6374739605173293,"width":53},{"comparison":"4","disposition":"REJECTED","method":"GETRANDBITS","ordinal":20,"position":1,"replicate":1,"value":4,"width":3},{"comparison":"4","disposition":"REJECTED","method":"GETRANDBITS","ordinal":21,"position":1,"replicate":1,"value":7,"width":3},{"comparison":"4","disposition":"REJECTED","method":"GETRANDBITS","ordinal":22,"position":1,"replicate":1,"value":6,"width":3},{"comparison":"4","disposition":"REJECTED","method":"GETRANDBITS","ordinal":23,"position":1,"replicate":1,"value":7,"width":3},{"comparison":"4","disposition":"REJECTED","method":"GETRANDBITS","ordinal":24,"position":1,"replicate":1,"value":6,"width":3},{"comparison":"4","disposition":"REJECTED","method":"GETRANDBITS","ordinal":25,"position":1,"replicate":1,"value":6,"width":3},{"comparison":"4","disposition":"REJECTED","method":"GETRANDBITS","ordinal":26,"position":1,"replicate":1,"value":5,"width":3},{"comparison":"4","disposition":"REJECTED","method":"GETRANDBITS","ordinal":27,"position":1,"replicate":1,"value":7,"width":3},{"comparison":"4","disposition":"REJECTED","method":"GETRANDBITS","ordinal":28,"position":1,"replicate":1,"value":4,"width":3},{"comparison":"4","disposition":"REJECTED","method":"GETRANDBITS","ordinal":29,"position":1,"replicate":1,"value":5,"width":3},{"comparison":"4","disposition":"REJECTED","method":"GETRANDBITS","ordinal":30,"position":1,"replicate":1,"value":7,"width":3},{"comparison":"4","disposition":"REJECTED","method":"GETRANDBITS","ordinal":31,"position":1,"replicate":1,"value":6,"width":3},{"comparison":"4","disposition":"SELECTED","method":"GETRANDBITS","ordinal":32,"position":1,"replicate":1,"value":1,"width":3},{"comparison":"3ff0000000000000","disposition":"RESTART","method":"RANDOM_U53","ordinal":33,"position":2,"replicate":1,"value":3319397094041662,"width":53},{"comparison":"4","disposition":"REJECTED","method":"GETRANDBITS","ordinal":34,"position":2,"replicate":1,"value":5,"width":3},{"comparison":"4","disposition":"REJECTED","method":"GETRANDBITS","ordinal":35,"position":2,"replicate":1,"value":5,"width":3},{"comparison":"4","disposition":"REJECTED","method":"GETRANDBITS","ordinal":36,"position":2,"replicate":1,"value":4,"width":3},{"comparison":"4","disposition":"REJECTED","method":"GETRANDBITS","ordinal":37,"position":2,"replicate":1,"value":5,"width":3},{"comparison":"4","disposition":"SELECTED","method":"GETRANDBITS","ordinal":38,"position":2,"replicate":1,"value":1,"width":3},{"comparison":"3ff0000000000000","disposition":"RESTART","method":"RANDOM_U53","ordinal":39,"position":3,"replicate":1,"value":8685348348650618,"width":53},{"comparison":"4","disposition":"REJECTED","method":"GETRANDBITS","ordinal":40,"position":3,"replicate":1,"value":5,"width":3},{"comparison":"4","disposition":"SELECTED","method":"GETRANDBITS","ordinal":41,"position":3,"replicate":1,"value":2,"width":3},{"comparison":"4","disposition":"REJECTED","method":"GETRANDBITS","ordinal":42,"position":0,"replicate":2,"value":4,"width":3},{"comparison":"4","disposition":"SELECTED","method":"GETRANDBITS","ordinal":43,"position":0,"replicate":2,"value":1,"width":3},{"comparison":"3ff0000000000000","disposition":"RESTART","method":"RANDOM_U53","ordinal":44,"position":1,"replicate":2,"value":8122790624983867,"width":53},{"comparison":"4","disposition":"SELECTED","method":"GETRANDBITS","ordinal":45,"position":1,"replicate":2,"value":1,"width":3},{"comparison":"3ff0000000000000","disposition":"RESTART","method":"RANDOM_U53","ordinal":46,"position":2,"replicate":2,"value":5456080112443078,"width":53},{"comparison":"4","disposition":"REJECTED","method":"GETRANDBITS","ordinal":47,"position":2,"replicate":2,"value":7,"width":3},{"comparison":"4","disposition":"REJECTED","method":"GETRANDBITS","ordinal":48,"position":2,"replicate":2,"value":7,"width":3},{"comparison":"4","disposition":"SELECTED","method":"GETRANDBITS","ordinal":49,"position":2,"replicate":2,"value":1,"width":3},{"comparison":"3ff0000000000000","disposition":"RESTART","method":"RANDOM_U53","ordinal":50,"position":3,"replicate":2,"value":6429367834191314,"width":53},{"comparison":"4","disposition":"REJECTED","method":"GETRANDBITS","ordinal":51,"position":3,"replicate":2,"value":5,"width":3},{"comparison":"4","disposition":"REJECTED","method":"GETRANDBITS","ordinal":52,"position":3,"replicate":2,"value":7,"width":3},{"comparison":"4","disposition":"REJECTED","method":"GETRANDBITS","ordinal":53,"position":3,"replicate":2,"value":4,"width":3},{"comparison":"4","disposition":"REJECTED","method":"GETRANDBITS","ordinal":54,"position":3,"replicate":2,"value":4,"width":3},{"comparison":"4","disposition":"SELECTED","method":"GETRANDBITS","ordinal":55,"position":3,"replicate":2,"value":0,"width":3},{"comparison":"4","disposition":"REJECTED","method":"GETRANDBITS","ordinal":56,"position":0,"replicate":3,"value":5,"width":3},{"comparison":"4","disposition":"SELECTED","method":"GETRANDBITS","ordinal":57,"position":0,"replicate":3,"value":3,"width":3},{"comparison":"3ff0000000000000","disposition":"RESTART","method":"RANDOM_U53","ordinal":58,"position":1,"replicate":3,"value":3005305065223835,"width":53},{"comparison":"4","disposition":"SELECTED","method":"GETRANDBITS","ordinal":59,"position":1,"replicate":3,"value":0,"width":3},{"comparison":"3ff0000000000000","disposition":"RESTART","method":"RANDOM_U53","ordinal":60,"position":2,"replicate":3,"value":2251644347957803,"width":53},{"comparison":"4","disposition":"SELECTED","method":"GETRANDBITS","ordinal":61,"position":2,"replicate":3,"value":3,"width":3},{"comparison":"3ff0000000000000","disposition":"RESTART","method":"RANDOM_U53","ordinal":62,"position":3,"replicate":3,"value":3715359117590394,"width":53},{"comparison":"4","disposition":"REJECTED","method":"GETRANDBITS","ordinal":63,"position":3,"replicate":3,"value":5,"width":3},{"comparison":"4","disposition":"REJECTED","method":"GETRANDBITS","ordinal":64,"position":3,"replicate":3,"value":6,"width":3},{"comparison":"4","disposition":"SELECTED","method":"GETRANDBITS","ordinal":65,"position":3,"replicate":3,"value":2,"width":3}],"exceedances":0,"inputs":{"alpha":0.5,"expected_block_length":1.0,"loss_differentials":[[0.0],[0.25],[0.5],[0.75]],"replicates":4,"seed":211,"sign_convention":"BENCHMARK_LOSS_MINUS_CANDIDATE_LOSS_POSITIVE_IS_BETTER"},"mt_words":[2426209752,1534887359,3181626103,1039783140,90182474,1347050235,3793398221,3965145061,2714794848,2354471423,2800738770,3953375915,3630872045,2657129074,1472843118,2444182367,3432614385,2501576010,2910065370,2760822743,567525806,1787396809,3039712710,1827474253,2560985913,3775020680,3517991193,4264159436,3569466558,3702504945,2836816842,3905475147,2615913821,2715098091,3988300256,3491162230,765165997,1582811891,707399587,2972266105,2808394990,2211636749,2896169087,918617678,4141496810,3298369203,3078325679,1534214791,2317446078,1056176280,3873248405,1918815968,551390709,2601661749,1039643043,3876152625,4203882553,688326762,3065761495,2026468509,2735448034,4180032738,2245631930,2441264534,272196781,2844604069,1646219048,1433041143,917350133,299141031,1073667683,1632668383,2032472067,1771621282,447733418,2828446633,3515116339,1273237306],"observation_scope":"ALL_FORMULA_INTERMEDIATES_DERIVED_NOT_OBSERVED","observed_selected_column":0,"oriented_matrix_bits":[["0000000000000000"],["3fd0000000000000"],["3fe0000000000000"],["3fe8000000000000"]],"raw":{"candidate_means":[0.375],"p_value":0.2,"recenter_policy":"CENTER_EACH_COMPLETE_MATERIAL_CANDIDATE_AT_ITS_SAMPLE_MEAN","reject":true,"simulated_statistics":[0.0,0.125,0.0,0.25],"statistic":0.75},"raw_json":"{\\"candidate_means\\":[0.375],\\"p_value\\":0.2,\\"recenter_policy\\":\\"CENTER_EACH_COMPLETE_MATERIAL_CANDIDATE_AT_ITS_SAMPLE_MEAN\\",\\"reject\\":true,\\"simulated_statistics\\":[0.0,0.125,0.0,0.25],\\"statistic\\":0.75}","replicate_selected_columns":[-1,0,-1,0],"scope":"INDEPENDENT_M15_CAP_WITNESS_DRAFT_ONLY","seeds_examined":212,"statistical_authority":"NO_EMPIRICAL_FAMILY_OR_SIGNIFICANCE_CERTIFICATION"}')
    work = _EvidenceNumericalWorkV1(limits, retained_input_capacity=0)
    with pytest.raises(ComputationControlPlaneError, match="LP03_BOOTSTRAP_REPLAY_DRAW_LIMIT_EXHAUSTED"):run(cap, work)
    assert work.state == "FAILED" and work.consumed["random_draws"] == 64
    entry = work._bootstrap_invocations[0][0]
    assert len(entry.prefix) == 64 and entry.pending_request == ("GETRANDBITS", 3, 3, 3, 4, None, "4")
    assert [row[3] for row in entry.prefix] == [row["value"] for row in cap["draws"][:64]]
    work._assert_bootstrap_custody_v1(failed=True)
    denials.append(dict(case="retained_64_draws_unentered_65", failure=work.failure, consumed=dict(work.consumed),
        prefix=tuple(dict(ordinal=row[0], request=row[1], value=row[3], state=row[5]) for row in entry.prefix), pending_request=entry.pending_request))
    print("LP03_REALITY_CHECK_PURE_QUALIFICATION=" + deterministic_json(dict(
        scope="BOUNDED_REALITY_CHECK_MODEL_ONLY_NO_FAMILY_SOURCE_NATIVE_OR_SIGNIFICANCE_AUTHORITY",
        positives=positives, denials=denials, original_work_all_zero=original_work_zero)))




def _assert_lp03_bootstrap_signed_mt_data():
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.models import _evidence_bootstrap_mt_words_v1
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import ComputationControlPlaneError
    # Literals from the independent integer-state reference, including all
    # 128 words at the validator's boundary; no Random/producer generated them.
    vectors = (('two_point', 0, (3626764237, 1654615998, 3255389356, 3823568514, 1806341205, 173879092, 1112038970, 4146640122, 2195908194, 2087043557)), ('negative_seed', -1, (577090037, 2444712010, 3639700191, 3445702192, 3280387012, 271041745, 1095513148, 506456969, 2127877499, 3268308804, 1930549411, 2028277857, 2798570523, 1630434966, 3387541014, 901749037, 403123852, 2095328386, 121751464)), ('always_restart', 17, (2241903809, 1778837931, 3464710496, 1303193990, 4125293655, 1570340887, 1243931546, 750280511, 3290406397, 3028564149, 3024601294, 2320078575, 2840618605, 1195188523, 473142372, 3940602561, 115692582, 1069030695, 1650002322, 3501197581, 3205742961, 1802024078)), ('three_point', 13, (1112433019, 1248794762, 2943160652, 3906445129, 2938109453, 3444583746, 3647871021, 3822511289, 797679261, 2800360461, 990241682, 2861245199, 632047008, 3733318544, 967067425, 2752890056, 3152607373, 804765948, 559260700, 304199074, 2281979487, 3632642988, 918725831, 3198428526, 1265541136)), ('single_replicate', 2, (4106135923, 3707026329, 4070888059, 3646664648, 242886303, 393353683, 364522461, 1550730039)), ('signed_zero', 7, (1390851128, 4071050724, 647892279, 1695753998, 2795742288, 207388624)), ('negative_values', 3, (1022050301, 2545373330, 2337446730, 560161641, 1588945316, 3933953013, 2593816829, 2036044446, 2687448230, 2494740733, 281444313, 2601030205, 56556069, 3903345311, 3596902313, 2015337560, 1113916996, 2365602028, 1006443827, 823534631, 4276262006, 3080127366, 2019766388, 2323465141, 3592574581, 2360647895, 2045921456, 1705680002, 2744776746, 3698061793, 646892613, 996097414, 2726705791, 651213124, 3728226180, 3976433076, 2247046192, 1674765456)), ('wide_seed', 57896044618658097711785492504343953926634992332820282019728792003956564820091, (271236419, 2986030370, 779893860, 3508160949, 1724829902, 2944238293, 2172775280)), ('maximum_word_roster', 0, (3626764237, 1654615998, 3255389356, 3823568514, 1806341205, 173879092, 1112038970, 4146640122, 2195908194, 2087043557, 1739178872, 3943786419, 3366389305, 3564191072, 1302718217, 4156669319, 2046968324, 1537810351, 2505606783, 3829653368, 3900315155, 938204377, 2167613558, 598176026, 1210484339, 600203567, 3246154361, 407295012, 2655874620, 3433407905, 1075916535, 4240245955, 3907330410, 2287343378, 4221031477, 3028691745, 3479856542, 2585149702, 3874773259, 631194409, 1332073689, 424185324, 3134603515, 316721330, 3860481052, 3652757268, 2937688618, 1418186270, 2027837527, 2404381470, 432508404, 1519522183, 1864753826, 1358054485, 2623739577, 2750597567, 3921352636, 878225224, 4151542721, 2373071108, 2048741382, 1901353491, 3716477854, 2239196826, 1118805955, 267488770, 3457568186, 3944776678, 2356645542, 3934166345, 60308648, 400599612, 3091108076, 3608164305, 1712934065, 3050515222, 3542682188, 3371754448, 2869696129, 2685496293, 4908357, 2628077981, 2119900799, 3556504698, 3726325546, 1430804514, 1047589226, 3136522618, 1396742090, 3022121707, 3738645480, 270515404, 820626892, 3938566479, 2437440079, 952210990, 1024847607, 3450340716, 4155553746, 612008755, 3449629565, 2332124097, 1924014660, 391769539, 345512145, 4265854110, 1374624034, 3758471264, 2181588438, 4286255502, 4006490763, 2101470722, 468399889, 1294704107, 2367674807, 1250224899, 3034658173, 536057929, 2351240810, 1429152570, 3498108526, 3961032443, 2320500417, 872745308, 4139655026, 3433513287, 2590662546, 2350335399)))
    positives = []
    for name, seed, expected in vectors:
        words = _evidence_bootstrap_mt_words_v1(seed, len(expected))
        assert type(words) is tuple and words == expected and all(type(value) is int and 0 <= value < 2**32 for value in words)
        positives.append(dict(case=name, seed=seed, words=words))
    denials = []
    for name, seed, count in (("boolean_seed",True,1),("float_seed",0.0,1),("seed_positive_limit",2**256,1),
            ("seed_negative_limit",-2**256,1),("zero_words",0,0),("excess_words",0,129),("negative_words",0,-1),
            ("boolean_words",0,True),("float_words",0,1.0),("string_words",0,"1")):
        with pytest.raises(ComputationControlPlaneError, match="LP03_BOOTSTRAP_REVIEW_MT_DOMAIN") as caught:
            _evidence_bootstrap_mt_words_v1(seed, count)
        denials.append(dict(case=name, diagnostic=str(caught.value)))
    print("LP03_BOOTSTRAP_MT_DATA_VALIDATION_QUALIFICATION=" + deterministic_json(dict(
        scope="BOUNDED_INTEGER_MT_SIGNED_DATA_VALIDATOR_ONLY_NO_RNG_OBSERVATION", positives=positives, denials=denials)))


def _assert_lp03_bootstrap_ordered_model_proof():
    import json
    import math
    import random
    from contextlib import ExitStack
    from dataclasses import replace
    from types import MappingProxyType
    from unittest.mock import patch
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane import implementation_registry as formulas
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.evidence import IndependentEvidenceReviewV1
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.evidence_execution import _worker_environment_v1
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.parameter_policy import _EvidenceNumericalWorkV1
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import ComputationControlPlaneError
    limits = dict(max_input_bits=4096, max_work_bits=65536, max_serialized_bytes=65536)
    environment = _worker_environment_v1()
    def projection(value):
        return MappingProxyType(dict(value, bootstrap_distribution=tuple(value["bootstrap_distribution"])))
    # Independent 624-word integer MT reference and exact rational ordered
    # arithmetic supplied these literals; no QTT formula/proof created them.
    cases = json.loads('[{"case":"two_point","inputs":{"confidence":0.5,"expected_block_length":2.0,"interval_method":"PERCENTILE_TYPE7","replicates":2,"seed":0,"series":[0.25,0.75]},"raw":{"bootstrap_distribution":[0.5,0.75],"expected_block_length":2.0,"interval_method":"PERCENTILE_TYPE7","lower":0.5625,"replicates":2,"sample_mean":0.5,"seed":0,"upper":0.6875},"draws":[{"accepted":false,"method":"GETRANDBITS","ordinal":0,"position":0,"replicate":0,"value":3,"width":2},{"accepted":true,"method":"GETRANDBITS","ordinal":1,"position":0,"replicate":0,"value":1,"width":2},{"accepted":false,"method":"RANDOM_U53","ordinal":2,"position":1,"replicate":0,"value":6827046333291546,"width":53},{"accepted":true,"method":"GETRANDBITS","ordinal":3,"position":0,"replicate":1,"value":1,"width":2},{"accepted":true,"method":"RANDOM_U53","ordinal":4,"position":1,"replicate":1,"value":364650860978552,"width":53},{"accepted":false,"method":"GETRANDBITS","ordinal":5,"position":1,"replicate":1,"value":3,"width":2},{"accepted":false,"method":"GETRANDBITS","ordinal":6,"position":1,"replicate":1,"value":2,"width":2},{"accepted":true,"method":"GETRANDBITS","ordinal":7,"position":1,"replicate":1,"value":1,"width":2}],"derived_indices":[[1,0],[1,1]]},{"case":"negative_seed","inputs":{"confidence":0.5,"expected_block_length":2.0,"interval_method":"PERCENTILE_TYPE7","replicates":4,"seed":-1,"series":[0.25,0.75]},"raw":{"bootstrap_distribution":[0.5,0.5,0.75,0.25],"expected_block_length":2.0,"interval_method":"PERCENTILE_TYPE7","lower":0.4375,"replicates":4,"sample_mean":0.5,"seed":-1,"upper":0.5625},"draws":[{"accepted":true,"method":"GETRANDBITS","ordinal":0,"position":0,"replicate":0,"value":0,"width":2},{"accepted":false,"method":"RANDOM_U53","ordinal":1,"position":1,"replicate":0,"value":5126932717094315,"width":53},{"accepted":false,"method":"GETRANDBITS","ordinal":2,"position":0,"replicate":1,"value":3,"width":2},{"accepted":false,"method":"GETRANDBITS","ordinal":3,"position":0,"replicate":1,"value":3,"width":2},{"accepted":true,"method":"GETRANDBITS","ordinal":4,"position":0,"replicate":1,"value":0,"width":2},{"accepted":true,"method":"RANDOM_U53","ordinal":5,"position":1,"replicate":1,"value":2297457538547630,"width":53},{"accepted":true,"method":"GETRANDBITS","ordinal":6,"position":1,"replicate":1,"value":1,"width":2},{"accepted":false,"method":"GETRANDBITS","ordinal":7,"position":0,"replicate":2,"value":3,"width":2},{"accepted":true,"method":"GETRANDBITS","ordinal":8,"position":0,"replicate":2,"value":1,"width":2},{"accepted":true,"method":"RANDOM_U53","ordinal":9,"position":1,"replicate":2,"value":4253607005993776,"width":53},{"accepted":true,"method":"GETRANDBITS","ordinal":10,"position":1,"replicate":2,"value":1,"width":2},{"accepted":false,"method":"GETRANDBITS","ordinal":11,"position":0,"replicate":3,"value":3,"width":2},{"accepted":true,"method":"GETRANDBITS","ordinal":12,"position":0,"replicate":3,"value":0,"width":2},{"accepted":true,"method":"RANDOM_U53","ordinal":13,"position":1,"replicate":3,"value":845412000043186,"width":53},{"accepted":true,"method":"GETRANDBITS","ordinal":14,"position":1,"replicate":3,"value":0,"width":2}],"derived_indices":[[0,1],[0,1],[1,1],[0,0]]},{"case":"always_restart","inputs":{"confidence":0.5,"expected_block_length":1.0,"interval_method":"PERCENTILE_TYPE7","replicates":4,"seed":17,"series":[0.0,1.0]},"raw":{"bootstrap_distribution":[1.0,1.0,0.0,1.0],"expected_block_length":1.0,"interval_method":"PERCENTILE_TYPE7","lower":0.75,"replicates":4,"sample_mean":0.5,"seed":17,"upper":1.0},"draws":[{"accepted":false,"method":"GETRANDBITS","ordinal":0,"position":0,"replicate":0,"value":2,"width":2},{"accepted":true,"method":"GETRANDBITS","ordinal":1,"position":0,"replicate":0,"value":1,"width":2},{"accepted":true,"method":"RANDOM_U53","ordinal":2,"position":1,"replicate":0,"value":7266024566469798,"width":53},{"accepted":false,"method":"GETRANDBITS","ordinal":3,"position":1,"replicate":0,"value":3,"width":2},{"accepted":true,"method":"GETRANDBITS","ordinal":4,"position":1,"replicate":0,"value":1,"width":2},{"accepted":true,"method":"GETRANDBITS","ordinal":5,"position":0,"replicate":1,"value":1,"width":2},{"accepted":true,"method":"RANDOM_U53","ordinal":6,"position":1,"replicate":1,"value":1573452260605559,"width":53},{"accepted":false,"method":"GETRANDBITS","ordinal":7,"position":1,"replicate":1,"value":2,"width":2},{"accepted":false,"method":"GETRANDBITS","ordinal":8,"position":1,"replicate":1,"value":2,"width":2},{"accepted":false,"method":"GETRANDBITS","ordinal":9,"position":1,"replicate":1,"value":2,"width":2},{"accepted":false,"method":"GETRANDBITS","ordinal":10,"position":1,"replicate":1,"value":2,"width":2},{"accepted":true,"method":"GETRANDBITS","ordinal":11,"position":1,"replicate":1,"value":1,"width":2},{"accepted":true,"method":"GETRANDBITS","ordinal":12,"position":0,"replicate":2,"value":0,"width":2},{"accepted":true,"method":"RANDOM_U53","ordinal":13,"position":1,"replicate":2,"value":8264042541716816,"width":53},{"accepted":true,"method":"GETRANDBITS","ordinal":14,"position":1,"replicate":2,"value":0,"width":2},{"accepted":true,"method":"GETRANDBITS","ordinal":15,"position":0,"replicate":3,"value":1,"width":2},{"accepted":true,"method":"RANDOM_U53","ordinal":16,"position":1,"replicate":3,"value":7342543532216069,"width":53},{"accepted":true,"method":"GETRANDBITS","ordinal":17,"position":1,"replicate":3,"value":1,"width":2}],"derived_indices":[[1,1],[1,1],[0,0],[1,1]]},{"case":"three_point","inputs":{"confidence":0.5,"expected_block_length":3.0,"interval_method":"PERCENTILE_TYPE7","replicates":4,"seed":13,"series":[0.0,0.5,1.0]},"raw":{"bootstrap_distribution":[0.5,0.5,0.16666666666666666,0.5],"expected_block_length":3.0,"interval_method":"PERCENTILE_TYPE7","lower":0.4166666666666667,"replicates":4,"sample_mean":0.5,"seed":13,"upper":0.5},"draws":[{"accepted":true,"method":"GETRANDBITS","ordinal":0,"position":0,"replicate":0,"value":1,"width":2},{"accepted":true,"method":"RANDOM_U53","ordinal":1,"position":1,"replicate":0,"value":2618912457733189,"width":53},{"accepted":false,"method":"GETRANDBITS","ordinal":2,"position":1,"replicate":0,"value":3,"width":2},{"accepted":true,"method":"GETRANDBITS","ordinal":3,"position":1,"replicate":0,"value":2,"width":2},{"accepted":false,"method":"RANDOM_U53","ordinal":4,"position":2,"replicate":0,"value":7223815744895072,"width":53},{"accepted":false,"method":"GETRANDBITS","ordinal":5,"position":0,"replicate":1,"value":3,"width":2},{"accepted":true,"method":"GETRANDBITS","ordinal":6,"position":0,"replicate":1,"value":0,"width":2},{"accepted":false,"method":"RANDOM_U53","ordinal":7,"position":1,"replicate":1,"value":5872781529716622,"width":53},{"accepted":false,"method":"RANDOM_U53","ordinal":8,"position":2,"replicate":1,"value":6000466069991702,"width":53},{"accepted":false,"method":"GETRANDBITS","ordinal":9,"position":0,"replicate":2,"value":3,"width":2},{"accepted":true,"method":"GETRANDBITS","ordinal":10,"position":0,"replicate":2,"value":0,"width":2},{"accepted":false,"method":"RANDOM_U53","ordinal":11,"position":1,"replicate":2,"value":5773228919202786,"width":53},{"accepted":true,"method":"RANDOM_U53","ordinal":12,"position":2,"replicate":2,"value":1687716467398288,"width":53},{"accepted":true,"method":"GETRANDBITS","ordinal":13,"position":2,"replicate":2,"value":0,"width":2},{"accepted":true,"method":"GETRANDBITS","ordinal":14,"position":0,"replicate":3,"value":2,"width":2},{"accepted":false,"method":"RANDOM_U53","ordinal":15,"position":1,"replicate":3,"value":7618204496759443,"width":53},{"accepted":false,"method":"RANDOM_U53","ordinal":16,"position":2,"replicate":3,"value":6707590770571904,"width":53}],"derived_indices":[[1,2,0],[0,1,2],[0,1,0],[2,0,1]]},{"case":"single_replicate","inputs":{"confidence":0.5,"expected_block_length":2.0,"interval_method":"PERCENTILE_TYPE7","replicates":1,"seed":2,"series":[0.25,0.75]},"raw":{"bootstrap_distribution":[0.5],"expected_block_length":2.0,"interval_method":"PERCENTILE_TYPE7","lower":0.5,"replicates":1,"sample_mean":0.5,"seed":2,"upper":0.5},"draws":[{"accepted":false,"method":"GETRANDBITS","ordinal":0,"position":0,"replicate":0,"value":3,"width":2},{"accepted":false,"method":"GETRANDBITS","ordinal":1,"position":0,"replicate":0,"value":3,"width":2},{"accepted":false,"method":"GETRANDBITS","ordinal":2,"position":0,"replicate":0,"value":3,"width":2},{"accepted":false,"method":"GETRANDBITS","ordinal":3,"position":0,"replicate":0,"value":3,"width":2},{"accepted":true,"method":"GETRANDBITS","ordinal":4,"position":0,"replicate":0,"value":0,"width":2},{"accepted":true,"method":"RANDOM_U53","ordinal":5,"position":1,"replicate":0,"value":824922428860591,"width":53},{"accepted":true,"method":"GETRANDBITS","ordinal":6,"position":1,"replicate":0,"value":1,"width":2}],"derived_indices":[[0,1]]},{"case":"signed_zero","inputs":{"confidence":0.5,"expected_block_length":2.0,"interval_method":"PERCENTILE_TYPE7","replicates":2,"seed":7,"series":[-0.0,0.0]},"raw":{"bootstrap_distribution":[0.0,0.0],"expected_block_length":2.0,"interval_method":"PERCENTILE_TYPE7","lower":0.0,"replicates":2,"sample_mean":0.0,"seed":7,"upper":0.0},"draws":[{"accepted":true,"method":"GETRANDBITS","ordinal":0,"position":0,"replicate":0,"value":1,"width":2},{"accepted":false,"method":"RANDOM_U53","ordinal":1,"position":1,"replicate":0,"value":8537612169672756,"width":53},{"accepted":true,"method":"GETRANDBITS","ordinal":2,"position":0,"replicate":1,"value":1,"width":2},{"accepted":false,"method":"RANDOM_U53","ordinal":3,"position":1,"replicate":1,"value":5863096500449791,"width":53}],"derived_indices":[[1,0],[1,0]]},{"case":"negative_values","inputs":{"confidence":0.75,"expected_block_length":2.0,"interval_method":"PERCENTILE_TYPE7","replicates":4,"seed":3,"series":[-0.75,-0.25,0.25,0.75]},"raw":{"bootstrap_distribution":[0.0,-0.25,0.125,0.0],"expected_block_length":2.0,"interval_method":"PERCENTILE_TYPE7","lower":-0.15625,"replicates":4,"sample_mean":0.0,"seed":3,"upper":0.078125},"draws":[{"accepted":true,"method":"GETRANDBITS","ordinal":0,"position":0,"replicate":0,"value":1,"width":3},{"accepted":false,"method":"RANDOM_U53","ordinal":1,"position":1,"replicate":0,"value":5338034768530029,"width":53},{"accepted":true,"method":"RANDOM_U53","ordinal":2,"position":2,"replicate":0,"value":1174744111699334,"width":53},{"accepted":false,"method":"GETRANDBITS","ordinal":3,"position":2,"replicate":0,"value":7,"width":3},{"accepted":false,"method":"GETRANDBITS","ordinal":4,"position":2,"replicate":0,"value":4,"width":3},{"accepted":true,"method":"GETRANDBITS","ordinal":5,"position":2,"replicate":0,"value":3,"width":3},{"accepted":false,"method":"RANDOM_U53","ordinal":6,"position":3,"replicate":0,"value":5635987456838371,"width":53},{"accepted":true,"method":"GETRANDBITS","ordinal":7,"position":0,"replicate":1,"value":0,"width":3},{"accepted":false,"method":"RANDOM_U53","ordinal":8,"position":1,"replicate":1,"value":5454755636542440,"width":53},{"accepted":false,"method":"RANDOM_U53","ordinal":9,"position":2,"replicate":1,"value":8185908416844158,"width":53},{"accepted":true,"method":"RANDOM_U53","ordinal":10,"position":3,"replicate":1,"value":4226469161702425,"width":53},{"accepted":false,"method":"GETRANDBITS","ordinal":11,"position":3,"replicate":1,"value":4,"width":3},{"accepted":true,"method":"GETRANDBITS","ordinal":12,"position":3,"replicate":1,"value":1,"width":3},{"accepted":true,"method":"GETRANDBITS","ordinal":13,"position":0,"replicate":2,"value":1,"width":3},{"accepted":false,"method":"RANDOM_U53","ordinal":14,"position":1,"replicate":2,"value":8967971420396558,"width":53},{"accepted":true,"method":"RANDOM_U53","ordinal":15,"position":2,"replicate":2,"value":4235757114488078,"width":53},{"accepted":false,"method":"GETRANDBITS","ordinal":16,"position":2,"replicate":2,"value":6,"width":3},{"accepted":false,"method":"GETRANDBITS","ordinal":17,"position":2,"replicate":2,"value":4,"width":3},{"accepted":true,"method":"GETRANDBITS","ordinal":18,"position":2,"replicate":2,"value":3,"width":3},{"accepted":true,"method":"RANDOM_U53","ordinal":19,"position":3,"replicate":2,"value":3577070266247136,"width":53},{"accepted":false,"method":"GETRANDBITS","ordinal":20,"position":3,"replicate":2,"value":6,"width":3},{"accepted":true,"method":"GETRANDBITS","ordinal":21,"position":3,"replicate":2,"value":1,"width":3},{"accepted":true,"method":"GETRANDBITS","ordinal":22,"position":0,"replicate":3,"value":1,"width":3},{"accepted":false,"method":"RANDOM_U53","ordinal":23,"position":1,"replicate":3,"value":5718316448170725,"width":53},{"accepted":false,"method":"RANDOM_U53","ordinal":24,"position":2,"replicate":3,"value":7818657043582518,"width":53},{"accepted":false,"method":"RANDOM_U53","ordinal":25,"position":3,"replicate":3,"value":4712397408258962,"width":53}],"derived_indices":[[1,2,3,0],[0,1,2,1],[1,2,3,1],[1,2,3,0]]},{"case":"wide_seed","inputs":{"confidence":0.5,"expected_block_length":2.0,"interval_method":"PERCENTILE_TYPE7","replicates":2,"seed":57896044618658097711785492504343953926634992332820282019728792003956564820091,"series":[0.25,0.75]},"raw":{"bootstrap_distribution":[0.5,0.5],"expected_block_length":2.0,"interval_method":"PERCENTILE_TYPE7","lower":0.5,"replicates":2,"sample_mean":0.5,"seed":57896044618658097711785492504343953926634992332820282019728792003956564820091,"upper":0.5},"draws":[{"accepted":true,"method":"GETRANDBITS","ordinal":0,"position":0,"replicate":0,"value":0,"width":2},{"accepted":false,"method":"RANDOM_U53","ordinal":1,"position":1,"replicate":0,"value":6262159570497777,"width":53},{"accepted":false,"method":"GETRANDBITS","ordinal":2,"position":0,"replicate":1,"value":3,"width":2},{"accepted":true,"method":"GETRANDBITS","ordinal":3,"position":0,"replicate":1,"value":1,"width":2},{"accepted":false,"method":"RANDOM_U53","ordinal":4,"position":1,"replicate":1,"value":6174515214550957,"width":53}],"derived_indices":[[0,1],[1,0]]}]')
    # Exact negative minimum subnormal / 2 is the nearest-even negative zero.
    # Seed7 samples indices (1,0),(1,0); both original two-element sums are -ulp.
    zero_case = dict(cases[5], case="negative_underflow", inputs=dict(cases[5]["inputs"], series=[-5e-324, 0.0]),
        raw=dict(cases[5]["raw"], sample_mean=-0.0, lower=-0.0, upper=-0.0, bootstrap_distribution=[-0.0, -0.0]))
    cases.append(zero_case)
    def run(selected, work, *, inputs=None, raw=None, expected=None, projected=None, expected_environment=None):
        source = selected["inputs"] if inputs is None else inputs
        observed = selected["raw"] if raw is None else raw
        expectation = selected["raw"] if expected is None else expected
        selected_projection = projection(selected["raw"]) if projected is None else projected
        return IndependentEvidenceReviewV1._bounded_review_bootstrap_v1(
            deterministic_json(source).encode("utf-8"), deterministic_json(observed).encode("utf-8"),
            deterministic_json(expectation).encode("utf-8"), selected_projection,
            expected_environment=environment if expected_environment is None else expected_environment, work=work)
    def forbidden(*args, **kwargs):
        raise AssertionError("independent bootstrap proof invoked formula, resampler, percentile or fsum")
    positives = []
    with ExitStack() as stack:
        for name in ("compute_math_14_stationary_bootstrap_mean_interval", "compute_math_14_stationary_bootstrap_mean_interval_v2",
                     "_stationary_indices", "_percentile"):
            stack.enter_context(patch.object(formulas, name, forbidden))
        stack.enter_context(patch.object(math, "fsum", forbidden))
        for selected in cases:
            work = _EvidenceNumericalWorkV1(limits, retained_input_capacity=0)
            proof = run(selected, work)
            consumed = dict(work.consumed)
            assert work.state == "OPEN" and len(proof["cells"]) <= 26
            assert tuple(tuple(row) for row in selected["derived_indices"]) == proof["indices"]
            assert len(proof["draws"]) == consumed["random_draws"] == len(selected["draws"])
            for actual, original in zip(proof["draws"], selected["draws"]):
                assert all(actual[name] == original[name] for name in ("ordinal", "method", "width", "value", "replicate", "position"))
                assert actual["disposition"] == ("SELECTED" if original["accepted"] else "REJECTED") if original["method"] == "GETRANDBITS" else actual["disposition"] == ("RESTART" if original["accepted"] else "CONTINUE")
            fragments = [*proof["draws"], *proof["cells"], proof["summary"], proof]
            assert consumed["serialized_bytes"] == sum(len(deterministic_json(value).encode("utf-8")) for value in fragments)
            repetitions = 2 if selected["case"] in ("two_point", "signed_zero", "negative_underflow") else 1
            if repetitions == 2:
                assert run(selected, work) == proof
                assert work.consumed["serialized_bytes"] == 2 * consumed["serialized_bytes"]
                assert work.consumed["random_draws"] == 2 * consumed["random_draws"]
            work._assert_bootstrap_custody_v1()
            assert len(work._bootstrap_invocations) == repetitions
            assert all(value == 0 for key, value in consumed.items() if key in (
                "log_series_terms", "square_roots", "decimal_constructions", "retained_decimal_inputs"))
            positives.append(dict(case=selected["case"], proof=proof, repetitions=repetitions,
                first_consumption=consumed, cumulative_consumption=dict(work.consumed)))
    base = cases[0]
    mutations = (
        ("boolean_seed", "inputs", dict(seed=True)),
        ("seed_bits", "inputs", dict(seed=2**256)),
        ("zero_replicates", "inputs", dict(replicates=0)),
        ("boolean_replicates", "inputs", dict(replicates=True)),
        ("replicate_bound", "inputs", dict(replicates=5)),
        ("series_short", "inputs", dict(series=[0.5])),
        ("series_long", "inputs", dict(series=[0.5] * 9)),
        ("series_boolean", "inputs", dict(series=[True, 0.75])),
        ("series_proof_bound", "inputs", dict(series=[-1.0000000000000002, 0.75])),
        ("block_low", "inputs", dict(expected_block_length=0.5)),
        ("block_high", "inputs", dict(expected_block_length=3.0)),
        ("block_integer", "inputs", dict(expected_block_length=2)),
        ("confidence_zero", "inputs", dict(confidence=0.0)),
        ("confidence_one", "inputs", dict(confidence=1.0)),
        ("method", "inputs", dict(interval_method="OTHER")),
        ("raw_lower_ulp", "raw", dict(lower=math.nextafter(0.5625, 1.0))),
        ("raw_mean_ulp", "raw", dict(sample_mean=math.nextafter(0.5, 1.0))),
        ("raw_distribution_order", "raw", dict(bootstrap_distribution=[0.75, 0.5])),
        ("raw_seed", "raw", dict(seed=1)),
        ("raw_replicates", "raw", dict(replicates=3)),
        ("raw_block", "raw", dict(expected_block_length=1.0)),
        ("expected", "expected", dict(upper=math.nextafter(0.6875, 1.0))),
    )
    denials = []
    for name, field, changes in mutations:
        value = dict(base["inputs"] if field == "inputs" else base["raw"], **changes)
        work = _EvidenceNumericalWorkV1(limits, retained_input_capacity=0)
        with pytest.raises(ComputationControlPlaneError):run(base, work, **{field: value})
        assert work.state == "FAILED"
        if work._bootstrap_invocations:work._assert_bootstrap_custody_v1(failed=True)
        consumed = dict(work.consumed)
        with pytest.raises(ComputationControlPlaneError, match="LP03_NUMERICAL_WORK_NOT_OPEN"):run(base, work)
        assert dict(work.consumed) == consumed
        denials.append(dict(case=name, failure=work.failure, consumed=consumed))
    extras = (
        ("environment", {}, dict(expected_environment=replace(environment, build="different"))),
        ("projection_mutable", {}, dict(projected=dict(base["raw"]))),
        ("projection_seed", {}, dict(projected=projection(dict(base["raw"], seed=1)))),
        ("zero_budget", dict(max_serialized_bytes=0), {}),
        ("complete_bytes", dict(max_serialized_bytes=10000), {}),
        ("work_bits", dict(max_work_bits=1074), {}),
        ("input_bits", dict(max_input_bits=1), {}),
    )
    for name, changes, arguments in extras:
        work = _EvidenceNumericalWorkV1(dict(limits, **changes), retained_input_capacity=0)
        with pytest.raises(ComputationControlPlaneError):run(base, work, **arguments)
        assert work.state == "FAILED"
        if work._bootstrap_invocations:work._assert_bootstrap_custody_v1(failed=True)
        denials.append(dict(case=name, failure=work.failure, consumed=dict(work.consumed)))
    # Concrete independent seed132 witness needs 67 API calls. Preserve exactly
    # 64 actual calls plus the unexecuted 65th request; never retry its seed.
    cap = json.loads('{"case":"cap64","inputs":{"series":[0.0,0.125,0.25,0.375,0.5,0.625,0.75,0.875],"expected_block_length":1.0,"seed":132,"replicates":2,"confidence":0.5,"interval_method":"PERCENTILE_TYPE7"},"raw":{"bootstrap_distribution":[0.515625,0.390625],"expected_block_length":1.0,"interval_method":"PERCENTILE_TYPE7","lower":0.421875,"replicates":2,"sample_mean":0.4375,"seed":132,"upper":0.484375},"draws":[{"accepted":true,"method":"GETRANDBITS","ordinal":0,"position":0,"replicate":0,"value":6,"width":4},{"accepted":true,"method":"RANDOM_U53","ordinal":1,"position":1,"replicate":0,"value":1403085714981351,"width":53},{"accepted":true,"method":"GETRANDBITS","ordinal":2,"position":1,"replicate":0,"value":0,"width":4},{"accepted":true,"method":"RANDOM_U53","ordinal":3,"position":2,"replicate":0,"value":8086289088714680,"width":53},{"accepted":false,"method":"GETRANDBITS","ordinal":4,"position":2,"replicate":0,"value":14,"width":4},{"accepted":true,"method":"GETRANDBITS","ordinal":5,"position":2,"replicate":0,"value":0,"width":4},{"accepted":true,"method":"RANDOM_U53","ordinal":6,"position":3,"replicate":0,"value":2766121081861460,"width":53},{"accepted":false,"method":"GETRANDBITS","ordinal":7,"position":3,"replicate":0,"value":13,"width":4},{"accepted":false,"method":"GETRANDBITS","ordinal":8,"position":3,"replicate":0,"value":12,"width":4},{"accepted":false,"method":"GETRANDBITS","ordinal":9,"position":3,"replicate":0,"value":15,"width":4},{"accepted":false,"method":"GETRANDBITS","ordinal":10,"position":3,"replicate":0,"value":12,"width":4},{"accepted":false,"method":"GETRANDBITS","ordinal":11,"position":3,"replicate":0,"value":13,"width":4},{"accepted":false,"method":"GETRANDBITS","ordinal":12,"position":3,"replicate":0,"value":8,"width":4},{"accepted":true,"method":"GETRANDBITS","ordinal":13,"position":3,"replicate":0,"value":0,"width":4},{"accepted":true,"method":"RANDOM_U53","ordinal":14,"position":4,"replicate":0,"value":2235199897973142,"width":53},{"accepted":true,"method":"GETRANDBITS","ordinal":15,"position":4,"replicate":0,"value":7,"width":4},{"accepted":true,"method":"RANDOM_U53","ordinal":16,"position":5,"replicate":0,"value":2337814936007933,"width":53},{"accepted":false,"method":"GETRANDBITS","ordinal":17,"position":5,"replicate":0,"value":12,"width":4},{"accepted":true,"method":"GETRANDBITS","ordinal":18,"position":5,"replicate":0,"value":7,"width":4},{"accepted":true,"method":"RANDOM_U53","ordinal":19,"position":6,"replicate":0,"value":1539272702298488,"width":53},{"accepted":false,"method":"GETRANDBITS","ordinal":20,"position":6,"replicate":0,"value":9,"width":4},{"accepted":false,"method":"GETRANDBITS","ordinal":21,"position":6,"replicate":0,"value":15,"width":4},{"accepted":true,"method":"GETRANDBITS","ordinal":22,"position":6,"replicate":0,"value":6,"width":4},{"accepted":true,"method":"RANDOM_U53","ordinal":23,"position":7,"replicate":0,"value":2227218889720727,"width":53},{"accepted":false,"method":"GETRANDBITS","ordinal":24,"position":7,"replicate":0,"value":10,"width":4},{"accepted":false,"method":"GETRANDBITS","ordinal":25,"position":7,"replicate":0,"value":12,"width":4},{"accepted":false,"method":"GETRANDBITS","ordinal":26,"position":7,"replicate":0,"value":15,"width":4},{"accepted":false,"method":"GETRANDBITS","ordinal":27,"position":7,"replicate":0,"value":13,"width":4},{"accepted":true,"method":"GETRANDBITS","ordinal":28,"position":7,"replicate":0,"value":7,"width":4},{"accepted":false,"method":"GETRANDBITS","ordinal":29,"position":0,"replicate":1,"value":13,"width":4},{"accepted":false,"method":"GETRANDBITS","ordinal":30,"position":0,"replicate":1,"value":14,"width":4},{"accepted":false,"method":"GETRANDBITS","ordinal":31,"position":0,"replicate":1,"value":13,"width":4},{"accepted":false,"method":"GETRANDBITS","ordinal":32,"position":0,"replicate":1,"value":14,"width":4},{"accepted":false,"method":"GETRANDBITS","ordinal":33,"position":0,"replicate":1,"value":9,"width":4},{"accepted":false,"method":"GETRANDBITS","ordinal":34,"position":0,"replicate":1,"value":12,"width":4},{"accepted":false,"method":"GETRANDBITS","ordinal":35,"position":0,"replicate":1,"value":8,"width":4},{"accepted":false,"method":"GETRANDBITS","ordinal":36,"position":0,"replicate":1,"value":14,"width":4},{"accepted":false,"method":"GETRANDBITS","ordinal":37,"position":0,"replicate":1,"value":12,"width":4},{"accepted":false,"method":"GETRANDBITS","ordinal":38,"position":0,"replicate":1,"value":13,"width":4},{"accepted":false,"method":"GETRANDBITS","ordinal":39,"position":0,"replicate":1,"value":9,"width":4},{"accepted":false,"method":"GETRANDBITS","ordinal":40,"position":0,"replicate":1,"value":8,"width":4},{"accepted":false,"method":"GETRANDBITS","ordinal":41,"position":0,"replicate":1,"value":12,"width":4},{"accepted":true,"method":"GETRANDBITS","ordinal":42,"position":0,"replicate":1,"value":5,"width":4},{"accepted":true,"method":"RANDOM_U53","ordinal":43,"position":1,"replicate":1,"value":3441664394076324,"width":53},{"accepted":false,"method":"GETRANDBITS","ordinal":44,"position":1,"replicate":1,"value":15,"width":4},{"accepted":false,"method":"GETRANDBITS","ordinal":45,"position":1,"replicate":1,"value":9,"width":4},{"accepted":false,"method":"GETRANDBITS","ordinal":46,"position":1,"replicate":1,"value":14,"width":4},{"accepted":true,"method":"GETRANDBITS","ordinal":47,"position":1,"replicate":1,"value":5,"width":4},{"accepted":true,"method":"RANDOM_U53","ordinal":48,"position":2,"replicate":1,"value":1764247788942826,"width":53},{"accepted":false,"method":"GETRANDBITS","ordinal":49,"position":2,"replicate":1,"value":12,"width":4},{"accepted":true,"method":"GETRANDBITS","ordinal":50,"position":2,"replicate":1,"value":1,"width":4},{"accepted":true,"method":"RANDOM_U53","ordinal":51,"position":3,"replicate":1,"value":4937317373039903,"width":53},{"accepted":false,"method":"GETRANDBITS","ordinal":52,"position":3,"replicate":1,"value":9,"width":4},{"accepted":false,"method":"GETRANDBITS","ordinal":53,"position":3,"replicate":1,"value":13,"width":4},{"accepted":false,"method":"GETRANDBITS","ordinal":54,"position":3,"replicate":1,"value":12,"width":4},{"accepted":true,"method":"GETRANDBITS","ordinal":55,"position":3,"replicate":1,"value":5,"width":4},{"accepted":true,"method":"RANDOM_U53","ordinal":56,"position":4,"replicate":1,"value":6063945242608638,"width":53},{"accepted":false,"method":"GETRANDBITS","ordinal":57,"position":4,"replicate":1,"value":10,"width":4},{"accepted":true,"method":"GETRANDBITS","ordinal":58,"position":4,"replicate":1,"value":1,"width":4},{"accepted":true,"method":"RANDOM_U53","ordinal":59,"position":5,"replicate":1,"value":7946530277117706,"width":53},{"accepted":true,"method":"GETRANDBITS","ordinal":60,"position":5,"replicate":1,"value":2,"width":4},{"accepted":true,"method":"RANDOM_U53","ordinal":61,"position":6,"replicate":1,"value":3234230570417225,"width":53},{"accepted":false,"method":"GETRANDBITS","ordinal":62,"position":6,"replicate":1,"value":13,"width":4},{"accepted":true,"method":"GETRANDBITS","ordinal":63,"position":6,"replicate":1,"value":4,"width":4},{"accepted":true,"method":"RANDOM_U53","ordinal":64,"position":7,"replicate":1,"value":2319263170785042,"width":53},{"accepted":false,"method":"GETRANDBITS","ordinal":65,"position":7,"replicate":1,"value":12,"width":4},{"accepted":true,"method":"GETRANDBITS","ordinal":66,"position":7,"replicate":1,"value":2,"width":4}]}')
    work = _EvidenceNumericalWorkV1(limits, retained_input_capacity=0)
    with pytest.raises(ComputationControlPlaneError, match="LP03_BOOTSTRAP_REPLAY_DRAW_LIMIT_EXHAUSTED"):
        run(cap, work)
    assert work.state == "FAILED" and work.consumed["random_draws"] == 64
    entry = work._bootstrap_invocations[0][0]
    assert len(entry.prefix) == len(entry.attempts) == 64 and entry.completed is None
    assert entry.pending_request == ("RANDOM_U53", 53, 1, 7, None, 1.0, "3ff0000000000000")
    work._assert_bootstrap_custody_v1(failed=True)
    for actual, original in zip(entry.prefix, cap["draws"][:64]):
        assert actual[3] == original["value"]
    denials.append(dict(case="retained_64_draws_unentered_65", failure=work.failure, consumed=dict(work.consumed),
        prefix=tuple(dict(ordinal=row[0], request=row[1], returned=row[2], value=row[3], disposition=row[4], state=row[5], bits=row[6]) for row in entry.prefix),
        pending_request=entry.pending_request))
    before = dict(work.consumed)
    with pytest.raises(ComputationControlPlaneError, match="LP03_NUMERICAL_WORK_NOT_OPEN"):run(base, work)
    assert dict(work.consumed) == before
    # A real returned getrandbits value must survive a later encoder exception.
    original_emit = _EvidenceNumericalWorkV1._emit
    def fail_draw_emit(work, values):
        if "disposition" in values:raise RuntimeError("retained-return encoder failure")
        return original_emit(work, values)
    work = _EvidenceNumericalWorkV1(limits, retained_input_capacity=0)
    with patch.object(_EvidenceNumericalWorkV1, "_emit", fail_draw_emit):
        with pytest.raises(RuntimeError, match="retained-return encoder failure"):run(base, work)
    assert work.state == "FAILED" and work.consumed["random_draws"] == 1
    entry = work._bootstrap_invocations[0][0]
    assert len(entry.prefix) == 0 and len(entry.attempts) == 1 and entry.attempts[0][2] == 3
    work._assert_bootstrap_custody_v1(failed=True)
    failure = work.failure
    entry.attempts[0][2] = 2
    with pytest.raises(ComputationControlPlaneError, match="LP03_BOOTSTRAP_FAILED_ATTEMPT_CHANGED"):
        work._assert_bootstrap_custody_v1(failed=True)
    assert work.failure == failure and work.consumed["random_draws"] == 1
    denials.append(dict(case="returned_draw_encoding_failure_and_substitution", failure=failure, consumed=dict(work.consumed)))
    def fail_constructor(*args, **kwargs):raise RuntimeError("retained constructor failure")
    work = _EvidenceNumericalWorkV1(limits, retained_input_capacity=0)
    with patch.object(random, "Random", fail_constructor):
        with pytest.raises(RuntimeError, match="retained constructor failure"):run(base, work)
    work._assert_bootstrap_custody_v1(failed=True)
    assert work.state == "FAILED" and work.consumed["random_draws"] == 0 and len(work._bootstrap_invocations) == 1
    denials.append(dict(case="constructor_failure", failure=work.failure, consumed=dict(work.consumed)))
    for name in ("completion_proof", "completion_json", "header", "prefix_and_attempts", "roster", "guard", "generator_advanced"):
        work = _EvidenceNumericalWorkV1(limits, retained_input_capacity=0)
        run(base, work)
        entry = work._bootstrap_invocations[0][0]
        if name == "completion_proof":entry.completed = (entry.prefix, MappingProxyType({}), entry.completed[2], len(entry.prefix))
        elif name == "completion_json":entry.completed = (entry.prefix, entry.completed[1], "{}", len(entry.prefix))
        elif name == "header":entry.original = tuple(list(entry.original))
        elif name == "prefix_and_attempts":
            entry.prefix = tuple(tuple(list(row)) for row in entry.prefix)
            entry.attempts[:] = entry.prefix
        elif name == "roster":work._bootstrap_invocations.clear()
        elif name == "guard":entry._inspect = lambda **kwargs:None
        else:entry.generator.random()
        before = dict(work.consumed)
        with pytest.raises(ComputationControlPlaneError):work._assert_bootstrap_custody_v1()
        assert work.state == "FAILED" and dict(work.consumed) == before
        denials.append(dict(case=name, failure=work.failure, consumed=dict(work.consumed)))
    work = _EvidenceNumericalWorkV1(limits, retained_input_capacity=0)
    completed = 0
    for _ in range(8):
        before = dict(work.consumed)
        try:run(base, work)
        except ComputationControlPlaneError:
            assert completed >= 2 and work.failure == "LP03_BOOTSTRAP_REVIEW_COMPLETE_BYTES_EXHAUSTED"
            assert dict(work.consumed) == before and len(work._bootstrap_invocations) == completed
            break
        completed += 1
    else:raise AssertionError("original bootstrap allowance failed to stop cumulative replay")
    denials.append(dict(case="original_cumulative_allowance", completed=completed, failure=work.failure, consumed=dict(work.consumed)))
    work._assert_bootstrap_custody_v1(failed=True)
    original_failure, original_consumed = work.failure, dict(work.consumed)
    entry = work._bootstrap_invocations[0][0]
    entry.completed = (entry.prefix, entry.completed[1], "{}", len(entry.prefix))
    with pytest.raises(ComputationControlPlaneError, match="LP03_BOOTSTRAP_ORIGINAL_REPLAY_CHANGED"):
        work._assert_bootstrap_custody_v1(failed=True)
    assert work.failure == original_failure and dict(work.consumed) == original_consumed
    denials.append(dict(case="completed_failed_inspection_keeps_original_reason", failure=work.failure,
        consumed=dict(work.consumed)))
    print("LP03_BOOTSTRAP_PURE_QUALIFICATION=" + deterministic_json(dict(
        scope="BOUNDED_BOOTSTRAP_MODEL_DATA_ONLY_NO_SOURCE_NATIVE_OR_COVERAGE_AUTHORITY", positives=positives, denials=denials)))


def _assert_lp03_wilson_ordered_model_proof():
    import math
    import statistics
    from contextlib import ExitStack
    from unittest.mock import patch
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane import implementation_registry as formulas
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.evidence import IndependentEvidenceReviewV1
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.parameter_policy import _EvidenceNumericalWorkV1
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import ComputationControlPlaneError
    limits = dict(max_input_bits=4096, max_work_bits=65536, max_serialized_bytes=65536)
    # Independent Decimal160 interpretation of the pinned stdlib AS241 source,
    # with separate binary64 rounding at each operation. No QTT output or
    # proposed proof helper generated these original endpoint literals.
    cases = (
        ("central_balanced", 5, 10, .5, .39569991542468774, .6043000845753123, "CENTRAL"),
        ("central_zero", 0, 10, .5, 3.469446951953614e-18, .04351403056966917, "CENTRAL"),
        ("central_full", 10, 10, .5, .956485969430331, 1.0, "CENTRAL"),
        ("central_one", 1, 1, .5, .6873152559174167, 1.0, "CENTRAL"),
        ("tail_standard", 5, 10, .95, .23659309051256405, .763406909487436, "TAIL_LE_FIVE"),
        ("tail_zero", 0, 10, .95, 2.7755575615628914e-17, .27753279986288915, "TAIL_LE_FIVE"),
        ("tail_full", 10, 10, .95, .7224672001371109, 1.0, "TAIL_LE_FIVE"),
        ("deep_tail", 3, 7, .9999999999999964, .019304237408469815, .9661890077132576, "TAIL_GT_FIVE"),
        ("largest_count", 4503599627370496, 9007199254740992, .5, .49999999644654786, .5000000035534522, "CENTRAL"),
        ("tiny_confidence", 0, 4096, 4.440892098500626e-16, 0.0, 7.563109205769428e-35, "CENTRAL"),
        ("rounded_boundary_to_tail", 2, 7, .85, .11327561076365919, .5560457023617696, "TAIL_LE_FIVE"),
        ("next_boundary_to_tail", 2, 7, .8500000000000001, .11327561076365919, .5560457023617696, "TAIL_LE_FIVE"),
    )
    def run(selected, work, *, inputs=None, raw=None, expected=None, projected=None):
        _, successes, trials, confidence, lower, upper, _ = selected
        original_input = dict(successes=successes, trials=trials, confidence=confidence)
        original_raw = dict(lower=lower, upper=upper)
        return IndependentEvidenceReviewV1._bounded_review_wilson_v1(
            deterministic_json(original_input if inputs is None else inputs).encode("utf-8"),
            deterministic_json(original_raw if raw is None else raw).encode("utf-8"),
            deterministic_json(original_raw if expected is None else expected).encode("utf-8"),
            (lower, upper) if projected is None else projected, work=work)
    def forbidden(*args, **kwargs):
        raise AssertionError("independent Wilson proof invoked production formula, inverse normal, log or sqrt")
    positives = []
    with ExitStack() as stack:
        for name in ("compute_math_11_v34", "compute_math_11_wilson_score_interval"):
            stack.enter_context(patch.object(formulas, name, forbidden))
        stack.enter_context(patch.object(statistics.NormalDist, "inv_cdf", forbidden))
        stack.enter_context(patch.object(statistics, "_normal_dist_inv_cdf", forbidden))
        stack.enter_context(patch.object(math, "log", forbidden))
        stack.enter_context(patch.object(math, "sqrt", forbidden))
        for selected in cases:
            work = _EvidenceNumericalWorkV1(limits, retained_input_capacity=0)
            first = run(selected, work)
            prefix = dict(work.consumed)
            repetitions = 2 if selected[-1] == "CENTRAL" else 1
            if repetitions == 2:
                second = run(selected, work)
                assert first == second
            assert work.state == "OPEN" and len(first["cells"]) == 58
            assert first["summary"]["branch"] == selected[-1]
            assert (first["log_enclosure"] is None) == (selected[-1] == "CENTRAL")
            assert prefix["log_series_terms"] == (0 if selected[-1] == "CENTRAL" else 128)
            assert prefix["square_roots"] == (1 if selected[-1] == "CENTRAL" else 2)
            assert prefix["input_values"] == 9
            assert all(prefix[key] == 0 for key in ("random_draws", "decimal_constructions", "retained_decimal_inputs"))
            fragments = list(first["cells"]) + [first["summary"]]
            if first["log_enclosure"] is not None: fragments.append(first["log_enclosure"])
            exact_bytes = sum(len(deterministic_json(value).encode("utf-8")) for value in fragments + [first])
            assert exact_bytes == prefix["serialized_bytes"]
            assert work.consumed["serialized_bytes"] == repetitions * exact_bytes <= 65536
            positives.append(dict(case=selected[0], proof=first, repetitions=repetitions,
                first_consumption=prefix, cumulative_consumption=dict(work.consumed)))
    base = cases[0]
    original_input = dict(successes=5, trials=10, confidence=.5)
    original_raw = dict(lower=base[4], upper=base[5])
    mutations = (
        ("boolean_successes", "inputs", dict(successes=True)),
        ("boolean_trials", "inputs", dict(trials=True)),
        ("float_trials", "inputs", dict(trials=10.0)),
        ("zero_trials", "inputs", dict(trials=0)),
        ("negative_successes", "inputs", dict(successes=-1)),
        ("successes_exceed_trials", "inputs", dict(successes=11)),
        ("inexact_count_conversion", "inputs", dict(trials=9007199254740993)),
        ("zero_confidence", "inputs", dict(confidence=0.0)),
        ("negative_zero_confidence", "inputs", dict(confidence=-0.0)),
        ("one_confidence", "inputs", dict(confidence=1.0)),
        ("boolean_confidence", "inputs", dict(confidence=True)),
        ("string_confidence", "inputs", dict(confidence="0.5")),
        ("rounded_quantile_zero", "inputs", dict(confidence=2.0**-55)),
        ("rounded_quantile_one", "inputs", dict(confidence=math.nextafter(1.0, 0.0))),
        ("lower_ulp", "raw", dict(lower=math.nextafter(base[4], 1.0))),
        ("upper_ulp", "raw", dict(upper=math.nextafter(base[5], 1.0))),
        ("reversed_endpoints", "raw", dict(lower=base[5], upper=base[4])),
        ("integer_endpoint", "raw", dict(lower=0)),
        ("boolean_endpoint", "raw", dict(upper=True)),
        ("wrong_expectation", "expected", dict(lower=math.nextafter(base[4], 0.0))),
    )
    denials = []
    for name, field, changes in mutations:
        value = dict(original_input if field == "inputs" else original_raw, **changes)
        work = _EvidenceNumericalWorkV1(limits, retained_input_capacity=0)
        with pytest.raises(ComputationControlPlaneError):run(base, work, **{field: value})
        assert work.state == "FAILED"
        consumed = dict(work.consumed)
        with pytest.raises(ComputationControlPlaneError, match="LP03_NUMERICAL_WORK_NOT_OPEN"):run(base, work)
        assert dict(work.consumed) == consumed
        denials.append(dict(case=name, failure=work.failure, consumed=consumed))
    extras = (
        ("projection_lower_ulp", base, {}, dict(projected=(math.nextafter(base[4], 1.0), base[5]))),
        ("projection_wrong_type", base, {}, dict(projected=[base[4], base[5]])),
        ("projection_truncated", base, {}, dict(projected=(base[4],))),
        ("clamp_signed_zero_raw", cases[9], {}, dict(raw=dict(lower=-0.0, upper=cases[9][5]))),
        ("clamp_signed_zero_projection", cases[9], {}, dict(projected=(-0.0, cases[9][5]))),
        ("zero_budget", base, dict(max_serialized_bytes=0), {}),
        ("complete_bytes", base, dict(max_serialized_bytes=10000), {}),
        ("work_bits", base, dict(max_work_bits=1074), {}),
        ("input_bits", base, dict(max_input_bits=1), {}),
    )
    for name, selected, changes, arguments in extras:
        work = _EvidenceNumericalWorkV1(dict(limits, **changes), retained_input_capacity=0)
        with pytest.raises(ComputationControlPlaneError):run(selected, work, **arguments)
        assert work.state == "FAILED"
        consumed = dict(work.consumed)
        with pytest.raises(ComputationControlPlaneError, match="LP03_NUMERICAL_WORK_NOT_OPEN"):run(base, work)
        assert dict(work.consumed) == consumed
        denials.append(dict(case=name, failure=work.failure, consumed=consumed))
    # Preserve successful same-work prefixes, then observe finite cumulative
    # refusal. Never reset the original object or raise its admitted allowance.
    work = _EvidenceNumericalWorkV1(limits, retained_input_capacity=0)
    completed = 0
    for _ in range(6):
        before = dict(work.consumed)
        try:
            run(base, work)
        except ComputationControlPlaneError:
            assert completed >= 2 and work.state == "FAILED"
            assert work.failure == "LP03_WILSON_REVIEW_COMPLETE_BYTES_EXHAUSTED"
            assert dict(work.consumed) == before
            break
        completed += 1
    else:raise AssertionError("original Wilson allowance did not stop the finite repeated work")
    with pytest.raises(ComputationControlPlaneError, match="LP03_NUMERICAL_WORK_NOT_OPEN"):run(base, work)
    denials.append(dict(case="original_cumulative_allowance", completed=completed,
        failure=work.failure, consumed=dict(work.consumed)))
    print("LP03_WILSON_PURE_QUALIFICATION=" + deterministic_json(dict(
        scope="BOUNDED_AS241_WILSON_MODEL_DATA_ONLY_NO_SOURCE_NATIVE_OR_COVERAGE_AUTHORITY",
        positives=positives, denials=denials)))


def _assert_lp03_multiple_testing_ordered_proof():
    import math
    from contextlib import ExitStack
    from copy import deepcopy
    from unittest.mock import patch
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane import implementation_registry as formulas
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.evidence import IndependentEvidenceReviewV1
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.parameter_policy import _EvidenceNumericalWorkV1
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import ComputationControlPlaneError
    limits = dict(max_input_bits=4096, max_work_bits=65536, max_serialized_bytes=65536)
    def case(name, math_id, ps, q, rank, indices, adjusted, correction):
        return (name, math_id, dict(p_values=ps, q=q), dict(largest_rank=rank,
            rejected_original_indices=indices, adjusted_p_values=adjusted, correction=correction))
    # Original algorithm order and IEEE binary64 reference literals, never
    # obtained from the production multiple-testing formula or proof helper.
    cases = (
        case("bh_unsorted", "MATH-12", (.25, .03125), .125, 1, (1,), (.25, .0625), 1.0),
        case("bh_stable_ties", "MATH-12", (.5, .125, .125), .25, 2, (1, 2), (.5, .1875, .1875), 1.0),
        case("by_two", "MATH-13", (.03125, .25), .125, 1, (0,), (.09375, .375), 1.5),
        case("by_three_rounded_harmonic", "MATH-13", (.5, .125, .125), .5, 2, (1, 2), (.9166666666666666, .34375, .34375), 1.8333333333333333),
        case("by_rejection_differs_from_adjusted_comparison", "MATH-13", (.08333333333333334, 1.0), .25, 0, (), (.25, 1.0), 1.5),
        case("bh_positive_zero_last", "MATH-12", (-0.0, 0.0), .25, 2, (0, 1), (0.0, 0.0), 1.0),
        case("bh_negative_zero_last", "MATH-12", (0.0, -0.0), .25, 2, (0, 1), (-0.0, -0.0), 1.0),
        case("by_negative_zero_last", "MATH-13", (0.0, -0.0), .25, 2, (0, 1), (-0.0, -0.0), 1.5),
        case("bh_single_one", "MATH-12", (1.0,), .5, 0, (), (1.0,), 1.0),
        case("by_single_negative_zero", "MATH-13", (-0.0,), .5, 1, (0,), (-0.0,), 1.0),
    )
    def projection(raw):
        return dict(rows=[dict(original_index=i, adjusted_p=p, rejected=i in raw["rejected_original_indices"])
            for i, p in enumerate(raw["adjusted_p_values"])], correction=raw["correction"], largest_rank=raw["largest_rank"])
    def run(selected, work, *, inputs=None, raw=None, expected=None, projected=None, math_id=None):
        _, original_math, original_input, original_raw = selected
        return IndependentEvidenceReviewV1._bounded_review_multiple_testing_v1(original_math if math_id is None else math_id,
            deterministic_json(original_input if inputs is None else inputs).encode("utf-8"),
            deterministic_json(original_raw if raw is None else raw).encode("utf-8"),
            deterministic_json(original_raw if expected is None else expected).encode("utf-8"),
            deterministic_json(projection(original_raw) if projected is None else projected).encode("utf-8"), work=work)
    def forbidden(*args, **kwargs):raise AssertionError("independent multiple-testing proof invoked production formula or fsum")
    positives = []
    with ExitStack() as stack:
        for name in ("compute_math_12_v34", "compute_math_13_v34", "compute_math_12_benjamini_hochberg", "compute_math_13_benjamini_yekutieli", "_multiple_testing"):
            stack.enter_context(patch.object(formulas, name, forbidden))
        stack.enter_context(patch.object(math, "fsum", forbidden))
        for selected in cases:
            work = _EvidenceNumericalWorkV1(limits, retained_input_capacity=0)
            first = run(selected, work); prefix = dict(work.consumed)
            second = run(selected, work)
            assert first == second and work.state == "OPEN"
            assert work.consumed["serialized_bytes"] == 2 * prefix["serialized_bytes"] <= 65536
            assert all(work.consumed[key] == 0 for key in ("log_series_terms", "square_roots", "random_draws", "retained_decimal_inputs"))
            if selected[0] == "by_rejection_differs_from_adjusted_comparison":
                assert first["summary"]["largest_rank"] == 0 and selected[3]["adjusted_p_values"][0] == selected[2]["q"]
                assert all(row["satisfies_threshold"] == 0 for row in first["forward_thresholds"])
            if "zero" in selected[0]:
                assert first["sorted_source_indices"] == tuple(range(len(selected[2]["p_values"])))
                assert '-0.0' in first["summary"]["typed_input_json"]
            positives.append(dict(case=selected[0], proof=first, first_consumption=prefix, cumulative_consumption=dict(work.consumed)))
    base = cases[0]
    mutations = (
        ("negative_p", "inputs", lambda value: value["p_values"].__setitem__(0, -.125)),
        ("p_above_one", "inputs", lambda value: value["p_values"].__setitem__(0, 1.125)),
        ("integer_p", "inputs", lambda value: value["p_values"].__setitem__(0, 0)),
        ("boolean_p", "inputs", lambda value: value["p_values"].__setitem__(0, True)),
        ("scalar_p", "inputs", lambda value: value.update(p_values=.5)),
        ("empty_p", "inputs", lambda value: value.update(p_values=[])),
        ("zero_q", "inputs", lambda value: value.update(q=0.0)),
        ("one_q", "inputs", lambda value: value.update(q=1.0)),
        ("boolean_q", "inputs", lambda value: value.update(q=True)),
        ("text_q", "inputs", lambda value: value.update(q="0.125")),
        ("largest_rank", "raw", lambda value: value.update(largest_rank=0)),
        ("boolean_rank", "raw", lambda value: value.update(largest_rank=True)),
        ("wrong_index", "raw", lambda value: value.update(rejected_original_indices=[0])),
        ("boolean_index", "raw", lambda value: value.update(rejected_original_indices=[True])),
        ("index_omission", "raw", lambda value: value.update(rejected_original_indices=[])),
        ("adjusted_order", "raw", lambda value: value["adjusted_p_values"].reverse()),
        ("adjusted_ulp", "raw", lambda value: value["adjusted_p_values"].__setitem__(1, math.nextafter(.0625, 1.0))),
        ("adjusted_omission", "raw", lambda value: value["adjusted_p_values"].pop()),
        ("correction", "raw", lambda value: value.update(correction=1.5)),
        ("expected_value", "expected", lambda value: value["adjusted_p_values"].__setitem__(1, .125)),
        ("projection_row_order", "projected", lambda value: value["rows"].reverse()),
        ("projection_boolean_index", "projected", lambda value: value["rows"][1].update(original_index=True)),
        ("projection_rejection", "projected", lambda value: value["rows"][0].update(rejected=True)),
        ("projection_correction", "projected", lambda value: value.update(correction=1.5)),
    )
    denials = []
    for name, field, mutate in mutations:
        source = base[2] if field == "inputs" else projection(base[3]) if field == "projected" else base[3]
        value = json.loads(deterministic_json(source));mutate(value)
        work = _EvidenceNumericalWorkV1(limits, retained_input_capacity=0)
        with pytest.raises(ComputationControlPlaneError):run(base, work, **{field: value})
        assert work.state == "FAILED"
        with pytest.raises(ComputationControlPlaneError, match="LP03_NUMERICAL_WORK_NOT_OPEN"):run(base, work)
        denials.append(dict(case=name, failure=work.failure, consumed=dict(work.consumed)))
    wrong_zero = deepcopy(cases[6][3]);wrong_zero["adjusted_p_values"] = (0.0, 0.0)
    wrong_boundary = deepcopy(cases[4][3]);wrong_boundary.update(largest_rank=1, rejected_original_indices=(0,))
    extras = (
        ("unknown_math", base, {}, dict(math_id="MATH-11")),
        ("negative_zero_min_tie", cases[6], {}, dict(raw=wrong_zero)),
        ("rejection_from_adjusted_p", cases[4], {}, dict(raw=wrong_boundary)),
        ("zero_budget", base, dict(max_serialized_bytes=0), {}),
        ("aggregate_input_bytes", base, dict(max_serialized_bytes=256), {}),
        ("complete_bytes", base, dict(max_serialized_bytes=6000), {}),
        ("work_bits", base, dict(max_work_bits=1074), {}),
        ("input_bits", base, dict(max_input_bits=1), {}),
        ("complete_node_layout", base, {}, dict(inputs=dict(p_values=(.5,) * 41, q=.125))),
    )
    for name, selected, changes, arguments in extras:
        work = _EvidenceNumericalWorkV1(dict(limits, **changes), retained_input_capacity=0)
        with pytest.raises(ComputationControlPlaneError):run(selected, work, **arguments)
        assert work.state == "FAILED"
        denials.append(dict(case=name, failure=work.failure, consumed=dict(work.consumed)))
    print("LP03_MULTIPLE_TESTING_PURE_QUALIFICATION=" + deterministic_json(dict(
        scope="CLOSED_MATH12_MATH13_NUMERICAL_DATA_ONLY_NO_COMPLETE_TRIAL_LEDGER_OR_FDR_AUTHORITY", positives=positives, denials=denials)))



def _assert_lp03_calibration_ordered_proof():
    import math
    from copy import deepcopy
    from unittest.mock import patch
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane import implementation_registry as formulas
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.evidence import IndependentEvidenceReviewV1
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.parameter_policy import _EvidenceNumericalWorkV1
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import ComputationControlPlaneError
    limits = dict(max_input_bits=4096, max_work_bits=65536, max_serialized_bytes=65536)
    def bin_row(index, left, right, inclusive, count, confidence, frequency, gap):
        return dict(bin_index=index, left=left, right=right, right_inclusive=inclusive, count=count,
            mean_confidence=confidence, empirical_frequency=frequency, absolute_gap=gap)
    def case(name, probabilities, outcomes, policy, count, edges, bins, ece):
        return (name, dict(probabilities=probabilities, outcomes=outcomes, bin_policy=policy, bin_count=count),
            dict(bin_policy=policy, requested_bin_count=count, effective_edges=edges, bins=bins, expected_calibration_error=ece))
    # Hand-derived dyadic bins and ordered contributions. These literals are
    # independent of the production formula and of the proof implementation.
    common_bins = (bin_row(0, 0.0, 0.5, False, 2, 0.25, 0.5, 0.25), bin_row(1, 0.5, 1.0, True, 2, 0.75, 1.0, 0.25))
    cases = (
        case("equal_width", (0.125, 0.375, 0.625, 0.875), (0, 1, 1, 1), "EQUAL_WIDTH", 2, (0.0, 0.5, 1.0), common_bins, 0.25),
        case("equal_frequency_type7", (0.875, 0.125, 0.625, 0.375), (1, 0, 1, 1),
            "EQUAL_FREQUENCY_TYPE7_COLLAPSE_DUPLICATES", 2, (0.0, 0.5, 1.0), common_bins, 0.25),
        case("empty_bin", (0.25, 0.25), (0, 1), "EQUAL_WIDTH", 2, (0.0, 0.5, 1.0),
            (bin_row(0, 0.0, 0.5, False, 2, 0.25, 0.5, 0.25), bin_row(1, 0.5, 1.0, True, 0, None, None, None)), 0.25),
        case("duplicate_type7_edges", (0.5, 0.5, 0.5, 0.5), (0, 0, 0, 1),
            "EQUAL_FREQUENCY_TYPE7_COLLAPSE_DUPLICATES", 4, (0.0, 0.5, 1.0),
            (bin_row(0, 0.0, 0.5, False, 0, None, None, None), bin_row(1, 0.5, 1.0, True, 4, 0.5, 0.25, 0.25)), 0.25),
        case("signed_zero_source_and_endpoints", (-0.0, 1.0), (0, 1), "EQUAL_WIDTH", 2, (0.0, 0.5, 1.0),
            (bin_row(0, 0.0, 0.5, False, 1, 0.0, 0.0, 0.0), bin_row(1, 0.5, 1.0, True, 1, 1.0, 1.0, 0.0)), 0.0),
        case("internal_boundary_goes_right", (0.5, 1.0), (0, 1), "EQUAL_WIDTH", 2, (0.0, 0.5, 1.0),
            (bin_row(0, 0.0, 0.5, False, 0, None, None, None), bin_row(1, 0.5, 1.0, True, 2, 0.75, 0.5, 0.25)), 0.25),
    )
    def run(selected, work, *, inputs=None, raw=None, expected=None, projection=None):
        _, original_input, original_raw = selected
        return IndependentEvidenceReviewV1._bounded_review_calibration_v1(
            deterministic_json(original_input if inputs is None else inputs).encode("utf-8"),
            deterministic_json(original_raw if raw is None else raw).encode("utf-8"),
            deterministic_json(original_raw if expected is None else expected).encode("utf-8"),
            original_raw["expected_calibration_error"] if projection is None else projection, work=work)
    def forbidden(*args, **kwargs):
        raise AssertionError("independent calibration proof invoked production binning, percentile or fsum")
    positives = []
    with patch.object(formulas, "compute_math_10_expected_calibration_error_v2", forbidden), \
            patch.object(formulas, "_v34_type7", forbidden), patch.object(formulas, "_percentile", forbidden), patch.object(math, "fsum", forbidden):
        for selected in cases:
            work = _EvidenceNumericalWorkV1(limits, retained_input_capacity=0)
            first = run(selected, work)
            prefix = dict(work.consumed)
            second = run(selected, work)
            assert first == second and work.state == "OPEN"
            assert work.consumed["serialized_bytes"] == 2 * prefix["serialized_bytes"] <= 65536
            assert all(work.consumed[key] == 0 for key in ("log_series_terms", "square_roots", "random_draws", "retained_decimal_inputs"))
            assert first["summary"]["original_raw_json"] == first["summary"]["preregistered_raw_json"]
            if selected[0] == "signed_zero_source_and_endpoints":
                assert '[-0.0,1.0]' in first["summary"]["typed_input_json"]
            if selected[0] == "duplicate_type7_edges":
                assert first["summary"]["requested_bin_count"] == 4 and first["summary"]["effective_bin_count"] == 2
                assert first["sorted_source_indices"] == (0, 1, 2, 3)
            if selected[0] == "equal_frequency_type7":
                assert first["sorted_source_indices"] == (1, 3, 2, 0)
            positives.append(dict(case=selected[0], proof=first, first_consumption=prefix, cumulative_consumption=dict(work.consumed)))
    base = cases[0]
    mutations = (
        ("negative_probability", "inputs", lambda value: value["probabilities"].__setitem__(0, -0.125)),
        ("probability_above_one", "inputs", lambda value: value["probabilities"].__setitem__(0, 1.125)),
        ("integer_probability", "inputs", lambda value: value["probabilities"].__setitem__(0, 0)),
        ("scalar_probability", "inputs", lambda value: value.update(probabilities=0.5)),
        ("scalar_outcomes", "inputs", lambda value: value.update(outcomes=1)),
        ("omitted_outcome", "inputs", lambda value: value["outcomes"].pop()),
        ("boolean_outcome", "inputs", lambda value: value["outcomes"].__setitem__(0, True)),
        ("outcome_domain", "inputs", lambda value: value["outcomes"].__setitem__(0, 2)),
        ("zero_bin_count", "inputs", lambda value: value.update(bin_count=0)),
        ("boolean_bin_count", "inputs", lambda value: value.update(bin_count=True)),
        ("unknown_policy", "inputs", lambda value: value.update(bin_policy="CALLER_POLICY")),
        ("frequency_count", "inputs", lambda value: value.update(bin_policy="EQUAL_FREQUENCY_TYPE7_COLLAPSE_DUPLICATES", bin_count=5)),
        ("changed_edge", "raw", lambda value: value["effective_edges"].__setitem__(1, math.nextafter(0.5, 1.0))),
        ("omitted_edge", "raw", lambda value: value["effective_edges"].pop()),
        ("bin_order", "raw", lambda value: value["bins"].reverse()),
        ("bin_count", "raw", lambda value: value["bins"][0].update(count=1)),
        ("right_inclusion", "raw", lambda value: value["bins"][0].update(right_inclusive=True)),
        ("confidence", "raw", lambda value: value["bins"][0].update(mean_confidence=0.5)),
        ("frequency", "raw", lambda value: value["bins"][0].update(empirical_frequency=0.25)),
        ("gap", "raw", lambda value: value["bins"][0].update(absolute_gap=0.125)),
        ("ece_ulp", "raw", lambda value: value.update(expected_calibration_error=math.nextafter(0.25, 1.0))),
        ("expected_value", "expected", lambda value: value.update(expected_calibration_error=0.5)),
    )
    denials = []
    for name, field, mutate in mutations:
        value = json.loads(deterministic_json(base[1] if field == "inputs" else base[2]))
        mutate(value)
        work = _EvidenceNumericalWorkV1(limits, retained_input_capacity=0)
        with pytest.raises(ComputationControlPlaneError): run(base, work, **{field: value})
        assert work.state == "FAILED"
        with pytest.raises(ComputationControlPlaneError, match="LP03_NUMERICAL_WORK_NOT_OPEN"): run(base, work)
        denials.append(dict(case=name, failure=work.failure, consumed=dict(work.consumed)))
    rounded_edges = case("nonexact_equal_width", base[1]["probabilities"], base[1]["outcomes"], "EQUAL_WIDTH", 3,
        (0.0, 0.3333333333333333, 0.6666666666666666, 1.0),
        (bin_row(0, 0.0, 0.3333333333333333, False, 1, 0.125, 0.0, 0.125),
         bin_row(1, 0.3333333333333333, 0.6666666666666666, False, 2, 0.5, 1.0, 0.5),
         bin_row(2, 0.6666666666666666, 1.0, True, 1, 0.875, 1.0, 0.125)), 0.3125)
    rounded_sum = case("nonexact_fsum", (0.1, 0.2), (0, 0), "EQUAL_WIDTH", 1, (0.0, 1.0),
        (bin_row(0, 0.0, 1.0, True, 2, 0.15000000000000002, 0.0, 0.15000000000000002),), 0.15000000000000002)
    empty = deepcopy(cases[2][2]);empty["bins"][1]["mean_confidence"] = 0.0
    wrong_zero = deepcopy(cases[4][2]);wrong_zero["expected_calibration_error"] = -0.0
    extras = (
        ("projection", base, {}, dict(projection=0.5)),
        ("empty_bin_numeric", cases[2], {}, dict(raw=empty)),
        ("zero_output_sign", cases[4], {}, dict(raw=wrong_zero)),
        ("nonexact_equal_width", rounded_edges, {}, {}),
        ("nonexact_fsum", rounded_sum, {}, {}),
        ("zero_budget", base, dict(max_serialized_bytes=0), {}),
        ("tiny_serialization", base, dict(max_serialized_bytes=512), {}),
        ("work_bits", base, dict(max_work_bits=1074), {}),
        ("input_bits", base, dict(max_input_bits=1), {}),
    )
    for name, selected, changes, arguments in extras:
        work = _EvidenceNumericalWorkV1(dict(limits, **changes), retained_input_capacity=0)
        with pytest.raises(ComputationControlPlaneError): run(selected, work, **arguments)
        assert work.state == "FAILED"
        if name.startswith("nonexact_"):
            assert work.failure == "LP03_CALIBRATION_REVIEW_NONEXACT_BINARY64_INTERMEDIATE"
        denials.append(dict(case=name, failure=work.failure, consumed=dict(work.consumed)))
    print("LP03_CALIBRATION_PURE_QUALIFICATION=" + deterministic_json(dict(
        scope="CLOSED_MATH10_EXACT_NUMERICAL_DATA_ONLY_NO_SOURCE_OR_NATIVE_AUTHORITY", positives=positives, denials=denials)))


def _assert_lp03_log_loss_enclosure_proof():
    import math
    from copy import deepcopy
    from unittest.mock import patch
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane import implementation_registry as formulas
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.evidence import IndependentEvidenceReviewV1
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.parameter_policy import _EvidenceNumericalWorkV1
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import ComputationControlPlaneError
    limits = dict(max_input_bits=4096, max_work_bits=65536, max_serialized_bytes=65536)
    # Literal expectations were derived independently with high-precision
    # Decimal logarithms. No native production result supplies these values.
    cases = (
        ("interior_and_upper_clip", ((0.5, 0.5), (0.0, 1.0)), (1, 1), 0.125,
            (0.6931471805599453, 0.13353139262452263), 0.41333928659223396),
        ("lower_clip", ((0.0, 1.0),), (0,), 0.125, (2.0794415416798357,), 2.0794415416798357),
        ("lower_tie", ((0.125, 0.875),), (0,), 0.125, (2.0794415416798357,), 2.0794415416798357),
        ("upper_tie", ((0.125, 0.875),), (1,), 0.125, (0.13353139262452263,), 0.13353139262452263),
        ("negative_zero_source", ((-0.0, 1.0),), (0,), 0.125, (2.0794415416798357,), 2.0794415416798357),
        ("negated_log_one_and_positive_mean_zero", ((-0.0, 1.0),), (1,), 2.0**-54, (-0.0,), 0.0),
        ("inexact_upper_clip", ((0.0, 1.0),), (1,), 0.1, (0.10536051565782628,), 0.10536051565782628),
        ("row_sum_nearest_even_tie", ((0.5000000000000001, 0.5),), (1,), 0.125, (0.6931471805599453,), 0.6931471805599453),
    )
    def run(case, work, *, inputs=None, raw=None, expected=None, projection=None):
        name, rows, outcomes, epsilon, scores, mean = case
        inputs = inputs if inputs is not None else dict(probability_rows=rows, outcome_indices=outcomes, clip_epsilon=epsilon)
        raw = raw if raw is not None else dict(per_observation=scores, mean_log_loss=mean)
        expected = expected if expected is not None else dict(per_observation=scores, mean_log_loss=mean)
        return IndependentEvidenceReviewV1._bounded_review_log_loss_v1(
            deterministic_json(inputs).encode("utf-8"), deterministic_json(raw).encode("utf-8"),
            deterministic_json(expected).encode("utf-8"), mean if projection is None else projection, work=work)
    def forbidden(*args, **kwargs):
        raise AssertionError("independent log-loss proof invoked production logarithm or summation")
    positives = []
    with patch.object(formulas, "compute_math_09_v34", forbidden), patch.object(math, "log", forbidden), patch.object(math, "fsum", forbidden):
        for case in cases:
            work = _EvidenceNumericalWorkV1(limits, retained_input_capacity=0)
            first = run(case, work)
            prefix = dict(work.consumed)
            second = run(case, work)
            assert first == second and work.state == "OPEN"
            assert work.consumed["serialized_bytes"] == 2 * prefix["serialized_bytes"] <= 65536
            assert work.consumed["log_series_terms"] == 2 * prefix["log_series_terms"]
            assert work.consumed["random_draws"] == work.consumed["retained_decimal_inputs"] == 0
            assert first["intermediate_observation_scope"] == "ROW_AND_SCORE_SUMS_ARE_DERIVED_NOT_OBSERVED"
            assert first["derived_score_sum"]["operation"] == "DERIVED_UNOBSERVED_SCORE_FSUM"
            assert first["summary"]["original_raw_json"] == first["summary"]["preregistered_raw_json"]
            if case[0] == "negated_log_one_and_positive_mean_zero":
                assert first["per_observation"][0]["logarithm"]["candidate_bits"] == "8000000000000000"
                assert first["final_division"]["candidate_bits"] == "0000000000000000"
                assert prefix["log_series_terms"] == 0
            if case[0] in ("negative_zero_source", "negated_log_one_and_positive_mean_zero"):
                assert '[-0.0,1.0]' in first["summary"]["typed_input_json"]
            if case[0] == "lower_tie":
                assert first["per_observation"][0]["selection"]["lower_selected_index"] == 0
            if case[0] == "upper_tie":
                assert first["per_observation"][0]["selection"]["upper_selected_index"] == 0
            positives.append(dict(case=case[0], proof=first, first_consumption=prefix, cumulative_consumption=dict(work.consumed)))
    base = cases[0]
    good_inputs = dict(probability_rows=[list(row) for row in base[1]], outcome_indices=list(base[2]), clip_epsilon=base[3])
    good_raw = dict(per_observation=list(base[4]), mean_log_loss=base[5])
    mutations = (
        ("epsilon_zero", "inputs", lambda data: data.update(clip_epsilon=0.0)),
        ("epsilon_half", "inputs", lambda data: data.update(clip_epsilon=0.5)),
        ("epsilon_boolean", "inputs", lambda data: data.update(clip_epsilon=True)),
        ("negative_probability", "inputs", lambda data: data["probability_rows"][0].__setitem__(0, -0.1)),
        ("probability_above_one", "inputs", lambda data: data["probability_rows"][0].__setitem__(0, 1.1)),
        ("row_sum", "inputs", lambda data: data["probability_rows"][0].__setitem__(0, 0.50000001)),
        ("ragged", "inputs", lambda data: data["probability_rows"][0].pop()),
        ("outcome_omission", "inputs", lambda data: data["outcome_indices"].pop()),
        ("outcome_boolean", "inputs", lambda data: data["outcome_indices"].__setitem__(0, True)),
        ("outcome_outside", "inputs", lambda data: data["outcome_indices"].__setitem__(0, 2)),
        ("one_ulp_log_error", "raw", lambda data: data["per_observation"].__setitem__(0, math.nextafter(base[4][0], math.inf))),
        ("score_order", "raw", lambda data: data["per_observation"].reverse()),
        ("score_omission", "raw", lambda data: data["per_observation"].pop()),
        ("mean_error", "raw", lambda data: data.update(mean_log_loss=math.nextafter(base[5], math.inf))),
        ("expected_error", "expected", lambda data: data["per_observation"].__setitem__(1, 0.125)),
    )
    denials = []
    for name, field, mutate in mutations:
        data = deepcopy(good_inputs if field == "inputs" else good_raw)
        mutate(data)
        work = _EvidenceNumericalWorkV1(limits, retained_input_capacity=0)
        with pytest.raises(ComputationControlPlaneError):
            run(base, work, **{field: data})
        assert work.state == "FAILED"
        with pytest.raises(ComputationControlPlaneError, match="LP03_NUMERICAL_WORK_NOT_OPEN"):
            run(base, work)
        denials.append(dict(case=name, failure=work.failure, consumed=dict(work.consumed)))
    extra = (
        ("projection_error", base, {}, dict(projection=0.4)),
        ("log_zero_wrong_sign", cases[5], {}, dict(raw=dict(per_observation=(0.0,), mean_log_loss=0.0))),
        ("mean_zero_wrong_sign", cases[5], {}, dict(raw=dict(per_observation=(-0.0,), mean_log_loss=-0.0))),
        ("zero_budget", base, dict(max_serialized_bytes=0), {}),
        ("tiny_serialization", base, dict(max_serialized_bytes=256), {}),
        ("work_bits", base, dict(max_work_bits=1074), {}),
        ("input_bits", base, dict(max_input_bits=8), {}),
    )
    for name, case, changes, arguments in extra:
        work = _EvidenceNumericalWorkV1(dict(limits, **changes), retained_input_capacity=0)
        with pytest.raises(ComputationControlPlaneError):
            run(case, work, **arguments)
        assert work.state == "FAILED"
        denials.append(dict(case=name, failure=work.failure, consumed=dict(work.consumed)))
    print("LP03_LOG_LOSS_PURE_QUALIFICATION=" + deterministic_json(dict(
        scope="CLOSED_MATH09_NUMERICAL_DATA_ONLY_NO_SOURCE_OR_NATIVE_AUTHORITY", positives=positives, denials=denials)))


def _lp03_numeric_work(limits):
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.parameter_policy import _EvidenceNumericalWorkV1
    return _EvidenceNumericalWorkV1(limits, retained_input_capacity=64)


def _assert_lp03_recorded_dr_uncertainty() -> None:
    from copy import deepcopy
    from fractions import Fraction
    from math import copysign
    from unittest.mock import patch
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane import specification
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import ComputationControlPlaneError
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.evidence_execution import measure_dr_score_uncertainty_v1
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.implementation_registry import (
        _evidence_snapshot_version_pins_v1, resolve_evidence_invocation_v1, invoke_evidence_public_wire_v1,
    )
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.models import EvidenceOriginV1

    def wire(value):
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    def rational(value):
        return Fraction(int(value["numerator"]), int(value["denominator"]))

    inputs = dict(logged_rows=[dict(row_id=f"row-{index + 1}", behavior_action_probabilities=[1.0],
        target_action_probabilities=[1.0], cross_fitted_reward_model_predictions=[0.0], logged_action_index=0,
        fold_id=index // 2, cross_fitted_prediction=True, reward=reward)
        for index, reward in enumerate((0.1, 0.2, 0.3, 0.4))])
    specifications, implementations = _evidence_snapshot_version_pins_v1()
    contract = resolve_evidence_invocation_v1("MATH-22", implementation_pin=implementations["MATH-22"],
        specification_pin=specifications["MATH-22"], resource_policy_ref="LP03-TEST::DR-RESOURCES",
        origin=EvidenceOriginV1.SOFTWARE_CONFORMANCE)
    original = invoke_evidence_public_wire_v1(contract, wire(inputs), maximum_input_bytes=65536,
        maximum_nodes=4096, maximum_output_bytes=65536, maximum_output_nodes=4096)
    raw = json.loads(original.output_json)
    assert raw == dict(doubly_robust_estimate=0.25, row_values=[0.1, 0.2, 0.3, 0.4],
        importance_weights=[1.0] * 4, effective_sample_size=4.0, clipping_applied=False)
    policy = dict(profile="RECORDED_DR_EQUAL_GROUPS_V1", protocol_ref="LP03-TEST::DR-POLICY",
        raw_receipt_ref="LP03-TEST::RAW22", input_receipt_ref="LP03-TEST::INPUT22",
        row_ids=["row-1", "row-2", "row-3", "row-4"],
        groups=[dict(ordinal=1, row_ids=["row-1", "row-2"]), dict(ordinal=2, row_ids=["row-3", "row-4"])],
        group_weights=["1", "1"], group_lower="0", group_upper="1", alpha="0.05", claim_ordinal=1,
        unit="REWARD_UNIT", basis="SYNTHETIC_RECORDED_REWARD", logging_policy_ref="LP03-TEST::LOGGING",
        support_receipt_ref="LP03-TEST::SUPPORT", reward_basis_ref="LP03-TEST::REWARD",
        crossfit_plan_ref="LP03-TEST::CROSSFIT", conditional_target_assumption_ref="LP03-TEST::CONDITIONAL",
        group_bound_proof_ref="LP03-TEST::GROUP-BOUNDS",
        crossfit_records=[dict(fold_id=0, training_row_ids=["row-3", "row-4"], evaluation_row_ids=["row-1", "row-2"],
            prediction_receipt_ref="LP03-TEST::PREDICTION0", training_exclusion_ref="LP03-TEST::EXCLUSION0"),
            dict(fold_id=1, training_row_ids=["row-1", "row-2"], evaluation_row_ids=["row-3", "row-4"],
            prediction_receipt_ref="LP03-TEST::PREDICTION1", training_exclusion_ref="LP03-TEST::EXCLUSION1")])
    limits = dict(max_input_bits=4096, max_work_bits=65536, max_serialized_bytes=65536)

    def calculate(*, selected_policy=None, selected_raw=None, selected_inputs=None, work=None, **budgets):
        arguments = dict(raw_json=original.output_json if selected_raw is None else wire(selected_raw),
            input_json=original.input_json if selected_inputs is None else wire(selected_inputs),
            policy_json=wire(policy if selected_policy is None else selected_policy),
            maximum_input_bytes=65536, maximum_input_nodes=4096, maximum_output_bytes=65536, maximum_output_nodes=4096,
            work=_lp03_numeric_work(limits) if work is None else work)
        arguments.update(budgets)
        result = measure_dr_score_uncertainty_v1(**arguments)
        return json.loads(result), result, arguments["work"]

    result, encoded, work = calculate()
    assert result["disposition"] == "CONDITIONAL_DATA_CALCULATION" and result["reasons"] == []
    assert result["target"] == "MEAN_CONDITIONAL_RECORDED_DR_SCORE"
    assert result["original_raw"] == raw and wire(result["original_raw"]) == original.output_json
    assert wire(result["original_input"]) == original.input_json and result["original_policy"] == policy
    assert result["source_admission"] == result["measurement_model_uncertainty"] == "NOT_ESTABLISHED_BY_DATA_PROCEDURE"
    assert rational(result["arithmetic"]["row_mean"]) == Fraction(1, 4) + Fraction(1, 2**57)
    assert rational(result["arithmetic"]["represented_estimator"]) == Fraction(1, 4)
    assert rational(result["arithmetic"]["estimator_minus_row_mean"]) == -Fraction(1, 2**57)
    assert [rational(group["mean"]) for group in result["group_means"]] == [
        Fraction(10808639105689191, 2**56), Fraction(12610078956637389, 2**55)]
    assert result["interval"]["n"] == 2 and result["interval"]["claim_ordinal"] == 1
    assert rational(result["interval"]["delta"]) == Fraction(1, 240)
    assert rational(result["interval"]["mean"]) == rational(result["arithmetic"]["row_mean"])
    assert rational(result["interval"]["lower"]) == 0 and rational(result["interval"]["upper"]) == 1
    assert work.consumed["log_series_terms"] == 128 and work.consumed["square_roots"] == 1
    assert work.consumed["serialized_bytes"] > len(encoded) and work.state == "OPEN"
    # Original binary64/policy inputs fit 56 bits. The first exact group mean
    # has a 57-bit denominator and is governed by max_work_bits, not input bits.
    narrow_inputs = _lp03_numeric_work(dict(limits, max_input_bits=56))
    narrow_result, narrow_encoded, _ = calculate(work=narrow_inputs)
    assert narrow_encoded == encoded and narrow_result == result and narrow_inputs.state == "OPEN"
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.parameter_policy import certify_evidence_conditional_mean_v1
    external = _lp03_numeric_work(dict(limits, max_input_bits=56))
    with pytest.raises(ComputationControlPlaneError, match="INPUT_BITS_EXHAUSTED"):
        certify_evidence_conditional_mean_v1((Fraction(10808639105689191, 2**56),), lower=0, upper=1,
            alpha=Fraction(1, 20), claim_ordinal=1, work=external)
    assert external.state == "FAILED"

    # The original primitive permits noncontiguous predeclared groups. Preserve
    # their row order and membership; do not sort groups by observed outcomes.
    alternate = deepcopy(policy)
    alternate["groups"][0]["row_ids"] = ["row-1", "row-3"]
    alternate["groups"][1]["row_ids"] = ["row-2", "row-4"]
    alternate_result, _, _ = calculate(selected_policy=alternate)
    assert alternate_result["disposition"] == "CONDITIONAL_DATA_CALCULATION"
    assert alternate_result["original_policy"]["groups"] == alternate["groups"]
    assert rational(alternate_result["interval"]["mean"]) == rational(result["interval"]["mean"])

    cases = []
    def changed(reason, mutate):
        selected = deepcopy(policy)
        mutate(selected)
        cases.append((selected, reason))
    changed("UNEQUAL_OR_EMPTY_GROUP_SIZES", lambda p: (p["groups"][0].update(row_ids=["row-1"]), p["groups"][1].update(row_ids=["row-2", "row-3", "row-4"])))
    changed("UNEQUAL_OR_NONPOSITIVE_GROUP_WEIGHTS", lambda p: p.update(group_weights=["1", "2"]))
    changed("INCOMPLETE_ORDERED_GROUP_PREFIX", lambda p: p["groups"][1].update(ordinal=3))
    changed("INCOMPLETE_ORDERED_GROUP_PREFIX", lambda p: p["groups"].reverse())
    changed("INCOMPLETE_GROUP_MEMBERSHIP", lambda p: p["groups"][1].update(row_ids=["row-2", "row-4"]))
    changed("GROUP_ROW_ORDER_CHANGED", lambda p: p["groups"][0]["row_ids"].reverse())
    changed("RAW_INPUT_ROW_ROSTER_MISMATCH", lambda p: p["row_ids"].reverse())
    changed("OUTCOME_LEAKING_NUISANCE_FIT", lambda p: p["crossfit_records"][0]["training_row_ids"].append("row-1"))
    changed("CROSSFIT_FOLD_MEMBERSHIP_MISMATCH", lambda p: p["crossfit_records"][0].update(fold_id=9))
    changed("INCOMPLETE_CROSSFIT_COVERAGE", lambda p: p["crossfit_records"].pop())
    changed("MISSING_CROSSFIT_PRODUCER_RECORDS", lambda p: p["crossfit_records"][0].update(training_exclusion_ref=None))
    for field in ("group_lower", "group_upper", "alpha", "logging_policy_ref", "support_receipt_ref", "reward_basis_ref",
                  "crossfit_plan_ref", "conditional_target_assumption_ref", "group_bound_proof_ref"):
        changed("MISSING_" + field.upper(), lambda p, name=field: p.update({name: None}))
    for selected, expected in cases:
        actual, _, unavailable_work = calculate(selected_policy=selected)
        assert actual["disposition"] == "UNCERTAINTY_UNAVAILABLE" and expected in actual["reasons"]
        assert actual["interval"] is actual["arithmetic"] is None and actual["group_means"] == []
        assert actual["original_raw"] == raw and actual["original_policy"] == selected
        assert unavailable_work.consumed["log_series_terms"] == 0 and unavailable_work.state == "OPEN"

    negative_zero = deepcopy(raw)
    negative_zero["row_values"][0] = -0.0
    actual, _, _ = calculate(selected_raw=negative_zero)
    assert actual["disposition"] == "UNCERTAINTY_UNAVAILABLE"
    assert "NEGATIVE_ZERO_STATISTICAL_INPUT_UNSUPPORTED" in actual["reasons"]
    assert copysign(1, actual["original_raw"]["row_values"][0]) == -1
    assert wire(actual["original_raw"]) == wire(negative_zero)

    # Bounds are on complete group means, not inferred row extrema.
    wider_rows = deepcopy(raw)
    wider_rows["row_values"] = [-1.0, 2.0, -2.0, 3.0]
    bounded_groups, _, _ = calculate(selected_raw=wider_rows)
    assert bounded_groups["disposition"] == "CONDITIONAL_DATA_CALCULATION"
    assert rational(bounded_groups["arithmetic"]["row_mean"]) == Fraction(1, 2)
    assert rational(bounded_groups["arithmetic"]["estimator_minus_row_mean"]) == -Fraction(1, 4)
    # This altered data is deliberately not a producer-authentic fixture.
    assert bounded_groups["source_admission"] == "NOT_ESTABLISHED_BY_DATA_PROCEDURE"

    for change in (dict(claim_ordinal=True), dict(alpha="NaN"), dict(alpha="1"), dict(group_upper="0"), dict(unexpected="x")):
        selected = dict(policy, **change)
        failed = _lp03_numeric_work(limits)
        with pytest.raises(ComputationControlPlaneError):
            calculate(selected_policy=selected, work=failed)
        assert failed.state == "FAILED"
    with patch.object(specification, "decode_evidence_raw_output_v1", side_effect=AssertionError("decode before admission")):
        for budgets in (dict(maximum_input_bytes=1), dict(maximum_output_bytes=0), dict(maximum_output_nodes=True)):
            with pytest.raises(ComputationControlPlaneError):
                calculate(**budgets)
    for budgets in (dict(maximum_input_nodes=32), dict(maximum_output_nodes=4), dict(maximum_output_bytes=1)):
        failed = _lp03_numeric_work(limits)
        with pytest.raises(ComputationControlPlaneError):
            calculate(work=failed, **budgets)
        assert failed.state == "FAILED"
    for changes in (dict(max_input_bits=1), dict(max_work_bits=8), dict(max_serialized_bytes=64)):
        failed = _lp03_numeric_work(dict(limits, **changes))
        with pytest.raises(ComputationControlPlaneError):
            calculate(work=failed)
        assert failed.state == "FAILED"
        retained = dict(failed.consumed)
        with pytest.raises(ComputationControlPlaneError, match="WORK_NOT_OPEN"):
            calculate(work=failed)
        assert dict(failed.consumed) == retained


def _assert_lp03_certified_numerical_boundaries() -> None:
    """Independent decimal/analytic checks in the original collected B group."""
    from decimal import Context, ROUND_DOWN, localcontext
    from fractions import Fraction
    from math import nextafter, inf
    from sys import float_info
    from types import MappingProxyType
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import ContractValidationError
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.parameter_policy import (
        _EvidenceNumericalWorkV1,
        certify_evidence_binary64_v1,
        certify_evidence_conditional_mean_v1,
    )

    # Explicit finite software-test inputs; no financial/claim-policy defaults.
    limits = dict(max_input_bits=4096, max_work_bits=65536, max_serialized_bytes=65536)

    def rational(result, name):
        pair = result[name]
        assert set(pair) == {"numerator", "denominator"}
        return Fraction(int(pair["numerator"]), int(pair["denominator"]))

    def conversion(source, work, **metadata):
        # These test-owned fixed Decimal literals supply original text to the
        # bounded parser; production never formats an unadmitted Decimal.
        if type(source) is Decimal:
            source = work.parse_decimal_v1(str(source))
        return certify_evidence_binary64_v1(source, math_id=metadata.get("math_id", "MATH-29"),
            unit=metadata.get("unit", "USD"), basis=metadata.get("basis", "ORIGINAL_WEIGHTS"), work=work)

    # Decimal ln/sqrt is a distinct reconstruction, never the production series.
    for values, low, high, alpha, ordinal in (
        ((Fraction(1, 2),), 0, 1, Fraction(1, 20), 1),
        ((Fraction(1, 4), Fraction(3, 4)) * 32, 0, 1, Fraction(1, 10), 2),
        ((-2, 0, 2, 1) * 8, -2, 2, Fraction(1, 3), 7),
        ((0.1, 0.2, 0.3, 0.4), 0, 1, Fraction(1, 100), 3),
    ):
        work = _lp03_numeric_work(limits)
        result = certify_evidence_conditional_mean_v1(values, lower=low, upper=high,
            alpha=alpha, claim_ordinal=ordinal, work=work)
        count = len(values)
        mean = sum(map(Fraction, values), Fraction()) / count
        allocated = alpha / (ordinal * (ordinal + 1) * count * (count + 1))
        assert rational(result, "mean") == mean
        assert rational(result, "delta") == allocated
        assert result["n"] == count and result["claim_ordinal"] == ordinal
        log_low, log_high = rational(result, "log_lower"), rational(result, "log_upper")
        radius = rational(result, "radius_upper")
        root = radius / (high - low)
        assert root * root >= log_high / (2 * count)
        assert (root - Fraction(1, 2**128)) ** 2 < log_high / (2 * count)
        assert rational(result, "lower") == max(Fraction(low), mean - radius)
        assert rational(result, "upper") == min(Fraction(high), mean + radius)
        with localcontext(Context(prec=180)):
            def decimal(q):
                return Decimal(q.numerator) / Decimal(q.denominator)
            logarithm = (Decimal(2) / decimal(allocated)).ln()
            analytical_radius = Decimal(high - low) * (logarithm / (2 * count)).sqrt()
            # The 180-digit reconstruction's enclosure is much tighter than
            # the specified fixed-series remainder; no production tolerance.
            oracle_unit = Decimal("1e-170")
            assert decimal(log_low) <= logarithm - oracle_unit
            assert logarithm + oracle_unit <= decimal(log_high)
            assert decimal(radius) >= analytical_radius + oracle_unit
        assert work.consumed["log_series_terms"] == 128
        assert work.consumed["square_roots"] == 1
        assert work.consumed["integer_operations"] > 0 and work.consumed["comparisons"] > 0
        assert work.consumed["serialized_bytes"] == len(deterministic_json(result).encode("utf-8"))
        assert type(result) is MappingProxyType and work.state == "OPEN"
        with pytest.raises(TypeError):
            result["mean"]["numerator"] = "0"

    # Original exact values, fixed binary64 tie cases, both subnormal signs.
    vectors = (
        (Decimal("0.1"), float.fromhex("0x1.999999999999ap-4")),
        (Fraction(1) + Fraction(1, 2**53), 1.0),
        (Fraction(1) + Fraction(3, 2**53), float.fromhex("0x1.0000000000002p+0")),
        (Fraction(-1) - Fraction(1, 2**53), -1.0),
        (Fraction(1, 2**1074), float.fromhex("0x0.0000000000001p-1022")),
        (Fraction(-1, 2**1074), -float.fromhex("0x0.0000000000001p-1022")),
        (Decimal("0"), 0.0),
    )
    for source, expected in vectors:
        work = _lp03_numeric_work(limits)
        result = conversion(source, work)
        exact, represented = Fraction(source), Fraction(expected)
        assert result["analytic_value"].hex() == expected.hex()
        assert rational(result, "exact_source") == exact
        assert rational(result, "signed_error") == represented - exact
        assert rational(result, "enclosing_lower") <= exact <= rational(result, "enclosing_upper")
        assert rational(result, "enclosing_lower") <= represented <= rational(result, "enclosing_upper")
        if exact != represented:
            lower, upper = rational(result, "enclosing_lower"), rational(result, "enclosing_upper")
            assert float(upper) == nextafter(float(lower), inf)
    decimal_result = conversion(Decimal("0.1"), _lp03_numeric_work(limits))
    assert rational(decimal_result, "signed_error") == Fraction(1, 180143985094819840)

    # Source-size limits apply to actual reduced inputs, not certificate work.
    for source in (1, Fraction(1), Decimal("1.0000")):
        work = _lp03_numeric_work(dict(limits, max_input_bits=1))
        assert conversion(source, work)["analytic_value"] == 1.0
        assert work.consumed["peak_preflight_bits"] > 1
    with localcontext(Context(prec=2, rounding=ROUND_DOWN)):
        altered = conversion(Decimal("0.1"), _lp03_numeric_work(limits))
    assert deterministic_json(altered) == deterministic_json(decimal_result)

    for bad, diagnostic in (
        (True, "EXACT_INPUT_TYPE"), (Decimal("-0"), "EXACT_INPUT_DOMAIN"),
        (Decimal("NaN"), "EXACT_INPUT_DOMAIN"), (Decimal("Infinity"), "EXACT_INPUT_DOMAIN"),
        (0.1, "EXACT_INPUT_TYPE"), (Fraction(1, 2**1076), "BINARY64_UNREPRESENTABLE"),
        (Fraction(2**1024), "BINARY64_UNREPRESENTABLE"),
        (Fraction(float_info.max), "FINITE_ROUNDING_CELL_REQUIRED"),
    ):
        work = _lp03_numeric_work(limits)
        with pytest.raises(ContractValidationError, match=diagnostic):
            conversion(bad, work)
        assert work.state == "FAILED"
        retained, failure = dict(work.consumed), work.failure
        with pytest.raises(ContractValidationError, match="WORK_NOT_OPEN"):
            conversion(1, work)
        assert dict(work.consumed) == retained and work.failure == failure

    for changes, diagnostic in (
        ({"values": ()}, "COMPLETE_PREFIX_DATA_REQUIRED"),
        ({"values": [0]}, "COMPLETE_PREFIX_DATA_REQUIRED"),
        ({"values": (True,)}, "EXACT_INPUT_TYPE"),
        ({"values": (-0.0,)}, "BINARY64_INPUT_DOMAIN"),
        ({"values": (2,)}, "OBSERVATION_OUT_OF_BOUNDS"),
        ({"claim_ordinal": True}, "POSITIVE_ORDINAL_REQUIRED"),
        ({"alpha": 0}, "BOUND_OR_ALPHA_DOMAIN"),
        ({"alpha": 1}, "BOUND_OR_ALPHA_DOMAIN"),
        ({"upper": 0}, "BOUND_OR_ALPHA_DOMAIN"),
    ):
        work = _lp03_numeric_work(limits)
        arguments = dict(values=(0,), lower=0, upper=1, alpha=Fraction(1, 20), claim_ordinal=1, work=work)
        arguments.update(changes)
        with pytest.raises(ContractValidationError, match=diagnostic):
            certify_evidence_conditional_mean_v1(**arguments)
        assert work.state == "FAILED"

    for changes, diagnostic in (
        ({"max_work_bits": 8}, "WORK_BITS_EXHAUSTED"),
        ({"max_input_bits": 1}, "INPUT_BITS_EXHAUSTED"),
        ({"max_serialized_bytes": 1}, "SERIALIZATION_EXHAUSTED"),
        ({"max_input_bits": 0}, "ZERO_BUDGET"),
        ({"max_work_bits": 0}, "ZERO_BUDGET"),
        ({"max_serialized_bytes": 0}, "ZERO_BUDGET"),
    ):
        work = _lp03_numeric_work(dict(limits, **changes))
        with pytest.raises(ContractValidationError, match=diagnostic):
            conversion(Decimal("0.1"), work)
        assert work.state == "FAILED"
    work = _lp03_numeric_work(limits)
    with pytest.raises(ContractValidationError, match="WORK_BITS_EXHAUSTED"):
        conversion(Decimal("1e1000000"), work)
    assert work.consumed["integer_powers"] == 0 and work.consumed["decimal_constructions"] == 0

    # No tuple conversion, formatting or equality is needed to deny a foreign
    # Decimal. Equal numerical values from another parser are still foreign.
    for unadmitted in (Decimal("0.1"), Decimal("1" + "0" * 100000)):
        work = _lp03_numeric_work(limits)
        with pytest.raises(ContractValidationError, match="ORIGINAL_BOUNDED_NUMERICAL_DECIMAL_REQUIRED"):
            certify_evidence_binary64_v1(unadmitted, math_id="MATH-29", unit="USD", basis="ORIGINAL_WEIGHTS", work=work)
        assert work.state == "FAILED" and work.consumed["integer_operations"] == 0
    first_owner, second_owner = _lp03_numeric_work(limits), _lp03_numeric_work(limits)
    first, equal = first_owner.parse_decimal_v1("1.0000"), second_owner.parse_decimal_v1("1.0000")
    assert first == equal and first is not equal and str(first) == "1.0000"
    with pytest.raises(ContractValidationError, match="ORIGINAL_BOUNDED_NUMERICAL_DECIMAL_REQUIRED"):
        certify_evidence_binary64_v1(equal, math_id="MATH-29", unit="USD", basis="ORIGINAL_WEIGHTS", work=first_owner)
    work = _lp03_numeric_work(limits)
    with pytest.raises(ContractValidationError, match="WORK_BITS_EXHAUSTED"):
        work.parse_decimal_v1("1" * 65537)
    assert work.consumed["integer_operations"] == 0 and work.consumed["decimal_constructions"] == 0
    work = _EvidenceNumericalWorkV1(limits, retained_input_capacity=1)
    retained_decimal = work.parse_decimal_v1("1.00")
    retained = dict(work.consumed)
    with pytest.raises(ContractValidationError, match="RETAINED_INPUT_CAPACITY_EXHAUSTED"):
        work.parse_decimal_v1("1.00")
    assert work.state == "FAILED" and work.consumed["decimal_constructions"] == 1
    assert work.consumed["retained_decimal_inputs"] == 1 and work.consumed["decimal_parse_attempts"] == 2
    assert work._decimal_inputs[id(retained_decimal)][0] is retained_decimal
    assert work.consumed["integer_operations"] == retained["integer_operations"]
    for change in ("replacement", "omission", "foreign_insertion"):
        work = _lp03_numeric_work(limits)
        admitted = work.parse_decimal_v1("0.1")
        entry = work._decimal_inputs[id(admitted)]
        if change == "replacement":
            work._decimal_inputs[id(admitted)] = (admitted, Fraction(9, 10), entry[2])
        elif change == "omission":
            del work._decimal_inputs[id(admitted)]
        else:
            foreign = Decimal("0.2")
            work._decimal_inputs[id(foreign)] = (foreign, Fraction(1, 5), "0.2")
        retained = dict(work.consumed)
        with pytest.raises(ContractValidationError, match="ORIGINAL_DECIMAL_ADMISSION_ROSTER_REQUIRED"):
            certify_evidence_binary64_v1(admitted, math_id="MATH-29", unit="USD", basis="ORIGINAL_WEIGHTS", work=work)
        assert work.state == "FAILED" and dict(work.consumed) == retained
        assert work._decimal_admissions == (entry,) and work._decimal_admissions[0] is entry
    work = _lp03_numeric_work(limits)
    admitted = work.parse_decimal_v1("0.1")
    del work._decimal_inputs[id(admitted)]
    with pytest.raises(ContractValidationError, match="ORIGINAL_DECIMAL_ADMISSION_ROSTER_REQUIRED"):
        work.parse_decimal_v1("0.2")
    assert work.consumed["decimal_parse_attempts"] == 1 and work.consumed["retained_decimal_inputs"] == 1

    for metadata in ({"math_id": "MATH-03"}, {"unit": "bad unit"}, {"basis": ""}):
        work = _lp03_numeric_work(limits)
        with pytest.raises(ContractValidationError):
            conversion(1, work, **metadata)
        assert work.state == "FAILED" and work.consumed["serialized_bytes"] == 0

    # Every call shares its original cumulative serialization allowance.
    work = _lp03_numeric_work(dict(limits, max_serialized_bytes=2048))
    successful = 0
    for _ in range(16):
        before = dict(work.consumed)
        try:
            conversion(1, work)
        except ContractValidationError as error:
            assert "SERIALIZATION_EXHAUSTED" in str(error)
            assert work.consumed["serialized_bytes"] == before["serialized_bytes"]
            assert work.consumed["integer_operations"] > before["integer_operations"]
            break
        successful += 1
    assert successful > 0 and work.state == "FAILED" and work.consumed["serialized_bytes"] > 0
    with pytest.raises(TypeError):
        work.consumed["serialized_bytes"] = 0
    with pytest.raises(AttributeError):
        work.consumed = dict(work.consumed)
    with pytest.raises(AttributeError):
        work.limits = dict(limits)
    original = _lp03_numeric_work(limits)
    original._consumed = dict(original.consumed)
    with pytest.raises(ContractValidationError, match="ORIGINAL_WORK_MEMBERS_REQUIRED"):
        conversion(1, original)
    assert original.state == "FAILED"


def _assert_lp03_math26_decimal_admission() -> None:
    """Separate original financial/statistical admissions share one work cap."""
    import json
    from decimal import Context, ROUND_DOWN, localcontext
    from fractions import Fraction
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import ContractValidationError
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.parameter_policy import (
        _EvidenceNumericalWorkV1, certify_evidence_binary64_v1, certify_evidence_conditional_mean_v1,
    )
    limits = dict(max_input_bits=4096, max_work_bits=65536, max_serialized_bytes=65536)
    positives, denials = [], []
    for text, expected in (("-0", Fraction(0)), ("-0.00", Fraction(0)), ("-0E+3", Fraction(0)),
                           ("1.2300", Fraction(123, 100)), ("1E+3", Fraction(1000)), ("-2.25", Fraction(-9, 4))):
        work = _EvidenceNumericalWorkV1(limits, retained_input_capacity=2)
        original = work._parse_math26_decimal_v1(text)
        assert str(original) == text and original.as_tuple() == Decimal(text).as_tuple()
        assert work._exact_math26_decimal_v1(original) == expected
        entry = work._decimal_inputs[id(original)]
        assert entry[0] is original and entry[1] == expected and entry[2:] == (text, "MATH26_FINANCIAL_DECIMAL_V1")
        assert work._decimal_admissions == (entry,) and work.consumed["retained_decimal_inputs"] == 1
        positives.append(dict(text=text, ratio=[str(expected.numerator), str(expected.denominator)],
            decimal_tuple=[original.as_tuple().sign, list(original.as_tuple().digits), original.as_tuple().exponent],
            admission_profile=entry[3], consumed=dict(work.consumed)))
        # The ordinary public conversion must reject even numerically ordinary
        # financial values; no untagged Decimal can cross the profile boundary.
        with pytest.raises(ContractValidationError, match="LP03_NUMERICAL_DECIMAL_PROFILE_MISMATCH"):
            certify_evidence_binary64_v1(original, math_id="MATH-29", unit="USD", basis="ORIGINAL_WEIGHTS", work=work)
        assert work.state == "FAILED" and work.consumed["serialized_bytes"] == 0
        retained = dict(work.consumed)
        with pytest.raises(ContractValidationError, match="LP03_NUMERICAL_WORK_NOT_OPEN"):
            work._parse_math26_decimal_v1("0")
        assert dict(work.consumed) == retained
        denials.append("financial_to_statistical_conversion::" + text)
    for text in ("-0", "-0.00", "-0E+3"):
        work = _EvidenceNumericalWorkV1(limits, retained_input_capacity=2)
        with pytest.raises(ContractValidationError, match="LP03_NUMERICAL_EXACT_INPUT_DOMAIN"):
            work.parse_decimal_v1(text)
        assert work.state == "FAILED" and work.consumed["decimal_constructions"] == work.consumed["retained_decimal_inputs"] == 0
        denials.append("statistical_signed_zero::" + text)
        work = _EvidenceNumericalWorkV1(limits, retained_input_capacity=2)
        value = work._parse_math26_decimal_v1(text)
        with pytest.raises(ContractValidationError, match="LP03_NUMERICAL_DECIMAL_PROFILE_MISMATCH"):
            certify_evidence_conditional_mean_v1((value,), lower=0, upper=1, alpha=Fraction(1, 20), claim_ordinal=1, work=work)
        assert work.state == "FAILED" and work.consumed["log_series_terms"] == 0
        denials.append("financial_to_conditional_mean::" + text)
    for text in ("0", "1.2300"):
        work = _EvidenceNumericalWorkV1(limits, retained_input_capacity=2)
        value = work.parse_decimal_v1(text)
        assert work._decimal_inputs[id(value)][3] == "STATISTICAL_EXACT_DECIMAL_V1"
        with pytest.raises(ContractValidationError, match="LP03_NUMERICAL_DECIMAL_PROFILE_MISMATCH"):
            work._exact_math26_decimal_v1(value)
        assert work.state == "FAILED"
        denials.append("statistical_to_financial::" + text)
    capacity = []
    for financial_first in (False, True):
        work = _EvidenceNumericalWorkV1(limits, retained_input_capacity=2)
        parsers = (work._parse_math26_decimal_v1, work.parse_decimal_v1) if financial_first else (
            work.parse_decimal_v1, work._parse_math26_decimal_v1)
        first, second = parsers[0]("1.00"), parsers[1]("0.00")
        assert first is not second and len(work._decimal_admissions) == 2
        statistical, financial = (second, first) if financial_first else (first, second)
        assert work._exact(statistical) == Fraction(0 if financial_first else 1)
        assert work._exact_math26_decimal_v1(financial) == Fraction(1 if financial_first else 0)
        before = dict(work.consumed)
        with pytest.raises(ContractValidationError, match="LP03_NUMERICAL_RETAINED_INPUT_CAPACITY_EXHAUSTED"):
            parsers[0]("0.25")
        assert work.state == "FAILED" and work.consumed["retained_decimal_inputs"] == work.consumed["decimal_constructions"] == 2
        assert work.consumed["decimal_parse_attempts"] == 3 and work.consumed["integer_operations"] == before["integer_operations"]
        assert work._decimal_inputs[id(first)][0] is first and work._decimal_inputs[id(second)][0] is second
        capacity.append(dict(financial_first=financial_first, before=before, after=dict(work.consumed)))
    for text in ("+1", "01", "1e+3"):
        work = _EvidenceNumericalWorkV1(limits, retained_input_capacity=1)
        with pytest.raises(ContractValidationError, match="LP03_MATH26_NUMERICAL_DECIMAL_CANONICAL"):
            work._parse_math26_decimal_v1(text)
        assert work.state == "FAILED" and work.consumed["decimal_constructions"] == 1 and work.consumed["retained_decimal_inputs"] == 0
        denials.append("financial_noncanonical::" + text)
    hostile_context_cases = []
    for text in ("1E+3", "-0E+3", "1e+3", "-0e+3"):
        work = _EvidenceNumericalWorkV1(limits, retained_input_capacity=1)
        with localcontext(Context(prec=2, rounding=ROUND_DOWN, Emin=-9, Emax=9, capitals=0)) as ambient:
            before = (ambient.prec, ambient.rounding, ambient.Emin, ambient.Emax, ambient.capitals,
                      tuple(ambient.traps.items()), tuple(ambient.flags.items()))
            if "E" in text:
                value = work._parse_math26_decimal_v1(text)
                assert str(value) == text.replace("E", "e")
                assert work._decimal_inputs[id(value)][2:] == (text, "MATH26_FINANCIAL_DECIMAL_V1")
                assert work._exact_math26_decimal_v1(value) == Fraction(0 if text.startswith("-") else 1000)
                assert work.state == "OPEN"
            else:
                with pytest.raises(ContractValidationError, match="LP03_MATH26_NUMERICAL_DECIMAL_CANONICAL"):
                    work._parse_math26_decimal_v1(text)
                assert work.state == "FAILED" and work.consumed["retained_decimal_inputs"] == 0
            assert before == (ambient.prec, ambient.rounding, ambient.Emin, ambient.Emax, ambient.capitals,
                              tuple(ambient.traps.items()), tuple(ambient.flags.items()))
        hostile_context_cases.append(dict(text=text, state=work.state, consumed=dict(work.consumed), ambient_unchanged=True))
    for financial in (False, True):
        work = _EvidenceNumericalWorkV1(limits, retained_input_capacity=1)
        value = (work._parse_math26_decimal_v1 if financial else work.parse_decimal_v1)("0.00")
        entry = work._decimal_inputs[id(value)]
        replacement = (*entry[:3], "STATISTICAL_EXACT_DECIMAL_V1" if financial else "MATH26_FINANCIAL_DECIMAL_V1")
        assert len(replacement) == 4 and replacement[:3] == entry[:3]
        work._decimal_inputs[id(value)] = replacement
        before = dict(work.consumed)
        with pytest.raises(ContractValidationError, match="LP03_ORIGINAL_DECIMAL_ADMISSION_ROSTER_REQUIRED"):
            (work._parse_math26_decimal_v1 if financial else work.parse_decimal_v1)("1")
        assert work.state == "FAILED" and work._decimal_admissions == (entry,) and work._decimal_admissions[0] is entry
        assert dict(work.consumed) == before
        denials.append("original_profile_tag_replacement::" + str(financial))
    work = _EvidenceNumericalWorkV1(limits, retained_input_capacity=1)
    with pytest.raises(ContractValidationError, match="LP03_NUMERICAL_WORK_BITS_EXHAUSTED"):
        work._parse_math26_decimal_v1("-0E+1000000")
    assert work.state == "FAILED" and work.consumed["decimal_constructions"] == 0
    denials.append("financial_exponent_preflight")
    print("LP03_MATH26_NUMERICAL_ADMISSION_QUALIFICATION=" + json.dumps(dict(
        profile="BOUNDED_FINANCIAL_DATA_ADMISSION_ONLY", positives=positives, denials=denials,
        shared_capacity=capacity, hostile_context_cases=hostile_context_cases,
        exponent_failure_consumption=dict(work.consumed), limits=limits,
        original_source_or_runtime_authority=False), sort_keys=True))


def _assert_lp03_math26_ordered_context_proof() -> None:
    """Independent literals and actual context steps; no M26 lane authority."""
    from decimal import Context, ROUND_DOWN, localcontext
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import ContractValidationError
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.parameter_policy import (
        _EvidenceNumericalWorkV1, _bounded_evidence_math26_review_v1,
    )
    limits = dict(max_input_bits=4096, max_work_bits=65536, max_serialized_bytes=65536)
    base = dict(current_texts=("1", "2"), scenario_texts=(("0.5", ("4", "1")), ("0.5", ("1", "5"))),
        cost_text="0.25", lower_text="0", upper_text="5", cost_cap_text="0.25",
        raw_text="2.25", projected_text="2.25", expected_text="2.25")
    def capacity(case):
        return len(case["current_texts"]) + len(case["scenario_texts"]) * (len(case["current_texts"]) + 4) + 6
    def run(case, selected_limits=limits, retained_capacity=None):
        work = _EvidenceNumericalWorkV1(selected_limits,
            retained_input_capacity=capacity(case) if retained_capacity is None else retained_capacity)
        return work, _bounded_evidence_math26_review_v1(**case, work=work)
    def ratio(value, numerator, denominator="1"):
        assert value == dict(numerator=str(numerator), denominator=str(denominator))
    def failed_retry(work, case):
        assert work.state == "FAILED"
        consumed, steps = dict(work.consumed), tuple(work._math26_context_steps)
        with pytest.raises(ContractValidationError, match="LP03_NUMERICAL_WORK_NOT_OPEN"):
            _bounded_evidence_math26_review_v1(**case, work=work)
        assert dict(work.consumed) == consumed and tuple(work._math26_context_steps) == steps
    positives, denials = [], []
    work, proof = run(base)
    assert len(work._math26_context_steps) == len(work._math26_context_prefix) == 8
    assert work.consumed["retained_decimal_inputs"] == 20 and work.consumed["decimal_constructions"] == 22
    assert work.consumed["decimal_parse_attempts"] == work.consumed["input_values"] == 12
    assert [step["decimal_text"] for step in proof["steps"]] == ["0.5", "2.0", "2.0", "1.0", "2.5", "4.5", "2.5", "2.25"]
    assert all(step["flags"] == "" for step in proof["steps"])
    assert proof["scenario_max_positions"] == (0, 1) and proof["summary"]["current_max_position"] == 1
    ratio(proof["summary"]["result"], 9, 4)
    ratio(proof["summary"]["lower"], -21, 4)
    ratio(proof["summary"]["upper"], 5)
    assert all(work._math26_context_steps[index] is original for index, original in enumerate(work._math26_context_prefix))
    assert all(work._decimal_inputs[id(step[5])][0] is step[5]
               and work._decimal_inputs[id(step[5])][3] == "MATH26_CONTEXT_RESULT_V1" for step in work._math26_context_steps)
    positives.append(dict(case="original_literal", proof=proof, consumed=dict(work.consumed)))
    complete_bytes = work.consumed["serialized_bytes"]

    tiny = dict(base, current_texts=("0.1",), scenario_texts=(("0.1", ("0.2",)), ("0.9", ("0.2",))),
        cost_text="0", lower_text="0", upper_text="1", cost_cap_text="0",
        raw_text="0.10", projected_text="0.10", expected_text="0.10")
    work, proof = run(tiny, dict(limits, max_input_bits=4))
    ratio(proof["steps"][1]["exact"], 1, 50)
    ratio(proof["summary"]["result"], 1, 10)
    assert work._math26_context_steps[1][5].as_tuple() == Decimal("0.02").as_tuple()
    positives.append(dict(case="derived_denominator_exceeds_source_bits", proof=proof, consumed=dict(work.consumed)))

    signed = dict(base, current_texts=("-0.00", "0.0"), scenario_texts=(("1", ("-0.000", "0")),),
        cost_text="0.0000", lower_text="-0", upper_text="0", cost_cap_text="0",
        raw_text="0.0000", projected_text="0.0000", expected_text="0.0000")
    work, proof = run(signed)
    assert proof["scenario_max_positions"] == (0,) and proof["summary"]["current_max_position"] == 0
    assert [step["decimal_text"] for step in proof["steps"]] == ["1", "-0.000", "0.000", "0.000", "0.0000"]
    assert work._math26_context_steps[1][3] is work._decimal_admissions[3][0]
    assert work._math26_context_steps[3][3] is work._decimal_admissions[0][0]
    assert work._math26_context_steps[0][2].as_tuple() == Decimal("0").as_tuple()
    positives.append(dict(case="first_equal_signed_zero_and_scale", proof=proof, consumed=dict(work.consumed)))

    negative = dict(base, current_texts=("5",), scenario_texts=(("1", ("1",)),),
        raw_text="-4.25", projected_text="-4.25", expected_text="-4.25")
    work, proof = run(negative)
    ratio(proof["summary"]["result"], -17, 4)
    positives.append(dict(case="negative_value_valid", proof=proof, consumed=dict(work.consumed)))

    rounded_text, exact_text = "1." + "0" * 34, "1." + "0" * 33
    rounded = dict(base, current_texts=("0",), scenario_texts=(("1", (rounded_text,)),),
        cost_text="0", lower_text="0", upper_text="2", cost_cap_text="0",
        raw_text=exact_text, projected_text=exact_text, expected_text=exact_text)
    work, proof = run(rounded)
    assert proof["steps"][1]["flags"] == "Rounded" and proof["steps"][1]["decimal_text"] == exact_text
    ratio(proof["summary"]["result"], 1)
    positives.append(dict(case="exact_rounded_trailing_zero", proof=proof, consumed=dict(work.consumed)))

    shared = _EvidenceNumericalWorkV1(limits, retained_input_capacity=2 * capacity(base))
    first = _bounded_evidence_math26_review_v1(**base, work=shared)
    originals, first_consumed = shared._math26_context_prefix, dict(shared.consumed)
    second = _bounded_evidence_math26_review_v1(**base, work=shared)
    assert len(shared._decimal_admissions) == 40 and len(shared._math26_context_prefix) == 16
    assert all(shared._math26_context_steps[index] is value for index, value in enumerate(originals))
    assert first["summary"] == second["summary"]
    assert [step["position"] for step in second["steps"]] == list(range(8, 16))
    positives.append(dict(case="two_proofs_share_original_work", first_consumed=first_consumed,
        consumed=dict(shared.consumed), second_positions=[step["position"] for step in second["steps"]]))
    with localcontext(Context(prec=2, rounding=ROUND_DOWN, Emin=-9, Emax=9, capitals=0)) as ambient:
        before = (ambient.prec, ambient.rounding, ambient.Emin, ambient.Emax, ambient.capitals,
                  tuple(ambient.traps.items()), tuple(ambient.flags.items()))
        work, proof = run(base)
        assert before == (ambient.prec, ambient.rounding, ambient.Emin, ambient.Emax, ambient.capitals,
                          tuple(ambient.traps.items()), tuple(ambient.flags.items()))
        ratio(proof["summary"]["result"], 9, 4)
    positives.append(dict(case="hostile_ambient_unchanged", consumed=dict(work.consumed)))

    mutations = (
        ("utility_order", dict(base, lower_text="6"), "DECLARED_BOUND_OR_COST"),
        ("negative_cost", dict(base, cost_text="-0.25"), "DECLARED_BOUND_OR_COST"),
        ("cost_cap", dict(base, cost_cap_text="0"), "DECLARED_BOUND_OR_COST"),
        ("utility_lower", dict(base, lower_text="2"), "UTILITY_OUT_OF_BOUNDS"),
        ("utility_upper", dict(base, upper_text="4"), "UTILITY_OUT_OF_BOUNDS"),
        ("negative_probability", dict(base, scenario_texts=(("-0.5", ("4", "1")),)), "PROBABILITY_DOMAIN"),
        ("large_probability", dict(base, scenario_texts=(("1.5", ("4", "1")),)), "PROBABILITY_DOMAIN"),
        ("incomplete_probability_sum", dict(base, scenario_texts=(("0.5", ("4", "1")),)), "PROBABILITY_SUM"),
        ("raw_scale", dict(base, raw_text="2.250"), "ORIGINAL_RESULT_TEXT_MISMATCH"),
        ("projection_scale", dict(base, projected_text="2.250"), "ORIGINAL_RESULT_TEXT_MISMATCH"),
        ("expected_scale", dict(base, expected_text="2.250"), "ORIGINAL_RESULT_TEXT_MISMATCH"),
        ("scenario_length", dict(base, scenario_texts=(("1", ("4",)),)), "COMPLETE_ORDERED_ROSTER"),
        ("inexact_probability_prefix", dict(rounded, scenario_texts=(("0." + "9" * 35, ("1",)),)), "NONEXACT_CONTEXT_STEP"),
        ("inexact_weighted_max", dict(rounded, scenario_texts=(("1", ("1." + "0" * 33 + "1",)),)), "NONEXACT_CONTEXT_STEP"),
    )
    for name, case, diagnostic in mutations:
        work = _EvidenceNumericalWorkV1(limits, retained_input_capacity=64)
        with pytest.raises(ContractValidationError, match=diagnostic):
            _bounded_evidence_math26_review_v1(**case, work=work)
        failed_retry(work, case)
        flags = ()
        if name.startswith("inexact_"):
            attempt = work._math26_context_steps[-1]
            assert type(attempt) is list and type(attempt[5]) is Decimal
            assert attempt[6] == ("Inexact", "Rounded") and attempt[8] == "ATTEMPTED"
            assert id(attempt[5]) not in work._decimal_inputs
            assert len(work._math26_context_prefix) + 1 == len(work._math26_context_steps)
            flags = attempt[6]
        denials.append(dict(case=name, flags=flags, consumed=dict(work.consumed), steps=len(work._math26_context_steps)))
    for name, selected_limits, selected_capacity, diagnostic in (
        ("capacity_before_any_parse", limits, capacity(base) - 1, "RETAINED_INPUT_CAPACITY_EXHAUSTED"),
        ("source_bits", dict(limits, max_input_bits=2), capacity(base), "INPUT_BITS_EXHAUSTED"),
        ("work_bits", dict(limits, max_work_bits=8), capacity(base), "WORK_BITS_EXHAUSTED"),
        ("step_serialization_preflight", dict(limits, max_serialized_bytes=500), capacity(base), "SERIALIZATION_EXHAUSTED"),
        ("complete_proof_serialization", dict(limits, max_serialized_bytes=complete_bytes - 1), capacity(base), "PROJECTION_JSON_BYTES"),
    ):
        work = _EvidenceNumericalWorkV1(selected_limits, retained_input_capacity=selected_capacity)
        with pytest.raises(ContractValidationError, match=diagnostic):
            _bounded_evidence_math26_review_v1(**base, work=work)
        failed_retry(work, base)
        if name == "capacity_before_any_parse":
            assert work.consumed["decimal_parse_attempts"] == work.consumed["decimal_constructions"] == 0
        if name == "complete_proof_serialization":
            assert len(work._math26_context_prefix) == len(work._math26_context_steps) == 8
            assert work.consumed["retained_decimal_inputs"] == 20
        denials.append(dict(case=name, consumed=dict(work.consumed), steps=len(work._math26_context_steps)))

    for accessor in ("statistical", "financial"):
        work, _ = run(base)
        value = work._math26_context_steps[0][5]
        with pytest.raises(ContractValidationError, match="DECIMAL_PROFILE_MISMATCH"):
            (work._exact if accessor == "statistical" else work._exact_math26_decimal_v1)(value)
        failed_retry(work, base)
        denials.append(dict(case="derived_result_to_" + accessor))
    work = _EvidenceNumericalWorkV1(limits, retained_input_capacity=1)
    with pytest.raises(ContractValidationError, match="NUMERICAL_DECIMAL_PROFILE"):
        work._parse_decimal_text_v1("1", "MATH26_CONTEXT_RESULT_V1")
    assert work.consumed["decimal_parse_attempts"] == work.consumed["decimal_constructions"] == 0
    denials.append(dict(case="source_parser_cannot_mint_context_tag"))
    for name in ("equal_step_replacement", "omitted_step", "reordered_steps", "cleared_both_step_mirrors", "hostile_ordinal"):
        work, _ = run(base, retained_capacity=2 * capacity(base))
        original = work._math26_context_prefix
        equality_calls = []
        if name == "equal_step_replacement":
            work._math26_context_steps[0] = tuple(list(original[0]))
            assert work._math26_context_steps[0] == original[0] and work._math26_context_steps[0] is not original[0]
        elif name == "omitted_step":
            work._math26_context_steps.pop()
        elif name == "reordered_steps":
            work._math26_context_steps[0], work._math26_context_steps[1] = work._math26_context_steps[1], work._math26_context_steps[0]
        elif name == "cleared_both_step_mirrors":
            work._math26_context_steps.clear()
            work._math26_context_prefix = ()
        else:
            class HostileOrdinal:
                def __eq__(self, other):
                    equality_calls.append(other)
                    return True
            replacement = (HostileOrdinal(), *original[0][1:])
            work._math26_context_steps[0] = replacement
            work._math26_context_prefix = (replacement, *original[1:])
        retained_prefix = work._math26_context_prefix
        before = dict(work.consumed)
        with pytest.raises(ContractValidationError, match="ORIGINAL_CONTEXT_PREFIX_REQUIRED"):
            _bounded_evidence_math26_review_v1(**base, work=work)
        assert dict(work.consumed) == before and work._math26_context_prefix is retained_prefix and not equality_calls
        assert all(work._decimal_inputs[id(record[5])][0] is record[5] for record in original)
        failed_retry(work, base)
        denials.append(dict(case=name))
    large_current = ("0",) * 4096
    large_case = dict(base, current_texts=large_current, scenario_texts=(("1", large_current),) * 4096)
    work = _EvidenceNumericalWorkV1(limits, retained_input_capacity=capacity(large_case))
    with pytest.raises(ContractValidationError, match="LP03_MATH26_REVIEW_COMPLETE_PROOF_ROSTER_BOUND"):
        _bounded_evidence_math26_review_v1(**large_case, work=work)
    assert work.consumed["decimal_parse_attempts"] == work.consumed["decimal_constructions"] == 0
    assert not work._math26_context_steps and not work._decimal_admissions
    failed_retry(work, large_case)
    denials.append(dict(case="cartesian_roster_before_expansion", consumed=dict(work.consumed)))
    work, _ = run(base)
    tag_equality_calls = []
    class HostileTag:
        def __eq__(self, other):
            tag_equality_calls.append(other)
            return True
    original = work._decimal_admissions[-1]
    replacement = (*original[:3], HostileTag())
    work._decimal_admissions = (*work._decimal_admissions[:-1], replacement)
    work._decimal_inputs[id(original[0])] = replacement
    with pytest.raises(ContractValidationError, match="LP03_ORIGINAL_DECIMAL_ADMISSION_ROSTER_REQUIRED"):
        work._assert_math26_context_custody_v1()
    assert not tag_equality_calls
    failed_retry(work, base)
    denials.append(dict(case="context_custody_rejects_hostile_admission_tag_first"))
    work = _EvidenceNumericalWorkV1(limits, retained_input_capacity=capacity(base))
    with pytest.MonkeyPatch.context() as patch:
        def encoding_failure(self, values):
            raise MemoryError("injected after actual Decimal operation and admission")
        patch.setattr(_EvidenceNumericalWorkV1, "_emit", encoding_failure)
        with pytest.raises(ContractValidationError, match="LP03_NUMERICAL_OPERATION_FAILED"):
            _bounded_evidence_math26_review_v1(**base, work=work)
    attempt = work._math26_context_steps[0]
    assert len(work._math26_context_prefix) == 0 and attempt[5].as_tuple() == Decimal("0.5").as_tuple()
    assert attempt[6] == () and attempt[7:] == ["0.5", "ATTEMPTED"]
    assert work._decimal_inputs[id(attempt[5])][0] is attempt[5] and work.consumed["serialized_bytes"] == 0
    failed_retry(work, base)
    denials.append(dict(case="encoding_failure_retains_actual_step", consumed=dict(work.consumed)))
    print("LP03_MATH26_ORDERED_CONTEXT_QUALIFICATION=" + json.dumps(dict(
        profile="PURE_INDEPENDENT_ORDERED_DECIMAL_PROOF_ONLY", positives=positives, denials=denials,
        original_source_or_runtime_authority=False), sort_keys=True))


def _assert_lp03_math26_declared_bounds() -> None:
    """Declared enclosures and original failed work, without evaluating EVI."""
    from decimal import Context, ROUND_DOWN, localcontext
    from types import MappingProxyType
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane import economic_math
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import ContractValidationError
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.parameter_policy import (
        _EvidenceNumericalWorkV1, _validate_evidence_math26_bounds_v1,
    )
    limits = dict(max_input_bits=4096, max_work_bits=65536, max_serialized_bytes=65536)
    base = dict(current_texts=("1", "2"), scenario_texts=(("0.5", ("4", "1")), ("0.5", ("1", "5"))),
        cost_text="0.25", lower_text="0", upper_text="5", cost_cap_text="0.25",
        fixed_lower_text="-5.25", fixed_upper_text="5")
    original_texts = ("0", "5", "0.25", "-5.25", "5", "1", "2", "0.5", "4", "1", "0.5", "1", "5", "0.25")
    def ratio(numerator, denominator=1):
        return dict(numerator=str(numerator), denominator=str(denominator))
    expected = dict(profile="DECLARED_MATH26_UTILITY_AND_COST_ENCLOSURE_V1", action_count=2, scenario_count=2,
        probability_sum=ratio(1), declared_utility_lower=ratio(0), declared_utility_upper=ratio(5),
        declared_cost_cap=ratio(1, 4), fixed_lower=ratio(-21, 4), fixed_upper=ratio(5))
    expected_bytes = len(json.dumps(expected, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
                                   allow_nan=False).encode("utf-8"))
    positives, denials, formula_calls = [], [], []
    def forbidden_formula(*args, **kwargs):
        formula_calls.append((args, kwargs))
        raise AssertionError("bounds admission invoked the EVI formula")
    def pure(work):
        assert work._math26_context_steps == [] and work._math26_context_prefix == ()
        assert all(work.consumed[name] == 0 for name in ("log_series_terms", "square_roots", "random_draws"))
        assert all(entry[3] == "MATH26_FINANCIAL_DECIMAL_V1" for entry in work._decimal_admissions)
        assert formula_calls == []
    def retained(work):
        pure(work)
        return dict(state=work.state, failure=work.failure, consumed=dict(work.consumed),
            admitted_texts=[entry[2] for entry in work._decimal_admissions])
    def failed_retry(work, case):
        assert work.state == "FAILED"
        before, originals = dict(work.consumed), work._decimal_admissions
        with pytest.raises(ContractValidationError, match="LP03_NUMERICAL_WORK_NOT_OPEN"):
            _validate_evidence_math26_bounds_v1(**case, work=work)
        assert dict(work.consumed) == before and work._decimal_admissions is originals
        pure(work)
    def positive(name, case, expected_proof, count):
        work = _EvidenceNumericalWorkV1(limits, retained_input_capacity=count)
        proof = _validate_evidence_math26_bounds_v1(**case, work=work)
        assert type(proof) is MappingProxyType and proof == expected_proof
        assert all(type(proof[key]) is MappingProxyType for key in (
            "probability_sum", "declared_utility_lower", "declared_utility_upper", "declared_cost_cap", "fixed_lower", "fixed_upper"))
        assert work.state == "OPEN" and work.failure is None
        assert work.consumed["decimal_parse_attempts"] == work.consumed["decimal_constructions"] == count
        assert work.consumed["retained_decimal_inputs"] == work.consumed["input_values"] == count
        wire = json.dumps(expected_proof, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
        assert work.consumed["serialized_bytes"] == len(wire.encode("utf-8"))
        positives.append(dict(case=name, inputs=case, proof=proof, **retained(work)))
        return work
    def denied(name, case, diagnostic, attempts, admissions, *, constructions=None, selected_limits=limits, capacity=14):
        work = _EvidenceNumericalWorkV1(selected_limits, retained_input_capacity=capacity)
        with pytest.raises(ContractValidationError, match=diagnostic):
            _validate_evidence_math26_bounds_v1(**case, work=work)
        assert work.failure == diagnostic
        assert work.consumed["decimal_parse_attempts"] == attempts
        assert work.consumed["retained_decimal_inputs"] == admissions
        assert work.consumed["decimal_constructions"] == (admissions if constructions is None else constructions)
        assert len(work._decimal_admissions) == admissions and work.consumed["serialized_bytes"] == 0
        failed_retry(work, case)
        denials.append(dict(case=name, **retained(work)))
        return work
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(economic_math, "expected_value_of_information_v1", forbidden_formula)
        work = positive("original_literal_exact_capacity", base, expected, 14)
        assert tuple(entry[2] for entry in work._decimal_admissions) == original_texts
        base_consumed = dict(work.consumed)
        for cap in ("0", "2"):
            case = dict(base, current_texts=("2",), scenario_texts=(("1", ("2",)),), cost_text=cap,
                lower_text="2", upper_text="2", cost_cap_text=cap, fixed_lower_text="0" if cap == "0" else "-2",
                fixed_upper_text="0")
            proof = dict(expected, action_count=1, scenario_count=1, declared_utility_lower=ratio(2),
                declared_utility_upper=ratio(2), declared_cost_cap=ratio(int(cap)), fixed_lower=ratio(-int(cap)), fixed_upper=ratio(0))
            positive("degenerate_utility_cost_" + cap, case, proof, 9)
        signed = dict(base, current_texts=("-0.00", "0.0"), scenario_texts=(("-0", ("-0.0", "0")), ("1.00", ("0", "-0.00"))),
            cost_text="-0.000", lower_text="-0", upper_text="0", cost_cap_text="0", fixed_lower_text="-0", fixed_upper_text="0")
        positive("signed_zero_and_zero_probability", signed, dict(expected, declared_utility_upper=ratio(0),
            declared_cost_cap=ratio(0), fixed_lower=ratio(0), fixed_upper=ratio(0)), 14)
        negative = dict(base, current_texts=("-4", "-1"), scenario_texts=(("1", ("-2", "-3")),),
            cost_text="1", lower_text="-4", upper_text="-1", cost_cap_text="2", fixed_lower_text="-5", fixed_upper_text="3")
        positive("negative_utility", negative, dict(expected, scenario_count=1, declared_utility_lower=ratio(-4),
            declared_utility_upper=ratio(-1), declared_cost_cap=ratio(2), fixed_lower=ratio(-5), fixed_upper=ratio(3)), 11)
        with localcontext(Context(prec=2, rounding=ROUND_DOWN, Emin=-9, Emax=9, capitals=0)) as ambient:
            before = (ambient.prec, ambient.rounding, ambient.Emin, ambient.Emax, ambient.capitals,
                      tuple(ambient.traps.items()), tuple(ambient.flags.items()))
            hostile = positive("hostile_ambient_unchanged", base, expected, 14)
            assert dict(hostile.consumed) == base_consumed
            assert before == (ambient.prec, ambient.rounding, ambient.Emin, ambient.Emax, ambient.capitals,
                              tuple(ambient.traps.items()), tuple(ambient.flags.items()))
        malformed = (
            ("empty_actions", dict(base, current_texts=())),
            ("empty_scenarios", dict(base, scenario_texts=())),
            ("list_actions", dict(base, current_texts=["1", "2"])),
            ("list_scenarios", dict(base, scenario_texts=list(base["scenario_texts"]))),
            ("list_scenario_row", dict(base, scenario_texts=(["1", ("1", "2")],))),
            ("list_scenario_values", dict(base, scenario_texts=(("1", ["1", "2"]),))),
            ("ragged_scenario", dict(base, scenario_texts=(("1", ("1",)),))),
            ("extra_scenario_member", dict(base, scenario_texts=(("1", ("1", "2"), "extra"),))),
        )
        for name, case in malformed:
            denied(name, case, "LP03_MATH26_ADMISSION_COMPLETE_ORDERED_ROSTER", 0, 0)
        denied("cartesian_roster_before_parse", dict(base, current_texts=("0",) * 32,
            scenario_texts=(("1", ("0",) * 32),) * 128), "LP03_MATH26_ADMISSION_ROSTER_BOUND", 0, 0, capacity=10000)
        for cap in (0, 13):
            denied("capacity_before_parse_" + str(cap), base, "LP03_NUMERICAL_RETAINED_INPUT_CAPACITY_EXHAUSTED", 0, 0, capacity=cap)
        for name, changes, diagnostic, count in (
            ("reversed_declared_bounds", dict(lower_text="6"), "LP03_MATH26_ADMISSION_DECLARED_BOUND_OR_COST", 5),
            ("negative_cost_cap", dict(cost_cap_text="-0.25"), "LP03_MATH26_ADMISSION_DECLARED_BOUND_OR_COST", 5),
            ("wrong_fixed_lower", dict(fixed_lower_text="-5"), "LP03_MATH26_ADMISSION_DECLARED_ENCLOSURE_MISMATCH", 5),
            ("wrong_fixed_upper", dict(fixed_upper_text="5.25"), "LP03_MATH26_ADMISSION_DECLARED_ENCLOSURE_MISMATCH", 5),
            ("current_below_lower", dict(current_texts=("-1", "2")), "LP03_MATH26_ADMISSION_UTILITY_OUT_OF_BOUNDS", 6),
            ("current_above_upper", dict(current_texts=("1", "6")), "LP03_MATH26_ADMISSION_UTILITY_OUT_OF_BOUNDS", 7),
            ("scenario_above_upper", dict(scenario_texts=(("0.5", ("4", "6")), ("0.5", ("1", "5")))), "LP03_MATH26_ADMISSION_UTILITY_OUT_OF_BOUNDS", 10),
            ("zero_probability_still_bounded", dict(scenario_texts=(("0", ("-1", "1")), ("1", ("1", "5")))), "LP03_MATH26_ADMISSION_UTILITY_OUT_OF_BOUNDS", 9),
            ("negative_probability", dict(scenario_texts=(("-0.5", ("4", "1")), ("1.5", ("1", "5")))), "LP03_MATH26_ADMISSION_PROBABILITY_DOMAIN", 8),
            ("probability_above_one", dict(scenario_texts=(("1.5", ("4", "1")), ("-0.5", ("1", "5")))), "LP03_MATH26_ADMISSION_PROBABILITY_DOMAIN", 8),
            ("incomplete_probability_sum", dict(scenario_texts=(("0.4", ("4", "1")), ("0.5", ("1", "5")))), "LP03_MATH26_ADMISSION_PROBABILITY_SUM", 13),
            ("excess_probability_sum", dict(scenario_texts=(("0.6", ("4", "1")), ("0.5", ("1", "5")))), "LP03_MATH26_ADMISSION_PROBABILITY_SUM", 13),
            ("negative_actual_cost", dict(cost_text="-0.25"), "LP03_MATH26_ADMISSION_DECLARED_BOUND_OR_COST", 14),
            ("actual_cost_above_cap", dict(cost_text="0.26"), "LP03_MATH26_ADMISSION_DECLARED_BOUND_OR_COST", 14),
        ):
            failed = denied(name, dict(base, **changes), diagnostic, count, count)
            if count == 14:
                assert tuple(entry[2] for entry in failed._decimal_admissions) == (*original_texts[:-1], changes["cost_text"])
        for name, changes, attempts, admissions, constructions in (
            ("late_cost_nan", dict(cost_text="NaN"), 14, 13, 13),
            ("late_utility_nan", dict(scenario_texts=(("0.5", ("4", "1")), ("0.5", ("1", "NaN")))), 13, 12, 12),
            ("late_noncanonical_cost", dict(cost_text="00"), 14, 13, 14),
        ):
            diagnostic = "LP03_MATH26_NUMERICAL_DECIMAL_CANONICAL" if name == "late_noncanonical_cost" else "LP03_NUMERICAL_EXACT_INPUT_DOMAIN"
            failed = denied(name, dict(base, **changes), diagnostic, attempts, admissions, constructions=constructions)
            assert tuple(entry[2] for entry in failed._decimal_admissions) == original_texts[:admissions]
        for name, text in (("empty_original_cost", ""), ("nonnative_original_cost", Decimal("0.25")),
                           ("oversized_original_cost", "0" * 65537)):
            denied(name, dict(base, cost_text=text), "LP03_MATH26_ADMISSION_ORIGINAL_TEXTS", 13, 13)
        denied("external_fixed_bound_exceeds_input_bits", base, "LP03_NUMERICAL_INPUT_BITS_EXHAUSTED", 4, 3,
            selected_limits=dict(limits, max_input_bits=4))
        denied("work_bits_before_construction", base, "LP03_NUMERICAL_WORK_BITS_EXHAUSTED", 1, 0,
            selected_limits=dict(limits, max_work_bits=3))
        denied("serialization_preflight_retains_all_inputs", base, "LP03_NUMERICAL_SERIALIZATION_EXHAUSTED", 14, 14,
            selected_limits=dict(limits, max_serialized_bytes=512))
        shared = _EvidenceNumericalWorkV1(limits, retained_input_capacity=28)
        first = _validate_evidence_math26_bounds_v1(**base, work=shared)
        first_originals, first_consumed = shared._decimal_admissions, dict(shared.consumed)
        second = _validate_evidence_math26_bounds_v1(**base, work=shared)
        assert first == second == expected and first is not second
        assert all(first_originals[index] is shared._decimal_admissions[index] for index in range(14))
        assert dict(shared.consumed) == {key: value if key == "peak_preflight_bits" else 2 * value for key, value in base_consumed.items()}
        positives.append(dict(case="two_admissions_share_original_work", proof=second,
            first_consumed=first_consumed, **retained(shared)))
        before = dict(shared.consumed)
        with pytest.raises(ContractValidationError, match="LP03_NUMERICAL_RETAINED_INPUT_CAPACITY_EXHAUSTED"):
            _validate_evidence_math26_bounds_v1(**base, work=shared)
        assert dict(shared.consumed) == before
        failed_retry(shared, base)
        denials.append(dict(case="third_admission_cannot_reset_capacity", **retained(shared)))
        shared_bytes = _EvidenceNumericalWorkV1(dict(limits, max_serialized_bytes=1024), retained_input_capacity=28)
        assert _validate_evidence_math26_bounds_v1(**base, work=shared_bytes) == expected
        originals = shared_bytes._decimal_admissions
        with pytest.raises(ContractValidationError, match="LP03_NUMERICAL_SERIALIZATION_EXHAUSTED"):
            _validate_evidence_math26_bounds_v1(**base, work=shared_bytes)
        assert shared_bytes.consumed["retained_decimal_inputs"] == 28
        assert shared_bytes.consumed["serialized_bytes"] == expected_bytes
        assert all(originals[index] is shared_bytes._decimal_admissions[index] for index in range(14))
        failed_retry(shared_bytes, base)
        denials.append(dict(case="second_admission_cannot_reset_serialized_bytes", **retained(shared_bytes)))
    assert formula_calls == []
    print("LP03_MATH26_DECLARED_BOUNDS_QUALIFICATION=" + json.dumps(dict(
        profile="PURE_DECLARED_ENCLOSURE_ADMISSION_ONLY", positives=positives, denials=denials,
        original_source_or_runtime_authority=False, formula_calls=0, expected_serialized_bytes=expected_bytes),
        default=lambda value: dict(value) if isinstance(value, MappingProxyType) else value, sort_keys=True))


def _assert_lp03_market_ordered_context_proof():
    import json
    from decimal import Context, ROUND_DOWN, localcontext
    from unittest.mock import patch
    from types import MappingProxyType
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane import implementation_registry as formulas
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.parameter_policy import (
        _EvidenceNumericalWorkV1, _bounded_evidence_market_review_v1, _validate_evidence_market_bounds_v1,
        _bounded_evidence_math26_review_v1,
    )
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import ComputationControlPlaneError
    limits = dict(max_input_bits=4096, max_work_bits=65536, max_serialized_bytes=65536)
    cases = (
        ("MATH-01", (("contract_price", "0.40"), ("payout_per_winning_contract", "1.00")), "1", ("0.4",),
            ("0.4",), ((2, 5),)),
        ("MATH-04", (("best_bid", "0.40"), ("best_ask", "0.60"), ("payout", "1.00")), "1.00", ("0.20",),
            ("0.20",), ((1, 5),)),
        ("MATH-05", (("best_bid", "0.40"), ("best_ask", "0.60"), ("payout", "1.00")), "2", ("0.4", "4000.0"),
            ("1.00", "0.50", "0.20", "0.4", "4000.0"), ((1, 1), (1, 2), (1, 5), (2, 5), (4000, 1))),
    )
    rational = lambda n, d=1: dict(numerator=str(n), denominator=str(d))
    positives, denials, first_consumptions = [], [], {}
    def compute(case, work, **changes):
        math_id, sources, upper, raw, texts, ratios = case
        args = dict(lower_text="0", upper_text=upper, raw_texts=raw, expected_texts=raw, projected_text=raw[0], work=work)
        sources = changes.pop("source_texts", sources)
        args.update(changes)
        return _bounded_evidence_market_review_v1(math_id, sources, **args)
    def forbidden(*args, **kwargs):
        raise AssertionError("independent proof invoked the production formula")
    with patch.object(formulas, "compute_math_01_v34", forbidden), patch.object(formulas, "compute_math_03_v34", forbidden), patch.object(formulas, "compute_math_04_v34", forbidden), patch.object(formulas, "compute_math_05_v34", forbidden):
        for case in cases:
            math_id, sources, upper, raw, texts, ratios = case
            registered = _EvidenceNumericalWorkV1(limits, retained_input_capacity=len(sources)+2+len(raw))
            bound = _validate_evidence_market_bounds_v1(math_id, sources, lower_text="0", upper_text=upper, expected_texts=raw, work=registered)
            assert registered._math26_context_steps == [] and registered._math26_context_prefix == ()
            assert bound["declared_lower"] == rational(0)
            assert bound["declared_upper"] == rational(2 if math_id == "MATH-05" else 1)
            assert bound["original_payout"] == rational(1)
            assert registered.consumed["retained_decimal_inputs"] == len(sources)+2+len(raw)
            remaining = dict(limits, max_serialized_bytes=65536-registered.consumed["serialized_bytes"])
            work = _EvidenceNumericalWorkV1(remaining, retained_input_capacity=2*(len(sources)+2+len(texts)))
            first = compute(case, work)
            first_consumptions[math_id] = dict(work.consumed)
            second = compute(case, work)
            for index, proof in enumerate((first, second)):
                assert tuple(step["decimal_text"] for step in proof["steps"]) == texts
                assert tuple(step["exact"] for step in proof["steps"]) == tuple(rational(n,d) for n,d in ratios)
                assert tuple(step["position"] for step in proof["steps"]) == tuple(range(index*len(texts),(index+1)*len(texts)))
                assert all(step["flags"] == "" for step in proof["steps"])
                assert proof["original_raw_texts"] == proof["preregistered_raw_texts"] == raw
                assert proof["projected_text"] == raw[0]
            assert work.consumed["retained_decimal_inputs"] == 2*(len(sources)+2+len(texts))
            assert all(work.consumed[key] == 0 for key in ("random_draws", "log_series_terms", "square_roots"))
            assert all(entry[3] in ("MARKET_FINANCIAL_DECIMAL_V1", "MARKET_CONTEXT_RESULT_V1") for entry in work._decimal_admissions)
            positives.append(dict(math_id=math_id, registration_bound=bound, registration_consumed=dict(registered.consumed),
                review_limits=remaining, review_consumed=dict(work.consumed), proofs=(first,second)))
        boundaries = (
            ("MATH-01", (("contract_price","0"),("payout_per_winning_contract","1")), "1", ("0",)),
            ("MATH-01", (("contract_price","1"),("payout_per_winning_contract","1")), "1", ("1",)),
            ("MATH-04", (("best_bid","1"),("best_ask","1"),("payout","1")), "1", ("0",)),
            ("MATH-04", (("best_bid","0"),("best_ask","1"),("payout","1")), "1", ("1",)),
            ("MATH-05", (("best_bid","1"),("best_ask","1"),("payout","1")), "2", ("0","0")),
            ("MATH-05", (("best_bid","0"),("best_ask","1"),("payout","1")), "2", ("2","20000")),
        )
        for math_id, sources, upper, expected in boundaries:
            work = _EvidenceNumericalWorkV1(limits, retained_input_capacity=10)
            proof = _bounded_evidence_market_review_v1(math_id, sources, lower_text="0", upper_text=upper,
                raw_texts=expected, expected_texts=expected, projected_text=expected[0], work=work)
            assert proof["summary"]["result"] == rational(int(expected[0]))
            if math_id == "MATH-05":
                assert proof["summary"]["basis_points"] == rational(int(expected[1]))
            positives.append(dict(case="fixed_enclosure_endpoint", math_id=math_id, proof=proof, consumed=dict(work.consumed)))
        domain_cases = (
            ("zero_payout", "MATH-01", (("contract_price","0"),("payout_per_winning_contract","0")), "1", ("0",), "LP03_MARKET_ADMISSION_DECLARED_ENCLOSURE"),
            ("negative_price", "MATH-01", (("contract_price","-0.1"),("payout_per_winning_contract","1")), "1", ("0",), "LP03_MARKET_ADMISSION_PRICE_DOMAIN"),
            ("price_above_payout", "MATH-01", (("contract_price","2"),("payout_per_winning_contract","1")), "1", ("0",), "LP03_MARKET_ADMISSION_PRICE_DOMAIN"),
            ("crossed_registration", "MATH-04", (("best_bid","1"),("best_ask","0"),("payout","1")), "1", ("0",), "LP03_MARKET_ADMISSION_CROSSED_BOOK"),
            ("zero_midpoint", "MATH-05", (("best_bid","0"),("best_ask","0"),("payout","1")), "2", ("0","0"), "LP03_MARKET_ADMISSION_POSITIVE_MIDPOINT"),
        )
        for name, math_id, sources, upper, expected, reason in domain_cases:
            work = _EvidenceNumericalWorkV1(limits, retained_input_capacity=7)
            with pytest.raises(ComputationControlPlaneError, match=reason):
                _validate_evidence_market_bounds_v1(math_id, sources, lower_text="0", upper_text=upper, expected_texts=expected, work=work)
            assert work.state == "FAILED" and work._math26_context_steps == [] and work._math26_context_prefix == ()
            denials.append(dict(case=name, reason=work.failure, consumed=dict(work.consumed), formula_steps=0))
        hostile = Context(prec=2, rounding=ROUND_DOWN, capitals=0)
        with localcontext(hostile) as ambient:
            before = (ambient.prec, ambient.rounding, ambient.capitals, dict(ambient.flags), dict(ambient.traps))
            work = _EvidenceNumericalWorkV1(limits, retained_input_capacity=10)
            proof = compute(cases[2], work)
            assert tuple(step["decimal_text"] for step in proof["steps"]) == cases[2][4]
            assert (ambient.prec, ambient.rounding, ambient.capitals, dict(ambient.flags), dict(ambient.traps)) == before
        tiny = _EvidenceNumericalWorkV1(dict(limits, max_input_bits=4), retained_input_capacity=10)
        assert compute(cases[2], tiny)["summary"]["basis_points"] == rational(4000)
        assert tiny.consumed["peak_preflight_bits"] == 136
        negatives = (
            ("zero_budget", cases[0], dict(limits, max_work_bits=0), {}, "LP03_NUMERICAL_ZERO_BUDGET"),
            ("nonexact_division", cases[0], limits, dict(source_texts=(("contract_price","1"),("payout_per_winning_contract","3"))), "LP03_MARKET_REVIEW_NONEXACT_CONTEXT_STEP"),
            ("crossed_book", cases[1], limits, dict(source_texts=(("best_bid","0.60"),("best_ask","0.40"),("payout","1.00"))), "LP03_MARKET_REVIEW_CROSSED_BOOK"),
            ("wrong_bounds", cases[2], limits, dict(upper_text="1"), "LP03_MARKET_REVIEW_DECLARED_ENCLOSURE"),
            ("wrong_raw_scale", cases[0], limits, dict(raw_texts=("0.40",)), "LP03_MARKET_REVIEW_ORIGINAL_RESULT_TEXT_MISMATCH"),
            ("wrong_bps", cases[2], limits, dict(raw_texts=("0.4","4000")), "LP03_MARKET_REVIEW_ORIGINAL_RESULT_TEXT_MISMATCH"),
            ("wrong_expectation", cases[0], limits, dict(expected_texts=("0.5",)), "LP03_MARKET_REVIEW_ORIGINAL_RESULT_TEXT_MISMATCH"),
            ("wrong_projection", cases[2], limits, dict(projected_text="4000.0"), "LP03_MARKET_REVIEW_ORIGINAL_RESULT_TEXT_MISMATCH"),
            ("malformed_late_source", cases[1], limits, dict(source_texts=(("best_bid","0.40"),("best_ask","0.60"),("payout","NaN"))), "LP03_NUMERICAL_EXACT_INPUT_DOMAIN"),
            ("final_encoding", cases[2], dict(limits,max_serialized_bytes=first_consumptions["MATH-05"]["serialized_bytes"]-1), {}, "LP03_PROJECTION_JSON_BYTES"),
        )
        for name, case, budget, changes, reason in negatives:
            work = _EvidenceNumericalWorkV1(budget, retained_input_capacity=32)
            with pytest.raises(ComputationControlPlaneError, match=reason):
                compute(case, work, **changes)
            assert work.state == "FAILED"
            consumed = dict(work.consumed)
            with pytest.raises(ComputationControlPlaneError, match="LP03_NUMERICAL_WORK_NOT_OPEN"):
                compute(case, work)
            assert dict(work.consumed) == consumed
            if name == "nonexact_division":
                assert len(work._math26_context_steps) == 1 and work._math26_context_prefix == ()
                assert "Inexact" in work._math26_context_steps[0][6]
            if name == "final_encoding":
                assert len(work._math26_context_prefix) == 5 and consumed["retained_decimal_inputs"] == 10
            denials.append(dict(case=name, reason=reason, consumed=consumed,
                retained_steps=len(work._math26_context_steps), completed_steps=len(work._math26_context_prefix)))
        for name in ("M26_input_to_market", "market_input_to_M26", "market_result_to_M26_review"):
            work = _EvidenceNumericalWorkV1(limits, retained_input_capacity=64)
            if name == "M26_input_to_market":
                work._parse_math26_decimal_v1("1")
                refused = lambda: compute(cases[0], work)
            elif name == "market_input_to_M26":
                value = work._parse_market_decimal_v1("1")
                refused = lambda: work._exact_math26_decimal_v1(value)
            else:
                compute(cases[0], work)
                refused = lambda: _bounded_evidence_math26_review_v1(("1","2"),(("0.5",("4","1")),("0.5",("1","5"))),"0.25",
                    lower_text="0",upper_text="5",cost_cap_text="0.25",raw_text="2.25",projected_text="2.25",expected_text="2.25",work=work)
            with pytest.raises(ComputationControlPlaneError, match="LP03_NUMERICAL_DECIMAL_PROFILE_MISMATCH"):
                refused()
            denials.append(dict(case=name, reason=work.failure, consumed=dict(work.consumed)))
    print("LP03_MARKET_ORDERED_CONTEXT_QUALIFICATION=" + json.dumps(dict(
        scope="PURE_MARKET_DOMAINS_AND_ORDERED_CONTEXT_ONLY", positives=positives, denials=denials,
        hostile_ambient_unchanged=True, tiny_source_bits_derived_bps=dict(tiny.consumed), original_source_or_runtime_authority=False),
        default=lambda value: dict(value) if isinstance(value, MappingProxyType) else value, sort_keys=True))


def _assert_lp03_kelly_ordered_context_proof():
    import json
    from decimal import Context, ROUND_DOWN, localcontext
    from unittest.mock import patch
    from types import MappingProxyType
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane import economic_math as formulas
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.parameter_policy import (
        _EvidenceNumericalWorkV1, _bounded_evidence_kelly_review_v1, _validate_evidence_kelly_bounds_v1,
    )
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import ComputationControlPlaneError
    limits = dict(max_input_bits=4096, max_work_bits=65536, max_serialized_bytes=65536)
    rational = lambda n, d=1: dict(numerator=str(n), denominator=str(d))
    def full(p, odds):
        return (("win_probability",p),("net_odds",odds))
    def fractional(raw, multiplier, *caps):
        return (("full_kelly_fraction",raw),("fraction_multiplier",multiplier),("risk_caps",caps))
    # Values, operation order, ratios and first-tie indices are literal oracles.
    cases = (
        ("positive", "MATH-27", full("0.75","1"), "-1", ("0.50","0.50"),
            ("0.75","0.25","0.50","0.50"), ((3,4),(1,4),(1,2),(1,2)), (1,)),
        ("negative_raw_retained", "MATH-27", full("0.25","1"), "-1", ("-0.50","0"),
            ("0.25","0.75","-0.50","-0.50"), ((1,4),(3,4),(-1,2),(-1,2)), (0,)),
        ("zero_raw_first_constant", "MATH-27", full("0.5","1"), "-1", ("0.0","0"),
            ("0.5","0.5","0.0","0.0"), ((1,2),(1,2),(0,1),(0,1)), (0,)),
        ("lower_endpoint", "MATH-27", full("0","0.5"), "-2", ("-2","0"),
            ("0.0","1","-1.0","-2"), ((0,1),(1,1),(-1,1),(-2,1)), (0,)),
        ("upper_endpoint", "MATH-27", full("1","1"), "-1", ("1","1"),
            ("1","0","1","1"), ((1,1),(0,1),(1,1),(1,1)), (1,)),
        ("derived_exceeds_input_bits", "MATH-27", full("0.875","0.125"), "-8", ("-0.125","0"),
            ("0.109375","0.125","-0.015625","-0.125"), ((7,64),(1,8),(-1,64),(-1,8)), (0,)),
        ("cap_selected", "MATH-28", fractional("0.50","0.5","0.20","0.40"), "0", ("0.20",),
            ("0.250",), ((1,4),), (1,1)),
        ("candidate_wins_tie", "MATH-28", fractional("0.40","0.5","0.20","0.200"), "0", ("0.200",),
            ("0.200",), ((1,5),), (1,0)),
        ("first_cap_wins_tie", "MATH-28", fractional("0.5","1","0.20","0.200"), "0", ("0.20",),
            ("0.5",), ((1,2),), (1,1)),
        ("signed_zero_first_candidate", "MATH-28", fractional("-0.00","0.50","-0.0"), "0", ("0.00",),
            ("0.00",), ((0,1),), (0,0)),
        ("negative_upstream_raw", "MATH-28", fractional("-0.50","0.50","0.1"), "0", ("0.00",),
            ("0.00",), ((0,1),), (0,0)),
        ("signed_zero_cap_selected", "MATH-28", fractional("0.5","0.5","-0.00"), "0", ("-0.00",),
            ("0.25",), ((1,4),), (1,1)),
    )
    positives, denials, first_consumptions = [], [], {}
    def compute(case, work, **changes):
        name, math_id, sources, lower, raw, steps, ratios, selected = case
        args = dict(lower_text=lower, upper_text="1", raw_texts=raw, expected_texts=raw, projected_text=raw[0], work=work)
        sources = changes.pop("source_texts", sources)
        args.update(changes)
        return _bounded_evidence_kelly_review_v1(math_id, sources, **args)
    def forbidden(*args, **kwargs):
        raise AssertionError("independent Kelly proof invoked production sizing")
    with patch.object(formulas,"binary_kelly_fraction_v1",forbidden), patch.object(formulas,"fractional_kelly_v1",forbidden):
        for case in cases:
            name, math_id, sources, lower, raw, steps, ratios, selected = case
            count = 2 if math_id == "MATH-27" else 2+len(sources[2][1])
            registered = _EvidenceNumericalWorkV1(limits, retained_input_capacity=count+2+len(raw))
            bound = _validate_evidence_kelly_bounds_v1(math_id,sources,lower_text=lower,upper_text="1",expected_texts=raw,work=registered)
            assert registered._math26_context_steps == [] and registered._math26_context_prefix == ()
            assert bound["declared_upper"] == rational(1) and bound["declared_lower"] == rational(int(lower))
            remaining = dict(limits,max_serialized_bytes=65536-registered.consumed["serialized_bytes"])
            work = _EvidenceNumericalWorkV1(remaining,retained_input_capacity=2*(count+2+len(steps)))
            first = compute(case,work)
            first_consumptions[name] = dict(work.consumed)
            second = compute(case,work)
            for lane, proof in enumerate((first,second)):
                assert tuple(row["decimal_text"] for row in proof["steps"]) == steps
                assert tuple(row["exact"] for row in proof["steps"]) == tuple(rational(n,d) for n,d in ratios)
                assert tuple(row["position"] for row in proof["steps"]) == tuple(range(lane*len(steps),(lane+1)*len(steps)))
                assert tuple(row["selected_index"] for row in proof["selections"]) == selected
                assert proof["original_raw_texts"] == proof["preregistered_raw_texts"] == raw
                assert proof["projected_text"] == raw[0] and all(row["flags"] == "" for row in proof["steps"])
            assert work.consumed["retained_decimal_inputs"] == 2*(count+2+len(steps))
            assert all(work.consumed[key] == 0 for key in ("random_draws","log_series_terms","square_roots"))
            positives.append(dict(case=name,math_id=math_id,registration_bound=bound,registration_consumed=dict(registered.consumed),
                review_limits=remaining,review_consumed=dict(work.consumed),proofs=(first,second)))
        tiny = _EvidenceNumericalWorkV1(dict(limits,max_input_bits=4),retained_input_capacity=8)
        assert compute(cases[5],tiny)["summary"]["result"] == rational(-1,8)
        assert tiny.consumed["peak_preflight_bits"] == 136
        with localcontext(Context(prec=2,rounding=ROUND_DOWN,capitals=0)) as ambient:
            before = (ambient.prec,ambient.rounding,ambient.capitals,dict(ambient.flags),dict(ambient.traps))
            assert compute(cases[5],_EvidenceNumericalWorkV1(limits,retained_input_capacity=8))["projected_text"] == "-0.125"
            assert (ambient.prec,ambient.rounding,ambient.capitals,dict(ambient.flags),dict(ambient.traps)) == before
        domain_cases = (
            ("probability_low","MATH-27",full("-0.1","1"),"-1","1",("0","0"),"LP03_KELLY_PROBABILITY_DOMAIN"),
            ("probability_high","MATH-27",full("1.1","1"),"-1","1",("0","0"),"LP03_KELLY_PROBABILITY_DOMAIN"),
            ("zero_odds","MATH-27",full("0.5","0"),"-1","1",("0","0"),"LP03_KELLY_ODDS_DOMAIN"),
            ("negative_odds","MATH-27",full("0.5","-1"),"-1","1",("0","0"),"LP03_KELLY_ODDS_DOMAIN"),
            ("lower_not_enclosing","MATH-27",full("0.5","0.5"),"-1","1",("0","0"),"LP03_KELLY_DECLARED_ENCLOSURE"),
            ("wrong_upper","MATH-27",full("0.5","1"),"-1","2",("0","0"),"LP03_KELLY_DECLARED_ENCLOSURE"),
            ("raw_expectation_outside","MATH-27",full("0.5","1"),"-1","1",("-2","0"),"LP03_KELLY_EXPECTATION_OUT_OF_BOUNDS"),
            ("negative_sizing_expectation","MATH-27",full("0.5","1"),"-1","1",("0","-0.1"),"LP03_KELLY_SIZING_EXPECTATION_DOMAIN"),
            ("empty_caps","MATH-28",fractional("0.5","1"),"0","1",("0",),"LP03_KELLY_ORIGINAL_CAP_ROSTER"),
            ("negative_cap","MATH-28",fractional("0.5","1","-0.1"),"0","1",("0",),"LP03_KELLY_CAP_DOMAIN"),
            ("upstream_above_one","MATH-28",fractional("1.1","1","1"),"0","1",("0",),"LP03_KELLY_UPSTREAM_RAW_DOMAIN"),
            ("zero_multiplier","MATH-28",fractional("0.5","0","1"),"0","1",("0",),"LP03_KELLY_MULTIPLIER_DOMAIN"),
            ("high_multiplier","MATH-28",fractional("0.5","1.1","1"),"0","1",("0",),"LP03_KELLY_MULTIPLIER_DOMAIN"),
        )
        for name, math_id, sources, lower, upper, expected, reason in domain_cases:
            work = _EvidenceNumericalWorkV1(limits,retained_input_capacity=16)
            with pytest.raises(ComputationControlPlaneError,match=reason):
                _validate_evidence_kelly_bounds_v1(math_id,sources,lower_text=lower,upper_text=upper,expected_texts=expected,work=work)
            assert work.state == "FAILED" and work._math26_context_steps == []
            denials.append(dict(case=name,reason=work.failure,consumed=dict(work.consumed),formula_steps=0))
        negatives = (
            ("zero_work",cases[0],dict(limits,max_work_bits=0),{},"LP03_NUMERICAL_ZERO_BUDGET"),
            ("nonexact_final_division",cases[0],limits,dict(source_texts=full("0.5","3")),"LP03_KELLY_NONEXACT_CONTEXT_STEP"),
            ("lost_raw_fraction",cases[1],limits,dict(raw_texts=("0","0")),"LP03_KELLY_ORIGINAL_RESULT_TEXT_MISMATCH"),
            ("zero_scale_changed",cases[2],limits,dict(raw_texts=("0.0","0.0")),"LP03_KELLY_ORIGINAL_RESULT_TEXT_MISMATCH"),
            ("cap_tie_scale_changed",cases[8],limits,dict(raw_texts=("0.200",)),"LP03_KELLY_ORIGINAL_RESULT_TEXT_MISMATCH"),
            ("wrong_expectation",cases[0],limits,dict(expected_texts=("0.5","0.5")),"LP03_KELLY_ORIGINAL_RESULT_TEXT_MISMATCH"),
            ("clipped_projection",cases[1],limits,dict(projected_text="0"),"LP03_KELLY_ORIGINAL_RESULT_TEXT_MISMATCH"),
            ("late_bad_cap",cases[6],limits,dict(source_texts=fractional("0.50","0.5","0.20","NaN")),"LP03_NUMERICAL_EXACT_INPUT_DOMAIN"),
            ("original_input_bit_limit",cases[0],dict(limits,max_input_bits=1),{},"LP03_NUMERICAL_INPUT_BITS_EXHAUSTED"),
            ("final_encoding",cases[0],dict(limits,max_serialized_bytes=first_consumptions["positive"]["serialized_bytes"]-1),{},"LP03_PROJECTION_JSON_BYTES"),
        )
        for name, case, budget, changes, reason in negatives:
            work = _EvidenceNumericalWorkV1(budget,retained_input_capacity=32)
            with pytest.raises(ComputationControlPlaneError,match=reason):
                compute(case,work,**changes)
            assert work.state == "FAILED"
            consumed = dict(work.consumed)
            with pytest.raises(ComputationControlPlaneError,match="LP03_NUMERICAL_WORK_NOT_OPEN"):
                compute(case,work)
            assert dict(work.consumed) == consumed
            if name == "nonexact_final_division":
                assert len(work._math26_context_steps) == 4 and len(work._math26_context_prefix) == 3
                assert "Inexact" in work._math26_context_steps[3][6]
            if name == "final_encoding":
                assert len(work._math26_context_prefix) == 4 and consumed["retained_decimal_inputs"] == 8
            denials.append(dict(case=name,reason=reason,consumed=consumed,
                retained_steps=len(work._math26_context_steps),completed_steps=len(work._math26_context_prefix)))
        for name in ("statistical_to_kelly","M26_to_kelly","market_to_kelly","kelly_to_statistical","kelly_to_M26","kelly_to_market","kelly_result_as_source"):
            work = _EvidenceNumericalWorkV1(limits,retained_input_capacity=32)
            if name.endswith("_to_kelly"):
                reader = {"statistical_to_kelly":work.parse_decimal_v1,"M26_to_kelly":work._parse_math26_decimal_v1,
                          "market_to_kelly":work._parse_market_decimal_v1}[name]
                reader("1")
                refused = lambda: compute(cases[0],work)
            elif name == "kelly_result_as_source":
                compute(cases[0],work)
                result = work._math26_context_prefix[-1][5]
                refused = lambda: work._exact_kelly_decimal_v1(result)
            else:
                value = work._parse_kelly_decimal_v1("1")
                reader = {"kelly_to_statistical":work._exact,"kelly_to_M26":work._exact_math26_decimal_v1,
                          "kelly_to_market":work._exact_market_decimal_v1}[name]
                refused = lambda: reader(value)
            with pytest.raises(ComputationControlPlaneError,match="LP03_NUMERICAL_DECIMAL_PROFILE_MISMATCH"):
                refused()
            denials.append(dict(case=name,reason=work.failure,consumed=dict(work.consumed)))
    print("LP03_KELLY_ORDERED_CONTEXT_QUALIFICATION=" + json.dumps(dict(
        scope="PURE_KELLY_DOMAINS_ORDERED_CONTEXT_AND_FIRST_TIE_SELECTION_ONLY",positives=positives,denials=denials,
        hostile_ambient_unchanged=True,tiny_source_bits_derived_intermediates=dict(tiny.consumed),
        original_source_or_runtime_authority=False),default=lambda value:dict(value) if isinstance(value,MappingProxyType) else value,sort_keys=True))


def _assert_lp03_uniform_coordinate_recipe() -> None:
    from dataclasses import replace
    from fractions import Fraction
    import random
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import ContractValidationError
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.evidence_execution import (
        _worker_environment_v1, sample_evidence_uniform53_v1,
    )
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.parameter_policy import _EvidenceNumericalWorkV1

    limits = dict(max_input_bits=4096, max_work_bits=65536, max_serialized_bytes=65536)
    environment = _worker_environment_v1()
    coordinates = (1, 2, 3, 4, 5, 6, 7, 8)
    encoded = b"QTT-LP03-SCENARIO-V1\0\0\1\1\0\1\2\0\1\3\0\1\4\0\1\5\0\1\6\0\1\7\0\1\10"
    before_global = random.getstate()
    work = _lp03_numeric_work(limits)
    result = sample_evidence_uniform53_v1(coordinates, expected_environment=environment, work=work)
    # Literal retained reference vector, not recomputed through production RNG.
    assert result["uniform53_bits"] == 956095223955784
    assert Fraction(int(result["uniform"]["numerator"]), int(result["uniform"]["denominator"])) == Fraction(119511902994473, 1125899906842624)
    assert result["encoded_coordinate"] == encoded.hex()
    assert work.consumed["random_draws"] == 1 and random.getstate() == before_global
    observed = {}
    for index in reversed(range(8)):
        changed = coordinates[:index] + (coordinates[index] + 1,) + coordinates[index + 1:]
        observed[changed] = sample_evidence_uniform53_v1(changed, expected_environment=environment, work=work)
    for changed in reversed(tuple(observed)):
        replay = sample_evidence_uniform53_v1(changed, expected_environment=environment, work=work)
        assert deterministic_json(replay) == deterministic_json(observed[changed])
        assert replay["encoded_coordinate"] != encoded.hex()
    replay = sample_evidence_uniform53_v1(coordinates, expected_environment=environment, work=work)
    assert deterministic_json(replay) == deterministic_json(result)
    assert work.consumed["random_draws"] == 18 and random.getstate() == before_global

    zero = sample_evidence_uniform53_v1((0,) * 8, expected_environment=environment, work=_lp03_numeric_work(limits))
    assert zero["encoded_coordinate"] == (b"QTT-LP03-SCENARIO-V1\0" + b"\0\1\0" * 8).hex()
    largest = sample_evidence_uniform53_v1((2**256 - 1,) * 8, expected_environment=environment, work=_lp03_numeric_work(limits))
    assert largest["encoded_coordinate"] == (b"QTT-LP03-SCENARIO-V1\0" + (b"\0\x20" + b"\xff" * 32) * 8).hex()
    for bad in ((), coordinates[:-1], coordinates + (0,), list(coordinates), (True,) + coordinates[1:],
                (-1,) + coordinates[1:], (2**256,) + coordinates[1:]):
        work = _lp03_numeric_work(limits)
        with pytest.raises(ContractValidationError, match="RNG_COORDINATE"):
            sample_evidence_uniform53_v1(bad, expected_environment=environment, work=work)
        assert work.state == "FAILED" and work.consumed["random_draws"] == 0
    work = _lp03_numeric_work(dict(limits, max_work_bits=8))
    with pytest.raises(ContractValidationError, match="WORK_BITS_EXHAUSTED"):
        sample_evidence_uniform53_v1(coordinates, expected_environment=environment, work=work)
    assert work.consumed["random_draws"] == 0 and work.state == "FAILED"

    # Instrument this finite recipe to verify one actual getrandbits(53) call;
    # these observations are unit coverage, not native execution authority.
    original_random, calls = random.Random, []
    def observed_random(seed):
        calls.append(("seed", seed))
        generator = original_random(seed)
        class ObservedGenerator:
            def getrandbits(self, width):
                calls.append(("getrandbits", width))
                return generator.getrandbits(width)
        return ObservedGenerator()
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(random, "Random", observed_random)
        sample_evidence_uniform53_v1(coordinates, expected_environment=environment, work=_lp03_numeric_work(limits))
        assert calls == [("seed", int.from_bytes(encoded, "big")), ("getrandbits", 53)]
        work = _lp03_numeric_work(limits)
        from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import ReasonCode
        with pytest.raises(ContractValidationError, match="RNG_ENVIRONMENT_MISMATCH") as mismatch:
            sample_evidence_uniform53_v1(coordinates,
                expected_environment=replace(environment, complete_version=environment.complete_version + "-different"), work=work)
        assert mismatch.value.reason_code is ReasonCode.EVIDENCE_RNG_ENVIRONMENT_MISMATCH
        assert len(calls) == 2 and work.consumed["random_draws"] == 0 and work.state == "FAILED"
        from src.qtt.stage1_prediction_markets.qku_computation_control_plane import evidence_execution
        work = _lp03_numeric_work(limits)
        def unexpected_environment_observation():
            raise AssertionError("malformed expected environment advanced to native comparison")
        patch.setattr(evidence_execution, "_worker_environment_v1", unexpected_environment_observation)
        with pytest.raises(ContractValidationError, match="LP03_RNG_EXPECTED_ENVIRONMENT_TYPE") as malformed:
            sample_evidence_uniform53_v1(coordinates, expected_environment={}, work=work)
        assert malformed.value.reason_code is ReasonCode.INVALID_CONTRACT
        assert work.consumed["random_draws"] == 0 and work.state == "FAILED"


def _assert_lp03_cashflow_source_frame_data():
    import json
    from copy import deepcopy
    from types import SimpleNamespace
    from unittest.mock import patch
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.bindings import FORMULA_INPUT_AUTHORITY_BY_MATH_ID
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane import implementation_registry as formulas
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.implementation_registry import (
        CURRENT_IMPLEMENTATION_REGISTRY,resolve_evidence_invocation_v1)
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.models import (
        EvidenceOriginV1,_evidence_cashflow_source_slices_v1,_evidence_normalized_event_v1)
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.input_resolver import _evidence_cashflow_worker_payload_v1
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.evidence_execution import (
        WORKER_PROTOCOL_V1,encode_evidence_worker_frame_v1,decode_evidence_worker_frame_v1,_worker_cashflow_inputs_v1)
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import ComputationControlPlaneError
    cases = (('MATH-06', {'p_win': '0.50', 'p_void': '0.25', 'win_terminal_cashflow_total': '1.00', 'lose_terminal_cashflow_total': '0.00', 'void_terminal_cashflow_total': '0.40', 'fill_probability': '0.50', 'entry_trade_cashflow_total': '-0.40', 'no_fill_cashflow_total': '-0.02', 'platform_fee_total': '0.01', 'builder_fee_total': '0.02', 'other_fee_total': '0.03', 'expected_rebate_total': '0.005', 'exit_slippage_reserve_total': '0.01', 'market_impact_reserve_total': '0.01', 'latency_adverse_selection_reserve_total': '0.01', 'capital_time_cost_reserve_total': '0.01', 'cashflow_basis': 'SIGNED_TOTAL_ACCOUNT_CASHFLOW_EACH_EVENT_INCLUDED_EXACTLY_ONCE'}), ('MATH-07', {'outcome_ids': ['WIN', 'LOSE'], 'outcome_probabilities': ['0.25', '0.75'], 'outcome_terminal_cashflow_totals': ['1.00', '0.00'], 'probability_simplex_tolerance': '0.00', 'fill_probability': '0.50', 'entry_trade_cashflow_total': '-0.40', 'no_fill_cashflow_total': '-0.02', 'platform_fee_total': '0.01', 'builder_fee_total': '0.02', 'other_fee_total': '0.03', 'expected_rebate_total': '0.005', 'exit_slippage_reserve_total': '0.01', 'market_impact_reserve_total': '0.01', 'latency_adverse_selection_reserve_total': '0.01', 'capital_time_cost_reserve_total': '0.01', 'cashflow_basis': 'SIGNED_TOTAL_ACCOUNT_CASHFLOW_EACH_EVENT_INCLUDED_EXACTLY_ONCE'}))
    source_scope=dict(market_scope_id="DATA-MARKET",venue_scope_id="DATA-VENUE",event_scope_id="DATA-EVENT",
        instrument_or_contract_scope_id="DATA-INSTRUMENT",mode_context_id="DATA-SOFTWARE",input_snapshot_id="DATA-SNAPSHOT")
    clocks=dict(observed_time=100,effective_time=99,available_time=101,received_time=102,processed_time=103,as_of_time=104)
    def absent(reason):return dict(state="ABSENT_WITH_REASON",reason=reason)
    def encode(frame,limit=65536):
        return encode_evidence_worker_frame_v1(frame,direction="PARENT_TO_WORKER",attempt_ref="DATA-ATTEMPT",
            fence_ref="DATA-FENCE",ordinal=1,frame_byte_limit=limit)
    def node_count(value):
        if type(value) is dict:return 1+sum(1+node_count(child) for child in value.values())
        if type(value) in (list,tuple):return 1+sum(node_count(child) for child in value)
        return 1
    def forbidden(*args,**kwargs):raise AssertionError("source/frame validation invoked a production formula")
    reports=[]
    with patch.object(formulas,"invoke_formula_v34",forbidden),patch.object(formulas,"invoke_evidence_public_wire_v1",forbidden):
        for math_id,inputs in cases:
            context=dict(profile="SOFTWARE_ORIGINAL_SIGNED_TOTAL_CASHFLOW_CONTEXT_V1",input_snapshot_ref="DATA-SNAPSHOT",
                event_ref="DATA-EVENT",instrument_ref="DATA-INSTRUMENT",horizon_ref="DATA-HORIZON",horizon_end_wall_ns=1000,
                currency="USD",cashflow_basis=inputs["cashflow_basis"],account_basis="SYNTHETIC_TOTAL_ACCOUNT_NO_CASH_MOVEMENT",
                account_context_ref="DATA-ACCOUNT",outcome_ids=["WIN","LOSE","VOID"] if math_id=="MATH-06" else list(inputs["outcome_ids"]),
                ordered_outcome_roles=["WIN","LOSE","VOID"] if math_id=="MATH-06" else ["DECLARED_OUTCOME_ORDER"],
                empirical_evidence_bundle=absent("NO_EMPIRICAL_MODEL_FEE_OR_ACCOUNT_BUNDLE_IN_SOFTWARE_FIXTURE"))
            slices=[]
            bindings=FORMULA_INPUT_AUTHORITY_BY_MATH_ID[math_id]
            for index,binding in enumerate(bindings):
                record="DATA-SOURCE::"+binding.input_name;ref=dict(store_id="DATA-STORE::"+str(index),record_id=record)
                original=dict(representation="OWNER_PACKET_V1",origin="SOFTWARE_CONFORMANCE",record_ref=record,
                    owner_id=binding.accepted_upstream_owner_id,record_kind=binding.accepted_packet_or_snapshot_type,
                    schema_id=binding.schema_id,schema_version=binding.schema_version,context_id="DATA-CONTEXT",
                    scope=deepcopy(source_scope),source_epoch_id="DATA-EPOCH",input_version="DATA-V1",native_clocks=dict(clocks),ttl_ns=500,
                    values={binding.exact_field_path:deepcopy(inputs[binding.input_name]),"cashflow_context":deepcopy(context)},
                    authorized_binding_ids=[binding.binding_id],producer_receipt_id="DATA-RECEIPT::"+str(index),
                    producer_receipt_type=binding.producer_receipt_type,source_state_and_claim_lineage=binding.source_state_and_claim_lineage,
                    provider_sequence=absent("PROVIDER_SEQUENCE_UNAVAILABLE"),revision=index,
                    prior_revision_available_wall_ns_or_absence=absent("NO_PRIOR_REVISION_CLOCK"),source_conflict=False)
                slices.append(dict(original_record_refs=[ref],reconstructed_canonical_events=[original],
                    original_native_clock_companions=[[record,[[name,value] for name,value in clocks.items()]]],
                    access_wall_ns=110,origin="SOFTWARE_CONFORMANCE",rights_refs=["DATA-RIGHT::"+str(index)],revision_limitations=[]))
            payload=dict(association_profile="ORIGINAL_SOFTWARE_SIGNED_TOTAL_CASHFLOW_CONTEXT",math_id=math_id,source_slices=slices)
            source_data=_evidence_cashflow_source_slices_v1(payload)
            assert len(source_data)==len(bindings)==(17 if math_id=="MATH-06" else 16)
            assert json.loads(deterministic_json(source_data))==slices
            event=dict(event_id="DATA-CASHFLOW",kind="SYNTHETIC_SIGNED_TOTAL_CASHFLOW_CONTEXT",origin="SOFTWARE_CONFORMANCE",
                source_record_ref=slices[0]["original_record_refs"][0],availability_wall_ns=101,effective_wall_ns=99,
                provider_order_or_absence=absent("NO_AGGREGATE_PROVIDER_ORDER"),source_revision=0,connection_epoch="DATA-EPOCH",
                local_ordinal=0,payload=payload)
            contract_source=CURRENT_IMPLEMENTATION_REGISTRY[math_id].contract
            contract=resolve_evidence_invocation_v1(math_id,implementation_pin=contract_source.implementation_id,
                specification_pin=contract_source.specification_version,resource_policy_ref="DATA-RESOURCES",origin=EvidenceOriginV1.SOFTWARE_CONFORMANCE)
            frame=dict(protocol=WORKER_PROTOCOL_V1,kind="INPUT_SEGMENT",attempt_ref="DATA-ATTEMPT",fence_ref="DATA-FENCE",ordinal=1,
                payload=dict(segment_ordinal=0,final_segment=True,inputs=deepcopy(inputs),
                    original_record_refs=[part["original_record_refs"][0] for part in slices],event=event,
                    invocation_contract=json.loads(deterministic_json(contract))))
            raw=encode(frame)
            assert raw==len(raw[4:]).to_bytes(4,"big")+deterministic_json(frame).encode()
            decoded=decode_evidence_worker_frame_v1(raw,direction="PARENT_TO_WORKER",attempt_ref="DATA-ATTEMPT",
                fence_ref="DATA-FENCE",ordinal=1,frame_byte_limit=65536)
            assert deterministic_json(decoded)==deterministic_json(frame) and len(raw)<=65540 and node_count(frame)<=4096
            typed=_worker_cashflow_inputs_v1(decoded["payload"],_evidence_normalized_event_v1(event))
            assert set(typed)==set(inputs) and typed["cashflow_basis"]==inputs["cashflow_basis"]
            assert str(typed["fill_probability"])==inputs["fill_probability"]
            assert tuple(part.reconstructed_canonical_events[0]["source_state_and_claim_lineage"] for part in source_data)==tuple(binding.source_state_and_claim_lineage for binding in bindings)
            def sources(chosen):return chosen["payload"]["event"]["payload"]["source_slices"]
            def source(chosen,index=0):return sources(chosen)[index]["reconstructed_canonical_events"][0]
            def metadata(chosen,index=0):return source(chosen,index)["values"]["cashflow_context"]
            mutations=[
                ("source_omission",lambda chosen:sources(chosen).pop(),"LP03_CASHFLOW_SOURCE_ROSTER"),
                ("source_order",lambda chosen:sources(chosen).reverse(),"LP03_CASHFLOW_ORIGINAL_BINDING_SOURCE_JOIN"),
                ("binding_lineage",lambda chosen:source(chosen).update(source_state_and_claim_lineage="WRONG-LINEAGE"),"LP03_CASHFLOW_ORIGINAL_BINDING_SOURCE_JOIN"),
                ("binding_owner",lambda chosen:source(chosen).update(owner_id="WRONG-OWNER"),"LP03_CASHFLOW_ORIGINAL_BINDING_SOURCE_JOIN"),
                ("binding_receipt_type",lambda chosen:source(chosen).update(producer_receipt_type="WRONG-RECEIPT-TYPE"),"LP03_CASHFLOW_ORIGINAL_BINDING_SOURCE_JOIN"),
                ("binding_schema",lambda chosen:source(chosen).update(schema_version="9.9"),"LP03_CASHFLOW_ORIGINAL_BINDING_SOURCE_JOIN"),
                ("binding_roster",lambda chosen:source(chosen)["authorized_binding_ids"].append(bindings[1].binding_id),"LP03_CASHFLOW_ORIGINAL_BINDING_SOURCE_JOIN"),
                ("receipt_duplicate",lambda chosen:source(chosen,1).update(producer_receipt_id=source(chosen)["producer_receipt_id"]),"LP03_CASHFLOW_ORIGINAL_CONTEXT_JOIN"),
                ("source_clock_companion",lambda chosen:source(chosen)["native_clocks"].update(as_of_time=105),"LP03_SOURCE_SLICE_EVENT_CLOCK_JOIN"),
                ("source_horizon",lambda chosen:metadata(chosen).update(horizon_end_wall_ns=104),"LP03_CASHFLOW_ORIGINAL_SCOPE_HORIZON"),
                ("snapshot_context",lambda chosen:metadata(chosen).update(input_snapshot_ref="WRONG-SNAPSHOT"),"LP03_CASHFLOW_ORIGINAL_SCOPE_HORIZON"),
                ("currency_context",lambda chosen:metadata(chosen).update(currency="EUR"),"LP03_CASHFLOW_ORIGINAL_CONTEXT_JOIN"),
                ("account_context",lambda chosen:metadata(chosen).update(account_context_ref="OTHER-ACCOUNT"),"LP03_CASHFLOW_ORIGINAL_CONTEXT_JOIN"),
                ("account_basis",lambda chosen:metadata(chosen).update(account_basis="REAL_ACCOUNT"),"LP03_CASHFLOW_ORIGINAL_CONTEXT_PROFILE"),
                ("outcome_order",lambda chosen:metadata(chosen)["outcome_ids"].reverse(),"LP03_CASHFLOW_ORIGINAL_CONTEXT_JOIN"),
                ("outcome_roles",lambda chosen:metadata(chosen).update(ordered_outcome_roles=["LOSS_FIRST"]),"LP03_CASHFLOW_ORIGINAL_OUTCOME_ORIENTATION"),
                ("empirical_absence",lambda chosen:metadata(chosen).update(empirical_evidence_bundle=absent("UNSPECIFIED")),"LP03_CASHFLOW_EMPIRICAL_BUNDLE_ABSENCE"),
                ("read_roster",lambda chosen:chosen["payload"]["original_record_refs"].pop(),"LP03_WORKER_CASHFLOW_SOURCE_ROSTER_JOIN"),
                ("direct_input",lambda chosen:chosen["payload"]["inputs"].update(fill_probability="0.75"),"LP03_WORKER_CASHFLOW_ORIGINAL_TEXT_JOIN"),
                ("event_summary",lambda chosen:chosen["payload"]["event"].update(availability_wall_ns=102),"LP03_CASHFLOW_CONTEXT_SUMMARY_JOIN"),
                ("contract_math",lambda chosen:chosen["payload"]["event"]["payload"].update(math_id="MATH-03"),"LP03_CASHFLOW_SOURCE_ROSTER"),
            ]
            denied=[]
            for label,mutation,diagnostic in mutations:
                changed=deepcopy(frame);mutation(changed)
                with pytest.raises(ComputationControlPlaneError,match=diagnostic) as error:encode(changed)
                denied.append(dict(case=label,diagnostic=str(error.value)))
            with pytest.raises(ComputationControlPlaneError,match="LP03_PROJECTION_JSON_BYTES") as error:encode(frame,len(raw)-5)
            denied.append(dict(case="actual_complete_frame_one_byte_short",diagnostic=str(error.value)))
            too_many=deepcopy(frame);too_many["payload"]["inputs"]["outcome_ids"]=["X"]*4096
            with pytest.raises(ComputationControlPlaneError,match="LP03_PROJECTION_JSON_NODES_OR_DEPTH") as error:encode(too_many)
            denied.append(dict(case="complete_frame_node_ceiling",diagnostic=str(error.value)))
            with pytest.raises(ComputationControlPlaneError,match="LP03_ORIGINAL_INVOCATION_INPUTS_CHANGED") as error:
                _evidence_cashflow_worker_payload_v1(frame,SimpleNamespace(invocation_original=None),contract,
                    original_record_refs=frame["payload"]["original_record_refs"],frame_byte_limit=65536)
            denied.append(dict(case="decoded_data_is_not_parent_custody",diagnostic=str(error.value)))
            assert encode(frame)==raw
            reports.append(dict(math_id=math_id,frame=frame,frame_hex=raw.hex(),frame_bytes=len(raw),frame_nodes=node_count(frame),
                source_count=len(source_data),binding_ids=[binding.binding_id for binding in bindings],denials=denied))
    print("LP03_CASHFLOW_SOURCE_FRAME_DATA_QUALIFICATION="+json.dumps(dict(cases=reports,
        scope="SYNTHETIC_DECODED_SOURCE_AND_COMPLETE_FRAME_DATA_ONLY_NO_CUSTODY_GRANT_NATIVE_LANE_OR_PUBLICATION_AUTHORITY"),sort_keys=True,separators=(",",":")))


def _assert_lp03_cashflow_preregistered_enclosure():
    import json
    from decimal import Context,ROUND_UP,localcontext
    from fractions import Fraction
    from unittest.mock import patch
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane import implementation_registry as formulas
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.parameter_policy import (
        _EvidenceNumericalWorkV1,_validate_evidence_cashflow_bounds_v1)
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import ComputationControlPlaneError
    limits = dict(max_input_bits=4096,max_work_bits=65536,max_serialized_bytes=65536)
    basis = "SIGNED_TOTAL_ACCOUNT_CASHFLOW_EACH_EVENT_INCLUDED_EXACTLY_ONCE"
    binary = (("p_win","0.50"),("p_void","0.25"),("fill_probability","0.50"),
        ("entry_trade_cashflow_total","-0.40"),("win_terminal_cashflow_total","1.00"),
        ("lose_terminal_cashflow_total","0.00"),("void_terminal_cashflow_total","0.40"),
        ("no_fill_cashflow_total","-0.02"),("platform_fee_total","0.01"),("builder_fee_total","0.02"),
        ("other_fee_total","0.03"),("expected_rebate_total","0.005"),("exit_slippage_reserve_total","0.01"),
        ("market_impact_reserve_total","0.01"),("latency_adverse_selection_reserve_total","0.01"),
        ("capital_time_cost_reserve_total","0.01"))
    multiple = (("probability_simplex_tolerance","0.05"),*binary[2:4],*binary[7:])
    binary_expected = (("expected_net_cash","0.042500"),("expected_net_cash_if_filled","0.1050"),
        ("expected_terminal_cashflow","0.6000"),("p_lose","0.25"))
    multi_expected = (("expected_net_cash","-0.132500"),("expected_net_cash_if_filled","-0.2450"),
        ("expected_terminal_cashflow","0.2500"),("outcome_ids",("WIN","LOSE")),
        ("normalized_probabilities",("0.25","0.75")),("original_probability_sum","1.00"),("normalization_applied",False))
    normalized_expected = (*multi_expected[:5],("original_probability_sum","0.96"),("normalization_applied",True))
    tri_expected = (*multi_expected[:3],("outcome_ids",("A","B","C")),
        ("normalized_probabilities",("0.25","0.25","0.50")),*multi_expected[5:])
    binary_steps = ("0.50","0.25","0.01","0.03","0.06","0.07","0.08","0.09","0.10",
        "0.5000","0.0000","0.5000","0.1000","0.6000","0.2000","0.1000","0.1050",
        "0.052500","0.50","-0.0100","0.042500")
    multi_steps = ("0.25","1.00","0.00","0.00","0.2500","0.2500","0.0000","0.2500",
        "0.01","0.03","0.06","0.07","0.08","0.09","0.10","-0.1500","-0.2500","-0.2450",
        "-0.122500","0.50","-0.0100","-0.132500")
    normalized_steps = ("0.24","0.96","-0.04","0.04","0.25","0.75",*multi_steps[4:])
    tri_steps = ("0.25","0.50","1.00","0.00","0.00","0.2500","0.2500","0.0000","0.2500",
        "0.0000","0.2500",*multi_steps[8:])
    def calculate(work,math_id="MATH-06",**changes):
        source = changes.pop("source_texts",binary if math_id=="MATH-06" else multiple)
        args = dict(cashflow_basis=basis,lower_text="-2",upper_text="2",
            expected_fields=binary_expected if math_id=="MATH-06" else multi_expected,work=work)
        if math_id=="MATH-07":
            args.update(outcome_ids=("WIN","LOSE"),probability_texts=("0.25","0.75"),terminal_texts=("1.00","0.00"))
        args.update(changes)
        return _validate_evidence_cashflow_bounds_v1(math_id,source,**args)
    def replace_source(source,name,text):
        return tuple((key,text if key==name else value) for key,value in source)
    def forbidden(*args,**kwargs):
        raise AssertionError("cashflow admission invoked production formula")
    def ratio(value):
        return Fraction(int(value["numerator"]),int(value["denominator"]))
    wire_size = lambda value:len(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(",",":"),allow_nan=False).encode())
    charge = lambda proof:sum(wire_size(row) for row in proof["steps"])+wire_size(proof["summary"])+wire_size(proof)
    reports = []
    with patch.object(formulas,"invoke_formula_v34",forbidden),patch.object(formulas,"compute_math_06_binary_contract_expected_net_cash_v2",forbidden),patch.object(formulas,"compute_math_07_multi_outcome_expected_net_cash_v2",forbidden):
        for label,math_id,changes,steps,retained,expected_net in (
            ("binary","MATH-06",{},binary_steps,22,Fraction(17,400)),
            ("multi","MATH-07",{},multi_steps,24,Fraction(-53,400)),
            ("normalized","MATH-07",dict(probability_texts=("0.24","0.72"),expected_fields=normalized_expected),normalized_steps,24,Fraction(-53,400)),
            ("three_outcomes","MATH-07",dict(outcome_ids=("A","B","C"),probability_texts=("0.25","0.25","0.50"),
                terminal_texts=("1.00","0.00","0.00"),expected_fields=tri_expected),tri_steps,27,Fraction(-53,400))):
            work = _EvidenceNumericalWorkV1(limits,retained_input_capacity=2*retained)
            with localcontext(Context(prec=2,rounding=ROUND_UP,Emin=-3,Emax=3)) as ambient:
                before=str(ambient);first=calculate(work,math_id,**changes);first_counts=dict(work.consumed)
                second=calculate(work,math_id,**changes);assert str(ambient)==before
            assert first==second
            for proof in (first,second):
                assert proof["profile"]=="DECLARED_EXACT_SOURCE_CASHFLOW_ENCLOSURE_V1"
                assert proof["scope"]=="INDEPENDENT_RATIONAL_SOURCE_ENCLOSURE_NO_NATIVE_RETURN_OR_SCALE_AUTHORITY"
                assert tuple(ratio(row["exact"]) for row in proof["steps"])==tuple(Fraction(text) for text in steps)
                assert tuple(row["position"] for row in proof["steps"])==tuple(range(len(steps)))
                for row in proof["steps"]:
                    coefficient,exponent=row["absolute_coefficient"],row["decimal_exponent"]
                    assert type(coefficient) is int and 0<=coefficient<10**34 and (coefficient==0 or coefficient%10!=0)
                    assert -999966<=exponent<=999966
                    assert Fraction(coefficient)*Fraction(10)**exponent==abs(ratio(row["exact"]))
                assert ratio(proof["summary"]["derived_net_cash"])==expected_net
                assert ratio(proof["summary"]["declared_lower"])==-2 and ratio(proof["summary"]["declared_upper"])==2
                assert "original_raw_fields" not in proof and "context" not in proof
                assert all("decimal_text" not in row and "flags" not in row for row in proof["steps"])
            assert first_counts["serialized_bytes"]==charge(first) and work.consumed["serialized_bytes"]==2*charge(first)
            assert first_counts["retained_decimal_inputs"]==first_counts["decimal_constructions"]==retained
            assert work.consumed["retained_decimal_inputs"]==work.consumed["decimal_constructions"]==2*retained
            assert not work._math26_context_steps and not work._math26_context_prefix
            assert all(work.consumed[key]==0 for key in ("random_draws","log_series_terms","square_roots"))
            reports.append(dict(case=label,proofs=(first,second),consumed=dict(work.consumed)))
        denials = [
            ("basis","MATH-06",dict(cashflow_basis="PER_CONTRACT"),"LP03_CASHFLOW_ADMISSION_SIGNED_TOTAL_BASIS"),
            ("roster","MATH-06",dict(source_texts=binary[::-1]),"LP03_CASHFLOW_ADMISSION_ORIGINAL_ROSTER"),
            ("extra_outcomes_binary","MATH-06",dict(outcome_ids=("A","B")),"LP03_CASHFLOW_ADMISSION_OUTCOME_ROSTER"),
            ("probability_domain","MATH-06",dict(source_texts=replace_source(binary,"p_win","1.01")),"LP03_CASHFLOW_ADMISSION_PROBABILITY_DOMAIN"),
            ("simplex","MATH-06",dict(source_texts=replace_source(binary,"p_win","0.90")),"LP03_CASHFLOW_ADMISSION_PROBABILITY_SIMPLEX"),
            ("reversed_bounds","MATH-06",dict(lower_text="2",upper_text="-2"),"LP03_CASHFLOW_ADMISSION_DECLARED_ENCLOSURE"),
            ("tight_bounds","MATH-06",dict(upper_text="0.04"),"LP03_CASHFLOW_ADMISSION_EXPECTATION_OUT_OF_BOUNDS"),
            ("expected_net","MATH-06",dict(expected_fields=(("expected_net_cash","0.04"),*binary_expected[1:])),"LP03_CASHFLOW_ADMISSION_DECLARED_EXPECTATION_MISMATCH"),
            ("expected_auxiliary","MATH-06",dict(expected_fields=(*binary_expected[:2],("expected_terminal_cashflow","0.61"),binary_expected[3])),"LP03_CASHFLOW_ADMISSION_DECLARED_EXPECTATION_MISMATCH"),
            ("input_context_precision","MATH-06",dict(source_texts=replace_source(binary,"p_win","0.12345678901234567890123456789012345")),"LP03_CASHFLOW_ADMISSION_EXACT_SOURCE_CONTEXT_UNAVAILABLE"),
            ("first_inexact_intermediate","MATH-06",dict(source_texts=replace_source(binary,"p_win","1E-36")),"LP03_CASHFLOW_ADMISSION_NONEXACT_CONTEXT_INTERMEDIATE"),
            ("duplicate_outcomes","MATH-07",dict(outcome_ids=("WIN","WIN")),"LP03_CASHFLOW_ADMISSION_OUTCOME_IDENTITIES"),
            ("vector_length","MATH-07",dict(probability_texts=("0.25",)),"LP03_CASHFLOW_ADMISSION_OUTCOME_ROSTER"),
            ("expected_outcomes","MATH-07",dict(expected_fields=(*multi_expected[:3],("outcome_ids",("LOSE","WIN")),*multi_expected[4:])),"LP03_CASHFLOW_ADMISSION_EXPECTED_FIELDS"),
            ("negative_tolerance","MATH-07",dict(source_texts=replace_source(multiple,"probability_simplex_tolerance","-0.01")),"LP03_CASHFLOW_ADMISSION_SIMPLEX_TOLERANCE"),
            ("zero_sum","MATH-07",dict(probability_texts=("0.00","0.00")),"LP03_CASHFLOW_ADMISSION_PROBABILITY_SIMPLEX"),
            ("outside_tolerance","MATH-07",dict(probability_texts=("0.24","0.70")),"LP03_CASHFLOW_ADMISSION_PROBABILITY_SIMPLEX"),
            ("nonterminating_normalization","MATH-07",dict(probability_texts=("0.10","0.20"),
                source_texts=replace_source(multiple,"probability_simplex_tolerance","0.70")),"LP03_CASHFLOW_ADMISSION_NONTERMINATING_INTERMEDIATE"),
            ("normalization_bool","MATH-07",dict(expected_fields=(*multi_expected[:-1],("normalization_applied",1))),"LP03_CASHFLOW_ADMISSION_EXPECTED_FIELDS"),
            ("normalization_value","MATH-07",dict(expected_fields=(*multi_expected[:-1],("normalization_applied",True))),"LP03_CASHFLOW_ADMISSION_DECLARED_EXPECTATION_MISMATCH"),
            ("normalized_probability","MATH-07",dict(expected_fields=(*multi_expected[:4],("normalized_probabilities",("0.24","0.76")),*multi_expected[5:])),"LP03_CASHFLOW_ADMISSION_DECLARED_EXPECTATION_MISMATCH"),
        ]
        for name in ("platform_fee_total","builder_fee_total","other_fee_total","expected_rebate_total","exit_slippage_reserve_total",
                "market_impact_reserve_total","latency_adverse_selection_reserve_total","capital_time_cost_reserve_total"):
            denials.append(("negative_"+name,"MATH-06",dict(source_texts=replace_source(binary,name,"-0.01")),"LP03_CASHFLOW_ADMISSION_NONNEGATIVE_FRICTION"))
        for label,math_id,changes,diagnostic in denials:
            work=_EvidenceNumericalWorkV1(limits,retained_input_capacity=64)
            with pytest.raises(ComputationControlPlaneError,match=diagnostic):calculate(work,math_id,**changes)
            assert work.state=="FAILED" and work.failure==diagnostic and not work._math26_context_steps
            counts=dict(work.consumed)
            with pytest.raises(ComputationControlPlaneError,match="LP03_NUMERICAL_WORK_NOT_OPEN"):calculate(work,math_id)
            assert dict(work.consumed)==counts
            reports.append(dict(case=label,failure=work.failure,consumed=counts,retry_denied=True))
        for label,changed_limits,capacity,diagnostic in (
            ("positive_input_bits",dict(limits,max_input_bits=1),22,"LP03_NUMERICAL_INPUT_BITS_EXHAUSTED"),
            ("zero_work",dict(limits,max_work_bits=0),22,"LP03_NUMERICAL_ZERO_BUDGET"),
            ("retained_capacity",limits,21,"LP03_NUMERICAL_RETAINED_INPUT_CAPACITY_EXHAUSTED"),
            ("serialization",dict(limits,max_serialized_bytes=2048),22,"LP03_NUMERICAL_SERIALIZATION_EXHAUSTED")):
            work=_EvidenceNumericalWorkV1(changed_limits,retained_input_capacity=capacity)
            with pytest.raises(ComputationControlPlaneError,match=diagnostic):calculate(work)
            assert work.state=="FAILED" and work.failure==diagnostic and not work._math26_context_steps
            if label=="positive_input_bits":assert work.consumed["decimal_constructions"]==0
            if label=="serialization":assert work.consumed["serialized_bytes"]>0 and work.consumed["retained_decimal_inputs"]==22
            reports.append(dict(case=label,failure=work.failure,limits=changed_limits,consumed=dict(work.consumed)))
        foreign=_EvidenceNumericalWorkV1(limits,retained_input_capacity=64)
        with foreign:foreign._parse_market_decimal_v1("0.5")
        with pytest.raises(ComputationControlPlaneError,match="LP03_NUMERICAL_DECIMAL_PROFILE_MISMATCH"):calculate(foreign)
        reports.append(dict(case="foreign_profile",failure=foreign.failure,consumed=dict(foreign.consumed)))
    assert len(reports)==38
    print("LP03_CASHFLOW_ADMISSION_NUMERICAL_QUALIFICATION="+json.dumps(dict(cases=reports,
        disposition="DECLARED_EXACT_SOURCE_ENCLOSURE_ONLY_NO_NATIVE_RETURN_OR_RUNTIME_AUTHORITY"),sort_keys=True,separators=(",",":")))


def _assert_lp03_multi_outcome_cashflow_ordered_proof():
    import json
    from decimal import Context,ROUND_UP,localcontext
    from fractions import Fraction
    from unittest.mock import patch
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane import implementation_registry as formulas
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.parameter_policy import (
        _EvidenceNumericalWorkV1,_bounded_evidence_multi_outcome_cashflow_review_v1)
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import ComputationControlPlaneError
    limits = dict(max_input_bits=4096,max_work_bits=65536,max_serialized_bytes=65536)
    source = (("probability_simplex_tolerance","0.05"),("fill_probability","0.50"),
        ("entry_trade_cashflow_total","-0.40"),("no_fill_cashflow_total","-0.02"),
        ("platform_fee_total","0.01"),("builder_fee_total","0.02"),("other_fee_total","0.03"),
        ("expected_rebate_total","0.005"),("exit_slippage_reserve_total","0.01"),
        ("market_impact_reserve_total","0.01"),("latency_adverse_selection_reserve_total","0.01"),
        ("capital_time_cost_reserve_total","0.01"))
    ids,probabilities,terminals = ("WIN","LOSE"),("0.25","0.75"),("1.00","0.00")
    basis = "SIGNED_TOTAL_ACCOUNT_CASHFLOW_EACH_EVENT_INCLUDED_EXACTLY_ONCE"
    expected = (("expected_net_cash","-0.132500"),("expected_net_cash_if_filled","-0.2450"),
        ("expected_terminal_cashflow","0.2500"),("outcome_ids",ids),("normalized_probabilities",probabilities),
        ("original_probability_sum","1.00"),("normalization_applied",False))
    normalized_expected = (*expected[:5],("original_probability_sum","0.96"),("normalization_applied",True))
    expected_steps = ("0.25","1.00","0.00","0.00","0.2500","0.2500","0.0000","0.2500",
        "0.01","0.03","0.06","0.07","0.08","0.09","0.10","-0.1500","-0.2500","-0.2450",
        "-0.122500","0.50","-0.0100","-0.132500")
    normalized_steps = ("0.24","0.96","-0.04","0.04","0.25","0.75",*expected_steps[4:])
    tri_ids,tri_probabilities,tri_terminals = ("A","B","C"),("0.25","0.25","0.50"),("1.00","0.00","0.00")
    tri_expected = (*expected[:3],("outcome_ids",tri_ids),("normalized_probabilities",tri_probabilities),*expected[5:])
    def original_fields(result):
        return tuple((name,tuple(str(v) for v in result[name]) if name=="normalized_probabilities"
            else result[name] if name in ("outcome_ids","normalization_applied") else str(result[name])) for name,value in expected)
    # These separate original calls are checked against literal expectations.
    originals=[]
    for selected_ids,selected_probabilities,selected_terminals,declared in (
        (ids,probabilities,terminals,expected),(ids,("0.24","0.72"),terminals,normalized_expected),
        (tri_ids,tri_probabilities,tri_terminals,tri_expected)):
        result=formulas.invoke_formula_v34("MATH-07",dict(source,outcome_ids=selected_ids,
            outcome_probabilities=selected_probabilities,outcome_terminal_cashflow_totals=selected_terminals,cashflow_basis=basis))
        assert original_fields(result)==declared
        assert type(result["normalization_applied"])is bool
        originals.append(original_fields(result))
    def calculate(work,**changes):
        args=dict(outcome_ids=ids,probability_texts=probabilities,terminal_texts=terminals,cashflow_basis=basis,
            lower_text="-2",upper_text="2",raw_fields=expected,expected_fields=expected,projected_text="-0.132500",work=work)
        chosen=changes.pop("source_texts",source);args.update(changes)
        return _bounded_evidence_multi_outcome_cashflow_review_v1(chosen,**args)
    def forbidden(*args,**kwargs):
        raise AssertionError("multi-outcome cashflow proof invoked production formula")
    def ratio(value):
        return dict(numerator=str(value.numerator),denominator=str(value.denominator))
    def prefix(work):
        return tuple(dict(position=row[0],operation=row[1],left=str(row[2]),right=str(row[3]),exact=ratio(row[4]),
            actual_return=None if row[5]is None else str(row[5]),flags=row[6],captured_text=row[7],phase=row[8])
            for row in work._math26_context_steps)
    def replace_source(name,text):
        return tuple((key,text if key==name else value)for key,value in source)
    wire_size=lambda value:len(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(",",":"),allow_nan=False).encode())
    charged=lambda proof:sum(wire_size(row)for row in proof["steps"])+wire_size(proof["summary"])+wire_size(proof)
    reports=[]
    with patch.object(formulas,"invoke_formula_v34",forbidden),patch.object(formulas,"compute_math_07_multi_outcome_expected_net_cash_v2",forbidden):
        work=_EvidenceNumericalWorkV1(limits,retained_input_capacity=84)
        with localcontext(Context(prec=2,rounding=ROUND_UP,Emin=-3,Emax=3))as ambient:
            before=str(ambient);first=calculate(work);first_counts=dict(work.consumed);second=calculate(work)
            assert str(ambient)==before
        for i,proof in enumerate((first,second)):
            assert tuple(row["decimal_text"]for row in proof["steps"])==expected_steps
            assert tuple(row["exact"]for row in proof["steps"])==tuple(ratio(Fraction(text))for text in expected_steps)
            assert tuple(row["position"]for row in proof["steps"])==tuple(range(i*22,(i+1)*22))
            assert all(row["flags"]==""for row in proof["steps"])
            assert proof["steps"][3]["operation"]=="SIMPLEX_UNARY_ABSOLUTE"and proof["steps"][3]["operand_arity"]==1
            assert proof["steps"][3]["right_operand_usage"]=="UNUSED_UNARY_PLACEHOLDER"
            assert all(row["operand_arity"]==2 for j,row in enumerate(proof["steps"])if j!=3)
            assert proof["summary"]["expected_net_cash"]==ratio(Fraction(-53,400))
            assert proof["original_raw_fields"]==proof["preregistered_raw_fields"]==expected
        assert first_counts["retained_decimal_inputs"]==40 and work.consumed["retained_decimal_inputs"]==80
        assert first_counts["decimal_constructions"]==42 and work.consumed["decimal_constructions"]==84
        assert first_counts["serialized_bytes"]==charged(first)
        assert work.consumed["serialized_bytes"]==charged(first)+charged(second)
        assert len(work._math26_context_steps)==len(work._math26_context_prefix)==44
        assert all(work.consumed[key]==0 for key in("random_draws","log_series_terms","square_roots"))
        reports.append(dict(case="ordered_no_normalization_twice",proofs=(first,second),consumed=dict(work.consumed),prefix=prefix(work)))
        normalized=_EvidenceNumericalWorkV1(limits,retained_input_capacity=42)
        proof=calculate(normalized,probability_texts=("0.24","0.72"),raw_fields=normalized_expected,expected_fields=normalized_expected)
        assert tuple(row["decimal_text"]for row in proof["steps"])==normalized_steps
        assert tuple(row["exact"]for row in proof["steps"])==tuple(ratio(Fraction(text))for text in normalized_steps)
        assert normalized.consumed["retained_decimal_inputs"]==42 and normalized.consumed["decimal_constructions"]==44
        assert normalized.consumed["serialized_bytes"]==charged(proof)and len(normalized._math26_context_steps)==24
        assert proof["steps"][2]["decimal_text"]=="-0.04"and proof["steps"][3]["decimal_text"]=="0.04"
        reports.append(dict(case="exact_normalization",proof=proof,consumed=dict(normalized.consumed),prefix=prefix(normalized)))
        tri=_EvidenceNumericalWorkV1(limits,retained_input_capacity=48)
        proof=calculate(tri,outcome_ids=tri_ids,probability_texts=tri_probabilities,terminal_texts=tri_terminals,
            raw_fields=tri_expected,expected_fields=tri_expected)
        assert len(proof["steps"])==25 and tri.consumed["retained_decimal_inputs"]==45
        assert tri.consumed["decimal_constructions"]==47 and tri.consumed["serialized_bytes"]==charged(proof)
        assert proof["summary"]["expected_net_cash"]==ratio(Fraction(-53,400))
        reports.append(dict(case="three_original_outcomes",proof=proof,consumed=dict(tri.consumed),prefix=prefix(tri)))
        negatives=[
            ("wrong_basis",dict(cashflow_basis="PER_CONTRACT"),"SIGNED_TOTAL_BASIS"),
            ("missing_scalar_source",dict(source_texts=source[:-1]),"ORIGINAL_ROSTER"),
            ("reordered_scalar_source",dict(source_texts=tuple(reversed(source))),"ORIGINAL_ROSTER"),
            ("binary64_cash",dict(source_texts=replace_source("entry_trade_cashflow_total",-0.4)),"ORIGINAL_ROSTER"),
            ("missing_probability",dict(probability_texts=("0.25",)),"OUTCOME_ROSTER"),
            ("missing_terminal",dict(terminal_texts=("1.00",)),"OUTCOME_ROSTER"),
            ("duplicate_ids",dict(outcome_ids=("WIN","WIN")),"OUTCOME_IDENTITIES"),
            ("nontext_id",dict(outcome_ids=("WIN",1)),"OUTCOME_IDENTITIES"),
            ("negative_probability",dict(probability_texts=("-0.25","0.75")),"PROBABILITY_DOMAIN"),
            ("probability_above_one",dict(probability_texts=("1.01","0.00")),"PROBABILITY_DOMAIN"),
            ("negative_fill",dict(source_texts=replace_source("fill_probability","-0.01")),"PROBABILITY_DOMAIN"),
            ("negative_tolerance",dict(source_texts=replace_source("probability_simplex_tolerance","-0.01")),"SIMPLEX_TOLERANCE"),
            ("rounded_source",dict(probability_texts=("0.25000000000000000000000000000000001","0.75")),"EXACT_SOURCE_CONTEXT_UNAVAILABLE"),
            ("zero_simplex",dict(probability_texts=("0.00","0.00"),source_texts=replace_source("probability_simplex_tolerance","1")),"PROBABILITY_SIMPLEX"),
            ("outside_tolerance",dict(probability_texts=("0.24","0.70")),"PROBABILITY_SIMPLEX"),
            ("inexact_normalization",dict(probability_texts=("0.10","0.20"),source_texts=replace_source("probability_simplex_tolerance","0.70")),"NONEXACT_CONTEXT_STEP"),
            ("wrong_raw_net",dict(raw_fields=(("expected_net_cash","-0.1325"),*expected[1:])),"ORIGINAL_RESULT_TEXT_MISMATCH"),
            ("wrong_raw_ids",dict(raw_fields=(*expected[:3],("outcome_ids",tuple(reversed(ids))),*expected[4:])),"ORIGINAL_RESULT_TEXT_MISMATCH"),
            ("wrong_normalized_roster",dict(raw_fields=(*expected[:4],("normalized_probabilities",tuple(reversed(probabilities))),*expected[5:])),"ORIGINAL_RESULT_TEXT_MISMATCH"),
            ("wrong_original_sum_scale",dict(raw_fields=(*expected[:5],("original_probability_sum","1.0"),expected[6])),"ORIGINAL_RESULT_TEXT_MISMATCH"),
            ("wrong_normalization_flag",dict(raw_fields=(*expected[:6],("normalization_applied",True))),"ORIGINAL_RESULT_TEXT_MISMATCH"),
            ("integer_normalization_flag",dict(raw_fields=(*expected[:6],("normalization_applied",0))),"RAW_FIELDS"),
            ("wrong_preregistered",dict(expected_fields=(("expected_net_cash","-0.1325"),*expected[1:])),"ORIGINAL_RESULT_TEXT_MISMATCH"),
            ("wrong_projection",dict(projected_text="-0.1325"),"ORIGINAL_RESULT_TEXT_MISMATCH"),
            ("outside_bound",dict(lower_text="0"),"RESULT_OUT_OF_BOUNDS"),
        ]
        for name in("platform_fee_total","builder_fee_total","other_fee_total","expected_rebate_total",
            "exit_slippage_reserve_total","market_impact_reserve_total","latency_adverse_selection_reserve_total","capital_time_cost_reserve_total"):
            negatives.append(("negative_"+name,dict(source_texts=replace_source(name,"-0.01")),"NONNEGATIVE_FRICTION"))
        for label,changes,reason in negatives:
            failed=_EvidenceNumericalWorkV1(limits,retained_input_capacity=42)
            with pytest.raises(ComputationControlPlaneError,match=reason):calculate(failed,**changes)
            assert failed.state=="FAILED";before=dict(failed.consumed);retained=prefix(failed)
            if label=="inexact_normalization":
                assert len(retained)==5 and retained[-1]["operation"]=="NORMALIZE_PROBABILITY::0"
                assert retained[-1]["flags"]==("Inexact","Rounded")and retained[-1]["captured_text"]is None
                assert retained[-1]["actual_return"]=="0.3333333333333333333333333333333333"and retained[-1]["phase"]=="ATTEMPTED"
                assert failed.consumed["retained_decimal_inputs"]==22
            if label in("zero_simplex","outside_tolerance"):assert len(retained)==4
            if reason in("ORIGINAL_RESULT_TEXT_MISMATCH","RESULT_OUT_OF_BOUNDS"):
                assert len(retained)==22 and retained[-1]["actual_return"]=="-0.132500"
            with pytest.raises(ComputationControlPlaneError):calculate(failed)
            assert dict(failed.consumed)==before and prefix(failed)==retained
            reports.append(dict(case=label,failure=failed.failure,consumed=before,retained_prefix=retained,retry_denied=True))
        for label,chosen_limits,capacity in(
            ("zero_work_bits",dict(limits,max_work_bits=0),42),
            ("positive_input_bits",dict(limits,max_input_bits=1),42),
            ("retained_capacity",limits,41),
            ("serialization",dict(limits,max_serialized_bytes=2048),42)):
            failed=_EvidenceNumericalWorkV1(chosen_limits,retained_input_capacity=capacity)
            with pytest.raises(ComputationControlPlaneError):calculate(failed)
            assert failed.state=="FAILED";before=dict(failed.consumed);retained=prefix(failed)
            if label in("zero_work_bits","positive_input_bits"):assert failed.consumed["decimal_constructions"]==0
            if label=="positive_input_bits":assert "INPUT_BITS_EXHAUSTED"in str(failed.failure)
            if label=="serialization":assert 0<len(retained)<22
            with pytest.raises(ComputationControlPlaneError):calculate(failed)
            assert dict(failed.consumed)==before and prefix(failed)==retained
            reports.append(dict(case=label,failure=failed.failure,limits=dict(failed.limits),consumed=before,retained_prefix=retained,retry_denied=True))
        mixed=_EvidenceNumericalWorkV1(limits,retained_input_capacity=43);mixed.parse_decimal_v1("1")
        with pytest.raises(ComputationControlPlaneError,match="PROFILE_MISMATCH"):calculate(mixed)
        assert mixed.consumed["retained_decimal_inputs"]==1 and mixed._math26_context_steps==[]
        reports.append(dict(case="foreign_decimal_profile",failure=mixed.failure,consumed=dict(mixed.consumed)))
    print("LP03_MULTI_OUTCOME_CASHFLOW_NUMERICAL_QUALIFICATION="+deterministic_json(dict(
        scope="PURE_ORIGINAL_WORK_EXACT_MULTI_OUTCOME_CASHFLOW_REVIEW_ONLY_NO_RUNTIME_OR_SOURCE_AUTHORITY",
        original_formula_raw=originals,cases=reports,limitations=("EXACT_INPUT_AND_INTERMEDIATE_CONTEXT_PROFILE_ONLY",
            "NO_NATIVE_LANE_PUBLICATION_REVIEW_R2_OR_EMPIRICAL_AUTHORITY"))))


def _assert_lp03_binary_cashflow_ordered_proof():
    import json
    from decimal import Context, ROUND_UP, localcontext
    from fractions import Fraction
    from unittest.mock import patch
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane import implementation_registry as formulas
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.parameter_policy import (
        _EvidenceNumericalWorkV1, _bounded_evidence_binary_cashflow_review_v1,
    )
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import ComputationControlPlaneError
    limits = dict(max_input_bits=4096, max_work_bits=65536, max_serialized_bytes=65536)
    source = (("p_win","0.50"),("p_void","0.25"),("fill_probability","0.50"),
        ("entry_trade_cashflow_total","-0.40"),("win_terminal_cashflow_total","1.00"),
        ("lose_terminal_cashflow_total","0.00"),("void_terminal_cashflow_total","0.40"),
        ("no_fill_cashflow_total","-0.02"),("platform_fee_total","0.01"),("builder_fee_total","0.02"),
        ("other_fee_total","0.03"),("expected_rebate_total","0.005"),("exit_slippage_reserve_total","0.01"),
        ("market_impact_reserve_total","0.01"),("latency_adverse_selection_reserve_total","0.01"),
        ("capital_time_cost_reserve_total","0.01"))
    basis = "SIGNED_TOTAL_ACCOUNT_CASHFLOW_EACH_EVENT_INCLUDED_EXACTLY_ONCE"
    expected = (("expected_net_cash","0.042500"),("expected_net_cash_if_filled","0.1050"),
        ("expected_terminal_cashflow","0.6000"),("p_lose","0.25"))
    expected_steps = ("0.50","0.25","0.01","0.03","0.06","0.07","0.08","0.09","0.10",
        "0.5000","0.0000","0.5000","0.1000","0.6000","0.2000","0.1000","0.1050",
        "0.052500","0.50","-0.0100","0.042500")
    # This separate original invocation does not supply expected values.
    original = formulas.invoke_formula_v34("MATH-06", dict(source,cashflow_basis=basis))
    assert tuple((name,str(original[name])) for name,value in expected) == expected
    assert all(type(value) is Decimal for value in original.values())
    def calculate(work, **changes):
        args = dict(cashflow_basis=basis,lower_text="-2",upper_text="2",raw_fields=expected,
            expected_fields=expected,projected_text="0.042500",work=work)
        selected = changes.pop("source_texts",source)
        args.update(changes)
        return _bounded_evidence_binary_cashflow_review_v1(selected,**args)
    def forbidden(*args,**kwargs):
        raise AssertionError("cashflow proof invoked production formula")
    def ratio(value):
        return dict(numerator=str(value.numerator),denominator=str(value.denominator))
    def prefix(work):
        return tuple(dict(position=row[0],operation=row[1],left=str(row[2]),right=str(row[3]),
            exact=ratio(row[4]),actual_return=None if row[5] is None else str(row[5]),
            flags=row[6],captured_text=row[7],phase=row[8]) for row in work._math26_context_steps)
    reports = []
    with patch.object(formulas,"invoke_formula_v34",forbidden), patch.object(formulas,"compute_math_06_binary_contract_expected_net_cash_v2",forbidden):
        work = _EvidenceNumericalWorkV1(limits,retained_input_capacity=78)
        with localcontext(Context(prec=2,rounding=ROUND_UP,Emin=-3,Emax=3)) as ambient:
            ambient_before = str(ambient)
            first = calculate(work)
            first_counts = dict(work.consumed)
            second = calculate(work)
            assert str(ambient) == ambient_before
        for index,proof in enumerate((first,second)):
            assert tuple(row["decimal_text"] for row in proof["steps"]) == expected_steps
            assert tuple(row["exact"] for row in proof["steps"]) == tuple(ratio(Fraction(text)) for text in expected_steps)
            assert tuple(row["position"] for row in proof["steps"]) == tuple(range(index*21,(index+1)*21))
            assert all(row["flags"] == "" for row in proof["steps"])
            assert proof["original_raw_fields"] == proof["preregistered_raw_fields"] == expected
            assert proof["projected_text"] == "0.042500" and proof["summary"]["expected_net_cash"] == ratio(Fraction(17,400))
            assert proof["source_texts"] is source and proof["cashflow_basis"] == basis
            assert proof["context"]["precision"] == 34 and proof["context"]["rounding"] == "ROUND_HALF_EVEN"
        assert first_counts["retained_decimal_inputs"] == 39 and work.consumed["retained_decimal_inputs"] == 78
        assert first_counts["decimal_constructions"] == 41 and work.consumed["decimal_constructions"] == 82
        assert len(work._math26_context_steps) == len(work._math26_context_prefix) == 42
        assert all(record[3] in ("CASHFLOW_FINANCIAL_DECIMAL_V1","CASHFLOW_CONTEXT_RESULT_V1") for record in work._decimal_admissions)
        assert all(work.consumed[key] == 0 for key in ("random_draws","log_series_terms","square_roots"))
        wire_size = lambda value:len(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(",",":"),allow_nan=False).encode("utf-8"))
        charged = lambda proof:sum(wire_size(row) for row in proof["steps"])+wire_size(proof["summary"])+wire_size(proof)
        assert first_counts["serialized_bytes"] == charged(first)
        assert work.consumed["serialized_bytes"] == charged(first)+charged(second)
        reports.append(dict(case="nonzero_all_friction_two_original_proofs",proofs=(first,second),consumed=dict(work.consumed),prefix=prefix(work)))
        for pwin,fill in (("0","0"),("1","1")):
            endpoint_source = tuple((name,pwin if name=="p_win" else fill if name=="fill_probability"
                else "1" if name=="win_terminal_cashflow_total" else "0") for name,text in source)
            endpoint_expected = tuple(zip((name for name,text in expected),(pwin,pwin,pwin,"1" if pwin=="0" else "0"),strict=True))
            endpoint = _EvidenceNumericalWorkV1(limits,retained_input_capacity=39)
            proof = calculate(endpoint,source_texts=endpoint_source,raw_fields=endpoint_expected,
                expected_fields=endpoint_expected,projected_text=pwin)
            assert proof["summary"]["expected_net_cash"] == ratio(Fraction(pwin))
            reports.append(dict(case="exact_probability_endpoint",pwin=pwin,fill=fill,proof=proof,consumed=dict(endpoint.consumed)))
        def replace_source(name,text):
            return tuple((key,text if key==name else value) for key,value in source)
        negatives = [
            ("wrong_basis",dict(cashflow_basis="PER_CONTRACT"),"LP03_CASHFLOW_REVIEW_SIGNED_TOTAL_BASIS"),
            ("missing_source",dict(source_texts=source[:-1]),"LP03_CASHFLOW_REVIEW_ORIGINAL_ROSTER"),
            ("reordered_sources",dict(source_texts=tuple(reversed(source))),"LP03_CASHFLOW_REVIEW_ORIGINAL_ROSTER"),
            ("binary64_cash",dict(source_texts=replace_source("entry_trade_cashflow_total",-0.4)),"LP03_CASHFLOW_REVIEW_ORIGINAL_ROSTER"),
            ("probability_above_one",dict(source_texts=replace_source("p_win","1.01")),"LP03_CASHFLOW_REVIEW_PROBABILITY_DOMAIN"),
            ("negative_fill",dict(source_texts=replace_source("fill_probability","-0.01")),"LP03_CASHFLOW_REVIEW_PROBABILITY_DOMAIN"),
            ("rounded_source_input",dict(source_texts=replace_source("p_win","0.50000000000000000000000000000000001")),"LP03_CASHFLOW_REVIEW_EXACT_SOURCE_CONTEXT_UNAVAILABLE"),
            ("inexact_intermediate",dict(source_texts=replace_source("p_win","1E-36")),"LP03_CASHFLOW_REVIEW_NONEXACT_CONTEXT_STEP"),
            ("simplex_exhausted",dict(source_texts=replace_source("p_win","0.90")),"LP03_CASHFLOW_REVIEW_PROBABILITY_SIMPLEX"),
            ("wrong_raw_member",dict(raw_fields=((expected[0][0],"0.0425"),*expected[1:])),"LP03_CASHFLOW_REVIEW_ORIGINAL_RESULT_TEXT_MISMATCH"),
            ("wrong_preregistered_member",dict(expected_fields=(*expected[:3],("p_lose","0.250"))),"LP03_CASHFLOW_REVIEW_ORIGINAL_RESULT_TEXT_MISMATCH"),
            ("wrong_projection",dict(projected_text="0.0425"),"LP03_CASHFLOW_REVIEW_ORIGINAL_RESULT_TEXT_MISMATCH"),
            ("outside_declared_bound",dict(lower_text="0.05"),"LP03_CASHFLOW_REVIEW_RESULT_OUT_OF_BOUNDS"),
        ]
        for name in ("platform_fee_total","builder_fee_total","other_fee_total","expected_rebate_total",
            "exit_slippage_reserve_total","market_impact_reserve_total","latency_adverse_selection_reserve_total","capital_time_cost_reserve_total"):
            negatives.append(("negative_"+name,dict(source_texts=replace_source(name,"-0.01")),"LP03_CASHFLOW_REVIEW_NONNEGATIVE_FRICTION"))
        for label,changes,reason in negatives:
            failed = _EvidenceNumericalWorkV1(limits,retained_input_capacity=39)
            with pytest.raises(ComputationControlPlaneError,match=reason):
                calculate(failed,**changes)
            assert failed.state == "FAILED"
            before = dict(failed.consumed)
            retained = prefix(failed)
            if label == "inexact_intermediate":
                assert len(retained)==1 and Fraction(retained[0]["actual_return"])==1
                assert retained[0]["flags"]==("Inexact","Rounded") and retained[0]["captured_text"] is None
                assert retained[0]["phase"]=="ATTEMPTED" and failed.consumed["retained_decimal_inputs"]==18
            if label == "simplex_exhausted":
                assert len(retained)==2 and retained[-1]["actual_return"]=="-0.15"
            if label in ("wrong_raw_member","wrong_preregistered_member","wrong_projection","outside_declared_bound"):
                assert len(retained)==21 and retained[-1]["actual_return"]=="0.042500"
            with pytest.raises(ComputationControlPlaneError):
                calculate(failed)
            assert dict(failed.consumed)==before and prefix(failed)==retained
            reports.append(dict(case=label,failure=failed.failure,consumed=before,retained_prefix=retained,retry_denied=True))
        for label,selected_limits,capacity in (
            ("source_bits",dict(limits,max_work_bits=0),39),
            ("retained_capacity",limits,38),
            ("serialization",dict(limits,max_serialized_bytes=2048),39),
        ):
            failed = _EvidenceNumericalWorkV1(selected_limits,retained_input_capacity=capacity)
            with pytest.raises(ComputationControlPlaneError):
                calculate(failed)
            assert failed.state=="FAILED"
            if label=="serialization":assert 0<len(failed._math26_context_steps)<21
            if label=="source_bits":assert failed.consumed["decimal_constructions"]==0
            reports.append(dict(case=label,failure=failed.failure,limits=dict(failed.limits),consumed=dict(failed.consumed),retained_prefix=prefix(failed)))
        mixed = _EvidenceNumericalWorkV1(limits,retained_input_capacity=40)
        mixed.parse_decimal_v1("1")
        with pytest.raises(ComputationControlPlaneError,match="LP03_NUMERICAL_DECIMAL_PROFILE_MISMATCH"):
            calculate(mixed)
        assert mixed.consumed["retained_decimal_inputs"]==1 and mixed._math26_context_steps==[]
        reports.append(dict(case="foreign_decimal_profile",failure=mixed.failure,consumed=dict(mixed.consumed)))
    print("LP03_BINARY_CASHFLOW_NUMERICAL_QUALIFICATION="+deterministic_json(dict(
        scope="PURE_ORIGINAL_WORK_EXACT_BINARY_CASHFLOW_REVIEW_ONLY_NO_RUNTIME_OR_SOURCE_AUTHORITY",
        original_formula_raw={name:str(original[name]) for name,value in expected},cases=reports,
        limitations=("EXACT_INPUT_CONTEXT_AND_INTERMEDIATE_PROFILE_ONLY","NO_MATH07_QUALIFICATION",
            "NO_NATIVE_LANE_PUBLICATION_REVIEW_R2_OR_EMPIRICAL_AUTHORITY"))))



def _assert_lp03_probabilistic_sharpe_ordered_model_proof():
    import math
    import statistics
    import struct
    from fractions import Fraction
    from contextlib import ExitStack
    from unittest.mock import patch
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane import implementation_registry as formulas
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.evidence import IndependentEvidenceReviewV1
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.parameter_policy import _EvidenceNumericalWorkV1
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import ComputationControlPlaneError
    limits = dict(max_input_bits=4096, max_work_bits=65536, max_serialized_bytes=65536)
    # Original literals are independently derived with Fraction/Decimal160 and
    # the finite integral/Machin enclosure, never from this proof or QTT output.
    cases = (('positive', {'estimated_sharpe': 1.0, 'reference_sharpe': 0.0, 'independent_equivalent_observations': 2, 'sample_skewness': 0.0, 'sample_non_excess_kurtosis': 1.0}, {'probabilistic_sharpe_ratio': 0.8413447460685429, 'z_score': 1.0}, 'bfe6a09e667f3bcc', '3ffaec4bd120d37d', 'EXP_INTEGRAL_64'), ('negative', {'estimated_sharpe': -1.0, 'reference_sharpe': 0.0, 'independent_equivalent_observations': 2, 'sample_skewness': 0.0, 'sample_non_excess_kurtosis': 1.0}, {'probabilistic_sharpe_ratio': 0.15865525393145707, 'z_score': -1.0}, '3fe6a09e667f3bcc', '3fd44ed0bb7cb20c', 'EXP_INTEGRAL_64'), ('positive_zero', {'estimated_sharpe': 0.0, 'reference_sharpe': 0.0, 'independent_equivalent_observations': 2, 'sample_skewness': 0.0, 'sample_non_excess_kurtosis': 1.0}, {'probabilistic_sharpe_ratio': 0.5, 'z_score': 0.0}, '0000000000000000', '3ff0000000000000', 'SMALL_ARGUMENT'), ('negative_zero', {'estimated_sharpe': -0.0, 'reference_sharpe': 0.0, 'independent_equivalent_observations': 2, 'sample_skewness': 0.0, 'sample_non_excess_kurtosis': 1.0}, {'probabilistic_sharpe_ratio': 0.5, 'z_score': -0.0}, '0000000000000000', '3ff0000000000000', 'SMALL_ARGUMENT'), ('half_score', {'estimated_sharpe': 0.25, 'reference_sharpe': 0.0, 'independent_equivalent_observations': 5, 'sample_skewness': 0.0, 'sample_non_excess_kurtosis': 1.0}, {'probabilistic_sharpe_ratio': 0.6914624612740131, 'z_score': 0.5}, 'bfd6a09e667f3bcc', '3ff62075e232ac77', 'EXP_INTEGRAL_64'), ('moments', {'estimated_sharpe': 0.25, 'reference_sharpe': -0.1, 'independent_equivalent_observations': 9, 'sample_skewness': 0.5, 'sample_non_excess_kurtosis': 3.0}, {'probabilistic_sharpe_ratio': 0.8508054001546258, 'z_score': 1.0398938937914903}, 'bfe787b5786bbccd', '3ffb39cc3f1d93f5', 'EXP_INTEGRAL_64'), ('near_positive_denominator', {'estimated_sharpe': 1.0, 'reference_sharpe': 0.9999999850988388, 'independent_equivalent_observations': 2, 'sample_skewness': 0.9999999999999999, 'sample_non_excess_kurtosis': 1.0}, {'probabilistic_sharpe_ratio': 0.9213503964748574, 'z_score': 1.414213562373095}, 'bfefffffffffffff', '3ffd7bb3d3a08445', 'EXP_INTEGRAL_64'), ('largest_support', {'estimated_sharpe': 1.4901161193847656e-08, 'reference_sharpe': 0.0, 'independent_equivalent_observations': 9007199254740992, 'sample_skewness': 0.0, 'sample_non_excess_kurtosis': 1.0}, {'probabilistic_sharpe_ratio': 0.9213503964748574, 'z_score': 1.414213562373095}, 'bfefffffffffffff', '3ffd7bb3d3a08445', 'EXP_INTEGRAL_64'), ('positive_subnormal', {'estimated_sharpe': 5e-324, 'reference_sharpe': 0.0, 'independent_equivalent_observations': 2, 'sample_skewness': 0.0, 'sample_non_excess_kurtosis': 1.0}, {'probabilistic_sharpe_ratio': 0.5, 'z_score': 5e-324}, '8000000000000001', '3ff0000000000000', 'SMALL_ARGUMENT'), ('negative_subnormal', {'estimated_sharpe': -5e-324, 'reference_sharpe': 0.0, 'independent_equivalent_observations': 2, 'sample_skewness': 0.0, 'sample_non_excess_kurtosis': 1.0}, {'probabilistic_sharpe_ratio': 0.5, 'z_score': -5e-324}, '0000000000000001', '3ff0000000000000', 'SMALL_ARGUMENT'))
    def bits(value): return struct.pack(">d", value).hex()
    def unpack(value): return struct.unpack(">d", bytes.fromhex(value))[0]
    def run(selected, work, *, inputs=None, raw=None, expected=None, projected=None):
        return IndependentEvidenceReviewV1._bounded_review_probabilistic_sharpe_v1(
            deterministic_json(selected[1] if inputs is None else inputs).encode(),
            deterministic_json(selected[2] if raw is None else raw).encode(),
            deterministic_json(selected[2] if expected is None else expected).encode(),
            selected[2]["probabilistic_sharpe_ratio"] if projected is None else projected, work=work)
    def forbidden(*args, **kwargs):
        raise AssertionError("independent PSR proof called production formula, NormalDist, sqrt, erf, erfc or exp")
    positives = []
    with ExitStack() as stack:
        for name in ("compute_math_17_probabilistic_sharpe_ratio", "_v34_probabilistic_sharpe"):
            stack.enter_context(patch.object(formulas, name, forbidden))
        stack.enter_context(patch.object(statistics.NormalDist, "cdf", forbidden))
        for name in ("sqrt", "erf", "erfc", "exp"):
            stack.enter_context(patch.object(math, name, forbidden))
        for selected in cases:
            work = _EvidenceNumericalWorkV1(limits, retained_input_capacity=0)
            first = run(selected, work)
            prefix = dict(work.consumed)
            second = run(selected, work)
            assert first == second and work.state == "OPEN" and len(first["cells"]) == 16
            enclosure = first["erfc_enclosure"]
            assert enclosure["argument_bits"] == selected[3] and enclosure["derived_erfc_bits"] == selected[4]
            assert enclosure["branch"] == selected[5] and enclosure["integral_terms"] == (0 if selected[5] == "SMALL_ARGUMENT" else 64)
            assert prefix["input_values"] == 10 and prefix["square_roots"] == 4
            assert all(prefix[key] == 0 for key in ("log_series_terms", "random_draws", "decimal_constructions", "retained_decimal_inputs"))
            assert first["summary"]["score_bits"] == bits(selected[2]["z_score"])
            assert first["summary"]["probability_bits"] == bits(selected[2]["probabilistic_sharpe_ratio"])
            # Reconstruct each compact arithmetic cell from its exact bits.
            for row in first["cells"]:
                left, right, value = map(unpack, (row["left"], row["right"], row["candidate"]))
                low = (Fraction(math.nextafter(value, -math.inf)) + Fraction(value)) / 2
                high = (Fraction(value) + Fraction(math.nextafter(value, math.inf))) / 2
                even = int(row["candidate"], 16) & 1 == 0
                if row["kind"] == "SQRT":
                    exact = Fraction(left)
                    assert value >= 0 and (low < 0 or low * low < exact or low * low == exact and even)
                    assert exact < high * high or exact == high * high and even
                else:
                    a, b = Fraction(left), Fraction(right)
                    exact = {"ADD": lambda: a+b, "SUB": lambda: a-b, "MUL": lambda: a*b, "DIV": lambda: a/b}[row["kind"]]()
                    assert low < exact or low == exact and even
                    assert exact < high or exact == high and even
            erfc = unpack(enclosure["derived_erfc_bits"])
            low = (Fraction(math.nextafter(erfc, -math.inf)) + Fraction(erfc)) / 2
            high = (Fraction(erfc) + Fraction(math.nextafter(erfc, math.inf))) / 2
            assert low < Fraction(enclosure["lower_numerator"], 2**128) <= Fraction(enclosure["upper_numerator"], 2**128) < high
            fragments = list(first["cells"]) + [enclosure, first["summary"]]
            charged = sum(len(deterministic_json(value).encode()) for value in fragments + [first])
            assert charged == prefix["serialized_bytes"] and work.consumed["serialized_bytes"] == 2 * charged <= 65536
            positives.append(dict(case=selected[0], proof=first, first_consumption=prefix, cumulative_consumption=dict(work.consumed), repetitions=2))
    base = cases[0]
    mutations = (
        ("boolean_support", "inputs", dict(independent_equivalent_observations=True)),
        ("fractional_support", "inputs", dict(independent_equivalent_observations=2.5)),
        ("one_support", "inputs", dict(independent_equivalent_observations=1)),
        ("support_above_declared_profile", "inputs", dict(independent_equivalent_observations=9007199254740993)),
        ("boolean_estimate", "inputs", dict(estimated_sharpe=True)),
        ("string_reference", "inputs", dict(reference_sharpe="0.0")),
        ("excess_for_nonexcess", "inputs", dict(sample_non_excess_kurtosis=0.0)),
        ("zero_denominator", "inputs", dict(sample_skewness=1.0)),
        ("negative_denominator", "inputs", dict(sample_skewness=2.0)),
        ("argument_region", "inputs", dict(estimated_sharpe=4.0)),
        ("cdf_ulp", "raw", dict(probabilistic_sharpe_ratio=math.nextafter(base[2]["probabilistic_sharpe_ratio"], 1.0))),
        ("score_ulp", "raw", dict(z_score=math.nextafter(1.0, 2.0))),
        ("wrong_expectation", "expected", dict(z_score=-1.0)),
        ("integer_score", "raw", dict(z_score=1)),
        ("boolean_probability", "raw", dict(probabilistic_sharpe_ratio=True)),
    )
    denials = []
    def deny(name, selected, changes, arguments):
        work = _EvidenceNumericalWorkV1(dict(limits, **changes), retained_input_capacity=0)
        with pytest.raises(ComputationControlPlaneError): run(selected, work, **arguments)
        assert work.state == "FAILED"
        consumed = dict(work.consumed)
        with pytest.raises(ComputationControlPlaneError, match="LP03_NUMERICAL_WORK_NOT_OPEN"): run(base, work)
        assert dict(work.consumed) == consumed
        denials.append(dict(case=name, failure=work.failure, consumed=consumed))
    for name, field, changes in mutations:
        value = dict(base[1] if field == "inputs" else base[2], **changes)
        deny(name, base, {}, {field: value})
        if name in ("zero_denominator", "negative_denominator"):
            assert "LP03_SHARPE_POSITIVE_DENOMINATOR_REQUIRED" in denials[-1]["failure"]
            assert denials[-1]["consumed"]["comparisons"] == 22
    for name, selected, changes, arguments in (
        ("projection_ulp", base, {}, dict(projected=math.nextafter(base[2]["probabilistic_sharpe_ratio"], 1.0))),
        ("projection_boolean", base, {}, dict(projected=True)),
        ("signed_zero_score", cases[3], {}, dict(raw=dict(cases[3][2], z_score=0.0))),
        ("coherent_wrong_outputs", base, {}, dict(raw=dict(probabilistic_sharpe_ratio=.5,z_score=0.0),expected=dict(probabilistic_sharpe_ratio=.5,z_score=0.0),projected=.5)),
        ("zero_budget", base, dict(max_serialized_bytes=0), {}),
        ("complete_bytes", base, dict(max_serialized_bytes=10000), {}),
        ("work_bits", base, dict(max_work_bits=1074), {}),
        ("input_bits", cases[8], dict(max_input_bits=64), {}),
        ("machin_work_bits", base, dict(max_work_bits=2048), {}),
    ): deny(name, selected, changes, arguments)
    work = _EvidenceNumericalWorkV1(limits, retained_input_capacity=0)
    completed = 0
    # This smaller 16-cell proof can legitimately fit more than six times.
    # Thirty-two fixed attempts exceed the original 65536-byte allowance:
    # each call retains sixteen charged fragments plus their whole-proof copy.
    for _ in range(32):
        before = dict(work.consumed)
        try: run(base, work)
        except ComputationControlPlaneError: break
        completed += 1
    assert 1 <= completed < 32 and work.state == "FAILED" and before["serialized_bytes"] > 0
    failed = dict(work.consumed)
    with pytest.raises(ComputationControlPlaneError, match="LP03_NUMERICAL_WORK_NOT_OPEN"): run(base, work)
    assert dict(work.consumed) == failed
    print("LP03_SHARPE_NUMERICAL_QUALIFICATION=" + deterministic_json(dict(math_id="MATH-17", positives=positives,
        denials=denials, cumulative_exhaustion=dict(completed=completed, before=before, failed=failed, failure=work.failure),
        scope="PURE_ORDERED_PSR_ERFC_MODEL_ONLY_NO_NATIVE_SOURCE_ROUTE_OR_EMPIRICAL_QUALIFICATION")))


def _assert_lp03_deflated_sharpe_ordered_model_proof():
    import math
    import statistics
    import struct
    from fractions import Fraction
    from contextlib import ExitStack
    from unittest.mock import patch
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane import implementation_registry as formulas
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.evidence import IndependentEvidenceReviewV1
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.parameter_policy import _EvidenceNumericalWorkV1
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import ComputationControlPlaneError
    limits = dict(max_input_bits=4096, max_work_bits=65536, max_serialized_bytes=65536)
    # Independently transcribed original operation schedule, Fraction arithmetic,
    # Decimal160 roots/logs and rigorous erfc intervals produced these literals.
    # No QTT formula/proof output generated their raw or intermediate values.
    cases = (('fractional_lower_central', {'complete_material_trial_sharpes': [-0.1, 0.0, 0.1, 0.2, 0.3], 'effective_independent_trial_count': 1.5, 'candidate_estimated_sharpe': 0.2, 'candidate_independent_equivalent_observations': 5, 'candidate_sample_skewness': 0.0, 'candidate_sample_non_excess_kurtosis': 3.0}, {'deflated_sharpe_ratio': 0.5518878182714037, 'expected_maximum_sharpe_threshold': 0.1341348853779482, 'trial_mean_sharpe': 0.1, 'trial_sharpe_variance': 0.025}, ('3fe0000000000000', '3fb999999999999a', '3fe0000000000000', '3fb999999999999a', 'bfc999999999999a', '3fa47ae147ae147c', 'bfb999999999999a', '3f847ae147ae147c', '0000000000000000', '0000000000000000', '3fb999999999999a', '3f847ae147ae147c', '3fc9999999999999', '3fa47ae147ae147a', '3fb999999999999a', '3f9999999999999a', '3fc43d136248490f', '3fdb0ee6072093ce', '3fe5555555555555', '3fd5555555555556', 'bfc5555555555554', '3f9c71c71c71c719', '3fc3907f6e5d4c3c', '4077f818c82f973f', '40e082c29cbea512', '40b43063717114a8', '40f1af228ccea06a', '40c59fae16460b8d', '40ebd42a0c2cf80d', '40c103a28672d167', '40d5eabda9e0dc42', '40aaccb073230681', '40b519ef82167374', '4089cd5de577e5a4', '408df680083e7680', '406251a896ad040b', '4062be0bfb277fc9', 'c038fd654edf550a', '4088f6d79fd5d044', '40dcd5fc39b05cf8', '40b1a14385f8fb67', '40e565a51b24142b', '40ba29f1489537f4', '40db41ef27fba063', '40b0aa3b3fa098e3', '40c2de36b70b30c1', '409712472bc4b934', '40a0e78355548998', '4074ab9635910aab', '407750999c9ece02', '404c8245811388b5', '404d0245811388b5', 'bfdb91093bfdfa27', 'bfdb91093bfdfa27', 'bfdb91093bfdfa27', 'bfc74f35673eb3c2', '40104f47e84f418f', '3fcf6472f2e6944a', '3fe826e343465aee', '3fd04dc6868cb5dc', '3fb09d071d87bc94', '3fbda069864f4daa', '407225f900555801', '40e0771e5d2ef094', '40ae7cfad0776755', '40f160042c3b4a5b', '40c0161d28edb5a8', '40ea71c5d0d6e294', '40b87bab56a5fa6d', '40d387d73c50f22a', '40a21502aa8a6a29', '40b0be189dca2548', '407f00680034de8e', '4083a95622e10022', '405234059472c208', '40530ccc5d67b984', '40336966537cf8a6', '4082e6dab4af91fa', '40dca57c52572b06', '40aa85928f7697ad', '40e4d9d5d35c5e39', '40b34defb6f5fc8a', '40d98aeec393d188', '40a7a5f346245f86', '40c07295e8c3fc31', '408e74960b03d591', '4099f70a846644c4', '40680a0a5c28050a', '406d54112a438bb7', '403b27349b1191a0', '403c27349b1191a0', '3fe6106b7a2b2d76', '3fe6106b7a2b2d76', '3fe6106b7a2b2d76', '3fd978b67b4dedbf', '3fcba2378f5d27bc', '3fa17a20b0b3b5c4', '3fc12b54f8f9ba3e', '0000000000000000', '3ff0000000000000', '4000000000000000', '3fe0000000000000', '3fb999999999999a', '3f947ae147ae147c', '3ff051eb851eb852', '3fb0dc89413fbeb8', '4000000000000000', '3fc0dc89413fbeb8', '3ff028c1d959b062', '3fc0b201f6546f73', 'bfc0b201f6546f73', '3ff6a09e667f3bcd', 'bfb79c5c0f1a55f2', '3fe1a910a4512ac3'), [{'call': 'Q1', 'probability_bits': '3fd5555555555556', 'q_bits': 'bfc5555555555554', 'branch': 'CENTRAL', 'result_bits': 'bfdb91093bfdfa27'}, {'call': 'Q2', 'probability_bits': '3fe826e343465aee', 'q_bits': '3fd04dc6868cb5dc', 'branch': 'CENTRAL', 'result_bits': '3fe6106b7a2b2d76'}], '3fc0b201f6546f73', '3ff1a910a4512ac3', 'bfb79c5c0f1a55f2'), ('central_zero', {'complete_material_trial_sharpes': [-0.1, 0.0, 0.1, 0.2, 0.3], 'effective_independent_trial_count': 2.0, 'candidate_estimated_sharpe': 0.2, 'candidate_independent_equivalent_observations': 5, 'candidate_sample_skewness': 0.0, 'candidate_sample_non_excess_kurtosis': 3.0}, {'deflated_sharpe_ratio': 0.5140748733078602, 'expected_maximum_sharpe_threshold': 0.18218053569858234, 'trial_mean_sharpe': 0.1, 'trial_sharpe_variance': 0.025}, ('3fe0000000000000', '3fb999999999999a', '3fe0000000000000', '3fb999999999999a', 'bfc999999999999a', '3fa47ae147ae147c', 'bfb999999999999a', '3f847ae147ae147c', '0000000000000000', '0000000000000000', '3fb999999999999a', '3f847ae147ae147c', '3fc9999999999999', '3fa47ae147ae147a', '3fb999999999999a', '3f9999999999999a', '3fc43d136248490f', '3fdb0ee6072093ce', '3fe0000000000000', '3fe0000000000000', '0000000000000000', '0000000000000000', '3fc71eb851eb851f', '407c533e6f2f0d1a', '40e08b78e80ca3fe', '40b7e841e8e94e40', '40f1eaa074462404', '40c9e3acf9ef97e2', '40ece529c5175b22', '40c4e0734c7a7986', '40d7d9260ce4b052', '40b13af84a986d79', '40b8ee8f931d5dac', '4092036673e3efd7', '409417f785473845', '406d09083a2fdf64', '406d756b9eaa5b22', '0000000000000000', '408d804922308bb0', '40dcfa47c5c332d4', '40b4efb522b930e2', '40e5cf734ebc1ada', '40bf8415fabb54e2', '40dc98785485279e', '40b4a90a23773e8b', '40c4dd9e28f68395', '409e26a342df17bd', '40a471b160e1b8dc', '407d8aafabfe7d0b', '408017d989862031', '4057412ed23df8c2', '4057812ed23df8c2', '0000000000000000', '0000000000000000', '0000000000000000', '0000000000000000', '4015bf0a8b145769', '3fc78b56362cef38', '3fea1d2a7274c432', '3fd43a54e4e98864', '3fb992a8e585e276', '3fb4aac7be5127c8', '406951ee7a2b010d', '40e06c2459a870e5', '40a5367776a6c1e2', '40f115d0116cc52f', '40b611a12306a29a', '40e92e72aafc497d', '40b0436b9aa6c73d', '40d179c74d51255e', '409692c130b8812e', '40aab08f296620fd', '40713cca0b220ebf', '40798f0e50af3076', '404081d0781d5d9e', '4042335e0a074c95', '402702905380d215', '407a5f08dfc817b5', '40dc77c1a030ced5', '40a262c6eacce0ed', '40e457a91911c2cd', '40aa46b4b83fde69', '40d800496cde4e33', '409f008a7548fad9', '40bcd254cbc80755', '40829d464940de35', '40940b62a384c916', '4059e42e80770ec7', '40623c1e0e570e11', '40278dc7f5e1637e', '40298dc7f5e1637e', '3fecd081f6c50af8', '3fecd081f6c50af8', '3fecd081f6c50af8', '3fe0a1d5f5b36765', '3fe0a1d5f5b36765', '3fb509c8993173b3', '3fc751b1196586a6', '0000000000000000', '3ff0000000000000', '4000000000000000', '3fe0000000000000', '3fb999999999999a', '3f947ae147ae147c', '3ff051eb851eb852', '3f923f4401a097a0', '4000000000000000', '3fa23f4401a097a0', '3ff028c1d959b062', '3fa2113e01328ace', 'bfa2113e01328ace', '3ff6a09e667f3bcd', 'bf998d148bb35bc4', '3fe0734d2611aeec'), [{'call': 'Q1', 'probability_bits': '3fe0000000000000', 'q_bits': '0000000000000000', 'branch': 'CENTRAL', 'result_bits': '0000000000000000'}, {'call': 'Q2', 'probability_bits': '3fea1d2a7274c432', 'q_bits': '3fd43a54e4e98864', 'branch': 'CENTRAL', 'result_bits': '3fecd081f6c50af8'}], '3fa2113e01328ace', '3ff0734d2611aeec', 'bf998d148bb35bc4'), ('fractional_upper', {'complete_material_trial_sharpes': [-0.1, 0.0, 0.1, 0.2, 0.3], 'effective_independent_trial_count': 3.5, 'candidate_estimated_sharpe': 0.2, 'candidate_independent_equivalent_observations': 5, 'candidate_sample_skewness': 0.0, 'candidate_sample_non_excess_kurtosis': 3.0}, {'deflated_sharpe_ratio': 0.45884521476462836, 'expected_maximum_sharpe_threshold': 0.25218586035960167, 'trial_mean_sharpe': 0.1, 'trial_sharpe_variance': 0.025}, ('3fe0000000000000', '3fb999999999999a', '3fe0000000000000', '3fb999999999999a', 'bfc999999999999a', '3fa47ae147ae147c', 'bfb999999999999a', '3f847ae147ae147c', '0000000000000000', '0000000000000000', '3fb999999999999a', '3f847ae147ae147c', '3fc9999999999999', '3fa47ae147ae147a', '3fb999999999999a', '3f9999999999999a', '3fc43d136248490f', '3fdb0ee6072093ce', '3fd2492492492492', '3fe6db6db6db6db7', '3fcb6db6db6db6dc', '3fa7829cbc14e5e2', '3fc13e1122e64ba6', '40751fd66593355f', '40e07d1217f96c4f', '40b1c4d988703d5d', '40f18869ee3e92f6', '40c2e4f3eecc78b4', '40eb257b824e9357', '40bd41218c160919', '40d4b934c9acf5d5', '40a6552bf4d13231', '40b2de2d42ed894c', '408455413bb7849f', '40887e635e7e157a', '405a654d912ad397', '405b3e145a1fcb13', '403759c84d3fd2a3', '408600594041be5a', '40dcbe4846b3bc69', '40aef9acec0fcc94', '40e521177925f187', '40b6c51fcced25d9', '40da68bac9119bdc', '40ac75b8924efabe', '40c1a6873bcea2ff', '40930567e302ea1d', '409dc22761e74418', '407008dd07e9ebf0', '4072ade06ef7af47', '404421343d11f8a1', '4044a1343d11f8a1', '3fe21c40b42d29fb', '3fe21c40b42d29fb', '3fe21c40b42d29fb', '3fcea08a46dd3883', '4023072939b1cc7c', '3fbae862870ec840', '3feca2f3af1e26f8', '3fd945e75e3c4df0', '3fc3f5d2378d7773', '3f994730d2f06d60', '404ef818a6fd2eaa', '40e05a9071580530', '4089d645795c38cb', '40f09fc8e0aa4792', '409a43a1a4f4a05f', '40e73e5b93c31a2d', '40925c6d5d617f15', '40cd1d6678fb1700', '4076ffbdb5e5fd0a', '40a2472647c6a007', '404ce07f50703164', '4067dca85f364fc7', '4012d979883d9715', '402032f30bc68768', '40099661b9865799', '4060209e7deaf146', '40dc2e86b9ad8459', '4086430b7b8ab04f', '40e38a88d8531f7f', '408edf68327c42bd', '40d5ae6e176a347c', '408120821b1fa893', '40b7364271d9bdb1', '40625607b6c4dc6a', '408a0f00eb79eb12', '403495b1c4495700', '404f72f41a92c635', '3ff8d7c5be1a73f0', '40046be2df0d39f8', '3ff40c29b2b67f51', '3ff40c29b2b67f51', '3ff40c29b2b67f51', '3fe724bac8820cfd', '3feeccdd5a395b1e', '3fc37ad386943d03', '3fd023d029b084e8', '0000000000000000', '3ff0000000000000', '4000000000000000', '3fe0000000000000', '3fb999999999999a', '3f947ae147ae147c', '3ff051eb851eb852', 'bfaab81ae71dc0d8', '4000000000000000', 'bfbab81ae71dc0d8', '3ff028c1d959b062', 'bfba74b69765878a', '3fba74b69765878a', '3ff6a09e667f3bcd', '3fb2b5080e0d8b01', '3fdd5db851d5c56e'), [{'call': 'Q1', 'probability_bits': '3fe6db6db6db6db7', 'q_bits': '3fcb6db6db6db6dc', 'branch': 'CENTRAL', 'result_bits': '3fe21c40b42d29fb'}, {'call': 'Q2', 'probability_bits': '3feca2f3af1e26f8', 'q_bits': '3fd945e75e3c4df0', 'branch': 'CENTRAL', 'result_bits': '3ff40c29b2b67f51'}], 'bfba74b69765878a', '3fed5db851d5c56e', '3fb2b5080e0d8b01'), ('upper_tail', {'complete_material_trial_sharpes': [-0.1, 0.0, 0.1, 0.2, 0.3], 'effective_independent_trial_count': 5.0, 'candidate_estimated_sharpe': 0.2, 'candidate_independent_equivalent_observations': 5, 'candidate_sample_skewness': 0.0, 'candidate_sample_non_excess_kurtosis': 3.0}, {'deflated_sharpe_ratio': 0.4303881082328183, 'expected_maximum_sharpe_threshold': 0.2885656683529947, 'trial_mean_sharpe': 0.1, 'trial_sharpe_variance': 0.025}, ('3fe0000000000000', '3fb999999999999a', '3fe0000000000000', '3fb999999999999a', 'bfc999999999999a', '3fa47ae147ae147c', 'bfb999999999999a', '3f847ae147ae147c', '0000000000000000', '0000000000000000', '3fb999999999999a', '3f847ae147ae147c', '3fc9999999999999', '3fa47ae147ae147a', '3fb999999999999a', '3f9999999999999a', '3fc43d136248490f', '3fdb0ee6072093ce', '3fc999999999999a', '3fe999999999999a', '3fd3333333333334', '3fb70a3d70a3d70c', '3fb7333333333332', '406c6c55ae76143a', '40e06f3ec0dcbbf8', '40a7d481647343c0', '40f12ac060db293e', '40b8e463bfa42eff', '40e988cafe8ffb0a', '40b2832cc55b9600', '40d209b797fe590e', '409a27b09c640120', '40ac7b06df3be0f6', '4074a5fe950b697e', '407cf842da988b35', '404500ca11ae981f', '4046b257a3988716', '402b3c692ab70882', '407d9a6b0c29a08a', '40dc84af28e254f8', '40a4acfefda41733', '40e47c4c9a3f3631', '40adb43bdfa874f9', '40d86dfa51cb6105', '40a1b6224819d989', '40bded435282b564', '4085b26a689ec381', '409595f4b333bbbc', '405f4ca2d0a49d02', '4064f058366dd52e', '402e5c7fe885a84e', '40302e3ff442d427', '3feaee8fa73a1335', '3feaee8fa73a1335', '3feaee8fa73a1335', '3fd6c5d32c9a45f0', '402b2ecd2dd96d43', '3fb2d5de91bd8c2d', '3feda5442dc84e7a', '3fdb4a885b909cf4', '3fb2d5de91bd8c30', 'c004e020fbf6c698', '4004e020fbf6c698', '3ff9d893f32df632', '3f8f7d2cca2e4c00', '3ee8f997bb6acb14', '3f97480a9f3d59c0', '3f36e8dc49e88375', '3fcefe2027dd5079', '3f6e7f6b3577572d', '3ff4630bbdee315e', '3f940fb2cedb8856', '400d56ea7fdab9d5', '3facdef7c0c0dd20', '40174db503e3a724', '3fb6ee6f84f0de3e', '4012e13106de7514', '3fb29401931695df', '3ff7efa6171abbc8', '3db1c3727115cd4e', '3f41f18cc8c0e061', '3ee1a8310deb5d5f', '3f8f24e48aee9296', '3f2ea5911ad602a3', '3fc2fcbb97dba5c1', '3f62af1b8b5ec3f5', '3fe625420dbee48d', '3f85cab8867cad1a', '3ffafe0e575f5f8d', '3f9a8fb414883119', '4000a20f236fb4ab', '3fa05e0efd62841f', '3ff082f077eb1421', '3ff731d49e4805f5', '3ff731d49e4805f5', '3ff731d49e4805f5', '3feac6d14eab5242', '3ff314dd727c3a9d', '3fc822eb795cbc3a', '3fd277dc2314c484', '0000000000000000', '3ff0000000000000', '4000000000000000', '3fe0000000000000', '3fb999999999999a', '3f947ae147ae147c', '3ff051eb851eb852', 'bfb6ac3d591fdedc', '4000000000000000', 'bfc6ac3d591fdedc', '3ff028c1d959b062', 'bfc6730dba0301f1', '3fc6730dba0301f1', '3ff6a09e667f3bcd', '3fbfbf8fa8ffca42', '3fdb8b7a905c9ff5'), [{'call': 'Q1', 'probability_bits': '3fe999999999999a', 'q_bits': '3fd3333333333334', 'branch': 'CENTRAL', 'result_bits': '3feaee8fa73a1335'}, {'call': 'Q2', 'probability_bits': '3feda5442dc84e7a', 'q_bits': '3fdb4a885b909cf4', 'branch': 'TAIL_LE_FIVE', 'result_bits': '3ff731d49e4805f5'}], 'bfc6730dba0301f1', '3feb8b7a905c9ff5', '3fbfbf8fa8ffca42'), ('lower_tail', {'complete_material_trial_sharpes': [-0.1, 0.0, 0.1, 0.2, 0.3], 'effective_independent_trial_count': 1.00001, 'candidate_estimated_sharpe': 0.2, 'candidate_independent_equivalent_observations': 5, 'candidate_sample_skewness': 0.0, 'candidate_sample_non_excess_kurtosis': 3.0}, {'deflated_sharpe_ratio': 0.7585408809474238, 'expected_maximum_sharpe_threshold': -0.1542990630844032, 'trial_mean_sharpe': 0.1, 'trial_sharpe_variance': 0.025}, ('3fe0000000000000', '3fb999999999999a', '3fe0000000000000', '3fb999999999999a', 'bfc999999999999a', '3fa47ae147ae147c', 'bfb999999999999a', '3f847ae147ae147c', '0000000000000000', '0000000000000000', '3fb999999999999a', '3f847ae147ae147c', '3fc9999999999999', '3fa47ae147ae147a', '3fb999999999999a', '3f9999999999999a', '3fc43d136248490f', '3fdb0ee6072093ce', '3fefffeb07583583', '3ee4f8a7ca7d0000', 'bfdfffd60eb06b06', 'c027069f7a2d888c', '4027069f7a2d888c', '400b2502c49ba32a', '3ffcb06bef9dacba', '3f56c11c77584a5c', '3f98b0fd33bb710d', '3fa622fe4692bb8f', '3fd23db5a5ae858d', '3fe05a8fdef61ca0', '3ffc8113f7ce8402', '40098e178bb2e83b', '401b5e7152f7f580', '40288986e89c717e', '403209c13966c21a', '40402bfb90a57350', '40427caa79bec983', '405093012f6cc168', '4050ee1ac76466b2', '3e202f1d3b8dc2f8', '3f41f190cba6760b', '3f50164bd4aa7f42', '3f9091a1fca033d4', '3f9db58d360131ee', '3fc6abc3da55167e', '3fd453488c54bd95', '3ff01e1b9c2ef24a', '3ffce6683bc162c0', '400bdc709109e47a', '4018fa7ce3be73f3', '4020987a60b0e30c', '402dc1d35f98bd13', '402fc1d35f98bd13', '40110f401e1a302e', 'c0110f401e1a302e', 'c0110f401e1a302e', 'c0110f401e1a302e', 'bffcd99ecdb9a115', '4005bf18cb7edda6', '3fd78b46c823bd13', '3fe43a5c9bee2176', '3fc0e9726fb885d8', '3f91e032f79964fc', '3fc4e2b1f2f85880', '4079966f57ba1aab', '40e085ff49ddba19', '40b5919b978bd340', '40f1c5360f304c54', '40c7324ad213965c', '40ec38d13b205ac1', '40c26b70fb33d0f6', '40d69ea4e4415c0a', '40ad86ca88e88169', '40b676fc8cf930e8', '408d530638ecf0da', '4090be142dd9c0db', '4065dad04b55e018', '40664733afd05bd6', '40378c3fe75fce7f', '408aa661cc4e47f4', '40dce3788b1420b6', '40b2dad27fce0647', '40e58cd6fa5eb587', '40bc2161c2d1c027', '40dbbfcb468ac270', '40b21c73e747181e', '40c397530ade705e', '409992bb2617188e', '40a227bd527db945', '4077b2e7e49b93e0', '407a57eb4ba95737', '405131927b6302a2', '405171927b6302a2', '3fd59959889f6a94', '3fd59959889f6a94', '3fd59959889f6a94', '3fc8ef412bc97ed0', 'bff9bbb6a840713b', 'bfd0466f93d67602', 'bfc3c0125ae01f37', '0000000000000000', '3ff0000000000000', '4000000000000000', '3fe0000000000000', '3fb999999999999a', '3f947ae147ae147c', '3ff051eb851eb852', '3fd6acd5fa3cdc68', '4000000000000000', '3fe6acd5fa3cdc68', '3ff028c1d959b062', '3fe673a4da28a8a3', 'bfe673a4da28a8a3', '3ff6a09e667f3bcd', 'bfdfc065624d2d8c', '3fe845f7868b2493'), [{'call': 'Q1', 'probability_bits': '3ee4f8a7ca7d0000', 'q_bits': 'bfdfffd60eb06b06', 'branch': 'TAIL_LE_FIVE', 'result_bits': 'c0110f401e1a302e'}, {'call': 'Q2', 'probability_bits': '3fe43a5c9bee2176', 'q_bits': '3fc0e9726fb885d8', 'branch': 'CENTRAL', 'result_bits': '3fd59959889f6a94'}], '3fe673a4da28a8a3', '3ff845f7868b2493', 'bfdfc065624d2d8c'), ('lower_deep_tail', {'complete_material_trial_sharpes': [-0.1, 0.0, 0.1, 0.2, 0.3], 'effective_independent_trial_count': 1.0000000000000002, 'candidate_estimated_sharpe': 0.1, 'candidate_independent_equivalent_observations': 5, 'candidate_sample_skewness': 0.0, 'candidate_sample_non_excess_kurtosis': 3.0}, {'deflated_sharpe_ratio': 0.8466682258462469, 'expected_maximum_sharpe_threshold': -0.4124002055514484, 'trial_mean_sharpe': 0.1, 'trial_sharpe_variance': 0.025}, ('3fe0000000000000', '3fb999999999999a', '3fe0000000000000', '3fb999999999999a', 'bfc999999999999a', '3fa47ae147ae147c', 'bfb999999999999a', '3f847ae147ae147c', '0000000000000000', '0000000000000000', '3fb999999999999a', '3f847ae147ae147c', '3fc9999999999999', '3fa47ae147ae147a', '3fb999999999999a', '3f9999999999999a', '3fc43d136248490f', '3fdb0ee6072093ce', '3feffffffffffffe', '3cb0000000000000', 'bfdffffffffffffc', 'c04205966f2b4f12', '404205966f2b4f12', '401803b9557bec5b', '3ff00ee555efb16c', '3e8b14939cb3d406', '3efca4eff39347d2', '3efcbf9ad80c0efd', '3f54cf1773a28381', '3f54e276ebeb417e', '3f9c796887fa02ff', '3f9c93eae608a487', '3fd4c417dfb2e017', '3fd4d76d1ab5248a', '4000e240c66676b4', '4000f1f8c0020ef5', '401e53e6ce88577e', '401e7022ec388a88', '402c88ea56bbb7d7', '3ce27ae4665d55f8', '3e831446fbdf72fa', '3e83260a32ad56fc', '3ef382785dc8cf6d', '3ef394a22b3f021c', '3f4a6561a8f7bde8', '3f4a7df4b7375ef0', '3f900f6c3ec45e0c', '3f901e5ff07b13be', '3fc38ab71643a673', '3fc39ce890c93db4', '3fe8190d73fa26ec', '3fe82f7cc7be46a3', '3ffc17be63df2352', '40204074bdbf8864', 'c0204074bdbf8864', 'c0204074bdbf8864', 'c0204074bdbf8864', 'c00b7be70c24af7f', '4005bf0a8b14576a', '3fd78b56362cef37', '3fe43a54e4e98864', '3fc0e95393a62190', '3f91dff1bb2d1ae0', '3fc4e2ba1a85e1c3', '407996795543fe21', '40e085ff5dd8cde0', '40b591a41d793ca5', '40f1c536978f22ea', '40c73254929f7e1c', '40ec38d3ab4354b1', '40c26b79c3a63333', '40d69ea9487a8d28', '40ad86dbcba7f72c', '40b677052e58ebc9', '408d531ceff76c49', '4090be1f895efe92', '4065dae7a71ac4d6', '4066474b0b954094', '40378c2d9fd98e07', '408aa66c3405dbf0', '40dce378de51dd56', '40b2dada12b5882f', '40e58cd7ecbba5c4', '40bc216dfae1bb77', '40dbbfce548ec144', '40b21c7cf7eda519', '40c397579331b6dc', '409992cb0cd12eb2', '40a227c545dac457', '4077b2fb8639fee7', '407a57feed47c23e', '405131a602081e1b', '405171a602081e1b', '3fd5993097258196', '3fd5993097258196', '3fd5993097258196', '3fc8ef11e7a47f7b', 'c009ecf5edaa6787', 'bfe065951da9d429', 'bfda64c3d4ed41ec', '0000000000000000', '3ff0000000000000', '4000000000000000', '3fe0000000000000', '3fa999999999999a', '3f747ae147ae147c', '3ff0147ae147ae14', '3fe065951da9d429', '4000000000000000', '3ff065951da9d429', '3ff00a3a2bdeac9b', '3ff05b20b20b7eda', 'bff05b20b20b7eda', '3ff6a09e667f3bcd', 'bfe7217e286e2075', '3feb17e7f6924d99'), [{'call': 'Q1', 'probability_bits': '3cb0000000000000', 'q_bits': 'bfdffffffffffffc', 'branch': 'TAIL_GT_FIVE', 'result_bits': 'c0204074bdbf8864'}, {'call': 'Q2', 'probability_bits': '3fe43a54e4e98864', 'q_bits': '3fc0e95393a62190', 'branch': 'CENTRAL', 'result_bits': '3fd5993097258196'}], '3ff05b20b20b7eda', '3ffb17e7f6924d99', 'bfe7217e286e2075'), ('zero_variance_both_quantiles', {'complete_material_trial_sharpes': [0.1, 0.1, 0.1, 0.1, 0.1], 'effective_independent_trial_count': 1.5, 'candidate_estimated_sharpe': 0.1, 'candidate_independent_equivalent_observations': 5, 'candidate_sample_skewness': 0.0, 'candidate_sample_non_excess_kurtosis': 3.0}, {'deflated_sharpe_ratio': 0.5, 'expected_maximum_sharpe_threshold': 0.1, 'trial_mean_sharpe': 0.1, 'trial_sharpe_variance': 0.0}, ('3fe0000000000000', '3fb999999999999a', '3fe0000000000000', '3fb999999999999a', '0000000000000000', '0000000000000000', '0000000000000000', '0000000000000000', '0000000000000000', '0000000000000000', '0000000000000000', '0000000000000000', '0000000000000000', '0000000000000000', '0000000000000000', '0000000000000000', '0000000000000000', '3fdb0ee6072093ce', '3fe5555555555555', '3fd5555555555556', 'bfc5555555555554', '3f9c71c71c71c719', '3fc3907f6e5d4c3c', '4077f818c82f973f', '40e082c29cbea512', '40b43063717114a8', '40f1af228ccea06a', '40c59fae16460b8d', '40ebd42a0c2cf80d', '40c103a28672d167', '40d5eabda9e0dc42', '40aaccb073230681', '40b519ef82167374', '4089cd5de577e5a4', '408df680083e7680', '406251a896ad040b', '4062be0bfb277fc9', 'c038fd654edf550a', '4088f6d79fd5d044', '40dcd5fc39b05cf8', '40b1a14385f8fb67', '40e565a51b24142b', '40ba29f1489537f4', '40db41ef27fba063', '40b0aa3b3fa098e3', '40c2de36b70b30c1', '409712472bc4b934', '40a0e78355548998', '4074ab9635910aab', '407750999c9ece02', '404c8245811388b5', '404d0245811388b5', 'bfdb91093bfdfa27', 'bfdb91093bfdfa27', 'bfdb91093bfdfa27', 'bfc74f35673eb3c2', '40104f47e84f418f', '3fcf6472f2e6944a', '3fe826e343465aee', '3fd04dc6868cb5dc', '3fb09d071d87bc94', '3fbda069864f4daa', '407225f900555801', '40e0771e5d2ef094', '40ae7cfad0776755', '40f160042c3b4a5b', '40c0161d28edb5a8', '40ea71c5d0d6e294', '40b87bab56a5fa6d', '40d387d73c50f22a', '40a21502aa8a6a29', '40b0be189dca2548', '407f00680034de8e', '4083a95622e10022', '405234059472c208', '40530ccc5d67b984', '40336966537cf8a6', '4082e6dab4af91fa', '40dca57c52572b06', '40aa85928f7697ad', '40e4d9d5d35c5e39', '40b34defb6f5fc8a', '40d98aeec393d188', '40a7a5f346245f86', '40c07295e8c3fc31', '408e74960b03d591', '4099f70a846644c4', '40680a0a5c28050a', '406d54112a438bb7', '403b27349b1191a0', '403c27349b1191a0', '3fe6106b7a2b2d76', '3fe6106b7a2b2d76', '3fe6106b7a2b2d76', '3fd978b67b4dedbf', '3fcba2378f5d27bc', '0000000000000000', '3fb999999999999a', '0000000000000000', '3ff0000000000000', '4000000000000000', '3fe0000000000000', '3fa999999999999a', '3f747ae147ae147c', '3ff0147ae147ae14', '0000000000000000', '4000000000000000', '0000000000000000', '3ff00a3a2bdeac9b', '0000000000000000', '0000000000000000', '3ff6a09e667f3bcd', '0000000000000000', '3fe0000000000000'), [{'call': 'Q1', 'probability_bits': '3fd5555555555556', 'q_bits': 'bfc5555555555554', 'branch': 'CENTRAL', 'result_bits': 'bfdb91093bfdfa27'}, {'call': 'Q2', 'probability_bits': '3fe826e343465aee', 'q_bits': '3fd04dc6868cb5dc', 'branch': 'CENTRAL', 'result_bits': '3fe6106b7a2b2d76'}], '0000000000000000', '3ff0000000000000', '0000000000000000'), ('derived_negative_zero_score', {'complete_material_trial_sharpes': [0.0, 0.0], 'effective_independent_trial_count': 1.5, 'candidate_estimated_sharpe': -0.0, 'candidate_independent_equivalent_observations': 5, 'candidate_sample_skewness': 0.0, 'candidate_sample_non_excess_kurtosis': 3.0}, {'deflated_sharpe_ratio': 0.5, 'expected_maximum_sharpe_threshold': 0.0, 'trial_mean_sharpe': 0.0, 'trial_sharpe_variance': 0.0}, ('0000000000000000', '0000000000000000', '0000000000000000', '0000000000000000', '0000000000000000', '0000000000000000', '0000000000000000', '0000000000000000', '0000000000000000', '0000000000000000', '0000000000000000', '3fdb0ee6072093ce', '3fe5555555555555', '3fd5555555555556', 'bfc5555555555554', '3f9c71c71c71c719', '3fc3907f6e5d4c3c', '4077f818c82f973f', '40e082c29cbea512', '40b43063717114a8', '40f1af228ccea06a', '40c59fae16460b8d', '40ebd42a0c2cf80d', '40c103a28672d167', '40d5eabda9e0dc42', '40aaccb073230681', '40b519ef82167374', '4089cd5de577e5a4', '408df680083e7680', '406251a896ad040b', '4062be0bfb277fc9', 'c038fd654edf550a', '4088f6d79fd5d044', '40dcd5fc39b05cf8', '40b1a14385f8fb67', '40e565a51b24142b', '40ba29f1489537f4', '40db41ef27fba063', '40b0aa3b3fa098e3', '40c2de36b70b30c1', '409712472bc4b934', '40a0e78355548998', '4074ab9635910aab', '407750999c9ece02', '404c8245811388b5', '404d0245811388b5', 'bfdb91093bfdfa27', 'bfdb91093bfdfa27', 'bfdb91093bfdfa27', 'bfc74f35673eb3c2', '40104f47e84f418f', '3fcf6472f2e6944a', '3fe826e343465aee', '3fd04dc6868cb5dc', '3fb09d071d87bc94', '3fbda069864f4daa', '407225f900555801', '40e0771e5d2ef094', '40ae7cfad0776755', '40f160042c3b4a5b', '40c0161d28edb5a8', '40ea71c5d0d6e294', '40b87bab56a5fa6d', '40d387d73c50f22a', '40a21502aa8a6a29', '40b0be189dca2548', '407f00680034de8e', '4083a95622e10022', '405234059472c208', '40530ccc5d67b984', '40336966537cf8a6', '4082e6dab4af91fa', '40dca57c52572b06', '40aa85928f7697ad', '40e4d9d5d35c5e39', '40b34defb6f5fc8a', '40d98aeec393d188', '40a7a5f346245f86', '40c07295e8c3fc31', '408e74960b03d591', '4099f70a846644c4', '40680a0a5c28050a', '406d54112a438bb7', '403b27349b1191a0', '403c27349b1191a0', '3fe6106b7a2b2d76', '3fe6106b7a2b2d76', '3fe6106b7a2b2d76', '3fd978b67b4dedbf', '3fcba2378f5d27bc', '0000000000000000', '0000000000000000', '8000000000000000', '3ff0000000000000', '4000000000000000', '3fe0000000000000', '8000000000000000', '0000000000000000', '3ff0000000000000', '8000000000000000', '4000000000000000', '8000000000000000', '3ff0000000000000', '8000000000000000', '0000000000000000', '3ff6a09e667f3bcd', '0000000000000000', '3fe0000000000000'), [{'call': 'Q1', 'probability_bits': '3fd5555555555556', 'q_bits': 'bfc5555555555554', 'branch': 'CENTRAL', 'result_bits': 'bfdb91093bfdfa27'}, {'call': 'Q2', 'probability_bits': '3fe826e343465aee', 'q_bits': '3fd04dc6868cb5dc', 'branch': 'CENTRAL', 'result_bits': '3fe6106b7a2b2d76'}], '8000000000000000', '3ff0000000000000', '0000000000000000'), ('nonzero_candidate_moments', {'complete_material_trial_sharpes': [-0.1, 0.0, 0.1, 0.2, 0.3], 'effective_independent_trial_count': 2.0, 'candidate_estimated_sharpe': 0.25, 'candidate_independent_equivalent_observations': 9, 'candidate_sample_skewness': 0.5, 'candidate_sample_non_excess_kurtosis': 4.0}, {'deflated_sharpe_ratio': 0.5791757147123929, 'expected_maximum_sharpe_threshold': 0.18218053569858234, 'trial_mean_sharpe': 0.1, 'trial_sharpe_variance': 0.025}, ('3fe0000000000000', '3fb999999999999a', '3fe0000000000000', '3fb999999999999a', 'bfc999999999999a', '3fa47ae147ae147c', 'bfb999999999999a', '3f847ae147ae147c', '0000000000000000', '0000000000000000', '3fb999999999999a', '3f847ae147ae147c', '3fc9999999999999', '3fa47ae147ae147a', '3fb999999999999a', '3f9999999999999a', '3fc43d136248490f', '3fdb0ee6072093ce', '3fe0000000000000', '3fe0000000000000', '0000000000000000', '0000000000000000', '3fc71eb851eb851f', '407c533e6f2f0d1a', '40e08b78e80ca3fe', '40b7e841e8e94e40', '40f1eaa074462404', '40c9e3acf9ef97e2', '40ece529c5175b22', '40c4e0734c7a7986', '40d7d9260ce4b052', '40b13af84a986d79', '40b8ee8f931d5dac', '4092036673e3efd7', '409417f785473845', '406d09083a2fdf64', '406d756b9eaa5b22', '0000000000000000', '408d804922308bb0', '40dcfa47c5c332d4', '40b4efb522b930e2', '40e5cf734ebc1ada', '40bf8415fabb54e2', '40dc98785485279e', '40b4a90a23773e8b', '40c4dd9e28f68395', '409e26a342df17bd', '40a471b160e1b8dc', '407d8aafabfe7d0b', '408017d989862031', '4057412ed23df8c2', '4057812ed23df8c2', '0000000000000000', '0000000000000000', '0000000000000000', '0000000000000000', '4015bf0a8b145769', '3fc78b56362cef38', '3fea1d2a7274c432', '3fd43a54e4e98864', '3fb992a8e585e276', '3fb4aac7be5127c8', '406951ee7a2b010d', '40e06c2459a870e5', '40a5367776a6c1e2', '40f115d0116cc52f', '40b611a12306a29a', '40e92e72aafc497d', '40b0436b9aa6c73d', '40d179c74d51255e', '409692c130b8812e', '40aab08f296620fd', '40713cca0b220ebf', '40798f0e50af3076', '404081d0781d5d9e', '4042335e0a074c95', '402702905380d215', '407a5f08dfc817b5', '40dc77c1a030ced5', '40a262c6eacce0ed', '40e457a91911c2cd', '40aa46b4b83fde69', '40d800496cde4e33', '409f008a7548fad9', '40bcd254cbc80755', '40829d464940de35', '40940b62a384c916', '4059e42e80770ec7', '40623c1e0e570e11', '40278dc7f5e1637e', '40298dc7f5e1637e', '3fecd081f6c50af8', '3fecd081f6c50af8', '3fecd081f6c50af8', '3fe0a1d5f5b36765', '3fe0a1d5f5b36765', '3fb509c8993173b3', '3fc751b1196586a6', '3fc0000000000000', '3fec000000000000', '4008000000000000', '3fe8000000000000', '3fc8000000000000', '3fa8000000000000', '3fed800000000000', '3fb15c9dcd34f2b4', '4006a09e667f3bcd', '3fc88da305fba7a2', '3feeb97e455b9edb', '3fc9928fcad91576', 'bfc9928fcad91576', '3ff6a09e667f3bcd', 'bfc2151e3ffa4d87', '3fe2889b822a780b'), [{'call': 'Q1', 'probability_bits': '3fe0000000000000', 'q_bits': '0000000000000000', 'branch': 'CENTRAL', 'result_bits': '0000000000000000'}, {'call': 'Q2', 'probability_bits': '3fea1d2a7274c432', 'q_bits': '3fd43a54e4e98864', 'branch': 'CENTRAL', 'result_bits': '3fecd081f6c50af8'}], '3fc9928fcad91576', '3ff2889b822a780b', 'bfc2151e3ffa4d87'))
    def bits(value): return struct.pack(">d", value).hex()
    def unpack(value): return struct.unpack(">d", bytes.fromhex(value))[0]
    def run(selected, work, *, inputs=None, raw=None, expected=None, projected=None):
        return IndependentEvidenceReviewV1._bounded_review_deflated_sharpe_v1(
            deterministic_json(selected[1] if inputs is None else inputs).encode(),
            deterministic_json(selected[2] if raw is None else raw).encode(),
            deterministic_json(selected[2] if expected is None else expected).encode(),
            selected[2]["deflated_sharpe_ratio"] if projected is None else projected, work=work)
    def forbidden(*args, **kwargs):
        raise AssertionError("independent DSR proof called original formula, NormalDist or native transcendental/fsum/pow")
    positives = []
    with ExitStack() as stack:
        for name in ("compute_math_18_deflated_sharpe_ratio", "_v34_probabilistic_sharpe", "_v34_mean", "_v34_sample_variance"):
            stack.enter_context(patch.object(formulas, name, forbidden))
        for name in ("cdf", "inv_cdf"):
            stack.enter_context(patch.object(statistics.NormalDist, name, forbidden))
        stack.enter_context(patch.object(statistics, "_normal_dist_inv_cdf", forbidden))
        for name in ("sqrt", "log", "erf", "erfc", "exp", "fsum", "pow"):
            stack.enter_context(patch.object(math, name, forbidden))
        for selected in cases:
            work = _EvidenceNumericalWorkV1(limits, retained_input_capacity=0)
            first = run(selected, work);prefix = dict(work.consumed)
            second = run(selected, work)
            assert first == second and work.state == "OPEN"
            assert first["cell_candidates"] == selected[3] and 108 <= len(first["cell_candidates"]) <= 116
            assert len(first["inverse_certificates"]) == 2
            for actual, original in zip(first["inverse_certificates"], selected[4], strict=True):
                assert {key: actual[key] for key in original} == original
                assert actual["interpretation"] == "DERIVED_AS241_SOURCE_MODEL_NOT_EXACT_QUANTILE"
            tails = sum(value["branch"] != "CENTRAL" for value in selected[4])
            assert len(first["log_certificates"]) == tails
            for certificate in first["log_certificates"]:
                candidate = unpack(certificate["candidate_bits"])
                lower = Fraction(certificate["lower_numerator"], 2**128)
                upper = Fraction(certificate["upper_numerator"], 2**128)
                cell_lower = (Fraction(math.nextafter(candidate, -math.inf)) + Fraction(candidate)) / 2
                cell_upper = (Fraction(candidate) + Fraction(math.nextafter(candidate, math.inf))) / 2
                assert cell_lower < lower <= upper < cell_upper and upper < 0
                assert first["cell_candidates"][certificate["position"]] == certificate["candidate_bits"]
            assert prefix["input_values"] == len(selected[1]["complete_material_trial_sharpes"]) + 14
            assert prefix["log_series_terms"] == 128 * tails
            assert prefix["square_roots"] == 4 + tails + (selected[2]["trial_sharpe_variance"] != 0.0)
            assert all(prefix[key] == 0 for key in ("random_draws", "decimal_constructions", "retained_decimal_inputs"))
            assert first["summary"]["score_bits"] == selected[5]
            assert first["summary"]["probability_bits"] == bits(selected[2]["deflated_sharpe_ratio"])
            assert first["erfc_enclosure"]["derived_erfc_bits"] == selected[6]
            assert first["erfc_enclosure"]["argument_bits"] == selected[7]
            fragments = [dict(position=index, candidate=value) for index, value in enumerate(first["cell_candidates"])]
            fragments += list(first["inverse_certificates"]) + list(first["log_certificates"]) + [first["erfc_enclosure"], first["summary"]]
            charged = sum(len(deterministic_json(value).encode()) for value in fragments + [first])
            assert charged == prefix["serialized_bytes"] and work.consumed["serialized_bytes"] == 2 * charged <= 65536
            positives.append(dict(case=selected[0], proof=first, first_consumption=prefix, cumulative_consumption=dict(work.consumed), repetitions=2))
    base = cases[0]
    mutations = (
        ("boolean_support", "inputs", dict(candidate_independent_equivalent_observations=True)),
        ("fractional_support", "inputs", dict(candidate_independent_equivalent_observations=2.5)),
        ("one_support", "inputs", dict(candidate_independent_equivalent_observations=1)),
        ("support_above_declared_profile", "inputs", dict(candidate_independent_equivalent_observations=9007199254740993)),
        ("one_trial", "inputs", dict(complete_material_trial_sharpes=[.1])),
        ("empty_trials", "inputs", dict(complete_material_trial_sharpes=[])),
        ("trial_capacity", "inputs", dict(complete_material_trial_sharpes=[.1]*6)),
        ("boolean_trial", "inputs", dict(complete_material_trial_sharpes=[True,0.0,.1,.2,.3])),
        ("integer_trial", "inputs", dict(complete_material_trial_sharpes=[0,0.0,.1,.2,.3])),
        ("non_scalar_trial", "inputs", dict(complete_material_trial_sharpes=[[0.0],0.0,.1,.2,.3])),
        ("trial_outside_declared_domain", "inputs", dict(complete_material_trial_sharpes=[-1.0000000000000002,0.0,.1,.2,.3])),
        ("truncated_values_original_raw", "inputs", dict(complete_material_trial_sharpes=[-.1,0.0,.1,.2])),
        ("one_effective_trial", "inputs", dict(effective_independent_trial_count=1.0)),
        ("excess_effective_trials", "inputs", dict(effective_independent_trial_count=5.000000000000001)),
        ("boolean_effective_trials", "inputs", dict(effective_independent_trial_count=True)),
        ("string_effective_trials", "inputs", dict(effective_independent_trial_count="1.5")),
        ("boolean_estimate", "inputs", dict(candidate_estimated_sharpe=True)),
        ("excess_for_nonexcess", "inputs", dict(candidate_sample_non_excess_kurtosis=0.0)),
        ("zero_denominator", "inputs", dict(candidate_estimated_sharpe=1.0,candidate_sample_skewness=1.0,candidate_sample_non_excess_kurtosis=1.0)),
        ("negative_denominator", "inputs", dict(candidate_estimated_sharpe=1.0,candidate_sample_skewness=2.0,candidate_sample_non_excess_kurtosis=1.0)),
        ("erfc_argument_region", "inputs", dict(candidate_estimated_sharpe=4.0,candidate_sample_non_excess_kurtosis=1.0)),
        ("cdf_ulp", "raw", dict(deflated_sharpe_ratio=math.nextafter(base[2]["deflated_sharpe_ratio"], 1.0))),
        ("threshold_ulp", "raw", dict(expected_maximum_sharpe_threshold=math.nextafter(base[2]["expected_maximum_sharpe_threshold"],1.0))),
        ("mean_ulp", "raw", dict(trial_mean_sharpe=math.nextafter(.1,1.0))),
        ("variance_ulp", "raw", dict(trial_sharpe_variance=math.nextafter(.025,1.0))),
        ("wrong_expectation", "expected", dict(trial_mean_sharpe=0.0)),
        ("boolean_probability", "raw", dict(deflated_sharpe_ratio=True)),
        ("integer_variance", "raw", dict(trial_sharpe_variance=0)),
    )
    denials = []
    def deny(name, selected, changes, arguments):
        work = _EvidenceNumericalWorkV1(dict(limits, **changes), retained_input_capacity=0)
        with pytest.raises(ComputationControlPlaneError): run(selected, work, **arguments)
        assert work.state == "FAILED"
        consumed = dict(work.consumed)
        with pytest.raises(ComputationControlPlaneError, match="LP03_NUMERICAL_WORK_NOT_OPEN"): run(base, work)
        assert dict(work.consumed) == consumed
        denials.append(dict(case=name, failure=work.failure, consumed=consumed))
    for name, field, changes in mutations:
        value = dict(base[1] if field == "inputs" else base[2], **changes)
        deny(name, base, {}, {field: value})
    for name, selected, changes, arguments in (
        ("projection_ulp", base, {}, dict(projected=math.nextafter(base[2]["deflated_sharpe_ratio"],1.0))),
        ("projection_boolean", base, {}, dict(projected=True)),
        ("coherent_wrong_outputs", base, {}, dict(raw=dict(base[2],deflated_sharpe_ratio=.5),expected=dict(base[2],deflated_sharpe_ratio=.5),projected=.5)),
        ("signed_zero_threshold", cases[7], {}, dict(raw=dict(cases[7][2],expected_maximum_sharpe_threshold=-0.0))),
        ("unknown_input_field", base, {}, dict(inputs=dict(base[1],group_count=5))),
        ("missing_support", base, {}, dict(inputs={k:v for k,v in base[1].items() if k!='candidate_independent_equivalent_observations'})),
        ("zero_budget", base, dict(max_serialized_bytes=0), {}),
        ("complete_bytes", base, dict(max_serialized_bytes=10000), {}),
        ("work_bits", base, dict(max_work_bits=1074), {}),
        ("input_bits", base, dict(max_input_bits=1), {}),
        ("transcendental_work_bits", cases[4], dict(max_work_bits=2048), {}),
    ): deny(name, selected, changes, arguments)
    work = _EvidenceNumericalWorkV1(limits, retained_input_capacity=0);completed = 0
    for _ in range(32):
        before = dict(work.consumed)
        try: run(base, work)
        except ComputationControlPlaneError: break
        completed += 1
    assert 1 <= completed < 32 and work.state == "FAILED" and before["serialized_bytes"] > 0
    failed = dict(work.consumed)
    with pytest.raises(ComputationControlPlaneError, match="LP03_NUMERICAL_WORK_NOT_OPEN"): run(base, work)
    assert dict(work.consumed) == failed
    print("LP03_DEFLATED_SHARPE_NUMERICAL_QUALIFICATION=" + deterministic_json(dict(math_id="MATH-18", positives=positives,
        denials=denials, cumulative_exhaustion=dict(completed=completed,before=before,failed=failed,failure=work.failure),
        scope="PURE_ORDERED_DSR_SOURCE_MODEL_ONLY_NO_COMPLETE_LEDGER_SUPPORT_OR_NATIVE_ROUTE_QUALIFICATION")))


def _assert_lp03_fold_topology_original_rosters():
    import json
    import pytest
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.evidence import IndependentEvidenceReviewV1
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.parameter_policy import _EvidenceNumericalWorkV1
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.serialization import deterministic_json
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import ComputationControlPlaneError

    # Independent endpoint sweep, stable grouping and exact complementary covers.
    vectors=json.loads('[["MATH-20",{"embargo_duration":0.5,"folds":3,"sample_intervals":[{"end":9.0,"sample_id":"x5","start":8.0},{"end":4.0,"sample_id":"x2","start":2.0},{"end":2.0,"sample_id":"x0","start":0.0},{"end":6.0,"sample_id":"x3","start":4.5},{"end":3.0,"sample_id":"x1","start":1.0},{"end":7.0,"sample_id":"x4","start":6.0}]},{"embargo_basis":"TIME_DURATION_AFTER_MERGED_TEST_INTERVAL","folds":[{"embargoed_sample_ids":[],"fold_id":0,"merged_test_intervals":[[0.0,3.0]],"purged_sample_ids":["x2"],"test_sample_ids":["x0","x1"],"train_sample_ids":["x3","x4","x5"]},{"embargoed_sample_ids":["x4"],"fold_id":1,"merged_test_intervals":[[2.0,4.0],[4.5,6.0]],"purged_sample_ids":["x1"],"test_sample_ids":["x2","x3"],"train_sample_ids":["x0","x5"]},{"embargoed_sample_ids":[],"fold_id":2,"merged_test_intervals":[[6.0,7.0],[8.0,9.0]],"purged_sample_ids":[],"test_sample_ids":["x4","x5"],"train_sample_ids":["x0","x1","x2","x3"]}],"interval_semantics":"HALF_OPEN_START_INCLUSIVE_END_EXCLUSIVE","ordered_sample_ids":["x0","x1","x2","x3","x4","x5"]}],["MATH-21",{"N_groups":4,"aggregation_rule":"ALL_PATHS_NO_CHERRY_PICKING","embargo_duration":0.5,"k_test_groups":2,"sample_intervals":[{"end":9.0,"sample_id":"x5","start":8.0},{"end":4.0,"sample_id":"x2","start":2.0},{"end":2.0,"sample_id":"x0","start":0.0},{"end":6.0,"sample_id":"x3","start":4.5},{"end":3.0,"sample_id":"x1","start":1.0},{"end":7.0,"sample_id":"x4","start":6.0}]},{"N_groups":4,"aggregation_rule":"ALL_PATHS_NO_CHERRY_PICKING","expected_path_count":3,"k_test_groups":2,"path_count":3,"paths":[{"path_id":0,"split_ids":[0,5],"test_group_partition":[[0,1],[2,3]]},{"path_id":1,"split_ids":[1,4],"test_group_partition":[[0,2],[1,3]]},{"path_id":2,"split_ids":[2,3],"test_group_partition":[[0,3],[1,2]]}],"split_count":6,"splits":[{"embargoed_sample_ids":["x4"],"merged_test_intervals":[[0.0,4.0],[4.5,6.0]],"purged_sample_ids":[],"split_id":0,"test_groups":[0,1],"test_sample_ids":["x0","x1","x2","x3"],"train_sample_ids":["x5"]},{"embargoed_sample_ids":[],"merged_test_intervals":[[0.0,3.0],[6.0,7.0]],"purged_sample_ids":["x2"],"split_id":1,"test_groups":[0,2],"test_sample_ids":["x0","x1","x4"],"train_sample_ids":["x3","x5"]},{"embargoed_sample_ids":[],"merged_test_intervals":[[0.0,3.0],[8.0,9.0]],"purged_sample_ids":["x2"],"split_id":2,"test_groups":[0,3],"test_sample_ids":["x0","x1","x5"],"train_sample_ids":["x3","x4"]},{"embargoed_sample_ids":[],"merged_test_intervals":[[2.0,4.0],[4.5,7.0]],"purged_sample_ids":["x1"],"split_id":3,"test_groups":[1,2],"test_sample_ids":["x2","x3","x4"],"train_sample_ids":["x0","x5"]},{"embargoed_sample_ids":["x4"],"merged_test_intervals":[[2.0,4.0],[4.5,6.0],[8.0,9.0]],"purged_sample_ids":["x1"],"split_id":4,"test_groups":[1,3],"test_sample_ids":["x2","x3","x5"],"train_sample_ids":["x0"]},{"embargoed_sample_ids":[],"merged_test_intervals":[[6.0,7.0],[8.0,9.0]],"purged_sample_ids":[],"split_id":5,"test_groups":[2,3],"test_sample_ids":["x4","x5"],"train_sample_ids":["x0","x1","x2","x3"]}]}],["MATH-20",{"embargo_duration":-0.0,"folds":2,"sample_intervals":[{"end":2.0,"sample_id":"d","start":1.0},{"end":-0.0,"sample_id":"b","start":-1.0},{"end":-1.0,"sample_id":"a","start":-2.0},{"end":1.0,"sample_id":"c","start":0.0}]},{"embargo_basis":"TIME_DURATION_AFTER_MERGED_TEST_INTERVAL","folds":[{"embargoed_sample_ids":[],"fold_id":0,"merged_test_intervals":[[-2.0,-0.0]],"purged_sample_ids":[],"test_sample_ids":["a","b"],"train_sample_ids":["c","d"]},{"embargoed_sample_ids":[],"fold_id":1,"merged_test_intervals":[[0.0,2.0]],"purged_sample_ids":[],"test_sample_ids":["c","d"],"train_sample_ids":["a","b"]}],"interval_semantics":"HALF_OPEN_START_INCLUSIVE_END_EXCLUSIVE","ordered_sample_ids":["a","b","c","d"]}]]')
    limits=dict(max_input_bits=4096,max_work_bits=65536,max_serialized_bytes=65536)
    for math_id,inputs,expected in vectors:
        work=_EvidenceNumericalWorkV1(limits,retained_input_capacity=0)
        proof=IndependentEvidenceReviewV1._bounded_review_fold_topology_v1(math_id,
            deterministic_json(inputs).encode("utf-8"),deterministic_json(expected).encode("utf-8"),work=work)
        if math_id=="MATH-20":
            assert proof["ordered_original_ids"]==tuple(expected["ordered_sample_ids"])
            assert len(proof["split_assignments"])==len(expected["folds"])
        else:
            assert proof["ordered_original_ids"]==tuple("x"+str(index) for index in range(6))
            assert len(proof["split_assignments"])==len(expected["splits"])
        if len(inputs["sample_intervals"])==4:
            assert proof["split_assignments"][0]["embargo_boundary_bits"]==("8000000000000000",)
        assert proof["held_out_score_coverage"]=="TOPOLOGY_ONLY_NO_SCORE_RECEIPTS"
        assert work.consumed["serialized_bytes"]==len(deterministic_json(proof).encode("utf-8"))
        print("LP03_FOLD_TOPOLOGY_PROOF="+deterministic_json(dict(math_id=math_id,proof=proof,counters=dict(work.consumed))))
        altered=json.loads(deterministic_json(expected))
        key="folds" if math_id=="MATH-20" else "splits"
        altered[key][0]["test_sample_ids"].reverse()
        invalid=_EvidenceNumericalWorkV1(limits,retained_input_capacity=0)
        with pytest.raises(ComputationControlPlaneError,match="LP03_FOLD_TOPOLOGY_ORIGINAL_RESULT_MISMATCH") as caught:
            IndependentEvidenceReviewV1._bounded_review_fold_topology_v1(math_id,
                deterministic_json(inputs).encode("utf-8"),deterministic_json(altered).encode("utf-8"),work=invalid)
        assert invalid.state=="FAILED"
        print("LP03_FOLD_TOPOLOGY_DENIAL="+deterministic_json(dict(math_id=math_id,
            case="test_order",diagnostic=str(caught.value),counters=dict(invalid.consumed))))


def _assert_lp03_pbo_ordered_model_proof():
    import json
    import pytest
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import ComputationControlPlaneError
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.evidence import IndependentEvidenceReviewV1
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.parameter_policy import _EvidenceNumericalWorkV1
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.serialization import deterministic_json

    # Independent Fraction series and complete ordered split enumeration.
    vectors = json.loads('{"cases":[["lexicographic_winner_and_two_way_midrank",{"S":2,"performance_matrix":[[0.5,0.5,0.0],[0.5,0.5,0.0],[0.75,0.25,0.25],[0.75,0.25,0.25]],"strategy_ids":["z","a","m"]},{"S":2,"logits":[-0.5108256237659907,0.5108256237659907],"probability_of_backtest_overfitting":0.5,"split_count":2,"splits":[{"is_winner_strategy_id":"a","logit":-0.5108256237659907,"oos_midrank_worst_1_best_n":1.5,"relative_rank":0.375,"train_groups":[0]},{"is_winner_strategy_id":"z","logit":0.5108256237659907,"oos_midrank_worst_1_best_n":2.5,"relative_rank":0.625,"train_groups":[1]}]},{"groups":[[0,1],[2,3]],"probability_bits":"3fe0000000000000","split_traces":[{"complement_bits":"3fe4000000000000","logit_bits":"bfe058aefa811452","lower_count":0,"odds_bits":"3fe3333333333333","rank_bits":"3ff8000000000000","relative_bits":"3fd8000000000000","test_rows":[2,3],"testing_means_bits":["3fe8000000000000","3fd0000000000000","3fd0000000000000"],"tie_count":2,"train_rows":[0,1],"training_means_bits":["3fe0000000000000","3fe0000000000000","0000000000000000"],"winner_column":1},{"complement_bits":"3fd8000000000000","logit_bits":"3fe058aefa811452","lower_count":1,"odds_bits":"3ffaaaaaaaaaaaab","rank_bits":"4004000000000000","relative_bits":"3fe4000000000000","test_rows":[0,1],"testing_means_bits":["3fe0000000000000","3fe0000000000000","0000000000000000"],"tie_count":2,"train_rows":[2,3],"training_means_bits":["3fe8000000000000","3fd0000000000000","3fd0000000000000"],"winner_column":0}]}],["all_tied_zero_logits_are_counted",{"S":2,"performance_matrix":[[-0.0,0.0,0.0],[0.0,-0.0,0.0]],"strategy_ids":["last","first","middle"]},{"S":2,"logits":[0.0,0.0],"probability_of_backtest_overfitting":1.0,"split_count":2,"splits":[{"is_winner_strategy_id":"first","logit":0.0,"oos_midrank_worst_1_best_n":2.0,"relative_rank":0.5,"train_groups":[0]},{"is_winner_strategy_id":"first","logit":0.0,"oos_midrank_worst_1_best_n":2.0,"relative_rank":0.5,"train_groups":[1]}]},{"groups":[[0],[1]],"probability_bits":"3ff0000000000000","split_traces":[{"complement_bits":"3fe0000000000000","logit_bits":"0000000000000000","lower_count":0,"odds_bits":"3ff0000000000000","rank_bits":"4000000000000000","relative_bits":"3fe0000000000000","test_rows":[1],"testing_means_bits":["0000000000000000","0000000000000000","0000000000000000"],"tie_count":3,"train_rows":[0],"training_means_bits":["0000000000000000","0000000000000000","0000000000000000"],"winner_column":1},{"complement_bits":"3fe0000000000000","logit_bits":"0000000000000000","lower_count":0,"odds_bits":"3ff0000000000000","rank_bits":"4000000000000000","relative_bits":"3fe0000000000000","test_rows":[0],"testing_means_bits":["0000000000000000","0000000000000000","0000000000000000"],"tie_count":3,"train_rows":[1],"training_means_bits":["0000000000000000","0000000000000000","0000000000000000"],"winner_column":1}]}],["single_declared_strategy",{"S":2,"performance_matrix":[[0.0],[-0.0]],"strategy_ids":["sole"]},{"S":2,"logits":[0.0,0.0],"probability_of_backtest_overfitting":1.0,"split_count":2,"splits":[{"is_winner_strategy_id":"sole","logit":0.0,"oos_midrank_worst_1_best_n":1.0,"relative_rank":0.5,"train_groups":[0]},{"is_winner_strategy_id":"sole","logit":0.0,"oos_midrank_worst_1_best_n":1.0,"relative_rank":0.5,"train_groups":[1]}]},{"groups":[[0],[1]],"probability_bits":"3ff0000000000000","split_traces":[{"complement_bits":"3fe0000000000000","logit_bits":"0000000000000000","lower_count":0,"odds_bits":"3ff0000000000000","rank_bits":"3ff0000000000000","relative_bits":"3fe0000000000000","test_rows":[1],"testing_means_bits":["0000000000000000"],"tie_count":1,"train_rows":[0],"training_means_bits":["0000000000000000"],"winner_column":0},{"complement_bits":"3fe0000000000000","logit_bits":"0000000000000000","lower_count":0,"odds_bits":"3ff0000000000000","rank_bits":"3ff0000000000000","relative_bits":"3fe0000000000000","test_rows":[0],"testing_means_bits":["0000000000000000"],"tie_count":1,"train_rows":[1],"training_means_bits":["0000000000000000"],"winner_column":0}]}],["six_contiguous_divisions_mixed_sign",{"S":4,"performance_matrix":[[0.25,0.5,-0.25,0.0],[0.5,0.25,-0.25,0.0],[0.5,0.0,0.25,0.75],[0.0,0.0,0.5,0.75],[0.0,0.5,0.75,0.25],[0.75,0.0,0.75,0.0],[0.25,0.75,0.0,0.25],[0.0,0.75,0.25,0.25]],"strategy_ids":["z","beta","a","delta"]},{"S":4,"logits":[-1.3862943611198906,-1.3862943611198906,-1.3862943611198906,-1.3862943611198906,-1.3862943611198906,-0.4054651081081643],"probability_of_backtest_overfitting":1.0,"split_count":6,"splits":[{"is_winner_strategy_id":"delta","logit":-1.3862943611198906,"oos_midrank_worst_1_best_n":1.0,"relative_rank":0.2,"train_groups":[0,1]},{"is_winner_strategy_id":"z","logit":-1.3862943611198906,"oos_midrank_worst_1_best_n":1.0,"relative_rank":0.2,"train_groups":[0,2]},{"is_winner_strategy_id":"beta","logit":-1.3862943611198906,"oos_midrank_worst_1_best_n":1.0,"relative_rank":0.2,"train_groups":[0,3]},{"is_winner_strategy_id":"a","logit":-1.3862943611198906,"oos_midrank_worst_1_best_n":1.0,"relative_rank":0.2,"train_groups":[1,2]},{"is_winner_strategy_id":"delta","logit":-1.3862943611198906,"oos_midrank_worst_1_best_n":1.0,"relative_rank":0.2,"train_groups":[1,3]},{"is_winner_strategy_id":"beta","logit":-0.4054651081081643,"oos_midrank_worst_1_best_n":2.0,"relative_rank":0.4,"train_groups":[2,3]}]},{"groups":[[0,1],[2,3],[4,5],[6,7]],"probability_bits":"3ff0000000000000","split_traces":[{"complement_bits":"3fe999999999999a","logit_bits":"bff62e42fefa39ef","lower_count":0,"odds_bits":"3fd0000000000000","rank_bits":"3ff0000000000000","relative_bits":"3fc999999999999a","test_rows":[4,5,6,7],"testing_means_bits":["3fd0000000000000","3fe0000000000000","3fdc000000000000","3fc8000000000000"],"tie_count":1,"train_rows":[0,1,2,3],"training_means_bits":["3fd4000000000000","3fc8000000000000","3fb0000000000000","3fd8000000000000"],"winner_column":3},{"complement_bits":"3fe999999999999a","logit_bits":"bff62e42fefa39ef","lower_count":0,"odds_bits":"3fd0000000000000","rank_bits":"3ff0000000000000","relative_bits":"3fc999999999999a","test_rows":[2,3,6,7],"testing_means_bits":["3fc8000000000000","3fd8000000000000","3fd0000000000000","3fe0000000000000"],"tie_count":1,"train_rows":[0,1,4,5],"training_means_bits":["3fd8000000000000","3fd4000000000000","3fd0000000000000","3fb0000000000000"],"winner_column":0},{"complement_bits":"3fe999999999999a","logit_bits":"bff62e42fefa39ef","lower_count":0,"odds_bits":"3fd0000000000000","rank_bits":"3ff0000000000000","relative_bits":"3fc999999999999a","test_rows":[2,3,4,5],"testing_means_bits":["3fd4000000000000","3fc0000000000000","3fe2000000000000","3fdc000000000000"],"tie_count":1,"train_rows":[0,1,6,7],"training_means_bits":["3fd0000000000000","3fe2000000000000","bfb0000000000000","3fc0000000000000"],"winner_column":1},{"complement_bits":"3fe999999999999a","logit_bits":"bff62e42fefa39ef","lower_count":0,"odds_bits":"3fd0000000000000","rank_bits":"3ff0000000000000","relative_bits":"3fc999999999999a","test_rows":[0,1,6,7],"testing_means_bits":["3fd0000000000000","3fe2000000000000","bfb0000000000000","3fc0000000000000"],"tie_count":1,"train_rows":[2,3,4,5],"training_means_bits":["3fd4000000000000","3fc0000000000000","3fe2000000000000","3fdc000000000000"],"winner_column":2},{"complement_bits":"3fe999999999999a","logit_bits":"bff62e42fefa39ef","lower_count":0,"odds_bits":"3fd0000000000000","rank_bits":"3ff0000000000000","relative_bits":"3fc999999999999a","test_rows":[0,1,4,5],"testing_means_bits":["3fd8000000000000","3fd4000000000000","3fd0000000000000","3fb0000000000000"],"tie_count":1,"train_rows":[2,3,6,7],"training_means_bits":["3fc8000000000000","3fd8000000000000","3fd0000000000000","3fe0000000000000"],"winner_column":3},{"complement_bits":"3fe3333333333333","logit_bits":"bfd9f323ecbf984a","lower_count":1,"odds_bits":"3fe5555555555556","rank_bits":"4000000000000000","relative_bits":"3fd999999999999a","test_rows":[0,1,2,3],"testing_means_bits":["3fd4000000000000","3fc8000000000000","3fb0000000000000","3fd8000000000000"],"tie_count":1,"train_rows":[4,5,6,7],"training_means_bits":["3fd0000000000000","3fe0000000000000","3fdc000000000000","3fc8000000000000"],"winner_column":1}]}],["binary64_sum_rounded_before_mean",{"S":2,"performance_matrix":[[0.5,0.5,0.25],[5.551115123125783e-17,0.0,-0.25],[0.0,0.0,-0.0],[0.5,0.5,0.5],[0.5,-0.5,0.0],[0.5,0.25,-0.5]],"strategy_ids":["z","a","m"]},{"S":2,"logits":[0.0,0.5108256237659907],"probability_of_backtest_overfitting":0.5,"split_count":2,"splits":[{"is_winner_strategy_id":"a","logit":0.0,"oos_midrank_worst_1_best_n":2.0,"relative_rank":0.5,"train_groups":[0]},{"is_winner_strategy_id":"z","logit":0.5108256237659907,"oos_midrank_worst_1_best_n":2.5,"relative_rank":0.625,"train_groups":[1]}]},{"groups":[[0,1,2],[3,4,5]],"probability_bits":"3fe0000000000000","split_traces":[{"complement_bits":"3fe0000000000000","logit_bits":"0000000000000000","lower_count":1,"odds_bits":"3ff0000000000000","rank_bits":"4000000000000000","relative_bits":"3fe0000000000000","test_rows":[3,4,5],"testing_means_bits":["3fe0000000000000","3fb5555555555555","0000000000000000"],"tie_count":1,"train_rows":[0,1,2],"training_means_bits":["3fc5555555555555","3fc5555555555555","0000000000000000"],"winner_column":1},{"complement_bits":"3fd8000000000000","logit_bits":"3fe058aefa811452","lower_count":1,"odds_bits":"3ffaaaaaaaaaaaab","rank_bits":"4004000000000000","relative_bits":"3fe4000000000000","test_rows":[0,1,2],"testing_means_bits":["3fc5555555555555","3fc5555555555555","0000000000000000"],"tie_count":2,"train_rows":[3,4,5],"training_means_bits":["3fe0000000000000","3fb5555555555555","0000000000000000"],"winner_column":0}]}]]}')["cases"]
    limits = dict(max_input_bits=4096, max_work_bits=65536, max_serialized_bytes=65536)

    def run(inputs, raw, expected, projected, work):
        return IndependentEvidenceReviewV1._bounded_review_pbo_v1(
            deterministic_json(inputs).encode("utf-8"), deterministic_json(raw).encode("utf-8"),
            deterministic_json(expected).encode("utf-8"), projected, work=work)

    for case, inputs, expected, trace in vectors:
        work = _EvidenceNumericalWorkV1(limits, retained_input_capacity=0)
        proof = run(inputs, expected, expected, expected, work)
        assert proof["probability_bits"] == trace["probability_bits"]
        assert deterministic_json(proof["contiguous_blocks"]) == deterministic_json(trace["groups"])
        for split, reference in zip(proof["splits"], trace["split_traces"], strict=True):
            for field in ("winner_column", "lower_count", "tie_count", "rank_bits", "complement_bits", "odds_bits", "logit_bits"):
                assert split[field] == reference[field]
            assert split["relative_rank_bits"] == reference["relative_bits"]
            for stage in ("training", "testing"):
                assert tuple(pair[1] for pair in split[stage + "_cells"]) == tuple(reference[stage + "_means_bits"])
            assert tuple(split["train_rows"]) == tuple(reference["train_rows"])
            assert tuple(split["test_rows"]) == tuple(reference["test_rows"])
        assert work.consumed["random_draws"] == 0
        assert work.consumed["serialized_bytes"] == len(deterministic_json(proof).encode("utf-8"))
        print("LP03_PBO_ORDERED_PROOF="+deterministic_json(dict(case=case,inputs=inputs,expected=expected,proof=proof,
            counters=dict(work.consumed))))

    _, inputs, expected, _ = vectors[0]
    swapped = dict(expected, splits=expected["splits"][::-1], logits=expected["logits"][::-1])
    wrong_result = dict(expected, probability_of_backtest_overfitting=0.0)
    for name, candidate_inputs, raw, projected, diagnostic in (
        ("wrong_block_count", dict(inputs,S=6), expected, expected, "LP03_PBO_REVIEW_COMPLETE_DOMAIN"),
        ("duplicate_strategy", dict(inputs,strategy_ids=["z","z","m"]), expected, expected, "LP03_PBO_REVIEW_STRATEGY_ROSTER"),
        ("incomplete_order", inputs, swapped, expected, "LP03_PBO_REVIEW_(GROUP_OR_WINNER|NEAREST_EVEN_CELL)"),
        ("wrong_probability", inputs, wrong_result, expected, "LP03_PBO_REVIEW_RAW_OR_PROJECTED_RECORD_MISMATCH"),
        ("scalar_projection", inputs, expected, 0.5, "LP03_PBO_REVIEW_RAW_OR_PROJECTED_RECORD_MISMATCH"),
    ):
        work = _EvidenceNumericalWorkV1(limits, retained_input_capacity=0)
        with pytest.raises(ComputationControlPlaneError, match=diagnostic) as caught:
            run(candidate_inputs, raw, expected, projected, work)
        assert work.state == "FAILED"
        print("LP03_PBO_ORDERED_DENIAL="+deterministic_json(dict(case=name,diagnostic=str(caught.value),
            counters=dict(work.consumed))))


def _assert_lp03_sharpe_projection_bounds():
    import struct
    import pytest
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.parameter_policy import _EvidenceNumericalWorkV1, _validate_evidence_sharpe_bounds_v1
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.serialization import deterministic_json
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import ComputationControlPlaneError
    inputs={
        'MATH-17':dict(estimated_sharpe=.2,reference_sharpe=.2,independent_equivalent_observations=5,sample_skewness=-0.0,sample_non_excess_kurtosis=3.0),
        'MATH-18':dict(complete_material_trial_sharpes=(-.1,0.0,.1,.2,.3),effective_independent_trial_count=2.0,candidate_estimated_sharpe=.2,
            candidate_independent_equivalent_observations=5,candidate_sample_skewness=0.0,candidate_sample_non_excess_kurtosis=3.0)}
    outputs={'MATH-17':dict(probabilistic_sharpe_ratio=.5,z_score=0.0),
        'MATH-18':dict(deflated_sharpe_ratio=.5140748733078602,expected_maximum_sharpe_threshold=.18218053569858234,trial_mean_sharpe=.1,trial_sharpe_variance=.025)}
    limits=dict(max_input_bits=4096,max_work_bits=16384,max_serialized_bytes=65536)
    def run(math_id,work,*,native=None,raw=None,lower='0',upper='1'):
        return _validate_evidence_sharpe_bounds_v1(inputs[math_id] if native is None else native,math_id=math_id,
            lower_text=lower,upper_text=upper,expected_json=deterministic_json(outputs[math_id] if raw is None else raw).encode(),work=work)
    positives=[];denials=[]
    for math_id in ('MATH-17','MATH-18'):
        work=_EvidenceNumericalWorkV1(limits,retained_input_capacity=2)
        proof=run(math_id,work)
        count='independent_equivalent_observations' if math_id=='MATH-17' else 'candidate_independent_equivalent_observations'
        assert proof['original_integer_support']==5 and proof['integer_support_field']==count
        assert dict(proof['fixed_lower'])==dict(numerator='0',denominator='1') and dict(proof['fixed_upper'])==dict(numerator='1',denominator='1')
        assert proof['bound_scope']=='PROJECTED_PSR_OR_DSR_PROBABILITY_ONLY'
        scalar_names=tuple(name for name in inputs[math_id] if name not in (count,'complete_material_trial_sharpes'))
        assert proof['scalar_input_bits_json']==deterministic_json(tuple((name,struct.pack('>d',inputs[math_id][name]).hex())for name in scalar_names))
        assert proof['complete_material_trial_bits_json']==deterministic_json(tuple(struct.pack('>d',value).hex()for value in inputs[math_id].get('complete_material_trial_sharpes',())))
        assert proof['expected_raw_bits_json']==deterministic_json(tuple((name,struct.pack('>d',value).hex())for name,value in sorted(outputs[math_id].items())))
        assert work.state=='OPEN' and work.consumed['serialized_bytes']==len(deterministic_json(proof).encode())
        assert work.consumed['retained_decimal_inputs']==2
        positives.append(dict(math_id=math_id,inputs_json=deterministic_json(inputs[math_id]),expected_json=deterministic_json(outputs[math_id]),proof=proof,consumed=dict(work.consumed)))
        print('LP03_SHARPE_PROJECTED_BOUNDS_POSITIVE_QUALIFICATION='+deterministic_json(positives[-1]))
        probability='probabilistic_sharpe_ratio' if math_id=='MATH-17' else 'deflated_sharpe_ratio'
        estimate='estimated_sharpe' if math_id=='MATH-17' else 'candidate_estimated_sharpe'
        kurtosis='sample_non_excess_kurtosis' if math_id=='MATH-17' else 'candidate_sample_non_excess_kurtosis'
        cases=[
            ('extra_input',dict(native=dict(inputs[math_id],extra=0)),'LP03_SHARPE_DECLARED_INPUT_FIELDS'),
            ('boolean_support',dict(native=dict(inputs[math_id],**{count:True})),'LP03_SHARPE_DECLARED_INPUT_DOMAIN'),
            ('float_support',dict(native=dict(inputs[math_id],**{count:5.0})),'LP03_SHARPE_DECLARED_INPUT_DOMAIN'),
            ('too_small_support',dict(native=dict(inputs[math_id],**{count:1})),'LP03_SHARPE_DECLARED_INPUT_DOMAIN'),
            ('too_wide_support',dict(native=dict(inputs[math_id],**{count:2**53+1})),'LP03_SHARPE_DECLARED_INPUT_DOMAIN'),
            ('integer_estimate',dict(native=dict(inputs[math_id],**{estimate:0})),'LP03_SHARPE_DECLARED_INPUT_DOMAIN'),
            ('nonfinite_estimate',dict(native=dict(inputs[math_id],**{estimate:float('inf')})),'LP03_SHARPE_DECLARED_INPUT_DOMAIN'),
            ('excess_kurtosis_substitution',dict(native=dict(inputs[math_id],**{kurtosis:0.0})),'LP03_SHARPE_DECLARED_INPUT_DOMAIN'),
            ('changed_lower',dict(lower='-1'),'LP03_SHARPE_DECLARED_PROBABILITY_ENCLOSURE'),
            ('changed_upper',dict(upper='2'),'LP03_SHARPE_DECLARED_PROBABILITY_ENCLOSURE'),
            ('negative_probability',dict(raw=dict(outputs[math_id],**{probability:-.1})),'LP03_SHARPE_EXPECTATION_PROBABILITY_BOUNDS'),
            ('probability_above_one',dict(raw=dict(outputs[math_id],**{probability:1.1})),'LP03_SHARPE_EXPECTATION_PROBABILITY_BOUNDS'),
        ]
        if math_id=='MATH-18':
            for name,change in (
                ('missing_material_trial',dict(complete_material_trial_sharpes=(.2,))),
                ('too_many_material_trials',dict(complete_material_trial_sharpes=(.2,)*6)),
                ('integer_material_trial',dict(complete_material_trial_sharpes=(0,.2))),
                ('trial_domain',dict(complete_material_trial_sharpes=(1.1,.2))),
                ('effective_count_one',dict(effective_independent_trial_count=1.0)),
                ('effective_count_exceeds_roster',dict(effective_independent_trial_count=6.0))):
                cases.append((name,dict(native=dict(inputs[math_id],**change)),'LP03_SHARPE_DECLARED_TRIAL_DOMAIN'))
        for name,kwargs,diagnostic in cases:
            failed=_EvidenceNumericalWorkV1(limits,retained_input_capacity=2)
            with pytest.raises(ComputationControlPlaneError,match=diagnostic):run(math_id,failed,**kwargs)
            assert failed.state=='FAILED';before=dict(failed.consumed)
            with pytest.raises(ComputationControlPlaneError,match='LP03_NUMERICAL_WORK_NOT_OPEN'):run(math_id,failed)
            assert dict(failed.consumed)==before
            denials.append(dict(math_id=math_id,case=name,failure=failed.failure,consumed=before,retry_denied_without_work=True))
            print('LP03_SHARPE_PROJECTED_BOUNDS_DENIAL_QUALIFICATION='+deterministic_json(denials[-1]))
        for name,limit,diagnostic in (('zero_bytes',0,'LP03_NUMERICAL_ZERO_BUDGET'),('finite_bytes_exhausted',512,'LP03_NUMERICAL_SERIALIZATION_EXHAUSTED')):
            failed=_EvidenceNumericalWorkV1(dict(limits,max_serialized_bytes=limit),retained_input_capacity=2)
            with pytest.raises(ComputationControlPlaneError,match=diagnostic):run(math_id,failed)
            assert failed.state=='FAILED';before=dict(failed.consumed)
            with pytest.raises(ComputationControlPlaneError,match='LP03_NUMERICAL_WORK_NOT_OPEN'):run(math_id,failed)
            assert dict(failed.consumed)==before
            denials.append(dict(math_id=math_id,case=name,failure=failed.failure,consumed=before,retry_denied_without_work=True))
            print('LP03_SHARPE_PROJECTED_BOUNDS_DENIAL_QUALIFICATION='+deterministic_json(denials[-1]))
        # The original retained-input capacity is cumulative across calls.
        before=dict(work.consumed)
        with pytest.raises(ComputationControlPlaneError,match='LP03_NUMERICAL_RETAINED_INPUT_CAPACITY_EXHAUSTED'):run(math_id,work)
        after=dict(work.consumed)
        assert work.state=='FAILED' and after['serialized_bytes']==before['serialized_bytes'] and after['retained_decimal_inputs']==2
        assert after['decimal_parse_attempts']==before['decimal_parse_attempts']+1
        with pytest.raises(ComputationControlPlaneError,match='LP03_NUMERICAL_WORK_NOT_OPEN'):run(math_id,work)
        assert dict(work.consumed)==after
        denials.append(dict(math_id=math_id,case='original_capacity_reuse',failure=work.failure,consumed=after,retry_denied_without_work=True))
        print('LP03_SHARPE_PROJECTED_BOUNDS_DENIAL_QUALIFICATION='+deterministic_json(denials[-1]))
    print('LP03_SHARPE_PROJECTED_BOUNDS_QUALIFICATION='+deterministic_json(dict(positives=positives,denials=denials,
        scope='PROJECTED_PROBABILITY_CODOMAIN_ONLY; ARITHMETIC_MODEL_SOURCE_CUSTODY_GRANTS_AND_STATISTICAL_SUPPORT_REQUIRE_SEPARATE_CHECKS')))
