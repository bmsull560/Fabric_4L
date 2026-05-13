import glob
import re

for path in glob.glob('services/layer3-knowledge/src/**/*.py', recursive=True):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fix from ...X imports (triple dot) -> from X
    fixed = re.sub(r'from \.\.\.([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*) import', r'from \1 import', content)
    
    # Fix from ..X imports (double dot) -> from X
    fixed = re.sub(r'from \.\.([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*) import', r'from \1 import', fixed)
    
    if fixed != content:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(fixed)
        print(f'Fixed {path}')
