#!/usr/bin/env bash
source "$(dirname "$0")/common.sh"
uv_bin="$(quant_uv)"
if [[ "$#" == 0 ]]; then
  mapfile -t profiles < <(find requirements -maxdepth 1 -name '*.in' -printf '%f\n' | sed 's/\.in$//' | sort)
else
  profiles=("$@")
fi
for profile in "${profiles[@]}"; do
  [[ "$profile" =~ ^[a-z][a-z0-9_-]*$ ]] || { echo 'Invalid profile' >&2; exit 1; }
  version="$(quant_python_version "$profile")"
  "$uv_bin" python install "$version" --no-bin
  "$uv_bin" pip compile "requirements/$profile.in" \
    --python-version "$version" --python-platform x86_64-unknown-linux-gnu \
    --generate-hashes --emit-index-url --no-annotate --no-header \
    --torch-backend cpu --quiet --output-file "requirements/$profile.lock"
  echo "Locked profile: $profile (Python $version, Linux x86_64)"
done
