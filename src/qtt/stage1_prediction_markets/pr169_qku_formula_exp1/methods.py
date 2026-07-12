from __future__ import annotations

"""Literal, audited card-to-callable registry.

The registry deliberately contains no loop-driven wrapper creation, ``globals``
mutation, semantic-name dispatch, or untrusted import resolution.  Each public
symbol is source-visible and bound by immutable card identity.
"""

from collections.abc import Mapping
from typing import Any

from src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.formula_seed_library import (
    compute_brier_score as _central_brier_score,
    compute_capital_utilization as _central_capital_utilization,
    compute_depth_weighted_mid_price as _central_depth_weighted_mid_price,
    compute_log_loss as _central_log_loss,
    compute_one_hot_penalty as _central_one_hot_penalty,
    compute_orderbook_imbalance as _central_orderbook_imbalance,
)

from .family_j import FAMILY_J_CALLABLES
from .family_j import FormulaDomainError
from .runtime import _execute_card


EXACT_TARGETS = {
    "B11": {"formula_id": "PR168_GFP2R_FORMULA_ORDERBOOK_IMBALANCE", "version": "1.0.0", "callable_ref": "src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.formula_seed_library:compute_orderbook_imbalance", "output_field": "orderbook_imbalance"},
    "B12": {"formula_id": "PR162D_R2A::DEPTH_WEIGHTED_MID_PRICE", "version": "1.0.0", "callable_ref": "src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.formula_seed_library:compute_depth_weighted_mid_price", "output_field": "depth_weighted_mid_price"},
    "C01": {"formula_id": "FORM_MAP3_CALIB_BRIER_001", "version": "1.0.0", "callable_ref": "src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.formula_seed_library:compute_brier_score", "output_field": "brier_score"},
    "C02": {"formula_id": "FORM_MAP3_CALIB_LOGLOSS_001", "version": "1.0.0", "callable_ref": "src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.formula_seed_library:compute_log_loss", "output_field": "log_loss"},
    "D10": {"formula_id": "PR162D_R2A::CAPITAL_UTILIZATION", "version": "1.0.0", "callable_ref": "src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.formula_seed_library:compute_capital_utilization", "output_field": "capital_utilization"},
    "F08": {"formula_id": "PR162D_R2A::ONE_HOT_PENALTY", "version": "1.0.0", "callable_ref": "src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.formula_seed_library:compute_one_hot_penalty", "output_field": "one_hot_penalty"},
}


def _guard_operational_envelope(values: Mapping[str, Any]) -> None:
    if int(values.get("__problem_size__", 1)) > 64:
        raise FormulaDomainError("UNSUPPORTED_OPERATIONAL_ENVELOPE:problem_size")


def compute_A01(values: Mapping[str, Any]) -> Any:
    return _execute_card("A01", values)

def compute_A02(values: Mapping[str, Any]) -> Any:
    return _execute_card("A02", values)

def compute_A03(values: Mapping[str, Any]) -> Any:
    return _execute_card("A03", values)

def compute_A04(values: Mapping[str, Any]) -> Any:
    return _execute_card("A04", values)

def compute_A05(values: Mapping[str, Any]) -> Any:
    return _execute_card("A05", values)

def compute_A06(values: Mapping[str, Any]) -> Any:
    return _execute_card("A06", values)

def compute_A07(values: Mapping[str, Any]) -> Any:
    return _execute_card("A07", values)

def compute_A08(values: Mapping[str, Any]) -> Any:
    return _execute_card("A08", values)

def compute_A09(values: Mapping[str, Any]) -> Any:
    return _execute_card("A09", values)

def compute_A10(values: Mapping[str, Any]) -> Any:
    return _execute_card("A10", values)

def compute_A11(values: Mapping[str, Any]) -> Any:
    return _execute_card("A11", values)

def compute_A12(values: Mapping[str, Any]) -> Any:
    return _execute_card("A12", values)

def compute_A13(values: Mapping[str, Any]) -> Any:
    return _execute_card("A13", values)

def compute_A14(values: Mapping[str, Any]) -> Any:
    return _execute_card("A14", values)

def compute_A15(values: Mapping[str, Any]) -> Any:
    return _execute_card("A15", values)

def compute_A16(values: Mapping[str, Any]) -> Any:
    return _execute_card("A16", values)

def compute_A17(values: Mapping[str, Any]) -> Any:
    return _execute_card("A17", values)

def compute_A18(values: Mapping[str, Any]) -> Any:
    return _execute_card("A18", values)

def compute_A19(values: Mapping[str, Any]) -> Any:
    return _execute_card("A19", values)

