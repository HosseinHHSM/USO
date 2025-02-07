import os
import pandas as pd
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext

# --- تنظیمات اولیه ---
TOKEN = os.getenv("BOT_TOKEN")  # توکن از متغیر محیطی خوانده می‌شود
EXCEL_FILE = "RF PLAN.xlsx"  # نام فایل اکسل
AUTHORIZED_USERS = set()  # مجموعه‌ای از کاربران تأیید شده
VERIFICATION_CODES = {
    "766060", "296752", "783213", "047129", "188709", "904796", "086363",
    "144584", "866372", "394644", "808387", "343647", "917012", "920483",
    "292397", "604952", "714342", "390238", "406511", "714780"
}  # لیست کدهای تأیید

# --- تابع خواندن اطلاعات از اکسل ---
def get_site_info(site_id):
    try:
        df = pd.read_excel(EXCEL_FILE, engine="openpyxl")
        row = df[df["Site ID"].astype(str) == str(site_id)]  # بررسی Site ID به عنوان رشته
        if row.empty:
            return "❌ سایت یافت نشد."
        
        info = f"📡 **Site ID:** {site_id}\n"
        for col in df.columns:
            info += f"**{col}:** {row.iloc[0][col]}\n"
        return info
    except Exception as e:
        return f"⚠️ خطا در خواندن فایل اکسل: {str(e)}"

# --- پیام خوش‌آمدگویی و شروع ---
async def start(update: Update, context: CallbackContext):
    user_id = update.message.chat_id
    if user_id in AUTHORIZED_USERS:
        await update.message.reply_text("✅ شما قبلاً تأیید شده‌اید! لطفاً Site ID را وارد کنید.")
    else:
        await update.message.reply_text("👋 خوش آمدید! لطفاً کد تأیید خود را وارد کنید.")

# --- هندلر تأیید هویت و پردازش Site ID در یک تابع ---
async def handle_user_input(update: Update, context: CallbackContext):
    user_id = update.message.chat_id
    user_input = update.message.text.strip()

    # اگر کاربر تأیید نشده است، پیام را به عنوان کد تأیید بررسی کن
    if user_id not in AUTHORIZED_USERS:
        if user_input in VERIFICATION_CODES:
            AUTHORIZED_USERS.add(user_id)
            await update.message.reply_text("✅ تأیید موفقیت‌آمیز بود! لطفاً Site ID را وارد کنید.")
        else:
            await update.message.reply_text("❌ کد نادرست است. لطفاً دوباره امتحان کنید.")
        return

    # اگر کاربر تأیید شده است، پیام را به عنوان Site ID پردازش کن
    response = get_site_info(user_input)
    await update.message.reply_text(response, parse_mode="Markdown")

# --- راه‌اندازی بات ---
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_user_input))  # مدیریت همه ورودی‌های متنی

    print("🤖 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    if not TOKEN:
        raise ValueError("❌ خطا: توکن ربات در متغیرهای محیطی تنظیم نشده است!")
    main()
