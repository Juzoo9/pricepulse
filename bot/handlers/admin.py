from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from bot.services.database import get_stats

router = Router()


@router.message(Command("admin"))
async def cmd_admin(message: Message):
    stats = await get_stats()
    await message.answer(
        f"<b>Статистика бота</b>\n\n"
        f"Уникальных пользователей: {stats['unique_users']}\n"
        f"Всего товаров: {stats['total_products']}\n"
        f"Всего проверок: {stats['total_checks']}",
        parse_mode="HTML",
    )