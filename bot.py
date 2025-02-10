import os
import pandas as pd
import json
import requests
from io import BytesIO
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, CallbackContext

# --- تنظیمات اولیه ---
TOKEN = os.getenv("BOT_TOKEN")  # توکن از متغیر محیطی خوانده می‌شود
AUTHORIZED_USERS_FILE = 'authorized_users.json'  # فایل JSON برای ذخیره کاربران تأیید شده

# لینک‌های raw فایل‌های اکسل
EXCEL_FILES = {
    "smart_tracker": "https://github.com/HosseinHHSM/USO/raw/main/RF%20PLAN.xlsx",
    "master_tracker": "https://github.com/HosseinHHSM/USO/raw/main/Master.xlsx",
    "target_village": "https://github.com/HosseinHHSM/USO/raw/main/Target%20village.xlsx"
}

# لیست کدهای تأیید
VERIFICATION_CODES = {
    "766060", "296752", "783213", "047129", "188709", "904796", "086363",
    "144584", "866372", "394644", "808387", "343647", "917012", "920483",
    "292397", "604952", "714342", "390238", "406511", "714780"
}

# --- توابع ذخیره و بارگذاری کاربران تأیید شده ---
def load_authorized_users():
    try:
        with open(AUTHORIZED_USERS_FILE, 'r') as f:
            return set(json.load(f))
    except (FileNotFoundError, json.JSONDecodeError):
        return set()

def save_authorized_users(auth_users):
    with open(AUTHORIZED_USERS_FILE, 'w') as f:
        json.dump(list(auth_users), f)

AUTHORIZED_USERS = load_authorized_users()

# --- تابع دانلود و خواندن فایل اکسل از URL ---
def read_excel_from_url(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            excel_data = BytesIO(response.content)
            df = pd.read_excel(excel_data, engine="openpyxl")
            # برای دیباگ: چاپ اولین ۵ ردیف
            print(f"File loaded from {url}")
            print(df.head())
            return df
        else:
            print(f"Failed to download file from {url}. Status Code: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error downloading file: {str(e)}")
        return None

# --- تابع دریافت اطلاعات از اکسل بر اساس Site ID ---
def get_site_info(site_id, tracker_type):
    if tracker_type not in EXCEL_FILES:
        return "❌ نوع ترکر نامعتبر است."
    df = read_excel_from_url(EXCEL_FILES[tracker_type])
    if df is None:
        return "⚠️ خطا در بارگذاری فایل اکسل."
    # فرض کنید نام ستون مربوط به Site ID دقیقا "Site ID" است.
    row = df[df["Site ID"].astype(str).str.strip().str.lower() == str(site_id).strip().lower()]
    if row.empty:
        return "❌ سایت مورد نظر یافت نشد."
    info = f"📡 **Site ID:** {site_id}\n"
    for col in df.columns:
        info += f"**{col}:** {row.iloc[0][col]}\n"
    return info

# --- ساخت منوی اصلی (Inline Keyboard) ---
def main_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("1- بررسی دیتا از اسمارت ترکر", callback_data='1')],
        [InlineKeyboardButton("2- بررسی دیتا از مستر ترکر", callback_data='2')],
        [InlineKeyboardButton("3- بررسی دیتا از Target Village", callback_data='3')]
    ]
    return InlineKeyboardMarkup(keyboard)

# --- پیام شروع ربات ---
async def start(update: Update, context: CallbackContext):
    user_id = update.message.chat_id
    if user_id in AUTHORIZED_USERS:
        await update.message.reply_text("✅ شما قبلاً تأیید شده‌اید! لطفاً یک گزینه انتخاب کنید:", reply_markup=main_menu_keyboard())
    else:
        await update.message.reply_text("👋 سلام! لطفاً کد تأیید خود را وارد کنید.")

# --- هندلر دکمه‌های منو ---
async def button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    data = query.data
    tracker_map = {'1': "smart_tracker", '2': "master_tracker", '3': "target_village"}
    if data in tracker_map:
        context.user_data['tracker_type'] = tracker_map[data]
        await query.edit_message_text("📡 لطفاً Site ID را وارد کنید:")
    elif data == 'back':
        await query.edit_message_text("بازگشت به منو اصلی.")
        await query.message.reply_text("لطفاً یک گزینه انتخاب کنید:", reply_markup=main_menu_keyboard())
    else:
        await query.edit_message_text("❌ انتخاب نامعتبر است.")

# --- هندلر ورودی‌های متنی (برای احراز هویت و دریافت Site ID) ---
async def main_text_handler(update: Update, context: CallbackContext):
    user_id = update.message.chat_id
    text = update.message.text.strip()
    
    # اگر کاربر تأیید نشده باشد، متن را به عنوان کد تأیید در نظر می‌گیریم
    if user_id not in AUTHORIZED_USERS:
        if text in VERIFICATION_CODES:
            AUTHORIZED_USERS.add(user_id)
            save_authorized_users(AUTHORIZED_USERS)
            await update.message.reply_text("✅ تأیید موفقیت‌آمیز! لطفاً یک گزینه انتخاب کنید:", reply_markup=main_menu_keyboard())
        else:
            await update.message.reply_text("❌ کد ورود نادرست است. لطفاً دوباره امتحان کنید.")
        return

    # اگر کاربر تأیید شده و در حالت وارد کردن Site ID است:
    tracker_type = context.user_data.get('tracker_type')
    if tracker_type:
        response = get_site_info(text, tracker_type)
        await update.message.reply_text(response, parse_mode="Markdown")
        # پس از دریافت پاسخ، حالت انتخاب ترکر را پاک می‌کنیم
        context.user_data['tracker_type'] = None
        await update.message.reply_text("لطفاً دوباره از منو استفاده کنید.", reply_markup=main_menu_keyboard())
    else:
        await update.message.reply_text("❌ لطفاً از منوی ارائه شده یک گزینه را انتخاب کنید.")

def main():
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, main_text_handler))
    
    print("🤖 Bot is running...")
    # اگر از polling استفاده می‌کنید:
    app.run_polling()

if __name__ == "__main__":
    if not TOKEN:
        raise ValueError("❌ خطا: توکن ربات تنظیم نشده است!")
    main()
