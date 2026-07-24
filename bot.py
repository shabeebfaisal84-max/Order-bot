from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
import os

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 1672975374

keyboard = [
    ["📚 المراحل الدراسية"],
    ["🔍 البحث عن ملازمة"],
    ["🛒 طلباتي"],
    ["☎️ التواصل مع المكتبة", "📍 موقع المكتبة"],
]

reply_markup = ReplyKeyboardMarkup(
    keyboard,
    resize_keyboard=True
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = f"""
📚 أهلاً بك في بوت مكتبة ملازم دراسية

اختر الخدمة التي تريدها من الأزرار بالأسفل.
"""

    await update.message.reply_text(
        text,
        reply_markup=reply_markup
    )

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "📚 المراحل الدراسية":
        await update.message.reply_text(
            "اختر المرحلة:\n\n"
            "1️⃣ السادس الإعدادي\n"
            "2️⃣ الخامس الإعدادي\n"
            "3️⃣ الرابع الإعدادي\n"
            "4️⃣ الثالث المتوسط\n"
            "5️⃣ الثاني المتوسط\n"
            "6️⃣ الأول المتوسط"
        )

    elif text == "🔍 البحث عن ملازمة":
        await update.message.reply_text(
            "✍️ أرسل اسم المادة أو الأستاذ."
        )

    elif text == "🛒 طلباتي":
        await update.message.reply_text(
            "لا توجد طلبات حالياً."
        )

    elif text == "☎️ التواصل مع المكتبة":
        await update.message.reply_text(
            "راسل الأدمن مباشرة."
        )

    elif text == "📍 موقع المكتبة":
        await update.message.reply_text(
            "سيتم إضافة موقع المكتبة قريباً."
        )

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, buttons)
    )

    print("Bot Started...")

    app.run_polling()

if __name__ == "__main__":
    main()
