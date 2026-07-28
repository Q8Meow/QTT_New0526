"""Read-only PR162E-Q semantic views; no backend or simulator execution."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
import json
from pathlib import Path
from types import MappingProxyType
from typing import Mapping

from .errors import OwnerAdapterError, ReasonCode


class QuantumModelKind(StrEnum):
    QUBO = "QUBO"
    BQM = "BQM"
    ISING = "ISING"
    CQM = "CQM"
    DQM = "DQM"
    QUADRATIC_PROGRAM = "QUADRATIC_PROGRAM"


@dataclass(frozen=True, slots=True)
class QuantumMappingViewV1:
    row_id: str
    model_kind: QuantumModelKind
    source_report: str
    source_schema: str
    source_owner: str = "PR162E_Q_QUANTUM_AUTOMAPPER"
    backend_execution_allowed: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.model_kind, QuantumModelKind):
            raise OwnerAdapterError(
                ReasonCode.OWNER_DATA_MALFORMED,
                "quantum model kind must be a typed allowlisted enum",
            )
        if any(
            not isinstance(value, str) or not value
            for value in (
                self.row_id,
                self.source_report,
                self.source_schema,
                self.source_owner,
            )
        ):
            raise OwnerAdapterError(
                ReasonCode.OWNER_DATA_MALFORMED,
                "quantum mapping lineage is incomplete",
            )
        if self.source_owner != "PR162E_Q_QUANTUM_AUTOMAPPER":
            raise OwnerAdapterError(
                ReasonCode.OWNER_DATA_CONTRADICTORY,
                "quantum mapping owner lineage changed",
            )
        if type(self.backend_execution_allowed) is not bool:
            raise OwnerAdapterError(
                ReasonCode.OWNER_DATA_MALFORMED,
                "backend execution flag must be a boolean",
            )
        if self.backend_execution_allowed:
            raise OwnerAdapterError(
                ReasonCode.CAPABILITY_DENIED,
                "Tranche A quantum views cannot authorize backend execution",
            )
        from .serialization import validate_relative_path

        validate_relative_path(self.source_report)


_REPORTS = {
    QuantumModelKind.QUBO: "PR162E_Q_QUBORecipe.report.json",
    QuantumModelKind.BQM: "PR162E_Q_BQMRecipe.report.json",
    QuantumModelKind.ISING: "PR162E_Q_IsingRecipe.report.json",
    QuantumModelKind.CQM: "PR162E_Q_CQMRecipe.report.json",
    QuantumModelKind.DQM: "PR162E_Q_DQMRecipe.report.json",
    QuantumModelKind.QUADRATIC_PROGRAM: (
        "PR162E_Q_QuadProgramRecipe.report.json"
    ),
}


class PR162EQuantumAdapterV1:
    def __init__(self, repo_root: str | Path) -> None:
        self._repo_root = Path(repo_root).resolve()

    def load_mappings(
        self, model_kind: QuantumModelKind
    ) -> tuple[QuantumMappingViewV1, ...]:
        from src.qtt.stage1_prediction_markets.pr162e_q_quantum_automapper.io import (
            records_from_report_payload,
        )

        if not isinstance(model_kind, QuantumModelKind):
            raise OwnerAdapterError(
                ReasonCode.OWNER_DATA_MALFORMED,
                "model_kind must be a QuantumModelKind value",
            )
        filename = _REPORTS[model_kind]
        relative = Path("docs/master_plan/generated") / filename
        try:
            payload = json.loads(
                (self._repo_root / relative).read_text(encoding="utf-8")
            )
        except (OSError, json.JSONDecodeError) as exc:
            raise OwnerAdapterError(
                ReasonCode.OWNER_DATA_MISSING,
                f"PR162E-Q report unavailable: {filename}",
            ) from exc
        if not isinstance(payload, dict):
            raise OwnerAdapterError(
                ReasonCode.OWNER_DATA_MALFORMED,
                f"PR162E-Q report must be an object: {filename}",
            )
        if payload.get("validation_status") != "PASS":
            raise OwnerAdapterError(
                ReasonCode.OWNER_DATA_STALE,
                f"PR162E-Q report is not validated: {filename}",
            )
        forbidden_counts = (
            "cloud_backend_execution_count",
            "credential_access_count",
            "live_order_authority_count",
            "private_state_fetch_count",
            "provider_api_call_count",
            "quantum_backend_execution_count",
        )
        if any(payload.get(key) != 0 for key in forbidden_counts):
            raise OwnerAdapterError(
                ReasonCode.OWNER_DATA_CONTRADICTORY,
                "PR162E-Q mapping reports exercise forbidden authority",
            )
        try:
            records = records_from_report_payload(self._repo_root, payload)
        except (OSError, KeyError, TypeError, ValueError) as exc:
            raise OwnerAdapterError(
                ReasonCode.OWNER_DATA_MALFORMED,
                f"PR162E-Q records could not be resolved: {filename}",
            ) from exc
        schema = payload.get("schema_ref")
        if not isinstance(schema, str) or not schema:
            raise OwnerAdapterError(
                ReasonCode.OWNER_DATA_MALFORMED,
                f"PR162E-Q schema lineage is missing: {filename}",
            )
        if any(not isinstance(record, dict) for record in records):
            raise OwnerAdapterError(
                ReasonCode.OWNER_DATA_MALFORMED,
                "PR162E-Q record set contains a non-object row",
            )
        views: list[QuantumMappingViewV1] = []
        for record in records:
            row_id = next(
                (
                    record[field_name]
                    for field_name in ("row_id", "mapping_id", "recipe_id")
                    if isinstance(record.get(field_name), str)
                    and record[field_name]
                ),
                "",
            )
            views.append(
                QuantumMappingViewV1(
                    row_id=row_id,
                    model_kind=model_kind,
                    source_report=relative.as_posix(),
                    source_schema=schema,
                )
            )
        if not views or len({view.row_id for view in views}) != len(views):
            raise OwnerAdapterError(
                ReasonCode.OWNER_DATA_CONTRADICTORY,
                "PR162E-Q mapping identities must be nonempty and unique",
            )
        return tuple(sorted(views, key=lambda item: item.row_id))

    def structural_readiness_requirements(
        self,
        model_kind: QuantumModelKind,
    ) -> tuple["QuantumStructuralReadinessProjectionV1", ...]:
        """Project exact Tranche-B closure requirements without backend work."""

        mappings = self.load_mappings(model_kind)
        mapping_refs = tuple(view.row_id for view in mappings)
        math_refs = _MATH_REFS_BY_MODEL[model_kind]
        oracle_refs = tuple(f"ORACLE::{math_id}" for math_id in math_refs)
        return tuple(
            QuantumStructuralReadinessProjectionV1(
                projection_id=(
                    f"ST12B-QUANTUM-STRUCTURAL::{model_kind.value}::"
                    f"{closure_id.rsplit('::', 1)[-1]}"
                ),
                closure_id=closure_id,
                control_slug=control_slug,
                model_kind=model_kind,
                mapping_owner="PR162E_Q_QUANTUM_AUTOMAPPER",
                mapping_refs=mapping_refs,
                source_schema=mappings[0].source_schema,
                original_formulation_refs=math_refs,
                objective_sense="EXACT_ORIGINAL_DECLARED_OBJECTIVE_SENSE_REQUIRED",
                economic_scale=(
                    "ORIGINAL_OBJECTIVE_SCALING_RECEIPT_AND_ECONOMIC_UNIT_REQUIRED"
                ),
                variable_domains="EXACT_ORIGINAL_VARIABLE_DOMAINS_REQUIRED",
                hard_constraints=(
                    "ALL_ORIGINAL_HARD_CONSTRAINTS_PRESERVED_AND_REVALIDATED"
                ),
                soft_preferences=(
                    "EXPLICITLY_SEPARATED_FROM_HARD_CONSTRAINTS"
                ),
                mapping_family=model_kind.value,
                converter_version=(
                    f"PR162E-Q::{mappings[0].source_schema}"
                ),
                coefficient_scale_dynamic_range=(
                    "TYPED_INSTANCE_SCALE_AND_DYNAMIC_RANGE_EVIDENCE_REQUIRED"
                ),
                penalty_adequacy=(
                    "NO_UNIVERSAL_PENALTY;"
                    "INSTANCE_SPECIFIC_DOMINANCE_EVIDENCE_REQUIRED"
                ),
                inverse_mapping=(
                    "TYPED_INVERSE_MAPPING_TO_ORIGINAL_VARIABLES_REQUIRED"
                ),
                economic_interpret_back=(
                    "ORIGINAL_UNITS_CANDIDATE_ID_AND_ECONOMIC_OUTPUT_REQUIRED"
                ),
                original_model_feasibility=(
                    "INDEPENDENT_POST_INTERPRET_BACK_REVALIDATION_REQUIRED"
                ),
                independent_small_instance_oracle_refs=oracle_refs,
                classical_fallback=(
                    "DETERMINISTIC_SAME_FORMULATION_CLASSICAL_FALLBACK"
                ),
                no_trade_fallback="NO_TRADE",
                maturity_state=(
                    "STRUCTURAL_REQUIREMENTS_ONLY_NO_SIMULATOR_QPU_OR_ADVANTAGE_EVIDENCE"
                ),
                latency_ttl_compatibility=(
                    "TYPED_CONTEXT_LATENCY_AND_TTL_EVIDENCE_REQUIRED"
                ),
                blocker_codes=(
                    "ORIGINAL_FORMULATION_INSTANCE_EVIDENCE_REQUIRED",
                ),
                terminal_route=(
                    "quantum_optimizer_agent::"
                    "STRUCTURAL_EVIDENCE_OR_CLASSICAL_NO_TRADE"
                ),
            )
            for closure_id, control_slug in _QUANTUM_CLOSURE_ROWS
        )


_QUANTUM_CLOSURE_ROWS = (
    ("ST12-CLOSURE::ST11-QUANTUM::007", "penalty-adequacy"),
    ("ST12-CLOSURE::ST11-QUANTUM::008", "converter-compatibility"),
    ("ST12-CLOSURE::ST11-QUANTUM::009", "interpret-back"),
    ("ST12-CLOSURE::ST11-QUANTUM::010", "original-model-feasibility"),
    ("ST12-CLOSURE::ST11-QUANTUM::011", "same-formulation-comparator"),
    ("ST12-CLOSURE::ST11-QUANTUM::012", "small-instance-oracle"),
    ("ST12-CLOSURE::ST11-QUANTUM::013", "maturity-state-separation"),
    ("ST12-CLOSURE::ST11-QUANTUM::014", "sample-frequency-boundary"),
)

_MATH_REFS_BY_MODEL: Mapping[
    QuantumModelKind, tuple[str, ...]
] = MappingProxyType(
    {
        QuantumModelKind.QUBO: ("MATH-46",),
        QuantumModelKind.BQM: ("MATH-46",),
        QuantumModelKind.ISING: ("MATH-46", "MATH-47"),
        QuantumModelKind.CQM: ("MATH-48",),
        QuantumModelKind.DQM: ("MATH-49",),
        QuantumModelKind.QUADRATIC_PROGRAM: ("MATH-48",),
    }
)


@dataclass(frozen=True, slots=True)
class QuantumStructuralReadinessProjectionV1:
    """Typed structural requirement; never simulator/QPU readiness."""

    projection_id: str
    closure_id: str
    control_slug: str
    model_kind: QuantumModelKind
    mapping_owner: str
    mapping_refs: tuple[str, ...]
    source_schema: str
    original_formulation_refs: tuple[str, ...]
    objective_sense: str
    economic_scale: str
    variable_domains: str
    hard_constraints: str
    soft_preferences: str
    mapping_family: str
    converter_version: str
    coefficient_scale_dynamic_range: str
    penalty_adequacy: str
    inverse_mapping: str
    economic_interpret_back: str
    original_model_feasibility: str
    independent_small_instance_oracle_refs: tuple[str, ...]
    classical_fallback: str
    no_trade_fallback: str
    maturity_state: str
    latency_ttl_compatibility: str
    blocker_codes: tuple[str, ...]
    terminal_route: str
    structural_requirements_complete: bool = True
    simulator_execution: bool = False
    qpu_execution: bool = False
    quantum_advantage_claim: bool = False
    order_effect: bool = False

    def __post_init__(self) -> None:
        for name in (
            "projection_id",
            "closure_id",
            "control_slug",
            "mapping_owner",
            "source_schema",
            "objective_sense",
            "economic_scale",
            "variable_domains",
            "hard_constraints",
            "soft_preferences",
            "mapping_family",
            "converter_version",
            "coefficient_scale_dynamic_range",
            "penalty_adequacy",
            "inverse_mapping",
            "economic_interpret_back",
            "original_model_feasibility",
            "classical_fallback",
            "no_trade_fallback",
            "maturity_state",
            "latency_ttl_compatibility",
            "terminal_route",
        ):
            if not isinstance(getattr(self, name), str) or not getattr(
                self, name
            ):
                raise OwnerAdapterError(
                    ReasonCode.OWNER_DATA_MALFORMED,
                    f"quantum structural projection {name} is required",
                )
        for name in (
            "mapping_refs",
            "original_formulation_refs",
            "independent_small_instance_oracle_refs",
            "blocker_codes",
        ):
            values = getattr(self, name)
            if (
                not isinstance(values, tuple)
                or not values
                or any(not isinstance(value, str) or not value for value in values)
                or len(values) != len(set(values))
            ):
                raise OwnerAdapterError(
                    ReasonCode.OWNER_DATA_MALFORMED,
                    f"quantum structural projection {name} must be exact and unique",
                )
        effect_flags = (
            self.simulator_execution,
            self.qpu_execution,
            self.quantum_advantage_claim,
            self.order_effect,
        )
        if (
            not isinstance(self.model_kind, QuantumModelKind)
            or self.mapping_owner != "PR162E_Q_QUANTUM_AUTOMAPPER"
            or type(self.structural_requirements_complete) is not bool
            or not self.structural_requirements_complete
            or any(type(value) is not bool for value in effect_flags)
            or any(effect_flags)
            or (self.closure_id, self.control_slug)
            not in _QUANTUM_CLOSURE_ROWS
        ):
            raise OwnerAdapterError(
                ReasonCode.CAPABILITY_DENIED,
                "quantum structural projection changed owner, closure, or effect boundary",
            )
