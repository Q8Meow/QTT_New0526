from __future__ import annotations

import ast
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import timedelta
from pathlib import Path

import pytest

from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import (
    ContractValidationError,
    NumericDomainError,
    ReasonCode,
    SerializationSafetyError,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.implementation_registry import (
    compute_math_39_queue_position_estimate,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.latency_policy import (
    ALLOWED_HOTPATH_DEPENDENCIES,
    CLOCK_REGISTRY,
    FORBIDDEN_HOTPATH_DEPENDENCIES,
    STAGE_NAMES,
    ResourceUsageV1,
    aggregate_latency_samples,
    build_latency_measurement,
    evaluate_latency_profile,
    latency_stage_durations,
    local_duration_now_ns,
    measure_callable,
    stale_fallback,
    utc_event_time,
    validate_hotpath_dependency_classes,
    validate_resource_bounds,
    validate_trace_propagation,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.mode_snapshot_policy import (
    evaluate_mode_snapshot_candidate,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.models import (
    LatencyBudgetProfileV1,
    LatencyMeasurementLabelsV1,
    ResourceBoundsProfileV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.stage1_launch_graph import (
    build_stage1_launch_graph_v2,
    validate_stage1_launch_graph_v2,
)
from tests.stage1_prediction_markets.qku_computation_control_plane.test_policy_state_matrix import (
    _inputs,
)


def _stage_values(multiplier: int = 1) -> dict[str, int]:
    return {
        name: multiplier * position
        for position, name in enumerate(STAGE_NAMES, start=1)
    }


def _labels(*, concurrency: int = 1, fallback: bool = False) -> LatencyMeasurementLabelsV1:
    return LatencyMeasurementLabelsV1(
        cold_or_warm="WARM",
        concurrency_level=concurrency,
        platform_profile_id="OWNER-PLATFORM::TEST",
        operation_id="submit_candidate_proposal",
        success_or_blocker="NO_EFFECT_TEST",
        fallback_used=fallback,
    )


def test_clock_decomposition_distribution_and_telemetry_semantics() -> None:
    assert tuple(CLOCK_REGISTRY) == (
        "LOCAL_DURATION",
        "LOCAL_DURATION_FALLBACK",
        "EVENT_CORRELATION",
        "PROVIDER_EVENT_TIME",
    )
    assert len(STAGE_NAMES) == 9
    event_time = utc_event_time()
    assert event_time.utcoffset() is not None
    assert event_time.utcoffset().total_seconds() == 0
    first = local_duration_now_ns()
    _, elapsed = measure_callable(lambda: sum(range(32)))
    second = local_duration_now_ns()
    assert second >= first
    assert elapsed >= 0

    stages = latency_stage_durations(_stage_values())
    assert stages.total_local_no_effect_ns == sum(range(1, 10))
    measurement = build_latency_measurement(
        measurement_ref="LATENCY::D::1",
        stage_values_ns=_stage_values(),
        labels=_labels(),
        rejection_count=2,
        observer_overhead_ns=3,
        event_time_utc=event_time,
    )
    assert measurement.stages == stages
    assert measurement.cumulative_stage_ns[-1] == stages.total_local_no_effect_ns
    assert measurement.local_duration_clock_id in {
        "LOCAL_DURATION",
        "LOCAL_DURATION_FALLBACK",
    }
    assert measurement.clock_implementation
    assert measurement.platform_description
    assert measurement.runtime_effect_authorized is False

    distribution = aggregate_latency_samples((9, 1, 5, 3, 7, 2, 8, 6, 4, 10))
    assert (
        distribution.count,
        distribution.minimum_ns,
        distribution.maximum_ns,
        distribution.p50_ns,
        distribution.p95_ns,
        distribution.p99_ns,
    ) == (10, 1, 10, 5, 10, 10)


def test_owner_profiles_observer_effect_staleness_and_resource_bounds() -> None:
    measurement = build_latency_measurement(
        measurement_ref="LATENCY::D::PROFILE",
        stage_values_ns=_stage_values(),
        labels=_labels(),
        observer_overhead_ns=5,
    )
    missing = evaluate_latency_profile(measurement, None)
    assert missing.accepted_for_offline_measurement is True
    assert missing.promotion_sensitive_allow_blocked is True
    assert missing.reason_codes == (ReasonCode.LATENCY_PROFILE_REQUIRED,)

    profile = LatencyBudgetProfileV1(
        profile_id="LATENCY-PROFILE::OWNER::1",
        component_budget_ns=tuple((name, 10) for name in STAGE_NAMES),
        histogram_boundaries_ns=(1, 10, 100),
        maximum_observer_overhead_ns=5,
        alert_threshold_ns=100,
        policy_version="LATENCY-POLICY::1",
    )
    assert evaluate_latency_profile(measurement, profile).promotion_sensitive_allow_blocked is False
    exceeded = replace(profile, maximum_observer_overhead_ns=4)
    assert evaluate_latency_profile(measurement, exceeded).promotion_sensitive_allow_blocked is True

    usage = ResourceUsageV1(
        input_cardinality=4,
        input_bytes=128,
        dependency_depth=4,
        bootstrap_repetitions=0,
        concurrency=2,
    )
    bounds = ResourceBoundsProfileV1(
        profile_id="RESOURCE-BOUNDS::OWNER::1",
        maximum_input_cardinality=4,
        maximum_input_bytes=128,
        maximum_dependency_depth=4,
        maximum_bootstrap_repetitions=1,
        maximum_concurrency=2,
    )
    assert validate_resource_bounds(usage, bounds) == ()
    assert validate_resource_bounds(replace(usage, input_bytes=129), bounds) == (
        ReasonCode.RESOURCE_BOUND_EXCEEDED,
    )
    assert validate_resource_bounds(usage, None) == (
        ReasonCode.RESOURCE_BOUND_EXCEEDED,
    )

    now = utc_event_time()
    assert stale_fallback(
        evaluated_at=now,
        valid_until=now + timedelta(seconds=1),
        preapproved_fast_classical_fallback_ref=None,
    ).terminal_route == "CONTINUE_NO_EFFECT"
    assert stale_fallback(
        evaluated_at=now,
        valid_until=now - timedelta(seconds=1),
        preapproved_fast_classical_fallback_ref="FAST-CLASSICAL::PREAPPROVED",
    ).terminal_route == "PREAPPROVED_FAST_CLASSICAL_FALLBACK_NO_EFFECT"
    assert stale_fallback(
        evaluated_at=now,
        valid_until=now - timedelta(seconds=1),
        preapproved_fast_classical_fallback_ref=None,
    ).terminal_route == "NO_TRADE"


def test_hotpath_dependency_trace_and_input_adversaries_fail_closed() -> None:
    assert validate_hotpath_dependency_classes(tuple(ALLOWED_HOTPATH_DEPENDENCIES)) == ()
    for forbidden in FORBIDDEN_HOTPATH_DEPENDENCIES:
        assert validate_hotpath_dependency_classes((forbidden,)) == (
            ReasonCode.LATER_TRANCHE_AUTHORITY_REQUIRED,
        )
    traceparent = "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01"
    assert validate_trace_propagation(
        input_traceparent=traceparent,
        input_tracestate="vendor=value",
        output_traceparent=traceparent,
        output_tracestate="vendor=value",
    ) == ()
    assert validate_trace_propagation(
        input_traceparent=traceparent,
        input_tracestate="vendor=value",
        output_traceparent=traceparent[:-2] + "00",
        output_tracestate="vendor=value",
    ) == (ReasonCode.IDENTITY_OR_VERSION_UNRESOLVED,)

    with pytest.raises(NumericDomainError):
        compute_math_39_queue_position_estimate("-1", "0", "0", "0")
    with pytest.raises(ContractValidationError):
        evaluate_mode_snapshot_candidate(
            replace(_inputs(), correlation_id="CAUSE::D::1")
        )
    with pytest.raises(ContractValidationError):
        LatencyBudgetProfileV1(
            profile_id="MALFORMED",
            component_budget_ns=((STAGE_NAMES[0], 1), (STAGE_NAMES[0], 2)),
            histogram_boundaries_ns=(1,),
            maximum_observer_overhead_ns=1,
            alert_threshold_ns=1,
            policy_version="1",
        )

    graph = build_stage1_launch_graph_v2()
    forecast_selected_ids = (
        *graph.scope.selected_profile_ids[:2],
        graph.scope.excluded_profile_ids[0],
    )
    forecast_selected_scope = replace(
        graph.scope,
        selected_profile_ids=forecast_selected_ids,
        serialization=forecast_selected_ids,
    )
    duplicate_profile_scope = replace(
        graph.scope,
        profiles=(*graph.scope.profiles, graph.scope.profiles[0]),
    )
    duplicate_role_graph = replace(graph, roles=(*graph.roles, graph.roles[0]))
    missing_edge_graph = replace(
        graph,
        dependency_edges=graph.dependency_edges[:-1],
    )
    extra_edge_graph = replace(
        graph,
        dependency_edges=(*graph.dependency_edges, graph.dependency_edges[0]),
    )
    cycle_roles = tuple(
        replace(role, direct_prerequisite_role_ids=("ROLE-25",))
        if role.role_id == "ROLE-01"
        else role
        for role in graph.roles
    )
    orphan_operations = tuple(
        replace(
            operation,
            required_role_ids=tuple(
                role_id
                for role_id in operation.required_role_ids
                if role_id != "ROLE-27"
            ),
            optional_role_ids=tuple(
                role_id
                for role_id in operation.optional_role_ids
                if role_id != "ROLE-27"
            ),
        )
        for operation in graph.operation_profiles
    )
    writer_latency_class = next(
        role.latency_class for role in graph.roles if role.role_id == "ROLE-25"
    )
    second_writer_roles = tuple(
        replace(role, latency_class=writer_latency_class)
        if role.role_id == "ROLE-24"
        else role
        for role in graph.roles
    )
    nonempty_live_scope = replace(
        graph.scope,
        active_live_profile_ids=(graph.scope.selected_profile_ids[0],),
    )
    mutated_graphs = (
        replace(graph, scope=forecast_selected_scope),
        replace(graph, scope=duplicate_profile_scope),
        duplicate_role_graph,
        missing_edge_graph,
        extra_edge_graph,
        replace(graph, roles=cycle_roles),
        replace(graph, operation_profiles=orphan_operations),
        replace(graph, roles=second_writer_roles),
        replace(graph, scope=nonempty_live_scope),
    )
    for mutated_graph in mutated_graphs:
        rejection = validate_stage1_launch_graph_v2(mutated_graph)
        assert rejection.terminal_state.value == "REJECTED_INVALID"
        assert rejection.reason_codes

    with pytest.raises(ContractValidationError):
        replace(graph.scope.profiles[1], profile_id="POLYMARKET")
    with pytest.raises(SerializationSafetyError):
        replace(graph.roles[0].path_refs[0], path="../execution_router.py")
    future_path_ref = next(
        path_ref
        for role in graph.roles
        for path_ref in role.path_refs
        if path_ref.disposition.value
        == "FUTURE_AUTHORIZED_OWNER_NOT_YET_IMPLEMENTED"
    )
    with pytest.raises(ContractValidationError):
        replace(
            graph.roles[0].path_refs[0],
            disposition=future_path_ref.disposition,
        )
    with pytest.raises(ContractValidationError):
        replace(graph.no_effects, provider_connection_allowed=True)


def test_bounded_concurrency_is_deterministic_and_never_mutates_a_pointer() -> None:
    inputs = _inputs()
    with ThreadPoolExecutor(max_workers=4) as executor:
        results = tuple(executor.map(lambda _index: evaluate_mode_snapshot_candidate(inputs), range(8)))
    serialized = tuple(repr(result) for result in results)
    assert len(set(serialized)) == 1
    assert all(
        result.snapshot_transition_proposal.active_pointer_commit_allowed is False
        and result.snapshot_transition_proposal.mutation_allowed is False
        and result.mode_snapshot_decision.active_pointer_commit_allowed is False
        for result in results
    )
    cold = build_latency_measurement(
        measurement_ref="LATENCY::COLD",
        stage_values_ns=_stage_values(2),
        labels=replace(_labels(), cold_or_warm="COLD"),
    )
    concurrent = build_latency_measurement(
        measurement_ref="LATENCY::CONCURRENT",
        stage_values_ns=_stage_values(),
        labels=_labels(concurrency=4),
    )
    assert cold.labels.cold_or_warm == "COLD"
    assert concurrent.labels.concurrency_level == 4
    assert cold.runtime_effect_authorized is False
    assert concurrent.runtime_effect_authorized is False


def test_d_hotpath_sources_have_no_effect_or_escape_dependencies() -> None:
    root = Path(__file__).resolve().parents[3]
    package = root / "src/qtt/stage1_prediction_markets/qku_computation_control_plane"
    sources = {
        name: (package / name).read_text(encoding="utf-8")
        for name in ("mode_snapshot_policy.py", "latency_policy.py")
    }
    forbidden_import_roots = {
        "requests",
        "urllib",
        "httpx",
        "socket",
        "subprocess",
        "openai",
        "qiskit",
        "pennylane",
        "boto3",
    }
    forbidden_calls = {
        "eval",
        "exec",
        "open",
        "compile",
        "__import__",
        "system",
        "popen",
    }
    for source in sources.values():
        linux_tree = ast.parse(source.replace("\r\n", "\n"))
        windows_tree = ast.parse(source.replace("\n", "\r\n"))
        assert len(linux_tree.body) == len(windows_tree.body)
        imports = {
            alias.name.split(".", 1)[0]
            for node in ast.walk(linux_tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        } | {
            (node.module or "").split(".", 1)[0]
            for node in ast.walk(linux_tree)
            if isinstance(node, ast.ImportFrom) and node.level == 0
        }
        calls = {
            node.func.id
            for node in ast.walk(linux_tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        }
        declared_names = {
            node.name.lower()
            for node in ast.walk(linux_tree)
            if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
        }
        assert imports.isdisjoint(forbidden_import_roots)
        assert calls.isdisjoint(forbidden_calls)
        assert not any(
            token in name
            for name in declared_names
            for token in ("checksum", "digest", "sha_authority")
        )
        assert "active_pointer_commit_allowed=True" not in source.replace(" ", "")
        assert "runtime_effect_authorized=True" not in source.replace(" ", "")
        assert "order_release_authorized=True" not in source.replace(" ", "")
