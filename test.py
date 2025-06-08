# 余振中 (Yu Chen Chung)
import streamlit as st
from google import genai


# 1. 把你的 API Key 填在這裡
API_KEY = "AIzaSyAUxCNknjAaCUNQQEy766URNhug5V7ofhE"

# 2. 直接在模組頂部建立 client（之後按要呼叫時可直接用）
client = genai.Client(api_key=API_KEY)

# 3. Streamlit 頁面設定
st.set_page_config(page_title="Ask Gemini with Streamlit", layout="centered")
st.title("💬 Streamlit + Gemini Demo")
st.write("在下方輸入問題，按下「送出」後，就會呼叫 Gemini-2.0-Flash API，並顯示回覆內容。")

# 4. 使用者輸入區：預設先放一句範例問題
user_prompt = st.text_area(
    label="請輸入你想問 Gemini 的問題：",
    value="Explain how AI works in a few words",
    height=120
)

# 5. 按鈕：按下之後執行 API 呼叫
if st.button("送出"):
    with st.spinner("正在呼叫 Gemini，請稍候…"):
        try:
            # 6. 呼叫你說「可以運行」的那一行
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=user_prompt
            )

            # 7. 顯示回覆文字（.text 屬性裡就是生成的內容）
            st.markdown("**📝 Gemini 回覆如下：**")
            st.write(response.text)

        except Exception as e:
            st.error(f"呼叫過程中發生錯誤：{e}")