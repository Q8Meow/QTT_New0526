import pytest

from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import (
    ContractValidationError,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.models import (
    ComputationEvidenceBundleV1,
    ComputationModeEligibilityV1,
    EvidenceState,
    ModeEligibilityState,
)


def test_evidence_and_mode_authority_remain_orthogonal() -> None:
    evidence = ComputationEvidenceBundleV1(
        "evidence-1",
        "spec-1",
        "oracle-1",
        EvidenceState.INDEPENDENTLY_VALIDATED,
        ("PASS",),
        ("MUTATION_REJECTED",),
    )
    mode = ComputationModeEligibilityV1("mode-1")
    assert evidence.state is EvidenceState.INDEPENDENTLY_VALIDATED
    assert mode.state is ModeEligibilityState.CONTRACT_ONLY
    assert not mode.allow_activation
    with pytest.raises(ContractValidationError):
        ComputationModeEligibilityV1("mode-2", order_release=True)
