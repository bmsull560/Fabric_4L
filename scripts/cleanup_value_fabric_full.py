import os
import shutil

root = 'c:/Users/BBB/Fabric_4L/value_fabric'
for dirpath, dirnames, filenames in os.walk(root, topdown=False):
    for f in filenames:
        p = os.path.join(dirpath, f)
        if f != 'DEPRECATED.md':
            os.remove(p)
    # Remove empty dirs (except root)
    if dirpath != root and not os.listdir(dirpath):
        os.rmdir(dirpath)
print('done')
