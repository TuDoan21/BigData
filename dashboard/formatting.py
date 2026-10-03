"""
=============================================================================
MODULE: formatting.py
MỤC ĐÍCH: Tiện ích định dạng số, tiền tệ VNĐ và thời gian hiển thị chuẩn hóa
- Chuẩn hóa tiền tệ: '28.500.000 VNĐ', không để hiển thị dạng số mũ 2.85E+7
- Chuẩn hóa số lượng: Dấu phân cách hàng nghìn '1.250'
- Chuẩn hóa thời gian: 'dd/MM/yyyy HH:mm:ss'
- Giá trị NULL hiển thị thành dấu '—'
- Tối ưu hóa hiệu năng: Hạn chế copy DataFrame, xử lý vector hóa với Pandas 2.x & 3.x
- Tuyệt đối không dùng DataFrame.applymap() (đã bị khai tử)
=============================================================================
"""

import decimal
from typing import Any
import pandas as pd


def format_currency(val: Any, null_as_dash: bool = False, symbol: str = "VNĐ") -> str:
    """
    Định dạng số tiền thống nhất chuẩn quốc gia: Việt Nam Đồng (VNĐ).
    Xử lý an toàn: None, NaN, Decimal, Float, chuỗi dạng số mũ khoa học (2.85E+7).
    Ví dụ: 14500000 -> '14.500.000 VNĐ'.
    """
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return "—" if null_as_dash else "0 VNĐ"

    try:
        if isinstance(val, decimal.Decimal):
            val_float = float(val)
        elif isinstance(val, str):
            val_cleaned = val.strip().replace("'", "").replace('"', "")
            if not val_cleaned or val_cleaned.lower() in ("null", "none", "nan"):
                return "—" if null_as_dash else "0 VNĐ"
            val_float = float(val_cleaned)
        else:
            val_float = float(val)

        return f"{val_float:,.0f}".replace(",", ".") + " VNĐ"
    except (ValueError, TypeError, decimal.InvalidOperation):
        return "—" if null_as_dash else "0 VNĐ"


def format_currency_compact(val: Any) -> str:
    """Định dạng rút gọn công nghệ cao cho KPI: tỷ / triệu VNĐ."""
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return "0 VNĐ"
    try:
        num = float(val)
        abs_num = abs(num)
        if abs_num >= 1_000_000_000:
            return f"{num / 1_000_000_000:,.2f} tỷ VNĐ"
        elif abs_num >= 1_000_000:
            return f"{num / 1_000_000:,.1f} tr VNĐ"
        else:
            return f"{num:,.0f}".replace(",", ".") + " VNĐ"
    except Exception:
        return "0 VNĐ"


def format_number(val: Any, null_as_dash: bool = False) -> str:
    """
    Định dạng số nguyên có dấu chấm phân cách hàng nghìn (ví dụ: '1.250').
    """
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return "—" if null_as_dash else "0"

    try:
        if isinstance(val, decimal.Decimal):
            val_int = int(round(float(val)))
        elif isinstance(val, str):
            val_cleaned = val.strip().replace("'", "").replace('"', "")
            if not val_cleaned or val_cleaned.lower() in ("null", "none", "nan"):
                return "—" if null_as_dash else "0"
            val_int = int(round(float(val_cleaned)))
        else:
            val_int = int(round(float(val)))

        return f"{val_int:,}".replace(",", ".")
    except (ValueError, TypeError, decimal.InvalidOperation):
        return "—" if null_as_dash else "0"


def format_datetime(val: Any) -> str:
    """
    Chuẩn hóa thời gian hiển thị theo định dạng 'dd/MM/yyyy HH:mm:ss'.
    Ví dụ: '2026-03-01 14:30:00' -> '01/03/2026 14:30:00'.
    Giá trị NULL hoặc rỗng trả về '—'.
    """
    if val is None or pd.isna(val):
        return "—"

    s = str(val).strip().replace("'", "").replace('"', "")
    if not s or s.lower() in ("null", "none", "nan", "nat", ""):
        return "—"

    if s.endswith(".0"):
        s = s[:-2]

    try:
        dt = pd.to_datetime(s)
        return dt.strftime("%d/%m/%Y %H:%M:%S")
    except Exception:
        return s


def format_null(val: Any) -> Any:
    """Chuyển đổi giá trị NULL, NaN, None, rỗng thành ký tự gạch ngang '—'."""
    if val is None or pd.isna(val):
        return "—"
    if isinstance(val, str):
        s = val.strip().replace("'", "").replace('"', "")
        if not s or s.lower() in ("null", "none", "nan", "nat"):
            return "—"
        return s
    return val


def format_giao_dich_table(df: pd.DataFrame, symbol: str = "VNĐ") -> pd.DataFrame:
    """
    Chuẩn bị DataFrame để hiển thị đẹp trên giao diện Streamlit:
    - Không làm thay đổi kiểu dữ liệu gốc của DataFrame đầu vào (tránh lỗi biểu đồ).
    - Tạo các cột đã được format tiền tệ, số lượng và thời gian cho bảng hiển thị.
    - Xử lý vector hóa để tối ưu tốc độ render.
    """
    if df.empty:
        return df.copy()

    df_display = df.copy()

    # Làm sạch tên cột
    df_display.columns = [c.strip().replace("'", "").replace('"', "") for c in df_display.columns]

    # Tính toán thành tiền nếu chưa có (vectorized)
    if "SO_LUONG" in df_display.columns and "DON_GIA" in df_display.columns and "THANH_TIEN" not in df_display.columns:
        so_luong_num = pd.to_numeric(df_display["SO_LUONG"], errors="coerce").fillna(0)
        don_gia_num = pd.to_numeric(df_display["DON_GIA"], errors="coerce").fillna(0.0)
        df_display["THANH_TIEN"] = so_luong_num * don_gia_num

    # Định dạng các cột hiển thị
    if "SO_LUONG" in df_display.columns:
        df_display["SO_LUONG_HIEN_THI"] = df_display["SO_LUONG"].map(lambda x: format_number(x, null_as_dash=True))

    if "DON_GIA" in df_display.columns:
        df_display["DON_GIA_HIEN_THI"] = df_display["DON_GIA"].map(lambda x: format_currency(x, null_as_dash=True, symbol=symbol))

    if "THANH_TIEN" in df_display.columns:
        df_display["THANH_TIEN_HIEN_THI"] = df_display["THANH_TIEN"].map(lambda x: format_currency(x, null_as_dash=True, symbol=symbol))

    if "THOI_GIAN" in df_display.columns:
        df_display["THOI_GIAN_HIEN_THI"] = df_display["THOI_GIAN"].map(format_datetime)

    for col in ["MA_GIAO_DICH", "MA_KHACH_HANG", "MA_SAN_PHAM", "KHU_VUC"]:
        if col in df_display.columns:
            df_display[col] = df_display[col].map(format_null)

    return df_display
