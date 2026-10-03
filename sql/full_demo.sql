-- =============================================================================
-- SCRIPT TOÀN DIỆN: full_demo.sql
-- DỰ ÁN: Apache Phoenix Demo trên HBase 2.5 (Big Data 2026)
-- MỤC ĐÍCH: Tự động chạy toàn bộ quy trình demo tuần tự từ khởi tạo đến phân tích
-- =============================================================================


-- =============================================================================
-- PHẦN 1: DỌN DẸP BẢNG VÀ CHỈ MỤC CŨ (RESET ENVIRONMENT)
-- =============================================================================
DROP INDEX IF EXISTS IDX_GIAO_DICH_KHU_VUC ON GIAO_DICH;
DROP TABLE IF EXISTS GIAO_DICH;


-- =============================================================================
-- PHẦN 2: TẠO BẢNG GIAO_DICH VỚI CƠ CHẾ SALT BUCKETS
-- =============================================================================
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


-- =============================================================================
-- PHẦN 3: NẠP DỮ LIỆU BAN ĐẦU BẰNG CƠ CHẾ UPSERT INTO
-- =============================================================================
UPSERT INTO GIAO_DICH (MA_GIAO_DICH, MA_KHACH_HANG, MA_SAN_PHAM, KHU_VUC, SO_LUONG, DON_GIA, THOI_GIAN)
VALUES ('TX_0000001', 'KH_17850', '85123A', 'MIEN_NAM', 10, 15000000.00, TO_TIMESTAMP('2026-03-01 08:30:00', 'yyyy-MM-dd HH:mm:ss'));

UPSERT INTO GIAO_DICH (MA_GIAO_DICH, MA_KHACH_HANG, MA_SAN_PHAM, KHU_VUC, SO_LUONG, DON_GIA, THOI_GIAN)
VALUES ('TX_0000002', 'KH_13047', '71053', 'MIEN_BAC', 5, 25000000.00, TO_TIMESTAMP('2026-03-01 09:15:00', 'yyyy-MM-dd HH:mm:ss'));

UPSERT INTO GIAO_DICH (MA_GIAO_DICH, MA_KHACH_HANG, MA_SAN_PHAM, KHU_VUC, SO_LUONG, DON_GIA, THOI_GIAN)
VALUES ('TX_0000003', 'KH_12583', '84406B', 'MIEN_TRUNG', 20, 5500000.00, TO_TIMESTAMP('2026-03-01 10:45:00', 'yyyy-MM-dd HH:mm:ss'));

UPSERT INTO GIAO_DICH (MA_GIAO_DICH, MA_KHACH_HANG, MA_SAN_PHAM, KHU_VUC, SO_LUONG, DON_GIA, THOI_GIAN)
VALUES ('TX_0000004', 'KH_13748', '85123A', 'MIEN_NAM', 15, 15000000.00, TO_TIMESTAMP('2026-03-02 11:20:00', 'yyyy-MM-dd HH:mm:ss'));

UPSERT INTO GIAO_DICH (MA_GIAO_DICH, MA_KHACH_HANG, MA_SAN_PHAM, KHU_VUC, SO_LUONG, DON_GIA, THOI_GIAN)
VALUES ('TX_0000005', 'KH_15100', '84029G', 'MIEN_BAC', 30, 1200000.00, TO_TIMESTAMP('2026-03-02 14:05:00', 'yyyy-MM-dd HH:mm:ss'));

UPSERT INTO GIAO_DICH (MA_GIAO_DICH, MA_KHACH_HANG, MA_SAN_PHAM, KHU_VUC, SO_LUONG, DON_GIA, THOI_GIAN)
VALUES ('TX_0000006', 'KH_17850', '84029E', 'MIEN_TRUNG', 8, 8500000.00, TO_TIMESTAMP('2026-03-02 16:30:00', 'yyyy-MM-dd HH:mm:ss'));

UPSERT INTO GIAO_DICH (MA_GIAO_DICH, MA_KHACH_HANG, MA_SAN_PHAM, KHU_VUC, SO_LUONG, DON_GIA, THOI_GIAN)
VALUES ('TX_0000007', 'KH_15291', '71053', 'MIEN_NAM', 12, 24500000.00, TO_TIMESTAMP('2026-03-03 08:50:00', 'yyyy-MM-dd HH:mm:ss'));

