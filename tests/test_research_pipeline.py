import json
import sqlite3

import pandas as pd
import pytest

from quant_cloud.cli import main
from quant_cloud.config import load_config
from quant_cloud.data import synthetic_prices, validate_prices
from quant_cloud.engine import Broker, run_backtest
from quant_cloud.paper import run_paper
from quant_cloud.strategy import momentum_weights


def test_synthetic_data_are_seeded_and_explicit():
    first = synthetic_prices(seed=7, days=90, symbols=3)
    second = synthetic_prices(seed=7, days=90, symbols=3)
    pd.testing.assert_frame_equal(first, second)
    assert first["symbol"].str.startswith("SYNTH").all()
    assert first["suspended"].any()
    assert not first.equals(synthetic_prices(seed=8, days=90, symbols=3))


def test_signal_cannot_see_current_or_future_close():
    prices = synthetic_prices(seed=4, days=90, symbols=3)
    original = momentum_weights(prices, 10, 2)
    cutoff = sorted(prices["date"].unique())[55]
    changed = prices.copy()
    changed.loc[changed["date"] >= cutoff, "close"] *= 7
    modified = momentum_weights(changed, 10, 2)
    pd.testing.assert_frame_equal(original.loc[:cutoff], modified.loc[:cutoff])


def test_signal_is_next_session_after_observation():
    rows = []
    for date, a, b in [
        ("2024-01-02", 10, 10),
        ("2024-01-03", 11, 9),
        ("2024-01-04", 5, 20),
    ]:
        rows.extend(
            [
                {"date": date, "symbol": "A", "close": a},
                {"date": date, "symbol": "B", "close": b},
            ]
        )
    weights = momentum_weights(pd.DataFrame(rows), lookback=1, top_k=1)
    assert weights.loc["2024-01-03"].sum() == 0
    assert weights.loc["2024-01-04", "A"] == 1
    assert weights.loc["2024-01-04", "B"] == 0


def test_opening_order_sizing_cannot_see_current_close():
    prices = pd.DataFrame(
        [
            {
                "date": "2024-01-02",
                "symbol": "TEST.SH",
                "open": 10.0,
                "close": 10.0,
                "upper_limit": 30.0,
                "lower_limit": 5.0,
                "suspended": False,
            }
        ]
    )
    weights = pd.DataFrame({"TEST.SH": [1.0]}, index=["2024-01-02"])
    config = load_config()
    unchanged = run_backtest(prices, weights, config)
    modified = run_backtest(prices.assign(close=20.0), weights, config)
    pd.testing.assert_frame_equal(unchanged["orders"], modified["orders"])
    assert modified["metrics"]["final_equity"] > unchanged["metrics"]["final_equity"]


@pytest.mark.parametrize(
    "mutation,error",
    [
        (lambda frame: pd.concat([frame, frame.iloc[[0]]]), "unique"),
        (lambda frame: frame.iloc[1:], "complete daily panel"),
        (lambda frame: frame.assign(open=-1), "positive"),
        (lambda frame: frame.assign(suspended="unknown"), "boolean"),
        (lambda frame: frame.assign(close=frame.upper_limit + 1), "within"),
    ],
)
def test_malformed_market_data_are_rejected(mutation, error):
    with pytest.raises(ValueError, match=error):
        validate_prices(mutation(synthetic_prices(days=90, symbols=2)))


def test_backtest_cash_lots_and_paper_reconcile(tmp_path):
    prices = synthetic_prices(days=90, symbols=3)
    config = load_config()
    weights = momentum_weights(prices, 10, 2)
    start = sorted(prices["date"].unique())[45]
    backtest = run_backtest(prices, weights, config, start=start)
    assert (backtest["equity"]["cash"] >= 0).all()
    assert (backtest["trades"]["quantity"] % 100 == 0).all()
    assert backtest["metrics"]["total_fees"] > 0
    database = tmp_path / "paper.sqlite"
    paper = run_paper(prices, weights, config, database, start=start)
    pd.testing.assert_frame_equal(
        backtest["equity"], paper["equity"], check_dtype=False
    )
    pd.testing.assert_frame_equal(
        backtest["orders"], paper["orders"], check_dtype=False
    )
    with sqlite3.connect(database) as connection:
        event_count = connection.execute("SELECT COUNT(*) FROM events").fetchone()[0]
    rerun = run_paper(prices, weights, config, database, start=start)
    assert rerun["summary"]["newly_processed_sessions"] == 0
    assert rerun["summary"]["external_orders_sent"] == 0
    with sqlite3.connect(database) as connection:
        assert (
            connection.execute("SELECT COUNT(*) FROM events").fetchone()[0]
            == event_count
        )


