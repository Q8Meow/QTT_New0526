from tests.stage1_prediction_markets.pr157_completion_materialization_bridge.test_support import atomic_records


def test_pr157_fill_paths_have_exact_steps_acceptance_criteria_and_unblock_validator():
    plans = [plan for record in atomic_records() for plan in record["unresolved_field_fill_plans"]]
    assert plans
    assert all(plan["exact_steps_to_fill"] for plan in plans)
    assert all(plan["exact_acceptance_criteria"] for plan in plans)
    assert all(plan["validator_that_will_unblock"] for plan in plans)
