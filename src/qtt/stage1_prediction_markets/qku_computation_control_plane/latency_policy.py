"""Pure ST12-D clock, latency, stale-fallback, and resource-bound policy."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import math
import platform
import time
from types import MappingProxyType
from typing import Callable, Mapping, TypeVar

from .errors import ContractValidationError, ReasonCode
from .models import (
    LatencyBudgetProfileV1,
    LatencyMeasurementLabelsV1,
    LatencyMeasurementV1,
    LatencyStageDurationsV1,
    ResourceBoundsProfileV1,
)


STAGE_NAMES = (
    "central_capability_admission_ns",
    "request_validation_ns",
    "identity_and_context_resolution_ns",
    "parameter_and_source_binding_ns",
    "snapshot_candidate_resolution_ns",
    "formula_compute_ns",
    "output_validation_ns",
    "receipt_materialization_ns",
    "owner_projection_ns",
)

CLOCK_REGISTRY: Mapping[str, tuple[str, str, str]] = MappingProxyType(
    {
        "LOCAL_DURATION": (
            "time.perf_counter_ns",
            "duration deltas only",
            "monotonic highest-resolution process/system performance counter",
        ),
        "LOCAL_DURATION_FALLBACK": (
            "time.monotonic_ns",
            "duration deltas only",
            "monotonic non-adjustable clock",
        ),
        "EVENT_CORRELATION": (
            "timezone-aware UTC wall clock",
            "never subtract for local latency",
            "cross-system event/correlation timestamps",
        ),
        "PROVIDER_EVENT_TIME": (
            "typed provider/source timestamp",
            "never treat as local duration without synchronization receipt",
            "source decomposition only after clock-domain declaration",
        ),
    }
)

ALLOWED_HOTPATH_DEPENDENCIES = frozenset(
    {
        "precomputed local immutable snapshot",
        "version-pinned pure deterministic computation",
        "bounded local validation",
        "append-only no-effect receipt proposal",
    }
)
FORBIDDEN_HOTPATH_DEPENDENCIES = frozenset(
    {
        "network",
        "filesystem search",
        "raw JSONL or global-library scan",
        "online source retrieval",
        "dashboard/mobile/chat work",
        "LLM inference",
        "REPLAY execution",
        "PAPER execution",
        "model training",
        "full-universe graph construction",
        "caller-selected dynamic imports",
        "package installation",
        "QPU execution",
        "quantum simulator execution",
        "provider connection",
        "private state access",
    }
)


@dataclass(frozen=True, slots=True)
class LatencyDistributionV1:
    count: int
    minimum_ns: int
    maximum_ns: int
    p50_ns: int
    p95_ns: int
    p99_ns: int


@dataclass(frozen=True, slots=True)
class ResourceUsageV1:
    input_cardinality: int
    input_bytes: int
    dependency_depth: int
    bootstrap_repetitions: int
    concurrency: int

    def __post_init__(self) -> None:
        for name in (
            "input_cardinality",
            "input_bytes",
            "dependency_depth",
            "bootstrap_repetitions",
            "concurrency",
        ):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ContractValidationError(
                    ReasonCode.CONTRACT_OR_TYPE_INVALID,
                    f"{name} must be explicit nonnegative integer usage",
                )


@dataclass(frozen=True, slots=True)
class LatencyPolicyDecisionV1:
    accepted_for_offline_measurement: bool
    promotion_sensitive_allow_blocked: bool
    reason_codes: tuple[ReasonCode, ...]
    terminal_route: str
    runtime_effect_authorized: bool = False

    def __post_init__(self) -> None:
        if (
            type(self.accepted_for_offline_measurement) is not bool
            or type(self.promotion_sensitive_allow_blocked) is not bool
            or not isinstance(self.reason_codes, tuple)
            or any(type(reason) is not ReasonCode for reason in self.reason_codes)
            or not isinstance(self.terminal_route, str)
            or not self.terminal_route
            or self.runtime_effect_authorized is not False
        ):
            raise ContractValidationError(
                ReasonCode.CONTRACT_OR_TYPE_INVALID,
                "latency policy decisions must be typed and no-effect",
            )


_T = TypeVar("_T")


def utc_event_time() -> datetime:
    """Wall-clock event/correlation timestamp; never a duration source."""

    return datetime.now(timezone.utc)


def local_duration_now_ns() -> int:
    """Highest-resolution monotonic local duration clock."""

    clock = getattr(time, "perf_counter_ns", None)
    return clock() if clock is not None else time.monotonic_ns()


def measure_callable(callable_: Callable[[], _T]) -> tuple[_T, int]:
    """Measure one bounded local callable without wall-clock subtraction."""

    if not callable(callable_):
        raise ContractValidationError(
            ReasonCode.CONTRACT_OR_TYPE_INVALID,
            "latency measurement target must be callable",
        )
    started = local_duration_now_ns()
    result = callable_()
    completed = local_duration_now_ns()
    if completed < started:
        raise ContractValidationError(
            ReasonCode.CLOCK_DOMAIN_MISMATCH,
            "monotonic clock moved backwards",
        )
    return result, completed - started


def latency_stage_durations(
    stage_values_ns: Mapping[str, int],
) -> LatencyStageDurationsV1:
    """Create the exact nine-stage decomposition from already measured values."""

    if not isinstance(stage_values_ns, Mapping) or set(stage_values_ns) != set(
        STAGE_NAMES
    ):
        raise ContractValidationError(
            ReasonCode.CONTRACT_OR_TYPE_INVALID,
            "latency decomposition requires exactly the nine frozen stages",
        )
    values = {name: stage_values_ns[name] for name in STAGE_NAMES}
    return LatencyStageDurationsV1(
        **values,
        total_local_no_effect_ns=sum(values.values()),
    )


def build_latency_measurement(
    *,
    measurement_ref: str,
    stage_values_ns: Mapping[str, int],
    labels: LatencyMeasurementLabelsV1,
    rejection_count: int = 0,
    observer_overhead_ns: int = 0,
    event_time_utc: datetime | None = None,
) -> LatencyMeasurementV1:
    stages = latency_stage_durations(stage_values_ns)
    cumulative: list[int] = []
    running = 0
    for name in STAGE_NAMES:
        running += getattr(stages, name)
        cumulative.append(running)
    clock_name = (
        "perf_counter" if getattr(time, "perf_counter_ns", None) is not None else "monotonic"
    )
    clock_info = time.get_clock_info(clock_name)
    return LatencyMeasurementV1(
        measurement_ref=measurement_ref,
        event_time_utc=event_time_utc or utc_event_time(),
        local_duration_clock_id=(
            "LOCAL_DURATION" if clock_name == "perf_counter" else "LOCAL_DURATION_FALLBACK"
        ),
        clock_implementation=clock_info.implementation,
        clock_resolution_ns=max(0, math.ceil(clock_info.resolution * 1_000_000_000)),
        platform_description=(
            f"{platform.system()}::{platform.machine()}::{platform.python_implementation()}"
        ),
        stages=stages,
        labels=labels,
        cumulative_stage_ns=tuple(cumulative),
        rejection_count=rejection_count,
        observer_overhead_ns=observer_overhead_ns,
    )


def _nearest_rank(sorted_values: tuple[int, ...], percentile: int) -> int:
    index = max(0, math.ceil(percentile * len(sorted_values) / 100) - 1)
    return sorted_values[index]


def aggregate_latency_samples(samples_ns: tuple[int, ...]) -> LatencyDistributionV1:
    if (
        not isinstance(samples_ns, tuple)
        or not samples_ns
        or any(
            isinstance(value, bool) or not isinstance(value, int) or value < 0
            for value in samples_ns
        )
    ):
        raise ContractValidationError(
            ReasonCode.CONTRACT_OR_TYPE_INVALID,
            "latency samples must be a nonempty immutable nanosecond tuple",
        )
    ordered = tuple(sorted(samples_ns))
    return LatencyDistributionV1(
        count=len(ordered),
        minimum_ns=ordered[0],
        maximum_ns=ordered[-1],
        p50_ns=_nearest_rank(ordered, 50),
        p95_ns=_nearest_rank(ordered, 95),
        p99_ns=_nearest_rank(ordered, 99),
    )


def evaluate_latency_profile(
    measurement: LatencyMeasurementV1,
    profile: LatencyBudgetProfileV1 | None,
) -> LatencyPolicyDecisionV1:
    """Missing owner profile permits offline measurement but blocks ALLOW."""

    if type(measurement) is not LatencyMeasurementV1:
        raise ContractValidationError(
            ReasonCode.CONTRACT_OR_TYPE_INVALID,
            "latency policy requires the exact typed measurement",
        )
    if profile is None:
        return LatencyPolicyDecisionV1(
            accepted_for_offline_measurement=True,
            promotion_sensitive_allow_blocked=True,
            reason_codes=(ReasonCode.LATENCY_PROFILE_REQUIRED,),
            terminal_route="OFFLINE_MEASUREMENT_ONLY_BLOCK_ALLOW_CANDIDACY",
        )
    if type(profile) is not LatencyBudgetProfileV1:
        raise ContractValidationError(
            ReasonCode.LATENCY_PROFILE_REQUIRED,
            "latency profile must be the exact owner-supplied contract",
        )
    budgets = dict(profile.component_budget_ns)
    missing = tuple(name for name in STAGE_NAMES if name not in budgets)
    exceeded = tuple(
        name for name in STAGE_NAMES if name in budgets and getattr(measurement.stages, name) > budgets[name]
    )
    observer_exceeded = (
        measurement.observer_overhead_ns > profile.maximum_observer_overhead_ns
    )
    if missing or exceeded or observer_exceeded:
        return LatencyPolicyDecisionV1(
            accepted_for_offline_measurement=True,
            promotion_sensitive_allow_blocked=True,
            reason_codes=(ReasonCode.LATENCY_PROFILE_REQUIRED,),
            terminal_route="OWNER_LATENCY_PROFILE_REVALIDATION",
        )
    return LatencyPolicyDecisionV1(
        accepted_for_offline_measurement=True,
        promotion_sensitive_allow_blocked=False,
        reason_codes=(),
        terminal_route="CONTINUE_NO_EFFECT",
    )


def validate_resource_bounds(
    usage: ResourceUsageV1,
    profile: ResourceBoundsProfileV1 | None,
) -> tuple[ReasonCode, ...]:
    if profile is None:
        return (ReasonCode.RESOURCE_BOUND_EXCEEDED,)
    if type(usage) is not ResourceUsageV1 or type(profile) is not ResourceBoundsProfileV1:
        raise ContractValidationError(
            ReasonCode.CONTRACT_OR_TYPE_INVALID,
            "resource checks require exact usage and owner profile contracts",
        )
    exceeded = (
        usage.input_cardinality > profile.maximum_input_cardinality
        or usage.input_bytes > profile.maximum_input_bytes
        or usage.dependency_depth > profile.maximum_dependency_depth
        or usage.bootstrap_repetitions > profile.maximum_bootstrap_repetitions
        or usage.concurrency > profile.maximum_concurrency
    )
    return (ReasonCode.RESOURCE_BOUND_EXCEEDED,) if exceeded else ()


def validate_hotpath_dependency_classes(
    dependency_classes: tuple[str, ...],
) -> tuple[ReasonCode, ...]:
    if (
        not isinstance(dependency_classes, tuple)
        or any(not isinstance(value, str) or not value for value in dependency_classes)
    ):
        raise ContractValidationError(
            ReasonCode.CONTRACT_OR_TYPE_INVALID,
            "dependency classes must be immutable canonical text",
        )
    if any(value in FORBIDDEN_HOTPATH_DEPENDENCIES for value in dependency_classes) or any(
        value not in ALLOWED_HOTPATH_DEPENDENCIES for value in dependency_classes
    ):
        return (ReasonCode.LATER_TRANCHE_AUTHORITY_REQUIRED,)
    return ()


def validate_trace_propagation(
    *,
    input_traceparent: str,
    input_tracestate: str,
    output_traceparent: str,
    output_tracestate: str,
) -> tuple[ReasonCode, ...]:
    """The request contract validates W3C syntax; D verifies exact propagation."""

    values = (input_traceparent, input_tracestate, output_traceparent, output_tracestate)
    if any(not isinstance(value, str) for value in values):
        raise ContractValidationError(
            ReasonCode.CONTRACT_OR_TYPE_INVALID,
            "trace propagation inputs must be text",
        )
    if (input_traceparent, input_tracestate) != (
        output_traceparent,
        output_tracestate,
    ):
        return (ReasonCode.IDENTITY_OR_VERSION_UNRESOLVED,)
    return ()


def stale_fallback(
    *,
    evaluated_at: datetime,
    valid_until: datetime,
    preapproved_fast_classical_fallback_ref: str | None,
) -> LatencyPolicyDecisionV1:
    for value in (evaluated_at, valid_until):
        if (
            not isinstance(value, datetime)
            or value.tzinfo is None
            or value.utcoffset() is None
            or value.utcoffset().total_seconds() != 0
        ):
            raise ContractValidationError(
                ReasonCode.CLOCK_DOMAIN_MISMATCH,
                "stale policy requires aware UTC event timestamps",
            )
    if evaluated_at <= valid_until:
        return LatencyPolicyDecisionV1(
            accepted_for_offline_measurement=True,
            promotion_sensitive_allow_blocked=False,
            reason_codes=(),
            terminal_route="CONTINUE_NO_EFFECT",
        )
    if preapproved_fast_classical_fallback_ref:
        return LatencyPolicyDecisionV1(
            accepted_for_offline_measurement=True,
            promotion_sensitive_allow_blocked=True,
            reason_codes=(ReasonCode.SNAPSHOT_STALE,),
            terminal_route="PREAPPROVED_FAST_CLASSICAL_FALLBACK_NO_EFFECT",
        )
    return LatencyPolicyDecisionV1(
        accepted_for_offline_measurement=True,
        promotion_sensitive_allow_blocked=True,
        reason_codes=(ReasonCode.SNAPSHOT_STALE,),
        terminal_route="NO_TRADE",
    )


if tuple(CLOCK_REGISTRY) != (
    "LOCAL_DURATION",
    "LOCAL_DURATION_FALLBACK",
    "EVENT_CORRELATION",
    "PROVIDER_EVENT_TIME",
) or len(STAGE_NAMES) != 9:
    raise RuntimeError("ST12-D latency registry closure is incomplete")
