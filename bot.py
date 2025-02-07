import pandas as pd
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, filters, CallbackContext

# --- Configuration ---
TOKEN = "7825218464:AAEmaLKgP8hD5wzK_DUA0h64rd3Y-HnVlhY"  # Replace with your BotFather token
EXCEL_FILE = "RF PLAN.xlsx"  # Name of the Excel file
AUTHORIZED_USERS = {}  # Dictionary to store verified users
VERIFICATION_CODES = {"766060", "296752", "783213", "047129", "188709", "904796", "086363", "144584", "866372", "394644",
                      "808387", "343647", "917012", "920483", "292397", "604952", "714342", "390238", "406511", "714780"}  # Predefined verification codes

# --- Function to read data from Excel ---
def get_site_info(site_id):
    df = pd.read_excel(EXCEL_FILE, engine="openpyxl")  # Read Excel file
    row = df[df["Site ID"] == site_id]  # Search for Site ID

    if row.empty:
        return "❌ Site not found."

    # Extract all column data
    info = f"📡 **Site ID:** {site_id}\n"
    for col in df.columns:
        info += f"**{col}:** {row.iloc[0][col]}\n"

    return info

# --- Welcome message ---
def start(update: Update, context: CallbackContext):
    user_id = update.message.chat_id
    if user_id in AUTHORIZED_USERS:
        update.message.reply_text("✅ You are already verified! Please enter a Site ID.")
    else:
        update.message.reply_text("👋 Welcome! Please enter your verification code.")

# --- Verification process ---
def verify(update: Update, context: CallbackContext):
    user_id = update.message.chat_id
    code = update.message.text.strip()

    if user_id in AUTHORIZED_USERS:
        update.message.reply_text("✅ You are already verified! Please enter a Site ID.")
        return

    if code in VERIFICATION_CODES:
        AUTHORIZED_USERS[user_id] = True
        update.message.reply_text("✅ Verification successful! Please enter a Site ID.")
    else:
        update.message.reply_text("❌ Incorrect code. Please try again.")

# --- Handle Site ID request ---
def handle_site_id(update: Update, context: CallbackContext):
    user_id = update.message.chat_id
    if user_id not in AUTHORIZED_USERS:
        update.message.reply_text("❌ You need to verify first. Please enter your verification code.")
        return

    site_id = update.message.text.strip()
    response = get_site_info(site_id)
    update.message.reply_text(response, parse_mode="Markdown")

# --- Main function to run the bot ---
def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(filters.text & ~filters.command, verify))  # First, check the verification code
    dp.add_handler(MessageHandler(filters.text & ~filters.command, handle_site_id))  # Then process Site ID

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
