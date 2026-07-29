from datetime import date, timedelta

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.services.appointment_db import Service


def services_keyboard(services: list[Service]) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(
            text=f"{s.name} — {s.price}₽ ({s.duration} мин)",
            callback_data=f"service_{s.id}"
        )]
        for s in services
    ]
    buttons.append([InlineKeyboardButton(text="Отмена", callback_data="cancel")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def dates_keyboard() -> InlineKeyboardMarkup:
    buttons = []
    today = date.today()
    for i in range(7):
        d = today + timedelta(days=i)
        label = d.strftime("%a %d.%m")
        buttons.append([
            InlineKeyboardButton(text=label, callback_data=f"date_{d.isoformat()}")
        ])
    buttons.append([InlineKeyboardButton(text="Отмена", callback_data="cancel")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def times_keyboard(slots: list) -> InlineKeyboardMarkup:
    buttons = []
    row = []
    for i, slot in enumerate(slots):
        label = slot.strftime("%H:%M")
        row.append(InlineKeyboardButton(text=label, callback_data=f"time_{label}"))
        if (i + 1) % 3 == 0:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton(text="Отмена", callback_data="cancel")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def confirm_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Подтвердить", callback_data="app_confirm_yes"),
            InlineKeyboardButton(text="Отмена", callback_data="cancel"),
        ],
    ])


def admin_appointments_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Подтвердить ✅", callback_data="admin_app_status_confirmed"),
            InlineKeyboardButton(text="Отменить ❌", callback_data="admin_app_status_cancelled"),
        ],
        [InlineKeyboardButton(text="Завершить ✔️", callback_data="admin_app_status_completed")],
        [InlineKeyboardButton(text="« Назад", callback_data="admin_app_back")],
    ])