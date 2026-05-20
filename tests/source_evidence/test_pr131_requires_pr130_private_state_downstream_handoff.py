from tests.source_evidence import pr131_credential_alias_readiness_support as support


def test_pr131_requires_pr130_private_state_downstream_handoff():
    value = support.cloned_artifacts()
    value["pr130_handoff"] = None

    failures = support.validation_failures(value)

    assert any("missing PR130 private-state downstream handoff" in failure for failure in failures)
