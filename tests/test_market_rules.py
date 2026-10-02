import pytest

from quant_cloud.config import load_config
from quant_cloud.engine import Broker


def bar(date="2024-01-02", price=10.0, **changes):
    values = {
        "date": date,
        "symbol": "TEST.SH",
        "open": price,
        "close": price,
        "upper_limit": 12.0,
        "lower_limit": 8.0,
        "suspended": False,
    }
    values.update(changes)
    return values


def broker():
    config = load_config()
    config["account"]["initial_cash"] = 10_000.0
    return Broker(config)


def test_t_plus_one_blocks_same_day_sale_and_survives_checkpoint():
    account = broker()
    assert account.submit("TEST.SH", "buy", 100, bar())["status"] == "filled"
    checkpoint = Broker(account.config, state=account.state())
    rejected = checkpoint.submit("TEST.SH", "sell", 100, bar())
    assert rejected["reason"] == "t_plus_one_or_insufficient_shares"
    assert checkpoint.shares("TEST.SH") == 100
    assert (
        checkpoint.submit("TEST.SH", "sell", 100, bar(date="2024-01-03"))["status"]
        == "filled"
    )
    assert checkpoint.shares("TEST.SH") == 0


def test_only_prior_session_lots_can_be_sold():
    account = broker()
    account.submit("TEST.SH", "buy", 100, bar())
    account.submit("TEST.SH", "buy", 100, bar(date="2024-01-03"))
    assert account.available("TEST.SH", "2024-01-03") == 100
    assert (
        account.submit("TEST.SH", "sell", 200, bar(date="2024-01-03"))["status"]
        == "rejected"
    )
    assert (
        account.submit("TEST.SH", "sell", 100, bar(date="2024-01-03"))["status"]
        == "filled"
    )
    assert account.available("TEST.SH", "2024-01-03") == 0
    assert account.shares("TEST.SH") == 100


@pytest.mark.parametrize("quantity", [0, -100, 99, 150, 100.5])
def test_invalid_round_lot_changes_no_cash_or_holdings(quantity):
    account = broker()
    result = account.submit("TEST.SH", "buy", quantity, bar())
    assert result["reason"] == "invalid_round_lot"
    assert account.cash == 10_000
    assert account.shares("TEST.SH") == 0


def test_commission_minimum_stamp_and_transfer_cash_accounting():
    account = broker()
    bought = account.submit("TEST.SH", "buy", 100, bar())
    assert bought["brokerage"] == 5
    assert bought["stamp"] == 0
    assert bought["transfer"] == 0.01
    assert account.cash == pytest.approx(8994.99)
    sold = account.submit("TEST.SH", "sell", 100, bar(date="2024-01-03", price=11))
    assert sold["brokerage"] == 5
    assert sold["stamp"] == 0.55
    assert sold["transfer"] == 0.01
    assert account.cash == pytest.approx(10089.43)


def test_insufficient_cash_does_not_create_a_position():
    account = broker()
    result = account.submit("TEST.SH", "buy", 1000, bar())
    assert result["reason"] == "insufficient_cash"
    assert account.cash == 10_000
    assert account.shares("TEST.SH") == 0


@pytest.mark.parametrize(
    "side,changes,reason",
    [
        ("buy", {"suspended": True}, "suspended"),
        ("sell", {"suspended": True}, "suspended"),
        ("buy", {"open": 12.0}, "upper_limit"),
        ("sell", {"open": 8.0}, "lower_limit"),
    ],
)
def test_suspensions_and_adverse_limits_reject_without_changing_cash(
    side, changes, reason
):
    account = broker()
    account.submit("TEST.SH", "buy", 100, bar())
    cash, shares = account.cash, account.shares("TEST.SH")
    result = account.submit("TEST.SH", side, 100, bar(date="2024-01-03", **changes))
    assert result["reason"] == reason
    assert account.cash == cash
    assert account.shares("TEST.SH") == shares


def test_slippage_may_not_cross_supplied_price_limits():
    account = broker()
    account.config["fees"]["slippage_bps"] = 100
    result = account.submit("TEST.SH", "buy", 100, bar(price=11.99))
    assert result["reason"] == "upper_limit"
    assert account.shares("TEST.SH") == 0


def test_live_mode_is_rejected():
    config = load_config()
    config["execution_mode"] = "live"
    with pytest.raises(ValueError, match="no live-order adapter"):
        Broker(config)
