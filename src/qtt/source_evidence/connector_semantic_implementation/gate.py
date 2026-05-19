from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any, Mapping, Sequence

from .manifest import build_pr126_fixture_scope_manifest_record

DETERMINISTIC_FIXTURE_TIME = "2026-05-19T00:00:00Z"
FIXTURE_AUTHORITY_CLASS = "TEST_FIXTURE_NOT_EXTERNAL_FACT"

READY_FOR_PR126_FIXTURE_SCOPE_IMPLEMENTATION = (
    "READY_FOR_PR126_FIXTURE_SCOPE_IMPLEMENTATION"
)
REJECTED_MISSING_ACCEPTED_SOURCE_EVIDENCE = (
    "REJECTED_MISSING_ACCEPTED_SOURCE_EVIDENCE"
)
REJECTED_STALE_ACCEPTED_PACKET = "REJECTED_STALE_ACCEPTED_PACKET"
REJECTED_SUPERSEDED_ACCEPTED_PACKET = "REJECTED_SUPERSEDED_ACCEPTED_PACKET"
REJECTED_REVALIDATION_REQUIRED = "REJECTED_REVALIDATION_REQUIRED"
REJECTED_CONNECTOR_BLOCKING_MATERIALITY = (
    "REJECTED_CONNECTOR_BLOCKING_MATERIALITY"
)
REJECTED_LIVE_TRADING_BLOCKING_MATERIALITY = (
    "REJECTED_LIVE_TRADING_BLOCKING_MATERIALITY"
)
REJECTED_MISSING_UNIT_SCALE_SCOPE = "REJECTED_MISSING_UNIT_SCALE_SCOPE"
REJECTED_CANONICALIZATION_FAILURE = "REJECTED_CANONICALIZATION_FAILURE"
REJECTED_SCOPE_OR_VENUE_MISMATCH = "REJECTED_SCOPE_OR_VENUE_MISMATCH"

IMPLEMENTATION_GATE_STATES = (
    READY_FOR_PR126_FIXTURE_SCOPE_IMPLEMENTATION,
    REJECTED_MISSING_ACCEPTED_SOURCE_EVIDENCE,
    REJECTED_STALE_ACCEPTED_PACKET,
    REJECTED_SUPERSEDED_ACCEPTED_PACKET,
    REJECTED_REVALIDATION_REQUIRED,
    REJECTED_CONNECTOR_BLOCKING_MATERIALITY,
    REJECTED_LIVE_TRADING_BLOCKING_MATERIALITY,
    REJECTED_MISSING_UNIT_SCALE_SCOPE,
    REJECTED_CANONICALIZATION_FAILURE,
    REJECTED_SCOPE_OR_VENUE_MISMATCH,
)

ACTIVE_STAGE1_VENUES = {
    "KALSHI",
    "POLYMARKET",
    "FORECASTEX_IBKR",
    "PREDICTION_MARKETS_GENERAL",
}
FUTURE_MARKET_FAMILIES = {
    "STOCKS",
    "CRYPTOCURRENCY",
    "FUTURES",
    "OPTIONS",
    "EQUITIES",
    "ETFS",
    "FX",
    "COMMODITIES",
}
FALSE_AUTHORITY_FLAGS = (
    "production_connector_semantic_implementation_authority",
    "production_connector_use_allowed_flag",
    "network_io_allowed_flag",
    "order_execution_allowed_flag",
    "production_reachability_allowed_flag",
    "runtime_resolver_snapshot_creation_allowed_flag",
    "replay_paper_execution_allowed_flag",
)


def load_fixture_inputs(
    repo_root: Path,
    fixture_dir: Path | None = None,
) -> dict[str, Any]:
    fixture_dir = fixture_dir or (
        repo_root
        / "tests"
        / "fixtures"
        / "source_evidence"
        / "pr126_connector_semantic_implementation_gate"
    )
    return {
        "accepted_source_evidence_records": _records(
            _load_json(fixture_dir / "accepted_source_evidence_records.v1.fixture.json"),
            "accepted_source_evidence_records",
        ),
        "connector_semantic_binding_records": _records(
            _load_json(fixture_dir / "connector_semantic_binding_records.v1.fixture.json"),
            "connector_semantic_binding_records",
        ),
        "source_change_snapshot": _first_record(
            _load_json(fixture_dir / "source_change_snapshot.v1.fixture.json"),
            "source_change_snapshots",
        ),
    }


