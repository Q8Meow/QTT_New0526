"""Read-only PR162E-Q semantic views; no backend or simulator execution."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
import json
from pathlib import Path
from types import MappingProxyType
from typing import Mapping

from .errors import ContractValidationError, OwnerAdapterError, ReasonCode


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


# BEGIN GENERATED ST12B V3.4 OWNER-FROZEN DATA
_ST12B_QUANTUM_STRUCTURAL_READINESS_JSON = (
    '[{"canonical_storage":"constant + diagonal linear binary terms + unique i<j interactions","classical_baseline":"direct energy enumeration/solver","coefficient_units":"normalized objective plus external scaling receipt","constraint_route":"not represented in bare QUBO; conversion proof required","converter_route":"explicit adapter only","executable_oracle_capabilities":["DIRECT_ASSIGNMENT_ENERGY","EXHAUSTIVE_BINARY_ENUMERATION_N_LE_12"],"fallback":"deterministic classical evaluator","feasibility_recheck":"original model outside bare QUBO required","interpret_back":"original objective scaling receipt required","inverse_mapping":"binary labels preserved","latency_suitability":"precomputed/nearline; no QPU wait in order path","math_spec_id":"MATH-46","maturity_state":"STRUCTURALLY_READY","model_grammar":"QTT_QUBO_UPPER_TRIANGULAR_V1","objective_sense":"preserved from original model","penalty_route":"not applicable in bare energy convention","qpu_or_simulator_authority":false,"sampler_compa'
    'tibility":"BQM/QUBO capable sampler only after backend capability receipt","small_exact_oracle":"exhaustive binary enumeration for n<=12 implemented in quantum_models.math_46","structural_readiness_matches_executable_oracle":true,"terminal_state":"STRUCTURAL_READINESS_CLAIM_EXECUTABLY_PROVEN","topology_or_embedding_requirements":"runtime backend-specific and not hardcoded","variable_domains":["BINARY"]},{"canonical_storage":"h,J,offset with x=(1-s)/2","classical_baseline":"direct QUBO evaluation","coefficient_units":"same normalized objective","constraint_route":"inherited from mapped QUBO and original-model feasibility","converter_route":"formal algebra; optional Qiskit compatibility adapter only","executable_oracle_capabilities":["RAW_FIELD_CANONICALIZATION_ADAPTER","EXHAUSTIVE_QUBO_ISING_PARITY_N_LE_12"],"fallback":"QUBO/direct classical","feasibility_recheck":"mandatory original model","interpret_back":"QUBO and original model","inverse_mapping":"x=(1-s)/2","latency_suitability":"p'
    'recomputed/nearline","math_spec_id":"MATH-47","maturity_state":"STRUCTURALLY_READY","model_grammar":"QTT_ISING_X_EQUALS_ONE_MINUS_S_OVER_TWO_V1","objective_sense":"energy parity preserves QUBO","penalty_route":"inherited and must already be adequate","qpu_or_simulator_authority":false,"sampler_compatibility":"Ising capable sampler only after capability receipt","small_exact_oracle":"immutable raw-field canonicalization plus exhaustive QUBO/Ising energy parity for n<=12","structural_readiness_matches_executable_oracle":true,"terminal_state":"STRUCTURAL_READINESS_CLAIM_EXECUTABLY_PROVEN","topology_or_embedding_requirements":"runtime backend-specific","variable_domains":["SPIN {-1,+1}"]},{"canonical_storage":"versioned variables/objective/named constraints","classical_baseline":"same-formulation MILP/MIQP/enumeration","coefficient_units":"declared per term","constraint_route":"native CQM preferred when exact backend support; otherwise proven conversion","converter_route":"optional dimod 0'
    '.12.22 cqm_to_bqm with inverter","executable_oracle_capabilities":["ENUMERATION_VALUES_VALIDATION","FINITE_CQM_ENUMERATION_MAX_4096","ORIGINAL_MODEL_FEASIBILITY","CONVERSION_PENALTY_ADEQUACY"],"fallback":"same-formulation classical","feasibility_recheck":"mandatory","interpret_back":"original variables, units, objective, constraints","inverse_mapping":"converter inverter plus label crosswalk","latency_suitability":"offline/nearline","math_spec_id":"MATH-48","maturity_state":"STRUCTURALLY_READY","model_grammar":"QTT_CQM_GRAMMAR_V1","objective_sense":"MINIMIZE or MAXIMIZE explicit","penalty_route":"no universal penalty; omitted dimod default is pinned candidate only","qpu_or_simulator_authority":false,"sampler_compatibility":"CQM/hybrid or converted BQM only after capability receipt","small_exact_oracle":"finite enumeration using every declared enumeration_values row, max 4096 assignments, with native feasible optimum and conversion-penalty adequacy comparison","structural_readiness_matc'
    'hes_executable_oracle":true,"terminal_state":"STRUCTURAL_READINESS_CLAIM_EXECUTABLY_PROVEN","topology_or_embedding_requirements":"runtime specific","variable_domains":["BINARY","INTEGER","REAL with explicit bounds/enumeration for small oracle"]},{"canonical_storage":"ordered variables/cases, explicit linear biases, unique pairwise case interactions","classical_baseline":"direct enumeration/heuristic","coefficient_units":"normalized objective","constraint_route":"one case per variable is native model semantics","converter_route":"no silent one-hot; comparator conversion requires proved penalty","executable_oracle_capabilities":["FINITE_DQM_CARTESIAN_ENUMERATION_MAX_4096","NATIVE_CASE_LABEL_INTERPRET_BACK"],"fallback":"classical enumeration/heuristic","feasibility_recheck":"case membership mandatory","interpret_back":"original case selections","inverse_mapping":"case labels preserved","latency_suitability":"offline/nearline","math_spec_id":"MATH-49","maturity_state":"STRUCTURALLY_READY",'
    '"model_grammar":"QTT_DQM_GRAMMAR_V1","objective_sense":"declared by consumer","penalty_route":"comparator only, no universal penalty","qpu_or_simulator_authority":false,"sampler_compatibility":"DQM/hybrid after capability receipt","small_exact_oracle":"cartesian native-case enumeration max 4096 assignments","structural_readiness_matches_executable_oracle":true,"terminal_state":"STRUCTURAL_READINESS_CLAIM_EXECUTABLY_PROVEN","topology_or_embedding_requirements":"runtime specific","variable_domains":["ORDERED_DISCRETE_CASES"]}]'
)
# END GENERATED ST12B V3.4 OWNER-FROZEN DATA


@dataclass(frozen=True, slots=True)
class QuantumStructuralReadinessV1:
    math_spec_id: str
    model_grammar: str
    maturity_state: str
    variable_domains: tuple[str, ...]
    canonical_storage: str
    objective_sense: str
    coefficient_units: str
    constraint_route: str
    penalty_route: str
    converter_route: str
    inverse_mapping: str
    interpret_back: str
    feasibility_recheck: str
    sampler_compatibility: str
    topology_or_embedding_requirements: str
    latency_suitability: str
    classical_baseline: str
    fallback: str
    small_exact_oracle: str
    executable_oracle_capabilities: tuple[str, ...]
    qpu_or_simulator_authority: bool
    structural_readiness_matches_executable_oracle: bool
    terminal_state: str

    def __post_init__(self) -> None:
        for name in (
            "math_spec_id",
            "model_grammar",
            "maturity_state",
            "canonical_storage",
            "objective_sense",
            "coefficient_units",
            "constraint_route",
            "penalty_route",
            "converter_route",
            "inverse_mapping",
            "interpret_back",
            "feasibility_recheck",
            "sampler_compatibility",
            "topology_or_embedding_requirements",
            "latency_suitability",
            "classical_baseline",
            "fallback",
            "small_exact_oracle",
            "terminal_state",
        ):
            value = getattr(self, name)
            if not isinstance(value, str) or not value:
                raise ContractValidationError(
                    ReasonCode.INVALID_CONTRACT,
                    f"quantum structural field {name} must be nonempty text",
                )
        for name in ("variable_domains", "executable_oracle_capabilities"):
            values = getattr(self, name)
            if (
                not isinstance(values, tuple)
                or not values
                or any(not isinstance(value, str) or not value for value in values)
                or len(values) != len(set(values))
            ):
                raise ContractValidationError(
                    ReasonCode.INVALID_CONTRACT,
                    f"quantum structural field {name} is invalid",
                )
        if (
            self.math_spec_id not in {"MATH-46", "MATH-47", "MATH-48", "MATH-49"}
            or self.maturity_state != "STRUCTURALLY_READY"
            or self.terminal_state
            != "STRUCTURAL_READINESS_CLAIM_EXECUTABLY_PROVEN"
            or type(self.qpu_or_simulator_authority) is not bool
            or self.qpu_or_simulator_authority
            or type(self.structural_readiness_matches_executable_oracle)
            is not bool
            or not self.structural_readiness_matches_executable_oracle
        ):
            raise ContractValidationError(
                ReasonCode.CAPABILITY_DENIED,
                "quantum structural readiness cannot authorize a simulator or QPU",
            )


def _quantum_structural_row(
    row: Mapping[str, object],
) -> QuantumStructuralReadinessV1:
    return QuantumStructuralReadinessV1(
        math_spec_id=str(row["math_spec_id"]),
        model_grammar=str(row["model_grammar"]),
        maturity_state=str(row["maturity_state"]),
        variable_domains=tuple(str(value) for value in row["variable_domains"]),
        canonical_storage=str(row["canonical_storage"]),
        objective_sense=str(row["objective_sense"]),
        coefficient_units=str(row["coefficient_units"]),
        constraint_route=str(row["constraint_route"]),
        penalty_route=str(row["penalty_route"]),
        converter_route=str(row["converter_route"]),
        inverse_mapping=str(row["inverse_mapping"]),
        interpret_back=str(row["interpret_back"]),
        feasibility_recheck=str(row["feasibility_recheck"]),
        sampler_compatibility=str(row["sampler_compatibility"]),
        topology_or_embedding_requirements=str(
            row["topology_or_embedding_requirements"]
        ),
        latency_suitability=str(row["latency_suitability"]),
        classical_baseline=str(row["classical_baseline"]),
        fallback=str(row["fallback"]),
        small_exact_oracle=str(row["small_exact_oracle"]),
        executable_oracle_capabilities=tuple(
            str(value) for value in row["executable_oracle_capabilities"]
        ),
        qpu_or_simulator_authority=(
            row["qpu_or_simulator_authority"] is True
        ),
        structural_readiness_matches_executable_oracle=(
            row["structural_readiness_matches_executable_oracle"] is True
        ),
        terminal_state=str(row["terminal_state"]),
    )


QUANTUM_STRUCTURAL_READINESS = tuple(
    _quantum_structural_row(row)
    for row in json.loads(_ST12B_QUANTUM_STRUCTURAL_READINESS_JSON)
)
QUANTUM_STRUCTURAL_READINESS_BY_MATH_ID: Mapping[
    str, QuantumStructuralReadinessV1
] = MappingProxyType(
    {row.math_spec_id: row for row in QUANTUM_STRUCTURAL_READINESS}
)
if (
    tuple(QUANTUM_STRUCTURAL_READINESS_BY_MATH_ID)
    != ("MATH-46", "MATH-47", "MATH-48", "MATH-49")
    or len(QUANTUM_STRUCTURAL_READINESS) != 4
):
    raise ContractValidationError(
        ReasonCode.INVALID_CONTRACT,
        "the frozen quantum structural-readiness roster must contain four rows",
    )
