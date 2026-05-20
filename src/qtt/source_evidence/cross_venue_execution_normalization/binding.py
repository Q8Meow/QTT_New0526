from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any, Mapping, Sequence

from src.qtt.source_evidence.execution_lifecycle.phases import (
    GENERIC_FIXTURE_PHASE_FAMILIES,
)
from src.qtt.source_evidence.execution_lifecycle.transitions import (
    GENERIC_FIXTURE_TRANSITION_FAMILIES,
)

from .comparability import build_arbitrage_comparability_preconditions
from .handoff import build_downstream_handoff
from .placeholders import build_placeholder_normalization_records
from .taxonomy import (
    ACTIVE_STAGE1_VENUES,
    DETERMINISTIC_FIXTURE_TIME,
    FIXTURE_AUTHORITY_CLASS,
    PLACEHOLDER_REJECTION_STATE_BY_DIMENSION,
    READY_FOR_PR128_FIXTURE_SCOPE_NORMALIZATION,
    REJECTED_CONNECTOR_BLOCKING_MATERIALITY,
    REJECTED_MISSING_ACCEPTED_SOURCE_EVIDENCE,
    REJECTED_MISSING_PER_VENUE_LIFECYCLE_MODEL,
    REJECTED_MISSING_PHASE_MAPPING,
    REJECTED_MISSING_PR127_HANDOFF,
    REJECTED_MISSING_TRANSITION_MAPPING,
    REJECTED_REVALIDATION_REQUIRED,
    REJECTED_SCOPE_OR_VENUE_MISMATCH,
    REJECTED_STALE_ACCEPTED_PACKET,
    REJECTED_SUPERSEDED_ACCEPTED_PACKET,
    REJECTED_TRADING_BLOCKING_MATERIALITY,
    REQUIRED_NORMALIZATION_DIMENSIONS,
    REQUIRED_PLACEHOLDER_DIMENSIONS,
    SHARED_SCOPE_METADATA_VENUES,
    build_taxonomy_record,
    false_authority_flags,
)


PR127_FIXTURE_DIR = Path("tests/fixtures/source_evidence/pr127_execution_lifecycle")
GENERATED_DIR = Path("docs/master_plan/source_evidence/generated")
PR127_MODELS_REPORT = GENERATED_DIR / "PerVenueExecutionLifecycleModels.report.json"
PR127_HANDOFF_REPORT = (
    GENERATED_DIR / "PerVenueExecutionLifecycleCrossVenueNormalizationHandoff.report.json"
)


def load_fixture_inputs(repo_root: Path) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    fixture_dir = repo_root / PR127_FIXTURE_DIR
    accepted_payload = _load_json(
        fixture_dir / "accepted_source_evidence_records.v1.fixture.json"
    )
    return {
        "per_venue_execution_lifecycle_models": _records(
            _load_json(repo_root / PR127_MODELS_REPORT),
            "lifecycle_model_records",
        ),
        "cross_venue_normalization_handoff": _load_json(repo_root / PR127_HANDOFF_REPORT)[
            "handoff"
        ],
        "accepted_source_evidence_records": _records(
            accepted_payload,
            "accepted_source_evidence_records",
        ),
        "shared_scope_metadata_records": _records(
            accepted_payload,
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
            _load_json(
                fixture_dir
                / "connector_implementation_gate_records.v1.fixture.json"
            ),
            "connector_implementation_gate_records",
        ),
    }


