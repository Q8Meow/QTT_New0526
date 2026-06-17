from __future__ import annotations

from src.qtt.stage1_prediction_markets.pr166_qc_quantum_selected_replay_paper_retest.report_writer import (
    build_payloads_with_shards,
)

from .helpers import REPO_ROOT


def bounded_snapshot():
    payloads, shards = build_payloads_with_shards(REPO_ROOT)
    return payloads, shards


def assert_bounded_idempotence_equal(left, right):
    assert left == right


def test_pr166_qc_bounded_idempotence():
    assert_bounded_idempotence_equal(bounded_snapshot(), bounded_snapshot())
