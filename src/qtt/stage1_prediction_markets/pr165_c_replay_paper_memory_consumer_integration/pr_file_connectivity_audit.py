"""PR-file connectivity rows for PR165-C-created files."""

from __future__ import annotations

from pathlib import Path

from . import paths as p
from .central_vocab import AUTHORITY_BOUNDARY_REF, DOWNSTREAM_PR_ROUTES, NO_ORPHAN_STATUS, UPSTREAM_PR_REFS
from .deterministic_ids import ordinal_ref


def build_pr_file_connectivity_rows(repo_root: Path, shard_paths: list[str]) -> list[dict[str, object]]:
    files: list[str] = []
    files.extend(p.normalize_repo_ref(p.PACKAGE_DIR / path.name) for path in sorted((repo_root / p.PACKAGE_DIR).glob("*.py")))
    files.extend(p.normalize_repo_ref(p.SCHEMA_DIR / filename) for filename in p.SCHEMA_FILENAMES)
    files.extend(
        [
            "tools/build_pr165_c_replay_paper_memory_consumer_integration.py",
            "tools/validate_pr165_c_replay_paper_memory_consumer_integration.py",
            "tests/stage1_prediction_markets/pr165_c_replay_paper_memory_consumer_integration/__init__.py",
            "tests/stage1_prediction_markets/pr165_c_replay_paper_memory_consumer_integration/test_pr165_c_artifacts.py",
        ]
    )
    files.extend(p.normalize_repo_ref(p.GENERATED_DIR / filename) for filename in p.REPORT_FILENAMES)
    files.extend(p.normalize_repo_ref(path) for path in shard_paths)
    unique_files = sorted(dict.fromkeys(files))
    rows = []
    for index, rel_path in enumerate(unique_files, start=1):
        rows.append(
            {
                "pr_file_connectivity_id": ordinal_ref("PR165_C_PR_FILE_CONNECTIVITY", index),
                "core_table_row_id": ordinal_ref("PR165_C_PR_FILE_CONNECTIVITY", index),
                "file_path": rel_path,
                "file_role": _file_role(rel_path),
                "upstream_source_pr_refs": list(UPSTREAM_PR_REFS),
                "upstream_source_artifact_refs": [
                    "PR165_ReportManifest.report.json",
                    "PR165_B_ReportManifest.report.json",
                    "PR165_C_UpstreamAgentPRDiscovery.report.json",
                ],
                "downstream_consumer_pr_refs": list(DOWNSTREAM_PR_ROUTES),
                "downstream_consumer_artifact_refs": _downstream_artifacts(rel_path),
                "owning_agent": _owning_agent(rel_path),
                "owning_builder_or_tool": "tools/build_pr165_c_replay_paper_memory_consumer_integration.py",
                "validator": "tools/validate_pr165_c_replay_paper_memory_consumer_integration.py",
                "tests_covering_file": [
                    "tests/stage1_prediction_markets/pr165_c_replay_paper_memory_consumer_integration/test_pr165_c_artifacts.py"
                ],
                "manifest_entry_ref": "PR165_C_ReportManifest.report.json",
                "no_orphan_status": NO_ORPHAN_STATUS,
                "authority_boundary_ref": AUTHORITY_BOUNDARY_REF,
                "validation_status": "PASS",
            }
        )
    return rows


def _file_role(rel_path: str) -> str:
    if rel_path.endswith(".schema.json"):
        return "SCHEMA"
    if rel_path.startswith("tools/"):
        return "TOOL"
    if rel_path.startswith("tests/"):
        return "TEST"
    if rel_path.startswith("docs/master_plan/generated/pr165_c_shards/"):
        return "SHARDED_ROW_REPORT"
    if rel_path.startswith("docs/master_plan/generated/"):
        return "ROOT_REPORT"
    return "PACKAGE_SOURCE"


def _owning_agent(rel_path: str) -> str:
    lowered = rel_path.lower()
    if "dashboard" in lowered:
        return "dashboard_agent"
    if "governance" in lowered:
        return "governance_agent"
    if "commander" in lowered:
        return "commander_agent"
    if "quantum" in lowered:
        return "quantum_mapper_advisory_agent"
    if "retest" in lowered or "replay" in lowered:
        return "replay_agent"
    if "repair" in lowered:
        return "repair_agent"
    return "memory_agent"


def _downstream_artifacts(rel_path: str) -> list[str]:
    if rel_path.startswith("docs/master_plan/generated/"):
        return ["PR165_C_ReportManifest.report.json", "PR165_C_FinalSummary.report.json"]
    return ["PR165_C_PRFileConnectivityAudit.report.json", "PR165_C_ReportManifest.report.json"]
