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
    # Quy tắc mã giao dịch: bắt đầu từ GD_100001 để TUYỆT ĐỐI KHÔNG trùng lặp với GD001 -> GD999
    START_ID = 100001
    REGIONS = ["MIEN_NAM", "MIEN_BAC", "MIEN_TRUNG"]
    CUSTOMERS = [f"KH{i:03d}" for i in range(1, 101)]  # KH001 -> KH100
    PRODUCTS = [
        {"id": "SP01", "name": "Laptop Dell Precision", "base_price": 25000000.00},
        {"id": "SP02", "name": "MacBook Pro M3", "base_price": 32000000.00},
        {"id": "SP03", "name": "Man hinh Dell Ultrasharp", "base_price": 8500000.00},
        {"id": "SP04", "name": "Ban phim co Keychron", "base_price": 1850000.00},
        {"id": "SP05", "name": "Chuot Logitech MX Master", "base_price": 1950000.00},
        {"id": "SP06", "name": "Tai nghe Sony WH-1000XM5", "base_price": 6900000.00},
        {"id": "SP07", "name": "O cung SSD Samsung 2TB", "base_price": 3500000.00},
        {"id": "SP08", "name": "RAM DDR5 Kingston 32GB", "base_price": 2400000.00},
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
            tx_id = f"GD_{START_ID + i}"
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