def compute_A20(values: Mapping[str, Any]) -> Any:
    return _execute_card("A20", values)

def compute_A21(values: Mapping[str, Any]) -> Any:
    return _execute_card("A21", values)

def compute_A22(values: Mapping[str, Any]) -> Any:
    return _execute_card("A22", values)

def compute_A23(values: Mapping[str, Any]) -> Any:
    return _execute_card("A23", values)

def compute_A24(values: Mapping[str, Any]) -> Any:
    return _execute_card("A24", values)

def compute_A25(values: Mapping[str, Any]) -> Any:
    return _execute_card("A25", values)

def compute_A26(values: Mapping[str, Any]) -> Any:
    return _execute_card("A26", values)

def compute_A27(values: Mapping[str, Any]) -> Any:
    return _execute_card("A27", values)

def compute_A28(values: Mapping[str, Any]) -> Any:
    return _execute_card("A28", values)

def compute_A29(values: Mapping[str, Any]) -> Any:
    return _execute_card("A29", values)

def compute_A30(values: Mapping[str, Any]) -> Any:
    return _execute_card("A30", values)

def compute_A31(values: Mapping[str, Any]) -> Any:
    return _execute_card("A31", values)

def compute_A32(values: Mapping[str, Any]) -> Any:
    return _execute_card("A32", values)

def compute_A33(values: Mapping[str, Any]) -> Any:
    return _execute_card("A33", values)

def compute_B01(values: Mapping[str, Any]) -> Any:
    return _execute_card("B01", values)

def compute_B02(values: Mapping[str, Any]) -> Any:
    return _execute_card("B02", values)

def compute_B03(values: Mapping[str, Any]) -> Any:
    return _execute_card("B03", values)

def compute_B04(values: Mapping[str, Any]) -> Any:
    return _execute_card("B04", values)

def compute_B05(values: Mapping[str, Any]) -> Any:
    return _execute_card("B05", values)

def compute_B06(values: Mapping[str, Any]) -> Any:
    return _execute_card("B06", values)

def compute_B07(values: Mapping[str, Any]) -> Any:
    return _execute_card("B07", values)

def compute_B08(values: Mapping[str, Any]) -> Any:
    return _execute_card("B08", values)

def compute_B09(values: Mapping[str, Any]) -> Any:
    return _execute_card("B09", values)

def compute_B10(values: Mapping[str, Any]) -> Any:
    return _execute_card("B10", values)

def compute_B11(values: Mapping[str, Any]) -> Any:
    _guard_operational_envelope(values)
    return _central_orderbook_imbalance(dict(values))["orderbook_imbalance"]

def compute_B12(values: Mapping[str, Any]) -> Any:
    _guard_operational_envelope(values)
    return _central_depth_weighted_mid_price(dict(values))["depth_weighted_mid_price"]

def compute_B13(values: Mapping[str, Any]) -> Any:
    return _execute_card("B13", values)

def compute_B14(values: Mapping[str, Any]) -> Any:
    return _execute_card("B14", values)

def compute_B15(values: Mapping[str, Any]) -> Any:
    return _execute_card("B15", values)

def compute_B16(values: Mapping[str, Any]) -> Any:
    return _execute_card("B16", values)

def compute_B17(values: Mapping[str, Any]) -> Any:
    return _execute_card("B17", values)

def compute_B18(values: Mapping[str, Any]) -> Any:
    return _execute_card("B18", values)

def compute_B19(values: Mapping[str, Any]) -> Any:
    return _execute_card("B19", values)

def compute_B20(values: Mapping[str, Any]) -> Any:
    return _execute_card("B20", values)

def compute_B21(values: Mapping[str, Any]) -> Any:
    return _execute_card("B21", values)

def compute_C01(values: Mapping[str, Any]) -> Any:
    _guard_operational_envelope(values)
    return _central_brier_score({
        "actual_outcomes": values["outcomes"],
        "predicted_probabilities": values["probabilities"],
    })["brier_score"]

def compute_C02(values: Mapping[str, Any]) -> Any:
    _guard_operational_envelope(values)
    return _central_log_loss({
        "actual_outcomes": values["outcomes"],
        "predicted_probabilities": values["probabilities"],
    })["log_loss"]

def compute_C03(values: Mapping[str, Any]) -> Any:
    return _execute_card("C03", values)

def compute_C04(values: Mapping[str, Any]) -> Any:
    return _execute_card("C04", values)

def compute_C05(values: Mapping[str, Any]) -> Any:
    return _execute_card("C05", values)

def compute_C06(values: Mapping[str, Any]) -> Any:
    return _execute_card("C06", values)

