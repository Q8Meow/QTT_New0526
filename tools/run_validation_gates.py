#!/usr/bin/env python3
from __future__ import annotations

import pathlib
import subprocess
import sys
from typing import Sequence

SUCCESS_MARKER = "QTT_VALIDATION_GATES_OK"


def _path(*parts: str) -> str:
    return str(pathlib.Path(*parts))


def build_validation_commands() -> list[list[str]]:
    validation_dir = pathlib.Path(".tmp") / "validation_gates"
    section_manifest = validation_dir / "SectionManifest.json"
    traceability_report = validation_dir / "TraceabilityReport.json"
    first_pr_scope_report = validation_dir / "FirstPrScopeReport.json"
    master_plan = pathlib.Path("docs") / "master_plan" / "QTT_MasterPlan_Current.md"

    return [
        [
            sys.executable,
            _path("tools", "master_plan_ingest.py"),
            "--input",
            str(master_plan),
            "--section-manifest-out",
            str(section_manifest),
            "--traceability-out",
            str(traceability_report),
            "--scope-report-out",
            str(first_pr_scope_report),
        ],
        [
            sys.executable,
            _path("tools", "master_plan_traceability_check.py"),
            "--master-plan",
            str(master_plan),
            "--section-manifest",
            str(section_manifest),
            "--traceability-report",
            str(traceability_report),
        ],
        [
            sys.executable,
            _path("tools", "validate_source_evidence_static.py"),
            "--schema",
            _path("schemas", "source_evidence", "source_evidence.schema.json"),
            "--owner-packet",
            _path(
                "docs",
                "master_plan",
                "source_evidence",
                "QTT_OWNER_SOURCE_EVIDENCE_DEFINITIONS_PACKET.md",
            ),
        ],
        [
            sys.executable,
            _path("tools", "validate_connector_capability_static.py"),
            "--schema",
            _path("schemas", "connectors", "connector_capability_registry.schema.json"),
            "--fixture",
            _path(
                "tests",
                "fixtures",
                "connectors",
                "synthetic_connector_capability_registry.v1.fixture.json",
            ),
        ],
        [
            sys.executable,
            _path("tools", "validate_runtime_orchestration_static.py"),
            "--schema",
            _path(
                "schemas",
                "runtime_orchestration",
                "runtime_orchestration_skeleton.schema.json",
            ),
            "--fixture",
            _path(
                "tests",
                "fixtures",
                "runtime_orchestration",
                "synthetic_runtime_orchestration_skeleton.v1.fixture.json",
            ),
        ],
        [
            sys.executable,
            _path("tools", "validate_replay_paper_execution_graph_static.py"),
            "--schema",
            _path(
                "schemas",
                "replay_paper_review",
                "replay_paper_execution_graph.schema.json",
            ),
            "--fixture",
            _path(
                "tests",
                "fixtures",
                "replay_paper_review",
                "synthetic_replay_paper_execution_graph.v1.fixture.json",
            ),
        ],
        [
            sys.executable,
            _path("tools", "validate_no_runtime_artifacts.py"),
            "--repo-root",
            ".",
            "--forbid-source-retrieval",
            "--forbid-source-acceptance",
            "--forbid-connector-binding",
            "--forbid-private-state-fetch",
            "--forbid-order-execution",
            "--forbid-neural-training",
            "--forbid-neural-inference",
            "--forbid-external-repo-clone",
            "--forbid-package-install-scripts",
        ],
        [
            sys.executable,
            _path("tools", "run_pytest_fresh_basetemp.py"),
            "-q",
        ],
    ]


def run_commands(commands: Sequence[Sequence[str]]) -> int:
    for command in commands:
        command_list = list(command)
        print(subprocess.list2cmdline(command_list), flush=True)
        completed = subprocess.run(command_list)
        if completed.returncode != 0:
            return completed.returncode

    print(SUCCESS_MARKER, flush=True)
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else list(argv)
    if args:
        print("run_validation_gates.py does not accept arguments", file=sys.stderr)
        return 2
    return run_commands(build_validation_commands())


if __name__ == "__main__":
    raise SystemExit(main())
