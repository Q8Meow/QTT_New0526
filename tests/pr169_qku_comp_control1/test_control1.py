from __future__ import annotations

import copy
from decimal import Decimal
import importlib
import json
from pathlib import Path
import subprocess
import threading
from typing import Any, Mapping

import pytest

from qtt.computation_control import QKUComputationControlPlaneV1
from qtt.computation_control.control import (
    REGISTRY_FILE,
    REGISTRY_MANIFEST,
    ComputationControlError,
    _apply_registry_update,
    _build_snapshot,
    _compile_expansion_batch,
    _derive_registry_update,
    _index_signature,
    _load_logical_registry,
    _validate_record_shape,
    _write_registry_layout,
)
from qtt.computation_control.models import ExpansionBatchV1


def _requirement(target: str, producer: str, consumer: str, role: str) -> dict[str, Any]:
    return {
        "required_component_id_or_source_selector": target,
        "required_semantic_version_constraint": "==1.0",
        "requirement_role": role,
        "required_or_optional": "REQUIRED",
        "producer_output_name": producer,
        "consumer_input_name": consumer,
        "unit_or_basis_conversion": "IDENTITY",
        "timing_and_freshness_constraint": "SAME_REQUEST_INPUT_LOCK",
        "activation_condition": "ALWAYS",
        "fallback_component_id_or_null": None,
        "failure_behavior": "FAIL_CLOSED",
    }


def _record(
    component_id: str,
    callable_ref: str,
    inputs: list[tuple[str, str]],
    outputs: list[tuple[str, str]],
    *,
    requirements: list[dict[str, Any]] | None = None,
    memoizable: bool = True,
    record_state: str = "CANONICAL_ACCEPTED",
    binding_id: str | None = None,
) -> dict[str, Any]:
    suffix = component_id.rsplit(".", 1)[-1]
    implementation_version = "impl-1.0"
    binding_id = binding_id or f"BIND.TEST.{suffix}"
    return {
        "canonical_component_id": component_id,
        "semantic_version": "1.0",
        "record_state": record_state,
        "origin_cohorts": ["CONTROL1_TEST_FIXTURE"],
        "definition": {
            "display_name": suffix,
            "description": f"Independent CONTROL1 fixture for {suffix}",
            "component_kind": "PURE_FORMULA",
            "family_template_ref_or_null": None,
            "complete_mathematical_or_procedural_definition": f"typed procedure {suffix}",
            "objective_sense_or_null": None,
            "assumptions": ["bounded deterministic fixture"],
            "hard_constraints": [],
            "soft_preferences": [],
            "domain_and_boundary_behavior": {"invalid": "FAIL_CLOSED"},
            "state_and_time_semantics": {"state": "STATELESS", "time": "SAME_REQUEST"},
            "input_schema": [
                {"name": name, "type": "NUMBER", "unit": unit, "required": True}
                for name, unit in inputs
            ],
            "output_schema": [
                {"name": name, "type": "NUMBER", "unit": unit, "required": True}
                for name, unit in outputs
            ],
            "units_and_bases": {name: unit for name, unit in [*inputs, *outputs]},
            "output_accounting_class": "NON_ACCOUNTING_FIXTURE",
            "missing_stale_nonfinite_behavior": "FAIL_CLOSED",
            "precision_and_rounding": {"numeric": "EXACT_FIXTURE"},
            "parameter_schema_and_default_provenance": {
                "parameters": [],
                "default_provenance": "CONTROL1_TEST_FIXTURE",
            },
            "requirements": requirements or [],
            "latency_class": "PRETRADE_BOUNDED",
            "risk_materiality": "TEST_ONLY",
            "failure_domain_tags": ["TEST_ONLY"],
            "classical_fallback": {"state": "NOT_REQUIRED"},
            "quantum": {
                "applicability_state": "NOT_APPLICABLE",
                "original_economic_problem_ref": None,
                "problem_family": None,
                "formulation_candidates": [],
                "selected_formulation_or_none": None,
                "variable_encoding": None,
                "objective_map": None,
                "constraint_map": None,
                "penalty_policy": None,
                "coefficient_scaling": None,
                "precision_and_quantization": None,
                "decomposition_or_embedding": None,
                "warm_start": None,
                "optimizer_and_version": None,
                "shots_reads_or_sampling_policy": None,
                "seed_resampling_policy": None,
                "inverse_map": None,
                "original_model_feasibility_check": None,
                "same_formulation_classical_comparator": None,
                "local_exact_or_small_instance_parity": None,
                "fallback": "NOT_REQUIRED",
                "maturity_ceiling": "SPECIFIED",
            },
            "implementation_versions": [
                {
                    "implementation_version": implementation_version,
                    "callable_or_solver_ref": callable_ref,
                    "code_owner": "CONTROL1_TEST",
                    "supported_platforms": ["WINDOWS", "LINUX"],
                    "pinned_dependencies": ["PYTHON_STANDARD_LIBRARY"],
                    "determinism_seed_policy": "DETERMINISTIC_NO_SEED",
                    "precision": "FIXTURE_EXACT",
                    "latency_class": "PRETRADE_BOUNDED",
                    "security_state": "LOCAL_ALLOWLIST_ONLY",
                    "memoizable": memoizable,
                    "memoizable_proof_basis": "PURE_STATELESS_TEST_FUNCTION" if memoizable else "EXPLICITLY_DISABLED",
                    "fallback": None,
                }
            ],
            "oracle_and_test_refs": ["tests/pr169_qku_comp_control1/test_control1.py"],
            "equivalence_proof_refs": [],
        },
        "uses": {
            "decision_roles": ["INTERNAL_SUPPORT"],
            "decision_outputs": [name for name, _ in outputs],
            "market_family_tags": ["TEST"],
            "qku_role_bindings": [
                {
                    "qku_id": f"QKU.TEST.{suffix}",
                    "role_or_decision_stage": "TEST",
                    "market_family": "TEST",
                    "stack_root_or_direct_component": component_id,
                    "selection_rule_if_container": None,
                    "agent_policy_tags": ["TEST_ONLY"],
                    "source_refs": ["tests/pr169_qku_comp_control1/test_control1.py"],
                }
            ],
            "consumer_class_tags": ["TEST_CONSUMER"],
        },
        "bindings": [
            {
                "binding_id": binding_id,
                "market": "TEST",
                "venue": "LOCAL",
                "context_selector": {"market": "TEST", "venue": "LOCAL"},
                "qku_binding_selector_or_null": None,
                "supported_modes": ["STATIC_VALIDATION", "TEST_VECTOR"],
                "mode_state": {
                    "STATIC_VALIDATION": "FIXTURE_ONLY",
                    "TEST_VECTOR": "FIXTURE_ONLY",
                },
                "as_of_policy": "REQUEST_PINNED",
                "selected_implementation_version": implementation_version,
                "binding_version": "1.0",
                "selected_parameter_policy": {
                    "policy_id": "PARAM.TEST.FIXED",
                    "version": "1.0",
                    "defaults": {},
                    "default_provenance": "CONTROL1_TEST_FIXTURE",
                },
                "input_source_bindings": {name: "CALLER_TYPED_FIXTURE" for name, _ in inputs},
                "venue_semantic_version": "LOCAL.TEST.1",
                "portfolio_state_requirement": "NOT_REQUIRED",
                "cash_state_requirement": "NOT_REQUIRED",
                "freshness_and_TTL": {"policy": "REQUEST_SCOPED", "ttl_seconds": 60},
                "point_in_time_policy": "SAME_REQUEST_LOCK",
                "requirement_context_policy": "INHERIT_ROOT_CONTEXT",
                "selected_requirement_alternatives": [],
                "readiness": {
                    "specification": "PASS",
                    "implementation": "PASS",
                    "inputs": "PASS",
                    "requirements": "PASS",
                    "oracle": "PASS",
                    "context": "PASS",
                    "evidence": "FIXTURE",
                    "authorization": "NOT_ELIGIBLE",
                },
                "derived_state": "STACK_READY",
                "exact_resolution_action_or_null": None,
                "evidence_summary": {
                    "state": "FIXTURE",
                    "source_evidence_refs": ["tests/pr169_qku_comp_control1/test_control1.py"],
                    "limitations": ["No market, replay, PAPER, shadow, live, or QPU evidence"],
                },
                "agent_access_policy": {
                    "test_agent": {
                        "control_plane_operations": ["resolve", "compute", "status", "explain"],
                        "mode_ceiling": "STATIC_VALIDATION",
                    }
                },
                "fallback_policy": {"state": "FAIL_CLOSED"},
                "runtime_snapshot_ref_or_null": None,
                "activation_state": "INACTIVE",
                "rollback_target_or_null": None,
                "upstream_value_lineage": ["CALLER_TYPED_FIXTURE"],
                "downstream_consumer_classes": ["TEST_CONSUMER"],
                "producer_owner": "CONTROL1_TEST",
                "validator_refs": ["tests/pr169_qku_comp_control1/test_control1.py"],
                "terminal_disposition_or_null": None,
            }
        ],
        "provenance": [
            {
                "source_artifact_ref": "tests/pr169_qku_comp_control1/test_control1.py",
                "source_row_ref": component_id,
                "source_local_identity_or_name": suffix,
                "source_fields_consumed": ["fixture definition"],
                "source_relation": "CONTROL1_INDEPENDENT_TEST_FIXTURE",
                "canonical_target_ref": component_id,
                "proof_refs": ["tests/pr169_qku_comp_control1/test_control1.py"],
            }
        ],
        "relations": [],
        "governance": {
            "producer_owner": "CONTROL1_TEST",
            "validator_refs": ["tests/pr169_qku_comp_control1/test_control1.py"],
            "reviewer_or_challenger_owner": "CONTROL1_TEST_ORACLE",
            "change_authority": "CONTROL1_TEST_ONLY",
        },
    }


def _diamond_records(*, common_memoizable: bool = True) -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, int]]:
    calls: dict[str, int] = {"common": 0, "left": 0, "right": 0, "root": 0}

    def common(values: dict[str, Any]) -> dict[str, Any]:
        calls["common"] += 1
        return {"common": values["x"] * 2}

    def left(values: dict[str, Any]) -> dict[str, Any]:
        calls["left"] += 1
        return {"left": values["common"] + 1}

    def right(values: dict[str, Any]) -> dict[str, Any]:
        calls["right"] += 1
        return {"right": values["common"] + 2}

    def root(values: dict[str, Any]) -> dict[str, Any]:
        calls["root"] += 1
        return {"result": values["left"] + values["right"]}

    common_id = "QTT.COMP.TEST.COMMON"
    left_id = "QTT.COMP.TEST.LEFT"
    right_id = "QTT.COMP.TEST.RIGHT"
    root_id = "QTT.COMP.TEST.ROOT"
    records = [
        _record(common_id, "test:common", [("x", "UNITLESS")], [("common", "UNITLESS")], memoizable=common_memoizable),
        _record(
            left_id,
            "test:left",
            [("common", "UNITLESS")],
            [("left", "UNITLESS")],
            requirements=[_requirement(common_id, "common", "common", "COMMON_LEFT")],
        ),
        _record(
            right_id,
            "test:right",
            [("common", "UNITLESS")],
            [("right", "UNITLESS")],
            requirements=[_requirement(common_id, "common", "common", "COMMON_RIGHT")],
        ),
        _record(
            root_id,
            "test:root",
            [("left", "UNITLESS"), ("right", "UNITLESS")],
            [("result", "UNITLESS")],
            requirements=[
                _requirement(left_id, "left", "left", "LEFT_TERM"),
                _requirement(right_id, "right", "right", "RIGHT_TERM"),
            ],
        ),
    ]
    allowlist = {"test:common": common, "test:left": left, "test:right": right, "test:root": root}
    return records, allowlist, calls


def _context() -> dict[str, Any]:
    return {
        "market": "TEST",
        "venue": "LOCAL",
        "input_units": {"x": "UNITLESS"},
        "input_lineage": {"x": "FIXTURE:X"},
    }


def test_package_exports_one_runtime_object() -> None:
    package = importlib.import_module("qtt.computation_control")
    assert package.__all__ == ["QKUComputationControlPlaneV1"]


def test_requirements_compile_and_selected_subgraph_memoizes_once() -> None:
    records, allowlist, calls = _diamond_records()
    plane = QKUComputationControlPlaneV1(
        records=records,
        implementation_allowlist=allowlist,
        trusted_memoizable_refs={"test:common"},
    )
    plan = plane.resolve("QTT.COMP.TEST.ROOT", _context(), agent_id="test_agent")
    assert [node.canonical_component_id for node in plan.topological_nodes] == [
        "QTT.COMP.TEST.COMMON",
        "QTT.COMP.TEST.LEFT",
        "QTT.COMP.TEST.RIGHT",
        "QTT.COMP.TEST.ROOT",
    ]
    receipt = plane.compute(
        "QTT.COMP.TEST.ROOT",
        {"x": {"value": 3, "unit": "UNITLESS", "lineage": "FIXTURE:X"}},
        _context(),
        agent_id="test_agent",
    )
    assert receipt.outputs["result"] == 15
    assert receipt.nodes_executed == 4
    assert receipt.shared_invocations_reused == 1
    assert calls == {"common": 1, "left": 1, "right": 1, "root": 1}
    diagnostics = plane._diagnostics()
    assert diagnostics["runtime_registry_file_reads_after_initialization"] == 0
    assert diagnostics["per_request_full_registry_iterations"] == 0
    assert diagnostics["unrelated_component_executions"] == 0


