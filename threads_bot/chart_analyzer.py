"""
Use Claude's vision capability to analyze Kiyotaka.ai chart screenshots.
Extracts support/resistance, patterns, and trading insights from chart images.
"""
import base64
import anthropic
from typing import Dict

from .config import ANTHROPIC_API_KEY

CHART_ANALYSIS_PROMPT = """你是一位專業的技術分析師。請仔細分析這張 H1 K線圖，並提供以下資訊：

1. **支撐與阻力位**：從圖表中識別出關鍵的支撐和阻力價位
2. **趨勢判斷**：目前是上升趨勢、下降趨勢還是盤整？
3. **K線形態**：是否有明顯的 K 線形態（如錘子線、吞噬、十字星等）？
4. **成交量分析**：成交量是否配合價格走勢？
5. **關鍵觀察**：任何值得注意的技術訊號

請用繁體中文回答，簡潔扼要，重點突出。總字數控制在 200 字以內。
"""


def encode_image(image_path: str) -> str:
    """Read and base64-encode an image file."""
    with open(image_path, "rb") as f:
        return base64.standard_b64encode(f.read()).decode("utf-8")


def analyze_single_chart(image_path: str, asset_name: str) -> str:
    """
    Send a chart screenshot to Claude for visual analysis.
    Returns the analysis text.
    """
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    image_data = encode_image(image_path)

    # Determine media type
    ext = image_path.lower().rsplit(".", 1)[-1]
    media_type = {
        "png": "image/png",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
    }.get(ext, "image/png")

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=512,
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
                    "text": f"這是 {asset_name} 的 H1 K線圖（來自 Kiyotaka.ai）。\n\n{CHART_ANALYSIS_PROMPT}",
                },
            ],
        }],
    )

    return message.content[0].text


def analyze_charts_with_claude(chart_paths: Dict[str, str]) -> Dict[str, str]:
    """
    Analyze all chart screenshots with Claude vision.

    Args:
        chart_paths: dict mapping asset key ('bitcoin', 'gold') to image file path

    Returns:
        dict mapping asset key to Claude's analysis text
    """
    results = {}

    asset_names = {
        "bitcoin": "Bitcoin (BTC/USDT)",
        "gold": "Gold (XAU/USD)",
    }

    for key, path in chart_paths.items():
        name = asset_names.get(key, key)
        print(f"[chart_analyzer] Analyzing {name} chart...")
        try:
            analysis = analyze_single_chart(path, name)
            results[key] = analysis
            print(f"[chart_analyzer] {name} analysis complete ({len(analysis)} chars)")
        except Exception as e:
            print(f"[chart_analyzer] Failed to analyze {name}: {e}")
            results[key] = f"圖表分析暫時無法取得"

    return results


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        path = sys.argv[1]
        result = analyze_single_chart(path, "Test Asset")
        print(result)
    else:
        print("Usage: python -m threads_bot.chart_analyzer <image_path>")
