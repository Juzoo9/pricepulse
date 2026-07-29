import asyncio
import random
import httpx
from typing import List, Optional, Set
from datetime import datetime, timedelta


class ProxyRotator:
    """Загрузка, валидация и ротация бесплатных HTTP-прокси."""

    SOURCES = [
        "https://api.proxyscrape.com/v2/?request=get&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all",
        "https://www.proxy-list.download/api/v1/get?type=http",
        "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
        "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt",
    ]

    def __init__(self, enabled: bool = True, max_proxies: int = 20):
        self.enabled = enabled
        self.max_proxies = max_proxies
        self.proxies: List[str] = []
        self.working_proxies: List[str] = []
        self.current_index = 0
        self.last_fetch: Optional[datetime] = None

    async def fetch_proxies(self) -> List[str]:
        all_proxies: Set[str] = set()
        async with httpx.AsyncClient(timeout=15.0) as client:
            for source in self.SOURCES:
                try:
                    resp = await client.get(source)
                    if resp.status_code == 200:
                        for line in resp.text.splitlines():
                            line = line.strip()
                            if line and ":" in line and not line.startswith("#"):
                                parts = line.split(":")
                                if len(parts) >= 2:
                                    ip, port = parts[0], parts[1]
                                    if ip.replace(".", "").isdigit():
                                        all_proxies.add(f"http://{ip}:{port}")
                except Exception as e:
                    print(f"[ProxyRotator] Ошибка загрузки {source}: {e}")

        self.proxies = list(all_proxies)[: self.max_proxies * 3]
        self.last_fetch = datetime.now()
        print(f"[ProxyRotator] Загружено {len(self.proxies)} прокси")
        return self.proxies

    async def validate_proxy(self, proxy: str) -> bool:
        try:
            async with httpx.AsyncClient(proxy=proxy, timeout=8.0) as client:
                resp = await client.get("http://httpbin.org/ip")
                return resp.status_code == 200
        except Exception:
            return False

    async def validate_proxy_simple(self, proxy: str) -> bool:
        try:
            async with httpx.AsyncClient(proxy=proxy, timeout=5.0) as client:
                resp = await client.get("http://1.1.1.1")
                return resp.status_code in (200, 301, 302)
        except Exception:
            return False

    async def validate_all(self, max_concurrent: int = 10):
        if not self.proxies:
            await self.fetch_proxies()

        self.working_proxies = []
        semaphore = asyncio.Semaphore(max_concurrent)

        async def check_one(proxy: str):
            async with semaphore:
                if await self.validate_proxy(proxy) or await self.validate_proxy_simple(proxy):
                    self.working_proxies.append(proxy)
                    print(f"[ProxyRotator] ✅ {proxy}")
                else:
                    print(f"[ProxyRotator] ❌ {proxy}")

        await asyncio.gather(*[check_one(p) for p in self.proxies])
        self.proxies = []
        print(f"[ProxyRotator] Рабочих: {len(self.working_proxies)}")

    def get_next(self) -> Optional[str]:
        if not self.working_proxies:
            return None
        proxy = self.working_proxies[self.current_index % len(self.working_proxies)]
        self.current_index += 1
        return proxy

    async def get_working_proxy(self) -> Optional[str]:
        if not self.enabled:
            return None
        if not self.working_proxies or (
            self.last_fetch and datetime.now() - self.last_fetch > timedelta(minutes=30)
        ):
            await self.fetch_proxies()
            await self.validate_all()
        return self.get_next()

    def remove_current(self, proxy: str):
        if proxy in self.working_proxies:
            self.working_proxies.remove(proxy)
            print(f"[ProxyRotator] Удалён забаненный: {proxy}")
