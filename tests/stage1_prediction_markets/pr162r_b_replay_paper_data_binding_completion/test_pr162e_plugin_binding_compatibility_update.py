def test_pr162e_plugin_binding_compatibility_update(summary, records):
    rows = records("PR162R_B_PR162EPluginBindingCompatibilityUpdate.report.json")
    assert len(rows) == summary["pr162e_compatibility_update_rows"] == 6502
