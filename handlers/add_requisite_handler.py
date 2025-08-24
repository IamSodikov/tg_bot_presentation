import re
from telegram import Update
from telegram.ext import ContextTypes
from utils.storage import set_user_requisites

def _digits_only(s: str) -> str:
    return "".join(ch for ch in (s or "") if ch.isdigit())

def _normalize_phone(phone: str) -> str:
    raw = "".join(ch for ch in (phone or "") if ch.isdigit() or ch == "+")
    if raw.startswith("00"):
        raw = "+" + raw[2:]
    if raw and raw[0] != "+" and len(raw) in (12, 13):
        raw = "+" + raw
    return raw

def _mask_card(card: str | None) -> str:
    d = _digits_only(card or "")
    if len(d) >= 4:
        return "**** **** **** " + d[-4:]
    return "****"

async def requisites_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stage = context.user_data.get("req_stage")
    if stage not in {"card", "phone", "fio", "bank"}:  # bank qo'shildi
        return

    text = (update.message.text or "").strip()

    if stage == "card":
        digits = _digits_only(text)
        if len(digits) != 16:
            await update.message.reply_text("❌ Номер карты должен содержать 16 цифр. Попробуйте ещё раз.")
            return
        context.user_data["req_card"] = digits
        context.user_data["req_stage"] = "phone"
        await update.message.reply_text("📱 Введите номер телефона (например: +998901234567).")
        return
    
    if stage == "phone":
        norm = _normalize_phone(text)
        if not (norm.startswith("+") and len(re.sub(r"[^\d]", "", norm)) >= 10):
            await update.message.reply_text("❌ Введите корректный номер телефона. Например: +998901234567.")
            return
        context.user_data["req_phone"] = norm
        context.user_data["req_stage"] = "fio"
        await update.message.reply_text("👤 Введите ФИО полностью (например: Иванов Иван Иванович).")
        return
    
    if stage == "fio":
        if len(text) < 3:
            await update.message.reply_text("❌ Слишком короткое ФИО. Введите ещё раз.")
            return
        fio = re.sub(r"\s+", " ", text).strip()
        context.user_data["req_fio"] = fio
        context.user_data["req_stage"] = "bank"
        await update.message.reply_text("🏦 Введите название банка получателя:")
        return

    if stage == "bank":
        if len(text) < 2:
            await update.message.reply_text("❌ Слишком короткое название банка. Введите ещё раз.")
            return
        bank = text.strip()
        
        user_id = update.effective_user.id
        card = context.user_data.get("req_card")
        phone = context.user_data.get("req_phone")
        fio = context.user_data.get("req_fio")
        
        # Bank bilan birga saqlash
        set_user_requisites(user_id, {
            "card": card,
            "phone": phone,
            "fio": fio,
            "bank": bank,
            "modes": []
        })

        # Barcha ma'lumotlarni tozalash
        for key in ("req_stage", "req_card", "req_phone", "req_fio", "req_bank"):
            context.user_data.pop(key, None)
        
        await update.message.reply_text("✅ Реквизиты сохранены")
        
        # Rekvizitlarni ko'rsatish (dynamic import to avoid circular import)
        from handlers.requisites_handler import requisites_info
        return await requisites_info(update, context)