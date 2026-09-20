# HƯỚNG DẪN THỰC THI DEMO APACHE PHOENIX TRÊN HBASE (BIG DATA 2026)

Tài liệu hướng dẫn triển khai, vận hành và kiểm thử toàn diện giải pháp SQL Layer **Apache Phoenix** trên nền tảng NoSQL **Apache HBase 2.5**.

---

## 1. Mục tiêu dự án

Dự án cung cấp bộ kịch bản thực nghiệm hoàn chỉnh trên môi trường **Ubuntu WSL**, chứng minh các năng lực cốt lõi của Apache Phoenix:
1. **Kiến trúc Salt Buckets (`SALT_BUCKETS = 8`)**: Tự động phân phối tải đều trên các HBase RegionServers, triệt tiêu hiện tượng thắt cổ chai ghi tuần tự (Region Hotspotting).
2. **Cơ chế UPSERT thay thế INSERT/UPDATE**: Thao tác ghi/cập nhật dữ liệu đồng nhất dựa trên Primary Key của HBase.
3. **Truy vấn SQL linh hoạt**: Hỗ trợ lọc điều kiện phức hợp (`AND`, `OR`, `IN`, `BETWEEN`), tính toán thời gian thực (`SO_LUONG * DON_GIA`), sắp xếp và phân trang (`LIMIT`).
4. **Aggregate Queries**: Tổng hợp thống kê tốc độ cao (`COUNT`, `SUM`, `AVG`, `MIN`, `MAX`, `GROUP BY`, `HAVING`).
5. **Secondary Covered Index (`INCLUDE`)**: Tối ưu hóa truy vấn đọc từ Full Table Scan thành Range Scan với chỉ mục thứ cấp bao phủ.
6. **Kế hoạch thực thi (`EXPLAIN`) & Index Hint**: Kiểm tra và điều hướng bộ tối ưu hóa truy vấn (Phoenix Query Optimizer).
7. **Xử lý Big Data**: Sinh tập dữ liệu quy mô lớn (1.000 đến 50.000+ dòng) và nạp tốc độ cao vào HBase bằng công cụ `psql.py`.
8. **Trực quan hóa Dashboard**: Theo dõi số liệu thời gian thực và quản lý DML qua giao diện Streamlit.

---

## 2. Cấu trúc thư mục dự án

```text
phoenix-demo/
├── sql/
│   ├── 00_reset.sql            # Xóa sạch bảng và index cũ để đưa về trạng thái nguyên bản
│   ├── 01_create_table.sql      # Tạo bảng GIAO_DICH với 8 Salt Buckets và kiểm tra schema
│   ├── 02_insert_data.sql       # Nạp 25 bản ghi mẫu ban đầu bằng lệnh UPSERT INTO
│   ├── 03_select_queries.sql    # 14 truy vấn chọn lọc, tìm kiếm, tính toán thành tiền
│   ├── 04_update_delete.sql     # Minh họa cập nhật qua UPSERT và xóa dữ liệu qua DELETE
│   ├── 05_aggregate_queries.sql # Các truy vấn gom nhóm, thống kê doanh thu và báo cáo ngày
│   ├── 06_index_demo.sql        # Tạo Covered Index, so sánh EXPLAIN và dùng Index Hint
│   ├── 07_performance.sql       # Đánh giá hiệu năng truy vấn có index vs không index
│   └── full_demo.sql            # Kịch bản tổng hợp 13 phần chạy tự động toàn diện
├── scripts/
│   ├── check_services.sh        # Kiểm tra Java, HMaster, ZooKeeper 2181 và đường dẫn
│   ├── start_services.sh        # Khởi động dịch vụ HBase Master/RegionServer
│   ├── run_demo.sh              # Shell script tự động thực thi kịch bản full_demo.sql
│   └── generate_large_data.py   # Công cụ Python sinh dữ liệu lớn xuất ra file CSV
├── dashboard/
│   ├── app.py                   # Ứng dụng Streamlit hiển thị KPI, biểu đồ và form DML
│   └── requirements.txt         # Danh mục thư viện Python phụ thuộc
├── data/
│   └── giao_dich_large_1000.csv # File dữ liệu lớn được sinh phục vụ kiểm thử
└── README.md                    # Tài liệu hướng dẫn thực thi duy nhất của dự án
```

