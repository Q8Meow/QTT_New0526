from tests.pr169_dash1.conftest import jsonl


def test_shadow_mode_rows_have_comparison_slots_not_execution_authority() -> None:
    rows = jsonl("owner_shadow_mode_display_contract.generated.jsonl")
    assert rows
    for row in rows:
        assert row["shadow_panel_id"]
        assert row["authority_boundary_ref"]
        assert "SHADOW" in " ".join(row["shadow_candidate_refs"] + row["paper_shadow_diff_refs"] + row["replay_shadow_diff_refs"])
