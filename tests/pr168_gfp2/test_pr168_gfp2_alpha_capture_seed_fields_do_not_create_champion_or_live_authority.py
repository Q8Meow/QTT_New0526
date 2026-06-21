from tests.pr168_gfp2.pr168_gfp2_test_support import load


def test_alpha_capture_seed_fields_do_not_create_champion_or_live_authority() -> None:
    for row in load("PR168_GFP2_AlphaCaptureMechanismRegistry.report.json"):
        assert row["creates_champion_or_live_authority_flag"] is False
