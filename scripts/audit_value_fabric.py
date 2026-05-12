import os
root = r'c:\Users\BBB\Fabric_4L\value_fabric'
files = []
for dirpath, dirnames, filenames in os.walk(root):
    dirnames[:] = [d for d in dirnames if d != '__pycache__']
    for f in filenames:
        if not f.endswith('.pyc') and f != 'DEPRECATED.md':
            files.append(os.path.join(dirpath, f))
for f in sorted(files):
    print(f)
print(f'Total non-deprecated files: {len(files)}')
