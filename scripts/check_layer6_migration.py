import os

value_fabric_dir = 'c:/Users/BBB/Fabric_4L/value_fabric/layer6'
canonical_dir = 'c:/Users/BBB/Fabric_4L/services/layer6-benchmarks/src'

def list_files(root, prefix=''):
    if not os.path.exists(root):
        return []
    files = []
    for entry in os.listdir(root):
        path = os.path.join(root, entry)
        rel = prefix + '/' + entry if prefix else entry
        if os.path.isdir(path):
            files.extend(list_files(path, rel))
        elif entry.endswith('.py'):
            files.append(rel)
    return files

vf_files = list_files(value_fabric_dir)
canonical_files = list_files(canonical_dir)

print(f"value_fabric/layer6 files: {len(vf_files)}")
print(f"services/layer6-benchmarks/src files: {len(canonical_files)}")

both = []
only_vf = []

for f in vf_files:
    if f in canonical_files:
        both.append(f)
    else:
        only_vf.append(f)

print(f"\nFiles in BOTH: {len(both)}")
for f in both:
    print(f"  {f}")

print(f"\nFiles ONLY in value_fabric/layer6: {len(only_vf)}")
for f in only_vf:
    print(f"  {f}")
