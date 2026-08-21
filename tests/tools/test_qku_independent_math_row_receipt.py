from __future__ import annotations

import ast
from copy import deepcopy
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import json
from pathlib import Path

import pytest

from src.qtt.stage1_prediction_markets.qku_computation_control_plane.context import (
    decimal_context_v1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.economic_math import (
    FillProbabilityModelArtifactV1,
    FillQuantityDistributionArtifactV1,
    expected_partial_fill_quantity_v1,
    fill_probability_v1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import (
    NumericDomainError,
    ReasonCode,
)
from tools import qku_independent_math_row_receipt as receipt
from tools import independent_validate_qku_computation_control_plane_execution as execution_receipt


def _valid_row(domain: str, math_id: str) -> receipt.IndependentMathRowEvidenceV1:
    independence_class = receipt.EXPECTED_INDEPENDENCE_CLASS_BY_DOMAIN[domain]
    sut_count = (
        0
        if independence_class
        == receipt.INDEPENDENT_REFERENCE_NO_PRODUCTION_RUNTIME_IMPORT
        else 1
    )
    operation_evidence = receipt.evidence_observation(
        "INDEPENDENT_TEST_OPERATION",
        "OBSERVED",
        {"math_id": math_id, "result": "OBSERVED_RESULT"},
    )
    return receipt.IndependentMathRowEvidenceV1(
        math_id=math_id,
        domain_owner=receipt.EXPECTED_DOMAIN_OWNER[domain],
        oracle_id=f"ORACLE::{math_id}",
        golden_vector_id=f"GOLDEN::{math_id}",
        comparison_policy=receipt.EXPECTED_COMPARISON_POLICY_BY_MATH_ID[math_id],
        evidence_tier=receipt.EVIDENCE_TIER,
        observed_result=receipt.observed_result(
            independent_observation={"value": math_id},
            independent_expected_result={"value": math_id},
            system_under_test_observation=(
                receipt.NO_PRODUCTION_SYSTEM_UNDER_TEST
                if sut_count == 0
                else {"value": math_id}
            ),
            comparison_passed=True,
        ),
        boundary_or_invariant_observation=operation_evidence,
        negative_or_abstention_observation=operation_evidence,
        formula_or_procedure_mutation_observation=operation_evidence,
        domain_guard_observation=operation_evidence,
        precision_or_tolerance_observation=operation_evidence,
        source_unit_or_binding_observation=operation_evidence,
        independence_class=independence_class,
        production_system_under_test_invocation_count=sut_count,
        production_expected_value_import_count=0,
        production_oracle_call_count=0,
        external_effect_count=0,
        terminal_state=receipt.TERMINAL_STATE,
    )


def _valid_envelope(domain: str) -> receipt.IndependentMathEvidenceEnvelopeV1:
    return receipt.build_envelope(
        domain,
        tuple(
            _valid_row(domain, math_id)
            for math_id in receipt.EXPECTED_DOMAIN_MATH_IDS[domain]
        ),
    )


def _line(payload: object, *, allow_nan: bool = False) -> str:
    return (
        f"{receipt.EVIDENCE_PREFIX} "
        + json.dumps(
            payload,
            ensure_ascii=False,
            allow_nan=allow_nan,
            separators=(",", ":"),
            sort_keys=True,
        )
    )


def _production_fill_distribution(
    distribution: tuple[tuple[object, object], ...],
    normalization_tolerance: object,
    *,
    order_quantity: object = "100",
) -> FillQuantityDistributionArtifactV1:
    evaluated = datetime(2026, 1, 1, tzinfo=UTC)
    return FillQuantityDistributionArtifactV1(
        artifact_id="TEST::MATH-38::DISTRIBUTION",
        artifact_version="1",
        source_binding_ref="TEST::MATH-38::SOURCE",
        scope_ref="TEST::MATH-38::SCOPE",
        horizon_seconds=30,
        evaluated_at=evaluated,
        artifact_valid_until=datetime(2026, 1, 2, tzinfo=UTC),
        order_quantity=order_quantity,  # type: ignore[arg-type]
        normalization_tolerance=normalization_tolerance,
        fill_quantity_distribution=distribution,  # type: ignore[arg-type]
    )


def _production_fill_probability(
    probability: object,
) -> tuple[FillProbabilityModelArtifactV1, Decimal]:
    observed = datetime(2026, 1, 1, tzinfo=UTC)
    artifact = FillProbabilityModelArtifactV1(
        artifact_id="TEST::MATH-37::MODEL",
        artifact_version="1",
        feature_schema_ref="TEST::MATH-37::FEATURES",
        calibration_receipt_ref="TEST::MATH-37::CALIBRATION",
        scope_ref="TEST::MATH-37::SCOPE",
        horizon_seconds=5,
        probability=probability,  # type: ignore[arg-type]
        feature_snapshot_ref="TEST::MATH-37::SNAPSHOT",
        feature_observed_at=observed,
        evaluated_at=observed + timedelta(seconds=1),
        artifact_valid_until=observed + timedelta(minutes=1),
        maximum_feature_age=timedelta(seconds=5),
        calibration_state="VALIDATED",
    )
    return artifact, fill_probability_v1(
        artifact=artifact,
        feature_schema_ref="TEST::MATH-37::FEATURES",
        scope_ref="TEST::MATH-37::SCOPE",
        horizon_seconds=5,
    )


def test_receipt_schema_serialization_and_parser_are_canonical() -> None:
    envelope = _valid_envelope("ACCOUNTING")
    evidence_line = receipt.format_evidence_line(envelope)

    assert evidence_line.count(receipt.EVIDENCE_PREFIX) == 2
    assert receipt.parse_evidence_line(evidence_line) == envelope
    assert receipt.format_evidence_line(receipt.parse_evidence_line(evidence_line)) == evidence_line
    assert tuple(row.math_id for row in envelope.rows) == tuple(
        f"MATH-{number:02d}" for number in range(26, 37)
    )
    assert envelope.denominators["marker_only_row_count"] == 0
    assert envelope.denominators["declared_step_only_observation_count"] == 0
    assert envelope.denominators["external_effect_count"] == 0


def test_receipt_domains_have_exact_ordered_membership() -> None:
    combined: list[str] = []
    for domain, expected_ids in receipt.EXPECTED_DOMAIN_MATH_IDS.items():
        envelope = receipt.parse_evidence_line(
            receipt.format_evidence_line(_valid_envelope(domain))
        )
        assert envelope.domain == domain
        assert envelope.ordered_math_ids == expected_ids
        assert tuple(row.math_id for row in envelope.rows) == expected_ids
        assert envelope.row_count == len(expected_ids)
        combined.extend(expected_ids)

    assert tuple(combined) == (
        *(f"MATH-{number:02d}" for number in range(26, 40)),
        "MATH-45",
        "MATH-50",
        "MATH-51",
        "MATH-52",
    )
    assert len(combined) == len(set(combined)) == 18

    def independent_probability(value: object) -> Decimal:
        return execution_receipt._independent_fill_probability(
            execution_receipt._fill_probability_fixture(5, value),
            feature_schema_ref="GOLDEN::FEATURES",
            scope_ref="GOLDEN::SCOPE",
            horizon_seconds=5,
        )

    def independent_fill(
        distribution: tuple[tuple[object, object], ...],
        tolerance: object = "0",
        *,
        order_quantity: object = "100",
    ) -> Decimal:
        return execution_receipt._independent_expected_fill(
            execution_receipt._distribution_fixture(
                distribution,
                normalization_tolerance=tolerance,
                order_quantity=order_quantity,
            )
        )

    def production_fill(
        distribution: tuple[tuple[object, object], ...],
        tolerance: object = "0",
        *,
        order_quantity: object = "100",
    ) -> Decimal:
        return expected_partial_fill_quantity_v1(
            artifact=_production_fill_distribution(
                distribution,
                tolerance,
                order_quantity=order_quantity,
            )
        )

    def assert_numeric_rejection_pair(
        independent_call,
        production_call,
        expected_family: str,
    ) -> None:
        with pytest.raises(
            execution_receipt._IndependentArtifactRejection
        ) as independent_error:
            independent_call()
        assert independent_error.value.failure_family == expected_family
        with pytest.raises(NumericDomainError) as production_error:
            production_call()
        assert production_error.value.reason_code is getattr(
            ReasonCode, expected_family
        )

    math37_high_precision_text = "0.12345678901234567890123456789012345"
    math37_string_expected = Decimal("0.1234567890123456789012345678901234")
    independent_string_result = independent_probability(math37_high_precision_text)
    _, production_string_result = _production_fill_probability(
        math37_high_precision_text
    )
    assert independent_string_result == math37_string_expected
    assert production_string_result == math37_string_expected

    math37_decimal_input = Decimal(math37_high_precision_text)
    independent_decimal_artifact = execution_receipt._fill_probability_fixture(
        5, math37_decimal_input
    )
    independent_decimal_result = execution_receipt._independent_fill_probability(
        independent_decimal_artifact,
        feature_schema_ref="GOLDEN::FEATURES",
        scope_ref="GOLDEN::SCOPE",
        horizon_seconds=5,
    )
    production_decimal_artifact, production_decimal_result = (
        _production_fill_probability(math37_decimal_input)
    )
    assert independent_decimal_artifact.probability is math37_decimal_input
    assert production_decimal_artifact.probability is math37_decimal_input
    assert independent_decimal_result is math37_decimal_input
    assert production_decimal_result is math37_decimal_input
    assert independent_decimal_result == Decimal(math37_high_precision_text)

    assert_numeric_rejection_pair(
        lambda: independent_probability(0.4),
        lambda: _production_fill_probability(0.4),
        "FLOAT_DECIMAL_CONTAMINATION",
    )
    context_overflow_text = f"1e{decimal_context_v1().Emax + 1}"
    assert_numeric_rejection_pair(
        lambda: independent_probability(context_overflow_text),
        lambda: _production_fill_probability(context_overflow_text),
        "INVALID_NUMERIC_INPUT",
    )
    decimal_tuple_representation = (0, (1, 2, 3), -2)
    decimal_list_representation = [0, (1, 2, 3), -2]
    assert_numeric_rejection_pair(
        lambda: independent_probability(decimal_tuple_representation),
        lambda: _production_fill_probability(decimal_tuple_representation),
        "INVALID_NUMERIC_INPUT",
    )

    math38_high_precision_distribution = (
        ("76.619839145498174104090161033962172", "0.5"),
        ("0", "0.5"),
    )
    math38_high_precision_expected = Decimal(
        "38.30991957274908705204508051698108"
    )
    assert (
        independent_fill(math38_high_precision_distribution)
        == math38_high_precision_expected
    )
    assert (
        production_fill(math38_high_precision_distribution)
        == math38_high_precision_expected
    )
    assert independent_fill(math38_high_precision_distribution) != Decimal(
        "38.30991957274908705204508051698109"
    )

    normalized_distribution: tuple[tuple[object, object], ...] = (
        ("0", "0.5"),
        ("100", "0.5"),
    )
    float_contamination_cases = (
        (
            lambda: independent_fill(
                normalized_distribution, order_quantity=100.0
            ),
            lambda: production_fill(
                normalized_distribution, order_quantity=100.0
            ),
        ),
        (
            lambda: independent_fill(normalized_distribution, 0.0),
            lambda: production_fill(normalized_distribution, 0.0),
        ),
        (
            lambda: independent_fill(((0.0, "0.5"), ("100", "0.5"))),
            lambda: production_fill(((0.0, "0.5"), ("100", "0.5"))),
        ),
        (
            lambda: independent_fill((("0", 0.5), ("100", "0.5"))),
            lambda: production_fill((("0", 0.5), ("100", "0.5"))),
        ),
    )
    for independent_call, production_call in float_contamination_cases:
        assert_numeric_rejection_pair(
            independent_call,
            production_call,
            "FLOAT_DECIMAL_CONTAMINATION",
        )

    for unsupported_numeric in (
        decimal_tuple_representation,
        decimal_list_representation,
    ):
        assert_numeric_rejection_pair(
            lambda value=unsupported_numeric: independent_fill(
                ((value, "0.5"), ("100", "0.5"))
            ),
            lambda value=unsupported_numeric: production_fill(
                ((value, "0.5"), ("100", "0.5"))
            ),
            "INVALID_NUMERIC_INPUT",
        )

    assert_numeric_rejection_pair(
        lambda: independent_fill((("not-a-number", "0.5"), ("100", "0.5"))),
        lambda: production_fill((("not-a-number", "0.5"), ("100", "0.5"))),
        "INVALID_NUMERIC_INPUT",
    )
    assert_numeric_rejection_pair(
        lambda: independent_fill(
            ((context_overflow_text, "0.5"), ("100", "0.5"))
        ),
        lambda: production_fill(
            ((context_overflow_text, "0.5"), ("100", "0.5"))
        ),
        "INVALID_NUMERIC_INPUT",
    )
    assert_numeric_rejection_pair(
        lambda: independent_fill((("0", "NaN"), ("100", "0.5"))),
        lambda: production_fill((("0", "NaN"), ("100", "0.5"))),
        "NONFINITE_NUMERIC_INPUT",
    )
    assert_numeric_rejection_pair(
        lambda: independent_fill(normalized_distribution, order_quantity=True),
        lambda: production_fill(normalized_distribution, order_quantity=True),
        "FLOAT_DECIMAL_CONTAMINATION",
    )

    class NumericLookingObject:
        def __str__(self) -> str:
            return "0.5"

    numeric_looking_object = NumericLookingObject()
    assert_numeric_rejection_pair(
        lambda: independent_probability(numeric_looking_object),
        lambda: _production_fill_probability(numeric_looking_object),
        "INVALID_NUMERIC_INPUT",
    )

    math38_admitted_cases = (
        (
            (("0", "0.2"), ("50", "0.3"), ("100", "0.5")),
            "0",
            Decimal("1"),
            Decimal("65.0"),
            Decimal("65"),
        ),
        (
            (("0", "0.2"), ("50", "0.3"), ("100", "0.5000000000005")),
            "0.000000000001",
            Decimal("1.0000000000005"),
            Decimal("65.0000000000500"),
            Decimal("65.00000000001749999999999125000000"),
        ),
        (
            (("0", "0.2"), ("50", "0.3"), ("100", "0.500000000001")),
            "0.000000000001",
            Decimal("1.000000000001"),
            Decimal("65.000000000100"),
            Decimal("65.00000000003499999999996500000000"),
        ),
    )
    for distribution, tolerance, expected_sum, expected_weighted, expected in (
        math38_admitted_cases
    ):
        independent_computation = (
            execution_receipt._independent_expected_fill_computation(
                execution_receipt._distribution_fixture(
                    distribution,
                    normalization_tolerance=tolerance,
                )
            )
        )
        assert independent_computation.probability_sum == expected_sum
        assert independent_computation.weighted_sum == expected_weighted
        assert independent_computation.normalized_expected_fill == expected
        production_result = expected_partial_fill_quantity_v1(
            artifact=_production_fill_distribution(distribution, tolerance)
        )
        assert production_result == expected
        assert independent_computation.normalized_expected_fill == production_result

    within_tolerance_raw_sum = math38_admitted_cases[1][3]
    within_tolerance_expected = math38_admitted_cases[1][4]
    assert within_tolerance_raw_sum != within_tolerance_expected

    outside_tolerance_distribution = (
        ("0", "0.2"),
        ("50", "0.3"),
        ("100", "0.500000000002"),
    )
    with pytest.raises(
        execution_receipt._IndependentArtifactRejection,
        match="fill probabilities exceed",
    ):
        execution_receipt._independent_expected_fill(
            execution_receipt._distribution_fixture(
                outside_tolerance_distribution,
                normalization_tolerance="0.000000000001",
            )
        )
    with pytest.raises(NumericDomainError, match="fill probabilities exceed"):
        expected_partial_fill_quantity_v1(
            artifact=_production_fill_distribution(
                outside_tolerance_distribution,
                "0.000000000001",
            )
        )

    execution_source = Path(execution_receipt.__file__).read_text(encoding="utf-8")
    execution_tree = ast.parse(execution_source)
    imported_modules = {
        alias.name
        for node in ast.walk(execution_tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    } | {
        node.module or ""
        for node in ast.walk(execution_tree)
        if isinstance(node, ast.ImportFrom)
    }
    assert not any(
        name == "qtt"
        or name.startswith("qtt.")
        or name == "src.qtt"
        or name.startswith("src.qtt.")
        for name in imported_modules
    )
    assert not any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "expected_partial_fill_quantity_v1"
        for node in ast.walk(execution_tree)
    )


def test_receipt_adversarial_mutations_fail_closed() -> None:
    valid_line = receipt.format_evidence_line(_valid_envelope("ACCOUNTING"))
    baseline = receipt.envelope_payload(_valid_envelope("ACCOUNTING"))
    malformed_lines = (
        f"{receipt.EVIDENCE_PREFIX} {{",
        f"{receipt.EVIDENCE_PREFIX} [] trailing",
        f"{receipt.EVIDENCE_PREFIX} {{\"value\":NaN}}",
        f"{receipt.EVIDENCE_PREFIX} {{\"value\":Infinity}}",
        valid_line + " trailing-material",
    )
    duplicate_key_line = valid_line.replace(
        '"domain":"ACCOUNTING"',
        '"domain":"ACCOUNTING","domain":"ACCOUNTING"',
        1,
    )
    for invalid_line in (*malformed_lines, duplicate_key_line):
        with pytest.raises(receipt.MathRowReceiptValidationError):
            receipt.parse_evidence_line(invalid_line)

    mutations: list[dict[str, object]] = []

    def mutated(change) -> dict[str, object]:
        payload = deepcopy(baseline)
        change(payload)
        mutations.append(payload)
        return payload

    mutated(lambda payload: payload.pop("schema_version"))
    mutated(lambda payload: payload.__setitem__("extra_envelope_field", True))
    mutated(lambda payload: payload["rows"][0].pop("oracle_id"))
    mutated(lambda payload: payload["rows"][0].__setitem__("extra_row_field", True))
    mutated(lambda payload: payload["rows"].__setitem__(1, deepcopy(payload["rows"][0])))
    mutated(lambda payload: payload["rows"].pop())
    mutated(lambda payload: payload["rows"].append(deepcopy(payload["rows"][-1])))
    mutated(lambda payload: payload["rows"].__setitem__(slice(0, 2), reversed(payload["rows"][:2])))
    mutated(lambda payload: payload.__setitem__("domain", "EXECUTION"))
    mutated(lambda payload: payload["rows"][0].__setitem__("domain_owner", "tools/wrong_owner.py"))
    mutated(lambda payload: payload["rows"][0].__setitem__("oracle_id", "ORACLE::WRONG"))
    mutated(lambda payload: payload["rows"][0].__setitem__("golden_vector_id", "GOLDEN::WRONG"))
    mutated(lambda payload: payload["rows"][0].__setitem__("comparison_policy", "FALSE_POLICY"))
    mutated(lambda payload: payload["rows"][0]["observed_result"].__setitem__("independent_observation", {"marker": "VALIDATED"}))
    mutated(lambda payload: payload["rows"][0]["observed_result"].__setitem__("independent_observation", {"algorithm_steps": ["declared only"]}))
    mutated(lambda payload: payload["rows"][0].__setitem__("formula_or_procedure_mutation_observation", None))
    mutated(lambda payload: payload["rows"][0]["observed_result"].__setitem__("expected_result_source", "PRODUCTION_RESULT"))
    mutated(lambda payload: payload["rows"][0].__setitem__("production_expected_value_import_count", 1))
    mutated(lambda payload: payload["rows"][0].__setitem__("production_oracle_call_count", 1))
    mutated(lambda payload: payload["rows"][0].__setitem__("external_effect_count", 1))
    mutated(lambda payload: payload["rows"][0].__setitem__("terminal_state", "DECLARED_ONLY"))
    mutated(lambda payload: payload["denominators"].__setitem__("row_count", 999))

    for payload in mutations:
        with pytest.raises(receipt.MathRowReceiptValidationError):
            receipt.parse_evidence_line(_line(payload))
