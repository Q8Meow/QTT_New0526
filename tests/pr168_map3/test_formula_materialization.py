from __future__ import annotations

from tests.pr168_map3._helpers import records


def test_materialized_formulas_have_contract_data_unit_and_dryrun_routes() -> None:
    rows = records("PR168_MAP3_FormulaMaterialization.report.json")
    materialized = [
        row for row in rows if row["materialization_path"] == "MATERIALIZED_FORMULA_PLUGIN_CONTRACT"
    ]
    assert materialized
    for row in materialized:
        assert row["formula_contract_ref"].startswith("FormulaPluginContractV1:")
        assert row["data_requirement_contract_ref"].startswith("DataRequirementContractV1:")
        assert row["unit_normalization_contract_ref"].startswith("UnitNormalizationContractV1:")
        assert row["dry_run_receipt_ref"].startswith("ReplayPaperComputeReceiptV1:")
        assert row["dry_run_status"] == "DRY_RUN_COMPUTABLE_WITH_SYNTHETIC_UNIT_TEST_ONLY_NON_PROOF"
