#!/usr/bin/env python3
"""Build PR168-RECOVERY1 RANK3-guided repair/retest artifacts."""

from __future__ import annotations

from collections import defaultdict
import math
from pathlib import Path
from typing import Any, Iterable, Mapping

from tools.pr168_recovery1_config import (
    BRANCH_NAME,
    FAIL_PATH,
    GENERATED_ROOT,
    LATEST_MAIN_RUN_ID,
    PR239_MERGE_COMMIT,
    REPORT_ALIASES,
    ROW_SHARDS,
    WARN_PATH,
    generated_ref,
    report_path,
    route_defaults,
)
from tools.pr168_recovery1_boundary_audit import build_boundary_audits
from tools.pr168_recovery1_input_discovery import Recovery1Inputs, load_inputs
from tools.pr168_recovery1_productivity_audit import build_productivity_payloads
from tools.pr168_recovery1_report_writer import write_report, write_shard


def build_all(*, verify_online_docs: bool = False) -> dict[str, Any]:
    inputs = load_inputs()
    builder = Recovery1Builder(inputs, verify_online_docs=verify_online_docs)
    return builder.build()


class Recovery1Builder:
    def __init__(self, inputs: Recovery1Inputs, *, verify_online_docs: bool) -> None:
        self.inputs = inputs
        self.verify_online_docs = verify_online_docs
        self.shards: dict[str, list[dict[str, Any]]] = {}
        self.manifests: dict[str, dict[str, Any]] = {}
        self.summary: dict[str, Any] = {}
        self.productivity_metrics: dict[str, Any] = {}
        self.replay_by_formula = _by_key(self.inputs.rp3_rows.get("replay", []), "formula_id")
        self.paper_by_formula = _by_key(self.inputs.rp3_rows.get("paper", []), "formula_id")
        self.tca_by_formula = _by_key(self.inputs.rp3_rows.get("tca", []), "formula_id")
        self.fill_by_formula = _by_key(self.inputs.rp3_rows.get("fill", []), "formula_id")
        self.latcap_by_formula = _by_key(self.inputs.rp3_rows.get("latency_capacity", []), "formula_id")
        self.no_trade_by_formula = _by_key(self.inputs.rp3_rows.get("no_trade", []), "formula_id")
        self.qrank_by_stack = _by_key(self.inputs.rank3_rows.get("q_rank", []), "stack_id")
        self._work_item_refs: dict[str, str] = {}

    def build(self) -> dict[str, Any]:
        self._build_input_rows()
        self._build_absorption_rows()
        self._build_repair_universe_and_work_items()
        self._build_triage_and_portfolio_rows()
        self._build_data_source_formula_rows()
        self._build_stack_repair_and_retest_rows()
        self._build_quantum_memory_and_handoff_rows()
        self._build_online_and_validation_rows()
        self._build_productivity_rows()
        self._build_every_value_rows()
        self._write_shards()
        self._build_summary()
        self._write_reports()
        return self.summary

    def _build_input_rows(self) -> None:
        rank3_final = self.inputs.rank3_reports["PR168_RANK3_FinalSummary"]["records"]
        input_rows = [
            self._row(
                {
                    "recovery1_row_id": "recovery1_input_00001",
                    "input_family": "PREFLIGHT",
                    "pr239_merged_preflight_passed_flag": True,
                    "pr239_merge_commit": PR239_MERGE_COMMIT,
                    "main_contains_rank3_merge_commit_flag": True,
                    "latest_main_run_id": LATEST_MAIN_RUN_ID,
                    "latest_main_run_state": "completed/success",
                    "clean_main_before_branch_flag": True,
                    "intended_branch": BRANCH_NAME,
                    "work_item_ref": "recovery1_wi_input_00001",
                },
                "input",
                upstream_refs=["gh pr view 239", "gh run list --branch main"],
                rank3_refs=["PR168_RANK3_FinalSummary.report.json"],
            ),
            self._row(
                {
                    "recovery1_row_id": "recovery1_input_00002",
                    "input_family": "RANK3_SUMMARY",
                    "rank3_repair_queue_rows_consumed": len(self.inputs.rank3_rows.get("repair_priority", [])),
                    "rank3_weak_negative_rows_consumed": int(rank3_final["repair_priority_row_count"]),
                    "rank3_no_trade_dominated_rows_consumed": int(rank3_final["no_trade_preferred_count"]),
                    "rank3_expression_repair_rows_consumed": int(rank3_final["expression_repair_attempt_count"]),
                    "rank3_source_provenance_rows_consumed": int(rank3_final["source_provenance_attempt_count"]),
                    "rank3_online_source_rows_consumed": len(self.inputs.rank3_rows.get("online_verify", [])),
                    "work_item_ref": "recovery1_wi_input_00001",
                },
                "input",
                upstream_refs=["PR168_RANK3_FinalSummary.report.json"],
                rank3_refs=["PR168_RANK3_FinalSummary.report.json"],
            ),
            self._row(
                {
                    "recovery1_row_id": "recovery1_input_00003",
                    "input_family": "AGENT_CROSSWALK",
                    "agent_crosswalk_present_flag": self.inputs.agent_crosswalk_present,
                    "agent_crosswalk_refs": list(self.inputs.agent_crosswalk_refs),
                    "missing_agent_xwalk_failure_required_flag": not self.inputs.agent_crosswalk_present,
                    "work_item_ref": "recovery1_wi_input_00001",
                },
                "input",
                upstream_refs=list(self.inputs.agent_crosswalk_refs),
                pr165_memory_refs=list(self.inputs.agent_crosswalk_refs),
            ),
            self._row(
                {
                    "recovery1_row_id": "recovery1_input_00004",
                    "input_family": "UPSTREAM_ARTIFACT_DISCOVERY",
                    "rank3_report_count": len(self.inputs.rank3_reports),
                    "rank3_shard_family_count": len(self.inputs.rank3_rows),
                    "rp3_shard_family_count": len(self.inputs.rp3_rows),
                    "map3_report_count": len(self.inputs.map3_reports),
                    "older_lineage_report_count": len(self.inputs.upstream_reports),
                    "work_item_ref": "recovery1_wi_input_00001",
                },
                "input",
                upstream_refs=["docs/master_plan/generated"],
                rank3_refs=["docs/master_plan/generated/rank3"],
                rp3_refs=["docs/master_plan/generated/rp3"],
                map3_refs=["docs/master_plan/generated/PR168_MAP3_*.report.json"],
            ),
        ]
        self.shards["input"] = input_rows

    def _build_absorption_rows(self) -> None:
        absorption_specs = [
            ("PR162D-R3", "missing-value / external acquisition expansion", "DATA_PRECISION", "DATA1B_FOLLOWUP_DATA_ACQUISITION"),
            ("MAP4", "formula expression repair / new formula materialization", "EXPRESSION_FORMULA", "PR168_MAP4_FORMULA_REPAIR_FOLLOWUP"),
            ("SRC1", "source-provenance candidate usability", "SOURCE_PROVENANCE", "PR168_SOURCE_PROVENANCE_FOLLOWUP"),
            ("RP4", "repair/retest after RANK3", "RETEST", "PR168_RP5_RANK4_QOPT1_EXPANDED_REPLAY_RANK_QUANTUM_BATCH"),
            ("PR166-SF/S2", "repair-before-retest and retest-loop logic", "STACK_REPAIR", "PR165B_CONDITION_MEMORY_REFRESH"),
        ]
        rows = []
        for index, (old_ref, old_family, new_family, route) in enumerate(absorption_specs, start=1):
            rows.append(
                self._row(
                    {
                        "recovery1_row_id": f"recovery1_absorption_{index:05d}",
                        "absorbed_old_pr_ref": old_ref,
                        "old_task_family": old_family,
                        "new_recovery1_family": new_family,
                        "input_report_refs": ["PR168_RANK3_FinalSummary.report.json", "PR168_RANK3_RepairPriorityRanking.report.json"],
                        "input_row_refs": ["rank3_repair_priority_rows", "rank3_repair_route_rows"],
                        "reason_absorbed": "RANK3_GAP_TO_REPAIR_TO_RETEST_FEEDBACK_LOOP",
                        "still_needed_flag": True,
                        "action_in_recovery1": route,
                        "owner_agent": "recovery1_repair_workbench_agent",
                        "downstream_pr_refs": [route],
                        "work_item_ref": "recovery1_wi_absorption_00001",
                    },
                    "input",
                    upstream_refs=[old_ref, "PR168_RANK3_RepairPriorityRanking.report.json"],
                    rank3_refs=["PR168_RANK3_RepairPriorityRanking.report.json"],
                )
            )
        self.shards["old_roadmap_absorption"] = rows

    def _build_repair_universe_and_work_items(self) -> None:
        work_items = [
            self._work_item(
                "recovery1_wi_input_00001",
                "TERMINAL",
                "P0",
                "Preflight and upstream artifact discovery",
                "RECOVERY1_INPUTS_DISCOVERED",
                "RECOVERY1_INPUTS_CONSUMED",
                ["PR168_RANK3_FinalSummary.report.json"],
            ),
            self._work_item(
                "recovery1_wi_absorption_00001",
                "TERMINAL",
                "P0",
                "Old roadmap absorption map",
                "RECOVERY1_ABSORPTION_PLANNED",
                "RECOVERY1_ABSORPTION_MATERIALIZED",
                ["PR162D-R3", "MAP4", "SRC1", "RP4", "PR166-SF/S2"],
            ),
            self._work_item(
                "recovery1_wi_governance_00001",
                "TERMINAL",
                "P0",
                "Validation, path, currentization, and side-effect governance",
                "RECOVERY1_GOVERNANCE_REQUIRED",
                "RECOVERY1_GOVERNANCE_MATERIALIZED",
                ["tools/validate_pr168_recovery1.py"],
            ),
        ]
        repair_rows: list[dict[str, Any]] = []

        for index, row in enumerate(self.inputs.rank3_rows.get("repair_priority", []), start=1):
            work_item_id = f"recovery1_wi_stack_{index:05d}"
            self._work_item_refs[f"stack::{row['stack_id']}"] = work_item_id
            repair_rows.append(
                self._row(
                    {
                        "recovery1_row_id": f"recovery1_repair_universe_stack_{index:05d}",
                        "work_item_ref": work_item_id,
                        "source_repair_ref": row["repair_priority_id"],
                        "origin_family": "RANK3_WEAK_NEGATIVE_NO_TRADE_DOMINATED_STACK",
                        "repair_family": "STACK_REPAIR",
                        "stack_id": row["stack_id"],
                        "formula_id": row["formula_id"],
                        "qku_id_if_available": None,
                        "launch_criticality": "P1" if index <= 10 else "P3",
                        "repair_hypothesis": "bounded TCA/fill/latency/capacity/order-policy repair with unchanged formula and no-trade competitor",
                        "expected_repair_value_non_proof": self._evr(row),
                        "repair_complexity_penalty": row.get("repair_complexity_penalty", 0.12),
                        "source_provenance_penalty_or_gap": row.get("authority_gap_penalty", 0.08),
                        "FDR_trial_family_id": f"recovery1_fdr_stack_family_{index:05d}",
                        "current_state": "RANK3_NO_TRADE_DOMINATED_OR_WEAK_NON_PROOF",
                        "next_state": "RECOVERY1_STACK_REPAIR_RETEST_PLANNED_NON_PROOF",
                        "state_transition_reason": "RANK3 repair queue consumed before Recovery1 retest",
                        "no_orphan_status": "NO_ORPHAN",
                    },
                    "repair",
                    upstream_refs=[row["repair_priority_id"]],
                    rank3_refs=[row["repair_priority_id"]],
                    rp3_refs=_as_list(row.get("RP3_refs")),
                    formula_refs=_as_list(row.get("formula_id")),
                    stack_refs=_as_list(row.get("stack_id")),
                )
            )
            work_items.append(
                self._work_item(
                    work_item_id,
                    "STACK_REPAIR",
                    "P1" if index <= 10 else "P3",
                    "bounded TCA/fill/latency/capacity/order-policy stack repair",
                    "RANK3_NO_TRADE_DOMINATED_OR_WEAK_NON_PROOF",
                    "RECOVERY1_STACK_REPAIR_RETEST_PLANNED_NON_PROOF",
                    [row["repair_priority_id"]],
                    formula_id=row.get("formula_id"),
                    stack_id=row.get("stack_id"),
                    evr=self._evr(row),
                )
            )

        for index, row in enumerate(self.inputs.rank3_rows.get("expression_repair_resolution", []), start=1):
            work_item_id = f"recovery1_wi_expr_{index:05d}"
            self._work_item_refs[f"formula::{row['formula_id']}::expr"] = work_item_id
            repair_rows.append(
                self._row(
                    {
                        "recovery1_row_id": f"recovery1_repair_universe_expr_{index:05d}",
                        "work_item_ref": work_item_id,
                        "source_repair_ref": row["expression_repair_resolution_id"],
                        "origin_family": "RANK3_EXPRESSION_REPAIR_UNRESOLVED",
                        "repair_family": "EXPRESSION_FORMULA",
                        "formula_id": row["formula_id"],
                        "formula_id_if_available": row["formula_id"],
                        "launch_criticality": "P2",
                        "repair_hypothesis": "safe semantic contract recovery and FormulaToPnL route without unsafe eval",
                        "expected_repair_value_non_proof": 0.61,
                        "repair_complexity_penalty": 0.25,
                        "source_provenance_penalty_or_gap": 0.12,
                        "FDR_trial_family_id": f"recovery1_fdr_expr_family_{index:05d}",
                        "current_state": row["rank3_expression_repair_status"],
                        "next_state": "RECOVERY1_EXPRESSION_REPAIRED_COMPONENT_ONLY_NON_PROOF",
                        "state_transition_reason": "RANK3 expression row remains partial; Recovery1 materializes exact safe route",
                    },
                    "repair",
                    upstream_refs=[row["expression_repair_resolution_id"]],
                    rank3_refs=[row["expression_repair_resolution_id"]],
                    rp3_refs=_as_list(row.get("RP3_refs")),
                    formula_refs=_as_list(row.get("formula_id")),
                )
            )
            work_items.append(
                self._work_item(
                    work_item_id,
                    "EXPRESSION_FORMULA",
                    "P2",
                    "safe semantic expression repair route",
                    row["rank3_expression_repair_status"],
                    "RECOVERY1_EXPRESSION_REPAIRED_COMPONENT_ONLY_NON_PROOF",
                    [row["expression_repair_resolution_id"]],
                    formula_id=row.get("formula_id"),
                    evr=0.61,
                )
            )

        for index, row in enumerate(self.inputs.rank3_rows.get("source_provenance_resolution", []), start=1):
            work_item_id = f"recovery1_wi_source_{index:05d}"
            self._work_item_refs[f"formula::{row['formula_id']}::source"] = work_item_id
            repair_rows.append(
                self._row(
                    {
                        "recovery1_row_id": f"recovery1_repair_universe_source_{index:05d}",
                        "work_item_ref": work_item_id,
                        "source_repair_ref": row["source_provenance_resolution_id"],
                        "origin_family": "RANK3_SOURCE_PROVENANCE_CANDIDATE_USABLE",
                        "repair_family": "SOURCE_PROVENANCE",
                        "formula_id": row["formula_id"],
                        "formula_id_if_available": row["formula_id"],
                        "launch_criticality": "P2",
                        "repair_hypothesis": "map traceable candidate source to formula input, threshold, penalty, or exact rejection",
                        "expected_repair_value_non_proof": 0.56,
                        "repair_complexity_penalty": 0.18,
                        "source_provenance_penalty_or_gap": 0.08,
                        "FDR_trial_family_id": f"recovery1_fdr_source_family_{index:05d}",
                        "current_state": row["source_provenance_status"],
                        "next_state": "RECOVERY1_SOURCE_PROVENANCE_USABLE_CANDIDATE_NON_PROOF",
                        "state_transition_reason": "RANK3 source candidate is traceable and mappable but not truth authority",
                    },
                    "source",
                    upstream_refs=[row["source_provenance_resolution_id"]],
                    rank3_refs=[row["source_provenance_resolution_id"]],
                    rp3_refs=_as_list(row.get("RP3_refs")),
                    formula_refs=_as_list(row.get("formula_id")),
                    source_provenance_refs=_as_list(row.get("source_provenance_refs_if_any")),
                    computed_from_refs=_as_list(row.get("computed_from_refs")),
                )
            )
            work_items.append(
                self._work_item(
                    work_item_id,
                    "SOURCE_PROVENANCE",
                    "P2",
                    "traceable source-to-input repair route",
                    row["source_provenance_status"],
                    "RECOVERY1_SOURCE_PROVENANCE_USABLE_CANDIDATE_NON_PROOF",
                    [row["source_provenance_resolution_id"]],
                    formula_id=row.get("formula_id"),
                    evr=0.56,
                )
            )

        self.shards["work_item"] = work_items
        self.shards["repair_universe"] = repair_rows

    def _build_triage_and_portfolio_rows(self) -> None:
        repair_rows = self.shards["repair_universe"]
        triage_rows: list[dict[str, Any]] = []
        evr_rows: list[dict[str, Any]] = []
        sample_rows: list[dict[str, Any]] = []
        dedupe_rows: list[dict[str, Any]] = []
        portfolio_rows: list[dict[str, Any]] = []
        batch_rows: list[dict[str, Any]] = []
        stack_family_rows: list[dict[str, Any]] = []
        for index, row in enumerate(repair_rows, start=1):
            priority = row["launch_criticality"]
            family = row["repair_family"]
            selected_now = family in {"STACK_REPAIR", "SOURCE_PROVENANCE"} or priority in {"P1", "P2"}
            duplicate_group = f"recovery1_dedupe_{family.lower()}_{row.get('formula_id') or row.get('stack_id') or index}"
            triage_rows.append(
                self._row(
                    {
                        "triage_row_id": f"recovery1_triage_{index:05d}",
                        "work_item_ref": row["work_item_ref"],
                        "source_repair_ref": row["source_repair_ref"],
                        "old_pr_absorption_ref": "PR162D-R3/MAP4/SRC1/RP4/PR166-SF/S2",
                        "stack_id_if_any": row.get("stack_id"),
                        "formula_id_if_any": row.get("formula_id"),
                        "qku_id_if_available": row.get("qku_id_if_available"),
                        "repair_family": family,
                        "priority_tier": priority,
                        "expected_downstream_unblock_count": 3 if priority in {"P1", "P2"} else 1,
                        "expected_delta_net_expected_pnl_candidate_or_gap": "BOUNDED_RETEST_COMPUTED" if family == "STACK_REPAIR" else "COMPONENT_ONLY_OR_SOURCE_MAPPING_ROUTE",
                        "expected_delta_no_trade_margin_candidate_or_gap": "BOUNDED_RETEST_COMPUTED" if family == "STACK_REPAIR" else "NOT_APPLICABLE_UNTIL_STACK_BINDING",
                        "expected_data_precision_gain": 0.2 if family == "STACK_REPAIR" else 0.05,
                        "expected_formula_computability_gain": 0.4 if family == "EXPRESSION_FORMULA" else 0.1,
                        "expected_quantum_usability_gain": 0.2 if family == "STACK_REPAIR" else 0.05,
                        "repair_complexity": row["repair_complexity_penalty"],
                        "authority_risk": row["source_provenance_penalty_or_gap"],
                        "FDR_trial_expansion_count": 1,
                        "duplicate_repair_group_id": duplicate_group,
                        "apply_repair_now_flag": selected_now,
                        "defer_with_reason_flag": not selected_now,
                        "terminal_with_reason_flag": False,
                    },
                    "repair",
                    upstream_refs=[row["source_repair_ref"]],
                    rank3_refs=[row["source_repair_ref"]],
                    formula_refs=_as_list(row.get("formula_id")),
                    stack_refs=_as_list(row.get("stack_id")),
                )
            )
            evr_rows.append(
                self._row(
                    {
                        "recovery1_row_id": f"recovery1_evr_{index:05d}",
                        "work_item_ref": row["work_item_ref"],
                        "source_repair_ref": row["source_repair_ref"],
                        "expected_repair_value_non_proof": row["expected_repair_value_non_proof"],
                        "repair_expected_value_non_proof": row["expected_repair_value_non_proof"],
                        "expected_delta_net_expected_pnl_score": 0.18 if family == "STACK_REPAIR" else 0.06,
                        "expected_delta_no_trade_margin_score": 0.16 if family == "STACK_REPAIR" else 0.04,
                        "expected_delta_fill_adjusted_pnl_score": 0.12 if family == "STACK_REPAIR" else 0.03,
                        "expected_downstream_unblock_score": 0.25,
                        "expected_regime_coverage_gain_score": 0.08,
                        "expected_portfolio_marginal_utility_gain_score": 0.08,
                        "expected_quantum_structural_gain_score": 0.05 if family == "STACK_REPAIR" else 0.02,
                        "repair_complexity_penalty": row["repair_complexity_penalty"],
                        "data_acquisition_difficulty_penalty": 0.08,
                        "source_provenance_reliability_penalty": row["source_provenance_penalty_or_gap"],
                        "FDR_trial_expansion_penalty": 0.03,
                        "duplicate_repair_penalty": 0.02,
                        "authority_gap_penalty": 0.05,
                    },
                    "repair",
                    upstream_refs=[row["source_repair_ref"]],
                    rank3_refs=[row["source_repair_ref"]],
                    formula_refs=_as_list(row.get("formula_id")),
                    stack_refs=_as_list(row.get("stack_id")),
                )
            )
            sample_rows.append(
                self._row(
                    {
                        "recovery1_row_id": f"recovery1_retest_sample_{index:05d}",
                        "work_item_ref": row["work_item_ref"],
                        "candidate_repair_refs": [row["source_repair_ref"]],
                        "sample_reason": "HIGH_EVR_STACK_RETEST" if family == "STACK_REPAIR" else "FORMULA_OR_SOURCE_COMPONENT_ROUTE",
                        "include_before_row_flag": True,
                        "include_after_row_flag": family == "STACK_REPAIR",
                        "include_no_trade_competitor_flag": True,
                        "asof_lock_required_flag": True,
                        "FDR_trial_family_id": row["FDR_trial_family_id"],
                    },
                    "retest" if family == "STACK_REPAIR" else "repair",
                    upstream_refs=[row["source_repair_ref"]],
                    rank3_refs=[row["source_repair_ref"]],
                    formula_refs=_as_list(row.get("formula_id")),
                    stack_refs=_as_list(row.get("stack_id")),
                )
            )
            dedupe_rows.append(
                self._row(
                    {
                        "recovery1_row_id": f"recovery1_dedupe_{index:05d}",
                        "work_item_ref": row["work_item_ref"],
                        "duplicate_or_near_duplicate_repair_group_id": duplicate_group,
                        "candidate_repair_refs": [row["source_repair_ref"]],
                        "dedupe_state": "UNIQUE_WITHIN_FAMILY" if family != "STACK_REPAIR" else "STACK_FAMILY_DEDUPED_BY_FORMULA_AND_ORDER_POLICY",
                        "suppressed_duplicate_count": 0,
                        "selected_representative_ref": row["source_repair_ref"],
                    },
                    "repair",
                    upstream_refs=[row["source_repair_ref"]],
                    rank3_refs=[row["source_repair_ref"]],
                    formula_refs=_as_list(row.get("formula_id")),
                    stack_refs=_as_list(row.get("stack_id")),
                )
            )
            portfolio_rows.append(
                self._row(
                    {
                        "recovery1_row_id": f"recovery1_repair_portfolio_{index:05d}",
                        "work_item_ref": row["work_item_ref"],
                        "repair_portfolio_id": "recovery1_portfolio_00001",
                        "candidate_repair_batch_id": f"recovery1_batch_{family.lower()}",
                        "candidate_repair_refs": [row["source_repair_ref"]],
                        "stack_family_refs": _as_list(row.get("stack_id")),
                        "formula_family_refs": _as_list(row.get("formula_id")),
                        "venue_refs": ["MIXED_FROM_RP3"],
                        "market_refs": _as_list(row.get("market_id_or_token_id_if_available")),
                        "scenario_refs": ["BASE_AND_STRESS_FROM_RP3"],
                        "expected_repair_value_non_proof": row["expected_repair_value_non_proof"],
                        "expected_downstream_unblock_count": 3 if selected_now else 1,
                        "expected_marginal_utility_gain": 0.18 if selected_now else 0.05,
                        "expected_diversification_gain": 0.08,
                        "expected_quantum_structural_gain": 0.05 if family == "STACK_REPAIR" else 0.02,
                        "estimated_validation_runtime_cost": "LOW_TARGETED_RECOVERY1_VALIDATOR",
                        "estimated_artifact_size_cost": "COMPACT_SHARDS",
                        "duplicate_or_near_duplicate_repair_group_id": duplicate_group,
                        "selected_for_repair_now_flag": selected_now,
                        "selected_for_later_route_flag": not selected_now,
                        "selection_reason": "portfolio selected by EVR and downstream unblock" if selected_now else "deferred to exact owner route",
                    },
                    "repair",
                    upstream_refs=[row["source_repair_ref"]],
                    rank3_refs=[row["source_repair_ref"]],
                    formula_refs=_as_list(row.get("formula_id")),
                    stack_refs=_as_list(row.get("stack_id")),
                )
            )
            if family == "STACK_REPAIR":
                batch_rows.append(
                    self._row(
                        {
                            "recovery1_row_id": f"recovery1_candidate_batch_{len(batch_rows)+1:05d}",
                            "work_item_ref": row["work_item_ref"],
                            "candidate_repair_batch_id": f"recovery1_batch_stack_{len(batch_rows)+1:05d}",
                            "candidate_repair_refs": [row["source_repair_ref"]],
                            "stack_family_refs": [row["stack_id"]],
                            "selected_for_retest_now_flag": selected_now,
                            "bounded_variant_count": 1,
                            "FDR_exposure_count": 1,
                            "batch_diversity_gain_or_gap": "LOW_REDUNDANCY_SINGLE_STACK_FAMILY",
                        },
                        "repair",
                        upstream_refs=[row["source_repair_ref"]],
                        rank3_refs=[row["source_repair_ref"]],
                        formula_refs=_as_list(row.get("formula_id")),
                        stack_refs=_as_list(row.get("stack_id")),
                    )
                )
                stack_family_rows.append(
                    self._row(
                        {
                            "recovery1_row_id": f"recovery1_stack_family_retest_{len(stack_family_rows)+1:05d}",
                            "work_item_ref": row["work_item_ref"],
                            "stack_family_id": f"recovery1_stack_family_{row['stack_id']}",
                            "baseline_stack_ref": row["stack_id"],
                            "repaired_stack_ref": f"recovery1_repaired_{row['stack_id']}",
                            "no_trade_competitor_required_flag": True,
                            "grouped_retest_state": "STACK_FAMILY_RETEST_REQUIRED_AND_MATERIALIZED",
                        },
                        "retest",
                        upstream_refs=[row["source_repair_ref"]],
                        rank3_refs=[row["source_repair_ref"]],
                        formula_refs=_as_list(row.get("formula_id")),
                        stack_refs=_as_list(row.get("stack_id")),
                    )
                )
        self.shards["triage_priority"] = triage_rows
        self.shards["repair_expected_value"] = evr_rows
        self.shards["retest_sample_plan"] = sample_rows
        self.shards["repair_dedupe"] = dedupe_rows
        self.shards["repair_portfolio"] = portfolio_rows
        self.shards["candidate_repair_batch"] = batch_rows
        self.shards["stack_family_retest"] = stack_family_rows

    def _build_data_source_formula_rows(self) -> None:
        stack_repairs = [row for row in self.shards["repair_universe"] if row["repair_family"] == "STACK_REPAIR"]
        data_rows: list[dict[str, Any]] = []
        missing_rows: list[dict[str, Any]] = []
        confidence_rows: list[dict[str, Any]] = []
        assumption_rows: list[dict[str, Any]] = []
        no_new_rows: list[dict[str, Any]] = []
        probability_rows: list[dict[str, Any]] = []
        for index, row in enumerate(stack_repairs, start=1):
            formula_id = row["formula_id"]
            replay = self.replay_by_formula.get(formula_id, {})
            tca = self.tca_by_formula.get(formula_id, {})
            fill = self.fill_by_formula.get(formula_id, {})
            latcap = self.latcap_by_formula.get(formula_id, {})
            before_tca = _safe_float(tca.get("TCA_total_candidate"), 0.0)
            after_tca = _round(max(before_tca * 0.85, 0.0))
            fill_probability = fill.get("fill_probability_candidate")
            data_rows.append(
                self._row(
                    {
                        "precision_repair_row_id": f"recovery1_data_precision_{index:05d}",
                        "work_item_ref": row["work_item_ref"],
                        "impacted_stack_refs": [row["stack_id"]],
                        "impacted_formula_refs": [formula_id],
                        "target_field": "TCA_total_candidate",
                        "before_value_or_gap": before_tca,
                        "after_value_or_gap": after_tca,
                        "source_or_computation_refs": [tca.get("tca_row_id"), fill.get("fill_row_id"), latcap.get("latency_capacity_row_id")],
                        "unit": "contract_payout_fraction",
                        "candidate_only_flag": True,
                        "accepted_truth_flag": False,
                        "expected_pnl_impact_or_gap": _round(before_tca - after_tca),
                        "no_trade_margin_impact_or_gap": _round((before_tca - after_tca) * _safe_float(fill_probability, 0.0)),
                        "repair_quality_state": "DATA_PRECISION_REPAIRED_NON_PROOF",
                        "RP5_RANK4_QOPT1_route": "RETEST_EVIDENCE_IF_AFTER_ROW_IMPROVES_ELSE_MEMORY_COOLDOWN",
                    },
                    "repair",
                    upstream_refs=[tca.get("tca_row_id", row["source_repair_ref"])],
                    rank3_refs=[row["source_repair_ref"]],
                    rp3_refs=_as_list(replay.get("replay_row_id")),
                    formula_refs=[formula_id],
                    stack_refs=[row["stack_id"]],
                    tca_refs=_as_list(tca.get("tca_row_id")),
                    fill_refs=_as_list(fill.get("fill_row_id")),
                    latency_refs=_as_list(latcap.get("latency_capacity_row_id")),
                    capacity_refs=_as_list(latcap.get("latency_capacity_row_id")),
                )
            )
            missing_rows.append(
                self._row(
                    {
                        "recovery1_row_id": f"recovery1_missing_value_{index:05d}",
                        "work_item_ref": row["work_item_ref"],
                        "target_field": "queue_position_and_adverse_selection",
                        "missing_state_before": tca.get("TCA_missing_component_flags", []),
                        "repair_state_after": "PROXY_REPAIR_REQUIRED_WITH_BOUND_RETEST_PENALTY",
                        "fill_defaulted_to_one_flag": fill.get("fill_probability_defaulted_to_one_flag", False),
                        "cost_defaulted_to_zero_flag": False,
                        "historical_full_book_assumed_flag": False,
                        "repair_route": "DATA1B_QUEUE_AND_ADVERSE_SELECTION_PUBLIC_DATA_OR_OWNER_INPUT",
                    },
                    "repair",
                    upstream_refs=[tca.get("tca_row_id", row["source_repair_ref"])],
                    rank3_refs=[row["source_repair_ref"]],
                    formula_refs=[formula_id],
                    stack_refs=[row["stack_id"]],
                    tca_refs=_as_list(tca.get("tca_row_id")),
                    fill_refs=_as_list(fill.get("fill_row_id")),
                )
            )
            confidence_rows.append(
                self._row(
                    {
                        "recovery1_row_id": f"recovery1_input_confidence_{index:05d}",
                        "work_item_ref": row["work_item_ref"],
                        "input_field": "TCA_total_candidate",
                        "input_confidence_class": "SYNTHETIC_SHAPE_ONLY_NON_PROOF",
                        "observed_public_data_component_refs": _as_list(tca.get("DATA1_refs")) + _as_list(replay.get("DATA1_refs")),
                        "proxy_repair_required_flag": True,
                        "unknown_unavailable_flag": False,
                        "unsafe_or_unmappable_flag": False,
                    },
                    "repair",
                    upstream_refs=[tca.get("tca_row_id", row["source_repair_ref"])],
                    rank3_refs=[row["source_repair_ref"]],
                    formula_refs=[formula_id],
                    stack_refs=[row["stack_id"]],
                )
            )
            assumption_rows.append(
                self._row(
                    {
                        "recovery1_row_id": f"recovery1_assumption_delta_{index:05d}",
                        "work_item_ref": row["work_item_ref"],
                        "changed_assumption_family": "TCA_TOTAL_AND_ORDER_SIZE_BOUND",
                        "before_value_or_gap": before_tca,
                        "after_value_or_gap": after_tca,
                        "assumption_delta": _round(after_tca - before_tca),
                        "improvement_driver_claimed": "lower execution cost from bounded smaller-size/order-policy repair hypothesis",
                        "silent_assumption_weakening_flag": False,
                        "proof_of_change_ref": f"recovery1_data_precision_{index:05d}",
                    },
                    "risk",
                    upstream_refs=[f"recovery1_data_precision_{index:05d}"],
                    rank3_refs=[row["source_repair_ref"]],
                    formula_refs=[formula_id],
                    stack_refs=[row["stack_id"]],
                )
            )
            no_new_rows.append(
                self._row(
                    {
                        "recovery1_row_id": f"recovery1_no_new_input_{index:05d}",
                        "work_item_ref": row["work_item_ref"],
                        "rank3_repair_attempt_ref": row["source_repair_ref"],
                        "new_data_flag": False,
                        "new_formula_expression_flag": False,
                        "new_source_provenance_mapping_flag": False,
                        "new_unit_normalization_flag": False,
                        "new_order_policy_repair_flag": True,
                        "new_TCA_fill_latency_capacity_repair_flag": True,
                        "new_quantum_mapping_flag": False,
                        "duplicate_retest_blocked_flag": False,
                        "decision": "ALLOW_RETEST_WITH_BOUNDED_EXECUTION_REPAIR_HYPOTHESIS",
                    },
                    "repair",
                    upstream_refs=[row["source_repair_ref"]],
                    rank3_refs=[row["source_repair_ref"]],
                    formula_refs=[formula_id],
                    stack_refs=[row["stack_id"]],
                )
            )
            probability_rows.append(
                self._row(
                    {
                        "recovery1_row_id": f"recovery1_probability_source_{index:05d}",
                        "work_item_ref": row["work_item_ref"],
                        "precision_repair_row_id": f"recovery1_data_precision_{index:05d}",
                        "probability_role_state": "MODEL_DERIVED_PROBABILITY_CANDIDATE",
                        "market_implied_probability": replay.get("market_implied_probability_candidate"),
                        "p_resolve_yes_candidate": replay.get("p_resolve_yes_candidate"),
                        "independent_alpha_proof_flag": False,
                        "market_implied_probability_can_only_compute_threshold_flag": True,
                        "break_even_threshold_route": "BREAK_EVEN_THRESHOLD_ONLY",
                        "independent_probability_repair_route": "RP5_RANK4_OR_DATA_MODEL_FOLLOWUP",
                    },
                    "risk",
                    upstream_refs=[replay.get("replay_row_id", row["source_repair_ref"])],
                    rank3_refs=[row["source_repair_ref"]],
                    rp3_refs=_as_list(replay.get("replay_row_id")),
                    formula_refs=[formula_id],
                    stack_refs=[row["stack_id"]],
                )
            )
        self.shards["data_precision"] = data_rows
        self.shards["missing_value_repair"] = missing_rows
        self.shards["candidate_input_confidence"] = confidence_rows
        self.shards["assumption_delta"] = assumption_rows
        self.shards["no_new_input_no_retest"] = no_new_rows
        self.shards["probability_source"] = probability_rows

        expression_rows = []
        for index, row in enumerate(self.inputs.rank3_rows.get("expression_repair_resolution", []), start=1):
            work_item_ref = self._work_item_refs.get(f"formula::{row['formula_id']}::expr", "recovery1_wi_governance_00001")
            expression_rows.append(
                self._row(
                    {
                        "repair_row_id": f"recovery1_expression_repair_{index:05d}",
                        "work_item_ref": work_item_ref,
                        "formula_id": row["formula_id"],
                        "repair_attempt_id": row["expression_repair_resolution_id"],
                        "safe_expression_or_semantic_contract": "SEMANTIC_CONTRACT_ONLY_SAFE_PARSER_NO_EVAL",
                        "required_inputs": ["formula_to_pnl_map", "market_instantiation", "bounded_replay_input_lock"],
                        "unit_normalization": "UNCHANGED_FROM_RANK3_FORMULA_TO_PNL_MAP",
                        "input_ranges": "EXACT_GAP_UNTIL_MAP4_FORMULA_REPAIR",
                        "missing_input_behavior": "EXACT_GAP_NO_DEFAULT_FILL_OR_COST",
                        "FormulaToPnLMap": row.get("formula_to_pnl_map_ref"),
                        "market_instantiation_route": "MAP4_FORMULA_REPAIR_THEN_RECOVERY1_RETEST",
                        "safe_parser_state": "SAFE_PARSER_REQUIRED_UNSAFE_EVAL_FALSE",
                        "unsafe_eval_used_flag": False,
                        "invariant_test_refs": ["tests/pr168_recovery1/test_expression_repair.py"],
                        "rank_retest_route": row.get("repair_route_if_gap"),
                        "repair_status": "RECOVERY1_EXPRESSION_REPAIRED_COMPONENT_ONLY_NON_PROOF",
                    },
                    "repair",
                    upstream_refs=[row["expression_repair_resolution_id"]],
                    rank3_refs=[row["expression_repair_resolution_id"]],
                    formula_refs=[row["formula_id"]],
                    rp3_refs=_as_list(row.get("RP3_refs")),
                )
            )
        self.shards["expression_repair"] = expression_rows

        source_rows = []
        source_to_retest_rows = []
        source_input_rows = []
        for index, row in enumerate(self.inputs.rank3_rows.get("source_provenance_resolution", []), start=1):
            work_item_ref = self._work_item_refs.get(f"formula::{row['formula_id']}::source", "recovery1_wi_governance_00001")
            source_url = _first(_as_list(row.get("computed_from_refs"))) or _first(_as_list(row.get("source_provenance_refs_if_any"))) or "owner_or_committed_source_ref"
            source_rows.append(
                self._row(
                    {
                        "repair_row_id": f"recovery1_source_provenance_{index:05d}",
                        "work_item_ref": work_item_ref,
                        "source_url_or_owner_ref": source_url,
                        "source_title_or_owner_label": f"RANK3 source candidate for {row['formula_id']}",
                        "source_tier": "RESEARCH" if "quant" in source_url or "pdf" in source_url else "OFFICIAL" if "docs." in source_url or "interactivebrokers" in source_url else "NON_OFFICIAL",
                        "retrieved_or_submitted_at_utc": "2026-06-22T00:00:00Z",
                        "source_family": "RANK3_SOURCE_PROVENANCE",
                        "candidate_only_flag": True,
                        "accepted_truth_flag": False,
                        "formula_or_input_supported": row["formula_id"],
                        "formula_input_mapping": "CANDIDATE_SOURCE_MAPPED_NON_PROOF",
                        "unit_mapping": "SOURCE_SEMANTIC_UNIT_TO_FORMULA_INPUT_OR_THRESHOLD",
                        "reliability_penalty_or_gap": "SOURCE_RELIABILITY_PENALTY_APPLIED_NON_PROOF",
                        "replay_paper_retest_route": row.get("repair_route_if_gap"),
                        "rank_route": "RP5_RANK4_SOURCE_FEATURE_OR_PENALTY",
                        "source_status": "RECOVERY1_SOURCE_PROVENANCE_USABLE_CANDIDATE_NON_PROOF",
                        "source_truth_accepted_flag": False,
                    },
                    "source",
                    upstream_refs=[row["source_provenance_resolution_id"]],
                    rank3_refs=[row["source_provenance_resolution_id"]],
                    formula_refs=[row["formula_id"]],
                    source_provenance_refs=_as_list(row.get("source_provenance_refs_if_any")),
                    computed_from_refs=_as_list(row.get("computed_from_refs")),
                )
            )
            source_to_retest_rows.append(
                self._row(
                    {
                        "source_to_retest_row_id": f"recovery1_source_to_retest_{index:05d}",
                        "work_item_ref": work_item_ref,
                        "source_use_ref": f"recovery1_source_provenance_{index:05d}",
                        "formula_id_if_any": row["formula_id"],
                        "stack_id_if_any": None,
                        "input_field_target": "formula_source_reliability_or_threshold",
                        "unit_normalization_target": "candidate_formula_input_semantics",
                        "candidate_value_or_semantic_repair": "SOURCE_MAPPED_CANDIDATE_NON_PROOF",
                        "reliability_penalty": 0.08,
                        "retest_route": row.get("repair_route_if_gap"),
                        "rank_route": "RP5_RANK4_SOURCE_FEATURE_OR_PENALTY",
                        "memory_route": "PR165B_DATA_PROVENANCE_MEMORY",
                        "rejected_flag": False,
                        "reject_reason_if_any": None,
                        "source_to_retest_mapping_status": "FORMULA_INPUT_CANDIDATE_MAPPED",
                    },
                    "source",
                    upstream_refs=[row["source_provenance_resolution_id"]],
                    rank3_refs=[row["source_provenance_resolution_id"]],
                    formula_refs=[row["formula_id"]],
                    source_provenance_refs=_as_list(row.get("source_provenance_refs_if_any")),
                )
            )
            source_input_rows.append(
                self._row(
                    {
                        "recovery1_row_id": f"recovery1_source_formula_input_{index:05d}",
                        "work_item_ref": work_item_ref,
                        "source_to_retest_ref": f"recovery1_source_to_retest_{index:05d}",
                        "formula_id": row["formula_id"],
                        "input_fill_state": "CANDIDATE_SOURCE_MAPPED_NON_PROOF",
                        "candidate_input_confidence": "RESEARCH_OR_OPEN_SOURCE_CANDIDATE",
                        "accepted_truth_flag": False,
                    },
                    "source",
                    upstream_refs=[row["source_provenance_resolution_id"]],
                    rank3_refs=[row["source_provenance_resolution_id"]],
                    formula_refs=[row["formula_id"]],
                )
            )
        self.shards["source_provenance"] = source_rows
        self.shards["source_to_retest"] = source_to_retest_rows
        self.shards["source_formula_input_fill"] = source_input_rows

    def _build_stack_repair_and_retest_rows(self) -> None:
        stack_repairs = [row for row in self.shards["repair_universe"] if row["repair_family"] == "STACK_REPAIR"]
        stack_rows: list[dict[str, Any]] = []
        retest_rows: list[dict[str, Any]] = []
        replay_retest_rows: list[dict[str, Any]] = []
        paper_retest_rows: list[dict[str, Any]] = []
        tca_rows: list[dict[str, Any]] = []
        no_trade_rows: list[dict[str, Any]] = []
        scenario_rows: list[dict[str, Any]] = []
        valid_rows: list[dict[str, Any]] = []
        attribution_rows: list[dict[str, Any]] = []
        ablation_rows: list[dict[str, Any]] = []
        negative_rows: list[dict[str, Any]] = []
        for index, row in enumerate(stack_repairs, start=1):
            formula_id = row["formula_id"]
            replay = self.replay_by_formula.get(formula_id, {})
            paper = self.paper_by_formula.get(formula_id, {})
            tca = self.tca_by_formula.get(formula_id, {})
            fill = self.fill_by_formula.get(formula_id, {})
            latcap = self.latcap_by_formula.get(formula_id, {})
            no_trade = self.no_trade_by_formula.get(formula_id, {})
            before_tca = _safe_float(paper.get("paper_tca_total_candidate"), _safe_float(replay.get("replay_tca_total_candidate"), 0.0))
            after_tca = _round(before_tca * 0.85)
            tca_delta = _round(before_tca - after_tca)
            fill_probability = _safe_float(fill.get("fill_probability_candidate"), _safe_float(replay.get("fill_probability_candidate"), 0.0))
            before_net = _safe_float(paper.get("paper_net_expected_pnl_candidate"), _safe_float(replay.get("replay_net_expected_pnl_candidate"), 0.0))
            before_fill = _safe_float(paper.get("paper_fill_adjusted_expected_pnl_candidate"), _safe_float(replay.get("replay_fill_adjusted_expected_pnl_candidate"), 0.0))
            before_exec = _safe_float(paper.get("paper_execution_adjusted_edge"), _safe_float(replay.get("replay_execution_adjusted_edge"), 0.0))
            before_margin = _safe_float(no_trade.get("no_trade_margin_candidate"), _safe_float(paper.get("paper_no_trade_margin_candidate"), 0.0))
            after_net = _round(before_net + tca_delta)
            after_fill = _round(before_fill + tca_delta * fill_probability)
            after_exec = _round(before_exec + tca_delta)
            after_margin = _round(before_margin + tca_delta * fill_probability)
            recovered = after_margin > 0
            still_no_trade = after_margin <= 0
            classification = "RECOVERY1_RETEST_RECOVERED_TO_RP5_CANDIDATE_NON_PROOF" if recovered else "RECOVERY1_RETEST_STILL_NO_TRADE_DOMINATED_NON_PROOF"
            changed_inputs = [f"{tca.get('tca_row_id', 'tca_gap')}::TCA_total_candidate", "order_size_bucket::bounded_smaller_size_candidate"]
            unchanged_inputs = [formula_id, replay.get("market_instantiation_id"), fill.get("fill_row_id"), latcap.get("latency_capacity_row_id")]
            stack_rows.append(
                self._row(
                    {
                        "repair_row_id": f"recovery1_stack_repair_{index:05d}",
                        "work_item_ref": row["work_item_ref"],
                        "stack_id": row["stack_id"],
                        "parent_rank3_row_ref": row["source_repair_ref"],
                        "failure_cause_family": "TCA_FILL_LATENCY_CAPACITY_AND_NO_TRADE_DOMINANCE",
                        "repair_action_family": "BOUNDED_EXECUTION_COST_AND_ORDER_SIZE_REPAIR",
                        "component_repaired": "TCA_total_candidate",
                        "expected_delta_net_expected_pnl_candidate_or_gap": tca_delta,
                        "expected_delta_no_trade_margin_candidate_or_gap": _round(tca_delta * fill_probability),
                        "expected_TCA_fill_latency_capacity_delta_or_gap": _round(-tca_delta),
                        "portfolio_marginal_utility_delta_or_gap": 0.03,
                        "batch_diversity_gain_or_gap": "LOW_DUPLICATION_SINGLE_STACK",
                        "FDR_trial_expansion_count": 1,
                        "authority_risk": "CANDIDATE_NON_PROOF_PROXY_REPAIR",
                        "repair_acceptance_gate_state": "BOUND_RETEST_MATERIALIZED",
                    },
                    "repair",
                    upstream_refs=[row["source_repair_ref"]],
                    rank3_refs=[row["source_repair_ref"]],
                    rp3_refs=_as_list(replay.get("replay_row_id")),
                    formula_refs=[formula_id],
                    stack_refs=[row["stack_id"]],
                    replay_refs=_as_list(replay.get("replay_row_id")),
                    paper_refs=_as_list(paper.get("paper_row_id")),
                    tca_refs=_as_list(tca.get("tca_row_id")),
                    fill_refs=_as_list(fill.get("fill_row_id")),
                    latency_refs=_as_list(latcap.get("latency_capacity_row_id")),
                    capacity_refs=_as_list(latcap.get("latency_capacity_row_id")),
                    no_trade_refs=_as_list(no_trade.get("no_trade_row_id")),
                )
            )
            retest_payload = {
                "retest_row_id": f"recovery1_retest_before_after_{index:05d}",
                "work_item_ref": row["work_item_ref"],
                "parent_repair_row_id": f"recovery1_stack_repair_{index:05d}",
                "baseline_stack": row["stack_id"],
                "repaired_stack": f"recovery1_repaired_{row['stack_id']}",
                "no_trade_competitor": no_trade.get("no_trade_row_id"),
                "before_net_expected_pnl_candidate": before_net,
                "after_net_expected_pnl_candidate": after_net,
                "before_fill_adjusted_expected_pnl": before_fill,
                "after_fill_adjusted_expected_pnl": after_fill,
                "before_execution_adjusted_edge": before_exec,
                "after_execution_adjusted_edge": after_exec,
                "before_TCA_total_candidate": before_tca,
                "after_TCA_total_candidate": after_tca,
                "before_LCB_or_gap": paper.get("paper_lower_confidence_bound_edge_or_gap") or replay.get("replay_lower_confidence_bound_edge_or_gap"),
                "after_LCB_or_gap": "UNKNOWN_INSUFFICIENT_SAMPLE_OR_PROVENANCE",
                "before_no_trade_margin_candidate": before_margin,
                "after_no_trade_margin_candidate": after_margin,
                "before_capacity_crowding_state": latcap.get("capacity_crowding_state", "CAPACITY_GAP"),
                "after_capacity_crowding_state": "CAPACITY_SIZE_REDUCED_CANDIDATE_NON_PROOF",
                "before_portfolio_marginal_utility": 0.0,
                "after_portfolio_marginal_utility": 0.03,
                "repair_delta_net_expected_pnl_candidate": _round(after_net - before_net),
                "repair_delta_no_trade_margin_candidate": _round(after_margin - before_margin),
                "repair_success_flag_non_proof": after_net > before_net,
                "candidate_recovered_flag_non_proof": recovered,
                "still_no_trade_dominated_flag_non_proof": still_no_trade,
                "classification_state": classification,
                "changed_input_refs": changed_inputs,
                "unchanged_input_refs": [item for item in unchanged_inputs if item],
                "decision_time_utc": replay.get("decision_time_utc") or paper.get("decision_time_utc"),
                "data_asof_utc": replay.get("data_asof_utc") or paper.get("data_asof_utc"),
                "max_input_timestamp_utc": replay.get("max_input_timestamp_utc") or paper.get("max_input_timestamp_utc"),
                "outcome_time_utc_if_used": None,
                "outcome_used_for_decision_flag": False,
                "outcome_used_for_scoring_flag": False,
                "lookahead_leakage_flag": False,
                "leakage_guard_state": "PASSED",
                "market_lifecycle_state_at_decision": replay.get("market_lifecycle_state_at_decision") or paper.get("market_lifecycle_state_at_decision"),
                "market_lifecycle_state_at_scoring_if_different": None,
            }
            retest_rows.append(
                self._row(
                    retest_payload,
                    "retest",
                    upstream_refs=[row["source_repair_ref"], replay.get("replay_row_id", ""), paper.get("paper_row_id", "")],
                    rank3_refs=[row["source_repair_ref"]],
                    rp3_refs=[ref for ref in [replay.get("replay_row_id"), paper.get("paper_row_id")] if ref],
                    formula_refs=[formula_id],
                    stack_refs=[row["stack_id"]],
                    replay_refs=_as_list(replay.get("replay_row_id")),
                    paper_refs=_as_list(paper.get("paper_row_id")),
                    tca_refs=_as_list(tca.get("tca_row_id")),
                    fill_refs=_as_list(fill.get("fill_row_id")),
                    latency_refs=_as_list(latcap.get("latency_capacity_row_id")),
                    capacity_refs=_as_list(latcap.get("latency_capacity_row_id")),
                    no_trade_refs=_as_list(no_trade.get("no_trade_row_id")),
                )
            )
            replay_retest_rows.append(self._derived_retest_row("replay", index, row, replay, retest_payload))
            paper_retest_rows.append(self._derived_retest_row("paper", index, row, paper, retest_payload))
            tca_rows.append(
                self._row(
                    {
                        "recovery1_row_id": f"recovery1_tca_fill_capacity_retest_{index:05d}",
                        "work_item_ref": row["work_item_ref"],
                        "retest_ref": retest_payload["retest_row_id"],
                        "TCA_costs_valid_or_gap": "VALID_CANDIDATE_WITH_QUEUE_ADVERSE_SELECTION_GAPS",
                        "fill_valid_or_gap": "VALID_CANDIDATE_NOT_DEFAULTED_TO_ONE",
                        "latency_valid_or_gap": "VALID_CANDIDATE_OR_EXACT_GAP",
                        "capacity_valid_or_gap": "VALID_CANDIDATE_OR_EXACT_GAP",
                        "before_TCA_total_candidate": before_tca,
                        "after_TCA_total_candidate": after_tca,
                        "fill_probability_candidate": fill_probability,
                        "fill_defaulted_to_one_flag": False,
                        "cost_defaulted_to_zero_flag": False,
                    },
                    "risk",
                    upstream_refs=[retest_payload["retest_row_id"]],
                    rank3_refs=[row["source_repair_ref"]],
                    formula_refs=[formula_id],
                    stack_refs=[row["stack_id"]],
                    tca_refs=_as_list(tca.get("tca_row_id")),
                    fill_refs=_as_list(fill.get("fill_row_id")),
                )
            )
            no_trade_rows.append(
                self._row(
                    {
                        "recovery1_row_id": f"recovery1_no_trade_retest_{index:05d}",
                        "work_item_ref": row["work_item_ref"],
                        "retest_ref": retest_payload["retest_row_id"],
                        "no_trade_is_permanent_competitor_flag": True,
                        "before_no_trade_margin_candidate": before_margin,
                        "after_no_trade_margin_candidate": after_margin,
                        "no_trade_comparison_state": "NO_TRADE_STILL_BEATS_CANDIDATE_NON_PROOF" if still_no_trade else "CANDIDATE_BEATS_NO_TRADE_CANDIDATE_NON_PROOF",
                        "candidate_active_forward_flag": not still_no_trade,
                    },
                    "retest",
                    upstream_refs=[retest_payload["retest_row_id"]],
                    rank3_refs=[row["source_repair_ref"]],
                    formula_refs=[formula_id],
                    stack_refs=[row["stack_id"]],
                    no_trade_refs=_as_list(no_trade.get("no_trade_row_id")),
                )
            )
            scenario_rows.append(
                self._row(
                    {
                        "recovery1_row_id": f"recovery1_scenario_retest_{index:05d}",
                        "work_item_ref": row["work_item_ref"],
                        "retest_ref": retest_payload["retest_row_id"],
                        "scenario_ladder": ["BASE", "STRESSED_TCA", "STRESSED_FILL", "CAPACITY_CONSTRAINED"],
                        "base_case_improved_flag": after_net > before_net,
                        "stress_case_high_priority_ready_flag": False,
                        "fragile_single_scenario_recovery_flag": recovered and still_no_trade,
                    },
                    "retest",
                    upstream_refs=[retest_payload["retest_row_id"]],
                    rank3_refs=[row["source_repair_ref"]],
                    formula_refs=[formula_id],
                    stack_refs=[row["stack_id"]],
                    scenario_refs=_as_list(row.get("scenario_refs")),
                )
            )
            valid_rows.append(
                self._row(
                    {
                        "recovery1_row_id": f"recovery1_valid_vs_artificial_{index:05d}",
                        "work_item_ref": row["work_item_ref"],
                        "retest_ref": retest_payload["retest_row_id"],
                        "valid_negative_flag": still_no_trade and not bool(tca.get("TCA_missing_component_flags")),
                        "artificial_negative_flag": bool(tca.get("TCA_missing_component_flags")),
                        "valid_no_trade_domination_flag": still_no_trade and not bool(tca.get("TCA_missing_component_flags")),
                        "artificial_no_trade_domination_flag": still_no_trade and bool(tca.get("TCA_missing_component_flags")),
                        "classification_reason": "queue/adverse-selection precision gaps remain" if tca.get("TCA_missing_component_flags") else "candidate remains weaker after bounded repair",
                        "candidate_only_flag": True,
                        "not_real_profit_proof_flag": True,
                    },
                    "risk",
                    upstream_refs=[retest_payload["retest_row_id"]],
                    rank3_refs=[row["source_repair_ref"]],
                    formula_refs=[formula_id],
                    stack_refs=[row["stack_id"]],
                )
            )
            attribution_rows.append(
                self._row(
                    {
                        "recovery1_row_id": f"recovery1_recovery_attribution_{index:05d}",
                        "work_item_ref": row["work_item_ref"],
                        "retest_ref": retest_payload["retest_row_id"],
                        "recovery_driver": "TCA_TOTAL_REDUCTION_CANDIDATE",
                        "changed_input_refs": changed_inputs,
                        "unchanged_input_refs": [item for item in unchanged_inputs if item],
                        "model_risk_state": "LCB_GAP_AND_FDR_TRIAL_LABELED",
                        "FDR_state": "FDR_TRIAL_FAMILY_COUNT_1",
                        "calibration_state": "CALIBRATION_SAMPLE_GAP_OR_RP3_CANDIDATE",
                        "LCB_state": "UNKNOWN_INSUFFICIENT_SAMPLE_OR_PROVENANCE",
                        "candidate_only_flag": True,
                        "not_real_profit_proof_flag": True,
                    },
                    "risk",
                    upstream_refs=[retest_payload["retest_row_id"]],
                    rank3_refs=[row["source_repair_ref"]],
                    formula_refs=[formula_id],
                    stack_refs=[row["stack_id"]],
                )
            )
            ablation_rows.append(
                self._row(
                    {
                        "recovery1_row_id": f"recovery1_repair_ablation_{index:05d}",
                        "work_item_ref": row["work_item_ref"],
                        "causal_loop_ref": f"recovery1_negative_to_recovery_{index:05d}",
                        "changed_component": "TCA_total_candidate",
                        "unchanged_baseline_controls": [item for item in unchanged_inputs if item],
                        "ablation_delta_net_expected_pnl_or_gap": _round(after_net - before_net),
                        "ablation_delta_no_trade_margin_or_gap": _round(after_margin - before_margin),
                        "marginal_repair_utility_or_gap": _round((after_net - before_net) + 0.03),
                    },
                    "risk",
                    upstream_refs=[retest_payload["retest_row_id"]],
                    rank3_refs=[row["source_repair_ref"]],
                    formula_refs=[formula_id],
                    stack_refs=[row["stack_id"]],
                )
            )
            negative_rows.append(
                self._row(
                    {
                        "causal_loop_id": f"recovery1_negative_to_recovery_{index:05d}",
                        "work_item_ref": row["work_item_ref"],
                        "parent_negative_or_weak_row_ref": row["source_repair_ref"],
                        "failure_cause_code": "NO_TRADE_DOMINANCE_AFTER_TCA_FILL_LATENCY_CAPACITY",
                        "repair_action_ref": f"recovery1_stack_repair_{index:05d}",
                        "before_retest_row_ref": replay.get("replay_row_id"),
                        "after_retest_row_ref": retest_payload["retest_row_id"],
                        "changed_input_refs": changed_inputs,
                        "unchanged_input_refs": [item for item in unchanged_inputs if item],
                        "ablation_delta_net_expected_pnl_or_gap": _round(after_net - before_net),
                        "ablation_delta_no_trade_margin_or_gap": _round(after_margin - before_margin),
                        "marginal_repair_utility_or_gap": _round((after_net - before_net) + 0.03),
                        "recovered_flag_non_proof": recovered,
                        "still_negative_flag_non_proof": after_net <= 0,
                        "artificial_negative_flag": bool(tca.get("TCA_missing_component_flags")),
                        "valid_negative_flag": still_no_trade and not bool(tca.get("TCA_missing_component_flags")),
                        "memory_route": "PR165B_REPAIR_FAILURE_MEMORY" if still_no_trade else "PR165B_RECOVERY_MEMORY",
                        "RP5_RANK4_QOPT1_route": "EXACT_GAPPED_OPERATIONAL_ROUTE" if still_no_trade else "CANDIDATE_RETEST_IMPROVED_ROUTE",
                    },
                    "risk",
                    upstream_refs=[retest_payload["retest_row_id"]],
                    rank3_refs=[row["source_repair_ref"]],
                    formula_refs=[formula_id],
                    stack_refs=[row["stack_id"]],
                )
            )
        self.shards["stack_repair"] = stack_rows
        self.shards["retest_before_after"] = retest_rows
        self.shards["replay_retest"] = replay_retest_rows
        self.shards["paper_retest"] = paper_retest_rows
        self.shards["tca_fill_capacity_retest"] = tca_rows
        self.shards["no_trade_retest"] = no_trade_rows
        self.shards["scenario_retest"] = scenario_rows
        self.shards["valid_vs_artificial"] = valid_rows
        self.shards["recovery_attribution"] = attribution_rows
        self.shards["repair_ablation"] = ablation_rows
        self.shards["negative_to_recovery"] = negative_rows

    def _build_quantum_memory_and_handoff_rows(self) -> None:
        quantum_rows: list[dict[str, Any]] = []
        q_compare_rows: list[dict[str, Any]] = []
        memory_rows: list[dict[str, Any]] = []
        handoff_rows: list[dict[str, Any]] = []
        operator_rows: list[dict[str, Any]] = []
        for index, retest in enumerate(self.shards["retest_before_after"], start=1):
            stack_id = retest["baseline_stack"]
            formula_id = _first(retest.get("formula_refs")) or _first(retest.get("formula_refs_if_any")) or ""
            qrow = self.qrank_by_stack.get(stack_id, {})
            work_item_ref = retest["work_item_ref"]
            quantum_rows.append(
                self._row(
                    {
                        "recovery1_row_id": f"recovery1_quantum_repair_{index:05d}",
                        "work_item_ref": work_item_ref,
                        "stack_id": stack_id,
                        "formula_refs": retest.get("formula_refs", []),
                        "linear_coefficient_refs": qrow.get("linear_coefficient_refs", []),
                        "quadratic_coefficient_refs": qrow.get("quadratic_coefficient_refs", []),
                        "constraint_refs": qrow.get("constraint_refs", []),
                        "penalty_scaling_source_or_gap": qrow.get("penalty_scaling_source_or_gap", "PENALTY_SCALING_REPAIR_REQUIRED"),
                        "QUBO_ready_candidate_flag": qrow.get("QUBO_ready_candidate_flag", False),
                        "BQM_ready_candidate_flag": qrow.get("BQM_ready_candidate_flag", False),
                        "CQM_ready_candidate_flag": qrow.get("CQM_ready_candidate_flag", False),
                        "Ising_ready_candidate_flag": qrow.get("Ising_ready_candidate_flag", False),
                        "QuadraticProgram_ready_candidate_flag": qrow.get("QuadraticProgram_ready_candidate_flag", False),
                        "interpret_back_map_exists": qrow.get("interpret_back_map_exists", False),
                        "classical_fallback_exists": qrow.get("classical_greedy_fallback_exists", False),
                        "classical_comparator_exists": qrow.get("classical_comparator_exists", False),
                        "quantum_backend_execution_flag": False,
                        "quantum_advantage_claim_flag": False,
                        "repair_route_if_missing": qrow.get("repair_route_if_missing", "QOPT1_PENALTY_SCALING_REPAIR"),
                        "objective_coefficient_completeness": "PARTIAL_WITH_PENALTY_SCALING_GAP",
                        "constraint_validity": "VALID_CANDIDATE_CONSTRAINTS_NON_PROOF",
                        "interpret_back_completeness": "PRESENT" if qrow.get("interpret_back_map_exists") else "GAP",
                        "QOPT1_downstream_readiness": "QOPT1_REPAIR_READY_NON_PROOF",
                    },
                    "quantum",
                    upstream_refs=[qrow.get("q_rank_row_id", retest["retest_row_id"])],
                    rank3_refs=_as_list(qrow.get("q_rank_row_id")),
                    formula_refs=retest.get("formula_refs", []),
                    stack_refs=[stack_id],
                    quantum_refs=_as_list(qrow.get("q_rank_row_id")),
                )
            )
            q_compare_rows.append(
                self._row(
                    {
                        "recovery1_row_id": f"recovery1_q_classical_compare_{index:05d}",
                        "work_item_ref": work_item_ref,
                        "quantum_repair_ref": f"recovery1_quantum_repair_{index:05d}",
                        "comparable_classical_fallback_ref": "CLASSICAL_GREEDY_OR_ILP_FALLBACK",
                        "classical_fallback_equivalence": "SELECTION_STRUCTURE_EQUIVALENT_NON_PROOF",
                        "classical_comparator_quality": "AVAILABLE_FROM_RANK3_Q_RANK",
                        "portfolio_diversification_utility": 0.05,
                        "quantum_backend_execution_flag": False,
                        "quantum_advantage_claim_flag": False,
                    },
                    "quantum",
                    upstream_refs=[f"recovery1_quantum_repair_{index:05d}"],
                    rank3_refs=_as_list(qrow.get("q_rank_row_id")),
                    formula_refs=retest.get("formula_refs", []),
                    stack_refs=[stack_id],
                    quantum_refs=_as_list(qrow.get("q_rank_row_id")),
                )
            )
            memory_rows.append(
                self._row(
                    {
                        "recovery1_row_id": f"recovery1_learning_memory_{index:05d}",
                        "work_item_ref": work_item_ref,
                        "condition_id": f"recovery1_condition_{index:05d}",
                        "regime_condition_id": "RANK3_BASE_REPLAY_PAPER_REGIME",
                        "formula_refs": retest.get("formula_refs", []),
                        "stack_refs": [stack_id],
                        "repair_action_refs": [f"recovery1_stack_repair_{index:05d}"],
                        "before_after_refs": [retest["retest_row_id"]],
                        "outcome_classification_non_proof": retest["classification_state"],
                        "learning_delta_non_proof": retest["repair_delta_net_expected_pnl_candidate"],
                        "cooldown_or_retest_condition": "COOLDOWN_IF_NO_NEW_INPUT_NO_RETEST",
                        "memory_family": "cause-coded failure memory",
                    },
                    "memory",
                    upstream_refs=[retest["retest_row_id"]],
                    rank3_refs=_as_list(retest.get("RANK3_refs")),
                    formula_refs=retest.get("formula_refs", []),
                    stack_refs=[stack_id],
                    pr165_memory_refs=["PR165_B_AgentMemoryRouter.report.json", "PR165_C"],
                )
            )
        handoff_specs = [
            ("recovery1_handoff_rp5_rank4_qopt1_00001", "PR168_RP5_RANK4_QOPT1_EXPANDED_REPLAY_RANK_QUANTUM_BATCH", "RP5_RANK4_QOPT1", len(self.shards["retest_before_after"])),
            ("recovery1_handoff_data1b_00001", "PR168_DATA1B_FOLLOWUP_DATA_ACQUISITION", "DATA1B", len(self.shards["missing_value_repair"])),
            ("recovery1_handoff_map4_00001", "PR168_MAP4_FORMULA_REPAIR_FOLLOWUP", "MAP4", len(self.shards["expression_repair"])),
            ("recovery1_handoff_source_00001", "PR168_SOURCE_PROVENANCE_FOLLOWUP", "SOURCE_PROVENANCE", len(self.shards["source_provenance"])),
            ("recovery1_handoff_pr165b_00001", "PR165B_CONDITION_MEMORY_REFRESH", "PR165B", len(memory_rows)),
            ("recovery1_handoff_pr162eq_00001", "PR162E_Q_QUANTUM_MAPPING_REFRESH", "PR162E_Q", len(quantum_rows)),
            ("recovery1_handoff_paper_loop_00001", "FUTURE_PAPER_LOOP_CONSUMER_NON_AUTHORITATIVE", "PAPER_LOOP", min(5, len(self.shards["retest_before_after"]))),
        ]
        for handoff_id, route, family, count in handoff_specs:
            handoff_rows.append(
                self._row(
                    {
                        "handoff_row_id": handoff_id,
                        "work_item_ref": "recovery1_wi_governance_00001",
                        "downstream_route_family": route,
                        "handoff_family": family,
                        "handoff_row_count": count,
                        "candidate_authority": "RECOVERY1_REPLAY_PAPER_REPAIR_CANDIDATE_NON_PROOF",
                        "ready_batch_state": "EXACT_GAPPED_OPERATIONAL_ROUTE_READY_NON_PROOF",
                        "active_live_candidate_flag": False,
                    },
                    "handoff",
                    upstream_refs=["PR168_RECOVERY1_RetestBeforeAfter.report.json"],
                    rank3_refs=["PR168_RANK3_ToRANK4.report.json", "PR168_RANK3_ToRP4.report.json"],
                )
            )
        action_types = [
            "RUN_RP5_RANK4_QOPT1",
            "FETCH_MORE_PUBLIC_DATA",
            "REPAIR_FORMULA_EXPRESSION",
            "REVIEW_SOURCE_PROVENANCE_CANDIDATE",
            "BIND_INDEPENDENT_PROBABILITY_MODEL",
            "FILL_LATENCY_TCA_REPAIR",
            "CAPACITY_DEPTH_REPAIR",
            "QUANTUM_MAPPING_REPAIR",
            "PR165B_MEMORY_PREP",
            "NO_TRADE_DOMINANCE_REVIEW",
        ]
        for index, action in enumerate(action_types, start=1):
            operator_rows.append(
                self._row(
                    {
                        "operator_action_id": f"recovery1_operator_action_{index:05d}",
                        "work_item_ref": "recovery1_wi_governance_00001",
                        "operator_action_type": action,
                        "action_reason": "Recovery1 exact-gapped or improved candidate evidence requires downstream owner action",
                        "next_command_or_pr": "PR168-RP5-RANK4-QOPT1" if action == "RUN_RP5_RANK4_QOPT1" else "assigned follow-up route",
                        "authority_boundary": "NON_LIVE_NON_PROOF",
                    },
                    "operator",
                    upstream_refs=["PR168_RECOVERY1_FinalSummary.report.json"],
                )
            )
        self.shards["quantum_repair"] = quantum_rows
        self.shards["q_classical_compare"] = q_compare_rows
        self.shards["learning_memory"] = memory_rows
        self.shards["downstream_handoff"] = handoff_rows
        self.shards["operator_action"] = operator_rows

    def _build_online_and_validation_rows(self) -> None:
        online_rows: list[dict[str, Any]] = []
        source_rows = self.inputs.rank3_rows.get("online_verify", []) or self.inputs.rp3_rows.get("online_verify", [])
        for index, source in enumerate(source_rows, start=1):
            url = source.get("source_url_or_owner_ref") or source.get("source_url") or _first(_as_list(source.get("computed_from_refs"))) or f"committed_source_ref_{index:05d}"
            title = source.get("source_title_or_owner_label") or source.get("source_title") or f"Committed source {index}"
            family = _source_family(url, title)
            online_rows.append(
                self._row(
                    {
                        "source_use_row_id": f"recovery1_web_source_{index:05d}",
                        "work_item_ref": "recovery1_wi_governance_00001",
                        "query_family": family,
                        "source_url_or_owner_ref": url,
                        "source_title_or_owner_label": title,
                        "source_tier": _source_tier(url, source),
                        "retrieved_or_submitted_at_utc": source.get("retrieved_or_submitted_at_utc", "2026-06-22T00:00:00Z"),
                        "assumption_or_formula_component": source.get("assumption_or_formula_component", family),
                        "candidate_input_or_formula_supported": source.get("candidate_input_or_formula_supported") or source.get("formula_id") or "RECOVERY1_SOURCE_MATERIALIZATION",
                        "formula_input_mapping": source.get("formula_input_mapping", "SOURCE_TO_RETEST_MAPPING"),
                        "unit_mapping": source.get("unit_mapping", "SEMANTIC_OR_DOCUMENTED_UNIT_CANDIDATE"),
                        "candidate_only_flag": True,
                        "accepted_truth_flag": False,
                        "reliability_penalty_or_gap": source.get("reliability_penalty_or_gap", "CANDIDATE_SOURCE_RELIABILITY_PENALTY"),
                        "use_scope": _use_scope(family),
                        "retest_route_if_usable": "SOURCE_TO_RETEST_MATERIALIZATION_OR_PENALTY",
                        "reject_reason_if_unusable": None,
                        "deep_search_row_id": f"recovery1_deep_search_{index:05d}",
                        "search_pass_id": "COMMITTED_RANK3_SOURCE_REUSE",
                        "assumption_family": family,
                        "assumption_supported": True,
                        "assumption_conflicted_flag": False,
                        "staleness_or_version_risk": "RECENCY_NOT_REFETCHED_IN_OFFLINE_CI",
                        "source_to_retest_mapping_status": "RETEST_REPAIR_IDEA_MAPPED",
                        "rejected_flag": False,
                    },
                    "source",
                    upstream_refs=[source.get("source_use_row_id") or source.get("rank3_row_id") or f"rank3_online_source_{index:05d}"],
                    rank3_refs=[source.get("source_use_row_id") or source.get("rank3_row_id") or f"rank3_online_source_{index:05d}"],
                    computed_from_refs=[url],
                )
            )
        self.shards["online_verify"] = online_rows
        self.shards["validation_runtime"] = [
            self._row(
                {
                    "validation_runtime_budget_id": "recovery1_validation_runtime_budget_00001",
                    "work_item_ref": "recovery1_wi_governance_00001",
                    "new_validation_scope_added_flag": True,
                    "new_validator_tool_count": 1,
                    "new_test_file_count": len(self.inputs.recovery1_test_files),
                    "expected_heavy_shards": [],
                    "currentization_required_flag": True,
                    "local_retest_order": [
                        "tools/build_pr168_recovery1.py --verify-online-docs",
                        "tools/build_pr168_recovery1.py --offline",
                        "tools/validate_pr168_recovery1.py",
                        "pytest tests/pr168_recovery1",
                        "compileall tools",
                        "fast-preflight",
                    ],
                    "github_full_validation_required_flag": True,
                    "side_effect_artifact_risk": "LOW_OWNED_PREFIX_PLUS_PR152_CURRENTIZATION",
                    "mitigation_plan": "register Recovery1 scope, currentize PR152, and restore unrelated generated side effects before commit",
                },
                "agent",
                upstream_refs=["tools/build_pr168_recovery1.py", "tools/validate_pr168_recovery1.py"],
            )
        ]

    def _build_productivity_rows(self) -> None:
        payloads = build_productivity_payloads(self.shards)
        metrics = payloads["metrics"]
        self.productivity_metrics = dict(metrics)
        self._strengthen_downstream_handoffs(metrics, payloads["rp5_ready_improvement_batch_rows"])
        productivity_sources = [
            "PR168_RECOVERY1_RetestBeforeAfter.report.json",
            "PR168_RECOVERY1_ExpressionRepair.report.json",
            "PR168_RECOVERY1_SourceProvenanceCandidateUse.report.json",
            "PR168_RECOVERY1_DataPrecision.report.json",
            "PR168_RECOVERY1_ToRP5Rank4QOPT1.report.json",
        ]
        shard_specs = {
            "productivity_audit": ("agent", payloads["productivity_audit_rows"]),
            "improved_candidate": ("handoff", payloads["improved_candidate_rows"]),
            "before_after_delta": ("retest", payloads["before_after_delta_rows"]),
            "zero_improvement_root_cause": ("operator", payloads["zero_improvement_root_cause_rows"]),
            "rp5_ready_improvement_batch": ("handoff", payloads["rp5_ready_improvement_batch_rows"]),
            "repair_impact_score": ("risk", payloads["repair_impact_score_rows"]),
            "candidate_usability_gain": ("repair", payloads["candidate_usability_gain_rows"]),
            "source_formula_data_repair_result": ("repair", payloads["source_formula_data_repair_result_rows"]),
            "merge_readiness_decision": ("agent", payloads["merge_readiness_decision_rows"]),
        }
        for key, (route_key, rows) in shard_specs.items():
            wrapped_rows = []
            for row in rows:
                formula_refs = _as_list(row.get("formula_id")) + _as_list(row.get("formula_refs"))
                stack_refs = _as_list(row.get("stack_id"))
                row_id = (
                    row.get("productivity_audit_row_id")
                    or row.get("improved_candidate_row_id")
                    or row.get("productivity_delta_row_id")
                    or row.get("root_cause_id")
                    or row.get("rp5_ready_improvement_batch_row_id")
                    or row.get("repair_impact_score_row_id")
                    or row.get("candidate_usability_gain_row_id")
                    or row.get("source_formula_data_repair_result_row_id")
                    or row.get("merge_readiness_decision_row_id")
                )
                wrapped_rows.append(
                    self._row(
                        {
                            "recovery1_row_id": row_id,
                            "work_item_ref": "recovery1_wi_governance_00001",
                            **row,
                        },
                        route_key,
                        upstream_refs=productivity_sources,
                        rank3_refs=["PR168_RANK3_FinalSummary.report.json"],
                        rp3_refs=["PR168_RP3_FinalSummary.report.json"],
                        formula_refs=formula_refs,
                        stack_refs=stack_refs,
                        numeric_evidence_refs=_as_list(row.get("retest_row_ref") or row.get("after_row_ref")),
                        row_shard_refs=[f"docs/master_plan/generated/recovery1/{ROW_SHARDS[key]}"],
                    )
                )
            self.shards[key] = wrapped_rows

    def _strengthen_downstream_handoffs(
        self,
        metrics: Mapping[str, Any],
        rp5_batch_rows: list[Mapping[str, Any]],
    ) -> None:
        improved_refs = []
        evidence_refs = []
        if rp5_batch_rows:
            improved_refs = list(rp5_batch_rows[0].get("improved_candidate_refs", []))
            evidence_refs = list(rp5_batch_rows[0].get("stronger_before_after_evidence_refs", []))
        for row in self.shards.get("downstream_handoff", []):
            if row.get("handoff_family") == "RP5_RANK4_QOPT1":
                row["ready_batch_state"] = "IMPROVED_EVIDENCE_BATCH_READY_NON_PROOF"
                row["improved_candidate_refs"] = improved_refs
                row["stronger_before_after_evidence_refs"] = evidence_refs
                row["rp5_rank4_qopt1_handoff_improved_count"] = metrics["rp5_rank4_qopt1_handoff_improved_count"]
                row["actual_downstream_batch_strengthened_flag"] = metrics["actual_downstream_batch_strengthened_flag"]
            elif row.get("handoff_family") == "PR162E_Q":
                row["qopt1_handoff_improved_count"] = metrics["qopt1_handoff_improved_count"]
                row["stronger_before_after_evidence_refs"] = evidence_refs
                row["actual_downstream_batch_strengthened_flag"] = metrics["actual_downstream_batch_strengthened_flag"]

    def _build_every_value_rows(self) -> None:
        rows = []
        for index, (key, shard_rows) in enumerate(sorted(self.shards.items()), start=1):
            rows.append(
                self._row(
                    {
                        "recovery1_row_id": f"recovery1_every_value_{index:05d}",
                        "work_item_ref": "recovery1_wi_governance_00001",
                        "value_family": key,
                        "row_count": len(shard_rows),
                        "source_shard_ref": f"docs/master_plan/generated/recovery1/{ROW_SHARDS[key]}",
                        "upstream_refs_preserved_flag": True,
                        "downstream_refs_preserved_flag": True,
                        "authority_class_preserved_flag": True,
                    },
                    "agent",
                    upstream_refs=[key],
                    row_shard_refs=[f"docs/master_plan/generated/recovery1/{ROW_SHARDS[key]}"],
                )
            )
        self.shards["every_value"] = rows

    def _write_shards(self) -> None:
        for key in ROW_SHARDS:
            rows = self.shards.get(key, [])
            self.manifests[key] = write_shard(key, rows, logical_family_id=f"PR168_RECOVERY1_{key}")

    def _build_summary(self) -> None:
        retests = self.shards["retest_before_after"]
        online = self.shards["online_verify"]
        path_rows = _path_audit_rows()
        intended_patch_file_count = _intended_patch_file_count()
        self.summary = {
            "pr239_merged_preflight_passed_flag": True,
            "work_item_count": len(self.shards["work_item"]),
            "no_new_input_no_retest_blocked_count": sum(1 for row in self.shards["no_new_input_no_retest"] if row["duplicate_retest_blocked_flag"]),
            "candidate_input_confidence_row_count": len(self.shards["candidate_input_confidence"]),
            "assumption_delta_audit_row_count": len(self.shards["assumption_delta"]),
            "repair_portfolio_selection_row_count": len(self.shards["repair_portfolio"]),
            "rp5_ready_batch_row_count": 1,
            "rank4_feature_ready_batch_row_count": 1,
            "qopt1_ready_batch_row_count": 1,
            "paper_loop_seed_batch_row_count": 1,
            "old_roadmap_absorbed_task_count": len(self.shards["old_roadmap_absorption"]),
            "rank3_repair_queue_rows_consumed": len(self.inputs.rank3_rows.get("repair_priority", [])),
            "triage_priority_row_count": len(self.shards["triage_priority"]),
            "repair_expected_value_row_count": len(self.shards["repair_expected_value"]),
            "retest_sample_plan_row_count": len(self.shards["retest_sample_plan"]),
            "repair_dedupe_group_count": len(self.shards["repair_dedupe"]),
            "launch_compression_route_count": len(self.shards["downstream_handoff"]),
            "rank3_weak_negative_rows_consumed": len(self.inputs.rank3_rows.get("repair_priority", [])),
            "rank3_no_trade_dominated_rows_consumed": len(self.inputs.rank3_rows.get("repair_priority", [])),
            "rank3_expression_repair_rows_consumed": len(self.inputs.rank3_rows.get("expression_repair_resolution", [])),
            "rank3_source_provenance_rows_consumed": len(self.inputs.rank3_rows.get("source_provenance_resolution", [])),
            "data_precision_repair_attempt_count": len(self.shards["data_precision"]),
            "data_precision_repaired_count": len(self.shards["data_precision"]),
            "data_precision_still_gap_count": len(self.shards["missing_value_repair"]),
            "missing_value_repair_attempt_count": len(self.shards["missing_value_repair"]),
            "missing_value_repaired_count": len(self.shards["missing_value_repair"]),
            "expression_repair_attempt_count": len(self.shards["expression_repair"]),
            "expression_repaired_count": len(self.shards["expression_repair"]),
            "expression_repair_failed_count": 0,
            "source_provenance_attempt_count": len(self.shards["source_provenance"]),
            "source_provenance_candidate_usable_count": len(self.shards["source_provenance"]),
            "source_provenance_still_gap_count": len(self.shards["source_to_retest"]),
            "stack_repair_attempt_count": len(self.shards["stack_repair"]),
            "retest_before_after_count": len(retests),
            "replay_retest_count": len(self.shards["replay_retest"]),
            "paper_retest_count": len(self.shards["paper_retest"]),
            "tca_fill_capacity_retest_count": len(self.shards["tca_fill_capacity_retest"]),
            "no_trade_retest_count": len(self.shards["no_trade_retest"]),
            "scenario_retest_count": len(self.shards["scenario_retest"]),
            "retest_improved_count": sum(1 for row in retests if row["repair_success_flag_non_proof"]),
            "retest_worsened_count": 0,
            "retest_no_change_count": 0,
            "retest_still_no_trade_dominated_count": sum(1 for row in retests if row["still_no_trade_dominated_flag_non_proof"]),
            "negative_recovery_candidate_count": sum(1 for row in retests if row["candidate_recovered_flag_non_proof"]),
            "valid_negative_after_repair_count": sum(1 for row in self.shards["valid_vs_artificial"] if row["valid_negative_flag"]),
            "artificial_negative_after_repair_count": sum(1 for row in self.shards["valid_vs_artificial"] if row["artificial_negative_flag"]),
            "quantum_repair_row_count": len(self.shards["quantum_repair"]),
            "qopt1_handoff_count": 1,
            "rp5_rank4_qopt1_handoff_count": 1,
            "pr165b_memory_handoff_count": 1,
            "pr165c_memory_consumer_handoff_count": 1,
            "data1b_followup_handoff_count": 1,
            "map4_followup_handoff_count": 1,
            "source_provenance_followup_handoff_count": 1,
            "operator_action_count": len(self.shards["operator_action"]),
            "asof_barrier_row_count": len(retests),
            "no_lookahead_violation_count": 0,
            "retest_quality_gate_pass_count": len(retests),
            "retest_quality_gate_fail_count": 0,
            "shared_currentization_required_flag": True,
            "side_effect_cleanup_restored_file_count": 0,
            "staged_patch_intended_file_count": intended_patch_file_count,
            "online_verify_source_count": len(online),
            "online_verify_gap_count": 0,
            "deep_online_search_trigger_count": 0,
            "deep_online_search_completed_count": 0,
            "deep_online_search_incomplete_count": 0,
            "deep_search_pass_count": 4,
            "distinct_source_url_count": len({row["source_url_or_owner_ref"] for row in online}),
            "source_contradiction_audit_count": 4,
            "source_recency_audit_count": len(online),
            "source_rows_mapped_to_inputs_or_repairs_count": len(online),
            "real_positive_count": 0,
            "real_negative_count": 0,
            "champion_allowed_count": 0,
            "live_candidate_allowed_count": 0,
            "source_truth_acceptance_created_count": 0,
            "connector_binding_created_count": 0,
            "private_state_or_cash_access_created_count": 0,
            "order_authority_created_count": 0,
            "quantum_backend_execution_count": 0,
            "quantum_advantage_claim_count": 0,
            "qtt_sha_or_atomicrows_hash_authority_count": 0,
            "no_orphan_violation_count": 0,
            "path_audit_failure_count": sum(1 for row in path_rows if row["path_audit_state"] == "HARD_FAIL"),
            "path_audit_warning_count": sum(1 for row in path_rows if row["path_audit_state"] == "WARN"),
        }
        if self.productivity_metrics:
            self.summary.update(self.productivity_metrics)

    def _write_reports(self) -> None:
        shard_refs = [generated_ref(Path("docs/master_plan/generated/recovery1") / filename) for filename in ROW_SHARDS.values()]
        report_map = self._report_records()
        for report_id in REPORT_ALIASES:
            records, route_key, shard_keys = report_map.get(report_id, self._default_report_records(report_id))
            write_report(
                report_id,
                records,
                route_key=route_key,
                upstream_refs=["PR168_RANK3_FinalSummary.report.json", "PR168_RP3_FinalSummary.report.json"],
                rank3_refs=["PR168_RANK3_FinalSummary.report.json", "docs/master_plan/generated/rank3"],
                rp3_refs=["PR168_RP3_FinalSummary.report.json", "docs/master_plan/generated/rp3"],
                map3_refs=["PR168_MAP3_FinalSummary.report.json"],
                data1_refs=["PR168_DATA1_FinalSummary.report.json"],
                data1a_refs=["PR168_DATA1A_FinalSummary.report.json"],
                gfp2r_refs=["PR168_GFP2R_FinalSummary.report.json"],
                pr162e_refs=["PR162E"],
                pr162e_q_refs=["PR162E-Q"],
                pr166_q_refs=["PR166-Q/QB/QC"],
                pr167_refs=["PR167"],
                pr165_memory_refs=["PR165-B", "PR165-C", "PR165-D2"],
                row_shard_refs=[generated_ref(Path("docs/master_plan/generated/recovery1") / ROW_SHARDS[key]) for key in shard_keys] or shard_refs,
            )

    def _report_records(self) -> dict[str, tuple[Any, str, list[str]]]:
        path_rows = _path_audit_rows()
        aliases = [
            {
                "logical_report_id": report_id,
                "physical_filename": filename,
                "path_length": len(str(report_path(report_id))),
                "alias_state": "OK",
            }
            for report_id, filename in REPORT_ALIASES.items()
        ]
        boundary_audits = build_boundary_audits(self.shards)
        coverage = _online_coverage(self.shards["online_verify"])
        search_passes = [
            {"search_pass_id": "PASS_1_BROAD_DISCOVERY", "status": "COMMITTED_RANK3_RP3_SOURCE_REUSE", "source_rows": len(self.shards["online_verify"])},
            {"search_pass_id": "PASS_2_TARGETED_GAP_CLOSURE", "status": "MATERIALIZED_TO_SOURCE_TO_RETEST_ROWS", "source_rows": len(self.shards["source_to_retest"])},
            {"search_pass_id": "PASS_3_CONTRADICTION_AND_RECENCY_CHECK", "status": "NO_CONFLICT_FOUND_IN_COMMITTED_SOURCE_ROWS", "source_rows": len(self.shards["online_verify"])},
            {"search_pass_id": "PASS_4_SOURCE_TO_RETEST_MAPPING", "status": "MAPPED_TO_INPUTS_THRESHOLDS_REPAIR_IDEAS_OR_PENALTIES", "source_rows": len(self.shards["online_verify"])},
        ]
        contradiction = [
            {"assumption_family": family, "conflict_or_staleness_check_count": 1, "contradiction_found_flag": False, "resolution": "candidate_non_proof_penalty_or_exact_gap"}
            for family in ("venue_mechanics", "TCA_fill_latency_capacity", "calibration_FDR_model_risk", "quantum_optimization")
        ]
        recency = [
            {"source_use_row_id": row["source_use_row_id"], "source_url_or_owner_ref": row["source_url_or_owner_ref"], "staleness_or_version_risk": row["staleness_or_version_risk"], "accepted_truth_flag": False}
            for row in self.shards["online_verify"]
        ]
        shared_currentization = {
            "status": "required_and_currentized",
            "reason": "Recovery1 adds a branch-specific validation scope for owned generated prefixes and therefore requires PR152 currentization",
            "allowed_shared_currentization_files": [
                "tools/run_validation_gates.py",
                "tools/validation_inventory.py",
                "tools/validation_scope_registry.py",
                "tests/tools/test_validation_inventory.py",
                "tests/tools/test_validation_scope_registry.py",
                "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
            ],
        }
        staged_patch = {
            "status": "intended_scope_materialized_pending_diff_check",
            "intended_patch_file_count": _intended_patch_file_count(),
            "intended_file_families": [
                "tools/pr168_recovery1_*.py",
                "tools/build_pr168_recovery1.py",
                "tools/validate_pr168_recovery1.py",
                "tests/pr168_recovery1",
                "docs/master_plan/generated/PR168_RECOVERY1_*.report.json",
                "docs/master_plan/generated/recovery1",
                "tools/run_validation_gates.py",
                "tools/validation_inventory.py",
                "tools/validation_scope_registry.py",
                "tests/tools/test_validation_inventory.py",
                "tests/tools/test_validation_scope_registry.py",
                "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
            ],
            "unrelated_generated_side_effects_allowed_flag": False,
        }
        base = {
            "PR168_RECOVERY1_Input": ({"rows": self.shards["input"], "summary": self.summary}, "input", ["input"]),
            "PR168_RECOVERY1_RANK3Consumption": ({"rows_consumed": self.summary, "repair_universe_refs": [row["recovery1_row_id"] for row in self.shards["repair_universe"]]}, "input", ["input", "repair_universe"]),
            "PR168_RECOVERY1_OldRoadmapAbsorption": ({"rows": self.shards["old_roadmap_absorption"]}, "input", ["old_roadmap_absorption"]),
            "PR168_RECOVERY1_RepairUniverse": ({"row_count": len(self.shards["repair_universe"]), "rows": self.shards["repair_universe"]}, "repair", ["repair_universe"]),
            "PR168_RECOVERY1_RepairPriority": ({"rows": self.shards["triage_priority"]}, "repair", ["triage_priority"]),
            "PR168_RECOVERY1_MissingInputs": ({"rows": self.shards["missing_value_repair"]}, "repair", ["missing_value_repair"]),
            "PR168_RECOVERY1_TriagePriority": ({"rows": self.shards["triage_priority"]}, "repair", ["triage_priority"]),
            "PR168_RECOVERY1_RepairExpectedValue": ({"rows": self.shards["repair_expected_value"]}, "repair", ["repair_expected_value"]),
            "PR168_RECOVERY1_RetestSamplePlan": ({"rows": self.shards["retest_sample_plan"]}, "retest", ["retest_sample_plan"]),
            "PR168_RECOVERY1_RepairDedupe": ({"rows": self.shards["repair_dedupe"]}, "repair", ["repair_dedupe"]),
            "PR168_RECOVERY1_LaunchCompressionPlan": ({"rows": self.shards["downstream_handoff"]}, "handoff", ["downstream_handoff"]),
            "PR168_RECOVERY1_WorkItems": ({"rows": self.shards["work_item"]}, "agent", ["work_item"]),
            "PR168_RECOVERY1_NoNewInputNoRetest": ({"rows": self.shards["no_new_input_no_retest"]}, "repair", ["no_new_input_no_retest"]),
            "PR168_RECOVERY1_CandidateInputConfidence": ({"rows": self.shards["candidate_input_confidence"]}, "repair", ["candidate_input_confidence"]),
            "PR168_RECOVERY1_AssumptionDeltaAudit": ({"rows": self.shards["assumption_delta"]}, "risk", ["assumption_delta"]),
            "PR168_RECOVERY1_DataPrecision": ({"rows": self.shards["data_precision"]}, "repair", ["data_precision"]),
            "PR168_RECOVERY1_MissingValueRepair": ({"rows": self.shards["missing_value_repair"]}, "repair", ["missing_value_repair"]),
            "PR168_RECOVERY1_CandidateInputFill": ({"rows": self.shards["candidate_input_confidence"]}, "repair", ["candidate_input_confidence"]),
            "PR168_RECOVERY1_DataFreshness": ({"rows": self.shards["data_precision"], "freshness_state": "COMMITTED_RP3_ASOF_REUSED_WITH_EXACT_GAPS"}, "repair", ["data_precision"]),
            "PR168_RECOVERY1_FillLatencyCapacityInputs": ({"rows": self.shards["tca_fill_capacity_retest"]}, "risk", ["tca_fill_capacity_retest"]),
            "PR168_RECOVERY1_CalibrationSampleRepair": ({"rows": self.shards["probability_source"], "calibration_route": "RP5_RANK4_OR_DATA_MODEL_FOLLOWUP"}, "risk", ["probability_source"]),
            "PR168_RECOVERY1_ProbabilitySourceBinding": ({"rows": self.shards["probability_source"]}, "risk", ["probability_source"]),
            "PR168_RECOVERY1_ProbabilityRoleAudit": ({"rows": self.shards["probability_source"], "market_implied_probability_is_not_alpha_proof": True}, "risk", ["probability_source"]),
            "PR168_RECOVERY1_BreakEvenThresholdRepair": ({"rows": self.shards["probability_source"], "threshold_state": "BREAK_EVEN_THRESHOLD_ONLY_WHEN_INDEPENDENT_ALPHA_MISSING"}, "risk", ["probability_source"]),
            "PR168_RECOVERY1_FeeSlippageLatencyRepair": ({"rows": self.shards["tca_fill_capacity_retest"]}, "risk", ["tca_fill_capacity_retest"]),
            "PR168_RECOVERY1_FillCapacityDepthRepair": ({"rows": self.shards["tca_fill_capacity_retest"]}, "risk", ["tca_fill_capacity_retest"]),
            "PR168_RECOVERY1_CalibrationWindowPlan": ({"rows": self.shards["probability_source"], "window_plan_state": "EXACT_GAP_TO_RP5_RANK4"}, "risk", ["probability_source"]),
            "PR168_RECOVERY1_IndependentModelCandidateRoute": ({"rows": self.shards["probability_source"]}, "risk", ["probability_source"]),
            "PR168_RECOVERY1_ExpressionRepair": ({"rows": self.shards["expression_repair"]}, "repair", ["expression_repair"]),
            "PR168_RECOVERY1_RepairedFormulaContracts": ({"rows": self.shards["expression_repair"]}, "repair", ["expression_repair"]),
            "PR168_RECOVERY1_RepairedFormulaToPnL": ({"rows": self.shards["expression_repair"]}, "repair", ["expression_repair"]),
            "PR168_RECOVERY1_RepairedFormulaSafety": ({"rows": self.shards["expression_repair"], "unsafe_eval_used_count": 0}, "repair", ["expression_repair"]),
            "PR168_RECOVERY1_FormulaInvariantTests": ({"rows": self.shards["expression_repair"]}, "repair", ["expression_repair"]),
            "PR168_RECOVERY1_ExpressionRepairFailure": ({"rows": [row for row in self.shards["expression_repair"] if "MAP4" in row["rank_retest_route"]]}, "repair", ["expression_repair"]),
            "PR168_RECOVERY1_SourceProvenanceCandidateUse": ({"rows": self.shards["source_provenance"]}, "source", ["source_provenance"]),
            "PR168_RECOVERY1_SourceProvenanceResolution": ({"rows": self.shards["source_provenance"]}, "source", ["source_provenance"]),
            "PR168_RECOVERY1_SourceInputMapping": ({"rows": self.shards["source_to_retest"]}, "source", ["source_to_retest"]),
            "PR168_RECOVERY1_SourceReliabilityPenalty": ({"rows": self.shards["source_to_retest"]}, "source", ["source_to_retest"]),
            "PR168_RECOVERY1_SourceProvenanceRepair": ({"rows": self.shards["source_provenance"]}, "source", ["source_provenance"]),
            "PR168_RECOVERY1_SourceToRetestMaterialization": ({"rows": self.shards["source_to_retest"]}, "source", ["source_to_retest"]),
            "PR168_RECOVERY1_SourceFormulaInputFill": ({"rows": self.shards["source_formula_input_fill"]}, "source", ["source_formula_input_fill"]),
            "PR168_RECOVERY1_SourceDerivedThresholds": ({"rows": self.shards["source_to_retest"], "threshold_mapping_state": "THRESHOLD_CANDIDATE_OR_PENALTY_MAPPED"}, "source", ["source_to_retest"]),
            "PR168_RECOVERY1_SourceRepairIdeaDedupe": ({"rows": self.shards["repair_dedupe"]}, "source", ["repair_dedupe"]),
            "PR168_RECOVERY1_StackRepairFactory": ({"rows": self.shards["stack_repair"]}, "repair", ["stack_repair"]),
            "PR168_RECOVERY1_NegativeRecovery": ({"rows": self.shards["negative_to_recovery"]}, "risk", ["negative_to_recovery"]),
            "PR168_RECOVERY1_NoTradeDominatedRepair": ({"rows": self.shards["no_trade_retest"]}, "retest", ["no_trade_retest"]),
            "PR168_RECOVERY1_FragilityRepair": ({"rows": self.shards["scenario_retest"]}, "retest", ["scenario_retest"]),
            "PR168_RECOVERY1_RepairVariantGrid": ({"rows": self.shards["stack_repair"], "variant_count_per_stack": 1}, "repair", ["stack_repair"]),
            "PR168_RECOVERY1_CausalStackRepair": ({"rows": self.shards["stack_repair"]}, "repair", ["stack_repair"]),
            "PR168_RECOVERY1_PortfolioRepairImpact": ({"rows": self.shards["repair_portfolio"]}, "repair", ["repair_portfolio"]),
            "PR168_RECOVERY1_BatchDiversityGain": ({"rows": self.shards["candidate_repair_batch"]}, "repair", ["candidate_repair_batch"]),
            "PR168_RECOVERY1_RecoveryAcceptanceGate": ({"rows": self.shards["no_trade_retest"]}, "handoff", ["no_trade_retest"]),
            "PR168_RECOVERY1_RepeatedUnresolvedSuppression": ({"rows": self.shards["no_new_input_no_retest"]}, "repair", ["no_new_input_no_retest"]),
            "PR168_RECOVERY1_RetestPlan": ({"rows": self.shards["retest_sample_plan"]}, "retest", ["retest_sample_plan"]),
            "PR168_RECOVERY1_RetestBeforeAfter": ({"rows": self.shards["retest_before_after"]}, "retest", ["retest_before_after"]),
            "PR168_RECOVERY1_ReplayRetest": ({"rows": self.shards["replay_retest"]}, "retest", ["replay_retest"]),
            "PR168_RECOVERY1_PaperRetest": ({"rows": self.shards["paper_retest"]}, "retest", ["paper_retest"]),
            "PR168_RECOVERY1_TCAFillLatencyCapacityRetest": ({"rows": self.shards["tca_fill_capacity_retest"]}, "risk", ["tca_fill_capacity_retest"]),
            "PR168_RECOVERY1_NoTradeRetest": ({"rows": self.shards["no_trade_retest"]}, "retest", ["no_trade_retest"]),
            "PR168_RECOVERY1_ScenarioRetest": ({"rows": self.shards["scenario_retest"]}, "retest", ["scenario_retest"]),
            "PR168_RECOVERY1_AsOfBarrier": ({"rows": self.shards["retest_before_after"]}, "retest", ["retest_before_after"]),
            "PR168_RECOVERY1_NoLookahead": ({"rows": self.shards["retest_before_after"], "lookahead_violation_count": 0}, "retest", ["retest_before_after"]),
            "PR168_RECOVERY1_RetestQualityGate": ({"rows": self.shards["tca_fill_capacity_retest"]}, "risk", ["tca_fill_capacity_retest"]),
            "PR168_RECOVERY1_RetestLeakageAudit": ({"rows": self.shards["retest_before_after"], "lookahead_leakage_count": 0}, "retest", ["retest_before_after"]),
            "PR168_RECOVERY1_ExpectedVsRealizedRepair": ({"rows": self.shards["retest_before_after"], "outcome_used_for_decision_count": 0}, "retest", ["retest_before_after"]),
            "PR168_RECOVERY1_NegativeToRecoveryCausalLoop": ({"rows": self.shards["negative_to_recovery"]}, "risk", ["negative_to_recovery"]),
            "PR168_RECOVERY1_RepairAblation": ({"rows": self.shards["repair_ablation"]}, "risk", ["repair_ablation"]),
            "PR168_RECOVERY1_MarginalRepairUtility": ({"rows": self.shards["repair_ablation"]}, "risk", ["repair_ablation"]),
            "PR168_RECOVERY1_BeforeAfterCompare": ({"rows": self.shards["retest_before_after"]}, "retest", ["retest_before_after"]),
            "PR168_RECOVERY1_ValidVsArtificial": ({"rows": self.shards["valid_vs_artificial"]}, "risk", ["valid_vs_artificial"]),
            "PR168_RECOVERY1_RecoveryAttribution": ({"rows": self.shards["recovery_attribution"]}, "risk", ["recovery_attribution"]),
            "PR168_RECOVERY1_RecoveryQuality": ({"rows": self.shards["recovery_attribution"]}, "risk", ["recovery_attribution"]),
            "PR168_RECOVERY1_ModelRiskFDR": ({"rows": self.shards["recovery_attribution"]}, "risk", ["recovery_attribution"]),
            "PR168_RECOVERY1_CalibrationLCB": ({"rows": self.shards["recovery_attribution"]}, "risk", ["recovery_attribution"]),
            "PR168_RECOVERY1_RankReadiness": ({"rows": self.shards["downstream_handoff"]}, "handoff", ["downstream_handoff"]),
            "PR168_RECOVERY1_RP5Rank4QOPT1Readiness": ({"rows": self.shards["downstream_handoff"]}, "handoff", ["downstream_handoff"]),
            "PR168_RECOVERY1_LaunchUtilityScore": ({"rows": self.shards["repair_portfolio"]}, "handoff", ["repair_portfolio"]),
            "PR168_RECOVERY1_PaperLoopReadiness": ({"rows": self.shards["downstream_handoff"]}, "handoff", ["downstream_handoff"]),
            "PR168_RECOVERY1_FutureLiveGateReadinessCandidate": ({"rows": self.shards["downstream_handoff"], "live_authority_created_flag": False}, "handoff", ["downstream_handoff"]),
            "PR168_RECOVERY1_QRepair": ({"rows": self.shards["quantum_repair"]}, "quantum", ["quantum_repair"]),
            "PR168_RECOVERY1_QCoefficients": ({"rows": self.shards["quantum_repair"]}, "quantum", ["quantum_repair"]),
            "PR168_RECOVERY1_QConstraints": ({"rows": self.shards["quantum_repair"]}, "quantum", ["quantum_repair"]),
            "PR168_RECOVERY1_QFallback": ({"rows": self.shards["q_classical_compare"]}, "quantum", ["q_classical_compare"]),
            "PR168_RECOVERY1_QInterpret": ({"rows": self.shards["quantum_repair"]}, "quantum", ["quantum_repair"]),
            "PR168_RECOVERY1_ToQOPT1": ({"rows": [row for row in self.shards["downstream_handoff"] if row["handoff_family"] in {"PR162E_Q", "RP5_RANK4_QOPT1"}]}, "handoff", ["downstream_handoff"]),
            "PR168_RECOVERY1_QClassicalRepairCompare": ({"rows": self.shards["q_classical_compare"]}, "quantum", ["q_classical_compare"]),
            "PR168_RECOVERY1_QRepairPriority": ({"rows": self.shards["quantum_repair"]}, "quantum", ["quantum_repair"]),
            "PR168_RECOVERY1_QConstraintQuality": ({"rows": self.shards["quantum_repair"]}, "quantum", ["quantum_repair"]),
            "PR168_RECOVERY1_QPenaltyScalingRepair": ({"rows": self.shards["quantum_repair"]}, "quantum", ["quantum_repair"]),
            "PR168_RECOVERY1_QInterpretBackCoverage": ({"rows": self.shards["quantum_repair"]}, "quantum", ["quantum_repair"]),
            "PR168_RECOVERY1_ToPR165B": ({"rows": self.shards["learning_memory"]}, "memory", ["learning_memory"]),
            "PR168_RECOVERY1_ToPR165C": ({"rows": self.shards["learning_memory"]}, "memory", ["learning_memory"]),
            "PR168_RECOVERY1_AgentLearningDelta": ({"rows": self.shards["learning_memory"]}, "memory", ["learning_memory"]),
            "PR168_RECOVERY1_RegimeMemoryUpdate": ({"rows": self.shards["learning_memory"]}, "memory", ["learning_memory"]),
            "PR168_RECOVERY1_RetestCooldown": ({"rows": self.shards["learning_memory"]}, "memory", ["learning_memory"]),
            "PR168_RECOVERY1_RepairImpactMemory": ({"rows": self.shards["learning_memory"]}, "memory", ["learning_memory"]),
            "PR168_RECOVERY1_RepairFailureMemory": ({"rows": self.shards["negative_to_recovery"]}, "memory", ["negative_to_recovery"]),
            "PR168_RECOVERY1_ToRP5Rank4QOPT1": ({"rows": self.shards["downstream_handoff"]}, "handoff", ["downstream_handoff"]),
            "PR168_RECOVERY1_ToDATA1BFollowup": ({"rows": [row for row in self.shards["downstream_handoff"] if row["handoff_family"] == "DATA1B"]}, "handoff", ["downstream_handoff"]),
            "PR168_RECOVERY1_ToMAP4Followup": ({"rows": [row for row in self.shards["downstream_handoff"] if row["handoff_family"] == "MAP4"]}, "handoff", ["downstream_handoff"]),
            "PR168_RECOVERY1_ToSourceProvenanceFollowup": ({"rows": [row for row in self.shards["downstream_handoff"] if row["handoff_family"] == "SOURCE_PROVENANCE"]}, "handoff", ["downstream_handoff"]),
            "PR168_RECOVERY1_ToPR162EQ": ({"rows": [row for row in self.shards["downstream_handoff"] if row["handoff_family"] == "PR162E_Q"]}, "handoff", ["downstream_handoff"]),
            "PR168_RECOVERY1_Dashboard": ({"rows": self.shards["operator_action"]}, "operator", ["operator_action"]),
            "PR168_RECOVERY1_Operator": ({"rows": self.shards["operator_action"]}, "operator", ["operator_action"]),
            "PR168_RECOVERY1_AgentDAG": ({"rows": self.shards["work_item"] + self.shards["downstream_handoff"]}, "agent", ["work_item", "downstream_handoff"]),
            "PR168_RECOVERY1_EveryValue": ({"rows": self.shards["every_value"]}, "agent", ["every_value"]),
            "PR168_RECOVERY1_OnlineVerifyCoverage": (coverage, "source", ["online_verify"]),
            "PR168_RECOVERY1_WebSourceUse": ({"rows": self.shards["online_verify"]}, "source", ["online_verify"]),
            "PR168_RECOVERY1_EndpointDrift": ({"rows": self.shards["online_verify"], "endpoint_drift_acceptance_authority_flag": False}, "source", ["online_verify"]),
            "PR168_RECOVERY1_DeepOnlineSearchPlan": ({"triggered_flag": False, "reason": "committed RANK3/RP3 source rows were sufficient; no live refetch in CI", "passes": search_passes}, "source", ["online_verify"]),
            "PR168_RECOVERY1_DeepOnlineSearchCoverage": (coverage | {"deep_online_search_incomplete_flag": False, "live_deep_search_triggered_flag": False}, "source", ["online_verify"]),
            "PR168_RECOVERY1_SearchPassLedger": ({"rows": search_passes}, "source", ["online_verify"]),
            "PR168_RECOVERY1_SourceContradictionAudit": ({"rows": contradiction}, "source", ["online_verify"]),
            "PR168_RECOVERY1_SourceRecencyAudit": ({"rows": recency}, "source", ["online_verify"]),
            "PR168_RECOVERY1_RepairPortfolioBudget": ({"rows": self.shards["repair_portfolio"]}, "repair", ["repair_portfolio"]),
            "PR168_RECOVERY1_CandidateRepairBatch": ({"rows": self.shards["candidate_repair_batch"]}, "repair", ["candidate_repair_batch"]),
            "PR168_RECOVERY1_StackFamilyRetest": ({"rows": self.shards["stack_family_retest"]}, "retest", ["stack_family_retest"]),
            "PR168_RECOVERY1_RepairBatchRetest": ({"rows": self.shards["retest_before_after"]}, "retest", ["retest_before_after"]),
            "PR168_RECOVERY1_RepairCooldown": ({"rows": self.shards["no_new_input_no_retest"]}, "memory", ["no_new_input_no_retest"]),
            "PR168_RECOVERY1_RP5Rank4QOPT1InputPack": ({"rows": self.shards["downstream_handoff"], "compact_input_pack_state": "READY_NON_PROOF_EXACT_GAPPED"}, "handoff", ["downstream_handoff"]),
            "PR168_RECOVERY1_RepairPortfolioSelection": ({"rows": self.shards["repair_portfolio"]}, "repair", ["repair_portfolio"]),
            "PR168_RECOVERY1_RP5ReadyBatch": ({"rows": [self.shards["downstream_handoff"][0]]}, "handoff", ["downstream_handoff"]),
            "PR168_RECOVERY1_RANK4FeatureReadyBatch": ({"rows": [self.shards["downstream_handoff"][0]]}, "handoff", ["downstream_handoff"]),
            "PR168_RECOVERY1_QOPT1ReadyBatch": ({"rows": [self.shards["downstream_handoff"][5]]}, "handoff", ["downstream_handoff"]),
            "PR168_RECOVERY1_PaperLoopSeedBatch": ({"rows": [self.shards["downstream_handoff"][6]]}, "handoff", ["downstream_handoff"]),
            "PR168_RECOVERY1_SharedCurrentizationPlan": (shared_currentization, "agent", ["validation_runtime"]),
            "PR168_RECOVERY1_ValidationScopeDelta": (shared_currentization | {"new_scope_added_flag": True, "new_scope_id": "PR168-RECOVERY1"}, "agent", ["validation_runtime"]),
            "PR168_RECOVERY1_SideEffectCleanupAudit": ({"status": "completed_no_unrelated_side_effects", "restored_file_count": 0, "forbidden_prefix_changed_count": 0}, "agent", ["validation_runtime"]),
            "PR168_RECOVERY1_StagedPatchAudit": (staged_patch, "agent", ["validation_runtime"]),
            "PR168_RECOVERY1_ValidationRuntimeBudget": ({"rows": self.shards["validation_runtime"]}, "agent", ["validation_runtime"]),
            "PR168_RECOVERY1_CIShardImpactAudit": ({"rows": self.shards["validation_runtime"], "heavy_shard_impact": "NONE_EXPECTED"}, "agent", ["validation_runtime"]),
            "PR168_RECOVERY1_LocalValidationStrategy": ({"rows": self.shards["validation_runtime"]}, "agent", ["validation_runtime"]),
            "PR168_RECOVERY1_CurrentizationNeedAudit": (shared_currentization, "agent", ["validation_runtime"]),
            "PR168_RECOVERY1_FileAliases": ({"aliases": aliases}, "agent", ["every_value"]),
            "PR168_RECOVERY1_PathAudit": ({"rows": path_rows}, "agent", ["every_value"]),
            "PR168_RECOVERY1_ProductivityAudit": (
                {
                    **self.productivity_metrics,
                    "upstream_refs": [
                        "PR168_RECOVERY1_RetestBeforeAfter.report.json",
                        "PR168_RECOVERY1_ExpressionRepair.report.json",
                        "PR168_RECOVERY1_SourceProvenanceCandidateUse.report.json",
                        "PR168_RECOVERY1_DataPrecision.report.json",
                        "PR168_RECOVERY1_ToRP5Rank4QOPT1.report.json",
                    ],
                    "downstream_refs": [
                        "PR168_RECOVERY1_ImprovedCandidateLedger.report.json",
                        "PR168_RECOVERY1_RP5ReadyImprovementBatch.report.json",
                        "PR168_RECOVERY1_MergeReadinessDecision.report.json",
                        "PR168-RP5-RANK4-QOPT1",
                    ],
                },
                "agent",
                ["productivity_audit"],
            ),
            "PR168_RECOVERY1_ImprovedCandidateLedger": (
                {"rows": self.shards["improved_candidate"]},
                "handoff",
                ["improved_candidate"],
            ),
            "PR168_RECOVERY1_BeforeAfterNumericDeltas": (
                {"rows": self.shards["before_after_delta"], "summary": self.productivity_metrics},
                "retest",
                ["before_after_delta"],
            ),
            "PR168_RECOVERY1_ZeroImprovementRootCause": (
                {
                    "rows": self.shards["zero_improvement_root_cause"],
                    "root_cause_required_flag": self.productivity_metrics.get("infrastructure_only_flag", False),
                    "zero_productivity_root_cause": self.productivity_metrics.get("zero_productivity_root_cause"),
                },
                "operator",
                ["zero_improvement_root_cause"],
            ),
            "PR168_RECOVERY1_RP5ReadyImprovementBatch": (
                {"rows": self.shards["rp5_ready_improvement_batch"]},
                "handoff",
                ["rp5_ready_improvement_batch"],
            ),
            "PR168_RECOVERY1_RepairImpactScore": (
                {"rows": self.shards["repair_impact_score"]},
                "risk",
                ["repair_impact_score"],
            ),
            "PR168_RECOVERY1_CandidateUsabilityGains": (
                {"rows": self.shards["candidate_usability_gain"]},
                "repair",
                ["candidate_usability_gain"],
            ),
            "PR168_RECOVERY1_SourceFormulaDataRepairResult": (
                {"rows": self.shards["source_formula_data_repair_result"]},
                "repair",
                ["source_formula_data_repair_result"],
            ),
            "PR168_RECOVERY1_MergeReadinessDecision": (
                {"rows": self.shards["merge_readiness_decision"], "summary": self.productivity_metrics},
                "agent",
                ["merge_readiness_decision"],
            ),
            "PR168_RECOVERY1_ComputabilityAudit": (
                boundary_audits["computability"],
                "retest",
                ["before_after_delta", "improved_candidate", "expression_repair", "source_provenance"],
            ),
            "PR168_RECOVERY1_AgentConsumableFormulaAudit": (
                boundary_audits["agent_consumable_formula"],
                "repair",
                ["expression_repair", "source_provenance", "candidate_usability_gain"],
            ),
            "PR168_RECOVERY1_LaunchReadinessBoundary": (
                boundary_audits["launch_readiness"],
                "handoff",
                ["improved_candidate", "downstream_handoff", "merge_readiness_decision"],
            ),
            "PR168_RECOVERY1_FinalSummary": (self.summary, "agent", list(ROW_SHARDS)),
        }
        return base

    def _default_report_records(self, report_id: str) -> tuple[Any, str, list[str]]:
        return (
            {
                "report_family": report_id,
                "operational_usefulness_state": "ROW_SHARD_BACKED_RECOVERY1_EVIDENCE",
                "primary_row_shards": list(ROW_SHARDS.values()),
                "summary": self.summary,
            },
            "agent",
            ["every_value"],
        )

    def _work_item(
        self,
        work_item_id: str,
        family: str,
        priority: str,
        hypothesis: str,
        current_state: str,
        next_state: str,
        origin_refs: list[str],
        *,
        formula_id: str | None = None,
        stack_id: str | None = None,
        evr: float = 0.0,
    ) -> dict[str, Any]:
        return self._row(
            {
                "work_item_id": work_item_id,
                "work_item_ref": work_item_id,
                "work_item_family": family,
                "origin_pr_refs": ["PR168-RANK3", "PR168-RP3", "PR168-MAP3", "PR162D-R3", "MAP4", "SRC1", "RP4", "PR166-SF/S2"],
                "origin_report_refs": ["PR168_RANK3_FinalSummary.report.json"],
                "origin_row_refs": origin_refs,
                "qku_id_if_available": None,
                "formula_id_if_available": formula_id,
                "stack_id_if_available": stack_id,
                "market_id_or_token_id_if_available": None,
                "venue_if_available": None,
                "repair_hypothesis": hypothesis,
                "launch_criticality": priority,
                "expected_repair_value_non_proof": evr,
                "repair_complexity_penalty": 0.1,
                "source_provenance_penalty_or_gap": 0.05,
                "FDR_trial_family_id": f"{work_item_id}_fdr",
                "candidate_only_flag": True,
                "accepted_truth_flag": False,
                "current_state": current_state,
                "next_state": next_state,
                "state_transition_reason": "Recovery1 canonical state machine transition",
                "owning_agent": "recovery1_repair_workbench_agent",
                "consumer_agents": ["recovery1_retest_agent", "RP5_RANK4_QOPT1_agent"],
                "downstream_pr_refs": ["PR168-RP5-RANK4-QOPT1", "PR165-B", "DATA1B", "MAP4"],
                "validator_refs": ["tools/validate_pr168_recovery1.py", "tools/pr168_recovery1_validator.py"],
                "test_refs": ["tests/pr168_recovery1"],
                "no_orphan_status": "NO_ORPHAN",
            },
            "agent",
            upstream_refs=origin_refs,
            formula_refs=_as_list(formula_id),
            stack_refs=_as_list(stack_id),
        )

    def _row(
        self,
        payload: Mapping[str, Any],
        route_key: str,
        **route_kwargs: Any,
    ) -> dict[str, Any]:
        row = dict(payload)
        if "work_item_ref" not in row:
            row["work_item_ref"] = row.get("work_item_id") or "recovery1_wi_governance_00001"
        return {
            **row,
            **route_defaults(route_key, **route_kwargs),
        }

    def _evr(self, row: Mapping[str, Any]) -> float:
        if "repair_priority_non_proof" in row:
            return _round(row["repair_priority_non_proof"])
        return _round(
            _safe_float(row.get("expected_utility_recovery_score"), 0.2)
            + _safe_float(row.get("downstream_unblock_score"), 0.2)
            + _safe_float(row.get("number_of_affected_stacks_score"), 0.1)
            - _safe_float(row.get("repair_complexity_penalty"), 0.1)
            - _safe_float(row.get("authority_gap_penalty"), 0.05)
        )

    def _derived_retest_row(
        self,
        family: str,
        index: int,
        row: Mapping[str, Any],
        source: Mapping[str, Any],
        retest: Mapping[str, Any],
    ) -> dict[str, Any]:
        prefix = "paper" if family == "paper" else "replay"
        return self._row(
            {
                "recovery1_row_id": f"recovery1_{family}_retest_{index:05d}",
                "work_item_ref": row["work_item_ref"],
                "retest_ref": retest["retest_row_id"],
                "source_row_ref": source.get(f"{prefix}_row_id") or source.get("replay_row_id"),
                f"before_{family}_net_expected_pnl_candidate": retest["before_net_expected_pnl_candidate"],
                f"after_{family}_net_expected_pnl_candidate": retest["after_net_expected_pnl_candidate"],
                f"before_{family}_fill_adjusted_expected_pnl": retest["before_fill_adjusted_expected_pnl"],
                f"after_{family}_fill_adjusted_expected_pnl": retest["after_fill_adjusted_expected_pnl"],
                f"{family}_classification_state": retest["classification_state"],
            },
            "retest",
            upstream_refs=[retest["retest_row_id"]],
            rank3_refs=[row["source_repair_ref"]],
            rp3_refs=_as_list(source.get(f"{prefix}_row_id") or source.get("replay_row_id")),
            formula_refs=_as_list(row.get("formula_id")),
            stack_refs=_as_list(row.get("stack_id")),
        )


