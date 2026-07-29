from .factory import get_parser
from .ozon import OzonParser
from .wildberries import WildberriesParser
from .yandex_market import YandexMarketParser
from .lamoda import LamodaParser
from .sbermegamarket import SberMegaMarketParser
from .aliexpress import AliExpressParser
from .universal_browser_parser import UniversalBrowserParser
from .browser_proxy_client import BrowserProxyClient

__all__ = [
    "get_parser",
    "OzonParser",
    "WildberriesParser",
    "YandexMarketParser",
    "LamodaParser",
    "SberMegaMarketParser",
    "AliExpressParser",
    "UniversalBrowserParser",
    "BrowserProxyClient",
]