def compute_C07(values: Mapping[str, Any]) -> Any:
    return _execute_card("C07", values)

def compute_C08(values: Mapping[str, Any]) -> Any:
    return _execute_card("C08", values)

def compute_C09(values: Mapping[str, Any]) -> Any:
    return _execute_card("C09", values)

def compute_C10(values: Mapping[str, Any]) -> Any:
    return _execute_card("C10", values)

def compute_C11(values: Mapping[str, Any]) -> Any:
    return _execute_card("C11", values)

def compute_C12(values: Mapping[str, Any]) -> Any:
    return _execute_card("C12", values)

def compute_C13(values: Mapping[str, Any]) -> Any:
    return _execute_card("C13", values)

def compute_C14(values: Mapping[str, Any]) -> Any:
    return _execute_card("C14", values)

def compute_C15(values: Mapping[str, Any]) -> Any:
    return _execute_card("C15", values)

def compute_C16(values: Mapping[str, Any]) -> Any:
    return _execute_card("C16", values)

def compute_C17(values: Mapping[str, Any]) -> Any:
    return _execute_card("C17", values)

def compute_C18(values: Mapping[str, Any]) -> Any:
    return _execute_card("C18", values)

def compute_C19(values: Mapping[str, Any]) -> Any:
    return _execute_card("C19", values)

def compute_C20(values: Mapping[str, Any]) -> Any:
    return _execute_card("C20", values)

def compute_C21(values: Mapping[str, Any]) -> Any:
    return _execute_card("C21", values)

def compute_C22(values: Mapping[str, Any]) -> Any:
    return _execute_card("C22", values)

def compute_C23(values: Mapping[str, Any]) -> Any:
    return _execute_card("C23", values)

def compute_C24(values: Mapping[str, Any]) -> Any:
    return _execute_card("C24", values)

def compute_C25(values: Mapping[str, Any]) -> Any:
    return _execute_card("C25", values)

def compute_D01(values: Mapping[str, Any]) -> Any:
    return _execute_card("D01", values)

def compute_D02(values: Mapping[str, Any]) -> Any:
    return _execute_card("D02", values)

def compute_D03(values: Mapping[str, Any]) -> Any:
    return _execute_card("D03", values)

def compute_D04(values: Mapping[str, Any]) -> Any:
    return _execute_card("D04", values)

def compute_D05(values: Mapping[str, Any]) -> Any:
    return _execute_card("D05", values)

def compute_D06(values: Mapping[str, Any]) -> Any:
    return _execute_card("D06", values)

def compute_D07(values: Mapping[str, Any]) -> Any:
    return _execute_card("D07", values)

def compute_D08(values: Mapping[str, Any]) -> Any:
    return _execute_card("D08", values)

def compute_D09(values: Mapping[str, Any]) -> Any:
    return _execute_card("D09", values)

def compute_D10(values: Mapping[str, Any]) -> Any:
    _guard_operational_envelope(values)
    return _central_capital_utilization(dict(values))["capital_utilization"]

def compute_D11(values: Mapping[str, Any]) -> Any:
    return _execute_card("D11", values)

def compute_D12(values: Mapping[str, Any]) -> Any:
    return _execute_card("D12", values)

def compute_D13(values: Mapping[str, Any]) -> Any:
    return _execute_card("D13", values)

def compute_D14(values: Mapping[str, Any]) -> Any:
    return _execute_card("D14", values)

def compute_D15(values: Mapping[str, Any]) -> Any:
    return _execute_card("D15", values)

def compute_D16(values: Mapping[str, Any]) -> Any:
    return _execute_card("D16", values)

def compute_D17(values: Mapping[str, Any]) -> Any:
    return _execute_card("D17", values)

def compute_D18(values: Mapping[str, Any]) -> Any:
    return _execute_card("D18", values)

def compute_D19(values: Mapping[str, Any]) -> Any:
    return _execute_card("D19", values)

def compute_D20(values: Mapping[str, Any]) -> Any:
    return _execute_card("D20", values)

def compute_D21(values: Mapping[str, Any]) -> Any:
    return _execute_card("D21", values)

def compute_D22(values: Mapping[str, Any]) -> Any:
    return _execute_card("D22", values)

def compute_D23(values: Mapping[str, Any]) -> Any:
    return _execute_card("D23", values)

def compute_D24(values: Mapping[str, Any]) -> Any:
    return _execute_card("D24", values)

def compute_D25(values: Mapping[str, Any]) -> Any:
    return _execute_card("D25", values)

def compute_D26(values: Mapping[str, Any]) -> Any:
    return _execute_card("D26", values)

def compute_D27(values: Mapping[str, Any]) -> Any:
    return _execute_card("D27", values)

