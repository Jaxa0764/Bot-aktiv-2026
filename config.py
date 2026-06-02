import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from a .env file if present
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent

# Core configurations
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
# Default telegram channel users are forced to join
CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME", "@dev_quiz_channel")
# If DEV_MODE is True, the bot ignores joining checks and runs in mock mode if token is missing
DEV_MODE = os.getenv("DEV_MODE", "True").lower() in ("true", "1", "yes")

DATABASE_PATH = os.getenv("DATABASE_PATH", str(BASE_DIR / "quiz_bot.db"))

HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))
# The public/local URL for the Telegram Mini App (used for the WebApp launch button)
MINI_APP_URL = os.getenv("MINI_APP_URL", f"http://localhost:{PORT}")

# Firebase configurations
FIREBASE_PROJECT_ID = os.getenv("FIREBASE_PROJECT_ID", "")
FIREBASE_API_KEY = os.getenv("FIREBASE_API_KEY", "")
FIREBASE_AUTH_DOMAIN = os.getenv("FIREBASE_AUTH_DOMAIN", "")
FIREBASE_SERVICE_ACCOUNT_JSON = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON", "")

# Static folders for serving web pages and profile photos
STATIC_DIR = BASE_DIR / "static"
PHOTOS_DIR = STATIC_DIR / "photos"

# Ensure directories exist
STATIC_DIR.mkdir(exist_ok=True)
PHOTOS_DIR.mkdir(exist_ok=True)

# Print current configuration details
print("=" * 50)
print("SMART QUIZ BOT CONFIGURATION:")
print(f"  - Firebase Project ID: {FIREBASE_PROJECT_ID}")
print(f"  - Channel Forced: {CHANNEL_USERNAME}")
print(f"  - Bot Token Set: {'Yes' if BOT_TOKEN else 'No (Running in DEV Fallback Mode)'}")
print(f"  - Developer Mode: {DEV_MODE}")
print(f"  - Mini App Host: http://{HOST}:{PORT}")
print(f"  - Mini App WebApp URL: {MINI_APP_URL}")
print("=" * 50)
