"""Seeded synthetic prices; all assets and dates are demonstration inputs."""

import hashlib
from pathlib import Path

import numpy as np
import pandas as pd

REQUIRED_COLUMNS = {
    "date",
    "symbol",
    "open",
    "close",
    "upper_limit",
    "lower_limit",
    "suspended",
}


def synthetic_prices(seed=42, days=220, symbols=6):
    if days < 90 or symbols < 2:
        raise ValueError("The demo needs at least 90 dates and 2 synthetic symbols")
    generator = np.random.default_rng(seed)
    dates = pd.bdate_range("2023-01-03", periods=days)
    previous = generator.uniform(8, 35, symbols)
    trend = np.zeros(symbols)
    rows = []
    for day_index, date in enumerate(dates):
        common = generator.normal(0.00025, 0.009)
        trend = 0.85 * trend + generator.normal(0.0002, 0.0025, symbols)
        for stock_index in range(symbols):
            prior = float(previous[stock_index])
            upper = round(prior * 1.10, 2)
            lower = round(prior * 0.90, 2)
            suspended = (day_index + stock_index * 7) % 67 == 24
            open_price = round(
                np.clip(prior * (1 + generator.normal(0, 0.003)), lower, upper), 2
            )
            close_price = round(
                np.clip(
                    prior
                    * (1 + common + trend[stock_index] + generator.normal(0, 0.014)),
                    lower,
                    upper,
                ),
                2,
            )
            if (day_index + stock_index * 13) % 71 == 32:
                open_price = close_price = upper
            if (day_index + stock_index * 17) % 79 == 41:
                open_price = close_price = lower
            if suspended:
                open_price = close_price = prior
            rows.append(
                {
                    "date": date.strftime("%Y-%m-%d"),
                    "symbol": f"SYNTH{stock_index + 1:03d}.SH",
                    "open": open_price,
                    "close": close_price,
                    "previous_close": prior,
                    "upper_limit": upper,
                    "lower_limit": lower,
                    "suspended": suspended,
                    "volume": 0
                    if suspended
                    else int(generator.integers(500_000, 5_000_000)),
                }
            )
            previous[stock_index] = close_price
    return validate_prices(pd.DataFrame(rows))


def validate_prices(prices):
    missing = REQUIRED_COLUMNS - set(prices.columns)
    if missing:
        raise ValueError(f"Price data is missing columns: {sorted(missing)}")
    frame = prices.copy()
    if (
        frame["symbol"].isna().any()
        or not frame["symbol"]
        .map(lambda value: isinstance(value, str) and bool(value.strip()))
        .all()
    ):
        raise ValueError("Symbols must be nonempty strings")
    frame["date"] = pd.to_datetime(frame["date"], errors="raise").dt.strftime(
        "%Y-%m-%d"
    )
    if frame["date"].isna().any():
        raise ValueError("Dates must be nonmissing trading sessions")
    if frame.empty or frame.duplicated(["date", "symbol"]).any():
        raise ValueError("Price data must be nonempty with unique date/symbol pairs")
    numeric = ["open", "close", "upper_limit", "lower_limit"]
    for column in numeric:
        frame[column] = pd.to_numeric(frame[column], errors="raise")
    if (
        not np.isfinite(frame[numeric].to_numpy()).all()
        or (frame[numeric] <= 0).any().any()
    ):
        raise ValueError("Prices and price limits must be finite and positive")
    if (
        (frame["lower_limit"] > frame["upper_limit"])
        | (frame["open"] < frame["lower_limit"] - 1e-8)
        | (frame["open"] > frame["upper_limit"] + 1e-8)
        | (frame["close"] < frame["lower_limit"] - 1e-8)
        | (frame["close"] > frame["upper_limit"] + 1e-8)
    ).any():
        raise ValueError(
            "Open/close prices must be within the supplied daily price limits"
        )
    if frame["suspended"].dtype != bool:
        normalized = (
            frame["suspended"]
            .astype(str)
            .str.lower()
            .map({"true": True, "false": False, "1": True, "0": False})
        )
        if normalized.isna().any():
            raise ValueError("suspended must contain boolean values")
        frame["suspended"] = normalized.astype(bool)
    universe = set(frame["symbol"])
    if any(set(group["symbol"]) != universe for _, group in frame.groupby("date")):
        raise ValueError(
            "The example requires a complete daily panel; fill missing rows with explicit suspension/mark data"
        )
    return frame.sort_values(["date", "symbol"]).reset_index(drop=True)


def read_prices(path):
    return validate_prices(pd.read_csv(Path(path)))


def dataset_hash(prices):
    return hashlib.sha256(
        prices.to_csv(index=False, float_format="%.10g").encode()
    ).hexdigest()


def dataset_summary(prices, synthetic=False):
    return {
        "synthetic": synthetic,
        "rows": len(prices),
        "sessions": int(prices["date"].nunique()),
        "symbols": sorted(prices["symbol"].unique().tolist()),
        "first_date": prices["date"].min(),
        "last_date": prices["date"].max(),
        "suspended_rows": int(prices["suspended"].sum()),
        "sha256": dataset_hash(prices),
        "date_convention": "Synthetic business weekdays; not a validated mainland exchange calendar"
        if synthetic
        else "Supplied trading sessions; caller must validate exchange calendar",
        "price_convention": "Unadjusted synthetic prices with explicitly supplied daily limit prices"
        if synthetic
        else "Caller supplies tradeable raw prices and point-in-time daily limits; corporate actions are not handled",
    }
