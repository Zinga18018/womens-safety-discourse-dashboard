import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SUMMARY_PATH = ROOT / "docs" / "data" / "public_summary.json"
sys.path.insert(0, str(ROOT / "scripts"))

from build_public_summary import parse_date  # noqa: E402


def load_summary() -> dict:
    with SUMMARY_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


class PublicSummaryTests(unittest.TestCase):
    def test_verified_headline_counts_are_stable(self):
        data = load_summary()

        self.assertEqual(data["headline_metrics"]["public_discourse_rows"], 351_501)
        self.assertEqual(data["headline_metrics"]["canonical_case_rows"], 130_858)
        self.assertEqual(data["headline_metrics"]["case_count"], 16)
        self.assertEqual(data["headline_metrics"]["general_discourse_rows"], 219_641)

    def test_public_summary_is_aggregate_only(self):
        data = load_summary()

        serialized_case_data = json.dumps(data["per_case"])
        self.assertNotIn('"text"', serialized_case_data)
        self.assertIn("privacy_note", data)
        self.assertIn("Raw post text is not shipped", data["privacy_note"])

    def test_case_rows_have_dashboard_fields(self):
        data = load_summary()
        cases = data["per_case"]

        self.assertEqual(len(cases), 16)
        self.assertTrue(all("stance_gap_vs_general_pct_points" in item for item in cases))
        self.assertTrue(all("stance_pct" in item for item in cases))
        self.assertTrue(all("phase_counts" in item for item in cases))

    def test_unix_seconds_dates_are_normalized_to_utc_date(self):
        self.assertEqual(parse_date(1711929600), "2024-04-01")


if __name__ == "__main__":
    unittest.main()
