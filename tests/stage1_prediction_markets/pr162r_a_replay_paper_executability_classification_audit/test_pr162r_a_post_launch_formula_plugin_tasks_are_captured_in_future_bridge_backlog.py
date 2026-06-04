from __future__ import annotations


def test_pr162r_a_post_launch_formula_plugin_tasks_are_captured_in_future_bridge_backlog(summary, records):
    bridge = records("PR162R_A_PR162EFormulaPluginFutureBridge.report.json")
    backlog = records("PR162R_A_PostLaunchFormulaPluginRequirementBacklog.report.json")
    assert len(bridge) == summary["post_launch_formula_plugin_future_bridge_count"]
    assert len(backlog) == summary["post_launch_formula_plugin_requirement_backlog_count"]
    assert summary["post_launch_formula_plugin_future_bridge_missing_count"] == 0
    assert summary["post_launch_formula_plugin_requirement_backlog_missing_count"] == 0
