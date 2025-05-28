# keyboards/goal_kb.py
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def skip_deadline_kb():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Пропустить")]],
        resize_keyboard=True
    )

def goals_list_kb(goals):
    keyboard = []
    for goal in goals:
        keyboard.append([KeyboardButton(text=f"🎯 {goal['name']}")])
    keyboard.append([KeyboardButton(text="🔙 Назад")])
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)



def confirm_delete_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✅ Да, удалить")],
            [KeyboardButton(text="❌ Нет, отменить")]
        ],
        resize_keyboard=True
    )

def get_goal_keyboard():
    kb = [
        [KeyboardButton(text="➕ Создать цель"), KeyboardButton(text="✏️ Редактировать цель")],
        [KeyboardButton(text="💰 Внести сумму"), KeyboardButton(text="📉 Снять сумму")],
        [KeyboardButton(text="📈 Активные цели"), KeyboardButton(text="✅ Выполненные")],
        [KeyboardButton(text="🗑 Удалить цель"), KeyboardButton(text="🔙 Назад")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def edit_goal_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📝 Изменить название"),
             KeyboardButton(text="💵 Изменить сумму")],
            [KeyboardButton(text="📅 Изменить дедлайн"),
             KeyboardButton(text="🚫 Отменить редактирование")]
        ],
        resize_keyboard=True
    )