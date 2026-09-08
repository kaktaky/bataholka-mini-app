"""Конфигурация приложения из переменных окружения / файла .env.

Единая точка загрузки: .env читается один раз при импорте модуля,
дальше все настройки берутся отсюда. Дефолты повторяют прежние
захардкоженные значения — без .env поведение не меняется.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

# ------------------------- Telegram -------------------------
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
MINI_APP_URL = os.getenv("MINI_APP_URL", "https://6bc2eea42e6dd4.lhr.life")
RULES_URL = os.getenv("RULES_URL", "loquacious-donut-e20cc1.netlify.app")

# ------------------------- База данных -------------------------
DB_PATH = os.getenv("DB_PATH", "orders.db")

# ------------------------- CORS -------------------------
CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "*").split(",") if o.strip()]

# ------------------------- LM Studio / модерация -------------------------
LM_BASE_URL = os.getenv("LM_BASE_URL", "http://localhost:1234/v1")
LM_MODEL = os.getenv("LM_MODEL", "google/gemma-3-1b")
LM_API_KEY = os.getenv("LM_API_KEY", "lm-studio")
MODERATION_POLL_INTERVAL = int(os.getenv("MODERATION_POLL_INTERVAL", "3"))
