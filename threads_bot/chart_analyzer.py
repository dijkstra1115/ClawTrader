"""
Use Claude's vision to fully analyze Kiyotaka.ai BTC chart screenshots.
No numeric data fetching — Claude does all analysis from the chart image.
"""
import base64
import anthropic
from typing import Optional

from .config import ANTHROPIC_API_KEY

ANALYSIS_PROMPT = """你是 ClawTrader 的首席技術分析師。請仔細分析這張來自 Kiyotaka.ai 的 BTC/USDT H1 K線圖。

圖表上可能包含以下資訊：
- K線（蠟燭圖）：開高低收價格
- 成交量柱狀圖
- CVD (Cumulative Volume Delta)：主動買賣力道
- OI (Open Interest Delta)：未平倉合約變化

請提供完整分析：

1. **當前價格與走勢**：目前價格、近期趨勢方向
2. **支撐與阻力位**：從 K 線圖中辨識出的關鍵價位
3. **K線形態**：近期是否有重要的 K 線形態（錘子線、吞噬、十字星、頭肩等）
4. **成交量分析**：成交量是否配合價格走勢、有無量能背離
5. **CVD 分析**（如圖上有顯示）：主動買單還是賣單主導、CVD 與價格是否背離
6. **OI 分析**（如圖上有顯示）：持倉量變化趨勢、是否有異常增減
7. **綜合研判**：多空力道對比、短期可能的走勢方向
8. **風險提示**：需要注意的風險因素

使用繁體中文回答，專業但簡潔。
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
