# downloads prices and Brent, and reads the rig count files in data/raw
# the rig files have to be downloaded by hand first (see README)
import argparse
import io
import urllib.request

import pandas as pd

import config
from rig_counts import load_rig_counts

FRED_BRENT = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=MCOILBRENTEU"
BACKUP_BRENT = "https://raw.githubusercontent.com/datasets/oil-prices/main/data/brent-monthly.csv"


def tickers_to_download():
    uni = pd.read_csv(config.DATA / "universe.csv")
    return sorted(set(uni["ticker"]) | {config.BENCHMARK, config.MARKET})


# daily prices adjusted for splits and dividends
def download_prices(tickers):
    import yfinance as yf
    raw = yf.download(tickers, start=config.START, auto_adjust=True, progress=False)
    close = raw["Close"]
    if isinstance(close, pd.Series):
        close = close.to_frame(tickers[0])
    close.index = pd.to_datetime(close.index).tz_localize(None)
    close.index.name = "date"
    missing = [t for t in tickers if t not in close.columns or close[t].dropna().empty]
    if missing:
        print("No price data came back for:", ", ".join(missing))
    return close.dropna(how="all")


# monthly average Brent price, in dollars per barrel
def download_brent():
    for url in (FRED_BRENT, BACKUP_BRENT):
        try:
            text = urllib.request.urlopen(url, timeout=30).read().decode()
            table = pd.read_csv(io.StringIO(text))
            table.columns = ["date", "brent"]
            table["date"] = pd.to_datetime(table["date"]).dt.to_period("M").dt.to_timestamp("M")
            table["brent"] = pd.to_numeric(table["brent"], errors="coerce")
            print("Brent prices from", url)
            return table.dropna().set_index("date")["brent"]
        except Exception as err:
            print("Could not read", url, "-", err)
    raise RuntimeError("No Brent price source worked.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--rig-files", nargs="*",
                        help="rig count workbooks, default is every .xlsx in data/raw")
    args = parser.parse_args()

    raw = config.raw_dir()
    raw.mkdir(parents=True, exist_ok=True)

    prices = download_prices(tickers_to_download())
    prices.to_csv(raw / "prices_daily.csv")
    print(f"Saved prices for {prices.shape[1]} tickers, "
          f"{prices.index.min():%Y-%m-%d} to {prices.index.max():%Y-%m-%d}")

    download_brent().to_csv(raw / "brent_monthly.csv")

    rig_files = args.rig_files or sorted(str(p) for p in raw.glob("*.xlsx"))
    if rig_files:
        rigs = load_rig_counts(rig_files)
        rigs.to_csv(raw / "rig_counts.csv")
        print(f"Saved rig counts, {rigs.index.min():%Y-%m} to {rigs.index.max():%Y-%m}")
    elif not (raw / "rig_counts.csv").exists():
        print("No rig count workbook found in data/raw. Download it from "
              "https://rigcount.bakerhughes.com/intl-rig-count and run this again.")


if __name__ == "__main__":
    main()
