"""Small value objects for PR137L static boundary validation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class PR137RStaticEvidenceSnapshot:
    source_report: str
    atomicrows_bundle_artifact_found: bool
    atomicrows_functional_bundle_status: str
    expected_atomicrows_row_count: int
    atomicrows_row_count_proven: bool
    atomicrows_row_count_value: int
    atomicrows_schema_validated: bool
    atomicrows_validation_error_count: int
    atomicrows_row_family_source_files_found: bool
    atomicrows_row_family_source_file_count: int
    atomicrows_bundle_builder_found: bool
    atomicrows_bundle_validator_found: bool
    atomicrows_agent_read_only_consumer_found: bool
    atomicrows_agent_consumption_boundary: str
    atomicrows_final_readiness_gate_found: bool
    atomicrows_day1_live_trading_ready: bool
    atomicrows_profit_evidence_created: bool
    atomicrows_quantum_advantage_evidence_created: bool
    atomicrows_semantic_row_contract_complete: bool
    atomicrows_pr137l_usage: str

    def as_report(self) -> dict[str, Any]:
        return {
            "source_report": self.source_report,
            "atomicrows_bundle_artifact_found": self.atomicrows_bundle_artifact_found,
            "atomicrows_functional_bundle_status": self.atomicrows_functional_bundle_status,
            "expected_atomicrows_row_count": self.expected_atomicrows_row_count,
            "atomicrows_row_count_proven": self.atomicrows_row_count_proven,
            "atomicrows_row_count_value": self.atomicrows_row_count_value,
            "atomicrows_schema_validated": self.atomicrows_schema_validated,
            "atomicrows_validation_error_count": self.atomicrows_validation_error_count,
            "atomicrows_row_family_source_files_found": (
                self.atomicrows_row_family_source_files_found
            ),
            "atomicrows_row_family_source_file_count": (
                self.atomicrows_row_family_source_file_count
            ),
            "atomicrows_bundle_builder_found": self.atomicrows_bundle_builder_found,
            "atomicrows_bundle_validator_found": self.atomicrows_bundle_validator_found,
            "atomicrows_agent_read_only_consumer_found": (
                self.atomicrows_agent_read_only_consumer_found
            ),
            "atomicrows_agent_consumption_boundary": (
                self.atomicrows_agent_consumption_boundary
            ),
            "atomicrows_final_readiness_gate_found": (
                self.atomicrows_final_readiness_gate_found
            ),
            "atomicrows_day1_live_trading_ready": self.atomicrows_day1_live_trading_ready,
            "atomicrows_profit_evidence_created": self.atomicrows_profit_evidence_created,
            "atomicrows_quantum_advantage_evidence_created": (
                self.atomicrows_quantum_advantage_evidence_created
            ),
            "atomicrows_semantic_row_contract_complete": (
                self.atomicrows_semantic_row_contract_complete
            ),
            "atomicrows_pr137l_usage": self.atomicrows_pr137l_usage,
        }


@dataclass(frozen=True)
class DependencyChainSnapshot:
    source_sequence: str
    active_sequence_observed_prefix: tuple[str, ...]
    pr137l_occurrence_count: int
    pr137_to_pr137l: bool
    pr137l_to_pr138: bool
    pr138_requires_pr137l: bool
    pr137r_active_sequence_node: bool
    disconnected_roadmap_created: bool
    controller_mutation_required: bool
    controller_mutation_decision: str

    def as_report(self) -> dict[str, Any]:
        return {
            "source_sequence": self.source_sequence,
            "active_sequence_observed_prefix": list(self.active_sequence_observed_prefix),
            "pr137l_occurrence_count": self.pr137l_occurrence_count,
            "pr137_to_pr137l": self.pr137_to_pr137l,
            "pr137l_to_pr138": self.pr137l_to_pr138,
            "pr138_requires_pr137l": self.pr138_requires_pr137l,
            "pr137r_active_sequence_node": self.pr137r_active_sequence_node,
            "disconnected_roadmap_created": self.disconnected_roadmap_created,
            "controller_mutation_required": self.controller_mutation_required,
            "controller_mutation_decision": self.controller_mutation_decision,
        }


@dataclass(frozen=True)
class ValidationOutcome:
    ok: bool
    failures: tuple[str, ...]
    receipts: tuple[str, ...]

