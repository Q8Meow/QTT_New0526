"""Bounded local source-use protocol and controller; import performs no native I/O.

The fixed verifier attributes a frozen action to the protected public enrollment.
It does not establish source truth, account eligibility, or a protected installation.
Native qualification is a separate, explicitly launched Windows operation.
"""

from __future__ import annotations

import base64
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import json
import logging
import re
from types import MappingProxyType

from ..stage1_prediction_markets.qku_computation_control_plane.receipts import (
    SourceUseProofV1, _source_use_b64_v1, _source_use_fields_v1,
    _source_use_mapping_v1, _source_use_require_v1, _source_use_stored_utc_v1,
    _source_use_text_v1, _source_use_utc_v1,
    SourceUseScopeV1, SourceUseOriginalContentV1, SourceUseReviewFactsV1,
    SourceUseObservationRequestV1, _source_use_record_ref_v1,
)
from ..stage1_prediction_markets.qku_computation_control_plane.economic_math import KalshiQuadraticTakerBuyYesFillV1
from ..stage1_prediction_markets.qku_computation_control_plane.context import _native_ident
from ..stage1_prediction_markets.qku_computation_control_plane.stage1_launch_graph import Stage1VenueProfileIdV1


def _b64_v1(raw: bytes) -> str:
    _source_use_require_v1(type(raw) is bytes)
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _closed_json_v1(raw: bytes, maximum: int) -> dict:
    _source_use_require_v1(type(raw) is bytes and 0 < len(raw) <= maximum)

    def pairs(items):
        result = {}
        for key, value in items:
            _source_use_require_v1(type(key) is str and key not in result)
            result[key] = value
        return result

    def bad_constant(_):
        _source_use_require_v1(False)

    value = json.loads(raw.decode("utf-8", errors="strict"), object_pairs_hook=pairs,
                       parse_constant=bad_constant)
    _source_use_require_v1(type(value) is dict)
    return value


def _validate_public_key_v1(raw: bytes):
    from cryptography.hazmat.primitives.asymmetric import ec
    from fido2 import cbor
    from fido2.cose import ES256
    from fido2.webauthn import AttestedCredentialData

    _source_use_require_v1(type(raw) is bytes and 18 <= len(raw) <= 4096)
    parsed = AttestedCredentialData(raw)
    key = parsed.public_key
    _source_use_require_v1(type(key) is ES256 and set(key) == {1, 3, -1, -2, -3}
                           and all(type(key[n]) is int for n in (1, 3, -1))
                           and (key[1], key[3], key[-1]) == (2, -7, 1)
                           and all(type(key[n]) is bytes and len(key[n]) == 32 for n in (-2, -3))
                           and 1 <= len(parsed.credential_id) <= 1024)
    native_key = ec.EllipticCurvePublicNumbers(int.from_bytes(key[-2], "big"),
                                             int.from_bytes(key[-3], "big"), ec.SECP256R1()).public_key()
    _source_use_require_v1(ES256.from_cryptography_key(native_key) == key
                           and raw[18 + len(parsed.credential_id):] == cbor.encode(dict(key)))
    return parsed


@dataclass(frozen=True, slots=True)
class PublicSourceUseEnrollmentV1:
    schema_version: str
    root_state: str
    enrollment_ref: str
    approval_sid: str
    owner_ref: str
    rp_id: str
    origin: str
    user_handle_b64: str
    key_id_b64: str | None
    key_data_b64: str | None
    initial_counter: int | None
    key_backup_eligible: bool | None
    registered_at_utc: datetime | None
    roles: tuple[str, ...]

    def __post_init__(self) -> None:
        for name in ("schema_version", "root_state", "enrollment_ref", "approval_sid", "owner_ref", "rp_id", "origin"):
            _source_use_text_v1(getattr(self, name))
        for name in ("enrollment_ref", "owner_ref"):
            _native_ident(getattr(self, name))
        _source_use_require_v1(self.schema_version == "QTT_OWNER_SOURCE_USE_ROOT_V1"
                               and self.root_state in {"ENROLLMENT_ONLY", "ACTIVE", "DISABLED"}
                               and self.rp_id == "localhost" and self.origin == "https://localhost"
                               and re.fullmatch(r"S-1-(?:0|[1-9][0-9]*)(?:-(?:0|[1-9][0-9]*)){1,15}", self.approval_sid) is not None)
        sid_parts = self.approval_sid.split("-")
        _source_use_require_v1(int(sid_parts[2]) < 2**48 and all(int(value) < 2**32 for value in sid_parts[3:]))
        _source_use_b64_v1(self.user_handle_b64, minimum=32, maximum=32)
        _source_use_require_v1(type(self.roles) is tuple and all(type(role) is str for role in self.roles)
                               and self.roles == ("REVIEW_ACCEPT", "USE_ADMIT", "OBSERVE_ONCE"))
        key_values = (self.key_id_b64, self.key_data_b64, self.initial_counter,
                      self.key_backup_eligible, self.registered_at_utc)
        if self.root_state == "ENROLLMENT_ONLY":
            _source_use_require_v1(all(value is None for value in key_values))
        else:
            _source_use_require_v1(all(value is not None for value in key_values))
            key_id = _source_use_b64_v1(self.key_id_b64, maximum=1024)
            parsed = _validate_public_key_v1(_source_use_b64_v1(self.key_data_b64, maximum=4096))
            _source_use_require_v1(parsed.credential_id == key_id
                                   and type(self.initial_counter) is int and 0 <= self.initial_counter <= 2**32 - 1
                                   and type(self.key_backup_eligible) is bool)
            object.__setattr__(self, "registered_at_utc", _source_use_utc_v1(self.registered_at_utc))


