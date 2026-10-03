#!/usr/bin/env python3
"""
=============================================================================
SCRIPT: generate_large_data.py
MỤC ĐÍCH: Sinh tập dữ liệu lớn giao dịch (1.000, 10.000, 50.000+ dòng)
           xuất ra định dạng CSV chuẩn tương thích với công cụ psql.py của Apache Phoenix.
=============================================================================
"""

import argparse
import csv
import datetime
import os
import random
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Công cụ sinh dữ liệu lớn giao dịch cho Apache Phoenix trên HBase."
    )
    parser.add_argument(
        "--rows",
        type=int,
        default=1000,
        help="Số lượng dòng bản ghi cần sinh (Mặc định: 1000). Ví dụ: 1000, 10000, 50000",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=2026,
        help="Hạt giống sinh số ngẫu nhiên để tái lặp kết quả (Mặc định: 2026)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="",
        help="Đường dẫn file CSV xuất ra. Mặc định: <project_root>/data/giao_dich_large_<rows>.csv",
    )
    parser.add_argument(
        "--no-header",
        action="store_true",
        help="Không xuất dòng tiêu đề (header). Mặc định luôn có header để dùng với '-h in-line'",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Ghi đè file nếu đã tồn tại mà không yêu cầu xác nhận",
    )
    return parser.parse_args()


