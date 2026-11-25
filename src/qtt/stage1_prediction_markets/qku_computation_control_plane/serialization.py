"""Deterministic JSON and cross-platform relative-path safety."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, fields, is_dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
import json
import ntpath
import re
from pathlib import PureWindowsPath
import unicodedata
from typing import Any

from .context import _native_bounded_decimal, _native_require, _native_text
from .errors import ContractValidationError, ReasonCode, SerializationSafetyError


# ASCII is unchanged by NFKC. This fixed immutable table implements the same
# case folding and alphanumeric filter without retaining any input strings.
_ASCII_KEY_NORMALIZATION_TRANSLATION_V1 = tuple(
    value + 32 if 65 <= value <= 90 else value if 48 <= value <= 57 or 97 <= value <= 122 else None
    for value in range(128)
)


@dataclass(frozen=True, slots=True)
class SecretKeyPolicyV1:
    """Immutable field-name policy shared by every secret-rejection surface."""

    forbidden_normalized_terms: frozenset[str]
    allowed_normalized_names: frozenset[str]

    @staticmethod
    def normalize(field_name: str) -> str:
        if not isinstance(field_name, str) or not field_name:
            return ""
        if type(field_name) is str and field_name.isascii():
            return field_name.translate(_ASCII_KEY_NORMALIZATION_TRANSLATION_V1)
        normalized = unicodedata.normalize("NFKC", field_name).casefold()
        return "".join(character for character in normalized if character.isalnum())

    def is_secret_key(self, field_name: str) -> bool:
        normalized = self.normalize(field_name)
        if not normalized or normalized in self.allowed_normalized_names:
            return False
        if normalized == "token" or normalized.endswith("token"):
            return True
        if type(normalized) is str:
            return any(map(normalized.__contains__, self.forbidden_normalized_terms))
        return any(
            term in normalized for term in self.forbidden_normalized_terms
        )

    def reject(self, field_name: str) -> None:
        if self.is_secret_key(field_name):
            raise SerializationSafetyError(
                ReasonCode.SECRET_MATERIAL_REJECTED,
                "secret-bearing field name is rejected",
            )


SECRET_KEY_POLICY = SecretKeyPolicyV1(
    forbidden_normalized_terms=frozenset(
        {
            "apikey",
            "apisecret",
            "authorization",
            "bearer",
            "password",
            "passphrase",
            "accesstoken",
            "refreshtoken",
            "sessiontoken",
            "cookie",
            "credential",
            "privatekey",
            "secret",
            "seedphrase",
            "walletsecret",
        }
    ),
    allowed_normalized_names=frozenset(
        {
            "tokencount",
            "tokenbudget",
            "credentialstate",
        }
    ),
)


def _is_windows_reserved_segment(segment: str) -> bool:
    return (
        ntpath.isreserved(segment)
        or ":" in segment
        or segment.endswith((" ", "."))
        or any(
            ord(character) < 32 or ord(character) == 127
            for character in segment
        )
        or segment.rstrip(" .").split(".", 1)[0].casefold() == "clock$"
    )


def validate_relative_path(path: str) -> str:
    if type(path) is not str or not path:
        raise SerializationSafetyError(
            ReasonCode.PATH_UNSAFE, "path must be a nonempty text value"
        )
    normalized = path.replace("\\", "/")
    windows = PureWindowsPath(path)
    parts = normalized.split("/")
    if (
        normalized.startswith("/")
        or windows.is_absolute()
        or windows.drive
        or any(part in {"", ".", ".."} for part in parts)
        or any(_is_windows_reserved_segment(part) for part in parts)
    ):
        raise SerializationSafetyError(
            ReasonCode.PATH_UNSAFE,
            "only portable repository-relative paths without traversal are allowed",
        )
    return "/".join(parts)


def _check_key(key: str) -> None:
    SECRET_KEY_POLICY.reject(key)


def _check_path_value(
    key: str,
    value: Any,
    *,
    location: tuple[str | int, ...] = (),
) -> None:
    if type(key) is not str:
        raise SerializationSafetyError(
            ReasonCode.SERIALIZATION_UNSAFE,
            "JSON keys must be exact strings",
        )
    lowered = key.casefold()
    if not (
        lowered == "path"
        or lowered.endswith("_path")
        or lowered.endswith("_paths")
    ):
        return

    if (
        key == "no_llm_hot_path"
        and len(location) >= 2
        and location[-2] == "authority_envelope"
    ):
        if type(value) is not bool:
            raise SerializationSafetyError(
                ReasonCode.PATH_UNSAFE,
                f"path-bearing authority flag must be an exact boolean: {key}",
            )
        return

    is_entry_owner_path = (
        key in {"existing_owner_paths", "future_owner_paths"}
        and len(location) >= 4
        and location[-4] == "manifest"
        and location[-3] == "entries"
        and type(location[-2]) is int
        and location[-1] == key
    )
    if is_entry_owner_path:
        if type(value) not in {list, tuple} or any(
            type(item) is not str for item in value
        ):
            raise SerializationSafetyError(
                ReasonCode.PATH_UNSAFE,
                f"entry owner paths must be an exact text sequence: {key}",
            )
        for candidate in value:
            validate_relative_path(candidate)
        return

    if value is None:
        return
    if type(value) is str:
        candidates = (value,)
    elif type(value) in {tuple, list}:
        candidates = value
    else:
        raise SerializationSafetyError(
            ReasonCode.PATH_UNSAFE,
            f"path-bearing field must contain relative text paths: {key}",
        )
    if not candidates or any(type(item) is not str for item in candidates):
        raise SerializationSafetyError(
            ReasonCode.PATH_UNSAFE,
            f"path-bearing field must contain relative text paths: {key}",
        )
    for candidate in candidates:
        validate_relative_path(candidate)


def _json_value(
    value: Any,
    *,
    location: tuple[str | int, ...] = (),
) -> Any:
    if value is None or isinstance(value, (bool, int, str)):
        return value
    if isinstance(value, float):
        if value != value or value in (float("inf"), float("-inf")):
            raise SerializationSafetyError(
                ReasonCode.SERIALIZATION_UNSAFE, "nonfinite floats are forbidden"
            )
        return value
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise SerializationSafetyError(
                ReasonCode.SERIALIZATION_UNSAFE, "nonfinite Decimals are forbidden"
            )
        return str(value)
    if isinstance(value, datetime):
        if value.tzinfo is None:
            raise SerializationSafetyError(
                ReasonCode.SERIALIZATION_UNSAFE,
                "naive datetimes are forbidden",
            )
        return value.isoformat()
    if isinstance(value, timedelta):
        return value.total_seconds()
    if isinstance(value, Enum):
        return _json_value(value.value, location=location)
    if type(value).__name__ == "PublicDataSourceUseScopeV1":
        from .receipts import PublicDataSourceUseScopeV1

        _native_require(type(value) is PublicDataSourceUseScopeV1, "foreign public scope type")
        value.__post_init__()
        # This exact typed field is a protected-config alias, never key material.
        # Untyped mappings retain the ordinary secret-key rejection policy.
        result = {}
        for field in fields(value):
            if field.name != "credential_alias_ref_or_none":
                _check_key(field.name)
            result[field.name] = _json_value(getattr(value, field.name), location=(*location, field.name))
        return result
    if type(value).__name__ == "PITRawFrameV1":
        from ..market_data_ingest.adapter import PITRawFrameV1

        _native_require(type(value) is PITRawFrameV1, "foreign raw frame type")
        value.__post_init__()
        # These exact typed declarations are all False, as checked by the
        # existing frame owner. They never contain credentials or headers.
        denials = {"contains_credential", "contains_signature",
                   "contains_authorization_header", "contains_private_state"}
        result = {}
        for field in fields(value):
            if field.name not in denials:
                _check_key(field.name)
            result[field.name] = _json_value(getattr(value, field.name), location=(*location, field.name))
        return result
    if is_dataclass(value) and not isinstance(value, type):
        return _json_value(
            {
                field.name: getattr(value, field.name)
                for field in fields(value)
            },
            location=location,
        )
    if isinstance(value, tuple | list):
        return [
            _json_value(item, location=(*location, index))
            for index, item in enumerate(value)
        ]
    if isinstance(value, Mapping):
        converted: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise SerializationSafetyError(
                    ReasonCode.SERIALIZATION_UNSAFE, "JSON object keys must be strings"
                )
            _check_key(key)
            child_location = (*location, key)
            _check_path_value(key, item, location=child_location)
            converted[key] = _json_value(item, location=child_location)
        return converted
    raise SerializationSafetyError(
        ReasonCode.SERIALIZATION_UNSAFE,
        f"unsupported serialization type: {type(value).__name__}",
    )


def deterministic_json(value: Any) -> str:
    return json.dumps(
        _json_value(value),
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def _evidence_canonical_object_v1(raw: bytes, *, max_bytes: int = 65536) -> dict:
    """Decode LP03 data without admitting an effect or bypassing existing guards.

    Decimal amounts are text in this protocol. JSON fractional/exponent numbers
    are rejected even when numerically integral; bool remains distinct from int.
    Kind-specific constructors must subsequently validate the exact field roster.
    """
    value = _native_strict_json(raw, max_bytes=max_bytes)
    _native_require(type(value) is dict, "LP03_JSON_OBJECT")

    def check(item):
        if type(item) in (str, bool) or item is None:
            return
        if type(item) is int:
            _native_require(-(2**256) < item < 2**256, "LP03_INTEGER_BOUND")
            return
        if type(item) is list:
            for child in item:
                check(child)
            return
        if type(item) is dict:
            for child in item.values():
                check(child)
            return
        raise SerializationSafetyError(ReasonCode.SERIALIZATION_UNSAFE, "LP03_EXACT_JSON_SCALAR")

    check(value)
    # deterministic_json still performs the ordinary secret and path checks.
    _native_require(deterministic_json(value).encode("utf-8") == raw,
                    "LP03_NONCANONICAL_JSON")
    return value


def _evidence_switch_projection_float_leaf_v1(path, root):
    """Admit binary64 at the closed M25 coordinates only."""
    if path[:3] != root:
        return False
    at = path[3:]
    if at == ("switch_ope_estimate",):
        return True
    if len(at) == 2 and at[0] == "held_out_row_values":
        return type(at[1]) is int and 0 <= at[1] < 64
    if len(at) < 3 or at[0] != "outer_fold_results" or type(at[1]) is not int or not 0 <= at[1] < 8:
        return False
    if at[2:] == ("selected_tau",):
        return True
    if len(at) == 4 and at[2] == "held_out_row_values":
        return type(at[3]) is int and 0 <= at[3] < 64
    return (len(at)==5 and at[2]=="criteria" and type(at[3]) is int and 0 <= at[3] < 16
        and at[4] in ("tau", "variance_of_mean", "bias_upper_bound", "estimated_mse_upper_bound"))


def _evidence_projection_spine_object_v1(raw: bytes) -> dict:
    """Closed stored-spine decoder; only closed typed projections admit floats.

    The typed projection validates the original schema, implementation, field,
    unit and basis before this leaf is admitted. No other record or position
    receives a binary64 exception, and this grants no publication authority.
    """
    value = _native_strict_json(raw, max_bytes=1048576, binary64_numbers=True)
    _native_require(type(value) is dict, "LP03_JSON_OBJECT")
    payload = value.get("typed_payload")
    record = payload.get("record") if type(payload) is dict else None
    projection_path = None
    multiple_projection = False
    interval_projection = False
    fold_projection = False
    cscv_projection = False
    spa_projection = False
    reality_projection = False
    bootstrap_projection = False
    recorded_dr_projection = False
    switch_projection = False
    execution_matrix_projection = False
    if (value.get("record_type") == "LP03_EVIDENCE_CONTROL_V1" and type(record) is dict
            and record.get("kind") == "VALUE_PROJECTION"
            and record.get("original_raw_schema_ref") in ("MATH-02::OUTPUT", "MATH-08::OUTPUT", "MATH-09::OUTPUT", "MATH-10::OUTPUT", "MATH-11::OUTPUT", "MATH-14::OUTPUT", "MATH-15::OUTPUT", "MATH-16::OUTPUT", "MATH-17::OUTPUT", "MATH-18::OUTPUT", "MATH-19::OUTPUT", "MATH-20::OUTPUT", "MATH-21::OUTPUT", "MATH-22::OUTPUT", "MATH-23::OUTPUT", "MATH-24::OUTPUT", "MATH-25::OUTPUT", "MATH-12::OUTPUT", "MATH-13::OUTPUT", "LP03::MATH-29::RAW_V1", "LP03::MATH-30::RAW_V1", "LP03::MATH-31::RAW_V1", "LP03::MATH-37::RAW_V1", "LP03::MATH-41::RAW_V1", "LP03::MATH-42::RAW_V1", "LP03::MATH-43::RAW_V1", "LP03::MATH-44::RAW_V1")):
        from .models import EvidenceValueProjectionRecordV1
        EvidenceValueProjectionRecordV1.from_canonical_mapping(record)
        projection_path = ("typed_payload", "record", "projected_value")
        multiple_projection = record["original_raw_schema_ref"] in ("MATH-12::OUTPUT", "MATH-13::OUTPUT")
        interval_projection = record["original_raw_schema_ref"] == "MATH-11::OUTPUT"
        fold_projection = record["original_raw_schema_ref"] == "MATH-20::OUTPUT"
        cscv_projection = record["original_raw_schema_ref"] == "MATH-19::OUTPUT"
        spa_projection = record["original_raw_schema_ref"] == "MATH-16::OUTPUT"
        reality_projection = record["original_raw_schema_ref"] == "MATH-15::OUTPUT"
        bootstrap_projection = record["original_raw_schema_ref"] == "MATH-14::OUTPUT"
        recorded_dr_projection = record["original_raw_schema_ref"] == "MATH-22::OUTPUT"
        switch_projection = record["original_raw_schema_ref"] == "MATH-25::OUTPUT"
        execution_matrix_projection = record["original_raw_schema_ref"] == "LP03::MATH-44::RAW_V1"

    def check(item, path=()):
        if type(item) in (str, bool) or item is None:
            return
        if type(item) is int:
            _native_require(-(2**256) < item < 2**256, "LP03_INTEGER_BOUND")
            return
        typed_multiple_leaf = (multiple_projection and (path == (*projection_path, "correction") or
            len(path) == 6 and path[:4] == (*projection_path, "rows") and type(path[4]) is int and path[5] == "adjusted_p"))
        typed_interval_leaf = (interval_projection and len(path) == 4 and path[:3] == projection_path
                               and type(path[3]) is int and path[3] in (0, 1))
        typed_fold_leaf = (fold_projection and len(path)==8 and path[:3]==projection_path
            and path[3]=="topology" and type(path[4]) is int and 0<=path[4]<4
            and path[5]=="merged_test_intervals" and type(path[6]) is int and 0<=path[6]<8
            and type(path[7]) is int and path[7] in (0,1))
        typed_cscv_leaf = (cscv_projection and path[:3] == projection_path and (
            len(path) == 4 and path[3] == "probability_of_backtest_overfitting"
            or len(path) == 5 and path[3] == "logits" and type(path[4]) is int and 0 <= path[4] < 6
            or len(path) == 6 and path[3] == "splits" and type(path[4]) is int and 0 <= path[4] < 6
                and path[5] in ("oos_midrank_worst_1_best_n", "relative_rank", "logit")))
        typed_spa_leaf = (spa_projection and path[:3] == projection_path and (
            len(path) == 4 and path[3] in ("statistic", "p_value")
            or len(path) == 5 and type(path[4]) is int and (
                path[3] in ("candidate_means", "long_run_variances") and 0 <= path[4] < 2
                or path[3] == "simulated_statistics" and 0 <= path[4] < 4)))
        typed_reality_leaf = (reality_projection and path[:3] == projection_path and (
            len(path) == 4 and path[3] in ("statistic", "p_value")
            or len(path) == 5 and type(path[4]) is int and (
                path[3] == "candidate_means" and 0 <= path[4] < 2
                or path[3] == "simulated_statistics" and 0 <= path[4] < 4)))
        typed_bootstrap_leaf = (bootstrap_projection and path[:3] == projection_path and (
            len(path) == 4 and path[3] in ("sample_mean", "lower", "upper", "expected_block_length")
            or len(path) == 5 and path[3] == "bootstrap_distribution" and type(path[4]) is int and 0 <= path[4] < 4))
        typed_recorded_dr_leaf = recorded_dr_projection and path == (*projection_path, "estimate")
        typed_execution_matrix_leaf = (execution_matrix_projection and len(path) == 5
            and path[:3] == projection_path and all(type(index) is int and 0 <= index < 16 for index in path[3:]))
        if type(item) is float and ((not execution_matrix_projection and not multiple_projection and not interval_projection and not bootstrap_projection and not reality_projection and not spa_projection and not cscv_projection and not fold_projection and not recorded_dr_projection and not switch_projection and path == projection_path)
                                   or switch_projection and _evidence_switch_projection_float_leaf_v1(path, projection_path)
                                   or typed_execution_matrix_leaf or typed_recorded_dr_leaf or typed_multiple_leaf or typed_interval_leaf or typed_bootstrap_leaf or typed_reality_leaf or typed_spa_leaf or typed_cscv_leaf or typed_fold_leaf):
            return  # The exact native type, finite state and domain were checked above.
        if type(item) is list:
            for index, child in enumerate(item):
                check(child, (*path, index))
            return
        if type(item) is dict:
            for name, child in item.items():
                check(child, (*path, name))
            return
        raise SerializationSafetyError(ReasonCode.SERIALIZATION_UNSAFE, "LP03_EXACT_JSON_SCALAR")

    check(value)
    _native_require(deterministic_json(value).encode("utf-8") == raw, "LP03_NONCANONICAL_JSON")
    return value


def _evidence_native_decimal_json_upper_v1(value, *, maximum_bytes):
    """Preflight this qualified native Decimal without copying its coefficient.

    CPython3.14.6 _decimal.c dec_sizeof includes embedded/dynamic coefficient
    storage. libmpdec uses at most19 digits per8 bytes (9 per4 on32-bit).
    io.c's TOSCI buffer adds at most33 bytes beyond coefficient digits.
    Three times the entire native size plus64 therefore bounds its C buffer
    and quoted JSON text conservatively. This is not physical-work accounting.
    No tuple, context rounding, hashing, integer-ratio or formatting is used.
    """
    import sys
    import _decimal
    from types import MethodDescriptorType
    _native_require(type(maximum_bytes) is int and 0 < maximum_bytes <= 1048576,
                    "LP03_NATIVE_DECIMAL_BYTE_BUDGET")
    _native_require(sys.implementation.name == "cpython" and sys.version_info[:3] == (3, 14, 6)
                    and Decimal is _decimal.Decimal and type(value) is Decimal
                    and _decimal.__libmpdec_version__ == "4.0.0"
                    and _decimal.MAX_PREC in (999999999999999999, 425000000)
                    and type(Decimal.__sizeof__) is MethodDescriptorType,
                    "LP03_NATIVE_DECIMAL_PROFILE_UNAVAILABLE")
    size = Decimal.__sizeof__(value)
    _native_require(0 < size <= maximum_bytes and 3 * size + 64 <= maximum_bytes,
                    "LP03_NATIVE_DECIMAL_ALLOCATION_BOUND")
    _native_require(Decimal.is_finite(value), "LP03_ORIGINAL_SOURCE_NONFINITE")
    return 3 * size + 64


def _encode_evidence_projection_json_v1(value, *, maximum_bytes, maximum_nodes):
    """Bound canonical projection JSON before growing tokens or output buffers.

    Only exact built-in JSON data is accepted. In particular mapping proxies
    may hide a custom backing mapping and are not a callback-free input proof.
    The projection owner builds this graph from its own decoded originals.
    This codec grants no source, projection-schema or publication authority.
    """
    import math
    _native_require(type(maximum_bytes) is int and 0 < maximum_bytes <= 1048576
                    and type(maximum_nodes) is int and 0 < maximum_nodes <= 4096, "LP03_PROJECTION_JSON_BUDGET")
    chunks, active = [], set()
    size = nodes = 0

    def emit(raw):
        nonlocal size
        _native_require(size + len(raw) <= maximum_bytes, "LP03_PROJECTION_JSON_BYTES")
        chunks.append(raw)
        size += len(raw)

    def string(item):
        # Every character needs at least one UTF-8 byte, plus both quotes.
        _native_require(len(item) + 2 <= maximum_bytes - size, "LP03_PROJECTION_JSON_BYTES")
        needed = 2
        for char in item:
            point = ord(char)
            _native_require(not 0xD800 <= point <= 0xDFFF, "LP03_PROJECTION_JSON_SURROGATE")
            if char in ('"', '\\', '\b', '\f', '\n', '\r', '\t'):
                needed += 2
            elif point < 0x20:
                needed += 6
            else:
                needed += 1 if point < 0x80 else 2 if point < 0x800 else 3 if point < 0x10000 else 4
            _native_require(needed <= maximum_bytes - size, "LP03_PROJECTION_JSON_BYTES")
        raw = json.dumps(item, ensure_ascii=False, allow_nan=False).encode("utf-8")
        _native_require(len(raw) == needed, "LP03_PROJECTION_JSON_STRING_SIZE")
        emit(raw)

    def visit(item, depth=0, location=()):
        nonlocal nodes
        nodes += 1
        _native_require(nodes <= maximum_nodes and depth <= 16, "LP03_PROJECTION_JSON_NODES_OR_DEPTH")
        if item is None:
            emit(b"null")
        elif type(item) is bool:
            emit(b"true" if item else b"false")
        elif type(item) is str:
            string(item)
        elif type(item) is int:
            # 128 decimal token characters need no more than 426 binary bits.
            # The constant-size formatting follows this allocation preflight.
            _native_require(item.bit_length() <= 426, "LP03_PROJECTION_JSON_INTEGER")
            token = str(item)
            _native_require(len(token) <= 128, "LP03_PROJECTION_JSON_INTEGER")
            emit(token.encode("ascii"))
        elif type(item) is float:
            _native_require(math.isfinite(item), "LP03_PROJECTION_JSON_NONFINITE")
            emit(json.dumps(item, allow_nan=False, separators=(",", ":")).encode("ascii"))
        elif type(item) in (dict, list, tuple):
            _native_require(depth < 16 and id(item) not in active, "LP03_PROJECTION_JSON_CYCLE_OR_DEPTH")
            _native_require(len(item) * (2 if type(item) is dict else 1) <= maximum_nodes - nodes,
                            "LP03_PROJECTION_JSON_NODES_OR_DEPTH")
            active.add(id(item))
            if type(item) is dict:
                minimum_key_bytes = 0
                for key in item:
                    _native_require(type(key) is str, "LP03_PROJECTION_JSON_KEY")
                    _native_require(len(key) + 2 <= maximum_bytes - size, "LP03_PROJECTION_JSON_BYTES")
                    minimum_key_bytes += len(key) + 2
                # Bound aggregate key comparison/normalization work before
                # sorting; each value needs at least one byte as well.
                _native_require(2 + minimum_key_bytes + 2 * len(item) + max(0, len(item) - 1)
                                <= maximum_bytes - size, "LP03_PROJECTION_JSON_BYTES")
                emit(b"{")
                for index, name in enumerate(sorted(item)):
                    _check_key(name)
                    child_location = (*location, name)
                    if index:
                        emit(b",")
                    visit(name, depth + 1, child_location)
                    emit(b":")
                    visit(item[name], depth + 1, child_location)
                    # Path normalization must only inspect the child's already
                    # admitted finite data. Nothing is returned before it passes.
                    _check_path_value(name, item[name], location=child_location)
                emit(b"}")
            else:
                emit(b"[")
                for index, child in enumerate(item):
                    if index:
                        emit(b",")
                    visit(child, depth + 1, (*location, index))
                emit(b"]")
            active.remove(id(item))
        else:
            _native_require(False, "LP03_PROJECTION_JSON_NATIVE_DATA_REQUIRED")

    visit(value)
    # Every chunk and its aggregate size have already passed byte admission.
    return b"".join(chunks)


def _evidence_frozen_data_v1(value: object) -> object:
    """Bound and detach a data tree; this is never an authority/record decoder."""
    from types import MappingProxyType

    nodes = 0

    def freeze(item, depth=0):
        nonlocal nodes
        nodes += 1
        _native_require(nodes <= 4096 and depth <= 16, "LP03_DATA_COMPLEXITY")
        if item is None or type(item) is bool:
            return item
        if type(item) is int:
            _native_require(-(2**256) < item < 2**256, "LP03_INTEGER_BOUND")
            return item
        if type(item) is str:
            _native_require(len(item) <= 65536
                            and not any(0xD800 <= ord(c) <= 0xDFFF for c in item),
                            "LP03_DATA_TEXT")
            return item
        if type(item) in (tuple, list):
            return tuple(freeze(child, depth + 1) for child in item)
        if type(item) in (dict, MappingProxyType):
            result = {}
            for name, child in item.items():
                _native_require(type(name) is str, "LP03_DATA_MEMBER")
                freeze(name, depth + 1)
                _check_key(name)
                _check_path_value(name, child, location=(name,))
                result[name] = freeze(child, depth + 1)
            return MappingProxyType(result)
        raise SerializationSafetyError(ReasonCode.SERIALIZATION_UNSAFE, "LP03_DATA_TYPE")

    result = freeze(value)
    _native_require(len(deterministic_json(result).encode("utf-8")) <= 1048576,
                    "LP03_DATA_BYTE_BOUND")
    return result


def _evidence_process_capture_segment_preflight_v1(raw: bytes, *, maximum_segment_bytes: int):
    """Closed bounded metadata, with no base64 decode or byte authority."""
    from .context import _native_ident, _public_counter_v1
    _native_require(type(maximum_segment_bytes) is int and 0 < maximum_segment_bytes <= 65536,
                    "LP03_CAPTURE_SEGMENT_BUDGET")
    value = _evidence_canonical_object_v1(raw, max_bytes=maximum_segment_bytes)
    _native_require(set(value) == {"schema_version", "operation", "capture_segment_ref", "observation_ref",
        "grant_ref", "fence_ref", "supervisor_instance_ref", "stream", "segment_ordinal", "stream_segment_count",
        "first_byte_offset", "captured_byte_count", "stream_captured_byte_count", "stream_observed_byte_count",
        "stream_discarded_byte_count", "stream_eof", "capture_complete", "encoding", "data_base64"},
        "LP03_CAPTURE_SEGMENT_FIELDS")
    _native_require(value["schema_version"] == "1.0" and value["operation"] == "SVC_PROCESS_CAPTURE_SEGMENT_V1"
                    and value["stream"] in ("STDOUT", "STDERR") and value["encoding"] == "BASE64_RFC4648_STANDARD_PADDED",
                    "LP03_CAPTURE_SEGMENT_KIND")
    for name in ("capture_segment_ref", "observation_ref", "grant_ref", "fence_ref", "supervisor_instance_ref"):
        _native_ident(value[name])
    for name in ("segment_ordinal", "first_byte_offset", "stream_observed_byte_count", "stream_discarded_byte_count"):
        _public_counter_v1(value[name], allow_zero=True)
    for name in ("stream_segment_count", "captured_byte_count", "stream_captured_byte_count"):
        _public_counter_v1(value[name])
    _native_require(type(value["stream_eof"]) is bool and type(value["capture_complete"]) is bool,
                    "LP03_CAPTURE_SEGMENT_BOOLEAN")
    ordinal, count, first, size = (value[name] for name in (
        "segment_ordinal", "stream_segment_count", "first_byte_offset", "captured_byte_count"))
    retained, observed, discarded = (value[name] for name in (
        "stream_captured_byte_count", "stream_observed_byte_count", "stream_discarded_byte_count"))
    _native_require(ordinal < count <= retained and size <= maximum_segment_bytes
                    and first + size <= retained <= 1048576 and observed == retained + discarded
                    and ((ordinal == 0) == (first == 0))
                    and ((ordinal == count - 1) == (first + size == retained))
                    and (not value["capture_complete"] or (value["stream_eof"] and discarded == 0)),
                    "LP03_CAPTURE_SEGMENT_POSITION_OR_COUNTS")
    _native_require(value["observation_ref"] == value["grant_ref"] + "::PROCESS:FAILURE"
                    and value["capture_segment_ref"] == value["observation_ref"] + "::CAPTURE:" + value["stream"] + ":" + str(ordinal),
                    "LP03_CAPTURE_SEGMENT_IDENTITY_JOIN")
    text = value["data_base64"]
    _native_require(type(text) is str and len(text) == 4 * ((size + 2) // 3)
                    and len(text) <= maximum_segment_bytes, "LP03_CAPTURE_ENCODED_LENGTH")
    return value


def _evidence_process_capture_segment_body_v1(raw: bytes, *, maximum_segment_bytes: int):
    """Opaque original-capture data only, never worker/source authority.

    These closed bodies use the existing private idempotency carrier; they add
    no spine kind. The producer and effect owner establish original custody.
    """
    import base64
    import binascii
    value = _evidence_process_capture_segment_preflight_v1(raw, maximum_segment_bytes=maximum_segment_bytes)
    text, size = value["data_base64"], value["captured_byte_count"]
    # Encoded and decoded lengths are bounded before either allocation. Strict
    # re-encoding also rejects alternate pad bits accepted by some decoders.
    try:
        binary = base64.b64decode(text.encode("ascii"), validate=True)
    except (ValueError, UnicodeError, binascii.Error) as exc:
        raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "LP03_CAPTURE_BASE64") from exc
    _native_require(len(binary) == size and base64.b64encode(binary).decode("ascii") == text,
                    "LP03_CAPTURE_BASE64_NONCANONICAL")
    return _evidence_frozen_data_v1(value), binary


def _evidence_process_capture_manifest_v1(raw: bytes, *, segment_bodies: tuple[bytes, ...],
        maximum_capture_bytes: int, maximum_segment_bytes: int, maximum_segments: int, maximum_total_bytes: int):
    """Validate a whole opaque capture roster, without creating custody.

    Empty streams keep their own observed/discard/EOF facts. Every nonempty
    retained stream must have exactly its contiguous original byte prefix.
    The surrounding failure operation still owns authority and work charges.
    """
    from .context import _native_ident, _public_counter_v1
    for bound in (maximum_capture_bytes, maximum_segments, maximum_total_bytes):
        _public_counter_v1(bound, allow_zero=True)
    _native_require(maximum_capture_bytes <= 1048576 and type(maximum_segment_bytes) is int
                    and 0 < maximum_segment_bytes <= 65536, "LP03_CAPTURE_MANIFEST_BUDGET")
    _native_require(type(raw) is bytes and len(raw) <= 16384 and type(segment_bodies) is tuple
                    and len(segment_bodies) <= min(maximum_segments, 4096)
                    and all(type(body) is bytes and len(body) <= maximum_segment_bytes for body in segment_bodies),
                    "LP03_CAPTURE_MANIFEST_INPUT_BOUND")
    _native_require(len(raw) + sum(len(body) for body in segment_bodies) <= maximum_total_bytes,
                    "LP03_CAPTURE_MANIFEST_TOTAL_BYTES")
    value = _evidence_canonical_object_v1(raw, max_bytes=16384)
    _native_require(set(value) == {"schema_version", "operation", "observation_ref", "grant_ref", "fence_ref",
        "supervisor_instance_ref", "capture_complete", "streams"}, "LP03_CAPTURE_MANIFEST_FIELDS")
    _native_require(value["schema_version"] == "1.0" and value["operation"] == "SVC_PROCESS_CAPTURE_MANIFEST_V1",
                    "LP03_CAPTURE_MANIFEST_KIND")
    for name in ("observation_ref", "grant_ref", "fence_ref", "supervisor_instance_ref"):
        _native_ident(value[name])
    _native_require(value["observation_ref"] == value["grant_ref"] + "::PROCESS:FAILURE"
                    and type(value["capture_complete"]) is bool and type(value["streams"]) is list
                    and len(value["streams"]) == 2, "LP03_CAPTURE_MANIFEST_JOIN")
    references, captured, observed, complete = [], 0, 0, True
    for stream, facts in zip(("STDOUT", "STDERR"), value["streams"], strict=True):
        _native_require(type(facts) is dict and set(facts) == {"stream", "observed_byte_count", "captured_byte_count",
            "discarded_byte_count", "eof", "segment_refs"} and facts["stream"] == stream,
            "LP03_CAPTURE_STREAM_FACTS")
        for name in ("observed_byte_count", "captured_byte_count", "discarded_byte_count"):
            _public_counter_v1(facts[name], allow_zero=True)
        refs = facts["segment_refs"]
        _native_require(type(facts["eof"]) is bool and type(refs) is list and len(refs) <= len(segment_bodies)
                        and bool(refs) == bool(facts["captured_byte_count"])
                        and facts["observed_byte_count"] == facts["captured_byte_count"] + facts["discarded_byte_count"],
                        "LP03_CAPTURE_STREAM_COUNTS")
        for ordinal, ref in enumerate(refs):
            _native_ident(ref)
            _native_require(ref == value["observation_ref"] + "::CAPTURE:" + stream + ":" + str(ordinal),
                            "LP03_CAPTURE_MANIFEST_REFERENCE_ORDER")
        references.extend(refs)
        captured += facts["captured_byte_count"]
        observed += facts["observed_byte_count"]
        complete = complete and facts["eof"] and facts["discarded_byte_count"] == 0
    _native_require(captured <= maximum_capture_bytes and observed < 2**63
                    and len(references) == len(segment_bodies) == len(set(references))
                    and value["capture_complete"] is complete, "LP03_CAPTURE_MANIFEST_TOTALS")
    # The complete roster and cumulative encoded/decoded bounds precede any
    # base64 decode or allocation of the reconstructed streams.
    bodies = iter(segment_bodies)
    for facts in value["streams"]:
        offset = 0
        for ordinal, ref in enumerate(facts["segment_refs"]):
            segment = _evidence_process_capture_segment_preflight_v1(next(bodies), maximum_segment_bytes=maximum_segment_bytes)
            _native_require(all(segment[name] == value[name] for name in
                ("observation_ref", "grant_ref", "fence_ref", "supervisor_instance_ref", "capture_complete"))
                and segment["capture_segment_ref"] == ref and segment["stream"] == facts["stream"]
                and segment["segment_ordinal"] == ordinal and segment["stream_segment_count"] == len(facts["segment_refs"])
                and segment["first_byte_offset"] == offset
                and segment["stream_captured_byte_count"] == facts["captured_byte_count"]
                and segment["stream_observed_byte_count"] == facts["observed_byte_count"]
                and segment["stream_discarded_byte_count"] == facts["discarded_byte_count"]
                and segment["stream_eof"] is facts["eof"], "LP03_CAPTURE_SEGMENT_MANIFEST_MISMATCH")
            offset += segment["captured_byte_count"]
        _native_require(offset == facts["captured_byte_count"], "LP03_CAPTURE_STREAM_INCOMPLETE")
    bodies = iter(segment_bodies)
    reconstructed = []
    for facts in value["streams"]:
        binary = bytearray()
        for _ref in facts["segment_refs"]:
            _segment, chunk = _evidence_process_capture_segment_body_v1(next(bodies), maximum_segment_bytes=maximum_segment_bytes)
            binary.extend(chunk)
        _native_require(len(binary) == facts["captured_byte_count"], "LP03_CAPTURE_STREAM_INCOMPLETE")
        reconstructed.append(bytes(binary))
    return _evidence_frozen_data_v1(value), tuple(reconstructed)


def _evidence_process_native_observation_v1(native):
    """Validate native observation data; original handles establish its truth."""
    from .context import _public_counter_v1
    _native_require(type(native) is dict and set(native) == {
        "process_identity", "exit_code", "active_processes", "total_processes", "terminated_processes",
        "assigned_process_ids", "effective_limit_flags", "effective_active_process_limit", "cpu_ns",
        "process_memory_high_water_bytes", "job_memory_high_water_bytes"}, "LP03_PROCESS_NATIVE_FIELDS")
    identity = native["process_identity"]
    _native_require(type(identity) is list and len(identity) == 3 and type(identity[2]) is str
                    and 0 < len(identity[2]) <= 32768, "LP03_PROCESS_NATIVE_IDENTITY")
    for number in identity[:2]:
        _public_counter_v1(number)
    for name, number in native.items():
        if name not in ("process_identity", "assigned_process_ids", "exit_code"):
            _public_counter_v1(number, allow_zero=True)
    _native_require(native["exit_code"] is None or (type(native["exit_code"]) is int
                    and 0 <= native["exit_code"] <= 0xffffffff), "LP03_PROCESS_NATIVE_EXIT")
    pids = native["assigned_process_ids"]
    _native_require(type(pids) is list and len(pids) <= 4, "LP03_PROCESS_NATIVE_ROSTER")
    for pid in pids:
        _public_counter_v1(pid)
    _native_require(len(set(pids)) == len(pids), "LP03_PROCESS_NATIVE_ROSTER")
    return native


def _evidence_process_observation_body_v1(raw: bytes):
    """Closed SVC observation append data; decoding never recreates custody."""
    from .context import _native_ident, _public_counter_v1
    value = _evidence_canonical_object_v1(raw, max_bytes=16384)
    _native_require(set(value) == {
        "schema_version", "operation", "observation_ref", "grant_ref", "fence_ref", "supervisor_instance_ref",
        "predecessor_state_ref", "stage", "clock_domain_id", "boot_identity_ref", "observed_at",
        "native_observation", "resumed", "stdout_eof", "stderr_eof", "controller_joined", "drains_joined",
        "output_bytes", "diagnostic_bytes", "controller_error_count", "drain_error_count", "cleanup_error_count",
        "reason_codes", "exchange_complete", "events", "computations", "invocation_measurement_or_absence"}, "LP03_PROCESS_OBSERVATION_FIELDS")
    _native_require(value["schema_version"] == "1.1" and value["operation"] == "SVC_PROCESS_OBSERVATION_APPEND_V1"
                    and value["stage"] in ("SUSPENDED", "RUNNING", "TERMINAL"), "LP03_PROCESS_OBSERVATION_KIND")
    for name in ("observation_ref", "grant_ref", "fence_ref", "supervisor_instance_ref", "predecessor_state_ref",
                 "clock_domain_id", "boot_identity_ref"):
        _native_ident(value[name])
    _native_require(type(value["observed_at"]) is list and len(value["observed_at"]) == 3,
                    "LP03_PROCESS_OBSERVATION_CLOCK")
    for number in value["observed_at"]:
        _public_counter_v1(number, allow_zero=True)
    for name in ("resumed", "stdout_eof", "stderr_eof", "controller_joined", "drains_joined", "exchange_complete"):
        _native_require(type(value[name]) is bool, "LP03_PROCESS_OBSERVATION_BOOLEAN")
    for name in ("output_bytes", "diagnostic_bytes", "controller_error_count", "drain_error_count", "cleanup_error_count", "events", "computations"):
        _public_counter_v1(value[name], allow_zero=True)
    measurement = value["invocation_measurement_or_absence"]
    if isinstance(measurement, Mapping) and measurement.get("state") == "ABSENT_WITH_REASON":
        _native_require(set(measurement) == {"state", "reason"} and measurement["reason"] in (
            "INVOCATION_NOT_STARTED", "INVOCATION_CLOCK_UNAVAILABLE", "INVOCATION_MEASUREMENT_UNAVAILABLE",
            "INVOCATION_MEASUREMENT_UNQUALIFIED"),
            "LP03_PROCESS_INVOCATION_ABSENCE")
        _native_require(not value["exchange_complete"], "LP03_PROCESS_COMPLETED_MEASUREMENT_REQUIRED")
    else:
        from .latency_policy import _evidence_invocation_measurement_v1
        _evidence_invocation_measurement_v1(measurement)
        _native_require(value["stage"] == "TERMINAL" and measurement["clock_domain_id"] == value["clock_domain_id"]
                        and measurement["boot_identity_ref"] == value["boot_identity_ref"]
                        and measurement["completed"][1] <= value["observed_at"][1], "LP03_PROCESS_INVOCATION_CLOCK")
    native = _evidence_process_native_observation_v1(value["native_observation"])
    identity = native["process_identity"]
    pids = native["assigned_process_ids"]
    from .lifecycle import _EVIDENCE_REASON_STATE_V1
    reasons = value["reason_codes"]
    _native_require(type(reasons) is list and all(type(reason) is str and reason in _EVIDENCE_REASON_STATE_V1 for reason in reasons)
                    and len(set(reasons)) == len(reasons), "LP03_PROCESS_OBSERVATION_REASONS")
    if value["stage"] == "SUSPENDED":
        _native_require(not value["resumed"] and native["exit_code"] is None and pids == identity[:1]
                        and native["active_processes"] == native["total_processes"] == 1,
                        "LP03_PROCESS_SUSPENDED_OBSERVATION")
    elif value["stage"] == "RUNNING":
        _native_require(value["resumed"], "LP03_PROCESS_RESUME_OBSERVATION")
    else:
        _native_require(native["exit_code"] is not None and native["active_processes"] == 0 and not pids
                        and value["stdout_eof"] and value["stderr_eof"] and value["controller_joined"]
                        and value["drains_joined"], "LP03_PROCESS_TERMINAL_OBSERVATION")
    return _evidence_frozen_data_v1(value)


def _evidence_process_capture_metadata_v1(*, grant_ref, fence_ref, supervisor_instance_ref, stream,
        ordinal, count, first, size, captured, observed, discarded, eof, complete):
    """One data-only segment field roster for planning and original capture."""
    observation_ref = grant_ref + "::PROCESS:FAILURE"
    return dict(schema_version="1.0", operation="SVC_PROCESS_CAPTURE_SEGMENT_V1",
        capture_segment_ref=observation_ref + "::CAPTURE:" + stream + ":" + str(ordinal),
        observation_ref=observation_ref, grant_ref=grant_ref, fence_ref=fence_ref,
        supervisor_instance_ref=supervisor_instance_ref, stream=stream, segment_ordinal=ordinal,
        stream_segment_count=count, first_byte_offset=first, captured_byte_count=size,
        stream_captured_byte_count=captured, stream_observed_byte_count=observed,
        stream_discarded_byte_count=discarded, stream_eof=eof, capture_complete=complete,
        encoding="BASE64_RFC4648_STANDARD_PADDED", data_base64="")


def _evidence_failure_trigger_header_v1(argument_count, *, cause_present, context_present,
        suppress_context, observed_between, secondary_error_count):
    """Fixed incomplete envelope; variable original diagnostics fill its room."""
    def absent(reason):
        return dict(state="ABSENT_WITH_REASON", reason=reason)
    return dict(exception_type_or_absence=absent("TYPE_UNREPRESENTABLE"),
        exception_shape="UNSUPPORTED",
        reason_code_or_absence=absent("REASON_CODE_UNREPRESENTABLE"),
        native_error_or_absence=absent("NATIVE_ERROR_UNREPRESENTABLE"),
        argument_count=argument_count, argument_prefix=[], arguments_complete=False,
        traceback_prefix=[], traceback_complete=False,
        traceback_remainder="UNOBSERVED", cause_retention="PRESENT_NOT_RETAINED" if cause_present else "ABSENT",
        context_retention="PRESENT_NOT_RETAINED" if context_present else "ABSENT", suppress_context=suppress_context,
        secondary_error_count=secondary_error_count, observed_between=observed_between, complete=False)


def _evidence_process_failure_body_v1(raw: bytes, *, capture_segment_bodies: tuple[bytes, ...],
        maximum_capture_bytes: int, maximum_segment_bytes: int, maximum_segments: int, maximum_total_bytes: int):
    """Closed nonpositive integrity data, never process or writer authority."""
    from .context import _native_ident, _public_counter_v1
    from .lifecycle import _EVIDENCE_REASON_STATE_V1, evidence_attempt_primary_reason_v1
    from .models import EvidenceExecutionConsumptionV1
    for bound in (maximum_capture_bytes, maximum_segments, maximum_total_bytes):
        _public_counter_v1(bound, allow_zero=True)
    _native_require(maximum_capture_bytes <= 1048576 and type(maximum_segment_bytes) is int
                    and 0 < maximum_segment_bytes <= 65536 and type(raw) is bytes and len(raw) <= 16384
                    and type(capture_segment_bodies) is tuple and len(capture_segment_bodies) <= min(maximum_segments, 4096)
                    and all(type(body) is bytes and len(body) <= maximum_segment_bytes for body in capture_segment_bodies),
                    "LP03_FAILURE_BODY_INPUT_BOUND")
    _native_require(len(raw) + sum(len(body) for body in capture_segment_bodies) <= maximum_total_bytes,
                    "LP03_FAILURE_BODY_TOTAL_BYTES")
    value = _evidence_canonical_object_v1(raw, max_bytes=16384)
    _native_require(set(value) == {"schema_version", "operation", "observation_ref", "grant_ref", "fence_ref",
        "supervisor_instance_ref", "predecessor_state_ref", "clock_domain_id", "boot_identity_ref", "accounting_observed_at",
        "consumed_prefix", "final_accounting_tail", "lifecycle_disposition", "reservation_ref", "failure_bounds", "reason_codes", "primary_reason",
        "custody", "capture_manifest_or_absence", "capture_observed_between_or_absence", "controller_error_count",
        "drain_error_count", "cleanup_error_count", "diagnostic_errors", "diagnostic_observed_between",
        "invocation_measurement_or_absence", "trigger_error"}, "LP03_FAILURE_BODY_FIELDS")
    _native_require(value["schema_version"] == "1.0" and value["operation"] == "SVC_PROCESS_FAILURE_AUDIT_V1"
                    and value["final_accounting_tail"] == "UNRECONCILED_FULL_RESERVATION_RETAINED",
                    "LP03_FAILURE_BODY_KIND_OR_TAIL")
    _native_require(value["lifecycle_disposition"] in ("ORIGINAL_PREDECESSOR_RETAINED", "NONPOSITIVE_SUCCESSOR_REQUESTED"),
                    "LP03_FAILURE_LIFECYCLE_DISPOSITION")
    for name in ("observation_ref", "grant_ref", "fence_ref", "supervisor_instance_ref", "predecessor_state_ref",
                 "clock_domain_id", "boot_identity_ref", "reservation_ref"):
        _native_ident(value[name])
    _native_require(value["observation_ref"] == value["grant_ref"] + "::PROCESS:FAILURE"
                    and value["reservation_ref"] == value["grant_ref"] + "::RESERVATION", "LP03_FAILURE_REFERENCE_JOIN")

    def clock(point):
        _native_require(type(point) is list and len(point) == 3, "LP03_FAILURE_CLOCK_SHAPE")
        for number in point:
            _public_counter_v1(number, allow_zero=True)

    def interval(points):
        _native_require(type(points) is list and len(points) == 2, "LP03_FAILURE_INTERVAL_SHAPE")
        for point in points:
            clock(point)
        _native_require(points[0][1] <= points[1][1] <= value["accounting_observed_at"][1]
                        and points[0][2] <= points[1][2], "LP03_FAILURE_INTERVAL_ORDER")

    def absence(item, reasons):
        _native_require(type(item) is dict and set(item) == {"state", "reason"}
                        and item["state"] == "ABSENT_WITH_REASON" and item["reason"] in reasons,
                        "LP03_FAILURE_TYPED_ABSENCE")

    clock(value["accounting_observed_at"])
    bounds = value["failure_bounds"]
    _native_require(type(bounds) is list and len(bounds) == 3, "LP03_FAILURE_FIXED_WINDOWS")
    for number in bounds:
        _public_counter_v1(number)
    _native_require(bounds[0] <= bounds[1] < bounds[2] and value["accounting_observed_at"][1] < bounds[2],
                    "LP03_FAILURE_FIXED_WINDOWS")
    EvidenceExecutionConsumptionV1.from_canonical_mapping(value["consumed_prefix"])
    trigger = value["trigger_error"]
    _native_require(type(trigger) is dict and set(trigger) == set(_evidence_failure_trigger_header_v1(0,
        cause_present=False, context_present=False, suppress_context=False, observed_between=[], secondary_error_count=0)),
        "LP03_FAILURE_TRIGGER_FIELDS")
    interval(trigger["observed_between"])
    _public_counter_v1(trigger["argument_count"], allow_zero=True)
    _public_counter_v1(trigger["secondary_error_count"], allow_zero=True)
    for key in ("arguments_complete", "traceback_complete", "suppress_context", "complete"):
        _native_require(type(trigger[key]) is bool, "LP03_FAILURE_TRIGGER_BOOLEAN")
    _native_require(trigger["exception_shape"] in ("SELECTED_NATIVE_FIELDS", "UNSUPPORTED"), "LP03_FAILURE_TRIGGER_SHAPE")
    for key in ("cause_retention", "context_retention"):
        _native_require(trigger[key] in ("ABSENT", "PRESENT_NOT_RETAINED"), "LP03_FAILURE_TRIGGER_CHAIN")
    kind = trigger["exception_type_or_absence"]
    if type(kind) is dict:
        absence(kind, ("TYPE_UNREPRESENTABLE",))
    else:
        _native_require(type(kind) is list and len(kind) == 2
                        and all(type(item) is str and 0 < len(item) <= 512 for item in kind), "LP03_FAILURE_TRIGGER_TYPE")
    code = trigger["reason_code_or_absence"]
    if type(code) is dict:
        absence(code, ("REASON_CODE_UNREPRESENTABLE", "NOT_CONTROL_PLANE_ERROR"))
    else:
        _native_require(type(code) is str and code in {item.value for item in ReasonCode}, "LP03_FAILURE_TRIGGER_CODE")
    native_error = trigger["native_error_or_absence"]
    if type(native_error) is dict:
        absence(native_error, ("NATIVE_ERROR_UNREPRESENTABLE", "NOT_OS_ERROR"))
    else:
        _native_require(type(native_error) is list and len(native_error) == 5
            and all(item is None or (type(item) is int and -2**63 < item < 2**63) for item in native_error[:2])
            and all(item is None or (type(item) is str and len(item) <= 16384) for item in native_error[2:]),
            "LP03_FAILURE_TRIGGER_NATIVE_ERROR")
    arguments = trigger["argument_prefix"]
    _native_require(type(arguments) is list and len(arguments) <= min(128, trigger["argument_count"])
        and all(item is None or type(item) is bool or (type(item) is str and len(item) <= 16384)
                or (type(item) is int and -2**63 < item < 2**63) for item in arguments)
        and trigger["arguments_complete"] is (len(arguments) == trigger["argument_count"]), "LP03_FAILURE_TRIGGER_ARGUMENTS")
    frames = trigger["traceback_prefix"]
    _native_require(type(frames) is list and len(frames) <= 64, "LP03_FAILURE_TRIGGER_TRACEBACK")
    for frame in frames:
        _native_require(type(frame) is list and len(frame) == 3 and type(frame[0]) is str and len(frame[0]) <= 4096
            and type(frame[1]) is str and len(frame[1]) <= 512 and type(frame[2]) is int and 0 <= frame[2] < 2**63,
            "LP03_FAILURE_TRIGGER_LOCATION")
    _native_require(trigger["traceback_remainder"] in ("NONE", "PRESENT_NOT_RETAINED", "LOCATION_UNAVAILABLE", "UNOBSERVED")
        and trigger["traceback_complete"] is (trigger["traceback_remainder"] == "NONE"), "LP03_FAILURE_TRIGGER_TRACEBACK_TAIL")
    complete = (trigger["exception_shape"] == "SELECTED_NATIVE_FIELDS" and type(kind) is list
        and (type(code) is str or code["reason"] == "NOT_CONTROL_PLANE_ERROR")
        and (type(native_error) is list or native_error["reason"] == "NOT_OS_ERROR")
        and trigger["arguments_complete"] and trigger["traceback_complete"]
        and trigger["cause_retention"] == trigger["context_retention"] == "ABSENT" and trigger["secondary_error_count"] == 0)
    _native_require(trigger["complete"] is complete, "LP03_FAILURE_TRIGGER_COMPLETENESS")
    reasons = value["reason_codes"]
    _native_require(type(reasons) is list and bool(reasons) and len(reasons) <= len(_EVIDENCE_REASON_STATE_V1)
                    and all(type(reason) is str and reason in _EVIDENCE_REASON_STATE_V1 for reason in reasons)
                    and len(reasons) == len(set(reasons)) and not {"COLLECTION_COMPLETE", "FUTILITY"} & set(reasons)
                    and value["primary_reason"] == evidence_attempt_primary_reason_v1(tuple(reasons)),
                    "LP03_FAILURE_REASONS")
    for name in ("controller_error_count", "drain_error_count", "cleanup_error_count"):
        _public_counter_v1(value[name], allow_zero=True)
    errors = value["diagnostic_errors"]
    _native_require(type(errors) is dict and set(errors) == {"controller", "drain", "cleanup"},
                    "LP03_FAILURE_DIAGNOSTIC_FIELDS")
    interval(value["diagnostic_observed_between"])
    for domain, summary in errors.items():
        _native_require(type(summary) is dict and set(summary) == {"retained_entries", "omitted_entry_count", "complete"},
                        "LP03_FAILURE_DIAGNOSTIC_SUMMARY")
        entries = summary["retained_entries"]
        _public_counter_v1(summary["omitted_entry_count"], allow_zero=True)
        _native_require(type(entries) is list and len(entries) <= 128
                        and len(entries) + summary["omitted_entry_count"] == value[domain + "_error_count"]
                        and summary["complete"] is (summary["omitted_entry_count"] == 0), "LP03_FAILURE_DIAGNOSTIC_COUNT")
        for entry in entries:
            _native_require(type(entry) is list and 1 <= len(entry) <= 3
                            and all(item is None or (type(item) is str and len(item) <= 16384)
                                    or (type(item) is int and 0 <= item < 2**63) for item in entry),
                            "LP03_FAILURE_DIAGNOSTIC_ENTRY")
    _native_require(not any(value[name] for name in ("controller_error_count", "drain_error_count", "cleanup_error_count"))
                    or "SUPERVISION_FAILURE" in reasons, "LP03_FAILURE_SUPERVISION_REASON_REQUIRED")
    custody = value["custody"]
    _native_require(type(custody) is dict and custody.get("kind") in ("TERMINAL", "NO_CHILD", "TERMINATION_UNKNOWN"),
                    "LP03_FAILURE_CUSTODY_KIND")
    if custody["kind"] == "NO_CHILD":
        _native_require(set(custody) == {"kind", "creation_stage", "controller_joined", "controller_status", "cleanup_complete",
            "job_total_processes", "output_storage_present"}
            and custody["creation_stage"] in ("NOT_ENTERED", "OUTPUT_ALLOCATED", "RETURNED_FAILURE")
            and custody["controller_status"] in ("NOT_CREATED", "JOINED")
            and custody["controller_joined"] is (custody["controller_status"] == "JOINED")
            and (custody["controller_status"] != "NOT_CREATED" or custody["creation_stage"] == "NOT_ENTERED")
            and type(custody["cleanup_complete"]) is bool
            and type(custody["job_total_processes"]) is int and custody["job_total_processes"] == 0
            and type(custody["output_storage_present"]) is bool
            and custody["output_storage_present"] is (custody["creation_stage"] != "NOT_ENTERED"),
            "LP03_FAILURE_NO_CHILD_FACTS")
        _native_require("TERMINATION_UNKNOWN" not in reasons, "LP03_FAILURE_NO_CHILD_REASON")
        if custody["creation_stage"] == "RETURNED_FAILURE":
            _native_require("FAILED_TO_START" in reasons, "LP03_FAILURE_NATIVE_CREATE_FAILURE_REASON")
        _native_require(all(value["consumed_prefix"][name] == 0 for name in
            ("events", "computations", "output_bytes", "active_workers", "process_memory_high_water_bytes", "job_memory_high_water_bytes")),
            "LP03_FAILURE_NO_CHILD_CONSUMPTION")
    else:
        _native_require(set(custody) == {"kind", "native_observation_or_absence", "native_observed_between_or_absence",
            "stdout_eof", "stderr_eof", "controller_joined", "drains_joined", "cleanup_complete"},
            "LP03_FAILURE_NATIVE_CUSTODY_FIELDS")
        for name in ("stdout_eof", "stderr_eof", "controller_joined", "drains_joined", "cleanup_complete"):
            _native_require(type(custody[name]) is bool, "LP03_FAILURE_CUSTODY_BOOLEAN")
        native = custody["native_observation_or_absence"]
        if type(native) is dict and native.get("state") == "ABSENT_WITH_REASON":
            absence(native, ("NATIVE_OBSERVATION_UNAVAILABLE",))
            absence(custody["native_observed_between_or_absence"], ("NATIVE_OBSERVATION_UNAVAILABLE",))
            _native_require(custody["kind"] == "TERMINATION_UNKNOWN", "LP03_FAILURE_TERMINAL_NATIVE_REQUIRED")
        else:
            _evidence_process_native_observation_v1(native)
            interval(custody["native_observed_between_or_absence"])
        if custody["kind"] == "TERMINAL":
            _native_require(native["exit_code"] is not None and native["active_processes"] == 0
                            and not native["assigned_process_ids"] and all(custody[name] for name in
                            ("stdout_eof", "stderr_eof", "controller_joined", "drains_joined")), "LP03_FAILURE_TERMINAL_FACTS")
        else:
            _native_require("TERMINATION_UNKNOWN" in reasons and value["primary_reason"] == "TERMINATION_UNKNOWN"
                            and custody["cleanup_complete"] is False, "LP03_FAILURE_UNKNOWN_STAYS_UNRESOLVED")
    if not custody["cleanup_complete"]:
        _native_require(bool({"TERMINATION_UNKNOWN", "INTEGRITY_FAILURE", "SUPERVISION_FAILURE"} & set(reasons)),
                        "LP03_FAILURE_CLEANUP_BLOCKING_REASON")
    else:
        _native_require(value["cleanup_error_count"] == 0, "LP03_FAILURE_CLEANUP_COMPLETENESS")
    capture = value["capture_manifest_or_absence"]
    if type(capture) is dict and capture.get("state") == "ABSENT_WITH_REASON":
        absence(capture, ("NO_CHILD_NO_STREAMS", "DRAIN_SNAPSHOT_UNAVAILABLE"))
        absence(value["capture_observed_between_or_absence"], (capture["reason"],))
        _native_require(type(capture_segment_bodies) is tuple and not capture_segment_bodies
                        and ((custody["kind"] == "NO_CHILD") == (capture["reason"] == "NO_CHILD_NO_STREAMS")),
                        "LP03_FAILURE_CAPTURE_ABSENCE_JOIN")
    else:
        _native_require(custody["kind"] != "NO_CHILD", "LP03_FAILURE_NO_CHILD_HAS_CAPTURE")
        interval(value["capture_observed_between_or_absence"])
        manifest_raw = _encode_evidence_projection_json_v1(capture, maximum_bytes=16384, maximum_nodes=4096)
        manifest, _binary = _evidence_process_capture_manifest_v1(manifest_raw, segment_bodies=capture_segment_bodies,
            maximum_capture_bytes=maximum_capture_bytes, maximum_segment_bytes=maximum_segment_bytes,
            maximum_segments=maximum_segments, maximum_total_bytes=maximum_total_bytes)
        _native_require(all(manifest[name] == value[name] for name in
            ("observation_ref", "grant_ref", "fence_ref", "supervisor_instance_ref"))
            and manifest["streams"][0]["eof"] is custody["stdout_eof"]
            and manifest["streams"][1]["eof"] is custody["stderr_eof"], "LP03_FAILURE_CAPTURE_CUSTODY_JOIN")
    measurement = value["invocation_measurement_or_absence"]
    if type(measurement) is dict and measurement.get("state") == "ABSENT_WITH_REASON":
        absence(measurement, ("INVOCATION_NOT_STARTED", "INVOCATION_MEASUREMENT_UNAVAILABLE",
            "INVOCATION_MEASUREMENT_UNQUALIFIED", "INVOCATION_MEASUREMENT_NOT_FROZEN"))
    else:
        from .latency_policy import _evidence_invocation_measurement_v1
        _evidence_invocation_measurement_v1(measurement)
        _native_require(custody["kind"] == "TERMINAL" and measurement["clock_domain_id"] == value["clock_domain_id"]
                        and measurement["boot_identity_ref"] == value["boot_identity_ref"]
                        and measurement["completed"][1] <= value["accounting_observed_at"][1], "LP03_FAILURE_INVOCATION_CLOCK")
    return _evidence_frozen_data_v1(value)


def safe_json_loads(text: str) -> object:
    if not isinstance(text, str):
        raise SerializationSafetyError(
            ReasonCode.SERIALIZATION_UNSAFE, "serialized input must be text"
        )
    try:
        def reject_duplicate_keys(
            pairs: list[tuple[str, object]],
        ) -> dict[str, object]:
            result: dict[str, object] = {}
            for key, item in pairs:
                if key in result:
                    raise ValueError(f"duplicate JSON object key: {key}")
                result[key] = item
            return result

        value = json.loads(
            text,
            parse_constant=lambda value: (_ for _ in ()).throw(
                ValueError(f"invalid constant {value}")
            ),
            object_pairs_hook=reject_duplicate_keys,
        )
    except (json.JSONDecodeError, ValueError) as exc:
        raise SerializationSafetyError(
            ReasonCode.SERIALIZATION_UNSAFE, "invalid or nonfinite JSON"
        ) from exc
    _json_value(value)
    return value


def _native_strict_json(raw: bytes, max_bytes: int = 65536, *,
                        max_nodes: int = 4096, binary64_numbers: bool = False) -> Any:
    """Bounded raw JSON; ordinary callers retain exact Decimal numeric tokens.

    The private raw-output schema decoder explicitly selects binary64 numbers.
    Its declared scalar positions and canonical re-encoding remain mandatory;
    this switch grants no source or evidence authority.
    """
    _native_require(type(max_bytes) is int and 0 < max_bytes <= 1048576, "JSON_BUDGET")
    _native_require(type(max_nodes) is int and 0 < max_nodes <= 4096
                    and type(binary64_numbers) is bool, "JSON_BUDGET")
    _native_require(type(raw) is bytes and len(raw) <= max_bytes, "JSON_BOUND")
    try:
        decoded = raw.decode("utf-8", errors="strict")
    except UnicodeError as exc:
        raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "JSON") from exc

    # Bound nesting before recursive decoding; ignore brackets in quoted text.
    stack = []
    quoted = escaped = False
    for char in decoded:
        if quoted:
            if escaped:
                escaped = False
            elif char == chr(92):
                escaped = True
            elif char == '"':
                quoted = False
        elif char == '"':
            quoted = True
        elif char in "[{":
            stack.append(char)
            _native_require(len(stack) <= 16, "JSON_DEPTH")
        elif char in "]}":
            _native_require(bool(stack) and stack.pop() == ("[" if char == "]" else "{"), "JSON")
    _native_require(not quoted and not stack, "JSON")

    def pairs(items):
        result = {}
        for key, value in items:
            _native_text(key)
            _native_require(key not in result, "DUPLICATE_JSON_KEY")
            result[key] = value
        return result

    def number(token):
        _native_require(len(token) <= 128, "NUMBER_BOUND")
        if binary64_numbers:
            import math
            result = float(token)
            _native_require(math.isfinite(result), "NONFINITE")
            return result
        exponent = re.search(r"[eE]([+-]?[0-9]+)$", token)
        _native_require(exponent is None or abs(int(exponent.group(1))) <= 128, "NUMBER_BOUND")
        return _native_bounded_decimal(Decimal(token))

    def int_number(token):
        number(token)
        return int(token)

    def nonfinite(_token):
        raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "NONFINITE")

    try:
        result = json.loads(
            decoded, object_pairs_hook=pairs, parse_float=number,
            parse_int=int_number, parse_constant=nonfinite,
        )
    except (UnicodeError, json.JSONDecodeError, RecursionError) as exc:
        raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "JSON") from exc

    nodes = 0

    def visit(value, depth=0):
        nonlocal nodes
        nodes += 1
        _native_require(nodes <= max_nodes, "JSON_NODES")
        _native_require(depth <= 16, "JSON_DEPTH")
        if type(value) is str:
            _native_require(not any(0xD800 <= ord(char) <= 0xDFFF for char in value), "SURROGATE")
        elif type(value) is dict:
            for key, item in value.items():
                visit(key, depth + 1)
                visit(item, depth + 1)
        elif type(value) is list:
            for item in value:
                visit(item, depth + 1)

    visit(result)
    return result


# F14 isolated native/value serialization. Existing global codecs stay unchanged.
import copy
from datetime import timezone
from .context import _native_ident, _native_obj, _native_utc_nanoseconds
from .errors import PersistenceContractError, PointInTimeError


def _native_retail_wire_encode_v1(x: Any) -> bytes:
    """Bound each token and emitted aggregate before growing an encoded buffer."""
    chunks = []
    size = 0
    nodes = 0
    active = set()

    def emit(v):
        nonlocal size
        b = v.encode('utf-8')
        size += len(b)
        _native_require(size <= 65536, 'JSON_BOUND')
        chunks.append(b)

    def visit(v, depth=0):
        nonlocal nodes
        nodes += 1
        _native_require(depth <= 16 and nodes <= 4096, 'JSON_RESOURCE_BOUND')
        if v is None:
            emit('null')
        elif type(v) is bool:
            emit('true' if v else 'false')
        elif type(v) is int:
            _native_require(v.bit_length() <= 425, 'NUMBER_BOUND')
            _native_bounded_decimal(Decimal(v))
            emit(str(v))
        elif type(v) is Decimal:
            token = format(_native_bounded_decimal(v), 'f')
            _native_require(len(token) <= 128, 'NUMBER_BOUND')
            emit(token)
        elif type(v) is str:
            _native_require(len(v) <= 65536 and (not any((55296 <= ord(c) <= 57343 for c in v))), 'STRING_BOUND')
            emit(json.dumps(v, ensure_ascii=True))
        elif type(v) in (list, dict):
            _native_require(depth < 16, 'JSON_DEPTH')
            _native_require(id(v) not in active and len(v) <= 4096, 'JSON_CONTAINER_BOUND')
            active.add(id(v))
            if type(v) is list:
                emit('[')
                for i, a in enumerate(v):
                    if i:
                        emit(',')
                    visit(a, depth + 1)
                emit(']')
            else:
                for k in v:
                    _native_text(k)
                emit('{')
                for i, k in enumerate(sorted(v)):
                    if i:
                        emit(',')
                    visit(k, depth + 1)
                    emit(':')
                    visit(v[k], depth + 1)
                emit('}')
            active.remove(id(v))
        else:
            raise ContractValidationError(ReasonCode.INVALID_CONTRACT, 'WIRE_TYPE')
    visit(x)
    return b''.join(chunks)


def _native_retail_strict_equal_v1(a: object, b: object) -> bool:
    if type(a) is not type(b):
        return False
    if type(a) is dict:
        return a.keys() == b.keys() and all((_native_retail_strict_equal_v1(a[k], b[k]) for k in a))
    if type(a) in (tuple, list):
        return len(a) == len(b) and all((_native_retail_strict_equal_v1(x, y) for x, y in zip(a, b)))
    return a == b


def _native_retail_transport_storage_projection_v1(transport, *, expected_binding_ref, restore=False):
    """Lossless storage-key adaptation for a trusted nonsecret binding reference.

    This is not a transport validator or secret detector. Run the existing closed
    witness schema, secret-safe serializer and source-owner alias resolution as
    separate gates. Never pass API keys, headers or secret values in this field.
    """
    _native_require(type(transport) is dict and type(restore) is bool, 'PRIVATE_TRANSPORT_STORAGE_TYPE')
    _native_require(type(expected_binding_ref) is str, 'PRIVATE_TRANSPORT_STORAGE_BINDING')
    _native_ident(expected_binding_ref)
    source, target = ('authentication_binding_ref', 'credential_binding_ref') if restore else ('credential_binding_ref', 'authentication_binding_ref')
    _native_require(source in transport and target not in transport, 'PRIVATE_TRANSPORT_STORAGE_ALIAS')
    _native_require(type(transport[source]) is str and transport[source] == expected_binding_ref, 'PRIVATE_TRANSPORT_STORAGE_BINDING')
    result = copy.deepcopy(transport)
    result[target] = result.pop(source)
    return result



def _f14_require_v1(ok: bool, reason: str) -> None:
    if ok:
        return
    if reason in ['F14_STORAGE_DEPTH', 'F14_STORAGE_ENVELOPE_BOUND', 'F14_STORAGE_JSON', 'F14_STORAGE_NODES', 'F14_STORAGE_NONCANONICAL', 'F14_STORAGE_UTF8']:
        raise SerializationSafetyError(ReasonCode.SERIALIZATION_UNSAFE, reason)
    if reason in ['F14_CONTROL_TIME_BINDING', 'F14_STORAGE_CLOCK_ORDER', 'F14_STORAGE_TIME', 'F14_STORAGE_WRAPPER_TIME']:
        raise PointInTimeError(ReasonCode.POINT_IN_TIME_VIOLATION, reason)
    if reason in ['F14_CONTROL_ID_ALIAS', 'F14_CONTROL_INTENT_BINDING', 'F14_CONTROL_RESULT_BINDING', 'F14_CONTROL_UOW_BINDING', 'F14_PHYSICAL_PARTIAL_BATCH', 'F14_STORAGE_ID_BINDING', 'F14_STORAGE_PLAN_ACTUAL_MISMATCH', 'F14_STORAGE_SCOPE_BINDING', 'F14_STORAGE_SELF_COMMIT', 'F14_STORAGE_VIEW_MEMBERSHIP', 'F14_STORAGE_VIEW_TABLES']:
        raise PersistenceContractError(ReasonCode.PERSISTENCE_CONFLICT, reason)
    if reason in {"F14_STORAGE_SECRET", "F14_STORAGE_SECRET_KEY"}:
        raise SerializationSafetyError(ReasonCode.SECRET_MATERIAL_REJECTED, reason)
    raise ContractValidationError(ReasonCode.INVALID_CONTRACT, reason)


_F14_MAX_RAW_BYTES = 1048576


_F14_MAX_INT = (1 << 63) - 1


_F14_SCOPE_FIELDS = ('profile', 'ledger_account_ref', 'source_binding_ref', 'source_context_ref', 'capture_epoch_ref', 'partition_ref')


_F14_FLAG_FIELDS = ('provider_connection_allowed', 'private_state_read_allowed', 'replay_or_paper_execution_allowed', 'llm_inference_allowed', 'qpu_execution_allowed', 'mode_or_allow_activation_allowed', 'order_release_allowed', 'capital_mutation_allowed')


_F14_SPINE_FIELDS = ('record_id', 'record_type', 'schema_version', 'semantic_owner', 'implementation_owner', 'context_ref', 'effective_at', 'recorded_at', 'causation_id', 'correlation_id', 'traceparent', 'tracestate', 'sequence', 'aggregate_id', 'aggregate_version', 'authority_class', 'typed_payload', 'no_effect_flags')


_F14_COMMIT_CLASSES = ('COORDINATOR_POST_RETURN_UPPER_BOUND_REFERENCE_ONLY', 'STORAGE_ASSIGNED_ATOMIC_COMMIT_EVIDENCE')


_F14_OPERATIONS = ('ACTIVITY_TRADE', 'ACTIVITY_RESOLUTION', 'ACTIVITY_FUNDING', 'POSITIONS', 'BALANCES', 'WS_POSITION', 'WS_BALANCE')


_F14_ROUTES = dict(zip(_F14_OPERATIONS, ('/v1/portfolio/activities',) * 3 + ('/v1/portfolio/positions', '/v1/account/balances', '/v1/ws/private', '/v1/ws/private')))


def _f14_dumps_v1(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(',', ':'))


@dataclass(frozen=True, slots=True)
class _F14ShapeV1:
    kind: str
    limit: int = 0
    fields: tuple[tuple[str, '_F14ShapeV1'], ...] = ()
    item: '_F14ShapeV1 | None' = None
    options: tuple[object, ...] = ()


def _f14_obj_v1(**fields: Shape) -> _F14ShapeV1:
    return _F14ShapeV1('object', fields=tuple(fields.items()))


_F14_ID = _F14ShapeV1('id', 256)


_F14_TS = _F14ShapeV1('time', 35)


_F14_SQL_TIME = _F14ShapeV1('sql_time', 32)


_F14_INTEGER = _F14ShapeV1('integer')


_F14_TRUE = _F14ShapeV1('literal', options=(True,))


_F14_FALSE = _F14ShapeV1('literal', options=(False,))


_F14_NULL = _F14ShapeV1('literal', options=(None,))


def _f14_enum_v1(*choices: str) -> _F14ShapeV1:
    return _F14ShapeV1('literal', options=tuple(choices))


def _f14_array_v1(item: _F14ShapeV1, maximum: int) -> _F14ShapeV1:
    return _F14ShapeV1('array', maximum, item=item)


_F14_SCOPE = _f14_obj_v1(**{k: _F14_ID for k in _F14_SCOPE_FIELDS})


_F14_BASE = dict(record_id=_F14_ID, scope=_F14_SCOPE)


_F14_COMMIT = _f14_obj_v1(**_F14_BASE, committed_record_refs=_f14_array_v1(_F14_ID, 100), evidence_class=_f14_enum_v1(*_F14_COMMIT_CLASSES), completed_at=_F14_TS, completed_monotonic_ns=_F14_INTEGER, process_epoch_id=_F14_ID, monotonic_clock_id=_F14_ID)


_F14_PHASES = {'RAW': _f14_obj_v1(raw_body_utf8=_F14ShapeV1('raw_json_utf8', _F14_MAX_RAW_BYTES), scope=_F14_SCOPE), 'TRANSPORT': _f14_obj_v1(**_F14_BASE, raw_record_ref=_F14_ID, source_binding_ref=_F14_ID, source_snapshot_ref=_F14_ID, revocation_epoch=_F14_INTEGER, operation=_f14_enum_v1(*_F14_OPERATIONS), request_ref=_F14_ID, authentication_binding_ref=_F14_ID, endpoint=_F14ShapeV1('text', 256), method=_f14_enum_v1('GET'), response_status=_F14ShapeV1('literal', options=(200, 101)), tls_peer_verified=_F14_TRUE, request_authentication_verified=_F14_TRUE, session_ref=_F14_ID, response_received=_F14_TRUE, received_at=_F14_TS, received_monotonic_ns=_F14_INTEGER, parse_completed_at=_F14_TS, parse_completed_monotonic_ns=_F14_INTEGER, process_epoch_id=_F14_ID, monotonic_clock_id=_F14_ID), 'CAPTURE_COMMIT': _F14_COMMIT, 'PUBLICATION': _f14_obj_v1(**_F14_BASE, raw_record_ref=_F14_ID, capture_commit_ref=_F14_ID, source_snapshot_ref=_F14_ID, revocation_epoch=_F14_INTEGER, published_at=_F14_TS, published_monotonic_ns=_F14_INTEGER, process_epoch_id=_F14_ID, monotonic_clock_id=_F14_ID), 'COMPANION_COMMIT': _F14_COMMIT, 'CLOCK_PROOF': _f14_obj_v1(**_F14_BASE, subject_raw_record_ref=_F14_ID, source_binding_ref=_F14_ID, value=_F14_TS)}


def _f14_validate_v1(shape: _F14ShapeV1, value: object) -> None:
    k = shape.kind
    if k == 'object':
        _f14_require_v1(type(value) is dict and set(value) == {n for n, _ in shape.fields}, 'F14_STORAGE_FIELDS')
        for name, child in shape.fields:
            _f14_validate_v1(child, value[name])
    elif k == 'sequence':
        _f14_require_v1(type(value) is list and len(value) == len(shape.fields), 'F14_STORAGE_SEQUENCE')
        for (_, child), item in zip(shape.fields, value, strict=True):
            _f14_validate_v1(child, item)
    elif k == 'nullable':
        if value is not None:
            _f14_validate_v1(shape.item, value)
    elif k == 'json_text':
        _f14_load_canonical_v1(value, shape.item)
    elif k == 'array':
        _f14_require_v1(type(value) is list and 1 <= len(value) <= shape.limit, 'F14_STORAGE_LIST')
        for v in value:
            _f14_validate_v1(shape.item, v)
        _f14_require_v1(len(value) == len(set(value)), 'F14_STORAGE_DUPLICATE')
    elif k == 'integer':
        _f14_require_v1(type(value) is int and 0 <= value <= (shape.limit or _F14_MAX_INT), 'F14_STORAGE_INTEGER')
    elif k == 'literal':
        _f14_require_v1(any((type(value) is type(v) and value == v for v in shape.options)), 'F14_STORAGE_LITERAL')
    else:
        _f14_require_v1(type(value) is str, 'F14_STORAGE_TEXT')
        try:
            b = value.encode('utf8', 'strict')
        except UnicodeError as e:
            raise SerializationSafetyError(ReasonCode.SERIALIZATION_UNSAFE, 'F14_STORAGE_UTF8') from e
        if k in ('utf8_bytes', 'raw_json_utf8'):
            _f14_require_v1(len(b) <= shape.limit, 'F14_STORAGE_RAW_BOUND')
            if k == 'raw_json_utf8':
                parsed = _native_strict_json(b, shape.limit)
                _f14_require_v1(type(parsed) is dict, 'F14_STORAGE_RAW_OBJECT')
                _f14_secret_keys_v1(parsed)
        elif k in ('id', 'text'):
            _f14_require_v1(1 <= len(value) <= shape.limit and value == value.strip(), 'F14_STORAGE_TEXT_BOUND')
            _f14_require_v1(not any((ord(c) < 33 or 127 <= ord(c) < 160 for c in value)), 'F14_STORAGE_ID')
        elif k == 'time':
            _f14_require_v1(len(value) <= shape.limit, 'F14_STORAGE_TIME')
            _f14_native_time_v1(value)
        elif k == 'sql_time':
            _f14_require_v1(len(value) <= shape.limit, 'F14_STORAGE_TIME')
            try:
                t = datetime.fromisoformat(value)
            except ValueError as e:
                raise PointInTimeError(ReasonCode.POINT_IN_TIME_VIOLATION, 'F14_STORAGE_TIME') from e
            _f14_require_v1(t.tzinfo is not None and t.utcoffset().total_seconds() == 0 and (t.isoformat() == value), 'F14_STORAGE_TIME')
        else:
            raise ContractValidationError(ReasonCode.INVALID_CONTRACT, 'F14_UNKNOWN_SHAPE')


def _f14_native_time_v1(value: str) -> tuple[int, str]:
    """Exact inherited clock domain; normalize only the derived SQL floor.

    Preserve raw/native lexical values, including known numeric offsets.
    Unknown -00:00, leap seconds, sub-nanosecond precision and UTC calendar
    overflow are rejected just as in the inherited exact-time contract.
    This independent implementation does not call its native-time oracle.
    """
    _f14_require_v1(type(value) is str and len(value) <= 35, 'F14_STORAGE_TIME')
    match = re.fullmatch('([0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2})(?:\\.([0-9]{1,9}))?(Z|[+-][0-9]{2}:[0-9]{2})', value)
    _f14_require_v1(match is not None and match[3] != '-00:00', 'F14_STORAGE_TIME')
    zone = match[3]
    offset_minutes = 0
    if zone != 'Z':
        hours = int(zone[1:3])
        minutes = int(zone[4:6])
        _f14_require_v1(hours < 24 and minutes < 60, 'F14_STORAGE_TIME')
        offset_minutes = (1 if zone[0] == '+' else -1) * (hours * 60 + minutes)
    try:
        local = datetime.strptime(match[1], '%Y-%m-%dT%H:%M:%S').replace(tzinfo=timezone.utc)
        whole = local - timedelta(minutes=offset_minutes)
    except (ValueError, OverflowError) as exc:
        raise PointInTimeError(ReasonCode.POINT_IN_TIME_VIOLATION, 'F14_STORAGE_TIME') from exc
    fraction = int((match[2] or '').ljust(9, '0') or '0')
    delta = whole - datetime(1970, 1, 1, tzinfo=timezone.utc)
    ns = (delta.days * 86400 + delta.seconds) * 1000000000 + fraction
    return (ns, whole.replace(microsecond=fraction // 1000).isoformat())


def _f14_payload_shape_v1(phase: str) -> _F14ShapeV1:
    return _f14_obj_v1(record_id=_F14_ID, phase=_f14_enum_v1(phase), canonical_payload_json=_F14ShapeV1('json_text', item=_F14_PHASES[phase]))


def _f14_spine_shape_v1(phase: str) -> _F14ShapeV1:
    names = {n: _F14_ID for n in _F14_SPINE_FIELDS if n not in ('record_type', 'schema_version', 'effective_at', 'recorded_at', 'sequence', 'aggregate_version', 'typed_payload', 'no_effect_flags')}
    names['authority_class'] = _f14_enum_v1('PRIVATE_EVIDENCE_CONFORMANCE_ONLY')
    return _f14_obj_v1(**names, record_type=_f14_enum_v1('PRIVATE_EVIDENCE_WITNESS'), schema_version=_f14_enum_v1('1'), effective_at=_F14_SQL_TIME, recorded_at=_F14_SQL_TIME, sequence=_F14_INTEGER, aggregate_version=_F14_INTEGER, typed_payload=_f14_payload_shape_v1(phase), no_effect_flags=_f14_obj_v1(**{k: _F14_FALSE for k in _F14_FLAG_FIELDS}))


def _f14_shape_scan_v1(text: str, max_depth: int, max_nodes: int) -> None:
    """Bound depth and key/value/container tokens before allocating a JSON tree."""
    quoted = escaped = scalar = False
    stack = []
    nodes = 0

    def bump():
        nonlocal nodes
        nodes += 1
        _f14_require_v1(nodes <= max_nodes, 'F14_STORAGE_NODES')
    for c in text:
        if quoted:
            if escaped:
                escaped = False
            elif c == '\\':
                escaped = True
            elif c == '"':
                quoted = False
            continue
        if c in ' \t\r\n,:':
            scalar = False
            continue
        if c == '"':
            scalar = False
            quoted = True
            bump()
        elif c in '{[':
            scalar = False
            bump()
            stack.append(c)
            _f14_require_v1(len(stack) <= max_depth, 'F14_STORAGE_DEPTH')
        elif c in '}]':
            scalar = False
            _f14_require_v1(bool(stack) and stack.pop() == ('{' if c == '}' else '['), 'F14_STORAGE_JSON')
        elif not scalar:
            scalar = True
            bump()
    _f14_require_v1(not quoted and (not stack), 'F14_STORAGE_JSON')


def _f14_load_canonical_v1(text: str, shape: _F14ShapeV1) -> object:
    _f14_require_v1(type(text) is str, 'F14_STORAGE_TEXT')
    bound = _F14_SHAPE_LIMITS[shape][0]
    _f14_require_v1(len(text) <= bound, 'F14_STORAGE_ENVELOPE_BOUND')
    try:
        b = text.encode('utf8', 'strict')
    except UnicodeError as e:
        raise SerializationSafetyError(ReasonCode.SERIALIZATION_UNSAFE, 'F14_STORAGE_UTF8') from e
    _f14_require_v1(len(b) <= bound, 'F14_STORAGE_ENVELOPE_BOUND')
    nodes, depth = _F14_SHAPE_LIMITS[shape][1:]
    _f14_shape_scan_v1(text, depth + 1, nodes)

    def pairs(items):
        r = {}
        for k, v in items:
            _f14_require_v1(k not in r, 'F14_STORAGE_DUPLICATE_JSON_KEY')
            r[k] = v
        return r

    def integer(token):
        _f14_require_v1(len(token) <= 19, 'F14_STORAGE_INTEGER')
        v = int(token)
        _f14_validate_v1(_F14_INTEGER, v)
        return v

    def no_number(_):
        raise ContractValidationError(ReasonCode.INVALID_CONTRACT, 'F14_STORAGE_NUMBER')
    try:
        v = json.loads(text, object_pairs_hook=pairs, parse_int=integer, parse_float=no_number, parse_constant=no_number)
    except (json.JSONDecodeError, RecursionError, UnicodeError) as e:
        raise SerializationSafetyError(ReasonCode.SERIALIZATION_UNSAFE, 'F14_STORAGE_JSON') from e
    _f14_validate_v1(shape, v)
    _f14_secret_keys_v1(v)
    _f14_require_v1(_f14_dumps_v1(v) == text, 'F14_STORAGE_NONCANONICAL')
    return v


def _f14_reconstruct_v1(row: dict[str, object], expected_id: str, expected_phase: str, expected_scope: dict[str, str]) -> tuple[PrivateEvidenceWitnessV1, dict[str, object]]:
    from .receipts import PrivateEvidenceWitnessV1, _f14_witness_v1
    _f14_validate_v1(_F14_ID, expected_id)
    _f14_validate_v1(_F14_SCOPE, expected_scope)
    _f14_require_v1(type(expected_phase) is str and expected_phase in _F14_PHASES, 'F14_STORAGE_PHASE')
    _f14_validate_v1(_f14_spine_shape_v1(expected_phase), row)
    _f14_require_v1(row['record_id'] == expected_id, 'F14_STORAGE_ID_BINDING')
    payload = row['typed_payload']
    body = _f14_load_canonical_v1(payload['canonical_payload_json'], _F14_PHASES[expected_phase])
    restored = _f14_witness_v1(payload['record_id'], expected_phase, body)
    _f14_require_v1(restored.record_id == expected_id and body['scope'] == expected_scope and (row['aggregate_id'] == expected_scope['ledger_account_ref']) and (row['context_ref'] == expected_scope['source_context_ref']), 'F14_STORAGE_SCOPE_BINDING')
    _f14_require_v1(row['causation_id'] != row['correlation_id'] and row['traceparent'] not in {row['record_id'], row['aggregate_id'], row['causation_id'], row['correlation_id']}, 'F14_STORAGE_TRACE')
    _f14_require_v1(row['effective_at'] == row['recorded_at'], 'F14_STORAGE_WRAPPER_TIME')
    field = {'TRANSPORT': 'parse_completed_at', 'CAPTURE_COMMIT': 'completed_at', 'PUBLICATION': 'published_at', 'COMPANION_COMMIT': 'completed_at'}.get(expected_phase)
    if field:
        _f14_require_v1(row['recorded_at'] == _f14_native_time_v1(body[field])[1], 'F14_STORAGE_WRAPPER_TIME')
    return (restored, copy.deepcopy(body))


def _f14_hydrate_v1(text: str, expected_id: str, expected_phase: str, expected_scope: dict[str, str]) -> tuple[PrivateEvidenceWitnessV1, dict[str, object]]:
    from .receipts import PrivateEvidenceWitnessV1, _f14_witness_v1
    _f14_require_v1(type(expected_phase) is str and expected_phase in _F14_PHASES, 'F14_STORAGE_PHASE')
    row = _f14_load_canonical_v1(text, _f14_spine_shape_v1(expected_phase))
    return _f14_reconstruct_v1(row, expected_id, expected_phase, expected_scope)


def _f14_nullable_v1(shape: _F14ShapeV1) -> _F14ShapeV1:
    return _F14ShapeV1('nullable', item=shape)


def _f14_sequence_v1(*shapes: Shape) -> _F14ShapeV1:
    return _F14ShapeV1('sequence', fields=tuple(((str(i), s) for i, s in enumerate(shapes))))


def _f14_json_text_v1(shape: _F14ShapeV1) -> _F14ShapeV1:
    return _F14ShapeV1('json_text', item=shape)


_F14_CLOCK_ROLES = ('provider_publication_time_utc_or_none', 'revision_effective_time_utc_or_none', 'settlement_finality_time_utc_or_none')


_F14_CLOCKS = _f14_obj_v1(provider_event_time_utc_or_none=_f14_nullable_v1(_F14_TS), **{k: _f14_nullable_v1(_F14_TS) for k in _F14_CLOCK_ROLES}, **{k: _F14_TS for k in ('qtt_received_at_utc', 'qtt_parse_completed_at_utc', 'durable_commit_completed_at_utc', 'strategy_available_at_utc')}, **{k: _F14_INTEGER for k in ('qtt_received_monotonic_ns', 'qtt_parse_completed_monotonic_ns', 'durable_commit_completed_monotonic_ns', 'strategy_available_monotonic_ns', 'wall_clock_uncertainty_ns')}, **{k: _F14_ID for k in ('process_epoch_id', 'monotonic_clock_id', 'wall_clock_source_id', 'clock_quality_receipt_ref')})


_F14_CLOCK_BODY = _f14_obj_v1(schema_version=_f14_enum_v1('1'), record_id=_F14_ID, scope=_F14_SCOPE, raw_record_ref=_F14_ID, raw_body_utf8=_F14ShapeV1('raw_json_utf8', _F14_MAX_RAW_BYTES), raw_byte_limit=_F14ShapeV1('integer', _F14_MAX_RAW_BYTES), provider_event_pointer_or_none=_f14_nullable_v1(_F14ShapeV1('text', 1024)), clock_proof_refs=_f14_obj_v1(**{k: _f14_nullable_v1(_F14_ID) for k in _F14_CLOCK_ROLES}), clocks=_F14_CLOCKS, capture_commit_ref=_F14_ID, publication_witness_ref=_F14_ID, commit_evidence_class=_f14_enum_v1(*_F14_COMMIT_CLASSES), issued_at=_F14_TS, issued_monotonic_ns=_F14_INTEGER)


_F14_CLOCK_PAYLOAD = _f14_obj_v1(record_id=_F14_ID, canonical_payload_json=_f14_json_text_v1(_F14_CLOCK_BODY))


_F14_FIELDS = dict(_f14_spine_shape_v1('RAW').fields)


_F14_FIELDS['record_type'] = _f14_enum_v1('PRIVATE_OBSERVATION_CLOCK')


_F14_FIELDS['typed_payload'] = _F14_CLOCK_PAYLOAD


_F14_CLOCK_SPINE = _f14_obj_v1(**_F14_FIELDS)


_F14_INTENT = _f14_obj_v1(outbox_intent_id=_F14_ID, topic_class=_f14_enum_v1('PRIVATE_OBSERVATION_REFERENCE_PUBLICATION'), aggregate_id=_F14_ID, payload_record_ref=_F14_ID, created_at=_F14_SQL_TIME, dispatch_state=_f14_enum_v1('RECORDED_NOT_DISPATCHABLE'), dispatch_attempt_count=_F14ShapeV1('literal', options=(0,)), next_eligible_at=_F14_NULL, authority_class=_f14_enum_v1('NO_WRITE_CONTRACT_ONLY'))


_F14_TRANSITION = _f14_obj_v1(transition_id=_F14_ID, aggregate_id=_F14_ID, transition_family=_f14_enum_v1('UNIT_OF_WORK_STATE_MACHINE_V1'), prior_state=_f14_enum_v1('COMMITTING'), event_class=_F14_ID, candidate_state=_f14_enum_v1('COMMITTED'), disposition=_f14_enum_v1('ACCEPTED'), event_identity=_F14_ID, aggregate_version_before=_F14ShapeV1('literal', options=(0,)), aggregate_version_after=_F14ShapeV1('literal', options=(1,)), effective_at=_F14_SQL_TIME, recorded_at=_F14_SQL_TIME, reason_code=_F14_ID, reconciliation_required=_F14_FALSE)


_F14_RESULT_BINDING = _f14_obj_v1(binding_id=_F14_ID, claim_ref=_F14ShapeV1('id', 248), result_record_ref=_F14_ID, created_at=_F14_SQL_TIME)


def _f14_phase_shapes_v1(proofs: int) -> dict[str, dict[str, _F14ShapeV1]]:
    _f14_require_v1(type(proofs) is int and 0 <= proofs <= 3, 'F14_PHYSICAL_PROOFS')
    receipts = {'A': _f14_sequence_v1(_f14_spine_shape_v1('RAW'), _f14_spine_shape_v1('TRANSPORT')), 'B': _f14_sequence_v1(_f14_spine_shape_v1('CAPTURE_COMMIT'), _f14_spine_shape_v1('PUBLICATION'), _F14_CLOCK_SPINE, *[_f14_spine_shape_v1('CLOCK_PROOF') for _ in range(proofs)]), 'C': _f14_sequence_v1(_f14_spine_shape_v1('COMPANION_COMMIT'))}
    result = {}
    for phase, records in receipts.items():
        request = _f14_obj_v1(phase=_f14_enum_v1(phase), scope=_F14_SCOPE, receipt_records=records, publication_intent_or_none=_F14_INTENT if phase == 'A' else _F14_NULL, state_transition=_F14_TRANSITION)
        claim = _f14_obj_v1(claim_id=_F14ShapeV1('id', 248), idempotency_key=_F14_ID, identity_class=_f14_enum_v1('PRIVATE_EVIDENCE_PHASE_REFERENCE_ONLY'), canonical_request_json=_f14_json_text_v1(request), claim_state=_f14_enum_v1('ACQUIRED'), result_record_ref=_F14_NULL, created_at=_F14_SQL_TIME, completed_at=_F14_NULL, failure_code=_F14_NULL)
        result[phase] = dict(request=request, claim=claim, result_binding=_F14_RESULT_BINDING, transition=_F14_TRANSITION, receipts=records, publication_intent=_F14_INTENT if phase == 'A' else _F14_NULL)
    return result


def _f14_hydrate_clock_v1(text: str, expected_id: str, expected_scope: dict[str, str]) -> dict[str, object]:
    from .receipts import _native_retail_clock_companion
    'New-profile envelope checks then unchanged full companion conformance.'
    _f14_validate_v1(_F14_ID, expected_id)
    _f14_validate_v1(_F14_SCOPE, expected_scope)
    row = _f14_load_canonical_v1(text, _F14_CLOCK_SPINE)
    body = _f14_load_canonical_v1(row['typed_payload']['canonical_payload_json'], _F14_CLOCK_BODY)
    _f14_require_v1(row['record_id'] == row['typed_payload']['record_id'] == body['record_id'] == expected_id, 'F14_STORAGE_ID_BINDING')
    _f14_require_v1(body['scope'] == expected_scope and row['aggregate_id'] == expected_scope['ledger_account_ref'] and (row['context_ref'] == expected_scope['source_context_ref']), 'F14_STORAGE_SCOPE_BINDING')
    _f14_require_v1(row['effective_at'] == row['recorded_at'] == _f14_native_time_v1(body['issued_at'])[1], 'F14_STORAGE_WRAPPER_TIME')
    _f14_require_v1(row['causation_id'] != row['correlation_id'] and row['traceparent'] not in {row['record_id'], row['aggregate_id'], row['causation_id'], row['correlation_id']}, 'F14_STORAGE_TRACE')
    checked = _native_retail_clock_companion(body)
    _f14_require_v1(checked['canonical_payload_json'] == row['typed_payload']['canonical_payload_json'], 'F14_STORAGE_NONCANONICAL')
    return copy.deepcopy(body)


def _f14_hydrate_phase_controls_v1(claim_text: str, binding_text: str, *, phase: str, proof_count: int, expected_scope: dict[str, str]) -> dict[str, object]:
    """Reconstruct a complete phase's control joins; authenticate no issuer."""
    _f14_require_v1(type(phase) is str and phase in ('A', 'B', 'C'), 'F14_STORAGE_PHASE')
    _f14_validate_v1(_F14_SCOPE, expected_scope)
    shapes = _f14_phase_shapes_v1(proof_count)[phase]
    claim = _f14_load_canonical_v1(claim_text, shapes['claim'])
    binding = _f14_load_canonical_v1(binding_text, _F14_RESULT_BINDING)
    request = _f14_load_canonical_v1(claim['canonical_request_json'], shapes['request'])
    _f14_require_v1(request['scope'] == expected_scope, 'F14_STORAGE_SCOPE_BINDING')
    expected_phases = {'A': ['RAW', 'TRANSPORT'], 'B': ['CAPTURE_COMMIT', 'PUBLICATION', None] + ['CLOCK_PROOF'] * proof_count, 'C': ['COMPANION_COMMIT']}[phase]
    records = request['receipt_records']
    ids = []
    for row, kind in zip(records, expected_phases, strict=True):
        rid = row['record_id']
        ids.append(rid)
        if kind is None:
            _f14_hydrate_clock_v1(_f14_dumps_v1(row), rid, expected_scope)
        else:
            _f14_reconstruct_v1(row, rid, kind, expected_scope)
    result = records[2 if phase == 'B' else 0]['record_id']
    transition = request['state_transition']
    _f14_require_v1(transition['recorded_at'] == transition['effective_at'], 'F14_STORAGE_WRAPPER_TIME')
    _f14_require_v1(binding['binding_id'] == claim['claim_id'] + '::RESULT' and binding['claim_ref'] == claim['claim_id'] and (binding['result_record_ref'] == result), 'F14_CONTROL_RESULT_BINDING')
    _f14_require_v1(binding['created_at'] == transition['recorded_at'], 'F14_CONTROL_TIME_BINDING')
    _f14_require_v1(datetime.fromisoformat(claim['created_at']) <= datetime.fromisoformat(binding['created_at']), 'F14_CONTROL_TIME_BINDING')
    ids.extend((claim['claim_id'], binding['binding_id'], transition['transition_id']))
    if phase == 'A':
        intent = request['publication_intent_or_none']
        ids.append(intent['outbox_intent_id'])
        _f14_require_v1(intent['payload_record_ref'] == records[0]['record_id'] and intent['aggregate_id'] == expected_scope['ledger_account_ref'], 'F14_CONTROL_INTENT_BINDING')
    _f14_require_v1(len(ids) == len(set(ids)), 'F14_CONTROL_ID_ALIAS')
    return copy.deepcopy(dict(claim=claim, binding=binding, request=request))


