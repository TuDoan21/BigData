"""
=============================================================================
MODULE: queries.py
MỤC ĐÍCH: Tập trung toàn bộ câu truy vấn SQL Apache Phoenix chuẩn hóa.
- Phù hợp với các script trong thư mục sql/ (01 đến 07).
- Hỗ trợ xây dựng câu lệnh an toàn (parameterized logic / input validation).
=============================================================================
"""

TABLE_NAME = "GIAO_DICH"
INDEX_NAME = "IDX_GIAO_DICH_KHU_VUC"

# Schema chuẩn cho bảng GIAO_DICH
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
# 1. TRUY VẤN TRANG TỔNG QUAN (OVERVIEW)
# =============================================================================

SQL_OVERVIEW_KPI = """
SELECT 
    COUNT(*) AS TONG_GIAO_DICH,
    SUM(SO_LUONG * DON_GIA) AS TONG_DOANH_THU,
    AVG(SO_LUONG * DON_GIA) AS GIA_TRI_TRUNG_BINH,
    COUNT(DISTINCT KHU_VUC) AS SO_KHU_VUC
FROM GIAO_DICH;
""".strip()

SQL_OVERVIEW_CHART = """
SELECT 
    KHU_VUC,
    COUNT(*) AS SO_GIAO_DICH,
    SUM(SO_LUONG * DON_GIA) AS TONG_DOANH_THU
FROM GIAO_DICH
GROUP BY KHU_VUC
ORDER BY TONG_DOANH_THU DESC;
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
ORDER BY MA_GIAO_DICH
LIMIT 10;
""".strip()


def get_overview_batch_sql() -> list[str]:
    """Trả về danh sách các câu truy vấn trang tổng quan để chạy trong 1 phiên SQLLine duy nhất."""
    return [SQL_OVERVIEW_KPI, SQL_OVERVIEW_CHART, SQL_OVERVIEW_TOP10]


# =============================================================================
# 2. BUILDER TRANG TRUY VẤN DỮ LIỆU (SELECT QUERIES)
# =============================================================================

def build_search_query(
    ma_giao_dich: str = "",
    khu_vuc_list: list[str] | None = None,
    min_don_gia: float | None = None,
    max_don_gia: float | None = None,
    start_time: str = "",
    end_time: str = "",
    sort_by: str = "MA_GIAO_DICH",
    sort_order: str = "ASC",
    limit: int = 20,
) -> str:
    """
    Sinh câu lệnh SQL tìm kiếm và lọc dữ liệu an toàn dựa trên tham số đầu vào.
    Hỗ trợ tính toán THANH_TIEN = SO_LUONG * DON_GIA.
    """
    conditions = []

    # 1. Tìm chính xác Row Key (Point Lookup)
    if ma_giao_dich and ma_giao_dich.strip():
        clean_id = ma_giao_dich.strip().replace("'", "")
        conditions.append(f"MA_GIAO_DICH = '{clean_id}'")

    # 2. Lọc danh sách khu vực bằng toán tử IN
    valid_regions = {"MIEN_NAM", "MIEN_BAC", "MIEN_TRUNG"}
    if khu_vuc_list:
        filtered_regions = [r for r in khu_vuc_list if r in valid_regions]
        if filtered_regions:
            in_clause = ", ".join(f"'{r}'" for r in filtered_regions)
            conditions.append(f"KHU_VUC IN ({in_clause})")

    # 3. Lọc khoảng đơn giá
    if min_don_gia is not None and min_don_gia > 0:
        conditions.append(f"DON_GIA >= {float(min_don_gia):.2f}")
    if max_don_gia is not None and max_don_gia > 0:
        conditions.append(f"DON_GIA <= {float(max_don_gia):.2f}")

    # 4. Lọc khoảng thời gian (BETWEEN hoặc >= <=)
    if start_time and end_time:
        conditions.append(
            f"THOI_GIAN BETWEEN TO_TIMESTAMP('{start_time}', 'yyyy-MM-dd HH:mm:ss') "
            f"AND TO_TIMESTAMP('{end_time}', 'yyyy-MM-dd HH:mm:ss')"
        )
    elif start_time:
        conditions.append(f"THOI_GIAN >= TO_TIMESTAMP('{start_time}', 'yyyy-MM-dd HH:mm:ss')")
    elif end_time:
        conditions.append(f"THOI_GIAN <= TO_TIMESTAMP('{end_time}', 'yyyy-MM-dd HH:mm:ss')")

    where_clause = f"\nWHERE {' AND '.join(conditions)}" if conditions else ""

    # Xác định biểu thức sắp xếp
    valid_sort_cols = {
        "MA_GIAO_DICH": "MA_GIAO_DICH",
        "DON_GIA": "DON_GIA",
        "THANH_TIEN": "SO_LUONG * DON_GIA",
        "SO_LUONG": "SO_LUONG",
        "THOI_GIAN": "THOI_GIAN",
    }
    col_sort = valid_sort_cols.get(sort_by, "MA_GIAO_DICH")
    order = "DESC" if sort_order.upper() == "DESC" else "ASC"

    # Giới hạn số dòng
    safe_limit = max(1, min(100, int(limit)))

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
LIMIT {safe_limit};
""".strip()
    return sql


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
# 4. TRUY VẤN THỐNG KÊ (AGGREGATE QUERIES)
# =============================================================================

SQL_AGGREGATE_REGION = """
SELECT 
    KHU_VUC,
    COUNT(*) AS SO_GIAO_DICH,
    SUM(SO_LUONG) AS TONG_SO_LUONG,
    SUM(SO_LUONG * DON_GIA) AS TONG_DOANH_THU
FROM GIAO_DICH
GROUP BY KHU_VUC
ORDER BY TONG_DOANH_THU DESC;
""".strip()

SQL_AGGREGATE_TOP_PRODUCTS = """
SELECT 
    MA_SAN_PHAM,
    SUM(SO_LUONG) AS TONG_SO_LUONG
FROM GIAO_DICH
GROUP BY MA_SAN_PHAM
ORDER BY TONG_SO_LUONG DESC
LIMIT 5;
""".strip()

SQL_AGGREGATE_TOP_CUSTOMERS = """
SELECT 
    MA_KHACH_HANG,
    SUM(SO_LUONG * DON_GIA) AS TONG_GIA_TRI
FROM GIAO_DICH
GROUP BY MA_KHACH_HANG
ORDER BY TONG_GIA_TRI DESC
LIMIT 5;
""".strip()


# =============================================================================
# 5. TRUY VẤN INDEX & EXPLAIN
# =============================================================================

SQL_EXPLAIN_WITHOUT_INDEX = """
EXPLAIN
SELECT 
    MA_GIAO_DICH,
    KHU_VUC,
    SO_LUONG,
    DON_GIA
FROM GIAO_DICH
WHERE KHU_VUC = 'MIEN_NAM';
""".strip()

SQL_CREATE_COVERED_INDEX = """
CREATE INDEX IDX_GIAO_DICH_KHU_VUC
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
