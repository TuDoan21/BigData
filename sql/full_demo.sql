-- =============================================================================
-- SCRIPT TOÀN DIỆN: full_demo.sql
-- DỰ ÁN: Apache Phoenix Demo trên HBase 2.5 (Big Data 2026)
-- MỤC ĐÍCH: Tự động chạy toàn bộ quy trình demo tuần tự từ khởi tạo đến phân tích
-- =============================================================================


-- =============================================================================
-- PHẦN 1: TẠO BẢNG GIAO_DICH VỚI CƠ CHẾ SALT BUCKETS (NẾU CHƯA CÓ)
-- =============================================================================
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


-- =============================================================================
-- PHẦN 3: NẠP DỮ LIỆU BAN ĐẦU BẰNG CƠ CHẾ UPSERT INTO
-- =============================================================================
UPSERT INTO GIAO_DICH (MA_GIAO_DICH, MA_KHACH_HANG, MA_SAN_PHAM, KHU_VUC, SO_LUONG, DON_GIA, THOI_GIAN)
VALUES ('TX_0000003', 'KH_20476', 'SP_111821003', 'MIEN_BAC', 8, 2000.0, TO_TIMESTAMP('2025-06-30 12:07:04', 'yyyy-MM-dd HH:mm:ss'));

UPSERT INTO GIAO_DICH (MA_GIAO_DICH, MA_KHACH_HANG, MA_SAN_PHAM, KHU_VUC, SO_LUONG, DON_GIA, THOI_GIAN)
VALUES ('TX_0000007', 'KH_20295', 'SP_35042297', 'MIEN_BAC', 3, 55000.0, TO_TIMESTAMP('2025-06-24 09:26:48', 'yyyy-MM-dd HH:mm:ss'));

UPSERT INTO GIAO_DICH (MA_GIAO_DICH, MA_KHACH_HANG, MA_SAN_PHAM, KHU_VUC, SO_LUONG, DON_GIA, THOI_GIAN)
VALUES ('TX_0000010', 'KH_20361', 'SP_154858227', 'MIEN_NAM', 2, 25000.0, TO_TIMESTAMP('2025-11-12 04:07:36', 'yyyy-MM-dd HH:mm:ss'));

UPSERT INTO GIAO_DICH (MA_GIAO_DICH, MA_KHACH_HANG, MA_SAN_PHAM, KHU_VUC, SO_LUONG, DON_GIA, THOI_GIAN)
VALUES ('TX_0000014', 'KH_20020', 'SP_160449800', 'MIEN_NAM', 1, 79000.0, TO_TIMESTAMP('2025-12-15 21:11:47', 'yyyy-MM-dd HH:mm:ss'));

UPSERT INTO GIAO_DICH (MA_GIAO_DICH, MA_KHACH_HANG, MA_SAN_PHAM, KHU_VUC, SO_LUONG, DON_GIA, THOI_GIAN)
VALUES ('TX_0000018', 'KH_20363', 'SP_262974253', 'MIEN_NAM', 3, 32000.0, TO_TIMESTAMP('2026-06-25 16:49:14', 'yyyy-MM-dd HH:mm:ss'));

UPSERT INTO GIAO_DICH (MA_GIAO_DICH, MA_KHACH_HANG, MA_SAN_PHAM, KHU_VUC, SO_LUONG, DON_GIA, THOI_GIAN)
VALUES ('TX_0000019', 'KH_20388', 'SP_263025426', 'MIEN_NAM', 1, 45000.0, TO_TIMESTAMP('2025-04-13 12:24:28', 'yyyy-MM-dd HH:mm:ss'));

UPSERT INTO GIAO_DICH (MA_GIAO_DICH, MA_KHACH_HANG, MA_SAN_PHAM, KHU_VUC, SO_LUONG, DON_GIA, THOI_GIAN)
VALUES ('TX_0000020', 'KH_20060', 'SP_209643731', 'MIEN_BAC', 3, 88900.0, TO_TIMESTAMP('2025-09-07 11:55:36', 'yyyy-MM-dd HH:mm:ss'));

UPSERT INTO GIAO_DICH (MA_GIAO_DICH, MA_KHACH_HANG, MA_SAN_PHAM, KHU_VUC, SO_LUONG, DON_GIA, THOI_GIAN)
VALUES ('TX_0000025', 'KH_20373', 'SP_251446835', 'MIEN_TRUNG', 1, 845500.0, TO_TIMESTAMP('2025-01-22 08:55:04', 'yyyy-MM-dd HH:mm:ss'));

