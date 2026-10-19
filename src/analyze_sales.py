"""Audit a sample sales export without silently repairing questionable orders."""

import argparse
from datetime import datetime
from pathlib import Path

import pandas as pd

COLUMNS = (
    "order_id", "customer_id", "order_date", "product", "category",
    "quantity", "unit_price", "region",
)
DATE_FORMATS = ("%Y-%m-%d", "%Y/%m/%d", "%m/%d/%Y", "%d-%m-%Y")


def parse_date(value):
    """Slash dates use month/day/year; hyphenated day-first dates are explicit."""
    if not isinstance(value, str) or not value.strip():
        return pd.NaT
    for pattern in DATE_FORMATS:
        try:
            return pd.Timestamp(datetime.strptime(value.strip(), pattern))
        except ValueError:
            pass
    return pd.NaT


def audit(raw):
    """Return accepted order rows and a list of rows needing review."""
    rows = raw.copy()
    rows.columns = rows.columns.str.strip().str.lower()
    missing = set(COLUMNS) - set(rows.columns)
    if missing:
        raise ValueError(f"Missing columns: {', '.join(sorted(missing))}")

    rows = rows[list(COLUMNS)]
    rows.insert(0, "source_row", range(2, len(rows) + 2))

    for field in ("order_id", "customer_id", "product", "category", "region"):
        rows[field] = rows[field].astype("string").str.strip()
    rows["category"] = rows["category"].str.title()
    rows["region"] = rows["region"].replace("", pd.NA)
    rows["order_date"] = rows["order_date"].astype("string").str.strip().map(parse_date)
    rows["quantity"] = pd.to_numeric(rows["quantity"], errors="coerce")
    rows["unit_price"] = pd.to_numeric(rows["unit_price"], errors="coerce")

    # Repeated identical rows are counted once. If an order ID has different
    # details on different rows, neither version is trustworthy enough to total.
    exact_repeat = rows.duplicated(subset=list(COLUMNS), keep="first")
    conflicting_ids = {
        order_id
        for order_id, group in rows.groupby("order_id", dropna=True)
        if len(group[list(COLUMNS)].drop_duplicates()) > 1
    }

    issues = []
    accepted = []
    for index, row in rows.iterrows():
        problems = []
        if any(pd.isna(row[field]) or str(row[field]).strip() == ""
               for field in ("order_id", "customer_id", "product", "category", "region")):
            problems.append("missing_required_text")
        if pd.isna(row["order_date"]):
            problems.append("unreadable_date")
        if pd.isna(row["quantity"]) or row["quantity"] <= 0 or row["quantity"] % 1 != 0:
            problems.append("invalid_quantity")
        if pd.isna(row["unit_price"]) or row["unit_price"] <= 0:
            problems.append("invalid_unit_price")
        elif abs(row["unit_price"] * 100 - round(row["unit_price"] * 100)) > 0.00001:
            problems.append("subcent_price")
        if row["order_id"] in conflicting_ids:
            problems.append("conflicting_order_id")
        elif exact_repeat.iloc[index]:
            problems.append("duplicate_row")

        if problems:
            issues.append({
                "source_row": int(row["source_row"]),
                "order_id": row["order_id"],
                "issues": "|".join(problems),
            })
        else:
            accepted.append(index)

    clean = rows.loc[accepted].copy()
    # Integer cents keep currency totals exact.
    clean["quantity"] = clean["quantity"].astype("int64")
    clean["unit_price_cents"] = (clean["unit_price"] * 100).round().astype("int64")
    clean["revenue_cents"] = clean["quantity"] * clean["unit_price_cents"]
    clean["revenue"] = clean["revenue_cents"] / 100
    clean["order_date"] = clean["order_date"].dt.strftime("%Y-%m-%d")

    review = pd.DataFrame(issues, columns=["source_row", "order_id", "issues"])
    return clean, review


def summarize(clean, review, input_rows):
    """Summarize only accepted rows, not the rows waiting for manual review."""
    total_cents = int(clean["revenue_cents"].sum())
    summary = pd.DataFrame([{
        "input_rows": input_rows,
        "accepted_orders": len(clean),
        "excluded_rows": len(review),
        "unique_customers": clean["customer_id"].nunique(),
        "revenue_cad": f"{total_cents / 100:.2f}",
    }])
    return summary


def write_reports(clean, review, raw_count, output):
    output.mkdir(parents=True, exist_ok=True)

    clean.drop(columns=["unit_price_cents", "revenue_cents"]).to_csv(
        output / "clean_orders.csv", index=False
    )
    review.to_csv(output / "review_required.csv", index=False)
    summarize(clean, review, raw_count).to_csv(output / "summary.csv", index=False)

    for field, filename in (
        ("category", "revenue_by_category.csv"),
        ("region", "revenue_by_region.csv"),
    ):
        grouped = clean.groupby(field)["revenue_cents"].sum().sort_values(ascending=False)
        report = grouped.rename("revenue_cents").reset_index()
        report["revenue_cad"] = (report["revenue_cents"] / 100).round(2)
        report.drop(columns=["revenue_cents"]).to_csv(output / filename, index=False)

    months = clean.assign(month=clean["order_date"].str.slice(0, 7))
    monthly = months.groupby("month")["revenue_cents"].sum().sort_index()
    report = monthly.rename("revenue_cents").reset_index()
    report["revenue_cad"] = (report["revenue_cents"] / 100).round(2)
    report.drop(columns=["revenue_cents"]).to_csv(
        output / "revenue_by_month.csv", index=False
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("data/sales.csv"))
    parser.add_argument("--output", type=Path, default=Path("output"))
    args = parser.parse_args()

    raw = pd.read_csv(args.input, dtype={"order_id": "string", "customer_id": "string"})
    clean, review = audit(raw)
    write_reports(clean, review, len(raw), args.output)
    summary = summarize(clean, review, len(raw)).iloc[0]
    print(
        f"Accepted {summary['accepted_orders']} of {summary['input_rows']} rows; "
        f"{summary['excluded_rows']} need review. "
        f"Accepted revenue: CAD {summary['revenue_cad']}."
    )
    print(f"Reports written to {args.output.resolve()}")


if __name__ == "__main__":
    main()