def test_different_input_does_not_reuse_and_nonmemoizable_repeats() -> None:
    records, allowlist, calls = _diamond_records(common_memoizable=False)
    plane = QKUComputationControlPlaneV1(records=records, implementation_allowlist=allowlist)
    first = plane.compute("QTT.COMP.TEST.ROOT", {"x": 2}, _context())
    second = plane.compute("QTT.COMP.TEST.ROOT", {"x": 4}, _context())
    assert first.outputs["result"] == 11
    assert second.outputs["result"] == 19
    assert calls["common"] == 4
    assert first.shared_invocations_reused == 0


def test_cycle_unit_nonfinite_passthrough_and_money_defects_fail_closed() -> None:
    first = _record(
        "QTT.COMP.TEST.CYCLE_A",
        "test:a",
        [("b", "UNITLESS")],
        [("a", "UNITLESS")],
        requirements=[_requirement("QTT.COMP.TEST.CYCLE_B", "b", "b", "B")],
    )
    second = _record(
        "QTT.COMP.TEST.CYCLE_B",
        "test:b",
        [("a", "UNITLESS")],
        [("b", "UNITLESS")],
        requirements=[_requirement("QTT.COMP.TEST.CYCLE_A", "a", "a", "A")],
    )
    with pytest.raises(ValueError, match="REQUIREMENT_CYCLE"):
        QKUComputationControlPlaneV1(records=[first, second], implementation_allowlist={"test:a": lambda x: x, "test:b": lambda x: x})

    money = _record(
        "QTT.COMP.NATIVE.MONEY",
        "qtt.computation_control.native:decimal_implied_probability",
        [("price", "PRICE"), ("payout", "PRICE")],
        [("implied_probability", "PROBABILITY")],
    )
    plane = QKUComputationControlPlaneV1(records=[money])
    with pytest.raises(ComputationControlError, match="CALLER_RESULT_PASSTHROUGH"):
        plane.compute(money["canonical_component_id"], {"expected_result": 1}, _context())
    with pytest.raises(ComputationControlError, match="BINARY_FLOAT_MONEY_BOUNDARY"):
        plane.compute(
            money["canonical_component_id"],
            {
                "price": {"value": 0.4, "unit": "PRICE"},
                "payout": {"value": Decimal("1"), "unit": "PRICE"},
            },
            {"market": "TEST", "venue": "LOCAL"},
        )
    with pytest.raises(ComputationControlError, match="NONFINITE"):
        plane.compute(
            money["canonical_component_id"],
            {
                "price": {"value": Decimal("NaN"), "unit": "PRICE"},
                "payout": {"value": Decimal("1"), "unit": "PRICE"},
            },
            {"market": "TEST", "venue": "LOCAL"},
        )
    with pytest.raises(ComputationControlError, match="MISSING_UNIT"):
        plane.compute(
            money["canonical_component_id"],
            {"price": Decimal("0.4"), "payout": Decimal("1")},
            {"market": "TEST", "venue": "LOCAL"},
        )


def test_stale_typed_input_fails_closed() -> None:
    record = _record("QTT.COMP.TEST.STALE", "test:identity", [("x", "UNITLESS")], [("y", "UNITLESS")])
    plane = QKUComputationControlPlaneV1(records=[record], implementation_allowlist={"test:identity": lambda value: {"y": value["x"]}})
    with pytest.raises(ComputationControlError, match="STALE_INPUT"):
        plane.compute(
            record["canonical_component_id"],
            {"x": {"value": 1, "unit": "UNITLESS", "as_of": "2026-01-01T00:00:00Z"}},
            {
                "market": "TEST",
                "venue": "LOCAL",
                "request_time": "2026-01-01T00:02:00Z",
                "freshness_ttl_seconds": 30,
            },
        )


def test_delta_exactness_incremental_full_rebuild_parity_and_atomic_swap() -> None:
    records, allowlist, _ = _diamond_records()
    candidate = copy.deepcopy(records)
    candidate[0]["bindings"][0]["selected_parameter_policy"]["version"] = "1.1"
    delta = _derive_registry_update(records, candidate, batch_id="BATCH.TEST")
    assert delta.changed_component_ids == ("QTT.COMP.TEST.COMMON",)
    assert delta.affected_dependent_ids == (
        "QTT.COMP.TEST.LEFT",
        "QTT.COMP.TEST.RIGHT",
        "QTT.COMP.TEST.ROOT",
    )
    base = _build_snapshot(records, generation=1)
    replacement, stats = _apply_registry_update(
        base, delta, candidate, verify_full_rebuild=True
    )
    assert stats["full_rebuild_parity"] is True
    assert _index_signature(replacement.indexes) == _index_signature(_build_snapshot(candidate, generation=2).indexes)
    plane = QKUComputationControlPlaneV1(records=records, implementation_allowlist=allowlist)
    plane._replace_snapshot(candidate, delta)
    assert plane._diagnostics()["current_generation"] == 2
    with pytest.raises(ValueError, match="REGISTRY_DELTA_NOT_EXACT"):
        plane._replace_snapshot(candidate, {**delta.as_dict(), "changed_component_ids": []})


def test_in_flight_request_pins_one_complete_generation() -> None:
    started = threading.Event()
    release = threading.Event()

    def old_impl(values: dict[str, Any]) -> dict[str, Any]:
        started.set()
        assert release.wait(10)
        return {"y": values["x"] + 1}

    def new_impl(values: dict[str, Any]) -> dict[str, Any]:
        return {"y": values["x"] + 2}

    record = _record("QTT.COMP.TEST.SNAPSHOT", "test:old", [("x", "UNITLESS")], [("y", "UNITLESS")])
    candidate = copy.deepcopy(record)
    candidate["definition"]["implementation_versions"].append(
        {
            **candidate["definition"]["implementation_versions"][0],
            "implementation_version": "impl-2.0",
            "callable_or_solver_ref": "test:new",
        }
    )
    candidate["bindings"][0]["selected_implementation_version"] = "impl-2.0"
    candidate["bindings"][0]["binding_version"] = "2.0"
    plane = QKUComputationControlPlaneV1(
        records=[record], implementation_allowlist={"test:old": old_impl, "test:new": new_impl}
    )
    result: list[Any] = []

    def run_old() -> None:
        result.append(plane.compute(record["canonical_component_id"], {"x": 3}, _context()))

    thread = threading.Thread(target=run_old)
    thread.start()
    assert started.wait(10)
    delta = _derive_registry_update([record], [candidate], batch_id="BATCH.SNAPSHOT")
    plane._replace_snapshot([candidate], delta)
    release.set()
    thread.join(10)
    assert not thread.is_alive()
    assert result[0].generation == 1
    assert result[0].outputs["y"] == 4
    current = plane.compute(record["canonical_component_id"], {"x": 3}, _context())
    assert current.generation == 2
    assert current.outputs["y"] == 5


def test_single_and_sharded_layouts_are_logically_identical_and_runtime_does_not_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    record = _record(
        "QTT.COMP.NATIVE.LAYOUT_PROBABILITY_EDGE",
        "qtt.computation_control.native:decimal_probability_edge",
        [("p_model", "PROBABILITY"), ("implied_probability", "PROBABILITY")],
        [("probability_edge", "PROBABILITY")],
    )
    records = [record]
    single = tmp_path / "single"
    sharded = tmp_path / "sharded"
    _write_registry_layout(records, single, force_layout="single")
    _write_registry_layout(records, sharded, force_layout="sharded")
    single_rows, single_meta = _load_logical_registry(single)
    sharded_rows, sharded_meta = _load_logical_registry(sharded)
    assert single_rows == sharded_rows
    assert single_meta["layout"] == "SINGLE_JSONL"
    assert sharded_meta["layout"] == "DETERMINISTIC_SHARDED_JSONL"
    single_plane = QKUComputationControlPlaneV1(single)
    sharded_plane = QKUComputationControlPlaneV1(sharded)

    def forbidden_open(*args: Any, **kwargs: Any) -> Any:
        raise AssertionError("runtime reopened physical registry")

    monkeypatch.setattr(Path, "open", forbidden_open)
    typed_inputs = {
        "p_model": {"value": Decimal("0.70"), "unit": "PROBABILITY"},
        "implied_probability": {
            "value": Decimal("0.45"),
            "unit": "PROBABILITY",
        },
    }
    context = {"market": "TEST", "venue": "LOCAL"}
    single_receipt = single_plane.compute(record["canonical_component_id"], typed_inputs, context)
    sharded_receipt = sharded_plane.compute(record["canonical_component_id"], typed_inputs, context)
    assert single_receipt.outputs == sharded_receipt.outputs == {
        "probability_edge": Decimal("0.25")
    }
    assert single_plane._diagnostics()["runtime_registry_file_reads_after_initialization"] == 0
    assert sharded_plane._diagnostics()["runtime_registry_file_reads_after_initialization"] == 0


