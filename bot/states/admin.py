from aiogram.fsm.state import State, StatesGroup


class AdminGroupStates(StatesGroup):
    waiting_name = State()
    waiting_year = State()


class AdminSubjectStates(StatesGroup):
    waiting_name = State()


class AdminLessonStates(StatesGroup):
    waiting_subject = State()
    waiting_teacher = State()
    waiting_group = State()
    waiting_weekday = State()
    waiting_start_time = State()
    waiting_end_time = State()
    waiting_room = State()
