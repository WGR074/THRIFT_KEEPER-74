from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_skip_keyboard():
    return ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="⏭ Пропустить")]], 
                               resize_keyboard=True)