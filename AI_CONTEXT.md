# AI Context — PricePulse

## Что уже работает (НЕ ломай!)
- Browser Proxy на localhost:8000
- Chrome Extension Manifest V3
- Парсеры: Ozon, WB, Yandex, Lamoda, MegaMarket, AliExpress
- Бот: Aiogram 3, FSM, /add, /list, /history, /admin
- Все парсеры возвращают: name, price, price_card, old_price, image, url, source, error

## Типичные ошибки (проверяй всегда!)
1. 'title' → использовать result['name'] или result.get('name')
2. 'bool object can't be awaited' → is_valid() должен быть async def
3. 'NoneType' has no attribute 'string' → проверять soup.title на None
4. Пустые цены → regex fallback ищет ₽ в тексте страницы
5. 'Event loop is closed' → close() в парсерах: pass

## Архитектура парсера (шаблон)
class XParser:
    PATTERNS = [r"regex_url"]
    def __init__(self, notifier=None): ...
    async def is_valid(self, url) -> bool: ...  # async!
    async def parse(self, url) -> dict: ...      # name, price, price_card, old_price, image, url, source, error
    async def close(self): pass

## Команды для проверки
- Сервер: py -m uvicorn browser_proxy.main:app --port 8000
- Тест: py test_anticaptcha.py
- Синтаксис: python -m py_compile файл.py

## Правила работы с ботом
- result.get('error') проверять ДО извлечения name/price
- out_of_stock: отправлять 📭 сообщение, не пытаться показать цены
- HTML в сообщениях: использовать parse_mode="HTML", но экранировать <b> через html.escape() если данные из парсера