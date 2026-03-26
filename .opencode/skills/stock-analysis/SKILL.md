---
name: stock-analysis
description: Run Vanguard ETF and custom stock analysis with price trends and provide investment recommendations
---

# Stock Analysis Skill

This skill runs stock price analysis and provides investment recommendations based on market trends.

## How to Use

When the user wants to analyze stocks, run this command:

```bash
cd /Users/tylerzhu/Documents/GitHub/epollo && python3 -c "
from stock_sentiment.stocks import print_multi_period_table
from stock_sentiment.lists import VANGUARD_CANADA, VANGUARD_US

print('=== VANGUARD CANADA ETFs ===')
print_multi_period_table(VANGUARD_CANADA)
print()
print('=== VANGUARD US ETFs ===')
print_multi_period_table(VANGUARD_US)
"
```

Or for custom symbols:
```bash
cd /Users/tylerzhu/Documents/GitHub/epollo && python3 stock_sentiment/stocks.py <symbols>
```

## Analysis Output

After running the analysis, interpret the results:

1. **Trend Column**: Shows arrows (↑ green = up, ↓ red = down) for 7d, 30d, 60d, 90d periods
2. **Pattern Recognition**:
   - `↓↓↓↓` (all down) = bearish
   - `↓↓↓↑` (recovering) = short-term pain, long-term hope
   - `↓↑↑↑` (recovered) = turnaround complete
   - `↑↑↑↑` (all up) = bullish

## Summary Template

After analysis, provide this summary template:

```
## Summary

**Market Context (March 2026)**:
- 15% universal tariff in effect (trade war uncertainty)
- "Great Rotation" from tech/growth → value/domestic/defensive
- Fed balancing inflation vs slowing growth

**Recommendations**:
- 🔴 SELL/REDUCE: Tech/Growth with tariff exposure (GOOG, META, AC.TO), emerging markets (VEF)
- 🟡 HOLD/WATCH: Volatile tech (NVDA, ADSK), REITs
- 🟢 BUY/ADD: Canadian dividend stocks (BCE.TO, T.TO), domestic Canadian exposure (VCN.TO)

**Key Insight**: Defensive shift - move toward Canadian dividend stocks (BCE, TELUS) and domestic exposure, avoid multinational tech due to tariff uncertainty.
```

## Current Market Research

Key findings from recent research:
- Tariff Turmoil 2.0: 15% universal tariff imposed Feb 24, 2026
- Russell 2000 outperforming Nasdaq by ~9% (value over growth)
- Canadian telcos (BCE, TELUS) offering 5-8% dividend yields
- Tech under pressure from tariffs + AI uncertainty
