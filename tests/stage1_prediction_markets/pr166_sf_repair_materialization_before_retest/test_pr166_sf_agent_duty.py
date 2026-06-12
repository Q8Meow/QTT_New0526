from .conftest import assert_rows


def test_pr166_sf_agent_duty_ledger_covers_targets(pr166_sf_records):
    rows = assert_rows(pr166_sf_records, "PR166_SF_AgentDutyLedger.report.json")
    assert len(rows) == 6502
    for row in rows[:100]:
        assert row["source_agent_duty_ref"]
        assert row["expected_output_artifact"]
        assert row["validation_receipt"]
        assert row["priority"]
