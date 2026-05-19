from __future__ import annotations

import json
from pathlib import Path


SCHEMA_ROOT = Path("schemas/source_evidence/revalidation")


def test_pr125_source_revalidation_policy_schema_supports_owner_policy():
    policy_schema = json.loads(
        (SCHEMA_ROOT / "source_revalidation_policy.schema.json").read_text(
            encoding="utf-8"
        )
    )
    materiality_schema = json.loads(
        (SCHEMA_ROOT / "source_change_materiality_event.schema.json").read_text(
            encoding="utf-8"
        )
    )

    assert policy_schema["properties"]["live_critical_revalidation_interval"]["const"] == "P1D"
    assert policy_schema["properties"]["low_risk_revalidation_interval"]["const"] == "P7D"
    assert (
        policy_schema["properties"]["event_triggered_revalidation_latency_class"]["const"]
        == "IMMEDIATE_CONTROL_PLANE_REVALIDATION_BEFORE_NEW_BINDING_OR_NEW_LIVE_USE"
    )
    assert policy_schema["properties"]["source_retrieval_allowed_flag"]["const"] is False
    assert policy_schema["properties"]["source_acceptance_allowed_flag"]["const"] is False
    assert set(materiality_schema["$defs"]["materiality_class"]["enum"]) == {
        "INFO_ONLY",
        "LOW_RISK",
        "MEDIUM_RISK",
        "HIGH_RISK",
        "CONNECTOR_BLOCKING",
        "LIVE_TRADING_BLOCKING",
    }
