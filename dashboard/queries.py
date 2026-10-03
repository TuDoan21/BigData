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
CREATE TABLE IF NOT EXISTS GIAO_DICH (
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


def get_super_batch_overview_sql(scope: str = "ALL") -> list[str]:
    """
    Trả về toàn bộ 6 câu truy vấn của trang Tổng quan để chạy trong ĐÚNG 1 phiên SQLLine.
    Hỗ trợ tách biệt:
    - 'VN': Thị trường Việt Nam (MIEN_BAC, MIEN_TRUNG, MIEN_NAM)
    - 'INTL': Thị trường Quốc tế (Archive Dataset - E-Commerce)
    - 'ALL': Toàn bộ dữ liệu
    """
    where_clause = ""
    if scope == "VN":
        where_clause = "WHERE KHU_VUC IN ('MIEN_BAC', 'MIEN_TRUNG', 'MIEN_NAM')"
    elif scope == "INTL":
        where_clause = "WHERE KHU_VUC NOT IN ('MIEN_BAC', 'MIEN_TRUNG', 'MIEN_NAM')"

    chk_table = f"SELECT 1 AS TONG_SO FROM GIAO_DICH {where_clause} LIMIT 1;".strip()
    chk_indexes = SQL_OVERVIEW_CHECK_INDEXES

    kpi = f"""
SELECT 
    COUNT(*) AS TONG_GIAO_DICH,
    COUNT(DISTINCT MA_KHACH_HANG) AS TONG_KHACH_HANG,
    SUM(SO_LUONG * DON_GIA) AS TONG_DOANH_THU,
    AVG(SO_LUONG * DON_GIA) AS GIA_TRI_TRUNG_BINH,
    COUNT(DISTINCT KHU_VUC) AS SO_KHU_VUC
FROM GIAO_DICH {where_clause};
""".strip()

    chart_region = f"""
SELECT 
    KHU_VUC,
    COUNT(*) AS SO_GIAO_DICH,
    SUM(SO_LUONG * DON_GIA) AS TONG_DOANH_THU
FROM GIAO_DICH {where_clause}
GROUP BY KHU_VUC
ORDER BY TONG_DOANH_THU DESC
LIMIT 10;
""".strip()

    timeline = f"""
SELECT 
    TO_CHAR(THOI_GIAN, 'yyyy-MM-dd') AS NGAY_GIAO_DICH,
    COUNT(*) AS SO_GIAO_DICH,
    SUM(SO_LUONG * DON_GIA) AS DOANH_THU_NGAY
FROM GIAO_DICH {where_clause}
GROUP BY TO_CHAR(THOI_GIAN, 'yyyy-MM-dd')
ORDER BY NGAY_GIAO_DICH ASC;
""".strip()

    top10 = f"""
SELECT 
    MA_GIAO_DICH,
    MA_KHACH_HANG,
    MA_SAN_PHAM,
    KHU_VUC,
    SO_LUONG,
    DON_GIA,
    THOI_GIAN
FROM GIAO_DICH {where_clause}
ORDER BY THOI_GIAN DESC
LIMIT 10;
""".strip()

    return [chk_table, chk_indexes, kpi, chart_region, timeline, top10]


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
    market_scope: str = "ALL",
) -> str:
    """
    Sinh câu lệnh SQL tìm kiếm và phân trang trực tiếp trên database.
    Hỗ trợ lọc theo phạm vi thị trường: 'VN', 'INTL', hoặc 'ALL'.
    """
    conditions = []

    if market_scope == "VN":
        conditions.append("KHU_VUC IN ('MIEN_BAC', 'MIEN_TRUNG', 'MIEN_NAM')")
    elif market_scope == "INTL":
        conditions.append("KHU_VUC NOT IN ('MIEN_BAC', 'MIEN_TRUNG', 'MIEN_NAM')")

    if search_keyword and search_keyword.strip():
        kw = search_keyword.strip().replace("'", "")
        conditions.append(f"(MA_GIAO_DICH = '{kw}' OR MA_KHACH_HANG = '{kw}' OR MA_SAN_PHAM = '{kw}')")

    if khu_vuc_list:
        clean_regions = [r.strip().replace("'", "") for r in khu_vuc_list if r and str(r).strip() and str(r).strip() != "Tất cả"]
        if clean_regions:
            in_clause = ", ".join(f"'{r}'" for r in clean_regions)
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
    market_scope: str = "ALL",
) -> str:
    """Đếm tổng số bản ghi thỏa mãn điều kiện lọc và thị trường để tính tổng số trang."""
    conditions = []

    if market_scope == "VN":
        conditions.append("KHU_VUC IN ('MIEN_BAC', 'MIEN_TRUNG', 'MIEN_NAM')")
    elif market_scope == "INTL":
        conditions.append("KHU_VUC NOT IN ('MIEN_BAC', 'MIEN_TRUNG', 'MIEN_NAM')")

    if search_keyword and search_keyword.strip():
        kw = search_keyword.strip().replace("'", "")
        conditions.append(f"(MA_GIAO_DICH = '{kw}' OR MA_KHACH_HANG = '{kw}' OR MA_SAN_PHAM = '{kw}')")

    if khu_vuc_list:
        clean_regions = [r.strip().replace("'", "") for r in khu_vuc_list if r and str(r).strip() and str(r).strip() != "Tất cả"]
        if clean_regions:
            in_clause = ", ".join(f"'{r}'" for r in clean_regions)
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
    """Tạo câu lệnh UPSERT INTO chuẩn ANSI Phoenix SQL (tự động commit qua kết nối)."""
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
""".strip()


def sql_delete_transaction(ma_giao_dich: str) -> str:
    """Tạo câu lệnh DELETE chuẩn Phoenix SQL."""
    clean_id = ma_giao_dich.strip().replace("'", "")
    return f"DELETE FROM GIAO_DICH WHERE MA_GIAO_DICH = '{clean_id}';"


# =============================================================================
# 4. DANH MỤC 10 TRUY VẤN DEMO BÁO CÁO (TÁCH BIỆT VN & QUỐC TẾ)
# =============================================================================

SAMPLE_QUERIES_VN = [
    {
        "id": 1,
        "title": "1. Danh sách 20 giao dịch thị trường Việt Nam",
        "purpose": "Quét và lấy 20 bản ghi đầu tiên phát sinh tại thị trường nội địa (MIEN_BAC, MIEN_TRUNG, MIEN_NAM).",
        "sql": """
