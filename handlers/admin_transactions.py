from pathlib import Path
from telegram import Update
from telegram.ext import (
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# Conversation stages
TX1, TX2, TX3, TX4 = "tx:1", "tx:2", "tx:3", "tx:4"

# Directory where transaction images are stored
TRANS_DIR = Path(__file__).resolve().parent.parent / "data" / "transactions"
TRANS_DIR.mkdir(parents=True, exist_ok=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start the admin transaction update conversation."""
    context.user_data["await_stage"] = TX1
    await update.message.reply_text("1-rasmni yuboring")
    return TX1

async def _save_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    stage = context.user_data.get("await_stage")
    if not update.message or not update.message.photo:
        await update.message.reply_text("❌ Rasm yuboring")
        return stage or ConversationHandler.END

    number = stage.split(":")[1] if stage else "1"
    file_path = TRANS_DIR / f"{number}.jpg"
    photo_file = await update.message.photo[-1].get_file()
    await photo_file.download_to_drive(str(file_path))

    if stage == TX1:
        next_stage = TX2
        await update.message.reply_text("2-rasmni yuboring")
    elif stage == TX2:
        next_stage = TX3
        await update.message.reply_text("3-rasmni yuboring")
    elif stage == TX3:
        next_stage = TX4
        await update.message.reply_text("4-rasmni yuboring")
    else:
        await update.message.reply_text("✅ Расмлар yangilandi")
        context.user_data.pop("await_stage", None)
        return ConversationHandler.END

    context.user_data["await_stage"] = next_stage
    return next_stage

async def _invalid(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    await update.message.reply_text("❌ Rasm yuboring")
    return context.user_data.get("await_stage", ConversationHandler.END)

def get_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[CommandHandler("admin_tx", start)],
        states={
            TX1: [
                MessageHandler(filters.PHOTO, _save_photo),
                MessageHandler(filters.ALL & ~filters.PHOTO, _invalid),
            ],
            TX2: [
                MessageHandler(filters.PHOTO, _save_photo),
                MessageHandler(filters.ALL & ~filters.PHOTO, _invalid),
            ],
            TX3: [
                MessageHandler(filters.PHOTO, _save_photo),
                MessageHandler(filters.ALL & ~filters.PHOTO, _invalid),
            ],
            TX4: [
                MessageHandler(filters.PHOTO, _save_photo),
                MessageHandler(filters.ALL & ~filters.PHOTO, _invalid),
            ],
        },
        fallbacks=[],
        allow_reentry=True,
    )
