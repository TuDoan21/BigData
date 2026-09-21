"""
=============================================================================
MODULE: queries.py
MỤC ĐÍCH: Tập trung toàn bộ câu truy vấn SQL Apache Phoenix chuẩn hóa.
- Tối ưu hóa Super-Batch: Gộp toàn bộ dữ liệu Tổng quan vào 1 lần chạy JVM duy nhất.
- Hỗ trợ phân trang SQL an toàn LIMIT 20 OFFSET ...
- Danh mục 10 câu truy vấn demo chuẩn mực cho bài báo cáo môn Big Data.
- Loại bỏ các câu truy vấn thừa, cam kết không quét toàn bộ bảng khi chỉ cần một phần dữ liệu.
=============================================================================
"""

TABLE_NAME = "GIAO_DICH"
INDEX_NAME = "IDX_GIAO_DICH_KHU_VUC"

# Schema chuẩn cho bảng GIAO_DICH với Salt Buckets = 8
CREATE_TABLE_SQL = """
CREATE TABLE GIAO_DICH (
    MA_GIAO_DICH VARCHAR NOT NULL,
    MA_KHACH_HANG VARCHAR,
    MA_SAN_PHAM VARCHAR,
    KHU_VUC VARCHAR,
    SO_LUONG INTEGER,
    DON_GIA DECIMAL(15,2),
    THOI_GIAN TIMESTAMP,
    CONSTRAINT PK PRIMARY KEY (MA_GIAO_DICH)
) SALT_BUCKETS = 8;
""".strip()


# =============================================================================
# 1. TRUY VẤN TỔNG QUAN (SUPER-BATCH TỐI ƯU HÓA TỐI ĐA)
# =============================================================================

SQL_OVERVIEW_CHECK_TABLE = "SELECT COUNT(*) AS TONG_SO FROM GIAO_DICH;"
SQL_OVERVIEW_CHECK_INDEXES = "SELECT TABLE_NAME AS INDEX_NAME, INDEX_TYPE, INDEX_STATE FROM SYSTEM.CATALOG WHERE TABLE_TYPE = 'i' AND DATA_TABLE_NAME = 'GIAO_DICH';"

SQL_OVERVIEW_KPI = """
SELECT 
    COUNT(*) AS TONG_GIAO_DICH,
    COUNT(DISTINCT MA_KHACH_HANG) AS TONG_KHACH_HANG,
    SUM(SO_LUONG * DON_GIA) AS TONG_DOANH_THU,
    AVG(SO_LUONG * DON_GIA) AS GIA_TRI_TRUNG_BINH,
    COUNT(DISTINCT KHU_VUC) AS SO_KHU_VUC
FROM GIAO_DICH;
""".strip()

SQL_OVERVIEW_CHART_REGION = """
SELECT 
    KHU_VUC,
    COUNT(*) AS SO_GIAO_DICH,
    SUM(SO_LUONG * DON_GIA) AS TONG_DOANH_THU
FROM GIAO_DICH
GROUP BY KHU_VUC
ORDER BY TONG_DOANH_THU DESC;
""".strip()

SQL_OVERVIEW_TIMELINE = """
SELECT 
    TO_CHAR(THOI_GIAN, 'yyyy-MM-dd') AS NGAY_GIAO_DICH,
    COUNT(*) AS SO_GIAO_DICH,
    SUM(SO_LUONG * DON_GIA) AS DOANH_THU_NGAY
FROM GIAO_DICH
GROUP BY TO_CHAR(THOI_GIAN, 'yyyy-MM-dd')
ORDER BY NGAY_GIAO_DICH ASC;
""".strip()

SQL_OVERVIEW_TOP10 = """
SELECT 
    MA_GIAO_DICH,
    MA_KHACH_HANG,
    MA_SAN_PHAM,
    KHU_VUC,
    SO_LUONG,
    DON_GIA,
    THOI_GIAN
FROM GIAO_DICH
ORDER BY THOI_GIAN DESC
LIMIT 10;
""".strip()


