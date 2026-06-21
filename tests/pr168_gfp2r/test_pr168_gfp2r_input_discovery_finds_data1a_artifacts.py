from tests.pr168_gfp2r._helpers import records


def test_pr168_gfp2r_input_discovery_finds_data1a_artifacts() -> None:
    discovery = records("PR168_GFP2R_InputDiscovery")
    assert discovery["DATA1A_discovered_artifact_count"] == discovery["DATA1A_required_artifact_count"]
    assert discovery["DATA1A_missing_required_artifact_refs"] == []