def evaluate_implementation_gate(
    *,
    accepted_source_evidence_records: Sequence[Mapping[str, Any]],
    connector_semantic_binding_records: Sequence[Mapping[str, Any]],
    source_change_snapshot: Mapping[str, Any],
) -> dict[str, Any]:
    accepted_index = {
        str(record["accepted_source_evidence_packet_id"]): deepcopy(dict(record))
        for record in accepted_source_evidence_records
    }
    snapshot = deepcopy(dict(source_change_snapshot))
    decision_receipts: list[dict[str, Any]] = []
    rejection_records: list[dict[str, Any]] = []
    manifest_records: list[dict[str, Any]] = []

    for raw_binding in sorted(
        (deepcopy(dict(record)) for record in connector_semantic_binding_records),
        key=_binding_id,
    ):
        accepted = accepted_index.get(str(raw_binding.get("accepted_source_evidence_packet_id")))
        gate_state, reason_code = _gate_state_for(raw_binding, accepted, snapshot)
        decision = _decision_receipt(
            binding=raw_binding,
            accepted_source_evidence=accepted,
            source_change_snapshot=snapshot,
            implementation_gate_state=gate_state,
            reason_code=reason_code,
        )
        decision_receipts.append(decision)
        if gate_state != READY_FOR_PR126_FIXTURE_SCOPE_IMPLEMENTATION:
            rejection_records.append(
                _rejection_record(
                    decision=decision,
                    binding=raw_binding,
                    accepted_source_evidence=accepted,
                    source_change_snapshot=snapshot,
                    reason_code=reason_code,
                )
            )
            continue

        if accepted is None:
            raise AssertionError("ready decisions must have accepted source evidence")
        manifest_records.append(
            build_pr126_fixture_scope_manifest_record(
                decision=decision,
                binding=raw_binding,
                accepted_source_evidence=accepted,
                source_change_snapshot=snapshot,
                deterministic_fixture_time=DETERMINISTIC_FIXTURE_TIME,
                fixture_authority_class=FIXTURE_AUTHORITY_CLASS,
            )
        )

    return {
        "connector_semantic_implementation_gate_report_id": (
            "PR126_CONNECTOR_SEMANTIC_BINDING_IMPLEMENTATION_GATE_REPORT"
        ),
        "repo_pr_label": "PR126",
        "roadmap_pr_implemented": "PR108",
        "fixture_authority_class": FIXTURE_AUTHORITY_CLASS,
        "production_connector_semantic_implementation_authority": False,
        "future_production_launch_path_preserved": True,
        "source_change_snapshot_id": str(snapshot["source_change_snapshot_id"]),
        "deterministic_fixture_time": DETERMINISTIC_FIXTURE_TIME,
        "decision_receipts": decision_receipts,
        "rejection_records": rejection_records,
        "manifest_records": manifest_records,
        "summary": _summary(decision_receipts, rejection_records, manifest_records),
    }


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _records(payload: Mapping[str, Any], key: str) -> list[dict[str, Any]]:
    value = payload.get(key)
    if not isinstance(value, list):
        raise ValueError(f"{key} must be an array")
    return [dict(record) for record in value]


def _first_record(payload: Mapping[str, Any], key: str) -> dict[str, Any]:
    records = _records(payload, key)
    if len(records) != 1:
        raise ValueError(f"{key} must contain exactly one record")
    return records[0]


def _binding_id(binding: Mapping[str, Any]) -> str:
    return str(
        binding.get("source_connector_binding_ledger_record_id")
        or binding.get("connector_semantic_binding_ledger_record_id")
        or ""
    )


def _gate_state_for(
    binding: Mapping[str, Any],
    accepted_source_evidence: Mapping[str, Any] | None,
    source_change_snapshot: Mapping[str, Any],
) -> tuple[str, str]:
    binding_id = _binding_id(binding)
    accepted_id = str(binding.get("accepted_source_evidence_packet_id", ""))

    if accepted_source_evidence is None:
        return (
            REJECTED_MISSING_ACCEPTED_SOURCE_EVIDENCE,
            "ACCEPTED_SOURCE_EVIDENCE_NOT_FOUND",
        )
    if _missing_unit_scale_scope(binding, accepted_source_evidence):
        return REJECTED_MISSING_UNIT_SCALE_SCOPE, "MISSING_UNIT_SCALE_OR_SCOPE"
    if _canonicalization_failed(binding, accepted_source_evidence):
        return REJECTED_CANONICALIZATION_FAILURE, "CANONICALIZATION_MEANING_NOT_PRESERVED"
    if _scope_or_venue_mismatch(binding, accepted_source_evidence, source_change_snapshot):
        return REJECTED_SCOPE_OR_VENUE_MISMATCH, "SCOPE_OR_VENUE_MISMATCH"
    if accepted_id in _set(source_change_snapshot, "stale_accepted_packet_ids"):
        return REJECTED_STALE_ACCEPTED_PACKET, "ACCEPTED_PACKET_STALE"
    if accepted_id in _set(source_change_snapshot, "superseded_accepted_packet_ids"):
        return REJECTED_SUPERSEDED_ACCEPTED_PACKET, "ACCEPTED_PACKET_SUPERSEDED"
    if binding_id in _set(source_change_snapshot, "connector_blocking_materiality_binding_ids"):
        return (
            REJECTED_CONNECTOR_BLOCKING_MATERIALITY,
            "CONNECTOR_BLOCKING_MATERIALITY",
        )
    if binding_id in _set(
        source_change_snapshot, "live_trading_blocking_materiality_binding_ids"
    ):
        return (
            REJECTED_LIVE_TRADING_BLOCKING_MATERIALITY,
            "LIVE_TRADING_BLOCKING_MATERIALITY",
        )
    if _revalidation_required(binding, accepted_id, binding_id, source_change_snapshot):
        return REJECTED_REVALIDATION_REQUIRED, "CONNECTOR_BINDING_REVALIDATION_REQUIRED"

    return (
        READY_FOR_PR126_FIXTURE_SCOPE_IMPLEMENTATION,
        "PR126_FIXTURE_SCOPE_IMPLEMENTATION_READY",
    )


