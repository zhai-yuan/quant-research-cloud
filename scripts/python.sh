#!/usr/bin/env bash
source "$(dirname "$0")/common.sh"
profile="${1:?Usage: bash scripts/python.sh <profile> <python arguments>}"
shift
[[ "$profile" =~ ^[a-z][a-z0-9_-]*$ ]] || exit 2
python_bin=".venvs/$profile/bin/python"
if [[ "$profile" == main || "$profile" == minimal ]]; then python_bin=.venv/bin/python; fi
[[ -x "$python_bin" ]] || { echo "Profile $profile is not installed." >&2; exit 1; }
exec "$python_bin" "$@"
