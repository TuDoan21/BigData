"""
=============================================================================
MODULE: components.py
MỤC ĐÍCH: Các thành phần giao diện Streamlit Đậm Chất Công Nghệ Cao (High-Tech Cluster HUD):
- Bảng màu: Deep Cyber Navy (#0B0F19), Electric Cyan (#00F2FE), Neon Emerald (#10B981), Amber Glow (#F59E0B)
- Hiệu ứng Glassmorphism, Neon Glow & Animated Pulse Dot thời gian thực
- Thống nhất 100% tiền tệ sang Việt Nam Đồng (VNĐ)
- Trực quan hóa kiến trúc Apache Phoenix & Coprocessors phân tán
- Trực quan hóa cơ chế Salt Buckets = 8 chống Hotspotting với lưới Hex/Node Cyber
- Trực quan hóa đường ống EXPLAIN phân tán (Client Scan vs Server Coprocessor)
=============================================================================
"""

import streamlit as st
import textwrap
from formatting import format_currency, format_currency_compact, format_number


def render_html_block(html_str: str):
    """Render HTML an toàn tuyệt đối qua st.html để không bao giờ bị Markdown biến thành code block."""
    clean_html = textwrap.dedent(html_str).strip()
    if hasattr(st, "html"):
        st.html(clean_html)
    else:
        st.markdown(clean_html, unsafe_allow_html=True)


