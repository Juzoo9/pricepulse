import re
from typing import Optional, Dict, Any
from bs4 import BeautifulSoup
from .browser_proxy_client import BrowserProxyClient
from bot.services.captcha_notifier import CaptchaNotifier


class UniversalBrowserParser:
    def __init__(self, notifier: Optional[CaptchaNotifier] = None):
        self.client = BrowserProxyClient()
        self.notifier = notifier or CaptchaNotifier()

    async def parse(self, url: str, selectors: Dict[str, str] = None) -> Optional[Dict]:
        html = await self.client.get_html(url)
        if not html:
            return {"error": "empty_html", "url": url, "source": "universal"}

        soup = BeautifulSoup(html, 'lxml')
        text = soup.get_text(separator=" ", strip=True)

        title = (soup.title.string or "").lower() if soup.title else ""
        if any(x in title for x in ["captcha", "капча", "ddos", "access denied"]):
            await self.notifier.notify(url, f"title: {title[:100]}", "universal")
            return {"error": "captcha", "captcha_type": title[:100], "url": url, "source": "universal"}

        # --- Проверка на отсутствие в наличии ---
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

        result = {"url": url, "source": "universal", "name": "Неизвестно", "price": None, "price_card": None, "old_price": None, "image": ""}

        # Селекторы
        if selectors:
            for field, selector in selectors.items():
                if field in ["price", "old_price", "price_card"]:
                    continue
                el = soup.select_one(selector)
                result[field] = el.get_text(strip=True) if el else "Не найдено"

        # Regex fallback для цен
        prices_found = re.findall(r'(\d[\d\s]+)\s*₽', text)
        all_prices = []
        for p in prices_found:
            clean = int(re.sub(r'\D', '', p))
            if clean > 500 and clean not in all_prices:
                all_prices.append(clean)
        all_prices.sort()

        if len(all_prices) >= 3:
            result["price_card"] = all_prices[0]
            result["price"] = all_prices[1]
            result["old_price"] = all_prices[-1]
        elif len(all_prices) == 2:
            result["price"] = all_prices[0]
            result["old_price"] = all_prices[-1]
        elif len(all_prices) == 1:
            result["price"] = all_prices[0]

        # Meta
        meta = soup.find("meta", property="og:title")
        if meta:
            result["name"] = meta.get("content", "Неизвестно").split('|')[0].strip()
        meta_img = soup.find("meta", property="og:image")
        if meta_img:
            result["image"] = meta_img.get("content", "")

        # Очистка цен из селекторов
        for pf in ["price", "old_price", "price_card"]:
            if pf in result and result[pf] and result[pf] not in ["Не найдено", None]:
                digits = re.sub(r"[^\d]", "", str(result[pf]))
                result[pf] = int(digits) if digits else None

        return result

    async def close(self):
        pass