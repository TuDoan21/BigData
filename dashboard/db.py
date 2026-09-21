"""
=============================================================================
MODULE: db.py
MỤC ĐÍCH: Quản lý kết nối Apache Phoenix qua SQLLine Bridge trên nền HBase.
- Quản lý kết nối tái sử dụng: @st.cache_resource get_connection()
- Lớp PhoenixConnection & PhoenixCursor chuẩn context manager
- Socket pre-check siêu nhanh (< 4 ms) tránh treo giao diện khi HBase tắt
- Đo lường thời gian thực thi (ms)
- Tương thích kép: Ubuntu WSL trực tiếp và Windows PowerShell qua WSL bridge
- Xử lý ngắt kết nối an toàn, thử kết nối lại đúng 1 lần (không vòng lặp vô hạn)
=============================================================================
"""

import io
import os
import socket
import subprocess
import sys
import time
import pandas as pd
import streamlit as st

# Đường dẫn mặc định tương ứng trên Ubuntu WSL
SQLLINE_PATH = "/mnt/d/2026/BigData/phoenix/bin/sqlline.py"
JAVA_HOME_DEFAULT = "/usr/lib/jvm/java-11-openjdk-amd64"
ZOOKEEPER_HOST = "127.0.0.1"
ZOOKEEPER_PORT = 2181


def is_zookeeper_alive(host: str = ZOOKEEPER_HOST, port: int = ZOOKEEPER_PORT, timeout: float = 0.5) -> bool:
    """
    Kiểm tra nhanh (< 0.5s) cổng ZooKeeper 2181 xem có mở hay không.
    Ngăn chặn hoàn toàn việc gọi SQLLine bị treo khi HBase chưa chạy.
    """
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except (OSError, socket.timeout):
        return False


def format_db_error(raw_err: str) -> str:
    """Chuyển đổi các mã lỗi kỹ thuật Phoenix/HBase thành thông báo tiếng Việt dễ hiểu."""
    if not raw_err:
        return "Lỗi không xác định."
    if "TableNotFoundException" in raw_err or "ERROR 1012" in raw_err:
        return "Bảng dữ liệu không tồn tại trong Apache Phoenix."
    if "TableAlreadyExistsException" in raw_err or "ERROR 1013" in raw_err:
        return "Bảng hoặc Index này đã tồn tại trong hệ thống."
    if "Connection refused" in raw_err or "2181" in raw_err:
        return "Không thể kết nối đến HBase/ZooKeeper (Cổng 2181 chưa mở). Vui lòng khởi động HBase."
    if "Quá thời gian chờ" in raw_err or "TimeoutExpired" in raw_err:
        return "Truy vấn bị quá thời gian chờ (Timeout). Hệ thống đang xử lý tác vụ nặng hoặc nghẽn mạng."
    if "ConstraintViolationException" in raw_err:
        return "Vi phạm ràng buộc dữ liệu hoặc trùng khóa chính (Primary Key)."
    return raw_err


def extract_csv_from_line(line: str) -> str | None:
    """Trích xuất phần chuỗi CSV chuẩn xác từ một dòng output của SQLLine."""
    line = line.strip()
    idx_single = line.find("'")
    idx_double = line.find('"')
    idx = -1
    if idx_single != -1 and idx_double != -1:
        idx = min(idx_single, idx_double)
    elif idx_single != -1:
        idx = idx_single
    elif idx_double != -1:
        idx = idx_double

    if idx != -1:
        csv_part = line[idx:].strip()
        if (csv_part.startswith("'") and csv_part.endswith("'")) or (csv_part.startswith('"') and csv_part.endswith('"')):
            return csv_part
    return None


def parse_sqlline_csv_blocks(raw_output: str) -> list[pd.DataFrame]:
    """
    Phân tích toàn bộ các khối kết quả CSV trong output của SQLLine thành danh sách DataFrame.
    Hỗ trợ gộp đa truy vấn trong 1 phiên SQLLine.
    """
    if not raw_output:
        return []

    dataframes: list[pd.DataFrame] = []
    lines = raw_output.splitlines()
    current_block: list[str] = []

    for line in lines:
        sline = line.strip()
        csv_line = extract_csv_from_line(line)

        if sline.startswith("0: jdbc:") or "rows selected" in sline or "row selected" in sline:
            if csv_line:
                if current_block:
                    try:
                        csv_text = "\n".join(current_block)
                        df = pd.read_csv(io.StringIO(csv_text), quotechar="'", skipinitialspace=True)
                        df.columns = [c.strip().replace("'", "").replace('"', "") for c in df.columns]
                        df.replace({"null": None, "'null'": None}, inplace=True)
                        dataframes.append(df)
                    except Exception:
                        pass
                    current_block = []
                current_block.append(csv_line)
            else:
                if current_block:
                    try:
                        csv_text = "\n".join(current_block)
                        df = pd.read_csv(io.StringIO(csv_text), quotechar="'", skipinitialspace=True)
                        df.columns = [c.strip().replace("'", "").replace('"', "") for c in df.columns]
                        df.replace({"null": None, "'null'": None}, inplace=True)
                        dataframes.append(df)
                    except Exception:
                        pass
                    current_block = []
        else:
            if csv_line:
                current_block.append(csv_line)

    if current_block:
        try:
            csv_text = "\n".join(current_block)
            df = pd.read_csv(io.StringIO(csv_text), quotechar="'", skipinitialspace=True)
            df.columns = [c.strip().replace("'", "").replace('"', "") for c in df.columns]
            df.replace({"null": None, "'null'": None}, inplace=True)
            dataframes.append(df)
        except Exception:
            pass

    return dataframes


