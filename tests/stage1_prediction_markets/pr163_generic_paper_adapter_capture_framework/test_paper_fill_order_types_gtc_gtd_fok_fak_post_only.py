def test_order_type_scenarios_are_covered(records):
    rows = records("PR163_PaperScenarioCoverageMatrix.report.json")
    by_scenario = {row["scenario_id"]: row for row in rows}
    for scenario in ("FOK_FULL_FILL", "FOK_KILL_NO_FILL", "FAK_PARTIAL_FILL_CANCEL_RESIDUAL", "POST_ONLY_REJECT_MARKETABLE", "GTD_EXPIRE", "GTC_REST_THEN_CANCEL"):
        assert by_scenario[scenario]["scenario_rows"] > 0
