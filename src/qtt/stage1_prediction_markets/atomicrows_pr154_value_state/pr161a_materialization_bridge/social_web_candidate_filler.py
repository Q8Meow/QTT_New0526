"""Social/web candidate helpers for PR161A."""

from __future__ import annotations

from typing import Mapping

from .source_intake import SOCIAL_WEB_CLASSES


def is_social_web_source(record: Mapping[str, object]) -> bool:
    return str(record.get("source_class")) in SOCIAL_WEB_CLASSES

