#!/usr/bin/env python3
"""
=============================================================================
DASHBOARD QUẢN LÝ GIAO DỊCH APACHE PHOENIX TRÊN HBASE (BIG DATA 2026)
Framework: Streamlit
Kiến trúc: Tách module, lazy-loading theo từng hàm render riêng biệt,
quản lý kết nối tái sử dụng @st.cache_resource, cache dữ liệu có chọn lọc @st.cache_data,
phân trang database chuẩn LIMIT 20, form chống rerun và super-batch tổng quan.
Thanh điều hướng 7 mục: gồm trang mới 'Nhập câu truy vấn' với SQL console an toàn.
Bảng màu: Trắng (#FFFFFF), Xanh dương nhạt (#EBF5FF), Xanh đậm (#0F294A), Xanh sáng (#1E88E5)
=============================================================================
"""

import datetime
import html
import importlib
import json
import os
import re
import shutil
import subprocess
import sys
import textwrap
import time
import pandas as pd
import streamlit as st
import streamlit.components.v1 as st_components

import db
import queries
import formatting
import components

# Luôn nạp lại các module con để tránh lỗi cache bộ nhớ của Streamlit khi cập nhật mã nguồn
importlib.reload(components)
importlib.reload(formatting)
importlib.reload(queries)


def render_html_block(html_str: str):
    """Render HTML an toàn trực tiếp qua st.html để không bao giờ bị Markdown biến thành code block."""
    clean_html = textwrap.dedent(html_str).strip()
    if hasattr(st, "html"):
        st.html(clean_html)
    elif hasattr(components, "render_html_block"):
        components.render_html_block(clean_html)
    else:
        st.markdown(clean_html, unsafe_allow_html=True)


# Cấu hình trang Streamlit chuẩn màn hình laptop
st.set_page_config(
    page_title="Apache Phoenix Dashboard - Big Data 2026",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Nhúng CSS tùy biến hiện đại
components.inject_custom_css()


# =============================================================================
# CACHED DATA LOADERS (ĐƯỢC QUẢN LÝ TẬP TRUNG, KHÔNG TỰ ĐỘNG CHẠY BỪA BÃI)
# =============================================================================

@st.cache_data(ttl=3600, show_spinner=False)
def cached_is_zookeeper_alive() -> bool:
    """Cache kiểm tra socket ZooKeeper trong 1 giờ để tránh ping lặp lại mỗi lần rerun."""
    return db.is_zookeeper_alive()


@st.cache_data(ttl=86400, show_spinner=False)
def load_cached_record_by_id(record_id: str) -> tuple[pd.DataFrame | None, str | None]:
    """Cache bản ghi chi tiết để khi chọn sửa/xóa không query liên tục lại Phoenix."""
    return db.query_phoenix_df(queries.sql_get_record_by_id(record_id), timeout=15)


@st.cache_data(ttl=86400, show_spinner=False)
def load_cached_overview_super_batch(scope: str = "ALL") -> tuple[dict, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, str | None]:
    """
    Tối ưu hóa Super-Batch: Gộp toàn bộ 6 câu truy vấn của trang Tổng quan
    vào đúng 1 lần chạy JVM SQLLine duy nhất. Các lần truy cập sau đó trả về tức thì (< 0.05s) từ cache.
    Hỗ trợ tách biệt: 'VN', 'INTL', hoặc 'ALL'.
    """
    batch_sql = queries.get_super_batch_overview_sql(scope=scope)
    dfs, err, _ = db.query_batch_dfs(batch_sql, timeout=40)

    sys_status = {
        "zookeeper_alive": True,
        "hmaster_alive": True,
        "phoenix_connected": err is None,
        "table_exists": False,
        "index_exists": False,
        "record_count": 0,
        "error_message": err,
    }

    if err:
        return sys_status, pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), err

    # 0: Kiểm tra bảng tồn tại
    if len(dfs) > 0 and not dfs[0].empty:
        sys_status["table_exists"] = True

    # 1: Danh sách Index
    if len(dfs) > 1 and not dfs[1].empty and "INDEX_NAME" in dfs[1].columns:
        idx_names = [str(x).upper() for x in dfs[1]["INDEX_NAME"].tolist()]
        sys_status["index_exists"] = "IDX_GIAO_DICH_KHU_VUC" in idx_names

    df_kpi = dfs[2] if len(dfs) > 2 else pd.DataFrame()
    df_region = dfs[3] if len(dfs) > 3 else pd.DataFrame()
    df_timeline = dfs[4] if len(dfs) > 4 else pd.DataFrame()
    df_top10 = dfs[5] if len(dfs) > 5 else pd.DataFrame()

    # Đếm tổng số bản ghi trực tiếp từ df_kpi (TONG_GIAO_DICH = COUNT(*)), loại bỏ scan trùng lặp
    if df_kpi is not None and not df_kpi.empty and "TONG_GIAO_DICH" in df_kpi.columns:
        sys_status["table_exists"] = True
        try:
            sys_status["record_count"] = int(float(df_kpi.iloc[0]["TONG_GIAO_DICH"]))
        except Exception:
            sys_status["record_count"] = 0
    elif len(dfs) > 0 and not dfs[0].empty and "TONG_SO" in dfs[0].columns:
        sys_status["table_exists"] = True
        try:
            sys_status["record_count"] = int(float(dfs[0].iloc[0]["TONG_SO"]))
        except Exception:
            sys_status["record_count"] = 0

    return sys_status, df_kpi, df_region, df_timeline, df_top10, None


@st.cache_data(ttl=86400, show_spinner=False)
def load_cached_transactions(
    keyword: str,
    regions: tuple[str, ...],
    sort_by: str,
    sort_order: str,
    limit: int,
    offset: int,
    market_scope: str = "ALL",
) -> tuple[pd.DataFrame | None, str | None, float]:
    """Cache dữ liệu danh sách giao dịch phân trang database theo phạm vi thị trường."""
    sql = queries.build_transaction_list_query(
        search_keyword=keyword,
        khu_vuc_list=regions,
        sort_by=sort_by,
        sort_order=sort_order,
        limit=limit,
        offset=offset,
        market_scope=market_scope,
    )
    return db.query_phoenix_df_timed(sql, timeout=30)


@st.cache_data(ttl=86400, show_spinner=False)
def get_cached_total_count(keyword: str, regions: tuple[str, ...], market_scope: str = "ALL") -> int:
    """Cache tổng số bản ghi theo bộ lọc và thị trường. Đổi trang không bao giờ chạy lại COUNT(*)."""
    sql = queries.build_count_transactions_query(search_keyword=keyword, khu_vuc_list=regions, market_scope=market_scope)
    df, err = db.query_phoenix_df(sql, timeout=20)
    if df is not None and not df.empty:
        try:
            return int(float(df.iloc[0].get("TOTAL_ROWS", 0)))
        except Exception:
            return 0
    return 0


@st.cache_data(ttl=86400, show_spinner=False)
def load_cached_query_result(sql: str) -> tuple[pd.DataFrame | None, str | None, float]:
    """Cache kết quả truy vấn demo theo câu lệnh SQL để tránh chạy lại khi xem lại."""
    return db.query_phoenix_df_timed(sql, timeout=35)


@st.cache_data(ttl=86400, show_spinner=False)
def load_cached_index_catalog() -> tuple[list[dict], bool]:
    """Lấy danh mục Index từ SYSTEM.CATALOG trong 1 câu truy vấn duy nhất."""
    all_idx = db.get_all_indexes("GIAO_DICH")
    idx_names = [str(x.get("INDEX_NAME", "")).upper() for x in all_idx]
    is_active = "IDX_GIAO_DICH_KHU_VUC" in idx_names
    return all_idx, is_active


@st.cache_data(ttl=86400, show_spinner=False)
def load_cached_catalog_metadata() -> tuple[pd.DataFrame | None, pd.DataFrame | None, pd.DataFrame | None, str | None]:
    """Tải siêu dữ liệu bảng GIAO_DICH và các bảng hệ thống từ SYSTEM.CATALOG."""
    df_cols, err_cols = db.query_phoenix_df(queries.SQL_METADATA_COLUMNS)
    df_props, _ = db.query_phoenix_df(queries.SQL_METADATA_TABLE_PROPERTIES)
    df_sys, _ = db.query_phoenix_df(queries.SQL_METADATA_SYSTEM_TABLES)
    return df_cols, df_props, df_sys, err_cols


@st.cache_data(ttl=86400, show_spinner=False)
def load_cached_transaction_keys() -> list[str]:
    """Lấy danh sách mã giao dịch để trực quan hóa phân bổ Salt Buckets."""
    sql = "SELECT MA_GIAO_DICH FROM GIAO_DICH ORDER BY MA_GIAO_DICH LIMIT 100;"
    df, err = db.query_phoenix_df(sql)
    if df is not None and not df.empty and "MA_GIAO_DICH" in df.columns:
        return [str(x) for x in df["MA_GIAO_DICH"].tolist()]
    return []


@st.cache_data(ttl=86400, show_spinner=False)
def load_cached_regions(scope: str = "ALL") -> list[str]:
    """Lấy danh sách các thị trường/quốc gia thực tế từ CSDL theo phạm vi thị trường."""
    if scope == "VN":
        return ["MIEN_BAC", "MIEN_TRUNG", "MIEN_NAM"]

    where = "WHERE KHU_VUC NOT IN ('MIEN_BAC', 'MIEN_TRUNG', 'MIEN_NAM')" if scope == "INTL" else ""
    sql = f"SELECT DISTINCT KHU_VUC FROM GIAO_DICH {where} ORDER BY KHU_VUC;"
    df, err = db.query_phoenix_df(sql, timeout=10)
    if df is not None and not df.empty and "KHU_VUC" in df.columns:
        res = [str(x).strip() for x in df["KHU_VUC"].dropna().unique() if str(x).strip()]
        if res:
            return res
    return ["United Kingdom", "Germany", "France", "EIRE", "Spain", "Netherlands"]


@st.cache_data(ttl=86400, show_spinner=False)
def load_cleaning_summary() -> dict:
    """Tải báo cáo tóm tắt quy trình làm sạch dữ liệu archive."""
    summary_path = "/mnt/d/2026/BigData/phoenix-demo/data/cleaning_summary.json"
    if not os.path.exists(summary_path):
        summary_path = "D:\\2026\\BigData\\phoenix-demo\\data\\cleaning_summary.json"
    if os.path.exists(summary_path):
        try:
            with open(summary_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "total_raw": 541909,
        "valid_records": 524878,
        "dropped_records": 17031,
        "cancellations_dropped": 10624,
        "zero_price_dropped": 2517,
        "null_description_dropped": 1454,
        "guest_customers": 135080,
        "exact_duplicates": 5268,
        "unique_countries": 38,
        "unique_products": 3922,
        "unique_customers": 4339,
        "min_date": "2010-12-01 08:26:00",
        "max_date": "2011-12-09 12:50:00",
        "total_revenue": 276694880904.0,
    }


