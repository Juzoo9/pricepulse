import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class CaptchaNotifier:
    def __init__(self, bot_token: Optional[str] = None, admin_chat_id: Optional[str] = None):
        self.bot_token = bot_token or os.getenv("BOT_TOKEN", "")
        self.admin_chat_id = admin_chat_id or os.getenv("ADMIN_CHAT_ID", "")

    async def notify(self, url: str, captcha_type: str, source: str):
        message = (
            f"🛡 Обнаружена капча!\n"
            f"Источник: {source}\n"
            f"Тип: {captcha_type}\n"
            f"URL: {url}"
        )
        print(f"[CaptchaNotifier] {message}")
        if self.bot_token and self.admin_chat_id:
            try:
                import httpx
                async with httpx.AsyncClient() as client:
                    await client.post(
                        f"https://api.telegram.org/bot{self.bot_token}/sendMessage",
                        json={"chat_id": self.admin_chat_id, "text": message},
                    )
            except Exception as e:
                logger.error(f"Ошибка отправки уведомления: {e}")