from __future__ import annotations

from ._helpers import assert_hard_zero_report, load_report, load_rows


def test_rp5c_input_discovery_consumes_required_surfaces() -> None:
    report = load_report("PR168_RP5C_Input.report.json")
    rows = load_rows("source_artifact_consumption_ledger")
    paths = {row["source_file_path"] for row in rows}

    assert report["branch_name"] == "pr168-rp5c-immutable-qku-formula-library"
    assert "docs/master_plan/generated/PR168_RP5B_ActiveArtifactRegistry.report.json" in paths
    assert "docs/master_plan/generated/PR168_RP5B_LegacyKeepReasonLedger.report.json" in paths
    assert "docs/master_plan/generated/PR168_RP5A_QKUFormulaIdentityDependency.report.json" in paths
    assert "docs/master_plan/generated/PR165_D2_AgentRosterDiscoveryAudit.report.json" in paths
    assert "docs/master_plan/generated/PR165_D2_AgentDutySourceCrosswalk.report.json" in paths
    assert all(row["consumption_status"] for row in rows)
    assert_hard_zero_report(report)
