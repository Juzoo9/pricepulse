import re
import json
from typing import Optional, Dict
from bs4 import BeautifulSoup
from .browser_proxy_client import BrowserProxyClient
from bot.services.captcha_notifier import CaptchaNotifier


class WildberriesParser:
    PATTERNS = [
        r"https?://(?:www\.)?wildberries\.ru/catalog/\d+/detail\.aspx.*",
        r"https?://(?:www\.)?wildberries\.ru/.*",
    ]

    def __init__(self, notifier: Optional[CaptchaNotifier] = None):
        self.client = BrowserProxyClient()
        self.notifier = notifier or CaptchaNotifier()

    async def is_valid(self, url: str) -> bool:
        return any(re.match(p, url) for p in self.PATTERNS)

    async def parse(self, url: str) -> Optional[Dict]:
        html = await self.client.get_html(url)
        if not html:
            return {"error": "empty_html", "url": url, "source": "wildberries"}

        soup = BeautifulSoup(html, 'lxml')
        text = soup.get_text(separator=" ", strip=True)

        if any(x in text.lower() for x in ["ничего не найдено", "not found", "товар не найден", "404"]):
            return {"error": "product_not_found", "url": url, "source": "wildberries"}

        # Проверка на отсутствие в наличии
        stock_text = text.lower()
        if any(x in stock_text for x in ["нет в наличии", "распродано", "sold out", "out of stock", "ожидается поступление"]):
            name = "Неизвестно"
            meta = soup.find("meta", property="og:title")
            if meta:
                name = meta.get("content", "Неизвестно").split('|')[0].strip()
            return {"error": "out_of_stock", "name": name, "url": url, "source": "wildberries", "price": None, "price_card": None, "old_price": None, "image": ""}

        title = (soup.title.string or "").lower() if soup.title else ""
        if any(x in title for x in ["captcha", "капча", "ddos", "access denied"]):
            await self.notifier.notify(url, f"title: {title[:100]}", "wildberries")
            return {"error": "captcha", "captcha_type": title[:100], "url": url, "source": "wildberries"}

        result = {"name": "Неизвестно", "price": None, "price_card": None, "old_price": None, "image": "", "url": url, "source": "wildberries"}

        # window.__INITIAL_STATE__
        for script in soup.find_all("script"):
            if script.string and "window.__INITIAL_STATE__" in script.string:
                try:
                    match = re.search(r'window\.__INITIAL_STATE__\s*=\s*({.+?});?</script>', html, re.DOTALL)
                    if match:
                        data = json.loads(match.group(1))
                        p = data.get("catalog", {}).get("product", {})
                        if p:
                            result["name"] = p.get("name", p.get("goodsName", "Неизвестно"))
                            price_raw = p.get("salePriceU") or p.get("price") or p.get("priceU")
                            result["price"] = int(price_raw) / 100 if price_raw else None
                            old_raw = p.get("priceU") or p.get("oldPrice")
                            old_price = int(old_raw) / 100 if old_raw else None
                            if old_price and result["price"] and old_price > result["price"]:
                                result["old_price"] = old_price
                            result["image"] = p.get("image", "")
                except Exception:
                    continue

        # DOM fallback
        if result["price"] is None:
            name_el = soup.find("h1") or soup.find(class_=re.compile("product-page__title"))
            price_el = soup.find(class_=re.compile("price-block__final-price"))
            img_el = soup.find("img", class_=re.compile("photo-zoom__preview")) or soup.find("img")
            if name_el:
                result["name"] = name_el.get_text(strip=True)
            if price_el:
                result["price"] = self._clean_price(price_el.get_text(strip=True))
            if img_el:
                result["image"] = img_el.get("src", "")

        # Regex fallback
        prices_found = re.findall(r'(\d[\d\s]+)\s*₽', text)
        all_prices = []
        for p in prices_found:
            clean = int(re.sub(r'\D', '', p))
            if clean > 100 and clean not in all_prices:
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