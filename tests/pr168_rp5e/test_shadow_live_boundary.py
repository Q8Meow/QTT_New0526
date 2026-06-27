from ._helpers import by_key, read_json, read_jsonl


def test_shadow_handoff_requires_live_surface_and_is_not_pre_live_gate_or_authority() -> None:
    shadow = by_key(read_jsonl("mode_boundary.jsonl"), "runtime_state")[
        "SHADOW_LIVE_CONCURRENT_COMPARISON"
    ]
    report = read_json("to_shadow.report.json")

    assert shadow["requires_live_execution_surface_flag"] is True
    assert shadow["requires_live_receipts_flag"] is True
    assert shadow["pre_live_gate_role_allowed_flag"] is False
    assert shadow["post_live_validation_role_flag"] is True
    assert shadow["order_authority_allowed_in_rp5e_flag"] is False
    assert shadow["no_changed_scope_no_risk_escalation_result"] == "NO_SHADOW_RUN_REQUIRED"
    assert report["order_authority_flag"] is False
