import re

import aiohttp

from parsers.base import BaseParser


class WildberriesParser(BaseParser):
    API_URL = "https://card.wb.ru/cards/v1/detail?appType=1&curr=rub&dest=-1257786&nm={article}"
    HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }

    ARTICLE_PATTERN = re.compile(r"/catalog/(\d+)/detail")

    async def is_valid(self, url: str) -> bool:
        return bool(self.ARTICLE_PATTERN.search(url))

    async def parse(self, url: str) -> dict:
        match = self.ARTICLE_PATTERN.search(url)
        if not match:
            raise ValueError(f"Не удалось извлечь артикул из URL: {url}")

        article = match.group(1)

        async with aiohttp.ClientSession(headers=self.HEADERS) as session:
            async with session.get(self.API_URL.format(article=article)) as resp:
                resp.raise_for_status()
                data = await resp.json()

        products = data.get("data", {}).get("products", [])
        if not products:
            raise ValueError(f"Товар с артикулом {article} не найден")

        product = products[0]
        title = product.get("name", "")
        sizes = product.get("sizes", [])
        price_kopek = 0
        if sizes:
            price_kopek = sizes[0].get("price", {}).get("total", 0)
        price = round(price_kopek / 100, 2)
        currency = "rub"
        image_url = (
            f"https://basket-{article[0]}.wb.ru/vol{article[:len(article)-5]}"
            f"/part{article[:len(article)-3]}/{article}/images/big/1.jpg"
        )

        return {
            "title": title,
            "price": price,
            "currency": currency,
            "image_url": image_url,
        }