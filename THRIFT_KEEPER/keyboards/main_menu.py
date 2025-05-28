from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_main_menu_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Добавить расход"), KeyboardButton(text="💰 Добавить доход")],
            [KeyboardButton(text="📊 Статистика"), KeyboardButton(text="🎯 Цели")],
            [KeyboardButton(text="📘 О нас"), KeyboardButton(text="🆘 Помощь")]
        ],
        resize_keyboard=True,
        input_field_placeholder='Выберите пункт меню...'
    )