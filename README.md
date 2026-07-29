# PricePulse 🔥

Telegram-бот для мониторинга цен с российских маркетплейсов. Обходит защиту от ботов через реальный Chrome + Browser Proxy.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=flat-square)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-green?style=flat-square)
![Aiogram](https://img.shields.io/badge/Aiogram-3.x-blueviolet?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)

## Архитектура
[Telegram Bot] → [FastAPI Browser Proxy] → [Chrome Extension] → [Target Site]
↑                        ↓
Queue Manager            Real HTML
plain

- **Browser Proxy** — FastAPI-сервер, управляет очередью URL
- **Chrome Extension** (Manifest V3) — открывает страницы в реальном Chrome, проходит Cloudflare/SmartCaptcha
- **Parsers** — BeautifulSoup + regex, извлекают 3 цены (текущая, с картой, старая)
- **Bot** — Aiogram 3, уведомления о снижении цен

## Поддерживаемые магазины

| Магазин | Цена | С картой | Старая | Статус наличия |
|---------|------|----------|--------|----------------|
| Ozon | ✅ | ✅ | ✅ | ✅ |
| Wildberries | ✅ | — | ✅ | ✅ |
| Яндекс.Маркет | ✅ | — | ✅ | ✅ |
| Lamoda | ✅ | — | ✅ | ✅ |
| СберМегаМаркет | ✅ | — | ✅ | ✅ |
| AliExpress | ✅ | — | — | ✅ |

## Стек

- **Backend:** Python 3.10, FastAPI, Uvicorn
- **Parsing:** BeautifulSoup4, lxml, httpx
- **Bot:** Aiogram 3, python-dotenv
- **Browser:** Chrome Extension (Manifest V3)
- **Queue:** Asyncio Event + Deque

## Установка

```bash
git clone https://github.com/Juzoo9/pricepulse.git
cd pricepulse
pip install -r requirements.txt
Создать .env:
env
BOT_TOKEN=your_telegram_bot_token
ADMIN_ID=your_telegram_id
Запуск (3 окна PowerShell)
1. Browser Proxy
bash
uvicorn browser_proxy.main:app --host 0.0.0.0 --port 8000
2. Chrome с расширением
bash
chrome --load-extension=./browser_extension --user-data-dir=./chrome_profile
3. Bot
bash
python -m bot.main
Структура проекта
plain
pricepulse/
├── bot/                    # Telegram-бот (Aiogram 3)
│   ├── handlers/           # Команды и callback'и
│   └── services/           # Планировщик, уведомления
├── browser_extension/      # Chrome Extension (Manifest V3)
│   ├── manifest.json
│   └── background.js
├── browser_proxy/          # FastAPI-сервер очереди
│   ├── main.py
│   └── queue_manager.py
├── parsers/                # Парсеры магазинов
│   ├── ozon.py             # JSON-LD + NUXT + DOM + regex fallback
│   ├── wildberries.py      # __INITIAL_STATE__ + DOM
│   ├── yandex_market.py    # JSON-LD + DOM
│   ├── lamoda.py           # DOM + meta fallback
│   ├── sbermegamarket.py   # DOM + regex
│   ├── aliexpress.py       # DOM + multi-currency regex
│   └── browser_proxy_client.py
├── requirements.txt
└── .env
Особенности реализации
3 цены: price (текущая), price_card (с Ozon-картой/подпиской), old_price (зачёркнутая)
Out of stock: Детекция по 11+ фразам ("нет в наличии", "sold out" и др.)
Anti-bot bypass: Реальный Chrome с GUI проходит JS-challenge самостоятельно
Fallback chain: JSON-LD → NUXT → DOM-селекторы → regex → meta tags
Smart discount: Скидка считается от old_price к price_card (если есть) или price
Лицензия
MIT