"""Cash-based long-only simulator with explicit simplified A-share rules."""

from dataclasses import dataclass
from math import floor

import numpy as np
import pandas as pd

from .config import validate_config

ORDER_COLUMNS = [
    "date",
    "symbol",
    "side",
    "quantity",
    "status",
    "reason",
    "price",
    "notional",
    "brokerage",
    "stamp",
    "transfer",
    "fee",
    "cash_after",
]
EQUITY_COLUMNS = ["date", "cash", "market_value", "equity", "holdings"]


@dataclass
class Lot:
    acquired: str
    quantity: int


class Broker:
    def __init__(self, config, state=None):
        validate_config(config)
        self.config = config
        self.cash = float(config["account"]["initial_cash"])
        self.positions = {}
        self.marks = {}
        self.orders = []
        if state:
            self.cash = float(state["cash"])
            self.marks = {key: float(value) for key, value in state["marks"].items()}
            self.positions = {
                key: [Lot(**lot) for lot in lots]
                for key, lots in state["positions"].items()
            }

    def shares(self, symbol):
        return sum(lot.quantity for lot in self.positions.get(symbol, []))

    def available(self, symbol, date):
        return sum(
            lot.quantity
            for lot in self.positions.get(symbol, [])
            if lot.acquired < date
        )

    def fees(self, side, quantity, price):
        notional = quantity * price
        rates = self.config["fees"]
        brokerage = round(
            max(rates["minimum_brokerage"], notional * rates["brokerage_rate"]), 2
        )
        stamp = round(notional * rates["sell_stamp_rate"], 2) if side == "sell" else 0.0
        transfer = round(notional * rates["transfer_rate"], 2)
        return brokerage, stamp, transfer

    def _price(self, side, bar):
        factor = (
            1
            + (1 if side == "buy" else -1) * self.config["fees"]["slippage_bps"] / 10000
        )
        return round(float(bar["open"]) * factor, 2)

    def submit(self, symbol, side, quantity, bar):
        date = str(bar["date"])
        if isinstance(quantity, np.integer):
            quantity = int(quantity)
        order = {
            key: 0.0
            for key in ["price", "notional", "brokerage", "stamp", "transfer", "fee"]
        }
        order.update(
            date=date,
            symbol=symbol,
            side=side,
            quantity=quantity,
            status="rejected",
            reason="",
            cash_after=self.cash,
        )
        reason = ""
        if side not in {"buy", "sell"}:
            reason = "unsupported_side"
        elif (
            not isinstance(quantity, (int, np.integer))
            or quantity <= 0
            or quantity % self.config["market"]["round_lot"]
        ):
            reason = "invalid_round_lot"
        elif bool(bar["suspended"]):
            reason = "suspended"
        else:
            price = self._price(side, bar)
            order["price"] = price
            if side == "buy" and (
                float(bar["open"]) >= float(bar["upper_limit"]) - 1e-8
                or price > float(bar["upper_limit"]) + 1e-8
            ):
                reason = "upper_limit"
            elif side == "sell" and (
                float(bar["open"]) <= float(bar["lower_limit"]) + 1e-8
                or price < float(bar["lower_limit"]) - 1e-8
            ):
                reason = "lower_limit"
            elif side == "sell" and self.available(symbol, date) < quantity:
                reason = "t_plus_one_or_insufficient_shares"
            else:
                brokerage, stamp, transfer = self.fees(side, quantity, price)
                fee = round(brokerage + stamp + transfer, 2)
                notional = round(quantity * price, 2)
                if side == "buy" and notional + fee > self.cash + 1e-8:
                    reason = "insufficient_cash"
                else:
                    if side == "buy":
                        self.cash = round(self.cash - notional - fee, 2)
                        self.positions.setdefault(symbol, []).append(
                            Lot(date, int(quantity))
                        )
                    else:
                        self.cash = round(self.cash + notional - fee, 2)
                        remaining = quantity
                        for lot in self.positions[symbol]:
                            if lot.acquired < date:
                                sold = min(lot.quantity, remaining)
                                lot.quantity -= sold
                                remaining -= sold
                        self.positions[symbol] = [
                            lot for lot in self.positions[symbol] if lot.quantity
                        ]
                    order.update(
                        status="filled",
                        price=price,
                        notional=notional,
                        brokerage=brokerage,
                        stamp=stamp,
                        transfer=transfer,
                        fee=fee,
                        cash_after=self.cash,
                    )
        order["reason"] = reason
        self.orders.append(order)
        return order

    def equity(self):
        return self.cash + sum(
            self.shares(symbol) * self.marks[symbol]
            for symbol in self.positions
            if self.shares(symbol)
        )

    def rebalance(self, bars, weights):
        rows = {row["symbol"]: row for row in bars.to_dict("records")}
        date = str(bars.iloc[0]["date"])
        for symbol, bar in rows.items():
            self.marks[symbol] = float(bar["open"])
        opening_equity = self.equity()
        lot_size = self.config["market"]["round_lot"]
        targets = {
            symbol: floor(
                max(float(weights.get(symbol, 0)), 0)
                * opening_equity
                / float(bar["open"])
                / lot_size
            )
            * lot_size
            for symbol, bar in rows.items()
        }
        for symbol in sorted(rows):
            difference = self.shares(symbol) - targets[symbol]
            if difference > 0:
                self.submit(symbol, "sell", int(difference), rows[symbol])
        for symbol in sorted(rows):
            quantity = targets[symbol] - self.shares(symbol)
            if quantity <= 0:
                continue
            price = self._price("buy", rows[symbol])
            quantity = min(
                quantity, floor(max(self.cash, 0) / price / lot_size) * lot_size
            )
            # Include the minimum brokerage in affordability; never use leverage.
            while quantity > 0:
                fees = sum(self.fees("buy", quantity, price))
                if quantity * price + fees <= self.cash + 1e-8:
                    break
                quantity -= lot_size
            if quantity > 0:
                self.submit(symbol, "buy", int(quantity), rows[symbol])
        for symbol, bar in rows.items():
            self.marks[symbol] = float(bar["close"])
        value = self.equity()
        if self.cash < -1e-8:
            raise ArithmeticError("Cash account became negative")
        return {
            "date": date,
            "cash": self.cash,
            "market_value": value - self.cash,
            "equity": value,
            "holdings": sum(self.shares(symbol) > 0 for symbol in self.positions),
        }

    def state(self):
        return {
            "cash": self.cash,
            "marks": self.marks,
            "positions": {
                symbol: [
                    {"acquired": lot.acquired, "quantity": lot.quantity} for lot in lots
                ]
                for symbol, lots in self.positions.items()
            },
        }


