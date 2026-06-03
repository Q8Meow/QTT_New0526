"""Acquisition-first effort allocation audit."""

from __future__ import annotations

from typing import Any


def acquisition_effort_records() -> list[dict[str, Any]]:
    rows = [
        ("MASTER_PLAN_FORMULA_ALGORITHM_PARAMETER_QUANTUM_MINING", 28),
        ("MANDATORY_EXTERNAL_SOURCE_SCOUTING", 24),
        ("FORMULA_ALGORITHM_PARAMETER_DATASET_ACQUISITION", 30),
        ("QUANTUM_FORMULATION_ACQUISITION", 16),
        ("REPORT_PLUMBING_AND_VALIDATOR_INTEGRATION", 6),
    ]
    total = sum(units for _, units in rows)
    acquisition = sum(units for name, units in rows if name != "REPORT_PLUMBING_AND_VALIDATOR_INTEGRATION")
    return [
        {
            "effort_bucket": name,
            "effort_units": units,
            "acquisition_first_bucket_flag": name != "REPORT_PLUMBING_AND_VALIDATOR_INTEGRATION",
            "allocation_basis": "PR162D_R1_OWNER_DIRECTED_ACQUISITION_FIRST_SCOPE",
            "live_order_authority": False,
            "acquisition_first_effort_ratio": round(acquisition / total, 4),
        }
        for name, units in rows
    ]


def acquisition_first_effort_ratio(records: list[dict[str, Any]]) -> float:
    total = sum(float(record["effort_units"]) for record in records)
    acquisition = sum(
        float(record["effort_units"])
        for record in records
        if record["acquisition_first_bucket_flag"]
    )
    return round(acquisition / total, 4)
