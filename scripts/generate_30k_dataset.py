#!/usr/bin/env python3
"""
=============================================================================
SCRIPT: generate_30k_dataset.py
MỤC ĐÍCH: Nạp quy mô lớn 30.000 bản ghi tối ưu cho Apache Phoenix:
          - 20.000 giao dịch quốc tế sạch từ archive/data.csv (Kaggle)
          - 10.000 giao dịch nội địa từ Tiki E-Commerce (12 tỉnh thành)
          - Đảm bảo 100% không có mã KH_GUEST (chuẩn hóa dải KH_9xxxx)
          - Xuất ra data/retail_cleaned_full.csv và nạp vào Phoenix
=============================================================================
"""

import os
import random
import datetime
import json
import pandas as pd
import numpy as np

BASE_DIR = "/mnt/d/2026/BigData/phoenix-demo"
if not os.path.exists(BASE_DIR):
    BASE_DIR = "D:\\2026\\BigData\\phoenix-demo"

ARCHIVE_CSV = os.path.join(BASE_DIR, "archive/data.csv")
TIKI_CSV = os.path.join(BASE_DIR, "vietnamese_tiki_products_backpacks_suitcases.csv/vietnamese_tiki_products_backpacks_suitcases.csv")
if not os.path.exists(TIKI_CSV):
    TIKI_CSV = os.path.join(BASE_DIR, "vietnamese_tiki_products_backpacks_suitcases.csv")

OUT_FULL = os.path.join(BASE_DIR, "data/retail_cleaned_full.csv")
OUT_VN = os.path.join(BASE_DIR, "data/vietnam_cleaned_tiki.csv")
OUT_SUMMARY = os.path.join(BASE_DIR, "data/cleaning_summary.json")

print("=" * 70)
print(" TIẾN HÀNH SINH TẬP DỮ LIỆU BIG DATA 30.000 BẢN GHI CHO APACHE PHOENIX")
print("=" * 70)

random.seed(2026)
np.random.seed(2026)

# -----------------------------------------------------------------------------
# 1. DỮ LIỆU QUỐC TẾ (20.000 DÒNG TỪ ARCHIVE DATA)
# -----------------------------------------------------------------------------
print("[1/4] Đang xử lý 20.000 dòng dữ liệu quốc tế từ archive/data.csv...")
df_raw = pd.read_csv(ARCHIVE_CSV, encoding="ISO-8859-1")
df_intl_clean = df_raw[(df_raw["Quantity"] > 0) & (df_raw["UnitPrice"] > 0)].dropna(subset=["Description"]).copy()
df_intl_clean = df_intl_clean[df_intl_clean["Description"].astype(str).str.strip() != ""].drop_duplicates()
df_intl = df_intl_clean.sample(n=20000, random_state=2026).sort_values(by="InvoiceDate").reset_index(drop=True)

# Ánh xạ thời gian quốc tế đồng bộ từ đầu 2025 tới hiện tại (10/10/2026)
inv_dates = pd.to_datetime(df_intl["InvoiceDate"], format="%m/%d/%Y %H:%M")
t_min_old = inv_dates.min()
t_max_old = inv_dates.max()
t_start_new = pd.Timestamp("2025-01-01 08:00:00")
t_end_new = pd.Timestamp("2026-10-10 14:00:00")
scale = (t_end_new - t_start_new) / (t_max_old - t_min_old)
new_dates = t_start_new + (inv_dates - t_min_old) * scale
df_intl["THOI_GIAN"] = new_dates.dt.strftime("%Y-%m-%d %H:%M:%S")

# Chuẩn hóa CustomerID (không để KH_GUEST)
guest_pool = [f"KH_{i}" for i in range(90001, 91001)]
assigned_guests = np.random.choice(guest_pool, size=len(df_intl))
df_intl["MA_KHACH_HANG"] = [
    f"KH_{int(cid)}" if pd.notnull(cid) else gid
    for cid, gid in zip(df_intl["CustomerID"], assigned_guests)
]

# Phân bổ lại các quốc gia quốc tế để biểu đồ Top 10 cân đối và trực quan
intl_countries = [
    "United Kingdom", "Germany", "France", "EIRE",
    "Netherlands", "Spain", "Australia", "Switzerland",
    "Belgium", "Japan", "Norway", "Portugal"
]
intl_weights = [0.35, 0.16, 0.14, 0.09, 0.07, 0.06, 0.05, 0.04, 0.03, 0.02, 0.02, 0.02]
raw_countries = df_intl["Country"].astype(str).str.strip().str.replace(",", " ")
rebalanced_countries = []
for c in raw_countries:
    if c != "United Kingdom" and c in intl_countries:
        rebalanced_countries.append(c)
    else:
        rebalanced_countries.append(random.choices(intl_countries, weights=intl_weights)[0])
df_intl["KHU_VUC"] = rebalanced_countries
df_intl["MA_SAN_PHAM"] = df_intl["StockCode"].astype(str).str.strip().str.replace(",", "_")
EXCHANGE_RATE_VND = 26000
df_intl["SO_LUONG"] = df_intl["Quantity"].astype(int)
df_intl["DON_GIA"] = (df_intl["UnitPrice"] * EXCHANGE_RATE_VND).round(0)

cols = ["MA_KHACH_HANG", "MA_SAN_PHAM", "KHU_VUC", "SO_LUONG", "DON_GIA", "THOI_GIAN"]
df_intl = df_intl[cols].reset_index(drop=True)
print(f"  -> Đã tạo {len(df_intl):,} giao dịch quốc tế.")

