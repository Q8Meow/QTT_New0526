from __future__ import annotations

from typing import Mapping

from src.qtt.stage1_prediction_markets.market_data_ingest import policy


def _scope_value(record: Mapping[str, object]) -> str:
    return str(record.get("venue_id") or record.get("scope_id"))


def _scope_ref_from_value(scope_value: str) -> policy.ScopeRef:
    scope_kind = "venue" if scope_value in policy.STAGE1_VENUE_IDS else "shared_scope"
    return policy.ScopeRef(scope_kind, scope_value)


def build_adapter_bindings(
    adapter_inputs: list[Mapping[str, object]],
    canonical_events: list[Mapping[str, object]],
    source_dependencies: list[Mapping[str, object]],
    credential_handoff_ref: str,
) -> list[dict[str, object]]:
    inputs_by_scope: dict[str, list[str]] = {}
    events_by_scope: dict[str, list[str]] = {}
    deps_by_scope: dict[str, list[str]] = {}
    connector_refs_by_scope: dict[str, list[str]] = {}
    for record in adapter_inputs:
        inputs_by_scope.setdefault(_scope_value(record), []).append(str(record["input_id"]))
    for record in canonical_events:
        events_by_scope.setdefault(_scope_value(record), []).append(str(record["event_id"]))
    for record in source_dependencies:
        scope_value = _scope_value(record)
        deps_by_scope.setdefault(scope_value, []).append(str(record["dependency_id"]))
        connector_ref = record.get("connector_semantic_binding_ref")
        if connector_ref:
            connector_refs_by_scope.setdefault(scope_value, []).append(str(connector_ref))

    records: list[dict[str, object]] = []
    for scope_ref in policy.stage1_scope_refs():
        scope_value = scope_ref.value
        records.append(
            {
                **policy.common_record_fields("VENUE_MARKET_DATA_ADAPTER_BINDING"),
                **policy.scope_field(_scope_ref_from_value(scope_value)),
                "binding_id": f"PR132_{scope_value}_MARKET_DATA_ADAPTER_BINDING_V1",
                "adapter_name": f"PR132_{scope_value}_FIXTURE_MARKET_DATA_INGEST_ADAPTER",
                "adapter_version": "v1",
                "adapter_scope": "FIXTURE_BACKED_CONTRACT_ONLY",
                "input_refs": inputs_by_scope[scope_value],
                "output_event_refs": events_by_scope[scope_value],
                "credential_readiness_handoff_ref": credential_handoff_ref,
                "source_dependency_refs": deps_by_scope[scope_value],
                "connector_semantic_dependency_refs": sorted(
                    connector_refs_by_scope.get(scope_value, [])
                ),
                "allowed_use": "FIXTURE_BACKED_MARKET_DATA_INGEST_CONTRACT_ONLY",
                "disallowed_use": list(policy.DISALLOWED_USE),
                "future_live_use_requires_owner_approval": True,
                "future_live_use_requires_accepted_source_packet": True,
                "future_live_use_requires_fresh_revalidation_state": True,
                "future_live_use_requires_connector_semantic_binding": True,
                "future_live_use_requires_credential_provider_receipt_if_credentials_needed": True,
                "future_quantum_use_requires_pr115_pr116_pr117_data_chain": True,
                "future_quantum_use_requires_replay_paper_validation": True,
                "future_quantum_use_requires_owner_approval": True,
            }
        )
    return records
