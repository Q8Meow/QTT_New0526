#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import UTC, datetime
import pathlib
import subprocess
import sys
import tempfile
import inspect
import json
import time
from typing import Sequence

SUCCESS_MARKER = "QTT_VALIDATION_GATES_OK"
PYTEST_FRESH_BASETEMP_SCRIPT = "run_pytest_fresh_basetemp.py"
PHASE_SUCCESS_MARKER_PREFIX = "QTT_VALIDATION_PHASE_OK"
TIMING_SCHEMA_VERSION = 1
SLOWEST_ENTRY_LIMIT = 20
PYTEST_DURATIONS_ARG = "--durations=50"
FAST_PREFLIGHT_PHASE = "fast-preflight"
DETERMINISTIC_VALIDATORS_PHASE = "deterministic-validators"
PYTEST_SHARD_PHASES = (
    "pytest-shard-1",
    "pytest-shard-2",
    "pytest-shard-3",
    "pytest-shard-4",
)
POST_VALIDATION_PHASE = "post-validation"
ALL_PHASE = "all"
ORDERED_PHASES = (
    FAST_PREFLIGHT_PHASE,
    DETERMINISTIC_VALIDATORS_PHASE,
    *PYTEST_SHARD_PHASES,
    POST_VALIDATION_PHASE,
)
VALIDATION_PHASES = (*ORDERED_PHASES, ALL_PHASE)
FAST_PREFLIGHT_SCRIPT_NAMES = frozenset(
    {
        "validate_grand_global_debug_logical_consistency_audit.py",
        "validate_ci_branch_context_matrix.py",
        "validate_repair_pr_changed_file_scope.py",
        "validate_nested_validator_contracts.py",
    }
)
ISOLATED_SOURCE_EVIDENCE_PYTEST = (
    "tests/source_evidence/"
    "test_controlled_official_source_capture_candidate_packets.py"
)


@dataclass(frozen=True)
class PytestShardCommand:
    paths: tuple[str, ...]
    ignores: tuple[str, ...] = ()
    reason: str = ""


@dataclass(frozen=True)
class TimingEntry:
    phase: str
    command_index: int
    command: list[str]
    elapsed_seconds: float
    returncode: int


