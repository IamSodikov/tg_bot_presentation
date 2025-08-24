from telegram import Update
from telegram.ext import ContextTypes
from handlers.menu_handler import personal_inline_kb, set_limit_inline_kb
from utils.storage import get_user_token, get_user_limits, get_user_status
from utils.exchange import get_rate
from telegram.error import BadRequest
from utils.formatting import format_amount_short
from utils.task_store import TaskStore  # Yangi import



async def render_user_info(token:str|None, limits: dict|None, status: str|None) -> str:
    token_str = token or "-"
    rate = await get_rate()
    
    # Agar limits bo'sh yoki None bo'lsa default qiymatlar
    if not limits or not limits.get("min") or not limits.get("max"):
        min_limit = "25K"
        max_limit = "140K"
    else:
        min_limit = format_amount_short(limits.get("min"))
        max_limit = format_amount_short(limits.get("max"))
    
    # Status belgisi
    if status == "online":
        status_str = "🟢 Онлайн"
    else:
        status_str = "🔴 Оффлайн"
        
    return (
        f"👤 Личный кабинет\n\n"
        f"🆔 Токен:\n└ {token_str}\n\n"
        f"🪪 Рабочий уровень:\n└ 🤓Starter\n\n"
        f"📶 Рабочий статус:\n└ {status_str}\n\n"
        f"🛡️ Страховой депозит:\n└ Без депозита\n\n"
        f"🎚️ Лимиты:\n└ от {min_limit} до {max_limit} \n\n"
        f"🔥Курс HTX:\n└🇷🇺USDTxRUB: {rate}"
    ) 

async def personal_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    chat_id = update.effective_chat.id
    # Avvalgi taskni to'xtatish
    TaskStore.cancel_task(chat_id)
    
    user_id = update.effective_user.id
    token = get_user_token(user_id)
    limits = get_user_limits(user_id)
    status = get_user_status(user_id)
    text = await render_user_info(token, limits, status)
    kb = personal_inline_kb()
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        try:
            return await query.edit_message_text(text, reply_markup=kb)
        except BadRequest:
            return await query.message.reply_text(text, reply_markup=kb)
    elif update.message:
        await update.message.reply_text(text, reply_markup=kb)

async def personal_inline_action(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    user_id = update.effective_user.id
    limits = get_user_limits(user_id) or {}
    min_sum = format_amount_short(limits.get("min"))
    max_sum = format_amount_short(limits.get("max"))
    
    query = update.callback_query
    data = query.data
    await query.answer()

    if data == "pi:set_limits":
        if limits:
            await query.edit_message_text(f"Ваши лимиты 📊  от 💵{min_sum} до 💵{max_sum} изменить?", reply_markup=set_limit_inline_kb())
        else:
            await query.edit_message_text(f"У вас нет лимитов. Установить лимит? ⚙️📈❓", reply_markup=set_limit_inline_kb())
            await set_new_limits_action(update, context)
    elif data == "pi:withdraw_deposit":
        await query.edit_message_text("На вашем аккаунте нет депозита 🤷‍♂️")

async def set_new_limits_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    await query.answer()

    if data == "set:yes":
        await query.edit_message_text("➡️ Введите начальную сумму (min: 25K)")
        context.user_data["await"] = "limits:min"    
        return
    elif data == "set:no":
        return await personal_info(update, context)