def _missing_unit_scale_scope(
    binding: Mapping[str, Any],
    accepted_source_evidence: Mapping[str, Any],
) -> bool:
    required_fields = ("bound_value_unit_or_scale", "bound_value_scope")
    return any(
        not str(record.get(field, "")).strip()
        for record in (binding, accepted_source_evidence)
        for field in required_fields
    )


def _canonicalization_failed(
    binding: Mapping[str, Any],
    accepted_source_evidence: Mapping[str, Any],
) -> bool:
    if binding.get("canonicalization_meaning_preserved_flag") is not True:
        return True
    if not str(binding.get("bound_value_canonical", "")).strip():
        return True
    if not str(binding.get("bound_value_type", "")).strip():
        return True
    return any(
        binding.get(field) != accepted_source_evidence.get(field)
        for field in ("bound_value_canonical", "bound_value_type")
    )


def _scope_or_venue_mismatch(
    binding: Mapping[str, Any],
    accepted_source_evidence: Mapping[str, Any],
    source_change_snapshot: Mapping[str, Any],
) -> bool:
    for field in (
        "venue_id",
        "target_field_path",
        "semantic_surface_id",
        "bound_value_scope",
    ):
        if binding.get(field) != accepted_source_evidence.get(field):
            return True

    expected_digest = binding.get("accepted_source_evidence_packet_digest")
    if expected_digest and expected_digest != accepted_source_evidence.get(
        "accepted_source_evidence_packet_digest"
    ):
        return True

    accepted_id = str(binding["accepted_source_evidence_packet_id"])
    snapshot_index = source_change_snapshot.get("accepted_packet_scope_index", {})
    if isinstance(snapshot_index, Mapping) and accepted_id in snapshot_index:
        snapshot_scope = snapshot_index[accepted_id]
        if isinstance(snapshot_scope, Mapping):
            if snapshot_scope.get("venue_id") != accepted_source_evidence.get("venue_id"):
                return True
            if snapshot_scope.get("bound_value_scope") != accepted_source_evidence.get(
                "bound_value_scope"
            ):
                return True
    return False


def _revalidation_required(
    binding: Mapping[str, Any],
    accepted_id: str,
    binding_id: str,
    source_change_snapshot: Mapping[str, Any],
) -> bool:
    return (
        binding.get("connector_binding_revalidation_state") == "REVALIDATION_REQUIRED"
        or accepted_id in _set(source_change_snapshot, "revalidation_due_packet_ids")
        or binding_id
        in _set(source_change_snapshot, "connector_binding_revalidation_required_ids")
    )


