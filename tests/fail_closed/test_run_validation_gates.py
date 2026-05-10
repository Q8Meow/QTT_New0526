from pathlib import Path

from tools import run_validation_gates as runner


def _expected_commands(python_executable: str) -> list[list[str]]:
    validation_dir = runner._default_validation_dir()
    section_manifest = validation_dir / "SectionManifest.json"
    traceability_report = validation_dir / "TraceabilityReport.json"
    first_pr_scope_report = validation_dir / "FirstPrScopeReport.json"
    master_plan = Path("docs") / "master_plan" / "QTT_MasterPlan_Current.md"

    return [
        [
            python_executable,
            str(Path("tools") / "master_plan_ingest.py"),
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
            python_executable,
            str(Path("tools") / "master_plan_traceability_check.py"),
            "--master-plan",
            str(master_plan),
            "--section-manifest",
            str(section_manifest),
            "--traceability-report",
            str(traceability_report),
        ],
        [
            python_executable,
            str(Path("tools") / "validate_first_pr_scope.py"),
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
            python_executable,
            str(Path("tools") / "validate_qtt_owner_global_override_authority.py"),
            "--mode",
            "dev",
            "--repo-root",
            ".",
            "--out",
            str(
                Path("docs")
                / "master_plan"
                / "generated"
                / "QTTOwnerGlobalOverrideAuthority.report.json"
            ),
        ],
        [
            python_executable,
            str(Path("tools") / "validate_source_evidence_static.py"),
            "--schema",
            str(Path("schemas") / "source_evidence" / "source_evidence.schema.json"),
            "--owner-packet",
            str(
                Path("docs")
                / "master_plan"
                / "source_evidence"
                / "QTT_OWNER_SOURCE_EVIDENCE_DEFINITIONS_PACKET.md"
            ),
            "--registry-fixture",
            str(
                Path("tests")
                / "fixtures"
                / "source_evidence"
                / "synthetic_acceptance_registry.v1.fixture.json"
            ),
        ],
        [
            python_executable,
            str(Path("tools") / "validate_source_evidence_gate_confirmation_static.py"),
            "--repo-root",
            ".",
            "--schema",
            str(
                Path("schemas")
                / "source_evidence"
                / "source_evidence_gate_confirmation.schema.json"
            ),
            "--fixture",
            str(
                Path("tests")
                / "fixtures"
                / "source_evidence"
                / "synthetic_source_evidence_gate_confirmation_blocked.v1.fixture.json"
            ),
        ],
        [
            python_executable,
            str(Path("tools") / "validate_connector_capability_static.py"),
            "--schema",
            str(
                Path("schemas")
                / "connectors"
                / "connector_capability_registry.schema.json"
            ),
            "--fixture",
            str(
                Path("tests")
                / "fixtures"
                / "connectors"
                / "synthetic_connector_capability_registry.v1.fixture.json"
            ),
        ],
        [
            python_executable,
            str(Path("tools") / "validate_runtime_orchestration_static.py"),
            "--schema",
            str(
                Path("schemas")
                / "runtime_orchestration"
                / "runtime_orchestration_skeleton.schema.json"
            ),
            "--fixture",
            str(
                Path("tests")
                / "fixtures"
                / "runtime_orchestration"
                / "synthetic_runtime_orchestration_skeleton.v1.fixture.json"
            ),
        ],
        [
            python_executable,
            str(Path("tools") / "validate_replay_paper_execution_graph_static.py"),
            "--schema",
            str(
                Path("schemas")
                / "replay_paper_review"
                / "replay_paper_execution_graph.schema.json"
            ),
            "--fixture",
            str(
                Path("tests")
                / "fixtures"
                / "replay_paper_review"
                / "synthetic_replay_paper_execution_graph.v1.fixture.json"
            ),
        ],
        [
            python_executable,
            str(Path("tools") / "validate_venue_abstraction_layer_static.py"),
            "--schema",
            str(Path("schemas") / "connectors" / "venue_abstraction_layer.schema.json"),
            "--fixture",
            str(
                Path("tests")
                / "fixtures"
                / "connectors"
                / "synthetic_venue_abstraction_layer.v1.fixture.json"
            ),
        ],
        [
            python_executable,
            str(Path("tools") / "validate_order_intent_execution_router_static.py"),
            "--schema",
            str(
                Path("schemas")
                / "connectors"
                / "order_intent_execution_router_scaffolding.schema.json"
            ),
            "--fixture",
            str(
                Path("tests")
                / "fixtures"
                / "connectors"
                / "synthetic_order_intent_execution_router_scaffolding.v1.fixture.json"
            ),
        ],
        [
            python_executable,
            str(Path("tools") / "validate_atomicrows_readiness_static.py"),
            "--repo-root",
            ".",
            "--schema",
            str(Path("schemas") / "atomicrows" / "atomicrows_readiness_audit.schema.json"),
            "--fixture",
            str(
                Path("tests")
                / "fixtures"
                / "atomicrows"
                / "synthetic_atomicrows_readiness_blocked.v1.fixture.json"
            ),
        ],
        [
            python_executable,
            str(Path("tools") / "validate_atomicrows_unblocking_requirements_static.py"),
            "--repo-root",
            ".",
            "--schema",
            str(
                Path("schemas")
                / "atomicrows"
                / "atomicrows_unblocking_requirements_audit.schema.json"
            ),
            "--fixture",
            str(
                Path("tests")
                / "fixtures"
                / "atomicrows"
                / "synthetic_atomicrows_unblocking_requirements_required.v1.fixture.json"
            ),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_atomicrows_canonical_row_specification_static.py"
            ),
            "--repo-root",
            ".",
            "--schema",
            str(
                Path("schemas")
                / "atomicrows"
                / "atomicrows_canonical_row_specification_audit.schema.json"
            ),
            "--fixture",
            str(
                Path("tests")
                / "fixtures"
                / "atomicrows"
                / "synthetic_atomicrows_canonical_row_specification_required.v1.fixture.json"
            ),
        ],
        [
            python_executable,
            str(Path("tools") / "validate_atomicrows_bundle_schema_checker_static.py"),
            "--repo-root",
            ".",
            "--row-schema",
            str(Path("schemas") / "atomicrows" / "atomic_parameter_row.schema.json"),
            "--bundle-schema",
            str(Path("schemas") / "atomicrows" / "atomic_row_bundle.schema.json"),
            "--fixture",
            str(
                Path("tests")
                / "fixtures"
                / "atomicrows"
                / "synthetic_atomicrows_bundle_bootstrap_absent.v1.fixture.json"
            ),
        ],
        [
            python_executable,
            str(Path("tools") / "build_atomicrows_parameter_lifecycle_report.py"),
        ],
        [
            python_executable,
            str(Path("tools") / "validate_atomicrows_parameter_lifecycle.py"),
            "--mode",
            "dev",
        ],
        [
            python_executable,
            str(Path("tools") / "validate_atomicrows_lifecycle_consumer_gate.py"),
            "--mode",
            "dev",
            "--out",
            str(
                Path("docs")
                / "master_plan"
                / "generated"
                / "AtomicRowsLifecycleConsumerGate.report.json"
            ),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_atomicrows_lifecycle_promotion_receipt_gate.py"
            ),
            "--mode",
            "dev",
            "--out",
            str(
                Path("docs")
                / "master_plan"
                / "generated"
                / "AtomicRowsLifecyclePromotionReceiptGate.report.json"
            ),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_atomicrows_lifecycle_registry_mutation_guard.py"
            ),
            "--mode",
            "dev",
            "--out",
            str(
                Path("docs")
                / "master_plan"
                / "generated"
                / "AtomicRowsLifecycleRegistryMutationGuard.report.json"
            ),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_atomicrows_lifecycle_cumulative_readiness_gate.py"
            ),
            "--mode",
            "dev",
            "--out",
            str(
                Path("docs")
                / "master_plan"
                / "generated"
                / "AtomicRowsLifecycleCumulativeReadinessGate.report.json"
            ),
        ],
        [
            python_executable,
            str(Path("tools") / "validate_atomicrows_lifecycle_gate_command_matrix.py"),
            "--mode",
            "dev",
            "--out",
            str(
                Path("docs")
                / "master_plan"
                / "generated"
                / "AtomicRowsLifecycleGateCommandMatrix.json"
            ),
        ],
        [
            python_executable,
            str(Path("tools") / "validate_generated_derivative_bootstrap_gate_static.py"),
            "--repo-root",
            ".",
            "--schema",
            str(
                Path("schemas")
                / "master_plan"
                / "generated_derivative_bootstrap_gate.schema.json"
            ),
            "--fixture",
            str(
                Path("tests")
                / "fixtures"
                / "master_plan"
                / "synthetic_generated_derivative_bootstrap_gate.v1.fixture.json"
            ),
        ],
        [
            python_executable,
            str(Path("tools") / "validate_stage1_packet_schema_gate_static.py"),
            "--repo-root",
            ".",
            "--schema-dir",
            str(Path("schemas") / "stage1_prediction_markets"),
            "--fixture",
            str(
                Path("tests")
                / "fixtures"
                / "stage1_prediction_markets"
                / "synthetic_stage1_packet_schema_gate_blocked.v1.fixture.json"
            ),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_venue_neutral_prediction_adapter_gate_static.py"
            ),
            "--repo-root",
            ".",
            "--schema-dir",
            str(Path("schemas") / "venue_neutral_prediction_adapter"),
            "--fixture",
            str(
                Path("tests")
                / "fixtures"
                / "venue_neutral_prediction_adapter"
                / "synthetic_venue_neutral_prediction_adapter_gate_blocked.v1.fixture.json"
            ),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_connector_scaffold_source_required_gate_static.py"
            ),
            "--repo-root",
            ".",
            "--schema",
            str(
                Path("schemas")
                / "connectors"
                / "connector_scaffold_source_required_gate.schema.json"
            ),
            "--fixture",
            str(
                Path("tests")
                / "fixtures"
                / "connectors"
                / "synthetic_connector_scaffold_source_required_blocked.v1.fixture.json"
            ),
        ],
        [
            python_executable,
            str(Path("tools") / "validate_stage1_runtime_scaffold_gate_static.py"),
            "--repo-root",
            ".",
            "--schema",
            str(
                Path("schemas")
                / "runtime_orchestration"
                / "stage1_runtime_scaffold_gate.schema.json"
            ),
            "--fixture",
            str(
                Path("tests")
                / "fixtures"
                / "runtime_orchestration"
                / "synthetic_stage1_runtime_scaffold_gate_blocked.v1.fixture.json"
            ),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_source_fact_binding_connector_semantic_readiness_static.py"
            ),
            "--repo-root",
            ".",
            "--source-to-connector-schema",
            str(
                Path("schemas")
                / "source_fact_binding_readiness"
                / "stage1_source_to_connector_field_binding_matrix.schema.json"
            ),
            "--source-to-connector-fixture",
            str(
                Path("tests")
                / "fixtures"
                / "source_fact_binding_readiness"
                / "synthetic_stage1_source_to_connector_field_binding_matrix.v1.fixture.json"
            ),
            "--connector-target-schema",
            str(
                Path("schemas")
                / "source_fact_binding_readiness"
                / "stage1_connector_semantic_target_field_matrix.schema.json"
            ),
            "--connector-target-fixture",
            str(
                Path("tests")
                / "fixtures"
                / "source_fact_binding_readiness"
                / "synthetic_stage1_connector_semantic_target_field_matrix.v1.fixture.json"
            ),
            "--gate-report-schema",
            str(
                Path("schemas")
                / "source_fact_binding_readiness"
                / "stage1_connector_semantic_readiness_gate_report.schema.json"
            ),
            "--gate-report-fixture",
            str(
                Path("tests")
                / "fixtures"
                / "source_fact_binding_readiness"
                / "synthetic_stage1_connector_semantic_readiness_gate_report.v1.fixture.json"
            ),
        ],
        [
            python_executable,
            str(Path("tools") / "source_evidence_acceptance_consumer_contract_check.py"),
            "--repo-root",
            ".",
            "--consumer-contract-schema",
            str(
                Path("src")
                / "qtt"
                / "source_evidence"
                / "acceptance"
                / "accepted_source_evidence_consumer_contract.schema.json"
            ),
            "--target-field-ledger-schema",
            str(
                Path("src")
                / "qtt"
                / "source_evidence"
                / "acceptance"
                / "stage1_target_field_acceptance_ledger_record.schema.json"
            ),
            "--export-record-schema",
            str(
                Path("src")
                / "qtt"
                / "source_evidence"
                / "acceptance"
                / "stage1_accepted_source_evidence_export_record.schema.json"
            ),
            "--fixture",
            str(
                Path("tests")
                / "fixtures"
                / "source_evidence"
                / "acceptance_consumer_contract"
                / "synthetic_accepted_source_evidence_consumer_contract_records.v1.fixture.json"
            ),
        ],
        [
            python_executable,
            str(Path("tools") / "stage1_connector_semantic_binding_ledger_check.py"),
            "--repo-root",
            ".",
            "--ledger-schema",
            str(
                Path("src")
                / "qtt"
                / "stage1_prediction_markets"
                / "connector_semantic_binding"
                / "stage1_connector_semantic_binding_ledger_record.schema.json"
            ),
            "--canonicalization-schema",
            str(
                Path("src")
                / "qtt"
                / "stage1_prediction_markets"
                / "connector_semantic_binding"
                / "stage1_connector_semantic_value_canonicalization.schema.json"
            ),
            "--consumer-contract-schema",
            str(
                Path("src")
                / "qtt"
                / "stage1_prediction_markets"
                / "connector_semantic_binding"
                / "stage1_connector_semantic_binding_consumer_contract.schema.json"
            ),
            "--fixture",
            str(
                Path("tests")
                / "fixtures"
                / "source_evidence"
                / "connector_semantic_binding"
                / "synthetic_stage1_connector_semantic_binding_contracts.v1.fixture.json"
            ),
            "--out",
            str(
                Path("docs")
                / "master_plan"
                / "generated"
                / "Stage1ConnectorSemanticBindingLedgerCheck.report.json"
            ),
        ],
        [
            python_executable,
            str(Path("tools") / "stage1_runtime_resolver_snapshot_contract_check.py"),
            "--repo-root",
            ".",
            "--input-lock-schema",
            str(
                Path("src")
                / "qtt"
                / "stage1_prediction_markets"
                / "runtime_resolver"
                / "stage1_runtime_resolver_snapshot_input_lock.schema.json"
            ),
            "--manifest-schema",
            str(
                Path("src")
                / "qtt"
                / "stage1_prediction_markets"
                / "runtime_resolver"
                / "stage1_runtime_resolver_snapshot_manifest.schema.json"
            ),
            "--consumer-contract-schema",
            str(
                Path("src")
                / "qtt"
                / "stage1_prediction_markets"
                / "runtime_resolver"
                / "stage1_runtime_resolver_consumer_contract.schema.json"
            ),
            "--gate-report-schema",
            str(
                Path("src")
                / "qtt"
                / "stage1_prediction_markets"
                / "runtime_resolver"
                / "stage1_runtime_resolver_snapshot_gate_report.schema.json"
            ),
            "--fixture",
            str(
                Path("tests")
                / "fixtures"
                / "source_evidence"
                / "runtime_resolver"
                / "synthetic_stage1_runtime_resolver_snapshot_contracts.v1.fixture.json"
            ),
            "--out",
            str(
                Path("docs")
                / "master_plan"
                / "generated"
                / "Stage1RuntimeResolverSnapshotContractCheck.report.json"
            ),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "stage1_runtime_resolver_to_replay_paper_handoff_check.py"
            ),
            "--repo-root",
            ".",
            "--consumer-allowlist-schema",
            str(
                Path("src")
                / "qtt"
                / "stage1_prediction_markets"
                / "runtime_resolver_snapshot"
                / "stage1_runtime_resolver_snapshot_consumer_allowlist.schema.json"
            ),
            "--handoff-contract-schema",
            str(
                Path("src")
                / "qtt"
                / "stage1_prediction_markets"
                / "runtime_resolver_snapshot"
                / "stage1_runtime_resolver_to_replay_paper_handoff_contract.schema.json"
            ),
            "--handoff-report-schema",
            str(
                Path("src")
                / "qtt"
                / "stage1_prediction_markets"
                / "runtime_resolver_snapshot"
                / "stage1_runtime_resolver_to_replay_paper_handoff_report.schema.json"
            ),
            "--fixture",
            str(
                Path("tests")
                / "fixtures"
                / "source_evidence"
                / "runtime_resolver_snapshot"
                / "synthetic_stage1_runtime_resolver_to_replay_paper_handoff.v1.fixture.json"
            ),
            "--out",
            str(
                Path("docs")
                / "master_plan"
                / "generated"
                / "Stage1RuntimeResolverToReplayPaperHandoff.report.json"
            ),
        ],
        [
            python_executable,
            str(Path("tools") / "stage1_concurrent_replay_paper_contract_check.py"),
            "--repo-root",
            ".",
            "--input-identity-schema",
            str(
                Path("src")
                / "qtt"
                / "stage1_prediction_markets"
                / "replay_paper"
                / "concurrent_replay_paper_input_identity.schema.json"
            ),
            "--replay-lane-schema",
            str(
                Path("src")
                / "qtt"
                / "stage1_prediction_markets"
                / "replay_paper"
                / "concurrent_replay_lane_contract.schema.json"
            ),
            "--paper-lane-schema",
            str(
                Path("src")
                / "qtt"
                / "stage1_prediction_markets"
                / "replay_paper"
                / "concurrent_paper_lane_contract.schema.json"
            ),
            "--replay-result-boundary-schema",
            str(
                Path("src")
                / "qtt"
                / "stage1_prediction_markets"
                / "replay_paper"
                / "replay_result_packet_boundary.schema.json"
            ),
            "--paper-result-boundary-schema",
            str(
                Path("src")
                / "qtt"
                / "stage1_prediction_markets"
                / "replay_paper"
                / "paper_result_packet_boundary.schema.json"
            ),
            "--gate-report-schema",
            str(
                Path("src")
                / "qtt"
                / "stage1_prediction_markets"
                / "replay_paper"
                / "concurrent_replay_paper_execution_gate_report.schema.json"
            ),
            "--fixture",
            str(
                Path("tests")
                / "fixtures"
                / "source_evidence"
                / "replay_paper"
                / "synthetic_concurrent_replay_paper_contracts.v1.fixture.json"
            ),
            "--out",
            str(
                Path("docs")
                / "master_plan"
                / "generated"
                / "Stage1ConcurrentReplayPaperContractCheck.report.json"
            ),
        ],
        [
            python_executable,
            str(Path("tools") / "stage1_dual_result_review_contract_check.py"),
            "--repo-root",
            ".",
            "--input-contract-schema",
            str(
                Path("src")
                / "qtt"
                / "stage1_prediction_markets"
                / "dual_result_review"
                / "stage1_dual_result_review_input_contract.schema.json"
            ),
            "--comparison-matrix-schema",
            str(
                Path("src")
                / "qtt"
                / "stage1_prediction_markets"
                / "dual_result_review"
                / "stage1_replay_paper_comparison_matrix.schema.json"
            ),
            "--gate-report-schema",
            str(
                Path("src")
                / "qtt"
                / "stage1_prediction_markets"
                / "dual_result_review"
                / "stage1_dual_result_review_gate_report.schema.json"
            ),
            "--owner-handoff-block-schema",
            str(
                Path("src")
                / "qtt"
                / "stage1_prediction_markets"
                / "dual_result_review"
                / "stage1_owner_live_promotion_handoff_block.schema.json"
            ),
            "--fixture",
            str(
                Path("tests")
                / "fixtures"
                / "source_evidence"
                / "dual_result_review"
                / "synthetic_stage1_dual_result_review_contracts.v1.fixture.json"
            ),
            "--out",
            str(
                Path("docs")
                / "master_plan"
                / "generated"
                / "Stage1DualResultReviewContractCheck.report.json"
            ),
        ],
        [
            python_executable,
            str(Path("tools") / "stage1_owner_live_promotion_review_contract_check.py"),
            "--repo-root",
            ".",
            "--input-contract-schema",
            str(
                Path("src")
                / "qtt"
                / "stage1_prediction_markets"
                / "owner_live_promotion_review"
                / "stage1_owner_live_promotion_review_input_contract.schema.json"
            ),
            "--owner-approval-receipt-boundary-schema",
            str(
                Path("src")
                / "qtt"
                / "stage1_prediction_markets"
                / "owner_live_promotion_review"
                / "stage1_owner_approval_receipt_boundary.schema.json"
            ),
            "--gate-report-schema",
            str(
                Path("src")
                / "qtt"
                / "stage1_prediction_markets"
                / "owner_live_promotion_review"
                / "stage1_owner_live_promotion_review_gate_report.schema.json"
            ),
            "--handoff-block-schema",
            str(
                Path("src")
                / "qtt"
                / "stage1_prediction_markets"
                / "owner_live_promotion_review"
                / "stage1_three_venue_canary_eligibility_handoff_block.schema.json"
            ),
            "--fixture",
            str(
                Path("tests")
                / "fixtures"
                / "source_evidence"
                / "owner_live_promotion_review"
                / "synthetic_stage1_owner_live_promotion_review_contracts.v1.fixture.json"
            ),
            "--out",
            str(
                Path("docs")
                / "master_plan"
                / "generated"
                / "Stage1OwnerLivePromotionReviewContractCheck.report.json"
            ),
        ],
        [
            python_executable,
            str(Path("tools") / "stage1_three_venue_canary_eligibility_contract_check.py"),
            "--repo-root",
            ".",
            "--input-contract-schema",
            str(
                Path("src")
                / "qtt"
                / "stage1_prediction_markets"
                / "three_venue_canary_eligibility"
                / "stage1_three_venue_canary_eligibility_input_contract.schema.json"
            ),
            "--readiness-matrix-schema",
            str(
                Path("src")
                / "qtt"
                / "stage1_prediction_markets"
                / "three_venue_canary_eligibility"
                / "stage1_three_venue_platform_readiness_matrix.schema.json"
            ),
            "--handoff-schema",
            str(
                Path("src")
                / "qtt"
                / "stage1_prediction_markets"
                / "three_venue_canary_eligibility"
                / "stage1_owner_review_to_canary_eligibility_handoff.schema.json"
            ),
            "--gate-report-schema",
            str(
                Path("src")
                / "qtt"
                / "stage1_prediction_markets"
                / "three_venue_canary_eligibility"
                / "stage1_three_venue_canary_eligibility_gate_report.schema.json"
            ),
            "--execution-block-schema",
            str(
                Path("src")
                / "qtt"
                / "stage1_prediction_markets"
                / "three_venue_canary_eligibility"
                / "stage1_limited_live_canary_execution_block.schema.json"
            ),
            "--fixture",
            str(
                Path("tests")
                / "fixtures"
                / "source_evidence"
                / "three_venue_canary_eligibility"
                / "synthetic_stage1_three_venue_canary_eligibility_contracts.v1.fixture.json"
            ),
            "--out",
            str(
                Path("docs")
                / "master_plan"
                / "generated"
                / "Stage1ThreeVenueCanaryEligibilityContractCheck.report.json"
            ),
        ],
        [
            python_executable,
            str(Path("tools") / "build_master_plan_section_coverage_report.py"),
        ],
        [
            python_executable,
            str(Path("tools") / "validate_master_plan_section_coverage.py"),
            "--mode",
            "dev",
        ],
        [
            python_executable,
            str(Path("tools") / "qtt_test_gate.py"),
            "--phase",
            "first-coding-runbook",
            "--repo-root",
            ".",
            "--strict-no-claim",
            "--out",
            str(Path("docs") / "master_plan" / "generated" / "QTTTestGate.report.json"),
        ],
        [
            python_executable,
            str(Path("tools") / "local_gate_command_matrix.py"),
            "--repo-root",
            ".",
            "--out",
            str(Path("docs") / "master_plan" / "generated" / "LocalGateCommandMatrix.json"),
        ],
        [
            python_executable,
            str(Path("tools") / "pr_handoff_check.py"),
            "--repo-root",
            ".",
            "--out",
            str(
                Path("docs")
                / "master_plan"
                / "generated"
                / "FirstCodingPRHandoff.packet.json"
            ),
        ],
        [
            python_executable,
            str(Path("tools") / "validate_no_runtime_artifacts.py"),
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
            python_executable,
            str(Path("tools") / "run_pytest_fresh_basetemp.py"),
            "-q",
        ],
    ]


