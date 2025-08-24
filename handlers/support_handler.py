from telegram import Update
from telegram.ext import ContextTypes
from handlers.menu_handler import support_inline_kb
from utils.task_store import TaskStore

async def support_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    chat_id = update.effective_chat.id
    TaskStore.cancel_task(chat_id)
    
    kb = support_inline_kb()
    # Inline button bosilganda
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        return
    # Support tugmasi bosilganda
    elif update.message and update.message.text == "🛟 Поддержка":
        await update.message.reply_text("📞 Для поддержки обратитесь к:", reply_markup=kb)