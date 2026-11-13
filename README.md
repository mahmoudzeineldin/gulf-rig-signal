# gulf-rig-signal

I spent this summer working in oil and gas, and one idea kept coming up: when Aramco and ADNOC drill more, the service companies that work for them should make more money, maybe before the stock market notices. Baker Hughes publishes a monthly rig count by region, so I tested whether the Middle East count predicts returns for oil-service stocks, weighted by how much of each company's revenue comes from the Middle East.

The stocks are SLB, Halliburton and NESR, with RPC as a control since it has no Middle East business. I collected each company's Middle East revenue share by hand from its annual reports for 2005 to 2025 (`data/segment_revenue.csv`).

## What I found

It doesn't work, and I think I understand why.

The rig count does track the business. Growth in the Middle East rig count lines up with growth in the companies' Middle East revenue in the same year (t = 6.1). But that doesn't turn into a trading signal:

| Test | Result |
|---|---|
| Does the signal predict next month's return? | No (t = 0.75) |
| Sharpe of a strategy built on it, after 15 bps costs | -0.40 in sample (2006-2017), 0.09 out of sample (2018-2025) |
| Stock reaction to 10 Aramco and ADNOC contract awards | +0.9% on average, not significant |

The rig count is free and comes out every month, so the market has already priced it by the time you could trade on it. An edge would need information the market doesn't have yet, like contract awards before they're announced.

Some caveats. The revenue result rests on only about 23 company-years. SLB and Halliburton report "Middle East and Asia" as one region, so the weights overstate how exposed they are to the Gulf. There are only four stocks, and the rig data I have ends in July 2025.

## Data cleaning

The Middle East rig count jumps 26% in June 2012 and stays at the new level, which looks like Baker Hughes started counting something new rather than a real jump in drilling. Baker Hughes also changed how it counts Saudi rigs in January 2024. I treat both as breaks and drop any momentum window that crosses one. I made both calls before running the backtest, and the reasoning is in `DATA_NOTES.md`.

## Running it

The rig counts can't be downloaded automatically. Get the Worldwide Rig Count files from rigcount.bakerhughes.com/intl-rig-count (the current report and the Jan 2007 to Mar 2024 archive) and put them in `data/raw/`. Then:

```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python src/get_data.py
python src/run_all.py
```

The results go to `results/summary.md` and the charts to `results/figures/`.

Before trusting it on real data I checked it on fake data with a known effect planted in it:

```
python tests/make_fake_data.py --effect 0.5 --event-jump 0.03
python src/run_all.py --fake
```

## Files

- `data/` has the hand-collected revenue shares, the company list and the contract awards
- `src/rig_counts.py` reads the Baker Hughes files
- `src/build_signal.py` builds the monthly signal, lagged a month since the count comes out after the month ends
- `src/exposure_tests.py` has the three tests
- `src/event_study.py` has the contract award study
- `DATA_NOTES.md` explains where every number came from
