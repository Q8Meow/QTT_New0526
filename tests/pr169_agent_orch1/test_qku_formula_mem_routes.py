from __future__ import annotations

from tools import build_pr169_agent_orch1 as builder

from .conftest import jsonl


def test_qku_formula_access_uses_central_selected_refs():
    for file_name in ("qku_tasks.jsonl", "formula_tasks.jsonl", "access_proof.jsonl", "library_receipts.jsonl"):
        rows = jsonl(file_name)
        assert rows
        for row in rows:
            assert row["stage_profile_ref_or_gap"]
            assert row["market_applicability_ref_or_gap"]
            assert row["platform_filter_ref_or_gap"]
            assert row["agent_duty_filter_ref_or_gap"].endswith("PR165_D2_AgentDutySourceCrosswalk.report.json")
            assert row["executability_overlay_ref_or_gap"]
            assert row["context_filter_ref_or_gap"]
            assert row["mem1_filter_ref_or_gap"]
            assert row["selected_qku_refs"]
            assert row["selected_formula_refs"]
            assert row["library_query_receipt_ref_or_gap"]
            assert row["full_library_access_used"] is False


def test_mem1_bindings_are_prior_only_and_revalidated():
    for file_name in ("mem1_bindings.jsonl", "mem_prior_tasks.jsonl", "learning_routes.jsonl"):
        for row in jsonl(file_name):
            assert row["memory_prior_ref_or_gap"]
            assert row["memory_is_prior_not_proof"] is True
            assert row["memory_revalidation_required"] is True
            assert row["memory_update_receipt_created"] is False
            assert row["same_venue_scope"] is True
            assert row["same_market_type_scope"] is True
            assert row["same_event_lifecycle_scope"] is True
            assert row["same_formula_algorithm_qku_stack_scope"] is True


def test_institutional_control_tasks_are_bound_to_refs_or_gaps():
    for file_name in (
        "rank_tasks.jsonl",
        "tca_tasks.jsonl",
        "fdr_tasks.jsonl",
        "portfolio_tasks.jsonl",
        "capacity_tasks.jsonl",
        "champion_tasks.jsonl",
        "mem_prior_tasks.jsonl",
        "utility_tasks.jsonl",
        "scenario_tasks.jsonl",
        "calibration_tasks.jsonl",
    ):
        for row in jsonl(file_name):
            for field in builder.INSTITUTIONAL_REFS:
                assert row[field], f"{file_name} missing {field}"
            assert row["dag_ref"]
            assert row["no_trade_ref_or_gap"]


def test_quantum_routes_are_structural_only_with_fallbacks():
    for row in jsonl("quantum_tasks.jsonl"):
        for field in (
            "qstruct_ref_or_gap",
            "objective_route_ref_or_gap",
            "variable_route_ref_or_gap",
            "constraint_route_ref_or_gap",
            "penalty_route_ref_or_gap",
            "coefficient_scale_ref_or_gap",
            "quadratic_program_ref_or_gap",
            "qubo_ref_or_gap",
            "bqm_ref_or_gap",
            "cqm_ref_or_gap",
            "ising_ref_or_gap",
            "qaoa_vqe_route_ref_or_gap",
            "classical_fallback_ref_or_gap",
            "interpret_back_map_ref_or_gap",
            "qmap_owner_route_ref_or_gap",
        ):
            assert row[field]
        assert row["quantum_route_uses"]
        assert row["quantum_backend_execution_created"] is False
        assert row["quantum_advantage_claim_created"] is False
        assert row["quantum_order_authority_created"] is False
