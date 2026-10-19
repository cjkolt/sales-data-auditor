# Sales Data Auditor

A small Python/pandas practice repo. I'm using a sample sales CSV to get more comfortable finding messy data and turning it into something that can actually be analyzed.

It's **not finished**, and I'm keeping that distinction clear.

## What's here

- `data/sales.csv`: the practice dataset
- `src/analyze_sales.py`: an early script that loads the CSV, inspects missing/duplicate rows, and works on inconsistent order dates

The current script is exploratory. It still prints the dataframe, repeats some date-conversion work, and hasn't completed the planned validation, revenue summaries, charts, or cleaned-data export.

## Run the current script

With Python and pandas installed, from the repository root:

```bash
python src/analyze_sales.py
```

## Next

1. Add clear checks for invalid quantities, prices, and dates.
2. Make the cleaning steps reproducible rather than editing columns ad hoc.
3. Calculate and verify basic sales metrics.
4. Export cleaned data and a short summary of issues found.
5. Add a couple of tests using intentionally messy sample rows.

This is a learning exercise, not a published analytics result.
