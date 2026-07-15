from __future__ import annotations

import copy
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
import importlib
import json
from pathlib import Path
import random
import subprocess
import tempfile
import threading
from typing import Any, Mapping

import pytest

from src.qtt.computation_control import QKUComputationControlPlaneV1
from src.qtt.computation_control.control import (
    NATIVE_IMPLEMENTATIONS,
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
from src.qtt.computation_control.models import ExpansionBatchV1


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
    requirements = requirements or []
    requirements_by_input = {
        str(requirement["consumer_input_name"]): requirement
        for requirement in requirements
        if requirement.get("required_or_optional") != "OPTIONAL"
    }
    input_source_bindings: list[dict[str, Any]] = []
    for name, unit in inputs:
        requirement = requirements_by_input.get(name)
        if requirement is None:
            input_source_bindings.append(
                {
                    "input_name": name,
                    "source_ref": "CALLER_TYPED_FIXTURE",
                    "declared_type": "NUMBER",
                    "unit_or_basis": unit,
                    "binding_state": "EXACT_TYPED_FIXTURE_BINDING",
                }
            )
        else:
            input_source_bindings.append(
                {
                    "input_name": name,
                    "source_ref": requirement[
                        "required_component_id_or_source_selector"
                    ],
                    "producer_output_name": requirement["producer_output_name"],
                    "declared_type": "NUMBER",
                    "unit_or_basis": unit,
                    "binding_state": "CANONICAL_REQUIREMENT_OUTPUT",
                }
            )
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
            "zero_input_proof": "TEST_CALLABLE_HAS_NO_INPUT_PORTS",
            "zero_output_proof": "TEST_CALLABLE_HAS_NO_OUTPUT_PORTS",
            "output_accounting_class": "NON_ACCOUNTING_FIXTURE",
            "missing_stale_nonfinite_behavior": "FAIL_CLOSED",
            "precision_and_rounding": {"numeric": "EXACT_FIXTURE"},
            "parameter_schema_and_default_provenance": {
                "parameters": [],
                "default_provenance": "CONTROL1_TEST_FIXTURE",
            },
            "requirements": requirements,
            "latency_class": "PRETRADE_BOUNDED",
            "risk_materiality": "TEST_ONLY",
            "failure_domain_tags": ["TEST_ONLY"],
            "classical_fallback": {
                "not_applicable": True,
                "proof_ref": "TEST_COMPONENT_FAILS_CLOSED_WITHOUT_ALTERNATE_SEMANTICS",
            },
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
                    "STATIC_VALIDATION": {
                        "evidence": "FIXTURE",
                        "authorization": "NOT_ELIGIBLE",
                    },
                    "TEST_VECTOR": {
                        "evidence": "FIXTURE",
                        "authorization": "NOT_ELIGIBLE",
                    },
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
                "input_source_bindings": input_source_bindings,
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
                    "parameter_selector_agent": {
                        "control_plane_operations": ["resolve", "compute", "status", "explain"],
                        "mode_ceiling": "STATIC_VALIDATION",
                        "order_release_authority": False,
                        "source_truth_authority": False,
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


def test_fixture_reference_cannot_manufacture_specification_or_agent_compute() -> None:
    false_spec = _record(
        "QTT.COMP.TEST.FALSE_FIXTURE_SPEC",
        "test:false_fixture_spec",
        [("x", "UNITLESS")],
        [("y", "UNITLESS")],
    )
    false_spec["bindings"][0]["evidence_summary"]["fixture_ref"] = "FIXTURE.EXISTS"
    false_spec["definition"]["input_schema"][0]["type"] = (
        "SOURCE_DECLARED_NUMERIC_OR_SEQUENCE"
    )
    with pytest.raises(ValueError, match="FALSE_SPECIFICATION_PASS"):
        _validate_record_shape(false_spec)

    false_compute = copy.deepcopy(false_spec)
    false_compute["bindings"][0]["readiness"]["specification"] = "REQUIRED"
    false_compute["bindings"][0]["exact_resolution_action_or_null"] = (
        "MISSING_SPECIFICATION_SEMANTICS: QTT.COMP.TEST.FALSE_FIXTURE_SPEC@1.0: "
        "input_schema[0].type"
    )
    with pytest.raises(ValueError, match="FALSE_SPECIFIED_STATE"):
        _validate_record_shape(false_compute)
    false_compute["bindings"][0]["derived_state"] = "SPECIFICATION_REQUIRED"
    false_compute["bindings"][0]["input_source_bindings"][0][
        "declared_type"
    ] = "SOURCE_DECLARED_NUMERIC_OR_SEQUENCE"
    with pytest.raises(ValueError, match="FALSE_AGENT_COMPUTE_ELIGIBILITY"):
        _validate_record_shape(false_compute)

    from tools import build_pr169_qku_comp_control1 as builder

    generated = builder._binding(
        false_compute["canonical_component_id"],
        definition=false_compute["definition"],
        binding_id="BINDING.TEST.FALSE_FIXTURE_SPEC.BUILDER",
        agent_ids=("parameter_selector_agent",),
        implementation_version="impl-1.0",
        exact_action=None,
        fixture_ref="FIXTURE.EXISTS",
        requirements_ready=True,
        oracle_ready=True,
    )
    assert generated["readiness"]["specification"] == "REQUIRED"
    assert generated["readiness"]["inputs"] == "REQUIRED"
    assert generated["readiness"]["context"] == "REQUIRED"
    assert generated["derived_state"] == "SPECIFICATION_REQUIRED"
    assert generated["agent_access_policy"]["parameter_selector_agent"][
        "control_plane_operations"
    ] == ["status", "explain"]


def _closed_implied_fixture_case() -> tuple[Any, dict[str, Any], dict[str, Any]]:
    from tools import build_pr169_qku_comp_control1 as builder
    from src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.formula_seed_library import (
        formula_specs,
    )

    spec = next(
        value for value in formula_specs() if value.formula_id == "IMPLIED_PROBABILITY"
    )
    rows = builder._read_pr162d_test_vector_rows(Path.cwd())
    fixture_ref = "PR162D_R2A_TV_FORMULA::IMPLIED_PROBABILITY"
    record = builder._formula_record(
        spec,
        ("parameter_selector_agent",),
        rows[fixture_ref],
    )
    contract = builder._closed_formula_fixture_contract(
        spec, record["definition"], rows[fixture_ref]
    )
    assert contract is not None
    return spec, record, contract


@pytest.mark.parametrize(
    ("defect", "expected_issue"),
    [
        ("nonexistent_ref", "fixture_ref_unresolved"),
        ("unresolved_source", "source_fixture_unresolved"),
        ("missing_port", "fixture_port_missing:price"),
        ("extra_port", "fixture_port_extra:unexpected"),
        ("mistyped_port", "fixture_type_mismatch:price"),
        ("unit_mismatch", "fixture_unit_mismatch:price"),
        ("float_value", "non_exact_scalar_type:float"),
        ("wrong_exact_value", "fixture_value_source_mismatch:price"),
        ("boolean_value", "non_exact_scalar_type:bool"),
        ("nonfinite_value", "nonfinite_decimal"),
    ],
)
def test_ephemeral_fixture_contract_defects_cannot_create_readiness_or_compute(
    defect: str, expected_issue: str
) -> None:
    from tools import build_pr169_qku_comp_control1 as builder
    from tools import validate_pr169_qku_comp_control1 as validator

    _spec, record, valid_contract = _closed_implied_fixture_case()
    contract = copy.deepcopy(valid_contract)
    fixture_ref = str(valid_contract["fixture_ref"])
    if defect == "nonexistent_ref":
        fixture_ref += ".MISSING"
    elif defect == "unresolved_source":
        contract["source_resolution_state"] = "UNRESOLVED"
    elif defect == "missing_port":
        contract["ports"] = [
            port for port in contract["ports"] if port["input_name"] != "price"
        ]
    elif defect == "extra_port":
        contract["ports"].append(
            {
                "input_name": "unexpected",
                "declared_type": "FINITE_DECIMAL_COMPATIBLE_SCALAR",
                "unit_or_basis": "price",
                "value": Decimal("1"),
                "ownership": "DIRECT_TYPED_REQUEST_INPUT",
            }
        )
    else:
        price = next(
            port for port in contract["ports"] if port["input_name"] == "price"
        )
        if defect == "mistyped_port":
            price["declared_type"] = "FLOAT"
        elif defect == "unit_mismatch":
            price["unit_or_basis"] = "currency"
        elif defect == "float_value":
            price["value"] = 0.43
        elif defect == "wrong_exact_value":
            price["value"] = Decimal("0.99")
        elif defect == "boolean_value":
            price["value"] = True
        elif defect == "nonfinite_value":
            price["value"] = Decimal("NaN")

    component_id = str(record["canonical_component_id"])
    issues = builder._ephemeral_fixture_contract_issues(
        component_id, record["definition"], fixture_ref, contract
    )
    assert any(expected_issue in issue for issue in issues)
    binding = builder._binding(
        component_id,
        definition=record["definition"],
        binding_id="BINDING.TEST.INVALID.EPHEMERAL.FIXTURE",
        agent_ids=("parameter_selector_agent",),
        implementation_version="control-native-decimal-v1",
        exact_action=None,
        fixture_ref=fixture_ref,
        fixture_contract=contract,
        requirements_ready=True,
        oracle_ready=True,
    )
    assert binding["readiness"]["inputs"] == "REQUIRED"
    assert binding["readiness"]["context"] == "REQUIRED"
    assert binding["derived_state"] == "SPECIFIED"
    assert expected_issue in binding["exact_resolution_action_or_null"]
    assert binding["agent_access_policy"]["parameter_selector_agent"][
        "control_plane_operations"
    ] == ["status", "explain"]

    invalid_record = copy.deepcopy(record)
    invalid_record["bindings"] = [binding]
    validator._validate_record(invalid_record)
    invalid_record["bindings"][0]["agent_access_policy"][
        "parameter_selector_agent"
    ]["control_plane_operations"] = ["resolve", "compute", "status", "explain"]
    with pytest.raises(validator.InvariantError, match="FALSE_AGENT_COMPUTE_ELIGIBILITY"):
        validator._validate_record(invalid_record)


def test_incomplete_implementation_inventory_is_dispositioned_without_facade_compute() -> None:
    from src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.algorithm_seed_library import (
        algorithm_specs,
    )
    from tools import build_pr169_qku_comp_control1 as builder
    from tools import validate_pr169_qku_comp_control1 as validator

    spec = next(
        value
        for value in algorithm_specs()
        if value.algorithm_id == "BUILD_PARAMETER_PACK_FROM_DEFAULTS"
    )
    record = builder._algorithm_record(spec, ("parameter_selector_agent",))
    binding = record["bindings"][0]
    assert binding["readiness"]["specification"] == "REQUIRED"
    assert binding["supported_modes"] == []
    assert binding["agent_access_policy"]["parameter_selector_agent"][
        "control_plane_operations"
    ] == ["status", "explain"]

    facade_calls: list[str] = []

    class GuardFacade:
        _implementation_allowlist = {
            spec.callable_ref: lambda _inputs: (_ for _ in ()).throw(
                AssertionError("incomplete implementation must not execute")
            )
        }

        def resolve(self, *_args: Any, **_kwargs: Any) -> None:
            facade_calls.append("resolve")
            raise AssertionError("incomplete implementation must not resolve")

        def compute(self, *_args: Any, **_kwargs: Any) -> None:
            facade_calls.append("compute")
            raise AssertionError("incomplete implementation must not compute")

    result = validator._invoke_implementation_fixtures(
        GuardFacade(),
        object(),
        [record],
        validator.Deadline(10_000),
    )
    assert result[:3] == (1, 0, 1)
    assert result[3] == []
    assert facade_calls == []

    falsely_eligible = copy.deepcopy(record)
    falsely_eligible["bindings"][0]["agent_access_policy"][
        "parameter_selector_agent"
    ]["control_plane_operations"] = ["resolve", "compute", "status", "explain"]
    with pytest.raises(
        validator.InvariantError,
        match="INCOMPLETE_IMPLEMENTATION_OPERATION_ELIGIBILITY",
    ):
        validator._invoke_implementation_fixtures(
            GuardFacade(),
            object(),
            [falsely_eligible],
            validator.Deadline(10_000),
        )
    assert facade_calls == []


def test_requirement_owned_fixture_port_is_not_a_direct_caller_port() -> None:
    from tools import build_pr169_qku_comp_control1 as builder
    from tools import validate_pr169_qku_comp_control1 as validator
    from src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.formula_seed_library import (
        formula_specs,
    )

    spec = next(
        value for value in formula_specs() if value.formula_id == "PROBABILITY_EDGE"
    )
    rows = builder._read_pr162d_test_vector_rows(Path.cwd())
    fixture_ref = "PR162D_R2A_TV_FORMULA::PROBABILITY_EDGE"
    record = builder._formula_record(
        spec,
        ("parameter_selector_agent",),
        rows[fixture_ref],
    )
    binding_by_name = {
        value["input_name"]: value
        for value in record["bindings"][0]["input_source_bindings"]
    }
    assert binding_by_name["p_model"]["binding_state"] == (
        "EXACT_TYPED_REQUEST_INPUT_LOCK"
    )
    assert binding_by_name["implied_probability"]["binding_state"] == (
        "CANONICAL_REQUIREMENT_OUTPUT"
    )
    assert binding_by_name["implied_probability"]["source_ref"] == (
        "QTT.COMP.FORMULA.IMPLIED_PROBABILITY"
    )
    implied_spec = next(
        value for value in formula_specs() if value.formula_id == "IMPLIED_PROBABILITY"
    )
    implied_ref = "PR162D_R2A_TV_FORMULA::IMPLIED_PROBABILITY"
    implied_record = builder._formula_record(
        implied_spec,
        ("parameter_selector_agent",),
        rows[implied_ref],
    )
    records_by_id = {
        str(value["canonical_component_id"]): value
        for value in (implied_record, record)
    }
    assert not validator._independent_closed_fixture_contract_issues(
        record, rows[fixture_ref], records_by_id
    )
    mislabeled = copy.deepcopy(record)
    requirement_port = next(
        value
        for value in mislabeled["bindings"][0]["input_source_bindings"]
        if value["input_name"] == "implied_probability"
    )
    requirement_port.update(
        {
            "binding_state": "EXACT_TYPED_REQUEST_INPUT_LOCK",
            "source_ref": (
                "QKUComputationControlPlaneV1.compute.inputs::implied_probability"
            ),
            "fixture_evidence_ref": fixture_ref,
        }
    )
    mislabeled_issues = validator._independent_closed_fixture_contract_issues(
        mislabeled,
        rows[fixture_ref],
        {
            **records_by_id,
            str(mislabeled["canonical_component_id"]): mislabeled,
        },
    )
    assert "requirement_mislabeled_as_fixture:implied_probability" in (
        mislabeled_issues
    )


def test_crafted_complete_nonclosed_formula_contract_is_not_allowlisted() -> None:
    from tools import build_pr169_qku_comp_control1 as builder
    from tools import validate_pr169_qku_comp_control1 as validator

    _spec, record, contract = _closed_implied_fixture_case()
    component_id = "QTT.COMP.FORMULA.CRAFTED_NONCLOSED"
    fixture_ref = "PR162D_R2A_TV_FORMULA::CRAFTED_NONCLOSED"
    contract = copy.deepcopy(contract)
    contract.update(
        {
            "fixture_ref": fixture_ref,
            "source_artifact_ref": builder.PR162D_TEST_VECTOR_REGISTRY.as_posix(),
            "source_row_ref": f"records[{fixture_ref}]",
        }
    )
    issues = builder._ephemeral_fixture_contract_issues(
        component_id, record["definition"], fixture_ref, contract
    )
    assert "component_not_fixture_allowlisted" in issues
    binding = builder._binding(
        component_id,
        definition=record["definition"],
        binding_id="BINDING.TEST.CRAFTED.NONCLOSED",
        agent_ids=("parameter_selector_agent",),
        implementation_version="control-native-decimal-v1",
        exact_action=None,
        fixture_ref=fixture_ref,
        fixture_contract=contract,
        requirements_ready=True,
        oracle_ready=True,
    )
    assert binding["readiness"]["inputs"] == "REQUIRED"
    assert binding["readiness"]["context"] == "REQUIRED"
    assert binding["agent_access_policy"]["parameter_selector_agent"][
        "control_plane_operations"
    ] == ["status", "explain"]

    crafted_record = copy.deepcopy(record)
    crafted_record["canonical_component_id"] = component_id
    assert validator._independent_closed_fixture_contract_issues(
        crafted_record, {}, {component_id: crafted_record}
    ) == ("component_not_fixture_allowlisted",)


@pytest.mark.parametrize(
    ("defect", "expected_issue"),
    [
        ("missing_source", "source_fixture_unresolved"),
        ("missing_port", "source_input_ports"),
        ("extra_port", "source_input_ports"),
        ("float_value", "non_exact_numeric_type:float"),
        ("wrong_input_value", "source_input_value_mismatch:price"),
        (
            "wrong_expected_output",
            "source_output_value_mismatch:implied_probability",
        ),
        ("boolean_value", "non_exact_numeric_type:bool"),
        ("nonfinite_value", "nonfinite_decimal"),
        ("unit_mismatch", "unit_or_basis"),
        ("fixture_ref_mismatch", "binding_fixture_ref"),
    ],
)
def test_independent_validator_reconstructs_closed_fixture_contract_defects(
    defect: str, expected_issue: str
) -> None:
    from tools import build_pr169_qku_comp_control1 as builder
    from tools import validate_pr169_qku_comp_control1 as validator

    _spec, record, _contract = _closed_implied_fixture_case()
    fixture_ref = "PR162D_R2A_TV_FORMULA::IMPLIED_PROBABILITY"
    source_row: Mapping[str, Any] | None = copy.deepcopy(
        builder._read_pr162d_test_vector_rows(Path.cwd())[fixture_ref]
    )
    mutated = copy.deepcopy(record)
    if defect == "missing_source":
        source_row = None
    elif defect == "missing_port":
        assert source_row is not None
        source_row["inputs"].pop("price")
    elif defect == "extra_port":
        assert source_row is not None
        source_row["inputs"]["unexpected"] = Decimal("1")
    elif defect == "float_value":
        assert source_row is not None
        source_row["inputs"]["price"] = 0.43
    elif defect == "wrong_input_value":
        assert source_row is not None
        source_row["inputs"]["price"] = Decimal("0.99")
    elif defect == "wrong_expected_output":
        assert source_row is not None
        source_row["expected_outputs"]["implied_probability"] = Decimal("0.99")
    elif defect == "boolean_value":
        assert source_row is not None
        source_row["inputs"]["price"] = True
    elif defect == "nonfinite_value":
        assert source_row is not None
        source_row["inputs"]["price"] = Decimal("Infinity")
    elif defect == "unit_mismatch":
        mutated["bindings"][0]["input_source_bindings"][0][
            "unit_or_basis"
        ] = "currency"
    elif defect == "fixture_ref_mismatch":
        mutated["bindings"][0]["evidence_summary"]["fixture_ref"] += ".MISSING"
    issues = validator._independent_closed_fixture_contract_issues(
        mutated,
        source_row,
        {str(mutated["canonical_component_id"]): mutated},
    )
    assert any(expected_issue in issue for issue in issues)


@pytest.mark.parametrize(
    "defect",
    [
        "empty_definition",
        "empty_units",
        "empty_domain",
        "empty_state_time",
        "empty_missing_behavior",
        "empty_precision",
        "empty_parameter_policy",
        "empty_fallback",
        "empty_risk_materiality",
        "unproven_zero_input_schema",
        "unproven_zero_output_schema",
    ],
)
def test_specification_pass_rejects_empty_mandatory_semantic_blocks(
    defect: str,
) -> None:
    record = _record(
        "QTT.COMP.TEST.EMPTY_SPEC_BLOCK",
        "test:empty_spec_block",
        [("x", "UNITLESS")],
        [("y", "UNITLESS")],
    )
    definition = record["definition"]
    if defect == "empty_definition":
        definition["complete_mathematical_or_procedural_definition"] = ""
    elif defect == "empty_units":
        definition["units_and_bases"] = {}
    elif defect == "empty_domain":
        definition["domain_and_boundary_behavior"] = {}
    elif defect == "empty_state_time":
        definition["state_and_time_semantics"] = {}
    elif defect == "empty_missing_behavior":
        definition["missing_stale_nonfinite_behavior"] = ""
    elif defect == "empty_precision":
        definition["precision_and_rounding"] = {}
    elif defect == "empty_parameter_policy":
        definition["parameter_schema_and_default_provenance"] = {}
    elif defect == "empty_fallback":
        definition["classical_fallback"] = {}
    elif defect == "empty_risk_materiality":
        definition["risk_materiality"] = ""
    elif defect == "unproven_zero_input_schema":
        definition["input_schema"] = []
        definition["units_and_bases"].pop("x")
        definition.pop("zero_input_proof")
        record["bindings"][0]["input_source_bindings"] = {}
    elif defect == "unproven_zero_output_schema":
        definition["output_schema"] = []
        definition["units_and_bases"].pop("y")
        definition.pop("zero_output_proof")
    else:  # pragma: no cover - the parameter table is closed above
        raise AssertionError(defect)

    with pytest.raises(ValueError, match="FALSE_SPECIFICATION_PASS"):
        _validate_record_shape(record)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("input_type", "UNKNOWN"),
        ("input_type", "UNRESOLVEDTYPE"),
        ("input_type", "MYSTERY_SCALAR"),
        ("input_type", "SOURCE_DECLARED_NUMERIC_OR_SEQUENCE"),
        ("input_unit", "UNSPECIFIED"),
        ("output_unit", "EXACT_RUNTIME_UNIT_REQUIRED"),
        ("units_map", "UNKNOWN"),
        ("state", "REQUIRES_CONTEXT_CLASSIFICATION"),
        ("state", "PENDING_INDEPENDENT_REVIEW"),
        ("boundary", "DOMAIN_UNKNOWN"),
        ("boundary", "TO_BE_CONFIRMED"),
        ("boundary_key", "TBD_PROOF"),
    ],
)
def test_specification_pass_rejects_unresolved_tokens_and_units(
    field: str, value: str
) -> None:
    record = _record(
        "QTT.COMP.TEST.UNRESOLVED_SPEC_TOKEN",
        "test:unresolved_spec_token",
        [("x", "UNITLESS")],
        [("y", "UNITLESS")],
    )
    definition = record["definition"]
    if field == "input_type":
        definition["input_schema"][0]["type"] = value
    elif field == "input_unit":
        definition["input_schema"][0]["unit"] = value
        definition["units_and_bases"]["x"] = value
    elif field == "output_unit":
        definition["output_schema"][0]["unit"] = value
        definition["units_and_bases"]["y"] = value
    elif field == "units_map":
        definition["units_and_bases"]["x"] = value
    elif field == "state":
        definition["state_and_time_semantics"]["state"] = value
    elif field == "boundary":
        definition["domain_and_boundary_behavior"]["invalid"] = value
    elif field == "boundary_key":
        definition["domain_and_boundary_behavior"][value] = "FAIL_CLOSED"
    else:  # pragma: no cover - the parameter table is closed above
        raise AssertionError(field)

    with pytest.raises(ValueError, match="FALSE_SPECIFICATION_PASS"):
        _validate_record_shape(record)