PYTEST_SHARD_COMMANDS: dict[str, tuple[PytestShardCommand, ...]] = {
    "pytest-shard-1": (
        PytestShardCommand(
            paths=("tests/tools", "tests/fail_closed"),
            reason="CI tooling and fail-closed runner policy tests",
        ),
    ),
    "pytest-shard-2": (
        PytestShardCommand(
            paths=("tests/stage1_prediction_markets",),
            reason="Stage 1 prediction-market tests",
        ),
    ),
    "pytest-shard-3": (
        PytestShardCommand(
            paths=("tests/atomicrows",),
            reason="AtomicRows tests",
        ),
    ),
    "pytest-shard-4": (
        PytestShardCommand(
            paths=(ISOLATED_SOURCE_EVIDENCE_PYTEST,),
            reason="Preserves the existing isolated source-evidence pytest invocation",
        ),
        PytestShardCommand(
            paths=("tests",),
            ignores=(
                "tests/tools",
                "tests/fail_closed",
                "tests/stage1_prediction_markets",
                "tests/atomicrows",
                ISOLATED_SOURCE_EVIDENCE_PYTEST,
            ),
            reason="Remaining tests after the explicit stable shard groups",
        ),
    ),
}
PRE_VALIDATION_FINALIZATION_GUIDANCE = (
    {
        "command_id": "pr152_currentize_after_generated_artifacts",
        "command": (
            ".\\.venv\\Scripts\\python.exe "
            "tools\\currentize_pr152_after_generated_artifacts.py"
        ),
        "when": "after final generated artifacts settle and before validation gates",
        "ci_tracked_report_mutation_allowed": False,
    },
)
PR142_HANDOFF_READINESS_VALIDATOR_SCRIPT = (
    "validate_atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate.py"
)
PR143_OWNER_OVERRIDE_CURRENTIZATION_VALIDATOR_SCRIPT = (
    "validate_qtt_owner_global_override_directive_currentization_and_internal_gate_release.py"
)
_RUN_COMMANDS_CLEANUP_REPO_ROOT: pathlib.Path | None = None
TRACKED_GENERATED_PATH_PREFIXES = (
    "docs/master_plan/generated/",
    "docs/master_plan/source_evidence/generated/",
    "docs/roadmap/generated/",
)
VOLATILE_GENERATED_REPORT_CURRENTNESS_FIELDS = frozenset(
    {
        "branch",
        "base_head",
    }
)
GENERATED_REPORT_CURRENTNESS_IGNORED_FIELDS = (
    VOLATILE_GENERATED_REPORT_CURRENTNESS_FIELDS | {"report_path"}
)
CHECK_ONLY_VALIDATOR_SCRIPTS = frozenset(
    {
        "validate_source_evidence_retrieval_executor.py",
        "validate_source_evidence_acceptance.py",
        "validate_source_revalidation_scheduler.py",
        "validate_connector_semantic_binding_implementation_gate.py",
        "validate_per_venue_execution_lifecycle_model.py",
        "validate_cross_venue_execution_normalization_binding.py",
        "runtime_cash_component_field_map_validate.py",
        "private_state_read_receipt_gate_validate.py",
        "credential_alias_secret_no_capture_readiness_validate.py",
        "venue_market_data_ingest_adapters_validate.py",
        "orderbook_event_state_snapshot_builder_validate.py",
        "runtime_resolver_snapshot_executor_validate.py",
    }
)
DEFAULT_GENERATED_OUTPUT_ARGS = {
    "validate_qtt_owner_global_override_authority.py": (
        "--out",
        "docs/master_plan/generated/QTTOwnerGlobalOverrideAuthority.report.json",
    ),
    "validate_qtt_agent_role_operating_charter_registry.py": (
        "--out",
        "docs/master_plan/generated/QTTAgentRoleOperatingCharterReport.json",
    ),
    "validate_qtt_algorithm_formula_family_registry.py": (
        "--out",
        "docs/master_plan/generated/QTTAlgorithmFormulaFamilyReport.json",
    ),
    "validate_qtt_agent_algorithm_binding_registry.py": (
        "--out",
        "docs/master_plan/generated/QTTAgentAlgorithmBindingReport.json",
    ),
    "validate_qtt_agent_algorithm_consumer_gate.py": (
        "--out",
        "docs/master_plan/generated/QTTAgentAlgorithmConsumerGate.report.json",
    ),
    "validate_qtt_agent_algorithm_cumulative_readiness_gate.py": (
        "--out",
        "docs/master_plan/generated/QTTAgentAlgorithmCumulativeReadinessGate.report.json",
    ),
    "validate_accepted_source_to_connector_semantic_binding.py": (
        "--out",
        "docs/master_plan/source_evidence/generated/CODEX_PR124_ACCEPTED_SOURCE_TO_CONNECTOR_SEMANTIC_BINDING_CONSUMER_GATE_REPORT.json",
    ),
    "validate_source_revalidation_scheduler.py": (
        "--out",
        "docs/master_plan/source_evidence/generated/CODEX_PR125_SOURCE_REVALIDATION_SUPERSESSION_MATERIALITY_SCHEDULER_REPORT.json",
    ),
    "validate_qtt_agent_algorithm_command_matrix.py": (
        "--out",
        "docs/master_plan/generated/QTTAgentAlgorithmCommandMatrix.json",
    ),
    "build_atomicrows_parameter_lifecycle_report.py": (
        "--out",
        "docs/master_plan/generated/AtomicRowsParameterLifecycleReport.json",
    ),
    "validate_atomicrows_lifecycle_consumer_gate.py": (
        "--out",
        "docs/master_plan/generated/AtomicRowsLifecycleConsumerGate.report.json",
    ),
    "validate_atomicrows_lifecycle_promotion_receipt_gate.py": (
        "--out",
        "docs/master_plan/generated/AtomicRowsLifecyclePromotionReceiptGate.report.json",
    ),
    "validate_atomicrows_lifecycle_registry_mutation_guard.py": (
        "--out",
        "docs/master_plan/generated/AtomicRowsLifecycleRegistryMutationGuard.report.json",
    ),
    "validate_atomicrows_lifecycle_cumulative_readiness_gate.py": (
        "--out",
        "docs/master_plan/generated/AtomicRowsLifecycleCumulativeReadinessGate.report.json",
    ),
    "validate_atomicrows_lifecycle_gate_command_matrix.py": (
        "--out",
        "docs/master_plan/generated/AtomicRowsLifecycleGateCommandMatrix.json",
    ),
    "validate_atomicrows_parameter_agent_binding_registry.py": (
        "--out",
        "docs/master_plan/generated/AtomicRowsParameterAgentBindingReport.json",
    ),
    "validate_atomicrows_parameter_agent_binding_consumer_gate.py": (
        "--out",
        "docs/master_plan/generated/AtomicRowsParameterAgentBindingConsumerGate.report.json",
    ),
    "validate_atomicrows_parameter_agent_binding_cumulative_readiness_gate.py": (
        "--out",
        "docs/master_plan/generated/AtomicRowsParameterAgentBindingCumulativeReadinessGate.report.json",
    ),
    "validate_atomicrows_parameter_agent_binding_command_matrix.py": (
        "--out",
        "docs/master_plan/generated/AtomicRowsParameterAgentBindingCommandMatrix.json",
    ),
    "validate_atomicrows_research_provenance_evidence_tier_classification.py": (
        "--out",
        "docs/master_plan/generated/AtomicRowsResearchProvenanceEvidenceTierClassification.report.json",
    ),
    "validate_atomicrows_owner_submitted_research_source_intake_registry.py": (
        "--out",
        "docs/master_plan/generated/AtomicRowsOwnerSubmittedResearchSourceIntakeRegistry.report.json",
    ),
    "validate_atomicrows_research_source_to_candidate_family_gate.py": (
        "--out",
        "docs/master_plan/generated/AtomicRowsResearchSourceToCandidateFamilyGate.report.json",
    ),
    "validate_atomicrows_parameter_stack_role_taxonomy.py": (
        "--out",
        "docs/master_plan/generated/AtomicRowsParameterStackRoleTaxonomy.report.json",
    ),
    "validate_atomicrows_parameter_stack_completeness_gate.py": (
        "--out",
        "docs/master_plan/generated/AtomicRowsParameterStackCompletenessGate.report.json",
    ),
    "validate_atomicrows_parameter_stack_compatibility_gate.py": (
        "--out",
        "docs/master_plan/generated/AtomicRowsParameterStackCompatibilityGate.report.json",
    ),
    "validate_edge_parameter_stack_selection_packet.py": (
        "--out",
        "docs/master_plan/generated/EDGEParameterStackSelectionPacket.report.json",
    ),
    "validate_qtt_trade_context_packet.py": (
        "--out",
        "docs/master_plan/generated/QTTTradeContextPacket.report.json",
    ),
    "validate_atomicrows_parameter_selection_universe_registry.py": (
        "--out",
        "docs/master_plan/generated/AtomicRowsParameterSelectionUniverseRegistry.report.json",
    ),
    "validate_atomicrows_parameter_selection_universe_consumer_gate.py": (
        "--out",
        "docs/master_plan/generated/AtomicRowsParameterSelectionUniverseConsumerGate.report.json",
    ),
    "validate_trade_context_selection_universe_routing_gate.py": (
        "--out",
        "docs/master_plan/generated/AtomicRowsTradeContextSelectionUniverseRoutingGate.report.json",
    ),
    "validate_quantum_applicability_classification_registry.py": (
        "--out",
        "docs/master_plan/generated/QuantumApplicabilityClassificationRegistry.report.json",
    ),
    "validate_owner_quantum_priority_policy_registry.py": (
        "--out",
        "docs/master_plan/generated/OwnerQuantumPriorityPolicyRegistry.report.json",
    ),
    "validate_parameter_algorithm_scoring_policy_registry.py": (
        "--out",
        "docs/master_plan/generated/ParameterAlgorithmScoringPolicyRegistry.report.json",
    ),
    "validate_parameter_stack_scoring_and_ranking_gate.py": (
        "--out",
        "docs/master_plan/generated/ParameterStackScoringAndRankingGate.report.json",
    ),
    "validate_quantum_classical_optimizer_arbitration_gate.py": (
        "--out",
        "docs/master_plan/generated/QuantumClassicalOptimizerArbitrationGate.report.json",
    ),
    "validate_candidate_parameter_stack_generation_gate.py": (
        "--out",
        "docs/master_plan/generated/CandidateParameterStackGenerationGate.report.json",
    ),
    "validate_trade_context_parameter_stack_selection_gate.py": (
        "--out",
        "docs/master_plan/generated/TradeContextParameterStackSelectionGate.report.json",
    ),
    "validate_selected_parameter_stack_handoff_packet.py": (
        "--out",
        "docs/master_plan/generated/SelectedParameterStackHandoffPacket.report.json",
    ),
    "validate_replay_paper_candidate_stack_competition_gate.py": (
        "--out",
        "docs/master_plan/generated/ReplayPaperCandidateStackCompetitionGate.report.json",
    ),
    "validate_dual_result_review_for_parameter_stacks.py": (
        "--out",
        "docs/master_plan/generated/DualResultReviewForParameterStacks.report.json",
    ),
    "validate_owner_live_promotion_review_for_parameter_stacks.py": (
        "--out",
        "docs/master_plan/generated/OwnerLivePromotionReviewForParameterStacks.report.json",
    ),
    "validate_owner_approval_request_queue_registry.py": (
        "--out",
        "docs/master_plan/generated/OwnerApprovalRequestQueueRegistry.report.json",
    ),
    "validate_owner_override_receipt_authoring_gate.py": (
        "--out",
        "docs/master_plan/generated/OwnerOverrideReceiptAuthoringGate.report.json",
    ),
    "validate_owner_dashboard_approval_menu_schema.py": (
        "--out",
        "docs/master_plan/generated/OwnerDashboardApprovalMenuSchema.report.json",
    ),
    "validate_owner_dashboard_approval_static_screen_contract.py": (
        "--out",
        "docs/master_plan/generated/OwnerDashboardApprovalStaticScreenContract.report.json",
    ),
    "validate_atomicrows_full_bundle_row_expansion_plan.py": (
        "--out",
        "docs/master_plan/generated/AtomicRowsFullBundleRowExpansionPlan.report.json",
    ),
    "validate_atomicrows_bundle_row_family_source_files.py": (
        "--out",
        "docs/master_plan/generated/AtomicRowsBundleRowFamilySourceFiles.report.json",
    ),
    "validate_atomicrows_bundle_builder_deterministic_assembly_gate.py": (
        "--out",
        "docs/master_plan/generated/AtomicRowsBundleBuilderDeterministicAssemblyGate.report.json",
    ),
    "validate_atomicrows_sha_system_dormancy_state_contract.py": (
        "--report-out",
        "docs/master_plan/generated/AtomicRowsShaSystemDormancyStateContract.report.json",
    ),
    "validate_qtt_final_readiness_dependency_policy_contract.py": (
        "--report-out",
        "docs/master_plan/generated/QttFinalReadinessDependencyPolicy.report.json",
    ),
    "validate_qtt_active_non_sha_day1_gate_state_registry_contract.py": (
        "--report-out",
        "docs/master_plan/generated/QttActiveNonShaDay1GateStateRegistry.report.json",
    ),
    "validate_qtt_pr_identity_roster.py": (
        "--report-out",
        "docs/master_plan/generated/QttPrIdentityRoster.report.json",
    ),
    "validate_qtt_roadmap_execution_state_controller.py": (
        "--report-out",
        "docs/master_plan/generated/QttRoadmapExecutionStateController.report.json",
    ),
    "validate_atomicrows_bundle_sha_freeze_authority_gate.py": (
        "--report-out",
        "docs/master_plan/generated/AtomicRowsBundleShaFreezeAuthorityGate.report.json",
    ),
    "validate_atomicrows_exact_row_authority_classifier_bridge.py": (
        "--report-out",
        "docs/master_plan/generated/AtomicRowsExactRowAuthorityClassifierBridge.report.json",
    ),
    "validate_atomicrows_exact_row_expansion_manifest.py": (
        "--report-out",
        "docs/master_plan/generated/AtomicRowsExactRowExpansionManifest.report.json",
    ),
    "validate_atomicrows_owner_approved_exact_15_family_count_distribution.py": (
        "--report-out",
        "docs/master_plan/generated/AtomicRowsOwnerApprovedExact15FamilyCountDistribution.report.json",
    ),
    "validate_atomicrows_exact_row_generator_dry_run_manifest.py": (
        "--report-out",
        "docs/master_plan/generated/AtomicRowsExactRowGeneratorDryRun.report.json",
    ),
    "validate_atomicrows_repair_chain_grand_debug_logic_audit_manifest.py": (
        "--report-out",
        "docs/master_plan/generated/AtomicRowsRepairChainGrandDebugLogicAudit.report.json",
    ),
    "validate_atomicrows_exact_row_source_materialization_manifest.py": (
        "--report-out",
        "docs/master_plan/generated/AtomicRowsExactRowSourceMaterialization.report.json",
    ),
    "validate_atomicrows_exact_row_agent_family_eligibility_matrix.py": (
        "--report-out",
        "docs/master_plan/generated/AtomicRowsExactRowAgentFamilyEligibilityMatrix.report.json",
    ),
    "validate_atomicrows_bundle_materialization_manifest.py": (
        "--report-out",
        "docs/master_plan/generated/AtomicRowsBundleMaterialization.report.json",
    ),
    "validate_atomicrows_bundle_boundary_state_contract.py": (
        "--report-out",
        "docs/master_plan/generated/AtomicRowsBundleBoundaryStateContract.report.json",
    ),
    "validate_atomicrows_sha_freeze_final_readiness_state_contract.py": (
        "--report-out",
        "docs/master_plan/generated/AtomicRowsShaFreezeFinalReadinessStateContract.report.json",
    ),
    "stage1_connector_semantic_binding_ledger_check.py": (
        "--out",
        "docs/master_plan/generated/Stage1ConnectorSemanticBindingLedgerCheck.report.json",
    ),
    "stage1_runtime_resolver_snapshot_contract_check.py": (
        "--out",
        "docs/master_plan/generated/Stage1RuntimeResolverSnapshotContractCheck.report.json",
    ),
    "stage1_runtime_resolver_to_replay_paper_handoff_check.py": (
        "--out",
        "docs/master_plan/generated/Stage1RuntimeResolverToReplayPaperHandoff.report.json",
    ),
    "stage1_concurrent_replay_paper_contract_check.py": (
        "--out",
        "docs/master_plan/generated/Stage1ConcurrentReplayPaperContractCheck.report.json",
    ),
    "stage1_dual_result_review_contract_check.py": (
        "--out",
        "docs/master_plan/generated/Stage1DualResultReviewContractCheck.report.json",
    ),
    "stage1_owner_live_promotion_review_contract_check.py": (
        "--out",
        "docs/master_plan/generated/Stage1OwnerLivePromotionReviewContractCheck.report.json",
    ),
    "stage1_three_venue_canary_eligibility_contract_check.py": (
        "--out",
        "docs/master_plan/generated/Stage1ThreeVenueCanaryEligibilityContractCheck.report.json",
    ),
    "qtt_test_gate.py": (
        "--out",
        "docs/master_plan/generated/QTTTestGate.report.json",
    ),
    "local_gate_command_matrix.py": (
        "--out",
        "docs/master_plan/generated/LocalGateCommandMatrix.json",
    ),
    "pr_handoff_check.py": (
        "--out",
        "docs/master_plan/generated/FirstCodingPRHandoff.packet.json",
    ),
    "build_master_plan_section_coverage_report.py": (
        "--out",
        "docs/master_plan/generated/MasterPlanSectionCoverageReport.json",
    ),
}
GENERATED_REPORT_CURRENTNESS_OUTPUT_ARGS: dict[str, tuple[str, str]] = {}
PR138_NON_MUTATING_VALIDATION_SCRIPT = (
    "from pathlib import Path\n"
    "from src.qtt.stage1_prediction_markets.atomicrows_semantic_contract.report "
    "import build_report\n"
    "from src.qtt.stage1_prediction_markets.atomicrows_semantic_contract.validator "
    "import validate_report_payload, validate_repository_artifacts\n"
    "root = Path('.').resolve()\n"
    "report = build_report(root)\n"
    "failures = list(validate_repository_artifacts(root))\n"
    "outcome = validate_report_payload(\n"
    "    report,\n"
    "    repo_root=root,\n"
    "    enforce_environment=True,\n"
    "    enforce_protected_diff=True,\n"
    ")\n"
    "failures.extend(outcome.failures)\n"
    "unique_failures = tuple(sorted(set(failures)))\n"
    "if unique_failures:\n"
    "    print('\\n'.join(unique_failures))\n"
    "    raise SystemExit(1)\n"
    "for receipt in outcome.receipts:\n"
    "    print(receipt)\n"
)
ATOMICROWS_BUNDLE_CHECK_SCRIPT = (
    "import json\n"
    "from pathlib import Path\n"
    "\n"
    "bundle = Path('docs/master_plan/atomic_rows/AtomicRows.bundle.jsonl')\n"
    "sidecar = Path('docs/master_plan/atomic_rows') / ('AtomicRows' + '.bundle' + '.' + 'sha256')\n"
    "if not bundle.is_file():\n"
    "    raise SystemExit('AtomicRows bundle is missing')\n"
    "if sidecar.exists():\n"
    "    raise SystemExit('AtomicRows bundle SHA sidecar must be absent')\n"
    "data = bundle.read_bytes()\n"
    "assert data, 'AtomicRows bundle is empty'\n"
    "assert not data.startswith(b'\\xef\\xbb\\xbf'), 'AtomicRows bundle has a UTF-8 BOM'\n"
    "assert b'\\r' not in data, 'AtomicRows bundle contains CR or CRLF line endings'\n"
    "assert data.endswith(b'\\n'), 'AtomicRows bundle must end with LF'\n"
    "lines = data.decode('utf-8').splitlines()\n"
    "assert len(lines) == 4183, f'expected 4183 AtomicRows rows, found {len(lines)}'\n"
    "assert all(line.strip() for line in lines), 'AtomicRows bundle contains blank rows'\n"
    "for line_number, line in enumerate(lines, start=1):\n"
    "    json.loads(line)\n"
)


