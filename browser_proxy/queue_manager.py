import asyncio
import time
from collections import deque
from typing import Optional, Dict


class QueueManager:
    def __init__(self, default_timeout: float = 45.0):
        self.pending = deque()
        self.processing = {}
        self.results = {}
        self.events = {}
        self.lock = asyncio.Lock()
        self.default_timeout = default_timeout

    async def submit(self, url: str, timeout: Optional[float] = None) -> Dict:
        timeout = timeout or self.default_timeout
        async with self.lock:
            if url in self.results:
                return {"status": "ok", "html": self.results.pop(url)}

            task = {"url": url, "submitted_at": time.time()}
            self.pending.append(task)
            event = asyncio.Event()
            self.events[url] = event

        try:
            await asyncio.wait_for(event.wait(), timeout=timeout)
            async with self.lock:
                html = self.results.pop(url, None)
            if html:
                return {"status": "ok", "html": html}
            return {"status": "error", "detail": "empty result"}
        except asyncio.TimeoutError:
            async with self.lock:
                self.events.pop(url, None)
                self.pending = deque([t for t in self.pending if t["url"] != url])
                self.processing.pop(url, None)
            return {"status": "error", "detail": "timeout"}

    async def get_task(self) -> Optional[Dict]:
        async with self.lock:
            while self.pending:
                task = self.pending.popleft()
                if time.time() - task["submitted_at"] > 60:
                    continue
                self.processing[task["url"]] = time.time()
                return {"url": task["url"]}
            return None

    async def set_result(self, url: str, html: str):
        async with self.lock:
            self.results[url] = html
            event = self.events.pop(url, None)
            if event:
                event.set()
            self.processing.pop(url, None)