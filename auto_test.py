import subprocess
import sys
import os

def run_tests():
    results = []
    py_files = []
    
    for root, dirs, files in os.walk('.'):
        if any(skip in root for skip in ['venv', '__pycache__', '.git', 'examples']):
            continue
        for f in files:
            if f.endswith('.py'):
                py_files.append(os.path.join(root, f))
    
    if not py_files:
        print("Python файлы не найдены")
        return
    
    for pf in py_files:
        with open(pf, 'r', encoding='utf-8') as file:
            content = file.read()
        
        result = subprocess.run(
            [sys.executable, '-m', 'py_compile', pf],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            results.append(f"❌ СИНТАКСИС в {pf}: {result.stderr.strip()}")
            continue
        
        results.append(f"✅ Синтаксис OK: {pf}")
        
        if 'bot' in pf.lower():
            if 'telebot' in content.lower():
                results.append(f"❌ {pf}: запрещён telebot, используй aiogram 3.x")
            if 'aiogram' in content and 'Router()' not in content:
                results.append(f"⚠️ {pf}: добавь Router()")
        
        if 'parser' in pf.lower() or 'parse' in pf.lower():
            if 'import requests' in content:
                results.append(f"❌ {pf}: запрещён requests, используй aiohttp")
            if 'async def' not in content:
                results.append(f"❌ {pf}: парсер должен быть async")
    
    report = "\n".join(results)
    print("\n" + "="*50)
    print("РЕЗУЛЬТАТЫ ТЕСТОВ:")
    print("="*50)
    print(report)
    
    with open('test_report.txt', 'w', encoding='utf-8') as f:
        f.write(report)
    
    errors = [r for r in results if r.startswith('❌')]
    if errors:
        print(f"\n❌ Найдено {len(errors)} ошибок!")
        sys.exit(1)
    else:
        print("\n🎉 Все тесты пройдены!")
        sys.exit(0)

if __name__ == '__main__':
    run_tests()