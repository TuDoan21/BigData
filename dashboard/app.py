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
import time
import pandas as pd
import streamlit as st

import db
import queries
import formatting
import components

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

@st.cache_data(ttl=15, show_spinner=False)
def cached_is_zookeeper_alive() -> bool:
    """Cache kiểm tra socket ZooKeeper trong 15s để tránh ping lặp lại mỗi lần rerun."""
    return db.is_zookeeper_alive()


@st.cache_data(ttl=120, show_spinner=False)
def load_cached_overview_super_batch() -> tuple[dict, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, str | None]:
    """
    Tối ưu hóa Super-Batch: Gộp toàn bộ 6 câu truy vấn của trang Tổng quan
    vào đúng 1 lần chạy JVM SQLLine duy nhất (giảm từ 25s xuống ~7s).
    Các lần truy cập sau đó trả về tức thì (< 0.05s) từ cache.
    """
    batch_sql = queries.get_super_batch_overview_sql()
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

    # 0: Đếm tổng số bản ghi
    if len(dfs) > 0 and not dfs[0].empty and "TONG_SO" in dfs[0].columns:
        sys_status["table_exists"] = True
        try:
            sys_status["record_count"] = int(float(dfs[0].iloc[0]["TONG_SO"]))
        except Exception:
            sys_status["record_count"] = 0

    # 1: Danh sách Index
    if len(dfs) > 1 and not dfs[1].empty and "INDEX_NAME" in dfs[1].columns:
        idx_names = [str(x).upper() for x in dfs[1]["INDEX_NAME"].tolist()]
        sys_status["index_exists"] = "IDX_GIAO_DICH_KHU_VUC" in idx_names

    df_kpi = dfs[2] if len(dfs) > 2 else pd.DataFrame()
    df_region = dfs[3] if len(dfs) > 3 else pd.DataFrame()
    df_timeline = dfs[4] if len(dfs) > 4 else pd.DataFrame()
    df_top10 = dfs[5] if len(dfs) > 5 else pd.DataFrame()

    return sys_status, df_kpi, df_region, df_timeline, df_top10, None


@st.cache_data(ttl=60, show_spinner=False)
def load_cached_transactions(
    keyword: str,
    regions: tuple[str, ...],
    sort_by: str,
    sort_order: str,
    limit: int,
    offset: int,
) -> tuple[pd.DataFrame | None, str | None, float]:
    """Cache dữ liệu danh sách giao dịch phân trang database."""
    sql = queries.build_transaction_list_query(
        search_keyword=keyword,
        khu_vuc_list=regions,
        sort_by=sort_by,
        sort_order=sort_order,
        limit=limit,
        offset=offset,
    )
    return db.query_phoenix_df_timed(sql, timeout=30)


@st.cache_data(ttl=120, show_spinner=False)
def get_cached_total_count(keyword: str, regions: tuple[str, ...]) -> int:
    """Cache tổng số bản ghi theo bộ lọc. Đổi trang không bao giờ chạy lại COUNT(*)."""
    sql = queries.build_count_transactions_query(search_keyword=keyword, khu_vuc_list=regions)
    df, err = db.query_phoenix_df(sql, timeout=20)
    if df is not None and not df.empty:
        try:
            return int(float(df.iloc[0].get("TOTAL_ROWS", 0)))
        except Exception:
            return 0
    return 0


@st.cache_data(ttl=120, show_spinner=False)
def load_cached_query_result(sql: str) -> tuple[pd.DataFrame | None, str | None, float]:
    """Cache kết quả truy vấn demo theo câu lệnh SQL để tránh chạy lại khi xem lại."""
    return db.query_phoenix_df_timed(sql, timeout=35)


@st.cache_data(ttl=120, show_spinner=False)
def load_cached_index_catalog() -> tuple[list[dict], bool]:
    """Lấy danh mục Index từ SYSTEM.CATALOG trong 1 câu truy vấn duy nhất."""
    all_idx = db.get_all_indexes("GIAO_DICH")
    idx_names = [str(x.get("INDEX_NAME", "")).upper() for x in all_idx]
    is_active = "IDX_GIAO_DICH_KHU_VUC" in idx_names
    return all_idx, is_active


