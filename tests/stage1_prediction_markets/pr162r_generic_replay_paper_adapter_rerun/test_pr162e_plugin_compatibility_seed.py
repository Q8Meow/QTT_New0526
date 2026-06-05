def test_pr162e_plugin_compatibility_seed(summary, records):
    rows = records("PR162R_PR162EPluginReplayPaperCompatibilitySeed.report.json")
    assert len(rows) == summary["pr162e_compatibility_seed_count"]
    assert rows
    assert all(row["plugin_intake_recommendation"] == "PR162E_FORMULA_ALGORITHM_QUANTUM_PLUGIN_INTAKE" for row in rows)
    assert all(row["no_live_order_authority"] is True for row in rows)
