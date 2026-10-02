"""Explicit, illustrative market and research configuration."""

from copy import deepcopy
from math import isfinite
from pathlib import Path

import yaml

DEFAULT_CONFIG = {
    "timezone": "Asia/Shanghai",
    "execution_mode": "local-paper",
    "account": {"initial_cash": 1_000_000.0},
    "market": {
        "round_lot": 100,
        "settlement": "T+1",
        "fill_model": "conservative_open",
    },
    "fees": {
        "brokerage_rate": 0.0003,
        "minimum_brokerage": 5.0,
        "sell_stamp_rate": 0.0005,
        "transfer_rate": 0.00001,
        "slippage_bps": 0.0,
    },
    "research": {"lookbacks": [10, 20, 40], "top_k": 3, "train_fraction": 0.65},
}


def load_config(path=None):
    config = deepcopy(DEFAULT_CONFIG)
    if path:
        with Path(path).open(encoding="utf-8") as stream:
            updates = yaml.safe_load(stream) or {}
        if not isinstance(updates, dict):
            raise ValueError("Configuration must be a YAML mapping")
        for key, value in updates.items():
            if key not in config:
                raise ValueError(f"Unknown configuration section: {key}")
            if isinstance(config[key], dict):
                if not isinstance(value, dict):
                    raise TypeError(f"Configuration section {key} must be a mapping")
                unknown = set(value) - set(config[key])
                if unknown:
                    raise ValueError(
                        f"Unknown configuration keys in {key}: {sorted(unknown)}"
                    )
                config[key].update(value)
            else:
                config[key] = value
    validate_config(config)
    return config


def validate_config(config):
    if config["execution_mode"] != "local-paper":
        raise ValueError(
            "Only execution_mode=local-paper is supported; no live-order adapter exists"
        )
    if config["market"]["round_lot"] != 100:
        raise ValueError(
            "This example models 100-share lots; other security lot rules need an adapter"
        )
    if config["market"]["settlement"] != "T+1":
        raise ValueError("This example requires settlement=T+1")
    if config["market"]["fill_model"] != "conservative_open":
        raise ValueError("Only fill_model=conservative_open is supported")
    if not 0 < config["research"]["train_fraction"] < 1:
        raise ValueError("train_fraction must be between 0 and 1")
    if (
        not isfinite(config["account"]["initial_cash"])
        or config["account"]["initial_cash"] <= 0
    ):
        raise ValueError("initial_cash must be finite and positive")
    if (
        not isinstance(config["research"]["top_k"], int)
        or config["research"]["top_k"] < 1
    ):
        raise ValueError("top_k must be a positive integer")
    if not config["research"]["lookbacks"] or any(
        not isinstance(value, int) or value < 1
        for value in config["research"]["lookbacks"]
    ):
        raise ValueError("lookbacks must be nonempty positive integers")
    if any(not isfinite(value) or value < 0 for value in config["fees"].values()):
        raise ValueError("Fees and slippage must be finite and nonnegative")
    if config["fees"]["slippage_bps"] >= 10_000:
        raise ValueError("slippage_bps must be below 10000")
