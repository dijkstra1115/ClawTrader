"""
Use Claude's vision to fully analyze velo.xyz BTC chart screenshots.
No numeric data fetching — Claude does all analysis from the chart image.
"""
import base64
import anthropic
from typing import Optional

from .config import ANTHROPIC_API_KEY

ANALYSIS_PROMPT = """你是一個經驗豐富的加密貨幣交易員。分析這張 velo.xyz 的 BTC/USDT H1 K線圖。

圖表上有：K線、成交量、Cumulative Volume Delta（CVD，主動買賣力道累積）、Aggregated Open Interest（OI，未平倉合約）。

請像交易員一樣分析，不是寫學術報告：

1. **價格結構**：現在在哪個位置？趨勢是什麼？有沒有在做底/做頭？
2. **關鍵價位**：哪裡有明顯的支撐和阻力？哪個位置破了會大動？
3. **K線訊號**：最近有沒有值得注意的 K 線形態？
4. **量價關係**：量有沒有跟上？有沒有背離？
5. **CVD 觀察**：主動買盤還是賣盤在主導？有沒有 CVD 與價格背離？
6. **OI 變化**：持倉量在增加還是減少？配合價格走勢代表什麼？
7. **交易觀點**：你現在偏多還是偏空？為什麼？在等什麼進場訊號？

用繁體中文回答。講人話，不要八股文。
"""


def analyze_chart(image_path: str) -> str:
    """
    Send BTC chart screenshot to Claude for complete visual analysis.
    Returns the full analysis text.
    """
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    with open(image_path, "rb") as f:
        image_data = base64.standard_b64encode(f.read()).decode("utf-8")

    ext = image_path.lower().rsplit(".", 1)[-1]
    media_type = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg"}.get(ext, "image/png")

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1500,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": media_type,
                        "data": image_data,
                    },
                },
                {
                    "type": "text",
                    "text": ANALYSIS_PROMPT,
                },
            ],
        }],
    )

    return message.content[0].text


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        result = analyze_chart(sys.argv[1])
        print(result)
    else:
        print("Usage: python -m threads_bot.chart_analyzer <image_path>")