UPSERT INTO GIAO_DICH (MA_GIAO_DICH, MA_KHACH_HANG, MA_SAN_PHAM, KHU_VUC, SO_LUONG, DON_GIA, THOI_GIAN)
VALUES ('TX_0000008', 'KH_14688', '22752', 'MIEN_BAC', 50, 450000.00, TO_TIMESTAMP('2026-03-03 10:10:00', 'yyyy-MM-dd HH:mm:ss'));

UPSERT INTO GIAO_DICH (MA_GIAO_DICH, MA_KHACH_HANG, MA_SAN_PHAM, KHU_VUC, SO_LUONG, DON_GIA, THOI_GIAN)
VALUES ('TX_0000009', 'KH_13047', '84406B', 'MIEN_TRUNG', 18, 5400000.00, TO_TIMESTAMP('2026-03-03 13:40:00', 'yyyy-MM-dd HH:mm:ss'));

UPSERT INTO GIAO_DICH (MA_GIAO_DICH, MA_KHACH_HANG, MA_SAN_PHAM, KHU_VUC, SO_LUONG, DON_GIA, THOI_GIAN)
VALUES ('TX_0000010', 'KH_12583', '85123A', 'MIEN_NAM', 25, 14800000.00, TO_TIMESTAMP('2026-03-04 09:00:00', 'yyyy-MM-dd HH:mm:ss'));

UPSERT INTO GIAO_DICH (MA_GIAO_DICH, MA_KHACH_HANG, MA_SAN_PHAM, KHU_VUC, SO_LUONG, DON_GIA, THOI_GIAN)
VALUES ('TX_0000011', 'KH_17809', '84029G', 'MIEN_BAC', 40, 1150000.00, TO_TIMESTAMP('2026-03-04 11:15:00', 'yyyy-MM-dd HH:mm:ss'));

UPSERT INTO GIAO_DICH (MA_GIAO_DICH, MA_KHACH_HANG, MA_SAN_PHAM, KHU_VUC, SO_LUONG, DON_GIA, THOI_GIAN)
VALUES ('TX_0000012', 'KH_13748', '84029E', 'MIEN_TRUNG', 6, 8900000.00, TO_TIMESTAMP('2026-03-04 15:30:00', 'yyyy-MM-dd HH:mm:ss'));

UPSERT INTO GIAO_DICH (MA_GIAO_DICH, MA_KHACH_HANG, MA_SAN_PHAM, KHU_VUC, SO_LUONG, DON_GIA, THOI_GIAN)
VALUES ('TX_0000013', 'KH_15100', '71053', 'MIEN_NAM', 7, 25000000.00, TO_TIMESTAMP('2026-03-05 08:20:00', 'yyyy-MM-dd HH:mm:ss'));

UPSERT INTO GIAO_DICH (MA_GIAO_DICH, MA_KHACH_HANG, MA_SAN_PHAM, KHU_VUC, SO_LUONG, DON_GIA, THOI_GIAN)
VALUES ('TX_0000014', 'KH_15291', '22752', 'MIEN_BAC', 60, 420000.00, TO_TIMESTAMP('2026-03-05 10:40:00', 'yyyy-MM-dd HH:mm:ss'));

UPSERT INTO GIAO_DICH (MA_GIAO_DICH, MA_KHACH_HANG, MA_SAN_PHAM, KHU_VUC, SO_LUONG, DON_GIA, THOI_GIAN)
VALUES ('TX_0000015', 'KH_14688', '84406B', 'MIEN_TRUNG', 14, 5600000.00, TO_TIMESTAMP('2026-03-05 14:10:00', 'yyyy-MM-dd HH:mm:ss'));

UPSERT INTO GIAO_DICH (MA_GIAO_DICH, MA_KHACH_HANG, MA_SAN_PHAM, KHU_VUC, SO_LUONG, DON_GIA, THOI_GIAN)
VALUES ('TX_0000016', 'KH_17850', '85123A', 'MIEN_NAM', 16, 15000000.00, TO_TIMESTAMP('2026-03-06 09:30:00', 'yyyy-MM-dd HH:mm:ss'));

