from tests.pr169_dash1_ui1.conftest import boot_data


def test_ui1_no_platform_specific_source_default_anywhere() -> None:
    intake = boot_data()["source_agnostic_research_intake"]
    assert intake["no_single_source_family_is_default_truth_or_default_trading_authority"] is True
    assert intake["source_candidate_is_research_input_not_source_truth"] is True
    assert "source_family" in intake["object_fields"]
    assert "website" in intake["supported_source_families"]
