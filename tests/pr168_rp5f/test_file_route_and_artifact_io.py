from ._helpers import assert_rows_have_contract, read_json


def test_every_artifact_registry_entry_has_file_route_and_artifact_io_rows() -> None:
    registry = read_json("art_reg.json")
    artifact_paths = {entry["file_path"] for entry in registry["artifacts"]}
    artifact_io = assert_rows_have_contract("artifact_io.jsonl")
    file_route = assert_rows_have_contract("file_route.jsonl")

    assert artifact_paths <= {row["file_path"] for row in artifact_io}
    assert artifact_paths <= {row["file_path"] for row in file_route}
    assert all(row["orphan_flag"] is False for row in artifact_io)
    assert all(row["orphan_flag"] is False for row in file_route)
