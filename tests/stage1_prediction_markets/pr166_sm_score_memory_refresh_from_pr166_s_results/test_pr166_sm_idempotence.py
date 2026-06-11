import json

from .conftest import REPO_ROOT
from src.qtt.stage1_prediction_markets.pr166_sm_score_memory_refresh_from_pr166_s_results.report_writer import (
    build_payloads,
)


def test_pr166_sm_payload_build_is_idempotent():
    first = build_payloads(REPO_ROOT)
    second = build_payloads(REPO_ROOT)
    assert json.dumps(first, sort_keys=True, separators=(",", ":")) == json.dumps(
        second, sort_keys=True, separators=(",", ":")
    )
