import os
import telebot
from telebot import types
import database
from config import BOT_TOKEN, CHANNEL_USERNAME, DEV_MODE, STATIC_DIR, PHOTOS_DIR, MINI_APP_URL

# Initialize the Bot object. 
# Handle empty BOT_TOKEN gracefully so that browser Demo Mode still works without crashes.
bot = None
if BOT_TOKEN:
    try:
        bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")
        print("[Bot] Telegram Bot initialized successfully.")
    except Exception as e:
        print(f"[Bot] Error initializing bot with provided token: {e}")
else:
    print("[Bot] WARNING: BOT_TOKEN is empty! Telegram Bot polling will NOT start.")
    print("[Bot] You can still test the Mini App directly in your browser (Demo Mode).")

def check_channel_membership(user_id: int):
    """Checks if the user is a member of the required channel.
    Returns:
      True: if the user is a member, or if the check failed due to bot permissions or other API issues (graceful bypass).
      False: if the user is not a member.
    """
    if not bot or DEV_MODE:
        return True  # Bypass check in DEV_MODE or if no bot token is set
        
    try:
        member = bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        if member.status in ['creator', 'administrator', 'member']:
            return True
        return False
    except Exception as e:
        print(f"[Bot] Channel membership check error for user {user_id}: {e}")
        print(f"[Bot] GRACEFUL FALLBACK: Bypassing force-join check because the bot encountered an error checking membership.")
        return True # Gracefully allow them to proceed

def get_join_keyboard() -> types.InlineKeyboardMarkup:
    """Returns the inline keyboard forcing users to join the official channel."""
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    clean_channel = CHANNEL_USERNAME.strip("@")
    join_url = f"https://t.me/{clean_channel}"
    
    btn_join = types.InlineKeyboardButton("A'zo bo'lish 📢 (Join Channel)", url=join_url)
    btn_check = types.InlineKeyboardButton("Tekshirish 🔄 (Check Membership)", callback_data="check_sub")
    
    markup.add(btn_join, btn_check)
    return markup

def get_contact_keyboard() -> types.ReplyKeyboardMarkup:
    """Returns the keyboard requesting user's contact number."""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    btn_phone = types.KeyboardButton("Telefon raqamni ulash 📞 (Share Phone Number)", request_contact=True)
    markup.add(btn_phone)
    return markup

def get_webapp_keyboard() -> types.ReplyKeyboardMarkup:
    """Returns the persistent keyboard with WebApp launch button."""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    web_app_info = types.WebAppInfo(url=MINI_APP_URL)
    btn_start = types.KeyboardButton("TESTNI BOSHLASH 🚀 (START QUIZ)", web_app=web_app_info)
    markup.add(btn_start)
    return markup

