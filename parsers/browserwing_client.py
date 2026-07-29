import httpx
import asyncio
import json
import random
from typing import Optional, Dict, Any
from .stealth_config import USER_AGENTS, STEALTH_SCRIPT


class BrowserWingClient:
    def __init__(self, base_url: str = "http://127.0.0.1:8080/api/v1", proxy: Optional[str] = None):
        self.base_url = base_url
        self.proxy = proxy  # сохраняем для информации, но НЕ используем в httpx к localhost
        self.client = httpx.AsyncClient(base_url=base_url, timeout=60.0)
        self.user_agent = random.choice(USER_AGENTS)

    async def navigate(self, url: str, wait: float = 5.0) -> bool:
        try:
            response = await self.client.post("/executor/navigate", json={"url": url})
            response.raise_for_status()
            await asyncio.sleep(wait)
            await self.apply_stealth()
            return True
        except Exception as e:
            print(f"[BrowserWing] Ошибка navigate: {e}")
            return False

    async def apply_stealth(self):
        try:
            await self.execute_js(STEALTH_SCRIPT)
        except Exception as e:
            print(f"[BrowserWing] Stealth ошибка: {e}")

    async def execute_js(self, script: str) -> Any:
        try:
            # Rod требует IIFE с явным return
            if not script.strip().startswith("(") and "return" not in script:
                script = f"(function() {{ {script} }})()"
            response = await self.client.post("/executor/execute_script", json={"script": script})
            response.raise_for_status()
            data = response.json()
            return data.get("result") if isinstance(data, dict) else data
        except Exception as e:
            print(f"[BrowserWing] Ошибка execute_js: {e}")
            return None

    async def snapshot(self) -> Dict[str, Any]:
        try:
            response = await self.client.get("/executor/snapshot")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"[BrowserWing] Ошибка snapshot: {e}")
            return {}

    async def get_html(self) -> str:
        try:
            result = await self.execute_js("return document.documentElement.outerHTML")
            return str(result) if result else ""
        except Exception:
            return ""

    async def reload(self) -> bool:
        try:
            await self.execute_js("location.reload()")
            await asyncio.sleep(4)
            return True
        except Exception:
            return False

    async def close(self):
        await self.client.aclose()