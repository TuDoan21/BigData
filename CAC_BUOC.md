Bước 1: Khởi động dịch vụ HBase
bash


cd /mnt/d/2026/BigData/phoenix-demo
bash scripts/start_services.sh
Bước 2: Kiểm tra trạng thái dịch vụ
bash


bash scripts/check_services.sh
Bước 3: Chạy toàn bộ kịch bản demo tự động (Full Demo)
bash


bash scripts/run_demo.sh
Bước 4: Chạy thủ công từng file SQL qua Terminal (Nếu muốn quan sát từng phần)
bash


export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
cd /mnt/d/2026/BigData/phoenix/bin
python3 ./sqlline.py localhost /mnt/d/2026/BigData/phoenix-demo/sql/01_create_table.sql
python3 ./sqlline.py localhost /mnt/d/2026/BigData/phoenix-demo/sql/02_insert_data.sql
python3 ./sqlline.py localhost /mnt/d/2026/BigData/phoenix-demo/sql/03_select_queries.sql
python3 ./sqlline.py localhost /mnt/d/2026/BigData/phoenix-demo/sql/04_update_delete.sql
python3 ./sqlline.py localhost /mnt/d/2026/BigData/phoenix-demo/sql/05_aggregate_queries.sql
python3 ./sqlline.py localhost /mnt/d/2026/BigData/phoenix-demo/sql/06_index_demo.sql
python3 ./sqlline.py localhost /mnt/d/2026/BigData/phoenix-demo/sql/07_performance.sql
Bước 5: Thao tác trực tiếp trong SQLLine
bash


/mnt/d/2026/BigData/phoenix/bin/sqlline.py localhost
Nhập các câu lệnh:

sql


!tables
!describe GIAO_DICH
SELECT COUNT(*) AS TONG_SO_GD FROM GIAO_DICH;
SELECT KHU_VUC, COUNT(*) AS SO_GD, SUM(SO_LUONG * DON_GIA) AS TONG_DOANH_THU
FROM GIAO_DICH
GROUP BY KHU_VUC
ORDER BY TONG_DOANH_THU DESC;
EXPLAIN
SELECT * FROM GIAO_DICH WHERE KHU_VUC = 'MIEN_NAM';
!quit
Bước 6: Sinh và nạp dữ liệu lớn vào Phoenix
bash


cd /mnt/d/2026/BigData/phoenix-demo
# 1. Sinh 10.000 dòng dữ liệu
python3 scripts/generate_large_data.py --rows 10000 --seed 2026 --force
# 2. Nạp dữ liệu CSV vào bảng GIAO_DICH bằng psql.py
export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
python3 /mnt/d/2026/BigData/phoenix/bin/psql.py -t GIAO_DICH -h in-line localhost /mnt/d/2026/BigData/phoenix-demo/data/giao_dich_large_10000.csv
Bước 7: Khởi chạy Dashboard (Tùy chọn)
bash


cd /mnt/d/2026/BigData/phoenix-demo
python3 -m venv .venv
source .venv/bin/activate
pip install -r dashboard/requirements.txt
streamlit run dashboard/app.py
(Mở trình duyệt tại http://localhost:8501. Nhấn Ctrl + C để dừng dashboard)