# builds the monthly panel, one row per stock per month
# a row dated t only uses what was public at the end of t, and the return is the one earned in t+1
import numpy as np
import pandas as pd

import config


def month_end(dates):
    return pd.DatetimeIndex(dates) + pd.offsets.MonthEnd(0)


def load_raw(fake=False):
    raw = config.raw_dir(fake)
    daily = pd.read_csv(raw / "prices_daily.csv", parse_dates=["date"], index_col="date").sort_index()

    brent = pd.read_csv(raw / "brent_monthly.csv", parse_dates=["date"], index_col="date")["brent"]
    brent.index = month_end(brent.index)

    rigs = pd.read_csv(raw / "rig_counts.csv", parse_dates=["date"], index_col="date")
    rigs.index = month_end(rigs.index)
    rigs = rigs.sort_index().asfreq("ME")
    return daily, brent, rigs


def monthly_returns(daily):
    month_close = daily.resample("ME").last()
    return month_close.pct_change(fill_method=None)


# rig momentum. the count for a month comes out early the next month,
# so at the end of month t we only have up to t-1
def rig_momentum(rigs):
    known = rigs["middle_east"].shift(1)
    mom = known / known.shift(config.MOM_MONTHS) - 1

    if config.DROP_BREAK_WINDOWS:
        for b in config.RIG_BREAKS:
            first_new = pd.Timestamp(b) + pd.offsets.MonthEnd(0)
            # skip windows that mix the old and new definitions
            mixed = pd.date_range(first_new + pd.offsets.MonthEnd(1),
                                  periods=config.MOM_MONTHS, freq="ME")
            mom[mom.index.isin(mixed)] = np.nan
    return mom


# middle east revenue share by company and year. if a year was reported twice,
# use the first report since that's what investors saw at the time
def yearly_weights():
    seg = pd.read_csv(config.DATA / "segment_revenue.csv")
    first = seg.sort_values("reported_in").drop_duplicates(["ticker", "fiscal_year"], keep="first")
    first = first.assign(weight=first["me_revenue_musd"] / first["total_revenue_musd"])
    return first.pivot(index="fiscal_year", columns="ticker", values="weight").sort_index()


# exposure weight at each month end, only using reports that were out by then
def monthly_weights(dates):
    yearly = yearly_weights()
    overrides = pd.read_csv(config.DATA / "exposure_overrides.csv", parse_dates=["from_date"])
    tickers = sorted(set(yearly.columns) | set(overrides["ticker"]))
    out = pd.DataFrame(index=dates, columns=tickers, dtype=float)

    for d in dates:
        # last fiscal year whose annual report is out by this date
        public = d.year - 1 if d.month >= config.REPORT_MONTH else d.year - 2
        seen = yearly[yearly.index <= public]
        if len(seen):
            # if a year is missing, keep using the last one we had
            out.loc[d, yearly.columns] = seen.ffill().iloc[-1]

    for row in overrides.itertuples():
        out.loc[out.index >= row.from_date, row.ticker] = row.weight
    return out


def build_panel(fake=False):
    daily, brent, rigs = load_raw(fake)
    rets = monthly_returns(daily)

    uni = pd.read_csv(config.DATA / "universe.csv")
    names = [t for t in uni.loc[uni["exposure_tests"] == "yes", "ticker"] if t in rets.columns]

    rig_mom = rig_momentum(rigs).reindex(rets.index)
    brent_mom = (brent / brent.shift(config.MOM_MONTHS) - 1).reindex(rets.index)
    weights = monthly_weights(rets.index)
    next_ret = rets.shift(-1)

    parts = []
    for t in names:
        parts.append(pd.DataFrame({
            "date": rets.index,
            "ticker": t,
            "w": weights[t].values if t in weights else np.nan,
            "rig_mom": rig_mom.values,
            "brent_mom": brent_mom.values,
            "ret_next": next_ret[t].values,
            "bench_next": next_ret[config.BENCHMARK].values,
        }))
    panel = pd.concat(parts, ignore_index=True)
    panel["signal"] = panel["w"] * panel["rig_mom"]
    panel["ex_ret_next"] = panel["ret_next"] - panel["bench_next"]
    return panel, rigs, brent, daily
