from __future__ import annotations

from tools.pr168_map3_config import MATERIALIZED, materialized_rows


def build_formula_factory_rows() -> list[dict]:
    rows = []
    for mat in materialized_rows():
        row = dict(mat)
        row["formula_factory_row_id"] = row.pop("formula_materialization_row_id").replace("MAT_", "FACTORY_")
        row["factory_output_state"] = (
            "MATERIALIZED_FORMULA_PLUGIN_CONTRACT"
            if row["materialization_path"] == MATERIALIZED
            else row["materialization_path"]
        )
        row["contract_family"] = (
            "FormulaPluginContractV1" if row["materialization_path"] == MATERIALIZED else None
        )
        row["formula_contract_ref"] = (
            f"FormulaPluginContractV1:{row['formula_id']}"
            if row["materialization_path"] == MATERIALIZED
            else None
        )
        row["data_requirement_contract_ref"] = f"DataRequirementContractV1:{row['formula_id']}"
        row["unit_normalization_contract_ref"] = f"UnitNormalizationContractV1:{row['formula_id']}"
        row["dry_run_receipt_ref"] = (
            f"ReplayPaperComputeReceiptV1:{row['formula_id']}"
            if row["materialization_path"] == MATERIALIZED
            else None
        )
        row["dry_run_status"] = (
            "DRY_RUN_COMPUTABLE_WITH_SYNTHETIC_UNIT_TEST_ONLY_NON_PROOF"
            if row["materialization_path"] == MATERIALIZED
            else "DRY_RUN_GAP_ROUTED_MISSING_INPUT"
        )
        return_rows = row.setdefault("downstream_consumers", [])
        if "PR168_RANK2_EVIDENCE_RANKING" not in return_rows:
            return_rows.append("PR168_RANK2_EVIDENCE_RANKING")
        rows.append(row)
    return rows
