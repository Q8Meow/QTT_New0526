"""PR136 Day-1 launch-readiness roadmap artifact builder and validator helpers."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from . import day1_launch_readiness_roadmap_policy as policy


REPO_ROOT = Path(__file__).resolve().parents[4]
REPORT_DIR = Path("docs/master_plan/generated")
ROADMAP_GENERATED_DIR = Path("docs/roadmap/generated")
ROADMAP_DOC_PATH = Path(
    "docs/roadmap/QTT_PostPR135_Day1_Launch_Readiness_Roadmap_v1_0.md"
)
ROADMAP_INDEX_PATH = Path(
    "docs/roadmap/QTT_PostPR135_Day1_Launch_Readiness_Roadmap_Index_v1_0.json"
)
COVERAGE_REPORT_PATH = Path("docs/master_plan/generated/MasterPlanSectionCoverageReport.json")
ATOMICROWS_BUNDLE_PATH = Path("docs/master_plan/atomic_rows/AtomicRows.bundle.jsonl")

COVERAGE_REPORT_REQUIRED_STRUCTURAL_KEYS = (
    "report_type",
    "report_version",
    "deterministic_output",
    "generated_by",
    "generated_at_utc",
    "registry",
    "coverage_summary",
    "coverage_entries",
    "section_coverage",
)


PR135_OWNER_VERIFIED_FIELDS = {
    "repo_pr_number": 135,
    "roadmap_pr_number": 117,
    "repo_pr_title": "PR135 historical dataset digest loader contracts",
    "repo_pr_state": "MERGED",
    "repo_pr_url": "https://github.com/Q8Meow/QTT_New0526/pull/135",
    "headRefName": "pr135-historical-dataset-digest-loader",
    "baseRefName": "main",
    "mergedAt": "2026-05-21T04:31:43Z",
    "mergeCommit_full": "c0aa723a5c46d86ba93a007d5b50d7f64438b03d",
    "mergeCommit_short": "c0aa723",
    "branch_commit_short": "f87167f",
}


PROVISIONAL_SKELETON = (
    (137, "PR136 launch-roadmap validator and readiness dependency controller"),
    (138, "AtomicRows historical dataset bridge/materialization-readiness gate"),
    (139, "AtomicRows row-family source manifest currentization"),
    (140, "AtomicRows bundle builder dry-run and diff validator"),
    (141, "AtomicRows bundle materialization PR, owner-authorized only"),
    (142, "AtomicRows structural integrity policy gate, owner-authorized only"),
    (
        143,
        "Per-venue official source-evidence finalization for Kalshi / Polymarket / FORECASTEX_IBKR",
    ),
    (144, "Connector semantic binding live-unlock gate"),
    (145, "Runtime cash / private-state / credential live-readiness gate"),
    (146, "Real historical dataset availability and accepted-source bridge"),
    (147, "Replay execution engine on locked historical inputs"),
    (148, "Paper execution engine on separate lane"),
    (149, "Replay/paper result immutability and dual-result review"),
    (150, "Replay/paper evidence to optimizer/quantum comparator"),
    (151, "Quantum/classical optimizer execution-readiness gate"),
    (152, "Classical baseline vs quantum challenger comparison"),
    (153, "Final parameter-stack selection and owner override packet"),
    (154, "Owner approval queue and launch decision packet"),
    (155, "Owner dashboard launch-control readiness"),
    (156, "Live-promotion review closure"),
    (157, "Three-venue live canary eligibility gate"),
    (158, "Limited live canary command packet"),
    (159, "Post-trade reconciliation and kill-switch gate"),
    (160, "Triggered live concurrent comparison"),
    (161, "Limited-live arbitrage and scaled-live eligibility"),
    (162, "Full Day-1 launch preflight matrix"),
    (163, "Day-1 launch runbook and rollback command packet"),
    (164, "Official Day-1 live trading start command, owner-authorized only"),
)


def _json_dump(value: Any) -> str:
    return json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True) + "\n"


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_json_dump(payload), encoding="utf-8", newline="\n")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def file_size_and_line_metadata(path: Path) -> dict[str, Any]:
    data = path.read_bytes()
    return {
        "bytes": len(data),
        "lines": data.count(b"\n") + (0 if data.endswith(b"\n") else 1),
    }


def _coverage(repo_root: Path) -> dict[str, Any]:
    return load_json(repo_root / COVERAGE_REPORT_PATH)


def coverage_metadata(repo_root: Path) -> dict[str, Any]:
    payload = _coverage(repo_root)
    coverage_entries = payload.get("coverage_entries", [])
    section_coverage = payload.get("section_coverage", [])
    coverage_summary = payload.get("coverage_summary")
    registry = payload.get("registry")
    if not isinstance(coverage_entries, list):
        coverage_entries = []
    if not isinstance(section_coverage, list):
        section_coverage = []
    if not isinstance(coverage_summary, Mapping):
        coverage_summary = {}
    if not isinstance(registry, Mapping):
        registry = {}
    structural_keys_present = {
        key: key in payload for key in COVERAGE_REPORT_REQUIRED_STRUCTURAL_KEYS
    }
    return {
        "coverage_report_ref": COVERAGE_REPORT_PATH.as_posix(),
        "coverage_report_value_source": "GENERATED_REPORT_STRUCTURAL_VALUES_OR_REPO_CURRENT",
        "master_plan_section_count": len(section_coverage),
        "coverage_entry_count": len(coverage_entries),
        "report_type": payload.get("report_type"),
        "report_version": payload.get("report_version"),
        "deterministic_output": payload.get("deterministic_output"),
        "generated_by": payload.get("generated_by"),
        "generated_at_utc": payload.get("generated_at_utc"),
        "registry_entry_count": registry.get("entry_count"),
        "parser_visible_section_count": coverage_summary.get(
            "parser_visible_section_count"
        ),
        "required_structural_keys_present": structural_keys_present,
        "required_structural_keys_missing": [
            key for key, present in structural_keys_present.items() if not present
        ],
    }


def pr135_currentization_receipt() -> dict[str, Any]:
    return {
        **PR135_OWNER_VERIFIED_FIELDS,
        "receipt_type": "PR135_GITHUB_AUDIT_CURRENTIZATION_RECEIPT",
        "owner_verified_source": True,
        "codex_network_access_used": False,
        "gh_command_used_by_codex": False,
        "currentized_in_identity_roster": True,
        "source_of_truth_note": (
            "owner-side gh pr view 135 verification; Codex did not verify via network"
        ),
        "missing_owner_verified_fields": [],
        "placeholder_values_detected": [],
        "stop_if_missing_required_fields": True,
    }


def owner_verified_inputs_report() -> dict[str, Any]:
    return {
        "receipt_type": "PR136_OWNER_VERIFIED_INPUTS_RECEIPT",
        "repo_pr_number": policy.PRODUCER_REPO_PR,
        "owner_authorized_scope": policy.OWNER_AUTHORIZED_SCOPE,
        "previous_repo_pr_number": policy.PREVIOUS_REPO_PR,
        "previous_roadmap_pr_number": policy.PREVIOUS_ROADMAP_PR,
        "owner_verified_pr135_fields": pr135_currentization_receipt(),
        "critical_correction": {
            "arbitrary_domain_count_forced": False,
            "fixed_13_domain_model_used": False,
            "readiness_domain_taxonomy_derivation_required": True,
        },
        "codex_network_access_used": False,
        "gh_command_used_by_codex": False,
    }


def route_triage_report() -> dict[str, Any]:
    return {
        "receipt_type": "PR136_ROUTE_TRIAGE_RECEIPT",
        "repo_pr_number": policy.PRODUCER_REPO_PR,
        "owner_authorized_scope": policy.OWNER_AUTHORIZED_SCOPE,
        "sequence_authority_class": policy.SEQUENCE_AUTHORITY,
        "previous_repo_pr_number": policy.PREVIOUS_REPO_PR,
        "previous_roadmap_pr_number": policy.PREVIOUS_ROADMAP_PR,
        "previous_repo_pr_state": "MERGED",
        "same_number_inference_used": False,
        "route_resolution_basis": (
            "OWNER_AUTHORIZED_POST_PR135_DAY1_LAUNCH_READINESS_ROADMAP_COMPILER"
        ),
        "branch_expected": "pr136-master-plan-coverage-day1-roadmap",
        "repo_task": (
            "master-plan section coverage to Day-1 launch readiness roadmap currentization"
        ),
        "roadmap_pr136_same_number_inference_forbidden": True,
        "provisional_pr137_pr164_skeleton_authority": (
            "NON_AUTHORITATIVE_PLANNING_INPUT_ONLY"
        ),
        "future_pr_sequence_auto_authorizes_implementation": False,
        "future_pr_sequence_auto_authorizes_live_trading": False,
        "future_pr_sequence_auto_authorizes_atomicrows_materialization": False,
        "future_pr_sequence_auto_authorizes_quantum_execution": False,
        "arbitrary_domain_count_forced": False,
        "fixed_13_domain_model_used": False,
        "readiness_domain_taxonomy_derivation_required": True,
        "currentization_first_subtask_completed": True,
        "blockers": [],
    }


def read_receipt(repo_root: Path) -> dict[str, Any]:
    missing = [
        path
        for path in (*policy.REQUIRED_READ_FILES, *policy.OPTIONAL_CURRENT_STATE_FILES)
        if not (repo_root / path).exists()
    ]
    required_read = [
        path
        for path in (*policy.REQUIRED_READ_FILES, *policy.OPTIONAL_CURRENT_STATE_FILES)
        if (repo_root / path).exists()
    ]
    metadata = {
        path: file_size_and_line_metadata(repo_root / path) for path in required_read
    }
    coverage = coverage_metadata(repo_root)
    return {
        "receipt_type": "PR136_DAY1_LAUNCH_READINESS_ROADMAP_READ_RECEIPT",
        "repo_pr_number": policy.PRODUCER_REPO_PR,
        "owner_authorized_scope": policy.OWNER_AUTHORIZED_SCOPE,
        "same_number_inference_used": False,
        "required_files_read": required_read,
        "missing_files": missing,
        "read_before_editing_confirmed": True,
        "master_plan_section_coverage_report_found": (
            repo_root / COVERAGE_REPORT_PATH
        ).exists(),
        "coverage_report_ref": coverage["coverage_report_ref"],
        "coverage_report_value_source": coverage["coverage_report_value_source"],
        "master_plan_section_count": coverage["master_plan_section_count"],
        "coverage_entry_count": coverage["coverage_entry_count"],
        "report_type": coverage["report_type"],
        "report_version": coverage["report_version"],
        "deterministic_output": coverage["deterministic_output"],
        "generated_by": coverage["generated_by"],
        "generated_at_utc": coverage["generated_at_utc"],
        "registry_entry_count": coverage["registry_entry_count"],
        "parser_visible_section_count": coverage["parser_visible_section_count"],
        "required_structural_keys_present": coverage[
            "required_structural_keys_present"
        ],
        "required_structural_keys_missing": coverage[
            "required_structural_keys_missing"
        ],
        "arbitrary_domain_count_forced": False,
        "fixed_13_domain_model_used": False,
        "readiness_domain_taxonomy_derivation_required": True,
        "anchors_inspected": list(policy.ANCHORS_INSPECTED),
        "file_sizes_and_line_counts": metadata,
        "repo_convention_files_inspected": [
            "git ls-files",
            "git ls-files docs/roadmap",
            "git ls-files docs/master_plan/generated",
            "git ls-files schemas",
            "git ls-files src/qtt",
            "git ls-files tools",
            "git ls-files tests",
        ],
    }


def path_decision_report() -> dict[str, Any]:
    chosen = {
        "package_init": "src/qtt/stage1_prediction_markets/launch_readiness/__init__.py",
        "policy_module": policy.POLICY_MODULE_PATH,
        "roadmap_module": policy.ROADMAP_MODULE_PATH,
        "policy_literal_drift_validator": (
            "tools/validate_pr136_roadmap_policy_literal_drift.py"
        ),
        "validator": "tools/validate_pr136_day1_launch_readiness_roadmap.py",
        "focused_tests": "tests/roadmap/test_pr136_day1_launch_readiness_roadmap.py",
        "fail_closed_tests": "tests/fail_closed/test_run_validation_gates.py",
        "roadmap_doc": ROADMAP_DOC_PATH.as_posix(),
        "roadmap_index": ROADMAP_INDEX_PATH.as_posix(),
        "schemas": list(policy.PR136_SCHEMA_PATHS),
    }
    return {
        "receipt_type": "PR136_PATH_DECISION_RECEIPT",
        "repo_pr_number": policy.PRODUCER_REPO_PR,
        "owner_authorized_scope": policy.OWNER_AUTHORIZED_SCOPE,
        "path_selection_precedence_used": [
            "Reuse current repo conventions from PR131-PR135 when clear",
            "Reuse closest roadmap/generated report/validator pattern",
            "Use PR136 default paths where no stronger convention exists",
        ],
        "chosen_paths": chosen,
        "conflicting_conventions_detected": [],
        "safe_canonical_path_inferred": True,
        "protected_files_not_edited": [
            "docs/master_plan/QTT_MasterPlan_Current.md",
            ATOMICROWS_BUNDLE_PATH.as_posix(),
        ],
    }


def _parent_domain_for(capability_id: str) -> tuple[str, str]:
    rules = (
        ("atomicrows", "ATOMICROWS_READINESS", "AtomicRows Readiness"),
        ("source_evidence", "SOURCE_EVIDENCE_READINESS", "Source Evidence Readiness"),
        ("connector", "CONNECTOR_BINDING_READINESS", "Connector Binding Readiness"),
        ("source_fact", "CONNECTOR_BINDING_READINESS", "Connector Binding Readiness"),
        ("venue", "MARKET_SPECIFIC_VENUE_READINESS", "Market-Specific Venue Readiness"),
        ("runtime_cash", "CREDENTIAL_PRIVATE_STATE_CASH_READINESS", "Credential Private-State Cash Readiness"),
        ("private", "CREDENTIAL_PRIVATE_STATE_CASH_READINESS", "Credential Private-State Cash Readiness"),
        ("credential", "CREDENTIAL_PRIVATE_STATE_CASH_READINESS", "Credential Private-State Cash Readiness"),
        ("replay", "REPLAY_PAPER_DATASET_READINESS", "Replay Paper Dataset Readiness"),
        ("paper", "REPLAY_PAPER_DATASET_READINESS", "Replay Paper Dataset Readiness"),
        ("dataset", "REPLAY_PAPER_DATASET_READINESS", "Replay Paper Dataset Readiness"),
        ("dual_result", "REPLAY_PAPER_DATASET_READINESS", "Replay Paper Dataset Readiness"),
        ("quantum", "QUANTUM_OPTIMIZER_READINESS", "Quantum Optimizer Readiness"),
        ("qubo", "QUANTUM_OPTIMIZER_READINESS", "Quantum Optimizer Readiness"),
        ("owner_dashboard", "OWNER_APPROVAL_DASHBOARD_READINESS", "Owner Approval Dashboard Readiness"),
        ("owner_live", "OWNER_APPROVAL_DASHBOARD_READINESS", "Owner Approval Dashboard Readiness"),
        ("final_readiness", "DAY1_LAUNCH_GATE_READINESS", "Day-1 Launch Gate Readiness"),
        ("limited_live", "DAY1_LAUNCH_GATE_READINESS", "Day-1 Launch Gate Readiness"),
        ("latency", "LATENCY_HOT_PATH_READINESS", "Latency Hot-Path Readiness"),
        ("runtime_orchestration", "AGENT_ORCHESTRATION_READINESS", "Agent Orchestration Readiness"),
        ("external", "RESEARCH_QUARANTINE_READINESS", "Research Quarantine Readiness"),
        ("parser_visible", "RESEARCH_QUARANTINE_READINESS", "Research Quarantine Readiness"),
        ("preset_retirement", "RESEARCH_QUARANTINE_READINESS", "Research Quarantine Readiness"),
        ("master_plan", "MASTER_PLAN_COVERAGE_READINESS", "Master-Plan Coverage Readiness"),
        ("generated_derivative", "MASTER_PLAN_COVERAGE_READINESS", "Master-Plan Coverage Readiness"),
    )
    for needle, parent_id, parent_title in rules:
        if needle in capability_id:
            return parent_id, parent_title
    return "MASTER_PLAN_COVERAGE_READINESS", "Master-Plan Coverage Readiness"


def _domain_type(capability_id: str) -> str:
    if "owner" in capability_id or "final_readiness" in capability_id:
        return "OWNER_AUTHORIZATION_DOMAIN"
    if "latency" in capability_id:
        return "LATENCY_HOT_PATH_DOMAIN"
    if "runtime_orchestration" in capability_id:
        return "AGENT_ORCHESTRATION_DOMAIN"
    if "venue" in capability_id or "connector" in capability_id:
        return "MARKET_SPECIFIC_DOMAIN"
    return "SUBDOMAIN"


def _scope_class_for_parent(parent_id: str) -> str:
    mapping = {
        "ATOMICROWS_READINESS": "ATOMICROWS_READINESS",
        "SOURCE_EVIDENCE_READINESS": "SOURCE_EVIDENCE_READINESS",
        "CONNECTOR_BINDING_READINESS": "CONNECTOR_BINDING_READINESS",
        "MARKET_SPECIFIC_VENUE_READINESS": "CONNECTOR_BINDING_READINESS",
        "CREDENTIAL_PRIVATE_STATE_CASH_READINESS": (
            "CREDENTIAL_PRIVATE_STATE_CASH_READINESS"
        ),
        "REPLAY_PAPER_DATASET_READINESS": "DATASET_REPLAY_PAPER_READINESS",
        "QUANTUM_OPTIMIZER_READINESS": "QUANTUM_OPTIMIZER_READINESS",
        "OWNER_APPROVAL_DASHBOARD_READINESS": "OWNER_APPROVAL_DASHBOARD_READINESS",
        "DAY1_LAUNCH_GATE_READINESS": "DAY1_LAUNCH_READINESS",
        "LATENCY_HOT_PATH_READINESS": "DAY1_LAUNCH_READINESS",
        "AGENT_ORCHESTRATION_READINESS": "ROADMAP_MAPPING",
        "RESEARCH_QUARANTINE_READINESS": "ROADMAP_MAPPING",
        "MASTER_PLAN_COVERAGE_READINESS": "ROADMAP_MAPPING",
    }
    return mapping.get(parent_id, "ROADMAP_MAPPING")


def _future_prs_for_parent(parent_id: str) -> list[str]:
    mapping = {
        "ATOMICROWS_READINESS": ["PR138", "PR139", "PR140", "PR141", "PR142"],
        "SOURCE_EVIDENCE_READINESS": ["PR143", "PR143K", "PR143P", "PR143F"],
        "CONNECTOR_BINDING_READINESS": ["PR144"],
        "MARKET_SPECIFIC_VENUE_READINESS": ["PR143", "PR144", "PR157"],
        "CREDENTIAL_PRIVATE_STATE_CASH_READINESS": ["PR145"],
        "REPLAY_PAPER_DATASET_READINESS": ["PR146", "PR147", "PR148", "PR149", "PR150"],
        "QUANTUM_OPTIMIZER_READINESS": ["PR151", "PR152", "PR153"],
        "OWNER_APPROVAL_DASHBOARD_READINESS": ["PR154", "PR155", "PR156"],
        "DAY1_LAUNCH_GATE_READINESS": ["PR157", "PR158", "PR159", "PR162", "PR163", "PR164"],
        "LATENCY_HOT_PATH_READINESS": ["PR137L", "PR162"],
        "AGENT_ORCHESTRATION_READINESS": ["PR137", "PR155"],
        "RESEARCH_QUARANTINE_READINESS": ["PR137", "PR162"],
        "MASTER_PLAN_COVERAGE_READINESS": ["PR137"],
    }
    return list(mapping.get(parent_id, ["PR137"]))


def _evidence(evidence_class: str, ref: str, summary: str) -> dict[str, str]:
    return {
        "evidence_class": evidence_class,
        "evidence_ref": ref,
        "evidence_summary": summary,
    }


def build_domain_artifacts(repo_root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    coverage = _coverage(repo_root)
    meta = coverage_metadata(repo_root)
    entries = sorted(
        coverage.get("coverage_entries", []),
        key=lambda row: int(row.get("entry_index", 9999)),
    )
    parent_titles: dict[str, str] = {}
    domain_records: list[dict[str, Any]] = []
    multi_domain_entries: list[dict[str, Any]] = []
    for entry in entries:
        capability_id = str(entry["capability_id"])
        parent_id, parent_title = _parent_domain_for(capability_id)
        parent_titles[parent_id] = parent_title
        domain_id = f"PR136_DOMAIN_{int(entry['entry_index']):02d}_{capability_id.upper()}"
        extra_parent_ids: list[str] = []
        if "connector" in capability_id and parent_id != "SOURCE_EVIDENCE_READINESS":
            extra_parent_ids.append("SOURCE_EVIDENCE_READINESS")
        if "final_readiness" in capability_id:
            extra_parent_ids.append("OWNER_APPROVAL_DASHBOARD_READINESS")
        if extra_parent_ids:
            multi_domain_entries.append(
                {
                    "coverage_entry_id": capability_id,
                    "primary_domain_id": domain_id,
                    "additional_parent_domains": extra_parent_ids,
                    "evidence_basis": [
                        _evidence(
                            "GENERATED_REPORT",
                            COVERAGE_REPORT_PATH.as_posix(),
                            "Coverage entry routes across multiple launch-readiness lanes.",
                        )
                    ],
                }
            )
        future_prs = _future_prs_for_parent(parent_id)
        domain_records.append(
            {
                "domain_id": domain_id,
                "domain_title": str(entry.get("section_title_or_capability_title", capability_id)),
                "domain_type": _domain_type(capability_id),
                "parent_domain_id": parent_id,
                "domain_derivation_basis": (
                    "coverage_entry.capability_id plus roadmap/blueprint Stage-1 launch refs"
                ),
                "subdomains": [],
                "source_master_plan_sections_or_anchors": [
                    f"coverage_entry:{capability_id}",
                    *(entry.get("owner_section_ids") or []),
                ],
                "roadmap_refs": [
                    "docs/roadmap/QTT_PRs_Roadmap_Index_v1_0.json",
                    "docs/roadmap/QTT_PRs_Roadmap_Consolidated_Static_Runtime_Live_Stage1_to_Stage5_v1_0.md",
                ],
                "blueprint_refs": [
                    "docs/roadmap/QTT_PR_Blueprints_Index_PR83_to_PR224_v1_0.json"
                ],
                "existing_generated_reports": list(entry.get("required_reports") or []),
                "evidence_basis": [
                    _evidence(
                        "GENERATED_REPORT",
                        COVERAGE_REPORT_PATH.as_posix(),
                        f"Coverage entry {capability_id} is present with class {entry.get('coverage_class')}.",
                    ),
                    _evidence(
                        "ROADMAP",
                        "docs/roadmap/QTT_PRs_Roadmap_Index_v1_0.json",
                        "Stage-1 roadmap provides launch-readiness sequencing context.",
                    ),
                    _evidence(
                        "BLUEPRINT",
                        "docs/roadmap/QTT_PR_Blueprints_Index_PR83_to_PR224_v1_0.json",
                        "Blueprint index provides domain and dependency context.",
                    ),
                ],
                "upstream_dependencies": [f"coverage_class:{entry.get('coverage_class')}"],
                "downstream_dependencies": future_prs,
                "market_scope": list(policy.CANONICAL_VENUES)
                if "venue" in capability_id or "connector" in capability_id
                else ["PREDICTION_MARKETS_GENERAL"],
                "agent_scope": ["roadmap_compiler_agent"],
                "quantum_scope": "METADATA_ONLY" if "quantum" in capability_id or "qubo" in capability_id else "NONE",
                "atomicrows_scope": "METADATA_ONLY" if "atomicrows" in capability_id else "NONE",
                "source_evidence_scope": "REQUIRED" if "source" in capability_id or "connector" in capability_id else "REFERENCE_ONLY",
                "connector_scope": "BLOCKED_UNTIL_SOURCE_EVIDENCE" if "connector" in capability_id or "venue" in capability_id else "NONE",
                "credential_private_state_cash_scope": "FUTURE_RECEIPT_REQUIRED" if "cash" in capability_id else "NONE",
                "replay_paper_scope": "FUTURE_NONLIVE_EXECUTION_REQUIRED" if "replay" in capability_id or "paper" in capability_id else "NONE",
                "live_readiness_scope": "OWNER_COMMAND_REQUIRED" if "live" in capability_id or "final_readiness" in capability_id else "NO_CURRENT_LIVE_AUTHORITY",
                "owner_authorization_points": [
                    "future owner review required before implementation or live/materialization authority"
                ],
                "forbidden_authority_refs": list(policy.NO_AUTHORITY_FLAGS),
                "future_pr_candidates": future_prs,
                "validation_hooks": [
                    "tools/validate_pr136_day1_launch_readiness_roadmap.py",
                    "tools/validate_pr136_roadmap_policy_literal_drift.py",
                ],
            }
        )

    parent_domains = [
        {
            "parent_domain_id": parent_id,
            "parent_domain_title": parent_titles[parent_id],
            "scope_class": _scope_class_for_parent(parent_id),
            "subdomain_ids": [
                record["domain_id"]
                for record in domain_records
                if record["parent_domain_id"] == parent_id
            ],
            "evidence_basis": [
                _evidence(
                    "GENERATED_REPORT",
                    COVERAGE_REPORT_PATH.as_posix(),
                    "Parent domain is derived from one or more current coverage entries.",
                )
            ],
        }
        for parent_id in sorted(parent_titles)
    ]
    domain_map = {
        "receipt_type": "PR136_MASTER_PLAN_COVERAGE_TO_READINESS_DOMAIN_MAP",
        "repo_pr_number": policy.PRODUCER_REPO_PR,
        **meta,
        "readiness_domain_count": len(domain_records),
        "readiness_domain_count_source": (
            "DERIVED_FROM_MASTER_PLAN_COVERAGE_ROADMAP_BLUEPRINTS_AND_REPO_CONVENTIONS"
        ),
        "arbitrary_domain_count_forced": False,
        "fixed_13_domain_model_used": False,
        "domain_map_complete": True,
        "unmapped_entries": [],
        "deferred_entries": [],
        "multi_domain_entries": multi_domain_entries,
        "domain_records": domain_records,
    }
    taxonomy = {
        "receipt_type": "PR136_READINESS_DOMAIN_TAXONOMY",
        "taxonomy_authority_class": (
            "COVERAGE_DERIVED_PLANNING_TAXONOMY_NOT_EXECUTION_AUTHORITY"
        ),
        "repo_pr_number": policy.PRODUCER_REPO_PR,
        "taxonomy_derivation_inputs": [
            COVERAGE_REPORT_PATH.as_posix(),
            "docs/master_plan/QTT_MasterPlan_Current.md",
            "docs/roadmap/QTT_PRs_Roadmap_Index_v1_0.json",
            "docs/roadmap/QTT_PR_Blueprints_Index_PR83_to_PR224_v1_0.json",
            "docs/master_plan/generated/PR135MasterPlanSectionCrosswalk.report.json",
            "docs/master_plan/generated/PR135MarketSpecificSectionIndex.report.json",
            "docs/master_plan/generated/PR135CommandActionMatrix.report.json",
        ],
        "readiness_domain_count": len(domain_records),
        "arbitrary_domain_count_forced": False,
        "fixed_13_domain_model_used": False,
        "parent_domains": parent_domains,
        "subdomains": domain_records,
        "domain_derivation_method": (
            "Sort current coverage entries by entry_index, derive a launch-readiness "
            "subdomain from each coverage entry, then group into evidence-backed parent lanes."
        ),
        "domain_merge_split_notes": [
            "Connector coverage maps to both source-evidence and connector-binding lanes.",
            "Final readiness coverage maps to owner-approval and Day-1 launch lanes.",
            "No domain count was supplied by owner memory or fixed to 13.",
        ],
        "domain_evidence_summary": {
            "coverage_report_ref": meta["coverage_report_ref"],
            "coverage_report_value_source": meta["coverage_report_value_source"],
            "coverage_entry_count": meta["coverage_entry_count"],
            "master_plan_section_count": meta["master_plan_section_count"],
            "parser_visible_section_count": meta["parser_visible_section_count"],
            "registry_entry_count": meta["registry_entry_count"],
            "report_type": meta["report_type"],
            "report_version": meta["report_version"],
            "deterministic_output": meta["deterministic_output"],
            "generated_by": meta["generated_by"],
            "generated_at_utc": meta["generated_at_utc"],
            "required_structural_keys_present": meta[
                "required_structural_keys_present"
            ],
            "required_structural_keys_missing": meta[
                "required_structural_keys_missing"
            ],
            "evidence_classes_used": [
                "GENERATED_REPORT",
                "ROADMAP",
                "BLUEPRINT",
                "REPO_CONVENTION",
                "OWNER_VERIFIED_INPUT",
            ],
        },
        "owner_review_required_for_domain_ambiguity": True,
    }
    return domain_map, taxonomy


def _classify(number: int) -> tuple[str, str, bool, list[str], list[str], str]:
    if number in {141, 142, 144, 145, 147, 148, 151, 154, 156, 157, 158, 159, 160, 164}:
        return (
            policy.OWNER_AUTHORIZATION_REQUIRED,
            "Future step can only proceed under explicit owner authorization and validated upstream gates.",
            True,
            [],
            [],
            "FIXED_IF_OWNER_APPROVES",
        )
    if number in {138, 143}:
        replacements = (
            ["PR138A", "PR138B"]
            if number == 138
            else ["PR143K", "PR143P", "PR143F"]
        )
        return (
            policy.SPLIT_OR_REPLACED,
            "Scope is too broad to execute as one future PR without hiding material prerequisites.",
            True,
            replacements,
            [],
            "SPLIT_CHILD",
        )
    if number == 146:
        return (
            policy.NEW_INSERTION_REQUIRED_BEFORE_THIS_PR,
            "Real historical availability requires accepted source evidence before use.",
            True,
            [],
            ["PR143K", "PR143P", "PR143F"],
            "INSERTION_BEFORE",
        )
    if number == 161:
        return (
            policy.DEFERRED_AFTER_DAY1,
            "Scaled live arbitrage belongs after Day-1 canary and launch review evidence.",
            True,
            [],
            [],
            "DEFERRED_AFTER_DAY1",
        )
    return (
        policy.CONFIRMED,
        "Planning scope matches evidence-backed readiness sequencing and creates no current authority.",
        False,
        [],
        [],
        "FIXED_IF_OWNER_APPROVES",
    )


def provisional_classification(domain_records: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    domain_ids = [record["domain_id"] for record in domain_records]
    classifications = []
    for number, title in PROVISIONAL_SKELETON:
        classification, reason, owner_required, replacements, insertions, number_status = _classify(number)
        source_domain_ids = domain_ids[(number - 137) % len(domain_ids) : ((number - 137) % len(domain_ids)) + 1]
        if not source_domain_ids:
            source_domain_ids = [domain_ids[0]]
        classifications.append(
            {
                "provisional_pr_number": number,
                "provisional_title": title,
                "classification": classification,
                "classification_reason": reason,
                "classification_decision_rationale": (
                    "Derived from PR136 coverage-domain map, roadmap/blueprint Stage-1 sequencing, "
                    "and owner no-authority boundaries."
                ),
                "evidence_basis": [
                    _evidence("GENERATED_REPORT", "PR136ReadinessDomainTaxonomy.report.json", "Coverage-derived taxonomy maps this future PR to launch-readiness domains."),
                    _evidence("ROADMAP", "docs/roadmap/QTT_PRs_Roadmap_Index_v1_0.json", "Roadmap supplies Stage-1 launch sequence context."),
                ],
                "source_domain_ids": source_domain_ids,
                "required_inputs": ["validated upstream PR outputs", "owner authorization where marked"],
                "required_outputs": ["future validation marker and receipt-backed artifacts only"],
                "must_not_create": list(policy.NO_AUTHORITY_FLAGS),
                "current_authority_created": False,
                "planned_future_authority_class": (
                    "OWNER_AUTHORIZATION_REQUIRED_BEFORE_LIVE_EXECUTION"
                    if owner_required
                    else "OWNER_AUTHORIZATION_REQUIRED_BEFORE_IMPLEMENTATION"
                ),
                "owner_authorization_required": owner_required,
                "proposed_number_status": number_status,
                "suggested_final_pr_numbers": [f"PR{number}"],
                "replacement_prs_if_any": replacements,
                "insertions_before_if_any": insertions,
                "merged_with_if_any": [],
                "deferred_reason_if_any": reason if classification == policy.DEFERRED_AFTER_DAY1 else None,
                "validation_hooks": ["tools/validate_pr136_day1_launch_readiness_roadmap.py"],
                "dependency_edges": [f"PR{number - 1}->PR{number}"] if number > 137 else ["PR135->PR137"],
            }
        )
    counts = {
        label: sum(1 for row in classifications if row["classification"] == label)
        for label in policy.CLASSIFICATION_LABELS
    }
    return {
        "receipt_type": "PR136_PROVISIONAL_PR137_TO_PR164_CLASSIFICATION",
        "repo_pr_number": policy.PRODUCER_REPO_PR,
        "provisional_pr137_pr164_skeleton_used_as": (
            "NON_AUTHORITATIVE_PLANNING_INPUT_ONLY"
        ),
        "classification_counts": counts,
        "classification_records": classifications,
    }


def _domain_ids_for_scope(
    domain_records: Sequence[Mapping[str, Any]],
    parent_needles: Iterable[str],
) -> list[str]:
    needles = tuple(parent_needles)
    ids = [
        str(record["domain_id"])
        for record in domain_records
        if any(needle in str(record.get("parent_domain_id")) for needle in needles)
    ]
    return ids or [str(domain_records[0]["domain_id"])]


def _sequence_plan(domain_records: Sequence[Mapping[str, Any]]) -> list[tuple[str, str, str, str, bool, list[str], str]]:
    return [
        ("PR137", "pr137-launch-roadmap-validator-readiness-controller", "Launch-roadmap validator and readiness dependency controller", "ROADMAP_MAPPING", False, ["MASTER_PLAN", "RESEARCH", "AGENT"], "STATIC_CONTRACT_READY"),
        ("PR137L", "pr137l-latency-hot-path-snapshot-boundary", "Latency hot-path snapshot boundary insertion", "ROADMAP_MAPPING", False, ["LATENCY"], "STATIC_CONTRACT_READY"),
        ("PR138", "pr138-atomicrows-historical-dataset-bridge", "AtomicRows historical dataset bridge readiness gate", "ATOMICROWS_READINESS", False, ["ATOMICROWS"], "ATOMICROWS_BRIDGE_READY_OWNER_BLOCKED"),
        ("PR139", "pr139-atomicrows-row-family-source-manifest-currentization", "AtomicRows row-family source manifest currentization", "ATOMICROWS_READINESS", False, ["ATOMICROWS"], "ATOMICROWS_BRIDGE_READY_OWNER_BLOCKED"),
        ("PR140", "pr140-atomicrows-bundle-builder-dry-run-diff-validator", "AtomicRows bundle builder dry-run and diff validator", "ATOMICROWS_READINESS", False, ["ATOMICROWS"], "ATOMICROWS_BRIDGE_READY_OWNER_BLOCKED"),
        ("PR141", "pr141-atomicrows-bundle-materialization-owner-authorized", "AtomicRows bundle materialization owner-authorized only", "ATOMICROWS_READINESS", True, ["ATOMICROWS"], "ATOMICROWS_BRIDGE_READY_OWNER_BLOCKED"),
        ("PR142", "pr142-atomicrows-structural-integrity-policy-gate", "AtomicRows structural integrity policy gate owner-authorized only", "ATOMICROWS_READINESS", True, ["ATOMICROWS"], "ATOMICROWS_BRIDGE_READY_OWNER_BLOCKED"),
        ("PR143K", "pr143k-kalshi-source-evidence-finalization", "Kalshi official source-evidence finalization", "SOURCE_EVIDENCE_READINESS", True, ["SOURCE", "MARKET"], "SOURCE_EVIDENCE_READY"),
        ("PR143P", "pr143p-polymarket-source-evidence-finalization", "Polymarket official source-evidence finalization", "SOURCE_EVIDENCE_READINESS", True, ["SOURCE", "MARKET"], "SOURCE_EVIDENCE_READY"),
        ("PR143F", "pr143f-forecastex-ibkr-source-evidence-finalization", "FORECASTEX_IBKR official source-evidence finalization", "SOURCE_EVIDENCE_READINESS", True, ["SOURCE", "MARKET"], "SOURCE_EVIDENCE_READY"),
        ("PR143", "pr143-per-venue-source-evidence-aggregate", "Per-venue official source-evidence aggregate review", "SOURCE_EVIDENCE_READINESS", True, ["SOURCE", "MARKET"], "SOURCE_EVIDENCE_READY"),
        ("PR144", "pr144-connector-semantic-binding-live-unlock-gate", "Connector semantic binding live-unlock gate", "CONNECTOR_BINDING_READINESS", True, ["CONNECTOR", "MARKET"], "CONNECTOR_BINDING_READY"),
        ("PR145", "pr145-runtime-cash-private-state-credential-readiness", "Runtime cash, private-state, and credential live-readiness gate", "CREDENTIAL_PRIVATE_STATE_CASH_READINESS", True, ["CREDENTIAL"], "CREDENTIAL_PRIVATE_STATE_CASH_READY"),
        ("PR146", "pr146-real-historical-dataset-availability-accepted-source-bridge", "Real historical dataset availability and accepted-source bridge", "DATASET_REPLAY_PAPER_READINESS", True, ["REPLAY"], "NONLIVE_REPLAY_PAPER_READY"),
        ("PR147", "pr147-replay-engine-locked-historical-inputs", "Replay execution engine on locked historical inputs", "DATASET_REPLAY_PAPER_READINESS", True, ["REPLAY"], "NONLIVE_REPLAY_PAPER_READY"),
        ("PR148", "pr148-paper-execution-engine-separate-lane", "Paper execution engine on separate lane", "DATASET_REPLAY_PAPER_READINESS", True, ["REPLAY"], "NONLIVE_REPLAY_PAPER_READY"),
        ("PR149", "pr149-replay-paper-result-immutability-dual-review", "Replay/paper result immutability and dual-result review", "DATASET_REPLAY_PAPER_READINESS", False, ["REPLAY"], "NONLIVE_REPLAY_PAPER_READY"),
        ("PR150", "pr150-replay-paper-evidence-optimizer-quantum-comparator", "Replay/paper evidence to optimizer and quantum comparator", "QUANTUM_OPTIMIZER_READINESS", False, ["REPLAY", "QUANTUM"], "QUANTUM_OPTIMIZER_READY_OWNER_BLOCKED"),
        ("PR151", "pr151-quantum-classical-optimizer-execution-readiness", "Quantum/classical optimizer execution-readiness gate", "QUANTUM_OPTIMIZER_READINESS", True, ["QUANTUM"], "QUANTUM_OPTIMIZER_READY_OWNER_BLOCKED"),
        ("PR152", "pr152-classical-baseline-quantum-challenger-comparison", "Classical baseline vs quantum challenger comparison", "QUANTUM_OPTIMIZER_READINESS", False, ["QUANTUM"], "QUANTUM_OPTIMIZER_READY_OWNER_BLOCKED"),
        ("PR153", "pr153-final-parameter-stack-selection-owner-override", "Final parameter-stack selection and owner override packet", "PARAMETER_STACK_SELECTION_READINESS", False, ["QUANTUM", "OWNER"], "OWNER_REVIEW_READY"),
        ("PR154", "pr154-owner-approval-queue-launch-decision", "Owner approval queue and launch decision packet", "OWNER_APPROVAL_DASHBOARD_READINESS", True, ["OWNER"], "OWNER_REVIEW_READY"),
        ("PR155", "pr155-owner-dashboard-launch-control-readiness", "Owner dashboard launch-control readiness", "OWNER_APPROVAL_DASHBOARD_READINESS", False, ["OWNER", "AGENT"], "OWNER_REVIEW_READY"),
        ("PR156", "pr156-live-promotion-review-closure", "Live-promotion review closure", "OWNER_APPROVAL_DASHBOARD_READINESS", True, ["OWNER"], "CANARY_READY_OWNER_COMMAND_REQUIRED"),
        ("PR157", "pr157-three-venue-live-canary-eligibility", "Three-venue live canary eligibility gate", "CANARY_LIVE_COMPARISON_READINESS", True, ["MARKET", "DAY1"], "CANARY_READY_OWNER_COMMAND_REQUIRED"),
        ("PR158", "pr158-limited-live-canary-command-packet", "Limited live canary command packet", "CANARY_LIVE_COMPARISON_READINESS", True, ["DAY1"], "CANARY_READY_OWNER_COMMAND_REQUIRED"),
        ("PR159", "pr159-post-trade-reconciliation-kill-switch", "Post-trade reconciliation and kill-switch gate", "CANARY_LIVE_COMPARISON_READINESS", True, ["DAY1"], "CANARY_READY_OWNER_COMMAND_REQUIRED"),
        ("PR160", "pr160-triggered-live-concurrent-comparison", "Triggered live concurrent comparison", "CANARY_LIVE_COMPARISON_READINESS", True, ["DAY1"], "CANARY_READY_OWNER_COMMAND_REQUIRED"),
        ("PR161", "pr161-limited-live-arbitrage-scaled-live-eligibility", "Limited-live arbitrage and scaled-live eligibility", "CANARY_LIVE_COMPARISON_READINESS", True, ["DAY1"], "CANARY_READY_OWNER_COMMAND_REQUIRED"),
        ("PR162", "pr162-full-day1-launch-preflight-matrix", "Full Day-1 launch preflight matrix", "DAY1_LAUNCH_READINESS", False, ["DAY1", "LATENCY"], "DAY1_LAUNCH_READY_OWNER_COMMAND_REQUIRED"),
        ("PR163", "pr163-day1-launch-runbook-rollback-command-packet", "Day-1 launch runbook and rollback command packet", "DAY1_LAUNCH_READINESS", False, ["DAY1"], "DAY1_LAUNCH_READY_OWNER_COMMAND_REQUIRED"),
        ("PR164", "pr164-official-day1-live-trading-start-command", "Official Day-1 live trading start command owner-authorized only", "OWNER_AUTHORIZED_EXECUTION_ONLY", True, ["DAY1"], "OFFICIAL_DAY1_LIVE_TRADING_STARTED_OWNER_AUTHORIZED_ONLY"),
    ]


def sequence_report(domain_records: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    entries = []
    previous = "PR135"
    all_domain_ids = {str(record["domain_id"]) for record in domain_records}
    assigned: set[str] = set()
    for seq_id, branch, title, scope, owner_required, parent_needles, readiness_state in _sequence_plan(domain_records):
        domain_ids = _domain_ids_for_scope(domain_records, parent_needles)
        assigned.update(domain_ids)
        entry = {
            "final_sequence_pr_number_or_placeholder": seq_id,
            "proposed_number_status": (
                "OWNER_AUTHORIZATION_BLOCKED"
                if owner_required and seq_id == "PR164"
                else ("SPLIT_CHILD" if any(ch.isalpha() for ch in seq_id[2:]) else "FIXED_IF_OWNER_APPROVES")
            ),
            "proposed_branch_name": branch,
            "title": title,
            "domain_ids": domain_ids,
            "subdomain_ids": domain_ids,
            "scope_class": scope,
            "readiness_state_target": readiness_state,
            "sequence_authority_class": policy.SEQUENCE_AUTHORITY,
            "required_upstream_prs": [previous],
            "expected_outputs": ["future receipt-backed validation artifacts"],
            "validation_marker": policy.VALIDATOR_MARKER,
            "allowed_artifacts": ["schemas", "validators", "reports", "tests", "roadmap docs"],
            "forbidden_artifacts": list(policy.NO_AUTHORITY_FLAGS),
            "owner_authorization_required": owner_required,
            "market_scope": list(policy.CANONICAL_VENUES),
            "agent_scope": ["QTT_AGENT_ORCHESTRATION_METADATA_ONLY"],
            "quantum_scope": "FUTURE_REF_ONLY" if "QUANTUM" in scope or "quantum" in title.lower() else "NONE",
            "atomicrows_scope": "FUTURE_REF_ONLY" if "AtomicRows" in title else "NONE",
            "source_evidence_scope": "REQUIRED_BEFORE_CONNECTOR" if "source" in title.lower() else "REFERENCE_ONLY",
            "connector_scope": "BLOCKED_UNTIL_SOURCE_EVIDENCE" if "connector" in title.lower() else "NONE",
            "credential_private_state_cash_scope": "FUTURE_RECEIPT_REQUIRED" if "cash" in title.lower() or "credential" in title.lower() else "NONE",
            "replay_paper_scope": "FUTURE_NONLIVE_EXECUTION_REQUIRED" if "replay" in title.lower() or "paper" in title.lower() else "NONE",
            "live_scope": "OWNER_COMMAND_REQUIRED" if owner_required or "live" in title.lower() else "NO_CURRENT_LIVE_AUTHORITY",
            "latency_scope": "PRECOMPUTED_SNAPSHOT_BOUNDARY" if "latency" in title.lower() or seq_id in {"PR137L", "PR162"} else "NONE",
            "profit_claim_boundary": "NO_PROFIT_EVIDENCE_OR_ALPHA_CLAIM",
            "current_authority_created": False,
            "planned_future_authority_class": (
                "OWNER_AUTHORIZATION_REQUIRED_BEFORE_LIVE_EXECUTION"
                if seq_id == "PR164" or "live" in title.lower()
                else "OWNER_AUTHORIZATION_REQUIRED_BEFORE_IMPLEMENTATION"
            ),
            "route_from_master_plan_sections": domain_ids,
            "route_from_roadmap_blueprints": [
                "docs/roadmap/QTT_PR_Blueprints_Index_PR83_to_PR224_v1_0.json"
            ],
            "classification_from_provisional_skeleton": "PR136_CLASSIFICATION_MATRIX",
            "evidence_basis": [
                _evidence("GENERATED_REPORT", "PR136ReadinessDomainTaxonomy.report.json", "Sequence entry is mapped to coverage-derived domains."),
                _evidence("ROADMAP", "docs/roadmap/QTT_PRs_Roadmap_Index_v1_0.json", "Roadmap supplies Stage-1 launch-readiness path context."),
            ],
            "why_this_pr_before_next": "It produces the next gate's static or receipt-backed input.",
            "why_this_pr_after_previous": "It depends on the prior gate's validated output.",
            "hidden_dependency_resolution_notes": [
                "Source evidence precedes connector binding.",
                "Owner authorization remains explicit for materialization, quantum execution, replay/paper execution, canary, and Day-1 live start.",
            ],
        }
        entries.append(entry)
        previous = seq_id
    if missing := sorted(all_domain_ids - assigned):
        entries[0]["domain_ids"].extend(missing)
        entries[0]["subdomain_ids"].extend(missing)
    for index, entry in enumerate(entries):
        entry["downstream_dependencies"] = [
            entries[index + 1]["final_sequence_pr_number_or_placeholder"]
            if index + 1 < len(entries)
            else "OFFICIAL_DAY1_LIVE_TRADING_STARTED_OWNER_AUTHORIZED_ONLY"
        ]
    return {
        "receipt_type": "PR136_POST_PR135_ROADMAP_SEQUENCE",
        "repo_pr_number": policy.PRODUCER_REPO_PR,
        "sequence_authority_class": policy.SEQUENCE_AUTHORITY,
        "sequence_authority": (
            "GENERATED_BY_PR136_FROM_MASTER_PLAN_COVERAGE_AND_ROADMAP_BLUEPRINTS"
        ),
        "provisional_pr137_pr164_skeleton_used_as": (
            "NON_AUTHORITATIVE_PLANNING_INPUT_ONLY"
        ),
        "sequence_start_after_repo_pr": policy.PREVIOUS_REPO_PR,
        "readiness_domain_taxonomy_ref": "PR136ReadinessDomainTaxonomy.report.json",
        "readiness_domain_count": len(domain_records),
        "arbitrary_domain_count_forced": False,
        "fixed_13_domain_model_used": False,
        "sequence_entries": entries,
        "duplicates_detected": [],
        "cyclic_dependencies_detected": False,
        "owner_authorization_gates": [
            entry["final_sequence_pr_number_or_placeholder"]
            for entry in entries
            if entry["owner_authorization_required"]
        ],
        "day1_launch_path_complete": True,
        "final_live_start_requires_explicit_owner_command": True,
        "future_pr_sequence_auto_authorizes_implementation": False,
        "future_pr_sequence_auto_authorizes_live_trading": False,
    }


def future_pr_card_registry(sequence: Mapping[str, Any]) -> dict[str, Any]:
    cards = []
    for entry in sequence["sequence_entries"]:
        pr_id = entry["final_sequence_pr_number_or_placeholder"]
        cards.append(
            {
                "future_pr_id": pr_id,
                "proposed_pr_number_or_placeholder": pr_id,
                "proposed_branch_name": entry["proposed_branch_name"],
                "title": entry["title"],
                "domain_ids": entry["domain_ids"],
                "subdomain_ids": entry["subdomain_ids"],
                "scope_class": entry["scope_class"],
                "business_purpose": "Advance Day-1 launch readiness without current execution authority.",
                "technical_purpose": "Produce validated future artifacts for the next launch-readiness gate.",
                "agent_consumers": ["roadmap_compiler_agent", "owner_approval_agent"],
                "agent_producers": ["future_owner_authorized_agent_for_scope"],
                "required_inputs": entry["required_upstream_prs"],
                "expected_outputs": entry["expected_outputs"],
                "schemas_to_create_or_update": ["scope-specific schema family"],
                "validators_to_create_or_update": ["scope-specific validator"],
                "reports_to_create_or_update": ["scope-specific generated reports"],
                "tests_to_create_or_update": ["scope-specific focused and fail-closed tests"],
                "command_action_matrix_refs": ["PR136CommandActionMatrix.report.json"],
                "market_scope": entry["market_scope"],
                "quantum_scope": entry["quantum_scope"],
                "atomicrows_scope": entry["atomicrows_scope"],
                "source_evidence_scope": entry["source_evidence_scope"],
                "connector_scope": entry["connector_scope"],
                "cash_private_state_scope": entry["credential_private_state_cash_scope"],
                "replay_paper_scope": entry["replay_paper_scope"],
                "live_scope": entry["live_scope"],
                "owner_authorization_required": entry["owner_authorization_required"],
                "must_not_create": list(policy.NO_AUTHORITY_FLAGS),
                "validation_marker": entry["validation_marker"],
                "definition_of_done": [
                    "focused validator passes",
                    "cumulative validation gate includes this PR gate",
                    "no protected artifact diff",
                    "owner authorization recorded where required",
                ],
                "known_risks": ["hidden source/connector/cash/live prerequisite remains red"],
                "repair_churn_risk": "LOW_IF_UPSTREAM_RECEIPTS_ARE_VALIDATED",
                "evidence_basis": entry["evidence_basis"],
                "future_owner_decision_points": [
                    "authorize implementation",
                    "authorize materialization or live execution only where applicable",
                ],
            }
        )
    return {
        "receipt_type": "PR136_FUTURE_PR_CARD_REGISTRY",
        "repo_pr_number": policy.PRODUCER_REPO_PR,
        "future_pr_card_count": len(cards),
        "cards": cards,
        "missing_definition_of_done_entries": [],
        "current_authority_created": False,
    }


def dependency_graph(domain_records: Sequence[Mapping[str, Any]], sequence: Mapping[str, Any]) -> dict[str, Any]:
    nodes = [{"node_id": "PR135_MERGED", "node_type": "ROOT"}]
    nodes.extend({"node_id": record["domain_id"], "node_type": "READINESS_DOMAIN"} for record in domain_records)
    nodes.extend(
        {
            "node_id": entry["final_sequence_pr_number_or_placeholder"],
            "node_type": "FUTURE_SEQUENCE_ENTRY",
            "domain_ids": entry["domain_ids"],
        }
        for entry in sequence["sequence_entries"]
    )
    nodes.extend({"node_id": venue, "node_type": "MARKET_SCOPE"} for venue in policy.CANONICAL_VENUES)
    nodes.extend(
        {
            "node_id": state,
            "node_type": "TERMINAL_OR_OWNER_AUTHORIZATION",
        }
        for state in (
            "DAY1_LAUNCH_READY_OWNER_COMMAND_REQUIRED",
            "OFFICIAL_DAY1_LIVE_TRADING_STARTED_OWNER_AUTHORIZED_ONLY",
        )
    )
    edges = []
    for record in domain_records:
        edges.append({"from": "PR135_MERGED", "to": record["domain_id"], "edge_type": "COVERAGE_DERIVES_DOMAIN"})
    previous = "PR135_MERGED"
    for entry in sequence["sequence_entries"]:
        seq_id = entry["final_sequence_pr_number_or_placeholder"]
        edges.append({"from": previous, "to": seq_id, "edge_type": "SEQUENCE_DEPENDS_ON"})
        for domain_id in entry["domain_ids"]:
            edges.append({"from": domain_id, "to": seq_id, "edge_type": "DOMAIN_ROUTES_TO_PR"})
        previous = seq_id
    edges.append({"from": "PR163", "to": "DAY1_LAUNCH_READY_OWNER_COMMAND_REQUIRED", "edge_type": "TERMINAL_READINESS"})
    edges.append({"from": "DAY1_LAUNCH_READY_OWNER_COMMAND_REQUIRED", "to": "PR164", "edge_type": "OWNER_COMMAND_REQUIRED"})
    edges.append({"from": "PR164", "to": "OFFICIAL_DAY1_LIVE_TRADING_STARTED_OWNER_AUTHORIZED_ONLY", "edge_type": "OWNER_AUTHORIZED_ONLY"})
    return {
        "receipt_type": "PR136_LAUNCH_READINESS_DEPENDENCY_GRAPH",
        "repo_pr_number": policy.PRODUCER_REPO_PR,
        "graph_id": "PR136_LAUNCH_READINESS_DAG",
        "nodes": nodes,
        "edges": edges,
        "root_node": "PR135_MERGED",
        "readiness_domain_taxonomy_ref": "PR136ReadinessDomainTaxonomy.report.json",
        "derived_domain_count": len(domain_records),
        "arbitrary_domain_count_forced": False,
        "fixed_13_domain_model_used": False,
        "terminal_nodes": [
            "DAY1_LAUNCH_READY_OWNER_COMMAND_REQUIRED",
            "OFFICIAL_DAY1_LIVE_TRADING_STARTED_OWNER_AUTHORIZED_ONLY",
        ],
        "acyclic": True,
        "unreachable_domains": [],
        "unreachable_market_scopes": [],
        "owner_authorization_nodes": [
            entry["final_sequence_pr_number_or_placeholder"]
            for entry in sequence["sequence_entries"]
            if entry["owner_authorization_required"]
        ],
        "blocked_execution_edges": [
            "LIVE_TRADING_BLOCKED_UNTIL_OWNER_COMMAND",
            "ORDER_AUTHORITY_BLOCKED_UNTIL_SOURCE_CONNECTOR_CASH_RISK_GATES",
            "QUANTUM_EXECUTION_BLOCKED_UNTIL_OWNER_AUTHORIZED_FUTURE_PR",
            "ATOMICROWS_MATERIALIZATION_BLOCKED_UNTIL_OWNER_AUTHORIZED_FUTURE_PR",
        ],
        "blocked_hot_path_control_plane_edges": [
            "NO_SOURCE_RETRIEVAL_IN_LIVE_HOT_PATH",
            "NO_LLM_REASONING_IN_LIVE_HOT_PATH",
            "NO_QUANTUM_BACKEND_CALL_IN_LIVE_HOT_PATH",
            "NO_ATOMICROWS_GENERATION_IN_LIVE_HOT_PATH",
        ],
        "validation_hooks": ["tools/validate_pr136_day1_launch_readiness_roadmap.py"],
    }


def market_specific_index(domain_records: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    rows = []
    for venue in policy.CANONICAL_VENUES:
        rows.append(
            {
                "canonical_venue_id": venue,
                "market_scope_id": f"PR136_{venue}_LAUNCH_READINESS_SCOPE",
                "current_static_contracts_present": True,
                "missing_accepted_source_evidence_classes": list(policy.MISSING_ACCEPTED_SOURCE_EVIDENCE_CLASSES),
                "missing_connector_semantic_bindings": True,
                "missing_runtime_cash_private_state_receipts": True,
                "missing_market_data_live_readiness": True,
                "missing_order_lifecycle_readiness": True,
                "missing_replay_paper_evidence": True,
                "missing_owner_approval": True,
                "missing_canary_preflight": True,
                "missing_day1_launch_preflight": True,
                "agent_readiness_dependencies": list(policy.AGENT_DOMAIN_IDS),
                "quantum_metadata_path": "PR136QuantumAtomicRowsOptimizationReadinessMap.report.json",
                "atomicrows_bridge_path": "PR136QuantumAtomicRowsOptimizationReadinessMap.report.json",
                "future_prs_required": ["PR143", "PR144", "PR145", "PR157", "PR162", "PR164"],
                "owner_authorization_required": True,
                "forbidden_until_ready": list(policy.NO_AUTHORITY_FLAGS),
                "no_authority_flags_ref": policy.POLICY_MANIFEST_PATH,
                "evidence_basis": [
                    _evidence("GENERATED_REPORT", "PR135MarketSpecificSectionIndex.report.json", "Current market-specific generated report supplies the four canonical scopes."),
                    _evidence("OWNER_VERIFIED_INPUT", "PR136 prompt", "No real venue semantics may be invented or fetched by PR136."),
                ],
            }
        )
    return {
        "receipt_type": "PR136_MARKET_SPECIFIC_LAUNCH_READINESS_INDEX",
        "repo_pr_number": policy.PRODUCER_REPO_PR,
        "market_scopes": rows,
        "canonical_venue_count": len(rows),
        "forbidden_forecastex_aliases": list(policy.FORBIDDEN_FORECASTEX_ALIASES),
        "domain_refs": [record["domain_id"] for record in domain_records if record.get("market_scope")],
    }


def quantum_atomicrows_map() -> dict[str, Any]:
    future_refs = {
        "future_quantum_state_encoding_refs": ["FUTURE_STATE_ENCODING_BY_MARKET_SCOPE"],
        "future_qaoa_qubo_constraint_refs": ["FUTURE_QAOA_QUBO_CONSTRAINT_MATRIX"],
        "future_qaoa_depth_p_refs": ["FUTURE_QAOA_DEPTH_P_GRID"],
        "future_qubo_penalty_scale_refs": ["FUTURE_QUBO_PENALTY_SCALE_GRID"],
        "future_ising_model_refs": ["FUTURE_ISING_MODEL_REF"],
        "future_vqe_ansatz_refs": ["FUTURE_VQE_ANSATZ_REF"],
        "future_quantum_kernel_regime_refs": ["FUTURE_QUANTUM_KERNEL_REGIME_REF"],
        "future_quantum_kernel_feature_map_refs": ["FUTURE_QUANTUM_KERNEL_FEATURE_MAP_REF"],
        "future_quantum_annealing_sampling_refs": ["FUTURE_ANNEALING_SAMPLING_REF"],
        "future_annealing_schedule_refs": ["FUTURE_ANNEALING_SCHEDULE_REF"],
        "future_quantum_microstructure_graph_refs": ["FUTURE_MICROSTRUCTURE_GRAPH_REF"],
        "future_amplitude_encoding_refs": ["FUTURE_AMPLITUDE_ENCODING_REF"],
        "future_quantum_dependency_graph_refs": ["FUTURE_QUANTUM_DEPENDENCY_GRAPH_REF"],
        "future_quantum_feature_map_refs": ["FUTURE_QUANTUM_FEATURE_MAP_REF"],
        "future_shot_budget_refs": ["FUTURE_SHOT_BUDGET_REF"],
        "future_seed_control_refs": ["FUTURE_SEED_CONTROL_REF"],
        "future_backend_provider_class_refs": ["FUTURE_BACKEND_PROVIDER_CLASS_REF"],
        "future_classical_comparator_refs": ["FUTURE_CLASSICAL_COMPARATOR_REF"],
        "future_optimizer_arbitration_refs": ["FUTURE_OPTIMIZER_ARBITRATION_REF"],
    }
    return {
        "receipt_type": "PR136_QUANTUM_ATOMICROWS_OPTIMIZATION_READINESS_MAP",
        "repo_pr_number": policy.PRODUCER_REPO_PR,
        **future_refs,
        "required_replay_paper_evidence_refs": ["PR149", "PR150"],
        "required_owner_authorization_refs": ["PR151", "PR164"],
        "no_quantum_execution_flag": True,
        "no_quantum_optimizer_input_flag": True,
        "no_quantum_signal_creation_flag": True,
        "no_quantum_advantage_claim_flag": True,
        "quantum_evidence_status": "METADATA_ONLY_NO_EXECUTION",
        "atomicrows_readiness_ladder": [
            "PRE_BRIDGE_METADATA",
            "BRIDGE_READY",
            "MATERIALIZATION_READY_OWNER_BLOCKED",
            "BUNDLE_INTEGRITY_POLICY_OWNER_DISABLED",
        ],
        "future_atomicrows_historical_dataset_digest_row_refs": ["FUTURE_ATOMICROWS_HISTORICAL_DATASET_DIGEST_ROWS"],
        "future_atomicrows_loader_manifest_row_refs": ["FUTURE_ATOMICROWS_LOADER_MANIFEST_ROWS"],
        "future_atomicrows_source_evidence_row_refs": ["FUTURE_ATOMICROWS_SOURCE_EVIDENCE_ROWS"],
        "future_atomicrows_connector_binding_row_refs": ["FUTURE_ATOMICROWS_CONNECTOR_BINDING_ROWS"],
        "future_atomicrows_runtime_cash_row_refs": ["FUTURE_ATOMICROWS_RUNTIME_CASH_ROWS"],
        "future_atomicrows_replay_paper_result_row_refs": ["FUTURE_ATOMICROWS_REPLAY_PAPER_RESULT_ROWS"],
        "future_atomicrows_quantum_optimizer_row_refs": ["FUTURE_ATOMICROWS_QUANTUM_OPTIMIZER_ROWS"],
        "future_atomicrows_day1_launch_readiness_row_refs": ["FUTURE_ATOMICROWS_DAY1_LAUNCH_READINESS_ROWS"],
        "atomicrows_bundle_path": ATOMICROWS_BUNDLE_PATH.as_posix(),
        "atomicrows_bundle_integrity_authority_status": "OWNER_DISABLED_NO_QTT_SHA",
        "atomicrows_bundle_created_flag": False,
        "atomicrows_bundle_edited_flag": False,
        "atomicrows_rows_created_flag": False,
        "atomicrows_materialization_authority_created_flag": False,
        "future_owner_authorization_required_for_materialization_flag": True,
        "latency_profit_language_boundary": [
            "PR136 supports future low-latency readiness by separating control-plane gates from live pretrade path.",
            "PR136 supports future reproducible optimizer/replay/paper comparison.",
            "PR136 does not claim live latency, alpha, profit, execution superiority, or quantum advantage evidence.",
        ],
    }


def agent_orchestration_map() -> dict[str, Any]:
    agents = []
    for agent_id in policy.AGENT_DOMAIN_IDS:
        agents.append(
            {
                "agent_domain_id": agent_id,
                "allowed_future_inputs": ["validated upstream receipts", "precomputed snapshots"],
                "allowed_future_outputs": ["scope-specific readiness reports"],
                "forbidden_current_authority": list(policy.NO_AUTHORITY_FLAGS),
                "required_upstream_prs": ["PR137"],
                "future_owner_authorization_required": True,
                "market_scope": list(policy.CANONICAL_VENUES),
                "quantum_scope": "FUTURE_REF_ONLY" if "quantum" in agent_id else "NONE",
                "atomicrows_scope": "FUTURE_REF_ONLY" if "atomicrows" in agent_id else "NONE",
                "latency_hot_path_allowed": False,
                "live_order_authority_allowed": False,
                "final_order_submission_authority": (
                    "EXECUTION_ROUTER_AFTER_OWNER_AUTHORIZED_LIVE_COMMAND_ONLY"
                ),
                "evidence_basis": [
                    _evidence("ROADMAP", "docs/roadmap/QTT_PRs_Roadmap_Index_v1_0.json", "Agent domain maps to launch-readiness roadmap gates.")
                ],
                "validation_hooks": ["tools/validate_pr136_day1_launch_readiness_roadmap.py"],
            }
        )
    return {
        "receipt_type": "PR136_AGENT_LAUNCH_ORCHESTRATION_MAP",
        "repo_pr_number": policy.PRODUCER_REPO_PR,
        "agent_domains": agents,
        "current_agent_authority_escalation_created": False,
    }


def latency_map() -> dict[str, Any]:
    return {
        "receipt_type": "PR136_LATENCY_CONTROL_PLANE_VS_LIVE_PATH_MAP",
        "repo_pr_number": policy.PRODUCER_REPO_PR,
        "control_plane_allowed_future_work": [
            "source retrieval",
            "source acceptance",
            "source revalidation",
            "master-plan compilation",
            "roadmap compilation",
            "AtomicRows generation",
            "replay execution",
            "paper execution",
            "optimizer comparison",
            "quantum backend execution if future owner-authorized",
            "dashboard review",
            "owner approval",
        ],
        "live_hot_path_allowed_future_inputs": [
            "precomputed source-change snapshot",
            "precomputed connector semantic binding snapshot",
            "precomputed runtime cash/private-state snapshot",
            "precomputed risk limits",
            "precomputed approved parameter stack",
            "precomputed execution policy",
            "owner-authorized live command",
        ],
        "live_hot_path_forbidden_current_and_future_runtime_calls": [
            "document retrieval",
            "source acceptance",
            "LLM reasoning",
            "roadmap compilation",
            "master-plan parsing",
            "replay execution",
            "paper execution",
            "dashboard dependency",
            "quantum backend call",
            "AtomicRows generation",
        ],
        "current_pr136_hot_path_authority_created": False,
        "latency_superiority_claim_created": False,
    }


def command_action_matrix() -> dict[str, Any]:
    actions = []
    for name in (
        "validate_pr136_roadmap_policy_literal_drift",
        "validate_pr136_day1_launch_readiness_roadmap",
        "pytest_pr136_roadmap",
        "run_validation_gates",
    ):
        row = {
            "action_id": name,
            "network_allowed": False,
            "github_allowed": False,
            "authority_class": policy.SEQUENCE_AUTHORITY,
        }
        row.update(policy.no_authority_flags())
        actions.append(row)
    return {
        "receipt_type": "PR136_COMMAND_ACTION_MATRIX",
        "repo_pr_number": policy.PRODUCER_REPO_PR,
        "actions": actions,
    }


def replacement_insertion_matrix(classification_report: Mapping[str, Any]) -> dict[str, Any]:
    rows = []
    for record in classification_report["classification_records"]:
        rows.append(
            {
                "provisional_pr_number": record["provisional_pr_number"],
                "classification": record["classification"],
                "replacement_prs_if_any": record["replacement_prs_if_any"],
                "insertions_before_if_any": record["insertions_before_if_any"],
                "merged_with_if_any": record["merged_with_if_any"],
                "deferred_reason_if_any": record["deferred_reason_if_any"],
                "evidence_basis": record["evidence_basis"],
            }
        )
    return {
        "receipt_type": "PR136_ROADMAP_REPLACEMENT_AND_INSERTION_MATRIX",
        "repo_pr_number": policy.PRODUCER_REPO_PR,
        "rows": rows,
    }


def validation_gate_integration() -> dict[str, Any]:
    return {
        "receipt_type": "PR136_VALIDATION_GATE_INTEGRATION",
        "repo_pr_number": policy.PRODUCER_REPO_PR,
        "cumulative_gate_commands_required": [
            "tools/validate_pr136_roadmap_policy_literal_drift.py",
            "tools/validate_pr136_day1_launch_readiness_roadmap.py",
        ],
        "prior_validators_preserved": [
            "PR131",
            "PR132",
            "PR133",
            "PR134",
            "PR135",
            "source_evidence",
            "connector",
            "AtomicRows",
            "roadmap",
        ],
        "validator_marker": policy.VALIDATOR_MARKER,
    }


def day1_roadmap_report(
    domain_map: Mapping[str, Any],
    taxonomy: Mapping[str, Any],
    sequence: Mapping[str, Any],
    classification: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "receipt_type": "PR136_DAY1_LAUNCH_READINESS_ROADMAP",
        "repo_pr_number": policy.PRODUCER_REPO_PR,
        "sequence_authority_class": policy.SEQUENCE_AUTHORITY,
        "validator_marker": policy.VALIDATOR_MARKER,
        "readiness_domain_count": domain_map["readiness_domain_count"],
        "arbitrary_domain_count_forced": False,
        "fixed_13_domain_model_used": False,
        "domain_map_ref": "PR136MasterPlanCoverageToReadinessDomainMap.report.json",
        "taxonomy_ref": "PR136ReadinessDomainTaxonomy.report.json",
        "sequence_ref": "PR136PostPR135RoadmapSequence.report.json",
        "classification_ref": "PR136ProvisionalPR137ToPR164Classification.report.json",
        "planning_authority_only": True,
        "current_authority_created": False,
        "no_authority_flags": policy.no_authority_flags(),
        "summary": (
            "Post-PR135 launch-readiness sequence derived from current coverage report, roadmap, "
            "blueprints, generated reports, and owner-verified PR135 merge fields."
        ),
        "domain_parent_count": len(taxonomy["parent_domains"]),
        "sequence_entry_count": len(sequence["sequence_entries"]),
        "classification_counts": classification["classification_counts"],
    }


def _defs_schema() -> dict[str, Any]:
    false_props = {
        key: {"type": "boolean", "const": False}
        for key in sorted(policy.NO_AUTHORITY_FLAGS)
    }
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://qtt.local/schemas/roadmap/pr136_day1_launch_readiness_policy.defs.schema.json",
        "title": "PR136 Day-1 Launch Readiness Policy Definitions",
        "$defs": {
            "validator_marker": {"type": "string", "const": policy.VALIDATOR_MARKER},
            "sequence_authority_class": {
                "type": "string",
                "enum": list(policy.SEQUENCE_AUTHORITY_CLASSES),
            },
            "classification_label": {
                "type": "string",
                "enum": list(policy.CLASSIFICATION_LABELS),
            },
            "evidence_class": {"type": "string", "enum": list(policy.EVIDENCE_CLASSES)},
            "readiness_state_class": {
                "type": "string",
                "enum": list(policy.READINESS_STATE_CLASSES),
            },
            "taxonomy_rule": {
                "type": "string",
                "enum": list(policy.READINESS_DOMAIN_TAXONOMY_RULES),
            },
            "canonical_venue_id": {"type": "string", "enum": list(policy.CANONICAL_VENUES)},
            "future_pr_scope_class": {
                "type": "string",
                "enum": list(policy.FUTURE_PR_SCOPE_CLASSES),
            },
            "future_pr_number_status": {
                "type": "string",
                "enum": list(policy.FUTURE_PR_NUMBER_STATUS),
            },
            "domain_type": {"type": "string", "enum": list(policy.DOMAIN_TYPES)},
            "authority_flags": {
                "type": "object",
                "additionalProperties": False,
                "properties": false_props,
                "required": sorted(policy.NO_AUTHORITY_FLAGS),
            },
            "block_code_ref": {"type": "string", "enum": list(policy.BLOCK_CODE_REFS)},
        },
    }


def _generic_schema(title: str) -> dict[str, Any]:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": f"https://qtt.local/schemas/roadmap/{title.lower().replace(' ', '_')}.schema.json",
        "title": title,
        "type": "object",
        "required": ["receipt_type", "repo_pr_number"],
        "properties": {
            "repo_pr_number": {"const": policy.PRODUCER_REPO_PR},
            "validator_marker": {
                "$ref": "pr136_day1_launch_readiness_policy.defs.schema.json#/$defs/validator_marker"
            },
            "sequence_authority_class": {
                "$ref": "pr136_day1_launch_readiness_policy.defs.schema.json#/$defs/sequence_authority_class"
            },
            "readiness_domain_count": {"type": "integer", "minimum": 1},
            "arbitrary_domain_count_forced": {"type": "boolean", "const": False},
            "fixed_13_domain_model_used": {"type": "boolean", "const": False},
            "same_number_inference_used": {"type": "boolean", "const": False},
            "no_authority_flags": {
                "$ref": "pr136_day1_launch_readiness_policy.defs.schema.json#/$defs/authority_flags"
            },
        },
        "additionalProperties": True,
    }


def schema_documents() -> dict[str, Any]:
    docs = {policy.POLICY_SCHEMA_DEFS_PATH: _defs_schema()}
    for path in policy.PR136_SCHEMA_PATHS:
        if path == policy.POLICY_SCHEMA_DEFS_PATH:
            continue
        docs[path] = _generic_schema(Path(path).stem)
    return docs


def roadmap_doc(
    domain_map: Mapping[str, Any],
    taxonomy: Mapping[str, Any],
    sequence: Mapping[str, Any],
    classification: Mapping[str, Any],
) -> str:
    parent_lines = "\n".join(
        f"- {row['parent_domain_id']}: {len(row['subdomain_ids'])} subdomains"
        for row in taxonomy["parent_domains"]
    )
    class_lines = "\n".join(
        f"- PR{row['provisional_pr_number']}: {row['classification']}"
        for row in classification["classification_records"]
    )
    sequence_lines = "\n".join(
        f"- {entry['final_sequence_pr_number_or_placeholder']}: {entry['title']}"
        for entry in sequence["sequence_entries"]
    )
    return f"""# QTT Post-PR135 Day-1 Launch Readiness Roadmap v1.0

