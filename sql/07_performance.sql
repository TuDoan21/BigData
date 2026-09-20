-- =============================================================================
-- SCRIPT: 07_performance.sql
-- MỤC ĐÍCH: Kiểm tra hiệu năng thực tế của truy vấn và đánh giá tác động của Index
-- =============================================================================

-- 1. Đếm tổng số bản ghi hiện có trong bảng GIAO_DICH
SELECT COUNT(*) AS TONG_SO_BAN_GHI
FROM GIAO_DICH;

-- 2. Đánh giá kế hoạch thực thi khi quét theo khu vực
EXPLAIN
SELECT MA_GIAO_DICH, KHU_VUC, SO_LUONG, DON_GIA, THOI_GIAN
FROM GIAO_DICH
WHERE KHU_VUC = 'MIEN_NAM';

-- 3. Thực thi truy vấn lọc theo khu vực và đo thời gian phản hồi thực tế
SELECT MA_GIAO_DICH, KHU_VUC, SO_LUONG, DON_GIA, THOI_GIAN
FROM GIAO_DICH
WHERE KHU_VUC = 'MIEN_NAM'
LIMIT 20;

-- 4. So sánh kế hoạch thực thi khi ép quét bảng chính không dùng index (NO_INDEX hint)
EXPLAIN
SELECT /*+ NO_INDEX */ MA_GIAO_DICH, KHU_VUC, SO_LUONG, DON_GIA, THOI_GIAN
FROM GIAO_DICH
WHERE KHU_VUC = 'MIEN_NAM';

-- 5. Kế hoạch thực thi khi sử dụng Covered Index
EXPLAIN
SELECT /*+ INDEX(GIAO_DICH IDX_GIAO_DICH_KHU_VUC) */ 
    MA_GIAO_DICH, KHU_VUC, SO_LUONG, DON_GIA, THOI_GIAN
FROM GIAO_DICH
WHERE KHU_VUC = 'MIEN_NAM';

-- 6. Truy vấn tổng hợp phân tích trên toàn bộ tập dữ liệu (Aggregation Performance)
SELECT 
    KHU_VUC,
    COUNT(*) AS TONG_SO_GD,
    SUM(SO_LUONG) AS TONG_SO_LUONG,
    SUM(SO_LUONG * DON_GIA) AS TONG_DOANH_THU,
    AVG(SO_LUONG * DON_GIA) AS DOANH_THU_TB
FROM GIAO_DICH
GROUP BY KHU_VUC
ORDER BY TONG_DOANH_THU DESC;

-- 7. Truy vấn phân tích lọc theo thời gian và gom nhóm (Time-range Aggregation)
SELECT 
    KHU_VUC,
    COUNT(*) AS SO_GD_TRONG_KY,
    SUM(SO_LUONG * DON_GIA) AS DOANH_THU_KY
FROM GIAO_DICH
WHERE THOI_GIAN >= TO_TIMESTAMP('2026-03-01 00:00:00', 'yyyy-MM-dd HH:mm:ss')
GROUP BY KHU_VUC
ORDER BY DOANH_THU_KY DESC;
