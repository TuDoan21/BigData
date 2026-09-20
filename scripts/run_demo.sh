#!/usr/bin/env bash
# =============================================================================
# SCRIPT: run_demo.sh
# MỤC ĐÍCH: Tự động kiểm tra điều kiện và thực thi toàn bộ kịch bản full_demo.sql
# =============================================================================

# Thiết lập JAVA_HOME mặc định nếu chưa được export
if [ -z "$JAVA_HOME" ]; then
    export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
fi

# Tự động xác định đường dẫn gốc của dự án
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SQL_FILE="$PROJECT_DIR/sql/full_demo.sql"
SQLLINE_BIN="/mnt/d/2026/BigData/phoenix/bin/sqlline.py"

echo "======================================================"
echo " KHỞI CHẠY DEMO APACHE PHOENIX TRÊN HBASE"
echo " Thư mục dự án: $PROJECT_DIR"
echo " File kịch bản:  $SQL_FILE"
echo "======================================================"

# 1. Kiểm tra tiến trình HMaster
if ! jps 2>/dev/null | grep -q -i HMaster; then
    echo "[LỖI NGHIÊM TRỌNG] HBase HMaster hiện KHÔNG chạy!"
    echo "Vui lòng khởi động HBase trước khi chạy demo:"
    echo "  $PROJECT_DIR/scripts/start_services.sh"
    echo "Hoặc:"
    echo "  /mnt/d/2026/BigData/hbase/bin/start-hbase.sh"
    exit 1
fi

# 2. Kiểm tra file kịch bản SQL
if [ ! -f "$SQL_FILE" ]; then
    echo "[LỖI] Không tìm thấy file kịch bản SQL tại: $SQL_FILE"
    exit 1
fi

# 3. Kiểm tra công cụ sqlline.py
if [ ! -f "$SQLLINE_BIN" ]; then
    echo "[LỖI] Không tìm thấy sqlline.py tại: $SQLLINE_BIN"
    exit 1
fi

echo "HBase HMaster đang hoạt động bình thường."
echo "Đang kết nối tới Phoenix và thực thi full_demo.sql..."
echo "======================================================"

# 4. Thực thi kịch bản với SQLLine (không che dấu lỗi)
python3 "$SQLLINE_BIN" localhost "$SQL_FILE"
EXIT_CODE=$?

echo "======================================================"
if [ $EXIT_CODE -eq 0 ]; then
    echo "QUY TRÌNH DEMO ĐÃ HOÀN TẤT THÀNH CÔNG!"
else
    echo "QUY TRÌNH DEMO KẾT THÚC VỚI MÃ LỖI: $EXIT_CODE"
fi
echo "======================================================"
exit $EXIT_CODE
