# 2) Foydalanuvchi matn yuborganda ishlaydigan handler:
import re
from telegram.error import BadRequest
from handlers.personal_handler import personal_info
from utils.storage import set_user_limits
from telegram import Update 
from telegram.ext import ContextTypes
from utils.formatting import format_amount_short

MIN_ALLOWED = 25_000
MAX_ALLOWED = 1_000_000

def parse_amount(s: str) -> int | None:
    t = re.sub(r"[ \t,_.]", "", (s or "")).lower().replace("к", "k")
    if t.endswith("kk"):
        num = t[:-2] or "0"
        return int(num) * 1_000_000 if num.isdigit() else None
    if t.endswith("k"):
        num = t[:-1] or "0"
        return int(num) * 1_000 if num.isdigit() else None
    return int(t) if t.isdigit() else None

async def limits_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stage = context.user_data.get("await")
    if stage not in ("limits:min", "limits:max"):
        return  # boshqa xabarlarga aralashmaymiz

    amount = parse_amount(update.message.text)
    if amount is None:
        await update.message.reply_text("❌ Введите число (напр. 25K или 25000).")
        return

    if stage == "limits:min":
        if amount < MIN_ALLOWED:
            await update.message.reply_text(f"❌ Минимум {MIN_ALLOWED:,}. Попробуйте ещё раз.")
            return
        context.user_data["limits_min"] = amount
        context.user_data["await"] = "limits:max"
        await update.message.reply_text("➡️ Теперь введите конечную сумму (max: 1KK)")
        return

    # stage == "limits:max"
    min_sum = context.user_data.get("limits_min")
    if min_sum is None:
        context.user_data["await"] = "limits:min"
        await update.message.reply_text("⚠️ Сначала введите начальную сумму (min).")
        return

    if amount < min_sum:
        await update.message.reply_text(f"❌ Максимум должен быть ≥ {min_sum:,}. Попробуйте ещё раз.")
        return
    if amount > MAX_ALLOWED:
        await update.message.reply_text(f"❌ Максимум {MAX_ALLOWED:,}. Попробуйте ещё раз.")
        return

    # Saqlaymiz
    user_id = update.effective_user.id
    set_user_limits(user_id, {"min": min_sum, "max": amount})

    # State tozalash
    context.user_data.pop("await", None)
    context.user_data.pop("limits_min", None)
    min_limit = format_amount_short(min_sum)
    max_limit = format_amount_short(amount)
    await update.message.reply_text(f"✅ Лимиты сохранены: {min_limit:} – {max_limit:}")
    return await personal_info(update, context)
