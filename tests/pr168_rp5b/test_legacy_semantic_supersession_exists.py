from tests.pr168_rp5b._helpers import load_rows


def test_legacy_semantic_supersession_exists() -> None:
    rows = load_rows("legacy_semantic_supersession_rows")
    interpretations = {row["canonical_future_interpretation"] for row in rows}
    assert "CONDITION_SCOPED_NEGATIVE_OUTCOME_MEMORY" in interpretations
    assert "NO_TRADE_ADVISED_FOR_THIS_CONTEXT_ONLY" in interpretations
    assert "FORMULA_EXECUTION_ADAPTER_OR_INPUT_BINDING" in interpretations
    assert all("global" in row["forbidden_old_interpretation"].lower() or row["legacy_term_family"] not in {"NEGATIVE_FORMULA", "NO_TRADE_DOMINATED_FORMULA"} for row in rows)
