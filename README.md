# ClawTrader

BTC 自動分析 Threads Bot，每日定時截圖 velo.xyz 圖表，透過 Claude Vision 分析盤面後自動發布到 Threads。

## Pipeline

```
velo.xyz 截圖 → Claude Vision 分析 → 抓取新聞 → 生成貼文 → 發布 Threads
```

1. **截圖** — Playwright 開啟 velo.xyz/chart，自動加入 CVD（Cumulative Delta）和 OI（Open Interest）指標，截取 BTC H1 圖表
2. **分析** — 將截圖送入 Claude，以交易員視角分析價格結構、量價關係、CVD/OI 訊號
3. **新聞** — 抓取最新 BTC 相關新聞作為參考
4. **生成** — Claude 結合技術分析與新聞，產出繁體中文 Threads 貼文（400 字內）
5. **發布** — 透過 Threads API 附圖發布

## 使用方式

```bash
# 安裝依賴
pip install -r requirements.txt
playwright install chromium

# 設定環境變數
cp .env.example .env
# 編輯 .env 填入 Threads API 與 Anthropic API 金鑰

# 定時排程（持續運行）
python -m threads_bot

# 單次執行
python -m threads_bot --once

# 測試模式（不實際發布）
python -m threads_bot --dry
```

## 環境變數

| 變數 | 說明 |
|------|------|
| `THREADS_USER_ID` | Threads 用戶 ID |
| `THREADS_ACCESS_TOKEN` | Threads API Access Token |
| `ANTHROPIC_API_KEY` | Claude API Key |
| `POST_TIMES` | 發文時間，24h 格式，逗號分隔（預設 `08:00`） |
| `TIMEZONE` | 時區（預設 `Asia/Taipei`） |

## 專案結構

```
threads_bot/
├── bot.py                # 主程式入口，串接整個 pipeline
├── chart_screenshot.py   # Playwright 自動化截圖 velo.xyz
├── chart_analyzer.py     # Claude Vision 圖表分析
├── news_fetcher.py       # BTC 新聞抓取
├── content_generator.py  # Claude 生成 Threads 貼文
├── threads_publisher.py  # Threads API 發布
├── scheduler.py          # 定時排程
└── config.py             # 環境變數設定
```

## Tech Stack

- **Python 3.13**
- **Playwright** — 瀏覽器自動化截圖
- **Claude API** — Vision 分析 + 內容生成
- **Threads API** — Meta 官方 API 發布貼文
- **velo.xyz** — BTC 圖表來源（TradingView 嵌入，含 CVD/OI 指標）
