-- =============================================================================
-- SCRIPT: 04_update_delete.sql
-- MỤC ĐÍCH: Thao tác cập nhật dữ liệu bằng UPSERT và xóa dữ liệu bằng DELETE
-- =============================================================================

-- =============================================================================
-- PHẦN 1: CẬP NHẬT DỮ LIỆU BẰNG CƠ CHẾ UPSERT (KHÔNG DÙNG LỆNH UPDATE)
-- =============================================================================

-- Bước 1.1: Xem thông tin bản ghi GD001 trước khi cập nhật
SELECT * 
FROM GIAO_DICH 
WHERE MA_GIAO_DICH = 'GD001';

-- Bước 1.2: Cập nhật bản ghi GD001 bằng UPSERT
-- (Truyền đầy đủ các cột để bảo toàn toàn bộ giá trị không thay đổi)
-- Thay đổi: SO_LUONG từ 10 thành 20, DON_GIA từ 15000000 thành 14500000
UPSERT INTO GIAO_DICH (
    MA_GIAO_DICH,
    MA_KHACH_HANG,
    MA_SAN_PHAM,
    KHU_VUC,
    SO_LUONG,
    DON_GIA,
    THOI_GIAN
) VALUES (
    'GD001',
    'KH01',
    'SP01',
    'MIEN_NAM',
    20,
    14500000.00,
    TO_TIMESTAMP('2026-03-01 08:30:00', 'yyyy-MM-dd HH:mm:ss')
);

-- Bước 1.3: Dữ liệu tự động được commit do SQLLine bật autocommit mặc định
-- (Nếu ở chế độ manual transaction !autocommit off, sử dụng !commit)

-- Bước 1.4: Truy vấn lại GD001 sau khi cập nhật để kiểm tra kết quả
SELECT * 
FROM GIAO_DICH 
WHERE MA_GIAO_DICH = 'GD001';


-- =============================================================================
-- PHẦN 2: MINH HỌA THAO TÁC XÓA DỮ LIỆU BẰNG BẢN GHI TẠM (GD999)
-- =============================================================================

-- Bước 2.1: Thêm một bản ghi thử nghiệm GD999
UPSERT INTO GIAO_DICH (
    MA_GIAO_DICH,
    MA_KHACH_HANG,
    MA_SAN_PHAM,
    KHU_VUC,
    SO_LUONG,
    DON_GIA,
    THOI_GIAN
) VALUES (
    'GD999',
    'KH99',
    'SP99',
    'MIEN_TRUNG',
    1,
    999999.00,
    TO_TIMESTAMP('2026-03-09 12:00:00', 'yyyy-MM-dd HH:mm:ss')
);

-- Bước 2.2: Bản ghi GD999 đã được tự động commit vào HBase

-- Bước 2.3: Xác nhận bản ghi tạm GD999 đã tồn tại
SELECT * 
FROM GIAO_DICH 
WHERE MA_GIAO_DICH = 'GD999';

-- Bước 2.4: Thực hiện xóa bản ghi GD999 bằng lệnh DELETE
DELETE FROM GIAO_DICH 
WHERE MA_GIAO_DICH = 'GD999';

-- Bước 2.5: Thao tác DELETE tự động hoàn tất và ghi nhận vào HBase

-- Bước 2.6: Truy vấn lại xác nhận GD999 đã bị xóa hoàn toàn (kết quả trả về 0 dòng)
SELECT * 
FROM GIAO_DICH 
WHERE MA_GIAO_DICH = 'GD999';
