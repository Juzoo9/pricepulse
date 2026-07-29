const PROXY_URL = 'http://localhost:8000';

// Keep-alive через alarms (V3)
chrome.alarms.create('poll', { periodInMinutes: 0.166 }); // каждые 10 сек

chrome.alarms.onAlarm.addListener(async (alarm) => {
  if (alarm.name !== 'poll') return;
  await pollTask();
});

async function pollTask() {
  try {
    const resp = await fetch(`${PROXY_URL}/task`);
    if (resp.status === 204) return;
    const task = await resp.json();
    if (!task || !task.url) return;

    console.log('[Extension] Получена задача:', task.url);

    // Открываем вкладку
    const tab = await chrome.tabs.create({ url: task.url, active: false });

    // Ждём полной загрузки
    await new Promise((resolve) => {
      const listener = (tabId, info) => {
        if (tabId === tab.id && info.status === 'complete') {
          chrome.tabs.onUpdated.removeListener(listener);
          resolve();
        }
      };
      chrome.tabs.onUpdated.addListener(listener);
    });

    // Даём время на прохождение challenge (Cloudflare/SmartCaptcha)
    await sleep(8000);

    // Получаем HTML
    const [{ result }] = await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      func: () => document.documentElement.outerHTML
    });

    // Отправляем результат
    await fetch(`${PROXY_URL}/result`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url: task.url, html: result })
    });

    console.log('[Extension] Результат отправлен:', task.url);

    // Закрываем вкладку
    await chrome.tabs.remove(tab.id);

  } catch (e) {
    console.error('[Extension] Ошибка:', e);
  }
}

function sleep(ms) {
  return new Promise(r => setTimeout(r, ms));
}