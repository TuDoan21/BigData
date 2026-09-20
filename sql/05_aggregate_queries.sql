-- =============================================================================
-- SCRIPT: 05_aggregate_queries.sql
-- MỤC ĐÍCH: Các câu truy vấn tổng hợp, thống kê, gom nhóm (Aggregate Queries)
-- =============================================================================

-- 1. Đếm tổng số giao dịch trong toàn hệ thống
SELECT COUNT(*) AS TONG_SO_GIAO_DICH
FROM GIAO_DICH;

-- 2. Đếm số lượng giao dịch theo từng khu vực
SELECT 
    KHU_VUC, 
    COUNT(*) AS SO_GIAO_DICH
FROM GIAO_DICH
GROUP BY KHU_VUC
ORDER BY SO_GIAO_DICH DESC;

-- 3. Tổng số lượng sản phẩm bán ra theo từng khu vực
SELECT 
    KHU_VUC, 
    SUM(SO_LUONG) AS TONG_SAN_PHAM
FROM GIAO_DICH
GROUP BY KHU_VUC
ORDER BY TONG_SAN_PHAM DESC;

-- 4. Tổng doanh thu (SO_LUONG * DON_GIA) theo từng khu vực
SELECT 
    KHU_VUC,
    COUNT(*) AS SO_GIAO_DICH,
    SUM(SO_LUONG * DON_GIA) AS TONG_DOANH_THU
FROM GIAO_DICH
GROUP BY KHU_VUC
ORDER BY TONG_DOANH_THU DESC;

-- 5. Doanh thu trung bình trên mỗi giao dịch theo khu vực
SELECT 
    KHU_VUC,
    AVG(SO_LUONG * DON_GIA) AS DOANH_THU_TRUNG_BINH
FROM GIAO_DICH
GROUP BY KHU_VUC
ORDER BY DOANH_THU_TRUNG_BINH DESC;

-- 6. Đơn giá thấp nhất và cao nhất trên toàn bảng
SELECT 
    MIN(DON_GIA) AS DON_GIA_THAP_NHAT,
    MAX(DON_GIA) AS DON_GIA_CAO_NHAT,
    AVG(DON_GIA) AS DON_GIA_TRUNG_BINH
FROM GIAO_DICH;

-- 7. Sản phẩm bán được nhiều nhất (theo tổng số lượng bán ra)
SELECT 
    MA_SAN_PHAM, 
    SUM(SO_LUONG) AS TONG_SO_LUONG_BAN
FROM GIAO_DICH
GROUP BY MA_SAN_PHAM
ORDER BY TONG_SO_LUONG_BAN DESC
LIMIT 1;

-- 8. Khách hàng có tổng giá trị giao dịch lớn nhất (VIP Customer)
SELECT 
    MA_KHACH_HANG, 
    COUNT(*) AS SO_LAN_MUA,
    SUM(SO_LUONG * DON_GIA) AS TONG_CHI_TIEU
FROM GIAO_DICH
GROUP BY MA_KHACH_HANG
ORDER BY TONG_CHI_TIEU DESC
LIMIT 1;

-- 9. Gom nhóm theo khu vực và lọc các khu vực có tổng doanh thu > 100.000.000 (dùng HAVING)
SELECT 
    KHU_VUC,
    COUNT(*) AS SO_GIAO_DICH,
    SUM(SO_LUONG * DON_GIA) AS TONG_DOANH_THU
FROM GIAO_DICH
GROUP BY KHU_VUC
HAVING SUM(SO_LUONG * DON_GIA) > 100000000.00
ORDER BY TONG_DOANH_THU DESC;

-- 10. Thống kê số lượng giao dịch và doanh thu theo ngày (dùng hàm TO_CHAR định dạng ngày)
SELECT 
    TO_CHAR(THOI_GIAN, 'yyyy-MM-dd') AS NGAY_GIAO_DICH,
    COUNT(*) AS SO_GIAO_DICH,
    SUM(SO_LUONG * DON_GIA) AS DOANH_THU_NGAY
FROM GIAO_DICH
GROUP BY TO_CHAR(THOI_GIAN, 'yyyy-MM-dd')
ORDER BY NGAY_GIAO_DICH ASC;
