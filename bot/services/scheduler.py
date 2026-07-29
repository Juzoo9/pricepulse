from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from bot.services.database import get_all_products, update_price
from bot.services.parser_engine import parse_url

scheduler = AsyncIOScheduler()


async def check_all_products(bot: Bot):
    products = await get_all_products()
    for product in products:
        try:
            result = await parse_url(product.url)

            if isinstance(result, dict) and result.get("error") == "out_of_stock":
                await bot.send_message(
                    chat_id=product.user_id,
                    text=(
                        f"\U0001f4ed <b>{product.title}</b>\n\n"
                        f"Товар временно отсутствует в продаже.\n"
                        f"<a href='{product.url}'>Посмотреть на сайте</a>"
                    ),
                    parse_mode="HTML",
                    disable_web_page_preview=True
                )
                continue

            new_price = result["price"]
        except Exception:
            continue
        old_price = product.current_price

        if new_price == old_price:
            continue

        await update_price(product.id, new_price)

        if old_price > 0 and product.threshold > 0:
            drop_percent = (old_price - new_price) / old_price * 100
            if drop_percent >= product.threshold:
                await bot.send_message(
                    chat_id=product.user_id,
                    text=(
                        f"Цена снизилась!\n"
                        f"{product.title}\n"
                        f"Было: {old_price} {product.currency.upper()}\n"
                        f"Стало: {new_price} {product.currency.upper()}\n"
                        f"Скидка: {drop_percent:.1f}%\n"
                        f"{product.url}"
                    ),
                )


def start_scheduler(bot: Bot):
    scheduler.add_job(
        check_all_products,
        "interval",
        minutes=30,
        args=[bot],
        id="check_prices",
        replace_existing=True,
    )
    scheduler.start()