def _path(*parts: str) -> str:
    return str(pathlib.Path(*parts))


def _default_validation_dir() -> pathlib.Path:
    return pathlib.Path(tempfile.gettempdir()) / "qtt_validation_gates"


def _repo_root() -> pathlib.Path:
    return pathlib.Path(__file__).resolve().parents[1]


def _is_final_pytest_command(command: Sequence[str]) -> bool:
    return (
        len(command) > 1
        and pathlib.PurePath(command[1]).name == PYTEST_FRESH_BASETEMP_SCRIPT
    )


def build_pre_validation_finalization_guidance() -> list[dict[str, object]]:
    return [dict(record) for record in PRE_VALIDATION_FINALIZATION_GUIDANCE]


def _command_script_name(command: Sequence[str]) -> str:
    if len(command) <= 1:
        return ""
    return pathlib.PurePath(command[1]).name


def _command_uses_pytest_helper(command: Sequence[str]) -> bool:
    return _command_script_name(command) == PYTEST_FRESH_BASETEMP_SCRIPT


def _normal_repo_path_text(value: pathlib.Path | str) -> str:
    return str(value).replace("\\", "/")


def _is_pytest_file(path: pathlib.Path) -> bool:
    return path.is_file() and path.suffix == ".py" and path.name.startswith("test_")


def discover_pytest_files(repo_root: pathlib.Path | str | None = None) -> tuple[str, ...]:
    root = _repo_root() if repo_root is None else pathlib.Path(repo_root)
    tests_root = root / "tests"
    if not tests_root.exists():
        return ()
    return tuple(
        sorted(
            _normal_repo_path_text(path.relative_to(root))
            for path in tests_root.rglob("*.py")
            if _is_pytest_file(path)
        )
    )


def _path_contains(parent: str, child: str) -> bool:
    normalized_parent = parent.rstrip("/")
    normalized_child = child.rstrip("/")
    return normalized_child == normalized_parent or normalized_child.startswith(
        f"{normalized_parent}/"
    )


def _pytest_files_for_command(
    command: PytestShardCommand,
    repo_root: pathlib.Path | str | None = None,
) -> tuple[str, ...]:
    root = _repo_root() if repo_root is None else pathlib.Path(repo_root)
    all_files = discover_pytest_files(root)
    selected: set[str] = set()
    for path_text in command.paths:
        normalized = _normal_repo_path_text(path_text)
        path = root / normalized
        if path.is_file():
            selected.add(normalized)
            continue
        selected.update(
            test_file for test_file in all_files if _path_contains(normalized, test_file)
        )
    for ignore_text in command.ignores:
        normalized_ignore = _normal_repo_path_text(ignore_text)
        selected = {
            test_file
            for test_file in selected
            if not _path_contains(normalized_ignore, test_file)
        }
    return tuple(sorted(selected))


def pytest_shard_manifest(
    repo_root: pathlib.Path | str | None = None,
) -> dict[str, tuple[str, ...]]:
    manifest: dict[str, list[str]] = {phase: [] for phase in PYTEST_SHARD_PHASES}
    for phase in PYTEST_SHARD_PHASES:
        for command in PYTEST_SHARD_COMMANDS[phase]:
            manifest[phase].extend(_pytest_files_for_command(command, repo_root))
    return {phase: tuple(sorted(paths)) for phase, paths in manifest.items()}


def pytest_shard_membership(
    repo_root: pathlib.Path | str | None = None,
) -> dict[str, str]:
    membership: dict[str, str] = {}
    duplicates: list[str] = []
    for phase, paths in pytest_shard_manifest(repo_root).items():
        for path in paths:
            if path in membership:
                duplicates.append(path)
                continue
            membership[path] = phase
    if duplicates:
        duplicate_text = ", ".join(sorted(duplicates))
        raise ValueError(f"pytest shard duplicate test files: {duplicate_text}")
    return membership


def _is_pr142_handoff_readiness_validator_command(command: Sequence[str]) -> bool:
    return (
        len(command) > 1
        and pathlib.PurePath(command[1]).name == PR142_HANDOFF_READINESS_VALIDATOR_SCRIPT
    )


def _is_pr143_owner_override_currentization_validator_command(
    command: Sequence[str],
) -> bool:
    return (
        len(command) > 1
        and pathlib.PurePath(command[1]).name
        == PR143_OWNER_OVERRIDE_CURRENTIZATION_VALIDATOR_SCRIPT
    )


def _normal_path_text(value: pathlib.Path | str) -> str:
    return str(value).replace("\\", "/")


def _is_tracked_generated_output_path(value: pathlib.Path | str) -> bool:
    normalized = _normal_path_text(value)
    return any(
        normalized.startswith(prefix) for prefix in TRACKED_GENERATED_PATH_PREFIXES
    )


def _validation_generated_output(
    validation_dir: pathlib.Path,
    tracked_path: pathlib.Path | str,
) -> pathlib.Path:
    normalized = _normal_path_text(tracked_path)
    bucket = (
        "roadmap_generated"
        if normalized.startswith("docs/roadmap/generated/")
        else "master_plan_generated"
    )
    return validation_dir / bucket / pathlib.PurePosixPath(normalized).name


