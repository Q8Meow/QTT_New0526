"""Dormant, finite selected-public-data transport. Import performs no I/O."""

from __future__ import annotations

import base64
import os
import ssl
import threading
import time
from types import MappingProxyType

from ..qku_computation_control_plane.context import _native_require, _public_counter_v1
from ..qku_computation_control_plane.receipts import (
    PublicNativeObservationV1, _public_identity_v1, _public_observation_spine_v1,
)
from ..qku_computation_control_plane.source_policy import (
    _public_binding_facts_v1, _resolve_public_operational_inputs_v1,
)
from ..qku_computation_control_plane.serialization import deterministic_json
from ..market_data_ingest.adapter import (
    PublicDataReadRequestV1, compile_public_read_request_v1, _public_native_tree_v1,
    translate_public_observation_v1,
)


_PUBLIC_SESSIONS_V1 = {}


def _public_tls_context_v1():
    context = ssl.create_default_context()
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    _native_require(context.check_hostname and context.verify_mode == ssl.CERT_REQUIRED,
                    "public transport requires verified TLS")
    return context


def _public_admit_effect_v1(*, binding, descriptor, method):
    facts = _public_binding_facts_v1(binding)
    session = binding._owner
    _native_require(facts["native_qualified"] is True and type(session) is PublicMarketDataSessionV1
                    and _PUBLIC_SESSIONS_V1.get(id(session)) is session,
                    "synthetic or unowned permission cannot open a native public transport")
    _, wall, _ = session._guard_v1()
    plan = _resolve_public_operational_inputs_v1(binding=binding, evaluated_at_ns=wall)
    matches = [row for row in plan if row[4] == descriptor and row[4]["method"] == method]
    _native_require(len(matches) == 1, "native effect descriptor differs from the admitted fixed request")
    return matches[0]


def _public_open_https_v1(descriptor, timeout, *, binding):
    _public_admit_effect_v1(binding=binding, descriptor=descriptor, method="GET")
    _native_require(type(timeout) in (int, float) and 0 < timeout < float("inf"), "invalid finite HTTPS timeout")
    timeout = min(timeout, binding._owner._timeout_v1(binding._capture.scope.budget.open_timeout_ns))
    import http.client

    # http.client does not discover or follow environment proxies or redirects.
    return http.client.HTTPSConnection(descriptor["host"], port=443, timeout=timeout,
                                       context=_public_tls_context_v1())


def _public_open_websocket_v1(descriptor, headers, *, binding, open_timeout, close_timeout, max_size, max_queue):
    _public_admit_effect_v1(binding=binding, descriptor=descriptor, method="WEBSOCKET")
    _native_require(headers is None, "caller-selected public handshake headers are forbidden")
    budget = binding._capture.scope.budget
    _native_require(type(max_size) is int and 0 < max_size <= budget.max_message_bytes
                    and type(max_queue) is int and 0 < max_queue <= budget.queue_high_water,
                    "WebSocket buffering exceeds the admitted finite budget")
    for timeout in (open_timeout, close_timeout):
        _native_require(type(timeout) in (int, float) and 0 < timeout < float("inf"), "invalid finite WebSocket timeout")
    open_timeout = min(open_timeout, binding._owner._timeout_v1(budget.open_timeout_ns))
    close_timeout = min(close_timeout, budget.close_timeout_ns / 1_000_000_000)
    import logging
    import websockets
    from websockets.sync.client import connect
    from ..qku_computation_control_plane.source_policy import _public_handshake_headers_v1

    _native_require(websockets.__version__ == "17.0.1", "unqualified public WebSocket runtime")
    uri = "wss://" + descriptor["host"] + descriptor["path"]
    if descriptor["query"]:
        uri += "?" + descriptor["query"]
    logger = logging.Logger("QTT_PUBLIC_CAPTURE")
    logger.disabled, logger.propagate = True, False
    ephemeral = _public_handshake_headers_v1(binding=binding, descriptor=descriptor)
    try:
        tls = _public_tls_context_v1()
        _public_admit_effect_v1(binding=binding, descriptor=descriptor, method="WEBSOCKET")
        effective_open_timeout = min(open_timeout, binding._owner._timeout_v1(budget.open_timeout_ns))
        return connect(uri, ssl=tls, additional_headers=ephemeral, proxy=None,
                       compression=None, ping_interval=None, open_timeout=effective_open_timeout,
                       close_timeout=close_timeout, max_size=max_size, max_queue=max_queue, logger=logger)
    finally:
        ephemeral.clear()


