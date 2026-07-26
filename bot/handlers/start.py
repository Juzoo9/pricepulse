from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "Привет! Я PricePulse Bot — помогу отслеживать цены на товары.\n\n"
        "Доступные команды:\n"
        "/add — добавить товар для отслеживания\n"
        "/list — мои товары\n"
        "/history <id> — график цены товара\n"
        "/admin — статистика (только для админа)\n"
        "/help — справка"
    )


@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "Как пользоваться ботом:\n\n"
        "1. Отправь /add и ссылку на товар\n"
        "2. Бот найдёт цену и предложит отслеживать\n"
        "3. Укажи порог скидки в процентах\n"
        "4. Каждые 30 минут бот проверяет цены\n"
        "5. Если цена упала ниже порога — придёт уведомление\n\n"
        "Команды:\n"
        "/add — добавить товар\n"
        "/list — показать все отслеживаемые товары\n"
        "/history <id> — график изменения цены\n"
        "/help — эта справка"
    )