def get_super_batch_overview_sql() -> list[str]:
    """
    Trả về toàn bộ 6 câu truy vấn của trang Tổng quan để chạy trong ĐÚNG 1 phiên SQLLine.
    Bao gồm:
    0: Kiểm tra số lượng bản ghi
    1: Kiểm tra Index
    2: 5 KPI Cards
    3: Biểu đồ theo khu vực
    4: Biểu đồ theo thời gian
    5: Top 10 giao dịch mới nhất
    """
    return [
        SQL_OVERVIEW_CHECK_TABLE,
        SQL_OVERVIEW_CHECK_INDEXES,
        SQL_OVERVIEW_KPI,
        SQL_OVERVIEW_CHART_REGION,
        SQL_OVERVIEW_TIMELINE,
        SQL_OVERVIEW_TOP10,
    ]


# =============================================================================
# 2. BUILDER TRANG QUẢN LÝ GIAO DỊCH (PHÂN TRANG DATABASE CHUẨN LIMIT 20)
# =============================================================================

def build_transaction_list_query(
    search_keyword: str = "",
    khu_vuc_list: tuple[str, ...] | list[str] | None = None,
    sort_by: str = "MA_GIAO_DICH",
    sort_order: str = "ASC",
    limit: int = 20,
    offset: int = 0,
) -> str:
    """
    Sinh câu lệnh SQL tìm kiếm và phân trang trực tiếp trên database.
    Mặc định 20 bản ghi mỗi trang theo yêu cầu.
    """
    conditions = []

    if search_keyword and search_keyword.strip():
        kw = search_keyword.strip().replace("'", "")
        if kw.upper().startswith("GD"):
            conditions.append(f"MA_GIAO_DICH = '{kw}'")
        elif kw.upper().startswith("KH"):
            conditions.append(f"MA_KHACH_HANG = '{kw}'")
        else:
            conditions.append(f"(MA_GIAO_DICH = '{kw}' OR MA_KHACH_HANG = '{kw}')")

    valid_regions = {"MIEN_NAM", "MIEN_BAC", "MIEN_TRUNG"}
    if khu_vuc_list:
        filtered_regions = [r for r in khu_vuc_list if r in valid_regions]
        if filtered_regions and len(filtered_regions) < len(valid_regions):
            in_clause = ", ".join(f"'{r}'" for r in filtered_regions)
            conditions.append(f"KHU_VUC IN ({in_clause})")

    where_clause = f"\nWHERE {' AND '.join(conditions)}" if conditions else ""

    valid_sort_cols = {
        "MA_GIAO_DICH": "MA_GIAO_DICH",
        "DON_GIA": "DON_GIA",
        "THANH_TIEN": "SO_LUONG * DON_GIA",
        "SO_LUONG": "SO_LUONG",
        "THOI_GIAN": "THOI_GIAN",
    }
    col_sort = valid_sort_cols.get(sort_by, "MA_GIAO_DICH")
    order = "DESC" if sort_order.upper() == "DESC" else "ASC"
    safe_limit = max(1, min(100, int(limit)))
    safe_offset = max(0, int(offset))

    offset_clause = f" OFFSET {safe_offset}" if safe_offset > 0 else ""

    sql = f"""
SELECT 
    MA_GIAO_DICH,
    MA_KHACH_HANG,
    MA_SAN_PHAM,
    KHU_VUC,
    SO_LUONG,
    DON_GIA,
    SO_LUONG * DON_GIA AS THANH_TIEN,
    THOI_GIAN
FROM GIAO_DICH{where_clause}
ORDER BY {col_sort} {order}
LIMIT {safe_limit}{offset_clause};
""".strip()
    return sql