def test_two_layouts_and_embedded_bulk_evidence_are_rejected(tmp_path: Path) -> None:
    record = _record("QTT.COMP.TEST.LAYOUT", "test:layout", [], [("y", "UNITLESS")])
    _write_registry_layout([record], tmp_path, force_layout="single")
    (tmp_path / REGISTRY_MANIFEST).write_text(
        json.dumps(
            {
                "registry_schema_version": "1.0",
                "layout": "DETERMINISTIC_SHARDED_JSONL",
                "partition_policy": {"kind": "TEST"},
                "row_count": 0,
                "partitions": [],
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="TWO_ACTIVE_REGISTRY_LAYOUTS"):
        _load_logical_registry(tmp_path)
    bulk = copy.deepcopy(record)
    bulk["bindings"][0]["evidence_summary"]["replay_history"] = [1]
    with pytest.raises(ValueError, match="EMBEDDED_BULK_EVIDENCE"):
        _validate_record_shape(bulk)


def test_expansion_compiler_executes_build_owned_proof_and_is_idempotent() -> None:
    base = _record("QTT.COMP.TEST.CANONICAL", "test:canonical", [("x", "UNITLESS")], [("y", "UNITLESS")])
    duplicate = copy.deepcopy(base)
    duplicate["canonical_component_id"] = "QTT.COMP.TEST.ALIAS_CANDIDATE"
    duplicate["uses"]["qku_role_bindings"][0]["stack_root_or_direct_component"] = duplicate["canonical_component_id"]
    duplicate["provenance"][0]["source_row_ref"] = "DUPLICATE_SOURCE"
    duplicate["provenance"][0]["canonical_target_ref"] = duplicate["canonical_component_id"]
    batch = ExpansionBatchV1(
        batch_id="BATCH.REUSE",
        batch_origin="CONTROL1_TEST_FIXTURE",
        submitted_by="CONTROL1_CENTRAL_BUILDER",
        submission_time="2026-07-14T00:00:00Z",
        source_refs=("tests/pr169_qku_comp_control1/test_control1.py",),
        source_classification="OWNER_SUBMITTED",
        intended_market_venue_modes=(),
        items=(
            {
                "record": duplicate,
                "equivalence_decision": "YES",
                "equivalence_proof_refs": ["DIRECT_DIFFERENTIAL_TEST::CANONICAL"],
                "equivalence_proof_evidence": [
                    {
                        "method": "FIXED_SEED_DIFFERENTIAL",
                        "independent_oracle_ref": "DIRECT_DIFFERENTIAL_TEST::CANONICAL",
                        "result": "PASS",
                        "units_domains_boundaries_state_time_requirements_checked": True,
                    }
                ],
                "trusted_proof_result_id": "TRUSTED.PROOF.CANONICAL",
                "candidate_alias": "ALIAS_CANDIDATE",
            },
        ),
        requested_evidence_modes=("FIXTURE",),
        requested_promotion_ceiling="SPECIFIED",
    )
    candidate, delta, report = _compile_expansion_batch([base], batch)
    assert len(candidate) == 1
    assert report["outcomes"][0]["decision"] == "REUSED"
    assert delta.changed_component_ids == (base["canonical_component_id"],)
    same, second_delta, _ = _compile_expansion_batch(candidate, batch)
    assert same == candidate
    assert not second_delta.added_component_ids
    assert not second_delta.changed_component_ids
    forged = copy.deepcopy(batch.as_dict())
    forged["batch_id"] = "BATCH.FORGED.PROOF"
    forged["requested_promotion_ceiling"] = "STACK_READY"
    forged["items"][0]["record"]["definition"][
        "complete_mathematical_or_procedural_definition"
    ] = "different semantics despite caller-authored PASS fields"
    forged["items"][0]["trusted_proof_result_id"] = "CALLER.FABRICATED.PASS"
    with pytest.raises(ValueError, match="UNPROVEN_EQUIVALENCE"):
        _compile_expansion_batch([base], forged)


@pytest.mark.parametrize(
    ("defect", "error"),
    [
        ("overlapping_binding_selectors", "OVERLAPPING_BINDING_SELECTORS"),
        ("missing_supported_mode_state", "MODE_STATE_COVERAGE_MISSING"),
        ("unknown_component_kind", "COMPONENT_KIND"),
        ("unknown_decision_role", "DECISION_ROLE"),
        ("unknown_requirement_optionality", "REQUIREMENT.*OPTIONAL"),
        ("forbidden_quantum_maturity", "QUANTUM.*MATURITY"),
        ("forbidden_quantum_claim", "QUANTUM.*CLAIM|QPU.*EXECUTION"),
        ("oversized_generic_evidence", "EMBEDDED_BULK_EVIDENCE"),
    ],
)
def test_admission_rejects_closed_world_and_compactness_defects(
    defect: str, error: str
) -> None:
    record = _record(
        "QTT.COMP.TEST.ADMISSION",
        "test:admission",
        [("x", "UNITLESS")],
        [("y", "UNITLESS")],
    )
    if defect == "overlapping_binding_selectors":
        overlapping = copy.deepcopy(record["bindings"][0])
        overlapping["binding_id"] = "BIND.TEST.ADMISSION.OVERLAP"
        overlapping["market"] = "ANY"
        overlapping["context_selector"] = {"market": "ANY", "venue": "LOCAL"}
        record["bindings"].append(overlapping)
    elif defect == "missing_supported_mode_state":
        record["bindings"][0]["mode_state"].pop("TEST_VECTOR")
    elif defect == "unknown_component_kind":
        record["definition"]["component_kind"] = "MAGICAL_UNREVIEWED_COMPUTATION"
    elif defect == "unknown_decision_role":
        record["uses"]["decision_roles"] = ["UNDECLARED_DECISION_AUTHORITY"]
    elif defect == "unknown_requirement_optionality":
        requirement = _requirement(
            "QTT.COMP.TEST.UPSTREAM", "upstream", "x", "ADMISSION_INPUT"
        )
        requirement["required_or_optional"] = "SOMETIMES"
        record["definition"]["requirements"] = [requirement]
    elif defect == "forbidden_quantum_maturity":
        record["definition"]["quantum"]["maturity_ceiling"] = "TRUE_QPU_EXECUTED"
    elif defect == "forbidden_quantum_claim":
        record["definition"]["quantum"].update(
            {"backend_execution": True, "quantum_advantage_claim": True}
        )
    elif defect == "oversized_generic_evidence":
        record["bindings"][0]["evidence_summary"]["bounded_note"] = "x" * 65_000
    else:  # pragma: no cover - the parameter table is closed above
        raise AssertionError(defect)
    with pytest.raises(ValueError, match=error):
        _validate_record_shape(record)


def test_snapshot_update_rejects_accepted_deletion_and_same_version_mutation() -> None:
    record = _record(
        "QTT.COMP.TEST.IMMUTABLE",
        "test:immutable",
        [("x", "UNITLESS")],
        [("y", "UNITLESS")],
    )
    plane = QKUComputationControlPlaneV1(
        records=[record],
        implementation_allowlist={"test:immutable": lambda values: {"y": values["x"]}},
    )

    deletion_delta = _derive_registry_update(
        [record], [], batch_id="BATCH.ACCEPTED.DELETION"
    )
    with pytest.raises(ValueError, match="ACCEPTED.*DELETION|DELETE.*ACCEPTED"):
        plane._replace_snapshot([], deletion_delta)

    mutated = copy.deepcopy(record)
    mutated["definition"]["complete_mathematical_or_procedural_definition"] = (
        "materially different same-version procedure"
    )
    mutation_delta = _derive_registry_update(
        [record], [mutated], batch_id="BATCH.SAME.VERSION.MUTATION"
    )
    with pytest.raises(ValueError, match="MATERIAL_DEFINITION_CHANGE_REQUIRES_SUCCESSOR"):
        plane._replace_snapshot([mutated], mutation_delta)

    demoted = copy.deepcopy(record)
    demoted["record_state"] = "PROVISIONAL"
    demotion_delta = _derive_registry_update(
        [record], [demoted], batch_id="BATCH.ACCEPTED.DEMOTION"
    )
    with pytest.raises(ValueError, match="ACCEPTED_RECORD_STATE_DEMOTION_FORBIDDEN"):
        plane._replace_snapshot([demoted], demotion_delta)

    authority_grant = copy.deepcopy(record)
    authority_grant["bindings"][0]["readiness"]["authorization"] = "AUTHORIZED"
    authority_grant["bindings"][0]["activation_state"] = "ACTIVE"
    authority_delta = _derive_registry_update(
        [record], [authority_grant], batch_id="BATCH.AUTHORITY.GRANT"
    )
    with pytest.raises(ValueError, match="BINDING_AUTHORITY_CHANGE_FORBIDDEN"):
        plane._replace_snapshot([authority_grant], authority_delta)


def test_status_reports_noneligible_mode_blockers_without_raising() -> None:
    record = _record(
        "QTT.COMP.TEST.STATUS_BLOCKERS",
        "test:status_blockers",
        [("x", "UNITLESS")],
        [("y", "UNITLESS")],
    )
    binding = record["bindings"][0]
    binding["supported_modes"].append("PAPER")
    binding["mode_state"]["PAPER"] = {
        "eligibility": "NOT_ELIGIBLE",
        "authorization": "NOT_AUTHORIZED",
    }
    plane = QKUComputationControlPlaneV1(
        records=[record],
        implementation_allowlist={
            "test:status_blockers": lambda values: {"y": values["x"]}
        },
    )
    status = plane.status(
        record["canonical_component_id"],
        {"market": "TEST", "venue": "LOCAL", "mode": "PAPER"},
    )
    assert any("MODE_STATE_NOT_ELIGIBLE: PAPER" in value for value in status["blockers"])
    assert any("MODE_NOT_AUTHORIZED: PAPER" in value for value in status["blockers"])


@pytest.mark.parametrize(
    ("value", "error"),
    [
        (-1, "MINIMUM|BELOW_MIN"),
        (11, "MAXIMUM|ABOVE_MAX"),
        (7, "ENUM|ALLOWED_VALUE"),
    ],
)
def test_compute_enforces_schema_bounds_and_enum(value: int, error: str) -> None:
    record = _record(
        "QTT.COMP.TEST.SCHEMA_CONSTRAINTS",
        "test:schema_constraints",
        [("x", "UNITLESS")],
        [("y", "UNITLESS")],
    )
    record["definition"]["input_schema"][0].update(
        {"minimum": 0, "maximum": 10, "enum": [0, 5, 10]}
    )
    plane = QKUComputationControlPlaneV1(
        records=[record],
        implementation_allowlist={
            "test:schema_constraints": lambda values: {"y": values["x"]}
        },
    )
    with pytest.raises(ComputationControlError, match=error):
        plane.compute(record["canonical_component_id"], {"x": value}, _context())


def test_compute_rejects_unknown_input_and_out_of_range_parameter_default() -> None:
    record = _record(
        "QTT.COMP.TEST.INPUT_CONTRACT",
        "test:input_contract",
        [("x", "UNITLESS")],
        [("y", "UNITLESS")],
    )
    record["definition"]["input_schema"][0].update({"minimum": 0, "maximum": 10})
    plane = QKUComputationControlPlaneV1(
        records=[record],
        implementation_allowlist={
            "test:input_contract": lambda values: {"y": values["x"]}
        },
    )
    with pytest.raises(
        ComputationControlError, match="UNDECLARED_INPUT|UNKNOWN_INPUT|EXTRA_INPUT"
    ):
        plane.compute(
            record["canonical_component_id"],
            {"x": 5, "caller_injected": 99},
            _context(),
        )

    defaulted = copy.deepcopy(record)
    defaulted["definition"]["parameter_schema_and_default_provenance"][
        "parameters"
    ] = [
        {
            "name": "x",
            "type": "NUMBER",
            "unit": "UNITLESS",
            "minimum": 0,
            "maximum": 10,
            "default_provenance": "CONTROL1_TEST_FIXTURE",
        }
    ]
    defaulted["bindings"][0]["selected_parameter_policy"]["defaults"] = {"x": 11}
    with pytest.raises(ComputationControlError, match="MAXIMUM|ABOVE_MAX"):
        QKUComputationControlPlaneV1(
            records=[defaulted],
            implementation_allowlist={
                "test:input_contract": lambda values: {"y": values["x"]}
            },
        )


def test_runtime_fallback_executes_only_after_primary_failure() -> None:
    calls = {"primary": 0, "fallback": 0}

    def failing_primary(values: dict[str, Any]) -> dict[str, Any]:
        calls["primary"] += 1
        raise RuntimeError("injected primary failure")

    def successful_primary(values: dict[str, Any]) -> dict[str, Any]:
        calls["primary"] += 1
        return {"y": values["x"] + 1}

    def fallback(values: dict[str, Any]) -> dict[str, Any]:
        calls["fallback"] += 1
        return {"y": values["x"] + 10}

    primary = _record(
        "QTT.COMP.TEST.PRIMARY",
        "test:primary",
        [("x", "UNITLESS")],
        [("y", "UNITLESS")],
    )
    fallback_record = _record(
        "QTT.COMP.TEST.FALLBACK",
        "test:fallback",
        [("x", "UNITLESS")],
        [("y", "UNITLESS")],
    )
    primary["bindings"][0]["fallback_policy"] = {
        "state": "USE_FALLBACK",
        "behavior": "USE_FALLBACK",
        "component_id": fallback_record["canonical_component_id"],
        "fallback_component_id": fallback_record["canonical_component_id"],
    }
    plane = QKUComputationControlPlaneV1(
        records=[primary, fallback_record],
        implementation_allowlist={
            "test:primary": failing_primary,
            "test:fallback": fallback,
        },
    )
    receipt = plane.compute(primary["canonical_component_id"], {"x": 2}, _context())
    assert receipt.outputs["y"] == 12
    assert receipt.fallback_used is True
    assert calls == {"primary": 1, "fallback": 1}

    calls.update(primary=0, fallback=0)
    success_plane = QKUComputationControlPlaneV1(
        records=[primary, fallback_record],
        implementation_allowlist={
            "test:primary": successful_primary,
            "test:fallback": fallback,
        },
    )
    success = success_plane.compute(
        primary["canonical_component_id"], {"x": 2}, _context()
    )
    assert success.outputs["y"] == 3
    assert success.fallback_used is False
    assert calls == {"primary": 1, "fallback": 0}


def test_expansion_submitter_and_equivalence_result_are_not_self_attested() -> None:
    base = _record(
        "QTT.COMP.TEST.TRUSTED_CANONICAL",
        "test:trusted_canonical",
        [("x", "UNITLESS")],
        [("y", "UNITLESS")],
    )
    duplicate = copy.deepcopy(base)
    duplicate_id = "QTT.COMP.TEST.SELF_AUTHORED_CANDIDATE"
    duplicate["canonical_component_id"] = duplicate_id
    duplicate["uses"]["qku_role_bindings"][0][
        "stack_root_or_direct_component"
    ] = duplicate_id
    duplicate["provenance"][0]["source_row_ref"] = duplicate_id
    duplicate["provenance"][0]["canonical_target_ref"] = duplicate_id
    proof_result_id = "TRUSTED.PROOF.SELF_AUTHORED_CANDIDATE"
    proof_ref = "tests/pr169_qku_comp_control1/test_control1.py::independent_trusted_proof"
    batch = {
        "batch_id": "BATCH.TRUSTED.PROOF",
        "batch_origin": "CONTROL1_TEST_FIXTURE",
        "submitted_by": "SELF_AUTHORED_CANDIDATE",
        "submission_time": "2026-07-14T00:00:00Z",
        "source_refs": ["tests/pr169_qku_comp_control1/test_control1.py"],
        "source_classification": "OWNER_SUBMITTED",
        "intended_market_venue_modes": [],
        "items": [
            {
                "record": duplicate,
                "equivalence_decision": "YES",
                "equivalence_proof_refs": [proof_ref],
                "equivalence_proof_evidence": [
                    {
                        "proof_result_id": proof_result_id,
                        "method": "FIXED_SEED_DIFFERENTIAL",
                        "independent_oracle_ref": proof_ref,
                        "result": "PASS",
                        "units_domains_boundaries_state_time_requirements_checked": True,
                    }
                ],
                "trusted_proof_result_id": proof_result_id,
                "candidate_alias": "SELF_AUTHORED_CANDIDATE",
            }
        ],
        "requested_evidence_modes": ["FIXTURE"],
        "requested_promotion_ceiling": "NOT_ELIGIBLE",
    }
    with pytest.raises(ValueError, match="UNTRUSTED_EXPANSION_SUBMITTER"):
        _compile_expansion_batch([base], batch)

    forged = copy.deepcopy(batch)
    forged["submitted_by"] = "CONTROL1_CENTRAL_BUILDER"
    forged["requested_promotion_ceiling"] = "STACK_READY"
    forged["items"][0]["record"]["definition"][
        "complete_mathematical_or_procedural_definition"
    ] = "attacker-selected nonidentical semantics"
    with pytest.raises(ValueError, match="UNPROVEN_EQUIVALENCE"):
        _compile_expansion_batch([base], forged)


def test_nonfixture_compute_requires_agent_or_declared_consumer() -> None:
    record = _record(
        "QTT.COMP.TEST.NONFIXTURE_IDENTITY",
        "test:nonfixture_identity",
        [("x", "UNITLESS")],
        [("y", "UNITLESS")],
    )
    binding = record["bindings"][0]
    binding["supported_modes"].append("PAPER")
    binding["mode_state"]["PAPER"] = {
        "eligibility": "ELIGIBLE",
        "authorization": "AUTHORIZED",
    }
    binding["readiness"]["authorization"] = "AUTHORIZED"
    binding["activation_state"] = "ACTIVE"
    binding["as_of_policy"] = "TIME_INVARIANT"
    binding["point_in_time_policy"] = "TIME_INVARIANT"
    binding["agent_access_policy"]["test_agent"]["mode_ceiling"] = "PAPER"
    plane = QKUComputationControlPlaneV1(
        records=[record],
        implementation_allowlist={
            "test:nonfixture_identity": lambda values: {"y": values["x"]}
        },
    )
    context = {
        "market": "TEST",
        "venue": "LOCAL",
        "mode": "PAPER",
        "input_units": {"x": "UNITLESS"},
        "input_lineage": {"x": "CALLER_TYPED_FIXTURE"},
    }
    with pytest.raises(
        ComputationControlError,
        match="AGENT_OR_CONSUMER_REQUIRED|UNTRUSTED_CONSUMER|CALLER_IDENTITY",
    ):
        plane.compute(record["canonical_component_id"], {"x": 2}, context)

    by_consumer = plane.compute(
        record["canonical_component_id"],
        {"x": 2},
        context,
        consumer="TEST_CONSUMER",
    )
    assert by_consumer.outputs["y"] == 2
    by_agent = plane.compute(
        record["canonical_component_id"],
        {"x": 3},
        context,
        agent_id="test_agent",
    )
    assert by_agent.outputs["y"] == 3


@pytest.mark.parametrize("layout", ["single", "sharded"])
def test_synthetic_2000_record_load_and_index(layout: str, tmp_path: Path) -> None:
    active = _record("QTT.COMP.SCALE.ACTIVE", "test:scale", [], [("value", "UNITLESS")])
    records = [active]
    for index in range(1, 2_000):
        record = _record(
            f"QTT.COMP.SCALE.{index:06d}",
            "test:dormant",
            [],
            [("value", "UNITLESS")],
            record_state="DORMANT_PRESERVED",
            binding_id=f"BIND.SCALE.{index:06d}",
        )
        record["bindings"] = []
        record["terminal_disposition"] = {
            "state": "DORMANT_PRESERVED",
            "reason": "SYNTHETIC_SCALE_RECORD_NOT_RUNTIME_REACHABLE",
        }
        records.append(record)
    root = tmp_path / layout
    metadata = _write_registry_layout(records, root, force_layout=layout)
    assert metadata["row_count"] == 2_000
    loaded, _ = _load_logical_registry(root)
    snapshot = _build_snapshot(loaded, generation=1)
    assert len(snapshot.records) == 2_000
    assert snapshot.indexes.record_keys_by_id[active["canonical_component_id"]] == (
        (active["canonical_component_id"], "1.0"),
    )


def _expansion_batch(
    items: list[dict[str, Any]], ceiling: str, *, batch_id: str
) -> dict[str, Any]:
    return {
        "batch_id": batch_id,
        "batch_origin": "CONTROL1_TEST_FIXTURE",
        "submitted_by": "CONTROL1_CENTRAL_BUILDER",
        "submission_time": "2026-07-14T00:00:00Z",
        "source_refs": ["tests/pr169_qku_comp_control1/test_control1.py"],
        "source_classification": "OWNER_SUBMITTED",
        "intended_market_venue_modes": [],
        "items": items,
        "requested_evidence_modes": ["FIXTURE"],
        "requested_promotion_ceiling": ceiling,
    }


def test_expansion_ceiling_and_raw_materialization() -> None:
    ready = _record(
        "QTT.COMP.TEST.CEILING_READY",
        "test:ceiling_ready",
        [("x", "UNITLESS")],
        [("y", "UNITLESS")],
    )
    ready_item = {
        "record": ready,
        "equivalence_decision": "NO",
        "nonidentical_relation": "DISTINCT",
    }
    with pytest.raises(ValueError, match="EXPANSION_STATE_EXCEEDS_CEILING"):
        _compile_expansion_batch(
            [],
            _expansion_batch(
                [ready_item], "SPECIFIED", batch_id="BATCH.CEILING.STATE"
            ),
        )

    eligibility = copy.deepcopy(ready)
    eligibility["canonical_component_id"] = "QTT.COMP.TEST.CEILING_ELIGIBILITY"
    eligibility["record_state"] = "PROVISIONAL"
    eligibility["bindings"][0]["binding_id"] = "BIND.TEST.CEILING_ELIGIBILITY"
    eligibility["bindings"][0]["readiness"].update(
        {
            "specification": "REQUIRED",
            "implementation": "REQUIRED",
            "inputs": "REQUIRED",
            "requirements": "REQUIRED",
            "oracle": "REQUIRED",
            "context": "REQUIRED",
            "authorization": "ELIGIBLE",
        }
    )
    eligibility["bindings"][0]["exact_resolution_action_or_null"] = (
        "MISSING_INDEPENDENT_ACCEPTANCE: QTT.COMP.TEST.CEILING_ELIGIBILITY"
    )
    eligibility["provenance"][0]["canonical_target_ref"] = eligibility[
        "canonical_component_id"
    ]
    eligibility["provenance"][0]["source_row_ref"] = eligibility[
        "canonical_component_id"
    ]
    with pytest.raises(ValueError, match="EXPANSION_AUTHORIZATION_EXCEEDS_CEILING"):
        _compile_expansion_batch(
            [],
            _expansion_batch(
                [{"record": eligibility, "equivalence_decision": "INCONCLUSIVE"}],
                "NOT_ELIGIBLE",
                batch_id="BATCH.CEILING.AUTHORIZATION",
            ),
        )

    raw_item = {
        "candidate_name": "raw typed score",
        "component_kind": "PURE_FORMULA",
        "decision_roles": ["INTERNAL_SUPPORT"],
        "decision_outputs": ["score"],
        "complete_mathematical_or_procedural_definition": "score = x + 1",
        "input_schema": [
            {"name": "x", "type": "NUMBER", "unit": "UNITLESS", "required": True}
        ],
        "output_schema": [
            {"name": "score", "type": "NUMBER", "unit": "UNITLESS", "required": True}
        ],
        "units_and_bases": {"x": "UNITLESS", "score": "UNITLESS"},
        "domain_and_boundary_behavior": {"nonfinite": "FAIL_CLOSED"},
        "state_and_time_semantics": {"state": "STATELESS", "time": "SAME_REQUEST"},
    }
    raw_records, _, _ = _compile_expansion_batch(
        [],
        _expansion_batch(
            [raw_item], "NOT_ELIGIBLE", batch_id="BATCH.RAW.MATERIALIZATION"
        ),
    )
    assert raw_records[0]["canonical_component_id"] == (
        "QTT.COMP.EXPANSION.RAW_TYPED_SCORE"
    )
    assert raw_records[0]["record_state"] == "PROVISIONAL"
    assert raw_records[0]["exact_resolution_action"].startswith(
        "MISSING_CONTEXTUAL_BINDING"
    )


def test_source_selector_resolution_and_collision_are_order_independent() -> None:
    source = _record(
        "QTT.COMP.TEST.SOURCE-SELECTOR-BASE",
        "test:source_selector_base",
        [("x", "UNITLESS")],
        [("y", "UNITLESS")],
    )
    source["provenance"][0]["source_local_identity_or_name"] = "SOURCE.LOCAL.BASE"
    dependent = _record(
        "QTT.COMP.TEST.SOURCE-SELECTOR-DEPENDENT",
        "test:source_selector_dependent",
        [("y", "UNITLESS")],
        [("result", "UNITLESS")],
        requirements=[
            _requirement("SOURCE.LOCAL.BASE", "y", "y", "SOURCE_VALUE")
        ],
    )
    resolved_records, _, _ = _compile_expansion_batch(
        [source],
        _expansion_batch(
            [
                {
                    "record": dependent,
                    "equivalence_decision": "NO",
                    "nonidentical_relation": "DISTINCT",
                }
            ],
            "STACK_READY",
            batch_id="BATCH.SOURCE.SELECTOR",
        ),
    )
    resolved_dependent = next(
        value
        for value in resolved_records
        if value["canonical_component_id"] == dependent["canonical_component_id"]
    )
    assert resolved_dependent["definition"]["requirements"][0][
        "required_component_id_or_source_selector"
    ] == source["canonical_component_id"]

    first = _record(
        "QTT.COMP.TEST.SELECTOR-A",
        "test:selector_a",
        [("x", "UNITLESS")],
        [("y", "UNITLESS")],
    )
    second = _record(
        "QTT.COMP.TEST.SELECTOR-B",
        "test:selector_b",
        [("x", "UNITLESS")],
        [("y", "UNITLESS")],
    )
    items = [
        {"record": first, "source_selector_aliases": ["SOURCE.SHARED"]},
        {"record": second, "source_selector_aliases": ["SOURCE.SHARED"]},
    ]
    for ordered in (items, list(reversed(items))):
        with pytest.raises(
            ValueError, match="AMBIGUOUS_SOURCE_SELECTOR: SOURCE.SHARED"
        ):
            _compile_expansion_batch(
                [],
                _expansion_batch(
                    ordered,
                    "STACK_READY",
                    batch_id="BATCH.SELECTOR.COLLISION",
                ),
            )


def test_requirement_context_is_pinned_and_changes_safe_subgraph_reuse() -> None:
    calls = {"common": 0}

    def common(values: dict[str, Any]) -> dict[str, Any]:
        calls["common"] += 1
        return {"value": values["x"] + 1}

    common_record = _record(
        "QTT.COMP.TEST.CONTEXT_COMMON",
        "test:context_common",
        [("x", "UNITLESS")],
        [("value", "UNITLESS")],
    )
    left = _requirement(
        common_record["canonical_component_id"], "value", "left", "LEFT"
    )
    right = _requirement(
        common_record["canonical_component_id"], "value", "right", "RIGHT"
    )
    right["timing_and_freshness_constraint"] = "SAME_REQUEST_IMMUTABLE_INPUT_LOCK"
    root = _record(
        "QTT.COMP.TEST.CONTEXT_ROOT",
        "test:context_root",
        [("left", "UNITLESS"), ("right", "UNITLESS")],
        [("result", "UNITLESS")],
        requirements=[left, right],
    )
    plane = QKUComputationControlPlaneV1(
        records=[common_record, root],
        implementation_allowlist={
            "test:context_common": common,
            "test:context_root": lambda values: {
                "result": values["left"] + values["right"]
            },
        },
        trusted_memoizable_refs={"test:context_common"},
    )
    plan = plane.resolve(root["canonical_component_id"], _context())
    common_nodes = [
        node
        for node in plan.topological_nodes
        if node.canonical_component_id == common_record["canonical_component_id"]
    ]
    assert len(common_nodes) == 2
    assert {node.context["input_lock_policy"] for node in common_nodes} == {
        "REQUEST_SCOPED",
        "IMMUTABLE",
    }
    receipt = plane.compute(root["canonical_component_id"], {"x": 2}, _context())
    assert receipt.outputs["result"] == 6
    assert calls["common"] == 2
    selected_nodes = receipt.selected_versions["nodes"]
    selected_common = [
        version
        for version in selected_nodes.values()
        if version["canonical_component_id"]
        == common_record["canonical_component_id"]
    ]
    assert len(selected_common) == 2
    assert {value["context"]["input_lock_policy"] for value in selected_common} == {
        "REQUEST_SCOPED",
        "IMMUTABLE",
    }

    unresolved = copy.deepcopy(root)
    unresolved["bindings"][0]["requirement_context_policy"] = "UNRESOLVED"
    unresolved_plane = QKUComputationControlPlaneV1(
        records=[common_record, unresolved],
        implementation_allowlist={
            "test:context_common": common,
            "test:context_root": lambda values: {
                "result": values["left"] + values["right"]
            },
        },
    )
    with pytest.raises(
        ComputationControlError, match="UNRESOLVED_REQUIREMENT_CONTEXT_POLICY"
    ):
        unresolved_plane.resolve(root["canonical_component_id"], _context())


def test_quantum_maturity_cannot_be_established_by_authored_labels() -> None:
    record = _record(
        "QTT.COMP.TEST.QUANTUM_ASSERTION",
        "test:quantum_assertion",
        [("x", "UNITLESS")],
        [("y", "UNITLESS")],
    )
    record["definition"]["quantum"]["maturity_ceiling"] = "LOCAL_EXACT_PARITY"
    with pytest.raises(
        ValueError,
        match="QUANTUM_MATURITY_REQUIRES_INDEPENDENT_PROMOTION_AUTHORITY",
    ):
        _validate_record_shape(record)


def test_fallback_projects_inputs_and_pins_one_snapshot_generation() -> None:
    observed: list[tuple[str, ...]] = []
    plane_ref: dict[str, Any] = {}
    swapped = {"done": False}

    def primary(_: dict[str, Any]) -> dict[str, Any]:
        if not swapped["done"]:
            swapped["done"] = True
            plane_ref["plane"]._replace_snapshot(candidate_records, delta)
        raise RuntimeError("injected primary failure")

    def old_fallback(values: dict[str, Any]) -> dict[str, Any]:
        observed.append(tuple(sorted(values)))
        return {"y": values["x"] + 10}

    def new_fallback(values: dict[str, Any]) -> dict[str, Any]:
        observed.append(tuple(sorted(values)))
        return {"y": values["x"] + 100}

    primary_record = _record(
        "QTT.COMP.TEST.PINNED_PRIMARY",
        "test:pinned_primary",
        [("x", "UNITLESS"), ("z", "UNITLESS")],
        [("y", "UNITLESS")],
    )
    fallback_record = _record(
        "QTT.COMP.TEST.PINNED_FALLBACK",
        "test:pinned_fallback_old",
        [("x", "UNITLESS")],
        [("y", "UNITLESS")],
    )
    primary_record["bindings"][0]["fallback_policy"] = {
        "state": "USE_FALLBACK",
        "behavior": "USE_FALLBACK",
        "component_id": fallback_record["canonical_component_id"],
        "fallback_component_id": fallback_record["canonical_component_id"],
    }
    candidate_primary = copy.deepcopy(primary_record)
    candidate_fallback = copy.deepcopy(fallback_record)
    new_implementation = copy.deepcopy(
        candidate_fallback["definition"]["implementation_versions"][0]
    )
    new_implementation["implementation_version"] = "impl-2.0"
    new_implementation["callable_or_solver_ref"] = "test:pinned_fallback_new"
    candidate_fallback["definition"]["implementation_versions"].append(
        new_implementation
    )
    candidate_fallback["bindings"][0]["selected_implementation_version"] = (
        "impl-2.0"
    )
    base_records = [primary_record, fallback_record]
    candidate_records = [candidate_primary, candidate_fallback]
    delta = _derive_registry_update(
        base_records, candidate_records, batch_id="BATCH.PINNED.FALLBACK"
    )
    plane = QKUComputationControlPlaneV1(
        records=base_records,
        implementation_allowlist={
            "test:pinned_primary": primary,
            "test:pinned_fallback_old": old_fallback,
            "test:pinned_fallback_new": new_fallback,
        },
    )
    plane_ref["plane"] = plane
    first = plane.compute(
        primary_record["canonical_component_id"],
        {"x": 2, "z": {"value": 99, "unit": "UNITLESS"}},
        _context(),
    )
    second = plane.compute(
        primary_record["canonical_component_id"],
        {"x": 2, "z": {"value": 99, "unit": "UNITLESS"}},
        _context(),
    )
    assert first.outputs["y"] == 12
    assert second.outputs["y"] == 102
    assert first.generation == 1
    assert second.generation == 2
    assert observed == [("x",), ("x",)]
    assert all(
        entry.get("receipt_generation") == first.generation
        for entry in first.requirement_receipts
    )


def test_requirement_fallback_projects_failed_producer_inputs() -> None:
    observed: list[tuple[str, ...]] = []
    primary = _record(
        "QTT.COMP.TEST.REQUIREMENT_PRIMARY",
        "test:requirement_primary",
        [("x", "UNITLESS"), ("z", "UNITLESS")],
        [("y", "UNITLESS")],
    )
    fallback = _record(
        "QTT.COMP.TEST.REQUIREMENT_FALLBACK",
        "test:requirement_fallback",
        [("x", "UNITLESS")],
        [("y", "UNITLESS")],
    )
    requirement = _requirement(
        primary["canonical_component_id"], "y", "y", "PRIMARY_VALUE"
    )
    requirement["failure_behavior"] = "USE_FALLBACK_FAIL_CLOSED"
    requirement["fallback_component_id_or_null"] = fallback[
        "canonical_component_id"
    ]
    root = _record(
        "QTT.COMP.TEST.REQUIREMENT_FALLBACK_ROOT",
        "test:requirement_fallback_root",
        [("y", "UNITLESS")],
        [("result", "UNITLESS")],
        requirements=[requirement],
    )

    def failing(_: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError("injected")

    def fallback_impl(values: dict[str, Any]) -> dict[str, Any]:
        observed.append(tuple(sorted(values)))
        return {"y": values["x"] + 10}

    plane = QKUComputationControlPlaneV1(
        records=[primary, fallback, root],
        implementation_allowlist={
            "test:requirement_primary": failing,
            "test:requirement_fallback": fallback_impl,
            "test:requirement_fallback_root": lambda values: {
                "result": values["y"]
            },
        },
    )
    receipt = plane.compute(
        root["canonical_component_id"],
        {"x": 2, "z": {"value": 99, "unit": "UNITLESS"}},
        _context(),
    )
    assert receipt.outputs["result"] == 12
    assert observed == [("x",)]


def test_nonfixture_mode_requires_exact_mode_authorization_and_no_escalation() -> None:
    record = _record(
        "QTT.COMP.TEST.MODE_AUTHORIZATION",
        "test:mode_authorization",
        [("x", "UNITLESS")],
        [("y", "UNITLESS")],
    )
    binding = record["bindings"][0]
    binding["supported_modes"].append("LIVE")
    binding["mode_state"]["LIVE"] = "FIXTURE_ONLY"
    binding["readiness"]["evidence"] = "REPLAY"
    binding["readiness"]["authorization"] = "AUTHORIZED"
    binding["activation_state"] = "ACTIVE"
    plane = QKUComputationControlPlaneV1(
        records=[record],
        implementation_allowlist={
            "test:mode_authorization": lambda values: {"y": values["x"] + 1}
        },
    )
    live_context = {"market": "TEST", "venue": "LOCAL", "mode": "LIVE"}
    plan = plane.resolve(record["canonical_component_id"], live_context)
    assert any("MODE_STATE_NOT_AUTHORIZED" in value for value in plan.blockers)
    with pytest.raises(ComputationControlError, match="PLAN_NOT_READY"):
        plane.compute(
            record["canonical_component_id"],
            {"x": 1},
            live_context,
            consumer="TEST_CONSUMER",
        )

    producer = _record(
        "QTT.COMP.TEST.MODE_ESCALATION_PRODUCER",
        "test:mode_escalation_producer",
        [("x", "UNITLESS")],
        [("y", "UNITLESS")],
    )
    producer_binding = producer["bindings"][0]
    producer_binding["supported_modes"].append("PAPER")
    producer_binding["mode_state"]["PAPER"] = {"authorization": "AUTHORIZED"}
    producer_binding["readiness"]["evidence"] = "PAPER"
    producer_binding["readiness"]["authorization"] = "AUTHORIZED"
    producer_binding["activation_state"] = "ACTIVE"
    requirement = _requirement(
        producer["canonical_component_id"], "y", "y", "ESCALATED_VALUE"
    )
    root = _record(
        "QTT.COMP.TEST.MODE_ESCALATION_ROOT",
        "test:mode_escalation_root",
        [("y", "UNITLESS")],
        [("result", "UNITLESS")],
        requirements=[requirement],
    )
    root["bindings"][0]["requirement_context_policy"] = {
        "inherit_root_context": True,
        "overrides": {"mode": "PAPER"},
    }
    escalation_plane = QKUComputationControlPlaneV1(
        records=[producer, root],
        implementation_allowlist={
            "test:mode_escalation_producer": lambda values: {"y": values["x"]},
            "test:mode_escalation_root": lambda values: {"result": values["y"]},
        },
    )
    with pytest.raises(
        ComputationControlError, match="REQUIREMENT_CONTEXT_MODE_ESCALATION"
    ):
        escalation_plane.resolve(root["canonical_component_id"], _context())


def test_reuse_blocks_unverified_new_implementation() -> None:
    base = _record(
        "QTT.COMP.TEST.IMPLEMENTATION_CANONICAL",
        "test:implementation_good",
        [("x", "UNITLESS")],
        [("y", "UNITLESS")],
    )
    candidate = copy.deepcopy(base)
    candidate_id = "QTT.COMP.TEST.IMPLEMENTATION_ALIAS"
    candidate["canonical_component_id"] = candidate_id
    candidate["uses"]["qku_role_bindings"][0][
        "stack_root_or_direct_component"
    ] = candidate_id
    candidate["provenance"][0]["canonical_target_ref"] = candidate_id
    candidate["definition"]["implementation_versions"][0].update(
        {
            "implementation_version": "impl-unverified",
            "callable_or_solver_ref": "test:implementation_bad",
        }
    )
    candidate["bindings"][0].update(
        {
            "binding_id": "BIND.TEST.IMPLEMENTATION_ALIAS",
            "market": "UNVERIFIED",
            "context_selector": {"market": "UNVERIFIED", "venue": "LOCAL"},
            "selected_implementation_version": "impl-unverified",
        }
    )
    with pytest.raises(
        ValueError,
        match="NEW_REUSED_IMPLEMENTATION_REQUIRES_BUILD_OWNED_VERIFIER",
    ):
        _compile_expansion_batch(
            [base],
            _expansion_batch(
                [
                    {
                        "record": candidate,
                        "equivalence_decision": "YES",
                        "candidate_alias": "IMPLEMENTATION_ALIAS",
                    }
                ],
                "STACK_READY",
                batch_id="BATCH.UNVERIFIED.IMPLEMENTATION",
            ),
        )

    no_implementation = copy.deepcopy(base)
    no_implementation["canonical_component_id"] = (
        "QTT.COMP.TEST.NO_IMPLEMENTATION_CANONICAL"
    )
    no_implementation["definition"]["implementation_versions"] = []
    no_implementation["bindings"][0]["selected_implementation_version"] = None
    no_implementation["bindings"][0]["readiness"]["implementation"] = "REQUIRED"
    no_implementation["bindings"][0]["exact_resolution_action_or_null"] = (
        "MISSING_IMPLEMENTATION: QTT.COMP.TEST.NO_IMPLEMENTATION_CANONICAL"
    )
    no_implementation["uses"]["qku_role_bindings"][0][
        "stack_root_or_direct_component"
    ] = no_implementation["canonical_component_id"]
    no_implementation["provenance"][0]["canonical_target_ref"] = (
        no_implementation["canonical_component_id"]
    )
    duplicate = copy.deepcopy(no_implementation)
    duplicate["canonical_component_id"] = "QTT.COMP.TEST.NO_IMPLEMENTATION_ALIAS"
    duplicate["uses"]["qku_role_bindings"][0][
        "stack_root_or_direct_component"
    ] = duplicate["canonical_component_id"]
    duplicate["provenance"][0]["canonical_target_ref"] = duplicate[
        "canonical_component_id"
    ]
    reused, _, reused_report = _compile_expansion_batch(
        [no_implementation],
        _expansion_batch(
            [{"record": duplicate, "equivalence_decision": "YES"}],
            "SPECIFIED",
            batch_id="BATCH.NO.IMPLEMENTATION.REUSE",
        ),
    )
    assert len(reused) == 1
    assert reused_report["outcomes"][0]["decision"] == "REUSED"

    qku_proposal = copy.deepcopy(base)
    qku_proposal["uses"]["qku_role_bindings"].append(
        {
            "qku_id": "QKU-UNVERIFIED-ROLE-PROPOSAL",
            "role_or_decision_stage": "INTERNAL_SUPPORT",
            "market_family": "TEST",
            "stack_root_or_direct_component": base["canonical_component_id"],
            "selection_rule_if_container": None,
            "agent_policy_tags": ["VALIDATOR_ONLY"],
            "source_refs": ["UNVERIFIED_CALLER_METADATA"],
        }
    )
    with pytest.raises(
        ValueError,
        match="NEW_REUSED_QKU_ROLE_REQUIRES_BUILD_OWNED_VERIFIER",
    ):
        _compile_expansion_batch(
            [base],
            _expansion_batch(
                [{"record": qku_proposal}],
                "STACK_READY",
                batch_id="BATCH.UNVERIFIED.QKU.ROLE",
            ),
        )


def test_identical_requirement_fallback_is_computed_once_per_call() -> None:
    calls = {"primary": 0, "fallback": 0}

    def primary(_: dict[str, Any]) -> dict[str, Any]:
        calls["primary"] += 1
        raise RuntimeError("injected primary failure")

    def fallback_impl(values: dict[str, Any]) -> dict[str, Any]:
        calls["fallback"] += 1
        return {"value": values["x"] + 10}

    primary_record = _record(
        "QTT.COMP.TEST.SHARED_FAILED_PRIMARY",
        "test:shared_failed_primary",
        [("x", "UNITLESS")],
        [("value", "UNITLESS")],
    )
    fallback_record = _record(
        "QTT.COMP.TEST.SHARED_RUNTIME_FALLBACK",
        "test:shared_runtime_fallback",
        [("x", "UNITLESS")],
        [("value", "UNITLESS")],
    )
    left = _requirement(
        primary_record["canonical_component_id"], "value", "left", "LEFT"
    )
    right = _requirement(
        primary_record["canonical_component_id"], "value", "right", "RIGHT"
    )
    for requirement in (left, right):
        requirement["failure_behavior"] = "USE_FALLBACK_FAIL_CLOSED"
        requirement["fallback_component_id_or_null"] = fallback_record[
            "canonical_component_id"
        ]
    root = _record(
        "QTT.COMP.TEST.SHARED_FALLBACK_ROOT",
        "test:shared_fallback_root",
        [("left", "UNITLESS"), ("right", "UNITLESS")],
        [("result", "UNITLESS")],
        requirements=[left, right],
    )
    plane = QKUComputationControlPlaneV1(
        records=[primary_record, fallback_record, root],
        implementation_allowlist={
            "test:shared_failed_primary": primary,
            "test:shared_runtime_fallback": fallback_impl,
            "test:shared_fallback_root": lambda values: {
                "result": values["left"] + values["right"]
            },
        },
        trusted_memoizable_refs={
            "test:shared_failed_primary",
            "test:shared_runtime_fallback",
        },
    )
    receipt = plane.compute(root["canonical_component_id"], {"x": 1}, _context())
    assert receipt.outputs["result"] == 22
    assert calls == {"primary": 1, "fallback": 1}
    fallback_refs = [
        value["receipt_ref"]
        for value in receipt.requirement_receipts
        if value.get("runtime_fallback_for_node_id")
    ]
    assert len(fallback_refs) == 2
    assert len(set(fallback_refs)) == 1


def test_fallback_edges_propagate_registry_delta_dependents() -> None:
    primary = _record(
        "QTT.COMP.TEST.DELTA_PRIMARY",
        "test:delta_primary",
        [("x", "UNITLESS")],
        [("value", "UNITLESS")],
    )
    fallback = _record(
        "QTT.COMP.TEST.DELTA_FALLBACK",
        "test:delta_fallback",
        [("x", "UNITLESS")],
        [("value", "UNITLESS")],
    )
    requirement = _requirement(
        primary["canonical_component_id"], "value", "value", "PRIMARY"
    )
    requirement["failure_behavior"] = "USE_FALLBACK"
    requirement["fallback_component_id_or_null"] = fallback[
        "canonical_component_id"
    ]
    requirement_consumer = _record(
        "QTT.COMP.TEST.DELTA_REQUIREMENT_CONSUMER",
        "test:delta_requirement_consumer",
        [("value", "UNITLESS")],
        [("result", "UNITLESS")],
        requirements=[requirement],
    )
    binding_consumer = _record(
        "QTT.COMP.TEST.DELTA_BINDING_CONSUMER",
        "test:delta_binding_consumer",
        [("x", "UNITLESS")],
        [("value", "UNITLESS")],
    )
    binding_consumer["bindings"][0]["fallback_policy"] = {
        "behavior": "USE_FALLBACK_FAIL_CLOSED",
        "fallback_component_id": fallback["canonical_component_id"],
    }
    changed_fallback = copy.deepcopy(fallback)
    changed_fallback["definition"]["description"] += " changed implementation note"
    base_records = [primary, fallback, requirement_consumer, binding_consumer]
    candidate_records = [
        primary,
        changed_fallback,
        requirement_consumer,
        binding_consumer,
    ]
    delta = _derive_registry_update(base_records, candidate_records)
    assert set(delta.affected_dependent_ids) == {
        requirement_consumer["canonical_component_id"],
        binding_consumer["canonical_component_id"],
    }
    snapshot = _build_snapshot(base_records, generation=1)
    _, stats = _apply_registry_update(
        snapshot, delta, candidate_records, verify_full_rebuild=True
    )
    assert stats["full_rebuild_parity"] is True


def test_receipt_explanation_enforces_pinned_agent_policy() -> None:
    record = _record(
        "QTT.COMP.TEST.RECEIPT_POLICY",
        "test:receipt_policy",
        [("x", "UNITLESS")],
        [("y", "UNITLESS")],
    )
    plane = QKUComputationControlPlaneV1(
        records=[record],
        implementation_allowlist={
            "test:receipt_policy": lambda values: {"y": values["x"]}
        },
    )
    receipt = plane.compute(record["canonical_component_id"], {"x": 1}, _context())
    with pytest.raises(ComputationControlError, match="AGENT_ACCESS_DENIED"):
        plane.explain(receipt, agent_id="denied_agent")
    explanation = plane.explain(receipt, agent_id="test_agent")
    assert explanation["outputs_unchanged"] == {"y": 1}


def test_unready_binding_fallback_blocks_plan_before_primary_execution() -> None:
    calls = {"primary": 0}

    def primary(_: dict[str, Any]) -> dict[str, Any]:
        calls["primary"] += 1
        raise RuntimeError("must not execute with an unready fallback")

    primary_record = _record(
        "QTT.COMP.TEST.UNREADY_FALLBACK_PRIMARY",
        "test:unready_fallback_primary",
        [("x", "UNITLESS")],
        [("y", "UNITLESS")],
    )
    fallback_record = _record(
        "QTT.COMP.TEST.UNREADY_FALLBACK",
        "test:unready_fallback",
        [("x", "UNITLESS")],
        [("y", "UNITLESS")],
        record_state="PROVISIONAL",
    )
    fallback_record["bindings"][0]["readiness"]["implementation"] = "REQUIRED"
    fallback_record["bindings"][0]["exact_resolution_action_or_null"] = (
        "MISSING_IMPLEMENTATION: QTT.COMP.TEST.UNREADY_FALLBACK"
    )
    primary_record["bindings"][0]["fallback_policy"] = {
        "behavior": "USE_FALLBACK_FAIL_CLOSED",
        "fallback_component_id": fallback_record["canonical_component_id"],
    }
    plane = QKUComputationControlPlaneV1(
        records=[primary_record, fallback_record],
        implementation_allowlist={
            "test:unready_fallback_primary": primary,
            "test:unready_fallback": lambda values: {"y": values["x"]},
        },
    )
    plan = plane.resolve(primary_record["canonical_component_id"], _context())
    assert plan.ready is False
    assert any("FALLBACK_NOT_READY" in value for value in plan.blockers)
    with pytest.raises(ComputationControlError, match="PLAN_NOT_READY"):
        plane.compute(primary_record["canonical_component_id"], {"x": 1}, _context())
    assert calls["primary"] == 0


def test_all_terminal_record_states_cannot_reactivate_in_place() -> None:
    for terminal_state in ("REJECTED_INVALID", "INAPPLICABLE_WITH_PROOF"):
        terminal = _record(
            f"QTT.COMP.TEST.TERMINAL_{terminal_state}",
            f"test:terminal_{terminal_state.lower()}",
            [("x", "UNITLESS")],
            [("y", "UNITLESS")],
            record_state=terminal_state,
        )
        candidate = copy.deepcopy(terminal)
        candidate["record_state"] = "CANONICAL_ACCEPTED"
        snapshot = _build_snapshot([terminal], generation=1)
        delta = _derive_registry_update([terminal], [candidate])
        with pytest.raises(ValueError, match="TERMINAL_RECORD_REACTIVATION_FORBIDDEN"):
            _apply_registry_update(
                snapshot, delta, [candidate], verify_full_rebuild=True
            )


def test_object_input_value_field_is_not_misread_as_typed_envelope() -> None:
    record = _record(
        "QTT.COMP.TEST.OBJECT_VALUE_FIELD",
        "test:object_value_field",
        [("payload", "UNSPECIFIED")],
        [("field_count", "UNITLESS")],
    )
    record["definition"]["input_schema"][0]["type"] = "OBJECT"
    plane = QKUComputationControlPlaneV1(
        records=[record],
        implementation_allowlist={
            "test:object_value_field": lambda values: {
                "field_count": len(values["payload"])
            }
        },
    )
    receipt = plane.compute(
        record["canonical_component_id"],
        {"payload": {"value": 1, "other": 2}},
        {"market": "TEST", "venue": "LOCAL"},
    )
    assert receipt.outputs["field_count"] == 2


def test_provisional_record_cannot_report_stack_ready() -> None:
    provisional = _record(
        "QTT.COMP.TEST.PROVISIONAL_STATUS",
        "test:provisional_status",
        [("x", "UNITLESS")],
        [("y", "UNITLESS")],
        record_state="PROVISIONAL",
    )
    plane = QKUComputationControlPlaneV1(
        records=[provisional],
        implementation_allowlist={
            "test:provisional_status": lambda values: {"y": values["x"]}
        },
    )
    status = plane.status(provisional["canonical_component_id"], _context())
    assert status["derived_state"] == "SPECIFIED"
    assert status["requirements_closed"] is False
    assert any("RECORD_NOT_CANONICAL_ACCEPTED" in value for value in status["blockers"])


def test_reuse_targets_only_accepted_records_and_merges_pending_occurrences() -> None:
    rejected = _record(
        "QTT.COMP.TEST.REJECTED_REUSE_TARGET",
        "test:rejected_reuse_target",
        [("x", "UNITLESS")],
        [("y", "UNITLESS")],
        record_state="REJECTED_INVALID",
    )
    candidate = copy.deepcopy(rejected)
    candidate_id = "QTT.COMP.TEST.REJECTED_REUSE_CANDIDATE"
    candidate["canonical_component_id"] = candidate_id
    candidate["record_state"] = "PROVISIONAL"
    candidate["bindings"] = []
    candidate["exact_resolution_action"] = f"MISSING_CONTEXTUAL_BINDING: {candidate_id}"
    candidate["uses"]["qku_role_bindings"] = []
    candidate["provenance"][0]["canonical_target_ref"] = candidate_id
    records, _, report = _compile_expansion_batch(
        [rejected],
        _expansion_batch(
            [
                {
                    "record": candidate,
                    "equivalence_decision": "INCONCLUSIVE",
                    "nonidentical_relation": "DISTINCT",
                }
            ],
            "SPECIFIED",
            batch_id="BATCH.REJECTED.NOT.REUSED",
        ),
    )
    assert len(records) == 2
    assert report["outcomes"][0]["decision"] == "DISTINCT"

    first = copy.deepcopy(candidate)
    first["canonical_component_id"] = "QTT.COMP.TEST.PENDING_OCCURRENCE_A"
    first["exact_resolution_action"] = (
        "MISSING_CONTEXTUAL_BINDING: QTT.COMP.TEST.PENDING_OCCURRENCE_A"
    )
    first["provenance"][0]["canonical_target_ref"] = first[
        "canonical_component_id"
    ]
    first["provenance"][0]["source_row_ref"] = "PENDING_A"
    second = copy.deepcopy(first)
    second["canonical_component_id"] = "QTT.COMP.TEST.PENDING_OCCURRENCE_B"
    second["exact_resolution_action"] = (
        "MISSING_CONTEXTUAL_BINDING: QTT.COMP.TEST.PENDING_OCCURRENCE_B"
    )
    second["provenance"][0]["canonical_target_ref"] = second[
        "canonical_component_id"
    ]
    second["provenance"][0]["source_row_ref"] = "PENDING_B"
    pending_records, _, pending_report = _compile_expansion_batch(
        [],
        _expansion_batch(
            [
                {"record": first, "equivalence_decision": "INCONCLUSIVE"},
                {"record": second, "equivalence_decision": "INCONCLUSIVE"},
            ],
            "SPECIFIED",
            batch_id="BATCH.PENDING.OCCURRENCES",
        ),
    )
    assert len(pending_records) == 1
    assert len(pending_records[0]["provenance"]) == 2
    assert pending_records[0]["relations"] == []
    assert {value["decision"] for value in pending_report["outcomes"]} == {
        "DISTINCT",
        "PROVISIONAL_OCCURRENCE_MERGED",
    }


def test_rp5c_occurrence_count_is_source_derived_and_lineage_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from tools import validate_pr169_qku_comp_control1 as validator

    monkeypatch.setattr(validator, "EXPECTED_RP5C_CANONICAL", 2)
    dedupe_rows = [
        {
            "canonical_identity_row_id": "RP5C_IDENTITY_00000001",
            "duplicate_group_id": "RP5C_DUP_GROUP_00000001",
            "dedupe_status": "DUPLICATE_GROUP_PRESERVED",
            "duplicate_member_count": 2,
            "duplicate_member_identity_row_ids": [
                "RP5C_IDENTITY_00000001",
                "RP5C_IDENTITY_00000003",
            ],
        },
        {
            "canonical_identity_row_id": "RP5C_IDENTITY_00000002",
            "duplicate_group_id": "RP5C_DUP_GROUP_00000002",
            "dedupe_status": "UNIQUE_PRESERVED",
            "duplicate_member_count": 1,
            "duplicate_member_identity_row_ids": ["RP5C_IDENTITY_00000002"],
        },
    ]
    lineage_rows = [
        {
            "canonical_identity_row_id": "RP5C_IDENTITY_00000001",
            "identity_row_id": "RP5C_IDENTITY_00000001",
        },
        {
            "canonical_identity_row_id": "RP5C_IDENTITY_00000001",
            "identity_row_id": "RP5C_IDENTITY_00000003",
        },
        {
            "canonical_identity_row_id": "RP5C_IDENTITY_00000002",
            "identity_row_id": "RP5C_IDENTITY_00000002",
        },
    ]

    dedupe_path = tmp_path / validator.RP5C_DEDUPE
    lineage_path = tmp_path / validator.RP5C_LINEAGE
    dedupe_path.parent.mkdir(parents=True)
    dedupe_path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in dedupe_rows),
        encoding="utf-8",
    )
    lineage_path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in lineage_rows),
        encoding="utf-8",
    )
    canonical_library_rows = [
        {
            "canonical_identity_row_id": row["canonical_identity_row_id"],
            "duplicate_group_id": row["duplicate_group_id"],
            "identity_type": "FORMULA",
            "qku_id": None,
            "formula_id": f"FORMULA_{index}",
            "formula_variant_id": None,
            "formula_expression_ref": None,
            "plugin_ref": None,
        }
        for index, row in enumerate(dedupe_rows, 1)
    ]
    for relative_path in validator.RP5C_LIBRARIES:
        library_path = tmp_path / relative_path
        library_path.parent.mkdir(parents=True, exist_ok=True)
        rows = canonical_library_rows if relative_path == validator.RP5C_CANONICAL_LIBRARY else []
        library_path.write_text(
            "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
            encoding="utf-8",
        )

    groups, member_count = validator._rp5c_source(
        tmp_path, validator.Deadline(10_000)
    )
    assert len(groups) == 2
    assert member_count == 3

    lineage_path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in lineage_rows[:-1]),
        encoding="utf-8",
    )
    with pytest.raises(validator.InvariantError, match="RP5C_LINEAGE_CLOSURE"):
        validator._rp5c_source(tmp_path, validator.Deadline(10_000))