SELECT MA_GIAO_DICH, MA_KHACH_HANG, MA_SAN_PHAM, KHU_VUC, SO_LUONG, DON_GIA, THOI_GIAN
FROM GIAO_DICH
WHERE KHU_VUC IN ('MIEN_BAC', 'MIEN_TRUNG', 'MIEN_NAM')
LIMIT 20;
""".strip(),
    },
    {
        "id": 2,
        "title": "2. Lọc giao dịch chi nhánh MIEN_NAM",
        "purpose": "Lọc các giao dịch phát sinh tại chi nhánh MIEN_NAM với đơn giá tiền Việt (VNĐ).",
        "sql": """
SELECT MA_GIAO_DICH, MA_KHACH_HANG, MA_SAN_PHAM, KHU_VUC, SO_LUONG, DON_GIA
FROM GIAO_DICH
WHERE KHU_VUC = 'MIEN_NAM';
""".strip(),
    },
    {
        "id": 3,
        "title": "3. Lọc theo khoảng thời gian đầu năm 2026 (Quý 1)",
        "purpose": "Sử dụng toán tử BETWEEN và hàm TO_TIMESTAMP để lọc giao dịch nội địa quý 1 năm 2026.",
        "sql": """
SELECT MA_GIAO_DICH, MA_KHACH_HANG, KHU_VUC, THOI_GIAN
FROM GIAO_DICH
WHERE KHU_VUC IN ('MIEN_BAC', 'MIEN_TRUNG', 'MIEN_NAM')
  AND THOI_GIAN BETWEEN TO_TIMESTAMP('2026-01-01 00:00:00', 'yyyy-MM-dd HH:mm:ss')
                    AND TO_TIMESTAMP('2026-03-31 23:59:59', 'yyyy-MM-dd HH:mm:ss')
