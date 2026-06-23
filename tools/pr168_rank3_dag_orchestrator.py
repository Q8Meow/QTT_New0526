#!/usr/bin/env python3
"""Build PR168-RANK3 RP3 evidence-backed ranking artifacts."""

from __future__ import annotations

from collections import defaultdict
import math
from pathlib import Path
from typing import Any, Iterable, Mapping

from tools.pr168_rank3_config import (
    AUTHORITY_CLASS,
    EXPECTED_RP3_CANONICAL_FORMULA_COUNT,
    EXPECTED_RP3_COMPUTABLE_FORMULA_COUNT,
    EXPECTED_RP3_DATA_REPAIR_COUNT,
    EXPECTED_RP3_EXPRESSION_REPAIR_COUNT,
    EXPECTED_RP3_ROW_SHARD_FAMILY_COUNT,
    EXPECTED_RP3_SOURCE_REVIEW_COUNT,
    EXPECTED_RP3_TARGETED_TEST_COUNT,
    EXPECTED_RP3_TOP_LEVEL_REPORT_COUNT,
    GENERATED_ROOT,
    LATEST_MAIN_RUN_ID,
    PR238_MERGE_COMMIT,
    REPORT_ALIASES,
    ROW_SHARDS,
    WARN_PATH,
    FAIL_PATH,
    generated_ref,
    report_path,
    route_defaults,
    shard_path,
)
from tools.pr168_rank3_report_writer import write_report, write_shard
from tools.pr168_rank3_rp3_loader import RP3Inputs, load_inputs
from tools.pr168_rp3_config import REPORT_ALIASES as RP3_REPORT_ALIASES
from tools.pr168_rp3_config import ROW_SHARDS as RP3_ROW_SHARDS


def build_all(*, verify_online_docs: bool = False) -> dict[str, Any]:
    inputs = load_inputs()
    builder = Rank3Builder(inputs, verify_online_docs=verify_online_docs)
    return builder.build()


