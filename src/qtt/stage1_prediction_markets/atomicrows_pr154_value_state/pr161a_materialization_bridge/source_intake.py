"""Source-intake candidate registry construction for PR161A."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from . import constants as c
from .io import as_mapping, read_json, records


SOCIAL_WEB_CLASSES = {
    "SOCIAL_POST",
    "X_POST",
    "FORUM_THREAD",
    "BLOG_POST",
    "NEWS_ARTICLE",
    "NEWSLETTER",
    "TRADING_ARTICLE",
    "THIRD_PARTY_ANALYSIS",
    "MICROSTRUCTURE_WRITEUP",
    "STRATEGY_WRITEUP",
}


def _state_for_source_class(source_class: str) -> str:
    if source_class == "GITHUB_REPOSITORY":
        return c.SourceIntakeState.SOURCE_INTAKE_ACCEPTED_GITHUB_RESEARCH_PATTERN.value
    if source_class == "FORUM_THREAD":
        return c.SourceIntakeState.SOURCE_INTAKE_ACCEPTED_FORUM_SIGNAL.value
    if source_class in {"BLOG_POST", "TRADING_ARTICLE", "STRATEGY_WRITEUP"}:
        return c.SourceIntakeState.SOURCE_INTAKE_ACCEPTED_BLOG_SIGNAL.value
    if source_class in {"NEWS_ARTICLE", "NEWSLETTER"}:
        return c.SourceIntakeState.SOURCE_INTAKE_ACCEPTED_NEWS_SIGNAL.value
    if source_class in {"SOCIAL_POST", "X_POST"}:
        return c.SourceIntakeState.SOURCE_INTAKE_ACCEPTED_SOCIAL_SIGNAL.value
    if source_class in SOCIAL_WEB_CLASSES:
        return c.SourceIntakeState.SOURCE_INTAKE_ACCEPTED_OPEN_SOURCE_INTELLIGENCE.value
    return c.SourceIntakeState.SOURCE_INTAKE_ACCEPTED_RESEARCH.value


def build_source_intake_records(root: Path) -> list[dict[str, Any]]:
    open_research = records(
        as_mapping(read_json(root / c.GENERATED_DIR / "PR159S_OpenResearchSourceIntake.report.json"))
    )
    official_delta = records(
        as_mapping(read_json(root / c.GENERATED_DIR / "PR159S_OfficialExternalFactDelta.report.json"))
    )
    output: list[dict[str, Any]] = []
    for index, record in enumerate(official_delta, start=1):
        target_id = str(record.get("target_id_or_row_id"))
        output.append(
            _source_record(
                f"PR161A_SOURCE_OFFICIAL_CANDIDATE__{index:04d}",
                c.SourceIntakeState.SOURCE_INTAKE_ACCEPTED_OFFICIAL_CANDIDATE.value,
                record.get("source_class") or "OFFICIAL_PROVIDER_DOCS",
                record.get("source_quality_tier") or "OFFICIAL_CANDIDATE_PENDING_EXACT_FIELD",
                record.get("source_locator") or record.get("source_artifact_path") or c.PR159S_REPORT_PATHS[6].as_posix(),
                "Official-source candidate reused from PR159S; pending exact accepted field before promotion.",
                target_id,
                target_id,
                None,
                "OFFICIAL_CANDIDATE_REUSE",
            )
        )
    for index, record in enumerate(open_research, start=1):
        target_id = str(record.get("target_id_or_row_id"))
        source_class = str(record.get("source_class"))
        output.append(
            _source_record(
                f"PR161A_SOURCE_OPEN_RESEARCH__{index:04d}",
                _state_for_source_class(source_class),
                source_class,
                str(record.get("source_quality_tier") or "OPEN_RESEARCH_CANDIDATE"),
                str(record.get("source_url") or record.get("source_artifact_path")),
                str(record.get("claim_summary") or "Open candidate intelligence only."),
                target_id,
                target_id if target_id.startswith("AR_") else None,
                target_id if target_id.startswith("PR154") else None,
                "PR159S_RESEARCH_REUSE",
                title=record.get("title"),
                author=record.get("author_or_handle_if_available"),
            )
        )
    output.extend(_internal_and_quantum_source_records())
    return output


def _source_record(
    source_intake_id: str,
    state: str,
    source_type: str,
    quality_tier: str,
    locator: str,
    claim: str,
    target_id: str,
    atomicrow_id: str | None,
    pr154_id: str | None,
    basis: str,
    *,
    title: Any = None,
    author: Any = None,
) -> dict[str, Any]:
    return {
        "source_intake_id": source_intake_id,
        "source_url_or_locator": locator,
        "source_type": source_type,
        "source_intake_state": state,
        "title_or_label": title,
        "author_or_publisher": author,
        "retrieval_date": c.RETRIEVAL_DATE,
        "extracted_claim": claim,
        "extracted_formula": None,
        "extracted_parameter": None,
        "extracted_default_or_range": None,
        "applicable_market": "PREDICTION_MARKETS_GENERAL",
        "applicable_platform": "PREDICTION_MARKETS_GENERAL",
        "applicable_strategy": "VALUE_STATE_MATERIALIZATION",
        "confidence_class": "CANDIDATE_CONFIDENCE_MEDIUM",
        "novelty_class": "CANDIDATE_NOVELTY_REUSED_PRIOR_PR_OR_DEFAULT",
        "duplication_status": "DEDUPED_BY_SOURCE_ID_AND_TARGET",
        "safety_status": "SAFE_METADATA_ONLY_NO_EXTERNAL_CODE_EXECUTED",
        "source_quality_tier": quality_tier,
        "candidate_value_or_range": basis,
        "replay_paper_test_route": f"PR161A_REPLAY_ROUTE__{target_id}",
        "risk_notes": c.NON_LIVE_PROMOTION_LIMITATION,
        "quantum_relevance": "QUANTUM_RELEVANT_IF_OPTIMIZER_OR_SELECTION_RELATED",
        "atomicrows_mapping": [atomicrow_id] if atomicrow_id else [],
        "pr154_mapping": [pr154_id] if pr154_id else [],
        "downstream_agent_mapping": list(c.DOWNSTREAM_AGENT_ROLES),
        "live_use_allowed_flag": False,
    }


def _internal_and_quantum_source_records() -> list[dict[str, Any]]:
    seeds = [
        (
            "PR161A_SOURCE_OWNER_INTERNAL_DEFAULTS",
            c.SourceIntakeState.SOURCE_INTAKE_ACCEPTED_OWNER_INTERNAL.value,
            "OWNER_INTERNAL_POLICY",
            "OWNER_APPROVED_INTERNAL_DEFAULT",
            "OWNER_PR161A_CANDIDATE_MATERIALIZATION_APPROVAL",
            "Owner approval allows candidate/default filling but does not create live authority.",
        ),
        (
            "PR161A_SOURCE_INSTITUTIONAL_DEFAULTS",
            c.SourceIntakeState.SOURCE_INTAKE_ACCEPTED_INSTITUTIONAL_CONVENTION.value,
            "INSTITUTIONAL_CONVENTION",
            "INSTITUTIONAL_QTT_STARTER_DEFAULT",
            "QTT_PR161A_INTERNAL_DEFAULT_LOGIC",
            "Institutional-style neutral candidate defaults for replay/paper preparation.",
        ),
        (
            "PR161A_SOURCE_CLASSICAL_BASELINE_DEFAULTS",
            c.SourceIntakeState.SOURCE_INTAKE_ACCEPTED_OPTIMIZER_DOCUMENTATION.value,
            "CLASSICAL_BASELINE_CONVENTION",
            "CLASSICAL_BASELINE_CANDIDATE",
            "QTT_CLASSICAL_COMPARATOR_DEFAULT_LOGIC",
            "Classical comparator candidates for every quantum-ready profile.",
        ),
        (
            "PR161A_SOURCE_IBM_QAOA_DOCS",
            c.SourceIntakeState.SOURCE_INTAKE_ACCEPTED_QUANTUM_RESEARCH.value,
            "QUANTUM_PROVIDER_DOCUMENTATION",
            "QUANTUM_RESEARCH_CANDIDATE",
            "https://qiskit-community.github.io/qiskit-optimization/stubs/qiskit_optimization.algorithms.MinimumEigenOptimizer.html",
            "QAOA can be modeled as a minimum-eigen optimizer candidate after QUBO or Ising mapping.",
        ),
        (
            "PR161A_SOURCE_IBM_VQE_DOCS",
            c.SourceIntakeState.SOURCE_INTAKE_ACCEPTED_QUANTUM_RESEARCH.value,
            "QUANTUM_PROVIDER_DOCUMENTATION",
            "QUANTUM_RESEARCH_CANDIDATE",
            "https://qiskit-community.github.io/qiskit-algorithms/stubs/qiskit_algorithms.VQE.html",
            "VQE provides a candidate expectation-minimization template for Hamiltonian objectives.",
        ),
        (
            "PR161A_SOURCE_DWAVE_BQM_DOCS",
            c.SourceIntakeState.SOURCE_INTAKE_ACCEPTED_OPTIMIZER_DOCUMENTATION.value,
            "OPTIMIZER_DOCUMENTATION",
            "OPTIMIZER_DOCUMENTATION_CANDIDATE",
            "https://docs.dwavequantum.com/en/latest/concepts/models.html",
            "Binary quadratic models support QUBO/Ising candidate objective representation.",
        ),
        (
            "PR161A_SOURCE_DWAVE_SAMPLER_DOCS",
            c.SourceIntakeState.SOURCE_INTAKE_ACCEPTED_OPTIMIZER_DOCUMENTATION.value,
            "OPTIMIZER_DOCUMENTATION",
            "OPTIMIZER_DOCUMENTATION_CANDIDATE",
            "https://docs.dwavequantum.com/en/latest/ocean/api_ref_dimod/sampler_composites.html",
            "Sampler-style interfaces support future annealing and quantum-inspired comparison candidates.",
        ),
    ]
    return [
        _source_record(
            source_id,
            state,
            source_type,
            quality,
            locator,
            claim,
            source_id,
            None,
            None,
            quality,
            title=source_type,
            author="QTT/Provider documentation",
        )
        for source_id, state, source_type, quality, locator, claim in seeds
    ]
