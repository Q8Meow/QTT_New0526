from __future__ import annotations

from copy import deepcopy
import json

import pytest

from tools import qku_independent_math_row_receipt as receipt


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