def test_runner_builds_expected_command_sequence(monkeypatch):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    assert runner.build_validation_commands() == _expected_commands(python_executable)


def test_runner_commands_use_sys_executable(monkeypatch):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()

    assert commands
    assert all(command[0] == python_executable for command in commands)


def test_runner_invokes_pytest_through_fresh_basetemp_helper(monkeypatch):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()

    assert commands[-1] == [
        python_executable,
        str(Path("tools") / "run_pytest_fresh_basetemp.py"),
        "-q",
    ]


def test_runner_includes_owner_global_override_authority_dev_gate(monkeypatch):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands]
    scope_index = command_names.index("validate_first_pr_scope.py")
    owner_override_index = command_names.index(
        "validate_qtt_owner_global_override_authority.py"
    )
    source_evidence_index = command_names.index("validate_source_evidence_static.py")

    assert scope_index < owner_override_index < source_evidence_index
    assert commands[owner_override_index] == [
        python_executable,
        str(Path("tools") / "validate_qtt_owner_global_override_authority.py"),
        "--mode",
        "dev",
        "--repo-root",
        ".",
        "--out",
        str(
            Path("docs")
            / "master_plan"
            / "generated"
            / "QTTOwnerGlobalOverrideAuthority.report.json"
        ),
    ]


