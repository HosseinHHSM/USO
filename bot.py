import os
import pandas as pd
import json
import requests
from io import BytesIO
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    filters, ContextTypes
)

TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise ValueError("BOT_TOKEN is not set in environment variables!")

AUTHORIZED_USERS_FILE = 'authorized_users.json'
USER_CREDENTIALS = {
    "Kamran-HH": "qxubRvAa",
    "Sadegh-HH": "5TybgdUV",
    "Mehran-HH": "R8PnX3yZ",
    "Nima-HH": "2JvWk6mT",
    "Arshia-HH": "L7qBpVzM",
    "Saeideh-HH": "9XtFwLrC",
    "Paria-HH": "H5KmNvXp",
    "Amirreza-HH": "3YrLtWQZ",
    "Mehrnoush-HH": "Z8MkpL6X",
    "Amir-HH": "J9QvXtB5",
    "Hossein-HH": "V4NpK2mT",
    **{f"Guest-{i:02d}": p for i, p in enumerate([
        "P7XqL8vM", "6TWNJ5Kv", "X3BZ9rLt", "L5QTN8Xv", "7XmR2KPJ",
        "W3NQLX85", "8PJXK2TN", "Q9TNX7KP", "L6Xv5JQW", "X8KP9QTN",
        "2M7QLXKP", "P5TXJNQ8", "K9XTL3NQ", "J7XKQ5TN", "4WPNXJQK",
        "X5KTN9LQ", "6QPNJXKT", "8LXTQ7PN", "X2NTKQJP"
    ], 1)}
}

RF_PLAN_URL = "https://github.com/HosseinHHSM/USO/raw/main/RF%20PLAN.xlsx"
MASTER_URL = "https://github.com/HosseinHHSM/USO/raw/main/Master.xlsx"
TARGET_VILLAGE_URL = "https://github.com/HosseinHHSM/USO/raw/main/Target%20village.xlsx"

def load_authorized_users():
    try:
        with open(AUTHORIZED_USERS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}

def save_authorized_users(auth_users: dict):
    with open(AUTHORIZED_USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(auth_users, f)

authorized_users = load_authorized_users()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None:
        return
    user_id = str(update.message.chat_id)
    if user_id in authorized_users:
        keyboard = [["Smart Tracker", "Master Tracker", "Target Village"]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)
        await update.message.reply_text("✅ شما تأیید شده‌اید!\nلطفاً یک گزینه را انتخاب کنید:", reply_markup=reply_markup)
    else:
        await update.message.reply_text("👋 سلام!\nلطفاً یوزرنیم و پسورد خود را به این صورت ارسال کنید: \n`یوزرنیم:پسورد`", parse_mode="Markdown")

async def auth_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None:
        return
    user_id = str(update.message.chat_id)
    text = update.message.text.strip()
    
    if user_id in authorized_users:
        await start(update, context)
        return
    
    if ":" in text:
        username, password = text.split(":", 1)
        username, password = username.strip(), password.strip()
        
        if username in USER_CREDENTIALS and USER_CREDENTIALS[username] == password:
            if username not in authorized_users.values():
                authorized_users[user_id] = username
                save_authorized_users(authorized_users)
                await update.message.reply_text("✅ ورود موفقیت‌آمیز! از /start برای ادامه استفاده کنید.")
            else:
                await update.message.reply_text("❌ این اکانت قبلاً توسط شخص دیگری ثبت شده است. شما مجاز به استفاده از آن نیستید.")
        else:
            await update.message.reply_text("❌ یوزرنیم یا پسورد نادرست است.")
    else:
        await update.message.reply_text("⚠️ لطفاً یوزرنیم و پسورد را به این فرمت ارسال کنید: \n`یوزرنیم:پسورد`", parse_mode="Markdown")

def main() -> None:
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, auth_handler))
    
    print("✅ Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
