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


def _evidence_clock_declarations_v1(declarations):
    """Declared native resolution is distinct from unqualified clock accuracy."""
    from collections.abc import Mapping
    from .context import _native_require
    from .serialization import _evidence_frozen_data_v1
    _native_require(isinstance(declarations, Mapping) and set(declarations) == {"wall", "monotonic", "process_cpu"},
                    "LP03_INVOCATION_CLOCK_DECLARATIONS")
    for declaration in declarations.values():
        _native_require(isinstance(declaration, Mapping) and set(declaration) == {
            "implementation", "reported_resolution_ns", "uncertainty_ns_or_absence"}
            and type(declaration["implementation"]) is str and 0 < len(declaration["implementation"]) <= 256,
            "LP03_INVOCATION_CLOCK_DECLARATION_FIELDS")
        resolution = declaration["reported_resolution_ns"]
        _native_require(type(resolution) in (tuple, list) and len(resolution) == 2
                        and all(type(item) is int and item > 0 for item in resolution), "LP03_INVOCATION_CLOCK_RESOLUTION")
        _native_require(declaration["uncertainty_ns_or_absence"] == {
            "state": "ABSENT_WITH_REASON", "reason": "NATIVE_CLOCK_ACCURACY_NOT_QUALIFIED"},
            "LP03_INVOCATION_CLOCK_UNCERTAINTY")
    _native_require(declarations["monotonic"]["implementation"] == "QueryPerformanceCounter()",
                    "LP03_INVOCATION_MONOTONIC_IMPLEMENTATION")
    return _evidence_frozen_data_v1(declarations)


def _evidence_invocation_measurement_v1(value):
    """Strict original-clock invocation data, including failed-call duration."""
    from collections.abc import Mapping
    from .context import _native_require, _native_ident, _public_counter_v1
    from .serialization import _evidence_frozen_data_v1
    _native_require(isinstance(value, Mapping) and set(value) == {
        "clock_domain_id", "boot_identity_ref", "process_identity_ref", "clock_declarations",
        "started", "completed", "duration_ns", "cpu_ns", "outcome"},
        "LP03_INVOCATION_MEASUREMENT_FIELDS")
    for name in ("clock_domain_id", "boot_identity_ref", "process_identity_ref"):
        _native_ident(value[name])
    _evidence_clock_declarations_v1(value["clock_declarations"])
    for name in ("started", "completed"):
        _native_require(type(value[name]) in (tuple, list) and len(value[name]) == 3, "LP03_INVOCATION_CLOCK_SHAPE")
        for number in value[name]:
            _public_counter_v1(number, allow_zero=True)
    for name in ("duration_ns", "cpu_ns"):
        _public_counter_v1(value[name], allow_zero=True)
    _native_require(all(end >= start for start, end in zip(value["started"], value["completed"]))
                    and value["duration_ns"] == value["completed"][1] - value["started"][1]
                    and value["cpu_ns"] == value["completed"][2] - value["started"][2]
                    and type(value["outcome"]) is str and value["outcome"] in ("SUCCESS", "FAILED"),
                    "LP03_INVOCATION_MEASUREMENT_JOIN")
    return _evidence_frozen_data_v1(value)


def _evidence_storage_observation_v1(value):
    """Strict native observation data; no claimed availability or permission."""
    from collections.abc import Mapping
    from .context import _native_require, _native_ident, _public_counter_v1
    from .serialization import _evidence_frozen_data_v1
    _native_require(isinstance(value, Mapping) and set(value) == {"wall_ns", "monotonic_ns", "process_cpu_ns",
        "clock_domain_id", "process_identity_ref", "boot_identity_ref", "clock_declarations"}, "LP03_STORAGE_OBSERVATION_FIELDS")
    for name in ("wall_ns", "monotonic_ns", "process_cpu_ns"):
        _public_counter_v1(value[name], allow_zero=True)
    for name in ("clock_domain_id", "process_identity_ref", "boot_identity_ref"):
        _native_ident(value[name])
    _evidence_clock_declarations_v1(value["clock_declarations"])
    return _evidence_frozen_data_v1(value)


