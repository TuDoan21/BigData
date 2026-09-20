"""
=============================================================================
MODULE: formatting.py
MỤC ĐÍCH: Tiện ích định dạng số, tiền tệ VNĐ và thời gian hiển thị chuẩn hóa
Không dùng DataFrame.applymap() (đã bị deprecate trong Pandas)
=============================================================================
"""

import decimal
from typing import Any
import pandas as pd


def format_currency(val: Any) -> str:
    """
    Định dạng số tiền theo chuẩn Việt Nam: '28.500.000 VNĐ'
    Xử lý an toàn: None, NaN, Decimal, Float, chuỗi dạng khoa học (2.85E+7).
    """
    if val is None:
        return "0 VNĐ"
    if isinstance(val, float) and pd.isna(val):
        return "0 VNĐ"

    try:
        if isinstance(val, decimal.Decimal):
            val_float = float(val)
        elif isinstance(val, str):
            val_cleaned = val.strip().replace("'", "").replace('"', "")
            if not val_cleaned:
                return "0 VNĐ"
            val_float = float(val_cleaned)
        else:
            val_float = float(val)

        return f"{val_float:,.0f}".replace(",", ".") + " VNĐ"
    except (ValueError, TypeError, decimal.InvalidOperation):
        return "0 VNĐ"


def format_number(val: Any) -> str:
    """
    Định dạng số nguyên có dấu chấm phân cách hàng nghìn (ví dụ: '1.250').
    """
    if val is None:
        return "0"
    if isinstance(val, float) and pd.isna(val):
        return "0"

    try:
        if isinstance(val, decimal.Decimal):
            val_int = int(round(float(val)))
        elif isinstance(val, str):
            val_cleaned = val.strip().replace("'", "").replace('"', "")
            if not val_cleaned:
                return "0"
            val_int = int(round(float(val_cleaned)))
        else:
            val_int = int(round(float(val)))

        return f"{val_int:,}".replace(",", ".")
    except (ValueError, TypeError, decimal.InvalidOperation):
        return "0"


def format_datetime(val: Any) -> str:
    """
    Chuẩn hóa chuỗi thời gian hiển thị (bỏ phần milli/nanoseconds dư thừa).
    """
    if val is None or pd.isna(val):
        return "N/A"
    s = str(val).strip().replace("'", "").replace('"', "")
    if s.endswith(".0"):
        s = s[:-2]
    return s


def format_giao_dich_table(df: pd.DataFrame) -> pd.DataFrame:
    """
    Chuẩn bị DataFrame để hiển thị đẹp trên giao diện Streamlit:
    - Không làm thay đổi kiểu dữ liệu gốc của DataFrame đầu vào (tránh lỗi biểu đồ).
    - Tạo các cột đã được format tiền tệ cho bảng hiển thị.
    """
    if df.empty:
        return df.copy()

    df_display = df.copy()

    # Làm sạch tên cột
    df_display.columns = [c.strip().replace("'", "").replace('"', "") for c in df_display.columns]

    if "DON_GIA" in df_display.columns:
        df_display["DON_GIA_HIEN_THI"] = df_display["DON_GIA"].map(format_currency)

    if "THANH_TIEN" in df_display.columns:
        df_display["THANH_TIEN_HIEN_THI"] = df_display["THANH_TIEN"].map(format_currency)
    elif "DON_GIA" in df_display.columns and "SO_LUONG" in df_display.columns:
        so_luong_num = pd.to_numeric(df_display["SO_LUONG"], errors="coerce").fillna(0)
        don_gia_num = pd.to_numeric(df_display["DON_GIA"], errors="coerce").fillna(0.0)
        df_display["THANH_TIEN_HIEN_THI"] = (so_luong_num * don_gia_num).map(format_currency)

    if "THOI_GIAN" in df_display.columns:
        df_display["THOI_GIAN_HIEN_THI"] = df_display["THOI_GIAN"].map(format_datetime)

    return df_display
