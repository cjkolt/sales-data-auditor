import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.analyze_sales import audit, summarize, write_reports


def order(order_id, date="2026-04-15", price=12.50, quantity=2, region="Winnipeg"):
    return {
        "order_id": order_id,
        "customer_id": "C001",
        "order_date": date,
        "product": "Work Gloves",
        "category": " safety ",
        "quantity": quantity,
        "unit_price": price,
        "region": region,
    }


class SalesAuditTests(unittest.TestCase):
    def test_normalizes_dates_and_totals_integer_cents(self):
        rows = pd.DataFrame([
            order("A", "04/15/2026", 12.50, 2),
            order("B", "15-04-2026", 4.25, 3),
            order("C", "2026/04/16", 5.00, 1),
        ])
        clean, review = audit(rows)
        self.assertTrue(review.empty)
        self.assertEqual(clean["order_date"].tolist(),
                         ["2026-04-15", "2026-04-15", "2026-04-16"])
        self.assertEqual(clean["category"].unique().tolist(), ["Safety"])
        self.assertEqual(int(clean["revenue_cents"].sum()), 4275)

    def test_exact_repeats_and_conflicting_order_ids(self):
        original = order("A")
        conflicting = order("B")
        changed = order("B", price=45.00)
        rows = pd.DataFrame([original, original.copy(), conflicting, changed, order("C")])
        clean, review = audit(rows)

        self.assertEqual(clean["order_id"].tolist(), ["A", "C"])
        self.assertEqual(len(review), 3)
        self.assertIn("duplicate_row", review["issues"].tolist())
        self.assertEqual(sum(review["issues"].str.contains("conflicting_order_id")), 2)

    def test_invalid_values_are_not_rolled_into_revenue(self):
        rows = pd.DataFrame([
            order("GOOD", "2026-01-01", 10, 1),
            order("BAD_QTY", quantity=-2),
            order("BAD_PRICE", price=None),
            order("BAD_REGION", region=""),
            order("BAD_DATE", date="2026-99-99"),
            order("BAD_CENTS", price=3.141),
        ])
        clean, review = audit(rows)
        self.assertEqual(clean["order_id"].tolist(), ["GOOD"])
        self.assertEqual(len(review), 5)
        self.assertEqual(summarize(clean, review, len(rows)).iloc[0]["revenue_cad"], "10.00")

    def test_exports_review_and_grouped_reports(self):
        clean, review = audit(pd.DataFrame([
            order("A", price=10),
            order("B", price=20, region="Brandon"),
            order("C", quantity=0),
        ]))
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            write_reports(clean, review, 3, folder)
            expected = {
                "clean_orders.csv", "review_required.csv", "summary.csv",
                "revenue_by_category.csv", "revenue_by_region.csv",
                "revenue_by_month.csv",
            }
            self.assertEqual({p.name for p in folder.iterdir()}, expected)
            summary = pd.read_csv(folder / "summary.csv")
            self.assertEqual(summary["accepted_orders"].iloc[0], 2)
            self.assertEqual(summary["excluded_rows"].iloc[0], 1)
            self.assertAlmostEqual(summary["revenue_cad"].iloc[0], 60.00)


if __name__ == "__main__":
    unittest.main()
