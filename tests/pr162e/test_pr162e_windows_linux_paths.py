from tests.pr162e.helpers import records


def test_generated_paths_are_portable_posix_relative_paths():
    rows = records("PR162E_FileConsumerMap.report.json")
    assert all("\\" not in row["artifact_path"] for row in rows)
    assert all(not row["artifact_path"].startswith("/") for row in rows)