def build_count_transactions_query(
    search_keyword: str = "",
    khu_vuc_list: tuple[str, ...] | list[str] | None = None,
) -> str:
    """Đếm tổng số bản ghi thỏa mãn điều kiện lọc để tính tổng số trang."""
    conditions = []

    if search_keyword and search_keyword.strip():
        kw = search_keyword.strip().replace("'", "")
        if kw.upper().startswith("GD"):
            conditions.append(f"MA_GIAO_DICH = '{kw}'")
        elif kw.upper().startswith("KH"):
            conditions.append(f"MA_KHACH_HANG = '{kw}'")
        else:
            conditions.append(f"(MA_GIAO_DICH = '{kw}' OR MA_KHACH_HANG = '{kw}')")

    valid_regions = {"MIEN_NAM", "MIEN_BAC", "MIEN_TRUNG"}
    if khu_vuc_list:
        filtered_regions = [r for r in khu_vuc_list if r in valid_regions]
        if filtered_regions and len(filtered_regions) < len(valid_regions):
            in_clause = ", ".join(f"'{r}'" for r in filtered_regions)
            conditions.append(f"KHU_VUC IN ({in_clause})")

    where_clause = f"\nWHERE {' AND '.join(conditions)}" if conditions else ""
    return f"SELECT COUNT(*) AS TOTAL_ROWS FROM GIAO_DICH{where_clause};".strip()


# =============================================================================
# 3. TRUY VẤN DML (THÊM, CẬP NHẬT, XÓA)
# =============================================================================

def sql_check_record_exists(ma_giao_dich: str) -> str:
    """Kiểm tra sự tồn tại của Row Key trước khi thêm mới hoặc xóa."""
    clean_id = ma_giao_dich.strip().replace("'", "")
    return f"SELECT COUNT(*) AS CNT FROM GIAO_DICH WHERE MA_GIAO_DICH = '{clean_id}';"


def sql_get_record_by_id(ma_giao_dich: str) -> str:
    """Lấy dữ liệu chi tiết một bản ghi theo Row Key."""
    clean_id = ma_giao_dich.strip().replace("'", "")
    return f"""
SELECT 
    MA_GIAO_DICH,
    MA_KHACH_HANG,
    MA_SAN_PHAM,
    KHU_VUC,
    SO_LUONG,
    DON_GIA,
    SO_LUONG * DON_GIA AS THANH_TIEN,
    THOI_GIAN
FROM GIAO_DICH
WHERE MA_GIAO_DICH = '{clean_id}';
""".strip()


def sql_upsert_transaction(
    ma_giao_dich: str,
    ma_khach_hang: str,
    ma_san_pham: str,
    khu_vuc: str,
    so_luong: int,
    don_gia: float,
    thoi_gian: str,
) -> str:
    """Tạo câu lệnh UPSERT INTO kèm COMMIT tự động."""
    c_id = ma_giao_dich.strip().replace("'", "")
    c_kh = ma_khach_hang.strip().replace("'", "")
    c_sp = ma_san_pham.strip().replace("'", "")
    c_kv = khu_vuc.strip().replace("'", "")
    c_qty = int(so_luong)
    c_price = float(don_gia)
    c_time = thoi_gian.strip().replace("'", "")

    return f"""
UPSERT INTO GIAO_DICH (
    MA_GIAO_DICH,
    MA_KHACH_HANG,
    MA_SAN_PHAM,
    KHU_VUC,
    SO_LUONG,
    DON_GIA,
    THOI_GIAN
) VALUES (
    '{c_id}',
    '{c_kh}',
    '{c_sp}',
    '{c_kv}',
    {c_qty},
    {c_price:.2f},
    TO_TIMESTAMP('{c_time}', 'yyyy-MM-dd HH:mm:ss')
);
!commit;
""".strip()


def sql_delete_transaction(ma_giao_dich: str) -> str:
    """Tạo câu lệnh DELETE kèm COMMIT."""
    clean_id = ma_giao_dich.strip().replace("'", "")
    return f"""
DELETE FROM GIAO_DICH 
WHERE MA_GIAO_DICH = '{clean_id}';
!commit;
""".strip()


# =============================================================================
# 4. DANH MỤC 10 TRUY VẤN DEMO BÁO CÁO (QUERIES & STATISTICS)
# =============================================================================