def test_paper_resumes_after_interruption_from_complete_daily_checkpoint(
    tmp_path, monkeypatch
):
    prices = synthetic_prices(days=90, symbols=3)
    weights = momentum_weights(prices, 10, 2)
    config = load_config()
    start = sorted(prices["date"].unique())[45]
    original = Broker.rebalance
    calls = 0

    def interrupt_after_four_days(self, bars, day_weights):
        nonlocal calls
        calls += 1
        if calls == 5:
            raise RuntimeError("simulated process interruption")
        return original(self, bars, day_weights)

    database = tmp_path / "interrupted.sqlite"
    monkeypatch.setattr(Broker, "rebalance", interrupt_after_four_days)
    with pytest.raises(RuntimeError, match="simulated process interruption"):
        run_paper(prices, weights, config, database, start=start)
    with sqlite3.connect(database) as connection:
        assert connection.execute("SELECT COUNT(*) FROM sessions").fetchone()[0] == 4
    monkeypatch.setattr(Broker, "rebalance", original)
    resumed = run_paper(prices, weights, config, database, start=start)
    reference = run_backtest(prices, weights, config, start=start)
    assert (
        resumed["summary"]["newly_processed_sessions"] == len(reference["equity"]) - 4
    )
    pd.testing.assert_frame_equal(
        reference["equity"], resumed["equity"], check_dtype=False
    )
    pd.testing.assert_frame_equal(
        reference["orders"], resumed["orders"], check_dtype=False
    )


def test_paper_live_mode_fails_without_creating_database(tmp_path):
    prices = synthetic_prices(days=90, symbols=2)
    with pytest.raises(ValueError, match="external and live orders"):
        run_paper(
            prices,
            momentum_weights(prices, 10, 2),
            load_config(),
            tmp_path / "live.sqlite",
            mode="live",
        )
    assert not (tmp_path / "live.sqlite").exists()


def test_cli_demo_creates_auditable_outputs_and_frozen_holdout(tmp_path, capsys):
    output = tmp_path / "demo"
    assert (
        main(
            [
                "demo",
                "--output",
                str(output),
                "--days",
                "90",
                "--symbols",
                "3",
                "--seed",
                "10",
            ]
        )
        == 0
    )
    capsys.readouterr()
    required = [
        "hypothesis.yaml",
        "manifest.json",
        "data/synthetic_prices.csv",
        "data/summary.json",
        "research/parameter_selection.csv",
        "research/validation.json",
        "research/holdout_signals.csv",
        "backtest/trades.csv",
        "backtest/orders.csv",
        "backtest/equity.csv",
        "backtest/metrics.json",
        "backtest/equity.png",
        "paper/paper.sqlite",
        "paper/orders.csv",
        "paper/equity.csv",
        "paper/summary.json",
    ]
    assert all((output / path).is_file() for path in required)
    manifest = json.loads((output / "manifest.json").read_text())
    validation = json.loads((output / "research/validation.json").read_text())
    assert manifest["synthetic"] is True
    assert manifest["external_orders_sent"] == 0
    assert manifest["backtest_final_equity"] == manifest["paper_final_equity"]
    assert validation["training_end"] < validation["holdout_start"]
    signals = pd.read_csv(output / "research" / "holdout_signals.csv")
    assert (signals["known_through"] < signals["execution_date"]).all()
    assert (
        main(
            [
                "demo",
                "--output",
                str(output),
                "--days",
                "90",
                "--symbols",
                "3",
                "--seed",
                "10",
            ]
        )
        == 0
    )
    paper = json.loads((output / "paper" / "summary.json").read_text())
    assert paper["newly_processed_sessions"] == 0


def test_cli_doctor(capsys):
    assert main(["doctor"]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["ok"] is True
    assert report["dependencies"]["sqlite3"]["ok"] is True
