import os
import sys

def minify_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    result = []
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith('#'):
            continue
        result.append(line.rstrip())
    return '\n'.join(result)

def process_project(path):
    total = 0
    saved = 0
    output = []
    for root, _, files in os.walk(path):
        if 'venv' in root or '__pycache__' in root or '.git' in root:
            continue
        for f in files:
            if not f.endswith('.py'):
                continue
            fp = os.path.join(root, f)
            rel = os.path.relpath(fp, path)
            with open(fp, 'r', encoding='utf-8') as file:
                original = file.read()
            minified = minify_file(fp)
            total += len(original)
            saved += len(original) - len(minified)
            output.append(f"\n=== {rel} ===\n{minified}")
    with open('context_minified.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(output))
    if total > 0:
        print(f"Исходно: {total} символов")
        print(f"Сокращено: {saved} символов ({saved/total*100:.1f}%)")
    print(f"Сохранено в context_minified.txt")

if __name__ == '__main__':
    process_project(sys.argv[1] if len(sys.argv) > 1 else '.')
