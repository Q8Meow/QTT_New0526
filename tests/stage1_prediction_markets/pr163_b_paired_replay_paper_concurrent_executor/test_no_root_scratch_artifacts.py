def test_no_root_scratch_artifacts(repo_root):
    forbidden = [
        path
        for path in repo_root.iterdir()
        if path.is_file() and path.name.startswith("PR163_B") and path.suffix.lower() in {".txt", ".json", ".zip"}
    ]
    assert forbidden == []