def _read_public_enrollment_v1(raw: bytes) -> PublicSourceUseEnrollmentV1:
    row = _source_use_mapping_v1(_closed_json_v1(raw, 65536), PublicSourceUseEnrollmentV1)
    _source_use_require_v1(type(row["roles"]) is list)
    row["roles"] = tuple(row["roles"])
    if row["registered_at_utc"] is not None:
        row["registered_at_utc"] = _source_use_stored_utc_v1(row["registered_at_utc"])
    return PublicSourceUseEnrollmentV1(**row)


def _source_use_proposal_v1(raw: bytes):
    from ..stage1_prediction_markets.qku_computation_control_plane.serialization import safe_json_loads, _native_strict_json
    from ..stage1_prediction_markets.qku_computation_control_plane.errors import SerializationSafetyError

    _source_use_require_v1(type(raw) is bytes and 0 < len(raw) <= 262144)
    try:
        row = safe_json_loads(raw.decode("utf-8", errors="strict"))
    except SerializationSafetyError:
        candidate = _native_strict_json(raw, max_bytes=262144)
        if type(candidate) is not dict or candidate.get("schema_version") != "PUBLIC_SOURCE_USE_ACTION_V1":
            raise
        return _public_source_use_proposal_v1(candidate)
    if type(row) is dict and row.get("schema_version") == "PUBLIC_SOURCE_USE_ACTION_V1":
        return _public_source_use_proposal_v1(_native_strict_json(raw, max_bytes=262144))
    _source_use_require_v1(type(row) is dict and type(row.get("action")) is str)
    action = row["action"]
    keys = {
        "REVIEW_ACCEPT": {"action", "scope", "original", "review_facts", "requested_expires_at_utc"},
        "USE_ADMIT": {"action", "scope", "original", "expected_review_ref", "requested_expires_at_utc"},
        "OBSERVE_ONCE": {"action", "scope", "expected_declaration_ref", "expected_review_ref", "observation"},
        "WITHDRAW_USE": {"action", "scope", "expected_declaration_ref", "expected_review_ref", "reason"},
        "INVALIDATE_REVIEW": {"action", "scope", "expected_declaration_ref", "expected_review_ref", "reason"},
    }
    _source_use_require_v1(action in keys and set(row) == keys[action])
    scope = _source_use_mapping_v1(row["scope"], SourceUseScopeV1)
    _source_use_require_v1(type(scope["profile_id"]) is str and scope["profile_id"] == "KALSHI_US_DCM_DIRECT")
    scope["profile_id"] = Stage1VenueProfileIdV1.KALSHI_US_DCM_DIRECT
    row["scope"] = SourceUseScopeV1(**scope)
    _source_use_require_v1(row["scope"].account_scope_ref is not None)
    for name in ("expected_declaration_ref", "expected_review_ref"):
        if name in row and row[name] is not None:
            _source_use_record_ref_v1(row[name])
    if "original" in row:
        original = _source_use_mapping_v1(row["original"], SourceUseOriginalContentV1)
        for name in ("claimed_effective_at_utc", "claimed_expires_at_utc"):
            if original[name] is not None:
                original[name] = _source_use_stored_utc_v1(original[name])
        row["original"] = SourceUseOriginalContentV1(**original)
    if "review_facts" in row:
        facts = _source_use_mapping_v1(row["review_facts"], SourceUseReviewFactsV1)
        for name in ("factual_checked_at_utc", "available_at_utc", "source_effective_at_utc", "source_expires_at_utc"):
            facts[name] = _source_use_stored_utc_v1(facts[name])
        for name in ("recheck_triggers", "reviewed_claims", "limitations"):
            _source_use_require_v1(type(facts[name]) is list)
            facts[name] = tuple(facts[name])
        row["review_facts"] = SourceUseReviewFactsV1(**facts)
    if "requested_expires_at_utc" in row:
        row["requested_expires_at_utc"] = _source_use_stored_utc_v1(row["requested_expires_at_utc"])
    if "observation" in row:
        request = _source_use_mapping_v1(row["observation"], SourceUseObservationRequestV1)
        request["expires_at_utc"] = _source_use_stored_utc_v1(request["expires_at_utc"])
        _source_use_require_v1(type(request["fills"]) is list and 1 <= len(request["fills"]) <= 4096)
        fills = []
        for value in request["fills"]:
            fill = _source_use_mapping_v1(value, KalshiQuadraticTakerBuyYesFillV1)
            for name in ("contracts", "yes_price"):
                _source_use_require_v1(type(fill[name]) is str and len(fill[name]) <= 256)
                fill[name] = Decimal(fill[name])
            fills.append(KalshiQuadraticTakerBuyYesFillV1(**fill))
        request["fills"] = tuple(fills)
        for name in ("balance_increment", "prior_rounding_overpayment"):
            _source_use_require_v1(type(request[name]) is str and len(request[name]) <= 256)
            request[name] = Decimal(request[name])
        row["observation"] = SourceUseObservationRequestV1(**request)
    if "reason" in row:
        _source_use_text_v1(row["reason"])
    return MappingProxyType(row)


