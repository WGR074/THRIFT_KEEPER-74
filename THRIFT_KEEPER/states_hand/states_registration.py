from aiogram.fsm.state import State, StatesGroup

class RegistrationStates(StatesGroup):
    getting_name = State()
    getting_currency = State()