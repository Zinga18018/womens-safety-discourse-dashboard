# StanceLens: Women's Safety Discourse Dashboard

[See the workflow flowchart and code walkthrough](WORKFLOW.md)

StanceLens is an interactive dashboard built from my women-safety public
discourse research dataset. It summarizes stance, platform, case volume, and
temporal patterns across Reddit and YouTube records tied to 16 women-safety
cases in India.

The goal is simple: make the research easier to inspect without publishing raw
post text in the demo.

## What this shows

- 351,501 public discourse records from the verified research export.
- 130,858 rows linked to the 16 canonical case set.
- Case-level stance mixes for Supportive of victim, Neutral reporting,
  Critical of society, and Critical of government.
- Platform split, temporal phase counts, monthly case volume, and a case-level
  stance gap score.

## Why this project matters

Most portfolio dashboards use clean toy data. This one is tied to a real
research pipeline, a real public-discourse question, and a dataset large enough
to force real data-cleaning decisions.

The public dashboard is aggregate-only. It does not ship raw post text. That
keeps the demo safer while still showing the analysis layer.

## Custom metric

`stance_gap_vs_general_pct_points` compares each case's stance mix to the
general-discourse baseline.

It is computed as half the L1 distance between the case stance percentages and
the general-discourse percentages. Higher values mean the case differs more from
background discourse.

This is a dashboard exploration metric, not a new paper claim.

## Run locally

From this folder:

```powershell
python -m http.server 8000 --directory docs
```

Then open:

```text
http://localhost:8000
```

If `python` is not on PATH, use the Python executable from your environment.

## Rebuild the public summary

The dashboard reads `docs/data/public_summary.json`. Rebuild it from the local
research export:

```powershell
python scripts/build_public_summary.py `
  --corpus "<path-to>\V5_PUBLIC_DISCOURSE_ONLY.ndjson" `
  --public-stats "<path-to>\V5_PUBLIC_STATS_RERUN_20260507.json" `
  --audit "<path-to>\V5_LABELED_CORPUS_AUDIT_20260506.json" `
  --output docs\data\public_summary.json
```

## Test

```powershell
python -m unittest discover -s tests
```

## Evidence and limitations

See `EVIDENCE.md` for the verified counts, source files, and caveats. The short
version: the row counts and aggregates are verified from local files; the public
demo intentionally excludes raw post text.