def compute_D28(values: Mapping[str, Any]) -> Any:
    return _execute_card("D28", values)

def compute_D29(values: Mapping[str, Any]) -> Any:
    return _execute_card("D29", values)

def compute_D30(values: Mapping[str, Any]) -> Any:
    return _execute_card("D30", values)

def compute_E01(values: Mapping[str, Any]) -> Any:
    return _execute_card("E01", values)

def compute_E02(values: Mapping[str, Any]) -> Any:
    return _execute_card("E02", values)

def compute_E03(values: Mapping[str, Any]) -> Any:
    return _execute_card("E03", values)

def compute_E04(values: Mapping[str, Any]) -> Any:
    return _execute_card("E04", values)

def compute_E05(values: Mapping[str, Any]) -> Any:
    return _execute_card("E05", values)

def compute_E06(values: Mapping[str, Any]) -> Any:
    return _execute_card("E06", values)

def compute_E07(values: Mapping[str, Any]) -> Any:
    return _execute_card("E07", values)

def compute_E08(values: Mapping[str, Any]) -> Any:
    return _execute_card("E08", values)

def compute_E09(values: Mapping[str, Any]) -> Any:
    return _execute_card("E09", values)

def compute_E10(values: Mapping[str, Any]) -> Any:
    return _execute_card("E10", values)

def compute_E11(values: Mapping[str, Any]) -> Any:
    return _execute_card("E11", values)

def compute_E12(values: Mapping[str, Any]) -> Any:
    return _execute_card("E12", values)

def compute_F01(values: Mapping[str, Any]) -> Any:
    return _execute_card("F01", values)

def compute_F02(values: Mapping[str, Any]) -> Any:
    return _execute_card("F02", values)

def compute_F03(values: Mapping[str, Any]) -> Any:
    return _execute_card("F03", values)

def compute_F04(values: Mapping[str, Any]) -> Any:
    return _execute_card("F04", values)

def compute_F05(values: Mapping[str, Any]) -> Any:
    return _execute_card("F05", values)

def compute_F06(values: Mapping[str, Any]) -> Any:
    return _execute_card("F06", values)

def compute_F07(values: Mapping[str, Any]) -> Any:
    return _execute_card("F07", values)

def compute_F08(values: Mapping[str, Any]) -> Any:
    _guard_operational_envelope(values)
    return _central_one_hot_penalty(dict(values))["one_hot_penalty"]

def compute_F09(values: Mapping[str, Any]) -> Any:
    return _execute_card("F09", values)

def compute_F10(values: Mapping[str, Any]) -> Any:
    return _execute_card("F10", values)

def compute_F11(values: Mapping[str, Any]) -> Any:
    return _execute_card("F11", values)

def compute_F12(values: Mapping[str, Any]) -> Any:
    return _execute_card("F12", values)

def compute_F13(values: Mapping[str, Any]) -> Any:
    return _execute_card("F13", values)

def compute_F14(values: Mapping[str, Any]) -> Any:
    return _execute_card("F14", values)

def compute_F15(values: Mapping[str, Any]) -> Any:
    return _execute_card("F15", values)

def compute_F16(values: Mapping[str, Any]) -> Any:
    return _execute_card("F16", values)

def compute_F17(values: Mapping[str, Any]) -> Any:
    return _execute_card("F17", values)

def compute_F18(values: Mapping[str, Any]) -> Any:
    return _execute_card("F18", values)

def compute_F19(values: Mapping[str, Any]) -> Any:
    return _execute_card("F19", values)

def compute_F20(values: Mapping[str, Any]) -> Any:
    return _execute_card("F20", values)

def compute_F21(values: Mapping[str, Any]) -> Any:
    return _execute_card("F21", values)

def compute_F22(values: Mapping[str, Any]) -> Any:
    return _execute_card("F22", values)

def compute_F23(values: Mapping[str, Any]) -> Any:
    return _execute_card("F23", values)

def compute_F24(values: Mapping[str, Any]) -> Any:
    return _execute_card("F24", values)

def compute_F25(values: Mapping[str, Any]) -> Any:
    return _execute_card("F25", values)

def compute_F26(values: Mapping[str, Any]) -> Any:
    return _execute_card("F26", values)

def compute_F27(values: Mapping[str, Any]) -> Any:
    return _execute_card("F27", values)

def compute_F28(values: Mapping[str, Any]) -> Any:
    return _execute_card("F28", values)

def compute_F29(values: Mapping[str, Any]) -> Any:
    return _execute_card("F29", values)

def compute_F30(values: Mapping[str, Any]) -> Any:
    return _execute_card("F30", values)