class _EvidenceLocalClockV1:
    """Original local clock/process observations; never restored from a record.

    The Windows boot query is dynamically bound and explicitly unavailable if
    the host does not return the qualified shape. This observes identity only;
    it changes neither the clock nor any operating-system configuration.
    """

    __slots__ = ("_kernel", "_ntdll", "_process", "_identity", "__functions", "__declarations",
                 "clock_domain_id", "process_identity_ref", "boot_identity_ref")

    def __init__(self):
        import ctypes
        import os
        import sys
        from types import BuiltinFunctionType
        from .context import _native_require

        _native_require(os.name == "nt" and sys.platform == "win32" and ctypes.sizeof(ctypes.c_void_p) == 8,
                        "LP03_ORIGINAL_LOCAL_CLOCK_UNAVAILABLE")
        functions = (time.time_ns, time.monotonic_ns, time.process_time_ns)
        _native_require(all(type(fn) is BuiltinFunctionType for fn in functions), "LP03_NATIVE_CLOCK_REQUIRED")
        info = time.get_clock_info("monotonic")
        _native_require(info.monotonic and not info.adjustable
                        and info.implementation == "QueryPerformanceCounter()", "LP03_ORIGINAL_CLOCK_DOMAIN")
        kernel = ctypes.WinDLL("kernel32.dll", use_last_error=True, winmode=0x800)
        ntdll = ctypes.WinDLL("ntdll.dll", use_last_error=True, winmode=0x800)
        handle, u32, u64 = ctypes.c_void_p, ctypes.c_uint32, ctypes.c_uint64
        kernel.GetCurrentProcess.argtypes, kernel.GetCurrentProcess.restype = [], handle
        kernel.GetProcessId.argtypes, kernel.GetProcessId.restype = [handle], u32
        kernel.GetProcessTimes.argtypes = [handle] + [ctypes.POINTER(u64)] * 4
        kernel.GetProcessTimes.restype = ctypes.c_int32
        kernel.QueryPerformanceFrequency.argtypes = [ctypes.POINTER(ctypes.c_int64)]
        kernel.QueryPerformanceFrequency.restype = ctypes.c_int32
        ntdll.NtQuerySystemInformation.argtypes = [u32, handle, u32, ctypes.POINTER(u32)]
        ntdll.NtQuerySystemInformation.restype = ctypes.c_int32
        self._kernel, self._ntdll, self._process = kernel, ntdll, kernel.GetCurrentProcess()
        self.__functions = functions
        self._identity = _EvidenceLocalClockV1._native_identity_v1(self)
        pid, creation, boot, frequency = self._identity
        self.boot_identity_ref = "LP03-BOOT::" + boot.hex()
        self.process_identity_ref = f"LP03-PROCESS::{pid}:{creation}:{boot.hex()}"
        self.clock_domain_id = f"LP03-QPC::{frequency}:{boot.hex()}"
        from fractions import Fraction
        from .serialization import _evidence_frozen_data_v1
        declarations = {}
        for label, name in (("wall", "time"), ("monotonic", "monotonic"), ("process_cpu", "process_time")):
            info = time.get_clock_info(name)
            resolution = Fraction(str(info.resolution)) * 1_000_000_000
            declarations[label] = dict(implementation=info.implementation,
                reported_resolution_ns=(resolution.numerator, resolution.denominator),
                uncertainty_ns_or_absence=dict(state="ABSENT_WITH_REASON", reason="NATIVE_CLOCK_ACCURACY_NOT_QUALIFIED"))
        self.__declarations = _evidence_frozen_data_v1(declarations)

    def declaration_v1(self):
        return self.__declarations

    def _native_identity_v1(self):
        import ctypes
        from .context import _native_require

        created, ended, kernel_time, user_time = (ctypes.c_uint64() for _ in range(4))
        _native_require(bool(self._kernel.GetProcessTimes(self._process, ctypes.byref(created), ctypes.byref(ended),
                        ctypes.byref(kernel_time), ctypes.byref(user_time))), "LP03_ORIGINAL_PROCESS_CLOCK_UNAVAILABLE")
        pid = self._kernel.GetProcessId(self._process)
        boot = (ctypes.c_ubyte * 32)()
        length, frequency = ctypes.c_uint32(), ctypes.c_int64()
        # SystemBootEnvironmentInformation, Windows 8+ 32-byte layout. The
        # first 16 bytes are the original boot GUID, not a generated label.
        status = self._ntdll.NtQuerySystemInformation(90, boot, 32, ctypes.byref(length))
        _native_require(status == 0 and length.value == 32 and any(boot[:16])
                        and pid > 0 and created.value > 0 and ended.value == 0,
                        "LP03_ORIGINAL_BOOT_PROCESS_UNAVAILABLE")
        _native_require(bool(self._kernel.QueryPerformanceFrequency(ctypes.byref(frequency)))
                        and frequency.value > 0, "LP03_ORIGINAL_CLOCK_FREQUENCY_UNAVAILABLE")
        return pid, created.value, bytes(boot[:16]), frequency.value

    def observe_v1(self):
        from .context import _native_require
        _native_require(type(self) is _EvidenceLocalClockV1
                        and _EvidenceLocalClockV1._native_identity_v1(self) == self._identity,
                        "LP03_ORIGINAL_CLOCK_PROCESS_CHANGED")
        wall, mono, cpu = self.__functions
        return wall(), mono(), cpu()

    def __copy__(self):
        raise TypeError("LP03 local clock cannot be copied")

    def __deepcopy__(self, memo):
        raise TypeError("LP03 local clock cannot be copied")

    def __reduce_ex__(self, protocol):
        raise TypeError("LP03 local clock cannot be serialized")

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
class LatencyDistributionV2:
    """Exact observed sample ranks; no inferred unobserved population tail."""

    count: int
    minimum_ns: int
    maximum_ns: int
    p50_ns: int
    p95_ns: int
    p99_ns: int
    p999_ns: int

    def __post_init__(self):
        from .context import _native_require, _public_counter_v1
        _public_counter_v1(self.count)
        ordered = (self.minimum_ns, self.p50_ns, self.p95_ns, self.p99_ns, self.p999_ns, self.maximum_ns)
        for value in ordered:
            _public_counter_v1(value, allow_zero=True)
        _native_require(all(left <= right for left, right in zip(ordered, ordered[1:])), "LP03_LATENCY_QUANTILE_ORDER")


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


