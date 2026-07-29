import ast
import os

def test_all_parsers():
    base = os.path.join(os.path.dirname(__file__), "parsers")
    errors = []
    for root, dirs, files in os.walk(base):
        for file in files:
            if not file.endswith(".py"):
                continue
            path = os.path.join(root, file)
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            # Проверяем только файлы с классом парсера
            if "class" not in content or "Parser" not in content:
                continue
            try:
                ast.parse(content)
                print(f"[OK] {file}")
            except SyntaxError as e:
                print(f"❌ {file}: {e}")
                errors.append((file, e))
    if errors:
        raise Exception(f"Syntax errors: {errors}")
    print("All parsers passed syntax check.")

if __name__ == "__main__":
    test_all_parsers()