def _route_command_generated_outputs_to_temp(
    command: Sequence[str],
    validation_dir: pathlib.Path,
) -> list[str]:
    routed = [str(part) for part in command]
    for index, token in enumerate(routed[:-1]):
        if (
            token in {"--out", "--report-out"}
            or token.endswith("-out")
        ) and _is_tracked_generated_output_path(routed[index + 1]):
            routed[index + 1] = str(
                _validation_generated_output(validation_dir, routed[index + 1])
            )

    if len(routed) > 1:
        script_name = pathlib.PurePath(routed[1]).name
        if script_name in CHECK_ONLY_VALIDATOR_SCRIPTS and "--check-only" not in routed:
            routed.append("--check-only")
        if script_name in DEFAULT_GENERATED_OUTPUT_ARGS:
            flag, tracked_path = DEFAULT_GENERATED_OUTPUT_ARGS[script_name]
            if flag not in routed:
                routed.extend(
                    [
                        flag,
                        str(_validation_generated_output(validation_dir, tracked_path)),
                    ]
                )
    return routed


def _resolved_repo_path(repo_root: pathlib.Path, path_text: str) -> pathlib.Path:
    path = pathlib.Path(path_text)
    return path if path.is_absolute() else repo_root / path


def _json_currentness_payload(path: pathlib.Path) -> object:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        return {
            key: value
            for key, value in payload.items()
            if key not in GENERATED_REPORT_CURRENTNESS_IGNORED_FIELDS
        }
    return payload


def _tracked_report_has_volatile_currentness_context(path: pathlib.Path) -> bool:
    if path.suffix.lower() != ".json":
        return False
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    return isinstance(payload, dict) and any(
        key in payload for key in VOLATILE_GENERATED_REPORT_CURRENTNESS_FIELDS
    )


def _generated_reports_match_for_currentness(
    output_path: pathlib.Path,
    tracked_path: pathlib.Path,
) -> bool:
    if output_path.read_bytes() == tracked_path.read_bytes():
        return True
    if output_path.suffix.lower() != ".json" or tracked_path.suffix.lower() != ".json":
        return False
    try:
        return _json_currentness_payload(output_path) == _json_currentness_payload(
            tracked_path
        )
    except (OSError, json.JSONDecodeError):
        return False


def _routed_generated_output_currentness_failures(
    command: Sequence[str],
    repo_root: pathlib.Path,
) -> list[str]:
    if "--check-only" in command or len(command) <= 1:
        return []
    script_name = pathlib.PurePath(command[1]).name
    output_arg = GENERATED_REPORT_CURRENTNESS_OUTPUT_ARGS.get(script_name)
    if output_arg is None:
        return []
    flag, tracked_path_text = output_arg
    command_list = [str(part) for part in command]
    if flag not in command_list:
        return []
    output_index = command_list.index(flag) + 1
    if output_index >= len(command_list):
        return [f"TRACKED_GENERATED_REPORT_OUTPUT_ARG_MISSING: {script_name} {flag}"]

    output_text = command_list[output_index]
    if _is_tracked_generated_output_path(output_text):
        return []

    output_path = _resolved_repo_path(repo_root, output_text)
    tracked_path = _resolved_repo_path(repo_root, tracked_path_text)
    if not output_path.exists():
        return [
            "TRACKED_GENERATED_REPORT_TEMP_OUTPUT_MISSING: "
            f"{_normal_path_text(output_path)}"
        ]
    if not tracked_path.exists():
        return [
            "TRACKED_GENERATED_REPORT_MISSING: "
            f"{_normal_path_text(tracked_path_text)}"
        ]
    if _tracked_report_has_volatile_currentness_context(tracked_path):
        return []
    if not _generated_reports_match_for_currentness(output_path, tracked_path):
        return [
            "TRACKED_GENERATED_REPORT_STALE: "
            f"{_normal_path_text(tracked_path_text)} differs from validation temp output "
            f"{_normal_path_text(output_path)}"
        ]
    return []


def _git_stdout(repo_root: pathlib.Path, args: Sequence[str]) -> tuple[int, str, str]:
    completed = subprocess.run(
        ["git", *args],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )
    return completed.returncode, completed.stdout, completed.stderr


def _tracked_modified_paths(repo_root: pathlib.Path) -> set[str]:
    returncode, stdout, stderr = _git_stdout(repo_root, ["ls-files", "-m"])
    if returncode != 0:
        detail = stderr.strip() or stdout.strip() or "git ls-files -m failed"
        raise RuntimeError(detail)
    return {
        path.strip().replace("\\", "/")
        for path in stdout.splitlines()
        if path.strip()
    }


def _modified_file_snapshots(
    repo_root: pathlib.Path,
    paths: set[str],
) -> dict[str, bytes | None]:
    snapshots: dict[str, bytes | None] = {}
    for path_text in sorted(paths):
        path = repo_root / path_text
        snapshots[path_text] = path.read_bytes() if path.exists() else None
    return snapshots


def _restore_modified_file_snapshots(
    repo_root: pathlib.Path,
    snapshots: dict[str, bytes | None],
) -> tuple[str, ...]:
    restored: list[str] = []
    for path_text, content in sorted(snapshots.items()):
        path = repo_root / path_text
        if content is None:
            if path.exists() and path.is_file():
                path.unlink()
                restored.append(path_text)
            continue
        if path.exists() and path.read_bytes() == content:
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        restored.append(path_text)
    return tuple(restored)


def _restore_tracked_gate_side_effects(
    repo_root: pathlib.Path,
    initially_modified_paths: set[str],
) -> tuple[str, ...]:
    restore_paths = sorted(_tracked_modified_paths(repo_root) - initially_modified_paths)
    if not restore_paths:
        return ()

    returncode, stdout, stderr = _git_stdout(
        repo_root,
        [
            "restore",
            "--source=HEAD",
            "--worktree",
            "--",
            *restore_paths,
        ],
    )
    if returncode != 0:
        detail = stderr.strip() or stdout.strip() or "git restore failed"
        raise RuntimeError(detail)
    return tuple(restore_paths)


