import os
import pandas as pd
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext

# --- تنظیمات ---
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")  # توکن را از متغیر محیطی دریافت کن
EXCEL_FILE = "RF PLAN.xlsx"  # فایل اکسل داده‌ها
AUTHORIZED_USERS = {}  # ذخیره کاربران تأیید شده
VERIFICATION_CODES = {"766060", "296752", "783213", "047129", "188709", "904796", "086363", "144584", "866372", "394644",
                      "808387", "343647", "917012", "920483", "292397", "604952", "714342", "390238", "406511", "714780"}  # کدهای تأیید

if not TOKEN:
    raise ValueError("❌ خطا: توکن ربات در متغیرهای محیطی تنظیم نشده است!")

# --- خواندن داده از اکسل ---
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
        return f"⚠️ خطا در خواندن داده‌ها: {str(e)}"

# --- پیام خوش‌آمدگویی ---
async def start(update: Update, context: CallbackContext):
    user_id = update.message.chat_id
    if user_id in AUTHORIZED_USERS:
        await update.message.reply_text("✅ شما قبلاً تأیید شده‌اید! لطفاً Site ID را وارد کنید.")
    else:
        await update.message.reply_text("👋 خوش آمدید! لطفاً کد تأیید خود را وارد کنید.")

# --- بررسی و تأیید کد ---
async def verify(update: Update, context: CallbackContext):
    user_id = update.message.chat_id
    message_text = update.message.text.strip()

    if user_id in AUTHORIZED_USERS:
        # اگر قبلاً تأیید شده، درخواست Site ID کند
        await update.message.reply_text("✅ شما قبلاً تأیید شده‌اید! لطفاً Site ID را وارد کنید.")
        return

    if message_text in VERIFICATION_CODES:
        AUTHORIZED_USERS[user_id] = True
        await update.message.reply_text("✅ تأیید موفقیت‌آمیز بود! لطفاً Site ID را وارد کنید.")
    else:
        await update.message.reply_text("❌ کد اشتباه است. لطفاً دوباره تلاش کنید.")

# --- دریافت اطلاعات Site ID ---
async def handle_site_id(update: Update, context: CallbackContext):
    user_id = update.message.chat_id
    message_text = update.message.text.strip()

    if user_id not in AUTHORIZED_USERS:
        await update.message.reply_text("❌ شما ابتدا باید تأیید شوید. لطفاً کد تأیید خود را وارد کنید.")
        return

    # جستجو و ارسال اطلاعات سایت
    response = get_site_info(message_text)
    await update.message.reply_text(response, parse_mode="Markdown")

# --- راه‌اندازی ربات ---
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, verify))  # مرحله تأیید
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_site_id))  # مرحله دریافت Site ID

    print("✅ Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
