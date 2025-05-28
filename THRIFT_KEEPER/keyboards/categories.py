from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_categories_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🍔 Еда"), KeyboardButton(text="🚕 Транспорт"), KeyboardButton(text="🏠 Жильё")],
            [KeyboardButton(text="🎮 Развлечения"), KeyboardButton(text="🛒 Покупки")],
            [KeyboardButton(text="✏️ Другая категория"), KeyboardButton(text="🔙 Назад")]
        ],
        resize_keyboard=True
    )


def get_income_categories_keyboard():
    buttons = [
        [KeyboardButton(text="💰 Зарплата"), KeyboardButton(text="🧾 Бонус")],
        [KeyboardButton(text="🎁 Подарок"), KeyboardButton(text="📈 Инвестиции")],
        [KeyboardButton(text="💼 Самозанятость"), KeyboardButton(text="✏️ Другая категория")],
        [KeyboardButton(text="🔙 Назад")]  # ← новая кнопка
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)