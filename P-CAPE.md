---
date: 2026-09-06
source: https://elmwealth.com/p-cape/
author: Victor Haghani & James White (Elm Wealth, 2024)
tags:
- financial
- investing
- valuation
- economics
aliases:
- Payout-Adjusted CAPE
- P-CAE
- P-CAEY
- Payout and Cyclically-Adjusted Earnings
---

modified [[Shiller PE Ratio|CAPE]] metric introduced by Victor Haghani and James White (Elm Wealth, 2024). It corrects standard CAPE's structural underestimation of earnings by accounting for retained corporate earnings and share buybacks over the 10-year trailing window.

### why standard CAPE breaks

cyclically-adjusted earnings yield (CAEY = 1 / CAPE) is widely used to estimate long-term real stock market returns. The underlying premise assumes that if companies paid out 100% of earnings to shareholders, real earnings would stay flat in perpetuity.

in reality, companies don't pay out 100%:
- 1880–1988: average dividend payout ratio was ~65%.
- 1988–2024: payout ratio dropped to ~45%, and ~35% recently.

unpaid earnings don't disappear. They're either reinvested in the business to grow future earnings or used for share buybacks to reduce share count and boost EPS. 

by taking a simple 10-year inflation-adjusted average of past earnings without crediting retained capital, standard CAPE acts as if unpaid cash evaporated. This causes standard CAPE to underestimate baseline earnings power by 13%–15% on average, making the market look artificially expensive.

### the P-CAPE fix

P-CAPE computes payout and cyclically-adjusted earnings (P-CAE) by taking each year's inflation-adjusted earnings over the past 10 years and compounding forward the portion not paid as dividends at that year's earnings yield (CAEY):

payout-adjusted earnings year t = (payout ratio * earnings) + ((1 - payout ratio) * earnings * (1 + CAEY)^years_forward)

averaging these 10 adjusted years produces P-CAE:
- P-CAE averages **19% higher** than standard CAE (1890–2024).
- P-CAPE is roughly **16% lower** (cheaper) than traditional CAPE (e.g. a standard CAPE of 36 corresponds to a P-CAPE around 30).
- P-CAEY (1 / P-CAPE) predicts 10-year prospective real returns with nearly zero bias (0.1% vs -1.4% for traditional CAPE).
- explains **33%–35% of 10-year return variance**, compared to only 15%–24% for standard CAPE.

### how it ties to our earlier valuation frameworks

connection to [[Total Return EPS to Decompose Historical S&P 500 Performance|TR-EPS]]
P-CAPE is the 10-year moving average equivalent of Jesse Livermore's Total Return EPS. Livermore addressed the post-1982 shift from cash dividends to share buybacks across 140 years of market history by simulating counterfactual dividend reinvestment back to 1871. P-CAPE applies this same economic principle directly to Shiller's 10-year trailing window by compounding retained earnings forward at the market earnings yield.

revisiting the [[2025-11-18 CAPE]] bubble dilemma
in late 2025, standard CAPE hit 39, implying prices needed to fall 28% or earnings surge 39% to reach historical averages. Investors interpreting high CAPE as an immediate signal to hold cash suffered heavy cash drag. Under P-CAPE, the multiple was closer to 31–32 because massive corporate buybacks and reinvestment over the prior decade had built real underlying earnings power that standard CAPE ignored.

critique of Shiller's TR-CAPE
in 2014, Barclays and Shiller launched Total Return CAPE (TR CAPE). Elm Wealth points out that TR-CAPE was built as an econometric regression signal rather than a direct return forecast, and mathematically made retained earnings reduce future earnings expectations—the opposite of corporate reinvestment reality. P-CAPE provides an intuitive, economically grounded forecast.

### related
- [[Shiller PE Ratio]]
- [[Total Return EPS to Decompose Historical S&P 500 Performance]]
- [[2025-11-18 CAPE]]
- [[S&P 500]]
- [[investing]]
