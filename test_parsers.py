import asyncio
import os
from parsers.factory import get_parser
from exporters.excel_exporter import ExcelExporter
from exporters.google_sheets_exporter import GoogleSheetsExporter
import config

async def test():
    urls = [
        "https://ozon.ru/t/V22UySC",
        "https://www.wildberries.ru/catalog/123456/detail.aspx",
        "https://market.yandex.ru/product--smartfon-apple-iphone-15/12345",
        "https://www.lamoda.ru/p/mp002xw08qlo/clothes-acoola-tolstovka/",
        "https://sbermegamarket.ru/catalog/details/smartfon-xiaomi-123/",
        "https://aliexpress.ru/item/1005001234567890.html",
    ]

    results = []
    for url in urls:
        print(f"\n=== Тест: {url} ===")
        try:
            p = get_parser(url)
            print(f"Выбран парсер: {type(p).__name__}")
            r = await p.parse(url)
            print(f"Результат: {r}")
            if r:
                results.append(r)
            await p.close()
        except Exception as e:
            print(f"Ошибка теста: {e}")
        await asyncio.sleep(2)

    if results:
        print("\n=== Экспорт в Excel ===")
        excel = ExcelExporter(output_path=config.EXCEL_OUTPUT_PATH)
        path = excel.export(results)
        print(f"Excel сохранён: {path}")

        creds_path = config.GOOGLE_CREDENTIALS_PATH
        if os.path.exists(creds_path):
            print("\n=== Экспорт в Google Sheets ===")
            try:
                gs = GoogleSheetsExporter(credentials_path=creds_path)
                sheet_url = gs.export(results, spreadsheet_name=config.GOOGLE_SHEETS_NAME)
                print(f"Google Sheets создана: {sheet_url}")
            except Exception as e:
                print(f"Ошибка Google Sheets: {e}")
        else:
            print(f"\n[Пропуск Google Sheets] Файл credentials не найден: {creds_path}")
            print("Инструкция: создай Service Account в https://console.cloud.google.com/")
            print("Скачай JSON-ключ, переименуй в google_credentials.json и положи в C:\\projects\\pricepulse\\")
    else:
        print("Нет данных для экспорта.")

if __name__ == "__main__":
    asyncio.run(test())