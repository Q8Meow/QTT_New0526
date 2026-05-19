from __future__ import annotations

from tests.source_evidence.pr124_connector_semantic_binding_support import consumed


def test_pr124_consumer_boundary_blocks_direct_runtime_and_live_use():
    record = consumed()["success_records"][0]

    assert record["runtime_resolver_gate_may_consume_connector_semantic_binding_ledger"] is True
    assert (
        record[
            "runtime_resolver_snapshot_create_may_consume_only_after_runtime_resolver_snapshot_gate_green"
        ]
        is True
    )
    assert (
        record[
            "venue_connector_scaffold_may_consume_binding_for_static_non_live_configuration_tests_only"
        ]
        is True
    )
    assert (
        record[
            "venue_connector_live_client_may_not_consume_binding_until_later_live_connector_authorization_exists"
        ]
        is True
    )
    assert (
        record[
            "replay_paper_may_not_consume_connector_semantic_binding_without_runtime_resolver_snapshot_input_lock"
        ]
        is True
    )
    assert (
        record[
            "connector_semantic_binding_ledger_may_not_be_treated_as_live_order_authority"
        ]
        is True
    )
    assert record["consumer_contract_state"] == "STATIC_FIXTURE_CONSUMER_CONTRACT_NONLIVE_ONLY"
