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
            _path("tools", "validate_first_pr_scope.py"),
            "--repo-root",
            ".",
            "--scope-report",
            str(first_pr_scope_report),
            "--block-runtime",
            "--block-live",
            "--block-sha",
            "--block-companion-package",
            "--block-profit-claims",
            "--block-source-retrieval",
            "--block-source-acceptance",
            "--block-connector-binding",
            "--block-private-state-fetch",
            "--block-order-execution",
            "--block-neural-training",
            "--block-neural-inference",
            "--block-external-repo-clone",
            "--block-package-install-scripts",
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
            "--registry-fixture",
            _path(
                "tests",
                "fixtures",
                "source_evidence",
                "synthetic_acceptance_registry.v1.fixture.json",
            ),
        ],
        [
            sys.executable,
            _path("tools", "validate_source_evidence_gate_confirmation_static.py"),
            "--repo-root",
            ".",
            "--schema",
            _path(
                "schemas",
                "source_evidence",
                "source_evidence_gate_confirmation.schema.json",
            ),
            "--fixture",
            _path(
                "tests",
                "fixtures",
                "source_evidence",
                "synthetic_source_evidence_gate_confirmation_blocked.v1.fixture.json",
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
            _path("tools", "validate_venue_abstraction_layer_static.py"),
            "--schema",
            _path("schemas", "connectors", "venue_abstraction_layer.schema.json"),
            "--fixture",
            _path(
                "tests",
                "fixtures",
                "connectors",
                "synthetic_venue_abstraction_layer.v1.fixture.json",
            ),
        ],
        [
            sys.executable,
            _path("tools", "validate_order_intent_execution_router_static.py"),
            "--schema",
            _path(
                "schemas",
                "connectors",
                "order_intent_execution_router_scaffolding.schema.json",
            ),
            "--fixture",
            _path(
                "tests",
                "fixtures",
                "connectors",
                "synthetic_order_intent_execution_router_scaffolding.v1.fixture.json",
            ),
        ],
        [
            sys.executable,
            _path("tools", "validate_atomicrows_readiness_static.py"),
            "--repo-root",
            ".",
            "--schema",
            _path("schemas", "atomicrows", "atomicrows_readiness_audit.schema.json"),
            "--fixture",
            _path(
                "tests",
                "fixtures",
                "atomicrows",
                "synthetic_atomicrows_readiness_blocked.v1.fixture.json",
            ),
        ],
        [
            sys.executable,
            _path("tools", "validate_atomicrows_unblocking_requirements_static.py"),
            "--repo-root",
            ".",
            "--schema",
            _path(
                "schemas",
                "atomicrows",
                "atomicrows_unblocking_requirements_audit.schema.json",
            ),
            "--fixture",
            _path(
                "tests",
                "fixtures",
                "atomicrows",
                "synthetic_atomicrows_unblocking_requirements_required.v1.fixture.json",
            ),
        ],
        [
            sys.executable,
            _path("tools", "validate_atomicrows_canonical_row_specification_static.py"),
            "--repo-root",
            ".",
            "--schema",
            _path(
                "schemas",
                "atomicrows",
                "atomicrows_canonical_row_specification_audit.schema.json",
            ),
            "--fixture",
            _path(
                "tests",
                "fixtures",
                "atomicrows",
                "synthetic_atomicrows_canonical_row_specification_required.v1.fixture.json",
            ),
        ],
        [
            sys.executable,
            _path("tools", "validate_atomicrows_bundle_schema_checker_static.py"),
            "--repo-root",
            ".",
            "--row-schema",
            _path("schemas", "atomicrows", "atomic_parameter_row.schema.json"),
            "--bundle-schema",
            _path("schemas", "atomicrows", "atomic_row_bundle.schema.json"),
            "--fixture",
            _path(
                "tests",
                "fixtures",
                "atomicrows",
                "synthetic_atomicrows_bundle_bootstrap_absent.v1.fixture.json",
            ),
        ],
        [
            sys.executable,
            _path("tools", "validate_generated_derivative_bootstrap_gate_static.py"),
            "--repo-root",
            ".",
            "--schema",
            _path(
                "schemas",
                "master_plan",
                "generated_derivative_bootstrap_gate.schema.json",
            ),
            "--fixture",
            _path(
                "tests",
                "fixtures",
                "master_plan",
                "synthetic_generated_derivative_bootstrap_gate.v1.fixture.json",
            ),
        ],
        [
            sys.executable,
            _path("tools", "validate_stage1_packet_schema_gate_static.py"),
            "--repo-root",
            ".",
            "--schema-dir",
            _path("schemas", "stage1_prediction_markets"),
            "--fixture",
            _path(
                "tests",
                "fixtures",
                "stage1_prediction_markets",
                "synthetic_stage1_packet_schema_gate_blocked.v1.fixture.json",
            ),
        ],
        [
            sys.executable,
            _path("tools", "validate_venue_neutral_prediction_adapter_gate_static.py"),
            "--repo-root",
            ".",
            "--schema-dir",
            _path("schemas", "venue_neutral_prediction_adapter"),
            "--fixture",
            _path(
                "tests",
                "fixtures",
                "venue_neutral_prediction_adapter",
                "synthetic_venue_neutral_prediction_adapter_gate_blocked.v1.fixture.json",
            ),
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_connector_scaffold_source_required_gate_static.py",
            ),
            "--repo-root",
            ".",
            "--schema",
            _path(
                "schemas",
                "connectors",
                "connector_scaffold_source_required_gate.schema.json",
            ),
            "--fixture",
            _path(
                "tests",
                "fixtures",
                "connectors",
                "synthetic_connector_scaffold_source_required_blocked.v1.fixture.json",
            ),
        ],
        [
            sys.executable,
            _path("tools", "validate_stage1_runtime_scaffold_gate_static.py"),
            "--repo-root",
            ".",
            "--schema",
            _path(
                "schemas",
                "runtime_orchestration",
                "stage1_runtime_scaffold_gate.schema.json",
            ),
            "--fixture",
            _path(
                "tests",
                "fixtures",
                "runtime_orchestration",
                "synthetic_stage1_runtime_scaffold_gate_blocked.v1.fixture.json",
            ),
        ],
        [
            sys.executable,
            _path("tools", "qtt_test_gate.py"),
            "--phase",
            "first-coding-runbook",
            "--repo-root",
            ".",
            "--strict-no-claim",
            "--out",
            _path("docs", "master_plan", "generated", "QTTTestGate.report.json"),
        ],
        [
            sys.executable,
            _path("tools", "local_gate_command_matrix.py"),
            "--repo-root",
            ".",
            "--out",
            _path(
                "docs",
                "master_plan",
                "generated",
                "LocalGateCommandMatrix.json",
            ),
        ],
        [
            sys.executable,
            _path("tools", "pr_handoff_check.py"),
            "--repo-root",
            ".",
            "--out",
            _path(
                "docs",
                "master_plan",
                "generated",
                "FirstCodingPRHandoff.packet.json",
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
