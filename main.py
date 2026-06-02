# main.py
# Unified execution file for the Smart Quiz Bot project.
# Initializes the SQLite database, starts the Telegram Bot polling thread in the background,
# and starts the FastAPI Uvicorn web server in the main thread.

import threading
import uvicorn
import database
import bot
from config import HOST, PORT, BOT_TOKEN

def main():
    print("=" * 50)
    print("STARTING SMART QUIZ BOT & BACKEND WEB SERVER")
    print("=" * 50)
    
    # 1. Initialize SQLite Database Tables
    database.init_db()
    
    # 2. Start the Telegram Bot Polling Thread (if BOT_TOKEN is configured)
    if BOT_TOKEN:
        try:
            bot_thread = threading.Thread(target=bot.start_bot_polling, daemon=True)
            bot_thread.start()
            print("[System] Telegram Bot background polling thread started successfully.")
        except Exception as e:
            print(f"[System] Failed to start bot polling thread: {e}")
    else:
        print("[System] Skipping Telegram Bot start (No BOT_TOKEN set). Running in browser-only Demo Mode.")
        
    # 3. Start the FastAPI Web Server (Uvicorn)
    # Note: reload is set to False to prevent thread duplication on file alterations during run.
    print(f"[System] Starting FastAPI Web Server on http://{HOST}:{PORT}...")
    uvicorn.run("server:app", host=HOST, port=PORT, reload=False)

if __name__ == "__main__":
    main()
