# event study around Gulf contract awards. normal returns come from a regression
# on the oil services ETF over the year before each event
import numpy as np
import pandas as pd
from scipy import stats

import config

WINDOWS = {
    "before, days -10 to -1": (-10, -1),
    "announcement, days 0 to +1": (0, 1),
    "around, days -5 to +5": (-5, 5),
}


# abnormal returns from day -10 to +10 for one event
def abnormal_returns(daily, ticker, date, timing):
    if ticker not in daily.columns:
        return None, "no price data"
    rets = daily[[ticker, config.BENCHMARK]].pct_change(fill_method=None).dropna()
    days = rets.index

    # day 0 is the first trading day on which the market could react
    side = "right" if timing == "after_close" else "left"
    day0 = days.searchsorted(pd.Timestamp(date), side=side)

    half = config.EVENT_HALF_WIDTH
    if day0 + half >= len(days):
        return None, "not enough trading days after the event yet"

    est = rets.iloc[max(0, day0 + config.EST_START): max(0, day0 + config.EST_END + 1)]
    if len(est) < config.MIN_EST_DAYS:
        return None, f"only {len(est)} days of history before the event"

    beta, alpha = np.polyfit(est[config.BENCHMARK], est[ticker], 1)
    window = rets.iloc[day0 - half: day0 + half + 1]
    ar = window[ticker] - (alpha + beta * window[config.BENCHMARK])
    ar.index = range(-half, half + 1)
    return ar, None


def summarise(cars, label):
    rows = []
    for name in WINDOWS:
        x = cars[name].dropna()
        if len(x) < 2:
            continue
        t, p = stats.ttest_1samp(x, 0)
        rows.append({"sample": label, "window": name, "n": len(x),
                     "mean CAR": x.mean(), "median CAR": x.median(),
                     "t": t, "p": p, "share positive": (x > 0).mean()})
    return rows


def run_event_study(daily):
    events = pd.read_csv(config.DATA / "contract_awards.csv", parse_dates=["announce_date"])
    paths, cars, skipped = {}, [], []

    for i, ev in events.iterrows():
        ar, why = abnormal_returns(daily, ev["ticker"], ev["announce_date"], ev["release_timing"])
        label = f"{ev['announce_date']:%Y-%m-%d} {ev['ticker']} ({ev['client']})"
        if ar is None:
            skipped.append({"event": label, "reason": why})
            continue
        paths[label] = ar
        row = {"event": label, "date": ev["announce_date"], "ticker": ev["ticker"],
               "client": ev["client"], "value_usd_m": ev["value_usd_m"]}
        for name, (a, b) in WINDOWS.items():
            row[name] = ar.loc[a:b].sum()
        cars.append(row)

    cars = pd.DataFrame(cars)
    paths = pd.DataFrame(paths)
    skipped = pd.DataFrame(skipped)
    if cars.empty:
        return cars, paths, pd.DataFrame(), skipped, "No events could be used."

    summary = summarise(cars, "each company-event counted once")
    # companies sharing an announcement aren't independent, so also average within each date
    by_date = cars.groupby("date")[list(WINDOWS)].mean()
    summary += summarise(by_date, "averaged within each announcement date")
    summary = pd.DataFrame(summary)

    valued = cars.dropna(subset=["value_usd_m"])
    if len(valued) >= 8:
        rho, p = stats.spearmanr(valued["value_usd_m"], valued["announcement, days 0 to +1"])
        size_note = (f"Award size and announcement reaction: rank correlation {rho:.2f} "
                     f"(p = {p:.2f}, {len(valued)} events with a disclosed value).")
    else:
        size_note = (f"Events with a disclosed value: {len(valued)}. The link between award "
                     f"size and the reaction is not tested until there are at least 8.")
    return cars, paths, summary, skipped, size_note
