from src.qtt.stage1_prediction_markets.pr164_review_provenance_qku_canonical_coverage_audit.execution_cost_component_model import EXECUTION_COST_COMPONENTS
from src.qtt.stage1_prediction_markets.pr164_review_provenance_qku_canonical_coverage_audit.tests_support import load_records, summary


def test_pr164_execution_cost_component_coverage():
    rows = load_records("PR164_ExecutionCostComponentCoverage.report.json")
    assert len(rows) == summary()["execution_cost_component_rows"]
    for row in rows[:100]:
        assert row["expected_net_profit_candidate_formula"]
        assert all(row[component] for component in EXECUTION_COST_COMPONENTS)
