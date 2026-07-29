import httpx
from typing import Optional


class BrowserProxyClient:
    """Клиент для Browser Proxy (реальный Chrome)."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.client = httpx.AsyncClient(base_url=base_url, timeout=60.0)

    async def get_html(self, url: str, timeout: float = 45.0) -> str:
        resp = await self.client.post("/load", params={"url": url, "timeout": timeout})
        resp.raise_for_status()
        data = resp.json()
        if data.get("status") == "success":
            return data.get("html", "")
        return ""

    async def close(self):
        pass  # httpx закроет соединения сам при выходе