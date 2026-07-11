from __future__ import annotations

"""Card-specific callable surface for the PR169 formula expansion.

Every exported ``compute_<card>`` object is a distinct callable.  The six
verified PR162D-R2A reuses invoke their existing central callable directly;
the remaining cards invoke the repaired in-place implementation selected by
immutable card identity.  The generic service is only a dispatcher to these
objects and never accepts a caller-authored final result.
"""

from collections.abc import Callable, Mapping
from typing import Any

from .catalog import CARD_NAMES


EXACT_TARGETS: dict[str, dict[str, str]] = {
    "B11": {
        "formula_id": "PR168_GFP2R_FORMULA_ORDERBOOK_IMBALANCE",
        "version": "1.0.0",
        "callable_ref": "src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.formula_seed_library:compute_orderbook_imbalance",
        "output_field": "orderbook_imbalance",
    },
    "B12": {
        "formula_id": "PR162D_R2A::DEPTH_WEIGHTED_MID_PRICE",
        "version": "1.0.0",
        "callable_ref": "src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.formula_seed_library:compute_depth_weighted_mid_price",
        "output_field": "depth_weighted_mid_price",
    },
    "C01": {
        "formula_id": "FORM_MAP3_CALIB_BRIER_001",
        "version": "1.0.0",
        "callable_ref": "src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.formula_seed_library:compute_brier_score",
        "output_field": "brier_score",
    },
    "C02": {
        "formula_id": "FORM_MAP3_CALIB_LOGLOSS_001",
        "version": "1.0.0",
        "callable_ref": "src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.formula_seed_library:compute_log_loss",
        "output_field": "log_loss",
    },
    "D10": {
        "formula_id": "PR162D_R2A::CAPITAL_UTILIZATION",
        "version": "1.0.0",
        "callable_ref": "src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.formula_seed_library:compute_capital_utilization",
        "output_field": "capital_utilization",
    },
    "F08": {
        "formula_id": "PR162D_R2A::ONE_HOT_PENALTY",
        "version": "1.0.0",
        "callable_ref": "src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.formula_seed_library:compute_one_hot_penalty",
        "output_field": "one_hot_penalty",
    },
}


def _central_inputs(card_id: str, values: Mapping[str, Any]) -> dict[str, Any]:
    if card_id == "C01" or card_id == "C02":
        return {
            "actual_outcomes": values.get("actual_outcomes", values.get("outcomes")),
            "predicted_probabilities": values.get(
                "predicted_probabilities", values.get("probabilities")
            ),
        }
    return dict(values)


def _call_exact(card_id: str, values: Mapping[str, Any]) -> Any:
    from importlib import import_module

    target = EXACT_TARGETS[card_id]
    module_name, attribute = target["callable_ref"].split(":", 1)
    result = getattr(import_module(module_name), attribute)(_central_inputs(card_id, values))
    return result[target["output_field"]]


def _make_card_callable(card_id: str) -> Callable[[Mapping[str, Any]], Any]:
    def compute(values: Mapping[str, Any]) -> Any:
        problem_size = int(values.get("__problem_size__", 1))
        if problem_size > 64:
            from .family_j import FormulaDomainError
            raise FormulaDomainError("UNSUPPORTED_OPERATIONAL_ENVELOPE:problem_size")
        if card_id in EXACT_TARGETS:
            return _call_exact(card_id, values)
        if card_id.startswith("J"):
            from .family_j import FAMILY_J_CALLABLES

            return FAMILY_J_CALLABLES[card_id](values)
        from .runtime import _execute_card

        return _execute_card(card_id, values)

    compute.__name__ = f"compute_{card_id}"
    compute.__qualname__ = compute.__name__
    compute.__doc__ = f"Execute immutable formula/procedure card {card_id}."
    return compute


METHOD_CALLABLES: dict[str, Callable[[Mapping[str, Any]], Any]] = {}
for _card_id, _semantic_key in CARD_NAMES:
    _callable = _make_card_callable(_card_id)
    globals()[_callable.__name__] = _callable
    METHOD_CALLABLES[_card_id] = _callable


def callable_ref(card_id: str) -> str:
    if card_id not in METHOD_CALLABLES:
        raise KeyError(card_id)
    return (
        "src.qtt.stage1_prediction_markets.pr169_qku_formula_exp1.methods:"
        f"compute_{card_id}"
    )


__all__ = ["EXACT_TARGETS", "METHOD_CALLABLES", "callable_ref", *[f"compute_{card_id}" for card_id, _ in CARD_NAMES]]