LIMIT 50;
""".strip(),
    },
    {
        "id": 4,
        "title": "4. Tìm kiếm theo mã khách hàng nội địa (KH_17850 / KH_13047)",
        "purpose": "Tra cứu lịch sử mua sắm và chi tiêu của khách hàng nội địa cụ thể.",
        "sql": """
SELECT MA_GIAO_DICH, MA_SAN_PHAM, KHU_VUC, SO_LUONG, DON_GIA, THOI_GIAN
FROM GIAO_DICH
WHERE MA_KHACH_HANG IN ('KH_17850', 'KH_13047', 'KH_12583', 'KH_13748');
""".strip(),
    },
    {
        "id": 5,
        "title": "5. Tổng doanh thu toàn thị trường Việt Nam (VNĐ)",
        "purpose": "Tính toán tổng doanh thu, số lượng sản phẩm bán ra của 3 miền Việt Nam.",
        "sql": """
SELECT 
    COUNT(*) AS TONG_SO_GD,
    SUM(SO_LUONG) AS TONG_SAN_PHAM,
    SUM(SO_LUONG * DON_GIA) AS TONG_DOANH_THU_VND,
    AVG(SO_LUONG * DON_GIA) AS DOANH_THU_TRUNG_BINH_VND
FROM GIAO_DICH
WHERE KHU_VUC IN ('MIEN_BAC', 'MIEN_TRUNG', 'MIEN_NAM');
""".strip(),
    },
    {
        "id": 6,
        "title": "6. Thống kê doanh thu theo 3 miền (Group By Vùng Miền)",
        "purpose": "Gom nhóm dữ liệu theo từng miền để so sánh tổng doanh thu và sản lượng bán ra.",
        "sql": """
SELECT 
    KHU_VUC,
    COUNT(*) AS SO_GIAO_DICH,
    SUM(SO_LUONG) AS TONG_SAN_PHAM,
    SUM(SO_LUONG * DON_GIA) AS TONG_DOANH_THU_VND
FROM GIAO_DICH
WHERE KHU_VUC IN ('MIEN_BAC', 'MIEN_TRUNG', 'MIEN_NAM')
GROUP BY KHU_VUC
ORDER BY TONG_DOANH_THU_VND DESC;
""".strip(),
    },
    {
        "id": 7,
        "title": "7. Thống kê sản phẩm bán chạy nhất Việt Nam (85123A, 71053...)",
        "purpose": "Tìm ra danh sách các mặt hàng có sản lượng bán cao nhất.",
        "sql": """
SELECT 
    MA_SAN_PHAM, 
    SUM(SO_LUONG) AS TONG_SO_LUONG_BAN,
    SUM(SO_LUONG * DON_GIA) AS DOANH_THU_SAN_PHAM
FROM GIAO_DICH
WHERE KHU_VUC IN ('MIEN_BAC', 'MIEN_TRUNG', 'MIEN_NAM')
GROUP BY MA_SAN_PHAM
ORDER BY TONG_SO_LUONG_BAN DESC;
""".strip(),
    },
    {
        "id": 8,
        "title": "8. Top 5 giao dịch có giá trị đơn hàng lớn nhất (VNĐ)",
        "purpose": "Tính thành tiền (SO_LUONG * DON_GIA) và trích xuất 5 giao dịch quy mô lớn nhất.",
        "sql": """
