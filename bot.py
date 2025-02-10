import os
import pandas as pd
import json
import requests
from io import BytesIO
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext

# --- تنظیمات اولیه ---
TOKEN = os.getenv("BOT_TOKEN")  # توکن از متغیر محیطی خوانده می‌شود
AUTHORIZED_USERS_FILE = 'authorized_users.json'  # فایل JSON برای ذخیره کاربران تأیید شده
EXCEL_FILES = {
    "smart_tracker": "https://github.com/HosseinHHSM/USO/raw/main/RF%20PLAN.xlsx",
    "master_tracker": "https://github.com/HosseinHHSM/USO/raw/main/Master.xlsx",
    "target_village": "https://github.com/HosseinHHSM/USO/raw/main/Target%20village.xlsx"
}  # لینک‌های raw برای هر فایل اکسل

# لیست کدهای تأیید
VERIFICATION_CODES = {
    "766060", "296752", "783213", "047129", "188709", "904796", "086363",
    "144584", "866372", "394644", "808387", "343647", "917012", "920483",
    "292397", "604952", "714342", "390238", "406511", "714780"
}

# --- توابع مربوط به ذخیره و بارگذاری کاربران تأیید شده ---
def load_authorized_users():
    try:
        with open(AUTHORIZED_USERS_FILE, 'r') as f:
            return set(json.load(f))
    except (FileNotFoundError, json.JSONDecodeError):
        return set()

def save_authorized_users():
    with open(AUTHORIZED_USERS_FILE, 'w') as f:
        json.dump(list(AUTHORIZED_USERS), f)

AUTHORIZED_USERS = load_authorized_users()

