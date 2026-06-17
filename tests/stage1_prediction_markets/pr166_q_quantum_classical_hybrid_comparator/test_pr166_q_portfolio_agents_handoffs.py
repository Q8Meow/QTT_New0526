from __future__ import annotations

from .helpers import assert_report_contract, summary


def test_pr166_q_portfolio_capacity_marginal_utility_and_roles_are_complete():
    portfolio = assert_report_contract("PR166_Q_PortfolioDiversificationLedger.report.json", 559)
    capacity = assert_report_contract("PR166_Q_CapacityCrowdingLimitLedger.report.json", 559)
    marginal = assert_report_contract("PR166_Q_MarginalUtilitySelection.report.json", 559)
    roles = assert_report_contract("PR166_Q_ChampionChallengerSelection.report.json", 559)
    assert all(row["diversification_contribution"] >= 0 for row in portfolio)
    assert all(row["capacity_estimate"] >= 0 for row in capacity)
    assert all(row["final_marginal_utility_score"] >= 0 for row in marginal)
    assert set(summary()["champion_challenger_role_counts"]) == {
        "champion",
        "challenger",
        "watch",
        "retest",
        "repair",
        "no-trade",
    }
    assert all(row["selection_role"] in {"champion", "challenger", "watch", "retest", "repair", "no-trade"} for row in roles)


def test_pr166_q_agent_dag_no_orphan_and_downstream_handoffs_are_complete():
    work = assert_report_contract("PR166_Q_AgentWorkOrderLedger.report.json", 559)
    dag = assert_report_contract("PR166_Q_AgentOrchestrationDAG.report.json", 559)
    no_orphan = assert_report_contract("PR166_Q_NoOrphanProof.report.json", 559)
    uac = assert_report_contract("PR166_Q_UniversalArtifactConsumerMap.report.json")
    assert all(row["no_live_authority_flag"] is True for row in work)
    assert all(row["upstream_report_refs"] for row in dag)
    assert all(row["downstream_report_route"] for row in dag)
    assert all(row["no_orphan_status"].startswith("CONNECTED_") for row in no_orphan)
    assert all(row["terminal_flag"] or row["consumed_by_report"] for row in uac)
    for filename in (
        "PR166_Q_PR166_QB_BoundedNonLiveQuantumBenchmarkHandoff.report.json",
        "PR166_Q_PR166_QC_QuantumSelectedReplayPaperRetestHandoff.report.json",
        "PR166_Q_PR162E_Q_AutoMapperHandoff.report.json",
        "PR166_Q_PR167_OpenTradeSimulatorHandoff.report.json",
        "PR166_Q_PR162D_R3_ExternalAcquisitionGapHandoff.report.json",
        "PR166_Q_PR162E_PluginFrameworkHandoff.report.json",
        "PR166_Q_PR162F_OwnerAgentIntakeHandoff.report.json",
    ):
        rows = assert_report_contract(filename, 559)
        assert all(row["handoff_status"] == "READY_FOR_DOWNSTREAM_NONLIVE_CONSUMPTION" for row in rows)
