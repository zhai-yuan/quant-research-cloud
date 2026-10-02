"""Past-only cross-sectional momentum, deliberately small and auditable."""

import pandas as pd


def momentum_weights(prices, lookback=20, top_k=3):
    if not isinstance(lookback, int) or lookback < 1 or top_k < 1:
        raise ValueError("lookback and top_k must be positive integers")
    close = prices.pivot(index="date", columns="symbol", values="close").sort_index()
    # At a date's open, yesterday's close is the most recent available close.
    score = close.shift(1).divide(close.shift(lookback + 1)) - 1
    weights = pd.DataFrame(0.0, index=close.index, columns=close.columns)
    for date, scores in score.iterrows():
        # Symbol-order tie breaking is stable across runs and Python versions.
        candidates = scores.dropna().loc[lambda values: values > 0]
        winners = sorted(
            candidates.index, key=lambda symbol: (-candidates[symbol], symbol)
        )[:top_k]
        if winners:
            weights.loc[date, winners] = 1 / len(winners)
    return weights


def signal_records(weights):
    records = []
    dates = list(weights.index)
    for index, date in enumerate(dates):
        for symbol, weight in weights.loc[date].items():
            records.append(
                {
                    "execution_date": date,
                    "known_through": dates[index - 1] if index else "",
                    "symbol": symbol,
                    "target_weight": float(weight),
                }
            )
    return pd.DataFrame(records)
