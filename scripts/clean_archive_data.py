#!/usr/bin/env python3
"""
=============================================================================
SCRIPT: clean_archive_data.py
MỤC ĐÍCH: Lọc, làm sạch và chuẩn hóa tập dữ liệu e-commerce từ archive/data.csv
- Xử lý các dòng số lượng âm (đơn hủy, hàng hoàn)
- Xử lý đơn giá <= 0 (bad debt, quà tặng nội bộ)
- Xử lý các dòng thiếu tên sản phẩm (Description rỗng)
- Chuẩn hóa mã khách hàng vãng lai (CustomerID null -> KH_GUEST)
- Chuyển đổi định dạng thời gian sang chuẩn ISO: yyyy-MM-dd HH:mm:ss
- Loại bỏ các dòng trùng lặp hoàn toàn
- Sinh mã giao dịch duy nhất (TX_0000001, ...) làm RowKey cho Phoenix Primary Key
- Xuất file sạch đầy đủ và file mẫu chuẩn để nạp vào Apache Phoenix
=============================================================================
"""

import os
import sys
import pandas as pd
import numpy as np

def run_cleaning_pipeline(
    input_path: str = "/mnt/d/2026/BigData/phoenix-demo/archive/data.csv",
    output_dir: str = "/mnt/d/2026/BigData/phoenix-demo/data",
    sample_size: int = 5000
):
    print("=" * 70)
    print(" BẮT ĐẦU QUY TRÌNH LỌC VÀ LÀM SẠCH DỮ LIỆU ARCHIVE")
    print(f" File nguồn: {input_path}")
    print("=" * 70)

    if not os.path.exists(input_path):
        # Thử đường dẫn Windows nếu đang chạy trên Windows
        win_path = "D:\\2026\\BigData\\phoenix-demo\\archive\\data.csv"
        if os.path.exists(win_path):
            input_path = win_path
        else:
            print(f"[LỖI] Không tìm thấy file dữ liệu tại {input_path}")
            sys.exit(1)

    # 1. Đọc dữ liệu thô
    print("[1/6] Đang đọc file CSV gốc (encoding ISO-8859-1)...")
    df_raw = pd.read_csv(input_path, encoding="ISO-8859-1")
    total_raw = len(df_raw)
    print(f"  -> Tổng số dòng dữ liệu thô: {total_raw:,} bản ghi")

    # 2. Phân tích các lỗi dữ liệu
    neg_qty = (df_raw["Quantity"] <= 0).sum()
    zero_price = (df_raw["UnitPrice"] <= 0).sum()
    null_desc = df_raw["Description"].isnull().sum()
    null_cust = df_raw["CustomerID"].isnull().sum()
    exact_dup = df_raw.duplicated().sum()

    print("\n[2/6] Thống kê phát hiện dữ liệu bẩn / bất thường:")
    print(f"  - Số lượng âm hoặc bằng 0 (Đơn hủy/hoàn): {neg_qty:,} dòng ({neg_qty/total_raw*100:.2f}%)")
    print(f"  - Đơn giá âm hoặc bằng 0 (Lỗi ghi sổ/nợ): {zero_price:,} dòng ({zero_price/total_raw*100:.2f}%)")
    print(f"  - Tên mô tả mặt hàng bị rỗng (Null Description): {null_desc:,} dòng ({null_desc/total_raw*100:.2f}%)")
    print(f"  - Thiếu mã khách hàng (Khách vãng lai): {null_cust:,} dòng ({null_cust/total_raw*100:.2f}%)")
    print(f"  - Bản ghi trùng lặp hoàn toàn (Exact Duplicates): {exact_dup:,} dòng ({exact_dup/total_raw*100:.2f}%)")

    # 3. Tiến hành lọc sạch (Filtering)
    print("\n[3/6] Tiến hành lọc các bản ghi không hợp lệ...")
    df_clean = df_raw[df_raw["Quantity"] > 0].copy()
    df_clean = df_clean[df_clean["UnitPrice"] > 0].copy()
    df_clean = df_clean.dropna(subset=["Description"]).copy()
    df_clean["Description"] = df_clean["Description"].astype(str).str.strip()
    df_clean = df_clean[df_clean["Description"] != ""].copy()
    df_clean = df_clean.drop_duplicates().copy()

    valid_records = len(df_clean)
    dropped_records = total_raw - valid_records
    print(f"  -> Số dòng hợp lệ sau khi lọc: {valid_records:,} bản ghi")
    print(f"  -> Đã loại bỏ: {dropped_records:,} bản ghi ({dropped_records/total_raw*100:.2f}%)")

    # 4. Chuẩn hóa định dạng và tạo cấu trúc cho Apache Phoenix
    print("\n[4/6] Chuẩn hóa cột, kiểu dữ liệu và sinh RowKey...")

    # Chuyển đổi InvoiceDate sang chuẩn yyyy-MM-dd HH:mm:ss
    df_clean["InvoiceDate"] = pd.to_datetime(df_clean["InvoiceDate"], format="%m/%d/%Y %H:%M")
    df_clean["THOI_GIAN"] = df_clean["InvoiceDate"].dt.strftime("%Y-%m-%d %H:%M:%S")

    # Xử lý CustomerID
    df_clean["MA_KHACH_HANG"] = df_clean["CustomerID"].apply(
        lambda x: f"KH_{int(x)}" if pd.notnull(x) else "KH_GUEST"
    )

    # Xử lý Country -> KHU_VUC (loại bỏ dấu phẩy để an toàn CSV)
    df_clean["KHU_VUC"] = df_clean["Country"].astype(str).str.strip().str.replace(",", " ")

    # Xử lý StockCode -> MA_SAN_PHAM
    df_clean["MA_SAN_PHAM"] = df_clean["StockCode"].astype(str).str.strip().str.replace(",", "_")

    # Số lượng & Đơn giá (Quy đổi toàn bộ ngoại tệ sang VNĐ: 1 USD ~ 26,000 VNĐ theo yêu cầu người dùng)
    EXCHANGE_RATE_VND = 26000
    df_clean["SO_LUONG"] = df_clean["Quantity"].astype(int)
    df_clean["DON_GIA"] = (df_clean["UnitPrice"] * EXCHANGE_RATE_VND).round(0)

    # Sinh khóa chính duy nhất MA_GIAO_DICH (TX_0000001 ...)
    df_clean.reset_index(drop=True, inplace=True)
    df_clean["MA_GIAO_DICH"] = [f"TX_{i+1:07d}" for i in range(len(df_clean))]

    # 5. Xuất file dữ liệu sạch
    print("\n[5/6] Xuất dữ liệu sạch ra thư mục data/...")
    os.makedirs(output_dir, exist_ok=True)

    # Các cột chuẩn tương thích với bảng GIAO_DICH của Phoenix
    phoenix_cols = [
        "MA_GIAO_DICH",
        "MA_KHACH_HANG",
        "MA_SAN_PHAM",
        "KHU_VUC",
        "SO_LUONG",
        "DON_GIA",
        "THOI_GIAN",
    ]

    # File mẫu 5,000 dòng để nạp nhanh vào HBase/Phoenix
    sample_file = os.path.join(output_dir, f"retail_cleaned_{sample_size}.csv")
    df_sample = df_clean[phoenix_cols].head(sample_size)
    df_sample.to_csv(sample_file, index=False)
    print(f"  -> File mẫu ({sample_size:,} dòng): {sample_file}")

    # File mẫu 10,000 dòng nếu muốn kiểm thử tải lớn hơn
    sample_10k_file = os.path.join(output_dir, "retail_cleaned_10000.csv")
    df_clean[phoenix_cols].head(10000).to_csv(sample_10k_file, index=False)
    print(f"  -> File mẫu (10,000 dòng): {sample_10k_file}")

    # File sạch đầy đủ (dành cho archive & bulk load)
    full_clean_file = os.path.join(output_dir, "retail_cleaned_full.csv")
    df_clean[phoenix_cols].to_csv(full_clean_file, index=False)
    print(f"  -> File sạch toàn bộ ({valid_records:,} dòng): {full_clean_file}")

    # File metadata báo cáo tóm tắt quá trình làm sạch
    summary = {
        "total_raw": total_raw,
        "valid_records": valid_records,
        "dropped_records": dropped_records,
        "cancellations_dropped": int(neg_qty),
        "zero_price_dropped": int(zero_price),
        "null_description_dropped": int(null_desc),
        "guest_customers": int(null_cust),
        "exact_duplicates": int(exact_dup),
        "unique_countries": int(df_clean["KHU_VUC"].nunique()),
        "unique_products": int(df_clean["MA_SAN_PHAM"].nunique()),
        "unique_customers": int(df_clean["MA_KHACH_HANG"].nunique()),
        "min_date": str(df_clean["THOI_GIAN"].min()),
        "max_date": str(df_clean["THOI_GIAN"].max()),
        "total_revenue": float((df_clean["SO_LUONG"] * df_clean["DON_GIA"]).sum()),
    }
    summary_file = os.path.join(output_dir, "cleaning_summary.json")
    import json
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=4, ensure_ascii=False)
    print(f"  -> Báo cáo thống kê: {summary_file}")

    print("\n[6/6] HOÀN TẤT QUY TRÌNH LÀM SẠCH DỮ LIỆU!")
    print("=" * 70)
    return summary

if __name__ == "__main__":
    run_cleaning_pipeline()
