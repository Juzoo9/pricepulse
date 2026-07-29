from typing import Optional, Dict


class CaptchaDetector:
    KEYWORDS = [
        "captcha", "recaptcha", "hcaptcha", "turnstile",
        "проверка", "робот", "robot", "verify", "antibot",
        "js-challenge", "challenge-platform",
    ]

    SELECTORS = [
        "iframe[src*='captcha']", "iframe[src*='recaptcha']",
        "iframe[src*='hcaptcha']", "iframe[src*='turnstile']",
        "div[class*='captcha']", "div[id*='captcha']",
        "div[class*='recaptcha']", "div[id*='recaptcha']",
        "div[class*='hcaptcha']", "div[id*='hcaptcha']",
        "div[class*='turnstile']", "div[id*='turnstile']",
        "div[class*='challenge']", "div[id*='challenge']",
        "form[action*='captcha']",
    ]

    async def check(self, browser) -> Optional[Dict]:
        try:
            html = ""
            try:
                html = await browser.get_html()
            except Exception:
                pass
            if not html:
                html = ""

            html_lower = html.lower()
            for keyword in self.KEYWORDS:
                if keyword in html_lower:
                    return {"detected": True, "type": keyword}

            for selector in self.SELECTORS:
                try:
                    script = f"return document.querySelector('{selector}') !== null;"
                    result = await browser.execute_js(script)
                    if result:
                        return {"detected": True, "type": selector}
                except Exception:
                    pass

            return None
        except Exception:
            return None