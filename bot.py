import os
import logging
from dotenv import load_dotenv
from telegram.ext import Application, MessageHandler, filters, CallbackQueryHandler
from handlers.start_handler import get_handler
from handlers.personal_handler import personal_info, personal_inline_action, set_new_limits_action
from handlers.limit_handler import limits_text_handler
from handlers.requisites_handler import add_requisites, requisites_info, manage_requisites_action
from handlers.add_requisite_handler import requisites_text_handler
from handlers.support_handler import support_action
from handlers.status_handler import send_transaction, status_offline, history_transaction
from handlers.admin_transactions import start as admin_transactions_start, admin_transactions_text_handler
from utils.storage import get_user_role
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
if TOKEN:
    TOKEN = TOKEN.strip()

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)


async def error_handler(update, context):
    print("ERROR:", context.error)


async def admin_update_transaction(update, context):
    """Start admin transaction update conversation if user is admin."""
    user_id = update.effective_user.id
    if get_user_role(user_id) != "admin":
        await update.message.reply_text("Sizda ruxsat yo'q")
        return
    await admin_transactions_start(update, context)



def main():
    if not TOKEN:
        raise RuntimeError("BOT TOKEN yo'q ")
    app = Application.builder().token(TOKEN).build()
    # register global error handler
    app.add_error_handler(error_handler)
    app.add_handler(get_handler()) #start
    # reply keyboards
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex(r"^👤 Личный кабинет$"), personal_info))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex(r"^💳 Мои реквизиты$"), requisites_info))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex(r"^🛟 Поддержка$"), support_action))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex(r"^🟢 В онлайн: ON$"), send_transaction))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex(r"^🔴 Отключиться: OFF$"), status_offline))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex(r"^🧾История операций$"), history_transaction))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex(r"^♻️ Транзакцию обновить$"), admin_update_transaction))
    # inline keyboards
    app.add_handler(CallbackQueryHandler(personal_inline_action, pattern=r"^pi:"))
    app.add_handler(CallbackQueryHandler(set_new_limits_action, pattern=r"^set:"))
    app.add_handler(CallbackQueryHandler(add_requisites, pattern=r"^req:add$"))
    app.add_handler(CallbackQueryHandler(manage_requisites_action, pattern=r"^manage:(cbp|c2c|delete):[0-9a-fA-F-]{36}$"))
    app.add_handler(CallbackQueryHandler(support_action, pattern=r"^support"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, requisites_text_handler), group=1)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, limits_text_handler ), group=2)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, admin_transactions_text_handler ), group=3)

    # Fallback debug handler (runs last) to log unmatched messages and help diagnose keyboard issues
    async def _debug_unknown(update, context):
        try:
            text = update.message.text if update.message else None
        except Exception:
            text = None
        logger.info("Received message not handled by other handlers: %r", text)
        # don't reply automatically to avoid spamming — just log

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, _debug_unknown), group=99)

    app.run_polling()

if __name__ == "__main__":
    main()

