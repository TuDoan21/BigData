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

Công cụ Python cho phép sinh dữ liệu giả lập thực tế với mã giao dịch chuẩn hóa tiền tố `TX_` gồm 7 chữ số (`TX_0000001` trở đi), đồng bộ hoàn toàn với cấu trúc tập dữ liệu e-commerce quốc tế.

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

## 12. Hướng dẫn toàn diện cách chạy và sử dụng Dashboard Apache Phoenix

Dashboard được xây dựng trên nền tảng **Streamlit**, kết nối **100% dữ liệu thật** tới cụm Apache Phoenix / HBase thông qua kiến trúc **Persistent SQLLine JVM Bridge** tốc độ cao (< 100ms/truy vấn). Giao diện tối ưu theo chuẩn báo cáo học phần Big Data với đầy đủ 10 phân hệ nghiệp vụ, biểu đồ phân tích và công cụ quản trị.

---

### 12.1. Điều kiện tiên quyết trước khi chạy Dashboard
Trước khi khởi động Dashboard, đảm bảo cụm HBase và ZooKeeper đang ở trạng thái hoạt động:
1. **Kiểm tra cổng ZooKeeper 2181 và tiến trình HMaster:**
   ```bash
   jps
   ```
   *Kết quả phải có tiến trình `HMaster`.*

2. **Nếu HBase chưa chạy, khởi động ngay bằng lệnh:**
   ```bash
   export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
   bash /mnt/d/2026/BigData/phoenix-demo/scripts/start_services.sh
   ```
   *Hoặc gọi trực tiếp: `/mnt/d/2026/BigData/hbase/bin/start-hbase.sh`*

---

### 12.2. Các cách khởi chạy Dashboard

#### Cách 1: Chạy trực tiếp từ Ubuntu WSL (Khuyên dùng khi demo)
Mở cửa sổ dòng lệnh Terminal Ubuntu WSL và thực thi chuỗi lệnh:

```bash
# 1. Điều hướng vào thư mục dự án
cd /mnt/d/2026/BigData/phoenix-demo

# 2. Kích hoạt môi trường ảo Python
source .venv/bin/activate

# 3. Khởi chạy ứng dụng Streamlit trên cổng 8501
streamlit run dashboard/app.py --server.headless true --server.port 8501
```

#### Cách 2: Chạy từ Windows PowerShell (Không cần mở WSL thủ công)
Mở PowerShell tại máy Windows và chạy lệnh một dòng:

```powershell
wsl bash -c "cd /mnt/d/2026/BigData/phoenix-demo && source .venv/bin/activate && streamlit run dashboard/app.py --server.headless true --server.port 8501"
```

#### Cách 3: Chạy ở chế độ nền (Background Daemon)
Nếu muốn Dashboard chạy liên tục ngầm không bị đóng khi tắt cửa sổ Terminal:

```bash
cd /mnt/d/2026/BigData/phoenix-demo
source .venv/bin/activate
nohup streamlit run dashboard/app.py --server.headless true --server.port 8501 > streamlit.log 2>&1 &
```

---

### 12.3. Truy cập giao diện ứng dụng
Mở trình duyệt web bất kỳ (Chrome, Edge, Firefox) và truy cập vào địa chỉ:
- **`http://localhost:8501`** (hoặc `http://127.0.0.1:8501`)

---

### 12.4. Cấu trúc và hướng dẫn sử dụng 10 Trang chức năng của Dashboard

#### 1. 📊 Tổng Quan Hệ Thống (System Overview & Super-Batch)
- **Thanh trạng thái hạ tầng đồng bộ (Status Bar):** Giám sát trạng thái thời gian thực của 6 thành phần:
  * `🟢 ZooKeeper: 2181 Online`
  * `🟢 HBase HMaster: Active`
  * `🟢 Phoenix SQLLine: Connected`
  * `🟢 Bảng GIAO_DICH (Số lượng dòng hiện có)`
  * `🟢 Covered Index: Active`
  * `⚡ Salt Buckets: 8 Regions`
