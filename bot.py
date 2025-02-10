import os
import pandas as pd
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# تنظیمات لاگ‌گیری
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

TOKEN = os.getenv("BOT_TOKEN")

# خواندن داده‌های اکسل
def read_excel_files():
    global df_rf, df_master, df_target
    df_rf = pd.read_excel("RF PLAN.xlsx")
    df_master = pd.read_excel("Master.xlsx")
    df_target = pd.read_excel("Target village.xlsx")

read_excel_files()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📊 بررسی Smart Tracker", callback_data='smart_tracker')],
        [InlineKeyboardButton("📑 بررسی Master Tracker", callback_data='master_tracker')],
        [InlineKeyboardButton("🎯 بررسی Target Village", callback_data='target_village')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text("لطفاً یک گزینه را انتخاب کنید:", reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    context.user_data['mode'] = query.data
    await query.message.reply_text("🔹 لطفاً Site ID موردنظر را وارد کنید:")

async def site_id_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    site_id = update.message.text.strip()
    mode = context.user_data.get('mode')
    
    if mode == 'smart_tracker':
        df = df_rf
    elif mode == 'master_tracker':
        df = df_master
    elif mode == 'target_village':
        df = df_target
    else:
        await update.message.reply_text("❌ لطفاً ابتدا یک گزینه از منو انتخاب کنید.")
        return
    
    result = df[df['Site ID'] == site_id]
    if result.empty:
        await update.message.reply_text("⚠️ اطلاعاتی برای این Site ID یافت نشد.")
    else:
        message_text = "\n==================================================\n".join(result.astype(str).apply(lambda x: "\n".join(f"{col}: {val}" for col, val in x.items()), axis=1))
        await update.message.reply_text(f"🔹 اطلاعات سایت {site_id}:\n{message_text}")

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logging.error(f"Error: {context.error}")

if __name__ == "__main__":
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, site_id_handler))
    
    app.add_error_handler(error_handler)
    
    print("✅ ربات در حال اجراست...")
    app.run_polling()}]}
