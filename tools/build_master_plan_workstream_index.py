#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
import pathlib
from typing import Any, Sequence


DEFAULT_MASTER_PLAN = pathlib.Path("docs") / "master_plan" / "QTT_MasterPlan_Current.md"
DEFAULT_OUTPUT = (
    pathlib.Path(".tmp")
    / "master_plan_workstream_index"
    / "ImplementationWorkstreamIndex.json"
)

REQUIRED_WORKSTREAM_FIELDS = (
    "workstream_id",
    "title",
    "implementation_phase_order",
    "master_plan_anchor_terms",
    "allowed_scope_summary",
    "blocked_scope_summary",
    "requires_accepted_source_evidence_before_runtime_use",
    "creates_runtime_trading_authority",
    "creates_order_execution_authority",
    "creates_profit_claim",
    "status",
)


@dataclass(frozen=True)
class WorkstreamDefinition:
    workstream_id: str
    title: str
    implementation_phase_order: int
    master_plan_anchor_terms: tuple[str, ...]
    allowed_scope_summary: str
    blocked_scope_summary: str
    requires_accepted_source_evidence_before_runtime_use: bool
    status: str


class AnchorValidationError(ValueError):
    pass


WORKSTREAM_DEFINITIONS: tuple[WorkstreamDefinition, ...] = (
    WorkstreamDefinition(
        workstream_id="source_evidence_acceptance_registry",
        title="Source Evidence Acceptance Registry",
        implementation_phase_order=10,
        master_plan_anchor_terms=(
            "### 0X.4Q Official source-evidence retrieval, exact quote/span capture, conditional acceptance execution, and revalidation Codex task packet",
            "accepted source-evidence packet",
            "target-field acceptance ledger",
            "This working draft does not itself retrieve sources, accept facts, populate connector semantics, or reduce blockers.",
        ),
        allowed_scope_summary=(
            "Index the future source-evidence acceptance registry and target-field ledger "
            "tooling as a control-plane workstream only."
        ),
        blocked_scope_summary=(
            "No source retrieval execution, source-fact acceptance, connector semantic "
            "population, runtime resolver snapshot, live reachability, blocker reduction, "
            "or profit evidence is created by this index."
        ),
        requires_accepted_source_evidence_before_runtime_use=False,
        status="immediate_non_runtime_index_target",
    ),
    WorkstreamDefinition(
        workstream_id="connector_capability_registry",
        title="Connector Capability Registry",
        implementation_phase_order=20,
        master_plan_anchor_terms=(
            "### 0X.4R Connector semantic binding after accepted source-evidence packets Codex task packet",
            "target-field-specific accepted source-evidence packets already exist and validate",
            "connector capability card",
            "active connector capability matrix",
            "Market and platform setup must precede connector semantic population.",
        ),
        allowed_scope_summary=(
            "Index connector capability and semantic-readiness registry scaffolding that "
            "keeps source-required placeholders until accepted evidence and gates exist."
        ),
        blocked_scope_summary=(
            "No connector semantic values, venue/API facts, live clients, network IO, "
            "order authority, runtime cash values, or connector binding authority are "
            "created by this index."
        ),
        requires_accepted_source_evidence_before_runtime_use=True,
        status="next_after_source_evidence_acceptance_registry",
    ),
    WorkstreamDefinition(
        workstream_id="runtime_orchestration_skeleton",
        title="Runtime Orchestration Skeleton",
        implementation_phase_order=30,
        master_plan_anchor_terms=(
            "### 0X.4N Stage-1 resolver / replay-paper / arbitrage / dashboard / capital-risk runtime-scaffold gate Codex task packet",
            "stage1_runtime_scaffold_gate",
            "transition-runtime scaffolds may define state-machine and gate contract placeholders only",
            "It does not select exact contracts, events, or markets; does not create runtime resolver snapshots; does not run replay or paper",
        ),
        allowed_scope_summary=(
            "Index non-live runtime scaffold, receipt-envelope, state-machine, and "
            "gate-placeholder work needed before real resolver snapshots or lanes."
        ),
        blocked_scope_summary=(
            "No exact market selection, runtime resolver snapshot creation, replay or "
            "paper execution, live reachability, runtime cash claim, order path, or "
            "profit evidence is created by this index."
        ),
        requires_accepted_source_evidence_before_runtime_use=True,
        status="next_after_connector_capability_registry",
    ),
    WorkstreamDefinition(
        workstream_id="replay_paper_execution_graph",
        title="Replay/Paper Execution Graph",
        implementation_phase_order=40,
        master_plan_anchor_terms=(
            "### 0X.4T Concurrent replay/paper execution after runtime resolver snapshot Codex task packet",
            "valid runtime resolver snapshot, immutable input lock, and replay/paper input identity",
            "same runtime resolver snapshot, same input lock, same replay_paper_input_identity_digest",
            "separate replay result packet",
            "separate paper result packet",
        ),
        allowed_scope_summary=(
            "Index the non-live replay/paper graph shape, shared input identity, lane "
            "separation, and result-packet boundaries for future implementation."
        ),
        blocked_scope_summary=(
            "No replay run, paper run, result packet, dual-result review, live "
            "eligibility, order execution, runtime cash receipt, AtomicRows mutation, "
            "or profit claim is created by this index."
        ),
        requires_accepted_source_evidence_before_runtime_use=True,
        status="next_after_runtime_orchestration_skeleton",
    ),
    WorkstreamDefinition(
        workstream_id="venue_abstraction_layer",
        title="Venue Abstraction Layer",
        implementation_phase_order=50,
        master_plan_anchor_terms=(
            "### 0X.4L Venue-neutral prediction-adapter, source-required placeholder contracts, and pre-connector-scaffold gate Codex task packet",
            "Venue-neutral and market-neutral foundations",
            "Build venue-neutral market-data abstractions.",
            "Build venue-neutral order-intent abstractions.",
            "Codex must not hard-code Kalshi / FORECASTEX_IBKR / Polymarket assumptions into venue-neutral abstractions.",
        ),
        allowed_scope_summary=(
            "Index venue-neutral adapter and abstraction work that separates market "
            "data, order-intent, private-state, and capability surfaces from concrete "
            "venue semantics."
        ),
        blocked_scope_summary=(
            "No venue-specific fees, ticks, rate limits, settlement rules, order "
            "semantics, private-state semantics, exact markets, live clients, or "
            "trading authority are created by this index."
        ),
        requires_accepted_source_evidence_before_runtime_use=True,
        status="next_after_replay_paper_execution_graph",
    ),
    WorkstreamDefinition(
        workstream_id="order_intent_execution_router_scaffolding",
        title="Order Intent Execution Router Scaffolding",
        implementation_phase_order=60,
        master_plan_anchor_terms=(
            "No QTT runtime agent may send a live order directly to a venue connector without the risk gate and execution router.",
            "Execution Router final order-submission authority",
            "Build venue-neutral order-intent abstractions.",
            "Paper-order intent and paper-order receipt are replay/paper schemas only. They do not submit real orders",
        ),
        allowed_scope_summary=(
            "Index order-intent and execution-router scaffold boundaries so future "
            "work can define typed intents and routing checks without live release."
        ),
        blocked_scope_summary=(
            "No real order submission, cancellation, reduction, closure, live signer "
            "path, venue write connectivity, order execution authority, or profit "
            "evidence is created by this index."
        ),
        requires_accepted_source_evidence_before_runtime_use=True,
        status="next_after_venue_abstraction_layer",
    ),
    WorkstreamDefinition(
        workstream_id="atomicrows_parameter_bundle_validation_later",
        title="AtomicRows Parameter Bundle Validation Later",
        implementation_phase_order=90,
        master_plan_anchor_terms=(
            "AtomicRows.bundle.jsonl",
            "Bootstrap generated-derivative mode may proceed while `AtomicRows.bundle.jsonl` is absent",
            "must not claim 4,183-row completion",
            "Completion generated-derivative mode may claim 4,183-row derivative coverage only when `AtomicRows.bundle.jsonl` and `AtomicRows.bundle.sha256` exist, validate, contain exactly 4,183 parameter rows, and pass AtomicRows completion gates.",
        ),
        allowed_scope_summary=(
            "Index AtomicRows bundle validation as a later workstream only, preserving "
            "the bootstrap no-completion boundary until real bundle authority exists."
        ),
        blocked_scope_summary=(
            "No AtomicRows bundle creation, bundle hash creation, row invention, "
            "4,183-row completion claim, blocker reduction, runtime trading authority, "
            "or profit evidence is created by this index."
        ),
        requires_accepted_source_evidence_before_runtime_use=True,
        status="later_blocked_until_atomicrows_bundle_authority",
    ),
)


