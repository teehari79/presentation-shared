#!/usr/bin/env bash
set -euo pipefail

python3 - <<'PY'
import json
from pathlib import Path

root = Path('.')
for path in sorted((root / 'schemas').glob('*.json')):
    with path.open('r', encoding='utf-8') as f:
        json.load(f)
    print(f'valid json: {path}')
PY

python3 tests/validate_fixtures.py
