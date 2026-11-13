# Results

Sample: 2006-01 to 2025-07, 4 stocks (HAL, NESR, RES, SLB), 658 stock-months. In sample ends 2017-12-31.

## Test 1: rig activity and Middle East revenue (annual)

| model | term | coef | t | p | n | r2 |
|---|---|---|---|---|---|---|
| same year | rig_g | 1.145 | 6.129 | 0.000 | 23 | 0.525 |
| rigs one year earlier | rig_g_lag | 0.233 | 0.585 | 0.559 | 25 | 0.024 |
| both, with Brent | rig_g | 0.840 | 3.933 | 0.000 | 21 | 0.740 |
| both, with Brent | rig_g_lag | 0.679 | 1.835 | 0.066 | 21 | 0.740 |
| both, with Brent | brent_g | 0.270 | 2.892 | 0.004 | 21 | 0.740 |

29 firm-years of revenue growth. Standard errors are clustered by year.

## Test 2: does the signal predict next month's return?

| model | term | coef | t | p | n | r2 |
|---|---|---|---|---|---|---|
| panel, signal only | signal | 0.151 | 0.753 | 0.451 | 658 | 0.002 |
| panel, with Brent | signal | 0.228 | 1.237 | 0.216 | 658 | 0.005 |
| panel, with Brent | brent_mom | -0.004 | -0.093 | 0.926 | 658 | 0.005 |
| panel, with Brent | w:brent_mom | 0.111 | 0.679 | 0.497 | 658 | 0.005 |
| spread, rigs only | rig_mom | -0.002 | -0.023 | 0.982 | 226 | 0.000 |
| spread, with Brent | rig_mom | -0.001 | -0.015 | 0.988 | 226 | 0.000 |
| spread, with Brent | brent_mom | 0.001 | 0.047 | 0.962 | 226 | 0.000 |

| measure | value | p | n |
|---|---|---|---|
| time-series IC (rig momentum vs next spread return) | -0.058 | 0.385 | 226 |
| cross-sectional IC (mean of monthly rank correlations) | -0.030 | 0.598 | 184 |

Panel regressions use returns in excess of the oil services ETF, company fixed effects and standard errors clustered by month. Spread regressions use Newey-West standard errors with 3 lags.

## Test 3: strategy

| strategy | period | returns | months | months invested | annual return | annual volatility | Sharpe | max drawdown | hit rate | avg monthly turnover |
|---|---|---|---|---|---|---|---|---|---|---|
| rig signal | in sample | gross | 140 | 135 | -0.065 | 0.190 | -0.342 | -0.682 | 0.415 | 0.585 |
| rig signal | in sample | net | 140 | 135 | -0.075 | 0.190 | -0.397 | -0.712 | 0.407 | 0.585 |
| rig signal | out of sample | gross | 91 | 85 | 0.028 | 0.215 | 0.132 | -0.394 | 0.506 | 0.506 |
| rig signal | out of sample | net | 91 | 85 | 0.019 | 0.215 | 0.090 | -0.396 | 0.506 | 0.506 |
| rig signal | full | gross | 231 | 220 | -0.028 | 0.200 | -0.140 | -0.759 | 0.450 | 0.554 |
| rig signal | full | net | 231 | 220 | -0.038 | 0.200 | -0.190 | -0.786 | 0.445 | 0.554 |
| Brent momentum (placebo) | in sample | gross | 140 | 140 | -0.047 | 0.192 | -0.246 | -0.742 | 0.450 | 0.528 |
| Brent momentum (placebo) | in sample | net | 140 | 140 | -0.057 | 0.192 | -0.294 | -0.760 | 0.436 | 0.528 |
| Brent momentum (placebo) | out of sample | gross | 107 | 107 | -0.026 | 0.244 | -0.105 | -0.644 | 0.486 | 0.506 |
| Brent momentum (placebo) | out of sample | net | 107 | 107 | -0.035 | 0.244 | -0.142 | -0.663 | 0.477 | 0.506 |
| Brent momentum (placebo) | full | gross | 247 | 247 | -0.038 | 0.215 | -0.175 | -0.819 | 0.466 | 0.519 |
| Brent momentum (placebo) | full | net | 247 | 247 | -0.047 | 0.216 | -0.218 | -0.847 | 0.453 | 0.519 |
| always long the spread | in sample | gross | 140 | 140 | -0.084 | 0.191 | -0.439 | -0.747 | 0.407 | 0.014 |
| always long the spread | in sample | net | 140 | 140 | -0.084 | 0.191 | -0.441 | -0.747 | 0.407 | 0.014 |
| always long the spread | out of sample | gross | 107 | 107 | 0.094 | 0.242 | 0.389 | -0.455 | 0.636 | 0.021 |
| always long the spread | out of sample | net | 107 | 107 | 0.094 | 0.242 | 0.387 | -0.455 | 0.636 | 0.021 |
| always long the spread | full | gross | 247 | 247 | -0.007 | 0.216 | -0.031 | -0.753 | 0.506 | 0.017 |
| always long the spread | full | net | 247 | 247 | -0.007 | 0.216 | -0.033 | -0.754 | 0.506 | 0.017 |

## Contract award event study

| sample | window | n | mean CAR | median CAR | t | p | share positive |
|---|---|---|---|---|---|---|---|
| each company-event counted once | before, days -10 to -1 | 10 | 0.009 | 0.009 | 0.987 | 0.350 | 0.800 |
| each company-event counted once | announcement, days 0 to +1 | 10 | 0.009 | 0.004 | 0.941 | 0.371 | 0.600 |
| each company-event counted once | around, days -5 to +5 | 10 | -0.050 | -0.037 | -1.945 | 0.084 | 0.300 |
| averaged within each announcement date | before, days -10 to -1 | 7 | 0.011 | 0.011 | 0.871 | 0.417 | 0.714 |
| averaged within each announcement date | announcement, days 0 to +1 | 7 | 0.015 | 0.011 | 1.141 | 0.297 | 0.714 |
| averaged within each announcement date | around, days -5 to +5 | 7 | -0.037 | -0.038 | -1.930 | 0.102 | 0.286 |

Events with a disclosed value: 1. The link between award size and the reaction is not tested until there are at least 8.