def _public_source_use_proposal_v1(row):
    from ..stage1_prediction_markets.qku_computation_control_plane.receipts import (
        PublicDataSourceUseScopeV1, PublicCaptureBudgetV1, PublicCaptureRequestV1, _public_control_ref_v1,
    )

    _source_use_require_v1(type(row) is dict and type(row.get("action")) is str)
    row = dict(row)
    keys = {
        "REVIEW_ACCEPT": {"schema_version", "action", "scope", "original", "review_facts", "requested_expires_at_utc"},
        "USE_ADMIT": {"schema_version", "action", "scope", "original", "expected_review_ref", "requested_expires_at_utc"},
        "OBSERVE_ONCE": {"schema_version", "action", "scope", "expected_declaration_ref", "expected_review_ref", "capture"},
        "WITHDRAW_USE": {"schema_version", "action", "scope", "expected_declaration_ref", "expected_review_ref", "reason"},
        "INVALIDATE_REVIEW": {"schema_version", "action", "scope", "expected_declaration_ref", "expected_review_ref", "reason"},
    }
    _source_use_require_v1(row["schema_version"] == "PUBLIC_SOURCE_USE_ACTION_V1"
                           and row["action"] in keys and set(row) == keys[row["action"]])

    def make_scope(value):
        scope = _source_use_mapping_v1(value, PublicDataSourceUseScopeV1)
        _source_use_require_v1(type(scope["profile_id"]) is str)
        scope["profile_id"] = Stage1VenueProfileIdV1(scope["profile_id"])
        scope["budget"] = PublicCaptureBudgetV1(**_source_use_mapping_v1(scope["budget"], PublicCaptureBudgetV1))
        for key in ("source_ids", "native_operation_ids", "instrument_ids", "permitted_consumer_ids", "receive_scope_classes"):
            _source_use_require_v1(type(scope[key]) is list)
            scope[key] = tuple(scope[key])
        return PublicDataSourceUseScopeV1(**scope)

    row["scope"] = make_scope(row["scope"])
    for name in ("expected_declaration_ref", "expected_review_ref"):
        if name in row and row[name] is not None:
            _public_control_ref_v1(row[name], kind="PUBLIC_SOURCE_ORIGINAL_V1")
    if "original" in row:
        original = _source_use_mapping_v1(row["original"], SourceUseOriginalContentV1)
        for key in ("claimed_effective_at_utc", "claimed_expires_at_utc"):
            if original[key] is not None:
                original[key] = _source_use_stored_utc_v1(original[key])
        row["original"] = SourceUseOriginalContentV1(**original)
    if "review_facts" in row:
        facts = _source_use_mapping_v1(row["review_facts"], SourceUseReviewFactsV1)
        for key in ("factual_checked_at_utc", "available_at_utc", "source_effective_at_utc", "source_expires_at_utc"):
            facts[key] = _source_use_stored_utc_v1(facts[key])
        for key in ("recheck_triggers", "reviewed_claims", "limitations"):
            _source_use_require_v1(type(facts[key]) is list)
            facts[key] = tuple(facts[key])
        row["review_facts"] = SourceUseReviewFactsV1(**facts)
    if "requested_expires_at_utc" in row:
        row["requested_expires_at_utc"] = _source_use_stored_utc_v1(row["requested_expires_at_utc"])
    if "capture" in row:
        capture = _source_use_mapping_v1(row["capture"], PublicCaptureRequestV1)
        capture["scope"] = make_scope(capture["scope"])
        for key in ("source_binding_refs", "requested_operation_ids", "requested_instrument_ids"):
            _source_use_require_v1(type(capture[key]) is list)
            capture[key] = tuple(capture[key])
        row["capture"] = PublicCaptureRequestV1(**capture)
        _source_use_require_v1(row["capture"].scope == row["scope"])
    if "reason" in row:
        _source_use_text_v1(row["reason"])
    return MappingProxyType(row)


