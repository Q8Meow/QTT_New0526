from __future__ import annotations

from ._helpers import rows


def test_vs1_policy_parameter_registry_centralizes_caps_gates_and_no_pnl_policy():
    params = rows("vs1_policy_parameter_registry.jsonl")
    names = {row["parameter_name"]: row for row in params}

    assert names["max_selected_identities"]["value_decimal_string"] == "50"
    assert names["configured_min_fill_probability"]["parameter_role"] == "execution_gates"
    assert names["gate_relaxation_to_force_pnl_allowed"]["policy_value_string"] == "false"
    assert names["coefficient_normalization_policy"]["policy_value_string"] == "UNIT_NORMALIZED_FOR_FIXTURE_ONLY"
    assert all(row["fixture_only_flag"] is True for row in params)
    assert all(row["live_default_flag"] is False for row in params)
