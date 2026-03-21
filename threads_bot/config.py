"""
Configuration for ClawTrader Threads Bot.
Copy .env.example to .env and fill in your credentials.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Threads API
THREADS_USER_ID = os.getenv("THREADS_USER_ID")
THREADS_ACCESS_TOKEN = os.getenv("THREADS_ACCESS_TOKEN")
THREADS_API_BASE = "https://graph.threads.net/v1.0"

# Claude API
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# Scheduling (24h format, e.g. "08:00" or "08:00,20:00" for multiple times)
POST_TIMES = os.getenv("POST_TIMES", "08:00").split(",")

# Timezone
TIMEZONE = os.getenv("TIMEZONE", "Asia/Taipei")

# Data sources
COINGECKO_API_BASE = "https://api.coingecko.com/api/v3"
