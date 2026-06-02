from src.qtt.stage1_prediction_markets.multisource_safe_nonlive_dataset_expansion_strict_qku_coverage import constants as c

from .test_support import records, report


def test_pr162c_pr162b_handoff_all_requirements_classified():
    summary = report("PR162C_FinalSummary.report.json")
    ledger = records("PR162C_DataRequirementClassificationLedger.report.json")
    proofs = records("PR162C_StrictQKUCoverageProofMatrix.report.json")

    assert summary["data_requirement_total"] == 6502
    assert summary["unclassified_requirement_count"] == 0
    assert len(ledger) == 6502
    assert len(proofs) == 6502
    assert {record["terminal_status"] for record in ledger} <= set(c.TERMINAL_REQUIREMENT_STATUSES)