---

## 3. Thiết lập môi trường JAVA_HOME

Apache HBase và Apache Phoenix yêu cầu OpenJDK 11. Để đảm bảo mọi script nhận diện đúng Java, chạy lệnh:

```bash
export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
export PATH=$JAVA_HOME/bin:$PATH
```

> **Mẹo:** Để cấu hình vĩnh viễn cho mỗi lần mở terminal WSL, thêm vào file `~/.bashrc`:
> ```bash
> echo 'export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64' >> ~/.bashrc
> echo 'export PATH=$JAVA_HOME/bin:$PATH' >> ~/.bashrc
> source ~/.bashrc
> ```

---

## 4. Cách khởi động HBase

Chạy script tự động đã được cấu hình sẵn trong dự án:

```bash
cd /mnt/d/2026/BigData/phoenix-demo
bash scripts/start_services.sh
```

Hoặc gọi trực tiếp lệnh khởi động của HBase:

```bash
export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
/mnt/d/2026/BigData/hbase/bin/start-hbase.sh
```

---

## 5. Cách kiểm tra trạng thái dịch vụ và HMaster

Kiểm tra nhanh bằng lệnh `jps`:

```bash
jps
```
Kết quả đạt chuẩn sẽ hiển thị tiến trình **HMaster**:
```text
1060 HMaster
1280 Jps
```

Để kiểm tra toàn diện cả cổng kết nối ZooKeeper (2181), phiên bản Java và các thư mục liên quan, chạy:

```bash
bash /mnt/d/2026/BigData/phoenix-demo/scripts/check_services.sh
```

---

## 6. Cách mở Phoenix SQLLine

Kết nối vào giao diện dòng lệnh tương tác của Phoenix:

```bash
cd /mnt/d/2026/BigData/phoenix/bin
./sqlline.py localhost
```

Giao diện sẵn sàng nhận lệnh khi xuất hiện dấu nhắc:
```text
0: jdbc:phoenix:localhost>
```

Để thoát SQLLine, gõ:
```sql
!quit
```

---

## 7. Cách chạy từng file SQL

Có 2 phương thức thực thi:

### Cách 1: Chạy file trực tiếp từ Terminal Linux (Không cần vào SQLLine)

```bash
cd /mnt/d/2026/BigData/phoenix/bin

# 1. Reset môi trường
python3 ./sqlline.py localhost /mnt/d/2026/BigData/phoenix-demo/sql/00_reset.sql

# 2. Tạo bảng
python3 ./sqlline.py localhost /mnt/d/2026/BigData/phoenix-demo/sql/01_create_table.sql

# 3. Nạp 25 bản ghi ban đầu
python3 ./sqlline.py localhost /mnt/d/2026/BigData/phoenix-demo/sql/02_insert_data.sql

# 4. Chạy truy vấn lọc và sắp xếp
python3 ./sqlline.py localhost /mnt/d/2026/BigData/phoenix-demo/sql/03_select_queries.sql

# 5. Cập nhật và xóa dữ liệu
python3 ./sqlline.py localhost /mnt/d/2026/BigData/phoenix-demo/sql/04_update_delete.sql

# 6. Truy vấn tổng hợp thống kê
python3 ./sqlline.py localhost /mnt/d/2026/BigData/phoenix-demo/sql/05_aggregate_queries.sql

# 7. Demo chỉ mục Secondary Index
python3 ./sqlline.py localhost /mnt/d/2026/BigData/phoenix-demo/sql/06_index_demo.sql

# 8. Đo lường hiệu năng
python3 ./sqlline.py localhost /mnt/d/2026/BigData/phoenix-demo/sql/07_performance.sql
```

### Cách 2: Chạy từ bên trong SQLLine bằng lệnh `!run`

Mở SQLLine:
```bash
/mnt/d/2026/BigData/phoenix/bin/sqlline.py localhost
```
Sau đó gõ lệnh `!run` kèm đường dẫn tuyệt đối:
```text
!run /mnt/d/2026/BigData/phoenix-demo/sql/00_reset.sql
!run /mnt/d/2026/BigData/phoenix-demo/sql/01_create_table.sql
!run /mnt/d/2026/BigData/phoenix-demo/sql/02_insert_data.sql
!run /mnt/d/2026/BigData/phoenix-demo/sql/03_select_queries.sql
!run /mnt/d/2026/BigData/phoenix-demo/sql/04_update_delete.sql
!run /mnt/d/2026/BigData/phoenix-demo/sql/05_aggregate_queries.sql
!run /mnt/d/2026/BigData/phoenix-demo/sql/06_index_demo.sql
!run /mnt/d/2026/BigData/phoenix-demo/sql/07_performance.sql
```

