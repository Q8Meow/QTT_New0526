from ._helpers import by_key, read_json, read_jsonl


def test_every_artifact_registry_file_has_io_and_file_route_rows() -> None:
    registry = read_json("art_reg.json")
    expected = {f"docs/master_plan/generated/pr168_rp5e/{row['short_file']}" for row in registry["artifacts"]}
    artifact_io = by_key(read_jsonl("artifact_io.jsonl"), "file_path")
    file_route = by_key(read_jsonl("file_route.jsonl"), "file_path")

    assert expected <= set(artifact_io)
    assert expected <= set(file_route)
    for path in expected:
        assert artifact_io[path]["orphan_flag"] is False
        assert file_route[path]["orphan_flag"] is False