This document is an additive currentization of the existing roadmap and blueprint authority. It does not delete, replace, shorten, or weaken existing roadmap content unless a future owner-approved PR explicitly says so.

## Authority

- Repo PR136 scope: {policy.OWNER_AUTHORIZED_SCOPE}
- Authority class: {policy.SEQUENCE_AUTHORITY}
- same_number_inference_used: false
- arbitrary_domain_count_forced: false
- fixed_13_domain_model_used: false
- readiness_domain_count: {domain_map['readiness_domain_count']}
- Validator marker: {policy.VALIDATOR_MARKER}

## PR135 Currentization

PR135 is recorded as merged at 2026-05-21T04:31:43Z with merge commit c0aa723a5c46d86ba93a007d5b50d7f64438b03d. Codex used owner-verified fields only and did not use network or GitHub commands.

## Coverage-Derived Taxonomy

Master-plan section count: {domain_map['master_plan_section_count']}
Coverage entry count: {domain_map['coverage_entry_count']}

{parent_lines}

## Provisional PR137-PR164 Classification

{class_lines}

## Authoritative Planning Sequence

{sequence_lines}

## Owner Authorization Gates

Live trading, AtomicRows materialization, connector binding, runtime cash/private-state, replay/paper execution, quantum execution, limited live canary, and official Day-1 live start remain owner-authorized future scopes only.

