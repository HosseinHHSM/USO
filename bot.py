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

VERIFICATION_CODES = {
    "766060", "296752", "783213", "047129", "188709",
    "904796", "086363", "144584", "866372", "394644",
    "808387", "343647", "917012", "920483", "292397",
    "604952", "714342", "390238", "406511", "714780"
}

def load_authorized_users():
    try:
        with open(AUTHORIZED_USERS_FILE, 'r', encoding='utf-8') as f:
            return set(json.load(f))
    except Exception:
        return set()

def save_authorized_users(auth_users: set):
    with open(AUTHORIZED_USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(list(auth_users), f)

AUTHORIZED_USERS = load_authorized_users()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None:
        return
    
    user_id = update.message.chat_id
    if user_id not in AUTHORIZED_USERS:
        await update.message.reply_text("👋 **سلام!**\nمن **دستیار هوشمند تیم USO Radio Planning** هستم. برای شروع لطفاً کد تأیید خود را وارد کنید.")
    else:
        keyboard = [
            ["Smart Tracker", "Master Tracker", "Target Village"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)
        await update.message.reply_text("✅ شما تأیید شده‌اید!\nلطفاً یک گزینه را انتخاب کنید:", reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None:
        return
    text = update.message.text.strip()

    if text in ["Smart Tracker", "Master Tracker", "Target Village"]:
        context.user_data['tracker_type'] = text.lower().replace(" ", "_")  # ذخیره نوع ترکر در context
        await update.message.reply_text("🔹 لطفاً Site ID را وارد کنید:")
    else:
        await update.message.reply_text("❌ لطفاً از گزینه‌های موجود استفاده کنید.")

async def site_id_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None:
        return
    site_id = update.message.text.strip()
    
    # اگر کاربر گزینه‌ای انتخاب نکرده باشد، آخرین انتخاب را در نظر بگیرد
    tracker_type = context.user_data.get('tracker_type')

    if not tracker_type:
        keyboard = [["Smart Tracker", "Master Tracker", "Target Village"]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)
        await update.message.reply_text("🔹 لطفاً ابتدا یک گزینه را انتخاب کنید:", reply_markup=reply_markup)
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

async def auth_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None:
        return
    user_id = update.message.chat_id
    text = update.message.text.strip()
    
    if user_id not in AUTHORIZED_USERS:
        if text in VERIFICATION_CODES:
            AUTHORIZED_USERS.add(user_id)
            save_authorized_users(AUTHORIZED_USERS)
            await update.message.reply_text("✅ تأیید موفقیت‌آمیز! لطفاً از /start برای ادامه استفاده کنید.")
        else:
            await update.message.reply_text("❌ کد تأیید نادرست است. لطفاً دوباره امتحان کنید.")
    else:
        await site_id_handler(update, context)
        
async def main_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.chat_id
    if user_id not in AUTHORIZED_USERS:
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
