from __future__ import annotations

from ._helpers import rows


def test_policy_parameter_registry_centralizes_required_groups() -> None:
    groups: dict[str, dict[str, object]] = {}
    for row in rows("rp5d_policy_params.jsonl"):
        groups.setdefault(str(row["parameter_group"]), {})[str(row["parameter_name"])] = row["parameter_value"]

    for required in (
        "coverage_caps",
        "materialization_rules",
        "edge_capture_readiness_rules",
        "execution_readiness_contracts",
        "quantum_compatibility_rules",
        "external_research_policy",
        "path_safety_policy",
        "validation_timeout_policy",
    ):
        assert required in groups

    assert groups["materialization_rules"]["final_unknown_state_allowed"] is False
    assert groups["path_safety_policy"]["max_generated_filename_chars"] == 90
