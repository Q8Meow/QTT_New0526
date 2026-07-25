"""Central immutable materialization and resolver for all 135 parameter rows."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
import json
import re
from types import MappingProxyType
from typing import Mapping

from .context import exact_decimal
from .errors import NumericDomainError, ParameterPolicyError, ReasonCode


@dataclass(frozen=True, slots=True)
class SourceClaimJustificationV1:
    binding_rule_ref: str
    claim_selector: str
    exact_parameter_scope: tuple[str, ...]
    justification: str
    source_identity_ref: str

    def __post_init__(self) -> None:
        required = (
            self.binding_rule_ref,
            self.claim_selector,
            self.justification,
            self.source_identity_ref,
        )
        if any(not isinstance(value, str) or not value for value in required):
            raise ParameterPolicyError(
                ReasonCode.PARAMETER_OUT_OF_POLICY,
                "source-claim justification is incomplete",
            )
        if not isinstance(self.exact_parameter_scope, tuple) or any(
            not isinstance(value, str) or not value
            for value in self.exact_parameter_scope
        ):
            raise ParameterPolicyError(
                ReasonCode.PARAMETER_OUT_OF_POLICY,
                "source-claim parameter scope must be a string tuple",
            )
        if len(self.exact_parameter_scope) != len(
            set(self.exact_parameter_scope)
        ):
            raise ParameterPolicyError(
                ReasonCode.PARAMETER_OUT_OF_POLICY,
                "source-claim parameter scope must be unique",
            )


@dataclass(frozen=True, slots=True)
class ParameterPolicyRecordV1:
    canonical_owner: str
    certified_step11_custody_ref: str
    certified_step11_row_embedded_in_prompt: bool
    codex_online_research_allowed: bool
    direct_source_claim_justifications: tuple[SourceClaimJustificationV1, ...]
    effective_bounded_search_space_or_fit_constraint: str
    effective_day1_seed_value_or_resolution_rule: str
    effective_default_authority_class: str
    effective_fallback_behavior_when_value_unavailable: str
    effective_owner_dashboard_editability_class: str
    effective_policy_authority: str
    effective_reference_range_or_structural_constraint: str
    effective_resolution_class: str
    effective_source_state_refs: tuple[str, ...]
    effective_ui_widget_class: str
    effective_unit_or_basis: str
    effective_value_source_class: str
    evidence_basis_class: str
    evidence_binding_rule_refs: tuple[str, ...]
    family_evidence_binding_ref: str
    implementation_resolution_kind: str
    launch_computability_state: str
    master_plan_heading_path: tuple[str, ...]
    master_plan_section_id: str
    missing_stale_invalid_behavior: str
    parameter_audit_id: str
    parameter_id: str
    parameter_symbol: str
    precision_and_rounding_policy: tuple[tuple[str, str], ...]
    runtime_resolution_procedure: tuple[str, ...]
    source_line_end: int
    source_line_start: int
    step12_primary_tranche_id: str
    original_row_json: str

    def __post_init__(self) -> None:
        string_fields = (
            "canonical_owner",
            "certified_step11_custody_ref",
            "effective_bounded_search_space_or_fit_constraint",
            "effective_day1_seed_value_or_resolution_rule",
            "effective_default_authority_class",
            "effective_fallback_behavior_when_value_unavailable",
            "effective_owner_dashboard_editability_class",
            "effective_policy_authority",
            "effective_reference_range_or_structural_constraint",
            "effective_resolution_class",
            "effective_ui_widget_class",
            "effective_unit_or_basis",
            "effective_value_source_class",
            "evidence_basis_class",
            "family_evidence_binding_ref",
            "implementation_resolution_kind",
            "launch_computability_state",
            "master_plan_section_id",
            "missing_stale_invalid_behavior",
            "parameter_audit_id",
            "parameter_id",
            "parameter_symbol",
            "step12_primary_tranche_id",
            "original_row_json",
        )
        if any(
            not isinstance(getattr(self, name), str)
            or not getattr(self, name)
            for name in string_fields
        ):
            raise ParameterPolicyError(
                ReasonCode.INCOMPLETE_CONTRACT, "parameter row is incomplete"
            )
        tuple_fields = (
            "effective_source_state_refs",
            "evidence_binding_rule_refs",
            "master_plan_heading_path",
            "runtime_resolution_procedure",
        )
        for name in tuple_fields:
            values = getattr(self, name)
            if (
                not isinstance(values, tuple)
                or any(not isinstance(value, str) or not value for value in values)
                or len(values) != len(set(values))
            ):
                raise ParameterPolicyError(
                    ReasonCode.PARAMETER_OUT_OF_POLICY,
                    f"{name} must be an immutable unique string tuple",
                )
        if (
            not isinstance(self.direct_source_claim_justifications, tuple)
            or any(
                not isinstance(value, SourceClaimJustificationV1)
                for value in self.direct_source_claim_justifications
            )
        ):
            raise ParameterPolicyError(
                ReasonCode.PARAMETER_OUT_OF_POLICY,
                "source-claim justifications must be typed immutable rows",
            )
        if (
            not isinstance(self.precision_and_rounding_policy, tuple)
            or not self.precision_and_rounding_policy
            or any(
                not isinstance(item, tuple)
                or len(item) != 2
                or any(
                    not isinstance(value, str) or not value
                    for value in item
                )
                for item in self.precision_and_rounding_policy
            )
            or len({item[0] for item in self.precision_and_rounding_policy})
            != len(self.precision_and_rounding_policy)
        ):
            raise ParameterPolicyError(
                ReasonCode.PARAMETER_OUT_OF_POLICY,
                "precision policy must be an immutable unique string mapping",
            )
        for name in (
            "certified_step11_row_embedded_in_prompt",
            "codex_online_research_allowed",
        ):
            if type(getattr(self, name)) is not bool:
                raise ParameterPolicyError(
                    ReasonCode.PARAMETER_OUT_OF_POLICY,
                    f"{name} must be a boolean",
                )
        if (
            self.canonical_owner != "QKUComputationControlPlaneV1"
            or self.certified_step11_row_embedded_in_prompt is not False
            or self.codex_online_research_allowed
            or self.effective_policy_authority
            != "CERTIFIED_STEP11_PARAMETER_POLICY"
            or self.step12_primary_tranche_id != "ST12-TRANCHE-A"
        ):
            raise ParameterPolicyError(
                ReasonCode.PARAMETER_OUT_OF_POLICY,
                f"parameter authority invariant failed for {self.parameter_id}",
            )
        if (
            isinstance(self.source_line_start, bool)
            or not isinstance(self.source_line_start, int)
            or isinstance(self.source_line_end, bool)
            or not isinstance(self.source_line_end, int)
            or self.source_line_start <= 0
            or self.source_line_end < self.source_line_start
        ):
            raise ParameterPolicyError(
                ReasonCode.PARAMETER_OUT_OF_POLICY,
                f"invalid certified custody line range for {self.parameter_id}",
            )
        try:
            original_row = json.loads(self.original_row_json)
        except json.JSONDecodeError as exc:
            raise ParameterPolicyError(
                ReasonCode.PARAMETER_OUT_OF_POLICY,
                "parameter original-row metadata is not valid JSON",
            ) from exc
        if not isinstance(original_row, dict):
            raise ParameterPolicyError(
                ReasonCode.PARAMETER_OUT_OF_POLICY,
                "parameter original-row metadata must be an object",
            )


@dataclass(frozen=True, slots=True)
class ResolvedParameterV1:
    parameter_id: str
    parameter_audit_id: str
    parameter_symbol: str
    value: str
    unit_or_basis: str
    resolution_class: str
    authority_class: str
    fallback: str
    owner_editability: str
    used_day1_seed: bool

    def __post_init__(self) -> None:
        for name in (
            "parameter_id",
            "parameter_audit_id",
            "parameter_symbol",
            "value",
            "unit_or_basis",
            "resolution_class",
            "authority_class",
            "fallback",
            "owner_editability",
        ):
            value = getattr(self, name)
            if not isinstance(value, str) or not value:
                raise ParameterPolicyError(
                    ReasonCode.PARAMETER_OUT_OF_POLICY,
                    f"resolved parameter {name} must be nonempty text",
                )
        if type(self.used_day1_seed) is not bool:
            raise ParameterPolicyError(
                ReasonCode.PARAMETER_OUT_OF_POLICY,
                "used_day1_seed must be a boolean",
            )


_PARAMETER_ROWS_JSON = r'''
[
{
  "canonical_owner": "QKUComputationControlPlaneV1",
  "certified_step11_custody_ref": "inputs/certified_step11/QTT_Stage1_Step11_Parameter_Policy_Adjudication_v1_0.jsonl#ST11-PARAM::00083",
  "certified_step11_row_embedded_in_prompt": false,
  "codex_online_research_allowed": false,
  "direct_source_claim_justifications": [],
  "effective_bounded_search_space_or_fit_constraint": "prose-only ideas may not enter promotion-sensitive paths without typed translation",
  "effective_day1_seed_value_or_resolution_rule": "TYPED_CONTRACT_REQUIRED",
  "effective_default_authority_class": "EXPLICIT_QTT_OR_OWNER_POLICY_SEED_OR_RESOLUTION_RULE",
  "effective_fallback_behavior_when_value_unavailable": "FAIL_CLOSED_TO_REGISTERED_LOWER_SAFE_PATH_OR_NO_TRADE",
  "effective_owner_dashboard_editability_class": "READ_ONLY_SYMBOLIC",
  "effective_policy_authority": "CERTIFIED_STEP11_PARAMETER_POLICY",
  "effective_reference_range_or_structural_constraint": "{TYPED_CONTRACT_REQUIRED}",
  "effective_resolution_class": "STATIC_ENUM",
  "effective_source_state_refs": [
    "OWNER_POLICY::D2_13C",
    "SOURCE_PACK::D2_13C"
  ],
  "effective_ui_widget_class": "FORMULA_BADGE",
  "effective_unit_or_basis": "typed-contract requirement rule",
  "effective_value_source_class": "QTT_TYPED_CONTRACT_RULE",
  "evidence_basis_class": "FAMILY_SOURCE_PACK_PLUS_EXACT_OWNER_APPROVED_VALUE",
  "evidence_binding_rule_refs": [],
  "family_evidence_binding_ref": "ST12-FAMILY-EVIDENCE::D2_13C",
  "implementation_resolution_kind": "STATIC_OR_DETERMINISTIC_RULE",
  "launch_computability_state": "COMPUTABLE_FROM_STATIC_VALUE_OR_DETERMINISTIC_RULE",
  "master_plan_heading_path": [
    "Part II — Retained institutional design and parameter catalog",
    "D2. Non-negotiable system laws",
    "D2.13C Report-injection firewall atomic parameter and control specification"
  ],
  "master_plan_section_id": "D2.13C",
  "missing_stale_invalid_behavior": "REJECT_INVALID_VALUE_NO_SILENT_DEFAULT",
  "parameter_audit_id": "ST11-PARAM::00083",
  "parameter_id": "ST10-PARAM::0083",
  "parameter_symbol": "req_rfw_type",
  "precision_and_rounding_policy": {
    "allowlist_check": "REQUIRED",
    "internal_numeric_type": "typed_symbolic",
    "normalization": "CANONICAL_EXACT_TOKEN_NO_FREE_TEXT_COERCION",
    "rounding": "NOT_APPLICABLE"
  },
  "runtime_resolution_procedure": [
    "Parse the declared Day-1 seed or deterministic rule into the declared type.",
    "Validate against the reference range and structural constraint.",
    "Apply the declared bounded edit/search law; reject any value outside it."
  ],
  "source_line_end": 3342,
  "source_line_start": 3331,
  "step12_primary_tranche_id": "ST12-TRANCHE-A"
},
{
  "canonical_owner": "QKUComputationControlPlaneV1",
  "certified_step11_custody_ref": "inputs/certified_step11/QTT_Stage1_Step11_Parameter_Policy_Adjudication_v1_0.jsonl#ST11-PARAM::00140",
  "certified_step11_row_embedded_in_prompt": false,
  "codex_online_research_allowed": false,
  "direct_source_claim_justifications": [],
  "effective_bounded_search_space_or_fit_constraint": "autonomy stage may not be sourced from free-form prose or undeclared runtime flags",
  "effective_day1_seed_value_or_resolution_rule": "CANONICAL_STAGE_REGISTRY_BINDING_REQUIRED",
  "effective_default_authority_class": "EXPLICIT_QTT_OR_OWNER_POLICY_SEED_OR_RESOLUTION_RULE",
  "effective_fallback_behavior_when_value_unavailable": "FAIL_CLOSED_TO_REGISTERED_LOWER_SAFE_PATH_OR_NO_TRADE",
  "effective_owner_dashboard_editability_class": "READ_ONLY_SYMBOLIC",
  "effective_policy_authority": "CERTIFIED_STEP11_PARAMETER_POLICY",
  "effective_reference_range_or_structural_constraint": "{CANONICAL_STAGE_REGISTRY_BINDING_REQUIRED}",
  "effective_resolution_class": "STATIC_ENUM",
  "effective_source_state_refs": [
    "OWNER_POLICY::D2_19A",
    "SOURCE_PACK::D2_19A"
  ],
  "effective_ui_widget_class": "FORMULA_BADGE",
  "effective_unit_or_basis": "stage-registry binding rule",
  "effective_value_source_class": "QTT_STEPPED_AUTONOMY_LAW",
  "evidence_basis_class": "FAMILY_SOURCE_PACK_PLUS_EXACT_OWNER_APPROVED_VALUE",
  "evidence_binding_rule_refs": [],
  "family_evidence_binding_ref": "ST12-FAMILY-EVIDENCE::D2_19A",
  "implementation_resolution_kind": "STATIC_OR_DETERMINISTIC_RULE",
  "launch_computability_state": "COMPUTABLE_FROM_STATIC_VALUE_OR_DETERMINISTIC_RULE",
  "master_plan_heading_path": [
    "Part II — Retained institutional design and parameter catalog",
    "D2. Non-negotiable system laws",
    "D2.19A Stepped-autonomy transition atomic parameter and control specification"
  ],
  "master_plan_section_id": "D2.19A",
  "missing_stale_invalid_behavior": "REJECT_INVALID_VALUE_NO_SILENT_DEFAULT",
  "parameter_audit_id": "ST11-PARAM::00140",
  "parameter_id": "ST10-PARAM::0140",
  "parameter_symbol": "req_stage_reg",
  "precision_and_rounding_policy": {
    "allowlist_check": "REQUIRED",
    "internal_numeric_type": "typed_symbolic",
    "normalization": "CANONICAL_EXACT_TOKEN_NO_FREE_TEXT_COERCION",
    "rounding": "NOT_APPLICABLE"
  },
  "runtime_resolution_procedure": [
    "Parse the declared Day-1 seed or deterministic rule into the declared type.",
    "Validate against the reference range and structural constraint.",
    "Apply the declared bounded edit/search law; reject any value outside it."
  ],
  "source_line_end": 4299,
  "source_line_start": 4285,
  "step12_primary_tranche_id": "ST12-TRANCHE-A"
},
{
  "canonical_owner": "QKUComputationControlPlaneV1",
  "certified_step11_custody_ref": "inputs/certified_step11/QTT_Stage1_Step11_Parameter_Policy_Adjudication_v1_0.jsonl#ST11-PARAM::00217",
  "certified_step11_row_embedded_in_prompt": false,
  "codex_online_research_allowed": false,
  "direct_source_claim_justifications": [],
  "effective_bounded_search_space_or_fit_constraint": "fixed symbolic requirement only; may not be weakened in the active edition",
  "effective_day1_seed_value_or_resolution_rule": "REQUIRED",
  "effective_default_authority_class": "EXPLICIT_QTT_OR_OWNER_POLICY_SEED_OR_RESOLUTION_RULE",
  "effective_fallback_behavior_when_value_unavailable": "FAIL_CLOSED_TO_REGISTERED_LOWER_SAFE_PATH_OR_NO_TRADE",
  "effective_owner_dashboard_editability_class": "READ_ONLY_SYMBOLIC",
  "effective_policy_authority": "CERTIFIED_STEP11_PARAMETER_POLICY",
  "effective_reference_range_or_structural_constraint": "{REQUIRED}",
  "effective_resolution_class": "STATIC_ENUM",
  "effective_source_state_refs": [
    "OWNER_POLICY::D3_1A",
    "SOURCE_PACK::D3_1A"
  ],
  "effective_ui_widget_class": "FORMULA_BADGE",
  "effective_unit_or_basis": "provenance requirement",
  "effective_value_source_class": "QTT_OFFLINE_ARTIFACT_GOVERNANCE_RULE",
  "evidence_basis_class": "FAMILY_SOURCE_PACK_PLUS_EXACT_OWNER_APPROVED_VALUE",
  "evidence_binding_rule_refs": [],
  "family_evidence_binding_ref": "ST12-FAMILY-EVIDENCE::D3_1A",
  "implementation_resolution_kind": "STATIC_OR_DETERMINISTIC_RULE",
  "launch_computability_state": "COMPUTABLE_FROM_STATIC_VALUE_OR_DETERMINISTIC_RULE",
  "master_plan_heading_path": [
    "Part II — Retained institutional design and parameter catalog",
    "D3. Operating architecture",
    "D3.1A Three-lane architecture atomic parameter and control specification"
  ],
  "master_plan_section_id": "D3.1A",
  "missing_stale_invalid_behavior": "REJECT_INVALID_VALUE_NO_SILENT_DEFAULT",
  "parameter_audit_id": "ST11-PARAM::00217",
  "parameter_id": "ST10-PARAM::0217",
  "parameter_symbol": "req_laneC_prov",
  "precision_and_rounding_policy": {
    "allowlist_check": "REQUIRED",
    "internal_numeric_type": "typed_symbolic",
    "normalization": "CANONICAL_EXACT_TOKEN_NO_FREE_TEXT_COERCION",
    "rounding": "NOT_APPLICABLE"
  },
  "runtime_resolution_procedure": [
    "Parse the declared Day-1 seed or deterministic rule into the declared type.",
    "Validate against the reference range and structural constraint.",
    "Apply the declared bounded edit/search law; reject any value outside it."
  ],
  "source_line_end": 6029,
  "source_line_start": 6018,
  "step12_primary_tranche_id": "ST12-TRANCHE-A"
},
{
  "canonical_owner": "QKUComputationControlPlaneV1",
  "certified_step11_custody_ref": "inputs/certified_step11/QTT_Stage1_Step11_Parameter_Policy_Adjudication_v1_0.jsonl#ST11-PARAM::00231",
  "certified_step11_row_embedded_in_prompt": false,
  "codex_online_research_allowed": false,
  "direct_source_claim_justifications": [],
  "effective_bounded_search_space_or_fit_constraint": "fixed symbolic requirement only; may not be weakened in the active edition",
  "effective_day1_seed_value_or_resolution_rule": "REQUIRED",
  "effective_default_authority_class": "EXPLICIT_QTT_OR_OWNER_POLICY_SEED_OR_RESOLUTION_RULE",
  "effective_fallback_behavior_when_value_unavailable": "FAIL_CLOSED_TO_REGISTERED_LOWER_SAFE_PATH_OR_NO_TRADE",
  "effective_owner_dashboard_editability_class": "READ_ONLY_SYMBOLIC",
  "effective_policy_authority": "CERTIFIED_STEP11_PARAMETER_POLICY",
  "effective_reference_range_or_structural_constraint": "{REQUIRED}",
  "effective_resolution_class": "STATIC_ENUM",
  "effective_source_state_refs": [
    "OWNER_POLICY::D3_3S",
    "SOURCE_PACK::D3_3S"
  ],
  "effective_ui_widget_class": "FORMULA_BADGE",
  "effective_unit_or_basis": "service-presence requirement",
  "effective_value_source_class": "QTT_ROOT_SERVICE_GRAPH_RULE",
  "evidence_basis_class": "FAMILY_SOURCE_PACK_PLUS_EXACT_OWNER_APPROVED_VALUE",
  "evidence_binding_rule_refs": [],
  "family_evidence_binding_ref": "ST12-FAMILY-EVIDENCE::D3_3S",
  "implementation_resolution_kind": "STATIC_OR_DETERMINISTIC_RULE",
  "launch_computability_state": "COMPUTABLE_FROM_STATIC_VALUE_OR_DETERMINISTIC_RULE",
  "master_plan_heading_path": [
    "Part II — Retained institutional design and parameter catalog",
    "D3. Operating architecture",
    "D3.3S Service-map atomic parameter and control specification"
  ],
  "master_plan_section_id": "D3.3S",
  "missing_stale_invalid_behavior": "REJECT_INVALID_VALUE_NO_SILENT_DEFAULT",
  "parameter_audit_id": "ST11-PARAM::00231",
  "parameter_id": "ST10-PARAM::0231",
  "parameter_symbol": "req_svc_reg",
  "precision_and_rounding_policy": {
    "allowlist_check": "REQUIRED",
    "internal_numeric_type": "typed_symbolic",
    "normalization": "CANONICAL_EXACT_TOKEN_NO_FREE_TEXT_COERCION",
    "rounding": "NOT_APPLICABLE"
  },
  "runtime_resolution_procedure": [
    "Parse the declared Day-1 seed or deterministic rule into the declared type.",
    "Validate against the reference range and structural constraint.",
    "Apply the declared bounded edit/search law; reject any value outside it."
  ],
  "source_line_end": 6374,
  "source_line_start": 6363,
  "step12_primary_tranche_id": "ST12-TRANCHE-A"
},
{
  "canonical_owner": "QKUComputationControlPlaneV1",
  "certified_step11_custody_ref": "inputs/certified_step11/QTT_Stage1_Step11_Parameter_Policy_Adjudication_v1_0.jsonl#ST11-PARAM::00269",
  "certified_step11_row_embedded_in_prompt": false,
  "codex_online_research_allowed": false,
  "direct_source_claim_justifications": [],
  "effective_bounded_search_space_or_fit_constraint": "fixed symbolic requirement only; may not be weakened in the active edition",
  "effective_day1_seed_value_or_resolution_rule": "REQUIRED_FOR_ALL_LIVE_AUTHORITATIVE_SLEEVES",
  "effective_default_authority_class": "EXPLICIT_QTT_OR_OWNER_POLICY_SEED_OR_RESOLUTION_RULE",
  "effective_fallback_behavior_when_value_unavailable": "FAIL_CLOSED_TO_REGISTERED_LOWER_SAFE_PATH_OR_NO_TRADE",
  "effective_owner_dashboard_editability_class": "READ_ONLY_SYMBOLIC",
  "effective_policy_authority": "CERTIFIED_STEP11_PARAMETER_POLICY",
  "effective_reference_range_or_structural_constraint": "{REQUIRED_FOR_ALL_LIVE_AUTHORITATIVE_SLEEVES}",
  "effective_resolution_class": "STATIC_ENUM",
  "effective_source_state_refs": [
    "OWNER_POLICY::D3_3ABA",
    "SOURCE_PACK::D3_3ABA"
  ],
  "effective_ui_widget_class": "FORMULA_BADGE",
  "effective_unit_or_basis": "stage-family registry requirement",
  "effective_value_source_class": "QTT_LATENCY_LEDGER_RULE",
  "evidence_basis_class": "FAMILY_SOURCE_PACK_PLUS_EXACT_OWNER_APPROVED_VALUE",
  "evidence_binding_rule_refs": [],
  "family_evidence_binding_ref": "ST12-FAMILY-EVIDENCE::D3_3ABA",
  "implementation_resolution_kind": "STATIC_OR_DETERMINISTIC_RULE",
  "launch_computability_state": "COMPUTABLE_FROM_STATIC_VALUE_OR_DETERMINISTIC_RULE",
  "master_plan_heading_path": [
    "Part II — Retained institutional design and parameter catalog",
    "D3. Operating architecture",
    "D3.3ABA Critical-path latency-budget ledger atomic parameter and control specification"
  ],
  "master_plan_section_id": "D3.3ABA",
  "missing_stale_invalid_behavior": "REJECT_INVALID_VALUE_NO_SILENT_DEFAULT",
  "parameter_audit_id": "ST11-PARAM::00269",
  "parameter_id": "ST10-PARAM::0269",
  "parameter_symbol": "req_lat_stg",
  "precision_and_rounding_policy": {
    "allowlist_check": "REQUIRED",
    "internal_numeric_type": "typed_symbolic",
    "normalization": "CANONICAL_EXACT_TOKEN_NO_FREE_TEXT_COERCION",
    "rounding": "NOT_APPLICABLE"
  },
  "runtime_resolution_procedure": [
    "Parse the declared Day-1 seed or deterministic rule into the declared type.",
    "Validate against the reference range and structural constraint.",
    "Apply the declared bounded edit/search law; reject any value outside it."
  ],
  "source_line_end": 7515,
  "source_line_start": 7504,
  "step12_primary_tranche_id": "ST12-TRANCHE-A"
},
{
  "canonical_owner": "QKUComputationControlPlaneV1",
  "certified_step11_custody_ref": "inputs/certified_step11/QTT_Stage1_Step11_Parameter_Policy_Adjudication_v1_0.jsonl#ST11-PARAM::00362",
  "certified_step11_row_embedded_in_prompt": false,
  "codex_online_research_allowed": false,
  "direct_source_claim_justifications": [],
  "effective_bounded_search_space_or_fit_constraint": "hidden undeclared file paths or string matching forbidden",
  "effective_day1_seed_value_or_resolution_rule": "CONSUMERS_MUST_BIND_THROUGH_DECLARED_REGISTRY_NAMESPACE_AND_CANONICAL_RESOLUTION_TARGET",
  "effective_default_authority_class": "EXPLICIT_QTT_OR_OWNER_POLICY_SEED_OR_RESOLUTION_RULE",
  "effective_fallback_behavior_when_value_unavailable": "FAIL_CLOSED_TO_REGISTERED_LOWER_SAFE_PATH_OR_NO_TRADE",
  "effective_owner_dashboard_editability_class": "READ_ONLY_SYMBOLIC",
  "effective_policy_authority": "CERTIFIED_STEP11_PARAMETER_POLICY",
  "effective_reference_range_or_structural_constraint": "{CONSUMERS_MUST_BIND_THROUGH_DECLARED_REGISTRY_NAMESPACE_AND_CANONICAL_RESOLUTION_TARGET}",
  "effective_resolution_class": "STATIC_RULE",
  "effective_source_state_refs": [
    "OWNER_POLICY::D3_3AB3B0",
    "SOURCE_PACK::D3_3AB3B0"
  ],
  "effective_ui_widget_class": "FORMULA_BADGE",
  "effective_unit_or_basis": "consumer-registry-binding rule",
  "effective_value_source_class": "QTT_FAST_LANE_ARTIFACT_GOVERNANCE_RULE",
  "evidence_basis_class": "FAMILY_SOURCE_PACK_PLUS_EXACT_OWNER_APPROVED_VALUE",
  "evidence_binding_rule_refs": [],
  "family_evidence_binding_ref": "ST12-FAMILY-EVIDENCE::D3_3AB3B0",
  "implementation_resolution_kind": "STATIC_OR_DETERMINISTIC_RULE",
  "launch_computability_state": "COMPUTABLE_FROM_STATIC_VALUE_OR_DETERMINISTIC_RULE",
  "master_plan_heading_path": [
    "Part II — Retained institutional design and parameter catalog",
    "D3. Operating architecture",
    "D3.3AB3B0 Fast-lane timing artifact-governance atomic parameter and control specification"
  ],
  "master_plan_section_id": "D3.3AB3B0",
  "missing_stale_invalid_behavior": "REJECT_INVALID_VALUE_NO_SILENT_DEFAULT",
  "parameter_audit_id": "ST11-PARAM::00362",
  "parameter_id": "ST10-PARAM::0362",
  "parameter_symbol": "rule_tart_bind",
  "precision_and_rounding_policy": {
    "allowlist_check": "REQUIRED",
    "internal_numeric_type": "typed_symbolic",
    "normalization": "CANONICAL_EXACT_TOKEN_NO_FREE_TEXT_COERCION",
    "rounding": "NOT_APPLICABLE"
  },
  "runtime_resolution_procedure": [
    "Parse the declared Day-1 seed or deterministic rule into the declared type.",
    "Validate against the reference range and structural constraint.",
    "Apply the declared bounded edit/search law; reject any value outside it."
  ],
  "source_line_end": 9116,
  "source_line_start": 9102,
  "step12_primary_tranche_id": "ST12-TRANCHE-A"
},
{
  "canonical_owner": "QKUComputationControlPlaneV1",
  "certified_step11_custody_ref": "inputs/certified_step11/QTT_Stage1_Step11_Parameter_Policy_Adjudication_v1_0.jsonl#ST11-PARAM::00397",
  "certified_step11_row_embedded_in_prompt": false,
  "codex_online_research_allowed": false,
  "direct_source_claim_justifications": [],
  "effective_bounded_search_space_or_fit_constraint": "fixed namespace rule only; silent foreign-group discovery is forbidden",
  "effective_day1_seed_value_or_resolution_rule": "ENTRYPOINT_NAMES_MUST_RESOLVE_INSIDE_QTT_OWNED_CONNECTOR_GROUP",
  "effective_default_authority_class": "PUBLIC_METHOD_OR_PINNED_PROVIDER_DEFAULT_REQUIRES_IMPLEMENTATION_VERSION_BINDING",
  "effective_fallback_behavior_when_value_unavailable": "FAIL_CLOSED_TO_REGISTERED_LOWER_SAFE_PATH_OR_NO_TRADE",
  "effective_owner_dashboard_editability_class": "READ_ONLY_SYMBOLIC",
  "effective_policy_authority": "CERTIFIED_STEP11_PARAMETER_POLICY",
  "effective_reference_range_or_structural_constraint": "{ENTRYPOINT_NAMES_MUST_RESOLVE_INSIDE_QTT_OWNED_CONNECTOR_GROUP}",
  "effective_resolution_class": "STATIC_RULE",
  "effective_source_state_refs": [
    "OWNER_POLICY::D3_3AC1C",
    "SOURCE_PACK::D3_3AC1C"
  ],
  "effective_ui_widget_class": "FORMULA_BADGE",
  "effective_unit_or_basis": "entrypoint-namespace rule",
  "effective_value_source_class": "PUBLIC_PYPA_ENTRY_POINTS_SPEC_PLUS_QTT_RULE",
  "evidence_basis_class": "FAMILY_SOURCE_PACK_PLUS_EXACT_OWNER_APPROVED_VALUE",
  "evidence_binding_rule_refs": [],
  "family_evidence_binding_ref": "ST12-FAMILY-EVIDENCE::D3_3AC1C",
  "implementation_resolution_kind": "STATIC_OR_DETERMINISTIC_RULE",
  "launch_computability_state": "COMPUTABLE_FROM_STATIC_VALUE_OR_DETERMINISTIC_RULE",
  "master_plan_heading_path": [
    "Part II — Retained institutional design and parameter catalog",
    "D3. Operating architecture",
    "D3.3AC1C Extension-first connector-plugin and platform-onboarding atomic parameter and control specification"
  ],
  "master_plan_section_id": "D3.3AC1C",
  "missing_stale_invalid_behavior": "REJECT_INVALID_VALUE_NO_SILENT_DEFAULT",
  "parameter_audit_id": "ST11-PARAM::00397",
  "parameter_id": "ST10-PARAM::0397",
  "parameter_symbol": "rule_plug_ns",
  "precision_and_rounding_policy": {
    "allowlist_check": "REQUIRED",
    "internal_numeric_type": "typed_symbolic",
    "normalization": "CANONICAL_EXACT_TOKEN_NO_FREE_TEXT_COERCION",
    "rounding": "NOT_APPLICABLE"
  },
  "runtime_resolution_procedure": [
    "Parse the declared Day-1 seed or deterministic rule into the declared type.",
    "Validate against the reference range and structural constraint.",
    "Apply the declared bounded edit/search law; reject any value outside it."
  ],
  "source_line_end": 9791,
  "source_line_start": 9780,
  "step12_primary_tranche_id": "ST12-TRANCHE-A"
},
{
  "canonical_owner": "QKUComputationControlPlaneV1",
  "certified_step11_custody_ref": "inputs/certified_step11/QTT_Stage1_Step11_Parameter_Policy_Adjudication_v1_0.jsonl#ST11-PARAM::00398",
  "certified_step11_row_embedded_in_prompt": false,
  "codex_online_research_allowed": false,
  "direct_source_claim_justifications": [],
  "effective_bounded_search_space_or_fit_constraint": "silent fallback to arbitrary module import side effects is forbidden",
  "effective_day1_seed_value_or_resolution_rule": "DISCOVERED_PLUGIN_MUST_BIND_ONE_EXPLICIT_CONNECTOR_FACTORY_CALLABLE",
  "effective_default_authority_class": "EXPLICIT_QTT_OR_OWNER_POLICY_SEED_OR_RESOLUTION_RULE",
  "effective_fallback_behavior_when_value_unavailable": "FAIL_CLOSED_TO_REGISTERED_LOWER_SAFE_PATH_OR_NO_TRADE",
  "effective_owner_dashboard_editability_class": "READ_ONLY_SYMBOLIC",
  "effective_policy_authority": "CERTIFIED_STEP11_PARAMETER_POLICY",
  "effective_reference_range_or_structural_constraint": "{DISCOVERED_PLUGIN_MUST_BIND_ONE_EXPLICIT_CONNECTOR_FACTORY_CALLABLE}",
  "effective_resolution_class": "STATIC_RULE",
  "effective_source_state_refs": [
    "OWNER_POLICY::D3_3AC1C",
    "SOURCE_PACK::D3_3AC1C"
  ],
  "effective_ui_widget_class": "FORMULA_BADGE",
  "effective_unit_or_basis": "adapter-factory binding rule",
  "effective_value_source_class": "QTT_CONNECTOR_ADAPTER_FACTORY_RULE",
  "evidence_basis_class": "FAMILY_SOURCE_PACK_PLUS_EXACT_OWNER_APPROVED_VALUE",
  "evidence_binding_rule_refs": [],
  "family_evidence_binding_ref": "ST12-FAMILY-EVIDENCE::D3_3AC1C",
  "implementation_resolution_kind": "STATIC_OR_DETERMINISTIC_RULE",
  "launch_computability_state": "COMPUTABLE_FROM_STATIC_VALUE_OR_DETERMINISTIC_RULE",
  "master_plan_heading_path": [
    "Part II — Retained institutional design and parameter catalog",
    "D3. Operating architecture",
    "D3.3AC1C Extension-first connector-plugin and platform-onboarding atomic parameter and control specification"
  ],
  "master_plan_section_id": "D3.3AC1C",
  "missing_stale_invalid_behavior": "REJECT_INVALID_VALUE_NO_SILENT_DEFAULT",
  "parameter_audit_id": "ST11-PARAM::00398",
  "parameter_id": "ST10-PARAM::0398",
  "parameter_symbol": "rule_plug_fact",
  "precision_and_rounding_policy": {
    "allowlist_check": "REQUIRED",
    "internal_numeric_type": "typed_symbolic",
    "normalization": "CANONICAL_EXACT_TOKEN_NO_FREE_TEXT_COERCION",
    "rounding": "NOT_APPLICABLE"
  },
  "runtime_resolution_procedure": [
    "Parse the declared Day-1 seed or deterministic rule into the declared type.",
    "Validate against the reference range and structural constraint.",
    "Apply the declared bounded edit/search law; reject any value outside it."
  ],
  "source_line_end": 9803,
  "source_line_start": 9792,
  "step12_primary_tranche_id": "ST12-TRANCHE-A"
},
{
  "canonical_owner": "QKUComputationControlPlaneV1",
  "certified_step11_custody_ref": "inputs/certified_step11/QTT_Stage1_Step11_Parameter_Policy_Adjudication_v1_0.jsonl#ST11-PARAM::00400",
  "certified_step11_row_embedded_in_prompt": false,
  "codex_online_research_allowed": false,
  "direct_source_claim_justifications": [],
  "effective_bounded_search_space_or_fit_constraint": "missing account-state mapper forces read-only or applicable shadow-observe or live-twin comparison-only",
  "effective_day1_seed_value_or_resolution_rule": "ONE_ACCOUNT_STATE_MAPPER_REQUIRED_PER_NEW_PLATFORM",
  "effective_default_authority_class": "EXPLICIT_QTT_OR_OWNER_POLICY_SEED_OR_RESOLUTION_RULE",
  "effective_fallback_behavior_when_value_unavailable": "FAIL_CLOSED_TO_REGISTERED_LOWER_SAFE_PATH_OR_NO_TRADE",
  "effective_owner_dashboard_editability_class": "READ_ONLY_SYMBOLIC",
  "effective_policy_authority": "CERTIFIED_STEP11_PARAMETER_POLICY",
  "effective_reference_range_or_structural_constraint": "{ONE_ACCOUNT_STATE_MAPPER_REQUIRED_PER_NEW_PLATFORM}",
  "effective_resolution_class": "STATIC_RULE",
  "effective_source_state_refs": [
    "OWNER_POLICY::D3_3AC1C",
    "SOURCE_PACK::D3_3AC1C"
  ],
  "effective_ui_widget_class": "FORMULA_BADGE",
  "effective_unit_or_basis": "account-state-mapper rule",
  "effective_value_source_class": "QTT_LEDGER_MAPPER_COMPLETENESS_RULE",
  "evidence_basis_class": "FAMILY_SOURCE_PACK_PLUS_EXACT_OWNER_APPROVED_VALUE",
  "evidence_binding_rule_refs": [],
  "family_evidence_binding_ref": "ST12-FAMILY-EVIDENCE::D3_3AC1C",
  "implementation_resolution_kind": "STATIC_OR_DETERMINISTIC_RULE",
  "launch_computability_state": "COMPUTABLE_FROM_STATIC_VALUE_OR_DETERMINISTIC_RULE",
  "master_plan_heading_path": [
    "Part II — Retained institutional design and parameter catalog",
    "D3. Operating architecture",
    "D3.3AC1C Extension-first connector-plugin and platform-onboarding atomic parameter and control specification"
  ],
  "master_plan_section_id": "D3.3AC1C",
  "missing_stale_invalid_behavior": "REJECT_INVALID_VALUE_NO_SILENT_DEFAULT",
  "parameter_audit_id": "ST11-PARAM::00400",
  "parameter_id": "ST10-PARAM::0400",
  "parameter_symbol": "rule_plug_acct",
  "precision_and_rounding_policy": {
    "allowlist_check": "REQUIRED",
    "internal_numeric_type": "typed_symbolic",
    "normalization": "CANONICAL_EXACT_TOKEN_NO_FREE_TEXT_COERCION",
    "rounding": "NOT_APPLICABLE"
  },
  "runtime_resolution_procedure": [
    "Parse the declared Day-1 seed or deterministic rule into the declared type.",
    "Validate against the reference range and structural constraint.",
    "Apply the declared bounded edit/search law; reject any value outside it."
  ],
  "source_line_end": 9827,
  "source_line_start": 9816,
  "step12_primary_tranche_id": "ST12-TRANCHE-A"
},
{
  "canonical_owner": "QKUComputationControlPlaneV1",
  "certified_step11_custody_ref": "inputs/certified_step11/QTT_Stage1_Step11_Parameter_Policy_Adjudication_v1_0.jsonl#ST11-PARAM::00401",
  "certified_step11_row_embedded_in_prompt": false,
  "codex_online_research_allowed": false,
  "direct_source_claim_justifications": [],
  "effective_bounded_search_space_or_fit_constraint": "missing position-lot mapper forces read-only or applicable shadow-observe or live-twin comparison-only",
  "effective_day1_seed_value_or_resolution_rule": "ONE_POSITION_LOT_MAPPER_REQUIRED_PER_NEW_PLATFORM",
  "effective_default_authority_class": "EXPLICIT_QTT_OR_OWNER_POLICY_SEED_OR_RESOLUTION_RULE",
  "effective_fallback_behavior_when_value_unavailable": "FAIL_CLOSED_TO_REGISTERED_LOWER_SAFE_PATH_OR_NO_TRADE",
  "effective_owner_dashboard_editability_class": "READ_ONLY_SYMBOLIC",
  "effective_policy_authority": "CERTIFIED_STEP11_PARAMETER_POLICY",
  "effective_reference_range_or_structural_constraint": "{ONE_POSITION_LOT_MAPPER_REQUIRED_PER_NEW_PLATFORM}",
  "effective_resolution_class": "STATIC_RULE",
  "effective_source_state_refs": [
    "OWNER_POLICY::D3_3AC1C",
    "SOURCE_PACK::D3_3AC1C"
  ],
  "effective_ui_widget_class": "FORMULA_BADGE",
  "effective_unit_or_basis": "position-lot-mapper rule",
  "effective_value_source_class": "QTT_LEDGER_MAPPER_COMPLETENESS_RULE",
  "evidence_basis_class": "FAMILY_SOURCE_PACK_PLUS_EXACT_OWNER_APPROVED_VALUE",
  "evidence_binding_rule_refs": [],
  "family_evidence_binding_ref": "ST12-FAMILY-EVIDENCE::D3_3AC1C",
  "implementation_resolution_kind": "STATIC_OR_DETERMINISTIC_RULE",
  "launch_computability_state": "COMPUTABLE_FROM_STATIC_VALUE_OR_DETERMINISTIC_RULE",
  "master_plan_heading_path": [
    "Part II — Retained institutional design and parameter catalog",
    "D3. Operating architecture",
    "D3.3AC1C Extension-first connector-plugin and platform-onboarding atomic parameter and control specification"
  ],
  "master_plan_section_id": "D3.3AC1C",
  "missing_stale_invalid_behavior": "REJECT_INVALID_VALUE_NO_SILENT_DEFAULT",
  "parameter_audit_id": "ST11-PARAM::00401",
  "parameter_id": "ST10-PARAM::0401",
  "parameter_symbol": "rule_plug_lot",
  "precision_and_rounding_policy": {
    "allowlist_check": "REQUIRED",
    "internal_numeric_type": "typed_symbolic",
    "normalization": "CANONICAL_EXACT_TOKEN_NO_FREE_TEXT_COERCION",
    "rounding": "NOT_APPLICABLE"
  },
  "runtime_resolution_procedure": [
    "Parse the declared Day-1 seed or deterministic rule into the declared type.",
    "Validate against the reference range and structural constraint.",
    "Apply the declared bounded edit/search law; reject any value outside it."
  ],
  "source_line_end": 9839,
  "source_line_start": 9828,
  "step12_primary_tranche_id": "ST12-TRANCHE-A"
},
{
  "canonical_owner": "QKUComputationControlPlaneV1",
  "certified_step11_custody_ref": "inputs/certified_step11/QTT_Stage1_Step11_Parameter_Policy_Adjudication_v1_0.jsonl#ST11-PARAM::00404",
  "certified_step11_row_embedded_in_prompt": false,
  "codex_online_research_allowed": false,
  "direct_source_claim_justifications": [],
  "effective_bounded_search_space_or_fit_constraint": "successful install or discovery may not imply live authority",
  "effective_day1_seed_value_or_resolution_rule": "DISCOVERED_PLUGIN_REMAINS_NONLIVE_UNTIL_COMPATIBILITY_AND_MAPPERS_ARE_GREEN",
  "effective_default_authority_class": "EXPLICIT_QTT_OR_OWNER_POLICY_SEED_OR_RESOLUTION_RULE",
  "effective_fallback_behavior_when_value_unavailable": "FAIL_CLOSED_TO_REGISTERED_LOWER_SAFE_PATH_OR_NO_TRADE",
  "effective_owner_dashboard_editability_class": "READ_ONLY_SYMBOLIC",
  "effective_policy_authority": "CERTIFIED_STEP11_PARAMETER_POLICY",
  "effective_reference_range_or_structural_constraint": "{DISCOVERED_PLUGIN_REMAINS_NONLIVE_UNTIL_COMPATIBILITY_AND_MAPPERS_ARE_GREEN}",
  "effective_resolution_class": "STATIC_RULE",
  "effective_source_state_refs": [
    "OWNER_POLICY::D3_3AC1C",
    "SOURCE_PACK::D3_3AC1C"
  ],
  "effective_ui_widget_class": "FORMULA_BADGE",
  "effective_unit_or_basis": "discovered-plugin authority rule",
  "effective_value_source_class": "QTT_PLUGIN_AUTHORITY_FAIL_CLOSED_RULE",
  "evidence_basis_class": "FAMILY_SOURCE_PACK_PLUS_EXACT_OWNER_APPROVED_VALUE",
  "evidence_binding_rule_refs": [],
  "family_evidence_binding_ref": "ST12-FAMILY-EVIDENCE::D3_3AC1C",
  "implementation_resolution_kind": "STATIC_OR_DETERMINISTIC_RULE",
  "launch_computability_state": "COMPUTABLE_FROM_STATIC_VALUE_OR_DETERMINISTIC_RULE",
  "master_plan_heading_path": [
    "Part II — Retained institutional design and parameter catalog",
    "D3. Operating architecture",
    "D3.3AC1C Extension-first connector-plugin and platform-onboarding atomic parameter and control specification"
  ],
  "master_plan_section_id": "D3.3AC1C",
  "missing_stale_invalid_behavior": "REJECT_INVALID_VALUE_NO_SILENT_DEFAULT",
  "parameter_audit_id": "ST11-PARAM::00404",
  "parameter_id": "ST10-PARAM::0404",
  "parameter_symbol": "rule_plug_auth",
  "precision_and_rounding_policy": {
    "allowlist_check": "REQUIRED",
    "internal_numeric_type": "typed_symbolic",
    "normalization": "CANONICAL_EXACT_TOKEN_NO_FREE_TEXT_COERCION",
    "rounding": "NOT_APPLICABLE"
  },
  "runtime_resolution_procedure": [
    "Parse the declared Day-1 seed or deterministic rule into the declared type.",
    "Validate against the reference range and structural constraint.",
    "Apply the declared bounded edit/search law; reject any value outside it."
  ],
  "source_line_end": 9875,
  "source_line_start": 9864,
  "step12_primary_tranche_id": "ST12-TRANCHE-A"
},
{
  "canonical_owner": "QKUComputationControlPlaneV1",
  "certified_step11_custody_ref": "inputs/certified_step11/QTT_Stage1_Step11_Parameter_Policy_Adjudication_v1_0.jsonl#ST11-PARAM::00405",
  "certified_step11_row_embedded_in_prompt": false,
  "codex_online_research_allowed": false,
  "direct_source_claim_justifications": [],
  "effective_bounded_search_space_or_fit_constraint": "fixed anti-branching rule only; may not be weakened in the active edition",
  "effective_day1_seed_value_or_resolution_rule": "NO_HARD_CODED_PLATFORM_LISTS_IN_CORE_RUNTIME_MODULES",
  "effective_default_authority_class": "EXPLICIT_QTT_OR_OWNER_POLICY_SEED_OR_RESOLUTION_RULE",
  "effective_fallback_behavior_when_value_unavailable": "FAIL_CLOSED_TO_REGISTERED_LOWER_SAFE_PATH_OR_NO_TRADE",
  "effective_owner_dashboard_editability_class": "READ_ONLY_SYMBOLIC",
  "effective_policy_authority": "CERTIFIED_STEP11_PARAMETER_POLICY",
  "effective_reference_range_or_structural_constraint": "{NO_HARD_CODED_PLATFORM_LISTS_IN_CORE_RUNTIME_MODULES}",
  "effective_resolution_class": "STATIC_RULE",
  "effective_source_state_refs": [
    "OWNER_POLICY::D3_3AC1C",
    "SOURCE_PACK::D3_3AC1C"
  ],
  "effective_ui_widget_class": "FORMULA_BADGE",
  "effective_unit_or_basis": "core-runtime hard-coded-platform-list rule",
  "effective_value_source_class": "QTT_EXTENSION_FIRST_CONNECTOR_RULE",
  "evidence_basis_class": "FAMILY_SOURCE_PACK_PLUS_EXACT_OWNER_APPROVED_VALUE",
  "evidence_binding_rule_refs": [],
  "family_evidence_binding_ref": "ST12-FAMILY-EVIDENCE::D3_3AC1C",
  "implementation_resolution_kind": "STATIC_OR_DETERMINISTIC_RULE",
  "launch_computability_state": "COMPUTABLE_FROM_STATIC_VALUE_OR_DETERMINISTIC_RULE",
  "master_plan_heading_path": [
    "Part II — Retained institutional design and parameter catalog",
    "D3. Operating architecture",
    "D3.3AC1C Extension-first connector-plugin and platform-onboarding atomic parameter and control specification"
  ],
  "master_plan_section_id": "D3.3AC1C",
  "missing_stale_invalid_behavior": "REJECT_INVALID_VALUE_NO_SILENT_DEFAULT",
  "parameter_audit_id": "ST11-PARAM::00405",
  "parameter_id": "ST10-PARAM::0405",
  "parameter_symbol": "rule_plug_core_list",
  "precision_and_rounding_policy": {
    "allowlist_check": "REQUIRED",
    "internal_numeric_type": "typed_symbolic",
    "normalization": "CANONICAL_EXACT_TOKEN_NO_FREE_TEXT_COERCION",
    "rounding": "NOT_APPLICABLE"
  },
  "runtime_resolution_procedure": [
    "Parse the declared Day-1 seed or deterministic rule into the declared type.",
    "Validate against the reference range and structural constraint.",
    "Apply the declared bounded edit/search law; reject any value outside it."
  ],
  "source_line_end": 9890,
  "source_line_start": 9876,
  "step12_primary_tranche_id": "ST12-TRANCHE-A"
},
{
  "canonical_owner": "QKUComputationControlPlaneV1",
  "certified_step11_custody_ref": "inputs/certified_step11/QTT_Stage1_Step11_Parameter_Policy_Adjudication_v1_0.jsonl#ST11-PARAM::00432",
  "certified_step11_row_embedded_in_prompt": false,
  "codex_online_research_allowed": false,
  "direct_source_claim_justifications": [],
  "effective_bounded_search_space_or_fit_constraint": "fixed symbolic rule only; may not be weakened in the active edition",
  "effective_day1_seed_value_or_resolution_rule": "EXECUTION_ADAPTER_MAY_NOT_BE_THE_ONLY_SOURCE_OF_POST_TRADE_TRUTH",
  "effective_default_authority_class": "EXPLICIT_QTT_OR_OWNER_POLICY_SEED_OR_RESOLUTION_RULE",
  "effective_fallback_behavior_when_value_unavailable": "FAIL_CLOSED_TO_REGISTERED_LOWER_SAFE_PATH_OR_NO_TRADE",
  "effective_owner_dashboard_editability_class": "READ_ONLY_SYMBOLIC",
  "effective_policy_authority": "CERTIFIED_STEP11_PARAMETER_POLICY",
  "effective_reference_range_or_structural_constraint": "{EXECUTION_ADAPTER_MAY_NOT_BE_THE_ONLY_SOURCE_OF_POST_TRADE_TRUTH}",
  "effective_resolution_class": "STATIC_RULE",
  "effective_source_state_refs": [
    "OWNER_POLICY::D3_3C0",
    "SOURCE_PACK::D3_3C0"
  ],
  "effective_ui_widget_class": "FORMULA_BADGE",
  "effective_unit_or_basis": "reconciliation-authority separation rule",
  "effective_value_source_class": "QTT_RECONCILIATION_AUTHORITY_RULE",
  "evidence_basis_class": "FAMILY_SOURCE_PACK_PLUS_EXACT_OWNER_APPROVED_VALUE",
  "evidence_binding_rule_refs": [],
  "family_evidence_binding_ref": "ST12-FAMILY-EVIDENCE::D3_3C0",
  "implementation_resolution_kind": "STATIC_OR_DETERMINISTIC_RULE",
  "launch_computability_state": "COMPUTABLE_FROM_STATIC_VALUE_OR_DETERMINISTIC_RULE",
  "master_plan_heading_path": [
    "Part II — Retained institutional design and parameter catalog",
    "D3. Operating architecture",
    "D3.3C0 Shadow-book and external-statement reconciliation atomic parameter and control specification"
  ],
  "master_plan_section_id": "D3.3C0",
  "missing_stale_invalid_behavior": "REJECT_INVALID_VALUE_NO_SILENT_DEFAULT",
  "parameter_audit_id": "ST11-PARAM::00432",
  "parameter_id": "ST10-PARAM::0432",
  "parameter_symbol": "rule_recon_sep",
  "precision_and_rounding_policy": {
    "allowlist_check": "REQUIRED",
    "internal_numeric_type": "typed_symbolic",
    "normalization": "CANONICAL_EXACT_TOKEN_NO_FREE_TEXT_COERCION",
    "rounding": "NOT_APPLICABLE"
  },
  "runtime_resolution_procedure": [
    "Parse the declared Day-1 seed or deterministic rule into the declared type.",
    "Validate against the reference range and structural constraint.",
    "Apply the declared bounded edit/search law; reject any value outside it."
  ],
  "source_line_end": 12341,
  "source_line_start": 12330,
  "step12_primary_tranche_id": "ST12-TRANCHE-A"
},
{
  "canonical_owner": "QKUComputationControlPlaneV1",
  "certified_step11_custody_ref": "inputs/certified_step11/QTT_Stage1_Step11_Parameter_Policy_Adjudication_v1_0.jsonl#ST11-PARAM::00440",
  "certified_step11_row_embedded_in_prompt": false,
  "codex_online_research_allowed": false,
  "direct_source_claim_justifications": [],
  "effective_bounded_search_space_or_fit_constraint": "fixed symbolic rule only; may not be weakened in the active edition",
  "effective_day1_seed_value_or_resolution_rule": "NO_SINGLE_EXECUTION_ADAPTER_MAY_MONOPOLIZE_POST_TRADE_RECONCILIATION_TRUTH",
  "effective_default_authority_class": "EXPLICIT_QTT_OR_OWNER_POLICY_SEED_OR_RESOLUTION_RULE",
  "effective_fallback_behavior_when_value_unavailable": "FAIL_CLOSED_TO_REGISTERED_LOWER_SAFE_PATH_OR_NO_TRADE",
  "effective_owner_dashboard_editability_class": "READ_ONLY_SYMBOLIC",
  "effective_policy_authority": "CERTIFIED_STEP11_PARAMETER_POLICY",
  "effective_reference_range_or_structural_constraint": "{NO_SINGLE_EXECUTION_ADAPTER_MAY_MONOPOLIZE_POST_TRADE_RECONCILIATION_TRUTH}",
  "effective_resolution_class": "STATIC_RULE",
  "effective_source_state_refs": [
    "OWNER_POLICY::D3_3C0",
    "SOURCE_PACK::D3_3C0"
  ],
  "effective_ui_widget_class": "FORMULA_BADGE",
  "effective_unit_or_basis": "execution-adapter-monopoly prohibition rule",
  "effective_value_source_class": "QTT_EXECUTION_ADAPTER_MONOPOLY_RULE",
  "evidence_basis_class": "FAMILY_SOURCE_PACK_PLUS_EXACT_OWNER_APPROVED_VALUE",
  "evidence_binding_rule_refs": [],
  "family_evidence_binding_ref": "ST12-FAMILY-EVIDENCE::D3_3C0",
  "implementation_resolution_kind": "STATIC_OR_DETERMINISTIC_RULE",
  "launch_computability_state": "COMPUTABLE_FROM_STATIC_VALUE_OR_DETERMINISTIC_RULE",
  "master_plan_heading_path": [
    "Part II — Retained institutional design and parameter catalog",
    "D3. Operating architecture",
    "D3.3C0 Shadow-book and external-statement reconciliation atomic parameter and control specification"
  ],
  "master_plan_section_id": "D3.3C0",
  "missing_stale_invalid_behavior": "REJECT_INVALID_VALUE_NO_SILENT_DEFAULT",
  "parameter_audit_id": "ST11-PARAM::00440",
  "parameter_id": "ST10-PARAM::0440",
  "parameter_symbol": "rule_exec_monopoly",
  "precision_and_rounding_policy": {
    "allowlist_check": "REQUIRED",
    "internal_numeric_type": "typed_symbolic",
    "normalization": "CANONICAL_EXACT_TOKEN_NO_FREE_TEXT_COERCION",
    "rounding": "NOT_APPLICABLE"
  },
  "runtime_resolution_procedure": [
    "Parse the declared Day-1 seed or deterministic rule into the declared type.",
    "Validate against the reference range and structural constraint.",
    "Apply the declared bounded edit/search law; reject any value outside it."
  ],
  "source_line_end": 12440,
  "source_line_start": 12426,
  "step12_primary_tranche_id": "ST12-TRANCHE-A"
},
{
  "canonical_owner": "QKUComputationControlPlaneV1",
  "certified_step11_custody_ref": "inputs/certified_step11/QTT_Stage1_Step11_Parameter_Policy_Adjudication_v1_0.jsonl#ST11-PARAM::00441",
  "certified_step11_row_embedded_in_prompt": false,
  "codex_online_research_allowed": false,
  "direct_source_claim_justifications": [],
  "effective_bounded_search_space_or_fit_constraint": "fixed symbolic law only; may not be weakened in the active edition",
  "effective_day1_seed_value_or_resolution_rule": "REPOSITORY_TRUTH_AND_DEPLOYMENT_TRUTH_SEPARATE_BUT_BOUND",
  "effective_default_authority_class": "EXPLICIT_QTT_OR_OWNER_POLICY_SEED_OR_RESOLUTION_RULE",
  "effective_fallback_behavior_when_value_unavailable": "FAIL_CLOSED_TO_REGISTERED_LOWER_SAFE_PATH_OR_NO_TRADE",
  "effective_owner_dashboard_editability_class": "READ_ONLY_SYMBOLIC",
  "effective_policy_authority": "CERTIFIED_STEP11_PARAMETER_POLICY",
  "effective_reference_range_or_structural_constraint": "{REPOSITORY_TRUTH_AND_DEPLOYMENT_TRUTH_SEPARATE_BUT_BOUND}",
  "effective_resolution_class": "STATIC_ENUM",
  "effective_source_state_refs": [
    "OWNER_POLICY::D3_11_4D",
    "SOURCE_PACK::D3_11_4D"
  ],
  "effective_ui_widget_class": "FORMULA_BADGE",
  "effective_unit_or_basis": "repository-versus-deployment-truth law",
  "effective_value_source_class": "QTT_DEPLOYMENT_CONTROL_LAW",
  "evidence_basis_class": "FAMILY_SOURCE_PACK_PLUS_EXACT_OWNER_APPROVED_VALUE",
  "evidence_binding_rule_refs": [],
  "family_evidence_binding_ref": "ST12-FAMILY-EVIDENCE::D3_11_4D",
  "implementation_resolution_kind": "STATIC_OR_DETERMINISTIC_RULE",
  "launch_computability_state": "COMPUTABLE_FROM_STATIC_VALUE_OR_DETERMINISTIC_RULE",
  "master_plan_heading_path": [
    "Part II — Retained institutional design and parameter catalog",
    "D3. Operating architecture",
    "D3.11 Deployment Manifests and Codex Override Files",
    "D3.11.4D Deployment control-plane, host-identity, and service-placement atomic parameter and control specification"
  ],
  "master_plan_section_id": "D3.11.4D",
  "missing_stale_invalid_behavior": "REJECT_INVALID_VALUE_NO_SILENT_DEFAULT",
  "parameter_audit_id": "ST11-PARAM::00441",
  "parameter_id": "ST10-PARAM::0441",
  "parameter_symbol": "repo_dep_sep",
  "precision_and_rounding_policy": {
    "allowlist_check": "REQUIRED",
    "internal_numeric_type": "typed_symbolic",
    "normalization": "CANONICAL_EXACT_TOKEN_NO_FREE_TEXT_COERCION",
    "rounding": "NOT_APPLICABLE"
  },
  "runtime_resolution_procedure": [
    "Parse the declared Day-1 seed or deterministic rule into the declared type.",
    "Validate against the reference range and structural constraint.",
    "Apply the declared bounded edit/search law; reject any value outside it."
  ],
  "source_line_end": 18078,
  "source_line_start": 18067,
  "step12_primary_tranche_id": "ST12-TRANCHE-A"
},
{
  "canonical_owner": "QKUComputationControlPlaneV1",
  "certified_step11_custody_ref": "inputs/certified_step11/QTT_Stage1_Step11_Parameter_Policy_Adjudication_v1_0.jsonl#ST11-PARAM::00442",
  "certified_step11_row_embedded_in_prompt": false,
  "codex_online_research_allowed": false,
  "direct_source_claim_justifications": [],
  "effective_bounded_search_space_or_fit_constraint": "fixed symbolic law only; may not be weakened in the active edition",
  "effective_day1_seed_value_or_resolution_rule": "QTT_HOST_DEPLOYMENT_LAYER_NOT_GITHUB_OR_CODEX",
  "effective_default_authority_class": "EXPLICIT_QTT_OR_OWNER_POLICY_SEED_OR_RESOLUTION_RULE",
  "effective_fallback_behavior_when_value_unavailable": "FAIL_CLOSED_TO_REGISTERED_LOWER_SAFE_PATH_OR_NO_TRADE",
  "effective_owner_dashboard_editability_class": "READ_ONLY_SYMBOLIC",
  "effective_policy_authority": "CERTIFIED_STEP11_PARAMETER_POLICY",
  "effective_reference_range_or_structural_constraint": "{QTT_HOST_DEPLOYMENT_LAYER_NOT_GITHUB_OR_CODEX}",
  "effective_resolution_class": "STATIC_ENUM",
  "effective_source_state_refs": [
    "OWNER_POLICY::D3_11_4D",
    "SOURCE_PACK::D3_11_4D"
  ],
  "effective_ui_widget_class": "FORMULA_BADGE",
  "effective_unit_or_basis": "runtime-control-plane law",
  "effective_value_source_class": "QTT_RUNTIME_CONTROL_PLANE_LAW",
  "evidence_basis_class": "FAMILY_SOURCE_PACK_PLUS_EXACT_OWNER_APPROVED_VALUE",
  "evidence_binding_rule_refs": [],
  "family_evidence_binding_ref": "ST12-FAMILY-EVIDENCE::D3_11_4D",
  "implementation_resolution_kind": "STATIC_OR_DETERMINISTIC_RULE",
  "launch_computability_state": "COMPUTABLE_FROM_STATIC_VALUE_OR_DETERMINISTIC_RULE",
  "master_plan_heading_path": [
    "Part II — Retained institutional design and parameter catalog",
    "D3. Operating architecture",
    "D3.11 Deployment Manifests and Codex Override Files",
    "D3.11.4D Deployment control-plane, host-identity, and service-placement atomic parameter and control specification"
  ],
  "master_plan_section_id": "D3.11.4D",
  "missing_stale_invalid_behavior": "REJECT_INVALID_VALUE_NO_SILENT_DEFAULT",
  "parameter_audit_id": "ST11-PARAM::00442",
  "parameter_id": "ST10-PARAM::0442",
  "parameter_symbol": "ctrl_plane",
  "precision_and_rounding_policy": {
    "allowlist_check": "REQUIRED",
    "internal_numeric_type": "typed_symbolic",
    "normalization": "CANONICAL_EXACT_TOKEN_NO_FREE_TEXT_COERCION",
    "rounding": "NOT_APPLICABLE"
  },
  "runtime_resolution_procedure": [
    "Parse the declared Day-1 seed or deterministic rule into the declared type.",
    "Validate against the reference range and structural constraint.",
    "Apply the declared bounded edit/search law; reject any value outside it."
  ],
  "source_line_end": 18090,
  "source_line_start": 18079,
  "step12_primary_tranche_id": "ST12-TRANCHE-A"
},
{
  "canonical_owner": "QKUComputationControlPlaneV1",
  "certified_step11_custody_ref": "inputs/certified_step11/QTT_Stage1_Step11_Parameter_Policy_Adjudication_v1_0.jsonl#ST11-PARAM::00443",
  "certified_step11_row_embedded_in_prompt": false,
  "codex_online_research_allowed": false,
  "direct_source_claim_justifications": [],
  "effective_bounded_search_space_or_fit_constraint": "host placement may not be inferred from ad hoc filenames or casual prose",
  "effective_day1_seed_value_or_resolution_rule": "HOST_ROLE_ID_PLUS_ALIAS_REGISTRY_REQUIRED",
  "effective_default_authority_class": "EXPLICIT_QTT_OR_OWNER_POLICY_SEED_OR_RESOLUTION_RULE",
  "effective_fallback_behavior_when_value_unavailable": "FAIL_CLOSED_TO_REGISTERED_LOWER_SAFE_PATH_OR_NO_TRADE",
  "effective_owner_dashboard_editability_class": "READ_ONLY_SYMBOLIC",
  "effective_policy_authority": "CERTIFIED_STEP11_PARAMETER_POLICY",
  "effective_reference_range_or_structural_constraint": "{HOST_ROLE_ID_PLUS_ALIAS_REGISTRY_REQUIRED}",
  "effective_resolution_class": "STATIC_ENUM",
  "effective_source_state_refs": [
    "OWNER_POLICY::D3_11_4D",
    "SOURCE_PACK::D3_11_4D"
  ],
  "effective_ui_widget_class": "FORMULA_BADGE",
  "effective_unit_or_basis": "host-identity law",
  "effective_value_source_class": "QTT_HOST_IDENTITY_LAW",
  "evidence_basis_class": "FAMILY_SOURCE_PACK_PLUS_EXACT_OWNER_APPROVED_VALUE",
  "evidence_binding_rule_refs": [],
  "family_evidence_binding_ref": "ST12-FAMILY-EVIDENCE::D3_11_4D",
  "implementation_resolution_kind": "STATIC_OR_DETERMINISTIC_RULE",
  "launch_computability_state": "COMPUTABLE_FROM_STATIC_VALUE_OR_DETERMINISTIC_RULE",
  "master_plan_heading_path": [
    "Part II — Retained institutional design and parameter catalog",
    "D3. Operating architecture",
    "D3.11 Deployment Manifests and Codex Override Files",
    "D3.11.4D Deployment control-plane, host-identity, and service-placement atomic parameter and control specification"
  ],
  "master_plan_section_id": "D3.11.4D",
  "missing_stale_invalid_behavior": "REJECT_INVALID_VALUE_NO_SILENT_DEFAULT",
  "parameter_audit_id": "ST11-PARAM::00443",
  "parameter_id": "ST10-PARAM::0443",
  "parameter_symbol": "host_id_mode",
  "precision_and_rounding_policy": {
    "allowlist_check": "REQUIRED",
    "internal_numeric_type": "typed_symbolic",
    "normalization": "CANONICAL_EXACT_TOKEN_NO_FREE_TEXT_COERCION",
    "rounding": "NOT_APPLICABLE"
  },
  "runtime_resolution_procedure": [
    "Parse the declared Day-1 seed or deterministic rule into the declared type.",
    "Validate against the reference range and structural constraint.",
    "Apply the declared bounded edit/search law; reject any value outside it."
  ],
  "source_line_end": 18102,
  "source_line_start": 18091,
  "step12_primary_tranche_id": "ST12-TRANCHE-A"
},
{
  "canonical_owner": "QKUComputationControlPlaneV1",
  "certified_step11_custody_ref": "inputs/certified_step11/QTT_Stage1_Step11_Parameter_Policy_Adjudication_v1_0.jsonl#ST11-PARAM::00445",
  "certified_step11_row_embedded_in_prompt": false,
  "codex_online_research_allowed": false,
  "direct_source_claim_justifications": [],
  "effective_bounded_search_space_or_fit_constraint": "alias files may exist only when they resolve back to the primary manifest path",
  "effective_day1_seed_value_or_resolution_rule": "PRIMARY_FILENAMES_PLUS_ALIAS_MAP_NO_SECOND_AUTHORITY",
  "effective_default_authority_class": "EXPLICIT_QTT_OR_OWNER_POLICY_SEED_OR_RESOLUTION_RULE",
  "effective_fallback_behavior_when_value_unavailable": "FAIL_CLOSED_TO_REGISTERED_LOWER_SAFE_PATH_OR_NO_TRADE",
  "effective_owner_dashboard_editability_class": "READ_ONLY_SYMBOLIC",
  "effective_policy_authority": "CERTIFIED_STEP11_PARAMETER_POLICY",
  "effective_reference_range_or_structural_constraint": "{PRIMARY_FILENAMES_PLUS_ALIAS_MAP_NO_SECOND_AUTHORITY}",
  "effective_resolution_class": "STATIC_ENUM",
  "effective_source_state_refs": [
    "OWNER_POLICY::D3_11_4D",
    "SOURCE_PACK::D3_11_4D"
  ],
  "effective_ui_widget_class": "FORMULA_BADGE",
  "effective_unit_or_basis": "host-alias policy",
  "effective_value_source_class": "QTT_ALIAS_CONTINUITY_RULE",
  "evidence_basis_class": "FAMILY_SOURCE_PACK_PLUS_EXACT_OWNER_APPROVED_VALUE",
  "evidence_binding_rule_refs": [],
  "family_evidence_binding_ref": "ST12-FAMILY-EVIDENCE::D3_11_4D",
  "implementation_resolution_kind": "STATIC_OR_DETERMINISTIC_RULE",
  "launch_computability_state": "COMPUTABLE_FROM_STATIC_VALUE_OR_DETERMINISTIC_RULE",
  "master_plan_heading_path": [
    "Part II — Retained institutional design and parameter catalog",
    "D3. Operating architecture",
    "D3.11 Deployment Manifests and Codex Override Files",
    "D3.11.4D Deployment control-plane, host-identity, and service-placement atomic parameter and control specification"
  ],
  "master_plan_section_id": "D3.11.4D",
  "missing_stale_invalid_behavior": "REJECT_INVALID_VALUE_NO_SILENT_DEFAULT",
  "parameter_audit_id": "ST11-PARAM::00445",
  "parameter_id": "ST10-PARAM::0445",
  "parameter_symbol": "host_alias",
  "precision_and_rounding_policy": {
    "allowlist_check": "REQUIRED",
    "internal_numeric_type": "typed_symbolic",
    "normalization": "CANONICAL_EXACT_TOKEN_NO_FREE_TEXT_COERCION",
    "rounding": "NOT_APPLICABLE"
  },
  "runtime_resolution_procedure": [
    "Parse the declared Day-1 seed or deterministic rule into the declared type.",
    "Validate against the reference range and structural constraint.",
    "Apply the declared bounded edit/search law; reject any value outside it."
  ],
  "source_line_end": 18126,
  "source_line_start": 18115,
  "step12_primary_tranche_id": "ST12-TRANCHE-A"
},
{
  "canonical_owner": "QKUComputationControlPlaneV1",
  "certified_step11_custody_ref": "inputs/certified_step11/QTT_Stage1_Step11_Parameter_Policy_Adjudication_v1_0.jsonl#ST11-PARAM::00446",
  "certified_step11_row_embedded_in_prompt": false,
  "codex_online_research_allowed": false,
  "direct_source_claim_justifications": [],
  "effective_bounded_search_space_or_fit_constraint": "materially used services may not rely on placement folklore or ad hoc shell notes",
  "effective_day1_seed_value_or_resolution_rule": "EVERY_MATERIAL_SERVICE_REQUIRES_DEPLOYMENT_PROFILE",
  "effective_default_authority_class": "EXPLICIT_QTT_OR_OWNER_POLICY_SEED_OR_RESOLUTION_RULE",
  "effective_fallback_behavior_when_value_unavailable": "FAIL_CLOSED_TO_REGISTERED_LOWER_SAFE_PATH_OR_NO_TRADE",
  "effective_owner_dashboard_editability_class": "READ_ONLY_SYMBOLIC",
  "effective_policy_authority": "CERTIFIED_STEP11_PARAMETER_POLICY",
  "effective_reference_range_or_structural_constraint": "{EVERY_MATERIAL_SERVICE_REQUIRES_DEPLOYMENT_PROFILE}",
  "effective_resolution_class": "STATIC_ENUM",
  "effective_source_state_refs": [
    "OWNER_POLICY::D3_11_4D",
    "SOURCE_PACK::D3_11_4D"
  ],
  "effective_ui_widget_class": "FORMULA_BADGE",
  "effective_unit_or_basis": "service-profile requirement",
  "effective_value_source_class": "QTT_SERVICE_DEPLOYMENT_PROFILE_LAW",
  "evidence_basis_class": "FAMILY_SOURCE_PACK_PLUS_EXACT_OWNER_APPROVED_VALUE",
  "evidence_binding_rule_refs": [],
  "family_evidence_binding_ref": "ST12-FAMILY-EVIDENCE::D3_11_4D",
  "implementation_resolution_kind": "STATIC_OR_DETERMINISTIC_RULE",
  "launch_computability_state": "COMPUTABLE_FROM_STATIC_VALUE_OR_DETERMINISTIC_RULE",
  "master_plan_heading_path": [
    "Part II — Retained institutional design and parameter catalog",
    "D3. Operating architecture",
    "D3.11 Deployment Manifests and Codex Override Files",
    "D3.11.4D Deployment control-plane, host-identity, and service-placement atomic parameter and control specification"
  ],
  "master_plan_section_id": "D3.11.4D",
  "missing_stale_invalid_behavior": "REJECT_INVALID_VALUE_NO_SILENT_DEFAULT",
  "parameter_audit_id": "ST11-PARAM::00446",
  "parameter_id": "ST10-PARAM::0446",
  "parameter_symbol": "svc_profile_req",
  "precision_and_rounding_policy": {
    "allowlist_check": "REQUIRED",
    "internal_numeric_type": "typed_symbolic",
    "normalization": "CANONICAL_EXACT_TOKEN_NO_FREE_TEXT_COERCION",
    "rounding": "NOT_APPLICABLE"
  },
  "runtime_resolution_procedure": [
    "Parse the declared Day-1 seed or deterministic rule into the declared type.",
    "Validate against the reference range and structural constraint.",
    "Apply the declared bounded edit/search law; reject any value outside it."
  ],
  "source_line_end": 18138,
  "source_line_start": 18127,
  "step12_primary_tranche_id": "ST12-TRANCHE-A"
},
{
  "canonical_owner": "QKUComputationControlPlaneV1",
  "certified_step11_custody_ref": "inputs/certified_step11/QTT_Stage1_Step11_Parameter_Policy_Adjudication_v1_0.jsonl#ST11-PARAM::00447",
  "certified_step11_row_embedded_in_prompt": false,
  "codex_online_research_allowed": false,
  "direct_source_claim_justifications": [],
  "effective_bounded_search_space_or_fit_constraint": "no service may silently widen host scope beyond the declared set",
  "effective_day1_seed_value_or_resolution_rule": "DECLARED_ALLOWED_HOST_ROLE_SET_REQUIRED",
  "effective_default_authority_class": "EXPLICIT_QTT_OR_OWNER_POLICY_SEED_OR_RESOLUTION_RULE",
  "effective_fallback_behavior_when_value_unavailable": "FAIL_CLOSED_TO_REGISTERED_LOWER_SAFE_PATH_OR_NO_TRADE",
  "effective_owner_dashboard_editability_class": "READ_ONLY_SYMBOLIC",
  "effective_policy_authority": "CERTIFIED_STEP11_PARAMETER_POLICY",
  "effective_reference_range_or_structural_constraint": "{DECLARED_ALLOWED_HOST_ROLE_SET_REQUIRED}",
  "effective_resolution_class": "STATIC_ENUM",
  "effective_source_state_refs": [
    "OWNER_POLICY::D3_11_4D",
    "SOURCE_PACK::D3_11_4D"
  ],
  "effective_ui_widget_class": "FORMULA_BADGE",
  "effective_unit_or_basis": "allowed-host-role rule",
  "effective_value_source_class": "QTT_SERVICE_HOST_SCOPE_RULE",
  "evidence_basis_class": "FAMILY_SOURCE_PACK_PLUS_EXACT_OWNER_APPROVED_VALUE",
  "evidence_binding_rule_refs": [],
  "family_evidence_binding_ref": "ST12-FAMILY-EVIDENCE::D3_11_4D",
  "implementation_resolution_kind": "STATIC_OR_DETERMINISTIC_RULE",
  "launch_computability_state": "COMPUTABLE_FROM_STATIC_VALUE_OR_DETERMINISTIC_RULE",
  "master_plan_heading_path": [
    "Part II — Retained institutional design and parameter catalog",
    "D3. Operating architecture",
    "D3.11 Deployment Manifests and Codex Override Files",
    "D3.11.4D Deployment control-plane, host-identity, and service-placement atomic parameter and control specification"
  ],
  "master_plan_section_id": "D3.11.4D",
  "missing_stale_invalid_behavior": "REJECT_INVALID_VALUE_NO_SILENT_DEFAULT",
  "parameter_audit_id": "ST11-PARAM::00447",
  "parameter_id": "ST10-PARAM::0447",
  "parameter_symbol": "svc_host_rule",
  "precision_and_rounding_policy": {
    "allowlist_check": "REQUIRED",
    "internal_numeric_type": "typed_symbolic",
    "normalization": "CANONICAL_EXACT_TOKEN_NO_FREE_TEXT_COERCION",
    "rounding": "NOT_APPLICABLE"
  },
  "runtime_resolution_procedure": [
    "Parse the declared Day-1 seed or deterministic rule into the declared type.",
    "Validate against the reference range and structural constraint.",
    "Apply the declared bounded edit/search law; reject any value outside it."
  ],
  "source_line_end": 18150,
  "source_line_start": 18139,
  "step12_primary_tranche_id": "ST12-TRANCHE-A"
},
{
  "canonical_owner": "QKUComputationControlPlaneV1",
  "certified_step11_custody_ref": "inputs/certified_step11/QTT_Stage1_Step11_Parameter_Policy_Adjudication_v1_0.jsonl#ST11-PARAM::00448",
  "certified_step11_row_embedded_in_prompt": false,
  "codex_online_research_allowed": false,
  "direct_source_claim_justifications": [],
  "effective_bounded_search_space_or_fit_constraint": "runtime cross-host dependency may not be reconstructed from code comments or ad hoc orchestration",
  "effective_day1_seed_value_or_resolution_rule": "DECLARED_ARTIFACT_DEPENDENCIES_ONLY_NO_HIDDEN_CLUSTER_DEPENDENCY",
  "effective_default_authority_class": "EXPLICIT_QTT_OR_OWNER_POLICY_SEED_OR_RESOLUTION_RULE",
  "effective_fallback_behavior_when_value_unavailable": "FAIL_CLOSED_TO_REGISTERED_LOWER_SAFE_PATH_OR_NO_TRADE",
  "effective_owner_dashboard_editability_class": "READ_ONLY_SYMBOLIC",
  "effective_policy_authority": "CERTIFIED_STEP11_PARAMETER_POLICY",
  "effective_reference_range_or_structural_constraint": "{DECLARED_ARTIFACT_DEPENDENCIES_ONLY_NO_HIDDEN_CLUSTER_DEPENDENCY}",
  "effective_resolution_class": "STATIC_ENUM",
  "effective_source_state_refs": [
    "OWNER_POLICY::D3_11_4D",
    "SOURCE_PACK::D3_11_4D"
  ],
  "effective_ui_widget_class": "FORMULA_BADGE",
  "effective_unit_or_basis": "service-artifact-dependency rule",
  "effective_value_source_class": "QTT_ARTIFACT_DEPENDENCY_RULE",
  "evidence_basis_class": "FAMILY_SOURCE_PACK_PLUS_EXACT_OWNER_APPROVED_VALUE",
  "evidence_binding_rule_refs": [],
  "family_evidence_binding_ref": "ST12-FAMILY-EVIDENCE::D3_11_4D",
  "implementation_resolution_kind": "STATIC_OR_DETERMINISTIC_RULE",
  "launch_computability_state": "COMPUTABLE_FROM_STATIC_VALUE_OR_DETERMINISTIC_RULE",
  "master_plan_heading_path": [
    "Part II — Retained institutional design and parameter catalog",
    "D3. Operating architecture",
    "D3.11 Deployment Manifests and Codex Override Files",
    "D3.11.4D Deployment control-plane, host-identity, and service-placement atomic parameter and control specification"
  ],
  "master_plan_section_id": "D3.11.4D",
  "missing_stale_invalid_behavior": "REJECT_INVALID_VALUE_NO_SILENT_DEFAULT",
  "parameter_audit_id": "ST11-PARAM::00448",
  "parameter_id": "ST10-PARAM::0448",
  "parameter_symbol": "svc_art_dep",
  "precision_and_rounding_policy": {
    "allowlist_check": "REQUIRED",
    "internal_numeric_type": "typed_symbolic",
    "normalization": "CANONICAL_EXACT_TOKEN_NO_FREE_TEXT_COERCION",
    "rounding": "NOT_APPLICABLE"
  },
  "runtime_resolution_procedure": [
    "Parse the declared Day-1 seed or deterministic rule into the declared type.",
    "Validate against the reference range and structural constraint.",
    "Apply the declared bounded edit/search law; reject any value outside it."
  ],
  "source_line_end": 18162,
  "source_line_start": 18151,
  "step12_primary_tranche_id": "ST12-TRANCHE-A"
},
{
  "canonical_owner": "QKUComputationControlPlaneV1",
  "certified_step11_custody_ref": "inputs/certified_step11/QTT_Stage1_Step11_Parameter_Policy_Adjudication_v1_0.jsonl#ST11-PARAM::00452",
  "certified_step11_row_embedded_in_prompt": false,
  "codex_online_research_allowed": false,
  "direct_source_claim_justifications": [],
  "effective_bounded_search_space_or_fit_constraint": "Wave 1 may not silently convert three-venue canary eligibility into live execution before each declared per-venue gate is green",
  "effective_day1_seed_value_or_resolution_rule": "THREE_VENUE_STAGE1_CORE_BUILD_WITH_SEPARATE_PER_VENUE_GATES",
  "effective_default_authority_class": "EXPLICIT_QTT_OR_OWNER_POLICY_SEED_OR_RESOLUTION_RULE",
  "effective_fallback_behavior_when_value_unavailable": "FAIL_CLOSED_TO_REGISTERED_LOWER_SAFE_PATH_OR_NO_TRADE",
  "effective_owner_dashboard_editability_class": "READ_ONLY_SYMBOLIC",
  "effective_policy_authority": "CERTIFIED_STEP11_PARAMETER_POLICY",
  "effective_reference_range_or_structural_constraint": "{THREE_VENUE_STAGE1_CORE_BUILD_WITH_SEPARATE_PER_VENUE_GATES}",
  "effective_resolution_class": "STATIC_ENUM",
  "effective_source_state_refs": [
    "OWNER_POLICY::D3_11_4D",
    "SOURCE_PACK::D3_11_4D"
  ],
  "effective_ui_widget_class": "FORMULA_BADGE",
  "effective_unit_or_basis": "Wave-1 build family",
  "effective_value_source_class": "QTT_STAGED_BUILD_MANIFEST_RULE",
  "evidence_basis_class": "FAMILY_SOURCE_PACK_PLUS_EXACT_OWNER_APPROVED_VALUE",
  "evidence_binding_rule_refs": [],
  "family_evidence_binding_ref": "ST12-FAMILY-EVIDENCE::D3_11_4D",
  "implementation_resolution_kind": "STATIC_OR_DETERMINISTIC_RULE",
  "launch_computability_state": "COMPUTABLE_FROM_STATIC_VALUE_OR_DETERMINISTIC_RULE",
  "master_plan_heading_path": [
    "Part II — Retained institutional design and parameter catalog",
    "D3. Operating architecture",
    "D3.11 Deployment Manifests and Codex Override Files",
    "D3.11.4D Deployment control-plane, host-identity, and service-placement atomic parameter and control specification"
  ],
  "master_plan_section_id": "D3.11.4D",
  "missing_stale_invalid_behavior": "REJECT_INVALID_VALUE_NO_SILENT_DEFAULT",
  "parameter_audit_id": "ST11-PARAM::00452",
  "parameter_id": "ST10-PARAM::0452",
  "parameter_symbol": "wave_build",
  "precision_and_rounding_policy": {
    "allowlist_check": "REQUIRED",
    "internal_numeric_type": "typed_symbolic",
    "normalization": "CANONICAL_EXACT_TOKEN_NO_FREE_TEXT_COERCION",
    "rounding": "NOT_APPLICABLE"
  },
  "runtime_resolution_procedure": [
    "Parse the declared Day-1 seed or deterministic rule into the declared type.",
    "Validate against the reference range and structural constraint.",
    "Apply the declared bounded edit/search law; reject any value outside it."
  ],
  "source_line_end": 18210,
  "source_line_start": 18199,
  "step12_primary_tranche_id": "ST12-TRANCHE-A"
},
{
  "canonical_owner": "QKUComputationControlPlaneV1",
  "certified_step11_custody_ref": "inputs/certified_step11/QTT_Stage1_Step11_Parameter_Policy_Adjudication_v1_0.jsonl#ST11-PARAM::00453",
  "certified_step11_row_embedded_in_prompt": false,
  "codex_online_research_allowed": false,
  "direct_source_claim_justifications": [],
  "effective_bounded_search_space_or_fit_constraint": "dormant connector scaffold availability may not be misread as live-enablement permission",
  "effective_day1_seed_value_or_resolution_rule": "POLYMARKET_V2_SCAFFOLDED_DISABLED_AND_NONLIVE_UNTIL_KALSHI_STABLE_AND_OWNER_ENABLED",
  "effective_default_authority_class": "EXPLICIT_QTT_OR_OWNER_POLICY_SEED_OR_RESOLUTION_RULE",
  "effective_fallback_behavior_when_value_unavailable": "FAIL_CLOSED_TO_REGISTERED_LOWER_SAFE_PATH_OR_NO_TRADE",
  "effective_owner_dashboard_editability_class": "READ_ONLY_SYMBOLIC",
  "effective_policy_authority": "CERTIFIED_STEP11_PARAMETER_POLICY",
  "effective_reference_range_or_structural_constraint": "{POLYMARKET_V2_SCAFFOLDED_DISABLED_AND_NONLIVE_UNTIL_KALSHI_STABLE_AND_OWNER_ENABLED}",
  "effective_resolution_class": "STATIC_ENUM",
  "effective_source_state_refs": [
    "OWNER_POLICY::D3_11_4D",
    "SOURCE_PACK::D3_11_4D"
  ],
  "effective_ui_widget_class": "FORMULA_BADGE",
  "effective_unit_or_basis": "next-venue connector state",
  "effective_value_source_class": "QTT_NEXT_VENUE_DORMANT_CONNECTOR_RULE",
  "evidence_basis_class": "FAMILY_SOURCE_PACK_PLUS_EXACT_OWNER_APPROVED_VALUE",
  "evidence_binding_rule_refs": [],
  "family_evidence_binding_ref": "ST12-FAMILY-EVIDENCE::D3_11_4D",
  "implementation_resolution_kind": "EXPLICIT_FAIL_CLOSED_POLICY",
  "launch_computability_state": "COMPUTABLE_TYPED_FAIL_CLOSED_OR_NO_TRADE_STATE",
  "master_plan_heading_path": [
    "Part II — Retained institutional design and parameter catalog",
    "D3. Operating architecture",
    "D3.11 Deployment Manifests and Codex Override Files",
    "D3.11.4D Deployment control-plane, host-identity, and service-placement atomic parameter and control specification"
  ],
  "master_plan_section_id": "D3.11.4D",
  "missing_stale_invalid_behavior": "PRESERVE_EXPLICIT_FAIL_CLOSED_STATE",
  "parameter_audit_id": "ST11-PARAM::00453",
  "parameter_id": "ST10-PARAM::0453",
  "parameter_symbol": "next_venue_state",
  "precision_and_rounding_policy": {
    "allowlist_check": "REQUIRED",
    "internal_numeric_type": "typed_symbolic",
    "normalization": "CANONICAL_EXACT_TOKEN_NO_FREE_TEXT_COERCION",
    "rounding": "NOT_APPLICABLE"
  },
  "runtime_resolution_procedure": [
    "Materialize the declared fail-closed state exactly.",
    "Return a typed blocker/no-trade status and do not substitute a numeric fallback.",
    "Validate the resolved typed value or token against the effective resolution class, declared structural constraint, and canonical allowlist; on failure apply the declared fail-closed fallback and emit the exact reason code."
  ],
  "source_line_end": 18225,
  "source_line_start": 18211,
  "step12_primary_tranche_id": "ST12-TRANCHE-A"
},
{
  "canonical_owner": "QKUComputationControlPlaneV1",
  "certified_step11_custody_ref": "inputs/certified_step11/QTT_Stage1_Step11_Parameter_Policy_Adjudication_v1_0.jsonl#ST11-PARAM::00454",
  "certified_step11_row_embedded_in_prompt": false,
  "codex_online_research_allowed": false,
  "direct_source_claim_justifications": [],
  "effective_bounded_search_space_or_fit_constraint": "automatic backup may not self-arm before the owner-approved backup policy is green",
  "effective_day1_seed_value_or_resolution_rule": "OWNER_APPROVED_AUTOMATIC_AFTER_POLICY_APPROVAL",
  "effective_default_authority_class": "EXPLICIT_QTT_OR_OWNER_POLICY_SEED_OR_RESOLUTION_RULE",
  "effective_fallback_behavior_when_value_unavailable": "FAIL_CLOSED_TO_REGISTERED_LOWER_SAFE_PATH_OR_NO_TRADE",
  "effective_owner_dashboard_editability_class": "EDITABLE_WITH_SHADOW",
  "effective_policy_authority": "CERTIFIED_STEP11_PARAMETER_POLICY",
  "effective_reference_range_or_structural_constraint": "{OWNER_APPROVED_AUTOMATIC_AFTER_POLICY_APPROVAL,MANUAL_ONLY_OWNER_APPROVED_WITHIN_HARD_GATES,DISABLED_UNTIL_APPROVED}",
  "effective_resolution_class": "STATIC_ENUM",
  "effective_source_state_refs": [
    "OWNER_POLICY::D3_11_7_10B",
    "SOURCE_PACK::D3_11_7_10B"
  ],
  "effective_ui_widget_class": "ENUM_DROPDOWN",
  "effective_unit_or_basis": "backup-activation-mode enum",
  "effective_value_source_class": "QTT_BACKUP_GOVERNANCE_RULE",
  "evidence_basis_class": "FAMILY_SOURCE_PACK_PLUS_EXACT_OWNER_APPROVED_VALUE",
  "evidence_binding_rule_refs": [],
  "family_evidence_binding_ref": "ST12-FAMILY-EVIDENCE::D3_11_7_10B",
  "implementation_resolution_kind": "STATIC_OR_DETERMINISTIC_RULE",
  "launch_computability_state": "COMPUTABLE_FROM_STATIC_VALUE_OR_DETERMINISTIC_RULE",
  "master_plan_heading_path": [
    "Part II — Retained institutional design and parameter catalog",
    "D3. Operating architecture",
    "D3.11 Deployment Manifests and Codex Override Files",
    "D3.11.7 Hands-off automation governance registry, stepped-autonomy maturity model, and optional translator role law",
    "D3.11.7.10B Automatic backup subsystem atomic parameter and control specification"
  ],
  "master_plan_section_id": "D3.11.7.10B",
  "missing_stale_invalid_behavior": "REJECT_INVALID_VALUE_NO_SILENT_DEFAULT",
  "parameter_audit_id": "ST11-PARAM::00454",
  "parameter_id": "ST10-PARAM::0454",
  "parameter_symbol": "bkp_mode",
  "precision_and_rounding_policy": {
    "allowlist_check": "REQUIRED",
    "internal_numeric_type": "typed_symbolic",
    "normalization": "CANONICAL_EXACT_TOKEN_NO_FREE_TEXT_COERCION",
    "rounding": "NOT_APPLICABLE"
  },
  "runtime_resolution_procedure": [
    "Parse the declared Day-1 seed or deterministic rule into the declared type.",
    "Validate against the reference range and structural constraint.",
    "Apply the declared bounded edit/search law; reject any value outside it."
  ],
  "source_line_end": 18849,
  "source_line_start": 18838,
  "step12_primary_tranche_id": "ST12-TRANCHE-A"
},
{
  "canonical_owner": "QKUComputationControlPlaneV1",
  "certified_step11_custody_ref": "inputs/certified_step11/QTT_Stage1_Step11_Parameter_Policy_Adjudication_v1_0.jsonl#ST11-PARAM::00455",
  "certified_step11_row_embedded_in_prompt": false,
  "codex_online_research_allowed": false,
  "direct_source_claim_justifications": [],
  "effective_bounded_search_space_or_fit_constraint": "materially valuable artifacts may not wait for weekly-only backup cadence",
  "effective_day1_seed_value_or_resolution_rule": "IMMEDIATE_MATERIAL_ARTIFACT_WRITE_PLUS_NIGHTLY_INCREMENTAL_PLUS_WEEKLY_FULL",
  "effective_default_authority_class": "EXPLICIT_QTT_OR_OWNER_POLICY_SEED_OR_RESOLUTION_RULE",
  "effective_fallback_behavior_when_value_unavailable": "FAIL_CLOSED_TO_REGISTERED_LOWER_SAFE_PATH_OR_NO_TRADE",
  "effective_owner_dashboard_editability_class": "EDITABLE_WITH_SHADOW",
  "effective_policy_authority": "CERTIFIED_STEP11_PARAMETER_POLICY",
  "effective_reference_range_or_structural_constraint": "{IMMEDIATE_MATERIAL_ARTIFACT_WRITE_PLUS_NIGHTLY_INCREMENTAL_PLUS_WEEKLY_FULL,IMMEDIATE_MATERIAL_ARTIFACT_WRITE_PLUS_HOURLY_INCREMENTAL_PLUS_DAILY_FULL,OWNER_CUSTOM_APPROVED}",
  "effective_resolution_class": "STATIC_ENUM",
  "effective_source_state_refs": [
    "OWNER_POLICY::D3_11_7_10B",
    "SOURCE_PACK::D3_11_7_10B"
  ],
  "effective_ui_widget_class": "ENUM_DROPDOWN",
  "effective_unit_or_basis": "cadence-family enum",
  "effective_value_source_class": "QTT_BACKUP_SCHEDULE_RULE",
  "evidence_basis_class": "FAMILY_SOURCE_PACK_PLUS_EXACT_OWNER_APPROVED_VALUE",
  "evidence_binding_rule_refs": [],
  "family_evidence_binding_ref": "ST12-FAMILY-EVIDENCE::D3_11_7_10B",
  "implementation_resolution_kind": "STATIC_OR_DETERMINISTIC_RULE",
  "launch_computability_state": "COMPUTABLE_FROM_STATIC_VALUE_OR_DETERMINISTIC_RULE",
  "master_plan_heading_path": [
    "Part II — Retained institutional design and parameter catalog",
    "D3. Operating architecture",
    "D3.11 Deployment Manifests and Codex Override Files",
    "D3.11.7 Hands-off automation governance registry, stepped-autonomy maturity model, and optional translator role law",
    "D3.11.7.10B Automatic backup subsystem atomic parameter and control specification"
  ],
  "master_plan_section_id": "D3.11.7.10B",
  "missing_stale_invalid_behavior": "REJECT_INVALID_VALUE_NO_SILENT_DEFAULT",
  "parameter_audit_id": "ST11-PARAM::00455",
  "parameter_id": "ST10-PARAM::0455",
  "parameter_symbol": "bkp_freq",
  "precision_and_rounding_policy": {
    "allowlist_check": "REQUIRED",
    "internal_numeric_type": "typed_symbolic",
    "normalization": "CANONICAL_EXACT_TOKEN_NO_FREE_TEXT_COERCION",
    "rounding": "NOT_APPLICABLE"
  },
  "runtime_resolution_procedure": [
    "Parse the declared Day-1 seed or deterministic rule into the declared type.",
    "Validate against the reference range and structural constraint.",
    "Apply the declared bounded edit/search law; reject any value outside it."
  ],
  "source_line_end": 18861,
  "source_line_start": 18850,
  "step12_primary_tranche_id": "ST12-TRANCHE-A"
},
{
  "canonical_owner": "QKUComputationControlPlaneV1",
  "certified_step11_custody_ref": "inputs/certified_step11/QTT_Stage1_Step11_Parameter_Policy_Adjudication_v1_0.jsonl#ST11-PARAM::00458",
  "certified_step11_row_embedded_in_prompt": false,
  "codex_online_research_allowed": false,
  "direct_source_claim_justifications": [],
  "effective_bounded_search_space_or_fit_constraint": "retention weakening may not silently delete restore points below the declared policy floor without owner edit",
  "effective_day1_seed_value_or_resolution_rule": "HOT_30_DAILY_PLUS_26_WEEKLY_PLUS_12_MONTHLY",
  "effective_default_authority_class": "EXPLICIT_QTT_OR_OWNER_POLICY_SEED_OR_RESOLUTION_RULE",
  "effective_fallback_behavior_when_value_unavailable": "FAIL_CLOSED_TO_REGISTERED_LOWER_SAFE_PATH_OR_NO_TRADE",
  "effective_owner_dashboard_editability_class": "EDITABLE_WITH_SHADOW",
  "effective_policy_authority": "CERTIFIED_STEP11_PARAMETER_POLICY",
  "effective_reference_range_or_structural_constraint": "{HOT_7_DAILY_PLUS_8_WEEKLY_PLUS_6_MONTHLY,HOT_30_DAILY_PLUS_26_WEEKLY_PLUS_12_MONTHLY,OWNER_CUSTOM_APPROVED}",
  "effective_resolution_class": "STATIC_ENUM",
  "effective_source_state_refs": [
    "OWNER_POLICY::D3_11_7_10B",
    "SOURCE_PACK::D3_11_7_10B"
  ],
  "effective_ui_widget_class": "RETENTION_POLICY_EDITOR",
  "effective_unit_or_basis": "retention-policy profile",
  "effective_value_source_class": "QTT_BACKUP_RETENTION_RULE",
  "evidence_basis_class": "FAMILY_SOURCE_PACK_PLUS_EXACT_OWNER_APPROVED_VALUE",
  "evidence_binding_rule_refs": [],
  "family_evidence_binding_ref": "ST12-FAMILY-EVIDENCE::D3_11_7_10B",
  "implementation_resolution_kind": "STATIC_OR_DETERMINISTIC_RULE",
  "launch_computability_state": "COMPUTABLE_FROM_STATIC_VALUE_OR_DETERMINISTIC_RULE",
  "master_plan_heading_path": [
    "Part II — Retained institutional design and parameter catalog",
    "D3. Operating architecture",
    "D3.11 Deployment Manifests and Codex Override Files",
    "D3.11.7 Hands-off automation governance registry, stepped-autonomy maturity model, and optional translator role law",
    "D3.11.7.10B Automatic backup subsystem atomic parameter and control specification"
  ],
  "master_plan_section_id": "D3.11.7.10B",
  "missing_stale_invalid_behavior": "REJECT_INVALID_VALUE_NO_SILENT_DEFAULT",
  "parameter_audit_id": "ST11-PARAM::00458",
  "parameter_id": "ST10-PARAM::0458",
  "parameter_symbol": "bkp_ret",
  "precision_and_rounding_policy": {
    "allowlist_check": "REQUIRED",
    "internal_numeric_type": "typed_symbolic",
    "normalization": "CANONICAL_EXACT_TOKEN_NO_FREE_TEXT_COERCION",
    "rounding": "NOT_APPLICABLE"
  },
  "runtime_resolution_procedure": [
    "Parse the declared Day-1 seed or deterministic rule into the declared type.",
    "Validate against the reference range and structural constraint.",
    "Apply the declared bounded edit/search law; reject any value outside it."
  ],
  "source_line_end": 18897,
  "source_line_start": 18886,
  "step12_primary_tranche_id": "ST12-TRANCHE-A"
},
{
  "canonical_owner": "QKUComputationControlPlaneV1",
  "certified_step11_custody_ref": "inputs/certified_step11/QTT_Stage1_Step11_Parameter_Policy_Adjudication_v1_0.jsonl#ST11-PARAM::00461",
  "certified_step11_row_embedded_in_prompt": false,
  "codex_online_research_allowed": false,
  "direct_source_claim_justifications": [],
  "effective_bounded_search_space_or_fit_constraint": "material archive bundles and secret-recovery exports may not be stored as plaintext when encrypted backup mode is active",
  "effective_day1_seed_value_or_resolution_rule": "AGE_ENCRYPTED_BACKUP_BUNDLE_PLUS_HASH_MANIFEST",
  "effective_default_authority_class": "EXPLICIT_QTT_OR_OWNER_POLICY_SEED_OR_RESOLUTION_RULE",
  "effective_fallback_behavior_when_value_unavailable": "FAIL_CLOSED_TO_REGISTERED_LOWER_SAFE_PATH_OR_NO_TRADE",
  "effective_owner_dashboard_editability_class": "EDITABLE_WITH_SHADOW",
  "effective_policy_authority": "CERTIFIED_STEP11_PARAMETER_POLICY",
  "effective_reference_range_or_structural_constraint": "{AGE_ENCRYPTED_BACKUP_BUNDLE_PLUS_HASH_MANIFEST,OWNER_APPROVED_EQUIVALENT}",
  "effective_resolution_class": "STATIC_ENUM",
  "effective_source_state_refs": [
    "OWNER_POLICY::D3_11_7_10B",
    "SOURCE_PACK::D3_11_7_10B"
  ],
  "effective_ui_widget_class": "ENUM_DROPDOWN",
  "effective_unit_or_basis": "encryption-mode enum",
  "effective_value_source_class": "QTT_BACKUP_ENCRYPTION_RULE",
  "evidence_basis_class": "FAMILY_SOURCE_PACK_PLUS_EXACT_OWNER_APPROVED_VALUE",
  "evidence_binding_rule_refs": [],
  "family_evidence_binding_ref": "ST12-FAMILY-EVIDENCE::D3_11_7_10B",
  "implementation_resolution_kind": "STATIC_OR_DETERMINISTIC_RULE",
  "launch_computability_state": "COMPUTABLE_FROM_STATIC_VALUE_OR_DETERMINISTIC_RULE",
  "master_plan_heading_path": [
    "Part II — Retained institutional design and parameter catalog",
    "D3. Operating architecture",
    "D3.11 Deployment Manifests and Codex Override Files",
    "D3.11.7 Hands-off automation governance registry, stepped-autonomy maturity model, and optional translator role law",
    "D3.11.7.10B Automatic backup subsystem atomic parameter and control specification"
  ],
  "master_plan_section_id": "D3.11.7.10B",
  "missing_stale_invalid_behavior": "REJECT_INVALID_VALUE_NO_SILENT_DEFAULT",
  "parameter_audit_id": "ST11-PARAM::00461",
  "parameter_id": "ST10-PARAM::0461",
  "parameter_symbol": "bkp_enc",
  "precision_and_rounding_policy": {
    "allowlist_check": "REQUIRED",
    "internal_numeric_type": "typed_symbolic",
    "normalization": "CANONICAL_EXACT_TOKEN_NO_FREE_TEXT_COERCION",
    "rounding": "NOT_APPLICABLE"
  },
  "runtime_resolution_procedure": [
    "Parse the declared Day-1 seed or deterministic rule into the declared type.",
    "Validate against the reference range and structural constraint.",
    "Apply the declared bounded edit/search law; reject any value outside it."
  ],
  "source_line_end": 18933,
  "source_line_start": 18922,
  "step12_primary_tranche_id": "ST12-TRANCHE-A"
},
{
  "canonical_owner": "QKUComputationControlPlaneV1",
  "certified_step11_custody_ref": "inputs/certified_step11/QTT_Stage1_Step11_Parameter_Policy_Adjudication_v1_0.jsonl#ST11-PARAM::00462",
  "certified_step11_row_embedded_in_prompt": false,
  "codex_online_research_allowed": false,
  "direct_source_claim_justifications": [],
  "effective_bounded_search_space_or_fit_constraint": "material archives may not be treated as safely recoverable from one removable drive alone when off-device mirroring is required",
  "effective_day1_seed_value_or_resolution_rule": "TRUE_FOR_MATERIAL_ARCHIVE_AND_SECRET_RECOVERY_EXPORTS",
  "effective_default_authority_class": "EXPLICIT_QTT_OR_OWNER_POLICY_SEED_OR_RESOLUTION_RULE",
  "effective_fallback_behavior_when_value_unavailable": "FAIL_CLOSED_TO_REGISTERED_LOWER_SAFE_PATH_OR_NO_TRADE",
  "effective_owner_dashboard_editability_class": "EDITABLE_WITH_SHADOW",
  "effective_policy_authority": "CERTIFIED_STEP11_PARAMETER_POLICY",
  "effective_reference_range_or_structural_constraint": "{TRUE_FOR_MATERIAL_ARCHIVE_AND_SECRET_RECOVERY_EXPORTS,OWNER_EXPLICITLY_DISABLED_FOR_NONMATERIAL_CACHE_CLASSES_ONLY}",
  "effective_resolution_class": "STATIC_ENUM",
  "effective_source_state_refs": [
    "OWNER_POLICY::D3_11_7_10B",
    "SOURCE_PACK::D3_11_7_10B"
  ],
  "effective_ui_widget_class": "BOOLEAN_TOGGLE_PLUS_WARNING_BADGE",
  "effective_unit_or_basis": "off-device-mirror rule",
  "effective_value_source_class": "QTT_BACKUP_MIRROR_RULE",
  "evidence_basis_class": "FAMILY_SOURCE_PACK_PLUS_EXACT_OWNER_APPROVED_VALUE",
  "evidence_binding_rule_refs": [],
  "family_evidence_binding_ref": "ST12-FAMILY-EVIDENCE::D3_11_7_10B",
  "implementation_resolution_kind": "STATIC_OR_DETERMINISTIC_RULE",
  "launch_computability_state": "COMPUTABLE_FROM_STATIC_VALUE_OR_DETERMINISTIC_RULE",
  "master_plan_heading_path": [
    "Part II — Retained institutional design and parameter catalog",
    "D3. Operating architecture",
    "D3.11 Deployment Manifests and Codex Override Files",
    "D3.11.7 Hands-off automation governance registry, stepped-autonomy maturity model, and optional translator role law",
    "D3.11.7.10B Automatic backup subsystem atomic parameter and control specification"
  ],
  "master_plan_section_id": "D3.11.7.10B",
  "missing_stale_invalid_behavior": "REJECT_INVALID_VALUE_NO_SILENT_DEFAULT",
  "parameter_audit_id": "ST11-PARAM::00462",
  "parameter_id": "ST10-PARAM::0462",
  "parameter_symbol": "bkp_mirror",
  "precision_and_rounding_policy": {
    "allowlist_check": "REQUIRED",
    "internal_numeric_type": "typed_symbolic",
    "normalization": "CANONICAL_EXACT_TOKEN_NO_FREE_TEXT_COERCION",
    "rounding": "NOT_APPLICABLE"
  },
  "runtime_resolution_procedure": [
    "Parse the declared Day-1 seed or deterministic rule into the declared type.",
    "Validate against the reference range and structural constraint.",
    "Apply the declared bounded edit/search law; reject any value outside it."
  ],
  "source_line_end": 18945,
  "source_line_start": 18934,
  "step12_primary_tranche_id": "ST12-TRANCHE-A"
},
{
  "canonical_owner": "QKUComputationControlPlaneV1",
  "certified_step11_custody_ref": "inputs/certified_step11/QTT_Stage1_Step11_Parameter_Policy_Adjudication_v1_0.jsonl#ST11-PARAM::00465",
  "certified_step11_row_embedded_in_prompt": false,
  "codex_online_research_allowed": false,
  "direct_source_claim_justifications": [],
  "effective_bounded_search_space_or_fit_constraint": "automatic runtime backup may not silently mutate the primary coding branch",
  "effective_day1_seed_value_or_resolution_rule": "FORBIDDEN_FOR_AUTOMATED_BACKUP_SYNCS",
  "effective_default_authority_class": "EXPLICIT_QTT_OR_OWNER_POLICY_SEED_OR_RESOLUTION_RULE",
  "effective_fallback_behavior_when_value_unavailable": "FAIL_CLOSED_TO_REGISTERED_LOWER_SAFE_PATH_OR_NO_TRADE",
  "effective_owner_dashboard_editability_class": "READ_ONLY_SYMBOLIC",
  "effective_policy_authority": "CERTIFIED_STEP11_PARAMETER_POLICY",
  "effective_reference_range_or_structural_constraint": "{FORBIDDEN_FOR_AUTOMATED_BACKUP_SYNCS}",
  "effective_resolution_class": "STATIC_ENUM",
  "effective_source_state_refs": [
    "OWNER_POLICY::D3_11_7_10B",
    "SOURCE_PACK::D3_11_7_10B"
  ],
  "effective_ui_widget_class": "FORMULA_BADGE",
  "effective_unit_or_basis": "primary-branch auto-push rule",
  "effective_value_source_class": "QTT_PRIMARY_BRANCH_PROTECTION_RULE",
  "evidence_basis_class": "FAMILY_SOURCE_PACK_PLUS_EXACT_OWNER_APPROVED_VALUE",
  "evidence_binding_rule_refs": [],
  "family_evidence_binding_ref": "ST12-FAMILY-EVIDENCE::D3_11_7_10B",
  "implementation_resolution_kind": "STATIC_OR_DETERMINISTIC_RULE",
  "launch_computability_state": "COMPUTABLE_FROM_STATIC_VALUE_OR_DETERMINISTIC_RULE",
  "master_plan_heading_path": [
    "Part II — Retained institutional design and parameter catalog",
    "D3. Operating architecture",
    "D3.11 Deployment Manifests and Codex Override Files",
    "D3.11.7 Hands-off automation governance registry, stepped-autonomy maturity model, and optional translator role law",
    "D3.11.7.10B Automatic backup subsystem atomic parameter and control specification"
  ],
  "master_plan_section_id": "D3.11.7.10B",
  "missing_stale_invalid_behavior": "REJECT_INVALID_VALUE_NO_SILENT_DEFAULT",
  "parameter_audit_id": "ST11-PARAM::00465",
  "parameter_id": "ST10-PARAM::0465",
  "parameter_symbol": "gh_main_protect",
  "precision_and_rounding_policy": {
    "allowlist_check": "REQUIRED",
    "internal_numeric_type": "typed_symbolic",
    "normalization": "CANONICAL_EXACT_TOKEN_NO_FREE_TEXT_COERCION",
    "rounding": "NOT_APPLICABLE"
  },
  "runtime_resolution_procedure": [
    "Parse the declared Day-1 seed or deterministic rule into the declared type.",
    "Validate against the reference range and structural constraint.",
    "Apply the declared bounded edit/search law; reject any value outside it."
  ],
  "source_line_end": 18981,
  "source_line_start": 18970,
  "step12_primary_tranche_id": "ST12-TRANCHE-A"
},
{
  "canonical_owner": "QKUComputationControlPlaneV1",
  "certified_step11_custody_ref": "inputs/certified_step11/QTT_Stage1_Step11_Parameter_Policy_Adjudication_v1_0.jsonl#ST11-PARAM::00466",
  "certified_step11_row_embedded_in_prompt": false,
  "codex_online_research_allowed": false,
  "direct_source_claim_justifications": [],
  "effective_bounded_search_space_or_fit_constraint": "write success alone may not be treated as verified backup health",
  "effective_day1_seed_value_or_resolution_rule": "POST_BACKUP_MANIFEST_HASH_CHECK_PLUS_PERIODIC_RESTORE_TEST",
  "effective_default_authority_class": "EXPLICIT_QTT_OR_OWNER_POLICY_SEED_OR_RESOLUTION_RULE",
  "effective_fallback_behavior_when_value_unavailable": "FAIL_CLOSED_TO_REGISTERED_LOWER_SAFE_PATH_OR_NO_TRADE",
  "effective_owner_dashboard_editability_class": "EDITABLE_WITH_SHADOW",
  "effective_policy_authority": "CERTIFIED_STEP11_PARAMETER_POLICY",
  "effective_reference_range_or_structural_constraint": "{POST_BACKUP_MANIFEST_HASH_CHECK_PLUS_PERIODIC_RESTORE_TEST,POST_BACKUP_HASH_ONLY_OWNER_APPROVED_TEMPORARY_EXCEPTION}",
  "effective_resolution_class": "STATIC_ENUM",
  "effective_source_state_refs": [
    "OWNER_POLICY::D3_11_7_10B",
    "SOURCE_PACK::D3_11_7_10B"
  ],
  "effective_ui_widget_class": "ENUM_DROPDOWN",
  "effective_unit_or_basis": "backup-integrity-verification mode",
  "effective_value_source_class": "QTT_BACKUP_VERIFICATION_RULE",
  "evidence_basis_class": "FAMILY_SOURCE_PACK_PLUS_EXACT_OWNER_APPROVED_VALUE",
  "evidence_binding_rule_refs": [],
  "family_evidence_binding_ref": "ST12-FAMILY-EVIDENCE::D3_11_7_10B",
  "implementation_resolution_kind": "STATIC_OR_DETERMINISTIC_RULE",
  "launch_computability_state": "COMPUTABLE_FROM_STATIC_VALUE_OR_DETERMINISTIC_RULE",
  "master_plan_heading_path": [
    "Part II — Retained institutional design and parameter catalog",
    "D3. Operating architecture",
    "D3.11 Deployment Manifests and Codex Override Files",
    "D3.11.7 Hands-off automation governance registry, stepped-autonomy maturity model, and optional translator role law",
    "D3.11.7.10B Automatic backup subsystem atomic parameter and control specification"
  ],
  "master_plan_section_id": "D3.11.7.10B",
  "missing_stale_invalid_behavior": "REJECT_INVALID_VALUE_NO_SILENT_DEFAULT",
  "parameter_audit_id": "ST11-PARAM::00466",
  "parameter_id": "ST10-PARAM::0466",
  "parameter_symbol": "bkp_verify",
  "precision_and_rounding_policy": {
    "allowlist_check": "REQUIRED",
    "internal_numeric_type": "typed_symbolic",
    "normalization": "CANONICAL_EXACT_TOKEN_NO_FREE_TEXT_COERCION",
    "rounding": "NOT_APPLICABLE"
  },
  "runtime_resolution_procedure": [
    "Parse the declared Day-1 seed or deterministic rule into the declared type.",
    "Validate against the reference range and structural constraint.",
    "Apply the declared bounded edit/search law; reject any value outside it."
  ],
  "source_line_end": 18993,
  "source_line_start": 18982,
  "step12_primary_tranche_id": "ST12-TRANCHE-A"
},
{
  "canonical_owner": "QKUComputationControlPlaneV1",
  "certified_step11_custody_ref": "inputs/certified_step11/QTT_Stage1_Step11_Parameter_Policy_Adjudication_v1_0.jsonl#ST11-PARAM::00468",
  "certified_step11_row_embedded_in_prompt": false,
  "codex_online_research_allowed": false,
  "direct_source_claim_justifications": [],
  "effective_bounded_search_space_or_fit_constraint": "backups may not exist only as opaque bundles with no indexed restore catalog",
  "effective_day1_seed_value_or_resolution_rule": "VERSIONED_RESTORE_POINT_CATALOG_REQUIRED",
  "effective_default_authority_class": "EXPLICIT_QTT_OR_OWNER_POLICY_SEED_OR_RESOLUTION_RULE",
  "effective_fallback_behavior_when_value_unavailable": "FAIL_CLOSED_TO_REGISTERED_LOWER_SAFE_PATH_OR_NO_TRADE",
  "effective_owner_dashboard_editability_class": "READ_ONLY_SYMBOLIC",
  "effective_policy_authority": "CERTIFIED_STEP11_PARAMETER_POLICY",
  "effective_reference_range_or_structural_constraint": "{VERSIONED_RESTORE_POINT_CATALOG_REQUIRED}",
  "effective_resolution_class": "STATIC_ENUM",
  "effective_source_state_refs": [
    "OWNER_POLICY::D3_11_7_10B",
    "SOURCE_PACK::D3_11_7_10B"
  ],
  "effective_ui_widget_class": "FORMULA_BADGE",
  "effective_unit_or_basis": "restore-point catalog requirement",
  "effective_value_source_class": "QTT_RESTORE_CATALOG_RULE",
  "evidence_basis_class": "FAMILY_SOURCE_PACK_PLUS_EXACT_OWNER_APPROVED_VALUE",
  "evidence_binding_rule_refs": [],
  "family_evidence_binding_ref": "ST12-FAMILY-EVIDENCE::D3_11_7_10B",
  "implementation_resolution_kind": "STATIC_OR_DETERMINISTIC_RULE",
  "launch_computability_state": "COMPUTABLE_FROM_STATIC_VALUE_OR_DETERMINISTIC_RULE",
  "master_plan_heading_path": [
    "Part II — Retained institutional design and parameter catalog",
    "D3. Operating architecture",
    "D3.11 Deployment Manifests and Codex Override Files",
    "D3.11.7 Hands-off automation governance registry, stepped-autonomy maturity model, and optional translator role law",
    "D3.11.7.10B Automatic backup subsystem atomic parameter and control specification"
  ],
  "master_plan_section_id": "D3.11.7.10B",
  "missing_stale_invalid_behavior": "REJECT_INVALID_VALUE_NO_SILENT_DEFAULT",
  "parameter_audit_id": "ST11-PARAM::00468",
  "parameter_id": "ST10-PARAM::0468",
  "parameter_symbol": "bkp_catalog",
  "precision_and_rounding_policy": {
    "allowlist_check": "REQUIRED",
    "internal_numeric_type": "typed_symbolic",
    "normalization": "CANONICAL_EXACT_TOKEN_NO_FREE_TEXT_COERCION",
    "rounding": "NOT_APPLICABLE"
  },
  "runtime_resolution_procedure": [
    "Parse the declared Day-1 seed or deterministic rule into the declared type.",
    "Validate against the reference range and structural constraint.",
    "Apply the declared bounded edit/search law; reject any value outside it."
  ],
  "source_line_end": 19020,
  "source_line_start": 19006,
  "step12_primary_tranche_id": "ST12-TRANCHE-A"
},
{
  "canonical_owner": "QKUComputationControlPlaneV1",
  "certified_step11_custody_ref": "inputs/certified_step11/QTT_Stage1_Step11_Parameter_Policy_Adjudication_v1_0.jsonl#ST11-PARAM::00487",
  "certified_step11_row_embedded_in_prompt": false,
  "codex_online_research_allowed": false,
  "direct_source_claim_justifications": [],
  "effective_bounded_search_space_or_fit_constraint": "unresolved expiration-pricing basis may not be guessed or inherited from prior-day series state",
  "effective_day1_seed_value_or_resolution_rule": "DOWNGRADE_TO_NO_AUTO_EXERCISE_AND_MANUAL_REVIEW_UNTIL_OFFICIAL_EXPIRATION_PRICING_BASIS_RECOVERS",
  "effective_default_authority_class": "EXPLICIT_QTT_OR_OWNER_POLICY_SEED_OR_RESOLUTION_RULE",
  "effective_fallback_behavior_when_value_unavailable": "FAIL_CLOSED_TO_REGISTERED_LOWER_SAFE_PATH_OR_NO_TRADE",
  "effective_owner_dashboard_editability_class": "READ_ONLY_BY_DEFAULT",
  "effective_policy_authority": "CERTIFIED_STEP11_PARAMETER_POLICY",
  "effective_reference_range_or_structural_constraint": "{DOWNGRADE_TO_NO_AUTO_EXERCISE_AND_MANUAL_REVIEW_UNTIL_OFFICIAL_EXPIRATION_PRICING_BASIS_RECOVERS}",
  "effective_resolution_class": "STATIC_ENUM_OR_RULE",
  "effective_source_state_refs": [
    "OWNER_POLICY::EX_10J0A",
    "SOURCE_PACK::EX_10J0A"
  ],
  "effective_ui_widget_class": "READ_ONLY_POLICY_CARD",
  "effective_unit_or_basis": "fail-closed expiration-pricing rule",
  "effective_value_source_class": "QTT_FAIL_CLOSED_LISTED_OPTION_EXPIRATION_RULE",
  "evidence_basis_class": "FAMILY_SOURCE_PACK_PLUS_EXACT_OWNER_APPROVED_VALUE",
  "evidence_binding_rule_refs": [],
  "family_evidence_binding_ref": "ST12-FAMILY-EVIDENCE::EX_10J0A",
  "implementation_resolution_kind": "STATIC_OR_DETERMINISTIC_RULE",
  "launch_computability_state": "COMPUTABLE_FROM_STATIC_VALUE_OR_DETERMINISTIC_RULE",
  "master_plan_heading_path": [
    "Part II — Retained institutional design and parameter catalog",
    "D6. Core contract layer",
    "EX-10J0A — Listed-option expiration-pricing and adjustment-memo pointer resolution closure"
  ],
  "master_plan_section_id": "EX-10J0A",
  "missing_stale_invalid_behavior": "REJECT_INVALID_VALUE_NO_SILENT_DEFAULT",
  "parameter_audit_id": "ST11-PARAM::00487",
  "parameter_id": "ST10-PARAM::0487",
  "parameter_symbol": "opt_exp_px_fail",
  "precision_and_rounding_policy": {
    "allowlist_check": "REQUIRED",
    "internal_numeric_type": "typed_symbolic",
    "normalization": "CANONICAL_EXACT_TOKEN_NO_FREE_TEXT_COERCION",
    "rounding": "NOT_APPLICABLE"
  },
  "runtime_resolution_procedure": [
    "Parse the declared Day-1 seed or deterministic rule into the declared type.",
    "Validate against the reference range and structural constraint.",
    "Apply the declared bounded edit/search law; reject any value outside it."
  ],
  "source_line_end": 23618,
  "source_line_start": 23607,
  "step12_primary_tranche_id": "ST12-TRANCHE-A"
},
{
  "canonical_owner": "QKUComputationControlPlaneV1",
  "certified_step11_custody_ref": "inputs/certified_step11/QTT_Stage1_Step11_Parameter_Policy_Adjudication_v1_0.jsonl#ST11-PARAM::00489",
  "certified_step11_row_embedded_in_prompt": false,
  "codex_online_research_allowed": false,
  "direct_source_claim_justifications": [],
  "effective_bounded_search_space_or_fit_constraint": "adjusted-series deliverables may not be guessed from stale class history or informal broker commentary",
  "effective_day1_seed_value_or_resolution_rule": "DOWNGRADE_TO_NO_TRADE_NO_AUTO_EXERCISE_AND_MANUAL_REVIEW_FOR_ADJUSTED_SERIES_WITH_MISSING_MEMO",
  "effective_default_authority_class": "EXPLICIT_QTT_OR_OWNER_POLICY_SEED_OR_RESOLUTION_RULE",
  "effective_fallback_behavior_when_value_unavailable": "FAIL_CLOSED_TO_REGISTERED_LOWER_SAFE_PATH_OR_NO_TRADE",
  "effective_owner_dashboard_editability_class": "READ_ONLY_BY_DEFAULT",
  "effective_policy_authority": "CERTIFIED_STEP11_PARAMETER_POLICY",
  "effective_reference_range_or_structural_constraint": "{DOWNGRADE_TO_NO_TRADE_NO_AUTO_EXERCISE_AND_MANUAL_REVIEW_FOR_ADJUSTED_SERIES_WITH_MISSING_MEMO}",
  "effective_resolution_class": "STATIC_ENUM_OR_RULE",
  "effective_source_state_refs": [
    "OWNER_POLICY::EX_10J0A",
    "SOURCE_PACK::EX_10J0A"
  ],
  "effective_ui_widget_class": "READ_ONLY_POLICY_CARD",
  "effective_unit_or_basis": "fail-closed adjustment-memo rule",
  "effective_value_source_class": "QTT_FAIL_CLOSED_LISTED_OPTION_ADJUSTMENT_RULE",
  "evidence_basis_class": "FAMILY_SOURCE_PACK_PLUS_EXACT_OWNER_APPROVED_VALUE",
  "evidence_binding_rule_refs": [],
  "family_evidence_binding_ref": "ST12-FAMILY-EVIDENCE::EX_10J0A",
  "implementation_resolution_kind": "EXPLICIT_FAIL_CLOSED_POLICY",
  "launch_computability_state": "COMPUTABLE_TYPED_FAIL_CLOSED_OR_NO_TRADE_STATE",
  "master_plan_heading_path": [
    "Part II — Retained institutional design and parameter catalog",
    "D6. Core contract layer",
    "EX-10J0A — Listed-option expiration-pricing and adjustment-memo pointer resolution closure"
  ],
  "master_plan_section_id": "EX-10J0A",
  "missing_stale_invalid_behavior": "PRESERVE_EXPLICIT_FAIL_CLOSED_STATE",
  "parameter_audit_id": "ST11-PARAM::00489",
  "parameter_id": "ST10-PARAM::0489",
  "parameter_symbol": "opt_adj_fail",
  "precision_and_rounding_policy": {
    "allowlist_check": "REQUIRED",
    "internal_numeric_type": "typed_symbolic",
    "normalization": "CANONICAL_EXACT_TOKEN_NO_FREE_TEXT_COERCION",
    "rounding": "NOT_APPLICABLE"
  },
  "runtime_resolution_procedure": [
    "Materialize the declared fail-closed state exactly.",
    "Return a typed blocker/no-trade status and do not substitute a numeric fallback.",
    "Validate the resolved typed value or token against the effective resolution class, declared structural constraint, and canonical allowlist; on failure apply the declared fail-closed fallback and emit the exact reason code."
  ],
  "source_line_end": 23651,
  "source_line_start": 23631,
  "step12_primary_tranche_id": "ST12-TRANCHE-A"
},
{
  "canonical_owner": "QKUComputationControlPlaneV1",
  "certified_step11_custody_ref": "inputs/certified_step11/QTT_Stage1_Step11_Parameter_Policy_Adjudication_v1_0.jsonl#ST11-PARAM::00504",
  "certified_step11_row_embedded_in_prompt": false,
  "codex_online_research_allowed": false,
  "direct_source_claim_justifications": [],
  "effective_bounded_search_space_or_fit_constraint": "fixed public method only unless a later controlled upgrade adds another public weighting basis",
  "effective_day1_seed_value_or_resolution_rule": "RETURN_ATTRIBUTION_PLUS_AVERAGE_UNIQUENESS_FROM_DECLARED_EVENT_SET",
  "effective_default_authority_class": "PUBLIC_METHOD_OR_PINNED_PROVIDER_DEFAULT_REQUIRES_IMPLEMENTATION_VERSION_BINDING",
  "effective_fallback_behavior_when_value_unavailable": "FAIL_CLOSED_TO_REGISTERED_LOWER_SAFE_PATH_OR_NO_TRADE",
  "effective_owner_dashboard_editability_class": "VIEW_ONLY_RESOLVED",
  "effective_policy_authority": "CERTIFIED_STEP11_PARAMETER_POLICY",
  "effective_reference_range_or_structural_constraint": "{RETURN_ATTRIBUTION_PLUS_AVERAGE_UNIQUENESS_FROM_DECLARED_EVENT_SET}",
  "effective_resolution_class": "STATIC_RULE_ENUM",
  "effective_source_state_refs": [
    "OWNER_POLICY::D6_3D4A",
    "SOURCE_PACK::D6_3D4A"
  ],
  "effective_ui_widget_class": "READ_ONLY_RULE_CARD",
  "effective_unit_or_basis": "weighting-basis rule",
  "effective_value_source_class": "PUBLIC_FINANCE_ML_IMPLEMENTATION_DOC",
  "evidence_basis_class": "FAMILY_SOURCE_PACK_PLUS_EXACT_OWNER_APPROVED_VALUE",
  "evidence_binding_rule_refs": [],
  "family_evidence_binding_ref": "ST12-FAMILY-EVIDENCE::D6_3D4A",
  "implementation_resolution_kind": "STATIC_OR_DETERMINISTIC_RULE",
  "launch_computability_state": "COMPUTABLE_FROM_STATIC_VALUE_OR_DETERMINISTIC_RULE",
  "master_plan_heading_path": [
    "Part II — Retained institutional design and parameter catalog",
    "D6. Core contract layer",
    "D6.3D4A Sample-weighting atomic parameter pack"
  ],
  "master_plan_section_id": "D6.3D4A",
  "missing_stale_invalid_behavior": "REJECT_INVALID_VALUE_NO_SILENT_DEFAULT",
  "parameter_audit_id": "ST11-PARAM::00504",
  "parameter_id": "ST10-PARAM::0504",
  "parameter_symbol": "w_basis_ru",
  "precision_and_rounding_policy": {
    "allowlist_check": "REQUIRED",
    "internal_numeric_type": "typed_symbolic",
    "normalization": "CANONICAL_EXACT_TOKEN_NO_FREE_TEXT_COERCION",
    "rounding": "NOT_APPLICABLE"
  },
  "runtime_resolution_procedure": [
    "Parse the declared Day-1 seed or deterministic rule into the declared type.",
    "Validate against the reference range and structural constraint.",
    "Apply the declared bounded edit/search law; reject any value outside it."
  ],
  "source_line_end": 23933,
  "source_line_start": 23922,
  "step12_primary_tranche_id": "ST12-TRANCHE-A"
},
{
  "canonical_owner": "QKUComputationControlPlaneV1",
  "certified_step11_custody_ref": "inputs/certified_step11/QTT_Stage1_Step11_Parameter_Policy_Adjudication_v1_0.jsonl#ST11-PARAM::00506",
  "certified_step11_row_embedded_in_prompt": false,
  "codex_online_research_allowed": false,
  "direct_source_claim_justifications": [],
  "effective_bounded_search_space_or_fit_constraint": "fixed Day-1 rule only",
  "effective_day1_seed_value_or_resolution_rule": "ROUTE_SAMPLE_WEIGHT_TO_ALL_DECLARED_WEIGHT_CAPABLE_CONSUMERS_ELSE_FAIL_CLOSED_TO_COMPARATOR",
  "effective_default_authority_class": "EXPLICIT_QTT_OR_OWNER_POLICY_SEED_OR_RESOLUTION_RULE",
  "effective_fallback_behavior_when_value_unavailable": "FAIL_CLOSED_TO_REGISTERED_LOWER_SAFE_PATH_OR_NO_TRADE",
  "effective_owner_dashboard_editability_class": "VIEW_ONLY_RESOLVED",
  "effective_policy_authority": "CERTIFIED_STEP11_PARAMETER_POLICY",
  "effective_reference_range_or_structural_constraint": "{ROUTE_SAMPLE_WEIGHT_TO_ALL_DECLARED_WEIGHT_CAPABLE_CONSUMERS_ELSE_FAIL_CLOSED_TO_COMPARATOR}",
  "effective_resolution_class": "STATIC_RULE_ENUM",
  "effective_source_state_refs": [
    "OWNER_POLICY::D6_3D4A",
    "SOURCE_PACK::D6_3D4A"
  ],
  "effective_ui_widget_class": "READ_ONLY_RULE_CARD",
  "effective_unit_or_basis": "routing rule",
  "effective_value_source_class": "QTT_CANONICAL_POLICY_RULE",
  "evidence_basis_class": "FAMILY_SOURCE_PACK_PLUS_EXACT_OWNER_APPROVED_VALUE",
  "evidence_binding_rule_refs": [],
  "family_evidence_binding_ref": "ST12-FAMILY-EVIDENCE::D6_3D4A",
  "implementation_resolution_kind": "EXPLICIT_FAIL_CLOSED_POLICY",
  "launch_computability_state": "COMPUTABLE_TYPED_FAIL_CLOSED_OR_NO_TRADE_STATE",
  "master_plan_heading_path": [
    "Part II — Retained institutional design and parameter catalog",
    "D6. Core contract layer",
    "D6.3D4A Sample-weighting atomic parameter pack"
  ],
  "master_plan_section_id": "D6.3D4A",
  "missing_stale_invalid_behavior": "PRESERVE_EXPLICIT_FAIL_CLOSED_STATE",
  "parameter_audit_id": "ST11-PARAM::00506",
  "parameter_id": "ST10-PARAM::0506",
  "parameter_symbol": "w_route",
  "precision_and_rounding_policy": {
    "allowlist_check": "REQUIRED",
    "internal_numeric_type": "typed_symbolic",
    "normalization": "CANONICAL_EXACT_TOKEN_NO_FREE_TEXT_COERCION",
    "rounding": "NOT_APPLICABLE"
  },
  "runtime_resolution_procedure": [
    "Materialize the declared fail-closed state exactly.",
    "Return a typed blocker/no-trade status and do not substitute a numeric fallback.",
    "Validate the resolved typed value or token against the effective resolution class, declared structural constraint, and canonical allowlist; on failure apply the declared fail-closed fallback and emit the exact reason code."
  ],
  "source_line_end": 23960,
  "source_line_start": 23946,
  "step12_primary_tranche_id": "ST12-TRANCHE-A"
},
{
  "canonical_owner": "QKUComputationControlPlaneV1",
  "certified_step11_custody_ref": "inputs/certified_step11/QTT_Stage1_Step11_Parameter_Policy_Adjudication_v1_0.jsonl#ST11-PARAM::00595",
  "certified_step11_row_embedded_in_prompt": false,
  "codex_online_research_allowed": false,
  "direct_source_claim_justifications": [],
  "effective_bounded_search_space_or_fit_constraint": "hard-veto inputs fixed in the active edition unless later strengthened",
  "effective_day1_seed_value_or_resolution_rule": "VENUE_CONSTRAINT_VALID_PLUS_ARTIFACT_TTL_FRESH_PLUS_SCHEMA_VALID_PLUS_RISK_ENVELOPE_SATISFIED_PLUS_LATENCY_FIT_ACCEPTABLE_PLUS_CONNECTOR_AND_LOCAL_HOST_HEALTH_ACCEPTABLE",
  "effective_default_authority_class": "EXPLICIT_QTT_OR_OWNER_POLICY_SEED_OR_RESOLUTION_RULE",
  "effective_fallback_behavior_when_value_unavailable": "FAIL_CLOSED_TO_REGISTERED_LOWER_SAFE_PATH_OR_NO_TRADE",
  "effective_owner_dashboard_editability_class": "READ_ONLY_SYMBOLIC",
  "effective_policy_authority": "CERTIFIED_STEP11_PARAMETER_POLICY",
  "effective_reference_range_or_structural_constraint": "{VENUE_CONSTRAINT_VALID_PLUS_ARTIFACT_TTL_FRESH_PLUS_SCHEMA_VALID_PLUS_RISK_ENVELOPE_SATISFIED_PLUS_LATENCY_FIT_ACCEPTABLE_PLUS_CONNECTOR_AND_LOCAL_HOST_HEALTH_ACCEPTABLE}",
  "effective_resolution_class": "STATIC_ENUM",
  "effective_source_state_refs": [
    "OWNER_POLICY::D8_10A",
    "SOURCE_PACK::D8_10A"
  ],
  "effective_ui_widget_class": "FORMULA_BADGE",
  "effective_unit_or_basis": "hard-veto health profile",
  "effective_value_source_class": "QTT_RISK_AND_EXECUTION_VETO_LAW",
  "evidence_basis_class": "FAMILY_SOURCE_PACK_PLUS_EXACT_OWNER_APPROVED_VALUE",
  "evidence_binding_rule_refs": [],
  "family_evidence_binding_ref": "ST12-FAMILY-EVIDENCE::D8_10A",
  "implementation_resolution_kind": "STATIC_OR_DETERMINISTIC_RULE",
  "launch_computability_state": "COMPUTABLE_FROM_STATIC_VALUE_OR_DETERMINISTIC_RULE",
  "master_plan_heading_path": [
    "Part II — Retained institutional design and parameter catalog",
    "D8. Promotion ladder",
    "D8.10A Regime-conditioned bundle, paired-workflow, ablation, and preset-lifecycle atomic parameter and control specification"
  ],
  "master_plan_section_id": "D8.10A",
  "missing_stale_invalid_behavior": "REJECT_INVALID_VALUE_NO_SILENT_DEFAULT",
  "parameter_audit_id": "ST11-PARAM::00595",
  "parameter_id": "ST10-PARAM::0595",
  "parameter_symbol": "veto_hexec",
  "precision_and_rounding_policy": {
    "allowlist_check": "REQUIRED",
    "internal_numeric_type": "typed_symbolic",
    "normalization": "CANONICAL_EXACT_TOKEN_NO_FREE_TEXT_COERCION",
    "rounding": "NOT_APPLICABLE"
  },
  "runtime_resolution_procedure": [
    "Parse the declared Day-1 seed or deterministic rule into the declared type.",
    "Validate against the reference range and structural constraint.",
    "Apply the declared bounded edit/search law; reject any value outside it."
  ],
  "source_line_end": 28286,
  "source_line_start": 28275,
  "step12_primary_tranche_id": "ST12-TRANCHE-A"
},
{
  "canonical_owner": "QKUComputationControlPlaneV1",
  "certified_step11_custody_ref": "inputs/certified_step11/QTT_Stage1_Step11_Parameter_Policy_Adjudication_v1_0.jsonl#ST11-PARAM::00636",
  "certified_step11_row_embedded_in_prompt": false,
  "codex_online_research_allowed": false,
  "direct_source_claim_justifications": [],
  "effective_bounded_search_space_or_fit_constraint": "fixed custody contract only",
  "effective_day1_seed_value_or_resolution_rule": "OWNER_OR_OWNER_SURFACE_SUBMITS_AND_RESEARCH_INTAKE_RECORD_IS_MATERIALIZED",
  "effective_default_authority_class": "EXPLICIT_QTT_OR_OWNER_POLICY_SEED_OR_RESOLUTION_RULE",
  "effective_fallback_behavior_when_value_unavailable": "FAIL_CLOSED_TO_REGISTERED_LOWER_SAFE_PATH_OR_NO_TRADE",
  "effective_owner_dashboard_editability_class": "READ_ONLY_SYMBOLIC",
  "effective_policy_authority": "CERTIFIED_STEP11_PARAMETER_POLICY",
  "effective_reference_range_or_structural_constraint": "{OWNER_OR_OWNER_SURFACE_SUBMITS_AND_RESEARCH_INTAKE_RECORD_IS_MATERIALIZED}",
  "effective_resolution_class": "STATIC_ENUM",
  "effective_source_state_refs": [
    "OWNER_POLICY::D8_11D1",
    "SOURCE_PACK::D8_11D1"
  ],
  "effective_ui_widget_class": "FORMULA_BADGE",
  "effective_unit_or_basis": "intake-stage custody profile",
  "effective_value_source_class": "QTT_WORKFLOW_CUSTODY_LAW",
  "evidence_basis_class": "FAMILY_SOURCE_PACK_PLUS_EXACT_OWNER_APPROVED_VALUE",
  "evidence_binding_rule_refs": [],
  "family_evidence_binding_ref": "ST12-FAMILY-EVIDENCE::D8_11D1",
  "implementation_resolution_kind": "STATIC_OR_DETERMINISTIC_RULE",
  "launch_computability_state": "COMPUTABLE_FROM_STATIC_VALUE_OR_DETERMINISTIC_RULE",
  "master_plan_heading_path": [
    "Part II — Retained institutional design and parameter catalog",
    "D8. Promotion ladder",
    "D8.11D1 Review-gateway spend governance and workflow-custody atomic parameter and control specification"
  ],
  "master_plan_section_id": "D8.11D1",
  "missing_stale_invalid_behavior": "REJECT_INVALID_VALUE_NO_SILENT_DEFAULT",
  "parameter_audit_id": "ST11-PARAM::00636",
  "parameter_id": "ST10-PARAM::0636",
  "parameter_symbol": "cust_intake",
  "precision_and_rounding_policy": {
    "allowlist_check": "REQUIRED",
    "internal_numeric_type": "typed_symbolic",
    "normalization": "CANONICAL_EXACT_TOKEN_NO_FREE_TEXT_COERCION",
    "rounding": "NOT_APPLICABLE"
  },
  "runtime_resolution_procedure": [
    "Parse the declared Day-1 seed or deterministic rule into the declared type.",
    "Validate against the reference range and structural constraint.",
    "Apply the declared bounded edit/search law; reject any value outside it."
  ],
  "source_line_end": 29376,
  "source_line_start": 29365,
  "step12_primary_tranche_id": "ST12-TRANCHE-A"
},
{
  "canonical_owner": "QKUComputationControlPlaneV1",
  "certified_step11_custody_ref": "inputs/certified_step11/QTT_Stage1_Step11_Parameter_Policy_Adjudication_v1_0.jsonl#ST11-PARAM::00637",
  "certified_step11_row_embedded_in_prompt": false,
  "codex_online_research_allowed": false,
  "direct_source_claim_justifications": [],
  "effective_bounded_search_space_or_fit_constraint": "fixed custody contract only",
  "effective_day1_seed_value_or_resolution_rule": "PROPOSAL_PACKAGER_AND_RESEARCH_SYNTHESIS_TRIAGE_SCOPE_AND_NEXT_ACTION",
  "effective_default_authority_class": "EXPLICIT_QTT_OR_OWNER_POLICY_SEED_OR_RESOLUTION_RULE",
  "effective_fallback_behavior_when_value_unavailable": "FAIL_CLOSED_TO_REGISTERED_LOWER_SAFE_PATH_OR_NO_TRADE",
  "effective_owner_dashboard_editability_class": "READ_ONLY_SYMBOLIC",
  "effective_policy_authority": "CERTIFIED_STEP11_PARAMETER_POLICY",
  "effective_reference_range_or_structural_constraint": "{PROPOSAL_PACKAGER_AND_RESEARCH_SYNTHESIS_TRIAGE_SCOPE_AND_NEXT_ACTION}",
  "effective_resolution_class": "STATIC_ENUM",
  "effective_source_state_refs": [
    "OWNER_POLICY::D8_11D1",
    "SOURCE_PACK::D8_11D1"
  ],
  "effective_ui_widget_class": "FORMULA_BADGE",
  "effective_unit_or_basis": "triage-stage custody profile",
  "effective_value_source_class": "QTT_WORKFLOW_CUSTODY_LAW",
  "evidence_basis_class": "FAMILY_SOURCE_PACK_PLUS_EXACT_OWNER_APPROVED_VALUE",
  "evidence_binding_rule_refs": [],
  "family_evidence_binding_ref": "ST12-FAMILY-EVIDENCE::D8_11D1",
  "implementation_resolution_kind": "STATIC_OR_DETERMINISTIC_RULE",
  "launch_computability_state": "COMPUTABLE_FROM_STATIC_VALUE_OR_DETERMINISTIC_RULE",
  "master_plan_heading_path": [
    "Part II — Retained institutional design and parameter catalog",
    "D8. Promotion ladder",
    "D8.11D1 Review-gateway spend governance and workflow-custody atomic parameter and control specification"
  ],
  "master_plan_section_id": "D8.11D1",
  "missing_stale_invalid_behavior": "REJECT_INVALID_VALUE_NO_SILENT_DEFAULT",
  "parameter_audit_id": "ST11-PARAM::00637",
  "parameter_id": "ST10-PARAM::0637",
  "parameter_symbol": "cust_triage",
  "precision_and_rounding_policy": {
    "allowlist_check": "REQUIRED",
    "internal_numeric_type": "typed_symbolic",
    "normalization": "CANONICAL_EXACT_TOKEN_NO_FREE_TEXT_COERCION",
    "rounding": "NOT_APPLICABLE"
  },
  "runtime_resolution_procedure": [
    "Parse the declared Day-1 seed or deterministic rule into the declared type.",
    "Validate against the reference range and structural constraint.",
    "Apply the declared bounded edit/search law; reject any value outside it."
  ],
  "source_line_end": 29388,
  "source_line_start": 29377,
  "step12_primary_tranche_id": "ST12-TRANCHE-A"
},
{
  "canonical_owner": "QKUComputationControlPlaneV1",
  "certified_step11_custody_ref": "inputs/certified_step11/QTT_Stage1_Step11_Parameter_Policy_Adjudication_v1_0.jsonl#ST11-PARAM::00639",
  "certified_step11_row_embedded_in_prompt": false,
  "codex_online_research_allowed": false,
  "direct_source_claim_justifications": [],
  "effective_bounded_search_space_or_fit_constraint": "fixed custody contract only",
  "effective_day1_seed_value_or_resolution_rule": "ARCHITECTURE_REVIEW_DESK_OR_MANUAL_CHATGPT_REVIEW_EMITS_REVIEW_PACKET_AND_BLOCKERS",
  "effective_default_authority_class": "EXPLICIT_QTT_OR_OWNER_POLICY_SEED_OR_RESOLUTION_RULE",
  "effective_fallback_behavior_when_value_unavailable": "FAIL_CLOSED_TO_REGISTERED_LOWER_SAFE_PATH_OR_NO_TRADE",
  "effective_owner_dashboard_editability_class": "READ_ONLY_SYMBOLIC",
  "effective_policy_authority": "CERTIFIED_STEP11_PARAMETER_POLICY",
  "effective_reference_range_or_structural_constraint": "{ARCHITECTURE_REVIEW_DESK_OR_MANUAL_CHATGPT_REVIEW_EMITS_REVIEW_PACKET_AND_BLOCKERS}",
  "effective_resolution_class": "STATIC_ENUM",
  "effective_source_state_refs": [
    "OWNER_POLICY::D8_11D1",
    "SOURCE_PACK::D8_11D1"
  ],
  "effective_ui_widget_class": "FORMULA_BADGE",
  "effective_unit_or_basis": "architecture-review custody profile",
  "effective_value_source_class": "QTT_WORKFLOW_CUSTODY_LAW",
  "evidence_basis_class": "FAMILY_SOURCE_PACK_PLUS_EXACT_OWNER_APPROVED_VALUE",
  "evidence_binding_rule_refs": [],
  "family_evidence_binding_ref": "ST12-FAMILY-EVIDENCE::D8_11D1",
  "implementation_resolution_kind": "STATIC_OR_DETERMINISTIC_RULE",
  "launch_computability_state": "COMPUTABLE_FROM_STATIC_VALUE_OR_DETERMINISTIC_RULE",
  "master_plan_heading_path": [
    "Part II — Retained institutional design and parameter catalog",
    "D8. Promotion ladder",
    "D8.11D1 Review-gateway spend governance and workflow-custody atomic parameter and control specification"
  ],
  "master_plan_section_id": "D8.11D1",
  "missing_stale_invalid_behavior": "REJECT_INVALID_VALUE_NO_SILENT_DEFAULT",
  "parameter_audit_id": "ST11-PARAM::00639",
  "parameter_id": "ST10-PARAM::0639",
  "parameter_symbol": "cust_arch",
  "precision_and_rounding_policy": {
    "allowlist_check": "REQUIRED",
    "internal_numeric_type": "typed_symbolic",
    "normalization": "CANONICAL_EXACT_TOKEN_NO_FREE_TEXT_COERCION",
    "rounding": "NOT_APPLICABLE"
  },
  "runtime_resolution_procedure": [
    "Parse the declared Day-1 seed or deterministic rule into the declared type.",
    "Validate against the reference range and structural constraint.",
    "Apply the declared bounded edit/search law; reject any value outside it."
  ],
  "source_line_end": 29412,
  "source_line_start": 29401,
  "step12_primary_tranche_id": "ST12-TRANCHE-A"
},
{
  "canonical_owner": "QKUComputationControlPlaneV1",
  "certified_step11_custody_ref": "inputs/certified_step11/QTT_Stage1_Step11_Parameter_Policy_Adjudication_v1_0.jsonl#ST11-PARAM::00640",
  "certified_step11_row_embedded_in_prompt": false,
  "codex_online_research_allowed": false,
  "direct_source_claim_justifications": [],
  "effective_bounded_search_space_or_fit_constraint": "fixed custody contract only",
  "effective_day1_seed_value_or_resolution_rule": "OWNER_DECIDES_APPROVE_FOR_SHADOW_REQUEST_MORE_RESEARCH_REJECT_ARCHIVE_OR_RETURN_TO_BACKLOG_REVITALIZATION",
  "effective_default_authority_class": "EXPLICIT_QTT_OR_OWNER_POLICY_SEED_OR_RESOLUTION_RULE",
  "effective_fallback_behavior_when_value_unavailable": "FAIL_CLOSED_TO_REGISTERED_LOWER_SAFE_PATH_OR_NO_TRADE",
  "effective_owner_dashboard_editability_class": "READ_ONLY_SYMBOLIC",
  "effective_policy_authority": "CERTIFIED_STEP11_PARAMETER_POLICY",
  "effective_reference_range_or_structural_constraint": "{OWNER_DECIDES_APPROVE_FOR_SHADOW_REQUEST_MORE_RESEARCH_REJECT_ARCHIVE_OR_RETURN_TO_BACKLOG_REVITALIZATION}",
  "effective_resolution_class": "STATIC_ENUM",
  "effective_source_state_refs": [
    "OWNER_POLICY::D8_11D1",
    "SOURCE_PACK::D8_11D1"
  ],
  "effective_ui_widget_class": "FORMULA_BADGE",
  "effective_unit_or_basis": "Gate-1 custody profile",
  "effective_value_source_class": "QTT_WORKFLOW_CUSTODY_LAW",
  "evidence_basis_class": "FAMILY_SOURCE_PACK_PLUS_EXACT_OWNER_APPROVED_VALUE",
  "evidence_binding_rule_refs": [],
  "family_evidence_binding_ref": "ST12-FAMILY-EVIDENCE::D8_11D1",
  "implementation_resolution_kind": "STATIC_OR_DETERMINISTIC_RULE",
  "launch_computability_state": "COMPUTABLE_FROM_STATIC_VALUE_OR_DETERMINISTIC_RULE",
  "master_plan_heading_path": [
    "Part II — Retained institutional design and parameter catalog",
    "D8. Promotion ladder",
    "D8.11D1 Review-gateway spend governance and workflow-custody atomic parameter and control specification"
  ],
  "master_plan_section_id": "D8.11D1",
  "missing_stale_invalid_behavior": "REJECT_INVALID_VALUE_NO_SILENT_DEFAULT",
  "parameter_audit_id": "ST11-PARAM::00640",
  "parameter_id": "ST10-PARAM::0640",
  "parameter_symbol": "cust_gate1",
  "precision_and_rounding_policy": {
    "allowlist_check": "REQUIRED",
    "internal_numeric_type": "typed_symbolic",
    "normalization": "CANONICAL_EXACT_TOKEN_NO_FREE_TEXT_COERCION",
    "rounding": "NOT_APPLICABLE"
  },
  "runtime_resolution_procedure": [
    "Parse the declared Day-1 seed or deterministic rule into the declared type.",
    "Validate against the reference range and structural constraint.",
    "Apply the declared bounded edit/search law; reject any value outside it."
  ],
  "source_line_end": 29424,
  "source_line_start": 29413,
  "step12_primary_tranche_id": "ST12-TRANCHE-A"
},
{
  "canonical_owner": "QKUComputationControlPlaneV1",
  "certified_step11_custody_ref": "inputs/certified_step11/QTT_Stage1_Step11_Parameter_Policy_Adjudication_v1_0.jsonl#ST11-PARAM::00642",
  "certified_step11_row_embedded_in_prompt": false,
  "codex_online_research_allowed": false,
  "direct_source_claim_justifications": [],
  "effective_bounded_search_space_or_fit_constraint": "fixed custody contract only",
  "effective_day1_seed_value_or_resolution_rule": "SHADOW_HARNESS_PRODUCES_SHADOW_RESULTS_AND_RISK_MANAGER_RETAINS_VETO",
  "effective_default_authority_class": "EXPLICIT_QTT_OR_OWNER_POLICY_SEED_OR_RESOLUTION_RULE",
  "effective_fallback_behavior_when_value_unavailable": "FAIL_CLOSED_TO_REGISTERED_LOWER_SAFE_PATH_OR_NO_TRADE",
  "effective_owner_dashboard_editability_class": "READ_ONLY_SYMBOLIC",
  "effective_policy_authority": "CERTIFIED_STEP11_PARAMETER_POLICY",
  "effective_reference_range_or_structural_constraint": "{SHADOW_HARNESS_PRODUCES_SHADOW_RESULTS_AND_RISK_MANAGER_RETAINS_VETO}",
  "effective_resolution_class": "STATIC_ENUM",
  "effective_source_state_refs": [
    "OWNER_POLICY::D8_11D1",
    "SOURCE_PACK::D8_11D1"
  ],
  "effective_ui_widget_class": "FORMULA_BADGE",
  "effective_unit_or_basis": "shadow-stage custody profile",
  "effective_value_source_class": "QTT_WORKFLOW_CUSTODY_LAW",
  "evidence_basis_class": "FAMILY_SOURCE_PACK_PLUS_EXACT_OWNER_APPROVED_VALUE",
  "evidence_binding_rule_refs": [],
  "family_evidence_binding_ref": "ST12-FAMILY-EVIDENCE::D8_11D1",
  "implementation_resolution_kind": "STATIC_OR_DETERMINISTIC_RULE",
  "launch_computability_state": "COMPUTABLE_FROM_STATIC_VALUE_OR_DETERMINISTIC_RULE",
  "master_plan_heading_path": [
    "Part II — Retained institutional design and parameter catalog",
    "D8. Promotion ladder",
    "D8.11D1 Review-gateway spend governance and workflow-custody atomic parameter and control specification"
  ],
  "master_plan_section_id": "D8.11D1",
  "missing_stale_invalid_behavior": "REJECT_INVALID_VALUE_NO_SILENT_DEFAULT",
  "parameter_audit_id": "ST11-PARAM::00642",
  "parameter_id": "ST10-PARAM::0642",
  "parameter_symbol": "cust_shadow",
  "precision_and_rounding_policy": {
    "allowlist_check": "REQUIRED",
    "internal_numeric_type": "typed_symbolic",
    "normalization": "CANONICAL_EXACT_TOKEN_NO_FREE_TEXT_COERCION",
    "rounding": "NOT_APPLICABLE"
  },
  "runtime_resolution_procedure": [
    "Parse the declared Day-1 seed or deterministic rule into the declared type.",
    "Validate against the reference range and structural constraint.",
    "Apply the declared bounded edit/search law; reject any value outside it."
  ],
  "source_line_end": 29448,
  "source_line_start": 29437,
  "step12_primary_tranche_id": "ST12-TRANCHE-A"
},
{
  "canonical_owner": "QKUComputationControlPlaneV1",
  "certified_step11_custody_ref": "inputs/certified_step11/QTT_Stage1_Step11_Parameter_Policy_Adjudication_v1_0.jsonl#ST11-PARAM::00643",
  "certified_step11_row_embedded_in_prompt": false,
  "codex_online_research_allowed": false,
  "direct_source_claim_justifications": [],
  "effective_bounded_search_space_or_fit_constraint": "fixed custody contract only",
  "effective_day1_seed_value_or_resolution_rule": "OWNER_DECIDES_APPROVE_LIVE_EXTEND_SHADOW_REJECT_RETURN_FOR_REFINEMENT_OR_RETURN_TO_BACKLOG_REVITALIZATION",
  "effective_default_authority_class": "EXPLICIT_QTT_OR_OWNER_POLICY_SEED_OR_RESOLUTION_RULE",
  "effective_fallback_behavior_when_value_unavailable": "FAIL_CLOSED_TO_REGISTERED_LOWER_SAFE_PATH_OR_NO_TRADE",
  "effective_owner_dashboard_editability_class": "READ_ONLY_SYMBOLIC",
  "effective_policy_authority": "CERTIFIED_STEP11_PARAMETER_POLICY",
  "effective_reference_range_or_structural_constraint": "{OWNER_DECIDES_APPROVE_LIVE_EXTEND_SHADOW_REJECT_RETURN_FOR_REFINEMENT_OR_RETURN_TO_BACKLOG_REVITALIZATION}",
  "effective_resolution_class": "STATIC_ENUM",
  "effective_source_state_refs": [
    "OWNER_POLICY::D8_11D1",
    "SOURCE_PACK::D8_11D1"
  ],
  "effective_ui_widget_class": "FORMULA_BADGE",
  "effective_unit_or_basis": "Gate-2 custody profile",
  "effective_value_source_class": "QTT_WORKFLOW_CUSTODY_LAW",
  "evidence_basis_class": "FAMILY_SOURCE_PACK_PLUS_EXACT_OWNER_APPROVED_VALUE",
  "evidence_binding_rule_refs": [],
  "family_evidence_binding_ref": "ST12-FAMILY-EVIDENCE::D8_11D1",
  "implementation_resolution_kind": "STATIC_OR_DETERMINISTIC_RULE",
  "launch_computability_state": "COMPUTABLE_FROM_STATIC_VALUE_OR_DETERMINISTIC_RULE",
  "master_plan_heading_path": [
    "Part II — Retained institutional design and parameter catalog",
    "D8. Promotion ladder",
    "D8.11D1 Review-gateway spend governance and workflow-custody atomic parameter and control specification"
  ],
  "master_plan_section_id": "D8.11D1",
  "missing_stale_invalid_behavior": "REJECT_INVALID_VALUE_NO_SILENT_DEFAULT",
  "parameter_audit_id": "ST11-PARAM::00643",
  "parameter_id": "ST10-PARAM::0643",
  "parameter_symbol": "cust_gate2",
  "precision_and_rounding_policy": {
    "allowlist_check": "REQUIRED",
    "internal_numeric_type": "typed_symbolic",
    "normalization": "CANONICAL_EXACT_TOKEN_NO_FREE_TEXT_COERCION",
    "rounding": "NOT_APPLICABLE"
  },
  "runtime_resolution_procedure": [
    "Parse the declared Day-1 seed or deterministic rule into the declared type.",
    "Validate against the reference range and structural constraint.",
    "Apply the declared bounded edit/search law; reject any value outside it."
  ],
  "source_line_end": 29460,
  "source_line_start": 29449,
  "step12_primary_tranche_id": "ST12-TRANCHE-A"
},
{
  "canonical_owner": "QKUComputationControlPlaneV1",
  "certified_step11_custody_ref": "inputs/certified_step11/QTT_Stage1_Step11_Parameter_Policy_Adjudication_v1_0.jsonl#ST11-PARAM::00644",
  "certified_step11_row_embedded_in_prompt": false,
  "codex_online_research_allowed": false,
  "direct_source_claim_justifications": [],
  "effective_bounded_search_space_or_fit_constraint": "fixed custody contract only",
  "effective_day1_seed_value_or_resolution_rule": "TRADE_EXECUTOR_ACTS_ONLY_AFTER_GATE2_GREEN_AND_RISK_AND_EXECUTION_VETO_CLEARANCE",
  "effective_default_authority_class": "EXPLICIT_QTT_OR_OWNER_POLICY_SEED_OR_RESOLUTION_RULE",
  "effective_fallback_behavior_when_value_unavailable": "FAIL_CLOSED_TO_REGISTERED_LOWER_SAFE_PATH_OR_NO_TRADE",
  "effective_owner_dashboard_editability_class": "READ_ONLY_SYMBOLIC",
  "effective_policy_authority": "CERTIFIED_STEP11_PARAMETER_POLICY",
  "effective_reference_range_or_structural_constraint": "{TRADE_EXECUTOR_ACTS_ONLY_AFTER_GATE2_GREEN_AND_RISK_AND_EXECUTION_VETO_CLEARANCE}",
  "effective_resolution_class": "STATIC_ENUM",
  "effective_source_state_refs": [
    "OWNER_POLICY::D8_11D1",
    "SOURCE_PACK::D8_11D1"
  ],
  "effective_ui_widget_class": "FORMULA_BADGE",
  "effective_unit_or_basis": "limited-live custody profile",
  "effective_value_source_class": "QTT_WORKFLOW_CUSTODY_LAW",
  "evidence_basis_class": "FAMILY_SOURCE_PACK_PLUS_EXACT_OWNER_APPROVED_VALUE",
  "evidence_binding_rule_refs": [],
  "family_evidence_binding_ref": "ST12-FAMILY-EVIDENCE::D8_11D1",
  "implementation_resolution_kind": "STATIC_OR_DETERMINISTIC_RULE",
  "launch_computability_state": "COMPUTABLE_FROM_STATIC_VALUE_OR_DETERMINISTIC_RULE",
  "master_plan_heading_path": [
    "Part II — Retained institutional design and parameter catalog",
    "D8. Promotion ladder",
    "D8.11D1 Review-gateway spend governance and workflow-custody atomic parameter and control specification"
  ],
  "master_plan_section_id": "D8.11D1",
  "missing_stale_invalid_behavior": "REJECT_INVALID_VALUE_NO_SILENT_DEFAULT",
  "parameter_audit_id": "ST11-PARAM::00644",
  "parameter_id": "ST10-PARAM::0644",
  "parameter_symbol": "cust_live",
  "precision_and_rounding_policy": {
    "allowlist_check": "REQUIRED",
    "internal_numeric_type": "typed_symbolic",
    "normalization": "CANONICAL_EXACT_TOKEN_NO_FREE_TEXT_COERCION",
    "rounding": "NOT_APPLICABLE"
  },
  "runtime_resolution_procedure": [
    "Parse the declared Day-1 seed or deterministic rule into the declared type.",
    "Validate against the reference range and structural constraint.",
    "Apply the declared bounded edit/search law; reject any value outside it."
  ],
  "source_line_end": 29472,
  "source_line_start": 29461,
  "step12_primary_tranche_id": "ST12-TRANCHE-A"
},
{
  "canonical_owner": "QKUComputationControlPlaneV1",
  "certified_step11_custody_ref": "inputs/certified_step11/QTT_Stage1_Step11_Parameter_Policy_Adjudication_v1_0.jsonl#ST11-PARAM::00721",
  "certified_step11_row_embedded_in_prompt": false,
  "codex_online_research_allowed": false,
  "direct_source_claim_justifications": [],
  "effective_bounded_search_space_or_fit_constraint": "HEAVY may not run without an explicit demeaning / precentering rule",
  "effective_day1_seed_value_or_resolution_rule": "DEMEAN_ALWAYS_FOR_HEAVY",
  "effective_default_authority_class": "PUBLIC_METHOD_OR_PINNED_PROVIDER_DEFAULT_REQUIRES_IMPLEMENTATION_VERSION_BINDING",
  "effective_fallback_behavior_when_value_unavailable": "FAIL_CLOSED_TO_REGISTERED_LOWER_SAFE_PATH_OR_NO_TRADE",
  "effective_owner_dashboard_editability_class": "READ_ONLY_RULE_CARD",
  "effective_policy_authority": "CERTIFIED_STEP11_PARAMETER_POLICY",
  "effective_reference_range_or_structural_constraint": "{DEMEAN_ALWAYS_FOR_HEAVY, DECLARED_EQUIVALENT_PRECENTERING_RECEIPT}",
  "effective_resolution_class": "STATIC_ENUM",
  "effective_source_state_refs": [
    "OWNER_POLICY::FE_03D2",
    "SOURCE_PACK::FE_03D2"
  ],
  "effective_ui_widget_class": "READ_ONLY_RULE_CARD",
  "effective_unit_or_basis": "preprocessing-policy enum",
  "effective_value_source_class": "PUBLIC_OFFICIAL_DOC_REFERENCE",
  "evidence_basis_class": "FAMILY_SOURCE_PACK_PLUS_EXACT_OWNER_APPROVED_VALUE",
  "evidence_binding_rule_refs": [],
  "family_evidence_binding_ref": "ST12-FAMILY-EVIDENCE::FE_03D2",
  "implementation_resolution_kind": "STATIC_OR_DETERMINISTIC_RULE",
  "launch_computability_state": "COMPUTABLE_FROM_STATIC_VALUE_OR_DETERMINISTIC_RULE",
  "master_plan_heading_path": [
    "Part II — Retained institutional design and parameter catalog",
    "D11. Canonical family registry — feature engineering",
    "FE-03D2 — Realized-GARCH / HEAVY atomic parameter pack"
  ],
  "master_plan_section_id": "FE-03D2",
  "missing_stale_invalid_behavior": "REJECT_INVALID_VALUE_NO_SILENT_DEFAULT",
  "parameter_audit_id": "ST11-PARAM::00721",
  "parameter_id": "ST10-PARAM::0721",
  "parameter_symbol": "heavy_demean",
  "precision_and_rounding_policy": {
    "allowlist_check": "REQUIRED",
    "internal_numeric_type": "typed_symbolic",
    "normalization": "CANONICAL_EXACT_TOKEN_NO_FREE_TEXT_COERCION",
    "rounding": "NOT_APPLICABLE"
  },
  "runtime_resolution_procedure": [
    "Parse the declared Day-1 seed or deterministic rule into the declared type.",
    "Validate against the reference range and structural constraint.",
    "Apply the declared bounded edit/search law; reject any value outside it."
  ],
  "source_line_end": 31767,
  "source_line_start": 31752,
  "step12_primary_tranche_id": "ST12-TRANCHE-A"
},
{
  "canonical_owner": "QKUComputationControlPlaneV1",
  "certified_step11_custody_ref": "inputs/certified_step11/QTT_Stage1_Step11_Parameter_Policy_Adjudication_v1_0.jsonl#ST11-PARAM::00761",
  "certified_step11_row_embedded_in_prompt": false,
  "codex_online_research_allowed": false,
  "direct_source_claim_justifications": [],
  "effective_bounded_search_space_or_fit_constraint": "read-only rule when the family is already selected",
  "effective_day1_seed_value_or_resolution_rule": "3_FOR_DNS_OR_AFNS_ELSE_4_FOR_DNSS",
  "effective_default_authority_class": "PUBLIC_METHOD_OR_PINNED_PROVIDER_DEFAULT_REQUIRES_IMPLEMENTATION_VERSION_BINDING",
  "effective_fallback_behavior_when_value_unavailable": "FAIL_CLOSED_TO_REGISTERED_LOWER_SAFE_PATH_OR_NO_TRADE",
  "effective_owner_dashboard_editability_class": "READ_ONLY_RULE_CARD",
  "effective_policy_authority": "CERTIFIED_STEP11_PARAMETER_POLICY",
  "effective_reference_range_or_structural_constraint": "{3,4}",
  "effective_resolution_class": "STATIC_INTEGER_OR_RULE",
  "effective_source_state_refs": [
    "OWNER_POLICY::FE_09F2",
    "SOURCE_PACK::FE_09F2"
  ],
  "effective_ui_widget_class": "READ_ONLY_RULE_CARD",
  "effective_unit_or_basis": "factor count",
  "effective_value_source_class": "PUBLIC_ACADEMIC_METHOD_REFERENCE_WITH_EXPLICIT_QTT_BINDING",
  "evidence_basis_class": "FAMILY_SOURCE_PACK_PLUS_EXACT_OWNER_APPROVED_VALUE",
  "evidence_binding_rule_refs": [],
  "family_evidence_binding_ref": "ST12-FAMILY-EVIDENCE::FE_09F2",
  "implementation_resolution_kind": "STATIC_OR_DETERMINISTIC_RULE",
  "launch_computability_state": "COMPUTABLE_FROM_STATIC_VALUE_OR_DETERMINISTIC_RULE",
  "master_plan_heading_path": [
    "Part II — Retained institutional design and parameter catalog",
    "D11. Canonical family registry — feature engineering",
    "FE-09F2 — Dynamic Nelson-Siegel / AFNS atomic parameter pack"
  ],
  "master_plan_section_id": "FE-09F2",
  "missing_stale_invalid_behavior": "REJECT_INVALID_VALUE_NO_SILENT_DEFAULT",
  "parameter_audit_id": "ST11-PARAM::00761",
  "parameter_id": "ST10-PARAM::0761",
  "parameter_symbol": "k_dns",
  "precision_and_rounding_policy": {
    "allowlist_check": "REQUIRED",
    "internal_numeric_type": "typed_symbolic",
    "normalization": "CANONICAL_EXACT_TOKEN_NO_FREE_TEXT_COERCION",
    "rounding": "NOT_APPLICABLE"
  },
  "runtime_resolution_procedure": [
    "Parse the declared Day-1 seed or deterministic rule into the declared type.",
    "Validate against the reference range and structural constraint.",
    "Apply the declared bounded edit/search law; reject any value outside it."
  ],
  "source_line_end": 32635,
  "source_line_start": 32624,
  "step12_primary_tranche_id": "ST12-TRANCHE-A"
},
{
  "canonical_owner": "QKUComputationControlPlaneV1",
  "certified_step11_custody_ref": "inputs/certified_step11/QTT_Stage1_Step11_Parameter_Policy_Adjudication_v1_0.jsonl#ST11-PARAM::00765",
  "certified_step11_row_embedded_in_prompt": false,
  "codex_online_research_allowed": false,
  "direct_source_claim_justifications": [],
  "effective_bounded_search_space_or_fit_constraint": "closed numerical search inside `[-0.999, 0.999]`",
  "effective_day1_seed_value_or_resolution_rule": "LAST_ACCEPTED_SURFACE.rho if available else 0.0",
  "effective_default_authority_class": "PUBLIC_METHOD_OR_PINNED_PROVIDER_DEFAULT_REQUIRES_IMPLEMENTATION_VERSION_BINDING",
  "effective_fallback_behavior_when_value_unavailable": "FAIL_CLOSED_TO_REGISTERED_LOWER_SAFE_PATH_OR_NO_TRADE",
  "effective_owner_dashboard_editability_class": "READ_ONLY_BY_DEFAULT",
  "effective_policy_authority": "CERTIFIED_STEP11_PARAMETER_POLICY",
  "effective_reference_range_or_structural_constraint": "(-1,1)",
  "effective_resolution_class": "FIT_TIME_RESOLVED",
  "effective_source_state_refs": [
    "OWNER_POLICY::FE_10C1",
    "SOURCE_PACK::FE_10C1"
  ],
  "effective_ui_widget_class": "READ_ONLY_NUMERIC",
  "effective_unit_or_basis": "dimensionless",
  "effective_value_source_class": "ACADEMIC_PUBLIC_REFERENCE",
  "evidence_basis_class": "FAMILY_SOURCE_PACK_PLUS_EXACT_OWNER_APPROVED_VALUE",
  "evidence_binding_rule_refs": [],
  "family_evidence_binding_ref": "ST12-FAMILY-EVIDENCE::FE_10C1",
  "implementation_resolution_kind": "OFFLINE_CALIBRATION_OR_BOUNDED_OPTIMIZATION",
  "launch_computability_state": "COMPUTABLE_WITH_DECLARED_DAY1_SEED_AND_OFFLINE_VALIDATION",
  "master_plan_heading_path": [
    "Part II — Retained institutional design and parameter catalog",
    "D11. Canonical family registry — feature engineering",
    "FE-10C1 — SVI / SSVI atomic parameter pack"
  ],
  "master_plan_section_id": "FE-10C1",
  "missing_stale_invalid_behavior": "USE_DECLARED_SEED_ONLY_IF_PRESENT_ELSE_BLOCK; NEVER_WIDEN_SEARCH_SPACE",
  "parameter_audit_id": "ST11-PARAM::00765",
  "parameter_id": "ST10-PARAM::0765",
  "parameter_symbol": "rho",
  "precision_and_rounding_policy": {
    "finite_check": "REQUIRED_FOR_NUMERIC_VALUES",
    "internal_numeric_type": "declared_typed_scalar_or_structure",
    "rounding": "PER_UNIT_OR_SOURCE_RULE"
  },
  "runtime_resolution_procedure": [
    "Use the declared Day-1 seed when one exists and mark it SEED_NOT_VALIDATED.",
    "Fit or optimize only in REPLAY/PAPER research lanes using point-in-time data, purging/embargo when labels overlap, and a declared comparator.",
    "Search only the bounded space in bounded_search_space_or_fit_constraint; deterministic seed and full trial inventory are mandatory.",
    "No promotion follows from fit success alone; evidence and owner gates remain separate."
  ],
  "source_line_end": 32722,
  "source_line_start": 32711,
  "step12_primary_tranche_id": "ST12-TRANCHE-A"
},
{
  "canonical_owner": "QKUComputationControlPlaneV1",
  "certified_step11_custody_ref": "inputs/certified_step11/QTT_Stage1_Step11_Parameter_Policy_Adjudication_v1_0.jsonl#ST11-PARAM::00801",
  "certified_step11_row_embedded_in_prompt": false,
  "codex_online_research_allowed": false,
  "direct_source_claim_justifications": [],
  "effective_bounded_search_space_or_fit_constraint": "singleton basis only in the current repository-authoritative baseline edition",
  "effective_day1_seed_value_or_resolution_rule": "TREND_PLUS_SEASONAL_PLUS_RESIDUAL_PLUS_DESEASONALIZED_SERIES",
  "effective_default_authority_class": "EXPLICIT_QTT_OR_OWNER_POLICY_SEED_OR_RESOLUTION_RULE",
  "effective_fallback_behavior_when_value_unavailable": "FAIL_CLOSED_TO_REGISTERED_LOWER_SAFE_PATH_OR_NO_TRADE",
  "effective_owner_dashboard_editability_class": "OWNER_VISIBLE_NOT_EDITABLE",
  "effective_policy_authority": "CERTIFIED_STEP11_PARAMETER_POLICY",
  "effective_reference_range_or_structural_constraint": "`{TREND_PLUS_SEASONAL_PLUS_RESIDUAL_PLUS_DESEASONALIZED_SERIES}` unless a later canonical master plan adds an explicit alternative basis",
  "effective_resolution_class": "STATIC_ENUM",
  "effective_source_state_refs": [
    "OWNER_POLICY::DI_03B",
    "SOURCE_PACK::DI_03B"
  ],
  "effective_ui_widget_class": "READONLY_ENUM_BADGE",
  "effective_unit_or_basis": "decomposition output basis",
  "effective_value_source_class": "QTT_CANONICAL_OUTPUT_BASIS_RULE",
  "evidence_basis_class": "FAMILY_SOURCE_PACK_PLUS_EXACT_OWNER_APPROVED_VALUE",
  "evidence_binding_rule_refs": [],
  "family_evidence_binding_ref": "ST12-FAMILY-EVIDENCE::DI_03B",
  "implementation_resolution_kind": "STATIC_OR_DETERMINISTIC_RULE",
  "launch_computability_state": "COMPUTABLE_FROM_STATIC_VALUE_OR_DETERMINISTIC_RULE",
  "master_plan_heading_path": [
    "Part II — Retained institutional design and parameter catalog",
    "D11A. Canonical family registry — statistical diagnostics and decomposition",
    "DI-03B — Classical moving-average decomposition atomic parameter pack and current-version deployment and binding specification"
  ],
  "master_plan_section_id": "DI-03B",
  "missing_stale_invalid_behavior": "REJECT_INVALID_VALUE_NO_SILENT_DEFAULT",
  "parameter_audit_id": "ST11-PARAM::00801",
  "parameter_id": "ST10-PARAM::0801",
  "parameter_symbol": "sdec_out",
  "precision_and_rounding_policy": {
    "allowlist_check": "REQUIRED",
    "internal_numeric_type": "typed_symbolic",
    "normalization": "CANONICAL_EXACT_TOKEN_NO_FREE_TEXT_COERCION",
    "rounding": "NOT_APPLICABLE"
  },
  "runtime_resolution_procedure": [
    "Parse the declared Day-1 seed or deterministic rule into the declared type.",
    "Validate against the reference range and structural constraint.",
    "Apply the declared bounded edit/search law; reject any value outside it."
  ],
  "source_line_end": 33661,
  "source_line_start": 33650,
  "step12_primary_tranche_id": "ST12-TRANCHE-A"
},
{
  "canonical_owner": "QKUComputationControlPlaneV1",
  "certified_step11_custody_ref": "inputs/certified_step11/QTT_Stage1_Step11_Parameter_Policy_Adjudication_v1_0.jsonl#ST11-PARAM::00819",
  "certified_step11_row_embedded_in_prompt": false,
  "codex_online_research_allowed": false,
  "direct_source_claim_justifications": [],
  "effective_bounded_search_space_or_fit_constraint": "singleton basis only in the current repository-authoritative baseline edition",
  "effective_day1_seed_value_or_resolution_rule": "MULTI_SEASON_COMPONENT_TABLE_PLUS_TREND_PLUS_RESIDUAL_PLUS_DESEASONALIZED_SERIES",
  "effective_default_authority_class": "EXPLICIT_QTT_OR_OWNER_POLICY_SEED_OR_RESOLUTION_RULE",
  "effective_fallback_behavior_when_value_unavailable": "FAIL_CLOSED_TO_REGISTERED_LOWER_SAFE_PATH_OR_NO_TRADE",
  "effective_owner_dashboard_editability_class": "OWNER_VISIBLE_NOT_EDITABLE",
  "effective_policy_authority": "CERTIFIED_STEP11_PARAMETER_POLICY",
  "effective_reference_range_or_structural_constraint": "`{MULTI_SEASON_COMPONENT_TABLE_PLUS_TREND_PLUS_RESIDUAL_PLUS_DESEASONALIZED_SERIES}` unless a later canonical master plan adds an explicit alternative basis",
  "effective_resolution_class": "STATIC_ENUM",
  "effective_source_state_refs": [
    "OWNER_POLICY::DI_05B",
    "SOURCE_PACK::DI_05B"
  ],
  "effective_ui_widget_class": "READONLY_ENUM_BADGE",
  "effective_unit_or_basis": "decomposition output basis",
  "effective_value_source_class": "QTT_CANONICAL_OUTPUT_BASIS_RULE",
  "evidence_basis_class": "FAMILY_SOURCE_PACK_PLUS_EXACT_OWNER_APPROVED_VALUE",
  "evidence_binding_rule_refs": [],
  "family_evidence_binding_ref": "ST12-FAMILY-EVIDENCE::DI_05B",
  "implementation_resolution_kind": "STATIC_OR_DETERMINISTIC_RULE",
  "launch_computability_state": "COMPUTABLE_FROM_STATIC_VALUE_OR_DETERMINISTIC_RULE",
  "master_plan_heading_path": [
    "Part II — Retained institutional design and parameter catalog",
    "D11A. Canonical family registry — statistical diagnostics and decomposition",
    "DI-05B — MSTL decomposition atomic parameter pack and current-version deployment and binding specification"
  ],
  "master_plan_section_id": "DI-05B",
  "missing_stale_invalid_behavior": "REJECT_INVALID_VALUE_NO_SILENT_DEFAULT",
  "parameter_audit_id": "ST11-PARAM::00819",
  "parameter_id": "ST10-PARAM::0819",
  "parameter_symbol": "mstl_out",
  "precision_and_rounding_policy": {
    "allowlist_check": "REQUIRED",
    "internal_numeric_type": "typed_symbolic",
    "normalization": "CANONICAL_EXACT_TOKEN_NO_FREE_TEXT_COERCION",
    "rounding": "NOT_APPLICABLE"
  },
  "runtime_resolution_procedure": [
    "Parse the declared Day-1 seed or deterministic rule into the declared type.",
    "Validate against the reference range and structural constraint.",
    "Apply the declared bounded edit/search law; reject any value outside it."
  ],
  "source_line_end": 33951,
  "source_line_start": 33940,
  "step12_primary_tranche_id": "ST12-TRANCHE-A"
},
{
  "canonical_owner": "QKUComputationControlPlaneV1",
  "certified_step11_custody_ref": "inputs/certified_step11/QTT_Stage1_Step11_Parameter_Policy_Adjudication_v1_0.jsonl#ST11-PARAM::00827",
  "certified_step11_row_embedded_in_prompt": false,
  "codex_online_research_allowed": false,
  "direct_source_claim_justifications": [],
  "effective_bounded_search_space_or_fit_constraint": "singleton policy only in the current repository-authoritative baseline edition",
  "effective_day1_seed_value_or_resolution_rule": "ALL_JUMPS_DEFAULT_TO_1_UNLESS_LATER_CONTROLLING_EDITION_SPLITS_THEM",
  "effective_default_authority_class": "PUBLIC_METHOD_OR_PINNED_PROVIDER_DEFAULT_REQUIRES_IMPLEMENTATION_VERSION_BINDING",
  "effective_fallback_behavior_when_value_unavailable": "FAIL_CLOSED_TO_REGISTERED_LOWER_SAFE_PATH_OR_NO_TRADE",
  "effective_owner_dashboard_editability_class": "OWNER_VISIBLE_NOT_EDITABLE",
  "effective_policy_authority": "CERTIFIED_STEP11_PARAMETER_POLICY",
  "effective_reference_range_or_structural_constraint": "{ALL_JUMPS_DEFAULT_TO_1_UNLESS_LATER_CONTROLLING_EDITION_SPLITS_THEM}",
  "effective_resolution_class": "STATIC_ENUM",
  "effective_source_state_refs": [
    "OWNER_POLICY::DI_06B",
    "SOURCE_PACK::DI_06B"
  ],
  "effective_ui_widget_class": "READONLY_ENUM_BADGE",
  "effective_unit_or_basis": "inherited jump-default policy",
  "effective_value_source_class": "PUBLIC_LIBRARY_DEFAULT_RULE_PLUS_QTT_WRAPPER_NORMALIZATION",
  "evidence_basis_class": "FAMILY_SOURCE_PACK_PLUS_EXACT_OWNER_APPROVED_VALUE",
  "evidence_binding_rule_refs": [],
  "family_evidence_binding_ref": "ST12-FAMILY-EVIDENCE::DI_06B",
  "implementation_resolution_kind": "STATIC_OR_DETERMINISTIC_RULE",
  "launch_computability_state": "COMPUTABLE_FROM_STATIC_VALUE_OR_DETERMINISTIC_RULE",
  "master_plan_heading_path": [
    "Part II — Retained institutional design and parameter catalog",
    "D11A. Canonical family registry — statistical diagnostics and decomposition",
    "DI-06B — STLForecast wrapper atomic parameter pack and current-version deployment and binding specification"
  ],
  "master_plan_section_id": "DI-06B",
  "missing_stale_invalid_behavior": "REJECT_INVALID_VALUE_NO_SILENT_DEFAULT",
  "parameter_audit_id": "ST11-PARAM::00827",
  "parameter_id": "ST10-PARAM::0827",
  "parameter_symbol": "stlf_jump",
  "precision_and_rounding_policy": {
    "allowlist_check": "REQUIRED",
    "internal_numeric_type": "typed_symbolic",
    "normalization": "CANONICAL_EXACT_TOKEN_NO_FREE_TEXT_COERCION",
    "rounding": "NOT_APPLICABLE"
  },
  "runtime_resolution_procedure": [
    "Parse the declared Day-1 seed or deterministic rule into the declared type.",
    "Validate against the reference range and structural constraint.",
    "Apply the declared bounded edit/search law; reject any value outside it."
  ],
  "source_line_end": 34082,
  "source_line_start": 34071,
  "step12_primary_tranche_id": "ST12-TRANCHE-A"
},
{
  "canonical_owner": "QKUComputationControlPlaneV1",
  "certified_step11_custody_ref": "inputs/certified_step11/QTT_Stage1_Step11_Parameter_Policy_Adjudication_v1_0.jsonl#ST11-PARAM::00837",
  "certified_step11_row_embedded_in_prompt": false,
  "codex_online_research_allowed": false,
  "direct_source_claim_justifications": [],
  "effective_bounded_search_space_or_fit_constraint": "singleton basis only in the current repository-authoritative baseline edition",
  "effective_day1_seed_value_or_resolution_rule": "RAW_COMPONENT_SCORES_WHEN_PCA_WHITEN_FALSE_ELSE_WHITENED_COMPONENT_SCORES",
  "effective_default_authority_class": "EXPLICIT_QTT_OR_OWNER_POLICY_SEED_OR_RESOLUTION_RULE",
  "effective_fallback_behavior_when_value_unavailable": "FAIL_CLOSED_TO_REGISTERED_LOWER_SAFE_PATH_OR_NO_TRADE",
  "effective_owner_dashboard_editability_class": "OWNER_VISIBLE_NOT_EDITABLE",
  "effective_policy_authority": "CERTIFIED_STEP11_PARAMETER_POLICY",
  "effective_reference_range_or_structural_constraint": "`{RAW_COMPONENT_SCORES_WHEN_PCA_WHITEN_FALSE_ELSE_WHITENED_COMPONENT_SCORES}` unless a later canonical master plan adds an explicit alternative basis",
  "effective_resolution_class": "STATIC_ENUM",
  "effective_source_state_refs": [
    "OWNER_POLICY::FC_01B",
    "SOURCE_PACK::FC_01B"
  ],
  "effective_ui_widget_class": "READONLY_ENUM_BADGE",
  "effective_unit_or_basis": "component-score output basis",
  "effective_value_source_class": "QTT_CANONICAL_OUTPUT_BASIS_RULE",
  "evidence_basis_class": "FAMILY_SOURCE_PACK_PLUS_EXACT_OWNER_APPROVED_VALUE",
  "evidence_binding_rule_refs": [],
  "family_evidence_binding_ref": "ST12-FAMILY-EVIDENCE::FC_01B",
  "implementation_resolution_kind": "STATIC_OR_DETERMINISTIC_RULE",
  "launch_computability_state": "COMPUTABLE_FROM_STATIC_VALUE_OR_DETERMINISTIC_RULE",
  "master_plan_heading_path": [
    "Part II — Retained institutional design and parameter catalog",
    "D11B. Canonical family registry — feature compression and selection",
    "FC-01B — PCA atomic parameter pack and current-version deployment and binding specification"
  ],
  "master_plan_section_id": "FC-01B",
  "missing_stale_invalid_behavior": "REJECT_INVALID_VALUE_NO_SILENT_DEFAULT",
  "parameter_audit_id": "ST11-PARAM::00837",
  "parameter_id": "ST10-PARAM::0837",
  "parameter_symbol": "pca_out",
  "precision_and_rounding_policy": {
    "allowlist_check": "REQUIRED",
    "internal_numeric_type": "typed_symbolic",
    "normalization": "CANONICAL_EXACT_TOKEN_NO_FREE_TEXT_COERCION",
    "rounding": "NOT_APPLICABLE"
  },
  "runtime_resolution_procedure": [
    "Parse the declared Day-1 seed or deterministic rule into the declared type.",
    "Validate against the reference range and structural constraint.",
    "Apply the declared bounded edit/search law; reject any value outside it."
  ],
  "source_line_end": 34247,
  "source_line_start": 34236,
  "step12_primary_tranche_id": "ST12-TRANCHE-A"
},
{
  "canonical_owner": "QKUComputationControlPlaneV1",
  "certified_step11_custody_ref": "inputs/certified_step11/QTT_Stage1_Step11_Parameter_Policy_Adjudication_v1_0.jsonl#ST11-PARAM::00844",
  "certified_step11_row_embedded_in_prompt": false,
  "codex_online_research_allowed": false,
  "direct_source_claim_justifications": [],
  "effective_bounded_search_space_or_fit_constraint": "singleton basis only in the current repository-authoritative baseline edition",
  "effective_day1_seed_value_or_resolution_rule": "RAW_LATENT_FACTOR_SCORES",
  "effective_default_authority_class": "EXPLICIT_QTT_OR_OWNER_POLICY_SEED_OR_RESOLUTION_RULE",
  "effective_fallback_behavior_when_value_unavailable": "FAIL_CLOSED_TO_REGISTERED_LOWER_SAFE_PATH_OR_NO_TRADE",
  "effective_owner_dashboard_editability_class": "OWNER_VISIBLE_NOT_EDITABLE",
  "effective_policy_authority": "CERTIFIED_STEP11_PARAMETER_POLICY",
  "effective_reference_range_or_structural_constraint": "`{RAW_LATENT_FACTOR_SCORES}` unless a later canonical master plan adds an explicit alternative basis",
  "effective_resolution_class": "STATIC_ENUM",
  "effective_source_state_refs": [
    "OWNER_POLICY::FC_02B",
    "SOURCE_PACK::FC_02B"
  ],
  "effective_ui_widget_class": "READONLY_ENUM_BADGE",
  "effective_unit_or_basis": "downstream transform output basis",
  "effective_value_source_class": "QTT_CANONICAL_OUTPUT_BASIS_RULE",
  "evidence_basis_class": "FAMILY_SOURCE_PACK_PLUS_EXACT_OWNER_APPROVED_VALUE",
  "evidence_binding_rule_refs": [],
  "family_evidence_binding_ref": "ST12-FAMILY-EVIDENCE::FC_02B",
  "implementation_resolution_kind": "STATIC_OR_DETERMINISTIC_RULE",
  "launch_computability_state": "COMPUTABLE_FROM_STATIC_VALUE_OR_DETERMINISTIC_RULE",
  "master_plan_heading_path": [
    "Part II — Retained institutional design and parameter catalog",
    "D11B. Canonical family registry — feature compression and selection",
    "FC-02B — TruncatedSVD atomic parameter pack and current-version deployment and binding specification"
  ],
  "master_plan_section_id": "FC-02B",
  "missing_stale_invalid_behavior": "REJECT_INVALID_VALUE_NO_SILENT_DEFAULT",
  "parameter_audit_id": "ST11-PARAM::00844",
  "parameter_id": "ST10-PARAM::0844",
  "parameter_symbol": "svd_out_basis",
  "precision_and_rounding_policy": {
    "allowlist_check": "REQUIRED",
    "internal_numeric_type": "typed_symbolic",
    "normalization": "CANONICAL_EXACT_TOKEN_NO_FREE_TEXT_COERCION",
    "rounding": "NOT_APPLICABLE"
  },
  "runtime_resolution_procedure": [
    "Parse the declared Day-1 seed or deterministic rule into the declared type.",
    "Validate against the reference range and structural constraint.",
    "Apply the declared bounded edit/search law; reject any value outside it."
  ],
  "source_line_end": 34368,
  "source_line_start": 34357,
  "step12_primary_tranche_id": "ST12-TRANCHE-A"
},
{
  "canonical_owner": "QKUComputationControlPlaneV1",
  "certified_step11_custody_ref": "inputs/certified_step11/QTT_Stage1_Step11_Parameter_Policy_Adjudication_v1_0.jsonl#ST11-PARAM::00851",
  "certified_step11_row_embedded_in_prompt": false,
  "codex_online_research_allowed": false,
  "direct_source_claim_justifications": [],
  "effective_bounded_search_space_or_fit_constraint": "singleton basis only in the current repository-authoritative baseline edition",
  "effective_day1_seed_value_or_resolution_rule": "SUPERVISED_LATENT_SCORES_PLUS_PREDICTION_PACKET",
  "effective_default_authority_class": "EXPLICIT_QTT_OR_OWNER_POLICY_SEED_OR_RESOLUTION_RULE",
  "effective_fallback_behavior_when_value_unavailable": "FAIL_CLOSED_TO_REGISTERED_LOWER_SAFE_PATH_OR_NO_TRADE",
  "effective_owner_dashboard_editability_class": "OWNER_VISIBLE_NOT_EDITABLE",
  "effective_policy_authority": "CERTIFIED_STEP11_PARAMETER_POLICY",
  "effective_reference_range_or_structural_constraint": "`{SUPERVISED_LATENT_SCORES_PLUS_PREDICTION_PACKET}` unless a later canonical master plan adds an explicit alternative basis",
  "effective_resolution_class": "STATIC_ENUM",
  "effective_source_state_refs": [
    "OWNER_POLICY::FC_03B",
    "SOURCE_PACK::FC_03B"
  ],
  "effective_ui_widget_class": "READONLY_ENUM_BADGE",
  "effective_unit_or_basis": "downstream transform output basis",
  "effective_value_source_class": "QTT_CANONICAL_OUTPUT_BASIS_RULE",
  "evidence_basis_class": "FAMILY_SOURCE_PACK_PLUS_EXACT_OWNER_APPROVED_VALUE",
  "evidence_binding_rule_refs": [],
  "family_evidence_binding_ref": "ST12-FAMILY-EVIDENCE::FC_03B",
  "implementation_resolution_kind": "STATIC_OR_DETERMINISTIC_RULE",
  "launch_computability_state": "COMPUTABLE_FROM_STATIC_VALUE_OR_DETERMINISTIC_RULE",
  "master_plan_heading_path": [
    "Part II — Retained institutional design and parameter catalog",
    "D11B. Canonical family registry — feature compression and selection",
    "FC-03B — PLS regression atomic parameter pack and current-version deployment and binding specification"
  ],
  "master_plan_section_id": "FC-03B",
  "missing_stale_invalid_behavior": "REJECT_INVALID_VALUE_NO_SILENT_DEFAULT",
  "parameter_audit_id": "ST11-PARAM::00851",
  "parameter_id": "ST10-PARAM::0851",
  "parameter_symbol": "pls_out_basis",
  "precision_and_rounding_policy": {
    "allowlist_check": "REQUIRED",
    "internal_numeric_type": "typed_symbolic",
    "normalization": "CANONICAL_EXACT_TOKEN_NO_FREE_TEXT_COERCION",
    "rounding": "NOT_APPLICABLE"
  },
  "runtime_resolution_procedure": [
    "Parse the declared Day-1 seed or deterministic rule into the declared type.",
    "Validate against the reference range and structural constraint.",
    "Apply the declared bounded edit/search law; reject any value outside it."
  ],
  "source_line_end": 34490,
  "source_line_start": 34479,
  "step12_primary_tranche_id": "ST12-TRANCHE-A"
},
{
  "canonical_owner": "QKUComputationControlPlaneV1",
  "certified_step11_custody_ref": "inputs/certified_step11/QTT_Stage1_Step11_Parameter_Policy_Adjudication_v1_0.jsonl#ST11-PARAM::00854",
  "certified_step11_row_embedded_in_prompt": false,
  "codex_online_research_allowed": false,
  "direct_source_claim_justifications": [],
  "effective_bounded_search_space_or_fit_constraint": "singleton branch rule unless a later canonical master plan adds another admissible branch",
  "effective_day1_seed_value_or_resolution_rule": "USE_1E_MINUS_5_WHEN_ESTIMATOR_PENALTY_IS_L1_OR_IMPLICIT_L1",
  "effective_default_authority_class": "PUBLIC_METHOD_OR_PINNED_PROVIDER_DEFAULT_REQUIRES_IMPLEMENTATION_VERSION_BINDING",
  "effective_fallback_behavior_when_value_unavailable": "FAIL_CLOSED_TO_REGISTERED_LOWER_SAFE_PATH_OR_NO_TRADE",
  "effective_owner_dashboard_editability_class": "OWNER_VISIBLE_NOT_EDITABLE",
  "effective_policy_authority": "CERTIFIED_STEP11_PARAMETER_POLICY",
  "effective_reference_range_or_structural_constraint": "{USE_1E_MINUS_5_WHEN_ESTIMATOR_PENALTY_IS_L1_OR_IMPLICIT_L1,DISABLED_BY_EXPLICIT_THRESHOLD}",
  "effective_resolution_class": "STATIC_ENUM",
  "effective_source_state_refs": [
    "OWNER_POLICY::FC_04B",
    "SOURCE_PACK::FC_04B"
  ],
  "effective_ui_widget_class": "READONLY_ENUM_BADGE",
  "effective_unit_or_basis": "threshold-branch semantics",
  "effective_value_source_class": "PUBLIC_LIBRARY_DEFAULT_RULE",
  "evidence_basis_class": "FAMILY_SOURCE_PACK_PLUS_EXACT_OWNER_APPROVED_VALUE",
  "evidence_binding_rule_refs": [],
  "family_evidence_binding_ref": "ST12-FAMILY-EVIDENCE::FC_04B",
  "implementation_resolution_kind": "STATIC_OR_DETERMINISTIC_RULE",
  "launch_computability_state": "COMPUTABLE_FROM_STATIC_VALUE_OR_DETERMINISTIC_RULE",
  "master_plan_heading_path": [
    "Part II — Retained institutional design and parameter catalog",
    "D11B. Canonical family registry — feature compression and selection",
    "FC-04B — SelectFromModel atomic parameter pack and current-version deployment and binding specification"
  ],
  "master_plan_section_id": "FC-04B",
  "missing_stale_invalid_behavior": "REJECT_INVALID_VALUE_NO_SILENT_DEFAULT",
  "parameter_audit_id": "ST11-PARAM::00854",
  "parameter_id": "ST10-PARAM::0854",
  "parameter_symbol": "sfm_l1_rule",
  "precision_and_rounding_policy": {
    "allowlist_check": "REQUIRED",
    "internal_numeric_type": "typed_symbolic",
    "normalization": "CANONICAL_EXACT_TOKEN_NO_FREE_TEXT_COERCION",
    "rounding": "NOT_APPLICABLE"
  },
  "runtime_resolution_procedure": [
    "Parse the declared Day-1 seed or deterministic rule into the declared type.",
    "Validate against the reference range and structural constraint.",
    "Apply the declared bounded edit/search law; reject any value outside it."
  ],
  "source_line_end": 34566,
  "source_line_start": 34555,
  "step12_primary_tranche_id": "ST12-TRANCHE-A"
},
{
  "canonical_owner": "QKUComputationControlPlaneV1",
  "certified_step11_custody_ref": "inputs/certified_step11/QTT_Stage1_Step11_Parameter_Policy_Adjudication_v1_0.jsonl#ST11-PARAM::00973",
  "certified_step11_row_embedded_in_prompt": false,
  "codex_online_research_allowed": false,
  "direct_source_claim_justifications": [],
  "effective_bounded_search_space_or_fit_constraint": "singleton basis only in the current repository-authoritative baseline edition",
  "effective_day1_seed_value_or_resolution_rule": "CLASSIFIER_HARD_LABEL_AND_CLASS_PROBABILITY_OR_REGRESSOR_RAW_VALUE_AND_SPLIT_STRUCTURE_RECEIPT_BY_DECLARED_TASK",
  "effective_default_authority_class": "EXPLICIT_QTT_OR_OWNER_POLICY_SEED_OR_RESOLUTION_RULE",
  "effective_fallback_behavior_when_value_unavailable": "FAIL_CLOSED_TO_REGISTERED_LOWER_SAFE_PATH_OR_NO_TRADE",
  "effective_owner_dashboard_editability_class": "OWNER_VISIBLE_NOT_EDITABLE",
  "effective_policy_authority": "CERTIFIED_STEP11_PARAMETER_POLICY",
  "effective_reference_range_or_structural_constraint": "singleton output-basis contract only in the current repository-authoritative baseline edition",
  "effective_resolution_class": "STATIC_ENUM",
  "effective_source_state_refs": [
    "OWNER_POLICY::CM_05A2",
    "SOURCE_PACK::CM_05A2"
  ],
  "effective_ui_widget_class": "READONLY_ENUM_BADGE",
  "effective_unit_or_basis": "downstream output basis",
  "effective_value_source_class": "QTT_CANONICAL_OUTPUT_BASIS_RULE",
  "evidence_basis_class": "FAMILY_SOURCE_PACK_PLUS_EXACT_OWNER_APPROVED_VALUE",
  "evidence_binding_rule_refs": [],
  "family_evidence_binding_ref": "ST12-FAMILY-EVIDENCE::CM_05A2",
  "implementation_resolution_kind": "STATIC_OR_DETERMINISTIC_RULE",
  "launch_computability_state": "COMPUTABLE_FROM_STATIC_VALUE_OR_DETERMINISTIC_RULE",
  "master_plan_heading_path": [
    "Part II — Retained institutional design and parameter catalog",
    "D12. Canonical family registry — classical model families",
    "CM-05A2 — Decision-tree transparent anchor atomic parameter pack and current-version deployment and binding specification"
  ],
  "master_plan_section_id": "CM-05A2",
  "missing_stale_invalid_behavior": "REJECT_INVALID_VALUE_NO_SILENT_DEFAULT",
  "parameter_audit_id": "ST11-PARAM::00973",
  "parameter_id": "ST10-PARAM::0973",
  "parameter_symbol": "dt_out",
  "precision_and_rounding_policy": {
    "allowlist_check": "REQUIRED",
    "internal_numeric_type": "typed_symbolic",
    "normalization": "CANONICAL_EXACT_TOKEN_NO_FREE_TEXT_COERCION",
    "rounding": "NOT_APPLICABLE"
  },
  "runtime_resolution_procedure": [
    "Parse the declared Day-1 seed or deterministic rule into the declared type.",
    "Validate against the reference range and structural constraint.",
    "Apply the declared bounded edit/search law; reject any value outside it."
  ],
  "source_line_end": 36904,
  "source_line_start": 36892,
  "step12_primary_tranche_id": "ST12-TRANCHE-A"
},
{
  "canonical_owner": "QKUComputationControlPlaneV1",
  "certified_step11_custody_ref": "inputs/certified_step11/QTT_Stage1_Step11_Parameter_Policy_Adjudication_v1_0.jsonl#ST11-PARAM::00989",
  "certified_step11_row_embedded_in_prompt": false,
  "codex_online_research_allowed": false,
  "direct_source_claim_justifications": [],
  "effective_bounded_search_space_or_fit_constraint": "singleton basis only in the current repository-authoritative baseline edition",
  "effective_day1_seed_value_or_resolution_rule": "CLASSIFIER_RAW_SCORE_PROBABILITY_AND_CALIBRATED_PROBABILITY_OR_REGRESSOR_RAW_VALUE_AND_QUANTILE_PACKET_BY_DECLARED_TASK",
  "effective_default_authority_class": "EXPLICIT_QTT_OR_OWNER_POLICY_SEED_OR_RESOLUTION_RULE",
  "effective_fallback_behavior_when_value_unavailable": "FAIL_CLOSED_TO_REGISTERED_LOWER_SAFE_PATH_OR_NO_TRADE",
  "effective_owner_dashboard_editability_class": "OWNER_VISIBLE_NOT_EDITABLE",
  "effective_policy_authority": "CERTIFIED_STEP11_PARAMETER_POLICY",
  "effective_reference_range_or_structural_constraint": "singleton output-basis contract only in the current repository-authoritative baseline edition",
  "effective_resolution_class": "STATIC_ENUM",
  "effective_source_state_refs": [
    "OWNER_POLICY::CM_05B2",
    "SOURCE_PACK::CM_05B2"
  ],
  "effective_ui_widget_class": "READONLY_ENUM_BADGE",
  "effective_unit_or_basis": "downstream output basis",
  "effective_value_source_class": "QTT_CANONICAL_OUTPUT_BASIS_RULE",
  "evidence_basis_class": "FAMILY_SOURCE_PACK_PLUS_EXACT_OWNER_APPROVED_VALUE",
  "evidence_binding_rule_refs": [],
  "family_evidence_binding_ref": "ST12-FAMILY-EVIDENCE::CM_05B2",
  "implementation_resolution_kind": "OFFLINE_CALIBRATION_REQUIRED",
  "launch_computability_state": "EXECUTABLE_FAIL_CLOSED_UNTIL_CALIBRATION_RECEIPT",
  "master_plan_heading_path": [
    "Part II — Retained institutional design and parameter catalog",
    "D12. Canonical family registry — classical model families",
    "CM-05B2 — Classical gradient-boosting anchor atomic parameter pack and current-version deployment and binding specification"
  ],
  "master_plan_section_id": "CM-05B2",
  "missing_stale_invalid_behavior": "RETURN_BLOCKER_CALIBRATION_REQUIRED_NO_GUESSED_DEFAULT",
  "parameter_audit_id": "ST11-PARAM::00989",
  "parameter_id": "ST10-PARAM::0989",
  "parameter_symbol": "gb_out",
  "precision_and_rounding_policy": {
    "allowlist_check": "REQUIRED",
    "internal_numeric_type": "typed_symbolic",
    "normalization": "CANONICAL_EXACT_TOKEN_NO_FREE_TEXT_COERCION",
    "rounding": "NOT_APPLICABLE"
  },
  "runtime_resolution_procedure": [
    "Use the declared Day-1 seed when one exists and mark it SEED_NOT_VALIDATED.",
    "Fit or optimize only in REPLAY/PAPER research lanes using point-in-time data, purging/embargo when labels overlap, and a declared comparator.",
    "Search only the bounded space in bounded_search_space_or_fit_constraint; deterministic seed and full trial inventory are mandatory.",
    "No promotion follows from fit success alone; evidence and owner gates remain separate."
  ],
  "source_line_end": 37154,
  "source_line_start": 37143,
  "step12_primary_tranche_id": "ST12-TRANCHE-A"
},
{
  "canonical_owner": "QKUComputationControlPlaneV1",
  "certified_step11_custody_ref": "inputs/certified_step11/QTT_Stage1_Step11_Parameter_Policy_Adjudication_v1_0.jsonl#ST11-PARAM::01024",
  "certified_step11_row_embedded_in_prompt": false,
  "codex_online_research_allowed": false,
  "direct_source_claim_justifications": [],
  "effective_bounded_search_space_or_fit_constraint": "no promoted Kalman profile may omit an innovation-health monitor",
  "effective_day1_seed_value_or_resolution_rule": "STANDARDIZED_INNOVATION_AND_NIS_MONITOR_REQUIRED",
  "effective_default_authority_class": "PUBLIC_METHOD_OR_PINNED_PROVIDER_DEFAULT_REQUIRES_IMPLEMENTATION_VERSION_BINDING",
  "effective_fallback_behavior_when_value_unavailable": "FAIL_CLOSED_TO_REGISTERED_LOWER_SAFE_PATH_OR_NO_TRADE",
  "effective_owner_dashboard_editability_class": "READ_ONLY_SYMBOLIC",
  "effective_policy_authority": "CERTIFIED_STEP11_PARAMETER_POLICY",
  "effective_reference_range_or_structural_constraint": "{STANDARDIZED_INNOVATION_AND_NIS_MONITOR_REQUIRED, STANDARDIZED_INNOVATION_ONLY}",
  "effective_resolution_class": "STATIC_ENUM",
  "effective_source_state_refs": [
    "OWNER_POLICY::CM_11A",
    "SOURCE_PACK::CM_11A"
  ],
  "effective_ui_widget_class": "FORMULA_BADGE",
  "effective_unit_or_basis": "innovation-monitoring rule",
  "effective_value_source_class": "PUBLIC_STATE_SPACE_DIAGNOSTIC_REFERENCE_PLUS_QTT_STABILITY_RULE",
  "evidence_basis_class": "FAMILY_SOURCE_PACK_PLUS_EXACT_OWNER_APPROVED_VALUE",
  "evidence_binding_rule_refs": [],
  "family_evidence_binding_ref": "ST12-FAMILY-EVIDENCE::CM_11A",
  "implementation_resolution_kind": "STATIC_OR_DETERMINISTIC_RULE",
  "launch_computability_state": "COMPUTABLE_FROM_STATIC_VALUE_OR_DETERMINISTIC_RULE",
  "master_plan_heading_path": [
    "Part II — Retained institutional design and parameter catalog",
    "D12. Canonical family registry — classical model families",
    "CM-11A — State-space / Kalman atomic parameter pack and current-version deployment and binding specification"
  ],
  "master_plan_section_id": "CM-11A",
  "missing_stale_invalid_behavior": "REJECT_INVALID_VALUE_NO_SILENT_DEFAULT",
  "parameter_audit_id": "ST11-PARAM::01024",
  "parameter_id": "ST10-PARAM::1024",
  "parameter_symbol": "kf_innov",
  "precision_and_rounding_policy": {
    "allowlist_check": "REQUIRED",
    "internal_numeric_type": "typed_symbolic",
    "normalization": "CANONICAL_EXACT_TOKEN_NO_FREE_TEXT_COERCION",
    "rounding": "NOT_APPLICABLE"
  },
  "runtime_resolution_procedure": [
    "Parse the declared Day-1 seed or deterministic rule into the declared type.",
    "Validate against the reference range and structural constraint.",
    "Apply the declared bounded edit/search law; reject any value outside it."
  ],
  "source_line_end": 37745,
  "source_line_start": 37734,
  "step12_primary_tranche_id": "ST12-TRANCHE-A"
},
{
  "canonical_owner": "QKUComputationControlPlaneV1",
  "certified_step11_custody_ref": "inputs/certified_step11/QTT_Stage1_Step11_Parameter_Policy_Adjudication_v1_0.jsonl#ST11-PARAM::01125",
  "certified_step11_row_embedded_in_prompt": false,
  "codex_online_research_allowed": false,
  "direct_source_claim_justifications": [],
  "effective_bounded_search_space_or_fit_constraint": "singleton fit identity only in the current repository-authoritative baseline edition",
  "effective_day1_seed_value_or_resolution_rule": "GPD_MLE",
  "effective_default_authority_class": "PUBLIC_METHOD_OR_PINNED_PROVIDER_DEFAULT_REQUIRES_IMPLEMENTATION_VERSION_BINDING",
  "effective_fallback_behavior_when_value_unavailable": "FAIL_CLOSED_TO_REGISTERED_LOWER_SAFE_PATH_OR_NO_TRADE",
  "effective_owner_dashboard_editability_class": "OWNER_VISIBLE_NOT_EDITABLE",
  "effective_policy_authority": "CERTIFIED_STEP11_PARAMETER_POLICY",
  "effective_reference_range_or_structural_constraint": "`{GPD_MLE}` unless a later canonical master plan admits additional explicitly governed POT fit methods",
  "effective_resolution_class": "STATIC_ENUM",
  "effective_source_state_refs": [
    "OWNER_POLICY::CM_14B",
    "SOURCE_PACK::CM_14B"
  ],
  "effective_ui_widget_class": "READONLY_ENUM_BADGE",
  "effective_unit_or_basis": "tail-fit identity",
  "effective_value_source_class": "PUBLIC_LIBRARY_IMPLEMENTATION_BASIS",
  "evidence_basis_class": "FAMILY_SOURCE_PACK_PLUS_EXACT_OWNER_APPROVED_VALUE",
  "evidence_binding_rule_refs": [],
  "family_evidence_binding_ref": "ST12-FAMILY-EVIDENCE::CM_14B",
  "implementation_resolution_kind": "STATIC_OR_DETERMINISTIC_RULE",
  "launch_computability_state": "COMPUTABLE_FROM_STATIC_VALUE_OR_DETERMINISTIC_RULE",
  "master_plan_heading_path": [
    "Part II — Retained institutional design and parameter catalog",
    "D12. Canonical family registry — classical model families",
    "CM-14B — EVT / POT tail atomic parameter pack and current-version deployment and binding specification"
  ],
  "master_plan_section_id": "CM-14B",
  "missing_stale_invalid_behavior": "REJECT_INVALID_VALUE_NO_SILENT_DEFAULT",
  "parameter_audit_id": "ST11-PARAM::01125",
  "parameter_id": "ST10-PARAM::1125",
  "parameter_symbol": "evt_fit",
  "precision_and_rounding_policy": {
    "allowlist_check": "REQUIRED",
    "internal_numeric_type": "typed_symbolic",
    "normalization": "CANONICAL_EXACT_TOKEN_NO_FREE_TEXT_COERCION",
    "rounding": "NOT_APPLICABLE"
  },
  "runtime_resolution_procedure": [
    "Parse the declared Day-1 seed or deterministic rule into the declared type.",
    "Validate against the reference range and structural constraint.",
    "Apply the declared bounded edit/search law; reject any value outside it."
  ],
  "source_line_end": 39513,
  "source_line_start": 39502,
  "step12_primary_tranche_id": "ST12-TRANCHE-A"
},
{
  "canonical_owner": "QKUComputationControlPlaneV1",
  "certified_step11_custody_ref": "inputs/certified_step11/QTT_Stage1_Step11_Parameter_Policy_Adjudication_v1_0.jsonl#ST11-PARAM::01126",
  "certified_step11_row_embedded_in_prompt": false,
  "codex_online_research_allowed": false,
  "direct_source_claim_justifications": [],
  "effective_bounded_search_space_or_fit_constraint": "singleton basis only in the current repository-authoritative baseline edition",
  "effective_day1_seed_value_or_resolution_rule": "TAIL_INDEX_AND_GPD_SCALE_PLUS_EXCEEDANCE_RISK_METRICS",
  "effective_default_authority_class": "EXPLICIT_QTT_OR_OWNER_POLICY_SEED_OR_RESOLUTION_RULE",
  "effective_fallback_behavior_when_value_unavailable": "FAIL_CLOSED_TO_REGISTERED_LOWER_SAFE_PATH_OR_NO_TRADE",
  "effective_owner_dashboard_editability_class": "OWNER_VISIBLE_NOT_EDITABLE",
  "effective_policy_authority": "CERTIFIED_STEP11_PARAMETER_POLICY",
  "effective_reference_range_or_structural_constraint": "`{TAIL_INDEX_AND_GPD_SCALE_PLUS_EXCEEDANCE_RISK_METRICS}` unless a later canonical master plan adds an explicit alternative basis",
  "effective_resolution_class": "STATIC_ENUM",
  "effective_source_state_refs": [
    "OWNER_POLICY::CM_14B",
    "SOURCE_PACK::CM_14B"
  ],
  "effective_ui_widget_class": "READONLY_ENUM_BADGE",
  "effective_unit_or_basis": "tail-output basis",
  "effective_value_source_class": "QTT_CANONICAL_OUTPUT_BASIS_RULE",
  "evidence_basis_class": "FAMILY_SOURCE_PACK_PLUS_EXACT_OWNER_APPROVED_VALUE",
  "evidence_binding_rule_refs": [],
  "family_evidence_binding_ref": "ST12-FAMILY-EVIDENCE::CM_14B",
  "implementation_resolution_kind": "STATIC_OR_DETERMINISTIC_RULE",
  "launch_computability_state": "COMPUTABLE_FROM_STATIC_VALUE_OR_DETERMINISTIC_RULE",
  "master_plan_heading_path": [
    "Part II — Retained institutional design and parameter catalog",
    "D12. Canonical family registry — classical model families",
    "CM-14B — EVT / POT tail atomic parameter pack and current-version deployment and binding specification"
  ],
  "master_plan_section_id": "CM-14B",
  "missing_stale_invalid_behavior": "REJECT_INVALID_VALUE_NO_SILENT_DEFAULT",
  "parameter_audit_id": "ST11-PARAM::01126",
  "parameter_id": "ST10-PARAM::1126",
  "parameter_symbol": "evt_out",
  "precision_and_rounding_policy": {
    "allowlist_check": "REQUIRED",
    "internal_numeric_type": "typed_symbolic",
    "normalization": "CANONICAL_EXACT_TOKEN_NO_FREE_TEXT_COERCION",
    "rounding": "NOT_APPLICABLE"
  },
  "runtime_resolution_procedure": [
    "Parse the declared Day-1 seed or deterministic rule into the declared type.",
    "Validate against the reference range and structural constraint.",
    "Apply the declared bounded edit/search law; reject any value outside it."
  ],
  "source_line_end": 39525,
  "source_line_start": 39514,
  "step12_primary_tranche_id": "ST12-TRANCHE-A"
},
{
  "canonical_owner": "QKUComputationControlPlaneV1",
  "certified_step11_custody_ref": "inputs/certified_step11/QTT_Stage1_Step11_Parameter_Policy_Adjudication_v1_0.jsonl#ST11-PARAM::01132",
  "certified_step11_row_embedded_in_prompt": false,
  "codex_online_research_allowed": false,
  "direct_source_claim_justifications": [],
  "effective_bounded_search_space_or_fit_constraint": "rule only; no duplicate lambda surface is admissible here",
  "effective_day1_seed_value_or_resolution_rule": "CM-19F1.lambda_rm_when_cov_base == EWMA_RISKMETRICS else NONE",
  "effective_default_authority_class": "EXPLICIT_QTT_OR_OWNER_POLICY_SEED_OR_RESOLUTION_RULE",
  "effective_fallback_behavior_when_value_unavailable": "FAIL_CLOSED_TO_REGISTERED_LOWER_SAFE_PATH_OR_NO_TRADE",
  "effective_owner_dashboard_editability_class": "READ_ONLY_RULE_CARD",
  "effective_policy_authority": "CERTIFIED_STEP11_PARAMETER_POLICY",
  "effective_reference_range_or_structural_constraint": "{CM19F1_BINDING, NONE}",
  "effective_resolution_class": "STATIC_RULE_CARD",
  "effective_source_state_refs": [
    "OWNER_POLICY::CM_19A0",
    "SOURCE_PACK::CM_19A0"
  ],
  "effective_ui_widget_class": "READ_ONLY_RULE_CARD",
  "effective_unit_or_basis": "canonical-binding rule",
  "effective_value_source_class": "QTT_CANONICAL_SINGLE_PLACEMENT_RULE",
  "evidence_basis_class": "FAMILY_SOURCE_PACK_PLUS_EXACT_OWNER_APPROVED_VALUE",
  "evidence_binding_rule_refs": [],
  "family_evidence_binding_ref": "ST12-FAMILY-EVIDENCE::CM_19A0",
  "implementation_resolution_kind": "STATIC_OR_DETERMINISTIC_RULE",
  "launch_computability_state": "COMPUTABLE_FROM_STATIC_VALUE_OR_DETERMINISTIC_RULE",
  "master_plan_heading_path": [
    "Part II — Retained institutional design and parameter catalog",
    "D12. Canonical family registry — classical model families",
    "CM-19A0 — Empirical / Ledoit-Wolf / OAS / EWMA covariance atomic parameter pack"
  ],
  "master_plan_section_id": "CM-19A0",
  "missing_stale_invalid_behavior": "REJECT_INVALID_VALUE_NO_SILENT_DEFAULT",
  "parameter_audit_id": "ST11-PARAM::01132",
  "parameter_id": "ST10-PARAM::1132",
  "parameter_symbol": "ewma_bind_cov",
  "precision_and_rounding_policy": {
    "allowlist_check": "REQUIRED",
    "internal_numeric_type": "typed_symbolic",
    "normalization": "CANONICAL_EXACT_TOKEN_NO_FREE_TEXT_COERCION",
    "rounding": "NOT_APPLICABLE"
  },
  "runtime_resolution_procedure": [
    "Parse the declared Day-1 seed or deterministic rule into the declared type.",
    "Validate against the reference range and structural constraint.",
    "Apply the declared bounded edit/search law; reject any value outside it."
  ],
  "source_line_end": 39728,
  "source_line_start": 39717,
  "step12_primary_tranche_id": "ST12-TRANCHE-A"
},
{
  "canonical_owner": "QKUComputationControlPlaneV1",
  "certified_step11_custody_ref": "inputs/certified_step11/QTT_Stage1_Step11_Parameter_Policy_Adjudication_v1_0.jsonl#ST11-PARAM::01287",
  "certified_step11_row_embedded_in_prompt": false,
  "codex_online_research_allowed": false,
  "direct_source_claim_justifications": [],
  "effective_bounded_search_space_or_fit_constraint": "enum only",
  "effective_day1_seed_value_or_resolution_rule": "IRMV1",
  "effective_default_authority_class": "PUBLIC_METHOD_OR_PINNED_PROVIDER_DEFAULT_REQUIRES_IMPLEMENTATION_VERSION_BINDING",
  "effective_fallback_behavior_when_value_unavailable": "FAIL_CLOSED_TO_REGISTERED_LOWER_SAFE_PATH_OR_NO_TRADE",
  "effective_owner_dashboard_editability_class": "EDITABLE_WITH_SHADOW",
  "effective_policy_authority": "CERTIFIED_STEP11_PARAMETER_POLICY",
  "effective_reference_range_or_structural_constraint": "{IRMV1, ENVIRONMENT_SPLIT_CAUSAL_CHALLENGER, INVARIANT_FEATURE_SELECTION_COMPARATOR}",
  "effective_resolution_class": "STATIC_ENUM",
  "effective_source_state_refs": [
    "OWNER_POLICY::CM_28A5A",
    "SOURCE_PACK::CM_28A5A"
  ],
  "effective_ui_widget_class": "ENUM_DROPDOWN",
  "effective_unit_or_basis": "objective-family enum",
  "effective_value_source_class": "ACADEMIC_PUBLIC_REFERENCE",
  "evidence_basis_class": "FAMILY_SOURCE_PACK_PLUS_EXACT_OWNER_APPROVED_VALUE",
  "evidence_binding_rule_refs": [],
  "family_evidence_binding_ref": "ST12-FAMILY-EVIDENCE::CM_28A5A",
  "implementation_resolution_kind": "STATIC_OR_DETERMINISTIC_RULE",
  "launch_computability_state": "COMPUTABLE_FROM_STATIC_VALUE_OR_DETERMINISTIC_RULE",
  "master_plan_heading_path": [
    "Part II — Retained institutional design and parameter catalog",
    "D12. Canonical family registry — classical model families",
    "CM-28A5A — Causal and invariance challenger atomic parameter pack"
  ],
  "master_plan_section_id": "CM-28A5A",
  "missing_stale_invalid_behavior": "REJECT_INVALID_VALUE_NO_SILENT_DEFAULT",
  "parameter_audit_id": "ST11-PARAM::01287",
  "parameter_id": "ST10-PARAM::1287",
  "parameter_symbol": "obj_inv",
  "precision_and_rounding_policy": {
    "allowlist_check": "REQUIRED",
    "internal_numeric_type": "typed_symbolic",
    "normalization": "CANONICAL_EXACT_TOKEN_NO_FREE_TEXT_COERCION",
    "rounding": "NOT_APPLICABLE"
  },
  "runtime_resolution_procedure": [
    "Parse the declared Day-1 seed or deterministic rule into the declared type.",
    "Validate against the reference range and structural constraint.",
    "Apply the declared bounded edit/search law; reject any value outside it."
  ],
  "source_line_end": 42520,
  "source_line_start": 42509,
  "step12_primary_tranche_id": "ST12-TRANCHE-A"
},
{
  "canonical_owner": "QKUComputationControlPlaneV1",
  "certified_step11_custody_ref": "inputs/certified_step11/QTT_Stage1_Step11_Parameter_Policy_Adjudication_v1_0.jsonl#ST11-PARAM::01288",
  "certified_step11_row_embedded_in_prompt": false,
  "codex_online_research_allowed": false,
  "direct_source_claim_justifications": [],
  "effective_bounded_search_space_or_fit_constraint": "integer search `2..10`",
  "effective_day1_seed_value_or_resolution_rule": "2",
  "effective_default_authority_class": "PUBLIC_METHOD_OR_PINNED_PROVIDER_DEFAULT_REQUIRES_IMPLEMENTATION_VERSION_BINDING",
  "effective_fallback_behavior_when_value_unavailable": "FAIL_CLOSED_TO_REGISTERED_LOWER_SAFE_PATH_OR_NO_TRADE",
  "effective_owner_dashboard_editability_class": "CONDITIONALLY_EDITABLE_WITH_SHADOW",
  "effective_policy_authority": "CERTIFIED_STEP11_PARAMETER_POLICY",
  "effective_reference_range_or_structural_constraint": "integer in `2..10`",
  "effective_resolution_class": "STATIC_INTEGER",
  "effective_source_state_refs": [
    "OWNER_POLICY::CM_28A5A",
    "SOURCE_PACK::CM_28A5A"
  ],
  "effective_ui_widget_class": "INTEGER_STEPPER",
  "effective_unit_or_basis": "environment count",
  "effective_value_source_class": "ACADEMIC_PUBLIC_REFERENCE",
  "evidence_basis_class": "FAMILY_SOURCE_PACK_PLUS_EXACT_OWNER_APPROVED_VALUE",
  "evidence_binding_rule_refs": [],
  "family_evidence_binding_ref": "ST12-FAMILY-EVIDENCE::CM_28A5A",
  "implementation_resolution_kind": "STATIC_OR_DETERMINISTIC_RULE",
  "launch_computability_state": "COMPUTABLE_FROM_STATIC_VALUE_OR_DETERMINISTIC_RULE",
  "master_plan_heading_path": [
    "Part II — Retained institutional design and parameter catalog",
    "D12. Canonical family registry — classical model families",
    "CM-28A5A — Causal and invariance challenger atomic parameter pack"
  ],
  "master_plan_section_id": "CM-28A5A",
  "missing_stale_invalid_behavior": "REJECT_INVALID_VALUE_NO_SILENT_DEFAULT",
  "parameter_audit_id": "ST11-PARAM::01288",
  "parameter_id": "ST10-PARAM::1288",
  "parameter_symbol": "N_env_min",
  "precision_and_rounding_policy": {
    "bounds_check": "REQUIRED",
    "internal_numeric_type": "int",
    "rounding": "NOT_APPLICABLE"
  },
  "runtime_resolution_procedure": [
    "Parse the declared Day-1 seed or deterministic rule into the declared type.",
    "Validate against the reference range and structural constraint.",
    "Apply the declared bounded edit/search law; reject any value outside it."
  ],
  "source_line_end": 42532,
  "source_line_start": 42521,
  "step12_primary_tranche_id": "ST12-TRANCHE-A"
},
{
  "canonical_owner": "QKUComputationControlPlaneV1",
  "certified_step11_custody_ref": "inputs/certified_step11/QTT_Stage1_Step11_Parameter_Policy_Adjudication_v1_0.jsonl#ST11-PARAM::01289",
  "certified_step11_row_embedded_in_prompt": false,
  "codex_online_research_allowed": false,
  "direct_source_claim_justifications": [],
  "effective_bounded_search_space_or_fit_constraint": "integer search `{50,150,190}`",
  "effective_day1_seed_value_or_resolution_rule": "50",
  "effective_default_authority_class": "PUBLIC_METHOD_OR_PINNED_PROVIDER_DEFAULT_REQUIRES_IMPLEMENTATION_VERSION_BINDING",
  "effective_fallback_behavior_when_value_unavailable": "FAIL_CLOSED_TO_REGISTERED_LOWER_SAFE_PATH_OR_NO_TRADE",
  "effective_owner_dashboard_editability_class": "EDITABLE_WITH_SHADOW",
  "effective_policy_authority": "CERTIFIED_STEP11_PARAMETER_POLICY",
  "effective_reference_range_or_structural_constraint": "positive integer",
  "effective_resolution_class": "STATIC_INTEGER",
  "effective_source_state_refs": [
    "OWNER_POLICY::CM_28A5A",
    "SOURCE_PACK::CM_28A5A"
  ],
  "effective_ui_widget_class": "INTEGER_STEPPER",
  "effective_unit_or_basis": "optimization iterations",
  "effective_value_source_class": "PUBLIC_BENCHMARK_IMPLEMENTATION_PRACTICE",
  "evidence_basis_class": "FAMILY_SOURCE_PACK_PLUS_EXACT_OWNER_APPROVED_VALUE",
  "evidence_binding_rule_refs": [],
  "family_evidence_binding_ref": "ST12-FAMILY-EVIDENCE::CM_28A5A",
  "implementation_resolution_kind": "STATIC_OR_DETERMINISTIC_RULE",
  "launch_computability_state": "COMPUTABLE_FROM_STATIC_VALUE_OR_DETERMINISTIC_RULE",
  "master_plan_heading_path": [
    "Part II — Retained institutional design and parameter catalog",
    "D12. Canonical family registry — classical model families",
    "CM-28A5A — Causal and invariance challenger atomic parameter pack"
  ],
  "master_plan_section_id": "CM-28A5A",
  "missing_stale_invalid_behavior": "REJECT_INVALID_VALUE_NO_SILENT_DEFAULT",
  "parameter_audit_id": "ST11-PARAM::01289",
  "parameter_id": "ST10-PARAM::1289",
  "parameter_symbol": "T_anneal",
  "precision_and_rounding_policy": {
    "bounds_check": "REQUIRED",
    "internal_numeric_type": "int",
    "rounding": "NOT_APPLICABLE"
  },
  "runtime_resolution_procedure": [
    "Parse the declared Day-1 seed or deterministic rule into the declared type.",
    "Validate against the reference range and structural constraint.",
    "Apply the declared bounded edit/search law; reject any value outside it."
  ],
  "source_line_end": 42544,
  "source_line_start": 42533,
  "step12_primary_tranche_id": "ST12-TRANCHE-A"
},
{
  "canonical_owner": "QKUComputationControlPlaneV1",
  "certified_step11_custody_ref": "inputs/certified_step11/QTT_Stage1_Step11_Parameter_Policy_Adjudication_v1_0.jsonl#ST11-PARAM::01290",
  "certified_step11_row_embedded_in_prompt": false,
  "codex_online_research_allowed": false,
  "direct_source_claim_justifications": [],
  "effective_bounded_search_space_or_fit_constraint": "{1e-2,1e-1,1,1e1}",
  "effective_day1_seed_value_or_resolution_rule": "GRID_SEARCH_OVER_{1e-2,1e-1,1,1e1}_UNDER_CPCV_AND_OOD_COMPARATOR_RULES",
  "effective_default_authority_class": "PUBLIC_METHOD_OR_PINNED_PROVIDER_DEFAULT_REQUIRES_IMPLEMENTATION_VERSION_BINDING",
  "effective_fallback_behavior_when_value_unavailable": "FAIL_CLOSED_TO_REGISTERED_LOWER_SAFE_PATH_OR_NO_TRADE",
  "effective_owner_dashboard_editability_class": "EDITABLE_WITH_SHADOW",
  "effective_policy_authority": "CERTIFIED_STEP11_PARAMETER_POLICY",
  "effective_reference_range_or_structural_constraint": "positive scalar",
  "effective_resolution_class": "STATIC_NUMERIC_OR_GRID_RULE",
  "effective_source_state_refs": [
    "OWNER_POLICY::CM_28A5A",
    "SOURCE_PACK::CM_28A5A"
  ],
  "effective_ui_widget_class": "LOG_GRID_SELECTOR",
  "effective_unit_or_basis": "penalty-weight scalar",
  "effective_value_source_class": "ACADEMIC_PUBLIC_REFERENCE_AND_PUBLIC_BENCHMARK_PRACTICE",
  "evidence_basis_class": "FAMILY_SOURCE_PACK_PLUS_EXACT_OWNER_APPROVED_VALUE",
  "evidence_binding_rule_refs": [],
  "family_evidence_binding_ref": "ST12-FAMILY-EVIDENCE::CM_28A5A",
  "implementation_resolution_kind": "STATIC_OR_DETERMINISTIC_RULE",
  "launch_computability_state": "COMPUTABLE_FROM_STATIC_VALUE_OR_DETERMINISTIC_RULE",
  "master_plan_heading_path": [
    "Part II — Retained institutional design and parameter catalog",
    "D12. Canonical family registry — classical model families",
    "CM-28A5A — Causal and invariance challenger atomic parameter pack"
  ],
  "master_plan_section_id": "CM-28A5A",
  "missing_stale_invalid_behavior": "REJECT_INVALID_VALUE_NO_SILENT_DEFAULT",
  "parameter_audit_id": "ST11-PARAM::01290",
  "parameter_id": "ST10-PARAM::1290",
  "parameter_symbol": "lambda_irm",
  "precision_and_rounding_policy": {
    "finite_check": "REQUIRED",
    "internal_numeric_type": "float64_or_declared_array_dtype",
    "probability_domain": "[0,1] WHEN APPLICABLE",
    "rounding": "NONE_INTERNAL; CONVERT_TO_DECIMAL_AT_FINANCIAL_BOUNDARY"
  },
  "runtime_resolution_procedure": [
    "Parse the declared Day-1 seed or deterministic rule into the declared type.",
    "Validate against the reference range and structural constraint.",
    "Apply the declared bounded edit/search law; reject any value outside it."
  ],
  "source_line_end": 42557,
  "source_line_start": 42545,
  "step12_primary_tranche_id": "ST12-TRANCHE-A"
},
{
  "canonical_owner": "QKUComputationControlPlaneV1",
  "certified_step11_custody_ref": "inputs/certified_step11/QTT_Stage1_Step11_Parameter_Policy_Adjudication_v1_0.jsonl#ST11-PARAM::01291",
  "certified_step11_row_embedded_in_prompt": false,
  "codex_online_research_allowed": false,
  "direct_source_claim_justifications": [],
  "effective_bounded_search_space_or_fit_constraint": "enum only",
  "effective_day1_seed_value_or_resolution_rule": "EXPECTED_INFORMATION_GAIN",
  "effective_default_authority_class": "PUBLIC_METHOD_OR_PINNED_PROVIDER_DEFAULT_REQUIRES_IMPLEMENTATION_VERSION_BINDING",
  "effective_fallback_behavior_when_value_unavailable": "FAIL_CLOSED_TO_REGISTERED_LOWER_SAFE_PATH_OR_NO_TRADE",
  "effective_owner_dashboard_editability_class": "EDITABLE_WITH_SHADOW",
  "effective_policy_authority": "CERTIFIED_STEP11_PARAMETER_POLICY",
  "effective_reference_range_or_structural_constraint": "{EXPECTED_INFORMATION_GAIN,ROBUST_EXPECTED_INFORMATION_GAIN}",
  "effective_resolution_class": "STATIC_ENUM",
  "effective_source_state_refs": [
    "OWNER_POLICY::CM_28A6A",
    "SOURCE_PACK::CM_28A6A"
  ],
  "effective_ui_widget_class": "ENUM_DROPDOWN",
  "effective_unit_or_basis": "objective-family enum",
  "effective_value_source_class": "ACADEMIC_PUBLIC_REFERENCE",
  "evidence_basis_class": "FAMILY_SOURCE_PACK_PLUS_EXACT_OWNER_APPROVED_VALUE",
  "evidence_binding_rule_refs": [],
  "family_evidence_binding_ref": "ST12-FAMILY-EVIDENCE::CM_28A6A",
  "implementation_resolution_kind": "STATIC_OR_DETERMINISTIC_RULE",
  "launch_computability_state": "COMPUTABLE_FROM_STATIC_VALUE_OR_DETERMINISTIC_RULE",
  "master_plan_heading_path": [
    "Part II — Retained institutional design and parameter catalog",
    "D12. Canonical family registry — classical model families",
    "CM-28A6A — Expected-information-gain scheduler atomic parameter pack"
  ],
  "master_plan_section_id": "CM-28A6A",
  "missing_stale_invalid_behavior": "REJECT_INVALID_VALUE_NO_SILENT_DEFAULT",
  "parameter_audit_id": "ST11-PARAM::01291",
  "parameter_id": "ST10-PARAM::1291",
  "parameter_symbol": "obj_eig",
  "precision_and_rounding_policy": {
    "allowlist_check": "REQUIRED",
    "internal_numeric_type": "typed_symbolic",
    "normalization": "CANONICAL_EXACT_TOKEN_NO_FREE_TEXT_COERCION",
    "rounding": "NOT_APPLICABLE"
  },
  "runtime_resolution_procedure": [
    "Parse the declared Day-1 seed or deterministic rule into the declared type.",
    "Validate against the reference range and structural constraint.",
    "Apply the declared bounded edit/search law; reject any value outside it."
  ],
  "source_line_end": 42588,
  "source_line_start": 42577,
  "step12_primary_tranche_id": "ST12-TRANCHE-A"
},
{
  "canonical_owner": "QKUComputationControlPlaneV1",
  "certified_step11_custody_ref": "inputs/certified_step11/QTT_Stage1_Step11_Parameter_Policy_Adjudication_v1_0.jsonl#ST11-PARAM::01292",
  "certified_step11_row_embedded_in_prompt": false,
  "codex_online_research_allowed": false,
  "direct_source_claim_justifications": [],
  "effective_bounded_search_space_or_fit_constraint": "enum only",
  "effective_day1_seed_value_or_resolution_rule": "NESTED_MONTE_CARLO",
  "effective_default_authority_class": "PUBLIC_METHOD_OR_PINNED_PROVIDER_DEFAULT_REQUIRES_IMPLEMENTATION_VERSION_BINDING",
  "effective_fallback_behavior_when_value_unavailable": "FAIL_CLOSED_TO_REGISTERED_LOWER_SAFE_PATH_OR_NO_TRADE",
  "effective_owner_dashboard_editability_class": "EDITABLE_WITH_SHADOW",
  "effective_policy_authority": "CERTIFIED_STEP11_PARAMETER_POLICY",
  "effective_reference_range_or_structural_constraint": "{NESTED_MONTE_CARLO,VARIATIONAL_NESTED_MONTE_CARLO,LOWER_BOUND_APPROXIMATION}",
  "effective_resolution_class": "STATIC_ENUM",
  "effective_source_state_refs": [
    "OWNER_POLICY::CM_28A6A",
    "SOURCE_PACK::CM_28A6A"
  ],
  "effective_ui_widget_class": "ENUM_DROPDOWN",
  "effective_unit_or_basis": "estimator-family enum",
  "effective_value_source_class": "ACADEMIC_PUBLIC_REFERENCE",
  "evidence_basis_class": "FAMILY_SOURCE_PACK_PLUS_EXACT_OWNER_APPROVED_VALUE",
  "evidence_binding_rule_refs": [],
  "family_evidence_binding_ref": "ST12-FAMILY-EVIDENCE::CM_28A6A",
  "implementation_resolution_kind": "STATIC_OR_DETERMINISTIC_RULE",
  "launch_computability_state": "COMPUTABLE_FROM_STATIC_VALUE_OR_DETERMINISTIC_RULE",
  "master_plan_heading_path": [
    "Part II — Retained institutional design and parameter catalog",
    "D12. Canonical family registry — classical model families",
    "CM-28A6A — Expected-information-gain scheduler atomic parameter pack"
  ],
  "master_plan_section_id": "CM-28A6A",
  "missing_stale_invalid_behavior": "REJECT_INVALID_VALUE_NO_SILENT_DEFAULT",
  "parameter_audit_id": "ST11-PARAM::01292",
  "parameter_id": "ST10-PARAM::1292",
  "parameter_symbol": "eig_est",
  "precision_and_rounding_policy": {
    "allowlist_check": "REQUIRED",
    "internal_numeric_type": "typed_symbolic",
    "normalization": "CANONICAL_EXACT_TOKEN_NO_FREE_TEXT_COERCION",
    "rounding": "NOT_APPLICABLE"
  },
  "runtime_resolution_procedure": [
    "Parse the declared Day-1 seed or deterministic rule into the declared type.",
    "Validate against the reference range and structural constraint.",
    "Apply the declared bounded edit/search law; reject any value outside it."
  ],
  "source_line_end": 42600,
  "source_line_start": 42589,
  "step12_primary_tranche_id": "ST12-TRANCHE-A"
},
{
  "canonical_owner": "QKUComputationControlPlaneV1",
  "certified_step11_custody_ref": "inputs/certified_step11/QTT_Stage1_Step11_Parameter_Policy_Adjudication_v1_0.jsonl#ST11-PARAM::01293",
  "certified_step11_row_embedded_in_prompt": false,
  "codex_online_research_allowed": false,
  "direct_source_claim_justifications": [],
  "effective_bounded_search_space_or_fit_constraint": "enum menu only",
  "effective_day1_seed_value_or_resolution_rule": "TOP_3",
  "effective_default_authority_class": "EXPLICIT_QTT_OR_OWNER_POLICY_SEED_OR_RESOLUTION_RULE",
  "effective_fallback_behavior_when_value_unavailable": "FAIL_CLOSED_TO_REGISTERED_LOWER_SAFE_PATH_OR_NO_TRADE",
  "effective_owner_dashboard_editability_class": "EDITABLE_WITH_SHADOW",
  "effective_policy_authority": "CERTIFIED_STEP11_PARAMETER_POLICY",
  "effective_reference_range_or_structural_constraint": "{TOP_1,TOP_3,TOP_5,TOP_10}",
  "effective_resolution_class": "STATIC_INTEGER_OR_ENUM",
  "effective_source_state_refs": [
    "OWNER_POLICY::CM_28A6A",
    "SOURCE_PACK::CM_28A6A"
  ],
  "effective_ui_widget_class": "ENUM_DROPDOWN",
  "effective_unit_or_basis": "scheduled-candidate-count enum",
  "effective_value_source_class": "QTT_CANONICAL_RESEARCH_BUDGET_POLICY",
  "evidence_basis_class": "FAMILY_SOURCE_PACK_PLUS_EXACT_OWNER_APPROVED_VALUE",
  "evidence_binding_rule_refs": [],
  "family_evidence_binding_ref": "ST12-FAMILY-EVIDENCE::CM_28A6A",
  "implementation_resolution_kind": "STATIC_OR_DETERMINISTIC_RULE",
  "launch_computability_state": "COMPUTABLE_FROM_STATIC_VALUE_OR_DETERMINISTIC_RULE",
  "master_plan_heading_path": [
    "Part II — Retained institutional design and parameter catalog",
    "D12. Canonical family registry — classical model families",
    "CM-28A6A — Expected-information-gain scheduler atomic parameter pack"
  ],
  "master_plan_section_id": "CM-28A6A",
  "missing_stale_invalid_behavior": "REJECT_INVALID_VALUE_NO_SILENT_DEFAULT",
  "parameter_audit_id": "ST11-PARAM::01293",
  "parameter_id": "ST10-PARAM::1293",
  "parameter_symbol": "K_sched",
  "precision_and_rounding_policy": {
    "allowlist_check": "REQUIRED",
    "internal_numeric_type": "typed_symbolic",
    "normalization": "CANONICAL_EXACT_TOKEN_NO_FREE_TEXT_COERCION",
    "rounding": "NOT_APPLICABLE"
  },
  "runtime_resolution_procedure": [
    "Parse the declared Day-1 seed or deterministic rule into the declared type.",
    "Validate against the reference range and structural constraint.",
    "Apply the declared bounded edit/search law; reject any value outside it."
  ],
  "source_line_end": 42612,
  "source_line_start": 42601,
  "step12_primary_tranche_id": "ST12-TRANCHE-A"
},
{
  "canonical_owner": "QKUComputationControlPlaneV1",
  "certified_step11_custody_ref": "inputs/certified_step11/QTT_Stage1_Step11_Parameter_Policy_Adjudication_v1_0.jsonl#ST11-PARAM::01422",
  "certified_step11_row_embedded_in_prompt": false,
  "codex_online_research_allowed": false,
  "direct_source_claim_justifications": [],
  "effective_bounded_search_space_or_fit_constraint": "no free scalar override; basis conversion must remain explicit",
  "effective_day1_seed_value_or_resolution_rule": "`trade_only_if_p > 1/(b+1)` on binary payoff-ratio basis, or exact declared equivalent on the chosen payoff basis",
  "effective_default_authority_class": "PUBLIC_METHOD_OR_PINNED_PROVIDER_DEFAULT_REQUIRES_IMPLEMENTATION_VERSION_BINDING",
  "effective_fallback_behavior_when_value_unavailable": "FAIL_CLOSED_TO_REGISTERED_LOWER_SAFE_PATH_OR_NO_TRADE",
  "effective_owner_dashboard_editability_class": "VIEW_ONLY_RESOLVED",
  "effective_policy_authority": "CERTIFIED_STEP11_PARAMETER_POLICY",
  "effective_reference_range_or_structural_constraint": "strict inequality on the declared breakeven probability basis",
  "effective_resolution_class": "STRUCTURAL_FORMULA_RULE",
  "effective_source_state_refs": [
    "OWNER_POLICY::RA_01A",
    "SOURCE_PACK::RA_01A"
  ],
  "effective_ui_widget_class": "FORMULA_BADGE",
  "effective_unit_or_basis": "breakeven-probability inequality",
  "effective_value_source_class": "ACADEMIC_PUBLIC_REFERENCE",
  "evidence_basis_class": "FAMILY_SOURCE_PACK_PLUS_EXACT_OWNER_APPROVED_VALUE",
  "evidence_binding_rule_refs": [],
  "family_evidence_binding_ref": "ST12-FAMILY-EVIDENCE::RA_01A",
  "implementation_resolution_kind": "STATIC_OR_DETERMINISTIC_RULE",
  "launch_computability_state": "COMPUTABLE_FROM_STATIC_VALUE_OR_DETERMINISTIC_RULE",
  "master_plan_heading_path": [
    "Part II — Retained institutional design and parameter catalog",
    "D14. Canonical family registry — risk and allocation",
    "RA-01A — Kelly sizing atomic parameter pack"
  ],
  "master_plan_section_id": "RA-01A",
  "missing_stale_invalid_behavior": "REJECT_INVALID_VALUE_NO_SILENT_DEFAULT",
  "parameter_audit_id": "ST11-PARAM::01422",
  "parameter_id": "ST10-PARAM::1422",
  "parameter_symbol": "p_gt_p_star",
  "precision_and_rounding_policy": {
    "allowlist_check": "REQUIRED",
    "internal_numeric_type": "typed_symbolic",
    "normalization": "CANONICAL_EXACT_TOKEN_NO_FREE_TEXT_COERCION",
    "rounding": "NOT_APPLICABLE"
  },
  "runtime_resolution_procedure": [
    "Parse the declared Day-1 seed or deterministic rule into the declared type.",
    "Validate against the reference range and structural constraint.",
    "Apply the declared bounded edit/search law; reject any value outside it."
  ],
  "source_line_end": 45153,
  "source_line_start": 45142,
  "step12_primary_tranche_id": "ST12-TRANCHE-A"
},
{
  "canonical_owner": "QKUComputationControlPlaneV1",
  "certified_step11_custody_ref": "inputs/certified_step11/QTT_Stage1_Step11_Parameter_Policy_Adjudication_v1_0.jsonl#ST11-PARAM::01423",
  "certified_step11_row_embedded_in_prompt": false,
  "codex_online_research_allowed": false,
  "direct_source_claim_justifications": [],
  "effective_bounded_search_space_or_fit_constraint": "derived from the currently approved live risk envelope only",
  "effective_day1_seed_value_or_resolution_rule": "min(fractional_kelly_output, assisted_live_per_trade_risk_cap_from_2_24)",
  "effective_default_authority_class": "EXPLICIT_QTT_OR_OWNER_POLICY_SEED_OR_RESOLUTION_RULE",
  "effective_fallback_behavior_when_value_unavailable": "FAIL_CLOSED_TO_REGISTERED_LOWER_SAFE_PATH_OR_NO_TRADE",
  "effective_owner_dashboard_editability_class": "READ_ONLY_GOVERNANCE_BOUND",
  "effective_policy_authority": "CERTIFIED_STEP11_PARAMETER_POLICY",
  "effective_reference_range_or_structural_constraint": "non-negative and never above the currently approved live risk cap",
  "effective_resolution_class": "RISK_POLICY_DERIVED",
  "effective_source_state_refs": [
    "OWNER_POLICY::RA_01A",
    "SOURCE_PACK::RA_01A"
  ],
  "effective_ui_widget_class": "READ_ONLY_FORMULA_FIELD",
  "effective_unit_or_basis": "fraction of approved live risk budget",
  "effective_value_source_class": "QTT_INTERNAL_VALIDATED_DEFAULT",
  "evidence_basis_class": "FAMILY_SOURCE_PACK_PLUS_EXACT_OWNER_APPROVED_VALUE",
  "evidence_binding_rule_refs": [],
  "family_evidence_binding_ref": "ST12-FAMILY-EVIDENCE::RA_01A",
  "implementation_resolution_kind": "STATIC_OR_DETERMINISTIC_RULE",
  "launch_computability_state": "COMPUTABLE_FROM_STATIC_VALUE_OR_DETERMINISTIC_RULE",
  "master_plan_heading_path": [
    "Part II — Retained institutional design and parameter catalog",
    "D14. Canonical family registry — risk and allocation",
    "RA-01A — Kelly sizing atomic parameter pack"
  ],
  "master_plan_section_id": "RA-01A",
  "missing_stale_invalid_behavior": "REJECT_INVALID_VALUE_NO_SILENT_DEFAULT",
  "parameter_audit_id": "ST11-PARAM::01423",
  "parameter_id": "ST10-PARAM::1423",
  "parameter_symbol": "r_live_cap",
  "precision_and_rounding_policy": {
    "decimal_context_precision": 34,
    "internal_numeric_type": "Decimal",
    "nonfinite_policy": "REJECT",
    "quantization": "SOURCE_OR_UNIT_DECLARED; NO_IMPLICIT_BINARY_FLOAT_CONVERSION",
    "rounding": "ROUND_HALF_EVEN"
  },
  "runtime_resolution_procedure": [
    "Parse the declared Day-1 seed or deterministic rule into the declared type.",
    "Validate against the reference range and structural constraint.",
    "Apply the declared bounded edit/search law; reject any value outside it."
  ],
  "source_line_end": 45165,
  "source_line_start": 45154,
  "step12_primary_tranche_id": "ST12-TRANCHE-A"
},
{
  "canonical_owner": "QKUComputationControlPlaneV1",
  "certified_step11_custody_ref": "inputs/certified_step11/QTT_Stage1_Step11_Parameter_Policy_Adjudication_v1_0.jsonl#ST11-PARAM::01448",
  "certified_step11_row_embedded_in_prompt": false,
  "codex_online_research_allowed": false,
  "direct_source_claim_justifications": [],
  "effective_bounded_search_space_or_fit_constraint": "enum only; any non-quasi-diagonalized order requires an explicit equivalence receipt versus the canonical HRP ordering law",
  "effective_day1_seed_value_or_resolution_rule": "QUASI_DIAGONALIZED_TREE_ORDER",
  "effective_default_authority_class": "PUBLIC_METHOD_OR_PINNED_PROVIDER_DEFAULT_REQUIRES_IMPLEMENTATION_VERSION_BINDING",
  "effective_fallback_behavior_when_value_unavailable": "FAIL_CLOSED_TO_REGISTERED_LOWER_SAFE_PATH_OR_NO_TRADE",
  "effective_owner_dashboard_editability_class": "VIEW_ONLY_RESOLVED",
  "effective_policy_authority": "CERTIFIED_STEP11_PARAMETER_POLICY",
  "effective_reference_range_or_structural_constraint": "{QUASI_DIAGONALIZED_TREE_ORDER, LIBRARY_NATIVE_EQUIVALENT_IF_RECEIPT_EQUIVALENCE_PROVED}",
  "effective_resolution_class": "STATIC_ENUM",
  "effective_source_state_refs": [
    "OWNER_POLICY::RA_08H1",
    "SOURCE_PACK::RA_08H1"
  ],
  "effective_ui_widget_class": "ENUM_BADGE",
  "effective_unit_or_basis": "leaf-order-family enum",
  "effective_value_source_class": "PUBLIC_HIERARCHICAL_PORTFOLIO_METHOD_REFERENCE_WITH_QTT_CANONICALIZATION",
  "evidence_basis_class": "FAMILY_SOURCE_PACK_PLUS_EXACT_OWNER_APPROVED_VALUE",
  "evidence_binding_rule_refs": [],
  "family_evidence_binding_ref": "ST12-FAMILY-EVIDENCE::RA_08H1",
  "implementation_resolution_kind": "STATIC_OR_DETERMINISTIC_RULE",
  "launch_computability_state": "COMPUTABLE_FROM_STATIC_VALUE_OR_DETERMINISTIC_RULE",
  "master_plan_heading_path": [
    "Part II — Retained institutional design and parameter catalog",
    "D14. Canonical family registry — risk and allocation",
    "RA-08H1 — Hierarchical risk parity atomic parameter pack and current-version deployment and binding specification"
  ],
  "master_plan_section_id": "RA-08H1",
  "missing_stale_invalid_behavior": "REJECT_INVALID_VALUE_NO_SILENT_DEFAULT",
  "parameter_audit_id": "ST11-PARAM::01448",
  "parameter_id": "ST10-PARAM::1448",
  "parameter_symbol": "leaf_hrp",
  "precision_and_rounding_policy": {
    "allowlist_check": "REQUIRED",
    "internal_numeric_type": "typed_symbolic",
    "normalization": "CANONICAL_EXACT_TOKEN_NO_FREE_TEXT_COERCION",
    "rounding": "NOT_APPLICABLE"
  },
  "runtime_resolution_procedure": [
    "Parse the declared Day-1 seed or deterministic rule into the declared type.",
    "Validate against the reference range and structural constraint.",
    "Apply the declared bounded edit/search law; reject any value outside it."
  ],
  "source_line_end": 45625,
  "source_line_start": 45614,
  "step12_primary_tranche_id": "ST12-TRANCHE-A"
},
{
  "canonical_owner": "QKUComputationControlPlaneV1",
  "certified_step11_custody_ref": "inputs/certified_step11/QTT_Stage1_Step11_Parameter_Policy_Adjudication_v1_0.jsonl#ST11-PARAM::01449",
  "certified_step11_row_embedded_in_prompt": false,
  "codex_online_research_allowed": false,
  "direct_source_claim_justifications": [],
  "effective_bounded_search_space_or_fit_constraint": "fixed canonical Day-1 HRP rule only unless a later admitted hierarchical-family upgrade materializes a different public split law separately",
  "effective_day1_seed_value_or_resolution_rule": "INVERSE_CLUSTER_VARIANCE_SPLIT",
  "effective_default_authority_class": "PUBLIC_METHOD_OR_PINNED_PROVIDER_DEFAULT_REQUIRES_IMPLEMENTATION_VERSION_BINDING",
  "effective_fallback_behavior_when_value_unavailable": "FAIL_CLOSED_TO_REGISTERED_LOWER_SAFE_PATH_OR_NO_TRADE",
  "effective_owner_dashboard_editability_class": "VIEW_ONLY_RESOLVED",
  "effective_policy_authority": "CERTIFIED_STEP11_PARAMETER_POLICY",
  "effective_reference_range_or_structural_constraint": "{INVERSE_CLUSTER_VARIANCE_SPLIT}",
  "effective_resolution_class": "STATIC_ENUM",
  "effective_source_state_refs": [
    "OWNER_POLICY::RA_08H1",
    "SOURCE_PACK::RA_08H1"
  ],
  "effective_ui_widget_class": "READ_ONLY_RULE_CARD",
  "effective_unit_or_basis": "recursive-bisection variance-split rule",
  "effective_value_source_class": "PUBLIC_HIERARCHICAL_PORTFOLIO_METHOD_REFERENCE_WITH_QTT_CANONICALIZATION",
  "evidence_basis_class": "FAMILY_SOURCE_PACK_PLUS_EXACT_OWNER_APPROVED_VALUE",
  "evidence_binding_rule_refs": [],
  "family_evidence_binding_ref": "ST12-FAMILY-EVIDENCE::RA_08H1",
  "implementation_resolution_kind": "STATIC_OR_DETERMINISTIC_RULE",
  "launch_computability_state": "COMPUTABLE_FROM_STATIC_VALUE_OR_DETERMINISTIC_RULE",
  "master_plan_heading_path": [
    "Part II — Retained institutional design and parameter catalog",
    "D14. Canonical family registry — risk and allocation",
    "RA-08H1 — Hierarchical risk parity atomic parameter pack and current-version deployment and binding specification"
  ],
  "master_plan_section_id": "RA-08H1",
  "missing_stale_invalid_behavior": "REJECT_INVALID_VALUE_NO_SILENT_DEFAULT",
  "parameter_audit_id": "ST11-PARAM::01449",
  "parameter_id": "ST10-PARAM::1449",
  "parameter_symbol": "varsplit_hrp",
  "precision_and_rounding_policy": {
    "allowlist_check": "REQUIRED",
    "internal_numeric_type": "typed_symbolic",
    "normalization": "CANONICAL_EXACT_TOKEN_NO_FREE_TEXT_COERCION",
    "rounding": "NOT_APPLICABLE"
  },
  "runtime_resolution_procedure": [
    "Parse the declared Day-1 seed or deterministic rule into the declared type.",
    "Validate against the reference range and structural constraint.",
    "Apply the declared bounded edit/search law; reject any value outside it."
  ],
  "source_line_end": 45637,
  "source_line_start": 45626,
  "step12_primary_tranche_id": "ST12-TRANCHE-A"
},
{
  "canonical_owner": "QKUComputationControlPlaneV1",
  "certified_step11_custody_ref": "inputs/certified_step11/QTT_Stage1_Step11_Parameter_Policy_Adjudication_v1_0.jsonl#ST11-PARAM::01552",
  "certified_step11_row_embedded_in_prompt": false,
  "codex_online_research_allowed": false,
  "direct_source_claim_justifications": [],
  "effective_bounded_search_space_or_fit_constraint": "{CONSTRAINED_EXPECTED_ACTIVE_RETURN_OVER_UNCONSTRAINED_EXPECTED_ACTIVE_RETURN,RISK_ADJUSTED_ACTIVE_WEIGHT_CORRELATION_WHEN_DECLARED}",
  "effective_day1_seed_value_or_resolution_rule": "CONSTRAINED_EXPECTED_ACTIVE_RETURN_OVER_UNCONSTRAINED_EXPECTED_ACTIVE_RETURN",
  "effective_default_authority_class": "PUBLIC_METHOD_OR_PINNED_PROVIDER_DEFAULT_REQUIRES_IMPLEMENTATION_VERSION_BINDING",
  "effective_fallback_behavior_when_value_unavailable": "FAIL_CLOSED_TO_REGISTERED_LOWER_SAFE_PATH_OR_NO_TRADE",
  "effective_owner_dashboard_editability_class": "VIEW_ONLY_RESOLVED",
  "effective_policy_authority": "CERTIFIED_STEP11_PARAMETER_POLICY",
  "effective_reference_range_or_structural_constraint": "continuous coefficient on `[0,1]` with `1.0` reserved for the unconstrained comparator case",
  "effective_resolution_class": "STATIC_ENUM",
  "effective_source_state_refs": [
    "OWNER_POLICY::RA_13E1",
    "SOURCE_PACK::RA_13E1"
  ],
  "effective_ui_widget_class": "READ_ONLY_NUMERIC",
  "effective_unit_or_basis": "transfer coefficient in `[0,1]`",
  "effective_value_source_class": "PUBLIC_METHOD_REFERENCE_WITH_EXPLICIT_QTT_COMPARATOR_RULE",
  "evidence_basis_class": "FAMILY_SOURCE_PACK_PLUS_EXACT_OWNER_APPROVED_VALUE",
  "evidence_binding_rule_refs": [],
  "family_evidence_binding_ref": "ST12-FAMILY-EVIDENCE::RA_13E1",
  "implementation_resolution_kind": "STATIC_OR_DETERMINISTIC_RULE",
  "launch_computability_state": "COMPUTABLE_FROM_STATIC_VALUE_OR_DETERMINISTIC_RULE",
  "master_plan_heading_path": [
    "Part II — Retained institutional design and parameter catalog",
    "D14. Canonical family registry — risk and allocation",
    "RA-13E1 — Fundamental-law active-management diagnostic family"
  ],
  "master_plan_section_id": "RA-13E1",
  "missing_stale_invalid_behavior": "REJECT_INVALID_VALUE_NO_SILENT_DEFAULT",
  "parameter_audit_id": "ST11-PARAM::01552",
  "parameter_id": "ST10-PARAM::1552",
  "parameter_symbol": "tc_flam",
  "precision_and_rounding_policy": {
    "allowlist_check": "REQUIRED",
    "internal_numeric_type": "typed_symbolic",
    "normalization": "CANONICAL_EXACT_TOKEN_NO_FREE_TEXT_COERCION",
    "rounding": "NOT_APPLICABLE"
  },
  "runtime_resolution_procedure": [
    "Parse the declared Day-1 seed or deterministic rule into the declared type.",
    "Validate against the reference range and structural constraint.",
    "Apply the declared bounded edit/search law; reject any value outside it."
  ],
  "source_line_end": 47555,
  "source_line_start": 47544,
  "step12_primary_tranche_id": "ST12-TRANCHE-A"
},
{
  "canonical_owner": "QKUComputationControlPlaneV1",
  "certified_step11_custody_ref": "inputs/certified_step11/QTT_Stage1_Step11_Parameter_Policy_Adjudication_v1_0.jsonl#ST11-PARAM::01602",
  "certified_step11_row_embedded_in_prompt": false,
  "codex_online_research_allowed": false,
  "direct_source_claim_justifications": [],
  "effective_bounded_search_space_or_fit_constraint": "singleton provenance requirement only in the current repository-authoritative baseline edition",
  "effective_day1_seed_value_or_resolution_rule": "REQUIRED_TYPED_PRIOR_SCENARIO_SET_AND_PRIOR_SIMPLEX_PACKET",
  "effective_default_authority_class": "EXPLICIT_QTT_OR_OWNER_POLICY_SEED_OR_RESOLUTION_RULE",
  "effective_fallback_behavior_when_value_unavailable": "FAIL_CLOSED_TO_REGISTERED_LOWER_SAFE_PATH_OR_NO_TRADE",
  "effective_owner_dashboard_editability_class": "OWNER_VISIBLE_NOT_EDITABLE",
  "effective_policy_authority": "CERTIFIED_STEP11_PARAMETER_POLICY",
  "effective_reference_range_or_structural_constraint": "`{REQUIRED_TYPED_PRIOR_SCENARIO_SET_AND_PRIOR_SIMPLEX_PACKET}` unless a later canonical master plan admits an alternative prior packet basis",
  "effective_resolution_class": "STATIC_ENUM",
  "effective_source_state_refs": [
    "OWNER_POLICY::RA_13M2",
    "SOURCE_PACK::RA_13M2"
  ],
  "effective_ui_widget_class": "READONLY_ENUM_BADGE",
  "effective_unit_or_basis": "prior-packet requirement",
  "effective_value_source_class": "QTT_CANONICAL_INPUT_CONTRACT_RULE",
  "evidence_basis_class": "FAMILY_SOURCE_PACK_PLUS_EXACT_OWNER_APPROVED_VALUE",
  "evidence_binding_rule_refs": [],
  "family_evidence_binding_ref": "ST12-FAMILY-EVIDENCE::RA_13M2",
  "implementation_resolution_kind": "STATIC_OR_DETERMINISTIC_RULE",
  "launch_computability_state": "COMPUTABLE_FROM_STATIC_VALUE_OR_DETERMINISTIC_RULE",
  "master_plan_heading_path": [
    "Part II — Retained institutional design and parameter catalog",
    "D14. Canonical family registry — risk and allocation",
    "RA-13M2 — Entropy pooling atomic parameter pack and current-version deployment and binding specification"
  ],
  "master_plan_section_id": "RA-13M2",
  "missing_stale_invalid_behavior": "REJECT_INVALID_VALUE_NO_SILENT_DEFAULT",
  "parameter_audit_id": "ST11-PARAM::01602",
  "parameter_id": "ST10-PARAM::1602",
  "parameter_symbol": "ep_priorpkt",
  "precision_and_rounding_policy": {
    "allowlist_check": "REQUIRED",
    "internal_numeric_type": "typed_symbolic",
    "normalization": "CANONICAL_EXACT_TOKEN_NO_FREE_TEXT_COERCION",
    "rounding": "NOT_APPLICABLE"
  },
  "runtime_resolution_procedure": [
    "Parse the declared Day-1 seed or deterministic rule into the declared type.",
    "Validate against the reference range and structural constraint.",
    "Apply the declared bounded edit/search law; reject any value outside it."
  ],
  "source_line_end": 48358,
  "source_line_start": 48347,
  "step12_primary_tranche_id": "ST12-TRANCHE-A"
},
{
  "canonical_owner": "QKUComputationControlPlaneV1",
  "certified_step11_custody_ref": "inputs/certified_step11/QTT_Stage1_Step11_Parameter_Policy_Adjudication_v1_0.jsonl#ST11-PARAM::01603",
  "certified_step11_row_embedded_in_prompt": false,
  "codex_online_research_allowed": false,
  "direct_source_claim_justifications": [],
  "effective_bounded_search_space_or_fit_constraint": "singleton basis only in the current repository-authoritative baseline edition",
  "effective_day1_seed_value_or_resolution_rule": "POSTERIOR_SCENARIO_WEIGHT_VECTOR_PLUS_VIEW_CONSISTENCY_RECEIPT_PLUS_POSTERIOR_MOMENT_PACKET",
  "effective_default_authority_class": "EXPLICIT_QTT_OR_OWNER_POLICY_SEED_OR_RESOLUTION_RULE",
  "effective_fallback_behavior_when_value_unavailable": "FAIL_CLOSED_TO_REGISTERED_LOWER_SAFE_PATH_OR_NO_TRADE",
  "effective_owner_dashboard_editability_class": "OWNER_VISIBLE_NOT_EDITABLE",
  "effective_policy_authority": "CERTIFIED_STEP11_PARAMETER_POLICY",
  "effective_reference_range_or_structural_constraint": "`{POSTERIOR_SCENARIO_WEIGHT_VECTOR_PLUS_VIEW_CONSISTENCY_RECEIPT_PLUS_POSTERIOR_MOMENT_PACKET}` unless a later canonical master plan adds an explicit alternative basis",
  "effective_resolution_class": "STATIC_ENUM",
  "effective_source_state_refs": [
    "OWNER_POLICY::RA_13M2",
    "SOURCE_PACK::RA_13M2"
  ],
  "effective_ui_widget_class": "READONLY_ENUM_BADGE",
  "effective_unit_or_basis": "posterior output basis",
  "effective_value_source_class": "QTT_CANONICAL_OUTPUT_BASIS_RULE",
  "evidence_basis_class": "FAMILY_SOURCE_PACK_PLUS_EXACT_OWNER_APPROVED_VALUE",
  "evidence_binding_rule_refs": [],
  "family_evidence_binding_ref": "ST12-FAMILY-EVIDENCE::RA_13M2",
  "implementation_resolution_kind": "STATIC_OR_DETERMINISTIC_RULE",
  "launch_computability_state": "COMPUTABLE_FROM_STATIC_VALUE_OR_DETERMINISTIC_RULE",
  "master_plan_heading_path": [
    "Part II — Retained institutional design and parameter catalog",
    "D14. Canonical family registry — risk and allocation",
    "RA-13M2 — Entropy pooling atomic parameter pack and current-version deployment and binding specification"
  ],
  "master_plan_section_id": "RA-13M2",
  "missing_stale_invalid_behavior": "REJECT_INVALID_VALUE_NO_SILENT_DEFAULT",
  "parameter_audit_id": "ST11-PARAM::01603",
  "parameter_id": "ST10-PARAM::1603",
  "parameter_symbol": "ep_out",
  "precision_and_rounding_policy": {
    "allowlist_check": "REQUIRED",
    "internal_numeric_type": "typed_symbolic",
    "normalization": "CANONICAL_EXACT_TOKEN_NO_FREE_TEXT_COERCION",
    "rounding": "NOT_APPLICABLE"
  },
  "runtime_resolution_procedure": [
    "Parse the declared Day-1 seed or deterministic rule into the declared type.",
    "Validate against the reference range and structural constraint.",
    "Apply the declared bounded edit/search law; reject any value outside it."
  ],
  "source_line_end": 48370,
  "source_line_start": 48359,
  "step12_primary_tranche_id": "ST12-TRANCHE-A"
},
{
  "canonical_owner": "QKUComputationControlPlaneV1",
  "certified_step11_custody_ref": "inputs/certified_step11/QTT_Stage1_Step11_Parameter_Policy_Adjudication_v1_0.jsonl#ST11-PARAM::01610",
  "certified_step11_row_embedded_in_prompt": false,
  "codex_online_research_allowed": false,
  "direct_source_claim_justifications": [],
  "effective_bounded_search_space_or_fit_constraint": "singleton normalization requirement only in the current repository-authoritative baseline edition",
  "effective_day1_seed_value_or_resolution_rule": "REQUIRED_NORMALIZED_UNIT_PROFIT_OR_UNIT_LOSS_BASIS",
  "effective_default_authority_class": "EXPLICIT_QTT_OR_OWNER_POLICY_SEED_OR_RESOLUTION_RULE",
  "effective_fallback_behavior_when_value_unavailable": "FAIL_CLOSED_TO_REGISTERED_LOWER_SAFE_PATH_OR_NO_TRADE",
  "effective_owner_dashboard_editability_class": "OWNER_VISIBLE_NOT_EDITABLE",
  "effective_policy_authority": "CERTIFIED_STEP11_PARAMETER_POLICY",
  "effective_reference_range_or_structural_constraint": "`{REQUIRED_NORMALIZED_UNIT_PROFIT_OR_UNIT_LOSS_BASIS}` unless a later canonical master plan admits an alternative normalized basis contract",
  "effective_resolution_class": "STATIC_ENUM",
  "effective_source_state_refs": [
    "OWNER_POLICY::RA_13N2",
    "SOURCE_PACK::RA_13N2"
  ],
  "effective_ui_widget_class": "READONLY_ENUM_BADGE",
  "effective_unit_or_basis": "normalization contract",
  "effective_value_source_class": "QTT_CANONICAL_NORMALIZATION_RULE",
  "evidence_basis_class": "FAMILY_SOURCE_PACK_PLUS_EXACT_OWNER_APPROVED_VALUE",
  "evidence_binding_rule_refs": [],
  "family_evidence_binding_ref": "ST12-FAMILY-EVIDENCE::RA_13N2",
  "implementation_resolution_kind": "STATIC_OR_DETERMINISTIC_RULE",
  "launch_computability_state": "COMPUTABLE_FROM_STATIC_VALUE_OR_DETERMINISTIC_RULE",
  "master_plan_heading_path": [
    "Part II — Retained institutional design and parameter catalog",
    "D14. Canonical family registry — risk and allocation",
    "RA-13N2 — Entropic-risk atomic parameter pack and current-version deployment and binding specification"
  ],
  "master_plan_section_id": "RA-13N2",
  "missing_stale_invalid_behavior": "REJECT_INVALID_VALUE_NO_SILENT_DEFAULT",
  "parameter_audit_id": "ST11-PARAM::01610",
  "parameter_id": "ST10-PARAM::1610",
  "parameter_symbol": "er_norm",
  "precision_and_rounding_policy": {
    "allowlist_check": "REQUIRED",
    "internal_numeric_type": "typed_symbolic",
    "normalization": "CANONICAL_EXACT_TOKEN_NO_FREE_TEXT_COERCION",
    "rounding": "NOT_APPLICABLE"
  },
  "runtime_resolution_procedure": [
    "Parse the declared Day-1 seed or deterministic rule into the declared type.",
    "Validate against the reference range and structural constraint.",
    "Apply the declared bounded edit/search law; reject any value outside it."
  ],
  "source_line_end": 48486,
  "source_line_start": 48475,
  "step12_primary_tranche_id": "ST12-TRANCHE-A"
},
{
  "canonical_owner": "QKUComputationControlPlaneV1",
  "certified_step11_custody_ref": "inputs/certified_step11/QTT_Stage1_Step11_Parameter_Policy_Adjudication_v1_0.jsonl#ST11-PARAM::01611",
  "certified_step11_row_embedded_in_prompt": false,
  "codex_online_research_allowed": false,
  "direct_source_claim_justifications": [],
  "effective_bounded_search_space_or_fit_constraint": "singleton basis only in the current repository-authoritative baseline edition",
  "effective_day1_seed_value_or_resolution_rule": "CERTAINTY_EQUIVALENT_RECEIPT_PLUS_ENTROPIC_RISK_RECEIPT_PLUS_GAMMA_SENSITIVITY_PACKET",
  "effective_default_authority_class": "EXPLICIT_QTT_OR_OWNER_POLICY_SEED_OR_RESOLUTION_RULE",
  "effective_fallback_behavior_when_value_unavailable": "FAIL_CLOSED_TO_REGISTERED_LOWER_SAFE_PATH_OR_NO_TRADE",
  "effective_owner_dashboard_editability_class": "OWNER_VISIBLE_NOT_EDITABLE",
  "effective_policy_authority": "CERTIFIED_STEP11_PARAMETER_POLICY",
  "effective_reference_range_or_structural_constraint": "`{CERTAINTY_EQUIVALENT_RECEIPT_PLUS_ENTROPIC_RISK_RECEIPT_PLUS_GAMMA_SENSITIVITY_PACKET}` unless a later canonical master plan adds an explicit alternative basis",
  "effective_resolution_class": "STATIC_ENUM",
  "effective_source_state_refs": [
    "OWNER_POLICY::RA_13N2",
    "SOURCE_PACK::RA_13N2"
  ],
  "effective_ui_widget_class": "READONLY_ENUM_BADGE",
  "effective_unit_or_basis": "entropic-risk output basis",
  "effective_value_source_class": "QTT_CANONICAL_OUTPUT_BASIS_RULE",
  "evidence_basis_class": "FAMILY_SOURCE_PACK_PLUS_EXACT_OWNER_APPROVED_VALUE",
  "evidence_binding_rule_refs": [],
  "family_evidence_binding_ref": "ST12-FAMILY-EVIDENCE::RA_13N2",
  "implementation_resolution_kind": "STATIC_OR_DETERMINISTIC_RULE",
  "launch_computability_state": "COMPUTABLE_FROM_STATIC_VALUE_OR_DETERMINISTIC_RULE",
  "master_plan_heading_path": [
    "Part II — Retained institutional design and parameter catalog",
    "D14. Canonical family registry — risk and allocation",
    "RA-13N2 — Entropic-risk atomic parameter pack and current-version deployment and binding specification"
  ],
  "master_plan_section_id": "RA-13N2",
  "missing_stale_invalid_behavior": "REJECT_INVALID_VALUE_NO_SILENT_DEFAULT",
  "parameter_audit_id": "ST11-PARAM::01611",
  "parameter_id": "ST10-PARAM::1611",
  "parameter_symbol": "er_out",
  "precision_and_rounding_policy": {
    "allowlist_check": "REQUIRED",
    "internal_numeric_type": "typed_symbolic",
    "normalization": "CANONICAL_EXACT_TOKEN_NO_FREE_TEXT_COERCION",
    "rounding": "NOT_APPLICABLE"
  },
  "runtime_resolution_procedure": [
    "Parse the declared Day-1 seed or deterministic rule into the declared type.",
    "Validate against the reference range and structural constraint.",
    "Apply the declared bounded edit/search law; reject any value outside it."
  ],
  "source_line_end": 48498,
  "source_line_start": 48487,
  "step12_primary_tranche_id": "ST12-TRANCHE-A"
},
{
  "canonical_owner": "QKUComputationControlPlaneV1",
  "certified_step11_custody_ref": "inputs/certified_step11/QTT_Stage1_Step11_Parameter_Policy_Adjudication_v1_0.jsonl#ST11-PARAM::01683",
  "certified_step11_row_embedded_in_prompt": false,
  "codex_online_research_allowed": false,
  "direct_source_claim_justifications": [],
  "effective_bounded_search_space_or_fit_constraint": "ambiguous rejects may not silently unlock fresh live release",
  "effective_day1_seed_value_or_resolution_rule": "FAIL_CLOSED_NO_RETRY_PRESERVE_RESERVATIONS_AND_REQUIRE_AUTHORITATIVE_RECONCILIATION",
  "effective_default_authority_class": "EXPLICIT_QTT_OR_OWNER_POLICY_SEED_OR_RESOLUTION_RULE",
  "effective_fallback_behavior_when_value_unavailable": "FAIL_CLOSED_TO_REGISTERED_LOWER_SAFE_PATH_OR_NO_TRADE",
  "effective_owner_dashboard_editability_class": "READ_ONLY_SYMBOLIC",
  "effective_policy_authority": "CERTIFIED_STEP11_PARAMETER_POLICY",
  "effective_reference_range_or_structural_constraint": "{FAIL_CLOSED_NO_RETRY_PRESERVE_RESERVATIONS_AND_REQUIRE_AUTHORITATIVE_RECONCILIATION}",
  "effective_resolution_class": "STATIC_ENUM",
  "effective_source_state_refs": [
    "OWNER_POLICY::RA_16G2",
    "SOURCE_PACK::RA_16G2"
  ],
  "effective_ui_widget_class": "FORMULA_BADGE",
  "effective_unit_or_basis": "reject fallback rule",
  "effective_value_source_class": "QTT_REJECT_FALLBACK_RULE",
  "evidence_basis_class": "FAMILY_SOURCE_PACK_PLUS_EXACT_OWNER_APPROVED_VALUE",
  "evidence_binding_rule_refs": [],
  "family_evidence_binding_ref": "ST12-FAMILY-EVIDENCE::RA_16G2",
  "implementation_resolution_kind": "EXPLICIT_FAIL_CLOSED_POLICY",
  "launch_computability_state": "COMPUTABLE_TYPED_FAIL_CLOSED_OR_NO_TRADE_STATE",
  "master_plan_heading_path": [
    "Part II — Retained institutional design and parameter catalog",
    "D14. Canonical family registry — risk and allocation",
    "RA-16G2 — Order-reject, cancel-reject, business-reject, and session-reject atomic parameter pack"
  ],
  "master_plan_section_id": "RA-16G2",
  "missing_stale_invalid_behavior": "PRESERVE_EXPLICIT_FAIL_CLOSED_STATE",
  "parameter_audit_id": "ST11-PARAM::01683",
  "parameter_id": "ST10-PARAM::1683",
  "parameter_symbol": "rej_fb",
  "precision_and_rounding_policy": {
    "allowlist_check": "REQUIRED",
    "internal_numeric_type": "typed_symbolic",
    "normalization": "CANONICAL_EXACT_TOKEN_NO_FREE_TEXT_COERCION",
    "rounding": "NOT_APPLICABLE"
  },
  "runtime_resolution_procedure": [
    "Materialize the declared fail-closed state exactly.",
    "Return a typed blocker/no-trade status and do not substitute a numeric fallback.",
    "Validate the resolved typed value or token against the effective resolution class, declared structural constraint, and canonical allowlist; on failure apply the declared fail-closed fallback and emit the exact reason code."
  ],
  "source_line_end": 49796,
  "source_line_start": 49782,
  "step12_primary_tranche_id": "ST12-TRANCHE-A"
},
{
  "canonical_owner": "QKUComputationControlPlaneV1",
  "certified_step11_custody_ref": "inputs/certified_step11/QTT_Stage1_Step11_Parameter_Policy_Adjudication_v1_0.jsonl#ST11-PARAM::01697",
  "certified_step11_row_embedded_in_prompt": false,
  "codex_online_research_allowed": false,
  "direct_source_claim_justifications": [],
  "effective_bounded_search_space_or_fit_constraint": "ambiguous pending or restated states may not unlock optimistic live behavior",
  "effective_day1_seed_value_or_resolution_rule": "FAIL_CLOSED_PRESERVE_STRICT_RESERVATIONS_BLOCK_NEW_RELEASE_AND_REQUIRE_AUTHORITATIVE_RECONCILIATION",
  "effective_default_authority_class": "EXPLICIT_QTT_OR_OWNER_POLICY_SEED_OR_RESOLUTION_RULE",
  "effective_fallback_behavior_when_value_unavailable": "FAIL_CLOSED_TO_REGISTERED_LOWER_SAFE_PATH_OR_NO_TRADE",
  "effective_owner_dashboard_editability_class": "READ_ONLY_SYMBOLIC",
  "effective_policy_authority": "CERTIFIED_STEP11_PARAMETER_POLICY",
  "effective_reference_range_or_structural_constraint": "{FAIL_CLOSED_PRESERVE_STRICT_RESERVATIONS_BLOCK_NEW_RELEASE_AND_REQUIRE_AUTHORITATIVE_RECONCILIATION}",
  "effective_resolution_class": "STATIC_ENUM",
  "effective_source_state_refs": [
    "OWNER_POLICY::RA_16G3",
    "SOURCE_PACK::RA_16G3"
  ],
  "effective_ui_widget_class": "FORMULA_BADGE",
  "effective_unit_or_basis": "status fallback rule",
  "effective_value_source_class": "QTT_STATUS_FALLBACK_RULE",
  "evidence_basis_class": "FAMILY_SOURCE_PACK_PLUS_EXACT_OWNER_APPROVED_VALUE",
  "evidence_binding_rule_refs": [],
  "family_evidence_binding_ref": "ST12-FAMILY-EVIDENCE::RA_16G3",
  "implementation_resolution_kind": "EXPLICIT_FAIL_CLOSED_POLICY",
  "launch_computability_state": "COMPUTABLE_TYPED_FAIL_CLOSED_OR_NO_TRADE_STATE",
  "master_plan_heading_path": [
    "Part II — Retained institutional design and parameter catalog",
    "D14. Canonical family registry — risk and allocation",
    "RA-16G3 — Pending-state, restatement, and nonterminal status atomic parameter pack"
  ],
  "master_plan_section_id": "RA-16G3",
  "missing_stale_invalid_behavior": "PRESERVE_EXPLICIT_FAIL_CLOSED_STATE",
  "parameter_audit_id": "ST11-PARAM::01697",
  "parameter_id": "ST10-PARAM::1697",
  "parameter_symbol": "stat_fb",
  "precision_and_rounding_policy": {
    "allowlist_check": "REQUIRED",
    "internal_numeric_type": "typed_symbolic",
    "normalization": "CANONICAL_EXACT_TOKEN_NO_FREE_TEXT_COERCION",
    "rounding": "NOT_APPLICABLE"
  },
  "runtime_resolution_procedure": [
    "Materialize the declared fail-closed state exactly.",
    "Return a typed blocker/no-trade status and do not substitute a numeric fallback.",
    "Validate the resolved typed value or token against the effective resolution class, declared structural constraint, and canonical allowlist; on failure apply the declared fail-closed fallback and emit the exact reason code."
  ],
  "source_line_end": 49974,
  "source_line_start": 49960,
  "step12_primary_tranche_id": "ST12-TRANCHE-A"
},
{
  "canonical_owner": "QKUComputationControlPlaneV1",
  "certified_step11_custody_ref": "inputs/certified_step11/QTT_Stage1_Step11_Parameter_Policy_Adjudication_v1_0.jsonl#ST11-PARAM::01734",
  "certified_step11_row_embedded_in_prompt": false,
  "codex_online_research_allowed": false,
  "direct_source_claim_justifications": [],
  "effective_bounded_search_space_or_fit_constraint": "post-trade break ambiguity may not silently resolve to green realized truth or autonomous entry authority",
  "effective_day1_seed_value_or_resolution_rule": "FAIL_CLOSED_TO_PROVISIONAL_LEDGER_AND_NO_AUTONOMOUS_REENTRY_UNTIL_AUTHORITATIVE_RECONCILIATION_COMPLETES",
  "effective_default_authority_class": "EXPLICIT_QTT_OR_OWNER_POLICY_SEED_OR_RESOLUTION_RULE",
  "effective_fallback_behavior_when_value_unavailable": "FAIL_CLOSED_TO_REGISTERED_LOWER_SAFE_PATH_OR_NO_TRADE",
  "effective_owner_dashboard_editability_class": "READ_ONLY_SYMBOLIC",
  "effective_policy_authority": "CERTIFIED_STEP11_PARAMETER_POLICY",
  "effective_reference_range_or_structural_constraint": "{FAIL_CLOSED_TO_PROVISIONAL_LEDGER_AND_NO_AUTONOMOUS_REENTRY_UNTIL_AUTHORITATIVE_RECONCILIATION_COMPLETES}",
  "effective_resolution_class": "STATIC_ENUM",
  "effective_source_state_refs": [
    "OWNER_POLICY::RA_16G4",
    "SOURCE_PACK::RA_16G4"
  ],
  "effective_ui_widget_class": "FORMULA_BADGE",
  "effective_unit_or_basis": "post-trade-break fallback rule",
  "effective_value_source_class": "QTT_FAIL_CLOSED_POST_TRADE_BREAK_RULE",
  "evidence_basis_class": "FAMILY_SOURCE_PACK_PLUS_EXACT_OWNER_APPROVED_VALUE",
  "evidence_binding_rule_refs": [],
  "family_evidence_binding_ref": "ST12-FAMILY-EVIDENCE::RA_16G4",
  "implementation_resolution_kind": "EXPLICIT_FAIL_CLOSED_POLICY",
  "launch_computability_state": "COMPUTABLE_TYPED_FAIL_CLOSED_OR_NO_TRADE_STATE",
  "master_plan_heading_path": [
    "Part II — Retained institutional design and parameter catalog",
    "D14. Canonical family registry — risk and allocation",
    "RA-16G4 — Clearly-erroneous, trade-cancel, trade-correct, and post-trade break workflow atomic parameter pack"
  ],
  "master_plan_section_id": "RA-16G4",
  "missing_stale_invalid_behavior": "PRESERVE_EXPLICIT_FAIL_CLOSED_STATE",
  "parameter_audit_id": "ST11-PARAM::01734",
  "parameter_id": "ST10-PARAM::1734",
  "parameter_symbol": "ptbrk_fb",
  "precision_and_rounding_policy": {
    "allowlist_check": "REQUIRED",
    "internal_numeric_type": "typed_symbolic",
    "normalization": "CANONICAL_EXACT_TOKEN_NO_FREE_TEXT_COERCION",
    "rounding": "NOT_APPLICABLE"
  },
  "runtime_resolution_procedure": [
    "Materialize the declared fail-closed state exactly.",
    "Return a typed blocker/no-trade status and do not substitute a numeric fallback.",
    "Validate the resolved typed value or token against the effective resolution class, declared structural constraint, and canonical allowlist; on failure apply the declared fail-closed fallback and emit the exact reason code."
  ],
  "source_line_end": 50641,
  "source_line_start": 50627,
  "step12_primary_tranche_id": "ST12-TRANCHE-A"
},
{
  "canonical_owner": "QKUComputationControlPlaneV1",
  "certified_step11_custody_ref": "inputs/certified_step11/QTT_Stage1_Step11_Parameter_Policy_Adjudication_v1_0.jsonl#ST11-PARAM::01777",
  "certified_step11_row_embedded_in_prompt": false,
  "codex_online_research_allowed": false,
  "direct_source_claim_justifications": [],
  "effective_bounded_search_space_or_fit_constraint": "fixed routing guard only; destination changes may not override active protective price constraints",
  "effective_day1_seed_value_or_resolution_rule": "ROUTING_MAY_NOT_BYPASS_ACTIVE_LIMIT_PRICE_COLLAR_AND_PRICE_RANGE_GUARDS",
  "effective_default_authority_class": "EXPLICIT_QTT_OR_OWNER_POLICY_SEED_OR_RESOLUTION_RULE",
  "effective_fallback_behavior_when_value_unavailable": "FAIL_CLOSED_TO_REGISTERED_LOWER_SAFE_PATH_OR_NO_TRADE",
  "effective_owner_dashboard_editability_class": "READ_ONLY_SYMBOLIC",
  "effective_policy_authority": "CERTIFIED_STEP11_PARAMETER_POLICY",
  "effective_reference_range_or_structural_constraint": "{ROUTING_MAY_NOT_BYPASS_ACTIVE_LIMIT_PRICE_COLLAR_AND_PRICE_RANGE_GUARDS}",
  "effective_resolution_class": "STATIC_ENUM",
  "effective_source_state_refs": [
    "OWNER_POLICY::EX_05C",
    "SOURCE_PACK::EX_05C"
  ],
  "effective_ui_widget_class": "FORMULA_BADGE",
  "effective_unit_or_basis": "routing-price-guard rule",
  "effective_value_source_class": "QTT_PRICE_PROTECTION_RULE",
  "evidence_basis_class": "FAMILY_SOURCE_PACK_PLUS_EXACT_OWNER_APPROVED_VALUE",
  "evidence_binding_rule_refs": [],
  "family_evidence_binding_ref": "ST12-FAMILY-EVIDENCE::EX_05C",
  "implementation_resolution_kind": "STATIC_OR_DETERMINISTIC_RULE",
  "launch_computability_state": "COMPUTABLE_FROM_STATIC_VALUE_OR_DETERMINISTIC_RULE",
  "master_plan_heading_path": [
    "Part II — Retained institutional design and parameter catalog",
    "D14. Canonical family registry — risk and allocation",
    "EX-05C — Smart-order-routing, venue-selection, and destination-scoring atomic parameter pack"
  ],
  "master_plan_section_id": "EX-05C",
  "missing_stale_invalid_behavior": "REJECT_INVALID_VALUE_NO_SILENT_DEFAULT",
  "parameter_audit_id": "ST11-PARAM::01777",
  "parameter_id": "ST10-PARAM::1777",
  "parameter_symbol": "guard_route",
  "precision_and_rounding_policy": {
    "allowlist_check": "REQUIRED",
    "internal_numeric_type": "typed_symbolic",
    "normalization": "CANONICAL_EXACT_TOKEN_NO_FREE_TEXT_COERCION",
    "rounding": "NOT_APPLICABLE"
  },
  "runtime_resolution_procedure": [
    "Parse the declared Day-1 seed or deterministic rule into the declared type.",
    "Validate against the reference range and structural constraint.",
    "Apply the declared bounded edit/search law; reject any value outside it."
  ],
  "source_line_end": 51204,
  "source_line_start": 51193,
  "step12_primary_tranche_id": "ST12-TRANCHE-A"
},
{
  "canonical_owner": "QKUComputationControlPlaneV1",
  "certified_step11_custody_ref": "inputs/certified_step11/QTT_Stage1_Step11_Parameter_Policy_Adjudication_v1_0.jsonl#ST11-PARAM::01834",
  "certified_step11_row_embedded_in_prompt": false,
  "codex_online_research_allowed": false,
  "direct_source_claim_justifications": [],
  "effective_bounded_search_space_or_fit_constraint": "formula only; eligible set and score family must already be explicit",
  "effective_day1_seed_value_or_resolution_rule": "equal_weight_on_eligible_set for BROKER_WHEEL_EQUAL_RANDOM; p_i = w_i / Σ_j w_j with w_i = max(0,S_i) for BROKER_WHEEL_WEIGHTED_RANDOM; dormant otherwise",
  "effective_default_authority_class": "PUBLIC_METHOD_OR_PINNED_PROVIDER_DEFAULT_REQUIRES_IMPLEMENTATION_VERSION_BINDING",
  "effective_fallback_behavior_when_value_unavailable": "FAIL_CLOSED_TO_REGISTERED_LOWER_SAFE_PATH_OR_NO_TRADE",
  "effective_owner_dashboard_editability_class": "READ_ONLY_FORMULA_WITH_UPSTREAM_EDITS",
  "effective_policy_authority": "CERTIFIED_STEP11_PARAMETER_POLICY",
  "effective_reference_range_or_structural_constraint": "valid probability vector over the eligible approved partner set",
  "effective_resolution_class": "STATIC_FORMULA_CONDITIONAL",
  "effective_source_state_refs": [
    "OWNER_POLICY::EX_10E1",
    "SOURCE_PACK::EX_10E1"
  ],
  "effective_ui_widget_class": "READ_ONLY_FORMULA_CARD",
  "effective_unit_or_basis": "probability vector on the eligible partner set",
  "effective_value_source_class": "PUBLIC_METHODOLOGICAL_FORMULA_WITH_QTT_CANONICAL_BINDING",
  "evidence_basis_class": "FAMILY_SOURCE_PACK_PLUS_EXACT_OWNER_APPROVED_VALUE",
  "evidence_binding_rule_refs": [],
  "family_evidence_binding_ref": "ST12-FAMILY-EVIDENCE::EX_10E1",
  "implementation_resolution_kind": "STATIC_OR_DETERMINISTIC_RULE",
  "launch_computability_state": "COMPUTABLE_FROM_STATIC_VALUE_OR_DETERMINISTIC_RULE",
  "master_plan_heading_path": [
    "Part II — Retained institutional design and parameter catalog",
    "D14. Canonical family registry — risk and allocation",
    "EX-10E1 — Cross-asset execution-partner selection, partner-wheel, and LP-scorecard atomic parameter pack"
  ],
  "master_plan_section_id": "EX-10E1",
  "missing_stale_invalid_behavior": "REJECT_INVALID_VALUE_NO_SILENT_DEFAULT",
  "parameter_audit_id": "ST11-PARAM::01834",
  "parameter_id": "ST10-PARAM::1834",
  "parameter_symbol": "p_partner_rule",
  "precision_and_rounding_policy": {
    "finite_check": "REQUIRED",
    "internal_numeric_type": "float64_or_declared_array_dtype",
    "probability_domain": "[0,1] WHEN APPLICABLE",
    "rounding": "NONE_INTERNAL; CONVERT_TO_DECIMAL_AT_FINANCIAL_BOUNDARY"
  },
  "runtime_resolution_procedure": [
    "Parse the declared Day-1 seed or deterministic rule into the declared type.",
    "Validate against the reference range and structural constraint.",
    "Apply the declared bounded edit/search law; reject any value outside it."
  ],
  "source_line_end": 52304,
  "source_line_start": 52293,
  "step12_primary_tranche_id": "ST12-TRANCHE-A"
},
{
  "canonical_owner": "QKUComputationControlPlaneV1",
  "certified_step11_custody_ref": "inputs/certified_step11/QTT_Stage1_Step11_Parameter_Policy_Adjudication_v1_0.jsonl#ST11-PARAM::01838",
  "certified_step11_row_embedded_in_prompt": false,
  "codex_online_research_allowed": false,
  "direct_source_claim_justifications": [],
  "effective_bounded_search_space_or_fit_constraint": "one governing rule family per sleeve; weaker treatment is forbidden",
  "effective_day1_seed_value_or_resolution_rule": "DECLARED_RFQ_PMP_WATERFALL_FOR_CORPORATE_AND_AGENCY_DEBT; DECLARED_RFQ_PMP_WATERFALL_FOR_MUNICIPAL_PATHS",
  "effective_default_authority_class": "PUBLIC_METHOD_OR_PINNED_PROVIDER_DEFAULT_REQUIRES_IMPLEMENTATION_VERSION_BINDING",
  "effective_fallback_behavior_when_value_unavailable": "FAIL_CLOSED_TO_REGISTERED_LOWER_SAFE_PATH_OR_NO_TRADE",
  "effective_owner_dashboard_editability_class": "READ_ONLY_BY_DEFAULT",
  "effective_policy_authority": "CERTIFIED_STEP11_PARAMETER_POLICY",
  "effective_reference_range_or_structural_constraint": "{DECLARED_RFQ_PMP_WATERFALL, DECLARED_MUNICIPAL_PMP_WATERFALL, DECLARED_STRICTER_INTERNAL_EQUIVALENT}",
  "effective_resolution_class": "STATIC_ENUM",
  "effective_source_state_refs": [
    "OWNER_POLICY::EX_10F",
    "SOURCE_PACK::EX_10F"
  ],
  "effective_ui_widget_class": "READ_ONLY_ENUM_BADGE",
  "effective_unit_or_basis": "rule-family enum",
  "effective_value_source_class": "PUBLIC_MARKET_STRUCTURE_STANDARD",
  "evidence_basis_class": "FAMILY_SOURCE_PACK_PLUS_EXACT_OWNER_APPROVED_VALUE",
  "evidence_binding_rule_refs": [],
  "family_evidence_binding_ref": "ST12-FAMILY-EVIDENCE::EX_10F",
  "implementation_resolution_kind": "STATIC_OR_DETERMINISTIC_RULE",
  "launch_computability_state": "COMPUTABLE_FROM_STATIC_VALUE_OR_DETERMINISTIC_RULE",
  "master_plan_heading_path": [
    "Part II — Retained institutional design and parameter catalog",
    "D14. Canonical family registry — risk and allocation",
    "EX-10F — Fixed-income RFQ executable-price waterfall and quote-quality atomic parameter pack"
  ],
  "master_plan_section_id": "EX-10F",
  "missing_stale_invalid_behavior": "REJECT_INVALID_VALUE_NO_SILENT_DEFAULT",
  "parameter_audit_id": "ST11-PARAM::01838",
  "parameter_id": "ST10-PARAM::1838",
  "parameter_symbol": "rfq_fp_rule",
  "precision_and_rounding_policy": {
    "allowlist_check": "REQUIRED",
    "internal_numeric_type": "typed_symbolic",
    "normalization": "CANONICAL_EXACT_TOKEN_NO_FREE_TEXT_COERCION",
    "rounding": "NOT_APPLICABLE"
  },
  "runtime_resolution_procedure": [
    "Parse the declared Day-1 seed or deterministic rule into the declared type.",
    "Validate against the reference range and structural constraint.",
    "Apply the declared bounded edit/search law; reject any value outside it."
  ],
  "source_line_end": 52358,
  "source_line_start": 52347,
  "step12_primary_tranche_id": "ST12-TRANCHE-A"
},
{
  "canonical_owner": "QKUComputationControlPlaneV1",
  "certified_step11_custody_ref": "inputs/certified_step11/QTT_Stage1_Step11_Parameter_Policy_Adjudication_v1_0.jsonl#ST11-PARAM::01839",
  "certified_step11_row_embedded_in_prompt": false,
  "codex_online_research_allowed": false,
  "direct_source_claim_justifications": [],
  "effective_bounded_search_space_or_fit_constraint": "any alternate path must remain at least as strict as the declared pricing waterfall",
  "effective_day1_seed_value_or_resolution_rule": "CONTEMPORANEOUS_COST_OR_PROCEEDS_FIRST_THEN_RULE_WATERFALL",
  "effective_default_authority_class": "PUBLIC_METHOD_OR_PINNED_PROVIDER_DEFAULT_REQUIRES_IMPLEMENTATION_VERSION_BINDING",
  "effective_fallback_behavior_when_value_unavailable": "FAIL_CLOSED_TO_REGISTERED_LOWER_SAFE_PATH_OR_NO_TRADE",
  "effective_owner_dashboard_editability_class": "READ_ONLY_BY_DEFAULT",
  "effective_policy_authority": "CERTIFIED_STEP11_PARAMETER_POLICY",
  "effective_reference_range_or_structural_constraint": "{CONTEMPORANEOUS_COST_OR_PROCEEDS_FIRST_THEN_RULE_WATERFALL, DECLARED_STRICTER_INTERNAL_WATERFALL}",
  "effective_resolution_class": "STATIC_POLICY_ID_WITH_WATERFALL",
  "effective_source_state_refs": [
    "OWNER_POLICY::EX_10F",
    "SOURCE_PACK::EX_10F"
  ],
  "effective_ui_widget_class": "READ_ONLY_POLICY_BADGE",
  "effective_unit_or_basis": "PMP-basis policy",
  "effective_value_source_class": "PUBLIC_MARKET_STRUCTURE_STANDARD",
  "evidence_basis_class": "FAMILY_SOURCE_PACK_PLUS_EXACT_OWNER_APPROVED_VALUE",
  "evidence_binding_rule_refs": [],
  "family_evidence_binding_ref": "ST12-FAMILY-EVIDENCE::EX_10F",
  "implementation_resolution_kind": "STATIC_OR_DETERMINISTIC_RULE",
  "launch_computability_state": "COMPUTABLE_FROM_STATIC_VALUE_OR_DETERMINISTIC_RULE",
  "master_plan_heading_path": [
    "Part II — Retained institutional design and parameter catalog",
    "D14. Canonical family registry — risk and allocation",
    "EX-10F — Fixed-income RFQ executable-price waterfall and quote-quality atomic parameter pack"
  ],
  "master_plan_section_id": "EX-10F",
  "missing_stale_invalid_behavior": "REJECT_INVALID_VALUE_NO_SILENT_DEFAULT",
  "parameter_audit_id": "ST11-PARAM::01839",
  "parameter_id": "ST10-PARAM::1839",
  "parameter_symbol": "pmp_basis",
  "precision_and_rounding_policy": {
    "allowlist_check": "REQUIRED",
    "internal_numeric_type": "typed_symbolic",
    "normalization": "CANONICAL_EXACT_TOKEN_NO_FREE_TEXT_COERCION",
    "rounding": "NOT_APPLICABLE"
  },
  "runtime_resolution_procedure": [
    "Parse the declared Day-1 seed or deterministic rule into the declared type.",
    "Validate against the reference range and structural constraint.",
    "Apply the declared bounded edit/search law; reject any value outside it."
  ],
  "source_line_end": 52370,
  "source_line_start": 52359,
  "step12_primary_tranche_id": "ST12-TRANCHE-A"
},
{
  "canonical_owner": "QKUComputationControlPlaneV1",
  "certified_step11_custody_ref": "inputs/certified_step11/QTT_Stage1_Step11_Parameter_Policy_Adjudication_v1_0.jsonl#ST11-PARAM::01845",
  "certified_step11_row_embedded_in_prompt": false,
  "codex_online_research_allowed": false,
  "direct_source_claim_justifications": [],
  "effective_bounded_search_space_or_fit_constraint": "any cadence weaker than the declared minimum review cadence is forbidden on applicable paths",
  "effective_day1_seed_value_or_resolution_rule": "AT_LEAST_QUARTERLY_SECURITY_BY_SECURITY_AND_ORDER_TYPE_BY_ORDER_TYPE_REVIEW_WHEN_REGULAR_AND_RIGOROUS_MODE_IS_ACTIVE",
  "effective_default_authority_class": "PUBLIC_METHOD_OR_PINNED_PROVIDER_DEFAULT_REQUIRES_IMPLEMENTATION_VERSION_BINDING",
  "effective_fallback_behavior_when_value_unavailable": "FAIL_CLOSED_TO_REGISTERED_LOWER_SAFE_PATH_OR_NO_TRADE",
  "effective_owner_dashboard_editability_class": "READ_ONLY_BY_DEFAULT",
  "effective_policy_authority": "CERTIFIED_STEP11_PARAMETER_POLICY",
  "effective_reference_range_or_structural_constraint": "{AT_LEAST_QUARTERLY_SECURITY_BY_SECURITY_AND_ORDER_TYPE_BY_ORDER_TYPE_REVIEW, STRONGER_MORE_FREQUENT_REVIEW}",
  "effective_resolution_class": "STATIC_ENUM_OR_POLICY_RULE",
  "effective_source_state_refs": [
    "OWNER_POLICY::EX_10E1A",
    "SOURCE_PACK::EX_10E1A"
  ],
  "effective_ui_widget_class": "READ_ONLY_POLICY_BADGE",
  "effective_unit_or_basis": "review-cadence policy ID",
  "effective_value_source_class": "PUBLIC_MARKET_PRACTICE_STANDARD",
  "evidence_basis_class": "FAMILY_SOURCE_PACK_PLUS_EXACT_OWNER_APPROVED_VALUE",
  "evidence_binding_rule_refs": [],
  "family_evidence_binding_ref": "ST12-FAMILY-EVIDENCE::EX_10E1A",
  "implementation_resolution_kind": "STATIC_OR_DETERMINISTIC_RULE",
  "launch_computability_state": "COMPUTABLE_FROM_STATIC_VALUE_OR_DETERMINISTIC_RULE",
  "master_plan_heading_path": [
    "Part II — Retained institutional design and parameter catalog",
    "D14. Canonical family registry — risk and allocation",
    "EX-10E1A — Cross-asset best-execution review, public execution-quality and routing-disclosure, and regular-and-rigorous benchmark-governance atomic parameter pack"
  ],
  "master_plan_section_id": "EX-10E1A",
  "missing_stale_invalid_behavior": "REJECT_INVALID_VALUE_NO_SILENT_DEFAULT",
  "parameter_audit_id": "ST11-PARAM::01845",
  "parameter_id": "ST10-PARAM::1845",
  "parameter_symbol": "bestex_cad",
  "precision_and_rounding_policy": {
    "allowlist_check": "REQUIRED",
    "internal_numeric_type": "typed_symbolic",
    "normalization": "CANONICAL_EXACT_TOKEN_NO_FREE_TEXT_COERCION",
    "rounding": "NOT_APPLICABLE"
  },
  "runtime_resolution_procedure": [
    "Parse the declared Day-1 seed or deterministic rule into the declared type.",
    "Validate against the reference range and structural constraint.",
    "Apply the declared bounded edit/search law; reject any value outside it."
  ],
  "source_line_end": 52458,
  "source_line_start": 52447,
  "step12_primary_tranche_id": "ST12-TRANCHE-A"
},
{
  "canonical_owner": "QKUComputationControlPlaneV1",
  "certified_step11_custody_ref": "inputs/certified_step11/QTT_Stage1_Step11_Parameter_Policy_Adjudication_v1_0.jsonl#ST11-PARAM::01854",
  "certified_step11_row_embedded_in_prompt": false,
  "codex_online_research_allowed": false,
  "direct_source_claim_justifications": [],
  "effective_bounded_search_space_or_fit_constraint": "best-execution governance ambiguity may not silently degrade into green partner-comparison or routing authority",
  "effective_day1_seed_value_or_resolution_rule": "FAIL_CLOSED_TO_SIMPLER_APPROVED_PARTNER_SELECTION_OR_DIRECT_ROUTE_AND_SUPPRESS_BEST_EXECUTION_CLAIMS_UNTIL_RECONCILED",
  "effective_default_authority_class": "EXPLICIT_QTT_OR_OWNER_POLICY_SEED_OR_RESOLUTION_RULE",
  "effective_fallback_behavior_when_value_unavailable": "FAIL_CLOSED_TO_REGISTERED_LOWER_SAFE_PATH_OR_NO_TRADE",
  "effective_owner_dashboard_editability_class": "READ_ONLY_SYMBOLIC",
  "effective_policy_authority": "CERTIFIED_STEP11_PARAMETER_POLICY",
  "effective_reference_range_or_structural_constraint": "{FAIL_CLOSED_TO_SIMPLER_APPROVED_PARTNER_SELECTION_OR_DIRECT_ROUTE_AND_SUPPRESS_BEST_EXECUTION_CLAIMS_UNTIL_RECONCILED}",
  "effective_resolution_class": "STATIC_ENUM",
  "effective_source_state_refs": [
    "OWNER_POLICY::EX_10E1A",
    "SOURCE_PACK::EX_10E1A"
  ],
  "effective_ui_widget_class": "FORMULA_BADGE",
  "effective_unit_or_basis": "best-execution fallback rule",
  "effective_value_source_class": "QTT_FAIL_CLOSED_BEST_EXECUTION_RULE",
  "evidence_basis_class": "FAMILY_SOURCE_PACK_PLUS_EXACT_OWNER_APPROVED_VALUE",
  "evidence_binding_rule_refs": [],
  "family_evidence_binding_ref": "ST12-FAMILY-EVIDENCE::EX_10E1A",
  "implementation_resolution_kind": "EXPLICIT_FAIL_CLOSED_POLICY",
  "launch_computability_state": "COMPUTABLE_TYPED_FAIL_CLOSED_OR_NO_TRADE_STATE",
  "master_plan_heading_path": [
    "Part II — Retained institutional design and parameter catalog",
    "D14. Canonical family registry — risk and allocation",
    "EX-10E1A — Cross-asset best-execution review, public execution-quality and routing-disclosure, and regular-and-rigorous benchmark-governance atomic parameter pack"
  ],
  "master_plan_section_id": "EX-10E1A",
  "missing_stale_invalid_behavior": "PRESERVE_EXPLICIT_FAIL_CLOSED_STATE",
  "parameter_audit_id": "ST11-PARAM::01854",
  "parameter_id": "ST10-PARAM::1854",
  "parameter_symbol": "bestex_fb",
  "precision_and_rounding_policy": {
    "allowlist_check": "REQUIRED",
    "internal_numeric_type": "typed_symbolic",
    "normalization": "CANONICAL_EXACT_TOKEN_NO_FREE_TEXT_COERCION",
    "rounding": "NOT_APPLICABLE"
  },
  "runtime_resolution_procedure": [
    "Materialize the declared fail-closed state exactly.",
    "Return a typed blocker/no-trade status and do not substitute a numeric fallback.",
    "Validate the resolved typed value or token against the effective resolution class, declared structural constraint, and canonical allowlist; on failure apply the declared fail-closed fallback and emit the exact reason code."
  ],
  "source_line_end": 52569,
  "source_line_start": 52555,
  "step12_primary_tranche_id": "ST12-TRANCHE-A"
},
{
  "canonical_owner": "QKUComputationControlPlaneV1",
  "certified_step11_custody_ref": "inputs/certified_step11/QTT_Stage1_Step11_Parameter_Policy_Adjudication_v1_0.jsonl#ST11-PARAM::01882",
  "certified_step11_row_embedded_in_prompt": false,
  "codex_online_research_allowed": false,
  "direct_source_claim_justifications": [],
  "effective_bounded_search_space_or_fit_constraint": "no cross-firm carry-transfer may proceed when the written agreement, approved destination, venue support, or reporting surface disagree",
  "effective_day1_seed_value_or_resolution_rule": "CROSS_FIRM_CARRY_TRANSFER_IS_ADMISSIBLE_ONLY_WHEN_carry_agmt_ptr_carry_dest_ptr_venue_support_ok_AND_reporting_rule_ok_ARE_ALL_TRUE_AND_MUTUALLY_CONSISTENT",
  "effective_default_authority_class": "EXPLICIT_QTT_OR_OWNER_POLICY_SEED_OR_RESOLUTION_RULE",
  "effective_fallback_behavior_when_value_unavailable": "FAIL_CLOSED_TO_REGISTERED_LOWER_SAFE_PATH_OR_NO_TRADE",
  "effective_owner_dashboard_editability_class": "READ_ONLY_BY_DEFAULT",
  "effective_policy_authority": "CERTIFIED_STEP11_PARAMETER_POLICY",
  "effective_reference_range_or_structural_constraint": "{ALL_REQUIRED_RECEIPTS_MUTUALLY_CONSISTENT_AND_TRUE, FAIL_CLOSED}",
  "effective_resolution_class": "STATIC_ENUM_OR_RULE",
  "effective_source_state_refs": [
    "OWNER_POLICY::EX_10E3A",
    "SOURCE_PACK::EX_10E3A"
  ],
  "effective_ui_widget_class": "READ_ONLY_POLICY_CARD",
  "effective_unit_or_basis": "carry-transfer consistency rule",
  "effective_value_source_class": "QTT_CARRY_TRANSFER_ADMISSIBILITY_LAW",
  "evidence_basis_class": "FAMILY_SOURCE_PACK_PLUS_EXACT_OWNER_APPROVED_VALUE",
  "evidence_binding_rule_refs": [],
  "family_evidence_binding_ref": "ST12-FAMILY-EVIDENCE::EX_10E3A",
  "implementation_resolution_kind": "STATIC_OR_DETERMINISTIC_RULE",
  "launch_computability_state": "COMPUTABLE_FROM_STATIC_VALUE_OR_DETERMINISTIC_RULE",
  "master_plan_heading_path": [
    "Part II — Retained institutional design and parameter catalog",
    "D14. Canonical family registry — risk and allocation",
    "EX-10E3A — Carrying-destination pointer resolution closure"
  ],
  "master_plan_section_id": "EX-10E3A",
  "missing_stale_invalid_behavior": "REJECT_INVALID_VALUE_NO_SILENT_DEFAULT",
  "parameter_audit_id": "ST11-PARAM::01882",
  "parameter_id": "ST10-PARAM::1882",
  "parameter_symbol": "carry_dest_cons_rule",
  "precision_and_rounding_policy": {
    "allowlist_check": "REQUIRED",
    "internal_numeric_type": "typed_symbolic",
    "normalization": "CANONICAL_EXACT_TOKEN_NO_FREE_TEXT_COERCION",
    "rounding": "NOT_APPLICABLE"
  },
  "runtime_resolution_procedure": [
    "Parse the declared Day-1 seed or deterministic rule into the declared type.",
    "Validate against the reference range and structural constraint.",
    "Apply the declared bounded edit/search law; reject any value outside it."
  ],
  "source_line_end": 52982,
  "source_line_start": 52971,
  "step12_primary_tranche_id": "ST12-TRANCHE-A"
},
{
  "canonical_owner": "QKUComputationControlPlaneV1",
  "certified_step11_custody_ref": "inputs/certified_step11/QTT_Stage1_Step11_Parameter_Policy_Adjudication_v1_0.jsonl#ST11-PARAM::01883",
  "certified_step11_row_embedded_in_prompt": false,
  "codex_online_research_allowed": false,
  "direct_source_claim_justifications": [],
  "effective_bounded_search_space_or_fit_constraint": "unresolved carrying-destination identity may not be guessed from broker folklore, prior account routing, or a similar product family",
  "effective_day1_seed_value_or_resolution_rule": "BLOCK_AUTONOMOUS_CROSS_FIRM_CARRY_TRANSFER_BLOCK_AUTONOMOUS_GIVEUP_OR_CMTA_DESTINATION_ASSUMPTIONS_AND_DOWNGRADE_TO_STRONGEST_APPROVED_SAME_FIRM_SELF_CARRY_OR_NO_TRADE_UNTIL_AUTHORITATIVE_BROKER_CLEARING_AND_AGREEMENT_RECEIPTS_RECOVER",
  "effective_default_authority_class": "EXPLICIT_QTT_OR_OWNER_POLICY_SEED_OR_RESOLUTION_RULE",
  "effective_fallback_behavior_when_value_unavailable": "FAIL_CLOSED_TO_REGISTERED_LOWER_SAFE_PATH_OR_NO_TRADE",
  "effective_owner_dashboard_editability_class": "READ_ONLY_BY_DEFAULT",
  "effective_policy_authority": "CERTIFIED_STEP11_PARAMETER_POLICY",
  "effective_reference_range_or_structural_constraint": "{BLOCK_AUTONOMOUS_CROSS_FIRM_TRANSFER_WHEN_DESTINATION_UNKNOWN, FALL_BACK_TO_EXECUTING_FIRM_SELF_CARRY_WHEN_ADMISSIBLE, OWNER_VISIBLE_NO_TRADE_WHEN_NO_APPROVED_SAME_FIRM_PATH_EXISTS}",
  "effective_resolution_class": "STATIC_ENUM_OR_RULE",
  "effective_source_state_refs": [
    "OWNER_POLICY::EX_10E3A",
    "SOURCE_PACK::EX_10E3A"
  ],
  "effective_ui_widget_class": "READ_ONLY_POLICY_CARD",
  "effective_unit_or_basis": "shared carrying-destination fail-closed rule",
  "effective_value_source_class": "QTT_FAIL_CLOSED_CARRYING_DESTINATION_RULE",
  "evidence_basis_class": "FAMILY_SOURCE_PACK_PLUS_EXACT_OWNER_APPROVED_VALUE",
  "evidence_binding_rule_refs": [],
  "family_evidence_binding_ref": "ST12-FAMILY-EVIDENCE::EX_10E3A",
  "implementation_resolution_kind": "EXPLICIT_FAIL_CLOSED_POLICY",
  "launch_computability_state": "COMPUTABLE_TYPED_FAIL_CLOSED_OR_NO_TRADE_STATE",
  "master_plan_heading_path": [
    "Part II — Retained institutional design and parameter catalog",
    "D14. Canonical family registry — risk and allocation",
    "EX-10E3A — Carrying-destination pointer resolution closure"
  ],
  "master_plan_section_id": "EX-10E3A",
  "missing_stale_invalid_behavior": "PRESERVE_EXPLICIT_FAIL_CLOSED_STATE",
  "parameter_audit_id": "ST11-PARAM::01883",
  "parameter_id": "ST10-PARAM::1883",
  "parameter_symbol": "carry_dest_fail",
  "precision_and_rounding_policy": {
    "allowlist_check": "REQUIRED",
    "internal_numeric_type": "typed_symbolic",
    "normalization": "CANONICAL_EXACT_TOKEN_NO_FREE_TEXT_COERCION",
    "rounding": "NOT_APPLICABLE"
  },
  "runtime_resolution_procedure": [
    "Materialize the declared fail-closed state exactly.",
    "Return a typed blocker/no-trade status and do not substitute a numeric fallback.",
    "Validate the resolved typed value or token against the effective resolution class, declared structural constraint, and canonical allowlist; on failure apply the declared fail-closed fallback and emit the exact reason code."
  ],
  "source_line_end": 52997,
  "source_line_start": 52983,
  "step12_primary_tranche_id": "ST12-TRANCHE-A"
},
{
  "canonical_owner": "QKUComputationControlPlaneV1",
  "certified_step11_custody_ref": "inputs/certified_step11/QTT_Stage1_Step11_Parameter_Policy_Adjudication_v1_0.jsonl#ST11-PARAM::01885",
  "certified_step11_row_embedded_in_prompt": false,
  "codex_online_research_allowed": false,
  "direct_source_claim_justifications": [],
  "effective_bounded_search_space_or_fit_constraint": "agreement requirement may not be relaxed by historical practice, operator familiarity, or one-off manual exception on a live path",
  "effective_day1_seed_value_or_resolution_rule": "WRITTEN_AGREEMENT_REQUIRED_WHEN_carry_xfer_IS_NOT_SELF_CARRY_AND_CROSS_FIRM_DESTINATION_IS_ACTIVE",
  "effective_default_authority_class": "PUBLIC_METHOD_OR_PINNED_PROVIDER_DEFAULT_REQUIRES_IMPLEMENTATION_VERSION_BINDING",
  "effective_fallback_behavior_when_value_unavailable": "FAIL_CLOSED_TO_REGISTERED_LOWER_SAFE_PATH_OR_NO_TRADE",
  "effective_owner_dashboard_editability_class": "READ_ONLY_BY_DEFAULT",
  "effective_policy_authority": "CERTIFIED_STEP11_PARAMETER_POLICY",
  "effective_reference_range_or_structural_constraint": "{WRITTEN_AGREEMENT_REQUIRED_FOR_CROSS_FIRM_TRANSFER, NOT_APPLICABLE_FOR_SELF_CARRY, FAIL_CLOSED_IF_CROSS_FIRM_TRANSFER_REQUESTED_WITHOUT_AGREEMENT}",
  "effective_resolution_class": "STATIC_ENUM_OR_RULE",
  "effective_source_state_refs": [
    "OWNER_POLICY::EX_10E3B",
    "SOURCE_PACK::EX_10E3B"
  ],
  "effective_ui_widget_class": "READ_ONLY_POLICY_CARD",
  "effective_unit_or_basis": "agreement-requirement rule",
  "effective_value_source_class": "PUBLIC_CARRYING_AGREEMENT_REQUIREMENT_WITH_QTT_CANONICAL_DEFAULT_RULE",
  "evidence_basis_class": "FAMILY_SOURCE_PACK_PLUS_EXACT_OWNER_APPROVED_VALUE",
  "evidence_binding_rule_refs": [],
  "family_evidence_binding_ref": "ST12-FAMILY-EVIDENCE::EX_10E3B",
  "implementation_resolution_kind": "STATIC_OR_DETERMINISTIC_RULE",
  "launch_computability_state": "COMPUTABLE_FROM_STATIC_VALUE_OR_DETERMINISTIC_RULE",
  "master_plan_heading_path": [
    "Part II — Retained institutional design and parameter catalog",
    "D14. Canonical family registry — risk and allocation",
    "EX-10E3B — Carry-transfer agreement-pointer resolution closure"
  ],
  "master_plan_section_id": "EX-10E3B",
  "missing_stale_invalid_behavior": "REJECT_INVALID_VALUE_NO_SILENT_DEFAULT",
  "parameter_audit_id": "ST11-PARAM::01885",
  "parameter_id": "ST10-PARAM::1885",
  "parameter_symbol": "carry_agmt_req_rule",
  "precision_and_rounding_policy": {
    "allowlist_check": "REQUIRED",
    "internal_numeric_type": "typed_symbolic",
    "normalization": "CANONICAL_EXACT_TOKEN_NO_FREE_TEXT_COERCION",
    "rounding": "NOT_APPLICABLE"
  },
  "runtime_resolution_procedure": [
    "Parse the declared Day-1 seed or deterministic rule into the declared type.",
    "Validate against the reference range and structural constraint.",
    "Apply the declared bounded edit/search law; reject any value outside it."
  ],
  "source_line_end": 53027,
  "source_line_start": 53016,
  "step12_primary_tranche_id": "ST12-TRANCHE-A"
},
{
  "canonical_owner": "QKUComputationControlPlaneV1",
  "certified_step11_custody_ref": "inputs/certified_step11/QTT_Stage1_Step11_Parameter_Policy_Adjudication_v1_0.jsonl#ST11-PARAM::01886",
  "certified_step11_row_embedded_in_prompt": false,
  "codex_online_research_allowed": false,
  "direct_source_claim_justifications": [],
  "effective_bounded_search_space_or_fit_constraint": "unresolved agreement identity may not be guessed from prior carry destinations, broker folklore, or a related product path",
  "effective_day1_seed_value_or_resolution_rule": "BLOCK_AUTONOMOUS_CROSS_FIRM_CARRY_TRANSFER_BLOCK_AUTONOMOUS_GIVEUP_OR_CMTA_AGREEMENT_ASSUMPTIONS_AND_DOWNGRADE_TO_STRONGEST_APPROVED_SELF_CARRY_OR_NO_TRADE_UNTIL_AUTHORITATIVE_BROKER_CLEARING_AND_AGREEMENT_RECEIPTS_RECOVER",
  "effective_default_authority_class": "EXPLICIT_QTT_OR_OWNER_POLICY_SEED_OR_RESOLUTION_RULE",
  "effective_fallback_behavior_when_value_unavailable": "FAIL_CLOSED_TO_REGISTERED_LOWER_SAFE_PATH_OR_NO_TRADE",
  "effective_owner_dashboard_editability_class": "READ_ONLY_BY_DEFAULT",
  "effective_policy_authority": "CERTIFIED_STEP11_PARAMETER_POLICY",
  "effective_reference_range_or_structural_constraint": "{BLOCK_AUTONOMOUS_CROSS_FIRM_TRANSFER_WHEN_AGREEMENT_UNKNOWN, FALL_BACK_TO_SELF_CARRY_WHEN_ADMISSIBLE, OWNER_VISIBLE_NO_TRADE_WHEN_NO_APPROVED_SELF_CARRY_PATH_EXISTS}",
  "effective_resolution_class": "STATIC_ENUM_OR_RULE",
  "effective_source_state_refs": [
    "OWNER_POLICY::EX_10E3B",
    "SOURCE_PACK::EX_10E3B"
  ],
  "effective_ui_widget_class": "READ_ONLY_POLICY_CARD",
  "effective_unit_or_basis": "shared carry-transfer-agreement fail-closed rule",
  "effective_value_source_class": "QTT_FAIL_CLOSED_CARRY_TRANSFER_AGREEMENT_RULE",
  "evidence_basis_class": "FAMILY_SOURCE_PACK_PLUS_EXACT_OWNER_APPROVED_VALUE",
  "evidence_binding_rule_refs": [],
  "family_evidence_binding_ref": "ST12-FAMILY-EVIDENCE::EX_10E3B",
  "implementation_resolution_kind": "EXPLICIT_FAIL_CLOSED_POLICY",
  "launch_computability_state": "COMPUTABLE_TYPED_FAIL_CLOSED_OR_NO_TRADE_STATE",
  "master_plan_heading_path": [
    "Part II — Retained institutional design and parameter catalog",
    "D14. Canonical family registry — risk and allocation",
    "EX-10E3B — Carry-transfer agreement-pointer resolution closure"
  ],
  "master_plan_section_id": "EX-10E3B",
  "missing_stale_invalid_behavior": "PRESERVE_EXPLICIT_FAIL_CLOSED_STATE",
  "parameter_audit_id": "ST11-PARAM::01886",
  "parameter_id": "ST10-PARAM::1886",
  "parameter_symbol": "carry_agmt_fail",
  "precision_and_rounding_policy": {
    "allowlist_check": "REQUIRED",
    "internal_numeric_type": "typed_symbolic",
    "normalization": "CANONICAL_EXACT_TOKEN_NO_FREE_TEXT_COERCION",
    "rounding": "NOT_APPLICABLE"
  },
  "runtime_resolution_procedure": [
    "Materialize the declared fail-closed state exactly.",
    "Return a typed blocker/no-trade status and do not substitute a numeric fallback.",
    "Validate the resolved typed value or token against the effective resolution class, declared structural constraint, and canonical allowlist; on failure apply the declared fail-closed fallback and emit the exact reason code."
  ],
  "source_line_end": 53042,
  "source_line_start": 53028,
  "step12_primary_tranche_id": "ST12-TRANCHE-A"
},
{
  "canonical_owner": "QKUComputationControlPlaneV1",
  "certified_step11_custody_ref": "inputs/certified_step11/QTT_Stage1_Step11_Parameter_Policy_Adjudication_v1_0.jsonl#ST11-PARAM::01896",
  "certified_step11_row_embedded_in_prompt": false,
  "codex_online_research_allowed": false,
  "direct_source_claim_justifications": [],
  "effective_bounded_search_space_or_fit_constraint": "allocation ambiguity may not silently resolve into affirmed booking or downstream account movement",
  "effective_day1_seed_value_or_resolution_rule": "FAIL_CLOSED_TO_UNALLOCATED_EXCEPTION_STATE_AND_NO_DOWNSTREAM_MULTI_ACCOUNT_BOOKING_UNTIL_AUTHORITATIVE_RECONCILIATION_COMPLETES",
  "effective_default_authority_class": "EXPLICIT_QTT_OR_OWNER_POLICY_SEED_OR_RESOLUTION_RULE",
  "effective_fallback_behavior_when_value_unavailable": "FAIL_CLOSED_TO_REGISTERED_LOWER_SAFE_PATH_OR_NO_TRADE",
  "effective_owner_dashboard_editability_class": "READ_ONLY_SYMBOLIC",
  "effective_policy_authority": "CERTIFIED_STEP11_PARAMETER_POLICY",
  "effective_reference_range_or_structural_constraint": "{FAIL_CLOSED_TO_UNALLOCATED_EXCEPTION_STATE_AND_NO_DOWNSTREAM_MULTI_ACCOUNT_BOOKING_UNTIL_AUTHORITATIVE_RECONCILIATION_COMPLETES}",
  "effective_resolution_class": "STATIC_ENUM",
  "effective_source_state_refs": [
    "OWNER_POLICY::EX_10E4",
    "SOURCE_PACK::EX_10E4"
  ],
  "effective_ui_widget_class": "FORMULA_BADGE",
  "effective_unit_or_basis": "allocation fallback rule",
  "effective_value_source_class": "QTT_FAIL_CLOSED_POST_TRADE_ALLOCATION_RULE",
  "evidence_basis_class": "FAMILY_SOURCE_PACK_PLUS_EXACT_OWNER_APPROVED_VALUE",
  "evidence_binding_rule_refs": [],
  "family_evidence_binding_ref": "ST12-FAMILY-EVIDENCE::EX_10E4",
  "implementation_resolution_kind": "EXPLICIT_FAIL_CLOSED_POLICY",
  "launch_computability_state": "COMPUTABLE_TYPED_FAIL_CLOSED_OR_NO_TRADE_STATE",
  "master_plan_heading_path": [
    "Part II — Retained institutional design and parameter catalog",
    "D14. Canonical family registry — risk and allocation",
    "EX-10E4 — Cross-asset post-trade allocation, allocation-instruction, allocation-report, and average-price-group atomic parameter pack"
  ],
  "master_plan_section_id": "EX-10E4",
  "missing_stale_invalid_behavior": "PRESERVE_EXPLICIT_FAIL_CLOSED_STATE",
  "parameter_audit_id": "ST11-PARAM::01896",
  "parameter_id": "ST10-PARAM::1896",
  "parameter_symbol": "alloc_fb",
  "precision_and_rounding_policy": {
    "allowlist_check": "REQUIRED",
    "internal_numeric_type": "typed_symbolic",
    "normalization": "CANONICAL_EXACT_TOKEN_NO_FREE_TEXT_COERCION",
    "rounding": "NOT_APPLICABLE"
  },
  "runtime_resolution_procedure": [
    "Materialize the declared fail-closed state exactly.",
    "Return a typed blocker/no-trade status and do not substitute a numeric fallback.",
    "Validate the resolved typed value or token against the effective resolution class, declared structural constraint, and canonical allowlist; on failure apply the declared fail-closed fallback and emit the exact reason code."
  ],
  "source_line_end": 53172,
  "source_line_start": 53158,
  "step12_primary_tranche_id": "ST12-TRANCHE-A"
},
{
  "canonical_owner": "QKUComputationControlPlaneV1",
  "certified_step11_custody_ref": "inputs/certified_step11/QTT_Stage1_Step11_Parameter_Policy_Adjudication_v1_0.jsonl#ST11-PARAM::01898",
  "certified_step11_row_embedded_in_prompt": false,
  "codex_online_research_allowed": false,
  "direct_source_claim_justifications": [],
  "effective_bounded_search_space_or_fit_constraint": "QTT may not silently synthesize downstream account splits from historical patterns or convenience defaults when the message class intentionally omits them",
  "effective_day1_seed_value_or_resolution_rule": "IF_ALLOC_TYPE_IS_READY_TO_BOOK_OR_WAREHOUSE_INSTRUCTION_WITHOUT_ALLOCACCOUNT_BREAKOUT_ALLOW_BLOCK_LEVEL_READY_TO_BOOK_STATE_ONLY_AND_REQUIRE_SUBSEQUENT_AUTHORITATIVE_ACCOUNT_LEVEL_INSTRUCTION_BEFORE_ACCOUNT_BOOKDOWN_CONFIRMATION_OR_NETMONEY_FINALIZATION",
  "effective_default_authority_class": "PUBLIC_METHOD_OR_PINNED_PROVIDER_DEFAULT_REQUIRES_IMPLEMENTATION_VERSION_BINDING",
  "effective_fallback_behavior_when_value_unavailable": "FAIL_CLOSED_TO_REGISTERED_LOWER_SAFE_PATH_OR_NO_TRADE",
  "effective_owner_dashboard_editability_class": "READ_ONLY_BY_DEFAULT",
  "effective_policy_authority": "CERTIFIED_STEP11_PARAMETER_POLICY",
  "effective_reference_range_or_structural_constraint": "{BLOCK_LEVEL_READY_TO_BOOK_ONLY_PENDING_ACCOUNT_BREAKOUT, EXPLICIT_ACCOUNT_BREAKOUT_ALREADY_PRESENT, FAIL_CLOSED_IF_ACCOUNT_LEVEL_BOOKDOWN_IS_REQUESTED_WITHOUT_ACCOUNT_SET}",
  "effective_resolution_class": "STATIC_ENUM_OR_RULE",
  "effective_source_state_refs": [
    "OWNER_POLICY::EX_10E4A",
    "SOURCE_PACK::EX_10E4A"
  ],
  "effective_ui_widget_class": "READ_ONLY_POLICY_CARD",
  "effective_unit_or_basis": "ready-to-book account-breakout rule",
  "effective_value_source_class": "PUBLIC_FIX_POSTTRADE_READY_TO_BOOK_REFERENCE_WITH_QTT_CANONICAL_DEFAULT_RULE",
  "evidence_basis_class": "FAMILY_SOURCE_PACK_PLUS_EXACT_OWNER_APPROVED_VALUE",
  "evidence_binding_rule_refs": [],
  "family_evidence_binding_ref": "ST12-FAMILY-EVIDENCE::EX_10E4A",
  "implementation_resolution_kind": "STATIC_OR_DETERMINISTIC_RULE",
  "launch_computability_state": "COMPUTABLE_FROM_STATIC_VALUE_OR_DETERMINISTIC_RULE",
  "master_plan_heading_path": [
    "Part II — Retained institutional design and parameter catalog",
    "D14. Canonical family registry — risk and allocation",
    "EX-10E4A — Allocation-account-scope pointer resolution closure"
  ],
  "master_plan_section_id": "EX-10E4A",
  "missing_stale_invalid_behavior": "REJECT_INVALID_VALUE_NO_SILENT_DEFAULT",
  "parameter_audit_id": "ST11-PARAM::01898",
  "parameter_id": "ST10-PARAM::1898",
  "parameter_symbol": "alloc_rtb_scope_rule",
  "precision_and_rounding_policy": {
    "allowlist_check": "REQUIRED",
    "internal_numeric_type": "typed_symbolic",
    "normalization": "CANONICAL_EXACT_TOKEN_NO_FREE_TEXT_COERCION",
    "rounding": "NOT_APPLICABLE"
  },
  "runtime_resolution_procedure": [
    "Parse the declared Day-1 seed or deterministic rule into the declared type.",
    "Validate against the reference range and structural constraint.",
    "Apply the declared bounded edit/search law; reject any value outside it."
  ],
  "source_line_end": 53202,
  "source_line_start": 53191,
  "step12_primary_tranche_id": "ST12-TRANCHE-A"
},
{
  "canonical_owner": "QKUComputationControlPlaneV1",
  "certified_step11_custody_ref": "inputs/certified_step11/QTT_Stage1_Step11_Parameter_Policy_Adjudication_v1_0.jsonl#ST11-PARAM::01899",
  "certified_step11_row_embedded_in_prompt": false,
  "codex_online_research_allowed": false,
  "direct_source_claim_justifications": [],
  "effective_bounded_search_space_or_fit_constraint": "unresolved account scope may not be guessed from stale allocations, habitual subaccount mappings, or one broker-side default mnemonic",
  "effective_day1_seed_value_or_resolution_rule": "BLOCK_ACCOUNT_LEVEL_BOOKDOWN_BLOCK_ACCOUNT_LEVEL_CONFIRMATION_BLOCK_FINAL_SUBACCOUNT_NETMONEY_AND_DOWNGRADE_TO_OWNER_VISIBLE_ALLOCATION_RECONCILIATION_PENDING_AUTHORITATIVE_ALLOCATIONINSTRUCTION_OR_SCOPE_CARD_RECOVERY",
  "effective_default_authority_class": "EXPLICIT_QTT_OR_OWNER_POLICY_SEED_OR_RESOLUTION_RULE",
  "effective_fallback_behavior_when_value_unavailable": "FAIL_CLOSED_TO_REGISTERED_LOWER_SAFE_PATH_OR_NO_TRADE",
  "effective_owner_dashboard_editability_class": "READ_ONLY_BY_DEFAULT",
  "effective_policy_authority": "CERTIFIED_STEP11_PARAMETER_POLICY",
  "effective_reference_range_or_structural_constraint": "{BLOCK_ACCOUNT_LEVEL_BOOKDOWN_WHEN_SCOPE_UNKNOWN, BLOCK_CONFIRMATION_AND_NETMONEY_FINALITY_WHEN_ACCOUNT_SET_UNKNOWN, OWNER_VISIBLE_RECONCILIATION_PENDING_RECOVERY}",
  "effective_resolution_class": "STATIC_ENUM_OR_RULE",
  "effective_source_state_refs": [
    "OWNER_POLICY::EX_10E4A",
    "SOURCE_PACK::EX_10E4A"
  ],
  "effective_ui_widget_class": "READ_ONLY_POLICY_CARD",
  "effective_unit_or_basis": "shared allocation-account-scope fail-closed rule",
  "effective_value_source_class": "QTT_FAIL_CLOSED_ALLOCATION_ACCOUNT_SCOPE_RULE",
  "evidence_basis_class": "FAMILY_SOURCE_PACK_PLUS_EXACT_OWNER_APPROVED_VALUE",
  "evidence_binding_rule_refs": [],
  "family_evidence_binding_ref": "ST12-FAMILY-EVIDENCE::EX_10E4A",
  "implementation_resolution_kind": "STATIC_OR_DETERMINISTIC_RULE",
  "launch_computability_state": "COMPUTABLE_FROM_STATIC_VALUE_OR_DETERMINISTIC_RULE",
  "master_plan_heading_path": [
    "Part II — Retained institutional design and parameter catalog",
    "D14. Canonical family registry — risk and allocation",
    "EX-10E4A — Allocation-account-scope pointer resolution closure"
  ],
  "master_plan_section_id": "EX-10E4A",
  "missing_stale_invalid_behavior": "REJECT_INVALID_VALUE_NO_SILENT_DEFAULT",
  "parameter_audit_id": "ST11-PARAM::01899",
  "parameter_id": "ST10-PARAM::1899",
  "parameter_symbol": "alloc_scope_fail",
  "precision_and_rounding_policy": {
    "allowlist_check": "REQUIRED",
    "internal_numeric_type": "typed_symbolic",
    "normalization": "CANONICAL_EXACT_TOKEN_NO_FREE_TEXT_COERCION",
    "rounding": "NOT_APPLICABLE"
  },
  "runtime_resolution_procedure": [
    "Parse the declared Day-1 seed or deterministic rule into the declared type.",
    "Validate against the reference range and structural constraint.",
    "Apply the declared bounded edit/search law; reject any value outside it."
  ],
  "source_line_end": 53217,
  "source_line_start": 53203,
  "step12_primary_tranche_id": "ST12-TRANCHE-A"
},
{
  "canonical_owner": "QKUComputationControlPlaneV1",
  "certified_step11_custody_ref": "inputs/certified_step11/QTT_Stage1_Step11_Parameter_Policy_Adjudication_v1_0.jsonl#ST11-PARAM::01920",
  "certified_step11_row_embedded_in_prompt": false,
  "codex_online_research_allowed": false,
  "direct_source_claim_justifications": [],
  "effective_bounded_search_space_or_fit_constraint": "canonical root-length widening is forbidden unless a later canonical master plan adopts a different official standard with a lossless migration receipt",
  "effective_day1_seed_value_or_resolution_rule": "6",
  "effective_default_authority_class": "PUBLIC_METHOD_OR_PINNED_PROVIDER_DEFAULT_REQUIRES_IMPLEMENTATION_VERSION_BINDING",
  "effective_fallback_behavior_when_value_unavailable": "FAIL_CLOSED_TO_REGISTERED_LOWER_SAFE_PATH_OR_NO_TRADE",
  "effective_owner_dashboard_editability_class": "READ_ONLY_BY_DEFAULT",
  "effective_policy_authority": "CERTIFIED_STEP11_PARAMETER_POLICY",
  "effective_reference_range_or_structural_constraint": "exact integer `6` characters for the canonical root field",
  "effective_resolution_class": "STATIC_NUMERIC",
  "effective_source_state_refs": [
    "OWNER_POLICY::EX_10I0",
    "SOURCE_PACK::EX_10I0"
  ],
  "effective_ui_widget_class": "READ_ONLY_NUMERIC",
  "effective_unit_or_basis": "characters",
  "effective_value_source_class": "PUBLIC_LISTED_OPTION_SYMBOLOGY_STANDARD",
  "evidence_basis_class": "FAMILY_SOURCE_PACK_PLUS_EXACT_OWNER_APPROVED_VALUE",
  "evidence_binding_rule_refs": [],
  "family_evidence_binding_ref": "ST12-FAMILY-EVIDENCE::EX_10I0",
  "implementation_resolution_kind": "STATIC_OR_DETERMINISTIC_RULE",
  "launch_computability_state": "COMPUTABLE_FROM_STATIC_VALUE_OR_DETERMINISTIC_RULE",
  "master_plan_heading_path": [
    "Part II — Retained institutional design and parameter catalog",
    "D14. Canonical family registry — risk and allocation",
    "EX-10I0 — Listed-option symbology, series-key, and OSI normalization atomic parameter pack"
  ],
  "master_plan_section_id": "EX-10I0",
  "missing_stale_invalid_behavior": "REJECT_INVALID_VALUE_NO_SILENT_DEFAULT",
  "parameter_audit_id": "ST11-PARAM::01920",
  "parameter_id": "ST10-PARAM::1920",
  "parameter_symbol": "opt_root_len",
  "precision_and_rounding_policy": {
    "finite_check": "REQUIRED",
    "internal_numeric_type": "float64_or_declared_array_dtype",
    "probability_domain": "[0,1] WHEN APPLICABLE",
    "rounding": "NONE_INTERNAL; CONVERT_TO_DECIMAL_AT_FINANCIAL_BOUNDARY"
  },
  "runtime_resolution_procedure": [
    "Parse the declared Day-1 seed or deterministic rule into the declared type.",
    "Validate against the reference range and structural constraint.",
    "Apply the declared bounded edit/search law; reject any value outside it."
  ],
  "source_line_end": 53498,
  "source_line_start": 53487,
  "step12_primary_tranche_id": "ST12-TRANCHE-A"
},
{
  "canonical_owner": "QKUComputationControlPlaneV1",
  "certified_step11_custody_ref": "inputs/certified_step11/QTT_Stage1_Step11_Parameter_Policy_Adjudication_v1_0.jsonl#ST11-PARAM::01921",
  "certified_step11_row_embedded_in_prompt": false,
  "codex_online_research_allowed": false,
  "direct_source_claim_justifications": [],
  "effective_bounded_search_space_or_fit_constraint": "root padding may not be stripped or collapsed before canonical identity hashing if the fixed-width canonical key is the authoritative machine identifier",
  "effective_day1_seed_value_or_resolution_rule": "RIGHT_PAD_SPACES_TO_CANONICAL_ROOT_FIELD_WIDTH",
  "effective_default_authority_class": "PUBLIC_METHOD_OR_PINNED_PROVIDER_DEFAULT_REQUIRES_IMPLEMENTATION_VERSION_BINDING",
  "effective_fallback_behavior_when_value_unavailable": "FAIL_CLOSED_TO_REGISTERED_LOWER_SAFE_PATH_OR_NO_TRADE",
  "effective_owner_dashboard_editability_class": "READ_ONLY_BY_DEFAULT",
  "effective_policy_authority": "CERTIFIED_STEP11_PARAMETER_POLICY",
  "effective_reference_range_or_structural_constraint": "{RIGHT_PAD_SPACES_TO_CANONICAL_ROOT_FIELD_WIDTH, LOSSLESS_TYPED_STRUCT_NORMALIZATION_WITH_EQUIVALENT_FIXED_WIDTH_RENDER}",
  "effective_resolution_class": "STATIC_ENUM",
  "effective_source_state_refs": [
    "OWNER_POLICY::EX_10I0",
    "SOURCE_PACK::EX_10I0"
  ],
  "effective_ui_widget_class": "READ_ONLY_ENUM_CARD",
  "effective_unit_or_basis": "root-padding rule enum",
  "effective_value_source_class": "PUBLIC_LISTED_OPTION_SYMBOLOGY_STANDARD_WITH_QTT_NORMALIZATION_RULE",
  "evidence_basis_class": "FAMILY_SOURCE_PACK_PLUS_EXACT_OWNER_APPROVED_VALUE",
  "evidence_binding_rule_refs": [],
  "family_evidence_binding_ref": "ST12-FAMILY-EVIDENCE::EX_10I0",
  "implementation_resolution_kind": "STATIC_OR_DETERMINISTIC_RULE",
  "launch_computability_state": "COMPUTABLE_FROM_STATIC_VALUE_OR_DETERMINISTIC_RULE",
  "master_plan_heading_path": [
    "Part II — Retained institutional design and parameter catalog",
    "D14. Canonical family registry — risk and allocation",
    "EX-10I0 — Listed-option symbology, series-key, and OSI normalization atomic parameter pack"
  ],
  "master_plan_section_id": "EX-10I0",
  "missing_stale_invalid_behavior": "REJECT_INVALID_VALUE_NO_SILENT_DEFAULT",
  "parameter_audit_id": "ST11-PARAM::01921",
  "parameter_id": "ST10-PARAM::1921",
  "parameter_symbol": "opt_root_pad",
  "precision_and_rounding_policy": {
    "allowlist_check": "REQUIRED",
    "internal_numeric_type": "typed_symbolic",
    "normalization": "CANONICAL_EXACT_TOKEN_NO_FREE_TEXT_COERCION",
    "rounding": "NOT_APPLICABLE"
  },
  "runtime_resolution_procedure": [
    "Parse the declared Day-1 seed or deterministic rule into the declared type.",
    "Validate against the reference range and structural constraint.",
    "Apply the declared bounded edit/search law; reject any value outside it."
  ],
  "source_line_end": 53510,
  "source_line_start": 53499,
  "step12_primary_tranche_id": "ST12-TRANCHE-A"
},
{
  "canonical_owner": "QKUComputationControlPlaneV1",
  "certified_step11_custody_ref": "inputs/certified_step11/QTT_Stage1_Step11_Parameter_Policy_Adjudication_v1_0.jsonl#ST11-PARAM::01922",
  "certified_step11_row_embedded_in_prompt": false,
  "codex_online_research_allowed": false,
  "direct_source_claim_justifications": [],
  "effective_bounded_search_space_or_fit_constraint": "alternate display-date renderings may exist in UI surfaces but may not replace the canonical machine identity basis",
  "effective_day1_seed_value_or_resolution_rule": "YYMMDD",
  "effective_default_authority_class": "PUBLIC_METHOD_OR_PINNED_PROVIDER_DEFAULT_REQUIRES_IMPLEMENTATION_VERSION_BINDING",
  "effective_fallback_behavior_when_value_unavailable": "FAIL_CLOSED_TO_REGISTERED_LOWER_SAFE_PATH_OR_NO_TRADE",
  "effective_owner_dashboard_editability_class": "READ_ONLY_BY_DEFAULT",
  "effective_policy_authority": "CERTIFIED_STEP11_PARAMETER_POLICY",
  "effective_reference_range_or_structural_constraint": "`{YYMMDD}` on the canonical standardized series key",
  "effective_resolution_class": "STATIC_ENUM",
  "effective_source_state_refs": [
    "OWNER_POLICY::EX_10I0",
    "SOURCE_PACK::EX_10I0"
  ],
  "effective_ui_widget_class": "READ_ONLY_ENUM_CARD",
  "effective_unit_or_basis": "expiration-date encoding enum",
  "effective_value_source_class": "PUBLIC_LISTED_OPTION_SYMBOLOGY_STANDARD",
  "evidence_basis_class": "FAMILY_SOURCE_PACK_PLUS_EXACT_OWNER_APPROVED_VALUE",
  "evidence_binding_rule_refs": [],
  "family_evidence_binding_ref": "ST12-FAMILY-EVIDENCE::EX_10I0",
  "implementation_resolution_kind": "STATIC_OR_DETERMINISTIC_RULE",
  "launch_computability_state": "COMPUTABLE_FROM_STATIC_VALUE_OR_DETERMINISTIC_RULE",
  "master_plan_heading_path": [
    "Part II — Retained institutional design and parameter catalog",
    "D14. Canonical family registry — risk and allocation",
    "EX-10I0 — Listed-option symbology, series-key, and OSI normalization atomic parameter pack"
  ],
  "master_plan_section_id": "EX-10I0",
  "missing_stale_invalid_behavior": "REJECT_INVALID_VALUE_NO_SILENT_DEFAULT",
  "parameter_audit_id": "ST11-PARAM::01922",
  "parameter_id": "ST10-PARAM::1922",
  "parameter_symbol": "opt_exp_enc",
  "precision_and_rounding_policy": {
    "allowlist_check": "REQUIRED",
    "internal_numeric_type": "typed_symbolic",
    "normalization": "CANONICAL_EXACT_TOKEN_NO_FREE_TEXT_COERCION",
    "rounding": "NOT_APPLICABLE"
  },
  "runtime_resolution_procedure": [
    "Parse the declared Day-1 seed or deterministic rule into the declared type.",
    "Validate against the reference range and structural constraint.",
    "Apply the declared bounded edit/search law; reject any value outside it."
  ],
  "source_line_end": 53522,
  "source_line_start": 53511,
  "step12_primary_tranche_id": "ST12-TRANCHE-A"
},
{
  "canonical_owner": "QKUComputationControlPlaneV1",
  "certified_step11_custody_ref": "inputs/certified_step11/QTT_Stage1_Step11_Parameter_Policy_Adjudication_v1_0.jsonl#ST11-PARAM::01923",
  "certified_step11_row_embedded_in_prompt": false,
  "codex_online_research_allowed": false,
  "direct_source_claim_justifications": [],
  "effective_bounded_search_space_or_fit_constraint": "verbose display strings such as `PUT` or `CALL` may exist in UI layers but may not replace the canonical machine field in transport or identity hashing",
  "effective_day1_seed_value_or_resolution_rule": "{P,C}",
  "effective_default_authority_class": "PUBLIC_METHOD_OR_PINNED_PROVIDER_DEFAULT_REQUIRES_IMPLEMENTATION_VERSION_BINDING",
  "effective_fallback_behavior_when_value_unavailable": "FAIL_CLOSED_TO_REGISTERED_LOWER_SAFE_PATH_OR_NO_TRADE",
  "effective_owner_dashboard_editability_class": "READ_ONLY_BY_DEFAULT",
  "effective_policy_authority": "CERTIFIED_STEP11_PARAMETER_POLICY",
  "effective_reference_range_or_structural_constraint": "exact two-value set `{P,C}` for the canonical put-call designator field",
  "effective_resolution_class": "STATIC_ENUM_SET",
  "effective_source_state_refs": [
    "OWNER_POLICY::EX_10I0",
    "SOURCE_PACK::EX_10I0"
  ],
  "effective_ui_widget_class": "READ_ONLY_ENUM_CARD",
  "effective_unit_or_basis": "put-call designator enum set",
  "effective_value_source_class": "PUBLIC_LISTED_OPTION_SYMBOLOGY_STANDARD",
  "evidence_basis_class": "FAMILY_SOURCE_PACK_PLUS_EXACT_OWNER_APPROVED_VALUE",
  "evidence_binding_rule_refs": [],
  "family_evidence_binding_ref": "ST12-FAMILY-EVIDENCE::EX_10I0",
  "implementation_resolution_kind": "STATIC_OR_DETERMINISTIC_RULE",
  "launch_computability_state": "COMPUTABLE_FROM_STATIC_VALUE_OR_DETERMINISTIC_RULE",
  "master_plan_heading_path": [
    "Part II — Retained institutional design and parameter catalog",
    "D14. Canonical family registry — risk and allocation",
    "EX-10I0 — Listed-option symbology, series-key, and OSI normalization atomic parameter pack"
  ],
  "master_plan_section_id": "EX-10I0",
  "missing_stale_invalid_behavior": "REJECT_INVALID_VALUE_NO_SILENT_DEFAULT",
  "parameter_audit_id": "ST11-PARAM::01923",
  "parameter_id": "ST10-PARAM::1923",
  "parameter_symbol": "opt_pc_prof",
  "precision_and_rounding_policy": {
    "allowlist_check": "REQUIRED",
    "internal_numeric_type": "typed_symbolic",
    "normalization": "CANONICAL_EXACT_TOKEN_NO_FREE_TEXT_COERCION",
    "rounding": "NOT_APPLICABLE"
  },
  "runtime_resolution_procedure": [
    "Parse the declared Day-1 seed or deterministic rule into the declared type.",
    "Validate against the reference range and structural constraint.",
    "Apply the declared bounded edit/search law; reject any value outside it."
  ],
  "source_line_end": 53534,
  "source_line_start": 53523,
  "step12_primary_tranche_id": "ST12-TRANCHE-A"
},
{
  "canonical_owner": "QKUComputationControlPlaneV1",
  "certified_step11_custody_ref": "inputs/certified_step11/QTT_Stage1_Step11_Parameter_Policy_Adjudication_v1_0.jsonl#ST11-PARAM::01924",
  "certified_step11_row_embedded_in_prompt": false,
  "codex_online_research_allowed": false,
  "direct_source_claim_justifications": [],
  "effective_bounded_search_space_or_fit_constraint": "display strike formatting may vary, but canonical machine identity must preserve the fixed-width scaled strike basis",
  "effective_day1_seed_value_or_resolution_rule": "ENCODE_STRIKE_AS_DECIMAL_PRICE_SCALED_BY_1000_AND_ZERO_PAD_TO_8_DIGITS",
  "effective_default_authority_class": "PUBLIC_METHOD_OR_PINNED_PROVIDER_DEFAULT_REQUIRES_IMPLEMENTATION_VERSION_BINDING",
  "effective_fallback_behavior_when_value_unavailable": "FAIL_CLOSED_TO_REGISTERED_LOWER_SAFE_PATH_OR_NO_TRADE",
  "effective_owner_dashboard_editability_class": "READ_ONLY_BY_DEFAULT",
  "effective_policy_authority": "CERTIFIED_STEP11_PARAMETER_POLICY",
  "effective_reference_range_or_structural_constraint": "fixed standardized strike encoding with three implied decimal places on an eight-digit field",
  "effective_resolution_class": "STATIC_FORMULA_WITH_FIXED_WIDTH_RULE",
  "effective_source_state_refs": [
    "OWNER_POLICY::EX_10I0",
    "SOURCE_PACK::EX_10I0"
  ],
  "effective_ui_widget_class": "READ_ONLY_FORMULA_CARD",
  "effective_unit_or_basis": "fixed-width scaled-strike encoding rule",
  "effective_value_source_class": "PUBLIC_LISTED_OPTION_SYMBOLOGY_STANDARD",
  "evidence_basis_class": "FAMILY_SOURCE_PACK_PLUS_EXACT_OWNER_APPROVED_VALUE",
  "evidence_binding_rule_refs": [],
  "family_evidence_binding_ref": "ST12-FAMILY-EVIDENCE::EX_10I0",
  "implementation_resolution_kind": "STATIC_OR_DETERMINISTIC_RULE",
  "launch_computability_state": "COMPUTABLE_FROM_STATIC_VALUE_OR_DETERMINISTIC_RULE",
  "master_plan_heading_path": [
    "Part II — Retained institutional design and parameter catalog",
    "D14. Canonical family registry — risk and allocation",
    "EX-10I0 — Listed-option symbology, series-key, and OSI normalization atomic parameter pack"
  ],
  "master_plan_section_id": "EX-10I0",
  "missing_stale_invalid_behavior": "REJECT_INVALID_VALUE_NO_SILENT_DEFAULT",
  "parameter_audit_id": "ST11-PARAM::01924",
  "parameter_id": "ST10-PARAM::1924",
  "parameter_symbol": "opt_strike_scale",
  "precision_and_rounding_policy": {
    "allowlist_check": "REQUIRED",
    "internal_numeric_type": "typed_symbolic",
    "normalization": "CANONICAL_EXACT_TOKEN_NO_FREE_TEXT_COERCION",
    "rounding": "NOT_APPLICABLE"
  },
  "runtime_resolution_procedure": [
    "Parse the declared Day-1 seed or deterministic rule into the declared type.",
    "Validate against the reference range and structural constraint.",
    "Apply the declared bounded edit/search law; reject any value outside it."
  ],
  "source_line_end": 53546,
  "source_line_start": 53535,
  "step12_primary_tranche_id": "ST12-TRANCHE-A"
},
{
  "canonical_owner": "QKUComputationControlPlaneV1",
  "certified_step11_custody_ref": "inputs/certified_step11/QTT_Stage1_Step11_Parameter_Policy_Adjudication_v1_0.jsonl#ST11-PARAM::01933",
  "certified_step11_row_embedded_in_prompt": false,
  "codex_online_research_allowed": false,
  "direct_source_claim_justifications": [],
  "effective_bounded_search_space_or_fit_constraint": "read-only on live paths",
  "effective_day1_seed_value_or_resolution_rule": "quoted_premium_per_share * contract_multiplier * number_of_contracts",
  "effective_default_authority_class": "PUBLIC_METHOD_OR_PINNED_PROVIDER_DEFAULT_REQUIRES_IMPLEMENTATION_VERSION_BINDING",
  "effective_fallback_behavior_when_value_unavailable": "FAIL_CLOSED_TO_REGISTERED_LOWER_SAFE_PATH_OR_NO_TRADE",
  "effective_owner_dashboard_editability_class": "READ_ONLY_BY_DEFAULT",
  "effective_policy_authority": "CERTIFIED_STEP11_PARAMETER_POLICY",
  "effective_reference_range_or_structural_constraint": "quoted premium is per share; total premium must apply the active contract multiplier",
  "effective_resolution_class": "STATIC_FORMULA",
  "effective_source_state_refs": [
    "OWNER_POLICY::EX_10I",
    "SOURCE_PACK::EX_10I"
  ],
  "effective_ui_widget_class": "READ_ONLY_FORMULA_CARD",
  "effective_unit_or_basis": "USD total premium formula",
  "effective_value_source_class": "PUBLIC_OFFICIAL_PRODUCT_STANDARD",
  "evidence_basis_class": "FAMILY_SOURCE_PACK_PLUS_EXACT_OWNER_APPROVED_VALUE",
  "evidence_binding_rule_refs": [],
  "family_evidence_binding_ref": "ST12-FAMILY-EVIDENCE::EX_10I",
  "implementation_resolution_kind": "STATIC_OR_DETERMINISTIC_RULE",
  "launch_computability_state": "COMPUTABLE_FROM_STATIC_VALUE_OR_DETERMINISTIC_RULE",
  "master_plan_heading_path": [
    "Part II — Retained institutional design and parameter catalog",
    "D14. Canonical family registry — risk and allocation",
    "EX-10I — Listed-option contract-convention, premium-basis, and minimum-price-variation atomic parameter pack"
  ],
  "master_plan_section_id": "EX-10I",
  "missing_stale_invalid_behavior": "REJECT_INVALID_VALUE_NO_SILENT_DEFAULT",
  "parameter_audit_id": "ST11-PARAM::01933",
  "parameter_id": "ST10-PARAM::1933",
  "parameter_symbol": "opt_prem_eq",
  "precision_and_rounding_policy": {
    "decimal_context_precision": 34,
    "internal_numeric_type": "Decimal",
    "nonfinite_policy": "REJECT",
    "quantization": "SOURCE_OR_UNIT_DECLARED; NO_IMPLICIT_BINARY_FLOAT_CONVERSION",
    "rounding": "ROUND_HALF_EVEN"
  },
  "runtime_resolution_procedure": [
    "Parse the declared Day-1 seed or deterministic rule into the declared type.",
    "Validate against the reference range and structural constraint.",
    "Apply the declared bounded edit/search law; reject any value outside it."
  ],
  "source_line_end": 53671,
  "source_line_start": 53660,
  "step12_primary_tranche_id": "ST12-TRANCHE-A"
},
{
  "canonical_owner": "QKUComputationControlPlaneV1",
  "certified_step11_custody_ref": "inputs/certified_step11/QTT_Stage1_Step11_Parameter_Policy_Adjudication_v1_0.jsonl#ST11-PARAM::01943",
  "certified_step11_row_embedded_in_prompt": false,
  "codex_online_research_allowed": false,
  "direct_source_claim_justifications": [],
  "effective_bounded_search_space_or_fit_constraint": "unresolved listed-option identity or penny-class state may not be guessed from stale local caches, trader shorthand, or vendor display text",
  "effective_day1_seed_value_or_resolution_rule": "BLOCK_ANY_PATH_THAT_REQUIRES_AMBIGUOUS_SERIES_IDENTITY_AND_DOWNGRADE_ANY_PENNY_AMBIGUITY_TO_NON_PENNY_MPVS_ONLY_WHILE_REMAINING_OWNER_VISIBLE_UNTIL_AUTHORITATIVE_RECOVERY",
  "effective_default_authority_class": "EXPLICIT_QTT_OR_OWNER_POLICY_SEED_OR_RESOLUTION_RULE",
  "effective_fallback_behavior_when_value_unavailable": "FAIL_CLOSED_TO_REGISTERED_LOWER_SAFE_PATH_OR_NO_TRADE",
  "effective_owner_dashboard_editability_class": "READ_ONLY_BY_DEFAULT",
  "effective_policy_authority": "CERTIFIED_STEP11_PARAMETER_POLICY",
  "effective_reference_range_or_structural_constraint": "{FAIL_CLOSED_ON_IDENTITY_AMBIGUITY,DOWNGRADE_TO_NON_PENNY_MPVS_ON_PENNY_AMBIGUITY,OWNER_VISIBLE_BLOCKER_RECEIPT_REQUIRED}",
  "effective_resolution_class": "STATIC_ENUM_OR_RULE",
  "effective_source_state_refs": [
    "OWNER_POLICY::EX_10I0A",
    "SOURCE_PACK::EX_10I0A"
  ],
  "effective_ui_widget_class": "READ_ONLY_POLICY_CARD",
  "effective_unit_or_basis": "shared listed-option identity and tick fail-closed rule",
  "effective_value_source_class": "QTT_FAIL_CLOSED_LISTED_OPTION_IDENTITY_AND_TICK_RULE",
  "evidence_basis_class": "FAMILY_SOURCE_PACK_PLUS_EXACT_OWNER_APPROVED_VALUE",
  "evidence_binding_rule_refs": [],
  "family_evidence_binding_ref": "ST12-FAMILY-EVIDENCE::EX_10I0A",
  "implementation_resolution_kind": "STATIC_OR_DETERMINISTIC_RULE",
  "launch_computability_state": "COMPUTABLE_FROM_STATIC_VALUE_OR_DETERMINISTIC_RULE",
  "master_plan_heading_path": [
    "Part II — Retained institutional design and parameter catalog",
    "D14. Canonical family registry — risk and allocation",
    "EX-10I0A — Listed-option alias, display-symbol, and penny-program pointer resolution closure"
  ],
  "master_plan_section_id": "EX-10I0A",
  "missing_stale_invalid_behavior": "REJECT_INVALID_VALUE_NO_SILENT_DEFAULT",
  "parameter_audit_id": "ST11-PARAM::01943",
  "parameter_id": "ST10-PARAM::1943",
  "parameter_symbol": "opt_id_tick_fail",
  "precision_and_rounding_policy": {
    "allowlist_check": "REQUIRED",
    "internal_numeric_type": "typed_symbolic",
    "normalization": "CANONICAL_EXACT_TOKEN_NO_FREE_TEXT_COERCION",
    "rounding": "NOT_APPLICABLE"
  },
  "runtime_resolution_procedure": [
    "Parse the declared Day-1 seed or deterministic rule into the declared type.",
    "Validate against the reference range and structural constraint.",
    "Apply the declared bounded edit/search law; reject any value outside it."
  ],
  "source_line_end": 53811,
  "source_line_start": 53797,
  "step12_primary_tranche_id": "ST12-TRANCHE-A"
},
{
  "canonical_owner": "QKUComputationControlPlaneV1",
  "certified_step11_custody_ref": "inputs/certified_step11/QTT_Stage1_Step11_Parameter_Policy_Adjudication_v1_0.jsonl#ST11-PARAM::01974",
  "certified_step11_row_embedded_in_prompt": false,
  "codex_online_research_allowed": false,
  "direct_source_claim_justifications": [],
  "effective_bounded_search_space_or_fit_constraint": "fixed symbolic rule only; live paths may not silently weaken it",
  "effective_day1_seed_value_or_resolution_rule": "NO_LATE_CEA_OR_ADVICE_CHANGE_BASED_SOLELY_ON_MATERIAL_INFORMATION_RELEASED_AFTER_DECLARED_CUTOFF",
  "effective_default_authority_class": "PUBLIC_METHOD_OR_PINNED_PROVIDER_DEFAULT_REQUIRES_IMPLEMENTATION_VERSION_BINDING",
  "effective_fallback_behavior_when_value_unavailable": "FAIL_CLOSED_TO_REGISTERED_LOWER_SAFE_PATH_OR_NO_TRADE",
  "effective_owner_dashboard_editability_class": "READ_ONLY_SYMBOLIC",
  "effective_policy_authority": "CERTIFIED_STEP11_PARAMETER_POLICY",
  "effective_reference_range_or_structural_constraint": "{NO_LATE_CEA_OR_ADVICE_CHANGE_BASED_SOLELY_ON_MATERIAL_INFORMATION_RELEASED_AFTER_DECLARED_CUTOFF}",
  "effective_resolution_class": "STATIC_ENUM",
  "effective_source_state_refs": [
    "OWNER_POLICY::EX_10KA",
    "SOURCE_PACK::EX_10KA"
  ],
  "effective_ui_widget_class": "FORMULA_BADGE",
  "effective_unit_or_basis": "post-cutoff information prohibition rule",
  "effective_value_source_class": "PUBLIC_EXCHANGE_CONTRACT_SPEC_SOURCE_WITH_QTT_DAY1_SELECTION",
  "evidence_basis_class": "FAMILY_SOURCE_PACK_PLUS_EXACT_OWNER_APPROVED_VALUE",
  "evidence_binding_rule_refs": [],
  "family_evidence_binding_ref": "ST12-FAMILY-EVIDENCE::EX_10KA",
  "implementation_resolution_kind": "STATIC_OR_DETERMINISTIC_RULE",
  "launch_computability_state": "COMPUTABLE_FROM_STATIC_VALUE_OR_DETERMINISTIC_RULE",
  "master_plan_heading_path": [
    "Part II — Retained institutional design and parameter catalog",
    "D14. Canonical family registry — risk and allocation",
    "EX-10KA — Listed-option exercise-by-exception, contrary-exercise-advice, and advice-cancel cutoff atomic parameter pack"
  ],
  "master_plan_section_id": "EX-10KA",
  "missing_stale_invalid_behavior": "REJECT_INVALID_VALUE_NO_SILENT_DEFAULT",
  "parameter_audit_id": "ST11-PARAM::01974",
  "parameter_id": "ST10-PARAM::1974",
  "parameter_symbol": "opt_postcutoff_info_rule",
  "precision_and_rounding_policy": {
    "allowlist_check": "REQUIRED",
    "internal_numeric_type": "typed_symbolic",
    "normalization": "CANONICAL_EXACT_TOKEN_NO_FREE_TEXT_COERCION",
    "rounding": "NOT_APPLICABLE"
  },
  "runtime_resolution_procedure": [
    "Parse the declared Day-1 seed or deterministic rule into the declared type.",
    "Validate against the reference range and structural constraint.",
    "Apply the declared bounded edit/search law; reject any value outside it."
  ],
  "source_line_end": 54244,
  "source_line_start": 54233,
  "step12_primary_tranche_id": "ST12-TRANCHE-A"
},
{
  "canonical_owner": "QKUComputationControlPlaneV1",
  "certified_step11_custody_ref": "inputs/certified_step11/QTT_Stage1_Step11_Parameter_Policy_Adjudication_v1_0.jsonl#ST11-PARAM::01975",
  "certified_step11_row_embedded_in_prompt": false,
  "codex_online_research_allowed": false,
  "direct_source_claim_justifications": [],
  "effective_bounded_search_space_or_fit_constraint": "fixed symbolic rule only; filing with one surface may not be treated as universally sufficient notice",
  "effective_day1_seed_value_or_resolution_rule": "EXCHANGE_SIDE_FILING_DOES_NOT_SUBSTITUTE_FOR_EFFECTIVE_OCC_OR_CARRYING_BROKER_NOTICE",
  "effective_default_authority_class": "PUBLIC_METHOD_OR_PINNED_PROVIDER_DEFAULT_REQUIRES_IMPLEMENTATION_VERSION_BINDING",
  "effective_fallback_behavior_when_value_unavailable": "FAIL_CLOSED_TO_REGISTERED_LOWER_SAFE_PATH_OR_NO_TRADE",
  "effective_owner_dashboard_editability_class": "READ_ONLY_SYMBOLIC",
  "effective_policy_authority": "CERTIFIED_STEP11_PARAMETER_POLICY",
  "effective_reference_range_or_structural_constraint": "{EXCHANGE_SIDE_FILING_DOES_NOT_SUBSTITUTE_FOR_EFFECTIVE_OCC_OR_CARRYING_BROKER_NOTICE}",
  "effective_resolution_class": "STATIC_ENUM",
  "effective_source_state_refs": [
    "OWNER_POLICY::EX_10KA",
    "SOURCE_PACK::EX_10KA"
  ],
  "effective_ui_widget_class": "FORMULA_BADGE",
  "effective_unit_or_basis": "exchange-versus-OCC notice rule",
  "effective_value_source_class": "PUBLIC_EXCHANGE_CONTRACT_SPEC_SOURCE_WITH_QTT_DAY1_SELECTION",
  "evidence_basis_class": "FAMILY_SOURCE_PACK_PLUS_EXACT_OWNER_APPROVED_VALUE",
  "evidence_binding_rule_refs": [],
  "family_evidence_binding_ref": "ST12-FAMILY-EVIDENCE::EX_10KA",
  "implementation_resolution_kind": "RUNTIME_TYPED_BINDING",
  "launch_computability_state": "EXECUTABLE_FAIL_CLOSED_UNTIL_TYPED_CURRENT_BINDING",
  "master_plan_heading_path": [
    "Part II — Retained institutional design and parameter catalog",
    "D14. Canonical family registry — risk and allocation",
    "EX-10KA — Listed-option exercise-by-exception, contrary-exercise-advice, and advice-cancel cutoff atomic parameter pack"
  ],
  "master_plan_section_id": "EX-10KA",
  "missing_stale_invalid_behavior": "RETURN_BLOCKER_MISSING_STALE_AMBIGUOUS_OR_OUT_OF_RANGE_NO_VALUE",
  "parameter_audit_id": "ST11-PARAM::01975",
  "parameter_id": "ST10-PARAM::1975",
  "parameter_symbol": "opt_exch_occ_non_sub",
  "precision_and_rounding_policy": {
    "allowlist_check": "REQUIRED",
    "internal_numeric_type": "typed_symbolic",
    "normalization": "CANONICAL_EXACT_TOKEN_NO_FREE_TEXT_COERCION",
    "rounding": "NOT_APPLICABLE"
  },
  "runtime_resolution_procedure": [
    "Resolve only through BindingProfileV1 using a current SourceSnapshotV1 or declared internal state snapshot.",
    "Validate type, unit, effective time, scope and source epoch before computation.",
    "If missing, stale, ambiguous or out of range, return the exact blocker and no value.",
    "Never let a Codex implementation browse or invent the value; source parser and blocker behavior are specified in the Step 12 source registry."
  ],
  "source_line_end": 54256,
  "source_line_start": 54245,
  "step12_primary_tranche_id": "ST12-TRANCHE-A"
},
{
  "canonical_owner": "QKUComputationControlPlaneV1",
  "certified_step11_custody_ref": "inputs/certified_step11/QTT_Stage1_Step11_Parameter_Policy_Adjudication_v1_0.jsonl#ST11-PARAM::02012",
  "certified_step11_row_embedded_in_prompt": false,
  "codex_online_research_allowed": false,
  "direct_source_claim_justifications": [],
  "effective_bounded_search_space_or_fit_constraint": "unresolved listed-option special-execution surfaces may not degrade to silent heuristics in live execution",
  "effective_day1_seed_value_or_resolution_rule": "BLOCK_AUTONOMOUS_QCC_RELEASE_BLOCK_AUTONOMOUS_COMPLEX_AUCTION_RELEASE_BLOCK_AUTONOMOUS_SPECIAL_CROSS_RELEASE_AND_DOWNGRADE_TO_STANDARD_LISTED_OPTION_BOOK_HANDLING_OR_INDICATIVE_ONLY_OR_RESEARCH_ONLY_HANDLING_UNTIL_AUTHORITATIVE_SPECIAL_EXECUTION_RECEIPTS_RECOVER",
  "effective_default_authority_class": "EXPLICIT_QTT_OR_OWNER_POLICY_SEED_OR_RESOLUTION_RULE",
  "effective_fallback_behavior_when_value_unavailable": "FAIL_CLOSED_TO_REGISTERED_LOWER_SAFE_PATH_OR_NO_TRADE",
  "effective_owner_dashboard_editability_class": "READ_ONLY_RULE_POINTER_OWNER_VISIBLE",
  "effective_policy_authority": "CERTIFIED_STEP11_PARAMETER_POLICY",
  "effective_reference_range_or_structural_constraint": "{STANDARD_BOOK_ONLY_FALLBACK,INDICATIVE_ONLY_FALLBACK,RESEARCH_ONLY_FALLBACK,FAIL_CLOSED}",
  "effective_resolution_class": "STATIC_FAIL_CLOSED_RULE",
  "effective_source_state_refs": [
    "OWNER_POLICY::EX_10K1A",
    "SOURCE_PACK::EX_10K1A"
  ],
  "effective_ui_widget_class": "RULE_CARD_PLUS_WARNING_BADGE",
  "effective_unit_or_basis": "fail-closed special-execution rule",
  "effective_value_source_class": "QTT_CANONICAL_FAIL_CLOSED_RUNTIME_RULE",
  "evidence_basis_class": "FAMILY_SOURCE_PACK_PLUS_EXACT_OWNER_APPROVED_VALUE",
  "evidence_binding_rule_refs": [],
  "family_evidence_binding_ref": "ST12-FAMILY-EVIDENCE::EX_10K1A",
  "implementation_resolution_kind": "STATIC_OR_DETERMINISTIC_RULE",
  "launch_computability_state": "COMPUTABLE_FROM_STATIC_VALUE_OR_DETERMINISTIC_RULE",
  "master_plan_heading_path": [
    "Part II — Retained institutional design and parameter catalog",
    "D14. Canonical family registry — risk and allocation",
    "EX-10K1A — Listed-option special-execution and auction-policy resolution closure"
  ],
  "master_plan_section_id": "EX-10K1A",
  "missing_stale_invalid_behavior": "REJECT_INVALID_VALUE_NO_SILENT_DEFAULT",
  "parameter_audit_id": "ST11-PARAM::02012",
  "parameter_id": "ST10-PARAM::2012",
  "parameter_symbol": "opt_special_exec_fail",
  "precision_and_rounding_policy": {
    "allowlist_check": "REQUIRED",
    "internal_numeric_type": "typed_symbolic",
    "normalization": "CANONICAL_EXACT_TOKEN_NO_FREE_TEXT_COERCION",
    "rounding": "NOT_APPLICABLE"
  },
  "runtime_resolution_procedure": [
    "Parse the declared Day-1 seed or deterministic rule into the declared type.",
    "Validate against the reference range and structural constraint.",
    "Apply the declared bounded edit/search law; reject any value outside it."
  ],
  "source_line_end": 54768,
  "source_line_start": 54754,
  "step12_primary_tranche_id": "ST12-TRANCHE-A"
},
{
  "canonical_owner": "QKUComputationControlPlaneV1",
  "certified_step11_custody_ref": "inputs/certified_step11/QTT_Stage1_Step11_Parameter_Policy_Adjudication_v1_0.jsonl#ST11-PARAM::02042",
  "certified_step11_row_embedded_in_prompt": false,
  "codex_online_research_allowed": false,
  "direct_source_claim_justifications": [],
  "effective_bounded_search_space_or_fit_constraint": "unresolved futures contract semantics may not be guessed from stale local cache, broker shorthand, or a similar contract family",
  "effective_day1_seed_value_or_resolution_rule": "BLOCK_AUTONOMOUS_FUTURES_ORDER_RELEASE_BLOCK_AUTONOMOUS_ROLL_AND_DELIVERY_LOGIC_SUPPRESS_TICK_VALUE_DERIVATION_AND_DOWNGRADE_TO_INDICATIVE_ONLY_OR_NO_TRADE_UNTIL_AUTHORITATIVE_EXCHANGE_CONTRACT_SPEC_AND_CRITICAL_DATE_RECOVERY",
  "effective_default_authority_class": "EXPLICIT_QTT_OR_OWNER_POLICY_SEED_OR_RESOLUTION_RULE",
  "effective_fallback_behavior_when_value_unavailable": "FAIL_CLOSED_TO_REGISTERED_LOWER_SAFE_PATH_OR_NO_TRADE",
  "effective_owner_dashboard_editability_class": "READ_ONLY_BY_DEFAULT",
  "effective_policy_authority": "CERTIFIED_STEP11_PARAMETER_POLICY",
  "effective_reference_range_or_structural_constraint": "{BLOCK_AUTONOMOUS_ORDER_RELEASE_WHEN_CONTRACT_UNIT_UNKNOWN,BLOCK_AUTONOMOUS_ORDER_RELEASE_WHEN_MINIMUM_PRICE_FLUCTUATION_UNKNOWN,BLOCK_AUTONOMOUS_ROLL_AND_DELIVERY_LOGIC_WHEN_CRITICAL_DATES_UNKNOWN,INDICATIVE_ONLY_OR_NO_TRADE_UNTIL_RECOVERY}",
  "effective_resolution_class": "STATIC_ENUM_OR_RULE",
  "effective_source_state_refs": [
    "OWNER_POLICY::EX_10M0A",
    "SOURCE_PACK::EX_10M0A"
  ],
  "effective_ui_widget_class": "READ_ONLY_POLICY_CARD",
  "effective_unit_or_basis": "shared futures contract-spec fail-closed rule",
  "effective_value_source_class": "QTT_FAIL_CLOSED_FUTURES_CONTRACT_SPEC_RULE",
  "evidence_basis_class": "FAMILY_SOURCE_PACK_PLUS_EXACT_OWNER_APPROVED_VALUE",
  "evidence_binding_rule_refs": [],
  "family_evidence_binding_ref": "ST12-FAMILY-EVIDENCE::EX_10M0A",
  "implementation_resolution_kind": "EXPLICIT_FAIL_CLOSED_POLICY",
  "launch_computability_state": "COMPUTABLE_TYPED_FAIL_CLOSED_OR_NO_TRADE_STATE",
  "master_plan_heading_path": [
    "Part II — Retained institutional design and parameter catalog",
    "D14. Canonical family registry — risk and allocation",
    "EX-10M0A — Futures contract-unit, minimum-price-fluctuation, and critical-date pointer resolution closure"
  ],
  "master_plan_section_id": "EX-10M0A",
  "missing_stale_invalid_behavior": "PRESERVE_EXPLICIT_FAIL_CLOSED_STATE",
  "parameter_audit_id": "ST11-PARAM::02042",
  "parameter_id": "ST10-PARAM::2042",
  "parameter_symbol": "fut_spec_fail",
  "precision_and_rounding_policy": {
    "allowlist_check": "REQUIRED",
    "internal_numeric_type": "typed_symbolic",
    "normalization": "CANONICAL_EXACT_TOKEN_NO_FREE_TEXT_COERCION",
    "rounding": "NOT_APPLICABLE"
  },
  "runtime_resolution_procedure": [
    "Materialize the declared fail-closed state exactly.",
    "Return a typed blocker/no-trade status and do not substitute a numeric fallback.",
    "Validate the resolved typed value or token against the effective resolution class, declared structural constraint, and canonical allowlist; on failure apply the declared fail-closed fallback and emit the exact reason code."
  ],
  "source_line_end": 55181,
  "source_line_start": 55167,
  "step12_primary_tranche_id": "ST12-TRANCHE-A"
},
{
  "canonical_owner": "QKUComputationControlPlaneV1",
  "certified_step11_custody_ref": "inputs/certified_step11/QTT_Stage1_Step11_Parameter_Policy_Adjudication_v1_0.jsonl#ST11-PARAM::02062",
  "certified_step11_row_embedded_in_prompt": false,
  "codex_online_research_allowed": false,
  "direct_source_claim_justifications": [],
  "effective_bounded_search_space_or_fit_constraint": "unresolved special-execution pointers may not be guessed from broker interfaces, prior tickets, or nearby product analogies",
  "effective_day1_seed_value_or_resolution_rule": "BLOCK_AUTONOMOUS_SPECIAL_EXECUTION_PATH_SELECTION_BLOCK_AUTONOMOUS_BLOCK_NEGOTIATION_ASSUMPTIONS_BLOCK_AUTONOMOUS_EFRP_ENABLEMENT_AND_DOWNGRADE_TO_OWNER_VISIBLE_SCREEN_ONLY_OR_NO_TRADE_HANDLING_UNTIL_AUTHORITATIVE_EXCHANGE_AND_CLEARING_RECEIPTS_RECOVER",
  "effective_default_authority_class": "EXPLICIT_QTT_OR_OWNER_POLICY_SEED_OR_RESOLUTION_RULE",
  "effective_fallback_behavior_when_value_unavailable": "FAIL_CLOSED_TO_REGISTERED_LOWER_SAFE_PATH_OR_NO_TRADE",
  "effective_owner_dashboard_editability_class": "READ_ONLY_BY_DEFAULT",
  "effective_policy_authority": "CERTIFIED_STEP11_PARAMETER_POLICY",
  "effective_reference_range_or_structural_constraint": "{BLOCK_AUTONOMOUS_BLOCK_PATH_WHEN_THRESHOLD_UNKNOWN, BLOCK_AUTONOMOUS_BLOCK_REPORTING_ASSUMPTIONS_WHEN_WINDOW_UNKNOWN, BLOCK_AUTONOMOUS_EFRP_ENABLEMENT_WHEN_PERMISSION_UNKNOWN, OWNER_VISIBLE_SCREEN_ONLY_OR_NO_TRADE_HANDLING_UNTIL_RECOVERY}",
  "effective_resolution_class": "STATIC_ENUM_OR_RULE",
  "effective_source_state_refs": [
    "OWNER_POLICY::EX_10M1A",
    "SOURCE_PACK::EX_10M1A"
  ],
  "effective_ui_widget_class": "READ_ONLY_POLICY_CARD",
  "effective_unit_or_basis": "shared futures-special-execution fail-closed rule",
  "effective_value_source_class": "QTT_FAIL_CLOSED_FUTURES_SPECIAL_EXECUTION_RULE",
  "evidence_basis_class": "FAMILY_SOURCE_PACK_PLUS_EXACT_OWNER_APPROVED_VALUE",
  "evidence_binding_rule_refs": [],
  "family_evidence_binding_ref": "ST12-FAMILY-EVIDENCE::EX_10M1A",
  "implementation_resolution_kind": "EXPLICIT_FAIL_CLOSED_POLICY",
  "launch_computability_state": "COMPUTABLE_TYPED_FAIL_CLOSED_OR_NO_TRADE_STATE",
  "master_plan_heading_path": [
    "Part II — Retained institutional design and parameter catalog",
    "D14. Canonical family registry — risk and allocation",
    "EX-10M1A — Futures block-threshold, block-reporting, and EFRP pointer resolution closure"
  ],
  "master_plan_section_id": "EX-10M1A",
  "missing_stale_invalid_behavior": "PRESERVE_EXPLICIT_FAIL_CLOSED_STATE",
  "parameter_audit_id": "ST11-PARAM::02062",
  "parameter_id": "ST10-PARAM::2062",
  "parameter_symbol": "fut_spx_fail",
  "precision_and_rounding_policy": {
    "allowlist_check": "REQUIRED",
    "internal_numeric_type": "typed_symbolic",
    "normalization": "CANONICAL_EXACT_TOKEN_NO_FREE_TEXT_COERCION",
    "rounding": "NOT_APPLICABLE"
  },
  "runtime_resolution_procedure": [
    "Materialize the declared fail-closed state exactly.",
    "Return a typed blocker/no-trade status and do not substitute a numeric fallback.",
    "Validate the resolved typed value or token against the effective resolution class, declared structural constraint, and canonical allowlist; on failure apply the declared fail-closed fallback and emit the exact reason code."
  ],
  "source_line_end": 55456,
  "source_line_start": 55442,
  "step12_primary_tranche_id": "ST12-TRANCHE-A"
},
{
  "canonical_owner": "QKUComputationControlPlaneV1",
  "certified_step11_custody_ref": "inputs/certified_step11/QTT_Stage1_Step11_Parameter_Policy_Adjudication_v1_0.jsonl#ST11-PARAM::02068",
  "certified_step11_row_embedded_in_prompt": false,
  "codex_online_research_allowed": false,
  "direct_source_claim_justifications": [],
  "effective_bounded_search_space_or_fit_constraint": "unresolved futures special-execution surfaces may not degrade to silent heuristics in live execution",
  "effective_day1_seed_value_or_resolution_rule": "BLOCK_AUTONOMOUS_BLOCK_TRADE_RELEASE_BLOCK_AUTONOMOUS_DEFERRED_PRICE_EXECUTION_BLOCK_AUTONOMOUS_EFRP_RELEASE_AND_DOWNGRADE_TO_SCREEN_ONLY_OR_INDICATIVE_ONLY_OR_RESEARCH_ONLY_HANDLING_UNTIL_AUTHORITATIVE_SPECIAL_EXECUTION_RECEIPTS_RECOVER",
  "effective_default_authority_class": "EXPLICIT_QTT_OR_OWNER_POLICY_SEED_OR_RESOLUTION_RULE",
  "effective_fallback_behavior_when_value_unavailable": "FAIL_CLOSED_TO_REGISTERED_LOWER_SAFE_PATH_OR_NO_TRADE",
  "effective_owner_dashboard_editability_class": "READ_ONLY_RULE_POINTER_OWNER_VISIBLE",
  "effective_policy_authority": "CERTIFIED_STEP11_PARAMETER_POLICY",
  "effective_reference_range_or_structural_constraint": "{SCREEN_ONLY_FALLBACK,INDICATIVE_ONLY_FALLBACK,RESEARCH_ONLY_FALLBACK,FAIL_CLOSED}",
  "effective_resolution_class": "STATIC_FAIL_CLOSED_RULE",
  "effective_source_state_refs": [
    "OWNER_POLICY::EX_10M1B",
    "SOURCE_PACK::EX_10M1B"
  ],
  "effective_ui_widget_class": "RULE_CARD_PLUS_WARNING_BADGE",
  "effective_unit_or_basis": "fail-closed special-execution rule",
  "effective_value_source_class": "QTT_CANONICAL_FAIL_CLOSED_RUNTIME_RULE",
  "evidence_basis_class": "FAMILY_SOURCE_PACK_PLUS_EXACT_OWNER_APPROVED_VALUE",
  "evidence_binding_rule_refs": [],
  "family_evidence_binding_ref": "ST12-FAMILY-EVIDENCE::EX_10M1B",
  "implementation_resolution_kind": "STATIC_OR_DETERMINISTIC_RULE",
  "launch_computability_state": "COMPUTABLE_FROM_STATIC_VALUE_OR_DETERMINISTIC_RULE",
  "master_plan_heading_path": [
    "Part II — Retained institutional design and parameter catalog",
    "D14. Canonical family registry — risk and allocation",
    "EX-10M1B — Futures special-execution menu, deferred-price, and EFRP reporting resolution closure"
  ],
  "master_plan_section_id": "EX-10M1B",
  "missing_stale_invalid_behavior": "REJECT_INVALID_VALUE_NO_SILENT_DEFAULT",
  "parameter_audit_id": "ST11-PARAM::02068",
  "parameter_id": "ST10-PARAM::2068",
  "parameter_symbol": "fut_special_exec_fail",
  "precision_and_rounding_policy": {
    "allowlist_check": "REQUIRED",
    "internal_numeric_type": "typed_symbolic",
    "normalization": "CANONICAL_EXACT_TOKEN_NO_FREE_TEXT_COERCION",
    "rounding": "NOT_APPLICABLE"
  },
  "runtime_resolution_procedure": [
    "Parse the declared Day-1 seed or deterministic rule into the declared type.",
    "Validate against the reference range and structural constraint.",
    "Apply the declared bounded edit/search law; reject any value outside it."
  ],
  "source_line_end": 55538,
  "source_line_start": 55524,
  "step12_primary_tranche_id": "ST12-TRANCHE-A"
},
{
  "canonical_owner": "QKUComputationControlPlaneV1",
  "certified_step11_custody_ref": "inputs/certified_step11/QTT_Stage1_Step11_Parameter_Policy_Adjudication_v1_0.jsonl#ST11-PARAM::02072",
  "certified_step11_row_embedded_in_prompt": false,
  "codex_online_research_allowed": false,
  "direct_source_claim_justifications": [],
  "effective_bounded_search_space_or_fit_constraint": "formula only; live paths may not approximate repo interest from P&L drift or informal desk shortcuts",
  "effective_day1_seed_value_or_resolution_rule": "repo_interest = purchase_price * repo_rate * day_count / (100 * annual_basis)",
  "effective_default_authority_class": "PUBLIC_METHOD_OR_PINNED_PROVIDER_DEFAULT_REQUIRES_IMPLEMENTATION_VERSION_BINDING",
  "effective_fallback_behavior_when_value_unavailable": "FAIL_CLOSED_TO_REGISTERED_LOWER_SAFE_PATH_OR_NO_TRADE",
  "effective_owner_dashboard_editability_class": "READ_ONLY_FORMULA_CARD",
  "effective_policy_authority": "CERTIFIED_STEP11_PARAMETER_POLICY",
  "effective_reference_range_or_structural_constraint": "exact public formula identity on the declared rate-percent basis",
  "effective_resolution_class": "STATIC_FORMULA_WITH_RUNTIME_INPUTS",
  "effective_source_state_refs": [
    "OWNER_POLICY::EX_10N",
    "SOURCE_PACK::EX_10N"
  ],
  "effective_ui_widget_class": "READ_ONLY_FORMULA_CARD",
  "effective_unit_or_basis": "currency interest amount on declared rate-percent basis",
  "effective_value_source_class": "PUBLIC_MARKET_FORMULA_STANDARD",
  "evidence_basis_class": "FAMILY_SOURCE_PACK_PLUS_EXACT_OWNER_APPROVED_VALUE",
  "evidence_binding_rule_refs": [],
  "family_evidence_binding_ref": "ST12-FAMILY-EVIDENCE::EX_10N",
  "implementation_resolution_kind": "RUNTIME_TYPED_BINDING",
  "launch_computability_state": "EXECUTABLE_FAIL_CLOSED_UNTIL_TYPED_CURRENT_BINDING",
  "master_plan_heading_path": [
    "Part II — Retained institutional design and parameter catalog",
    "D14. Canonical family registry — risk and allocation",
    "EX-10N — Securities-financing / repo / reverse-repo collateral, haircut, term, and clearing-control atomic parameter pack"
  ],
  "master_plan_section_id": "EX-10N",
  "missing_stale_invalid_behavior": "RETURN_BLOCKER_MISSING_STALE_AMBIGUOUS_OR_OUT_OF_RANGE_NO_VALUE",
  "parameter_audit_id": "ST11-PARAM::02072",
  "parameter_id": "ST10-PARAM::2072",
  "parameter_symbol": "repo_int_formula",
  "precision_and_rounding_policy": {
    "decimal_context_precision": 34,
    "internal_numeric_type": "Decimal",
    "nonfinite_policy": "REJECT",
    "quantization": "SOURCE_OR_UNIT_DECLARED; NO_IMPLICIT_BINARY_FLOAT_CONVERSION",
    "rounding": "ROUND_HALF_EVEN"
  },
  "runtime_resolution_procedure": [
    "Resolve only through BindingProfileV1 using a current SourceSnapshotV1 or declared internal state snapshot.",
    "Validate type, unit, effective time, scope and source epoch before computation.",
    "If missing, stale, ambiguous or out of range, return the exact blocker and no value.",
    "Never let a Codex implementation browse or invent the value; source parser and blocker behavior are specified in the Step 12 source registry."
  ],
  "source_line_end": 55590,
  "source_line_start": 55579,
  "step12_primary_tranche_id": "ST12-TRANCHE-A"
},
{
  "canonical_owner": "QKUComputationControlPlaneV1",
  "certified_step11_custody_ref": "inputs/certified_step11/QTT_Stage1_Step11_Parameter_Policy_Adjudication_v1_0.jsonl#ST11-PARAM::02076",
  "certified_step11_row_embedded_in_prompt": false,
  "codex_online_research_allowed": false,
  "direct_source_claim_justifications": [],
  "effective_bounded_search_space_or_fit_constraint": "formula only; haircut may not be approximated from leverage folklore or generic risk labels",
  "effective_day1_seed_value_or_resolution_rule": "haircut = (market_value_of_collateral - purchase_price) / market_value_of_collateral",
  "effective_default_authority_class": "PUBLIC_METHOD_OR_PINNED_PROVIDER_DEFAULT_REQUIRES_IMPLEMENTATION_VERSION_BINDING",
  "effective_fallback_behavior_when_value_unavailable": "FAIL_CLOSED_TO_REGISTERED_LOWER_SAFE_PATH_OR_NO_TRADE",
  "effective_owner_dashboard_editability_class": "READ_ONLY_FORMULA_CARD",
  "effective_policy_authority": "CERTIFIED_STEP11_PARAMETER_POLICY",
  "effective_reference_range_or_structural_constraint": "exact public formula identity on non-negative market value and purchase price inputs",
  "effective_resolution_class": "STATIC_FORMULA_WITH_RUNTIME_INPUTS",
  "effective_source_state_refs": [
    "OWNER_POLICY::EX_10N",
    "SOURCE_PACK::EX_10N"
  ],
  "effective_ui_widget_class": "READ_ONLY_FORMULA_CARD",
  "effective_unit_or_basis": "haircut decimal fraction",
  "effective_value_source_class": "PUBLIC_MARKET_FORMULA_STANDARD",
  "evidence_basis_class": "FAMILY_SOURCE_PACK_PLUS_EXACT_OWNER_APPROVED_VALUE",
  "evidence_binding_rule_refs": [],
  "family_evidence_binding_ref": "ST12-FAMILY-EVIDENCE::EX_10N",
  "implementation_resolution_kind": "RUNTIME_TYPED_BINDING",
  "launch_computability_state": "EXECUTABLE_FAIL_CLOSED_UNTIL_TYPED_CURRENT_BINDING",
  "master_plan_heading_path": [
    "Part II — Retained institutional design and parameter catalog",
    "D14. Canonical family registry — risk and allocation",
    "EX-10N — Securities-financing / repo / reverse-repo collateral, haircut, term, and clearing-control atomic parameter pack"
  ],
  "master_plan_section_id": "EX-10N",
  "missing_stale_invalid_behavior": "RETURN_BLOCKER_MISSING_STALE_AMBIGUOUS_OR_OUT_OF_RANGE_NO_VALUE",
  "parameter_audit_id": "ST11-PARAM::02076",
  "parameter_id": "ST10-PARAM::2076",
  "parameter_symbol": "repo_hcut_formula",
  "precision_and_rounding_policy": {
    "decimal_context_precision": 34,
    "internal_numeric_type": "Decimal",
    "nonfinite_policy": "REJECT",
    "quantization": "SOURCE_OR_UNIT_DECLARED; NO_IMPLICIT_BINARY_FLOAT_CONVERSION",
    "rounding": "ROUND_HALF_EVEN"
  },
  "runtime_resolution_procedure": [
    "Resolve only through BindingProfileV1 using a current SourceSnapshotV1 or declared internal state snapshot.",
    "Validate type, unit, effective time, scope and source epoch before computation.",
    "If missing, stale, ambiguous or out of range, return the exact blocker and no value.",
    "Never let a Codex implementation browse or invent the value; source parser and blocker behavior are specified in the Step 12 source registry."
  ],
  "source_line_end": 55638,
  "source_line_start": 55627,
  "step12_primary_tranche_id": "ST12-TRANCHE-A"
},
{
  "canonical_owner": "QKUComputationControlPlaneV1",
  "certified_step11_custody_ref": "inputs/certified_step11/QTT_Stage1_Step11_Parameter_Policy_Adjudication_v1_0.jsonl#ST11-PARAM::02077",
  "certified_step11_row_embedded_in_prompt": false,
  "codex_online_research_allowed": false,
  "direct_source_claim_justifications": [],
  "effective_bounded_search_space_or_fit_constraint": "formula only; live paths may not treat haircut and margin ratio as interchangeable badges",
  "effective_day1_seed_value_or_resolution_rule": "margin_ratio = market_value_of_collateral / purchase_price",
  "effective_default_authority_class": "PUBLIC_METHOD_OR_PINNED_PROVIDER_DEFAULT_REQUIRES_IMPLEMENTATION_VERSION_BINDING",
  "effective_fallback_behavior_when_value_unavailable": "FAIL_CLOSED_TO_REGISTERED_LOWER_SAFE_PATH_OR_NO_TRADE",
  "effective_owner_dashboard_editability_class": "READ_ONLY_FORMULA_CARD",
  "effective_policy_authority": "CERTIFIED_STEP11_PARAMETER_POLICY",
  "effective_reference_range_or_structural_constraint": "exact public formula identity on positive purchase price; owner-visible note that a `102%` margin ratio is not arithmetically identical to a `2%` haircut",
  "effective_resolution_class": "STATIC_FORMULA_WITH_RUNTIME_INPUTS",
  "effective_source_state_refs": [
    "OWNER_POLICY::EX_10N",
    "SOURCE_PACK::EX_10N"
  ],
  "effective_ui_widget_class": "READ_ONLY_FORMULA_CARD",
  "effective_unit_or_basis": "margin-ratio multiplier or percent basis as declared",
  "effective_value_source_class": "PUBLIC_MARKET_FORMULA_STANDARD",
  "evidence_basis_class": "FAMILY_SOURCE_PACK_PLUS_EXACT_OWNER_APPROVED_VALUE",
  "evidence_binding_rule_refs": [],
  "family_evidence_binding_ref": "ST12-FAMILY-EVIDENCE::EX_10N",
  "implementation_resolution_kind": "RUNTIME_TYPED_BINDING",
  "launch_computability_state": "EXECUTABLE_FAIL_CLOSED_UNTIL_TYPED_CURRENT_BINDING",
  "master_plan_heading_path": [
    "Part II — Retained institutional design and parameter catalog",
    "D14. Canonical family registry — risk and allocation",
    "EX-10N — Securities-financing / repo / reverse-repo collateral, haircut, term, and clearing-control atomic parameter pack"
  ],
  "master_plan_section_id": "EX-10N",
  "missing_stale_invalid_behavior": "RETURN_BLOCKER_MISSING_STALE_AMBIGUOUS_OR_OUT_OF_RANGE_NO_VALUE",
  "parameter_audit_id": "ST11-PARAM::02077",
  "parameter_id": "ST10-PARAM::2077",
  "parameter_symbol": "repo_mratio_formula",
  "precision_and_rounding_policy": {
    "decimal_context_precision": 34,
    "internal_numeric_type": "Decimal",
    "nonfinite_policy": "REJECT",
    "quantization": "SOURCE_OR_UNIT_DECLARED; NO_IMPLICIT_BINARY_FLOAT_CONVERSION",
    "rounding": "ROUND_HALF_EVEN"
  },
  "runtime_resolution_procedure": [
    "Resolve only through BindingProfileV1 using a current SourceSnapshotV1 or declared internal state snapshot.",
    "Validate type, unit, effective time, scope and source epoch before computation.",
    "If missing, stale, ambiguous or out of range, return the exact blocker and no value.",
    "Never let a Codex implementation browse or invent the value; source parser and blocker behavior are specified in the Step 12 source registry."
  ],
  "source_line_end": 55650,
  "source_line_start": 55639,
  "step12_primary_tranche_id": "ST12-TRANCHE-A"
},
{
  "canonical_owner": "QKUComputationControlPlaneV1",
  "certified_step11_custody_ref": "inputs/certified_step11/QTT_Stage1_Step11_Parameter_Policy_Adjudication_v1_0.jsonl#ST11-PARAM::02085",
  "certified_step11_row_embedded_in_prompt": false,
  "codex_online_research_allowed": false,
  "direct_source_claim_justifications": [],
  "effective_bounded_search_space_or_fit_constraint": "unresolved financing pointers may not be guessed from prior trade history, counterparty folklore, or a similar collateral class",
  "effective_day1_seed_value_or_resolution_rule": "BLOCK_AUTONOMOUS_FINANCING_ASSUMPTIONS_BLOCK_AUTONOMOUS_HAIRCUT_SELECTION_BLOCK_AUTONOMOUS_OPEN_REPO_UNWIND_ASSUMPTIONS_AND_DOWNGRADE_TO_OWNER_VISIBLE_NO_TRADE_OR_NONAUTOMATIC_FINANCING_HANDLING_UNTIL_AUTHORITATIVE_COUNTERPARTY_CCP_AND_CONFIRMATION_RECEIPTS_RECOVER",
  "effective_default_authority_class": "EXPLICIT_QTT_OR_OWNER_POLICY_SEED_OR_RESOLUTION_RULE",
  "effective_fallback_behavior_when_value_unavailable": "FAIL_CLOSED_TO_REGISTERED_LOWER_SAFE_PATH_OR_NO_TRADE",
  "effective_owner_dashboard_editability_class": "READ_ONLY_BY_DEFAULT",
  "effective_policy_authority": "CERTIFIED_STEP11_PARAMETER_POLICY",
  "effective_reference_range_or_structural_constraint": "{BLOCK_AUTONOMOUS_HAIRCUT_SELECTION_WHEN_SCHEDULE_UNKNOWN, BLOCK_AUTONOMOUS_OPEN_REPO_UNWIND_ASSUMPTIONS_WHEN_NOTICE_RULE_UNKNOWN, OWNER_VISIBLE_NO_TRADE_OR_NONAUTOMATIC_FINANCING_HANDLING_UNTIL_RECOVERY}",
  "effective_resolution_class": "STATIC_ENUM_OR_RULE",
  "effective_source_state_refs": [
    "OWNER_POLICY::EX_10N0A",
    "SOURCE_PACK::EX_10N0A"
  ],
  "effective_ui_widget_class": "READ_ONLY_POLICY_CARD",
  "effective_unit_or_basis": "shared repo-pointer fail-closed rule",
  "effective_value_source_class": "QTT_FAIL_CLOSED_REPO_POINTER_RULE",
  "evidence_basis_class": "FAMILY_SOURCE_PACK_PLUS_EXACT_OWNER_APPROVED_VALUE",
  "evidence_binding_rule_refs": [],
  "family_evidence_binding_ref": "ST12-FAMILY-EVIDENCE::EX_10N0A",
  "implementation_resolution_kind": "EXPLICIT_FAIL_CLOSED_POLICY",
  "launch_computability_state": "COMPUTABLE_TYPED_FAIL_CLOSED_OR_NO_TRADE_STATE",
  "master_plan_heading_path": [
    "Part II — Retained institutional design and parameter catalog",
    "D14. Canonical family registry — risk and allocation",
    "EX-10N0A — Repo haircut and open-notice pointer resolution closure"
  ],
  "master_plan_section_id": "EX-10N0A",
  "missing_stale_invalid_behavior": "PRESERVE_EXPLICIT_FAIL_CLOSED_STATE",
  "parameter_audit_id": "ST11-PARAM::02085",
  "parameter_id": "ST10-PARAM::2085",
  "parameter_symbol": "repo_ptr_fail",
  "precision_and_rounding_policy": {
    "allowlist_check": "REQUIRED",
    "internal_numeric_type": "typed_symbolic",
    "normalization": "CANONICAL_EXACT_TOKEN_NO_FREE_TEXT_COERCION",
    "rounding": "NOT_APPLICABLE"
  },
  "runtime_resolution_procedure": [
    "Materialize the declared fail-closed state exactly.",
    "Return a typed blocker/no-trade status and do not substitute a numeric fallback.",
    "Validate the resolved typed value or token against the effective resolution class, declared structural constraint, and canonical allowlist; on failure apply the declared fail-closed fallback and emit the exact reason code."
  ],
  "source_line_end": 55768,
  "source_line_start": 55754,
  "step12_primary_tranche_id": "ST12-TRANCHE-A"
},
{
  "canonical_owner": "QKUComputationControlPlaneV1",
  "certified_step11_custody_ref": "inputs/certified_step11/QTT_Stage1_Step11_Parameter_Policy_Adjudication_v1_0.jsonl#ST11-PARAM::02093",
  "certified_step11_row_embedded_in_prompt": false,
  "codex_online_research_allowed": false,
  "direct_source_claim_justifications": [],
  "effective_bounded_search_space_or_fit_constraint": "rule only; no live path may treat large distributions as ordinary ex-date events without explicit override",
  "effective_day1_seed_value_or_resolution_rule": "IF_DISTRIBUTION_OR_SPLIT_GTE_25_PERCENT_OF_SECURITY_VALUE_THEN_EX_DATE_IS_FIRST_BUSINESS_DAY_FOLLOWING_PAYABLE_DATE",
  "effective_default_authority_class": "PUBLIC_METHOD_OR_PINNED_PROVIDER_DEFAULT_REQUIRES_IMPLEMENTATION_VERSION_BINDING",
  "effective_fallback_behavior_when_value_unavailable": "FAIL_CLOSED_TO_REGISTERED_LOWER_SAFE_PATH_OR_NO_TRADE",
  "effective_owner_dashboard_editability_class": "READ_ONLY_FORMULA_CARD",
  "effective_policy_authority": "CERTIFIED_STEP11_PARAMETER_POLICY",
  "effective_reference_range_or_structural_constraint": "rule only; applies when the distribution or split is 25 percent or greater of the security value on the declared market-structure path",
  "effective_resolution_class": "STATIC_RULE_ID",
  "effective_source_state_refs": [
    "OWNER_POLICY::EX_10O",
    "SOURCE_PACK::EX_10O"
  ],
  "effective_ui_widget_class": "READ_ONLY_RULE_CARD",
  "effective_unit_or_basis": "threshold rule at 25 percent-of-value boundary",
  "effective_value_source_class": "PUBLIC_MARKET_STRUCTURE_STANDARD",
  "evidence_basis_class": "FAMILY_SOURCE_PACK_PLUS_EXACT_OWNER_APPROVED_VALUE",
  "evidence_binding_rule_refs": [],
  "family_evidence_binding_ref": "ST12-FAMILY-EVIDENCE::EX_10O",
  "implementation_resolution_kind": "STATIC_OR_DETERMINISTIC_RULE",
  "launch_computability_state": "COMPUTABLE_FROM_STATIC_VALUE_OR_DETERMINISTIC_RULE",
  "master_plan_heading_path": [
    "Part II — Retained institutional design and parameter catalog",
    "D14. Canonical family registry — risk and allocation",
    "EX-10O — Equities / ETF corporate-action, ex-date, identifier-change, and position-adjustment atomic parameter pack"
  ],
  "master_plan_section_id": "EX-10O",
  "missing_stale_invalid_behavior": "REJECT_INVALID_VALUE_NO_SILENT_DEFAULT",
  "parameter_audit_id": "ST11-PARAM::02093",
  "parameter_id": "ST10-PARAM::2093",
  "parameter_symbol": "eq_large_exdate",
  "precision_and_rounding_policy": {
    "allowlist_check": "REQUIRED",
    "internal_numeric_type": "typed_symbolic",
    "normalization": "CANONICAL_EXACT_TOKEN_NO_FREE_TEXT_COERCION",
    "rounding": "NOT_APPLICABLE"
  },
  "runtime_resolution_procedure": [
    "Parse the declared Day-1 seed or deterministic rule into the declared type.",
    "Validate against the reference range and structural constraint.",
    "Apply the declared bounded edit/search law; reject any value outside it."
  ],
  "source_line_end": 55878,
  "source_line_start": 55867,
  "step12_primary_tranche_id": "ST12-TRANCHE-A"
},
{
  "canonical_owner": "QKUComputationControlPlaneV1",
  "certified_step11_custody_ref": "inputs/certified_step11/QTT_Stage1_Step11_Parameter_Policy_Adjudication_v1_0.jsonl#ST11-PARAM::02094",
  "certified_step11_row_embedded_in_prompt": false,
  "codex_online_research_allowed": false,
  "direct_source_claim_justifications": [],
  "effective_bounded_search_space_or_fit_constraint": "formula only; live paths may not infer factor from rounded displayed prices without the action card",
  "effective_day1_seed_value_or_resolution_rule": "split_factor = post_event_share_count / pre_event_share_count",
  "effective_default_authority_class": "PUBLIC_METHOD_OR_PINNED_PROVIDER_DEFAULT_REQUIRES_IMPLEMENTATION_VERSION_BINDING",
  "effective_fallback_behavior_when_value_unavailable": "FAIL_CLOSED_TO_REGISTERED_LOWER_SAFE_PATH_OR_NO_TRADE",
  "effective_owner_dashboard_editability_class": "READ_ONLY_FORMULA_CARD",
  "effective_policy_authority": "CERTIFIED_STEP11_PARAMETER_POLICY",
  "effective_reference_range_or_structural_constraint": "positive rational factor with forward splits typically `> 1` and reverse splits typically `< 1` when expressed on a post/pre basis",
  "effective_resolution_class": "STATIC_FORMULA_WITH_RUNTIME_INPUTS",
  "effective_source_state_refs": [
    "OWNER_POLICY::EX_10O",
    "SOURCE_PACK::EX_10O"
  ],
  "effective_ui_widget_class": "READ_ONLY_FORMULA_CARD",
  "effective_unit_or_basis": "post/pre split factor",
  "effective_value_source_class": "PUBLIC_MARKET_FORMULA_STANDARD",
  "evidence_basis_class": "FAMILY_SOURCE_PACK_PLUS_EXACT_OWNER_APPROVED_VALUE",
  "evidence_binding_rule_refs": [],
  "family_evidence_binding_ref": "ST12-FAMILY-EVIDENCE::EX_10O",
  "implementation_resolution_kind": "RUNTIME_TYPED_BINDING",
  "launch_computability_state": "EXECUTABLE_FAIL_CLOSED_UNTIL_TYPED_CURRENT_BINDING",
  "master_plan_heading_path": [
    "Part II — Retained institutional design and parameter catalog",
    "D14. Canonical family registry — risk and allocation",
    "EX-10O — Equities / ETF corporate-action, ex-date, identifier-change, and position-adjustment atomic parameter pack"
  ],
  "master_plan_section_id": "EX-10O",
  "missing_stale_invalid_behavior": "RETURN_BLOCKER_MISSING_STALE_AMBIGUOUS_OR_OUT_OF_RANGE_NO_VALUE",
  "parameter_audit_id": "ST11-PARAM::02094",
  "parameter_id": "ST10-PARAM::2094",
  "parameter_symbol": "eq_split_factor",
  "precision_and_rounding_policy": {
    "decimal_context_precision": 34,
    "internal_numeric_type": "Decimal",
    "nonfinite_policy": "REJECT",
    "quantization": "SOURCE_OR_UNIT_DECLARED; NO_IMPLICIT_BINARY_FLOAT_CONVERSION",
    "rounding": "ROUND_HALF_EVEN"
  },
  "runtime_resolution_procedure": [
    "Resolve only through BindingProfileV1 using a current SourceSnapshotV1 or declared internal state snapshot.",
    "Validate type, unit, effective time, scope and source epoch before computation.",
    "If missing, stale, ambiguous or out of range, return the exact blocker and no value.",
    "Never let a Codex implementation browse or invent the value; source parser and blocker behavior are specified in the Step 12 source registry."
  ],
  "source_line_end": 55890,
  "source_line_start": 55879,
  "step12_primary_tranche_id": "ST12-TRANCHE-A"
},
{
  "canonical_owner": "QKUComputationControlPlaneV1",
  "certified_step11_custody_ref": "inputs/certified_step11/QTT_Stage1_Step11_Parameter_Policy_Adjudication_v1_0.jsonl#ST11-PARAM::02095",
  "certified_step11_row_embedded_in_prompt": false,
  "codex_online_research_allowed": false,
  "direct_source_claim_justifications": [],
  "effective_bounded_search_space_or_fit_constraint": "formula only; quantity may not be approximated from broker statement deltas without the declared action card",
  "effective_day1_seed_value_or_resolution_rule": "adjusted_quantity = pre_event_quantity * split_factor",
  "effective_default_authority_class": "PUBLIC_METHOD_OR_PINNED_PROVIDER_DEFAULT_REQUIRES_IMPLEMENTATION_VERSION_BINDING",
  "effective_fallback_behavior_when_value_unavailable": "FAIL_CLOSED_TO_REGISTERED_LOWER_SAFE_PATH_OR_NO_TRADE",
  "effective_owner_dashboard_editability_class": "READ_ONLY_FORMULA_CARD",
  "effective_policy_authority": "CERTIFIED_STEP11_PARAMETER_POLICY",
  "effective_reference_range_or_structural_constraint": "exact arithmetic identity on the declared split factor",
  "effective_resolution_class": "STATIC_FORMULA_WITH_RUNTIME_INPUTS",
  "effective_source_state_refs": [
    "OWNER_POLICY::EX_10O",
    "SOURCE_PACK::EX_10O"
  ],
  "effective_ui_widget_class": "READ_ONLY_FORMULA_CARD",
  "effective_unit_or_basis": "shares or units",
  "effective_value_source_class": "PUBLIC_MARKET_FORMULA_STANDARD",
  "evidence_basis_class": "FAMILY_SOURCE_PACK_PLUS_EXACT_OWNER_APPROVED_VALUE",
  "evidence_binding_rule_refs": [],
  "family_evidence_binding_ref": "ST12-FAMILY-EVIDENCE::EX_10O",
  "implementation_resolution_kind": "RUNTIME_TYPED_BINDING",
  "launch_computability_state": "EXECUTABLE_FAIL_CLOSED_UNTIL_TYPED_CURRENT_BINDING",
  "master_plan_heading_path": [
    "Part II — Retained institutional design and parameter catalog",
    "D14. Canonical family registry — risk and allocation",
    "EX-10O — Equities / ETF corporate-action, ex-date, identifier-change, and position-adjustment atomic parameter pack"
  ],
  "master_plan_section_id": "EX-10O",
  "missing_stale_invalid_behavior": "RETURN_BLOCKER_MISSING_STALE_AMBIGUOUS_OR_OUT_OF_RANGE_NO_VALUE",
  "parameter_audit_id": "ST11-PARAM::02095",
  "parameter_id": "ST10-PARAM::2095",
  "parameter_symbol": "eq_split_qty_formula",
  "precision_and_rounding_policy": {
    "finite_check": "REQUIRED",
    "internal_numeric_type": "float64_or_declared_array_dtype",
    "probability_domain": "[0,1] WHEN APPLICABLE",
    "rounding": "NONE_INTERNAL; CONVERT_TO_DECIMAL_AT_FINANCIAL_BOUNDARY"
  },
  "runtime_resolution_procedure": [
    "Resolve only through BindingProfileV1 using a current SourceSnapshotV1 or declared internal state snapshot.",
    "Validate type, unit, effective time, scope and source epoch before computation.",
    "If missing, stale, ambiguous or out of range, return the exact blocker and no value.",
    "Never let a Codex implementation browse or invent the value; source parser and blocker behavior are specified in the Step 12 source registry."
  ],
  "source_line_end": 55902,
  "source_line_start": 55891,
  "step12_primary_tranche_id": "ST12-TRANCHE-A"
},
{
  "canonical_owner": "QKUComputationControlPlaneV1",
  "certified_step11_custody_ref": "inputs/certified_step11/QTT_Stage1_Step11_Parameter_Policy_Adjudication_v1_0.jsonl#ST11-PARAM::02096",
  "certified_step11_row_embedded_in_prompt": false,
  "codex_online_research_allowed": false,
  "direct_source_claim_justifications": [],
  "effective_bounded_search_space_or_fit_constraint": "formula only; price continuity may not be inferred from charting vendor defaults without an explicit adjustment-basis card",
  "effective_day1_seed_value_or_resolution_rule": "adjusted_reference_price = pre_event_reference_price / split_factor",
  "effective_default_authority_class": "PUBLIC_METHOD_OR_PINNED_PROVIDER_DEFAULT_REQUIRES_IMPLEMENTATION_VERSION_BINDING",
  "effective_fallback_behavior_when_value_unavailable": "FAIL_CLOSED_TO_REGISTERED_LOWER_SAFE_PATH_OR_NO_TRADE",
  "effective_owner_dashboard_editability_class": "READ_ONLY_FORMULA_CARD",
  "effective_policy_authority": "CERTIFIED_STEP11_PARAMETER_POLICY",
  "effective_reference_range_or_structural_constraint": "exact arithmetic identity on the declared split factor",
  "effective_resolution_class": "STATIC_FORMULA_WITH_RUNTIME_INPUTS",
  "effective_source_state_refs": [
    "OWNER_POLICY::EX_10O",
    "SOURCE_PACK::EX_10O"
  ],
  "effective_ui_widget_class": "READ_ONLY_FORMULA_CARD",
  "effective_unit_or_basis": "price per share or unit on declared storage basis",
  "effective_value_source_class": "PUBLIC_MARKET_FORMULA_STANDARD",
  "evidence_basis_class": "FAMILY_SOURCE_PACK_PLUS_EXACT_OWNER_APPROVED_VALUE",
  "evidence_binding_rule_refs": [],
  "family_evidence_binding_ref": "ST12-FAMILY-EVIDENCE::EX_10O",
  "implementation_resolution_kind": "RUNTIME_TYPED_BINDING",
  "launch_computability_state": "EXECUTABLE_FAIL_CLOSED_UNTIL_TYPED_CURRENT_BINDING",
  "master_plan_heading_path": [
    "Part II — Retained institutional design and parameter catalog",
    "D14. Canonical family registry — risk and allocation",
    "EX-10O — Equities / ETF corporate-action, ex-date, identifier-change, and position-adjustment atomic parameter pack"
  ],
  "master_plan_section_id": "EX-10O",
  "missing_stale_invalid_behavior": "RETURN_BLOCKER_MISSING_STALE_AMBIGUOUS_OR_OUT_OF_RANGE_NO_VALUE",
  "parameter_audit_id": "ST11-PARAM::02096",
  "parameter_id": "ST10-PARAM::2096",
  "parameter_symbol": "eq_split_px_formula",
  "precision_and_rounding_policy": {
    "decimal_context_precision": 34,
    "internal_numeric_type": "Decimal",
    "nonfinite_policy": "REJECT",
    "quantization": "SOURCE_OR_UNIT_DECLARED; NO_IMPLICIT_BINARY_FLOAT_CONVERSION",
    "rounding": "ROUND_HALF_EVEN"
  },
  "runtime_resolution_procedure": [
    "Resolve only through BindingProfileV1 using a current SourceSnapshotV1 or declared internal state snapshot.",
    "Validate type, unit, effective time, scope and source epoch before computation.",
    "If missing, stale, ambiguous or out of range, return the exact blocker and no value.",
    "Never let a Codex implementation browse or invent the value; source parser and blocker behavior are specified in the Step 12 source registry."
  ],
  "source_line_end": 55914,
  "source_line_start": 55903,
  "step12_primary_tranche_id": "ST12-TRANCHE-A"
},
{
  "canonical_owner": "QKUComputationControlPlaneV1",
  "certified_step11_custody_ref": "inputs/certified_step11/QTT_Stage1_Step11_Parameter_Policy_Adjudication_v1_0.jsonl#ST11-PARAM::02113",
  "certified_step11_row_embedded_in_prompt": false,
  "codex_online_research_allowed": false,
  "direct_source_claim_justifications": [],
  "effective_bounded_search_space_or_fit_constraint": "formula only; no live path may preserve a fixed `< 100 shares` shortcut when the active round lot is smaller than 100",
  "effective_day1_seed_value_or_resolution_rule": "share_quantity < active_round_lot_size",
  "effective_default_authority_class": "PUBLIC_METHOD_OR_PINNED_PROVIDER_DEFAULT_REQUIRES_IMPLEMENTATION_VERSION_BINDING",
  "effective_fallback_behavior_when_value_unavailable": "FAIL_CLOSED_TO_REGISTERED_LOWER_SAFE_PATH_OR_NO_TRADE",
  "effective_owner_dashboard_editability_class": "READ_ONLY_FORMULA_CARD",
  "effective_policy_authority": "CERTIFIED_STEP11_PARAMETER_POLICY",
  "effective_reference_range_or_structural_constraint": "exact public odd-lot definition on the current active round-lot basis",
  "effective_resolution_class": "STRUCTURAL_FORMULA_RULE",
  "effective_source_state_refs": [
    "OWNER_POLICY::EX_10OAA",
    "SOURCE_PACK::EX_10OAA"
  ],
  "effective_ui_widget_class": "READ_ONLY_FORMULA_CARD",
  "effective_unit_or_basis": "odd-lot classification rule",
  "effective_value_source_class": "PUBLIC_OFFICIAL_MARKET_STRUCTURE_STANDARD",
  "evidence_basis_class": "FAMILY_SOURCE_PACK_PLUS_EXACT_OWNER_APPROVED_VALUE",
  "evidence_binding_rule_refs": [],
  "family_evidence_binding_ref": "ST12-FAMILY-EVIDENCE::EX_10OAA",
  "implementation_resolution_kind": "STATIC_OR_DETERMINISTIC_RULE",
  "launch_computability_state": "COMPUTABLE_FROM_STATIC_VALUE_OR_DETERMINISTIC_RULE",
  "master_plan_heading_path": [
    "Part II — Retained institutional design and parameter catalog",
    "D14. Canonical family registry — risk and allocation",
    "EX-10OAA — Equities / ETF variable-round-lot, odd-lot, mixed-lot, and BOLO atomic parameter pack"
  ],
  "master_plan_section_id": "EX-10OAA",
  "missing_stale_invalid_behavior": "REJECT_INVALID_VALUE_NO_SILENT_DEFAULT",
  "parameter_audit_id": "ST11-PARAM::02113",
  "parameter_id": "ST10-PARAM::2113",
  "parameter_symbol": "nms_odd_formula",
  "precision_and_rounding_policy": {
    "allowlist_check": "REQUIRED",
    "internal_numeric_type": "typed_symbolic",
    "normalization": "CANONICAL_EXACT_TOKEN_NO_FREE_TEXT_COERCION",
    "rounding": "NOT_APPLICABLE"
  },
  "runtime_resolution_procedure": [
    "Parse the declared Day-1 seed or deterministic rule into the declared type.",
    "Validate against the reference range and structural constraint.",
    "Apply the declared bounded edit/search law; reject any value outside it."
  ],
  "source_line_end": 56141,
  "source_line_start": 56130,
  "step12_primary_tranche_id": "ST12-TRANCHE-A"
},
{
  "canonical_owner": "QKUComputationControlPlaneV1",
  "certified_step11_custody_ref": "inputs/certified_step11/QTT_Stage1_Step11_Parameter_Policy_Adjudication_v1_0.jsonl#ST11-PARAM::02114",
  "certified_step11_row_embedded_in_prompt": false,
  "codex_online_research_allowed": false,
  "direct_source_claim_justifications": [],
  "effective_bounded_search_space_or_fit_constraint": "formula only; live paths may not infer mixed-lot state from a universal 100-share modulus when the active round lot differs from 100",
  "effective_day1_seed_value_or_resolution_rule": "share_quantity > active_round_lot_size AND share_quantity mod active_round_lot_size != 0",
  "effective_default_authority_class": "PUBLIC_METHOD_OR_PINNED_PROVIDER_DEFAULT_REQUIRES_IMPLEMENTATION_VERSION_BINDING",
  "effective_fallback_behavior_when_value_unavailable": "FAIL_CLOSED_TO_REGISTERED_LOWER_SAFE_PATH_OR_NO_TRADE",
  "effective_owner_dashboard_editability_class": "READ_ONLY_FORMULA_CARD",
  "effective_policy_authority": "CERTIFIED_STEP11_PARAMETER_POLICY",
  "effective_reference_range_or_structural_constraint": "exact public mixed-lot definition on the active round-lot basis",
  "effective_resolution_class": "STRUCTURAL_FORMULA_RULE",
  "effective_source_state_refs": [
    "OWNER_POLICY::EX_10OAA",
    "SOURCE_PACK::EX_10OAA"
  ],
  "effective_ui_widget_class": "READ_ONLY_FORMULA_CARD",
  "effective_unit_or_basis": "mixed-lot classification rule",
  "effective_value_source_class": "PUBLIC_OFFICIAL_MARKET_STRUCTURE_STANDARD",
  "evidence_basis_class": "FAMILY_SOURCE_PACK_PLUS_EXACT_OWNER_APPROVED_VALUE",
  "evidence_binding_rule_refs": [],
  "family_evidence_binding_ref": "ST12-FAMILY-EVIDENCE::EX_10OAA",
  "implementation_resolution_kind": "STATIC_OR_DETERMINISTIC_RULE",
  "launch_computability_state": "COMPUTABLE_FROM_STATIC_VALUE_OR_DETERMINISTIC_RULE",
  "master_plan_heading_path": [
    "Part II — Retained institutional design and parameter catalog",
    "D14. Canonical family registry — risk and allocation",
    "EX-10OAA — Equities / ETF variable-round-lot, odd-lot, mixed-lot, and BOLO atomic parameter pack"
  ],
  "master_plan_section_id": "EX-10OAA",
  "missing_stale_invalid_behavior": "REJECT_INVALID_VALUE_NO_SILENT_DEFAULT",
  "parameter_audit_id": "ST11-PARAM::02114",
  "parameter_id": "ST10-PARAM::2114",
  "parameter_symbol": "nms_mixed_formula",
  "precision_and_rounding_policy": {
    "allowlist_check": "REQUIRED",
    "internal_numeric_type": "typed_symbolic",
    "normalization": "CANONICAL_EXACT_TOKEN_NO_FREE_TEXT_COERCION",
    "rounding": "NOT_APPLICABLE"
  },
  "runtime_resolution_procedure": [
    "Parse the declared Day-1 seed or deterministic rule into the declared type.",
    "Validate against the reference range and structural constraint.",
    "Apply the declared bounded edit/search law; reject any value outside it."
  ],
  "source_line_end": 56153,
  "source_line_start": 56142,
  "step12_primary_tranche_id": "ST12-TRANCHE-A"
},
{
  "canonical_owner": "QKUComputationControlPlaneV1",
  "certified_step11_custody_ref": "inputs/certified_step11/QTT_Stage1_Step11_Parameter_Policy_Adjudication_v1_0.jsonl#ST11-PARAM::02132",
  "certified_step11_row_embedded_in_prompt": false,
  "codex_online_research_allowed": false,
  "direct_source_claim_justifications": [],
  "effective_bounded_search_space_or_fit_constraint": "volatility-guard ambiguity may not silently degrade into ordinary green routing authority",
  "effective_day1_seed_value_or_resolution_rule": "FAIL_CLOSED_TO_NO_NEW_ENTRY_CANCEL_WHAT_CAN_BE_SAFELY_CANCELED_AND_WAIT_FOR_AUTHORITATIVE_REOPEN_OR_RULE_RECOVERY",
  "effective_default_authority_class": "EXPLICIT_QTT_OR_OWNER_POLICY_SEED_OR_RESOLUTION_RULE",
  "effective_fallback_behavior_when_value_unavailable": "FAIL_CLOSED_TO_REGISTERED_LOWER_SAFE_PATH_OR_NO_TRADE",
  "effective_owner_dashboard_editability_class": "READ_ONLY_SYMBOLIC",
  "effective_policy_authority": "CERTIFIED_STEP11_PARAMETER_POLICY",
  "effective_reference_range_or_structural_constraint": "{FAIL_CLOSED_TO_NO_NEW_ENTRY_CANCEL_WHAT_CAN_BE_SAFELY_CANCELED_AND_WAIT_FOR_AUTHORITATIVE_REOPEN_OR_RULE_RECOVERY}",
  "effective_resolution_class": "STATIC_ENUM",
  "effective_source_state_refs": [
    "OWNER_POLICY::EX_10OAB",
    "SOURCE_PACK::EX_10OAB"
  ],
  "effective_ui_widget_class": "FORMULA_BADGE",
  "effective_unit_or_basis": "volatility-guard fallback rule",
  "effective_value_source_class": "QTT_FAIL_CLOSED_MARKET_STRUCTURE_RULE",
  "evidence_basis_class": "FAMILY_SOURCE_PACK_PLUS_EXACT_OWNER_APPROVED_VALUE",
  "evidence_binding_rule_refs": [],
  "family_evidence_binding_ref": "ST12-FAMILY-EVIDENCE::EX_10OAB",
  "implementation_resolution_kind": "EXPLICIT_FAIL_CLOSED_POLICY",
  "launch_computability_state": "COMPUTABLE_TYPED_FAIL_CLOSED_OR_NO_TRADE_STATE",
  "master_plan_heading_path": [
    "Part II — Retained institutional design and parameter catalog",
    "D14. Canonical family registry — risk and allocation",
    "EX-10OAB — Equities / ETF Limit Up-Limit Down, trading-pause, and market-wide circuit-breaker atomic parameter pack"
  ],
  "master_plan_section_id": "EX-10OAB",
  "missing_stale_invalid_behavior": "PRESERVE_EXPLICIT_FAIL_CLOSED_STATE",
  "parameter_audit_id": "ST11-PARAM::02132",
  "parameter_id": "ST10-PARAM::2132",
  "parameter_symbol": "nms_vol_guard_fb",
  "precision_and_rounding_policy": {
    "allowlist_check": "REQUIRED",
    "internal_numeric_type": "typed_symbolic",
    "normalization": "CANONICAL_EXACT_TOKEN_NO_FREE_TEXT_COERCION",
    "rounding": "NOT_APPLICABLE"
  },
  "runtime_resolution_procedure": [
    "Materialize the declared fail-closed state exactly.",
    "Return a typed blocker/no-trade status and do not substitute a numeric fallback.",
    "Validate the resolved typed value or token against the effective resolution class, declared structural constraint, and canonical allowlist; on failure apply the declared fail-closed fallback and emit the exact reason code."
  ],
  "source_line_end": 56389,
  "source_line_start": 56374,
  "step12_primary_tranche_id": "ST12-TRANCHE-A"
},
{
  "canonical_owner": "QKUComputationControlPlaneV1",
  "certified_step11_custody_ref": "inputs/certified_step11/QTT_Stage1_Step11_Parameter_Policy_Adjudication_v1_0.jsonl#ST11-PARAM::02140",
  "certified_step11_row_embedded_in_prompt": false,
  "codex_online_research_allowed": false,
  "direct_source_claim_justifications": [],
  "effective_bounded_search_space_or_fit_constraint": "partial or best-effort sweeps may not masquerade as ISO-compliant behavior",
  "effective_day1_seed_value_or_resolution_rule": "SIMULTANEOUSLY_ROUTE_LIMIT_ORDERS_AS_NEEDED_TO_EXECUTE_AGAINST_FULL_DISPLAYED_SIZE_OF_ALL_BETTER_PRICED_PROTECTED_QUOTES",
  "effective_default_authority_class": "PUBLIC_METHOD_OR_PINNED_PROVIDER_DEFAULT_REQUIRES_IMPLEMENTATION_VERSION_BINDING",
  "effective_fallback_behavior_when_value_unavailable": "FAIL_CLOSED_TO_REGISTERED_LOWER_SAFE_PATH_OR_NO_TRADE",
  "effective_owner_dashboard_editability_class": "READ_ONLY_BY_DEFAULT",
  "effective_policy_authority": "CERTIFIED_STEP11_PARAMETER_POLICY",
  "effective_reference_range_or_structural_constraint": "{FULL_DISPLAYED_SIZE_OF_ALL_BETTER_PRICED_PROTECTED_QUOTES_MUST_BE_SWEPT, DECLARED_STRICTER_INTERNAL_EQUIVALENT}",
  "effective_resolution_class": "STATIC_POLICY_ID",
  "effective_source_state_refs": [
    "OWNER_POLICY::EX_10OAC",
    "SOURCE_PACK::EX_10OAC"
  ],
  "effective_ui_widget_class": "READ_ONLY_POLICY_BADGE",
  "effective_unit_or_basis": "protected-quote sweep requirement policy ID",
  "effective_value_source_class": "PUBLIC_OFFICIAL_MARKET_STRUCTURE_STANDARD",
  "evidence_basis_class": "FAMILY_SOURCE_PACK_PLUS_EXACT_OWNER_APPROVED_VALUE",
  "evidence_binding_rule_refs": [],
  "family_evidence_binding_ref": "ST12-FAMILY-EVIDENCE::EX_10OAC",
  "implementation_resolution_kind": "STATIC_OR_DETERMINISTIC_RULE",
  "launch_computability_state": "COMPUTABLE_FROM_STATIC_VALUE_OR_DETERMINISTIC_RULE",
  "master_plan_heading_path": [
    "Part II — Retained institutional design and parameter catalog",
    "D14. Canonical family registry — risk and allocation",
    "EX-10OAC — Equities / ETF Order Protection Rule, protected-quotation, intermarket-sweep-order, and locked/crossed-market atomic parameter pack"
  ],
  "master_plan_section_id": "EX-10OAC",
  "missing_stale_invalid_behavior": "REJECT_INVALID_VALUE_NO_SILENT_DEFAULT",
  "parameter_audit_id": "ST11-PARAM::02140",
  "parameter_id": "ST10-PARAM::2140",
  "parameter_symbol": "nms_iso_sweep",
  "precision_and_rounding_policy": {
    "allowlist_check": "REQUIRED",
    "internal_numeric_type": "typed_symbolic",
    "normalization": "CANONICAL_EXACT_TOKEN_NO_FREE_TEXT_COERCION",
    "rounding": "NOT_APPLICABLE"
  },
  "runtime_resolution_procedure": [
    "Parse the declared Day-1 seed or deterministic rule into the declared type.",
    "Validate against the reference range and structural constraint.",
    "Apply the declared bounded edit/search law; reject any value outside it."
  ],
  "source_line_end": 56492,
  "source_line_start": 56481,
  "step12_primary_tranche_id": "ST12-TRANCHE-A"
},
{
  "canonical_owner": "QKUComputationControlPlaneV1",
  "certified_step11_custody_ref": "inputs/certified_step11/QTT_Stage1_Step11_Parameter_Policy_Adjudication_v1_0.jsonl#ST11-PARAM::02144",
  "certified_step11_row_embedded_in_prompt": false,
  "codex_online_research_allowed": false,
  "direct_source_claim_justifications": [],
  "effective_bounded_search_space_or_fit_constraint": "order-protection ambiguity may not silently degrade into ordinary green routing authority",
  "effective_day1_seed_value_or_resolution_rule": "FAIL_CLOSED_TO_NO_INFERIOR_EXECUTION_NO_UNPROVEN_ISO_AND_WAIT_FOR_AUTHORITATIVE_PROTECTED_QUOTE_STATE_RECOVERY",
  "effective_default_authority_class": "EXPLICIT_QTT_OR_OWNER_POLICY_SEED_OR_RESOLUTION_RULE",
  "effective_fallback_behavior_when_value_unavailable": "FAIL_CLOSED_TO_REGISTERED_LOWER_SAFE_PATH_OR_NO_TRADE",
  "effective_owner_dashboard_editability_class": "READ_ONLY_SYMBOLIC",
  "effective_policy_authority": "CERTIFIED_STEP11_PARAMETER_POLICY",
  "effective_reference_range_or_structural_constraint": "{FAIL_CLOSED_TO_NO_INFERIOR_EXECUTION_NO_UNPROVEN_ISO_AND_WAIT_FOR_AUTHORITATIVE_PROTECTED_QUOTE_STATE_RECOVERY}",
  "effective_resolution_class": "STATIC_ENUM",
  "effective_source_state_refs": [
    "OWNER_POLICY::EX_10OAC",
    "SOURCE_PACK::EX_10OAC"
  ],
  "effective_ui_widget_class": "FORMULA_BADGE",
  "effective_unit_or_basis": "order-protection fallback rule",
  "effective_value_source_class": "QTT_FAIL_CLOSED_MARKET_STRUCTURE_RULE",
  "evidence_basis_class": "FAMILY_SOURCE_PACK_PLUS_EXACT_OWNER_APPROVED_VALUE",
  "evidence_binding_rule_refs": [],
  "family_evidence_binding_ref": "ST12-FAMILY-EVIDENCE::EX_10OAC",
  "implementation_resolution_kind": "EXPLICIT_FAIL_CLOSED_POLICY",
  "launch_computability_state": "COMPUTABLE_TYPED_FAIL_CLOSED_OR_NO_TRADE_STATE",
  "master_plan_heading_path": [
    "Part II — Retained institutional design and parameter catalog",
    "D14. Canonical family registry — risk and allocation",
    "EX-10OAC — Equities / ETF Order Protection Rule, protected-quotation, intermarket-sweep-order, and locked/crossed-market atomic parameter pack"
  ],
  "master_plan_section_id": "EX-10OAC",
  "missing_stale_invalid_behavior": "PRESERVE_EXPLICIT_FAIL_CLOSED_STATE",
  "parameter_audit_id": "ST11-PARAM::02144",
  "parameter_id": "ST10-PARAM::2144",
  "parameter_symbol": "nms_opr_fb",
  "precision_and_rounding_policy": {
    "allowlist_check": "REQUIRED",
    "internal_numeric_type": "typed_symbolic",
    "normalization": "CANONICAL_EXACT_TOKEN_NO_FREE_TEXT_COERCION",
    "rounding": "NOT_APPLICABLE"
  },
  "runtime_resolution_procedure": [
    "Materialize the declared fail-closed state exactly.",
    "Return a typed blocker/no-trade status and do not substitute a numeric fallback.",
    "Validate the resolved typed value or token against the effective resolution class, declared structural constraint, and canonical allowlist; on failure apply the declared fail-closed fallback and emit the exact reason code."
  ],
  "source_line_end": 56545,
  "source_line_start": 56529,
  "step12_primary_tranche_id": "ST12-TRANCHE-A"
},
{
  "canonical_owner": "QKUComputationControlPlaneV1",
  "certified_step11_custody_ref": "inputs/certified_step11/QTT_Stage1_Step11_Parameter_Policy_Adjudication_v1_0.jsonl#ST11-PARAM::02153",
  "certified_step11_row_embedded_in_prompt": false,
  "codex_online_research_allowed": false,
  "direct_source_claim_justifications": [],
  "effective_bounded_search_space_or_fit_constraint": "unresolved consolidated-equity market-structure semantics may not be guessed from stale vendor memory, copied exchange examples, or undeclared local heuristics",
  "effective_day1_seed_value_or_resolution_rule": "PRESERVE_LAST_AUTHORIZED_OPERATIVE_ROUND_LOT_ASSIGNMENT_IF_AND_ONLY_IF_ITS_EFFECTIVE_PERIOD_IS_STILL_VALID; OTHERWISE_DISABLE_ROUND_LOT_SENSITIVE_ANALYTICS_DISABLE_BOLO_DEPENDENT_LOGIC_SUPPRESS_ISO_HANDLING_BLOCK_OUT_OF_BAND_ORDER_RELEASE_BLOCK_UNAUTHORIZED_ORDER_PROTECTION_ASSERTIONS_AND_DOWNGRADE_TO_READ_ONLY_OR_NO_TRADE_UNTIL_AUTHORITATIVE_MARKET_STRUCTURE_RECOVERY",
  "effective_default_authority_class": "EXPLICIT_QTT_OR_OWNER_POLICY_SEED_OR_RESOLUTION_RULE",
  "effective_fallback_behavior_when_value_unavailable": "FAIL_CLOSED_TO_REGISTERED_LOWER_SAFE_PATH_OR_NO_TRADE",
  "effective_owner_dashboard_editability_class": "READ_ONLY_BY_DEFAULT",
  "effective_policy_authority": "CERTIFIED_STEP11_PARAMETER_POLICY",
  "effective_reference_range_or_structural_constraint": "{PRESERVE_STILL_VALID_OPERATIVE_ROUND_LOT_ONLY,DISABLE_BOLO_WHEN_NOT_AUTHORITATIVE,SUPPRESS_ISO_WHEN_MARKER_NOT_AUTHORITATIVE,BLOCK_OUT_OF_BAND_AND_ORDER_PROTECTION_ASSUMPTIONS_WHEN_LULD_OR_NBBO_STATE_IS_NOT_AUTHORITATIVE,READ_ONLY_OR_NO_TRADE_UNTIL_RECOVERY}",
  "effective_resolution_class": "STATIC_ENUM_OR_RULE",
  "effective_source_state_refs": [
    "OWNER_POLICY::EX_10OAC1",
    "SOURCE_PACK::EX_10OAC1"
  ],
  "effective_ui_widget_class": "READ_ONLY_POLICY_CARD",
  "effective_unit_or_basis": "shared consolidated-equity pointer fail-closed rule",
  "effective_value_source_class": "QTT_FAIL_CLOSED_CONSOLIDATED_EQUITY_MARKET_STRUCTURE_RULE",
  "evidence_basis_class": "FAMILY_SOURCE_PACK_PLUS_EXACT_OWNER_APPROVED_VALUE",
  "evidence_binding_rule_refs": [],
  "family_evidence_binding_ref": "ST12-FAMILY-EVIDENCE::EX_10OAC1",
  "implementation_resolution_kind": "EXPLICIT_FAIL_CLOSED_POLICY",
  "launch_computability_state": "COMPUTABLE_TYPED_FAIL_CLOSED_OR_NO_TRADE_STATE",
  "master_plan_heading_path": [
    "Part II — Retained institutional design and parameter catalog",
    "D14. Canonical family registry — risk and allocation",
    "EX-10OAC1 — Equities / ETF round-lot, BOLO, LULD, MWCB, NBBO, and ISO pointer resolution closure"
  ],
  "master_plan_section_id": "EX-10OAC1",
  "missing_stale_invalid_behavior": "PRESERVE_EXPLICIT_FAIL_CLOSED_STATE",
  "parameter_audit_id": "ST11-PARAM::02153",
  "parameter_id": "ST10-PARAM::2153",
  "parameter_symbol": "nms_ptr_fail",
  "precision_and_rounding_policy": {
    "allowlist_check": "REQUIRED",
    "internal_numeric_type": "typed_symbolic",
    "normalization": "CANONICAL_EXACT_TOKEN_NO_FREE_TEXT_COERCION",
    "rounding": "NOT_APPLICABLE"
  },
  "runtime_resolution_procedure": [
    "Materialize the declared fail-closed state exactly.",
    "Return a typed blocker/no-trade status and do not substitute a numeric fallback.",
    "Validate the resolved typed value or token against the effective resolution class, declared structural constraint, and canonical allowlist; on failure apply the declared fail-closed fallback and emit the exact reason code."
  ],
  "source_line_end": 56662,
  "source_line_start": 56648,
  "step12_primary_tranche_id": "ST12-TRANCHE-A"
},
{
  "canonical_owner": "QKUComputationControlPlaneV1",
  "certified_step11_custody_ref": "inputs/certified_step11/QTT_Stage1_Step11_Parameter_Policy_Adjudication_v1_0.jsonl#ST11-PARAM::02159",
  "certified_step11_row_embedded_in_prompt": false,
  "codex_online_research_allowed": false,
  "direct_source_claim_justifications": [],
  "effective_bounded_search_space_or_fit_constraint": "formula fixed unless a strictly equivalent algebraic representation is declared; live paths may not mix premium/discount percentages and cents without explicit unit labeling",
  "effective_day1_seed_value_or_resolution_rule": "PREMIUM_DISCOUNT_TO_NAV = (MARKET_PRICE - NAV_PER_SHARE) / NAV_PER_SHARE",
  "effective_default_authority_class": "PUBLIC_METHOD_OR_PINNED_PROVIDER_DEFAULT_REQUIRES_IMPLEMENTATION_VERSION_BINDING",
  "effective_fallback_behavior_when_value_unavailable": "FAIL_CLOSED_TO_REGISTERED_LOWER_SAFE_PATH_OR_NO_TRADE",
  "effective_owner_dashboard_editability_class": "READ_ONLY_BY_DEFAULT",
  "effective_policy_authority": "CERTIFIED_STEP11_PARAMETER_POLICY",
  "effective_reference_range_or_structural_constraint": "open real-valued ratio; zero denotes parity; sign preserves premium-versus-discount direction",
  "effective_resolution_class": "STATIC_FORMULA_ID",
  "effective_source_state_refs": [
    "OWNER_POLICY::EX_10OB",
    "SOURCE_PACK::EX_10OB"
  ],
  "effective_ui_widget_class": "FORMULA_CARD",
  "effective_unit_or_basis": "ratio to NAV per share",
  "effective_value_source_class": "PUBLIC_STRUCTURAL_FORMULA",
  "evidence_basis_class": "FAMILY_SOURCE_PACK_PLUS_EXACT_OWNER_APPROVED_VALUE",
  "evidence_binding_rule_refs": [],
  "family_evidence_binding_ref": "ST12-FAMILY-EVIDENCE::EX_10OB",
  "implementation_resolution_kind": "STATIC_OR_DETERMINISTIC_RULE",
  "launch_computability_state": "COMPUTABLE_FROM_STATIC_VALUE_OR_DETERMINISTIC_RULE",
  "master_plan_heading_path": [
    "Part II — Retained institutional design and parameter catalog",
    "D14. Canonical family registry — risk and allocation",
    "EX-10OB — ETF primary-market creation/redemption, basket-policy, and NAV-deviation atomic parameter pack"
  ],
  "master_plan_section_id": "EX-10OB",
  "missing_stale_invalid_behavior": "REJECT_INVALID_VALUE_NO_SILENT_DEFAULT",
  "parameter_audit_id": "ST11-PARAM::02159",
  "parameter_id": "ST10-PARAM::2159",
  "parameter_symbol": "etf_nav_gap_policy",
  "precision_and_rounding_policy": {
    "decimal_context_precision": 34,
    "internal_numeric_type": "Decimal",
    "nonfinite_policy": "REJECT",
    "quantization": "SOURCE_OR_UNIT_DECLARED; NO_IMPLICIT_BINARY_FLOAT_CONVERSION",
    "rounding": "ROUND_HALF_EVEN"
  },
  "runtime_resolution_procedure": [
    "Parse the declared Day-1 seed or deterministic rule into the declared type.",
    "Validate against the reference range and structural constraint.",
    "Apply the declared bounded edit/search law; reject any value outside it."
  ],
  "source_line_end": 56738,
  "source_line_start": 56727,
  "step12_primary_tranche_id": "ST12-TRANCHE-A"
},
{
  "canonical_owner": "QKUComputationControlPlaneV1",
  "certified_step11_custody_ref": "inputs/certified_step11/QTT_Stage1_Step11_Parameter_Policy_Adjudication_v1_0.jsonl#ST11-PARAM::02256",
  "certified_step11_row_embedded_in_prompt": false,
  "codex_online_research_allowed": false,
  "direct_source_claim_justifications": [],
  "effective_bounded_search_space_or_fit_constraint": "runtime-derived only inside the declared session or quoting window",
  "effective_day1_seed_value_or_resolution_rule": "remaining_session_or_quote_horizon",
  "effective_default_authority_class": "EXPLICIT_QTT_OR_OWNER_POLICY_SEED_OR_RESOLUTION_RULE",
  "effective_fallback_behavior_when_value_unavailable": "FAIL_CLOSED_TO_REGISTERED_LOWER_SAFE_PATH_OR_NO_TRADE",
  "effective_owner_dashboard_editability_class": "READ_ONLY_BY_DEFAULT",
  "effective_policy_authority": "CERTIFIED_STEP11_PARAMETER_POLICY",
  "effective_reference_range_or_structural_constraint": "positive remaining horizon on the declared time basis",
  "effective_resolution_class": "RUN_TIME_CONTEXTUAL_READ_ONLY",
  "effective_source_state_refs": [
    "OWNER_POLICY::EX_15B",
    "SOURCE_PACK::EX_15B"
  ],
  "effective_ui_widget_class": "READ_ONLY_NUMERIC",
  "effective_unit_or_basis": "remaining quote horizon on declared time basis",
  "effective_value_source_class": "MARKET_FAMILY_CONVENTION",
  "evidence_basis_class": "FAMILY_SOURCE_PACK_PLUS_EXACT_OWNER_APPROVED_VALUE",
  "evidence_binding_rule_refs": [],
  "family_evidence_binding_ref": "ST12-FAMILY-EVIDENCE::EX_15B",
  "implementation_resolution_kind": "STATIC_OR_DETERMINISTIC_RULE",
  "launch_computability_state": "COMPUTABLE_FROM_STATIC_VALUE_OR_DETERMINISTIC_RULE",
  "master_plan_heading_path": [
    "Part II — Retained institutional design and parameter catalog",
    "D14. Canonical family registry — risk and allocation",
    "EX-15B — Quote-utility and inventory-aware market-making atomic parameter pack"
  ],
  "master_plan_section_id": "EX-15B",
  "missing_stale_invalid_behavior": "REJECT_INVALID_VALUE_NO_SILENT_DEFAULT",
  "parameter_audit_id": "ST11-PARAM::02256",
  "parameter_id": "ST10-PARAM::2256",
  "parameter_symbol": "T_minus_t",
  "precision_and_rounding_policy": {
    "finite_check": "REQUIRED_FOR_NUMERIC_VALUES",
    "internal_numeric_type": "declared_typed_scalar_or_structure",
    "rounding": "PER_UNIT_OR_SOURCE_RULE"
  },
  "runtime_resolution_procedure": [
    "Parse the declared Day-1 seed or deterministic rule into the declared type.",
    "Validate against the reference range and structural constraint.",
    "Apply the declared bounded edit/search law; reject any value outside it."
  ],
  "source_line_end": 58180,
  "source_line_start": 58169,
  "step12_primary_tranche_id": "ST12-TRANCHE-A"
},
{
  "canonical_owner": "QKUComputationControlPlaneV1",
  "certified_step11_custody_ref": "inputs/certified_step11/QTT_Stage1_Step11_Parameter_Policy_Adjudication_v1_0.jsonl#ST11-PARAM::03267",
  "certified_step11_row_embedded_in_prompt": false,
  "codex_online_research_allowed": false,
  "direct_source_claim_justifications": [],
  "effective_bounded_search_space_or_fit_constraint": "venue-defined only",
  "effective_day1_seed_value_or_resolution_rule": "FIXT.1.1",
  "effective_default_authority_class": "EXPLICIT_QTT_OR_OWNER_POLICY_SEED_OR_RESOLUTION_RULE",
  "effective_fallback_behavior_when_value_unavailable": "FAIL_CLOSED_TO_REGISTERED_LOWER_SAFE_PATH_OR_NO_TRADE",
  "effective_owner_dashboard_editability_class": "VIEW_ONLY_RESOLVED",
  "effective_policy_authority": "CERTIFIED_STEP11_PARAMETER_POLICY",
  "effective_reference_range_or_structural_constraint": "{FIXT.1.1}",
  "effective_resolution_class": "STATIC_ENUM",
  "effective_source_state_refs": [
    "OWNER_POLICY::CN_02A",
    "SOURCE_PACK::CN_02A"
  ],
  "effective_ui_widget_class": "BADGE",
  "effective_unit_or_basis": "protocol-version enum",
  "effective_value_source_class": "OFFICIAL_VENUE_DOCUMENTATION",
  "evidence_basis_class": "FAMILY_SOURCE_PACK_PLUS_EXACT_OWNER_APPROVED_VALUE",
  "evidence_binding_rule_refs": [],
  "family_evidence_binding_ref": "ST12-FAMILY-EVIDENCE::CN_02A",
  "implementation_resolution_kind": "STATIC_OR_DETERMINISTIC_RULE",
  "launch_computability_state": "COMPUTABLE_FROM_STATIC_VALUE_OR_DETERMINISTIC_RULE",
  "master_plan_heading_path": [
    "Part II — Retained institutional design and parameter catalog",
    "D17. Canonical family registry — connectors",
    "CN-02A — Kalshi FIX session, protocol-version, signature, and maintenance atomic profile"
  ],
  "master_plan_section_id": "CN-02A",
  "missing_stale_invalid_behavior": "REJECT_INVALID_VALUE_NO_SILENT_DEFAULT",
  "parameter_audit_id": "ST11-PARAM::03267",
  "parameter_id": "ST10-PARAM::3267",
  "parameter_symbol": "fix_begin",
  "precision_and_rounding_policy": {
    "allowlist_check": "REQUIRED",
    "internal_numeric_type": "typed_symbolic",
    "normalization": "CANONICAL_EXACT_TOKEN_NO_FREE_TEXT_COERCION",
    "rounding": "NOT_APPLICABLE"
  },
  "runtime_resolution_procedure": [
    "Parse the declared Day-1 seed or deterministic rule into the declared type.",
    "Validate against the reference range and structural constraint.",
    "Apply the declared bounded edit/search law; reject any value outside it."
  ],
  "source_line_end": 78496,
  "source_line_start": 78485,
  "step12_primary_tranche_id": "ST12-TRANCHE-A"
},
{
  "canonical_owner": "QKUComputationControlPlaneV1",
  "certified_step11_custody_ref": "inputs/certified_step11/QTT_Stage1_Step11_Parameter_Policy_Adjudication_v1_0.jsonl#ST11-PARAM::03268",
  "certified_step11_row_embedded_in_prompt": false,
  "codex_online_research_allowed": false,
  "direct_source_claim_justifications": [],
  "effective_bounded_search_space_or_fit_constraint": "venue-defined only",
  "effective_day1_seed_value_or_resolution_rule": "FIX50SP2",
  "effective_default_authority_class": "EXPLICIT_QTT_OR_OWNER_POLICY_SEED_OR_RESOLUTION_RULE",
  "effective_fallback_behavior_when_value_unavailable": "FAIL_CLOSED_TO_REGISTERED_LOWER_SAFE_PATH_OR_NO_TRADE",
  "effective_owner_dashboard_editability_class": "VIEW_ONLY_RESOLVED",
  "effective_policy_authority": "CERTIFIED_STEP11_PARAMETER_POLICY",
  "effective_reference_range_or_structural_constraint": "{FIX50SP2}",
  "effective_resolution_class": "STATIC_ENUM",
  "effective_source_state_refs": [
    "OWNER_POLICY::CN_02A",
    "SOURCE_PACK::CN_02A"
  ],
  "effective_ui_widget_class": "BADGE",
  "effective_unit_or_basis": "FIX application-version enum",
  "effective_value_source_class": "OFFICIAL_VENUE_DOCUMENTATION",
  "evidence_basis_class": "FAMILY_SOURCE_PACK_PLUS_EXACT_OWNER_APPROVED_VALUE",
  "evidence_binding_rule_refs": [],
  "family_evidence_binding_ref": "ST12-FAMILY-EVIDENCE::CN_02A",
  "implementation_resolution_kind": "STATIC_OR_DETERMINISTIC_RULE",
  "launch_computability_state": "COMPUTABLE_FROM_STATIC_VALUE_OR_DETERMINISTIC_RULE",
  "master_plan_heading_path": [
    "Part II — Retained institutional design and parameter catalog",
    "D17. Canonical family registry — connectors",
    "CN-02A — Kalshi FIX session, protocol-version, signature, and maintenance atomic profile"
  ],
  "master_plan_section_id": "CN-02A",
  "missing_stale_invalid_behavior": "REJECT_INVALID_VALUE_NO_SILENT_DEFAULT",
  "parameter_audit_id": "ST11-PARAM::03268",
  "parameter_id": "ST10-PARAM::3268",
  "parameter_symbol": "fix_app_ver",
  "precision_and_rounding_policy": {
    "allowlist_check": "REQUIRED",
    "internal_numeric_type": "typed_symbolic",
    "normalization": "CANONICAL_EXACT_TOKEN_NO_FREE_TEXT_COERCION",
    "rounding": "NOT_APPLICABLE"
  },
  "runtime_resolution_procedure": [
    "Parse the declared Day-1 seed or deterministic rule into the declared type.",
    "Validate against the reference range and structural constraint.",
    "Apply the declared bounded edit/search law; reject any value outside it."
  ],
  "source_line_end": 78508,
  "source_line_start": 78497,
  "step12_primary_tranche_id": "ST12-TRANCHE-A"
},
{
  "canonical_owner": "QKUComputationControlPlaneV1",
  "certified_step11_custody_ref": "inputs/certified_step11/QTT_Stage1_Step11_Parameter_Policy_Adjudication_v1_0.jsonl#ST11-PARAM::03269",
  "certified_step11_row_embedded_in_prompt": false,
  "codex_online_research_allowed": false,
  "direct_source_claim_justifications": [],
  "effective_bounded_search_space_or_fit_constraint": "venue-defined only",
  "effective_day1_seed_value_or_resolution_rule": "RSA_PSS_OVER_PREHASH_STRING",
  "effective_default_authority_class": "EXPLICIT_QTT_OR_OWNER_POLICY_SEED_OR_RESOLUTION_RULE",
  "effective_fallback_behavior_when_value_unavailable": "FAIL_CLOSED_TO_REGISTERED_LOWER_SAFE_PATH_OR_NO_TRADE",
  "effective_owner_dashboard_editability_class": "VIEW_ONLY_RESOLVED",
  "effective_policy_authority": "CERTIFIED_STEP11_PARAMETER_POLICY",
  "effective_reference_range_or_structural_constraint": "{RSA_PSS_OVER_PREHASH_STRING}",
  "effective_resolution_class": "STATIC_ENUM",
  "effective_source_state_refs": [
    "OWNER_POLICY::CN_02A",
    "SOURCE_PACK::CN_02A"
  ],
  "effective_ui_widget_class": "BADGE",
  "effective_unit_or_basis": "signature-method enum",
  "effective_value_source_class": "OFFICIAL_VENUE_DOCUMENTATION",
  "evidence_basis_class": "FAMILY_SOURCE_PACK_PLUS_EXACT_OWNER_APPROVED_VALUE",
  "evidence_binding_rule_refs": [],
  "family_evidence_binding_ref": "ST12-FAMILY-EVIDENCE::CN_02A",
  "implementation_resolution_kind": "STATIC_OR_DETERMINISTIC_RULE",
  "launch_computability_state": "COMPUTABLE_FROM_STATIC_VALUE_OR_DETERMINISTIC_RULE",
  "master_plan_heading_path": [
    "Part II — Retained institutional design and parameter catalog",
    "D17. Canonical family registry — connectors",
    "CN-02A — Kalshi FIX session, protocol-version, signature, and maintenance atomic profile"
  ],
  "master_plan_section_id": "CN-02A",
  "missing_stale_invalid_behavior": "REJECT_INVALID_VALUE_NO_SILENT_DEFAULT",
  "parameter_audit_id": "ST11-PARAM::03269",
  "parameter_id": "ST10-PARAM::3269",
  "parameter_symbol": "sig_method_fix",
  "precision_and_rounding_policy": {
    "allowlist_check": "REQUIRED",
    "internal_numeric_type": "typed_symbolic",
    "normalization": "CANONICAL_EXACT_TOKEN_NO_FREE_TEXT_COERCION",
    "rounding": "NOT_APPLICABLE"
  },
  "runtime_resolution_procedure": [
    "Parse the declared Day-1 seed or deterministic rule into the declared type.",
    "Validate against the reference range and structural constraint.",
    "Apply the declared bounded edit/search law; reject any value outside it."
  ],
  "source_line_end": 78520,
  "source_line_start": 78509,
  "step12_primary_tranche_id": "ST12-TRANCHE-A"
},
{
  "canonical_owner": "QKUComputationControlPlaneV1",
  "certified_step11_custody_ref": "inputs/certified_step11/QTT_Stage1_Step11_Parameter_Policy_Adjudication_v1_0.jsonl#ST11-PARAM::03271",
  "certified_step11_row_embedded_in_prompt": false,
  "codex_online_research_allowed": false,
  "direct_source_claim_justifications": [],
  "effective_bounded_search_space_or_fit_constraint": "venue-defined only",
  "effective_day1_seed_value_or_resolution_rule": "Y_ON_FIRST_LOGON_AFTER_MAINTENANCE",
  "effective_default_authority_class": "EXPLICIT_QTT_OR_OWNER_POLICY_SEED_OR_RESOLUTION_RULE",
  "effective_fallback_behavior_when_value_unavailable": "FAIL_CLOSED_TO_REGISTERED_LOWER_SAFE_PATH_OR_NO_TRADE",
  "effective_owner_dashboard_editability_class": "VIEW_ONLY_RESOLVED",
  "effective_policy_authority": "CERTIFIED_STEP11_PARAMETER_POLICY",
  "effective_reference_range_or_structural_constraint": "{Y_ON_FIRST_LOGON_AFTER_MAINTENANCE}",
  "effective_resolution_class": "STATIC_ENUM",
  "effective_source_state_refs": [
    "OWNER_POLICY::CN_02A",
    "SOURCE_PACK::CN_02A"
  ],
  "effective_ui_widget_class": "BADGE",
  "effective_unit_or_basis": "reset-sequence policy enum",
  "effective_value_source_class": "OFFICIAL_VENUE_DOCUMENTATION",
  "evidence_basis_class": "FAMILY_SOURCE_PACK_PLUS_EXACT_OWNER_APPROVED_VALUE",
  "evidence_binding_rule_refs": [],
  "family_evidence_binding_ref": "ST12-FAMILY-EVIDENCE::CN_02A",
  "implementation_resolution_kind": "STATIC_OR_DETERMINISTIC_RULE",
  "launch_computability_state": "COMPUTABLE_FROM_STATIC_VALUE_OR_DETERMINISTIC_RULE",
  "master_plan_heading_path": [
    "Part II — Retained institutional design and parameter catalog",
    "D17. Canonical family registry — connectors",
    "CN-02A — Kalshi FIX session, protocol-version, signature, and maintenance atomic profile"
  ],
  "master_plan_section_id": "CN-02A",
  "missing_stale_invalid_behavior": "REJECT_INVALID_VALUE_NO_SILENT_DEFAULT",
  "parameter_audit_id": "ST11-PARAM::03271",
  "parameter_id": "ST10-PARAM::3271",
  "parameter_symbol": "reset_seq_post_maint",
  "precision_and_rounding_policy": {
    "allowlist_check": "REQUIRED",
    "internal_numeric_type": "typed_symbolic",
    "normalization": "CANONICAL_EXACT_TOKEN_NO_FREE_TEXT_COERCION",
    "rounding": "NOT_APPLICABLE"
  },
  "runtime_resolution_procedure": [
    "Parse the declared Day-1 seed or deterministic rule into the declared type.",
    "Validate against the reference range and structural constraint.",
    "Apply the declared bounded edit/search law; reject any value outside it."
  ],
  "source_line_end": 78544,
  "source_line_start": 78533,
  "step12_primary_tranche_id": "ST12-TRANCHE-A"
},
{
  "canonical_owner": "QKUComputationControlPlaneV1",
  "certified_step11_custody_ref": "inputs/certified_step11/QTT_Stage1_Step11_Parameter_Policy_Adjudication_v1_0.jsonl#ST11-PARAM::03272",
  "certified_step11_row_embedded_in_prompt": false,
  "codex_online_research_allowed": false,
  "direct_source_claim_justifications": [],
  "effective_bounded_search_space_or_fit_constraint": "venue-defined only until official docs change",
  "effective_day1_seed_value_or_resolution_rule": "THURSDAY_03_00_TO_05_00_ET_FORCE_DISCONNECT_AND_RESET_TO_1_ON_RECONNECT",
  "effective_default_authority_class": "EXPLICIT_QTT_OR_OWNER_POLICY_SEED_OR_RESOLUTION_RULE",
  "effective_fallback_behavior_when_value_unavailable": "FAIL_CLOSED_TO_REGISTERED_LOWER_SAFE_PATH_OR_NO_TRADE",
  "effective_owner_dashboard_editability_class": "VIEW_ONLY_RESOLVED",
  "effective_policy_authority": "CERTIFIED_STEP11_PARAMETER_POLICY",
  "effective_reference_range_or_structural_constraint": "venue-defined scheduled window plus mandatory reset behavior",
  "effective_resolution_class": "STATIC_STRUCTURED_POLICY",
  "effective_source_state_refs": [
    "OWNER_POLICY::CN_02A",
    "SOURCE_PACK::CN_02A"
  ],
  "effective_ui_widget_class": "READ_ONLY_SCHEDULE_BADGE",
  "effective_unit_or_basis": "weekly scheduled-maintenance policy",
  "effective_value_source_class": "OFFICIAL_VENUE_DOCUMENTATION",
  "evidence_basis_class": "FAMILY_SOURCE_PACK_PLUS_EXACT_OWNER_APPROVED_VALUE",
  "evidence_binding_rule_refs": [],
  "family_evidence_binding_ref": "ST12-FAMILY-EVIDENCE::CN_02A",
  "implementation_resolution_kind": "STATIC_OR_DETERMINISTIC_RULE",
  "launch_computability_state": "COMPUTABLE_FROM_STATIC_VALUE_OR_DETERMINISTIC_RULE",
  "master_plan_heading_path": [
    "Part II — Retained institutional design and parameter catalog",
    "D17. Canonical family registry — connectors",
    "CN-02A — Kalshi FIX session, protocol-version, signature, and maintenance atomic profile"
  ],
  "master_plan_section_id": "CN-02A",
  "missing_stale_invalid_behavior": "REJECT_INVALID_VALUE_NO_SILENT_DEFAULT",
  "parameter_audit_id": "ST11-PARAM::03272",
  "parameter_id": "ST10-PARAM::3272",
  "parameter_symbol": "maint_fix_kalshi",
  "precision_and_rounding_policy": {
    "allowlist_check": "REQUIRED",
    "internal_numeric_type": "typed_symbolic",
    "normalization": "CANONICAL_EXACT_TOKEN_NO_FREE_TEXT_COERCION",
    "rounding": "NOT_APPLICABLE"
  },
  "runtime_resolution_procedure": [
    "Parse the declared Day-1 seed or deterministic rule into the declared type.",
    "Validate against the reference range and structural constraint.",
    "Apply the declared bounded edit/search law; reject any value outside it."
  ],
  "source_line_end": 78557,
  "source_line_start": 78545,
  "step12_primary_tranche_id": "ST12-TRANCHE-A"
},
{
  "canonical_owner": "QKUComputationControlPlaneV1",
  "certified_step11_custody_ref": "inputs/certified_step11/QTT_Stage1_Step11_Parameter_Policy_Adjudication_v1_0.jsonl#ST11-PARAM::03350",
  "certified_step11_row_embedded_in_prompt": false,
  "codex_online_research_allowed": false,
  "direct_source_claim_justifications": [
    {
      "binding_rule_ref": "ST12-SOURCE-RULE::011",
      "claim_selector": "EXACT_ATOMIC_FACT_ID_MEMBERSHIP_ONLY",
      "exact_parameter_scope": [
        "ST10-PARAM::3350"
      ],
      "justification": "EXACT_SECTION_PARAMETER_OR_CURRENTIZATION_OVERRIDE_MATCH; NO_INHERITED_SHORT_ALIAS_OR_BROAD_REGEX",
      "source_identity_ref": "VENUE::ST10-SOURCE_11::POLYMARKET_GLOBAL_CURRENT_RATE_LIMITS"
    }
  ],
  "effective_bounded_search_space_or_fit_constraint": "ambiguous connector health may not preserve ordinary new-write authority",
  "effective_day1_seed_value_or_resolution_rule": "FAIL_CLOSED_TO_READ_ONLY_OR_SAFE_HARBOR_WITH_NO_NEW_WRITES",
  "effective_default_authority_class": "EXPLICIT_QTT_OR_OWNER_POLICY_SEED_OR_RESOLUTION_RULE",
  "effective_fallback_behavior_when_value_unavailable": "FAIL_CLOSED_TO_REGISTERED_LOWER_SAFE_PATH_OR_NO_TRADE",
  "effective_owner_dashboard_editability_class": "READ_ONLY_SYMBOLIC",
  "effective_policy_authority": "CERTIFIED_STEP11_PARAMETER_POLICY",
  "effective_reference_range_or_structural_constraint": "{FAIL_CLOSED_TO_READ_ONLY_OR_SAFE_HARBOR_WITH_NO_NEW_WRITES}",
  "effective_resolution_class": "STATIC_ENUM",
  "effective_source_state_refs": [
    "OWNER_POLICY::CN_08A",
    "VENUE::ST10-SOURCE_11::POLYMARKET_GLOBAL_CURRENT_RATE_LIMITS"
  ],
  "effective_ui_widget_class": "FORMULA_BADGE",
  "effective_unit_or_basis": "connector-health fallback rule",
  "effective_value_source_class": "QTT_CONNECTOR_HEALTH_FALLBACK_RULE",
  "evidence_basis_class": "DIRECT_EXTERNAL_PLUS_OWNER_POLICY",
  "evidence_binding_rule_refs": [
    "ST12-SOURCE-RULE::011"
  ],
  "family_evidence_binding_ref": "ST12-FAMILY-EVIDENCE::CN_08A",
  "implementation_resolution_kind": "EXPLICIT_FAIL_CLOSED_POLICY",
  "launch_computability_state": "COMPUTABLE_TYPED_FAIL_CLOSED_OR_NO_TRADE_STATE",
  "master_plan_heading_path": [
    "Part II — Retained institutional design and parameter catalog",
    "D17. Canonical family registry — connectors",
    "CN-08A — Connector rate-limit, pacing, heartbeat-loss, and degraded-mode atomic parameter and control specification"
  ],
  "master_plan_section_id": "CN-08A",
  "missing_stale_invalid_behavior": "PRESERVE_EXPLICIT_FAIL_CLOSED_STATE",
  "parameter_audit_id": "ST11-PARAM::03350",
  "parameter_id": "ST10-PARAM::3350",
  "parameter_symbol": "cn8_fb",
  "precision_and_rounding_policy": {
    "allowlist_check": "REQUIRED",
    "internal_numeric_type": "typed_symbolic",
    "normalization": "CANONICAL_EXACT_TOKEN_NO_FREE_TEXT_COERCION",
    "rounding": "NOT_APPLICABLE"
  },
  "runtime_resolution_procedure": [
    "Materialize the declared fail-closed state exactly.",
    "Return a typed blocker/no-trade status and do not substitute a numeric fallback.",
    "Validate the resolved typed value or token against the effective resolution class, declared structural constraint, and canonical allowlist; on failure apply the declared fail-closed fallback and emit the exact reason code."
  ],
  "source_line_end": 81637,
  "source_line_start": 81623,
  "step12_primary_tranche_id": "ST12-TRANCHE-A"
},
{
  "canonical_owner": "QKUComputationControlPlaneV1",
  "certified_step11_custody_ref": "inputs/certified_step11/QTT_Stage1_Step11_Parameter_Policy_Adjudication_v1_0.jsonl#ST11-PARAM::03381",
  "certified_step11_row_embedded_in_prompt": false,
  "codex_online_research_allowed": false,
  "direct_source_claim_justifications": [],
  "effective_bounded_search_space_or_fit_constraint": "fixed canonical render rule for Day-1; benchmark-relative sleeves may not display only one member of the capture pair",
  "effective_day1_seed_value_or_resolution_rule": "RENDER_UP_AND_DOWN_CAPTURE_TOGETHER_FOR_BENCHMARK_RELATIVE_SLEEVES",
  "effective_default_authority_class": "EXPLICIT_QTT_OR_OWNER_POLICY_SEED_OR_RESOLUTION_RULE",
  "effective_fallback_behavior_when_value_unavailable": "FAIL_CLOSED_TO_REGISTERED_LOWER_SAFE_PATH_OR_NO_TRADE",
  "effective_owner_dashboard_editability_class": "VIEW_ONLY_RESOLVED",
  "effective_policy_authority": "CERTIFIED_STEP11_PARAMETER_POLICY",
  "effective_reference_range_or_structural_constraint": "{RENDER_UP_AND_DOWN_CAPTURE_TOGETHER_FOR_BENCHMARK_RELATIVE_SLEEVES}",
  "effective_resolution_class": "STATIC_ENUM",
  "effective_source_state_refs": [
    "OWNER_POLICY::GV_19A1",
    "SOURCE_PACK::GV_19A1"
  ],
  "effective_ui_widget_class": "READ_ONLY_RULE_CARD",
  "effective_unit_or_basis": "dual-render-state enum",
  "effective_value_source_class": "QTT_CANONICAL_POLICY_RULE",
  "evidence_basis_class": "FAMILY_SOURCE_PACK_PLUS_EXACT_OWNER_APPROVED_VALUE",
  "evidence_binding_rule_refs": [],
  "family_evidence_binding_ref": "ST12-FAMILY-EVIDENCE::GV_19A1",
  "implementation_resolution_kind": "STATIC_OR_DETERMINISTIC_RULE",
  "launch_computability_state": "COMPUTABLE_FROM_STATIC_VALUE_OR_DETERMINISTIC_RULE",
  "master_plan_heading_path": [
    "Part II — Retained institutional design and parameter catalog",
    "D18. Canonical family registry — governance and validation",
    "GV-19A1 — Benchmark-relative allocator-metric atomic parameter pack"
  ],
  "master_plan_section_id": "GV-19A1",
  "missing_stale_invalid_behavior": "REJECT_INVALID_VALUE_NO_SILENT_DEFAULT",
  "parameter_audit_id": "ST11-PARAM::03381",
  "parameter_id": "ST10-PARAM::3381",
  "parameter_symbol": "cap_pair",
  "precision_and_rounding_policy": {
    "allowlist_check": "REQUIRED",
    "internal_numeric_type": "typed_symbolic",
    "normalization": "CANONICAL_EXACT_TOKEN_NO_FREE_TEXT_COERCION",
    "rounding": "NOT_APPLICABLE"
  },
  "runtime_resolution_procedure": [
    "Parse the declared Day-1 seed or deterministic rule into the declared type.",
    "Validate against the reference range and structural constraint.",
    "Apply the declared bounded edit/search law; reject any value outside it."
  ],
  "source_line_end": 82969,
  "source_line_start": 82958,
  "step12_primary_tranche_id": "ST12-TRANCHE-A"
},
{
  "canonical_owner": "QKUComputationControlPlaneV1",
  "certified_step11_custody_ref": "inputs/certified_step11/QTT_Stage1_Step11_Parameter_Policy_Adjudication_v1_0.jsonl#ST11-PARAM::03382",
  "certified_step11_row_embedded_in_prompt": false,
  "codex_online_research_allowed": false,
  "direct_source_claim_justifications": [],
  "effective_bounded_search_space_or_fit_constraint": "the corresponding capture metric may not silently coerce a denominator, impute a substitute denominator, or propagate a numeric score when the denominator guard fires",
  "effective_day1_seed_value_or_resolution_rule": "NOT_MEANINGFUL_ON_DECLARED_BASIS",
  "effective_default_authority_class": "PUBLIC_METHOD_OR_PINNED_PROVIDER_DEFAULT_REQUIRES_IMPLEMENTATION_VERSION_BINDING",
  "effective_fallback_behavior_when_value_unavailable": "FAIL_CLOSED_TO_REGISTERED_LOWER_SAFE_PATH_OR_NO_TRADE",
  "effective_owner_dashboard_editability_class": "VIEW_ONLY_RESOLVED",
  "effective_policy_authority": "CERTIFIED_STEP11_PARAMETER_POLICY",
  "effective_reference_range_or_structural_constraint": "{NOT_MEANINGFUL_ON_DECLARED_BASIS, FAIL_CLOSED_WITH_WARNING_BADGE_AND_NO_SCORE_PROPAGATION}",
  "effective_resolution_class": "STATIC_ENUM",
  "effective_source_state_refs": [
    "OWNER_POLICY::GV_19A1",
    "SOURCE_PACK::GV_19A1"
  ],
  "effective_ui_widget_class": "READ_ONLY_RULE_CARD",
  "effective_unit_or_basis": "denominator-guard enum",
  "effective_value_source_class": "PUBLIC_CAPTURE_RATIO_FORMULA_REFERENCE_PLUS_QTT_FAIL_CLOSED_POLICY",
  "evidence_basis_class": "FAMILY_SOURCE_PACK_PLUS_EXACT_OWNER_APPROVED_VALUE",
  "evidence_binding_rule_refs": [],
  "family_evidence_binding_ref": "ST12-FAMILY-EVIDENCE::GV_19A1",
  "implementation_resolution_kind": "STATIC_OR_DETERMINISTIC_RULE",
  "launch_computability_state": "COMPUTABLE_FROM_STATIC_VALUE_OR_DETERMINISTIC_RULE",
  "master_plan_heading_path": [
    "Part II — Retained institutional design and parameter catalog",
    "D18. Canonical family registry — governance and validation",
    "GV-19A1 — Benchmark-relative allocator-metric atomic parameter pack"
  ],
  "master_plan_section_id": "GV-19A1",
  "missing_stale_invalid_behavior": "REJECT_INVALID_VALUE_NO_SILENT_DEFAULT",
  "parameter_audit_id": "ST11-PARAM::03382",
  "parameter_id": "ST10-PARAM::3382",
  "parameter_symbol": "cap_guard",
  "precision_and_rounding_policy": {
    "allowlist_check": "REQUIRED",
    "internal_numeric_type": "typed_symbolic",
    "normalization": "CANONICAL_EXACT_TOKEN_NO_FREE_TEXT_COERCION",
    "rounding": "NOT_APPLICABLE"
  },
  "runtime_resolution_procedure": [
    "Parse the declared Day-1 seed or deterministic rule into the declared type.",
    "Validate against the reference range and structural constraint.",
    "Apply the declared bounded edit/search law; reject any value outside it."
  ],
  "source_line_end": 82981,
  "source_line_start": 82970,
  "step12_primary_tranche_id": "ST12-TRANCHE-A"
},
{
  "canonical_owner": "QKUComputationControlPlaneV1",
  "certified_step11_custody_ref": "inputs/certified_step11/QTT_Stage1_Step11_Parameter_Policy_Adjudication_v1_0.jsonl#ST11-PARAM::03394",
  "certified_step11_row_embedded_in_prompt": false,
  "codex_online_research_allowed": false,
  "direct_source_claim_justifications": [],
  "effective_bounded_search_space_or_fit_constraint": "fixed Day-1 rule only; any non-since-inception variant must be renamed rather than silently called MAR",
  "effective_day1_seed_value_or_resolution_rule": "SINCE_INCEPTION",
  "effective_default_authority_class": "PUBLIC_METHOD_OR_PINNED_PROVIDER_DEFAULT_REQUIRES_IMPLEMENTATION_VERSION_BINDING",
  "effective_fallback_behavior_when_value_unavailable": "FAIL_CLOSED_TO_REGISTERED_LOWER_SAFE_PATH_OR_NO_TRADE",
  "effective_owner_dashboard_editability_class": "VIEW_ONLY_RESOLVED",
  "effective_policy_authority": "CERTIFIED_STEP11_PARAMETER_POLICY",
  "effective_reference_range_or_structural_constraint": "{SINCE_INCEPTION}",
  "effective_resolution_class": "STATIC_ENUM",
  "effective_source_state_refs": [
    "OWNER_POLICY::GV_19A3",
    "SOURCE_PACK::GV_19A3"
  ],
  "effective_ui_widget_class": "READ_ONLY_RULE_CARD",
  "effective_unit_or_basis": "window-profile enum",
  "effective_value_source_class": "PUBLIC_PERFORMANCE_METRIC_REFERENCE_WITH_QTT_CANONICALIZATION",
  "evidence_basis_class": "FAMILY_SOURCE_PACK_PLUS_EXACT_OWNER_APPROVED_VALUE",
  "evidence_binding_rule_refs": [],
  "family_evidence_binding_ref": "ST12-FAMILY-EVIDENCE::GV_19A3",
  "implementation_resolution_kind": "STATIC_OR_DETERMINISTIC_RULE",
  "launch_computability_state": "COMPUTABLE_FROM_STATIC_VALUE_OR_DETERMINISTIC_RULE",
  "master_plan_heading_path": [
    "Part II — Retained institutional design and parameter catalog",
    "D18. Canonical family registry — governance and validation",
    "GV-19A3 — Advanced companion performance-metric atomic parameter pack and current-version deployment and binding specification"
  ],
  "master_plan_section_id": "GV-19A3",
  "missing_stale_invalid_behavior": "REJECT_INVALID_VALUE_NO_SILENT_DEFAULT",
  "parameter_audit_id": "ST11-PARAM::03394",
  "parameter_id": "ST10-PARAM::3394",
  "parameter_symbol": "mar_win",
  "precision_and_rounding_policy": {
    "allowlist_check": "REQUIRED",
    "internal_numeric_type": "typed_symbolic",
    "normalization": "CANONICAL_EXACT_TOKEN_NO_FREE_TEXT_COERCION",
    "rounding": "NOT_APPLICABLE"
  },
  "runtime_resolution_procedure": [
    "Parse the declared Day-1 seed or deterministic rule into the declared type.",
    "Validate against the reference range and structural constraint.",
    "Apply the declared bounded edit/search law; reject any value outside it."
  ],
  "source_line_end": 83133,
  "source_line_start": 83122,
  "step12_primary_tranche_id": "ST12-TRANCHE-A"
},
{
  "canonical_owner": "QKUComputationControlPlaneV1",
  "certified_step11_custody_ref": "inputs/certified_step11/QTT_Stage1_Step11_Parameter_Policy_Adjudication_v1_0.jsonl#ST11-PARAM::03395",
  "certified_step11_row_embedded_in_prompt": false,
  "codex_online_research_allowed": false,
  "direct_source_claim_justifications": [],
  "effective_bounded_search_space_or_fit_constraint": "fixed Day-1 rule only; a non-annualized numerator may not silently be labeled MAR",
  "effective_day1_seed_value_or_resolution_rule": "ANNUALIZED_RETURN_SINCE_INCEPTION",
  "effective_default_authority_class": "PUBLIC_METHOD_OR_PINNED_PROVIDER_DEFAULT_REQUIRES_IMPLEMENTATION_VERSION_BINDING",
  "effective_fallback_behavior_when_value_unavailable": "FAIL_CLOSED_TO_REGISTERED_LOWER_SAFE_PATH_OR_NO_TRADE",
  "effective_owner_dashboard_editability_class": "VIEW_ONLY_RESOLVED",
  "effective_policy_authority": "CERTIFIED_STEP11_PARAMETER_POLICY",
  "effective_reference_range_or_structural_constraint": "{ANNUALIZED_RETURN_SINCE_INCEPTION}",
  "effective_resolution_class": "STATIC_ENUM",
  "effective_source_state_refs": [
    "OWNER_POLICY::GV_19A3",
    "SOURCE_PACK::GV_19A3"
  ],
  "effective_ui_widget_class": "READ_ONLY_RULE_CARD",
  "effective_unit_or_basis": "MAR-return-basis enum",
  "effective_value_source_class": "PUBLIC_PERFORMANCE_METRIC_REFERENCE_WITH_QTT_CANONICALIZATION",
  "evidence_basis_class": "FAMILY_SOURCE_PACK_PLUS_EXACT_OWNER_APPROVED_VALUE",
  "evidence_binding_rule_refs": [],
  "family_evidence_binding_ref": "ST12-FAMILY-EVIDENCE::GV_19A3",
  "implementation_resolution_kind": "STATIC_OR_DETERMINISTIC_RULE",
  "launch_computability_state": "COMPUTABLE_FROM_STATIC_VALUE_OR_DETERMINISTIC_RULE",
  "master_plan_heading_path": [
    "Part II — Retained institutional design and parameter catalog",
    "D18. Canonical family registry — governance and validation",
    "GV-19A3 — Advanced companion performance-metric atomic parameter pack and current-version deployment and binding specification"
  ],
  "master_plan_section_id": "GV-19A3",
  "missing_stale_invalid_behavior": "REJECT_INVALID_VALUE_NO_SILENT_DEFAULT",
  "parameter_audit_id": "ST11-PARAM::03395",
  "parameter_id": "ST10-PARAM::3395",
  "parameter_symbol": "mar_ret",
  "precision_and_rounding_policy": {
    "allowlist_check": "REQUIRED",
    "internal_numeric_type": "typed_symbolic",
    "normalization": "CANONICAL_EXACT_TOKEN_NO_FREE_TEXT_COERCION",
    "rounding": "NOT_APPLICABLE"
  },
  "runtime_resolution_procedure": [
    "Parse the declared Day-1 seed or deterministic rule into the declared type.",
    "Validate against the reference range and structural constraint.",
    "Apply the declared bounded edit/search law; reject any value outside it."
  ],
  "source_line_end": 83145,
  "source_line_start": 83134,
  "step12_primary_tranche_id": "ST12-TRANCHE-A"
},
{
  "canonical_owner": "QKUComputationControlPlaneV1",
  "certified_step11_custody_ref": "inputs/certified_step11/QTT_Stage1_Step11_Parameter_Policy_Adjudication_v1_0.jsonl#ST11-PARAM::03396",
  "certified_step11_row_embedded_in_prompt": false,
  "codex_online_research_allowed": false,
  "direct_source_claim_justifications": [],
  "effective_bounded_search_space_or_fit_constraint": "fixed Day-1 rule only; MAR may not silently reset its inception clock on trailing windows",
  "effective_day1_seed_value_or_resolution_rule": "FIRST_FULL_OBSERVATION_TO_CURRENT_REVIEW_TIMESTAMP",
  "effective_default_authority_class": "EXPLICIT_QTT_OR_OWNER_POLICY_SEED_OR_RESOLUTION_RULE",
  "effective_fallback_behavior_when_value_unavailable": "FAIL_CLOSED_TO_REGISTERED_LOWER_SAFE_PATH_OR_NO_TRADE",
  "effective_owner_dashboard_editability_class": "VIEW_ONLY_RESOLVED",
  "effective_policy_authority": "CERTIFIED_STEP11_PARAMETER_POLICY",
  "effective_reference_range_or_structural_constraint": "{FIRST_FULL_OBSERVATION_TO_CURRENT_REVIEW_TIMESTAMP}",
  "effective_resolution_class": "STATIC_ENUM",
  "effective_source_state_refs": [
    "OWNER_POLICY::GV_19A3",
    "SOURCE_PACK::GV_19A3"
  ],
  "effective_ui_widget_class": "READ_ONLY_RULE_CARD",
  "effective_unit_or_basis": "since-inception-clock enum",
  "effective_value_source_class": "QTT_CANONICAL_POLICY_RULE",
  "evidence_basis_class": "FAMILY_SOURCE_PACK_PLUS_EXACT_OWNER_APPROVED_VALUE",
  "evidence_binding_rule_refs": [],
  "family_evidence_binding_ref": "ST12-FAMILY-EVIDENCE::GV_19A3",
  "implementation_resolution_kind": "STATIC_OR_DETERMINISTIC_RULE",
  "launch_computability_state": "COMPUTABLE_FROM_STATIC_VALUE_OR_DETERMINISTIC_RULE",
  "master_plan_heading_path": [
    "Part II — Retained institutional design and parameter catalog",
    "D18. Canonical family registry — governance and validation",
    "GV-19A3 — Advanced companion performance-metric atomic parameter pack and current-version deployment and binding specification"
  ],
  "master_plan_section_id": "GV-19A3",
  "missing_stale_invalid_behavior": "REJECT_INVALID_VALUE_NO_SILENT_DEFAULT",
  "parameter_audit_id": "ST11-PARAM::03396",
  "parameter_id": "ST10-PARAM::3396",
  "parameter_symbol": "mar_clock",
  "precision_and_rounding_policy": {
    "allowlist_check": "REQUIRED",
    "internal_numeric_type": "typed_symbolic",
    "normalization": "CANONICAL_EXACT_TOKEN_NO_FREE_TEXT_COERCION",
    "rounding": "NOT_APPLICABLE"
  },
  "runtime_resolution_procedure": [
    "Parse the declared Day-1 seed or deterministic rule into the declared type.",
    "Validate against the reference range and structural constraint.",
    "Apply the declared bounded edit/search law; reject any value outside it."
  ],
  "source_line_end": 83157,
  "source_line_start": 83146,
  "step12_primary_tranche_id": "ST12-TRANCHE-A"
},
{
  "canonical_owner": "QKUComputationControlPlaneV1",
  "certified_step11_custody_ref": "inputs/certified_step11/QTT_Stage1_Step11_Parameter_Policy_Adjudication_v1_0.jsonl#ST11-PARAM::03407",
  "certified_step11_row_embedded_in_prompt": false,
  "codex_online_research_allowed": false,
  "direct_source_claim_justifications": [],
  "effective_bounded_search_space_or_fit_constraint": "fixed canonical storage seed `1000.0` for Day-1 comparability",
  "effective_day1_seed_value_or_resolution_rule": "1000.0",
  "effective_default_authority_class": "PUBLIC_METHOD_OR_PINNED_PROVIDER_DEFAULT_REQUIRES_IMPLEMENTATION_VERSION_BINDING",
  "effective_fallback_behavior_when_value_unavailable": "FAIL_CLOSED_TO_REGISTERED_LOWER_SAFE_PATH_OR_NO_TRADE",
  "effective_owner_dashboard_editability_class": "VIEW_ONLY_RESOLVED",
  "effective_policy_authority": "CERTIFIED_STEP11_PARAMETER_POLICY",
  "effective_reference_range_or_structural_constraint": "positive base notional with canonical public VAMI seed `1000.0`; display-normalized alternatives remain derived views only",
  "effective_resolution_class": "STATIC_NUMERIC",
  "effective_source_state_refs": [
    "OWNER_POLICY::GV_19A3",
    "SOURCE_PACK::GV_19A3"
  ],
  "effective_ui_widget_class": "READ_ONLY_RULE_CARD",
  "effective_unit_or_basis": "account-currency notional seed",
  "effective_value_source_class": "PUBLIC_K_RATIO_REFERENCE_WITH_QTT_CANONICALIZATION",
  "evidence_basis_class": "FAMILY_SOURCE_PACK_PLUS_EXACT_OWNER_APPROVED_VALUE",
  "evidence_binding_rule_refs": [],
  "family_evidence_binding_ref": "ST12-FAMILY-EVIDENCE::GV_19A3",
  "implementation_resolution_kind": "STATIC_OR_DETERMINISTIC_RULE",
  "launch_computability_state": "COMPUTABLE_FROM_STATIC_VALUE_OR_DETERMINISTIC_RULE",
  "master_plan_heading_path": [
    "Part II — Retained institutional design and parameter catalog",
    "D18. Canonical family registry — governance and validation",
    "GV-19A3 — Advanced companion performance-metric atomic parameter pack and current-version deployment and binding specification"
  ],
  "master_plan_section_id": "GV-19A3",
  "missing_stale_invalid_behavior": "REJECT_INVALID_VALUE_NO_SILENT_DEFAULT",
  "parameter_audit_id": "ST11-PARAM::03407",
  "parameter_id": "ST10-PARAM::3407",
  "parameter_symbol": "vami_0",
  "precision_and_rounding_policy": {
    "allowlist_check": "REQUIRED",
    "internal_numeric_type": "typed_symbolic",
    "normalization": "CANONICAL_EXACT_TOKEN_NO_FREE_TEXT_COERCION",
    "rounding": "NOT_APPLICABLE"
  },
  "runtime_resolution_procedure": [
    "Parse the declared Day-1 seed or deterministic rule into the declared type.",
    "Validate against the reference range and structural constraint.",
    "Apply the declared bounded edit/search law; reject any value outside it."
  ],
  "source_line_end": 83289,
  "source_line_start": 83278,
  "step12_primary_tranche_id": "ST12-TRANCHE-A"
},
{
  "canonical_owner": "QKUComputationControlPlaneV1",
  "certified_step11_custody_ref": "inputs/certified_step11/QTT_Stage1_Step11_Parameter_Policy_Adjudication_v1_0.jsonl#ST11-PARAM::03420",
  "certified_step11_row_embedded_in_prompt": false,
  "codex_online_research_allowed": false,
  "direct_source_claim_justifications": [],
  "effective_bounded_search_space_or_fit_constraint": "the current underwater-time state may not silently average completed episodes or silently substitute peak-to-recovery duration",
  "effective_day1_seed_value_or_resolution_rule": "CURRENT_UNDERWATER_EPISODE_DURATION_ON_DECLARED_CLOCK_ELSE_ZERO_IF_AT_NEW_HIGH",
  "effective_default_authority_class": "PUBLIC_METHOD_OR_PINNED_PROVIDER_DEFAULT_REQUIRES_IMPLEMENTATION_VERSION_BINDING",
  "effective_fallback_behavior_when_value_unavailable": "FAIL_CLOSED_TO_REGISTERED_LOWER_SAFE_PATH_OR_NO_TRADE",
  "effective_owner_dashboard_editability_class": "VIEW_ONLY_RESOLVED",
  "effective_policy_authority": "CERTIFIED_STEP11_PARAMETER_POLICY",
  "effective_reference_range_or_structural_constraint": "{CURRENT_UNDERWATER_EPISODE_DURATION_ON_DECLARED_CLOCK_ELSE_ZERO_IF_AT_NEW_HIGH, NOT_MEANINGFUL_OUTSIDE_CURRENT_UNDERWATER_STATE}",
  "effective_resolution_class": "STATIC_ENUM",
  "effective_source_state_refs": [
    "OWNER_POLICY::GV_19A3",
    "SOURCE_PACK::GV_19A3"
  ],
  "effective_ui_widget_class": "READ_ONLY_RULE_CARD",
  "effective_unit_or_basis": "current-time-under-water state enum",
  "effective_value_source_class": "PUBLIC_DRAWDOWN_DURATION_REFERENCE_WITH_QTT_CANONICALIZATION",
  "evidence_basis_class": "FAMILY_SOURCE_PACK_PLUS_EXACT_OWNER_APPROVED_VALUE",
  "evidence_binding_rule_refs": [],
  "family_evidence_binding_ref": "ST12-FAMILY-EVIDENCE::GV_19A3",
  "implementation_resolution_kind": "STATIC_OR_DETERMINISTIC_RULE",
  "launch_computability_state": "COMPUTABLE_FROM_STATIC_VALUE_OR_DETERMINISTIC_RULE",
  "master_plan_heading_path": [
    "Part II — Retained institutional design and parameter catalog",
    "D18. Canonical family registry — governance and validation",
    "GV-19A3 — Advanced companion performance-metric atomic parameter pack and current-version deployment and binding specification"
  ],
  "master_plan_section_id": "GV-19A3",
  "missing_stale_invalid_behavior": "REJECT_INVALID_VALUE_NO_SILENT_DEFAULT",
  "parameter_audit_id": "ST11-PARAM::03420",
  "parameter_id": "ST10-PARAM::3420",
  "parameter_symbol": "ctuw_state",
  "precision_and_rounding_policy": {
    "allowlist_check": "REQUIRED",
    "internal_numeric_type": "typed_symbolic",
    "normalization": "CANONICAL_EXACT_TOKEN_NO_FREE_TEXT_COERCION",
    "rounding": "NOT_APPLICABLE"
  },
  "runtime_resolution_procedure": [
    "Parse the declared Day-1 seed or deterministic rule into the declared type.",
    "Validate against the reference range and structural constraint.",
    "Apply the declared bounded edit/search law; reject any value outside it."
  ],
  "source_line_end": 83445,
  "source_line_start": 83434,
  "step12_primary_tranche_id": "ST12-TRANCHE-A"
},
{
  "canonical_owner": "QKUComputationControlPlaneV1",
  "certified_step11_custody_ref": "inputs/certified_step11/QTT_Stage1_Step11_Parameter_Policy_Adjudication_v1_0.jsonl#ST11-PARAM::03422",
  "certified_step11_row_embedded_in_prompt": false,
  "codex_online_research_allowed": false,
  "direct_source_claim_justifications": [],
  "effective_bounded_search_space_or_fit_constraint": "fixed canonical rule for Day-1; underwater-depth views may not render without a typed receipt on the declared review window",
  "effective_day1_seed_value_or_resolution_rule": "REQUIRED_TYPED_DEPTH_SERIES_RECEIPT_ON_DECLARED_DRAWDOWN_WINDOW",
  "effective_default_authority_class": "EXPLICIT_QTT_OR_OWNER_POLICY_SEED_OR_RESOLUTION_RULE",
  "effective_fallback_behavior_when_value_unavailable": "FAIL_CLOSED_TO_REGISTERED_LOWER_SAFE_PATH_OR_NO_TRADE",
  "effective_owner_dashboard_editability_class": "VIEW_ONLY_RESOLVED",
  "effective_policy_authority": "CERTIFIED_STEP11_PARAMETER_POLICY",
  "effective_reference_range_or_structural_constraint": "{REQUIRED_TYPED_DEPTH_SERIES_RECEIPT_ON_DECLARED_DRAWDOWN_WINDOW}",
  "effective_resolution_class": "STATIC_ENUM",
  "effective_source_state_refs": [
    "OWNER_POLICY::GV_19A3",
    "SOURCE_PACK::GV_19A3"
  ],
  "effective_ui_widget_class": "READ_ONLY_RULE_CARD",
  "effective_unit_or_basis": "underwater-depth-receipt-requirement enum",
  "effective_value_source_class": "QTT_CANONICAL_POLICY_RULE",
  "evidence_basis_class": "FAMILY_SOURCE_PACK_PLUS_EXACT_OWNER_APPROVED_VALUE",
  "evidence_binding_rule_refs": [],
  "family_evidence_binding_ref": "ST12-FAMILY-EVIDENCE::GV_19A3",
  "implementation_resolution_kind": "STATIC_OR_DETERMINISTIC_RULE",
  "launch_computability_state": "COMPUTABLE_FROM_STATIC_VALUE_OR_DETERMINISTIC_RULE",
  "master_plan_heading_path": [
    "Part II — Retained institutional design and parameter catalog",
    "D18. Canonical family registry — governance and validation",
    "GV-19A3 — Advanced companion performance-metric atomic parameter pack and current-version deployment and binding specification"
  ],
  "master_plan_section_id": "GV-19A3",
  "missing_stale_invalid_behavior": "REJECT_INVALID_VALUE_NO_SILENT_DEFAULT",
  "parameter_audit_id": "ST11-PARAM::03422",
  "parameter_id": "ST10-PARAM::3422",
  "parameter_symbol": "uw_depth_rcpt",
  "precision_and_rounding_policy": {
    "allowlist_check": "REQUIRED",
    "internal_numeric_type": "typed_symbolic",
    "normalization": "CANONICAL_EXACT_TOKEN_NO_FREE_TEXT_COERCION",
    "rounding": "NOT_APPLICABLE"
  },
  "runtime_resolution_procedure": [
    "Parse the declared Day-1 seed or deterministic rule into the declared type.",
    "Validate against the reference range and structural constraint.",
    "Apply the declared bounded edit/search law; reject any value outside it."
  ],
  "source_line_end": 83470,
  "source_line_start": 83458,
  "step12_primary_tranche_id": "ST12-TRANCHE-A"
},
{
  "canonical_owner": "QKUComputationControlPlaneV1",
  "certified_step11_custody_ref": "inputs/certified_step11/QTT_Stage1_Step11_Parameter_Policy_Adjudication_v1_0.jsonl#ST11-PARAM::03435",
  "certified_step11_row_embedded_in_prompt": false,
  "codex_online_research_allowed": false,
  "direct_source_claim_justifications": [],
  "effective_bounded_search_space_or_fit_constraint": "rendering only; raw observation count always preserved internally",
  "effective_day1_seed_value_or_resolution_rule": "RAW_OBSERVATION_COUNT",
  "effective_default_authority_class": "EXPLICIT_QTT_OR_OWNER_POLICY_SEED_OR_RESOLUTION_RULE",
  "effective_fallback_behavior_when_value_unavailable": "FAIL_CLOSED_TO_REGISTERED_LOWER_SAFE_PATH_OR_NO_TRADE",
  "effective_owner_dashboard_editability_class": "EDITABLE_WITH_SHADOW",
  "effective_policy_authority": "CERTIFIED_STEP11_PARAMETER_POLICY",
  "effective_reference_range_or_structural_constraint": "{RAW_OBSERVATION_COUNT,TRADING_DAYS_EQUIVALENT,MONTHS_EQUIVALENT,YEARS_EQUIVALENT}",
  "effective_resolution_class": "STATIC_ENUM",
  "effective_source_state_refs": [
    "OWNER_POLICY::GV_19D1A",
    "SOURCE_PACK::GV_19D1A"
  ],
  "effective_ui_widget_class": "ENUM_DROPDOWN",
  "effective_unit_or_basis": "observation-unit render enum",
  "effective_value_source_class": "QTT_INTERNAL_VALIDATED_DEFAULT",
  "evidence_basis_class": "FAMILY_SOURCE_PACK_PLUS_EXACT_OWNER_APPROVED_VALUE",
  "evidence_binding_rule_refs": [],
  "family_evidence_binding_ref": "ST12-FAMILY-EVIDENCE::GV_19D1A",
  "implementation_resolution_kind": "STATIC_OR_DETERMINISTIC_RULE",
  "launch_computability_state": "COMPUTABLE_FROM_STATIC_VALUE_OR_DETERMINISTIC_RULE",
  "master_plan_heading_path": [
    "Part II — Retained institutional design and parameter catalog",
    "D18. Canonical family registry — governance and validation",
    "GV-19D1A — Minimum Track Record Length atomic parameter pack"
  ],
  "master_plan_section_id": "GV-19D1A",
  "missing_stale_invalid_behavior": "REJECT_INVALID_VALUE_NO_SILENT_DEFAULT",
  "parameter_audit_id": "ST11-PARAM::03435",
  "parameter_id": "ST10-PARAM::3435",
  "parameter_symbol": "mintrl_unit",
  "precision_and_rounding_policy": {
    "allowlist_check": "REQUIRED",
    "internal_numeric_type": "typed_symbolic",
    "normalization": "CANONICAL_EXACT_TOKEN_NO_FREE_TEXT_COERCION",
    "rounding": "NOT_APPLICABLE"
  },
  "runtime_resolution_procedure": [
    "Parse the declared Day-1 seed or deterministic rule into the declared type.",
    "Validate against the reference range and structural constraint.",
    "Apply the declared bounded edit/search law; reject any value outside it."
  ],
  "source_line_end": 83780,
  "source_line_start": 83769,
  "step12_primary_tranche_id": "ST12-TRANCHE-A"
}
]
'''


def _record(row: object) -> ParameterPolicyRecordV1:
    if not isinstance(row, dict):
        raise ParameterPolicyError(
            ReasonCode.PARAMETER_OUT_OF_POLICY, "parameter row must be an object"
        )
    justifications = tuple(
        SourceClaimJustificationV1(
            binding_rule_ref=str(item["binding_rule_ref"]),
            claim_selector=str(item["claim_selector"]),
            exact_parameter_scope=tuple(str(v) for v in item["exact_parameter_scope"]),
            justification=str(item["justification"]),
            source_identity_ref=str(item["source_identity_ref"]),
        )
        for item in row["direct_source_claim_justifications"]
    )
    precision = row["precision_and_rounding_policy"]
    if not isinstance(precision, dict):
        raise ParameterPolicyError(
            ReasonCode.PARAMETER_OUT_OF_POLICY,
            "precision policy must be a typed object",
        )
    for field_name in (
        "certified_step11_row_embedded_in_prompt",
        "codex_online_research_allowed",
    ):
        if type(row[field_name]) is not bool:
            raise ParameterPolicyError(
                ReasonCode.PARAMETER_OUT_OF_POLICY,
                f"{field_name} must be a boolean",
            )
    return ParameterPolicyRecordV1(
        canonical_owner=str(row["canonical_owner"]),
        certified_step11_custody_ref=str(row["certified_step11_custody_ref"]),
        certified_step11_row_embedded_in_prompt=row[
            "certified_step11_row_embedded_in_prompt"
        ],
        codex_online_research_allowed=row["codex_online_research_allowed"],
        direct_source_claim_justifications=justifications,
        effective_bounded_search_space_or_fit_constraint=str(
            row["effective_bounded_search_space_or_fit_constraint"]
        ),
        effective_day1_seed_value_or_resolution_rule=str(
            row["effective_day1_seed_value_or_resolution_rule"]
        ),
        effective_default_authority_class=str(
            row["effective_default_authority_class"]
        ),
        effective_fallback_behavior_when_value_unavailable=str(
            row["effective_fallback_behavior_when_value_unavailable"]
        ),
        effective_owner_dashboard_editability_class=str(
            row["effective_owner_dashboard_editability_class"]
        ),
        effective_policy_authority=str(row["effective_policy_authority"]),
        effective_reference_range_or_structural_constraint=str(
            row["effective_reference_range_or_structural_constraint"]
        ),
        effective_resolution_class=str(row["effective_resolution_class"]),
        effective_source_state_refs=tuple(
            str(value) for value in row["effective_source_state_refs"]
        ),
        effective_ui_widget_class=str(row["effective_ui_widget_class"]),
        effective_unit_or_basis=str(row["effective_unit_or_basis"]),
        effective_value_source_class=str(row["effective_value_source_class"]),
        evidence_basis_class=str(row["evidence_basis_class"]),
        evidence_binding_rule_refs=tuple(
            str(value) for value in row["evidence_binding_rule_refs"]
        ),
        family_evidence_binding_ref=str(row["family_evidence_binding_ref"]),
        implementation_resolution_kind=str(row["implementation_resolution_kind"]),
        launch_computability_state=str(row["launch_computability_state"]),
        master_plan_heading_path=tuple(
            str(value) for value in row["master_plan_heading_path"]
        ),
        master_plan_section_id=str(row["master_plan_section_id"]),
        missing_stale_invalid_behavior=str(row["missing_stale_invalid_behavior"]),
        parameter_audit_id=str(row["parameter_audit_id"]),
        parameter_id=str(row["parameter_id"]),
        parameter_symbol=str(row["parameter_symbol"]),
        precision_and_rounding_policy=tuple(
            sorted((str(key), str(value)) for key, value in precision.items())
        ),
        runtime_resolution_procedure=tuple(
            str(value) for value in row["runtime_resolution_procedure"]
        ),
        source_line_end=int(row["source_line_end"]),
        source_line_start=int(row["source_line_start"]),
        step12_primary_tranche_id=str(row["step12_primary_tranche_id"]),
        original_row_json=json.dumps(
            row,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ),
    )


def _load_rows() -> tuple[ParameterPolicyRecordV1, ...]:
    rows = json.loads(_PARAMETER_ROWS_JSON)
    if not isinstance(rows, list):
        raise ParameterPolicyError(
            ReasonCode.PARAMETER_OUT_OF_POLICY,
            "parameter policy materialization must be a list",
        )
    records = tuple(_record(row) for row in rows)
    if len(records) != 135:
        raise ParameterPolicyError(
            ReasonCode.PARAMETER_OUT_OF_POLICY,
            f"expected 135 parameter rows, found {len(records)}",
        )
    if len({record.parameter_id for record in records}) != 135:
        raise ParameterPolicyError(
            ReasonCode.PARAMETER_OUT_OF_POLICY, "parameter ids are not unique"
        )
    if len({record.parameter_audit_id for record in records}) != 135:
        raise ParameterPolicyError(
            ReasonCode.PARAMETER_OUT_OF_POLICY,
            "parameter audit ids are not unique",
        )
    return records


PARAMETER_POLICIES = _load_rows()
PARAMETER_POLICY_BY_ID: Mapping[str, ParameterPolicyRecordV1] = MappingProxyType(
    {
        identifier: record
        for record in PARAMETER_POLICIES
        for identifier in (record.parameter_id, record.parameter_audit_id)
    }
)


def get_parameter_policy(parameter_id: str) -> ParameterPolicyRecordV1:
    if not isinstance(parameter_id, str) or not parameter_id:
        raise ParameterPolicyError(
            ReasonCode.PARAMETER_UNKNOWN,
            "parameter identity must be nonempty text",
        )
    try:
        return PARAMETER_POLICY_BY_ID[parameter_id]
    except KeyError as exc:
        raise ParameterPolicyError(
            ReasonCode.PARAMETER_UNKNOWN, f"unknown parameter: {parameter_id}"
        ) from exc


def _simple_enum_values(constraint: str) -> frozenset[str]:
    stripped = constraint.strip()
    if (
        not stripped.startswith("{")
        or not stripped.endswith("}")
        or any(token in stripped for token in ("->", ":", "[", "]", "(", ")"))
    ):
        return frozenset()
    return frozenset(
        value.strip() for value in stripped[1:-1].split(",") if value.strip()
    )


_EDITABLE_CLASSES = frozenset(
    {"EDITABLE_WITH_SHADOW", "CONDITIONALLY_EDITABLE_WITH_SHADOW"}
)
_INTEGER_RANGE = re.compile(r"`?(-?\d+)\.\.(-?\d+)`?")


def _numeric_grid_values(text: str) -> frozenset[Decimal]:
    start = text.find("{")
    end = text.find("}", start + 1)
    if start < 0 or end < 0:
        return frozenset()
    values: set[Decimal] = set()
    for token in text[start + 1 : end].split(","):
        try:
            values.add(exact_decimal(token.strip(), field_name="numeric_grid"))
        except NumericDomainError:
            return frozenset()
    return frozenset(values)


def _validate_numeric_override(
    policy: ParameterPolicyRecordV1,
    candidate: str | int | Decimal,
) -> str:
    try:
        numeric = exact_decimal(candidate, field_name=policy.parameter_id)
    except NumericDomainError as exc:
        raise ParameterPolicyError(
            ReasonCode.PARAMETER_OUT_OF_POLICY,
            f"{policy.parameter_id} requires an exact numeric value",
        ) from exc
    resolution = policy.effective_resolution_class
    constraint = policy.effective_reference_range_or_structural_constraint
    if "INTEGER" in resolution and numeric != numeric.to_integral_value():
        raise ParameterPolicyError(
            ReasonCode.PARAMETER_OUT_OF_POLICY,
            f"{policy.parameter_id} requires an integer",
        )
    if "positive" in constraint.casefold() and numeric <= 0:
        raise ParameterPolicyError(
            ReasonCode.PARAMETER_OUT_OF_POLICY,
            f"{policy.parameter_id} requires a positive value",
        )
    integer_range = _INTEGER_RANGE.search(constraint)
    if integer_range and not (
        Decimal(integer_range.group(1))
        <= numeric
        <= Decimal(integer_range.group(2))
    ):
        raise ParameterPolicyError(
            ReasonCode.PARAMETER_OUT_OF_POLICY,
            f"{policy.parameter_id} is outside its integer range",
        )
    grid = _numeric_grid_values(
        policy.effective_bounded_search_space_or_fit_constraint
    )
    if grid and numeric not in grid:
        raise ParameterPolicyError(
            ReasonCode.PARAMETER_OUT_OF_POLICY,
            f"{policy.parameter_id} is outside its exact numeric grid",
        )
    return str(candidate)


class ParameterPolicyResolverV1:
    @staticmethod
    def resolve(
        parameter_id: str,
        *,
        candidate: str | int | Decimal | None = None,
    ) -> ResolvedParameterV1:
        policy = get_parameter_policy(parameter_id)
        seed = policy.effective_day1_seed_value_or_resolution_rule
        if candidate is None:
            value = seed
            used_seed = True
        else:
            editability = policy.effective_owner_dashboard_editability_class
            if editability not in _EDITABLE_CLASSES:
                raise ParameterPolicyError(
                    ReasonCode.PARAMETER_NOT_EDITABLE,
                    f"{policy.parameter_id} is {editability}",
                )
            value = str(candidate)
            used_seed = value == seed
            allowed = _simple_enum_values(
                policy.effective_reference_range_or_structural_constraint
            )
            if allowed and value not in allowed:
                raise ParameterPolicyError(
                    ReasonCode.PARAMETER_OUT_OF_POLICY,
                    f"{value!r} is outside {policy.parameter_id}'s enum",
                )
            if (
                not allowed
                and any(
                    token in policy.effective_resolution_class
                    for token in ("INTEGER", "NUMERIC")
                )
            ):
                value = _validate_numeric_override(policy, candidate)
            elif not allowed and value != seed:
                raise ParameterPolicyError(
                    ReasonCode.PARAMETER_OUT_OF_POLICY,
                    "complex policy overrides require a later typed owner contract",
                )
        return ResolvedParameterV1(
            parameter_id=policy.parameter_id,
            parameter_audit_id=policy.parameter_audit_id,
            parameter_symbol=policy.parameter_symbol,
            value=value,
            unit_or_basis=policy.effective_unit_or_basis,
            resolution_class=policy.effective_resolution_class,
            authority_class=policy.effective_default_authority_class,
            fallback=policy.effective_fallback_behavior_when_value_unavailable,
            owner_editability=policy.effective_owner_dashboard_editability_class,
            used_day1_seed=used_seed,
        )
