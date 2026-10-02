"""Check every declared distribution and import selected framework entry points."""

import argparse
import importlib.metadata
import json
import subprocess
import sys
from pathlib import Path

from packaging.requirements import Requirement

ROOT = Path(__file__).resolve().parents[1]
IMPORT_NAMES = {
    "numpy": "numpy",
    "pandas": "pandas",
    "pyyaml": "yaml",
    "matplotlib": "matplotlib",
    "polars": "polars",
    "pyarrow": "pyarrow",
    "duckdb": "duckdb",
    "scipy": "scipy",
    "statsmodels": "statsmodels.api",
    "scikit-learn": "sklearn",
    "akshare": "akshare",
    "baostock": "baostock",
    "tushare": "tushare",
    "rqdatac": "rqdatac",
    "ta-lib": "talib",
    "vectorbt": "vectorbt",
    "backtrader": "backtrader",
    "backtesting": "backtesting",
    "quantstats": "quantstats",
    "alphalens-reloaded": "alphalens",
    "quantlib": "QuantLib",
    "cvxpy": "cvxpy",
    "riskfolio-lib": "riskfolio",
    "rqalpha": "rqalpha",
    "pyqlib": "qlib",
    "torch": "torch",
    "tensorflow": "tensorflow",
    "nautilus-trader": "nautilus_trader",
    "zipline-reloaded": "zipline",
    "vnpy": "vnpy",
    "hftbacktest": "hftbacktest",
    "pyspark": "pyspark",
    "transformers": "transformers",
    "stable-baselines3": "stable_baselines3",
    "lightgbm": "lightgbm",
    "xgboost": "xgboost",
    "catboost": "catboost",
    "empyrical-reloaded": "empyrical",
    "tensorflow-probability": "tensorflow_probability",
    "tf-keras": "tf_keras",
    "vnpy-paperaccount": "vnpy_paperaccount",
    "gm": "gm.api",
    "gmtrade": "gmtrade.api",
    "pymc": "pymc",
    "numpyro": "numpyro",
    "jax": "jax",
}


def declared(path):
    for line in path.read_text().splitlines():
        line = line.split(" #", 1)[0].strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("-r "):
            yield from declared(path.parent / line[3:].strip())
        elif not line.startswith("-"):
            yield Requirement(line)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile")
    parser.add_argument(
        "--metadata-only",
        action="store_true",
        help="Check declared versions without repeating framework imports",
    )
    args = parser.parse_args()
    state_path = ROOT / ".environment-status.json"
    state = json.loads(state_path.read_text()) if state_path.exists() else {}
    profile = args.profile or ("minimal" if state.get("requested_mode") == "minimal" else "main")
    requirements = list(declared(ROOT / "requirements" / f"{profile}.in"))
    versions, failures = {}, []
    for requirement in requirements:
        if requirement.marker and not requirement.marker.evaluate():
            continue
        name = requirement.name.lower().replace("_", "-")
        try:
            version = importlib.metadata.version(requirement.name)
            versions[name] = version
            if version not in requirement.specifier:
                failures.append(f"{name}: {version} does not satisfy {requirement.specifier}")
            module = IMPORT_NAMES.get(name)
            if module and not args.metadata_only:
                result = subprocess.run(
                    [
                        sys.executable,
                        "-c",
                        f"import importlib; importlib.import_module({module!r})",
                    ],
                    cwd=ROOT,
                    capture_output=True,
                    text=True,
                    timeout=90,
                    check=False,
                )
                if result.returncode:
                    failures.append(f"{name}: import failed: {result.stderr[-1600:]}")
        except (
            importlib.metadata.PackageNotFoundError,
            subprocess.TimeoutExpired,
        ) as exc:
            failures.append(f"{name}: {type(exc).__name__}")
    report = {
        "profile": profile,
        "python": sys.version.split()[0],
        "declared_distributions": len(versions),
        "versions": versions,
        "failures": failures,
        "ready": not failures,
        "framework_imports_checked": not args.metadata_only,
        "scope": "Local package health only; external data entitlements and gateways are untested.",
    }
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return int(bool(failures))


if __name__ == "__main__":
    raise SystemExit(main())
