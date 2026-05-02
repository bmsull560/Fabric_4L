import re, os, subprocess, sys

cwd = 'value-fabric/layer4-agents'
p = subprocess.run([sys.executable, '-m', 'ruff', 'check', 'src/'], capture_output=True, text=True, cwd=cwd)
lines = (p.stdout + p.stderr).split('\n')

files = set()
i = 0
while i < len(lines):
    if 'F821 Undefined name' in lines[i]:
        if i + 1 < len(lines):
            m = re.search(r'-->\s+(src\\.+?):\d+:\d+', lines[i + 1])
            if m:
                files.add(m.group(1).replace('\\', '/'))
    i += 1

print('Files with F821:', sorted(files))

for rel in sorted(files):
    path = os.path.join(cwd, rel)
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    if re.search(r'from typing import[^\n]*Any', content):
        print(f'Skip {rel} (already has Any)')
    else:
        m = re.search(r'^(from typing import .*)$', content, re.MULTILINE)
        if m:
            old = m.group(1)
            new = old.rstrip() + ', Any'
            content = content.replace(old, new, 1)
        else:
            lines2 = content.split('\n')
            idx = 0
            for j, line in enumerate(lines2):
                if line.startswith('import ') or line.startswith('from '):
                    idx = j + 1
            lines2.insert(idx, 'from typing import Any')
            content = '\n'.join(lines2)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f'Updated {rel}')
