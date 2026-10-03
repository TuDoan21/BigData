import pandas as pd
import numpy as np
import os

input_file = "/mnt/d/2026/BigData/phoenix-demo/archive/data.csv"
print(f"Loading {input_file}...")
df = pd.read_csv(input_file, encoding="ISO-8859-1")
print("Raw rows:", len(df))

# 1. Clean cancellations / negative quantities
df_valid_qty = df[df['Quantity'] > 0]
print("After Quantity > 0:", len(df_valid_qty))

# 2. Clean invalid unit price (<= 0)
df_valid_price = df_valid_qty[df_valid_qty['UnitPrice'] > 0]
print("After UnitPrice > 0:", len(df_valid_price))

# 3. Clean description
df_valid_desc = df_valid_price.dropna(subset=['Description']).copy()
df_valid_desc['Description'] = df_valid_desc['Description'].str.strip()
df_valid_desc = df_valid_desc[df_valid_desc['Description'] != '']
print("After valid Description:", len(df_valid_desc))

# 4. Check CustomerID nulls
print("Rows with valid CustomerID:", df_valid_desc['CustomerID'].notnull().sum())
print("Rows with missing CustomerID:", df_valid_desc['CustomerID'].isnull().sum())

# 5. Check duplicate rows (exact duplicates)
print("Exact duplicate rows:", df_valid_desc.duplicated().sum())

# 6. Check (InvoiceNo, StockCode) uniqueness
print("Duplicates on (InvoiceNo, StockCode):", df_valid_desc.duplicated(subset=['InvoiceNo', 'StockCode']).sum())

# 7. Check date formats
sample_dates = df_valid_desc['InvoiceDate'].head(10).tolist()
print("Sample InvoiceDate:", sample_dates)
