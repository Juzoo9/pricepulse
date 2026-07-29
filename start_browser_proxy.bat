@echo off
echo ==========================================
echo  PricePulse Browser Proxy Launcher
echo ==========================================
echo.

cd /d C:\projects\pricepulse

echo [1/3] Проверка зависимостей...
python -c "import fastapi, uvicorn, bs4" 2>nul
if errorlevel 1 (
    echo Установка зависимостей...
    pip install -r requirements.txt
)

echo [2/3] Запуск FastAPI сервера...
start "Browser Proxy Server" cmd /k "uvicorn browser_proxy.main:app --host 0.0.0.0 --port 8000 --reload"

echo [3/3] Ожидание сервера...
timeout /t 3 /nobreak >nul

echo [3/3] Запуск Chrome с расширением...
start chrome --load-extension="C:\projects\pricepulse\browser_extension" --user-data-dir="C:\projects\pricepulse\chrome_profile" --no-first-run --no-default-browser-check "http://localhost:8000/docs"

echo.
echo ==========================================
echo  Готово! Chrome откроется с расширением.
echo  Не закрывай окна сервера и Chrome.
echo  Запусти тест: python test_anticaptcha.py
echo ==========================================
pause