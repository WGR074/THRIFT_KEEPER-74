from states_hand.states_statistics import StatisticsStates
from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from datetime import datetime, timedelta

from database.db import Database
from keyboards.main_menu import get_main_menu_keyboard
from keyboards.period_kb import get_period_keyboard

router = Router()
db = Database()

PERIOD_BUTTONS = {
    "today": "🌞 Сегодня",
    "week": "📅 Эта неделя", 
    "month": "🌙 Этот месяц",
    "year": "🎉 Этот год",
    "back": "🔙 Назад"
}

async def back_to_menu(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("🔙 Возврат в главное меню", reply_markup=get_main_menu_keyboard())

@router.message(F.text == PERIOD_BUTTONS["back"])
async def handle_back_command_global(message: Message, state: FSMContext):
    await back_to_menu(message, state)

@router.message(F.text == "📊 Статистика")
async def choose_statistics_period(message: Message, state: FSMContext):
    await message.answer("Выберите период для статистики:", reply_markup=get_period_keyboard())
    await state.set_state(StatisticsStates.waiting_for_period)

@router.message(StatisticsStates.waiting_for_period)
async def show_statistics_by_period(message: Message, state: FSMContext):
    user_id = message.from_user.id
    today = datetime.today()
    period_text = message.text

    period_config = {
        PERIOD_BUTTONS["today"]: {
            "start": today.replace(hour=0, minute=0, second=0, microsecond=0),
            "name": "🌞 за сегодня"
        },
        PERIOD_BUTTONS["week"]: {
            "start": (today - timedelta(days=today.weekday())).replace(hour=0, minute=0, second=0),
            "name": "📅 за неделю"
        },
        PERIOD_BUTTONS["month"]: {
            "start": today.replace(day=1, hour=0, minute=0, second=0),
            "name": "🌙 за месяц"
        },
        PERIOD_BUTTONS["year"]: {
            "start": today.replace(month=1, day=1, hour=0, minute=0, second=0),
            "name": "🎉 за год"
        },
        PERIOD_BUTTONS["back"]: {
            "action": back_to_menu
        }
    }

    if period_text not in period_config:
        await message.answer("❌ Неизвестный период.")
        return await back_to_menu(message, state)

    config = period_config[period_text]
    
    if "action" in config:
        return await config["action"](message, state)

    stats = db.get_statistics_by_period(
        user_id, 
        start_date=config["start"], 
        end_date=today
    )

    text = (
        f"<b>{config['name']}</b>\n\n"
        f"💰 <b>Баланс:</b> {stats['balance']:.2f}\n"
        f"📈 <b>Доходы:</b> +{stats['total_income']:.2f}\n"
        f"📉 <b>Расходы:</b> -{stats['total_expenses']:.2f}\n\n"
        "📌 <b>Расходы по категориям:</b>\n"
    )

    if stats.get('expenses_by_category'):
        text += "\n".join([f"• {cat}: {amt:.2f}" for cat, amt in stats['expenses_by_category']])
    else:
        text += "Нет данных"

    text += "\n\n📜 <b>Последние транзакции:</b>\n"
    if stats.get('recent_transactions'):
        for t in stats['recent_transactions']:
            text += (
                f"{'💸 Доход' if t['type'] == 'income' else '🛒 Расход'}\n"
                f"  Категория: {t['category']}\n"
                f"  Сумма: {t['amount']:.2f}\n"
                f"  Описание: {t.get('description', '—')}\n——————\n"
            )
    else:
        text += "Нет записей"

    await message.answer(text, parse_mode="HTML", reply_markup=get_main_menu_keyboard())
    await state.clear()
