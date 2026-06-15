from __future__ import annotations

from .helpers import assert_report_contract, summary


def test_pr166_sm3_champion_and_challenger_counts_are_synchronized():
    assert_report_contract("PR166_SM3_ChampionRegistry.report.json", 1)
    assert_report_contract("PR166_SM3_ChallengerRegistry.report.json", 150)
    assert summary()["champion_rows"] == 1
    assert summary()["challenger_rows"] == 150
