import pytest

from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import (
    ContractValidationError,
    ReasonCode,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.models import (
    OperationContractV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.validation import (
    TRANCHE_A_OPERATION_CONTRACTS,
    validate_operation_contract_closure,
)


def test_operation_contract_is_complete_collision_free_and_data_only() -> None:
    operations = validate_operation_contract_closure()
    assert operations is TRANCHE_A_OPERATION_CONTRACTS
    assert len({item.operation_id for item in operations}) == 15
    assert len({item.input_contract for item in operations}) == 15
    assert len({item.output_contract for item in operations}) == 15
    assert len({item.failure_contract for item in operations}) == 15
    assert not any(item.runtime_effect_authorized for item in operations)
    request = operations[0].bind_request(
        request_id="request-1",
        contract_version="1.0",
        payload_json='{"formula_id":"FORMULA_QKU"}',
    )
    response = operations[0].bind_response(
        request,
        result_json='{"identity":"FORMULA_QKU"}',
    )
    failure = operations[0].bind_failure(
        request,
        reason_code=ReasonCode.OWNER_DATA_MISSING,
        detail="owner row missing",
    )
    assert response.request_id == request.request_id
    assert failure.failure_contract == operations[0].failure_contract
    with pytest.raises(ContractValidationError):
        operations[0].bind_failure(
            request,
            reason_code=ReasonCode.PATH_UNSAFE,
            detail="not allowlisted",
        )
    with pytest.raises(ContractValidationError):
        operations[0].bind_request(
            request_id="request-2",
            contract_version="1.0",
            payload_json='{ "formula_id": "FORMULA_QKU" }',
        )
    collision = (
        OperationContractV1(
            "COLLIDING_OPERATION",
            operations[1].input_contract,
            "CollidingResponseV1",
            "CollidingFailureV1",
            request_fields=operations[0].request_fields,
            response_fields=operations[0].response_fields,
            failure_reason_codes=operations[0].failure_reason_codes,
        ),
        *operations[1:],
    )
    with pytest.raises(ContractValidationError):
        validate_operation_contract_closure(collision)
    with pytest.raises(ContractValidationError):
        OperationContractV1("effect", "In", "Out", "Failure", True)
