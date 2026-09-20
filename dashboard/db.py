"""
=============================================================================
MODULE: db.py
MỤC ĐÍCH: Quản lý kết nối Apache Phoenix qua SQLLine Bridge trên nền HBase.
- Socket pre-check siêu nhanh (< 0.5s) tránh treo giao diện khi HBase tắt.
- Tối ưu gộp đa truy vấn trong 1 phiên SQLLine.
- Parse CSV chuẩn xác, hỗ trợ COMMIT và quản lý timeout chặt chẽ.
=============================================================================
"""

import io
import os
import socket
import subprocess
import sys
import pandas as pd

# Đường dẫn mặc định tương ứng trên Ubuntu WSL
SQLLINE_PATH = "/mnt/d/2026/BigData/phoenix/bin/sqlline.py"
JAVA_HOME_DEFAULT = "/usr/lib/jvm/java-11-openjdk-amd64"
ZOOKEEPER_HOST = "127.0.0.1"
ZOOKEEPER_PORT = 2181


def is_zookeeper_alive(host: str = ZOOKEEPER_HOST, port: int = ZOOKEEPER_PORT, timeout: float = 0.6) -> bool:
    """
    Kiểm tra nhanh (< 0.6s) cổng ZooKeeper 2181 xem có mở hay không.
    Ngăn chặn hoàn toàn việc gọi SQLLine bị treo khi HBase chưa chạy.
    """
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except (OSError, socket.timeout):
        return False


