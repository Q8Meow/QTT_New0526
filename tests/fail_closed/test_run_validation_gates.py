import json
from pathlib import Path

from tools import (
    validate_atomicrows_research_provenance_evidence_tier_classification as research_provenance_gate,
)
from tools import (
    validate_atomicrows_owner_submitted_research_source_intake_registry as owner_intake_gate,
)
from tools import (
    validate_atomicrows_research_source_to_candidate_family_gate as candidate_family_gate,
)
from tools import (
    validate_atomicrows_parameter_stack_role_taxonomy as parameter_stack_role_gate,
)
from tools import (
    validate_atomicrows_parameter_stack_completeness_gate as parameter_stack_completeness_gate,
)
from tools import (
    validate_atomicrows_parameter_stack_compatibility_gate as parameter_stack_compatibility_gate,
)
from tools import validate_edge_parameter_stack_selection_packet as edge_packet_gate
from tools import validate_qtt_trade_context_packet as trade_context_gate
from tools import (
    validate_atomicrows_parameter_selection_universe_registry as selection_universe_gate,
)
from tools import (
    validate_atomicrows_parameter_selection_universe_consumer_gate as selection_universe_consumer_gate,
)
from tools import (
    validate_trade_context_selection_universe_routing_gate as trade_context_routing_gate,
)
from tools import (
    validate_quantum_applicability_classification_registry as quantum_applicability_gate,
)
from tools import (
    validate_owner_quantum_priority_policy_registry as owner_quantum_priority_gate,
)
from tools import (
    validate_parameter_algorithm_scoring_policy_registry as scoring_policy_gate,
)
from tools import (
    validate_parameter_stack_scoring_and_ranking_gate as stack_scoring_gate,
)
from tools import (
    validate_quantum_classical_optimizer_arbitration_gate as optimizer_arbitration_gate,
)
from tools import (
    validate_candidate_parameter_stack_generation_gate as candidate_generation_gate,
)
from tools import (
    validate_trade_context_parameter_stack_selection_gate as trade_context_stack_selection_gate,
)
from tools import (
    validate_selected_parameter_stack_handoff_packet as selected_stack_handoff_gate,
)
from tools import (
    validate_replay_paper_candidate_stack_competition_gate as replay_paper_competition_gate,
)
from tools import (
    validate_dual_result_review_for_parameter_stacks as dual_result_review_gate,
)
from tools import (
    validate_owner_live_promotion_review_for_parameter_stacks as owner_live_promotion_review_gate,
)
from tools import (
    validate_owner_approval_request_queue_registry as owner_approval_request_queue_gate,
)
from tools import (
    validate_owner_override_receipt_authoring_gate as owner_override_receipt_authoring_gate,
)
from tools import (
    validate_owner_dashboard_approval_menu_schema as owner_dashboard_approval_menu_schema_gate,
)
from tools import (
    validate_owner_dashboard_approval_static_screen_contract
    as owner_dashboard_approval_static_screen_contract_gate,
)
from tools import (
    validate_atomicrows_full_bundle_row_expansion_plan
    as atomicrows_full_bundle_row_expansion_plan_gate,
)
from tools import (
    validate_atomicrows_bundle_row_family_source_files
    as atomicrows_bundle_row_family_source_files_gate,
)
from tools import (
    validate_atomicrows_bundle_builder_deterministic_assembly_gate
    as atomicrows_bundle_builder_deterministic_assembly_gate,
)
from tools import (
    validate_atomicrows_bundle_sha_freeze_authority_gate
    as atomicrows_bundle_sha_freeze_authority_gate,
)
from tools import (
    validate_atomicrows_exact_row_authority_classifier_bridge
    as atomicrows_exact_row_authority_classifier_bridge,
)
from tools import validate_qtt_agent_algorithm_command_matrix as command_matrix_gate
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
            str(Path("tools") / "validate_qtt_agent_role_operating_charter_registry.py"),
            "--mode",
            "dev",
            "--repo-root",
            ".",
            "--out",
            str(
                Path("docs")
                / "master_plan"
                / "generated"
                / "QTTAgentRoleOperatingCharterReport.json"
            ),
        ],
        [
            python_executable,
            str(Path("tools") / "validate_qtt_algorithm_formula_family_registry.py"),
            "--mode",
            "dev",
            "--repo-root",
            ".",
            "--out",
            str(
                Path("docs")
                / "master_plan"
                / "generated"
                / "QTTAlgorithmFormulaFamilyReport.json"
            ),
        ],
        [
            python_executable,
            str(Path("tools") / "validate_qtt_agent_algorithm_binding_registry.py"),
            "--mode",
            "dev",
            "--repo-root",
            ".",
            "--out",
            str(
                Path("docs")
                / "master_plan"
                / "generated"
                / "QTTAgentAlgorithmBindingReport.json"
            ),
        ],
        [
            python_executable,
            str(Path("tools") / "validate_qtt_agent_algorithm_consumer_gate.py"),
            "--mode",
            "dev",
            "--repo-root",
            ".",
            "--out",
            str(
                Path("docs")
                / "master_plan"
                / "generated"
                / "QTTAgentAlgorithmConsumerGate.report.json"
            ),
        ],
        [
            python_executable,
            str(Path("tools") / "validate_qtt_agent_algorithm_cumulative_readiness_gate.py"),
            "--mode",
            "dev",
            "--repo-root",
            ".",
            "--out",
            str(
                Path("docs")
                / "master_plan"
                / "generated"
                / "QTTAgentAlgorithmCumulativeReadinessGate.report.json"
            ),
        ],
        [
            python_executable,
            str(Path("tools") / "validate_qtt_agent_algorithm_command_matrix.py"),
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
            str(
                Path("tools")
                / "validate_atomicrows_parameter_agent_binding_registry.py"
            ),
            "--mode",
            "dev",
            "--out",
            str(
                Path("docs")
                / "master_plan"
                / "generated"
                / "AtomicRowsParameterAgentBindingReport.json"
            ),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_atomicrows_parameter_agent_binding_consumer_gate.py"
            ),
            "--mode",
            "dev",
            "--out",
            str(
                Path("docs")
                / "master_plan"
                / "generated"
                / "AtomicRowsParameterAgentBindingConsumerGate.report.json"
            ),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_atomicrows_parameter_agent_binding_cumulative_readiness_gate.py"
            ),
            "--mode",
            "dev",
            "--out",
            str(
                Path("docs")
                / "master_plan"
                / "generated"
                / "AtomicRowsParameterAgentBindingCumulativeReadinessGate.report.json"
            ),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_atomicrows_parameter_agent_binding_command_matrix.py"
            ),
            "--mode",
            "dev",
            "--out",
            str(
                Path("docs")
                / "master_plan"
                / "generated"
                / "AtomicRowsParameterAgentBindingCommandMatrix.json"
            ),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_atomicrows_research_provenance_evidence_tier_classification.py"
            ),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_atomicrows_owner_submitted_research_source_intake_registry.py"
            ),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_atomicrows_research_source_to_candidate_family_gate.py"
            ),
        ],
        [
            python_executable,
            str(Path("tools") / "validate_atomicrows_parameter_stack_role_taxonomy.py"),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_atomicrows_parameter_stack_completeness_gate.py"
            ),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_atomicrows_parameter_stack_compatibility_gate.py"
            ),
        ],
        [
            python_executable,
            str(Path("tools") / "validate_edge_parameter_stack_selection_packet.py"),
        ],
        [
            python_executable,
            str(Path("tools") / "validate_qtt_trade_context_packet.py"),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_atomicrows_parameter_selection_universe_registry.py"
            ),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_atomicrows_parameter_selection_universe_consumer_gate.py"
            ),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_trade_context_selection_universe_routing_gate.py"
            ),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_quantum_applicability_classification_registry.py"
            ),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_owner_quantum_priority_policy_registry.py"
            ),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_parameter_algorithm_scoring_policy_registry.py"
            ),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_parameter_stack_scoring_and_ranking_gate.py"
            ),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_quantum_classical_optimizer_arbitration_gate.py"
            ),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_candidate_parameter_stack_generation_gate.py"
            ),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_trade_context_parameter_stack_selection_gate.py"
            ),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_selected_parameter_stack_handoff_packet.py"
            ),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_replay_paper_candidate_stack_competition_gate.py"
            ),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_dual_result_review_for_parameter_stacks.py"
            ),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_owner_live_promotion_review_for_parameter_stacks.py"
            ),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_owner_approval_request_queue_registry.py"
            ),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_owner_override_receipt_authoring_gate.py"
            ),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_owner_dashboard_approval_menu_schema.py"
            ),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_owner_dashboard_approval_static_screen_contract.py"
            ),
        ],
        [
            python_executable,
            str(Path("tools") / "validate_atomicrows_full_bundle_row_expansion_plan.py"),
        ],
        [
            python_executable,
            str(Path("tools") / "validate_atomicrows_bundle_row_family_source_files.py"),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_atomicrows_bundle_builder_deterministic_assembly_gate.py"
            ),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_atomicrows_bundle_sha_freeze_authority_gate.py"
            ),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_atomicrows_exact_row_authority_classifier_bridge.py"
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
    agent_charter_index = command_names.index(
        "validate_qtt_agent_role_operating_charter_registry.py"
    )
    algorithm_registry_index = command_names.index(
        "validate_qtt_algorithm_formula_family_registry.py"
    )
    agent_algorithm_binding_index = command_names.index(
        "validate_qtt_agent_algorithm_binding_registry.py"
    )
    agent_algorithm_consumer_gate_index = command_names.index(
        "validate_qtt_agent_algorithm_consumer_gate.py"
    )
    agent_algorithm_cumulative_readiness_index = command_names.index(
        "validate_qtt_agent_algorithm_cumulative_readiness_gate.py"
    )
    agent_algorithm_command_matrix_index = command_names.index(
        "validate_qtt_agent_algorithm_command_matrix.py"
    )
    source_evidence_index = command_names.index("validate_source_evidence_static.py")

    assert (
        scope_index
        < owner_override_index
        < agent_charter_index
        < algorithm_registry_index
        < agent_algorithm_binding_index
        < agent_algorithm_consumer_gate_index
        < agent_algorithm_cumulative_readiness_index
        < agent_algorithm_command_matrix_index
        < source_evidence_index
    )
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
    assert commands[agent_charter_index] == [
        python_executable,
        str(Path("tools") / "validate_qtt_agent_role_operating_charter_registry.py"),
        "--mode",
        "dev",
        "--repo-root",
        ".",
        "--out",
        str(
            Path("docs")
            / "master_plan"
            / "generated"
            / "QTTAgentRoleOperatingCharterReport.json"
        ),
    ]
    assert commands[algorithm_registry_index] == [
        python_executable,
        str(Path("tools") / "validate_qtt_algorithm_formula_family_registry.py"),
        "--mode",
        "dev",
        "--repo-root",
        ".",
        "--out",
        str(
            Path("docs")
            / "master_plan"
            / "generated"
            / "QTTAlgorithmFormulaFamilyReport.json"
        ),
    ]
    assert commands[agent_algorithm_binding_index] == [
        python_executable,
        str(Path("tools") / "validate_qtt_agent_algorithm_binding_registry.py"),
        "--mode",
        "dev",
        "--repo-root",
        ".",
        "--out",
        str(
            Path("docs")
            / "master_plan"
            / "generated"
            / "QTTAgentAlgorithmBindingReport.json"
        ),
    ]
    assert commands[agent_algorithm_consumer_gate_index] == [
        python_executable,
        str(Path("tools") / "validate_qtt_agent_algorithm_consumer_gate.py"),
        "--mode",
        "dev",
        "--repo-root",
        ".",
        "--out",
        str(
            Path("docs")
            / "master_plan"
            / "generated"
            / "QTTAgentAlgorithmConsumerGate.report.json"
        ),
    ]
    assert commands[agent_algorithm_cumulative_readiness_index] == [
        python_executable,
        str(Path("tools") / "validate_qtt_agent_algorithm_cumulative_readiness_gate.py"),
        "--mode",
        "dev",
        "--repo-root",
        ".",
        "--out",
        str(
            Path("docs")
            / "master_plan"
            / "generated"
            / "QTTAgentAlgorithmCumulativeReadinessGate.report.json"
        ),
    ]
    assert commands[agent_algorithm_command_matrix_index] == [
        python_executable,
        str(Path("tools") / "validate_qtt_agent_algorithm_command_matrix.py"),
    ]


def test_runner_exposes_agent_algorithm_command_matrix_success_marker():
    assert command_matrix_gate.SUCCESS_MARKER == "QTT_AGENT_ALGORITHM_COMMAND_MATRIX_OK"


def test_runner_exposes_atomicrows_research_provenance_success_marker():
    assert (
        research_provenance_gate.SUCCESS_MARKER
        == "ATOMICROWS_RESEARCH_PROVENANCE_EVIDENCE_TIER_CLASSIFICATION_OK"
    )


def test_runner_exposes_owner_submitted_research_source_intake_success_marker():
    assert (
        owner_intake_gate.SUCCESS_MARKER
        == "ATOMICROWS_OWNER_SUBMITTED_RESEARCH_SOURCE_INTAKE_REGISTRY_OK"
    )


def test_runner_exposes_research_source_to_candidate_family_gate_success_marker():
    assert (
        candidate_family_gate.SUCCESS_MARKER
        == "ATOMICROWS_RESEARCH_SOURCE_TO_CANDIDATE_FAMILY_GATE_OK"
    )


def test_runner_exposes_parameter_stack_role_taxonomy_success_marker():
    assert (
        parameter_stack_role_gate.SUCCESS_MARKER
        == "ATOMICROWS_PARAMETER_STACK_ROLE_TAXONOMY_OK"
    )


def test_runner_exposes_parameter_stack_completeness_gate_success_marker():
    assert (
        parameter_stack_completeness_gate.SUCCESS_MARKER
        == "ATOMICROWS_PARAMETER_STACK_COMPLETENESS_GATE_OK"
    )


def test_runner_exposes_parameter_stack_compatibility_gate_success_marker():
    assert (
        parameter_stack_compatibility_gate.SUCCESS_MARKER
        == "ATOMICROWS_PARAMETER_STACK_COMPATIBILITY_GATE_OK"
    )


def test_runner_exposes_edge_parameter_stack_selection_packet_success_marker():
    assert edge_packet_gate.SUCCESS_MARKER == "EDGE_PARAMETER_STACK_SELECTION_PACKET_SCHEMA_OK"


def test_runner_exposes_qtt_trade_context_packet_success_marker():
    assert trade_context_gate.SUCCESS_MARKER == "QTT_TRADE_CONTEXT_PACKET_SCHEMA_OK"


def test_runner_exposes_parameter_selection_universe_consumer_gate_success_marker():
    assert (
        selection_universe_consumer_gate.SUCCESS_MARKER
        == "ATOMICROWS_PARAMETER_SELECTION_UNIVERSE_CONSUMER_GATE_OK"
    )


def test_runner_exposes_trade_context_selection_universe_routing_gate_success_marker():
    assert (
        trade_context_routing_gate.SUCCESS_MARKER
        == "QTT_TRADE_CONTEXT_SELECTION_UNIVERSE_ROUTING_GATE_OK"
    )


def test_runner_exposes_quantum_applicability_classification_registry_success_marker():
    assert (
        quantum_applicability_gate.SUCCESS_MARKER
        == "QTT_QUANTUM_APPLICABILITY_CLASSIFICATION_REGISTRY_OK"
    )


def test_runner_exposes_owner_quantum_priority_policy_registry_success_marker():
    assert (
        owner_quantum_priority_gate.SUCCESS_MARKER
        == "QTT_OWNER_QUANTUM_PRIORITY_POLICY_REGISTRY_OK"
    )


def test_runner_exposes_parameter_algorithm_scoring_policy_registry_success_marker():
    assert (
        scoring_policy_gate.SUCCESS_MARKER
        == "QTT_PARAMETER_AND_ALGORITHM_SCORING_POLICY_REGISTRY_OK"
    )


def test_runner_exposes_parameter_stack_scoring_and_ranking_gate_success_marker():
    assert (
        stack_scoring_gate.SUCCESS_MARKER
        == "QTT_PARAMETER_STACK_SCORING_AND_RANKING_GATE_OK"
    )


