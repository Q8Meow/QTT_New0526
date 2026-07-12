from __future__ import annotations

from typing import Any

from .policy import STRATEGY_TEMPLATES
from .catalog import CARD_NAMES


STRATEGY_IDS = (
    *(f"SH{i:02d}" for i in range(1, 9)),
    *(f"PM{i:02d}" for i in range(1, 8)),
    *(f"PF{i:02d}" for i in range(1, 7)),
    *(f"LM{i:02d}" for i in range(1, 7)),
    *(f"QPM{i:02d}" for i in range(1, 12)),
)

_SETS = (
"A03 A05 A06 A07 A08 A09 A10 A11 A12 A13 A21 A22 A23 A24 A25 A27 A28 A29 B01 B02 B03 B04 B05 B06 B07 B08 B09 B15 B16 C08 C21 D11 D12",
"A03 A05 A06 A07 A08 A30 A31 A32 A33 B01 B02 B06 B09 B10 B11 B12 B13 B14 B15 B16 B17 B18 B19 D11 D27",
"A03 A05 A25 B01 B02 B08 B09 B10 B11 B12 B13 B14 B15 B16 C08 D27",
"A03 A05 A08 A09 A10 A11 A12 A25 A30 A31 A32 B01 B02 B09 B15",
"A03 A05 A08 A09 A10 A11 A12 A13 A21 A22 A25 B01 B02 B09 B10 D11",
"A03 A05 A25 B07 B08 B09 B10 B11 B12 B13 B14 C08 C09 C21 D27 J03",
"A03 A05 A25 B08 B09 B13 B14 B15 C08 C09 D27 J03",
"A03 A05 A25 B06 B11 B12 B15 B17 B18 B19 C08 D27 J03",
"A25 A30 A31 A32 A33 B01 B02 E01 E10 E11 E12 J02",
"A25 A30 A31 A32 A33 B01 B02 E02 E03 E10 E11 E12 J02",
"A25 B01 B02 E05 E10 E11 E12 J02",
"A25 B01 B02 E07 E10 E11 E12 H02 J02",
"A25 B01 B02 E08 E10 E11 E12 J02",
"A25 A30 A31 A32 A33 B01 B02 B08 B09 B10 E09 E10 E11 J02",
"A25 B01 B02 E04 E10 E11 E12 J02",
"A06 A07 A23 A25 D11 D12 D14 J01",
"A25 D04 D05 D06 D07 D11 D13 D29 J01 J02",
"A25 A33 B09 B10 B15 B17 B18 B19 D04 D05 D11",
"A07 A23 A25 D05 D06 D11 D14 J01 J04",
"A25 D05 D06 D07 D11 E09 J01 J04",
"A03 A05 A25 A27 A28 B07 B09 D10 D11 J02",
"A25 C19 C20 C24 D20 D27 D29 I05 I06 J03",
"A25 B15 B16 D21 D22 D23 D24 D25 D30 I05 I06 J03",
"A25 D19 D27 G06 I05 I06 J03",
"A29 C08 C09 C21 C22 C23 C24 J02 J03",
"A25 C19 C20 D28 D29 F24 F25 F26 F27 F28 J03",
"A22 A25 B15 B16 D11 D12 D26 D30 J01 J02",
"A25 E01 E02 E03 E04 E05 E06 E07 E08 E09 E10 E11 E12 F01 F02 F03 F04 F05 F06 F07 F08 F09 F10 F11 F12 F13 F14 F29 F30 F31 F32 F33 F34 F35 J01 J02 J06 J07 J08",
"A03 A05 A06 A07 A08 A09 A10 A11 A12 A13 A14 A15 A16 A17 A18 A19 A20 A21 A22 A23 A24 A25 A26 A27 A28 A29 B01 B02 B03 B04 B05 B06 B07 B08 B09 B10 B11 B12 B13 B14 B15 B16 B17 B18 B19 B20 B21 D11 D12 D13 D14 D15 D16 D17 D18 F01 F02 F03 F04 F05 F06 F07 F08 F09 F10 F11 F12 F13 F14 F29 F30 F31 F32 F33 F34 F35 J01 J02 J06 J07 J08",
"A25 A30 A31 A32 A33 B09 B10 B11 B12 B13 B14 B15 B16 B17 B18 B19 B20 B21 D04 D05 D11 F01 F02 F03 F04 F05 F06 F07 F08 F09 F10 F11 F12 F13 F14 J02 J06 J07 J08",
"A06 A07 A25 D03 D04 D05 D06 D07 D08 D09 D10 D11 D12 D13 D14 D15 D16 D17 D18 F01 F02 F03 F04 F05 F06 F07 F08 F09 F10 F11 F12 F13 F14 F29 F30 F31 F32 F33 F34 F35 J01 J02 J04 J06 J07 J08",
"A25 C24 D21 D22 D30 F33 F34 F35 G14 J03 J04 J06",
"A25 D26 D30 F01 F02 F03 F04 F05 F06 F07 F08 F09 F10 F11 F12 F13 F14 J01 J02 J06 J07 J08",
"F01 F02 F03 F04 F05 F06 F07 F08 F09 F10 F11 F12 F13 F14 F29 F30 F31 F32 F33 F34 F35 H08 H09 J06 J07 J08",
"D30 F01 F02 F03 F04 F05 F06 F07 F08 F09 F10 F11 F12 F13 F14 F29 F30 F31 F32 F33 F34 F35 H11 J06 J07 J08",
"F07 F08 F09 F10 F11 F12 F13 F14 F39 F40 F41 F42 F43 F44 F45 F46 G10 G11 G12 G13 H08 H09 J06 J07 J08",
"F03 F04 F05 F06 F07 F29 F30 F31 F32 F33 F34 F35 F39 F40 F41 F42 F43 F44 F45 F46 G10 G13 H08 H09 H10 H11 J01 J06 J07 J08",
"F33 F34 F35 F46 G09 G10 G11 G12 G13 H10 H11 H12 H13 I07 I08 I09 J03 J06",
)