def compute_F31(values: Mapping[str, Any]) -> Any:
    return _execute_card("F31", values)

def compute_F32(values: Mapping[str, Any]) -> Any:
    return _execute_card("F32", values)

def compute_F33(values: Mapping[str, Any]) -> Any:
    return _execute_card("F33", values)

def compute_F34(values: Mapping[str, Any]) -> Any:
    return _execute_card("F34", values)

def compute_F35(values: Mapping[str, Any]) -> Any:
    return _execute_card("F35", values)

def compute_F36(values: Mapping[str, Any]) -> Any:
    return _execute_card("F36", values)

def compute_F37(values: Mapping[str, Any]) -> Any:
    return _execute_card("F37", values)

def compute_F38(values: Mapping[str, Any]) -> Any:
    return _execute_card("F38", values)

def compute_F39(values: Mapping[str, Any]) -> Any:
    return _execute_card("F39", values)

def compute_F40(values: Mapping[str, Any]) -> Any:
    return _execute_card("F40", values)

def compute_F41(values: Mapping[str, Any]) -> Any:
    return _execute_card("F41", values)

def compute_F42(values: Mapping[str, Any]) -> Any:
    return _execute_card("F42", values)

def compute_F43(values: Mapping[str, Any]) -> Any:
    return _execute_card("F43", values)

def compute_F44(values: Mapping[str, Any]) -> Any:
    return _execute_card("F44", values)

def compute_F45(values: Mapping[str, Any]) -> Any:
    return _execute_card("F45", values)

def compute_F46(values: Mapping[str, Any]) -> Any:
    return _execute_card("F46", values)

def compute_G01(values: Mapping[str, Any]) -> Any:
    return _execute_card("G01", values)

def compute_G02(values: Mapping[str, Any]) -> Any:
    return _execute_card("G02", values)

def compute_G03(values: Mapping[str, Any]) -> Any:
    return _execute_card("G03", values)

def compute_G04(values: Mapping[str, Any]) -> Any:
    return _execute_card("G04", values)

def compute_G05(values: Mapping[str, Any]) -> Any:
    return _execute_card("G05", values)

def compute_G06(values: Mapping[str, Any]) -> Any:
    return _execute_card("G06", values)

def compute_G07(values: Mapping[str, Any]) -> Any:
    return _execute_card("G07", values)

def compute_G08(values: Mapping[str, Any]) -> Any:
    return _execute_card("G08", values)

def compute_G09(values: Mapping[str, Any]) -> Any:
    return _execute_card("G09", values)

def compute_G10(values: Mapping[str, Any]) -> Any:
    return _execute_card("G10", values)

def compute_G11(values: Mapping[str, Any]) -> Any:
    return _execute_card("G11", values)

def compute_G12(values: Mapping[str, Any]) -> Any:
    return _execute_card("G12", values)

def compute_G13(values: Mapping[str, Any]) -> Any:
    return _execute_card("G13", values)

def compute_G14(values: Mapping[str, Any]) -> Any:
    return _execute_card("G14", values)

def compute_H01(values: Mapping[str, Any]) -> Any:
    return _execute_card("H01", values)

def compute_H02(values: Mapping[str, Any]) -> Any:
    return _execute_card("H02", values)

def compute_H03(values: Mapping[str, Any]) -> Any:
    return _execute_card("H03", values)

def compute_H04(values: Mapping[str, Any]) -> Any:
    return _execute_card("H04", values)

def compute_H05(values: Mapping[str, Any]) -> Any:
    return _execute_card("H05", values)

def compute_H06(values: Mapping[str, Any]) -> Any:
    return _execute_card("H06", values)

def compute_H07(values: Mapping[str, Any]) -> Any:
    return _execute_card("H07", values)

def compute_H08(values: Mapping[str, Any]) -> Any:
    return _execute_card("H08", values)

def compute_H09(values: Mapping[str, Any]) -> Any:
    return _execute_card("H09", values)

def compute_H10(values: Mapping[str, Any]) -> Any:
    return _execute_card("H10", values)

def compute_H11(values: Mapping[str, Any]) -> Any:
    return _execute_card("H11", values)

def compute_H12(values: Mapping[str, Any]) -> Any:
    return _execute_card("H12", values)

def compute_H13(values: Mapping[str, Any]) -> Any:
    return _execute_card("H13", values)

def compute_H14(values: Mapping[str, Any]) -> Any:
    return _execute_card("H14", values)

def compute_I01(values: Mapping[str, Any]) -> Any:
    return _execute_card("I01", values)

def compute_I02(values: Mapping[str, Any]) -> Any:
    return _execute_card("I02", values)

