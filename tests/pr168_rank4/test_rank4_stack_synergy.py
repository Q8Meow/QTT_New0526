from ._helpers import rows


def test_stack_synergy_does_not_mutate_formulas() -> None:
    for row in rows("rank_stack_synergy.jsonl"):
        assert row["formula_mutation_flag"] is False
        assert row["qku_mutation_flag"] is False
        assert row["causal_claim_flag"] is False