def test_runner_does_not_use_direct_python_m_pytest(monkeypatch):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()

    assert not any(command[:3] == [python_executable, "-m", "pytest"] for command in commands)


def test_runner_does_not_use_direct_pytest_command(monkeypatch):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()

    assert not any(
        Path(token).name.lower() in {"pytest", "pytest.exe"}
        for command in commands
        for token in command
    )


def test_runner_includes_no_runtime_artifact_flags(monkeypatch):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    no_runtime_command = next(
        command
        for command in commands
        if command[1] == str(Path("tools") / "validate_no_runtime_artifacts.py")
    )

    assert "--forbid-source-retrieval" in no_runtime_command
    assert "--forbid-source-acceptance" in no_runtime_command
    assert "--forbid-connector-binding" in no_runtime_command
    assert "--forbid-private-state-fetch" in no_runtime_command
    assert "--forbid-order-execution" in no_runtime_command
    assert "--forbid-neural-training" in no_runtime_command
    assert "--forbid-neural-inference" in no_runtime_command
    assert "--forbid-external-repo-clone" in no_runtime_command
    assert "--forbid-package-install-scripts" in no_runtime_command


def test_runner_orders_source_evidence_gate_confirmation_before_connectors(monkeypatch):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands]

    source_evidence_index = command_names.index("validate_source_evidence_static.py")
    gate_confirmation_index = command_names.index(
        "validate_source_evidence_gate_confirmation_static.py"
    )
    connector_index = command_names.index("validate_connector_capability_static.py")

    assert source_evidence_index < gate_confirmation_index < connector_index


