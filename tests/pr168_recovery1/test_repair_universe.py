from tests.pr168_recovery1._helpers import assert_recovery1_valid, rows


def test_repair_universe_has_stack_formula_source_families() -> None:
    assert_recovery1_valid()
    assert {row["repair_family"] for row in rows("repair_universe")} >= {"STACK_REPAIR", "EXPRESSION_FORMULA", "SOURCE_PROVENANCE"}
