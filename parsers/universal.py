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