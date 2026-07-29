import asyncio
import time
from parsers.factory import get_parser
from bot.services.captcha_notifier import CaptchaNotifier


TEST_URLS = [
    "https://www.ozon.ru/product/elektronnaya-kniga-7-amazon-kindle-bez-reklamy-2024-gen11-paperwhite-16gb-garantiya-12-mesyatsev-4406016672/",
    "https://www.wildberries.ru/catalog/15622747/detail.aspx",
    "https://market.yandex.ru/product--smartfon-apple-iphone-15-128gb-chernyi/1762667413",
    "https://www.lamoda.ru/p/mp002xw04f3j/clothes-nike-tolstovka/",
    "https://megamarket.ru/catalog/details/smartfon-xiaomi-redmi-note-12-128gb-onyx-gray-100030743080/",
    "https://aliexpress.ru/item/1005004953214053.html",
    "https://www.ozon.ru/product/naushniki-apple-airpods-pro-2-1040534600/",
    "https://www.wildberries.ru/catalog/150033123/detail.aspx",
    "https://market.yandex.ru/product--naushniki-apple-airpods-pro-2/1760234567",
    "https://www.lamoda.ru/p/mp002xw08qlo/clothes-acoola-tolstovka/",
]

def format_price(p):
    return f"{int(p):,}₽".replace(",", " ") if p else "-"

def format_discount(price, price_card, old_price):
    actual = price_card if price_card else price
    base = old_price
    if actual and base and base > actual:
        return f"{round((1 - actual / base) * 100)}%"
    return "-"

async def test():
    print("=" * 80)
    print("ТЕСТ: Browser Proxy + Три цены (price, price_card, old_price)")
    print("=" * 80)
    print("Убедись, что запущены:")
    print("  1. uvicorn browser_proxy.main:app --port 8000")
    print("  2. Chrome с загруженным расширением")
    print("=" * 80)

    notifier = CaptchaNotifier()
    stats = {"success": 0, "captcha": 0, "error": 0, "total": len(TEST_URLS)}

    for i, url in enumerate(TEST_URLS, 1):
        print(f"\n[{i}/{len(TEST_URLS)}] {url[:70]}...")
        start = time.time()
        try:
            parser = get_parser(url, notifier=notifier)
            r = await parser.parse(url)
            elapsed = time.time() - start

            if r is None:
                stats["error"] += 1
                print(f"      ❌ None ({elapsed:.1f}с)")
            elif isinstance(r, dict) and r.get("error") == "captcha":
                stats["captcha"] += 1
                print(f"      🛡 КАПЧА: {r.get('captcha_type')} ({elapsed:.1f}с)")
            elif isinstance(r, dict) and "error" in r:
                if r.get("error") == "out_of_stock":
                    stats["success"] += 1
                    name = r.get('name', 'N/A')[:45]
                    print(f"      \ud83d\udced НЕТ В НАЛИЧИИ: {name} ({elapsed:.1f}с)")
                else:
                    stats["error"] += 1
                    print(f"      ❌ {r['error']} ({elapsed:.1f}с)")
            else:
                stats["success"] += 1
                name = r.get('name', 'N/A')[:45]
                price = format_price(r.get('price'))
                price_card = format_price(r.get('price_card'))
                old_price = format_price(r.get('old_price'))
                discount = format_discount(r.get('price'), r.get('price_card'), r.get('old_price'))
                print(f"      ✅ {name}")
                print(f"         Текущая: {price} | С картой: {price_card} | Старая: {old_price} | Скидка: {discount} ({elapsed:.1f}с)")

            await parser.close()
        except Exception as e:
            stats["error"] += 1
            print(f"      ❌ Исключение: {e}")

    print("\n" + "=" * 80)
    print("ИТОГОВАЯ СТАТИСТИКА")
    print(f"  Всего URL:   {stats['total']}")
    print(f"  ✅ Успех:    {stats['success']}")
    print(f"  🛡 Капча:    {stats['captcha']}")
    print(f"  ❌ Ошибки:   {stats['error']}")
    print(f"  Успешность:  {stats['success']/stats['total']*100:.1f}%")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(test())