def test_runner_exposes_quantum_classical_optimizer_arbitration_gate_success_marker():
    assert (
        optimizer_arbitration_gate.SUCCESS_MARKER
        == "QTT_QUANTUM_CLASSICAL_OPTIMIZER_ARBITRATION_GATE_OK"
    )


def test_runner_exposes_candidate_parameter_stack_generation_gate_success_marker():
    assert (
        candidate_generation_gate.SUCCESS_MARKER
        == "QTT_CANDIDATE_PARAMETER_STACK_GENERATION_GATE_OK"
    )


def test_runner_exposes_trade_context_parameter_stack_selection_gate_success_marker():
    assert (
        trade_context_stack_selection_gate.SUCCESS_MARKER
        == "QTT_TRADE_CONTEXT_PARAMETER_STACK_SELECTION_GATE_OK"
    )


def test_runner_exposes_selected_parameter_stack_handoff_packet_success_marker():
    assert (
        selected_stack_handoff_gate.SUCCESS_MARKER
        == "QTT_SELECTED_PARAMETER_STACK_HANDOFF_PACKET_OK"
    )


def test_runner_exposes_replay_paper_candidate_stack_competition_gate_success_marker():
    assert (
        replay_paper_competition_gate.SUCCESS_MARKER
        == "QTT_REPLAY_PAPER_CANDIDATE_STACK_COMPETITION_GATE_OK"
    )


def test_runner_exposes_dual_result_review_for_parameter_stacks_success_marker():
    assert (
        dual_result_review_gate.SUCCESS_MARKER
        == "QTT_DUAL_RESULT_REVIEW_FOR_PARAMETER_STACKS_OK"
    )


def test_runner_exposes_owner_live_promotion_review_for_parameter_stacks_success_marker():
    assert (
        owner_live_promotion_review_gate.SUCCESS_MARKER
        == "QTT_OWNER_LIVE_PROMOTION_REVIEW_FOR_PARAMETER_STACKS_OK"
    )


def test_runner_exposes_owner_approval_request_queue_registry_success_marker():
    assert (
        owner_approval_request_queue_gate.SUCCESS_MARKER
        == "QTT_OWNER_APPROVAL_REQUEST_QUEUE_REGISTRY_OK"
    )


def test_runner_exposes_owner_override_receipt_authoring_gate_success_marker():
    assert (
        owner_override_receipt_authoring_gate.SUCCESS_MARKER
        == "QTT_OWNER_OVERRIDE_RECEIPT_AUTHORING_GATE_OK"
    )


def test_runner_exposes_owner_dashboard_approval_menu_schema_success_marker():
    assert (
        owner_dashboard_approval_menu_schema_gate.SUCCESS_MARKER
        == "QTT_OWNER_DASHBOARD_APPROVAL_MENU_SCHEMA_OK"
    )


def test_runner_exposes_owner_dashboard_approval_static_screen_contract_success_marker():
    assert (
        owner_dashboard_approval_static_screen_contract_gate.SUCCESS_MARKER
        == "QTT_OWNER_DASHBOARD_APPROVAL_STATIC_SCREEN_CONTRACT_OK"
    )


def test_runner_exposes_atomicrows_full_bundle_row_expansion_plan_success_marker():
    assert (
        atomicrows_full_bundle_row_expansion_plan_gate.SUCCESS_MARKER
        == "QTT_ATOMICROWS_FULL_BUNDLE_ROW_EXPANSION_PLAN_OK"
    )


def test_runner_exposes_atomicrows_bundle_row_family_source_files_success_marker():
    assert (
        atomicrows_bundle_row_family_source_files_gate.SUCCESS_MARKER
        == "QTT_ATOMICROWS_BUNDLE_ROW_FAMILY_SOURCE_FILES_OK"
    )


def test_runner_exposes_atomicrows_bundle_builder_success_marker():
    assert (
        atomicrows_bundle_builder_deterministic_assembly_gate.SUCCESS_MARKER
        == "QTT_ATOMICROWS_BUNDLE_BUILDER_OK"
    )


def test_runner_exposes_atomicrows_bundle_sha_freeze_authority_gate_success_marker():
    assert (
        atomicrows_bundle_sha_freeze_authority_gate.SUCCESS_MARKER
        == "QTT_ATOMICROWS_BUNDLE_SHA_FREEZE_AUTHORITY_GATE_BLOCKED_OK"
    )


def test_runner_exposes_atomicrows_exact_row_authority_classifier_bridge_success_marker():
    assert (
        atomicrows_exact_row_authority_classifier_bridge.SUCCESS_MARKER
        == "QTT_ATOMICROWS_EXACT_ROW_AUTHORITY_CLASSIFIER_BRIDGE_OK"
    )


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


def test_runner_keeps_scope_runtime_live_order_profit_and_source_blocks(monkeypatch):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    scope_command = next(
        command
        for command in commands
        if command[1] == str(Path("tools") / "validate_first_pr_scope.py")
    )

    assert "--block-runtime" in scope_command
    assert "--block-live" in scope_command
    assert "--block-profit-claims" in scope_command
    assert "--block-source-retrieval" in scope_command
    assert "--block-source-acceptance" in scope_command
    assert "--block-connector-binding" in scope_command
    assert "--block-order-execution" in scope_command


def test_runner_orders_owner_intake_after_pr70_classifier(monkeypatch):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands]

    pr70_index = command_names.index(
        "validate_atomicrows_research_provenance_evidence_tier_classification.py"
    )
    owner_intake_index = command_names.index(
        "validate_atomicrows_owner_submitted_research_source_intake_registry.py"
    )
    candidate_family_index = command_names.index(
        "validate_atomicrows_research_source_to_candidate_family_gate.py"
    )
    parameter_stack_role_index = command_names.index(
        "validate_atomicrows_parameter_stack_role_taxonomy.py"
    )
    parameter_stack_completeness_index = command_names.index(
        "validate_atomicrows_parameter_stack_completeness_gate.py"
    )
    parameter_stack_compatibility_index = command_names.index(
        "validate_atomicrows_parameter_stack_compatibility_gate.py"
    )
    edge_packet_index = command_names.index(
        "validate_edge_parameter_stack_selection_packet.py"
    )
    trade_context_index = command_names.index("validate_qtt_trade_context_packet.py")
    selection_universe_index = command_names.index(
        "validate_atomicrows_parameter_selection_universe_registry.py"
    )
    generated_gate_index = command_names.index(
        "validate_generated_derivative_bootstrap_gate_static.py"
    )
    no_runtime_index = command_names.index("validate_no_runtime_artifacts.py")

    assert (
        pr70_index
        < owner_intake_index
        < candidate_family_index
        < parameter_stack_role_index
        < parameter_stack_completeness_index
        < parameter_stack_compatibility_index
        < edge_packet_index
        < trade_context_index
        < selection_universe_index
        < generated_gate_index
        < no_runtime_index
    )
    assert commands[pr70_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_atomicrows_research_provenance_evidence_tier_classification.py"
        ),
    ]
    assert commands[owner_intake_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_atomicrows_owner_submitted_research_source_intake_registry.py"
        ),
    ]
    assert commands[candidate_family_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_atomicrows_research_source_to_candidate_family_gate.py"
        ),
    ]
    assert commands[parameter_stack_role_index] == [
        python_executable,
        str(Path("tools") / "validate_atomicrows_parameter_stack_role_taxonomy.py"),
    ]
    assert commands[parameter_stack_completeness_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_atomicrows_parameter_stack_completeness_gate.py"
        ),
    ]
    assert commands[parameter_stack_compatibility_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_atomicrows_parameter_stack_compatibility_gate.py"
        ),
    ]
    assert commands[edge_packet_index] == [
        python_executable,
        str(Path("tools") / "validate_edge_parameter_stack_selection_packet.py"),
    ]
    assert commands[trade_context_index] == [
        python_executable,
        str(Path("tools") / "validate_qtt_trade_context_packet.py"),
    ]
    assert commands[selection_universe_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_atomicrows_parameter_selection_universe_registry.py"
        ),
    ]


def test_runner_pr74_completeness_gate_has_no_runtime_source_or_bundle_args(monkeypatch):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands]
    pr73_index = command_names.index("validate_atomicrows_parameter_stack_role_taxonomy.py")
    pr74_index = command_names.index(
        "validate_atomicrows_parameter_stack_completeness_gate.py"
    )
    pr70_index = command_names.index(
        "validate_atomicrows_research_provenance_evidence_tier_classification.py"
    )
    pr71_index = command_names.index(
        "validate_atomicrows_owner_submitted_research_source_intake_registry.py"
    )
    pr72_index = command_names.index(
        "validate_atomicrows_research_source_to_candidate_family_gate.py"
    )

    assert pr70_index < pr71_index < pr72_index < pr73_index < pr74_index
    assert commands[pr74_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_atomicrows_parameter_stack_completeness_gate.py"
        ),
    ]
    pr74_text = " ".join(commands[pr74_index]).lower()
    assert "source-retrieval" not in pr74_text
    assert "source-acceptance" not in pr74_text
    assert "connector" not in pr74_text
    assert "runtime" not in pr74_text
    assert "live" not in pr74_text
    assert "order" not in pr74_text
    assert "profit" not in pr74_text
    assert "atomicrows.bundle.jsonl" not in pr74_text
    assert "atomicrows.bundle.sha256" not in pr74_text


def test_runner_includes_pr75_compatibility_gate_after_pr74_and_before_generated_derivative(
    monkeypatch,
):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands]
    pr70_index = command_names.index(
        "validate_atomicrows_research_provenance_evidence_tier_classification.py"
    )
    pr71_index = command_names.index(
        "validate_atomicrows_owner_submitted_research_source_intake_registry.py"
    )
    pr72_index = command_names.index(
        "validate_atomicrows_research_source_to_candidate_family_gate.py"
    )
    pr73_index = command_names.index("validate_atomicrows_parameter_stack_role_taxonomy.py")
    pr74_index = command_names.index(
        "validate_atomicrows_parameter_stack_completeness_gate.py"
    )
    pr75_index = command_names.index(
        "validate_atomicrows_parameter_stack_compatibility_gate.py"
    )
    pr77_index = command_names.index("validate_edge_parameter_stack_selection_packet.py")
    generated_gate_index = command_names.index(
        "validate_generated_derivative_bootstrap_gate_static.py"
    )
    no_runtime_index = command_names.index("validate_no_runtime_artifacts.py")

    assert (
        pr70_index
        < pr71_index
        < pr72_index
        < pr73_index
        < pr74_index
        < pr75_index
        < pr77_index
        < generated_gate_index
        < no_runtime_index
    )
    assert commands[pr75_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_atomicrows_parameter_stack_compatibility_gate.py"
        ),
    ]
    assert commands[pr77_index] == [
        python_executable,
        str(Path("tools") / "validate_edge_parameter_stack_selection_packet.py"),
    ]


def test_runner_pr75_compatibility_gate_has_no_runtime_source_connector_or_future_args(
    monkeypatch,
):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands]
    pr75_command = commands[
        command_names.index("validate_atomicrows_parameter_stack_compatibility_gate.py")
    ]

    assert pr75_command == [
        python_executable,
        str(
            Path("tools")
            / "validate_atomicrows_parameter_stack_compatibility_gate.py"
        ),
    ]
    pr75_text = " ".join(pr75_command).lower()
    assert "source-retrieval" not in pr75_text
    assert "source-acceptance" not in pr75_text
    assert "connector" not in pr75_text
    assert "runtime" not in pr75_text
    assert "live" not in pr75_text
    assert "order" not in pr75_text
    assert "profit" not in pr75_text
    assert "replay" not in pr75_text
    assert "paper" not in pr75_text
    assert "quantum-backend" not in pr75_text
    assert "quantum-advantage" not in pr75_text
    assert "ranking" not in pr75_text
    assert "scoring" not in pr75_text
    assert "selection" not in pr75_text
    assert "arbitration" not in pr75_text
    assert "trade-context" not in pr75_text
    assert "candidate-stack" not in pr75_text
    assert "atomicrows.bundle.jsonl" not in pr75_text
    assert "atomicrows.bundle.sha256" not in pr75_text


def test_pr75_static_contract_preserves_no_claim_boundaries():
    production = parameter_stack_compatibility_gate.load_yaml(
        parameter_stack_compatibility_gate.DEFAULT_PRODUCTION_GATE
    )
    flags = production["explicit_no_claim_flags"]
    future = production["future_consumer_contract"]
    quantum = production["quantum_compatibility_policy"]
    runtime = production["runtime_live_order_boundary_policy"]
    source = production["source_evidence_boundary_policy"]
    connector = production["connector_semantic_boundary_policy"]

    assert source["source_retrieval_created"] is False
    assert source["source_acceptance_created"] is False
    assert source["accepted_source_packets_created"] is False
    assert connector["connector_semantics_created"] is False
    assert connector["connector_semantic_binding_created"] is False
    assert runtime["runtime_artifacts_created"] is False
    assert runtime["live_readiness_created"] is False
    assert runtime["runtime_live_use_created"] is False
    assert runtime["order_authority_created"] is False
    assert runtime["cash_receipts_created"] is False
    assert runtime["order_receipts_created"] is False
    assert runtime["fill_receipts_created"] is False
    assert flags["creates_profit_evidence"] is False
    assert flags["creates_replay_results"] is False
    assert flags["creates_paper_results"] is False
    assert quantum["quantum_backend_execution_created"] is False
    assert flags["creates_quantum_backend_evidence"] is False
    assert quantum["quantum_advantage_claim_created"] is False
    assert flags["creates_quantum_advantage_claim"] is False
    assert flags["creates_scoring"] is False
    assert flags["creates_ranking"] is False
    assert flags["creates_stack_selection"] is False
    assert flags["creates_optimizer_arbitration"] is False
    assert flags["creates_trade_context_routing"] is False
    assert flags["creates_candidate_stack_generation"] is False
    assert future["this_gate_performs_scoring"] is False
    assert future["this_gate_performs_ranking"] is False
    assert future["this_gate_performs_selection"] is False
    assert future["this_gate_performs_arbitration"] is False
    assert future["this_gate_routes_trade_context"] is False
    assert future["this_gate_executes_replay_or_paper"] is False
    assert future["this_gate_executes_runtime_or_live"] is False
    assert not (
        Path(".") / parameter_stack_compatibility_gate.CANONICAL_BUNDLE_JSONL
    ).exists()
    assert not (
        Path(".") / parameter_stack_compatibility_gate.CANONICAL_BUNDLE_SHA256
    ).exists()


def test_runner_includes_pr77_edge_packet_after_pr75_and_before_generated_derivative(
    monkeypatch,
):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands]

    pr70_index = command_names.index(
        "validate_atomicrows_research_provenance_evidence_tier_classification.py"
    )
    pr71_index = command_names.index(
        "validate_atomicrows_owner_submitted_research_source_intake_registry.py"
    )
    pr72_index = command_names.index(
        "validate_atomicrows_research_source_to_candidate_family_gate.py"
    )
    pr73_index = command_names.index("validate_atomicrows_parameter_stack_role_taxonomy.py")
    pr74_index = command_names.index(
        "validate_atomicrows_parameter_stack_completeness_gate.py"
    )
    pr75_index = command_names.index(
        "validate_atomicrows_parameter_stack_compatibility_gate.py"
    )
    pr77_index = command_names.index("validate_edge_parameter_stack_selection_packet.py")
    generated_gate_index = command_names.index(
        "validate_generated_derivative_bootstrap_gate_static.py"
    )

    assert (
        pr70_index
        < pr71_index
        < pr72_index
        < pr73_index
        < pr74_index
        < pr75_index
        < pr77_index
        < generated_gate_index
    )
    assert commands[pr77_index] == [
        python_executable,
        str(Path("tools") / "validate_edge_parameter_stack_selection_packet.py"),
    ]


