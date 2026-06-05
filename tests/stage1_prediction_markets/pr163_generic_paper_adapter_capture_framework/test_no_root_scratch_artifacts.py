from pathlib import Path


def test_no_root_pr163_scratch_artifacts(repo_root):
    scratch_suffixes = {".txt", ".json", ".zip"}
    offenders = []
    for path in Path(repo_root).iterdir():
        if path.is_file() and path.name.lower().startswith("pr163") and path.suffix.lower() in scratch_suffixes:
            offenders.append(path.name)
    assert offenders == []
