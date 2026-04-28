#!/usr/bin/env bash
set -euo pipefail

python3 - <<'PY'
import json
from pathlib import Path

root = Path('.')
schema_paths = sorted((root / 'schemas').glob('*.json')) + sorted((root / 'redteam' / 'schemas').glob('*.json'))
for path in schema_paths:
    with path.open('r', encoding='utf-8') as f:
        json.load(f)
    print(f'valid json: {path}')
PY

python3 tests/validate_fixtures.py

python3 tests/validate_scoring_framework.py
