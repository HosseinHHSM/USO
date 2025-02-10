import os
import json
import pandas as pd
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
from datetime import datetime

# --- تنظیمات اولیه ---
TOKEN = os.getenv("BOT_TOKEN")  # توکن از متغیر محیطی خوانده می‌شود
EXCEL_FILES = {
    "RF_PLAN": "RF PLAN.xlsx",  # فایل اکسل RF Plan
    "MASTER": "Master.xlsx",    # فایل اکسل Master
    "TARGET_VILLAGE": "Target Village.xlsx"  # فایل اکسل Target Village
}
AUTHORIZED_USERS_FILE = "authorized_users.json"  # فایل JSON برای ذخیره اطلاعات کاربران تأیید شده
VERIFICATION_CODES = {
    "766060", "296752", "783213", "047129", "188709", "904796", "086363",
    "144584", "866372", "394644", "808387", "343647", "917012", "920483",
    "292397", "604952", "714342", "390238", "406511", "714780"
}  # لیست کدهای تأیید

# --- بارگذاری اطلاعات کاربران از فایل JSON ---
def load_authorized_users():
    if os.path.exists(AUTHORIZED_USERS_FILE):
        with open(AUTHORIZED_USERS_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    return {}

# --- ذخیره اطلاعات کاربران به فایل JSON ---
def save_authorized_users():
    with open(AUTHORIZED_USERS_FILE, "w", encoding="utf-8") as file:
        json.dump(AUTHORIZED_USERS, file, ensure_ascii=False, indent=4)

# --- تابع خواندن اطلاعات از اکسل ---
def get_site_info(site_id, file_type):
    try:
        # نام فایل اکسل را از دیکشنری بر اساس نوع فایل انتخاب می‌کنیم
        df = pd.read_excel(EXCEL_FILES[file_type], engine="openpyxl")
        rows = df[df["Site ID"].astype(str) == str(site_id)]  # بررسی Site ID به عنوان رشته

        if rows.empty:
            return "❌ سایت یافت نشد."

        # اگر چندین ردیف برای یک Site ID وجود داشته باشد، باید آن‌ها را ترکیب کنیم
        info = f"📡 **Site ID:** {site_id}\n"
        for _, row in rows.iterrows():
            info += "\n"
            for col in df.columns:
                info += f"**{col}:** {row[col]}\n"
            info += "----------------------------\n"  # جداکننده برای هر ردیف

        return info
    except Exception as e:
        return f"⚠️ خطا در خواندن فایل اکسل: {str(e)}"

# --- پیام خوش‌آمدگویی و شروع ---
async def start(update: Update, context: CallbackContext):
    user_id = update.message.chat_id
    if user_id in AUTHORIZED_USERS:
        await update.message.reply_text(
            "✅ شما قبلاً تأیید شده‌اید! لطفاً یک گزینه را انتخاب کنید:\n"
            "1. بررسی دیتا از اسمارت ترکر\n"
            "2. بررسی دیتا در مستر ترکر\n"
            "3. بررسی دیتا در Target Village"
        )
    else:
        await update.message.reply_text("👋 سلام به دستیار هوشمند تیم USO Radio Planning خوش آمدید! لطفاً کد تأیید خود را وارد کنید.")

# --- هندلر تأیید هویت و پردازش Site ID در یک تابع ---
async def handle_user_input(update: Update, context: CallbackContext):
    user_id = update.message.chat_id
    user_input = update.message.text.strip()

    # اگر کاربر تأیید نشده است، پیام را به عنوان کد تأیید بررسی کن
    if user_id not in AUTHORIZED_USERS:
        if user_input in VERIFICATION_CODES:
            AUTHORIZED_USERS[user_id] = {"verified": True}
            save_authorized_users()  # ذخیره اطلاعات پس از تأیید
            await update.message.reply_text(
                "✅ تبریک! شما مجاز به استفاده از خدمات ربات هستید، لطفاً یکی از گزینه های زیر را انتخاب کنید:\n"
                "1. بررسی دیتا از اسمارت ترکر\n"
                "2. بررسی دیتا در مستر ترکر\n"
                "3. بررسی دیتا در Target Village"
            )
        else:
            await update.message.reply_text("❌ کد ورود اشتباه است. لطفاً دوباره امتحان کنید.")
        return

    # اگر کاربر تأیید شده است، پیام را به عنوان Site ID پردازش کن
    if user_input == "1":
        await update.message.reply_text("لطفاً Site ID را وارد کنید برای اسمارت ترکر.")
    elif user_input == "2":
        await update.message.reply_text("لطفاً Site ID را وارد کنید برای مستر ترکر.")
    elif user_input == "3":
        await update.message.reply_text("لطفاً Site ID را وارد کنید برای Target Village.")
    else:
        # بررسی داده در هر فایل اکسل بر اساس Site ID
        if "RF PLAN" in user_input:
            site_id = user_input.replace("RF PLAN", "").strip()  # پاک کردن پیشوند
            response = get_site_info(site_id, "RF_PLAN")
            await update.message.reply_text(response, parse_mode="Markdown")
        elif "MASTER" in user_input:
            site_id = user_input.replace("MASTER", "").strip()  # پاک کردن پیشوند
            response = get_site_info(site_id, "MASTER")
            await update.message.reply_text(response, parse_mode="Markdown")
        elif "TARGET VILLAGE" in user_input:
            site_id = user_input.replace("TARGET VILLAGE", "").strip()  # پاک کردن پیشوند
            response = get_site_info(site_id, "TARGET_VILLAGE")
            await update.message.reply_text(response, parse_mode="Markdown")
        else:
            await update.message.reply_text("❌ انتخاب نامعتبر بود. لطفاً دوباره تلاش کنید.")

# --- تابع برای بررسی زمان و توقف ربات بین 12 شب تا 8 صبح ---
def check_time():
    now = datetime.now()
    if now.hour >= 0 and now.hour < 8:
        return True
    return False

# --- راه‌اندازی بات ---
def main():
    global AUTHORIZED_USERS
    AUTHORIZED_USERS = load_authorized_users()  # بارگذاری اطلاعات کاربران

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_user_input))  # مدیریت همه ورودی‌های متنی

    print("🤖 Bot is running...")
    
    # بررسی زمان و توقف ربات در ساعت‌های مشخص شده
    if check_time():
        print("🔴 ربات در ساعات خاموشی است. تا ساعت 8 صبح متوقف خواهد بود.")
        return  # ربات در ساعت خاموشی متوقف می‌شود.

    app.run_polling()

if __name__ == "__main__":
    if not TOKEN:
        raise ValueError("❌ خطا: توکن ربات در متغیرهای محیطی تنظیم نشده است!")
    main()
