import re

import aiohttp
from bs4 import BeautifulSoup

from parsers.base import BaseParser


class UniversalParser(BaseParser):
    HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }

    async def is_valid(self, url: str) -> bool:
        return url.startswith(("http://", "https://"))

    async def parse(self, url: str) -> dict:
        async with aiohttp.ClientSession(headers=self.HEADERS) as session:
            async with session.get(url) as resp:
                resp.raise_for_status()
                html = await resp.text()

        soup = BeautifulSoup(html, "html.parser")

        # --- Проверка на отсутствие в наличии ---
        text = soup.get_text(separator=" ", strip=True)
        stock_text = text.lower()
        out_of_stock_phrases = [
            "нет в наличии", "out of stock", "распродано", "sold out",
            "ожидается поступление", "not available", "нет размеров",
            "временно отсутствует", "закончился", "нет в продаже",
            "не доступен", "unavailable", "отсутствует", "нет на складе"
        ]
        if any(phrase in stock_text for phrase in out_of_stock_phrases):
            name = "Неизвестно"
            meta = soup.find("meta", property="og:title")
            if meta:
                name = meta.get("content", "Неизвестно").split('|')[0].strip()
            if not name or name == "Неизвестно":
                h1 = soup.find("h1")
                if h1:
                    name = h1.get_text(strip=True)
            return {
                "error": "out_of_stock",
                "name": name,
                "url": url,
                "source": "universal",
                "price": None,
                "price_card": None,
                "old_price": None,
                "image": ""
            }

        title = self._extract_title(soup)
        price = self._extract_price(soup)
        currency = self._extract_currency(soup)
        image_url = self._extract_image(soup)

        return {
            "title": title,
            "price": price,
            "currency": currency,
            "image_url": image_url,
        }

    def _extract_title(self, soup: BeautifulSoup) -> str:
        og_title = soup.find("meta", property="og:title")
        if og_title and og_title.get("content"):
            return og_title["content"].strip()
        tag = soup.find("title")
        if tag and tag.string:
            return tag.string.strip()
        return ""

    def _extract_price(self, soup: BeautifulSoup) -> float:
        og_price = soup.find("meta", property="og:price:amount")
        if og_price and og_price.get("content"):
            return self._clean_price(og_price["content"])
        meta_price = soup.find("meta", itemprop="price")
        if meta_price and meta_price.get("content"):
            return self._clean_price(meta_price["content"])
        price_el = soup.select_one(".price")
        if price_el:
            return self._clean_price(price_el.get_text(strip=True))
        price_el = soup.select_one('[class*="price"]')
        if price_el:
            return self._clean_price(price_el.get_text(strip=True))
        return 0.0

    def _extract_currency(self, soup: BeautifulSoup) -> str:
        og_currency = soup.find("meta", property="og:price:currency")
        if og_currency and og_currency.get("content"):
            return og_currency["content"].strip().lower()
        meta_currency = soup.find("meta", itemprop="priceCurrency")
        if meta_currency and meta_currency.get("content"):
            return meta_currency["content"].strip().lower()
        return "rub"

    def _extract_image(self, soup: BeautifulSoup) -> str:
        og_image = soup.find("meta", property="og:image")
        if og_image and og_image.get("content"):
            return og_image["content"].strip()
        meta_image = soup.find("meta", itemprop="image")
        if meta_image and meta_image.get("content"):
            return meta_image["content"].strip()
        return ""

    @staticmethod
    def _clean_price(raw: str) -> float:
        cleaned = re.sub(r"[^\d.,]", "", raw)
        cleaned = cleaned.replace(",", ".")
        parts = cleaned.split(".")
        if len(parts) > 2:
            cleaned = "".join(parts[:-1]) + "." + parts[-1]
        try:
            return round(float(cleaned), 2)
        except ValueError:
            return 0.0
async def parse(self, url: str) -> dict:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=HEADERS, timeout=30) as resp:
                if resp.status == 403:
                    return {
                        "title": "Ошибка 403",
                        "price": "Сайт заблокировал парсер",
                        "currency": "",
                        "image_url": ""
                    }
                resp.raise_for_status()
                html = await resp.text()
                # ... дальше твой код парсинга ...
    except Exception as e:
        return {
            "title": "Ошибка парсинга",
            "price": str(e),
            "currency": "",
            "image_url": ""
        }