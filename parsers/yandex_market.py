import re
import json
from typing import Optional, Dict
from bs4 import BeautifulSoup
from .browser_proxy_client import BrowserProxyClient
from bot.services.captcha_notifier import CaptchaNotifier


class YandexMarketParser:
    PATTERNS = [r"https?://(?:www\.)?market\.yandex\.ru/.*"]

    def __init__(self, notifier: Optional[CaptchaNotifier] = None):
        self.client = BrowserProxyClient()
        self.notifier = notifier or CaptchaNotifier()

    def is_valid(self, url: str) -> bool:
        return any(re.match(p, url) for p in self.PATTERNS)

    async def parse(self, url: str) -> Optional[Dict]:
        html = await self.client.get_html(url)
        if not html:
            return {"error": "empty_html", "url": url, "source": "yandex_market"}

        soup = BeautifulSoup(html, 'lxml')
        text = soup.get_text(separator=" ", strip=True)

        title = (soup.title.string or "").lower() if soup.title else ""
        if any(x in title for x in ["captcha", "капча", "smartcaptcha", "ddos"]):
            await self.notifier.notify(url, f"title: {title[:100]}", "yandex_market")
            return {"error": "captcha", "captcha_type": title[:100], "url": url, "source": "yandex_market"}

        # Проверка на отсутствие в наличии
        stock_text = text.lower()
        if any(x in stock_text for x in ["нет в наличии", "распродано", "sold out", "out of stock", "не доступен"]):
            name = "Неизвестно"
            meta = soup.find("meta", property="og:title")
            if meta:
                name = meta.get("content", "Неизвестно").split('|')[0].strip()
            return {"error": "out_of_stock", "name": name, "url": url, "source": "yandex_market", "price": None, "price_card": None, "old_price": None, "image": ""}

        result = {"name": "Неизвестно", "price": None, "price_card": None, "old_price": None, "image": "", "url": url, "source": "yandex_market"}

        # JSON-LD
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.string)
                if isinstance(data, dict) and data.get("@type") == "Product":
                    offers = data.get("offers", {})
                    if isinstance(offers, dict):
                        result["name"] = data.get("name", "Неизвестно")
                        result["price"] = self._clean_price(offers.get("price"))
                        result["old_price"] = self._clean_price(offers.get("highPrice"))
                        result["image"] = data.get("image", "")
            except Exception:
                continue

        # DOM fallback
        if result["price"] is None:
            name_el = soup.find("h1", {"data-auto": "productCardTitle"}) or soup.find("h1") or soup.find("h3")
            price_el = soup.find("span", {"data-auto": "mainPrice"}) or soup.find("div", {"data-auto": "price"})
            img_el = soup.find("img", {"data-auto": "image"}) or soup.find("div", {"data-auto": "gallery"})
            if name_el:
                result["name"] = name_el.get_text(strip=True)
            if price_el:
                result["price"] = self._clean_price(price_el.get_text(strip=True))
            if img_el:
                result["image"] = img_el.get("src", "") if img_el.name == "img" else ""

        # Regex fallback
        prices_found = re.findall(r'(\d[\d\s]+)\s*₽', text)
        all_prices = []
        for p in prices_found:
            clean = int(re.sub(r'\D', '', p))
            if clean > 500 and clean not in all_prices:
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
        if result["image"] == "":
            meta_img = soup.find("meta", property="og:image")
            if meta_img:
                result["image"] = meta_img.get("content", "")

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