UPSERT INTO GIAO_DICH (MA_GIAO_DICH, MA_KHACH_HANG, MA_SAN_PHAM, KHU_VUC, SO_LUONG, DON_GIA, THOI_GIAN)
VALUES ('TX_0000035', 'KH_20380', 'SP_191981357', 'MIEN_TRUNG', 2, 37800.0, TO_TIMESTAMP('2026-06-27 20:52:07', 'yyyy-MM-dd HH:mm:ss'));

UPSERT INTO GIAO_DICH (MA_GIAO_DICH, MA_KHACH_HANG, MA_SAN_PHAM, KHU_VUC, SO_LUONG, DON_GIA, THOI_GIAN)
VALUES ('TX_0000037', 'KH_20332', 'SP_160205765', 'MIEN_NAM', 1, 169000.0, TO_TIMESTAMP('2025-04-04 06:33:32', 'yyyy-MM-dd HH:mm:ss'));

UPSERT INTO GIAO_DICH (MA_GIAO_DICH, MA_KHACH_HANG, MA_SAN_PHAM, KHU_VUC, SO_LUONG, DON_GIA, THOI_GIAN)
VALUES ('TX_0000001', 'KH_GUEST', '20979', 'United Kingdom', 12, 32500.0, TO_TIMESTAMP('2024-10-13 02:51:34', 'yyyy-MM-dd HH:mm:ss'));

UPSERT INTO GIAO_DICH (MA_GIAO_DICH, MA_KHACH_HANG, MA_SAN_PHAM, KHU_VUC, SO_LUONG, DON_GIA, THOI_GIAN)
VALUES ('TX_0000002', 'KH_17757', '21212', 'United Kingdom', 10, 14300.0, TO_TIMESTAMP('2025-08-16 10:41:48', 'yyyy-MM-dd HH:mm:ss'));

UPSERT INTO GIAO_DICH (MA_GIAO_DICH, MA_KHACH_HANG, MA_SAN_PHAM, KHU_VUC, SO_LUONG, DON_GIA, THOI_GIAN)
VALUES ('TX_0000004', 'KH_GUEST', '84755', 'United Kingdom', 4, 32240.0, TO_TIMESTAMP('2025-06-28 00:25:35', 'yyyy-MM-dd HH:mm:ss'));

UPSERT INTO GIAO_DICH (MA_GIAO_DICH, MA_KHACH_HANG, MA_SAN_PHAM, KHU_VUC, SO_LUONG, DON_GIA, THOI_GIAN)
VALUES ('TX_0000006', 'KH_15508', '22969', 'United Kingdom', 24, 37700.0, TO_TIMESTAMP('2026-07-09 17:37:33', 'yyyy-MM-dd HH:mm:ss'));

UPSERT INTO GIAO_DICH (MA_GIAO_DICH, MA_KHACH_HANG, MA_SAN_PHAM, KHU_VUC, SO_LUONG, DON_GIA, THOI_GIAN)
VALUES ('TX_0000008', 'KH_16101', '23484', 'United Kingdom', 8, 75140.0, TO_TIMESTAMP('2025-04-15 18:00:23', 'yyyy-MM-dd HH:mm:ss'));


-- =============================================================================
-- PHẦN 4: GHI NHẬN GIAO DỊCH (AUTOCOMMIT TRONG PHOENIX SQLLINE)
-- =============================================================================
-- Ghi chú: Trong Phoenix SQLLine, autocommit được bật mặc định, toàn bộ 25 lệnh
-- UPSERT trên đã tự động được ghi nhận và lưu trữ phân tán xuống HBase.


-- =============================================================================
-- PHẦN 5: KIỂM TRA SỐ LƯỢNG DỮ LIỆU
-- =============================================================================
SELECT COUNT(*) AS TONG_SO_GIAO_DICH
FROM GIAO_DICH;


-- =============================================================================
-- PHẦN 6: CHẠY CÁC TRUY VẤN CƠ BẢN
-- =============================================================================
-- Lấy 5 giao dịch đầu tiên
SELECT MA_GIAO_DICH, MA_KHACH_HANG, MA_SAN_PHAM, KHU_VUC, SO_LUONG, DON_GIA
FROM GIAO_DICH
ORDER BY MA_GIAO_DICH
LIMIT 5;

-- Tính thành tiền và hiển thị top 3 giao dịch lớn nhất
SELECT 
    MA_GIAO_DICH, 
    MA_SAN_PHAM, 
    KHU_VUC, 
    SO_LUONG, 
    DON_GIA, 
    SO_LUONG * DON_GIA AS THANH_TIEN
FROM GIAO_DICH
ORDER BY THANH_TIEN DESC
LIMIT 3;


-- =============================================================================
-- PHẦN 7: CẬP NHẬT DỮ LIỆU BẰNG UPSERT (BẢN GHI TX_0000001)
-- =============================================================================
-- Giá trị cũ của TX_0000001
SELECT * FROM GIAO_DICH WHERE MA_GIAO_DICH = 'TX_0000001';

