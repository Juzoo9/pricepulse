from typing import Optional
from .ozon import OzonParser
from .wildberries import WildberriesParser
from .yandex_market import YandexMarketParser
from .lamoda import LamodaParser
from .sbermegamarket import SberMegaMarketParser
from .aliexpress import AliExpressParser
from .universal_browser_parser import UniversalBrowserParser
from bot.services.captcha_notifier import CaptchaNotifier


PARSERS = [OzonParser, WildberriesParser, YandexMarketParser, LamodaParser, SberMegaMarketParser, AliExpressParser]

def get_parser(url: str, notifier: Optional[CaptchaNotifier] = None):
    for ParserClass in PARSERS:
        p = ParserClass(notifier=notifier)
        if p.is_valid(url):
            return p
    return UniversalBrowserParser(notifier=notifier)