#!/usr/bin/env bash
source "$(dirname "$0")/common.sh"
# Explicitly rerun after changing locks. The current Cloud experience does not
# automatically execute legacy maintenance scripts during repository refresh.
mode="$(python3 - <<'PY'
import json
from pathlib import Path
p=Path('.environment-status.json')
print(json.loads(p.read_text()).get('requested_mode','all') if p.exists() else 'all')
PY
)"
exec bash scripts/setup.sh "$mode"