# =============================================================================
# HÀM RENDER TỪNG TRANG RIÊNG BIỆT (CHỈ THỰC THI TRANG ĐƯỢC CHỌN)
# =============================================================================

def render_overview():
    """Trang 1: Tổng quan - Tối ưu Super Batch nạp dữ liệu tức thì."""
    components.render_header("📊 TỔNG QUAN HỆ THỐNG")

    with st.spinner("Đang tải dữ liệu tổng quan từ Phoenix HBase..."):
        sys_status, df_kpi, df_region, df_timeline, df_top10, err = load_cached_overview_super_batch()

    if err:
        if "TableNotFoundException" in err or "ERROR 1012" in err:
            components.render_table_missing_box()
        else:
            components.render_connection_error_box(err)
        return

    # Thanh trạng thái hạ tầng
    components.render_status_bar(sys_status)

    # 5 KPI Cards
    total_tx = 0
    total_cust = 0
    total_rev = 0.0
    avg_val = 0.0
    num_regions = 0

    if df_kpi is not None and not df_kpi.empty:
        try:
            total_tx = int(float(df_kpi.iloc[0].get("TONG_GIAO_DICH", 0)))
            total_cust = int(float(df_kpi.iloc[0].get("TONG_KHACH_HANG", 0)))
            total_rev = float(df_kpi.iloc[0].get("TONG_DOANH_THU", 0.0))
            avg_val = float(df_kpi.iloc[0].get("GIA_TRI_TRUNG_BINH", 0.0))
            num_regions = int(float(df_kpi.iloc[0].get("SO_KHU_VUC", 0)))
        except (ValueError, TypeError, KeyError):
            pass

    components.render_kpi_cards(total_tx, total_cust, total_rev, avg_val, num_regions)

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

    # 2 Biểu đồ: Khu vực & Chuỗi thời gian
    c_chart1, c_chart2 = st.columns(2)
    with c_chart1:
        st.markdown("##### 📍 Doanh Thu Theo Khu Vực")
        if df_region is not None and not df_region.empty and "KHU_VUC" in df_region.columns:
            df_reg_plot = df_region.copy()
            df_reg_plot["TONG_DOANH_THU"] = pd.to_numeric(df_reg_plot["TONG_DOANH_THU"], errors="coerce").fillna(0)
            st.bar_chart(data=df_reg_plot, x="KHU_VUC", y="TONG_DOANH_THU", color="#1E88E5", height=280)
        else:
            st.info("Chưa có dữ liệu phân bố theo khu vực.")

    with c_chart2:
        st.markdown("##### 📈 Doanh Thu Theo Dòng Thời Gian")
        if df_timeline is not None and not df_timeline.empty and "NGAY_GIAO_DICH" in df_timeline.columns:
            df_time_plot = df_timeline.copy()
            df_time_plot["DOANH_THU_NGAY"] = pd.to_numeric(df_time_plot["DOANH_THU_NGAY"], errors="coerce").fillna(0)
            st.line_chart(data=df_time_plot, x="NGAY_GIAO_DICH", y="DOANH_THU_NGAY", color="#0F294A", height=280)
        else:
            st.info("Chưa có dữ liệu chuỗi thời gian.")

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    # Bảng 10 giao dịch mới nhất
    st.markdown("##### 📋 Danh Sách 10 Giao Dịch Mới Nhất (LIMIT 10)")
    if df_top10 is not None and not df_top10.empty:
        df_display = formatting.format_giao_dich_table(df_top10)
        col_order = ["MA_GIAO_DICH", "MA_KHACH_HANG", "MA_SAN_PHAM", "KHU_VUC", "SO_LUONG_HIEN_THI", "DON_GIA_HIEN_THI", "THANH_TIEN_HIEN_THI", "THOI_GIAN_HIEN_THI"]
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
        cols_exist = [c for c in col_order if c in df_display.columns]
        st.dataframe(df_display[cols_exist].rename(columns=rename_map), use_container_width=True, height=330)
    else:
        st.info("Bảng GIAO_DICH hiện tại chưa có dữ liệu.")