def test_rp5c_structured_custody_key_preserves_ids_across_ordinal_and_source_renumbering(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from tools import build_pr169_qku_comp_control1 as builder
    from tools import validate_pr169_qku_comp_control1 as validator

    monkeypatch.setattr(builder, "EXPECTED_RP5C_IDENTITIES", 2)
    monkeypatch.setattr(validator, "EXPECTED_RP5C_CANONICAL", 2)

    def write_source(
        dedupe_rows: list[dict[str, Any]],
        lineage_rows: list[dict[str, Any]],
        formula_ids: Mapping[str, str],
    ) -> None:
        dedupe_path = tmp_path / builder.RP5C_DEDUPE
        lineage_path = tmp_path / builder.RP5C_LINEAGE
        dedupe_path.parent.mkdir(parents=True, exist_ok=True)
        dedupe_path.write_text(
            "".join(json.dumps(row, sort_keys=True) + "\n" for row in dedupe_rows),
            encoding="utf-8",
        )
        lineage_path.write_text(
            "".join(json.dumps(row, sort_keys=True) + "\n" for row in lineage_rows),
            encoding="utf-8",
        )
        canonical_library_rows = [
            {
                "canonical_identity_row_id": row["canonical_identity_row_id"],
                "duplicate_group_id": row["duplicate_group_id"],
                "identity_type": "FORMULA",
                "qku_id": None,
                "formula_id": formula_ids[row["canonical_identity_row_id"]],
                "formula_variant_id": None,
                "formula_expression_ref": None,
                "plugin_ref": None,
            }
            for row in dedupe_rows
        ]
        for relative_path in builder.RP5C_LIBRARIES:
            library_path = tmp_path / relative_path
            library_path.parent.mkdir(parents=True, exist_ok=True)
            rows = (
                canonical_library_rows
                if relative_path == builder.RP5C_CANONICAL_LIBRARY
                else []
            )
            library_path.write_text(
                "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
                encoding="utf-8",
            )

    first_dedupe = [
        {
            "row_id": "ROW.1",
            "canonical_identity_row_id": "RP5C_IDENTITY_00000001",
            "duplicate_group_id": "RP5C_DUP_GROUP_00000001",
            "dedupe_status": "UNIQUE_PRESERVED",
            "duplicate_member_count": 1,
            "duplicate_member_identity_row_ids": ["RP5C_IDENTITY_00000001"],
        },
        {
            "row_id": "ROW.2",
            "canonical_identity_row_id": "RP5C_IDENTITY_00000002",
            "duplicate_group_id": "RP5C_DUP_GROUP_00000002",
            "dedupe_status": "UNIQUE_PRESERVED",
            "duplicate_member_count": 1,
            "duplicate_member_identity_row_ids": ["RP5C_IDENTITY_00000002"],
        },
    ]
    first_lineage = [
        {
            "canonical_identity_row_id": row["canonical_identity_row_id"],
            "identity_row_id": row["canonical_identity_row_id"],
        }
        for row in first_dedupe
    ]
    write_source(
        first_dedupe,
        first_lineage,
        {
            "RP5C_IDENTITY_00000001": "FORMULA_A",
            "RP5C_IDENTITY_00000002": "FORMULA_B",
        },
    )
    first_batch = builder._build_rp5c_batch(
        tmp_path, (), builder._Deadline(10_000)
    )
    base_records = [copy.deepcopy(item["record"]) for item in first_batch["items"]]
    assert {record["canonical_component_id"] for record in base_records} == {
        "QTT.COMP.RP5C.00000001",
        "QTT.COMP.RP5C.00000002",
    }

    renumbered_dedupe = [
        {
            "row_id": "ROW.100",
            "canonical_identity_row_id": "RP5C_IDENTITY_00000100",
            "duplicate_group_id": "RP5C_DUP_GROUP_00000002",
            "dedupe_status": "DUPLICATE_GROUP_PRESERVED",
            "duplicate_member_count": 2,
            "duplicate_member_identity_row_ids": [
                "RP5C_IDENTITY_00000100",
                "RP5C_IDENTITY_00000102",
            ],
        },
        {
            "row_id": "ROW.101",
            "canonical_identity_row_id": "RP5C_IDENTITY_00000101",
            "duplicate_group_id": "RP5C_DUP_GROUP_00000001",
            "dedupe_status": "UNIQUE_PRESERVED",
            "duplicate_member_count": 1,
            "duplicate_member_identity_row_ids": ["RP5C_IDENTITY_00000101"],
        },
    ]
    renumbered_lineage = [
        {
            "canonical_identity_row_id": "RP5C_IDENTITY_00000100",
            "identity_row_id": "RP5C_IDENTITY_00000100",
        },
        {
            "canonical_identity_row_id": "RP5C_IDENTITY_00000100",
            "identity_row_id": "RP5C_IDENTITY_00000102",
        },
        {
            "canonical_identity_row_id": "RP5C_IDENTITY_00000101",
            "identity_row_id": "RP5C_IDENTITY_00000101",
        },
    ]
    write_source(
        renumbered_dedupe,
        renumbered_lineage,
        {
            "RP5C_IDENTITY_00000100": "FORMULA_A",
            "RP5C_IDENTITY_00000101": "FORMULA_B",
        },
    )
    rebuilt = builder._build_rp5c_batch(
        tmp_path, (), builder._Deadline(10_000), base_records
    )
    rebuilt_records = [item["record"] for item in rebuilt["items"]]
    assert {record["canonical_component_id"] for record in rebuilt_records} == {
        "QTT.COMP.RP5C.00000001",
        "QTT.COMP.RP5C.00000002",
    }
    first_record = next(
        record
        for record in rebuilt_records
        if record["canonical_component_id"] == "QTT.COMP.RP5C.00000001"
    )
    assert first_record["bindings"][0]["binding_id"] == "BINDING.RP5C.REVIEW.00000001"
    assert next(
        relation
        for relation in first_record["relations"]
        if relation["relation_type"] == "RP5C_SOURCE_LINEAGE_SUMMARY"
    )["source_canonical_identity_row_id"] == "RP5C_IDENTITY_00000100"
    assert next(
        relation
        for relation in first_record["relations"]
        if relation["relation_type"]
        == "RP5C_BASELINE_GROUPING_NOT_CONTROL1_EQUIVALENCE_PROOF"
    )["source_duplicate_group_id"] == "RP5C_DUP_GROUP_00000002"

    source_groups, source_member_count = validator._rp5c_source(
        tmp_path, validator.Deadline(10_000)
    )
    accepted_key_map = validator._registry_rp5c_group_map(base_records)
    assert validator._validate_rp5c_import(
        rebuilt_records,
        source_groups,
        validator.Deadline(10_000),
        accepted_key_map,
    ) == (2, source_member_count)
    corrupt_key = copy.deepcopy(rebuilt_records)
    group_relation = next(
        relation
        for relation in corrupt_key[0]["relations"]
        if relation["relation_type"]
        == "RP5C_BASELINE_GROUPING_NOT_CONTROL1_EQUIVALENCE_PROOF"
    )
    group_relation["source_group_custody_key"]["formula_id"] = "FORGED_FORMULA"
    with pytest.raises(validator.InvariantError, match="RP5C_CANONICAL_IMPORT"):
        validator._validate_rp5c_import(
            corrupt_key, source_groups, validator.Deadline(10_000), accepted_key_map
        )

    dormant_target = copy.deepcopy(base_records[0])
    dormant_target["record_state"] = "DORMANT_PRESERVED"
    dormant_target["bindings"][0]["activation_state"] = "DORMANT_PRESERVED"
    dormant_candidate = copy.deepcopy(dormant_target)
    dormant_candidate["uses"]["qku_role_bindings"].append(
        {
            "qku_id": "QKU-RP5C-PRESERVED-NONRUNTIME",
            "role_or_decision_stage": "source_role",
            "market_family": "unknown_needs_review",
            "stack_root_or_direct_component": None,
            "selection_rule_if_container": None,
            "agent_policy_tags": [],
            "source_refs": [builder.RP5C_LIBRARIES[0].as_posix(), "SOURCE.ROW.1"],
            "exact_resolution_action": (
                "MISSING_SEMANTIC_SPECIFICATION: "
                f"{dormant_candidate['canonical_component_id']}"
            ),
            "runtime_root_eligibility": (
                "INELIGIBLE_UNTIL_COMPLETE_SEMANTICS_AND_DIRECT_ROOT_PROOF"
            ),
        }
    )
    exact_action = (
        "MISSING_SEMANTIC_SPECIFICATION: "
        f"{dormant_candidate['canonical_component_id']}"
    )
    dormant_candidate["relations"].append(
        {
            "relation_type": "RP5C_RUNTIME_ROOT_INELIGIBILITY",
            "runtime_root_eligible": False,
            "preserved_qku_role_count": 1,
            "source_stage1_dormant": False,
            "reason": "INCOMPLETE_IMPORTED_SEMANTICS_CANNOT_BE_A_RUNTIME_QKU_ROOT",
            "exact_resolution_action": exact_action,
            "selector_or_root_invented": False,
            "qku_roles_erased": False,
        }
    )
    dormant_candidate["bindings"][0]["activation_state"] = "DORMANT_PRESERVED"
    role_batch = _expansion_batch(
        [{"record": dormant_candidate}],
        "SPECIFIED",
        batch_id="BATCH.RP5C.NONRUNTIME.ROLE.PRESERVATION",
    )
    role_batch["source_refs"].append(builder.RP5C_DEDUPE.as_posix())
    compiled, _, _ = _compile_expansion_batch([dormant_target], role_batch)
    assert len(compiled[0]["uses"]["qku_role_bindings"]) == 1
    assert compiled[0]["uses"]["qku_role_bindings"][0][
        "stack_root_or_direct_component"
    ] is None

    write_source(
        renumbered_dedupe,
        renumbered_lineage,
        {
            "RP5C_IDENTITY_00000100": "FORMULA_A",
            "RP5C_IDENTITY_00000101": "FORMULA_C",
        },
    )
    with pytest.raises(builder.BuildError, match="custody-key set added an unknown group"):
        builder._build_rp5c_batch(
            tmp_path, (), builder._Deadline(10_000), base_records
        )


def test_temporary_output_loads_the_accepted_cumulative_registry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from tools import build_pr169_qku_comp_control1 as builder

    repo_root = tmp_path / "repo"
    target = (tmp_path / "candidate").resolve()
    accepted = [{"canonical_component_id": "QTT.COMP.TEST.ACCEPTED"}]
    calls: list[Path] = []

    def fake_read(path: Path, _deadline: Any) -> list[dict[str, Any]]:
        calls.append(path)
        return copy.deepcopy(accepted)

    monkeypatch.setattr(builder, "_read_accepted_registry_from_base", fake_read)
    assert builder._load_cumulative_base_records(
        repo_root, target, builder._Deadline(10_000)
    ) == accepted
    assert calls == [repo_root]


def test_cumulative_base_is_merge_base_not_committed_pr_candidate(tmp_path: Path) -> None:
    from tools import build_pr169_qku_comp_control1 as builder

    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    def git(*args: str) -> str:
        result = subprocess.run(
            ["git", "-C", str(repo_root), *args],
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip()

    git("init")
    git("config", "user.email", "control1-test@example.invalid")
    git("config", "user.name", "CONTROL1 test")
    (repo_root / "README.md").write_text("accepted base\n", encoding="utf-8")
    git("add", "README.md")
    git("commit", "-m", "base")
    git("branch", "-M", "main")
    base_sha = git("rev-parse", "HEAD")
    git("update-ref", "refs/remotes/origin/main", base_sha)
    git("switch", "-c", "pr169-qku-comp-control1")

    candidate_root = repo_root / builder.GENERATED_PREFIX
    candidate_root.mkdir(parents=True)
    (candidate_root / "registry.jsonl").write_text(
        '{"canonical_component_id":"QTT.COMP.UNAUTHORIZED.CANDIDATE"}\n',
        encoding="utf-8",
    )
    git("add", builder.GENERATED_PREFIX.as_posix())
    git("commit", "-m", "unreviewed candidate")
    assert git("rev-parse", "HEAD") != base_sha
    assert builder._accepted_base_ref(repo_root) == base_sha
    assert builder._read_accepted_registry_from_base(
        repo_root, builder._Deadline(10_000)
    ) == []


@pytest.mark.parametrize("layout", ["single", "sharded"])
def test_single_and_sharded_merge_base_registry_materialization(
    tmp_path: Path, layout: str
) -> None:
    from tools import build_pr169_qku_comp_control1 as builder
    from tools import validate_pr169_qku_comp_control1 as validator

    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    def git(*args: str) -> str:
        result = subprocess.run(
            ["git", "-C", str(repo_root), *args],
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip()

    git("init")
    git("config", "user.email", "control1-test@example.invalid")
    git("config", "user.name", "CONTROL1 test")
    artifact_dir = repo_root / builder.GENERATED_PREFIX
    base_record = _record(
        "QTT.COMP.TEST.ACCEPTED_BASE",
        "test:accepted_base",
        [("x", "UNITLESS")],
        [("y", "UNITLESS")],
    )
    _write_registry_layout([base_record], artifact_dir, force_layout=layout)
    (artifact_dir / "acceptance.report.json").write_text("{}\n", encoding="utf-8")
    git("add", builder.GENERATED_PREFIX.as_posix())
    git("commit", "-m", "accepted registry base")
    git("branch", "-M", "main")
    base_sha = git("rev-parse", "HEAD")
    git("update-ref", "refs/remotes/origin/main", base_sha)
    git("switch", "-c", "pr169-qku-comp-control1")

    data_file = next(artifact_dir.glob("registry*.jsonl"))
    with data_file.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write('{"canonical_component_id":"QTT.COMP.UNAUTHORIZED.CANDIDATE"}\n')
    git("add", builder.GENERATED_PREFIX.as_posix())
    git("commit", "-m", "candidate contamination")

    builder_records = builder._read_accepted_registry_from_base(
        repo_root, builder._Deadline(10_000)
    )
    assert [row["canonical_component_id"] for row in builder_records] == [
        "QTT.COMP.TEST.ACCEPTED_BASE"
    ]
    control_module = importlib.import_module("qtt.computation_control.control")
    validator_records = validator._load_accepted_base_records(
        control_module, repo_root, validator.Deadline(10_000)
    )
    assert [row["canonical_component_id"] for row in validator_records] == [
        "QTT.COMP.TEST.ACCEPTED_BASE"
    ]


def test_git_base_tree_inspection_errors_fail_closed(tmp_path: Path) -> None:
    from tools import build_pr169_qku_comp_control1 as builder
    from tools import validate_pr169_qku_comp_control1 as validator

    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    subprocess.run(["git", "-C", str(repo_root), "init"], check=True, capture_output=True)
    invalid_ref = "0" * 40
    with pytest.raises(builder.BuildError, match="cannot enumerate accepted Git base tree"):
        builder._git_base_tree_paths(repo_root, invalid_ref, builder.GENERATED_PREFIX)
    with pytest.raises(validator.InvariantError, match="ACCEPTED_BASE_READ"):
        validator._git_base_tree_paths(
            repo_root, invalid_ref, validator.DEFAULT_ARTIFACT_DIR
        )


@pytest.mark.parametrize(
    "defect", ["shard_without_manifest", "single_plus_shard", "manifest_extra_shard"]
)
def test_invalid_merge_base_physical_layout_fails_closed(
    tmp_path: Path, defect: str
) -> None:
    from tools import build_pr169_qku_comp_control1 as builder
    from tools import validate_pr169_qku_comp_control1 as validator

    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    def git(*args: str) -> str:
        result = subprocess.run(
            ["git", "-C", str(repo_root), *args],
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip()

    git("init")
    git("config", "user.email", "control1-test@example.invalid")
    git("config", "user.name", "CONTROL1 test")
    artifact_dir = repo_root / builder.GENERATED_PREFIX
    artifact_dir.mkdir(parents=True)
    record = _record(
        "QTT.COMP.TEST.INVALID_BASE",
        "test:invalid_base",
        [("x", "UNITLESS")],
        [("y", "UNITLESS")],
    )
    if defect == "shard_without_manifest":
        (artifact_dir / "registry.part-extra.jsonl").write_text(
            json.dumps(record, sort_keys=True) + "\n", encoding="utf-8"
        )
    elif defect == "single_plus_shard":
        _write_registry_layout([record], artifact_dir, force_layout="single")
        (artifact_dir / "registry.part-extra.jsonl").write_text(
            json.dumps(record, sort_keys=True) + "\n", encoding="utf-8"
        )
    else:
        _write_registry_layout([record], artifact_dir, force_layout="sharded")
        (artifact_dir / "registry.part-extra.jsonl").write_text(
            json.dumps(record, sort_keys=True) + "\n", encoding="utf-8"
        )
    (artifact_dir / "acceptance.report.json").write_text("{}\n", encoding="utf-8")
    git("add", builder.GENERATED_PREFIX.as_posix())
    git("commit", "-m", f"invalid base {defect}")
    git("branch", "-M", "main")
    base_sha = git("rev-parse", "HEAD")
    git("update-ref", "refs/remotes/origin/main", base_sha)

    with pytest.raises(builder.BuildError):
        builder._read_accepted_registry_from_base(
            repo_root, builder._Deadline(10_000)
        )
    control_module = importlib.import_module("qtt.computation_control.control")
    with pytest.raises(validator.InvariantError, match="ACCEPTED_BASE"):
        validator._load_accepted_base_records(
            control_module, repo_root, validator.Deadline(10_000)
        )


def test_rp5c_custody_key_is_structured_and_normalizes_null_like_source() -> None:
    from tools import build_pr169_qku_comp_control1 as builder

    left = builder._rp5c_group_custody_key(
        {"identity_type": "A|B", "qku_id": "C"}
    )
    right = builder._rp5c_group_custody_key(
        {"identity_type": "A", "qku_id": "B|C"}
    )
    assert builder._rp5c_group_custody_tuple(left) != builder._rp5c_group_custody_tuple(
        right
    )
    assert builder._rp5c_group_custody_tuple(
        builder._rp5c_group_custody_key({"identity_type": "FORMULA", "qku_id": None})
    ) == builder._rp5c_group_custody_tuple(
        builder._rp5c_group_custody_key({"identity_type": "FORMULA", "qku_id": ""})
    )
    assert set(left) == {"key_version", *builder.RP5C_GROUP_KEY_FIELDS}


def test_builder_output_target_guard_never_replaces_arbitrary_content(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from tools import build_pr169_qku_comp_control1 as builder

    repo_root = (tmp_path / "repo").resolve()
    repo_root.mkdir()
    monkeypatch.setattr(builder.tempfile, "gettempdir", lambda: str(tmp_path))
    canonical = (repo_root / builder.GENERATED_PREFIX).resolve()
    assert builder._resolve_safe_output_target(repo_root, canonical) == canonical

    with pytest.raises(builder.BuildError, match="non-canonical.*repository"):
        builder._resolve_safe_output_target(repo_root, repo_root / "unowned")

    empty_temp_target = (tmp_path / "empty-control1-output").resolve()
    empty_temp_target.mkdir()
    assert (
        builder._resolve_safe_output_target(repo_root, empty_temp_target)
        == empty_temp_target
    )

    occupied = (tmp_path / "unrelated-existing-directory").resolve()
    occupied.mkdir()
    marker = occupied / "owner-data.txt"
    marker.write_text("preserve", encoding="utf-8")
    with pytest.raises(builder.BuildError, match="must not replace existing content"):
        builder._resolve_safe_output_target(repo_root, occupied)
    assert marker.read_text(encoding="utf-8") == "preserve"

    with pytest.raises(builder.BuildError, match="unsafe CONTROL1 output"):
        builder._resolve_safe_output_target(
            repo_root, tmp_path / ".codex_inputs" / "candidate"
        )


def _rp5c_nonruntime_role_record() -> dict[str, Any]:
    component_id = "QTT.COMP.RP5C.00000001"
    record = _record(component_id, "test:rp5c_nonruntime", [], [])
    record["record_state"] = "DORMANT_PRESERVED"
    record["origin_cohorts"] = ["RP5C_BASELINE"]
    exact_action = f"MISSING_SEMANTIC_SPECIFICATION: {component_id}"
    role = record["uses"]["qku_role_bindings"][0]
    role["stack_root_or_direct_component"] = None
    role["selection_rule_if_container"] = None
    role["runtime_root_eligibility"] = (
        "INELIGIBLE_UNTIL_COMPLETE_SEMANTICS_AND_DIRECT_ROOT_PROOF"
    )
    role["exact_resolution_action"] = exact_action
    binding = record["bindings"][0]
    binding["supported_modes"] = []
    binding["mode_state"] = {}
    binding["selected_implementation_version"] = None
    binding["activation_state"] = "DORMANT_PRESERVED"
    binding["readiness"]["authorization"] = "NOT_ELIGIBLE"
    record["relations"] = [
        {
            "relation_type": "RP5C_BASELINE_GROUPING_NOT_CONTROL1_EQUIVALENCE_PROOF",
            "source_group_custody_key": {
                "key_version": "RP5C_SOURCE_GROUP_CUSTODY_KEY_V1",
                "identity_type": "FORMULA",
                "qku_id": "QKU.TEST.00000001",
                "formula_id": "",
                "formula_variant_id": "",
                "formula_expression_ref": "",
                "plugin_ref": "",
            },
            "source_duplicate_group_id": "RP5C_DUP_GROUP_00000001",
            "source_dedupe_status": "UNIQUE_PRESERVED",
            "member_identity_row_ids": ["RP5C_IDENTITY_00000001"],
            "direct_semantic_equivalence_proven": False,
            "exact_proof_action": None,
        },
        {
            "relation_type": "RP5C_RUNTIME_ROOT_INELIGIBILITY",
            "runtime_root_eligible": False,
            "preserved_qku_role_count": 1,
            "source_stage1_dormant": False,
            "reason": "INCOMPLETE_IMPORTED_SEMANTICS_CANNOT_BE_A_RUNTIME_QKU_ROOT",
            "exact_resolution_action": exact_action,
            "selector_or_root_invented": False,
            "qku_roles_erased": False,
        },
    ]
    return record


def test_rp5c_preserved_qku_roles_fail_closed_against_runtime_activation() -> None:
    from tools import validate_pr169_qku_comp_control1 as validator

    record = _rp5c_nonruntime_role_record()
    _validate_record_shape(record)
    assert validator._validate_rp5c_nonruntime_qku_roles(record) == 1

    active = copy.deepcopy(record)
    active["record_state"] = "PROVISIONAL"
    with pytest.raises(ValueError, match="RP5C_QKU_ROLE_RUNTIME_ACTIVATION"):
        _validate_record_shape(active)
    with pytest.raises(
        validator.InvariantError, match="RP5C_QKU_ROLE_RUNTIME_ACTIVATION"
    ):
        validator._validate_rp5c_nonruntime_qku_roles(active)

    rooted = copy.deepcopy(record)
    rooted["uses"]["qku_role_bindings"][0][
        "stack_root_or_direct_component"
    ] = rooted["canonical_component_id"]
    with pytest.raises(ValueError, match="RP5C_QKU_ROLE_RUNTIME_ROOT"):
        _validate_record_shape(rooted)
    with pytest.raises(validator.InvariantError, match="RP5C_QKU_ROLE_RUNTIME_ROOT"):
        validator._validate_rp5c_nonruntime_qku_roles(rooted)

    activated_binding = copy.deepcopy(record)
    activated_binding["bindings"][0]["activation_state"] = "INACTIVE"
    with pytest.raises(ValueError, match="RP5C_QKU_ROLE_RUNTIME_BINDING"):
        _validate_record_shape(activated_binding)
    with pytest.raises(
        validator.InvariantError, match="RP5C_QKU_ROLE_RUNTIME_BINDING"
    ):
        validator._validate_rp5c_nonruntime_qku_roles(activated_binding)
