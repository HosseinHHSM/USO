import os
import pandas as pd
import json
import requests
from io import BytesIO
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext

# --- تنظیمات اولیه ---
TOKEN = os.getenv("BOT_TOKEN")  # توکن از متغیر محیطی خوانده می‌شود
AUTHORIZED_USERS_FILE = 'authorized_users.json'  # فایل JSON برای ذخیره کاربران تأیید شده
EXCEL_FILES = {
    "smart_tracker": "https://github.com/HosseinHHSM/USO/raw/main/RF%20PLAN.xlsx",
    "master_tracker": "https://github.com/HosseinHHSM/USO/raw/main/Master.xlsx",
    "target_village": "https://github.com/HosseinHHSM/USO/raw/main/Target%20village.xlsx"
}  # لینک‌های raw برای هر فایل اکسل

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
def read_excel_from_url(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            excel_data = BytesIO(response.content)
            df = pd.read_excel(excel_data, engine="openpyxl")
            return df
        else:
            return None
    except Exception as e:
        return None

# تابع برای گرفتن اطلاعات از اکسل مربوطه
def get_site_info(site_id, tracker_type):
    # بارگذاری فایل اکسل مربوط به نوع ترکر
    if tracker_type not in EXCEL_FILES:
        return "❌ نوع ترکر نامعتبر است."

    df = read_excel_from_url(EXCEL_FILES[tracker_type])
    
    if df is None:
        return "⚠️ خطا در بارگذاری فایل اکسل."

    row = df[df["Site ID"].astype(str) == str(site_id)]  # بررسی Site ID به عنوان رشته
    if row.empty:
        return "❌ سایت مورد نظر یافت نشد."

    info = f"📡 **Site ID:** {site_id}\n"
    for col in df.columns:
        info += f"**{col}:** {row.iloc[0][col]}\n"
    return info

# --- پیام خوش‌آمدگویی و شروع ---
async def start(update: Update, context: CallbackContext):
    user_id = update.message.chat_id
    if user_id in AUTHORIZED_USERS:
        # منو با سه گزینه نمایش داده می‌شود
        keyboard = [
            ["1- بررسی دیتا از اسمارت ترکر", "2- بررسی دیتا از مستر ترکر", "3- بررسی دیتا از Target Village"]
        ]
        reply_markup = {"keyboard": keyboard, "one_time_keyboard": True, "resize_keyboard": True}
        await update.message.reply_text("✅ شما قبلاً تأیید شده‌اید! لطفاً یک گزینه انتخاب کنید:", reply_markup=reply_markup)
    else:
        await update.message.reply_text("👋 سلام دوست عزیز، خوش آمدید! لطفاً کد تأیید خود را وارد کنید.")

# --- هندلر تأیید هویت و پردازش Site ID در یک تابع ---
async def handle_user_input(update: Update, context: CallbackContext):
    user_id = update.message.chat_id
    user_input = update.message.text.strip()

    # اگر کاربر تأیید نشده است، پیام را به عنوان کد تأیید بررسی کن
    if user_id not in AUTHORIZED_USERS:
        if user_input in VERIFICATION_CODES:
            AUTHORIZED_USERS.add(user_id)
            save_authorized_users()  # ذخیره کردن اطلاعات جدید
            await update.message.reply_text("✅ شما مجاز هستید! لطفاً یک گزینه انتخاب کنید:")
        else:
            await update.message.reply_text("❌ کد ورود نادرست است. لطفاً دوباره امتحان کنید.")
        return

    # اگر کاربر تأیید شده است، باید بررسی کند که کدام گزینه را انتخاب کرده
    if user_input == "1- بررسی دیتا از اسمارت ترکر":
        await update.message.reply_text("📡 لطفاً Site ID را وارد کنید:")
        context.user_data['tracker_type'] = "smart_tracker"  # ذخیره نوع ترکر
    elif user_input == "2- بررسی دیتا از مستر ترکر":
        await update.message.reply_text("📡 لطفاً Site ID را وارد کنید:")
        context.user_data['tracker_type'] = "master_tracker"
    elif user_input == "3- بررسی دیتا از Target Village":
        await update.message.reply_text("📡 لطفاً Site ID را وارد کنید:")
        context.user_data['tracker_type'] = "target_village"
    else:
        await update.message.reply_text("❌ انتخاب نامعتبر است. لطفاً دوباره انتخاب کنید.")

# --- هندلر دریافت Site ID ---
async def handle_site_id(update: Update, context: CallbackContext):
    user_id = update.message.chat_id
    site_id = update.message.text.strip()

    # دریافت نوع ترکر از context
    tracker_type = context.user_data.get('tracker_type', None)
    if tracker_type:
        response = get_site_info(site_id, tracker_type)
        await update.message.reply_text(response, parse_mode="Markdown")
    else:
        await update.message.reply_text("❌ ابتدا یک گزینه انتخاب کنید.")

# --- راه‌اندازی بات ---
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_user_input))  # مدیریت همه ورودی‌های متنی
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_site_id))  # مدیریت Site ID

    print("🤖 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    if not TOKEN:
        raise ValueError("❌ خطا: توکن ربات در متغیرهای محیطی تنظیم نشده است!")
    main()
