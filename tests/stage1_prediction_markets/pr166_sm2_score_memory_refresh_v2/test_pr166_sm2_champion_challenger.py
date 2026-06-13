from __future__ import annotations

from .helpers import assert_report_rows


def test_pr166_sm2_champions_and_challengers_preserve_boundaries():
    champions = assert_report_rows("PR166_SM2_ChampionRegistry.report.json", 2)
    challengers = assert_report_rows("PR166_SM2_ChallengerRegistry.report.json", 25)
    assert all(row["champion_requires_future_replay_paper"] for row in champions)
    assert all(row["must_retest_before_positive_claim"] for row in challengers)