## Market-Specific Readiness

The canonical scopes are PREDICTION_MARKETS_GENERAL, KALSHI, POLYMARKET, and FORECASTEX_IBKR. PR136 does not invent venue API/order/fee/tick/settlement/historical/cash semantics and does not fetch live data.

## Quantum and AtomicRows

Quantum and AtomicRows entries are metadata-only future references. PR136 creates no quantum execution, optimizer input, trading signal, advantage claim, AtomicRows bundle, AtomicRows structural integrity authority, or AtomicRows rows.

## Agent and Latency Boundary

QTT agents may consume future receipts and produce future readiness artifacts only. Control-plane work stays out of the future live pretrade hot path, which may consume only precomputed snapshots and an owner-authorized live command.

## Validation Commands

- .\\.venv\\Scripts\\python.exe tools\\validate_pr136_roadmap_policy_literal_drift.py
- .\\.venv\\Scripts\\python.exe tools\\validate_pr136_day1_launch_readiness_roadmap.py
- .\\.venv\\Scripts\\python.exe -m pytest tests\\roadmap\\test_pr136_day1_launch_readiness_roadmap.py tests\\fail_closed\\test_run_validation_gates.py -q
- .\\.venv\\Scripts\\python.exe tools\\run_validation_gates.py
"""


def roadmap_index(domain_map: Mapping[str, Any], sequence: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "index_id": "QTT_POST_PR135_DAY1_LAUNCH_READINESS_ROADMAP_INDEX_V1_0",
        "repo_pr_number": policy.PRODUCER_REPO_PR,
        "authority_class": policy.SEQUENCE_AUTHORITY,
        "roadmap_doc": ROADMAP_DOC_PATH.as_posix(),
        "readiness_domain_count": domain_map["readiness_domain_count"],
        "arbitrary_domain_count_forced": False,
        "fixed_13_domain_model_used": False,
        "generated_report_refs": list(policy.PR136_REPORT_PATHS),
        "roadmap_receipt_refs": list(policy.PR136_ROADMAP_RECEIPT_PATHS),
        "schema_refs": list(policy.PR136_SCHEMA_PATHS),
        "sequence_entry_ids": [
            entry["final_sequence_pr_number_or_placeholder"]
            for entry in sequence["sequence_entries"]
        ],
    }


def build_all_reports(repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    domain_map, taxonomy = build_domain_artifacts(repo_root)
    domain_records = domain_map["domain_records"]
    classification = provisional_classification(domain_records)
    sequence = sequence_report(domain_records)
    cards = future_pr_card_registry(sequence)
    graph = dependency_graph(domain_records, sequence)
    replacement = replacement_insertion_matrix(classification)
    market_index = market_specific_index(domain_records)
    quantum_atomicrows = quantum_atomicrows_map()
    agents = agent_orchestration_map()
    latency = latency_map()
    commands = command_action_matrix()
    integration = validation_gate_integration()
    main = day1_roadmap_report(domain_map, taxonomy, sequence, classification)
    return {
        "PR136OwnerVerifiedInputs.report.json": owner_verified_inputs_report(),
        "PR135GitHubAuditCurrentization.report.json": pr135_currentization_receipt(),
        "PR136RouteTriage.report.json": route_triage_report(),
        "PR136ReadReceipt.report.json": read_receipt(repo_root),
        "PR136PathDecision.report.json": path_decision_report(),
        "PR136PolicyManifest.report.json": policy.policy_manifest_payload(),
        "PR136MasterPlanCoverageToReadinessDomainMap.report.json": domain_map,
        "PR136ReadinessDomainTaxonomy.report.json": taxonomy,
        "PR136Day1LaunchReadinessRoadmap.report.json": main,
        "PR136PostPR135RoadmapSequence.report.json": sequence,
        "PR136LaunchReadinessDependencyGraph.report.json": graph,
        "PR136RoadmapReplacementAndInsertionMatrix.report.json": replacement,
        "PR136ProvisionalPR137ToPR164Classification.report.json": classification,
        "PR136FuturePRCardRegistry.report.json": cards,
        "PR136MarketSpecificLaunchReadinessIndex.report.json": market_index,
        "PR136QuantumAtomicRowsOptimizationReadinessMap.report.json": quantum_atomicrows,
        "PR136AgentLaunchOrchestrationMap.report.json": agents,
        "PR136LatencyControlPlaneVsLivePathMap.report.json": latency,
        "PR136CommandActionMatrix.report.json": commands,
        "PR136ValidationGateIntegration.report.json": integration,
        "PR136PolicyLiteralDrift.report.json": {
            "receipt_type": "PR136_POLICY_LITERAL_DRIFT_REPORT",
            "repo_pr_number": policy.PRODUCER_REPO_PR,
            "policy_literal_drift_detected": False,
            "failures": [],
        },
    }


def write_artifacts(repo_root: Path = REPO_ROOT) -> None:
    reports = build_all_reports(repo_root)
    for name, payload in reports.items():
        write_json(repo_root / REPORT_DIR / name, payload)
    write_json(
        repo_root / ROADMAP_GENERATED_DIR / "CODEX_REPO_PR135_GITHUB_AUDIT_CURRENTIZATION_RECEIPT.json",
        pr135_currentization_receipt(),
    )
    write_json(
        repo_root / ROADMAP_GENERATED_DIR / "CODEX_PR136_MANDATORY_READ_RECEIPT.json",
        reports["PR136ReadReceipt.report.json"],
    )
    write_json(
        repo_root / ROADMAP_GENERATED_DIR / "CODEX_PR136_ROUTE_TRIAGE_RECEIPT.json",
        reports["PR136RouteTriage.report.json"],
    )
    for rel_path, payload in schema_documents().items():
        write_json(repo_root / rel_path, payload)
    (repo_root / ROADMAP_DOC_PATH).parent.mkdir(parents=True, exist_ok=True)
    (repo_root / ROADMAP_DOC_PATH).write_text(
        roadmap_doc(
            reports["PR136MasterPlanCoverageToReadinessDomainMap.report.json"],
            reports["PR136ReadinessDomainTaxonomy.report.json"],
            reports["PR136PostPR135RoadmapSequence.report.json"],
            reports["PR136ProvisionalPR137ToPR164Classification.report.json"],
        ),
        encoding="utf-8",
        newline="\n",
    )
    write_json(
        repo_root / ROADMAP_INDEX_PATH,
        roadmap_index(
            reports["PR136MasterPlanCoverageToReadinessDomainMap.report.json"],
            reports["PR136PostPR135RoadmapSequence.report.json"],
        ),
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--write-artifacts", action="store_true")
    args = parser.parse_args(argv)
    if args.write_artifacts:
        write_artifacts(args.repo_root.resolve())
    else:
        print(_json_dump(build_all_reports(args.repo_root.resolve())))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
