\# Правила



\## Боты

\- Только aiogram 3.x. Запрещено: telebot, aiogram 2.x

\- Используй Router()

\- FSM через aiogram.fsm

\- Токен из .env



\## Парсеры

\- Только async. Запрещено: requests, urllib

\- Используй aiohttp + BeautifulSoup

\- Добавляй User-Agent и задержки

\- Обрабатывай ошибки try/except



\## После каждого изменения

\- Запусти: python auto\_test.py

\- Не завершай задачу, пока тесты не пройдены



\## Интернет

\- Для парсинга сначала смотри HTML через /fetch