@dataclass(frozen=True, slots=True)
class _RawSourceUseResponseV1:
    operation: str
    key_id: bytes
    client_data: bytes
    authenticator_data: bytes
    signature: bytes | None
    user_handle: bytes | None
    attestation_object: bytes | None

    def __post_init__(self) -> None:
        _source_use_require_v1(type(self.operation) is str and self.operation in {"CREATE", "GET"})
        size = 0
        for value in (self.key_id, self.client_data, self.authenticator_data, self.signature,
                      self.user_handle, self.attestation_object):
            if value is not None:
                _source_use_require_v1(type(value) is bytes)
                size += len(value)
        _source_use_require_v1(size <= 65536 and type(self.key_id) is bytes and 1 <= len(self.key_id) <= 1024
                               and type(self.client_data) is bytes and self.client_data
                               and type(self.authenticator_data) is bytes and len(self.authenticator_data) >= 37)
        if self.operation == "GET":
            _source_use_require_v1(type(self.signature) is bytes and 0 < len(self.signature) <= 1024
                                   and self.attestation_object is None and len(self.authenticator_data) == 37)
        else:
            _source_use_require_v1(type(self.attestation_object) is bytes and self.attestation_object
                                   and self.signature is self.user_handle is None)
        if self.user_handle is not None:
            _source_use_require_v1(len(self.user_handle) == 32)


@dataclass(frozen=True, slots=True)
class _SourceUseAuthenticationV1:
    server: object
    state: object
    options: object
    client_data: bytes
    operation: str
    enrollment: PublicSourceUseEnrollmentV1


def _exact_source_use_origin_v1(origin):
    return type(origin) is str and origin == "https://localhost"


def _new_fido_server_v1():
    # Fixed logger only: keys, challenges and responses must never reach logs.
    logging.getLogger("fido2.server").disabled = True
    from fido2.server import Fido2Server
    from fido2.webauthn import (AttestationConveyancePreference, PublicKeyCredentialParameters,
                               PublicKeyCredentialRpEntity, PublicKeyCredentialType)

    server = Fido2Server(PublicKeyCredentialRpEntity(id="localhost", name="QTT Owner Source Use"),
                        attestation=AttestationConveyancePreference.NONE,
                        verify_origin=_exact_source_use_origin_v1)
    server.allowed_algorithms = [PublicKeyCredentialParameters(type=PublicKeyCredentialType.PUBLIC_KEY, alg=-7)]
    return server


