from __future__ import annotations

from .helpers import assert_report_contract, summary


def test_pr166_sm3_downstream_handoff_reports_are_count_synchronized():
    expected = {
        "PR166_SM3_PR165D3Handoff.report.json": 150,
        "PR166_SM3_PR166QHandoff.report.json": 559,
        "PR166_SM3_PR166QBHandoff.report.json": 559,
        "PR166_SM3_PR166QCHandoff.report.json": 559,
        "PR166_SM3_PR166SM4Handoff.report.json": 3215,
        "PR166_SM3_PR166SDHandoff.report.json": 183,
        "PR166_SM3_PR162DR3Handoff.report.json": 3065,
        "PR166_SM3_PR162EHandoff.report.json": 150,
        "PR166_SM3_PR162FHandoff.report.json": 150,
        "PR166_SM3_PR162EQHandoff.report.json": 559,
        "PR166_SM3_PR167Handoff.report.json": 150,
        "PR166_SM3_PR167BHandoff.report.json": 333,
        "PR166_SM3_PR168Handoff.report.json": 3215,
        "PR166_SM3_PR169Handoff.report.json": 3215,
        "PR166_SM3_PR170Handoff.report.json": 400,
        "PR166_SM3_PR171Handoff.report.json": 500,
        "PR166_SM3_PR172Handoff.report.json": 500,
        "PR166_SM3_PR173Handoff.report.json": 500,
        "PR166_SM3_PR174181Handoff.report.json": 150,
    }
    for report, count in expected.items():
        assert_report_contract(report, count)
    s = summary()
    assert s["PR165-D3 handoff rows"] == 150
    assert s["PR166-Q handoff rows"] == 559
    assert s["PR166-QB handoff rows"] == 559
    assert s["PR166-QC handoff rows"] == 559
    assert s["PR167 / PR167-B handoff rows"] == 483
    assert s["PR174-PR181 handoff rows"] == 150