def test_runner_includes_non_mutating_atomicrows_readiness_audit(monkeypatch):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    audit_command = next(
        command
        for command in commands
        if command[1] == str(Path("tools") / "validate_atomicrows_readiness_static.py")
    )

    assert audit_command == [
        python_executable,
        str(Path("tools") / "validate_atomicrows_readiness_static.py"),
        "--repo-root",
        ".",
        "--schema",
        str(Path("schemas") / "atomicrows" / "atomicrows_readiness_audit.schema.json"),
        "--fixture",
        str(
            Path("tests")
            / "fixtures"
            / "atomicrows"
            / "synthetic_atomicrows_readiness_blocked.v1.fixture.json"
        ),
    ]
    assert "AtomicRows.bundle.jsonl" not in audit_command
    assert "AtomicRows.bundle.sha256" not in audit_command


def test_runner_includes_non_mutating_atomicrows_unblocking_requirements_audit(
    monkeypatch,
):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    audit_command = next(
        command
        for command in commands
        if command[1]
        == str(Path("tools") / "validate_atomicrows_unblocking_requirements_static.py")
    )

    assert audit_command == [
        python_executable,
        str(Path("tools") / "validate_atomicrows_unblocking_requirements_static.py"),
        "--repo-root",
        ".",
        "--schema",
        str(
            Path("schemas")
            / "atomicrows"
            / "atomicrows_unblocking_requirements_audit.schema.json"
        ),
        "--fixture",
        str(
            Path("tests")
            / "fixtures"
            / "atomicrows"
            / "synthetic_atomicrows_unblocking_requirements_required.v1.fixture.json"
        ),
    ]
    assert "AtomicRows.bundle.jsonl" not in audit_command
    assert "AtomicRows.bundle.sha256" not in audit_command