def _decision_receipt(
    *,
    binding: Mapping[str, Any],
    accepted_source_evidence: Mapping[str, Any] | None,
    source_change_snapshot: Mapping[str, Any],
    implementation_gate_state: str,
    reason_code: str,
) -> dict[str, Any]:
    binding_id = _binding_id(binding)
    accepted_id = str(binding.get("accepted_source_evidence_packet_id", ""))
    ready = implementation_gate_state == READY_FOR_PR126_FIXTURE_SCOPE_IMPLEMENTATION
    return {
        "implementation_decision_receipt_id": f"PR126_IMPLEMENTATION_DECISION_{binding_id}",
        "fixture_authority_class": FIXTURE_AUTHORITY_CLASS,
        "source_connector_binding_ledger_record_id": binding_id,
        "accepted_source_evidence_packet_id": accepted_id,
        "source_change_snapshot_id": str(source_change_snapshot["source_change_snapshot_id"]),
        "venue_id": str(binding.get("venue_id", "")),
        "target_field_path": str(binding.get("target_field_path", "")),
        "semantic_surface_id": str(binding.get("semantic_surface_id", "")),
        "canonical_connector_namespace": str(
            binding.get("canonical_connector_namespace", "")
        ),
        "implementation_gate_state": implementation_gate_state,
        "implementation_decision_state": (
            "IMPLEMENTATION_ELIGIBLE_FOR_PR126_FIXTURE_SCOPE_MANIFEST"
            if ready
            else "IMPLEMENTATION_REJECTED_FOR_PR126_FIXTURE_SCOPE_MANIFEST"
        ),
        "implementation_manifest_state": (
            "PR126_FIXTURE_SCOPE_MANIFEST_READY"
            if ready
            else "PR126_FIXTURE_SCOPE_MANIFEST_NOT_CREATED"
        ),
        "connector_binding_revalidation_state": str(
            binding.get("connector_binding_revalidation_state", "UNKNOWN")
        ),
        "source_change_snapshot_state": str(
            source_change_snapshot["source_change_snapshot_state"]
        ),
        "decision_reason_code": reason_code,
        "deterministic_fixture_time": DETERMINISTIC_FIXTURE_TIME,
        "production_connector_semantic_implementation_authority": False,
        "production_connector_use_allowed_flag": False,
        "network_io_allowed_flag": False,
        "order_execution_allowed_flag": False,
        "production_reachability_allowed_flag": False,
        "runtime_resolver_snapshot_creation_allowed_flag": False,
        "replay_paper_execution_allowed_flag": False,
        "future_production_launch_path_preserved": True,
        "accepted_source_fixture_authority_class": (
            None
            if accepted_source_evidence is None
            else accepted_source_evidence.get("fixture_authority_class")
        ),
    }


def _rejection_record(
    *,
    decision: Mapping[str, Any],
    binding: Mapping[str, Any],
    accepted_source_evidence: Mapping[str, Any] | None,
    source_change_snapshot: Mapping[str, Any],
    reason_code: str,
) -> dict[str, Any]:
    binding_id = str(decision["source_connector_binding_ledger_record_id"])
    return {
        "connector_semantic_implementation_rejection_id": (
            f"PR126_IMPLEMENTATION_REJECTION_{binding_id}"
        ),
        "implementation_decision_receipt_id": str(
            decision["implementation_decision_receipt_id"]
        ),
        "fixture_authority_class": FIXTURE_AUTHORITY_CLASS,
        "source_connector_binding_ledger_record_id": binding_id,
        "accepted_source_evidence_packet_id": str(
            decision["accepted_source_evidence_packet_id"]
        ),
        "source_change_snapshot_id": str(source_change_snapshot["source_change_snapshot_id"]),
        "venue_id": str(binding.get("venue_id", "")),
        "target_field_path": str(binding.get("target_field_path", "")),
        "semantic_surface_id": str(binding.get("semantic_surface_id", "")),
        "implementation_gate_state": str(decision["implementation_gate_state"]),
        "implementation_decision_state": str(decision["implementation_decision_state"]),
        "connector_binding_revalidation_state": str(
            decision["connector_binding_revalidation_state"]
        ),
        "source_change_snapshot_state": str(decision["source_change_snapshot_state"]),
        "rejection_reason_code": reason_code,
        "deterministic_fixture_time": DETERMINISTIC_FIXTURE_TIME,
        "production_connector_semantic_implementation_authority": False,
        "production_connector_use_allowed_flag": False,
        "network_io_allowed_flag": False,
        "order_execution_allowed_flag": False,
        "production_reachability_allowed_flag": False,
        "runtime_resolver_snapshot_creation_allowed_flag": False,
        "replay_paper_execution_allowed_flag": False,
        "future_production_launch_path_preserved": True,
        "accepted_source_fixture_authority_class": (
            None
            if accepted_source_evidence is None
            else accepted_source_evidence.get("fixture_authority_class")
        ),
    }


def _set(record: Mapping[str, Any], key: str) -> set[str]:
    value = record.get(key, [])
    if not isinstance(value, list):
        return set()
    return {str(item) for item in value}


def _summary(
    decisions: Sequence[Mapping[str, Any]],
    rejections: Sequence[Mapping[str, Any]],
    manifests: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    rejection_counts = {
        state: sum(1 for record in rejections if record["implementation_gate_state"] == state)
        for state in IMPLEMENTATION_GATE_STATES
        if state != READY_FOR_PR126_FIXTURE_SCOPE_IMPLEMENTATION
    }
    return {
        "fixture_connector_binding_record_count": len(decisions),
        "fixture_implementation_gate_success_count": len(manifests),
        "fixture_implementation_gate_rejection_count": len(rejections),
        "production_connector_semantic_implementation_count": 0,
        "production_connector_semantic_implementation_authority_count": 0,
        "runtime_resolver_snapshot_created_count": 0,
        "order_authority_created": False,
        "network_io_created_count": 0,
        "future_production_launch_path_preserved": True,
        "rejection_counts_by_state": rejection_counts,
    }
