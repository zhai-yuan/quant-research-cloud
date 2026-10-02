#!/usr/bin/env bash
set -euo pipefail
QUANT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$QUANT_ROOT"
export TZ="${TZ:-Asia/Shanghai}"
export MPLBACKEND="${MPLBACKEND:-Agg}"
export UV_CACHE_DIR="${UV_CACHE_DIR:-$QUANT_ROOT/.cache/uv}"
export UV_PYTHON_INSTALL_DIR="${UV_PYTHON_INSTALL_DIR:-$QUANT_ROOT/.tools/python}"
export UV_LINK_MODE="${UV_LINK_MODE:-copy}"
export UV_NO_PROGRESS=1
export QUANT_EXECUTION_MODE="${QUANT_EXECUTION_MODE:-local-paper}"
export QT_QPA_PLATFORM="${QT_QPA_PLATFORM:-offscreen}"
export PLAYWRIGHT_BROWSERS_PATH="${PLAYWRIGHT_BROWSERS_PATH:-$QUANT_ROOT/.tools/browsers}"
if [[ -d "$QUANT_ROOT/.tools/native/usr/lib/x86_64-linux-gnu" ]]; then
  export LD_LIBRARY_PATH="$QUANT_ROOT/.tools/native/usr/lib/x86_64-linux-gnu${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
fi
quant_uv() { python3 "$QUANT_ROOT/scripts/bootstrap.py"; }
quant_python_version() {
  python3 - "$1" <<'PY'
import json, sys
from pathlib import Path
config = Path('requirements/profiles.json')
profiles = json.loads(config.read_text()) if config.exists() else {}
print(profiles.get(sys.argv[1], {}).get('python', '3.11'))
PY
}
