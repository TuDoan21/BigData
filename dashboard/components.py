"""
=============================================================================
MODULE: components.py
MỤC ĐÍCH: Các thành phần giao diện Streamlit chuẩn hóa bài báo cáo môn Big Data:
- Bảng màu: Trắng (#FFFFFF), Xanh dương nhạt (#EBF5FF), Xanh đậm (#0F294A), Xanh sáng (#1E88E5)
- Bố cục cân đối, hiển thị tối ưu trên màn hình laptop, không có khoảng trống thừa.
- Thẻ KPI cùng chiều cao, icon trực quan, thanh trạng thái hạ tầng đồng bộ.
=============================================================================
"""

import streamlit as st
from formatting import format_currency, format_number


def inject_custom_css():
    """Nhúng CSS định dạng giao diện sáng, tinh gọn, hiện đại và chuẩn tỷ lệ báo cáo."""
    st.markdown(
        """
        <style>
        /* Toàn cục giao diện */
        .main, .block-container {
            padding-top: 1.5rem !important;
            padding-bottom: 2rem !important;
            max-width: 98% !important;
            background-color: #FFFFFF;
        }

        /* Sidebar gọn gàng, chuyên nghiệp */
        section[data-testid="stSidebar"] {
            background-color: #F8FAFC;
            border-right: 1px solid #E2E8F0;
            padding-top: 1rem;
        }
        
        section[data-testid="stSidebar"] .block-container {
            padding-top: 1rem !important;
        }

        /* Tiêu đề ứng dụng */
        .header-container {
            background: linear-gradient(135deg, #0F294A 0%, #1565C0 100%);
            color: #FFFFFF;
            padding: 16px 24px;
            border-radius: 10px;
            margin-bottom: 20px;
            box-shadow: 0 4px 12px rgba(15, 41, 74, 0.08);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .header-title {
            font-size: 1.65rem;
            font-weight: 700;
            letter-spacing: -0.5px;
            margin: 0;
            color: #FFFFFF;
        }

        .header-subtitle {
            font-size: 0.88rem;
            color: #E2E8F0;
            margin-top: 4px;
            font-weight: 400;
        }

        .header-badge {
            background-color: rgba(255, 255, 255, 0.18);
            border: 1px solid rgba(255, 255, 255, 0.3);
            border-radius: 6px;
            padding: 6px 12px;
            font-size: 0.8rem;
            color: #FFFFFF;
            font-weight: 600;
        }

        /* Card KPI đồng nhất, hiện đại */
        div[data-testid="stMetric"] {
            background-color: #F8FAFC;
            border: 1px solid #E2E8F0;
            padding: 12px 16px;
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.03);
            min-height: 95px;
            display: flex;
            flex-direction: column;
            justify-content: center;
            border-left: 4px solid #1E88E5;
        }
        
        div[data-testid="stMetricLabel"] {
            font-size: 0.82rem !important;
            font-weight: 600 !important;
            color: #475569 !important;
            text-transform: uppercase;
            letter-spacing: 0.3px;
        }

        div[data-testid="stMetricValue"] {
            font-size: 1.35rem !important;
            font-weight: 700 !important;
            color: #0F294A !important;
            margin-top: 2px;
        }

        /* Nút bấm tinh chỉnh */
        .stButton button {
            border-radius: 6px;
            font-weight: 600;
            padding: 0.4rem 1.0rem;
            font-size: 0.88rem;
            transition: all 0.2s ease-in-out;
        }

        /* Khối code SQL */
        div[data-testid="stCodeBlock"] {
            border-radius: 6px;
            border: 1px solid #CBD5E1;
            background-color: #0F172A !important;
        }

        /* Status Bar Widget */
        .status-bar {
            display: flex;
            gap: 12px;
            margin-bottom: 16px;
            flex-wrap: wrap;
        }

        .status-chip {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 6px 12px;
            border-radius: 6px;
            font-size: 0.82rem;
            font-weight: 500;
            background-color: #F1F5F9;
            border: 1px solid #E2E8F0;
            color: #334155;
        }

        .status-chip.success {
            background-color: #ECFDF5;
            border-color: #A7F3D0;
            color: #065F46;
        }

        .status-chip.warning {
            background-color: #FFFBEB;
            border-color: #FDE68A;
            color: #92400E;
        }

        .status-chip.danger {
            background-color: #FEF2F2;
            border-color: #FECACA;
            color: #991B1B;
        }

        /* Huy hiệu thời gian thực thi */
        .exec-chip {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            background-color: #EFF6FF;
            border: 1px solid #BFDBFE;
            color: #1E40AF;
            border-radius: 6px;
            padding: 4px 10px;
            font-size: 0.84rem;
            font-weight: 600;
            margin-bottom: 10px;
        }

        /* Section Container */
        .content-card {
            background-color: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 8px;
            padding: 16px;
            margin-bottom: 16px;
            box-shadow: 0 1px 2px rgba(0, 0, 0, 0.02);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_header(page_title: str = "TỔNG QUAN HỆ THỐNG"):
    """Hiển thị Header chuẩn nhận diện thương hiệu báo cáo Big Data."""
    st.markdown(
        f"""
        <div class="header-container">
            <div>
                <h1 class="header-title">APACHE PHOENIX DASHBOARD</h1>
                <div class="header-subtitle">Hệ Quản Trị Cơ Sở Dữ Liệu SQL Phân Tán Trên Nền Apache HBase &bull; Báo Cáo Môn Big Data 2026</div>
            </div>
            <div class="header-badge">
                {page_title}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_status_bar(sys_status: dict):
    """Hiển thị thanh trạng thái hạ tầng phân tán theo hàng ngang nhỏ gọn."""
    zk_class = "success" if sys_status.get("zookeeper_alive") else "danger"
    zk_text = "🟢 ZooKeeper: 2181 Hoạt động" if sys_status.get("zookeeper_alive") else "🔴 ZooKeeper: Mất kết nối"

    hm_class = "success" if sys_status.get("hmaster_alive") else "danger"
    hm_text = "🟢 HBase HMaster: Đang chạy" if sys_status.get("hmaster_alive") else "🔴 HBase HMaster: Chưa chạy"

    ph_class = "success" if sys_status.get("phoenix_connected") else "danger"
    ph_text = "🟢 Phoenix SQLLine: Sẵn sàng" if sys_status.get("phoenix_connected") else "🔴 Phoenix: Lỗi kết nối"

    tb_class = "success" if sys_status.get("table_exists") else "warning"
    rec_count = sys_status.get("record_count", 0)
    tb_text = f"🟢 Bảng GIAO_DICH ({format_number(rec_count)} bản ghi)" if sys_status.get("table_exists") else "⚠️ Bảng GIAO_DICH: Chưa tạo"

    idx_class = "success" if sys_status.get("index_exists") else "warning"
    idx_text = "🟢 Index: Đã kích hoạt" if sys_status.get("index_exists") else "⚪ Index: Chưa tạo"

    html = f"""
    <div class="status-bar">
        <span class="status-chip {zk_class}">{zk_text}</span>
        <span class="status-chip {hm_class}">{hm_text}</span>
        <span class="status-chip {ph_class}">{ph_text}</span>
        <span class="status-chip {tb_class}">{tb_text}</span>
        <span class="status-chip {idx_class}">{idx_text}</span>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def render_kpi_cards(total_tx: int, total_customers: int, total_rev: float, avg_val: float, num_regions: int):
    """Hiển thị 5 KPI card cùng chiều cao, cân đối trên trang tổng quan."""
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.metric("📋 Tổng Bản Ghi", format_number(total_tx))
    with c2:
        st.metric("👥 Tổng Khách Hàng", format_number(total_customers))
    with c3:
        st.metric("💰 Tổng Doanh Thu", format_currency(total_rev))
    with c4:
        st.metric("📊 Giá Trị TB/Giao Dịch", format_currency(avg_val))
    with c5:
        st.metric("📍 Số Khu Vực", format_number(num_regions))


def render_execution_stats(duration_ms: float, row_count: int):
    """Hiển thị huy hiệu thời gian thực thi và số bản ghi tìm thấy."""
    st.markdown(
        f"""
        <div class="exec-chip">
            <span>⏱️ Thời gian thực thi: <b>{duration_ms:,.1f} ms</b></span>
            <span>&bull;</span>
            <span>📊 Số bản ghi trả về: <b>{format_number(row_count)} dòng</b></span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_connection_error_box(error_msg: str):
    """Hiển thị thông báo lỗi kết nối nhanh, rõ ràng và có hướng dẫn khắc phục cụ thể."""
    st.error("🚨 KHÔNG THỂ KẾT NỐI APACHE PHOENIX / HBASE!")
    st.markdown(
        """
        **Hướng dẫn khắc phục nhanh:**
        1. Mở cửa sổ dòng lệnh Terminal (Ubuntu WSL) và chạy lệnh:
           ```bash
           bash /mnt/d/2026/BigData/phoenix-demo/scripts/start_services.sh
           ```
        2. Hoặc khởi động HBase trực tiếp bằng lệnh:
           ```bash
           export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
           /mnt/d/2026/BigData/hbase/bin/start-hbase.sh
           ```
        3. Kiểm tra cổng ZooKeeper `2181` và tiến trình `HMaster` bằng lệnh `jps`.
        """
    )
    with st.expander("Chi tiết kỹ thuật từ hệ thống"):
        st.code(error_msg, language="text")


def render_table_missing_box():
    """Hiển thị thông báo và câu lệnh DDL khi bảng GIAO_DICH chưa được khởi tạo."""
    st.warning("⚠️ BẢNG GIAO_DICH CHƯA TỒN TẠI TRONG APACHE PHOENIX!")
    st.markdown(
        """
        Hệ thống không tìm thấy bảng `GIAO_DICH`. Hãy khởi tạo bảng bằng câu lệnh SQL bên dưới:
        """
    )
    create_sql = """
CREATE TABLE GIAO_DICH (
    MA_GIAO_DICH VARCHAR NOT NULL,
    MA_KHACH_HANG VARCHAR,
    MA_SAN_PHAM VARCHAR,
    KHU_VUC VARCHAR,
    SO_LUONG INTEGER,
    DON_GIA DECIMAL(15,2),
    THOI_GIAN TIMESTAMP,
    CONSTRAINT PK PRIMARY KEY (MA_GIAO_DICH)
) SALT_BUCKETS = 8;
    """.strip()
    st.code(create_sql, language="sql")
    st.info("💡 Bạn có thể chạy script `bash scripts/run_demo.sh` để nạp dữ liệu mẫu ban đầu.")
