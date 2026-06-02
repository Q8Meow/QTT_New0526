from src.qtt.stage1_prediction_markets.multisource_safe_nonlive_dataset_expansion_strict_qku_coverage import constants as c

from .test_support import report


def test_pr162c_no_scattered_guardrail_strings():
    dictionary = report("PR162C_SharedDictionary.report.json")["shared_dictionary"]
    scan = report("PR162C_ForbiddenAuthorityScan.report.json")["records"][0]

    assert dictionary["blocker_codes"] == list(c.BLOCKER_CODES)
    assert dictionary["source_classes"] == list(c.SOURCE_CLASSES)
    assert dictionary["qku_execution_classes"] == list(c.QKU_EXECUTION_CLASSES)
    assert scan["no_scattered_hardcoded_policy_scan_status"] == "PASS"
