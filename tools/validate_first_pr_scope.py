#!/usr/bin/env python3
from __future__ import annotations
import argparse
import json
import pathlib


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--repo-root', required=True)
    parser.add_argument('--scope-report', required=True)
    parser.add_argument('--block-runtime', action='store_true')
    parser.add_argument('--block-live', action='store_true')
    parser.add_argument('--block-sha', action='store_true')
    parser.add_argument('--block-companion-package', action='store_true')
    parser.add_argument('--block-profit-claims', action='store_true')
    args = parser.parse_args()
    scope = json.loads(pathlib.Path(args.scope_report).read_text(encoding='utf-8'))
    required = {
        'runtime', 'live', 'sha', 'companion_package', 'profit_claims',
        'source_retrieval', 'source_acceptance', 'connector_binding',
        'private_state_fetch', 'order_execution', 'neural_training',
        'neural_inference', 'external_repo_clone', 'package_install_scripts'
    }
    blocks = set(scope.get('blocks', []))
    if scope.get('first_pr_scope') != 'schema_only_scaffold' or not required.issubset(blocks):
        raise SystemExit('scope violation')
    print('FIRST_PR_SCOPE_GATE_OK')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
