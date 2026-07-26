import os
import sys

BOT = '''import asyncio
import os
from aiogram import Bot, Dispatcher, Router
from aiogram.filters import CommandStart
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer("Привет!")

async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
'''

PARSER = '''import asyncio
import random
import logging
import aiohttp
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

async def fetch_page(session, url):
    try:
        async with session.get(url, headers=HEADERS, timeout=30) as resp:
            resp.raise_for_status()
            return await resp.text()
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        return None

async def main():
    async with aiohttp.ClientSession() as session:
        html = await fetch_page(session, "https://example.com")
        if html:
            logger.info("OK")
    await asyncio.sleep(random.uniform(1, 3))

if __name__ == "__main__":
    asyncio.run(main())
'''

def create_bot(name):
    base = os.path.join(os.getcwd(), name)
    for d in ['handlers', 'keyboards', 'states', 'services']:
        os.makedirs(os.path.join(base, d), exist_ok=True)
        open(os.path.join(base, d, '__init__.py'), 'w').close()
    open(os.path.join(base, 'bot.py'), 'w', encoding='utf-8').write(BOT)
    open(os.path.join(base, 'config.py'), 'w', encoding='utf-8').write('import os\nfrom dotenv import load_dotenv\n\nload_dotenv()\nBOT_TOKEN = os.getenv("BOT_TOKEN")\n')
    open(os.path.join(base, 'requirements.txt'), 'w', encoding='utf-8').write('aiogram==3.17.0\npython-dotenv==1.0.0\n')
    open(os.path.join(base, '.env'), 'w', encoding='utf-8').write('BOT_TOKEN=your_token_here\n')
    print(f"✅ Бот создан: {base}")

def create_parser(name):
    base = os.path.join(os.getcwd(), name)
    os.makedirs(base, exist_ok=True)
    open(os.path.join(base, 'parser.py'), 'w', encoding='utf-8').write(PARSER)
    open(os.path.join(base, 'requirements.txt'), 'w', encoding='utf-8').write('aiohttp==3.11.0\nbeautifulsoup4==4.12.0\nlxml==5.3.0\n')
    print(f"✅ Парсер создан: {base}")

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("python new_project.py bot ИМЯ")
        print("python new_project.py parser ИМЯ")
        sys.exit(1)
    t, n = sys.argv[1], sys.argv[2]
    if t == 'bot':
        create_bot(n)
    elif t == 'parser':
        create_parser(n)
    else:
        print("Тип: bot или parser")