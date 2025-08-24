from telegram import Update, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from utils.storage import get_user_requisites, delete_requisites_by_id, update_modes_by_id
from handlers.menu_handler import manage_requisites_inline_kb, set_new_requisites_inline_kb
from utils.task_store import TaskStore
from telegram.error import BadRequest
from typing import List, TypedDict

async def requisites_info(update, context):
    context.user_data.clear()
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    TaskStore.cancel_task(chat_id)
    reqs = get_user_requisites(user_id)

    if update.callback_query:
        q = update.callback_query
        await q.answer()
        try:
            await q.edit_message_text("📄 Ваши реквизиты:\n")
        except BadRequest:
            pass
        send = q.message.reply_text
    else:
        send = update.message.reply_text

    if not reqs:
        return await send("ℹ️ У вас нет реквизитов", reply_markup=set_new_requisites_inline_kb())
    
    for idx, r in enumerate(reqs):
        text = (
            f"💳 Карта: {r.get('card','—')}\n"
            f"🏦 Номер СБП: {r.get('phone','—')}\n"
            f"👤 ФИО получателя: {r.get('fio','—')}\n"
            f"🏦 Банк получателя: {r.get('bank','—')}"
        )
        base_kb = manage_requisites_inline_kb(r["id"], modes=r.get("modes"))

        if idx == len(reqs) - 1:
            add_kb = set_new_requisites_inline_kb()
            rows = list(base_kb.inline_keyboard) + list(add_kb.inline_keyboard)
            kb = InlineKeyboardMarkup(rows)
        else:
            kb = base_kb

        await send(text, reply_markup=kb)


async def add_requisites(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    req = get_user_requisites(user_id)
    query = update.callback_query
    data = query.data
    await query.answer()

    if data == "req:add":
        context.user_data["req_stage"] = "card"
        await query.edit_message_text(
            "💳 Введите номер карты (16 цифр)"
        )
    return

async def manage_requisites_action(update, context):
    q = update.callback_query
    await q.answer()
    user_id = q.from_user.id

    try:
        _, action, rid = q.data.split(":", 2)
    except Exception:
        return

    if action == "delete":
        ok = delete_requisites_by_id(user_id, rid)
        if ok:
            try:
                await q.message.delete()
            except BadRequest:
                try:
                    await q.edit_message_reply_markup(reply_markup=None)
                except BadRequest:
                    pass
        return

    if action in ("cbp", "c2c"):
        reqs = get_user_requisites(user_id)
        req = next((r for r in reqs if str(r.get("id")) == str(rid)), None)
        if not req:
            return

        cur_modes = list(req.get("modes") or [])
        if action in cur_modes:
            new_modes = [m for m in cur_modes if m != action]
        else:
            new_modes = cur_modes + [action]

        ok = update_modes_by_id(user_id, rid, new_modes)
        if not ok:
            return

        base_kb = manage_requisites_inline_kb(rid, modes=new_modes)
        if reqs and str(reqs[-1].get("id")) == str(rid):
            add_kb = set_new_requisites_inline_kb()
            rows = list(base_kb.inline_keyboard) + list(add_kb.inline_keyboard)
            kb = InlineKeyboardMarkup(rows)
        else:
            kb = base_kb

        try:
            await q.edit_message_reply_markup(reply_markup=kb)
        except BadRequest as e:
            if "Message is not modified" not in str(e):
                try:
                    await q.edit_message_text(q.message.text, reply_markup=kb)
                except BadRequest:
                    pass
        return

    return

