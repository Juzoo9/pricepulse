import os
from typing import List, Dict, Optional
import gspread
from gspread.utils import rowcol_to_a1
from google.oauth2.service_account import Credentials


class GoogleSheetsExporter:
    """Экспорт результатов парсинга в Google Sheets."""

    SCOPES = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]

    def __init__(self, credentials_path: str = "google_credentials.json"):
        self.credentials_path = credentials_path
        self.client = None

    def _get_client(self) -> gspread.Client:
        if self.client is None:
            if not os.path.exists(self.credentials_path):
                raise FileNotFoundError(
                    f"Файл credentials не найден: {self.credentials_path}. "
                    "Создай Service Account в Google Cloud Console, скачай JSON-ключ и положи в проект."
                )
            creds = Credentials.from_service_account_file(self.credentials_path, scopes=self.SCOPES)
            self.client = gspread.authorize(creds)
        return self.client

    def export(self, data: List[Dict], spreadsheet_name: str = "PricePulse Results") -> str:
        """
        Создаёт Google-таблицу, заполняет данными и возвращает URL.
        """
        client = self._get_client()

        spreadsheet = client.create(spreadsheet_name)
        worksheet = spreadsheet.sheet1
        worksheet.title = "Парсинг"

        headers = ["Название", "Цена", "Старая цена", "Изображение", "URL", "Источник"]
        worksheet.append_row(headers)

        worksheet.format("A1:F1", {
            "textFormat": {"bold": True, "fontSize": 12},
            "backgroundColor": {"red": 0.21, "green": 0.38, "blue": 0.57},
            "horizontalAlignment": "CENTER",
        })

        for item in data:
            row = [
                item.get("name", ""),
                item.get("price", "") if item.get("price") is not None else "",
                item.get("old_price", "") if item.get("old_price") is not None else "",
                item.get("image", ""),
                item.get("url", ""),
                item.get("source", ""),
            ]
            worksheet.append_row(row)

        worksheet.columns_auto_resize(0, 5)

        spreadsheet.share("", perm_type="anyone", role="reader")

        return spreadsheet.url