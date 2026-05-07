#!/usr/bin/env python3
from __future__ import annotations
import argparse
import pathlib

FORBIDDEN_NAMES = {
    'AtomicRows.bundle.jsonl', 'AtomicRows.bundle.sha256', '.env', 'secrets.json',
}
FORBIDDEN_PATH_PARTS = {
    'live_connectors', 'order_execution', 'private_state', 'runtime_services',
    'telegram_runtime', 'dashboard_runtime', 'external_repo_clone',
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--repo-root', required=True)
    parser.add_argument('--forbid-source-retrieval', action='store_true')
    parser.add_argument('--forbid-source-acceptance', action='store_true')
    parser.add_argument('--forbid-connector-binding', action='store_true')
    parser.add_argument('--forbid-private-state-fetch', action='store_true')
    parser.add_argument('--forbid-order-execution', action='store_true')
    parser.add_argument('--forbid-neural-training', action='store_true')
    parser.add_argument('--forbid-neural-inference', action='store_true')
    parser.add_argument('--forbid-external-repo-clone', action='store_true')
    parser.add_argument('--forbid-package-install-scripts', action='store_true')
    args = parser.parse_args()

    root = pathlib.Path(args.repo_root)
    for path in root.rglob('*'):
        if '.git' in path.parts:
            continue
        if path.name in FORBIDDEN_NAMES:
            raise SystemExit(f'forbidden runtime/secret artifact present: {path}')
        normalized = '/'.join(path.parts)
        if any(part in normalized for part in FORBIDDEN_PATH_PARTS):
            raise SystemExit(f'forbidden runtime path present: {path}')
    print('NO_RUNTIME_ARTIFACT_GATE_OK')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
