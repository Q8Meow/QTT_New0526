from tests.source_evidence.pr127_execution_lifecycle_support import placeholder_records


def test_pr127_fill_integrity_cashflow_latency_settlement_reconciliation_are_placeholders_requiring_accepted_sources():
    placeholders = placeholder_records()
    families = {record["target_semantic_family"] for record in placeholders}

    assert len(placeholders) == 15
    assert families == {
        "fill_integrity",
        "cashflow_pnl",
        "latency_component",
        "settlement_finality",
        "reconciliation",
    }
    for record in placeholders:
        assert record["accepted_source_evidence_required_flag"] is True
        assert record["production_value_populated"] is False
        assert record["future_pr_required_for_production_population"].startswith("PR")
        assert record["fixture_authority_class"] == "TEST_FIXTURE_NOT_EXTERNAL_FACT"
