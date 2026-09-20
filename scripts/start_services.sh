#!/usr/bin/env bash
# =============================================================================
# SCRIPT: start_services.sh
# MỤC ĐÍCH: Khởi động dịch vụ HBase và kiểm tra tiến trình HMaster
# =============================================================================

# Thiết lập JAVA_HOME mặc định nếu chưa được export
if [ -z "$JAVA_HOME" ]; then
    export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
fi

echo "======================================================"
echo " Đang khởi động Apache HBase..."
echo " JAVA_HOME: $JAVA_HOME"
echo "======================================================"

/mnt/d/2026/BigData/hbase/bin/start-hbase.sh

echo "Đang đợi HBase khởi tạo tiến trình (khoảng 5 giây)..."
sleep 5

echo "======================================================"
echo " Danh sách tiến trình Java hiện tại (jps):"
echo "======================================================"
jps

if jps | grep -q -i HMaster; then
    echo "======================================================"
    echo " HBase HMaster đã khởi động thành công!"
    echo " Bạn có thể kết nối Phoenix SQLLine bằng lệnh:"
    echo " /mnt/d/2026/BigData/phoenix/bin/sqlline.py localhost"
    echo "======================================================"
else
    echo "======================================================"
    echo " CẢNH BÁO: Chưa phát hiện HMaster trong danh sách jps."
    echo " Vui lòng kiểm tra lại log tại /mnt/d/2026/BigData/hbase/logs"
    echo "======================================================"
fi