def build_validation_commands(
    validation_dir: pathlib.Path | str | None = None,
    pytest_basetemp: pathlib.Path | str | None = None,
) -> list[list[str]]:
    validation_dir = (
        _default_validation_dir()
        if validation_dir is None
        else pathlib.Path(validation_dir)
    )
    pytest_basetemp = (
        validation_dir / "run_validation_gates_pytest"
        if pytest_basetemp is None
        else pathlib.Path(pytest_basetemp)
    )
    section_manifest = validation_dir / "SectionManifest.json"
    traceability_report = validation_dir / "TraceabilityReport.json"
    first_pr_scope_report = validation_dir / "FirstPrScopeReport.json"
    row_family_currentization_report = (
        validation_dir / "AtomicRowsRowFamilySourceManifestCurrentization.report.json"
    )
    master_plan = pathlib.Path("docs") / "master_plan" / "QTT_MasterPlan_Current.md"

    commands = [
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
            "-c",
            PR138_NON_MUTATING_VALIDATION_SCRIPT,
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_atomicrows_row_family_source_manifest_currentization.py",
            ),
            "--repo-root",
            ".",
            "--out",
            str(row_family_currentization_report),
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_atomicrows_semantic_field_coverage_enrichment_plan.py",
            ),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_atomicrows_semantic_value_materialization_owner_authorization_gate.py",
            ),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate.py",
            ),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path("tools", "validate_qtt_owner_global_override_authority.py"),
            "--mode",
            "dev",
            "--repo-root",
            ".",
            "--out",
            _path(
                "docs",
                "master_plan",
                "generated",
                "QTTOwnerGlobalOverrideAuthority.report.json",
            ),
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_qtt_owner_global_override_directive_currentization_and_internal_gate_release.py",
            ),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_atomicrows_semantic_value_materialization_implementation_bridge.py",
            ),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_source_backed_classical_quantum_parameter_default_target_matrix.py",
            ),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_official_source_retrieval_target_pack_parameter_defaults.py",
            ),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_grand_global_debug_logical_consistency_audit.py",
            ),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_controlled_official_source_capture_candidate_packets.py",
            ),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_pr153r_redo_external_source_value_capture_targets.py",
            ),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_pr153s_source_value_capture_closure_classifier.py",
            ),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_atomicrows_parameter_default_value_materialization_gate.py",
            ),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_agent_consumable_parameter_default_registry.py",
            ),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_agent_default_binding_universal_intake_gate.py",
            ),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_pr157_pr154_atomicrows_completion_materialization_bridge.py",
            ),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_pr158_owner_response_selection_readiness_bridge.py",
            ),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_pr159_official_source_completion_bridge.py",
            ),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_pr160_split_reclassification_route_closure.py",
            ),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_pr159r_source_locator_value_capture.py",
            ),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_pr159s_open_intake_completion.py",
            ),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_pr161a_atomicrows_pr154_value_state_materialization.py",
            ),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_pr161b_master_plan_residual_candidate_coverage.py",
            ),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_pr161c_qku_residual_candidate_assimilation.py",
            ),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_pr161d_qku_candidate_quality_replay_paper_prioritization.py",
            ),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_pr161e_replay_paper_outcome_capture_scenario_learning.py",
            ),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_pr161f_replay_paper_executor_input_run_artifact_generation.py",
            ),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_pr162_safe_nonlive_replay_paper_data_adapter_quantum_forward_bridge.py",
            ),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_pr162a_safe_repo_local_nonlive_dataset_materialization_authority_gate.py",
            ),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_pr162b_qku_formula_algorithm_solver_market_scope_materialization.py",
            ),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_pr162c_multisource_safe_nonlive_dataset_expansion_strict_qku_coverage.py",
            ),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_pr162d_aggressive_qku_candidate_materialization_agent_routing.py",
            ),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_pr162r_a_replay_paper_executability_classification_audit.py",
            ),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_pr162d_r2a_real_formulations.py",
            ),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_pr162r_generic_replay_paper_adapter_rerun.py",
            ),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_pr162r_b_replay_paper_data_binding_completion.py",
            ),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_pr163_generic_paper_adapter_capture_framework.py",
            ),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_pr163_b_paired_replay_paper_concurrent_executor.py",
            ),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_pr164_review_provenance_qku_canonical_coverage_audit.py",
            ),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_pr163_c_pretrade_infrastructure_rejection_remediation.py",
            ),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_pr165_evidence_backed_scoring_ranking.py",
            ),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_qtt_agent_role_operating_charter_registry.py",
            ),
            "--mode",
            "dev",
            "--repo-root",
            ".",
            "--out",
            _path(
                "docs",
                "master_plan",
                "generated",
                "QTTAgentRoleOperatingCharterReport.json",
            ),
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_qtt_algorithm_formula_family_registry.py",
            ),
            "--mode",
            "dev",
            "--repo-root",
            ".",
            "--out",
            _path(
                "docs",
                "master_plan",
                "generated",
                "QTTAlgorithmFormulaFamilyReport.json",
            ),
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_qtt_agent_algorithm_binding_registry.py",
            ),
            "--mode",
            "dev",
            "--repo-root",
            ".",
            "--out",
            _path(
                "docs",
                "master_plan",
                "generated",
                "QTTAgentAlgorithmBindingReport.json",
            ),
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_qtt_agent_algorithm_consumer_gate.py",
            ),
            "--mode",
            "dev",
            "--repo-root",
            ".",
            "--out",
            _path(
                "docs",
                "master_plan",
                "generated",
                "QTTAgentAlgorithmConsumerGate.report.json",
            ),
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_qtt_agent_algorithm_cumulative_readiness_gate.py",
            ),
            "--mode",
            "dev",
            "--repo-root",
            ".",
            "--out",
            _path(
                "docs",
                "master_plan",
                "generated",
                "QTTAgentAlgorithmCumulativeReadinessGate.report.json",
            ),
        ],
        [
            sys.executable,
            _path("tools", "validate_qtt_agent_algorithm_command_matrix.py"),
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
            _path("tools", "validate_source_evidence_retrieval_executor.py"),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path("tools", "validate_source_evidence_acceptance.py"),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path("tools", "validate_accepted_source_to_connector_semantic_binding.py"),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path("tools", "validate_source_revalidation_scheduler.py"),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path("tools", "validate_connector_semantic_binding_implementation_gate.py"),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path("tools", "validate_per_venue_execution_lifecycle_model.py"),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path("tools", "validate_cross_venue_execution_normalization_binding.py"),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path("tools", "runtime_cash_component_field_map_validate.py"),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path("tools", "private_state_read_receipt_gate_validate.py"),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path("tools", "credential_alias_secret_no_capture_readiness_validate.py"),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path("tools", "venue_market_data_ingest_adapters_validate.py"),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path("tools", "orderbook_event_state_snapshot_builder_validate.py"),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path("tools", "runtime_resolver_snapshot_executor_validate.py"),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path("tools", "validate_historical_dataset_policy_literal_drift.py"),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path("tools", "validate_historical_dataset_digest_and_loader.py"),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path("tools", "validate_pr136_roadmap_policy_literal_drift.py"),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path("tools", "validate_pr136_day1_launch_readiness_roadmap.py"),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path("tools", "validate_pr137_generated_integrity_authority_boundary.py"),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path("tools", "validate_pr137_launch_readiness_dependency_controller.py"),
            "--repo-root",
            ".",
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
            _path("tools", "build_atomicrows_parameter_lifecycle_report.py"),
        ],
        [
            sys.executable,
            _path("tools", "validate_atomicrows_parameter_lifecycle.py"),
            "--mode",
            "dev",
        ],
        [
            sys.executable,
            _path("tools", "validate_atomicrows_lifecycle_consumer_gate.py"),
            "--mode",
            "dev",
            "--out",
            _path(
                "docs",
                "master_plan",
                "generated",
                "AtomicRowsLifecycleConsumerGate.report.json",
            ),
        ],
        [
            sys.executable,
            _path("tools", "validate_atomicrows_lifecycle_promotion_receipt_gate.py"),
            "--mode",
            "dev",
            "--out",
            _path(
                "docs",
                "master_plan",
                "generated",
                "AtomicRowsLifecyclePromotionReceiptGate.report.json",
            ),
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_atomicrows_lifecycle_registry_mutation_guard.py",
            ),
            "--mode",
            "dev",
            "--out",
            _path(
                "docs",
                "master_plan",
                "generated",
                "AtomicRowsLifecycleRegistryMutationGuard.report.json",
            ),
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_atomicrows_lifecycle_cumulative_readiness_gate.py",
            ),
            "--mode",
            "dev",
            "--out",
            _path(
                "docs",
                "master_plan",
                "generated",
                "AtomicRowsLifecycleCumulativeReadinessGate.report.json",
            ),
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_atomicrows_lifecycle_gate_command_matrix.py",
            ),
            "--mode",
            "dev",
            "--out",
            _path(
                "docs",
                "master_plan",
                "generated",
                "AtomicRowsLifecycleGateCommandMatrix.json",
            ),
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_atomicrows_parameter_agent_binding_registry.py",
            ),
            "--mode",
            "dev",
            "--out",
            _path(
                "docs",
                "master_plan",
                "generated",
                "AtomicRowsParameterAgentBindingReport.json",
            ),
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_atomicrows_parameter_agent_binding_consumer_gate.py",
            ),
            "--mode",
            "dev",
            "--out",
            _path(
                "docs",
                "master_plan",
                "generated",
                "AtomicRowsParameterAgentBindingConsumerGate.report.json",
            ),
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_atomicrows_parameter_agent_binding_cumulative_readiness_gate.py",
            ),
            "--mode",
            "dev",
            "--out",
            _path(
                "docs",
                "master_plan",
                "generated",
                "AtomicRowsParameterAgentBindingCumulativeReadinessGate.report.json",
            ),
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_atomicrows_parameter_agent_binding_command_matrix.py",
            ),
            "--mode",
            "dev",
            "--out",
            _path(
                "docs",
                "master_plan",
                "generated",
                "AtomicRowsParameterAgentBindingCommandMatrix.json",
            ),
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_atomicrows_research_provenance_evidence_tier_classification.py",
            ),
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_atomicrows_owner_submitted_research_source_intake_registry.py",
            ),
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_atomicrows_research_source_to_candidate_family_gate.py",
            ),
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_atomicrows_parameter_stack_role_taxonomy.py",
            ),
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_atomicrows_parameter_stack_completeness_gate.py",
            ),
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_atomicrows_parameter_stack_compatibility_gate.py",
            ),
        ],
        [
            sys.executable,
            _path("tools", "validate_edge_parameter_stack_selection_packet.py"),
        ],
        [
            sys.executable,
            _path("tools", "validate_qtt_trade_context_packet.py"),
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_atomicrows_parameter_selection_universe_registry.py",
            ),
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_atomicrows_parameter_selection_universe_consumer_gate.py",
            ),
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_trade_context_selection_universe_routing_gate.py",
            ),
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_quantum_applicability_classification_registry.py",
            ),
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_owner_quantum_priority_policy_registry.py",
            ),
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_parameter_algorithm_scoring_policy_registry.py",
            ),
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_parameter_stack_scoring_and_ranking_gate.py",
            ),
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_quantum_classical_optimizer_arbitration_gate.py",
            ),
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_candidate_parameter_stack_generation_gate.py",
            ),
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_trade_context_parameter_stack_selection_gate.py",
            ),
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_selected_parameter_stack_handoff_packet.py",
            ),
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_replay_paper_candidate_stack_competition_gate.py",
            ),
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_dual_result_review_for_parameter_stacks.py",
            ),
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_owner_live_promotion_review_for_parameter_stacks.py",
            ),
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_owner_approval_request_queue_registry.py",
            ),
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_owner_override_receipt_authoring_gate.py",
            ),
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_owner_dashboard_approval_menu_schema.py",
            ),
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_owner_dashboard_approval_static_screen_contract.py",
            ),
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_atomicrows_full_bundle_row_expansion_plan.py",
            ),
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_atomicrows_bundle_row_family_source_files.py",
            ),
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_atomicrows_bundle_builder_deterministic_assembly_gate.py",
            ),
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_atomicrows_sha_system_dormancy_state_contract.py",
            ),
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_qtt_final_readiness_dependency_policy_contract.py",
            ),
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_qtt_active_non_sha_day1_gate_state_registry_contract.py",
            ),
        ],
        [
            sys.executable,
            _path("tools", "validate_qtt_pr_identity_roster.py"),
        ],
        [
            sys.executable,
            _path("tools", "validate_qtt_roadmap_execution_state_controller.py"),
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_atomicrows_bundle_sha_freeze_authority_gate.py",
            ),
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_atomicrows_exact_row_authority_classifier_bridge.py",
            ),
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_atomicrows_exact_row_expansion_manifest.py",
            ),
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_atomicrows_owner_approved_exact_15_family_count_distribution.py",
            ),
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_atomicrows_exact_row_generator_dry_run_manifest.py",
            ),
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_atomicrows_repair_chain_grand_debug_logic_audit_manifest.py",
            ),
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_atomicrows_exact_row_source_materialization_manifest.py",
            ),
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_atomicrows_exact_row_agent_family_eligibility_matrix.py",
            ),
        ],
        [
            sys.executable,
            _path("tools", "validate_atomicrows_bundle_materialization_manifest.py"),
        ],
        [
            sys.executable,
            _path("tools", "validate_atomicrows_bundle_boundary_state_contract.py"),
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_atomicrows_sha_freeze_final_readiness_state_contract.py",
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
            _path(
                "tools",
                "validate_source_fact_binding_connector_semantic_readiness_static.py",
            ),
            "--repo-root",
            ".",
            "--source-to-connector-schema",
            _path(
                "schemas",
                "source_fact_binding_readiness",
                "stage1_source_to_connector_field_binding_matrix.schema.json",
            ),
            "--source-to-connector-fixture",
            _path(
                "tests",
                "fixtures",
                "source_fact_binding_readiness",
                "synthetic_stage1_source_to_connector_field_binding_matrix.v1.fixture.json",
            ),
            "--connector-target-schema",
            _path(
                "schemas",
                "source_fact_binding_readiness",
                "stage1_connector_semantic_target_field_matrix.schema.json",
            ),
            "--connector-target-fixture",
            _path(
                "tests",
                "fixtures",
                "source_fact_binding_readiness",
                "synthetic_stage1_connector_semantic_target_field_matrix.v1.fixture.json",
            ),
            "--gate-report-schema",
            _path(
                "schemas",
                "source_fact_binding_readiness",
                "stage1_connector_semantic_readiness_gate_report.schema.json",
            ),
            "--gate-report-fixture",
            _path(
                "tests",
                "fixtures",
                "source_fact_binding_readiness",
                "synthetic_stage1_connector_semantic_readiness_gate_report.v1.fixture.json",
            ),
        ],
        [
            sys.executable,
            _path("tools", "source_evidence_acceptance_consumer_contract_check.py"),
            "--repo-root",
            ".",
            "--consumer-contract-schema",
            _path(
                "src",
                "qtt",
                "source_evidence",
                "acceptance",
                "accepted_source_evidence_consumer_contract.schema.json",
            ),
            "--target-field-ledger-schema",
            _path(
                "src",
                "qtt",
                "source_evidence",
                "acceptance",
                "stage1_target_field_acceptance_ledger_record.schema.json",
            ),
            "--export-record-schema",
            _path(
                "src",
                "qtt",
                "source_evidence",
                "acceptance",
                "stage1_accepted_source_evidence_export_record.schema.json",
            ),
            "--fixture",
            _path(
                "tests",
                "fixtures",
                "source_evidence",
                "acceptance_consumer_contract",
                "synthetic_accepted_source_evidence_consumer_contract_records.v1.fixture.json",
            ),
        ],
        [
            sys.executable,
            _path("tools", "stage1_connector_semantic_binding_ledger_check.py"),
            "--repo-root",
            ".",
            "--ledger-schema",
            _path(
                "src",
                "qtt",
                "stage1_prediction_markets",
                "connector_semantic_binding",
                "stage1_connector_semantic_binding_ledger_record.schema.json",
            ),
            "--canonicalization-schema",
            _path(
                "src",
                "qtt",
                "stage1_prediction_markets",
                "connector_semantic_binding",
                "stage1_connector_semantic_value_canonicalization.schema.json",
            ),
            "--consumer-contract-schema",
            _path(
                "src",
                "qtt",
                "stage1_prediction_markets",
                "connector_semantic_binding",
                "stage1_connector_semantic_binding_consumer_contract.schema.json",
            ),
            "--fixture",
            _path(
                "tests",
                "fixtures",
                "source_evidence",
                "connector_semantic_binding",
                "synthetic_stage1_connector_semantic_binding_contracts.v1.fixture.json",
            ),
            "--out",
            _path(
                "docs",
                "master_plan",
                "generated",
                "Stage1ConnectorSemanticBindingLedgerCheck.report.json",
            ),
        ],
        [
            sys.executable,
            _path("tools", "stage1_runtime_resolver_snapshot_contract_check.py"),
            "--repo-root",
            ".",
            "--input-lock-schema",
            _path(
                "src",
                "qtt",
                "stage1_prediction_markets",
                "runtime_resolver",
                "stage1_runtime_resolver_snapshot_input_lock.schema.json",
            ),
            "--manifest-schema",
            _path(
                "src",
                "qtt",
                "stage1_prediction_markets",
                "runtime_resolver",
                "stage1_runtime_resolver_snapshot_manifest.schema.json",
            ),
            "--consumer-contract-schema",
            _path(
                "src",
                "qtt",
                "stage1_prediction_markets",
                "runtime_resolver",
                "stage1_runtime_resolver_consumer_contract.schema.json",
            ),
            "--gate-report-schema",
            _path(
                "src",
                "qtt",
                "stage1_prediction_markets",
                "runtime_resolver",
                "stage1_runtime_resolver_snapshot_gate_report.schema.json",
            ),
            "--fixture",
            _path(
                "tests",
                "fixtures",
                "source_evidence",
                "runtime_resolver",
                "synthetic_stage1_runtime_resolver_snapshot_contracts.v1.fixture.json",
            ),
            "--out",
            _path(
                "docs",
                "master_plan",
                "generated",
                "Stage1RuntimeResolverSnapshotContractCheck.report.json",
            ),
        ],
        [
            sys.executable,
            _path(
                "tools",
                "stage1_runtime_resolver_to_replay_paper_handoff_check.py",
            ),
            "--repo-root",
            ".",
            "--consumer-allowlist-schema",
            _path(
                "src",
                "qtt",
                "stage1_prediction_markets",
                "runtime_resolver_snapshot",
                "stage1_runtime_resolver_snapshot_consumer_allowlist.schema.json",
            ),
            "--handoff-contract-schema",
            _path(
                "src",
                "qtt",
                "stage1_prediction_markets",
                "runtime_resolver_snapshot",
                "stage1_runtime_resolver_to_replay_paper_handoff_contract.schema.json",
            ),
            "--handoff-report-schema",
            _path(
                "src",
                "qtt",
                "stage1_prediction_markets",
                "runtime_resolver_snapshot",
                "stage1_runtime_resolver_to_replay_paper_handoff_report.schema.json",
            ),
            "--fixture",
            _path(
                "tests",
                "fixtures",
                "source_evidence",
                "runtime_resolver_snapshot",
                "synthetic_stage1_runtime_resolver_to_replay_paper_handoff.v1.fixture.json",
            ),
            "--out",
            _path(
                "docs",
                "master_plan",
                "generated",
                "Stage1RuntimeResolverToReplayPaperHandoff.report.json",
            ),
        ],
        [
            sys.executable,
            _path("tools", "stage1_concurrent_replay_paper_contract_check.py"),
            "--repo-root",
            ".",
            "--input-identity-schema",
            _path(
                "src",
                "qtt",
                "stage1_prediction_markets",
                "replay_paper",
                "concurrent_replay_paper_input_identity.schema.json",
            ),
            "--replay-lane-schema",
            _path(
                "src",
                "qtt",
                "stage1_prediction_markets",
                "replay_paper",
                "concurrent_replay_lane_contract.schema.json",
            ),
            "--paper-lane-schema",
            _path(
                "src",
                "qtt",
                "stage1_prediction_markets",
                "replay_paper",
                "concurrent_paper_lane_contract.schema.json",
            ),
            "--replay-result-boundary-schema",
            _path(
                "src",
                "qtt",
                "stage1_prediction_markets",
                "replay_paper",
                "replay_result_packet_boundary.schema.json",
            ),
            "--paper-result-boundary-schema",
            _path(
                "src",
                "qtt",
                "stage1_prediction_markets",
                "replay_paper",
                "paper_result_packet_boundary.schema.json",
            ),
            "--gate-report-schema",
            _path(
                "src",
                "qtt",
                "stage1_prediction_markets",
                "replay_paper",
                "concurrent_replay_paper_execution_gate_report.schema.json",
            ),
            "--fixture",
            _path(
                "tests",
                "fixtures",
                "source_evidence",
                "replay_paper",
                "synthetic_concurrent_replay_paper_contracts.v1.fixture.json",
            ),
            "--out",
            _path(
                "docs",
                "master_plan",
                "generated",
                "Stage1ConcurrentReplayPaperContractCheck.report.json",
            ),
        ],
        [
            sys.executable,
            _path("tools", "stage1_dual_result_review_contract_check.py"),
            "--repo-root",
            ".",
            "--input-contract-schema",
            _path(
                "src",
                "qtt",
                "stage1_prediction_markets",
                "dual_result_review",
                "stage1_dual_result_review_input_contract.schema.json",
            ),
            "--comparison-matrix-schema",
            _path(
                "src",
                "qtt",
                "stage1_prediction_markets",
                "dual_result_review",
                "stage1_replay_paper_comparison_matrix.schema.json",
            ),
            "--gate-report-schema",
            _path(
                "src",
                "qtt",
                "stage1_prediction_markets",
                "dual_result_review",
                "stage1_dual_result_review_gate_report.schema.json",
            ),
            "--owner-handoff-block-schema",
            _path(
                "src",
                "qtt",
                "stage1_prediction_markets",
                "dual_result_review",
                "stage1_owner_live_promotion_handoff_block.schema.json",
            ),
            "--fixture",
            _path(
                "tests",
                "fixtures",
                "source_evidence",
                "dual_result_review",
                "synthetic_stage1_dual_result_review_contracts.v1.fixture.json",
            ),
            "--out",
            _path(
                "docs",
                "master_plan",
                "generated",
                "Stage1DualResultReviewContractCheck.report.json",
            ),
        ],
        [
            sys.executable,
            _path("tools", "stage1_owner_live_promotion_review_contract_check.py"),
            "--repo-root",
            ".",
            "--input-contract-schema",
            _path(
                "src",
                "qtt",
                "stage1_prediction_markets",
                "owner_live_promotion_review",
                "stage1_owner_live_promotion_review_input_contract.schema.json",
            ),
            "--owner-approval-receipt-boundary-schema",
            _path(
                "src",
                "qtt",
                "stage1_prediction_markets",
                "owner_live_promotion_review",
                "stage1_owner_approval_receipt_boundary.schema.json",
            ),
            "--gate-report-schema",
            _path(
                "src",
                "qtt",
                "stage1_prediction_markets",
                "owner_live_promotion_review",
                "stage1_owner_live_promotion_review_gate_report.schema.json",
            ),
            "--handoff-block-schema",
            _path(
                "src",
                "qtt",
                "stage1_prediction_markets",
                "owner_live_promotion_review",
                "stage1_three_venue_canary_eligibility_handoff_block.schema.json",
            ),
            "--fixture",
            _path(
                "tests",
                "fixtures",
                "source_evidence",
                "owner_live_promotion_review",
                "synthetic_stage1_owner_live_promotion_review_contracts.v1.fixture.json",
            ),
            "--out",
            _path(
                "docs",
                "master_plan",
                "generated",
                "Stage1OwnerLivePromotionReviewContractCheck.report.json",
            ),
        ],
        [
            sys.executable,
            _path("tools", "stage1_three_venue_canary_eligibility_contract_check.py"),
            "--repo-root",
            ".",
            "--input-contract-schema",
            _path(
                "src",
                "qtt",
                "stage1_prediction_markets",
                "three_venue_canary_eligibility",
                "stage1_three_venue_canary_eligibility_input_contract.schema.json",
            ),
            "--readiness-matrix-schema",
            _path(
                "src",
                "qtt",
                "stage1_prediction_markets",
                "three_venue_canary_eligibility",
                "stage1_three_venue_platform_readiness_matrix.schema.json",
            ),
            "--handoff-schema",
            _path(
                "src",
                "qtt",
                "stage1_prediction_markets",
                "three_venue_canary_eligibility",
                "stage1_owner_review_to_canary_eligibility_handoff.schema.json",
            ),
            "--gate-report-schema",
            _path(
                "src",
                "qtt",
                "stage1_prediction_markets",
                "three_venue_canary_eligibility",
                "stage1_three_venue_canary_eligibility_gate_report.schema.json",
            ),
            "--execution-block-schema",
            _path(
                "src",
                "qtt",
                "stage1_prediction_markets",
                "three_venue_canary_eligibility",
                "stage1_limited_live_canary_execution_block.schema.json",
            ),
            "--fixture",
            _path(
                "tests",
                "fixtures",
                "source_evidence",
                "three_venue_canary_eligibility",
                "synthetic_stage1_three_venue_canary_eligibility_contracts.v1.fixture.json",
            ),
            "--out",
            _path(
                "docs",
                "master_plan",
                "generated",
                "Stage1ThreeVenueCanaryEligibilityContractCheck.report.json",
            ),
        ],
        [
            sys.executable,
            _path("tools", "build_master_plan_section_coverage_report.py"),
        ],
        [
            sys.executable,
            _path("tools", "validate_master_plan_section_coverage.py"),
            "--mode",
            "dev",
        ],
        [
            sys.executable,
            _path("tools", "validate_qtt_master_plan_section_coverage_triage_routes.py"),
        ],
        [
            sys.executable,
            _path("tools", "validate_qtt_master_plan_section_roadmap_crosswalk.py"),
        ],
        [
            sys.executable,
            _path("tools", "validate_qtt_master_plan_section_coverage_command_matrix.py"),
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
            _path(
                "tests",
                "source_evidence",
                "test_controlled_official_source_capture_candidate_packets.py",
            ),
            "-q",
            PYTEST_DURATIONS_ARG,
            "--basetemp",
            str(pytest_basetemp),
        ],
        [
            sys.executable,
            _path("tools", "run_pytest_fresh_basetemp.py"),
            "tests",
            "-q",
            "--ignore",
            _path(
                "tests",
                "source_evidence",
                "test_controlled_official_source_capture_candidate_packets.py",
            ),
            PYTEST_DURATIONS_ARG,
            "--basetemp",
            str(pytest_basetemp),
        ],
    ]
    return [
        _route_command_generated_outputs_to_temp(command, pathlib.Path(validation_dir))
        for command in commands
    ]


