#!/usr/bin/env python3
"""
=============================================================================
SCRIPT: replace_guest_customers.py
MỤC ĐÍCH: Thay thế toàn bộ mã KH_GUEST trong các file CSV dữ liệu bán lẻ
          bằng các mã khách hàng chuẩn (dải KH_90001 - KH_90800) với phân bổ
          tự nhiên (~3 giao dịch / khách hàng).
          Đồng bộ trên retail_cleaned_10000.csv, retail_cleaned_5000.csv,
          và retail_cleaned_full.csv.
=============================================================================
"""

import os
import random
import json
import pandas as pd
from collections import Counter

DATA_DIR = "/mnt/d/2026/BigData/phoenix-demo/data"
if not os.path.exists(DATA_DIR):
    DATA_DIR = "D:\\2026\\BigData\\phoenix-demo\\data"

file_10k = os.path.join(DATA_DIR, "retail_cleaned_10000.csv")
file_5k = os.path.join(DATA_DIR, "retail_cleaned_5000.csv")
file_full = os.path.join(DATA_DIR, "retail_cleaned_full.csv")
summary_file = os.path.join(DATA_DIR, "cleaning_summary.json")

print("=" * 70)
print(" BẮT ĐẦU CHUYỂN ĐỔI MÃ KHÁCH HÀNG KH_GUEST -> KH_9xxxx")
print("=" * 70)

# 1. Đọc file 10k để lấy danh sách tất cả các MA_GIAO_DICH có KH_GUEST
df10 = pd.read_csv(file_10k)
guest_mask10 = df10["MA_KHACH_HANG"] == "KH_GUEST"
guest_tx_ids = sorted(df10.loc[guest_mask10, "MA_GIAO_DICH"].tolist())
print(f"-> Tìm thấy {len(guest_tx_ids):,} giao dịch KH_GUEST trong retail_cleaned_10000.csv")

# 2. Sinh mapping nhất quán theo seed 2026
random.seed(2026)
pool = [f"KH_{i}" for i in range(90001, 90801)]
tx_to_cust = {}
for tx_id in guest_tx_ids:
    tx_to_cust[tx_id] = random.choice(pool)

counts = Counter(tx_to_cust.values()).values()
print(f"-> Phân bổ vào {len(Counter(tx_to_cust.values())):,} khách hàng mới (Dải KH_90001 - KH_90800)")
print(f"   Số đơn/khách: min={min(counts)}, max={max(counts)}, trung bình={sum(counts)/len(counts):.2f}")

# 3. Cập nhật retail_cleaned_10000.csv
df10.loc[guest_mask10, "MA_KHACH_HANG"] = df10.loc[guest_mask10, "MA_GIAO_DICH"].map(tx_to_cust)
df10.to_csv(file_10k, index=False)
print(f"✓ Đã cập nhật file: {file_10k} (KH_GUEST còn lại: {(df10['MA_KHACH_HANG'] == 'KH_GUEST').sum()})")

# 4. Cập nhật retail_cleaned_5000.csv
if os.path.exists(file_5k):
    df5 = pd.read_csv(file_5k)
    guest_mask5 = df5["MA_KHACH_HANG"] == "KH_GUEST"
    df5.loc[guest_mask5, "MA_KHACH_HANG"] = df5.loc[guest_mask5, "MA_GIAO_DICH"].map(tx_to_cust)
    df5.to_csv(file_5k, index=False)
    print(f"✓ Đã cập nhật file: {file_5k} (KH_GUEST còn lại: {(df5['MA_KHACH_HANG'] == 'KH_GUEST').sum()})")

# 5. Cập nhật retail_cleaned_full.csv
if os.path.exists(file_full):
    dffull = pd.read_csv(file_full)
    guest_mask_full = dffull["MA_KHACH_HANG"] == "KH_GUEST"
    dffull.loc[guest_mask_full, "MA_KHACH_HANG"] = dffull.loc[guest_mask_full, "MA_GIAO_DICH"].map(tx_to_cust)
    dffull.to_csv(file_full, index=False)
    print(f"✓ Đã cập nhật file: {file_full} (KH_GUEST còn lại: {(dffull['MA_KHACH_HANG'] == 'KH_GUEST').sum()})")

# 6. Cập nhật cleaning_summary.json
if os.path.exists(summary_file):
    try:
        with open(summary_file, "r", encoding="utf-8") as f:
            summary = json.load(f)
        summary["guest_customers"] = 0
        summary["standardized_guests"] = len(counts)
        if "dffull" in locals():
            summary["unique_customers"] = int(dffull["MA_KHACH_HANG"].nunique())
        with open(summary_file, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=4, ensure_ascii=False)
        print(f"✓ Đã cập nhật tóm tắt thống kê: {summary_file}")
    except Exception as e:
        print(f"Lỗi cập nhật summary: {e}")

print("=" * 70)
print(" HOÀN TẤT THAY THẾ KH_GUEST THÀNH CÔNG!")
print("=" * 70)