def compute_I03(values: Mapping[str, Any]) -> Any:
    return _execute_card("I03", values)

def compute_I04(values: Mapping[str, Any]) -> Any:
    return _execute_card("I04", values)

def compute_I05(values: Mapping[str, Any]) -> Any:
    return _execute_card("I05", values)

def compute_I06(values: Mapping[str, Any]) -> Any:
    return _execute_card("I06", values)

def compute_I07(values: Mapping[str, Any]) -> Any:
    return _execute_card("I07", values)

def compute_I08(values: Mapping[str, Any]) -> Any:
    return _execute_card("I08", values)

def compute_I09(values: Mapping[str, Any]) -> Any:
    return _execute_card("I09", values)

def compute_I10(values: Mapping[str, Any]) -> Any:
    return _execute_card("I10", values)

def compute_J01(values: Mapping[str, Any]) -> Any:
    _guard_operational_envelope(values)
    return FAMILY_J_CALLABLES["J01"](values)

def compute_J02(values: Mapping[str, Any]) -> Any:
    _guard_operational_envelope(values)
    return FAMILY_J_CALLABLES["J02"](values)

def compute_J03(values: Mapping[str, Any]) -> Any:
    _guard_operational_envelope(values)
    return FAMILY_J_CALLABLES["J03"](values)

def compute_J04(values: Mapping[str, Any]) -> Any:
    _guard_operational_envelope(values)
    return FAMILY_J_CALLABLES["J04"](values)

def compute_J05(values: Mapping[str, Any]) -> Any:
    _guard_operational_envelope(values)
    return FAMILY_J_CALLABLES["J05"](values)

def compute_J06(values: Mapping[str, Any]) -> Any:
    _guard_operational_envelope(values)
    return FAMILY_J_CALLABLES["J06"](values)

def compute_J07(values: Mapping[str, Any]) -> Any:
    _guard_operational_envelope(values)
    return FAMILY_J_CALLABLES["J07"](values)

def compute_J08(values: Mapping[str, Any]) -> Any:
    _guard_operational_envelope(values)
    return FAMILY_J_CALLABLES["J08"](values)


