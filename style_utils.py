# 余振中 (Yu Chen Chung)
# style_utils.py
import pandas as pd

# 樣式化：把超出範圍的儲存格底色標紅
def apply_marking(df: pd.DataFrame, thresholds: dict[str, tuple[float,float]]):
    def mark(v, low, high):
        return "background-color: salmon" if (v < low or v > high) else ""
    styler = df.style
    for col, (low, high) in thresholds.items():
        styler = styler.applymap(
            lambda v, low=low, high=high: mark(v, low, high),
            subset=[col]
        )
    return styler

# 選出至少一個超標的列，並用 Styler 樣式標記
def filter_oos_and_style(df: pd.DataFrame, thresholds: dict[str, tuple[float,float]]):
    mask = pd.DataFrame({col: df[col].between(low, high) for col,(low,high) in thresholds.items()})
    oos = df.loc[~mask.all(axis=1)]
    # 樣式標記同 apply_marking
    return apply_marking(oos, thresholds)
