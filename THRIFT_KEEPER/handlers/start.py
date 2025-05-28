from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from database.db import Database

from handlers.registration import start_registration
from keyboards.main_menu import get_main_menu_keyboard

router = Router()
db = Database()

@router.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    """Приветствие и проверка регистрации"""
    welcome_text = """
👋 Привет! Я ваш личный Finance Keeper — бот для учёта финансов.

📊 С моей помощью вы сможете:
• 📝 Учитывать доходы и расходы
• 📊 Анализировать траты по категориям
• 💰 Контролировать бюджет и достигать целей

Давайте начнём работу!
"""
    await message.answer(welcome_text)

    user_id = message.from_user.id
    user = db.get_user(user_id)

    if not user:
        await message.answer("Для начала нужно пройти регистрацию")
        await start_registration(message, state)
    else:
        await message.answer(
            f"С возвращением, {user['first_name']}! 😊",
            reply_markup=get_main_menu_keyboard()
        )

@router.message(Command("help"))
async def cmd_help(message: types.Message):
    """Показывает справку по командам"""
    help_text = """
💡 Вот что я умею:

📌 Основные команды:
/start – Запустить бота
/help – Получить справку

💸 Учёт финансов:
/spent [сумма] [категория] – Добавить расход  
/income [сумма] [источник] – Добавить доход  

📊 Статистика:
/stats – Посмотреть общую статистику за месяц
/stats_week – Расходы за неделю
/stats_category [категория] – Статистика по конкретной категории

🎯 Цели:
/goals – Посмотреть свои цели
/add_goal [цель] [сумма] – Добавить новую цель
/deposit [цель] [сумма] – Внести средства в цель

⚙️ Настройки:
/set_currency [RUB/USD/EUR] – Изменить валюту
/set_limit [категория] [сумма] – Установить лимит на траты
"""
    await message.answer(help_text)