from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any, Mapping, Sequence

from .handoff import build_cross_venue_normalization_handoff
from .phases import build_phase_records
from .placeholders import build_placeholder_record
from .transitions import build_transition_records


DETERMINISTIC_FIXTURE_TIME = "2026-05-19T00:00:00Z"
FIXTURE_AUTHORITY_CLASS = "TEST_FIXTURE_NOT_EXTERNAL_FACT"

READY_FOR_PR127_FIXTURE_SCOPE_MODEL = "READY_FOR_PR127_FIXTURE_SCOPE_MODEL"
REJECTED_MISSING_CONNECTOR_IMPLEMENTATION_GATE = (
    "REJECTED_MISSING_CONNECTOR_IMPLEMENTATION_GATE"
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
REJECTED_TRADING_BLOCKING_MATERIALITY = "REJECTED_TRADING_BLOCKING_MATERIALITY"
REJECTED_SCOPE_OR_VENUE_MISMATCH = "REJECTED_SCOPE_OR_VENUE_MISMATCH"
REJECTED_MISSING_LIFECYCLE_SEMANTIC_SUPPORT = (
    "REJECTED_MISSING_LIFECYCLE_SEMANTIC_SUPPORT"
)
REJECTED_MISSING_FILL_INTEGRITY_SUPPORT = (
    "REJECTED_MISSING_FILL_INTEGRITY_SUPPORT"
)
REJECTED_MISSING_CASHFLOW_PNL_SUPPORT = "REJECTED_MISSING_CASHFLOW_PNL_SUPPORT"
REJECTED_MISSING_LATENCY_COMPONENT_SUPPORT = (
    "REJECTED_MISSING_LATENCY_COMPONENT_SUPPORT"
)
REJECTED_MISSING_SETTLEMENT_FINALITY_SUPPORT = (
    "REJECTED_MISSING_SETTLEMENT_FINALITY_SUPPORT"
)
REJECTED_MISSING_RECONCILIATION_SUPPORT = "REJECTED_MISSING_RECONCILIATION_SUPPORT"

LIFECYCLE_MODEL_STATES: tuple[str, ...] = (
    READY_FOR_PR127_FIXTURE_SCOPE_MODEL,
    REJECTED_MISSING_CONNECTOR_IMPLEMENTATION_GATE,
    REJECTED_MISSING_ACCEPTED_SOURCE_EVIDENCE,
    REJECTED_STALE_ACCEPTED_PACKET,
    REJECTED_SUPERSEDED_ACCEPTED_PACKET,
    REJECTED_REVALIDATION_REQUIRED,
    REJECTED_CONNECTOR_BLOCKING_MATERIALITY,
    REJECTED_TRADING_BLOCKING_MATERIALITY,
    REJECTED_SCOPE_OR_VENUE_MISMATCH,
    REJECTED_MISSING_LIFECYCLE_SEMANTIC_SUPPORT,
    REJECTED_MISSING_FILL_INTEGRITY_SUPPORT,
    REJECTED_MISSING_CASHFLOW_PNL_SUPPORT,
    REJECTED_MISSING_LATENCY_COMPONENT_SUPPORT,
    REJECTED_MISSING_SETTLEMENT_FINALITY_SUPPORT,
    REJECTED_MISSING_RECONCILIATION_SUPPORT,
)

ACTIVE_STAGE1_VENUES: tuple[str, ...] = (
    "KALSHI",
    "POLYMARKET",
    "FORECASTEX_IBKR",
)
SHARED_SCOPE_METADATA_VENUES: tuple[str, ...] = ("PREDICTION_MARKETS_GENERAL",)

REQUIRED_SEMANTIC_FAMILIES: tuple[str, ...] = (
    "execution_lifecycle",
    "fill_integrity",
    "cashflow_pnl",
    "latency_component",
    "settlement_finality",
    "reconciliation",
)

MISSING_SUPPORT_STATE_BY_FAMILY = {
    "execution_lifecycle": REJECTED_MISSING_LIFECYCLE_SEMANTIC_SUPPORT,
    "fill_integrity": REJECTED_MISSING_FILL_INTEGRITY_SUPPORT,
    "cashflow_pnl": REJECTED_MISSING_CASHFLOW_PNL_SUPPORT,
    "latency_component": REJECTED_MISSING_LATENCY_COMPONENT_SUPPORT,
    "settlement_finality": REJECTED_MISSING_SETTLEMENT_FINALITY_SUPPORT,
    "reconciliation": REJECTED_MISSING_RECONCILIATION_SUPPORT,
}

AUTHORITY_FALSE_FLAGS = (
    "production_connector_use_allowed_flag",
    "order_execution_allowed_flag",
    "order_routing_authority_allowed_flag",
    "network_io_allowed_flag",
    "runtime_cash_receipt_allowed_flag",
    "private_state_fetch_allowed_flag",
    "replay_paper_execution_allowed_flag",
    "runtime_resolver_snapshot_creation_allowed_flag",
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
        / "pr127_execution_lifecycle"
    )
    implementation_payload = _load_json(
        fixture_dir / "connector_implementation_gate_records.v1.fixture.json"
    )
    return {
        "accepted_source_evidence_records": _records(
            _load_json(fixture_dir / "accepted_source_evidence_records.v1.fixture.json"),
            "accepted_source_evidence_records",
        ),
        "shared_scope_metadata_records": _records(
            _load_json(fixture_dir / "accepted_source_evidence_records.v1.fixture.json"),
            "shared_scope_metadata_records",
        ),
        "connector_semantic_binding_records": _records(
            _load_json(
                fixture_dir / "connector_semantic_binding_records.v1.fixture.json"
            ),
            "connector_semantic_binding_records",
        ),
        "source_change_snapshot": _first_record(
            _load_json(fixture_dir / "source_change_snapshot.v1.fixture.json"),
            "source_change_snapshots",
        ),
        "connector_implementation_gate_records": _records(
            implementation_payload,
            "connector_implementation_gate_records",
        ),
        "lifecycle_model_candidate_records": _records(
            implementation_payload,
            "lifecycle_model_candidate_records",
        ),
    }


def build_execution_lifecycle_artifacts(
    *,
    accepted_source_evidence_records: Sequence[Mapping[str, Any]],
    connector_semantic_binding_records: Sequence[Mapping[str, Any]],
    source_change_snapshot: Mapping[str, Any],
    connector_implementation_gate_records: Sequence[Mapping[str, Any]],
    lifecycle_model_candidate_records: Sequence[Mapping[str, Any]],
    shared_scope_metadata_records: Sequence[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    accepted_index = _index_by(accepted_source_evidence_records, "accepted_source_evidence_packet_id")
    binding_index = _index_by(connector_semantic_binding_records, "source_connector_binding_ledger_record_id")
    implementation_index = _index_by(
        connector_implementation_gate_records,
        "connector_implementation_gate_record_id",
    )

    lifecycle_models: list[dict[str, Any]] = []
    phase_records: list[dict[str, Any]] = []
    transition_records: list[dict[str, Any]] = []
    placeholder_records: list[dict[str, Any]] = []
    validation_receipts: list[dict[str, Any]] = []
    rejection_records: list[dict[str, Any]] = []

    for candidate in sorted(
        (deepcopy(dict(record)) for record in lifecycle_model_candidate_records),
        key=lambda record: str(record["lifecycle_model_candidate_id"]),
    ):
        state, reason, support_refs = _candidate_state(
            candidate=candidate,
            accepted_index=accepted_index,
            binding_index=binding_index,
            implementation_index=implementation_index,
            source_change_snapshot=source_change_snapshot,
        )
        receipt = _validation_receipt(candidate, state, reason)
        validation_receipts.append(receipt)
        if state != READY_FOR_PR127_FIXTURE_SCOPE_MODEL:
            rejection_records.append(_rejection_record(candidate, receipt, state, reason))
            continue

        model = _model_record(
            candidate=candidate,
            receipt=receipt,
            support_refs=support_refs,
            source_change_snapshot=source_change_snapshot,
        )
        phases = build_phase_records(
            model_id=model["per_venue_execution_lifecycle_model_id"],
            venue_id=str(candidate["venue_id"]),
            deterministic_fixture_time=DETERMINISTIC_FIXTURE_TIME,
            fixture_authority_class=FIXTURE_AUTHORITY_CLASS,
        )
        transitions = build_transition_records(
            model_id=model["per_venue_execution_lifecycle_model_id"],
            venue_id=str(candidate["venue_id"]),
            deterministic_fixture_time=DETERMINISTIC_FIXTURE_TIME,
            fixture_authority_class=FIXTURE_AUTHORITY_CLASS,
        )
        placeholders = [
            build_placeholder_record(
                model_id=model["per_venue_execution_lifecycle_model_id"],
                venue_id=str(candidate["venue_id"]),
                target_semantic_family=family,
                deterministic_fixture_time=DETERMINISTIC_FIXTURE_TIME,
                fixture_authority_class=FIXTURE_AUTHORITY_CLASS,
            )
            for family in REQUIRED_SEMANTIC_FAMILIES
            if family != "execution_lifecycle"
        ]
        placeholder_by_family = {
            record["target_semantic_family"]: record for record in placeholders
        }
        model["lifecycle_phase_records"] = phases
        model["lifecycle_transition_records"] = transitions
        model["fill_integrity_placeholder_ref"] = placeholder_by_family[
            "fill_integrity"
        ]["placeholder_id"]
        model["cashflow_pnl_placeholder_ref"] = placeholder_by_family[
            "cashflow_pnl"
        ]["placeholder_id"]
        model["latency_component_placeholder_ref"] = placeholder_by_family[
            "latency_component"
        ]["placeholder_id"]
        model["settlement_finality_placeholder_ref"] = placeholder_by_family[
            "settlement_finality"
        ]["placeholder_id"]
        model["reconciliation_placeholder_ref"] = placeholder_by_family[
            "reconciliation"
        ]["placeholder_id"]

        lifecycle_models.append(model)
        phase_records.extend(phases)
        transition_records.extend(transitions)
        placeholder_records.extend(placeholders)

    handoff = build_cross_venue_normalization_handoff(
        model_records=lifecycle_models,
        deterministic_fixture_time=DETERMINISTIC_FIXTURE_TIME,
        fixture_authority_class=FIXTURE_AUTHORITY_CLASS,
    )
    for model in lifecycle_models:
        model["cross_venue_normalization_handoff_ref"] = handoff[
            "cross_venue_normalization_handoff_id"
        ]

    return {
        "repo_pr_label": "PR127",
        "roadmap_pr_implemented": "PR109",
        "fixture_authority_class": FIXTURE_AUTHORITY_CLASS,
        "deterministic_fixture_time": DETERMINISTIC_FIXTURE_TIME,
        "shared_scope_metadata_records": list(shared_scope_metadata_records),
        "lifecycle_model_records": lifecycle_models,
        "phase_records": phase_records,
        "transition_records": transition_records,
        "placeholder_records": placeholder_records,
        "validation_receipts": validation_receipts,
        "rejection_records": rejection_records,
        "cross_venue_normalization_handoff": handoff,
    }


def _candidate_state(
    *,
    candidate: Mapping[str, Any],
    accepted_index: Mapping[str, Mapping[str, Any]],
    binding_index: Mapping[str, Mapping[str, Any]],
    implementation_index: Mapping[str, Mapping[str, Any]],
    source_change_snapshot: Mapping[str, Any],
) -> tuple[str, str, list[Mapping[str, Any]]]:
    venue_id = str(candidate.get("venue_id", ""))
    if venue_id not in ACTIVE_STAGE1_VENUES:
        return (
            REJECTED_SCOPE_OR_VENUE_MISMATCH,
            "VENUE_NOT_STAGE1_VENUE_SPECIFIC_LIFECYCLE_SCOPE",
            [],
        )

    refs = candidate.get("semantic_support_refs", [])
    if not isinstance(refs, list):
        return (
            REJECTED_SCOPE_OR_VENUE_MISMATCH,
            "SEMANTIC_SUPPORT_REFS_MUST_BE_LIST",
            [],
        )
    support_by_family = {
        str(ref.get("target_semantic_family")): ref
        for ref in refs
        if isinstance(ref, Mapping)
    }
    for family in REQUIRED_SEMANTIC_FAMILIES:
        if family not in support_by_family:
            return (
                MISSING_SUPPORT_STATE_BY_FAMILY[family],
                f"MISSING_{family.upper()}_SEMANTIC_SUPPORT",
                [],
            )

    resolved_support: list[Mapping[str, Any]] = []
    for family in REQUIRED_SEMANTIC_FAMILIES:
        ref = support_by_family[family]
        accepted_id = str(ref.get("accepted_source_evidence_packet_id", ""))
        binding_id = str(ref.get("source_connector_binding_ledger_record_id", ""))
        implementation_id = str(ref.get("connector_implementation_gate_record_id", ""))
        accepted = accepted_index.get(accepted_id)
        if accepted is None:
            return (
                REJECTED_MISSING_ACCEPTED_SOURCE_EVIDENCE,
                "ACCEPTED_SOURCE_EVIDENCE_NOT_FOUND",
                [],
            )
        binding = binding_index.get(binding_id)
        if binding is None:
            return (
                MISSING_SUPPORT_STATE_BY_FAMILY[family],
                f"MISSING_{family.upper()}_CONNECTOR_BINDING_SUPPORT",
                [],
            )
        implementation = implementation_index.get(implementation_id)
        if implementation is None or implementation.get("implementation_gate_state") != (
            "READY_FOR_PR126_FIXTURE_SCOPE_IMPLEMENTATION"
        ):
            return (
                REJECTED_MISSING_CONNECTOR_IMPLEMENTATION_GATE,
                "CONNECTOR_IMPLEMENTATION_GATE_SUPPORT_NOT_FOUND",
                [],
            )
        if _scope_or_linkage_mismatch(
            candidate=candidate,
            family=family,
            accepted=accepted,
            binding=binding,
            implementation=implementation,
        ):
            return (
                REJECTED_SCOPE_OR_VENUE_MISMATCH,
                "VENUE_TARGET_FIELD_OR_SEMANTIC_SURFACE_MISMATCH",
                [],
            )
        if accepted_id in _set(source_change_snapshot, "stale_accepted_packet_ids"):
            return REJECTED_STALE_ACCEPTED_PACKET, "ACCEPTED_PACKET_STALE", []
        if accepted_id in _set(source_change_snapshot, "superseded_accepted_packet_ids"):
            return REJECTED_SUPERSEDED_ACCEPTED_PACKET, "ACCEPTED_PACKET_SUPERSEDED", []
        if accepted_id in _set(source_change_snapshot, "revalidation_due_packet_ids"):
            return REJECTED_REVALIDATION_REQUIRED, "ACCEPTED_PACKET_REVALIDATION_REQUIRED", []
        if binding_id in _set(
            source_change_snapshot,
            "connector_blocking_materiality_binding_ids",
        ):
            return (
                REJECTED_CONNECTOR_BLOCKING_MATERIALITY,
                "CONNECTOR_BLOCKING_MATERIALITY",
                [],
            )
        if binding_id in _set(
            source_change_snapshot,
            "trading_blocking_materiality_binding_ids",
        ):
            return (
                REJECTED_TRADING_BLOCKING_MATERIALITY,
                "TRADING_BLOCKING_MATERIALITY",
                [],
            )
        resolved_support.append(
            {
                "target_semantic_family": family,
                "accepted": accepted,
                "binding": binding,
                "implementation": implementation,
            }
        )

    return (
        READY_FOR_PR127_FIXTURE_SCOPE_MODEL,
        "PR127_FIXTURE_SCOPE_LIFECYCLE_MODEL_READY",
        resolved_support,
    )


def _scope_or_linkage_mismatch(
    *,
    candidate: Mapping[str, Any],
    family: str,
    accepted: Mapping[str, Any],
    binding: Mapping[str, Any],
    implementation: Mapping[str, Any],
) -> bool:
    venue_id = str(candidate["venue_id"])
    for record in (accepted, binding, implementation):
        if record.get("venue_id") != venue_id:
            return True
        if record.get("target_semantic_family") != family:
            return True
    for field in ("target_field_path", "semantic_surface_id"):
        if accepted.get(field) != binding.get(field):
            return True
        if accepted.get(field) != implementation.get(field):
            return True
    if accepted.get("accepted_source_evidence_packet_id") != binding.get(
        "accepted_source_evidence_packet_id"
    ):
        return True
    if accepted.get("accepted_source_evidence_packet_id") != implementation.get(
        "accepted_source_evidence_packet_id"
    ):
        return True
    if binding.get("source_connector_binding_ledger_record_id") != implementation.get(
        "source_connector_binding_ledger_record_id"
    ):
        return True
    return False


def _model_record(
    *,
    candidate: Mapping[str, Any],
    receipt: Mapping[str, Any],
    support_refs: Sequence[Mapping[str, Any]],
    source_change_snapshot: Mapping[str, Any],
) -> dict[str, Any]:
    venue_id = str(candidate["venue_id"])
    model_id = f"PR127_LIFECYCLE_MODEL_{venue_id}_FIXTURE"
    record: dict[str, Any] = {
        "per_venue_execution_lifecycle_model_id": model_id,
        "fixture_authority_class": FIXTURE_AUTHORITY_CLASS,
        "production_execution_lifecycle_authority": False,
        "future_production_launch_path_preserved": True,
        "future_cross_venue_normalization_path_preserved": True,
        "venue_id": venue_id,
        "platform_scope": str(candidate["platform_scope"]),
        "model_scope": "PR127_STAGE1_PREDICTION_MARKETS_FIXTURE_SCOPE",
        "upstream_connector_implementation_gate_receipt_id": str(
            support_refs[0]["implementation"]["connector_implementation_gate_record_id"]
        ),
        "upstream_connector_semantic_binding_record_ids": [
            str(ref["binding"]["source_connector_binding_ledger_record_id"])
            for ref in support_refs
        ],
        "upstream_accepted_source_evidence_packet_ids": [
            str(ref["accepted"]["accepted_source_evidence_packet_id"])
            for ref in support_refs
        ],
        "upstream_source_change_snapshot_id": str(
            source_change_snapshot["source_change_snapshot_id"]
        ),
        "lifecycle_phase_records": [],
        "lifecycle_transition_records": [],
        "fill_integrity_placeholder_ref": "",
        "cashflow_pnl_placeholder_ref": "",
        "latency_component_placeholder_ref": "",
        "settlement_finality_placeholder_ref": "",
        "reconciliation_placeholder_ref": "",
        "cross_venue_normalization_handoff_ref": "",
        "validation_receipt_id": str(receipt["validation_receipt_id"]),
        "lifecycle_model_state": READY_FOR_PR127_FIXTURE_SCOPE_MODEL,
        "deterministic_fixture_time": DETERMINISTIC_FIXTURE_TIME,
        "quantum_forward_metadata_placeholder": {
            "future_quantum_aware_latency_candidate_set_metadata_allowed": True,
            "quantum_backend_execution_count": 0,
            "quantum_simulator_execution_count": 0,
            "optimizer_execution_count": 0,
            "quantum_advantage_claim_created": False,
            "latency_superiority_claim_created": False,
            "execution_superiority_claim_created": False,
            "profit_evidence_created": False,
        },
    }
    record.update(_false_authority_flags())
    return record


def _validation_receipt(
    candidate: Mapping[str, Any],
    lifecycle_model_state: str,
    reason_code: str,
) -> dict[str, Any]:
    ready = lifecycle_model_state == READY_FOR_PR127_FIXTURE_SCOPE_MODEL
    receipt = {
        "validation_receipt_id": (
            f"PR127_LIFECYCLE_VALIDATION_{candidate['lifecycle_model_candidate_id']}"
        ),
        "lifecycle_model_candidate_id": str(candidate["lifecycle_model_candidate_id"]),
        "venue_id": str(candidate.get("venue_id", "")),
        "lifecycle_validation_state": (
            "VALIDATED_PR127_FIXTURE_SCOPE_MODEL" if ready else lifecycle_model_state
        ),
        "lifecycle_model_state": lifecycle_model_state,
        "decision_reason_code": reason_code,
        "fixture_authority_class": FIXTURE_AUTHORITY_CLASS,
        "production_execution_lifecycle_authority": False,
        "future_cross_venue_normalization_path_preserved": True,
        "future_production_launch_path_preserved": True,
        "deterministic_fixture_time": DETERMINISTIC_FIXTURE_TIME,
    }
    receipt.update(_false_authority_flags())
    return receipt


def _rejection_record(
    candidate: Mapping[str, Any],
    receipt: Mapping[str, Any],
    lifecycle_model_state: str,
    reason_code: str,
) -> dict[str, Any]:
    rejection = {
        "rejection_id": f"PR127_LIFECYCLE_REJECTION_{candidate['lifecycle_model_candidate_id']}",
        "validation_receipt_id": str(receipt["validation_receipt_id"]),
        "lifecycle_model_candidate_id": str(candidate["lifecycle_model_candidate_id"]),
        "venue_id": str(candidate.get("venue_id", "")),
        "lifecycle_model_state": lifecycle_model_state,
        "rejection_reason_code": reason_code,
        "fixture_authority_class": FIXTURE_AUTHORITY_CLASS,
        "production_execution_lifecycle_authority": False,
        "future_cross_venue_normalization_path_preserved": True,
        "future_production_launch_path_preserved": True,
        "deterministic_fixture_time": DETERMINISTIC_FIXTURE_TIME,
    }
    rejection.update(_false_authority_flags())
    return rejection


def _false_authority_flags() -> dict[str, bool]:
    return {field: False for field in AUTHORITY_FALSE_FLAGS}


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON root must be an object: {path}")
    return value


def _records(payload: Mapping[str, Any], key: str) -> list[dict[str, Any]]:
    records = payload.get(key)
    if not isinstance(records, list):
        raise ValueError(f"{key} must be an array")
    return [dict(record) for record in records]


def _first_record(payload: Mapping[str, Any], key: str) -> dict[str, Any]:
    records = _records(payload, key)
    if len(records) != 1:
        raise ValueError(f"{key} must contain exactly one record")
    return records[0]


def _index_by(records: Sequence[Mapping[str, Any]], key: str) -> dict[str, Mapping[str, Any]]:
    return {
        str(record[key]): deepcopy(dict(record))
        for record in records
        if isinstance(record.get(key), str)
    }


def _set(record: Mapping[str, Any], key: str) -> set[str]:
    value = record.get(key, [])
    if not isinstance(value, list):
        return set()
    return {str(item) for item in value}
