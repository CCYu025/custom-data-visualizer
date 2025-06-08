# 余振中 (Yu Chen Chung)
#
import streamlit as st
import os
# from dotenv import load_dotenv

# 1. 先把 env 載進來
# load_dotenv()
# 如果未來要呼叫 openai，就：
# import openai
# openai.api_key = os.getenv("OPENAI_API_KEY")

# 2. 先做 Streamlit 基本設定
st.set_page_config(
    page_title="電鍍履歷表",
    page_icon=":bar_chart:",
    layout="wide",
)

st.title("🧪 化學分析 Excel 讀取與呈現")

# 3. 導入自己寫的工具模組
from data_utils import load_sheets, clean_numeric_columns, compute_status, parse_year_month
from style_utils import apply_marking, filter_oos_and_style
from chart_utils import (
    render_line_chart,
    render_pie_chart,
    render_scatter_with_trend,
    render_monthly_count_bar,
    render_monthly_material_bar,
)
from genai_utils import ask_gemini


# 4. 側邊欄：讓使用者上傳檔案，選 EP15 / EP16
# uploaded_file = st.sidebar.file_uploader("📂 上傳 Excel 檔案", type=["xlsx"])
# if not uploaded_file:
#     st.sidebar.info("請先上傳含 EP15、EP16 的 Excel 檔案")
#     st.stop()

# 根目錄中的檔案名稱
EXCEL_FILE_PATH = "電鍍履歷表.xlsx"  # ← 請修改為實際檔名，例如 "electro_data.xlsx"

# 檢查檔案是否存在
if not os.path.exists(EXCEL_FILE_PATH):
    st.error(f"找不到檔案：{EXCEL_FILE_PATH}，請確認檔案已放在專案根目錄下。")
    st.stop()

sheets = load_sheets(EXCEL_FILE_PATH)
sheet_name = st.sidebar.selectbox("📑 選擇分頁", list(sheets.keys()))
df = sheets[sheet_name].copy()

# 5. 定義濃度標準範圍
thresholds = {
    "硫酸實際值(g/l)"     : (62,  68),
    "硫酸銅實際值(g/l)"   : (200, 210),
    "氯離子實際值(ppm/l)" : (64,  80),
}

# 6. 資料前處理
# 6.1 先轉數值 & 去除 NaN
df = clean_numeric_columns(df, list(thresholds.keys()))
# 6.2 計算狀態 OK/NG
df = compute_status(df, thresholds)

# 7. 標記 & 顯示全部資料
full_styler = apply_marking(df, thresholds)
st.subheader("📋 全部資料（已去除 NaN 且超標欄位標紅）")
st.dataframe(full_styler, use_container_width=True)

# 8. 顯示僅超標列
oos_styler = filter_oos_and_style(df, thresholds)
st.subheader("🚨 僅顯示超標列（超標欄位標紅）")
st.dataframe(oos_styler, use_container_width=True)

# 9. 多條折線圖（電鍍次數 vs 三项濃度）
st.subheader("📈 多條折線圖（電鍍次數 vs 三項濃度）")
render_line_chart(df, x_col="電鍍次數", y_cols=["硫酸實際值(g/l)", "硫酸銅實際值(g/l)", "氯離子實際值(ppm/l)"])

# 10. OK / NG 圓餅圖
st.subheader("📊 OK/NG 比例（顯示百分比）")
render_pie_chart(df, status_col="狀態")

# 11. SP10平均 vs 硬度HB 散點圖 + 趨勢線
st.subheader("🔍 SP10平均 vs 硬度HB 散點圖 (可縮放/平移)")
render_scatter_with_trend(df, x_col="SP10平均", y_col="硬度HB")

# 12. 每月電鍍批次總數柱狀圖
st.subheader("📈 每月電鍍批次總數")
render_monthly_count_bar(df, date_col="電鍍開始時間")

# 13. 每月磷銅球用量總和
st.subheader("📈 每月磷銅球使用量")
render_monthly_material_bar(df, date_col="電鍍開始時間", material_col="磷銅球(kg)")

# 14. gemini api
# st.subheader("📈 gemini api")
# st.write(
#     """
#     在下方輸入問題，按下「送出」後，就會呼叫包在 `genai_utils.py` 裡的 `ask_gemini` 函式。
#     該函式會負責向 Gemini-2.0-Flash API 發送請求並自動重試（遇到 503 過載時），
#     回傳結果或錯誤訊息後顯示於下方。
#     """
# )
#
# # 2. 使用者輸入區：預設一個範例問題
# user_prompt = st.text_area(
#     label="請輸入你想問 Gemini 的問題：",
#     value="Explain how AI works in a few words",
#     height=120
# )
#
# # 3. 當按下「送出」按鈕，就呼叫 ask_gemini() 並顯示結果
# if st.button("送出"):
#     with st.spinner("正在呼叫 Gemini，請稍候…"):
#         # 4. 呼叫我們在 genai_utils.py 定義的函式
#         result = ask_gemini(prompt_text=user_prompt)
#
#         # 5. 如果回傳以 "Error:" 開頭，就顯示錯誤提示；否則顯示正常回覆
#         if result.startswith("Error:"):
#             st.error(result)
#         else:
#             st.markdown("**📝 Gemini 回覆如下：**")
#             st.write(result)
st.subheader("📈 Gemini 自動分析電鍍資料")


# 顯示資料預覽
st.dataframe(df)

# 取最新 7 筆資料並轉換成文字格式（CSV 風格較易閱讀）
latest_7 = df.tail(7)
latest_7_text = latest_7.to_csv(index=False)

# 自動建立 prompt 並發送
if st.button("🔍 自動分析最新7筆資料"):
    with st.spinner("正在呼叫 Gemini 分析中…"):
        prompt = f"""你是一位資深電鍍分析師。請根據以下電鍍資料（包含日期、濃度、電鍍次數），
提出這7筆資料的趨勢判斷與改善建議：
{latest_7_text}
"""
        
        result = ask_gemini(prompt_text=prompt)

        if result.startswith("Error:"):
            st.error(result)
        else:
            st.markdown("**🧠 Gemini 分析回覆：**")
            st.write(result)