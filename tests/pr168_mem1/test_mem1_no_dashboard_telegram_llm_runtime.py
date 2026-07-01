from .test_support import all_rows


def test_no_dashboard_telegram_or_llm_runtime_created() -> None:
    for row in all_rows():
        assert row.get("dashboard_runtime_created_flag") is False
        assert row.get("telegram_runtime_created_flag") is False
        assert row.get("llm_runtime_created_flag") is False
        assert row.get("owner_approval_authority_created_flag") is False