def test_runner_includes_pr78_trade_context_packet_after_pr77_and_before_pr79(
    monkeypatch,
):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands]

    pr70_index = command_names.index(
        "validate_atomicrows_research_provenance_evidence_tier_classification.py"
    )
    pr71_index = command_names.index(
        "validate_atomicrows_owner_submitted_research_source_intake_registry.py"
    )
    pr72_index = command_names.index(
        "validate_atomicrows_research_source_to_candidate_family_gate.py"
    )
    pr73_index = command_names.index("validate_atomicrows_parameter_stack_role_taxonomy.py")
    pr74_index = command_names.index(
        "validate_atomicrows_parameter_stack_completeness_gate.py"
    )
    pr75_index = command_names.index(
        "validate_atomicrows_parameter_stack_compatibility_gate.py"
    )
    pr77_index = command_names.index("validate_edge_parameter_stack_selection_packet.py")
    pr78_index = command_names.index("validate_qtt_trade_context_packet.py")
    pr79_index = command_names.index(
        "validate_atomicrows_parameter_selection_universe_registry.py"
    )
    generated_gate_index = command_names.index(
        "validate_generated_derivative_bootstrap_gate_static.py"
    )

    assert (
        pr70_index
        < pr71_index
        < pr72_index
        < pr73_index
        < pr74_index
        < pr75_index
        < pr77_index
        < pr78_index
        < pr79_index
        < generated_gate_index
    )
    assert commands[pr78_index] == [
        python_executable,
        str(Path("tools") / "validate_qtt_trade_context_packet.py"),
    ]
    assert commands[pr79_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_atomicrows_parameter_selection_universe_registry.py"
        ),
    ]


def test_runner_pr77_edge_packet_has_no_runtime_source_connector_or_live_args(
    monkeypatch,
):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands]
    pr77_command = commands[
        command_names.index("validate_edge_parameter_stack_selection_packet.py")
    ]

    assert pr77_command == [
        python_executable,
        str(Path("tools") / "validate_edge_parameter_stack_selection_packet.py"),
    ]
    pr77_text = " ".join(pr77_command).lower()
    assert "source-retrieval" not in pr77_text
    assert "source-acceptance" not in pr77_text
    assert "connector-binding" not in pr77_text
    assert "runtime-live" not in pr77_text
    assert "live-use" not in pr77_text
    assert "order-authority" not in pr77_text
    assert "profit-evidence" not in pr77_text
    assert "replay-execution" not in pr77_text
    assert "paper-execution" not in pr77_text
    assert "quantum-backend" not in pr77_text
    assert "quantum-advantage" not in pr77_text
    assert "atomicrows.bundle.jsonl" not in pr77_text
    assert "atomicrows.bundle.sha256" not in pr77_text


def test_pr77_static_contract_preserves_no_claim_boundaries():
    production = edge_packet_gate.load_yaml(edge_packet_gate.DEFAULT_PRODUCTION_PACKET)
    flags = production["explicit_no_claim_flags"]
    future = production["future_consumer_contract"]
    quantum = production["quantum_advisory_policy"]
    source = production["source_evidence_boundary_policy"]
    bundle = production["atomicrows_bundle_boundary_policy"]
    readiness = production["production_readiness"]
    static_policy = production["static_packet_policy"]

    assert production["selected_stack_id"] == "SYNTHETIC_SELECTED_STACK_ID_SCHEMA_FIELD_ONLY"
    assert production["candidate_stack_generation_count"] == 0
    assert production["replay_paper_competition_required_flag"] is True
    assert production["owner_review_required_flag"] is True
    assert source["source_retrieval_created"] is False
    assert source["source_acceptance_created"] is False
    assert source["accepted_source_packets_created"] is False
    assert source["source_dependency_state_is_static_metadata_only"] is True
    assert bundle["atomicrows_bundle_digest_ref_static_placeholder_allowed"] is True
    assert bundle["atomicrows_bundle_file_created_by_this_pr"] is False
    assert bundle["atomicrows_bundle_sha_created_by_this_pr"] is False
    assert bundle["atomicrows_bundle_hash_authority_created_by_this_pr"] is False
    assert bundle["atomicrows_bundle_rows_created_by_this_pr"] is False
    assert quantum["selected_quantum_advisory_family_ids_required"] is True
    assert quantum["quantum_advisory_static_metadata_only"] is True
    assert quantum["quantum_backend_execution_created"] is False
    assert quantum["quantum_advantage_claim_created"] is False
    assert quantum["quantum_scoring_created"] is False
    assert quantum["quantum_ranking_created"] is False
    assert quantum["quantum_selection_created"] is False
    assert quantum["quantum_arbitration_created"] is False
    assert readiness["edge_parameter_stack_selection_packet_schema_ready"] is True
    assert readiness["production_edge_packet_evaluated"] is False
    assert readiness["production_edge_packet_ready"] is False
    assert readiness["production_stack_selected"] is False
    assert readiness["final_ready"] is False
    assert static_policy["selected_stack_id_is_static_schema_field_only"] is True
    assert all(flags[field] is False for field in edge_packet_gate.EXPLICIT_NO_CLAIM_FALSE_FIELDS)
    assert all(future[field] is False for field in edge_packet_gate.FUTURE_CONSUMER_FALSE_FIELDS)
    assert not (Path(".") / edge_packet_gate.CANONICAL_BUNDLE_JSONL).exists()
    assert not (Path(".") / edge_packet_gate.CANONICAL_BUNDLE_SHA256).exists()
    assert (Path(".") / edge_packet_gate.PR76_SHORT_TEST).exists()
    assert not (Path(".") / edge_packet_gate.PR76_OLD_LONG_TEST).exists()


def test_runner_pr78_trade_context_packet_has_no_runtime_source_connector_or_live_args(
    monkeypatch,
):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands]
    pr78_command = commands[command_names.index("validate_qtt_trade_context_packet.py")]

    assert pr78_command == [
        python_executable,
        str(Path("tools") / "validate_qtt_trade_context_packet.py"),
    ]
    pr78_text = " ".join(pr78_command).lower()
    assert "source-retrieval" not in pr78_text
    assert "source-acceptance" not in pr78_text
    assert "connector-binding" not in pr78_text
    assert "runtime-live" not in pr78_text
    assert "live-use" not in pr78_text
    assert "order-authority" not in pr78_text
    assert "profit-evidence" not in pr78_text
    assert "replay-execution" not in pr78_text
    assert "paper-execution" not in pr78_text
    assert "quantum-backend" not in pr78_text
    assert "quantum-advantage" not in pr78_text
    assert "atomicrows.bundle.jsonl" not in pr78_text
    assert "atomicrows.bundle.sha256" not in pr78_text


def test_pr78_static_contract_preserves_no_claim_boundaries():
    production = trade_context_gate.load_yaml(trade_context_gate.DEFAULT_PRODUCTION_PACKET)
    flags = production["explicit_no_claim_flags"]
    future = production["future_consumer_contract"]
    quantum = production["quantum_priority_boundary_policy"]
    source = production["source_evidence_boundary_policy"]
    connector = production["connector_semantic_boundary_policy"]
    runtime = production["runtime_live_order_boundary_policy"]
    readiness = production["production_readiness"]
    context = production["context_static_policy"]

    assert context["trade_context_is_static_schema_only"] is True
    assert context["trade_context_routes_selection_universe"] is False
    assert context["trade_context_selects_stack"] is False
    assert context["trade_context_scores_stack"] is False
    assert context["trade_context_ranks_stack"] is False
    assert context["trade_context_arbitrates_optimizer"] is False
    assert context["trade_context_executes_replay_or_paper"] is False
    assert context["trade_context_executes_runtime_or_live"] is False
    assert source["source_retrieval_created"] is False
    assert source["source_acceptance_created"] is False
    assert source["accepted_source_packets_created"] is False
    assert connector["connector_semantics_created"] is False
    assert connector["connector_semantic_binding_created"] is False
    assert runtime["runtime_artifacts_created"] is False
    assert runtime["runtime_resolver_execution_created"] is False
    assert runtime["runtime_live_use_created"] is False
    assert runtime["order_authority_created"] is False
    assert runtime["profit_evidence_created"] is False
    assert quantum["quantum_backend_execution_created"] is False
    assert quantum["quantum_advantage_claim_created"] is False
    assert quantum["quantum_selection_created"] is False
    assert quantum["quantum_arbitration_created"] is False
    assert readiness["qtt_trade_context_packet_schema_ready"] is True
    assert readiness["production_trade_context_evaluated"] is False
    assert readiness["production_trade_context_ready"] is False
    assert readiness["production_routing_ready"] is False
    assert readiness["production_selection_ready"] is False
    assert readiness["final_ready"] is False
    assert all(flags[field] is False for field in trade_context_gate.EXPLICIT_NO_CLAIM_FALSE_FIELDS)
    assert all(future[field] is False for field in trade_context_gate.FUTURE_CONSUMER_FALSE_FIELDS)
    assert not (Path(".") / trade_context_gate.CANONICAL_BUNDLE_JSONL).exists()
    assert not (Path(".") / trade_context_gate.CANONICAL_BUNDLE_SHA256).exists()
    assert (Path(".") / trade_context_gate.PR76_SHORT_TEST).exists()
    assert not (Path(".") / trade_context_gate.PR76_OLD_LONG_TEST).exists()


def test_runner_pr79_selection_universe_registry_has_no_runtime_source_connector_or_live_args(
    monkeypatch,
):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands]
    pr79_command = commands[
        command_names.index("validate_atomicrows_parameter_selection_universe_registry.py")
    ]

    assert pr79_command == [
        python_executable,
        str(
            Path("tools")
            / "validate_atomicrows_parameter_selection_universe_registry.py"
        ),
    ]
    pr79_text = " ".join(pr79_command).lower()
    assert "source-retrieval" not in pr79_text
    assert "source-acceptance" not in pr79_text
    assert "connector-binding" not in pr79_text
    assert "runtime-live" not in pr79_text
    assert "live-use" not in pr79_text
    assert "order-authority" not in pr79_text
    assert "profit-evidence" not in pr79_text
    assert "replay-execution" not in pr79_text
    assert "paper-execution" not in pr79_text
    assert "quantum-backend" not in pr79_text
    assert "quantum-advantage" not in pr79_text
    assert "consumer-gate" not in pr79_text
    assert "routing-gate" not in pr79_text
    assert "score" not in pr79_text
    assert "ranking" not in pr79_text
    assert "arbitration" not in pr79_text
    assert "candidate-stack" not in pr79_text
    assert "atomicrows.bundle.jsonl" not in pr79_text
    assert "atomicrows.bundle.sha256" not in pr79_text


def test_pr79_static_contract_preserves_no_claim_boundaries():
    production = selection_universe_gate.load_yaml(
        selection_universe_gate.DEFAULT_PRODUCTION_REGISTRY
    )
    flags = production["explicit_no_claim_flags"]
    static = production["registry_static_policy"]
    membership = production["universe_membership_policy"]
    source = production["source_evidence_boundary_policy"]
    connector = production["connector_semantic_boundary_policy"]
    runtime = production["runtime_live_order_boundary_policy"]
    quantum = production["quantum_universe_policy"]
    readiness = production["production_readiness"]
    future = production["future_consumer_contract"]

    assert static["selection_universe_consumer_gate_created"] is False
    assert static["trade_context_to_selection_universe_routing_created"] is False
    assert static["route_result_created"] is False
    assert static["selected_stack_created"] is False
    assert static["stack_selection_created"] is False
    assert static["scoring_created"] is False
    assert static["ranking_created"] is False
    assert static["optimizer_arbitration_created"] is False
    assert static["candidate_stack_generation_created"] is False
    assert static["replay_paper_execution_created"] is False
    assert static["runtime_live_order_authority_created"] is False
    assert static["member_row_ids_created"] is False
    assert membership["membership_uses_random_sampling"] is False
    assert membership["membership_evaluated_against_live_data"] is False
    assert source["source_retrieval_created"] is False
    assert source["source_acceptance_created"] is False
    assert source["accepted_source_packets_created"] is False
    assert connector["connector_semantics_created"] is False
    assert connector["connector_semantic_binding_created"] is False
    assert runtime["runtime_artifacts_created"] is False
    assert runtime["runtime_resolver_execution_created"] is False
    assert runtime["live_readiness_created"] is False
    assert runtime["runtime_live_use_created"] is False
    assert runtime["private_state_fetch_created"] is False
    assert runtime["order_intent_authority_created"] is False
    assert runtime["order_authority_created"] is False
    assert runtime["cash_receipts_created"] is False
    assert runtime["order_receipts_created"] is False
    assert runtime["fill_receipts_created"] is False
    assert runtime["profit_evidence_created"] is False
    assert quantum["quantum_backend_execution_created"] is False
    assert quantum["quantum_advantage_claim_created"] is False
    assert quantum["quantum_selection_created"] is False
    assert quantum["quantum_arbitration_created"] is False
    assert future["this_pr_performs_selection_universe_consumer_gate"] is False
    assert future["this_pr_performs_routing"] is False
    assert future["this_pr_performs_scoring"] is False
    assert future["this_pr_performs_ranking"] is False
    assert future["this_pr_performs_arbitration"] is False
    assert future["this_pr_generates_candidate_stacks"] is False
    assert future["this_pr_executes_replay_or_paper"] is False
    assert future["this_pr_executes_runtime_or_live"] is False
    assert readiness["atomicrows_parameter_selection_universe_registry_ready"] is True
    assert readiness["production_selection_universe_registry_evaluated"] is False
    assert readiness["production_selection_universe_registry_ready"] is False
    assert readiness["production_universe_membership_evaluated"] is False
    assert readiness["production_routing_ready"] is False
    assert readiness["production_selection_ready"] is False
    assert readiness["final_ready"] is False
    assert all(
        flags[field] is False
        for field in selection_universe_gate.EXPLICIT_NO_CLAIM_FALSE_FIELDS
    )
    assert not (Path(".") / selection_universe_gate.CANONICAL_BUNDLE_JSONL).exists()
    assert not (Path(".") / selection_universe_gate.CANONICAL_BUNDLE_SHA256).exists()
    assert (Path(".") / selection_universe_gate.PR76_SHORT_TEST).exists()
    assert not (Path(".") / selection_universe_gate.PR76_OLD_LONG_TEST).exists()