UPSERT INTO GIAO_DICH (MA_GIAO_DICH, MA_KHACH_HANG, MA_SAN_PHAM, KHU_VUC, SO_LUONG, DON_GIA, THOI_GIAN)
VALUES ('TX_0000017', 'KH_13047', '84029G', 'MIEN_BAC', 22, 1200000.00, TO_TIMESTAMP('2026-03-06 13:25:00', 'yyyy-MM-dd HH:mm:ss'));

UPSERT INTO GIAO_DICH (MA_GIAO_DICH, MA_KHACH_HANG, MA_SAN_PHAM, KHU_VUC, SO_LUONG, DON_GIA, THOI_GIAN)
VALUES ('TX_0000018', 'KH_17809', '84029E', 'MIEN_TRUNG', 11, 8700000.00, TO_TIMESTAMP('2026-03-06 16:50:00', 'yyyy-MM-dd HH:mm:ss'));

UPSERT INTO GIAO_DICH (MA_GIAO_DICH, MA_KHACH_HANG, MA_SAN_PHAM, KHU_VUC, SO_LUONG, DON_GIA, THOI_GIAN)
VALUES ('TX_0000019', 'KH_12583', '71053', 'MIEN_NAM', 4, 25200000.00, TO_TIMESTAMP('2026-03-07 10:15:00', 'yyyy-MM-dd HH:mm:ss'));

UPSERT INTO GIAO_DICH (MA_GIAO_DICH, MA_KHACH_HANG, MA_SAN_PHAM, KHU_VUC, SO_LUONG, DON_GIA, THOI_GIAN)
VALUES ('TX_0000020', 'KH_13748', '22752', 'MIEN_BAC', 35, 450000.00, TO_TIMESTAMP('2026-03-07 11:45:00', 'yyyy-MM-dd HH:mm:ss'));

UPSERT INTO GIAO_DICH (MA_GIAO_DICH, MA_KHACH_HANG, MA_SAN_PHAM, KHU_VUC, SO_LUONG, DON_GIA, THOI_GIAN)
VALUES ('TX_0000021', 'KH_15100', '85123A', 'MIEN_TRUNG', 9, 15100000.00, TO_TIMESTAMP('2026-03-07 15:20:00', 'yyyy-MM-dd HH:mm:ss'));

UPSERT INTO GIAO_DICH (MA_GIAO_DICH, MA_KHACH_HANG, MA_SAN_PHAM, KHU_VUC, SO_LUONG, DON_GIA, THOI_GIAN)
VALUES ('TX_0000022', 'KH_15291', '84406B', 'MIEN_NAM', 21, 5500000.00, TO_TIMESTAMP('2026-03-08 08:40:00', 'yyyy-MM-dd HH:mm:ss'));

UPSERT INTO GIAO_DICH (MA_GIAO_DICH, MA_KHACH_HANG, MA_SAN_PHAM, KHU_VUC, SO_LUONG, DON_GIA, THOI_GIAN)
VALUES ('TX_0000023', 'KH_14688', '84029G', 'MIEN_BAC', 28, 1200000.00, TO_TIMESTAMP('2026-03-08 11:00:00', 'yyyy-MM-dd HH:mm:ss'));

UPSERT INTO GIAO_DICH (MA_GIAO_DICH, MA_KHACH_HANG, MA_SAN_PHAM, KHU_VUC, SO_LUONG, DON_GIA, THOI_GIAN)
VALUES ('TX_0000024', 'KH_17809', '84029E', 'MIEN_NAM', 15, 8600000.00, TO_TIMESTAMP('2026-03-08 14:35:00', 'yyyy-MM-dd HH:mm:ss'));

UPSERT INTO GIAO_DICH (MA_GIAO_DICH, MA_KHACH_HANG, MA_SAN_PHAM, KHU_VUC, SO_LUONG, DON_GIA, THOI_GIAN)
VALUES ('TX_0000025', 'KH_13047', '71053', 'MIEN_TRUNG', 8, 24800000.00, TO_TIMESTAMP('2026-03-08 17:10:00', 'yyyy-MM-dd HH:mm:ss'));


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
