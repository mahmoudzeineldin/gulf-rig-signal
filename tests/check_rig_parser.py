# checks the rig reader on three small made-up workbooks
import sys
import tempfile
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from rig_counts import load_rig_counts, read_rig_file

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
REGIONS = ["Latin America", "Europe", "Africa", "Middle East", "Asia Pacific",
           "Total Intl.", "Canada", "U.S.", "Total World"]


def middle_east(year, month):
    return 200 + (year - 2020) * 12 + month


def write_rows(rows, path):
    # pad every row to the same length so pandas doesn't have to guess
    width = max(len(r) for r in rows)
    rows = [list(r) + [None] * (width - len(r)) for r in rows]
    pd.DataFrame(rows).to_excel(path, header=False, index=False)


def year_block_workbook(path):
    rows = [["Worldwide Rig Count"], []]
    for year in (2022, 2021, 2020):
        rows.append([year] + REGIONS)
        for m, name in enumerate(MONTHS, start=1):
            me = middle_east(year, m)
            rows.append([name, 150, 100, 90, me, 200, 540 + me, 120, 700, 2043])
        rows.append(["Avg.", 150, 100, 90, 0, 200, 0, 120, 700, 2043])
        rows.append([])
    write_rows(rows, path)


def flat_workbook(path):
    rows = [["Baker Hughes Worldwide Rig Count"], [],
            ["Region", "Country", "Year", "Month", "Rig Count"]]
    for year in (2022, 2023):
        for m in range(1, 13):
            me = middle_east(year, m)
            rows.append(["Middle East", "Saudi Arabia", year, m, me - 100])
            rows.append(["Middle East", "Kuwait", year, m, 100])
            rows.append(["Europe", "Norway", year, m, 17])
    write_rows(rows, path)


def monthly_report_workbook(path):
    # same layout as the July 2025 Baker Hughes report
    dates = [pd.Timestamp(2024, m, 1) for m in range(1, 13)]
    blank = [None] * 8
    rows = [[None, None, "INTERNATIONAL Monthly Rig Count Report"], [],
            blank + ["Region"] + dates + ["Monthly chg"]]
    for name in ("Africa", "Europe", "Middle East", "International"):
        rows.append(blank + [name] + [100] * 12 + [0])
    rows.append([])
    rows.append(["Region", "Country", "DrillFor", "Location", "Year", "Month",
                 "Rig Count Value"])
    for year in (2024, 2025):
        for m in range(1, 13):
            me = middle_east(year, m)
            rows.append(["Middle East", "SAUDI ARABIA", "Oil", "Land", year, m, me - 130])
            rows.append(["Middle East", "SAUDI ARABIA", "Gas", "Offshore", year, m, 30])
            rows.append(["Middle East", "KUWAIT", "Oil", "Land", year, m, 100])
            rows.append(["Africa", "ALGERIA", "Gas", "Land", year, m, 17])
    # months that have not happened yet show up as zeros and must be dropped
    for m in range(1, 4):
        rows.append(["Middle East", "SAUDI ARABIA", "Oil", "Land", 2026, m, 0])
        rows.append(["Middle East", "KUWAIT", "Oil", "Land", 2026, m, 0])
    write_rows(rows, path)


def main():
    with tempfile.TemporaryDirectory() as tmp:
        old, new = Path(tmp) / "old.xlsx", Path(tmp) / "new.xlsx"
        year_block_workbook(old)
        flat_workbook(new)
        rigs = load_rig_counts([str(old), str(new)])

    assert len(rigs) == 48, len(rigs)
    for date, value in rigs["middle_east"].items():
        assert value == middle_east(date.year, date.month), (date, value)
    assert rigs.loc["2021-06-30", "us"] == 700

    with tempfile.TemporaryDirectory() as tmp:
        report = Path(tmp) / "report.xlsx"
        monthly_report_workbook(report)
        rigs = read_rig_file(str(report))
    assert len(rigs) == 24, len(rigs)
    for date, value in rigs["middle_east"].items():
        assert value == middle_east(date.year, date.month), (date, value)
    print("Rig count reader passed on all three layouts.")


if __name__ == "__main__":
    main()
