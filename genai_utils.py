# 余振中 (Yu Chen Chung)
# genai_utils.py
import time
from google import genai

# 這裡把 API Key 寫在模組中（開發測試用）。
# 若要部署，建議改用環境變數：os.getenv("GOOGLE_API_KEY")
API_KEY = "AIzaSyAUxCNknjAaCUNQQEy766URNhug5V7ofhE"

# 在模組載入時，先建立一個 genai.Client 實例
_client = genai.Client(api_key=API_KEY)

def ask_gemini(
    prompt_text: str,
    model: str = "gemini-2.0-flash",
    max_retries: int = 4,
    initial_backoff: float = 1.0,
    backoff_factor: float = 2.0
) -> str:
    """
    呼叫 Gemini API 取得回答，內建 503 過載自動重試機制。

    參數：
    - prompt_text: 使用者想問的問題字串
    - model: 要呼叫的模型名稱，預設 "gemini-2.0-flash"
    - max_retries: 最大重試次數（遇到 503 時）
    - initial_backoff: 初始等待秒數
    - backoff_factor: 每次重試等待時間乘的係數（指數退避）

    回傳：Gemini 回答的文字。如果超過重試次數仍失敗，回傳錯誤訊息字串。
    """
    backoff = initial_backoff

    for attempt in range(1, max_retries + 1):
        try:
            # 呼叫模型：只傳 model 與 contents（避免 generation_config 參數錯誤）
            response = _client.models.generate_content(
                model=model,
                contents=prompt_text
            )
            # 成功後直接回傳文字內容
            return response.text

        except Exception as e:
            err_msg = str(e)
            # 判斷是否為 503（模型過載）錯誤
            if "503 UNAVAILABLE" in err_msg or "The model is overloaded" in err_msg:
                if attempt < max_retries:
                    # 如果未達上限，就等待後重試
                    time.sleep(backoff)
                    backoff *= backoff_factor
                    continue
                else:
                    # 已到達最大重試次數，回傳錯誤說明
                    return f"Error: 模型連續 {max_retries} 次 503 過載，請稍後再試。"
            else:
                # 不是 503，直接回傳錯誤訊息
                return f"Error: 呼叫過程中發生例外：{err_msg}"

    # 理論上不會跑到這裡，保險起見回傳一個通用錯誤
    return "Error: 無法取得回覆，請稍後再試。"