# Register message handlers if the bot is active
if bot:
    @bot.message_handler(commands=['start'])
    def handle_start(message):
        user_id = message.from_user.id
        print(f"[Bot] /start received from user {user_id}")
        
        # Step 1: Force Join Check
        if not check_channel_membership(user_id):
            bot.send_message(
                chat_id=message.chat.id,
                text=(
                    "⚠️ <b>Diqqat! Davom etish uchun kanalimizga a'zo bo'ling!</b>\n\n"
                    f"Botdan to'liq foydalanish va pul ishlash uchun quyidagi rasmiy kanalimizga a'zo bo'lishingiz shart:\n\n"
                    f"👉 {CHANNEL_USERNAME}\n\n"
                    "A'zo bo'lgach, 'Tekshirish 🔄' tugmasini bosing."
                ),
                reply_markup=get_join_keyboard()
            )
            return
            
        # Step 2: Already a member, request phone number
        send_welcome_flow(message.chat.id, message.from_user)

    @bot.callback_query_handler(func=lambda call: call.data == "check_sub")
    def handle_check_subscription(call):
        user_id = call.from_user.id
        print(f"[Bot] Callback subscription check for user {user_id}")
        
        if check_channel_membership(user_id):
            # Edit current message to show success
            try:
                bot.edit_message_text(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    text="✅ <b>A'zolik muvaffaqiyatli tekshirildi!</b>"
                )
            except Exception:
                pass
            
            # Send welcome flow
            send_welcome_flow(call.message.chat.id, call.from_user)
        else:
            bot.answer_callback_query(
                callback_query_id=call.id,
                text="❌ Siz hali kanalga a'zo bo'lmadingiz! Iltimos, avval a'zo bo'ling.",
                show_alert=True
            )

    @bot.message_handler(content_types=['contact'])
    def handle_contact(message):
        """Processes the shared contact, downloads the profile photo, and activates the profile."""
        user_id = message.from_user.id
        contact = message.contact
        
        if contact.user_id != user_id:
            bot.send_message(
                chat_id=message.chat.id,
                text="⚠️ **Xatolik!** Faqat o'zingizning telefon raqamingizni ulashingiz mumkin."
            )
            return
            
        phone_number = contact.phone_number
        if not phone_number.startswith("+"):
            phone_number = f"+{phone_number}"
            
        print(f"[Bot] Contact received from {user_id}: {phone_number}")
        
        # Download Profile Photo
        photo_url = "/static/images/default-avatar.png"  # Default fallback
        try:
            photos = bot.get_user_profile_photos(user_id, limit=1)
            if photos.total_count > 0:
                photo_file = photos.photos[0][-1]  # Get largest size
                file_info = bot.get_file(photo_file.file_id)
                downloaded_file = bot.download_file(file_info.file_path)
                
                # Save as photos/{user_id}.jpg under our static directory
                local_filename = f"photos/{user_id}.jpg"
                local_path = STATIC_DIR / local_filename
                
                with open(local_path, "wb") as f:
                    f.write(downloaded_file)
                photo_url = f"/static/photos/{user_id}.jpg"
                print(f"[Bot] Saved profile photo for user {user_id} at {local_filename}")
        except Exception as e:
            print(f"[Bot] Failed to download profile photo for {user_id}: {e}")
            
        # Save user to SQLite database
        username = message.from_user.username
        username_formatted = f"@{username}" if username else None
        
        user_db = database.create_or_update_user(
            telegram_id=user_id,
            username=username_formatted,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name,
            phone_number=phone_number,
            photo_url=photo_url
        )
        
        # Safe fallback in case database write returns None
        first_name_db = user_db.get('first_name', message.from_user.first_name) if user_db else message.from_user.first_name
        phone_number_db = user_db.get('phone_number', phone_number) if user_db else phone_number
        
        bot.send_message(
            chat_id=message.chat.id,
            text=(
                "🎉 <b>Hisobingiz muvaffaqiyatli ulandi!</b>\n\n"
                f"Ism: <b>{first_name_db}</b>\n"
                f"Raqam: <b>{phone_number_db}</b>\n\n"
                "Endi siz aqlli viktorinalarda qatnashib, haqiqiy pul topishga tayyorsiz! "
                "Har bir to'g'ri javob uchun hisobingizga <b>10 so'm</b> qo'shiladi.\n\n"
                "Pastdagi <b>'TESTNI BOSHLASH 🚀'</b> tugmasini bosing va o'yinni boshlang!"
            ),
            reply_markup=get_webapp_keyboard()
        )

    def send_welcome_flow(chat_id: int, user_info):
        """Helper to prompt the user to share their contact details."""
        bot.send_message(
            chat_id=chat_id,
            text=(
                f"👋 <b>Assalomu alaykum, {user_info.first_name}!</b>\n\n"
                "<b>SMART QUIZ BOT</b>ga xush kelibsiz! Bu bot orqali siz turli fanlardan o'z bilmingizni sinab ko'rishingiz va pul ishlashingiz mumkin.\n\n"
                "Botni faollashtirish uchun pastdagi tugmani bosib, telefon raqamingizni tasdiqlang. "
                "Bu xavfsizlik va mukofotlarni yechib olish uchun talab qilinadi."
            ),
            reply_markup=get_contact_keyboard()
        )

def start_bot_polling():
    """Starts the Telegram bot in a continuous polling loop (blocking)."""
    if bot:
        print("[Bot] Starting Telegram Bot polling engine...")
        # Ignore older updates when restarting
        bot.delete_webhook(drop_pending_updates=True)
        bot.infinity_polling()
    else:
        print("[Bot] Bot polling skipped because BOT_TOKEN is empty.")
