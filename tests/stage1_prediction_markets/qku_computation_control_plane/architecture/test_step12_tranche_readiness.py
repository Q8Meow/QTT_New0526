from dataclasses import replace
from decimal import Decimal

import pytest

from tools.build_qku_computation_control_plane import build_payload

from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import (
    ContractValidationError,
    ParameterPolicyError,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.parameter_policy import (
    PARAMETER_POLICIES,
    ParameterPolicyResolverV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.validation import (
    build_tranche_a_coverage_manifest,
    validate_domain,
    validate_tranche_a_coverage_manifest,
)


def test_tranche_a_manifest_is_derived_from_executed_rows_without_activation() -> None:
    manifest = build_tranche_a_coverage_manifest()
    executed = dict(manifest.executed_counts)
    payload = build_payload()
    assert payload["implementation_count"] == 19
    assert payload["parameter_count"] == 135
    assert payload["oracle_count"] == 19
    assert payload["golden_vector_count"] == 19
    assert payload["certified_source_state_count"] == 29
    assert payload["source_overlay_count"] == 7
    assert payload["source_claim_binding_rule_count"] == 1
    assert executed == {
        "closure_rows": 42,
        "repository_dispositions": 19,
        "parameter_policy_rows": 135,
        "mathematical_specifications": 19,
        "independent_oracle_specifications": 19,
        "golden_vectors_and_invariants": 19,
        "test_rows": 47,
        "validation_command_rows": 10,
        "source_claim_binding_rules": 1,
        "total_rows": 311,
    }
    assert payload["executed_coverage_rows"] == executed
    assert payload["coverage_manifest_schema"] == "TrancheACoverageManifestV1"
    assert validate_domain("architecture").passed
    assert payload["runtime_effect_authorized"] is False
    shared_test_refs = {
        row.subject_ref
        for row in manifest.rows
        if row.row_id.startswith("ST12A-TEST::SHARED::")
    }
    assert shared_test_refs == {
        "tests/fail_closed/test_run_validation_gates.py",
        "tests/tools/test_changed_area_validation_router.py",
        "tests/tools/test_validation_inventory.py",
        "tests/tools/test_validation_scope_registry.py",
        "tests/tools/test_ci_branch_context.py",
    }
    test_rows = tuple(row for row in manifest.rows if row.category == "test_rows")
    assert executed["test_rows"] == len(test_rows)
    assert len({row.row_id for row in test_rows}) == len(test_rows)
    assert all(
        not row.subject_ref.startswith(
            "tools/independent_validate_qku_computation_control_plane"
        )
        and not row.test_path.startswith(
            "tools/independent_validate_qku_computation_control_plane"
        )
        for row in test_rows
    )


def test_manifest_mutation_matrix_fails_closed() -> None:
    manifest = build_tranche_a_coverage_manifest()
    rows = manifest.rows
    with pytest.raises(ContractValidationError):
        validate_tranche_a_coverage_manifest(rows[:-1])
    with pytest.raises(ContractValidationError):
        validate_tranche_a_coverage_manifest((*rows, rows[0]))
    with pytest.raises(ContractValidationError):
        validate_tranche_a_coverage_manifest(
            (replace(rows[0], row_id="ST11-ARCHITECTURE::RENAMED"), *rows[1:])
        )
    with pytest.raises(ContractValidationError):
        replace(rows[0], consumer_refs=())
    for mutation in (
        {"predicate": ""},
        {"test_path": "tests/missing/test_manifest_route.py"},
        {"independent_validator": "tools/missing_validator.py"},
    ):
        with pytest.raises(ContractValidationError):
            validate_tranche_a_coverage_manifest(
                (replace(rows[0], **mutation), *rows[1:])
            )
    with pytest.raises(ContractValidationError):
        build_tranche_a_coverage_manifest(
            predicate_overrides={rows[0].row_id: False}
        )


def test_all_parameter_seeds_and_editable_bounds_are_value_checked() -> None:
    resolved = tuple(
        ParameterPolicyResolverV1.resolve(policy.parameter_id)
        for policy in PARAMETER_POLICIES
    )
    assert len(resolved) == 135
    assert all(
        row.value == policy.effective_day1_seed_value_or_resolution_rule
        and row.used_day1_seed
        for row, policy in zip(resolved, PARAMETER_POLICIES, strict=True)
    )
    assert ParameterPolicyResolverV1.resolve(
        "ST10-PARAM::1288", candidate=10
    ).value == "10"
    assert ParameterPolicyResolverV1.resolve(
        "ST10-PARAM::1289", candidate=150
    ).value == "150"
    assert ParameterPolicyResolverV1.resolve(
        "ST10-PARAM::1290", candidate=Decimal("0.01")
    ).value == "0.01"
    assert ParameterPolicyResolverV1.resolve(
        "ST10-PARAM::1293", candidate="TOP_5"
    ).value == "TOP_5"
    for parameter_id, candidate in (
        ("ST10-PARAM::1288", 1),
        ("ST10-PARAM::1288", Decimal("2.5")),
        ("ST10-PARAM::1289", 100),
        ("ST10-PARAM::1290", Decimal("0")),
        ("ST10-PARAM::1290", Decimal("0.5")),
        ("ST10-PARAM::0801", "ALTERED"),
    ):
        with pytest.raises(ParameterPolicyError):
            ParameterPolicyResolverV1.resolve(
                parameter_id,
                candidate=candidate,
            )
