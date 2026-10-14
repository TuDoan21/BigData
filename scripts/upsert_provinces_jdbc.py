#!/usr/bin/env python3
import os
import sys
import pandas as pd

sys.path.append("/mnt/d/2026/BigData/phoenix-demo/dashboard")
import db

def main():
    csv_path = "/mnt/d/2026/BigData/phoenix-demo/data/retail_cleaned_full.csv"
    df = pd.read_csv(csv_path)
    # Lấy 2,500 bản ghi Việt Nam (các dòng không phải quốc tế)
    vn_mask = ~df["KHU_VUC"].isin([
        'Australia', 'Austria', 'Bahrain', 'Belgium', 'Brazil', 'Canada', 'Channel Islands',
        'Cyprus', 'Czech Republic', 'Denmark', 'EIRE', 'European Community', 'Finland', 'France',
        'Germany', 'Greece', 'Hong Kong', 'Iceland', 'Israel', 'Italy', 'Japan', 'Lebanon',
        'Lithuania', 'Malta', 'Netherlands', 'Norway', 'Poland', 'Portugal', 'RSA', 'Saudi Arabia',
        'Singapore', 'Spain', 'Sweden', 'Switzerland', 'USA', 'United Arab Emirates',
        'United Kingdom', 'Unspecified'
    ])
    df_vn = df[vn_mask].copy()
    print(f"Tổng số bản ghi Việt Nam cần cập nhật: {len(df_vn)}")
    print("Các tỉnh thành:", df_vn["KHU_VUC"].value_counts().to_dict())

    # Thực hiện batch upsert
    conn = db.get_phoenix_connection()
    cursor = conn.cursor()
    
    batch_size = 500
    rows = list(zip(df_vn["MA_GIAO_DICH"].astype(str), df_vn["KHU_VUC"].astype(str)))
    
    for i in range(0, len(rows), batch_size):
        chunk = rows[i:i + batch_size]
        cursor.executemany("UPSERT INTO GIAO_DICH (MA_GIAO_DICH, KHU_VUC) VALUES (?, ?)", chunk)
        conn.commit()
        print(f"  Đã cập nhật {min(i + batch_size, len(rows))}/{len(rows)} bản ghi...")

    cursor.close()
    conn.close()
    print("✅ Đã commit toàn bộ 2,500 bản ghi vào Phoenix!")

    # Rebuild Index
    print("⚡ Tái xây dựng chỉ mục IDX_GIAO_DICH_KHU_VUC...")
    db.execute_phoenix_sql("ALTER INDEX IDX_GIAO_DICH_KHU_VUC ON GIAO_DICH REBUILD;")

    # Kiểm tra lại
    df_res, _ = db.query_phoenix_df("SELECT KHU_VUC, COUNT(*) AS CNT FROM GIAO_DICH GROUP BY KHU_VUC ORDER BY CNT DESC LIMIT 20;")
    print("Top 20 khu vực sau khi cập nhật:")
    print(df_res)

if __name__ == "__main__":
    main()