_F14_STORAGE_TABLES = ('receipt_records', 'value_lineage_edges', 'economic_events', 'journal_transactions', 'journal_postings', 'state_transitions', 'idempotency_claims', 'outbox_intents', 'reversal_links', 'reconciliation_breaks')


def _f14_hydrate_phase_storage_view_v1(table_rows: dict[str, dict[str, str]], *, phase: str, proof_count: int, expected_scope: dict[str, str], receipt_refs: tuple[str, ...], claim_ref: str, result_binding_ref: str, transition_ref: str, unit_of_work_id: str, publication_intent_ref: str | None) -> dict[str, object]:
    """Compare actual selected storage payloads with their persisted phase plan.

    The caller must obtain this query-scoped view under the EXISTING adapter's
    committed snapshot and cross-table lookup. A dictionary cannot authenticate
    storage or source custody. This pure specification adds neither a database,
    table, issuer, runtime service nor a current-repository implementation.
    Both claim and result binding inhabit idempotency_claims in current QTT.
    """
    shapes = _f14_phase_shapes_v1(proof_count)
    _f14_require_v1(type(phase) is str and phase in shapes, 'F14_STORAGE_PHASE')
    _f14_validate_v1(_F14_SCOPE, expected_scope)
    count = {'A': 2, 'B': 3 + proof_count, 'C': 1}[phase]
    _f14_require_v1(type(receipt_refs) is tuple and len(receipt_refs) == count, 'F14_STORAGE_VIEW_REFS')
    refs = (*receipt_refs, claim_ref, result_binding_ref, transition_ref)
    for rid in (*refs, unit_of_work_id):
        _f14_validate_v1(_F14_ID, rid)
    _f14_validate_v1(_F14ShapeV1('id', 248), claim_ref)
    if phase == 'A':
        _f14_validate_v1(_F14_ID, publication_intent_ref)
        refs += (publication_intent_ref,)
    else:
        _f14_require_v1(publication_intent_ref is None, 'F14_STORAGE_VIEW_REFS')
    _f14_require_v1(len(refs) == len(set(refs)), 'F14_CONTROL_ID_ALIAS')
    _f14_require_v1(result_binding_ref == claim_ref + '::RESULT', 'F14_CONTROL_RESULT_BINDING')
    _f14_require_v1(type(table_rows) is dict and set(table_rows) == set(_F14_STORAGE_TABLES), 'F14_STORAGE_VIEW_TABLES')
    expected = {name: set() for name in _F14_STORAGE_TABLES}
    expected['receipt_records'] = set(receipt_refs)
    expected['idempotency_claims'] = {claim_ref, result_binding_ref}
    expected['state_transitions'] = {transition_ref}
    if phase == 'A':
        expected['outbox_intents'] = {publication_intent_ref}
    for name, rows in table_rows.items():
        _f14_require_v1(type(rows) is dict and set(rows) == expected[name], 'F14_STORAGE_VIEW_MEMBERSHIP')
        _f14_require_v1(all((type(text) is str for text in rows.values())), 'F14_STORAGE_TEXT')
    restored = _f14_hydrate_phase_controls_v1(table_rows['idempotency_claims'][claim_ref], table_rows['idempotency_claims'][result_binding_ref], phase=phase, proof_count=proof_count, expected_scope=expected_scope)
    claim = restored['claim']
    binding = restored['binding']
    request = restored['request']
    _f14_require_v1(claim['claim_id'] == claim_ref and binding['binding_id'] == result_binding_ref, 'F14_STORAGE_ID_BINDING')
    _f14_require_v1(tuple((row['record_id'] for row in request['receipt_records'])) == receipt_refs, 'F14_STORAGE_VIEW_REFS')
    for row in request['receipt_records']:
        _f14_require_v1(table_rows['receipt_records'][row['record_id']] == _f14_dumps_v1(row), 'F14_STORAGE_PLAN_ACTUAL_MISMATCH')
    transition = request['state_transition']
    _f14_require_v1(transition['transition_id'] == transition_ref and transition['aggregate_id'] == unit_of_work_id, 'F14_CONTROL_UOW_BINDING')
    _f14_require_v1(table_rows['state_transitions'][transition_ref] == _f14_dumps_v1(transition), 'F14_STORAGE_PLAN_ACTUAL_MISMATCH')
    if phase == 'A':
        intent = request['publication_intent_or_none']
        _f14_require_v1(intent['outbox_intent_id'] == publication_intent_ref, 'F14_STORAGE_ID_BINDING')
        _f14_require_v1(table_rows['outbox_intents'][publication_intent_ref] == _f14_dumps_v1(intent), 'F14_STORAGE_PLAN_ACTUAL_MISMATCH')
    return copy.deepcopy(restored)



