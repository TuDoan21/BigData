import pandas as pd
import numpy as np

file_path = "/mnt/d/2026/BigData/phoenix-demo/archive/data.csv"
print(f"Reading {file_path}...")
df = pd.read_csv(file_path, encoding="ISO-8859-1")
print(f"Shape: {df.shape}")
print("\nColumns and types:")
print(df.dtypes)
print("\nMissing values:")
print(df.isnull().sum())
print("\nSample 5 rows:")
print(df.head(5))
print("\nSummary stats:")
print(df.describe())
print("\nUnique countries count:", df['Country'].nunique())
print("Top 10 countries:")
print(df['Country'].value_counts().head(10))
print("\nNegative Quantity count:", (df['Quantity'] <= 0).sum())
print("Zero/Negative UnitPrice count:", (df['UnitPrice'] <= 0).sum())
print("Null CustomerID count:", df['CustomerID'].isnull().sum())
print("Null Description count:", df['Description'].isnull().sum())
