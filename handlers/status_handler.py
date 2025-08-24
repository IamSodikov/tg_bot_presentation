import json
import asyncio
from telegram import Update, InputMediaPhoto
from datetime import datetime, timedelta, timezone
from telegram.ext import ContextTypes
from utils.storage import set_user_status, get_user_status
from utils.task_store import TaskStore  # Yangi import

JSON_PATH = "data/transaction.json"

def load_transactions():
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

async def send_transaction(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()  # Qo'shildi: har doim state tozalanadi
    if update.message and update.message.text == "🟢 В онлайн: ON":
        chat_id = update.effective_chat.id
        set_user_status(chat_id, "online")
        await update.message.reply_text("🟢 Вы вышли в онлайн")
        # Task yaratish va saqlash
        task = asyncio.create_task(rotate_transactions(context, chat_id))
        TaskStore.set_task(chat_id, task)
        

async def rotate_transactions(context: ContextTypes.DEFAULT_TYPE, chat_id: int,
                              initial_wait: int = 5, countdown_seconds: int = 30*60,
                              update_interval: float = 1.0, delay: int = 5):

    txs = load_transactions()
    if not txs:
        await context.bot.send_message(chat_id, "transaction.json bo'sh.")
        return

    sent = None

    # initial wait before first transaction
    try:
        await asyncio.sleep(initial_wait)
    except asyncio.CancelledError:
        return

    # resume progress if present (prevents resending same items during a session)
    i = TaskStore.get_progress(chat_id) or 0
    total = len(txs)
    loop = asyncio.get_event_loop()
    while i < total:
        # stop if user cancelled
        if not TaskStore.has_task(chat_id):
            return

        # --- first in pair: countdown item ---
        tx1 = txs[i]
        path1 = tx1.get("image_path")
        base_caption1 = tx1.get("caption", "")

        mm = countdown_seconds // 60
        ss = countdown_seconds % 60
        caption1 = f"{base_caption1}\n\nВремя на подтверждение: {mm:02d}:{ss:02d}"

        sent1 = None
        try:
            # check file exists
            with open(path1, "rb") as f:
                sent1 = await context.bot.send_photo(chat_id=chat_id, photo=f, caption=caption1)
        except Exception as e:
            await context.bot.send_message(chat_id, f"Rasmni yuborishda xatolik: {e}")
            # move to next pair
            i += 2
            continue

        # start countdown as background subtask
        async def _countdown_loop(message_id: int, base_caption: str, total_seconds: int, interval: float):
            start = loop.time()
            try:
                while True:
                    elapsed = int(loop.time() - start)
                    remaining = total_seconds - elapsed
                    if remaining < 0:
                        try:
                            await context.bot.edit_message_caption(chat_id=chat_id, message_id=message_id,
                                                                   caption=f"{base_caption}\n\nВремя на подтверждение: 00:00")
                        except Exception:
                            pass
                        break

                    mm, ss = divmod(remaining, 60)
                    caption = f"{base_caption}\n\nВремя на подтверждение: {mm:02d}:{ss:02d}"
                    try:
                        await context.bot.edit_message_caption(chat_id=chat_id, message_id=message_id, caption=caption)
                    except Exception:
                        pass

                    await asyncio.sleep(interval)
            except asyncio.CancelledError:
                return

        try:
            countdown_task = asyncio.create_task(_countdown_loop(sent1.message_id, base_caption1, countdown_seconds, update_interval))
            TaskStore.add_subtask(chat_id, countdown_task)
        except Exception:
            pass

        # wait delay, then send second in pair (if exists)
        try:
            await asyncio.sleep(delay)
        except asyncio.CancelledError:
            return

        if i + 1 < total:
            tx2 = txs[i + 1]
            path2 = tx2.get("image_path")
            caption2 = tx2.get("caption", "")
            # cancel countdown subtask and replace the first message with second media
            try:
                TaskStore.pop_and_cancel_last_subtask(chat_id)
            except Exception:
                pass

            try:
                with open(path2, "rb") as f2:
                    media = InputMediaPhoto(media=f2, caption=caption2)
                    await context.bot.edit_message_media(chat_id=chat_id, message_id=sent1.message_id, media=media)
            except Exception as e:
                await context.bot.send_message(chat_id, f"Rasmni yangilashda xatolik: {e}")

            # send success message and do not delete it
            try:
                await context.bot.send_message(chat_id, "✅ Успешная авторизация, продолжаем онлайн 🌐")
            except Exception:
                pass

            # after sending second and success, wait delay before next pair
            try:
                await asyncio.sleep(delay)
            except asyncio.CancelledError:
                return
        else:
            # no pair, mark progress as complete and end
            i = total
            TaskStore.set_progress(chat_id, i)
            break

        # advance to next pair and persist progress
        i += 2
        TaskStore.set_progress(chat_id, i)

    # finished - clear stored task/progress so it won't restart
    TaskStore.finish_task(chat_id)
    return


async def status_offline(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()  # Qo'shildi: har doim state tozalanadi
    if update.message and update.message.text == "🔴 Отключиться: OFF":
        chat_id = update.effective_chat.id
        # Avvalgi taskni to'xtatish
        TaskStore.cancel_task(chat_id)
        set_user_status(chat_id, "offline")
        await update.message.reply_text("❌ Вы отключились")

async def history_transaction(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()  # Qo'shildi: har doim state tozalanadi
    if update.message and update.message.text == "🧾История операций":
        await update.message.reply_text("🚫 Операций пока нет")