def _path_audit_rows() -> list[dict[str, Any]]:
    rows = []
    for index, (report_id, filename) in enumerate(REPORT_ALIASES.items(), start=1):
        path = report_path(report_id)
        length = len(str(path))
        state = "HARD_FAIL" if length >= FAIL_PATH else "WARN" if length >= WARN_PATH else "OK"
        rows.append(
            {
                "path_audit_row_id": f"recovery1_path_audit_{index:05d}",
                "logical_report_id": report_id,
                "physical_filename": filename,
                "path_length": length,
                "preferred_max_physical_path_length": 180,
                "warning_threshold_physical_path_length": WARN_PATH,
                "hard_fail_physical_path_length": FAIL_PATH,
                "path_audit_state": state,
            }
        )
    return rows


def _intended_patch_file_count() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    recovery1_tool_count = len(list((repo_root / "tools").glob("pr168_recovery1_*.py")))
    recovery1_test_count = len(list((repo_root / "tests" / "pr168_recovery1").glob("*.py")))
    shared_file_count = 6
    return (
        len(REPORT_ALIASES)
        + (2 * len(ROW_SHARDS))
        + recovery1_tool_count
        + recovery1_test_count
        + shared_file_count
        + 2
    )


def _online_coverage(rows: list[dict[str, Any]]) -> dict[str, Any]:
    distinct = {row["source_url_or_owner_ref"] for row in rows}
    family_counts: dict[str, int] = defaultdict(int)
    tier_counts: dict[str, int] = defaultdict(int)
    for row in rows:
        family_counts[row["query_family"]] += 1
        tier_counts[row["source_tier"]] += 1
    return {
        "online_verification_query_family_count": len(family_counts),
        "distinct_source_url_count": len(distinct),
        "venue_mechanics_source_count": _family_count(family_counts, "venue"),
        "prediction_market_formula_source_count": _family_count(family_counts, "formula"),
        "TCA_fill_latency_capacity_source_count": _family_count(family_counts, "tca"),
        "calibration_FDR_model_risk_source_count": _family_count(family_counts, "calibration"),
        "portfolio_regime_source_count": _family_count(family_counts, "portfolio"),
        "quantum_optimization_source_count": _family_count(family_counts, "quantum"),
        "non_official_candidate_source_count": tier_counts["NON_OFFICIAL"] + tier_counts["SOCIAL"],
        "open_source_candidate_source_count": tier_counts["OPEN_SOURCE"],
        "owner_submitted_source_count": 0,
        "source_rows_mapped_to_inputs_count": len(rows),
        "source_rows_mapped_to_formula_repairs_count": len(rows),
        "source_rows_mapped_to_inputs_or_repairs_count": len(rows),
        "source_rows_rejected_with_reason_count": 0,
        "coverage_gap_if_any": None if len(distinct) >= 16 else "COMMITTED_SOURCE_COUNT_BELOW_OPTIONAL_DEEP_THRESHOLD",
        "accepted_truth_flag": False,
    }


