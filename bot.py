import os
import pandas as pd
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext

# --- دریافت توکن از متغیر محیطی ---
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# --- بررسی مقدار توکن ---
if not TOKEN:
    raise ValueError("❌ خطا: توکن ربات در متغیرهای محیطی تنظیم نشده است!")

EXCEL_FILE = "RF PLAN.xlsx"

AUTHORIZED_USERS = {}  # کاربران تأییدشده
VERIFICATION_CODES = {
    "766060", "296752", "783213", "047129", "188709", "904796", "086363", "144584", "866372", "394644",
    "808387", "343647", "917012", "920483", "292397", "604952", "714342", "390238", "406511", "714780"
}  # کدهای تأیید

# --- خواندن اطلاعات از اکسل ---
def get_site_info(site_id):
    try:
        df = pd.read_excel(EXCEL_FILE, engine="openpyxl")
        row = df[df["Site ID"] == site_id]

        if row.empty:
            return "❌ Site not found."

        info = f"📡 **Site ID:** {site_id}\n"
        for col in df.columns:
            info += f"**{col}:** {row.iloc[0][col]}\n"

        return info

    except Exception as e:
        return f"❌ خطا در خواندن فایل اکسل: {e}"

# --- پیام خوش‌آمدگویی ---
async def start(update: Update, context: CallbackContext):
    user_id = update.message.chat_id
    if user_id in AUTHORIZED_USERS:
        await update.message.reply_text("✅ شما قبلاً تأیید شده‌اید! لطفاً Site ID را وارد کنید.")
    else:
        await update.message.reply_text("👋 خوش آمدید! لطفاً کد تأیید خود را وارد کنید.")

# --- فرآیند تأیید هویت ---
async def verify(update: Update, context: CallbackContext):
    user_id = update.message.chat_id
    code = update.message.text.strip()

    if user_id in AUTHORIZED_USERS:
        await update.message.reply_text("✅ شما قبلاً تأیید شده‌اید! لطفاً Site ID را وارد کنید.")
        return

    if code in VERIFICATION_CODES:
        AUTHORIZED_USERS[user_id] = True
        await update.message.reply_text("✅ تأیید موفقیت‌آمیز بود! لطفاً Site ID را وارد کنید.")
    else:
        await update.message.reply_text("❌ کد نادرست است. لطفاً دوباره امتحان کنید.")

# --- پردازش Site ID ---
async def handle_site_id(update: Update, context: CallbackContext):
    user_id = update.message.chat_id
    if user_id not in AUTHORIZED_USERS:
        await update.message.reply_text("❌ ابتدا باید تأیید شوید. لطفاً کد تأیید خود را وارد کنید.")
        return

    site_id = update.message.text.strip()
    response = get_site_info(site_id)
    await update.message.reply_text(response, parse_mode="Markdown")

# --- راه‌اندازی ربات ---
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, verify))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_site_id))

    print("✅ ربات در حال اجرا است...")
    app.run_polling()

if __name__ == "__main__":
    main()
