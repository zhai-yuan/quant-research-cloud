#!/usr/bin/env bash
set -euo pipefail
if ! command -v apt-get >/dev/null; then
  echo 'Native packages require an Ubuntu/Debian image; use the provided Dockerfile.' >&2
  exit 1
fi
apt_cmd=(apt-get)
if [[ "$(id -u)" != 0 ]]; then
  if command -v sudo >/dev/null && sudo -n true 2>/dev/null; then
    apt_cmd=(sudo -n apt-get)
  else
    echo 'Install system packages with an administrator, then use INSTALL_SYSTEM_PACKAGES=0.' >&2
    exit 1
  fi
fi
"${apt_cmd[@]}" update
"${apt_cmd[@]}" install -y --no-install-recommends \
  ca-certificates curl git unzip build-essential pkg-config cmake ninja-build \
  gfortran libopenblas-dev liblapack-dev libgomp1 libssl-dev libffi-dev \
  libxml2-dev libxslt1-dev zlib1g-dev libbz2-dev liblzma-dev libsqlite3-dev \
  libpq-dev libcurl4-openssl-dev libhdf5-dev libgl1 libegl1 libglib2.0-0 \
  libxkbcommon0 libxkbcommon-x11-0 libxcb-cursor0 \
  libsndfile1 libzmq3-dev libboost-dev openjdk-17-jre-headless \
  graphviz fonts-noto-cjk sqlite3 ffmpeg pandoc