- **Bộ lọc thị trường linh hoạt (Sidebar):** Chuyển đổi tức thì phạm vi báo cáo giữa:
  * `🇻🇳 Thị trường Việt Nam (VNĐ)`: Đơn vị tiền tệ VNĐ, 3 vùng miền (`MIEN_BAC`, `MIEN_TRUNG`, `MIEN_NAM`), danh mục `SP01` - `SP08`.
  * `🌍 Thị trường Quốc tế (Archive - $)`: Đơn vị tiền tệ USD, các quốc gia Châu Âu từ tập `Online Retail` (`United Kingdom`, `Germany`, `France`...).
  * `🌐 Toàn bộ hệ thống`: Chế độ xem gộp toàn diện 5,125 bản ghi.
- **5 Thẻ KPI chuẩn Dashboard doanh nghiệp:** Tổng số giao dịch (`COUNT`), Tổng khách hàng (`COUNT DISTINCT`), Tổng doanh thu (`SUM`), Giá trị trung bình/đơn (`AVG`), Số thị trường/quốc gia.
- **2 Biểu đồ phân tích trực quan:** Biểu đồ cột phân bổ doanh thu theo vùng miền và biểu đồ đường chuỗi thời gian doanh thu ngày.
- **Top 10 giao dịch gần nhất:** Bảng đối soát các đơn hàng mới nhất phát sinh trên hệ thống.
- **Nút khởi tạo bảng nhanh:** Nếu bảng chưa tồn tại, trang cung cấp sẵn nút bấm `🔨 Khởi tạo Bảng GIAO_DICH (Salt Buckets = 8)` để tạo bảng chỉ với 1 click.

#### 2. 💼 Quản Lý Giao Dịch (CRUD & Database Pagination)
- **Phân trang chuẩn Database:** Sử dụng `LIMIT 20 OFFSET ...` trên Phoenix, cam kết tải trang siêu tốc (< 60ms), không bao giờ kéo toàn bộ 5,000+ dòng lên RAM trình duyệt.
- **Bộ lọc tìm kiếm đa năng:** Tìm nhanh theo RowKey (`TX_0000001`, `TX_0000002`), mã khách hàng (`KH_17850`, `KH_13047`), mã sản phẩm (`85123A`, `71053`) và đa chọn khu vực/quốc gia.
- **Tab ➕ Thêm Giao Dịch Mới:** Nhập liệu form, tự động kiểm tra chống trùng khóa chính (`Primary Key`), ghi dữ liệu bằng lệnh `UPSERT INTO ... VALUES (...)` và tự động `COMMIT`.
- **Tab ✏️ Sửa Giao Dịch:** Chọn mã từ danh sách hiện tại hoặc nhập mã bất kỳ, tự động đổ dữ liệu cũ vào form, cho phép cập nhật đơn giá, số lượng, khu vực qua cơ chế `UPSERT` nguyên tử.
- **Tab 🗑️ Xóa Giao Dịch:** Nhập mã cần xóa, hệ thống hiển thị chi tiết đơn hàng để người dùng đối soát, bấm xác nhận để thực thi `DELETE FROM GIAO_DICH WHERE MA_GIAO_DICH = '...'`.

#### 3. 🔍 Truy Vấn Và Thống Kê (20 Demo Queries Chuẩn Mực)
Trang được phân chia rõ ràng làm 2 Tab chuyên biệt với 20 câu truy vấn thực tế:
- **Tab 🇻🇳 10 Truy Vấn Thị Trường Việt Nam:**
  1. Danh sách 20 giao dịch nội địa
  2. Lọc đơn hàng chi nhánh `MIEN_NAM`
  3. Lọc theo khoảng thời gian Quý 1/2026 (`BETWEEN ... AND`)
  4. Tra cứu lịch sử khách hàng `KH_17850` / `KH_13047`
  5. Thống kê tổng doanh thu toàn thị trường (VNĐ)
  6. Gom nhóm doanh thu theo 3 miền (`GROUP BY KHU_VUC`)
  7. Top sản phẩm bán chạy nhất Việt Nam (`85123A`, `71053`...)
  8. Top 5 đơn hàng giá trị cao nhất
  9. Lọc khu vực đạt doanh số trên 100 triệu VNĐ (`HAVING`)
  10. Xem kế hoạch thực thi `EXPLAIN Plan` trên vùng `MIEN_NAM`
