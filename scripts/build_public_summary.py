"""Build aggregate dashboard data from the public discourse export.

This script intentionally writes aggregates, not raw posts. The public dashboard
can be deployed without shipping the full NDJSON corpus.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


STANCE_ORDER = [
    "Supportive_of_Victim",
    "Neutral_Reporting",
    "Critical_of_Society",
    "Critical_of_Govt",
]

PHASE_ORDER = [
    "PRE",
    "ACUTE",
    "SUSTAINED",
    "RETROSPECTIVE",
    "UNKNOWN",
    "General_Discourse",
]

DISPLAY_STANCE = {
    "Supportive_of_Victim": "Supportive of victim",
    "Neutral_Reporting": "Neutral reporting",
    "Critical_of_Society": "Critical of society",
    "Critical_of_Govt": "Critical of government",
}

DISPLAY_PHASE = {
    "PRE": "Pre-event",
    "ACUTE": "Acute",
    "SUSTAINED": "Sustained",
    "RETROSPECTIVE": "Retrospective",
    "UNKNOWN": "Unknown",
    "General_Discourse": "General discourse",
}


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def pct(part: int | float, whole: int | float) -> float:
    if not whole:
        return 0.0
    return round((part / whole) * 100.0, 2)


def parse_date(value: str) -> str | None:
    if not value:
        return None
    if isinstance(value, (int, float)):
        try:
            return datetime.fromtimestamp(value, tz=timezone.utc).date().isoformat()
        except (OSError, OverflowError, ValueError):
            return None
    value = str(value)
    try:
        return datetime.fromisoformat(value[:10]).date().isoformat()
    except ValueError:
        return None


def month_key(value: str) -> str | None:
    parsed = parse_date(value)
    if not parsed:
        return None
    return parsed[:7]


def sort_counter(counter: Counter) -> dict:
    return {key: counter[key] for key in sorted(counter)}


def counter_for_known_order(counter: Counter, order: list[str]) -> dict:
    return {key: int(counter.get(key, 0)) for key in order if counter.get(key, 0)}


def stance_gap(case_pct: dict[str, float], baseline: dict[str, float]) -> float:
    """Half-L1 distance from general-discourse stance mix, in percentage points."""
    gap = 0.0
    for stance in STANCE_ORDER:
        baseline_key = {
            "Supportive_of_Victim": "SV",
            "Neutral_Reporting": "NR",
            "Critical_of_Society": "CS",
            "Critical_of_Govt": "CG",
        }[stance]
        gap += abs(case_pct.get(stance, 0.0) - float(baseline.get(baseline_key, 0.0)))
    return round(gap / 2.0, 2)


def build_summary(corpus_path: Path, public_stats_path: Path, audit_path: Path) -> dict:
    public_stats = load_json(public_stats_path)
    audit = load_json(audit_path)
    case_names = public_stats["case_names"]
    canonical_cases = set(case_names)

    totals = Counter()
    platform_counts = Counter()
    stance_counts = Counter()
    phase_counts = Counter()
    date_quality_counts = Counter()

    per_case = {
        case: {
            "case": case,
            "n": 0,
            "platform_counts": Counter(),
            "stance_counts": Counter(),
            "phase_counts": Counter(),
            "date_quality_counts": Counter(),
            "monthly_counts": Counter(),
            "first_date": None,
            "last_date": None,
        }
        for case in case_names
    }

    monthly_case_counts: dict[tuple[str, str], int] = defaultdict(int)
    monthly_all_counts = Counter()

    with corpus_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            case = row.get("case", "")
            stance = row.get("stance", "")
            phase = row.get("temporal_phase", "")
            platform = row.get("platform", "")
            date_quality = row.get("date_quality", "")
            created_at = row.get("created_at", "")

            totals["rows"] += 1
            platform_counts[platform] += 1
            stance_counts[stance] += 1
            phase_counts[phase] += 1
            date_quality_counts[date_quality] += 1

            month = month_key(created_at)
            if month:
                monthly_all_counts[month] += 1

            if case in canonical_cases:
                item = per_case[case]
                item["n"] += 1
                item["platform_counts"][platform] += 1
                item["stance_counts"][stance] += 1
                item["phase_counts"][phase] += 1
                item["date_quality_counts"][date_quality] += 1
                if month:
                    item["monthly_counts"][month] += 1
                    monthly_case_counts[(case, month)] += 1

                parsed_date = parse_date(created_at)
                if parsed_date:
                    if item["first_date"] is None or parsed_date < item["first_date"]:
                        item["first_date"] = parsed_date
                    if item["last_date"] is None or parsed_date > item["last_date"]:
                        item["last_date"] = parsed_date

    canonical_total = sum(item["n"] for item in per_case.values())
    baseline = public_stats["general_discourse_baseline"]

    case_rows = []
    for case, item in per_case.items():
        stance_pct_by_case = {
            stance: pct(item["stance_counts"].get(stance, 0), item["n"])
            for stance in STANCE_ORDER
        }
        phase_pct_by_case = {
            phase: pct(item["phase_counts"].get(phase, 0), item["n"])
            for phase in PHASE_ORDER
        }
        peak_month = ""
        peak_month_count = 0
        if item["monthly_counts"]:
            peak_month, peak_month_count = item["monthly_counts"].most_common(1)[0]

        dominant_stance = ""
        if item["stance_counts"]:
            dominant_stance = item["stance_counts"].most_common(1)[0][0]

        case_rows.append(
            {
                "case": case,
                "case_year": int(case.rsplit("_", 1)[-1]),
                "n": int(item["n"]),
                "share_of_canonical_rows_pct": pct(item["n"], canonical_total),
                "dominant_stance": dominant_stance,
                "stance_gap_vs_general_pct_points": stance_gap(stance_pct_by_case, baseline),
                "first_date": item["first_date"],
                "last_date": item["last_date"],
                "peak_month": peak_month,
                "peak_month_count": int(peak_month_count),
                "platform_counts": counter_for_known_order(item["platform_counts"], ["reddit", "youtube"]),
                "stance_counts": counter_for_known_order(item["stance_counts"], STANCE_ORDER),
                "stance_pct": stance_pct_by_case,
                "phase_counts": counter_for_known_order(item["phase_counts"], PHASE_ORDER),
                "phase_pct": phase_pct_by_case,
                "date_quality_counts": sort_counter(item["date_quality_counts"]),
            }
        )

    case_rows.sort(key=lambda row: row["n"], reverse=True)

    monthly = [
        {"case": case, "month": month, "count": count}
        for (case, month), count in sorted(monthly_case_counts.items())
    ]
    monthly_all = [
        {"month": month, "count": count}
        for month, count in sorted(monthly_all_counts.items())
    ]

    summary = {
        "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "project": "StanceLens: Women's Safety Discourse Dashboard",
        "source_files": {
            "corpus": corpus_path.name,
            "public_stats": public_stats_path.name,
            "audit": audit_path.name,
        },
        "privacy_note": "Dashboard data is aggregate-only. Raw post text is not shipped in docs/data.",
        "case_year_range": "2012-2024",
        "case_names": case_names,
        "stance_order": STANCE_ORDER,
        "phase_order": PHASE_ORDER,
        "display_stance": DISPLAY_STANCE,
        "display_phase": DISPLAY_PHASE,
        "headline_metrics": {
            "public_discourse_rows": int(totals["rows"]),
            "canonical_case_rows": int(canonical_total),
            "case_count": len(case_names),
            "general_discourse_rows": int(public_stats["general_discourse_baseline"]["n"]),
            "platforms": len([value for value in platform_counts.values() if value]),
            "duplicate_text_hash_extra_rows": int(audit.get("duplicate_text_hash_extra_rows", 0)),
            "invalid_stance_count": int(audit.get("invalid_stance_count", 0)),
            "invalid_phase_count": int(audit.get("invalid_phase_count", 0)),
            "headline_or_newsbot_total": int(audit.get("headline_or_newsbot_total", 0)),
        },
        "counts": {
            "platform": sort_counter(platform_counts),
            "stance": counter_for_known_order(stance_counts, STANCE_ORDER),
            "phase": counter_for_known_order(phase_counts, PHASE_ORDER),
            "date_quality": sort_counter(date_quality_counts),
        },
        "general_discourse_baseline": baseline,
        "per_case": case_rows,
        "monthly_case_counts": monthly,
        "monthly_all_counts": monthly_all,
        "metric_definitions": {
            "stance_gap_vs_general_pct_points": (
                "Half-L1 distance between a case stance mix and the general-discourse "
                "baseline; larger values mean the case differs more from background discourse."
            )
        },
    }

    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus", required=True, type=Path)
    parser.add_argument("--public-stats", required=True, type=Path)
    parser.add_argument("--audit", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    summary = build_summary(args.corpus, args.public_stats, args.audit)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2)
        handle.write("\n")

    print(f"wrote {args.output}")
    print(f"rows={summary['headline_metrics']['public_discourse_rows']}")
    print(f"canonical_case_rows={summary['headline_metrics']['canonical_case_rows']}")
    print(f"cases={summary['headline_metrics']['case_count']}")


if __name__ == "__main__":
    main()
