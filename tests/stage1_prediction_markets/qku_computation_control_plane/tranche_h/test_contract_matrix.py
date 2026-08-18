from __future__ import annotations

from dataclasses import replace
import json

import pytest

from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import (
    ContractValidationError,
    ReasonCode,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.models import (
    NO_EFFECTS_V1,
    ST12HControlCaseV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.receipts import (
    serialize_st12h_contract_v1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.validation import (
    ST12H_CONTROL_CASES,
    ST12H_SEMANTIC_TEST_IDENTITIES,
    validate_st12h_control_case_v1,
    validate_st12h_serialized_contracts_v1,
)
from tools.independent_validate_qku_computation_control_plane import (
    _exercise_st12h_grouped_defect_injections_v1,
)


def _domain_cases(domain: str) -> tuple[ST12HControlCaseV1, ...]:
    return tuple(case for case in ST12H_CONTROL_CASES if case.domain == domain)


def _assert_certified_control(case: ST12HControlCaseV1) -> None:
    receipt = validate_st12h_control_case_v1(case)
    assert receipt.case_id == case.case_id
    assert receipt.terminal_state == case.expected_terminal_state
    assert receipt.reason_code_or_none is case.expected_reason_code
    assert receipt.no_effect_flags is NO_EFFECTS_V1
    assert tuple(case.required_receipt_fields)
    payload_names = next(
        field
        for field in receipt.control_payload.fields
        if field.name == "required_receipt_fields"
    )
    assert payload_names.value == ",".join(case.required_receipt_fields)
    assertion_values = {
        field.name: field.value for field in receipt.assertion_results.fields
    }
    assert assertion_values["observed_valid_terminal_state"] == (
        case.expected_terminal_state
    )
    assert assertion_values["observed_mutation_reason_code"] == (
        case.expected_reason_code.value
        if case.expected_reason_code is not None
        else "EXPLICIT_ABSENCE_UNREGISTERED_EXCEPTION"
    )
    assert assertion_values["owner_valid_call_count"] == 1
    assert assertion_values["owner_mutation_call_count"] == 1
    assert assertion_values["required_fields_extracted"] is True
    assert assertion_values["no_effect_assertion_passed"] is True
    assert "expected_terminal_state" not in assertion_values
    assert "expected_reason_code" not in assertion_values

    serialized = serialize_st12h_contract_v1(
        receipt,
        binding_id="ST12H-SERIALIZED-CONTRACT::03",
    )
    payload = json.loads(serialized)
    assert validate_st12h_serialized_contracts_v1(
        binding_id="ST12H-SERIALIZED-CONTRACT::03",
        payload=payload,
    ) == ()

    mutated = replace(case, expected_terminal_state="FORGED_EXPECTED_RESULT")
    with pytest.raises(ContractValidationError) as captured:
        validate_st12h_control_case_v1(mutated)
    assert captured.value.reason_code is ReasonCode.VALIDATION_FAILED
    assert len(ST12H_SEMANTIC_TEST_IDENTITIES) == 42
    assert len(set(ST12H_SEMANTIC_TEST_IDENTITIES)) == 42
    if case.case_id == ST12H_CONTROL_CASES[0].case_id:
        defect_injections = _exercise_st12h_grouped_defect_injections_v1()
        assert len(defect_injections) == 19
        assert all(defect_injections.values())


@pytest.mark.parametrize("case", _domain_cases("accounting"))
def test_st12h_accounting_control_matrix(case: ST12HControlCaseV1) -> None:
    _assert_certified_control(case)


@pytest.mark.parametrize("case", _domain_cases("execution"))
def test_st12h_execution_control_matrix(case: ST12HControlCaseV1) -> None:
    _assert_certified_control(case)


@pytest.mark.parametrize("case", _domain_cases("llm"))
def test_st12h_llm_control_matrix(case: ST12HControlCaseV1) -> None:
    _assert_certified_control(case)


@pytest.mark.parametrize("case", _domain_cases("operations"))
def test_st12h_operations_control_matrix(case: ST12HControlCaseV1) -> None:
    _assert_certified_control(case)


@pytest.mark.parametrize("case", _domain_cases("security"))
def test_st12h_security_control_matrix(case: ST12HControlCaseV1) -> None:
    _assert_certified_control(case)


@pytest.mark.parametrize("case", _domain_cases("source"))
def test_st12h_source_control_matrix(case: ST12HControlCaseV1) -> None:
    _assert_certified_control(case)
