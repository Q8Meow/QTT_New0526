from tests.pr162e.helpers import records


def test_agent_duty_binding_uses_pr165_d2_crosswalk():
    rows = records("PR162E_AgentDutyBinding.report.json")
    assert rows
    assert all("PR165_D2_AgentDutySourceCrosswalk" in row["agent_duty_source_ref"] for row in rows)