def _as_posix(path: str | pathlib.Path) -> str:
    return pathlib.Path(path).as_posix()


def _missing_anchor_terms(
    text: str, definitions: Sequence[WorkstreamDefinition]
) -> list[tuple[str, str]]:
    return [
        (definition.workstream_id, term)
        for definition in definitions
        for term in definition.master_plan_anchor_terms
        if term not in text
    ]


def validate_anchor_terms(
    text: str, definitions: Sequence[WorkstreamDefinition] = WORKSTREAM_DEFINITIONS
) -> None:
    missing = _missing_anchor_terms(text, definitions)
    if not missing:
        return

    details = "\n".join(
        f"- {workstream_id}: missing anchor term {term!r}"
        for workstream_id, term in missing
    )
    raise AnchorValidationError(
        "master plan workstream index anchor validation failed:\n" + details
    )


def build_workstream_records(
    definitions: Sequence[WorkstreamDefinition] = WORKSTREAM_DEFINITIONS,
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for definition in definitions:
        records.append(
            {
                "workstream_id": definition.workstream_id,
                "title": definition.title,
                "implementation_phase_order": definition.implementation_phase_order,
                "master_plan_anchor_terms": list(definition.master_plan_anchor_terms),
                "allowed_scope_summary": definition.allowed_scope_summary,
                "blocked_scope_summary": definition.blocked_scope_summary,
                "requires_accepted_source_evidence_before_runtime_use": (
                    definition.requires_accepted_source_evidence_before_runtime_use
                ),
                "creates_runtime_trading_authority": False,
                "creates_order_execution_authority": False,
                "creates_profit_claim": False,
                "status": definition.status,
            }
        )
    return records


def build_master_plan_workstream_index(master_plan: pathlib.Path) -> dict[str, Any]:
    text = master_plan.read_text(encoding="utf-8")
    validate_anchor_terms(text)
    workstreams = build_workstream_records()

    return {
        "schema_version": 1,
        "index_name": "ImplementationWorkstreamIndex",
        "deterministic_output": True,
        "tool": "tools/build_master_plan_workstream_index.py",
        "source_document": _as_posix(master_plan),
        "authority": {
            "authority_class": "NON_AUTHORITATIVE_DERIVED_IMPLEMENTATION_INDEX",
            "derived_from_master_plan": _as_posix(master_plan),
            "notice": (
                "Derived from literal anchor terms in the master plan for future "
                "implementation planning only. This index is not the master plan, "
                "not source-fact acceptance, not connector binding, not runtime "
                "trading authority, not order execution authority, not AtomicRows "
                "bundle authority, not freeze authority, and not profit evidence."
            ),
        },
        "required_workstream_fields": list(REQUIRED_WORKSTREAM_FIELDS),
        "workstream_count": len(workstreams),
        "workstreams": workstreams,
    }


def write_index(index: dict[str, Any], output: pathlib.Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(index, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--master-plan", default=str(DEFAULT_MASTER_PLAN))
    parser.add_argument("--out", default=str(DEFAULT_OUTPUT))
    args = parser.parse_args(argv)

    try:
        index = build_master_plan_workstream_index(pathlib.Path(args.master_plan))
    except AnchorValidationError as exc:
        raise SystemExit(str(exc)) from exc

    output = pathlib.Path(args.out)
    write_index(index, output)
    print(
        "MASTER_PLAN_WORKSTREAM_INDEX_OK "
        f"workstreams={index['workstream_count']} out={output}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
