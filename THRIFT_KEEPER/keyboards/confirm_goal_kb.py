# keyboards/confirm_goal_kb.py
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_expired_goal_keyboard():
    kb = [
        [KeyboardButton(text="🔄 Продлить срок"), [KeyboardButton(text="🔁 Оставить как есть")],
        KeyboardButton(text="❌ Отметить как проваленную")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)