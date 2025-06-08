# 余振中 (Yu Chen Chung)
import streamlit as st
import pandas as pd
import altair as alt
import openai

st.set_page_config(
    page_title="電鍍履歷表",
    page_icon=":bar_chart:",
    layout="wide"
)  # 網頁設置 開頭 圖示 頁面寬窄

st.title("🧪 化學分析 Excel 讀取與呈現")

# --------------------------------------------------
# 快取：只要上傳的檔案物件沒變，就不會重複讀取
# --------------------------------------------------
@st.cache_data
def load_sheets(file) -> dict:
    # 只讀 EP15、EP16 兩個工作表
    return pd.read_excel(file, sheet_name=["EP15", "EP16"])


# --------------------------------------------------
# 側邊欄：上傳檔案 & 選擇分頁
# --------------------------------------------------
uploaded_file = st.sidebar.file_uploader("📂 上傳 Excel 檔案", type=["xlsx"])
if uploaded_file:
    try:
        sheets = load_sheets(uploaded_file)
    except ValueError:
        st.sidebar.error("找不到 EP15 或 EP16，請確認檔案內容。")
        st.stop()

    # 讓使用者選擇要顯示哪一個分頁
    sheet_name = st.sidebar.selectbox("📑 選擇分頁", options=list(sheets.keys()))

    # 顯示說明
    st.sidebar.markdown("---")
    st.sidebar.markdown("選擇後，主畫面將只顯示該分頁資料。")

    # --------------------------------------------------
    # 主畫面：顯示選定分頁的所有欄位
    # --------------------------------------------------
    df = sheets[sheet_name]

    st.subheader(f"分頁：{sheet_name}（共 {df.shape[0]} 筆，{df.shape[1]} 欄）")

    with st.expander("Data Preview"):  # 資料顯示折疊
        # st.dataframe(df)  # 未標記的資料

        # 假設你已經透過 load_sheets 或 pd.read_excel 取得 EP15 或 EP16 的 df
        # df = sheets[sheet_name]
        # 1. 定義標準範圍
        # 定義範圍
        thresholds = {
            "硫酸實際值(g/l)": (62, 68),
            "硫酸銅實際值(g/l)": (200, 210),
            "氯離子實際值(ppm/l)": (64, 80),
        }

        # 1. 轉成數值
        for col in thresholds:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        # # 2. 先去除只要三個欄位任一為 NaN 的列
        # df = df.dropna(subset=list(thresholds.keys()), how="any")


        # 3. 準備 full_styler：整表只標記超標欄位
        def mark(v, low, high):
            return "background-color: salmon" if (v < low or v > high) else ""


        full_styler = df.style
        for col, (low, high) in thresholds.items():
            full_styler = full_styler.applymap(
                lambda v, low=low, high=high: mark(v, low, high),
                subset=[col]
            )

        st.subheader("📋 全部資料（已去除 NaN 列，超標欄位標紅）")
        st.dataframe(full_styler, use_container_width=True)

        # 4. 選出至少一欄超標的列
        mask = pd.DataFrame({col: df[col].between(low, high)
                             for col, (low, high) in thresholds.items()})

        # 2. 先去除只要三個欄位任一為 NaN 的列
        df = df.dropna(subset=list(thresholds.keys()), how="any")


        oos = df.loc[~mask.all(axis=1)]

        # 5. 準備 oos_styler：同樣只標記超標欄位
        oos_styler = oos.style
        for col, (low, high) in thresholds.items():
            oos_styler = oos_styler.applymap(
                lambda v, low=low, high=high: mark(v, low, high),
                subset=[col]
            )

        st.subheader("🚨 僅顯示超標列（已去除 NaN，且超標欄位標紅）")
        st.dataframe(oos_styler, use_container_width=True)


    #  st.line_chart
    # 假設你已經在 sidebar 上傳並讀完 df
    # y 欄位名稱列表
    y_cols = ["硫酸實際值(g/l)", "硫酸銅實際值(g/l)", "氯離子實際值(ppm/l)"]

    # 1. 轉型：非數值自動成 NaN
    df[y_cols] = df[y_cols].apply(pd.to_numeric, errors="coerce")

    # 2. （可選）去掉全是 NaN 的列
    df = df.dropna(subset=y_cols, how="all")

    # 3. 畫圖：顯式告訴 st.line_chart 要用哪些欄
    st.line_chart(data=df, x="電鍍次數", y=y_cols)



    # --------------------------------------------------
    # 圓餅圖：OK vs NG 比例（使用 Altair）
    # --------------------------------------------------
    # 1. 準備統計資料
    counts = (
        df["合格"]
        .value_counts()
        .rename_axis("合格")
        .reset_index(name="數量")
    )
    # 計算百分比
    total = counts["數量"].sum()
    counts["percent"] = counts["數量"] / total

    # Altair 圓餅圖 + 百分比文字
    pie = (
        alt.Chart(counts)
        .mark_arc(innerRadius=50, outerRadius=100)
        .encode(
            theta=alt.Theta("數量:Q", title=None),
            color=alt.Color("合格:N", legend=alt.Legend(title="合格")),
            tooltip=[
                "合格",
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

    st.subheader("📊 OK/NG 比例（顯示百分比）")
    st.altair_chart(pie + labels, use_container_width=False)



    # --------------------------------------------------
    # 散點圖：繪製 + 趨勢線
    # --------------------------------------------------



    # —————————————— 1. 假設你已經有 df 並選好分頁 ——————————————
    # df = sheets[sheet_name].copy()

    # —————————————— 2. 只保留 SP10平均 & 硬度HB 都有值的列 ——————————————
    df_clean = df.dropna(subset=["SP10平均", "硬度HB"], how="any")

    # —————————————— 3. 繪製散點圖 + 趨勢線 ——————————————
    scatter = (
        alt.Chart(df_clean)
        .mark_point(size=60, opacity=0.7)
        .encode(
            x=alt.X("SP10平均:Q", title="SP10平均",scale=alt.Scale(nice=True)),
            y=alt.Y("硬度HB:Q", title="硬度HB",scale=alt.Scale(nice=True)),
            tooltip=[
                alt.Tooltip("SP10平均:Q", format=".2f"),
                alt.Tooltip("硬度HB:Q", format=".2f")
            ]
        )
    )

    trend = (
        alt.Chart(df_clean)
        .transform_regression("SP10平均", "硬度HB", method="linear")
        .mark_line(color="red", size=3)
        .encode(
            x="SP10平均:Q",
            y="硬度HB:Q"
        )
    )

    chart = (scatter + trend).properties(
        width=700,
        height=400,
        title="SP10平均 vs 硬度HB 散點圖"  #（含線性趨勢線）
    ).interactive()  # 允許使用者縮放/平移

    st.subheader("🔍 SP10平均 vs 硬度HB 散點圖(允許使用者縮放/平移)")
    st.altair_chart(chart, use_container_width=True)




    # --------------------------------------------------
    # 柱狀圖：按月顯示（使用 Altair）
    # --------------------------------------------------

    #
    #
    # # 假設 df 已經是你選好的 EP15 or EP16 sheet，且 df["狀態"] 已經有 OK/NG
    # # 並且 df["電鍍開始時間"] 是字串格式 "YYYY-MM-DD HH:MM:SS"
    #
    # 1. 轉成 datetime 並抽出年月
    df["電鍍開始時間"] = pd.to_datetime(df["電鍍開始時間"], errors="coerce")
    df = df.dropna(subset=["電鍍開始時間"])
    df["year_month"] = df["電鍍開始時間"].dt.to_period("M").dt.to_timestamp()
    #
    # 2. 計算每月總筆數
    monthly = (
        df
        .groupby("year_month")
        .size()
        .reset_index(name="count")
    )
    # 把 year_month 轉成字串
    monthly["month_str"] = monthly["year_month"].dt.strftime("%Y-%m")

    # 3. 畫柱狀圖 (畫成 Ordinal 軸)
    bar = (
        alt.Chart(monthly)
        .mark_bar()
        .encode(
            x=alt.X("month_str:O",
                    axis=alt.Axis(labelAngle=0, title="月份")),
            y=alt.Y("count:Q",
                    title="電鍍支數"),
            tooltip=[
                alt.Tooltip("month_str:O", title="月份"),
                alt.Tooltip("count:Q", title="電鍍支數")
            ]
        )
        .properties(width=600, height=400, title="每月電鍍批次總數")
    )

    st.subheader("📈 每月電鍍批次總數")
    st.altair_chart(bar, use_container_width=False)

    # --------------------------------------------------
    # 柱狀圖：原物料用量按月顯示（使用 Altair）
    # --------------------------------------------------



    # — 1. 假設 df 已讀取並選好分頁
    # df = sheets[sheet_name].copy()

    # — 2. 解析並取出年月
    df["電鍍開始時間"] = pd.to_datetime(df["電鍍開始時間"], errors="coerce")
    df = df.dropna(subset=["電鍍開始時間"])
    df["year_month"] = df["電鍍開始時間"].dt.to_period("M").dt.to_timestamp()

    # — 3. 轉數值並忽略空值

    df["磷銅球(kg)"] = pd.to_numeric(df["磷銅球(kg)"], errors="coerce")

    # — 4. 按月 groupby sum（NaN 自動被忽略），並轉成整數
    monthly = (
        df
        .groupby("year_month")["磷銅球(kg)"]
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
            y=alt.Y("total_int:Q", title="磷銅球總和 (kg)"),
            tooltip=["month_str", "total_int"]
        )
        .properties(width=600, height=400, title="每月磷銅球(kg) 總和")
    )

    st.subheader("📈 每月磷銅球使用量")
    st.altair_chart(bar, use_container_width=True)












else:
    st.sidebar.info("請先在側邊欄上傳 Excel 檔案。")