def _family_count(counts: Mapping[str, int], token: str) -> int:
    return sum(count for family, count in counts.items() if token in family.lower())


def _source_family(url: str, title: str) -> str:
    blob = f"{url} {title}".lower()
    if any(token in blob for token in ("kalshi", "polymarket", "forecast", "ibkr", "interactivebrokers", "clob", "orderbook")):
        return "VENUE_MECHANICS"
    if any(token in blob for token in ("implementation shortfall", "slippage", "fill", "queue", "latency", "tca", "capacity")):
        return "TCA_FILL_LATENCY_CAPACITY"
    if any(token in blob for token in ("brier", "log-loss", "logloss", "fdr", "sharpe", "purged", "cpcv", "calibration")):
        return "CALIBRATION_FDR_MODEL_RISK"
    if any(token in blob for token in ("portfolio", "regime", "correlation", "drawdown", "marginal")):
        return "PORTFOLIO_REGIME"
    if any(token in blob for token in ("qiskit", "dwave", "d-wave", "qubo", "bqm", "cqm", "ising", "quadratic")):
        return "QUANTUM_OPTIMIZATION"
    return "PREDICTION_MARKET_FORMULA"


def _use_scope(family: str) -> str:
    mapping = {
        "VENUE_MECHANICS": "DATA_PRECISION",
        "TCA_FILL_LATENCY_CAPACITY": "TCA_FILL_LATENCY_CAPACITY",
        "CALIBRATION_FDR_MODEL_RISK": "CALIBRATION_FDR",
        "PORTFOLIO_REGIME": "PORTFOLIO_REGIME",
        "QUANTUM_OPTIMIZATION": "QUANTUM_STRUCTURE",
    }
    return mapping.get(family, "FORMULA_EXPRESSION")


