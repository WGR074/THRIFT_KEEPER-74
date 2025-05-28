from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from database.db import Database
from keyboards.registration_kb import get_currency_keyboard
from states_hand.states_registration import RegistrationStates

router = Router()
db = Database()


async def start_registration(message: Message, state: FSMContext):
    await message.answer("👋 Привет! Как я могу к тебе обращаться?")
    await state.set_state(RegistrationStates.getting_name)


@router.message(RegistrationStates.getting_name)
async def process_name(message: Message, state: FSMContext):
    name = message.text.strip()

    if not name:
        await message.answer("Имя не может быть пустым. Введите снова:")
        return

    await state.update_data(name=name)
    await message.answer("Выберите вашу валюту:", reply_markup=get_currency_keyboard())
    await state.set_state(RegistrationStates.getting_currency)


@router.callback_query(RegistrationStates.getting_currency, F.data.startswith("currency_"))
async def process_currency(callback: CallbackQuery, state: FSMContext):
    currency = callback.data.replace("currency_", "")

    user_data = await state.get_data()
    user_id = callback.from_user.id
    name = user_data['name']

    if db.save_user(user_id, name, currency):
        await callback.message.edit_text(f"✅ Регистрация завершена!\n\nДобро пожаловать, {name}!")
        
        from keyboards.main_menu import get_main_menu_keyboard
        await callback.message.answer(
            "Выберите действие:",
            reply_markup=get_main_menu_keyboard()
        )
    else:
        await callback.message.edit_text("❌ Ошибка при сохранении данных. Попробуйте позже.")

    await state.clear()
    await callback.answer()

    