# Evidence Log

This file records what is verified for the dashboard and what should not be
overstated.

## Source files used

Local research sources used to generate the checked aggregate file:

- `V5_PUBLIC_DISCOURSE_ONLY.ndjson`
- `V5_PUBLIC_STATS_RERUN_20260507.json`
- `V5_LABELED_CORPUS_AUDIT_20260506.json`

The deployed dashboard uses only `docs/data/public_summary.json`, which contains
aggregate counts and chart data. It does not include raw post text.

## Build command run

The checked local command used `scripts/build_public_summary.py` with the three
source files listed above, writing `docs/data/public_summary.json`.

Observed output:

```text
wrote work\womens_safety_discourse_dashboard\docs\data\public_summary.json
rows=351501
canonical_case_rows=130858
cases=16
```

## Verified dashboard counts

From `docs/data/public_summary.json`:

- Public discourse rows: `351,501`
- Canonical case rows: `130,858`
- Canonical cases: `16`
- General discourse rows: `219,641`
- Platform counts: `328,199` Reddit, `23,302` YouTube
- Duplicate text-hash extra rows: `0`
- Invalid stance labels: `0`
- Invalid temporal phase labels: `0`
- Headline/newsbot audit count: `6,922`

## Date handling

Most `created_at` values are ISO date strings. A small set of rows used Unix
seconds. The builder normalizes Unix seconds to UTC dates before monthly chart
aggregation.

Observed type check:

```text
{'str': 350986, 'int': 515}
```

## Safe resume wording

Strong, defendable:

> Built an aggregate-only discourse dashboard over 351,501 Reddit/YouTube
> records, summarizing stance, platform, temporal phase, and case-level volume
> across 16 women-safety cases in India.

Also safe:

> Added a reproducible Python summary builder and validation tests to publish
> dashboard metrics without exposing raw post text.

Avoid:

- Do not say every row was manually labeled.
- Do not say the dashboard proves causality.
- Do not claim deployment scale or user traffic unless we actually measure it.
- Do not call `stance_gap_vs_general_pct_points` a published research metric.
