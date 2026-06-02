# SMART QUIZ BOT — Premium Telegram Mini App & Bot Platform

Welcome to the **SMART QUIZ BOT**! This is a startup-level, highly secure, and beautifully styled Telegram Mini App (Web App) and Bot platform that allows users to test their knowledge across multiple subjects, accumulate virtual cash rewards ("so'm") for correct answers, and request direct withdrawals to UzCard or Humo payment cards.

Designed with a cutting-edge, mobile-first **Dark Glassmorphism UI**, this application integrates seamless animations, a secure backend-verified quiz scoring engine, and a floating **AI Support Assistant** offering interactive help.

---

## 🌟 Core Features

1. **Telegram Bot Flow**:
   * **Force Join Verification**: Automatically checks membership in your official Telegram channel. Users must subscribe to continue.
   * **Bilingual Welcome & Verification**: Welcomes the player and requests phone number synchronization using Telegram's contact request button.
   * **Automatic Photo Downloading**: Resolves and downloads the user's high-res Telegram profile avatar directly to the server's static directory.
   * **One-Click Launch**: Displays a persistent reply keyboard button that launches the WebApp seamlessly.

2. **Telegram Mini App (Web App)**:
   * **Stunning Design**: A high-end dark glassmorphism theme using Google Fonts ("Outfit" and "Plus Jakarta Sans"), animated background glow blobs, reflective glass cards, and micro-interactions.
   * **SPA Bottom Navigation**: Instantly routes between four primary tabs (Home, Quizzes, Wallet, Profile) without page reloads.
   * **Secure Quiz System**: Fetches subject parameters securely, prompts text answers, and validates answers strictly on the server-side to prevent client-side balance hacking.
   * **Golden Balance & Wallet**: Automatically updates balances. Displays withdrawal forms once the threshold is reached (1000 so'm) and includes card format validators.
   * **Floating AI Support Assistant**: A conversational supports panel in the bottom corner offering prompt, simulated replies to user queries about the bot.

3. **Smart Developer Demo Mode**:
   * Detects if the app is launched in a standard browser (e.g. Chrome, Firefox) outside Telegram, and automatically spins up a simulated developer profile. This lets you test the complete frontend logic, quizzes, and withdrawals immediately in your browser without configuring real tokens!

---

## 📂 Project Architecture

```
bot/
├── main.py                # Unified coordinator starts bot thread & FastAPI server
├── bot.py                 # Telegram Bot command routines (pyTelegramBotAPI)
├── server.py              # FastAPI REST endpoints & SPA static file mounts
├── database.py            # SQLite database schema, CRUD operations & transactions
├── quiz_data.py           # Server-side quiz bank (5 subjects, 10 questions each)
├── config.py              # System config manager, environment loaders & directory setups
├── requirements.txt       # Python environment dependencies
└── static/                # Mini App Frontend files
    ├── index.html         # Single Page Application HTML body shell
    ├── css/
    │   └── style.css      # Premium dark glassmorphism stylesheet
    ├── js/
    │   └── app.js         # Reactive UI, API requester, AI chat, and forms validator
    ├── images/            # Graphic assets & fallback avatars
    └── photos/            # Destination folder for downloaded user profile photos
```

---

## 🛠️ Installation & Quickstart Guide

Since Python is fully operational on your computer, follow these simple terminal commands to set up the project locally:

### 1. Open Terminal and Navigate
Open PowerShell or Command Prompt, and navigate to the project directory:
```powershell
cd "c:\Users\User_203-9\Desktop\bot"
```

### 2. Set Up a Python Virtual Environment
We recommend creating an isolated virtual environment (`venv`) to keep dependencies self-contained:
```powershell
python -m venv venv
```
Activate the virtual environment:
* **Windows (PowerShell)**:
  ```powershell
  .\venv\Scripts\Activate.ps1
  ```
* **Windows (Command Prompt)**:
  ```cmd
  .\venv\Scripts\activate.bat
  ```

### 3. Install Package Dependencies
Install the required packages using pip:
```powershell
pip install -r requirements.txt
```

### 4. Create local `.env` Configuration (Optional)
Create a `.env` file in the root folder `c:\Users\User_203-9\Desktop\bot\` to configure your production keys:
```env
BOT_TOKEN=YOUR_TELEGRAM_BOT_TOKEN
CHANNEL_USERNAME=@your_channel_username
DEV_MODE=True
PORT=8000
```
* *Note*: If you do not create a `.env` file, the system automatically runs in **Developer Fallback Mode** (mocking bot connections so you can test immediately in the browser).

### 5. Launch the Application!
Run the main startup script:
```powershell
python main.py
```
This single command will:
1. Initialize the SQLite database `quiz_bot.db`.
2. Start the Telegram Bot background polling thread (if `BOT_TOKEN` is supplied).
3. Start the FastAPI local server at `http://localhost:8000`.

---

## 🖥️ How to Test & Review

### 1. Test in Local Browser (Demo Mode)
No Telegram configuration is needed!
1. Open your web browser and go to: `http://localhost:8000`
2. The app will detect that you are in a standard browser, load a mock developer account, and unlock all features.
3. Try:
   * **Quizzes**: Select a subject (e.g. Mathematics), answer some questions (e.g. "What is 5 + 7?" -> type `12` and click Submit). You will see custom success banners and your balance increase by 10 so'm.
   * **Wallet**: View your accrued earnings. Once balance >= 1000 so'm, the yechish (withdrawal) UzCard/Humo form unlocks! Type in your name and card number (auto-spaces credit cards), submit, and see it recorded in your logs.
   * **AI Assistant**: Click the floating robot bubble in the bottom corner and pick any question button to see responsive animated AI chats.
   * **Profile**: View your Telegram metadata, including verified contact labels.

### 2. Connect to Live Telegram
To test live inside the Telegram app:
1. Create a bot using [@BotFather](https://t.me/BotFather) on Telegram and copy the `BOT_TOKEN`.
2. Create a public Channel, add your bot as an **Administrator** with permission to post messages/invite links.
3. Use a tunneling tool like **ngrok** to create a public HTTPS tunnel for your local server:
   ```bash
   ngrok http 8000
   ```
4. Copy the secure HTTPS URL provided by ngrok (e.g. `https://a1b2-c3d4.ngrok-free.app`).
5. Open `@BotFather` and register a new WebApp for your bot via `/newapp`. Point the WebApp URL to your ngrok HTTPS URL.
6. Create/update your `.env` file:
   ```env
   BOT_TOKEN=your_bot_token_here
   CHANNEL_USERNAME=@your_channel_username
   MINI_APP_URL=https://your-ngrok-https-url.app
   DEV_MODE=False
   ```
7. Start `python main.py` again. Open the bot on Telegram and send `/start`. The full production flow (Force Join, Shared Contacts, verified Profile Photo downloads) is now live!
