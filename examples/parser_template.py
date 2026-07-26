"""
Шаблон асинхронного парсера. Копируй этот стиль.
"""
import asyncio
import random
import logging
import aiohttp
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

async def fetch_page(session, url):
    try:
        async with session.get(url, headers=HEADERS, timeout=30) as resp:
            resp.raise_for_status()
            return await resp.text()
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        return None

async def main():
    url = "https://example.com"
    async with aiohttp.ClientSession() as session:
        html = await fetch_page(session, url)
        if html:
            logger.info("Страница загружена")
    await asyncio.sleep(random.uniform(1, 3))

if __name__ == "__main__":
    asyncio.run(main())