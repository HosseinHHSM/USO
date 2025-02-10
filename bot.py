import os
import pandas as pd
import json
import requests
from io import BytesIO
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes
)

# خواندن توکن از متغیر محیطی
TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise ValueError("BOT_TOKEN is not set in environment variables!")

# فایل JSON برای ذخیره کاربران تأیید شده
AUTHORIZED_USERS_FILE = 'authorized_users.json'

# لینک‌های raw فایل‌های اکسل در گیت‌هاب
RF_PLAN_URL = "https://github.com/HosseinHHSM/USO/raw/main/RF%20PLAN.xlsx"
MASTER_URL = "https://github.com/HosseinHHSM/USO/raw/main/Master.xlsx"
TARGET_VILLAGE_URL = "https://github.com/HosseinHHSM/USO/raw/main/Target%20village.xlsx"

# دانلود و خواندن فایل‌های اکسل
def read_excel(url: str):
    try:
        response = requests.get(url)
        response.raise_for_status()  # در صورت خطا، استثناء ایجاد می‌کند
        excel_data = BytesIO(response.content)
        df = pd.read_excel(excel_data, engine="openpyxl")
        # برای دیباگ: چاپ ۵ ردیف اول
        print(f"File loaded from {url}:")
        print(df.head())
        return df
    except Exception as e:
        print(f"Error reading Excel from {url}: {e}")
        return None

# بارگذاری داده‌ها
rf_plan_df = read_excel(RF_PLAN_URL)
master_df = read_excel(MASTER_URL)
target_village_df = read_excel(TARGET_VILLAGE_URL)

# لیست کدهای تأیید
VERIFICATION_CODES = {
    "766060", "296752", "783213", "047129", "188709",
    "904796", "086363", "144584", "866372", "394644",
    "808387", "343647", "917012", "920483", "292397",
    "604952", "714342", "390238", "406511", "714780"
}

# توابع مربوط به ذخیره و بارگذاری کاربران تأیید شده
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

# تابع نمایش منوی اصلی (InlineKeyboard)
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None:
        return
    # اگر کاربر تأیید شده باشد، منو را نشان می‌دهد؛ در غیر این صورت، از کاربر کد تأیید می‌خواهد.
    user_id = update.message.chat_id
    if user_id in AUTHORIZED_USERS:
        keyboard = [
            [InlineKeyboardButton("Smart Tracker", callback_data="smart_tracker")],
            [InlineKeyboardButton("Master Tracker", callback_data="master_tracker")],
            [InlineKeyboardButton("Target Village", callback_data="target_village")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("✅ شما قبلاً تأیید شده‌اید! لطفاً یک گزینه را انتخاب کنید:", reply_markup=reply_markup)
    else:
        await update.message.reply_text("👋 سلام! لطفاً کد تأیید خود را وارد کنید:")

# هندلر دکمه‌های منو
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if query is None:
        return
    await query.answer()
    data = query.data
    context.user_data['tracker_type'] = data
    await query.message.reply_text("🔹 لطفاً Site ID را وارد کنید:")

# هندلر برای دریافت Site ID و جستجو در فایل‌های اکسل
async def site_id_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None:
        return
    site_id = update.message.text.strip()
    tracker_type = context.user_data.get('tracker_type')
    if not tracker_type:
        await update.message.reply_text("❌ لطفاً ابتدا از منو یک گزینه انتخاب کنید.")
        return
    # انتخاب DataFrame بر اساس نوع ترکر
    if tracker_type == "smart_tracker":
        df = rf_plan_df
    elif tracker_type == "master_tracker":
        df = master_df
    elif tracker_type == "target_village":
        df = target_village_df
    else:
        await update.message.reply_text("❌ نوع ترکر نامعتبر است.")
        return
    if df is None:
        await update.message.reply_text("⚠️ خطا در بارگذاری داده‌ها.")
        return
    # فیلتر کردن بر اساس Site ID (بدون حساسیت به حروف و فاصله‌ها)
    result = df[df["Site ID"].astype(str).str.strip().str.lower() == site_id.lower()]
    if result.empty:
        await update.message.reply_text("⚠️ اطلاعاتی برای این Site ID یافت نشد.")
    else:
        message_text = "\n\n".join(result.astype(str).apply(lambda row: "\n".join(f"{col}: {row[col]}" for col in result.columns), axis=1))
        await update.message.reply_text(message_text, parse_mode="Markdown")
    # بعد از ارسال نتایج، منوی اصلی را دوباره نشان می‌دهیم.
    await start(update, context)

# هندلر احراز هویت: اگر کاربر تأیید نشده باشد، متن وارد شده را به عنوان کد تأیید بررسی می‌کند.
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
        
# هندلر اصلی متنی
async def main_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.chat_id
    if user_id not in AUTHORIZED_USERS:
        await auth_handler(update, context)
    else:
        await site_id_handler(update, context)

def main() -> None:
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, main_text_handler))
    app.add_error_handler(lambda update, context: print(f"Error: {context.error}"))
    
    print("✅ Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
