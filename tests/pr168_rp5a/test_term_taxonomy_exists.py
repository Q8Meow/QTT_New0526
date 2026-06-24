from tests.pr168_rp5a._helpers import load_rows


def test_term_taxonomy_exists() -> None:
    rows = load_rows("term_taxonomy_rows")
    terms = {row["term_text_or_regex"] for row in rows}
    assert len(rows) >= 40
    assert {"formula repair", "QKU repair", "global formula ban", "LIVE_CANDIDATE"} <= terms
