from tests.source_evidence import pr131_credential_alias_readiness_support as support


def test_pr131_rejects_malformed_pr130_handoff():
    value = support.cloned_artifacts()
    value["pr130_handoff"]["source_repo_pr_label"] = "PR129"

    failures = support.validation_failures(value)

    assert any("source_repo_pr_label" in failure for failure in failures)