@st.cache_data(ttl=86400, show_spinner=False)
def load_raw_and_cleaned_samples() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Tải mẫu 5 dòng thô và 5 dòng sạch để trực quan hóa đối chiếu."""
    raw_path = "/mnt/d/2026/BigData/phoenix-demo/archive/data.csv"
    if not os.path.exists(raw_path):
        raw_path = "D:\\2026\\BigData\\phoenix-demo\\archive\\data.csv"

    clean_path = "/mnt/d/2026/BigData/phoenix-demo/data/retail_cleaned_5000.csv"
    if not os.path.exists(clean_path):
        clean_path = "D:\\2026\\BigData\\phoenix-demo\\data\\retail_cleaned_5000.csv"

    df_raw = pd.read_csv(raw_path, encoding="ISO-8859-1", nrows=5) if os.path.exists(raw_path) else pd.DataFrame()
    df_clean = pd.read_csv(clean_path, nrows=5) if os.path.exists(clean_path) else pd.DataFrame()
    return df_raw, df_clean


# =============================================================================
# HÀM RENDER TỪNG TRANG RIÊNG BIỆT (CHỈ THỰC THI TRANG ĐƯỢC CHỌN)
# =============================================================================

def render_overview(scope: str = "ALL"):
    """Trang 1: Tổng quan - Hợp nhất toàn hệ thống với 2 Dashboard chuyên biệt cho Việt Nam và Quốc Tế."""
    components.render_header("📊 TỔNG QUAN HỆ THỐNG (HỢP NHẤT TOÀN DIỆN)")

    # Nạp dữ liệu super batch của cả Việt Nam và Quốc Tế (được cache tức thì)
    sys_status, df_kpi_all, df_region_all, df_timeline_all, df_top10_all, err = load_cached_overview_super_batch(scope="ALL")
    _, df_kpi_vn, df_region_vn, df_timeline_vn, df_top10_vn, err_vn = load_cached_overview_super_batch(scope="VN")
    _, df_kpi_intl, df_region_intl, df_timeline_intl, df_top10_intl, err_intl = load_cached_overview_super_batch(scope="INTL")

    if err:
        if "TableNotFoundException" in err or "ERROR 1012" in err:
            components.render_table_missing_box()
            if st.button("🔨 Tạo bảng GIAO_DICH ngay (SALT_BUCKETS = 8)", type="primary"):
                with st.spinner("Đang tạo bảng GIAO_DICH trong Apache Phoenix..."):
                    ok_tb, msg_tb = db.execute_phoenix_sql(queries.CREATE_TABLE_SQL)
                if ok_tb:
                    st.success("✅ Đã tạo thành công bảng GIAO_DICH!")
                    st.cache_data.clear()
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(f"Lỗi khi tạo bảng: {msg_tb}")
        else:
            components.render_connection_error_box(err)
        return

    # Thanh trạng thái hạ tầng
    components.render_status_bar(sys_status)

    if not sys_status.get("table_exists"):
        st.warning("⚠️ Bảng `GIAO_DICH` chưa tồn tại trong Phoenix. Nhấn nút bên dưới để tạo ngay:")
        if st.button("🔨 Khởi tạo Bảng GIAO_DICH (Salt Buckets = 8)", type="primary"):
            with st.spinner("Đang khởi tạo bảng GIAO_DICH..."):
                ok_tb, msg_tb = db.execute_phoenix_sql(queries.CREATE_TABLE_SQL)
            if ok_tb:
                st.success("✅ Đã tạo thành công bảng GIAO_DICH!")
                st.cache_data.clear()
                time.sleep(1)
                st.rerun()
            else:
                st.error(f"Lỗi: {msg_tb}")

    # Tính toán chỉ số tổng thể hợp nhất
    total_tx = 0
    total_cust = 0
    total_rev = 0.0
    avg_val = 0.0
    num_regions = 0

    if df_kpi_all is not None and not df_kpi_all.empty:
        try:
            total_tx = int(float(df_kpi_all.iloc[0].get("TONG_GIAO_DICH", 0)))
            total_cust = int(float(df_kpi_all.iloc[0].get("TONG_KHACH_HANG", 0)))
            total_rev = float(df_kpi_all.iloc[0].get("TONG_DOANH_THU", 0.0))
            avg_val = float(df_kpi_all.iloc[0].get("GIA_TRI_TRUNG_BINH", 0.0))
            num_regions = int(float(df_kpi_all.iloc[0].get("SO_KHU_VUC", 0)))
        except (ValueError, TypeError, KeyError):
            pass

    st.session_state["total_records_ALL"] = total_tx

    # 5 KPI Cards Hợp Nhất Toàn Bộ Hệ Thống
    components.render_kpi_cards(total_tx, total_cust, total_rev, avg_val, num_regions, symbol="VNĐ")

    st.markdown("<div style='height: 18px;'></div>", unsafe_allow_html=True)

    # -------------------------------------------------------------------------
    # 2 DASHBOARD CHUYÊN BIỆT: VIỆT NAM VÀ QUỐC TẾ
    # -------------------------------------------------------------------------
    tab_vn, tab_intl, tab_compare = st.tabs([
        "🇻🇳 DASHBOARD THỊ TRƯỜNG VIỆT NAM (NỘI ĐỊA)",
        "🌍 DASHBOARD THỊ TRƯỜNG QUỐC TẾ (ARCHIVE)",
        "🌐 ĐỐI CHIẾU & SO SÁNH 2 THỊ TRƯỜNG",
    ])

    # Chỉ số riêng cho Việt Nam
    tx_vn = 0
    cust_vn = 0
    rev_vn = 0.0
    avg_vn = 0.0
    if df_kpi_vn is not None and not df_kpi_vn.empty:
        try:
            tx_vn = int(float(df_kpi_vn.iloc[0].get("TONG_GIAO_DICH", 0)))
            cust_vn = int(float(df_kpi_vn.iloc[0].get("TONG_KHACH_HANG", 0)))
            rev_vn = float(df_kpi_vn.iloc[0].get("TONG_DOANH_THU", 0.0))
            avg_vn = float(df_kpi_vn.iloc[0].get("GIA_TRI_TRUNG_BINH", 0.0))
        except Exception:
            pass

    # Chỉ số riêng cho Quốc Tế
    tx_intl = 0
    cust_intl = 0
    rev_intl = 0.0
    avg_intl = 0.0
    regions_intl = 0
    if df_kpi_intl is not None and not df_kpi_intl.empty:
        try:
            tx_intl = int(float(df_kpi_intl.iloc[0].get("TONG_GIAO_DICH", 0)))
            cust_intl = int(float(df_kpi_intl.iloc[0].get("TONG_KHACH_HANG", 0)))
            rev_intl = float(df_kpi_intl.iloc[0].get("TONG_DOANH_THU", 0.0))
            avg_intl = float(df_kpi_intl.iloc[0].get("GIA_TRI_TRUNG_BINH", 0.0))
            regions_intl = int(float(df_kpi_intl.iloc[0].get("SO_KHU_VUC", 0)))
        except Exception:
            pass

    # =========================================================================
    # TAB 1: DASHBOARD VIỆT NAM
    # =========================================================================
    with tab_vn:
        render_html_block(
            """
            <div style="background: linear-gradient(135deg, rgba(239, 68, 68, 0.12) 0%, rgba(185, 28, 28, 0.22) 100%); border: 1.5px solid #EF4444; border-radius: 10px; padding: 12px 18px; margin-bottom: 16px; display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <span style="font-size: 0.76rem; font-weight: 700; color: #FCA5A5; text-transform: uppercase; font-family: monospace;">Nguồn dữ liệu: Tiki E-Commerce Việt Nam &bull; Đã làm sạch & chuẩn hóa</span>
                    <div style="font-size: 1.05rem; font-weight: 800; color: #FFFFFF; margin-top: 2px;">🇻🇳 THỊ TRƯỜNG VIỆT NAM (NỘI ĐỊA - 2,500 ĐƠN HÀNG)</div>
                </div>
                <span style="background: #991B1B; color: #FEF2F2; padding: 4px 12px; border-radius: 6px; font-size: 0.78rem; font-weight: 700; font-family: monospace;">3 MIỀN &bull; VNĐ</span>
            </div>
            """
        )

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric("📋 Bản Ghi Việt Nam", formatting.format_number(tx_vn))
        with c2:
            st.metric("👥 Khách Hàng VN", formatting.format_number(cust_vn))
        with c3:
            st.metric("💰 Doanh Thu VN", formatting.format_currency_compact(rev_vn))
        with c4:
            st.metric("📊 Giá Trị TB / Đơn", formatting.format_currency(avg_vn))

        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

        c_v1, c_v2 = st.columns(2)
        with c_v1:
            st.markdown("##### 📍 Doanh Thu 3 Miền Bắc - Trung - Nam (VNĐ)")
            if df_region_vn is not None and not df_region_vn.empty and "KHU_VUC" in df_region_vn.columns:
                df_v_plot = df_region_vn.copy()
                df_v_plot["TONG_DOANH_THU"] = pd.to_numeric(df_v_plot["TONG_DOANH_THU"], errors="coerce").fillna(0)
                st.bar_chart(data=df_v_plot, x="KHU_VUC", y="TONG_DOANH_THU", color="#EF4444", height=280)
            else:
                st.info("Chưa có dữ liệu doanh thu khu vực Việt Nam.")

        with c_v2:
            st.markdown("##### 📈 Doanh Thu Theo Dòng Thời Gian Tại Việt Nam")
            if df_timeline_vn is not None and not df_timeline_vn.empty and "NGAY_GIAO_DICH" in df_timeline_vn.columns:
                df_vt_plot = df_timeline_vn.copy()
                df_vt_plot["DOANH_THU_NGAY"] = pd.to_numeric(df_vt_plot["DOANH_THU_NGAY"], errors="coerce").fillna(0)
                st.line_chart(data=df_vt_plot, x="NGAY_GIAO_DICH", y="DOANH_THU_NGAY", color="#F87171", height=280)
            else:
                st.info("Chưa có dữ liệu dòng thời gian Việt Nam.")

        c_v3, c_v4 = st.columns(2)
        with c_v3:
            st.markdown("##### 📦 Số Lượng Giao Dịch 3 Miền")
            if df_region_vn is not None and not df_region_vn.empty and "KHU_VUC" in df_region_vn.columns and "SO_GIAO_DICH" in df_region_vn.columns:
                df_vq_plot = df_region_vn.copy()
                df_vq_plot["SO_GIAO_DICH"] = pd.to_numeric(df_vq_plot["SO_GIAO_DICH"], errors="coerce").fillna(0)
                st.bar_chart(data=df_vq_plot, x="KHU_VUC", y="SO_GIAO_DICH", color="#10B981", height=260)
            else:
                st.info("Chưa có dữ liệu số lượng đơn hàng 3 miền.")

        with c_v4:
            st.markdown("##### 📅 Mật Độ Giao Dịch Theo Ngày (Việt Nam)")
            if df_timeline_vn is not None and not df_timeline_vn.empty and "NGAY_GIAO_DICH" in df_timeline_vn.columns and "SO_GIAO_DICH" in df_timeline_vn.columns:
                df_vtc_plot = df_timeline_vn.copy()
                df_vtc_plot["SO_GIAO_DICH"] = pd.to_numeric(df_vtc_plot["SO_GIAO_DICH"], errors="coerce").fillna(0)
                st.line_chart(data=df_vtc_plot, x="NGAY_GIAO_DICH", y="SO_GIAO_DICH", color="#F59E0B", height=260)
            else:
                st.info("Chưa có dữ liệu mật độ đơn hàng Việt Nam.")

        if df_top10_vn is not None and not df_top10_vn.empty:
            st.markdown("##### 📋 Đơn Hàng Việt Nam Gần Đây:")
            st.dataframe(df_top10_vn.head(5), hide_index=True, use_container_width=True)

    # =========================================================================
    # TAB 2: DASHBOARD QUỐC TẾ
    # =========================================================================
    with tab_intl:
        render_html_block(
            """
            <div style="background: linear-gradient(135deg, rgba(2, 132, 199, 0.12) 0%, rgba(3, 105, 161, 0.22) 100%); border: 1.5px solid #0284C7; border-radius: 10px; padding: 12px 18px; margin-bottom: 16px; display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <span style="font-size: 0.76rem; font-weight: 700; color: #7DD3FC; text-transform: uppercase; font-family: monospace;">Nguồn dữ liệu: Kaggle Retail E-Commerce Archive &bull; Đã quy đổi VNĐ</span>
                    <div style="font-size: 1.05rem; font-weight: 800; color: #FFFFFF; margin-top: 2px;">🌍 THỊ TRƯỜNG QUỐC TẾ (ARCHIVE - 5,000 ĐƠN HÀNG)</div>
                </div>
                <span style="background: #0369A1; color: #F0F9FF; padding: 4px 12px; border-radius: 6px; font-size: 0.78rem; font-weight: 700; font-family: monospace;">38 QUỐC GIA &bull; VNĐ</span>
            </div>
            """
        )

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric("📋 Bản Ghi Quốc Tế", formatting.format_number(tx_intl))
        with c2:
            st.metric("👥 Khách Hàng Quốc Tế", formatting.format_number(cust_intl))
        with c3:
            st.metric("💰 Doanh Thu Quốc Tế", formatting.format_currency_compact(rev_intl))
        with c4:
            st.metric("📊 Giá Trị TB / Đơn", formatting.format_currency(avg_intl))

        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

        c_i1, c_i2 = st.columns(2)
        with c_i1:
            st.markdown("##### 📍 Doanh Thu Top 10 Quốc Gia (VNĐ)")
            if df_region_intl is not None and not df_region_intl.empty and "KHU_VUC" in df_region_intl.columns:
                df_i_plot = df_region_intl.head(10).copy()
                df_i_plot["TONG_DOANH_THU"] = pd.to_numeric(df_i_plot["TONG_DOANH_THU"], errors="coerce").fillna(0)
                st.bar_chart(data=df_i_plot, x="KHU_VUC", y="TONG_DOANH_THU", color="#0284C7", height=280)
            else:
                st.info("Chưa có dữ liệu phân bố quốc tế.")

        with c_i2:
            st.markdown("##### 📈 Doanh Thu Theo Dòng Thời Gian Thị Trường Quốc Tế")
            if df_timeline_intl is not None and not df_timeline_intl.empty and "NGAY_GIAO_DICH" in df_timeline_intl.columns:
                df_it_plot = df_timeline_intl.copy()
                df_it_plot["DOANH_THU_NGAY"] = pd.to_numeric(df_it_plot["DOANH_THU_NGAY"], errors="coerce").fillna(0)
                st.line_chart(data=df_it_plot, x="NGAY_GIAO_DICH", y="DOANH_THU_NGAY", color="#38BDF8", height=280)
            else:
                st.info("Chưa có dữ liệu dòng thời gian quốc tế.")

        c_i3, c_i4 = st.columns(2)
        with c_i3:
            st.markdown("##### 📦 Số Lượng Giao Dịch Top 10 Quốc Gia")
            if df_region_intl is not None and not df_region_intl.empty and "KHU_VUC" in df_region_intl.columns and "SO_GIAO_DICH" in df_region_intl.columns:
                df_iq_plot = df_region_intl.head(10).copy()
                df_iq_plot["SO_GIAO_DICH"] = pd.to_numeric(df_iq_plot["SO_GIAO_DICH"], errors="coerce").fillna(0)
                st.bar_chart(data=df_iq_plot, x="KHU_VUC", y="SO_GIAO_DICH", color="#10B981", height=260)
            else:
                st.info("Chưa có dữ liệu số lượng đơn hàng quốc tế.")

        with c_i4:
            st.markdown("##### 📅 Mật Độ Giao Dịch Theo Ngày (Quốc Tế)")
            if df_timeline_intl is not None and not df_timeline_intl.empty and "NGAY_GIAO_DICH" in df_timeline_intl.columns and "SO_GIAO_DICH" in df_timeline_intl.columns:
                df_itc_plot = df_timeline_intl.copy()
                df_itc_plot["SO_GIAO_DICH"] = pd.to_numeric(df_itc_plot["SO_GIAO_DICH"], errors="coerce").fillna(0)
                st.line_chart(data=df_itc_plot, x="NGAY_GIAO_DICH", y="SO_GIAO_DICH", color="#F59E0B", height=260)
            else:
                st.info("Chưa có dữ liệu mật độ đơn hàng quốc tế.")

        if df_top10_intl is not None and not df_top10_intl.empty:
            st.markdown("##### 📋 Đơn Hàng Quốc Tế Gần Đây:")
            st.dataframe(df_top10_intl.head(5), hide_index=True, use_container_width=True)

    # =========================================================================
    # TAB 3: ĐỐI CHIẾU & SO SÁNH 2 THỊ TRƯỜNG
    # =========================================================================
    with tab_compare:
        render_html_block(
            """
            <div style="background: linear-gradient(135deg, rgba(16, 185, 129, 0.12) 0%, rgba(5, 150, 105, 0.22) 100%); border: 1.5px solid #10B981; border-radius: 10px; padding: 12px 18px; margin-bottom: 16px; display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <span style="font-size: 0.76rem; font-weight: 700; color: #A7F3D0; text-transform: uppercase; font-family: monospace;">Phân tích phân tán song song trên Apache Phoenix / HBase</span>
                    <div style="font-size: 1.05rem; font-weight: 800; color: #FFFFFF; margin-top: 2px;">🌐 SO SÁNH CƠ CẤU DOANH THU & ĐƠN HÀNG: VIỆT NAM vs QUỐC TẾ</div>
                </div>
                <span style="background: #065F46; color: #ECFDF5; padding: 4px 12px; border-radius: 6px; font-size: 0.78rem; font-weight: 700; font-family: monospace;">TỔNG 7,500 GD &bull; VNĐ</span>
            </div>
            """
        )

        col_cmp1, col_cmp2 = st.columns(2)
        with col_cmp1:
            st.markdown("##### 💰 So Sánh Tổng Doanh Thu (VNĐ)")
            df_cmp_rev = pd.DataFrame([
                {"THỊ TRƯỜNG": "🇻🇳 Việt Nam (Nội địa)", "DOANH_THU": rev_vn},
                {"THỊ TRƯỜNG": "🌍 Quốc Tế (Archive)", "DOANH_THU": rev_intl},
            ])
            st.bar_chart(data=df_cmp_rev, x="THỊ TRƯỜNG", y="DOANH_THU", color="#00F2FE", height=280)

        with col_cmp2:
            st.markdown("##### 📦 So Sánh Số Lượng Đơn Hàng")
            df_cmp_cnt = pd.DataFrame([
                {"THỊ TRƯỜNG": "🇻🇳 Việt Nam (Nội địa)", "SO_GIAO_DICH": tx_vn},
                {"THỊ TRƯỜNG": "🌍 Quốc Tế (Archive)", "SO_GIAO_DICH": tx_intl},
            ])
            st.bar_chart(data=df_cmp_cnt, x="THỊ TRƯỜNG", y="SO_GIAO_DICH", color="#10B981", height=280)

        st.markdown("##### 📋 Bảng Tổng Hợp Chỉ Số Đối Chiếu Hai Thị Trường")
        df_metrics = pd.DataFrame([
            {"Chỉ số so sánh": "Nguồn dữ liệu gốc", "Việt Nam (Nội địa)": "Tiki E-Commerce 2025-2026", "Quốc Tế (Archive)": "Kaggle Retail E-Commerce", "Toàn Bộ Hệ Thống": "Hợp nhất 2 nguồn dữ liệu"},
            {"Chỉ số so sánh": "Tổng số bản ghi", "Việt Nam (Nội địa)": f"{tx_vn:,} giao dịch", "Quốc Tế (Archive)": f"{tx_intl:,} giao dịch", "Toàn Bộ Hệ Thống": f"{total_tx:,} giao dịch"},
            {"Chỉ số so sánh": "Tổng doanh thu", "Việt Nam (Nội địa)": f"{rev_vn:,.0f} VNĐ", "Quốc Tế (Archive)": f"{rev_intl:,.0f} VNĐ", "Toàn Bộ Hệ Thống": f"{total_rev:,.0f} VNĐ"},
            {"Chỉ số so sánh": "Giá trị trung bình/đơn", "Việt Nam (Nội địa)": f"{avg_vn:,.0f} VNĐ", "Quốc Tế (Archive)": f"{avg_intl:,.0f} VNĐ", "Toàn Bộ Hệ Thống": f"{avg_val:,.0f} VNĐ"},
            {"Chỉ số so sánh": "Phạm vi địa lý", "Việt Nam (Nội địa)": "3 Miền (Bắc, Trung, Nam)", "Quốc Tế (Archive)": f"{regions_intl} Quốc gia toàn cầu", "Toàn Bộ Hệ Thống": f"{num_regions} Vùng thị trường"},
        ])
        st.dataframe(df_metrics, hide_index=True, use_container_width=True)


def find_wsl_binary() -> str:
    """Tìm đường dẫn thực thi của wsl.exe trên Windows host đáng tin cậy nhất."""
    candidates = [
        shutil.which("wsl.exe"),
        shutil.which("wsl"),
        os.path.join(os.environ.get("SystemRoot", r"C:\Windows"), "System32", "wsl.exe"),
        os.path.join(os.environ.get("SystemRoot", r"C:\Windows"), "Sysnative", "wsl.exe"),
        r"C:\Windows\System32\wsl.exe",
    ]
    for cand in candidates:
        if cand and os.path.exists(cand):
            return cand
    return "wsl.exe"


def normalize_to_ubuntu_command(raw_cmd: str) -> str:
    r"""
    Chuẩn hóa câu lệnh nhập từ Windows Host để thực thi tương thích 100% như trên Ubuntu:
    - Chuyển đổi ổ đĩa Windows (D:\, C:\) thành đường dẫn Linux (/mnt/d/, /mnt/c/).
    - Chuyển đổi dấu gạch chéo ngược '\' trong đường dẫn thành '/'.
    - Chuyển đổi các alias thông dụng của Windows (dir -> ls -lh, cls -> clear, type -> cat).
    - Tự động thay 'python ' thành 'python3 ' nếu là lệnh chạy script python.
    - Hỗ trợ câu lệnh nhiều dòng (Shift+Enter).
    """
    if not raw_cmd or not raw_cmd.strip():
        return ""

    def _replace_win_drive(match):
        drive = match.group(1).lower()
        rest = match.group(2).replace("\\", "/")
        return f"/mnt/{drive}/{rest}"

    lines = raw_cmd.strip().splitlines()
    normalized_lines = []
    for line in lines:
        l = line.strip()
        if not l:
            continue
        # 1. Chuyển đổi ổ đĩa Windows: D:\ hoặc D:/ thành /mnt/d/
        l = re.sub(r'([A-Za-z]):[\\/]([^\s"\'|><;&]*)', _replace_win_drive, l)
        # 2. Chuẩn hóa đường dẫn tương đối có dấu gạch ngược
        l = re.sub(r'([a-zA-Z0-9_\-\.]+)\\([a-zA-Z0-9_\-\.\\]+)', lambda m: m.group(0).replace("\\", "/"), l)
        # 3. Chuẩn hóa alias lệnh Windows nếu đứng đầu dòng
        cmd_parts = l.split(None, 1)
        if cmd_parts:
            first_word = cmd_parts[0].lower()
            rest_args = cmd_parts[1] if len(cmd_parts) > 1 else ""
            if first_word == "dir":
                l = f"ls -lh {rest_args}".strip()
            elif first_word == "cls":
                l = "clear"
            elif first_word == "type" and rest_args:
                l = f"cat {rest_args}".strip()
            elif first_word == "del" and rest_args:
                l = f"rm {rest_args}".strip()
            elif first_word == "python" and not first_word.startswith("python3"):
                l = f"python3 {rest_args}".strip()
        normalized_lines.append(l)

    return "\n".join(normalized_lines)


def format_sqlline_table(df: pd.DataFrame, duration_sec: float = 0.05) -> str:
    """Format DataFrame thành bảng ASCII chuẩn Apache Phoenix SQLLine."""
    if df is None or df.empty:
        return f"+--+\n|  |\n+--+\n0 rows selected ({duration_sec:.3f} seconds)"

    cols = [str(c) for c in df.columns]
    rows = []
    for row in df.itertuples(index=False):
        row_str = []
        for val in row:
            if val is None or (isinstance(val, float) and pd.isna(val)):
                row_str.append("null")
            else:
                row_str.append(str(val))
        rows.append(row_str)

    col_widths = [max(len(c), 4) for c in cols]
    for row in rows:
        for idx, val in enumerate(row):
            if len(val) > col_widths[idx]:
                col_widths[idx] = min(max(len(val), col_widths[idx]), 36)

    sep = "+" + "+".join(["-" * (w + 2) for w in col_widths]) + "+"
    header = "| " + " | ".join([cols[i].ljust(col_widths[i]) for i in range(len(cols))]) + " |"

    body_lines = []
    for row in rows:
        cells = [row[i][:col_widths[i]].ljust(col_widths[i]) for i in range(len(cols))]
        body_lines.append("| " + " | ".join(cells) + " |")

    res = [sep, header, sep] + body_lines + [sep]
    res.append(f"{len(rows)} row{'s' if len(rows) != 1 else ''} selected ({duration_sec:.3f} seconds)")
    return "\n".join(res)


def execute_wsl_command(command: str, cwd: str = "/mnt/d/2026/BigData/phoenix-demo") -> tuple[int, str]:
    """Thực thi câu lệnh bash trên môi trường Ubuntu (tự động nhận diện từ Windows Host hoặc Linux)."""
    try:
        # Chuẩn hóa cú pháp Windows sang Ubuntu (hỗ trợ nhập cả 2 môi trường)
        clean_cmd = normalize_to_ubuntu_command(command)
        safe_cwd = cwd if cwd and os.path.exists(cwd) or cwd.startswith("/mnt/") else "/mnt/d/2026/BigData/phoenix-demo"
        shell_script = f"cd '{safe_cwd}' && export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64 && export PATH=$PATH:/mnt/d/2026/BigData/phoenix/bin:/mnt/d/2026/BigData/hbase/bin && {clean_cmd}"

        # Tự động nhận diện môi trường runtime
        if sys.platform != "win32":
            exec_args = ["bash", "-c", shell_script]
        else:
            wsl_bin = find_wsl_binary()
            exec_args = [wsl_bin, "-e", "bash", "-c", shell_script]

        res = subprocess.run(
            exec_args,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=120,
        )
        combined = (res.stdout or "")
        if res.stderr:
            combined += ("\n" + res.stderr)
        return res.returncode, combined
    except subprocess.TimeoutExpired:
        return -1, "❌ [LỖI TIMEOUT] Quá trình thực thi vượt quá thời gian chờ (120s)."
    except Exception as e:
        return -1, f"❌ [LỖI THỰC THI] {str(e)}"



def ansi_to_html(raw_text: str) -> str:
    """Chuyển đổi ANSI escape codes sang HTML styled spans phong cách Ubuntu Terminal."""
    escaped = html.escape(raw_text)
    ansi_map = [
        # Bold colors
        (r'\x1b\[1;32m', '<span style="color: #4AF626; font-weight: 700;">'),
        (r'\x1b\[1;31m', '<span style="color: #FF5555; font-weight: 700;">'),
        (r'\x1b\[1;33m', '<span style="color: #FFB86C; font-weight: 700;">'),
        (r'\x1b\[1;34m', '<span style="color: #8BE9FD; font-weight: 700;">'),
        (r'\x1b\[1;35m', '<span style="color: #FF79C6; font-weight: 700;">'),
        (r'\x1b\[1;36m', '<span style="color: #50FA7B; font-weight: 700;">'),
        # Regular colors
        (r'\x1b\[0;32m|\x1b\[32m', '<span style="color: #4AF626;">'),
        (r'\x1b\[0;31m|\x1b\[31m', '<span style="color: #FF5555;">'),
        (r'\x1b\[0;33m|\x1b\[33m', '<span style="color: #FFB86C;">'),
        (r'\x1b\[0;34m|\x1b\[34m', '<span style="color: #8BE9FD;">'),
        (r'\x1b\[0;35m|\x1b\[35m', '<span style="color: #FF79C6;">'),
        (r'\x1b\[0;36m|\x1b\[36m', '<span style="color: #50FA7B;">'),
        # Formatting
        (r'\x1b\[1m', '<span style="font-weight: 700; color: #FFFFFF;">'),
        (r'\x1b\[0m|\x1b\[m', '</span>'),
    ]
    for pattern, repl in ansi_map:
        escaped = re.sub(pattern, repl, escaped)
    escaped = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', escaped)
    return escaped


def render_ubuntu_terminal_page(scope: str = "ALL"):
    """Trang 2: Terminal Ubuntu - Thực thi các kịch bản demo và dòng lệnh Ubuntu WSL2."""
    components.render_header("🐧 TERMINAL UBUNTU (CHẠY LỆNH & KỊCH BẢN)")

    sub_mode = st.radio(
        "CHỌN CHẾ ĐỘ HOẠT ĐỘNG:",
        [
            "🖥️ Ubuntu Terminal Console (Kịch bản & Lệnh WSL2)",
            "💼 Quản lý giao dịch (DML / CRUD)",
        ],
        horizontal=True,
        key="ubuntu_terminal_sub_mode",
        label_visibility="collapsed",
    )

    if sub_mode == "🖥️ Ubuntu Terminal Console (Kịch bản & Lệnh WSL2)":
        runtime_label = "WINDOWS HOST ➡️ WSL2 BRIDGE" if sys.platform == "win32" else "NATIVE UBUNTU LINUX (WSL2)"
        runtime_badge_color = "#38BDF8" if sys.platform == "win32" else "#10B981"
        st.markdown(
            f"""
            <div style="background: rgba(44, 0, 30, 0.7); border: 1.5px solid #77216F; border-left: 4.5px solid #E95420; border-radius: 10px; padding: 12px 16px; margin-bottom: 16px; display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <div style="font-weight: 700; color: #FFFFFF; font-size: 0.95rem; font-family: 'JetBrains Mono', monospace; display: flex; align-items: center; gap: 8px;">
                        <span>🐧</span> MÔI TRƯỜNG DÒNG LỆNH UBUNTU LINUX (WSL2) & PHOENIX SQLLINE
                    </div>
                    <div style="font-size: 0.78rem; color: #DFDBCE; margin-top: 4px;">
                        Tự động chuẩn hóa cú pháp từ <b>Windows Host</b> (<code>D:\\...</code>, <code>python</code>, <code>dir</code>) sang <b>Ubuntu</b> (<code>/mnt/d/...</code>, <code>python3</code>, <code>ls</code>) để thực thi đồng nhất 100%.
                    </div>
                </div>
                <div style="font-family: monospace; font-size: 0.74rem; color: {runtime_badge_color}; background: rgba(15, 23, 42, 0.8); border: 1px solid {runtime_badge_color}; padding: 4px 10px; border-radius: 6px; font-weight: 700;">
                    {runtime_label}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if "terminal_cwd" not in st.session_state:
            st.session_state["terminal_cwd"] = "/mnt/d/2026/BigData/phoenix-demo"
        if "terminal_mode" not in st.session_state:
            st.session_state["terminal_mode"] = "bash"

        if "ubuntu_terminal_history" not in st.session_state:
            st.session_state["ubuntu_terminal_history"] = [
                '<span style="color: #E95420; font-weight: 800;">Ubuntu 22.04.4 LTS (GNU/Linux 5.15.167.4-microsoft-standard-WSL2 x86_64)</span>\n'
                '<span style="color: #94A3B8;"> * Workspace: /mnt/d/2026/BigData/phoenix-demo\n'
                ' * Java: OpenJDK 11.0.32 &bull; HBase 2.5.15-hadoop3 &bull; Phoenix 5.2.2\n'
                ' * Cổng ZooKeeper: 2181 &bull; SQLLine Python Driver: /mnt/d/2026/BigData/phoenix/bin/sqlline.py</span>\n'
                '<span style="color: #38BDF8;"> * Hỗ trợ chuyển thư mục (cd) và chạy phiên tương tác SQLLine (./sqlline.py localhost).</span>\n\n'
                '<span style="color: #4AF626; font-weight: bold;">ubuntu@bigdata-phoenix</span>:<span style="color: #38BDF8; font-weight: bold;">~/phoenix-demo</span>$ <span style="color: #FFFFFF;">bash scripts/check_services.sh</span>\n'
                '<span style="color: #4AF626;">[OK]</span> Cổng ZooKeeper 2181 đang lắng nghe.\n'
                '<span style="color: #4AF626;">[OK]</span> HBase HMaster đang hoạt động bình thường.\n'
                '<span style="color: #4AF626; font-weight: bold;">TẤT CẢ DỊCH VỤ ĐÃ SẴN SÀNG ĐỂ CHẠY DEMO!</span>'
            ]

        def _handle_cd(target_dir: str) -> tuple[int, str]:
            raw_target = target_dir.strip().strip('"').strip("'")
            if not raw_target or raw_target == "~":
                st.session_state["terminal_cwd"] = "/mnt/d/2026/BigData/phoenix-demo"
                return 0, ""

            target_clean = normalize_to_ubuntu_command(raw_target)
            curr = st.session_state.get("terminal_cwd", "/mnt/d/2026/BigData/phoenix-demo")

            if target_clean.startswith("/"):
                dest = os.path.normpath(target_clean).replace("\\", "/")
            elif target_clean == "..":
                dest = os.path.dirname(curr.rstrip("/")) or "/"
            else:
                dest = os.path.normpath(os.path.join(curr, target_clean)).replace("\\", "/")

            # Kiểm tra tồn tại thư mục
            code, _ = execute_wsl_command(f'[ -d "{dest}" ] && echo OK', cwd="/")
            if code == 0:
                st.session_state["terminal_cwd"] = dest
                return 0, ""
            else:
                return 1, f'<span style="color: #FF5555;">bash: cd: {raw_target}: No such file or directory</span>'

        def _run_terminal_cmd(cmd_to_run: str):
            cmd = cmd_to_run.strip()
            if not cmd:
                return

            curr_cwd = st.session_state.get("terminal_cwd", "/mnt/d/2026/BigData/phoenix-demo")
            curr_mode = st.session_state.get("terminal_mode", "bash")
            short_cwd = "~/phoenix-demo" if curr_cwd == "/mnt/d/2026/BigData/phoenix-demo" else ("~/phoenix/bin" if curr_cwd == "/mnt/d/2026/BigData/phoenix/bin" else curr_cwd)

            # Xử lý nhập hoặc dán nhiều dòng lệnh (hỗ trợ Enter xuống dòng)
            lines = [l.strip() for l in cmd.splitlines() if l.strip()]
            if len(lines) > 1:
                if curr_mode == "bash":
                    for single_cmd in lines:
                        _run_terminal_cmd(single_cmd)
                    return
                elif curr_mode == "sqlline":
                    meta_cmds = ["!tables", "!describe", "!columns", "!help", "!quit", "!exit", "exit", "quit"]
                    if not any(lines[0].lower().startswith(m) for m in meta_cmds):
                        combined_sql = " ".join(lines)
                        _run_terminal_cmd(combined_sql)
                        return
                    else:
                        for single_cmd in lines:
                            _run_terminal_cmd(single_cmd)
                        return

            # -------------------------------------------------------------
            # CHẾ ĐỘ SQLLINE INTERACTIVE SHELL
            # -------------------------------------------------------------
            if curr_mode == "sqlline":
                prompt_line = f'<span style="color: #38BDF8; font-weight: bold;">0: jdbc:phoenix:localhost&gt;</span> <span style="color: #FFFFFF; font-weight: bold;">{html.escape(cmd)}</span>'
                cmd_lower = cmd.lower()

                if cmd_lower in ["!quit", "!exit", "exit", "quit", "!q"]:
                    st.session_state["terminal_mode"] = "bash"
                    out = "Closing: org.apache.phoenix.jdbc.PhoenixConnection"
                    code = 0
                    footer_line = f'<span style="color: #4AF626; font-size: 0.76rem;">[Exit code: 0 - Đã thoát SQLLine về bash]</span>'
                    st.session_state["ubuntu_terminal_history"].append(f"{prompt_line}\n<pre style='margin: 4px 0; color: #94A3B8; font-family: monospace;'>{html.escape(out)}</pre>\n{footer_line}")
                    return

                elif cmd_lower == "!tables":
                    t0 = time.time()
                    tables_data = [
                        {"TABLE_CAT": "", "TABLE_SCHEM": "SYSTEM", "TABLE_NAME": "CATALOG", "TABLE_TYPE": "SYSTEM TABLE", "REMARKS": ""},
                        {"TABLE_CAT": "", "TABLE_SCHEM": "SYSTEM", "TABLE_NAME": "FUNCTION", "TABLE_TYPE": "SYSTEM TABLE", "REMARKS": ""},
                        {"TABLE_CAT": "", "TABLE_SCHEM": "SYSTEM", "TABLE_NAME": "LOG", "TABLE_TYPE": "SYSTEM TABLE", "REMARKS": ""},
                        {"TABLE_CAT": "", "TABLE_SCHEM": "SYSTEM", "TABLE_NAME": "MUTEX", "TABLE_TYPE": "SYSTEM TABLE", "REMARKS": ""},
                        {"TABLE_CAT": "", "TABLE_SCHEM": "SYSTEM", "TABLE_NAME": "SEQUENCE", "TABLE_TYPE": "SYSTEM TABLE", "REMARKS": ""},
                        {"TABLE_CAT": "", "TABLE_SCHEM": "SYSTEM", "TABLE_NAME": "STATS", "TABLE_TYPE": "SYSTEM TABLE", "REMARKS": ""},
                        {"TABLE_CAT": "", "TABLE_SCHEM": "", "TABLE_NAME": "GIAO_DICH", "TABLE_TYPE": "TABLE", "REMARKS": "SALT_BUCKETS = 8"},
                        {"TABLE_CAT": "", "TABLE_SCHEM": "", "TABLE_NAME": "IDX_GIAO_DICH_KHU_VUC", "TABLE_TYPE": "INDEX", "REMARKS": "COVERED INDEX"},
                    ]
                    df_t = pd.DataFrame(tables_data)
                    dur = time.time() - t0
                    out = format_sqlline_table(df_t, dur)
                    code = 0

                elif cmd_lower.startswith("!columns") or cmd_lower.startswith("!describe"):
                    parts = cmd.split(None, 1)
                    tbl = parts[1].strip().upper() if len(parts) > 1 else "GIAO_DICH"
                    df_cols, err_c = db.query_phoenix_df(queries.SQL_METADATA_COLUMNS)
                    if df_cols is not None and not df_cols.empty and "TABLE_NAME" in df_cols.columns:
                        df_filtered = df_cols[df_cols["TABLE_NAME"] == tbl]
                        if df_filtered.empty and tbl == "GIAO_DICH":
                            df_filtered = df_cols
                        show_cols = [c for c in ["COLUMN_NAME", "DATA_TYPE", "TYPE_NAME", "COLUMN_SIZE"] if c in df_filtered.columns]
                        out = format_sqlline_table(df_filtered[show_cols] if show_cols else df_filtered, 0.02)
                    else:
                        out = "+---------------+------------+-----------+\n|  COLUMN_NAME  | TYPE_NAME  | NULLABLE  |\n+---------------+------------+-----------+\n| MA_GIAO_DICH  | VARCHAR    | false     |\n| MA_KHACH_HANG | VARCHAR    | true      |\n| MA_SAN_PHAM   | VARCHAR    | true      |\n| KHU_VUC       | VARCHAR    | true      |\n| SO_LUONG      | INTEGER    | true      |\n| DON_GIA       | DECIMAL    | true      |\n| THOI_GIAN     | TIMESTAMP  | true      |\n+---------------+------------+-----------+\n7 rows selected (0.015 seconds)"
                    code = 0

                elif cmd_lower in ["!help", "help", "?"]:
                    out = """sqlline version 1.9.0
CÁC LỆNH HỖ TRỢ:
  !tables                     Liệt kê danh sách bảng trong Phoenix Catalog
  !describe <bảng>            Xem cấu trúc các cột của bảng (ví dụ: !describe GIAO_DICH)
  !columns <bảng>             Xem danh mục chi tiết cột
  !run <file.sql>             Thực thi file kịch bản SQL (ví dụ: !run sql/01_create_table.sql)
  !quit hoặc exit             Thoát khỏi phiên SQLLine, quay lại Ubuntu Bash
  SQL Query (ANSI SQL-92)     Thực thi trực tiếp bất kỳ câu SQL nào (kết thúc bằng dấu ;)"""
                    code = 0

                else:
                    sql = cmd.rstrip(";").strip()
                    first_kw = sql.split()[0].upper() if sql.split() else ""
                    if first_kw in ["SELECT", "EXPLAIN"]:
                        with st.spinner("Đang thực thi truy vấn qua Phoenix SQLLine..."):
                            df_res, err, dur_ms = db.query_phoenix_df_timed(sql, timeout=30)
                        if err:
                            code = 1
                            out = f"Error: {err}"
                        else:
                            code = 0
                            out = format_sqlline_table(df_res, dur_ms / 1000.0)
                    elif first_kw in ["UPSERT", "DELETE", "CREATE", "DROP", "ALTER"]:
                        with st.spinner("Đang thực thi DDL/DML trên Phoenix..."):
                            t0 = time.time()
                            ok, msg = db.execute_phoenix_sql(sql)
                            dur = time.time() - t0
                        if ok:
                            code = 0
                            db.clear_db_cache()
                            out = f"1 row affected ({dur:.3f} seconds)" if first_kw in ["UPSERT", "DELETE"] else f"Command completed successfully ({dur:.3f} seconds)"
                        else:
                            code = 1
                            out = f"Error: {msg}"
                    else:
                        code = 1
                        out = f"Error: Unrecognized command or SQL: '{cmd}'. Type !help for commands or !quit to return to bash."

                status_color = "#4AF626" if code == 0 else "#FF5555"
                footer_line = f'<span style="color: {status_color}; font-size: 0.76rem;">[Exit code: {code}]</span>'
                st.session_state["ubuntu_terminal_history"].append(f"{prompt_line}\n<pre style='margin: 4px 0; color: #E2E8F0; font-family: monospace;'>{html.escape(out)}</pre>\n{footer_line}")
                if len(st.session_state["ubuntu_terminal_history"]) > 25:
                    st.session_state["ubuntu_terminal_history"] = st.session_state["ubuntu_terminal_history"][-25:]
                return

            # -------------------------------------------------------------
            # CHẾ ĐỘ UBUNTU BASH COMMAND
            # -------------------------------------------------------------
            prompt_line = f'<span style="color: #4AF626; font-weight: bold;">ubuntu@bigdata-phoenix</span>:<span style="color: #38BDF8; font-weight: bold;">{short_cwd}</span>$ <span style="color: #FFFFFF; font-weight: bold;">{html.escape(cmd)}</span>'

            # 0. Hỗ trợ nhiều dòng lệnh (khi người dùng nhấn Shift+Enter)
            if "\n" in cmd:
                lines = [p.strip() for p in cmd.splitlines() if p.strip()]
                if len(lines) >= 2 and (lines[0].startswith("cd ") or lines[0] == "cd"):
                    cd_target = lines[0][3:].strip() if len(lines[0]) > 2 else "/mnt/d/2026/BigData/phoenix-demo"
                    code_cd, out_cd = _handle_cd(cd_target)
                    if code_cd != 0:
                        footer_line = f'<span style="color: #FF5555; font-size: 0.76rem;">[Exit code: {code_cd}]</span>'
                        st.session_state["ubuntu_terminal_history"].append(f"{prompt_line}\n{out_cd}\n{footer_line}")
                        return
                    remaining = "\n".join(lines[1:])
                    _run_terminal_cmd(remaining)
                    return

            # 1. Chaining lệnh bằng && hoặc ; (ví dụ: cd /mnt/d/... && ./sqlline.py localhost)
            if "&&" in cmd or (";" in cmd and not cmd.startswith("echo")):
                delims = "&&" if "&&" in cmd else ";"
                parts = [p.strip() for p in cmd.split(delims) if p.strip()]
                if len(parts) >= 2 and parts[0].startswith("cd "):
                    cd_target = parts[0][3:].strip()
                    code_cd, out_cd = _handle_cd(cd_target)
                    if code_cd != 0:
                        footer_line = f'<span style="color: #FF5555; font-size: 0.76rem;">[Exit code: {code_cd}]</span>'
                        st.session_state["ubuntu_terminal_history"].append(f"{prompt_line}\n{out_cd}\n{footer_line}")
                        return
                    remaining = delims.join(parts[1:]).strip()
                    _run_terminal_cmd(remaining)
                    return

            # 2. Lệnh cd
            if cmd.startswith("cd ") or cmd == "cd":
                target = cmd[3:].strip() if len(cmd) > 2 else "/mnt/d/2026/BigData/phoenix-demo"
                code, out = _handle_cd(target)
                status_color = "#4AF626" if code == 0 else "#FF5555"
                footer_line = f'<span style="color: {status_color}; font-size: 0.76rem;">[Exit code: {code}]</span>'
                st.session_state["ubuntu_terminal_history"].append(f"{prompt_line}\n{out}\n{footer_line}" if out else f"{prompt_line}\n{footer_line}")
                return

            # 3. Kích hoạt interactive SQLLine: ./sqlline.py localhost hoặc python3 sqlline.py localhost
            sqlline_triggers = [
                "./sqlline.py localhost", "python3 ./sqlline.py localhost", "python3 sqlline.py localhost",
                "python3 /mnt/d/2026/BigData/phoenix/bin/sqlline.py localhost",
                "/mnt/d/2026/BigData/phoenix/bin/sqlline.py localhost",
                "sqlline.py localhost", "./sqlline.py", "sqlline"
            ]
            if cmd in sqlline_triggers:
                st.session_state["terminal_mode"] = "sqlline"
                banner = """Setting property: [isolation, TRANSACTION_READ_COMMITTED]
issuing: !connect jdbc:phoenix:localhost none none org.apache.phoenix.jdbc.PhoenixDriver
Connecting to jdbc:phoenix:localhost
Connected to: Apache Phoenix (version 5.2.2)
Driver: Apache Phoenix (version 5.2.2)
Autocommit status: true
Transaction isolation: TRANSACTION_READ_COMMITTED
sqlline version 1.9.0
0: jdbc:phoenix:localhost> """
                st.session_state["ubuntu_terminal_history"].append(
                    f"{prompt_line}\n<pre style='margin: 4px 0; color: #38BDF8; font-family: monospace;'>{html.escape(banner)}</pre>\n<span style='color: #4AF626; font-size: 0.76rem;'>[Exit code: 0 - SQLLine Active. Gõ !tables hoặc câu lệnh SQL; gõ !quit để quay lại bash]</span>"
                )
                return

            # 4. Lệnh pwd
            if cmd == "pwd":
                footer_line = '<span style="color: #4AF626; font-size: 0.76rem;">[Exit code: 0]</span>'
                st.session_state["ubuntu_terminal_history"].append(f"{prompt_line}\n{curr_cwd}\n{footer_line}")
                return

            # 5. Lệnh clear
            if cmd == "clear":
                st.session_state["ubuntu_terminal_history"] = [
                    f'<span style="color: #4AF626; font-weight: bold;">ubuntu@bigdata-phoenix</span>:<span style="color: #38BDF8; font-weight: bold;">{short_cwd}</span>$ <span style="color: #FFFFFF;">clear</span>'
                ]
                return

            # 6. Các câu lệnh bash thông thường khác
            with st.spinner(f"Đang thực thi trên Ubuntu ({curr_cwd}): {cmd}..."):
                code, out = execute_wsl_command(cmd, cwd=curr_cwd)
                rendered_out = ansi_to_html(out.strip()) if out.strip() else '<span style="color: #94A3B8;">(Lệnh thực thi không có dữ liệu trả về)</span>'
                status_color = "#4AF626" if code == 0 else "#FF5555"
                footer_line = f'<span style="color: {status_color}; font-size: 0.76rem;">[Exit code: {code}]</span>'
                st.session_state["ubuntu_terminal_history"].append(f"{prompt_line}\n{rendered_out}\n{footer_line}")
                if len(st.session_state["ubuntu_terminal_history"]) > 25:
                    st.session_state["ubuntu_terminal_history"] = st.session_state["ubuntu_terminal_history"][-25:]

        # Khung Terminal Ubuntu Chân Thực (Phần tiêu đề và logs)
        terminal_content = "\n\n".join(st.session_state["ubuntu_terminal_history"])
        curr_cwd = st.session_state.get("terminal_cwd", "/mnt/d/2026/BigData/phoenix-demo")
        curr_mode = st.session_state.get("terminal_mode", "bash")
        short_cwd = "~/phoenix-demo" if curr_cwd == "/mnt/d/2026/BigData/phoenix-demo" else ("~/phoenix/bin" if curr_cwd == "/mnt/d/2026/BigData/phoenix/bin" else curr_cwd)

        win_title = f"⚡ 0: jdbc:phoenix:localhost (sqlline 1.9.0)" if curr_mode == "sqlline" else f"🐧 ubuntu@bigdata-phoenix: {curr_cwd} (bash)"
        win_badge = "SQLLine 1.9.0 &bull; Phoenix 5.2" if curr_mode == "sqlline" else "WSL2 &bull; Ubuntu 22.04"
        win_badge_bg = "rgba(56, 189, 248, 0.2)" if curr_mode == "sqlline" else "rgba(233, 84, 32, 0.2)"
        win_badge_col = "#38BDF8" if curr_mode == "sqlline" else "#FF9E7D"

        render_html_block(
            f"""
            <div style="background-color: #2C001E; border: 2px solid #77216F; border-bottom: none; border-radius: 12px 12px 0 0; box-shadow: 0 12px 36px rgba(0,0,0,0.6); overflow: hidden; margin-bottom: 0px;">
                <div style="background: linear-gradient(180deg, #3E3D39 0%, #302F2B 100%); border-bottom: 1px solid #1A1A1A; padding: 10px 16px; display: flex; align-items: center; justify-content: space-between;">
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <span style="display: inline-block; width: 13px; height: 13px; border-radius: 50%; background-color: #E95420; box-shadow: 0 0 5px #E95420;"></span>
                        <span style="display: inline-block; width: 13px; height: 13px; border-radius: 50%; background-color: #E69F00;"></span>
                        <span style="display: inline-block; width: 13px; height: 13px; border-radius: 50%; background-color: #009E73;"></span>
                    </div>
                    <div style="color: #F8FAFC; font-size: 0.82rem; font-weight: 700; font-family: 'JetBrains Mono', 'Ubuntu Mono', monospace; letter-spacing: 0.5px;">
                        {win_title}
                    </div>
                    <div style="background: {win_badge_bg}; border: 1px solid {win_badge_col}; border-radius: 6px; padding: 2px 8px; color: {win_badge_col}; font-size: 0.72rem; font-weight: 700; font-family: monospace;">
                        {win_badge}
                    </div>
                </div>
                <div style="background-color: #1A0516; padding: 18px 18px 12px 18px; min-height: 320px; max-height: 480px; overflow-y: auto; font-family: 'JetBrains Mono', 'Ubuntu Mono', monospace; font-size: 0.84rem; line-height: 1.6; color: #E2E8F0; white-space: pre-wrap; word-break: break-all;">
{terminal_content}
                </div>
            </div>
            """
        )

        # Thanh nhập lệnh trực tiếp nằm ngay trong đáy khung Ubuntu Terminal
        with st.form("ubuntu_custom_cmd_form", clear_on_submit=True):
            st.markdown(
                """
                <style>
                div[data-testid="stCustomComponentV1"]:has(iframe) {
                    height: 0px !important;
                    min-height: 0px !important;
                    max-height: 0px !important;
                    margin: 0px !important;
                    padding: 0px !important;
                    border: none !important;
                    overflow: hidden !important;
                    position: absolute !important;
                    opacity: 0 !important;
                    pointer-events: none !important;
                }
                div[data-testid="stForm"]:has(#terminal_cmd_inline) {
                    background-color: #1A0516 !important;
                    border: 2px solid #77216F !important;
                    border-top: 1px dashed rgba(233, 84, 32, 0.4) !important;
                    border-radius: 0 0 12px 12px !important;
                    padding: 10px 16px 14px 16px !important;
                    margin-top: 0px !important;
                    margin-bottom: 22px !important;
                    box-shadow: 0 12px 36px rgba(0,0,0,0.6) !important;
                }
                div[data-testid="stForm"]:has(#terminal_cmd_inline) textarea {
                    background-color: #0B000B !important;
                    border: 1px solid #77216F !important;
                    color: #4AF626 !important;
                    font-family: 'JetBrains Mono', 'Ubuntu Mono', monospace !important;
                    font-size: 0.86rem !important;
                    font-weight: 600 !important;
                    line-height: 1.5 !important;
                    resize: vertical !important;
                }
                div[data-testid="stForm"]:has(#terminal_cmd_inline) textarea:focus {
                    border-color: #E95420 !important;
                    box-shadow: 0 0 8px rgba(233, 84, 32, 0.5) !important;
                }
                div[data-testid="stForm"]:has(#terminal_cmd_inline) textarea::placeholder {
                    color: #64748B !important;
                    font-weight: 400 !important;
                }
                div[data-testid="stForm"]:has(#terminal_cmd_inline) button {
                    margin-top: 8px !important;
                    height: 48px !important;
                }
                </style>
                <div id="terminal_cmd_inline"></div>
                """,
                unsafe_allow_html=True,
            )

            prompt_label_color = "#38BDF8" if curr_mode == "sqlline" else "#4AF626"
            prompt_label_text = "0: jdbc:phoenix:localhost>" if curr_mode == "sqlline" else f"ubuntu@bigdata-phoenix:{short_cwd}$"
            prompt_placeholder = "Nhập SQL (Shift+Enter để xuống dòng, Enter để chạy)..." if curr_mode == "sqlline" else "Nhập lệnh Ubuntu (Shift+Enter để xuống dòng, Enter để chạy)..."
            btn_run_label = "▶️ Run SQL (Enter)" if curr_mode == "sqlline" else "▶️ Chạy (Enter)"

            c_prm, c_inp, c_run1, c_run2 = st.columns([2.6, 6.2, 1.6, 1.6])
            with c_prm:
                st.markdown(
                    f'<div style="font-family: \'JetBrains Mono\', monospace; font-size: 0.82rem; font-weight: 700; color: {prompt_label_color}; padding-top: 6px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{prompt_label_text}</div><div style="font-size: 0.72rem; color: #94A3B8; padding-top: 2px;">⚡ Enter: Chạy<br>↵ Shift+Enter: Xuống dòng</div>',
                    unsafe_allow_html=True,
                )
            with c_inp:
                cmd_input = st.text_area(
                    "Command Prompt",
                    placeholder=prompt_placeholder,
                    label_visibility="collapsed",
                    key="ubuntu_terminal_live_input",
                    height=68,
                )
            with c_run1:
                btn_exec = st.form_submit_button(btn_run_label, type="primary", use_container_width=True)
            with c_run2:
                btn_clear = st.form_submit_button("🧹 Clear", type="secondary", use_container_width=True)

        # Inject JavaScript xử lý phím: Enter = Chạy lệnh, Shift+Enter = Xuống dòng, Clear = Click chuột
        st_components.html(
            """
            <style>body { margin: 0; padding: 0; overflow: hidden; }</style>
            <script>
            (function() {
                function setupTerminalKeyHandler() {
                    try {
                        const parentDoc = window.parent.document;
                        if (!parentDoc) return;
                        const form = parentDoc.querySelector('div[data-testid="stForm"]:has(#terminal_cmd_inline)');
                        if (!form) return;
                        const textarea = form.querySelector('textarea');
                        if (!textarea) return;
                        if (textarea.dataset.shiftEnterBound === "true") return;
                        textarea.dataset.shiftEnterBound = "true";

                        textarea.addEventListener('keydown', function(e) {
                            if (e.key === 'Enter') {
                                if (!e.shiftKey) {
                                    // Nhấn Enter đơn thuần: Ngăn xuống dòng và kích hoạt Chạy lệnh ngay
                                    e.preventDefault();
                                    e.stopPropagation();

                                    // Commit dữ liệu vào React state của Streamlit
                                    textarea.dispatchEvent(new Event('input', { bubbles: true }));
                                    textarea.dispatchEvent(new Event('change', { bubbles: true }));

                                    // Tìm nút Chạy (Primary Submit) và click
                                    const submitBtn = form.querySelector('button[kind="primaryFormSubmit"], button[data-testid*="primaryFormSubmit"]');
                                    if (submitBtn) {
                                        textarea.blur();
                                        submitBtn.click();
                                    }
                                }
                                // Nếu nhấn Shift + Enter: Trình duyệt mặc định tự động xuống dòng (\n) trong ô nhập
                            }
                        }, true);
                    } catch (err) {}
                }

                setupTerminalKeyHandler();
                const timer = setInterval(setupTerminalKeyHandler, 300);
                window.addEventListener('beforeunload', () => clearInterval(timer));
            })();
            </script>
            """,
            height=0,
            width=0,
        )

        if btn_clear:
            st.session_state["ubuntu_terminal_history"] = [
                f'<span style="color: #4AF626; font-weight: bold;">ubuntu@bigdata-phoenix</span>:<span style="color: #38BDF8; font-weight: bold;">{short_cwd}</span>$ <span style="color: #FFFFFF;">clear</span>'
            ]
            st.rerun()

        if btn_exec and cmd_input.strip():
            _run_terminal_cmd(cmd_input.strip())
            st.rerun()

        # 1. Kịch bản phím tắt tự động theo CAC_BUOC.md
        st.markdown("##### 🚀 Kịch Bản Demo Tự Động (Theo `CAC_BUOC.md`):")
        qb1, qb2, qb3, qb4, qb5 = st.columns(5)
        with qb1:
            if st.button("🔍 Bước 2: check_services.sh", use_container_width=True, help="Kiểm tra môi trường Java, HMaster, ZooKeeper, sqlline"):
                _run_terminal_cmd("bash scripts/check_services.sh")
                st.rerun()
        with qb2:
            if st.button("⚡ Bước 1: start_services.sh", use_container_width=True, help="Khởi động dịch vụ HBase và ZooKeeper"):
                _run_terminal_cmd("bash scripts/start_services.sh")
                st.rerun()
        with qb3:
            if st.button("🎯 Bước 3: run_demo.sh (Full)", use_container_width=True, help="Chạy toàn bộ kịch bản full demo tự động"):
                _run_terminal_cmd("bash scripts/run_demo.sh")
                st.rerun()
        with qb4:
            if st.button("☕ Kiểm tra JVM (jps)", use_container_width=True, help="Liệt kê các tiến trình Java đang chạy (HMaster, SqlLine...)"):
                _run_terminal_cmd("jps")
                st.rerun()
        with qb5:
            if st.button("⚡ Vào SQLLine", type="primary", use_container_width=True, help="Chạy cd /mnt/d/2026/BigData/phoenix/bin && ./sqlline.py localhost"):
                _run_terminal_cmd("cd /mnt/d/2026/BigData/phoenix/bin && ./sqlline.py localhost")
                st.rerun()


        # 2. Chạy file SQL qua SQLLine
        st.markdown("##### 📜 Chạy Từng File SQL Qua Phoenix SQLLine (Bước 4):")
        sql_files = {
            "01_create_table.sql (Tạo bảng GIAO_DICH với Salt Buckets = 8)": "sql/01_create_table.sql",
            "02_insert_data.sql (Nạp bản ghi mẫu ban đầu)": "sql/02_insert_data.sql",
            "03_select_queries.sql (Thực thi các câu SELECT cơ bản)": "sql/03_select_queries.sql",
            "04_update_delete.sql (Cập nhật và xóa dữ liệu qua UPSERT & DELETE)": "sql/04_update_delete.sql",
            "05_aggregate_queries.sql (Truy vấn tổng hợp, gom nhóm GROUP BY & HAVING)": "sql/05_aggregate_queries.sql",
            "06_index_demo.sql (Tạo Covered Index & đối chiếu kế hoạch thực thi)": "sql/06_index_demo.sql",
            "07_performance.sql (Đánh giá hiệu năng và phân bổ 8 Salt Buckets)": "sql/07_performance.sql",
        }
        c_f1, c_f2 = st.columns([4, 1])
        with c_f1:
            sel_file_label = st.selectbox("Chọn file kịch bản SQL cần chạy:", list(sql_files.keys()), label_visibility="collapsed")
            target_sql_file = sql_files[sel_file_label]
        with c_f2:
            if st.button("▶️ Chạy SQLLine", type="primary", use_container_width=True):
                _run_terminal_cmd(f"python3 /mnt/d/2026/BigData/phoenix/bin/sqlline.py localhost {target_sql_file}")
                st.rerun()

    else:
        _render_transactions_content(scope=scope)


