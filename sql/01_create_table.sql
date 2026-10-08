-- =============================================================================
-- SCRIPT: 01_create_table.sql
-- MỤC ĐÍCH: Khởi tạo cấu trúc bảng GIAO_DICH với cơ chế Salt Buckets trên Phoenix
-- =============================================================================

-- 1. Tạo bảng GIAO_DICH với 8 Salt Buckets để phân tán dữ liệu đều trên HBase RegionServers,
--    chống hiện tượng Region Hotspotting khi ghi dữ liệu lớn theo tuần tự.
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

-- 2. Kiểm tra danh sách bảng hiện có trong metadata
!tables

-- 3. Xem cấu trúc chi tiết của bảng GIAO_DICH
!describe GIAO_DICH
