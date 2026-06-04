"""Targeted deterministic micro-materialization for local PR162R-A classification."""

from __future__ import annotations

from typing import Any

from .candidate_loader import candidate_id, candidate_type


def materialize_candidate(record: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    cid = candidate_id(record)
    ctype = candidate_type(record)
    augmented = dict(record)
    ledger: list[dict[str, Any]] = []

    def add(field: str, value: Any, reason: str) -> None:
        if augmented.get(field):
            return
        augmented[field] = value
        ledger.append(
            {
                "materialization_id": f"PR162R_A_MICRO::{cid}::{field}",
                "candidate_id": cid,
                "candidate_type": ctype,
                "field_name": field,
                "materialized_value": value,
                "source_locator": record.get("source_locator"),
                "source_tier": record.get("source_tier"),
                "authority_class": record.get("authority_class", "SOURCE_BACKED_CANDIDATE_LOCAL_AUDIT"),
                "confidence_class": record.get("confidence_class", "SOURCE_BACKED_DETERMINISTIC_LOCAL_INFERENCE"),
                "candidate_or_provisional_flag": True,
                "micro_materialization_reason": reason,
                "replay_paper_route": "PR162R_A_CLASSIFICATION_ONLY_NO_EXECUTION",
                "no_live_order_authority": True,
                "live_order_authority": False,
            }
        )

    if ctype == "ALGORITHM":
        add("input_fields", list(record.get("inputs") or []), "algorithm inputs projected to adapter input_fields")
        add("output_fields", list(record.get("outputs") or []), "algorithm outputs projected to adapter output_fields")
        add("units", "algorithm_output_packet", "algorithm output unit class projected from deterministic_steps")
    elif ctype == "QUANTUM":
        variables = sorted((record.get("variable_definitions") or {}).keys())
        coefficients = sorted((record.get("coefficient_definitions") or {}).keys())
        parameters = sorted((record.get("parameter_definitions") or {}).keys())
        add(
            "input_fields",
            [*variables, *coefficients, *parameters],
            "quantum formulation variables, coefficients, and parameters projected to input_fields",
        )
        add(
            "output_fields",
            ["quantum_objective_value", "classical_comparator_value", "selected_binary_vector_candidate"],
            "quantum comparator outputs projected from objective and comparator mapping",
        )
        add("units", "objective_energy", "QUBO/Ising/BQM/CQM objective uses energy or cost units")
        add(
            "test_vector",
            record.get("local_exact_smoke_test_representation"),
            "local exact representation projected as deterministic non-executed test vector",
        )
    elif ctype == "DATASET":
        add(
            "test_vector",
            {
                "field_mapping_keys": sorted((record.get("field_mapping") or {}).keys()),
                "expected_output_fields": list(record.get("output_fields") or []),
                "dataset_family": record.get("dataset_family"),
            },
            "dataset field mapping projected as deterministic adapter binding test vector",
        )
    return augmented, ledger


def materialize_candidates(records: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    augmented: list[dict[str, Any]] = []
    ledger: list[dict[str, Any]] = []
    for record in records:
        candidate, rows = materialize_candidate(record)
        augmented.append(candidate)
        ledger.extend(rows)
    return augmented, ledger