METHOD_CALLABLES = {
    "A01": compute_A01,
    "A02": compute_A02,
    "A03": compute_A03,
    "A04": compute_A04,
    "A05": compute_A05,
    "A06": compute_A06,
    "A07": compute_A07,
    "A08": compute_A08,
    "A09": compute_A09,
    "A10": compute_A10,
    "A11": compute_A11,
    "A12": compute_A12,
    "A13": compute_A13,
    "A14": compute_A14,
    "A15": compute_A15,
    "A16": compute_A16,
    "A17": compute_A17,
    "A18": compute_A18,
    "A19": compute_A19,
    "A20": compute_A20,
    "A21": compute_A21,
    "A22": compute_A22,
    "A23": compute_A23,
    "A24": compute_A24,
    "A25": compute_A25,
    "A26": compute_A26,
    "A27": compute_A27,
    "A28": compute_A28,
    "A29": compute_A29,
    "A30": compute_A30,
    "A31": compute_A31,
    "A32": compute_A32,
    "A33": compute_A33,
    "B01": compute_B01,
    "B02": compute_B02,
    "B03": compute_B03,
    "B04": compute_B04,
    "B05": compute_B05,
    "B06": compute_B06,
    "B07": compute_B07,
    "B08": compute_B08,
    "B09": compute_B09,
    "B10": compute_B10,
    "B11": compute_B11,
    "B12": compute_B12,
    "B13": compute_B13,
    "B14": compute_B14,
    "B15": compute_B15,
    "B16": compute_B16,
    "B17": compute_B17,
    "B18": compute_B18,
    "B19": compute_B19,
    "B20": compute_B20,
    "B21": compute_B21,
    "C01": compute_C01,
    "C02": compute_C02,
    "C03": compute_C03,
    "C04": compute_C04,
    "C05": compute_C05,
    "C06": compute_C06,
    "C07": compute_C07,
    "C08": compute_C08,
    "C09": compute_C09,
    "C10": compute_C10,
    "C11": compute_C11,
    "C12": compute_C12,
    "C13": compute_C13,
    "C14": compute_C14,
    "C15": compute_C15,
    "C16": compute_C16,
    "C17": compute_C17,
    "C18": compute_C18,
    "C19": compute_C19,
    "C20": compute_C20,
    "C21": compute_C21,
    "C22": compute_C22,
    "C23": compute_C23,
    "C24": compute_C24,
    "C25": compute_C25,
    "D01": compute_D01,
    "D02": compute_D02,
    "D03": compute_D03,
    "D04": compute_D04,
    "D05": compute_D05,
    "D06": compute_D06,
    "D07": compute_D07,
    "D08": compute_D08,
    "D09": compute_D09,
    "D10": compute_D10,
    "D11": compute_D11,
    "D12": compute_D12,
    "D13": compute_D13,
    "D14": compute_D14,
    "D15": compute_D15,
    "D16": compute_D16,
    "D17": compute_D17,
    "D18": compute_D18,
    "D19": compute_D19,
    "D20": compute_D20,
    "D21": compute_D21,
    "D22": compute_D22,
    "D23": compute_D23,
    "D24": compute_D24,
    "D25": compute_D25,
    "D26": compute_D26,
    "D27": compute_D27,
    "D28": compute_D28,
    "D29": compute_D29,
    "D30": compute_D30,
    "E01": compute_E01,
    "E02": compute_E02,
    "E03": compute_E03,
    "E04": compute_E04,
    "E05": compute_E05,
    "E06": compute_E06,
    "E07": compute_E07,
    "E08": compute_E08,
    "E09": compute_E09,
    "E10": compute_E10,
    "E11": compute_E11,
    "E12": compute_E12,
    "F01": compute_F01,
    "F02": compute_F02,
    "F03": compute_F03,
    "F04": compute_F04,
    "F05": compute_F05,
    "F06": compute_F06,
    "F07": compute_F07,
    "F08": compute_F08,
    "F09": compute_F09,
    "F10": compute_F10,
    "F11": compute_F11,
    "F12": compute_F12,
    "F13": compute_F13,
    "F14": compute_F14,
    "F15": compute_F15,
    "F16": compute_F16,
    "F17": compute_F17,
    "F18": compute_F18,
    "F19": compute_F19,
    "F20": compute_F20,
    "F21": compute_F21,
    "F22": compute_F22,
    "F23": compute_F23,
    "F24": compute_F24,
    "F25": compute_F25,
    "F26": compute_F26,
    "F27": compute_F27,
    "F28": compute_F28,
    "F29": compute_F29,
    "F30": compute_F30,
    "F31": compute_F31,
    "F32": compute_F32,
    "F33": compute_F33,
    "F34": compute_F34,
    "F35": compute_F35,
    "F36": compute_F36,
    "F37": compute_F37,
    "F38": compute_F38,
    "F39": compute_F39,
    "F40": compute_F40,
    "F41": compute_F41,
    "F42": compute_F42,
    "F43": compute_F43,
    "F44": compute_F44,
    "F45": compute_F45,
    "F46": compute_F46,
    "G01": compute_G01,
    "G02": compute_G02,
    "G03": compute_G03,
    "G04": compute_G04,
    "G05": compute_G05,
    "G06": compute_G06,
    "G07": compute_G07,
    "G08": compute_G08,
    "G09": compute_G09,
    "G10": compute_G10,
    "G11": compute_G11,
    "G12": compute_G12,
    "G13": compute_G13,
    "G14": compute_G14,
    "H01": compute_H01,
    "H02": compute_H02,
    "H03": compute_H03,
    "H04": compute_H04,
    "H05": compute_H05,
    "H06": compute_H06,
    "H07": compute_H07,
    "H08": compute_H08,
    "H09": compute_H09,
    "H10": compute_H10,
    "H11": compute_H11,
    "H12": compute_H12,
    "H13": compute_H13,
    "H14": compute_H14,
    "I01": compute_I01,
    "I02": compute_I02,
    "I03": compute_I03,
    "I04": compute_I04,
    "I05": compute_I05,
    "I06": compute_I06,
    "I07": compute_I07,
    "I08": compute_I08,
    "I09": compute_I09,
    "I10": compute_I10,
    "J01": compute_J01,
    "J02": compute_J02,
    "J03": compute_J03,
    "J04": compute_J04,
    "J05": compute_J05,
    "J06": compute_J06,
    "J07": compute_J07,
    "J08": compute_J08,
}

if len(METHOD_CALLABLES) != 213:
    raise RuntimeError("static operator registry must contain 213 entries")

def callable_ref(card_id: str) -> str:
    if card_id not in METHOD_CALLABLES:
        raise KeyError(card_id)
    return ("src.qtt.stage1_prediction_markets.pr169_qku_formula_exp1.methods:"
            f"compute_{card_id}")

