-- =============================================================================
-- SCRIPT: 00_reset.sql
-- MỤC ĐÍCH: Đưa hệ thống về trạng thái ban đầu, dọn dẹp sạch bảng và chỉ mục cũ
-- CÔNG CỤ: Apache Phoenix SQLLine
-- =============================================================================

-- 1. Xóa Secondary Index nếu đã tồn tại
-- Lưu ý: Cú pháp DROP INDEX IF EXISTS <INDEX_NAME> ON <TABLE_NAME>
DROP INDEX IF EXISTS IDX_GIAO_DICH_KHU_VUC ON GIAO_DICH;

-- 2. Xóa bảng chính GIAO_DICH nếu đã tồn tại
DROP TABLE IF EXISTS GIAO_DICH;

-- Xác nhận trạng thái dọn dẹp hoàn tất
SELECT 'RESET THANH CONG - BANG VA INDEX DA DUOC XOA' AS TRANG_THAI FROM SYSTEM.CATALOG LIMIT 1;
