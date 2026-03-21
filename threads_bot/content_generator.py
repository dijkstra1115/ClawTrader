"""
Generate Threads post from Claude's chart analysis and news.
No numeric data — all analysis comes from Kiyotaka chart screenshots.
"""
import anthropic
from typing import Dict, Optional

from .config import ANTHROPIC_API_KEY

SYSTEM_PROMPT = """你是 ClawTrader，一個專業的加密貨幣市場分析師，在 Threads 上發布每日 BTC 分析。

要求：
1. 使用繁體中文撰寫
2. 語氣專業但親切，適合社群媒體
3. 基於提供的技術分析結果撰寫精簡版本
4. 包含支撐與阻力位、趨勢判斷、CVD/OI 解讀
5. 簡要提及重要新聞（如有提供）
6. 總字數控制在 400 字以內（Threads 限制 500 字）
7. 適當使用 emoji 增加可讀性
8. 結尾加上 #BTC #Bitcoin #加密貨幣 #ClawTrader 等標籤
"""

POST_PROMPT_TEMPLATE = """請根據以下 BTC H1 圖表分析和最新新聞，撰寫今日的 Threads 分析貼文：

## Claude 圖表技術分析（來自 Kiyotaka.ai H1 K線圖 + CVD + OI）

{chart_analysis}

## 最新 BTC 新聞
{news}

請將以上分析濃縮為一篇 400 字以內的 Threads 貼文。重點放在：
1. 當前價格與關鍵支撐阻力位
2. CVD/OI 的多空訊號
3. 結合新聞的綜合研判
"""


def format_news(news_list: list) -> str:
    """Format news items."""
    if not news_list:
        return "- 暫無最新新聞"
    lines = []
    for item in news_list[:5]:
        title = item.get("title", "")
        if title:
            lines.append(f"- {title}")
    return "\n".join(lines) if lines else "- 暫無最新新聞"


def generate_post(chart_analysis: str, news: Dict = None) -> str:
    """
    Generate a Threads post from chart analysis and news.
    chart_analysis: Claude's full visual analysis of the Kiyotaka chart
    news: dict with 'bitcoin' key containing 'news' list
    """
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    btc_news = []
    if news:
        btc_news = news.get("bitcoin", {}).get("news", [])

    prompt = POST_PROMPT_TEMPLATE.format(
        chart_analysis=chart_analysis,
        news=format_news(btc_news),
    )

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )

    return message.content[0].text