# The 38 mappings resolve repository-owned RP5C identities individually.  They
# are deliberately not inferred from a formula family and the unique identity
# count is derived by the builder/validator.
_STRATEGY_QKUS = (
    "QKU_PMKT_EDGE_EXPECTED_VALUE_AND_PAYOFF_019",
    "QKU_PMKT_EDGE_FILL_LATENCY_CAPACITY_007",
    "QKU_PMKT_EDGE_FILL_LATENCY_CAPACITY_012",
    "QKU_PMKT_EDGE_FILL_LATENCY_CAPACITY_018",
    "QKU_PMKT_EDGE_FILL_LATENCY_CAPACITY_023",
    "QKU_PMKT_EDGE_FILL_LATENCY_CAPACITY_024",
    "QKU_PMKT_EDGE_FILL_LATENCY_CAPACITY_029",
    "QKU_PMKT_EDGE_ORDERBOOK_MICROSTRUCTURE_003",
    "QKU_PMKT_EDGE_MARKET_IMPLIED_PROBABILITY_AND_PARITY_001",
    "QKU_PMKT_EDGE_MARKET_IMPLIED_PROBABILITY_AND_PARITY_002",
    "QKU_PMKT_EDGE_MARKET_IMPLIED_PROBABILITY_AND_PARITY_014",
    "QKU_PMKT_EDGE_MARKET_IMPLIED_PROBABILITY_AND_PARITY_021",
    "QKU_PMKT_EDGE_MARKET_IMPLIED_PROBABILITY_AND_PARITY_022",
    "QKU_PMKT_EDGE_VENUE_MECHANICS_CONSTRAINTS_010",
    "QKU_PMKT_EDGE_VENUE_MECHANICS_CONSTRAINTS_017",
    "QKU_PMKT_EDGE_PORTFOLIO_AND_MARGINAL_UTILITY_036",
    "QKU_PMKT_EDGE_PORTFOLIO_AND_MARGINAL_UTILITY_037",
    "QKU_PMKT_EDGE_PORTFOLIO_AND_MARGINAL_UTILITY_038",
    "QKU_PMKT_EDGE_PORTFOLIO_AND_MARGINAL_UTILITY_039",
    "QKU_PMKT_EDGE_FDR_AND_OVERFIT_CONTROLS_033",
    "QKU_PMKT_EDGE_FDR_AND_OVERFIT_CONTROLS_034",
    "QKU_PMKT_EDGE_REGIME_AND_SCENARIO_LADDER_006",
    "QKU_PMKT_EDGE_REGIME_AND_SCENARIO_LADDER_008",
    "QKU_PMKT_EDGE_REGIME_AND_SCENARIO_LADDER_040",
    "QKU_PMKT_EDGE_TRADE_PRICE_HISTORY_FEATURES_004",
    "QKU_PMKT_EDGE_TRADE_PRICE_HISTORY_FEATURES_005",
    "QKU_PMKT_EDGE_TRADE_PRICE_HISTORY_FEATURES_013",
    "QKU_PMKT_EDGE_QUANTUM_FORWARD_OPTIMIZATION_041",
    "QKU_PMKT_EDGE_QUANTUM_FORWARD_OPTIMIZATION_042",
    "QKU_PMKT_EDGE_QUANTUM_FORWARD_OPTIMIZATION_043",
    "QKU_PMKT_EDGE_QUANTUM_FORWARD_OPTIMIZATION_044",
    "QKU_PMKT_EDGE_CALIBRATION_AND_SCORING_030",
    "QKU_PMKT_EDGE_CALIBRATION_AND_SCORING_031",
    "QKU_PMKT_EDGE_CALIBRATION_AND_SCORING_032",
    "QKU_PMKT_EDGE_SOURCE_EVIDENCE_AND_DATA_QUALITY_045",
    "QKU_PMKT_EDGE_SOURCE_EVIDENCE_AND_DATA_QUALITY_046",
    "QKU_PMKT_EDGE_SOURCE_EVIDENCE_AND_DATA_QUALITY_047",
    "QKU_PMKT_EDGE_FDR_AND_OVERFIT_CONTROLS_035",
)