def test_runner_includes_pr80_pr81_pr82_pr83_pr84_pr85_pr86_pr87_pr88_pr89_pr90_pr91_pr92_and_pr93_gates_after_pr79(
    monkeypatch,
):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands]

    pr70_index = command_names.index(
        "validate_atomicrows_research_provenance_evidence_tier_classification.py"
    )
    pr71_index = command_names.index(
        "validate_atomicrows_owner_submitted_research_source_intake_registry.py"
    )
    pr72_index = command_names.index(
        "validate_atomicrows_research_source_to_candidate_family_gate.py"
    )
    pr73_index = command_names.index("validate_atomicrows_parameter_stack_role_taxonomy.py")
    pr74_index = command_names.index(
        "validate_atomicrows_parameter_stack_completeness_gate.py"
    )
    pr75_index = command_names.index(
        "validate_atomicrows_parameter_stack_compatibility_gate.py"
    )
    pr77_index = command_names.index("validate_edge_parameter_stack_selection_packet.py")
    pr78_index = command_names.index("validate_qtt_trade_context_packet.py")
    pr79_index = command_names.index(
        "validate_atomicrows_parameter_selection_universe_registry.py"
    )
    pr80_index = command_names.index(
        "validate_atomicrows_parameter_selection_universe_consumer_gate.py"
    )
    pr81_index = command_names.index(
        "validate_trade_context_selection_universe_routing_gate.py"
    )
    pr82_index = command_names.index(
        "validate_quantum_applicability_classification_registry.py"
    )
    pr83_index = command_names.index(
        "validate_owner_quantum_priority_policy_registry.py"
    )
    pr84_index = command_names.index(
        "validate_parameter_algorithm_scoring_policy_registry.py"
    )
    pr85_index = command_names.index(
        "validate_parameter_stack_scoring_and_ranking_gate.py"
    )
    pr86_index = command_names.index(
        "validate_quantum_classical_optimizer_arbitration_gate.py"
    )
    pr87_index = command_names.index(
        "validate_candidate_parameter_stack_generation_gate.py"
    )
    pr88_index = command_names.index(
        "validate_trade_context_parameter_stack_selection_gate.py"
    )
    pr89_index = command_names.index(
        "validate_selected_parameter_stack_handoff_packet.py"
    )
    pr90_index = command_names.index(
        "validate_replay_paper_candidate_stack_competition_gate.py"
    )
    pr91_index = command_names.index(
        "validate_dual_result_review_for_parameter_stacks.py"
    )
    pr92_index = command_names.index(
        "validate_owner_live_promotion_review_for_parameter_stacks.py"
    )
    pr93_index = command_names.index(
        "validate_owner_approval_request_queue_registry.py"
    )
    pr94_index = command_names.index(
        "validate_owner_override_receipt_authoring_gate.py"
    )
    pr95_index = command_names.index(
        "validate_owner_dashboard_approval_menu_schema.py"
    )
    pr96_index = command_names.index(
        "validate_owner_dashboard_approval_static_screen_contract.py"
    )
    pr97_index = command_names.index(
        "validate_atomicrows_full_bundle_row_expansion_plan.py"
    )
    pr98_index = command_names.index(
        "validate_atomicrows_bundle_row_family_source_files.py"
    )
    pr99_index = command_names.index(
        "validate_atomicrows_bundle_builder_deterministic_assembly_gate.py"
    )
    pr100_index = command_names.index(
        "validate_atomicrows_bundle_sha_freeze_authority_gate.py"
    )
    repair_bridge_index = command_names.index(
        "validate_atomicrows_exact_row_authority_classifier_bridge.py"
    )
    generated_gate_index = command_names.index(
        "validate_generated_derivative_bootstrap_gate_static.py"
    )
    no_runtime_index = command_names.index("validate_no_runtime_artifacts.py")

    assert (
        pr70_index
        < pr71_index
        < pr72_index
        < pr73_index
        < pr74_index
        < pr75_index
        < pr77_index
        < pr78_index
        < pr79_index
        < pr80_index
        < pr81_index
        < pr82_index
        < pr83_index
        < pr84_index
        < pr85_index
        < pr86_index
        < pr87_index
        < pr88_index
        < pr89_index
        < pr90_index
        < pr91_index
        < pr92_index
        < pr93_index
        < pr94_index
        < pr95_index
        < pr96_index
        < pr97_index
        < pr98_index
        < pr99_index
        < pr100_index
        < repair_bridge_index
        < generated_gate_index
        < no_runtime_index
    )
    assert commands[pr80_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_atomicrows_parameter_selection_universe_consumer_gate.py"
        ),
    ]
    assert commands[pr81_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_trade_context_selection_universe_routing_gate.py"
        ),
    ]
    assert commands[pr82_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_quantum_applicability_classification_registry.py"
        ),
    ]
    assert commands[pr83_index] == [
        python_executable,
        str(Path("tools") / "validate_owner_quantum_priority_policy_registry.py"),
    ]
    assert commands[pr84_index] == [
        python_executable,
        str(Path("tools") / "validate_parameter_algorithm_scoring_policy_registry.py"),
    ]
    assert commands[pr85_index] == [
        python_executable,
        str(Path("tools") / "validate_parameter_stack_scoring_and_ranking_gate.py"),
    ]
    assert commands[pr86_index] == [
        python_executable,
        str(Path("tools") / "validate_quantum_classical_optimizer_arbitration_gate.py"),
    ]
    assert commands[pr87_index] == [
        python_executable,
        str(Path("tools") / "validate_candidate_parameter_stack_generation_gate.py"),
    ]
    assert commands[pr88_index] == [
        python_executable,
        str(Path("tools") / "validate_trade_context_parameter_stack_selection_gate.py"),
    ]
    assert commands[pr89_index] == [
        python_executable,
        str(Path("tools") / "validate_selected_parameter_stack_handoff_packet.py"),
    ]
    assert commands[pr90_index] == [
        python_executable,
        str(Path("tools") / "validate_replay_paper_candidate_stack_competition_gate.py"),
    ]
    assert commands[pr91_index] == [
        python_executable,
        str(Path("tools") / "validate_dual_result_review_for_parameter_stacks.py"),
    ]
    assert commands[pr92_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_owner_live_promotion_review_for_parameter_stacks.py"
        ),
    ]
    assert commands[pr93_index] == [
        python_executable,
        str(Path("tools") / "validate_owner_approval_request_queue_registry.py"),
    ]
    assert commands[pr94_index] == [
        python_executable,
        str(Path("tools") / "validate_owner_override_receipt_authoring_gate.py"),
    ]
    assert commands[pr95_index] == [
        python_executable,
        str(Path("tools") / "validate_owner_dashboard_approval_menu_schema.py"),
    ]
    assert commands[pr96_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_owner_dashboard_approval_static_screen_contract.py"
        ),
    ]
    assert commands[pr97_index] == [
        python_executable,
        str(Path("tools") / "validate_atomicrows_full_bundle_row_expansion_plan.py"),
    ]
    assert commands[pr98_index] == [
        python_executable,
        str(Path("tools") / "validate_atomicrows_bundle_row_family_source_files.py"),
    ]
    assert commands[pr99_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_atomicrows_bundle_builder_deterministic_assembly_gate.py"
        ),
    ]
    assert commands[pr100_index] == [
        python_executable,
        str(Path("tools") / "validate_atomicrows_bundle_sha_freeze_authority_gate.py"),
    ]
    assert commands[repair_bridge_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_atomicrows_exact_row_authority_classifier_bridge.py"
        ),
    ]


def test_runner_does_not_emit_success_marker_if_selection_universe_consumer_gate_fails(
    monkeypatch,
    capsys,
):
    class Completed:
        def __init__(self, returncode: int) -> None:
            self.returncode = returncode

    commands = [
        ["python", "validate_atomicrows_parameter_selection_universe_registry.py"],
        ["python", "validate_atomicrows_parameter_selection_universe_consumer_gate.py"],
        ["python", "later_gate.py"],
    ]
    returncodes = [0, 37, 0]
    seen: list[list[str]] = []

    def fake_run(command: list[str]) -> Completed:
        seen.append(command)
        return Completed(returncodes[len(seen) - 1])

    monkeypatch.setattr(runner.subprocess, "run", fake_run)

    exit_code = runner.run_commands(commands)

    assert exit_code == 37
    assert seen == commands[:2]
    assert runner.SUCCESS_MARKER not in capsys.readouterr().out


def test_runner_does_not_emit_success_marker_if_trade_context_routing_gate_fails(
    monkeypatch,
    capsys,
):
    class Completed:
        def __init__(self, returncode: int) -> None:
            self.returncode = returncode

    commands = [
        ["python", "validate_atomicrows_parameter_selection_universe_registry.py"],
        ["python", "validate_atomicrows_parameter_selection_universe_consumer_gate.py"],
        ["python", "validate_trade_context_selection_universe_routing_gate.py"],
        ["python", "later_gate.py"],
    ]
    returncodes = [0, 0, 41, 0]
    seen: list[list[str]] = []

    def fake_run(command: list[str]) -> Completed:
        seen.append(command)
        return Completed(returncodes[len(seen) - 1])

    monkeypatch.setattr(runner.subprocess, "run", fake_run)

    exit_code = runner.run_commands(commands)

    assert exit_code == 41
    assert seen == commands[:3]
    assert runner.SUCCESS_MARKER not in capsys.readouterr().out


def test_runner_does_not_emit_success_marker_if_quantum_applicability_gate_fails(
    monkeypatch,
    capsys,
):
    class Completed:
        def __init__(self, returncode: int) -> None:
            self.returncode = returncode

    commands = [
        ["python", "validate_atomicrows_parameter_selection_universe_registry.py"],
        ["python", "validate_atomicrows_parameter_selection_universe_consumer_gate.py"],
        ["python", "validate_trade_context_selection_universe_routing_gate.py"],
        ["python", "validate_quantum_applicability_classification_registry.py"],
        ["python", "later_gate.py"],
    ]
    returncodes = [0, 0, 0, 43, 0]
    seen: list[list[str]] = []

    def fake_run(command: list[str]) -> Completed:
        seen.append(command)
        return Completed(returncodes[len(seen) - 1])

    monkeypatch.setattr(runner.subprocess, "run", fake_run)

    exit_code = runner.run_commands(commands)

    assert exit_code == 43
    assert seen == commands[:4]
    assert runner.SUCCESS_MARKER not in capsys.readouterr().out


def test_runner_does_not_emit_success_marker_if_owner_quantum_priority_gate_fails(
    monkeypatch,
    capsys,
):
    class Completed:
        def __init__(self, returncode: int) -> None:
            self.returncode = returncode

    commands = [
        ["python", "validate_atomicrows_parameter_selection_universe_registry.py"],
        ["python", "validate_atomicrows_parameter_selection_universe_consumer_gate.py"],
        ["python", "validate_trade_context_selection_universe_routing_gate.py"],
        ["python", "validate_quantum_applicability_classification_registry.py"],
        ["python", "validate_owner_quantum_priority_policy_registry.py"],
        ["python", "later_gate.py"],
    ]
    returncodes = [0, 0, 0, 0, 47, 0]
    seen: list[list[str]] = []

    def fake_run(command: list[str]) -> Completed:
        seen.append(command)
        return Completed(returncodes[len(seen) - 1])

    monkeypatch.setattr(runner.subprocess, "run", fake_run)

    exit_code = runner.run_commands(commands)

    assert exit_code == 47
    assert seen == commands[:5]
    assert runner.SUCCESS_MARKER not in capsys.readouterr().out


def test_runner_does_not_emit_success_marker_if_parameter_algorithm_scoring_policy_gate_fails(
    monkeypatch,
    capsys,
):
    class Completed:
        def __init__(self, returncode: int) -> None:
            self.returncode = returncode

    commands = [
        ["python", "validate_atomicrows_parameter_selection_universe_registry.py"],
        ["python", "validate_atomicrows_parameter_selection_universe_consumer_gate.py"],
        ["python", "validate_trade_context_selection_universe_routing_gate.py"],
        ["python", "validate_quantum_applicability_classification_registry.py"],
        ["python", "validate_owner_quantum_priority_policy_registry.py"],
        ["python", "validate_parameter_algorithm_scoring_policy_registry.py"],
        ["python", "later_gate.py"],
    ]
    returncodes = [0, 0, 0, 0, 0, 53, 0]
    seen: list[list[str]] = []

    def fake_run(command: list[str]) -> Completed:
        seen.append(command)
        return Completed(returncodes[len(seen) - 1])

    monkeypatch.setattr(runner.subprocess, "run", fake_run)

    exit_code = runner.run_commands(commands)

    assert exit_code == 53
    assert seen == commands[:6]
    assert runner.SUCCESS_MARKER not in capsys.readouterr().out


def test_runner_does_not_emit_success_marker_if_parameter_stack_scoring_and_ranking_gate_fails(
    monkeypatch,
    capsys,
):
    class Completed:
        def __init__(self, returncode: int) -> None:
            self.returncode = returncode

    commands = [
        ["python", "validate_atomicrows_parameter_selection_universe_registry.py"],
        ["python", "validate_atomicrows_parameter_selection_universe_consumer_gate.py"],
        ["python", "validate_trade_context_selection_universe_routing_gate.py"],
        ["python", "validate_quantum_applicability_classification_registry.py"],
        ["python", "validate_owner_quantum_priority_policy_registry.py"],
        ["python", "validate_parameter_algorithm_scoring_policy_registry.py"],
        ["python", "validate_parameter_stack_scoring_and_ranking_gate.py"],
        ["python", "later_gate.py"],
    ]
    returncodes = [0, 0, 0, 0, 0, 0, 59, 0]
    seen: list[list[str]] = []

    def fake_run(command: list[str]) -> Completed:
        seen.append(command)
        return Completed(returncodes[len(seen) - 1])

    monkeypatch.setattr(runner.subprocess, "run", fake_run)

    exit_code = runner.run_commands(commands)

    assert exit_code == 59
    assert seen == commands[:7]
    assert runner.SUCCESS_MARKER not in capsys.readouterr().out


def test_runner_does_not_emit_success_marker_if_optimizer_arbitration_gate_fails(
    monkeypatch,
    capsys,
):
    class Completed:
        def __init__(self, returncode: int) -> None:
            self.returncode = returncode

    commands = [
        ["python", "validate_atomicrows_parameter_selection_universe_registry.py"],
        ["python", "validate_atomicrows_parameter_selection_universe_consumer_gate.py"],
        ["python", "validate_trade_context_selection_universe_routing_gate.py"],
        ["python", "validate_quantum_applicability_classification_registry.py"],
        ["python", "validate_owner_quantum_priority_policy_registry.py"],
        ["python", "validate_parameter_algorithm_scoring_policy_registry.py"],
        ["python", "validate_parameter_stack_scoring_and_ranking_gate.py"],
        ["python", "validate_quantum_classical_optimizer_arbitration_gate.py"],
        ["python", "later_gate.py"],
    ]
    returncodes = [0, 0, 0, 0, 0, 0, 0, 61, 0]
    seen: list[list[str]] = []

    def fake_run(command: list[str]) -> Completed:
        seen.append(command)
        return Completed(returncodes[len(seen) - 1])

    monkeypatch.setattr(runner.subprocess, "run", fake_run)

    exit_code = runner.run_commands(commands)

    assert exit_code == 61
    assert seen == commands[:8]
    assert runner.SUCCESS_MARKER not in capsys.readouterr().out


def test_runner_does_not_emit_success_marker_if_candidate_generation_gate_fails(
    monkeypatch,
    capsys,
):
    class Completed:
        def __init__(self, returncode: int) -> None:
            self.returncode = returncode

    commands = [
        ["python", "validate_atomicrows_parameter_selection_universe_registry.py"],
        ["python", "validate_atomicrows_parameter_selection_universe_consumer_gate.py"],
        ["python", "validate_trade_context_selection_universe_routing_gate.py"],
        ["python", "validate_quantum_applicability_classification_registry.py"],
        ["python", "validate_owner_quantum_priority_policy_registry.py"],
        ["python", "validate_parameter_algorithm_scoring_policy_registry.py"],
        ["python", "validate_parameter_stack_scoring_and_ranking_gate.py"],
        ["python", "validate_quantum_classical_optimizer_arbitration_gate.py"],
        ["python", "validate_candidate_parameter_stack_generation_gate.py"],
        ["python", "later_gate.py"],
    ]
    returncodes = [0, 0, 0, 0, 0, 0, 0, 0, 62, 0]
    seen: list[list[str]] = []

    def fake_run(command: list[str]) -> Completed:
        seen.append(command)
        return Completed(returncodes[len(seen) - 1])

    monkeypatch.setattr(runner.subprocess, "run", fake_run)

    exit_code = runner.run_commands(commands)

    assert exit_code == 62
    assert seen == commands[:9]
    assert runner.SUCCESS_MARKER not in capsys.readouterr().out


def test_runner_does_not_emit_success_marker_if_selected_stack_handoff_gate_fails(
    monkeypatch,
    capsys,
):
    class Completed:
        def __init__(self, returncode: int) -> None:
            self.returncode = returncode

    commands = [
        ["python", "validate_atomicrows_parameter_selection_universe_registry.py"],
        ["python", "validate_atomicrows_parameter_selection_universe_consumer_gate.py"],
        ["python", "validate_trade_context_selection_universe_routing_gate.py"],
        ["python", "validate_quantum_applicability_classification_registry.py"],
        ["python", "validate_owner_quantum_priority_policy_registry.py"],
        ["python", "validate_parameter_algorithm_scoring_policy_registry.py"],
        ["python", "validate_parameter_stack_scoring_and_ranking_gate.py"],
        ["python", "validate_quantum_classical_optimizer_arbitration_gate.py"],
        ["python", "validate_candidate_parameter_stack_generation_gate.py"],
        ["python", "validate_trade_context_parameter_stack_selection_gate.py"],
        ["python", "validate_selected_parameter_stack_handoff_packet.py"],
        ["python", "later_gate.py"],
    ]
    returncodes = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 63, 0]
    seen: list[list[str]] = []

    def fake_run(command: list[str]) -> Completed:
        seen.append(command)
        return Completed(returncodes[len(seen) - 1])

    monkeypatch.setattr(runner.subprocess, "run", fake_run)

    exit_code = runner.run_commands(commands)

    assert exit_code == 63
    assert seen == commands[:11]
    assert runner.SUCCESS_MARKER not in capsys.readouterr().out


