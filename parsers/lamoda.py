import re
from typing import Optional, Dict
from bs4 import BeautifulSoup
from .browser_proxy_client import BrowserProxyClient
from bot.services.captcha_notifier import CaptchaNotifier


class LamodaParser:
    PATTERNS = [r"https?://(?:www\.)?lamoda\.ru/.*"]

    def __init__(self, notifier: Optional[CaptchaNotifier] = None):
        self.client = BrowserProxyClient()
        self.notifier = notifier or CaptchaNotifier()

    def is_valid(self, url: str) -> bool:
        return any(re.match(p, url) for p in self.PATTERNS)

    async def parse(self, url: str) -> Optional[Dict]:
        html = await self.client.get_html(url)
        if not html:
            return {"error": "empty_html", "url": url, "source": "lamoda"}

        soup = BeautifulSoup(html, 'lxml')
        text = soup.get_text(separator=" ", strip=True)

        title = (soup.title.string or "").lower() if soup.title else ""
        if any(x in title for x in ["captcha", "капча", "проверка", "404"]):
            await self.notifier.notify(url, f"title: {title[:100]}", "lamoda")
            return {"error": "captcha", "captcha_type": title[:100], "url": url, "source": "lamoda"}

        # Проверка на отсутствие в наличии
        stock_text = text.lower()
        stock_indicators = [
            "нет в наличии", "out of stock", "распродано", "sold out",
            "ожидается поступление", "not available", "нет размеров",
            "временно отсутствует", "закончился", "нет в продаже"
        ]
        if any(ind in stock_text for ind in stock_indicators):
            name = "Неизвестно"
            name_el = soup.find("h1") or soup.find("h1", class_=re.compile("product-title|product-name"))
            if name_el:
                name = name_el.get_text(strip=True)
            elif soup.find("meta", property="og:title"):
                name = soup.find("meta", property="og:title").get("content", "Неизвестно").split('|')[0].strip()
            return {
                "error": "out_of_stock",
                "name": name,
                "url": url,
                "source": "lamoda",
                "price": None,
                "price_card": None,
                "old_price": None,
                "image": ""
            }

        result = {"name": "Неизвестно", "price": None, "price_card": None, "old_price": None, "image": "", "url": url, "source": "lamoda"}

        # DOM
        name_el = soup.find("h1", class_=re.compile("product-title|product-name")) or soup.find("h1")
        price_el = soup.find("span", class_=re.compile("price")) or soup.find("div", class_=re.compile("product-prices__price")) or soup.find("span", itemprop="price")
        old_price_el = soup.find("span", class_=re.compile("price__old|product-prices__price-old")) or soup.find("span", style=re.compile("line-through"))
        img_el = soup.find("img", class_=re.compile("product-gallery|gallery-image")) or soup.find("meta", property="og:image")

        if name_el:
            result["name"] = name_el.get_text(strip=True)
        if price_el:
            result["price"] = self._clean_price(price_el.get_text(strip=True))
        if old_price_el:
            result["old_price"] = self._clean_price(old_price_el.get_text(strip=True))
        if img_el:
            result["image"] = img_el.get("src") if img_el.name == "img" else img_el.get("content", "")

        # Regex fallback
        prices_found = re.findall(r'(\d[\d\s]+)\s*₽', text)
        all_prices = []
        for p in prices_found:
            clean = int(re.sub(r'\D', '', p))
            if clean > 300 and clean not in all_prices:
                all_prices.append(clean)
        all_prices.sort()

        if len(all_prices) >= 2 and result["price"] is None:
            result["price"] = all_prices[0]
            result["old_price"] = all_prices[-1]
        elif len(all_prices) == 1 and result["price"] is None:
            result["price"] = all_prices[0]

        # Meta fallback
        if result["name"] == "Неизвестно":
            meta = soup.find("meta", property="og:title")
            if meta:
                result["name"] = meta.get("content", "Неизвестно").split('|')[0].strip()

        return result

    def _clean_price(self, raw) -> Optional[int]:
        if raw is None:
            return None
        if isinstance(raw, (int, float)):
            return int(raw)
        digits = re.sub(r"[^\d]", "", str(raw))
        return int(digits) if digits else None

    async def close(self):
        pass