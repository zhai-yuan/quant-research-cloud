"""Run from the repository root after installing the package."""

from quant_cloud.cli import main

if __name__ == "__main__":
    raise SystemExit(
        main(
            ["demo", "--output", "artifacts/demo", "--config", "configs/research.yaml"]
        )
    )
