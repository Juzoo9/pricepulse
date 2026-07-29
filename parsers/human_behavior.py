import asyncio
import random


async def random_delay(min_sec: float = 0.5, max_sec: float = 3.0):
    delay = random.uniform(min_sec, max_sec)
    await asyncio.sleep(delay)


async def human_scroll(browser, steps: int = 5):
    for _ in range(steps):
        scroll_y = random.randint(100, 400)
        script = f"window.scrollBy(0, {scroll_y});"
        await browser.execute_js(script)
        await asyncio.sleep(random.uniform(0.3, 1.0))


async def human_mouse_move(browser):
    for _ in range(3):
        x = random.randint(100, 800)
        y = random.randint(100, 600)
        script = f"""
            var event = new MouseEvent('mousemove', {{
                clientX: {x}, clientY: {y},
                bubbles: true, cancelable: true
            }});
            document.dispatchEvent(event);
        """
        await browser.execute_js(script)
        await asyncio.sleep(random.uniform(0.1, 0.5))