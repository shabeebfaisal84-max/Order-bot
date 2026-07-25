# -*- coding: utf-8 -*-
"""
بوت تلقرام لاستقبال طلبات العملاء وتسجيلها في ملف CSV (جدول).
"""

import csv
import os
import logging
from datetime import datetime

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (
    Application,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ------------------- الإعدادات -------------------
# ضع التوكن هنا مباشرة، أو عرّفه كمتغير بيئة باسم BOT_TOKEN
BOT_TOKEN = os.environ.get("BOT_TOKEN", "ضع_التوكن_هنا")

# آيدي حسابك في تلقرام (رقم)، حتى تقدر تستخدم أمر /orders لعرض آخر الطلبات
# لمعرفة آيديك، راسل بوت @userinfobot في تلقرام وهو يرسل لك رقمك
ADMIN_ID = int(os.environ.get("ADMIN_ID", "0"))

ORDERS_FILE = "orders.csv"

# ------------------- مراحل المحادثة -------------------
NAME, PHONE, PRODUCT, ADDRESS, NOTES, CONFIRM = range(6)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


# ------------------- أدوات مساعدة -------------------
def ensure_orders_file():
    """ينشئ ملف الطلبات مع رأس الجدول إذا لم يكن موجودًا."""
    if not os.path.exists(ORDERS_FILE):
        with open(ORDERS_FILE, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    "رقم الطلب",
                    "التاريخ والوقت",
                    "معرف العميل",
                    "اسم المستخدم في تلقرام",
                    "الاسم",
                    "رقم الجوال",
                    "تفاصيل الطلب",
                    "العنوان",
                    "ملاحظات",
                    "الحالة",
                ]
            )


def next_order_id() -> int:
    """يحسب رقم الطلب التالي بالاعتماد على عدد الأسطر في الملف."""
    ensure_orders_file()
    with open(ORDERS_FILE, "r", encoding="utf-8-sig") as f:
        count = sum(1 for _ in f) - 1  # نطرح سطر الرأس
    return max(count, 0) + 1


def save_order(order: dict):
    ensure_orders_file()
    with open(ORDERS_FILE, "a", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                order["id"],
                order["datetime"],
                order["user_id"],
                order["username"],
                order["name"],
                order["phone"],
                order["product"],
                order["address"],
                order["notes"],
                order["status"],
            ]
        )


# ------------------- خطوات المحادثة -------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "أهلاً وسهلاً بك! 👋\n"
        "أنا بوت استقبال الطلبات، وراح أساعدك تسجّل طلبك خطوة بخطوة.\n\n"
        "في أي وقت تقدر تكتب /cancel لإلغاء الطلب الحالي.\n\n"
        "خلّنا نبدأ 🙂\nما اسمك الكامل؟",
        reply_markup=ReplyKeyboardRemove(),
    )
    return NAME


async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["name"] = update.message.text.strip()
    await update.message.reply_text("تمام. ما رقم جوالك؟ (حتى نقدر نتواصل معك بخصوص الطلب)")
    return PHONE


async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["phone"] = update.message.text.strip()
    await update.message.reply_text("ممتاز. اكتب لي تفاصيل طلبك (المنتج/الخدمة والكمية).")
    return PRODUCT


async def get_product(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["product"] = update.message.text.strip()
    await update.message.reply_text(
        "وش عنوان التوصيل؟ (اذا الطلب ما يحتاج توصيل، اكتب: لا يوجد)"
    )
    return ADDRESS


async def get_address(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["address"] = update.message.text.strip()
    await update.message.reply_text("أي ملاحظات إضافية؟ (اذا ما فيه، اكتب: لا يوجد)")
    return NOTES


async def get_notes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["notes"] = update.message.text.strip()

    d = context.user_data
    summary = (
        "📋 ملخص طلبك:\n\n"
        f"👤 الاسم: {d['name']}\n"
        f"📞 الجوال: {d['phone']}\n"
        f"🛒 الطلب: {d['product']}\n"
        f"📍 العنوان: {d['address']}\n"
        f"📝 ملاحظات: {d['notes']}\n\n"
        "هل تأكد الطلب؟"
    )
    keyboard = [["✅ تأكيد الطلب"], ["✏️ إلغاء والبدء من جديد"]]
    await update.message.reply_text(
        summary, reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return CONFIRM


async def confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    if text != "✅ تأكيد الطلب":
        await update.message.reply_text(
            "تم إلغاء الطلب. اكتب /start إذا حبيت تبدأ طلب جديد.",
            reply_markup=ReplyKeyboardRemove(),
        )
        context.user_data.clear()
        return ConversationHandler.END

    d = context.user_data
    user = update.effective_user
    order = {
        "id": next_order_id(),
        "datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "user_id": user.id,
        "username": f"@{user.username}" if user.username else "-",
        "name": d["name"],
        "phone": d["phone"],
        "product": d["product"],
        "address": d["address"],
        "notes": d["notes"],
        "status": "جديد",
    }
    save_order(order)

    await update.message.reply_text(
        f"🎉 تم استلام طلبك برقم #{order['id']}\nراح نتواصل معك قريبًا. شكرًا لك!",
        reply_markup=ReplyKeyboardRemove(),
    )

    # إشعار صاحب المتجر (إذا تم ضبط ADMIN_ID)
    if ADMIN_ID:
        try:
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=(
                    f"🔔 طلب جديد #{order['id']}\n"
                    f"👤 {order['name']} | 📞 {order['phone']}\n"
                    f"🛒 {order['product']}\n"
                    f"📍 {order['address']}\n"
                    f"📝 {order['notes']}"
                ),
            )
        except Exception as e:
            logger.warning("تعذر إرسال إشعار للأدمن: %s", e)

    context.user_data.clear()
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "تم إلغاء الطلب. اكتب /start إذا حبيت تبدأ من جديد.",
        reply_markup=ReplyKeyboardRemove(),
    )
    context.user_data.clear()
    return ConversationHandler.END


# ------------------- أمر مراجعة الطلبات (لصاحب المتجر فقط) -------------------
async def orders_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("هذا الأمر خاص بصاحب المتجر فقط.")
        return

    ensure_orders_file()
    try:
        with open(ORDERS_FILE, "rb") as f:
            await update.message.reply_document(
                document=f, filename="orders.csv", caption="📊 جدول الطلبات كامل"
            )
    except Exception as e:
        await update.message.reply_text(f"صار خطأ أثناء إرسال الملف: {e}")


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "الأوامر المتاحة:\n"
        "/start - بدء طلب جديد\n"
        "/cancel - إلغاء الطلب الحالي\n"
        "/orders - عرض جدول كل الطلبات (لصاحب المتجر فقط)"
    )


def main():
    if BOT_TOKEN == "ضع_التوكن_هنا" or not BOT_TOKEN:
        raise SystemExit(
            "⚠️ لازم تحط التوكن أولاً. عدّل متغير BOT_TOKEN في أعلى الملف، "
            "أو عرّفه كمتغير بيئة باسم BOT_TOKEN."
        )

    ensure_orders_file()

    app = Application.builder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)],
            PRODUCT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_product)],
            ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_address)],
            NOTES: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_notes)],
            CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)
    app.add_handler(CommandHandler("orders", orders_cmd))
    app.add_handler(CommandHandler("help", help_cmd))

    print("✅ البوت شغّال الآن... اضغط Ctrl+C للإيقاف")
    app.run_polling()


if __name__ == "__main__":
    main()
      
