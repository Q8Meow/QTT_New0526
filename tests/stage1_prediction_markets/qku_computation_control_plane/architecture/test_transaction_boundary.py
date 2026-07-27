import pytest

from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import (
    ContractValidationError,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.models import (
    TransactionEnvelopeV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.validation import (
    validate_transaction_contract,
)


def test_transaction_is_in_memory_and_path_safe() -> None:
    transaction = TransactionEnvelopeV1(
        "transaction-1",
        "snapshot-1",
        "temporary/receipt.json",
    )
    validate_transaction_contract(transaction)
    assert not transaction.committed
    with pytest.raises(ContractValidationError):
        TransactionEnvelopeV1("transaction-2", "snapshot-1", committed=True)
