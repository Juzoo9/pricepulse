from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.keyboards.add_product import confirm_keyboard
from bot.services.database import add_product
from bot.services.parser_engine import parse_url
from bot.states.add_product import AddProduct

router = Router()


@router.message(Command("add"))
async def cmd_add(message: Message, state: FSMContext):
    await state.set_state(AddProduct.waiting_url)
    await message.answer("Отправьте ссылку на товар для отслеживания:")


@router.message(AddProduct.waiting_url)
async def process_url(message: Message, state: FSMContext):
    url = message.text.strip()
    try:
        result = await parse_url(url)
    except ValueError as e:
        await message.answer(f"Ошибка: {e}")
        await state.clear()
        return

    await state.update_data(
        url=url,
        title=result["title"],
        price=result["price"],
        currency=result["currency"],
        image_url=result["image_url"],
        parser_type="auto",
    )

    caption = (
        f"<b>{result['title']}</b>\n"
        f"Цена: {result['price']} {result['currency'].upper()}"
    )

    if result.get("image_url"):
        await message.answer_photo(
            photo=result["image_url"],
            caption=caption,
            parse_mode="HTML",
            reply_markup=confirm_keyboard(),
        )
    else:
        await message.answer(
            caption,
            parse_mode="HTML",
            reply_markup=confirm_keyboard(),
        )

    await state.set_state(AddProduct.confirm)


@router.callback_query(AddProduct.confirm, F.data == "confirm_yes")
async def confirm_add(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await state.set_state(AddProduct.set_threshold)
    await callback.message.answer(
        "Введите порог скидки в процентах (например, 10):"
    )
    await callback.answer()


@router.callback_query(AddProduct.confirm, F.data == "confirm_no")
async def cancel_add(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await state.clear()
    await callback.message.answer("Добавление отменено.")
    await callback.answer()


@router.message(AddProduct.set_threshold)
async def process_threshold(message: Message, state: FSMContext):
    try:
        threshold = float(message.text.strip().replace(",", "."))
    except ValueError:
        await message.answer("Введите число — процент скидки (например, 10):")
        return

    data = await state.get_data()
    try:
        await add_product(
            user_id=message.from_user.id,
            url=data["url"],
            title=data["title"],
            price=data["price"],
            currency=data["currency"],
            image_url=data.get("image_url", ""),
            parser_type=data.get("parser_type", "unknown"),
            threshold=threshold,
        )
    except Exception as e:
        await message.answer(f"Ошибка при сохранении: {e}")
        await state.clear()
        return

    await state.clear()
    await message.answer(
        f"Товар добавлен!\n"
        f"Название: {data['title']}\n"
        f"Цена: {data['price']} {data['currency'].upper()}\n"
        f"Порог скидки: {threshold}%"
    )