DEMO_QUERIES = [
    {
        "id": 1,
        "title": "1. Truy vấn danh sách dữ liệu (Hiển thị dữ liệu mẫu)",
        "purpose": "Quét và lấy 20 bản ghi đầu tiên trong bảng GIAO_DICH để kiểm tra cấu trúc các cột dữ liệu.",
        "sql": """
SELECT MA_GIAO_DICH, MA_KHACH_HANG, MA_SAN_PHAM, KHU_VUC, SO_LUONG, DON_GIA, THOI_GIAN
FROM GIAO_DICH
LIMIT 20;
""".strip(),
    },
    {
        "id": 2,
        "title": "2. Lọc dữ liệu theo khu vực (Filter by Region)",
        "purpose": "Lọc các giao dịch phát sinh tại chi nhánh MIEN_NAM để phục vụ thống kê vùng miền.",
        "sql": """
SELECT MA_GIAO_DICH, MA_KHACH_HANG, MA_SAN_PHAM, KHU_VUC, SO_LUONG, DON_GIA
FROM GIAO_DICH
WHERE KHU_VUC = 'MIEN_NAM';
""".strip(),
    },
    {
        "id": 3,
        "title": "3. Lọc theo khoảng thời gian (Date-range Filtering)",
        "purpose": "Sử dụng toán tử BETWEEN và hàm TO_TIMESTAMP để lọc các giao dịch trong khoảng đầu tháng 03/2026.",
        "sql": """
SELECT MA_GIAO_DICH, MA_KHACH_HANG, KHU_VUC, THOI_GIAN
FROM GIAO_DICH
WHERE THOI_GIAN BETWEEN TO_TIMESTAMP('2026-03-01 00:00:00', 'yyyy-MM-dd HH:mm:ss')
                    AND TO_TIMESTAMP('2026-03-04 23:59:59', 'yyyy-MM-dd HH:mm:ss');
""".strip(),
    },
    {
        "id": 4,
        "title": "4. Tìm kiếm theo mã khách hàng (Customer Point Search)",
        "purpose": "Tra cứu lịch sử mua sắm và chi tiêu của khách hàng cụ thể (ví dụ: KH01).",
        "sql": """
SELECT MA_GIAO_DICH, MA_SAN_PHAM, KHU_VUC, SO_LUONG, DON_GIA, THOI_GIAN
FROM GIAO_DICH
WHERE MA_KHACH_HANG = 'KH01';
""".strip(),
    },
    {
        "id": 5,
        "title": "5. Tính tổng doanh thu toàn hệ thống (Total Revenue KPI)",
        "purpose": "Tính toán tổng doanh thu, số lượng bán ra và giá trị trung bình trên toàn bộ dữ liệu.",
        "sql": """
SELECT 
    COUNT(*) AS TONG_SO_GD,
    SUM(SO_LUONG) AS TONG_SAN_PHAM,
    SUM(SO_LUONG * DON_GIA) AS TONG_DOANH_THU,
    AVG(SO_LUONG * DON_GIA) AS DOANH_THU_TRUNG_BINH
FROM GIAO_DICH;
""".strip(),
    },
    {
        "id": 6,
        "title": "6. Thống kê theo khu vực (Group By Region)",
        "purpose": "Gom nhóm dữ liệu theo từng khu vực để so sánh tổng doanh thu và sản lượng bán ra.",
        "sql": """
SELECT 
    KHU_VUC,
    COUNT(*) AS SO_GIAO_DICH,
    SUM(SO_LUONG) AS TONG_SAN_PHAM,
    SUM(SO_LUONG * DON_GIA) AS TONG_DOANH_THU
FROM GIAO_DICH
GROUP BY KHU_VUC
ORDER BY TONG_DOANH_THU DESC;
""".strip(),
    },
    {
        "id": 7,
        "title": "7. Thống kê theo sản phẩm (Top Selling Products)",
        "purpose": "Tìm ra danh sách 5 sản phẩm bán chạy nhất tính theo tổng số lượng bán ra.",
        "sql": """
SELECT 
    MA_SAN_PHAM, 
    SUM(SO_LUONG) AS TONG_SO_LUONG_BAN
FROM GIAO_DICH
GROUP BY MA_SAN_PHAM
ORDER BY TONG_SO_LUONG_BAN DESC
LIMIT 5;
""".strip(),
    },
    {
        "id": 8,
        "title": "8. Sắp xếp và giới hạn kết quả (Order By & Limit Top Values)",
        "purpose": "Tính thành tiền (SO_LUONG * DON_GIA) và trích xuất 5 giao dịch có giá trị đơn hàng lớn nhất.",
        "sql": """
SELECT 
    MA_GIAO_DICH,
    MA_KHACH_HANG,
    MA_SAN_PHAM,
    KHU_VUC,
    SO_LUONG,
    DON_GIA,
    SO_LUONG * DON_GIA AS THANH_TIEN
FROM GIAO_DICH
ORDER BY THANH_TIEN DESC
LIMIT 5;
""".strip(),
    },
    {
        "id": 9,
        "title": "9. Truy vấn nhóm với GROUP BY & HAVING (High Revenue Regions)",
        "purpose": "Lọc các khu vực có doanh thu vượt mức ngưỡng 100.000.000 VNĐ bằng mệnh đề HAVING.",
        "sql": """
SELECT 
    KHU_VUC,
    COUNT(*) AS SO_GIAO_DICH,
    SUM(SO_LUONG * DON_GIA) AS TONG_DOANH_THU
FROM GIAO_DICH
GROUP BY KHU_VUC
HAVING SUM(SO_LUONG * DON_GIA) > 100000000.00
ORDER BY TONG_DOANH_THU DESC;
""".strip(),
    },
    {
        "id": 10,
        "title": "10. Truy vấn kiểm tra trước và sau khi tạo Index (EXPLAIN Plan)",
        "purpose": "Phân tích kế hoạch thực thi để chứng minh Phoenix chuyển đổi từ Full Scan sang Range Scan khi có Index.",
        "sql": """
EXPLAIN
SELECT MA_GIAO_DICH, KHU_VUC, SO_LUONG, DON_GIA
FROM GIAO_DICH
WHERE KHU_VUC = 'MIEN_NAM';
""".strip(),
    },
]


