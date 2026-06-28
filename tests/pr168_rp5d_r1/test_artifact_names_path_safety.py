from ._helpers import read_json


def test_artifact_registry_paths_are_safe() -> None:
    registry = read_json("art_reg.json")
    assert registry["artifact_name_registry_count"] == len(registry["entries"])
    assert all(entry["safe_filename_flag"] for entry in registry["entries"])
