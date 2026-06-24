#!/usr/bin/env python3
"""Central configuration for PR168-RP5A legacy semantic audit."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
GENERATED_ROOT = REPO_ROOT / "docs" / "master_plan" / "generated"
SHARD_ROOT = GENERATED_ROOT / "rp5a"

REPORT_VERSION = "PR168-RP5A-v2.0"
CREATED_AT_UTC = "2026-06-24T00:00:00Z"
BRANCH_NAME = "pr168-rp5a-legacy-semantic-audit"
ROADMAP_PR = "PR168-RP5A"
PR_TITLE = "PR168-RP5A: Legacy semantic audit for immutable QKU/formula architecture"
PR240_HEAD_REF = "pr168-recovery1-rank3-guided-repair-retest"

PREFERRED_MAX_PHYSICAL_PATH_LENGTH = 180
WARNING_THRESHOLD_PHYSICAL_PATH_LENGTH = 200
HARD_FAIL_PHYSICAL_PATH_LENGTH = 240
MAX_WALL_SECONDS = 3600
MAX_FILES_SCANNED = 100_000
MAX_MATCHED_FILES = 25_000
MAX_LINE_HITS_PER_FILE = 50
MAX_TOTAL_LINE_HITS = 500_000
MAX_CONSUMER_REFS_PER_FILE = 100
MAX_IDENTITY_REFS_PER_FILE = 50
MAX_STRUCTURED_JSON_BYTES = 2_000_000
MAX_TOTAL_ROWS_PER_SHARD = 500_000
PROGRESS_INTERVAL_SECONDS = 30
CHECKPOINT_PATH = REPO_ROOT / ".tmp" / "rp5a_scan_checkpoint.json"

TEXT_EXTENSIONS = frozenset(
    {
        ".cfg",
        ".csv",
        ".ini",
        ".json",
        ".jsonl",
        ".md",
        ".ps1",
        ".py",
        ".rst",
        ".toml",
        ".tsv",
        ".txt",
        ".yaml",
        ".yml",
    }
)

SCAN_EXCLUDED_PREFIXES = (
    ".git/",
    ".mypy_cache/",
    ".pytest_cache/",
    ".tmp/",
    ".venv/",
    "__pycache__/",
    "node_modules/",
    "tmp/",
    "temp/",
    "archive/",
    "archives/",
    "docs/master_plan/generated/archive/",
    "docs/master_plan/generated/archived/",
    "docs/master_plan/generated/rp5a/",
    "tests/pr168_rp5a/",
)
SCAN_EXCLUDED_EXACT = frozenset(
    {
        "tools/build_pr168_rp5a_legacy_semantic_audit.py",
        "tools/validate_pr168_rp5a_legacy_semantic_audit.py",
    }
)
SCAN_EXCLUDED_NAME_PREFIXES = (
    "tools/pr168_rp5a_",
    "docs/master_plan/generated/PR168_RP5A_",
)

FILE_KIND_GENERATED_REPORT = "GENERATED_REPORT"
FILE_KIND_GENERATED_SHARD = "GENERATED_SHARD"
FILE_KIND_MANIFEST = "MANIFEST"
FILE_KIND_TOOL_SOURCE = "TOOL_SOURCE"
FILE_KIND_TEST_SOURCE = "TEST_SOURCE"
FILE_KIND_DOC = "DOC"
FILE_KIND_VALIDATOR = "VALIDATOR"
FILE_KIND_CURRENTIZATION = "CURRENTIZATION"
FILE_KIND_UNKNOWN = "UNKNOWN"

DELETE_CLASSIFICATIONS = (
    "DELETE_FROM_ACTIVE_TREE_SAFE",
    "DELETE_AFTER_QKU_FORMULA_IDENTITY_RECLAIM",
    "KEEP_ACTIVE_CONSUMER",
    "KEEP_UNIQUE_QKU_FORMULA_SOURCE",
    "KEEP_TEST_FIXTURE",
    "KEEP_VALIDATION_DEPENDENCY",
    "KEEP_LEGACY_SUMMARY_ONLY",
    "ARCHIVE_NO_VALIDATION_SCAN",
    "REWRITE_CONSUMER_FIRST",
    "UNCLEAR_DO_NOT_DELETE",
)

CONSUMER_STRENGTHS = (
    "DIRECT_IMPORT",
    "DIRECT_PATH_READ",
    "GLOB_SCAN",
    "REPORT_REF",
    "DOC_REF",
    "MANIFEST_REF",
    "UNKNOWN",
)

VALIDATION_DEPENDENCY_TYPES = (
    "REQUIRED_FILE",
    "REQUIRED_PREFIX",
    "GLOB_SCANNED",
    "COUNT_EXPECTATION",
    "CURRENTIZATION_EXPECTATION",
    "TEST_FIXTURE",
    "UNKNOWN",
    "NONE",
)

BLAST_RADIUS_WEIGHTS = {
    "critical_term": 8,
    "high_term": 5,
    "medium_term": 3,
    "low_term": 1,
    "active_consumer": 7,
    "validation_dependency": 7,
    "identity_dependency": 8,
    "agent_touchpoint": 6,
}

FORBIDDEN_OPERATION_COUNTERS = {
    "deleted_file_count": 0,
    "moved_file_count": 0,
    "archived_file_count": 0,
    "legacy_artifact_content_modified_count": 0,
    "validation_scope_removed_count": 0,
    "runtime_stack_generation_count": 0,
    "trade_simulation_count": 0,
    "formula_reclaim_count": 0,
    "active_registry_authority_created_count": 0,
    "live_order_authority_created_count": 0,
    "source_truth_authority_created_count": 0,
    "quantum_backend_execution_count": 0,
    "qtt_sha_or_atomicrows_hash_authority_count": 0,
    "global_formula_qku_ban_authority_created_count": 0,
}


@dataclass(frozen=True)
class TermSpec:
    term_id: str
    term_text_or_regex: str
    term_family: str
    severity: str
    old_semantic_risk: str
    canonical_future_interpretation: str
    is_regex: bool = False
    default_delete_signal: bool = False
    requires_human_review_if_unclear: bool = True

    def to_row(self) -> dict[str, Any]:
        return {
            "term_id": self.term_id,
            "term_text_or_regex": self.term_text_or_regex,
            "term_family": self.term_family,
            "severity": self.severity,
            "old_semantic_risk": self.old_semantic_risk,
            "canonical_future_interpretation": self.canonical_future_interpretation,
            "is_regex": self.is_regex,
            "default_delete_signal": self.default_delete_signal,
            "requires_human_review_if_unclear": self.requires_human_review_if_unclear,
        }


def _term(
    term_id: str,
    text: str,
    family: str,
    severity: str,
    risk: str,
    interpretation: str,
    *,
    regex: bool = False,
) -> TermSpec:
    return TermSpec(
        term_id=term_id,
        term_text_or_regex=text,
        term_family=family,
        severity=severity,
        old_semantic_risk=risk,
        canonical_future_interpretation=interpretation,
        is_regex=regex,
    )


TERM_TAXONOMY: tuple[TermSpec, ...] = (
    _term("T001", "formula repair", "FORMULA_REPAIR_SEMANTIC_RISK", "HIGH", "May imply canonical formula mutation to force usability or profit.", "FORMULA_EXECUTION_ADAPTER_OR_INPUT_BINDING"),
    _term("T002", "repair formula", "FORMULA_REPAIR_SEMANTIC_RISK", "HIGH", "May imply canonical formula mutation before replay/paper.", "FORMULA_EXECUTION_ADAPTER_OR_INPUT_BINDING"),
    _term("T003", "formula_repair", "FORMULA_REPAIR_SEMANTIC_RISK", "HIGH", "May encode repair as formula state.", "FORMULA_EXECUTION_ADAPTER_OR_INPUT_BINDING"),
    _term("T004", "FormulaRepair", "FORMULA_REPAIR_SEMANTIC_RISK", "HIGH", "May encode repair as formula state.", "FORMULA_EXECUTION_ADAPTER_OR_INPUT_BINDING"),
    _term("T005", "QKU repair", "QKU_REPAIR_SEMANTIC_RISK", "HIGH", "May imply QKU mutation instead of execution-route repair.", "QKU_EXECUTION_ROUTE_OR_TRADE_PLAN_BINDING"),
    _term("T006", "repair QKU", "QKU_REPAIR_SEMANTIC_RISK", "HIGH", "May imply QKU mutation before replay/paper.", "QKU_EXECUTION_ROUTE_OR_TRADE_PLAN_BINDING"),
    _term("T007", "qku_repair", "QKU_REPAIR_SEMANTIC_RISK", "HIGH", "May encode QKU repair as canonical identity state.", "QKU_EXECUTION_ROUTE_OR_TRADE_PLAN_BINDING"),
    _term("T008", "QKURepair", "QKU_REPAIR_SEMANTIC_RISK", "HIGH", "May encode QKU repair as canonical identity state.", "QKU_EXECUTION_ROUTE_OR_TRADE_PLAN_BINDING"),
    _term("T009", "negative formula", "NEGATIVE_OUTCOME_GLOBALIZATION_RISK", "HIGH", "May be read as permanent formula-level negative truth.", "CONDITION_SCOPED_NEGATIVE_OUTCOME_MEMORY"),
    _term("T010", "formula negative", "NEGATIVE_OUTCOME_GLOBALIZATION_RISK", "HIGH", "May be read as permanent formula-level negative truth.", "CONDITION_SCOPED_NEGATIVE_OUTCOME_MEMORY"),
    _term("T011", "negative_formula", "NEGATIVE_OUTCOME_GLOBALIZATION_RISK", "HIGH", "May be read as permanent formula-level negative truth.", "CONDITION_SCOPED_NEGATIVE_OUTCOME_MEMORY"),
    _term("T012", "no-trade dominated formula", "NO_TRADE_GLOBALIZATION_RISK", "HIGH", "May turn no-trade comparison into formula-level blocker.", "NO_TRADE_ADVISED_FOR_THIS_CONTEXT_ONLY"),
    _term("T013", "no_trade_dominated_formula", "NO_TRADE_GLOBALIZATION_RISK", "HIGH", "May turn no-trade comparison into formula-level blocker.", "NO_TRADE_ADVISED_FOR_THIS_CONTEXT_ONLY"),
    _term("T014", "no-trade dominated", "NO_TRADE_GLOBALIZATION_RISK", "HIGH", "May turn a context comparator into global blocker.", "NO_TRADE_ADVISED_FOR_THIS_CONTEXT_ONLY"),
    _term("T015", "no_trade_dominated", "NO_TRADE_GLOBALIZATION_RISK", "HIGH", "May turn a context comparator into global blocker.", "NO_TRADE_ADVISED_FOR_THIS_CONTEXT_ONLY"),
    _term("T016", "permanent no-trade", "NO_TRADE_GLOBALIZATION_RISK", "CRITICAL", "May permanently block future replay/paper attempts.", "NO_TRADE_ADVISED_FOR_THIS_CONTEXT_ONLY"),
    _term("T017", "permanent_no_trade", "NO_TRADE_GLOBALIZATION_RISK", "CRITICAL", "May permanently block future replay/paper attempts.", "NO_TRADE_ADVISED_FOR_THIS_CONTEXT_ONLY"),
    _term("T018", "global negative", "NEGATIVE_OUTCOME_GLOBALIZATION_RISK", "CRITICAL", "May promote condition-scoped negative memory into global truth.", "CONDITION_SCOPED_NEGATIVE_OUTCOME_MEMORY"),
    _term("T019", "global_negative", "NEGATIVE_OUTCOME_GLOBALIZATION_RISK", "CRITICAL", "May promote condition-scoped negative memory into global truth.", "CONDITION_SCOPED_NEGATIVE_OUTCOME_MEMORY"),
    _term("T020", "globally negative", "NEGATIVE_OUTCOME_GLOBALIZATION_RISK", "CRITICAL", "May promote condition-scoped negative memory into global truth.", "CONDITION_SCOPED_NEGATIVE_OUTCOME_MEMORY"),
    _term("T021", "global formula ban", "NEGATIVE_OUTCOME_GLOBALIZATION_RISK", "CRITICAL", "May create forbidden global formula ban semantics.", "CONDITION_SCOPED_NEGATIVE_OUTCOME_MEMORY"),
    _term("T022", "globally banned formula", "NEGATIVE_OUTCOME_GLOBALIZATION_RISK", "CRITICAL", "May create forbidden global formula ban semantics.", "CONDITION_SCOPED_NEGATIVE_OUTCOME_MEMORY"),
    _term("T023", "formula banned", "NEGATIVE_OUTCOME_GLOBALIZATION_RISK", "CRITICAL", "May create forbidden formula ban semantics.", "CONDITION_SCOPED_NEGATIVE_OUTCOME_MEMORY"),
    _term("T024", "QKU banned", "QKU_REPAIR_SEMANTIC_RISK", "CRITICAL", "May create forbidden global QKU ban semantics.", "QKU_EXECUTION_ROUTE_OR_TRADE_PLAN_BINDING"),
    _term("T025", "unselected formula", "UNSELECTED_OR_FAILED_SEMANTIC_RISK", "MEDIUM", "May be read as formula unusability rather than local non-selection.", "NOT_SELECTED_IN_THIS_CONTEXT_ONLY"),
    _term("T026", "unselected_formula", "UNSELECTED_OR_FAILED_SEMANTIC_RISK", "MEDIUM", "May be read as formula unusability rather than local non-selection.", "NOT_SELECTED_IN_THIS_CONTEXT_ONLY"),
    _term("T027", "failed formula", "UNSELECTED_OR_FAILED_SEMANTIC_RISK", "HIGH", "May be read as permanent formula failure.", "PRESERVED_NEEDS_EXECUTION_CONTRACT"),
    _term("T028", "formula failed", "UNSELECTED_OR_FAILED_SEMANTIC_RISK", "HIGH", "May be read as permanent formula failure.", "PRESERVED_NEEDS_EXECUTION_CONTRACT"),
    _term("T029", "non-computable formula", "NONCOMPUTABLE_BLOCKER_RISK", "HIGH", "May be read as permanent non-computability.", "PRESERVED_NEEDS_EXECUTION_CONTRACT"),
    _term("T030", "non_computable_formula", "NONCOMPUTABLE_BLOCKER_RISK", "HIGH", "May be read as permanent non-computability.", "PRESERVED_NEEDS_EXECUTION_CONTRACT"),
    _term("T031", "formula not usable", "NONCOMPUTABLE_BLOCKER_RISK", "HIGH", "May be read as permanent unusability.", "PRESERVED_NEEDS_EXECUTION_CONTRACT"),
    _term("T032", "formula_not_usable", "NONCOMPUTABLE_BLOCKER_RISK", "HIGH", "May be read as permanent unusability.", "PRESERVED_NEEDS_EXECUTION_CONTRACT"),
    _term("T033", "repair route", "FORMULA_REPAIR_SEMANTIC_RISK", "MEDIUM", "May imply mutation route rather than adapter/input binding work.", "FORMULA_EXECUTION_ADAPTER_OR_INPUT_BINDING"),
    _term("T034", "repair_route", "FORMULA_REPAIR_SEMANTIC_RISK", "MEDIUM", "May imply mutation route rather than adapter/input binding work.", "FORMULA_EXECUTION_ADAPTER_OR_INPUT_BINDING"),
    _term("T035", "negative repair", "NEGATIVE_OUTCOME_GLOBALIZATION_RISK", "HIGH", "May imply repairing away negative outcomes instead of preserving context memory.", "CONDITION_SCOPED_NEGATIVE_OUTCOME_MEMORY"),
    _term("T036", "negative_repair", "NEGATIVE_OUTCOME_GLOBALIZATION_RISK", "HIGH", "May imply repairing away negative outcomes instead of preserving context memory.", "CONDITION_SCOPED_NEGATIVE_OUTCOME_MEMORY"),
    _term("T037", "repair-before-retest", "FORMULA_REPAIR_SEMANTIC_RISK", "HIGH", "May imply formula repair as precondition for replay/paper.", "FORMULA_EXECUTION_ADAPTER_OR_INPUT_BINDING"),
    _term("T038", "repair_before_retest", "FORMULA_REPAIR_SEMANTIC_RISK", "HIGH", "May imply formula repair as precondition for replay/paper.", "FORMULA_EXECUTION_ADAPTER_OR_INPUT_BINDING"),
    _term("T039", "source truth", "SOURCE_TRUTH_AUTHORITY_RISK", "CRITICAL", "May be read as source-truth authority.", "INPUT_PROVENANCE_BINDING_OR_RELIABILITY_PENALTY"),
    _term("T040", "source-truth", "SOURCE_TRUTH_AUTHORITY_RISK", "CRITICAL", "May be read as source-truth authority.", "INPUT_PROVENANCE_BINDING_OR_RELIABILITY_PENALTY"),
    _term("T041", "champion", "LIVE_OR_CHAMPION_AUTHORITY_RISK", "CRITICAL", "May be read as champion/live promotion authority.", "AUTHORITY_BOUNDARY_LABEL_ONLY"),
    _term("T042", "live candidate", "LIVE_OR_CHAMPION_AUTHORITY_RISK", "CRITICAL", "May be read as live-trading readiness.", "AUTHORITY_BOUNDARY_LABEL_ONLY"),
    _term("T043", "LIVE_CANDIDATE", "LIVE_OR_CHAMPION_AUTHORITY_RISK", "CRITICAL", "May be read as live-trading readiness.", "AUTHORITY_BOUNDARY_LABEL_ONLY"),
    _term("T044", "REAL_POSITIVE", "LIVE_OR_CHAMPION_AUTHORITY_RISK", "CRITICAL", "May be read as real-profit proof authority.", "AUTHORITY_BOUNDARY_LABEL_ONLY"),
    _term("T045", "REAL_NEGATIVE", "NEGATIVE_OUTCOME_GLOBALIZATION_RISK", "CRITICAL", "May be read as real negative truth authority.", "CONDITION_SCOPED_NEGATIVE_OUTCOME_MEMORY"),
    _term("T046", "qtt sha", "HASH_OR_FREEZE_AUTHORITY_RISK", "CRITICAL", "May be read as QTT SHA/freeze authority.", "AUTHORITY_BOUNDARY_LABEL_ONLY"),
    _term("T047", "qtt_sha", "HASH_OR_FREEZE_AUTHORITY_RISK", "CRITICAL", "May be read as QTT SHA/freeze authority.", "AUTHORITY_BOUNDARY_LABEL_ONLY"),
    _term("T048", "AtomicRows hash", "HASH_OR_FREEZE_AUTHORITY_RISK", "CRITICAL", "May be read as AtomicRows hash authority.", "AUTHORITY_BOUNDARY_LABEL_ONLY"),
    _term("T049", "AtomicRows bundle hash", "HASH_OR_FREEZE_AUTHORITY_RISK", "CRITICAL", "May be read as AtomicRows bundle hash authority.", "AUTHORITY_BOUNDARY_LABEL_ONLY"),
    _term("T050", "freeze authority", "HASH_OR_FREEZE_AUTHORITY_RISK", "CRITICAL", "May be read as freeze authority.", "AUTHORITY_BOUNDARY_LABEL_ONLY"),
    _term("T051", "global digest", "HASH_OR_FREEZE_AUTHORITY_RISK", "CRITICAL", "May be read as global digest authority.", "AUTHORITY_BOUNDARY_LABEL_ONLY"),
    _term("R001", r"\b(formula|qku).{0,40}(repair|repaired|failed|negative|banned|unusable|non[-_ ]?computable)\b", "FORMULA_REPAIR_SEMANTIC_RISK", "HIGH", "Regex captures formula/QKU lifecycle labels that may become permanent blockers.", "FORMULA_EXECUTION_ADAPTER_OR_INPUT_BINDING", regex=True),
    _term("R002", r"\b(no[-_ ]?trade).{0,40}(dominated|dominant|permanent|block|blocked)\b", "NO_TRADE_GLOBALIZATION_RISK", "HIGH", "Regex captures no-trade labels that may be mistaken for global blockers.", "NO_TRADE_ADVISED_FOR_THIS_CONTEXT_ONLY", regex=True),
    _term("R003", r"\b(repair).{0,40}(formula|qku|stack)\b", "FORMULA_REPAIR_SEMANTIC_RISK", "HIGH", "Regex captures repair routes that may imply canonical mutation.", "FORMULA_EXECUTION_ADAPTER_OR_INPUT_BINDING", regex=True),
    _term("R004", r"\b(global|permanent).{0,40}(negative|ban|blocked|no[-_ ]?trade)\b", "NEGATIVE_OUTCOME_GLOBALIZATION_RISK", "CRITICAL", "Regex captures global/permanent outcome semantics.", "CONDITION_SCOPED_NEGATIVE_OUTCOME_MEMORY", regex=True),
    _term("R005", r"\b(live|champion|source[-_ ]?truth).{0,40}(authority|ready|candidate|accepted)\b", "LIVE_OR_CHAMPION_AUTHORITY_RISK", "CRITICAL", "Regex captures authority/readiness labels future agents must not treat as operational truth.", "AUTHORITY_BOUNDARY_LABEL_ONLY", regex=True),
)

REPORT_NAMES = (
    "PR168_RP5A_Input.report.json",
    "PR168_RP5A_Preflight.report.json",
    "PR168_RP5A_TermTaxonomy.report.json",
    "PR168_RP5A_LegacyPRSemanticAudit.report.json",
    "PR168_RP5A_LegacyFileSemanticAudit.report.json",
    "PR168_RP5A_RowFieldSemanticHitIndex.report.json",
    "PR168_RP5A_WrongConceptTermIndex.report.json",
    "PR168_RP5A_ConsumerGraph.report.json",
    "PR168_RP5A_ValidationDependencyGraph.report.json",
    "PR168_RP5A_QKUFormulaIdentityDependency.report.json",
    "PR168_RP5A_IdentityCustodyGraph.report.json",
    "PR168_RP5A_AgentCrosswalkTouchpoints.report.json",
    "PR168_RP5A_NoOrphanAuditTouchpoints.report.json",
    "PR168_RP5A_StaleSemanticBlastRadius.report.json",
    "PR168_RP5A_ValidationTimeRisk.report.json",
    "PR168_RP5A_DeleteEligibilityDraft.report.json",
    "PR168_RP5A_CrossGraphConsistency.report.json",
    "PR168_RP5A_NoDeletionProof.report.json",
    "PR168_RP5A_FutureRP5BPlan.report.json",
    "PR168_RP5A_PathAudit.report.json",
    "PR168_RP5A_ScanPerformance.report.json",
    "PR168_RP5A_FinalSummary.report.json",
)

ROW_SHARDS = {
    "input_rows": "input_rows.jsonl",
    "term_taxonomy_rows": "term_taxonomy_rows.jsonl",
    "legacy_pr_semantic_rows": "legacy_pr_semantic_rows.jsonl",
    "legacy_file_semantic_rows": "legacy_file_semantic_rows.jsonl",
    "row_field_semantic_hit_rows": "row_field_semantic_hit_rows.jsonl",
    "wrong_concept_term_rows": "wrong_concept_term_rows.jsonl",
    "consumer_graph_rows": "consumer_graph_rows.jsonl",
    "validation_dependency_rows": "validation_dependency_rows.jsonl",
    "qku_formula_identity_dependency_rows": "qku_formula_identity_dependency_rows.jsonl",
    "identity_custody_rows": "identity_custody_rows.jsonl",
    "agent_touchpoint_rows": "agent_touchpoint_rows.jsonl",
    "blast_radius_rows": "blast_radius_rows.jsonl",
    "validation_time_risk_rows": "validation_time_risk_rows.jsonl",
    "delete_eligibility_rows": "delete_eligibility_rows.jsonl",
    "future_rp5b_plan_rows": "future_rp5b_plan_rows.jsonl",
}


def normalize_repo_path(path: str | Path) -> str:
    text = str(path).replace("\\", "/")
    while text.startswith("./"):
        text = text[2:]
    return text


def report_path(name: str) -> Path:
    return GENERATED_ROOT / name


def shard_path(key: str) -> Path:
    return SHARD_ROOT / ROW_SHARDS[key]


def manifest_path_for_shard(path: Path) -> Path:
    return path.with_name(path.stem + ".manifest.json")


def generated_ref(path: str | Path) -> str:
    path_obj = Path(path)
    try:
        return normalize_repo_path(path_obj.relative_to(REPO_ROOT))
    except ValueError:
        return normalize_repo_path(path_obj)


def is_owned_rp5a_path(path: str | Path) -> bool:
    normalized = normalize_repo_path(path)
    return (
        normalized.startswith("docs/master_plan/generated/PR168_RP5A_")
        or normalized.startswith("docs/master_plan/generated/rp5a/")
        or normalized.startswith("tests/pr168_rp5a/")
        or normalized.startswith("tools/pr168_rp5a_")
        or normalized
        in {
            "tools/build_pr168_rp5a_legacy_semantic_audit.py",
            "tools/validate_pr168_rp5a_legacy_semantic_audit.py",
        }
    )


def should_scan_path(path: str | Path) -> bool:
    normalized = normalize_repo_path(path)
    if normalized in SCAN_EXCLUDED_EXACT:
        return False
    if any(normalized.startswith(prefix) for prefix in SCAN_EXCLUDED_PREFIXES):
        return False
    if any(normalized.startswith(prefix) for prefix in SCAN_EXCLUDED_NAME_PREFIXES):
        return False
    suffix = Path(normalized).suffix.lower()
    return suffix in TEXT_EXTENSIONS


def classify_file_kind(path: str | Path) -> str:
    normalized = normalize_repo_path(path)
    name = Path(normalized).name
    lower = normalized.lower()
    if "currentization" in lower or "currentize" in lower:
        return FILE_KIND_CURRENTIZATION
    if normalized.startswith("docs/master_plan/generated/"):
        if name.endswith(".manifest.json"):
            return FILE_KIND_MANIFEST
        if name.endswith(".jsonl"):
            return FILE_KIND_GENERATED_SHARD
        if name.endswith(".report.json") or name.endswith(".json"):
            return FILE_KIND_GENERATED_REPORT
    if normalized.startswith("tools/"):
        if name.startswith("validate_") or "validation" in name or name == "run_validation_gates.py":
            return FILE_KIND_VALIDATOR
        return FILE_KIND_TOOL_SOURCE
    if normalized.startswith("tests/"):
        return FILE_KIND_TEST_SOURCE
    if normalized.startswith("docs/") or name.endswith(".md"):
        return FILE_KIND_DOC
    return FILE_KIND_UNKNOWN


def severity_rank(severity: str) -> int:
    return {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}.get(severity, 0)


def semantic_risk_level(severities: list[str]) -> str:
    if not severities:
        return "LOW"
    max_rank = max(severity_rank(value) for value in severities)
    return {1: "LOW", 2: "MEDIUM", 3: "HIGH", 4: "CRITICAL"}[max_rank]


IDENTITY_REGEXES = {
    "QKU_ID": re.compile(r"\bQKU[-_:A-Z0-9]{8,}\b", re.IGNORECASE),
    "FORMULA_ID": re.compile(r"\b(?:FORMULA|QTT_FORMULA|PR\d+_[A-Z0-9_]*FORMULA)[-_:A-Z0-9]{4,}\b", re.IGNORECASE),
    "FORMULA_VARIANT_ID": re.compile(r"\b(?:formula_variant_id|FORMULA_VARIANT[-_:A-Z0-9]{4,})\b", re.IGNORECASE),
    "PLUGIN_CONTRACT": re.compile(r"\b(?:plugin_contract|FormulaPluginContract|plugin_id)\b", re.IGNORECASE),
    "FORMULA_TO_PNL": re.compile(r"\bFormulaToPnL\b|\bformula_to_pnl\b", re.IGNORECASE),
    "FORMULA_EXPRESSION": re.compile(r"\bformula_expression(?:_ref)?\b|\bexpression_repair\b", re.IGNORECASE),
    "QUANTUM_OBJECTIVE": re.compile(r"\b(?:QUBO|BQM|CQM|Ising|QuadraticProgram|quantum_objective|objective_quadratic_terms)\b", re.IGNORECASE),
    "AGENT_OWNER": re.compile(r"\b(?:owning_agent|agent_duty_ref|consumer_agents|downstream_consumers)\b", re.IGNORECASE),
}


AGENT_TOUCHPOINT_REGEX = re.compile(
    r"\b(?:agent|owning_agent|consumer_agents|downstream_consumer|downstream_consumers|"
    r"AgentDutySourceCrosswalk|AgentRosterDiscoveryAudit|PR165[_-]D2|no_orphan|handoff|duty_ref)\b",
    re.IGNORECASE,
)