__all__ = ["METHOD_CALLABLES", "callable_ref",
    "compute_A01",
    "compute_A02",
    "compute_A03",
    "compute_A04",
    "compute_A05",
    "compute_A06",
    "compute_A07",
    "compute_A08",
    "compute_A09",
    "compute_A10",
    "compute_A11",
    "compute_A12",
    "compute_A13",
    "compute_A14",
    "compute_A15",
    "compute_A16",
    "compute_A17",
    "compute_A18",
    "compute_A19",
    "compute_A20",
    "compute_A21",
    "compute_A22",
    "compute_A23",
    "compute_A24",
    "compute_A25",
    "compute_A26",
    "compute_A27",
    "compute_A28",
    "compute_A29",
    "compute_A30",
    "compute_A31",
    "compute_A32",
    "compute_A33",
    "compute_B01",
    "compute_B02",
    "compute_B03",
    "compute_B04",
    "compute_B05",
    "compute_B06",
    "compute_B07",
    "compute_B08",
    "compute_B09",
    "compute_B10",
    "compute_B11",
    "compute_B12",
    "compute_B13",
    "compute_B14",
    "compute_B15",
    "compute_B16",
    "compute_B17",
    "compute_B18",
    "compute_B19",
    "compute_B20",
    "compute_B21",
    "compute_C01",
    "compute_C02",
    "compute_C03",
    "compute_C04",
    "compute_C05",
    "compute_C06",
    "compute_C07",
    "compute_C08",
    "compute_C09",
    "compute_C10",
    "compute_C11",
    "compute_C12",
    "compute_C13",
    "compute_C14",
    "compute_C15",
    "compute_C16",
    "compute_C17",
    "compute_C18",
    "compute_C19",
    "compute_C20",
    "compute_C21",
    "compute_C22",
    "compute_C23",
    "compute_C24",
    "compute_C25",
    "compute_D01",
    "compute_D02",
    "compute_D03",
    "compute_D04",
    "compute_D05",
    "compute_D06",
    "compute_D07",
    "compute_D08",
    "compute_D09",
    "compute_D10",
    "compute_D11",
    "compute_D12",
    "compute_D13",
    "compute_D14",
    "compute_D15",
    "compute_D16",
    "compute_D17",
    "compute_D18",
    "compute_D19",
    "compute_D20",
    "compute_D21",
    "compute_D22",
    "compute_D23",
    "compute_D24",
    "compute_D25",
    "compute_D26",
    "compute_D27",
    "compute_D28",
    "compute_D29",
    "compute_D30",
    "compute_E01",
    "compute_E02",
    "compute_E03",
    "compute_E04",
    "compute_E05",
    "compute_E06",
    "compute_E07",
    "compute_E08",
    "compute_E09",
    "compute_E10",
    "compute_E11",
    "compute_E12",
    "compute_F01",
    "compute_F02",
    "compute_F03",
    "compute_F04",
    "compute_F05",
    "compute_F06",
    "compute_F07",
    "compute_F08",
    "compute_F09",
    "compute_F10",
    "compute_F11",
    "compute_F12",
    "compute_F13",
    "compute_F14",
    "compute_F15",
    "compute_F16",
    "compute_F17",
    "compute_F18",
    "compute_F19",
    "compute_F20",
    "compute_F21",
    "compute_F22",
    "compute_F23",
    "compute_F24",
    "compute_F25",
    "compute_F26",
    "compute_F27",
    "compute_F28",
    "compute_F29",
    "compute_F30",
    "compute_F31",
    "compute_F32",
    "compute_F33",
    "compute_F34",
    "compute_F35",
    "compute_F36",
    "compute_F37",
    "compute_F38",
    "compute_F39",
    "compute_F40",
    "compute_F41",
    "compute_F42",
    "compute_F43",
    "compute_F44",
    "compute_F45",
    "compute_F46",
    "compute_G01",
    "compute_G02",
    "compute_G03",
    "compute_G04",
    "compute_G05",
    "compute_G06",
    "compute_G07",
    "compute_G08",
    "compute_G09",
    "compute_G10",
    "compute_G11",
    "compute_G12",
    "compute_G13",
    "compute_G14",
    "compute_H01",
    "compute_H02",
    "compute_H03",
    "compute_H04",
    "compute_H05",
    "compute_H06",
    "compute_H07",
    "compute_H08",
    "compute_H09",
    "compute_H10",
    "compute_H11",
    "compute_H12",
    "compute_H13",
    "compute_H14",
    "compute_I01",
    "compute_I02",
    "compute_I03",
    "compute_I04",
    "compute_I05",
    "compute_I06",
    "compute_I07",
    "compute_I08",
    "compute_I09",
    "compute_I10",
    "compute_J01",
    "compute_J02",
    "compute_J03",
    "compute_J04",
    "compute_J05",
    "compute_J06",
    "compute_J07",
    "compute_J08",
]
