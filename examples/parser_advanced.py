"""
Продвинутый парсер с retry и ротацией заголовков.
Используй как шаблон для сложных сайтов.
"""
import asyncio
import random
import logging
from typing import Optional, List, Dict

import aiohttp

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/118.0.0.0 Safari/537.36",
]

HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "DNT": "1",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}


async def fetch_with_retry(
    session: aiohttp.ClientSession,
    url: str,
    max_retries: int = 3,
    use_proxy: bool = False
) -> Optional[str]:
    """
    Загружает страницу с retry и случайными задержками.
    """
    headers = {**HEADERS, "User-Agent": random.choice(USER_AGENTS)}
    
    for attempt in range(max_retries):
        try:
            logger.info(f"Попытка {attempt + 1}/{max_retries}: {url}")
            
            async with session.get(
                url,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30),
                ssl=False  # иногда помогает с ошибками SSL
            ) as response:
                
                if response.status == 200:
                    return await response.text()
                
                elif response.status == 403:
                    logger.warning("403 Forbidden — возможно, Cloudflare")
                    await asyncio.sleep(random.uniform(3, 6))
                
                elif response.status == 429:
                    logger.warning("429 Too Many Requests — ждём")
                    await asyncio.sleep(random.uniform(5, 10))
                
                else:
                    logger.warning(f"Статус {response.status}")
                    await asyncio.sleep(random.uniform(2, 4))
                    
        except asyncio.TimeoutError:
            logger.error("Таймаут")
            await asyncio.sleep(random.uniform(2, 4))
        except Exception as e:
            logger.error(f"Ошибка сети: {e}")
            await asyncio.sleep(random.uniform(1, 3))
    
    logger.error(f"Не удалось загрузить {url} после {max_retries} попыток")
    return None


async def main():
    url = "https://example.com/products"
    
    async with aiohttp.ClientSession() as session:
        html = await fetch_with_retry(session, url, max_retries=3)
        
        if html:
            logger.info(f"Успешно загружено {len(html)} символов")
        else:
            logger.error("Не удалось получить страницу. Попробуй ScraperAPI.")
        
        # Задержка между запросами
        await asyncio.sleep(random.uniform(1, 3))


if __name__ == "__main__":
    asyncio.run(main())