class PublicMarketDataSessionV1:
    """One exact authenticated capture. No constructor, retries, orders or implicit defaults."""

    __slots__ = ("_binding", "_scope", "_budget", "_inputs", "_started", "_closed", "_socket", "_store",
                 "_requests", "_messages", "_bytes", "_retained_records", "_retained_bytes", "_epoch",
                 "_ordinal", "_last_wall", "_last_mono", "_rate_state", "_observations", "_publications",
                 "_cleanup_error", "_cleanup_failed_resources", "_process_id", "_thread_id", "_stream_state",
                 "_translations", "_continuity_witnesses", "_lock", "_observation_lock",
                 "_active_metadata", "_metadata_versions", "_observation_plans")

    def __init__(self):
        raise TypeError("public session requires the authenticated controller factory")

    def __reduce__(self):
        raise TypeError("public session cannot be serialized")

    def __copy__(self):
        raise TypeError("public session cannot be copied")

    def __deepcopy__(self, memo):
        raise TypeError("public session cannot be copied")

    def _fail_v1(self):
        if _PUBLIC_SESSIONS_V1.get(id(self)) is self:
            authority = self._binding._authority
            if authority is None:
                self._binding._failed = True
            else:
                with authority._lock:
                    self._binding._failed = True

    def _guard_v1(self):
        _native_require(_PUBLIC_SESSIONS_V1.get(id(self)) is self and self._binding._owner is self
                        and self._process_id == os.getpid() and self._thread_id == threading.get_ident()
                        and not self._closed, "public session custody changed")
        try:
            facts = _public_binding_facts_v1(self._binding)
        except BaseException:
            self._fail_v1()
            raise
        before, wall, after = time.monotonic_ns(), time.time_ns(), time.monotonic_ns()
        coherent = (all(type(value) is int and 0 <= value <= 2**63 - 1 for value in (before, wall, after))
                    and after >= before >= self._last_mono and wall >= self._last_wall
                    and after - before <= self._budget.maximum_wall_uncertainty_ns)
        if not coherent:
            self._fail_v1()
        _native_require(coherent, "public clock regressed or uncertainty exceeded")
        self._last_mono, self._last_wall = after, wall
        current = after < min(self._budget.deadline_monotonic_ns, self._binding._deadline)
        if not current:
            self._fail_v1()
        _native_require(current, "public capture deadline expired")
        return facts, wall, after

    def _timeout_v1(self, limit_ns):
        _, _, now = self._guard_v1()
        remaining = min(limit_ns, min(self._budget.deadline_monotonic_ns, self._binding._deadline) - now)
        _native_require(remaining > 0, "public operation has no remaining time")
        return remaining / 1_000_000_000

    def _charge_request_v1(self, request):
        from ..qku_computation_control_plane.source_policy import PublicRequestRateBindingV1

        _, wall, mono = self._guard_v1()
        _native_require(self._requests < self._budget.max_requests
                        and self._messages < self._budget.max_application_messages
                        and self._bytes < self._budget.max_application_bytes
                        and self._retained_records < self._budget.max_retained_records
                        and self._retained_bytes < self._budget.max_retained_bytes,
                        "public request/receive/retention budget exhausted before effect")
        matches = [row for row in self._inputs["rate_bindings"] if type(row) is PublicRequestRateBindingV1
                   and row.profile_id is request.profile_id and request.operation_id in row.operation_classes
                   and row.effective_from_ns <= wall < row.expires_at_ns]
        _native_require(len(matches) == 1, "public request allocation missing or conflicting")
        rate = matches[0]
        rate.__post_init__()
        # The source owner must bind exclusive shared-counter custody explicitly.
        _native_require(rate.allocation_ref in self._inputs["exclusive_allocation_refs"],
                        "shared request counter has no verified exclusive allocation")
        state = self._rate_state.get(rate.binding_id)
        if state is None:
            state = dict(start=mono, last=None, count=0, tokens=None, token_time=mono)
            self._rate_state[rate.binding_id] = state
        _native_require(state["last"] is None or mono - state["last"] >= rate.minimum_request_interval_ns,
                        "provider/owner request spacing exhausted")
        if mono - state["start"] >= rate.window_ns:
            state["start"], state["count"] = mono, 0
        _native_require(state["count"] < rate.maximum_requests_per_window, "provider request window exhausted")
        if rate.token_capacity_or_none is not None:
            from fractions import Fraction
            from ..qku_computation_control_plane.context import _native_retail_decimal_string_v1

            capacity = Fraction(_native_retail_decimal_string_v1(rate.token_capacity_or_none))
            refill = Fraction(_native_retail_decimal_string_v1(rate.token_refill_per_second_or_none))
            available = capacity if state["tokens"] is None else min(capacity,
                state["tokens"] + refill * Fraction(mono - state["token_time"], 1_000_000_000))
            cost = Fraction(_native_retail_decimal_string_v1(dict(rate.token_costs)[request.operation_id]))
            _native_require(available >= cost, "provider token allocation exhausted")
            state["tokens"], state["token_time"] = available - cost, mono
        self._requests += 1
        state["count"] += 1
        state["last"] = mono

    def _observe_v1(self, request, raw, status, headers):
        # Count the received body before validation; rejection never refunds a budget.
        _native_require(type(raw) is bytes, "public receive requires original application bytes")
        self._messages += 1
        self._bytes += len(raw)
        _native_require(self._messages <= self._budget.max_application_messages
                        and self._bytes <= self._budget.max_application_bytes
                        and len(raw) <= self._budget.max_message_bytes, "received application budget exceeded")
        _public_native_tree_v1(raw, maximum_bytes=self._budget.max_message_bytes)
        facts, wall, mono = self._guard_v1()
        self._ordinal += 1
        identity = _public_identity_v1("PUBLIC_NATIVE_CAPTURE_V1", request.profile_id.value,
            facts["action_ref"], facts["capture_session_id"], self._epoch, self._ordinal)
        observation = PublicNativeObservationV1(identity, request.request_id, request.profile_id, request.operation_id,
            facts["capture_session_id"], self._epoch, self._ordinal, status, headers,
            base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii"), wall, mono, self._inputs["process_epoch_id"],
            self._inputs["monotonic_clock_id"], self._inputs["clock_quality_ref"],
            self._inputs["wall_uncertainty_ns"], (request.source_binding_ref,), facts["action_ref"],
            facts["scope_generation"], request.native_contract_version)
        encoded = deterministic_json(_public_observation_spine_v1(
            observation=observation, scope_ref=facts["scope_ref"])).encode("utf-8")
        _native_require(len(encoded) <= 65536 and self._retained_records < self._budget.max_retained_records
                        and self._retained_bytes + len(encoded) <= self._budget.max_retained_bytes,
                        "original observation cannot fit its admitted retention envelope")
        self._retained_records += 1
        self._retained_bytes += len(encoded)
        self._observations.append(observation)
        return observation

    def _https_v1(self, request, descriptor):
        _, wall, _ = self._guard_v1()
        plan = _resolve_public_operational_inputs_v1(binding=self._binding, evaluated_at_ns=wall)
        _native_require(any(row[0] is request and row[4] == descriptor for row in plan),
                        "HTTPS request does not have current source-owner admission")
        self._charge_request_v1(request)
        connection = _public_open_https_v1(descriptor, self._timeout_v1(self._budget.open_timeout_ns), binding=self._binding)
        self._socket = connection
        try:
            self._guard_v1()
            path = descriptor["path"] + ("?" + descriptor["query"] if descriptor["query"] else "")
            connection.timeout = self._timeout_v1(self._budget.open_timeout_ns)
            if connection.sock is not None:
                connection.sock.settimeout(connection.timeout)
            connection.request("GET", path, headers={"Accept": "application/json", "Accept-Encoding": "identity",
                                                      "Connection": "close"})
            connection.sock.settimeout(self._timeout_v1(self._budget.receive_timeout_ns))
            response = connection.getresponse()
            pairs = response.getheaders()
            normalized = {}
            for name, value in pairs:
                key = name.lower()
                _native_require(key not in normalized, "duplicate HTTP header framing")
                normalized[key] = value
            _native_require(normalized.get("content-encoding", "identity").lower() == "identity"
                            and "transfer-encoding" not in normalized
                            and normalized.get("content-type", "").split(";", 1)[0].strip().lower() == "application/json",
                            "unsupported HTTP compression/framing/media type")
            length = normalized.get("content-length")
            _native_require(type(length) is str and length.isascii() and length.isdigit(), "missing exact HTTP body length")
            size = int(length)
            _native_require(size <= self._budget.max_message_bytes, "HTTP body exceeds receive bound")
            connection.sock.settimeout(self._timeout_v1(self._budget.receive_timeout_ns))
            raw = response.read(size + 1)
            _native_require(len(raw) == size, "HTTP body length mismatch")
            headers = {key: value for key, value in normalized.items() if key in {
                "content-type", "content-length", "date", "retry-after"}}
            observation = self._observe_v1(request, raw, response.status, headers)
            _native_require(response.status == 200, "RATE_LIMITED" if response.status == 429 else "PUBLIC_HTTP_FAILURE")
            return (observation,)
        except BaseException:
            self._fail_v1()
            raise
        finally:
            try:
                connection.close()
            except BaseException as exc:
                self._cleanup_error = (exc,)
                self._cleanup_failed_resources.add("_socket")
                self._fail_v1()
                raise
            else:
                self._socket = None

    def _translate_received_v1(self, *, original, request, source, contract):
        from dataclasses import replace
        from ..market_data_ingest.adapter import _compile_public_catalog_metadata_v1

        _native_require(self._observations and self._observations[-1] is original
            and original.observation_id not in self._observation_plans,
            "translation must consume the current original exactly once")
        metadata = tuple(row for row in self._active_metadata if row.instrument_id in request.instrument_ids)
        selected_request = replace(request, metadata_refs=tuple(row.metadata_id for row in metadata))
        context = dict(request=selected_request, contract=contract, wall_clock_source_id=self._inputs["wall_clock_source_id"],
            source_bindings=self._inputs["source_bindings"], original_prefix=tuple(self._observations[:-1]))
        if request.operation_id in {"K_MARKET", "K_EVENT", "K_SERIES", "P_MARKET", "G_EVENT", "G_EVENTS"}:
            translation, metadata, selected_request = _compile_public_catalog_metadata_v1(observation=original,
                metadata=metadata, source_binding=source, translation_context=context)
            successors = {row.instrument_id: row for row in metadata}
            self._active_metadata = tuple(successors.get(row.instrument_id, row) for row in self._active_metadata)
            self._metadata_versions = (*self._metadata_versions, *metadata)
        else:
            translation = translate_public_observation_v1(observation=original, metadata=metadata,
                source_binding=source, translation_context=context)
        self._observation_plans[original.observation_id] = (selected_request, source, metadata, contract)
        self._translations.append(translation)
        return translation

    def _websocket_v1(self, request, descriptor, *, refresh_pending=False):
        from ..qku_computation_control_plane.point_in_time import _issue_public_stream_continuity_v1

        _, wall, _ = self._guard_v1()
        plan = _resolve_public_operational_inputs_v1(binding=self._binding, evaluated_at_ns=wall)
        selected = [row for row in plan if row[0] is request and row[4] == descriptor]
        _native_require(len(selected) == 1 and descriptor["method"] == "WEBSOCKET"
                        and self._socket is None and self._messages < self._budget.max_application_messages,
                        "public WebSocket request is not admitted or has no receive budget")
        _native_require(request.operation_id != "K_WS" or request.request_options["cmd"] == "subscribe",
                        "a new connection cannot unsubscribe an unowned subscription")
        _, source, metadata, contract, _ = selected[0]
        self._charge_request_v1(request)
        self._socket = _public_open_websocket_v1(descriptor, None, binding=self._binding,
            open_timeout=self._timeout_v1(self._budget.open_timeout_ns),
            close_timeout=self._budget.close_timeout_ns / 1_000_000_000,
            max_size=self._budget.max_message_bytes, max_queue=self._budget.queue_high_water)
        self._epoch += 1
        self._ordinal = 0
        received = []
        try:
            _, wall, _ = self._guard_v1()
            _resolve_public_operational_inputs_v1(binding=self._binding, evaluated_at_ns=wall)
            # The pinned client exposes its owned socket. Bound sendall as well
            # as application recv; a quiet peer cannot extend the original grant.
            self._socket.socket.settimeout(self._timeout_v1(self._budget.receive_timeout_ns))
            self._socket.send(deterministic_json(descriptor["command"]))
            while (self._messages < self._budget.max_application_messages
                   and self._bytes < self._budget.max_application_bytes
                   and self._retained_records < self._budget.max_retained_records
                   and self._retained_bytes < self._budget.max_retained_bytes):
                _, wall, _ = self._guard_v1()
                _resolve_public_operational_inputs_v1(binding=self._binding, evaluated_at_ns=wall)
                packet = self._socket.recv(timeout=self._timeout_v1(self._budget.receive_timeout_ns), decode=None)
                if type(packet) is bytes:
                    self._messages += 1
                    self._bytes += len(packet)
                    _native_require(False, "binary public WebSocket application body rejected")
                _native_require(type(packet) is str, "public WebSocket did not return a text opcode")
                try:
                    raw = packet.encode("utf-8", errors="strict")
                except UnicodeError:
                    self._messages += 1
                    _native_require(False, "public WebSocket text is not strict UTF-8")
                original = self._observe_v1(request, raw, None, {})
                _, wall, _ = self._guard_v1()
                _resolve_public_operational_inputs_v1(binding=self._binding, evaluated_at_ns=wall)
                translation = self._translate_received_v1(original=original, request=request, source=source, contract=contract)
                _native_require(translation.stream_disposition.get("message_type") != "error",
                                "public WebSocket provider protocol/authentication failure")
                if request.operation_id == "K_WS":
                    self._continuity_witnesses.append(_issue_public_stream_continuity_v1(session=self))
                received.append(original)
                if refresh_pending and (translation.stream_disposition.get("event_kind") == "LIFECYCLE"
                    or translation.stream_disposition.get("notification_type") in {"event_lifecycle","event_fee_update"}
                    and translation.stream_disposition["instrument_ids"]):
                    # Only an already-admitted later catalog request can consume
                    # the remaining original budget. This is not an implicit retry.
                    break
            return tuple(received)
        except BaseException:
            self._fail_v1()
            raise
        finally:
            owned = self._socket
            try:
                owned.close()
                worker = getattr(owned, "recv_events_thread", None)
                _native_require(worker is None or not worker.is_alive(), "public WebSocket receive worker remains live")
            except BaseException as exc:
                self._cleanup_error = (exc,)
                self._cleanup_failed_resources.add("_socket")
                self._fail_v1()
                raise
            else:
                self._socket = None

    def run_bounded_v1(self):
        """Return the existing committed disposition and issued publication handles."""
        from ..qku_computation_control_plane.context import _native_ident
        from ..qku_computation_control_plane.errors import SourcePolicyError, ReasonCode
        from ..qku_computation_control_plane.point_in_time import PITEventDispositionV1
        from ..qku_computation_control_plane.sqlite_reference import SQLitePhaseAAdapterV1
        from ..orderbook_event_state_snapshot.handoff import (
            _prepare_public_pit_batch_v1, _publish_public_pit_batch_v1, _require_public_publication_handle_v1,
        )

        _native_require(not self._started, "public capture can run only once")
        _, wall, _ = self._guard_v1()
        plan = _resolve_public_operational_inputs_v1(binding=self._binding, evaluated_at_ns=wall)
        for name in ("source_epoch_id", "input_version"):
            if name not in self._inputs:
                raise SourcePolicyError(ReasonCode.OWNER_DATA_MISSING, "public publication input unavailable: " + name)
            _native_ident(self._inputs[name])
        self._started = True
        try:
            self._store = SQLitePhaseAAdapterV1(root_capability=self._inputs["storage_root"],
                source_use_binding=self._binding, busy_timeout_ms=self._budget.storage_busy_timeout_ms)
            for index, (request, source, metadata, contract, descriptor) in enumerate(plan):
                self._guard_v1()
                if descriptor["method"] == "WEBSOCKET":
                    refresh_pending = any(row[0].operation_id in {"K_MARKET", "K_EVENT", "K_SERIES", "K_EVENT_FEES", "K_SERIES_FEES", "P_MARKET", "G_EVENT", "G_EVENTS"}
                        and set(row[0].instrument_ids) & set(request.instrument_ids) for row in plan[index+1:])
                    self._websocket_v1(request, descriptor, refresh_pending=refresh_pending)
                else:
                    original, = self._https_v1(request, descriptor)
                    self._translate_received_v1(original=original, request=request, source=source, contract=contract)
            batch = _prepare_public_pit_batch_v1(session=self, adapter=self._store)
            witness = self._store._commit_public_pit_batch_v1(batch=batch)
            publication = _publish_public_pit_batch_v1(batch=batch, adapter=self._store, witness=witness,
                source_epoch_id=self._inputs["source_epoch_id"], input_version=self._inputs["input_version"])
            self._publications.append(publication)
            result = (PITEventDispositionV1.COMMITTED, tuple(self._publications))
            self.close_v1()
            _require_public_publication_handle_v1(publication=publication)
            return result
        except BaseException:
            self._fail_v1()
            self.close_v1()
            raise

    def close_v1(self):
        if _PUBLIC_SESSIONS_V1.get(id(self)) is self:
            from ..qku_computation_control_plane.source_policy import _release_public_credential_v1

            _release_public_credential_v1(binding=self._binding)
        if self._closed:
            return
        prior = self._cleanup_error or ()
        if not hasattr(self, "_cleanup_failed_resources"):
            self._cleanup_failed_resources = set()
        failures = []
        for name in ("_socket", "_store"):
            owned = getattr(self, name)
            if owned is not None and name not in self._cleanup_failed_resources:
                try:
                    owned.close()
                    if name == "_socket":
                        worker = getattr(owned, "recv_events_thread", None)
                        _native_require(worker is None or not worker.is_alive(), "owned public receive worker remains live")
                except BaseException as exc:
                    failures.append(exc)
                    self._cleanup_failed_resources.add(name)
                else:
                    setattr(self, name, None)
        self._cleanup_error = tuple((*prior, *failures)) or None
        self._closed = self._cleanup_error is None
        _native_require(not prior, "prior owned cleanup remains unresolved")
        if failures:
            self._fail_v1()
            raise failures[0]


