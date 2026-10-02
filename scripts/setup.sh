#!/usr/bin/env bash
source "$(dirname "$0")/common.sh"
mode="${1:-all}"
case "$mode" in
  all) mapfile -t extensions < <(find requirements -maxdepth 1 -name '*.in' ! -name minimal.in ! -name main.in -printf '%f\n' | sed 's/\.in$//' | sort)
       profiles=(main "${extensions[@]}") ;;
  minimal|main) profiles=("$mode") ;;
  *) echo 'Usage: bash scripts/setup.sh [all|minimal|main]' >&2; exit 2 ;;
esac
python3 - "$mode" "${profiles[@]}" "${INSTALL_SYSTEM_PACKAGES:-1}" "${INSTALL_BROWSER:-1}" <<'PY'
import json, sys
from pathlib import Path
Path('.environment-status.json').write_text(json.dumps({
  'requested_mode':sys.argv[1], 'requested_profiles':sys.argv[2:-2],
  'complete':False, 'installed':[],
  'system_packages_requested':sys.argv[-2]=='1' and sys.argv[1]!='minimal',
  'browser_requested':sys.argv[-1]=='1' and sys.argv[1]!='minimal',
  'browser_launch_verified':False,
}, indent=2))
PY
if [[ "$mode" != minimal && "${INSTALL_SYSTEM_PACKAGES:-1}" == 1 ]]; then
  bash scripts/system.sh
fi
uv_bin="$(quant_uv)"
mkdir -p .venvs artifacts logs
for profile in "${profiles[@]}"; do
  [[ -n "$profile" ]] || continue
  lock="requirements/$profile.lock"
  [[ -f "$lock" ]] || { echo "Missing $lock. Generate and review locks before installation." >&2; exit 1; }
  version="$(quant_python_version "$profile")"
  env_dir=".venvs/$profile"
  if [[ "$profile" == main || "$profile" == minimal ]]; then env_dir=.venv; fi
  "$uv_bin" python install "$version" --no-bin
  "$uv_bin" venv --python "$version" --allow-existing "$env_dir"
  "$uv_bin" pip sync --python "$env_dir/bin/python" --require-hashes "$lock" --torch-backend cpu
  if [[ "$env_dir" == .venv ]]; then
    "$uv_bin" pip install --python "$env_dir/bin/python" --no-deps --no-build-isolation -e .
  fi
  "$uv_bin" pip check --python "$env_dir/bin/python"
  "$env_dir/bin/python" scripts/doctor.py --profile "$profile"
  if [[ "$mode" != minimal ]]; then
    "$env_dir/bin/python" -m ipykernel install --prefix "$QUANT_ROOT/.venv" \
      --name "quant-$profile" --display-name "Quant $profile (Python $version)"
  fi
  python3 - "$profile" <<'PY'
import json, sys
from pathlib import Path
p = Path('.environment-status.json'); status = json.loads(p.read_text())
status['installed'].append(sys.argv[1]); p.write_text(json.dumps(status, indent=2))
PY
done
if [[ "$mode" != minimal && "${INSTALL_BROWSER:-1}" == 1 ]]; then
  if [[ "${INSTALL_BROWSER_DEPS:-${INSTALL_SYSTEM_PACKAGES:-1}}" == 1 ]]; then
    .venv/bin/python -m playwright install --with-deps chromium
  else
    .venv/bin/python -m playwright install chromium
  fi
  .venv/bin/python scripts/browser_smoke.py
  python3 - <<'PY'
import json
from pathlib import Path
p=Path('.environment-status.json'); status=json.loads(p.read_text())
status['browser_launch_verified']=True; p.write_text(json.dumps(status,indent=2))
PY
fi
.venv/bin/python -m pytest -q
.venv/bin/python -m quant_cloud.cli demo --output artifacts/setup-demo
python3 - <<'PY'
import json
from pathlib import Path
p=Path('.environment-status.json'); status=json.loads(p.read_text())
status['complete']=True; p.write_text(json.dumps(status, indent=2))
PY
echo "Environment installation and offline workflow checks completed: $mode"