def build_fast_preflight_commands() -> list[list[str]]:
    return [
        [
            sys.executable,
            _path("tools", "validate_grand_global_debug_logical_consistency_audit.py"),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path("tools", "validate_ci_branch_context_matrix.py"),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path("tools", "validate_repair_pr_changed_file_scope.py"),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path("tools", "validate_nested_validator_contracts.py"),
            "--repo-root",
            ".",
        ],
    ]


def build_deterministic_validator_commands(
    validation_dir: pathlib.Path | str | None = None,
    pytest_basetemp: pathlib.Path | str | None = None,
) -> list[list[str]]:
    return [
        command
        for command in build_validation_commands(validation_dir, pytest_basetemp)
        if not _command_uses_pytest_helper(command)
        and _command_script_name(command) not in FAST_PREFLIGHT_SCRIPT_NAMES
    ]


def _build_pytest_command(
    command: PytestShardCommand,
    pytest_basetemp: pathlib.Path,
) -> list[str]:
    built = [
        sys.executable,
        _path("tools", PYTEST_FRESH_BASETEMP_SCRIPT),
        *command.paths,
        "-q",
    ]
    for ignored in command.ignores:
        built.extend(["--ignore", ignored])
    built.extend([PYTEST_DURATIONS_ARG, "--basetemp", str(pytest_basetemp)])
    return built


