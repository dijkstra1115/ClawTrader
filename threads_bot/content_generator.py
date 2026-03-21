"""
Use Claude API to generate Threads post content from news and technical analysis.
"""
import anthropic
from typing import Dict

from .config import ANTHROPIC_API_KEY

SYSTEM_PROMPT = """你是 ClawTrader，一個專業的加密貨幣與貴金屬市場分析師。
你的任務是根據提供的市場數據和新聞，撰寫一篇適合在 Threads 社群媒體上發布的分析文章。

要求：
1. 使用繁體中文撰寫
2. 語氣專業但親切，適合社群媒體
3. 包含支撐與阻力位分析
4. 包含趨勢判斷與 RSI 指標解讀
5. 簡要提及重要新聞
6. 總字數控制在 400 字以內（Threads 限制 500 字）
7. 適當使用 emoji 增加可讀性
8. 結尾加上 #BTC #Gold #加密貨幣 #黃金 #ClawTrader 等標籤
"""

POST_PROMPT_TEMPLATE = """請根據以下市場數據和新聞，撰寫今日的 Threads 分析貼文：

## 技術分析 (H1 時間框架)

### Bitcoin (BTC)
- 當前價格: ${btc_price}
- 24H 高/低: ${btc_high} / ${btc_low}
- 支撐位: {btc_support}
- 阻力位: {btc_resistance}
- 趨勢: {btc_trend}
- RSI(14): {btc_rsi}

### Gold (XAU)
- 當前價格: ${gold_price}
- 24H 高/低: ${gold_high} / ${gold_low}
- 支撐位: {gold_support}
- 阻力位: {gold_resistance}
- 趨勢: {gold_trend}
- RSI(14): {gold_rsi}

## 最新新聞

### Bitcoin 相關新聞
{btc_news}

### Gold 相關新聞
{gold_news}

請根據以上資訊撰寫分析貼文。
"""


def format_news_items(news_list: list) -> str:
    """Format news items into a readable string."""
    if not news_list:
        return "- 暫無最新新聞"
    lines = []
    for item in news_list[:5]:
        title = item.get("title", "")
        if title:
            lines.append(f"- {title}")
    return "\n".join(lines) if lines else "- 暫無最新新聞"


def build_prompt(analysis: Dict, news: Dict) -> str:
    """Build the prompt for Claude API from analysis and news data."""
    btc = analysis.get("bitcoin", {})
    gold = analysis.get("gold", {})
    btc_news = news.get("bitcoin", {}).get("news", [])
    gold_news = news.get("gold", {}).get("news", [])

    return POST_PROMPT_TEMPLATE.format(
        btc_price=btc.get("current_price", "N/A"),
        btc_high=btc.get("high_24h", "N/A"),
        btc_low=btc.get("low_24h", "N/A"),
        btc_support=", ".join(str(s) for s in btc.get("support", [])) or "N/A",
        btc_resistance=", ".join(str(r) for r in btc.get("resistance", [])) or "N/A",
        btc_trend=btc.get("trend", "N/A"),
        btc_rsi=btc.get("rsi", "N/A"),
        gold_price=gold.get("current_price", "N/A"),
        gold_high=gold.get("high_24h", "N/A"),
        gold_low=gold.get("low_24h", "N/A"),
        gold_support=", ".join(str(s) for s in gold.get("support", [])) or "N/A",
        gold_resistance=", ".join(str(r) for r in gold.get("resistance", [])) or "N/A",
        gold_trend=gold.get("trend", "N/A"),
        gold_rsi=gold.get("rsi", "N/A"),
        btc_news=format_news_items(btc_news),
        gold_news=format_news_items(gold_news),
    )


def generate_post(analysis: Dict, news: Dict) -> str:
    """
    Generate a Threads post using Claude API.
    Returns the post text ready to publish.
    """
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    prompt = build_prompt(analysis, news)

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )

    return message.content[0].text


if __name__ == "__main__":
    # Test with mock data
    mock_analysis = {
        "bitcoin": {
            "current_price": 84000,
            "high_24h": 85200,
            "low_24h": 83100,
            "support": [82500, 83000, 83500],
            "resistance": [85000, 86000, 87500],
            "trend": "bullish",
            "rsi": 62.5,
        },
        "gold": {
            "current_price": 3045,
            "high_24h": 3060,
            "low_24h": 3030,
            "support": [3020, 3030, 3040],
            "resistance": [3060, 3080, 3100],
            "trend": "bullish",
            "rsi": 58.3,
        },
    }
    mock_news = {
        "bitcoin": {"news": [{"title": "BTC breaks above 84k resistance"}]},
        "gold": {"news": [{"title": "Gold hits new all-time high amid uncertainty"}]},
    }
    post = generate_post(mock_analysis, mock_news)
    print(post)
