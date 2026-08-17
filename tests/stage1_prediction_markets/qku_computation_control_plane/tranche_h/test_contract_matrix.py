from __future__ import annotations

from dataclasses import replace
import json

import pytest

from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import (
    ContractValidationError,
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
    validate_st12h_domain_v1,
    validate_st12h_serialized_contracts_v1,
)


def _domain_cases(domain: str) -> tuple[ST12HControlCaseV1, ...]:
    return tuple(case for case in ST12H_CONTROL_CASES if case.domain == domain)


def _assert_certified_control(case: ST12HControlCaseV1) -> None:
    receipt = validate_st12h_control_case_v1(case)
    domain_receipts = validate_st12h_domain_v1(case.domain)
    assert receipt in domain_receipts
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

    serialized = serialize_st12h_contract_v1(
        receipt,
        binding_id="ST12H-SERIALIZED-CONTRACT::03",
    )
    payload = json.loads(serialized)
    assert validate_st12h_serialized_contracts_v1(
        binding_id="ST12H-SERIALIZED-CONTRACT::03",
        payload=payload,
    ) == ()

    mutated = replace(case, fixture_ref=f"{case.fixture_ref} [MUTATED]")
    with pytest.raises(ContractValidationError) as captured:
        validate_st12h_control_case_v1(mutated)
    assert captured.value.reason_code is case.expected_reason_code
    assert len(ST12H_SEMANTIC_TEST_IDENTITIES) == 42
    assert len(set(ST12H_SEMANTIC_TEST_IDENTITIES)) == 42


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
