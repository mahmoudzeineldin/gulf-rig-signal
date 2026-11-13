# the three tests: rigs vs revenue, rigs vs next month's returns, and a simple strategy
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from scipy import stats

import config


# OLS with clustered or Newey-West standard errors
def fit(formula, data, need, cluster=None, hac_lags=None):
    d = data.dropna(subset=need)
    if cluster:
        return smf.ols(formula, d).fit(cov_type="cluster",
                                       cov_kwds={"groups": pd.factorize(d[cluster])[0]})
    if hac_lags:
        return smf.ols(formula, d).fit(cov_type="HAC", cov_kwds={"maxlags": hac_lags})
    return smf.ols(formula, d).fit()


def coef_rows(label, model, terms):
    rows = []
    for term in terms:
        rows.append({"model": label, "term": term,
                     "coef": model.params[term], "t": model.tvalues[term],
                     "p": model.pvalues[term], "n": int(model.nobs),
                     "r2": model.rsquared})
    return rows


# Test 1

# yearly middle east revenue growth, only when both years use the same region definition
def revenue_growth():
    seg = pd.read_csv(config.DATA / "segment_revenue.csv")
    rows = []
    for ticker, g in seg.groupby("ticker"):
        for year in sorted(g["fiscal_year"].unique()):
            this = g[g["fiscal_year"] == year]
            last = g[g["fiscal_year"] == year - 1]
            both = this.merge(last, on="basis", suffixes=("", "_prev")).sort_values("reported_in")
            if len(both):
                r = both.iloc[0]
                rows.append({"ticker": ticker, "year": year,
                             "rev_g": r["me_revenue_musd"] / r["me_revenue_musd_prev"] - 1})
    return pd.DataFrame(rows)


def test_revenue(rigs, brent):
    counts = rigs["middle_east"].dropna()
    by_year = counts.groupby(counts.index.year)
    full_years = by_year.count() >= 10
    rig_g = by_year.mean()[full_years].pct_change()
    if config.DROP_BREAK_WINDOWS:
        for b in config.RIG_BREAKS:
            rig_g[rig_g.index == pd.Timestamp(b).year] = np.nan
    brent_g = brent.groupby(brent.index.year).mean().pct_change()

    d = revenue_growth()
    d["rig_g"] = d["year"].map(rig_g)
    d["rig_g_lag"] = d["year"].map(rig_g.shift(1))
    d["brent_g"] = d["year"].map(brent_g)

    rows = []
    specs = [
        ("same year", "rev_g ~ rig_g + C(ticker)", ["rig_g"]),
        ("rigs one year earlier", "rev_g ~ rig_g_lag + C(ticker)", ["rig_g_lag"]),
        ("both, with Brent", "rev_g ~ rig_g + rig_g_lag + brent_g + C(ticker)",
         ["rig_g", "rig_g_lag", "brent_g"]),
    ]
    for label, formula, terms in specs:
        usable = d.dropna(subset=["rev_g"] + terms)
        if len(usable) < len(terms) + usable["ticker"].nunique() + 3:
            continue
        model = fit(formula, d, ["rev_g"] + terms, cluster="year")
        rows += coef_rows(label, model, terms)
    return pd.DataFrame(rows), d


# Test 2

# long high exposure, short low exposure, with the two sides adding up to 1
def exposure_spread(panel):
    w = panel.pivot(index="date", columns="ticker", values="w")
    r = panel.pivot(index="date", columns="ticker", values="ret_next")
    w = w.where(w.notna() & r.notna())
    tilt = w.sub(w.mean(axis=1), axis=0)
    size = tilt.abs().sum(axis=1)
    tilt = tilt.div(size.where(size > 0), axis=0)
    spread_next = (tilt * r).sum(axis=1, min_count=2)
    return tilt, r, spread_next