def test_runner_includes_non_mutating_atomicrows_canonical_row_specification_audit(
    monkeypatch,
):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    audit_command = next(
        command
        for command in commands
        if command[1]
        == str(
            Path("tools")
            / "validate_atomicrows_canonical_row_specification_static.py"
        )
    )

    assert audit_command == [
        python_executable,
        str(Path("tools") / "validate_atomicrows_canonical_row_specification_static.py"),
        "--repo-root",
        ".",
        "--schema",
        str(
            Path("schemas")
            / "atomicrows"
            / "atomicrows_canonical_row_specification_audit.schema.json"
        ),
        "--fixture",
        str(
            Path("tests")
            / "fixtures"
            / "atomicrows"
            / "synthetic_atomicrows_canonical_row_specification_required.v1.fixture.json"
        ),
    ]
    assert "AtomicRows.bundle.jsonl" not in audit_command
    assert "AtomicRows.bundle.sha256" not in audit_command


def test_runner_includes_atomicrows_bundle_schema_checker_after_row_specification(
    monkeypatch,
):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands]

    row_spec_index = command_names.index(
        "validate_atomicrows_canonical_row_specification_static.py"
    )
    bundle_checker_index = command_names.index(
        "validate_atomicrows_bundle_schema_checker_static.py"
    )
    no_runtime_index = command_names.index("validate_no_runtime_artifacts.py")
    assert row_spec_index < bundle_checker_index < no_runtime_index

    audit_command = commands[bundle_checker_index]
    assert audit_command == [
        python_executable,
        str(Path("tools") / "validate_atomicrows_bundle_schema_checker_static.py"),
        "--repo-root",
        ".",
        "--row-schema",
        str(Path("schemas") / "atomicrows" / "atomic_parameter_row.schema.json"),
        "--bundle-schema",
        str(Path("schemas") / "atomicrows" / "atomic_row_bundle.schema.json"),
        "--fixture",
        str(
            Path("tests")
            / "fixtures"
            / "atomicrows"
            / "synthetic_atomicrows_bundle_bootstrap_absent.v1.fixture.json"
        ),
    ]


def test_runner_includes_generated_derivative_gate_after_bundle_checker(
    monkeypatch,
):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands]

    bundle_checker_index = command_names.index(
        "validate_atomicrows_bundle_schema_checker_static.py"
    )
    lifecycle_build_index = command_names.index(
        "build_atomicrows_parameter_lifecycle_report.py"
    )
    lifecycle_validate_index = command_names.index(
        "validate_atomicrows_parameter_lifecycle.py"
    )
    consumer_gate_index = command_names.index(
        "validate_atomicrows_lifecycle_consumer_gate.py"
    )
    promotion_receipt_gate_index = command_names.index(
        "validate_atomicrows_lifecycle_promotion_receipt_gate.py"
    )
    mutation_guard_index = command_names.index(
        "validate_atomicrows_lifecycle_registry_mutation_guard.py"
    )
    cumulative_readiness_index = command_names.index(
        "validate_atomicrows_lifecycle_cumulative_readiness_gate.py"
    )
    lifecycle_command_matrix_index = command_names.index(
        "validate_atomicrows_lifecycle_gate_command_matrix.py"
    )
    generated_gate_index = command_names.index(
        "validate_generated_derivative_bootstrap_gate_static.py"
    )
    no_runtime_index = command_names.index("validate_no_runtime_artifacts.py")
    assert (
        bundle_checker_index
        < lifecycle_build_index
        < lifecycle_validate_index
        < consumer_gate_index
        < promotion_receipt_gate_index
        < mutation_guard_index
        < cumulative_readiness_index
        < lifecycle_command_matrix_index
        < generated_gate_index
        < no_runtime_index
    )
    assert commands[lifecycle_build_index] == [
        python_executable,
        str(Path("tools") / "build_atomicrows_parameter_lifecycle_report.py"),
    ]
    assert commands[lifecycle_validate_index] == [
        python_executable,
        str(Path("tools") / "validate_atomicrows_parameter_lifecycle.py"),
        "--mode",
        "dev",
    ]
    assert "final" not in commands[lifecycle_validate_index]
    assert commands[consumer_gate_index] == [
        python_executable,
        str(Path("tools") / "validate_atomicrows_lifecycle_consumer_gate.py"),
        "--mode",
        "dev",
        "--out",
        str(
            Path("docs")
            / "master_plan"
            / "generated"
            / "AtomicRowsLifecycleConsumerGate.report.json"
        ),
    ]
    assert commands[promotion_receipt_gate_index] == [
        python_executable,
        str(Path("tools") / "validate_atomicrows_lifecycle_promotion_receipt_gate.py"),
        "--mode",
        "dev",
        "--out",
        str(
            Path("docs")
            / "master_plan"
            / "generated"
            / "AtomicRowsLifecyclePromotionReceiptGate.report.json"
        ),
    ]
    assert commands[mutation_guard_index] == [
        python_executable,
        str(Path("tools") / "validate_atomicrows_lifecycle_registry_mutation_guard.py"),
        "--mode",
        "dev",
        "--out",
        str(
            Path("docs")
            / "master_plan"
            / "generated"
            / "AtomicRowsLifecycleRegistryMutationGuard.report.json"
        ),
    ]
    assert commands[cumulative_readiness_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_atomicrows_lifecycle_cumulative_readiness_gate.py"
        ),
        "--mode",
        "dev",
        "--out",
        str(
            Path("docs")
            / "master_plan"
            / "generated"
            / "AtomicRowsLifecycleCumulativeReadinessGate.report.json"
        ),
    ]
    assert commands[lifecycle_command_matrix_index] == [
        python_executable,
        str(Path("tools") / "validate_atomicrows_lifecycle_gate_command_matrix.py"),
        "--mode",
        "dev",
        "--out",
        str(
            Path("docs")
            / "master_plan"
            / "generated"
            / "AtomicRowsLifecycleGateCommandMatrix.json"
        ),
    ]

    audit_command = commands[generated_gate_index]
    assert audit_command == [
        python_executable,
        str(Path("tools") / "validate_generated_derivative_bootstrap_gate_static.py"),
        "--repo-root",
        ".",
        "--schema",
        str(
            Path("schemas")
            / "master_plan"
            / "generated_derivative_bootstrap_gate.schema.json"
        ),
        "--fixture",
        str(
            Path("tests")
            / "fixtures"
            / "master_plan"
            / "synthetic_generated_derivative_bootstrap_gate.v1.fixture.json"
        ),
    ]


