# fake data with a known effect planted in it, to check the code finds it
# --effect is the extra return per unit of signal, --event-jump is the jump on award days
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import config
from build_signal import monthly_weights, rig_momentum


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--effect", type=float, default=0.5)
    parser.add_argument("--event-jump", type=float, default=0.03)
    parser.add_argument("--seed", type=int, default=1)
    args = parser.parse_args()
    rng = np.random.default_rng(args.seed)

    months = pd.date_range("2007-01-31", "2026-10-31", freq="ME")
    days = pd.bdate_range("2006-01-02", "2026-10-30")

    # rig count that wanders, with a jump in January 2024 like the real one
    rig = 250 * np.exp(np.cumsum(rng.normal(0, 0.02, len(months))))
    rig[months >= "2024-01-31"] *= 1.15
    rigs = pd.DataFrame({"middle_east": rig.round(), "us": 900.0}, index=months)
    rigs.index.name = "date"

    all_months = pd.date_range("2006-01-31", "2026-10-31", freq="ME")
    brent = pd.Series(70 * np.exp(np.cumsum(rng.normal(0, 0.08, len(all_months)))),
                      index=all_months, name="brent")
    brent.index.name = "date"

    uni = pd.read_csv(config.DATA / "universe.csv")
    tickers = list(uni["ticker"])
    month_of_day = days + pd.offsets.MonthEnd(0)

    # the planted effect: next month's return rises with weight x rig momentum
    signal_dates = pd.date_range("2006-01-31", "2026-10-31", freq="ME")
    mom = rig_momentum(rigs.asfreq("ME")).reindex(signal_dates)
    weights = monthly_weights(signal_dates)

    market = rng.normal(0.0003, 0.012, len(days))
    prices = {config.BENCHMARK: 100 * np.exp(np.cumsum(market)),
              config.MARKET: 100 * np.exp(np.cumsum(rng.normal(0.0003, 0.01, len(days))))}

    events = pd.read_csv(config.DATA / "contract_awards.csv", parse_dates=["announce_date"])
    for t in tickers:
        daily = 1.1 * market + rng.normal(0, 0.012, len(days))
        if t in weights:
            # earned the month after
            drift = (weights[t] * mom * args.effect).shift(1)
            per_day = drift.reindex(month_of_day).fillna(0).values / 21
            daily = daily + per_day
        for ev in events[events["ticker"] == t].itertuples():
            side = "right" if ev.release_timing == "after_close" else "left"
            day0 = days.searchsorted(ev.announce_date, side=side)
            if day0 < len(days):
                daily[day0] += args.event_jump
        prices[t] = 50 * np.exp(np.cumsum(daily))

    prices = pd.DataFrame(prices, index=days)
    prices.index.name = "date"

    raw = config.raw_dir(fake=True)
    raw.mkdir(parents=True, exist_ok=True)
    prices.to_csv(raw / "prices_daily.csv")
    brent.to_csv(raw / "brent_monthly.csv")
    rigs.to_csv(raw / "rig_counts.csv")
    print(f"Fake data written to {raw} with effect {args.effect} and event jump {args.event_jump}")


if __name__ == "__main__":
    main()