---

## 8. Cách chạy toàn bộ kịch bản demo tự động (`full_demo.sql`)

### Cách 1: Sử dụng Shell Script tự động (Khuyến nghị)
Script sẽ tự kiểm tra xem HBase HMaster có đang chạy hay không trước khi thực thi:

```bash
cd /mnt/d/2026/BigData/phoenix-demo
bash scripts/run_demo.sh
```

### Cách 2: Chạy qua SQLLine CLI từ Terminal
```bash
python3 /mnt/d/2026/BigData/phoenix/bin/sqlline.py localhost /mnt/d/2026/BigData/phoenix-demo/sql/full_demo.sql
```

### Cách 3: Chạy bên trong SQLLine
```text
0: jdbc:phoenix:localhost> !run /mnt/d/2026/BigData/phoenix-demo/sql/full_demo.sql
```

---

## 9. Nhập từng câu truy vấn trực tiếp trong SQLLine

Dưới đây là các câu lệnh mẫu người dùng có thể copy-paste trực tiếp vào terminal SQLLine:

```sql
-- 1. Kiểm tra danh mục bảng và cấu trúc schema
!tables
!describe GIAO_DICH

-- 2. Đếm tổng số bản ghi
SELECT COUNT(*) AS TONG_SO_GD FROM GIAO_DICH;

-- 3. Xem 10 dòng đầu tiên
SELECT *
FROM GIAO_DICH
ORDER BY MA_GIAO_DICH
LIMIT 10;

-- 4. Thống kê số giao dịch và tổng doanh thu theo khu vực
SELECT KHU_VUC,
       COUNT(*) AS SO_GIAO_DICH,
       SUM(SO_LUONG * DON_GIA) AS TONG_DOANH_THU
FROM GIAO_DICH
GROUP BY KHU_VUC
ORDER BY TONG_DOANH_THU DESC;

-- 5. Xem kế hoạch thực thi (EXPLAIN) lọc theo miền Nam
EXPLAIN
SELECT *
FROM GIAO_DICH
WHERE KHU_VUC = 'MIEN_NAM';

-- 6. Thoát khỏi SQLLine
!quit
```

---

## 10. Cách sinh dữ liệu lớn (`generate_large_data.py`)

Công cụ Python cho phép sinh dữ liệu giả lập thực tế với mã giao dịch dạng `GD_100001` trở đi, đảm bảo không bao giờ trùng lặp với `GD001`–`GD999`.

### Mặc định (Sinh 1.000 dòng):
```bash
cd /mnt/d/2026/BigData/phoenix-demo
python3 scripts/generate_large_data.py --rows 1000 --force
```

### Sinh 10.000 dòng kèm Random Seed cố định:
```bash
python3 scripts/generate_large_data.py --rows 10000 --seed 2026 --force
```

### Sinh 50.000 dòng:
```bash
python3 scripts/generate_large_data.py --rows 50000 --seed 2026 --force
```

File CSV sẽ được lưu tại thư mục: `phoenix-demo/data/giao_dich_large_<rows>.csv`.

---

## 11. Cách nạp (Import) file CSV vào Phoenix bằng `psql.py`

Apache Phoenix tích hợp sẵn tiện ích nạp dữ liệu bulk `psql.py`. Sử dụng cờ `-h in-line` để Phoenix tự động đọc header ở dòng đầu tiên:

```bash
export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
python3 /mnt/d/2026/BigData/phoenix/bin/psql.py -t GIAO_DICH -h in-line localhost /mnt/d/2026/BigData/phoenix-demo/data/giao_dich_large_1000.csv
```

Kết quả nạp thành công sẽ hiển thị:
```text
csv columns from header line. length=7, MA_GIAO_DICH, MA_KHACH_HANG, MA_SAN_PHAM, KHU_VUC, SO_LUONG, DON_GIA, THOI_GIAN
CSV Upsert complete. 1000 rows upserted
Time: 0.976 sec(s)
```

