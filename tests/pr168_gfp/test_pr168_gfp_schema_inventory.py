import json
from pathlib import Path


REQUIRED_SCHEMAS = {
    "pr168_gfp_global_label_inventory.schema.json",
    "pr168_gfp_count_reconcile.schema.json",
    "pr168_gfp_canonical_row_key.schema.json",
    "pr168_gfp_computation_evidence.schema.json",
    "pr168_gfp_demotion.schema.json",
    "pr168_gfp_truth_overlay.schema.json",
    "pr168_gfp_formula_assignment.schema.json",
    "pr168_gfp_required_formula_set.schema.json",
    "pr168_gfp_formula_source.schema.json",
    "pr168_gfp_formula_variable_map.schema.json",
    "pr168_gfp_real_formula_function.schema.json",
    "pr168_gfp_pnl_evidence.schema.json",
    "pr168_gfp_tca_calculation.schema.json",
    "pr168_gfp_quantum_objective_coefficients.schema.json",
    "pr168_gfp_atomicrows_coverage.schema.json",
    "pr168_gfp_qku_coverage.schema.json",
    "pr168_gfp_candidate_packet_v1_coverage.schema.json",
    "pr168_gfp_replay_paper_recompute_route.schema.json",
    "pr168_gfp_agent_work_order.schema.json",
    "pr168_gfp_lineage.schema.json",
    "pr168_gfp_no_orphan.schema.json",
    "pr168_gfp_authority_boundary.schema.json",
}


def test_required_schema_inventory_is_present_and_json_parseable():
    schema_dir = Path("src/qtt/stage1_prediction_markets/pr168_gfp_real_computation/schemas")
    actual = {path.name for path in schema_dir.glob("*.schema.json")}

    assert REQUIRED_SCHEMAS <= actual
    for schema_name in REQUIRED_SCHEMAS:
        schema = json.loads((schema_dir / schema_name).read_text(encoding="utf-8"))
        assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
        assert schema["title"].startswith("PR168-GFP")
