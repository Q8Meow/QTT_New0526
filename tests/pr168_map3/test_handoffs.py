from __future__ import annotations

from tests.pr168_map3._helpers import records


def test_downstream_handoffs_exist_for_required_consumers() -> None:
    for name in (
        "PR168_MAP3_ToRP2.report.json",
        "PR168_MAP3_ToRANK2.report.json",
        "PR168_MAP3_ToPR165B.report.json",
        "PR168_MAP3_ToPR162EQ.report.json",
        "PR168_MAP3_ToDATA1B.report.json",
        "PR168_MAP3_SourceReview.report.json",
    ):
        rows = records(name)
        assert rows
        assert all(row["formula_contract_ref"].startswith("FormulaPluginContractV1:") for row in rows)
