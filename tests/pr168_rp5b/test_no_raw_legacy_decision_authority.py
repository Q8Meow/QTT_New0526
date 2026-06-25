from tests.pr168_rp5b._helpers import load_report, load_rows


def test_no_raw_legacy_decision_authority() -> None:
    report = load_report("PR168_RP5B_NoRawLegacyDecisionAuthority.report.json")
    rows = load_rows("no_raw_legacy_decision_authority_rows")
    assert report["raw_legacy_decision_authority_violation_count"] == 0
    assert rows
    assert any(row["rule_id"] == "FUTURE_AGENTS_CONSUME_ACTIVE_REGISTRY" for row in rows)
