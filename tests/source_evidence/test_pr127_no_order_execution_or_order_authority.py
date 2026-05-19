from tests.source_evidence.pr127_execution_lifecycle_support import (
    main_report,
    model_records,
)


def test_pr127_no_order_execution_or_order_authority():
    report = main_report()

    assert report["production_order_authority_count"] == 0
    assert report["order_authority_created"] is False
    assert report["replay_paper_results_created_count"] == 0
    for model in model_records():
        assert model["order_execution_allowed_flag"] is False
        assert model["order_routing_authority_allowed_flag"] is False
        assert model["replay_paper_execution_allowed_flag"] is False
