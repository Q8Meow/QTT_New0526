from tests.source_evidence.pr127_execution_lifecycle_support import handoff, stage1_venues


def test_pr127_cross_venue_normalization_handoff_manifest_created():
    manifest = handoff()

    assert manifest["cross_venue_normalization_handoff_id"] == (
        "PR127_CROSS_VENUE_NORMALIZATION_HANDOFF_FIXTURE_V1"
    )
    assert manifest["source_repo_pr_label"] == "PR127"
    assert manifest["future_roadmap_pr"] == "PR110"
    assert set(manifest["venue_ids_in_scope"]) == stage1_venues()
    assert len(manifest["lifecycle_model_ids"]) == 3
    assert manifest["production_cross_venue_normalization_authority"] is False
    assert manifest["production_arbitrage_comparability_authority"] is False
