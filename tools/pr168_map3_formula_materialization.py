from __future__ import annotations

from tools.pr168_map3_config import MATERIALIZED, materialized_rows


def build_formula_materialization_rows() -> list[dict]:
    rows = []
    for row in materialized_rows():
        out = dict(row)
        out["contract_family"] = (
            "FormulaPluginContractV1" if out["materialization_path"] == MATERIALIZED else None
        )
        out["formula_contract_ref"] = (
            f"FormulaPluginContractV1:{out['formula_id']}"
            if out["materialization_path"] == MATERIALIZED
            else None
        )
        out["data_requirement_contract_ref"] = f"DataRequirementContractV1:{out['formula_id']}"
        out["unit_normalization_contract_ref"] = f"UnitNormalizationContractV1:{out['formula_id']}"
        out["dry_run_receipt_ref"] = (
            f"ReplayPaperComputeReceiptV1:{out['formula_id']}"
            if out["materialization_path"] == MATERIALIZED
            else None
        )
        out["dry_run_status"] = (
            "DRY_RUN_COMPUTABLE_WITH_SYNTHETIC_UNIT_TEST_ONLY_NON_PROOF"
            if out["materialization_path"] == MATERIALIZED
            else "DRY_RUN_GAP_ROUTED_MISSING_INPUT"
        )
        rows.append(out)
    return rows