@pytest.mark.parametrize(
    ("proof_ref", "error"),
    [
        ("TBD", "GENERIC_PLACEHOLDER_TERMINAL"),
        ("UNKNOWN", "FALSE_SPECIFICATION_PASS"),
        ("UNRESOLVED_PROOF", "FALSE_SPECIFICATION_PASS"),
        ("SELF_ATTESTED_EXTERNAL_PROOF", "FALSE_SPECIFICATION_PASS"),
    ],
)
def test_not_applicable_semantics_require_resolved_proof(
    proof_ref: str, error: str
) -> None:
    record = _record(
        "QTT.COMP.TEST.UNRESOLVED_NA_PROOF",
        "test:unresolved_na_proof",
        [("x", "UNITLESS")],
        [("y", "UNITLESS")],
    )
    record["definition"]["classical_fallback"] = {
        "not_applicable": True,
        "proof_ref": proof_ref,
    }
    with pytest.raises(ValueError, match=error):
        _validate_record_shape(record)


def test_independent_specification_predicate_rejects_closed_world_defects() -> None:
    from tools import validate_pr169_qku_comp_control1 as validator

    mutations = []
    unresolved_type = _record(
        "QTT.COMP.TEST.INDEPENDENT_UNRESOLVED_TYPE",
        "test:independent_unresolved_type",
        [("x", "UNITLESS")],
        [("y", "UNITLESS")],
    )["definition"]
    unresolved_type["input_schema"][0]["type"] = "UNRESOLVEDTYPE"
    mutations.append(unresolved_type)

    unknown_type = copy.deepcopy(unresolved_type)
    unknown_type["input_schema"][0]["type"] = "MYSTERY_SCALAR"
    mutations.append(unknown_type)

    unresolved_key = copy.deepcopy(unresolved_type)
    unresolved_key["input_schema"][0]["type"] = "NUMBER"
    unresolved_key["domain_and_boundary_behavior"]["TBD_PROOF"] = "FAIL_CLOSED"
    mutations.append(unresolved_key)

    self_attested_na = copy.deepcopy(unresolved_type)
    self_attested_na["input_schema"][0]["type"] = "NUMBER"
    self_attested_na["classical_fallback"] = {
        "not_applicable": True,
        "proof_ref": "SELF_ATTESTED_EXTERNAL_PROOF",
    }
    mutations.append(self_attested_na)

    for definition in mutations:
        assert validator._independent_specification_issues(definition)


@pytest.mark.parametrize(
    "defect",
    [
        "missing_port",
        "undeclared_port",
        "unresolved_source",
        "verbose_type_mismatch",
        "verbose_unit_mismatch",
    ],
)
def test_exact_typed_input_source_binding_controls_readiness_and_compute(
    defect: str,
) -> None:
    record = _record(
        "QTT.COMP.TEST.TYPED_INPUT_SOURCE",
        "test:typed_input_source",
        [("x", "UNITLESS")],
        [("y", "UNITLESS")],
    )
    binding = record["bindings"][0]
    if defect == "missing_port":
        binding["input_source_bindings"] = {}
    elif defect == "undeclared_port":
        binding["input_source_bindings"] = {
            "x": "CALLER_TYPED_FIXTURE",
            "not_an_input": "CALLER_TYPED_FIXTURE",
        }
    elif defect == "unresolved_source":
        binding["input_source_bindings"] = {"x": "UNKNOWN"}
    elif defect == "verbose_type_mismatch":
        binding["input_source_bindings"] = [
            {
                "input_name": "x",
                "source_ref": "CALLER_TYPED_FIXTURE",
                "declared_type": "STRING",
                "unit_or_basis": "UNITLESS",
            }
        ]
    elif defect == "verbose_unit_mismatch":
        binding["input_source_bindings"] = [
            {
                "input_name": "x",
                "source_ref": "CALLER_TYPED_FIXTURE",
                "declared_type": "NUMBER",
                "unit_or_basis": "PRICE",
            }
        ]
    else:  # pragma: no cover - the parameter table is closed above
        raise AssertionError(defect)

    # Inputs/context PASS may not coexist with an incomplete typed source map.
    with pytest.raises(ValueError, match="FALSE_TYPED_INPUT_SOURCE_BINDING"):
        _validate_record_shape(record)

    # Downgrading the truthful readiness dimensions still must not leave a
    # compute-capable agent policy behind.
    binding["readiness"]["specification"] = "REQUIRED"
    binding["readiness"]["inputs"] = "REQUIRED"
    binding["readiness"]["context"] = "REQUIRED"
    binding["derived_state"] = "SPECIFICATION_REQUIRED"
    binding["exact_resolution_action_or_null"] = (
        f"MISSING_INPUT_BINDING: {record['canonical_component_id']}@1.0"
    )
    with pytest.raises(ValueError, match="FALSE_AGENT_COMPUTE_ELIGIBILITY"):
        _validate_record_shape(record)


def test_exact_verbose_input_source_binding_is_admissible() -> None:
    record = _record(
        "QTT.COMP.TEST.EXACT_VERBOSE_INPUT_SOURCE",
        "test:exact_verbose_input_source",
        [("x", "UNITLESS")],
        [("y", "UNITLESS")],
    )
    record["bindings"][0]["input_source_bindings"] = [
        {
            "input_name": "x",
            "source_ref": "CALLER_TYPED_FIXTURE",
            "declared_type": "NUMBER",
            "unit_or_basis": "UNITLESS",
        }
    ]
    _validate_record_shape(record)


def test_requirement_owned_input_cannot_be_claimed_as_fixture_bound() -> None:
    from tools import validate_pr169_qku_comp_control1 as validator

    upstream = _record(
        "QTT.COMP.TEST.REQUIREMENT_SOURCE",
        "test:requirement_source",
        [("x", "UNITLESS")],
        [("upstream_value", "UNITLESS")],
    )
    dependent = _record(
        "QTT.COMP.TEST.REQUIREMENT_CONSUMER",
        "test:requirement_consumer",
        [("upstream_value", "UNITLESS")],
        [("y", "UNITLESS")],
        requirements=[
            _requirement(
                upstream["canonical_component_id"],
                "upstream_value",
                "upstream_value",
                "CANONICAL_UPSTREAM_VALUE",
            )
        ],
    )
    _validate_record_shape(dependent)
    validator._validate_record(dependent)

    false_fixture = copy.deepcopy(dependent)
    source_binding = false_fixture["bindings"][0]["input_source_bindings"][0]
    source_binding["source_ref"] = "CALLER_TYPED_FIXTURE"
    source_binding.pop("producer_output_name")
    source_binding["binding_state"] = "EXACT_TYPED_FIXTURE_BINDING"
    with pytest.raises(ValueError, match="FALSE_TYPED_INPUT_SOURCE_BINDING"):
        _validate_record_shape(false_fixture)
    with pytest.raises(
        validator.InvariantError, match="FALSE_TYPED_INPUT_SOURCE_BINDING"
    ):
        validator._validate_record(false_fixture)


def test_closed_formula_decimal_oracles_are_independent() -> None:
    implied = _record(
        "QTT.COMP.FORMULA.IMPLIED_PROBABILITY",
        "qtt.computation_control.native:decimal_implied_probability",
        [("price", "PRICE"), ("payout", "PRICE")],
        [("implied_probability", "PROBABILITY")],
    )
    edge = _record(
        "QTT.COMP.FORMULA.PROBABILITY_EDGE",
        "qtt.computation_control.native:decimal_probability_edge",
        [("p_model", "PROBABILITY"), ("implied_probability", "PROBABILITY")],
        [("probability_edge", "PROBABILITY")],
        requirements=[
            _requirement(
                implied["canonical_component_id"],
                "implied_probability",
                "implied_probability",
                "MARKET_IMPLIED_PROBABILITY",
            )
        ],
    )
    mid = _record(
        "QTT.COMP.FORMULA.MID_PRICE",
        "qtt.computation_control.native:decimal_mid_price",
        [("best_bid", "PRICE"), ("best_ask", "PRICE")],
        [("mid_price", "PRICE")],
    )
    spread = _record(
        "QTT.COMP.FORMULA.SPREAD",
        "qtt.computation_control.native:decimal_spread",
        [("best_bid", "PRICE"), ("best_ask", "PRICE")],
        [("spread", "PRICE_DELTA")],
    )
    relative = _record(
        "QTT.COMP.FORMULA.RELATIVE_SPREAD",
        "qtt.computation_control.native:decimal_relative_spread",
        [("spread", "PRICE_DELTA"), ("mid_price", "PRICE")],
        [("relative_spread", "RATIO")],
        requirements=[
            _requirement(mid["canonical_component_id"], "mid_price", "mid_price", "MID"),
            _requirement(spread["canonical_component_id"], "spread", "spread", "SPREAD"),
        ],
    )
    records = [implied, edge, mid, spread, relative]
    plane = QKUComputationControlPlaneV1(records=records)
    context = {"market": "TEST", "venue": "LOCAL", "mode": "STATIC_VALIDATION"}
    probability = plane.compute(
        edge["canonical_component_id"],
        {
            "p_model": {"value": Decimal("0.58"), "unit": "PROBABILITY"},
            "price": {"value": Decimal("0.43"), "unit": "PRICE"},
            "payout": {"value": Decimal("1"), "unit": "PRICE"},
        },
        context,
    )
    with localcontext(Context(prec=34, rounding=ROUND_HALF_EVEN)):
        expected_implied = Decimal("0.43") / Decimal("1")
        expected_edge = Decimal("0.58") - expected_implied
    assert probability.outputs == {"probability_edge": expected_edge}

    relative_receipt = plane.compute(
        relative["canonical_component_id"],
        {
            "best_bid": {"value": Decimal("0.42"), "unit": "PRICE"},
            "best_ask": {"value": Decimal("0.46"), "unit": "PRICE"},
        },
        context,
    )
    with localcontext(Context(prec=34, rounding=ROUND_HALF_EVEN)):
        expected_mid = (Decimal("0.42") + Decimal("0.46")) / Decimal("2")
        expected_spread = Decimal("0.46") - Decimal("0.42")
        expected_relative = expected_spread / expected_mid
    assert relative_receipt.outputs == {"relative_spread": expected_relative}
    assert relative_receipt.nodes_executed == 3

    with pytest.raises(ComputationControlError, match="INVALID_DOMAIN"):
        plane.compute(
            implied["canonical_component_id"],
            {
                "price": {"value": Decimal("0.2"), "unit": "PRICE"},
                "payout": {"value": Decimal("0"), "unit": "PRICE"},
            },
            context,
        )


