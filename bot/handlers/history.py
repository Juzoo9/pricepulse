from aiogram import Router
from aiogram.filters import Command
from aiogram.types import BufferedInputFile, Message

from bot.services.chart import generate_price_chart
from bot.services.database import get_product_by_id, get_price_history

router = Router()


@router.message(Command("history"))
async def cmd_history(message: Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("Укажите ID товара: /history <id>")
        return

    try:
        product_id = int(args[1])
    except ValueError:
        await message.answer("ID должен быть числом.")
        return

    product = await get_product_by_id(product_id)
    if product is None:
        await message.answer("Товар не найден.")
        return

    if product.user_id != message.from_user.id:
        await message.answer("Этот товар не принадлежит вам.")
        return

    history = await get_price_history(product_id)
    chart_bytes = await generate_price_chart(history, product.title)

    file = BufferedInputFile(chart_bytes, filename="chart.png")
    await message.answer_photo(
        photo=file,
        caption=(
            f"<b>{product.title}</b>\n"
            f"Текущая цена: {product.current_price} {product.currency.upper()}"
        ),
        parse_mode="HTML",
    )