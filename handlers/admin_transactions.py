import json
from telegram import Update
from telegram.ext import ContextTypes

JSON_PATH = "data/transaction.json"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Begin conversation for updating transactions JSON."""
    context.user_data["await"] = "admin_tx:json"
    await update.message.reply_text("Yangi transactionlar uchun JSON yuboring:")


async def admin_transactions_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stage = context.user_data.get("await")
    if stage != "admin_tx:json":
        return
    text = (update.message.text or "").strip()
    try:
        data = json.loads(text) if text else []
    except Exception:
        await update.message.reply_text("❌ JSON xato. Qayta urinib ko'ring.")
        return
    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    context.user_data.pop("await", None)
    await update.message.reply_text("✅ Транзакции обновлены")
