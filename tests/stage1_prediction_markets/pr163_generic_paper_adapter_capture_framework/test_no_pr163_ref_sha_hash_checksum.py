from src.qtt.stage1_prediction_markets.pr163_generic_paper_adapter_capture_framework.authority_policy import (
    validate_pr163_ref,
)


def test_pr163_created_refs_are_plain_text(records):
    for filename in (
        "PR163_PaperAdapterInputRegistry.report.json",
        "PR163_PaperDecisionIntentRegistry.report.json",
        "PR163_PaperOrderIntentRegistry.report.json",
        "PR163_PaperCaptureEventRegistry.report.json",
    ):
        for row in records(filename)[:100]:
            for key, value in row.items():
                if isinstance(value, str) and key.endswith("_ref") and value.startswith("PR163_"):
                    assert validate_pr163_ref(value).ok
