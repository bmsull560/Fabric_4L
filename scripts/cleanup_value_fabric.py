import os
import shutil

root = 'c:/Users/BBB/Fabric_4L/value_fabric'
for dirpath, dirnames, filenames in os.walk(root, topdown=False):
    for f in filenames:
        if f.endswith('.py'):
            os.remove(os.path.join(dirpath, f))
    for d in list(dirnames):
        if d == '__pycache__':
            p = os.path.join(dirpath, d)
            shutil.rmtree(p)
            dirnames.remove(d)
print('done')
