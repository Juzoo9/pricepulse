import re
import json
from typing import Optional, Dict
from bs4 import BeautifulSoup
from .browser_proxy_client import BrowserProxyClient
from bot.services.captcha_notifier import CaptchaNotifier


class OzonParser:
    PATTERNS = [r"https?://(?:www\.)?ozon\.ru/.*", r"https?://(?:www\.)?ozon\.ru/t/.*"]

    def __init__(self, notifier: Optional[CaptchaNotifier] = None):
        self.client = BrowserProxyClient()
        self.notifier = notifier or CaptchaNotifier()

    def is_valid(self, url: str) -> bool:
        return any(re.match(p, url) for p in self.PATTERNS)

    async def parse(self, url: str) -> Optional[Dict]:
        html = await self.client.get_html(url)
        if not html:
            return {"error": "empty_html", "url": url, "source": "ozon"}

        soup = BeautifulSoup(html, 'lxml')
        text = soup.get_text(separator=" ", strip=True)

        title = (soup.title.string or "").lower() if soup.title else ""
        if any(x in title for x in ["captcha", "капча", "ddos", "access denied", "just a moment"]):
            await self.notifier.notify(url, f"title: {title[:100]}", "ozon")
            return {"error": "captcha", "captcha_type": title[:100], "url": url, "source": "ozon"}

        # Проверка на отсутствие в наличии
        stock_text = text.lower()
        if any(x in stock_text for x in ["нет в наличии", "распродано", "sold out", "out of stock", "ожидается", "не доступен", "нет в продаже"]):
            name = "Неизвестно"
            meta = soup.find("meta", property="og:title")
            if meta:
                name = meta.get("content", "Неизвестно").split('|')[0].strip()
            return {"error": "out_of_stock", "name": name, "url": url, "source": "ozon", "price": None, "price_card": None, "old_price": None, "image": ""}

        result = {"name": "Неизвестно", "price": None, "price_card": None, "old_price": None, "image": "", "url": url, "source": "ozon"}

        # JSON-LD
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.string)
                if isinstance(data, dict) and data.get("@type") == "Product":
                    offers = data.get("offers", {})
                    if isinstance(offers, list) and offers:
                        offers = offers[0]
                    if isinstance(offers, dict):
                        result["price"] = self._clean_price(offers.get("price"))
                        result["old_price"] = self._clean_price(offers.get("highPrice"))
                    img = data.get("image", "")
                    if isinstance(img, list) and img:
                        img = img[0]
                    result["image"] = img or ""
                    result["name"] = data.get("name", "Неизвестно")
            except Exception:
                continue

        # NUXT
        if result["price"] is None:
            for script in soup.find_all("script"):
                if script.string and "window.__NUXT__" in script.string:
                    try:
                        match = re.search(r'window\.__NUXT__\s*=\s*({.+?});?</script>', html, re.DOTALL)
                        if match:
                            data = json.loads(match.group(1))
                            product = self._find_in_state(data)
                            if product:
                                result["name"] = product.get("name", product.get("title", "Неизвестно"))
                                result["price"] = self._clean_price(product.get("price") or product.get("finalPrice"))
                                result["old_price"] = self._clean_price(product.get("oldPrice") or product.get("originalPrice"))
                                result["image"] = product.get("image", product.get("coverImage", ""))
                    except Exception:
                        continue

        # DOM fallback
        if result["price"] is None:
            name_el = soup.find("h1")
            price_el = soup.find("span", {"data-testid": "price"})
            old_price_el = soup.find("span", {"data-testid": "old-price"})
            img_el = soup.find("img", {"data-testid": "image"}) or soup.find("img")
            if name_el:
                result["name"] = name_el.get_text(strip=True)
            if price_el:
                result["price"] = self._clean_price(price_el.get_text(strip=True))
            if old_price_el:
                result["old_price"] = self._clean_price(old_price_el.get_text(strip=True))
            if img_el:
                result["image"] = img_el.get("src", "")

        # Универсальный fallback: ищем ВСЕ цены на странице
        prices_found = re.findall(r'(\d[\d\s]+)\s*₽', text)
        all_prices = []
        for p in prices_found:
            clean = int(re.sub(r'\D', '', p))
            if clean > 100 and clean not in all_prices:
                all_prices.append(clean)
        all_prices.sort()

        # Ищем зачёркнутую цену отдельно (через line-through или класс old)
        old_from_dom = None
        for span in soup.find_all(["span", "div"]):
            style = span.get("style", "")
            cls = " ".join(span.get("class", []))
            if "line-through" in style or "old" in cls.lower():
                txt = span.get_text(strip=True)
                m = re.search(r'(\d[\d\s]+)', txt)
                if m:
                    val = int(re.sub(r'\D', '', m.group(1)))
                    if val > 1000:
                        old_from_dom = val
                        break

        # Логика: если 3+ цены — min=card, middle=current, max=old
        if len(all_prices) >= 3 and result["price"] is None:
            result["price_card"] = all_prices[0]
            result["price"] = all_prices[1]
            result["old_price"] = all_prices[-1]
        elif len(all_prices) == 2 and result["price"] is None:
            result["price"] = all_prices[0]
            result["old_price"] = all_prices[1]
        elif len(all_prices) == 1 and result["price"] is None:
            result["price"] = all_prices[0]

        # Если price_card ещё не найдена, но есть 3+ цены и price уже заполнен
        if result["price_card"] is None and len(all_prices) >= 3:
            result["price_card"] = all_prices[0]

        # Если нашли зачёркнутую цену через DOM — используем её как old_price
        if old_from_dom and old_from_dom > (result.get("price") or 0):
            result["old_price"] = old_from_dom

        # Если price_card == price — сбрасываем price_card
        if result["price_card"] == result["price"]:
            result["price_card"] = None

        # Meta fallback для названия и картинки
        if result["name"] == "Неизвестно":
            meta = soup.find("meta", property="og:title")
            if meta:
                result["name"] = meta.get("content", "Неизвестно").split('|')[0].strip()
        if result["image"] == "":
            meta_img = soup.find("meta", property="og:image")
            if meta_img:
                result["image"] = meta_img.get("content", "")

        return result

    def _find_in_state(self, obj):
        if not isinstance(obj, dict):
            return None
        if "name" in obj and ("price" in obj or "finalPrice" in obj):
            return obj
        for v in obj.values():
            if isinstance(v, dict):
                found = self._find_in_state(v)
                if found:
                    return found
            elif isinstance(v, list):
                for item in v:
                    found = self._find_in_state(item)
                    if found:
                        return found
        return None

    def _clean_price(self, raw) -> Optional[int]:
        if raw is None:
            return None
        if isinstance(raw, (int, float)):
            return int(raw)
        digits = re.sub(r"[^\d]", "", str(raw))
        return int(digits) if digits else None

    async def close(self):
        pass