def test_closed_decimal_context_and_epsilon_boundaries_are_pinned() -> None:
    implied = NATIVE_IMPLEMENTATIONS[
        "qtt.computation_control.native:decimal_implied_probability"
    ]
    midpoint = NATIVE_IMPLEMENTATIONS[
        "qtt.computation_control.native:decimal_mid_price"
    ]
    relative = NATIVE_IMPLEMENTATIONS[
        "qtt.computation_control.native:decimal_relative_spread"
    ]
    probability_edge = NATIVE_IMPLEMENTATIONS[
        "qtt.computation_control.native:decimal_probability_edge"
    ]

    expected_third = Decimal("0.3333333333333333333333333333333333")
    for ambient_precision in (6, 28, 60):
        with localcontext(Context(prec=ambient_precision, rounding=ROUND_HALF_EVEN)):
            assert implied({"price": "1", "payout": "3"}) == {
                "implied_probability": expected_third
            }
            assert relative({"spread": "1", "mid_price": "3"}) == {
                "relative_spread": expected_third
            }

    large_bid = Decimal("0.12345678901234567890123456789012345")
    large_ask = Decimal("0.22345678901234567890123456789012345")
    with localcontext(Context(prec=34, rounding=ROUND_HALF_EVEN)):
        expected_midpoint = (large_bid + large_ask) / Decimal("2")
    assert midpoint({"best_bid": large_bid, "best_ask": large_ask}) == {
        "mid_price": expected_midpoint
    }

    for function, values in (
        (implied, {"price": "0", "payout": "0.0000000001"}),
        (relative, {"spread": "0", "mid_price": "0.0000000001"}),
        (probability_edge, {"p_model": "0.5", "implied_probability": "1.1"}),
    ):
        with pytest.raises(ComputationControlError, match="INVALID_DOMAIN"):
            function(values)

    for value in (True, 0.5):
        with pytest.raises(
            ComputationControlError, match="BINARY_FLOAT_MONEY_BOUNDARY"
        ):
            implied({"price": value, "payout": "1"})
    for value in (Decimal("NaN"), Decimal("Infinity")):
        with pytest.raises(ComputationControlError, match="NONFINITE_INPUT"):
            implied({"price": value, "payout": "1"})


def _restrict_to_status_explain(record: dict[str, Any]) -> None:
    for binding in record["bindings"]:
        for policy in binding["agent_access_policy"].values():
            policy["control_plane_operations"] = ["status", "explain"]
        binding["derived_state"] = "SPECIFIED"


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
    package = importlib.import_module("src.qtt.computation_control")
    assert package.__all__ == ["QKUComputationControlPlaneV1"]


def test_requirements_compile_and_selected_subgraph_memoizes_once() -> None:
    records, allowlist, calls = _diamond_records()
    plane = QKUComputationControlPlaneV1(
        records=records,
        implementation_allowlist=allowlist,
        trusted_memoizable_refs={"test:common"},
    )
    plan = plane.resolve(
        "QTT.COMP.TEST.ROOT", _context(), agent_id="parameter_selector_agent"
    )
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
        agent_id="parameter_selector_agent",
    )
    assert receipt.outputs["result"] == 15
    assert receipt.nodes_executed == 4
    assert receipt.shared_invocations_reused == 1
    assert calls == {"common": 1, "left": 1, "right": 1, "root": 1}
    diagnostics = plane._diagnostics()
    assert diagnostics["runtime_registry_file_reads_after_initialization"] == 0
    assert diagnostics["per_request_full_registry_iterations"] == 0
    assert diagnostics["unrelated_component_executions"] == 0


def test_runtime_index_observer_detects_a_real_full_registry_iteration() -> None:
    record = _record(
        "QTT.COMP.TEST.INDEX_OBSERVER",
        "test:index_observer",
        [("x", "UNITLESS")],
        [("y", "UNITLESS")],
    )
    plane = QKUComputationControlPlaneV1(
        records=[record],
        implementation_allowlist={
            "test:index_observer": lambda values: {"y": values["x"]}
        },
    )

    # This deliberate defect probes the actual Mapping.__iter__ path.  A
    # constant diagnostic field would remain zero and fail this assertion.
    with plane._request_access_scope():
        assert list(plane._registry.pin().indexes.records_by_key) == [
            (record["canonical_component_id"], record["semantic_version"])
        ]
    injected = plane._diagnostics()
    assert injected["full_registry_iterations_last_request"] == 1
    assert injected["per_request_full_registry_iterations"] == 1

    # A normal indexed request must not iterate the record index.  The
    # cumulative count retains the injected defect while the request-local
    # counter proves this resolve was clean.
    plan = plane.resolve(record["canonical_component_id"], _context())
    assert plan.root_component_id == record["canonical_component_id"]
    clean = plane._diagnostics()
    assert clean["full_registry_iterations_last_request"] == 0
    assert clean["per_request_full_registry_iterations"] == 1
    assert clean["records_examined_last_request"] == 1


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


def test_fallback_partition_range_preserves_exact_canonical_prefix_and_is_independently_validated(
    tmp_path: Path,
) -> None:
    from tools import validate_pr169_qku_comp_control1 as validator

    record = _record(
        "QTT.COMP.ECONOMIC_MODEL.TEST_CASE",
        "test:economic_model",
        [],
        [("result", "UNITLESS")],
    )
    _write_registry_layout([record], tmp_path, force_layout="sharded")
    manifest = json.loads((tmp_path / REGISTRY_MANIFEST).read_text(encoding="utf-8"))
    assert len(manifest["partitions"]) == 1
    partition = manifest["partitions"][0]
    assert partition["file"] == "registry.part-other-economic-model.jsonl"
    assert partition["range_start"] == "QTT.COMP.ECONOMIC_MODEL."
    assert partition["range_end"] == "QTT.COMP.ECONOMIC_MODEL.\uffff"
    validator._validate_manifest_declared_ranges(tmp_path, manifest)

    prior_defect = copy.deepcopy(manifest)
    prior_defect["partitions"][0]["range_start"] = "QTT.COMP.ECONOMIC-MODEL."
    prior_defect["partitions"][0]["range_end"] = "QTT.COMP.ECONOMIC-MODEL.\uffff"
    with pytest.raises(
        validator.InvariantError, match="SHARD_MANIFEST_DECLARED_RANGE"
    ):
        validator._validate_manifest_declared_ranges(tmp_path, prior_defect)
    (tmp_path / REGISTRY_MANIFEST).write_text(
        json.dumps(prior_defect, sort_keys=True) + "\n", encoding="utf-8"
    )
    with pytest.raises(
        validator.InvariantError, match="SHARD_MANIFEST_DECLARED_RANGE"
    ):
        validator._detect_layout(tmp_path)

    candidate_dir = tmp_path / "candidate"
    candidate = _record(
        "QTT.COMP.CANDIDATE.TEST_CASE",
        "test:candidate",
        [],
        [("result", "UNITLESS")],
    )
    _write_registry_layout([candidate], candidate_dir, force_layout="sharded")
    candidate_manifest = json.loads(
        (candidate_dir / REGISTRY_MANIFEST).read_text(encoding="utf-8")
    )
    candidate_partition = candidate_manifest["partitions"][0]
    assert candidate_partition["file"] == "registry.part-other-research.jsonl"
    assert candidate_partition["range_start"] == "QTT.COMP.CANDIDATE."
    assert candidate_partition["range_end"] == "QTT.COMP.CANDIDATE.\uffff"
    validator._validate_manifest_declared_ranges(
        candidate_dir, candidate_manifest
    )


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