SELECT 
    MA_GIAO_DICH,
    MA_KHACH_HANG,
    MA_SAN_PHAM,
    KHU_VUC,
    SO_LUONG,
    DON_GIA,
    SO_LUONG * DON_GIA AS THANH_TIEN_VND
FROM GIAO_DICH
WHERE KHU_VUC IN ('MIEN_BAC', 'MIEN_TRUNG', 'MIEN_NAM')
ORDER BY THANH_TIEN_VND DESC
LIMIT 5;
""".strip(),
    },
    {
        "id": 9,
        "title": "9. Lọc khu vực có doanh thu vượt 100 triệu VNĐ (HAVING)",
        "purpose": "Lọc các vùng có doanh thu đạt chỉ tiêu lớn bằng mệnh đề HAVING.",
        "sql": """
SELECT 
    KHU_VUC,
    COUNT(*) AS SO_GIAO_DICH,
    SUM(SO_LUONG * DON_GIA) AS TONG_DOANH_THU_VND
FROM GIAO_DICH
WHERE KHU_VUC IN ('MIEN_BAC', 'MIEN_TRUNG', 'MIEN_NAM')
GROUP BY KHU_VUC
HAVING SUM(SO_LUONG * DON_GIA) > 100000000.00
ORDER BY TONG_DOANH_THU_VND DESC;
""".strip(),
    },
    {
        "id": 10,
        "title": "10. Kế hoạch thực thi EXPLAIN Plan trên vùng MIEN_NAM",
        "purpose": "Phân tích kế hoạch thực thi để chứng minh Phoenix sử dụng Index Range Scan cho dữ liệu nội địa.",
        "sql": """
EXPLAIN
SELECT MA_GIAO_DICH, KHU_VUC, SO_LUONG, DON_GIA
FROM GIAO_DICH
WHERE KHU_VUC = 'MIEN_NAM';
""".strip(),
    },
]

SAMPLE_QUERIES_INTL = [
    {
        "id": 1,
        "title": "1. Danh sách 20 giao dịch bán lẻ quốc tế (Online Retail)",
        "purpose": "Quét và lấy 20 bản ghi đầu tiên trong tập dữ liệu e-commerce quốc tế từ archive/data.csv.",
        "sql": """
SELECT MA_GIAO_DICH, MA_KHACH_HANG, MA_SAN_PHAM, KHU_VUC, SO_LUONG, DON_GIA, THOI_GIAN
FROM GIAO_DICH
WHERE KHU_VUC NOT IN ('MIEN_BAC', 'MIEN_TRUNG', 'MIEN_NAM')
LIMIT 20;
""".strip(),
    },
    {
        "id": 2,
        "title": "2. Lọc đơn hàng tại thị trường United Kingdom",
        "purpose": "Lọc các giao dịch phát sinh tại thị trường bán lẻ chính United Kingdom.",
        "sql": """
SELECT MA_GIAO_DICH, MA_KHACH_HANG, MA_SAN_PHAM, KHU_VUC, SO_LUONG, DON_GIA
FROM GIAO_DICH
WHERE KHU_VUC = 'United Kingdom'
LIMIT 50;
""".strip(),
    },
    {
        "id": 3,
        "title": "3. Lọc theo tuần lễ bán hàng đầu tiên (Tháng 12/2010)",
        "purpose": "Sử dụng toán tử BETWEEN để lọc các giao dịch trong tuần đầu tiên từ ngày 01/12/2010.",
        "sql": """
SELECT MA_GIAO_DICH, MA_KHACH_HANG, KHU_VUC, SO_LUONG, DON_GIA, THOI_GIAN
FROM GIAO_DICH
WHERE KHU_VUC NOT IN ('MIEN_BAC', 'MIEN_TRUNG', 'MIEN_NAM')
  AND THOI_GIAN BETWEEN TO_TIMESTAMP('2010-12-01 00:00:00', 'yyyy-MM-dd HH:mm:ss')
                    AND TO_TIMESTAMP('2010-12-07 23:59:59', 'yyyy-MM-dd HH:mm:ss')
