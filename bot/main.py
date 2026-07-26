import asyncio
import os

from aiogram import Bot, Dispatcher
from dotenv import load_dotenv

from bot.handlers.add_product import router as add_product_router
from bot.handlers.admin import router as admin_router
from bot.handlers.history import router as history_router
from bot.handlers.list_products import router as list_products_router
from bot.handlers.start import router as start_router
from bot.services.database import init_db
from bot.services.scheduler import start_scheduler

load_dotenv()


async def main():
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise ValueError("BOT_TOKEN не найден в .env")

    bot = Bot(token=token)
    dp = Dispatcher()

    dp.include_router(start_router)
    dp.include_router(add_product_router)
    dp.include_router(list_products_router)
    dp.include_router(history_router)
    dp.include_router(admin_router)

    await init_db()
    start_scheduler(bot)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())