#!/usr/bin/env python3
"""
Cập nhật phân vùng Việt Nam từ MIEN_BAC, MIEN_TRUNG, MIEN_NAM sang các tỉnh/thành phố thực tế:
- Miền Bắc: Hà Nội, Hải Phòng, Quảng Ninh, Bắc Ninh
- Miền Trung: Đà Nẵng, Khánh Hòa, Huế, Nghệ An
- Miền Nam: TP. Hồ Chí Minh, Bình Dương, Đồng Nai, Cần Thơ
"""

import os
import sys
import hashlib
import subprocess
import pandas as pd

def map_to_province(region: str, tx_id: str) -> str:
    r = str(region).strip()
    if r not in ["MIEN_BAC", "MIEN_TRUNG", "MIEN_NAM"]:
        return r
    h = int(hashlib.md5(str(tx_id).encode("utf-8")).hexdigest()[:6], 16) % 100
    if r == "MIEN_BAC":
        if h < 50:
            return "Hà Nội"
        elif h < 75:
            return "Hải Phòng"
        elif h < 88:
            return "Quảng Ninh"
        else:
            return "Bắc Ninh"
    elif r == "MIEN_TRUNG":
        if h < 50:
            return "Đà Nẵng"
        elif h < 75:
            return "Khánh Hòa"
        elif h < 88:
            return "Huế"
        else:
            return "Nghệ An"
    elif r == "MIEN_NAM":
        if h < 55:
            return "TP. Hồ Chí Minh"
        elif h < 75:
            return "Bình Dương"
        elif h < 88:
            return "Đồng Nai"
        else:
            return "Cần Thơ"
    return r

def main():
    base_dir = "/mnt/d/2026/BigData/phoenix-demo"
    
    # 1. Cập nhật vietnam_cleaned_tiki.csv
    vn_csv = os.path.join(base_dir, "data/vietnam_cleaned_tiki.csv")
    if os.path.exists(vn_csv):
        df_vn = pd.read_csv(vn_csv)
        df_vn["KHU_VUC"] = [map_to_province(r, tid) for r, tid in zip(df_vn["KHU_VUC"], df_vn["MA_GIAO_DICH"])]
        df_vn.to_csv(vn_csv, index=False, encoding="utf-8")
        print(f"✅ Đã cập nhật {vn_csv} ({len(df_vn)} dòng)")
        print("Phân bố tỉnh thành VN:", df_vn["KHU_VUC"].value_counts().to_dict())

    # 2. Cập nhật retail_cleaned_full.csv
    full_csv = os.path.join(base_dir, "data/retail_cleaned_full.csv")
    if os.path.exists(full_csv):
        df_full = pd.read_csv(full_csv)
        df_full["KHU_VUC"] = [map_to_province(r, tid) for r, tid in zip(df_full["KHU_VUC"], df_full["MA_GIAO_DICH"])]
        df_full.to_csv(full_csv, index=False, encoding="utf-8")
        print(f"✅ Đã cập nhật {full_csv} ({len(df_full)} dòng)")

    # 3. Cập nhật giao_dich_large_1000.csv nếu có
    large_csv = os.path.join(base_dir, "data/giao_dich_large_1000.csv")
    if os.path.exists(large_csv):
        df_large = pd.read_csv(large_csv)
        df_large["KHU_VUC"] = [map_to_province(r, tid) for r, tid in zip(df_large["KHU_VUC"], df_large["MA_GIAO_DICH"])]
        df_large.to_csv(large_csv, index=False, encoding="utf-8")
        print(f"✅ Đã cập nhật {large_csv} ({len(df_large)} dòng)")

    # 4. Nạp lại vào Phoenix qua psql.py
    print("⚡ Đang nạp dữ liệu vào Apache Phoenix qua psql.py...")
    psql_cmd = f"python3 /mnt/d/2026/BigData/phoenix/bin/psql.py localhost '{full_csv}'"
    res = subprocess.run(psql_cmd, shell=True, capture_output=True, text=True)
    print("psql returncode:", res.returncode)
    if res.stdout:
        print("psql stdout:", res.stdout[-300:])
    if res.stderr:
        print("psql stderr:", res.stderr[-300:])

    # 5. Tái xây dựng Secondary Index
    sys.path.append(os.path.join(base_dir, "dashboard"))
    import db
    print("⚡ Đang tái xây dựng chỉ mục IDX_GIAO_DICH_KHU_VUC...")
    ok, msg = db.execute_phoenix_sql("ALTER INDEX IDX_GIAO_DICH_KHU_VUC ON GIAO_DICH REBUILD;")
    print("Rebuild index result:", ok, msg)

    # 6. Kiểm tra lại dữ liệu tỉnh thành trong Phoenix
    df_chk, _ = db.query_phoenix_df("SELECT KHU_VUC, COUNT(*) AS CNT FROM GIAO_DICH GROUP BY KHU_VUC ORDER BY CNT DESC LIMIT 20;")
    print("Top 20 khu vực sau khi cập nhật:")
    print(df_chk)

if __name__ == "__main__":
    main()

