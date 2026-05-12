import os
for dirpath, dirnames, filenames in os.walk('c:/Users/BBB/Fabric_4L/value_fabric'):
    for f in filenames:
        print(os.path.join(dirpath, f))