_SEMANTIC_KEY = dict(CARD_NAMES)

# Card-level data dependencies.  A strategy includes an edge only when both
# nodes are present; otherwise the input is resolved from the typed PRETRADE
# snapshot.  This is deliberately not an adjacency chain.
_CARD_DEPENDENCIES: dict[str, tuple[str, ...]] = {
    "A05": ("A03",), "A06": ("A05",), "A07": ("A05",),
    "A08": ("A23", "A24"), "A11": ("A09", "A10"),
    "A12": ("A03", "A11", "B09"), "A13": ("A11",),
    "A21": ("A15", "A16"), "A22": ("A05", "A25"),
    "A25": ("A03", "A05"), "A27": ("A05", "B07", "B09"),
    "A28": ("A27",), "A29": ("C08", "C09", "C21"),
    "A33": ("A03", "B09", "B14"),
    "B02": ("B01",), "B08": ("B03",), "B10": ("B09",),
    "B15": ("A33", "B09", "B10"), "B16": ("B10", "B15"),
    "B19": ("B17",),
    "C09": ("C08",), "C19": ("A25",), "C20": ("C19",),
    "C21": ("A03",), "C24": ("C19",),
    "D11": ("A25",), "D12": ("A23", "D11"),
    "D14": ("A07",), "D20": ("C19",), "D26": ("A25", "D11"),
    "D27": ("A25",), "D29": ("D11",), "D30": ("D21",),
    "E10": ("B09", "B10"), "E11": ("E10",), "E12": ("E01", "E02", "E05", "E07", "E08", "E11"),
    "F02": ("F01",), "F03": ("F01",), "F04": ("F03",),
    "F05": ("F03",), "F06": ("F03",), "F07": ("F03",),
    "F08": ("F07",), "F09": ("F07",), "F10": ("F03",),
    "F11": ("F03",), "F12": ("F03",), "F13": ("F03",), "F14": ("F03",),
    "F29": ("F03",), "F30": ("F18", "F19", "F29"),
    "F31": ("F32",), "F32": ("F25", "F29"),
    "F33": ("F32",), "F34": ("F32",), "F35": ("F32", "F46"),
    "G10": ("G09",), "G13": ("F46",), "G14": ("D29",),
    "H02": ("H01",), "H09": ("H08",), "H10": ("F25",),
    "H11": ("F46",), "H13": ("F46", "I07", "I08", "I09"),
    "I06": ("I05",), "I09": ("I07", "I08"),
    "J01": ("D16",), "J02": ("B09",), "J03": ("D27",),
    "J04": ("D29",), "J06": ("F03",), "J07": ("F03", "F06", "F07", "J06"),
    "J08": ("F03", "J06"),
}