def test_runner_includes_stage1_packet_schema_gate_after_generated_derivative_gate(
    monkeypatch,
):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands]

    generated_gate_index = command_names.index(
        "validate_generated_derivative_bootstrap_gate_static.py"
    )
    stage1_gate_index = command_names.index(
        "validate_stage1_packet_schema_gate_static.py"
    )
    no_runtime_index = command_names.index("validate_no_runtime_artifacts.py")
    assert generated_gate_index < stage1_gate_index < no_runtime_index

    audit_command = commands[stage1_gate_index]
    assert audit_command == [
        python_executable,
        str(Path("tools") / "validate_stage1_packet_schema_gate_static.py"),
        "--repo-root",
        ".",
        "--schema-dir",
        str(Path("schemas") / "stage1_prediction_markets"),
        "--fixture",
        str(
            Path("tests")
            / "fixtures"
            / "stage1_prediction_markets"
            / "synthetic_stage1_packet_schema_gate_blocked.v1.fixture.json"
        ),
    ]


def test_runner_includes_venue_neutral_adapter_gate_after_stage1_and_before_no_runtime(
    monkeypatch,
):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands]

    stage1_gate_index = command_names.index(
        "validate_stage1_packet_schema_gate_static.py"
    )
    adapter_gate_index = command_names.index(
        "validate_venue_neutral_prediction_adapter_gate_static.py"
    )
    no_runtime_index = command_names.index("validate_no_runtime_artifacts.py")
    assert stage1_gate_index < adapter_gate_index < no_runtime_index

    audit_command = commands[adapter_gate_index]
    assert audit_command == [
        python_executable,
        str(Path("tools") / "validate_venue_neutral_prediction_adapter_gate_static.py"),
        "--repo-root",
        ".",
        "--schema-dir",
        str(Path("schemas") / "venue_neutral_prediction_adapter"),
        "--fixture",
        str(
            Path("tests")
            / "fixtures"
            / "venue_neutral_prediction_adapter"
            / "synthetic_venue_neutral_prediction_adapter_gate_blocked.v1.fixture.json"
        ),
    ]


def test_runner_includes_connector_scaffold_gate_after_adapter_and_before_no_runtime(
    monkeypatch,
):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands]

    adapter_gate_index = command_names.index(
        "validate_venue_neutral_prediction_adapter_gate_static.py"
    )
    connector_scaffold_gate_index = command_names.index(
        "validate_connector_scaffold_source_required_gate_static.py"
    )
    no_runtime_index = command_names.index("validate_no_runtime_artifacts.py")
    assert adapter_gate_index < connector_scaffold_gate_index < no_runtime_index

    audit_command = commands[connector_scaffold_gate_index]
    assert audit_command == [
        python_executable,
        str(Path("tools") / "validate_connector_scaffold_source_required_gate_static.py"),
        "--repo-root",
        ".",
        "--schema",
        str(
            Path("schemas")
            / "connectors"
            / "connector_scaffold_source_required_gate.schema.json"
        ),
        "--fixture",
        str(
            Path("tests")
            / "fixtures"
            / "connectors"
            / "synthetic_connector_scaffold_source_required_blocked.v1.fixture.json"
        ),
    ]


def test_runner_includes_stage1_runtime_scaffold_gate_after_connector_and_before_no_runtime(
    monkeypatch,
):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands]

    connector_scaffold_gate_index = command_names.index(
        "validate_connector_scaffold_source_required_gate_static.py"
    )
    stage1_runtime_scaffold_gate_index = command_names.index(
        "validate_stage1_runtime_scaffold_gate_static.py"
    )
    no_runtime_index = command_names.index("validate_no_runtime_artifacts.py")
    assert (
        connector_scaffold_gate_index
        < stage1_runtime_scaffold_gate_index
        < no_runtime_index
    )

    audit_command = commands[stage1_runtime_scaffold_gate_index]
    assert audit_command == [
        python_executable,
        str(Path("tools") / "validate_stage1_runtime_scaffold_gate_static.py"),
        "--repo-root",
        ".",
        "--schema",
        str(
            Path("schemas")
            / "runtime_orchestration"
            / "stage1_runtime_scaffold_gate.schema.json"
        ),
        "--fixture",
        str(
            Path("tests")
            / "fixtures"
            / "runtime_orchestration"
            / "synthetic_stage1_runtime_scaffold_gate_blocked.v1.fixture.json"
        ),
    ]


def test_runner_includes_pr37_static_gates_after_stage1_runtime_and_before_no_runtime(
    monkeypatch,
):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands]

    stage1_runtime_index = command_names.index(
        "validate_stage1_runtime_scaffold_gate_static.py"
    )
    qtt_gate_index = command_names.index("qtt_test_gate.py")
    matrix_index = command_names.index("local_gate_command_matrix.py")
    handoff_index = command_names.index("pr_handoff_check.py")
    no_runtime_index = command_names.index("validate_no_runtime_artifacts.py")

    assert (
        stage1_runtime_index
        < qtt_gate_index
        < matrix_index
        < handoff_index
        < no_runtime_index
    )
    assert commands[qtt_gate_index] == [
        python_executable,
        str(Path("tools") / "qtt_test_gate.py"),
        "--phase",
        "first-coding-runbook",
        "--repo-root",
        ".",
        "--strict-no-claim",
        "--out",
        str(Path("docs") / "master_plan" / "generated" / "QTTTestGate.report.json"),
    ]
    assert commands[matrix_index] == [
        python_executable,
        str(Path("tools") / "local_gate_command_matrix.py"),
        "--repo-root",
        ".",
        "--out",
        str(Path("docs") / "master_plan" / "generated" / "LocalGateCommandMatrix.json"),
    ]
    assert commands[handoff_index] == [
        python_executable,
        str(Path("tools") / "pr_handoff_check.py"),
        "--repo-root",
        ".",
        "--out",
        str(
            Path("docs")
            / "master_plan"
            / "generated"
            / "FirstCodingPRHandoff.packet.json"
        ),
    ]


def test_runner_includes_pr41_runtime_resolver_contract_gate_after_pr40_and_before_qtt_gate(
    monkeypatch,
):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands]

    pr40_index = command_names.index("stage1_connector_semantic_binding_ledger_check.py")
    pr41_index = command_names.index("stage1_runtime_resolver_snapshot_contract_check.py")
    qtt_gate_index = command_names.index("qtt_test_gate.py")
    no_runtime_index = command_names.index("validate_no_runtime_artifacts.py")

    assert pr40_index < pr41_index < qtt_gate_index < no_runtime_index
    assert commands[pr41_index] == [
        python_executable,
        str(Path("tools") / "stage1_runtime_resolver_snapshot_contract_check.py"),
        "--repo-root",
        ".",
        "--input-lock-schema",
        str(
            Path("src")
            / "qtt"
            / "stage1_prediction_markets"
            / "runtime_resolver"
            / "stage1_runtime_resolver_snapshot_input_lock.schema.json"
        ),
        "--manifest-schema",
        str(
            Path("src")
            / "qtt"
            / "stage1_prediction_markets"
            / "runtime_resolver"
            / "stage1_runtime_resolver_snapshot_manifest.schema.json"
        ),
        "--consumer-contract-schema",
        str(
            Path("src")
            / "qtt"
            / "stage1_prediction_markets"
            / "runtime_resolver"
            / "stage1_runtime_resolver_consumer_contract.schema.json"
        ),
        "--gate-report-schema",
        str(
            Path("src")
            / "qtt"
            / "stage1_prediction_markets"
            / "runtime_resolver"
            / "stage1_runtime_resolver_snapshot_gate_report.schema.json"
        ),
        "--fixture",
        str(
            Path("tests")
            / "fixtures"
            / "source_evidence"
            / "runtime_resolver"
            / "synthetic_stage1_runtime_resolver_snapshot_contracts.v1.fixture.json"
        ),
        "--out",
        str(
            Path("docs")
            / "master_plan"
            / "generated"
            / "Stage1RuntimeResolverSnapshotContractCheck.report.json"
        ),
    ]


