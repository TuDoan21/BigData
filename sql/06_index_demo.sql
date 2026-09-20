-- =============================================================================
-- SCRIPT: 06_index_demo.sql
-- MỤC ĐÍCH: Minh họa tạo và sử dụng Secondary Index (Covered Index) trên Phoenix
-- =============================================================================

-- =============================================================================
-- BƯỚC 1: TRUY VẤN VÀ KIỂM TRA KẾ HOẠCH THỰC THI KHI CHƯA CÓ INDEX
-- =============================================================================

-- Chạy truy vấn lọc theo KHU_VUC khi chưa có index
SELECT MA_GIAO_DICH, KHU_VUC, SO_LUONG, DON_GIA
FROM GIAO_DICH
WHERE KHU_VUC = 'MIEN_NAM';

-- Xem kế hoạch thực thi bằng EXPLAIN
-- Kết quả sẽ hiển thị Full Scan (PARALLEL 8-WAY FULL SCAN) trên bảng GIAO_DICH
EXPLAIN
SELECT MA_GIAO_DICH, KHU_VUC, SO_LUONG, DON_GIA
FROM GIAO_DICH
WHERE KHU_VUC = 'MIEN_NAM';


-- =============================================================================
-- BƯỚC 2: TẠO SECONDARY INDEX (COVERED INDEX VỚI MỆNH ĐỀ INCLUDE)
-- =============================================================================

-- Tạo Secondary Global Index trên cột KHU_VUC kèm mệnh đề INCLUDE
-- Mệnh đề INCLUDE giúp các cột được lưu ngay trong bảng chỉ mục, biến nó thành
-- Covered Index để Phoenix không cần quét ngược lại bảng chính (tránh Read Overhead).
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
-- BƯỚC 3: KIỂM TRA LẠI KẾ HOẠCH THỰC THI SAU KHI CÓ INDEX
-- =============================================================================

-- EXPLAIN lại cùng câu truy vấn
-- Kết quả tối ưu: Trình tối ưu hóa của Phoenix (CBO) sẽ tự động chọn
-- RANGE SCAN trên bảng chỉ mục IDX_GIAO_DICH_KHU_VUC thay vì Full Scan bảng chính.
EXPLAIN
SELECT MA_GIAO_DICH, KHU_VUC, SO_LUONG, DON_GIA
FROM GIAO_DICH
WHERE KHU_VUC = 'MIEN_NAM';

-- Chạy truy vấn kiểm tra kết quả thực tế
SELECT MA_GIAO_DICH, KHU_VUC, SO_LUONG, DON_GIA
FROM GIAO_DICH
WHERE KHU_VUC = 'MIEN_NAM';


-- =============================================================================
-- BƯỚC 4: TRUY VẤN ÉP SỬ DỤNG INDEX BẰNG INDEX HINT
-- =============================================================================

-- Cú pháp Index Hint trong Apache Phoenix: /*+ INDEX(<TABLE_NAME> <INDEX_NAME>) */
-- Giúp người quản trị ép buộc Phoenix Query Optimizer sử dụng chỉ mục mong muốn
SELECT /*+ INDEX(GIAO_DICH IDX_GIAO_DICH_KHU_VUC) */
    MA_GIAO_DICH,
    KHU_VUC,
    SO_LUONG,
    DON_GIA
FROM GIAO_DICH
WHERE KHU_VUC = 'MIEN_NAM';

-- EXPLAIN truy vấn có chứa Index Hint để kiểm chứng việc ép index thành công
EXPLAIN
SELECT /*+ INDEX(GIAO_DICH IDX_GIAO_DICH_KHU_VUC) */
    MA_GIAO_DICH,
    KHU_VUC,
    SO_LUONG,
    DON_GIA
FROM GIAO_DICH
WHERE KHU_VUC = 'MIEN_NAM';
