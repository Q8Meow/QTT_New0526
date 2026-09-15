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
