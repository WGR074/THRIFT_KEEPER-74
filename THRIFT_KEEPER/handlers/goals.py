from decimal import Decimal, InvalidOperation
from datetime import datetime
import logging
from aiogram.types import ReplyKeyboardRemove
from aiogram import types, Router, F
from aiogram.fsm.context import FSMContext
from aiogram.filters.state import State, StateFilter

from states_hand.states_goals import GoalStates
from database.db import Database
from keyboards.goal_kb import (get_goal_keyboard, goals_list_kb, skip_deadline_kb, confirm_delete_kb, edit_goal_kb)

router = Router()
db = Database()
logger = logging.getLogger(__name__)


async def handle_error(message: types.Message, state: FSMContext, error_msg: str, next_state: State):
    """Обработка ошибок с сохранением состояния"""
    await message.answer(f"❌ {error_msg}\nПопробуйте снова или нажмите /cancel для отмены")
    await state.set_state(next_state)

def format_goal_details(goal: dict) -> str:
    """
    Форматирует информацию о цели для вывода пользователю
    """
    try:
        progress = (goal['current_amount'] / goal['target_amount']) * 100 if goal['target_amount'] > 0 else 0
        deadline_info = ""
        if goal['deadline']:
            deadline = datetime.strptime(goal['deadline'], "%Y-%m-%d").date()
            days_left = (deadline - datetime.now().date()).days
            status = "осталось дней" if days_left > 0 else "просрочена на"
            deadline_info = f"\n⏳ До дедлайна: {abs(days_left)} {status} ({goal['deadline']})"
        
        return (
            f"\n🎯 <b>{goal['name']}</b>\n"
            f"💰 Баланс: {goal['current_amount']:.2f} / {goal['target_amount']:.2f}\n"
            f"📊 Прогресс: {min(progress, 100):.1f}%\n"
            f"📅 Дедлайн: {goal['deadline'] or 'Не задан'}"
            f"{deadline_info}\n"
        )
    except Exception as e:
        logger.error(f"Ошибка форматирования информации о цели: {e}")
        return "\n❌ Не удалось отобразить данные цели\n"

@router.message(F.text == "🎯 Цели")
async def handle_goals(message: types.Message):
    await message.answer("🎯 Управление целями:", reply_markup=get_goal_keyboard())


