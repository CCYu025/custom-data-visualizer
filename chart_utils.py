# 余振中 (Yu Chen Chung)
# chart_utils.py
import pandas as pd
import altair as alt
import streamlit as st

# 一定要從 data_utils 匯入 parse_year_month
from data_utils import parse_year_month

# 1. 折線圖（指定 y 欄位）
def render_line_chart(df: pd.DataFrame, x_col: str, y_cols: list[str]):
    df[y_cols] = df[y_cols].apply(pd.to_numeric, errors="coerce")
    df_clean = df.dropna(subset=y_cols, how="all")
    return st.line_chart(data=df_clean, x=x_col, y=y_cols)

# 2. 圓餅圖（顯示 OK vs NG 百分比）
def render_pie_chart(df: pd.DataFrame, status_col: str):
    counts = (
        df[status_col]
        .value_counts()
        .rename_axis(status_col)
        .reset_index(name="數量")
    )
    total = counts["數量"].sum()
    counts["percent"] = counts["數量"] / total

    pie = (
        alt.Chart(counts)
        .mark_arc(innerRadius=50, outerRadius=100)
        .encode(
            theta=alt.Theta("數量:Q"),
            color=alt.Color(f"{status_col}:N", legend=alt.Legend(title=status_col)),
            tooltip=[
                status_col,
                "數量",
                alt.Tooltip("percent:Q", format=".1%")
            ]
        )
    )
    labels = (
        alt.Chart(counts)
        .mark_text(radius=75, size=14, color="white")
        .encode(
            theta=alt.Theta("數量:Q"),
            text=alt.Text("percent:Q", format=".1%")
        )
    )
    st.altair_chart(pie + labels, use_container_width=False)

# 3. 散點圖 + 線性趨勢線（指定 x, y）
def render_scatter_with_trend(df: pd.DataFrame, x_col: str, y_col: str):
    df_clean = df.dropna(subset=[x_col, y_col], how="any")
    scatter = (
        alt.Chart(df_clean)
        .mark_point(size=60, opacity=0.7)
        .encode(
            x=alt.X(f"{x_col}:Q", title=x_col, scale=alt.Scale(nice=True)),
            y=alt.Y(f"{y_col}:Q", title=y_col, scale=alt.Scale(nice=True)),
            tooltip=[
                alt.Tooltip(f"{x_col}:Q", format=".2f"),
                alt.Tooltip(f"{y_col}:Q", format=".2f")
            ]
        )
    )
    trend = (
        alt.Chart(df_clean)
        .transform_regression(x_col, y_col, method="linear")
        .mark_line(color="red", size=3)
        .encode(x=f"{x_col}:Q", y=f"{y_col}:Q")
    )
    chart = (scatter + trend).properties(width=700, height=400).interactive()
    st.altair_chart(chart, use_container_width=True)

# 4. 每月批次總數柱狀圖
def render_monthly_count_bar(df: pd.DataFrame, date_col: str):
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    df = df.dropna(subset=[date_col])
    df["year_month"] = df[date_col].dt.to_period("M").dt.to_timestamp()

    monthly = df.groupby("year_month").size().reset_index(name="count")
    monthly["month_str"] = monthly["year_month"].dt.strftime("%Y-%m")

    bar = (
        alt.Chart(monthly)
        .mark_bar()
        .encode(
            x=alt.X("month_str:O", axis=alt.Axis(labelAngle=0, title="月份")),
            y=alt.Y("count:Q", title="電鍍支數"),
            tooltip=[
                alt.Tooltip("month_str:O", title="月份"),
                alt.Tooltip("count:Q", title="電鍍支數")
            ]
        )
        .properties(width=600, height=400, title="每月電鍍批次總數")
    )
    st.altair_chart(bar, use_container_width=False)

# 5. 每月原物料（磷銅球）用量
def render_monthly_material_bar(df: pd.DataFrame, date_col: str, material_col: str):
    df = parse_year_month(df, date_col)  # 如果你在 data_utils 已有這個函式，就調用它
    df[material_col] = pd.to_numeric(df[material_col], errors="coerce")

    monthly = (
        df.groupby("year_month")[material_col]
          .sum()
          .reset_index(name="total_kg")
    )
    monthly["total_int"] = monthly["total_kg"].round(0).astype(int)
    monthly["month_str"] = monthly["year_month"].dt.strftime("%Y-%m")

    bar = (
        alt.Chart(monthly)
        .mark_bar()
        .encode(
            x=alt.X("month_str:O", axis=alt.Axis(labelAngle=0, title="月份")),
            y=alt.Y("total_int:Q", title=f"{material_col} 總和 (kg)"),
            tooltip=["month_str", "total_int"]
        )
        .properties(width=600, height=400, title=f"每月{material_col} 總和")
    )
    st.altair_chart(bar, use_container_width=True)
