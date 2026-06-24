from collections import Counter

from tests.pr168_rp5a._helpers import delete_rows, file_rows


def test_every_matched_file_has_classification() -> None:
    counts = Counter(row["file_path"] for row in delete_rows())
    for row in file_rows():
        assert counts[row["file_path"]] == 1
        assert row["recommended_classification_draft"]
