"""
=============================================================================
MODULE: components.py
MỤC ĐÍCH: Các thành phần giao diện Streamlit chuẩn hóa:
- CSS tùy biến: Nền sáng, bo góc 8px, card KPI cùng chiều cao, độ tương phản cao.
- Header chuẩn báo cáo môn Big Data.
- Hiển thị KPI, bảng dữ liệu và hộp thông báo lỗi/hướng dẫn.
=============================================================================
"""

import pandas as pd
import streamlit as st
from formatting import format_currency, format_number


def inject_custom_css():
    """Nhúng CSS định dạng giao diện sáng, tinh gọn, hiện đại và chuẩn tỷ lệ."""
    st.markdown(
        """
        <style>
        /* Toàn cục giao diện */
        .main {
            background-color: #FFFFFF;
        }
        
        /* Card KPI đồng nhất */
        div[data-testid="stMetric"] {
            background-color: #F8F9FA;
            border: 1px solid #E5E7EB;
            padding: 16px 20px;
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
            min-height: 110px;
            display: flex;
            flex-direction: column;
            justify-content: center;
        }
        
        div[data-testid="stMetricLabel"] {
            font-size: 0.88rem !important;
            font-weight: 600 !important;
            color: #4B5563 !important;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        div[data-testid="stMetricValue"] {
            font-size: 1.55rem !important;
            font-weight: 700 !important;
            color: #1E88E5 !important;
            margin-top: 4px;
        }

        /* Nút bấm */
        .stButton button {
            border-radius: 6px;
            font-weight: 500;
            padding: 0.45rem 1.1rem;
            transition: all 0.2s ease-in-out;
        }

        /* Tiêu đề trang */
        .header-title {
            font-size: 1.85rem;
            font-weight: 700;
            color: #111827;
            margin-bottom: 2px;
            letter-spacing: -0.5px;
        }

        .header-subtitle {
            font-size: 0.98rem;
            color: #4B5563;
            margin-bottom: 20px;
        }

        /* Khối code SQL */
        div[data-testid="stCodeBlock"] {
            border-radius: 6px;
            border: 1px solid #E5E7EB;
        }
        
        /* Sidebar */
        section[data-testid="stSidebar"] {
            background-color: #F9FAFB;
            border-right: 1px solid #E5E7EB;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_header():
    """Hiển thị Header theo đúng yêu cầu đề bài."""
    st.markdown('<div class="header-title">APACHE PHOENIX – QUẢN LÝ GIAO DỊCH</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="header-subtitle">Demo truy vấn và quản lý dữ liệu giao dịch trên Apache HBase bằng Phoenix SQL</div>',
        unsafe_allow_html=True,
    )


def render_kpi_cards(total_tx: int, total_rev: float, avg_val: float, num_regions: int):
    """Hiển thị 4 KPI card cùng chiều cao trên trang tổng quan."""
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Tổng Số Giao Dịch", format_number(total_tx))
    with c2:
        st.metric("Tổng Doanh Thu", format_currency(total_rev))
    with c3:
        st.metric("Giá Trị Giao Dịch TB", format_currency(avg_val))
    with c4:
        st.metric("Số Khu Vực", format_number(num_regions))


def render_connection_error_box(error_msg: str):
    """Hiển thị thông báo lỗi kết nối nhanh, rõ ràng và có hướng dẫn khắc phục."""
    st.error("🚨 KHÔNG THỂ KẾT NỐI APACHE PHOENIX TRÊN HBASE!")
    st.markdown(
        """
        **Hướng dẫn kiểm tra và khởi động dịch vụ:**
        1. Mở terminal Ubuntu WSL và chạy script khởi động:
           ```bash
           bash /mnt/d/2026/BigData/phoenix-demo/scripts/start_services.sh
           ```
        2. Hoặc khởi động HBase trực tiếp:
           ```bash
           export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
           /mnt/d/2026/BigData/hbase/bin/start-hbase.sh
           ```
        3. Đảm bảo cổng ZooKeeper `2181` và tiến trình `HMaster` đang hoạt động (`jps`).
        """
    )
    with st.expander("Chi tiết kỹ thuật từ hệ thống"):
        st.code(error_msg, language="text")


def render_table_missing_box():
    """Hiển thị thông báo và hướng dẫn tạo bảng khi bảng GIAO_DICH chưa tồn tại."""
    st.warning("⚠️ BẢNG GIAO_DICH CHƯA TỒN TẠI TRONG APACHE PHOENIX!")
    st.markdown(
        """
        Hệ thống không tìm thấy bảng `GIAO_DICH`. Hãy tạo bảng bằng câu lệnh SQL bên dưới:
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
    st.info("💡 Bạn có thể chạy `bash scripts/run_demo.sh` hoặc SQLLine để khởi tạo bảng mẫu.")
