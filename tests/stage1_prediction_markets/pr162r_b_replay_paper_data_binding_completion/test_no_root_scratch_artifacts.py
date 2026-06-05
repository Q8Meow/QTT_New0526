def test_no_root_scratch_artifacts(repo_root):
    bad_suffixes = {".txt", ".json", ".zip"}
    bad = [
        path.name
        for path in repo_root.iterdir()
        if path.is_file() and path.name.startswith("PR162R_B") and path.suffix.lower() in bad_suffixes
    ]
    assert bad == []
