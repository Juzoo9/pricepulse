from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command, StateFilter

from bot.states.add_product import AddProduct
from bot.services.parser_engine import parse_url

router = Router()

# === ХЕНДЛЕР КОМАНДЫ /add ===
@router.message(Command("add"))
async def cmd_add(message: Message, state: FSMContext):
    await message.answer("Пришлите ссылку на товар:")
    await state.set_state(AddProduct.waiting_url)

# === ХЕНДЛЕР ПОЛУЧЕНИЯ ССЫЛКИ ===
@router.message(StateFilter(AddProduct.waiting_url))
async def process_url(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("Пожалуйста, отправьте ссылку текстом.")
        return
    
    url = message.text.strip()
    
    try:
        result = await parse_url(url)

        if isinstance(result, dict) and result.get("error") == "out_of_stock":
            name = result.get("name", "Товар")
            await message.answer(
                f"\ud83d\udced <b>{name}</b>\n\n"
                f"Товар временно отсутствует в продаже.\n"
                f"<a href='{result['url']}'>Посмотреть на сайте</a>",
                parse_mode="HTML",
                disable_web_page_preview=True
            )
            await state.clear()
            return

        await message.answer(
            f"Найден товар:\n\n"
            f"📦 {result['title']}\n"
            f"💰 {result['price']} {result['currency']}\n\n"
            f"Добавить в отслеживание?"
        )
        await state.set_state(AddProduct.confirm)
    except Exception as e:
        await message.answer(f"❌ Ошибка парсинга: {e}")
        await state.clear()