# =============================================================================
# 5. TRUY VẤN INDEX VÀ EXPLAIN (COVERED SECONDARY INDEX)
# =============================================================================

SQL_EXPLAIN_WITHOUT_INDEX = """
EXPLAIN
SELECT /*+ NO_INDEX */
    MA_GIAO_DICH,
    KHU_VUC,
    SO_LUONG,
    DON_GIA
FROM GIAO_DICH
WHERE KHU_VUC = 'MIEN_NAM';
""".strip()

SQL_CREATE_COVERED_INDEX = """
CREATE INDEX IF NOT EXISTS IDX_GIAO_DICH_KHU_VUC
ON GIAO_DICH (KHU_VUC)
INCLUDE (
    MA_KHACH_HANG,
    MA_SAN_PHAM,
    SO_LUONG,
    DON_GIA,
    THOI_GIAN
);
""".strip()

SQL_DROP_INDEX = """
DROP INDEX IF EXISTS IDX_GIAO_DICH_KHU_VUC ON GIAO_DICH;
""".strip()

SQL_EXPLAIN_WITH_INDEX_HINT = """
EXPLAIN
SELECT /*+ INDEX(GIAO_DICH IDX_GIAO_DICH_KHU_VUC) */
    MA_GIAO_DICH,
    KHU_VUC,
    SO_LUONG,
    DON_GIA
FROM GIAO_DICH
WHERE KHU_VUC = 'MIEN_NAM';
""".strip()

SQL_BENCHMARK_NO_INDEX = """
SELECT /*+ NO_INDEX */
    MA_GIAO_DICH, KHU_VUC, SO_LUONG, DON_GIA, THOI_GIAN
FROM GIAO_DICH
WHERE KHU_VUC = 'MIEN_NAM'
LIMIT 20;
""".strip()

SQL_BENCHMARK_WITH_INDEX = """
SELECT /*+ INDEX(GIAO_DICH IDX_GIAO_DICH_KHU_VUC) */
    MA_GIAO_DICH, KHU_VUC, SO_LUONG, DON_GIA, THOI_GIAN
FROM GIAO_DICH
WHERE KHU_VUC = 'MIEN_NAM'
LIMIT 20;
""".strip()

SQL_BENCHMARK_POINT_LOOKUP = """
SELECT * FROM GIAO_DICH WHERE MA_GIAO_DICH = 'GD001';
""".strip()