- **Tab 🌍 10 Truy Vấn Thị Trường Quốc Tế (Archive - Online Retail):**
  1. Danh sách 20 giao dịch bán lẻ thương mại điện tử
  2. Lọc đơn hàng thị trường `United Kingdom`
  3. Lọc doanh số tuần đầu tiên tháng 12/2010
  4. Tra cứu khách hàng VIP `KH_17850`
  5. Thống kê tổng doanh thu bán lẻ quốc tế ($)
  6. Thống kê doanh thu theo từng quốc gia (`Top Markets`)
  7. Top 10 mã sản phẩm bán chạy nhất quốc tế (`StockCode`)
  8. Top 10 đơn hàng giá trị cao nhất thị trường quốc tế
  9. Lọc các quốc gia có doanh số trên $1,000 (`HAVING`)
  10. Xem kế hoạch thực thi `EXPLAIN Plan` trên tập dữ liệu quốc tế
- **Thực thi 1-Click:** Mỗi câu truy vấn đều có nút "Chạy câu này", hiển thị cú pháp SQL định dạng màu, kết quả DataFrame và giải thích ý nghĩa nghiệp vụ chuyên sâu.

#### 4. 💻 Nhập Câu Truy Vấn (Interactive Phoenix SQL Console)
- Cho phép người dùng hoặc giảng viên trực tiếp gõ bất kỳ câu lệnh SQL Phoenix ANSI nào (`SELECT`, `EXPLAIN`, `UPSERT`).
- Tích hợp đo lường chính xác thời gian thực thi (mili-giây) và hiển thị kết quả trực tiếp dưới dạng bảng dữ liệu tương tác.

#### 5. ⚡ Quản Lý Index & Kế Hoạch Thực Thi (EXPLAIN Plan)
- **Quản trị Secondary Covered Index:** Nút bấm tạo / xóa chỉ mục `IDX_GIAO_DICH_KHU_VUC` kèm mệnh đề `INCLUDE (SO_LUONG, DON_GIA)`.
- **Trực quan hóa EXPLAIN Pipeline:** So sánh trực quan sự khác biệt hiệu năng giữa:
  * *Khi chưa có Index:* `PARALLEL 8-WAY FULL SCAN OVER GIAO_DICH` (quét toàn bộ bảng HBase).
  * *Khi có Covered Index:* `PARALLEL 8-WAY RANGE SCAN OVER IDX_GIAO_DICH_KHU_VUC` (chỉ đọc đúng dải dữ liệu cần tìm mà không cần trỏ ngược về bảng chính).
- **Thử nghiệm Index Hint:** Trực tiếp kiểm tra chỉ dẫn ép trình tối ưu hóa Phoenix sử dụng Index (`/*+ INDEX(GIAO_DICH IDX_GIAO_DICH_KHU_VUC) */`).

#### 6. 🧹 Làm Sạch & Dữ Liệu Archive (ETL Pipeline)
- **Quy trình ETL Big Data:** Trực quan hóa quy trình làm sạch từ tập dữ liệu thô gốc `archive/data.csv` (541,909 bản ghi) thành tập dữ liệu chuẩn mực `retail_cleaned_5000.csv`:
  * Loại bỏ các mã đơn hàng hủy (`InvoiceNo` bắt đầu bằng `C`).
  * Loại bỏ đơn hàng có đơn giá bằng 0 hoặc số lượng âm.
  * Xử lý Missing Value của trường khách hàng (`CustomerID` rỗng gán nhãn `GUEST`).
  * Chuẩn hóa định dạng thời gian `yyyy-MM-dd HH:mm:ss`.