def _create_public_market_data_session_v1(*, binding):
    facts = _public_binding_facts_v1(binding)
    _native_require(binding._owner is None and not binding._started,
                    "public operating permission has already selected a receiver")
    result = object.__new__(PublicMarketDataSessionV1)
    result._binding, result._scope, result._budget = binding, facts["scope"], facts["budget"]
    result._inputs = facts["source_inputs"]
    result._lock, result._observation_lock = threading.RLock(), threading.RLock()
    result._started = result._closed = False
    result._socket = result._store = None
    result._requests = result._messages = result._bytes = result._retained_records = result._retained_bytes = 0
    result._epoch = result._ordinal = 0
    result._last_wall = result._last_mono = 0
    result._rate_state, result._stream_state = {}, {}
    result._observations, result._publications = [], []
    result._translations, result._continuity_witnesses = [], []
    result._active_metadata = tuple(result._inputs.get("metadata", ()))
    result._metadata_versions = result._active_metadata
    result._observation_plans = {}
    result._cleanup_error = None
    result._cleanup_failed_resources = set()
    result._process_id, result._thread_id = os.getpid(), threading.get_ident()
    binding._owner = result
    binding._started = True
    _PUBLIC_SESSIONS_V1[id(result)] = result
    result._guard_v1()
    return result
