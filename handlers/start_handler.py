import os
from telegram import Update
from telegram.ext import (
    ContextTypes,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)
from handlers.menu_handler import build_menu, build_admin_menu
from utils.storage import set_user_token
from telegram.ext import ContextTypes, CommandHandler, ConversationHandler, MessageHandler, filters
from handlers.menu_handler import build_menu
from utils.storage import set_user_token, set_user_role
from handlers.personal_handler import personal_info  # Qo'shildi

WAITING_TOKEN = 1


def load_tokens() -> dict[str, str]:
    raw = os.getenv("TOKENS") or ""
    tokens: dict[str, str] = {}
    for item in raw.split(","):
        item = item.strip()
        if not item:
            continue
        token, _, role = item.partition(":")
        tokens[token] = role or "user"
    return tokens
  
def load_tokens() -> tuple[set[str], set[str]]:
    raw_tokens = os.getenv("TOKENS", "")
    raw_admin_tokens = os.getenv("ADMIN_TOKENS", "")
    tokens = {t.strip() for t in raw_tokens.split(",") if t.strip()}
    admin_tokens = {t.strip() for t in raw_admin_tokens.split(",") if t.strip()}
    return tokens, admin_tokens

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tokens, admin_tokens = load_tokens()
    all_tokens = tokens | admin_tokens
    if not all_tokens:
        await update.message.reply_text(
            "Configuration error: maybe you don't have any tokens"
        )
    await update.message.reply_text("Введите номер токена для входа:")
    return WAITING_TOKEN

async def check_token(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = (update.message.text or "").strip()

    tokens = load_tokens()

    role = tokens.get(user_input)
    if role:
        set_user_token(update.effective_user.id, user_input)
        menu = build_admin_menu() if role == "admin" else build_menu()
        await update.message.reply_text("Успешная авторизация✅", reply_markup=menu)

    tokens, admin_tokens = load_tokens()
    all_tokens = tokens | admin_tokens

    if user_input in all_tokens:
        set_user_token(update.effective_user.id, user_input)
        role = "admin" if user_input in admin_tokens else "user"
        set_user_role(update.effective_user.id, role)
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
