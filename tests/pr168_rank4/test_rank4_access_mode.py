from ._helpers import rows


def test_access_mode_prevents_full_library_default_access() -> None:
    for row in rows("rank_access_mode.jsonl"):
        assert row["full_library_default_access_flag"] is False
        assert row["lazy_load_selected_objects_only_flag"] is True
        assert row["access_mode"] in {"DEFAULT_COMPUTE", "AVAILABLE_ON_DEMAND", "REPLAY_PAPER_EXECUTABLE_NOW", "SOURCE_REQUIRED", "NOT_STAGE1_APPLICABLE", "AGENT_DUTY_NOT_ALLOWED", "UNKNOWN_COMPLETION_REQUIRED"}

