#!/usr/bin/env bash
# =============================================================================
# SCRIPT: check_services.sh
# MỤC ĐÍCH: Kiểm tra trạng thái môi trường Java, HBase, Phoenix và ZooKeeper
# =============================================================================

# Màu sắc thông báo
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}======================================================${NC}"
echo -e "${BLUE}   KIỂM TRA TRẠNG THÁI MÔI TRƯỜNG APACHE PHOENIX & HBASE   ${NC}"
echo -e "${BLUE}======================================================${NC}"

ERRORS=0

# 1. Kiểm tra lệnh java
echo -n "1. Kiểm tra lệnh 'java': "
if command -v java >/dev/null 2>&1; then
    JAVA_VER=$(java -version 2>&1 | head -n 1)
    echo -e "${GREEN}[OK]${NC} ($JAVA_VER)"
else
    echo -e "${RED}[LỖI] Không tìm thấy lệnh java trong PATH!${NC}"
    ERRORS=$((ERRORS + 1))
fi

# 2. Kiểm tra biến JAVA_HOME
echo -n "2. Kiểm tra biến 'JAVA_HOME': "
if [ -n "$JAVA_HOME" ] && [ -d "$JAVA_HOME" ]; then
    echo -e "${GREEN}[OK]${NC} ($JAVA_HOME)"
else
    echo -e "${YELLOW}[CẢNH BÁO] Biến JAVA_HOME chưa được thiết lập!${NC}"
    if [ -d "/usr/lib/jvm/java-11-openjdk-amd64" ]; then
        echo -e "   Gợi ý: export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64"
    fi
fi

# 3. Kiểm tra lệnh jps
echo -n "3. Kiểm tra lệnh 'jps': "
if command -v jps >/dev/null 2>&1; then
    echo -e "${GREEN}[OK]${NC}"
else
    echo -e "${YELLOW}[CẢNH BÁO] Không tìm thấy lệnh jps trong PATH.${NC}"
fi

# 4. Kiểm tra tiến trình HMaster
echo -n "4. Kiểm tra tiến trình 'HMaster': "
HMASTER_PID=$(jps 2>/dev/null | grep -i HMaster | awk '{print $1}')
if [ -n "$HMASTER_PID" ]; then
    echo -e "${GREEN}[OK]${NC} (HMaster đang chạy với PID: $HMASTER_PID)"
else
    echo -e "${RED}[CHƯA CHẠY] HBase HMaster chưa được khởi động!${NC}"
    echo -e "   Khởi động bằng lệnh: /mnt/d/2026/BigData/hbase/bin/start-hbase.sh"
    ERRORS=$((ERRORS + 1))
fi

# 5. Kiểm tra thư mục HBase
HBASE_DIR="/mnt/d/2026/BigData/hbase"
echo -n "5. Kiểm tra thư mục HBase ($HBASE_DIR): "
if [ -d "$HBASE_DIR" ]; then
    echo -e "${GREEN}[OK]${NC}"
else
    echo -e "${RED}[LỖI] Không tìm thấy thư mục HBase tại $HBASE_DIR!${NC}"
    ERRORS=$((ERRORS + 1))
fi

# 6. Kiểm tra thư mục Phoenix
PHOENIX_DIR="/mnt/d/2026/BigData/phoenix"
echo -n "6. Kiểm tra thư mục Phoenix ($PHOENIX_DIR): "
if [ -d "$PHOENIX_DIR" ]; then
    echo -e "${GREEN}[OK]${NC}"
else
    echo -e "${RED}[LỖI] Không tìm thấy thư mục Phoenix tại $PHOENIX_DIR!${NC}"
    ERRORS=$((ERRORS + 1))
fi

# 7. Kiểm tra file sqlline.py
SQLLINE_FILE="/mnt/d/2026/BigData/phoenix/bin/sqlline.py"
echo -n "7. Kiểm tra công cụ Phoenix SQLLine ($SQLLINE_FILE): "
if [ -f "$SQLLINE_FILE" ]; then
    echo -e "${GREEN}[OK]${NC}"
else
    echo -e "${RED}[LỖI] Không tìm thấy file sqlline.py!${NC}"
    ERRORS=$((ERRORS + 1))
fi

# 8. Kiểm tra cổng kết nối ZooKeeper (Port 2181)
echo -n "8. Kiểm tra kết nối cổng ZooKeeper (2181): "
if ss -tuln 2>/dev/null | grep -q ":2181 "; then
    echo -e "${GREEN}[OK] Cổng 2181 đang lắng nghe.${NC}"
elif netstat -tuln 2>/dev/null | grep -q ":2181 "; then
    echo -e "${GREEN}[OK] Cổng 2181 đang lắng nghe.${NC}"
else
    echo -e "${RED}[CHƯA SẴN SÀNG] Cổng 2181 chưa mở (HBase/ZooKeeper chưa chạy)!${NC}"
    ERRORS=$((ERRORS + 1))
fi

echo -e "${BLUE}======================================================${NC}"
if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}TẤT CẢ DỊCH VỤ ĐÃ SẴN SÀNG ĐỂ CHẠY DEMO!${NC}"
    exit 0
else
    echo -e "${YELLOW}CÓ $ERRORS VẤN ĐỀ CẦN XỬ LÝ TRƯỚC KHI CHẠY DEMO.${NC}"
    exit 1
fi
