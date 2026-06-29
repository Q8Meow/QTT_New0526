from ._helpers import assert_rows_have_contract


def test_master_and_roadmap_trace_cover_major_artifact_families() -> None:
    master = assert_rows_have_contract("master_trace.jsonl")
    roadmap = assert_rows_have_contract("roadmap_trace.jsonl")

    master_artifacts = {artifact for row in master for artifact in row["implemented_by_artifacts"]}
    assert any("targets.jsonl" in artifact for artifact in master_artifacts)
    assert any("var_grid.jsonl" in artifact for artifact in master_artifacts)
    assert any("trade_seed.jsonl" in artifact for artifact in master_artifacts)
    assert any("live_shadow_route.jsonl" in artifact for artifact in master_artifacts)
    future_consumers = {consumer for row in roadmap for consumer in row["future_consumer_prs"]}
    assert {"RP5G", "RANK4", "QOPT1"} <= future_consumers
    assert all("RP5F" in row["roadmap_position"] for row in roadmap)
