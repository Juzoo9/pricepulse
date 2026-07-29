from aiogram.fsm.state import State, StatesGroup


class AppointmentBooking(StatesGroup):
    select_service = State()
    enter_name = State()
    enter_phone = State()
    select_date = State()
    select_time = State()
    confirm = State()