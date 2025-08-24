from telegram import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from typing import List

def build_menu() -> ReplyKeyboardMarkup:
    keyboard =[
        [KeyboardButton("👤 Личный кабинет"), KeyboardButton("🟢 В онлайн: ON")],
        [KeyboardButton("💳 Мои реквизиты"), KeyboardButton("🔴 Отключиться: OFF")],
        [KeyboardButton("🛟 Поддержка"), KeyboardButton("🧾История операций")]
    ]

    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    return reply_markup

def personal_inline_kb() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("⚙️ Настроить лимиты", callback_data="pi:set_limits")],
        [InlineKeyboardButton("💰Вывести депозит", callback_data="pi:withdraw_deposit")]
    ]
    return InlineKeyboardMarkup(keyboard)

def set_limit_inline_kb() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("Да", callback_data="set:yes"), InlineKeyboardButton("Нет", callback_data="set:no")]
    ]
    return InlineKeyboardMarkup(keyboard)

def set_new_requisites_inline_kb() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("➕ добавить реквизиты", callback_data="req:add")],
        [InlineKeyboardButton("➕ добавить через support", url="https://t.me/sigmapay_support")]
    ]
    return InlineKeyboardMarkup(keyboard)

def manage_requisites_inline_kb(rid: str, modes: List[str] | None = None) -> InlineKeyboardMarkup:
    modes = modes or []
    cbp_label = "✅ СБП" if "cbp" in modes else "СБП"
    c2c_label = "✅ C2C" if "c2c" in modes else "C2C"

    keyboard = [
        [
            InlineKeyboardButton(cbp_label, callback_data=f"manage:cbp:{rid}"),
            InlineKeyboardButton(c2c_label, callback_data=f"manage:c2c:{rid}"),
            InlineKeyboardButton("Удалить🗑️", callback_data=f"manage:delete:{rid}"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)
def support_inline_kb() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("@sigmapay_support", url="https://t.me/sigmapay_support")]
    ]
    return InlineKeyboardMarkup(keyboard)