-- Cập nhật TX_0000001 với đầy đủ các thuộc tính
UPSERT INTO GIAO_DICH (MA_GIAO_DICH, MA_KHACH_HANG, MA_SAN_PHAM, KHU_VUC, SO_LUONG, DON_GIA, THOI_GIAN)
VALUES ('TX_0000001', 'KH_17850', '85123A', 'MIEN_NAM', 20, 14500000.00, TO_TIMESTAMP('2026-03-01 08:30:00', 'yyyy-MM-dd HH:mm:ss'));

-- Giá trị mới của TX_0000001 sau cập nhật
SELECT * FROM GIAO_DICH WHERE MA_GIAO_DICH = 'TX_0000001';


-- =============================================================================
-- PHẦN 8: THÊM VÀ XÓA DỮ LIỆU THỬ NGHIỆM (BẢN GHI TX_9999999)
-- =============================================================================
-- Thêm TX_9999999
UPSERT INTO GIAO_DICH (MA_GIAO_DICH, MA_KHACH_HANG, MA_SAN_PHAM, KHU_VUC, SO_LUONG, DON_GIA, THOI_GIAN)
VALUES ('TX_9999999', 'KH_99999', '99999', 'MIEN_TRUNG', 1, 999999.00, TO_TIMESTAMP('2026-03-09 12:00:00', 'yyyy-MM-dd HH:mm:ss'));

-- Xác nhận TX_9999999 tồn tại
SELECT * FROM GIAO_DICH WHERE MA_GIAO_DICH = 'TX_9999999';

-- Xóa TX_9999999
DELETE FROM GIAO_DICH WHERE MA_GIAO_DICH = 'TX_9999999';

-- Xác nhận TX_9999999 đã bị xóa (0 row)
SELECT * FROM GIAO_DICH WHERE MA_GIAO_DICH = 'TX_9999999';


-- =============================================================================
-- PHẦN 9: TRUY VẤN TỔNG HỢP (AGGREGATE)
-- =============================================================================
-- Thống kê theo khu vực: Số lượng GD, Tổng số lượng SP, Tổng Doanh thu
SELECT 
    KHU_VUC,
    COUNT(*) AS SO_GIAO_DICH,
    SUM(SO_LUONG) AS TONG_SO_LUONG,
    SUM(SO_LUONG * DON_GIA) AS TONG_DOANH_THU,
    AVG(SO_LUONG * DON_GIA) AS DOANH_THU_TRUNG_BINH
FROM GIAO_DICH
GROUP BY KHU_VUC
ORDER BY TONG_DOANH_THU DESC;


-- =============================================================================
-- PHẦN 10: KIỂM TRA KẾ HOẠCH THỰC THI (EXPLAIN) TRƯỚC KHI CÓ INDEX
-- =============================================================================
EXPLAIN
SELECT MA_GIAO_DICH, KHU_VUC, SO_LUONG, DON_GIA
FROM GIAO_DICH
WHERE KHU_VUC = 'MIEN_NAM';


-- =============================================================================
-- PHẦN 11: TẠO SECONDARY COVERED INDEX
-- =============================================================================
DROP INDEX IF EXISTS IDX_GIAO_DICH_KHU_VUC ON GIAO_DICH;

CREATE INDEX IDX_GIAO_DICH_KHU_VUC
ON GIAO_DICH (KHU_VUC)
INCLUDE (
    MA_KHACH_HANG,
    MA_SAN_PHAM,
    SO_LUONG,
    DON_GIA,
    THOI_GIAN
);


-- =============================================================================
-- PHẦN 12: KIỂM TRA LẠI KẾ HOẠCH THỰC THI (EXPLAIN) SAU KHI CÓ INDEX
-- =============================================================================
EXPLAIN
SELECT MA_GIAO_DICH, KHU_VUC, SO_LUONG, DON_GIA
FROM GIAO_DICH
WHERE KHU_VUC = 'MIEN_NAM';


-- =============================================================================
-- PHẦN 13: HIỂN THỊ KẾT QUẢ CUỐI CÙNG
-- =============================================================================
-- Truy vấn có Index Hint
SELECT /*+ INDEX(GIAO_DICH IDX_GIAO_DICH_KHU_VUC) */
    MA_GIAO_DICH, KHU_VUC, SO_LUONG, DON_GIA
FROM GIAO_DICH
WHERE KHU_VUC = 'MIEN_NAM'
LIMIT 5;

SELECT 'HOAN THANH TOAN BO DEMO APACHE PHOENIX THANH CONG!' AS KET_LUAN FROM SYSTEM.CATALOG LIMIT 1;