Sau khi nạp, kiểm tra lại số lượng bản ghi:
```sql
SELECT COUNT(*) FROM GIAO_DICH;
```

---

## 12. Cách chạy Dashboard giám sát (Tối ưu hóa & 8 Trang Lazy Loading)

Dashboard được xây dựng trên nền tảng **Streamlit**, truy vấn **100% dữ liệu thật** từ Phoenix/HBase, tích hợp cơ chế cache có kiểm soát `@st.cache_data(ttl=30)` và pre-check socket tránh treo ứng dụng.

### Các lệnh thực thi chính xác trên Ubuntu WSL:
```bash
cd /mnt/d/2026/BigData/phoenix-demo/dashboard
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Ứng dụng sẽ mở trên trình duyệt tại địa chỉ: `http://localhost:8501`.

**Cấu trúc 6 trang chức năng theo kịch bản demo môn Big Data:**
1. **📊 Tổng quan**: 4 thẻ KPI đồng nhất (Tổng số giao dịch, Tổng doanh thu, Giá trị giao dịch TB, Số khu vực), biểu đồ phân bổ doanh thu/giao dịch theo khu vực và danh sách 10 giao dịch gần nhất.
2. **🔍 Truy vấn dữ liệu**: Bộ lọc động (Row Key, Khu vực, Khoảng đơn giá, Sắp xếp theo đơn giá/thành tiền) trong form an toàn, tùy chọn phân trang (10, 20, 50, 100 dòng) và hiển thị rõ câu lệnh SQL.
3. **💼 Quản lý giao dịch**: Tích hợp 3 chức năng DML trong 3 tab duy nhất:
   - **➕ Thêm giao dịch**: Form nhập liệu, kiểm tra trùng lặp Row Key chống ghi đè nhầm, thực hiện `UPSERT INTO` và `COMMIT`.
   - **✏️ Cập nhật giao dịch**: Tìm theo Row Key, nạp dữ liệu cũ vào form, cập nhật bằng `UPSERT` và hiển thị so sánh trước/sau khi sửa.
   - **🗑️ Xóa giao dịch**: Tìm kiếm Row Key, hiển thị bản ghi đối soát, checkbox xác nhận an toàn trước khi bấm nút đỏ `DELETE FROM` và `COMMIT`.
4. **📈 Thống kê**: 3 nhóm báo cáo gom nhóm chuyên sâu (Theo khu vực, Top 5 sản phẩm bán chạy nhất, Top 5 khách hàng VIP) kèm biểu đồ trực quan.
5. **⚡ Index và EXPLAIN**: Quản trị Secondary Covered Index `IDX_GIAO_DICH_KHU_VUC` (tạo với mệnh đề `INCLUDE`, xóa an toàn, chạy `EXPLAIN` so sánh Full Table Scan vs Range Scan, và thử nghiệm ép `Index Hint`).
6. **🖥️ Trạng thái hệ thống**: Giám sát sức khỏe thời gian thực (ZooKeeper port 2181, tiến trình HMaster, kết nối Phoenix, bảng `GIAO_DICH`, trạng thái Index) cùng nút kiểm tra lại.

---

## 13. Cách dừng Dashboard

Tại terminal đang chạy Streamlit, nhấn tổ hợp phím:
```text
Ctrl + C
```

Nếu chạy trong môi trường ảo, thoát môi trường bằng:
```bash
deactivate
```

---

## 14. Cách đưa dữ liệu về trạng thái ban đầu (Reset)

Khi muốn dọn sạch bảng và chỉ mục để bắt đầu lại kịch bản từ đầu:

```bash
export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
python3 /mnt/d/2026/BigData/phoenix/bin/sqlline.py localhost /mnt/d/2026/BigData/phoenix-demo/sql/00_reset.sql
```

Lệnh trên sẽ:
1. Xóa Secondary Index `IDX_GIAO_DICH_KHU_VUC` an toàn (`DROP INDEX IF EXISTS`).
2. Xóa bảng chính `GIAO_DICH` an toàn (`DROP TABLE IF EXISTS`).

---

## 15. Các lỗi thường gặp và cách xử lý (Troubleshooting)