def test_returns(panel):
    rows = []
    need = ["ex_ret_next", "signal"]
    m = fit("ex_ret_next ~ signal + C(ticker)", panel, need, cluster="date")
    rows += coef_rows("panel, signal only", m, ["signal"])

    need = ["ex_ret_next", "signal", "brent_mom", "w"]
    m = fit("ex_ret_next ~ signal + brent_mom + w:brent_mom + C(ticker)", panel, need, cluster="date")
    rows += coef_rows("panel, with Brent", m, ["signal", "brent_mom", "w:brent_mom"])

    # same question as a single time series
    tilt, r, spread_next = exposure_spread(panel)
    timers = panel.drop_duplicates("date").set_index("date")[["rig_mom", "brent_mom"]]
    ts = timers.assign(spread_next=spread_next)

    m = fit("spread_next ~ rig_mom", ts, ["spread_next", "rig_mom"], hac_lags=config.MOM_MONTHS)
    rows += coef_rows("spread, rigs only", m, ["rig_mom"])
    m = fit("spread_next ~ rig_mom + brent_mom", ts, ["spread_next", "rig_mom", "brent_mom"],
            hac_lags=config.MOM_MONTHS)
    rows += coef_rows("spread, with Brent", m, ["rig_mom", "brent_mom"])

    # information coefficients
    ic = {}
    both = ts.dropna(subset=["spread_next", "rig_mom"])
    rho, p = stats.spearmanr(both["rig_mom"], both["spread_next"])
    ic["time-series IC (rig momentum vs next spread return)"] = (rho, p, len(both))

    monthly = []
    d = panel.dropna(subset=["signal", "ex_ret_next"])
    for date, g in d.groupby("date"):
        if len(g) >= 3 and g["signal"].nunique() > 1:
            monthly.append(stats.spearmanr(g["signal"], g["ex_ret_next"])[0])
    monthly = pd.Series(monthly).dropna()
    if len(monthly) > 12:
        t, p = stats.ttest_1samp(monthly, 0)
        ic["cross-sectional IC (mean of monthly rank correlations)"] = (monthly.mean(), p, len(monthly))
    ic = pd.DataFrame(ic, index=["value", "p", "n"]).T
    ic["n"] = ic["n"].astype(int)
    return pd.DataFrame(rows), ic, ts


# Test 3

# hold the spread when the signal is positive, flip it when it's negative
def run_strategy(tilt, r, timer):
    side = np.sign(timer.reindex(tilt.index)).fillna(0)
    pos = tilt.mul(side, axis=0).fillna(0)
    gross = (pos * r.fillna(0)).sum(axis=1)
    turnover = pos.diff().abs().sum(axis=1)
    turnover.iloc[0] = pos.iloc[0].abs().sum()
    net = gross - turnover * config.COST_BPS / 1e4

    out = pd.DataFrame({"gross": gross, "net": net, "turnover": turnover,
                        "invested": pos.abs().sum(axis=1) > 0})
    out.index = out.index + pd.offsets.MonthEnd(1)
    live = out.index[out["invested"]]
    return out.loc[live.min():live.max()] if len(live) else out.iloc[0:0]


def performance(returns, invested, turnover):
    if len(returns) < 12:
        return None
    growth = (1 + returns).cumprod()
    vol = returns.std() * np.sqrt(12)
    return {
        "months": len(returns),
        "months invested": int(invested.sum()),
        "annual return": returns.mean() * 12,
        "annual volatility": vol,
        "Sharpe": returns.mean() * 12 / vol if vol > 0 else np.nan,
        "max drawdown": (growth / growth.cummax() - 1).min(),
        "hit rate": (returns[invested] > 0).mean(),
        "avg monthly turnover": turnover.mean(),
    }


def test_strategy(panel):
    tilt, r, _ = exposure_spread(panel)
    timers = panel.drop_duplicates("date").set_index("date")[["rig_mom", "brent_mom"]]

    # start all three on the same month so they're comparable
    start = timers["rig_mom"].first_valid_index()
    tilt, r, timers = tilt.loc[start:], r.loc[start:], timers.loc[start:]
    always = pd.Series(1.0, index=tilt.index)

    runs = {
        "rig signal": run_strategy(tilt, r, timers["rig_mom"]),
        "Brent momentum (placebo)": run_strategy(tilt, r, timers["brent_mom"]),
        "always long the spread": run_strategy(tilt, r, always),
    }
    split = pd.Timestamp(config.IN_SAMPLE_END)
    rows = []
    for name, run in runs.items():
        periods = {"in sample": run[run.index <= split],
                   "out of sample": run[run.index > split],
                   "full": run}
        for period, part in periods.items():
            for kind in ("gross", "net"):
                perf = performance(part[kind], part["invested"], part["turnover"])
                if perf:
                    rows.append({"strategy": name, "period": period, "returns": kind, **perf})
    return pd.DataFrame(rows), runs