def build_pytest_shard_commands(
    phase: str,
    pytest_basetemp: pathlib.Path | str | None = None,
) -> list[list[str]]:
    if phase not in PYTEST_SHARD_COMMANDS:
        raise ValueError(f"unknown pytest shard phase: {phase}")
    basetemp = (
        _default_validation_dir() / "run_validation_gates_pytest"
        if pytest_basetemp is None
        else pathlib.Path(pytest_basetemp)
    )
    return [_build_pytest_command(command, basetemp) for command in PYTEST_SHARD_COMMANDS[phase]]


def build_post_validation_commands() -> list[list[str]]:
    return [
        [sys.executable, "-m", "compileall", "-q", "tools", "tests", "src"],
        ["git", "diff", "--check"],
        [
            "git",
            "diff",
            "--exit-code",
            "--",
            _path("docs", "master_plan", "QTT_MasterPlan_Current.md"),
        ],
        [sys.executable, "-c", ATOMICROWS_BUNDLE_CHECK_SCRIPT],
    ]


def build_phase_commands(
    phase: str = ALL_PHASE,
    validation_dir: pathlib.Path | str | None = None,
    pytest_basetemp: pathlib.Path | str | None = None,
) -> list[list[str]]:
    if phase == ALL_PHASE:
        commands: list[list[str]] = []
        for ordered_phase in ORDERED_PHASES:
            commands.extend(
                build_phase_commands(
                    ordered_phase,
                    validation_dir=validation_dir,
                    pytest_basetemp=pytest_basetemp,
                )
            )
        return commands
    if phase == FAST_PREFLIGHT_PHASE:
        return build_fast_preflight_commands()
    if phase == DETERMINISTIC_VALIDATORS_PHASE:
        return build_deterministic_validator_commands(validation_dir, pytest_basetemp)
    if phase in PYTEST_SHARD_PHASES:
        return build_pytest_shard_commands(phase, pytest_basetemp)
    if phase == POST_VALIDATION_PHASE:
        return build_post_validation_commands()
    raise ValueError(f"unknown validation phase: {phase}")