- **Công cụ nạp Bulk Loader `psql.py`:** Hướng dẫn lệnh nạp hàng nghìn dòng vào HBase chỉ trong 1-2 giây.

#### 7. 🏛️ Kiến Trúc Hệ Thống & Salt Buckets = 8
- **Sơ đồ phân tầng Phoenix - HBase:** Trực quan hóa cách Phoenix Client kết nối ZooKeeper, dịch ANSI SQL thành HBase Coprocessors và đẩy tính toán trực tiếp xuống các RegionServers chứa dữ liệu.
- **Trực quan hóa 8 Salt Buckets:** Giải thích cơ chế chống hiện tượng nghẽn cổ chai ghi tuần tự (*Region Hotspotting*) bằng cách thêm 1 byte băm `(0x00 .. 0x07)` vào trước RowKey.
- **Công cụ băm RowKey tương tác:** Nhập mã giao dịch bất kỳ (ví dụ: `TX_0000001`, `TX_0000002`), hệ thống tính toán ngay mã Salt Bucket và hiển thị cấu trúc RowKey thực tế trên HBase.

#### 8. 📚 SYSTEM.CATALOG & Siêu Dữ Liệu (Metadata Explorer)
- Khám phá bảng siêu dữ liệu nội tại `SYSTEM.CATALOG` của Apache Phoenix.
- Hiển thị đầy đủ Schema 7 cột của bảng `GIAO_DICH`, thứ tự cột, kiểu dữ liệu SQL và ràng buộc khóa chính.
- Danh mục 29 bảng hệ thống của Phoenix quản lý hàm thống kê, chuỗi tuần tự (`SYSTEM.SEQUENCE`), chỉ mục và quyền hạn.

#### 9. 🚀 Kiểm Tra Hiệu Năng (Latency Benchmark)
- Thử nghiệm so sánh thời gian phản hồi: Kết nối thường trực Persistent JVM Bridge (< 60ms) so với khởi động tiến trình One-shot rời rạc (~3,000ms).

#### 10. 📖 Hướng Dẫn Báo Cáo Demo (Presentation Guide)
- Cung cấp checklist 6 bước trình bày mẫu dành cho nhóm sinh viên khi thuyết trình đồ án trước hội đồng giảng viên.

---

### 12.5. Cách dừng Dashboard
Tại cửa sổ Terminal đang chạy ứng dụng Streamlit, nhấn tổ hợp phím:
```text
Ctrl + C
```
Hoặc nếu chạy ngầm dưới dạng background process, dừng bằng lệnh:
```bash
pkill -f 'streamlit run dashboard/app.py'
```

---

### 12.6. Xử lý các tình huống thường gặp (Dashboard Troubleshooting)

| Hiện tượng | Nguyên nhân | Cách xử lý |
| :--- | :--- | :--- |
| **Màn hình báo đỏ "Không thể kết nối cổng 2181"** | HBase và ZooKeeper chưa được bật trong WSL | Mở Terminal WSL và chạy `bash scripts/start_services.sh`, sau đó nhấn nút "Thử kết nối lại" trên web. |
| **Huy hiệu hiển thị "Chưa tạo bảng"** | Bảng `GIAO_DICH` chưa khởi tạo trong Phoenix | Nhấn nút **"🔨 Khởi tạo Bảng GIAO_DICH"** ngay tại trang Tổng quan. |
| **Số liệu chưa cập nhật sau khi nạp CSV từ terminal** | Streamlit lưu bộ nhớ cache `@st.cache_data` | Nhấn nút **"🔄 Làm mới"** trên thanh Sidebar bên trái để xóa cache và tải lại dữ liệu mới nhất. |
| **Cổng 8501 bị chiếm dụng** | Một tiến trình Streamlit cũ vẫn đang chạy ngầm | Chạy lệnh `pkill -f streamlit` trong WSL rồi khởi chạy lại. |

---

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

