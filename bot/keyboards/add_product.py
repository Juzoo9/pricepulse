from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def confirm_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Да, отслеживать", callback_data="confirm_yes"),
            InlineKeyboardButton(text="Отмена", callback_data="confirm_no"),
        ],
    ])