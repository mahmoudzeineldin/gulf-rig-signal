from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

# first day of price data to download
START = "2006-01-01"

# in sample ends here, everything after is out of sample
IN_SAMPLE_END = "2017-12-31"

# rig momentum is the change in the rig count over this many months
MOM_MONTHS = 3

# trading cost charged per unit of turnover, in basis points
COST_BPS = 15

# oil services ETF, used for excess returns
BENCHMARK = "OIH"
MARKET = "SPY"

# months where the rig count definition changed (see DATA_NOTES.md).
# momentum windows that cross one of these are dropped
RIG_BREAKS = ["2024-01"]
DROP_BREAK_WINDOWS = True

# a fiscal year's revenue counts as public from April of the next year
REPORT_MONTH = 4

# event study windows, in trading days relative to the announcement
EST_START, EST_END = -250, -31
MIN_EST_DAYS = 100
EVENT_HALF_WIDTH = 10


def raw_dir(fake=False):
    return DATA / ("fake_raw" if fake else "raw")


def out_dir(fake=False):
    return ROOT / ("results_fake" if fake else "results")
