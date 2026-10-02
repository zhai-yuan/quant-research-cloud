"""Install the pinned uv wheel into this repository, verifying its PyPI SHA256."""

import hashlib
import io
import json
import platform
import subprocess
import urllib.request
import zipfile
from pathlib import Path

UV_VERSION = "0.12.22"
ROOT = Path(__file__).resolve().parents[1]


def main():
    if platform.system() != "Linux" or platform.machine() != "x86_64":
        raise SystemExit("The supplied locks target Linux x86_64. Re-lock for another platform.")
    target = ROOT / ".tools/uv"
    if target.exists():
        version = subprocess.check_output([str(target), "--version"], text=True).split()[1]
        if version == UV_VERSION:
            print(target)
            return
    with urllib.request.urlopen(
        f"https://pypi.org/pypi/uv/{UV_VERSION}/json", timeout=60
    ) as response:
        metadata = json.load(response)
    wheel = next(
        item
        for item in metadata["urls"]
        if "manylinux" in item["filename"] and "x86_64" in item["filename"]
    )
    with urllib.request.urlopen(wheel["url"], timeout=180) as response:
        raw = response.read()
    if hashlib.sha256(raw).hexdigest() != wheel["digests"]["sha256"]:
        raise SystemExit("uv wheel checksum mismatch")
    archive = zipfile.ZipFile(io.BytesIO(raw))
    entry = next(name for name in archive.namelist() if name.endswith("/uv"))
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(".tmp")
    temporary.write_bytes(archive.read(entry))
    temporary.chmod(0o755)
    temporary.replace(target)
    print(target)


if __name__ == "__main__":
    main()
