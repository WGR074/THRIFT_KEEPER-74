from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_period_keyboard() -> ReplyKeyboardMarkup:
    kb = [
        [KeyboardButton(text="🌞 Сегодня"), KeyboardButton(text="📅 Эта неделя")],
        [KeyboardButton(text="🌙 Этот месяц"), KeyboardButton(text="🎉 Этот год")],
        [KeyboardButton(text="🔙 Назад")]
    ]
    return ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        one_time_keyboard=True
    )