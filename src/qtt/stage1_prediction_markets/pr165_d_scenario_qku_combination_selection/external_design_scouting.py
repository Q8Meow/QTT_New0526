"""Candidate-only external design scouting ledger for PR165-D."""

from __future__ import annotations

from typing import Any

from .authority_policy import authority_zero_counts
from .central_vocab import AUTHORITY_BOUNDARY_REF, DOWNSTREAM_PR_ROUTES, NO_ORPHAN_STATUS, UPSTREAM_PR_REFS, VALIDATION_STATUS
from .deterministic_ids import ordinal_ref


def build_external_design_scout_rows() -> list[dict[str, Any]]:
    sources = [
        (
            "MMR_DIVERSIFICATION_GREEDY_SELECTION",
            "https://www.elastic.co/search-labs/blog/maximum-marginal-relevance-diversify-results",
            "Candidate design input for deterministic marginal relevance versus diversity ranking.",
        ),
        (
            "COST_AWARE_PORTFOLIO_CONSTRUCTION",
            "https://arxiv.org/html/2412.11575v2",
            "Candidate design input for transaction-cost-aware capacity and concentration treatment.",
        ),
        (
            "FALSE_DISCOVERY_TRANSACTION_COST_SELECTION",
            "https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4487978",
            "Candidate design input for multiple-testing and false-discovery adjusted selection.",
        ),
        (
            "DWAVE_MODEL_CLASS_ROUTING",
            "https://docs.dwavequantum.com/en/latest/ocean/api_ref_dimod/models.html",
            "Candidate design input for BQM/QUBO/Ising/CQM/DQM formulation labels without backend execution.",
        ),
        (
            "QISKIT_QUADRATIC_PROGRAM_ROUTE",
            "https://qiskit-community.github.io/qiskit-optimization/tutorials/03_minimum_eigen_optimizer.html",
            "Candidate design input for QuadraticProgram to Ising and MinimumEigenOptimizer route labels.",
        ),
    ]
    rows: list[dict[str, Any]] = []
    for index, (topic, url, use) in enumerate(sources, start=1):
        rows.append(
            {
                "external_design_scout_id": ordinal_ref("PR165_D_EXTERNAL_DESIGN_SCOUT", index),
                "design_topic": topic,
                "source_url": url,
                "source_authority_label": "EXTERNAL_CANDIDATE_DESIGN_REFERENCE",
                "selection_use": use,
                "source_truth_conversion_allowed_by_pr165_d": False,
                "external_code_execution_allowed": False,
                "candidate_value_materialization_allowed": True,
                "provenance_label_preserved": True,
                "owning_agent": "selection_agent",
                "consuming_agent": "risk_agent",
                "upstream_source_pr_refs": list(UPSTREAM_PR_REFS),
                "downstream_consumer_pr_refs": list(DOWNSTREAM_PR_ROUTES),
                "validator": "tools/validate_pr165_d_scenario_qku_combination_selection.py",
                "manifest_entry_ref": "PR165_D_ReportManifest.report.json",
                "no_orphan_status": NO_ORPHAN_STATUS,
                "authority_boundary_ref": AUTHORITY_BOUNDARY_REF,
                "validation_status": VALIDATION_STATUS,
                **authority_zero_counts(),
            }
        )
    return rows