# --- تابع دانلود و خواندن فایل اکسل از URL ---
def read_excel_from_url(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            excel_data = BytesIO(response.content)
            df = pd.read_excel(excel_data, engine="openpyxl")
            # چاپ اولین 5 ردیف برای بررسی (برای دیباگ)
            print(f"File loaded from {url}. First 5 rows:")
            print(df.head())
            return df
        else:
            print(f"Failed to download file from {url}. Status Code: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error downloading file: {str(e)}")
        return None

# --- تابع خواندن اطلاعات از اکسل بر اساس Site ID ---
def get_site_info(site_id, tracker_type):
    if tracker_type not in EXCEL_FILES:
        return "❌ نوع ترکر نامعتبر است."

    df = read_excel_from_url(EXCEL_FILES[tracker_type])
    if df is None:
        return "⚠️ خطا در بارگذاری فایل اکسل."

    # پیدا کردن ستونی که شامل "site" و "id" (بدون حساسیت به حروف) است
    site_id_col = None
    for col in df.columns:
        if "site" in col.lower() and "id" in col.lower():
            site_id_col = col
            break
    if site_id_col is None:
        return "❌ ستون مربوط به Site ID در فایل اکسل یافت نشد."

    # نرمال‌سازی مقادیر ستون Site ID
    df[site_id_col] = df[site_id_col].astype(str).str.strip().str.lower()
    target_site = str(site_id).strip().lower()

    row = df[df[site_id_col] == target_site]
    if row.empty:
        return "❌ سایت مورد نظر یافت نشد."

    info = f"📡 **Site ID:** {site_id}\n"
    for col in df.columns:
        info += f"**{col}:** {row.iloc[0][col]}\n"
    return info

# --- منوی اصلی (Inline Keyboard) ---
async def show_main_menu(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton("1- بررسی دیتا از اسمارت ترکر", callback_data='1')],
        [InlineKeyboardButton("2- بررسی دیتا از مستر ترکر", callback_data='2')],
        [InlineKeyboardButton("3- بررسی دیتا از Target Village", callback_data='3')],
        [InlineKeyboardButton("بازگشت به منو اصلی", callback_data='back')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("لطفاً یک گزینه انتخاب کنید:", reply_markup=reply_markup)

# --- پیام خوش‌آمدگویی و شروع ---
async def start(update: Update, context: CallbackContext):
    user_id = update.message.chat_id
    if user_id in AUTHORIZED_USERS:
        await show_main_menu(update, context)
    else:
        await update.message.reply_text("👋 سلام دوست عزیز، خوش آمدید! لطفاً کد تأیید خود را وارد کنید.")

# --- هندلر دکمه‌های منو (CallbackQuery) ---
async def button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    data = query.data
    if data == 'back':
        # بازگشت به منو اصلی
        await query.edit_message_text("به منو اصلی برگشتید.")
        await show_main_menu(update, context)
    elif data in ['1', '2', '3']:
        # ذخیره نوع ترکر بر اساس انتخاب
        if data == '1':
            context.user_data['tracker_type'] = "smart_tracker"
        elif data == '2':
            context.user_data['tracker_type'] = "master_tracker"
        elif data == '3':
            context.user_data['tracker_type'] = "target_village"
        await query.edit_message_text("📡 لطفاً Site ID را وارد کنید:")
    else:
        await query.edit_message_text("❌ انتخاب نامعتبر است.")

# --- هندلر دریافت Site ID ---
async def handle_site_id(update: Update, context: CallbackContext):
    # این هندلر فقط زمانی اجرا می‌شود که کاربر Site ID را وارد کند.
    if update.message:
        site_id = update.message.text.strip()
        tracker_type = context.user_data.get('tracker_type')
        if tracker_type:
            response = get_site_info(site_id, tracker_type)
            await update.message.reply_text(response, parse_mode="Markdown")
            # بعد از نمایش دیتا، منو اصلی را نشان می‌دهیم
            await show_main_menu(update, context)
        else:
            await update.message.reply_text("❌ ابتدا یک گزینه از منو را انتخاب کنید.")

# --- هندلر تأیید هویت (برای متن وارد شده که کد تأیید است) ---
async def auth_handler(update: Update, context: CallbackContext):
    user_id = update.message.chat_id
    user_input = update.message.text.strip()
    if user_id not in AUTHORIZED_USERS:
        if user_input in VERIFICATION_CODES:
            AUTHORIZED_USERS.add(user_id)
            save_authorized_users()
            await update.message.reply_text("✅ تأیید موفقیت‌آمیز! اکنون می‌توانید از منو استفاده کنید.")
            await show_main_menu(update, context)
        else:
            await update.message.reply_text("❌ کد ورود نادرست است. لطفاً دوباره امتحان کنید.")

# --- هندلر اصلی متنی ---
async def main_text_handler(update: Update, context: CallbackContext):
    user_id = update.message.chat_id
    # اگر کاربر هنوز تأیید نشده، به تابع auth_handler هدایت می‌شود
    if user_id not in AUTHORIZED_USERS:
        await auth_handler(update, context)
    else:
        # اگر کاربر قبلاً انتخاب کرده و در انتظار Site ID است،
        # باید آن را به هندلر مربوط به دریافت Site ID ارسال کنیم.
        tracker_type = context.user_data.get('tracker_type')
        if tracker_type:
            await handle_site_id(update, context)
        else:
            # در غیر این صورت، ورودی کاربر ممکن است برای انتخاب منو باشد.
            await update.message.reply_text("❌ لطفاً از منوی ارائه شده یک گزینه را انتخاب کنید.")

# --- راه‌اندازی بات ---
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, main_text_handler))
    app.add_handler(MessageHandler(filters.StatusUpdate.INSERT, main_text_handler))  # برای دریافت Site ID (اختیاری)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_site_id))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, auth_handler))
    app.add_handler(CommandHandler("menu", show_main_menu))
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("restart", start))
    app.add_handler(CommandHandler("back", start))
    app.add_handler(CommandHandler("help", start))
    # اضافه کردن هندلر برای CallbackQuery (برای دکمه‌های منو)
    app.add_handler(MessageHandler(filters.COMMAND, start))
    app.add_handler(MessageHandler(filters.ALL, start))
    # استفاده از CallbackQueryHandler برای دکمه‌ها
    from telegram.ext import CallbackQueryHandler
    app.add_handler(CallbackQueryHandler(button_handler))

    print("🤖 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    if not TOKEN:
        raise ValueError("❌ خطا: توکن ربات در متغیرهای محیطی تنظیم نشده است!")
    main()
