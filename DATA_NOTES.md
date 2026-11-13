# Data notes

I collected the revenue figures and contract awards by hand, and every row in those files has a source link. They're the weakest part of the project, so check a few against the links before relying on them.

## segment_revenue.csv

Middle East revenue and total revenue for SLB and Halliburton, in millions of US dollars. Each row says which report it came from.

Some years are missing:

| Company | Missing years | Where to find them |
|---|---|---|
| SLB | 2006, 2007 | FY2008 10-K, segment note |
| SLB | 2017 | FY2019 10-K, segment note |
| SLB | 2020 | FY2022 10-K, segment note |
| SLB | 2021 (only a rounded number) | FY2022 or FY2023 10-K |
| HAL | 2007 | FY2008 or FY2009 10-K |

When a year is missing, the weight carries forward from the last year I have, and revenue growth isn't computed for that year or the next.

Things to know:

- SLB changed what its regional numbers include. In the FY2010 10-K they cover Oilfield Services only, and from FY2011 they include WesternGeco and the Smith businesses. 2011 and 2012 were restated later, so some years show up more than once. I only compute growth when both years come from the same version.
- I kept SLB's FY2013 and FY2016 rows as separate versions because I couldn't confirm 2013 was unchanged in the later report. That drops 2014 growth from the revenue test.
- Halliburton's numbers from 2008 on line up across filings where I could check them. HAL 2005 and 2006 are the Energy Services Group only, from before KBR was split off.
- SLB and Halliburton both report "Middle East and Asia" as one region, so the weights overstate how exposed they are to the Gulf.

## exposure_overrides.csv

- NESR gets a weight of 1 from July 2018, since it only operates in the Middle East and North Africa.
- RPC gets a weight of 0. Its international revenue was small, and none of it is reported as Middle East.

## Rig counts

The rig counts come from two Baker Hughes Worldwide Rig Count files, an archive that ends in March 2024 and the July 2025 report. They overlap for 135 months and agree exactly, so Baker Hughes didn't restate the history between them. Together they run from 1975 to July 2025.

The series is Baker Hughes' "Middle East" total, which covers more than just the Gulf states.

Two months are treated as breaks:

- June 2012. The count jumps from 318 in May to 400 in June (+26%) and stays there. Rigs take months to move, so a jump that size in one month looks like Baker Hughes started counting something new, not a real change in drilling.
- January 2024. Baker Hughes started counting all operating rigs in Saudi Arabia. It didn't show up as a big jump in the data, but I kept it as a break to be safe.

Any momentum window that crosses a break is dropped. I made both of these calls before running the backtest.

## contract_awards.csv

- 10 company-events on 7 dates, from 2021 to 2025. That's a small sample.
- I couldn't confirm the release time for most of them, so they're treated as same-day.
- The two ADNOC framework awards went to several contractors at once, and the value for each company isn't disclosed.
- I haven't checked whether any awards land close to earnings releases, which would mix the two reactions.

## Prices

- NESR was off Nasdaq for part of 2024, so its Yahoo history might have gaps around then.
- Weatherford and Baker Hughes are only in the event study. Their current listings start in 2021 and 2017, so earlier events can't be used.
