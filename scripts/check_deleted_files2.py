import subprocess
import os

result = subprocess.run(
    ['git', '-C', 'c:/Users/BBB/Fabric_4L', 'status', '--short'],
    capture_output=True, text=True
)

deleted_files = []
for line in result.stdout.split('\n'):
    if line.startswith(' D value_fabric/'):
        deleted_files.append(line[3:])

no_equivalent = []
have_equivalent = []

for f in deleted_files:
    if not f.endswith('.py'):
        continue
    parts = f.replace('value_fabric/', '').split('/')
    layer_map = {
        'layer1': 'layer1-ingestion',
        'layer1_ingestion': 'layer1-ingestion',
        'layer2': 'layer2-extraction',
        'layer3': 'layer3-knowledge',
        'layer3_knowledge': 'layer3-knowledge',
        'layer4': 'layer4-agents',
        'layer5': 'layer5-ground-truth',
        'layer5_ground_truth': 'layer5-ground-truth',
        'layer6': 'layer6-benchmarks',
        'layer6_benchmarks': 'layer6-benchmarks',
    }
    
    if parts[0] in layer_map:
        service_dir = f"services/{layer_map[parts[0]]}/src"
        equiv_path = '/'.join([service_dir] + parts[1:])
        full_path = f"c:/Users/BBB/Fabric_4L/{equiv_path}"
        if os.path.exists(full_path):
            have_equivalent.append((f, equiv_path))
        else:
            no_equivalent.append(f)
    else:
        no_equivalent.append(f)

with open('c:/Users/BBB/Fabric_4L/scripts/deleted_files_report.txt', 'w') as out:
    out.write(f"Deleted files with equivalents in services/: {len(have_equivalent)}\n")
    for orig, equiv in have_equivalent:
        out.write(f"  HAVE_EQ: {orig} -> {equiv}\n")
    
    out.write(f"\nDeleted files with NO equivalents in services/: {len(no_equivalent)}\n")
    for f in no_equivalent:
        out.write(f"  NO_EQ: {f}\n")

print(f"Done. Have equivalent: {len(have_equivalent)}, No equivalent: {len(no_equivalent)}")