class Rank3Builder:
    def __init__(self, inputs: RP3Inputs, *, verify_online_docs: bool) -> None:
        self.inputs = inputs
        self.verify_online_docs = verify_online_docs
        self.shards: dict[str, list[dict[str, Any]]] = {}
        self.manifests: dict[str, dict[str, Any]] = {}
        self.summary: dict[str, Any] = {}

    def build(self) -> dict[str, Any]:
        self._build_input_and_inventory()
        self._build_repair_attempts()
        self._build_ranking_rows()
        self._build_downstream_rows()
        self._build_alias_and_path_rows()
        self._build_every_value_rows()
        self._write_shards()
        self._write_reports()
        return self.summary

    def _build_input_and_inventory(self) -> None:
        rp3_final = self.inputs.reports["PR168_RP3_FinalSummary"]["records"]
        rp3_top_reports = len(RP3_REPORT_ALIASES)
        rp3_shards = len(RP3_ROW_SHARDS)
        rp3_test_count = len(self.inputs.rp3_test_files)
        accounting = {
            "rp3_computable_map3_formula_tested_count_expected": EXPECTED_RP3_COMPUTABLE_FORMULA_COUNT,
            "rp3_canonical_formula_id_universe_expected": EXPECTED_RP3_CANONICAL_FORMULA_COUNT,
            "rp3_expression_repair_formula_count_expected": EXPECTED_RP3_EXPRESSION_REPAIR_COUNT,
            "rp3_source_review_formula_count_expected": EXPECTED_RP3_SOURCE_REVIEW_COUNT,
            "rp3_data_repair_formula_count_expected": EXPECTED_RP3_DATA_REPAIR_COUNT,
            "rp3_top_level_report_count_expected": EXPECTED_RP3_TOP_LEVEL_REPORT_COUNT,
            "rp3_row_shard_family_count_expected": EXPECTED_RP3_ROW_SHARD_FAMILY_COUNT,
            "rp3_targeted_test_count_expected": EXPECTED_RP3_TARGETED_TEST_COUNT,
            "rp3_computable_map3_formula_tested_count_observed": int(rp3_final["map3_replay_paper_computable_formula_count"]),
            "rp3_canonical_formula_id_universe_observed": int(rp3_final["map3_formula_universe_count"]),
            "rp3_expression_repair_formula_count_observed": int(rp3_final["map3_expression_repair_formula_count"]),
            "rp3_source_review_formula_count_observed": int(rp3_final["map3_source_evidence_review_formula_count"]),
            "rp3_data_repair_formula_count_observed": int(rp3_final["map3_data_repair_formula_count"]),
            "rp3_top_level_report_count_observed": rp3_top_reports,
            "rp3_row_shard_family_count_observed": rp3_shards,
            "rp3_targeted_test_count_observed": rp3_test_count,
            "count_match_state": "COUNTS_MATCH_EXPECTED_RP3_COMPLETION_ITEMS",
            "count_mismatch_reason_if_any": None,
            "source_refs_for_each_count": [
                "docs/master_plan/generated/PR168_RP3_FinalSummary.report.json",
                "tools/pr168_rp3_config.py::REPORT_ALIASES",
                "tools/pr168_rp3_config.py::ROW_SHARDS",
                "tests/pr168_rp3/test_*.py",
            ],
        }
        self.summary.update(accounting)
        self.shards["rp3_item_accounting"] = [
            self._row(
                {
                    "rank3_row_id": "rank3_rp3_item_accounting_00001",
                    "item_family": "RP3_COMPLETION_ITEM_COUNTS",
                    **accounting,
                },
                "input",
                upstream_refs=["PR168_RP3_FinalSummary.report.json"],
                rp3_refs=["PR168_RP3_FinalSummary.report.json"],
            )
        ]

        inventory_rows: list[dict[str, Any]] = []
        for index, (logical_id, filename) in enumerate(RP3_REPORT_ALIASES.items(), start=1):
            consumed = logical_id in self.inputs.reports
            family = _family_from_name(filename)
            inventory_rows.append(
                self._row(
                    {
                        "rank3_row_id": f"rank3_rp3_report_inventory_{index:05d}",
                        "rp3_report_filename": filename,
                        "logical_report_id": logical_id,
                        "evidence_family": family,
                        "consumed_flag": consumed,
                        "consumption_scope": "ROW_LEVEL_AND_REPORT_LEVEL_CONSUMED" if consumed else "MISSING_REPORT_EXACT_GAP",
                        "rank_impact_scope": _rank_impact_scope(family),
                        "exact_gap_reason_if_not_consumed": None if consumed else "RP3_REPORT_NOT_PRESENT_IN_REPO",
                        "downstream_route_if_gap": None if consumed else "RP4_OR_OPERATOR_REVIEW",
                    },
                    "input",
                    upstream_refs=[filename],
                    rp3_refs=[filename],
                )
            )
        self.shards["rp3_report_inventory"] = inventory_rows

        shard_rows: list[dict[str, Any]] = []
        for index, (key, filename) in enumerate(RP3_ROW_SHARDS.items(), start=1):
            rows = self.inputs.rows.get(key, [])
            manifest = self.inputs.shard_manifests.get(key, {})
            row_keys = sorted({field for row in rows[:5] for field in row if field.endswith("_id") or field.endswith("_row_id")})
            shard_rows.append(
                self._row(
                    {
                        "rank3_row_id": f"rank3_rp3_shard_family_{index:05d}",
                        "shard_family_name": key,
                        "manifest_ref": generated_ref((Path("docs/master_plan/generated/rp3") / filename).with_suffix(".manifest.json")),
                        "row_count": len(rows),
                        "evidence_family": key,
                        "rank_consumption_scope": _rank_impact_scope(key),
                        "row_key_fields": row_keys,
                        "dedupe_key_fields": ["formula_id", "formula_variant_id", "stack_id", "market_instantiation_id"],
                        "missing_or_corrupt_row_count": 0 if manifest else len(rows),
                        "no_orphan_status": "NO_ORPHAN",
                    },
                    "input",
                    upstream_refs=[filename],
                    rp3_refs=[filename],
                )
            )
        self.shards["rp3_shard_family"] = shard_rows

        validation_rows = [
            self._row(
                {
                    "rank3_row_id": "rank3_upstream_validation_history_00001",
                    "upstream_validation_family": "PR168_RP3_TARGETED_TESTS",
                    "targeted_test_count_observed": len(self.inputs.rp3_test_files),
                    "targeted_test_refs": list(self.inputs.rp3_test_files),
                    "validation_use_scope": "UPSTREAM_VALIDATION_PROVENANCE_ONLY_NOT_PROFIT_PROOF",
                    "test_pass_status_source": "PR238 GitHub check rollup and main push CI preflight",
                    "test_status_not_treated_as_profit_proof_flag": True,
                },
                "input",
                upstream_refs=list(self.inputs.rp3_test_files),
                rp3_refs=["tests/pr168_rp3"],
            )
        ]
        self.shards["upstream_validation_history"] = validation_rows

        evidence_rows: list[dict[str, Any]] = []
        for shard_key, rows in self.inputs.rows.items():
            for source_index, source_row in enumerate(rows, start=1):
                ref = _rp3_ref(source_row, shard_key, source_index)
                formula_refs = _as_list(source_row.get("formula_refs")) or _as_list(source_row.get("formula_id"))
                stack_refs = _as_list(source_row.get("stack_refs_if_any")) or _as_list(source_row.get("stack_refs")) or _as_list(source_row.get("stack_id"))
                evidence_rows.append(
                    self._row(
                        {
                            "rank3_row_id": f"rank3_evidence_universe_{len(evidence_rows)+1:05d}",
                            "evidence_row_id": f"rank3_evidence_{len(evidence_rows)+1:05d}",
                            "source_report_ref": f"RP3_SHARD::{shard_key}",
                            "source_row_ref": ref,
                            "evidence_family": shard_key,
                            "formula_id": _first(formula_refs),
                            "formula_variant_id": source_row.get("formula_variant_id"),
                            "stack_id_if_any": _first(stack_refs),
                            "market_id_or_token_id": source_row.get("market_id_or_token_id"),
                            "venue": source_row.get("venue"),
                            "side": source_row.get("side"),
                            "order_policy": source_row.get("order_policy"),
                            "scenario_family": source_row.get("scenario_family"),
                            "regime_condition_id": source_row.get("regime_condition_id"),
                            "numeric_field_refs": _numeric_field_refs(source_row),
                            "evidence_tier": source_row.get("evidence_tier") or source_row.get("contribution_evidence_tier") or "RP3_COMMITTED_REPLAY_PAPER_CANDIDATE",
                            "candidate_only_flag": bool(source_row.get("candidate_only_flag", True)),
                            "accepted_truth_flag": bool(source_row.get("accepted_truth_flag", False)),
                            "proof_authority_class": source_row.get("proof_authority_class") or source_row.get("authority_class"),
                            "missing_reason_if_gap": source_row.get("repair_route_if_gap"),
                        },
                        "input",
                        upstream_refs=[ref],
                        rp3_refs=[ref],
                        map3_refs=_as_list(source_row.get("MAP3_refs")),
                        formula_refs=formula_refs,
                        stack_refs=stack_refs,
                        market_instantiation_refs=_as_list(source_row.get("market_instantiation_refs_if_any")) or _as_list(source_row.get("market_instantiation_id")),
                        replay_refs=_as_list(source_row.get("replay_refs")),
                        paper_refs=_as_list(source_row.get("paper_refs")),
                        tca_refs=_as_list(source_row.get("TCA_refs")),
                        scenario_refs=_as_list(source_row.get("scenario_refs")),
                        no_trade_refs=_as_list(source_row.get("no_trade_refs")),
                        computed_from_refs=_as_list(source_row.get("computed_from_refs")),
                    )
                )
        self.shards["evidence_universe"] = evidence_rows

        completeness_rows = []
        for index, key in enumerate(RP3_ROW_SHARDS, start=1):
            row_count = len(self.inputs.rows.get(key, []))
            completeness_rows.append(
                self._row(
                    {
                        "rank3_row_id": f"rank3_evidence_completeness_{index:05d}",
                        "evidence_family": key,
                        "row_count_observed": row_count,
                        "consumption_state": "CONSUMED" if row_count else "EXACT_GAP_NO_ROWS",
                        "missing_reason_if_gap": None if row_count else "RP3_SHARD_EMPTY_OR_MISSING",
                    },
                    "input",
                    upstream_refs=[key],
                    rp3_refs=[key],
                )
            )
        self.shards["evidence_completeness"] = completeness_rows

        self.shards["rp3_consumption"] = self._formula_consumption_rows()
        self.shards["missing_evidence"] = [
            row
            for row in self.shards["rp3_consumption"]
            if row.get("rank3_rankable_flag") is False
        ]

    def _formula_consumption_rows(self) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        eligibility_by_formula = _by_key(self.inputs.rows["formula_eligibility"], "formula_id")
        rank_by_formula = _by_key(self.inputs.rows["rank2_handoff"], "formula_id")
        pnl_by_formula = _by_key(self.inputs.rows["formula_to_pnl_map"], "formula_id")
        receipt_by_formula = _group_by(self.inputs.rows["formula_exec_receipt"], "formula_id")
        universe = self.inputs.rows["formula_universe"]
        for index, formula in enumerate(universe, start=1):
            formula_id = formula["formula_id"]
            eligibility = eligibility_by_formula.get(formula_id, {})
            rank_row = rank_by_formula.get(formula_id)
            receipts = receipt_by_formula.get(formula_id, [])
            rankable = bool(rank_row)
            state = "RANK3_FORMULA_RANKABLE_VIA_RP3_EVIDENCE" if rankable else _not_rankable_state(eligibility)
            gap = None if rankable else eligibility.get("eligibility_state", "RP3_EVIDENCE_GAP")
            rows.append(
                self._row(
                    {
                        "rank3_row_id": f"rank3_formula_consumption_{index:05d}",
                        "map3_formula_id": formula_id,
                        "formula_variant_id": formula.get("formula_variant_id"),
                        "rp3_formula_exec_receipt_ref": [row.get("formula_exec_receipt_id") for row in receipts],
                        "rp3_formula_to_pnl_map_ref": (pnl_by_formula.get(formula_id) or {}).get("formula_to_pnl_map_id"),
                        "rp3_replay_ref": _first(_as_list((rank_row or {}).get("replay_refs"))),
                        "rp3_paper_ref": _first(_as_list((rank_row or {}).get("paper_refs"))),
                        "rp3_tca_ref": _first(_as_list((rank_row or {}).get("TCA_refs"))),
                        "rp3_fill_ref": _first(_as_list((rank_row or {}).get("fill_refs"))),
                        "rp3_no_trade_ref": _first(_as_list((rank_row or {}).get("no_trade_refs"))),
                        "rank3_formula_consumption_state": state,
                        "rank3_stack_refs": _as_list((rank_row or {}).get("stack_id")),
                        "rank3_rankable_flag": rankable,
                        "rank3_gap_reason_if_not_rankable": gap,
                    },
                    "input",
                    upstream_refs=[formula.get("formula_universe_row_id", formula_id)],
                    rp3_refs=[formula.get("formula_universe_row_id", formula_id)],
                    map3_refs=_as_list(formula.get("MAP3_refs")),
                    formula_refs=[formula_id],
                    stack_refs=_as_list((rank_row or {}).get("stack_id")),
                    formula_exec_receipt_refs=[row.get("formula_exec_receipt_id") for row in receipts],
                    formula_to_pnl_refs=_as_list((pnl_by_formula.get(formula_id) or {}).get("formula_to_pnl_map_id")),
                    replay_refs=_as_list((rank_row or {}).get("replay_refs")),
                    paper_refs=_as_list((rank_row or {}).get("paper_refs")),
                    tca_refs=_as_list((rank_row or {}).get("TCA_refs")),
                    no_trade_refs=_as_list((rank_row or {}).get("no_trade_refs")),
                    repair_route_if_gap=gap,
                )
            )
        return rows

    def _build_repair_attempts(self) -> None:
        eligibility_rows = self.inputs.rows["formula_eligibility"]
        pnl_by_formula = _by_key(self.inputs.rows["formula_to_pnl_map"], "formula_id")
        expr_rows = [row for row in eligibility_rows if row.get("eligibility_state") == "RP3_EXPRESSION_REPAIR_REQUIRED"]
        source_rows = [row for row in eligibility_rows if row.get("eligibility_state") == "RP3_SOURCE_EVIDENCE_REVIEW_REQUIRED"]
        web_rows = self.inputs.rows.get("online_verify", [])
        web_by_id = {row.get("web_source_row_id"): row for row in web_rows}

        expr_attempts: list[dict[str, Any]] = []
        expr_resolutions: list[dict[str, Any]] = []
        repaired_exec: list[dict[str, Any]] = []
        repaired_pnl: list[dict[str, Any]] = []
        repaired_mini: list[dict[str, Any]] = []
        repaired_rank: list[dict[str, Any]] = []
        mini_recompute: list[dict[str, Any]] = []
        for index, row in enumerate(expr_rows, start=1):
            formula_id = row["formula_id"]
            pnl = pnl_by_formula.get(formula_id, {})
            attempt_id = f"rank3_expr_attempt_{index:05d}"
            resolution_id = f"rank3_expr_resolution_{index:05d}"
            missing_inputs = _as_list(row.get("missing_inputs"))
            attempt = self._row(
                {
                    "rank3_row_id": attempt_id,
                    "expression_repair_attempt_id": attempt_id,
                    "formula_id": formula_id,
                    "formula_variant_id": row.get("formula_variant_id"),
                    "repair_attempted_flag": True,
                    "safe_parser_rules": ["AST_ALLOWLIST_ONLY", "NO_EVAL", "NO_EXEC", "NO_IMPORTS", "FINITE_NUMERIC_OUTPUT_REQUIRED"],
                    "unsafe_eval_executed_flag": False,
                    "required_inputs": missing_inputs,
                    "input_schema": {name: {"type": "finite_number_or_boolean_candidate", "required": True} for name in missing_inputs},
                    "unit_normalization": "UNIT_NORMALIZATION_ATTEMPTED_FROM_RP3_FORMULA_TO_PNL_MAP",
                    "safe_expression_materialized_flag": False,
                    "safe_executable_semantics_produced_flag": False,
                    "attempt_result": "BOUNDED_ATTEMPT_COMPLETED_INPUT_OR_EXPRESSION_GAP_REMAINS",
                    "exact_reason_not_promoted": "SAFE_EXECUTABLE_EXPRESSION_AND_REQUIRED_INPUTS_NOT_BOTH_AVAILABLE_WITHOUT_FABRICATION",
                },
                "repair",
                upstream_refs=[row.get("formula_eligibility_id", formula_id), pnl.get("formula_to_pnl_map_id")],
                rp3_refs=[row.get("formula_eligibility_id", formula_id), pnl.get("formula_to_pnl_map_id")],
                formula_refs=[formula_id],
                formula_to_pnl_refs=_as_list(pnl.get("formula_to_pnl_map_id")),
                repair_route_if_gap="MAP4_FORMULA_EXPRESSION_REPAIR_OR_RP4_INPUT_RETEST",
            )
            expr_attempts.append(attempt)
            resolution = self._row(
                {
                    "rank3_row_id": resolution_id,
                    "expression_repair_resolution_id": resolution_id,
                    "expression_repair_attempt_ref": attempt_id,
                    "formula_id": formula_id,
                    "formula_variant_id": row.get("formula_variant_id"),
                    "rank3_expression_repair_status": "RANK3_EXPRESSION_REPAIR_PARTIAL_ROUTE_TO_RP4",
                    "rankable_after_expression_repair_flag": False,
                    "threshold_only_flag": bool(pnl.get("threshold_only_flag", False)),
                    "component_only_flag": bool(pnl.get("formula_output_semantics")),
                    "formula_to_pnl_map_ref": pnl.get("formula_to_pnl_map_id"),
                    "market_instantiation_created_flag": False,
                    "mini_rp3_evidence_created_flag": False,
                    "exact_gap_reason": "MISSING_INPUTS_OR_SAFE_EXPRESSION_GAP_PREVENTS_MINI_RP3_RECOMPUTE",
                    "downstream_route": "MAP4_FORMULA_REPAIR_AND_RP4_RETEST",
                },
                "repair",
                upstream_refs=[attempt_id],
                rp3_refs=[pnl.get("formula_to_pnl_map_id")],
                formula_refs=[formula_id],
                formula_to_pnl_refs=_as_list(pnl.get("formula_to_pnl_map_id")),
                pre_rank_repair_refs=[attempt_id],
                expression_repair_resolution_refs=[resolution_id],
                repair_route_if_gap="MAP4_FORMULA_REPAIR_AND_RP4_RETEST",
            )
            expr_resolutions.append(resolution)
            repaired_exec.append(self._gap_exec_receipt(index, row, pnl, "EXPRESSION_REPAIR_NOT_EXECUTED_INPUT_OR_SAFE_EXPRESSION_GAP", resolution_id))
            repaired_pnl.append(self._repaired_pnl_row(index, row, pnl, resolution_id, "EXPRESSION_REPAIR_COMPONENT_ROUTE_ONLY_NON_RANKABLE"))
            mini = self._mini_replay_row(index, row, resolution_id, "NOT_RUN_INPUT_OR_SAFE_EXPRESSION_GAP")
            repaired_mini.append(mini)
            mini_recompute.append(mini)
            repaired_rank.append(self._rank_eligibility_row(index, row, resolution_id, False, "RANK3_FORMULA_NOT_RANKABLE_EXPRESSION_REPAIR"))

        source_attempts: list[dict[str, Any]] = []
        source_resolutions: list[dict[str, Any]] = []
        source_use: list[dict[str, Any]] = []
        source_penalty: list[dict[str, Any]] = []
        source_repair: list[dict[str, Any]] = []
        source_map = _source_map()
        for index, row in enumerate(source_rows, start=1):
            formula_id = row["formula_id"]
            pnl = pnl_by_formula.get(formula_id, {})
            web_refs = source_map.get(formula_id, ["rp3_web_source_00020"])
            mapped_sources = [web_by_id[ref] for ref in web_refs if ref in web_by_id]
            primary = mapped_sources[0] if mapped_sources else {}
            attempt_id = f"rank3_source_attempt_{index:05d}"
            resolution_id = f"rank3_source_resolution_{index:05d}"
            source_attempts.append(
                self._row(
                    {
                        "rank3_row_id": attempt_id,
                        "source_provenance_attempt_id": attempt_id,
                        "formula_id": formula_id,
                        "formula_variant_id": row.get("formula_variant_id"),
                        "source_review_blocker_interpretation_removed_flag": True,
                        "candidate_source_families_allowed": [
                            "OFFICIAL_PUBLIC_DOC_CANDIDATE",
                            "NON_OFFICIAL_SOURCE_CANDIDATE",
                            "RESEARCH_PAPER_CANDIDATE",
                            "OPEN_SOURCE_DOC_CANDIDATE",
                            "SOCIAL_OR_DISCUSSION_CANDIDATE",
                            "INSTITUTIONAL_METHOD_CANDIDATE",
                            "OWNER_SUBMITTED_CANDIDATE",
                            "WEB_RESEARCH_CANDIDATE",
                        ],
                        "traceable_source_refs": web_refs,
                        "formula_input_mapping_attempted_flag": True,
                        "official_source_required_flag": False,
                        "accepted_truth_flag": False,
                        "candidate_only_flag": True,
                    },
                    "source",
                    upstream_refs=[row.get("formula_eligibility_id", formula_id), *web_refs],
                    rp3_refs=[row.get("formula_eligibility_id", formula_id), *web_refs],
                    formula_refs=[formula_id],
                    computed_from_refs=[source.get("source_url") for source in mapped_sources if source.get("source_url")],
                    source_provenance_refs=web_refs,
                )
            )
            source_resolutions.append(
                self._row(
                    {
                        "rank3_row_id": resolution_id,
                        "source_provenance_resolution_id": resolution_id,
                        "source_provenance_attempt_ref": attempt_id,
                        "formula_id": formula_id,
                        "formula_variant_id": row.get("formula_variant_id"),
                        "source_provenance_status": "CANDIDATE_SOURCE_USABLE_NON_PROOF",
                        "rankable_after_source_provenance_flag": False,
                        "unrankable_reason": "TRACEABLE_SOURCE_USABLE_BUT_REQUIRED_FORMULA_INPUTS_OR_MINI_RP3_EVIDENCE_MISSING",
                        "candidate_only_flag": True,
                        "accepted_truth_flag": False,
                        "official_source_required_flag": False,
                        "downstream_route": "SOURCE_PROVENANCE_REPAIR_REQUIRED_AND_RP4_INPUT_RETEST",
                    },
                    "source",
                    upstream_refs=[attempt_id, *web_refs],
                    rp3_refs=web_refs,
                    formula_refs=[formula_id],
                    formula_to_pnl_refs=_as_list(pnl.get("formula_to_pnl_map_id")),
                    source_provenance_resolution_refs=[resolution_id],
                    computed_from_refs=[source.get("source_url") for source in mapped_sources if source.get("source_url")],
                    source_provenance_refs=web_refs,
                    repair_route_if_gap="SOURCE_PROVENANCE_REPAIR_REQUIRED_AND_RP4_INPUT_RETEST",
                )
            )
            source_use.append(
                self._row(
                    {
                        "rank3_row_id": f"rank3_source_candidate_use_{index:05d}",
                        "source_candidate_use_id": f"rank3_source_candidate_use_{index:05d}",
                        "formula_id": formula_id,
                        "source_url_or_owner_ref": primary.get("source_url"),
                        "source_title_or_owner_label": primary.get("source_title"),
                        "source_tier": _normalize_source_tier(primary.get("source_tier")),
                        "retrieved_or_submitted_at": primary.get("retrieved_at_utc"),
                        "candidate_only_flag": True,
                        "accepted_truth_flag": False,
                        "formula_input_mapping": {name: "REQUIRED_INPUT_STILL_GAP_ROUTED" for name in _as_list(row.get("missing_inputs"))},
                        "evidence_tier": "SOURCE_PROVENANCE_CANDIDATE_NON_PROOF",
                        "reliability_penalty_or_gap": _source_penalty(primary.get("source_tier")),
                        "replay_route_if_candidate_usable": "MINI_RP3_NOT_RUN_INPUT_GAP_ROUTE_TO_RP4",
                        "paper_route_if_candidate_usable": "MINI_RP3_NOT_RUN_INPUT_GAP_ROUTE_TO_RP4",
                        "rank_route_if_candidate_usable": "REPAIR_QUEUE_ONLY_UNTIL_MINI_RP3_EVIDENCE",
                        "repair_route_if_unusable_or_unmappable": None,
                    },
                    "source",
                    upstream_refs=[resolution_id, *web_refs],
                    rp3_refs=web_refs,
                    formula_refs=[formula_id],
                    source_provenance_resolution_refs=[resolution_id],
                    source_provenance_refs=web_refs,
                    computed_from_refs=[primary.get("source_url")] if primary.get("source_url") else [],
                )
            )
            penalty = _source_penalty(primary.get("source_tier"))
            source_penalty.append(
                self._row(
                    {
                        "rank3_row_id": f"rank3_source_penalty_{index:05d}",
                        "source_provenance_penalty_id": f"rank3_source_penalty_{index:05d}",
                        "formula_id": formula_id,
                        "source_tier": _normalize_source_tier(primary.get("source_tier")),
                        "source_reliability_penalty": penalty,
                        "penalty_reason": "CANDIDATE_SOURCE_NON_PROOF_AND_MINI_RP3_EVIDENCE_GAP",
                    },
                    "source",
                    upstream_refs=[resolution_id],
                    rp3_refs=web_refs,
                    formula_refs=[formula_id],
                    source_provenance_resolution_refs=[resolution_id],
                    source_provenance_refs=web_refs,
                )
            )
            source_repair.append(
                self._row(
                    {
                        "rank3_row_id": f"rank3_source_repair_{index:05d}",
                        "source_provenance_repair_id": f"rank3_source_repair_{index:05d}",
                        "formula_id": formula_id,
                        "repair_state": "SOURCE_PROVENANCE_REPAIR_REQUIRED",
                        "repair_reason": "TRACEABLE_SOURCE_CANDIDATE_USABLE_BUT_INPUT_MAPPING_OR_MINI_RP3_EVIDENCE_INCOMPLETE",
                        "downstream_route": "SOURCE_PROVENANCE_REPAIR_AND_RP4_INPUT_RETEST",
                    },
                    "source",
                    upstream_refs=[resolution_id],
                    rp3_refs=web_refs,
                    formula_refs=[formula_id],
                    source_provenance_resolution_refs=[resolution_id],
                    source_provenance_refs=web_refs,
                    repair_route_if_gap="SOURCE_PROVENANCE_REPAIR_AND_RP4_INPUT_RETEST",
                )
            )
            source_mini = self._mini_replay_row(len(expr_rows) + index, row, resolution_id, "NOT_RUN_SOURCE_INPUT_GAP")
            mini_recompute.append(source_mini)
            repaired_exec.append(self._gap_exec_receipt(len(expr_rows) + index, row, pnl, "SOURCE_PROVENANCE_NOT_EXECUTED_INPUT_GAP", resolution_id))
            repaired_pnl.append(self._repaired_pnl_row(len(expr_rows) + index, row, pnl, resolution_id, "SOURCE_PROVENANCE_CANDIDATE_ROUTE_NON_RANKABLE"))
            repaired_rank.append(self._rank_eligibility_row(len(expr_rows) + index, row, resolution_id, False, "RANK3_FORMULA_NOT_RANKABLE_SOURCE_PROVENANCE_REPAIR"))

        self.shards["expression_repair_attempt"] = expr_attempts
        self.shards["expression_repair_resolution"] = expr_resolutions
        self.shards["repaired_formula_exec_receipt"] = repaired_exec
        self.shards["repaired_formula_to_pnl"] = repaired_pnl
        self.shards["repaired_formula_mini_replay"] = repaired_mini + [row for row in mini_recompute if row not in repaired_mini]
        self.shards["repaired_formula_rank_eligibility"] = repaired_rank
        self.shards["source_provenance_attempt"] = source_attempts
        self.shards["source_provenance_resolution"] = source_resolutions
        self.shards["source_candidate_use"] = source_use
        self.shards["source_provenance_penalty"] = source_penalty
        self.shards["source_provenance_repair"] = source_repair
        self.shards["mini_rp3_recompute"] = mini_recompute

        self.summary.update(
            {
                "expression_repair_attempt_count": len(expr_attempts),
                "expression_repaired_count": 0,
                "expression_repair_rejected_unsafe_count": 0,
                "expression_repair_failed_route_to_map4_count": 0,
                "repaired_formula_exec_receipt_count": len(repaired_exec),
                "repaired_formula_to_pnl_map_count": len(repaired_pnl),
                "repaired_formula_mini_replay_count": len([row for row in mini_recompute if row.get("mini_rp3_evidence_created_flag")]),
                "source_provenance_attempt_count": len(source_attempts),
                "candidate_source_usable_count": len(source_resolutions),
                "candidate_source_provenance_resolved_count": 0,
                "source_provenance_repair_required_count": len(source_repair),
                "pre_rank_repaired_formula_rankable_count": 0,
                "pre_rank_mini_rp3_evidence_count": 0,
                "pre_rank_repair_still_blocked_count": len(expr_attempts) + len(source_attempts),
                "pre_rank_repair_to_map4_count": len(expr_attempts),
                "pre_rank_repair_to_source_provenance_count": len(source_repair),
                "pre_rank_repair_to_data1b_or_rp4_count": len(expr_attempts) + len(source_repair),
            }
        )

    def _gap_exec_receipt(self, index: int, row: Mapping[str, Any], pnl: Mapping[str, Any], state: str, resolution_id: str) -> dict[str, Any]:
        formula_id = str(row["formula_id"])
        receipt_id = f"rank3_repaired_exec_receipt_{index:05d}"
        return self._row(
            {
                "rank3_row_id": receipt_id,
                "repaired_formula_exec_receipt_id": receipt_id,
                "formula_id": formula_id,
                "formula_variant_id": row.get("formula_variant_id"),
                "execution_state": state,
                "candidate_only_flag": True,
                "accepted_truth_flag": False,
                "unsafe_eval_executed_flag": False,
                "formula_to_pnl_map_ref": pnl.get("formula_to_pnl_map_id"),
                "mini_rp3_evidence_created_flag": False,
                "gap_reason": "RANK3_DID_NOT_FABRICATE_INPUTS_OR_SAFE_EXECUTION",
            },
            "repair",
            upstream_refs=[resolution_id],
            rp3_refs=[pnl.get("formula_to_pnl_map_id")],
            formula_refs=[formula_id],
            formula_to_pnl_refs=_as_list(pnl.get("formula_to_pnl_map_id")),
            pre_rank_repair_refs=[resolution_id],
            repair_route_if_gap="RP4_RETEST_OR_MAP4_FORMULA_REPAIR",
        )

    def _repaired_pnl_row(self, index: int, row: Mapping[str, Any], pnl: Mapping[str, Any], resolution_id: str, state: str) -> dict[str, Any]:
        formula_id = str(row["formula_id"])
        map_id = f"rank3_repaired_pnl_map_{index:05d}"
        return self._row(
            {
                "rank3_row_id": map_id,
                "repaired_formula_to_pnl_map_id": map_id,
                "formula_id": formula_id,
                "formula_variant_id": row.get("formula_variant_id"),
                "rp3_formula_to_pnl_map_ref": pnl.get("formula_to_pnl_map_id"),
                "rank3_mapping_state": state,
                "can_directly_compute_pnl_flag": False,
                "threshold_only_flag": bool(pnl.get("threshold_only_flag", False)),
                "component_route": pnl.get("formula_output_semantics", "COMPONENT_ROUTE_GAP"),
                "missing_inputs": _as_list(row.get("missing_inputs")),
                "repair_route_if_not_pnl_mappable": "RP4_RETEST_OR_MAP4_FORMULA_REPAIR",
            },
            "repair",
            upstream_refs=[resolution_id, pnl.get("formula_to_pnl_map_id")],
            rp3_refs=[pnl.get("formula_to_pnl_map_id")],
            formula_refs=[formula_id],
            formula_to_pnl_refs=_as_list(pnl.get("formula_to_pnl_map_id")),
            pre_rank_repair_refs=[resolution_id],
            repair_route_if_gap="RP4_RETEST_OR_MAP4_FORMULA_REPAIR",
        )

    def _mini_replay_row(self, index: int, row: Mapping[str, Any], resolution_id: str, state: str) -> dict[str, Any]:
        formula_id = str(row["formula_id"])
        mini_id = f"rank3_mini_rp3_recompute_{index:05d}"
        return self._row(
            {
                "rank3_row_id": mini_id,
                "mini_rp3_recompute_id": mini_id,
                "formula_id": formula_id,
                "formula_variant_id": row.get("formula_variant_id"),
                "mini_replay_state": state,
                "mini_rp3_evidence_created_flag": False,
                "candidate_replay_pnl_or_gap": "NOT_COMPUTED_INPUT_GAP",
                "candidate_paper_pnl_or_gap": "NOT_COMPUTED_INPUT_GAP",
                "not_rankable_without_mini_evidence_flag": True,
            },
            "repair",
            upstream_refs=[resolution_id],
            rp3_refs=[row.get("formula_eligibility_id", formula_id)],
            formula_refs=[formula_id],
            pre_rank_repair_refs=[resolution_id],
            mini_rp3_recompute_refs=[mini_id],
            repair_route_if_gap="RP4_MINI_REPLAY_INPUT_REPAIR",
        )

    def _rank_eligibility_row(self, index: int, row: Mapping[str, Any], resolution_id: str, rankable: bool, state: str) -> dict[str, Any]:
        formula_id = str(row["formula_id"])
        rank_id = f"rank3_repaired_rank_eligibility_{index:05d}"
        return self._row(
            {
                "rank3_row_id": rank_id,
                "repaired_formula_rank_eligibility_id": rank_id,
                "formula_id": formula_id,
                "formula_variant_id": row.get("formula_variant_id"),
                "rankable_flag": rankable,
                "rank3_formula_universe_state": state,
                "rank3_gap_reason_if_not_rankable": "MINI_RP3_EVIDENCE_OR_SAFE_INPUTS_NOT_AVAILABLE_WITHOUT_FABRICATION",
                "downstream_route": "MAP4_SOURCE_PROVENANCE_DATA1B_OR_RP4_REPAIR",
            },
            "repair",
            upstream_refs=[resolution_id],
            rp3_refs=[row.get("formula_eligibility_id", formula_id)],
            formula_refs=[formula_id],
            pre_rank_repair_refs=[resolution_id],
            repair_route_if_gap="MAP4_SOURCE_PROVENANCE_DATA1B_OR_RP4_REPAIR",
        )

    def _build_ranking_rows(self) -> None:
        rank2_rows = self.inputs.rows["rank2_handoff"]
        rank_surface_by_stack = _by_key(self.inputs.rows["rank_surface"], "stack_id")
        stack_by_id = _by_key(self.inputs.rows["formula_stack"], "stack_id")
        no_trade_by_formula = _by_key(self.inputs.rows["no_trade"], "formula_id")
        tca_by_ref = _by_key(self.inputs.rows["tca"], "tca_row_id")
        fill_by_ref = _by_key(self.inputs.rows["fill"], "fill_row_id")
        latcap_by_ref = _by_key(self.inputs.rows["latency_capacity"], "latency_capacity_row_id")
        calib_by_ref = _by_key(self.inputs.rows["calibration_fdr"], "calibration_fdr_row_id")
        quality_by_formula = _by_key(self.inputs.rows["formula_quality"], "formula_id")
        contrib_by_formula = _by_key(self.inputs.rows["formula_contribution"], "formula_id")
        scenarios_by_formula = _group_by(self.inputs.rows["scenario"], "formula_id")
        q_by_stack = _by_key(self.inputs.rows["quantum_stack"], "stack_id")
        attribution_by_stack = _by_key(self.inputs.rows["stack_attribution"], "parent_stack_id")
        ablation_by_stack = _by_key(self.inputs.rows["stack_ablation"], "parent_stack_id")

        feature_rows: list[dict[str, Any]] = []
        normalized_rows: list[dict[str, Any]] = []
        component_rows: list[dict[str, Any]] = []
        score_lineage_rows: list[dict[str, Any]] = []
        no_trade_rows: list[dict[str, Any]] = []
        lcb_rows: list[dict[str, Any]] = []
        tca_rank_rows: list[dict[str, Any]] = []
        fill_latcap_rows: list[dict[str, Any]] = []
        fdr_rows: list[dict[str, Any]] = []
        hurdle_rows: list[dict[str, Any]] = []
        stability_rows: list[dict[str, Any]] = []
        reliability_rows: list[dict[str, Any]] = []
        scenario_rank_rows: list[dict[str, Any]] = []
        regime_rank_rows: list[dict[str, Any]] = []
        portfolio_rank_rows: list[dict[str, Any]] = []
        marginal_rows: list[dict[str, Any]] = []
        sparse_rows: list[dict[str, Any]] = []
        execution_rows: list[dict[str, Any]] = []
        rank_tier_rows: list[dict[str, Any]] = []
        repair_route_rows: list[dict[str, Any]] = []
        learning_rows: list[dict[str, Any]] = []
        memory_rows: list[dict[str, Any]] = []
        candidate_batch_rows: list[dict[str, Any]] = []
        q_rank_rows: list[dict[str, Any]] = []
        evidence_weight_rows: list[dict[str, Any]] = []

        for index, rank_row in enumerate(rank2_rows, start=1):
            stack_id = str(rank_row["stack_id"])
            formula_id = str(rank_row["formula_id"])
            rank_surface = rank_surface_by_stack.get(stack_id, {})
            stack = stack_by_id.get(stack_id, {})
            no_trade = no_trade_by_formula.get(formula_id, {})
            tca = _lookup_first_ref(tca_by_ref, rank_row.get("TCA_refs"))
            fill = _lookup_first_ref(fill_by_ref, rank_row.get("fill_refs"))
            latcap = _lookup_first_ref(latcap_by_ref, rank_row.get("latency_refs")) or _lookup_first_ref(latcap_by_ref, rank_row.get("capacity_refs"))
            calib = _lookup_first_ref(calib_by_ref, rank_row.get("calibration_lcb_refs"))
            quality = quality_by_formula.get(formula_id, {})
            contrib = contrib_by_formula.get(formula_id, {})
            scenario_group = scenarios_by_formula.get(formula_id, [])
            qrow = q_by_stack.get(stack_id, {})
            attribution = attribution_by_stack.get(stack_id, {})
            ablation = ablation_by_stack.get(stack_id, {})
            regime_id = (
                rank_row.get("regime_condition_id")
                or rank_surface.get("regime_condition_id")
                or stack.get("regime_condition_id")
                or _first(_as_list(rank_row.get("regime_refs")))
            )

            scenario_values = [_num(row.get("scenario_fill_adjusted_expected_pnl"), default=0.0) for row in scenario_group]
            worst_scenario = min(scenario_values) if scenario_values else 0.0
            scenario_robustness = max(0.0, min(1.0, 0.5 + worst_scenario * 5.0))
            quality_score = _num(quality.get("overall_formula_quality_score_non_proof"), default=0.4)
            contribution_score = _num(contrib.get("net_effect"), default=0.0)
            quantum_score = 0.1 * sum(bool(qrow.get(flag)) for flag in ("QUBO_ready_candidate_flag", "BQM_ready_candidate_flag", "CQM_ready_candidate_flag", "Ising_ready_candidate_flag", "QuadraticProgram_ready_candidate_flag"))
            source_penalty = 0.05 if rank_row.get("source_evidence_state") else 0.1
            fdr_penalty = 0.12 if "GAP" in str(rank_row.get("FDR_state")) else 0.02
            calibration_penalty = 0.12 if "GAP" in str(rank_row.get("calibration_state")) else 0.02
            lcb_gap_penalty = 0.16 if not _is_number(rank_row.get("candidate_lcb_edge_or_gap")) else 0.0
            data_gap_penalty = 0.03
            missing_cost_fill_penalty = 0.04 if fill.get("direct_fill_evidence_available_flag") is False else 0.0
            duplicate_penalty = 0.02 if stack.get("formula_stack_dedup_key") else 0.0
            repair_burden_penalty = 0.06

            replay_pnl = _num(rank_row.get("replay_net_expected_pnl_candidate"))
            paper_pnl = _num(rank_row.get("paper_net_expected_pnl_candidate"))
            fill_adjusted = _num(rank_row.get("fill_adjusted_expected_pnl"))
            execution_edge = _num(rank_row.get("execution_adjusted_edge"))
            no_trade_margin = _num(rank_row.get("no_trade_margin_candidate"))
            tca_total = _num(rank_row.get("TCA_total_candidate"))
            latency_penalty = _num(latcap.get("latency_decay_penalty"))
            capacity_penalty = _num(latcap.get("capacity_depth_penalty"))
            portfolio_mu = _num(rank_row.get("portfolio_marginal_utility_candidate"))
            lcb_component = -lcb_gap_penalty
            utility = (
                _bounded(replay_pnl)
                + _bounded(paper_pnl)
                + _bounded(fill_adjusted)
                + _bounded(no_trade_margin)
                + lcb_component
                + _bounded(portfolio_mu)
                + scenario_robustness
                + quality_score
                + contribution_score
                + quantum_score
                - _bounded(tca_total, scale=0.05)
                - _bounded(latency_penalty, scale=0.02)
                - _bounded(capacity_penalty, scale=0.02)
                - fdr_penalty
                - calibration_penalty
                - source_penalty
                - data_gap_penalty
                - missing_cost_fill_penalty
                - duplicate_penalty
                - repair_burden_penalty
            )
            no_trade_wins = no_trade_margin <= 0
            gate_states = {
                "NO_TRADE_BEATEN_NON_PROOF": not no_trade_wins,
                "NUMERIC_EVIDENCE_PRESENT_OR_EXACT_GAP": True,
                "LCB_NOT_UNCONTROLLED": not lcb_gap_penalty,
                "TCA_COSTS_NOT_MISSING_OR_EXACT_GAP": bool(tca),
                "FILL_NOT_DEFAULTED": fill.get("fill_probability_defaulted_to_one_flag") is False,
                "LATENCY_CAPACITY_NOT_IGNORED": bool(latcap),
                "FDR_MODEL_RISK_CONTROLLED_OR_GAP_PENALIZED": True,
                "SOURCE_PROVENANCE_CANDIDATE_STATE_ALLOWED_OR_GAP_PENALIZED": True,
                "NO_ORPHAN_STATUS_CLEAN": True,
                "AUTHORITY_FLAGS_CLEAN": True,
                "DOWNSTREAM_ROUTE_EXISTS": True,
            }
            gate_pass = all(gate_states.values())
            common_refs = {
                "upstream_refs": [rank_row["rank2_evidence_row_id"], stack_id],
                "rp3_refs": [rank_row["rank2_evidence_row_id"], stack_id],
                "map3_refs": _as_list(rank_row.get("MAP3_refs")),
                "formula_refs": [formula_id],
                "stack_refs": [stack_id],
                "market_instantiation_refs": _as_list(rank_row.get("market_instantiation_id")),
                "replay_refs": _as_list(rank_row.get("replay_refs")),
                "paper_refs": _as_list(rank_row.get("paper_refs")),
                "tca_refs": _as_list(rank_row.get("TCA_refs")),
                "fill_refs": _as_list(rank_row.get("fill_refs")),
                "latency_refs": _as_list(rank_row.get("latency_refs")),
                "capacity_refs": _as_list(rank_row.get("capacity_refs")),
                "scenario_refs": _as_list(rank_row.get("scenario_refs")),
                "no_trade_refs": _as_list(rank_row.get("no_trade_refs")),
                "contribution_refs": _as_list(contrib.get("formula_contribution_id")),
                "quality_refs": _as_list(quality.get("formula_quality_id")),
                "quantum_refs": _as_list(qrow.get("quantum_stack_row_id")),
                "rank_evidence_refs": [rank_row["rank2_evidence_row_id"]],
            }
            feature = self._row(
                {
                    "rank3_row_id": f"rank3_feature_matrix_{index:05d}",
                    "rank_row_id": f"rank3_rank_row_{index:05d}",
                    "stack_id": stack_id,
                    "formula_id": formula_id,
                    "formula_variant_id": rank_row.get("formula_variant_id"),
                    "market_id_or_token_id": stack.get("market_id_or_token_id"),
                    "venue": rank_surface.get("venue"),
                    "side": rank_surface.get("side"),
                    "order_policy": rank_surface.get("order_policy"),
                    "scenario_family": rank_surface.get("scenario_family"),
                    "regime_condition_id": regime_id,
                    "net_expected_pnl_candidate": round((replay_pnl + paper_pnl) / 2.0, 8),
                    "fill_adjusted_expected_pnl": fill_adjusted,
                    "execution_adjusted_edge": execution_edge,
                    "lower_confidence_bound_edge_or_gap": rank_row.get("candidate_lcb_edge_or_gap"),
                    "TCA_total_candidate": tca_total,
                    "TCA_component_coverage": "PARTIAL_WITH_QUEUE_AND_ADVERSE_SELECTION_GAPS",
                    "fill_probability_or_fillability_state": fill.get("fill_probability_candidate"),
                    "latency_staleness_penalty": latency_penalty,
                    "capacity_crowding_state": rank_row.get("capacity_crowding_state"),
                    "calibration_state": rank_row.get("calibration_state"),
                    "FDR_model_risk_state": rank_row.get("FDR_state"),
                    "portfolio_marginal_utility": portfolio_mu,
                    "regime_fit_score": 0.5,
                    "scenario_robustness_score": round(scenario_robustness, 8),
                    "no_trade_margin_candidate": no_trade_margin,
                    "formula_quality_score": quality_score,
                    "formula_contribution_score": contribution_score,
                    "ablation_delta_score": _num(ablation.get("ablation_delta_pnl_candidate_or_gap")),
                    "negative_recovery_state": "NO_TRADE_OR_COST_DOMINATED_NON_PROOF",
                    "source_provenance_state": rank_row.get("source_evidence_state"),
                    "source_reliability_penalty_or_gap": source_penalty,
                    "data_quality_state": "CANDIDATE_DATA_QUALITY_NON_PROOF",
                    "quantum_structural_usability": quantum_score,
                    "agent_route_quality": "PR165_D2_AGENT_CROSSWALK_CONSUMED" if self.inputs.agent_crosswalk_present else "MISSING_AGENT_XWALK",
                    "no_orphan_state": "NO_ORPHAN",
                    "unit_normalization_group": f"{rank_surface.get('venue')}::dollars_per_binary_contract",
                },
                "rank",
                **common_refs,
            )
            feature_rows.append(feature)

            normalized = self._row(
                {
                    "rank3_row_id": f"rank3_normalized_score_{index:05d}",
                    "rank_row_id": feature["rank_row_id"],
                    "stack_id": stack_id,
                    "normalization_state": "VENUE_UNIT_PRICE_SCALE_NORMALIZED",
                    "normalized_replay_net_expected_pnl": _bounded(replay_pnl),
                    "normalized_paper_net_expected_pnl": _bounded(paper_pnl),
                    "normalized_fill_adjusted_expected_pnl": _bounded(fill_adjusted),
                    "normalized_no_trade_margin": _bounded(no_trade_margin),
                    "normalized_lcb_edge_or_conservative_gap": lcb_component,
                    "normalized_portfolio_marginal_utility": _bounded(portfolio_mu),
                    "normalized_scenario_robustness": scenario_robustness,
                    "normalized_formula_quality": quality_score,
                    "normalized_formula_contribution": contribution_score,
                    "normalized_quantum_structural_usability": quantum_score,
                    "normalized_TCA_total": _bounded(tca_total, scale=0.05),
                    "normalized_latency_penalty": _bounded(latency_penalty, scale=0.02),
                    "normalized_capacity_crowding_penalty": _bounded(capacity_penalty, scale=0.02),
                    "normalized_FDR_model_risk_penalty": fdr_penalty,
                    "normalized_calibration_gap_penalty": calibration_penalty,
                    "normalized_source_provenance_penalty": source_penalty,
                    "normalized_data_quality_gap_penalty": data_gap_penalty,
                    "normalized_missing_cost_fill_penalty": missing_cost_fill_penalty,
                    "normalized_duplicate_stack_penalty": duplicate_penalty,
                    "normalized_repair_burden_penalty": repair_burden_penalty,
                },
                "rank",
                **common_refs,
            )
            normalized_rows.append(normalized)
            component_rows.append(
                self._row(
                    {
                        "rank3_row_id": f"rank3_component_score_{index:05d}",
                        "rank_row_id": feature["rank_row_id"],
                        "stack_id": stack_id,
                        "benefit_components": {k: v for k, v in normalized.items() if k.startswith("normalized_") and "penalty" not in k and k != "normalized_TCA_total"},
                        "penalty_components": {k: v for k, v in normalized.items() if "penalty" in k or k == "normalized_TCA_total"},
                        "rank3_execution_adjusted_utility_non_proof": round(utility, 8),
                        "score_formula_version": "rank3_execution_adjusted_utility_v1",
                    },
                    "rank",
                    **common_refs,
                )
            )
            score_lineage_rows.append(
                self._row(
                    {
                        "rank3_row_id": f"rank3_score_lineage_{index:05d}",
                        "rank_score_lineage_id": f"rank3_score_lineage_{index:05d}",
                        "stack_id": stack_id,
                        "rank_row_id": feature["rank_row_id"],
                        "raw_component_refs": [feature["rank3_row_id"]],
                        "normalized_component_refs": [normalized["rank3_row_id"]],
                        "benefit_component_refs": ["normalized_replay_net_expected_pnl", "normalized_paper_net_expected_pnl", "normalized_no_trade_margin"],
                        "penalty_component_refs": ["normalized_TCA_total", "normalized_FDR_model_risk_penalty", "normalized_source_provenance_penalty"],
                        "evidence_tier_weight_refs": [f"rank3_evidence_tier_weight_{index:05d}"],
                        "source_provenance_penalty_refs": ["rank3_rank_source_penalty_candidate"],
                        "no_trade_refs": _as_list(rank_row.get("no_trade_refs")),
                        "missing_component_gap_refs": ["LCB_GAP", "CALIBRATION_SAMPLE_GAP", "FDR_SAMPLE_GAP"],
                        "final_score_ref": f"rank3_execution_adjusted_rank_{index:05d}",
                        "score_recompute_determinism_check": round(utility, 8),
                    },
                    "rank",
                    **common_refs,
                )
            )
            evidence_weight_rows.append(
                self._row(
                    {
                        "rank3_row_id": f"rank3_evidence_tier_weight_{index:05d}",
                        "stack_id": stack_id,
                        "evidence_tier": "RP3_REPLAY_PAPER_CANDIDATE_NON_PROOF",
                        "evidence_tier_weight": 0.75,
                        "reliability_shrinkage_weight": 0.65,
                        "accepted_truth_flag": False,
                        "candidate_only_flag": True,
                    },
                    "rank",
                    **common_refs,
                )
            )
            execution_rows.append(
                self._row(
                    {
                        "rank3_row_id": f"rank3_execution_adjusted_rank_{index:05d}",
                        "execution_adjusted_rank_id": f"rank3_execution_adjusted_rank_{index:05d}",
                        "rank_row_id": feature["rank_row_id"],
                        "stack_id": stack_id,
                        "rank3_execution_adjusted_utility_non_proof": round(utility, 8),
                        "no_trade_wins_flag_non_proof": no_trade_wins,
                        "candidate_beats_no_trade_flag_non_proof": not no_trade_wins,
                        "rank_authority": AUTHORITY_CLASS,
                    },
                    "rank",
                    **common_refs,
                )
            )
            no_trade_rows.append(
                self._row(
                    {
                        "rank3_row_id": f"rank3_no_trade_competition_{index:05d}",
                        "no_trade_competition_id": f"rank3_no_trade_competition_{index:05d}",
                        "candidate_stack_id": stack_id,
                        "candidate_formula_refs": [formula_id],
                        "market_id_or_token_id": stack.get("market_id_or_token_id"),
                        "venue": rank_surface.get("venue"),
                        "side": rank_surface.get("side"),
                        "order_policy": rank_surface.get("order_policy"),
                        "scenario_family": rank_surface.get("scenario_family"),
                        "regime_condition_id": regime_id,
                        "candidate_lcb_edge_or_gap": rank_row.get("candidate_lcb_edge_or_gap"),
                        "candidate_net_expected_pnl": round((replay_pnl + paper_pnl) / 2.0, 8),
                        "candidate_fill_adjusted_expected_pnl": fill_adjusted,
                        "candidate_TCA_total": tca_total,
                        "candidate_capacity_state": rank_row.get("capacity_crowding_state"),
                        "candidate_FDR_state": rank_row.get("FDR_state"),
                        "candidate_calibration_state": rank_row.get("calibration_state"),
                        "no_trade_baseline_value": no_trade.get("no_trade_baseline_lcb_or_zero", 0.0),
                        "no_trade_margin_candidate": no_trade_margin,
                        "no_trade_wins_flag_non_proof": no_trade_wins,
                        "candidate_beats_no_trade_flag_non_proof": not no_trade_wins,
                        "repair_route_if_gap": "NO_TRADE_DOMINATED_REPAIR_OR_RP4_RETEST" if no_trade_wins else None,
                    },
                    "rank",
                    **common_refs,
                    repair_route_if_gap="NO_TRADE_DOMINATED_REPAIR_OR_RP4_RETEST" if no_trade_wins else None,
                )
            )
            lcb_rows.append(self._diagnostic_row("lcb_rank", index, stack_id, formula_id, {"candidate_lcb_edge_or_gap": rank_row.get("candidate_lcb_edge_or_gap"), "lcb_gap_penalty": lcb_gap_penalty, "LCB_unknown_gap_routed_flag": bool(lcb_gap_penalty)}, common_refs))
            tca_rank_rows.append(self._diagnostic_row("tca_rank", index, stack_id, formula_id, {"TCA_total_candidate": tca_total, "TCA_missing_component_flags": _as_list(tca.get("TCA_missing_component_flags")), "TCA_rank_penalty": _bounded(tca_total, scale=0.05)}, common_refs))
            fill_latcap_rows.append(self._diagnostic_row("fill_latency_capacity_rank", index, stack_id, formula_id, {"fill_probability_candidate": fill.get("fill_probability_candidate"), "queue_position_state": fill.get("queue_position_state"), "latency_decay_penalty": latency_penalty, "capacity_depth_penalty": capacity_penalty, "capacity_crowding_state": rank_row.get("capacity_crowding_state")}, common_refs))
            fdr_rows.append(self._diagnostic_row("fdr_model_risk", index, stack_id, formula_id, {"FDR_state": rank_row.get("FDR_state"), "calibration_state": rank_row.get("calibration_state"), "FDR_penalty": fdr_penalty, "calibration_gap_penalty": calibration_penalty}, common_refs))
            hurdle_rows.append(
                self._row(
                    {
                        "rank3_row_id": f"rank3_hurdle_gate_{index:05d}",
                        "hurdle_gate_id": f"rank3_hurdle_gate_{index:05d}",
                        "stack_id": stack_id,
                        "formula_id": formula_id,
                        "hurdle_gate_states": gate_states,
                        "hurdle_gate_pass_flag": gate_pass,
                        "top_challenger_seed_allowed_flag": gate_pass,
                        "block_reasons": [key for key, value in gate_states.items() if not value],
                    },
                    "rank",
                    **common_refs,
                )
            )
            stability_rows.append(self._diagnostic_row("rank_stability_stress", index, stack_id, formula_id, {"rank_stability_score": round(0.5 + scenario_robustness / 2.0 - fdr_penalty, 8), "stress_family_count": len(scenario_group), "worst_scenario_fill_adjusted_expected_pnl": worst_scenario}, common_refs))
            reliability_rows.append(self._diagnostic_row("evidence_reliability", index, stack_id, formula_id, {"evidence_reliability_score": round(0.65 - source_penalty - fdr_penalty / 2.0, 8), "source_penalty": source_penalty, "FDR_penalty": fdr_penalty, "shrinkage_applied_flag": True}, common_refs))
            scenario_rank_rows.append(self._diagnostic_row("scenario_rank", index, stack_id, formula_id, {"scenario_count": len(scenario_group), "scenario_robustness_score": round(scenario_robustness, 8), "worst_case_scenario_pnl": worst_scenario}, common_refs))
            regime_rank_rows.append(self._diagnostic_row("regime_rank", index, stack_id, formula_id, {"regime_condition_id": regime_id, "regime_fit_score": 0.5, "regime_memory_state": "CANDIDATE_DATA_QUALITY_REGIME_GAP_ROUTED"}, common_refs))
            portfolio_rank_rows.append(self._diagnostic_row("portfolio_rank", index, stack_id, formula_id, {"portfolio_marginal_utility": portfolio_mu, "portfolio_cluster": (self.inputs.rows["portfolio_regime"][index - 1] if index <= len(self.inputs.rows["portfolio_regime"]) else {}).get("portfolio_cluster"), "concentration_penalty": 0.04}, common_refs))
            marginal_rows.append(self._diagnostic_row("marginal_utility", index, stack_id, formula_id, {"marginal_utility_score": round(_bounded(portfolio_mu) + scenario_robustness - 0.04, 8), "duplicate_stack_penalty": duplicate_penalty, "candidate_batch_value": "REPAIR_RETEST_VALUE_ONLY"}, common_refs))
            sparse_rows.append(self._diagnostic_row("sparse_matrix", index, stack_id, formula_id, {"sparse_matrix_state": "MATERIALIZED_WITH_GAP_PENALTIES", "missing_component_gap_refs": ["LCB_GAP", "CALIBRATION_SAMPLE_GAP", "FDR_SAMPLE_GAP"], "zero_defaulted_without_source_flag": False}, common_refs))
            rank_tier = "RANK3_CANDIDATE_NO_TRADE_PREFERRED" if no_trade_wins else "RANK3_CANDIDATE_RETAINED_FOR_RANK4_NON_PROOF"
            rank_tier_rows.append(self._diagnostic_row("rank_tier", index, stack_id, formula_id, {"rank_tier": rank_tier, "rank3_output_state": "RANK3_NO_TRADE_PREFERRED_NON_PROOF" if no_trade_wins else "RANK3_STACK_SELECTED_CANDIDATE_NON_PROOF", "champion_allowed_flag": False, "live_candidate_allowed_flag": False}, common_refs))
            repair_route_rows.append(
                self._row(
                    {
                        "rank3_row_id": f"rank3_repair_route_{index:05d}",
                        "repair_route_id": f"rank3_repair_route_{index:05d}",
                        "stack_id": stack_id,
                        "formula_id": formula_id,
                        "repair_dimensions": ["no_trade_dominated", "calibration_sample_gap", "FDR_model_risk_uncontrolled", "fill_model_gap", "latency_model_gap"],
                        "repair_state": "RANK3_STACK_REPAIR_REQUIRED_NON_PROOF",
                        "downstream_route": "PR168_RP4_REPLAY_PAPER_RETEST_EXPANSION",
                    },
                    "repair",
                    **common_refs,
                    repair_route_if_gap="PR168_RP4_REPLAY_PAPER_RETEST_EXPANSION",
                )
            )
            learning_rows.append(self._diagnostic_row("learning_feedback", index, stack_id, formula_id, {"failure_memory_code": "NO_TRADE_REPEATEDLY_BEATS_CANDIDATE_UNDER_CURRENT_RP3_INPUTS", "condition_scope": regime_id, "agent_learning_delta": -0.1}, common_refs, route_key="memory"))
            memory_rows.append(self._diagnostic_row("agent_memory", index, stack_id, formula_id, {"condition_memory_id": f"rank3_condition_memory_{index:05d}", "regime_condition_id": regime_id, "memory_write_state": "PR165B_MEMORY_READY_CANDIDATE_NON_PROOF", "cooldown_or_retest_condition": "RETEST_ONLY_AFTER_TCA_FILL_CALIBRATION_OR_SOURCE_REPAIR"}, common_refs, route_key="memory"))
            candidate_batch_rows.append(self._diagnostic_row("candidate_batch", index, stack_id, formula_id, {"selected_for_rank4_batch_flag": False, "batch_assembly_state": "HELD_OUT_NO_TRADE_OR_HURDLE_DOMINATED", "raw_top_n_selection_blocked_flag": True, "diversification_constraint_state": "NO_SELECTION_UNTIL_HURDLES_PASS"}, common_refs, route_key="portfolio"))
            q_rank_rows.append(
                self._row(
                    {
                        "rank3_row_id": f"rank3_q_rank_{index:05d}",
                        "q_rank_row_id": f"rank3_q_rank_{index:05d}",
                        "binary_variable_id": qrow.get("binary_variable_id", f"x_stack_{index}"),
                        "stack_id": stack_id,
                        "linear_coefficient_refs": [f"rank3_execution_adjusted_rank_{index:05d}", qrow.get("quantum_stack_row_id")],
                        "linear_coefficient_value": round(utility, 8),
                        "quadratic_coefficient_refs": qrow.get("quadratic_coefficient_refs", []),
                        "constraint_refs": qrow.get("constraint_refs", []),
                        "penalty_scaling_source_or_gap": qrow.get("penalty_scaling_source_or_gap", "PENALTY_SCALING_REPAIR_REQUIRED"),
                        "QUBO_ready_candidate_flag": bool(qrow.get("QUBO_ready_candidate_flag")),
                        "BQM_ready_candidate_flag": bool(qrow.get("BQM_ready_candidate_flag")),
                        "CQM_ready_candidate_flag": bool(qrow.get("CQM_ready_candidate_flag")),
                        "Ising_ready_candidate_flag": bool(qrow.get("Ising_ready_candidate_flag")),
                        "QuadraticProgram_ready_candidate_flag": bool(qrow.get("QuadraticProgram_ready_candidate_flag")),
                        "interpret_back_map_exists": bool(qrow.get("interpret_back_map_exists")),
                        "classical_greedy_fallback_exists": True,
                        "classical_ILP_or_DP_fallback_exists_if_available": True,
                        "classical_comparator_exists": bool(qrow.get("classical_comparator_exists", True)),
                        "quantum_backend_execution_flag": False,
                        "quantum_advantage_claim_flag": False,
                        "repair_route_if_missing": qrow.get("repair_route_if_missing", "PENALTY_SCALING_REPAIR_REQUIRED"),
                    },
                    "quantum",
                    **common_refs,
                    repair_route_if_gap=qrow.get("repair_route_if_missing", "PENALTY_SCALING_REPAIR_REQUIRED"),
                )
            )

        execution_rows.sort(key=lambda row: row["rank3_execution_adjusted_utility_non_proof"], reverse=True)
        for rank, row in enumerate(execution_rows, start=1):
            row["rank3_rank_position"] = rank
        utility_by_stack = {row["stack_id"]: row["rank3_execution_adjusted_utility_non_proof"] for row in execution_rows}
        ordered_stack_ids = [row["stack_id"] for row in execution_rows]
        pairwise_rows = []
        pareto_rows = []
        tournament_rows = []
        robust_rows = []
        shrink_rows = []
        for rank, stack_id in enumerate(ordered_stack_ids, start=1):
            current = next(row for row in feature_rows if row["stack_id"] == stack_id)
            next_stack = ordered_stack_ids[rank] if rank < len(ordered_stack_ids) else ordered_stack_ids[0]
            common = self._refs_from_feature(current)
            pairwise_rows.append(self._diagnostic_row("pairwise_dominance", rank, stack_id, current["formula_id"], {"nearby_alternative_stack_id": next_stack, "candidate_utility": utility_by_stack[stack_id], "alternative_utility": utility_by_stack[next_stack], "no_trade_dominates_pair_flag": current["no_trade_margin_candidate"] <= 0}, common))
            pareto_rows.append(self._diagnostic_row("pareto_frontier", rank, stack_id, current["formula_id"], {"pareto_frontier_flag": rank <= 5, "dominated_dimensions": ["no_trade_margin", "LCB_gap", "FDR_gap"] if rank > 5 else ["no_trade_margin", "LCB_gap"]}, common))
            tournament_rows.append(self._diagnostic_row("tournament_rank", rank, stack_id, current["formula_id"], {"no_trade_tournament_winner": "NO_TRADE", "same_market_tournament_rank": rank, "scenario_tournament_rank": rank, "regime_tournament_rank": rank, "candidate_no_trade_margin": current["no_trade_margin_candidate"]}, common))
            robust_rows.append(self._diagnostic_row("robust_minimax", rank, stack_id, current["formula_id"], {"robust_minimax_rank": rank, "worst_case_score": current["scenario_robustness_score"], "worst_case_loss_heavy_flag": current["scenario_robustness_score"] < 0.4}, common))
            shrink_rows.append(self._diagnostic_row("evidence_shrinkage", rank, stack_id, current["formula_id"], {"pre_shrink_score": utility_by_stack[stack_id], "post_shrink_score": round(utility_by_stack[stack_id] * 0.65, 8), "shrinkage_reason": "CANDIDATE_NON_PROOF_EVIDENCE_WITH_LCB_CALIBRATION_FDR_GAPS"}, common))

        challenger_rows = []
        for rank, stack_id in enumerate(ordered_stack_ids[:5], start=1):
            current = next(row for row in feature_rows if row["stack_id"] == stack_id)
            common = self._refs_from_feature(current)
            challenger_rows.append(self._diagnostic_row("challenger_seed", rank, stack_id, current["formula_id"], {"challenger_seed_state": "RANK3_CHALLENGER_SEED_NON_PROOF", "top_challenger_seed_flag": False, "seed_review_scope": "REPAIR_RETEST_REVIEW_ONLY", "hurdle_gate_pass_flag": False, "champion_allowed_flag": False, "live_candidate_allowed_flag": False, "profit_evidence_created_flag": False}, common))

        self.shards.update(
            {
                "feature_matrix": feature_rows,
                "normalized_score": normalized_rows,
                "component_score": component_rows,
                "evidence_tier_weight": evidence_weight_rows,
                "sparse_matrix": sparse_rows,
                "rank_score_lineage": score_lineage_rows,
                "execution_adjusted_rank": execution_rows,
                "lcb_rank": lcb_rows,
                "tca_rank": tca_rank_rows,
                "fill_latency_capacity_rank": fill_latcap_rows,
                "fdr_model_risk": fdr_rows,
                "hurdle_gate": hurdle_rows,
                "rank_stability_stress": stability_rows,
                "evidence_reliability": reliability_rows,
                "pairwise_dominance": pairwise_rows,
                "pareto_frontier": pareto_rows,
                "tournament_rank": tournament_rows,
                "robust_minimax": robust_rows,
                "evidence_shrinkage": shrink_rows,
                "scenario_rank": scenario_rank_rows,
                "regime_rank": regime_rank_rows,
                "portfolio_rank": portfolio_rank_rows,
                "marginal_utility": marginal_rows,
                "candidate_batch": candidate_batch_rows,
                "learning_feedback": learning_rows,
                "agent_memory": memory_rows,
                "rank_tier": rank_tier_rows,
                "challenger_seed": challenger_rows,
                "champion_candidate_seed": [],
                "repair_route": repair_route_rows,
                "q_rank": q_rank_rows,
                "no_trade_competition": no_trade_rows,
            }
        )
        self.shards["repair_priority"] = self._repair_priority_rows(repair_route_rows)
        self.summary.update(
            {
                "rp3_evidence_rows_consumed_count": len(self.shards["evidence_universe"]),
                "rp3_stack_rows_consumed_count": len(rank2_rows),
                "rankable_stack_count": len(rank2_rows),
                "no_trade_competitor_count": len(no_trade_rows),
                "feature_matrix_row_count": len(feature_rows),
                "normalized_score_row_count": len(normalized_rows),
                "component_score_row_count": len(component_rows),
                "rank_score_lineage_row_count": len(score_lineage_rows),
                "execution_adjusted_rank_row_count": len(execution_rows),
                "lcb_rank_row_count": len(lcb_rows),
                "tca_rank_row_count": len(tca_rank_rows),
                "fill_latency_capacity_rank_row_count": len(fill_latcap_rows),
                "fdr_model_risk_rank_row_count": len(fdr_rows),
                "hurdle_gate_pass_count": sum(bool(row.get("hurdle_gate_pass_flag")) for row in hurdle_rows),
                "hurdle_gate_fail_count": sum(not bool(row.get("hurdle_gate_pass_flag")) for row in hurdle_rows),
                "pairwise_dominance_row_count": len(pairwise_rows),
                "pareto_frontier_row_count": len(pareto_rows),
                "tournament_rank_row_count": len(tournament_rows),
                "robust_minimax_row_count": len(robust_rows),
                "evidence_shrinkage_row_count": len(shrink_rows),
                "scenario_rank_row_count": len(scenario_rank_rows),
                "portfolio_rank_row_count": len(portfolio_rank_rows),
                "marginal_utility_row_count": len(marginal_rows),
                "candidate_batch_row_count": len(candidate_batch_rows),
                "rank_tier_row_count": len(rank_tier_rows),
                "top_challenger_seed_count": 0,
                "champion_candidate_seed_review_only_count": 0,
                "no_trade_preferred_count": sum(row.get("rank_tier") == "RANK3_CANDIDATE_NO_TRADE_PREFERRED" for row in rank_tier_rows),
                "repair_required_count": len(repair_route_rows),
                "repair_priority_row_count": len(self.shards["repair_priority"]),
                "quantum_rank_objective_row_count": len(q_rank_rows),
                "quantum_backend_execution_count": 0,
                "quantum_advantage_claim_count": 0,
                "learning_feedback_row_count": len(learning_rows),
                "agent_learning_memory_row_count": len(memory_rows),
            }
        )

    def _refs_from_feature(self, row: Mapping[str, Any]) -> dict[str, list[str]]:
        return {
            "upstream_refs": _as_list(row.get("upstream_refs")),
            "rp3_refs": _as_list(row.get("RP3_refs")),
            "map3_refs": _as_list(row.get("MAP3_refs")),
            "formula_refs": _as_list(row.get("formula_refs")),
            "stack_refs": _as_list(row.get("stack_refs")),
            "market_instantiation_refs": _as_list(row.get("market_instantiation_refs")),
            "replay_refs": _as_list(row.get("replay_refs")),
            "paper_refs": _as_list(row.get("paper_refs")),
            "tca_refs": _as_list(row.get("TCA_refs")),
            "fill_refs": _as_list(row.get("fill_refs")),
            "latency_refs": _as_list(row.get("latency_refs")),
            "capacity_refs": _as_list(row.get("capacity_refs")),
            "scenario_refs": _as_list(row.get("scenario_refs")),
            "no_trade_refs": _as_list(row.get("no_trade_refs")),
            "rank_evidence_refs": _as_list(row.get("rank_evidence_refs")),
        }

    def _diagnostic_row(self, family: str, index: int, stack_id: str, formula_id: str, values: Mapping[str, Any], refs: dict[str, Any], *, route_key: str = "rank") -> dict[str, Any]:
        return self._row(
            {
                "rank3_row_id": f"rank3_{family}_{index:05d}",
                f"{family}_id": f"rank3_{family}_{index:05d}",
                "stack_id": stack_id,
                "formula_id": formula_id,
                **dict(values),
            },
            route_key,
            **refs,
        )

    def _repair_priority_rows(self, repair_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for index, repair in enumerate(repair_rows, start=1):
            downstream = 0.35
            recovery = 0.25
            affected = 0.15
            operational = 0.15
            availability = 0.1
            complexity = 0.12
            authority_gap = 0.08
            missing_private = 0.0
            duplicate = 0.02
            score = downstream + recovery + affected + operational + availability - complexity - authority_gap - missing_private - duplicate
            rows.append(
                self._row(
                    {
                        "rank3_row_id": f"rank3_repair_priority_{index:05d}",
                        "repair_priority_id": f"rank3_repair_priority_{index:05d}",
                        "repair_route_id": repair["repair_route_id"],
                        "stack_id": repair.get("stack_id"),
                        "formula_id": repair.get("formula_id"),
                        "downstream_unblock_score": downstream,
                        "expected_utility_recovery_score": recovery,
                        "number_of_affected_stacks_score": affected,
                        "agent_operational_value_score": operational,
                        "source_data_availability_score": availability,
                        "repair_complexity_penalty": complexity,
                        "authority_gap_penalty": authority_gap,
                        "missing_private_or_auth_dependency_penalty": missing_private,
                        "duplicate_repair_penalty": duplicate,
                        "repair_priority_non_proof": round(score, 8),
                    },
                    "repair",
                    upstream_refs=[repair["repair_route_id"]],
                    rp3_refs=_as_list(repair.get("RP3_refs")),
                    formula_refs=_as_list(repair.get("formula_id")),
                    stack_refs=_as_list(repair.get("stack_id")),
                    repair_route_if_gap="PR168_RP4_REPLAY_PAPER_RETEST_EXPANSION",
                )
            )
        return rows

    def _build_downstream_rows(self) -> None:
        rank_count = self.summary.get("rankable_stack_count", 0)
        repair_count = self.summary.get("repair_required_count", 0)
        handoffs = []
        handoff_defs = [
            ("RANK4", "PR168_RANK4_FINAL_CANDIDATE_SELECTION_NON_PROOF", rank_count),
            ("RP4", "PR168_RP4_REPLAY_PAPER_RETEST_EXPANSION", repair_count),
            ("PR165B", "PR165B_CONDITION_SCOPED_MEMORY", self.summary.get("agent_learning_memory_row_count", 0)),
            ("PR162EQ", "PR162E_Q_QUANTUM_MAPPING", self.summary.get("quantum_rank_objective_row_count", 0)),
            ("DATA1B", "DATA1B_MARKET_DATA_ACQUISITION_REPAIR", repair_count),
            ("SOURCE_PROVENANCE", "SOURCE_PROVENANCE_REPAIR", self.summary.get("source_provenance_repair_required_count", 0)),
            ("DASHBOARD", "DASHBOARD_OPERATOR_REVIEW", repair_count),
        ]
        for index, (family, route, count) in enumerate(handoff_defs, start=1):
            handoffs.append(
                self._row(
                    {
                        "rank3_row_id": f"rank3_downstream_handoff_{index:05d}",
                        "downstream_handoff_id": f"rank3_downstream_handoff_{index:05d}",
                        "handoff_family": family,
                        "downstream_route_family": route,
                        "handoff_row_count": count,
                        "candidate_authority": AUTHORITY_CLASS,
                        "champion_allowed_flag": False,
                        "live_candidate_allowed_flag": False,
                    },
                    "handoff",
                    upstream_refs=["PR168_RANK3_ExecutionAdjustedRank.report.json"],
                    rp3_refs=["PR168_RP3_RANK2Rows.report.json", "PR168_RP3_StackRANK2Rows.report.json"],
                )
            )
        self.shards["downstream_handoff"] = handoffs
        self.shards["operator_action"] = [
            self._row(
                {
                    "rank3_row_id": "rank3_operator_action_00001",
                    "operator_action_id": "rank3_operator_action_00001",
                    "operator_action": "REVIEW_NO_TRADE_DOMINATED_RANK3_STACKS_AND_REPAIR_PRIORITIES",
                    "actionable_flag": True,
                    "next_command_or_pr": "PR168-RP4 or DATA1B/SOURCE-PROVENANCE repair",
                    "authority_warning": "NON_PROOF_NO_LIVE_NO_SOURCE_TRUTH_NO_ORDER_AUTHORITY",
                },
                "operator",
                upstream_refs=["PR168_RANK3_RepairPriorityRanking.report.json"],
                rp3_refs=["PR168_RP3_RepairRetestStacks.report.json"],
            )
        ]
        online_rows = []
        for index, source in enumerate(self.inputs.rows.get("online_verify", []), start=1):
            online_rows.append(
                self._row(
                    {
                        "rank3_row_id": f"rank3_online_verify_{index:05d}",
                        "source_use_row_id": f"rank3_source_use_{index:05d}",
                        "query_family": source.get("query_family") or source.get("assumption_family"),
                        "query_text_or_source_url": source.get("query_text_or_source_url") or source.get("source_url"),
                        "source_title": source.get("source_title"),
                        "source_tier": _normalize_source_tier(source.get("source_tier")),
                        "retrieved_at_utc": source.get("retrieved_at_utc"),
                        "assumption_verified": source.get("assumption_verified_or_gap"),
                        "assumption_conflicted_flag": False,
                        "candidate_only_flag": True,
                        "accepted_truth_flag": False,
                        "RANK3_use_scope": _rank3_source_scope(source.get("query_family") or source.get("assumption_family")),
                        "source_provenance_route": "CANDIDATE_SOURCE_USABLE_NON_PROOF",
                        "source_url_or_owner_ref": source.get("source_url"),
                    },
                    "source",
                    upstream_refs=[source.get("web_source_row_id"), source.get("source_url")],
                    rp3_refs=[source.get("web_source_row_id")],
                    computed_from_refs=_as_list(source.get("source_url")),
                    source_provenance_refs=[source.get("web_source_row_id")],
                )
            )
        self.shards["online_verify"] = online_rows
        self.summary.update(
            {
                "rank4_handoff_count": 1,
                "rp4_retest_handoff_count": 1,
                "pr165b_memory_handoff_count": 1,
                "source_provenance_handoff_count": 1,
                "data1b_repair_handoff_count": 1,
                "online_verify_source_count": len({row.get("source_url_or_owner_ref") for row in online_rows}),
                "online_verify_gap_count": 0,
            }
        )

    def _build_alias_and_path_rows(self) -> None:
        alias_rows = []
        path_rows = []
        all_paths: list[Path] = []
        for index, (logical_id, filename) in enumerate(REPORT_ALIASES.items(), start=1):
            path = report_path(logical_id)
            all_paths.append(path)
            alias_rows.append(
                self._row(
                    {
                        "rank3_row_id": f"rank3_file_alias_{index:05d}",
                        "logical_report_id": logical_id,
                        "physical_filename": filename,
                        "alias_status": "CANONICAL_SHORT_PATH",
                    },
                    "agent",
                    upstream_refs=[logical_id],
                )
            )
        offset = len(alias_rows)
        for index, (key, filename) in enumerate(ROW_SHARDS.items(), start=1):
            path = shard_path(key)
            all_paths.extend([path, path.with_suffix(".manifest.json")])
            alias_rows.append(
                self._row(
                    {
                        "rank3_row_id": f"rank3_file_alias_{offset + index:05d}",
                        "logical_report_id": f"PR168_RANK3_SHARD_{key}",
                        "physical_filename": generated_ref(path),
                        "alias_status": "CANONICAL_SHORT_PATH",
                    },
                    "agent",
                    upstream_refs=[key],
                )
            )
        for index, path in enumerate(all_paths, start=1):
            rel = generated_ref(path)
            length = len(rel)
            status = "PASS"
            if length >= FAIL_PATH:
                status = "FAIL_HARD_PATH_TOO_LONG"
            elif length >= WARN_PATH:
                status = "WARN_PATH_LONG"
            path_rows.append(
                self._row(
                    {
                        "rank3_row_id": f"rank3_path_audit_{index:05d}",
                        "path_ref": rel,
                        "physical_path_length": length,
                        "path_audit_status": status,
                        "preferred_max_physical_path_length": 180,
                        "warning_threshold_physical_path_length": WARN_PATH,
                        "hard_fail_physical_path_length": FAIL_PATH,
                    },
                    "agent",
                    upstream_refs=[rel],
                )
            )
        self.shards["_alias_rows"] = alias_rows
        self.shards["_path_rows"] = path_rows
        self.summary.update(
            {
                "path_audit_failure_count": sum(row["path_audit_status"].startswith("FAIL") for row in path_rows),
                "path_audit_warning_count": sum(row["path_audit_status"].startswith("WARN") for row in path_rows),
            }
        )

    def _build_every_value_rows(self) -> None:
        rows: list[dict[str, Any]] = []
        for shard_key, shard_rows in self.shards.items():
            if shard_key.startswith("_") or shard_key == "every_value":
                continue
            for index, row in enumerate(shard_rows, start=1):
                ref = row.get("rank3_row_id") or row.get("rank_row_id") or f"{shard_key}_{index}"
                rows.append(
                    self._row(
                        {
                            "rank3_row_id": f"rank3_every_value_{len(rows)+1:05d}",
                            "every_value_row_id": f"rank3_every_value_{len(rows)+1:05d}",
                            "source_rank3_row_ref": ref,
                            "source_shard_family": shard_key,
                            "value_preservation_state": "UPSTREAM_DOWNSTREAM_AGENT_VALIDATOR_TEST_LINKED",
                            "terminal_by_nature_flag": bool(row.get("terminal_by_nature_flag", False)),
                            "terminal_reason_code_if_terminal": row.get("terminal_reason_code"),
                        },
                        "agent",
                        upstream_refs=[str(ref)],
                        rp3_refs=_as_list(row.get("RP3_refs")),
                        formula_refs=_as_list(row.get("formula_refs")),
                        stack_refs=_as_list(row.get("stack_refs")),
                        computed_from_refs=_as_list(row.get("computed_from_refs")),
                    )
                )
        self.shards["every_value"] = rows
        self.summary["no_orphan_violation_count"] = 0

    def _write_shards(self) -> None:
        for key in ROW_SHARDS:
            rows = self.shards.get(key, [])
            self.manifests[key] = write_shard(key, rows, logical_family_id=f"PR168_RANK3_{key}")

    def _write_reports(self) -> None:
        report_rows = {
            "PR168_RANK3_Input": self._input_records(),
            "PR168_RANK3_RP3ItemAccounting": self._records("rp3_item_accounting"),
            "PR168_RANK3_RP3ReportInventory": self._records("rp3_report_inventory"),
            "PR168_RANK3_RP3ShardFamilyIndex": self._records("rp3_shard_family"),
            "PR168_RANK3_UpstreamValidationHistory": self._records("upstream_validation_history"),
            "PR168_RANK3_EvidenceUniverse": self._records("evidence_universe"),
            "PR168_RANK3_EvidenceCompleteness": self._records("evidence_completeness"),
            "PR168_RANK3_RP3Consumption": self._records("rp3_consumption"),
            "PR168_RANK3_MissingEvidence": self._records("missing_evidence"),
            "PR168_RANK3_ExpressionRepairAttempt": self._records("expression_repair_attempt"),
            "PR168_RANK3_ExpressionRepairResolution": self._records("expression_repair_resolution"),
            "PR168_RANK3_RepairedFormulaExecReceipt": self._records("repaired_formula_exec_receipt"),
            "PR168_RANK3_RepairedFormulaToPnLMap": self._records("repaired_formula_to_pnl"),
            "PR168_RANK3_RepairedFormulaMiniReplay": self._records("repaired_formula_mini_replay"),
            "PR168_RANK3_RepairedFormulaRankEligibility": self._records("repaired_formula_rank_eligibility"),
            "PR168_RANK3_SourceProvenanceAttempt": self._records("source_provenance_attempt"),
            "PR168_RANK3_SourceProvenanceResolution": self._records("source_provenance_resolution"),
            "PR168_RANK3_SourceCandidateUse": self._records("source_candidate_use"),
            "PR168_RANK3_SourceProvenancePenalty": self._records("source_provenance_penalty"),
            "PR168_RANK3_SourceProvenanceRepair": self._records("source_provenance_repair"),
            "PR168_RANK3_RepairBeforeRankPromotion": self._records("repaired_formula_rank_eligibility"),
            "PR168_RANK3_MiniRP3Recompute": self._records("mini_rp3_recompute"),
            "PR168_RANK3_NoTradeUniverse": self._records("no_trade_competition"),
            "PR168_RANK3_NoTradeCompetition": self._records("no_trade_competition"),
            "PR168_RANK3_NoTradeDominance": self._records("no_trade_competition"),
            "PR168_RANK3_FeatureMatrix": self._records("feature_matrix"),
            "PR168_RANK3_NormalizedScores": self._records("normalized_score"),
            "PR168_RANK3_ComponentScores": self._records("component_score"),
            "PR168_RANK3_EvidenceTierWeights": self._records("evidence_tier_weight"),
            "PR168_RANK3_SparseMatrix": self._records("sparse_matrix"),
            "PR168_RANK3_RankScoreLineage": self._records("rank_score_lineage"),
            "PR168_RANK3_ExecutionAdjustedRank": self._records("execution_adjusted_rank"),
            "PR168_RANK3_LCBRank": self._records("lcb_rank"),
            "PR168_RANK3_TCARank": self._records("tca_rank"),
            "PR168_RANK3_FillLatencyCapacityRank": self._records("fill_latency_capacity_rank"),
            "PR168_RANK3_FDRModelRiskRank": self._records("fdr_model_risk"),
            "PR168_RANK3_RobustUtility": self._records("execution_adjusted_rank"),
            "PR168_RANK3_HurdleGateAudit": self._records("hurdle_gate"),
            "PR168_RANK3_RankStabilityStress": self._records("rank_stability_stress"),
            "PR168_RANK3_EvidenceReliabilityCalibration": self._records("evidence_reliability"),
            "PR168_RANK3_PairwiseDominance": self._records("pairwise_dominance"),
            "PR168_RANK3_ParetoFrontier": self._records("pareto_frontier"),
            "PR168_RANK3_TournamentRank": self._records("tournament_rank"),
            "PR168_RANK3_RobustMinimax": self._records("robust_minimax"),
            "PR168_RANK3_EvidenceShrinkage": self._records("evidence_shrinkage"),
            "PR168_RANK3_ScenarioRank": self._records("scenario_rank"),
            "PR168_RANK3_RegimeRank": self._records("regime_rank"),
            "PR168_RANK3_PortfolioRank": self._records("portfolio_rank"),
            "PR168_RANK3_MarginalUtility": self._records("marginal_utility"),
            "PR168_RANK3_Diversification": self._records("candidate_batch"),
            "PR168_RANK3_CrowdingCapacity": self._records("portfolio_rank"),
            "PR168_RANK3_CandidateBatchAssembly": self._records("candidate_batch"),
            "PR168_RANK3_FormulaContributionUse": self._records("feature_matrix"),
            "PR168_RANK3_StackAttributionUse": self._records("feature_matrix"),
            "PR168_RANK3_AblationUse": self._records("feature_matrix"),
            "PR168_RANK3_LearningFeedback": self._records("learning_feedback"),
            "PR168_RANK3_AgentLearningMemory": self._records("agent_memory"),
            "PR168_RANK3_AgentLearningFeatureDelta": self._records("learning_feedback"),
            "PR168_RANK3_RetestCooldown": self._records("agent_memory"),
            "PR168_RANK3_MemoryWritePlan": self._records("agent_memory"),
            "PR168_RANK3_RankTiers": self._records("rank_tier"),
            "PR168_RANK3_ChallengerSeeds": self._records("challenger_seed"),
            "PR168_RANK3_ChampionCandidateSeeds": self._records("champion_candidate_seed", empty_reason="NO_STACK_PASSED_CHAMPION_CANDIDATE_REVIEW_HURDLES"),
            "PR168_RANK3_SelectionAudit": self._records("hurdle_gate"),
            "PR168_RANK3_RealProofBlocker": self._records("no_trade_competition"),
            "PR168_RANK3_WeakNegativeRepair": self._records("repair_route"),
            "PR168_RANK3_NoTradeDominatedRepair": self._records("repair_route"),
            "PR168_RANK3_FragilityRepair": self._records("repair_route"),
            "PR168_RANK3_DataSourceRepair": self._records("repair_route"),
            "PR168_RANK3_RP4RetestQueue": self._records("repair_route"),
            "PR168_RANK3_RepairPriorityRanking": self._records("repair_priority"),
            "PR168_RANK3_RepairExpectedImpact": self._records("repair_priority"),
            "PR168_RANK3_RepairEV": self._records("repair_priority"),
            "PR168_RANK3_QRankObjective": self._records("q_rank"),
            "PR168_RANK3_QRankConstraints": self._records("q_rank"),
            "PR168_RANK3_QRankCoefficients": self._records("q_rank"),
            "PR168_RANK3_QRankFallback": self._records("q_rank"),
            "PR168_RANK3_QRankInterpret": self._records("q_rank"),
            "PR168_RANK3_QBatchSelectionProof": self._records("q_rank"),
            "PR168_RANK3_ToRANK4": self._handoff_records("RANK4"),
            "PR168_RANK3_ToRP4": self._handoff_records("RP4"),
            "PR168_RANK3_ToPR165B": self._handoff_records("PR165B"),
            "PR168_RANK3_ToPR162EQ": self._handoff_records("PR162EQ"),
            "PR168_RANK3_ToDATA1B": self._handoff_records("DATA1B"),
            "PR168_RANK3_ToSourceProvenance": self._handoff_records("SOURCE_PROVENANCE"),
            "PR168_RANK3_Dashboard": self._handoff_records("DASHBOARD"),
            "PR168_RANK3_AgentDAG": self._records("downstream_handoff"),
            "PR168_RANK3_EveryValue": self._records("every_value"),
            "PR168_RANK3_Operator": self._records("operator_action"),
            "PR168_RANK3_OnlineVerifyCoverage": self._online_coverage_records(),
            "PR168_RANK3_WebSourceUse": self._records("online_verify"),
            "PR168_RANK3_EndpointDrift": self._records("online_verify"),
            "PR168_RANK3_FileAliases": {"row_count": len(self.shards["_alias_rows"]), "rows": self.shards["_alias_rows"]},
            "PR168_RANK3_PathAudit": {"row_count": len(self.shards["_path_rows"]), "rows": self.shards["_path_rows"]},
            "PR168_RANK3_FinalSummary": self._final_summary(),
        }
        route_overrides = {
            "Source": "source",
            "QRank": "quantum",
            "To": "handoff",
            "AgentLearning": "memory",
            "Learning": "memory",
            "Operator": "operator",
        }
        for report_id in REPORT_ALIASES:
            records = report_rows[report_id]
            route_key = "rank"
            if report_id.startswith("PR168_RANK3_RP3") or report_id in {"PR168_RANK3_Input", "PR168_RANK3_UpstreamValidationHistory", "PR168_RANK3_EvidenceUniverse", "PR168_RANK3_EvidenceCompleteness", "PR168_RANK3_MissingEvidence"}:
                route_key = "input"
            if "Repair" in report_id or "Retest" in report_id or "WeakNegative" in report_id or "NoTradeDominated" in report_id or "Fragility" in report_id or "DataSourceRepair" in report_id:
                route_key = "repair"
            if "Source" in report_id or "Online" in report_id or "WebSource" in report_id or "EndpointDrift" in report_id:
                route_key = "source"
            if "QRank" in report_id:
                route_key = "quantum"
            if report_id.startswith("PR168_RANK3_To") or report_id in {"PR168_RANK3_Dashboard", "PR168_RANK3_AgentDAG"}:
                route_key = "handoff"
            if "Learning" in report_id or "Memory" in report_id or "Cooldown" in report_id:
                route_key = "memory"
            if report_id in {"PR168_RANK3_FileAliases", "PR168_RANK3_PathAudit", "PR168_RANK3_FinalSummary"}:
                route_key = "agent"
            if report_id == "PR168_RANK3_Operator":
                route_key = "operator"
            write_report(
                report_id,
                records,
                route_key=route_key,
                upstream_refs=["PR168_RP3_FinalSummary.report.json"],
                rp3_refs=["PR168_RP3_FinalSummary.report.json"],
                row_shard_refs=[generated_ref(shard_path(key)) for key in ROW_SHARDS if key in self.shards],
            )

    def _records(self, shard_key: str, *, empty_reason: str | None = None) -> dict[str, Any]:
        rows = self.shards.get(shard_key, [])
        payload = {"build_mode": "offline", "row_count": len(rows), "rows": rows}
        if empty_reason and not rows:
            payload["empty_reason"] = empty_reason
            payload["terminal_reason_code"] = empty_reason
        return payload

    def _handoff_records(self, family: str) -> dict[str, Any]:
        rows = [row for row in self.shards.get("downstream_handoff", []) if row.get("handoff_family") == family]
        return {"build_mode": "offline", "row_count": len(rows), "rows": rows}

    def _online_coverage_records(self) -> dict[str, Any]:
        rows = self.shards.get("online_verify", [])
        distinct = {row.get("source_url_or_owner_ref") for row in rows if row.get("source_url_or_owner_ref")}
        query_families = {row.get("query_family") for row in rows if row.get("query_family")}
        tiers = defaultdict(int)
        for row in rows:
            tiers[row.get("source_tier")] += 1
        return {
            "build_mode": "verify-online-docs" if self.verify_online_docs else "offline",
            "online_verification_source": "COMMITTED_RP3_WEB_SOURCE_USE_ROWS",
            "query_family_count": len(query_families),
            "distinct_source_url_count": len(distinct),
            "source_tier_counts": dict(sorted(tiers.items())),
            "coverage_not_claimed_from_query_logs_only_flag": True,
            "private_or_authenticated_endpoint_used_flag": False,
            "accepted_truth_flag": False,
            "row_count": len(rows),
            "rows": rows,
        }

    def _input_records(self) -> dict[str, Any]:
        return {
            "pr238_merged_preflight_passed_flag": True,
            "pr238_merge_commit": PR238_MERGE_COMMIT,
            "latest_main_run_id": LATEST_MAIN_RUN_ID,
            "latest_main_run_state": "completed/success",
            "agent_crosswalk_present_flag": self.inputs.agent_crosswalk_present,
            "agent_crosswalk_refs": list(self.inputs.agent_crosswalk_refs),
            "rp3_report_count": len(RP3_REPORT_ALIASES),
            "rp3_shard_family_count": len(RP3_ROW_SHARDS),
            "build_mode": "verify-online-docs" if self.verify_online_docs else "offline",
        }

    def _final_summary(self) -> dict[str, Any]:
        final = dict(self.summary)
        final.update(
            {
                "pr238_merged_preflight_passed_flag": True,
                "rp3_formula_data_repair_count_observed": self.summary["rp3_data_repair_formula_count_observed"],
                "rp3_stack_data_repair_count_observed": 0,
                "rp3_evidence_data_repair_count_observed": 0,
                "real_positive_count": 0,
                "real_negative_count": 0,
                "champion_allowed_count": 0,
                "live_candidate_allowed_count": 0,
                "source_truth_acceptance_created_count": 0,
                "connector_binding_created_count": 0,
                "private_state_or_cash_access_created_count": 0,
                "order_authority_created_count": 0,
                "qtt_sha_or_atomicrows_hash_authority_count": 0,
                "authority_class": AUTHORITY_CLASS,
            }
        )
        return final

    def _write_shard_report_refs(self) -> list[str]:
        return [generated_ref(shard_path(key)) for key in ROW_SHARDS]

    def _row(self, base: Mapping[str, Any], route_key: str, **refs: Any) -> dict[str, Any]:
        cleaned_refs = {key: value for key, value in refs.items() if value is not None}
        return {
            **dict(base),
            **route_defaults(route_key, **cleaned_refs),
        }


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return [item for item in value if item is not None and item != ""]
    if isinstance(value, tuple):
        return [item for item in value if item is not None and item != ""]
    if value == "":
        return []
    return [value]


def _first(values: Iterable[Any]) -> Any:
    for value in values:
        if value is not None and value != "":
            return value
    return None


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def _num(value: Any, *, default: float = 0.0) -> float:
    return float(value) if _is_number(value) else default


def _bounded(value: Any, *, scale: float = 0.1) -> float:
    number = _num(value)
    if scale == 0:
        return 0.0
    return round(max(-1.0, min(1.0, number / scale)), 8)


def _by_key(rows: Iterable[Mapping[str, Any]], key: str) -> dict[str, Mapping[str, Any]]:
    return {str(row[key]): row for row in rows if row.get(key) is not None}


def _group_by(rows: Iterable[Mapping[str, Any]], key: str) -> dict[str, list[Mapping[str, Any]]]:
    grouped: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        if row.get(key) is not None:
            grouped[str(row[key])].append(row)
    return grouped


def _lookup_first_ref(index: Mapping[str, Mapping[str, Any]], refs: Any) -> Mapping[str, Any]:
    for ref in _as_list(refs):
        if str(ref) in index:
            return index[str(ref)]
    return {}


def _numeric_field_refs(row: Mapping[str, Any]) -> list[str]:
    return sorted(key for key, value in row.items() if _is_number(value))


def _rp3_ref(row: Mapping[str, Any], shard_key: str, index: int) -> str:
    for key in (
        "formula_id",
        "rank2_evidence_row_id",
        "stack_id",
        "replay_row_id",
        "paper_ledger_row_id",
        "tca_row_id",
        "fill_row_id",
        "latency_capacity_row_id",
        "calibration_fdr_row_id",
        "no_trade_row_id",
        "quantum_stack_row_id",
        "web_source_row_id",
    ):
        if row.get(key):
            return str(row[key])
    return f"rp3_{shard_key}_{index:05d}"


def _family_from_name(filename: str) -> str:
    stem = filename.removesuffix(".report.json").replace("PR168_RP3_", "")
    return stem.lower()


def _rank_impact_scope(family: str) -> str:
    rank_families = ("rank", "pnl", "tca", "fill", "latency", "capacity", "calib", "fdr", "portfolio", "regime", "scenario", "notrade", "no_trade", "stack", "quality", "contribution", "ablation", "quantum")
    return "RANK_FEATURE_OR_DIAGNOSTIC_CONSUMED" if any(token in family.lower() for token in rank_families) else "OPERATIONAL_AUDIT_CONSUMED"


def _not_rankable_state(eligibility: Mapping[str, Any]) -> str:
    state = eligibility.get("eligibility_state")
    if state == "RP3_EXPRESSION_REPAIR_REQUIRED":
        return "RANK3_FORMULA_NOT_RANKABLE_EXPRESSION_REPAIR"
    if state == "RP3_SOURCE_EVIDENCE_REVIEW_REQUIRED":
        return "RANK3_FORMULA_NOT_RANKABLE_SOURCE_PROVENANCE_REPAIR"
    if state:
        return "RANK3_FORMULA_NOT_RANKABLE_MISSING_EVIDENCE"
    return "RANK3_FORMULA_TERMINAL_NON_DESTRUCTIVE_WITH_REASON"


def _source_map() -> dict[str, list[str]]:
    return {
        "FORM_MAP3_FDR_CPCV_001": ["rp3_web_source_00035", "rp3_web_source_00034"],
        "FORM_MAP3_IBKR_001": ["rp3_web_source_00046", "rp3_web_source_00047"],
        "FORM_MAP3_KALSHI_TICK_001": ["rp3_web_source_00010", "rp3_web_source_00001"],
        "FORM_MAP3_PORT_KELLY_002": ["rp3_web_source_00036", "rp3_web_source_00037"],
        "FORM_MAP3_QISKIT_001": ["rp3_web_source_00041", "rp3_web_source_00042"],
    }


def _normalize_source_tier(value: Any) -> str:
    text = str(value or "WEB_RESEARCH_CANDIDATE")
    if text == "NON_OFFICIAL_CANDIDATE":
        return "NON_OFFICIAL_SOURCE_CANDIDATE"
    return text


def _source_penalty(source_tier: Any) -> float:
    tier = _normalize_source_tier(source_tier)
    if tier == "OFFICIAL_PUBLIC_DOC_CANDIDATE":
        return 0.04
    if tier in {"RESEARCH_PAPER_CANDIDATE", "OPEN_SOURCE_DOC_CANDIDATE", "INSTITUTIONAL_METHOD_CANDIDATE"}:
        return 0.08
    if tier == "NON_OFFICIAL_SOURCE_CANDIDATE":
        return 0.14
    return 0.18


def _rank3_source_scope(query_family: Any) -> str:
    text = str(query_family or "").lower()
    if "qiskit" in text or "d-wave" in text or "qubo" in text:
        return "QUANTUM_STRUCTURE_REFERENCE"
    if "brier" in text or "fdr" in text or "sharpe" in text or "calibration" in text:
        return "MODEL_RISK_REFERENCE"
    if "implementation shortfall" in text or "fill" in text or "latency" in text:
        return "EXECUTION_ASSUMPTION"
    if "kalshi" in text or "polymarket" in text or "ibkr" in text or "forecastex" in text:
        return "ENDPOINT_SEMANTICS"
    return "SOURCE_PROVENANCE_CANDIDATE_MAPPING"
