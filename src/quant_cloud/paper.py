"""Restartable local paper account. No network or brokerage order calls."""

import hashlib
import json
import sqlite3
from pathlib import Path

import pandas as pd

from .config import validate_config
from .data import dataset_hash
from .engine import EQUITY_COLUMNS, ORDER_COLUMNS, Broker, metrics


def run_paper(
    prices, weights, config, database, start=None, end=None, mode="local-paper"
):
    if mode != "local-paper":
        raise ValueError(
            "Only local-paper is supported; external and live orders are unavailable"
        )
    validate_config(config)
    identity = {
        "dataset_sha256": dataset_hash(prices),
        "weights_sha256": hashlib.sha256(
            weights.to_csv(float_format="%.12g").encode()
        ).hexdigest(),
        "config": config,
        "start": start,
        "end": end,
        "mode": mode,
    }
    serialized = json.dumps(identity, sort_keys=True, separators=(",", ":"))
    run_id = hashlib.sha256(serialized.encode()).hexdigest()[:24]
    path = Path(database)
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, timeout=30)
    try:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.executescript("""
            CREATE TABLE IF NOT EXISTS runs (
                run_id TEXT PRIMARY KEY,
                identity_json TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS sessions (
                run_id TEXT NOT NULL REFERENCES runs(run_id),
                date TEXT NOT NULL,
                cash REAL NOT NULL,
                market_value REAL NOT NULL,
                equity REAL NOT NULL,
                holdings INTEGER NOT NULL,
                state_json TEXT NOT NULL,
                PRIMARY KEY (run_id, date)
            );
            CREATE TABLE IF NOT EXISTS events (
                run_id TEXT NOT NULL REFERENCES runs(run_id),
                date TEXT NOT NULL,
                sequence INTEGER NOT NULL,
                event_type TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                PRIMARY KEY (run_id, date, sequence)
            );
        """)
        with connection:
            connection.execute(
                "INSERT OR IGNORE INTO runs VALUES (?, ?)", (run_id, serialized)
            )
        checkpoint = connection.execute(
            "SELECT date, state_json FROM sessions WHERE run_id = ? ORDER BY date DESC LIMIT 1",
            (run_id,),
        ).fetchone()
        last_date, state = (
            (checkpoint[0], json.loads(checkpoint[1])) if checkpoint else (None, None)
        )
        broker = Broker(config, state=state)
        newly_processed = 0
        for date, bars in prices.groupby("date", sort=True):
            if (
                (start and date < start)
                or (end and date > end)
                or (last_date and date <= last_date)
            ):
                continue
            if date not in weights.index:
                raise ValueError(f"Missing past-only weights for {date}")
            beginning = len(broker.orders)
            equity = broker.rebalance(bars, weights.loc[date])
            day_orders = broker.orders[beginning:]
            # Orders, valuation and the complete account checkpoint commit together.
            with connection:
                connection.execute(
                    "INSERT INTO sessions VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (
                        run_id,
                        date,
                        equity["cash"],
                        equity["market_value"],
                        equity["equity"],
                        equity["holdings"],
                        json.dumps(broker.state(), sort_keys=True),
                    ),
                )
                for index, order in enumerate(day_orders):
                    connection.execute(
                        "INSERT INTO events VALUES (?, ?, ?, ?, ?)",
                        (
                            run_id,
                            date,
                            index,
                            "order",
                            json.dumps(order, sort_keys=True),
                        ),
                    )
                connection.execute(
                    "INSERT INTO events VALUES (?, ?, ?, ?, ?)",
                    (
                        run_id,
                        date,
                        len(day_orders),
                        "valuation",
                        json.dumps(equity, sort_keys=True),
                    ),
                )
            newly_processed += 1
        equity = pd.read_sql_query(
            "SELECT date, cash, market_value, equity, holdings FROM sessions WHERE run_id = ? ORDER BY date",
            connection,
            params=(run_id,),
        )
        if equity.empty:
            raise ValueError("The requested paper range contains no dates")
        payloads = connection.execute(
            "SELECT payload_json FROM events WHERE run_id = ? AND event_type = 'order' ORDER BY date, sequence",
            (run_id,),
        ).fetchall()
        orders = pd.DataFrame(
            [json.loads(row[0]) for row in payloads], columns=ORDER_COLUMNS
        )
        return {
            "equity": equity.reindex(columns=EQUITY_COLUMNS),
            "orders": orders,
            "summary": {
                "run_id": run_id,
                "execution_mode": mode,
                "external_orders_sent": 0,
                "newly_processed_sessions": newly_processed,
                "completed_sessions": len(equity),
                "checkpoint_date": equity.iloc[-1]["date"],
                "metrics": metrics(equity, orders, config["account"]["initial_cash"]),
                "persistence": "SQLite daily transactions contain order events, valuation events and complete cash/lot checkpoints. Identical reruns resume without duplicate orders; changed inputs create a separate run.",
            },
        }
    finally:
        connection.close()
