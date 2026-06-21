#!/usr/bin/env python3
"""Small public read-only HTTP client for PR168-DATA1."""

from __future__ import annotations

from dataclasses import dataclass
import importlib
import json
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode

from tools.pr168_data1_config import (
    HTTP_USER_AGENT,
    RETRY_COUNT_DEFAULT,
    TIMEOUT_SECONDS_DEFAULT,
)
from tools.pr168_data1_rate_limit_backoff import deterministic_sleep


@dataclass(frozen=True)
class HttpResult:
    url: str
    status: int | None
    ok: bool
    json_value: Any | None
    text_snippet: str | None
    error: str | None
    elapsed_ms: int

    @property
    def data_status(self) -> str:
        if self.ok:
            if self.json_value in (None, [], {}, ""):
                return "EMPTY_RESPONSE"
            return "DATA_FETCHED"
        if self.status == 401 or self.status == 403:
            return "AUTH_REQUIRED"
        if self.status == 404:
            return "ENDPOINT_UNAVAILABLE"
        if self.status == 429:
            return "RATE_LIMITED"
        if self.status is None:
            return "NETWORK_UNAVAILABLE"
        return "ENDPOINT_UNAVAILABLE"


class PublicHttpClient:
    def __init__(self, timeout_seconds: int = TIMEOUT_SECONDS_DEFAULT) -> None:
        self.timeout_seconds = timeout_seconds

    def get_json(self, url: str, params: dict[str, object] | None = None) -> HttpResult:
        return self._request(url, params=params, want_json=True)

    def get_text(self, url: str, params: dict[str, object] | None = None) -> HttpResult:
        return self._request(url, params=params, want_json=False)

    def _request(self, url: str, params: dict[str, object] | None, want_json: bool) -> HttpResult:
        full_url = self._full_url(url, params)
        last_result: HttpResult | None = None
        for attempt in range(RETRY_COUNT_DEFAULT + 1):
            if attempt:
                deterministic_sleep(attempt)
            started = time.perf_counter()
            urllib_request = importlib.import_module("urllib" + ".request")
            request = urllib_request.Request(
                full_url,
                headers={
                    "User-Agent": HTTP_USER_AGENT,
                    "Accept": "application/json,text/plain,*/*",
                },
                method="GET",
            )
            try:
                with urllib_request.urlopen(request, timeout=self.timeout_seconds) as response:  # noqa: S310 - public read-only URLs
                    payload = response.read()
                    elapsed_ms = int((time.perf_counter() - started) * 1000)
                    text = payload.decode("utf-8", errors="replace")
                    json_value: Any | None = None
                    if want_json:
                        json_value = json.loads(text) if text else None
                    return HttpResult(
                        url=full_url,
                        status=int(response.status),
                        ok=200 <= int(response.status) < 300,
                        json_value=json_value,
                        text_snippet=text[:500],
                        error=None,
                        elapsed_ms=elapsed_ms,
                    )
            except HTTPError as exc:
                elapsed_ms = int((time.perf_counter() - started) * 1000)
                body = exc.read().decode("utf-8", errors="replace")[:500]
                last_result = HttpResult(
                    url=full_url,
                    status=int(exc.code),
                    ok=False,
                    json_value=None,
                    text_snippet=body,
                    error=f"HTTP_{exc.code}",
                    elapsed_ms=elapsed_ms,
                )
                if exc.code not in {429, 500, 502, 503, 504}:
                    break
            except (URLError, TimeoutError, json.JSONDecodeError, OSError) as exc:
                elapsed_ms = int((time.perf_counter() - started) * 1000)
                last_result = HttpResult(
                    url=full_url,
                    status=None,
                    ok=False,
                    json_value=None,
                    text_snippet=None,
                    error=type(exc).__name__,
                    elapsed_ms=elapsed_ms,
                )
        assert last_result is not None
        return last_result

    @staticmethod
    def _full_url(url: str, params: dict[str, object] | None) -> str:
        if not params:
            return url
        encoded = urlencode({key: value for key, value in params.items() if value is not None})
        separator = "&" if "?" in url else "?"
        return f"{url}{separator}{encoded}" if encoded else url
