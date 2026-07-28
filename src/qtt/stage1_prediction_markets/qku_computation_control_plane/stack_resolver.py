"""Deterministic applicable-stack resolution over existing owner projections."""

from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
from pathlib import Path
from types import MappingProxyType
from typing import Mapping

from .context import ComputationContextKeyV1
from .dependency_graph import (
    CompiledDependencyGraphV1,
    DependencyGraphCompilerV1,
    UnitConversionV1,
)
from .errors import ReasonCode, StackResolutionError
from .fallback import REGISTERED_FALLBACK_RESOLVER
from .implementation_registry import IMPLEMENTATION_REGISTRY
from .models import DependencyEdgeV1, DependencyNodeV1
from .specification import MATH_IO_CONTRACTS


def _required_text(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise StackResolutionError(
            ReasonCode.INVALID_CONTRACT,
            f"{field_name} must be nonempty text",
        )
    return value


def _unique_text_tuple(
    value: object,
    field_name: str,
    *,
    nonempty: bool = True,
) -> tuple[str, ...]:
    if (
        not isinstance(value, tuple)
        or (nonempty and not value)
        or any(not isinstance(item, str) or not item for item in value)
        or len(set(value)) != len(value)
    ):
        raise StackResolutionError(
            ReasonCode.INVALID_CONTRACT,
            f"{field_name} must be a unique immutable text tuple",
        )
    return value


@dataclass(frozen=True, slots=True)
class RP5EStackOwnerSnapshotV1:
    run_id: str
    schema_version: str
    template_ids: tuple[str, ...]
    context_ids: tuple[str, ...]
    venues: tuple[str, ...]
    preview_ids: tuple[str, ...]
    quantum_tag_ids: tuple[str, ...]
    classical_fallback_ids: tuple[str, ...]
    source_paths: tuple[str, ...]
    persistent_cartesian_grid: bool
    owner_execution_authority: str
    loaded_once_at_construction: bool = True
    runtime_effect_allowed: bool = False

    def __post_init__(self) -> None:
        for name in (
            "run_id",
            "schema_version",
            "owner_execution_authority",
        ):
            _required_text(getattr(self, name), name)
        for name in (
            "template_ids",
            "context_ids",
            "venues",
            "preview_ids",
            "quantum_tag_ids",
            "classical_fallback_ids",
            "source_paths",
        ):
            _unique_text_tuple(getattr(self, name), name)
        if (
            type(self.persistent_cartesian_grid) is not bool
            or self.persistent_cartesian_grid
            or type(self.loaded_once_at_construction) is not bool
            or not self.loaded_once_at_construction
            or type(self.runtime_effect_allowed) is not bool
            or self.runtime_effect_allowed
        ):
            raise StackResolutionError(
                ReasonCode.CAPABILITY_DENIED,
                "RP5E consumption must be read-once, non-Cartesian, and no-effect",
            )


class RP5EStackReadAdapterV1:
    """Narrow read-only adapter because RP5E exposes builder-oriented readers."""

    _FILES = (
        "templates.jsonl",
        "ctx_univ.jsonl",
        "tmp_previews.jsonl",
        "tmp_manifest.jsonl",
        "q_tags.jsonl",
        "classic.jsonl",
    )

    def __init__(self, repo_root: str | Path) -> None:
        self._repo_root = Path(repo_root).resolve()
        expected = (
            self._repo_root
            / "docs"
            / "master_plan"
            / "generated"
            / "pr168_rp5e"
        )
        from src.qtt.stage1_prediction_markets.pr168_rp5e_stack_generator.models import (
            GENERATED_DIR,
            read_jsonl,
        )

        if GENERATED_DIR.resolve() != expected:
            raise StackResolutionError(
                ReasonCode.OWNER_DATA_CONTRADICTORY,
                "RP5E canonical generated owner path differs from the repository root",
            )
        rows = {
            filename: tuple(read_jsonl(GENERATED_DIR / filename))
            for filename in self._FILES
        }
        self._snapshot = self._compile_snapshot(rows)

    @staticmethod
    def _compile_snapshot(
        rows: Mapping[str, tuple[dict[str, object], ...]],
    ) -> RP5EStackOwnerSnapshotV1:
        if any(not values for values in rows.values()):
            raise StackResolutionError(
                ReasonCode.OWNER_DATA_MISSING,
                "RP5E owner snapshot is incomplete",
            )
        all_rows = tuple(row for values in rows.values() for row in values)
        if any(
            row.get("source_pr") != "PR168-RP5E"
            or row.get("live_authority_flag") is not False
            or row.get("paper_authority_flag") is not False
            or row.get("qopt_execution_flag") is not False
            or row.get("quantum_backend_execution_flag") is not False
            or row.get("quantum_advantage_claim_flag") is not False
            for row in all_rows
        ):
            raise StackResolutionError(
                ReasonCode.OWNER_DATA_CONTRADICTORY,
                "RP5E owner snapshot violates its preview-only authority boundary",
            )
        run_ids = {row.get("run_id") for row in all_rows}
        versions = {row.get("schema_version") for row in all_rows}
        authorities = {
            row.get("execution_authority_ref")
            for row in all_rows
            if row.get("execution_authority_ref") is not None
        }
        if (
            len(run_ids) != 1
            or len(versions) != 1
            or len(authorities) != 1
            or not all(isinstance(value, str) and value for value in run_ids)
            or not all(isinstance(value, str) and value for value in versions)
        ):
            raise StackResolutionError(
                ReasonCode.OWNER_DATA_CONTRADICTORY,
                "RP5E snapshot version/run/authority lineage is inconsistent",
            )
        manifest_rows = rows["tmp_manifest.jsonl"]
        if (
            len(manifest_rows) != 1
            or manifest_rows[0].get("persistent_full_cartesian_grid_flag")
            is not False
        ):
            raise StackResolutionError(
                ReasonCode.OWNER_DATA_CONTRADICTORY,
                "RP5E persistent Cartesian-grid boundary is not closed",
            )

        def identities(filename: str, field_name: str) -> tuple[str, ...]:
            values = tuple(
                row.get(field_name) for row in rows[filename]
            )
            if any(not isinstance(value, str) or not value for value in values):
                raise StackResolutionError(
                    ReasonCode.OWNER_DATA_MALFORMED,
                    f"RP5E {filename} has a malformed {field_name}",
                )
            return tuple(sorted(set(values)))

        venues = tuple(
            sorted(
                {
                    str(row["venue"])
                    for row in rows["ctx_univ.jsonl"]
                    if isinstance(row.get("venue"), str) and row["venue"]
                }
            )
        )
        if not venues or any(
            row.get("full_jsonl_scan_allowed_flag") is not False
            or row.get("centralized_resolver_required_flag") is not True
            for row in rows["ctx_univ.jsonl"]
        ):
            raise StackResolutionError(
                ReasonCode.OWNER_DATA_CONTRADICTORY,
                "RP5E context owner does not require centralized cached resolution",
            )
        return RP5EStackOwnerSnapshotV1(
            run_id=next(iter(run_ids)),
            schema_version=next(iter(versions)),
            template_ids=identities("templates.jsonl", "template_id"),
            context_ids=identities("ctx_univ.jsonl", "context_id"),
            venues=venues,
            preview_ids=identities("tmp_previews.jsonl", "stack_preview_id"),
            quantum_tag_ids=identities("q_tags.jsonl", "quantum_tag_id"),
            classical_fallback_ids=identities(
                "classic.jsonl",
                "classical_fallback_id",
            ),
            source_paths=tuple(
                f"docs/master_plan/generated/pr168_rp5e/{name}"
                for name in RP5EStackReadAdapterV1._FILES
            ),
            persistent_cartesian_grid=False,
            owner_execution_authority=next(iter(authorities)),
        )

    @property
    def snapshot(self) -> RP5EStackOwnerSnapshotV1:
        return self._snapshot


@dataclass(frozen=True, slots=True)
class StackApplicabilityContextV1:
    trade_plan_candidate_id: str
    context_key: ComputationContextKeyV1
    venue: str
    market_family: str
    market_category: str
    mode: str
    required_roles: tuple[str, ...]
    owner_intent_ref: str
    input_lock_ref: str
    source_readiness_receipt_refs: tuple[str, ...]
    consumer_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        for name in (
            "trade_plan_candidate_id",
            "venue",
            "market_family",
            "market_category",
            "mode",
            "owner_intent_ref",
            "input_lock_ref",
        ):
            _required_text(getattr(self, name), name)
        if not isinstance(self.context_key, ComputationContextKeyV1):
            raise StackResolutionError(
                ReasonCode.INVALID_CONTRACT,
                "stack applicability requires ComputationContextKeyV1",
            )
        for name in (
            "required_roles",
            "source_readiness_receipt_refs",
            "consumer_refs",
        ):
            _unique_text_tuple(getattr(self, name), name)
        if self.mode not in {"CONTRACT_ONLY", "REPLAY", "PAPER"}:
            raise StackResolutionError(
                ReasonCode.CAPABILITY_DENIED,
                "Tranche B stack applicability excludes live, shadow, and canary modes",
            )


@dataclass(frozen=True, slots=True)
class RegisteredStackTemplateV1:
    template_id: str
    component_role_bindings: tuple[tuple[str, str], ...]
    edges: tuple[DependencyEdgeV1, ...]
    conversions: tuple[UnitConversionV1, ...]
    applicable_venues: tuple[str, ...]
    applicable_market_families: tuple[str, ...]
    applicable_market_categories: tuple[str, ...]
    applicable_modes: tuple[str, ...]
    rp5e_template_refs: tuple[str, ...]
    rp5e_receipt_refs: tuple[str, ...]
    parameter_policy_refs: tuple[str, ...]
    fallback_refs: tuple[str, ...]
    generation_recipe_ref: str
    consumer_routes: tuple[str, ...]
    retained_evidence_refs: tuple[str, ...]
    compiled_graph: CompiledDependencyGraphV1 = field(init=False)
    external_input_fields: tuple[tuple[str, str], ...] = field(init=False)

    def __post_init__(self) -> None:
        _required_text(self.template_id, "template_id")
        _required_text(self.generation_recipe_ref, "generation_recipe_ref")
        for name in (
            "applicable_venues",
            "applicable_market_families",
            "applicable_market_categories",
            "applicable_modes",
            "rp5e_template_refs",
            "rp5e_receipt_refs",
            "fallback_refs",
            "consumer_routes",
            "retained_evidence_refs",
        ):
            _unique_text_tuple(getattr(self, name), name)
        _unique_text_tuple(
            self.parameter_policy_refs,
            "parameter_policy_refs",
            nonempty=False,
        )
        if (
            not isinstance(self.component_role_bindings, tuple)
            or not self.component_role_bindings
            or any(
                not isinstance(item, tuple)
                or len(item) != 2
                or any(not isinstance(value, str) or not value for value in item)
                for item in self.component_role_bindings
            )
        ):
            raise StackResolutionError(
                ReasonCode.INVALID_CONTRACT,
                "stack component-role bindings must be typed immutable pairs",
            )
        component_ids = tuple(
            component_id for component_id, _ in self.component_role_bindings
        )
        roles = tuple(role for _, role in self.component_role_bindings)
        if (
            len(component_ids) != len(set(component_ids))
            or len(roles) != len(set(roles))
            or any(component_id not in IMPLEMENTATION_REGISTRY for component_id in component_ids)
        ):
            raise StackResolutionError(
                ReasonCode.UNKNOWN_IMPLEMENTATION,
                "stack component and role identities must be canonical and unique",
            )
        if any(mode not in {"CONTRACT_ONLY", "REPLAY", "PAPER"} for mode in self.applicable_modes):
            raise StackResolutionError(
                ReasonCode.CAPABILITY_DENIED,
                "stack templates cannot become live/shadow/canary eligible",
            )
        for fallback_ref in self.fallback_refs:
            REGISTERED_FALLBACK_RESOLVER.get(fallback_ref)

        nodes = tuple(
            DependencyNodeV1(
                node_id=component_id,
                output_unit=MATH_IO_CONTRACTS[component_id].outputs[0].unit,
                timing_class="SNAPSHOT",
                output_basis=MATH_IO_CONTRACTS[component_id].outputs[0].basis,
                output_field_ids=tuple(
                    output.name
                    for output in MATH_IO_CONTRACTS[component_id].outputs
                ),
                consumer_refs=self.consumer_routes,
                registered_fallback_ref=self.fallback_refs[0],
            )
            for component_id in component_ids
        )
        graph = DependencyGraphCompilerV1.compile(
            nodes,
            self.edges,
            self.conversions,
        )
        routed_fields: set[tuple[str, str]] = set()
        for edge in self.edges:
            upstream = MATH_IO_CONTRACTS[edge.upstream_id]
            downstream = MATH_IO_CONTRACTS[edge.downstream_id]
            if edge.upstream_output_field not in {
                output.name for output in upstream.outputs
            } or edge.downstream_input_field not in {
                input_field.name for input_field in downstream.inputs
            }:
                raise StackResolutionError(
                    ReasonCode.INVALID_CONTRACT,
                    "dependency edge field selector is absent from registered I/O",
                )
            routed_fields.add(
                (edge.downstream_id, edge.downstream_input_field)
            )
        external = tuple(
            (component_id, input_field.name)
            for component_id in graph.topological_order
            for input_field in MATH_IO_CONTRACTS[component_id].inputs
            if (component_id, input_field.name) not in routed_fields
        )
        object.__setattr__(self, "compiled_graph", graph)
        object.__setattr__(self, "external_input_fields", external)

    @property
    def component_ids(self) -> tuple[str, ...]:
        return tuple(item[0] for item in self.component_role_bindings)

    @property
    def roles(self) -> tuple[str, ...]:
        return tuple(item[1] for item in self.component_role_bindings)


@dataclass(frozen=True, slots=True)
class ApplicableStackResolutionReceiptV1:
    receipt_id: str
    selected_stack_id: str
    template_id: str
    trade_plan_candidate_id: str
    component_ids: tuple[str, ...]
    component_role_bindings: tuple[tuple[str, str], ...]
    compiled_graph: CompiledDependencyGraphV1
    external_input_fields: tuple[tuple[str, str], ...]
    dependency_closure: tuple[str, ...]
    fallback_closure: tuple[str, ...]
    rp5e_owner_run_id: str
    rp5e_consumed_refs: tuple[str, ...]
    generation_input_lock_ref: str
    pruning_reasons: tuple[str, ...]
    retained_evidence_refs: tuple[str, ...]
    consumer_routes: tuple[str, ...]
    terminal_route: str
    full_cartesian_generated: bool = False
    persistent_stack_created: bool = False
    universal_top_k_used: bool = False
    profit_score_used: bool = False
    no_authority_flag: bool = True

    def __post_init__(self) -> None:
        flags = (
            self.full_cartesian_generated,
            self.persistent_stack_created,
            self.universal_top_k_used,
            self.profit_score_used,
        )
        if any(type(value) is not bool for value in flags) or any(flags):
            raise StackResolutionError(
                ReasonCode.CAPABILITY_DENIED,
                "stack resolution cannot create Cartesian persistence or profit ranking",
            )
        if type(self.no_authority_flag) is not bool or not self.no_authority_flag:
            raise StackResolutionError(
                ReasonCode.CAPABILITY_DENIED,
                "stack resolution cannot create authority",
            )


class ApplicableStackResolverV1:
    """Resolve only registered role templates under pinned context evidence."""

    def __init__(
        self,
        *,
        repo_root: str | Path,
        templates: tuple[RegisteredStackTemplateV1, ...] | None = None,
        rp5e_snapshot: RP5EStackOwnerSnapshotV1 | None = None,
    ) -> None:
        self._rp5e = (
            rp5e_snapshot
            if rp5e_snapshot is not None
            else RP5EStackReadAdapterV1(repo_root).snapshot
        )
        if not isinstance(self._rp5e, RP5EStackOwnerSnapshotV1):
            raise StackResolutionError(
                ReasonCode.INVALID_CONTRACT,
                "RP5E snapshot must be typed",
            )
        selected_templates = (
            DEFAULT_REGISTERED_STACK_TEMPLATES
            if templates is None
            else templates
        )
        if (
            not isinstance(selected_templates, tuple)
            or not selected_templates
            or any(
                not isinstance(item, RegisteredStackTemplateV1)
                for item in selected_templates
            )
            or len({item.template_id for item in selected_templates})
            != len(selected_templates)
        ):
            raise StackResolutionError(
                ReasonCode.INVALID_CONTRACT,
                "registered stack templates must be unique and typed",
            )
        if any(
            not set(template.rp5e_template_refs)
            <= set(self._rp5e.template_ids)
            for template in selected_templates
        ):
            raise StackResolutionError(
                ReasonCode.OWNER_DATA_MISSING,
                "a stack template lacks its RP5E owner reference",
            )
        self._templates = tuple(
            sorted(selected_templates, key=lambda item: item.template_id)
        )
        self._by_id: Mapping[str, RegisteredStackTemplateV1] = MappingProxyType(
            {item.template_id: item for item in self._templates}
        )

    @property
    def rp5e_snapshot(self) -> RP5EStackOwnerSnapshotV1:
        return self._rp5e

    @property
    def templates(self) -> tuple[RegisteredStackTemplateV1, ...]:
        return self._templates

    def template(self, template_id: str) -> RegisteredStackTemplateV1:
        try:
            return self._by_id[template_id]
        except KeyError as exc:
            raise StackResolutionError(
                ReasonCode.STACK_NOT_APPLICABLE,
                f"unknown stack template: {template_id}",
            ) from exc

    def resolve(
        self,
        applicability: StackApplicabilityContextV1,
    ) -> ApplicableStackResolutionReceiptV1:
        if not isinstance(applicability, StackApplicabilityContextV1):
            raise StackResolutionError(
                ReasonCode.INVALID_CONTRACT,
                "stack applicability context must be typed",
            )
        candidates = tuple(
            template
            for template in self._templates
            if applicability.venue in template.applicable_venues
            and applicability.market_family
            in template.applicable_market_families
            and applicability.market_category
            in template.applicable_market_categories
            and applicability.mode in template.applicable_modes
            and set(applicability.required_roles) <= set(template.roles)
        )
        if not candidates:
            raise StackResolutionError(
                ReasonCode.STACK_NOT_APPLICABLE,
                "no registered dependency-closed stack applies to the exact context",
            )
        selected = min(
            candidates,
            key=lambda item: (
                len(set(item.roles) - set(applicability.required_roles)),
                item.template_id,
            ),
        )
        pruned = tuple(
            f"{candidate.template_id}::LESS_EXACT_ROLE_CLOSURE"
            for candidate in candidates
            if candidate is not selected
        )
        selected_stack_material = "|".join(
            (
                selected.template_id,
                applicability.context_key.stable_key,
                applicability.trade_plan_candidate_id,
                applicability.input_lock_ref,
                *selected.component_ids,
            )
        )
        selected_stack_id = (
            "STACK::"
            + sha256(selected_stack_material.encode("utf-8")).hexdigest()
        )
        receipt_material = "|".join(
            (
                selected_stack_id,
                self._rp5e.run_id,
                *applicability.source_readiness_receipt_refs,
            )
        )
        return ApplicableStackResolutionReceiptV1(
            receipt_id=(
                "STACK-RESOLUTION::"
                + sha256(receipt_material.encode("utf-8")).hexdigest()
            ),
            selected_stack_id=selected_stack_id,
            template_id=selected.template_id,
            trade_plan_candidate_id=applicability.trade_plan_candidate_id,
            component_ids=selected.component_ids,
            component_role_bindings=selected.component_role_bindings,
            compiled_graph=selected.compiled_graph,
            external_input_fields=selected.external_input_fields,
            dependency_closure=selected.compiled_graph.topological_order,
            fallback_closure=selected.fallback_refs,
            rp5e_owner_run_id=self._rp5e.run_id,
            rp5e_consumed_refs=(
                *selected.rp5e_template_refs,
                *selected.rp5e_receipt_refs,
                *self._rp5e.source_paths,
            ),
            generation_input_lock_ref=applicability.input_lock_ref,
            pruning_reasons=pruned,
            retained_evidence_refs=(
                *selected.retained_evidence_refs,
                *applicability.source_readiness_receipt_refs,
                applicability.owner_intent_ref,
            ),
            consumer_routes=tuple(
                dict.fromkeys(
                    (*selected.consumer_routes, *applicability.consumer_refs)
                )
            ),
            terminal_route="QKUComputationControlPlaneServiceV1::COMPUTE_STACK",
        )


MARKET_PROBABILITY_EDGE_TEMPLATE = RegisteredStackTemplateV1(
    template_id="ST12B::TEMPLATE::MARKET_PROBABILITY_EDGE",
    component_role_bindings=(
        ("MATH-01", "market_implied_probability"),
        ("MATH-02", "edge_probability"),
    ),
    edges=(
        DependencyEdgeV1(
            upstream_id="MATH-01",
            downstream_id="MATH-02",
            supplied_unit="probability",
            required_unit="probability",
            timing_class="SNAPSHOT",
            upstream_output_field="p_market",
            downstream_input_field="market_implied_probability",
            supplied_basis="unit_interval",
            required_basis="unit_interval",
            material=True,
        ),
    ),
    conversions=(),
    applicable_venues=(
        "KALSHI",
        "POLYMARKET",
        "FORECASTEX_IBKR",
        "OWNER_SUPPLIED_PURE_COMPUTATION",
    ),
    applicable_market_families=("PREDICTION_MARKETS",),
    applicable_market_categories=("binary_event",),
    applicable_modes=("CONTRACT_ONLY", "REPLAY", "PAPER"),
    rp5e_template_refs=("RP5E_TEMPLATE_HOT_CORE",),
    rp5e_receipt_refs=(
        "RP5E_CONTEXT_ACCESS_PATH_RULE",
        "RP5E_EXEC_AUTH::STACK_PREVIEW_HANDOFF_ONLY_NO_ORDER_AUTHORITY",
    ),
    parameter_policy_refs=(),
    fallback_refs=("FALLBACK::NO_EFFECT_FAIL_CLOSED",),
    generation_recipe_ref=(
        "MATH-01.p_market->MATH-02.market_implied_probability@"
        "ST12_TRANCHE_B_MATH_REGISTRY_V1_1R1"
    ),
    consumer_routes=(
        "risk_manager_agent",
        "commander_agent",
        "READINESS1",
        "PRETRADE1",
        "SVC1",
        "AGENT-ORCH1",
    ),
    retained_evidence_refs=(
        "TRANCHE_B_GOLDEN::MATH-01",
        "TRANCHE_B_GOLDEN::MATH-02",
        "FALLBACK::NO_EFFECT_FAIL_CLOSED",
    ),
)

DEFAULT_REGISTERED_STACK_TEMPLATES = (MARKET_PROBABILITY_EDGE_TEMPLATE,)
