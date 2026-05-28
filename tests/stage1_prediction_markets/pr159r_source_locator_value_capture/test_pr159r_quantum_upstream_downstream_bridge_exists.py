def test_pr159r_quantum_upstream_downstream_bridge_exists(pr159r_artifacts):
    first = pr159r_artifacts["quantum"]["records"][0]
    assert first["upstream_PR82_quantum_applicability_ref_or_null"]
    assert first["future_optimizer_arbitration_route"]

