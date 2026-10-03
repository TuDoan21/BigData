-- =============================================================================
-- SCRIPT: 03_select_queries.sql
-- MỤC ĐÍCH: Các câu lệnh truy vấn lọc, sắp xếp, tính toán cơ bản và nâng cao
-- =============================================================================

-- 1. Hiển thị toàn bộ dữ liệu trong bảng
SELECT * 
FROM GIAO_DICH;

-- 2. Tìm kiếm chính xác theo mã giao dịch (Truy vấn Point Lookup theo Row Key)
SELECT * 
FROM GIAO_DICH 
WHERE MA_GIAO_DICH = 'TX_0000001';

-- 3. Lọc theo khu vực (Ví dụ: MIEN_NAM)
SELECT MA_GIAO_DICH, MA_KHACH_HANG, MA_SAN_PHAM, KHU_VUC, SO_LUONG, DON_GIA
FROM GIAO_DICH
WHERE KHU_VUC = 'MIEN_NAM';

-- 4. Lọc theo khách hàng cụ thể (Ví dụ: KH_17850)
SELECT MA_GIAO_DICH, MA_SAN_PHAM, KHU_VUC, SO_LUONG, DON_GIA, THOI_GIAN
FROM GIAO_DICH
WHERE MA_KHACH_HANG = 'KH_17850';

-- 5. Lọc theo sản phẩm (Ví dụ: 71053)
SELECT MA_GIAO_DICH, MA_KHACH_HANG, KHU_VUC, SO_LUONG, DON_GIA
FROM GIAO_DICH
WHERE MA_SAN_PHAM = '71053';

-- 6. Lọc theo khoảng đơn giá từ 5.000.000 đến 20.000.000
SELECT MA_GIAO_DICH, MA_SAN_PHAM, DON_GIA
FROM GIAO_DICH
WHERE DON_GIA >= 5000000.00 AND DON_GIA <= 20000000.00;

-- 7. Lọc theo khoảng thời gian bằng toán tử BETWEEN
SELECT MA_GIAO_DICH, MA_KHACH_HANG, KHU_VUC, THOI_GIAN
FROM GIAO_DICH
WHERE THOI_GIAN BETWEEN TO_TIMESTAMP('2026-03-01 00:00:00', 'yyyy-MM-dd HH:mm:ss')
                    AND TO_TIMESTAMP('2026-03-04 23:59:59', 'yyyy-MM-dd HH:mm:ss');

-- 8. Sắp xếp đơn giá tăng dần (ASC) với LIMIT 5
SELECT MA_GIAO_DICH, MA_SAN_PHAM, DON_GIA
FROM GIAO_DICH
ORDER BY DON_GIA ASC
LIMIT 5;

-- 9. Sắp xếp đơn giá giảm dần (DESC) với LIMIT 5
SELECT MA_GIAO_DICH, MA_SAN_PHAM, DON_GIA
FROM GIAO_DICH
ORDER BY DON_GIA DESC
LIMIT 5;

-- 10. Tính thành tiền (SO_LUONG * DON_GIA) cho từng giao dịch
SELECT 
    MA_GIAO_DICH,
    MA_SAN_PHAM,
    SO_LUONG,
    DON_GIA,
    SO_LUONG * DON_GIA AS THANH_TIEN
FROM GIAO_DICH
ORDER BY MA_GIAO_DICH
LIMIT 10;

-- 11. Top 5 giao dịch có thành tiền cao nhất
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

-- 12. Kết hợp nhiều điều kiện logic bằng AND và OR
SELECT MA_GIAO_DICH, MA_KHACH_HANG, MA_SAN_PHAM, KHU_VUC, SO_LUONG, DON_GIA
FROM GIAO_DICH
WHERE (KHU_VUC = 'MIEN_NAM' AND SO_LUONG >= 15)
   OR (KHU_VUC = 'MIEN_BAC' AND DON_GIA >= 20000000.00);

-- 13. Lọc danh sách giá trị bằng toán tử IN
SELECT MA_GIAO_DICH, MA_KHACH_HANG, MA_SAN_PHAM, KHU_VUC
FROM GIAO_DICH
WHERE KHU_VUC IN ('MIEN_NAM', 'MIEN_TRUNG');

-- 14. Lọc số lượng trong khoảng bằng toán tử BETWEEN
SELECT MA_GIAO_DICH, MA_SAN_PHAM, SO_LUONG
FROM GIAO_DICH
WHERE SO_LUONG BETWEEN 10 AND 25
ORDER BY SO_LUONG DESC;
