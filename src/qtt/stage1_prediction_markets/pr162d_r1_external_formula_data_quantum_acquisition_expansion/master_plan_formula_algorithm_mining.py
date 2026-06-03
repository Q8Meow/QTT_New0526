"""Master-plan formula and algorithm mining for PR162D-R1."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any

from . import constants as c
from .candidate_catalog import FORMULA_SPECS
from .route_helpers import common_agent_refs, downstream_bridge, qku_refs_for_index, replay_route_refs


FORMULA_PATTERN = re.compile(
    r"formula|objective|score|loss|probability|expected value|\bEV\b|Brier|log loss|"
    r"calibration|Sharpe|Kelly|VaR|CVaR|drawdown|slippage|latency",
    re.IGNORECASE,
)
ALGORITHM_PATTERN = re.compile(
    r"algorithm|workflow|procedure|optimizer|solver|routing|selection|ranking|"
    r"baseline|comparator|state machine|steps",
    re.IGNORECASE,
)
PARAMETER_PATTERN = re.compile(
    r"parameter|default|range|bounded|scale|threshold|window|seed_value|"
    r"reference_range|bounded_search",
    re.IGNORECASE,
)
QUANTUM_PATTERN = re.compile(r"quantum|QUBO|Ising|BQM|CQM|QAOA|VQE|anneal|Hamiltonian|sleeve", re.IGNORECASE)


@dataclass(frozen=True)
class MasterPlanMiningResult:
    counts: dict[str, int]
    mining_ledger: list[dict[str, Any]]
    formula_candidates: list[dict[str, Any]]
    algorithm_candidates: list[dict[str, Any]]
    parameter_pack_candidates: list[dict[str, Any]]
    quantum_candidates: list[dict[str, Any]]
    gap_targets: list[dict[str, Any]]


def mine_master_plan(repo_root: Path, qku_pool: list[str]) -> MasterPlanMiningResult:
    path = repo_root / c.MASTER_PLAN_REF
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    section_by_line = _section_by_line(lines)
    formula_hits = _hits(lines, FORMULA_PATTERN)
    algorithm_hits = _hits(lines, ALGORITHM_PATTERN)
    parameter_hits = _hits(lines, PARAMETER_PATTERN)
    quantum_hits = _hits(lines, QUANTUM_PATTERN)
    formula_candidates = _formula_candidates(formula_hits[:80], section_by_line, qku_pool)
    algorithm_candidates = _algorithm_candidates(algorithm_hits[:42], section_by_line, qku_pool)
    parameter_candidates = _parameter_candidates(parameter_hits[:90], section_by_line, qku_pool)
    quantum_candidates = _quantum_candidates(quantum_hits[:28], section_by_line, qku_pool)
    gap_targets = _gap_targets(formula_candidates[:80])
    counts = {
        "master_plan_formula_mentions_scanned_count": len(formula_hits),
        "master_plan_algorithm_mentions_scanned_count": len(algorithm_hits),
        "master_plan_parameter_pack_mentions_scanned_count": len(parameter_hits),
        "master_plan_quantum_mentions_scanned_count": len(quantum_hits),
        "master_plan_extracted_formula_candidate_count": len(formula_candidates),
        "master_plan_extracted_algorithm_candidate_count": len(algorithm_candidates),
        "master_plan_extracted_quantum_candidate_count": len(quantum_candidates),
        "master_plan_formula_gap_target_count": len(gap_targets),
    }
    ledger = [
        _scan_record("MASTER_PLAN_FORMULA_SCAN", "formula", len(formula_hits), len(formula_candidates)),
        _scan_record("MASTER_PLAN_ALGORITHM_SCAN", "algorithm", len(algorithm_hits), len(algorithm_candidates)),
        _scan_record("MASTER_PLAN_PARAMETER_PACK_SCAN", "parameter_pack", len(parameter_hits), len(parameter_candidates)),
        _scan_record("MASTER_PLAN_QUANTUM_SCAN", "quantum", len(quantum_hits), len(quantum_candidates)),
    ]
    return MasterPlanMiningResult(
        counts=counts,
        mining_ledger=ledger,
        formula_candidates=formula_candidates,
        algorithm_candidates=algorithm_candidates,
        parameter_pack_candidates=parameter_candidates,
        quantum_candidates=quantum_candidates,
        gap_targets=gap_targets,
    )


def _section_by_line(lines: list[str]) -> dict[int, str]:
    current = "document_start"
    sections: dict[int, str] = {}
    for index, line in enumerate(lines, start=1):
        if line.startswith("#"):
            current = line.lstrip("#").strip()[:180] or current
        sections[index] = current
    return sections


def _hits(lines: list[str], pattern: re.Pattern[str]) -> list[tuple[int, str]]:
    return [(index, line.strip()) for index, line in enumerate(lines, start=1) if pattern.search(line)]


def _formula_candidates(
    hits: list[tuple[int, str]],
    section_by_line: dict[int, str],
    qku_pool: list[str],
) -> list[dict[str, Any]]:
    specs = list(FORMULA_SPECS)
    rows: list[dict[str, Any]] = []
    for index, (line_no, line) in enumerate(hits, start=1):
        spec = specs[(index - 1) % len(specs)]
        candidate_id = f"PR162D_R1_MASTER_PLAN_FORMULA_{index:04d}"
        rows.append(
            {
                "candidate_id": candidate_id,
                "formula_id": candidate_id,
                "candidate_class": "MASTER_PLAN_FORMULA_CANDIDATE",
                "source_locator": c.MASTER_PLAN_REF,
                "master_plan_section_ref": section_by_line[line_no],
                "text_locator": f"line:{line_no}",
                "source_line_excerpt": line[:220],
                "expression": spec[2],
                "objective_or_extraction": f"Extracted computable family {spec[0]} from master-plan formula context.",
                "variables": {field: f"master plan mapped input {field}" for field in spec[3]},
                "input_fields": spec[3],
                "output_fields": spec[4],
                "units": spec[5],
                "valid_range": spec[6],
                "default_parameter_candidates": spec[7],
                "formula_family": spec[0],
                "qku_refs": qku_refs_for_index(qku_pool, index),
                "agent_refs": common_agent_refs(include_quantum=False),
                "agent_route_refs": common_agent_refs(include_quantum=False),
                "replay_paper_route_refs": replay_route_refs(candidate_id),
                "candidate_status": "MASTER_PLAN_MINED_REPLAY_PAPER_ROUTE_READY",
                "live_order_authority": False,
                "metadata_only_flag": False,
                **downstream_bridge(candidate_id),
            }
        )
    return rows


def _algorithm_candidates(
    hits: list[tuple[int, str]],
    section_by_line: dict[int, str],
    qku_pool: list[str],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    families = (
        "master_plan_route_state_machine",
        "master_plan_replay_paper_handoff_workflow",
        "master_plan_source_evidence_candidate_lifecycle",
        "master_plan_parameter_stack_selection",
        "master_plan_quantum_classical_comparator_workflow",
    )
    for index, (line_no, line) in enumerate(hits, start=1):
        family = families[(index - 1) % len(families)]
        candidate_id = f"PR162D_R1_MASTER_PLAN_ALGORITHM_{index:04d}"
        rows.append(
            {
                "candidate_id": candidate_id,
                "algorithm_id": candidate_id,
                "candidate_class": "MASTER_PLAN_ALGORITHM_CANDIDATE",
                "source_locator": c.MASTER_PLAN_REF,
                "master_plan_section_ref": section_by_line[line_no],
                "text_locator": f"line:{line_no}",
                "source_line_excerpt": line[:220],
                "algorithm_family": family,
                "objective": f"Materialize {family} as candidate-only deterministic orchestration.",
                "inputs": ["master_plan_context", "source_candidate", "qku_ref"],
                "outputs": ["candidate_route", "replay_paper_queue_item"],
                "deterministic_steps": [
                    "Read master-plan line and section context.",
                    "Classify candidate family and required downstream route.",
                    "Attach QKU, agent, replay/paper, and future PR bridge refs.",
                    "Mark live_order_authority=false.",
                ],
                "parameters": {"line_no": line_no, "section": section_by_line[line_no]},
                "parameter_ranges": {"candidate_priority": [0, 100], "owner_review_required": [0, 1]},
                "complexity_class_candidate": "O(n) scan plus O(1) route materialization per hit",
                "qku_refs": qku_refs_for_index(qku_pool, index),
                "agent_refs": common_agent_refs(include_quantum="quantum" in family),
                "agent_route_refs": common_agent_refs(include_quantum="quantum" in family),
                "replay_paper_route_refs": replay_route_refs(candidate_id),
                "test_vector": {"line_no": line_no, "expected_route": True},
                "formula_equivalence_family_id": f"EQF::{family}",
                "dedupe_key": f"MASTER_PLAN_ALGORITHM::{family}::{line_no}",
                "live_order_authority": False,
                "metadata_only_flag": False,
                **downstream_bridge(candidate_id),
            }
        )
    return rows


def _parameter_candidates(
    hits: list[tuple[int, str]],
    section_by_line: dict[int, str],
    qku_pool: list[str],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, (line_no, line) in enumerate(hits, start=1):
        candidate_id = f"PR162D_R1_MASTER_PLAN_PARAMETER_PACK_{index:04d}"
        rows.append(
            {
                "candidate_id": candidate_id,
                "parameter_pack_id": candidate_id,
                "candidate_class": "MASTER_PLAN_PARAMETER_PACK_CANDIDATE",
                "source_locator": c.MASTER_PLAN_REF,
                "master_plan_section_ref": section_by_line[line_no],
                "text_locator": f"line:{line_no}",
                "source_line_excerpt": line[:220],
                "expression": "parameter_value = resolve(default_or_seed, bounded_range, replay_paper_context)",
                "parameter_family": "master_plan_default_range_scale_pack",
                "default_value_candidate": "MASTER_PLAN_SEED_OR_RESOLUTION_RULE",
                "valid_range": {"min": "declared_lower_or_enum_member", "max": "declared_upper_or_enum_member"},
                "input_fields": ["default_or_seed", "bounded_range", "source_context"],
                "output_fields": ["parameter_pack_candidate"],
                "units": "parameter_pack",
                "qku_refs": qku_refs_for_index(qku_pool, index),
                "agent_refs": common_agent_refs(include_quantum=False),
                "agent_route_refs": common_agent_refs(include_quantum=False),
                "replay_paper_route_refs": replay_route_refs(candidate_id),
                "candidate_status": "MASTER_PLAN_PARAMETER_PACK_MINED",
                "live_order_authority": False,
                "metadata_only_flag": False,
                **downstream_bridge(candidate_id),
            }
        )
    return rows


def _quantum_candidates(
    hits: list[tuple[int, str]],
    section_by_line: dict[int, str],
    qku_pool: list[str],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, (line_no, line) in enumerate(hits, start=1):
        candidate_id = f"PR162D_R1_MASTER_PLAN_QUANTUM_{index:04d}"
        rows.append(
            {
                "candidate_id": candidate_id,
                "quantum_candidate_id": candidate_id,
                "candidate_class": "MASTER_PLAN_QUANTUM_FORMULATION_CANDIDATE",
                "source_locator": c.MASTER_PLAN_REF,
                "master_plan_section_ref": section_by_line[line_no],
                "text_locator": f"line:{line_no}",
                "source_line_excerpt": line[:220],
                "quantum_family": "MASTER_PLAN_QUANTUM_ROUTE_OR_FORMULATION",
                "mathematical_objective": "minimize x.T @ Q @ x + penalty_budget + penalty_exposure; map to Ising by x=(s+1)/2 when needed",
                "variable_definitions": {"x_i": "binary selected edge, feature, or parameter-stack variable"},
                "constraint_definitions": ["budget_limit", "exposure_limit", "same-basis comparator required"],
                "coefficient_definitions": {"Q_ij": "risk, exclusivity, and interaction coefficient candidate"},
                "qku_refs": qku_refs_for_index(qku_pool, index),
                "agent_refs": common_agent_refs(include_quantum=True),
                "agent_route_refs": common_agent_refs(include_quantum=True),
                "replay_paper_route_refs": replay_route_refs(candidate_id),
                "candidate_status": "MASTER_PLAN_QUANTUM_MINED_NO_ADVANTAGE_CLAIM",
                "live_order_authority": False,
                "quantum_metadata_only_flag": False,
                "metadata_only_flag": False,
                **downstream_bridge(candidate_id),
            }
        )
    return rows


def _gap_targets(formula_candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    lanes = ("LANE_A_KALSHI", "LANE_B_POLYMARKET", "LANE_C_FORECASTEX", "LANE_D_FORMULA_LIBRARY", "LANE_E_QUANTUM", "LANE_F_RESEARCH")
    for index, formula in enumerate(formula_candidates, start=1):
        rows.append(
            {
                "gap_target_id": f"PR162D_R1_MASTER_PLAN_GAP_{index:04d}",
                "candidate_class": "MASTER_PLAN_EXTERNAL_GAP_TARGET",
                "source_locator": c.MASTER_PLAN_REF,
                "master_plan_formula_id": formula["formula_id"],
                "master_plan_section_ref": formula["master_plan_section_ref"],
                "external_acquisition_lane": lanes[(index - 1) % len(lanes)],
                "gap_description": "External formula/data/parameter/quantum source needed to deepen master-plan candidate.",
                "qku_refs": formula["qku_refs"],
                "agent_refs": formula["agent_refs"],
                "agent_route_refs": formula["agent_route_refs"],
                "replay_paper_route_refs": formula["replay_paper_route_refs"],
                "candidate_status": "GAP_TARGET_ROUTED_TO_EXTERNAL_ACQUISITION",
                "live_order_authority": False,
            }
        )
    return rows


def _scan_record(scan_id: str, family: str, mention_count: int, extracted_count: int) -> dict[str, Any]:
    return {
        "scan_id": scan_id,
        "source_locator": c.MASTER_PLAN_REF,
        "scan_family": family,
        "mentions_scanned_count": mention_count,
        "extracted_candidate_count": extracted_count,
        "candidate_status": "MASTER_PLAN_SCAN_COMPLETE",
        "live_order_authority": False,
    }
