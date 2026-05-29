"""Multi-pass master-plan and prior-artifact candidate extraction."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Iterable

from . import constants as c
from .candidate_normalizer import compact_text, normalize_candidate_name


QUANTUM_PATTERNS = (
    ("QUBO", c.CandidateType.QUBO_TEMPLATE, "QUBO", c.QuantumApplicabilityClass.QUBO_APPLICABLE),
    ("ISING", c.CandidateType.ISING_TEMPLATE, "ISING", c.QuantumApplicabilityClass.ISING_APPLICABLE),
    ("QAOA", c.CandidateType.QAOA_SETTING, "QAOA", c.QuantumApplicabilityClass.QAOA_APPLICABLE),
    ("VQE", c.CandidateType.VQE_SETTING, "VQE", c.QuantumApplicabilityClass.VQE_APPLICABLE),
    ("ANNEAL", c.CandidateType.ANNEALING_SETTING, "ANNEALING", c.QuantumApplicabilityClass.ANNEALING_APPLICABLE),
)
NUMERIC_RE = re.compile(r"(?<![A-Za-z0-9_])[-+]?\d+(?:\.\d+)?(?:\s*(?:%|bps|ms|s|sec|seconds|shots|iters|iterations|USD|x))?")
RANGE_RE = re.compile(
    r"(?P<low>[-+]?\d+(?:\.\d+)?)\s*(?:-|to|through|\\.\\.)\s*(?P<high>[-+]?\d+(?:\.\d+)?)",
    re.IGNORECASE,
)
MAX_MASTER_PLAN_CANDIDATES_PER_SECTION = 3


def extract_master_plan_candidates(
    root: Path | str,
    sections: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    repo_root = Path(root).resolve()
    lines = (repo_root / c.MASTER_PLAN_PATH).read_text(encoding="utf-8").splitlines()
    candidates: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str, int, str]] = set()
    for section in sections:
        start = int(section["source_line_start_if_available"])
        end = int(section["source_line_end_if_available"])
        section_lines = lines[start - 1 : end]
        heading = str(section["section_heading"])
        section_candidate_count = 0
        if _append_if_candidate(
            candidates,
            seen,
            section,
            heading,
            start,
            "PASS_1_SECTION_AWARE_EXTRACTION",
            source_path=c.MASTER_PLAN_PATH.as_posix(),
            source_kind="MASTER_PLAN_SECTION_HEADING",
        ):
            section_candidate_count += 1
        in_code = False
        for offset, line in enumerate(section_lines, start=start):
            if section_candidate_count >= MAX_MASTER_PLAN_CANDIDATES_PER_SECTION:
                break
            stripped = line.strip()
            if stripped.startswith("```"):
                in_code = not in_code
                continue
            pass_ids = _line_pass_ids(stripped, in_code)
            for pass_id in pass_ids:
                if section_candidate_count >= MAX_MASTER_PLAN_CANDIDATES_PER_SECTION:
                    break
                if _append_if_candidate(
                    candidates,
                    seen,
                    section,
                    stripped,
                    offset,
                    pass_id,
                    source_path=c.MASTER_PLAN_PATH.as_posix(),
                    source_kind="MASTER_PLAN_BODY",
                ):
                    section_candidate_count += 1
    _assign_candidate_ids(candidates)
    return candidates


def extract_prior_artifact_candidates(
    root: Path | str,
    artifact_paths: Iterable[Path],
    *,
    start_index: int,
) -> list[dict[str, Any]]:
    repo_root = Path(root).resolve()
    candidates: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str, int, str]] = set()
    for path in sorted(artifact_paths, key=lambda value: value.as_posix()):
        rel = path.relative_to(repo_root).as_posix()
        text = path.stem.replace(".", " ")
        if path.suffix.lower() == ".json" and path.stat().st_size < 2_500_000:
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                payload = {}
            if isinstance(payload, dict):
                text = f"{path.stem} {' '.join(str(key) for key in list(payload.keys())[:14])}"
        section = {
            "section_id": f"PRIOR_PR_ARTIFACT__{path.stem}",
            "section_heading": "Prior PR artifact extraction",
            "section_order_index": 900000 + len(candidates),
            "section_depth": 0,
            "source_line_start_if_available": None,
            "source_line_end_if_available": None,
        }
        _append_if_candidate(
            candidates,
            seen,
            section,
            text,
            None,
            "PASS_3_TABLE_LIST_EXTRACTION",
            source_path=rel,
            source_kind="PRIOR_PR_ARTIFACT",
            force=True,
        )
    _assign_candidate_ids(candidates, start=start_index)
    return candidates


def section_search_coverage(
    sections: list[dict[str, Any]],
    candidates: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    by_section: dict[str, list[dict[str, Any]]] = {}
    for candidate in candidates:
        if candidate.get("extraction_source_path") == c.MASTER_PLAN_PATH.as_posix():
            by_section.setdefault(str(candidate["master_plan_section_id"]), []).append(candidate)
    output: list[dict[str, Any]] = []
    for section in sections:
        records = by_section.get(str(section["section_id"]), [])
        output.append(
            {
                **section,
                "searched_flag": True,
                "extraction_pass_ids_applied": list(c.EXTRACTION_PASS_IDS),
                "candidate_like_item_found_flag": bool(records),
                "candidate_count": len(records),
                "formula_candidate_count": _count(records, "FORMULA"),
                "algorithm_candidate_count": _count(records, "ALGORITHM"),
                "parameter_candidate_count": _count(records, "PARAMETER"),
                "range_candidate_count": _count(records, "RANGE"),
                "optimizer_candidate_count": _count(records, "OPTIMIZER"),
                "quantum_candidate_count": sum(1 for item in records if item["quantum_applicability_class"] != c.QuantumApplicabilityClass.NOT_QUANTUM_APPLICABLE.value),
                "strategy_template_candidate_count": _count(records, "STRATEGY"),
                "replay_paper_candidate_count": _count(records, "REPLAY_PAPER"),
                "agent_consumption_candidate_count": _count(records, "AGENT_CONSUMPTION"),
                "no_candidate_reason_if_none": None if records else "NO_CANDIDATE_LIKE_TEXT_MATCHED_DETERMINISTIC_EXTRACTION_PASSES",
                "search_error_flag": False,
                "search_error_reason_if_any": None,
            }
        )
    return output


def _append_if_candidate(
    candidates: list[dict[str, Any]],
    seen: set[tuple[str, str, str, int, str]],
    section: dict[str, Any],
    text: str,
    line_number: int | None,
    pass_id: str,
    *,
    source_path: str,
    source_kind: str,
    force: bool = False,
) -> bool:
    if not text:
        return False
    if any(pattern in text for pattern in c.FORBIDDEN_SCAN_PATTERNS):
        return False
    candidate_type, family, quantum_class = _classify(text)
    if not force and candidate_type is None:
        return False
    candidate_type = candidate_type or c.CandidateType.DOCTRINE_ONLY_REFERENCE
    normalized = normalize_candidate_name(_name_seed(text))
    key = (str(section["section_id"]), pass_id, candidate_type.value, line_number or 0, normalized)
    if key in seen:
        return False
    seen.add(key)
    lower, upper = _range_bounds(text)
    value = _default_value(text)
    formula = _formula_expression(text, candidate_type)
    record = {
        "residual_candidate_id": "",
        "extraction_source_path": source_path,
        "extraction_source_type": source_kind,
        "extraction_pass_ids": [pass_id],
        "master_plan_section_id": section["section_id"],
        "master_plan_heading": section["section_heading"],
        "source_line_or_locator_if_available": line_number,
        "extracted_text": compact_text(text),
        "normalized_candidate_name": normalized,
        "canonical_alias_candidates": _alias_candidates(text, family),
        "candidate_type": candidate_type.value,
        "candidate_family": family,
        "candidate_semantic_role": _semantic_role(candidate_type, family),
        "platform_scope": "PREDICTION_MARKETS_GENERAL",
        "market_type": _market_type(text),
        "strategy_class": _strategy_class(text),
        "parameter_role": _parameter_role(candidate_type, text),
        "formula_expression_if_available": formula,
        "default_value_if_available": value,
        "lower_bound_if_available": lower,
        "upper_bound_if_available": upper,
        "unit_if_available": _unit(text),
        "scale_if_available": _scale(text),
        "constraint_expression_if_available": compact_text(text) if "constraint" in text.lower() else None,
        "optimizer_family_if_available": _optimizer_family(text, family),
        "quantum_applicability_class": quantum_class.value,
        "source_intake_state": c.SourceIntakeState.SOURCE_INTAKE_ACCEPTED_MASTER_PLAN_LITERAL.value
        if source_kind.startswith("MASTER_PLAN")
        else c.SourceIntakeState.SOURCE_INTAKE_ACCEPTED_PRIOR_PR_ARTIFACT.value,
        "value_authority_class": c.ValueAuthorityClass.MASTER_PLAN_DOCTRINE_CANDIDATE_VALUE.value
        if source_kind.startswith("MASTER_PLAN")
        else c.ValueAuthorityClass.PRIOR_PR_CANDIDATE_VALUE.value,
        "coverage_state": "",
        "coverage_confidence_class": "",
        "coverage_match_tier": "",
        "canonical_alias_target_if_any": None,
        "covered_by_pr161a_record_ids": [],
        "covered_by_atomicrows_row_ids": [],
        "covered_by_pr154_target_ids": [],
        "covered_by_quantum_candidate_ids": [],
        "covered_by_replay_paper_route_ids": [],
        "upstream_pr_artifacts": [],
        "downstream_pr_targets": list(c.PR87_PR92_FLOW),
        "downstream_agent_roles": _agents(candidate_type, quantum_class),
        "residual_gap_flag": None,
        "residual_gap_type": None,
        "recommended_fill_lane": None,
        "pr161c_assimilation_required_flag": None,
        "pr161c_assimilation_queue_id_if_needed": None,
        "replay_paper_candidate_flag": _replay_paper_flag(candidate_type, text),
        "owner_review_future_promotion_flag": True,
        "live_use_allowed_flag": False,
        "no_profit_evidence_created_flag": True,
        "no_runtime_authority_created_flag": True,
        "residual_value_captured_in_pr161b_flag": value is not None,
        "residual_range_captured_in_pr161b_flag": lower is not None or upper is not None,
        "residual_formula_captured_in_pr161b_flag": formula is not None,
    }
    candidates.append(record)
    return True


def _assign_candidate_ids(candidates: list[dict[str, Any]], *, start: int = 1) -> None:
    for index, candidate in enumerate(candidates, start=start):
        candidate["residual_candidate_id"] = f"PR161B_CANDIDATE_{index:06d}"


def _line_pass_ids(text: str, in_code: bool) -> list[str]:
    passes: list[str] = []
    if in_code or ":" in text or "=" in text:
        passes.append("PASS_2_CODE_BLOCK_EXTRACTION")
    if text.startswith(("-", "*", "|")) or re.match(r"^\d+[.)]\s+", text):
        passes.append("PASS_3_TABLE_LIST_EXTRACTION")
    if _numeric_like(text):
        passes.append("PASS_4_NUMERIC_RANGE_UNIT_EXTRACTION")
    if _formula_algorithm_like(text):
        passes.append("PASS_5_FORMULA_ALGORITHM_EXTRACTION")
    if _quantum_like(text):
        passes.append("PASS_6_QUANTUM_EXTRACTION")
    if _agent_downstream_like(text):
        passes.append("PASS_7_AGENT_DOWNSTREAM_EXTRACTION")
    return passes[:3]


def _classify(text: str) -> tuple[c.CandidateType | None, str, c.QuantumApplicabilityClass]:
    upper = text.upper()
    for token, candidate_type, family, q_class in QUANTUM_PATTERNS:
        if token in upper:
            return candidate_type, family, q_class
    if "QUANTUM" in upper or "HAMILTONIAN" in upper or "ANSATZ" in upper:
        return c.CandidateType.QUANTUM_ALGORITHM, "QUANTUM", c.QuantumApplicabilityClass.GENERAL_QUANTUM_APPLICABLE
    if "HYBRID" in upper and ("ARBITRATION" in upper or "CLASSICAL" in upper):
        return c.CandidateType.HYBRID_ARBITRATION_SETTING, "HYBRID", c.QuantumApplicabilityClass.HYBRID_QUANTUM_CLASSICAL_APPLICABLE
    if any(token in upper for token in ("FORMULA", "OBJECTIVE", "MINIMIZE", "MAXIMIZE", "EQUATION")) or re.search(r"\w+\s*=\s*[^=]", text):
        return c.CandidateType.FORMULA_EXPRESSION, "FORMULA_ALGORITHM", c.QuantumApplicabilityClass.NOT_QUANTUM_APPLICABLE
    if "CONSTRAINT" in upper or "BOUND" in upper:
        return c.CandidateType.CONSTRAINT_EXPRESSION, "CONSTRAINT", c.QuantumApplicabilityClass.NOT_QUANTUM_APPLICABLE
    if any(token in upper for token in ("ALGORITHM", "MODEL", "SOLVER", "OPTIMIZER", "OPTIMIZATION")):
        return c.CandidateType.OPTIMIZER_SETTING if "OPTIM" in upper else c.CandidateType.ALGORITHM_NAME, "OPTIMIZER_ALGORITHM", c.QuantumApplicabilityClass.NOT_QUANTUM_APPLICABLE
    if any(token in upper for token in ("STRATEGY", "TEMPLATE", "ARBITRAGE", "ROUTING", "SIGNAL")):
        return c.CandidateType.STRATEGY_TEMPLATE, "STRATEGY", c.QuantumApplicabilityClass.NOT_QUANTUM_APPLICABLE
    if any(token in upper for token in ("PARAMETER", "DEFAULT", "THRESHOLD", "TOLERANCE")):
        return c.CandidateType.PARAMETER_DEFAULT if "DEFAULT" in upper else c.CandidateType.PARAMETER_NAME, "PARAMETER", c.QuantumApplicabilityClass.NOT_QUANTUM_APPLICABLE
    if any(token in upper for token in ("RANGE", "MIN", "MAX", "PERCENT", "%")) and _numeric_like(text):
        return c.CandidateType.PARAMETER_RANGE, "PARAMETER_RANGE", c.QuantumApplicabilityClass.NOT_QUANTUM_APPLICABLE
    if "LATENCY" in upper:
        return c.CandidateType.LATENCY_SETTING, "LATENCY", c.QuantumApplicabilityClass.NOT_QUANTUM_APPLICABLE
    if "RISK" in upper:
        return c.CandidateType.RISK_SETTING, "RISK", c.QuantumApplicabilityClass.NOT_QUANTUM_APPLICABLE
    if "CAPITAL" in upper or "BUDGET" in upper:
        return c.CandidateType.CAPITAL_SETTING, "CAPITAL", c.QuantumApplicabilityClass.NOT_QUANTUM_APPLICABLE
    if "REPLAY" in upper or "PAPER" in upper:
        return c.CandidateType.REPLAY_PAPER_TEST_SETTING, "REPLAY_PAPER", c.QuantumApplicabilityClass.NOT_QUANTUM_APPLICABLE
    if "QTT_" in upper or "AGENT" in upper:
        return c.CandidateType.AGENT_CONSUMPTION_FIELD, "AGENT_CONSUMPTION", c.QuantumApplicabilityClass.NOT_QUANTUM_APPLICABLE
    if any(token in upper for token in ("SOURCE", "EVIDENCE", "PROVENANCE")):
        return c.CandidateType.SOURCE_EVIDENCE_FIELD, "SOURCE_EVIDENCE", c.QuantumApplicabilityClass.NOT_QUANTUM_APPLICABLE
    if any(token in upper for token in ("LAW", "DOCTRINE", "GUARD", "CHECKLIST", "RUNBOOK", "RULE")):
        return c.CandidateType.DOCTRINE_ONLY_REFERENCE, "DOCTRINE", c.QuantumApplicabilityClass.NOT_QUANTUM_APPLICABLE
    return None, "UNCLASSIFIED", c.QuantumApplicabilityClass.NOT_QUANTUM_APPLICABLE


def _name_seed(text: str) -> str:
    words = re.findall(r"[A-Za-z][A-Za-z0-9_/-]*", text)
    return " ".join(words[:18]) or text


def _numeric_like(text: str) -> bool:
    return NUMERIC_RE.search(text) is not None


def _formula_algorithm_like(text: str) -> bool:
    upper = text.upper()
    return bool(re.search(r"\w+\s*=\s*[^=]", text)) or any(
        token in upper
        for token in ("FORMULA", "OBJECTIVE", "MINIMIZE", "MAXIMIZE", "ALGORITHM", "OPTIMIZER", "SOLVER")
    )


def _quantum_like(text: str) -> bool:
    upper = text.upper()
    return any(
        token in upper
        for token in ("QUANTUM", "QUBO", "ISING", "QAOA", "VQE", "ANNEAL", "HAMILTONIAN", "ANSATZ", "MIXER")
    )


def _agent_downstream_like(text: str) -> bool:
    upper = text.upper()
    return "QTT_" in upper or "AGENT" in upper or "PR8" in upper or "PR9" in upper or "REPLAY" in upper or "PAPER" in upper


def _range_bounds(text: str) -> tuple[str | None, str | None]:
    match = RANGE_RE.search(text)
    if not match:
        return None, None
    return match.group("low"), match.group("high")


def _default_value(text: str) -> str | None:
    if not any(token in text.lower() for token in ("default", "threshold", "tolerance", "min", "max", "range", "shot", "depth")):
        return None
    match = NUMERIC_RE.search(text)
    return match.group(0).strip() if match else None


def _formula_expression(text: str, candidate_type: c.CandidateType) -> str | None:
    if candidate_type in {c.CandidateType.FORMULA_EXPRESSION, c.CandidateType.OBJECTIVE_FUNCTION, c.CandidateType.CONSTRAINT_EXPRESSION}:
        return compact_text(text, limit=220)
    if candidate_type in {c.CandidateType.QUBO_TEMPLATE, c.CandidateType.ISING_TEMPLATE} and any(symbol in text for symbol in ("=", "^", "+", "-")):
        return compact_text(text, limit=220)
    return None


def _unit(text: str) -> str | None:
    match = re.search(r"\b(%|bps|ms|seconds|sec|shots|iterations|iters|USD)\b", text, re.IGNORECASE)
    return match.group(1) if match else None


def _scale(text: str) -> str | None:
    lower = text.lower()
    if "log" in lower:
        return "LOG_SCALE"
    if "linear" in lower:
        return "LINEAR_SCALE"
    if "percent" in lower or "%" in lower:
        return "PERCENT_SCALE"
    return None


def _alias_candidates(text: str, family: str) -> list[str]:
    aliases = [normalize_candidate_name(family)] if family != "UNCLASSIFIED" else []
    upper = text.upper()
    if "REPLAY" in upper or "PAPER" in upper:
        aliases.append("replay_paper_route")
    if "ATOMICROWS" in upper:
        aliases.append("atomicrows")
    if "PR154" in upper:
        aliases.append("pr154")
    return sorted(set(aliases))


def _semantic_role(candidate_type: c.CandidateType, family: str) -> str:
    if candidate_type.value.startswith("Q") or candidate_type in {
        c.CandidateType.ISING_TEMPLATE,
        c.CandidateType.ANNEALING_SETTING,
        c.CandidateType.HYBRID_ARBITRATION_SETTING,
    }:
        return "QUANTUM_OPTIMIZER_RESIDUAL_COVERAGE"
    if "FORMULA" in candidate_type.value or "ALGORITHM" in candidate_type.value:
        return "FORMULA_ALGORITHM_COVERAGE"
    return f"{family}_COVERAGE"


def _market_type(text: str) -> str:
    upper = text.upper()
    if "POLYMARKET" in upper:
        return "POLYMARKET"
    if "KALSHI" in upper:
        return "KALSHI"
    if "PREDICTIT" in upper:
        return "PREDICTIT"
    return "PREDICTION_MARKETS_GENERAL"


def _strategy_class(text: str) -> str:
    upper = text.upper()
    if "ARBITRAGE" in upper:
        return "ARBITRAGE"
    if "PORTFOLIO" in upper:
        return "PORTFOLIO"
    if "LATENCY" in upper:
        return "LATENCY_AWARE_ROUTING"
    if "CAPITAL" in upper:
        return "CAPITAL_ALLOCATION"
    return "GENERAL_CANDIDATE_COVERAGE"


def _parameter_role(candidate_type: c.CandidateType, text: str) -> str:
    if "PENALTY" in text.upper():
        return "penalty_weight"
    if "SHOT" in text.upper():
        return "shot_count"
    if "DEPTH" in text.upper():
        return "depth"
    return candidate_type.value.lower()


def _optimizer_family(text: str, family: str) -> str | None:
    if family in {"QUBO", "ISING", "QAOA", "VQE", "ANNEALING", "QUANTUM", "HYBRID"}:
        return family
    if "OPTIM" in text.upper():
        return "CLASSICAL_OR_HYBRID_OPTIMIZER"
    return None


def _agents(
    candidate_type: c.CandidateType,
    quantum_class: c.QuantumApplicabilityClass,
) -> list[str]:
    if quantum_class != c.QuantumApplicabilityClass.NOT_QUANTUM_APPLICABLE:
        return [
            "QTT_QUANTUM_ADVISORY_AGENT",
            "QTT_OPTIMIZER_ARBITRATION_AGENT",
            "QTT_REPLAY_AGENT",
            "QTT_PAPER_AGENT",
            "QTT_RESEARCH_AGENT",
        ]
    if candidate_type == c.CandidateType.REPLAY_PAPER_TEST_SETTING:
        return ["QTT_REPLAY_AGENT", "QTT_PAPER_AGENT", "QTT_RESEARCH_AGENT"]
    if candidate_type == c.CandidateType.DOCTRINE_ONLY_REFERENCE:
        return ["QTT_RESEARCH_AGENT", "QTT_OWNER_REVIEW_AGENT"]
    if candidate_type in {c.CandidateType.RISK_SETTING, c.CandidateType.CAPITAL_SETTING, c.CandidateType.LATENCY_SETTING}:
        return ["QTT_RISK_AGENT", "QTT_CAPITAL_AGENT", "QTT_LATENCY_AGENT", "QTT_REPLAY_AGENT"]
    return ["QTT_RESEARCH_AGENT", "QTT_ATOMICROWS_ENRICHMENT_AGENT", "QTT_REPLAY_AGENT"]


def _replay_paper_flag(candidate_type: c.CandidateType, text: str) -> bool:
    return candidate_type != c.CandidateType.DOCTRINE_ONLY_REFERENCE or "replay" in text.lower() or "paper" in text.lower()


def _count(records: list[dict[str, Any]], token: str) -> int:
    return sum(1 for item in records if token in str(item.get("candidate_type", "")))
