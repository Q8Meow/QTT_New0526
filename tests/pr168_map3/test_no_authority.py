from __future__ import annotations

from tests.pr168_map3._helpers import summary


def test_forbidden_authority_counts_are_zero() -> None:
    data = summary()
    for key in (
        "real_positive_count",
        "real_negative_count",
        "champion_allowed_count",
        "live_candidate_allowed_count",
        "source_truth_acceptance_created_count",
        "connector_binding_created_count",
        "private_state_or_cash_access_created_count",
        "order_authority_created_count",
        "quantum_backend_execution_count",
        "quantum_advantage_claim_count",
        "qtt_sha_or_atomicrows_hash_authority_count",
    ):
        assert data[key] == 0
