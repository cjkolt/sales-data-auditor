# Sales Data Auditor

A small Python/pandas project for checking a messy sales CSV before calculating revenue.

I started it as a practice exercise. The useful part was learning not to treat every row in a spreadsheet as valid sales data.

## What it does

- Standardizes category names and several explicit date formats.
- Reports missing values, bad quantities or prices, repeated rows, and order IDs with conflicting details.
- **Excludes** rows that need review instead of guessing what the right value was.
- Totals accepted sales in integer cents, then writes clean data and basic revenue summaries by category, region, and month.

The input in `data/sales.csv` is a practice dataset. These are not findings about a real business.

## Run it

Requires Python 3.12 or a compatible version.

```bash
python -m pip install -r requirements.txt
python src/analyze_sales.py
```

Reports appear in `output/`:

- `clean_orders.csv`
- `review_required.csv` (source row number, order ID, reason)
- `summary.csv`
- `revenue_by_category.csv`, `revenue_by_region.csv`, `revenue_by_month.csv`

To choose a different source or output location:

```bash
python src/analyze_sales.py --input data/sales.csv --output output
```

Run the tests:

```bash
python -m unittest discover -s tests -v
```

The GitHub Actions workflow runs those tests and checks the script against the included sample data.

## Decisions and limitations

Dates in `MM/DD/YYYY` format are interpreted as **month/day/year**. Dates written `DD-MM-YYYY` are interpreted as **day-month-year**. This assumption needs to be confirmed before using an unfamiliar export.

Repeated identical rows keep the first copy. If the same order ID has conflicting details, **all** versions of that order are held for review. Missing regions and invalid amounts are also excluded from the clean totals. Those are deliberate, conservative choices—not automatic corrections to source records.

These outputs describe the accepted subset, not necessarily the business's true revenue. A real reporting workflow would need reconciliation against invoices or another system of record.