### 1. Lỗi kết nối `Connection refused` (Cổng 2181)
- **Hiện tượng:** SQLLine báo `java.net.ConnectException: Connection refused` hoặc `ReadOnlyZKClient failed for get of /hbase/hbaseid`.
- **Nguyên nhân:** HBase chưa được khởi động hoặc tiến trình ZooKeeper chưa sẵn sàng.
- **Cách khắc phục:**
  ```bash
  bash /mnt/d/2026/BigData/phoenix-demo/scripts/start_services.sh
  ```
  Đợi khoảng 5–10 giây rồi kiểm tra `jps` xem `HMaster` đã xuất hiện chưa.

### 2. Lỗi cú pháp `Syntax error. Encountered "COMMIT"` (Mã lỗi 42P00)
- **Hiện tượng:** Chạy file SQL báo `ERROR 601 (42P00): Syntax error. Encountered "COMMIT" at line 1, column 1`.
- **Nguyên nhân:** Trong Apache Phoenix, `COMMIT;` không phải là câu lệnh SQL hợp lệ. Phoenix SQLLine mặc định bật chế độ `autocommit = true`, mọi câu lệnh `UPSERT` và `DELETE` đều tự động được commit xuống HBase ngay khi thực thi.
- **Cách khắc phục:** Không sử dụng câu lệnh SQL thuần `COMMIT;`. Nếu muốn commit thủ công trong SQLLine, phải tắt autocommit trước bằng `!autocommit off` rồi mới dùng lệnh SQLLine `!commit`.

### 3. Lỗi nạp CSV: `NumberFormatException: For input string: "SO_LUONG"`
- **Hiện tượng:** Chạy `psql.py` báo lỗi định dạng số ở dòng đầu tiên.
- **Nguyên nhân:** File CSV có dòng tiêu đề (header) chứa tên cột, nhưng `psql.py` cố ép kiểu chuỗi header thành số nguyên.
- **Cách khắc phục:** Luôn thêm cờ `-h in-line` khi gọi lệnh:
  ```bash
  python3 psql.py -t GIAO_DICH -h in-line localhost <file_csv>
  ```

### 4. Lỗi thiếu `JAVA_HOME`
- **Hiện tượng:** `Error: JAVA_HOME is not set and could not be found`.
- **Cách khắc phục:** Khai báo biến môi trường:
  ```bash
  export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
  ```

### 5. Lỗi ký tự tiếng Việt hoặc alias trong SQLLine
- **Hiện tượng:** Ký tự có dấu bị hiển thị lỗi `?` hoặc lệch cột trên terminal.
- **Cách khắc phục:** Kịch bản demo sử dụng toàn bộ alias tiếng Việt **không dấu** (ví dụ: `THANH_TIEN`, `TONG_DOANH_THU`, `SO_GIAO_DICH`) để đảm bảo tính thẩm mỹ và tương thích 100% với terminal.

### 6. Dashboard báo lỗi "Không thể kết nối Apache Phoenix / Cổng 2181 chưa mở"
- **Hiện tượng:** Vừa mở trang dashboard thì xuất hiện khung cảnh báo đỏ và dừng thực thi ngay lập tức (< 1 giây).
- **Nguyên nhân:** Cơ chế pre-check socket phát hiện ZooKeeper (cổng 2181) hoặc HBase HMaster chưa chạy.
- **Cách khắc phục:**
  1. Mở terminal WSL và chạy script khởi động:
     ```bash
     bash /mnt/d/2026/BigData/phoenix-demo/scripts/start_services.sh
     ```
  2. Quay lại giao diện dashboard và nhấn nút **"Kiểm tra lại kết nối"**.

### 7. Dữ liệu trên Dashboard chưa cập nhật sau khi thao tác ngoài terminal
- **Hiện tượng:** Bạn vừa nạp dữ liệu bằng SQLLine hoặc `psql.py` nhưng Dashboard vẫn hiển thị số liệu cũ.
- **Nguyên nhân:** Dashboard kích hoạt cơ chế cache `@st.cache_data(ttl=30)` để tối ưu tốc độ duyệt trang.
- **Cách khắc phục:**
  - Nhấn nút **"🔄 Làm mới dữ liệu (Clear Cache)"** trên Sidebar của Dashboard. Bộ đệm sẽ được dọn sạch và nạp lại số liệu mới nhất từ HBase.

