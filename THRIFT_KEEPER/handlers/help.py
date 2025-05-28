from aiogram import Router, F
from aiogram.types import Message
from aiogram.utils.markdown import hbold, hlink

router = Router()

HELP_TEXT = f"""
🌟 {hbold('Помощь по командам:')}

▫️ {hbold('Основные команды:')}
→ /start — Перезапустить бота
→ /menu — Главное меню
→ 📘 О нас — Информация о боте

▫️ {hbold('Финансы:')}
→ ➕ Доход — Добавить доход
→ ➖ Расход — Добавить расход
→ 📊 Статистика — Показать статистику

▫️ {hbold('Цели:')}
→ 🎯 Цели — Управление финансовыми целями

🛠 {hbold('Техническая поддержка:')}
→ Проблемы и вопросы: @wgr074
"""

@router.message(F.text == "🆘 Помощь")
async def help_command(message: Message):
    await message.answer(HELP_TEXT, parse_mode="HTML", disable_web_page_preview=True)