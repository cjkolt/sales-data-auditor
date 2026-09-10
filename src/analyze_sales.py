import pandas as pd

df = pd.read_csv('data/sales.csv')

num_rows = len(df)
num_cols = len(df.columns)

# identify missing values
rows_with_nan = df[df.isnull().any(axis=1)]

# identify duplicate rows/orders
duplicate_rows = df[df.duplicated()]

# clean category names
#dates
#strip hidden spaces
df.columns = df.columns.str.strip()
#Pandas reads rows ato transalte mixed formats
df['order_date'] = df['order_date'].astype(str).str.strip()
#make all into one visual standard YYYY-MM-DD
df['order_date'] = pd.to_datetime(df['order_date'], format='mixed', errors='coerce')

df['order_dates'] = pd.to_datetime(df['order_date'], format='mixed', errors='coerce')
df['order_date'] = df['order_date'].dt.strftime('%Y-%m-%d')
print(df['order_date'].head(10))

df['order_date'] = pd.to_datetime(df['order_date'], errors='coerce')

df

print(df)


# convert dates properly

# handle or flag invalid quantities/prices

# create new column

# CALCULATE
# total revenue
# avergae order value
# number of unique customers
# best-selling product 
# highest revenue product

# produce atleast three charts: revenue by category, revenue by region, revenue over time

# save cleaned data

# save a summary