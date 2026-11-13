# runs everything and writes results/ (add --fake to use the fake data)
import argparse

import pandas as pd

import charts
import config
from build_signal import build_panel, monthly_weights, rig_momentum
from event_study import run_event_study
from exposure_tests import test_returns, test_revenue, test_strategy


# simple markdown table so we don't need another package
def md_table(df, digits=3):
    def show(v):
        if isinstance(v, float):
            return "" if pd.isna(v) else f"{v:.{digits}f}"
        return str(v)
    head = "| " + " | ".join(df.columns) + " |"
    rule = "|" + "|".join(["---"] * len(df.columns)) + "|"
    body = ["| " + " | ".join(show(v) for v in row) + " |" for row in df.itertuples(index=False)]
    return "\n".join([head, rule] + body)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fake", action="store_true")
    fake = parser.parse_args().fake

    out = config.out_dir(fake)
    (out / "tables").mkdir(parents=True, exist_ok=True)
    (out / "figures").mkdir(parents=True, exist_ok=True)

    panel, rigs, brent, daily = build_panel(fake)
    panel.to_csv(out / "tables" / "panel.csv", index=False)

    rev_table, rev_data = test_revenue(rigs, brent)
    ret_table, ic_table, spread_ts = test_returns(panel)
    strat_table, runs = test_strategy(panel)
    cars, paths, event_table, skipped, size_note = run_event_study(daily)

    tables = {"test1_revenue": rev_table, "test1_data": rev_data, "test2_returns": ret_table,
              "test2_ic": ic_table.reset_index(names="measure"), "test3_strategy": strat_table,
              "events_cars": cars, "events_summary": event_table, "events_skipped": skipped}
    for name, table in tables.items():
        table.to_csv(out / "tables" / f"{name}.csv", index=False)

    names = sorted(panel["ticker"].unique())
    weights = monthly_weights(pd.DatetimeIndex(sorted(panel["date"].unique())))[names]
    charts.rig_chart(rigs, rig_momentum(rigs), out / "figures", fake)
    charts.weights_chart(weights.dropna(how="all"), out / "figures", fake)
    charts.strategy_chart(runs, out / "figures", fake)
    charts.event_chart(paths, out / "figures", fake)

    used = panel.dropna(subset=["signal", "ex_ret_next"])
    lines = []
    if fake:
        lines += ["# FAKE DATA: these numbers come from made-up prices and mean nothing", ""]
    lines += [
        "# Results",
        "",
        f"Sample: {used['date'].min():%Y-%m} to {used['date'].max():%Y-%m}, "
        f"{used['ticker'].nunique()} stocks ({', '.join(sorted(used['ticker'].unique()))}), "
        f"{len(used)} stock-months. In sample ends {config.IN_SAMPLE_END}.",
        "",
        "## Test 1: rig activity and Middle East revenue (annual)",
        "",
        md_table(rev_table) if len(rev_table) else "Not enough firm-years to run.",
        "",
        f"{rev_data['rev_g'].notna().sum()} firm-years of revenue growth. "
        "Standard errors are clustered by year.",
        "",
        "## Test 2: does the signal predict next month's return?",
        "",
        md_table(ret_table),
        "",
        md_table(ic_table.reset_index(names="measure")),
        "",
        "Panel regressions use returns in excess of the oil services ETF, company fixed "
        "effects and standard errors clustered by month. Spread regressions use "
        f"Newey-West standard errors with {config.MOM_MONTHS} lags.",
        "",
        "## Test 3: strategy",
        "",
        md_table(strat_table),
        "",
        "## Contract award event study",
        "",
        md_table(event_table) if len(event_table) else "No usable events.",
        "",
        size_note,
        "",
    ]
    if len(skipped):
        lines += ["Events left out:", "", md_table(skipped), ""]
    (out / "summary.md").write_text("\n".join(lines))
    print(f"Wrote {out / 'summary.md'}")


if __name__ == "__main__":
    main()