LIMIT 50;
""".strip(),
    },
    {
        "id": 4,
        "title": "4. Tra cứu lịch sử khách hàng quốc tế VIP (KH_17850)",
        "purpose": "Truy vấn điểm (Point Lookup) toàn bộ các mặt hàng được mua bởi khách hàng thường xuyên KH_17850.",
        "sql": """
SELECT MA_GIAO_DICH, MA_SAN_PHAM, KHU_VUC, SO_LUONG, DON_GIA, THOI_GIAN
FROM GIAO_DICH
WHERE MA_KHACH_HANG = 'KH_17850'
LIMIT 50;
""".strip(),
    },
    {
        "id": 5,
        "title": "5. Tổng doanh thu bán lẻ thương mại quốc tế (VNĐ)",
        "purpose": "Tổng hợp doanh số, sản lượng và giá trị trung bình mỗi dòng đơn hàng quốc tế theo tiền Việt Nam.",
        "sql": """
SELECT 
    COUNT(*) AS TONG_SO_GD,
    SUM(SO_LUONG) AS TONG_SAN_PHAM,
    SUM(SO_LUONG * DON_GIA) AS TONG_DOANH_THU_VND,
    AVG(SO_LUONG * DON_GIA) AS GIA_TRI_TRUNG_BINH_VND
FROM GIAO_DICH
WHERE KHU_VUC NOT IN ('MIEN_BAC', 'MIEN_TRUNG', 'MIEN_NAM');
""".strip(),
    },
    {
        "id": 6,
        "title": "6. Doanh thu theo từng quốc gia (Top Markets)",
        "purpose": "Gom nhóm theo quốc gia để xếp hạng các thị trường xuất khẩu / mua sắm nhiều nhất.",
        "sql": """
SELECT 
    KHU_VUC,
    COUNT(*) AS SO_GIAO_DICH,
    SUM(SO_LUONG) AS TONG_SAN_PHAM,
    SUM(SO_LUONG * DON_GIA) AS TONG_DOANH_THU_VND
FROM GIAO_DICH
WHERE KHU_VUC NOT IN ('MIEN_BAC', 'MIEN_TRUNG', 'MIEN_NAM')
GROUP BY KHU_VUC
ORDER BY TONG_DOANH_THU_VND DESC;
""".strip(),
    },
    {
        "id": 7,
        "title": "7. Top 10 mã sản phẩm bán chạy nhất quốc tế (StockCode)",
        "purpose": "Tìm ra 10 mã hàng hóa được đặt mua với số lượng lớn nhất.",
        "sql": """
SELECT 
    MA_SAN_PHAM, 
    SUM(SO_LUONG) AS TONG_SO_LUONG_BAN,
    COUNT(*) AS SO_LAN_DAT_HANG
FROM GIAO_DICH
WHERE KHU_VUC NOT IN ('MIEN_BAC', 'MIEN_TRUNG', 'MIEN_NAM')
GROUP BY MA_SAN_PHAM
ORDER BY TONG_SO_LUONG_BAN DESC
LIMIT 10;
""".strip(),
    },
    {
        "id": 8,
        "title": "8. Top 10 đơn hàng giá trị cao nhất (VNĐ)",
        "purpose": "Trích xuất 10 dòng giao dịch bán buôn / bán lẻ có thành tiền cao nhất (VNĐ).",
        "sql": """
SELECT 
    MA_GIAO_DICH,
    MA_KHACH_HANG,
    MA_SAN_PHAM,
    KHU_VUC,
    SO_LUONG,
    DON_GIA,
    SO_LUONG * DON_GIA AS THANH_TIEN_VND