def render_transactions():
    """Trang 2: Quản lý giao dịch (CRUD) - Phân trang database LIMIT 20, Form chống rerun."""
    components.render_header("💼 QUẢN LÝ GIAO DỊCH (DML)")

    # Khởi tạo session state cho bộ lọc nếu chưa có
    if "filter_kw" not in st.session_state:
        st.session_state["filter_kw"] = ""
    if "filter_regions" not in st.session_state:
        st.session_state["filter_regions"] = ("MIEN_NAM", "MIEN_BAC", "MIEN_TRUNG")
    if "crud_page" not in st.session_state:
        st.session_state["crud_page"] = 1

    # 1. Bộ lọc đặt trong st.form chống rerun khi gõ phím
    with st.form("filter_form"):
        fc1, fc2, fc3, fc4 = st.columns([3, 3, 2, 2])
        with fc1:
            inp_kw = st.text_input("Tìm kiếm (Mã GD hoặc Mã KH):", value=st.session_state["filter_kw"], placeholder="Ví dụ: GD001 hoặc KH01")
        with fc2:
            inp_regions = st.multiselect(
                "Khu vực:",
                options=["MIEN_NAM", "MIEN_BAC", "MIEN_TRUNG"],
                default=list(st.session_state["filter_regions"]),
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
            st.session_state["filter_regions"] = ("MIEN_NAM", "MIEN_BAC", "MIEN_TRUNG")
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

    # Lấy tổng số dòng từ cache (không gọi lại COUNT(*) khi chuyển trang)
    total_records = get_cached_total_count(active_kw, active_regions)
    total_pages = max(1, (total_records + page_size - 1) // page_size)

    # Tải danh sách giao dịch trang hiện tại từ cache
    with st.spinner(f"Đang tải trang {current_p}/{total_pages}..."):
        df_list, err_list, exec_ms = load_cached_transactions(
            active_kw, active_regions, "MA_GIAO_DICH", "ASC", page_size, offset
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
        df_formatted = formatting.format_giao_dich_table(df_list)
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

    current_ids = df_list["MA_GIAO_DICH"].dropna().tolist() if df_list is not None and not df_list.empty else []

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
                add_id = st.text_input("Mã Giao Dịch (Khóa chính - Bắt buộc):", placeholder="Ví dụ: GD2026")
                add_kh = st.text_input("Mã Khách Hàng:", value="KH01")
                add_sp = st.text_input("Mã Sản Phẩm:", value="SP01")
            with a2:
                add_kv = st.selectbox("Khu Vực:", options=["MIEN_NAM", "MIEN_BAC", "MIEN_TRUNG"])
                add_sl = st.number_input("Số Lượng:", min_value=1, max_value=10000, value=5)
                add_dg = st.number_input("Đơn Giá (VNĐ):", min_value=0.0, value=18500000.0, step=500000.0)

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
            with st.spinner(f"Đang tải giao dịch {target_edit_id}..."):
                df_curr, err_curr = db.query_phoenix_df(queries.sql_get_record_by_id(target_edit_id))

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
                        kv_idx = ["MIEN_NAM", "MIEN_BAC", "MIEN_TRUNG"].index(curr_kv) if curr_kv in ["MIEN_NAM", "MIEN_BAC", "MIEN_TRUNG"] else 0
                        edit_kv = st.selectbox("Khu Vực:", options=["MIEN_NAM", "MIEN_BAC", "MIEN_TRUNG"], index=kv_idx)
                        edit_sl = st.number_input("Số Lượng:", min_value=1, max_value=10000, value=int(float(row_data.get("SO_LUONG", 1))))
                        edit_dg = st.number_input("Đơn Giá (VNĐ):", min_value=0.0, value=float(row_data.get("DON_GIA", 0.0)), step=500000.0)

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
            with st.spinner(f"Đang kiểm tra {target_del_id}..."):
                df_to_del, err_td = db.query_phoenix_df(queries.sql_get_record_by_id(target_del_id))

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
                        st.success(f"✅ Đã xóa thành công giao dịch '{target_del_id}'!")
                        st.code(del_sql, language="sql")
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error(f"Xóa thất bại: {db.format_db_error(msg_d)}")
        else:
            st.info("💡 Chọn hoặc nhập mã giao dịch để tiến hành thao tác xóa.")


def render_queries_page():
    """Trang 3: Truy vấn và thống kê - Không tự động chạy truy vấn, chỉ chạy khi bấm nút."""
    components.render_header("🔍 TRUY VẤN VÀ THỐNG KÊ")

    st.markdown("Danh mục 10 câu truy vấn demo theo đúng kịch bản bài báo cáo môn Big Data.")

    query_options = [f"{q['id']}. {q['title'].split('.', 1)[1].strip()}" for q in queries.DEMO_QUERIES]
    selected_idx = st.selectbox("Chọn câu truy vấn để demo:", range(len(query_options)), format_func=lambda i: query_options[i])

    active_query = queries.DEMO_QUERIES[selected_idx]

    st.markdown(f"#### 📌 {active_query['title']}")
    st.markdown(f"**🎯 Mục đích truy vấn:** {active_query['purpose']}")

    st.markdown("##### 📝 Câu lệnh Phoenix SQL:")
    st.code(active_query["sql"], language="sql")

    col_btn, col_empty = st.columns([2, 5])
    with col_btn:
        btn_run = st.button("🚀 Thực Thi Truy Vấn", type="primary", use_container_width=True, key=f"btn_run_q_{active_query['id']}")

    result_key = f"query_res_{active_query['id']}"

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
                df_res_formatted = formatting.format_giao_dich_table(df_result)
                st.dataframe(df_res_formatted, use_container_width=True)

                if "KHU_VUC" in df_result.columns and "TONG_DOANH_THU" in df_result.columns:
                    df_chart = df_result.copy()
                    df_chart["TONG_DOANH_THU"] = pd.to_numeric(df_chart["TONG_DOANH_THU"], errors="coerce").fillna(0)
                    st.bar_chart(df_chart, x="KHU_VUC", y="TONG_DOANH_THU", color="#1E88E5", height=260)
                elif "MA_SAN_PHAM" in df_result.columns and "TONG_SO_LUONG_BAN" in df_result.columns:
                    df_chart = df_result.copy()
                    df_chart["TONG_SO_LUONG_BAN"] = pd.to_numeric(df_chart["TONG_SO_LUONG_BAN"], errors="coerce").fillna(0)
                    st.bar_chart(df_chart, x="MA_SAN_PHAM", y="TONG_SO_LUONG_BAN", color="#0F294A", height=260)
            else:
                st.info("Truy vấn thành công nhưng không có bản ghi nào được trả về.")
    else:
        st.info("💡 Bấm nút 'Thực Thi Truy Vấn' ở trên để bắt đầu chạy câu lệnh.")


# =============================================================================
# TRANG 4: NHẬP CÂU TRUY VẤN (SQL CONSOLE ĐẦY ĐỦ BẢO VỆ VÀ XÁC NHẬN AN TOÀN)
# =============================================================================

SAMPLE_CONSOLE_QUERIES = {
    "-- Chọn câu lệnh mẫu để nạp --": "",
    "1. Lấy 10 dòng đầu tiên (LIMIT 10)": "SELECT *\nFROM GIAO_DICH\nLIMIT 10;",
    "2. Lọc theo khu vực MIEN_NAM (LIMIT 20)": "SELECT *\nFROM GIAO_DICH\nWHERE KHU_VUC = 'MIEN_NAM'\nLIMIT 20;",
    "3. Thống kê doanh thu theo khu vực (GROUP BY)": "SELECT KHU_VUC,\n       COUNT(*) AS SO_GIAO_DICH,\n       SUM(SO_LUONG * DON_GIA) AS DOANH_THU\nFROM GIAO_DICH\nGROUP BY KHU_VUC;",
    "4. Phân tích kế hoạch thực thi EXPLAIN": "EXPLAIN\nSELECT *\nFROM GIAO_DICH\nWHERE KHU_VUC = 'MIEN_NAM';",
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
            # Gộp COMMIT tự động vào câu lệnh DML/DDL
            full_sql = pending_sql.strip().rstrip(";") + ";\n!commit;"
            with st.spinner("Đang thực thi và COMMIT vào HBase..."):
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
    """Trang 6: Kiểm tra hiệu năng - Chỉ chạy khi người dùng chủ động bấm nút."""
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

        st.markdown("##### 📊 Kết Quả Đo Thời Gian Phản Hồi (Mili-giây):")
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
            - Trong HBase truyền thống, Row Key tăng tuần tự (`GD001`, `GD002`...) sẽ khiến toàn bộ dữ liệu mới ghi tập trung vào một Region Server duy nhất.
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
            
            2. **Bước 2: Thao tác Quản lý Giao dịch (DML) (2 phút)**
               - Chuyển sang trang **💼 Quản lý giao dịch**.
               - Demo **Tìm kiếm & Phân trang**: Gõ `GD001` hoặc chọn khu vực `MIEN_NAM`.
               - Demo **Thêm mới**: Nhập mã `GD999`, điền thông tin, nhấn Lưu -> Bảng lập tức làm mới.
               - Demo **Sửa**: Chọn mã `GD999`, sửa số lượng và đơn giá -> Khóa chính bị khóa không thể sửa, cập nhật thành công qua `UPSERT`.
               - Demo **Xóa**: Chọn mã `GD999`, hộp thoại cảnh báo màu đỏ hiện rõ mã `GD999` -> Xác nhận xóa -> Bản ghi biến mất.
            
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
    <div style="text-align: center; padding-bottom: 12px;">
        <span style="font-size: 2rem;">⚡</span>
        <h3 style="margin: 0; color: #0F294A; font-weight: 700;">Apache Phoenix</h3>
        <p style="margin: 0; font-size: 0.82rem; color: #64748B;">SQL Engine trên Apache HBase</p>
    </div>
    """,
    unsafe_allow_html=True,
)

MENU_PAGES = [
    "📊 Tổng quan",
    "💼 Quản lý giao dịch",
    "🔍 Truy vấn và thống kê",
    "💻 Nhập câu truy vấn",
    "⚡ Quản lý Index",
    "🚀 Kiểm tra hiệu năng",
    "📖 Hướng dẫn demo",
]

selected_page = st.sidebar.radio("CHỌN CHỨC NĂNG:", MENU_PAGES, index=0)

st.sidebar.markdown("---")

# Kiểm tra kết nối nhanh từ cache
zk_alive = cached_is_zookeeper_alive()

col_sb1, col_sb2 = st.sidebar.columns([1, 1])
with col_sb1:
    if st.button("🔄 Làm mới", use_container_width=True, help="Làm mới bộ nhớ đệm"):
        st.cache_data.clear()
        st.rerun()

with col_sb2:
    status_light = "🟢 Online" if zk_alive else "🔴 Offline"
    st.markdown(f"<div style='text-align: center; padding-top: 6px; font-weight: 600; font-size: 0.85rem;'>{status_light}</div>", unsafe_allow_html=True)

st.sidebar.markdown(
    """
    <div style="font-size: 0.78rem; color: #64748B; background-color: #F1F5F9; padding: 10px; border-radius: 6px; margin-top: 15px; border: 1px solid #E2E8F0;">
    <b>Thông số môi trường:</b><br>
    &bull; Apache HBase: 2.5.15-hadoop3<br>
    &bull; Apache Phoenix: 5.2.2<br>
    &bull; ZooKeeper: 127.0.0.1:2181<br>
    &bull; Cấu trúc: Salt Buckets = 8<br>
    &bull; Báo cáo: Big Data 2026
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
    render_overview()
elif selected_page == "💼 Quản lý giao dịch":
    render_transactions()
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
