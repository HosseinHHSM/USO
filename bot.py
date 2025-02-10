import os
import pandas as pd
import requests
from io import BytesIO
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext

# --- تنظیمات اولیه ---
TOKEN = os.getenv("BOT_TOKEN")  # توکن از متغیر محیطی خوانده می‌شود
EXCEL_FILE_RF = "https://github.com/HosseinHHSM/USO/blob/main/RF%20PLAN.xlsx?raw=true"
EXCEL_FILE_MASTER = "https://github.com/HosseinHHSM/USO/blob/main/Master.xlsx?raw=true"
EXCEL_FILE_TARGET = "https://github.com/HosseinHHSM/USO/blob/main/Target%20village.xlsx?raw=true"

AUTHORIZED_USERS = set()  # مجموعه‌ای از کاربران تأیید شده
VERIFICATION_CODES = {
    "766060", "296752", "783213", "047129", "188709", "904796", "086363",
    "144584", "866372", "394644", "808387", "343647", "917012", "920483",
    "292397", "604952", "714342", "390238", "406511", "714780"
}  # لیست کدهای تأیید

# --- تابع بارگذاری و خواندن داده‌ها از اکسل ---
def read_excel_from_url(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # بررسی صحت درخواست
        excel_data = BytesIO(response.content)
        df = pd.read_excel(excel_data, engine="openpyxl")
        return df
    except Exception as e:
        print(f"Error loading Excel: {str(e)}")
        return None

# تابع خواندن اطلاعات از اکسل‌ها بر اساس سایت
def get_site_info(site_id, source):
    if source == "RF_PLAN":
        df = read_excel_from_url(EXCEL_FILE_RF)
    elif source == "MASTER":
        df = read_excel_from_url(EXCEL_FILE_MASTER)
    elif source == "TARGET_VILLAGE":
        df = read_excel_from_url(EXCEL_FILE_TARGET)
    else:
        return "❌ منبع نادرست است."

    if df is None:
        return "⚠️ خطا در بارگذاری فایل اکسل."

    # جستجو بر اساس Site ID
    row = df[df["Site ID"].astype(str) == str(site_id)]
    if row.empty:
        return "❌ سایت یافت نشد."
    
    # ساختار اطلاعات برای ارسال
    info = f"📡 **Site ID:** {site_id}\n"
    for col in df.columns:
        info += f"**{col}:** {row.iloc[0][col]}\n"
    
    return info

# --- پیام خوش‌آمدگویی و شروع ---
async def start(update: Update, context: CallbackContext):
    user_id = update.message.chat_id
    if user_id in AUTHORIZED_USERS:
        await update.message.reply_text("✅ شما قبلاً تأیید شده‌اید! لطفاً یکی از گزینه‌ها را انتخاب کنید.", reply_markup=main_menu_keyboard())
    else:
        await update.message.reply_text("👋 خوش آمدید! لطفاً کد تأیید خود را وارد کنید.")

# --- هندلر تأیید هویت ---
async def handle_user_input(update: Update, context: CallbackContext):
    user_id = update.message.chat_id
    user_input = update.message.text.strip()

    # اگر کاربر تأیید نشده است
    if user_id not in AUTHORIZED_USERS:
        if user_input in VERIFICATION_CODES:
            AUTHORIZED_USERS.add(user_id)
            await update.message.reply_text("✅ تأیید موفقیت‌آمیز بود! لطفاً یکی از گزینه‌ها را انتخاب کنید.", reply_markup=main_menu_keyboard())
        else:
            await update.message.reply_text("❌ کد نادرست است. لطفاً دوباره امتحان کنید.")
        return

    # اگر کاربر تأیید شده است
    if user_input == "1":
        await update.message.reply_text("📋 لطفاً Site ID را وارد کنید.")
        context.user_data['source'] = 'RF_PLAN'
    elif user_input == "2":
        await update.message.reply_text("📋 لطفاً Site ID را وارد کنید.")
        context.user_data['source'] = 'MASTER'
    elif user_input == "3":
        await update.message.reply_text("📋 لطفاً Site ID را وارد کنید.")
        context.user_data['source'] = 'TARGET_VILLAGE'
    else:
        await update.message.reply_text("❌ انتخاب نا معتبر است. لطفاً دوباره انتخاب کنید.", reply_markup=main_menu_keyboard())

# --- تابع دریافت اطلاعات از اکسل ---
async def handle_site_id(update: Update, context: CallbackContext):
    user_id = update.message.chat_id
    site_id = update.message.text.strip()

    source = context.user_data.get('source')
    if source:
        response = get_site_info(site_id, source)
        await update.message.reply_text(response)

        # بعد از نمایش دیتا، منوی اصلی رو نشون بده
        await update.message.reply_text("لطفاً یکی از گزینه‌ها را انتخاب کنید.", reply_markup=main_menu_keyboard())

# --- منوی اصلی ---
def main_menu_keyboard():
    from telegram import ReplyKeyboardMarkup
    keyboard = [
        ["1. بررسی دیتا از اسمارت ترکر", "2. بررسی دیتا از مستر ترکر"],
        ["3. بررسی دیتا از Target Village"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# --- راه‌اندازی بات ---
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_user_input))  # مدیریت ورودی‌های متن
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_site_id))  # مدیریت Site ID

    print("🤖 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    if not TOKEN:
        raise ValueError("❌ خطا: توکن ربات در متغیرهای محیطی تنظیم نشده است!")
    main()
