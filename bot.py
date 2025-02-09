import os
import pandas as pd
import json
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext

# --- تنظیمات اولیه ---
TOKEN = os.getenv("BOT_TOKEN")  # توکن از متغیر محیطی خوانده می‌شود
EXCEL_FILE = "RF PLAN.xlsx"  # نام فایل اکسل
AUTHORIZED_USERS_FILE = 'authorized_users.json'  # فایل JSON برای ذخیره کاربران تأیید شده

# تابع بارگذاری کاربران تأیید شده از فایل JSON
def load_authorized_users():
    try:
        with open(AUTHORIZED_USERS_FILE, 'r') as f:
            return set(json.load(f))
    except (FileNotFoundError, json.JSONDecodeError):
        return set()

# تابع ذخیره کاربران تأیید شده به فایل JSON
def save_authorized_users():
    with open(AUTHORIZED_USERS_FILE, 'w') as f:
        json.dump(list(AUTHORIZED_USERS), f)

# بارگذاری کاربران تأیید شده هنگام شروع ربات
AUTHORIZED_USERS = load_authorized_users()

# لیست کدهای تأیید
VERIFICATION_CODES = {
    "766060", "296752", "783213", "047129", "188709", "904796", "086363",
    "144584", "866372", "394644", "808387", "343647", "917012", "920483",
    "292397", "604952", "714342", "390238", "406511", "714780"
}

# --- تابع خواندن اطلاعات از اکسل ---
def get_site_info(site_id):
    try:
        df = pd.read_excel(EXCEL_FILE, engine="openpyxl")
        row = df[df["Site ID"].astype(str) == str(site_id)]  # بررسی Site ID به عنوان رشته
        if row.empty:
            return "❌ سایت مورد نظر یافت نشد، لطفا در نظر داشته باشید که شما به نسخه آفلاین ترکر دسترسی دارید و احتمال دارد سایت شما بعد از تاریخ به روز رسانی ما آپدیت شده است."
        
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
        await update.message.reply_text("👋 سلام دوست عزیز،خوش آمدید! لطفاً کد تأیید خود را وارد کنید.")

# --- هندلر تأیید هویت و پردازش Site ID در یک تابع ---
async def handle_user_input(update: Update, context: CallbackContext):
    user_id = update.message.chat_id
    user_input = update.message.text.strip()

    # اگر کاربر تأیید نشده است، پیام را به عنوان کد تأیید بررسی کن
    if user_id not in AUTHORIZED_USERS:
        if user_input in VERIFICATION_CODES:
            AUTHORIZED_USERS.add(user_id)
            save_authorized_users()  # ذخیره کردن اطلاعات جدید
            await update.message.reply_text("✅ شما مجاز هستید! لطفاً Site ID را وارد کنید.")
        else:
            await update.message.reply_text("❌ کد ورود نادرست است. لطفاً دوباره امتحان کنید.")
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
