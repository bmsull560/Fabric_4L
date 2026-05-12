import subprocess
import os

# Get list of deleted files from git
result = subprocess.run(
    ['git', '-C', 'c:/Users/BBB/Fabric_4L', 'status', '--short'],
    capture_output=True, text=True
)

deleted_files = []
for line in result.stdout.split('\n'):
    if line.startswith(' D value_fabric/'):
        deleted_files.append(line[3:])

# Check which deleted files have equivalents in services/
no_equivalent = []
have_equivalent = []

for f in deleted_files:
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
            have_equivalent.append(f)
        else:
            no_equivalent.append(f)
    else:
        no_equivalent.append(f)

# Restore files with no equivalent
print(f"Restoring {len(no_equivalent)} files that have no canonical equivalent...")
for f in no_equivalent:
    result = subprocess.run(
        ['git', '-C', 'c:/Users/BBB/Fabric_4L', 'checkout', 'HEAD', '--', f],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"  Failed to restore {f}: {result.stderr}")

print(f"\nKeeping {len(have_equivalent)} files deleted (they have canonical equivalents in services/)")
for f in have_equivalent:
    print(f"  DELETED: {f}")

print("\nDone.")
