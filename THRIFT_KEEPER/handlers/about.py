from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

router = Router()

ABOUT_TEXT = """
<b>📘 О нас</b>

Этот бот создан для управления финансами. 
Основные возможности:
- Учет доходов и расходов
- Статистика по категориям
- Постановка финансовых целей

Версия: 1.0
Разработчик: Рябов Егор
"""

@router.message(F.text == "📘 О нас")
async def about_command(message: Message):
    await message.answer(ABOUT_TEXT, parse_mode="HTML")