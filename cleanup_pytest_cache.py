import os
import shutil

removed = 0
for root, dirs, files in os.walk('c:/Users/BBB/Fabric_4L'):
    for d in dirs[:]:
        if d == '.pytest_cache':
            path = os.path.join(root, d)
            shutil.rmtree(path, ignore_errors=True)
            removed += 1
            dirs.remove(d)

print(f'Removed {removed} .pytest_cache directories')
