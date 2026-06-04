"""Executable deterministic algorithm seed library for PR162D-R2A."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


AlgorithmCallable = Callable[[dict[str, Any]], dict[str, Any]]


def deterministic_candidate_ranking(inputs: dict[str, Any]) -> dict[str, Any]:
    candidates = [item for item in inputs["candidates"] if item.get("valid_flag", True)]

    def sort_key(item: dict[str, Any]) -> tuple[float, str, str, str]:
        return (
            -float(item.get("final_score", item.get("score", 0.0))),
            str(item.get("latency_class", "")),
            str(item.get("risk_class", "")),
            str(item["candidate_id"]),
        )

    ranked = sorted(candidates, key=sort_key)
    return {"ranked_candidate_ids": [item["candidate_id"] for item in ranked]}


def greedy_market_bundle_selection(inputs: dict[str, Any]) -> dict[str, Any]:
    budget = float(inputs["budget"])
    max_exposure = float(inputs["max_exposure"])
    selected: list[str] = []
    spent = 0.0
    exposure = 0.0
    candidates = sorted(
        inputs["candidates"],
        key=lambda item: (
            -float(item["expected_net_value"]) / max(float(item["capital_required"]), 1.0e-9),
            str(item["candidate_id"]),
        ),
    )
    for item in candidates:
        cost = float(item["capital_required"])
        risk_exposure = float(item["risk_exposure"])
        if spent + cost <= budget and exposure + risk_exposure <= max_exposure:
            selected.append(str(item["candidate_id"]))
            spent += cost
            exposure += risk_exposure
    return {"selected_candidate_ids": selected, "capital_used": spent, "risk_exposure_used": exposure}


def replay_paper_eligibility_router(inputs: dict[str, Any]) -> dict[str, Any]:
    record = inputs["formulation_record"]
    route = inputs.get("route_record") or {}
    if record.get("validator_materiality_status") == "FORMULATION_FULLY_MATERIALIZED" and route:
        state = "REPLAY_PAPER_ROUTE_READY"
        fill_action = None
    elif record.get("validator_materiality_status") == "FORMULATION_FULLY_MATERIALIZED":
        state = "FORMULATION_ONLY_ROUTE_FILL_REQUIRED"
        fill_action = "CREATE_ROUTE_FILL_ACTION"
    else:
        state = "FIELD_FILL_REQUIRED"
        fill_action = "CREATE_FORMULATION_FIELD_FILL_ACTION"
    return {"route_state": state, "fill_action": fill_action}


def parameter_stack_selector(inputs: dict[str, Any]) -> dict[str, Any]:
    stacks = [item for item in inputs["stacks"] if item.get("compatible_flag", True)]
    ranked = sorted(
        stacks,
        key=lambda item: (
            -(
                float(item.get("compatibility_score", 0.0))
                + float(item.get("replay_value_score", 0.0))
                - float(item.get("risk_score", 0.0))
            ),
            str(item["stack_id"]),
        ),
    )
    return {"selected_stack_candidate": ranked[0]["stack_id"] if ranked else None}


def build_parameter_pack_from_defaults(inputs: dict[str, Any]) -> dict[str, Any]:
    defaults = dict(inputs["defaults"])
    ranges = dict(inputs["ranges"])
    return {"parameter_pack": {"defaults": defaults, "ranges": ranges, "version": inputs.get("version", "v1")}}


def stable_dedupe_by_family(inputs: dict[str, Any]) -> dict[str, Any]:
    seen: set[str] = set()
    selected: list[str] = []
    for item in sorted(inputs["records"], key=lambda row: str(row["record_id"])):
        family_key = str(item["equivalence_family"])
        if family_key not in seen:
            seen.add(family_key)
            selected.append(str(item["record_id"]))
    return {"canonical_record_ids": selected}


def top_k_candidate_filter(inputs: dict[str, Any]) -> dict[str, Any]:
    ranked = deterministic_candidate_ranking({"candidates": inputs["candidates"]})["ranked_candidate_ids"]
    return {"top_candidate_ids": ranked[: int(inputs["k"])]}


def latency_bucket_router(inputs: dict[str, Any]) -> dict[str, Any]:
    buckets: dict[str, list[str]] = {}
    for item in inputs["candidates"]:
        tier = str(item.get("latency_class", "REPLAY_PAPER_ONLY"))
        buckets.setdefault(tier, []).append(str(item["candidate_id"]))
    return {"latency_buckets": {key: sorted(value) for key, value in sorted(buckets.items())}}


def source_confidence_ranker(inputs: dict[str, Any]) -> dict[str, Any]:
    ranked = sorted(
        inputs["sources"],
        key=lambda item: (-float(item.get("source_confidence_score", 0.0)), str(item["source_locator_id"])),
    )
    return {"ranked_source_locator_ids": [item["source_locator_id"] for item in ranked]}


def field_fill_priority_order(inputs: dict[str, Any]) -> dict[str, Any]:
    ranked = sorted(
        inputs["actions"],
        key=lambda item: (-float(item.get("overall_materialization_priority_score", 0.0)), str(item["fill_action_id"])),
    )
    return {"ordered_fill_action_ids": [item["fill_action_id"] for item in ranked]}


def route_fill_priority_order(inputs: dict[str, Any]) -> dict[str, Any]:
    ranked = sorted(
        inputs["actions"],
        key=lambda item: (-float(item.get("route_fill_need_score", 0.0)), str(item["route_fill_action_id"])),
    )
    return {"ordered_route_fill_action_ids": [item["route_fill_action_id"] for item in ranked]}


def portfolio_exposure_check(inputs: dict[str, Any]) -> dict[str, Any]:
    exposure = sum(float(item["exposure"]) for item in inputs["positions"])
    return {"exposure": exposure, "within_limit_flag": exposure <= float(inputs["max_exposure"])}


def parameter_range_clipper(inputs: dict[str, Any]) -> dict[str, Any]:
    value = float(inputs["value"])
    return {"clipped_value": max(float(inputs["min_value"]), min(float(inputs["max_value"]), value))}


def compatibility_threshold_filter(inputs: dict[str, Any]) -> dict[str, Any]:
    threshold = float(inputs["threshold"])
    return {
        "compatible_ids": sorted(
            str(item["candidate_id"])
            for item in inputs["candidates"]
            if float(item.get("compatibility_score", 0.0)) >= threshold
        )
    }


def quantum_priority_ranker(inputs: dict[str, Any]) -> dict[str, Any]:
    ranked = sorted(
        inputs["candidates"],
        key=lambda item: (-float(item.get("quantum_priority_score", 0.0)), str(item["candidate_id"])),
    )
    return {"ranked_quantum_candidate_ids": [item["candidate_id"] for item in ranked]}


def family_variant_normalizer(inputs: dict[str, Any]) -> dict[str, Any]:
    token = str(inputs["raw_label"]).strip().lower().replace(" ", "_").replace("-", "_")
    return {"domain_family_key": token.split("__")[0], "variant_key": token}


def replay_paper_batch_partition(inputs: dict[str, Any]) -> dict[str, Any]:
    batch_size = int(inputs["batch_size"])
    ids = [str(item) for item in inputs["candidate_ids"]]
    return {"batches": [ids[index : index + batch_size] for index in range(0, len(ids), batch_size)]}


def cacheability_classifier(inputs: dict[str, Any]) -> dict[str, Any]:
    tier = str(inputs["compute_tier"])
    return {"cacheable": tier in {"TIER_0_CONSTANT_OR_CACHED_PARAMETER", "TIER_1_SIMPLE_ARITHMETIC_FORMULA", "TIER_2_VECTORIZED_FEATURE_FORMULA"}}


def hot_path_precompute_selector(inputs: dict[str, Any]) -> dict[str, Any]:
    hot: list[str] = []
    precompute: list[str] = []
    for item in inputs["formulations"]:
        if item.get("compute_tier") in {"TIER_0_CONSTANT_OR_CACHED_PARAMETER", "TIER_1_SIMPLE_ARITHMETIC_FORMULA"}:
            hot.append(str(item["formulation_id"]))
        else:
            precompute.append(str(item["formulation_id"]))
    return {"hot_path_candidate_ids": sorted(hot), "precompute_required_ids": sorted(precompute)}


def formula_coverage_classifier(inputs: dict[str, Any]) -> dict[str, Any]:
    backed = [item for item in inputs["mappings"] if item.get("formulation_ref")]
    unbacked = [item for item in inputs["mappings"] if not item.get("formulation_ref")]
    return {"formulation_backed_count": len(backed), "formulation_unmapped_count": len(unbacked)}


def exact_fill_action_builder(inputs: dict[str, Any]) -> dict[str, Any]:
    return {
        "fill_action": {
            "missing_field": inputs["missing_field"],
            "responsible_agent": inputs["responsible_agent"],
            "priority_score": float(inputs["priority_score"]),
        }
    }


def owner_review_escalation_selector(inputs: dict[str, Any]) -> dict[str, Any]:
    selected = [
        str(item["record_id"])
        for item in inputs["records"]
        if item.get("owner_review_required_flag") or float(item.get("priority_score", 0.0)) >= float(inputs["threshold"])
    ]
    return {"owner_review_record_ids": sorted(selected)}


def market_bundle_diversifier(inputs: dict[str, Any]) -> dict[str, Any]:
    selected: list[str] = []
    seen_families: set[str] = set()
    for item in sorted(inputs["candidates"], key=lambda row: (-float(row["score"]), str(row["candidate_id"]))):
        family = str(item["family"])
        if family not in seen_families:
            seen_families.add(family)
            selected.append(str(item["candidate_id"]))
    return {"diversified_candidate_ids": selected}


def objective_constraint_pairer(inputs: dict[str, Any]) -> dict[str, Any]:
    return {
        "objective_constraint_pairs": [
            {"objective_ref": objective, "constraint_ref": constraint}
            for objective, constraint in zip(inputs["objective_refs"], inputs["constraint_refs"], strict=True)
        ]
    }


def comparator_assignment(inputs: dict[str, Any]) -> dict[str, Any]:
    assignments = {
        str(item["quantum_formulation_id"]): str(item.get("preferred_comparator_ref", inputs["default_comparator_ref"]))
        for item in inputs["quantum_records"]
    }
    return {"classical_comparator_assignments": assignments}


def test_vector_smoke_selector(inputs: dict[str, Any]) -> dict[str, Any]:
    selected = sorted(str(item["test_vector_id"]) for item in inputs["test_vectors"] if item.get("smoke_test_flag", True))
    return {"smoke_test_vector_ids": selected[: int(inputs["limit"])]}


def schema_version_router(inputs: dict[str, Any]) -> dict[str, Any]:
    return {"schema_route": f"{inputs['candidate_type']}::{inputs['schema_version']}"}


def promotion_seed_classifier(inputs: dict[str, Any]) -> dict[str, Any]:
    if inputs.get("replay_paper_candidate_flag") and inputs.get("formulation_materialization_state") == "FORMULATION_FULLY_MATERIALIZED":
        state = "NEEDS_REPLAY_PAPER_EVIDENCE"
    else:
        state = "NEEDS_OWNER_REVIEW"
    return {"promotion_state_seed": state}


def deterministic_arbitration_merge(inputs: dict[str, Any]) -> dict[str, Any]:
    merged: dict[str, Any] = {}
    for record in sorted(inputs["records"], key=lambda row: str(row["source_priority"])):
        merged.update(record["values"])
    return {"merged_values": merged}


def source_locator_ranker(inputs: dict[str, Any]) -> dict[str, Any]:
    return source_confidence_ranker({"sources": inputs["source_locators"]})


@dataclass(frozen=True)
class AlgorithmSpec:
    algorithm_id: str
    procedure: str
    implementation: AlgorithmCallable
    required_inputs: tuple[str, ...]
    outputs: tuple[str, ...]
    domain_family_key: str
    subfamily_key: str
    variant_key: str
    test_inputs: dict[str, Any]
    failure_modes: tuple[str, ...] = ("missing required input", "non-numeric score where numeric score is required")
    compute_tier: str = "TIER_3_CLASSICAL_OPTIMIZER_FORMULA"
    latency_class: str = "PRECOMPUTE_REQUIRED"

    @property
    def callable_ref(self) -> str:
        return f"{__name__}:{self.implementation.__name__}"

    def test_vector(self) -> dict[str, Any]:
        return {
            "test_vector_id": f"PR162D_R2A_TV_ALGORITHM::{self.algorithm_id}",
            "callable_ref": self.callable_ref,
            "inputs": self.test_inputs,
            "expected_outputs": self.implementation(dict(self.test_inputs)),
            "tolerance": 0.0,
            "source_truth_status": "OWNER_TEMPLATE",
            "candidate_truth_status": "CANDIDATE",
            "live_order_authority": False,
        }


def algorithm_specs() -> list[AlgorithmSpec]:
    candidates = [
        {"candidate_id": "A", "final_score": 0.7, "latency_class": "B", "risk_class": "L", "valid_flag": True},
        {"candidate_id": "B", "final_score": 0.9, "latency_class": "A", "risk_class": "M", "valid_flag": True},
        {"candidate_id": "C", "final_score": 0.9, "latency_class": "A", "risk_class": "L", "valid_flag": True},
    ]
    return [
        AlgorithmSpec("DETERMINISTIC_CANDIDATE_RANKING", "Filter invalid candidates, compute final_score, sort descending, and tie-break by latency_class, risk_class, candidate_id.", deterministic_candidate_ranking, ("candidates",), ("ranked_candidate_ids",), "deterministic_candidate_ranking_algorithm", "candidate_ranking", "owner_template_v1", {"candidates": candidates}),
        AlgorithmSpec("GREEDY_MARKET_BUNDLE_SELECTION", "Sort candidates by expected_net_value/capital_required and greedily add while budget and exposure remain satisfied.", greedy_market_bundle_selection, ("candidates", "budget", "max_exposure"), ("selected_candidate_ids",), "risk_capital_sizing", "greedy_market_bundle_selection", "owner_template_v1", {"budget": 100, "max_exposure": 80, "candidates": [{"candidate_id": "A", "expected_net_value": 10, "capital_required": 50, "risk_exposure": 30}, {"candidate_id": "B", "expected_net_value": 8, "capital_required": 20, "risk_exposure": 20}, {"candidate_id": "C", "expected_net_value": 6, "capital_required": 40, "risk_exposure": 40}]}),
        AlgorithmSpec("REPLAY_PAPER_ELIGIBILITY_ROUTER", "Route materialized formulations with route records to replay/paper, create route fill actions for route gaps, and field-fill actions for unmaterialized records.", replay_paper_eligibility_router, ("formulation_record", "route_record"), ("route_state", "fill_action"), "deterministic_candidate_ranking_algorithm", "replay_paper_router", "owner_template_v1", {"formulation_record": {"validator_materiality_status": "FORMULATION_FULLY_MATERIALIZED"}, "route_record": {"route_id": "R1"}}),
        AlgorithmSpec("PARAMETER_STACK_SELECTOR", "Reject incompatible parameter stacks, compute deterministic stack score, rank, and select the top stack.", parameter_stack_selector, ("stacks",), ("selected_stack_candidate",), "parameter_default_range_pack", "parameter_stack_selector", "owner_template_v1", {"stacks": [{"stack_id": "S1", "compatible_flag": True, "compatibility_score": 0.7, "replay_value_score": 0.5, "risk_score": 0.1}, {"stack_id": "S2", "compatible_flag": False, "compatibility_score": 1.0, "replay_value_score": 1.0, "risk_score": 0.0}]}),
        AlgorithmSpec("BUILD_PARAMETER_PACK_FROM_DEFAULTS", "Return a versioned parameter pack from candidate defaults and ranges.", build_parameter_pack_from_defaults, ("defaults", "ranges", "version"), ("parameter_pack",), "parameter_default_range_pack", "parameter_pack_builder", "owner_template_v1", {"defaults": {"max_fraction_cap": 0.1}, "ranges": {"max_fraction_cap": [0.0, 0.25]}, "version": "v1"}),
        AlgorithmSpec("STABLE_DEDUPE_BY_FAMILY", "Sort records, keep first record per equivalence family, and preserve duplicate provenance externally.", stable_dedupe_by_family, ("records",), ("canonical_record_ids",), "deterministic_candidate_ranking_algorithm", "dedupe", "family_v1", {"records": [{"record_id": "R2", "equivalence_family": "F1"}, {"record_id": "R1", "equivalence_family": "F1"}, {"record_id": "R3", "equivalence_family": "F2"}]}),
        AlgorithmSpec("TOP_K_CANDIDATE_FILTER", "Rank candidates with deterministic ordering and return the top k candidate IDs.", top_k_candidate_filter, ("candidates", "k"), ("top_candidate_ids",), "deterministic_candidate_ranking_algorithm", "top_k", "owner_template_v1", {"candidates": candidates, "k": 2}),
        AlgorithmSpec("LATENCY_BUCKET_ROUTER", "Group candidates by latency class for hot path and precompute planning.", latency_bucket_router, ("candidates",), ("latency_buckets",), "latency_slippage_cost", "latency_router", "owner_template_v1", {"candidates": [{"candidate_id": "A", "latency_class": "HOT_PATH_ELIGIBLE_CANDIDATE"}, {"candidate_id": "B", "latency_class": "PRECOMPUTE_REQUIRED"}]}),
        AlgorithmSpec("SOURCE_CONFIDENCE_RANKER", "Rank candidate source locators by confidence while preserving candidate status.", source_confidence_ranker, ("sources",), ("ranked_source_locator_ids",), "probability_calibration_edge", "source_confidence", "owner_template_v1", {"sources": [{"source_locator_id": "S1", "source_confidence_score": 0.6}, {"source_locator_id": "S2", "source_confidence_score": 0.8}]}),
        AlgorithmSpec("FIELD_FILL_PRIORITY_ORDER", "Order exact field-fill actions by materialization priority.", field_fill_priority_order, ("actions",), ("ordered_fill_action_ids",), "deterministic_candidate_ranking_algorithm", "field_fill_priority", "owner_template_v1", {"actions": [{"fill_action_id": "F1", "overall_materialization_priority_score": 0.4}, {"fill_action_id": "F2", "overall_materialization_priority_score": 0.9}]}),
        AlgorithmSpec("ROUTE_FILL_PRIORITY_ORDER", "Order route-fill actions by route-fill need score.", route_fill_priority_order, ("actions",), ("ordered_route_fill_action_ids",), "deterministic_candidate_ranking_algorithm", "route_fill_priority", "owner_template_v1", {"actions": [{"route_fill_action_id": "R1", "route_fill_need_score": 0.2}, {"route_fill_action_id": "R2", "route_fill_need_score": 0.7}]}),
        AlgorithmSpec("PORTFOLIO_EXPOSURE_CHECK", "Sum candidate exposures and verify whether max exposure is satisfied.", portfolio_exposure_check, ("positions", "max_exposure"), ("exposure", "within_limit_flag"), "risk_capital_sizing", "exposure_check", "owner_template_v1", {"positions": [{"exposure": 10}, {"exposure": 15}], "max_exposure": 30}),
        AlgorithmSpec("PARAMETER_RANGE_CLIPPER", "Clip a candidate parameter value into a deterministic min/max range.", parameter_range_clipper, ("value", "min_value", "max_value"), ("clipped_value",), "parameter_default_range_pack", "range_clipper", "owner_template_v1", {"value": 1.2, "min_value": 0.0, "max_value": 1.0}),
        AlgorithmSpec("COMPATIBILITY_THRESHOLD_FILTER", "Keep candidates with compatibility scores above a deterministic threshold.", compatibility_threshold_filter, ("candidates", "threshold"), ("compatible_ids",), "parameter_default_range_pack", "compatibility_filter", "owner_template_v1", {"threshold": 0.5, "candidates": [{"candidate_id": "A", "compatibility_score": 0.4}, {"candidate_id": "B", "compatibility_score": 0.7}]}),
        AlgorithmSpec("QUANTUM_PRIORITY_RANKER", "Rank candidates by quantum priority for batch optimizer materialization.", quantum_priority_ranker, ("candidates",), ("ranked_quantum_candidate_ids",), "quantum_bundle_selection_optimizer", "quantum_priority_ranker", "owner_template_v1", {"candidates": [{"candidate_id": "Q1", "quantum_priority_score": 0.6}, {"candidate_id": "Q2", "quantum_priority_score": 0.9}]}),
        AlgorithmSpec("FAMILY_VARIANT_NORMALIZER", "Normalize a raw mention label into deterministic domain and variant keys.", family_variant_normalizer, ("raw_label",), ("domain_family_key", "variant_key"), "deterministic_candidate_ranking_algorithm", "family_normalizer", "owner_template_v1", {"raw_label": "Technical Indicator Price Feature__RSI"}),
        AlgorithmSpec("REPLAY_PAPER_BATCH_PARTITION", "Partition candidate IDs into stable replay/paper adapter batches.", replay_paper_batch_partition, ("candidate_ids", "batch_size"), ("batches",), "deterministic_candidate_ranking_algorithm", "batch_partition", "owner_template_v1", {"candidate_ids": ["A", "B", "C"], "batch_size": 2}),
        AlgorithmSpec("CACHEABILITY_CLASSIFIER", "Classify compute tiers that can be cached or precomputed.", cacheability_classifier, ("compute_tier",), ("cacheable",), "latency_slippage_cost", "cacheability", "owner_template_v1", {"compute_tier": "TIER_1_SIMPLE_ARITHMETIC_FORMULA"}),
        AlgorithmSpec("HOT_PATH_PRECOMPUTE_SELECTOR", "Split formulations into future hot-path candidates and precompute-required candidates.", hot_path_precompute_selector, ("formulations",), ("hot_path_candidate_ids", "precompute_required_ids"), "latency_slippage_cost", "hot_path_precompute", "owner_template_v1", {"formulations": [{"formulation_id": "F1", "compute_tier": "TIER_1_SIMPLE_ARITHMETIC_FORMULA"}, {"formulation_id": "F2", "compute_tier": "TIER_4_QUANTUM_OR_HYBRID_BATCH_OPTIMIZER"}]}),
        AlgorithmSpec("FORMULA_COVERAGE_CLASSIFIER", "Count formulation-backed and unmapped formulation attempts.", formula_coverage_classifier, ("mappings",), ("formulation_backed_count", "formulation_unmapped_count"), "deterministic_candidate_ranking_algorithm", "coverage", "owner_template_v1", {"mappings": [{"formulation_ref": "F1"}, {"formulation_ref": ""}]}),
        AlgorithmSpec("EXACT_FILL_ACTION_BUILDER", "Create a deterministic exact field-fill action payload after mapping attempts fail.", exact_fill_action_builder, ("missing_field", "responsible_agent", "priority_score"), ("fill_action",), "deterministic_candidate_ranking_algorithm", "field_fill_builder", "owner_template_v1", {"missing_field": "objective", "responsible_agent": "QKU_FORMULA_COMPUTE_ENGINE", "priority_score": 0.8}),
        AlgorithmSpec("OWNER_REVIEW_ESCALATION_SELECTOR", "Select owner-review rows only after deterministic materialization attempts fail or exceed priority threshold.", owner_review_escalation_selector, ("records", "threshold"), ("owner_review_record_ids",), "deterministic_candidate_ranking_algorithm", "owner_review", "owner_template_v1", {"threshold": 0.8, "records": [{"record_id": "R1", "priority_score": 0.7}, {"record_id": "R2", "priority_score": 0.9}]}),
        AlgorithmSpec("MARKET_BUNDLE_DIVERSIFIER", "Select highest-scoring candidates while limiting one candidate per family.", market_bundle_diversifier, ("candidates",), ("diversified_candidate_ids",), "risk_capital_sizing", "diversifier", "owner_template_v1", {"candidates": [{"candidate_id": "A", "score": 0.9, "family": "F1"}, {"candidate_id": "B", "score": 0.8, "family": "F1"}, {"candidate_id": "C", "score": 0.7, "family": "F2"}]}),
        AlgorithmSpec("OBJECTIVE_CONSTRAINT_PAIRER", "Pair objective refs with constraint refs for objective/constraint/solver records.", objective_constraint_pairer, ("objective_refs", "constraint_refs"), ("objective_constraint_pairs",), "objective_constraint_solver", "objective_constraint_pairer", "owner_template_v1", {"objective_refs": ["O1", "O2"], "constraint_refs": ["C1", "C2"]}),
        AlgorithmSpec("COMPARATOR_ASSIGNMENT", "Attach a deterministic classical comparator to each quantum formulation.", comparator_assignment, ("quantum_records", "default_comparator_ref"), ("classical_comparator_assignments",), "quantum_bundle_selection_optimizer", "comparator_assignment", "owner_template_v1", {"default_comparator_ref": "CMP_DEFAULT", "quantum_records": [{"quantum_formulation_id": "Q1", "preferred_comparator_ref": "CMP_A"}, {"quantum_formulation_id": "Q2"}]}),
        AlgorithmSpec("TEST_VECTOR_SMOKE_SELECTOR", "Select deterministic smoke test vectors for validation samples.", test_vector_smoke_selector, ("test_vectors", "limit"), ("smoke_test_vector_ids",), "deterministic_candidate_ranking_algorithm", "test_vector_selector", "owner_template_v1", {"limit": 2, "test_vectors": [{"test_vector_id": "T2"}, {"test_vector_id": "T1"}]}),
        AlgorithmSpec("SCHEMA_VERSION_ROUTER", "Route candidate packet rows to a candidate schema version.", schema_version_router, ("candidate_type", "schema_version"), ("schema_route",), "deterministic_candidate_ranking_algorithm", "schema_router", "owner_template_v1", {"candidate_type": "FORMULA", "schema_version": "v1"}),
        AlgorithmSpec("PROMOTION_SEED_CLASSIFIER", "Seed future promotion state without promoting to live authority.", promotion_seed_classifier, ("replay_paper_candidate_flag", "formulation_materialization_state"), ("promotion_state_seed",), "deterministic_candidate_ranking_algorithm", "promotion_seed", "owner_template_v1", {"replay_paper_candidate_flag": True, "formulation_materialization_state": "FORMULATION_FULLY_MATERIALIZED"}),
        AlgorithmSpec("DETERMINISTIC_ARBITRATION_MERGE", "Merge candidate values in deterministic source-priority order.", deterministic_arbitration_merge, ("records",), ("merged_values",), "deterministic_candidate_ranking_algorithm", "arbitration_merge", "owner_template_v1", {"records": [{"source_priority": "1", "values": {"a": 1}}, {"source_priority": "2", "values": {"b": 2}}]}),
        AlgorithmSpec("SOURCE_LOCATOR_RANKER", "Rank source locators as candidate inputs without making them accepted facts.", source_locator_ranker, ("source_locators",), ("ranked_source_locator_ids",), "probability_calibration_edge", "source_locator_ranker", "owner_template_v1", {"source_locators": [{"source_locator_id": "S1", "source_confidence_score": 0.4}, {"source_locator_id": "S2", "source_confidence_score": 0.9}]}),
    ]


def algorithm_by_id() -> dict[str, AlgorithmSpec]:
    return {spec.algorithm_id: spec for spec in algorithm_specs()}