def test_runner_does_not_emit_success_marker_if_replay_paper_competition_gate_fails(
    monkeypatch,
    capsys,
):
    class Completed:
        def __init__(self, returncode: int) -> None:
            self.returncode = returncode

    commands = [
        ["python", "validate_atomicrows_parameter_selection_universe_registry.py"],
        ["python", "validate_atomicrows_parameter_selection_universe_consumer_gate.py"],
        ["python", "validate_trade_context_selection_universe_routing_gate.py"],
        ["python", "validate_quantum_applicability_classification_registry.py"],
        ["python", "validate_owner_quantum_priority_policy_registry.py"],
        ["python", "validate_parameter_algorithm_scoring_policy_registry.py"],
        ["python", "validate_parameter_stack_scoring_and_ranking_gate.py"],
        ["python", "validate_quantum_classical_optimizer_arbitration_gate.py"],
        ["python", "validate_candidate_parameter_stack_generation_gate.py"],
        ["python", "validate_trade_context_parameter_stack_selection_gate.py"],
        ["python", "validate_selected_parameter_stack_handoff_packet.py"],
        ["python", "validate_replay_paper_candidate_stack_competition_gate.py"],
        ["python", "later_gate.py"],
    ]
    returncodes = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 64, 0]
    seen: list[list[str]] = []

    def fake_run(command: list[str]) -> Completed:
        seen.append(command)
        return Completed(returncodes[len(seen) - 1])

    monkeypatch.setattr(runner.subprocess, "run", fake_run)

    exit_code = runner.run_commands(commands)

    assert exit_code == 64
    assert seen == commands[:12]
    assert runner.SUCCESS_MARKER not in capsys.readouterr().out


def test_runner_does_not_emit_success_marker_if_dual_result_review_gate_fails(
    monkeypatch,
    capsys,
):
    class Completed:
        def __init__(self, returncode: int) -> None:
            self.returncode = returncode

    commands = [
        ["python", "validate_atomicrows_parameter_selection_universe_registry.py"],
        ["python", "validate_atomicrows_parameter_selection_universe_consumer_gate.py"],
        ["python", "validate_trade_context_selection_universe_routing_gate.py"],
        ["python", "validate_quantum_applicability_classification_registry.py"],
        ["python", "validate_owner_quantum_priority_policy_registry.py"],
        ["python", "validate_parameter_algorithm_scoring_policy_registry.py"],
        ["python", "validate_parameter_stack_scoring_and_ranking_gate.py"],
        ["python", "validate_quantum_classical_optimizer_arbitration_gate.py"],
        ["python", "validate_candidate_parameter_stack_generation_gate.py"],
        ["python", "validate_trade_context_parameter_stack_selection_gate.py"],
        ["python", "validate_selected_parameter_stack_handoff_packet.py"],
        ["python", "validate_replay_paper_candidate_stack_competition_gate.py"],
        ["python", "validate_dual_result_review_for_parameter_stacks.py"],
        ["python", "later_gate.py"],
    ]
    returncodes = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 65, 0]
    seen: list[list[str]] = []

    def fake_run(command: list[str]) -> Completed:
        seen.append(command)
        return Completed(returncodes[len(seen) - 1])

    monkeypatch.setattr(runner.subprocess, "run", fake_run)

    exit_code = runner.run_commands(commands)

    assert exit_code == 65
    assert seen == commands[:13]
    assert runner.SUCCESS_MARKER not in capsys.readouterr().out


def test_runner_does_not_emit_success_marker_if_owner_live_promotion_review_gate_fails(
    monkeypatch,
    capsys,
):
    class Completed:
        def __init__(self, returncode: int) -> None:
            self.returncode = returncode

    commands = [
        ["python", "validate_atomicrows_parameter_selection_universe_registry.py"],
        ["python", "validate_atomicrows_parameter_selection_universe_consumer_gate.py"],
        ["python", "validate_trade_context_selection_universe_routing_gate.py"],
        ["python", "validate_quantum_applicability_classification_registry.py"],
        ["python", "validate_owner_quantum_priority_policy_registry.py"],
        ["python", "validate_parameter_algorithm_scoring_policy_registry.py"],
        ["python", "validate_parameter_stack_scoring_and_ranking_gate.py"],
        ["python", "validate_quantum_classical_optimizer_arbitration_gate.py"],
        ["python", "validate_candidate_parameter_stack_generation_gate.py"],
        ["python", "validate_trade_context_parameter_stack_selection_gate.py"],
        ["python", "validate_selected_parameter_stack_handoff_packet.py"],
        ["python", "validate_replay_paper_candidate_stack_competition_gate.py"],
        ["python", "validate_dual_result_review_for_parameter_stacks.py"],
        ["python", "validate_owner_live_promotion_review_for_parameter_stacks.py"],
        ["python", "later_gate.py"],
    ]
    returncodes = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 66, 0]
    seen: list[list[str]] = []

    def fake_run(command: list[str]) -> Completed:
        seen.append(command)
        return Completed(returncodes[len(seen) - 1])

    monkeypatch.setattr(runner.subprocess, "run", fake_run)

    exit_code = runner.run_commands(commands)

    assert exit_code == 66
    assert seen == commands[:14]
    assert runner.SUCCESS_MARKER not in capsys.readouterr().out


def test_runner_does_not_emit_success_marker_if_owner_approval_request_queue_gate_fails(
    monkeypatch,
    capsys,
):
    class Completed:
        def __init__(self, returncode: int) -> None:
            self.returncode = returncode

    commands = [
        ["python", "validate_atomicrows_parameter_selection_universe_registry.py"],
        ["python", "validate_atomicrows_parameter_selection_universe_consumer_gate.py"],
        ["python", "validate_trade_context_selection_universe_routing_gate.py"],
        ["python", "validate_quantum_applicability_classification_registry.py"],
        ["python", "validate_owner_quantum_priority_policy_registry.py"],
        ["python", "validate_parameter_algorithm_scoring_policy_registry.py"],
        ["python", "validate_parameter_stack_scoring_and_ranking_gate.py"],
        ["python", "validate_quantum_classical_optimizer_arbitration_gate.py"],
        ["python", "validate_candidate_parameter_stack_generation_gate.py"],
        ["python", "validate_trade_context_parameter_stack_selection_gate.py"],
        ["python", "validate_selected_parameter_stack_handoff_packet.py"],
        ["python", "validate_replay_paper_candidate_stack_competition_gate.py"],
        ["python", "validate_dual_result_review_for_parameter_stacks.py"],
        ["python", "validate_owner_live_promotion_review_for_parameter_stacks.py"],
        ["python", "validate_owner_approval_request_queue_registry.py"],
        ["python", "later_gate.py"],
    ]
    returncodes = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 67, 0]
    seen: list[list[str]] = []

    def fake_run(command: list[str]) -> Completed:
        seen.append(command)
        return Completed(returncodes[len(seen) - 1])

    monkeypatch.setattr(runner.subprocess, "run", fake_run)

    exit_code = runner.run_commands(commands)

    assert exit_code == 67
    assert seen == commands[:15]
    assert runner.SUCCESS_MARKER not in capsys.readouterr().out


def test_runner_does_not_emit_success_marker_if_owner_override_receipt_authoring_gate_fails(
    monkeypatch,
    capsys,
):
    class Completed:
        def __init__(self, returncode: int) -> None:
            self.returncode = returncode

    commands = [
        ["python", "validate_atomicrows_parameter_selection_universe_registry.py"],
        ["python", "validate_atomicrows_parameter_selection_universe_consumer_gate.py"],
        ["python", "validate_trade_context_selection_universe_routing_gate.py"],
        ["python", "validate_quantum_applicability_classification_registry.py"],
        ["python", "validate_owner_quantum_priority_policy_registry.py"],
        ["python", "validate_parameter_algorithm_scoring_policy_registry.py"],
        ["python", "validate_parameter_stack_scoring_and_ranking_gate.py"],
        ["python", "validate_quantum_classical_optimizer_arbitration_gate.py"],
        ["python", "validate_candidate_parameter_stack_generation_gate.py"],
        ["python", "validate_trade_context_parameter_stack_selection_gate.py"],
        ["python", "validate_selected_parameter_stack_handoff_packet.py"],
        ["python", "validate_replay_paper_candidate_stack_competition_gate.py"],
        ["python", "validate_dual_result_review_for_parameter_stacks.py"],
        ["python", "validate_owner_live_promotion_review_for_parameter_stacks.py"],
        ["python", "validate_owner_approval_request_queue_registry.py"],
        ["python", "validate_owner_override_receipt_authoring_gate.py"],
        ["python", "later_gate.py"],
    ]
    returncodes = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 68, 0]
    seen: list[list[str]] = []

    def fake_run(command: list[str]) -> Completed:
        seen.append(command)
        return Completed(returncodes[len(seen) - 1])

    monkeypatch.setattr(runner.subprocess, "run", fake_run)

    exit_code = runner.run_commands(commands)

    assert exit_code == 68
    assert seen == commands[:16]
    assert runner.SUCCESS_MARKER not in capsys.readouterr().out


def test_runner_does_not_emit_success_marker_if_owner_dashboard_approval_menu_schema_gate_fails(
    monkeypatch,
    capsys,
):
    class Completed:
        def __init__(self, returncode: int) -> None:
            self.returncode = returncode

    commands = [
        ["python", "validate_atomicrows_parameter_selection_universe_registry.py"],
        ["python", "validate_atomicrows_parameter_selection_universe_consumer_gate.py"],
        ["python", "validate_trade_context_selection_universe_routing_gate.py"],
        ["python", "validate_quantum_applicability_classification_registry.py"],
        ["python", "validate_owner_quantum_priority_policy_registry.py"],
        ["python", "validate_parameter_algorithm_scoring_policy_registry.py"],
        ["python", "validate_parameter_stack_scoring_and_ranking_gate.py"],
        ["python", "validate_quantum_classical_optimizer_arbitration_gate.py"],
        ["python", "validate_candidate_parameter_stack_generation_gate.py"],
        ["python", "validate_trade_context_parameter_stack_selection_gate.py"],
        ["python", "validate_selected_parameter_stack_handoff_packet.py"],
        ["python", "validate_replay_paper_candidate_stack_competition_gate.py"],
        ["python", "validate_dual_result_review_for_parameter_stacks.py"],
        ["python", "validate_owner_live_promotion_review_for_parameter_stacks.py"],
        ["python", "validate_owner_approval_request_queue_registry.py"],
        ["python", "validate_owner_override_receipt_authoring_gate.py"],
        ["python", "validate_owner_dashboard_approval_menu_schema.py"],
        ["python", "later_gate.py"],
    ]
    returncodes = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 69, 0]
    seen: list[list[str]] = []

    def fake_run(command: list[str]) -> Completed:
        seen.append(command)
        return Completed(returncodes[len(seen) - 1])

    monkeypatch.setattr(runner.subprocess, "run", fake_run)

    exit_code = runner.run_commands(commands)

    assert exit_code == 69
    assert seen == commands[:17]
    assert runner.SUCCESS_MARKER not in capsys.readouterr().out


def test_runner_does_not_emit_success_marker_if_owner_dashboard_approval_static_screen_contract_gate_fails(
    monkeypatch,
    capsys,
):
    class Completed:
        def __init__(self, returncode: int) -> None:
            self.returncode = returncode

    commands = [
        ["python", "validate_atomicrows_parameter_selection_universe_registry.py"],
        ["python", "validate_atomicrows_parameter_selection_universe_consumer_gate.py"],
        ["python", "validate_trade_context_selection_universe_routing_gate.py"],
        ["python", "validate_quantum_applicability_classification_registry.py"],
        ["python", "validate_owner_quantum_priority_policy_registry.py"],
        ["python", "validate_parameter_algorithm_scoring_policy_registry.py"],
        ["python", "validate_parameter_stack_scoring_and_ranking_gate.py"],
        ["python", "validate_quantum_classical_optimizer_arbitration_gate.py"],
        ["python", "validate_candidate_parameter_stack_generation_gate.py"],
        ["python", "validate_trade_context_parameter_stack_selection_gate.py"],
        ["python", "validate_selected_parameter_stack_handoff_packet.py"],
        ["python", "validate_replay_paper_candidate_stack_competition_gate.py"],
        ["python", "validate_dual_result_review_for_parameter_stacks.py"],
        ["python", "validate_owner_live_promotion_review_for_parameter_stacks.py"],
        ["python", "validate_owner_approval_request_queue_registry.py"],
        ["python", "validate_owner_override_receipt_authoring_gate.py"],
        ["python", "validate_owner_dashboard_approval_menu_schema.py"],
        ["python", "validate_owner_dashboard_approval_static_screen_contract.py"],
        ["python", "later_gate.py"],
    ]
    returncodes = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 70, 0]
    seen: list[list[str]] = []

    def fake_run(command: list[str]) -> Completed:
        seen.append(command)
        return Completed(returncodes[len(seen) - 1])

    monkeypatch.setattr(runner.subprocess, "run", fake_run)

    exit_code = runner.run_commands(commands)

    assert exit_code == 70
    assert seen == commands[:18]
    assert runner.SUCCESS_MARKER not in capsys.readouterr().out


def test_runner_does_not_emit_success_marker_if_atomicrows_full_bundle_row_expansion_plan_gate_fails(
    monkeypatch,
    capsys,
):
    class Completed:
        def __init__(self, returncode: int) -> None:
            self.returncode = returncode

    commands = [
        ["python", "validate_atomicrows_parameter_selection_universe_registry.py"],
        ["python", "validate_atomicrows_parameter_selection_universe_consumer_gate.py"],
        ["python", "validate_trade_context_selection_universe_routing_gate.py"],
        ["python", "validate_quantum_applicability_classification_registry.py"],
        ["python", "validate_owner_quantum_priority_policy_registry.py"],
        ["python", "validate_parameter_algorithm_scoring_policy_registry.py"],
        ["python", "validate_parameter_stack_scoring_and_ranking_gate.py"],
        ["python", "validate_quantum_classical_optimizer_arbitration_gate.py"],
        ["python", "validate_candidate_parameter_stack_generation_gate.py"],
        ["python", "validate_trade_context_parameter_stack_selection_gate.py"],
        ["python", "validate_selected_parameter_stack_handoff_packet.py"],
        ["python", "validate_replay_paper_candidate_stack_competition_gate.py"],
        ["python", "validate_dual_result_review_for_parameter_stacks.py"],
        ["python", "validate_owner_live_promotion_review_for_parameter_stacks.py"],
        ["python", "validate_owner_approval_request_queue_registry.py"],
        ["python", "validate_owner_override_receipt_authoring_gate.py"],
        ["python", "validate_owner_dashboard_approval_menu_schema.py"],
        ["python", "validate_owner_dashboard_approval_static_screen_contract.py"],
        ["python", "validate_atomicrows_full_bundle_row_expansion_plan.py"],
        ["python", "later_gate.py"],
    ]
    returncodes = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 71, 0]
    seen: list[list[str]] = []

    def fake_run(command: list[str]) -> Completed:
        seen.append(command)
        return Completed(returncodes[len(seen) - 1])

    monkeypatch.setattr(runner.subprocess, "run", fake_run)

    exit_code = runner.run_commands(commands)

    assert exit_code == 71
    assert seen == commands[:19]
    assert runner.SUCCESS_MARKER not in capsys.readouterr().out