def generate_data(rows: int, seed: int, output_path: str, force: bool, include_header: bool = True):
    # Thiết lập random seed để đảm bảo tính tái lặp dữ liệu (Reproducibility)
    random.seed(seed)

    # Kiểm tra tồn tại file nếu không có cờ --force
    if os.path.exists(output_path) and not force:
        print(f"[CẢNH BÁO] File đích đã tồn tại: {output_path}")
        try:
            choice = input("Bạn có muốn ghi đè file này không? (y/N): ").strip().lower()
            if choice not in ("y", "yes"):
                print("[HỦY BỎ] Đã hủy thao tác sinh dữ liệu để bảo vệ file cũ.")
                sys.exit(0)
        except (EOFError, KeyboardInterrupt):
            print("\n[HỦY BỎ] Đã hủy thao tác.")
            sys.exit(0)

    # Đảm bảo thư mục cha tồn tại
    parent_dir = os.path.dirname(output_path)
    if parent_dir and not os.path.exists(parent_dir):
        os.makedirs(parent_dir, exist_ok=True)

    # Dữ liệu danh mục tham chiếu
    # Quy tắc mã giao dịch: chuẩn hóa tiền tố TX_ với 7 chữ số (TX_0000001, TX_0000002...)
    # đồng bộ hoàn toàn với bộ dữ liệu quốc tế.
    START_ID = 1
    REGIONS = ["MIEN_NAM", "MIEN_BAC", "MIEN_TRUNG"]
    CUSTOMERS = [
        "KH_17850", "KH_13047", "KH_12583", "KH_13748", "KH_15100",
        "KH_15291", "KH_14688", "KH_17809", "KH_15311", "KH_16098",
        "KH_18074", "KH_17420", "KH_16029", "KH_16250", "KH_12431",
        "KH_17511", "KH_13705", "KH_13747", "KH_13408", "KH_13767",
        "KH_17924", "KH_13448", "KH_15862", "KH_15513", "KH_12791",
        "KH_16218", "KH_14045", "KH_14307", "KH_17908", "KH_17920",
    ]
    PRODUCTS = [
        {"id": "85123A", "name": "White Hanging Heart T-Light Holder", "base_price": 75000.00},
        {"id": "71053", "name": "White Metal Lantern", "base_price": 88000.00},
        {"id": "84406B", "name": "Cream Cupidon Coat Hanger", "base_price": 72000.00},
        {"id": "84029G", "name": "Knitted Union Flag Hot Water Bottle", "base_price": 98000.00},
        {"id": "84029E", "name": "Red Woolly Hottie White Heart", "base_price": 97000.00},
        {"id": "22752", "name": "Set 72 Colour Pencils Dolly Girl", "base_price": 205000.00},
        {"id": "21730", "name": "Glass Star Frosted T-Light Holder", "base_price": 110000.00},
        {"id": "22633", "name": "Hand Warmer Union Jack", "base_price": 51000.00},
        {"id": "22632", "name": "Hand Warmer Red Retrospot", "base_price": 54000.00},
        {"id": "84879", "name": "Assorted Colour Bird Ornament", "base_price": 44000.00},
        {"id": "22745", "name": "Poppy's Playhouse Bedroom", "base_price": 55000.00},
        {"id": "22748", "name": "Poppy's Playhouse Kitchen", "base_price": 55000.00},
        {"id": "22749", "name": "Poppy's Playhouse Livingroom", "base_price": 98000.00},
        {"id": "22310", "name": "Ivory Knit Dinosaur", "base_price": 43000.00},
        {"id": "84969", "name": "Box Of 6 Assorted Colour Teaspoons", "base_price": 110000.00},
        {"id": "22623", "name": "Box Of 6 Herb Markers", "base_price": 128000.00},
        {"id": "22622", "name": "Box Of 24 Cocktail Parasols", "base_price": 258000.00},
        {"id": "21754", "name": "Home Sweet Home Ceramic Hanger", "base_price": 154000.00},
        {"id": "21755", "name": "Love Bird Hanger", "base_price": 154000.00},
        {"id": "21777", "name": "Recipe Box With Metal Heart", "base_price": 206000.00},
    ]

    start_date = datetime.datetime(2026, 1, 1, 0, 0, 0)
    total_seconds = 90 * 24 * 3600  # Khoảng 90 ngày đầu năm 2026

    print(f"[*] Bắt đầu sinh {rows:,} dòng dữ liệu...")
    print(f"[*] Random Seed: {seed}")
    print(f"[*] Định dạng thời gian: yyyy-MM-dd HH:mm:ss")

    with open(output_path, mode="w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile, quoting=csv.QUOTE_MINIMAL)

        if include_header:
            # Cột CSV tương thích chính xác với bảng GIAO_DICH trong Phoenix
            writer.writerow([
                "MA_GIAO_DICH",
                "MA_KHACH_HANG",
                "MA_SAN_PHAM",
                "KHU_VUC",
                "SO_LUONG",
                "DON_GIA",
                "THOI_GIAN",
            ])

        for i in range(rows):
            tx_id = f"TX_{START_ID + i:07d}"
            customer = random.choice(CUSTOMERS)
            prod = random.choice(PRODUCTS)
            region = random.choice(REGIONS)
            qty = random.randint(1, 50)
            
            # Biến thiên giá nhẹ (+/- 5%)
            price_variation = random.uniform(0.95, 1.05)
            price = round(prod["base_price"] * price_variation, 2)
            
            # Thời gian giao dịch ngẫu nhiên
            random_offset = random.randint(0, total_seconds)
            tx_time = start_date + datetime.timedelta(seconds=random_offset)
            time_str = tx_time.strftime("%Y-%m-%d %H:%M:%S")

            writer.writerow([
                tx_id,
                customer,
                prod["id"],
                region,
                qty,
                f"{price:.2f}",
                time_str,
            ])

    file_size_mb = os.path.getsize(output_path) / (1024 * 1024)
    abs_path = os.path.abspath(output_path)

    print("=============================================================================")
    print(f"[THÀNH CÔNG] Đã sinh thành công {rows:,} dòng giao dịch.")
    print(f"[ĐƯỜNG DẪN FILE]: {abs_path}")
    print(f"[KÍCH THƯỚC FILE]: {file_size_mb:.2f} MB")
    print("=============================================================================")
    print("HƯỚNG DẪN NẠP VÀO APACHE PHOENIX BẰNG psql.py:")
    print("Chạy lệnh sau tại terminal Linux/WSL:")
    if include_header:
        print(f"python3 /mnt/d/2026/BigData/phoenix/bin/psql.py -t GIAO_DICH -h in-line localhost {abs_path}")
    else:
        print(f"python3 /mnt/d/2026/BigData/phoenix/bin/psql.py -t GIAO_DICH localhost {abs_path}")
    print("=============================================================================")


def main():
    args = parse_arguments()

    if not args.output:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.abspath(os.path.join(script_dir, ".."))
        output_dir = os.path.join(project_root, "data")
        args.output = os.path.join(output_dir, f"giao_dich_large_{args.rows}.csv")

    generate_data(
        rows=args.rows,
        seed=args.seed,
        output_path=args.output,
        force=args.force,
        include_header=not args.no_header,
    )


if __name__ == "__main__":
    main()