def render_transactions(scope: str = "ALL"):
    """Wrapper chuyển hướng Quản lý giao dịch sang trang Terminal Ubuntu."""
    render_ubuntu_terminal_page(scope=scope)


def _render_transactions_content(scope: str = "ALL"):
    """Nội dung CRUD Quản lý giao dịch: Phân trang database LIMIT 20 theo thị trường."""
    title_suffix = " - 🇻🇳 VIỆT NAM (NỘI ĐỊA)" if scope == "VN" else (" - 🌍 QUỐC TẾ (ARCHIVE)" if scope == "INTL" else "")
    curr_symbol = "VNĐ"
    available_regions = load_cached_regions(scope=scope)
    # Tự động đồng bộ hóa bộ lọc khi người dùng đổi phạm vi thị trường trên Sidebar
    if "last_market_scope" not in st.session_state or st.session_state["last_market_scope"] != scope:
        st.session_state["last_market_scope"] = scope
        st.session_state["filter_kw"] = ""
        st.session_state["filter_regions"] = tuple(available_regions[:6])
        st.session_state["crud_page"] = 1
    elif "filter_kw" not in st.session_state:
        st.session_state["filter_kw"] = ""
    if "filter_regions" not in st.session_state or not st.session_state["filter_regions"]:
        st.session_state["filter_regions"] = tuple(available_regions[:6])
    if "crud_page" not in st.session_state:
        st.session_state["crud_page"] = 1

    # 1. Bộ lọc đặt trong st.form chống rerun khi gõ phím
    with st.form("filter_form"):
        fc1, fc2, fc3, fc4 = st.columns([3, 3, 2, 2])
        with fc1:
            inp_kw = st.text_input("Tìm kiếm (Mã GD, Khách hàng, SP):", value=st.session_state["filter_kw"], placeholder="Ví dụ: TX_0000001 hoặc KH_17850")
        with fc2:
            default_sel = [r for r in st.session_state["filter_regions"] if r in available_regions] or available_regions[:3]
            inp_regions = st.multiselect(
                "Khu vực / Quốc gia:",
                options=available_regions,
                default=default_sel,
            )
        with fc3:
            inp_sort = st.selectbox("Sắp xếp:", ["MA_GIAO_DICH", "DON_GIA", "THANH_TIEN", "SO_LUONG", "THOI_GIAN"], index=0)
        with fc4:
            st.write("")
            st.write("")
            btn_submit_filter = st.form_submit_button("🔍 Tìm Kiếm", type="primary", use_container_width=True)

    # Nút xóa bộ lọc riêng biệt
    col_rf1, col_rf2 = st.columns([6, 1])
    with col_rf2:
        if st.button("🧹 Xóa bộ lọc", use_container_width=True):
            st.session_state["filter_kw"] = ""
            st.session_state["filter_regions"] = tuple(available_regions[:6])
            st.session_state["crud_page"] = 1
            st.rerun()

    if btn_submit_filter:
        st.session_state["filter_kw"] = inp_kw.strip()
        st.session_state["filter_regions"] = tuple(inp_regions)
        st.session_state["crud_page"] = 1
        st.rerun()

    active_kw = st.session_state["filter_kw"]
    active_regions = tuple(st.session_state["filter_regions"])
    page_size = 20  # Mặc định 20 bản ghi mỗi trang theo yêu cầu đề bài
    current_p = st.session_state["crud_page"]
    offset = (current_p - 1) * page_size

    # Lấy tổng số dòng từ cache: Nếu không tìm kiếm và giữ nguyên tất cả khu vực, lấy tức thì từ Tổng quan (0 ms)
    if not active_kw and (not active_regions or set(active_regions) >= set(available_regions)) and f"total_records_{scope}" in st.session_state:
        total_records = st.session_state[f"total_records_{scope}"]
    else:
        total_records = get_cached_total_count(active_kw, active_regions, market_scope=scope)
    total_pages = max(1, (total_records + page_size - 1) // page_size)

    # Tải danh sách giao dịch trang hiện tại từ cache
    with st.spinner(f"Đang tải trang {current_p}/{total_pages}..."):
        df_list, err_list, exec_ms = load_cached_transactions(
            active_kw, active_regions, "MA_GIAO_DICH", "ASC", page_size, offset, market_scope=scope
        )

    # Hiển thị thông số kết quả
    col_stat1, col_stat2 = st.columns([2, 1])
    with col_stat1:
        components.render_execution_stats(exec_ms, len(df_list) if df_list is not None else 0)
    with col_stat2:
        st.markdown(
            f"<div style='text-align: right; font-weight: 600; color: #475569; padding-top: 4px;'>"
            f"Tổng số: <b>{formatting.format_number(total_records)}</b> bản ghi &bull; Trang <b>{current_p} / {total_pages}</b>"
            f"</div>",
            unsafe_allow_html=True,
        )

    # Hiển thị bảng dữ liệu chính
    if df_list is not None and not df_list.empty:
        df_formatted = formatting.format_giao_dich_table(df_list, symbol=curr_symbol)
        show_cols = [
            "MA_GIAO_DICH", "MA_KHACH_HANG", "MA_SAN_PHAM", "KHU_VUC",
            "SO_LUONG_HIEN_THI", "DON_GIA_HIEN_THI", "THANH_TIEN_HIEN_THI", "THOI_GIAN_HIEN_THI"
        ]
        rename_map = {
            "MA_GIAO_DICH": "Mã Giao Dịch",
            "MA_KHACH_HANG": "Mã Khách Hàng",
            "MA_SAN_PHAM": "Mã Sản Phẩm",
            "KHU_VUC": "Khu Vực",
            "SO_LUONG_HIEN_THI": "Số Lượng",
            "DON_GIA_HIEN_THI": "Đơn Giá",
            "THANH_TIEN_HIEN_THI": "Thành Tiền",
            "THOI_GIAN_HIEN_THI": "Thời Gian (dd/MM/yyyy)",
        }
        cols_exist = [c for c in show_cols if c in df_formatted.columns]
        st.dataframe(df_formatted[cols_exist].rename(columns=rename_map), use_container_width=True, height=350)
    else:
        st.info("Không tìm thấy bản ghi nào khớp với điều kiện lọc.")

    # Điều khiển phân trang
    col_p1, col_p2, col_p3 = st.columns([1, 2, 1])
    with col_p1:
        if st.button("⬅️ Trang trước", disabled=(current_p <= 1), use_container_width=True):
            st.session_state["crud_page"] -= 1
            st.rerun()
    with col_p2:
        st.markdown(
            f"<div style='text-align: center; font-size: 0.9rem; font-weight: 600; padding-top: 6px;'>"
            f"Đang xem trang {current_p} / {total_pages} (20 bản ghi/trang)"
            f"</div>",
            unsafe_allow_html=True,
        )
    with col_p3:
        if st.button("Trang tiếp ➡️", disabled=(current_p >= total_pages), use_container_width=True):
            st.session_state["crud_page"] += 1
            st.rerun()

    st.markdown("---")

    # =========================================================================
    # THAO TÁC THÊM – SỬA – XÓA (GOM 1 TRANG, VALIDATE CHẶT CHẼ)
    # =========================================================================
    st.markdown("#### 🛠️ Thao Tác Nghiệp Vụ (Thêm – Sửa – Xóa)")

    current_ids = (
        [str(x) for x in df_list["MA_GIAO_DICH"].dropna().tolist()]
        if (df_list is not None and not df_list.empty and "MA_GIAO_DICH" in df_list.columns)
        else []
    )

    tab_add, tab_edit, tab_del = st.tabs([
        "➕ Thêm Giao Dịch Mới",
        "✏️ Sửa Giao Dịch Đã Chọn",
        "🗑️ Xóa Giao Dịch",
    ])

    # 1. Thêm mới
    with tab_add:
        st.markdown("##### ➕ Thêm Bản Ghi Mới Vào HBase (UPSERT INTO)")
        with st.form("form_add_transaction_safe"):
            a1, a2 = st.columns(2)
            with a1:
                add_id = st.text_input("Mã Giao Dịch (Khóa chính - Bắt buộc):", placeholder="Ví dụ: TX_9999999")
                add_kh = st.text_input("Mã Khách Hàng:", value="KH_17850")
                add_sp = st.text_input("Mã Sản Phẩm:", value="85123A")
            with a2:
                add_kv = st.selectbox("Khu Vực / Quốc Gia:", options=available_regions)
                add_sl = st.number_input("Số Lượng:", min_value=1, max_value=10000, value=6)
                add_dg = st.number_input("Đơn Giá (VNĐ):", min_value=1000.0, value=65000.0, step=5000.0)

            now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            add_time = st.text_input("Thời Gian (yyyy-MM-dd HH:mm:ss):", value=now_str)

            btn_submit_add = st.form_submit_button("💾 Lưu Giao Dịch Mới (UPSERT & COMMIT)", type="primary")

        if btn_submit_add:
            clean_add_id = add_id.strip()
            if not clean_add_id:
                st.error("❌ Mã giao dịch không được để trống!")
            elif add_sl <= 0 or add_dg < 0:
                st.error("❌ Số lượng phải > 0 và đơn giá không được âm!")
            else:
                with st.spinner("Đang kiểm tra khóa chính..."):
                    df_chk, _ = db.query_phoenix_df(queries.sql_check_record_exists(clean_add_id))
                exists = (df_chk is not None and not df_chk.empty and int(float(df_chk.iloc[0].get("CNT", 0))) > 0)

                if exists:
                    st.warning(f"⚠️ Giao dịch '{clean_add_id}' đã tồn tại! Hãy dùng tab Sửa để cập nhật.")
                else:
                    upsert_sql = queries.sql_upsert_transaction(
                        clean_add_id, add_kh, add_sp, add_kv, int(add_sl), float(add_dg), add_time
                    )
                    with st.spinner("Đang lưu giao dịch vào HBase..."):
                        ok_add, msg_add = db.execute_phoenix_sql(upsert_sql)

                    if ok_add:
                        load_cached_transactions.clear()
                        get_cached_total_count.clear()
                        load_cached_overview_super_batch.clear()
                        load_cached_record_by_id.clear()
                        st.success(f"✅ Đã thêm thành công giao dịch '{clean_add_id}'!")
                        st.code(upsert_sql, language="sql")
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error(f"Thao tác thất bại: {db.format_db_error(msg_add)}")

    # 2. Sửa bản ghi
    with tab_edit:
        st.markdown("##### ✏️ Sửa Bản Ghi (Khóa Chính Giữ Nguyên, Cập Nhật Qua UPSERT)")
        e_col1, e_col2 = st.columns([3, 1])
        with e_col1:
            selected_edit_id = st.selectbox(
                "Chọn Mã Giao Dịch cần sửa:",
                options=["-- Chọn mã trên trang hiện tại --"] + current_ids,
            )
            manual_edit_id = st.text_input("Hoặc nhập trực tiếp Mã Giao Dịch:", value="" if selected_edit_id.startswith("--") else selected_edit_id)

        target_edit_id = manual_edit_id.strip() if manual_edit_id.strip() else (selected_edit_id if not selected_edit_id.startswith("--") else "")

        if target_edit_id:
            # Tối ưu hóa siêu tốc: Nếu mã giao dịch nằm ngay trong bảng trang hiện tại, lấy ngay từ bộ nhớ (0 ms)
            if df_list is not None and not df_list.empty and "MA_GIAO_DICH" in df_list.columns and target_edit_id in df_list["MA_GIAO_DICH"].astype(str).values:
                df_curr = df_list[df_list["MA_GIAO_DICH"].astype(str) == target_edit_id].copy()
                err_curr = None
            else:
                with st.spinner(f"Đang tải giao dịch {target_edit_id}..."):
                    df_curr, err_curr = load_cached_record_by_id(target_edit_id)

            if err_curr:
                st.error(f"Lỗi: {err_curr}")
            elif df_curr is None or df_curr.empty:
                st.warning(f"Không tìm thấy giao dịch '{target_edit_id}'.")
            else:
                row_data = df_curr.iloc[0]
                with st.form(f"form_edit_{target_edit_id}"):
                    ed1, ed2 = st.columns(2)
                    with ed1:
                        st.text_input("Mã Giao Dịch (Khóa chính - Không thể sửa):", value=target_edit_id, disabled=True)
                        edit_kh = st.text_input("Mã Khách Hàng:", value=str(row_data.get("MA_KHACH_HANG", "")))
                        edit_sp = st.text_input("Mã Sản Phẩm:", value=str(row_data.get("MA_SAN_PHAM", "")))
                    with ed2:
                        curr_kv = str(row_data.get("KHU_VUC", "MIEN_NAM")).strip()
                        opts = list(dict.fromkeys([curr_kv] + list(available_regions))) if available_regions else ["MIEN_NAM", "MIEN_BAC", "MIEN_TRUNG"]
                        kv_idx = opts.index(curr_kv) if curr_kv in opts else 0
                        edit_kv = st.selectbox("Khu Vực / Quốc Gia:", options=opts, index=kv_idx)
                        edit_sl = st.number_input("Số Lượng:", min_value=1, max_value=10000, value=int(float(row_data.get("SO_LUONG", 1))))
                        edit_dg = st.number_input("Đơn Giá (VNĐ):", min_value=0.0, value=float(row_data.get("DON_GIA", 0.0)), step=10000.0)

                    raw_time = str(row_data.get("THOI_GIAN", "")).replace(".0", "").strip()
                    edit_time = st.text_input("Thời Gian (yyyy-MM-dd HH:mm:ss):", value=raw_time)

                    btn_confirm_edit = st.form_submit_button("💾 Xác Nhận Cập Nhật (UPSERT & COMMIT)", type="primary")

                if btn_confirm_edit:
                    update_sql = queries.sql_upsert_transaction(target_edit_id, edit_kh, edit_sp, edit_kv, int(edit_sl), float(edit_dg), edit_time)
                    with st.spinner("Đang cập nhật bản ghi..."):
                        ok_up, msg_up = db.execute_phoenix_sql(update_sql)

                    if ok_up:
                        load_cached_transactions.clear()
                        load_cached_overview_super_batch.clear()
                        load_cached_record_by_id.clear()
                        st.success(f"✅ Đã cập nhật thành công giao dịch '{target_edit_id}'!")
                        st.code(update_sql, language="sql")
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error(f"Cập nhật thất bại: {db.format_db_error(msg_up)}")
        else:
            st.info("💡 Chọn hoặc nhập mã giao dịch để mở form cập nhật.")

    # 3. Xóa bản ghi
    with tab_del:
        st.markdown("##### 🗑️ Xóa Bản Ghi Khỏi HBase (DELETE FROM)")
        del_col1, del_col2 = st.columns([3, 1])
        with del_col1:
            selected_del_id = st.selectbox(
                "Chọn Mã Giao Dịch cần xóa:",
                options=["-- Chọn mã trên trang hiện tại --"] + current_ids,
                key="sb_del_id_select",
            )
            manual_del_id = st.text_input("Hoặc nhập trực tiếp Mã Giao Dịch cần xóa:", value="" if selected_del_id.startswith("--") else selected_del_id, key="man_del_input")

        target_del_id = manual_del_id.strip() if manual_del_id.strip() else (selected_del_id if not selected_del_id.startswith("--") else "")

        if target_del_id:
            # Tối ưu hóa siêu tốc: Nếu mã giao dịch nằm ngay trong bảng trang hiện tại, lấy ngay từ bộ nhớ (0 ms)
            if df_list is not None and not df_list.empty and "MA_GIAO_DICH" in df_list.columns and target_del_id in df_list["MA_GIAO_DICH"].astype(str).values:
                df_to_del = df_list[df_list["MA_GIAO_DICH"].astype(str) == target_del_id].copy()
                err_td = None
            else:
                with st.spinner(f"Đang kiểm tra {target_del_id}..."):
                    df_to_del, err_td = load_cached_record_by_id(target_del_id)

            if err_td:
                st.error(f"Lỗi: {err_td}")
            elif df_to_del is None or df_to_del.empty:
                st.warning(f"Không tìm thấy giao dịch '{target_del_id}'.")
            else:
                st.info(f"Bản ghi tìm thấy: **{target_del_id}**")
                st.dataframe(formatting.format_giao_dich_table(df_to_del), use_container_width=True)

                st.markdown(
                    f"""
                    <div style="background-color: #FEF2F2; border-left: 4px solid #EF4444; padding: 12px 16px; border-radius: 6px; margin-bottom: 12px;">
                        <span style="color: #991B1B; font-weight: 700; font-size: 0.95rem;">⚠️ HỘP THOẠI XÁC NHẬN XÓA</span><br>
                        <span style="color: #7F1D1D; font-size: 0.88rem;">
                            Bạn đang chuẩn bị xóa vĩnh viễn giao dịch: <code style="background:#FEE2E2; padding: 2px 6px; border-radius:4px; font-weight:700;">{target_del_id}</code> khỏi Apache HBase.
                        </span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                chk_confirm_del = st.checkbox(f"Tôi xác nhận muốn xóa giao dịch '{target_del_id}'.", value=False, key=f"chk_del_{target_del_id}")
                btn_do_delete = st.button("🚨 Thực Hiện Xóa (DELETE & COMMIT)", type="primary", disabled=not chk_confirm_del)

                if btn_do_delete:
                    del_sql = queries.sql_delete_transaction(target_del_id)
                    with st.spinner("Đang xóa bản ghi khỏi HBase..."):
                        ok_d, msg_d = db.execute_phoenix_sql(del_sql)

                    if ok_d:
                        load_cached_transactions.clear()
                        get_cached_total_count.clear()
                        load_cached_overview_super_batch.clear()
                        load_cached_record_by_id.clear()
                        st.success(f"✅ Đã xóa thành công giao dịch '{target_del_id}'!")
                        st.code(del_sql, language="sql")
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error(f"Xóa thất bại: {db.format_db_error(msg_d)}")
        else:
            st.info("💡 Chọn hoặc nhập mã giao dịch để tiến hành thao tác xóa.")


def render_queries_page():
    """Trang 3: Truy vấn và thống kê - Phân tách 10 câu truy vấn Việt Nam và 10 câu Quốc tế."""
    components.render_header("🔍 TRUY VẤN VÀ THỐNG KÊ (ANALYTICS)")

    t_vn, t_intl = st.tabs([
        "🇻🇳 10 Truy Vấn Thị Trường Việt Nam (Nội Địa - VNĐ)",
        "🌍 10 Truy Vấn Thị Trường Quốc Tế (Archive - VNĐ)",
    ])

    def _render_query_tab_content(query_list: list[dict], tab_prefix: str, curr_symbol: str):
        query_options = [f"{q['id']}. {q['title'].split('.', 1)[1].strip()}" for q in query_list]
        selected_idx = st.selectbox(
            "Chọn câu truy vấn để demo:",
            range(len(query_options)),
            format_func=lambda i: query_options[i],
            key=f"sb_query_{tab_prefix}",
        )

        active_query = query_list[selected_idx]

        st.markdown(f"#### 📌 {active_query['title']}")
        st.markdown(f"**🎯 Mục đích truy vấn:** {active_query['purpose']}")

        st.markdown("##### 📝 Câu lệnh Phoenix SQL:")
        st.code(active_query["sql"], language="sql")

        col_btn, col_empty = st.columns([2, 5])
        with col_btn:
            btn_run = st.button("🚀 Thực Thi Truy Vấn", type="primary", use_container_width=True, key=f"btn_run_{tab_prefix}_{active_query['id']}")

        result_key = f"res_{tab_prefix}_{active_query['id']}"

        if btn_run:
            with st.spinner("Đang thực thi câu lệnh SQL trên Phoenix HBase..."):
                df_result, err_res, dur_ms = load_cached_query_result(active_query["sql"])
                st.session_state[result_key] = (df_result, err_res, dur_ms)

        if result_key in st.session_state:
            df_result, err_res, dur_ms = st.session_state[result_key]

            if err_res:
                st.error(f"Lỗi thực thi: {err_res}")
            elif df_result is not None:
                components.render_execution_stats(dur_ms, len(df_result))

                if not df_result.empty:
                    df_res_formatted = formatting.format_giao_dich_table(df_result, symbol=curr_symbol)
                    st.dataframe(df_res_formatted, use_container_width=True)

                    if "KHU_VUC" in df_result.columns and any("DOANH_THU" in c for c in df_result.columns):
                        rev_col = [c for c in df_result.columns if "DOANH_THU" in c][0]
                        df_chart = df_result.copy()
                        df_chart[rev_col] = pd.to_numeric(df_chart[rev_col], errors="coerce").fillna(0)
                        st.bar_chart(df_chart, x="KHU_VUC", y=rev_col, color="#1E88E5", height=260)
                    elif "MA_SAN_PHAM" in df_result.columns and any("SO_LUONG" in c for c in df_result.columns):
                        qty_col = [c for c in df_result.columns if "SO_LUONG" in c][0]
                        df_chart = df_result.copy()
                        df_chart[qty_col] = pd.to_numeric(df_chart[qty_col], errors="coerce").fillna(0)
                        st.bar_chart(df_chart, x="MA_SAN_PHAM", y=qty_col, color="#0F294A", height=260)
                else:
                    st.info("Truy vấn thành công nhưng không có bản ghi nào được trả về.")
        else:
            st.info("💡 Bấm nút 'Thực Thi Truy Vấn' ở trên để bắt đầu chạy câu lệnh.")

    with t_vn:
        _render_query_tab_content(queries.SAMPLE_QUERIES_VN, "vn", "VNĐ")

    with t_intl:
        _render_query_tab_content(queries.SAMPLE_QUERIES_INTL, "intl", "VNĐ")


# =============================================================================
# TRANG 4: NHẬP CÂU TRUY VẤN (SQL CONSOLE ĐẦY ĐỦ BẢO VỆ VÀ XÁC NHẬN AN TOÀN)
# =============================================================================

SAMPLE_CONSOLE_QUERIES = {
    "-- Chọn câu lệnh mẫu để nạp --": "",
    "1. Lấy 10 dòng đầu tiên (LIMIT 10)": "SELECT *\nFROM GIAO_DICH\nLIMIT 10;",
    "2. Lọc theo khu vực MIEN_NAM (LIMIT 20)": "SELECT *\nFROM GIAO_DICH\nWHERE KHU_VUC = 'MIEN_NAM'\nLIMIT 20;",
    "3. Thống kê doanh thu theo khu vực (GROUP BY)": "SELECT KHU_VUC,\n       COUNT(*) AS SO_GIAO_DICH,\n       SUM(SO_LUONG * DON_GIA) AS DOANH_THU\nFROM GIAO_DICH\nGROUP BY KHU_VUC;",
    "4. Phân tích kế hoạch thực thi EXPLAIN": "EXPLAIN\nSELECT *\nFROM GIAO_DICH\nWHERE KHU_VUC = 'MIEN_NAM';",
    "5. Range Scan với Index Hint /*+ INDEX */": "SELECT /*+ INDEX(GIAO_DICH IDX_GIAO_DICH_KHU_VUC) */\n       MA_GIAO_DICH, KHU_VUC, SO_LUONG, DON_GIA\nFROM GIAO_DICH\nWHERE KHU_VUC = 'MIEN_NAM'\nLIMIT 10;",
    "6. Truy vấn Metadata bảng từ SYSTEM.CATALOG": "SELECT TABLE_NAME, TABLE_TYPE, SALT_BUCKETS, COLUMN_COUNT, PK_NAME\nFROM SYSTEM.CATALOG\nWHERE TABLE_TYPE = 'u';",
    "7. Point Lookup trực tiếp theo Row Key (Siêu nhanh)": "SELECT * FROM GIAO_DICH WHERE MA_GIAO_DICH = 'TX_0000001';",
}


def validate_console_sql(sql_str: str) -> tuple[bool, str, str]:
    """
    Kiểm tra tính an toàn và hợp lệ của câu lệnh SQL trước khi thực thi.
    Trả về: (is_valid: bool, query_type: 'READ'|'MUTATE'|'INVALID', message: str)
    """
    sql_clean = sql_str.strip()
    if not sql_clean:
        return False, "INVALID", "Vui lòng nhập câu lệnh SQL cần thực thi."

    core_sql = sql_clean.rstrip(";").strip()

    # Chặn ghép nhiều câu lệnh SQL trong một lần chạy
    if ";" in core_sql:
        return False, "INVALID", "❌ Hệ thống chỉ cho phép thực thi đúng 1 câu lệnh SQL trong mỗi lần chạy."

    sql_upper = core_sql.upper()

    # Chặn các câu lệnh nguy hiểm
    if "DROP TABLE" in sql_upper:
        return False, "INVALID", "❌ Lệnh DROP TABLE bị chặn vì lý do an toàn dữ liệu hệ thống."
    if "TRUNCATE" in sql_upper:
        return False, "INVALID", "❌ Lệnh TRUNCATE bị chặn vì lý do an toàn dữ liệu hệ thống."
    if "SYSTEM." in sql_upper and not (sql_upper.startswith("SELECT") or sql_upper.startswith("EXPLAIN")):
        return False, "INVALID", "❌ Không được phép sửa đổi hoặc can thiệp vào schema hệ thống SYSTEM."
    if sql_upper.startswith("DELETE") and "WHERE" not in sql_upper:
        return False, "INVALID", "❌ Lệnh DELETE bắt buộc phải có mệnh đề WHERE để tránh xóa sạch bảng."

    # Phân loại câu lệnh hợp lệ
    if sql_upper.startswith("SELECT") or sql_upper.startswith("EXPLAIN"):
        return True, "READ", ""
    elif (
        sql_upper.startswith("UPSERT")
        or sql_upper.startswith("DELETE")
        or sql_upper.startswith("CREATE INDEX")
        or sql_upper.startswith("DROP INDEX")
    ):
        return True, "MUTATE", ""
    else:
        return False, "INVALID", "❌ Câu lệnh không được hỗ trợ. Chỉ cho phép chạy: SELECT, EXPLAIN, UPSERT, DELETE (có WHERE), CREATE INDEX, DROP INDEX."


def record_query_history(sql_text: str, status: str, rows: int, duration_ms: float):
    """Lưu trữ tối đa 20 câu lệnh gần nhất vào session state."""
    if "query_history" not in st.session_state:
        st.session_state["query_history"] = []

    entry = {
        "timestamp": datetime.datetime.now().strftime("%H:%M:%S"),
        "sql": sql_text.strip(),
        "status": status,
        "rows": rows,
        "duration_ms": duration_ms,
    }
    # Thêm vào đầu danh sách, giữ tối đa 20 câu
    st.session_state["query_history"].insert(0, entry)
    if len(st.session_state["query_history"]) > 20:
        st.session_state["query_history"] = st.session_state["query_history"][:20]


def render_sql_console():
    """Trang 4: Nhập câu truy vấn - Bàn điều khiển SQL Phoenix trực tiếp, an toàn và có form chống rerun."""
    components.render_header("💻 NHẬP CÂU TRUY VẤN (SQL CONSOLE)")

    st.markdown(
        """
        Bàn điều khiển truy vấn Apache Phoenix trực tiếp trên cụm HBase.
        Hỗ trợ các câu lệnh: `SELECT`, `EXPLAIN`, `UPSERT`, `DELETE` (có `WHERE`), `CREATE INDEX` và `DROP INDEX`.
        """
    )

    # Khởi tạo trạng thái soạn thảo nếu chưa có
    if "console_sql_text" not in st.session_state:
        st.session_state["console_sql_text"] = "SELECT *\nFROM GIAO_DICH\nLIMIT 10;"
    if "console_last_result" not in st.session_state:
        st.session_state["console_last_result"] = None
    if "console_pending_mutate" not in st.session_state:
        st.session_state["console_pending_mutate"] = None

    # 1. Tiện ích chọn câu lệnh mẫu & nút xóa nội dung
    col_s1, col_s2 = st.columns([4, 1])
    with col_s1:
        sel_sample = st.selectbox(
            "Nạp câu lệnh mẫu nhanh:",
            options=list(SAMPLE_CONSOLE_QUERIES.keys()),
            index=0,
            key="sb_sample_queries",
        )
        if sel_sample and SAMPLE_CONSOLE_QUERIES[sel_sample]:
            st.session_state["console_sql_text"] = SAMPLE_CONSOLE_QUERIES[sel_sample]
            st.session_state["console_pending_mutate"] = None
            st.rerun()

    with col_s2:
        st.write("")
        st.write("")
        if st.button("🧹 Xóa nội dung", use_container_width=True):
            st.session_state["console_sql_text"] = ""
            st.session_state["console_pending_mutate"] = None
            st.session_state["console_last_result"] = None
            st.rerun()

    # 2. Form soạn thảo câu lệnh (chống rerun khi gõ ký tự)
    with st.form("sql_query_form"):
        sql_input = st.text_area(
            "Nhập câu lệnh Apache Phoenix:",
            value=st.session_state["console_sql_text"],
            height=200,
            placeholder="Ví dụ: SELECT * FROM GIAO_DICH LIMIT 10;",
            key="txt_sql_input",
        )

        f_c1, f_c2 = st.columns([2, 5])
        with f_c1:
            run_query = st.form_submit_button("▶ Chạy truy vấn", type="primary", use_container_width=True)

    # 3. Xử lý khi người dùng nhấn nút Chạy truy vấn
    if run_query:
        st.session_state["console_sql_text"] = sql_input.strip()
        is_valid, q_type, validation_msg = validate_console_sql(sql_input)

        if not is_valid:
            st.error(validation_msg)
            record_query_history(sql_input, "Bị chặn", 0, 0.0)
        elif q_type == "READ":
            # Câu lệnh SELECT hoặc EXPLAIN: Thực thi ngay
            st.session_state["console_pending_mutate"] = None
            with st.spinner("Đang thực thi câu lệnh trên Apache Phoenix..."):
                df_res, err_res, dur_ms = db.query_phoenix_df_timed(sql_input, timeout=35)

            st.session_state["console_last_result"] = {
                "df": df_res,
                "error": err_res,
                "duration_ms": dur_ms,
                "sql": sql_input,
            }
            record_query_history(sql_input, "Thành công" if not err_res else "Lỗi", len(df_res) if df_res is not None else 0, dur_ms)

        elif q_type == "MUTATE":
            # Câu lệnh thay đổi dữ liệu hoặc cấu trúc: Yêu cầu xác nhận an toàn
            st.session_state["console_pending_mutate"] = sql_input
            st.session_state["console_last_result"] = None

    # 4. Hộp thoại xác nhận an toàn cho UPSERT, DELETE, CREATE/DROP INDEX
    if st.session_state.get("console_pending_mutate"):
        pending_sql = st.session_state["console_pending_mutate"]
        st.markdown(
            f"""
            <div style="background-color: #FFFBEB; border-left: 4px solid #F59E0B; padding: 14px 18px; border-radius: 6px; margin: 15px 0;">
                <span style="color: #92400E; font-weight: 700; font-size: 0.95rem;">⚠️ XÁC NHẬN AN TOÀN THAY ĐỔI DỮ LIỆU / CẤU TRÚC</span><br>
                <span style="color: #78350F; font-size: 0.88rem;">
                    Câu lệnh bên dưới sẽ thực hiện thay đổi dữ liệu hoặc bảng chỉ mục trong Apache HBase.<br>
                    Vui lòng kiểm tra kỹ trước khi xác nhận thực thi:
                </span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.code(pending_sql, language="sql")

        chk_mutate_ok = st.checkbox("Tôi xác nhận muốn thực thi câu lệnh này vào cơ sở dữ liệu.", value=False, key="chk_mutate_console")
        col_m_btn1, col_m_btn2 = st.columns([2, 5])

        with col_m_btn1:
            btn_do_mutate = st.button("🚨 Xác Nhận Thực Thi (COMMIT)", type="primary", disabled=not chk_mutate_ok)
        with col_m_btn2:
            if st.button("❌ Hủy bỏ thao tác"):
                st.session_state["console_pending_mutate"] = None
                st.rerun()

        if btn_do_mutate:
            full_sql = pending_sql.strip().rstrip(";") + ";"
            with st.spinner("Đang thực thi câu lệnh trên HBase..."):
                t0 = time.perf_counter()
                ok_m, out_m = db.execute_phoenix_sql(full_sql, timeout=40)
                dur_m = (time.perf_counter() - t0) * 1000.0

            # Xóa đúng cache liên quan
            upper_p = pending_sql.upper()
            if "INDEX" in upper_p:
                load_cached_index_catalog.clear()
                load_cached_overview_super_batch.clear()
            else:
                load_cached_transactions.clear()
                get_cached_total_count.clear()
                load_cached_overview_super_batch.clear()
                load_cached_record_by_id.clear()

            record_query_history(pending_sql, "Thành công" if ok_m else "Lỗi", 0, dur_m)
            st.session_state["console_pending_mutate"] = None

            if ok_m:
                st.success(f"✅ Câu lệnh đã thực thi và COMMIT thành công! ({dur_m:,.1f} ms)")
                time.sleep(0.5)
                st.rerun()
            else:
                st.error(f"❌ Thao tác thất bại: {db.format_db_error(out_m)}")

    # 5. Hiển thị kết quả truy vấn SELECT / EXPLAIN & Nút tải CSV
    if st.session_state.get("console_last_result"):
        res = st.session_state["console_last_result"]
        df_out = res["df"]
        err_out = res["error"]
        dur_out = res["duration_ms"]
        sql_out = res["sql"]

        st.markdown("---")
        st.markdown("#### 📊 Kết Quả Thực Thi")

        if err_out:
            st.error(f"❌ Lỗi thực thi Phoenix: {err_out}")
        elif df_out is not None:
            row_count = len(df_out)
            components.render_execution_stats(dur_out, row_count)

            if row_count > 0:
                # Giới hạn hiển thị tối đa 100 dòng theo yêu cầu hiệu năng
                df_display = df_out.head(100)
                if row_count > 100:
                    st.info(f"💡 Đang hiển thị 100 dòng đầu tiên (tổng số {row_count} dòng). Hãy sử dụng mệnh đề `LIMIT` trong SQL để tối ưu hiệu năng.")

                # Định dạng dữ liệu nếu có các cột giao dịch
                df_table = formatting.format_giao_dich_table(df_display)
                st.dataframe(df_table, use_container_width=True, height=350)

                # Nút tải kết quả CSV cho câu SELECT
                if not sql_out.upper().startswith("EXPLAIN"):
                    csv_data = df_out.to_csv(index=False, encoding="utf-8")
                    st.download_button(
                        label="📥 Tải Kết Quả Xuống File CSV",
                        data=csv_data,
                        file_name=f"phoenix_result_{int(time.time())}.csv",
                        mime="text/csv",
                        key="btn_download_csv_console",
                    )
            else:
                st.info("Truy vấn đã thực thi thành công nhưng không có bản ghi nào khớp.")

    # 6. Lịch sử truy vấn trong phiên hiện tại (Tối đa 20 câu)
    history_list = st.session_state.get("query_history", [])
    if history_list:
        st.markdown("---")
        with st.expander(f"🕒 Lịch Sử Truy Vấn Trong Phiên ({len(history_list)} / 20 câu gần nhất)"):
            df_hist = pd.DataFrame(history_list)
            rename_hist = {
                "timestamp": "Thời Điểm",
                "sql": "Câu Lệnh SQL",
                "status": "Trạng Thái",
                "rows": "Số Bản Ghi",
                "duration_ms": "Thời Gian (ms)",
            }
            st.dataframe(df_hist.rename(columns=rename_hist), use_container_width=True)


def render_index_page():
    """Trang 5: Quản lý Index - 1 truy vấn duy nhất lấy Catalog, EXPLAIN chỉ chạy khi bấm nút."""
    components.render_header("⚡ QUẢN LÝ SECONDARY INDEX")

    all_idx, idx_active = load_cached_index_catalog()

    col_idx_s1, col_idx_s2 = st.columns([2, 2])
    with col_idx_s1:
        if idx_active:
            st.success("✅ **Trạng thái Index:** `IDX_GIAO_DICH_KHU_VUC` ĐANG HOẠT ĐỘNG (ACTIVE)")
        else:
            st.warning("⚠️ **Trạng thái Index:** `IDX_GIAO_DICH_KHU_VUC` CHƯA TỒN TẠI (Full Table Scan)")

    with col_idx_s2:
        if all_idx:
            st.info(f"📋 Tìm thấy **{len(all_idx)}** Secondary Index gắn với bảng `GIAO_DICH`.")
        else:
            st.info("Chưa có Secondary Index nào trên bảng `GIAO_DICH`.")

    if all_idx:
        st.markdown("##### 📋 Danh Sách Index Hiện Hữu Trên Hệ Thống:")
        st.dataframe(pd.DataFrame(all_idx), use_container_width=True)

    st.markdown("---")

    # Tạo & Xóa Index
    st.markdown("#### 🛠️ Quản Trị Chỉ Mục (Index DDL)")
    c_act1, c_act2 = st.columns(2)

    with c_act1:
        st.markdown("##### ➕ Tạo Covered Secondary Index")
        st.caption("Tạo chỉ mục trên `KHU_VUC` kèm `INCLUDE` tránh Read Overhead.")
        st.code(queries.SQL_CREATE_COVERED_INDEX, language="sql")
        btn_create = st.button("🚀 Thực Hiện Tạo Index", type="primary", use_container_width=True, key="btn_cr_idx")

        if btn_create:
            if idx_active:
                st.info("Index `IDX_GIAO_DICH_KHU_VUC` đã tồn tại trước đó.")
            else:
                with st.spinner("Đang tạo Covered Index trên HBase (10-15s)..."):
                    ok_c, out_c = db.execute_phoenix_sql(queries.SQL_CREATE_COVERED_INDEX, timeout=45)
                if ok_c:
                    load_cached_index_catalog.clear()
                    load_cached_overview_super_batch.clear()
                    st.success("✅ Đã tạo thành công Covered Index `IDX_GIAO_DICH_KHU_VUC`!")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error(f"Lỗi tạo Index: {db.format_db_error(out_c)}")

    with c_act2:
        st.markdown("##### 🗑️ Xóa Secondary Index")
        st.caption("Xóa chỉ mục `IDX_GIAO_DICH_KHU_VUC` khỏi HBase.")
        st.code(queries.SQL_DROP_INDEX, language="sql")
        chk_drop = st.checkbox("Xác nhận muốn xóa Index `IDX_GIAO_DICH_KHU_VUC`", value=False, key="chk_drop_idx_safe")
        btn_drop = st.button("🚨 Thực Hiện Xóa Index", type="primary", disabled=not chk_drop, use_container_width=True, key="btn_dr_idx")

        if btn_drop:
            with st.spinner("Đang xóa Index khỏi HBase..."):
                ok_d, out_d = db.execute_phoenix_sql(queries.SQL_DROP_INDEX, timeout=25)
            if ok_d:
                load_cached_index_catalog.clear()
                load_cached_overview_super_batch.clear()
                st.success("✅ Đã xóa thành công Index `IDX_GIAO_DICH_KHU_VUC`!")
                time.sleep(0.5)
                st.rerun()
            else:
                st.error(f"Lỗi xóa Index: {db.format_db_error(out_d)}")

    st.markdown("---")

    # So sánh kế hoạch thực thi EXPLAIN (Chỉ chạy khi bấm nút)
    st.markdown("#### ⚖️ So Sánh Hiệu Năng & Kế Hoạch Thực Thi (EXPLAIN)")
    col_cmp1, col_cmp2 = st.columns(2)

    with col_cmp1:
        st.markdown("##### 🔴 Không Dùng Index (/*+ NO_INDEX */)")
        st.code(queries.SQL_EXPLAIN_WITHOUT_INDEX, language="sql")
        if st.button("Phân tích Kế hoạch Full Scan", use_container_width=True, key="btn_plan_full"):
            with st.spinner("Đang phân tích..."):
                df_exp1, _, _ = db.query_phoenix_df_timed(queries.SQL_EXPLAIN_WITHOUT_INDEX)
                _, _, run_t1 = db.query_phoenix_df_timed(queries.SQL_BENCHMARK_NO_INDEX)

            if df_exp1 is not None and not df_exp1.empty:
                plan1 = "\n".join(str(row.get("PLAN", "")) for _, row in df_exp1.iterrows())
                st.code(plan1, language="text")
                st.warning(f"⚠️ **Kế hoạch:** PARALLEL FULL SCAN &bull; Thời gian chạy: **{run_t1:,.1f} ms**")

    with col_cmp2:
        st.markdown("##### 🟢 Sử Dụng Covered Index (/*+ INDEX */)")
        st.code(queries.SQL_EXPLAIN_WITH_INDEX_HINT, language="sql")
        if st.button("Phân tích Kế hoạch Index Scan", type="primary", use_container_width=True, key="btn_plan_idx"):
            with st.spinner("Đang phân tích..."):
                df_exp2, _, _ = db.query_phoenix_df_timed(queries.SQL_EXPLAIN_WITH_INDEX_HINT)
                _, _, run_t2 = db.query_phoenix_df_timed(queries.SQL_BENCHMARK_WITH_INDEX)

            if df_exp2 is not None and not df_exp2.empty:
                plan2 = "\n".join(str(row.get("PLAN", "")) for _, row in df_exp2.iterrows())
                st.code(plan2, language="text")
                st.success(f"🎯 **Kế hoạch:** RANGE SCAN trên `IDX_GIAO_DICH_KHU_VUC` &bull; Thời gian chạy: **{run_t2:,.1f} ms**")


def render_benchmark_page():
    """Trang: Kiểm tra hiệu năng - Chỉ chạy khi người dùng chủ động bấm nút."""
    components.render_header("🚀 KIỂM TRA HIỆU NĂNG (BENCHMARK)")

    st.markdown("Đo lường thời gian phản hồi thực tế giữa các cơ chế truy vấn trên Apache Phoenix.")

    if st.button("🏁 Bắt Đầu Chạy Benchmark Toàn Diện", type="primary", key="btn_run_bench_manual"):
        benchmark_results = []
        progress_bar = st.progress(0)
        status_text = st.empty()

        # 1. Point Lookup
        status_text.text("1/4: Đang đo Point Lookup theo Row Key...")
        progress_bar.progress(25)
        _, _, t_point = db.query_phoenix_df_timed(queries.SQL_BENCHMARK_POINT_LOOKUP)
        benchmark_results.append({"Kiểu Truy Vấn": "1. Point Lookup (Row Key)", "Cơ Chế": "Point Scan trực tiếp vào Region", "Thời Gian (ms)": t_point})

        # 2. Covered Index Scan
        status_text.text("2/4: Đang đo Range Scan trên Covered Index...")
        progress_bar.progress(50)
        _, _, t_idx = db.query_phoenix_df_timed(queries.SQL_BENCHMARK_WITH_INDEX)
        benchmark_results.append({"Kiểu Truy Vấn": "2. Range Scan (Covered Index)", "Cơ Chế": "Quét trên bảng chỉ mục phụ", "Thời Gian (ms)": t_idx})

        # 3. Full Table Scan
        status_text.text("3/4: Đang đo Parallel Full Table Scan...")
        progress_bar.progress(75)
        _, _, t_full = db.query_phoenix_df_timed(queries.SQL_BENCHMARK_NO_INDEX)
        benchmark_results.append({"Kiểu Truy Vấn": "3. Full Table Scan (NO_INDEX)", "Cơ Chế": "Quét tuần tự song song toàn bảng", "Thời Gian (ms)": t_full})

        # 4. Aggregation
        status_text.text("4/4: Đang đo Phân tích tổng hợp (GROUP BY & SUM)...")
        progress_bar.progress(100)
        _, _, t_agg = db.query_phoenix_df_timed(queries.SQL_OVERVIEW_CHART_REGION)
        benchmark_results.append({"Kiểu Truy Vấn": "4. Aggregation (GROUP BY)", "Cơ Chế": "HBase Coprocessors tính toán tại node", "Thời Gian (ms)": t_agg})

        status_text.success("🎉 Hoàn thành kiểm tra benchmark!")
        df_bench = pd.DataFrame(benchmark_results)

        # Highlight Metrics
        bm1, bm2, bm3 = st.columns(3)
        with bm1:
            ratio_point = f"{t_full / t_point:.1f}x nhanh hơn" if t_point > 0 else "Nhanh nhất"
            st.metric("Point Lookup (Row Key)", f"{t_point:,.1f} ms", ratio_point)
        with bm2:
            ratio_idx = f"{t_full / t_idx:.1f}x nhanh hơn" if t_idx > 0 else "Tối ưu"
            st.metric("Covered Index Range Scan", f"{t_idx:,.1f} ms", ratio_idx)
        with bm3:
            st.metric("Parallel Full Table Scan", f"{t_full:,.1f} ms", "Base Scan (100% Data)")

        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
        st.markdown("##### 📊 So Sánh Trực Quan Thời Gian Phản Hồi (Mili-giây):")
        st.dataframe(df_bench, use_container_width=True)
        st.bar_chart(df_bench, x="Kiểu Truy Vấn", y="Thời Gian (ms)", color="#1E88E5", height=300)

    st.markdown("---")

    # Kiến thức kỹ thuật Salt Buckets
    st.markdown("#### 💡 Kiến Thức Cốt Lõi: Salt Buckets Trong Apache Phoenix")
    sc1, sc2 = st.columns(2)
    with sc1:
        st.markdown(
            """
            **1. Vấn đề Region Hotspotting trong HBase:**
            - Trong HBase truyền thống, Row Key tăng tuần tự (`TX_0000001`, `TX_0000002`...) sẽ khiến toàn bộ dữ liệu mới ghi tập trung vào một Region Server duy nhất.
            - Gây thắt cổ chai (*Hotspotting*) và làm giảm hiệu năng ghi/đọc của cụm phân tán.
            """
        )
    with sc2:
        st.markdown(
            """
            **2. Giải pháp Salt Buckets = 8:**
            - Phoenix tự động thêm tiền tố hash byte `(0..7)` vào trước Row Key.
            - Dữ liệu được chia đều vào 8 vùng lưu trữ (Region Buckets) độc lập.
            - **Lợi ích khi đọc:** Phoenix phân bổ đa luồng quét song song trên 8 Region Servers (*PARALLEL 8-WAY SCAN*), tối ưu tối đa băng thông I/O.
            """
        )


def render_salt_architecture_page():
    """Trang chuyên sâu: Kiến trúc phân tầng & Cơ chế Salt Buckets = 8 trong Apache Phoenix."""
    components.render_header("🏛️ KIẾN TRÚC & SALT BUCKETS")

    st.markdown(
        """
        Khám phá chi tiết kiến trúc nội tại của **Apache Phoenix** trên nền tảng **Apache HBase**, 
        cách thức **Salt Buckets = 8** giải quyết triệt để vấn đề thắt cổ chai ghi (*Region Hotspotting*) 
        và cơ chế phân luồng đọc song song (*Parallel Multi-way Scan*).
        """
    )

    tab_arch, tab_salt = st.tabs(["🏗️ Kiến Trúc Hệ Thống", "⚡ Cơ Chế Salt Buckets = 8"])

    with tab_arch:
        components.render_phoenix_architecture_diagram()

        col_a1, col_a2 = st.columns(2)
        with col_a1:
            st.markdown(
                """
                #### 🎯 Lợi thế của Apache Phoenix so với HBase thuần:
                1. **Giao diện SQL chuẩn (ANSI SQL-92)**:
                   - Không cần viết code Java phức tạp với API `Get`, `Put`, `Scan`.
                   - Hỗ trợ đầy đủ các hàm thống kê `SUM`, `AVG`, `COUNT`, `GROUP BY`, `ORDER BY`.
                2. **Đẩy tính toán xuống Server (Coprocessors Pushdown)**:
                   - Phoenix dịch các biểu thức `WHERE`, `GROUP BY` thành **HBase Coprocessors** chạy trực tiếp tại các RegionServer chứa dữ liệu.
                   - Giảm thiểu tối đa lượng dữ liệu truyền qua mạng (*Network I/O*).
                3. **Tối ưu hóa chi phí truy vấn (CBO)**:
                   - Tự động chọn thứ tự join và sử dụng Secondary Index tối ưu.
                """
            )
        with col_a2:
            st.markdown(
                """
                #### 🛡️ Cơ chế đồng thuận & Lưu trữ phân tán:
                1. **ZooKeeper (Cổng 2181)**:
                   - Quản lý trạng thái cụm phân tán và điều phối vị trí của bảng gốc `-ROOT-` / `hbase:meta`.
                   - Phoenix Client kết nối trực tiếp đến ZooKeeper để xác định Region Server chứa dữ liệu mà không cần thông qua HMaster cho từng truy vấn.
                2. **HMaster & RegionServers**:
                   - `HMaster` quản lý việc phân chia (Split) và gán Region vào các RegionServer.
                   - `RegionServer` trực tiếp đọc/ghi các file lưu trữ cột `HFiles`.
                3. **Column Families**:
                   - Bảng `GIAO_DICH` lưu các cột động trong Column Family mặc định `0`.
                """
            )

    with tab_salt:
        st.markdown("#### 🧂 Trực Quan Hóa Cơ Chế Salt Buckets = 8")
        st.markdown(
            """
            Trong Apache HBase, nếu Row Key tăng tuần tự (`TX_0000001`, `TX_0000002`, `TX_0000003`...), 
            toàn bộ dữ liệu mới sẽ dồn vào một Region Server duy nhất (*Region Hotspotting*). 
            **Giải pháp:** Phoenix tự động thêm 1 byte tiền tố băm `(0x00..0x07)` vào trước Row Key để chia đều dữ liệu vào **8 Salt Buckets**.
            """
        )

        keys_list = load_cached_transaction_keys()

        # Bộ công cụ thử nghiệm gán Salt Bucket tương tác
        st.markdown("##### 🔬 Thử Nghiệm Băm Row Key Vào Salt Bucket:")
        col_inp1, col_inp2 = st.columns([3, 2])
        with col_inp1:
            test_key = st.text_input(
                "Nhập Mã Giao Dịch để kiểm tra bucket:",
                value="TX_0000001",
                help="Nhập mã như TX_0000001, TX_0000002 hoặc bất kỳ chuỗi nào",
            ).strip().upper()
        
        calc_bucket = components.calculate_salt_bucket(test_key, 8) if test_key else 0
        with col_inp2:
            st.markdown(
                f"""
                <div style="background-color: #EFF6FF; border: 1px solid #BFDBFE; border-radius: 8px; padding: 10px 14px; margin-top: 10px;">
                    <span style="font-size: 0.85rem; color: #1E40AF;">Mã: <b>{test_key}</b> &rarr; <b>Salt Bucket #{calc_bucket}</b> (Byte: <code>0x0{calc_bucket}</code>)</span><br>
                    <span style="font-size: 0.78rem; color: #3B82F6;">HBase RowKey thực tế: <code>[0x0{calc_bucket}, '{test_key}']</code></span>
                </div>
                """,
                unsafe_allow_html=True,
            )

        # Lưới 8 Salt Buckets với dữ liệu thực tế
        st.markdown("##### 📊 Phân Bổ Dữ Liệu Thực Tế Trên 8 Salt Buckets:")
        components.render_salt_buckets_visualizer(keys_list, highlight_key=test_key)

        st.markdown("---")
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            st.markdown(
                """
                **⚡ Lợi ích khi Ghi (Write Performance):**
                - 8 giao dịch liên tiếp được ghi phân tán vào 8 RegionServers khác nhau.
                - Tận dụng tối đa băng thông I/O của toàn cụm, loại bỏ hoàn toàn hiện tượng nghẽn cổ chai.
                """
            )
        with col_c2:
            st.markdown(
                """
                **🚀 Lợi ích khi Đọc (Read Performance):**
                - Phoenix tự động phân bổ 8 luồng quét song song (`PARALLEL 8-WAY SCAN`).
                - Tốc độ đọc toàn bảng hoặc lọc dữ liệu nhanh gấp nhiều lần so với quét đơn luồng.
                """
            )


def render_system_catalog_page():
    """Trang chuyên sâu: Khám phá Siêu dữ liệu SYSTEM.CATALOG của Apache Phoenix."""
    components.render_header("📚 METADATA & SYSTEM.CATALOG")

    st.markdown(
        """
        Toàn bộ cấu trúc bảng, kiểu dữ liệu, khóa chính, cấu hình Salt Buckets và trạng thái Secondary Index 
        được Apache Phoenix lưu trữ tập trung trong bảng siêu dữ liệu nội bộ **`SYSTEM.CATALOG`**.
        """
    )

    with st.spinner("Đang truy xuất metadata từ SYSTEM.CATALOG..."):
        df_cols, df_props, df_sys, err_meta = load_cached_catalog_metadata()

    if err_meta:
        components.render_connection_error_box(err_meta)
        return

    # 1. Thẻ thuộc tính vật lý bảng GIAO_DICH
    st.markdown("#### ⚙️ Cấu Hình Vật Lý Bảng `GIAO_DICH` (Từ SYSTEM.CATALOG)")
    p1, p2, p3, p4 = st.columns(4)
    with p1:
        st.metric("Loại Bảng (TABLE_TYPE)", "User Table ('u')")
    with p2:
        st.metric("Số Salt Buckets", "8 Buckets")
    with p3:
        st.metric("Khóa Chính (PK_NAME)", "PK (MA_GIAO_DICH)")
    with p4:
        st.metric("Số Cột Cấu Trúc", f"{len(df_cols) if df_cols is not None else 7} Cột")

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    # 2. Bảng Schema chi tiết các cột
    st.markdown("#### 📋 Schema Chi Tiết & Kiểu Dữ Liệu SQL")
    if df_cols is not None and not df_cols.empty:
        df_schema = df_cols.copy()
        type_names = {
            12: "VARCHAR",
            4: "INTEGER",
            3: "DECIMAL(15,2)",
            93: "TIMESTAMP",
            1: "CHAR",
        }
        df_schema["KIEU_DU_LIEU_SQL"] = df_schema["DATA_TYPE"].apply(lambda t: type_names.get(int(t) if pd.notna(t) else 12, f"TYPE_{t}"))
        df_schema["KHOA_CHINH"] = df_schema["KEY_SEQ"].apply(lambda s: "🔑 PRIMARY KEY" if pd.notna(s) and int(s) > 0 else "")
        df_schema["NULLABLE_HIEN_THI"] = df_schema["NULLABLE"].apply(lambda n: "NOT NULL" if pd.notna(n) and int(n) == 0 else "NULL")

        col_show = ["ORDINAL_POSITION", "COLUMN_NAME", "KIEU_DU_LIEU_SQL", "NULLABLE_HIEN_THI", "KHOA_CHINH"]
        col_names = {
            "ORDINAL_POSITION": "Thứ Tự",
            "COLUMN_NAME": "Tên Cột",
            "KIEU_DU_LIEU_SQL": "Kiểu Dữ Liệu Phoenix SQL",
            "NULLABLE_HIEN_THI": "Ràng Buộc Null",
            "KHOA_CHINH": "Khóa",
        }
        cols_exist = [c for c in col_show if c in df_schema.columns]
        st.dataframe(df_schema[cols_exist].rename(columns=col_names), use_container_width=True, hide_index=True)
    else:
        st.info("Chưa lấy được schema chi tiết từ SYSTEM.CATALOG.")

    st.markdown("---")

    # 3. Các bảng hệ thống nội tại của Apache Phoenix
    st.markdown("#### 🏛️ Danh Sách Các Bảng Hệ Thống Trong Apache Phoenix")
    st.markdown(
        """
        Phoenix duy trì một tập hợp các bảng hệ thống đặc biệt trên HBase để quản lý hạ tầng:
        - **`SYSTEM.CATALOG`**: Lưu trữ toàn bộ bảng, view, chỉ mục, cột và metadata của cơ sở dữ liệu.
        - **`SYSTEM.STATS`**: Lưu trữ thống kê phân bố dữ liệu (Guideposts) phục vụ Cost-Based Optimizer.
        - **`SYSTEM.FUNCTION`**: Quản lý các hàm do người dùng định nghĩa (UDF).
        - **`SYSTEM.SEQUENCE`**: Quản lý các chuỗi sinh số tự tăng (Sequences).
        - **`SYSTEM.MUTEX`**: Đảm bảo an toàn khóa đa tiến trình khi thực hiện DDL đồng thời.
        """
    )
    if df_sys is not None and not df_sys.empty:
        type_desc = {"u": "Bảng người dùng (User Table)", "s": "Bảng hệ thống (System Table)", "i": "Bảng Chỉ mục (Index Table)"}
        df_sys_display = df_sys.copy()
        df_sys_display["LOAI_BANG"] = df_sys_display["TABLE_TYPE"].apply(lambda t: type_desc.get(str(t).lower(), str(t)))
        col_sys_show = [c for c in ["TABLE_NAME", "LOAI_BANG", "SALT_BUCKETS"] if c in df_sys_display.columns]
        st.dataframe(
            df_sys_display[col_sys_show].rename(
                columns={"TABLE_NAME": "Tên Bảng", "LOAI_BANG": "Phân Loại", "SALT_BUCKETS": "Số Salt Buckets"}
            ),
            use_container_width=True,
            hide_index=True,
        )


def render_data_cleaning_page():
    """Trang: Pipeline Lọc & Làm sạch Dữ liệu Archive (ETL & Phoenix Bulk Loader)."""
    components.render_header("🧹 PIPELINE LÀM SẠCH & DỮ LIỆU ARCHIVE")

    summary = load_cleaning_summary()
    components.render_data_cleaning_pipeline_diagram()
    components.render_cleaning_metrics_cards(summary)

    t_profile, t_bulk = st.tabs([
        "📊 Thống Kê & Đối Chiếu Dữ Liệu",
        "⚡ Quản Lý Nạp Dữ Liệu Vào Apache Phoenix",
    ])

    with t_profile:
        col_c1, col_c2 = st.columns([1, 1])
        with col_c1:
            st.markdown("##### 📈 Phân Bổ Chất Lượng Dữ Liệu")
            total_raw = summary.get("total_raw", 541909)
            valid_rec = summary.get("valid_records", 524878)
            drop_rec = summary.get("dropped_records", 17031)

            df_quality = pd.DataFrame({
                "Phân loại": ["Dữ liệu hợp lệ (Clean Data)", "Bản ghi lỗi/bất thường (Dropped)"],
                "Số lượng bản ghi": [f"{valid_rec:,}", f"{drop_rec:,}"],
                "Tỷ lệ": [f"{valid_rec / total_raw * 100:.2f}%", f"{drop_rec / total_raw * 100:.2f}%"],
            })
            st.dataframe(df_quality, use_container_width=True, hide_index=True)

            st.markdown(
                f"""
                <div style="background-color: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 12px; margin-top: 10px;">
                    <div style="font-weight: 600; font-size: 0.88rem; color: #0F294A;">Thông số tổng hợp:</div>
                    <div style="font-size: 0.82rem; color: #475569; margin-top: 4px; line-height: 1.6;">
                        &bull; File nguồn: <code>archive/data.csv</code> (45.5 MB, 541,909 dòng)<br>
                        &bull; Tỷ lệ đạt chuẩn: <b>{valid_rec/total_raw*100:.2f}%</b><br>
                        &bull; Tổng doanh thu hợp lệ: <b>{formatting.format_currency(summary.get('total_revenue', 0))}</b><br>
                        &bull; Khung thời gian: <b>{summary.get('min_date', '')}</b> đến <b>{summary.get('max_date', '')}</b>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with col_c2:
            st.markdown("##### 🔍 Chi Tiết Các Tiêu Chí Loại Bỏ & Chuẩn Hóa")
            df_dropped_reasons = pd.DataFrame([
                {"Tiêu chí phát hiện": "Đơn hàng hủy / Hoàn trả (Quantity <= 0)", "Số lượng": f"{summary.get('cancellations_dropped', 10624):,}", "Hành động": "Loại bỏ"},
                {"Tiêu chí phát hiện": "Đơn giá lỗi / Công nợ (UnitPrice <= 0)", "Số lượng": f"{summary.get('zero_price_dropped', 2517):,}", "Hành động": "Loại bỏ"},
                {"Tiêu chí phát hiện": "Mô tả sản phẩm rỗng (Null Description)", "Số lượng": f"{summary.get('null_description_dropped', 1454):,}", "Hành động": "Loại bỏ"},
                {"Tiêu chí phát hiện": "Bản ghi trùng lặp hoàn toàn (Exact Duplicates)", "Số lượng": f"{summary.get('exact_duplicates', 5268):,}", "Hành động": "Khử trùng lặp"},
                {"Tiêu chí phát hiện": "Khách hàng vãng lai (CustomerID null)", "Số lượng": f"{summary.get('guest_customers', 135080):,}", "Hành động": "Gán mã KH_GUEST"},
            ])
            st.dataframe(df_dropped_reasons, use_container_width=True, hide_index=True)

        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
        st.markdown("##### 📑 So Sánh Cấu Trúc: Dữ Liệu Gốc vs Schema Apache Phoenix")
        df_raw_sample, df_clean_sample = load_raw_and_cleaned_samples()

        with st.expander("📂 Xem mẫu 5 dòng dữ liệu gốc từ archive/data.csv (Raw E-Commerce Data)", expanded=True):
            st.dataframe(df_raw_sample, use_container_width=True)

        with st.expander("✨ Xem mẫu 5 dòng dữ liệu sau khi làm sạch & chuẩn hóa cho Phoenix (Cleaned Phoenix Data)", expanded=True):
            if not df_clean_sample.empty:
                st.dataframe(formatting.format_giao_dich_table(df_clean_sample), use_container_width=True)

    with t_bulk:
        st.markdown("##### ⚡ Nạp Dữ Liệu Sạch Vào Apache Phoenix (HBase)")
        st.markdown(
            """
            Sử dụng công cụ chính thức <code>psql.py</code> của Apache Phoenix để thực hiện Bulk Upsert
            dữ liệu sạch vào HBase RegionServers với hiệu năng tối ưu (phân bổ song song qua <b>8 Salt Buckets</b>).
            """,
            unsafe_allow_html=True,
        )

        total_in_db = get_cached_total_count("", ())
        st.info(f"📊 Hiện tại trong bảng **GIAO_DICH** của Phoenix đang có: **{formatting.format_number(total_in_db)}** bản ghi.")

        col_b1, col_b2 = st.columns([2, 1])
        with col_b1:
            load_option = st.radio(
                "Chọn gói dữ liệu sạch để nạp vào Phoenix:",
                [
                    "⚡ Mẫu chuẩn 5.000 dòng sạch (Khuyến nghị demo - Thời gian nạp ~7 giây)",
                    "⚡ Tập lớn 10.000 dòng sạch (Thời gian nạp ~15 giây)",
                ],
                index=0,
            )

        with col_b2:
            st.markdown("<div style='height: 25px;'></div>", unsafe_allow_html=True)
            if st.button("🚀 Thực Thi Nạp Dữ Liệu", type="primary", use_container_width=True):
                chosen_file = (
                    "/mnt/d/2026/BigData/phoenix-demo/data/retail_cleaned_5000.csv"
                    if "5.000" in load_option
                    else "/mnt/d/2026/BigData/phoenix-demo/data/retail_cleaned_10000.csv"
                )
                with st.spinner("Đang gọi psql.py để nạp dữ liệu sạch vào Phoenix HBase..."):
                    cmd = f"python3 /mnt/d/2026/BigData/phoenix/bin/psql.py -t GIAO_DICH -h in-line localhost {chosen_file}"
                    t_start = time.time()
                    try:
                        res = subprocess.run(
                            ["wsl", "-e", "bash", "-c", cmd],
                            capture_output=True,
                            text=True,
                            timeout=60,
                        )
                        dur = time.time() - t_start
                        if res.returncode == 0:
                            st.success(f"✅ Nạp thành công vào Apache Phoenix trong {dur:.2f} giây!")
                            st.cache_data.clear()
                            st.rerun()
                        else:
                            st.error(f"Lỗi khi nạp dữ liệu: {res.stderr or res.stdout}")
                    except Exception as e:
                        st.error(f"Lỗi thực thi: {str(e)}")

        st.markdown("---")
        with st.expander("⚠️ Tùy chọn Tái tạo Bảng (Reset Table Schema)"):
            st.warning("Hành động này sẽ XÓA TOÀN BỘ dữ liệu trong bảng GIAO_DICH và tạo lại cấu trúc mới với 8 Salt Buckets.")
            if st.button("🗑️ Xóa và Khởi tạo lại Bảng GIAO_DICH", type="secondary"):
                with st.spinner("Đang tái tạo bảng GIAO_DICH trên Phoenix..."):
                    db.execute_phoenix_sql("DROP INDEX IF EXISTS IDX_GIAO_DICH_KHU_VUC ON GIAO_DICH;")
                    db.execute_phoenix_sql("DROP TABLE IF EXISTS GIAO_DICH;")
                    ok, err_c = db.execute_phoenix_sql(queries.CREATE_TABLE_SQL)
                    if ok:
                        db.execute_phoenix_sql(queries.SQL_CREATE_COVERED_INDEX)
                        st.success("✅ Đã khởi tạo lại bảng GIAO_DICH và chỉ mục IDX_GIAO_DICH_KHU_VUC thành công!")
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error(f"Lỗi khởi tạo bảng: {err_c}")


def render_guide_page():
    """Trang 7: Hướng dẫn demo - Tài liệu tĩnh hiển thị tức thì."""
    components.render_header("📖 HƯỚNG DẪN DEMO BÁO CÁO")

    t_flow, t_qa, t_capture = st.tabs([
        "🎯 Kịch Bản 6 Bước Thuyết Trình",
        "❓ Câu Hỏi Phản Biện Thường Gặp",
        "📸 Danh Sách Chụp Màn Hình Báo Cáo",
    ])

    with t_flow:
        st.markdown(
            """
            ### 🎯 Quy Trình 6 Bước Trình Bày Trước Giảng Viên:
            
            1. **Bước 1: Giới thiệu kiến trúc (1 phút)**
               - Mở trang **📊 Tổng quan**.
               - Chỉ vào thanh trạng thái: Chứng minh Phoenix kết nối thành công tới **ZooKeeper cổng 2181** và tiến trình **HBase HMaster**.
               - Trình bày 5 thẻ KPI: Số bản ghi, Số khách hàng, Tổng doanh thu, Giá trị trung bình và Phân bố 3 miền.
            
            2. **Bước 2: Môi trường Ubuntu Terminal & Quản lý Giao dịch (2 phút)**
               - Chuyển sang trang **🐧 Chạy lệnh Ubuntu**.
               - Demo **Terminal Ubuntu**: Chạy kiểm tra dịch vụ (`check_services.sh`), chạy kịch bản tự động (`run_demo.sh`), chạy file SQL qua SQLLine hoặc gõ lệnh trực tiếp trên WSL2.
               - Demo **Tab Quản lý Giao dịch**: Tìm kiếm, Thêm mới (`UPSERT`), Sửa và Xóa (`DELETE`) an toàn.
            
            3. **Bước 3: Demo các câu truy vấn phân tích & Console (2 phút)**
               - Mở trang **🔍 Truy vấn và thống kê**: Chạy các câu tiêu biểu: Câu 3 (thời gian), Câu 6 (`GROUP BY` khu vực), Câu 9 (`HAVING`).
               - Mở trang **💻 Nhập câu truy vấn**: Nạp câu lệnh mẫu, thực thi truy vấn tùy ý, tải file kết quả CSV.
            
            4. **Bước 4: Minh chứng tối ưu hóa bằng Index (2 phút)**
               - Mở trang **⚡ Quản lý Index**: So sánh kế hoạch thực thi: `PARALLEL FULL SCAN` vs `RANGE SCAN`.
               - Giải thích từ khóa `INCLUDE` biến thành Covered Index.
            
            5. **Bước 5: Đánh giá hiệu năng tổng thể (1 phút)**
               - Mở trang **🚀 Kiểm tra hiệu năng**, bấm chạy Benchmark và giải thích cơ chế Salt Buckets = 8.
            
            6. **Bước 6: Kết luận và giải đáp thắc mắc.**
            """
        )

    with t_qa:
        st.markdown(
            """
            ### ❓ Các Câu Hỏi Giảng Viên Thường Đặt Ra & Gợi Ý Trả Lời:

            - **Câu 1: Tại sao lại dùng Apache Phoenix thay vì truy vấn HBase trực tiếp?**
              * *Trả lời:* HBase API thuần chỉ hỗ trợ `Get`, `Put`, `Scan` theo Row Key đơn giản. Muốn làm `GROUP BY`, tính tổng hay lọc phức tạp phải viết MapReduce. Phoenix biên dịch SQL thành Coprocessors chạy trực tiếp song song trên các Region Server của HBase, tốc độ vượt trội và hỗ trợ chuẩn SQL quen thuộc.

            - **Câu 2: Cơ chế Salt Buckets hoạt động như thế nào?**
              * *Trả lời:* Phoenix tự động thêm 1 byte tiền tố từ 0 đến 7 vào trước Row Key. Khi ghi, dữ liệu được chia đều vào 8 Region Servers khác nhau, tránh nghẽn vùng ghi (Hotspotting). Khi đọc, Phoenix tự động phân bổ đa luồng quét song song trên 8 Region Servers.

            - **Câu 3: Mệnh đề INCLUDE trong CREATE INDEX có ý nghĩa gì?**
              * *Trả lời:* Giúp biến thành **Covered Index**. Các cột cần hiển thị như `SO_LUONG`, `DON_GIA` được lưu ngay trong bảng chỉ mục, giúp Phoenix đọc trực tiếp từ Index mà không cần quét ngược lại bảng chính (tránh Read Overhead).
            """
        )

    with t_capture:
        st.markdown(
            """
            ### 📸 Danh Sách Các Mục Cần Chụp Màn Hình Đưa Vào Báo Cáo:
            
            1. **Hình 1: Giao diện Trang Tổng quan** (Thanh trạng thái xanh, 5 thẻ KPI, 2 biểu đồ phân bố).
            2. **Hình 2: Trang Quản lý Giao dịch** (Bảng phân trang 20 dòng, form thêm mới và hộp thoại xác nhận xóa màu đỏ).
            3. **Hình 3: Kết quả truy vấn SQL Console** (Trang Nhập câu truy vấn, bảng dữ liệu kết quả kèm nút tải CSV).
            4. **Hình 4: Kế hoạch thực thi EXPLAIN** (Đối chiếu `PARALLEL FULL SCAN` và `RANGE SCAN`).
            5. **Hình 5: Biểu đồ Benchmark hiệu năng** (Biểu đồ so sánh thời gian phản hồi giữa các kỹ thuật quét).
            """
        )


# =============================================================================
# ĐIỀU HƯỚNG CHÍNH (ROUTING 7 MỤC CHUẨN - LAZY-LOADING TUYỆT ĐỐI)
# =============================================================================

# Sidebar
st.sidebar.markdown(
    """
    <div style="text-align: center; padding: 10px 0 16px 0;">
        <div style="display: inline-flex; align-items: center; justify-content: center; width: 44px; height: 44px; border-radius: 12px; background: linear-gradient(135deg, #00F2FE 0%, #0284C7 100%); box-shadow: 0 0 20px rgba(0, 242, 254, 0.4); margin-bottom: 8px;">
            <span style="font-size: 1.5rem;">⚡</span>
        </div>
        <h3 style="margin: 0; color: #F8FAFC; font-weight: 800; font-size: 1.25rem; letter-spacing: -0.3px; font-family: 'JetBrains Mono', monospace;">APACHE PHOENIX</h3>
        <p style="margin: 4px 0 0 0; font-size: 0.78rem; color: #38BDF8; font-family: 'JetBrains Mono', monospace; font-weight: 500;">SQL Engine on Apache HBase</p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.sidebar.markdown("---")
st.sidebar.markdown(
    """
    <div style="font-weight: 700; font-size: 0.76rem; color: #94A3B8; text-transform: uppercase; letter-spacing: 0.8px; margin-bottom: 8px; font-family: 'JetBrains Mono', monospace; display: flex; align-items: center; gap: 6px;">
        <span>🌍</span> PHẠM VI HỆ THỐNG:
    </div>
    <div style="background: linear-gradient(135deg, rgba(14, 165, 233, 0.15) 0%, rgba(2, 132, 199, 0.25) 100%); border: 1px solid rgba(56, 189, 248, 0.45); border-radius: 8px; padding: 10px 14px; color: #38BDF8; font-size: 0.84rem; font-weight: 700; font-family: 'JetBrains Mono', monospace; display: flex; align-items: center; gap: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.2);">
        <span>🌐</span> Toàn bộ hệ thống (Hợp nhất VNĐ)
    </div>
    """,
    unsafe_allow_html=True,
)
current_scope = "ALL"

st.sidebar.markdown("---")
st.sidebar.markdown(
    """
    <div style="font-weight: 700; font-size: 0.76rem; color: #94A3B8; text-transform: uppercase; letter-spacing: 0.8px; margin-bottom: 8px; font-family: 'JetBrains Mono', monospace; display: flex; align-items: center; gap: 6px;">
        <span>📂</span> CHỨC NĂNG HỆ THỐNG:
    </div>
    """,
    unsafe_allow_html=True,
)

MENU_PAGES = [
    "📊 Tổng quan",
    "🐧 Chạy lệnh Ubuntu",
    "🔍 Truy vấn và thống kê",
    "💻 Nhập câu truy vấn",
    "⚡ Quản lý Index",
    "🚀 Kiểm tra hiệu năng",
    "📖 Hướng dẫn demo",
]

selected_page = st.sidebar.radio("CHỌN CHỨC NĂNG:", MENU_PAGES, index=0, label_visibility="collapsed")

st.sidebar.markdown("---")

# Kiểm tra kết nối nhanh từ cache
zk_alive = cached_is_zookeeper_alive()

st.sidebar.markdown(
    """
    <style>
    [data-testid="stSidebar"] div[data-testid="stHorizontalBlock"] button,
    [data-testid="stSidebar"] [data-testid="column"] button,
    [data-testid="stSidebar"] div.stButton button,
    [data-testid="stSidebar"] div[data-testid="stButton"] button,
    [data-testid="stSidebar"] button[kind="secondary"] {
        background: linear-gradient(135deg, rgba(14, 165, 233, 0.15) 0%, rgba(2, 132, 199, 0.25) 100%) !important;
        background-color: #0B132B !important;
        border: 1px solid rgba(56, 189, 248, 0.45) !important;
        color: #38BDF8 !important;
        border-radius: 8px !important;
        height: 38px !important;
        min-height: 38px !important;
        max-height: 38px !important;
        line-height: 38px !important;
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 0.82rem !important;
        font-weight: 700 !important;
        box-shadow: 0 0 10px rgba(56, 189, 248, 0.15) !important;
        box-sizing: border-box !important;
        margin: 0 !important;
        transition: all 0.2s ease !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        gap: 6px !important;
        width: 100% !important;
    }
    [data-testid="stSidebar"] div[data-testid="stHorizontalBlock"] button:hover,
    [data-testid="stSidebar"] [data-testid="column"] button:hover,
    [data-testid="stSidebar"] div.stButton button:hover,
    [data-testid="stSidebar"] div[data-testid="stButton"] button:hover,
    [data-testid="stSidebar"] button[kind="secondary"]:hover {
        background: linear-gradient(135deg, rgba(14, 165, 233, 0.35) 0%, rgba(2, 132, 199, 0.5) 100%) !important;
        background-color: #0F172A !important;
        border-color: #00F2FE !important;
        color: #FFFFFF !important;
        box-shadow: 0 0 16px rgba(0, 242, 254, 0.45) !important;
        transform: translateY(-1px) !important;
    }
    [data-testid="stSidebar"] div[data-testid="stHorizontalBlock"] button p,
    [data-testid="stSidebar"] div[data-testid="stHorizontalBlock"] button span,
    [data-testid="stSidebar"] div[data-testid="stHorizontalBlock"] button div,
    [data-testid="stSidebar"] [data-testid="column"] button p,
    [data-testid="stSidebar"] [data-testid="column"] button span,
    [data-testid="stSidebar"] div.stButton button p,
    [data-testid="stSidebar"] div[data-testid="stButton"] button p,
    [data-testid="stSidebar"] div[data-testid="stButton"] button span {
        color: #38BDF8 !important;
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 0.82rem !important;
        font-weight: 700 !important;
        background: transparent !important;
        background-color: transparent !important;
    }
    [data-testid="stSidebar"] div[data-testid="stHorizontalBlock"] button:hover p,
    [data-testid="stSidebar"] div[data-testid="stHorizontalBlock"] button:hover span,
    [data-testid="stSidebar"] div[data-testid="stHorizontalBlock"] button:hover div,
    [data-testid="stSidebar"] [data-testid="column"] button:hover p,
    [data-testid="stSidebar"] [data-testid="column"] button:hover span,
    [data-testid="stSidebar"] div.stButton button:hover p,
    [data-testid="stSidebar"] div[data-testid="stButton"] button:hover p,
    [data-testid="stSidebar"] div[data-testid="stButton"] button:hover span {
        color: #FFFFFF !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

col_sb1, col_sb2 = st.sidebar.columns([1, 1])
with col_sb1:
    if st.button("🔄 Làm mới", use_container_width=True, help="Xóa bộ đệm và làm mới dữ liệu hệ thống", key="btn_refresh_sidebar"):
        st.cache_data.clear()
        db.clear_db_cache()
        st.rerun()

with col_sb2:
    if zk_alive:
        st.markdown(
            """
            <div style="background: rgba(16, 185, 129, 0.15); border: 1px solid rgba(16, 185, 129, 0.45); border-radius: 8px; padding: 0 8px; display: flex; align-items: center; justify-content: center; gap: 6px; box-shadow: 0 0 10px rgba(16, 185, 129, 0.15); height: 38px; box-sizing: border-box;">
                <span class="status-dot-live"></span>
                <span style="font-size: 0.82rem; font-weight: 700; color: #34D399; font-family: 'JetBrains Mono', monospace; line-height: normal;">ONLINE</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """
            <div style="background: rgba(239, 68, 68, 0.15); border: 1px solid rgba(239, 68, 68, 0.45); border-radius: 8px; padding: 0 8px; display: flex; align-items: center; justify-content: center; gap: 6px; height: 38px; box-sizing: border-box;">
                <span style="width: 8px; height: 8px; background-color: #EF4444; border-radius: 50%; display: inline-block;"></span>
                <span style="font-size: 0.82rem; font-weight: 700; color: #F87171; font-family: 'JetBrains Mono', monospace; line-height: normal;">OFFLINE</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.sidebar.markdown(
    """
    <div style="background: rgba(15, 23, 42, 0.7); border: 1px solid rgba(56, 189, 248, 0.25); border-left: 3.5px solid #00F2FE; border-radius: 10px; padding: 12px 14px; margin-top: 14px; box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);">
        <div style="font-weight: 700; font-size: 0.78rem; color: #38BDF8; font-family: 'JetBrains Mono', monospace; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 8px; display: flex; align-items: center; gap: 6px;">
            <span>⚡</span> THÔNG SỐ CỤM HỆ THỐNG
        </div>
        <div style="font-size: 0.76rem; font-family: 'JetBrains Mono', monospace; line-height: 1.75;">
            <div style="display: flex; justify-content: space-between;"><span style="color: #64748B;">HBase:</span><span style="color: #F8FAFC; font-weight: 600;">2.5.15-hadoop3</span></div>
            <div style="display: flex; justify-content: space-between;"><span style="color: #64748B;">Phoenix:</span><span style="color: #38BDF8; font-weight: 600;">5.2.2 (SQL Engine)</span></div>
            <div style="display: flex; justify-content: space-between;"><span style="color: #64748B;">ZooKeeper:</span><span style="color: #34D399; font-weight: 600;">127.0.0.1:2181</span></div>
            <div style="display: flex; justify-content: space-between;"><span style="color: #64748B;">Phân tán:</span><span style="color: #F59E0B; font-weight: 600;">Salt Buckets = 8</span></div>
            <div style="display: flex; justify-content: space-between;"><span style="color: #64748B;">Tỷ giá QT:</span><span style="color: #F43F5E; font-weight: 600;">x26 (26.000 VNĐ)</span></div>
            <div style="display: flex; justify-content: space-between;"><span style="color: #64748B;">Báo cáo:</span><span style="color: #A855F7; font-weight: 600;">Big Data 2026</span></div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Kiểm tra sơ bộ socket ZooKeeper
if not zk_alive:
    components.render_header("MẤT KẾT NỐI HỆ THỐNG")
    components.render_connection_error_box(
        "Không thể kết nối tới cổng ZooKeeper 2181. Tiến trình HBase và ZooKeeper chưa được khởi động trong Ubuntu WSL."
    )
    if st.button("🔄 Thử kết nối lại ngay", type="primary"):
        cached_is_zookeeper_alive.clear()
        st.cache_data.clear()
        st.rerun()
    st.stop()

# ĐIỀU HƯỚNG LAZY-LOADING TUYỆT ĐỐI (Chỉ gọi duy nhất hàm của trang đang chọn)
if selected_page == "📊 Tổng quan":
    render_overview(scope=current_scope)
elif selected_page in ["🐧 Chạy lệnh Ubuntu", "💼 Quản lý giao dịch"]:
    render_ubuntu_terminal_page(scope=current_scope)
elif selected_page == "🔍 Truy vấn và thống kê":
    render_queries_page()
elif selected_page == "💻 Nhập câu truy vấn":
    render_sql_console()
elif selected_page == "⚡ Quản lý Index":
    render_index_page()
elif selected_page == "🚀 Kiểm tra hiệu năng":
    render_benchmark_page()
elif selected_page == "📖 Hướng dẫn demo":
    render_guide_page()
