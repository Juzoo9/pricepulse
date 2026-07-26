from parsers.base import BaseParser
from parsers.universal import UniversalParser
from parsers.wildberries import WildberriesParser


async def parse_url(url: str) -> dict:
    parsers: list[BaseParser] = [
        WildberriesParser(),
        UniversalParser(),
    ]

    for parser in parsers:
        if await parser.is_valid(url):
            return await parser.parse(url)

    raise ValueError("Сайт не поддерживается")