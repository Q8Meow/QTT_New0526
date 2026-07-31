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