def inject_custom_css():
    """Nhúng CSS phong cách High-Tech Cyber Console, chuẩn trung tâm điều hành phân tán."""
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&family=Inter:wght@400;500;600;700;800&display=swap');

        /* Toàn cục giao diện */
        html, body, [class*="css"] {
            font-family: 'Inter', -apple-system, sans-serif;
        }

        header[data-testid="stHeader"] {
            background-color: transparent !important;
            height: 3.0rem !important;
        }

        .main, .block-container, div[data-testid="stMainBlockContainer"] {
            padding-top: 4.2rem !important;
            padding-bottom: 2rem !important;
            max-width: 98% !important;
            background-color: #F8FAFC;
        }

        /* Sidebar công nghệ cao */
        section[data-testid="stSidebar"] {
            background: linear-gradient(180deg, #070D18 0%, #0B132B 50%, #0F172A 100%) !important;
            border-right: 1px solid rgba(56, 189, 248, 0.2);
            padding-top: 1rem;
        }

        section[data-testid="stSidebar"] p, 
        section[data-testid="stSidebar"] span:not([class*="status"]):not([style*="color"]), 
        section[data-testid="stSidebar"] label {
            color: #CBD5E1;
        }

        section[data-testid="stSidebar"] hr {
            border-color: rgba(56, 189, 248, 0.15) !important;
            margin: 14px 0 !important;
        }

        section[data-testid="stSidebar"] .stRadio label {
            font-size: 0.88rem !important;
            font-weight: 500 !important;
            padding: 6px 10px;
            border-radius: 6px;
            transition: all 0.2s ease;
        }

        section[data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label:hover {
            background-color: rgba(56, 189, 248, 0.12);
            color: #38BDF8 !important;
        }

        /* Nút bấm trên Sidebar Cyber Tech đồng bộ với Status Badge */
        [data-testid="stSidebar"] div[data-testid="stHorizontalBlock"] div.stButton,
        [data-testid="stSidebar"] div[data-testid="stHorizontalBlock"] div[data-testid="stButton"],
        [data-testid="stSidebar"] div.stButton,
        [data-testid="stSidebar"] div[data-testid="stButton"] {
            margin: 0 !important;
            padding: 0 !important;
            height: 38px !important;
        }

        [data-testid="stSidebar"] div[data-testid="stHorizontalBlock"] button,
        [data-testid="stSidebar"] div.stButton button,
        [data-testid="stSidebar"] div[data-testid="stButton"] button,
        section[data-testid="stSidebar"] div[data-testid="stHorizontalBlock"] button,
        section[data-testid="stSidebar"] div.stButton button,
        section[data-testid="stSidebar"] div[data-testid="stButton"] button {
            background: linear-gradient(135deg, rgba(14, 165, 233, 0.15) 0%, rgba(2, 132, 199, 0.25) 100%) !important;
            background-color: #0B132B !important;
            border: 1px solid rgba(56, 189, 248, 0.45) !important;
            color: #38BDF8 !important;
            border-radius: 8px !important;
            font-weight: 700 !important;
            font-size: 0.82rem !important;
            font-family: 'JetBrains Mono', monospace !important;
            height: 38px !important;
            min-height: 38px !important;
            max-height: 38px !important;
            line-height: 38px !important;
            padding: 0 10px !important;
            display: inline-flex !important;
            align-items: center !important;
            justify-content: center !important;
            gap: 6px !important;
            box-shadow: 0 0 10px rgba(56, 189, 248, 0.15) !important;
            transition: all 0.2s ease !important;
            width: 100% !important;
            box-sizing: border-box !important;
            margin: 0 !important;
        }

        [data-testid="stSidebar"] div[data-testid="stHorizontalBlock"] button:hover,
        [data-testid="stSidebar"] div.stButton button:hover,
        [data-testid="stSidebar"] div[data-testid="stButton"] button:hover,
        section[data-testid="stSidebar"] div[data-testid="stHorizontalBlock"] button:hover,
        section[data-testid="stSidebar"] div.stButton button:hover,
        section[data-testid="stSidebar"] div[data-testid="stButton"] button:hover {
            background: linear-gradient(135deg, rgba(14, 165, 233, 0.35) 0%, rgba(2, 132, 199, 0.5) 100%) !important;
            background-color: #0F172A !important;
            border-color: #00F2FE !important;
            color: #FFFFFF !important;
            box-shadow: 0 0 16px rgba(0, 242, 254, 0.45) !important;
            transform: translateY(-1px) !important;
        }

        [data-testid="stSidebar"] div[data-testid="stHorizontalBlock"] button:active,
        [data-testid="stSidebar"] div.stButton button:active,
        [data-testid="stSidebar"] div[data-testid="stButton"] button:active,
        section[data-testid="stSidebar"] div.stButton button:active,
        section[data-testid="stSidebar"] div[data-testid="stButton"] button:active {
            transform: scale(0.97) !important;
        }

        [data-testid="stSidebar"] div[data-testid="stHorizontalBlock"] button p,
        [data-testid="stSidebar"] div[data-testid="stHorizontalBlock"] button div,
        [data-testid="stSidebar"] div[data-testid="stHorizontalBlock"] button span,
        [data-testid="stSidebar"] div.stButton button p,
        [data-testid="stSidebar"] div[data-testid="stButton"] button p,
        section[data-testid="stSidebar"] div.stButton button p,
        section[data-testid="stSidebar"] div[data-testid="stButton"] button p {
            color: #38BDF8 !important;
            font-family: 'JetBrains Mono', monospace !important;
            font-size: 0.82rem !important;
            font-weight: 700 !important;
            margin: 0 !important;
            padding: 0 !important;
            line-height: normal !important;
            background: transparent !important;
            background-color: transparent !important;
        }

        [data-testid="stSidebar"] div[data-testid="stHorizontalBlock"] button:hover p,
        [data-testid="stSidebar"] div[data-testid="stHorizontalBlock"] button:hover div,
        [data-testid="stSidebar"] div[data-testid="stHorizontalBlock"] button:hover span,
        [data-testid="stSidebar"] div.stButton button:hover p,
        [data-testid="stSidebar"] div[data-testid="stButton"] button:hover p,
        section[data-testid="stSidebar"] div.stButton button:hover p,
        section[data-testid="stSidebar"] div[data-testid="stButton"] button:hover p {
            color: #FFFFFF !important;
        }

        /* Bảo vệ tuyệt đối và khôi phục nút đóng/mở Sidebar của Streamlit (Material Symbols) */
        [data-testid="stSidebarCollapseButton"],
        [data-testid="stSidebarCollapseButton"] button,
        [data-testid="collapsedControl"],
        [data-testid="collapsedControl"] button,
        [data-testid="stSidebarCollapsedControl"],
        [data-testid="stSidebarCollapsedControl"] button,
        [data-testid="stSidebarHeader"] button,
        button[data-testid="baseButton-header"],
        button[data-testid="stBaseButton-header"] {
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
            width: auto !important;
            height: auto !important;
            min-height: unset !important;
            max-height: unset !important;
            line-height: normal !important;
            padding: 4px !important;
            color: #94A3B8 !important;
            transform: none !important;
        }

        [data-testid="stSidebarCollapseButton"] button:hover,
        [data-testid="collapsedControl"] button:hover,
        [data-testid="stSidebarCollapsedControl"] button:hover,
        [data-testid="stSidebarHeader"] button:hover,
        button[data-testid="baseButton-header"]:hover,
        button[data-testid="stBaseButton-header"]:hover {
            background: rgba(56, 189, 248, 0.1) !important;
            border: none !important;
            box-shadow: none !important;
            color: #38BDF8 !important;
            transform: none !important;
        }

        [data-testid="stSidebarCollapseButton"] span,
        [data-testid="collapsedControl"] span,
        [data-testid="stSidebarCollapsedControl"] span,
        [data-testid="stSidebarHeader"] button span,
        button[data-testid="baseButton-header"] span,
        button[data-testid="stBaseButton-header"] span,
        span[data-testid="stIconMaterial"],
        span[class*="material"] {
            font-family: 'Material Symbols Rounded', 'Material Symbols Outlined', 'Material Icons', sans-serif !important;
            font-style: normal !important;
            font-weight: normal !important;
            font-size: 1.25rem !important;
            line-height: 1 !important;
            letter-spacing: normal !important;
            text-transform: none !important;
            display: inline-block !important;
            white-space: nowrap !important;
            word-wrap: normal !important;
            direction: ltr !important;
            -webkit-font-feature-settings: 'liga' !important;
            -webkit-font-smoothing: antialiased !important;
        }

        /* Tiêu đề ứng dụng High-Tech Command Center HUD */
        .header-container {
            background: linear-gradient(135deg, #0A0F1D 0%, #0F172A 45%, #1E293B 100%);
            color: #FFFFFF;
            padding: 20px 26px;
            border-radius: 14px;
            margin-bottom: 18px;
            box-shadow: 0 10px 30px rgba(10, 15, 29, 0.25), inset 0 1px 0 rgba(255, 255, 255, 0.1);
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-left: 6px solid #00F2FE;
            position: relative;
            overflow: hidden;
        }

        .header-container::after {
            content: "";
            position: absolute;
            top: 0;
            right: 0;
            width: 300px;
            height: 100%;
            background: radial-gradient(circle at top right, rgba(0, 242, 254, 0.15), transparent 70%);
            pointer-events: none;
        }

        .header-title {
            font-size: 1.65rem;
            font-weight: 800;
            letter-spacing: -0.5px;
            margin: 0;
            color: #FFFFFF;
            display: flex;
            align-items: center;
            gap: 10px;
            text-shadow: 0 0 20px rgba(0, 242, 254, 0.4);
        }

        .header-subtitle {
            font-size: 0.86rem;
            color: #94A3B8;
            margin-top: 4px;
            font-family: 'JetBrains Mono', monospace;
            font-weight: 400;
        }

        .header-badges {
            display: flex;
            gap: 8px;
            align-items: center;
            flex-wrap: wrap;
            position: relative;
            z-index: 2;
        }

        .header-badge {
            background: rgba(15, 23, 42, 0.7);
            border: 1px solid rgba(56, 189, 248, 0.4);
            border-radius: 6px;
            padding: 6px 12px;
            font-size: 0.78rem;
            color: #38BDF8;
            font-family: 'JetBrains Mono', monospace;
            font-weight: 600;
            box-shadow: 0 0 10px rgba(56, 189, 248, 0.15);
        }

        .header-badge-accent {
            background: linear-gradient(135deg, #F59E0B 0%, #D97706 100%);
            border: 1px solid #FCD34D;
            border-radius: 6px;
            padding: 6px 12px;
            font-size: 0.78rem;
            color: #0F172A;
            font-family: 'JetBrains Mono', monospace;
            font-weight: 700;
            box-shadow: 0 0 15px rgba(245, 158, 11, 0.35);
        }

        /* Pulse live indicator */
        @keyframes pulse-live {
            0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }
            70% { transform: scale(1.1); box-shadow: 0 0 0 7px rgba(16, 185, 129, 0); }
            100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
        }

        .status-dot-live {
            width: 8px;
            height: 8px;
            background-color: #10B981;
            border-radius: 50%;
            display: inline-block;
            animation: pulse-live 2s infinite;
        }

        /* Status Bar Cyber HUD */
        .status-bar {
            display: flex;
            gap: 10px;
            margin-bottom: 18px;
            flex-wrap: wrap;
        }

        .status-chip {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 7px 14px;
            border-radius: 8px;
            font-size: 0.82rem;
            font-family: 'JetBrains Mono', monospace;
            font-weight: 600;
            background-color: #FFFFFF;
            border: 1px solid #E2E8F0;
            color: #1E293B;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.03);
            transition: all 0.2s ease;
        }

        .status-chip.success {
            background: linear-gradient(180deg, #F0FDF4 0%, #DCFCE7 100%);
            border-color: #86EFAC;
            color: #14532D;
        }

        .status-chip.warning {
            background: linear-gradient(180deg, #FEFCE8 0%, #FEF08A 100%);
            border-color: #FDE047;
            color: #713F12;
        }

        .status-chip.danger {
            background: linear-gradient(180deg, #FEF2F2 0%, #FEE2E2 100%);
            border-color: #FCA5A5;
            color: #7F1D1D;
        }

        .status-chip.accent {
            background: linear-gradient(180deg, #F0F9FF 0%, #E0F2FE 100%);
            border-color: #7DD3FC;
            color: #0369A1;
        }

        /* Card KPI High-Tech */
        div[data-testid="stMetric"] {
            background: linear-gradient(180deg, #FFFFFF 0%, #F8FAFC 100%);
            border: 1px solid #CBD5E1;
            border-top: 3.5px solid #0284C7;
            padding: 14px 18px;
            border-radius: 12px;
            box-shadow: 0 4px 12px rgba(15, 23, 42, 0.05);
            min-height: 104px;
            display: flex;
            flex-direction: column;
            justify-content: center;
            transition: transform 0.2s ease, box-shadow 0.2s ease, border-top-color 0.2s ease;
            position: relative;
        }

        div[data-testid="stMetric"]:hover {
            transform: translateY(-3px);
            box-shadow: 0 8px 24px rgba(2, 132, 199, 0.15);
            border-top-color: #00F2FE;
        }
        
        div[data-testid="stMetricLabel"] {
            font-size: 0.82rem !important;
            font-weight: 700 !important;
            color: #64748B !important;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        div[data-testid="stMetricValue"] {
            font-size: 1.42rem !important;
            font-weight: 800 !important;
            color: #0F172A !important;
            margin-top: 4px;
            font-family: 'JetBrains Mono', monospace;
            letter-spacing: -0.5px;
        }

        /* Nút bấm High-Tech */
        .stButton button {
            border-radius: 8px;
            font-weight: 600;
            padding: 0.5rem 1.2rem;
            font-size: 0.88rem;
            transition: all 0.2s ease-in-out;
            font-family: 'Inter', sans-serif;
        }

        .stButton button:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(59, 130, 246, 0.25);
        }

        /* Khối code SQL High-Tech Terminal */
        div[data-testid="stCodeBlock"] {
            border-radius: 10px;
            border: 1px solid rgba(59, 130, 246, 0.3);
            background-color: #0B0F19 !important;
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
        }

        /* Huy hiệu thời gian thực thi */
        .exec-chip {
            display: inline-flex;
            align-items: center;
            gap: 10px;
            background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
            border: 1px solid rgba(56, 189, 248, 0.3);
            color: #38BDF8;
            border-radius: 8px;
            padding: 6px 14px;
            font-size: 0.82rem;
            font-family: 'JetBrains Mono', monospace;
            font-weight: 600;
            margin-bottom: 12px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
        }

        /* Bucket Grid High-Tech */
        .bucket-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 12px;
            margin-top: 14px;
            margin-bottom: 18px;
        }

        .bucket-cell {
            background: linear-gradient(180deg, #FFFFFF 0%, #F8FAFC 100%);
            border: 1px solid #CBD5E1;
            border-top: 3px solid #64748B;
            border-radius: 10px;
            padding: 14px 12px;
            text-align: center;
            transition: all 0.25s ease;
            position: relative;
        }

        .bucket-cell:hover {
            transform: translateY(-2px);
            border-color: #38BDF8;
            box-shadow: 0 6px 16px rgba(56, 189, 248, 0.12);
        }

        .bucket-cell.active {
            border-color: #F59E0B;
            border-top: 3.5px solid #F59E0B;
            background: linear-gradient(180deg, #FFFBEB 0%, #FEF3C7 100%);
            box-shadow: 0 0 20px rgba(245, 158, 11, 0.35);
            transform: scale(1.03);
        }

        .bucket-num {
            font-size: 1.12rem;
            font-weight: 800;
            color: #0F172A;
            font-family: 'JetBrains Mono', monospace;
        }

        .bucket-hash {
            font-size: 0.74rem;
            color: #64748B;
            font-family: 'JetBrains Mono', monospace;
            margin-top: 2px;
            background-color: #F1F5F9;
            padding: 2px 6px;
            border-radius: 4px;
            display: inline-block;
        }

        .bucket-count {
            font-size: 0.88rem;
            font-weight: 700;
            color: #0284C7;
            margin-top: 6px;
            font-family: 'JetBrains Mono', monospace;
        }

        /* EXPLAIN Step */
        .explain-step {
            background-color: #FFFFFF;
            border-left: 4px solid #0284C7;
            border-radius: 8px;
            padding: 12px 16px;
            margin-bottom: 10px;
            font-size: 0.88rem;
            display: flex;
            align-items: center;
            gap: 14px;
            border: 1px solid #E2E8F0;
            border-left: 4px solid #0284C7;
            box-shadow: 0 1px 3px rgba(0,0,0,0.02);
        }

        .explain-badge {
            font-family: 'JetBrains Mono', monospace;
            font-weight: 700;
            padding: 3px 10px;
            border-radius: 6px;
            font-size: 0.76rem;
            text-transform: uppercase;
        }

        .explain-badge.client {
            background-color: #DBEAFE;
            color: #1E40AF;
            border: 1px solid #BFDBFE;
        }

        .explain-badge.server {
            background-color: #DCFCE7;
            color: #166534;
            border: 1px solid #BBF7D0;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_header(page_title: str = "TỔNG QUAN HỆ THỐNG"):
    """Hiển thị Header chuẩn nhận diện thương hiệu báo cáo Big Data công nghệ cao."""
    render_html_block(
        f"""
        <div class="header-container">
            <div>
                <h1 class="header-title">⚡ APACHE PHOENIX </h1>
                <div class="header-subtitle">Hệ Quản Trị Cơ Sở Dữ Liệu SQL Phân Tán Trên Apache HBase &bull; Báo Cáo Big Data 2026</div>
            </div>
            <div class="header-badges">
                <span class="header-badge">HBASE 2.5 + PHOENIX 5.2</span>
                <span class="header-badge-accent">SALT_BUCKETS = 8</span>
                <span class="header-badge">{page_title}</span>
            </div>
        </div>
        """
    )


def render_status_bar(sys_status: dict):
    """Hiển thị thanh trạng thái hạ tầng phân tán công nghệ cao với live pulse indicator."""
    zk_alive = sys_status.get("zookeeper_alive", False)
    zk_class = "success" if zk_alive else "danger"
    zk_dot = '<span class="status-dot-live"></span>' if zk_alive else '🔴'
    zk_text = f"{zk_dot} ZooKeeper: 2181 [ONLINE]" if zk_alive else "🔴 ZooKeeper: Mất kết nối"

    hm_alive = sys_status.get("hmaster_alive", False)
    hm_class = "success" if hm_alive else "danger"
    hm_dot = '<span class="status-dot-live"></span>' if hm_alive else '🔴'
    hm_text = f"{hm_dot} HBase HMaster [ACTIVE]" if hm_alive else "🔴 HBase HMaster: Chưa chạy"

    ph_conn = sys_status.get("phoenix_connected", False)
    ph_class = "success" if ph_conn else "danger"
    ph_dot = '<span class="status-dot-live"></span>' if ph_conn else '🔴'
    ph_text = f"{ph_dot} Phoenix SQLLine [RPC CONNECTED]" if ph_conn else "🔴 Phoenix: Lỗi kết nối"

    tb_exists = sys_status.get("table_exists", False)
    tb_class = "success" if tb_exists else "warning"
    rec_count = sys_status.get("record_count", 0)
    tb_dot = '<span class="status-dot-live"></span>' if tb_exists else '⚠️'
    tb_text = f"{tb_dot} Bảng GIAO_DICH ({format_number(rec_count)} dòng - VNĐ)" if tb_exists else "⚠️ Bảng GIAO_DICH: Chưa tạo"

    idx_exists = sys_status.get("index_exists", False)
    idx_class = "success" if idx_exists else "warning"
    idx_dot = '<span class="status-dot-live"></span>' if idx_exists else '⚪'
    idx_text = f"{idx_dot} Covered Index [ACTIVE]" if idx_exists else "⚪ Covered Index: Chưa tạo"

    html = f"""
    <div class="status-bar">
        <span class="status-chip {zk_class}">{zk_text}</span>
        <span class="status-chip {hm_class}">{hm_text}</span>
        <span class="status-chip {ph_class}">{ph_text}</span>
        <span class="status-chip {tb_class}">{tb_text}</span>
        <span class="status-chip {idx_class}">{idx_text}</span>
        <span class="status-chip accent">⚡ Salt Buckets: 8 Regions</span>
    </div>
    """
    render_html_block(html)


def render_kpi_cards(total_tx: int, total_customers: int, total_rev: float, avg_val: float, num_regions: int, symbol: str = "VNĐ"):
    """Hiển thị 5 KPI card công nghệ cao, thống nhất 100% sang tiền tệ VNĐ."""
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.metric("📋 Tổng Bản Ghi", format_number(total_tx))
    with c2:
        st.metric("👥 Tổng Khách Hàng", format_number(total_customers))
    with c3:
        st.metric("💰 Tổng Doanh Thu", format_currency_compact(total_rev))
    with c4:
        st.metric("📊 Giá Trị TB/Đơn", format_currency(avg_val))
    with c5:
        st.metric("📍 Thị Trường / Vùng", format_number(num_regions))


def render_execution_stats(duration_ms: float, row_count: int):
    """Hiển thị huy hiệu thời gian thực thi công nghệ cao và số bản ghi."""
    render_html_block(
        f"""
        <div class="exec-chip">
            <span>⚡ Persistent Bridge: <b>{duration_ms:,.1f} ms</b></span>
            <span>&bull;</span>
            <span>📊 Đã quét: <b>{format_number(row_count)} bản ghi</b></span>
            <span>&bull;</span>
            <span>💵 Tiền tệ: <b>VNĐ</b></span>
        </div>
        """
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
    """.strip()
    st.code(create_sql, language="sql")
    st.info("💡 Bạn có thể bấm nút khởi tạo hoặc chạy script `bash scripts/run_demo.sh` để nạp dữ liệu mẫu ban đầu.")


def render_phoenix_architecture_diagram():
    """Hiển thị sơ đồ kiến trúc các tầng của Apache Phoenix trên nền Apache HBase."""
    html = """
    <div style="background-color: #0F172A; border: 1px solid rgba(56, 189, 248, 0.3); border-radius: 12px; padding: 22px; margin-bottom: 20px; box-shadow: 0 8px 24px rgba(0,0,0,0.2);">
        <div style="text-align: center; margin-bottom: 16px;">
            <h4 style="margin: 0; color: #38BDF8; font-weight: 800; font-family: 'JetBrains Mono', monospace; letter-spacing: 0.5px;">KIẾN TRÚC PHÂN TẦNG: APACHE PHOENIX TRÊN APACHE HBASE</h4>
            <span style="font-size: 0.82rem; color: #94A3B8;">Mô hình dịch ANSI SQL sang HBase Coprocessors tính toán phân tán trực tiếp tại RegionServers</span>
        </div>
        
        <div style="display: flex; flex-direction: column; gap: 12px; max-width: 860px; margin: 0 auto;">
            
            <!-- Tầng 1: Application & SQL Client -->
            <div style="background: linear-gradient(135deg, #1E293B 0%, #334155 100%); border: 1.5px solid #64748B; border-radius: 8px; padding: 12px 18px; display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <span style="font-size: 0.75rem; font-weight: 700; color: #94A3B8; text-transform: uppercase; font-family: monospace;">Tầng 1 &bull; Client Interface</span>
                    <div style="font-size: 0.96rem; font-weight: 700; color: #FFFFFF; margin-top: 2px;">🖥️ Ứng Dụng / Streamlit Dashboard / Phoenix JDBC Client</div>
                </div>
                <span style="background-color: #0F172A; color: #38BDF8; border: 1px solid #38BDF8; padding: 3px 10px; border-radius: 6px; font-size: 0.76rem; font-weight: 600; font-family: monospace;">JDBC / Persistent SQLLine</span>
            </div>

            <div style="text-align: center; color: #38BDF8; font-size: 1rem; line-height: 1;">&darr; Biên dịch truy vấn ANSI SQL-92</div>

            <!-- Tầng 2: Phoenix Query Engine & CBO -->
            <div style="background: linear-gradient(135deg, #0369A1 0%, #0284C7 100%); border: 1.5px solid #38BDF8; border-radius: 8px; padding: 12px 18px; color: #FFFFFF; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 4px 12px rgba(2, 132, 199, 0.3);">
                <div>
                    <span style="font-size: 0.75rem; font-weight: 700; color: #BAE6FD; text-transform: uppercase; font-family: monospace;">Tầng 2 &bull; Trình Tối Ưu Hóa & Lập Lịch</span>
                    <div style="font-size: 0.96rem; font-weight: 700; margin-top: 2px;">⚡ Apache Phoenix Query Compiler & Cost-Based Optimizer (CBO)</div>
                    <div style="font-size: 0.8rem; color: #E0F2FE; margin-top: 2px;">Phân tích cú pháp SQL &bull; Lựa chọn Secondary Index &bull; Phân chia song song (Parallel 8-Way Scan)</div>
                </div>
                <span style="background-color: rgba(15, 23, 42, 0.6); color: #BAE6FD; border: 1px solid #BAE6FD; padding: 3px 10px; border-radius: 6px; font-size: 0.76rem; font-weight: 600; font-family: monospace;">SYSTEM.CATALOG</span>
            </div>

            <div style="text-align: center; color: #38BDF8; font-size: 1rem; line-height: 1;">&darr; Đẩy tính toán (Pushdown) sang Coprocessors</div>

            <!-- Tầng 3: HBase RegionServers & Coprocessors -->
            <div style="background: linear-gradient(135deg, #0F766E 0%, #0D9488 100%); border: 1.5px solid #2DD4BF; border-radius: 8px; padding: 12px 18px; color: #FFFFFF; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 4px 12px rgba(13, 148, 136, 0.3);">
                <div>
                    <span style="font-size: 0.75rem; font-weight: 700; color: #CCFBF1; text-transform: uppercase; font-family: monospace;">Tầng 3 &bull; Xử Lý Phân Tán Song Song (Server-Side)</span>
                    <div style="font-size: 0.96rem; font-weight: 700; margin-top: 2px;">🚀 HBase RegionServers + Phoenix Coprocessors</div>
                    <div style="font-size: 0.8rem; color: #F0FDFA; margin-top: 2px;">Thực thi FILTER, GROUP BY, SUM, COUNT trực tiếp tại Region chứa dữ liệu &bull; Loại bỏ tắc nghẽn mạng</div>
                </div>
                <span style="background-color: rgba(15, 23, 42, 0.6); color: #2DD4BF; border: 1px solid #2DD4BF; padding: 3px 10px; border-radius: 6px; font-size: 0.76rem; font-weight: 600; font-family: monospace;">8 Salt Buckets</span>
            </div>

            <div style="text-align: center; color: #38BDF8; font-size: 1rem; line-height: 1;">&darr; Đọc/Ghi dữ liệu dạng cột (Column-Family)</div>

            <!-- Tầng 4: HDFS / Local FS Storage -->
            <div style="background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%); border: 1.5px solid #475569; border-radius: 8px; padding: 12px 18px; color: #E2E8F0; display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <span style="font-size: 0.75rem; font-weight: 700; color: #94A3B8; text-transform: uppercase; font-family: monospace;">Tầng 4 &bull; Lưu Trữ Phân Tán Bền Vững</span>
                    <div style="font-size: 0.96rem; font-weight: 700; margin-top: 2px;">💾 HBase Storage Layer (HFiles & Write-Ahead Logs - WAL)</div>
                    <div style="font-size: 0.8rem; color: #94A3B8; margin-top: 2px;">Lưu trữ theo họ cột (Column Family '0') &bull; Tương thích HDFS / Hệ thống file cục bộ</div>
                </div>
                <span style="background-color: #0284C7; color: #FFFFFF; padding: 3px 10px; border-radius: 6px; font-size: 0.76rem; font-weight: 600; font-family: monospace;">HFile / Block Cache</span>
            </div>

        </div>
    </div>
    """
    render_html_block(html)


def render_explain_visualizer(explain_plan: str):
    """Phân tích các bước trong chuỗi EXPLAIN PLAN và hiển thị từng thẻ trực quan công nghệ cao."""
    if not explain_plan:
        st.info("Chưa có kế hoạch thực thi để trực quan hóa.")
        return

    lines = [line.strip() for line in explain_plan.strip().splitlines() if line.strip()]
    if not lines:
        return

    st.markdown("##### 🔬 Trực Quan Hóa Chuỗi Thực Thi EXPLAIN (Execution Pipeline):")

    for idx, line in enumerate(lines):
        clean_text = line.replace("CLIENT", "").strip()
        is_server = "SERVER" in line
        badge_type = "server" if is_server else "client"
        badge_label = "🖥️ SERVER COPROCESSOR" if is_server else "💻 CLIENT THREAD"
        border_col = "#10B981" if is_server else "#0284C7"

        # Nhận diện hành vi then chốt
        highlight_hint = ""
        if "RANGE SCAN" in line:
            highlight_hint = " &bull; <b style='color: #059669;'>TỐI ƯU: Sử dụng Index Range Scan (Bỏ qua Full Scan)</b>"
        elif "FULL SCAN" in line:
            highlight_hint = " &bull; <b style='color: #DC2626;'>CẢNH BÁO: Quét toàn bộ bảng HBase (Full Table Scan)</b>"
        elif "PARALLEL 8-WAY" in line:
            highlight_hint = " &bull; <b style='color: #F59E0B;'>PHÂN TÁN: Quét song song đồng thời trên 8 Salt Buckets</b>"
        elif "AGGREGATE" in line:
            highlight_hint = " &bull; <b style='color: #2563EB;'>TÍNH TOÁN: Gom nhóm và cộng dồn tại chỗ</b>"

        html_step = f"""
        <div class="explain-step" style="border-left-color: {border_col};">
            <span style="font-family: monospace; font-weight: 700; color: #64748B; font-size: 0.82rem;">BƯỚC {idx+1}</span>
            <span class="explain-badge {badge_type}">{badge_label}</span>
            <span style="color: #1E293B; font-size: 0.88rem; flex-grow: 1;"><code>{clean_text}</code>{highlight_hint}</span>
        </div>
        """
        render_html_block(html_step)


def calculate_salt_bucket(key: str, bucket_count: int = 8) -> int:
    """Tính toán Salt Bucket giả lập chuẩn thuật toán băm chuỗi của Phoenix."""
    h = 0
    for b in key.encode("utf-8"):
        h = (31 * h + b) & 0xFFFFFFFF
    return h % bucket_count


def render_salt_buckets_visualizer(keys: list[str], highlight_key: str | None = None):
    """Hiển thị lưới trực quan 8 Salt Buckets công nghệ cao với phân bổ thực tế."""
    bucket_count = 8
    buckets_data = {i: [] for i in range(bucket_count)}

    for k in keys:
        b_idx = calculate_salt_bucket(k, bucket_count)
        buckets_data[b_idx].append(k)

    target_bucket = calculate_salt_bucket(highlight_key, bucket_count) if highlight_key else -1

    cells_html = []
    for i in range(bucket_count):
        is_highlight = (i == target_bucket)
        active_cls = "active" if is_highlight else ""
        count = len(buckets_data[i])
        keys_preview = ", ".join(buckets_data[i][:3]) + ("..." if len(buckets_data[i]) > 3 else "") if buckets_data[i] else "Trống"
        
        cells_html.append(
            f'<div class="bucket-cell {active_cls}">'
            f'<div class="bucket-num">Bucket #{i}</div>'
            f'<div class="bucket-hash">Byte tiền tố: 0x0{i}</div>'
            f'<div class="bucket-count">{count} bản ghi</div>'
            f'<div style="font-size: 0.72rem; color: #64748B; margin-top: 5px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-family: monospace;">{keys_preview}</div>'
            f'</div>'
        )

    grid_content = "".join(cells_html)
    render_html_block(f'<div class="bucket-grid">{grid_content}</div>')


def render_data_cleaning_pipeline_diagram():
    """Vẽ sơ đồ quy trình ETL & làm sạch dữ liệu từ Archive vào Apache Phoenix."""
    html = """
    <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 12px; padding: 20px; margin-bottom: 24px; box-shadow: 0 4px 12px rgba(0,0,0,0.04);">
        <div style="font-weight: 800; color: #0F172A; font-size: 1.05rem; margin-bottom: 16px; display: flex; align-items: center; gap: 8px; font-family: 'JetBrains Mono', monospace;">
            <span>🔄</span> QUY TRÌNH ETL & LÀM SẠCH DỮ LIỆU ARCHIVE (QUY ĐỔI VNĐ ĐỒNG BỘ)
        </div>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 14px; position: relative;">
            
            <!-- Bước 1 -->
            <div style="background: #F8FAFC; border: 1.5px solid #CBD5E1; border-top: 4px solid #64748B; border-radius: 8px; padding: 14px;">
                <div style="font-size: 0.75rem; font-weight: 700; color: #64748B; text-transform: uppercase;">Giai đoạn 1</div>
                <div style="font-size: 0.95rem; font-weight: 700; color: #0F172A; margin: 4px 0 8px 0;">📂 Nguồn dữ liệu thô</div>
                <ul style="margin: 0; padding-left: 18px; font-size: 0.8rem; color: #475569; line-height: 1.5;">
                    <li>File: <code>archive/data.csv</code> & <code>vietnamese_tiki_products...</code></li>
                    <li>Dung lượng: <b>48.2 MB</b></li>
                    <li>Quy mô: <b>547,270</b> dòng thô</li>
                    <li>Nguồn: Kaggle E-Commerce & Tiki Việt Nam</li>
                </ul>
            </div>

            <!-- Bước 2 -->
            <div style="background: #FEF2F2; border: 1.5px solid #FECACA; border-top: 4px solid #EF4444; border-radius: 8px; padding: 14px;">
                <div style="font-size: 0.75rem; font-weight: 700; color: #DC2626; text-transform: uppercase;">Giai đoạn 2</div>
                <div style="font-size: 0.95rem; font-weight: 700; color: #991B1B; margin: 4px 0 8px 0;">🧹 Lọc dữ liệu rác & bất thường</div>
                <ul style="margin: 0; padding-left: 18px; font-size: 0.8rem; color: #7F1D1D; line-height: 1.5;">
                    <li>Loại bỏ đơn hủy/hoàn (Qty &le; 0)</li>
                    <li>Loại đơn giá &le; 0 (lỗi hạch toán)</li>
                    <li>Loại mô tả sản phẩm rỗng</li>
                    <li>Khử trùng lặp hoàn toàn</li>
                </ul>
            </div>

            <!-- Bước 3 -->
            <div style="background: #EFF6FF; border: 1.5px solid #BFDBFE; border-top: 4px solid #3B82F6; border-radius: 8px; padding: 14px;">
                <div style="font-size: 0.75rem; font-weight: 700; color: #2563EB; text-transform: uppercase;">Giai đoạn 3</div>
                <div style="font-size: 0.95rem; font-weight: 700; color: #1E40AF; margin: 4px 0 8px 0;">⚙️ Chuẩn hóa Schema & Đổi VNĐ</div>
                <ul style="margin: 0; padding-left: 18px; font-size: 0.8rem; color: #1E3A8A; line-height: 1.5;">
                    <li>Quy đổi <b>1 USD ~ 26.000 VNĐ</b> đồng nhất</li>
                    <li>Định dạng ISO <code>yyyy-MM-dd HH:mm:ss</code></li>
                    <li>Gán <b>KH_GUEST</b> cho khách vãng lai</li>
                    <li>RowKey chuẩn: <code>TX_0000001</code></li>
                </ul>
            </div>

            <!-- Bước 4 -->
            <div style="background: #F0FDF4; border: 1.5px solid #BBF7D0; border-top: 4px solid #10B981; border-radius: 8px; padding: 14px;">
                <div style="font-size: 0.75rem; font-weight: 700; color: #16A34A; text-transform: uppercase;">Giai đoạn 4</div>
                <div style="font-size: 0.95rem; font-weight: 700; color: #065F46; margin: 4px 0 8px 0;">⚡ Bulk Load & Salt Buckets</div>
                <ul style="margin: 0; padding-left: 18px; font-size: 0.8rem; color: #064E3B; line-height: 1.5;">
                    <li>Nạp tốc độ cao với <code>psql.py</code></li>
                    <li>Phân tán đều trên <b>8 Salt Buckets</b></li>
                    <li>Tự động cập nhật <b>Secondary Index</b></li>
                    <li>Truy vấn phân tích OLAP &lt; 50ms</li>
                </ul>
            </div>

        </div>
    </div>
    """
    render_html_block(html)


def render_metric_card(title: str, value: str, subtitle: str, icon: str = "📊", border_color: str = "#0284C7"):
    """Vẽ 1 thẻ metric công nghệ cao có viền màu tùy chọn."""
    render_html_block(
        f"""
        <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-top: 3.5px solid {border_color}; border-radius: 10px; padding: 14px; box-shadow: 0 2px 6px rgba(0,0,0,0.03); min-height: 100px;">
            <div style="font-size: 0.78rem; font-weight: 700; color: #64748B; text-transform: uppercase; display: flex; align-items: center; gap: 6px;">
                <span>{icon}</span> {title}
            </div>
            <div style="font-size: 1.4rem; font-weight: 800; color: #0F172A; margin: 6px 0 3px 0; font-family: 'JetBrains Mono', monospace;">
                {value}
            </div>
            <div style="font-size: 0.74rem; color: #94A3B8;">
                {subtitle}
            </div>
        </div>
        """
    )


def render_cleaning_metrics_cards(summary: dict):
    """Hiển thị các thẻ chỉ số tóm tắt sau khi lọc và làm sạch dữ liệu."""
    total_raw = summary.get("total_raw", 541909)
    valid_records = summary.get("valid_records", 524878)
    dropped_records = summary.get("dropped_records", 17031)
    guest_customers = summary.get("guest_customers", 135080)
    unique_countries = summary.get("unique_countries", 38)
    
    clean_pct = (valid_records / total_raw * 100) if total_raw > 0 else 0
    drop_pct = (dropped_records / total_raw * 100) if total_raw > 0 else 0

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        render_metric_card("Tổng dữ liệu thô", f"{total_raw:,}", "File archive/data.csv", icon="📦", border_color="#64748B")
    with col2:
        render_metric_card("Dữ liệu hợp lệ", f"{valid_records:,}", f"Đạt chuẩn {clean_pct:.1f}%", icon="✅", border_color="#10B981")
    with col3:
        render_metric_card("Bản ghi rác đã loại", f"{dropped_records:,}", f"Tỷ lệ loại {drop_pct:.1f}%", icon="🗑️", border_color="#EF4444")
    with col4:
        render_metric_card("Khách vãng lai", f"{guest_customers:,}", "Chuẩn hóa thành KH_GUEST", icon="👤", border_color="#3B82F6")
    with col5:
        render_metric_card("Thị trường / Quốc gia", f"{unique_countries}", "Quốc gia thương mại (VNĐ)", icon="🌍", border_color="#F59E0B")
