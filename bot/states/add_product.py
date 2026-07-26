from aiogram.fsm.state import State, StatesGroup


class AddProduct(StatesGroup):
    waiting_url = State()
    confirm = State()
    set_threshold = State()