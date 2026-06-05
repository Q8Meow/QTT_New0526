def test_binding_family_collapse(summary, records):
    rows = records("PR162R_B_BindingActionFamilyCollapse.report.json")
    families = {row["binding_family"] for row in rows}
    assert summary["binding_family_collapse_created"] is True
    assert len(families) >= 12
    assert all(not row["raw_missing_action_uncollapsed_flag"] for row in rows)
