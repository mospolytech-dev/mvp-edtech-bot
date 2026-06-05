from aiogram.fsm.state import State, StatesGroup


class UserStates(StatesGroup):
    idle = State()


class RegistrationStates(StatesGroup):
    waiting_role = State()
    waiting_full_name = State()
    waiting_group = State()
    waiting_subjects = State()
