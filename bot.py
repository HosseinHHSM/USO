import os
import pandas as pd
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters

# خواندن توکن از متغیر محیطی
TOKEN = os.getenv("BOT_TOKEN")

# لینک‌های اکسل‌ها
RF_PLAN_URL = "https://github.com/HosseinHHSM/USO/raw/main/RF%20PLAN.xlsx"
MASTER_URL = "https://github.com/HosseinHHSM/USO/raw/main/Master.xlsx"
TARGET_VILLAGE_URL = "https://github.com/HosseinHHSM/USO/raw/main/Target%20village.xlsx"

# دانلود و خواندن فایل‌های اکسل
def read_excel(url):
    try:
        df = pd.read_excel(url)
        return df
    except Exception as e:
        return None

rf_plan_df = read_excel(RF_PLAN_URL)
master_df = read_excel(MASTER_URL)
target_village_df = read_excel(TARGET_VILLAGE_URL)

# تابع نمایش منوی اصلی
def start(update: Update, context):
    keyboard = [
        [InlineKeyboardButton("Smart Tracker", callback_data='smart_tracker')],
        [InlineKeyboardButton("Master Tracker", callback_data='master_tracker')],
        [InlineKeyboardButton("Target Village", callback_data='target_village')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("لطفاً یک گزینه را انتخاب کنید:", reply_markup=reply_markup)

# تابع بررسی دیتا
def check_data(update: Update, context):
    query = update.callback_query
    query.answer()
    context.user_data['current_section'] = query.data
    query.message.reply_text("لطفاً Site ID را وارد کنید:")

# پردازش Site ID
def process_site_id(update: Update, context):
    site_id = update.message.text.strip()
    section = context.user_data.get('current_section')
    
    if section == 'smart_tracker':
        df = rf_plan_df
    elif section == 'master_tracker':
        df = master_df
    elif section == 'target_village':
        df = target_village_df
    else:
        update.message.reply_text("خطا: لطفاً از منو استفاده کنید.")
        return
    
    if df is not None:
        result = df[df['Site ID'].astype(str) == site_id]
        if not result.empty:
            message_text = "\n==================================================\n".join(
                [f"🌍 **موقعیت:** {row.get('استان', 'نامشخص')} - {row.get('شهرستان', 'نامشخص')}\n"
                 f"🏡 **آبادی:** {row.get('آبادی', 'نامشخص')}\n"
                 f"📍 **مختصات:** {row.get('عرض جغرافیایی', 'نامشخص')} , {row.get('طول جغرافیایی', 'نامشخص')}"
                 for _, row in result.iterrows()]
            )
        else:
            message_text = "⚠️ اطلاعاتی برای این Site ID یافت نشد."
    else:
        message_text = "⚠️ خطا در خواندن اطلاعات."
    
    update.message.reply_text(message_text)

# دکمه بازگشت
def back(update: Update, context):
    start(update, context)

# تنظیم ربات
def main():
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(check_data))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, process_site_id))
    
    app.run_polling()

if __name__ == "__main__":
    main()
