"""Field, component, stack, TTL, and monotonic-deadline resolution."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from enum import StrEnum
from hashlib import sha256
from time import monotonic
from typing import Callable

from .context import ComputationContextKeyV1, exact_decimal, parse_utc
from .errors import FreshnessError, ReasonCode


class FreshnessStateV1(StrEnum):
    FRESH = "FRESH"
    STALE = "STALE"
    UNKNOWN_FAIL_CLOSED = "UNKNOWN_FAIL_CLOSED"


class DeadlineStateV1(StrEnum):
    WITHIN_BUDGET = "WITHIN_BUDGET"
    EXHAUSTED = "EXHAUSTED"


def _required_text(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise FreshnessError(
            ReasonCode.INVALID_CONTRACT,
            f"{field_name} must be nonempty text",
        )
    return value


@dataclass(frozen=True, slots=True)
class FreshnessPolicyV1:
    policy_id: str
    ttl: timedelta | None
    parameter_policy_ref: str
    stale_behavior: str

    def __post_init__(self) -> None:
        for name in ("policy_id", "parameter_policy_ref", "stale_behavior"):
            _required_text(getattr(self, name), name)
        if self.ttl is not None and (
            not isinstance(self.ttl, timedelta) or self.ttl <= timedelta(0)
        ):
            raise FreshnessError(
                ReasonCode.INVALID_CONTRACT,
                "a declared TTL must be a positive timedelta",
            )


@dataclass(frozen=True, slots=True)
class FreshnessReceiptV1:
    receipt_id: str
    subject_id: str
    scope: str
    state: FreshnessStateV1
    observed_time: datetime | None
    as_of_time: datetime
    ttl: timedelta | None
    age: timedelta | None
    material_dependency_refs: tuple[str, ...]
    blocker_codes: tuple[ReasonCode, ...]
    terminal_route: str
    no_authority_flag: bool = True

    def __post_init__(self) -> None:
        for name in ("receipt_id", "subject_id", "scope", "terminal_route"):
            _required_text(getattr(self, name), name)
        if not isinstance(self.state, FreshnessStateV1):
            raise FreshnessError(
                ReasonCode.INVALID_CONTRACT,
                "freshness state must be typed",
            )
        object.__setattr__(
            self,
            "as_of_time",
            parse_utc(self.as_of_time, field_name="as_of_time"),
        )
        if self.observed_time is not None:
            object.__setattr__(
                self,
                "observed_time",
                parse_utc(self.observed_time, field_name="observed_time"),
            )
        if (
            not isinstance(self.material_dependency_refs, tuple)
            or any(
                not isinstance(ref, str) or not ref
                for ref in self.material_dependency_refs
            )
            or len(set(self.material_dependency_refs))
            != len(self.material_dependency_refs)
        ):
            raise FreshnessError(
                ReasonCode.INVALID_CONTRACT,
                "material dependency refs must be a unique text tuple",
            )
        if (
            not isinstance(self.blocker_codes, tuple)
            or any(not isinstance(code, ReasonCode) for code in self.blocker_codes)
            or len(set(self.blocker_codes)) != len(self.blocker_codes)
        ):
            raise FreshnessError(
                ReasonCode.INVALID_CONTRACT,
                "freshness blockers must be a unique typed tuple",
            )
        if (self.state is FreshnessStateV1.FRESH) == bool(self.blocker_codes):
            raise FreshnessError(
                ReasonCode.INVALID_CONTRACT,
                "fresh receipts have no blocker and nonfresh receipts require one",
            )
        if type(self.no_authority_flag) is not bool or not self.no_authority_flag:
            raise FreshnessError(
                ReasonCode.CAPABILITY_DENIED,
                "freshness receipts cannot create authority",
            )

    @property
    def fresh(self) -> bool:
        return self.state is FreshnessStateV1.FRESH


@dataclass(frozen=True, slots=True)
class DeadlineBudgetV1:
    deadline_id: str
    budget_seconds: Decimal
    parameter_policy_ref: str
    started_monotonic: Decimal

    def __post_init__(self) -> None:
        _required_text(self.deadline_id, "deadline_id")
        _required_text(self.parameter_policy_ref, "parameter_policy_ref")
        budget = exact_decimal(
            self.budget_seconds,
            field_name="budget_seconds",
        )
        started = exact_decimal(
            self.started_monotonic,
            field_name="started_monotonic",
        )
        if budget <= 0 or started < 0:
            raise FreshnessError(
                ReasonCode.INVALID_CONTRACT,
                "deadline budget must be positive and monotonic origin nonnegative",
            )
        object.__setattr__(self, "budget_seconds", budget)
        object.__setattr__(self, "started_monotonic", started)

    @classmethod
    def start(
        cls,
        *,
        deadline_id: str,
        budget_seconds: Decimal | str | int,
        parameter_policy_ref: str,
        monotonic_clock: Callable[[], float] = monotonic,
    ) -> "DeadlineBudgetV1":
        return cls(
            deadline_id=deadline_id,
            budget_seconds=exact_decimal(
                budget_seconds,
                field_name="budget_seconds",
            ),
            parameter_policy_ref=parameter_policy_ref,
            started_monotonic=exact_decimal(
                repr(monotonic_clock()),
                field_name="started_monotonic",
            ),
        )


@dataclass(frozen=True, slots=True)
class DeadlineReceiptV1:
    receipt_id: str
    deadline_id: str
    state: DeadlineStateV1
    budget_seconds: Decimal
    elapsed_seconds: Decimal
    blocker_codes: tuple[ReasonCode, ...]
    fallback_route: str
    no_authority_flag: bool = True

    @property
    def within_budget(self) -> bool:
        return self.state is DeadlineStateV1.WITHIN_BUDGET


class FreshnessResolverV1:
    """Compose the A context rule with exact field and closure semantics."""

    @staticmethod
    def resolve_field(
        *,
        subject_id: str,
        observed_time: datetime | None,
        as_of_time: datetime,
        policy: FreshnessPolicyV1,
        material: bool = True,
    ) -> FreshnessReceiptV1:
        _required_text(subject_id, "subject_id")
        if not isinstance(policy, FreshnessPolicyV1):
            raise FreshnessError(
                ReasonCode.INVALID_CONTRACT,
                "freshness policy must be typed",
            )
        if type(material) is not bool:
            raise FreshnessError(
                ReasonCode.INVALID_CONTRACT,
                "material must be an exact boolean",
            )
        as_of = parse_utc(as_of_time, field_name="as_of_time")
        observed = (
            None
            if observed_time is None
            else parse_utc(observed_time, field_name="observed_time")
        )
        age = None if observed is None else as_of - observed
        if observed is None or policy.ttl is None or age is None or age < timedelta(0):
            state = FreshnessStateV1.UNKNOWN_FAIL_CLOSED
            blockers = (ReasonCode.FRESHNESS_UNKNOWN,)
        elif age > policy.ttl:
            state = FreshnessStateV1.STALE
            blockers = (ReasonCode.FIELD_STALE,)
        else:
            state = FreshnessStateV1.FRESH
            blockers = ()
        digest = "|".join(
            (
                subject_id,
                as_of.isoformat(),
                "" if observed is None else observed.isoformat(),
                policy.policy_id,
                state.value,
                "MATERIAL" if material else "OPTIONAL",
            )
        )
        return FreshnessReceiptV1(
            receipt_id=f"FRESH::{sha256(digest.encode('utf-8')).hexdigest()}",
            subject_id=subject_id,
            scope="FIELD",
            state=state,
            observed_time=observed,
            as_of_time=as_of,
            ttl=policy.ttl,
            age=age,
            material_dependency_refs=(),
            blocker_codes=blockers,
            terminal_route=(
                "QKUComputationControlPlaneV1"
                if state is FreshnessStateV1.FRESH
                else "risk_manager_agent::FRESHNESS_REBIND_OR_REGISTERED_FALLBACK"
            ),
        )

    @staticmethod
    def resolve_context(
        context: ComputationContextKeyV1,
    ) -> FreshnessReceiptV1:
        if not isinstance(context, ComputationContextKeyV1):
            raise FreshnessError(
                ReasonCode.INVALID_CONTRACT,
                "context must be ComputationContextKeyV1",
            )
        policy = FreshnessPolicyV1(
            policy_id="ComputationContextKeyV1.maximum_age",
            ttl=context.maximum_age,
            parameter_policy_ref="ComputationContextKeyV1.maximum_age",
            stale_behavior="FAIL_CLOSED",
        )
        receipt = FreshnessResolverV1.resolve_field(
            subject_id=context.context_id,
            observed_time=context.observed_at,
            as_of_time=context.as_of,
            policy=policy,
        )
        try:
            context.assert_fresh()
        except ValueError:
            if receipt.state is FreshnessStateV1.FRESH:
                raise FreshnessError(
                    ReasonCode.INVALID_CONTRACT,
                    "context and field freshness rules disagree",
                )
        return receipt

    @staticmethod
    def resolve_closure(
        *,
        subject_id: str,
        scope: str,
        dependencies: tuple[tuple[FreshnessReceiptV1, bool], ...],
        as_of_time: datetime,
    ) -> FreshnessReceiptV1:
        if scope not in {"COMPONENT", "STACK"}:
            raise FreshnessError(
                ReasonCode.INVALID_CONTRACT,
                "closure freshness scope must be COMPONENT or STACK",
            )
        if (
            not isinstance(dependencies, tuple)
            or any(
                not isinstance(receipt, FreshnessReceiptV1)
                or type(material) is not bool
                for receipt, material in dependencies
            )
        ):
            raise FreshnessError(
                ReasonCode.INVALID_CONTRACT,
                "freshness dependencies must be typed immutable pairs",
            )
        material_receipts = tuple(
            receipt for receipt, material in dependencies if material
        )
        states = {receipt.state for receipt in material_receipts}
        if FreshnessStateV1.UNKNOWN_FAIL_CLOSED in states:
            state = FreshnessStateV1.UNKNOWN_FAIL_CLOSED
            blockers = (ReasonCode.FRESHNESS_UNKNOWN,)
        elif FreshnessStateV1.STALE in states:
            state = FreshnessStateV1.STALE
            blockers = (ReasonCode.FIELD_STALE,)
        else:
            state = FreshnessStateV1.FRESH
            blockers = ()
        as_of = parse_utc(as_of_time, field_name="as_of_time")
        refs = tuple(receipt.receipt_id for receipt in material_receipts)
        digest = "|".join((subject_id, scope, as_of.isoformat(), state.value, *refs))
        return FreshnessReceiptV1(
            receipt_id=f"FRESH::{sha256(digest.encode('utf-8')).hexdigest()}",
            subject_id=subject_id,
            scope=scope,
            state=state,
            observed_time=None,
            as_of_time=as_of,
            ttl=None,
            age=None,
            material_dependency_refs=refs,
            blocker_codes=blockers,
            terminal_route=(
                "QKUComputationControlPlaneV1"
                if state is FreshnessStateV1.FRESH
                else "risk_manager_agent::FRESHNESS_REBIND_OR_REGISTERED_FALLBACK"
            ),
        )


class DeadlineResolverV1:
    @staticmethod
    def resolve(
        budget: DeadlineBudgetV1,
        *,
        monotonic_clock: Callable[[], float] = monotonic,
    ) -> DeadlineReceiptV1:
        if not isinstance(budget, DeadlineBudgetV1):
            raise FreshnessError(
                ReasonCode.INVALID_CONTRACT,
                "deadline budget must be typed",
            )
        now = exact_decimal(
            repr(monotonic_clock()),
            field_name="current_monotonic",
        )
        elapsed = now - budget.started_monotonic
        if elapsed < 0:
            raise FreshnessError(
                ReasonCode.INVALID_CONTRACT,
                "monotonic clock moved backward",
            )
        exhausted = elapsed > budget.budget_seconds
        state = (
            DeadlineStateV1.EXHAUSTED
            if exhausted
            else DeadlineStateV1.WITHIN_BUDGET
        )
        blockers = (ReasonCode.DEADLINE_EXHAUSTED,) if exhausted else ()
        digest = "|".join(
            (
                budget.deadline_id,
                str(budget.budget_seconds),
                str(elapsed),
                state.value,
            )
        )
        return DeadlineReceiptV1(
            receipt_id=f"DEADLINE::{sha256(digest.encode('utf-8')).hexdigest()}",
            deadline_id=budget.deadline_id,
            state=state,
            budget_seconds=budget.budget_seconds,
            elapsed_seconds=elapsed,
            blocker_codes=blockers,
            fallback_route=(
                "CONTINUE_PURE_COMPUTATION"
                if not exhausted
                else "commander_agent::REGISTERED_FAST_CLASSICAL_OR_NO_TRADE"
            ),
        )
