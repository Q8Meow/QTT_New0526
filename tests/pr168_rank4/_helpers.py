from __future__ import annotations

from functools import lru_cache
from pathlib import Path
import json

from src.qtt.ranking.pr168_rank4.builder import run_layer
from src.qtt.ranking.pr168_rank4.models import GENERATED_DIR
from src.qtt.ranking.pr168_rank4.validator import run_validation


@lru_cache(maxsize=1)
def ensure_built() -> Path:
    run_layer(out_dir=GENERATED_DIR)
    run_validation(generated_dir=GENERATED_DIR)
    return GENERATED_DIR


def rows(filename: str) -> list[dict]:
    path = ensure_built() / filename
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def report(filename: str) -> dict:
    return json.loads((ensure_built() / filename).read_text(encoding="utf-8"))

