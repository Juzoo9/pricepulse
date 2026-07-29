import re
from typing import Optional, Dict
from bs4 import BeautifulSoup
from .browser_proxy_client import BrowserProxyClient
from bot.services.captcha_notifier import CaptchaNotifier


class AliExpressParser:
    PATTERNS = [r"https?://(?:www\.)?aliexpress\.(ru|com)/.*"]

    def __init__(self, notifier: Optional[CaptchaNotifier] = None):
        self.client = BrowserProxyClient()
        self.notifier = notifier or CaptchaNotifier()

    def is_valid(self, url: str) -> bool:
        return any(re.match(p, url) for p in self.PATTERNS)

    async def parse(self, url: str) -> Optional[Dict]:
        html = await self.client.get_html(url)
        if not html:
            return {"error": "empty_html", "url": url, "source": "aliexpress"}

        soup = BeautifulSoup(html, 'lxml')
        text = soup.get_text(separator=" ", strip=True)

        title = (soup.title.string or "").lower() if soup.title else ""
        if any(x in title for x in ["captcha", "капча", "ddos", "verify"]):
            await self.notifier.notify(url, f"title: {title[:100]}", "aliexpress")
            return {"error": "captcha", "captcha_type": title[:100], "url": url, "source": "aliexpress"}

        # Проверка на отсутствие в наличии
        stock_text = text.lower()
        if any(x in stock_text for x in ["out of stock", "sold out", "unavailable", "нет в наличии", "распродано"]):
            name = "Неизвестно"
            meta = soup.find("meta", property="og:title")
            if meta:
                name = meta.get("content", "Неизвестно").split('|')[0].strip()
            return {"error": "out_of_stock", "name": name, "url": url, "source": "aliexpress", "price": None, "price_card": None, "old_price": None, "image": ""}

        result = {"name": "Неизвестно", "price": None, "price_card": None, "old_price": None, "image": "", "url": url, "source": "aliexpress"}

        # DOM
        name_el = soup.find("h1") or soup.find("div", {"data-pl": "product-title"}) or soup.find("h1", class_="title")
        price_el = soup.find("span", class_="price") or soup.find("div", class_=re.compile("product-price-current")) or soup.find(string=re.compile(r"\d+\s*₽"))
        old_price_el = soup.find("span", class_=re.compile("original-price")) or soup.find("s") or soup.find(string=re.compile(r"was|original", re.I))
        img_el = soup.find("img", class_="magnifier-image") or soup.find("meta", property="og:image") or soup.find("img")

        if name_el:
            result["name"] = name_el.get_text(strip=True)
        if price_el:
            result["price"] = self._clean_price(price_el.get_text(strip=True) if hasattr(price_el, 'get_text') else str(price_el))
        if old_price_el:
            result["old_price"] = self._clean_price(old_price_el.get_text(strip=True) if hasattr(old_price_el, 'get_text') else str(old_price_el))
        if img_el:
            result["image"] = img_el.get("src", "") if img_el.name == "img" else ""

        # Regex fallback (ищем $, € или ₽)
        prices_found = re.findall(r'(\d[\d\s,.]+)\s*[₽$€]', text)
        all_prices = []
        for p in prices_found:
            clean = float(re.sub(r'[^\d.]', '', p.replace(',', '.')))
            if clean > 1 and clean not in all_prices:
                all_prices.append(clean)
        all_prices.sort()

        if len(all_prices) >= 2 and result["price"] is None:
            result["price"] = int(all_prices[0])
            result["old_price"] = int(all_prices[-1])
        elif len(all_prices) == 1 and result["price"] is None:
            result["price"] = int(all_prices[0])

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