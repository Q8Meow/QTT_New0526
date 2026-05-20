from tests.source_evidence import pr131_credential_alias_readiness_support as support


def test_pr131_rejects_scope_mismatch():
    value = support.cloned_artifacts()
    value["pr130_handoff"]["venue_ids_in_scope"] = ["KALSHI", "POLYMARKET"]

    failures = support.validation_failures(value)

    assert any("three Stage-1 venues" in failure or "scope mismatch" in failure for failure in failures)