def build_phase_manifest(
    validation_dir: pathlib.Path | str | None = None,
    pytest_basetemp: pathlib.Path | str | None = None,
) -> list[dict[str, object]]:
    manifest: list[dict[str, object]] = []
    for phase in ORDERED_PHASES:
        commands = build_phase_commands(
            phase,
            validation_dir=validation_dir,
            pytest_basetemp=pytest_basetemp,
        )
        manifest.append(
            {
                "phase": phase,
                "command_count": len(commands),
                "commands": [list(command) for command in commands],
            }
        )
    return manifest


def _timing_entry_payload(entry: TimingEntry) -> dict[str, object]:
    return {
        "phase": entry.phase,
        "command_index": entry.command_index,
        "command": entry.command,
        "elapsed_seconds": entry.elapsed_seconds,
        "returncode": entry.returncode,
    }


def _slowest_timing_entries(entries: Sequence[TimingEntry]) -> list[TimingEntry]:
    return sorted(entries, key=lambda entry: entry.elapsed_seconds, reverse=True)[
        :SLOWEST_ENTRY_LIMIT
    ]


def _print_timing_summary(
    entries: Sequence[TimingEntry],
    *,
    phase: str,
    total_elapsed_seconds: float,
) -> None:
    print(
        f"QTT_VALIDATION_TIMING_TOTAL phase={phase} "
        f"elapsed_seconds={total_elapsed_seconds:.3f}",
        flush=True,
    )
    print(
        f"QTT_VALIDATION_TIMING_SLOWEST_TOP_{SLOWEST_ENTRY_LIMIT} phase={phase}",
        flush=True,
    )
    for rank, entry in enumerate(_slowest_timing_entries(entries), start=1):
        print(
            "QTT_VALIDATION_TIMING_SLOWEST "
            f"rank={rank} phase={entry.phase} "
            f"command_index={entry.command_index} "
            f"elapsed_seconds={entry.elapsed_seconds:.3f} "
            f"returncode={entry.returncode} "
            f"command={subprocess.list2cmdline(entry.command)}",
            flush=True,
        )


def _timing_report_path_allowed(
    report_path: pathlib.Path,
    *,
    repo_root: pathlib.Path | None,
) -> bool:
    normalized = _normal_path_text(report_path)
    if repo_root is not None:
        try:
            normalized = _normal_path_text(report_path.resolve().relative_to(repo_root))
        except ValueError:
            normalized = _normal_path_text(report_path)
    return not any(
        normalized.startswith(prefix) for prefix in TRACKED_GENERATED_PATH_PREFIXES
    )


def _write_timing_report(
    report_path: pathlib.Path,
    *,
    phase: str,
    entries: Sequence[TimingEntry],
    total_elapsed_seconds: float,
    repo_root: pathlib.Path | None,
) -> None:
    if not _timing_report_path_allowed(report_path, repo_root=repo_root):
        raise ValueError(
            "timing report path is inside a tracked generated authority path: "
            f"{_normal_path_text(report_path)}"
        )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": TIMING_SCHEMA_VERSION,
        "generated_at_utc": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "phase": phase,
        "command_entries": [_timing_entry_payload(entry) for entry in entries],
        "total_elapsed_seconds": total_elapsed_seconds,
        "slowest_entries": [
            _timing_entry_payload(entry) for entry in _slowest_timing_entries(entries)
        ],
    }
    report_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def run_commands(
    commands: Sequence[Sequence[str]],
    repo_root: pathlib.Path | None = None,
    *,
    phase: str = ALL_PHASE,
    timing_report_path: pathlib.Path | None = None,
) -> int:
    cleanup_repo_root = (
        _RUN_COMMANDS_CLEANUP_REPO_ROOT if repo_root is None else repo_root
    )
    timing_entries: list[TimingEntry] = []
    total_started = time.perf_counter()

    def finish(returncode: int) -> int:
        total_elapsed_seconds = time.perf_counter() - total_started
        _print_timing_summary(
            timing_entries,
            phase=phase,
            total_elapsed_seconds=total_elapsed_seconds,
        )
        if timing_report_path is not None:
            try:
                _write_timing_report(
                    timing_report_path,
                    phase=phase,
                    entries=timing_entries,
                    total_elapsed_seconds=total_elapsed_seconds,
                    repo_root=cleanup_repo_root,
                )
            except ValueError as exc:
                print(str(exc), file=sys.stderr, flush=True)
                return 2
        if returncode == 0:
            print(f"{PHASE_SUCCESS_MARKER_PREFIX} phase={phase}", flush=True)
            print(SUCCESS_MARKER, flush=True)
        return returncode

    initially_modified_paths: set[str] = set()
    initially_modified_snapshots: dict[str, bytes | None] = {}
    if cleanup_repo_root is not None:
        initially_modified_paths = _tracked_modified_paths(cleanup_repo_root)
        initially_modified_snapshots = _modified_file_snapshots(
            cleanup_repo_root,
            initially_modified_paths,
        )

    def restore_gate_side_effects() -> None:
        if cleanup_repo_root is None:
            return
        _restore_tracked_gate_side_effects(
            cleanup_repo_root,
            initially_modified_paths,
        )
        _restore_modified_file_snapshots(
            cleanup_repo_root,
            initially_modified_snapshots,
        )

    for command_index, command in enumerate(commands, start=1):
        command_list = list(command)
        if cleanup_repo_root is not None and (
            _is_pr142_handoff_readiness_validator_command(command_list)
            or _is_pr143_owner_override_currentization_validator_command(command_list)
            or _is_final_pytest_command(command_list)
        ):
            try:
                restore_gate_side_effects()
            except RuntimeError as exc:
                print(str(exc), file=sys.stderr, flush=True)
                return finish(1)
        print(subprocess.list2cmdline(command_list), flush=True)
        command_started = time.perf_counter()
        completed = subprocess.run(command_list)
        elapsed_seconds = time.perf_counter() - command_started
        timing_entries.append(
            TimingEntry(
                phase=phase,
                command_index=command_index,
                command=command_list,
                elapsed_seconds=elapsed_seconds,
                returncode=completed.returncode,
            )
        )
        print(
            "QTT_VALIDATION_TIMING_COMMAND "
            f"phase={phase} command_index={command_index} "
            f"elapsed_seconds={elapsed_seconds:.3f} "
            f"returncode={completed.returncode}",
            flush=True,
        )
        if completed.returncode != 0:
            if cleanup_repo_root is not None and _is_final_pytest_command(
                command_list
            ):
                try:
                    restore_gate_side_effects()
                except RuntimeError as exc:
                    print(str(exc), file=sys.stderr, flush=True)
            return finish(completed.returncode)
        if cleanup_repo_root is not None and _is_final_pytest_command(command_list):
            try:
                restore_gate_side_effects()
            except RuntimeError as exc:
                print(str(exc), file=sys.stderr, flush=True)
                return finish(1)
        if cleanup_repo_root is not None:
            currentness_failures = _routed_generated_output_currentness_failures(
                command_list,
                cleanup_repo_root,
            )
            if currentness_failures:
                for failure in currentness_failures:
                    print(failure, file=sys.stderr, flush=True)
                return finish(1)

    return finish(0)


def _run_commands_accepts_repo_root() -> bool:
    try:
        signature = inspect.signature(run_commands)
    except (TypeError, ValueError):
        return True
    parameters = signature.parameters.values()
    return any(
        parameter.kind is inspect.Parameter.VAR_KEYWORD
        or parameter.name == "repo_root"
        for parameter in parameters
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--phase",
        choices=VALIDATION_PHASES,
        default=ALL_PHASE,
        help="Validation phase to run; default runs the full split validation plan.",
    )
    parser.add_argument(
        "--timing-report",
        type=pathlib.Path,
        help="Optional untracked JSON timing report path.",
    )
    args = parser.parse_args(sys.argv[1:] if argv is None else list(argv))
    repo_root = _repo_root()
    timing_report_path = args.timing_report
    if timing_report_path is not None and not timing_report_path.is_absolute():
        timing_report_path = repo_root / timing_report_path
    if timing_report_path is not None and not _timing_report_path_allowed(
        timing_report_path,
        repo_root=repo_root,
    ):
        print(
            "timing report path is inside a tracked generated authority path: "
            f"{_normal_path_text(timing_report_path)}",
            file=sys.stderr,
        )
        return 2
    tmp_parent = repo_root / ".tmp"
    tmp_parent.mkdir(parents=True, exist_ok=True)
    global _RUN_COMMANDS_CLEANUP_REPO_ROOT
    previous_cleanup_repo_root = _RUN_COMMANDS_CLEANUP_REPO_ROOT
    _RUN_COMMANDS_CLEANUP_REPO_ROOT = repo_root
    try:
        with tempfile.TemporaryDirectory(prefix="qtt_validation_gates_") as temp_dir:
            with tempfile.TemporaryDirectory(
                prefix="run_validation_gates_pytest_",
                dir=tmp_parent,
            ) as pytest_temp_dir:
                commands = build_phase_commands(
                    args.phase,
                    pathlib.Path(temp_dir),
                    pathlib.Path(pytest_temp_dir),
                )
                if _run_commands_accepts_repo_root():
                    return run_commands(
                        commands,
                        repo_root=repo_root,
                        phase=args.phase,
                        timing_report_path=timing_report_path,
                    )
                return run_commands(commands)
    finally:
        _RUN_COMMANDS_CLEANUP_REPO_ROOT = previous_cleanup_repo_root


if __name__ == "__main__":
    raise SystemExit(main())
