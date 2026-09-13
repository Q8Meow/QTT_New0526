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