def test_runner_includes_pr42_runtime_resolver_to_replay_paper_handoff_after_pr41_and_before_qtt_gate(
    monkeypatch,
):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands]

    pr41_index = command_names.index("stage1_runtime_resolver_snapshot_contract_check.py")
    pr42_index = command_names.index(
        "stage1_runtime_resolver_to_replay_paper_handoff_check.py"
    )
    qtt_gate_index = command_names.index("qtt_test_gate.py")
    no_runtime_index = command_names.index("validate_no_runtime_artifacts.py")

    assert pr41_index < pr42_index < qtt_gate_index < no_runtime_index
    assert commands[pr42_index] == [
        python_executable,
        str(
            Path("tools")
            / "stage1_runtime_resolver_to_replay_paper_handoff_check.py"
        ),
        "--repo-root",
        ".",
        "--consumer-allowlist-schema",
        str(
            Path("src")
            / "qtt"
            / "stage1_prediction_markets"
            / "runtime_resolver_snapshot"
            / "stage1_runtime_resolver_snapshot_consumer_allowlist.schema.json"
        ),
        "--handoff-contract-schema",
        str(
            Path("src")
            / "qtt"
            / "stage1_prediction_markets"
            / "runtime_resolver_snapshot"
            / "stage1_runtime_resolver_to_replay_paper_handoff_contract.schema.json"
        ),
        "--handoff-report-schema",
        str(
            Path("src")
            / "qtt"
            / "stage1_prediction_markets"
            / "runtime_resolver_snapshot"
            / "stage1_runtime_resolver_to_replay_paper_handoff_report.schema.json"
        ),
        "--fixture",
        str(
            Path("tests")
            / "fixtures"
            / "source_evidence"
            / "runtime_resolver_snapshot"
            / "synthetic_stage1_runtime_resolver_to_replay_paper_handoff.v1.fixture.json"
        ),
        "--out",
        str(
            Path("docs")
            / "master_plan"
            / "generated"
            / "Stage1RuntimeResolverToReplayPaperHandoff.report.json"
        ),
    ]


def test_runner_includes_pr43_concurrent_replay_paper_contract_after_pr42_and_before_qtt_gate(
    monkeypatch,
):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands]

    pr42_index = command_names.index(
        "stage1_runtime_resolver_to_replay_paper_handoff_check.py"
    )
    pr43_index = command_names.index("stage1_concurrent_replay_paper_contract_check.py")
    qtt_gate_index = command_names.index("qtt_test_gate.py")
    no_runtime_index = command_names.index("validate_no_runtime_artifacts.py")

    assert pr42_index < pr43_index < qtt_gate_index < no_runtime_index
    assert commands[pr43_index] == [
        python_executable,
        str(Path("tools") / "stage1_concurrent_replay_paper_contract_check.py"),
        "--repo-root",
        ".",
        "--input-identity-schema",
        str(
            Path("src")
            / "qtt"
            / "stage1_prediction_markets"
            / "replay_paper"
            / "concurrent_replay_paper_input_identity.schema.json"
        ),
        "--replay-lane-schema",
        str(
            Path("src")
            / "qtt"
            / "stage1_prediction_markets"
            / "replay_paper"
            / "concurrent_replay_lane_contract.schema.json"
        ),
        "--paper-lane-schema",
        str(
            Path("src")
            / "qtt"
            / "stage1_prediction_markets"
            / "replay_paper"
            / "concurrent_paper_lane_contract.schema.json"
        ),
        "--replay-result-boundary-schema",
        str(
            Path("src")
            / "qtt"
            / "stage1_prediction_markets"
            / "replay_paper"
            / "replay_result_packet_boundary.schema.json"
        ),
        "--paper-result-boundary-schema",
        str(
            Path("src")
            / "qtt"
            / "stage1_prediction_markets"
            / "replay_paper"
            / "paper_result_packet_boundary.schema.json"
        ),
        "--gate-report-schema",
        str(
            Path("src")
            / "qtt"
            / "stage1_prediction_markets"
            / "replay_paper"
            / "concurrent_replay_paper_execution_gate_report.schema.json"
        ),
        "--fixture",
        str(
            Path("tests")
            / "fixtures"
            / "source_evidence"
            / "replay_paper"
            / "synthetic_concurrent_replay_paper_contracts.v1.fixture.json"
        ),
        "--out",
        str(
            Path("docs")
            / "master_plan"
            / "generated"
            / "Stage1ConcurrentReplayPaperContractCheck.report.json"
        ),
    ]


def test_runner_includes_pr44_dual_result_review_contract_after_pr43_and_before_qtt_gate(
    monkeypatch,
):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands]

    pr43_index = command_names.index("stage1_concurrent_replay_paper_contract_check.py")
    pr44_index = command_names.index("stage1_dual_result_review_contract_check.py")
    qtt_gate_index = command_names.index("qtt_test_gate.py")
    no_runtime_index = command_names.index("validate_no_runtime_artifacts.py")

    assert pr43_index < pr44_index < qtt_gate_index < no_runtime_index
    assert commands[pr44_index] == [
        python_executable,
        str(Path("tools") / "stage1_dual_result_review_contract_check.py"),
        "--repo-root",
        ".",
        "--input-contract-schema",
        str(
            Path("src")
            / "qtt"
            / "stage1_prediction_markets"
            / "dual_result_review"
            / "stage1_dual_result_review_input_contract.schema.json"
        ),
        "--comparison-matrix-schema",
        str(
            Path("src")
            / "qtt"
            / "stage1_prediction_markets"
            / "dual_result_review"
            / "stage1_replay_paper_comparison_matrix.schema.json"
        ),
        "--gate-report-schema",
        str(
            Path("src")
            / "qtt"
            / "stage1_prediction_markets"
            / "dual_result_review"
            / "stage1_dual_result_review_gate_report.schema.json"
        ),
        "--owner-handoff-block-schema",
        str(
            Path("src")
            / "qtt"
            / "stage1_prediction_markets"
            / "dual_result_review"
            / "stage1_owner_live_promotion_handoff_block.schema.json"
        ),
        "--fixture",
        str(
            Path("tests")
            / "fixtures"
            / "source_evidence"
            / "dual_result_review"
            / "synthetic_stage1_dual_result_review_contracts.v1.fixture.json"
        ),
        "--out",
        str(
            Path("docs")
            / "master_plan"
            / "generated"
            / "Stage1DualResultReviewContractCheck.report.json"
        ),
    ]


