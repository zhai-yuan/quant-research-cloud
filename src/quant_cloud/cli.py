"""Run a deterministic offline research-to-paper demonstration."""

import argparse
import importlib
import json
import platform
import sys
from pathlib import Path


def write_json(path, data):
    Path(path).write_text(
        json.dumps(data, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def save_chart(equity, initial_cash, path):
    import matplotlib
    import pandas as pd

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    figure, axis = plt.subplots(figsize=(10, 4.5))
    axis.plot(
        pd.to_datetime(equity["date"]), equity["equity"] / initial_cash, linewidth=1.5
    )
    axis.axhline(1, color="gray", linestyle="--", linewidth=0.8)
    axis.set(
        title="SYNTHETIC A-share demonstration: chronological holdout",
        ylabel="Marked equity / initial cash",
        xlabel="Synthetic business date",
    )
    axis.grid(alpha=0.2)
    figure.tight_layout()
    figure.savefig(path, dpi=150)
    plt.close(figure)


def demo(args):
    import pandas as pd
    import yaml

    from .config import load_config
    from .data import dataset_summary, synthetic_prices
    from .engine import run_backtest
    from .paper import run_paper
    from .strategy import momentum_weights, signal_records

    config = load_config(args.config)
    output = Path(args.output)
    for name in ["data", "research", "backtest", "paper"]:
        (output / name).mkdir(parents=True, exist_ok=True)
    # Save the declared question and evaluation plan before generating results.
    hypothesis = {
        "id": "synthetic-ashare-momentum-demo",
        "status": "demonstration_only",
        "hypothesis": "Positive trailing relative momentum may persist into the next session among liquid A-share stocks",
        "scope": "Synthetic daily main-board-like stock panel only",
        "observable_inputs": "Prior-session closes and the next session's executable opening prices/limits",
        "signal": "Choose up to top_k positive trailing-return assets; equal weights; residual cash when no positive signal",
        "evaluation": "Choose a lookback on training net-of-cost Sharpe, freeze it, evaluate a chronological holdout",
        "research_acceptance": "On genuine point-in-time data require robust net-of-cost results across untouched out-of-sample windows and realistic liquidity/capacity tests; this synthetic run cannot accept or reject an investment thesis",
        "config": config,
    }
    (output / "hypothesis.yaml").write_text(
        yaml.safe_dump(hypothesis, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    prices = synthetic_prices(seed=args.seed, days=args.days, symbols=args.symbols)
    dates = sorted(prices["date"].unique())
    split = int(len(dates) * config["research"]["train_fraction"])
    common_start = max(config["research"]["lookbacks"]) + 1
    if split <= common_start + 5 or split >= len(dates) - 5:
        raise ValueError(
            "Too few dates for warmup, training and holdout; increase --days or revise train_fraction/lookbacks"
        )
    training_end = dates[split - 1]
    holdout_start = dates[split]
    train_prices = prices.loc[prices["date"] <= training_end].copy()
    candidates = []
    for lookback in config["research"]["lookbacks"]:
        train_weights = momentum_weights(
            train_prices, lookback, config["research"]["top_k"]
        )
        result = run_backtest(
            train_prices, train_weights, config, start=dates[common_start]
        )
        candidates.append(
            {
                "lookback": lookback,
                "training_start": dates[common_start],
                "training_end": training_end,
                **result["metrics"],
            }
        )
    selection = (
        pd.DataFrame(candidates)
        .sort_values(
            ["sharpe_zero_risk_free", "total_return", "lookback"],
            ascending=[False, False, True],
        )
        .reset_index(drop=True)
    )
    chosen = int(selection.iloc[0]["lookback"])
    weights = momentum_weights(prices, chosen, config["research"]["top_k"])
    result = run_backtest(prices, weights, config, start=holdout_start)
    paper = run_paper(
        prices, weights, config, output / "paper" / "paper.sqlite", start=holdout_start
    )
    prices.to_csv(output / "data" / "synthetic_prices.csv", index=False)
    write_json(
        output / "data" / "summary.json", dataset_summary(prices, synthetic=True)
    )
    selection.to_csv(output / "research" / "parameter_selection.csv", index=False)
    signals = signal_records(weights)
    signals.loc[signals["execution_date"] >= holdout_start].to_csv(
        output / "research" / "holdout_signals.csv", index=False
    )
    validation = {
        "method": "Single chronological train/holdout split with common training warmup",
        "training_start": dates[common_start],
        "training_end": training_end,
        "holdout_start": holdout_start,
        "holdout_end": dates[-1],
        "selected_lookback": chosen,
        "selection_criterion": "Training net-of-cost Sharpe, then total return, then shorter lookback",
        "top_k": config["research"]["top_k"],
        "lookahead_control": "Open-of-day weights use at most the prior session's close; lookback selection sees training prices only",
        "multiple_testing": "Candidate lookbacks are tried on the training sample. Repeated strategy selection using holdout results invalidates this holdout.",
        "limitations": [
            "All prices and instruments are synthetic; weekday dates are not an exchange holiday calendar",
            "Fixed universe has no historical listing/delisting or survivorship model",
            "No corporate actions, intraday order book, queue priority, market impact or partial liquidity fills",
            "Opening fills assume requested volume can fill when the opening price is away from the adverse limit; volume is not modeled",
            "Buy at the upper limit and sell at the lower limit are conservatively rejected; suspension rejects both sides",
            "Only 100-share lots and T+1 stock sale availability are modeled; board/security-specific rules require accurate supplied inputs and adapter changes",
            "No real broker simulation account or live execution adapter is connected",
            "One illustrative hypothesis and one holdout do not implement a complete production research workflow or demonstrate profitability",
        ],
    }
    write_json(output / "research" / "validation.json", validation)
    for name in ["trades", "orders", "equity"]:
        result[name].to_csv(output / "backtest" / f"{name}.csv", index=False)
    write_json(output / "backtest" / "metrics.json", result["metrics"])
    save_chart(
        result["equity"],
        config["account"]["initial_cash"],
        output / "backtest" / "equity.png",
    )
    paper["orders"].to_csv(output / "paper" / "orders.csv", index=False)
    paper["equity"].to_csv(output / "paper" / "equity.csv", index=False)
    write_json(output / "paper" / "summary.json", paper["summary"])
    write_json(
        output / "manifest.json",
        {
            "synthetic": True,
            "execution_mode": "local-paper",
            "timezone": config["timezone"],
            "seed": args.seed,
            "dataset": dataset_summary(prices, synthetic=True),
            "selected_lookback": chosen,
            "backtest_final_equity": result["metrics"]["final_equity"],
            "paper_final_equity": paper["summary"]["metrics"]["final_equity"],
            "external_orders_sent": 0,
            "fee_assumption": "All fees are illustrative, configurable example inputs; verify your broker and current rules before genuine-data research",
        },
    )
    print(
        json.dumps(
            {
                "output": str(output.resolve()),
                "synthetic": True,
                "selected_lookback": chosen,
                "holdout_metrics": result["metrics"],
                "paper_run_id": paper["summary"]["run_id"],
                "external_orders_sent": 0,
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


def paper_command(args):
    from .config import load_config
    from .data import read_prices
    from .paper import run_paper
    from .strategy import momentum_weights

    config = load_config(args.config)
    prices = read_prices(args.data)
    weights = momentum_weights(prices, args.lookback, config["research"]["top_k"])
    result = run_paper(
        prices,
        weights,
        config,
        args.database,
        start=args.start,
        end=args.end,
        mode=args.mode,
    )
    print(json.dumps(result["summary"], indent=2, ensure_ascii=False))
    return 0


def doctor(_args):
    modules = ["numpy", "pandas", "yaml", "matplotlib", "sqlite3"]
    report = {
        "python": platform.python_version(),
        "minimum_python": "3.11",
        "platform": platform.platform(),
        "dependencies": {},
    }
    failed = sys.version_info < (3, 11)
    for name in modules:
        try:
            module = importlib.import_module(name)
            report["dependencies"][name] = {
                "ok": True,
                "version": getattr(module, "__version__", "stdlib"),
            }
        except ImportError as error:
            failed = True
            report["dependencies"][name] = {"ok": False, "error": str(error)}
    report["ok"] = not failed
    print(json.dumps(report, indent=2))
    return int(failed)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="A-share research scaffold: synthetic demo and local paper accounting only"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    demo_parser = subparsers.add_parser(
        "demo",
        help="Offline seeded synthetic hypothesis -> training -> holdout -> paper run",
    )
    demo_parser.add_argument("--output", default="artifacts/demo")
    demo_parser.add_argument("--config")
    demo_parser.add_argument("--seed", type=int, default=42)
    demo_parser.add_argument("--days", type=int, default=220)
    demo_parser.add_argument("--symbols", type=int, default=6)
    demo_parser.set_defaults(func=demo)
    paper_parser = subparsers.add_parser(
        "paper",
        help="Restartable SQLite simulation using supplied daily data; no external orders",
    )
    paper_parser.add_argument("--data", required=True)
    paper_parser.add_argument("--database", required=True)
    paper_parser.add_argument("--config")
    paper_parser.add_argument("--lookback", type=int, default=20)
    paper_parser.add_argument("--start")
    paper_parser.add_argument("--end")
    paper_parser.add_argument("--mode", default="local-paper")
    paper_parser.set_defaults(func=paper_command)
    doctor_parser = subparsers.add_parser(
        "doctor", help="Report the small offline demo's dependencies"
    )
    doctor_parser.set_defaults(func=doctor)
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except (ValueError, TypeError, OSError) as error:
        parser.exit(2, f"error: {error}\n")


if __name__ == "__main__":
    raise SystemExit(main())
