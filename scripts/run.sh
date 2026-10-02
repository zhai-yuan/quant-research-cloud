#!/usr/bin/env bash
source "$(dirname "$0")/common.sh"
[[ -x .venv/bin/python ]] || { echo 'Run bash scripts/setup.sh first.' >&2; exit 1; }
exec .venv/bin/python -m quant_cloud.cli "$@"