# =============================================================================
# LỚP KẾT NỐI VÀ CON TRỎ CHUẨN (CONNECTION & CURSOR ABSTRACTION)
# =============================================================================

class PhoenixConnection:
    """
    Đại diện cho kết nối Apache Phoenix trên nền HBase.
    Được quản lý thông qua @st.cache_resource để tái sử dụng trong toàn bộ phiên ứng dụng.
    """
    def __init__(self, host: str = ZOOKEEPER_HOST, port: int = ZOOKEEPER_PORT):
        self.host = host
        self.port = port
        self._is_closed = False
        self.created_at = time.time()
        self.total_queries_executed = 0

    def is_alive(self) -> bool:
        """Kiểm tra xem kết nối đến ZooKeeper/HBase có còn khả dụng hay không."""
        if self._is_closed:
            return False
        return is_zookeeper_alive(self.host, self.port)

    def close(self):
        """Đóng kết nối."""
        self._is_closed = True

    def cursor(self) -> "PhoenixCursor":
        """Khởi tạo con trỏ thực thi mới."""
        if not self.is_alive():
            raise ConnectionError("Kết nối Apache Phoenix/ZooKeeper hiện không khả dụng.")
        return PhoenixCursor(self)

    def execute_raw(self, sql_commands: str | list[str], timeout: int = 30) -> tuple[bool, str]:
        """Thực thi câu lệnh SQL qua SQLLine bridge."""
        if not self.is_alive():
            return False, "Không thể kết nối Apache Phoenix. Hãy kiểm tra HMaster và ZooKeeper (Cổng 2181 chưa mở)."

        if isinstance(sql_commands, list):
            body = "\n".join(cmd.strip().rstrip(";") + ";" for cmd in sql_commands if cmd.strip())
        else:
            body = sql_commands.strip()
            if not body.endswith(";"):
                body += ";"

        input_payload = f"""!set outputformat csv
{body}
!quit
"""
        self.total_queries_executed += 1

        try:
            if sys.platform == "win32":
                wsl_cmd = f"export JAVA_HOME={JAVA_HOME_DEFAULT} && python3 {SQLLINE_PATH} -fc localhost"
                proc = subprocess.run(
                    ["wsl", "-e", "bash", "-c", wsl_cmd],
                    input=input_payload,
                    text=True,
                    capture_output=True,
                    timeout=timeout,
                )
            else:
                env = os.environ.copy()
                if "JAVA_HOME" not in env or not env["JAVA_HOME"]:
                    env["JAVA_HOME"] = JAVA_HOME_DEFAULT
                python_bin = sys.executable if sys.executable else "python3"
                proc = subprocess.run(
                    [python_bin, SQLLINE_PATH, "-fc", "localhost"],
                    input=input_payload,
                    text=True,
                    capture_output=True,
                    timeout=timeout,
                    env=env,
                )

            if proc.returncode != 0:
                err = proc.stderr or proc.stdout
                return False, f"Lỗi SQLLine (Exit {proc.returncode}):\n{err}"
            return True, proc.stdout
        except subprocess.TimeoutExpired:
            return False, f"Lỗi: Quá thời gian chờ phản hồi ({timeout}s) từ Phoenix SQLLine."
        except Exception as e:
            return False, f"Lỗi ngoại lệ khi gọi SQLLine: {str(e)}"


class PhoenixCursor:
    """
    Con trỏ truy vấn Apache Phoenix hỗ trợ Context Manager.
    Không bao giờ được cache cursor. Luôn đóng cursor sau khi hoàn tất.
    """
    def __init__(self, connection: PhoenixConnection):
        self.connection = connection
        self._closed = False
        self._last_output = ""
        self._last_dfs: list[pd.DataFrame] = []
        self._last_error: str | None = None
        self._execution_time_ms = 0.0

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        """Đóng con trỏ và giải phóng bộ đệm."""
        self._closed = True
        self._last_dfs = []

    def execute(self, sql: str | list[str], timeout: int = 30) -> "PhoenixCursor":
        """Thực thi câu lệnh SQL và đo thời gian chạy chính xác."""
        if self._closed:
            raise RuntimeError("Con trỏ đã bị đóng.")

        t0 = time.perf_counter()
        ok, out = self.connection.execute_raw(sql, timeout=timeout)
        self._execution_time_ms = (time.perf_counter() - t0) * 1000.0
        self._last_output = out

        if not ok:
            self._last_error = format_db_error(out)
            self._last_dfs = []
        else:
            self._last_error = None
            self._last_dfs = parse_sqlline_csv_blocks(out)

        return self

    def fetchone_df(self) -> pd.DataFrame:
        """Trả về DataFrame đầu tiên nhận được từ kết quả truy vấn."""
        if self._last_error:
            raise RuntimeError(self._last_error)
        if self._last_dfs:
            return self._last_dfs[0]
        return pd.DataFrame()

    def fetchall_dfs(self) -> list[pd.DataFrame]:
        """Trả về danh sách toàn bộ các DataFrame của phiên truy vấn gộp."""
        if self._last_error:
            raise RuntimeError(self._last_error)
        return self._last_dfs

    @property
    def execution_time_ms(self) -> float:
        return self._execution_time_ms

    @property
    def error(self) -> str | None:
        return self._last_error