def metrics(equity, orders, initial_cash):
    values = equity["equity"].to_numpy(dtype=float)
    curve = np.concatenate([[float(initial_cash)], values])
    returns = curve[1:] / curve[:-1] - 1
    volatility = float(returns.std(ddof=1)) if len(returns) > 1 else 0.0
    maximum_drawdown = float((curve / np.maximum.accumulate(curve) - 1).min())
    total_return = float(curve[-1] / curve[0] - 1)
    filled = orders.loc[orders["status"] == "filled"]
    return {
        "initial_cash": float(initial_cash),
        "final_equity": float(curve[-1]),
        "total_return": total_return,
        "annualized_return": float((curve[-1] / curve[0]) ** (252 / len(returns)) - 1)
        if len(returns)
        else 0.0,
        "annualized_volatility": volatility * np.sqrt(252),
        "sharpe_zero_risk_free": float(returns.mean() / volatility * np.sqrt(252))
        if volatility
        else 0.0,
        "maximum_drawdown": maximum_drawdown,
        "filled_orders": len(filled),
        "rejected_orders": int((orders["status"] == "rejected").sum()),
        "total_fees": float(filled["fee"].sum()),
        "sessions": len(equity),
        "annualization_sessions": 252,
        "note": "Illustrative metrics; synthetic results are not evidence of profitability. Fees are configurable assumptions, not a claim about current broker/tax rates.",
    }


def run_backtest(prices, weights, config, start=None, end=None):
    broker = Broker(config)
    equity_rows = []
    for date, bars in prices.groupby("date", sort=True):
        if (start and date < start) or (end and date > end):
            continue
        if date not in weights.index:
            raise ValueError(f"Missing past-only weights for {date}")
        equity_rows.append(broker.rebalance(bars, weights.loc[date]))
    if not equity_rows:
        raise ValueError("The requested evaluation range contains no dates")
    equity = pd.DataFrame(equity_rows, columns=EQUITY_COLUMNS)
    orders = pd.DataFrame(broker.orders, columns=ORDER_COLUMNS)
    trades = orders.loc[orders["status"] == "filled"].reset_index(drop=True)
    return {
        "equity": equity,
        "orders": orders,
        "trades": trades,
        "metrics": metrics(equity, orders, config["account"]["initial_cash"]),
        "state": broker.state(),
    }
