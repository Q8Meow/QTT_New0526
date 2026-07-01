from .test_support import all_rows


def test_no_rows_create_formula_or_qku_global_bans_or_mutation() -> None:
    for row in all_rows():
        assert row.get("formula_mutation_flag") is False
        assert row.get("qku_mutation_flag") is False
        assert row.get("global_formula_ban_flag") is False
        assert row.get("global_qku_ban_flag") is False
        assert row.get("formula_global_ban_flag") is False
        assert row.get("qku_global_ban_flag") is False
