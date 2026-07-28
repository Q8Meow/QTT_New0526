"""Deterministic unit/basis conversion with exact Decimal lineage."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import (
    Decimal,
    ROUND_CEILING,
    ROUND_DOWN,
    ROUND_FLOOR,
    ROUND_HALF_EVEN,
    ROUND_HALF_UP,
    ROUND_UP,
    localcontext,
)
from hashlib import sha256
from types import MappingProxyType
from typing import Mapping

from .context import decimal_context_v1, exact_decimal, parse_utc
from .dependency_graph import UnitConversionV1
from .errors import ReasonCode, UnitConversionError


_ROUNDING_RULES = MappingProxyType(
    {
        "ROUND_HALF_EVEN": ROUND_HALF_EVEN,
        "ROUND_HALF_UP": ROUND_HALF_UP,
        "ROUND_DOWN": ROUND_DOWN,
        "ROUND_UP": ROUND_UP,
        "ROUND_FLOOR": ROUND_FLOOR,
        "ROUND_CEILING": ROUND_CEILING,
    }
)
_SEMANTIC_BOUNDARY_TOKENS = (
    ("percent", "fraction"),
    ("per_contract", "total"),
    ("gross", "net"),
)


def _required_text(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise UnitConversionError(
            ReasonCode.INVALID_CONTRACT,
            f"{field_name} must be nonempty text",
        )
    return value


@dataclass(frozen=True, slots=True)
class RegisteredUnitConversionV1:
    conversion_id: str
    identity: UnitConversionV1
    supplied_basis: str
    required_basis: str
    precision_quantum: Decimal | None
    rounding_rule: str | None
    source_claim_ref: str
    supplied_currency: str | None = None
    required_currency: str | None = None
    currency_source_state_id: str | None = None
    source_epoch_id: str | None = None
    as_of_time: datetime | None = None

    def __post_init__(self) -> None:
        _required_text(self.conversion_id, "conversion_id")
        if not isinstance(self.identity, UnitConversionV1):
            raise UnitConversionError(
                ReasonCode.INVALID_CONTRACT,
                "conversion identity must reuse UnitConversionV1",
            )
        if (
            self.identity.supplied_basis != "declared"
            and self.identity.supplied_basis != self.supplied_basis
        ) or (
            self.identity.required_basis != "declared"
            and self.identity.required_basis != self.required_basis
        ):
            raise UnitConversionError(
                ReasonCode.INVALID_CONTRACT,
                "conversion identity and registered bases disagree",
            )
        for name in ("supplied_basis", "required_basis", "source_claim_ref"):
            _required_text(getattr(self, name), name)
        if (self.precision_quantum is None) != (self.rounding_rule is None):
            raise UnitConversionError(
                ReasonCode.PRECISION_BOUNDARY_INVALID,
                "precision quantum and rounding rule must be declared together",
            )
        if self.precision_quantum is not None:
            quantum = exact_decimal(
                self.precision_quantum,
                field_name="precision_quantum",
            )
            if quantum <= 0 or self.rounding_rule not in _ROUNDING_RULES:
                raise UnitConversionError(
                    ReasonCode.PRECISION_BOUNDARY_INVALID,
                    "precision quantum must be positive with a certified rounding rule",
                )
            object.__setattr__(self, "precision_quantum", quantum)

        currency_fields = (
            self.supplied_currency,
            self.required_currency,
            self.currency_source_state_id,
            self.source_epoch_id,
            self.as_of_time,
        )
        if any(value is not None for value in currency_fields):
            if any(value is None for value in currency_fields):
                raise UnitConversionError(
                    ReasonCode.BASIS_CONVERSION_FORBIDDEN,
                    "currency conversion requires currencies, source, epoch, and as-of",
                )
            for name in (
                "supplied_currency",
                "required_currency",
                "currency_source_state_id",
                "source_epoch_id",
            ):
                _required_text(getattr(self, name), name)
            object.__setattr__(
                self,
                "as_of_time",
                parse_utc(self.as_of_time, field_name="as_of_time"),
            )

    @property
    def source_key(self) -> tuple[str, str, str | None]:
        return (
            self.identity.supplied_unit,
            self.supplied_basis,
            self.supplied_currency,
        )

    @property
    def target_key(self) -> tuple[str, str, str | None]:
        return (
            self.identity.required_unit,
            self.required_basis,
            self.required_currency,
        )


@dataclass(frozen=True, slots=True)
class UnitConversionStepReceiptV1:
    conversion_id: str
    supplied_value: Decimal
    factor: Decimal
    unrounded_value: Decimal
    resolved_value: Decimal
    supplied_unit: str
    required_unit: str
    supplied_basis: str
    required_basis: str
    precision_quantum: Decimal | None
    rounding_rule: str | None
    source_claim_ref: str
    source_epoch_id: str | None


@dataclass(frozen=True, slots=True)
class UnitConversionReceiptV1:
    receipt_id: str
    supplied_value: Decimal
    resolved_value: Decimal
    supplied_unit: str
    required_unit: str
    supplied_basis: str
    required_basis: str
    conversion_path: tuple[str, ...]
    steps: tuple[UnitConversionStepReceiptV1, ...]
    precision_boundary_applied: bool
    no_source_truth_created: bool = True
    no_authority_flag: bool = True

    def __post_init__(self) -> None:
        if (
            type(self.no_source_truth_created) is not bool
            or not self.no_source_truth_created
            or type(self.no_authority_flag) is not bool
            or not self.no_authority_flag
        ):
            raise UnitConversionError(
                ReasonCode.CAPABILITY_DENIED,
                "conversion receipts cannot create source truth or authority",
            )


class UnitConversionRegistryV1:
    """An immutable registry that rejects cycles and ambiguous paths."""

    def __init__(
        self,
        conversions: tuple[RegisteredUnitConversionV1, ...] = (),
    ) -> None:
        if (
            not isinstance(conversions, tuple)
            or any(
                not isinstance(item, RegisteredUnitConversionV1)
                for item in conversions
            )
        ):
            raise UnitConversionError(
                ReasonCode.INVALID_CONTRACT,
                "conversions must be a typed immutable tuple",
            )
        ids = tuple(item.conversion_id for item in conversions)
        edges = tuple((item.source_key, item.target_key) for item in conversions)
        if len(ids) != len(set(ids)) or len(edges) != len(set(edges)):
            raise UnitConversionError(
                ReasonCode.UNIT_CONVERSION_AMBIGUOUS,
                "conversion ids and directed endpoints must be unique",
            )
        if any(source == target for source, target in edges):
            raise UnitConversionError(
                ReasonCode.UNIT_CONVERSION_CYCLE,
                "identity conversions are implicit and may not be registered",
            )
        self._conversions = conversions
        self._by_source: Mapping[
            tuple[str, str, str | None],
            tuple[RegisteredUnitConversionV1, ...],
        ] = MappingProxyType(
            {
                source: tuple(
                    item for item in conversions if item.source_key == source
                )
                for source in {item.source_key for item in conversions}
            }
        )
        self._assert_acyclic()
        self._assert_unique_paths()

    @property
    def conversions(self) -> tuple[RegisteredUnitConversionV1, ...]:
        return self._conversions

    def _all_paths(
        self,
        source: tuple[str, str, str | None],
        target: tuple[str, str, str | None],
        visited: frozenset[tuple[str, str, str | None]] = frozenset(),
    ) -> tuple[tuple[RegisteredUnitConversionV1, ...], ...]:
        if source == target:
            return ((),)
        if source in visited:
            return ()
        paths: list[tuple[RegisteredUnitConversionV1, ...]] = []
        for edge in self._by_source.get(source, ()):
            for suffix in self._all_paths(
                edge.target_key,
                target,
                visited | {source},
            ):
                paths.append((edge, *suffix))
        return tuple(paths)

    def _assert_acyclic(self) -> None:
        visiting: set[tuple[str, str, str | None]] = set()
        visited: set[tuple[str, str, str | None]] = set()

        def visit(node: tuple[str, str, str | None]) -> None:
            if node in visiting:
                raise UnitConversionError(
                    ReasonCode.UNIT_CONVERSION_CYCLE,
                    "conversion graph contains a cycle",
                )
            if node in visited:
                return
            visiting.add(node)
            for edge in self._by_source.get(node, ()):
                visit(edge.target_key)
            visiting.remove(node)
            visited.add(node)

        for node in self._by_source:
            visit(node)

    def _assert_unique_paths(self) -> None:
        endpoints = {
            endpoint
            for item in self._conversions
            for endpoint in (item.source_key, item.target_key)
        }
        for source in endpoints:
            for target in endpoints:
                if source != target and len(self._all_paths(source, target)) > 1:
                    raise UnitConversionError(
                        ReasonCode.UNIT_CONVERSION_AMBIGUOUS,
                        f"multiple conversion paths exist for {source!r} -> {target!r}",
                    )

    def resolve(
        self,
        *,
        value: Decimal | str | int,
        supplied_unit: str,
        required_unit: str,
        supplied_basis: str,
        required_basis: str,
        supplied_currency: str | None = None,
        required_currency: str | None = None,
        source_epoch_id: str | None = None,
        as_of_time: datetime | None = None,
    ) -> UnitConversionReceiptV1:
        supplied = exact_decimal(value, field_name="conversion_value")
        for name, item in (
            ("supplied_unit", supplied_unit),
            ("required_unit", required_unit),
            ("supplied_basis", supplied_basis),
            ("required_basis", required_basis),
        ):
            _required_text(item, name)
        source = (supplied_unit, supplied_basis, supplied_currency)
        target = (required_unit, required_basis, required_currency)
        if source == target:
            digest = sha256(
                f"{supplied}|{source!r}|IDENTITY".encode("utf-8")
            ).hexdigest()
            return UnitConversionReceiptV1(
                receipt_id=f"CONVERSION::{digest}",
                supplied_value=supplied,
                resolved_value=supplied,
                supplied_unit=supplied_unit,
                required_unit=required_unit,
                supplied_basis=supplied_basis,
                required_basis=required_basis,
                conversion_path=(),
                steps=(),
                precision_boundary_applied=False,
            )

        paths = self._all_paths(source, target)
        if not paths:
            semantic_change = any(
                (
                    left in f"{supplied_unit}|{supplied_basis}".casefold()
                    and right in f"{required_unit}|{required_basis}".casefold()
                )
                or (
                    right in f"{supplied_unit}|{supplied_basis}".casefold()
                    and left in f"{required_unit}|{required_basis}".casefold()
                )
                for left, right in _SEMANTIC_BOUNDARY_TOKENS
            )
            raise UnitConversionError(
                (
                    ReasonCode.BASIS_CONVERSION_FORBIDDEN
                    if semantic_change
                    else ReasonCode.UNIT_CONVERSION_UNKNOWN
                ),
                f"no registered conversion exists for {source!r} -> {target!r}",
            )
        if len(paths) != 1:
            raise UnitConversionError(
                ReasonCode.UNIT_CONVERSION_AMBIGUOUS,
                f"conversion path is not unique for {source!r} -> {target!r}",
            )

        current = supplied
        steps: list[UnitConversionStepReceiptV1] = []
        for edge in paths[0]:
            if edge.source_epoch_id is not None:
                if source_epoch_id != edge.source_epoch_id or as_of_time is None:
                    raise UnitConversionError(
                        ReasonCode.BASIS_CONVERSION_FORBIDDEN,
                        "currency conversion source epoch/as-of binding is missing",
                    )
                requested_as_of = parse_utc(as_of_time, field_name="as_of_time")
                if requested_as_of != edge.as_of_time:
                    raise UnitConversionError(
                        ReasonCode.BASIS_CONVERSION_FORBIDDEN,
                        "currency conversion as-of differs from the registered fact",
                    )
            with localcontext(decimal_context_v1()):
                unrounded = current * edge.identity.factor
                resolved = (
                    unrounded
                    if edge.precision_quantum is None
                    else unrounded.quantize(
                        edge.precision_quantum,
                        rounding=_ROUNDING_RULES[edge.rounding_rule],
                    )
                )
            steps.append(
                UnitConversionStepReceiptV1(
                    conversion_id=edge.conversion_id,
                    supplied_value=current,
                    factor=edge.identity.factor,
                    unrounded_value=unrounded,
                    resolved_value=resolved,
                    supplied_unit=edge.identity.supplied_unit,
                    required_unit=edge.identity.required_unit,
                    supplied_basis=edge.supplied_basis,
                    required_basis=edge.required_basis,
                    precision_quantum=edge.precision_quantum,
                    rounding_rule=edge.rounding_rule,
                    source_claim_ref=edge.source_claim_ref,
                    source_epoch_id=edge.source_epoch_id,
                )
            )
            current = resolved
        path_ids = tuple(step.conversion_id for step in steps)
        digest = sha256(
            "|".join((str(supplied), str(current), *path_ids)).encode("utf-8")
        ).hexdigest()
        return UnitConversionReceiptV1(
            receipt_id=f"CONVERSION::{digest}",
            supplied_value=supplied,
            resolved_value=current,
            supplied_unit=supplied_unit,
            required_unit=required_unit,
            supplied_basis=supplied_basis,
            required_basis=required_basis,
            conversion_path=path_ids,
            steps=tuple(steps),
            precision_boundary_applied=any(
                step.precision_quantum is not None for step in steps
            ),
        )


EMPTY_UNIT_CONVERSION_REGISTRY = UnitConversionRegistryV1()