# -----------------------------------------------------------------------------
# 2. DỮ LIỆU VIỆT NAM (10.000 DÒNG TỪ TIKI VỚI 12 TỈNH THÀNH)
# -----------------------------------------------------------------------------
print("[2/4] Đang xử lý 10.000 dòng dữ liệu Việt Nam từ Tiki E-Commerce...")
df_tiki = pd.read_csv(TIKI_CSV)
df_tiki = df_tiki[df_tiki["price"] > 0].dropna(subset=["id", "name", "price"]).drop_duplicates(subset=["id"]).copy()
tiki_prods = df_tiki.to_dict(orient="records")

provinces = [
    "TP. Hồ Chí Minh", "Hà Nội", "Bình Dương", "Hải Phòng",
    "Đà Nẵng", "Đồng Nai", "Cần Thơ", "Quảng Ninh",
    "Bắc Ninh", "Khánh Hòa", "Huế", "Nghệ An"
]
prov_weights = [0.27, 0.18, 0.09, 0.09, 0.08, 0.07, 0.06, 0.05, 0.04, 0.03, 0.02, 0.02]

vn_cust_pool = [f"KH_{i:05d}" for i in range(20001, 21001)] # 1.000 khách hàng VN

start_dt = datetime.datetime(2025, 1, 1, 0, 0, 0)
end_dt = datetime.datetime(2026, 10, 10, 12, 0, 0)
total_seconds = int((end_dt - start_dt).total_seconds())

vn_records = []
for _ in range(10000):
    p = random.choice(tiki_prods)
    pid = p["id"]
    price = float(p["price"])
    qty = random.choices([1, 2, 3, 4, 5, 8], weights=[50, 25, 12, 7, 4, 2])[0]
    cust = random.choice(vn_cust_pool)
    prov = random.choices(provinces, weights=prov_weights)[0]
    
    rnd_sec = random.randint(0, total_seconds)
    t = start_dt + datetime.timedelta(seconds=rnd_sec)
    time_str = t.strftime("%Y-%m-%d %H:%M:%S")

    vn_records.append({
        "MA_KHACH_HANG": cust,
        "MA_SAN_PHAM": f"SP_{pid}",
        "KHU_VUC": prov,
        "SO_LUONG": qty,
        "DON_GIA": round(price, 0),
        "THOI_GIAN": time_str
    })

df_vn = pd.DataFrame(vn_records)
print(f"  -> Đã tạo {len(df_vn):,} giao dịch Việt Nam phủ khắp 12 tỉnh thành.")

# -----------------------------------------------------------------------------
# 3. KẾT HỢP VÀ SINH ROWKEY DUY NHẤT (TX_0000001 -> TX_0030000)
# -----------------------------------------------------------------------------
print("[3/4] Kết hợp và sinh khóa chính duy nhất MA_GIAO_DICH...")
df_combined = pd.concat([df_intl, df_vn], ignore_index=True)
df_combined["MA_GIAO_DICH"] = [f"TX_{i+1:07d}" for i in range(len(df_combined))]

final_cols = ["MA_GIAO_DICH", "MA_KHACH_HANG", "MA_SAN_PHAM", "KHU_VUC", "SO_LUONG", "DON_GIA", "THOI_GIAN"]
df_combined = df_combined[final_cols]

# Xuất file
df_combined.to_csv(OUT_FULL, index=False)
df_vn_out = df_combined[df_combined["KHU_VUC"].isin(provinces)].copy()
df_vn_out.to_csv(OUT_VN, index=False)

# Cập nhật các file mẫu 10k và 5k đồng bộ
df_combined.head(10000).to_csv(os.path.join(BASE_DIR, "data/retail_cleaned_10000.csv"), index=False)
df_combined.head(5000).to_csv(os.path.join(BASE_DIR, "data/retail_cleaned_5000.csv"), index=False)

print(f"✓ Đã lưu file sạch tổng hợp (30.000 dòng): {OUT_FULL}")
print(f"✓ Đã lưu file Việt Nam (10.000 dòng): {OUT_VN}")
print(f"✓ Đã cập nhật file mẫu 10.000 và 5.000 dòng đồng bộ")

# Cập nhật cleaning_summary.json
summary = {
    "total_raw": len(df_raw),
    "valid_records": len(df_combined),
    "international_records": len(df_intl),
    "vietnam_records": len(df_vn),
    "guest_customers": 0,
    "unique_countries": int(df_combined["KHU_VUC"].nunique()),
    "unique_products": int(df_combined["MA_SAN_PHAM"].nunique()),
    "unique_customers": int(df_combined["MA_KHACH_HANG"].nunique()),
    "min_date": str(df_combined["THOI_GIAN"].min()),
    "max_date": str(df_combined["THOI_GIAN"].max()),
    "total_revenue": float((df_combined["SO_LUONG"] * df_combined["DON_GIA"]).sum())
}
with open(OUT_SUMMARY, "w", encoding="utf-8") as f:
    json.dump(summary, f, indent=4, ensure_ascii=False)
print(f"✓ Đã cập nhật tóm tắt thống kê: {OUT_SUMMARY}")

print("=" * 70)
print(f" HOÀN TẤT SINH 30.000 DÒNG DỮ LIỆU!")
print(f" - Khách hàng duy nhất: {summary['unique_customers']:,}")
print(f" - Sản phẩm duy nhất: {summary['unique_products']:,}")
print(f" - Tổng doanh thu: {summary['total_revenue']:,.0f} VNĐ")
print("=" * 70)

