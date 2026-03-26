---
name: polymarket
description: Fetch latest geopolitical prediction market questions from Polymarket with probabilities
---

# Polymarket Geopolitical News Skill

This skill fetches the latest high-volume geopolitical questions from Polymarket prediction markets, including outcome probabilities.

## Quick Start

When the user wants to see latest geopolitical news from Polymarket, run:

```bash
cd /Users/tylerzhu/Documents/GitHub/epollo && python3 -c "
import sys
sys.path.insert(0, '.')
from epollo.polymarket import PolymarketFetcher

fetcher = PolymarketFetcher()
results = fetcher.get_geopolitical_recent_high_volume(limit=20, days_back=60)

print(f'=== TOP {len(results)} GEOPOLITICAL QUESTIONS (LAST 60 DAYS) ===\n')
for i, q in enumerate(results, 1):
    print(f'{i}. {q[\"question\"]}')
    if q['outcomes']:
        outcome_str = ' | '.join([f\"{o['outcome']}: {o['probability']:.1f}%\" for o in q['outcomes']])
        print(f'   Answers: {outcome_str}')
    print(f'   Volume: \${q[\"volume\"]:,.0f}')
    print(f'   URL: {q[\"url\"]}')
    print()
"
```

## API Reference

### PolymarketFetcher Class

```python
from epollo.polymarket import PolymarketFetcher

fetcher = PolymarketFetcher()

# Get geopolitical questions from last N days
results = fetcher.get_geopolitical_recent_high_volume(
    limit=20,      # Number of questions
    days_back=60   # Look back period (default 60 days)
)

# Get all latest questions (no tag filtering)
results = fetcher.get_all_latest_questions(limit=50)

# Get questions by specific tag ID
results = fetcher.get_questions_by_tag(tag_id='100265', limit=100)
```

### Result Format

Each question returns a dict with:

```python
{
    "question": "US x Iran ceasefire by...?",
    "slug": "us-x-iran-ceasefire-by",
    "url": "https://polymarket.com/event/us-x-iran-ceasefire-by",
    "tags": ["Geopolitics", "Politics", "Trump"],
    "volume": 49402735,
    "volume_24hr": 4871009,
    "outcomes": [
        {"outcome": "No", "probability": 87.5},
        {"outcome": "Yes", "probability": 12.5}
    ],
    "creation_date": "2026-02-28T..."
}
```

## Known Geopolitical Tag IDs

The fetcher uses these tag IDs for filtering:
- `100265` - Geopolitics
- `101253` - Macro Geopolitics
- `2` - Politics
- `101970` - World
- `101794` - Foreign Policy
- `96` - Ukraine
- `180` - Israel
- `154` - Middle East
- `95` - Russia
- `303` - China

## Key Geopolitical Keywords

Questions are filtered using these keywords:
- geopolitic, politics, world, foreign, diplomat
- ukraine, russia, israel, iran, china, nato
- middle east, war, conflict, military, troop
- sovereignty, invasion, treaty, sanction, peace
- nuclear, missile, ceasefire, alliance, regime

## Example Output

```
=== TOP 5 GEOPOLITICAL QUESTIONS ===

1. US x Iran ceasefire by...?
   Answers: No: 87.5% | Yes: 12.5%
   Volume: $49,402,735
   URL: https://polymarket.com/event/us-x-iran-ceasefire-by

2. Who will be confirmed as Fed Chair?
   Answers: Yes: 95.7% | No: 4.3%
   Volume: $13,429,463
   URL: https://polymarket.com/event/who-will-be-confirmed-as-fed-chair

3. Which countries will conduct military action against Iran by March 31?
   Answers: No: 93.0% | Yes: 7.0%
   Volume: $9,892,871
   URL: https://polymarket.com/event/which-countries-will-strike-iran-by-march-31
```

## Troubleshooting

- **No results**: Check internet connection, Polymarket API may be temporarily unavailable
- **Few geopolitical results**: The market filtering is broad; try increasing `days_back`
- **Outcomes empty**: Some events may not have market data yet

## API Endpoint

Base URL: `https://gamma-api.polymarket.com`

Documentation: `https://docs.polymarket.com`