def _begin_source_use_authentication_v1(enrollment: PublicSourceUseEnrollmentV1, *, operation: str):
    from fido2.webauthn import (AuthenticatorAttachment, PublicKeyCredentialUserEntity,
                               ResidentKeyRequirement, UserVerificationRequirement)

    enrollment = PublicSourceUseEnrollmentV1(**_source_use_fields_v1(enrollment, PublicSourceUseEnrollmentV1))
    _source_use_require_v1(type(operation) is str and operation in {"CREATE", "GET"}
                           and enrollment.root_state != "DISABLED")
    server = _new_fido_server_v1()
    if operation == "GET":
        _source_use_require_v1(enrollment.root_state == "ACTIVE")
        key = _validate_public_key_v1(_source_use_b64_v1(enrollment.key_data_b64, maximum=4096))
        options, state = server.authenticate_begin([key], user_verification=UserVerificationRequirement.REQUIRED)
    else:
        _source_use_require_v1(enrollment.root_state == "ENROLLMENT_ONLY")
        options, state = server.register_begin(
            PublicKeyCredentialUserEntity(id=_source_use_b64_v1(enrollment.user_handle_b64, minimum=32, maximum=32),
                                          name=enrollment.owner_ref, display_name=enrollment.owner_ref),
            user_verification=UserVerificationRequirement.REQUIRED,
            authenticator_attachment=AuthenticatorAttachment.PLATFORM,
            resident_key_requirement=ResidentKeyRequirement.DISCOURAGED)
    _source_use_require_v1(type(state) is dict and set(state) == {"challenge", "user_verification"})
    _source_use_b64_v1(state["challenge"], minimum=32, maximum=32)
    client = json.dumps({"type": "webauthn.get" if operation == "GET" else "webauthn.create",
                         "challenge": state["challenge"], "origin": "https://localhost", "crossOrigin": False},
                        separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return _SourceUseAuthenticationV1(server, MappingProxyType(dict(state)), options, client, operation, enrollment)


def _verify_source_use_response_v1(pending: _SourceUseAuthenticationV1, raw: _RawSourceUseResponseV1,
                                  *, verified_at_utc: datetime):
    """Actual Fido2Server verification, with policy checks before FIDO parsing.

    Pending identity/consumption and counter publication belong to the authority.
    This pure function cannot issue a binding, permission or operational process.
    """
    from fido2 import cbor
    from fido2.server import Fido2Server
    from fido2.webauthn import (AttestationObject, AuthenticationResponse, AuthenticatorAssertionResponse,
                               AuthenticatorAttestationResponse, AuthenticatorData, CollectedClientData,
                               PublicKeyCredentialType, RegistrationResponse)

    _source_use_require_v1(type(pending) is _SourceUseAuthenticationV1 and type(pending.server) is Fido2Server
                           and pending.server._verify is _exact_source_use_origin_v1)
    raw = _RawSourceUseResponseV1(**_source_use_fields_v1(raw, _RawSourceUseResponseV1))
    _source_use_utc_v1(verified_at_utc)
    _source_use_require_v1(raw.operation == pending.operation and raw.client_data == pending.client_data)
    client = _closed_json_v1(raw.client_data, 65536)
    _source_use_require_v1(set(client) in ({"type", "challenge", "origin"}, {"type", "challenge", "origin", "crossOrigin"})
                           and type(client["type"]) is str and client["type"] == ("webauthn.get" if raw.operation == "GET" else "webauthn.create")
                           and type(client["origin"]) is str and client["origin"] == "https://localhost"
                           and type(client["challenge"]) is str and client["challenge"] == pending.state["challenge"]
                           and client.get("crossOrigin", False) is False)
    _source_use_b64_v1(client["challenge"], minimum=32, maximum=32)
    flags = raw.authenticator_data[32]
    _source_use_require_v1(flags & 0x05 == 0x05 and flags & 0x22 == 0
                           and not flags & 0x80 and (not flags & 0x10 or bool(flags & 0x08))
                           and bool(flags & 0x40) == (raw.operation == "CREATE"))
    enrollment = pending.enrollment
    logging.getLogger("fido2.server").disabled = True
    if raw.operation == "GET":
        _source_use_require_v1(raw.key_id == _source_use_b64_v1(enrollment.key_id_b64, maximum=1024)
                               and bool(flags & 0x08) is enrollment.key_backup_eligible
                               and (raw.user_handle is None or raw.user_handle == _source_use_b64_v1(
                                   enrollment.user_handle_b64, minimum=32, maximum=32)))
        key = _validate_public_key_v1(_source_use_b64_v1(enrollment.key_data_b64, maximum=4096))
        response = AuthenticationResponse(raw_id=raw.key_id, type=PublicKeyCredentialType.PUBLIC_KEY,
            response=AuthenticatorAssertionResponse(client_data=CollectedClientData(raw.client_data),
                authenticator_data=AuthenticatorData(raw.authenticator_data), signature=raw.signature,
                user_handle=raw.user_handle), client_extension_results={})
        actual_key = Fido2Server.authenticate_complete(pending.server, pending.state, [key], response)
        _source_use_require_v1(actual_key is key)
        return SourceUseProofV1(enrollment.enrollment_ref, _b64_v1(raw.client_data),
            _b64_v1(raw.authenticator_data), _b64_v1(raw.signature),
            None if raw.user_handle is None else _b64_v1(raw.user_handle),
            int.from_bytes(raw.authenticator_data[33:37], "big"), verified_at_utc)
    attestation = cbor.decode(raw.attestation_object)
    _source_use_require_v1(type(attestation) is dict and set(attestation) == {"fmt", "authData", "attStmt"}
                           and type(attestation["fmt"]) is str and attestation["fmt"] == "none"
                           and type(attestation["attStmt"]) is dict and not attestation["attStmt"]
                           and type(attestation["authData"]) is bytes and attestation["authData"] == raw.authenticator_data
                           and cbor.encode(attestation) == raw.attestation_object)
    key = _validate_public_key_v1(raw.authenticator_data[37:])
    _source_use_require_v1(key.credential_id == raw.key_id)
    response = RegistrationResponse(raw_id=raw.key_id, type=PublicKeyCredentialType.PUBLIC_KEY,
        response=AuthenticatorAttestationResponse(client_data=CollectedClientData(raw.client_data),
                                                   attestation_object=AttestationObject(raw.attestation_object)),
        client_extension_results={})
    verified = Fido2Server.register_complete(pending.server, pending.state, response)
    _source_use_require_v1(bytes(verified) == raw.authenticator_data)
    # Registration alone does not activate a root. The native enrollment ceremony
    # still requires a new assertion and returns only a public candidate for review.
    return bytes(key), bool(flags & 0x08)


def _create_owner_source_use_controller_v1(root):
    from .owner_source_use_windows import _require_native_root_v1
    from ..stage1_prediction_markets.qku_computation_control_plane.source_policy import _create_source_use_authority_v1

    _require_native_root_v1(root)
    controller = object.__new__(OwnerSourceUseControllerV1)
    controller._root = root
    controller._authority = _create_source_use_authority_v1(root) if root.enrollment.root_state == "ACTIVE" else None
    controller._pending_ref = controller._preview = controller._result = None
    controller._display_model = None
    controller._enrollment_pending = controller._enrollment_candidate = None
    controller._enrollment_stage = None
    controller._closed = False
    controller._enrollment_last_clock = None
    controller._enrollment_pending_deadline = None
    now, mono = controller._enrollment_clock_v1()
    controller._deadline = mono + 900_000_000_000
    controller._enrollment_expires = now + timedelta(seconds=900)
    return controller


class OwnerSourceUseControllerV1:
    """Closed local coordinator; only source policy may mint operational bindings."""

    def __init__(self):
        raise TypeError("local controller requires the original installed root")

    def _enrollment_clock_v1(self):
        import time

        before, wall, after = time.monotonic_ns(), time.time_ns(), time.monotonic_ns()
        valid = all(type(value) is int and 0 <= value <= 2**63 - 1 for value in (before, wall, after)) and before <= after
        if self._enrollment_last_clock is not None:
            valid = valid and wall >= self._enrollment_last_clock[0] and before >= self._enrollment_last_clock[1]
        if not valid:
            self._closed = True
            self._enrollment_pending = self._enrollment_pending_deadline = None
            _source_use_require_v1(False)
        self._enrollment_last_clock = (wall, after)
        seconds, nanos = divmod(wall, 1_000_000_000)
        return datetime(1970, 1, 1, tzinfo=UTC) + timedelta(seconds=seconds, microseconds=nanos // 1000), after

    def _enrollment_time_v1(self, stage_deadline=None):
        now, mono = self._enrollment_clock_v1()
        _source_use_require_v1(not self._closed and mono < self._deadline and now < self._enrollment_expires)
        if stage_deadline is not None:
            _source_use_require_v1(mono < stage_deadline[0] and now < stage_deadline[1])
        return now, mono

    def prepare_action_v1(self, raw_proposal: bytes):
        _source_use_require_v1(not self._closed and self._authority is not None and self._root.operation is None)
        request, preview = self._authority.prepare_action_v1(raw_proposal)
        self._pending_ref, self._preview = request, preview
        return request, preview

    def _confirm_prepared_v1(self):
        from .owner_source_use_windows import _start_native_operation_v1

        _source_use_require_v1(not self._closed and self._authority is not None)
        with self._authority._lock:
            _, mono = self._authority._live_v1()
            pending = self._authority._pending
            _source_use_require_v1(pending is not None and pending.request_ref == self._pending_ref
                                   and mono < pending.deadline_monotonic_ns)
            authentication, deadline, reference = pending.authentication, pending.deadline_monotonic_ns, pending.request_ref
        _start_native_operation_v1(self._root, reference, authentication, deadline)

    def complete_action_v1(self, pending_ref, raw_response):
        from ..pretrade.pr169_pretrade1_resolvers import KalshiFeeScenarioSessionV1
        from ..stage1_prediction_markets.qku_computation_control_plane.receipts import (
            PublicDataSourceUseActionV1, PublicDataSourceUseScopeV1, SourceUseAttributedActionV1,
        )

        try:
            _source_use_require_v1(not self._closed and self._authority is not None)
            self._pending_ref = self._preview = None
            result = self._authority.complete_action_v1(pending_ref, raw_response)
        finally:
            # A rejected/expired completion cannot leave its raw response in the
            # bounded native completion slot. Never discard another operation.
            with self._root.operation_lock:
                if type(pending_ref) is str:
                    retained = self._root.completed.get(pending_ref)
                    if retained is not None and retained[0] is raw_response:
                        self._root.completed.pop(pending_ref)
        payload = result.event.typed_payload
        if type(payload) is PublicDataSourceUseActionV1:
            _source_use_require_v1(payload.schema_version == "PUBLIC_SOURCE_USE_ACTION_V1"
                                   and type(payload.scope) is PublicDataSourceUseScopeV1)
            if payload.action == "OBSERVE_ONCE":
                self._complete_public_capture_v1(result.event)
            return self.read_status_v1()
        _source_use_require_v1(type(payload) is SourceUseAttributedActionV1)
        if payload.action == "OBSERVE_ONCE":
            authority = self._authority
            with authority._lock:
                binding = next((value for value in authority._bindings.values()
                    if value._permit is not None and value._permit._event.record_id == result.event.record_id), None)
                _source_use_require_v1(binding is not None)
                permit = binding._permit
                request = permit._request
                authority._check_binding_v1(binding, inputs=(request.fills, request.balance_increment, request.prior_rounding_overpayment))
                scope = authority._selected_scope
                arguments = dict(source_receipt=binding._source, rights_receipt=binding._rights,
                    account_scope=scope.account_scope_ref, internal_use_class=scope.internal_use_class,
                    permitted_retention_class=scope.permitted_retention_class, expected_market_ticker=request.market_ticker,
                    process_epoch_id=authority._process_ref, monotonic_clock_id=authority._clock_ref,
                    operating_authorization_ref=permit._event.record_id,
                    authorization_expires_at_utc=permit._event.typed_payload.expires_at_utc,
                    deadline_monotonic_ns=permit._deadline, source_use_binding=binding)
            try:
                # No S/O acquisition or computation under A. The original session
                # creates the original collector and uses the original cash owner.
                session = KalshiFeeScenarioSessionV1(**arguments)
                observed = session.evaluate(fills=request.fills, balance_increment=request.balance_increment,
                                             prior_rounding_overpayment=request.prior_rounding_overpayment)
                with authority._lock:
                    authority._check_binding_v1(binding, permit._owner,
                        inputs=(request.fills, request.balance_increment, request.prior_rounding_overpayment), allow_published=True)
                    _source_use_require_v1(permit._published and observed.operating_authorization_ref == permit._event.record_id)
                    self._result = (observed, binding, binding._generation, permit._event.record_id)
            except BaseException:
                with authority._lock:
                    permit._failed = True
                    if authority._active_permit is permit:
                        authority._active_permit = None
                raise
        return self.read_status_v1()

    def _complete_public_capture_v1(self, event):
        from ..stage1_prediction_markets.selected_venues.market_data import _create_public_market_data_session_v1
        from ..stage1_prediction_markets.qku_computation_control_plane.point_in_time import PITEventDispositionV1
        from ..stage1_prediction_markets.orderbook_event_state_snapshot.handoff import _require_public_publication_handle_v1

        authority = self._authority
        with authority._lock:
            binding = authority._active_permit
            authority._check_public_binding_v1(binding)
            _source_use_require_v1(binding._event == event and not binding._started)
        session = None
        try:
            # No public network/storage effect executes under the control lock.
            session = _create_public_market_data_session_v1(binding=binding)
            disposition, publications = session.run_bounded_v1()
            _source_use_require_v1(disposition is PITEventDispositionV1.COMMITTED
                                   and type(publications) is tuple and publications)
            for publication in publications:
                _require_public_publication_handle_v1(publication=publication)
            session.close_v1()
            with authority._lock:
                authority._check_public_binding_v1(binding)
                self._result = (publications, binding, binding._generation, event.record_id)
        except BaseException as primary:
            with authority._lock:
                binding._failed = True
            if session is not None:
                try:
                    session.close_v1()
                except BaseException:
                    primary.add_note("public capture owned cleanup failed; permission remains invalid")
            raise

    def cancel_v1(self):
        from .owner_source_use_windows import _cancel_native_operation_v1

        if self._authority is not None:
            self._authority.cancel_pending_v1()
        self._pending_ref = self._preview = self._enrollment_pending = self._enrollment_pending_deadline = None
        _cancel_native_operation_v1(self._root)

    def stop_v1(self):
        from .owner_source_use_windows import _cancel_native_operation_v1

        self._closed = True
        if self._authority is not None:
            self._authority.stop_v1()
        self._pending_ref = self._preview = self._enrollment_pending = self._enrollment_pending_deadline = None
        _cancel_native_operation_v1(self._root)

    def read_status_v1(self):
        from ..stage1_prediction_markets.qku_computation_control_plane.receipts import PublicDataSourceUseScopeV1

        if self._authority is None:
            return MappingProxyType({"action": "ENROLLMENT", "disposition": "STOPPED" if self._closed else "ENROLLMENT_ONLY",
                                     "request_ref": self._pending_ref, "generation": 0, "state": "DENIED", "expiry": None,
                                     "already_started": False})
        authority = self._authority
        with authority._lock:
            if not authority._stopped:
                try:
                    authority._live_v1()
                except Exception:
                    authority.stop_v1()
            head = authority._head
            permit = authority._last_operating_permit
            state = "STOPPED" if authority._stopped else "DENIED"
            if not authority._stopped and authority._use is not None:
                try:
                    if type(authority._selected_scope) is PublicDataSourceUseScopeV1:
                        now, _ = authority._live_v1()
                        _source_use_require_v1(authority._review is not None
                            and now < authority._review.typed_payload.expires_at_utc
                            and now < authority._use.typed_payload.expires_at_utc)
                        if authority._active_permit is not None:
                            authority._check_public_binding_v1(authority._active_permit)
                    else:
                        binding = next(iter(authority._bindings.values()))
                        authority._check_binding_v1(binding)
                    state = "ACTIVE"
                except Exception:
                    state = "STOPPED" if authority._stopped else "EXPIRED_OR_NOT_CURRENT"
            return MappingProxyType({"action": None if head is None else head.typed_payload.action,
                "disposition": authority._last_disposition, "request_ref": self._pending_ref,
                "event_ref": None if head is None else head.record_id,
                "generation": 0 if head is None else head.typed_payload.generation_after,
                "state": state,
                "expiry": None if authority._last_use_event is None else authority._last_use_event.typed_payload.expires_at_utc.isoformat(),
                "already_started": bool(permit is not None and permit._started)})

    def _display_result_v1(self):
        """Assign only the closed local model while A still protects publication."""
        from ..stage1_prediction_markets.qku_computation_control_plane.source_policy import PublicSourceUseBindingV1

        _source_use_require_v1(self._authority is not None)
        with self._authority._lock:
            _source_use_require_v1(self._result is not None)
            result, binding, generation, permit_ref = self._result
            if type(binding) is PublicSourceUseBindingV1:
                self._authority._check_public_binding_v1(binding)
                _source_use_require_v1(binding._generation == generation and binding._event.record_id == permit_ref
                                       and type(result) is tuple)
                self._display_model = MappingProxyType({"label": "PHASE_A_PUBLIC_DATA_INTERNAL",
                    "profile": binding._capture.scope.profile_id.value,
                    "capture_session": binding._capture.capture_session_id,
                    "publication_count": len(result), "no_order_authority": True})
                return self._display_model
            self._authority._check_binding_v1(binding, binding._permit._owner, allow_published=True)
            _source_use_require_v1(binding._generation == generation and binding._permit._published
                                   and binding._permit._event.record_id == permit_ref)
            self._display_model = MappingProxyType({"label": "OBSERVED_FEE_HYPOTHETICAL_SCENARIO — AS-OF HISTORICAL RESULT",
                "market": result.market_ticker, "event": result.event_ticker, "series": result.series_ticker,
                "basis": result.fee_basis, "multiplier": str(result.fee_multiplier),
                "entry_trade_cashflow_total": str(result.cashflows.entry_trade_cashflow_total),
                "platform_fee_total": str(result.cashflows.platform_fee_total),
                "expected_rebate_total": str(result.cashflows.expected_rebate_total),
                "rounding_overpayment_after": str(result.cashflows.rounding_overpayment_after),
                "fills": tuple((str(fill.contracts), str(fill.yes_price)) for fill in result.fills),
                "balance_increment": str(result.balance_increment), "prior_rounding_overpayment": str(result.prior_rounding_overpayment),
                "available_wall_ns": result.available_wall_ns, "available_monotonic_ns": result.available_monotonic_ns,
                "evaluated_monotonic_ns": result.evaluated_monotonic_ns})
            return self._display_model

    def _begin_enrollment_v1(self):
        from uuid import uuid4
        from .owner_source_use_windows import _start_native_operation_v1

        _source_use_require_v1(not self._closed and self._authority is None and self._enrollment_stage is None
                               and self._root.enrollment.root_state == "ENROLLMENT_ONLY" and self._root.operation is None)
        now, mono = self._enrollment_time_v1()
        deadline = (min(self._deadline, mono + 120_000_000_000), min(self._enrollment_expires, now + timedelta(seconds=120)))
        pending = _begin_source_use_authentication_v1(self._root.enrollment, operation="CREATE")
        self._enrollment_time_v1(deadline)
        self._enrollment_pending = pending
        self._enrollment_pending_deadline = deadline
        self._enrollment_stage = "CREATE"
        self._pending_ref = uuid4().hex
        _start_native_operation_v1(self._root, self._pending_ref, pending, deadline[0])

    def _complete_enrollment_v1(self, pending_ref, raw):
        from dataclasses import replace
        from uuid import uuid4
        from .owner_source_use_windows import _require_completed_operation_v1, _start_native_operation_v1
        from ..stage1_prediction_markets.qku_computation_control_plane.serialization import deterministic_json

        try:
            pending = self._enrollment_pending
            deadline = self._enrollment_pending_deadline
            self._enrollment_pending = self._enrollment_pending_deadline = None
            _source_use_require_v1(not self._closed and self._authority is None and pending is not None
                                   and deadline is not None and type(pending_ref) is str and pending_ref == self._pending_ref)
            now, _ = self._enrollment_time_v1(deadline)
            _require_completed_operation_v1(self._root, pending_ref, raw)
            verified = _verify_source_use_response_v1(pending, raw, verified_at_utc=now)
            now, mono = self._enrollment_time_v1(deadline)
            if self._enrollment_stage == "CREATE":
                key_data, backup = verified
                key = _validate_public_key_v1(key_data)
                temporary = replace(self._root.enrollment, root_state="ACTIVE", key_id_b64=_b64_v1(key.credential_id),
                    key_data_b64=_b64_v1(key_data), initial_counter=int.from_bytes(raw.authenticator_data[33:37], "big"),
                    key_backup_eligible=backup, registered_at_utc=now)
                pending = _begin_source_use_authentication_v1(temporary, operation="GET")
                deadline = (min(self._deadline, mono + 120_000_000_000), min(self._enrollment_expires, now + timedelta(seconds=120)))
                self._enrollment_time_v1(deadline)
                self._enrollment_pending = pending
                self._enrollment_pending_deadline = deadline
                self._enrollment_stage = "POSSESSION"
                self._pending_ref = uuid4().hex
                _start_native_operation_v1(self._root, self._pending_ref, pending, deadline[0])
                return None
            _source_use_require_v1(self._enrollment_stage == "POSSESSION")
            initial = pending.enrollment.initial_counter
            _source_use_require_v1((initial == verified.counter == 0) or verified.counter > initial)
            candidate = replace(pending.enrollment, initial_counter=verified.counter, registered_at_utc=now)
            self._enrollment_candidate = deterministic_json(candidate)
            self._pending_ref = None
            self._enrollment_stage = "PUBLIC_CANDIDATE_ONLY"
            # The protected root remains ENROLLMENT_ONLY; this process cannot activate.
            return self._enrollment_candidate
        finally:
            with self._root.operation_lock:
                if type(pending_ref) is str:
                    retained = self._root.completed.get(pending_ref)
                    if retained is not None and retained[0] is raw:
                        self._root.completed.pop(pending_ref)