def evidence_nearest_rank_v1(count, numerator, denominator):
    """One-based rational rank, with bounded exact integer operands."""
    from .context import _native_require, _public_counter_v1
    for value in (count, numerator, denominator):
        _public_counter_v1(value)
    _native_require(numerator <= denominator, "LP03_LATENCY_PERCENTILE_DOMAIN")
    # Each operand is <2**63 before multiplication; no binary64 rank rounding.
    return (count * numerator + denominator - 1) // denominator


def _nearest_rank(sorted_values: tuple[int, ...], percentile: int) -> int:
    return sorted_values[evidence_nearest_rank_v1(len(sorted_values), percentile, 100) - 1]


def aggregate_evidence_latency_samples_v1(samples_ns):
    """Summarize only the supplied observed population, preserving V1 shape."""
    from .context import _native_require, _public_counter_v1
    _native_require(type(samples_ns) is tuple and bool(samples_ns), "LP03_LATENCY_SAMPLE_TUPLE_REQUIRED")
    _public_counter_v1(len(samples_ns))
    for sample in samples_ns:
        _public_counter_v1(sample, allow_zero=True)
    ordered = tuple(sorted(samples_ns))
    quantiles = tuple(ordered[evidence_nearest_rank_v1(len(ordered), numerator, denominator) - 1]
                      for numerator, denominator in ((1, 2), (19, 20), (99, 100), (999, 1000)))
    return LatencyDistributionV2(len(ordered), ordered[0], ordered[-1], *quantiles)


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
