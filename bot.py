from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
import pandas as pd
import asyncio

TOKEN = "7825218464:AAEmaLKgP8hD5wzK_DUA0h64rd3Y-HnVlhY"

# خواندن فایل اکسل
EXCEL_FILE = "RF PLAN.xlsx"

AUTHORIZED_USERS = {}
VERIFICATION_CODES = {"766060", "296752", "783213", "047129", "188709", "904796", "086363", "144584"}

def get_site_info(site_id):
    df = pd.read_excel(EXCEL_FILE, engine="openpyxl")
    row = df[df["Site ID"] == site_id]
    if row.empty:
        return "❌ Site not found."
    
    info = f"📡 **Site ID:** {site_id}\n"
    for col in df.columns:
        info += f"**{col}:** {row.iloc[0][col]}\n"
    return info

async def start(update: Update, context: CallbackContext):
    user_id = update.message.chat_id
    if user_id in AUTHORIZED_USERS:
        await update.message.reply_text("✅ You are already verified! Please enter a Site ID.")
    else:
        await update.message.reply_text("👋 Welcome! Please enter your verification code.")

async def verify(update: Update, context: CallbackContext):
    user_id = update.message.chat_id
    code = update.message.text.strip()

    if user_id in AUTHORIZED_USERS:
        await update.message.reply_text("✅ You are already verified! Please enter a Site ID.")
        return

    if code in VERIFICATION_CODES:
        AUTHORIZED_USERS[user_id] = True
        await update.message.reply_text("✅ Verification successful! Please enter a Site ID.")
    else:
        await update.message.reply_text("❌ Incorrect code. Please try again.")

async def handle_site_id(update: Update, context: CallbackContext):
    user_id = update.message.chat_id
    if user_id not in AUTHORIZED_USERS:
        await update.message.reply_text("❌ You need to verify first. Please enter your verification code.")
        return

    site_id = update.message.text.strip()
    response = get_site_info(site_id)
    await update.message.reply_text(response, parse_mode="Markdown")

async def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, verify))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_site_id))

    print("Bot is running...")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