def test_runner_does_not_emit_success_marker_if_atomicrows_bundle_row_family_source_files_gate_fails(
    monkeypatch,
    capsys,
):
    class Completed:
        def __init__(self, returncode: int) -> None:
            self.returncode = returncode

    commands = [
        ["python", "validate_atomicrows_parameter_selection_universe_registry.py"],
        ["python", "validate_atomicrows_parameter_selection_universe_consumer_gate.py"],
        ["python", "validate_trade_context_selection_universe_routing_gate.py"],
        ["python", "validate_quantum_applicability_classification_registry.py"],
        ["python", "validate_owner_quantum_priority_policy_registry.py"],
        ["python", "validate_parameter_algorithm_scoring_policy_registry.py"],
        ["python", "validate_parameter_stack_scoring_and_ranking_gate.py"],
        ["python", "validate_quantum_classical_optimizer_arbitration_gate.py"],
        ["python", "validate_candidate_parameter_stack_generation_gate.py"],
        ["python", "validate_trade_context_parameter_stack_selection_gate.py"],
        ["python", "validate_selected_parameter_stack_handoff_packet.py"],
        ["python", "validate_replay_paper_candidate_stack_competition_gate.py"],
        ["python", "validate_dual_result_review_for_parameter_stacks.py"],
        ["python", "validate_owner_live_promotion_review_for_parameter_stacks.py"],
        ["python", "validate_owner_approval_request_queue_registry.py"],
        ["python", "validate_owner_override_receipt_authoring_gate.py"],
        ["python", "validate_owner_dashboard_approval_menu_schema.py"],
        ["python", "validate_owner_dashboard_approval_static_screen_contract.py"],
        ["python", "validate_atomicrows_full_bundle_row_expansion_plan.py"],
        ["python", "validate_atomicrows_bundle_row_family_source_files.py"],
        ["python", "later_gate.py"],
    ]
    returncodes = [
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        72,
        0,
    ]
    seen: list[list[str]] = []

    def fake_run(command: list[str]) -> Completed:
        seen.append(command)
        return Completed(returncodes[len(seen) - 1])

    monkeypatch.setattr(runner.subprocess, "run", fake_run)

    exit_code = runner.run_commands(commands)

    assert exit_code == 72
    assert seen == commands[:20]
    assert runner.SUCCESS_MARKER not in capsys.readouterr().out


def test_runner_pr80_consumer_gate_has_no_runtime_source_connector_or_routing_args(
    monkeypatch,
):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands]
    pr80_command = commands[
        command_names.index(
            "validate_atomicrows_parameter_selection_universe_consumer_gate.py"
        )
    ]

    assert pr80_command == [
        python_executable,
        str(
            Path("tools")
            / "validate_atomicrows_parameter_selection_universe_consumer_gate.py"
        ),
    ]
    pr80_text = " ".join(pr80_command).lower()
    assert "source-retrieval" not in pr80_text
    assert "source-acceptance" not in pr80_text
    assert "connector-binding" not in pr80_text
    assert "runtime-live" not in pr80_text
    assert "live-use" not in pr80_text
    assert "order-authority" not in pr80_text
    assert "profit-evidence" not in pr80_text
    assert "replay-execution" not in pr80_text
    assert "paper-execution" not in pr80_text
    assert "quantum-backend" not in pr80_text
    assert "quantum-advantage" not in pr80_text
    assert "atomicrows.bundle.jsonl" not in pr80_text
    assert "atomicrows.bundle.sha256" not in pr80_text


def test_pr80_static_contract_preserves_consumer_gate_no_claim_boundaries():
    production = selection_universe_consumer_gate.load_yaml(
        selection_universe_consumer_gate.DEFAULT_PRODUCTION_GATE
    )
    flags = production["explicit_no_claim_flags"]
    static = production["gate_static_policy"]
    source = production["source_evidence_boundary_policy"]
    connector = production["connector_semantic_boundary_policy"]
    runtime = production["runtime_live_order_boundary_policy"]
    quantum = production["quantum_consumer_policy"]
    readiness = production["production_readiness"]
    future = production["future_consumer_contract"]

    assert static["selection_universe_consumer_gate_is_static_only"] is True
    assert static["agent_universe_consumer_access_is_deterministic"] is True
    assert static["trade_context_to_selection_universe_routing_created"] is False
    assert static["routed_universe_ids_created"] is False
    assert static["route_result_created"] is False
    assert static["selected_stack_created"] is False
    assert static["stack_selection_created"] is False
    assert static["scoring_created"] is False
    assert static["ranking_created"] is False
    assert static["optimizer_arbitration_created"] is False
    assert static["candidate_stack_generation_created"] is False
    assert static["replay_paper_execution_created"] is False
    assert static["runtime_live_order_authority_created"] is False
    assert source["source_retrieval_created"] is False
    assert source["source_acceptance_created"] is False
    assert source["accepted_source_packets_created"] is False
    assert connector["connector_semantics_created"] is False
    assert connector["connector_semantic_binding_created"] is False
    assert runtime["runtime_artifacts_created"] is False
    assert runtime["runtime_resolver_execution_created"] is False
    assert runtime["live_readiness_created"] is False
    assert runtime["runtime_live_use_created"] is False
    assert runtime["private_state_fetch_created"] is False
    assert runtime["order_intent_authority_created"] is False
    assert runtime["order_authority_created"] is False
    assert runtime["cash_receipts_created"] is False
    assert runtime["order_receipts_created"] is False
    assert runtime["fill_receipts_created"] is False
    assert runtime["profit_evidence_created"] is False
    assert quantum["quantum_backend_execution_created"] is False
    assert quantum["quantum_advantage_claim_created"] is False
    assert quantum["quantum_selection_created"] is False
    assert quantum["quantum_arbitration_created"] is False
    assert future["this_pr_performs_routing"] is False
    assert future["this_pr_performs_scoring"] is False
    assert future["this_pr_performs_ranking"] is False
    assert future["this_pr_performs_selection"] is False
    assert future["this_pr_performs_arbitration"] is False
    assert future["this_pr_generates_candidate_stacks"] is False
    assert future["this_pr_executes_replay_or_paper"] is False
    assert future["this_pr_executes_runtime_or_live"] is False
    assert readiness["parameter_selection_universe_consumer_gate_ready"] is True
    assert readiness["production_selection_universe_consumer_gate_evaluated"] is False
    assert readiness["production_selection_universe_consumer_gate_ready"] is False
    assert readiness["production_consumer_access_evaluated"] is False
    assert readiness["production_routing_evaluated"] is False
    assert readiness["production_routing_ready"] is False
    assert readiness["production_selection_ready"] is False
    assert readiness["final_ready"] is False
    assert all(
        flags[field] is False
        for field in selection_universe_consumer_gate.EXPLICIT_NO_CLAIM_FALSE_FIELDS
    )
    assert not (Path(".") / selection_universe_consumer_gate.CANONICAL_BUNDLE_JSONL).exists()
    assert not (Path(".") / selection_universe_consumer_gate.CANONICAL_BUNDLE_SHA256).exists()
    assert (Path(".") / selection_universe_consumer_gate.PR76_SHORT_TEST).exists()
    assert not (Path(".") / selection_universe_consumer_gate.PR76_OLD_LONG_TEST).exists()


def test_runner_pr81_routing_gate_has_no_runtime_source_connector_or_live_args(
    monkeypatch,
):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands]
    pr81_command = commands[
        command_names.index("validate_trade_context_selection_universe_routing_gate.py")
    ]

    assert pr81_command == [
        python_executable,
        str(Path("tools") / "validate_trade_context_selection_universe_routing_gate.py"),
    ]
    pr81_text = " ".join(pr81_command).lower()
    assert "source-retrieval" not in pr81_text
    assert "source-acceptance" not in pr81_text
    assert "connector-binding" not in pr81_text
    assert "runtime-live" not in pr81_text
    assert "live-use" not in pr81_text
    assert "order-authority" not in pr81_text
    assert "profit-evidence" not in pr81_text
    assert "replay-execution" not in pr81_text
    assert "paper-execution" not in pr81_text
    assert "quantum-backend" not in pr81_text
    assert "quantum-advantage" not in pr81_text
    assert "atomicrows.bundle.jsonl" not in pr81_text
    assert "atomicrows.bundle.sha256" not in pr81_text


def test_runner_pr82_quantum_applicability_gate_has_no_runtime_source_connector_or_live_args(
    monkeypatch,
):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands]
    pr82_command = commands[
        command_names.index("validate_quantum_applicability_classification_registry.py")
    ]

    assert pr82_command == [
        python_executable,
        str(
            Path("tools")
            / "validate_quantum_applicability_classification_registry.py"
        ),
    ]
    pr82_text = " ".join(pr82_command).lower()
    assert "source-retrieval" not in pr82_text
    assert "source-acceptance" not in pr82_text
    assert "connector-binding" not in pr82_text
    assert "runtime-live" not in pr82_text
    assert "live-use" not in pr82_text
    assert "order-authority" not in pr82_text
    assert "profit-evidence" not in pr82_text
    assert "replay-execution" not in pr82_text
    assert "paper-execution" not in pr82_text
    assert "quantum-backend" not in pr82_text
    assert "quantum-simulator" not in pr82_text
    assert "atomicrows.bundle.jsonl" not in pr82_text
    assert "atomicrows.bundle.sha256" not in pr82_text


def test_runner_pr83_owner_quantum_priority_gate_has_no_runtime_source_connector_or_live_args(
    monkeypatch,
):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands]
    pr83_command = commands[
        command_names.index("validate_owner_quantum_priority_policy_registry.py")
    ]

    assert pr83_command == [
        python_executable,
        str(Path("tools") / "validate_owner_quantum_priority_policy_registry.py"),
    ]
    pr83_text = " ".join(pr83_command).lower()
    assert "source-retrieval" not in pr83_text
    assert "source-acceptance" not in pr83_text
    assert "connector-binding" not in pr83_text
    assert "runtime-live" not in pr83_text
    assert "live-use" not in pr83_text
    assert "order-authority" not in pr83_text
    assert "profit-evidence" not in pr83_text
    assert "replay-execution" not in pr83_text
    assert "paper-execution" not in pr83_text
    assert "quantum-backend" not in pr83_text
    assert "quantum-simulator" not in pr83_text
    assert "optimizer-execution" not in pr83_text
    assert "optimizer-arbitration" not in pr83_text
    assert "scoring-execution" not in pr83_text
    assert "ranking" not in pr83_text
    assert "selection" not in pr83_text
    assert "atomicrows.bundle.jsonl" not in pr83_text
    assert "atomicrows.bundle.sha256" not in pr83_text


def test_runner_pr84_parameter_algorithm_scoring_policy_gate_has_no_runtime_source_connector_or_live_args(
    monkeypatch,
):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands]
    pr84_command = commands[
        command_names.index("validate_parameter_algorithm_scoring_policy_registry.py")
    ]

    assert pr84_command == [
        python_executable,
        str(Path("tools") / "validate_parameter_algorithm_scoring_policy_registry.py"),
    ]
    pr84_text = " ".join(pr84_command).lower()
    assert "source-retrieval" not in pr84_text
    assert "source-acceptance" not in pr84_text
    assert "connector-binding" not in pr84_text
    assert "runtime-live" not in pr84_text
    assert "live-use" not in pr84_text
    assert "order-authority" not in pr84_text
    assert "profit-evidence" not in pr84_text
    assert "replay-execution" not in pr84_text
    assert "paper-execution" not in pr84_text
    assert "quantum-backend" not in pr84_text
    assert "quantum-simulator" not in pr84_text
    assert "optimizer-execution" not in pr84_text
    assert "optimizer-arbitration" not in pr84_text
    assert "scoring-execution" not in pr84_text
    assert "ranking" not in pr84_text
    assert "selection" not in pr84_text
    assert "atomicrows.bundle.jsonl" not in pr84_text
    assert "atomicrows.bundle.sha256" not in pr84_text


def test_runner_pr85_parameter_stack_scoring_and_ranking_gate_has_no_runtime_source_connector_or_live_args(
    monkeypatch,
):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands]
    pr85_command = commands[
        command_names.index("validate_parameter_stack_scoring_and_ranking_gate.py")
    ]

    assert pr85_command == [
        python_executable,
        str(Path("tools") / "validate_parameter_stack_scoring_and_ranking_gate.py"),
    ]
    pr85_text = " ".join(pr85_command).lower()
    assert "source-retrieval" not in pr85_text
    assert "source-acceptance" not in pr85_text
    assert "connector-binding" not in pr85_text
    assert "runtime-live" not in pr85_text
    assert "live-use" not in pr85_text
    assert "order-authority" not in pr85_text
    assert "profit-evidence" not in pr85_text
    assert "replay-execution" not in pr85_text
    assert "paper-execution" not in pr85_text
    assert "quantum-backend" not in pr85_text
    assert "quantum-simulator" not in pr85_text
    assert "optimizer-execution" not in pr85_text
    assert "optimizer-arbitration" not in pr85_text
    assert "atomicrows.bundle.jsonl" not in pr85_text
    assert "atomicrows.bundle.sha256" not in pr85_text


def test_runner_pr86_optimizer_arbitration_gate_has_no_runtime_source_connector_or_live_args(
    monkeypatch,
):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands]
    pr86_command = commands[
        command_names.index("validate_quantum_classical_optimizer_arbitration_gate.py")
    ]

    assert pr86_command == [
        python_executable,
        str(Path("tools") / "validate_quantum_classical_optimizer_arbitration_gate.py"),
    ]
    pr86_text = " ".join(pr86_command).lower()
    assert "source-retrieval" not in pr86_text
    assert "source-acceptance" not in pr86_text
    assert "connector-binding" not in pr86_text
    assert "runtime-live" not in pr86_text
    assert "live-use" not in pr86_text
    assert "order-authority" not in pr86_text
    assert "profit-evidence" not in pr86_text
    assert "replay-execution" not in pr86_text
    assert "paper-execution" not in pr86_text
    assert "quantum-backend" not in pr86_text
    assert "quantum-simulator" not in pr86_text
    assert "optimizer-execution" not in pr86_text
    assert "atomicrows.bundle.jsonl" not in pr86_text
    assert "atomicrows.bundle.sha256" not in pr86_text


def test_runner_pr87_candidate_generation_gate_has_no_runtime_source_connector_or_live_args(
    monkeypatch,
):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands]
    pr87_command = commands[
        command_names.index("validate_candidate_parameter_stack_generation_gate.py")
    ]

    assert pr87_command == [
        python_executable,
        str(Path("tools") / "validate_candidate_parameter_stack_generation_gate.py"),
    ]
    pr87_text = " ".join(pr87_command).lower()
    assert "source-retrieval" not in pr87_text
    assert "source-acceptance" not in pr87_text
    assert "connector-binding" not in pr87_text
    assert "runtime-live" not in pr87_text
    assert "live-use" not in pr87_text
    assert "order-authority" not in pr87_text
    assert "profit-evidence" not in pr87_text
    assert "replay-execution" not in pr87_text
    assert "paper-execution" not in pr87_text
    assert "quantum-backend" not in pr87_text
    assert "quantum-simulator" not in pr87_text
    assert "optimizer-execution" not in pr87_text
    assert "atomicrows.bundle.jsonl" not in pr87_text
    assert "atomicrows.bundle.sha256" not in pr87_text


def test_runner_pr88_trade_context_stack_selection_gate_has_no_runtime_source_connector_or_live_args(
    monkeypatch,
):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands]
    pr88_command = commands[
        command_names.index("validate_trade_context_parameter_stack_selection_gate.py")
    ]

    assert pr88_command == [
        python_executable,
        str(Path("tools") / "validate_trade_context_parameter_stack_selection_gate.py"),
    ]
    pr88_text = " ".join(pr88_command).lower()
    assert "source-retrieval" not in pr88_text
    assert "source-acceptance" not in pr88_text
    assert "connector-binding" not in pr88_text
    assert "runtime-live" not in pr88_text
    assert "live-use" not in pr88_text
    assert "order-authority" not in pr88_text
    assert "profit-evidence" not in pr88_text
    assert "replay-execution" not in pr88_text
    assert "paper-execution" not in pr88_text
    assert "selected-stack-handoff" not in pr88_text
    assert "quantum-backend" not in pr88_text
    assert "quantum-simulator" not in pr88_text
    assert "optimizer-execution" not in pr88_text
    assert "atomicrows.bundle.jsonl" not in pr88_text
    assert "atomicrows.bundle.sha256" not in pr88_text


def test_runner_pr89_selected_stack_handoff_packet_has_no_runtime_source_connector_or_live_args(
    monkeypatch,
):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands]
    pr89_command = commands[
        command_names.index("validate_selected_parameter_stack_handoff_packet.py")
    ]

    assert pr89_command == [
        python_executable,
        str(Path("tools") / "validate_selected_parameter_stack_handoff_packet.py"),
    ]
    pr89_text = " ".join(pr89_command).lower()
    assert "source-retrieval" not in pr89_text
    assert "source-acceptance" not in pr89_text
    assert "connector-binding" not in pr89_text
    assert "runtime-live" not in pr89_text
    assert "live-use" not in pr89_text
    assert "order-authority" not in pr89_text
    assert "profit-evidence" not in pr89_text
    assert "replay-execution" not in pr89_text
    assert "paper-execution" not in pr89_text
    assert "quantum-backend" not in pr89_text
    assert "quantum-simulator" not in pr89_text
    assert "optimizer-execution" not in pr89_text
    assert "atomicrows.bundle.jsonl" not in pr89_text
    assert "atomicrows.bundle.sha256" not in pr89_text