def _f14_secret_keys_v1(value: object) -> None:
    if type(value) is dict:
        for key, item in value.items():
            _f14_require_v1(type(key) is str, "F14_STORAGE_FIELDS")
            _f14_require_v1(not SECRET_KEY_POLICY.is_secret_key(key), "F14_STORAGE_SECRET")
            _f14_secret_keys_v1(item)
    elif type(value) is list:
        for item in value:
            _f14_secret_keys_v1(item)



# Fixed limits from the supplied offline structural proof, not runtime bound scans.
_F14_SHAPE_LIMITS = {


    _F14_PHASES['RAW']: (2103453, 17, 2),


    _f14_spine_shape_v1('RAW'): (4217972, 59, 2),


    _F14_PHASES['TRANSPORT']: (17137, 57, 2),


    _f14_spine_shape_v1('TRANSPORT'): (45346, 59, 2),


    _F14_PHASES['CAPTURE_COMMIT']: (112309, 129, 2),


    _f14_spine_shape_v1('CAPTURE_COMMIT'): (235695, 59, 2),


    _F14_PHASES['PUBLICATION']: (12693, 33, 2),


    _f14_spine_shape_v1('PUBLICATION'): (36460, 59, 2),


    _F14_PHASES['COMPANION_COMMIT']: (112309, 129, 2),


    _f14_spine_shape_v1('COMPANION_COMMIT'): (235697, 59, 2),


    _F14_PHASES['CLOCK_PROOF']: (9467, 23, 2),


    _f14_spine_shape_v1('CLOCK_PROOF'): (30008, 59, 2),


    _F14_CLOCK_BODY: (2120246, 81, 2),


    _F14_CLOCK_SPINE: (4251545, 57, 2),


    _F14_RESULT_BINDING: (3143, 9, 1),


    _F14_INTENT: (3382, 19, 1),


    _F14_TRANSITION: (5534, 29, 1),


    _f14_phase_shapes_v1(0)['A']['request']: (4278600, 187, 4),


    _f14_phase_shapes_v1(0)['A']['claim']: (8559475, 19, 1),


    _f14_phase_shapes_v1(0)['B']['request']: (4535605, 226, 4),


    _f14_phase_shapes_v1(0)['B']['claim']: (9073485, 19, 1),


    _f14_phase_shapes_v1(0)['C']['request']: (247600, 110, 4),


    _f14_phase_shapes_v1(0)['C']['claim']: (497475, 19, 1),


    _f14_phase_shapes_v1(1)['A']['request']: (4278600, 187, 4),


    _f14_phase_shapes_v1(1)['A']['claim']: (8559475, 19, 1),


    _f14_phase_shapes_v1(1)['B']['request']: (4565614, 285, 4),


    _f14_phase_shapes_v1(1)['B']['claim']: (9133503, 19, 1),


    _f14_phase_shapes_v1(1)['C']['request']: (247600, 110, 4),


    _f14_phase_shapes_v1(1)['C']['claim']: (497475, 19, 1),


    _f14_phase_shapes_v1(2)['A']['request']: (4278600, 187, 4),


    _f14_phase_shapes_v1(2)['A']['claim']: (8559475, 19, 1),


    _f14_phase_shapes_v1(2)['B']['request']: (4595623, 344, 4),


    _f14_phase_shapes_v1(2)['B']['claim']: (9193521, 19, 1),


    _f14_phase_shapes_v1(2)['C']['request']: (247600, 110, 4),


    _f14_phase_shapes_v1(2)['C']['claim']: (497475, 19, 1),


    _f14_phase_shapes_v1(3)['A']['request']: (4278600, 187, 4),


    _f14_phase_shapes_v1(3)['A']['claim']: (8559475, 19, 1),


    _f14_phase_shapes_v1(3)['B']['request']: (4625632, 403, 4),


    _f14_phase_shapes_v1(3)['B']['claim']: (9253539, 19, 1),


    _f14_phase_shapes_v1(3)['C']['request']: (247600, 110, 4),


    _f14_phase_shapes_v1(3)['C']['claim']: (497475, 19, 1),


}