# =============================================================================
# HÀM QUẢN LÝ KẾT NỐI TẬP TRUNG VỚI STREAMLIT CACHE_RESOURCE
# =============================================================================

@st.cache_resource(show_spinner=False)
def get_connection() -> PhoenixConnection:
    """
    Tạo và lưu trữ kết nối Phoenix duy nhất trong toàn bộ vòng đời ứng dụng.
    Tái sử dụng kết nối nếu còn sống. Tự động phục hồi đúng 1 lần nếu kết nối đứt.
    """
    conn = PhoenixConnection()
    return conn


def get_active_connection() -> PhoenixConnection:
    """
    Lấy kết nối hiện hành, kiểm tra liveness và tự động kết nối lại nếu bị đứt.
    Ngăn chặn vòng lặp kết nối lại vô hạn bằng cách thử tối đa 1 lần.
    """
    conn = get_connection()
    if not conn.is_alive():
        # Đóng kết nối cũ và xóa cache resource để tạo kết nối mới đúng 1 lần
        conn.close()
        st.cache_resource.clear()
        conn = get_connection()
    return conn


# =============================================================================
# CÁC HÀM TIỆN ÍCH TRUY VẤN TỐI ƯU
# =============================================================================

def execute_phoenix_sql(sql_commands: str | list[str], timeout: int = 30) -> tuple[bool, str]:
    """Thực thi qua kết nối dùng chung."""
    conn = get_active_connection()
    return conn.execute_raw(sql_commands, timeout=timeout)


def query_phoenix_df(sql: str, timeout: int = 30) -> tuple[pd.DataFrame | None, str | None]:
    """Thực thi 1 truy vấn SELECT và trả về (DataFrame, error_msg). Luôn đóng cursor bằng context manager."""
    conn = get_active_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, timeout=timeout)
            if cur.error:
                return None, cur.error
            return cur.fetchone_df(), None
    except Exception as e:
        return None, format_db_error(str(e))


def query_phoenix_df_timed(sql: str, timeout: int = 30) -> tuple[pd.DataFrame | None, str | None, float]:
    """Thực thi truy vấn có đo lường mili-giây. Luôn đóng cursor bằng context manager."""
    conn = get_active_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, timeout=timeout)
            if cur.error:
                return None, cur.error, cur.execution_time_ms
            return cur.fetchone_df(), None, cur.execution_time_ms
    except Exception as e:
        return None, format_db_error(str(e)), 0.0


def query_batch_dfs(sql_list: list[str], timeout: int = 35) -> tuple[list[pd.DataFrame], str | None, float]:
    """Thực thi gộp nhiều câu truy vấn trong 1 phiên SQLLine duy nhất. Tiết kiệm tối đa thời gian JVM."""
    conn = get_active_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql_list, timeout=timeout)
            if cur.error:
                return [], cur.error, cur.execution_time_ms
            return cur.fetchall_dfs(), None, cur.execution_time_ms
    except Exception as e:
        return [], format_db_error(str(e)), 0.0


def check_table_exists(table_name: str = "GIAO_DICH") -> bool:
    """Kiểm tra xem bảng có tồn tại trong Phoenix hay không."""
    if not is_zookeeper_alive():
        return False
    check_sql = f"SELECT 1 FROM {table_name} LIMIT 1;"
    df, err = query_phoenix_df(check_sql, timeout=10)
    return err is None


def get_all_indexes(data_table: str = "GIAO_DICH") -> list[dict]:
    """Lấy danh sách tất cả các Secondary Index hiện có từ SYSTEM.CATALOG."""
    if not is_zookeeper_alive():
        return []

    sql = f"""
    SELECT TABLE_NAME AS INDEX_NAME, DATA_TABLE_NAME, INDEX_TYPE, INDEX_STATE
    FROM SYSTEM.CATALOG
    WHERE TABLE_TYPE = 'i' AND DATA_TABLE_NAME = '{data_table}'
    ORDER BY TABLE_NAME;
    """
    df, err = query_phoenix_df(sql, timeout=15)
    if df is not None and not df.empty:
        return df.to_dict(orient="records")
    return []