def build_cross_venue_execution_normalization_artifacts(
    *,
    per_venue_execution_lifecycle_models: Sequence[Mapping[str, Any]],
    cross_venue_normalization_handoff: Mapping[str, Any] | None,
    accepted_source_evidence_records: Sequence[Mapping[str, Any]],
    connector_semantic_binding_records: Sequence[Mapping[str, Any]],
    source_change_snapshot: Mapping[str, Any],
    connector_implementation_gate_records: Sequence[Mapping[str, Any]],
    shared_scope_metadata_records: Sequence[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    models = [deepcopy(dict(record)) for record in per_venue_execution_lifecycle_models]
    handoff = deepcopy(dict(cross_venue_normalization_handoff or {}))
    state, reason = _normalization_input_state(
        models=models,
        handoff=handoff,
        accepted_source_evidence_records=accepted_source_evidence_records,
        connector_semantic_binding_records=connector_semantic_binding_records,
        source_change_snapshot=source_change_snapshot,
        connector_implementation_gate_records=connector_implementation_gate_records,
        shared_scope_metadata_records=shared_scope_metadata_records,
    )
    validation_receipts = [
        _validation_receipt(
            state=state,
            reason_code=reason,
            venue_ids=[str(record.get("venue_id", "")) for record in models],
        )
    ]
    if state != READY_FOR_PR128_FIXTURE_SCOPE_NORMALIZATION:
        return _empty_artifacts(
            validation_receipts=validation_receipts,
            rejection_records=[
                _rejection_record(
                    state=state,
                    reason_code=reason,
                    validation_receipt_id=validation_receipts[0][
                        "cross_venue_normalization_validation_receipt_id"
                    ],
                )
            ],
        )

    taxonomy_record = build_taxonomy_record()
    phase_bindings = _phase_bindings(models)
    transition_bindings = _transition_bindings(models)
    placeholders = build_placeholder_normalization_records()
    comparability_preconditions = build_arbitrage_comparability_preconditions(
        phase_bindings=phase_bindings,
        transition_bindings=transition_bindings,
    )
    downstream_handoff = build_downstream_handoff(
        phase_bindings=phase_bindings,
        transition_bindings=transition_bindings,
        placeholder_records=placeholders,
        arbitrage_preconditions=comparability_preconditions,
    )
    return {
        "repo_pr_label": "PR128",
        "roadmap_pr_implemented": "PR110",
        "fixture_authority_class": FIXTURE_AUTHORITY_CLASS,
        "deterministic_fixture_time": DETERMINISTIC_FIXTURE_TIME,
        "source_pr127_handoff_id": handoff["cross_venue_normalization_handoff_id"],
        "source_pr127_lifecycle_model_ids": handoff["lifecycle_model_ids"],
        "stage1_venue_ids": list(ACTIVE_STAGE1_VENUES),
        "shared_scope_metadata_records": list(
            deepcopy(list(shared_scope_metadata_records))
        ),
        "taxonomy_records": [taxonomy_record],
        "phase_binding_records": phase_bindings,
        "transition_binding_records": transition_bindings,
        "placeholder_normalization_records": placeholders,
        "arbitrage_comparability_precondition_records": comparability_preconditions,
        "validation_receipts": validation_receipts,
        "rejection_records": [],
        "downstream_handoff": downstream_handoff,
    }


def _normalization_input_state(
    *,
    models: Sequence[Mapping[str, Any]],
    handoff: Mapping[str, Any],
    accepted_source_evidence_records: Sequence[Mapping[str, Any]],
    connector_semantic_binding_records: Sequence[Mapping[str, Any]],
    source_change_snapshot: Mapping[str, Any],
    connector_implementation_gate_records: Sequence[Mapping[str, Any]],
    shared_scope_metadata_records: Sequence[Mapping[str, Any]],
) -> tuple[str, str]:
    if not handoff:
        return REJECTED_MISSING_PR127_HANDOFF, "PR127_CROSS_VENUE_HANDOFF_MISSING"
    if handoff.get("source_repo_pr_label") != "PR127":
        return REJECTED_MISSING_PR127_HANDOFF, "PR127_HANDOFF_SOURCE_LABEL_MISMATCH"
    if handoff.get("future_roadmap_pr") != "PR110":
        return REJECTED_MISSING_PR127_HANDOFF, "PR127_HANDOFF_NOT_TARGETED_TO_PR110"
    if handoff.get("production_cross_venue_normalization_authority") is not False:
        return REJECTED_SCOPE_OR_VENUE_MISMATCH, "HANDOFF_PRODUCTION_AUTHORITY_TRUE"
    if _set(handoff, "venue_ids_in_scope") != set(ACTIVE_STAGE1_VENUES):
        return REJECTED_SCOPE_OR_VENUE_MISMATCH, "HANDOFF_STAGE1_VENUE_SET_MISMATCH"

    model_by_venue = {str(record.get("venue_id", "")): record for record in models}
    if set(model_by_venue) != set(ACTIVE_STAGE1_VENUES):
        return (
            REJECTED_MISSING_PER_VENUE_LIFECYCLE_MODEL,
            "ACTIVE_STAGE1_VENUE_LIFECYCLE_MODEL_SET_MISMATCH",
        )
    if any(venue in model_by_venue for venue in SHARED_SCOPE_METADATA_VENUES):
        return REJECTED_SCOPE_OR_VENUE_MISMATCH, "SHARED_SCOPE_USED_AS_VENUE_MODEL"
    if _set(handoff, "lifecycle_model_ids") != {
        str(record["per_venue_execution_lifecycle_model_id"]) for record in models
    }:
        return REJECTED_SCOPE_OR_VENUE_MISMATCH, "HANDOFF_LIFECYCLE_MODEL_ID_MISMATCH"
    if not any(
        record.get("venue_id") == "PREDICTION_MARKETS_GENERAL"
        and record.get("shared_scope_only") is True
        for record in shared_scope_metadata_records
    ):
        return REJECTED_SCOPE_OR_VENUE_MISMATCH, "PREDICTION_MARKETS_GENERAL_SHARED_SCOPE_MISSING"

    required_dimensions = set(REQUIRED_NORMALIZATION_DIMENSIONS)
    if _set(handoff, "required_future_normalization_dimensions") != required_dimensions:
        return REJECTED_SCOPE_OR_VENUE_MISMATCH, "HANDOFF_NORMALIZATION_DIMENSION_MISMATCH"
    placeholder_support = _set(
        handoff,
        "placeholder_semantic_families_requiring_future_source_support",
    )
    for dimension in REQUIRED_PLACEHOLDER_DIMENSIONS:
        if dimension not in placeholder_support:
            return (
                PLACEHOLDER_REJECTION_STATE_BY_DIMENSION[dimension],
                f"MISSING_{dimension.upper()}_NORMALIZATION_SUPPORT",
            )

    accepted_index = _index_by(
        accepted_source_evidence_records,
        "accepted_source_evidence_packet_id",
    )
    binding_index = _index_by(
        connector_semantic_binding_records,
        "source_connector_binding_ledger_record_id",
    )
    implementation_by_binding_id = {
        str(record["source_connector_binding_ledger_record_id"]): record
        for record in connector_implementation_gate_records
        if isinstance(record.get("source_connector_binding_ledger_record_id"), str)
    }
    for model in models:
        state, reason = _model_support_state(
            model=model,
            accepted_index=accepted_index,
            binding_index=binding_index,
            implementation_by_binding_id=implementation_by_binding_id,
            source_change_snapshot=source_change_snapshot,
        )
        if state != READY_FOR_PR128_FIXTURE_SCOPE_NORMALIZATION:
            return state, reason
    return (
        READY_FOR_PR128_FIXTURE_SCOPE_NORMALIZATION,
        "PR128_FIXTURE_SCOPE_CROSS_VENUE_NORMALIZATION_READY",
    )


def _model_support_state(
    *,
    model: Mapping[str, Any],
    accepted_index: Mapping[str, Mapping[str, Any]],
    binding_index: Mapping[str, Mapping[str, Any]],
    implementation_by_binding_id: Mapping[str, Mapping[str, Any]],
    source_change_snapshot: Mapping[str, Any],
) -> tuple[str, str]:
    venue_id = str(model.get("venue_id", ""))
    if venue_id not in ACTIVE_STAGE1_VENUES:
        return REJECTED_SCOPE_OR_VENUE_MISMATCH, "MODEL_VENUE_NOT_STAGE1_ACTIVE"
    if model.get("lifecycle_model_state") != "READY_FOR_PR127_FIXTURE_SCOPE_MODEL":
        return REJECTED_MISSING_PER_VENUE_LIFECYCLE_MODEL, "PR127_MODEL_NOT_READY"

    phases = model.get("lifecycle_phase_records")
    if not isinstance(phases, list) or not phases:
        return REJECTED_MISSING_PHASE_MAPPING, "LIFECYCLE_PHASE_RECORDS_MISSING"
    if {str(record.get("phase_family")) for record in phases} != set(
        GENERIC_FIXTURE_PHASE_FAMILIES
    ):
        return REJECTED_MISSING_PHASE_MAPPING, "LIFECYCLE_PHASE_FAMILY_SET_MISMATCH"
    if any(str(record.get("venue_id")) != venue_id for record in phases):
        return REJECTED_SCOPE_OR_VENUE_MISMATCH, "PHASE_VENUE_ID_MISMATCH"

    transitions = model.get("lifecycle_transition_records")
    transition_family_set = {
        transition_family
        for transition_family, _from_phase, _to_phase in GENERIC_FIXTURE_TRANSITION_FAMILIES
    }
    if not isinstance(transitions, list) or not transitions:
        return REJECTED_MISSING_TRANSITION_MAPPING, "LIFECYCLE_TRANSITION_RECORDS_MISSING"
    if {str(record.get("transition_family")) for record in transitions} != transition_family_set:
        return (
            REJECTED_MISSING_TRANSITION_MAPPING,
            "LIFECYCLE_TRANSITION_FAMILY_SET_MISMATCH",
        )
    if any(str(record.get("venue_id")) != venue_id for record in transitions):
        return REJECTED_SCOPE_OR_VENUE_MISMATCH, "TRANSITION_VENUE_ID_MISMATCH"

    accepted_ids = model.get("upstream_accepted_source_evidence_packet_ids")
    binding_ids = model.get("upstream_connector_semantic_binding_record_ids")
    if not isinstance(accepted_ids, list) or not accepted_ids:
        return REJECTED_MISSING_ACCEPTED_SOURCE_EVIDENCE, "MODEL_ACCEPTED_SOURCE_IDS_MISSING"
    if not isinstance(binding_ids, list) or not binding_ids:
        return REJECTED_SCOPE_OR_VENUE_MISMATCH, "MODEL_CONNECTOR_BINDING_IDS_MISSING"

    for accepted_id in [str(value) for value in accepted_ids]:
        accepted = accepted_index.get(accepted_id)
        if accepted is None:
            return (
                REJECTED_MISSING_ACCEPTED_SOURCE_EVIDENCE,
                "ACCEPTED_SOURCE_EVIDENCE_NOT_FOUND",
            )
        if accepted.get("venue_id") != venue_id:
            return REJECTED_SCOPE_OR_VENUE_MISMATCH, "ACCEPTED_PACKET_VENUE_MISMATCH"
        if accepted.get("fixture_authority_class") != FIXTURE_AUTHORITY_CLASS:
            return REJECTED_SCOPE_OR_VENUE_MISMATCH, "ACCEPTED_PACKET_NOT_FIXTURE"
        if accepted.get("production_external_fact_authority") is not False:
            return REJECTED_SCOPE_OR_VENUE_MISMATCH, "ACCEPTED_PACKET_PRODUCTION_AUTHORITY_TRUE"
        if accepted_id in _set(source_change_snapshot, "stale_accepted_packet_ids"):
            return REJECTED_STALE_ACCEPTED_PACKET, "ACCEPTED_PACKET_STALE"
        if accepted_id in _set(source_change_snapshot, "superseded_accepted_packet_ids"):
            return REJECTED_SUPERSEDED_ACCEPTED_PACKET, "ACCEPTED_PACKET_SUPERSEDED"
        if accepted_id in _set(source_change_snapshot, "revalidation_due_packet_ids"):
            return (
                REJECTED_REVALIDATION_REQUIRED,
                "ACCEPTED_PACKET_REVALIDATION_REQUIRED",
            )

    for binding_id in [str(value) for value in binding_ids]:
        binding = binding_index.get(binding_id)
        implementation = implementation_by_binding_id.get(binding_id)
        if binding is None:
            return REJECTED_SCOPE_OR_VENUE_MISMATCH, "CONNECTOR_BINDING_NOT_FOUND"
        if binding.get("venue_id") != venue_id:
            return REJECTED_SCOPE_OR_VENUE_MISMATCH, "CONNECTOR_BINDING_VENUE_MISMATCH"
        if binding.get("production_connector_semantic_authority") is not False:
            return REJECTED_SCOPE_OR_VENUE_MISMATCH, "CONNECTOR_BINDING_PRODUCTION_AUTHORITY_TRUE"
        if implementation is None or implementation.get("implementation_gate_state") != (
            "READY_FOR_PR126_FIXTURE_SCOPE_IMPLEMENTATION"
        ):
            return REJECTED_SCOPE_OR_VENUE_MISMATCH, "CONNECTOR_IMPLEMENTATION_GATE_NOT_READY"
        if binding_id in _set(
            source_change_snapshot,
            "connector_blocking_materiality_binding_ids",
        ):
            return REJECTED_CONNECTOR_BLOCKING_MATERIALITY, "CONNECTOR_BLOCKING_MATERIALITY"
        if binding_id in _set(
            source_change_snapshot,
            "trading_blocking_materiality_binding_ids",
        ):
            return REJECTED_TRADING_BLOCKING_MATERIALITY, "TRADING_BLOCKING_MATERIALITY"
    return (
        READY_FOR_PR128_FIXTURE_SCOPE_NORMALIZATION,
        "MODEL_SUPPORT_READY_FOR_PR128_NORMALIZATION",
    )


def _phase_bindings(models: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for model in sorted(models, key=lambda record: str(record["venue_id"])):
        model_id = str(model["per_venue_execution_lifecycle_model_id"])
        venue_id = str(model["venue_id"])
        for phase in sorted(model["lifecycle_phase_records"], key=lambda record: int(record["phase_ordinal"])):
            record = {
                "cross_venue_phase_binding_id": (
                    f"PR128_PHASE_BINDING_{venue_id}_{int(phase['phase_ordinal']):02d}_{phase['phase_family']}"
                ),
                "fixture_authority_class": FIXTURE_AUTHORITY_CLASS,
                "taxonomy_authority_class": FIXTURE_AUTHORITY_CLASS,
                "production_cross_venue_normalization_authority": False,
                "venue_id": venue_id,
                "per_venue_execution_lifecycle_model_id": model_id,
                "source_execution_phase_id": str(
                    phase["execution_lifecycle_phase_record_id"]
                ),
                "normalized_execution_phase_family": str(phase["phase_family"]),
                "normalization_dimension": "execution_phase_taxonomy",
                "accepted_source_evidence_required_flag": True,
                "production_value_populated": False,
                "phase_binding_state": READY_FOR_PR128_FIXTURE_SCOPE_NORMALIZATION,
                "deterministic_fixture_time": DETERMINISTIC_FIXTURE_TIME,
                "future_production_launch_path_preserved": True,
            }
            record.update(false_authority_flags())
            records.append(record)
    return records


def _transition_bindings(models: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for model in sorted(models, key=lambda record: str(record["venue_id"])):
        model_id = str(model["per_venue_execution_lifecycle_model_id"])
        venue_id = str(model["venue_id"])
        for transition in sorted(
            model["lifecycle_transition_records"],
            key=lambda record: int(record["transition_ordinal"]),
        ):
            record = {
                "cross_venue_transition_binding_id": (
                    f"PR128_TRANSITION_BINDING_{venue_id}_{int(transition['transition_ordinal']):02d}_{transition['transition_family']}"
                ),
                "fixture_authority_class": FIXTURE_AUTHORITY_CLASS,
                "taxonomy_authority_class": FIXTURE_AUTHORITY_CLASS,
                "production_cross_venue_normalization_authority": False,
                "venue_id": venue_id,
                "per_venue_execution_lifecycle_model_id": model_id,
                "source_execution_transition_id": str(
                    transition["execution_lifecycle_transition_record_id"]
                ),
                "normalized_execution_transition_family": str(
                    transition["transition_family"]
                ),
                "normalization_dimension": "execution_transition_taxonomy",
                "accepted_source_evidence_required_flag": True,
                "production_value_populated": False,
                "transition_binding_state": READY_FOR_PR128_FIXTURE_SCOPE_NORMALIZATION,
                "deterministic_fixture_time": DETERMINISTIC_FIXTURE_TIME,
                "future_production_launch_path_preserved": True,
            }
            record.update(false_authority_flags())
            records.append(record)
    return records


def _validation_receipt(
    *,
    state: str,
    reason_code: str,
    venue_ids: Sequence[str],
) -> dict[str, Any]:
    ready = state == READY_FOR_PR128_FIXTURE_SCOPE_NORMALIZATION
    receipt = {
        "cross_venue_normalization_validation_receipt_id": (
            "PR128_CROSS_VENUE_NORMALIZATION_VALIDATION_RECEIPT_FIXTURE_V1"
            if ready
            else f"PR128_CROSS_VENUE_NORMALIZATION_VALIDATION_RECEIPT_{state}"
        ),
        "fixture_authority_class": FIXTURE_AUTHORITY_CLASS,
        "normalization_validation_state": (
            "VALIDATED_PR128_FIXTURE_SCOPE_NORMALIZATION" if ready else state
        ),
        "normalization_state": state,
        "decision_reason_code": reason_code,
        "venue_ids_in_scope": list(venue_ids),
        "production_cross_venue_normalization_authority": False,
        "production_arbitrage_comparability_authority": False,
        "deterministic_fixture_time": DETERMINISTIC_FIXTURE_TIME,
        "future_production_launch_path_preserved": True,
    }
    receipt.update(false_authority_flags())
    return receipt


def _rejection_record(
    *,
    state: str,
    reason_code: str,
    validation_receipt_id: str,
) -> dict[str, Any]:
    rejection = {
        "cross_venue_execution_normalization_rejection_id": (
            f"PR128_CROSS_VENUE_NORMALIZATION_REJECTION_{state}"
        ),
        "cross_venue_normalization_validation_receipt_id": validation_receipt_id,
        "fixture_authority_class": FIXTURE_AUTHORITY_CLASS,
        "normalization_state": state,
        "rejection_reason_code": reason_code,
        "production_cross_venue_normalization_authority": False,
        "production_arbitrage_comparability_authority": False,
        "deterministic_fixture_time": DETERMINISTIC_FIXTURE_TIME,
        "future_production_launch_path_preserved": True,
    }
    rejection.update(false_authority_flags())
    return rejection


def _empty_artifacts(
    *,
    validation_receipts: Sequence[Mapping[str, Any]],
    rejection_records: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    return {
        "repo_pr_label": "PR128",
        "roadmap_pr_implemented": "PR110",
        "fixture_authority_class": FIXTURE_AUTHORITY_CLASS,
        "deterministic_fixture_time": DETERMINISTIC_FIXTURE_TIME,
        "source_pr127_handoff_id": None,
        "source_pr127_lifecycle_model_ids": [],
        "stage1_venue_ids": list(ACTIVE_STAGE1_VENUES),
        "shared_scope_metadata_records": [],
        "taxonomy_records": [],
        "phase_binding_records": [],
        "transition_binding_records": [],
        "placeholder_normalization_records": [],
        "arbitrage_comparability_precondition_records": [],
        "validation_receipts": list(validation_receipts),
        "rejection_records": list(rejection_records),
        "downstream_handoff": None,
    }


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON root must be an object: {path}")
    return value


def _records(payload: Mapping[str, Any], key: str) -> list[dict[str, Any]]:
    records = payload.get(key)
    if not isinstance(records, list):
        raise ValueError(f"{key} must be an array")
    return [deepcopy(dict(record)) for record in records]


def _first_record(payload: Mapping[str, Any], key: str) -> dict[str, Any]:
    records = _records(payload, key)
    if len(records) != 1:
        raise ValueError(f"{key} must contain exactly one record")
    return records[0]


def _index_by(
    records: Sequence[Mapping[str, Any]],
    key: str,
) -> dict[str, Mapping[str, Any]]:
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