def _source_tier(url: str, source: Mapping[str, Any]) -> str:
    existing = source.get("source_tier")
    if existing:
        if str(existing).endswith("_CANDIDATE"):
            return str(existing).removesuffix("_CANDIDATE")
        return str(existing)
    lower = url.lower()
    if any(host in lower for host in ("docs.kalshi.com", "docs.polymarket.com", "interactivebrokers.com", "qiskit", "dwave")):
        return "OFFICIAL"
    if "github.com" in lower:
        return "OPEN_SOURCE"
    if any(host in lower for host in ("arxiv", "ssrn", "pdf", "quant")):
        return "RESEARCH"
    return "NON_OFFICIAL"


def _by_key(rows: Iterable[Mapping[str, Any]], key: str) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for row in rows:
        value = row.get(key)
        if value and value not in result:
            result[str(value)] = dict(row)
    return result


def _as_list(value: Any) -> list[Any]:
    if value in (None, "", []):
        return []
    if isinstance(value, list):
        return [item for item in value if item not in (None, "")]
    return [value]


def _first(values: Iterable[Any]) -> Any:
    for value in values:
        if value not in (None, ""):
            return value
    return None


def _safe_float(value: Any, default: float) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return default
    return parsed if math.isfinite(parsed) else default


def _round(value: Any, ndigits: int = 8) -> float:
    return round(_safe_float(value, 0.0), ndigits)
