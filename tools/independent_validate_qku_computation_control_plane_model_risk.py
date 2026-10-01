#!/usr/bin/env python3
"""Independent executable ST12-F model-risk and NO_TRADE validation."""

from __future__ import annotations

import ast
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.qku_independent_math_row_receipt import (  # noqa: E402
    EVIDENCE_TIER,
    PRODUCTION_SYSTEM_UNDER_TEST_WITH_INDEPENDENT_EXPECTED_RESULT,
    TERMINAL_STATE,
    IndependentMathRowEvidenceV1,
    build_envelope,
    evidence_observation,
    format_evidence_line,
    observed_result,
)

from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import (  # noqa: E402
    ReasonCode,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.model_risk import (  # noqa: E402
    MODEL_RISK_CONTROL_IDS_V1,
    NO_TRADE_CONDITION_IDS_V1,
    ModelRiskAdjudicationBasisV1,
    ModelRiskControlEvidenceV1,
    ModelRiskControlStateV1,
    ModelRiskEvidenceAdjudicatorV1,
    ModelRiskLaneEvidenceV1,
    NoTradeConditionOutcomeV1,
    PermanentNoTradeEvidenceComparisonV1,
)


NOW = datetime(2026, 1, 1, 12, tzinfo=UTC)
PACKAGE = ROOT / "src/qtt/stage1_prediction_markets/qku_computation_control_plane"


class _IndependentMath45Rejection(ValueError):
    pass


def _st12f_vector_rows() -> dict[str, dict[str, object]]:
    path = PACKAGE / "oracle_contracts.py"
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    node = next(
        item
        for item in tree.body
        if isinstance(item, ast.AnnAssign)
        and isinstance(item.target, ast.Name)
        and item.target.id == "_ST12F_NEW_VECTOR_ROWS_V1"
    )
    if (
        not isinstance(node.value, ast.Call)
        or not isinstance(node.value.func, ast.Name)
        or node.value.func.id != "MappingProxyType"
        or len(node.value.args) != 1
    ):
        raise ValueError("ST12-F tracked vector owner is not an immutable literal")
    rows = ast.literal_eval(node.value.args[0])
    if not isinstance(rows, dict) or any(
        not isinstance(key, str) or not isinstance(value, dict)
        for key, value in rows.items()
    ):
        raise ValueError("ST12-F tracked vector rows are malformed")
    return rows


def _math45_decimal(inputs: dict[str, object], name: str) -> Decimal:
    if name not in inputs:
        raise _IndependentMath45Rejection(f"{name} is required")
    try:
        value = Decimal(str(inputs[name]))
    except Exception as exc:
        raise _IndependentMath45Rejection(f"{name} must be an exact Decimal") from exc
    if not value.is_finite():
        raise _IndependentMath45Rejection(f"{name} must be finite")
    return value


def _independent_math45(
    raw_inputs: object,
    *,
    unit_basis: str = "declared edge",
    comparison_policy: str = "ABS_TOL_1E-15",
) -> dict[str, object]:
    if not isinstance(raw_inputs, dict):
        raise _IndependentMath45Rejection("MATH-45 inputs must be a mapping")
    if unit_basis != "declared edge":
        raise _IndependentMath45Rejection("MATH-45 unit/basis must be declared edge")
    if comparison_policy != "ABS_TOL_1E-15":
        raise _IndependentMath45Rejection("MATH-45 comparison policy is malformed")
    edge = _math45_decimal(raw_inputs, "estimated_net_edge")
    uncertainty = _math45_decimal(raw_inputs, "uncertainty")
    quantile = _math45_decimal(raw_inputs, "z_or_quantile")
    haircut = _math45_decimal(raw_inputs, "model_risk_haircut")
    if uncertainty < 0 or quantile < 0 or haircut < 0:
        raise _IndependentMath45Rejection(
            "uncertainty, quantile, and model-risk haircut must be nonnegative"
        )
    lcb = edge - quantile * uncertainty - haircut
    return {"lcb_net": lcb, "trade_gate": lcb > 0}


def _math45_rejection(callable_, message: str) -> dict[str, object]:
    try:
        callable_()
    except _IndependentMath45Rejection as exc:
        if message not in str(exc):
            raise ValueError(f"wrong MATH-45 rejection: {exc}") from exc
        return {"exception_type": type(exc).__name__, "message": str(exc)}
    raise ValueError(f"expected MATH-45 rejection was accepted: {message}")


def _build_math45_receipt() -> IndependentMathRowEvidenceV1:
    vector = _st12f_vector_rows()["MATH-45"]
    inputs = vector.get("inputs")
    expected = vector.get("expected")
    policy = vector.get("comparison")
    if (
        not isinstance(inputs, dict)
        or not isinstance(expected, dict)
        or policy != "ABS_TOL_1E-15"
    ):
        raise ValueError("MATH-45 tracked vector contract differs")
    independent = _independent_math45(inputs, comparison_policy=policy)
    tracked_lcb = Decimal(str(expected["lcb_net"]))
    if (
        independent["lcb_net"] != Decimal("0.0508")
        or independent["trade_gate"] is not True
        or abs(independent["lcb_net"] - tracked_lcb) > Decimal("1E-15")
        or expected["trade_gate"] is not True
    ):
        raise ValueError("MATH-45 independent golden reconstruction failed")

    comparison = _comparison(
        lcb=str(independent["lcb_net"]),
        classical="1.1",
    )
    assessment = _adjudicate(comparison=comparison)
    if (
        comparison.execution_adjusted_lcb != independent["lcb_net"]
        or assessment.permanent_no_trade_comparison.execution_adjusted_lcb
        != independent["lcb_net"]
        or assessment.terminal_state != "NO_TRADE"
    ):
        raise ValueError("MATH-45 independent LCB did not bind downstream NO_TRADE")

    boundary_inputs = dict(inputs)
    boundary_inputs["estimated_net_edge"] = "0.0492"
    boundary = _independent_math45(boundary_inputs)
    if boundary != {"lcb_net": Decimal(0), "trade_gate": False}:
        raise ValueError("MATH-45 zero-LCB boundary failed")

    formula_inputs = dict(inputs)
    formula_inputs["estimated_net_edge"] = "0.11"
    formula_mutation = _independent_math45(formula_inputs)
    if formula_mutation["lcb_net"] != Decimal("0.0608"):
        raise ValueError("MATH-45 formula mutation failed")

    precision_inputs = dict(inputs)
    precision_inputs["estimated_net_edge"] = "0.1000000000000001"
    precision_mutation = _independent_math45(precision_inputs)
    if precision_mutation["lcb_net"] != Decimal("0.0508000000000001"):
        raise ValueError("MATH-45 precision mutation failed")

    negative_ledger = {
        name: _math45_rejection(callable_, message)
        for name, callable_, message in (
            (
                "negative_uncertainty",
                lambda: _independent_math45({**inputs, "uncertainty": "-0.01"}),
                "must be nonnegative",
            ),
            (
                "negative_quantile",
                lambda: _independent_math45({**inputs, "z_or_quantile": "-1"}),
                "must be nonnegative",
            ),
            (
                "negative_haircut",
                lambda: _independent_math45(
                    {**inputs, "model_risk_haircut": "-0.01"}
                ),
                "must be nonnegative",
            ),
            (
                "nonfinite_edge",
                lambda: _independent_math45({**inputs, "estimated_net_edge": "NaN"}),
                "must be finite",
            ),
            (
                "missing_edge",
                lambda: _independent_math45(
                    {key: value for key, value in inputs.items() if key != "estimated_net_edge"}
                ),
                "estimated_net_edge is required",
            ),
            (
                "wrong_basis",
                lambda: _independent_math45(inputs, unit_basis="currency"),
                "unit/basis must be declared edge",
            ),
            (
                "wrong_comparison_policy",
                lambda: _independent_math45(inputs, comparison_policy="ABS_TOL_1E-12"),
                "comparison policy is malformed",
            ),
        )
    }

    return IndependentMathRowEvidenceV1(
        math_id="MATH-45",
        domain_owner=(
            "tools/independent_validate_qku_computation_control_plane_model_risk.py"
        ),
        oracle_id="ORACLE::MATH-45",
        golden_vector_id="GOLDEN::MATH-45",
        comparison_policy=policy,
        evidence_tier=EVIDENCE_TIER,
        observed_result=observed_result(
            independent_observation=independent,
            independent_expected_result={
                "lcb_net": Decimal("0.0508"),
                "trade_gate": True,
            },
            system_under_test_observation={
                "comparison_field": "execution_adjusted_lcb",
                "bound_lcb_net": comparison.execution_adjusted_lcb,
                "assessment_terminal_state": assessment.terminal_state,
                "permanent_no_trade_wins": assessment.permanent_no_trade_wins,
            },
            comparison_passed=True,
        ),
        boundary_or_invariant_observation=evidence_observation(
            "LCB_ZERO_STRICT_TRADE_GATE_BOUNDARY",
            "BOUNDARY_PASS",
            {
                "estimated_net_edge": "0.0492",
                "observed_lcb_net": boundary["lcb_net"],
                "observed_trade_gate": boundary["trade_gate"],
            },
        ),
        negative_or_abstention_observation=evidence_observation(
            "MATH45_EXACT_NEGATIVE_CONTRACT_MATRIX",
            "TYPED_REJECTION",
            negative_ledger,
        ),
        formula_or_procedure_mutation_observation=evidence_observation(
            "ESTIMATED_NET_EDGE_FORMULA_MUTATION",
            "OBSERVED_OUTPUT_CHANGE",
            {
                "input_path": ["estimated_net_edge"],
                "baseline_value": inputs["estimated_net_edge"],
                "replacement_value": "0.11",
                "baseline_result": independent,
                "mutated_result": formula_mutation,
            },
        ),
        domain_guard_observation=evidence_observation(
            "NONNEGATIVE_UNCERTAINTY_GUARD",
            "TYPED_REJECTION",
            negative_ledger["negative_uncertainty"],
        ),
        precision_or_tolerance_observation=evidence_observation(
            "ABS_TOL_1E-15_EDGE_PRECISION_MUTATION",
            "OBSERVED_OUTPUT_CHANGE",
            {
                "input_path": ["estimated_net_edge"],
                "baseline_value": inputs["estimated_net_edge"],
                "replacement_value": "0.1000000000000001",
                "baseline_result": independent,
                "mutated_result": precision_mutation,
                "comparison_policy": policy,
            },
        ),
        source_unit_or_binding_observation=evidence_observation(
            "DECLARED_EDGE_UNIT_BASIS_AND_DOWNSTREAM_FIELD_BINDING",
            "TYPED_REJECTION_AND_SUT_BINDING_PASS",
            {
                "wrong_basis_rejection": negative_ledger["wrong_basis"],
                "downstream_field": "PermanentNoTradeEvidenceComparisonV1.execution_adjusted_lcb",
                "downstream_value": comparison.execution_adjusted_lcb,
                "downstream_terminal_state": assessment.terminal_state,
            },
        ),
        independence_class=(
            PRODUCTION_SYSTEM_UNDER_TEST_WITH_INDEPENDENT_EXPECTED_RESULT
        ),
        production_system_under_test_invocation_count=1,
        production_expected_value_import_count=0,
        production_oracle_call_count=0,
        external_effect_count=0,
        terminal_state=TERMINAL_STATE,
    )


def _controls() -> tuple[ModelRiskControlEvidenceV1, ...]:
    return tuple(
        ModelRiskControlEvidenceV1(
            identity,
            ModelRiskControlStateV1.PASS_RECEIPTED,
            (f"R::{identity}",),
            (),
            (),
            True,
        )
        for identity in MODEL_RISK_CONTROL_IDS_V1
    )


def _caller_false_conditions() -> tuple[NoTradeConditionOutcomeV1, ...]:
    return tuple(
        NoTradeConditionOutcomeV1(identity, False, (f"R::{identity}",), ())
        for identity in NO_TRADE_CONDITION_IDS_V1
    )


def _comparison(
    *,
    lcb: str = "0.1",
    candidate: str = "1",
    classical: str = "0.8",
    no_trade: str = "0",
) -> PermanentNoTradeEvidenceComparisonV1:
    utilities = {
        "CANDIDATE": Decimal(candidate),
        "STRONGEST_CLASSICAL": Decimal(classical),
        "NO_TRADE": Decimal(no_trade),
    }
    priority = {"NO_TRADE": 0, "STRONGEST_CLASSICAL": 1, "CANDIDATE": 2}
    strongest = sorted(
        utilities, key=lambda name: (-utilities[name], priority[name])
    )[0]
    return PermanentNoTradeEvidenceComparisonV1(
        "C::1",
        "LOCK::1",
        Decimal(lcb),
        utilities["CANDIDATE"],
        utilities["STRONGEST_CLASSICAL"],
        utilities["NO_TRADE"],
        strongest,
    )


def _lane(lane: str, *, lock: str = "LOCK::1", scope: str = "MATH-01") -> ModelRiskLaneEvidenceV1:
    return ModelRiskLaneEvidenceV1(
        lane=lane,
        result_receipt_ref=f"R::{lane}",
        input_lock_id=lock,
        component_or_template_ref=scope,
        observed_at=NOW - timedelta(minutes=1),
        valid_until=NOW + timedelta(minutes=5),
    )


def _basis(**overrides: object) -> ModelRiskAdjudicationBasisV1:
    values: dict[str, object] = {
        "expected_component_or_template_ref": "MATH-01",
        "evaluated_at": NOW,
        "required_evidence_valid_until": NOW + timedelta(minutes=5),
        "required_evidence_receipt_refs": ("R::REQUIRED",),
        "replay_lane": _lane("REPLAY"),
        "paper_lane": _lane("PAPER"),
        "uncertainty_reserve": Decimal("0.05"),
        "model_risk_reserve": Decimal("0.05"),
        "capacity_hard_veto": False,
        "liquidity_hard_veto": False,
        "capacity_liquidity_receipt_refs": ("R::CAPACITY",),
        "independent_review_state": "READY_FOR_INDEPENDENT_REVIEW",
        "independent_review_receipt_ref": "R::REVIEW",
    }
    values.update(overrides)
    return ModelRiskAdjudicationBasisV1(**values)


def _adjudicate(
    *,
    controls: tuple[ModelRiskControlEvidenceV1, ...] | None = None,
    comparison: PermanentNoTradeEvidenceComparisonV1 | None = None,
    basis: ModelRiskAdjudicationBasisV1 | None = None,
):
    return ModelRiskEvidenceAdjudicatorV1().adjudicate(
        assessment_id="A::1",
        input_lock_id="LOCK::1",
        controls=_controls() if controls is None else controls,
        conditions=_caller_false_conditions(),
        comparison=_comparison() if comparison is None else comparison,
        adjudication_basis=_basis() if basis is None else basis,
        limitations=("L::1",),
        receipt_refs=("R::ASSESSMENT",),
    )


def _v35_independent_condition_matrix():
    """Independent Boolean table; production provides only the observed outcome."""
    from decimal import localcontext, ROUND_DOWN, ROUND_UP, Inexact, Overflow
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.context import decimal_context_v1
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import NumericDomainError
    names = ("NEGATIVE_OR_ZERO_EXECUTION_ADJUSTED_LCB", "MISSING_OR_STALE_REQUIRED_EVIDENCE",
             "REPLAY_OR_PAPER_LANE_MISSING", "LOCK_OR_SCOPE_CONFLICT",
             "UNCERTAINTY_OR_MODEL_RISK_DOMINATES_EDGE", "CAPACITY_OR_LIQUIDITY_HARD_VETO",
             "STRONGEST_CLASSICAL_OR_NO_TRADE_DOMINATES", "INDEPENDENT_REVIEW_NOT_CLOSED")
    controls, comparison = _controls(), _comparison()
    basis = _basis(independent_review_state="CLOSED_INDEPENDENTLY_VALIDATED")
    for mask in range(256):
        conditions = tuple(NoTradeConditionOutcomeV1(name, bool(mask & (1 << bit)),
            (f"SYNTHETIC::INDEPENDENT::{bit}",),
            (ReasonCode.ST12F_MODEL_RISK_VETO,) if mask & (1 << bit) else ())
            for bit, name in enumerate(names))
        result = ModelRiskEvidenceAdjudicatorV1().adjudicate(
            assessment_id="SYNTHETIC::V35::" + str(mask), input_lock_id="LOCK::1",
            controls=controls, conditions=conditions, comparison=comparison,
            adjudication_basis=basis, limitations=("SYNTHETIC_ONLY",), receipt_refs=("R::ASSESSMENT",))
        expected = ("NO_TRADE" if any(mask & (1 << bit) for bit in range(7)) else
                    "READY_FOR_INDEPENDENT_REVIEW" if mask & 128 else "CLOSED_INDEPENDENTLY_VALIDATED")
        if (result.terminal_state != expected or result.control_evidence is not controls
                or result.permanent_no_trade_comparison is not comparison or result.adjudication_basis is not basis
                or result.automatic_promotion_allowed is not False):
            raise ValueError("V35 independent condition decision or original basis mismatch: " + str(mask))
        for before, after in zip(conditions, result.no_trade_condition_outcomes, strict=True):
            if (before.condition_id != after.condition_id or before.active is not after.active
                    or not set(before.reason_codes) <= set(after.reason_codes)
                    or not set(before.evidence_receipt_refs) <= set(after.evidence_receipt_refs)):
                raise ValueError("V35 incoming condition evidence was lost")
    for precision, rounding in ((2, ROUND_DOWN), (9, ROUND_UP), (50, ROUND_DOWN)):
        with localcontext() as context:
            context.prec, context.rounding, context.Emin, context.Emax = precision, rounding, -10, 10
            before = (context.prec, context.rounding, context.Emin, context.Emax,
                      context.capitals, context.clamp, dict(context.traps), dict(context.flags))
            result = _adjudicate(controls=controls, comparison=comparison, basis=basis)
            if result.terminal_state != "CLOSED_INDEPENDENTLY_VALIDATED":
                raise ValueError("V35 exact admitted reserve comparison changed")
            reserves = replace(basis,
                uncertainty_reserve=Decimal("0.50000000000000000000000000004"),
                model_risk_reserve=Decimal("0.50000000000000000000000000004"))
            edge = replace(comparison, candidate_utility=Decimal("1.00000000000000000000000000007"))
            result = _adjudicate(controls=controls, comparison=edge, basis=reserves)
            if (result.terminal_state != "NO_TRADE" or not result.no_trade_condition_outcomes[4].active
                    or result.permanent_no_trade_comparison is not edge or result.adjudication_basis is not reserves):
                raise ValueError("V35 exact reserve boundary lost its original veto or basis")
            for candidate, classical, no_trade, winner in (
                    ("1.004", "1.003", "1.002", "CANDIDATE"),
                    ("1", "1", "1", "NO_TRADE"),
                    ("1", "1", "0.9", "STRONGEST_CLASSICAL")):
                ordered = replace(comparison, candidate_utility=Decimal(candidate),
                    strongest_classical_utility=Decimal(classical), no_trade_utility=Decimal(no_trade),
                    strongest_comparator=winner)
                if (ordered.strongest_comparator != winner or
                        (ordered.candidate_utility, ordered.strongest_classical_utility, ordered.no_trade_utility)
                        != (Decimal(candidate), Decimal(classical), Decimal(no_trade))):
                    raise ValueError("V35 exact comparator ordering or original values changed")
            overflow_operand = Decimal((0, (9,), decimal_context_v1().Emax))
            for uncertainty, model_risk, cause in (
                    (Decimal("1"), Decimal("1E-34"), Inexact),
                    (overflow_operand, overflow_operand, Overflow)):
                unrepresentable = replace(basis, uncertainty_reserve=uncertainty, model_risk_reserve=model_risk)
                try:
                    _adjudicate(controls=controls, comparison=comparison, basis=unrepresentable)
                except NumericDomainError as rejected:
                    if rejected.reason_code is not ReasonCode.INVALID_NUMERIC_INPUT or type(rejected.__cause__) is not cause:
                        raise ValueError("V35 reserve failure lost its original Decimal cause") from rejected
                else:
                    raise ValueError("V35 unrepresentable reserve sum was admitted")
            trailing_zero = replace(basis,
                uncertainty_reserve=Decimal("1.0000000000000000000000000000000000"), model_risk_reserve=Decimal("0"))
            result = _adjudicate(controls=controls, comparison=comparison, basis=trailing_zero)
            if result.terminal_state != "NO_TRADE" or not result.no_trade_condition_outcomes[4].active:
                raise ValueError("V35 exact trailing-zero reserve sum was rounded or rejected")
            if before != (context.prec, context.rounding, context.Emin, context.Emax,
                          context.capitals, context.clamp, dict(context.traps), dict(context.flags)):
                raise ValueError("V35 canonical arithmetic changed the caller's Decimal context")


def main() -> int:
    try:
        receipt_row = _build_math45_receipt()
        _v35_independent_condition_matrix()
    except (OSError, SyntaxError, ValueError, KeyError, TypeError) as exc:
        print(f"QKU_MODEL_RISK_INDEPENDENT_VALIDATION_FAILED::{exc}", file=sys.stderr)
        return 1
    stale_controls = list(_controls())
    stale_controls[0] = ModelRiskControlEvidenceV1(
        stale_controls[0].control_id,
        ModelRiskControlStateV1.BLOCKED_WITH_TYPED_REASON,
        (),
        (ReasonCode.STALE_CONTEXT,),
        (),
        False,
    )
    cases = (
        _adjudicate(comparison=_comparison(lcb="0")),
        _adjudicate(controls=tuple(stale_controls)),
        _adjudicate(basis=_basis(replay_lane=None)),
        _adjudicate(basis=_basis(replay_lane=_lane("REPLAY", lock="LOCK::OTHER"))),
        _adjudicate(
            basis=_basis(
                uncertainty_reserve=Decimal("0.6"),
                model_risk_reserve=Decimal("0.4"),
            )
        ),
        _adjudicate(basis=_basis(capacity_hard_veto=True)),
        _adjudicate(comparison=_comparison(classical="1.1")),
        _adjudicate(),
    )
    independently_matched_conditions = tuple(
        next(
            row.active
            for row in assessment.no_trade_condition_outcomes
            if row.condition_id == condition_id
        )
        for assessment, condition_id in zip(
            cases, NO_TRADE_CONDITION_IDS_V1, strict=True
        )
    )

    classical_tie = _adjudicate(comparison=_comparison(classical="1"))
    no_trade_tie = _adjudicate(comparison=_comparison(no_trade="1"))
    review_pending = _adjudicate()
    review_closed = _adjudicate(
        basis=_basis(independent_review_state="CLOSED_INDEPENDENTLY_VALIDATED")
    )

    checks = (
        len(MODEL_RISK_CONTROL_IDS_V1) == 12,
        len(NO_TRADE_CONDITION_IDS_V1) == 8,
        all(independently_matched_conditions),
        all(case.permanent_no_trade_wins for case in cases),
        all(
            case.no_trade_condition_outcomes[index].active
            for index, case in enumerate(cases)
        ),
        classical_tie.terminal_state == "NO_TRADE",
        no_trade_tie.terminal_state == "NO_TRADE",
        review_pending.terminal_state == "READY_FOR_INDEPENDENT_REVIEW",
        review_closed.terminal_state == "CLOSED_INDEPENDENTLY_VALIDATED",
        all(
            ReasonCode.ST12F_MODEL_RISK_VETO in case.blocker_codes
            for case in cases[:1] + cases[4:7]
        ),
        all(case.automatic_promotion_allowed is False for case in cases),
        all(case.champion_challenger_evidence_only is True for case in cases),
    )
    if not all(checks):
        print("QKU_MODEL_RISK_INDEPENDENT_VALIDATION_FAILED", file=sys.stderr)
        return 1
    print(format_evidence_line(build_envelope("MODEL_RISK", (receipt_row,))))
    print(
        "QKU_MODEL_RISK_INDEPENDENTLY_VALIDATED "
        "checks=12 controls=12 derived_conditions=8 strict_comparisons=2"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
