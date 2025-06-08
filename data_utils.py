# 余振中 (Yu Chen Chung)
# data_utils.py
import pandas as pd

# 1. 讀取 Excel（EP15、EP16）
def load_sheets(file) -> dict[str, pd.DataFrame]:
    return pd.read_excel(file, sheet_name=["EP15", "EP16"])

# 2. 清洗：轉數值 & 去除 NaN
def clean_numeric_columns(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    for c in cols:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    return df.dropna(subset=cols, how="any")

# 3. 計算 OK/NG
def compute_status(df: pd.DataFrame, thresholds: dict[str, tuple[float,float]]) -> pd.DataFrame:
    def _row_status(row):
        return "OK" if all(low <= row[col] <= high for col,(low,high) in thresholds.items()) else "NG"
    df["狀態"] = df.apply(_row_status, axis=1)
    return df

# 4. 解析「電鍍開始時間」成 year_month
def parse_year_month(df: pd.DataFrame, date_col: str) -> pd.DataFrame:
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    df = df.dropna(subset=[date_col])
    df["year_month"] = df[date_col].dt.to_period("M").dt.to_timestamp()
    return df