def test_runner_includes_pr45_owner_live_promotion_review_contract_after_pr44_and_before_qtt_gate(
    monkeypatch,
):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands]

    pr44_index = command_names.index("stage1_dual_result_review_contract_check.py")
    pr45_index = command_names.index(
        "stage1_owner_live_promotion_review_contract_check.py"
    )
    qtt_gate_index = command_names.index("qtt_test_gate.py")
    no_runtime_index = command_names.index("validate_no_runtime_artifacts.py")

    assert pr44_index < pr45_index < qtt_gate_index < no_runtime_index
    assert commands[pr45_index] == [
        python_executable,
        str(Path("tools") / "stage1_owner_live_promotion_review_contract_check.py"),
        "--repo-root",
        ".",
        "--input-contract-schema",
        str(
            Path("src")
            / "qtt"
            / "stage1_prediction_markets"
            / "owner_live_promotion_review"
            / "stage1_owner_live_promotion_review_input_contract.schema.json"
        ),
        "--owner-approval-receipt-boundary-schema",
        str(
            Path("src")
            / "qtt"
            / "stage1_prediction_markets"
            / "owner_live_promotion_review"
            / "stage1_owner_approval_receipt_boundary.schema.json"
        ),
        "--gate-report-schema",
        str(
            Path("src")
            / "qtt"
            / "stage1_prediction_markets"
            / "owner_live_promotion_review"
            / "stage1_owner_live_promotion_review_gate_report.schema.json"
        ),
        "--handoff-block-schema",
        str(
            Path("src")
            / "qtt"
            / "stage1_prediction_markets"
            / "owner_live_promotion_review"
            / "stage1_three_venue_canary_eligibility_handoff_block.schema.json"
        ),
        "--fixture",
        str(
            Path("tests")
            / "fixtures"
            / "source_evidence"
            / "owner_live_promotion_review"
            / "synthetic_stage1_owner_live_promotion_review_contracts.v1.fixture.json"
        ),
        "--out",
        str(
            Path("docs")
            / "master_plan"
            / "generated"
            / "Stage1OwnerLivePromotionReviewContractCheck.report.json"
        ),
    ]


def test_runner_includes_pr46_three_venue_canary_eligibility_contract_after_pr45_and_before_qtt_gate(
    monkeypatch,
):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands]

    pr45_index = command_names.index(
        "stage1_owner_live_promotion_review_contract_check.py"
    )
    pr46_index = command_names.index(
        "stage1_three_venue_canary_eligibility_contract_check.py"
    )
    qtt_gate_index = command_names.index("qtt_test_gate.py")
    no_runtime_index = command_names.index("validate_no_runtime_artifacts.py")

    assert pr45_index < pr46_index < qtt_gate_index < no_runtime_index
    assert commands[pr46_index] == [
        python_executable,
        str(Path("tools") / "stage1_three_venue_canary_eligibility_contract_check.py"),
        "--repo-root",
        ".",
        "--input-contract-schema",
        str(
            Path("src")
            / "qtt"
            / "stage1_prediction_markets"
            / "three_venue_canary_eligibility"
            / "stage1_three_venue_canary_eligibility_input_contract.schema.json"
        ),
        "--readiness-matrix-schema",
        str(
            Path("src")
            / "qtt"
            / "stage1_prediction_markets"
            / "three_venue_canary_eligibility"
            / "stage1_three_venue_platform_readiness_matrix.schema.json"
        ),
        "--handoff-schema",
        str(
            Path("src")
            / "qtt"
            / "stage1_prediction_markets"
            / "three_venue_canary_eligibility"
            / "stage1_owner_review_to_canary_eligibility_handoff.schema.json"
        ),
        "--gate-report-schema",
        str(
            Path("src")
            / "qtt"
            / "stage1_prediction_markets"
            / "three_venue_canary_eligibility"
            / "stage1_three_venue_canary_eligibility_gate_report.schema.json"
        ),
        "--execution-block-schema",
        str(
            Path("src")
            / "qtt"
            / "stage1_prediction_markets"
            / "three_venue_canary_eligibility"
            / "stage1_limited_live_canary_execution_block.schema.json"
        ),
        "--fixture",
        str(
            Path("tests")
            / "fixtures"
            / "source_evidence"
            / "three_venue_canary_eligibility"
            / "synthetic_stage1_three_venue_canary_eligibility_contracts.v1.fixture.json"
        ),
        "--out",
        str(
            Path("docs")
            / "master_plan"
            / "generated"
            / "Stage1ThreeVenueCanaryEligibilityContractCheck.report.json"
        ),
    ]


def test_runner_includes_section_coverage_dev_gate_after_three_venue_and_before_qtt_gate(
    monkeypatch,
):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands]

    three_venue_index = command_names.index(
        "stage1_three_venue_canary_eligibility_contract_check.py"
    )
    build_index = command_names.index("build_master_plan_section_coverage_report.py")
    validate_index = command_names.index("validate_master_plan_section_coverage.py")
    qtt_gate_index = command_names.index("qtt_test_gate.py")
    no_runtime_index = command_names.index("validate_no_runtime_artifacts.py")

    assert three_venue_index < build_index < validate_index < qtt_gate_index
    assert qtt_gate_index < no_runtime_index
    assert commands[build_index] == [
        python_executable,
        str(Path("tools") / "build_master_plan_section_coverage_report.py"),
    ]
    assert commands[validate_index] == [
        python_executable,
        str(Path("tools") / "validate_master_plan_section_coverage.py"),
        "--mode",
        "dev",
    ]
    assert "final" not in commands[validate_index]


def test_runner_stops_on_first_failure_and_returns_failing_exit_code(monkeypatch, capsys):
    class Completed:
        def __init__(self, returncode: int) -> None:
            self.returncode = returncode

    commands = [["python", "gate_a.py"], ["python", "gate_b.py"], ["python", "gate_c.py"]]
    returncodes = [0, 9, 0]
    seen: list[list[str]] = []

    def fake_run(command: list[str]) -> Completed:
        seen.append(command)
        return Completed(returncodes[len(seen) - 1])

    monkeypatch.setattr(runner.subprocess, "run", fake_run)

    exit_code = runner.run_commands(commands)

    assert exit_code == 9
    assert seen == commands[:2]
    assert runner.SUCCESS_MARKER not in capsys.readouterr().out


def test_runner_returns_zero_when_all_mocked_commands_pass(monkeypatch, capsys):
    class Completed:
        returncode = 0

    seen: list[list[str]] = []

    def fake_run(command: list[str]) -> Completed:
        seen.append(command)
        return Completed()

    monkeypatch.setattr(runner.subprocess, "run", fake_run)

    exit_code = runner.main([])

    assert exit_code == 0
    validation_dir = Path(seen[0][5]).parent
    assert seen == runner.build_validation_commands(validation_dir)
    assert capsys.readouterr().out.splitlines()[-1] == runner.SUCCESS_MARKER