def strategy_rows() -> list[dict[str, Any]]:
    rows=[]
    for strategy_id,name,encoded,qku_id in zip(STRATEGY_IDS,STRATEGY_TEMPLATES,_SETS,_STRATEGY_QKUS,strict=True):
        cards=encoded.split()
        card_set=set(cards)
        edges=sorted([
            [dependency,card]
            for card in cards
            for dependency in _CARD_DEPENDENCIES.get(card,())
            if dependency in card_set
        ])
        prefix="QPM" if strategy_id.startswith("QPM") else strategy_id[:2]
        rows.append({
            "strategy_template_id":strategy_id,"exact_source_name":name,"canonical_QKU_or_current_equivalent_ref":qku_id,
            "formula_DAG_refs":cards,"dependency_edges":edges,
            "input_maps":{
                card:({
                    f"upstream_{dependency.lower()}":f"node::{strategy_id}::{dependency}::{_SEMANTIC_KEY[dependency].lower()}"
                    for dependency in _CARD_DEPENDENCIES.get(card,()) if dependency in card_set
                } or {"typed_provider_input":f"PRETRADE_SNAPSHOT::{strategy_id}::{card}::{_SEMANTIC_KEY[card].lower()}"})
                for card in cards
            },
            "output_maps":{card:f"node::{strategy_id}::{card}::{_SEMANTIC_KEY[card].lower()}" for card in cards},
            "applicability_predicate":f"context.strategy_template_id == '{strategy_id}'",
            "state_barriers":["INPUT_LOCK","SEED_IF_STOCHASTIC","NO_TRADE_GATE"],
            "fallback_path":"DETERMINISTIC_NO_TRADE_THEN_BOUNDED_RECOVERY",
            "no_trade_comparator_ref":"A25",
            "required_PRETRADE_model_refs":["VenueRealityModelV1","CashflowModelV1","ModeAuthorityMatrixV1"],
            "approved_mutable_variable_schema":["market","venue","stack","side","entry","size","holding_duration","exit_rule","maker_taker_split","cancel_replace_interval","liquidity_spread_filters","latency_budget","portfolio_exposure"],
            "PR165_D2_responsible_agent_route":"quantum_optimizer_agent" if prefix=="QPM" else "risk_manager_agent",
            "AGENT_ORCH_task_template_ref":"AGENT_ORCH_GENERIC_FORMULA_QKU_TASK",
            "PAPER_handoff_ref":"PAPER_PREPARATION_CANDIDATE_ONLY",
            "QMAP_QBENCH_handoff_ref_if_applicable":"QMAP_QBENCH_CANDIDATE" if prefix=="QPM" else None,
            "HOTPATH_compilation_candidate_ref_if_applicable":"HOTPATH_CANDIDATE_NO_AUTHORITY" if prefix=="SH" else None,
            "terminal_or_downstream_disposition":"VALIDATED_ROUTED_UNACKNOWLEDGED_NO_ORDER_AUTHORITY",
        })
    return rows


if len(STRATEGY_IDS)!=38 or len(_SETS)!=38 or len(_STRATEGY_QKUS)!=38:
    raise RuntimeError("strategy closure must contain 38 table-driven DAGs")
