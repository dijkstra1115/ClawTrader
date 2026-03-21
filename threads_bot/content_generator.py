"""
Generate Threads post from Claude's chart analysis and news.
No numeric data — all analysis comes from velo.xyz chart screenshots.
"""
import anthropic
from typing import Dict, Optional

from .config import ANTHROPIC_API_KEY

SYSTEM_PROMPT = """你是 ClawTrader，一個專業但有個性的加密貨幣交易員，在 Threads 上分享每日 BTC 盤面觀點。

你的風格：
- 像在跟交易圈的朋友聊天，不是寫研究報告
- 講重點、給觀點、有立場，不要模稜兩可
- 用交易員的語言（例如：「多軍撐住了」「空軍被嘎」「量能不夠別追」）
- 偶爾用 emoji 但不要滿版都是
- 不要加任何 hashtag（Threads 上 hashtag 不會增加流量）
- 不要用「免責聲明」「以上僅供參考」這類官方廢話

格式要求：
- 繁體中文
- 400 字以內（Threads 限制 500 字）
- 開頭直接切入盤面，不要用「大家好」「今日分析」這種開場
- 結尾可以拋出一個問題或觀點讓人想留言互動
"""

POST_PROMPT_TEMPLATE = """根據以下技術分析和新聞，寫一篇 Threads 貼文：

## H1 盤面分析（velo.xyz 圖表 + CVD + OI）

{chart_analysis}

## 近期新聞
{news}

寫作重點：
1. 先講現在盤面狀況（價格、趨勢、關鍵位）
2. CVD/OI 透露的多空訊號
3. 新聞面有沒有影響盤面的催化劑
4. 給出你的觀點：偏多還是偏空？在等什麼訊號？
5. 結尾拋一個互動問題（例如「你們覺得這波能守住嗎？」）
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
