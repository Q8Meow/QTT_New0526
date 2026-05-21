from .pr134_runtime_resolver_snapshot_support import artifacts


def test_pr134_preserves_pr117_downstream_path():
    handoff = artifacts()["runtime_resolver_downstream_handoff"]
    assert handoff["downstream_prs"] == ["PR117"]
    assert handoff["downstream_pr117_contract_prepared"] is True
    assert handoff["downstream_pr117_execution_authorized"] is False
    assert handoff["downstream_historical_dataset_digest_authorized_now"] is False