@router.message(F.text.casefold() == "назад", StateFilter(GoalStates))
async def handle_back_command(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("🔙 Возврат в меню целей", reply_markup=get_goal_keyboard())

@router.message(F.text == "➕ Создать цель")
async def create_goal_start(message: types.Message, state: FSMContext):
    await state.set_state(GoalStates.enter_name)
    await message.answer("Введите название цели:", reply_markup=types.ReplyKeyboardRemove())


@router.message(GoalStates.enter_name)
async def process_goal_name(message: types.Message, state: FSMContext):
    if len(message.text.strip()) < 3:
        return await message.answer("❌ Название должно быть не короче 3 символов")
    await state.update_data(name=message.text.strip())
    await state.set_state(GoalStates.enter_amount)
    await message.answer("Введите целевую сумму:")


@router.message(F.text == "/cancel", StateFilter(GoalStates))
async def cancel_operation(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("🚫 Операция отменена", reply_markup=get_goal_keyboard())


@router.message(GoalStates.enter_amount)
async def process_goal_amount(message: types.Message, state: FSMContext):
    try:
        amount = Decimal(message.text.replace(',', '.'))
        if amount <= 0:
            raise ValueError("Сумма должна быть больше нуля")
        await state.update_data(target_amount=float(amount))
        await state.set_state(GoalStates.enter_deadline)
        await message.answer(
            "Введите дату завершения (ДД.ММ.ГГГГ) или нажмите 'Пропустить':",
            reply_markup=skip_deadline_kb()
        )
    except (ValueError, InvalidOperation) as e:
        await handle_error(
            message=message,
            state=state,
            error_msg=f"Неверный формат суммы: {str(e)}",
            next_state=GoalStates.enter_amount
        )


@router.message(GoalStates.enter_deadline)
async def process_goal_deadline(message: types.Message, state: FSMContext):
    data = await state.get_data()
    deadline = None
    if message.text.lower() != "пропустить":
        try:
            
            deadline = datetime.strptime(message.text, "%d.%m.%Y").date()
            today = datetime.now().date()
            if deadline < today:
                return await message.answer("❌ Дата не может быть в прошлом! Введите новую дату:")
        except ValueError:
            return await message.answer("❌ Неверный формат даты. Используйте ДД.ММ.ГГГГ:")


    if db.add_goal(
        user_id=message.from_user.id,
        name=data['name'],
        target_amount=data['target_amount'],
        deadline=deadline
    ):
        await message.answer("✅ Цель успешно создана!", reply_markup=get_goal_keyboard())
    else:
        await message.answer("❌ Ошибка при создании цели")
    await state.clear()


@router.message(F.text == "💰 Внести сумму")
async def select_goal_for_add(message: types.Message, state: FSMContext):
    try:
        goals = db.get_goals(message.from_user.id)
        if not goals:
            return await message.answer("❌ Нет активных целей", reply_markup=get_goal_keyboard())
        await state.set_state(GoalStates.select_goal_for_add)
        await message.answer("Выберите цель:", reply_markup=goals_list_kb(goals))
    except Exception as e:
        logger.error(f"Ошибка получения целей: {e}")
        await message.answer("❌ Ошибка при загрузке целей")


@router.message(GoalStates.select_goal_for_add)
async def process_goal_selection_for_add(message: types.Message, state: FSMContext):
    try:
        goal_name = message.text.replace("🎯 ", "").strip()
        goals = db.get_goals(message.from_user.id)
        goal = next((g for g in goals if g['name'].lower() == goal_name.lower()), None)
        if not goal:
            await state.clear()
            return await message.answer("❌ Цель не найдена")
        await state.update_data(goal_id=goal['id'])
        await message.answer(
            f"ℹ️ Информация о цели:\n{format_goal_details(goal)}\n\n"
            "Введите сумму для внесения:",
            reply_markup=types.ReplyKeyboardRemove()
        )
        await state.set_state(GoalStates.enter_amount_for_goal)
    except Exception as e:
        logger.error(f"Ошибка выбора цели: {e}")
        await message.answer("❌ Ошибка обработки запроса")


@router.message(GoalStates.enter_amount_for_goal)
async def process_add_amount(message: types.Message, state: FSMContext):
    try:
        data = await state.get_data()
        goal = db.get_goal_by_id(data['goal_id'])
        if not goal:
            await state.clear()
            return await message.answer("❌ Цель не найдена")

        try:
            amount = Decimal(message.text.replace(',', '.'))
            if amount <= 0:
                return await message.answer("❌ Сумма должна быть больше нуля")
            success, completed = db.update_goal_amount(data['goal_id'], float(amount))
            if not success:
                raise Exception("Ошибка обновления баланса")
            response = f"✅ Успешно внесено {amount:.2f}!"
            if completed:
                response += "\n🎉 Цель достигнута!"
            await message.answer(response, reply_markup=get_goal_keyboard())
        except (ValueError, InvalidOperation):
            return await message.answer("❌ Неверный формат суммы")
    except Exception as e:
        logger.error(f"Ошибка внесения средств: {e}", exc_info=True)
        await message.answer("❌ Произошла ошибка при внесении средств")
    finally:
        await state.clear()



@router.message(F.text == "📉 Снять сумму")
async def withdraw_goal_start(message: types.Message, state: FSMContext):
    try:
        user_id = message.from_user.id
        goals = db.get_goals(user_id)
        
        if not goals:
            return await message.answer("❌ Нет активных целей", reply_markup=get_goal_keyboard())
        
        await state.set_state(GoalStates.select_goal_for_withdraw)
        await message.answer("Выберите цель:", reply_markup=goals_list_kb(goals))
        
    except Exception as e:
        logger.error(f"Ошибка получения целей: {str(e)}", exc_info=True)
        await message.answer("❌ Ошибка при загрузке целей")

@router.message(GoalStates.select_goal_for_withdraw)
async def process_goal_withdraw_selection(message: types.Message, state: FSMContext):
    try:
        user_id = message.from_user.id
        goal_name = message.text.replace("🎯 ", "").strip()
        goal = db.get_goal_by_name(user_id, goal_name)
        
        if not goal:
            await state.clear()
            return await message.answer("❌ Цель не найдена")
        
        await state.update_data(goal_id=goal['id'])
        await message.answer(
            f"ℹ️ Текущий баланс: {goal['current_amount']:.2f}\n"
            "Введите сумму для снятия:",
            reply_markup=ReplyKeyboardRemove()
        )
        await state.set_state(GoalStates.enter_withdraw_amount)
        
    except Exception as e:
        logger.error(f"Ошибка выбора цели: {str(e)}", exc_info=True)
        await message.answer("❌ Ошибка обработки запроса")

@router.message(GoalStates.enter_withdraw_amount)
async def process_withdraw_amount(message: types.Message, state: FSMContext):
    try:
        data = await state.get_data()
        user_id = message.from_user.id
        goal_id = data['goal_id']
        
        goal = db.get_goal_by_id(goal_id)
        if not goal:
            await state.clear()
            return await message.answer("❌ Цель не найдена")
        
        try:

            amount = Decimal(message.text.replace(',', '.'))
            
            if amount <= 0:
                raise ValueError("Сумма должна быть больше нуля")
                
            current_balance = Decimal(str(goal['current_amount']))
            
            if amount > current_balance:
                raise ValueError(
                    f"Недостаточно средств. Доступно: {current_balance:.2f}"
                )

            new_balance = current_balance - amount
            if not db.update_goal_current_amount(goal_id, float(new_balance)):
                raise Exception("Ошибка обновления баланса в БД")
            
            updated_goal = db.get_goal_by_id(goal_id)
            
            await message.answer(
                f"✅ Успешно снято: {amount:.2f}\n"
                f"💰 Новый баланс: {updated_goal['current_amount']:.2f}",
                reply_markup=get_goal_keyboard()
            )
            
        except (ValueError, InvalidOperation) as e:
            await handle_error(
                message=message,
                state=state,
                error_msg=f"Ошибка: {str(e)}",
                next_state=GoalStates.enter_withdraw_amount
            )
            return
            
        except Exception as e:
            logger.error(f"Ошибка при обновлении баланса: {str(e)}", exc_info=True)
            await message.answer("❌ Ошибка при обновлении данных")
            
    except Exception as e:
        logger.error(f"Общая ошибка при снятии средств: {str(e)}", exc_info=True)
        await message.answer("❌ Критическая ошибка операции")
        
    finally:
        await state.clear()

@router.message(F.text == "🗑 Удалить цель")
async def delete_goal_start(message: types.Message, state: FSMContext):
    try:
        goals = db.get_all_goals(message.from_user.id)
        if not goals:
            return await message.answer("❌ Нет целей для удаления", reply_markup=get_goal_keyboard())
        await state.set_state(GoalStates.select_goal_for_delete)
        await message.answer("Выберите цель для удаления:", reply_markup=goals_list_kb(goals))
    except Exception as e:
        logger.error(f"Ошибка получения целей: {e}")
        await message.answer("❌ Ошибка при загрузке целей")


@router.message(GoalStates.select_goal_for_delete)
async def process_goal_deletion(message: types.Message, state: FSMContext):
    try:
        goal_name = message.text.replace("🎯 ", "").strip()
        goals = db.get_all_goals(message.from_user.id)
        goal = next((g for g in goals if g['name'].lower() == goal_name.lower()), None)
        if not goal:
            await state.clear()
            return await message.answer("❌ Цель не найдена")
        await state.update_data(goal_id=goal['id'])
        await message.answer(
            f"❓ Удалить цель '{goal['name']}'?\n"
            f"Текущий баланс: {goal['current_amount']:.2f}",
            reply_markup=confirm_delete_kb()
        )
        await state.set_state(GoalStates.confirm_delete)
    except Exception as e:
        logger.error(f"Ошибка выбора цели: {e}")
        await message.answer("❌ Ошибка обработки запроса")


@router.message(GoalStates.confirm_delete, F.text.in_(["✅ Да, удалить", "❌ Нет, отменить"]))
async def confirm_deletion(message: types.Message, state: FSMContext):
    try:
        if message.text == "❌ Нет, отменить":
            await message.answer("🚫 Удаление отменено", reply_markup=get_goal_keyboard())
            await state.clear()
            return
        data = await state.get_data()
        if db.delete_goal(data['goal_id']):
            await message.answer("✅ Цель успешно удалена!", reply_markup=get_goal_keyboard())
        else:
            raise Exception("Ошибка удаления цели")
    except Exception as e:
        logger.error(f"Ошибка удаления цели: {e}", exc_info=True)
        await message.answer("❌ Произошла ошибка при удалении")
    finally:
        await state.clear()

@router.message(F.text == "📈 Активные цели")
async def view_active_goals(message: types.Message):
    try:
        goals = db.get_goals(message.from_user.id)
        if not goals:
            return await message.answer("📭 Нет активных целей", reply_markup=get_goal_keyboard())
        text = "📋 Активные цели:\n" + "\n".join([format_goal_details(g) for g in goals])
        await message.answer(text, parse_mode="HTML", reply_markup=get_goal_keyboard())
    except Exception as e:
        logger.error(f"Ошибка загрузки целей: {e}")
        await message.answer("❌ Ошибка при загрузке целей")


@router.message(F.text == "✅ Выполненные")
async def view_completed_goals(message: types.Message):
    try:
        goals = db.get_completed_goals(message.from_user.id)
        if not goals:
            return await message.answer("📭 Нет выполненных целей", reply_markup=get_goal_keyboard())
        text = "🏆 Выполненные цели:\n" + "\n".join([format_goal_details(g) for g in goals])
        await message.answer(text, parse_mode="HTML", reply_markup=get_goal_keyboard())
    except Exception as e:
        logger.error(f"Ошибка загрузки целей: {e}")
        await message.answer("❌ Ошибка при загрузке целей")

@router.message(F.text == "✏️ Редактировать цель")
async def edit_goal_start(message: types.Message, state: FSMContext):
    try:
        goals = db.get_goals(message.from_user.id)
        if not goals:
            return await message.answer("❌ Нет целей для редактирования", reply_markup=get_goal_keyboard())
        await state.set_state(GoalStates.select_goal_to_edit)
        await message.answer("Выберите цель:", reply_markup=goals_list_kb(goals))
    except Exception as e:
        logger.error(f"Ошибка получения целей: {e}")
        await message.answer("❌ Ошибка при загрузке целей")


@router.message(GoalStates.select_goal_to_edit)
async def process_goal_selection_for_edit(message: types.Message, state: FSMContext):
    try:
        goal_name = message.text.replace("🎯 ", "").strip()
        goals = db.get_goals(message.from_user.id)
        goal = next((g for g in goals if g['name'].lower() == goal_name.lower()), None)
        if not goal:
            await state.clear()
            return await message.answer("❌ Цель не найдена")
        await state.update_data(edit_goal_id=goal['id'])
        await message.answer(
            f"ℹ️ Текущая информация о цели:\n{format_goal_details(goal)}\n\n"
            "Что вы хотите изменить?",
            reply_markup=edit_goal_kb()
        )
        await state.set_state(GoalStates.edit_goal_choice)
    except Exception as e:
        logger.error(f"Ошибка выбора цели: {e}")
        await message.answer("❌ Ошибка обработки запроса")


@router.message(GoalStates.edit_goal_choice, F.text == "📝 Изменить название")
async def edit_goal_name_start(message: types.Message, state: FSMContext):
    await state.set_state(GoalStates.edit_goal_name)
    await message.answer("Введите новое название:", reply_markup=types.ReplyKeyboardRemove())


@router.message(GoalStates.edit_goal_name)
async def process_edit_name(message: types.Message, state: FSMContext):
    try:
        data = await state.get_data()
        new_name = message.text.strip()
        if len(new_name) < 3:
            return await message.answer("❌ Название должно быть не короче 3 символов")
        if db.update_goal_name(data['edit_goal_id'], new_name):
            await message.answer("✅ Название успешно изменено!", reply_markup=get_goal_keyboard())
        else:
            raise Exception("Ошибка обновления названия")
    except Exception as e:
        logger.error(f"Ошибка изменения названия: {e}")
        await message.answer("❌ Ошибка при изменении названия")
    finally:
        await state.clear()


@router.message(GoalStates.edit_goal_choice, F.text == "💵 Изменить сумму")
async def edit_goal_amount_start(message: types.Message, state: FSMContext):
    await state.set_state(GoalStates.edit_goal_amount)
    await message.answer("Введите новую целевую сумму:", reply_markup=types.ReplyKeyboardRemove())


@router.message(GoalStates.edit_goal_amount)
async def process_edit_amount(message: types.Message, state: FSMContext):
    try:
        data = await state.get_data()
        goal = db.get_goal_by_id(data['edit_goal_id'])
        if not goal:
            await state.clear()
            return await message.answer("❌ Цель не найдена")
        try:
            new_amount = Decimal(message.text.replace(',', '.'))
            if new_amount <= 0:
                return await message.answer("❌ Сумма должна быть больше нуля")
            current_balance = Decimal(str(goal['current_amount']))
            if new_amount < current_balance:
                return await message.answer(
                    f"❌ Новая сумма ({new_amount:.2f}) не может быть меньше текущего баланса ({current_balance:.2f})"
                )
            if db.update_goal_target_amount(data['edit_goal_id'], float(new_amount)):
                await message.answer("✅ Целевая сумма обновлена!", reply_markup=get_goal_keyboard())
            else:
                raise Exception("Ошибка обновления суммы")
        except (ValueError, InvalidOperation):
            return await message.answer("❌ Неверный формат суммы")
    except Exception as e:
        logger.error(f"Ошибка изменения суммы: {e}")
        await message.answer("❌ Ошибка при изменении суммы")
    finally:
        await state.clear()


@router.message(GoalStates.edit_goal_choice, F.text == "📅 Изменить дедлайн")
async def edit_goal_deadline_start(message: types.Message, state: FSMContext):
    await state.set_state(GoalStates.edit_goal_deadline)
    await message.answer("Введите новую дату (ДД.ММ.ГГГГ):", reply_markup=types.ReplyKeyboardRemove())


@router.message(GoalStates.edit_goal_deadline)
async def process_edit_deadline(message: types.Message, state: FSMContext):
    try:
        data = await state.get_data()
        new_date = datetime.strptime(message.text, "%d.%m.%Y").date()
        today = datetime.now().date()
        if new_date < today:
            raise ValueError("Дата не может быть в прошлом")
        if db.update_goal_deadline(data['edit_goal_id'], new_date):
            await message.answer("✅ Дедлайн обновлен!", reply_markup=get_goal_keyboard())
        else:
            raise ValueError("Ошибка обновления дедлайна")
    except ValueError as e:
        await message.answer(f"❌ Ошибка: {str(e)}")
    except Exception as e:
        logger.error(f"Ошибка изменения дедлайна: {str(e)}")
        await message.answer("❌ Произошла ошибка при изменении")
    finally:
        await state.clear()


@router.message(GoalStates.edit_goal_choice, F.text == "🚫 Отменить редактирование")
async def cancel_editing(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("✖️ Редактирование отменено", reply_markup=get_goal_keyboard())

