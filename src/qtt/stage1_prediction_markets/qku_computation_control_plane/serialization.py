"""Deterministic JSON and cross-platform relative-path safety."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, fields, is_dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
import json
import math
import ntpath
import re
from pathlib import PureWindowsPath
import unicodedata
from typing import Any
from types import MappingProxyType

from .context import _native_bounded_decimal, _native_require, _native_text
from .errors import ContractValidationError, ReasonCode, SerializationSafetyError
from .context import is_nonnegative_json_integer_v1


@dataclass(frozen=True, slots=True)
class SecretKeyPolicyV1:
    """Immutable field-name policy shared by every secret-rejection surface."""

    forbidden_normalized_terms: frozenset[str]
    allowed_normalized_names: frozenset[str]

    @staticmethod
    def normalize(field_name: str) -> str:
        if not isinstance(field_name, str) or not field_name:
            return ""
        normalized = unicodedata.normalize("NFKC", field_name).casefold()
        return "".join(character for character in normalized if character.isalnum())

    def is_secret_key(self, field_name: str) -> bool:
        normalized = self.normalize(field_name)
        if not normalized or normalized in self.allowed_normalized_names:
            return False
        if normalized == "token" or normalized.endswith("token"):
            return True
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


def _native_strict_json(raw: bytes, max_bytes: int = 65536) -> Any:
    """Bounded raw JSON: lexical integers stay int; other numbers use Decimal."""
    _native_require(type(max_bytes) is int and 0 < max_bytes <= 1048576, "JSON_BUDGET")
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
        _native_require(nodes <= 4096, "JSON_NODES")
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


def _probability_transport_admission_v1(value: object, *, max_bytes: int) -> tuple[object, int]:
    """Admit every occurrence and retain its exact serialized byte measurement."""
    _native_require(type(max_bytes) is int and 0 < max_bytes <= 1048576, "JSON_BUDGET")
    used = nodes = 0
    active: set[int] = set()

    def charge(count: int) -> None:
        nonlocal used
        _native_require(count <= max_bytes - used, "JSON_BOUND")
        used += count

    def visit(item: object, depth: int) -> object:
        nonlocal nodes
        nodes += 1
        _native_require(nodes <= 4096, "JSON_NODES")
        _native_require(depth <= 16, "JSON_DEPTH")
        if item is None:
            charge(4)
            return None
        if type(item) is bool:
            charge(4 if item else 5)
            return item
        if type(item) is int:
            _native_require(-10**101 < item < 10**101, "NUMBER_BOUND")
            charge(len(str(item)))
            return item
        if type(item) is datetime:
            _native_require(item.tzinfo is timezone.utc, "PROBABILITY_UTC")
            item = item.isoformat()
        if type(item) is str:
            _native_require(len(item) + 2 <= max_bytes - used, "JSON_BOUND")
            charge(2)
            for character in item:
                point = ord(character)
                _native_require(not 0xD800 <= point <= 0xDFFF, "SURROGATE")
                if character in '"\\\b\f\n\r\t':
                    charge(2)
                elif point < 32:
                    charge(6)
                else:
                    charge(1 if point < 128 else 2 if point < 2048 else 3 if point < 65536 else 4)
            return item
        _native_require(type(item) in (dict, MappingProxyType, list, tuple), "PROBABILITY_WIRE_TYPE")
        _native_require(depth < 16, "JSON_DEPTH")
        _native_require(id(item) not in active, "PROBABILITY_WIRE_CYCLE")
        mapping = type(item) in (dict, MappingProxyType)
        _native_require(len(item) * (2 if mapping else 1) <= 4096 - nodes, "JSON_NODES")
        charge(2 + max(0, len(item) - 1) + (len(item) if mapping else 0))
        active.add(id(item))
        try:
            if mapping:
                # Check keys before sorting; foreign comparison/formatting is forbidden.
                _native_require(all(type(key) is str for key in item), "PROBABILITY_WIRE_KEY")
                return {visit(key, depth + 1): visit(item[key], depth + 1) for key in sorted(item)}
            return [visit(child, depth + 1) for child in item]
        finally:
            active.remove(id(item))

    owned = visit(value, 0)
    return owned, used


def _probability_transport_tree_v1(value: object, *, max_bytes: int) -> object:
    """Retain the existing tree-only interface for admitted frame consumers."""
    return _probability_transport_admission_v1(value, max_bytes=max_bytes)[0]


def _bounded_probability_json_v1(value: object, *, max_bytes: int) -> str:
    """V35-only bounded transport; retain the existing secret/path/parser policy."""
    owned, measured = _probability_transport_admission_v1(value, max_bytes=max_bytes)
    encoded = deterministic_json(owned)
    raw = encoded.encode("utf-8")
    _native_require(len(raw) == measured, "PROBABILITY_WIRE_BYTE_COUNT")
    _native_strict_json(raw, max_bytes)
    return encoded


def _probability_binary64_v1(value: object, *, probability: bool = False) -> float:
    """Decode canonical finite binary64 without crossing the Decimal boundary."""
    _native_require(type(probability) is bool, "PROBABILITY_CODEC_MODE")
    _native_require(type(value) is str and len(value) <= 80, "BINARY64_TEXT")
    _native_require(value.startswith(("0x", "-0x")), "BINARY64_TEXT")
    try:
        decoded = float.fromhex(value)
    except (ValueError, OverflowError) as exc:
        raise ContractValidationError(ReasonCode.SCHEMA_MISMATCH, "BINARY64_TEXT") from exc
    _native_require(math.isfinite(decoded) and decoded.hex() == value, "BINARY64_CANONICAL")
    if probability:
        _native_require(0.0 <= decoded <= 1.0 and value != "-0x0.0p+0", "PREDICTION_SCALAR")
    return decoded


def _probability_frame_bytes_v1(ordinal: int, path: list, tag: str, content: object) -> bytes:
    """Encode one frame without building an unbounded tagged intermediate tree."""
    parts: list[str] = []
    used = nodes = 0
    active: set[int] = set()

    def emit(token: str) -> None:
        nonlocal used
        size = len(token.encode("utf-8"))
        _native_require(size <= 65536 - used, "JSON_BOUND")
        used += size
        parts.append(token)

    def node(depth: int, *, container: bool = False) -> None:
        nonlocal nodes
        nodes += 1
        _native_require(nodes <= 4096, "JSON_NODES")
        _native_require(depth < 16 if container else depth <= 16, "JSON_DEPTH")

    def scalar(value: object, depth: int) -> None:
        node(depth)
        # Admission measures string code points before allocating escaped text.
        _probability_transport_tree_v1(value, max_bytes=max(1, 65536 - used))
        emit(json.dumps(value, ensure_ascii=False, allow_nan=False, separators=(",", ":")))

    def array(values: object, depth: int, child) -> None:
        node(depth, container=True)
        _native_require(len(values) <= 4096 - nodes, "JSON_NODES")
        emit("[")
        for index, value in enumerate(values):
            if index:
                emit(",")
            child(value, depth + 1)
        emit("]")

    def tagged(name: str, value: object, depth: int, child) -> None:
        node(depth, container=True)
        emit("{")
        scalar(name, depth + 1)
        emit(":")
        child(value, depth + 1)
        emit("}")

    def wire(value: object, depth: int) -> None:
        if value is None or type(value) in (bool, int, str):
            scalar(value, depth)
            return
        if type(value) is float:
            _native_require(math.isfinite(value), "PREDICTION_WIRE_NONFINITE")
            tagged("binary64", value.hex(), depth, scalar)
            return
        _native_require(type(value) in (dict, MappingProxyType, tuple, list), "PREDICTION_WIRE_TYPE")
        _native_require(id(value) not in active, "PREDICTION_WIRE_CYCLE")
        active.add(id(value))
        try:
            if type(value) in (dict, MappingProxyType):
                # Every mapping pair needs at least a key, value and pair node.
                _native_require(len(value) * 3 + 3 <= 4096 - nodes, "JSON_NODES")
                _native_require(all(type(key) is str for key in value), "PREDICTION_WIRE_KEY")
                keys = sorted(value)

                def pair(key, pair_depth):
                    node(pair_depth, container=True)
                    emit("[")
                    scalar(key, pair_depth + 1)
                    emit(",")
                    wire(value[key], pair_depth + 1)
                    emit("]")

                tagged("mapping", keys, depth, lambda items, d: array(items, d, pair))
            elif type(value) is tuple:
                tagged("tuple", value, depth, lambda items, d: array(items, d, wire))
            else:
                array(value, depth, wire)
        finally:
            active.remove(id(value))

    # Sorted canonical frame keys. Logical paths are not filesystem paths.
    node(0, container=True)
    emit("{")
    scalar("content", 1)
    emit(":")
    if tag == "VALUE":
        wire(content, 1)
    elif tag == "MAPPING":
        array(content, 1, scalar)
    else:
        scalar(content, 1)
    for key, value in (("ordinal", ordinal), ("path", path), ("tag", tag)):
        emit(",")
        scalar(key, 1)
        emit(":")
        if key == "path":
            array(value, 1, scalar)
        else:
            scalar(value, 1)
    emit("}")
    raw = "".join(parts).encode("utf-8")
    _native_strict_json(raw, 65536)
    return raw + b"\n"


def _iter_prediction_artifact_frames_v1(bank: object, *, max_bytes: int, max_frames: int):
    """Stream the fixed depth-first format; charge each LF before yielding it."""
    _native_require(type(max_bytes) is int and max_bytes > 0 and
                    type(max_frames) is int and max_frames > 0, "PREDICTION_ARTIFACT_BUDGET")
    ordinal = total = 0
    active: set[int] = set()

    def emit(value: object, path: list):
        nonlocal ordinal, total
        _native_require(len(path) <= 16 and ordinal < max_frames, "PREDICTION_FRAME_BUDGET")
        _native_require(id(value) not in active, "PREDICTION_WIRE_CYCLE")
        try:
            frame = _probability_frame_bytes_v1(ordinal, path, "VALUE", value)
        except ContractValidationError as exc:
            # Only the inherited representation bounds allow subdivision.
            if str(exc).split(": ", 1)[-1] not in {"JSON_BOUND", "JSON_NODES", "JSON_DEPTH"}:
                raise
            _native_require(type(value) in (dict, MappingProxyType, tuple, list),
                            "PREDICTION_FRAME_SCALAR_TOO_LARGE")
            _native_require(len(value) <= max_frames - ordinal - 1, "PREDICTION_FRAME_BUDGET")
            mapping = type(value) in (dict, MappingProxyType)
            if mapping:
                _native_require(all(type(k) is str for k in value), "PREDICTION_WIRE_KEY")
                # Header itself must fit before retaining its sorted key roster.
                _native_require(len(value) <= 4096 - 9 - len(path), "JSON_NODES")
                keys = sorted(value)
                frame = _probability_frame_bytes_v1(ordinal, path, "MAPPING", keys)
            else:
                frame = _probability_frame_bytes_v1(
                    ordinal, path, "TUPLE" if type(value) is tuple else "LIST", len(value))
            _native_require(len(frame) <= max_bytes - total, "PREDICTION_ARTIFACT_BUDGET")
            total += len(frame)
            ordinal += 1
            yield frame
            active.add(id(value))
            try:
                for key in keys if mapping else range(len(value)):
                    yield from emit(value[key], [*path, key])
            finally:
                active.remove(id(value))
        else:
            _native_require(len(frame) <= max_bytes - total, "PREDICTION_ARTIFACT_BUDGET")
            total += len(frame)
            ordinal += 1
            yield frame

    yield from emit(bank, [])


def _decode_prediction_artifact_v1(raw: bytes, *, max_bytes: int, max_frames: int) -> tuple[object, int]:
    """Decode only the data-only framed grammar; no type-selected construction."""
    import io

    _native_require(type(raw) is bytes and type(max_bytes) is int and 0 < len(raw) <= max_bytes
                    and type(max_frames) is int and max_frames > 0, "PREDICTION_ARTIFACT_BUDGET")
    stream = io.BytesIO(raw)
    ordinal = 0

    def unwire(value):
        if value is None or type(value) in (bool, int, str):
            return value
        if type(value) is list:
            return [unwire(v) for v in value]
        _native_require(type(value) is dict and len(value) == 1, "PREDICTION_WIRE_TAG")
        if set(value) == {"binary64"}:
            return _probability_binary64_v1(value["binary64"])
        if set(value) == {"tuple"}:
            _native_require(type(value["tuple"]) is list, "PREDICTION_WIRE_TUPLE")
            return tuple(unwire(v) for v in value["tuple"])
        _native_require(set(value) == {"mapping"} and type(value["mapping"]) is list,
                        "PREDICTION_WIRE_TAG")
        rows = value["mapping"]
        _native_require(all(type(row) is list and len(row) == 2 and type(row[0]) is str for row in rows),
                        "PREDICTION_WIRE_MAPPING")
        keys = [row[0] for row in rows]
        _native_require(keys == sorted(keys) and len(keys) == len(set(keys)), "PREDICTION_WIRE_MAPPING")
        return {key: unwire(value) for key, value in rows}

    def read(path: list, depth: int):
        nonlocal ordinal
        _native_require(depth <= 16 and ordinal < max_frames, "PREDICTION_FRAME_BUDGET")
        line = stream.readline(65538)
        _native_require(line.endswith(b"\n") and len(line) <= 65537, "PREDICTION_FRAME_BYTES")
        frame = _native_strict_json(line[:-1], 65536)
        _native_require(type(frame) is dict and set(frame) == {"ordinal", "path", "tag", "content"},
                        "PREDICTION_FRAME_FIELDS")
        _native_require(type(frame["ordinal"]) is int and frame["ordinal"] == ordinal and
                        type(frame["path"]) is list and len(frame["path"]) == len(path) and
                        all(type(a) is type(b) and a == b for a, b in zip(frame["path"], path)),
                        "PREDICTION_FRAME_ORDER")
        _native_require(type(frame["tag"]) is str, "PREDICTION_FRAME_TAG")
        # Reject Decimal real tokens rather than coercing them during canonicalization.
        owned = _probability_transport_tree_v1(frame, max_bytes=65536)
        canonical = json.dumps(owned, sort_keys=True, ensure_ascii=False, allow_nan=False,
                               separators=(",", ":")).encode("utf-8") + b"\n"
        _native_require(canonical == line, "PREDICTION_FRAME_CANONICAL")
        ordinal += 1
        tag, content = frame["tag"], frame["content"]
        if tag == "VALUE":
            return unwire(content)
        if tag == "MAPPING":
            _native_require(type(content) is list and all(type(k) is str for k in content) and
                            content == sorted(content) and len(content) == len(set(content)) and
                            len(content) <= max_frames - ordinal, "PREDICTION_FRAME_CONTAINER")
            return {key: read([*path, key], depth + 1) for key in content}
        _native_require(tag in ("TUPLE", "LIST") and type(content) is int and
                        0 <= content <= max_frames - ordinal, "PREDICTION_FRAME_CONTAINER")
        values = [read([*path, i], depth + 1) for i in range(content)]
        return tuple(values) if tag == "TUPLE" else values

    result = read([], 0)
    _native_require(stream.read(1) == b"", "PREDICTION_TRAILING_FRAME")
    return result, ordinal


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


# Closed frame codec for the four existing input-artifact roles.
_PROBABILITY_INPUT_ROLES_V1 = ('MODEL', 'CATALOG', 'RESULT', 'POLICY')
_PROBABILITY_INPUT_TUPLES_V1 = {
    'MODEL': frozenset(('feature_names', 'reference_clusters', 'targets', 'target_domains', 'dependency_refs')),
    'CATALOG': frozenset(('rows', 'dependency_refs')),
    'RESULT': frozenset(('cluster_ids', 'original_row_ids', 'targets', 'partition_codes',
                         'reference_values', 'current_values', 'reference_records', 'current_records', 'dependency_refs')),
    'POLICY': frozenset(('expected_environment',)),
}


def _probability_input_classes_v1():
    from .models import (_ProbabilityAdmissionModelV1, _ProbabilityAdmissionCatalogV1,
                         _ProbabilityAdmissionResultV1, _ProbabilityAdmissionLimitsV1)
    return {'MODEL': _ProbabilityAdmissionModelV1, 'CATALOG': _ProbabilityAdmissionCatalogV1,
            'RESULT': _ProbabilityAdmissionResultV1, 'POLICY': _ProbabilityAdmissionLimitsV1}


def _probability_input_canonical_v1(value):
    return _bounded_probability_json_v1(value, max_bytes=1048576)


def _probability_input_fields_v1(role):
    from .models import ProbabilityProducerScopeV1, _ProbabilityMaturityClusterV1, _ProbabilityAdmissionLimitsV1, _ProbabilityMaterializationReadBudgetV1, _probability_require_v1, _probability_projection_integer_v1, _probability_projection_text_v1
    _probability_require_v1(role in _PROBABILITY_INPUT_ROLES_V1, 'MATERIALIZATION_ROLE')
    fields = tuple(_probability_input_classes_v1()[role].__dataclass_fields__)
    return fields + (('expected_environment',) if role == 'POLICY' else ())

def _validate_probability_input_fields_v1(role, values):
    from .models import ProbabilityProducerScopeV1, _ProbabilityMaturityClusterV1, _ProbabilityAdmissionLimitsV1, _ProbabilityMaterializationReadBudgetV1, _probability_require_v1, _probability_projection_integer_v1, _probability_projection_text_v1
    'Storage shape validation only; numerical admission remains its old owner.'
    signed = {'MODEL': {'reference_cutoff_ns', 'available_ns', 'valid_until_ns'}, 'CATALOG': {'complete_through_ns'}, 'RESULT': {'selection_cutoff_ns', 'available_ns'}, 'POLICY': set()}
    integers = {'MODEL': {'replicate_count'}, 'CATALOG': {'owner_epoch', 'after_ordinal'}, 'RESULT': {'owner_epoch', 'replicate_count'}, 'POLICY': set(_ProbabilityAdmissionLimitsV1.__dataclass_fields__)}
    pairs = {'target_domains', 'reference_values', 'current_values', 'expected_environment'}
    for name, value in values.items():
        if name == 'scope':
            _probability_require_v1(type(value) is ProbabilityProducerScopeV1, 'MATERIALIZATION_SCOPE')
        elif name in ('reference_clusters', 'rows'):
            _probability_require_v1(type(value) is tuple and all((type(x) is _ProbabilityMaturityClusterV1 for x in value)), 'MATERIALIZATION_CATALOG_ROW')
        elif name in signed[role]:
            _probability_projection_integer_v1(value, 'MATERIALIZATION_FIELD_TYPE', None)
        elif name in integers[role]:
            minimum = 1 if role == 'POLICY' or name == 'replicate_count' else 0
            _probability_projection_integer_v1(value, 'MATERIALIZATION_FIELD_TYPE', minimum)
        elif name in pairs:
            _probability_require_v1(type(value) is tuple and all((type(row) is tuple and len(row) == 2 and all((type(x) is str for x in row)) for row in value)), 'MATERIALIZATION_PAIRS')
        elif name == 'partition_codes':
            _probability_require_v1(type(value) is tuple and len(value) == 2 and all((type(x) is int for x in value)) and (value == (3, 4)), 'MATERIALIZATION_PARTITION')
        elif name in _PROBABILITY_INPUT_TUPLES_V1[role]:
            _probability_require_v1(type(value) is tuple and all((type(x) is str for x in value)), 'MATERIALIZATION_FIELD_TYPE')
        elif name == 'precision_protocol_ref' and value is None:
            pass
        else:
            _probability_require_v1(type(value) is str, 'MATERIALIZATION_FIELD_TYPE')
            if name != 'export_text':
                _probability_projection_text_v1(value, 'MATERIALIZATION_FIELD_TYPE')

def _iter_probability_input_object_frames_v1(role, obj, *, budget, expected_environment=None):
    """Emit only the four fixed data-only schemas, charging before each yield."""
    from .models import (ProbabilityProducerScopeV1, _ProbabilityMaturityClusterV1,
                         _ProbabilityMaterializationReadBudgetV1, _probability_require_v1)
    need = _probability_require_v1
    need(type(role) is str and role in _PROBABILITY_INPUT_ROLES_V1, "MATERIALIZATION_ROLE")
    need(type(budget) is _ProbabilityMaterializationReadBudgetV1 and
         type(obj) is _probability_input_classes_v1()[role], "MATERIALIZATION_OBJECT_TYPE")
    budget.__post_init__()
    values = {name: getattr(obj, name) for name in obj.__dataclass_fields__}
    if role == "POLICY":
        values["expected_environment"] = expected_environment
    else:
        need(expected_environment is None, "MATERIALIZATION_UNEXPECTED_ENVIRONMENT")
    _validate_probability_input_fields_v1(role, values)
    count = 1 + len(values)
    for name in _PROBABILITY_INPUT_TUPLES_V1[role]:
        need(len(values[name]) <= budget.max_frames - count, "MATERIALIZATION_ARTIFACT_BUDGET")
        count += len(values[name])
    need(count <= budget.max_frames, "MATERIALIZATION_ARTIFACT_BUDGET")
    total = 0

    def project(value):
        if type(value) in (ProbabilityProducerScopeV1, _ProbabilityMaturityClusterV1):
            value.__post_init__()
            return {name: getattr(value, name) for name in value.__dataclass_fields__}
        return value

    def frame(value):
        nonlocal total
        text = _bounded_probability_json_v1(value, max_bytes=min(budget.max_frame_bytes,
                                                                budget.max_total_bytes - total))
        raw = text.encode("utf-8", "strict")
        need(total + len(raw) <= budget.max_total_bytes, "MATERIALIZATION_ARTIFACT_BUDGET")
        total += len(raw)
        return raw

    yield frame({"schema_version": "V35_INPUT_OBJECT_REFERENCE_V1", "role": role})
    for name in _probability_input_fields_v1(role):
        value = values[name]
        if name in _PROBABILITY_INPUT_TUPLES_V1[role]:
            yield frame({"field": name, "count": len(value)})
            for item in value:
                yield frame({"item": project(item)})
        else:
            yield frame({"field": name, "value": project(value)})


def _decode_probability_input_object_v1(role, frames, budget):
    from .models import ProbabilityProducerScopeV1, _ProbabilityMaturityClusterV1, _ProbabilityAdmissionLimitsV1, _ProbabilityMaterializationReadBudgetV1, _probability_require_v1, _probability_projection_integer_v1, _probability_projection_text_v1
    'Closed, ordered, frame-bounded parser; never imports a payload class name.'
    _probability_require_v1(type(budget) is _ProbabilityMaterializationReadBudgetV1, 'MATERIALIZATION_READ_BUDGET')
    _probability_require_v1(type(frames) is tuple and all((type(frame) is bytes for frame in frames)), 'MATERIALIZATION_ARTIFACT_TYPE')
    _probability_require_v1(len(frames) <= budget.max_frames and sum(map(len, frames)) <= budget.max_total_bytes, 'MATERIALIZATION_ARTIFACT_BUDGET')
    position = 0

    def take():
        nonlocal position
        _probability_require_v1(position < len(frames), 'MATERIALIZATION_FRAME_MISSING')
        raw = frames[position]
        position += 1
        value = _native_strict_json(raw, budget.max_frame_bytes)
        _probability_require_v1(type(value) is dict, 'MATERIALIZATION_FRAME_SHAPE')
        _probability_require_v1(_probability_input_canonical_v1(value).encode('utf-8') == raw, 'MATERIALIZATION_NONCANONICAL')
        return value
    _probability_require_v1(take() == {'schema_version': 'V35_INPUT_OBJECT_REFERENCE_V1', 'role': role}, 'MATERIALIZATION_OBJECT_HEADER')
    values = {}
    for name in _probability_input_fields_v1(role):
        row = take()
        if name in _PROBABILITY_INPUT_TUPLES_V1[role]:
            _probability_require_v1(set(row) == {'field', 'count'} and row['field'] == name, 'MATERIALIZATION_FIELD_ORDER')
            count = _probability_projection_integer_v1(row['count'], 'MATERIALIZATION_COUNT')
            _probability_require_v1(count <= budget.max_frames and count <= len(frames) - position, 'MATERIALIZATION_COUNT')
            items = []
            for _ in range(count):
                item = take()
                _probability_require_v1(set(item) == {'item'}, 'MATERIALIZATION_ITEM_SHAPE')
                items.append(item['item'])
            values[name] = tuple(items)
        else:
            _probability_require_v1(set(row) == {'field', 'value'} and row['field'] == name, 'MATERIALIZATION_FIELD_ORDER')
            values[name] = row['value']
    _probability_require_v1(position == len(frames), 'MATERIALIZATION_TRAILING_FRAMES')
    if 'scope' in values:
        _probability_require_v1(type(values['scope']) is dict and set(values['scope']) == set(ProbabilityProducerScopeV1.__dataclass_fields__), 'MATERIALIZATION_SCOPE')
        values['scope'] = ProbabilityProducerScopeV1(**values['scope'])
    for name in ('reference_clusters', 'rows'):
        if name in values:
            restored = []
            for row in values[name]:
                _probability_require_v1(type(row) is dict and set(row) == set(_ProbabilityMaturityClusterV1.__dataclass_fields__), 'MATERIALIZATION_CATALOG_ROW')
                row = dict(row)
                _probability_require_v1(type(row['row_ids']) is list, 'MATERIALIZATION_ROW_IDS')
                row['row_ids'] = tuple(row['row_ids'])
                restored.append(_ProbabilityMaturityClusterV1(**row))
            values[name] = tuple(restored)
    for name in ('target_domains', 'reference_values', 'current_values', 'expected_environment'):
        if name in values:
            _probability_require_v1(all((type(row) is list and len(row) == 2 for row in values[name])), 'MATERIALIZATION_PAIRS')
            values[name] = tuple((tuple(row) for row in values[name]))
    _validate_probability_input_fields_v1(role, values)
    environment = values.pop('expected_environment', None)
    obj = _probability_input_classes_v1()[role](**values)
    return (obj, environment)

# One process-local report acquisition binding. The runner installs this only
# inside its admitted lifecycle; a family is source-fixed, never caller-selected
# by profile JSON. This is not an authority or a sandbox.
_REPORT_READ_BINDING_V1 = None


def _report_read_json_v1(path, *, family):
    from pathlib import Path
    import os
    if type(family) is not str or family not in ("QB", "QC", "MAPPER"):
        raise ValueError("REPORT_UNKNOWN_READER_FAMILY")
    active = _REPORT_READ_BINDING_V1
    if active is not None:
        selected_family, reader = active
        if selected_family != family:
            raise ValueError("REPORT_READER_FAMILY_MISMATCH")
        path = Path(path)
        selected = path if path.is_absolute() else reader.root / path
        return reader.read_json(selected.relative_to(reader.root).as_posix(), _report_json_object_v1)
    if any(key.upper().startswith("QTT_MAPPER_") for key in os.environ):
        raise ValueError("MAPPER_PROFILE_PRESENT_WITHOUT_ACTIVE_READER")
    return _report_json_object_v1(path.read_text(encoding="utf-8"))


def _report_json_object_v1(text: str) -> dict[str, Any]:
    """Decode one report object; this creates no schema or source acceptance."""
    if type(text) is not str:
        raise SerializationSafetyError(ReasonCode.SERIALIZATION_UNSAFE, "report JSON must be text")

    def object_pairs(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise SerializationSafetyError(ReasonCode.SERIALIZATION_UNSAFE, "duplicate report JSON key")
            result[key] = value
        return result

    def finite_number(token):
        value = float(token)
        if not math.isfinite(value):
            raise SerializationSafetyError(ReasonCode.SERIALIZATION_UNSAFE, "nonfinite report JSON number")
        return value

    def reject_constant(_token):
        raise SerializationSafetyError(ReasonCode.SERIALIZATION_UNSAFE, "nonfinite report JSON constant")

    value = json.loads(text, object_pairs_hook=object_pairs, parse_float=finite_number, parse_constant=reject_constant)
    if type(value) is not dict:
        raise SerializationSafetyError(ReasonCode.SERIALIZATION_UNSAFE, "report JSON root must be an object")
    # Stack storage follows depth; do not flatten all rows or all string values.
    stack = [iter((value,))]
    while stack:
        try:
            item = next(stack[-1])
        except StopIteration:
            stack.pop()
            continue
        if type(item) is str:
            if any(0xD800 <= ord(char) <= 0xDFFF for char in item):
                raise SerializationSafetyError(ReasonCode.SERIALIZATION_UNSAFE, "unpaired report Unicode surrogate")
        elif type(item) is dict:
            stack.append(iter(part for pair in item.items() for part in pair))
        elif type(item) is list:
            stack.append(iter(item))
    return value

def _report_directory_entries_v1(directory, *, allow_absent=False):
    """Return a complete flat inventory or raise; never hide scan failures.

    Names alone are inventoried. Entries are not opened or recursively followed.
    This is a validation-only helper, not a sandbox or a resource admission owner.
    """
    import os
    import stat
    from pathlib import Path

    if not isinstance(directory, Path) or type(allow_absent) is not bool:
        raise SerializationSafetyError(ReasonCode.PATH_UNSAFE, "invalid report directory request")
    path = directory.absolute()
    chain = (*reversed(path.parents), path)

    def stamp(item):
        value = item.lstat()
        if (not stat.S_ISDIR(value.st_mode)
                or getattr(value, "st_file_attributes", 0)
                   & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)):
            raise SerializationSafetyError(ReasonCode.PATH_UNSAFE, "unsafe report directory ancestry")
        return (value.st_dev, value.st_ino, value.st_mode, value.st_size,
                value.st_mtime_ns, value.st_ctime_ns)

    before = []
    for item in chain:
        try:
            value = stamp(item)
        except FileNotFoundError:
            if not allow_absent or item != path:
                raise
            # Absence is permitted only for the requested optional leaf.
            for parent, expected in before:
                if stamp(parent) != expected:
                    raise SerializationSafetyError(ReasonCode.PATH_UNSAFE, "report directory changed")
            try:
                path.lstat()
            except FileNotFoundError:
                return ()
            raise SerializationSafetyError(ReasonCode.PATH_UNSAFE, "report directory appeared")
        before.append((item, value))
    with os.scandir(path) as entries:
        names = tuple(sorted(entry.name for entry in entries))
    for item, expected in before:
        if stamp(item) != expected:
            raise SerializationSafetyError(ReasonCode.PATH_UNSAFE, "report directory changed")
    return tuple(directory / name for name in names)

def _report_rows_v1(payload: Any) -> list[dict[str, Any]]:
    """Require an explicit row array; preserve row objects and order."""
    if type(payload) is not dict:
        raise SerializationSafetyError(ReasonCode.SERIALIZATION_UNSAFE, "report payload must be an object")
    rows = payload.get("records")
    if type(rows) is not list or any(type(row) is not dict for row in rows):
        raise SerializationSafetyError(ReasonCode.SERIALIZATION_UNSAFE, "report records must be an explicit object array")
    return rows

def _report_shard_refs_v1(payload: Any) -> tuple[str, ...]:
    """Resolve legacy aliases once; never discard a conflicting declaration."""
    if type(payload) is not dict:
        raise SerializationSafetyError(ReasonCode.SERIALIZATION_UNSAFE, "report payload must be an object")
    if "sharded_flag" in payload and type(payload["sharded_flag"]) is not bool:
        raise SerializationSafetyError(ReasonCode.SERIALIZATION_UNSAFE, "report sharded_flag must be boolean")
    aliases = []
    for key in ("shard_files", "shard_paths"):
        refs = payload[key] if key in payload else []
        if type(refs) is not list or any(type(ref) is not str for ref in refs):
            raise SerializationSafetyError(ReasonCode.SERIALIZATION_UNSAFE, "report shard references must be text arrays")
        for ref in refs:
            if validate_relative_path(ref) != ref:
                raise SerializationSafetyError(ReasonCode.PATH_UNSAFE, "report shard reference must be canonical")
        aliases.append(refs)
    primary, secondary = aliases
    if primary and secondary and primary != secondary:
        raise SerializationSafetyError(ReasonCode.SERIALIZATION_UNSAFE, "conflicting report shard aliases")
    selected = primary or secondary
    if payload.get("sharded_flag") is False and selected:
        raise SerializationSafetyError(ReasonCode.SERIALIZATION_UNSAFE, "nonsharded report declares shards")
    if payload.get("sharded_flag") is True and not selected:
        raise SerializationSafetyError(ReasonCode.SERIALIZATION_UNSAFE, "sharded report has no declared shards")
    return tuple(selected)

def _report_shard_descriptors_v1(payload, refs, *, required):
    """Check declared descriptor occurrences without collapsing repeated paths."""
    if type(required) is not bool:
        raise SerializationSafetyError(ReasonCode.SERIALIZATION_UNSAFE, "invalid descriptor policy")
    if "shard_manifest_refs" not in payload:
        if required and refs:
            raise SerializationSafetyError(ReasonCode.SERIALIZATION_UNSAFE, "missing shard descriptors")
        return () if not refs else None
    declarations = payload["shard_manifest_refs"]
    if type(declarations) is not list or len(declarations) != len(refs):
        raise SerializationSafetyError(ReasonCode.SERIALIZATION_UNSAFE, "shard descriptor count mismatch")
    for ordinal, (ref, declaration) in enumerate(zip(refs, declarations), start=1):
        if (type(declaration) is not dict
                or declaration.get("shard_path") != ref
                or not is_nonnegative_json_integer_v1(declaration.get("shard_index"))
                or declaration["shard_index"] != ordinal
                or not is_nonnegative_json_integer_v1(declaration.get("row_count"))):
            raise SerializationSafetyError(ReasonCode.SERIALIZATION_UNSAFE, "invalid ordered shard descriptor")
    return tuple(declarations)

def _expand_report_records_v1(repo_root, payload, read_json):
    """Expand one layer, checking each present count against that actual read.

    This does not authenticate data, resolve physical custody, or grant resources.
    Repeated paths remain separate reads. Counts are never coerced or defaulted.
    """
    inline = _report_rows_v1(payload)
    refs = _report_shard_refs_v1(payload)
    declarations = _report_shard_descriptors_v1(payload, refs, required=False)
    if payload.get("sharded_flag") is True and inline:
        raise SerializationSafetyError(ReasonCode.SERIALIZATION_UNSAFE, "compact sharded root duplicates inline records")
    rows = list(inline)
    for ordinal, ref in enumerate(refs):
        shard = read_json(repo_root / ref)
        shard_rows = _report_rows_v1(shard)
        if _report_shard_refs_v1(shard):
            raise SerializationSafetyError(ReasonCode.SERIALIZATION_UNSAFE, "nested report shards are not supported")
        if "record_count" in shard:
            count = shard["record_count"]
            if not is_nonnegative_json_integer_v1(count) or count != len(shard_rows):
                raise SerializationSafetyError(ReasonCode.SERIALIZATION_UNSAFE, "shard observed count mismatch")
        if declarations is not None and declarations[ordinal]["row_count"] != len(shard_rows):
            raise SerializationSafetyError(ReasonCode.SERIALIZATION_UNSAFE, "shard descriptor differs from observed row count")
        rows.extend(shard_rows)
    return rows

def _report_manifest_consistency_v1(
    payloads, records, report_names, manifest_name, generated_dir, schema_dir,
    *, style, schema_refs=None,
):
    """Check decoded inventory declarations, not schema validity or input custody.

    All arguments come from the fixed validator owner. Repeated identical shard
    paths retain their ordinal occurrences. No filesystem, source, solver, mode,
    or order operation is performed by this function.
    """
    def require(condition, detail):
        if not condition:
            raise SerializationSafetyError(
                ReasonCode.SERIALIZATION_UNSAFE,
                f"report manifest {manifest_name}: {detail}",
            )

    def text(value):
        return type(value) is str and bool(value)

    def path(value):
        require(text(value), "path must be nonempty text")
        require(validate_relative_path(value) == value, "path is not canonical")
        return value

    require(style in ("Q_ROOT_AND_SHARD", "ROOT_REFERENCE", "D3_ROOT_REFERENCE"), "unknown layout")
    names = tuple(report_names)
    require(all(text(name) and "/" not in name and "\\" not in name for name in names), "invalid report roster")
    require(len(names) == len(set(names)) and manifest_name in names, "invalid report identity set")
    for name in names:
        path(name)
    require(type(payloads) is dict and set(payloads) == set(names), "payload inventory mismatch")
    require(type(records) is dict and set(records) == set(names), "expanded inventory mismatch")
    generated = path(str(generated_dir).replace("\\", "/"))
    schemas = path(str(schema_dir).replace("\\", "/"))
    if schema_refs is not None:
        require(type(schema_refs) is dict and set(schema_refs) == set(names), "schema binding inventory mismatch")

    roots = {}
    shard_owners = {}
    for name in names:
        payload = payloads[name]
        inline = _report_rows_v1(payload)
        expanded = records[name]
        require(type(expanded) is list and all(type(row) is dict for row in expanded), f"{name}: invalid expanded records")
        require(is_nonnegative_json_integer_v1(payload.get("record_count")), f"{name}: invalid root count")
        require(payload["record_count"] == len(expanded), f"{name}: root count mismatch")
        require(type(payload.get("sharded_flag")) is bool, f"{name}: invalid sharded flag")
        refs = _report_shard_refs_v1(payload)
        require(not refs or not inline, f"{name}: compact root has inline rows")
        schema = payload.get("schema_ref")
        path(schema)
        require("/" not in schema, f"{name}: schema reference is not a filename")
        if schema_refs is not None:
            require(schema == schema_refs[name], f"{name}: wrong schema binding")
        if style == "D3_ROOT_REFERENCE":
            require(payload.get("report_name") == name, f"{name}: root identity mismatch")
        else:
            require(payload.get("report_filename") == name, f"{name}: root identity mismatch")
        omitted = payload.get("records_omitted_for_sharding_flag", False)
        require(type(omitted) is bool, f"{name}: invalid omitted flag")
        require(omitted is bool(refs), f"{name}: omitted flag disagrees with shard declarations")
        if "shard_count" in payload or refs:
            require(is_nonnegative_json_integer_v1(payload.get("shard_count")), f"{name}: invalid shard count")
            require(payload["shard_count"] == len(refs), f"{name}: shard count mismatch")
        declarations = _report_shard_descriptors_v1(
            payload, refs, required=(style != "D3_ROOT_REFERENCE"),
        )
        if declarations is not None:
            total = sum(declaration["row_count"] for declaration in declarations)
            require(not refs or total == len(expanded), f"{name}: shard declared total mismatch")
        for ref in refs:
            require(ref not in shard_owners or shard_owners[ref] == name, "one shard path declares multiple root owners")
            shard_owners[ref] = name
        roots[name] = (payload, schema, refs, declarations, omitted)

    manifest = records[manifest_name]
    seen = set()
    actual_shards = {name: [] for name in names}
    for row in manifest:
        if style == "Q_ROOT_AND_SHARD":
            kind = row.get("manifest_entry_class")
            require(kind in ("ROOT_REPORT", "SHARD_REPORT"), "unknown manifest entry class")
            if kind == "SHARD_REPORT":
                parent = row.get("parent_report_filename")
                require(text(parent) and parent in roots, "unknown shard parent")
                actual_shards[parent].append(row)
                continue
            name = row.get("report_filename")
            count_key, schema_key, path_key = "row_count", "schema_path", "report_path"
        elif style == "ROOT_REFERENCE":
            name = row.get("report_ref")
            count_key, schema_key, path_key = "record_count", "schema_ref", "report_path"
        else:
            name = row.get("manifest_report_name")
            count_key, schema_key, path_key = "record_count", "referenced_schema_ref", "root_report_path"
        require(text(name) and name in roots and name not in seen, "unknown or duplicate root entry")
        seen.add(name)
        payload, schema, refs, declarations, omitted = roots[name]
        require(row.get(path_key) == f"{generated}/{name}", f"{name}: manifest root path mismatch")
        expected_schema = f"{schemas}/{schema}" if style == "Q_ROOT_AND_SHARD" else schema
        require(row.get(schema_key) == expected_schema, f"{name}: manifest schema mismatch")
        require(is_nonnegative_json_integer_v1(row.get(count_key)) and row[count_key] == len(records[name]),
                f"{name}: manifest root count mismatch")
        if style == "Q_ROOT_AND_SHARD":
            require(row.get("report_name") == name.removesuffix(".report.json"), f"{name}: manifest root name mismatch")
            expected_kind = "SHARDED_COMPACT_ROOT" if refs else "ROOT_WITH_RECORDS"
            require(row.get("compact_or_sharded_flag") == expected_kind, f"{name}: manifest root kind mismatch")
        else:
            require(type(row.get("sharded_flag")) is bool and row["sharded_flag"] is payload["sharded_flag"],
                    f"{name}: manifest sharded flag mismatch")
            require(type(row.get("shard_files")) is list and tuple(row["shard_files"]) == refs,
                    f"{name}: manifest shard path/order mismatch")
            if style == "D3_ROOT_REFERENCE":
                require(type(row.get("records_omitted_for_sharding_flag")) is bool and row["records_omitted_for_sharding_flag"] is omitted,
                        f"{name}: manifest omitted flag mismatch")
                require(is_nonnegative_json_integer_v1(row.get("shard_count")) and row["shard_count"] == len(refs),
                        f"{name}: manifest shard count mismatch")
    require(seen == set(names), "manifest root inventory incomplete")
    if style == "Q_ROOT_AND_SHARD":
        for name in names:
            _payload, schema, refs, declarations, _omitted = roots[name]
            rows = actual_shards[name]
            require(len(rows) == len(refs), f"{name}: manifest shard multiplicity mismatch")
            for row, ref, declaration in zip(rows, refs, declarations):
                filename = ref.rsplit("/", 1)[-1]
                require(row.get("report_path") == ref, f"{name}: manifest shard path/order mismatch")
                require(row.get("report_filename") == filename and row.get("report_name") == filename.removesuffix(".report.json"),
                        f"{name}: manifest shard identity mismatch")
                require(row.get("schema_path") == f"{schemas}/{schema}", f"{name}: manifest shard schema mismatch")
                require(is_nonnegative_json_integer_v1(row.get("row_count")) and row["row_count"] == declaration["row_count"],
                        f"{name}: manifest shard row count mismatch")
                require(row.get("compact_or_sharded_flag") == "SHARD_REPORT" and row.get("consumed_by_report") == name,
                        f"{name}: manifest shard parent declaration mismatch")

def _report_schema_templates_v1(constants, *, profile, schema_name=None):
    """Independent schema contract for the six selected generated-report owners.

    constants and schema_name are fixed source-owner bindings, never payload data.
    This is a schema oracle, not another report builder or an evidence authority.
    """
    if profile not in ("Q", "QB", "QC", "MAPPER", "SIM", "D3"):
        raise SerializationSafetyError(ReasonCode.SERIALIZATION_UNSAFE, "unknown schema profile")
    names = tuple(constants.REPORT_FILENAMES)
    if not names or len(names) != len(set(names)):
        raise SerializationSafetyError(ReasonCode.SERIALIZATION_UNSAFE, "invalid report roster")
    refs = (dict(constants.REPORT_SCHEMA_REFS) if profile in ("Q", "D3")
            else {name: schema_name(name) for name in names})
    if set(refs) != set(names) or len(set(refs.values())) != len(names):
        raise SerializationSafetyError(ReasonCode.SERIALIZATION_UNSAFE, "invalid schema map")
    for name in (*names, *refs.values()):
        if type(name) is not str or "/" in name or validate_relative_path(name) != name:
            raise SerializationSafetyError(ReasonCode.PATH_UNSAFE, "schema identity must be a canonical filename")
    dialect = "https://json-schema.org/draft/2020-12/schema"
    schemas = {}
    if profile == "Q":
        common = "pr166_q_common.schema.json"
        schemas[common] = {
            "$schema": dialect, "$id": common, "title": "PR166-Q common generated report row", "type": "object",
            "required": ["row_id", "created_by_pr", "source_pr", "qku_id", "formula_id", "algorithm_id", "computability_disposition",
                         "quantum_backend_execution_flag", "quantum_advantage_claim_flag", "live_order_authority_flag", "profit_evidence_flag",
                         "source_truth_acceptance_flag", "connector_semantic_binding_flag", "private_state_fetch_flag", "runtime_cash_receipt_flag"],
            "properties": {"row_id": {"type": "string"}, "created_by_pr": {"const": constants.PR_ID},
                           "computability_disposition": {"enum": list(constants.COMPUTABILITY_DISPOSITIONS)}},
        }
        for name in names:
            schemas[refs[name]] = {
                "$schema": dialect, "$id": refs[name], "title": name, "type": "object",
                "required": ["report_filename", "roadmap_pr_id", "created_by_pr", "authority_class", "authority_boundary_ref", "schema_ref", "record_count", "records"],
                "properties": {
                    "report_filename": {"const": name}, "roadmap_pr_id": {"const": constants.PR_ID}, "created_by_pr": {"const": constants.PR_ID},
                    "authority_class": {"const": constants.AUTHORITY_CLASS}, "authority_boundary_ref": {"const": constants.AUTHORITY_BOUNDARY_REF},
                    "schema_ref": {"const": refs[name]}, "record_count": {"type": "integer", "minimum": 0},
                    "records": {"type": "array", "items": {"$ref": common}},
                }, "additionalProperties": True,
            }
    elif profile == "D3":
        common = "pr165_d3_common.schema.json"
        schemas[common] = {
            "$schema": dialect, "$id": common, "title": "PR165-D3 common report schema", "type": "object",
            "required": ["roadmap_pr_id", "created_by_pr", "report_name", "record_count", "schema_ref", "validator_ref"],
            "properties": {
                "roadmap_pr_id": {"const": constants.PR_ID}, "created_by_pr": {"const": constants.PR_ID}, "report_name": {"type": "string"},
                "record_count": {"type": "integer", "minimum": 0}, "records": {"type": "array"},
                "shard_files": {"type": "array", "items": {"type": "string"}}, "forbidden_authority_counts": {"type": "object"},
            }, "additionalProperties": True,
        }
        for name in names:
            schemas[refs[name]] = {
                "$schema": dialect, "$id": refs[name], "title": name.removesuffix(".report.json"),
                "allOf": [{"$ref": common}], "type": "object",
                "properties": {"report_name": {"const": name}, "schema_ref": {"const": refs[name]},
                               "roadmap_pr_id": {"const": constants.PR_ID}, "created_by_pr": {"const": constants.PR_ID}},
                "additionalProperties": True,
            }
    else:
        for name in names:
            schemas[refs[name]] = {
                "$schema": dialect, "$id": refs[name], "type": "object",
                "required": ["report_name", "roadmap_pr_id", "created_by_pr", "schema_ref", "record_count", "records"],
                "properties": {
                    "report_name": {"type": "string"}, "roadmap_pr_id": {"const": constants.PR_ID}, "created_by_pr": {"const": constants.PR_ID},
                    "schema_ref": {"const": refs[name]}, "record_count": {"type": "integer", "minimum": 0}, "records": {"type": "array"},
                    "sharded_flag": {"type": "boolean"}, "shard_files": {"type": "array", "items": {"type": "string"}},
                }, "additionalProperties": True,
            }
    return refs, schemas

def _report_schema_session_v1(repo_root, constants, read_json, *, profile, schema_name=None):
    """Load the exact selected schemas once per invocation; never fetch references.

    Physical file custody and the declared environment remain existing-owner duties.
    JSON Schema handles vocabulary semantics; stronger QTT count/row laws remain.
    """
    from jsonschema import Draft202012Validator
    from jsonschema.exceptions import ValidationError
    from referencing import Registry, Resource
    from referencing.exceptions import NoSuchResource

    refs, expected = _report_schema_templates_v1(constants, profile=profile, schema_name=schema_name)
    loaded = {}
    for filename, template in expected.items():
        observed = read_json(repo_root / constants.SCHEMA_DIR / filename)
        # Preserve type and ordered arrays, ignore only JSON object order/formatting.
        if json.dumps(observed, sort_keys=True, allow_nan=False) != json.dumps(template, sort_keys=True, allow_nan=False):
            raise SerializationSafetyError(ReasonCode.SERIALIZATION_UNSAFE, "schema differs from source-defined contract: " + filename)
        Draft202012Validator.check_schema(observed)
        loaded[filename] = observed

    def no_retrieval(uri):
        raise NoSuchResource(ref=uri)

    base = "https://qtt.invalid/selected-report-schemas/"
    registry = Registry(retrieve=no_retrieval).with_resources(
        (base + filename, Resource.from_contents(schema)) for filename, schema in loaded.items()
    )
    root_validators = {name: Draft202012Validator({"$ref": base + filename}, registry=registry) for name, filename in refs.items()}
    shard_validators = {}
    for name, filename in refs.items():
        if profile == "D3":
            # D3's writer does not put report_name/validator_ref in shard envelopes.
            schema = {
                "$schema": "https://json-schema.org/draft/2020-12/schema", "type": "object",
                "required": ["roadmap_pr_id", "created_by_pr", "parent_report", "schema_ref", "shard_index", "record_count", "records", "forbidden_authority_counts"],
                "properties": {
                    "roadmap_pr_id": {"const": constants.PR_ID}, "created_by_pr": {"const": constants.PR_ID}, "parent_report": {"const": name},
                    "schema_ref": {"const": filename}, "shard_index": {"type": "integer", "minimum": 1},
                    "record_count": {"type": "integer", "minimum": 0}, "records": {"type": "array", "items": {"type": "object"}},
                    "forbidden_authority_counts": {"type": "object"},
                }, "additionalProperties": True,
            }
        else:
            schema = json.loads(json.dumps(loaded[filename]))
            schema["$id"] = base + "shard-" + filename
            if profile == "Q":
                # Shard identity is its own filename, not the root-schema const.
                schema["properties"]["report_filename"] = {"type": "string"}
        Draft202012Validator.check_schema(schema)
        shard_validators[name] = Draft202012Validator(schema, registry=registry)

    def check(name, payload, *, shard_ref=None, ordinal=None, shard_count=None):
        if name not in root_validators:
            raise SerializationSafetyError(ReasonCode.SERIALIZATION_UNSAFE, "unselected schema report")
        _report_rows_v1(payload)
        count = payload.get("record_count")
        if not is_nonnegative_json_integer_v1(count):
            raise SerializationSafetyError(ReasonCode.SERIALIZATION_UNSAFE, "schema report count must be an observed integer")
        validator = root_validators[name] if shard_ref is None else shard_validators[name]
        try:
            validator.validate(payload)
        except ValidationError:
            raise SerializationSafetyError(ReasonCode.SERIALIZATION_UNSAFE, "report violates source-defined schema: " + name) from None
        if shard_ref is None:
            if payload.get("report_name") != name or (profile != "D3" and payload.get("report_filename") != name):
                raise SerializationSafetyError(ReasonCode.SERIALIZATION_UNSAFE, "root report identity mismatch")
            return
        if (type(ordinal) is not int or ordinal < 1 or type(shard_count) is not int or shard_count < ordinal
                or not is_nonnegative_json_integer_v1(payload.get("shard_index")) or payload["shard_index"] != ordinal):
            raise SerializationSafetyError(ReasonCode.SERIALIZATION_UNSAFE, "shard ordinal mismatch")
        if payload["record_count"] != len(payload["records"]):
            raise SerializationSafetyError(ReasonCode.SERIALIZATION_UNSAFE, "shard schema count mismatch")
        if profile == "Q":
            leaf = shard_ref.rsplit("/", 1)[-1]
            valid_parent = (payload.get("parent_report_filename") == name and payload.get("report_filename") == leaf and payload.get("report_name") == leaf)
        elif profile == "D3":
            valid_parent = payload.get("parent_report") == name
        else:
            valid_parent = (payload.get("root_report_ref") == (constants.GENERATED_DIR / name).as_posix()
                            and payload.get("report_name") == name and payload.get("report_filename") == name
                            and is_nonnegative_json_integer_v1(payload.get("shard_count")) and payload["shard_count"] == shard_count)
        if not valid_parent:
            raise SerializationSafetyError(ReasonCode.SERIALIZATION_UNSAFE, "shard parent identity mismatch")
    return check

def _report_schema_records_v1(repo_root, payload, read_json, check, report_name):
    """Validate the actual root and each actual child without extra report reads."""
    check(report_name, payload)
    refs = _report_shard_refs_v1(payload)
    read_ordinal = 0

    def checked_reader(path):
        nonlocal read_ordinal
        child = read_json(path)
        read_ordinal += 1
        check(report_name, child, shard_ref=refs[read_ordinal - 1], ordinal=read_ordinal, shard_count=len(refs))
        return child

    return _expand_report_records_v1(repo_root, payload, checked_reader)

def _report_companion_alignment_v1(primary, companions):
    """Match existing packet lineage and verify context without issuing identity.

    Packet identifiers must already be carried from admitted producer inputs.
    This local relation check does not accept source generations or runtime use.
    Preserve primary order and original row objects; no sorting, I/O or cache.
    """
    fields = (
        "qku_id", "formula_id", "algorithm_id", "parameter_stack_id",
        "execution_route_id", "market_scope",
    )

    def indexed(rows, label):
        if type(rows) is not list:
            raise SerializationSafetyError(ReasonCode.SERIALIZATION_UNSAFE,
                                           "companion rows must be an exact list: " + label)
        by_packet = {}
        row_ids = set()
        for row in rows:
            if type(row) is not dict:
                raise SerializationSafetyError(ReasonCode.SERIALIZATION_UNSAFE,
                                               "companion row must be an object: " + label)
            row_id = row.get("row_id")
            if type(row_id) is not str or not row_id.strip() or row_id in row_ids:
                raise SerializationSafetyError(ReasonCode.SERIALIZATION_UNSAFE,
                                               "missing or duplicate companion row identity: " + label)
            row_ids.add(row_id)
            packet = row.get("candidate_packet_id")
            if type(packet) is not str or not packet.strip():
                raise SerializationSafetyError(ReasonCode.SERIALIZATION_UNSAFE,
                                               "missing or malformed candidate packet identity: " + label)
            if packet in by_packet:
                raise SerializationSafetyError(ReasonCode.SERIALIZATION_UNSAFE,
                                               "ambiguous candidate packet identity: " + label)
            key = tuple(row.get(field) for field in fields)
            if any(type(value) is not str or not value.strip() for value in key):
                raise SerializationSafetyError(ReasonCode.SERIALIZATION_UNSAFE,
                                               "missing or malformed companion key: " + label)
            by_packet[packet] = row
        return by_packet

    if type(companions) is not dict or any(type(name) is not str or not name for name in companions):
        raise SerializationSafetyError(ReasonCode.SERIALIZATION_UNSAFE,
                                       "companion roster must be a named mapping")
    primary_index = indexed(primary, "primary")
    aligned = {}
    for name, rows in companions.items():
        index = indexed(rows, name)
        if index.keys() != primary_index.keys():
            raise SerializationSafetyError(ReasonCode.SERIALIZATION_UNSAFE,
                                           "candidate packet coverage mismatch: " + name)
        selected = []
        for packet, source in primary_index.items():
            companion = index[packet]
            if any(source[field] != companion[field] for field in fields):
                raise SerializationSafetyError(ReasonCode.SERIALIZATION_UNSAFE,
                                               "candidate packet context mismatch: " + name)
            selected.append(companion)
        aligned[name] = selected
        del index
    return aligned

def _report_carry_candidate_lineage_v1(source_row, produced_row):
    """Carry a supplied packet identifier into a new report row, never invent it.

    The producer retains its own row_id and every economic field. A conflicting
    explicit lineage value is a failure, not an invitation to overwrite it.
    """
    if type(source_row) is not dict or type(produced_row) is not dict:
        raise SerializationSafetyError(ReasonCode.SERIALIZATION_UNSAFE,
                                       "candidate lineage requires source and output objects")
    packet = source_row.get("candidate_packet_id")
    if type(packet) is not str or not packet.strip():
        raise SerializationSafetyError(ReasonCode.SERIALIZATION_UNSAFE,
                                       "candidate lineage must be present in the producer input")
    if "candidate_packet_id" in produced_row:
        present = produced_row["candidate_packet_id"]
        if type(present) is not str or present != packet:
            raise SerializationSafetyError(ReasonCode.SERIALIZATION_UNSAFE,
                                           "producer output contradicts its candidate lineage")
    result = dict(produced_row)
    result["candidate_packet_id"] = packet
    return result