def test_runner_pr90_replay_paper_competition_gate_has_no_runtime_source_connector_or_live_args(
    monkeypatch,
):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands]
    pr90_command = commands[
        command_names.index("validate_replay_paper_candidate_stack_competition_gate.py")
    ]

    assert pr90_command == [
        python_executable,
        str(Path("tools") / "validate_replay_paper_candidate_stack_competition_gate.py"),
    ]
    pr90_text = " ".join(pr90_command).lower()
    assert "source-retrieval" not in pr90_text
    assert "source-acceptance" not in pr90_text
    assert "connector-binding" not in pr90_text
    assert "runtime-live" not in pr90_text
    assert "live-use" not in pr90_text
    assert "order-authority" not in pr90_text
    assert "profit-evidence" not in pr90_text
    assert "replay-execution" not in pr90_text
    assert "paper-execution" not in pr90_text
    assert "quantum-backend" not in pr90_text
    assert "quantum-simulator" not in pr90_text
    assert "optimizer-execution" not in pr90_text
    assert "atomicrows.bundle.jsonl" not in pr90_text
    assert "atomicrows.bundle.sha256" not in pr90_text


def test_pr81_static_contract_preserves_route_only_boundaries():
    production = trade_context_routing_gate.load_yaml(
        trade_context_routing_gate.DEFAULT_PRODUCTION_GATE
    )
    report = json.loads(
        trade_context_routing_gate.DEFAULT_REPORT.read_text(encoding="utf-8")
    )

    assert production["routing_static_policy"]["routing_gate_is_static_only"] is True
    assert production["routing_static_policy"][
        "trade_context_to_selection_universe_static_routing_gate_created"
    ] is True
    assert report["route_scope"] == (
        "STATIC_TRADE_CONTEXT_TO_SELECTION_UNIVERSE_ELIGIBILITY_ONLY"
    )
    assert report["route_is_selection"] is False
    assert report["stack_selection_created"] is False
    assert report["selected_stack_id"] is None
    assert report["score_breakdown_created"] is False
    assert report["optimizer_arbitration_created"] is False
    assert report["runtime_authority_created"] is False
    assert report["live_authority_created"] is False
    assert report["order_authority_created"] is False
    assert report["source_retrieval_created"] is False
    assert report["source_acceptance_created"] is False
    assert report["connector_semantic_binding_created"] is False
    assert report["quantum_backend_execution_created"] is False
    assert report["quantum_advantage_claim_created"] is False
    assert report["profit_evidence_created"] is False
    assert report["random_selection_used"] is False
    assert all(
        production["explicit_no_claim_flags"][field] is False
        for field in trade_context_routing_gate.EXPLICIT_NO_CLAIM_FALSE_FIELDS
    )
    assert not (Path(".") / trade_context_routing_gate.CANONICAL_BUNDLE_JSONL).exists()
    assert not (Path(".") / trade_context_routing_gate.CANONICAL_BUNDLE_SHA256).exists()


def test_pr82_static_contract_preserves_metadata_only_boundaries():
    production = quantum_applicability_gate.load_yaml(
        quantum_applicability_gate.DEFAULT_PRODUCTION_REGISTRY
    )
    report = json.loads(
        quantum_applicability_gate.DEFAULT_REPORT.read_text(encoding="utf-8")
    )

    assert production["semantic_task_id"] == "ROADMAP-QUANTUM-APPLICABILITY-REGISTRY"
    assert production["registry_scope"] == "STATIC_QUANTUM_APPLICABILITY_METADATA_ONLY"
    assert production["static_only_flag"] is True
    assert production["metadata_only_flag"] is True
    assert report["classification_is_metadata_only"] is True
    assert report["backend_execution_created"] is False
    assert report["quantum_backend_execution_created"] is False
    assert report["quantum_simulator_execution_created"] is False
    assert report["optimizer_arbitration_created"] is False
    assert report["scoring_execution_created"] is False
    assert report["ranking_created"] is False
    assert report["selection_created"] is False
    assert report["runtime_authority_created"] is False
    assert report["live_authority_created"] is False
    assert report["order_authority_created"] is False
    assert report["source_retrieval_created"] is False
    assert report["source_acceptance_created"] is False
    assert report["connector_semantic_binding_created"] is False
    assert report["quantum_advantage_claim_created"] is False
    assert report["profit_evidence_created"] is False
    assert report["random_classification_used"] is False
    assert report["future_owner_quantum_priority_policy_required"] is True
    assert report["future_scoring_policy_required"] is True
    assert report["future_optimizer_arbitration_required"] is True
    assert report["missing_canonical_family_ids"] == []
    assert not (Path(".") / quantum_applicability_gate.CANONICAL_BUNDLE_JSONL).exists()
    assert not (Path(".") / quantum_applicability_gate.CANONICAL_BUNDLE_SHA256).exists()
    assert (Path(".") / quantum_applicability_gate.PR76_SHORT_TEST).exists()
    assert not (Path(".") / quantum_applicability_gate.PR76_OLD_LONG_TEST).exists()


def test_pr83_static_contract_preserves_owner_quantum_priority_boundaries():
    assert owner_quantum_priority_gate.main([]) == 0
    production = owner_quantum_priority_gate.load_yaml(
        owner_quantum_priority_gate.DEFAULT_PRODUCTION_REGISTRY
    )
    report = json.loads(
        owner_quantum_priority_gate.DEFAULT_REPORT.read_text(encoding="utf-8")
    )

    assert production["semantic_task_id"] == "ROADMAP-OWNER-QUANTUM-PRIORITY-POLICY"
    assert production["policy_scope"] == "STATIC_OWNER_QUANTUM_PRIORITY_POLICY_ONLY"
    assert production["static_only_flag"] is True
    assert production["metadata_only_flag"] is True
    assert report["policy_is_metadata_only"] is True
    assert report["owner_quantum_priority_enabled"] is True
    assert report["default_quantum_priority_mode"] == "QUANTUM_PREFERRED"
    assert report["supported_quantum_priority_modes"] == list(
        owner_quantum_priority_gate.MODE_ORDER
    )
    assert report["classical_only_families_valid_as_comparators"] is True
    assert report["hybrid_compare_requires_classical_comparator"] is True
    assert report["future_scoring_policy_required"] is True
    assert report["future_stack_ranking_gate_required"] is True
    assert report["future_optimizer_arbitration_required"] is True
    assert report["future_candidate_stack_generation_required"] is True
    assert report["future_trade_context_stack_selection_required"] is True
    assert report["future_consumer_contract_execution_created"] is False
    assert report["pr82_quantum_applicability_registry_consumed"] is True
    assert report["classical_only_label_validated_from_pr82"] is True
    for field in owner_quantum_priority_gate.ROOT_FALSE_FIELDS:
        assert report[field] is False
    assert not (Path(".") / owner_quantum_priority_gate.CANONICAL_BUNDLE_JSONL).exists()
    assert not (Path(".") / owner_quantum_priority_gate.CANONICAL_BUNDLE_SHA256).exists()
    assert (Path(".") / owner_quantum_priority_gate.PR76_SHORT_TEST).exists()
    assert not (Path(".") / owner_quantum_priority_gate.PR76_OLD_LONG_TEST).exists()


def test_pr84_static_contract_preserves_formula_registry_only_boundaries():
    assert scoring_policy_gate.main([]) == 0
    production = scoring_policy_gate.load_yaml(
        scoring_policy_gate.DEFAULT_PRODUCTION_REGISTRY
    )
    report = json.loads(
        scoring_policy_gate.DEFAULT_REPORT.read_text(encoding="utf-8")
    )

    assert production["semantic_task_id"] == (
        "ROADMAP-PARAMETER-AND-ALGORITHM-SCORING-POLICY-REGISTRY"
    )
    assert production["policy_scope"] == (
        "STATIC_PARAMETER_AND_ALGORITHM_SCORING_FORMULA_REGISTRY_ONLY"
    )
    assert production["static_only_flag"] is True
    assert production["metadata_only_flag"] is True
    assert production["formula_registry_only_flag"] is True
    assert report["formula_definition_allowed"] is True
    assert report["formula_execution_created"] is False
    assert report["scoring_result_created"] is False
    assert report["ranking_created"] is False
    assert report["selection_created"] is False
    assert report["candidate_stack_generation_created"] is False
    assert report["pr82_quantum_applicability_metadata_consumed"] is True
    assert report["pr83_owner_quantum_priority_policy_consumed"] is True
    assert report["formula_ids"] == list(scoring_policy_gate.FORMULA_ORDER)
    assert report["formula_outputs"] == list(scoring_policy_gate.FORMULA_OUTPUT_ORDER)
    assert report["scoring_component_names"] == list(scoring_policy_gate.COMPONENT_ORDER)
    assert report["future_consumer_ids"] == list(scoring_policy_gate.FUTURE_CONSUMER_ORDER)
    for field in scoring_policy_gate.NO_AUTHORITY_FALSE_FIELDS:
        assert report[field] is False
    assert report["expected_net_profit_score_is_profit_evidence"] is False
    assert report["latency_fit_score_is_latency_superiority_evidence"] is False
    assert report["optimizer_score_is_optimizer_execution"] is False
    assert report["runtime_readiness_score_is_runtime_receipt"] is False
    assert report["replay_paper_score_is_replay_paper_result"] is False
    assert report["source_currentness_penalty_is_source_authority"] is False
    assert report["execution_cost_penalty_is_venue_fact"] is False
    assert report["owner_override_score_can_fabricate_external_facts"] is False
    assert not (Path(".") / scoring_policy_gate.CANONICAL_BUNDLE_JSONL).exists()
    assert not (Path(".") / scoring_policy_gate.CANONICAL_BUNDLE_SHA256).exists()
    assert (Path(".") / scoring_policy_gate.PR76_SHORT_TEST).exists()
    assert not (Path(".") / scoring_policy_gate.PR76_OLD_LONG_TEST).exists()


def test_pr85_static_contract_preserves_parameter_stack_ranking_boundaries():
    assert stack_scoring_gate.main([]) == 0
    production = stack_scoring_gate.load_yaml(
        stack_scoring_gate.DEFAULT_PRODUCTION_REGISTRY
    )
    report = json.loads(
        stack_scoring_gate.DEFAULT_REPORT.read_text(encoding="utf-8")
    )

    assert production["semantic_task_id"] == (
        "ROADMAP-PARAMETER-STACK-SCORING-AND-RANKING-GATE"
    )
    assert production["gate_scope"] == (
        "STATIC_PARAMETER_STACK_SCORING_AND_RANKING_CONTRACT_ONLY"
    )
    assert production["static_only_flag"] is True
    assert production["metadata_only_flag"] is True
    assert production["synthetic_fixture_only_flag"] is True
    assert production["scoring_ranking_contract_only_flag"] is True
    assert report["pr82_quantum_applicability_labels"] == list(
        stack_scoring_gate.pr84_gate.PR82_LABEL_ORDER
    )
    assert report["pr83_supported_quantum_priority_modes"] == list(
        stack_scoring_gate.pr84_gate.PR83_MODE_ORDER
    )
    assert report["pr84_formula_ids"] == list(stack_scoring_gate.FORMULA_ORDER)
    assert report["ranked_candidate_descriptor_ids"] == [
        "OWNER_OVERRIDE_QUANTUM_PRIORITY_STACK_FIXTURE",
        "QUANTUM_APPLICABLE_PREFERRED_STACK_FIXTURE",
        "HYBRID_COMPARE_THEN_QUANTUM_TIEBREAK_STACK_FIXTURE",
        "CLASSICAL_BASELINE_COMPARATOR_STACK_FIXTURE",
        "TIE_BREAK_STABILITY_FIXTURE_A",
        "TIE_BREAK_STABILITY_FIXTURE_B",
    ]
    assert report["blocked_candidate_descriptor_ids"] == [
        "BLOCKED_INVALID_STACK_FIXTURE"
    ]
    assert report["highest_ranked_candidate_is_final_selected_stack"] is False
    assert report["future_pr86_optimizer_arbitration_implemented"] is False
    assert report["future_pr87_candidate_generation_implemented"] is False
    assert report["future_pr88_trade_context_selection_implemented"] is False
    for field in stack_scoring_gate.REPORT_FALSE_FIELDS:
        assert report[field] is False
    assert not (Path(".") / stack_scoring_gate.CANONICAL_BUNDLE_JSONL).exists()
    assert not (Path(".") / stack_scoring_gate.CANONICAL_BUNDLE_SHA256).exists()
    assert (Path(".") / stack_scoring_gate.PR76_SHORT_TEST).exists()
    assert not (Path(".") / stack_scoring_gate.PR76_OLD_LONG_TEST).exists()


def test_pr86_static_contract_preserves_optimizer_arbitration_boundaries():
    assert optimizer_arbitration_gate.main([]) == 0
    production = optimizer_arbitration_gate.load_yaml(
        optimizer_arbitration_gate.DEFAULT_PRODUCTION_REGISTRY
    )
    report = json.loads(
        optimizer_arbitration_gate.DEFAULT_REPORT.read_text(encoding="utf-8")
    )

    assert production["semantic_task_id"] == (
        "ROADMAP-QUANTUM-CLASSICAL-OPTIMIZER-ARBITRATION-GATE"
    )
    assert production["gate_scope"] == (
        "STATIC_QUANTUM_CLASSICAL_OPTIMIZER_ARBITRATION_CONTRACT_ONLY"
    )
    assert production["static_only_flag"] is True
    assert production["metadata_only_flag"] is True
    assert production["synthetic_fixture_only_flag"] is True
    assert production["optimizer_arbitration_contract_only_flag"] is True
    assert report["pr82_quantum_applicability_labels"] == list(
        optimizer_arbitration_gate.pr85_gate.pr84_gate.PR82_LABEL_ORDER
    )
    assert report["pr83_supported_quantum_priority_modes"] == list(
        optimizer_arbitration_gate.pr85_gate.pr84_gate.PR83_MODE_ORDER
    )
    assert report["pr84_formula_ids"] == list(
        optimizer_arbitration_gate.pr85_gate.FORMULA_ORDER
    )
    assert report["pr85_ranked_candidate_descriptor_ids"] == [
        "OWNER_OVERRIDE_QUANTUM_PRIORITY_STACK_FIXTURE",
        "QUANTUM_APPLICABLE_PREFERRED_STACK_FIXTURE",
        "HYBRID_COMPARE_THEN_QUANTUM_TIEBREAK_STACK_FIXTURE",
        "CLASSICAL_BASELINE_COMPARATOR_STACK_FIXTURE",
        "TIE_BREAK_STABILITY_FIXTURE_A",
        "TIE_BREAK_STABILITY_FIXTURE_B",
    ]
    assert report["arbitration_ordered_fixture_ids"] == list(
        optimizer_arbitration_gate.EXPECTED_ORDERED_VALID_FIXTURE_IDS
    )
    assert report["blocked_arbitration_fixture_ids"] == [
        "BLOCKED_BACKEND_EXECUTION_ATTEMPT_FIXTURE",
        "BLOCKED_MISSING_CLASSICAL_COMPARATOR_FIXTURE",
    ]
    assert report["static_arbitration_decision_is_final_selected_stack"] is False
    assert report["static_arbitration_decision_is_live_order_authority"] is False
    assert report["future_pr87_candidate_generation_implemented"] is False
    assert report["future_pr88_trade_context_selection_implemented"] is False
    assert report["future_pr90_replay_paper_competition_implemented"] is False
    for field in optimizer_arbitration_gate.REPORT_FALSE_FIELDS:
        assert report[field] is False
    assert not (Path(".") / optimizer_arbitration_gate.CANONICAL_BUNDLE_JSONL).exists()
    assert not (Path(".") / optimizer_arbitration_gate.CANONICAL_BUNDLE_SHA256).exists()
    assert (Path(".") / optimizer_arbitration_gate.PR76_SHORT_TEST).exists()
    assert not (Path(".") / optimizer_arbitration_gate.PR76_OLD_LONG_TEST).exists()


