# reads the Baker Hughes rig count spreadsheets. they come in two layouts so it tries both
# if a new file doesn't work, run: python src/rig_counts.py --inspect file.xlsx
import re
import sys
from datetime import datetime

import pandas as pd

MONTHS = {"jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
          "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12}

MONTH_NAMES = {"january", "february", "march", "april", "may", "june",
               "july", "august", "september", "october", "november",
               "december"} | set(MONTHS) | {"sept"}

# used only when a flat table has countries but no region column
MIDDLE_EAST_COUNTRIES = {
    "saudi arabia", "abu dhabi", "dubai", "uae", "united arab emirates",
    "kuwait", "qatar", "oman", "iraq", "bahrain", "egypt", "jordan",
    "yemen", "syria", "pakistan", "iran", "israel", "turkey", "sudan",
}


def is_number(x):
    return isinstance(x, (int, float)) and not pd.isna(x)


# returns (month, year or None) if the cell is a month label
def month_of(cell):
    if isinstance(cell, (pd.Timestamp, datetime)):
        return cell.month, cell.year
    if isinstance(cell, str):
        word = cell.strip().lower().rstrip(".")
        if word in MONTH_NAMES:
            return MONTHS[word[:3]], None
    return None


def year_of(cell):
    if is_number(cell) and float(cell).is_integer() and 1970 <= cell <= 2100:
        return int(cell)
    if isinstance(cell, str) and re.fullmatch(r"\s*(19|20)\d\d\s*", cell):
        return int(cell)
    return None


# layout 1: a block of months for each year
def parse_year_blocks(sheet):
    rows = []
    year = None
    me_col = None
    us_col = None
    for cells in sheet.itertuples(index=False):
        cells = list(cells)
        text = [c.strip().lower() if isinstance(c, str) else "" for c in cells]

        # a header row tells us which column holds the Middle East
        if any("middle east" in t for t in text):
            me_col = next(i for i, t in enumerate(text) if "middle east" in t)
            us_names = ("u.s.", "u.s", "us", "united states", "usa")
            us_col = next((i for i, t in enumerate(text) if t in us_names), None)

        filled = [i for i, c in enumerate(cells) if not pd.isna(c)]
        if not filled:
            continue
        first = cells[filled[0]]

        # a year on its own starts a new block. rows of counts can start with a number
        # like 2,043, so only treat it as a year if nothing else in the row is a number
        y = year_of(first)
        others_numeric = any(is_number(cells[i]) for i in filled[1:])
        if y and not others_numeric:
            year = y
            continue

        m = month_of(first)
        if m and me_col is not None:
            month, own_year = m
            use_year = own_year or year
            if use_year is None or not is_number(cells[me_col]):
                continue
            us = cells[us_col] if us_col is not None and is_number(cells[us_col]) else None
            rows.append((pd.Timestamp(use_year, month, 1), cells[me_col], us))
    return rows


# layout 2: one row per country per month
def parse_flat_table(sheet):
    # the header row needs a region column and a count column. newer files have a
    # small summary table above the data that would get picked up otherwise
    header_at = None
    for i in range(min(40, len(sheet))):
        text = [str(c).strip().lower() for c in sheet.iloc[i].tolist()]
        names_place = any(t in ("region", "country") or "region" in t for t in text)
        names_count = any(("count" in t and "country" not in t) or t in ("rigs", "total")
                          for t in text)
        if names_place and names_count:
            header_at = i
            break
    if header_at is None:
        return []

    table = sheet.iloc[header_at + 1:].copy()
    table.columns = [str(c).strip().lower() for c in sheet.iloc[header_at].tolist()]

    def find(*words, skip=()):
        for col in table.columns:
            if col not in skip and any(w in col for w in words):
                return col
        return None

    region = find("region")
    country = find("country")
    count = find("rig count", "rigs", "count", "total", skip=(region, country))
    date = find("date", "period")
    year, month = find("year"), find("month")
    if count is None or (date is None and (year is None or month is None)):
        return []

    if date is not None:
        table["_date"] = pd.to_datetime(table[date], errors="coerce")
    else:
        def to_month(v):
            m = month_of(v)
            if m:
                return m[0]
            return v if is_number(v) else None
        table["_date"] = pd.to_datetime(
            dict(year=pd.to_numeric(table[year], errors="coerce"),
                 month=pd.to_numeric(table[month].map(to_month), errors="coerce"),
                 day=1), errors="coerce")
    table["_count"] = pd.to_numeric(table[count], errors="coerce")
    table = table.dropna(subset=["_date", "_count"])
    table["_date"] = table["_date"].dt.to_period("M").dt.to_timestamp()

    if region is not None:
        reg = table[region].astype(str).str.lower()
        is_me = reg.str.contains("middle east")
        is_us = reg.isin(["u.s.", "us", "united states", "usa"])
    else:
        ctry = table[country].astype(str).str.strip().str.lower()
        is_me = ctry.isin(MIDDLE_EAST_COUNTRIES)
        is_us = ctry.isin(["u.s.", "us", "united states", "usa"])

    me = table[is_me].groupby("_date")["_count"].sum()
    us = table[is_us].groupby("_date")["_count"].sum()
    # future months show up as zeros, so drop them
    me = me[me > 0]
    return [(d, v, us.get(d)) for d, v in me.items()]


# try both layouts on every sheet and keep whichever finds the most months
def read_workbook(path):
    sheets = pd.read_excel(path, sheet_name=None, header=None)
    best = []
    for name, sheet in sheets.items():
        for parser in (parse_year_blocks, parse_flat_table):
            try:
                rows = parser(sheet)
            except Exception:
                rows = []
            if len(rows) > len(best):
                best = rows
    if len(best) < 24:
        raise ValueError(
            f"Could not find a monthly Middle East series in {path}. "
            f"Run: python src/rig_counts.py --inspect \"{path}\"")
    out = pd.DataFrame(best, columns=["date", "middle_east", "us"])
    out = out.drop_duplicates("date", keep="last").set_index("date").sort_index()
    return out


def read_rig_file(path):
    path = str(path)
    if path.lower().endswith(".csv"):
        out = pd.read_csv(path, parse_dates=["date"]).set_index("date").sort_index()
        if "us" not in out.columns:
            out["us"] = None
        return out[["middle_east", "us"]]
    return read_workbook(path)


# joins the files into one series. where they overlap the newer file wins
# and the differences get printed
def load_rig_counts(paths):
    frames = [read_rig_file(p) for p in paths]
    frames.sort(key=lambda f: f.index.max())
    rigs = frames[0]
    for newer in frames[1:]:
        both = rigs.index.intersection(newer.index)
        if len(both):
            gap = (newer.loc[both, "middle_east"] - rigs.loc[both, "middle_east"]).abs()
            print(f"Overlap of {len(both)} months between files. "
                  f"Largest difference in the Middle East count: {gap.max():.0f} rigs "
                  f"(in {gap.idxmax():%Y-%m}).")
            # average difference by year, to see if history was restated
            diff = newer.loc[both, "middle_east"] - rigs.loc[both, "middle_east"]
            by_year = diff.groupby(diff.index.year).mean()
            print("Average difference by year (newer file minus older file):")
            print("  " + "  ".join(f"{y}: {v:+.0f}" for y, v in by_year.items()))
        rigs = newer.combine_first(rigs)
    rigs.index = rigs.index + pd.offsets.MonthEnd(0)
    rigs.index.name = "date"

    # show the biggest one-month jumps so a change in definition is easy to spot
    change = rigs["middle_east"].pct_change().dropna()
    biggest = change.abs().sort_values(ascending=False).head(5)
    print("Largest one-month changes in the Middle East rig count:")
    for d in biggest.index:
        print(f"  {d:%Y-%m}  {change[d]:+.1%}")
    return rigs


def inspect(path):
    sheets = pd.read_excel(path, sheet_name=None, header=None)
    for name, sheet in sheets.items():
        print(f"\nSheet '{name}' with {sheet.shape[0]} rows and {sheet.shape[1]} columns")
        print(sheet.head(15).to_string())


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--inspect":
        inspect(sys.argv[2])
    else:
        print(load_rig_counts(sys.argv[1:]).tail(12))
