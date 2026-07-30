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

        if isinstance(result, dict) and result.get("error"):
            error = result.get("error")
            name = result.get("name", "Товар")
            if error == "out_of_stock":
                await message.answer(
                    f"\U0001f4ed <b>{name}</b>\n\n"
                    f"Товар временно отсутствует в продаже.\n"
                    f"<a href='{result['url']}'>Посмотреть на сайте</a>",
                    parse_mode="HTML",
                    disable_web_page_preview=True
                )
            elif error == "captcha":
                await message.answer(
                    f"\U0001f6ab Сайт запросил капчу. Вручную откройте ссылку:\n{result['url']}"
                )
            else:
                await message.answer(f"\u274c Ошибка парсинга: {error}")
            await state.clear()
            return

        name = result.get("name", "Неизвестно")
        price = result.get("price", "?")
        source = result.get("source", "магазин")
        await message.answer(
            f"Найден товар:\n\n"
            f"\U0001f4e6 <b>{name}</b>\n"
            f"\U0001f4b0 {price} {source}\n\n"
            f"Добавить в отслеживание?"
        )
        await state.set_state(AddProduct.confirm)
    except Exception as e:
        await message.answer(f"❌ Ошибка парсинга: {e}")
        await state.clear()