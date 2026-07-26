from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from bot.services.database import delete_product, get_user_products

router = Router()


@router.message(Command("list"))
async def cmd_list(message: Message):
    products = await get_user_products(message.from_user.id)
    if not products:
        await message.answer("У вас нет отслеживаемых товаров.")
        return

    for product in products:
        text = (
            f"<b>{product.title}</b>\n"
            f"Цена: {product.current_price} {product.currency.upper()}\n"
            f"Порог: {product.threshold}%\n"
            f"ID: {product.id}"
        )
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Удалить", callback_data=f"del_{product.id}")],
        ])
        await message.answer(text, parse_mode="HTML", reply_markup=keyboard)


@router.callback_query(F.data.startswith("del_"))
async def delete_product_callback(callback: CallbackQuery):
    product_id = int(callback.data.split("_")[1])
    try:
        await delete_product(product_id)
        await callback.message.edit_text("Товар удалён.")
    except ValueError:
        await callback.message.edit_text("Товар не найден.")
    await callback.answer()