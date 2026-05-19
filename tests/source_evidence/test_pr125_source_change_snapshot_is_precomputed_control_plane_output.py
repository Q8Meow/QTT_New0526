from __future__ import annotations

from tests.source_evidence.pr125_revalidation_scheduler_support import snapshot


def test_pr125_source_change_snapshot_is_precomputed_control_plane_output():
    snap = snapshot()

    assert snap["source_change_snapshot_state"] == "PRECOMPUTED_CONTROL_PLANE_FIXTURE"
    assert snap["fixture_authority_class"] == "TEST_FIXTURE_NOT_EXTERNAL_FACT"
    assert snap["production_source_change_authority"] is False
    assert snap["generated_by_tool"] == "tools/source_revalidation_scheduler.py"
    assert snap["live_pretrade_use_allowed_flag"] is False
    assert snap["live_pretrade_consumption_mode"] == (
        "PRECOMPUTED_SNAPSHOT_ONLY_FOR_FUTURE_PR"
    )
