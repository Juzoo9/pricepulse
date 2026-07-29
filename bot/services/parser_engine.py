from parsers.wildberries import WildberriesParser
from parsers.ozon import OzonParser
from parsers.universal import UniversalParser

PARSERS = [WildberriesParser(), OzonParser(), UniversalParser()]

async def parse_url(url: str):
    for parser in PARSERS:
        if await parser.is_valid(url):
            return await parser.parse(url)
    raise ValueError("Сайт не поддерживается")