from ._helpers import ART_DIR, assert_valid, read_json


def test_artifact_registry_paths_are_windows_safe_and_routed() -> None:
    assert_valid()
    registry = read_json("art_reg.json")
    entries = registry["artifacts"]

    assert entries
    for entry in entries:
        path = entry["file_path"]
        assert entry["windows_safe_flag"] is True
        assert entry["repo_relative_path_length"] <= 180
        assert " " not in path
        assert entry["filename_length"] <= 64
        assert (ART_DIR.parent.parent.parent.parent / path).exists()
