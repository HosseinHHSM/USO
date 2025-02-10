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

RF_PLAN_URL = "https://github.com/HosseinHHSM/USO/raw/main/RF%20PLAN.xlsx"
MASTER_URL = "https://github.com/HosseinHHSM/USO/raw/main/Master.xlsx"
TARGET_VILLAGE_URL = "https://github.com/HosseinHHSM/USO/raw/main/Target%20village.xlsx"

def read_excel(url: str):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return pd.read_excel(BytesIO(response.content), engine="openpyxl")
    except Exception as e:
        print(f"Error reading Excel from {url}: {e}")
        return None

rf_plan_df = read_excel(RF_PLAN_URL)
master_df = read_excel(MASTER_URL)
target_village_df = read_excel(TARGET_VILLAGE_URL)

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
        await update.message.reply_text("👋 سلام!به دستیار هوشمند تیم USO radio planing خوش آمدید لطفاً یوزرنیم و پسورد خود را به این صورت ارسال کنید:\n`یوزرنیم:پسورد`", parse_mode="Markdown")

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
                await update.message.reply_text("✅ شما مجاز به استفاده از خدمات ربات هستید! از /start برای ادامه استفاده کنید.")
                # حذف پیام یوزرنیم و پسورد پس از ورود موفق
                await update.message.delete()
            else:
                await update.message.reply_text("❌ این اکانت قبلاً توسط شخص دیگری ثبت شده است. شما مجاز به استفاده از آن نیستید.")
        else:
            await update.message.reply_text("❌ یوزرنیم یا پسورد نادرست است.")
    else:
        await update.message.reply_text("⚠️ لطفاً یوزرنیم و پسورد را به این فرمت ارسال کنید: \n`یوزرنیم:پسورد`", parse_mode="Markdown")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None:
        return
    text = update.message.text.strip()

    if text in ["Smart Tracker", "Master Tracker", "Target Village"]:
        context.user_data['tracker_type'] = text.lower().replace(" ", "_")
        await update.message.reply_text("🔹 لطفاً Site ID را وارد کنید:")
    else:
        await update.message.reply_text("❌ لطفاً یکی از گزینه‌های منو را انتخاب کنید.")

async def site_id_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None:
        return
    site_id = update.message.text.strip()

    tracker_type = context.user_data.get('tracker_type')

    if not tracker_type:
        keyboard = [["Smart Tracker", "Master Tracker", "Target Village"]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)
        await update.message.reply_text("🔹 لطفاً ابتدا یک گزینه از منو را انتخاب کنید:", reply_markup=reply_markup)
        return

    df = {
        "smart_tracker": rf_plan_df,
        "master_tracker": master_df,
        "target_village": target_village_df
    }.get(tracker_type)

    if df is None or df.empty:
        await update.message.reply_text("⚠️ اطلاعاتی برای این Site ID یافت نشد.")
        return

    result = df[df["Site ID"].astype(str).str.strip().str.lower() == site_id.lower()]
    if result.empty:
        await update.message.reply_text("⚠️ اطلاعاتی برای این Site ID یافت نشد.")
    else:
        message_text = "\n\n".join(result.astype(str).apply(lambda row: "\n".join(f"{col}: {row[col]}" for col in result.columns), axis=1))
        await update.message.reply_text(message_text, parse_mode="Markdown")

async def main_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.message.chat_id)
    text = update.message.text.strip()

    if text in ["Smart Tracker", "Master Tracker", "Target Village"]:
        await button_handler(update, context)
    elif user_id not in authorized_users:
        await auth_handler(update, context)
    else:
        await site_id_handler(update, context)

def main() -> None:
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, main_text_handler))

    print("✅ Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
