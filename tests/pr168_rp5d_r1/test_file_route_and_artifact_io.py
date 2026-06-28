from ._helpers import read_json, read_jsonl


def test_every_artifact_is_in_file_route_and_artifact_io() -> None:
    expected = {entry["artifact_filename"] for entry in read_json("art_reg.json")["entries"]}
    art_io = {row["file_path"].split("/")[-1] for row in read_jsonl("artifact_io.jsonl")}
    file_route = {row["file_path"].split("/")[-1] for row in read_jsonl("file_route.jsonl")}
    assert art_io == expected
    assert file_route == expected
