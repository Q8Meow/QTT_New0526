"""Unit normalization records for PR162D formulas and values."""

from __future__ import annotations


def unit_normalization_records() -> list[dict[str, object]]:
    return [
        {
            "normalization_rule_id": "PR162D-UNIT-NORMALIZATION-PROBABILITY",
            "input_units": ["cents", "normalized_price", "probability"],
            "output_unit": "probability",
            "normalization_rule": "price_cents/100 when cents; identity when normalized probability",
        },
        {
            "normalization_rule_id": "PR162D-UNIT-NORMALIZATION-EXPECTED-VALUE",
            "input_units": ["currency", "payout_fraction", "fee_fraction"],
            "output_unit": "expected_value",
            "normalization_rule": "all monetary candidates normalized to payout unit before replay/paper",
        },
        {
            "normalization_rule_id": "PR162D-UNIT-NORMALIZATION-QUBO",
            "input_units": ["unitless", "penalty_weight", "objective_weight"],
            "output_unit": "energy",
            "normalization_rule": "coefficient vectors are numeric finite local-smoke coefficients",
        },
    ]