def test_pr87_static_contract_preserves_candidate_generation_boundaries(monkeypatch):
    monkeypatch.setenv("GITHUB_ACTIONS", "true")

    assert candidate_generation_gate.main([]) == 0
    production = candidate_generation_gate.load_yaml(
        candidate_generation_gate.DEFAULT_PRODUCTION_REGISTRY
    )
    report = json.loads(
        candidate_generation_gate.DEFAULT_REPORT.read_text(encoding="utf-8")
    )

    assert production["semantic_task_id"] == (
        "ROADMAP-CANDIDATE-PARAMETER-STACK-GENERATION-GATE"
    )
    assert production["gate_scope"] == (
        "STATIC_CANDIDATE_PARAMETER_STACK_GENERATION_GATE_ONLY"
    )
    assert production["static_only_flag"] is True
    assert production["metadata_only_flag"] is True
    assert production["synthetic_fixture_only_flag"] is True
    assert production["candidate_generation_contract_only_flag"] is True
    assert report["candidate_generation_packet_status"] == (
        "STATIC_CANDIDATE_GENERATION_PACKET_READY"
    )
    assert report["active_candidate_stack_ids"] == list(
        candidate_generation_gate.EXPECTED_ACTIVE_CANDIDATE_IDS
    )
    assert report["blocked_candidate_stack_ids"] == list(
        candidate_generation_gate.EXPECTED_BLOCKED_CANDIDATE_IDS
    )
    assert report["static_candidate_generation_packet_is_final_selection"] is False
    assert report["static_candidate_generation_packet_is_live_order_authority"] is False
    assert report["future_pr88_trade_context_selection_implemented"] is False
    assert report["future_pr90_replay_paper_competition_implemented"] is False
    for field in candidate_generation_gate.REPORT_FALSE_FIELDS:
        assert report[field] is False
    assert not (Path(".") / candidate_generation_gate.CANONICAL_BUNDLE_JSONL).exists()
    assert not (Path(".") / candidate_generation_gate.CANONICAL_BUNDLE_SHA256).exists()


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
    parameter_agent_binding_index = command_names.index(
        "validate_atomicrows_parameter_agent_binding_registry.py"
    )
    parameter_agent_binding_consumer_gate_index = command_names.index(
        "validate_atomicrows_parameter_agent_binding_consumer_gate.py"
    )
    parameter_agent_binding_cumulative_gate_index = command_names.index(
        "validate_atomicrows_parameter_agent_binding_cumulative_readiness_gate.py"
    )
    parameter_agent_binding_command_matrix_index = command_names.index(
        "validate_atomicrows_parameter_agent_binding_command_matrix.py"
    )
    research_provenance_index = command_names.index(
        "validate_atomicrows_research_provenance_evidence_tier_classification.py"
    )
    owner_intake_index = command_names.index(
        "validate_atomicrows_owner_submitted_research_source_intake_registry.py"
    )
    candidate_family_index = command_names.index(
        "validate_atomicrows_research_source_to_candidate_family_gate.py"
    )
    parameter_stack_role_index = command_names.index(
        "validate_atomicrows_parameter_stack_role_taxonomy.py"
    )
    parameter_stack_completeness_index = command_names.index(
        "validate_atomicrows_parameter_stack_completeness_gate.py"
    )
    parameter_stack_compatibility_index = command_names.index(
        "validate_atomicrows_parameter_stack_compatibility_gate.py"
    )
    edge_packet_index = command_names.index(
        "validate_edge_parameter_stack_selection_packet.py"
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
        < parameter_agent_binding_index
        < parameter_agent_binding_consumer_gate_index
        < parameter_agent_binding_cumulative_gate_index
        < parameter_agent_binding_command_matrix_index
        < research_provenance_index
        < owner_intake_index
        < candidate_family_index
        < parameter_stack_role_index
        < parameter_stack_completeness_index
        < parameter_stack_compatibility_index
        < edge_packet_index
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
    assert commands[parameter_agent_binding_index] == [
        python_executable,
        str(Path("tools") / "validate_atomicrows_parameter_agent_binding_registry.py"),
        "--mode",
        "dev",
        "--out",
        str(
            Path("docs")
            / "master_plan"
            / "generated"
            / "AtomicRowsParameterAgentBindingReport.json"
        ),
    ]
    assert commands[parameter_agent_binding_consumer_gate_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_atomicrows_parameter_agent_binding_consumer_gate.py"
        ),
        "--mode",
        "dev",
        "--out",
        str(
            Path("docs")
            / "master_plan"
            / "generated"
            / "AtomicRowsParameterAgentBindingConsumerGate.report.json"
        ),
    ]
    assert commands[parameter_agent_binding_cumulative_gate_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_atomicrows_parameter_agent_binding_cumulative_readiness_gate.py"
        ),
        "--mode",
        "dev",
        "--out",
        str(
            Path("docs")
            / "master_plan"
            / "generated"
            / "AtomicRowsParameterAgentBindingCumulativeReadinessGate.report.json"
        ),
    ]
    assert commands[parameter_agent_binding_command_matrix_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_atomicrows_parameter_agent_binding_command_matrix.py"
        ),
        "--mode",
        "dev",
        "--out",
        str(
            Path("docs")
            / "master_plan"
            / "generated"
            / "AtomicRowsParameterAgentBindingCommandMatrix.json"
        ),
    ]
    assert commands[research_provenance_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_atomicrows_research_provenance_evidence_tier_classification.py"
        ),
    ]
    assert commands[owner_intake_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_atomicrows_owner_submitted_research_source_intake_registry.py"
        ),
    ]
    assert commands[candidate_family_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_atomicrows_research_source_to_candidate_family_gate.py"
        ),
    ]
    assert commands[parameter_stack_role_index] == [
        python_executable,
        str(Path("tools") / "validate_atomicrows_parameter_stack_role_taxonomy.py"),
    ]
    assert commands[parameter_stack_completeness_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_atomicrows_parameter_stack_completeness_gate.py"
        ),
    ]
    assert commands[parameter_stack_compatibility_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_atomicrows_parameter_stack_compatibility_gate.py"
        ),
    ]
    assert commands[edge_packet_index] == [
        python_executable,
        str(Path("tools") / "validate_edge_parameter_stack_selection_packet.py"),
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


def test_runner_does_not_emit_success_marker_if_owner_intake_validator_fails(
    monkeypatch,
    capsys,
):
    class Completed:
        def __init__(self, returncode: int) -> None:
            self.returncode = returncode

    commands = [
        [
            "python",
            "validate_atomicrows_research_provenance_evidence_tier_classification.py",
        ],
        [
            "python",
            "validate_atomicrows_owner_submitted_research_source_intake_registry.py",
        ],
        ["python", "later_gate.py"],
    ]
    returncodes = [0, 7, 0]
    seen: list[list[str]] = []

    def fake_run(command: list[str]) -> Completed:
        seen.append(command)
        return Completed(returncodes[len(seen) - 1])

    monkeypatch.setattr(runner.subprocess, "run", fake_run)

    exit_code = runner.run_commands(commands)

    assert exit_code == 7
    assert seen == commands[:2]
    assert runner.SUCCESS_MARKER not in capsys.readouterr().out


def test_runner_does_not_emit_success_marker_if_candidate_family_gate_fails(
    monkeypatch,
    capsys,
):
    class Completed:
        def __init__(self, returncode: int) -> None:
            self.returncode = returncode

    commands = [
        [
            "python",
            "validate_atomicrows_research_provenance_evidence_tier_classification.py",
        ],
        [
            "python",
            "validate_atomicrows_owner_submitted_research_source_intake_registry.py",
        ],
        [
            "python",
            "validate_atomicrows_research_source_to_candidate_family_gate.py",
        ],
        ["python", "later_gate.py"],
    ]
    returncodes = [0, 0, 11, 0]
    seen: list[list[str]] = []

    def fake_run(command: list[str]) -> Completed:
        seen.append(command)
        return Completed(returncodes[len(seen) - 1])

    monkeypatch.setattr(runner.subprocess, "run", fake_run)

    exit_code = runner.run_commands(commands)

    assert exit_code == 11
    assert seen == commands[:3]
    assert runner.SUCCESS_MARKER not in capsys.readouterr().out


def test_runner_does_not_emit_success_marker_if_parameter_stack_role_taxonomy_fails(
    monkeypatch,
    capsys,
):
    class Completed:
        def __init__(self, returncode: int) -> None:
            self.returncode = returncode

    commands = [
        [
            "python",
            "validate_atomicrows_research_provenance_evidence_tier_classification.py",
        ],
        [
            "python",
            "validate_atomicrows_owner_submitted_research_source_intake_registry.py",
        ],
        [
            "python",
            "validate_atomicrows_research_source_to_candidate_family_gate.py",
        ],
        ["python", "validate_atomicrows_parameter_stack_role_taxonomy.py"],
        ["python", "later_gate.py"],
    ]
    returncodes = [0, 0, 0, 13, 0]
    seen: list[list[str]] = []

    def fake_run(command: list[str]) -> Completed:
        seen.append(command)
        return Completed(returncodes[len(seen) - 1])

    monkeypatch.setattr(runner.subprocess, "run", fake_run)

    exit_code = runner.run_commands(commands)

    assert exit_code == 13
    assert seen == commands[:4]
    assert runner.SUCCESS_MARKER not in capsys.readouterr().out


def test_runner_does_not_emit_success_marker_if_parameter_stack_completeness_gate_fails(
    monkeypatch,
    capsys,
):
    class Completed:
        def __init__(self, returncode: int) -> None:
            self.returncode = returncode

    commands = [
        [
            "python",
            "validate_atomicrows_research_provenance_evidence_tier_classification.py",
        ],
        [
            "python",
            "validate_atomicrows_owner_submitted_research_source_intake_registry.py",
        ],
        [
            "python",
            "validate_atomicrows_research_source_to_candidate_family_gate.py",
        ],
        ["python", "validate_atomicrows_parameter_stack_role_taxonomy.py"],
        ["python", "validate_atomicrows_parameter_stack_completeness_gate.py"],
        ["python", "later_gate.py"],
    ]
    returncodes = [0, 0, 0, 0, 17, 0]
    seen: list[list[str]] = []

    def fake_run(command: list[str]) -> Completed:
        seen.append(command)
        return Completed(returncodes[len(seen) - 1])

    monkeypatch.setattr(runner.subprocess, "run", fake_run)

    exit_code = runner.run_commands(commands)

    assert exit_code == 17
    assert seen == commands[:5]
    assert runner.SUCCESS_MARKER not in capsys.readouterr().out


def test_runner_does_not_emit_success_marker_if_parameter_stack_compatibility_gate_fails(
    monkeypatch,
    capsys,
):
    class Completed:
        def __init__(self, returncode: int) -> None:
            self.returncode = returncode

    commands = [
        [
            "python",
            "validate_atomicrows_research_provenance_evidence_tier_classification.py",
        ],
        [
            "python",
            "validate_atomicrows_owner_submitted_research_source_intake_registry.py",
        ],
        [
            "python",
            "validate_atomicrows_research_source_to_candidate_family_gate.py",
        ],
        ["python", "validate_atomicrows_parameter_stack_role_taxonomy.py"],
        ["python", "validate_atomicrows_parameter_stack_completeness_gate.py"],
        ["python", "validate_atomicrows_parameter_stack_compatibility_gate.py"],
        ["python", "later_gate.py"],
    ]
    returncodes = [0, 0, 0, 0, 0, 19, 0]
    seen: list[list[str]] = []

    def fake_run(command: list[str]) -> Completed:
        seen.append(command)
        return Completed(returncodes[len(seen) - 1])

    monkeypatch.setattr(runner.subprocess, "run", fake_run)

    exit_code = runner.run_commands(commands)

    assert exit_code == 19
    assert seen == commands[:6]
    assert runner.SUCCESS_MARKER not in capsys.readouterr().out


def test_runner_does_not_emit_success_marker_if_edge_packet_validator_fails(
    monkeypatch,
    capsys,
):
    class Completed:
        def __init__(self, returncode: int) -> None:
            self.returncode = returncode

    commands = [
        [
            "python",
            "validate_atomicrows_research_provenance_evidence_tier_classification.py",
        ],
        [
            "python",
            "validate_atomicrows_owner_submitted_research_source_intake_registry.py",
        ],
        [
            "python",
            "validate_atomicrows_research_source_to_candidate_family_gate.py",
        ],
        ["python", "validate_atomicrows_parameter_stack_role_taxonomy.py"],
        ["python", "validate_atomicrows_parameter_stack_completeness_gate.py"],
        ["python", "validate_atomicrows_parameter_stack_compatibility_gate.py"],
        ["python", "validate_edge_parameter_stack_selection_packet.py"],
        ["python", "later_gate.py"],
    ]
    returncodes = [0, 0, 0, 0, 0, 0, 23, 0]
    seen: list[list[str]] = []

    def fake_run(command: list[str]) -> Completed:
        seen.append(command)
        return Completed(returncodes[len(seen) - 1])

    monkeypatch.setattr(runner.subprocess, "run", fake_run)

    exit_code = runner.run_commands(commands)

    assert exit_code == 23
    assert seen == commands[:7]
    assert runner.SUCCESS_MARKER not in capsys.readouterr().out


def test_runner_does_not_emit_success_marker_if_qtt_trade_context_packet_validator_fails(
    monkeypatch,
    capsys,
):
    class Completed:
        def __init__(self, returncode: int) -> None:
            self.returncode = returncode

    commands = [
        [
            "python",
            "validate_atomicrows_research_provenance_evidence_tier_classification.py",
        ],
        [
            "python",
            "validate_atomicrows_owner_submitted_research_source_intake_registry.py",
        ],
        [
            "python",
            "validate_atomicrows_research_source_to_candidate_family_gate.py",
        ],
        ["python", "validate_atomicrows_parameter_stack_role_taxonomy.py"],
        ["python", "validate_atomicrows_parameter_stack_completeness_gate.py"],
        ["python", "validate_atomicrows_parameter_stack_compatibility_gate.py"],
        ["python", "validate_edge_parameter_stack_selection_packet.py"],
        ["python", "validate_qtt_trade_context_packet.py"],
        ["python", "later_gate.py"],
    ]
    returncodes = [0, 0, 0, 0, 0, 0, 0, 29, 0]
    seen: list[list[str]] = []

    def fake_run(command: list[str]) -> Completed:
        seen.append(command)
        return Completed(returncodes[len(seen) - 1])

    monkeypatch.setattr(runner.subprocess, "run", fake_run)

    exit_code = runner.run_commands(commands)

    assert exit_code == 29
    assert seen == commands[:8]
    assert runner.SUCCESS_MARKER not in capsys.readouterr().out


def test_runner_does_not_emit_success_marker_if_selection_universe_registry_fails(
    monkeypatch,
    capsys,
):
    class Completed:
        def __init__(self, returncode: int) -> None:
            self.returncode = returncode

    commands = [
        [
            "python",
            "validate_atomicrows_research_provenance_evidence_tier_classification.py",
        ],
        [
            "python",
            "validate_atomicrows_owner_submitted_research_source_intake_registry.py",
        ],
        [
            "python",
            "validate_atomicrows_research_source_to_candidate_family_gate.py",
        ],
        ["python", "validate_atomicrows_parameter_stack_role_taxonomy.py"],
        ["python", "validate_atomicrows_parameter_stack_completeness_gate.py"],
        ["python", "validate_atomicrows_parameter_stack_compatibility_gate.py"],
        ["python", "validate_edge_parameter_stack_selection_packet.py"],
        ["python", "validate_qtt_trade_context_packet.py"],
        ["python", "validate_atomicrows_parameter_selection_universe_registry.py"],
        ["python", "later_gate.py"],
    ]
    returncodes = [0, 0, 0, 0, 0, 0, 0, 0, 31, 0]
    seen: list[list[str]] = []

    def fake_run(command: list[str]) -> Completed:
        seen.append(command)
        return Completed(returncodes[len(seen) - 1])

    monkeypatch.setattr(runner.subprocess, "run", fake_run)

    exit_code = runner.run_commands(commands)

    assert exit_code == 31
    assert seen == commands[:9]
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
