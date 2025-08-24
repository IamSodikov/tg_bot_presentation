import os
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, ConversationHandler, MessageHandler, filters
from handlers.menu_handler import build_menu
from utils.storage import set_user_token
from handlers.personal_handler import personal_info  # Qo'shildi

WAITING_TOKEN = 1

def load_tokens() -> set[str]:
    raw = os.getenv("TOKENS")
    return {t.strip() for t in raw.split(",") if t.strip()}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tokens = load_tokens()
    if not tokens:
        await update.message.reply_text(
            "Configuration error: maybe you don't have any tokens"
        )
    await update.message.reply_text("Введите номер токена для входа:")
    return WAITING_TOKEN

async def check_token(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = (update.message.text or "").strip()
    tokens = load_tokens()
    
    if user_input in tokens:
        set_user_token(update.effective_user.id, user_input)
        await update.message.reply_text("Успешная авторизация✅", reply_markup=build_menu())
        # Lichniy kabinet ma'lumotlarini ham yuborish
        await personal_info(update, context)
        return ConversationHandler.END
    else:
        await update.message.reply_text("❌ Неверный токен. Попробуйте ещё раз!")
        return WAITING_TOKEN

def get_handler():
    return ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            WAITING_TOKEN: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, check_token),
            ],
        },
        fallbacks=[]
    )