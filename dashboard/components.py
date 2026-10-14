"""
=============================================================================
MODULE: components.py
MỤC ĐÍCH: Hệ thống giao diện hiện đại, chuyên nghiệp cho Apache Phoenix Dashboard:
- Phong cách: Enterprise Data Platform (Data-Dense, Modern Light Theme)
- Palette: Slate (#0F172A), Tech Blue (#1E40AF, #2563EB), Emerald (#059669), Amber (#D97706)
- Typography: Inter (UI), JetBrains Mono (Code, Data, Metrics), Tabular Nums
- Biểu tượng: Inline SVG chuẩn kỹ thuật (thay thế emoji chức năng)
- Tiêu chuẩn: Vercel Web Interface Guidelines & Anthropic Frontend Design
=============================================================================
"""

import streamlit as st
import textwrap
from formatting import format_currency, format_currency_compact, format_number


# =============================================================================
# INLINE SVG ICONS (KHÔNG PHỤ THUỘC THƯ VIỆN BÊN NGOÀI, SẮC NÉT TRÊN MỌI MÀN HÌNH)
# =============================================================================

SVG_ICONS = {
    "database": '<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><ellipse cx="12" cy="5" rx="9" ry="3"></ellipse><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"></path><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"></path></svg>',
    "activity": '<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline></svg>',
    "server": '<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="2" width="20" height="8" rx="2" ry="2"></rect><rect x="2" y="14" width="20" height="8" rx="2" ry="2"></rect><line x1="6" y1="6" x2="6.01" y2="6"></line><line x1="6" y1="18" x2="6.01" y2="18"></line></svg>',
    "cpu": '<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="4" width="16" height="16" rx="2"></rect><rect x="9" y="9" width="6" height="6"></rect><line x1="9" y1="1" x2="9" y2="4"></line><line x1="15" y1="1" x2="15" y2="4"></line><line x1="9" y1="20" x2="9" y2="23"></line><line x1="15" y1="20" x2="15" y2="23"></line><line x1="20" y1="9" x2="23" y2="9"></line><line x1="20" y1="15" x2="23" y2="15"></line><line x1="1" y1="9" x2="4" y2="9"></line><line x1="1" y1="15" x2="4" y2="15"></line></svg>',
    "layers": '<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="12 2 2 7 12 12 22 7 12 2"></polygon><polyline points="2 17 12 22 22 17"></polyline><polyline points="2 12 12 17 22 12"></polyline></svg>',
    "check-circle": '<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>',
    "alert-triangle": '<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>',
    "alert-circle": '<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>',
    "zap": '<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon></svg>',
    "table": '<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2"></rect><line x1="3" y1="9" x2="21" y2="9"></line><line x1="3" y1="15" x2="21" y2="15"></line><line x1="12" y1="3" x2="12" y2="21"></line></svg>',
    "search": '<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>',
    "refresh": '<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 4 23 10 17 10"></polyline><polyline points="1 20 1 14 7 14"></polyline><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"></path></svg>',
    "terminal": '<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="4 17 10 11 4 5"></polyline><line x1="12" y1="19" x2="20" y2="19"></line></svg>',
    "clock": '<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>',
    "filter": '<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"></polygon></svg>',
    "users": '<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M23 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path></svg>',
    "globe": '<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="2" y1="12" x2="22" y2="12"></line><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path></svg>',
    "dollar-sign": '<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="1" x2="12" y2="23"></line><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"></path></svg>',
    "trending-up": '<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"></polyline><polyline points="17 6 23 6 23 12"></polyline></svg>',
    "plus-circle": '<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="16"></line><line x1="8" y1="12" x2="16" y2="12"></line></svg>',
    "edit": '<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path></svg>',
    "trash": '<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>',
    "check": '<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>',
    "crosshair": '<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="22" y1="12" x2="18" y2="12"></line><line x1="6" y1="12" x2="2" y2="12"></line><line x1="12" y1="6" x2="12" y2="2"></line><line x1="12" y1="22" x2="12" y2="18"></line></svg>',
}


def get_svg_icon(name: str, size: int = 16, color: str = "currentColor") -> str:
    """Trả về chuỗi SVG an toàn, nhẹ và sắc nét."""
    template = SVG_ICONS.get(name, SVG_ICONS["activity"])
    return template.format(size=size, color=color)


def render_html_block(html_str: str):
    """Render HTML an toàn qua st.html để không bao giờ bị Markdown parse lỗi."""
    clean_html = textwrap.dedent(html_str).strip()
    if hasattr(st, "html"):
        st.html(clean_html)
    else:
        st.markdown(clean_html, unsafe_allow_html=True)


# =============================================================================
# INJECT HỆ THỐNG CSS TOÀN DIỆN (DESIGN SYSTEM - ENTERPRISE DATA PLATFORM)
# =============================================================================

