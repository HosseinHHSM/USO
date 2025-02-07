AUTHORIZED_USERS = {}  # ذخیره کاربران تأیید‌شده
USER_SITE_IDS = {}  # ذخیره Site ID کاربران

async def verify(update: Update, context: CallbackContext):
    user_id = update.message.chat_id
    message_text = update.message.text.strip()

    if user_id in AUTHORIZED_USERS:
        await update.message.reply_text("✅ شما قبلاً تأیید شده‌اید! لطفاً Site ID را وارد کنید.")
        return

    if message_text in map(str, VERIFICATION_CODES):
        AUTHORIZED_USERS[user_id] = True
        await update.message.reply_text("✅ تأیید موفقیت‌آمیز بود! لطفاً Site ID را وارد کنید.")
    else:
        await update.message.reply_text("❌ کد نادرست است. لطفاً دوباره امتحان کنید.")

async def handle_site_id(update: Update, context: CallbackContext):
    """ وقتی کاربر Site ID رو وارد می‌کنه، اطلاعات سایت رو ارسال کن. """
    user_id = update.message.chat_id
    message_text = update.message.text.strip()

    if user_id not in AUTHORIZED_USERS:
        await update.message.reply_text("❌ ابتدا باید تأیید شوید. لطفاً کد تأیید را ارسال کنید.")
        return

    # ذخیره Site ID برای کاربر
    USER_SITE_IDS[user_id] = message_text

    # اینجا باید اطلاعات سایت را پردازش و ارسال کنیم
    site_data = get_site_data(message_text)  # یک تابع که اطلاعات سایت رو بگیره
    if site_data:
        await update.message.reply_text(f"✅ اطلاعات سایت:\n{site_data}")
    else:
        await update.message.reply_text("❌ Site ID نامعتبر است. لطفاً دوباره امتحان کنید.")

def get_site_data(site_id):
    """ اینجا تابعی تعریف کن که اطلاعات سایت را از دیتابیس یا API بگیره. """
    data = {
        "12345": "🔹 سایت: Example.com\n🔹 وضعیت: فعال ✅",
        "67890": "🔹 سایت: TestSite.com\n🔹 وضعیت: غیرفعال ❌",
    }
    return data.get(site_id, None)

# ثبت `handle_site_id` در هندلر
dispatcher.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_site_id))
