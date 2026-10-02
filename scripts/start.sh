#!/usr/bin/env bash
source "$(dirname "$0")/common.sh"
[[ -x .venv/bin/python ]] || { echo 'Environment is not installed.' >&2; exit 1; }
python3 - <<'PY'
import json
from pathlib import Path
p=Path('.environment-status.json')
if not p.exists():
    raise SystemExit('Installation status is missing. Run scripts/setup.sh before startup.')
state=json.loads(p.read_text())
if not state.get('complete'):
    raise SystemExit('Installation is incomplete. Inspect the last setup error and rerun setup.')
mode=state['requested_mode']
expected=({'main'} | {p.stem for p in Path('requirements').glob('*.in') if p.stem!='minimal'}) if mode=='all' else {mode}
if set(state.get('installed',[])) != expected:
    raise SystemExit('Installed profile set does not match the requested setup; rerun setup.')
for profile in expected:
    env=Path('.venv') if profile in {'main','minimal'} else Path('.venvs')/profile
    if not (env/'bin/python').exists():
        raise SystemExit(f'Missing interpreter for profile {profile}.')
if state.get('browser_requested') and not state.get('browser_launch_verified'):
    raise SystemExit('Requested browser runtime has not passed its launch check.')
print(f'Validated installation status: {mode} ({len(expected)} profile(s)).')
PY
.venv/bin/python scripts/doctor.py --metadata-only
echo 'Ready for the installed research profiles. No broker connection or perpetual trading process is started.'