def inject_custom_css():
    """
    Nhúng hệ thống CSS thiết kế chuyên nghiệp, hiện đại:
    - Bảng màu: Nền sáng nhẹ (#F8FAFC), card trắng (#FFFFFF), viền tinh tế (#E2E8F0)
    - Typography: Inter & JetBrains Mono, Tabular Nums cho số liệu & tiền tệ
    - Focus visible & Accessibility tuân thủ chuẩn Web Interface Guidelines
    """
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&display=swap');

        /* ---------------------------------------------------------------------
           1. CẤU TRÚC TOÀN CỤC & TYPOGRAPHY
           --------------------------------------------------------------------- */
        :root {
            --font-ui: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            --font-mono: 'JetBrains Mono', "SFMono-Regular", Consolas, monospace;
            
            --bg-page: #F8FAFC;
            --surface-card: #FFFFFF;
            --border-subtle: #E2E8F0;
            --border-emphasis: #CBD5E1;
            
            --text-heading: #0F172A;
            --text-body: #334155;
            --text-muted: #64748B;
            
            --brand-primary: #1E40AF;
            --brand-interactive: #2563EB;
            --brand-light: #EFF6FF;
            
            --state-success: #059669;
            --state-success-bg: #ECFDF5;
            --state-warning: #D97706;
            --state-warning-bg: #FFFBEB;
            --state-danger: #DC2626;
            --state-danger-bg: #FEF2F2;
            --state-info: #0284C7;
            --state-info-bg: #F0F9FF;
        }

        html, body, [class*="css"] {
            font-family: var(--font-ui) !important;
            color: var(--text-body);
            -webkit-font-smoothing: antialiased;
        }

        /* Tối ưu số liệu trên bảng và biểu đồ */
        [data-testid="stMetricValue"], 
        .tabular-nums, 
        td, th, 
        .exec-chip, 
        .status-chip {
            font-variant-numeric: tabular-nums;
        }

        /* ---------------------------------------------------------------------
           2. STREAMLIT APP SHELL & CONTAINER
           --------------------------------------------------------------------- */
        header[data-testid="stHeader"] {
            background-color: transparent !important;
            height: 2.75rem !important;
        }

        .main, .block-container, div[data-testid="stMainBlockContainer"] {
            padding-top: 3.5rem !important;
            padding-bottom: 3rem !important;
            padding-left: 2rem !important;
            padding-right: 2rem !important;
            max-width: 1400px !important;
            background-color: var(--bg-page);
        }

        /* ---------------------------------------------------------------------
           3. SIDEBAR HIỆN ĐẠI (SLATE NAVIGATOR)
           --------------------------------------------------------------------- */
        section[data-testid="stSidebar"] {
            background: #0F172A !important;
            border-right: 1px solid #1E293B !important;
            padding-top: 1.25rem;
        }

        section[data-testid="stSidebar"] p, 
        section[data-testid="stSidebar"] label,
        section[data-testid="stSidebar"] span:not([class*="status"]):not([style*="color"]) {
            color: #94A3B8 !important;
            font-size: 0.86rem;
        }

        section[data-testid="stSidebar"] hr {
            border-color: #1E293B !important;
            margin: 14px 0 !important;
        }

        /* Menu điều hướng Radio trên Sidebar */
        section[data-testid="stSidebar"] .stRadio div[role="radiogroup"] {
            gap: 4px;
        }

        section[data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label {
            background-color: transparent;
            color: #CBD5E1 !important;
            border-radius: 8px;
            padding: 9px 12px !important;
            margin: 0 !important;
            font-size: 0.88rem !important;
            font-weight: 500 !important;
            transition: background-color 0.15s ease, color 0.15s ease;
            cursor: pointer;
            border: 1px solid transparent;
            display: flex;
            align-items: center;
        }

        section[data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label:hover {
            background-color: rgba(30, 41, 59, 0.9) !important;
            color: #FFFFFF !important;
        }

        section[data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label[data-checked="true"],
        section[data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label:has(input:checked) {
            background: linear-gradient(135deg, rgba(14, 165, 233, 0.2) 0%, rgba(2, 132, 199, 0.35) 100%) !important;
            color: #38BDF8 !important;
            font-weight: 700 !important;
            border: 1px solid #00F2FE !important;
            box-shadow: 0 0 12px rgba(0, 242, 254, 0.25) !important;
        }

        /* Ẩn dấu chấm tròn radio mặc định để tạo dạng menu item sạch */
        section[data-testid="stSidebar"] .stRadio input[type="radio"] {
            display: none !important;
        }
        section[data-testid="stSidebar"] .stRadio div[data-testid="stMarkdownContainer"] {
            margin-left: 0 !important;
        }

        /* Nút Làm Mới trên Sidebar */
        section[data-testid="stSidebar"] div.stButton button {
            background: rgba(14, 165, 233, 0.12) !important;
            border: 1px solid rgba(56, 189, 248, 0.45) !important;
            color: #38BDF8 !important;
            border-radius: 8px !important;
            font-weight: 700 !important;
            font-family: 'JetBrains Mono', monospace !important;
            font-size: 0.82rem !important;
            height: 38px !important;
            transition: all 0.2s ease !important;
        }

        section[data-testid="stSidebar"] div.stButton button:hover {
            background: rgba(14, 165, 233, 0.3) !important;
            border-color: #00F2FE !important;
            color: #FFFFFF !important;
            box-shadow: 0 0 14px rgba(0, 242, 254, 0.35) !important;
        }

        /* ---------------------------------------------------------------------
           4. EXECUTIVE HEADER BAR
           --------------------------------------------------------------------- */
        .header-container {
            background: #FFFFFF;
            border: 1px solid var(--border-subtle);
            border-radius: 12px;
            padding: 18px 24px;
            margin-bottom: 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
            position: relative;
        }

        .header-title {
            font-size: 1.35rem;
            font-weight: 700;
            color: var(--text-heading);
            margin: 0;
            display: flex;
            align-items: center;
            gap: 10px;
            letter-spacing: -0.02em;
        }

        .header-subtitle {
            font-size: 0.84rem;
            color: var(--text-muted);
            margin-top: 3px;
            font-weight: 400;
        }

        .header-badges {
            display: flex;
            gap: 8px;
            align-items: center;
            flex-wrap: wrap;
        }

        .header-badge {
            background: #F1F5F9;
            border: 1px solid var(--border-subtle);
            border-radius: 6px;
            padding: 5px 10px;
            font-size: 0.76rem;
            color: var(--text-body);
            font-family: var(--font-mono);
            font-weight: 600;
        }

        .header-badge-accent {
            background: #EFF6FF;
            border: 1px solid #BFDBFE;
            border-radius: 6px;
            padding: 5px 10px;
            font-size: 0.76rem;
            color: var(--brand-interactive);
            font-family: var(--font-mono);
            font-weight: 600;
        }

        /* ---------------------------------------------------------------------
           5. STATUS CHIPS & LIVE INDICATORS
           --------------------------------------------------------------------- */
        .status-bar {
            display: flex;
            gap: 8px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }

        .status-chip {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 6px 12px;
            border-radius: 7px;
            font-size: 0.8rem;
            font-family: var(--font-mono);
            font-weight: 500;
            background-color: #FFFFFF;
            border: 1px solid var(--border-subtle);
            color: var(--text-body);
            box-shadow: 0 1px 2px rgba(0, 0, 0, 0.02);
            transition: border-color 0.15s ease;
        }

        .status-chip.success {
            background-color: var(--state-success-bg);
            border-color: #A7F3D0;
            color: #065F46;
        }

        .status-chip.warning {
            background-color: var(--state-warning-bg);
            border-color: #FDE68A;
            color: #92400E;
        }

        .status-chip.danger {
            background-color: var(--state-danger-bg);
            border-color: #FECACA;
            color: #991B1B;
        }

        .status-chip.accent {
            background-color: var(--brand-light);
            border-color: #BFDBFE;
            color: #1E40AF;
        }

        @keyframes pulse-live {
            0% { transform: scale(0.95); opacity: 0.8; }
            50% { transform: scale(1.15); opacity: 1; }
            100% { transform: scale(0.95); opacity: 0.8; }
        }

        .status-dot-live {
            width: 7px;
            height: 7px;
            background-color: var(--state-success);
            border-radius: 50%;
            display: inline-block;
            animation: pulse-live 2s infinite ease-in-out;
        }

        /* ---------------------------------------------------------------------
           6. METRIC CARDS (CLEAN ENTERPRISE CARDS)
           --------------------------------------------------------------------- */
        div[data-testid="stMetric"] {
            background: #FFFFFF;
            border: 1px solid var(--border-subtle);
            border-top: 3px solid var(--brand-interactive);
            padding: 16px 18px;
            border-radius: 10px;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
            min-height: 100px;
            transition: box-shadow 0.15s ease, border-color 0.15s ease;
        }

        div[data-testid="stMetric"]:hover {
            box-shadow: 0 4px 12px rgba(15, 23, 42, 0.06);
            border-top-color: var(--brand-primary);
        }
        
        div[data-testid="stMetricLabel"] {
            font-size: 0.78rem !important;
            font-weight: 600 !important;
            color: var(--text-muted) !important;
            text-transform: uppercase;
            letter-spacing: 0.04em;
        }

        div[data-testid="stMetricValue"] {
            font-size: 1.45rem !important;
            font-weight: 700 !important;
            color: var(--text-heading) !important;
            margin-top: 4px;
            font-family: var(--font-mono);
            letter-spacing: -0.02em;
        }

        /* ---------------------------------------------------------------------
           7. NÚT BẤM (BUTTONS) - HIGH USABILITY & VISIBLE FOCUS
           --------------------------------------------------------------------- */
        .stButton button {
            border-radius: 7px !important;
            font-weight: 600 !important;
            font-size: 0.86rem !important;
            padding: 0.5rem 1.15rem !important;
            transition: all 0.15s ease-in-out !important;
            font-family: var(--font-ui) !important;
            border: 1px solid var(--border-emphasis) !important;
        }

        .stButton button:focus-visible {
            outline: 2px solid var(--brand-interactive) !important;
            outline-offset: 2px !important;
        }

        /* Nút Primary */
        .stButton button[kind="primary"] {
            background-color: var(--brand-primary) !important;
            color: #FFFFFF !important;
            border: 1px solid var(--brand-primary) !important;
        }

        .stButton button[kind="primary"]:hover {
            background-color: var(--brand-interactive) !important;
            border-color: var(--brand-interactive) !important;
            box-shadow: 0 2px 8px rgba(37, 99, 235, 0.25) !important;
        }

        /* Nút Secondary */
        .stButton button[kind="secondary"],
        .stButton button:not([kind="primary"]) {
            background-color: #FFFFFF !important;
            color: var(--text-body) !important;
        }

        .stButton button[kind="secondary"]:hover,
        .stButton button:not([kind="primary"]):hover {
            background-color: #F8FAFC !important;
            border-color: var(--brand-interactive) !important;
            color: var(--brand-interactive) !important;
        }

        /* ---------------------------------------------------------------------
           8. FORM INPUTS & SELECTS
           --------------------------------------------------------------------- */
        input[type="text"], 
        input[type="number"], 
        div[data-baseweb="select"] > div {
            border-radius: 7px !important;
            border-color: var(--border-emphasis) !important;
            font-size: 0.88rem !important;
            background-color: #FFFFFF !important;
        }

        input[type="text"]:focus, 
        input[type="number"]:focus,
        div[data-baseweb="select"]:focus-within {
            border-color: var(--brand-interactive) !important;
            box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.12) !important;
        }

        /* ---------------------------------------------------------------------
           9. TABS NAVIGATION
           --------------------------------------------------------------------- */
        div[data-testid="stTabs"] button[role="tab"] {
            font-size: 0.88rem !important;
            font-weight: 600 !important;
            color: var(--text-muted) !important;
            padding: 8px 16px !important;
        }

        div[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
            color: var(--brand-interactive) !important;
            border-bottom: 2px solid var(--brand-interactive) !important;
        }

        /* ---------------------------------------------------------------------
           10. BẢNG DỮ LIỆU & HUY HIỆU THỜI GIAN THỰC THI
           --------------------------------------------------------------------- */
        .exec-chip {
            display: inline-flex;
            align-items: center;
            gap: 10px;
            background-color: #FFFFFF;
            border: 1px solid var(--border-subtle);
            color: var(--text-body);
            border-radius: 7px;
            padding: 6px 12px;
            font-size: 0.8rem;
            font-family: var(--font-mono);
            font-weight: 500;
            margin-bottom: 12px;
            box-shadow: 0 1px 2px rgba(0, 0, 0, 0.02);
        }

        .exec-chip b {
            color: var(--brand-primary);
            font-weight: 700;
        }

        /* Grid Salt Buckets */
        .bucket-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 12px;
            margin: 14px 0 18px 0;
        }

        .bucket-cell {
            background-color: #FFFFFF;
            border: 1px solid var(--border-subtle);
            border-top: 3px solid #64748B;
            border-radius: 9px;
            padding: 14px 12px;
            text-align: center;
            transition: all 0.2s ease;
        }

        .bucket-cell:hover {
            border-color: #94A3B8;
            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.04);
        }

        .bucket-cell.active {
            border-color: #D97706;
            border-top: 3px solid #D97706;
            background-color: #FFFBEB;
            box-shadow: 0 2px 8px rgba(217, 119, 6, 0.15);
        }

        .bucket-num {
            font-size: 1.05rem;
            font-weight: 700;
            color: var(--text-heading);
            font-family: var(--font-mono);
        }

        .bucket-hash {
            font-size: 0.74rem;
            color: var(--text-muted);
            font-family: var(--font-mono);
            margin-top: 2px;
            background-color: #F1F5F9;
            padding: 2px 6px;
            border-radius: 4px;
            display: inline-block;
        }

        .bucket-count {
            font-size: 0.86rem;
            font-weight: 600;
            color: var(--brand-interactive);
            margin-top: 6px;
            font-family: var(--font-mono);
        }

        /* EXPLAIN Step */
        .explain-step {
            background-color: #FFFFFF;
            border-radius: 8px;
            padding: 12px 16px;
            margin-bottom: 10px;
            font-size: 0.86rem;
            display: flex;
            align-items: center;
            gap: 12px;
            border: 1px solid var(--border-subtle);
            border-left: 4px solid var(--brand-interactive);
            box-shadow: 0 1px 2px rgba(0,0,0,0.02);
        }

        .explain-badge {
            font-family: var(--font-mono);
            font-weight: 600;
            padding: 3px 8px;
            border-radius: 5px;
            font-size: 0.72rem;
            letter-spacing: 0.03em;
            display: inline-flex;
            align-items: center;
            gap: 5px;
        }

        .explain-badge.client {
            background-color: #EFF6FF;
            color: #1E40AF;
            border: 1px solid #BFDBFE;
        }

        .explain-badge.server {
            background-color: #ECFDF5;
            color: #065F46;
            border: 1px solid #A7F3D0;
        }

        /* Terminal SQL Output */
        div[data-testid="stCodeBlock"] {
            border-radius: 8px;
            border: 1px solid #1E293B;
            background-color: #0F172A !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


# =============================================================================
# =============================================================================
# HEADER EXECUTIVE (APACHE PHOENIX CLUSTER HUD)
# =============================================================================

def render_header(page_title: str = "TỔNG QUAN HỆ THỐNG"):
    """Hiển thị Header công nghệ cao nhận diện thương hiệu phân tán Apache Phoenix."""
    zap_icon = get_svg_icon("zap", size=22, color="#00F2FE")
    render_html_block(
        f"""
        <div style="background: linear-gradient(135deg, #0B132B 0%, #172554 50%, #0F172A 100%); border: 1px solid rgba(56, 189, 248, 0.35); border-left: 5px solid #00F2FE; border-radius: 12px; padding: 16px 22px; margin-bottom: 20px; box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15); display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 14px;">
            <div style="display: flex; align-items: center; gap: 14px;">
                <div style="display: inline-flex; align-items: center; justify-content: center; width: 44px; height: 44px; border-radius: 10px; background: linear-gradient(135deg, #0284C7 0%, #0369A1 100%); color: #00F2FE; box-shadow: 0 0 16px rgba(0, 242, 254, 0.4); flex-shrink: 0;">
                    {zap_icon}
                </div>
                <div>
                    <h2 style="margin: 0; color: #F8FAFC; font-weight: 800; font-size: 1.28rem; font-family: 'JetBrains Mono', monospace; letter-spacing: -0.3px; display: flex; align-items: center; gap: 8px;">
                        APACHE PHOENIX CLUSTER HUD
                    </h2>
                    
                </div>
            </div>
            <div style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap;">
                <span style="background: rgba(15, 23, 42, 0.8); border: 1px solid rgba(56, 189, 248, 0.4); border-radius: 6px; padding: 5px 12px; color: #38BDF8; font-size: 0.76rem; font-family: 'JetBrains Mono', monospace; font-weight: 700;">
                    HBASE 2.5 + PHOENIX 5.2
                </span>
                <span style="background: rgba(245, 158, 11, 0.15); border: 1px solid rgba(245, 158, 11, 0.5); border-radius: 6px; padding: 5px 12px; color: #F59E0B; font-size: 0.76rem; font-family: 'JetBrains Mono', monospace; font-weight: 700;">
                    SALT_BUCKETS = 8
                </span>
                <span style="background: linear-gradient(135deg, #1E40AF 0%, #2563EB 100%); border-radius: 6px; padding: 5px 14px; color: #FFFFFF; font-size: 0.76rem; font-family: 'JetBrains Mono', monospace; font-weight: 700; box-shadow: 0 2px 8px rgba(37, 99, 235, 0.35);">
                    {page_title}
                </span>
            </div>
        </div>
        """
    )


# =============================================================================
# STATUS BAR
# =============================================================================

def render_status_bar(sys_status: dict):
    """Hiển thị thanh trạng thái hạ tầng phân tán công nghệ cao với live pulse indicator."""
    zk_alive = sys_status.get("zookeeper_alive", False)
    zk_class = "success" if zk_alive else "danger"
    zk_dot = '<span class="status-dot-live"></span>' if zk_alive else '<span style="color:#DC2626;">●</span>'
    zk_text = f"{zk_dot} ZooKeeper 2181 [ONLINE]" if zk_alive else "● ZooKeeper: Mất kết nối"

    hm_alive = sys_status.get("hmaster_alive", False)
    hm_class = "success" if hm_alive else "danger"
    hm_dot = '<span class="status-dot-live"></span>' if hm_alive else '<span style="color:#DC2626;">●</span>'
    hm_text = f"{hm_dot} HBase HMaster [ACTIVE]" if hm_alive else "● HBase HMaster: Chưa chạy"

    ph_conn = sys_status.get("phoenix_connected", False)
    ph_class = "success" if ph_conn else "danger"
    ph_dot = '<span class="status-dot-live"></span>' if ph_conn else '<span style="color:#DC2626;">●</span>'
    ph_text = f"{ph_dot} Phoenix SQLLine [RPC CONNECTED]" if ph_conn else "● Phoenix: Lỗi kết nối"

    tb_exists = sys_status.get("table_exists", False)
    tb_class = "success" if tb_exists else "warning"
    rec_count = sys_status.get("record_count", 0)
    tb_dot = '<span class="status-dot-live"></span>' if tb_exists else '▲'
    tb_text = f"{tb_dot} Bảng GIAO_DICH ({format_number(rec_count)} dòng)" if tb_exists else "▲ Bảng GIAO_DICH: Chưa tạo"

    idx_exists = sys_status.get("index_exists", False)
    idx_class = "success" if idx_exists else "warning"
    idx_dot = '<span class="status-dot-live"></span>' if idx_exists else '○'
    idx_text = f"{idx_dot} Covered Index [ACTIVE]" if idx_exists else "○ Covered Index: Chưa tạo"

    zap_icon = get_svg_icon("zap", size=14, color="#1E40AF")

    html = f"""
    <div class="status-bar">
        <span class="status-chip {zk_class}">{zk_text}</span>
        <span class="status-chip {hm_class}">{hm_text}</span>
        <span class="status-chip {ph_class}">{ph_text}</span>
        <span class="status-chip {tb_class}">{tb_text}</span>
        <span class="status-chip {idx_class}">{idx_text}</span>
        <span class="status-chip accent">{zap_icon} Salt Buckets: 8 Regions</span>
    </div>
    """
    render_html_block(html)


# =============================================================================
# KPI CARDS
# =============================================================================

def render_kpi_cards(total_tx: int, total_customers: int, total_rev: float, avg_val: float, num_regions: int, symbol: str = "VNĐ"):
    """Hiển thị 5 KPI card công nghệ cao, màu sắc sang trọng, thống nhất 100% sang tiền tệ VNĐ."""
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        render_metric_card("Tổng Giao Dịch", format_number(total_tx), "Lưu trữ phân tán HBase", icon="database", border_color="#2563EB")
    with c2:
        render_metric_card("Tổng Khách Hàng", format_number(total_customers), "Đã định danh chuẩn 100%", icon="users", border_color="#0D9488")
    with c3:
        render_metric_card("Tổng Doanh Thu", format_currency_compact(total_rev), "Hợp nhất VNĐ (x26)", icon="dollar-sign", border_color="#059669")
    with c4:
        render_metric_card("Giá Trị TB / Đơn", format_currency(avg_val), "Doanh thu / Giao dịch", icon="trending-up", border_color="#D97706")
    with c5:
        render_metric_card("Thị Trường / Vùng", format_number(num_regions), "12 tỉnh VN + 12 QT", icon="globe", border_color="#7C3AED")


# =============================================================================
# HUY HIỆU THỜI GIAN THỰC THI & SỐ BẢN GHI
# =============================================================================

def render_execution_stats(duration_ms: float, row_count: int):
    """Hiển thị huy hiệu thời gian thực thi công nghệ cao và số bản ghi."""
    render_html_block(
        f"""
        <div style="display: inline-flex; align-items: center; gap: 10px; background: #0B132B; border: 1px solid #1E293B; border-radius: 8px; padding: 7px 14px; font-family: 'JetBrains Mono', monospace; font-size: 0.8rem; box-shadow: 0 2px 8px rgba(0,0,0,0.12); margin-bottom: 14px;">
            <span style="color: #F59E0B; display: inline-flex; align-items: center; gap: 5px;">
                {get_svg_icon('zap', size=13, color='#F59E0B')} Persistent Bridge: <b style="color: #38BDF8;">{duration_ms:,.1f} ms</b>
            </span>
            <span style="color: #475569;">&bull;</span>
            <span style="color: #94A3B8; display: inline-flex; align-items: center; gap: 5px;">
                {get_svg_icon('table', size=13, color='#94A3B8')} Đã quét: <b style="color: #38BDF8;">{format_number(row_count)} bản ghi</b>
            </span>
            <span style="color: #475569;">&bull;</span>
            <span style="color: #94A3B8; display: inline-flex; align-items: center; gap: 5px;">
                {get_svg_icon('dollar-sign', size=13, color='#10B981')} Tiền tệ: <b style="color: #10B981;">VNĐ</b>
            </span>
        </div>
        """
    )


# =============================================================================
# HỘP THÔNG BÁO LỖI VÀ BẢNG THIẾU
# =============================================================================

def render_connection_error_box(error_msg: str):
    """Hiển thị thông báo lỗi kết nối rõ ràng với hướng dẫn xử lý."""
    st.error("Không thể kết nối tới Apache Phoenix hoặc HBase ZooKeeper")
    st.markdown(
        """
        **Hướng dẫn khắc phục nhanh:**
        1. Kiểm tra tiến trình HBase trong terminal Ubuntu WSL2:
           ```bash
           bash /mnt/d/2026/BigData/phoenix-demo/scripts/start_services.sh
           ```
        2. Đảm bảo cổng ZooKeeper `2181` đang mở và tiến trình `HMaster` đang chạy (`jps`).
        """
    )
    with st.expander("Chi tiết kỹ thuật từ hệ thống"):
        st.code(error_msg, language="text")


def render_table_missing_box():
    """Hiển thị thông báo khi bảng GIAO_DICH chưa được khởi tạo."""
    st.warning("Bảng GIAO_DICH chưa tồn tại trong Apache Phoenix.")
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


# =============================================================================
# KIẾN TRÚC PHÂN TẦNG (APACHE PHOENIX TRÊN HBASE)
# =============================================================================

def render_phoenix_architecture_diagram():
    """Hiển thị sơ đồ kiến trúc các tầng của Apache Phoenix trên nền Apache HBase."""
    server_icon = get_svg_icon("server", size=18, color="#1E40AF")
    cpu_icon = get_svg_icon("cpu", size=18, color="#059669")
    db_icon = get_svg_icon("database", size=18, color="#D97706")
    layers_icon = get_svg_icon("layers", size=18, color="#2563EB")

    html = f"""
    <div style="background-color: #FFFFFF; border: 1px solid var(--border-subtle); border-radius: 12px; padding: 22px; margin-bottom: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.03);">
        <div style="text-align: center; margin-bottom: 20px;">
            <h4 style="margin: 0; color: #0F172A; font-weight: 700; font-size: 1.05rem;">KIẾN TRÚC PHÂN TẦNG: APACHE PHOENIX TRÊN APACHE HBASE</h4>
            <span style="font-size: 0.82rem; color: #64748B;">Mô hình biên dịch ANSI SQL sang HBase Coprocessors tính toán phân tán trực tiếp tại RegionServers</span>
        </div>
        
        <div style="display: flex; flex-direction: column; gap: 10px; max-width: 860px; margin: 0 auto;">
            
            <!-- Tầng 1: Application & SQL Client -->
            <div style="background: #F8FAFC; border: 1px solid #CBD5E1; border-radius: 8px; padding: 12px 18px; display: flex; justify-content: space-between; align-items: center;">
                <div style="display: flex; align-items: center; gap: 12px;">
                    <div style="background: #EFF6FF; padding: 8px; border-radius: 6px; border: 1px solid #BFDBFE;">{server_icon}</div>
                    <div>
                        <span style="font-size: 0.72rem; font-weight: 700; color: #64748B; text-transform: uppercase;">Tầng 1 &bull; Client Interface</span>
                        <div style="font-size: 0.94rem; font-weight: 600; color: #0F172A;">Streamlit Dashboard / Phoenix JDBC Client</div>
                    </div>
                </div>
                <span style="background: #FFFFFF; color: #1E40AF; border: 1px solid #BFDBFE; padding: 4px 10px; border-radius: 6px; font-size: 0.76rem; font-weight: 600; font-family: monospace;">JDBC / SQLLine Bridge</span>
            </div>

            <div style="text-align: center; color: #64748B; font-size: 0.8rem; font-family: monospace;">&darr; Biên dịch truy vấn ANSI SQL-92</div>

            <!-- Tầng 2: Phoenix Query Engine & CBO -->
            <div style="background: #EFF6FF; border: 1px solid #93C5FD; border-radius: 8px; padding: 12px 18px; display: flex; justify-content: space-between; align-items: center;">
                <div style="display: flex; align-items: center; gap: 12px;">
                    <div style="background: #DBEAFE; padding: 8px; border-radius: 6px; border: 1px solid #93C5FD;">{layers_icon}</div>
                    <div>
                        <span style="font-size: 0.72rem; font-weight: 700; color: #1D4ED8; text-transform: uppercase;">Tầng 2 &bull; Trình Tối Ưu Hóa & Lập Lịch</span>
                        <div style="font-size: 0.94rem; font-weight: 600; color: #1E3A8A;">Apache Phoenix Query Compiler & Cost-Based Optimizer (CBO)</div>
                        <div style="font-size: 0.78rem; color: #2563EB;">Phân tích cú pháp SQL &bull; Lựa chọn Secondary Index &bull; Quét song song (Parallel 8-Way Scan)</div>
                    </div>
                </div>
                <span style="background: #FFFFFF; color: #1E40AF; border: 1px solid #93C5FD; padding: 4px 10px; border-radius: 6px; font-size: 0.76rem; font-weight: 600; font-family: monospace;">SYSTEM.CATALOG</span>
            </div>

            <div style="text-align: center; color: #64748B; font-size: 0.8rem; font-family: monospace;">&darr; Đẩy tính toán (Pushdown) sang Coprocessors</div>

            <!-- Tầng 3: HBase RegionServers & Coprocessors -->
            <div style="background: #ECFDF5; border: 1px solid #6EE7B7; border-radius: 8px; padding: 12px 18px; display: flex; justify-content: space-between; align-items: center;">
                <div style="display: flex; align-items: center; gap: 12px;">
                    <div style="background: #D1FAE5; padding: 8px; border-radius: 6px; border: 1px solid #6EE7B7;">{cpu_icon}</div>
                    <div>
                        <span style="font-size: 0.72rem; font-weight: 700; color: #047857; text-transform: uppercase;">Tầng 3 &bull; Xử Lý Phân Tán Song Song (Server-Side)</span>
                        <div style="font-size: 0.94rem; font-weight: 600; color: #064E3B;">HBase RegionServers + Phoenix Coprocessors</div>
                        <div style="font-size: 0.78rem; color: #059669;">Thực thi FILTER, GROUP BY, SUM, COUNT trực tiếp tại Region &bull; Giảm thiểu truyền dữ liệu qua mạng</div>
                    </div>
                </div>
                <span style="background: #FFFFFF; color: #065F46; border: 1px solid #6EE7B7; padding: 4px 10px; border-radius: 6px; font-size: 0.76rem; font-weight: 600; font-family: monospace;">8 Salt Buckets</span>
            </div>

            <div style="text-align: center; color: #64748B; font-size: 0.8rem; font-family: monospace;">&darr; Đọc/Ghi dữ liệu dạng cột (Column-Family)</div>

            <!-- Tầng 4: HDFS / Local FS Storage -->
            <div style="background: #FFFBEB; border: 1px solid #FCD34D; border-radius: 8px; padding: 12px 18px; display: flex; justify-content: space-between; align-items: center;">
                <div style="display: flex; align-items: center; gap: 12px;">
                    <div style="background: #FEF3C7; padding: 8px; border-radius: 6px; border: 1px solid #FCD34D;">{db_icon}</div>
                    <div>
                        <span style="font-size: 0.72rem; font-weight: 700; color: #B45309; text-transform: uppercase;">Tầng 4 &bull; Lưu Trữ Phân Tán Bền Vững</span>
                        <div style="font-size: 0.94rem; font-weight: 600; color: #78350F;">HBase Storage Layer (HFiles & Write-Ahead Logs - WAL)</div>
                        <div style="font-size: 0.78rem; color: #92400E;">Lưu trữ theo Column Family ('0') &bull; Tương thích HDFS / Hệ thống tệp cục bộ</div>
                    </div>
                </div>
                <span style="background: #FFFFFF; color: #92400E; border: 1px solid #FCD34D; padding: 4px 10px; border-radius: 6px; font-size: 0.76rem; font-weight: 600; font-family: monospace;">HFile / Block Cache</span>
            </div>

        </div>
    </div>
    """
    render_html_block(html)


# =============================================================================
# EXPLAIN PLAN VISUALIZER
# =============================================================================

def render_explain_visualizer(explain_plan: str):
    """Phân tích các bước trong chuỗi EXPLAIN PLAN và hiển thị từng bước rõ ràng."""
    if not explain_plan:
        st.info("Chưa có kế hoạch thực thi để hiển thị.")
        return

    lines = [line.strip() for line in explain_plan.strip().splitlines() if line.strip()]
    if not lines:
        return

    st.markdown("##### Kế hoạch thực thi EXPLAIN (Execution Pipeline):")

    server_icon = get_svg_icon("cpu", size=13, color="#065F46")
    client_icon = get_svg_icon("server", size=13, color="#1E40AF")

    for idx, line in enumerate(lines):
        clean_text = line.replace("CLIENT", "").strip()
        is_server = "SERVER" in line
        badge_type = "server" if is_server else "client"
        badge_label = f"{server_icon} SERVER COPROCESSOR" if is_server else f"{client_icon} CLIENT THREAD"
        border_col = "#059669" if is_server else "#2563EB"

        highlight_hint = ""
        if "RANGE SCAN" in line:
            highlight_hint = " &bull; <b style='color: #059669;'>TỐI ƯU: Sử dụng Index Range Scan (Bỏ qua Full Table Scan)</b>"
        elif "FULL SCAN" in line:
            highlight_hint = " &bull; <b style='color: #DC2626;'>CẢNH BÁO: Quét toàn bộ bảng HBase (Full Table Scan)</b>"
        elif "PARALLEL 8-WAY" in line:
            highlight_hint = " &bull; <b style='color: #D97706;'>PHÂN TÁN: Quét song song trên 8 Salt Buckets</b>"
        elif "AGGREGATE" in line:
            highlight_hint = " &bull; <b style='color: #2563EB;'>TÍNH TOÁN: Gom nhóm và cộng dồn tại chỗ</b>"

        html_step = f"""
        <div class="explain-step" style="border-left-color: {border_col};">
            <span style="font-family: monospace; font-weight: 700; color: #64748B; font-size: 0.8rem; min-width: 60px;">BƯỚC {idx+1}</span>
            <span class="explain-badge {badge_type}">{badge_label}</span>
            <span style="color: #1E293B; font-size: 0.86rem; flex-grow: 1;"><code>{clean_text}</code>{highlight_hint}</span>
        </div>
        """
        render_html_block(html_step)


# =============================================================================
# SALT BUCKETS VISUALIZER
# =============================================================================

def calculate_salt_bucket(key: str, bucket_count: int = 8) -> int:
    """Tính toán Salt Bucket giả lập chuẩn thuật toán băm chuỗi của Phoenix."""
    h = 0
    for b in key.encode("utf-8"):
        h = (31 * h + b) & 0xFFFFFFFF
    return h % bucket_count


def render_salt_buckets_visualizer(keys: list[str], highlight_key: str | None = None):
    """Hiển thị lưới trực quan 8 Salt Buckets với phân bổ thực tế."""
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


# =============================================================================
# DATA CLEANING ETL PIPELINE
# =============================================================================

def render_data_cleaning_pipeline_diagram():
    """Hiển thị quy trình ETL & làm sạch dữ liệu từ Archive vào Apache Phoenix."""
    html = """
    <div style="background: #FFFFFF; border: 1px solid var(--border-subtle); border-radius: 12px; padding: 20px; margin-bottom: 24px; box-shadow: 0 1px 3px rgba(0,0,0,0.03);">
        <div style="font-weight: 700; color: #0F172A; font-size: 1rem; margin-bottom: 16px;">
            QUY TRÌNH ETL & LÀM SẠCH DỮ LIỆU ARCHIVE (QUY ĐỔI VNĐ ĐỒNG BỘ)
        </div>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 14px;">
            
            <!-- Bước 1 -->
            <div style="background: #F8FAFC; border: 1px solid #CBD5E1; border-top: 3px solid #64748B; border-radius: 8px; padding: 14px;">
                <div style="font-size: 0.72rem; font-weight: 700; color: #64748B; text-transform: uppercase;">Giai đoạn 1</div>
                <div style="font-size: 0.92rem; font-weight: 600; color: #0F172A; margin: 4px 0 8px 0;">Nguồn dữ liệu thô</div>
                <ul style="margin: 0; padding-left: 18px; font-size: 0.8rem; color: #475569; line-height: 1.55;">
                    <li>File: <code>archive/data.csv</code> & Tiki E-Commerce</li>
                    <li>Dung lượng: <b>48.2 MB</b></li>
                    <li>Quy mô: <b>541,909</b> dòng thô</li>
                    <li>Nguồn: Kaggle E-Commerce & Tiki Việt Nam</li>
                </ul>
            </div>

            <!-- Bước 2 -->
            <div style="background: #FEF2F2; border: 1px solid #FECACA; border-top: 3px solid #DC2626; border-radius: 8px; padding: 14px;">
                <div style="font-size: 0.72rem; font-weight: 700; color: #DC2626; text-transform: uppercase;">Giai đoạn 2</div>
                <div style="font-size: 0.92rem; font-weight: 600; color: #991B1B; margin: 4px 0 8px 0;">Lọc rác & bất thường</div>
                <ul style="margin: 0; padding-left: 18px; font-size: 0.8rem; color: #7F1D1D; line-height: 1.55;">
                    <li>Loại đơn hoàn/hủy (Số lượng &le; 0)</li>
                    <li>Loại đơn giá &le; 0 (lỗi hạch toán)</li>
                    <li>Loại bỏ mô tả sản phẩm rỗng</li>
                    <li>Khử trùng lặp dòng tuyệt đối</li>
                </ul>
            </div>

            <!-- Bước 3 -->
            <div style="background: #EFF6FF; border: 1px solid #BFDBFE; border-top: 3px solid #2563EB; border-radius: 8px; padding: 14px;">
                <div style="font-size: 0.72rem; font-weight: 700; color: #1D4ED8; text-transform: uppercase;">Giai đoạn 3</div>
                <div style="font-size: 0.92rem; font-weight: 600; color: #1E40AF; margin: 4px 0 8px 0;">Chuẩn hóa Schema & VNĐ</div>
                <ul style="margin: 0; padding-left: 18px; font-size: 0.8rem; color: #1E3A8A; line-height: 1.55;">
                    <li>Quy đổi <b>1 USD ~ 26.000 VNĐ</b> thống nhất</li>
                    <li>Định dạng ISO <code>yyyy-MM-dd HH:mm:ss</code></li>
                    <li>Chuẩn hóa mã khách hàng dải KH_9xxxx</li>
                    <li>RowKey định dạng: <code>TX_0000001</code></li>
                </ul>
            </div>

            <!-- Bước 4 -->
            <div style="background: #ECFDF5; border: 1px solid #A7F3D0; border-top: 3px solid #059669; border-radius: 8px; padding: 14px;">
                <div style="font-size: 0.72rem; font-weight: 700; color: #047857; text-transform: uppercase;">Giai đoạn 4</div>
                <div style="font-size: 0.92rem; font-weight: 600; color: #065F46; margin: 4px 0 8px 0;">Bulk Load & Salt Buckets</div>
                <ul style="margin: 0; padding-left: 18px; font-size: 0.8rem; color: #064E3B; line-height: 1.55;">
                    <li>Nạp nhanh 30.000 dòng qua <code>psql.py</code></li>
                    <li>Phân tán song song trên <b>8 Salt Buckets</b></li>
                    <li>Đồng bộ <b>Secondary Index</b></li>
                    <li>Truy vấn OLAP trả về tức thì</li>
                </ul>
            </div>

        </div>
    </div>
    """
    render_html_block(html)


def render_metric_card(title: str, value: str, subtitle: str, icon: str = "table", border_color: str = "#2563EB"):
    """Vẽ 1 thẻ metric sạch có viền trên và biểu tượng SVG."""
    svg_icon = get_svg_icon(icon, size=15, color=border_color)
    render_html_block(
        f"""
        <div style="background: #FFFFFF; border: 1px solid var(--border-subtle); border-top: 3px solid {border_color}; border-radius: 9px; padding: 14px; box-shadow: 0 1px 3px rgba(0,0,0,0.02); min-height: 98px;">
            <div style="font-size: 0.76rem; font-weight: 600; color: #64748B; text-transform: uppercase; display: flex; align-items: center; gap: 6px;">
                <span>{svg_icon}</span> {title}
            </div>
            <div style="font-size: 1.35rem; font-weight: 700; color: #0F172A; margin: 6px 0 3px 0; font-family: var(--font-mono);">
                {value}
            </div>
            <div style="font-size: 0.74rem; color: #64748B;">
                {subtitle}
            </div>
        </div>
        """
    )


def render_cleaning_metrics_cards(summary: dict):
    """Hiển thị các thẻ chỉ số tóm tắt sau khi làm sạch dữ liệu."""
    total_raw = summary.get("total_raw", 541909)
    valid_records = summary.get("valid_records", 30000)
    dropped_records = summary.get("dropped_records", 17031)
    guest_customers = summary.get("guest_customers", 0)
    unique_countries = summary.get("unique_countries", 24)
    
    clean_pct = (valid_records / total_raw * 100) if total_raw > 0 else 0
    drop_pct = (dropped_records / total_raw * 100) if total_raw > 0 else 0

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        render_metric_card("Tổng dữ liệu thô", f"{total_raw:,}", "File archive/data.csv", icon="database", border_color="#64748B")
    with col2:
        render_metric_card("Dữ liệu nạp Phoenix", f"{valid_records:,}", f"Quy mô Big Data {valid_records:,}", icon="check-circle", border_color="#059669")
    with col3:
        render_metric_card("Bản ghi rác đã lọc", f"{dropped_records:,}", f"Tỷ lệ loại {drop_pct:.1f}%", icon="trash", border_color="#DC2626")
    with col4:
        render_metric_card("Mã khách hàng vãng lai", f"{guest_customers:,}", "100% định danh chuẩn", icon="users", border_color="#2563EB")
    with col5:
        render_metric_card("Thị trường / Vùng", f"{unique_countries}", "12 tỉnh VN + 12 QT", icon="globe", border_color="#D97706")