def test_synthetic_expansion_proof_stays_temporary_and_reaches_generic_owners(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Exercise every expansion class without admitting test rows to production."""

    base = _record(
        "QTT.COMP.TEST.EXPANSION_BASE",
        "test:expansion_base",
        [("x", "UNITLESS")],
        [("y", "UNITLESS")],
    )
    base["definition"]["parameter_schema_and_default_provenance"] = {
        "parameters": [
            {
                "name": "scale",
                "type": "DECIMAL",
                "unit": "UNITLESS",
                "minimum": "0",
                "default_provenance": "CONTROL1_TEST_POLICY_CUSTODY",
            }
        ],
        "default_provenance": "CONTROL1_TEST_POLICY_CUSTODY",
    }

    # Provenance-only reuse is a separate compiler action from adding a public
    # alias.  A new occurrence already mapped to the stable canonical identity
    # adds provenance and nothing else.
    provenance_only = copy.deepcopy(base)
    provenance_only["provenance"][0].update(
        {
            "source_row_ref": "SYNTHETIC_PROVENANCE_ONLY",
            "source_local_identity_or_name": "EXPANSION_PROVENANCE_ONLY",
            "canonical_target_ref": base["canonical_component_id"],
        }
    )
    after_provenance, _, provenance_report = _compile_expansion_batch(
        [base],
        _expansion_batch(
            [{"record": provenance_only}],
            "STACK_READY",
            batch_id="BATCH.TEST.PROVENANCE.ONLY",
        ),
    )
    assert provenance_report["outcomes"][0]["decision"] == "EXISTING_ID_UPDATE"
    assert len(after_provenance) == 1
    assert len(after_provenance[0]["provenance"]) == 2
    assert not after_provenance[0]["relations"]

    alias = copy.deepcopy(base)
    alias_id = "QTT.COMP.TEST.EXPANSION_ALIAS"
    alias["canonical_component_id"] = alias_id
    alias["uses"]["qku_role_bindings"][0][
        "stack_root_or_direct_component"
    ] = alias_id
    alias["provenance"][0].update(
        {
            "source_row_ref": "SYNTHETIC_ALIAS_AND_PROVENANCE_ONLY",
            "source_local_identity_or_name": "EXPANSION_ALIAS",
            "canonical_target_ref": alias_id,
        }
    )
    alias_batch = _expansion_batch(
        [
            {
                "record": alias,
                "equivalence_decision": "YES",
                "candidate_alias": "EXPANSION_ALIAS",
            }
        ],
        "STACK_READY",
        batch_id="BATCH.TEST.EXACT_ALIAS.PROVENANCE",
    )
    after_alias, _, alias_report = _compile_expansion_batch(
        after_provenance, alias_batch
    )
    assert len(after_alias) == 1
    assert alias_report["outcomes"][0]["decision"] == "REUSED"
    assert any(
        relation.get("relation_type") == "ALIAS_OF"
        for relation in after_alias[0]["relations"]
    )
    assert len(after_alias[0]["provenance"]) == 3

    contextual_update = copy.deepcopy(after_alias[0])
    contextual_update["bindings"][0]["selected_parameter_policy"] = {
        **contextual_update["bindings"][0]["selected_parameter_policy"],
        "policy_id": "PARAM.TEST.EXPANSION.UPDATED",
        "version": "2.0",
        "defaults": {"scale": "1"},
        "default_provenance": "TEST_ONLY_TYPED_POLICY",
    }
    added_binding = copy.deepcopy(contextual_update["bindings"][0])
    added_binding.update(
        {
            "binding_id": "BIND.TEST.EXPANSION.ALT",
            "market": "TEST_ALT",
            "context_selector": {"market": "TEST_ALT", "venue": "LOCAL"},
        }
    )
    contextual_update["bindings"].append(added_binding)
    after_context, _, context_report = _compile_expansion_batch(
        after_alias,
        _expansion_batch(
            [{"record": contextual_update}],
            "STACK_READY",
            batch_id="BATCH.TEST.BINDING.PARAMETER",
        ),
    )
    assert context_report["outcomes"][0]["decision"] == "EXISTING_ID_UPDATE"
    assert {binding["binding_id"] for binding in after_context[0]["bindings"]} == {
        "BIND.TEST.EXPANSION_BASE",
        "BIND.TEST.EXPANSION.ALT",
    }

    # A new implementation version on a reused semantic record is admitted
    # only after the fixed build-owned verifier actually executes.  The test
    # installs a bounded verifier into the build-only catalog; caller-authored
    # proof labels remain irrelevant.
    control_module = importlib.import_module(
        "src.qtt.computation_control.control"
    )
    verifier_calls: list[tuple[str, str]] = []

    def verify_expansion_base_v2(
        candidate_record: Mapping[str, Any],
        target_record: Mapping[str, Any],
        implementation: Mapping[str, Any],
    ) -> tuple[str, ...]:
        verifier_calls.append(
            (
                str(target_record["canonical_component_id"]),
                str(implementation["implementation_version"]),
            )
        )
        assert candidate_record["canonical_component_id"] == target_record[
            "canonical_component_id"
        ]
        def reference(payload: Mapping[str, int]) -> dict[str, int]:
            return {"y": payload["x"]}

        def candidate_v2(payload: Mapping[str, int]) -> dict[str, int]:
            return {"y": payload["x"] * 1}

        for value in (-5, 0, 11):
            payload = {"x": value}
            assert candidate_v2(payload) == reference(payload)
        return (
            "TEST_BUILD_OWNED_DIFFERENTIAL::EXPANSION_BASE_V2",
            "TEST_BUILD_OWNED_BOUNDARY::EXPANSION_BASE_V2",
        )

    monkeypatch.setattr(
        control_module,
        "_BUILD_OWNED_IMPLEMENTATION_VERIFIERS",
        {"test:expansion_base_v2": verify_expansion_base_v2},
    )
    implementation_update = copy.deepcopy(after_context[0])
    implementation_update["definition"]["implementation_versions"].append(
        {
            **copy.deepcopy(
                implementation_update["definition"]["implementation_versions"][0]
            ),
            "implementation_version": "impl-2.0",
            "callable_or_solver_ref": "test:expansion_base_v2",
        }
    )
    after_implementation, _, implementation_report = _compile_expansion_batch(
        after_context,
        _expansion_batch(
            [{"record": implementation_update}],
            "STACK_READY",
            batch_id="BATCH.TEST.VERIFIED.IMPLEMENTATION",
        ),
    )
    assert implementation_report["outcomes"][0]["decision"] == (
        "EXISTING_ID_UPDATE"
    )
    assert verifier_calls == [(base["canonical_component_id"], "impl-2.0")]
    assert {
        row["implementation_version"]
        for row in after_implementation[0]["definition"]["implementation_versions"]
    } == {"impl-1.0", "impl-2.0"}
    assert (
        "TEST_BUILD_OWNED_DIFFERENTIAL::EXPANSION_BASE_V2"
        in after_implementation[0]["definition"]["equivalence_proof_refs"]
    )

    family = copy.deepcopy(after_implementation[0])
    family_id = "QTT.COMP.TEST.EXPANSION_FAMILY_MEMBER"
    family["canonical_component_id"] = family_id
    family["bindings"] = [copy.deepcopy(family["bindings"][0])]
    family["bindings"][0].update(
        {
            "binding_id": "BIND.TEST.EXPANSION.FAMILY",
            "market": "TEST_FAMILY",
            "context_selector": {"market": "TEST_FAMILY", "venue": "LOCAL"},
        }
    )
    for role in family["uses"]["qku_role_bindings"]:
        if role.get("stack_root_or_direct_component") == base["canonical_component_id"]:
            role["stack_root_or_direct_component"] = family_id
    family["provenance"] = [
        {
            **copy.deepcopy(family["provenance"][0]),
            "source_row_ref": "SYNTHETIC_COMPATIBLE_FAMILY_MEMBER",
            "source_local_identity_or_name": "EXPANSION_FAMILY_MEMBER",
            "canonical_target_ref": family_id,
        }
    ]
    family["relations"] = [
        {
            "relation_type": "FAMILY_BINDING_OF",
            "canonical_target_ref": base["canonical_component_id"],
            "proof_refs": [
                "tests/pr169_qku_comp_control1/test_control1.py::"
                "test_synthetic_expansion_proof_stays_temporary_and_reaches_generic_owners"
            ],
        }
    ]
    after_family, _, family_report = _compile_expansion_batch(
        after_implementation,
        _expansion_batch(
            [
                {
                    "record": family,
                    "equivalence_decision": "NO",
                    "nonidentical_relation": "FAMILY_COMPATIBLE",
                }
            ],
            "STACK_READY",
            batch_id="BATCH.TEST.FAMILY",
        ),
    )
    assert family_report["outcomes"][0]["decision"] == "FAMILY_COMPATIBLE_REUSED"
    assert len(after_family) == 1

    similar = _record(
        "QTT.COMP.TEST.EXPANSION_SIGNED_DISTANCE",
        "test:signed_distance",
        [("left", "UNITLESS"), ("right", "UNITLESS")],
        [("signed_distance", "UNITLESS")],
    )
    similar["definition"][
        "complete_mathematical_or_procedural_definition"
    ] = "signed_distance = left - right"
    true_new = _record(
        "QTT.COMP.TEST.EXPANSION_ABSOLUTE_DISTANCE",
        "test:absolute_distance",
        [("left", "UNITLESS"), ("right", "UNITLESS")],
        [("absolute_distance", "UNITLESS")],
    )
    true_new["definition"][
        "complete_mathematical_or_procedural_definition"
    ] = "absolute_distance = abs(left - right)"
    quantum = _record(
        "QTT.COMP.TEST.EXPANSION_QUBO_ENCODING",
        "test:qubo_encoding",
        [("x", "UNITLESS")],
        [("energy", "UNITLESS")],
    )
    quantum["definition"]["component_kind"] = "QUANTUM_FORMULATION"
    quantum["definition"]["complete_mathematical_or_procedural_definition"] = (
        "test-only QUBO encoding of the original scalar objective"
    )
    quantum["definition"]["quantum"].update(
        {
            "applicability_state": "MAPPED",
            "original_economic_problem_ref": base["canonical_component_id"],
            "problem_family": "TEST_ONLY_QUBO",
            "selected_formulation_or_none": "QUBO",
            "variable_encoding": "BINARY_TEST_VARIABLE",
            "objective_map": "energy = x",
            "constraint_map": "NO_CONSTRAINTS",
            "inverse_map": "x = binary_test_variable",
            "original_model_feasibility_check": "TEST_ONLY_EXACT",
            "same_formulation_classical_comparator": base[
                "canonical_component_id"
            ],
            "local_exact_or_small_instance_parity": "TEST_ONLY_PROOF_CANDIDATE",
            "fallback": base["canonical_component_id"],
            "maturity_ceiling": "SPECIFIED",
        }
    )
    quantum["relations"] = [
        {
            "relation_type": "ENCODES_OR_MAPS",
            "canonical_target_ref": base["canonical_component_id"],
            "proof_refs": [
                "tests/pr169_qku_comp_control1/test_control1.py::"
                "test_synthetic_expansion_proof_stays_temporary_and_reaches_generic_owners"
            ],
        }
    ]
    candidate, delta, distinct_report = _compile_expansion_batch(
        after_family,
        _expansion_batch(
            [
                {
                    "record": similar,
                    "equivalence_decision": "NO",
                    "nonidentical_relation": "DISTINCT",
                },
                {
                    "record": true_new,
                    "equivalence_decision": "NO",
                    "nonidentical_relation": "DISTINCT",
                },
                {
                    "record": quantum,
                    "equivalence_decision": "NO",
                    "nonidentical_relation": "DISTINCT",
                },
            ],
            "STACK_READY",
            batch_id="BATCH.TEST.DISTINCT.NEW.QUANTUM",
        ),
    )
    assert {row["decision"] for row in distinct_report["outcomes"]} == {"DISTINCT"}
    assert len(candidate) == 4

    unverified_implementation = copy.deepcopy(candidate[0])
    unverified_implementation["definition"]["implementation_versions"].append(
        {
            **copy.deepcopy(
                unverified_implementation["definition"]["implementation_versions"][0]
            ),
            "implementation_version": "unverified-test-implementation",
            "callable_or_solver_ref": "test:unverified_expansion_implementation",
        }
    )
    with pytest.raises(
        ValueError, match="NEW_REUSED_IMPLEMENTATION_REQUIRES_BUILD_OWNED_VERIFIER"
    ):
        _compile_expansion_batch(
            candidate,
            _expansion_batch(
                [{"record": unverified_implementation}],
                "STACK_READY",
                batch_id="BATCH.TEST.UNVERIFIED.IMPLEMENTATION",
            ),
        )

    unverified_qku = copy.deepcopy(candidate[0])
    unverified_qku["uses"]["qku_role_bindings"].append(
        {
            "qku_id": "QKU.TEST.UNVERIFIED.EXPANSION",
            "role_or_decision_stage": "INTERNAL_SUPPORT",
            "market_family": "TEST",
            "stack_root_or_direct_component": unverified_qku[
                "canonical_component_id"
            ],
            "selection_rule_if_container": None,
            "agent_policy_tags": ["TEST_ONLY"],
            "source_refs": ["tests/pr169_qku_comp_control1/test_control1.py"],
        }
    )
    with pytest.raises(
        ValueError, match="NEW_REUSED_QKU_ROLE_REQUIRES_BUILD_OWNED_VERIFIER"
    ):
        _compile_expansion_batch(
            candidate,
            _expansion_batch(
                [{"record": unverified_qku}],
                "STACK_READY",
                batch_id="BATCH.TEST.UNVERIFIED.QKU",
            ),
        )

    # A true-new computation carries its declared QKU role without cloning a
    # downstream route.  Reused active semantics remain protected by the
    # negative case above.
    true_new_record = next(
        row
        for row in candidate
        if row["canonical_component_id"]
        == "QTT.COMP.TEST.EXPANSION_ABSOLUTE_DISTANCE"
    )
    true_new_qku = true_new_record["uses"]["qku_role_bindings"][0]["qku_id"]
    assert true_new_qku == "QKU.TEST.EXPANSION_ABSOLUTE_DISTANCE"

    # The sole successful existing-record QKU-role addition is the production
    # compiler's narrow RP5C custody lane: source-backed, dormant, no runtime
    # root, and status/explain only.  This proves preservation without granting
    # compute authority.
    dormant_target = _rp5c_nonruntime_role_record()
    dormant_component_id = dormant_target["canonical_component_id"]
    dormant_action = f"MISSING_SEMANTIC_SPECIFICATION: {dormant_component_id}"
    dormant_target["definition"][
        "complete_mathematical_or_procedural_definition"
    ] = dormant_action
    dormant_target["uses"]["qku_role_bindings"] = []
    dormant_ineligibility = copy.deepcopy(dormant_target["relations"].pop(1))
    dormant_binding = dormant_target["bindings"][0]
    for dimension in ("specification", "implementation", "inputs", "oracle", "context"):
        dormant_binding["readiness"][dimension] = "REQUIRED"
    dormant_binding["derived_state"] = "RETIRED"
    dormant_binding["exact_resolution_action_or_null"] = dormant_action
    dormant_binding["agent_access_policy"] = {
            "research_agent": {
                "control_plane_operations": ["status", "explain"],
                "mode_ceiling": "NOT_ELIGIBLE",
                "order_release_authority": False,
                "source_truth_authority": False,
            }
        }
    dormant_candidate = copy.deepcopy(dormant_target)
    dormant_candidate["uses"]["qku_role_bindings"].append(
        {
            "qku_id": "QKU-RP5C-PRESERVED-SYNTHETIC-PROOF",
            "role_or_decision_stage": "source_role",
            "market_family": "unknown_needs_review",
            "stack_root_or_direct_component": None,
            "selection_rule_if_container": None,
            "agent_policy_tags": [],
            "source_refs": [
                "docs/master_plan/generated/rp5c/formula_assignment_library.jsonl",
                "RP5C.SOURCE.ROW.SYNTHETIC.PROOF",
            ],
            "exact_resolution_action": dormant_action,
            "runtime_root_eligibility": (
                "INELIGIBLE_UNTIL_COMPLETE_SEMANTICS_AND_DIRECT_ROOT_PROOF"
            ),
        }
    )
    dormant_ineligibility["preserved_qku_role_count"] = 1
    dormant_candidate["relations"].append(dormant_ineligibility)
    dormant_batch = _expansion_batch(
        [{"record": dormant_candidate}],
        "SPECIFIED",
        batch_id="BATCH.TEST.RP5C.QKU.ROLE.PRESERVATION",
    )
    dormant_batch["source_refs"].append(
        "docs/master_plan/generated/rp5c/identity_deduplication_ledger.jsonl"
    )
    dormant_compiled, dormant_delta, _ = _compile_expansion_batch(
        [dormant_target], dormant_batch
    )
    assert dormant_delta.changed_component_ids == (dormant_component_id,)
    assert len(dormant_compiled[0]["uses"]["qku_role_bindings"]) == 1
    preserved_role = dormant_compiled[0]["uses"]["qku_role_bindings"][0]
    assert preserved_role["stack_root_or_direct_component"] is None
    assert preserved_role["runtime_root_eligibility"] == (
        "INELIGIBLE_UNTIL_COMPLETE_SEMANTICS_AND_DIRECT_ROOT_PROOF"
    )
    assert dormant_compiled[0]["bindings"][0]["agent_access_policy"][
        "research_agent"
    ]["control_plane_operations"] == ["status", "explain"]
    dormant_reapplied, dormant_second_delta, _ = _compile_expansion_batch(
        dormant_compiled, dormant_batch
    )
    assert dormant_reapplied == dormant_compiled
    assert not dormant_second_delta.changed_component_ids

    # Derive one final transient delta and stage all generic-owner observations
    # from temporary registry truth only.
    cumulative_delta = _derive_registry_update(
        [base], candidate, batch_id="BATCH.TEST.CUMULATIVE.DELTA"
    )
    temporary_registry = tmp_path / "candidate-registry"
    _write_registry_layout(candidate, temporary_registry, force_layout="single")
    staged_candidate, _ = _load_logical_registry(temporary_registry)
    plane = QKUComputationControlPlaneV1(
        records=staged_candidate,
        implementation_allowlist={
            "test:expansion_base": lambda values: {"y": values["x"]},
            "test:expansion_base_v2": lambda values: {"y": values["x"]},
            "test:signed_distance": lambda values: {
                "signed_distance": values["left"] - values["right"]
            },
            "test:absolute_distance": lambda values: {
                "absolute_distance": abs(values["left"] - values["right"])
            },
            "test:qubo_encoding": lambda values: {"energy": values["x"]},
        },
    )
    delta_payload = cumulative_delta.as_dict()
    expected_added_ids = {
        "QTT.COMP.TEST.EXPANSION_SIGNED_DISTANCE",
        "QTT.COMP.TEST.EXPANSION_ABSOLUTE_DISTANCE",
        "QTT.COMP.TEST.EXPANSION_QUBO_ENCODING",
    }
    assert set(cumulative_delta.added_component_ids) == expected_added_ids
    assert cumulative_delta.changed_component_ids == (
        base["canonical_component_id"],
    )

    # The incremental snapshot path and a complete index rebuild must produce
    # the same disposable indexes before any owner projection is consulted.
    base_snapshot = _build_snapshot([base], generation=1)
    replacement, refresh_stats = _apply_registry_update(
        base_snapshot,
        cumulative_delta,
        staged_candidate,
        verify_full_rebuild=True,
    )
    full_rebuild = _build_snapshot(staged_candidate, generation=2)
    assert refresh_stats["full_rebuild_parity"] is True
    assert _index_signature(replacement.indexes) == _index_signature(
        full_rebuild.indexes
    )

    implementation_allowlist = {
        "test:expansion_base": lambda values: {"y": values["x"]},
        "test:expansion_base_v2": lambda values: {"y": values["x"]},
        "test:signed_distance": lambda values: {
            "signed_distance": values["left"] - values["right"]
        },
        "test:absolute_distance": lambda values: {
            "absolute_distance": abs(values["left"] - values["right"])
        },
        "test:qubo_encoding": lambda values: {"energy": values["x"]},
    }
    incremental_plane = QKUComputationControlPlaneV1(
        records=[base], implementation_allowlist=implementation_allowlist
    )
    incremental_stats = incremental_plane._replace_snapshot(
        staged_candidate, cumulative_delta
    )
    assert incremental_stats["changed_index_component_ids"] == sorted(
        cumulative_delta.affected_component_ids
    )

    from src.qtt.agents.pr169_agent_orch1_resolvers import (
        AgentComputationCapabilityV1,
        invoke_computation_capability,
    )
    from src.qtt.pretrade.pr169_pretrade1_resolvers import compute_computation
    from src.qtt.readiness.pr169_readiness1_resolvers import project_computation_status
    from src.qtt.service.pr169_svc1_resolvers import DashboardReadModelService

    selectors = [row["canonical_component_id"] for row in candidate]
    readiness_projection = project_computation_status(
        plane, selectors, _context(), registry_update=delta_payload
    )
    assert {row["selector"] for row in readiness_projection} == set(selectors)
    # Reapplying the same transient delta to a generic projection is
    # idempotent; it does not create state or duplicate rows.
    assert project_computation_status(
        plane, selectors, _context(), registry_update=delta_payload
    ) == readiness_projection

    def without_generation(rows: tuple[dict[str, Any], ...]) -> tuple[Any, ...]:
        normalized = []
        for row in rows:
            copy_row = copy.deepcopy(row)
            copy_row["status"].pop("generation", None)
            normalized.append(copy_row)
        return tuple(normalized)

    incremental_projection = project_computation_status(
        incremental_plane, selectors, _context(), registry_update=delta_payload
    )
    assert without_generation(incremental_projection) == without_generation(
        readiness_projection
    )

    execution_cases = {
        base["canonical_component_id"]: (
            {"x": {"value": 2, "unit": "UNITLESS", "lineage": "TEST_ONLY"}},
            {"y": 2},
        ),
        "QTT.COMP.TEST.EXPANSION_SIGNED_DISTANCE": (
            {
                "left": {
                    "value": 5,
                    "unit": "UNITLESS",
                    "lineage": "TEST_ONLY",
                },
                "right": {
                    "value": 2,
                    "unit": "UNITLESS",
                    "lineage": "TEST_ONLY",
                },
            },
            {"signed_distance": 3},
        ),
        "QTT.COMP.TEST.EXPANSION_ABSOLUTE_DISTANCE": (
            {
                "left": {
                    "value": 2,
                    "unit": "UNITLESS",
                    "lineage": "TEST_ONLY",
                },
                "right": {
                    "value": 5,
                    "unit": "UNITLESS",
                    "lineage": "TEST_ONLY",
                },
            },
            {"absolute_distance": 3},
        ),
        "QTT.COMP.TEST.EXPANSION_QUBO_ENCODING": (
            {"x": {"value": 1, "unit": "UNITLESS", "lineage": "TEST_ONLY"}},
            {"energy": 1},
        ),
    }

    service = DashboardReadModelService(
        tmp_path / "unused-service-artifacts", computation_control=plane
    )
    incremental_service = DashboardReadModelService(
        tmp_path / "unused-incremental-service-artifacts",
        computation_control=incremental_plane,
    )
    for selector, (inputs, expected_outputs) in execution_cases.items():
        pretrade_receipt = compute_computation(
            plane,
            selector,
            inputs,
            _context(),
            consumer="TEST_CONSUMER",
        )
        incremental_receipt = compute_computation(
            incremental_plane,
            selector,
            inputs,
            _context(),
            consumer="TEST_CONSUMER",
        )
        assert pretrade_receipt.outputs == expected_outputs
        assert incremental_receipt.outputs == expected_outputs
        agent_status = invoke_computation_capability(
            plane,
            AgentComputationCapabilityV1.from_mapping(
                {
                    "operation": "status",
                    "selector": selector,
                    "context": _context(),
                    "input_contract": {},
                    "policy": {},
                }
            ),
        )
        assert agent_status["record_state"] == "CANONICAL_ACCEPTED"
        incremental_agent_status = invoke_computation_capability(
            incremental_plane,
            AgentComputationCapabilityV1.from_mapping(
                {
                    "operation": "status",
                    "selector": selector,
                    "context": _context(),
                    "input_contract": {},
                    "policy": {},
                }
            ),
        )
        for status in (agent_status, incremental_agent_status):
            status.pop("generation", None)
        assert incremental_agent_status == agent_status
        service_status = service.computation_status(selector, _context())
        incremental_service_status = incremental_service.computation_status(
            selector, _context()
        )
        for status in (service_status, incremental_service_status):
            status.pop("generation", None)
        assert incremental_service_status == service_status
        assert service_status["record_state"] == "CANONICAL_ACCEPTED"

    # The added binding and parameter policy are visible generically under a
    # second context without a formula-specific downstream row.
    alternative_context = {**_context(), "market": "TEST_ALT"}
    alternative_status = service.computation_status(
        base["canonical_component_id"], alternative_context
    )
    assert alternative_status["binding_id"] == "BIND.TEST.EXPANSION.ALT"
    assert alternative_status["selected_parameter_policy"]["version"] == "2.0"
    alternative_receipt = compute_computation(
        plane,
        base["canonical_component_id"],
        execution_cases[base["canonical_component_id"]][0],
        alternative_context,
        consumer="TEST_CONSUMER",
    )
    assert alternative_receipt.outputs == {"y": 2}

    # Direct alias and true-new QKU selectors reach every generic owner through
    # the same facade.  They are intentionally not separate registry rows.
    indirect_selectors = ("EXPANSION_ALIAS", true_new_qku)
    indirect_readiness = project_computation_status(
        plane, indirect_selectors, _context()
    )
    assert {row["selector"] for row in indirect_readiness} == set(
        indirect_selectors
    )
    for selector in indirect_selectors:
        expected_case = (
            execution_cases[base["canonical_component_id"]]
            if selector == "EXPANSION_ALIAS"
            else execution_cases[
                "QTT.COMP.TEST.EXPANSION_ABSOLUTE_DISTANCE"
            ]
        )
        assert compute_computation(
            plane,
            selector,
            expected_case[0],
            _context(),
            consumer="TEST_CONSUMER",
        ).outputs == expected_case[1]
        status = invoke_computation_capability(
            plane,
            AgentComputationCapabilityV1.from_mapping(
                {
                    "operation": "status",
                    "selector": selector,
                    "context": _context(),
                    "input_contract": {},
                    "policy": {},
                }
            ),
        )
        assert status["record_state"] == "CANONICAL_ACCEPTED"
        assert service.computation_status(selector, _context())[
            "record_state"
        ] == "CANONICAL_ACCEPTED"

    assert not any(tmp_path.rglob("RegistryUpdateV1*"))
    assert temporary_registry != Path(
        "docs/master_plan/generated/pr169_qku_comp_control1"
    )


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
    binding["agent_access_policy"]["parameter_selector_agent"][
        "mode_ceiling"
    ] = "PAPER"
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
        agent_id="parameter_selector_agent",
    )
    assert by_agent.outputs["y"] == 3


def test_pr165_d2_private_ceiling_rejects_unknown_and_governance_compute() -> None:
    record = _record(
        "QTT.COMP.TEST.TRUSTED_AGENT_CEILING",
        "test:trusted_agent_ceiling",
        [("x", "UNITLESS")],
        [("y", "UNITLESS")],
    )
    record["bindings"][0]["agent_access_policy"]["governance_agent"] = {
        "control_plane_operations": ["status", "explain"],
        "mode_ceiling": "STATIC_VALIDATION",
        "order_release_authority": False,
        "source_truth_authority": False,
    }
    plane = QKUComputationControlPlaneV1(
        records=[record],
        implementation_allowlist={
            "test:trusted_agent_ceiling": lambda values: {"y": values["x"]}
        },
    )
    with pytest.raises(ComputationControlError, match="AGENT_ACCESS_DENIED"):
        plane.resolve(
            record["canonical_component_id"],
            _context(),
            agent_id="attacker_agent",
        )
    with pytest.raises(ComputationControlError, match="AGENT_OPERATION_DENIED"):
        plane.compute(
            record["canonical_component_id"],
            {"x": 1},
            _context(),
            agent_id="governance_agent",
        )

    injected = copy.deepcopy(record)
    injected["bindings"][0]["agent_access_policy"]["attacker_agent"] = {
        "control_plane_operations": ["compute"],
        "mode_ceiling": "STATIC_VALIDATION",
        "order_release_authority": False,
        "source_truth_authority": False,
    }
    with pytest.raises(ValueError, match="UNTRUSTED_AGENT_POLICY_PRINCIPAL"):
        _validate_record_shape(injected)

    live_ceiling = copy.deepcopy(record)
    live_ceiling["bindings"][0]["agent_access_policy"][
        "parameter_selector_agent"
    ]["mode_ceiling"] = "LIVE"
    with pytest.raises(ValueError, match="AGENT_POLICY_MODE_EXPANSION"):
        _validate_record_shape(live_ceiling)


def test_independent_agent_validator_does_not_filter_authority_injection() -> None:
    from tools import validate_pr169_qku_comp_control1 as validator

    record = _record(
        "QTT.COMP.TEST.INDEPENDENT_AGENT_CEILING",
        "test:independent_agent_ceiling",
        [("x", "UNITLESS")],
        [("y", "UNITLESS")],
    )
    compute_agents = {
        "parameter_selector_agent",
        "risk_manager_agent",
        "quantum_optimizer_agent",
        "commander_agent",
    }
    record["bindings"][0]["agent_access_policy"] = {
        agent_id: {
            "control_plane_operations": (
                ["resolve", "compute", "status", "explain"]
                if agent_id in compute_agents
                else ["status", "explain"]
            ),
            "mode_ceiling": "STATIC_VALIDATION",
            "order_release_authority": False,
            "source_truth_authority": False,
        }
        for agent_id in validator.EXPECTED_AGENTS
    }
    assert validator._validate_agent_policies([record]) == len(
        validator.EXPECTED_AGENTS
    )

    injected = copy.deepcopy(record)
    injected["bindings"][0]["agent_access_policy"]["attacker_agent"] = {
        "control_plane_operations": ["compute"],
        "mode_ceiling": "STATIC_VALIDATION",
        "order_release_authority": False,
        "source_truth_authority": False,
    }
    with pytest.raises(validator.InvariantError, match="PR165_D2_AGENT_SET"):
        validator._validate_agent_policies([injected])

    governance_compute = copy.deepcopy(record)
    governance_compute["bindings"][0]["agent_access_policy"][
        "governance_agent"
    ]["control_plane_operations"].append("compute")
    with pytest.raises(validator.InvariantError, match="AGENT_ACCESS_ESCALATION"):
        validator._validate_agent_policies([governance_compute])

    live_ceiling = copy.deepcopy(record)
    live_ceiling["bindings"][0]["agent_access_policy"][
        "parameter_selector_agent"
    ]["mode_ceiling"] = "LIVE"
    with pytest.raises(validator.InvariantError, match="AGENT_ACCESS_ESCALATION"):
        validator._validate_agent_policies([live_ceiling])


_SCALE_PROBE_SEED = 169_10_000
_SCALE_ROOT_ID = "QTT.COMP.SCALE.SELECTED.RELATIVE_SPREAD"
_SCALE_NATIVE_STACK_IDENTITY = "qtt.computation_control.native:stack_identity"


def _fixed_seed_structural_scale_records(record_count: int) -> list[dict[str, Any]]:
    """Create a temporary executable registry; no row is ever published."""

    if record_count < 3:
        raise ValueError("structural scale probe requires at least three records")
    mid_id = "QTT.COMP.SCALE.SELECTED.MID_PRICE"
    spread_id = "QTT.COMP.SCALE.SELECTED.SPREAD"
    selected = [
        _record(
            mid_id,
            "qtt.computation_control.native:decimal_mid_price",
            [("best_bid", "PRICE"), ("best_ask", "PRICE")],
            [("mid_price", "PRICE")],
        ),
        _record(
            spread_id,
            "qtt.computation_control.native:decimal_spread",
            [("best_bid", "PRICE"), ("best_ask", "PRICE")],
            [("spread", "PRICE_DELTA")],
        ),
        _record(
            _SCALE_ROOT_ID,
            "qtt.computation_control.native:decimal_relative_spread",
            [("spread", "PRICE_DELTA"), ("mid_price", "PRICE")],
            [("relative_spread", "RATIO")],
            requirements=[
                _requirement(mid_id, "mid_price", "mid_price", "MID_PRICE_DENOMINATOR"),
                _requirement(spread_id, "spread", "spread", "ABSOLUTE_SPREAD_NUMERATOR"),
            ],
        ),
    ]
    unrelated = [
        _record(
            f"QTT.COMP.SCALE.UNRELATED.{index:08d}",
            _SCALE_NATIVE_STACK_IDENTITY,
            [("result", "UNITLESS")],
            [("result", "UNITLESS")],
            binding_id=f"BIND.SCALE.UNRELATED.{index:08d}",
        )
        for index in range(record_count - len(selected))
    ]
    records = [*selected, *unrelated]
    # Source order is reproducibly non-canonical.  The official layout writer
    # and facade must derive the same logical registry and indexes regardless.
    random.Random(_SCALE_PROBE_SEED).shuffle(records)
    return records


@pytest.mark.parametrize("record_count", [2_000, 10_000])
def test_fixed_seed_structural_scale_probe_real_layout_resolve_compute(
    record_count: int,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    records = _fixed_seed_structural_scale_records(record_count)
    single_root = tmp_path / f"single-{record_count}"
    sharded_root = tmp_path / f"sharded-{record_count}"
    single_metadata = _write_registry_layout(
        records, single_root, force_layout="single"
    )
    sharded_metadata = _write_registry_layout(
        records, sharded_root, force_layout="sharded"
    )
    assert single_metadata["row_count"] == record_count
    assert sharded_metadata["row_count"] == record_count
    assert single_metadata["layout"] == "SINGLE_JSONL"
    assert sharded_metadata["layout"] == "DETERMINISTIC_SHARDED_JSONL"
    assert sharded_metadata["shard_count"] > 0

    single_rows, single_layout = _load_logical_registry(single_root)
    sharded_rows, sharded_layout = _load_logical_registry(sharded_root)
    record_key = lambda row: (
        row["canonical_component_id"],
        row["semantic_version"],
    )
    assert sorted(single_rows, key=record_key) == sorted(
        sharded_rows, key=record_key
    )
    assert len(single_rows) == record_count
    assert single_layout["layout"] == "SINGLE_JSONL"
    assert sharded_layout["layout"] == "DETERMINISTIC_SHARDED_JSONL"

    single_plane = QKUComputationControlPlaneV1(single_root)
    sharded_plane = QKUComputationControlPlaneV1(sharded_root)

    def forbidden_open(*args: Any, **kwargs: Any) -> Any:
        raise AssertionError("runtime reopened a physical registry file")

    # Both physical layouts are fully loaded before this guard.  Resolve and
    # compute must operate exclusively on their immutable indexed snapshots.
    monkeypatch.setattr(Path, "open", forbidden_open)
    context = {
        "market": "TEST",
        "venue": "LOCAL",
        "mode": "STATIC_VALIDATION",
        "input_units": {"best_bid": "PRICE", "best_ask": "PRICE"},
        "input_lineage": {
            "best_bid": "FIXED_SEED_SCALE_PROBE",
            "best_ask": "FIXED_SEED_SCALE_PROBE",
        },
    }
    typed_inputs = {
        "best_bid": {
            "value": Decimal("0.40"),
            "unit": "PRICE",
            "lineage": "FIXED_SEED_SCALE_PROBE",
        },
        "best_ask": {
            "value": Decimal("0.60"),
            "unit": "PRICE",
            "lineage": "FIXED_SEED_SCALE_PROBE",
        },
    }
    planes = (single_plane, sharded_plane)
    plans = [plane.resolve(_SCALE_ROOT_ID, context) for plane in planes]
    expected_nodes = {
        "QTT.COMP.SCALE.SELECTED.MID_PRICE",
        "QTT.COMP.SCALE.SELECTED.SPREAD",
        _SCALE_ROOT_ID,
    }
    for plan in plans:
        assert plan.root_component_id == _SCALE_ROOT_ID
        assert plan.root_binding_id == "BIND.TEST.RELATIVE_SPREAD"
        assert {
            node.canonical_component_id for node in plan.topological_nodes
        } == expected_nodes
        assert len(plan.topological_nodes) == 3

    receipts = [
        plane.compute(_SCALE_ROOT_ID, typed_inputs, context) for plane in planes
    ]
    for receipt in receipts:
        assert receipt.outputs == {"relative_spread": Decimal("0.4")}
        assert receipt.nodes_executed == 3
        assert {
            row["component_id"] for row in receipt.requirement_receipts
        } == expected_nodes

    def stable_receipt(receipt: Any) -> tuple[Any, ...]:
        return (
            receipt.component_id,
            receipt.outputs,
            receipt.output_units,
            receipt.nodes_executed,
            tuple(
                sorted(
                    row["component_id"] for row in receipt.requirement_receipts
                )
            ),
        )

    assert stable_receipt(receipts[0]) == stable_receipt(receipts[1])
    for plane in planes:
        diagnostics = plane._diagnostics()
        assert diagnostics["registry_rows"] == record_count
        assert diagnostics["runtime_registry_file_reads_after_initialization"] == 0
        assert diagnostics["per_request_full_registry_iterations"] == 0
        assert diagnostics["unrelated_component_executions"] == 0
        assert diagnostics["records_examined_last_request"] == 3
        assert diagnostics["nodes_executed_last_request"] == 3
        assert diagnostics["implementation_call_counts"].get(
            _SCALE_NATIVE_STACK_IDENTITY, 0
        ) == 0


def test_scale_probe_records_complete_local_non_authoritative_measurement_matrix() -> None:
    """Use reduced bounds while exercising the production measurement path."""

    from tools.build_pr169_qku_comp_control1 import _run_scale_probe

    result = _run_scale_probe(
        64,
        _minimum_records=64,
        _measurement_subset_records=64,
        _sample_count=3,
    )
    matrix = result["local_non_authoritative_measurement_matrix"]
    assert matrix["authority"] == "LOCAL_NON_AUTHORITATIVE_DIAGNOSTIC_ONLY"
    assert matrix["measurement_registry_records"] == 64
    assert matrix["fixed_seed"] == _SCALE_PROBE_SEED
    assert matrix["timing_thresholds_applied"] is False
    assert matrix["percentile_method"] == "NEAREST_RANK"
    assert matrix["compile_proofs"] == {
        "no_op_delta_empty": True,
        "single_binding_changed_component_ids": [
            "QTT.COMP.SCALE.UNRELATED.00000000"
        ],
        "representative_new_record_added_component_ids": [
            "QTT.COMP.SCALE.MEASUREMENT.NEW.PROBABILITY_EDGE"
        ],
    }
    assert set(matrix["compile_ms"]) == {
        "no_op_expansion",
        "single_binding_update",
        "representative_new_record",
    }
    assert all(value >= 0 for value in matrix["compile_ms"].values())
    assert set(matrix["index_ms"]) == {"incremental_refresh", "full_rebuild"}
    assert matrix["incremental_index_full_rebuild_semantic_parity"] is True

    expected_subgraphs = {
        "one_node_zero_requirements": (1, 0),
        "three_nodes_two_requirements": (3, 2),
    }
    for name, (nodes, requirements) in expected_subgraphs.items():
        measurement = matrix["request_ms_by_selected_subgraph"][name]
        assert measurement["selected_nodes"] == nodes
        assert measurement["selected_requirements"] == requirements
        for operation in ("resolve", "compute"):
            summary = measurement[operation]
            assert summary["sample_count"] == 3
            assert 0 <= summary["p50_ms"] <= summary["p95_ms"]

    assert matrix["changed_projection_owners"] == [
        "READINESS1",
        "PRETRADE1",
        "AGENT_ORCH1",
        "SVC1",
    ]
    assert set(matrix["changed_projection_refresh_ms"]) == set(
        matrix["changed_projection_owners"]
    )
    assert all(
        value >= 0 for value in matrix["changed_projection_refresh_ms"].values()
    )
    assert matrix["runtime_registry_file_reads_after_initialization"] == 0
    assert matrix["per_request_full_registry_iterations"] == 0
    assert matrix["unrelated_component_executions"] == 0


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
    _restrict_to_status_explain(eligibility)
    eligibility["bindings"][0]["derived_state"] = "SPECIFICATION_REQUIRED"
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
    _restrict_to_status_explain(no_implementation)
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
    explanation = plane.explain(receipt, agent_id="parameter_selector_agent")
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
    _restrict_to_status_explain(fallback_record)
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
        [("payload", "OPAQUE_TEST_OBJECT")],
        [("field_count", "UNITLESS")],
    )
    record["definition"]["input_schema"][0]["type"] = "OBJECT"
    record["bindings"][0]["input_source_bindings"][0][
        "declared_type"
    ] = "OBJECT"
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
        {
            "market": "TEST",
            "venue": "LOCAL",
            "input_units": {"payload": "OPAQUE_TEST_OBJECT"},
            "input_lineage": {"payload": "CONTROL1_OBJECT_TEST_FIXTURE"},
        },
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
            "source_artifact_ref": f"source/FORMULA_{index}.json",
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

    canonical_library_path = tmp_path / validator.RP5C_CANONICAL_LIBRARY
    canonical_library_path.write_text(
        "".join(
            json.dumps(
                {
                    key: value
                    for key, value in row.items()
                    if key != "source_artifact_ref"
                },
                sort_keys=True,
            )
            + "\n"
            for row in canonical_library_rows
        ),
        encoding="utf-8",
    )
    with pytest.raises(validator.InvariantError, match="RP5C_INNER_SOURCE_REF_MISSING"):
        validator._rp5c_source(tmp_path, validator.Deadline(10_000))
    canonical_library_path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in canonical_library_rows),
        encoding="utf-8",
    )

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
            "".join(
                json.dumps(
                    {
                        **row,
                        "source_artifact_ref": (
                            "lineage/"
                            f"{formula_ids[row['canonical_identity_row_id']]}.json"
                        ),
                    },
                    sort_keys=True,
                )
                + "\n"
                for row in lineage_rows
            ),
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
                "source_artifact_ref": (
                    f"source/{formula_ids[row['canonical_identity_row_id']]}.json"
                ),
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
    first_lineage_summary = next(
        relation
        for relation in first_record["relations"]
        if relation["relation_type"] == "RP5C_SOURCE_LINEAGE_SUMMARY"
    )
    assert first_lineage_summary["source_artifact_refs"] == [
        "lineage/FORMULA_A.json",
        "source/FORMULA_A.json",
    ]
    assert first_lineage_summary["source_artifact_ref_count"] == 2

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
    missing_inner_ref = copy.deepcopy(rebuilt_records)
    missing_summary = next(
        relation
        for relation in missing_inner_ref[0]["relations"]
        if relation["relation_type"] == "RP5C_SOURCE_LINEAGE_SUMMARY"
    )
    missing_summary["source_artifact_refs"] = missing_summary[
        "source_artifact_refs"
    ][1:]
    missing_summary["source_artifact_ref_count"] -= 1
    with pytest.raises(validator.InvariantError, match="RP5C_CANONICAL_IMPORT"):
        validator._validate_rp5c_import(
            missing_inner_ref,
            source_groups,
            validator.Deadline(10_000),
            accepted_key_map,
        )
    extra_inner_ref = copy.deepcopy(rebuilt_records)
    extra_summary = next(
        relation
        for relation in extra_inner_ref[0]["relations"]
        if relation["relation_type"] == "RP5C_SOURCE_LINEAGE_SUMMARY"
    )
    extra_summary["source_artifact_refs"].append("source/NOT_PRESENT.json")
    extra_summary["source_artifact_refs"].sort()
    extra_summary["source_artifact_ref_count"] += 1
    with pytest.raises(validator.InvariantError, match="RP5C_CANONICAL_IMPORT"):
        validator._validate_rp5c_import(
            extra_inner_ref,
            source_groups,
            validator.Deadline(10_000),
            accepted_key_map,
        )
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
    control_module = importlib.import_module("src.qtt.computation_control.control")
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
    control_module = importlib.import_module("src.qtt.computation_control.control")
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
            "source_canonical_identity_row_id": "RP5C_IDENTITY_00000001",
            "source_occurrence_count": 1,
            "exact_lineage_validation_status": (
                "SOURCE_MEMBERSHIP_RECONSTRUCTED_AND_CLOSED_AT_BUILD_TIME"
            ),
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


@pytest.mark.parametrize(
    "location",
    [
        "provenance_mapping",
        "relation_sequence",
        "binding_evidence_mapping",
        "qku_role_sequence",
    ],
)
def test_rp5c_forbidden_occurrence_arrays_are_rejected_recursively(
    location: str,
) -> None:
    record = _rp5c_nonruntime_role_record()
    if location == "provenance_mapping":
        record["provenance"][0]["nested_lineage"] = {
            "member_identity_row_ids": ["RP5C_IDENTITY_00000001"]
        }
    elif location == "relation_sequence":
        record["relations"][0]["nested_lineage"] = [
            {"identity_row_ids": ["RP5C_IDENTITY_00000001"]}
        ]
    elif location == "binding_evidence_mapping":
        record["bindings"][0]["evidence_summary"]["nested_lineage"] = {
            "source_artifact_row_ids": ["SOURCE.ROW.1"]
        }
    elif location == "qku_role_sequence":
        record["uses"]["qku_role_bindings"][0]["nested_lineage"] = [
            {"member_identity_row_ids": []}
        ]
    else:  # pragma: no cover - the parameter table is closed above
        raise AssertionError(location)

    with pytest.raises(ValueError, match="RP5C_RUNTIME_LINEAGE_ARRAY"):
        _validate_record_shape(record)


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


@pytest.mark.parametrize(
    "defect",
    [
        "unknown_identity",
        "missing_target",
        "multiple_targets",
        "custody_mismatch",
        "formula_mismatch",
        "qku_mismatch",
        "formula_absence_token_mismatch",
        "qku_absence_token_mismatch",
    ],
)
def test_rp5d_reference_mapping_is_exact_identity_custody_join(
    defect: str,
) -> None:
    from tools import build_pr169_qku_comp_control1 as builder
    from tools import validate_pr169_qku_comp_control1 as validator

    identity = "RP5C_IDENTITY_00000001"
    target = "QTT.COMP.RP5C.00000001"
    custody = ("FORMULA", "QKU.ONE", "FORMULA.ONE", "", "", "")
    source = {
        identity: {
            "formula_ref": "FORMULA.ONE",
            "qku_ref": "QKU.ONE",
            "custody_key": custody,
        }
    }
    row: dict[str, Any] = {
        "identity_ref": identity,
        "formula_ref": "FORMULA.ONE",
        "qku_ref": "QKU.ONE",
    }
    identity_targets: dict[str, set[str]] = {identity: {target}}
    target_custodies: dict[str, set[tuple[str, ...]]] = {target: {custody}}
    if defect == "unknown_identity":
        row["identity_ref"] = "RP5C_IDENTITY_99999999"
    elif defect == "missing_target":
        identity_targets[identity] = set()
    elif defect == "multiple_targets":
        identity_targets[identity].add("QTT.COMP.RP5C.00000002")
    elif defect == "custody_mismatch":
        target_custodies[target] = {("FORMULA", "QKU.OTHER", "FORMULA.ONE", "", "", "")}
    elif defect == "formula_mismatch":
        row["formula_ref"] = "FORMULA.OTHER"
    elif defect == "qku_mismatch":
        row["qku_ref"] = "QKU.OTHER"
    elif defect == "formula_absence_token_mismatch":
        source[identity]["formula_ref"] = None
    elif defect == "qku_absence_token_mismatch":
        source[identity]["qku_ref"] = None
    else:  # pragma: no cover - the parameter table is closed above
        raise AssertionError(defect)

    with pytest.raises(builder.BuildError, match="RP5D_"):
        builder._classify_rp5d_reference_mapping(
            row,
            source_path="SOURCE.RP5D",
            rp5c_reference_rows=source,
            identity_targets=identity_targets,
            target_custody_keys=target_custodies,
        )
    with pytest.raises(validator.InvariantError, match="RP5D_"):
        validator._independent_rp5d_reference_mapping(
            row,
            source_path="SOURCE.RP5D",
            rp5c_reference_rows=source,
            identity_targets=identity_targets,
            target_custody_keys=target_custodies,
        )


def test_rp5d_reference_mapping_preserves_real_and_absent_references() -> None:
    from tools import build_pr169_qku_comp_control1 as builder
    from tools import validate_pr169_qku_comp_control1 as validator

    identity = "RP5C_IDENTITY_00000001"
    target = "QTT.COMP.RP5C.00000001"
    custody = ("FORMULA", "", "FORMULA.ONE", "", "", "")
    source = {
        identity: {
            "formula_ref": "FORMULA.ONE",
            "qku_ref": None,
            "custody_key": custody,
        }
    }
    row = {
        "identity_ref": identity,
        "formula_ref": "FORMULA.ONE",
        "qku_ref": f"{identity}::QKU_REF_NOT_PRESENT",
    }
    arguments = {
        "source_path": "SOURCE.RP5D",
        "rp5c_reference_rows": source,
        "identity_targets": {identity: {target}},
        "target_custody_keys": {target: {custody}},
    }
    built = builder._classify_rp5d_reference_mapping(row, **arguments)
    independently_derived = validator._independent_rp5d_reference_mapping(
        row, **arguments
    )
    assert built == independently_derived == {
        "target": target,
        "real_references": {"FORMULA": "FORMULA.ONE"},
        "absence_dispositions": {
            "QKU": f"{identity}::QKU_REF_NOT_PRESENT"
        },
    }


def test_independent_source_reference_requires_one_unambiguous_target() -> None:
    from tools import validate_pr169_qku_comp_control1 as validator

    assert validator._independent_reference_targets_resolved(
        {"QTT.COMP.EXACT.ONE"}
    )
    assert not validator._independent_reference_targets_resolved(set())
    assert not validator._independent_reference_targets_resolved(
        {"QTT.COMP.EXACT.ONE", "QTT.COMP.AMBIGUOUS.TWO"}
    )
    assert validator._independent_reference_targets_resolved(
        {"QTT.COMP.EXACT.ONE", "QTT.COMP.OTHER.CONTEXT"},
        {"QTT.COMP.EXACT.ONE"},
    )


def test_no_orphan_proof_rejects_missing_ownership_and_fake_consumers() -> None:
    from tools import validate_pr169_qku_comp_control1 as validator

    source_universe = {
        "artifacts": [
            {
                "artifact": "SOURCE.ONE",
                "actual_rows_read": 1,
                "classified_rows": 1,
                "unresolved_count": 0,
            }
        ]
    }
    record = _record(
        "QTT.COMP.TEST.NO_ORPHAN",
        "test:no_orphan",
        [("x", "UNITLESS")],
        [("y", "UNITLESS")],
    )
    result = validator._validate_no_orphan_closure([record], source_universe)
    assert result["active_agent_reachable_orphan_count"] == 0
    assert result["unclassified_in_scope_upstream_artifact_count"] == 0

    missing_producer = copy.deepcopy(record)
    missing_producer["governance"]["producer_owner"] = ""
    with pytest.raises(validator.InvariantError, match="ACTIVE_AGENT_REACHABLE_ORPHAN"):
        validator._validate_no_orphan_closure([missing_producer], source_universe)

    validator_only_consumer = copy.deepcopy(record)
    validator_only_consumer["uses"]["consumer_class_tags"] = [
        "CONTROL1_INDEPENDENT_VALIDATOR"
    ]
    validator_only_consumer["bindings"][0]["downstream_consumer_classes"] = [
        "CONTROL1_INDEPENDENT_VALIDATOR"
    ]
    with pytest.raises(validator.InvariantError, match="ACTIVE_AGENT_REACHABLE_ORPHAN"):
        validator._validate_no_orphan_closure(
            [validator_only_consumer], source_universe
        )

    missing_validator = copy.deepcopy(record)
    missing_validator["governance"]["validator_refs"] = []
    with pytest.raises(validator.InvariantError, match="ACTIVE_AGENT_REACHABLE_ORPHAN"):
        validator._validate_no_orphan_closure([missing_validator], source_universe)

    terminal_without_disposition = copy.deepcopy(record)
    terminal_without_disposition["record_state"] = "DORMANT_PRESERVED"
    terminal_without_disposition["bindings"][0]["derived_state"] = "RETIRED"
    with pytest.raises(validator.InvariantError, match="ACTIVE_AGENT_REACHABLE_ORPHAN"):
        validator._validate_no_orphan_closure(
            [terminal_without_disposition], source_universe
        )

    fake_audit_consumer = copy.deepcopy(record)
    fake_audit_consumer["provenance"][0]["source_relation"] = (
        "AUDIT_ONLY_TERMINAL"
    )
    with pytest.raises(
        validator.InvariantError, match="FAKE_AUDIT_ONLY_RUNTIME_CONSUMER"
    ):
        validator._validate_no_orphan_closure(
            [fake_audit_consumer], source_universe
        )

    unclassified = copy.deepcopy(source_universe)
    unclassified["artifacts"][0]["classified_rows"] = 0
    with pytest.raises(
        validator.InvariantError,
        match="UNCLASSIFIED_IN_SCOPE_UPSTREAM_ARTIFACT",
    ):
        validator._validate_no_orphan_closure([record], unclassified)


def test_gfp_discovery_labels_cannot_prove_semantic_mapping() -> None:
    from tools import build_pr169_qku_comp_control1 as builder
    from tools import validate_pr169_qku_comp_control1 as validator

    lossy_catalog_row = {
        "formula_catalog_id": "GFP.CATALOG.1",
        "selected_formula_id": "PR168_GFP_FORMULA_001",
        "coverage_status": "COVERED",
        "formula_expression_or_description": "similar looking prose",
    }
    assert not builder._gfp_discovery_has_complete_typed_semantics(
        lossy_catalog_row
    )
    assert not validator._independent_gfp_discovery_has_complete_typed_semantics(
        lossy_catalog_row
    )

    complete = {
        **lossy_catalog_row,
        "typed_input_schema": [{"name": "x", "type": "NUMBER"}],
        "typed_output_schema": [{"name": "y", "type": "NUMBER"}],
        "exact_units_and_bases": {"x": "UNITLESS", "y": "UNITLESS"},
        "domain_and_boundary_behavior": {"nonfinite": "FAIL_CLOSED"},
        "state_and_time_semantics": {"state": "STATELESS"},
        "missing_stale_nonfinite_behavior": "FAIL_CLOSED",
        "precision_and_rounding": "EXACT",
        "typed_requirements": [
            {
                "required_component_id": "QTT.COMP.EXACT.UPSTREAM",
                "consumer_input_name": "x",
            }
        ],
        "semantic_fallback": {"not_applicable": True, "proof_ref": "EXACT"},
        "direct_equivalence_proof_ref": "INDEPENDENT.PROOF.1",
    }
    assert builder._gfp_discovery_has_complete_typed_semantics(complete)
    assert validator._independent_gfp_discovery_has_complete_typed_semantics(
        complete
    )


def test_independent_source_owner_discovery_closes_exact_current_equivalents() -> None:
    from tools import validate_pr169_qku_comp_control1 as validator

    specs, split = validator._independent_source_closure_artifacts(
        Path.cwd(), validator.Deadline(30_000)
    )
    assert len(specs) == 311
    assert sum(int(spec["expected"]) for spec in specs) == 405_511
    by_cohort: dict[str, tuple[int, int]] = {}
    for cohort in {str(spec["cohort"]) for spec in specs}:
        selected = [spec for spec in specs if spec["cohort"] == cohort]
        by_cohort[cohort] = (
            len(selected),
            sum(int(spec["expected"]) for spec in selected),
        )
    assert by_cohort["FIXTURE_5"] == (1, 5)
    assert by_cohort["RP5D_R1"] == (27, 873)
    assert by_cohort["RP5D_R1_OWNER_CONTEXT"] == (1, 15)
    assert sum(by_cohort[name][0] for name in (
        "FIXTURE_5", "RP5D_R1", "RP5D_R1_OWNER_CONTEXT"
    )) == 29
    assert sum(by_cohort[name][1] for name in (
        "FIXTURE_5", "RP5D_R1", "RP5D_R1_OWNER_CONTEXT"
    )) == 893
    assert all(item["unclassified_manifest_entries"] == 0 for item in split)


def test_source_row_denominator_mismatch_fails_value_level_closure(
    tmp_path: Path,
) -> None:
    from tools import validate_pr169_qku_comp_control1 as validator

    (tmp_path / "owner.jsonl").write_text(
        '{"row_id":"OWNER.1"}\n', encoding="utf-8", newline="\n"
    )
    (tmp_path / "owner.manifest.json").write_text(
        '{"row_count":2}\n', encoding="utf-8", newline="\n"
    )
    with pytest.raises(validator.InvariantError, match="SOURCE_CLOSURE_DENOMINATOR"):
        validator._closure_read_rows(
            tmp_path, "owner.jsonl", validator.Deadline(30_000)
        )


@pytest.mark.parametrize("defect", ["canonical_admission", "digest_authority"])
def test_owner_projection_defects_fail_independent_validation(defect: str) -> None:
    from tools import validate_pr169_qku_comp_control1 as validator

    row: dict[str, Any] = {"row_id": "OWNER.ROW.1", "status": "OWNER_RETAINED"}
    targets: set[str] = set()
    if defect == "canonical_admission":
        targets.add("QTT.COMP.FALSE.CONTEXT_ADMISSION")
    else:
        row["content_digest"] = "FORBIDDEN_NONZERO_AUTHORITY"
    with pytest.raises(
        validator.InvariantError,
        match=(
            "SOURCE_OWNER_PROJECTION_FALSE_CANONICAL_ADMISSION"
            if defect == "canonical_admission"
            else "SOURCE_OWNER_HASH_DIGEST_AUTHORITY"
        ),
    ):
        validator._independent_validate_owner_projection_row(
            row,
            path="SOURCE.OWNER.PROJECTION",
            row_key="OWNER.ROW.1",
            canonical_provenance_targets=targets,
            reject_hash_authority=True,
        )


def test_source_context_tuple_record_is_rejected_before_owner_scan() -> None:
    from tools import validate_pr169_qku_comp_control1 as validator

    record = _record(
        "QTT.COMP.FALSE.SOURCE_SELECTION",
        "test:source_context",
        [("x", "UNITLESS")],
        [("y", "UNITLESS")],
    )
    record["definition"]["source_scoped_selection_tuple"] = {
        "formula_refs": ["FORMULA.OWNER"],
        "algorithm_refs": ["ALGORITHM.OWNER"],
        "parameter_stack_refs": ["PARAMETERS.OWNER"],
    }
    record["provenance"][0]["source_artifact_ref"] = "SOURCE.OWNER.CONTEXT"
    with pytest.raises(
        validator.InvariantError,
        match="SOURCE_CONTEXT_FALSE_SELECTION_POLICY_ADMISSION",
    ):
        validator._validate_source_universe_closure(
            Path.cwd(), [record], validator.Deadline(30_000)
        )


def test_source_owner_callable_normalization_is_fixed_and_allowlisted() -> None:
    from tools import build_pr169_qku_comp_control1 as builder
    from tools import validate_pr169_qku_comp_control1 as validator

    path = (
        "src/qtt/stage1_prediction_markets/pr168_gfp_real_computation/"
        "prediction_market_math.py"
    )
    function = "binary_contract_expected_value"
    expected = (
        "src.qtt.stage1_prediction_markets.pr168_gfp_real_computation."
        "prediction_market_math:binary_contract_expected_value"
    )
    assert builder._normalized_gfp_callable_ref(path, function) == expected
    assert validator._independent_normalized_gfp_callable_ref(path, function) == expected
    validator._validate_callable_ref(expected)
    validator._validate_callable_ref(
        "src.qtt.stage1_prediction_markets.pr168_gfp_real_computation."
        "execution_costs:adverse_selection_penalty"
    )
    for unsafe_ref in (
        "qtt.control.eval:run",
        "qtt.control:exec",
        "qtt.control.os.system:run",
        "qtt.control.importlib:run",
    ):
        with pytest.raises(validator.InvariantError, match="UNSAFE_CALLABLE_REF"):
            validator._validate_callable_ref(unsafe_ref)
    with pytest.raises(builder.BuildError, match="escaped allowlist"):
        builder._normalized_gfp_callable_ref(
            "src/qtt/stage1_prediction_markets/pr168_gfp_real_computation/unsafe.py",
            function,
        )
    with pytest.raises(validator.InvariantError, match="ALLOWLIST"):
        validator._independent_normalized_gfp_callable_ref(
            "src/qtt/stage1_prediction_markets/pr168_gfp_real_computation/unsafe.py",
            function,
        )


def test_source_inventory_only_implementation_cannot_be_selected_for_runtime() -> None:
    from tools import validate_pr169_qku_comp_control1 as validator

    source_inventory = _record(
        "QTT.COMP.TEST.SOURCE_INVENTORY",
        "MATERIALIZED_FORMULA_PLUGIN_CONTRACT",
        [("x", "UNITLESS")],
        [("y", "UNITLESS")],
        record_state="PROVISIONAL",
    )
    implementation = source_inventory["definition"]["implementation_versions"][0]
    implementation["security_state"] = "SOURCE_INVENTORY_NOT_RUNTIME_ALLOWLISTED"
    binding = source_inventory["bindings"][0]
    binding["selected_implementation_version"] = None
    binding["readiness"]["specification"] = "REQUIRED"
    binding["readiness"]["implementation"] = "REQUIRED"
    binding["derived_state"] = "SPECIFICATION_REQUIRED"
    for policy in binding["agent_access_policy"].values():
        policy["control_plane_operations"] = ["status", "explain"]

    assert (
        validator._validate_nonruntime_source_inventory_record(
            source_inventory, [implementation]
        )
        == 1
    )

    binding["selected_implementation_version"] = implementation[
        "implementation_version"
    ]
    with pytest.raises(
        validator.InvariantError, match="SOURCE_INVENTORY_RUNTIME_SELECTION"
    ):
        validator._validate_nonruntime_source_inventory_record(
            source_inventory, [implementation]
        )


def test_pr162b_source_vector_mutation_fails_both_derivations() -> None:
    from tools import build_pr169_qku_comp_control1 as builder
    from tools import validate_pr169_qku_comp_control1 as validator

    rows: list[dict[str, Any]] = []
    deadline = builder._Deadline(30_000)
    for source_path in builder.PR162B_TEST_VECTOR_PATHS:
        source_rows, _ = builder._read_source_artifact_rows(
            Path.cwd(), source_path, deadline
        )
        rows.extend(source_rows)
    assert builder._verify_pr162b_source_vectors(rows, deadline)[
        "source_vector_exact_match_count"
    ] == 75
    assert validator._independently_invoke_pr162b_source_vectors(
        rows, validator.Deadline(30_000)
    )["source_vector_exact_match_count"] == 75

    mutated = copy.deepcopy(rows)
    mutated[0]["expected_output"] = "CONTROL1_MUTATION_SENTINEL"
    with pytest.raises(builder.BuildError, match="source vector mismatch"):
        builder._verify_pr162b_source_vectors(mutated, builder._Deadline(30_000))
    with pytest.raises(
        validator.InvariantError, match="PR162B_SOURCE_VECTOR_MISMATCH"
    ):
        validator._independently_invoke_pr162b_source_vectors(
            mutated, validator.Deadline(30_000)
        )


def test_source_coassociation_cannot_mint_selection_policy_or_qku_root() -> None:
    from tools import build_pr169_qku_comp_control1 as builder

    agent_ids = (
        "research_agent",
        "parameter_selector_agent",
        "risk_manager_agent",
        "quantum_optimizer_agent",
        "commander_agent",
        "governance_agent",
        "dashboard_agent",
        "connector_venue_readiness_future_consumer",
    )
    batch = builder._build_source_semantic_candidate_batch(
        Path.cwd(), agent_ids, builder._Deadline(30_000)
    )
    records = [item["record"] for item in batch["items"]]
    assert all(
        "POST_LAUNCH_EXPANSION_BATCH" not in record["origin_cohorts"]
        and all("tests/" not in str(value) for value in record["origin_cohorts"])
        for record in records
    )
    selectors = [
        record
        for record in records
        if record["definition"]["component_kind"] == "QKU_SELECTION_POLICY"
        or "source_scoped_selection_tuple" in record["definition"]
    ]
    assert selectors == []
    contextual = [
        record
        for record in records
        if record["canonical_component_id"].startswith(
            ("QTT.COMP.CANDIDATE.FORMULA.", "QTT.COMP.CANDIDATE.ALGORITHM.")
        )
        and set(record["origin_cohorts"]).intersection(
            {
                "PR162E_PLUGIN_CONTEXT_REFERENCE",
                "PR162E_Q_QUANTUM_CONTEXT_REFERENCE",
                "PR166_SM3_EVIDENCE_REFERENCE",
            }
        )
    ]
    assert len(contextual) == 8
    assert all(not record["uses"]["qku_role_bindings"] for record in contextual)

    plane = QKUComputationControlPlaneV1(records=records)
    context = {
        "mode": "STATIC_VALIDATION",
        "market": "UNRESOLVED",
        "venue": "NO_VENUE",
        "context_family": "SOURCE_IDENTITY_REVIEW",
    }
    # Source owners may provide real implementation inventory while the
    # contextual binding intentionally selects none until typed semantics and
    # an independent oracle close.  Status/explain must remain useful, but the
    # inventory itself cannot manufacture resolve/compute eligibility.
    for source_origin in ("MAP3_RECOVERED", "PR162B_SOURCE_SEMANTICS"):
        incomplete = next(
            record
            for record in records
            if source_origin in record["origin_cohorts"]
            and record["uses"]["qku_role_bindings"]
        )
        incomplete_role = incomplete["uses"]["qku_role_bindings"][0]
        incomplete_selector = {
            "qku_id": incomplete_role["qku_id"],
            "role_or_decision_stage": incomplete_role[
                "role_or_decision_stage"
            ],
            "market_family": incomplete_role["market_family"],
        }
        incomplete_status = plane.status(
            incomplete_selector,
            context,
            agent_id="research_agent",
        )
        assert incomplete_status["canonical_component_id"] == incomplete[
            "canonical_component_id"
        ]
        assert incomplete_status["binding_readiness"]["specification"] == "REQUIRED"
        assert incomplete_status["derived_state"] == "SPECIFICATION_REQUIRED"
        assert any(
            blocker.startswith("MISSING_IMPLEMENTATION:")
            for blocker in incomplete_status["blockers"]
        )
        assert plane.explain(
            incomplete_selector,
            context,
            agent_id="research_agent",
        )["identity"]["canonical_component_id"] == incomplete[
            "canonical_component_id"
        ]
        with pytest.raises(
            ComputationControlError, match="SELECTOR_NOT_RESOLVED"
        ):
            plane.resolve(
                incomplete_selector,
                context,
                agent_id="research_agent",
            )
        with pytest.raises(
            ComputationControlError, match="SELECTOR_NOT_RESOLVED"
        ):
            plane.compute(
                incomplete_selector,
                {},
                context,
                agent_id="research_agent",
                consumer="CONTROL1_TEST",
            )


def _status_explain_only_qku_record(component_id: str) -> dict[str, Any]:
    record = _record(
        component_id,
        "test:qku_verification",
        [("x", "UNITLESS")],
        [("y", "UNITLESS")],
    )
    record["uses"]["qku_role_bindings"][0]["runtime_root_eligibility"] = (
        "STATUS_EXPLAIN_ONLY"
    )
    for policy in record["bindings"][0]["agent_access_policy"].values():
        policy["control_plane_operations"] = ["status", "explain"]
    return record


def test_qku_verification_receipts_fail_closed_for_missing_escape_and_escalation() -> None:
    from tools import build_pr169_qku_comp_control1 as builder
    from tools import validate_pr169_qku_comp_control1 as validator

    base = builder._attach_qku_verification_receipts(
        [_status_explain_only_qku_record("QTT.COMP.TEST.QKU_RECEIPT")]
    )[0]
    assert base["uses"]["qku_role_bindings"][0][
        "qku_verification_receipt"
    ]["verification_state"] == "UNRESOLVED_MATERIAL_BLOCKER"
    validator._validate_qku_verification_receipts([base])

    missing = copy.deepcopy(base)
    del missing["uses"]["qku_role_bindings"][0]["qku_verification_receipt"]
    with pytest.raises(
        validator.InvariantError, match="QKU_VERIFICATION_RECEIPT_MISSING"
    ):
        validator._validate_qku_verification_receipts([missing])

    generic_escape = _status_explain_only_qku_record(
        "QTT.COMP.TEST.QKU_GENERIC_NA_ESCAPE"
    )
    generic_escape["definition"][
        "external_verification_not_applicable_reason"
    ] = "not applicable"
    generic_attached = builder._attach_qku_verification_receipts(
        [generic_escape]
    )[0]
    assert generic_attached["uses"]["qku_role_bindings"][0][
        "qku_verification_receipt"
    ]["verification_state"] == "UNRESOLVED_MATERIAL_BLOCKER"

    escalated = copy.deepcopy(base)
    escalated["bindings"][0]["agent_access_policy"]["parameter_selector_agent"][
        "control_plane_operations"
    ].append("compute")
    with pytest.raises(
        validator.InvariantError, match="QKU_UNRESOLVED_MODE_ESCALATION"
    ):
        validator._validate_qku_verification_receipts([escalated])

    current_fact = builder._attach_qku_verification_receipts(
        [
            _status_explain_only_qku_record(
                "QTT.COMP.CANDIDATE.FORMULA.KALSHI_TICK_001"
            )
        ]
    )[0]
    del current_fact["uses"]["qku_role_bindings"][0][
        "qku_verification_receipt"
    ]["ttl_or_null"]
    with pytest.raises(
        validator.InvariantError, match="QKU_CURRENT_FACT_TIME_MISSING"
    ):
        validator._validate_qku_verification_receipts([current_fact])


@pytest.mark.parametrize(
    ("field", "value"),
    [
        (
            "external_verification_not_applicable_reason",
            {"reason": "fixture says external verification is not applicable"},
        ),
        (
            "official_current_documentation_proof",
            {"url": "https://example.invalid/fabricated-official-proof"},
        ),
        (
            "repository_historical_evidence_provenance",
            {"source_ref": "tests/fabricated-history"},
        ),
        (
            "qtt_internal_policy_provenance",
            {"owner": "fabricated-test-policy"},
        ),
    ],
)
def test_qku_proof_shaped_metadata_cannot_self_promote(
    field: str, value: dict[str, str]
) -> None:
    from tools import build_pr169_qku_comp_control1 as builder
    from tools import validate_pr169_qku_comp_control1 as validator

    record = _status_explain_only_qku_record(
        f"QTT.COMP.TEST.QKU.FABRICATED.{field.upper()}"
    )
    record["definition"][field] = value
    attached = builder._attach_qku_verification_receipts([record])[0]
    receipt = attached["uses"]["qku_role_bindings"][0][
        "qku_verification_receipt"
    ]
    assert receipt["verification_state"] == "UNRESOLVED_MATERIAL_BLOCKER"
    assert receipt["blocker_code"] == "UNAPPROVED_EXTERNAL_VERIFICATION_ESCAPE"
    assert receipt["exact_unique_claim"]["claim_kind"] == receipt["blocker_code"]
    validator._validate_qku_verification_receipts([attached])


def test_qku_exact_unique_claim_and_rejected_fail_closed_policy_are_independent() -> None:
    from tools import build_pr169_qku_comp_control1 as builder
    from tools import validate_pr169_qku_comp_control1 as validator

    unresolved = builder._attach_qku_verification_receipts(
        [_status_explain_only_qku_record("QTT.COMP.TEST.QKU.EXACT.CLAIM")]
    )[0]
    missing_claim = copy.deepcopy(unresolved)
    del missing_claim["uses"]["qku_role_bindings"][0][
        "qku_verification_receipt"
    ]["exact_unique_claim"]
    with pytest.raises(
        validator.InvariantError, match="QKU_EXACT_UNRESOLVED_CLAIM_MISSING"
    ):
        validator._validate_qku_verification_receipts([missing_claim])

    corrupted_claim = copy.deepcopy(unresolved)
    corrupted_claim["uses"]["qku_role_bindings"][0][
        "qku_verification_receipt"
    ]["exact_unique_claim"]["claim_kind"] = "GENERIC_ESCAPE"
    with pytest.raises(
        validator.InvariantError, match="QKU_EXACT_UNRESOLVED_CLAIM_MISSING"
    ):
        validator._validate_qku_verification_receipts([corrupted_claim])

    rejected = _status_explain_only_qku_record("QTT.COMP.TEST.QKU.REJECTED")
    rejected["record_state"] = "REJECTED_INVALID"
    rejected = builder._attach_qku_verification_receipts([rejected])[0]
    validator._validate_qku_verification_receipts([rejected])
    rejected["bindings"][0]["agent_access_policy"][
        "parameter_selector_agent"
    ]["control_plane_operations"].append("compute")
    with pytest.raises(
        validator.InvariantError, match="QKU_UNRESOLVED_MODE_ESCALATION"
    ):
        validator._validate_qku_verification_receipts([rejected])


def test_qku_family_inheritance_requires_exact_semantics_and_applicability_policy() -> None:
    from tools import build_pr169_qku_comp_control1 as builder
    from tools import validate_pr169_qku_comp_control1 as validator

    record = _status_explain_only_qku_record(
        "QTT.COMP.FORMULA.IMPLIED_PROBABILITY"
    )
    record["definition"].update(
        builder._reviewed_closed_decimal_semantics()[
            "QTT.COMP.FORMULA.IMPLIED_PROBABILITY"
        ]
    )
    record["definition"]["oracle_and_test_refs"] = [
        {
            "ref": (
                "tests/pr169_qku_comp_control1/test_control1.py::"
                "test_closed_formula_decimal_oracles_are_independent"
            )
        }
    ]
    first = record["uses"]["qku_role_bindings"][0]
    first["qku_id"] = "QKU.TEST.FAMILY.A"
    first["market_family"] = "binary_event_contract"
    second = copy.deepcopy(first)
    second["qku_id"] = "QKU.TEST.FAMILY.B"
    record["uses"]["qku_role_bindings"].append(second)
    attached = builder._attach_qku_verification_receipts([record])[0]
    validator._validate_qku_verification_receipts([attached])
    inherited = next(
        role
        for role in attached["uses"]["qku_role_bindings"]
        if role["qku_verification_receipt"]["verification_state"]
        == "VERIFIED_BY_CANONICAL_FAMILY_INHERITANCE"
    )
    inherited["qku_verification_receipt"][
        "inheritance_equivalence_proof_or_null"
    ]["equivalence_policy_id"] = "NAME_ONLY_FALSE_EQUIVALENCE"
    with pytest.raises(
        validator.InvariantError, match="QKU_INHERITANCE_SEMANTIC_DRIFT"
    ):
        validator._validate_qku_verification_receipts([attached])


def test_qku_positive_receipt_requires_exact_reviewed_semantics_not_component_id() -> None:
    from tools import build_pr169_qku_comp_control1 as builder
    from tools import validate_pr169_qku_comp_control1 as validator

    record = _status_explain_only_qku_record(
        "QTT.COMP.FORMULA.IMPLIED_PROBABILITY"
    )
    record["definition"].update(
        builder._reviewed_closed_decimal_semantics()[
            "QTT.COMP.FORMULA.IMPLIED_PROBABILITY"
        ]
    )
    record["definition"]["oracle_and_test_refs"] = [
        {
            "ref": (
                "tests/pr169_qku_comp_control1/test_control1.py::"
                "test_closed_formula_decimal_oracles_are_independent"
            )
        }
    ]
    role = record["uses"]["qku_role_bindings"][0]
    role["market_family"] = "binary_event_contract"
    exact = builder._attach_qku_verification_receipts([record])[0]
    receipt = exact["uses"]["qku_role_bindings"][0][
        "qku_verification_receipt"
    ]
    assert receipt["verification_state"] == (
        "VERIFIED_BY_INDEPENDENT_MATHEMATICAL_DERIVATION"
    )
    validator._validate_qku_verification_receipts([exact])

    mutated = copy.deepcopy(record)
    mutated["definition"]["complete_mathematical_or_procedural_definition"] = (
        "implied_probability = price / payout"
    )
    blocked = builder._attach_qku_verification_receipts([mutated])[0]
    blocked_receipt = blocked["uses"]["qku_role_bindings"][0][
        "qku_verification_receipt"
    ]
    assert blocked_receipt["verification_state"] == "UNRESOLVED_MATERIAL_BLOCKER"
    assert blocked_receipt["blocker_code"] == (
        "REVIEWED_SEMANTIC_BINDING_MISMATCH"
    )
    validator._validate_qku_verification_receipts([blocked])


def test_qku_inheritance_is_binding_venue_and_selector_aware() -> None:
    from tools import build_pr169_qku_comp_control1 as builder
    from tools import validate_pr169_qku_comp_control1 as validator

    record = _status_explain_only_qku_record(
        "QTT.COMP.FORMULA.IMPLIED_PROBABILITY"
    )
    record["definition"].update(
        builder._reviewed_closed_decimal_semantics()[
            "QTT.COMP.FORMULA.IMPLIED_PROBABILITY"
        ]
    )
    record["definition"]["oracle_and_test_refs"] = [
        {
            "ref": (
                "tests/pr169_qku_comp_control1/test_control1.py::"
                "test_closed_formula_decimal_oracles_are_independent"
            )
        }
    ]
    first_role = record["uses"]["qku_role_bindings"][0]
    first_role["qku_id"] = "QKU.TEST.SELECTOR.A"
    first_role["market_family"] = "binary_event_contract"
    second_role = copy.deepcopy(first_role)
    second_role["qku_id"] = "QKU.TEST.SELECTOR.B"
    record["uses"]["qku_role_bindings"].append(second_role)
    first_binding = record["bindings"][0]
    first_binding["binding_id"] = "BINDING.TEST.SELECTOR.A"
    first_binding["venue"] = "VENUE_A"
    first_binding["context_selector"]["venue"] = "VENUE_A"
    first_binding["qku_binding_selector_or_null"] = "QKU.TEST.SELECTOR.A"
    second_binding = copy.deepcopy(first_binding)
    second_binding["binding_id"] = "BINDING.TEST.SELECTOR.B"
    second_binding["venue"] = "VENUE_B"
    second_binding["context_selector"]["venue"] = "VENUE_B"
    second_binding["qku_binding_selector_or_null"] = "QKU.TEST.SELECTOR.B"
    record["bindings"].append(second_binding)

    attached = builder._attach_qku_verification_receipts([record])[0]
    states = [
        role["qku_verification_receipt"]["verification_state"]
        for role in attached["uses"]["qku_role_bindings"]
    ]
    assert states == [
        "VERIFIED_BY_INDEPENDENT_MATHEMATICAL_DERIVATION",
        "VERIFIED_BY_INDEPENDENT_MATHEMATICAL_DERIVATION",
    ]
    validator._validate_qku_verification_receipts([attached])

    forged = copy.deepcopy(attached)
    first_ref = builder._qku_role_ref(
        forged["uses"]["qku_role_bindings"][0]
    )
    forged_receipt = forged["uses"]["qku_role_bindings"][1][
        "qku_verification_receipt"
    ]
    forged_receipt["verification_state"] = (
        "VERIFIED_BY_CANONICAL_FAMILY_INHERITANCE"
    )
    forged_receipt["inheritance_equivalence_proof_or_null"] = {
        "reference_qku_role_ref": first_ref,
        "equivalence_policy_id": "QKU.INHERIT.EXACT_SEMANTICS.V1",
        "applicability_policy_id": (
            "QKU.INHERIT.EXACT_MARKET_VENUE_CONTEXT_BINDINGS.V1"
        ),
        "canonical_component_id": record["canonical_component_id"],
        "semantic_version": record["semantic_version"],
        "semantic_fields_compared": list(
            builder.QKU_INHERITANCE_SEMANTIC_FIELDS
        ),
        "binding_applicability": builder._qku_role_applicability_signature(
            forged, forged["uses"]["qku_role_bindings"][0]
        ),
    }
    with pytest.raises(
        validator.InvariantError, match="QKU_VERIFICATION_DISPOSITION_FALSE"
    ):
        validator._validate_qku_verification_receipts([forged])


def test_qku_risk_disposition_does_not_masquerade_as_positive_verification() -> None:
    from tools import build_pr169_qku_comp_control1 as builder
    from tools import validate_pr169_qku_comp_control1 as validator

    record = _status_explain_only_qku_record(
        "QTT.COMP.TEST.QKU.RISK.UNVERIFIED"
    )
    record["uses"]["decision_roles"] = [
        "HARD_SOURCE_RISK_CASH_ALLOW_AND_ROUTER_GATES"
    ]
    attached = builder._attach_qku_verification_receipts([record])[0]
    metrics = validator._validate_qku_verification_receipts([attached])
    assert metrics["risk_and_accounting_QKU_verification_coverage"] == "100%"
    assert metrics["risk_and_accounting_QKU_positive_verification_coverage"] == (
        "0.000000%"
    )
    assert metrics["risk_and_accounting_QKU_disposition_coverage"] == "100%"
    assert metrics["risk_and_accounting_QKU_verified_count"] == 0
    assert metrics["risk_and_accounting_QKU_blocked_count"] == 1


@pytest.fixture(scope="module")
def _canonical_qku_verification_fixture() -> tuple[
    list[dict[str, Any]], dict[str, Any], dict[str, Any]
]:
    from tools import build_pr169_qku_comp_control1 as builder
    from tools import validate_pr169_qku_comp_control1 as validator

    artifact_dir = (
        Path.cwd()
        / "docs/master_plan/generated/pr169_qku_comp_control1"
    )
    records, _ = _load_logical_registry(artifact_dir)
    records = builder._attach_qku_verification_receipts(records)
    report_section = builder._validate_qku_verification_receipts(
        records, enforce_current_universe=False
    )
    independently_derived = validator._validate_qku_verification_receipts(
        records
    )
    return records, report_section, independently_derived


def test_qku_source_claim_crosswalk_and_conflict_mutations_fail_independently(
    _canonical_qku_verification_fixture: tuple[
        list[dict[str, Any]], dict[str, Any], dict[str, Any]
    ],
) -> None:
    from tools import validate_pr169_qku_comp_control1 as validator

    records, clean_section, independently_derived = (
        _canonical_qku_verification_fixture
    )
    temporary_directory = tempfile.TemporaryDirectory(
        prefix="qtt-qku-verification-"
    )
    tmp_path = Path(temporary_directory.name)

    def validate_mutation(
        section: dict[str, Any], expected_code: str
    ) -> None:
        (tmp_path / "acceptance.report.json").write_text(
            json.dumps({"qku_verification": section}),
            encoding="utf-8",
        )
        with pytest.raises(validator.InvariantError, match=expected_code):
            validator._validate_qku_acceptance_source_packs(
                tmp_path,
                records,
                independently_derived,
            )

    wrong_consumer = copy.deepcopy(clean_section)
    source_pack = next(
        pack
        for pack in wrong_consumer["shared_claim_family_source_packs"]
        if pack["claim_family_pack_id"] == "QKU.CLAIM.VENUE_PROVIDER.V1"
    )
    source_pack["claims"][0]["exact_component_consumers"].pop()
    validate_mutation(wrong_consumer, "QKU_SOURCE_CLAIM_CONSUMER_JOIN")

    wrong_downstream_join = copy.deepcopy(clean_section)
    downstream_pack = next(
        pack
        for pack in wrong_downstream_join["shared_claim_family_source_packs"]
        if pack["claim_family_pack_id"] == "QKU.CLAIM.VENUE_PROVIDER.V1"
    )
    downstream_pack["claims"][0]["exact_component_consumers"][0][
        "downstream_consumer_classes"
    ] = ["FABRICATED_CONSUMER"]
    validate_mutation(
        wrong_downstream_join, "QKU_SOURCE_CLAIM_CONSUMER_JOIN"
    )

    missing_official_basis = copy.deepcopy(clean_section)
    quantum_pack = next(
        pack
        for pack in missing_official_basis["shared_claim_family_source_packs"]
        if pack["claim_family_pack_id"] == "QKU.CLAIM.QUANTUM.V1"
    )
    missing_url = (
        "https://qiskit-community.github.io/qiskit-optimization/stubs/"
        "qiskit_optimization.converters.QuadraticProgramToQubo.html"
    )
    quantum_pack["sources"] = [
        source for source in quantum_pack["sources"] if source["url"] != missing_url
    ]
    quantum_pack["claims"] = [
        claim
        for claim in quantum_pack["claims"]
        if claim["source_url_refs"] != [missing_url]
    ]
    quantum_pack["conflict_disposition"]["authoritative_basis_urls"].remove(
        missing_url
    )
    validate_mutation(missing_official_basis, "QKU_SOURCE_PACK_URL_SET")

    bad_crosswalk = copy.deepcopy(clean_section)
    bad_crosswalk["qku_to_verification_crosswalk_rows"][0][
        "verification_state"
    ] = "VERIFIED_AS_QTT_INTERNAL_POLICY"
    validate_mutation(bad_crosswalk, "QKU_CROSSWALK_COVERAGE")

    bad_conflict = copy.deepcopy(clean_section)
    conflict_pack = next(
        pack
        for pack in bad_conflict["shared_claim_family_source_packs"]
        if pack["claim_family_pack_id"] == "QKU.CLAIM.VENUE_PROVIDER.V1"
    )
    conflict_pack["material_component_conflicts"][0]["blocker"] = (
        "FALSE_CONFLICT_RESOLUTION"
    )
    validate_mutation(bad_conflict, "QKU_MATERIAL_CONFLICT_SHAPE")

    bad_ttl = copy.deepcopy(clean_section)
    ttl_pack = next(
        pack
        for pack in bad_ttl["shared_claim_family_source_packs"]
        if pack["claim_family_pack_id"] == "QKU.CLAIM.VENUE_PROVIDER.V1"
    )
    ttl_pack["sources"][0]["ttl"] = "NEVER"
    validate_mutation(bad_ttl, "QKU_CURRENT_FACT_RECHECK_MISSING")
    temporary_directory.cleanup()


def test_independent_snapshot_probe_observes_valid_old_and_new_payloads() -> None:
    from src.qtt.computation_control import control as control_module
    from tools import validate_pr169_qku_comp_control1 as validator

    observations = validator._bounded_snapshot_concurrency_probe(
        control_module,
        QKUComputationControlPlaneV1,
        {},
    )
    assert observations >= 2


def test_independent_compiler_probe_uses_disjoint_binding_domains() -> None:
    from src.qtt.computation_control import control as control_module
    from tools import validate_pr169_qku_comp_control1 as validator

    result = validator._compiler_mechanism_probe(
        control_module,
        validator._synthetic_records(64),
    )
    assert result["source_order_stable"] is True
    assert result["rollback"] is True
