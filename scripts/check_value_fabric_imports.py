import subprocess
import sys

# Search for actual Python import statements referencing value_fabric
result = subprocess.run(
    ['git', 'grep', '-n', '--extended-regexp', r'^\s*(from value_fabric|import value_fabric)'],
    cwd='c:/Users/BBB/Fabric_4L',
    capture_output=True,
    text=True
)

lines = result.stdout.splitlines()
# Filter out references within value_fabric/ itself
external = [l for l in lines if 'value_fabric/' not in l.split(':')[0]]

if external:
    print("EXTERNAL IMPORTS FOUND:")
    for l in external:
        print(l)
    sys.exit(1)
else:
    print("No external imports from value_fabric found.")
    sys.exit(0)
