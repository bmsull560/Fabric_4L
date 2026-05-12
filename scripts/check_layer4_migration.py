import os

value_fabric_dir = 'c:/Users/BBB/Fabric_4L/value_fabric/layer4'
canonical_dir = 'c:/Users/BBB/Fabric_4L/services/layer4-agents/src'

def list_files(root, prefix=''):
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

print(f"value_fabric/layer4 files: {len(vf_files)}")
print(f"services/layer4-agents/src files: {len(canonical_files)}")

both = []
only_vf = []
only_canonical = []

for f in vf_files:
    if f in canonical_files:
        both.append(f)
    else:
        only_vf.append(f)

for f in canonical_files:
    if f not in vf_files:
        only_canonical.append(f)

print(f"\nFiles in BOTH (can delete from value_fabric/layer4): {len(both)}")
for f in both:
    print(f"  {f}")

print(f"\nFiles ONLY in value_fabric/layer4 (keep or move): {len(only_vf)}")
for f in only_vf:
    print(f"  {f}")

print(f"\nFiles ONLY in services/layer4-agents/src (already canonical): {len(only_canonical)}")
for f in only_canonical[:20]:
    print(f"  {f}")
if len(only_canonical) > 20:
    print(f"  ... and {len(only_canonical) - 20} more")
