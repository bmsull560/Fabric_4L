import os, re
src_dir = os.path.abspath('client/src')
files = []
for root, dirs, filenames in os.walk(src_dir):
    for f in filenames:
        if f.endswith(('.ts','.tsx')):
            files.append(os.path.join(root, f))

import_regex = re.compile(r"from\s+['\"](@[^'\"]+)['\"]|import\s+['\"](@[^'\"]+)['\"]")
issues = []
for file in files:
    with open(file, 'r', encoding='utf-8', errors='ignore') as fh:
        content = fh.read()
    for m in import_regex.finditer(content):
        imp = m.group(1) or m.group(2)
        if not imp.startswith('@/'): continue
        rel = imp[2:]
        if rel.startswith('/'): rel = rel[1:]
        base = os.path.join(src_dir, rel.replace('/', os.sep))
        exists = any([
            os.path.exists(base + '.ts'),
            os.path.exists(base + '.tsx'),
            os.path.exists(os.path.join(base, 'index.ts')),
            os.path.exists(os.path.join(base, 'index.tsx')),
        ])
        if not exists:
            issues.append(file.replace(src_dir, '').replace(os.sep, '/') + ' -> ' + imp)

for i in issues:
    print(i)
print('Total issues:', len(issues))
