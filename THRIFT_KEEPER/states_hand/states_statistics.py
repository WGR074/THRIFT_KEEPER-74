from aiogram.fsm.state import State, StatesGroup

class StatisticsStates(StatesGroup):
    waiting_for_period = State()