def execute_phoenix_sql(sql_commands: str | list[str], timeout: int = 25) -> tuple[bool, str]:
    """
    Thực thi một hoặc chuỗi nhiều câu lệnh SQL trên Apache Phoenix thông qua SQLLine.
    - Cờ '-fc' (fastConnect) giúp tối ưu thời gian kết nối.
    - Tự động kiểm tra ZooKeeper trước khi khởi động tiến trình JVM.
    - Trả về: (success: bool, raw_output: str)
    """
    if not is_zookeeper_alive():
        return False, "Không thể kết nối Apache Phoenix. Hãy kiểm tra HMaster và ZooKeeper (Cổng 2181 chưa mở)."

    env = os.environ.copy()
    if "JAVA_HOME" not in env or not env["JAVA_HOME"]:
        env["JAVA_HOME"] = JAVA_HOME_DEFAULT

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

    python_bin = sys.executable if sys.executable else "python3"

    try:
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
    Hỗ trợ cả trường hợp chạy nhiều câu lệnh SELECT trong cùng một phiên SQLLine.
    """
    if not raw_output:
        return []

    dataframes: list[pd.DataFrame] = []
    lines = raw_output.splitlines()
    current_block: list[str] = []

    for line in lines:
        sline = line.strip()
        csv_line = extract_csv_from_line(line)

        # Kiểm tra nếu gặp dòng prompt của SQLLine hoặc thông báo dòng được chọn
        if sline.startswith("0: jdbc:") or "rows selected" in sline or "row selected" in sline:
            # Nếu dòng prompt đó CŨNG chứa phần đầu của CSV (ví dụ: ...'COL1','COL2')
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
                # Dòng prompt thuần túy kết thúc khối trước
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


def query_phoenix_df(sql: str, timeout: int = 25) -> tuple[pd.DataFrame | None, str | None]:
    """
    Thực thi 1 truy vấn SELECT và trả về DataFrame.
    Nếu bảng rỗng, trả về DataFrame rỗng.
    Nếu lỗi, trả về (None, error_msg).
    """
    ok, output = execute_phoenix_sql(sql, timeout=timeout)
    if not ok:
        return None, output

    dfs = parse_sqlline_csv_blocks(output)
    if dfs:
        return dfs[0], None

    return pd.DataFrame(), None


def check_table_exists(table_name: str = "GIAO_DICH") -> bool:
    """Kiểm tra xem bảng có tồn tại trong Phoenix hay không."""
    if not is_zookeeper_alive():
        return False
    check_sql = f"SELECT 1 FROM {table_name} LIMIT 1;"
    ok, output = execute_phoenix_sql(check_sql, timeout=15)
    if not ok:
        if "TableNotFoundException" in output or "ERROR 1012" in output:
            return False
    return ok


def check_index_exists(index_name: str = "IDX_GIAO_DICH_KHU_VUC") -> bool:
    """Kiểm tra xem index có tồn tại hay không."""
    if not is_zookeeper_alive():
        return False
    sql = f"""
    SELECT TABLE_NAME 
    FROM SYSTEM.CATALOG 
    WHERE TABLE_NAME = '{index_name}' AND TABLE_TYPE = 'i'
    LIMIT 1;
    """
    df, err = query_phoenix_df(sql, timeout=15)
    if df is not None and not df.empty:
        return True
    return False


def check_system_status() -> dict:
    """
    Kiểm tra toàn diện trạng thái hệ thống:
    - ZooKeeper (cổng 2181)
    - HMaster process
    - Kết nối Phoenix
    - Bảng GIAO_DICH và tổng số bản ghi
    - Secondary Index IDX_GIAO_DICH_KHU_VUC
    Tối ưu gộp kiểm tra bảng và index trong 1 phiên duy nhất để phản hồi nhanh.
    """
    status = {
        "zookeeper_alive": False,
        "hmaster_alive": False,
        "phoenix_connected": False,
        "table_exists": False,
        "index_exists": False,
        "record_count": 0,
        "error_message": None,
    }

    # 1. Kiểm tra ZooKeeper socket nhanh
    status["zookeeper_alive"] = is_zookeeper_alive()
    if not status["zookeeper_alive"]:
        status["error_message"] = "Không thể kết nối Apache Phoenix. Hãy kiểm tra HMaster và ZooKeeper (Cổng 2181 chưa mở)."
        return status

    # 2. Kiểm tra tiến trình HMaster
    try:
        jps_proc = subprocess.run(["jps"], text=True, capture_output=True, timeout=3)
        status["hmaster_alive"] = "HMaster" in jps_proc.stdout
    except Exception:
        status["hmaster_alive"] = True

    # 3. Gộp kiểm tra kết nối, bảng GIAO_DICH và Index trong 1 câu truy vấn duy nhất
    combined_check_sql = """
    SELECT COUNT(*) AS TONG_SO FROM GIAO_DICH;
    SELECT TABLE_NAME FROM SYSTEM.CATALOG WHERE TABLE_NAME = 'IDX_GIAO_DICH_KHU_VUC' AND TABLE_TYPE = 'i' LIMIT 1;
    """
    ok, out = execute_phoenix_sql(combined_check_sql, timeout=20)
    if not ok:
        if "TableNotFoundException" in out or "ERROR 1012" in out:
            status["phoenix_connected"] = True
            status["table_exists"] = False
            status["error_message"] = "Bảng GIAO_DICH chưa tồn tại trong Apache Phoenix."
        else:
            status["phoenix_connected"] = False
            status["error_message"] = f"Lỗi kết nối Phoenix: {out}"
        return status

    status["phoenix_connected"] = True
    dfs = parse_sqlline_csv_blocks(out)

    # Đánh giá kết quả từ bảng GIAO_DICH
    if len(dfs) >= 1 and not dfs[0].empty and "TONG_SO" in dfs[0].columns:
        status["table_exists"] = True
        try:
            status["record_count"] = int(float(dfs[0].iloc[0]["TONG_SO"]))
        except Exception:
            status["record_count"] = 0
    else:
        status["table_exists"] = True

    # Đánh giá kết quả kiểm tra Index
    if len(dfs) >= 2 and not dfs[1].empty:
        status["index_exists"] = True
    else:
        status["index_exists"] = False

    return status
