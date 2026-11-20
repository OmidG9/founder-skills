"""تست‌های مدل مالی آتیوار.

اجرا:
    python founder/test_financial_model.py -v
"""

import csv
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import financial_model as fm  # noqa: E402


class FinancialModel(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runs = {n: fm.run(n) for n in ("base", "stress", "severe")}

    def rows(self, name):
        return self.runs[name]["rows"]

    # ── سرتیتر هر سناریو ──────────────────────────────────────────────────────
    def test_base_headline(self):
        r = self.runs["base"]
        self.assertEqual(round(fm.at(r["rows"], 9, "active")), 616798)
        self.assertAlmostEqual(fm.at(r["rows"], 12, "revenue") / fm.B, 9.0, delta=0.05)
        self.assertEqual(r["payback"], 21)
        self.assertIsNone(r["gap"])

    def test_stress_headline(self):
        r = self.runs["stress"]
        self.assertEqual(round(fm.at(r["rows"], 9, "active")), 219933)
        self.assertAlmostEqual(fm.at(r["rows"], 12, "ebitda") / fm.B, 0.1, delta=0.05)
        self.assertIsNone(r["payback"])

    def test_severe_cash_gap(self):
        r = self.runs["severe"]
        self.assertEqual(r["gap"], 6)
        self.assertIsNone(r["payback"])
        self.assertLess(fm.at(r["rows"], 36, "cash"), 0)

    # ── قواعد حسابداری مدل ───────────────────────────────────────────────────
    def test_active_recurrence(self):
        for name, r in self.runs.items():
            churn = fm.SCENARIOS[name]["churn"]
            prev = 0.0
            for row in r["rows"]:
                expected = prev * (1 - churn) + row["adds"]
                self.assertAlmostEqual(row["active"], expected, places=6, msg=f"{name} m{row['month']}")
                self.assertGreaterEqual(row["active"], 0)
                prev = row["active"]

    def test_revenue_and_cash_identities(self):
        for name, r in self.runs.items():
            s = fm.SCENARIOS[name]
            invested = 0.0
            for row in r["rows"]:
                share = 1.0 if row["month"] >= s["license_month"] else s["pre_license_share"]
                self.assertAlmostEqual(row["revenue"], row["active"] * s["arpu"] * share,
                                       delta=1.0, msg=f"{name} m{row['month']} revenue")
                self.assertAlmostEqual(row["variable"], row["revenue"] * s["variable_pct"],
                                       delta=1.0, msg=f"{name} m{row['month']} variable")
                invested += row["tranche"]
                self.assertAlmostEqual(row["cash"], row["op_cum"] + invested,
                                       delta=1.0, msg=f"{name} m{row['month']} cash")

    def test_marketing_budget_and_reach_cap(self):
        for name, r in self.runs.items():
            s = fm.SCENARIOS[name]
            budgets = fm.series(s["marketing"])
            for i, row in enumerate(r["rows"]):
                self.assertLessEqual(row["marketing"], budgets[i] * fm.B + 1,
                                     msg=f"{name} m{row['month']} overspent")
                self.assertLessEqual(row["active"], s["reach_cap"] + 1e-6,
                                     msg=f"{name} m{row['month']} above reach cap")

    def test_marketing_budget_18_months(self):
        self.assertAlmostEqual(sum(fm.series(fm.SCENARIOS["base"]["marketing"])[:18]) * fm.B,
                               10.0e9, delta=1)
        self.assertAlmostEqual(sum(fm.series(fm.SCENARIOS["stress"]["marketing"])[:18]) * fm.B,
                               9.0e9, delta=1)
        self.assertAlmostEqual(sum(fm.series(fm.SCENARIOS["severe"]["marketing"])[:18]) * fm.B,
                               3.0e9, delta=1)

    # ── خروجی ────────────────────────────────────────────────────────────────
    def test_report_contains_headline(self):
        text = fm.build_report([self.runs[n] for n in ("base", "stress", "severe")])
        self.assertIn("616,798", text)
        self.assertIn("ماه 21", text)
        self.assertIn("هدف خود دک برای ماه ۱۲", text)

    def test_csv_output_has_108_rows(self):
        with tempfile.TemporaryDirectory() as d:
            md = os.path.join(d, "m.md")
            csv_path = os.path.join(d, "m.csv")
            sys.argv = ["financial_model.py", "--out", md, "--csv", csv_path]
            fm.main()
            self.assertTrue(os.path.exists(md))
            with open(csv_path, encoding="utf-8-sig") as fh:
                rows = list(csv.reader(fh))
            self.assertEqual(len(rows), 1 + 3 * 36)
            self.assertEqual(rows[0][0], "scenario")
            self.assertEqual(rows[0][1], "month")


if __name__ == "__main__":
    unittest.main(verbosity=2)
