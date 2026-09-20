#!/usr/bin/env python3
"""
=============================================================================
DASHBOARD QUẢN LÝ GIAO DỊCH APACHE PHOENIX TRÊN HBASE (BIG DATA 2026)
Framework: Streamlit
Kiến trúc: Tách module (db, queries, formatting, components), lazy-loading 8 trang,
cache có kiểm soát (@st.cache_data), pre-check socket chống treo vô hạn.
=============================================================================
"""

import datetime
import pandas as pd
import streamlit as st

import db
import queries
import formatting
import components

# Cấu hình trang Streamlit
st.set_page_config(
    page_title="Apache Phoenix - Quản Lý Giao Dịch",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Nhúng CSS tùy biến hiện đại
components.inject_custom_css()


# =============================================================================
# CÁC HÀM TRUY VẤN CÓ CACHE (CONTROLLED CACHING)
# =============================================================================

@st.cache_data(ttl=30)
def cached_overview_data() -> tuple[pd.DataFrame | None, pd.DataFrame | None, pd.DataFrame | None, str | None]:
    """
    Truy vấn gộp cho trang Tổng quan trong 1 phiên SQLLine duy nhất:
    - Khối 1: KPI (Tổng GD, Tổng doanh thu, TB doanh thu, Số KV)
    - Khối 2: Gom nhóm theo khu vực cho biểu đồ
    - Khối 3: 10 giao dịch đầu tiên / gần nhất
    """
    batch_sql = queries.get_overview_batch_sql()
    ok, raw_output = db.execute_phoenix_sql(batch_sql, timeout=25)
    if not ok:
        return None, None, None, raw_output

    dfs = db.parse_sqlline_csv_blocks(raw_output)
    df_kpi = dfs[0] if len(dfs) > 0 else pd.DataFrame()
    df_chart = dfs[1] if len(dfs) > 1 else pd.DataFrame()
    df_top10 = dfs[2] if len(dfs) > 2 else pd.DataFrame()

    return df_kpi, df_chart, df_top10, None


@st.cache_data(ttl=30)
def cached_system_status() -> dict:
    """Cache trạng thái hệ thống trong 30 giây để tránh kiểm tra liên tục."""
    return db.check_system_status()


# =============================================================================
# SIDEBAR NAVIGATION (8 TRANG LAZY-LOADING)
# =============================================================================

st.sidebar.markdown("### ⚡ Apache Phoenix")
st.sidebar.caption("SQL Layer trên Apache HBase")

MENU_PAGES = [
    "📊 Tổng quan",
    "🔍 Truy vấn dữ liệu",
    "💼 Quản lý giao dịch",
    "📈 Thống kê",
    "⚡ Index và EXPLAIN",
    "🖥️ Trạng thái hệ thống",
]

selected_page = st.sidebar.radio("Điều hướng chức năng:", MENU_PAGES, index=0)

st.sidebar.markdown("---")
if st.sidebar.button("🔄 Làm mới dữ liệu (Clear Cache)", use_container_width=True):
    st.cache_data.clear()
    st.sidebar.success("Đã làm mới bộ nhớ đệm!")
    st.rerun()

st.sidebar.markdown(
    """
    <div style="font-size: 0.8rem; color: #6B7280; margin-top: 15px;">
    <b>Môi trường:</b><br>
    - HBase: 2.5.15-hadoop3<br>
    - Phoenix: 5.2.2<br>
    - ZooKeeper: 127.0.0.1:2181<br>
    - Table: <code>GIAO_DICH</code> (8 Salts)
    </div>
    """,
    unsafe_allow_html=True,
)


# =============================================================================
# KIỂM TRA SƠ BỘ KẾT NỐI (PRE-CHECK NHANH < 0.6s)
# =============================================================================
if not db.is_zookeeper_alive():
    components.render_header()
    components.render_connection_error_box(
        "Không thể kết nối tới cổng ZooKeeper 2181. Tiến trình HBase/ZooKeeper chưa được khởi động trong Ubuntu WSL."
    )
    if st.button("🔄 Kiểm tra lại kết nối", type="primary"):
        st.cache_data.clear()
        st.rerun()
    st.stop()


# =============================================================================
# TRANG 1: TỔNG QUAN (OVERVIEW)
# =============================================================================
if selected_page == "📊 Tổng quan":
    components.render_header()

    with st.spinner("Đang tải dữ liệu tổng quan từ Phoenix HBase..."):
        df_kpi, df_chart, df_top10, err = cached_overview_data()

    if err:
        if "TableNotFoundException" in err or "ERROR 1012" in err:
            components.render_table_missing_box()
        else:
            components.render_connection_error_box(err)
        st.stop()

    # 1. Hiển thị 4 KPI Cards
    total_tx = 0
    total_rev = 0.0
    avg_val = 0.0
    num_regions = 0

    if df_kpi is not None and not df_kpi.empty:
        try:
            total_tx = int(float(df_kpi.iloc[0].get("TONG_GIAO_DICH", 0)))
            total_rev = float(df_kpi.iloc[0].get("TONG_DOANH_THU", 0.0))
            avg_val = float(df_kpi.iloc[0].get("GIA_TRI_TRUNG_BINH", 0.0))
            num_regions = int(float(df_kpi.iloc[0].get("SO_KHU_VUC", 0)))
        except (ValueError, TypeError, KeyError):
            pass

    components.render_kpi_cards(total_tx, total_rev, avg_val, num_regions)

    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

    # 2. Biểu đồ doanh thu và số lượng giao dịch theo khu vực
    c_chart1, c_chart2 = st.columns(2)

    with c_chart1:
        st.subheader("📊 Doanh Thu Theo Khu Vực")
        if df_chart is not None and not df_chart.empty and "KHU_VUC" in df_chart.columns:
            df_chart_copy = df_chart.copy()
            df_chart_copy["TONG_DOANH_THU"] = pd.to_numeric(df_chart_copy["TONG_DOANH_THU"], errors="coerce").fillna(0)
            st.bar_chart(data=df_chart_copy, x="KHU_VUC", y="TONG_DOANH_THU", color="#1E88E5", height=280)
        else:
            st.info("Chưa có dữ liệu biểu đồ doanh thu.")

    with c_chart2:
        st.subheader("📈 Số Giao Dịch Theo Khu Vực")
        if df_chart is not None and not df_chart.empty and "KHU_VUC" in df_chart.columns:
            df_chart_copy = df_chart.copy()
            df_chart_copy["SO_GIAO_DICH"] = pd.to_numeric(df_chart_copy["SO_GIAO_DICH"], errors="coerce").fillna(0)
            st.bar_chart(data=df_chart_copy, x="KHU_VUC", y="SO_GIAO_DICH", color="#00897B", height=280)
        else:
            st.info("Chưa có dữ liệu số lượng giao dịch.")

    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

    # 3. Bảng 10 giao dịch gần nhất
    st.subheader("📋 Danh Sách 10 Giao Dịch Mẫu (LIMIT 10)")
    if df_top10 is not None and not df_top10.empty:
        df_display = formatting.format_giao_dich_table(df_top10)
        col_order = ["MA_GIAO_DICH", "MA_KHACH_HANG", "MA_SAN_PHAM", "KHU_VUC", "SO_LUONG", "DON_GIA_HIEN_THI", "THANH_TIEN_HIEN_THI", "THOI_GIAN_HIEN_THI"]
        rename_map = {
            "MA_GIAO_DICH": "Mã GD",
            "MA_KHACH_HANG": "Khách Hàng",
            "MA_SAN_PHAM": "Sản Phẩm",
            "KHU_VUC": "Khu Vực",
            "SO_LUONG": "Số Lượng",
            "DON_GIA_HIEN_THI": "Đơn Giá",
            "THANH_TIEN_HIEN_THI": "Thành Tiền",
            "THOI_GIAN_HIEN_THI": "Thời Gian",
        }
        cols_exist = [c for c in col_order if c in df_display.columns]
        st.dataframe(df_display[cols_exist].rename(columns=rename_map), use_container_width=True, height=350)
    else:
        st.info("Bảng GIAO_DICH hiện tại chưa có dữ liệu.")

    with st.expander("📝 Xem các câu lệnh SQL đã thực thi ở trang Tổng quan"):
        for q in queries.get_overview_batch_sql():
            st.code(q, language="sql")


# =============================================================================
# TRANG 2: TRUY VẤN DỮ LIỆU (SELECT & FILTERS)
# =============================================================================
elif selected_page == "🔍 Truy vấn dữ liệu":
    components.render_header()
    st.subheader("🔍 Tìm Kiếm & Lọc Dữ Liệu Giao Dịch")

    with st.form("form_filter_giao_dich"):
        f1, f2 = st.columns([1, 2])
        with f1:
            input_ma_gd = st.text_input("Mã giao dịch (Point Lookup):", placeholder="Ví dụ: GD001")
        with f2:
            input_regions = st.multiselect(
                "Khu vực:",
                options=["MIEN_NAM", "MIEN_BAC", "MIEN_TRUNG"],
                default=["MIEN_NAM", "MIEN_BAC", "MIEN_TRUNG"],
            )

        f3, f4, f5 = st.columns(3)
        with f3:
            input_min_price = st.number_input("Đơn giá tối thiểu (VNĐ):", min_value=0.0, value=0.0, step=1000000.0)
        with f4:
            input_max_price = st.number_input("Đơn giá tối đa (VNĐ):", min_value=0.0, value=0.0, step=1000000.0)
        with f5:
            input_limit = st.selectbox("Số dòng hiển thị (LIMIT):", options=[10, 20, 50, 100], index=1)

        f6, f7 = st.columns(2)
        with f6:
            input_sort_by = st.selectbox(
                "Sắp xếp theo cột:",
                options=["MA_GIAO_DICH", "DON_GIA", "THANH_TIEN", "SO_LUONG", "THOI_GIAN"],
                index=0,
            )
        with f7:
            input_sort_order = st.selectbox("Thứ tự sắp xếp:", options=["Tăng dần (ASC)", "Giảm dần (DESC)"], index=0)

        btn_submit_search = st.form_submit_button("🚀 Thực hiện truy vấn", type="primary")

    # Mặc định tạo câu truy vấn an toàn
    order_direction = "DESC" if "DESC" in input_sort_order else "ASC"
    active_sql = queries.build_search_query(
        ma_giao_dich=input_ma_gd,
        khu_vuc_list=input_regions,
        min_don_gia=input_min_price if input_min_price > 0 else None,
        max_don_gia=input_max_price if input_max_price > 0 else None,
        sort_by=input_sort_by,
        sort_order=order_direction,
        limit=input_limit,
    )

    st.markdown("##### 📝 Câu lệnh Phoenix SQL tương ứng:")
    st.code(active_sql, language="sql")

    # Thực thi khi nhấn nút tìm kiếm hoặc khi vào trang lần đầu
    run_query = btn_submit_search or "has_searched" not in st.session_state
    if run_query:
        st.session_state["has_searched"] = True
        with st.spinner("Đang thực thi truy vấn trên HBase..."):
            df_search, err = db.query_phoenix_df(active_sql)

        if err:
            st.error(f"Lỗi thực thi truy vấn: {err}")
        elif df_search is not None:
            st.success(f"Truy vấn thành công! Tìm thấy {len(df_search)} dòng kết quả.")
            if not df_search.empty:
                df_formatted = formatting.format_giao_dich_table(df_search)
                cols_to_show = [
                    "MA_GIAO_DICH", "MA_KHACH_HANG", "MA_SAN_PHAM", "KHU_VUC",
                    "SO_LUONG", "DON_GIA_HIEN_THI", "THANH_TIEN_HIEN_THI", "THOI_GIAN_HIEN_THI"
                ]
                rename_map = {
                    "MA_GIAO_DICH": "Mã GD",
                    "MA_KHACH_HANG": "Khách Hàng",
                    "MA_SAN_PHAM": "Sản Phẩm",
                    "KHU_VUC": "Khu Vực",
                    "SO_LUONG": "Số Lượng",
                    "DON_GIA_HIEN_THI": "Đơn Giá",
                    "THANH_TIEN_HIEN_THI": "Thành Tiền",
                    "THOI_GIAN_HIEN_THI": "Thời Gian",
                }
                cols_exist = [c for c in cols_to_show if c in df_formatted.columns]
                st.dataframe(df_formatted[cols_exist].rename(columns=rename_map), use_container_width=True, height=380)
            else:
                st.info("Không có bản ghi nào khớp với điều kiện lọc.")


# =============================================================================
# TRANG 3: QUẢN LÝ GIAO DỊCH (THÊM – CẬP NHẬT – XÓA)
# =============================================================================
elif selected_page == "💼 Quản lý giao dịch":
    components.render_header()
    st.subheader("💼 Quản Lý Giao Dịch Apache Phoenix (DML)")
    st.caption("Thực hiện các thao tác thêm mới (UPSERT), cập nhật (UPSERT) và xóa (DELETE) trên bảng GIAO_DICH.")

    tab_add, tab_update, tab_delete = st.tabs([
        "➕ Thêm giao dịch",
        "✏️ Cập nhật giao dịch",
        "🗑️ Xóa giao dịch",
    ])

    # -------------------------------------------------------------------------
    # TAB 1: THÊM GIAO DỊCH
    # -------------------------------------------------------------------------
    with tab_add:
        st.markdown("##### ➕ Thêm Giao Dịch Mới (UPSERT INTO)")
        with st.form("form_add_transaction_tab"):
            a1, a2 = st.columns(2)
            with a1:
                in_new_id = st.text_input("Mã Giao Dịch (Row Key - Bắt buộc):", placeholder="Ví dụ: GD100")
                in_new_kh = st.text_input("Mã Khách Hàng:", value="KH01")
                in_new_sp = st.text_input("Mã Sản Phẩm:", value="SP01")
            with a2:
                in_new_kv = st.selectbox("Khu Vực:", options=["MIEN_NAM", "MIEN_BAC", "MIEN_TRUNG"])
                in_new_sl = st.number_input("Số Lượng:", min_value=1, max_value=10000, value=10)
                in_new_dg = st.number_input("Đơn Giá (VNĐ):", min_value=0.0, value=15000000.0, step=500000.0)

            now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            in_new_time = st.text_input("Thời Gian Giao Dịch (yyyy-MM-dd HH:mm:ss):", value=now_str)

            btn_add_submit = st.form_submit_button("💾 Lưu Giao Dịch Mới (UPSERT & COMMIT)", type="primary")

        if btn_add_submit:
            if not in_new_id.strip():
                st.error("Mã giao dịch không được để trống!")
            elif in_new_sl <= 0:
                st.error("Số lượng giao dịch phải lớn hơn 0!")
            elif in_new_dg < 0:
                st.error("Đơn giá không được âm!")
            else:
                clean_id = in_new_id.strip()
                # Kiểm tra trùng lặp Row Key chống ghi đè nhầm
                with st.spinner("Đang kiểm tra trùng lặp Row Key..."):
                    chk_sql = queries.sql_check_record_exists(clean_id)
                    df_chk, err_chk = db.query_phoenix_df(chk_sql)

                exists = False
                if df_chk is not None and not df_chk.empty:
                    try:
                        exists = int(float(df_chk.iloc[0].get("CNT", 0))) > 0
                    except Exception:
                        exists = False

                if exists:
                    st.warning(
                        f"⚠️ Giao dịch '{clean_id}' đã tồn tại trong HBase! "
                        "Để chỉnh sửa bản ghi này, vui lòng chuyển sang tab 'Cập nhật giao dịch' để tránh ghi đè nhầm."
                    )
                else:
                    upsert_sql = queries.sql_upsert_transaction(
                        clean_id, in_new_kh, in_new_sp, in_new_kv, in_new_sl, in_new_dg, in_new_time
                    )
                    with st.spinner("Đang thực thi UPSERT INTO và COMMIT vào HBase..."):
                        ok, msg = db.execute_phoenix_sql(upsert_sql)

                    if ok:
                        st.cache_data.clear()
                        st.success(f"✅ Đã thêm thành công giao dịch '{clean_id}' vào HBase!")
                        st.markdown("##### 📝 Câu lệnh SQL đã thực thi:")
                        st.code(upsert_sql, language="sql")
                    else:
                        st.error(f"Thao tác thêm giao dịch thất bại: {msg}")

    # -------------------------------------------------------------------------
    # TAB 2: CẬP NHẬT GIAO DỊCH
    # -------------------------------------------------------------------------
    with tab_update:
        st.markdown("##### ✏️ Cập Nhật Giao Dịch Theo Row Key (UPSERT)")
        with st.form("form_search_update_tab"):
            u_col1, u_col2 = st.columns([3, 1])
            with u_col1:
                u_search_id = st.text_input("Nhập Mã Giao Dịch cần cập nhật (Row Key):", value=st.session_state.get("update_current_id", "GD001"))
            with u_col2:
                st.write("")
                st.write("")
                btn_find_update = st.form_submit_button("🔍 Tìm kiếm giao dịch", type="primary")

        if btn_find_update or "update_current_id" in st.session_state:
            target_id = u_search_id.strip() if btn_find_update else st.session_state.get("update_current_id", "GD001")
            st.session_state["update_current_id"] = target_id

            get_sql = queries.sql_get_record_by_id(target_id)
            with st.spinner(f"Đang tải thông tin giao dịch {target_id}..."):
                df_curr, err_curr = db.query_phoenix_df(get_sql)

            if err_curr:
                st.error(f"Lỗi tìm kiếm: {err_curr}")
            elif df_curr is None or df_curr.empty:
                st.warning(f"Không tìm thấy giao dịch '{target_id}' trong bảng GIAO_DICH.")
            else:
                row = df_curr.iloc[0]
                st.info(f"Dữ liệu hiện tại của giao dịch **{target_id}**:")
                st.dataframe(formatting.format_giao_dich_table(df_curr), use_container_width=True)

                with st.form("form_execute_update_tab"):
                    uc1, uc2 = st.columns(2)
                    with uc1:
                        st.text_input("Mã Giao Dịch (Khóa chính - Không đổi):", value=target_id, disabled=True)
                        new_kh = st.text_input("Mã Khách Hàng:", value=str(row.get("MA_KHACH_HANG", "")))
                        new_sp = st.text_input("Mã Sản Phẩm:", value=str(row.get("MA_SAN_PHAM", "")))
                    with uc2:
                        curr_kv = str(row.get("KHU_VUC", "MIEN_NAM"))
                        kv_idx = ["MIEN_NAM", "MIEN_BAC", "MIEN_TRUNG"].index(curr_kv) if curr_kv in ["MIEN_NAM", "MIEN_BAC", "MIEN_TRUNG"] else 0
                        new_kv = st.selectbox("Khu Vực:", options=["MIEN_NAM", "MIEN_BAC", "MIEN_TRUNG"], index=kv_idx)
                        new_sl = st.number_input("Số Lượng Mới:", min_value=1, max_value=10000, value=int(float(row.get("SO_LUONG", 1))))
                        new_dg = st.number_input("Đơn Giá Mới (VNĐ):", min_value=0.0, value=float(row.get("DON_GIA", 0.0)), step=500000.0)

                    raw_time = str(row.get("THOI_GIAN", "")).replace(".0", "").strip()
                    new_time = st.text_input("Thời Gian (yyyy-MM-dd HH:mm:ss):", value=raw_time)

                    btn_save_update = st.form_submit_button("💾 Xác Nhận Cập Nhật (UPSERT & COMMIT)", type="primary")

                if btn_save_update:
                    update_sql = queries.sql_upsert_transaction(target_id, new_kh, new_sp, new_kv, new_sl, new_dg, new_time)
                    with st.spinner("Đang cập nhật bản ghi vào HBase..."):
                        ok_u, msg_u = db.execute_phoenix_sql(update_sql)

                    if ok_u:
                        st.cache_data.clear()
                        st.success(f"✅ Đã cập nhật thành công giao dịch '{target_id}'!")
                        st.markdown("##### 📝 Câu lệnh SQL đã thực thi:")
                        st.code(update_sql, language="sql")

                        df_after, _ = db.query_phoenix_df(queries.sql_get_record_by_id(target_id))
                        if df_after is not None and not df_after.empty:
                            st.markdown("##### 📋 Dữ liệu sau khi cập nhật:")
                            st.dataframe(formatting.format_giao_dich_table(df_after), use_container_width=True)
                    else:
                        st.error(f"Cập nhật thất bại: {msg_u}")

    # -------------------------------------------------------------------------
    # TAB 3: XÓA GIAO DỊCH
    # -------------------------------------------------------------------------
    with tab_delete:
        st.markdown("##### 🗑️ Xóa Giao Dịch Theo Row Key (DELETE FROM)")
        with st.form("form_search_delete_tab"):
            d1, d2 = st.columns([3, 1])
            with d1:
                del_target_id = st.text_input("Nhập Mã Giao Dịch cần xóa:", value=st.session_state.get("del_active_id", ""))
            with d2:
                st.write("")
                st.write("")
                btn_find_del = st.form_submit_button("🔍 Tìm kiếm để xóa", type="primary")

        if btn_find_del or "del_active_id" in st.session_state:
            search_id = del_target_id.strip() if btn_find_del else st.session_state.get("del_active_id", "")
            if search_id:
                st.session_state["del_active_id"] = search_id
                with st.spinner(f"Đang kiểm tra giao dịch {search_id}..."):
                    df_del, err_del = db.query_phoenix_df(queries.sql_get_record_by_id(search_id))

                if err_del:
                    st.error(f"Lỗi: {err_del}")
                elif df_del is None or df_del.empty:
                    st.warning(f"Không tìm thấy giao dịch '{search_id}' trong hệ thống.")
                else:
                    st.info(f"Bản ghi tìm thấy cho mã **{search_id}**:")
                    st.dataframe(formatting.format_giao_dich_table(df_del), use_container_width=True)

                    st.markdown("---")
                    st.markdown("<h5 style='color: #DC2626;'>⚠️ Xác nhận thao tác xóa:</h5>", unsafe_allow_html=True)
                    confirm_del = st.checkbox(
                        f"Tôi xác nhận muốn xóa vĩnh viễn giao dịch '{search_id}' khỏi hệ thống Phoenix/HBase.",
                        value=False,
                        key=f"chk_confirm_delete_{search_id}",
                    )

                    btn_do_delete = st.button("🚨 Xác nhận Xóa Vĩnh Viễn (DELETE)", type="primary", disabled=not confirm_del)

                    if btn_do_delete:
                        del_sql = queries.sql_delete_transaction(search_id)
                        with st.spinner(f"Đang xóa bản ghi {search_id}..."):
                            ok_d, msg_d = db.execute_phoenix_sql(del_sql)

                        if ok_d:
                            st.cache_data.clear()
                            st.session_state["del_active_id"] = ""
                            st.success(f"✅ Đã xóa thành công giao dịch '{search_id}' khỏi HBase!")
                            st.markdown("##### 📝 Câu lệnh SQL đã thực thi:")
                            st.code(del_sql, language="sql")
                        else:
                            st.error(f"Xóa thất bại: {msg_d}")


# =============================================================================
# TRANG 6: THỐNG KÊ (AGGREGATIONS)
# =============================================================================
elif selected_page == "📈 Thống kê":
    components.render_header()
    st.subheader("📈 Thống Kê & Báo Cáo Gom Nhóm (Aggregate Queries)")

    stat_type = st.radio(
        "Chọn báo cáo thống kê:",
        options=[
            "1. Thống kê theo khu vực (Doanh thu & Số lượng)",
            "2. Top 5 sản phẩm bán nhiều nhất",
            "3. Top 5 khách hàng có tổng giá trị giao dịch cao nhất",
        ],
        horizontal=True,
    )

    if stat_type.startswith("1."):
        st.markdown("##### 📍 Doanh Thu & Số Lượng Theo Khu Vực")
        st.code(queries.SQL_AGGREGATE_REGION, language="sql")

        with st.spinner("Đang tổng hợp dữ liệu theo khu vực..."):
            df_reg, err_reg = db.query_phoenix_df(queries.SQL_AGGREGATE_REGION)

        if err_reg:
            st.error(f"Lỗi: {err_reg}")
        elif df_reg is not None and not df_reg.empty:
            df_reg_display = df_reg.copy()
            df_reg_display["SO_GIAO_DICH"] = df_reg_display["SO_GIAO_DICH"].map(formatting.format_number)
            df_reg_display["TONG_SO_LUONG"] = df_reg_display["TONG_SO_LUONG"].map(formatting.format_number)
            df_reg_display["TONG_DOANH_THU_HIEN_THI"] = df_reg_display["TONG_DOANH_THU"].map(formatting.format_currency)

            rename_r = {
                "KHU_VUC": "Khu Vực",
                "SO_GIAO_DICH": "Số Giao Dịch",
                "TONG_SO_LUONG": "Tổng Số Lượng Bán",
                "TONG_DOANH_THU_HIEN_THI": "Tổng Doanh Thu",
            }
            st.dataframe(df_reg_display[["KHU_VUC", "SO_GIAO_DICH", "TONG_SO_LUONG", "TONG_DOANH_THU_HIEN_THI"]].rename(columns=rename_r), use_container_width=True)

            # Biểu đồ doanh thu
            df_reg["TONG_DOANH_THU"] = pd.to_numeric(df_reg["TONG_DOANH_THU"], errors="coerce").fillna(0)
            st.bar_chart(df_reg, x="KHU_VUC", y="TONG_DOANH_THU", color="#1E88E5")
        else:
            st.info("Chưa có dữ liệu thống kê.")

    elif stat_type.startswith("2."):
        st.markdown("##### 📦 Top 5 Sản Phẩm Bán Nhiều Nhất")
        st.code(queries.SQL_AGGREGATE_TOP_PRODUCTS, language="sql")

        with st.spinner("Đang tính toán sản phẩm bán chạy nhất..."):
            df_prod, err_prod = db.query_phoenix_df(queries.SQL_AGGREGATE_TOP_PRODUCTS)

        if err_prod:
            st.error(f"Lỗi: {err_prod}")
        elif df_prod is not None and not df_prod.empty:
            df_p_display = df_prod.copy()
            df_p_display["TONG_SO_LUONG_HIEN_THI"] = df_p_display["TONG_SO_LUONG"].map(formatting.format_number)
            rename_p = {"MA_SAN_PHAM": "Mã Sản Phẩm", "TONG_SO_LUONG_HIEN_THI": "Tổng Số Lượng Đã Bán"}
            st.dataframe(df_p_display[["MA_SAN_PHAM", "TONG_SO_LUONG_HIEN_THI"]].rename(columns=rename_p), use_container_width=True)

            df_prod["TONG_SO_LUONG"] = pd.to_numeric(df_prod["TONG_SO_LUONG"], errors="coerce").fillna(0)
            st.bar_chart(df_prod, x="MA_SAN_PHAM", y="TONG_SO_LUONG", color="#43A047")
        else:
            st.info("Chưa có dữ liệu sản phẩm.")

    elif stat_type.startswith("3."):
        st.markdown("##### 👑 Top 5 Khách Hàng VIP (Tổng Chi Tiêu Cao Nhất)")
        st.code(queries.SQL_AGGREGATE_TOP_CUSTOMERS, language="sql")

        with st.spinner("Đang tính toán chi tiêu khách hàng..."):
            df_cust, err_cust = db.query_phoenix_df(queries.SQL_AGGREGATE_TOP_CUSTOMERS)

        if err_cust:
            st.error(f"Lỗi: {err_cust}")
        elif df_cust is not None and not df_cust.empty:
            df_c_display = df_cust.copy()
            df_c_display["TONG_GIA_TRI_HIEN_THI"] = df_c_display["TONG_GIA_TRI"].map(formatting.format_currency)
            rename_c = {"MA_KHACH_HANG": "Mã Khách Hàng", "TONG_GIA_TRI_HIEN_THI": "Tổng Giá Trị Giao Dịch"}
            st.dataframe(df_c_display[["MA_KHACH_HANG", "TONG_GIA_TRI_HIEN_THI"]].rename(columns=rename_c), use_container_width=True)

            df_cust["TONG_GIA_TRI"] = pd.to_numeric(df_cust["TONG_GIA_TRI"], errors="coerce").fillna(0)
            st.bar_chart(df_cust, x="MA_KHACH_HANG", y="TONG_GIA_TRI", color="#FB8C00")
        else:
            st.info("Chưa có dữ liệu khách hàng.")


# =============================================================================
# TRANG 7: INDEX VÀ EXPLAIN (COVERED SECONDARY INDEX)
# =============================================================================
elif selected_page == "⚡ Index và EXPLAIN":
    components.render_header()
    st.subheader("⚡ Tối Ưu Hóa Truy Vấn Với Secondary Covered Index")
    st.caption("Minh họa sự khác biệt giữa Full Table Scan và Range Scan trên Phoenix Index.")

    # 1. Trạng thái Index hiện tại
    with st.spinner("Đang kiểm tra trạng thái Secondary Index..."):
        idx_exists = db.check_index_exists("IDX_GIAO_DICH_KHU_VUC")

    if idx_exists:
        st.success("✅ Trạng thái Index: `IDX_GIAO_DICH_KHU_VUC` ĐANG TỒN TẠI trên HBase.")
    else:
        st.warning("⚠️ Trạng thái Index: `IDX_GIAO_DICH_KHU_VUC` CHƯA TỒN TẠI (Đang quét Full Table Scan).")

    st.markdown("---")

    # 2. Các hành động Index & EXPLAIN (chỉ chạy khi nhấn nút)
    col_act1, col_act2 = st.columns(2)

    with col_act1:
        st.markdown("##### 🔍 Kế Hoạch Thực Thi (EXPLAIN)")
        btn_explain_standard = st.button("Chạy EXPLAIN truy vấn chuẩn", use_container_width=True)
        btn_explain_hint = st.button("Chạy EXPLAIN với Index Hint (/*+ INDEX */)", use_container_width=True)

    with col_act2:
        st.markdown("##### 🛠️ Quản Trị Chỉ Mục (Index DDL)")
        btn_create_idx = st.button("➕ Tạo Index IDX_GIAO_DICH_KHU_VUC (INCLUDE)", type="primary", use_container_width=True)
        confirm_drop_idx = st.checkbox("Xác nhận muốn xóa Index", value=False)
        btn_drop_idx = st.button("🗑️ Xóa Index IDX_GIAO_DICH_KHU_VUC", disabled=not confirm_drop_idx, use_container_width=True)

    st.markdown("---")

    # Xử lý nút Tạo Index
    if btn_create_idx:
        if idx_exists:
            st.info("Index `IDX_GIAO_DICH_KHU_VUC` đã tồn tại trước đó.")
        else:
            st.code(queries.SQL_CREATE_COVERED_INDEX, language="sql")
            with st.spinner("Đang tạo Covered Index trên HBase (có thể mất 10-15s)..."):
                ok_cr, out_cr = db.execute_phoenix_sql(queries.SQL_CREATE_COVERED_INDEX, timeout=40)
            if ok_cr:
                st.cache_data.clear()
                st.success("✅ Đã tạo thành công Covered Index `IDX_GIAO_DICH_KHU_VUC`!")
                st.rerun()
            else:
                st.error(f"Lỗi tạo Index: {out_cr}")

    # Xử lý nút Xóa Index
    if btn_drop_idx:
        st.code(queries.SQL_DROP_INDEX, language="sql")
        with st.spinner("Đang xóa Index khỏi HBase..."):
            ok_dr, out_dr = db.execute_phoenix_sql(queries.SQL_DROP_INDEX, timeout=25)
        if ok_dr:
            st.cache_data.clear()
            st.success("✅ Đã xóa thành công Index `IDX_GIAO_DICH_KHU_VUC`!")
            st.rerun()
        else:
            st.error(f"Lỗi xóa Index: {out_dr}")

    # Xử lý EXPLAIN chuẩn
    if btn_explain_standard:
        st.markdown("##### 📋 Câu lệnh truy vấn cần phân tích:")
        st.code(queries.SQL_EXPLAIN_WITHOUT_INDEX, language="sql")

        with st.spinner("Đang lấy kế hoạch thực thi từ Phoenix Query Optimizer..."):
            df_exp, err_exp = db.query_phoenix_df(queries.SQL_EXPLAIN_WITHOUT_INDEX)

        if err_exp:
            st.error(f"Lỗi EXPLAIN: {err_exp}")
        elif df_exp is not None and not df_exp.empty:
            st.markdown("##### 📌 Kết Quả EXPLAIN:")
            plan_text = "\n".join(str(row.get("PLAN", "")) for _, row in df_exp.iterrows())
            st.code(plan_text, language="text")

            # Phân tích kết quả
            if "RANGE SCAN" in plan_text:
                st.success("🎯 **Đánh giá tối ưu:** Phoenix đang sử dụng **RANGE SCAN** trên bảng chỉ mục `IDX_GIAO_DICH_KHU_VUC`! Hiệu năng tối đa.")
            else:
                st.warning("⚠️ **Đánh giá tối ưu:** Phoenix đang sử dụng **PARALLEL FULL SCAN** trên toàn bộ bảng chính `GIAO_DICH`.")

    # Xử lý EXPLAIN với Index Hint
    if btn_explain_hint:
        st.markdown("##### 📋 Truy vấn ép sử dụng Index Hint:")
        st.code(queries.SQL_EXPLAIN_WITH_INDEX_HINT, language="sql")

        with st.spinner("Đang thực thi EXPLAIN với Index Hint..."):
            df_hint, err_hint = db.query_phoenix_df(queries.SQL_EXPLAIN_WITH_INDEX_HINT)

        if err_hint:
            st.error(f"Lỗi EXPLAIN Index Hint: {err_hint}")
        elif df_hint is not None and not df_hint.empty:
            st.markdown("##### 📌 Kết Quả Kế Hoạch Với Index Hint:")
            hint_plan = "\n".join(str(row.get("PLAN", "")) for _, row in df_hint.iterrows())
            st.code(hint_plan, language="text")


# =============================================================================
# TRANG 8: TRẠNG THÁI HỆ THỐNG (SYSTEM HEALTH)
# =============================================================================
elif selected_page == "🖥️ Trạng thái hệ thống":
    components.render_header()
    st.subheader("🖥️ Trạng Thái Hạ Tầng & Dịch Vụ")

    col_h1, col_h2 = st.columns([3, 1])
    with col_h1:
        st.caption("Kiểm tra sức khỏe kết nối giữa Phoenix SQL Layer, HMaster và ZooKeeper.")
    with col_h2:
        if st.button("🔄 Kiểm tra lại", type="primary", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

    with st.spinner("Đang kiểm tra toàn diện trạng thái hệ thống..."):
        sys_status = cached_system_status()

    s1, s2, s3, s4 = st.columns(4)
    with s1:
        zk_status = "🟢 Hoạt động" if sys_status["zookeeper_alive"] else "🔴 Mất kết nối"
        st.metric("ZooKeeper (Port 2181)", zk_status)
    with s2:
        hm_status = "🟢 Hoạt động" if sys_status["hmaster_alive"] else "🔴 Chưa chạy"
        st.metric("HBase HMaster", hm_status)
    with s3:
        ph_status = "🟢 Sẵn sàng" if sys_status["phoenix_connected"] else "🔴 Lỗi"
        st.metric("Phoenix Connection", ph_status)
    with s4:
        tb_status = f"🟢 Có ({sys_status['record_count']} dòng)" if sys_status["table_exists"] else "🔴 Chưa tạo"
        st.metric("Bảng GIAO_DICH", tb_status)

    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

    st.markdown("##### 📋 Chi Tiết Môi Trường Triển Khai:")
    st.table(
        pd.DataFrame(
            [
                {"Thành phần": "Hệ điều hành", "Giá trị": "Ubuntu 22.04 LTS trên WSL2"},
                {"Thành phần": "Apache HBase", "Giá trị": "2.5.15-hadoop3 (Cổng ZK 2181)"},
                {"Thành phần": "Apache Phoenix", "Giá trị": "5.2.2 (SQLLine Client Bridge)"},
                {"Thành phần": "Java OpenJDK", "Giá trị": "11.0.32 (JAVA_HOME /usr/lib/jvm/java-11-openjdk-amd64)"},
                {"Thành phần": "Cơ chế Salt Buckets", "Giá trị": "SALT_BUCKETS = 8 (Phân tán đều trên HBase Regions)"},
                {"Thành phần": "Secondary Covered Index", "Giá trị": "IDX_GIAO_DICH_KHU_VUC (" + ("Đã bật" if sys_status["index_exists"] else "Chưa tạo") + ")"},
            ]
        )
    )

    if sys_status.get("error_message"):
        with st.expander("Thông tin cảnh báo / lỗi hệ thống"):
            st.warning(sys_status["error_message"])
