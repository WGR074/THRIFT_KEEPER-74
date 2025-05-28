from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from decimal import Decimal, InvalidOperation

from states_hand.states_expense import ExpenseStates
from database.db import Database
from keyboards.main_menu import get_main_menu_keyboard
from keyboards.categories import get_categories_keyboard
from keyboards.confirm import get_confirmation_keyboard

router = Router()
db = Database()

@router.message(F.text == "➕ Добавить расход")
async def add_expense(message: Message, state: FSMContext):
    await state.set_state(ExpenseStates.waiting_for_category)
    await message.answer(
        "Выберите категорию расхода:",
        reply_markup=get_categories_keyboard()
    )


@router.message(
    ExpenseStates.waiting_for_category,
    F.text.in_([
        "🍔 Еда", "🚕 Транспорт",
        "🏠 Жильё", "🎮 Развлечения",
        "🛒 Покупки"
    ])
)
async def handle_predefined_category(message: Message, state: FSMContext):
    await state.update_data(category=message.text)
    await state.set_state(ExpenseStates.waiting_for_amount)
    await message.answer(
        f"Введите сумму расхода для {message.text}:",
        reply_markup=ReplyKeyboardRemove()
    )


@router.message(ExpenseStates.waiting_for_category, F.text == "✏️ Другая категория")
async def request_custom_category(message: Message, state: FSMContext):
    await state.set_state(ExpenseStates.waiting_for_custom_category)
    await message.answer(
        "Введите название своей категории (макс. 30 символов):",
        reply_markup=ReplyKeyboardRemove()
    )


@router.message(ExpenseStates.waiting_for_custom_category, F.text.len() <= 30)
async def handle_custom_category(message: Message, state: FSMContext):
    custom_category = message.text.strip()
    if not custom_category:
        await message.answer("Название категории не может быть пустым. Введите снова:")
        return

    await state.update_data(category=custom_category)
    await state.set_state(ExpenseStates.waiting_for_amount)
    await message.answer(
        f"Введите сумму расхода для '{custom_category}':"
    )


@router.message(ExpenseStates.waiting_for_amount)
async def process_amount_input(message: Message, state: FSMContext):
    try:
        amount = Decimal(message.text.replace(',', '.'))
        if amount <= 0:
            raise ValueError("Сумма должна быть положительной")

        await state.update_data(amount=str(amount))
        await state.set_state(ExpenseStates.waiting_for_description)
        await message.answer(
            "Хотите добавить описание к расходу? (Напишите текст или нажмите 'Пропустить')",
            reply_markup=get_confirmation_keyboard()
        )

    except (ValueError, InvalidOperation):
        await message.answer(
            "Пожалуйста, введите корректную сумму (например: 150 или 45.50)\n"
            "Сумма должна быть больше нуля."
        )


@router.message(ExpenseStates.waiting_for_description)
async def handle_description(message: Message, state: FSMContext):
    if len(message.text) > 200:
        await message.answer("Описание слишком длинное (макс. 200 символов). Сократите:")
        return

    await state.update_data(description=message.text)
    await save_transaction(message, state)


async def save_transaction(message: Message, state: FSMContext):
    data = await state.get_data()

    try:
        # Проверяем обязательные поля
        if 'amount' not in data or 'category' not in data:
            await message.answer("❌ Не хватает данных для сохранения транзакции")
            return

        # Проверяем, что сумма — корректное число
        amount_str = data['amount']
        try:
            amount = Decimal(amount_str)
        except InvalidOperation:
            await message.answer("❌ Сумма указана некорректно. Введите число.")
            return

        if amount <= 0:
            await message.answer("❌ Сумма должна быть больше нуля.")
            return

        user_id = message.from_user.id

        success = db.add_transaction(
            user_id=user_id,
            amount=float(amount),
            category=data['category'],
            transaction_type='expense',
            description=data.get('description')
        )

        if success:
            balance = db.get_balance(user_id)
            await message.answer(
                f"✅ Расход успешно добавлен:\n"
                f"• Категория: {data['category']}\n"
                f"• Сумма: {amount:.2f}\n"
                f"• Описание: {data.get('description', 'нет')}\n\n"
                f"💳 Текущий баланс: {balance:.2f}",
                reply_markup=get_main_menu_keyboard()
            )
        else:
            await message.answer("❌ Не удалось сохранить расход. Попробуйте позже.")

    except Exception as e:
        print(f"Ошибка при сохранении транзакции: {e}")
        await message.answer("⚠️ Произошла ошибка при сохранении. Попробуйте снова.")

    finally:
        await state.clear()


@router.message(F.text == "🔙 Назад")
async def back_to_menu(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Главное меню:",
        reply_markup=get_main_menu_keyboard()
    )