FROM GIAO_DICH
WHERE KHU_VUC NOT IN ('MIEN_BAC', 'MIEN_TRUNG', 'MIEN_NAM')
ORDER BY THANH_TIEN_VND DESC
LIMIT 10;
""".strip(),
    },
    {
        "id": 9,
        "title": "9. Lọc các quốc gia có doanh số trên 50 triệu VNĐ (HAVING)",
        "purpose": "Phân khúc thị trường tiềm năng có doanh thu đạt ngưỡng lớn bằng mệnh đề HAVING.",
        "sql": """
SELECT 
    KHU_VUC,
    COUNT(*) AS SO_GIAO_DICH,
    SUM(SO_LUONG * DON_GIA) AS TONG_DOANH_THU_VND
FROM GIAO_DICH
WHERE KHU_VUC NOT IN ('MIEN_BAC', 'MIEN_TRUNG', 'MIEN_NAM')
GROUP BY KHU_VUC
HAVING SUM(SO_LUONG * DON_GIA) > 50000000.00
ORDER BY TONG_DOANH_THU_VND DESC;
""".strip(),
    },
    {
        "id": 10,
        "title": "10. Kế hoạch thực thi EXPLAIN Plan trên tập dữ liệu quốc tế",
        "purpose": "Đối chiếu việc sử dụng Covered Secondary Index trên tập dữ liệu 5.000 dòng quốc tế.",
        "sql": """
EXPLAIN
SELECT MA_GIAO_DICH, KHU_VUC, SO_LUONG, DON_GIA
FROM GIAO_DICH
WHERE KHU_VUC = 'United Kingdom';
""".strip(),
    },
]

DEMO_QUERIES = SAMPLE_QUERIES_VN
SAMPLE_QUERIES = SAMPLE_QUERIES_VN


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
WHERE KHU_VUC = 'United Kingdom';
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
WHERE KHU_VUC = 'United Kingdom';
""".strip()

SQL_BENCHMARK_NO_INDEX = """
SELECT /*+ NO_INDEX */
    MA_GIAO_DICH, KHU_VUC, SO_LUONG, DON_GIA, THOI_GIAN
FROM GIAO_DICH
WHERE KHU_VUC = 'United Kingdom'
LIMIT 20;
""".strip()

SQL_BENCHMARK_WITH_INDEX = """
SELECT /*+ INDEX(GIAO_DICH IDX_GIAO_DICH_KHU_VUC) */
    MA_GIAO_DICH, KHU_VUC, SO_LUONG, DON_GIA, THOI_GIAN
FROM GIAO_DICH
WHERE KHU_VUC = 'United Kingdom'
LIMIT 20;
""".strip()

SQL_BENCHMARK_POINT_LOOKUP = """
SELECT * FROM GIAO_DICH WHERE MA_GIAO_DICH = 'TX_0000200';
""".strip()

# =============================================================================
# 6. TRUY VẤN METADATA SYSTEM.CATALOG (PHOENIX SYSTEM CATALOG)
# =============================================================================

SQL_METADATA_COLUMNS = """
SELECT COLUMN_NAME, DATA_TYPE, COLUMN_SIZE, NULLABLE, ORDINAL_POSITION, KEY_SEQ
FROM SYSTEM.CATALOG
WHERE TABLE_NAME = 'GIAO_DICH' AND COLUMN_NAME IS NOT NULL
ORDER BY ORDINAL_POSITION;
""".strip()

SQL_METADATA_TABLE_PROPERTIES = """
SELECT TABLE_NAME, TABLE_TYPE, SALT_BUCKETS, COLUMN_COUNT, PK_NAME
FROM SYSTEM.CATALOG
WHERE TABLE_NAME = 'GIAO_DICH' AND COLUMN_NAME IS NULL;
""".strip()

SQL_METADATA_SYSTEM_TABLES = """
SELECT TABLE_NAME, TABLE_TYPE, SALT_BUCKETS
FROM SYSTEM.CATALOG
WHERE COLUMN_NAME IS NULL
ORDER BY TABLE_TYPE, TABLE_NAME;
""".strip()

