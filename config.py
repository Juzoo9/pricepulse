import os

GOOGLE_CREDENTIALS_PATH = os.getenv("GOOGLE_CREDENTIALS_PATH", "google_credentials.json")
EXCEL_OUTPUT_PATH = os.getenv("EXCEL_OUTPUT_PATH", "results.xlsx")
GOOGLE_SHEETS_NAME = os.getenv("GOOGLE_SHEETS_NAME", "PricePulse Results")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID", "")
PROXY_ENABLED = os.getenv("PROXY_ENABLED", "true").lower() == "true"
PROXY_MAX_PROXIES = int(os.getenv("PROXY_MAX_PROXIES", "20"))
