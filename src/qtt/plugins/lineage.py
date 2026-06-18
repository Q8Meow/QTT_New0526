"""Lineage row construction helpers."""

from __future__ import annotations


def lineage_row(
    *,
    artifact_id: str,
    artifact_path: str,
    artifact_type: str,
    producer_report: str,
    consumer_report: str,
    authority_envelope_ref: str,
) -> dict[str, object]:
    return {
        "artifact_id": artifact_id,
        "artifact_path": artifact_path,
        "artifact_type": artifact_type,
        "producer_pr": "PR162E",
        "producer_report": producer_report,
        "producer_row_id": artifact_id,
        "owning_agent": "Commander",
        "duty_source_ref": "PR165_D2_AgentDutySourceCrosswalk.report.json",
        "consumer_report": consumer_report,
        "consumer_row_id": artifact_id,
        "downstream_pr": "PR162F_OR_RETEST_SUCCESSOR",
        "downstream_agent": "Governance",
        "connector_readiness_route_if_applicable": "PR162E_To_FutureConnectors.report.json",
        "market_portability_route_if_applicable": "PR162E_To_MarketPortability.report.json",
        "dashboard_visibility": True,
        "commander_visibility": True,
        "governance_visibility": True,
        "terminal_flag": False,
        "terminal_reason_if_terminal": "",
        "authority_envelope_ref": authority_envelope_ref,
        "no_orphan_status": "PASS",
    }
